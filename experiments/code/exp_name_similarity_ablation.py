"""Validation-first N0-N7 name-similarity experiments on the multimodal baseline."""

from __future__ import annotations

import argparse
import json
import os
import pickle
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

from identity_resolution.core.name_similarity import (
    char_ngram_cosine,
    damerau_similarity,
    handle_features,
    latin_soundex_match,
    token_set_similarity,
)
from identity_resolution.stages.feature_registry import SCHEMA_VERSION, group_for_feature, resolve_feature_set
from identity_resolution.settings import PROJECT_ROOT


def _write_status(run_dir: Path, state: str, detail: str, progress: int | None = None) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_dir.name,
        "state": state,
        "detail": detail,
        "pid": os.getpid(),
        "progress": progress,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "status.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with (run_dir.parent / "task_events.jsonl").open("a", encoding="utf-8") as event_log:
        event_log.write(json.dumps(payload) + "\n")
    percent = f" {progress:3d}%" if progress is not None else ""
    print(f"[{run_dir.name}]{percent} {state}: {detail}", flush=True)


def _name_features(record_a: dict, record_b: dict) -> dict[str, float]:
    user_a, user_b = record_a.get("userName_norm", ""), record_b.get("userName_norm", "")
    full_a, full_b = record_a.get("fullName_norm", ""), record_b.get("fullName_norm", "")
    cross = (damerau_similarity(user_a, full_b), damerau_similarity(full_a, user_b))
    handle = handle_features(user_a, user_b)
    return {
        "name_damerau_username": damerau_similarity(user_a, user_b),
        "name_damerau_fullname": damerau_similarity(full_a, full_b),
        "name_char_ngram_username": char_ngram_cosine(user_a, user_b),
        "name_char_ngram_fullname": char_ngram_cosine(full_a, full_b),
        "name_token_set_username": token_set_similarity(user_a, user_b),
        "name_token_set_fullname": token_set_similarity(full_a, full_b),
        "name_handle_exact": handle["exact"],
        "name_handle_prefix": handle["prefix"],
        "name_handle_suffix": handle["suffix"],
        "name_handle_length_ratio": handle["length_ratio"],
        "name_handle_available": handle["available"],
        "name_cross_damerau_max": max(cross),
        "name_cross_damerau_mean": sum(cross) / len(cross),
        "name_phonetic_username": latin_soundex_match(user_a, user_b),
        "name_phonetic_fullname": latin_soundex_match(full_a, full_b),
    }


def _configure_base(run_dir: Path):
    from identity_resolution.stages import train_base as base

    base.SCRIPT_DIR = run_dir
    base.PROJECT_ROOT = PROJECT_ROOT
    base.PROFILES_PATH = PROJECT_ROOT / "data_for_project" / "normalized_profiles_with_profile_id.csv"
    base.ARTIFACTS_DIR = run_dir / "artifacts"
    base.MODELS_DIR = run_dir / "models"
    base.REPORTS_DIR = run_dir / "reports"
    base.SBERT_EMBEDDINGS_PATH = base.ARTIFACTS_DIR / "sbert_embeddings.npy"
    base.ensure_dirs()
    return base


def _prepare_offline_embeddings(base, profiles: pd.DataFrame) -> None:
    """Align the repository's cached MiniLM embeddings to the train-base profile subset."""
    source_dir = PROJECT_ROOT / "experiments"
    source_embeddings = source_dir / "profile_embeddings_minilm.npy"
    source_ids = source_dir / "profile_embeddings_minilm_ids.npy"
    if not source_embeddings.exists() or not source_ids.exists():
        raise FileNotFoundError("Offline text mode needs experiments/profile_embeddings_minilm*.npy")
    embeddings = np.load(source_embeddings, mmap_mode="r")
    ids = np.load(source_ids, mmap_mode="r")
    positions = {int(profile_id): index for index, profile_id in enumerate(ids)}
    selected_ids = profiles.loc[profiles["profile_id"].notna(), "profile_row_id"].astype(int).tolist()
    missing = [profile_id for profile_id in selected_ids if profile_id not in positions]
    if missing:
        raise ValueError(f"Offline embedding cache is missing {len(missing)} training profiles")
    aligned = np.asarray(embeddings[[positions[profile_id] for profile_id in selected_ids]], dtype=np.float32)
    base.SBERT_EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(base.SBERT_EMBEDDINGS_PATH, aligned)


def _feature_computer(base_compute, feature_set):
    def compute(pairs: pd.DataFrame, profile_bundle: dict[str, object]):
        feature_df, base_columns = base_compute(pairs, profile_bundle)
        if feature_set.extra_groups:
            records = profile_bundle["records"]
            extras = [
                _name_features(records[int(pair.profile_row_id_a)], records[int(pair.profile_row_id_b)])
                for pair in pairs.itertuples(index=False)
            ]
            feature_df = pd.concat([feature_df.reset_index(drop=True), pd.DataFrame(extras)], axis=1)
        selected = list(base_columns)
        for column in feature_df.columns:
            if group_for_feature(column) in feature_set.extra_groups:
                selected.append(column)
        selected = list(dict.fromkeys(selected))
        return feature_df, selected

    return compute


def _metrics(labels: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict[str, float]:
    predictions = (probabilities >= threshold).astype(int)
    return {
        "average_precision": float(average_precision_score(labels, probabilities)),
        "roc_auc": float(roc_auc_score(labels, probabilities)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "threshold": float(threshold),
    }


def _train_validation_only(feature_df: pd.DataFrame, feature_columns: list[str], seed: int, progress_callback):
    train_df = feature_df[feature_df["split_name"] == "train"]
    val_df = feature_df[feature_df["split_name"] == "val"]
    scaler = StandardScaler().fit(train_df[feature_columns].fillna(0.0))
    train_x = scaler.transform(train_df[feature_columns].fillna(0.0))
    val_x = scaler.transform(val_df[feature_columns].fillna(0.0))
    models = [
        ("logreg", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=seed, verbose=1)),
        ("gb", GradientBoostingClassifier(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=seed, verbose=1)),
        ("rf", RandomForestClassifier(n_estimators=400, max_depth=18, min_samples_leaf=2, class_weight="balanced_subsample", n_jobs=1, random_state=seed, verbose=1)),
    ]
    leaderboard = []
    fitted = {}
    for index, (name, model) in enumerate(models):
        start_progress = 70 + index * 8
        progress_callback(start_progress, f"fitting {name} ({index + 1}/3)")
        model.fit(train_x, train_df["label"])
        raw = model.predict_proba(val_x)[:, 1]
        leaderboard.append({"model": name, "validation_average_precision": float(average_precision_score(val_df["label"], raw)), "validation_roc_auc": float(roc_auc_score(val_df["label"], raw))})
        fitted[name] = model
        progress_callback(start_progress + 8, f"completed {name} ({index + 1}/3)")
    leaderboard.sort(key=lambda row: (row["validation_average_precision"], row["validation_roc_auc"]), reverse=True)
    model_name = leaderboard[0]["model"]
    model = fitted[model_name]
    val_raw = model.predict_proba(val_x)[:, 1]
    progress_callback(95, "calibrating selected model and choosing validation threshold")
    calibrator = IsotonicRegression(out_of_bounds="clip").fit(val_raw, val_df["label"])
    val_probabilities = calibrator.predict(val_raw)
    threshold, _ = __import__("identity_resolution.stages.train_base", fromlist=["choose_threshold"]).choose_threshold(val_df["label"].to_numpy(), val_probabilities)
    return model_name, model, scaler, calibrator, leaderboard, _metrics(val_df["label"].to_numpy(), val_probabilities, threshold)


def _run_training(args: argparse.Namespace) -> Path:
    output_root = Path(args.output_root)
    feature_set = resolve_feature_set(args.feature_set, tuple(filter(None, args.include_groups.split(","))))
    run_id = args.run_id or feature_set.name
    run_dir = output_root / run_id
    _write_status(run_dir, "PREPARING", "loading profiles and experiment configuration", 0)
    try:
        base = _configure_base(run_dir)
        from identity_resolution.stages import train_multimodal as suite

        base.set_seed(args.seed)
        profiles = base.load_profiles()
        if args.offline_text_only:
            _write_status(run_dir, "PREPARING", "aligning local MiniLM embedding cache", 3)
            _prepare_offline_embeddings(base, profiles)
            base.compute_features = _feature_computer(base.compute_features, feature_set)
        else:
            _write_status(run_dir, "PREPARING", "building image-context profile cache", 3)
            image_df, caption_embeddings = suite.build_image_profile_features(base, profiles)
            wrapped_make, multimodal_compute = suite.make_multimodal_wrappers(base, "image_context", image_df, caption_embeddings)
            base.make_profile_bundle = wrapped_make
            base.compute_features = _feature_computer(multimodal_compute, feature_set)
        _write_status(run_dir, "FEATURES", "building entity-aware pairs and feature matrix", 5)
        build_args = argparse.Namespace(seed=args.seed, random_neg_ratio=args.random_neg_ratio, hard_neg_ratio=args.hard_neg_ratio)
        def feature_progress(completed: int, total: int) -> None:
            progress = 5 + round(65 * completed / max(total, 1))
            _write_status(run_dir, "FEATURES", f"computed {completed:,}/{total:,} pair feature rows", progress)

        base.FEATURE_PROGRESS_HOOK = feature_progress
        try:
            feature_df, feature_columns, leakage = base.build_dataset(profiles, build_args)
        finally:
            base.FEATURE_PROGRESS_HOOK = None
        _write_status(run_dir, "TRAINING", "feature matrix complete; preparing model matrices", 70)
        model_name, model, scaler, calibrator, leaderboard, validation_metrics = _train_validation_only(
            feature_df,
            feature_columns,
            args.seed,
            lambda progress, detail: _write_status(run_dir, "TRAINING", detail, progress),
        )
        _write_status(run_dir, "VALIDATING", "saving validation-selected model and feature manifest", 98)
        feature_df.to_parquet(run_dir / "feature_matrix.parquet", index=False)
        manifest = {"schema_version": SCHEMA_VERSION, "feature_set": feature_set.name, "feature_columns": feature_columns, "feature_groups": {column: group_for_feature(column) for column in feature_columns}}
        (run_dir / "feature_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        for name, value in {"model.pkl": model, "scaler.pkl": scaler, "calibrator.pkl": calibrator}.items():
            with (run_dir / name).open("wb") as handle:
                pickle.dump(value, handle)
        config = {**vars(args), "output_root": str(args.output_root)}
        result = {"run_id": run_id, "model": model_name, "leaderboard": leaderboard, "validation_metrics": validation_metrics, "leakage_report": leakage, "config": config}
        (run_dir / "validation_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        _write_status(run_dir, "DONE", "validation complete; test remains sealed", 100)
        print(json.dumps({"run_id": run_id, **validation_metrics}, indent=2))
    except Exception as exc:
        _write_status(run_dir, "FAILED", str(exc))
        raise
    return run_dir


def _evaluate_test(run_dir: Path) -> None:
    feature_df = pd.read_parquet(run_dir / "feature_matrix.parquet")
    manifest = json.loads((run_dir / "feature_manifest.json").read_text(encoding="utf-8"))
    with (run_dir / "model.pkl").open("rb") as handle:
        model = pickle.load(handle)
    with (run_dir / "scaler.pkl").open("rb") as handle:
        scaler = pickle.load(handle)
    with (run_dir / "calibrator.pkl").open("rb") as handle:
        calibrator = pickle.load(handle)
    validation = json.loads((run_dir / "validation_metrics.json").read_text(encoding="utf-8"))
    test_df = feature_df[feature_df["split_name"] == "test"].copy()
    probabilities = calibrator.predict(model.predict_proba(scaler.transform(test_df[manifest["feature_columns"]].fillna(0.0)))[:, 1])
    metrics = _metrics(test_df["label"].to_numpy(), probabilities, validation["validation_metrics"]["threshold"])
    scores = test_df[["profile_row_id_a", "profile_row_id_b", "label", "pair_type", "split_name"]].copy()
    scores["probability"] = probabilities
    scores.to_parquet(run_dir / "test_scores.parquet", index=False)
    (run_dir / "test_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validation-first name-similarity ablation runner")
    parser.add_argument("--feature-set", choices=["N0", "N1", "N2", "N3", "N4", "N5", "N6", "N7"], required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--include-groups", default="")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--random-neg-ratio", type=float, default=0.75)
    parser.add_argument("--hard-neg-ratio", type=float, default=2.0)
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT / "artifacts" / "evaluation" / "name_similarity")
    parser.add_argument("--offline-text-only", action="store_true", help="Use aligned local MiniLM embeddings and skip image-caption features.")
    parser.add_argument("--evaluate-test", action="store_true")
    args = parser.parse_args()
    run_dir = args.output_root / (args.run_id or args.feature_set)
    if args.evaluate_test:
        _evaluate_test(run_dir)
    else:
        _run_training(args)


if __name__ == "__main__":
    main()