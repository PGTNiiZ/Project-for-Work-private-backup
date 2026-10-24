"""Apply a genetic algorithm to identity-resolution model optimization.

The GA jointly searches a feature subset, GradientBoosting hyperparameters,
and the MATCH decision threshold. Fitness uses validation data only; the test
split is read exactly once after the search to report an unbiased final result.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import pickle
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score

from src.genetic_optimizer import Bounds, GAConfig, GeneticOptimizer, Genome


PKG_DIR = Path(__file__).resolve().parent
DEFAULT_DATA = PKG_DIR / "data" / "train_all.parquet"
DEFAULT_OUTPUT = PKG_DIR / "ga_output"

NON_FEATURE_COLUMNS = {
    "split_name", "pair_type", "label", "pred_label", "pred_class", "probability",
    "profile_row_id_a", "profile_row_id_b", "profile_id_a", "profile_id_b",
    "platform_a", "platform_b", "userName_a", "userName_b", "fullName_a", "fullName_b",
    "user_folder_a", "user_folder_b", "component_a", "component_b",
    "is_tp", "is_tn", "is_fp", "is_fn",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="CSV or Parquet table containing train/val/test splits")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--population-size", type=int, default=20)
    parser.add_argument("--generations", type=int, default=12)
    parser.add_argument("--elite-size", type=int, default=2)
    parser.add_argument("--tournament-size", type=int, default=3)
    parser.add_argument("--mutation-rate", type=float, default=0.15)
    parser.add_argument("--crossover-rate", type=float, default=0.80)
    parser.add_argument("--feature-penalty", type=float, default=0.01, help="Penalty for selecting all available features")
    parser.add_argument("--max-train-rows", type=int, default=None, help="Optional stratified cap for quicker experiments")
    parser.add_argument("--max-val-rows", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    if path.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, low_memory=False)
    raise ValueError("--data must be a .csv or .parquet file")


def select_feature_columns(frame: pd.DataFrame) -> list[str]:
    """Select numeric model inputs while excluding IDs and prior model outputs."""
    numeric = frame.select_dtypes(include=[np.number, "bool"]).columns
    features = [column for column in numeric if column not in NON_FEATURE_COLUMNS]
    if not features:
        raise ValueError("No numeric feature columns remain after leakage exclusions")
    return features


def prepare_splits(frame: pd.DataFrame, seed: int, train_cap: int | None, val_cap: int | None) -> dict[str, pd.DataFrame]:
    required = {"split_name", "label"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    splits = {name: frame.loc[frame["split_name"] == name].copy() for name in ("train", "val", "test")}
    empty = [name for name, split in splits.items() if split.empty]
    if empty:
        raise ValueError(f"Dataset has no rows for split(s): {empty}")
    for name, split in splits.items():
        labels = set(split["label"].dropna().astype(int).unique())
        if labels != {0, 1}:
            raise ValueError(f"Split '{name}' must contain both binary labels; found {sorted(labels)}")
    splits["train"] = stratified_cap(splits["train"], train_cap, seed)
    splits["val"] = stratified_cap(splits["val"], val_cap, seed + 1)
    return splits


def stratified_cap(frame: pd.DataFrame, cap: int | None, seed: int) -> pd.DataFrame:
    if cap is None or len(frame) <= cap:
        return frame.reset_index(drop=True)
    if cap < 2:
        raise ValueError("row caps must be at least 2")
    fractions = frame["label"].value_counts(normalize=True)
    parts = []
    remaining = cap
    for index, (label, group) in enumerate(frame.groupby("label", sort=True)):
        amount = remaining if index == len(fractions) - 1 else max(1, round(cap * fractions[label]))
        amount = min(amount, len(group), remaining)
        parts.append(group.sample(n=amount, random_state=seed))
        remaining -= amount
    return pd.concat(parts).sample(frac=1.0, random_state=seed).reset_index(drop=True)


class IdentityFitness:
    def __init__(self, splits: dict[str, pd.DataFrame], feature_cols: list[str], seed: int, feature_penalty: float):
        self.feature_cols = feature_cols
        self.seed = seed
        self.feature_penalty = feature_penalty
        self.train_y = splits["train"]["label"].to_numpy(dtype=np.int8)
        self.val_y = splits["val"]["label"].to_numpy(dtype=np.int8)
        self.train_x = splits["train"][feature_cols].fillna(0.0).to_numpy(dtype=np.float32)
        self.val_x = splits["val"][feature_cols].fillna(0.0).to_numpy(dtype=np.float32)

    def __call__(self, genome: Genome) -> float:
        selected = np.asarray(genome.feature_mask, dtype=bool)
        model = build_model(genome, self.seed)
        model.fit(self.train_x[:, selected], self.train_y)
        probabilities = model.predict_proba(self.val_x[:, selected])[:, 1]
        predictions = (probabilities >= genome.threshold).astype(np.int8)
        ap = average_precision_score(self.val_y, probabilities)
        auc = roc_auc_score(self.val_y, probabilities)
        f1 = f1_score(self.val_y, predictions, zero_division=0)
        complexity = selected.mean()
        return float(0.45 * ap + 0.35 * f1 + 0.20 * auc - self.feature_penalty * complexity)


def build_model(genome: Genome, seed: int) -> GradientBoostingClassifier:
    return GradientBoostingClassifier(
        n_estimators=genome.n_estimators,
        learning_rate=genome.learning_rate,
        max_depth=genome.max_depth,
        min_samples_leaf=genome.min_samples_leaf,
        subsample=genome.subsample,
        random_state=seed,
    )


def metrics(labels: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict[str, float]:
    predictions = (probabilities >= threshold).astype(np.int8)
    return {
        "ap": float(average_precision_score(labels, probabilities)),
        "auc": float(roc_auc_score(labels, probabilities)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
    }


def save_outputs(
    output_dir: Path,
    best: Genome,
    fitness: float,
    history: list[dict[str, float]],
    feature_cols: list[str],
    model: GradientBoostingClassifier,
    result: dict[str, object],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_features = [name for name, enabled in zip(feature_cols, best.feature_mask) if enabled]
    pd.DataFrame(history).to_csv(output_dir / "generation_history.csv", index=False)
    (output_dir / "selected_features.txt").write_text("\n".join(selected_features) + "\n", encoding="utf-8")
    with (output_dir / "best_model.pkl").open("wb") as handle:
        pickle.dump({"model": model, "features": selected_features, "threshold": best.threshold}, handle)
    payload = {
        **result,
        "best_validation_fitness": fitness,
        "genome": {**asdict(best), "feature_mask": list(best.feature_mask)},
        "selected_features": selected_features,
    }
    (output_dir / "report.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.feature_penalty < 0:
        raise ValueError("--feature-penalty must be non-negative")
    started = time.perf_counter()
    frame = load_table(args.data)
    feature_cols = select_feature_columns(frame)
    splits = prepare_splits(frame, args.seed, args.max_train_rows, args.max_val_rows)
    config = GAConfig(
        population_size=args.population_size,
        generations=args.generations,
        elite_size=args.elite_size,
        tournament_size=args.tournament_size,
        crossover_rate=args.crossover_rate,
        mutation_rate=args.mutation_rate,
        seed=args.seed,
    )
    optimizer = GeneticOptimizer(len(feature_cols), config, Bounds())
    fitness = IdentityFitness(splits, feature_cols, args.seed, args.feature_penalty)

    def report_generation(generation: int, ranked: list[tuple[Genome, float]]) -> None:
        print(f"Generation {generation:02d}/{config.generations}: best={ranked[0][1]:.6f}", flush=True)

    best, best_fitness, history = optimizer.optimize(fitness, report_generation)
    selected_features = [name for name, enabled in zip(feature_cols, best.feature_mask) if enabled]
    final_model = build_model(best, args.seed)
    final_model.fit(
        splits["train"][selected_features].fillna(0.0).to_numpy(dtype=np.float32),
        splits["train"]["label"].to_numpy(dtype=np.int8),
    )
    validation_probs = final_model.predict_proba(splits["val"][selected_features].fillna(0.0).to_numpy(dtype=np.float32))[:, 1]
    test_probs = final_model.predict_proba(splits["test"][selected_features].fillna(0.0).to_numpy(dtype=np.float32))[:, 1]
    result = {
        "data": str(args.data.resolve()),
        "seed": args.seed,
        "ga_config": asdict(config),
        "split_rows": {name: len(split) for name, split in splits.items()},
        "available_feature_count": len(feature_cols),
        "selected_feature_count": len(selected_features),
        "validation_metrics": metrics(splits["val"]["label"].to_numpy(), validation_probs, best.threshold),
        "test_metrics": metrics(splits["test"]["label"].to_numpy(), test_probs, best.threshold),
        "elapsed_seconds": time.perf_counter() - started,
    }
    save_outputs(args.output_dir, best, best_fitness, history, feature_cols, final_model, result)
    print(json.dumps({"selected_features": len(selected_features), "threshold": best.threshold, **result["test_metrics"]}, indent=2))
    print(f"Artifacts written to {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
