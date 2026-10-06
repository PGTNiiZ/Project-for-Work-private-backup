"""Permutation attribution for a frozen name-similarity experiment run."""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, f1_score

from identity_resolution.settings import PROJECT_ROOT


def _probabilities(model, scaler, calibrator, frame: pd.DataFrame, columns: list[str]) -> np.ndarray:
    matrix = scaler.transform(frame[columns].fillna(0.0))
    return calibrator.predict(model.predict_proba(matrix)[:, 1])


def _confidence_interval(values: list[float]) -> tuple[float, float]:
    return float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))


def run_attribution(run_dir: Path, repetitions: int, seed: int) -> pd.DataFrame:
    test_report = run_dir / "test_metrics.json"
    if not test_report.exists():
        raise FileNotFoundError("Run --evaluate-test first; attribution is only valid for a frozen test evaluation.")
    manifest = json.loads((run_dir / "feature_manifest.json").read_text(encoding="utf-8"))
    feature_columns = manifest["feature_columns"]
    groups = manifest["feature_groups"]
    feature_df = pd.read_parquet(run_dir / "feature_matrix.parquet")
    test_df = feature_df[feature_df["split_name"] == "test"].reset_index(drop=True)
    labels = test_df["label"].to_numpy()
    threshold = json.loads((run_dir / "test_metrics.json").read_text(encoding="utf-8"))["threshold"]
    with (run_dir / "model.pkl").open("rb") as handle:
        model = pickle.load(handle)
    with (run_dir / "scaler.pkl").open("rb") as handle:
        scaler = pickle.load(handle)
    with (run_dir / "calibrator.pkl").open("rb") as handle:
        calibrator = pickle.load(handle)
    baseline = _probabilities(model, scaler, calibrator, test_df, feature_columns)
    baseline_ap = float(average_precision_score(labels, baseline))
    baseline_f1 = float(f1_score(labels, baseline >= threshold, zero_division=0))

    units = {f"feature:{column}": [column] for column in feature_columns}
    for group in sorted(set(groups.values())):
        units[f"group:{group}"] = [column for column in feature_columns if groups[column] == group]
    rng = np.random.default_rng(seed)
    rows = []
    for unit, columns in units.items():
        ap_deltas, f1_deltas = [], []
        for _ in range(repetitions):
            shuffled = test_df.copy()
            permutation = rng.permutation(len(shuffled))
            shuffled.loc[:, columns] = shuffled.loc[permutation, columns].to_numpy()
            probabilities = _probabilities(model, scaler, calibrator, shuffled, feature_columns)
            ap_deltas.append(baseline_ap - float(average_precision_score(labels, probabilities)))
            f1_deltas.append(baseline_f1 - float(f1_score(labels, probabilities >= threshold, zero_division=0)))
        ap_low, ap_high = _confidence_interval(ap_deltas)
        f1_low, f1_high = _confidence_interval(f1_deltas)
        unit_type, unit_name = unit.split(":", 1)
        rows.append({
            "unit_type": unit_type,
            "unit": unit_name,
            "feature_count": len(columns),
            "ap_delta_mean": float(np.mean(ap_deltas)),
            "ap_delta_ci_low": ap_low,
            "ap_delta_ci_high": ap_high,
            "f1_delta_mean": float(np.mean(f1_deltas)),
            "f1_delta_ci_low": f1_low,
            "f1_delta_ci_high": f1_high,
            "repetitions": repetitions,
            "baseline_ap": baseline_ap,
            "baseline_f1": baseline_f1,
        })
    report = pd.DataFrame(rows).sort_values(["unit_type", "ap_delta_mean"], ascending=[True, False])
    report.to_csv(run_dir / "permutation_importance.csv", index=False)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Permutation feature attribution for a frozen test run")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repetitions", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT / "artifacts" / "evaluation" / "name_similarity")
    args = parser.parse_args()
    if args.repetitions < 2:
        raise ValueError("--repetitions must be at least 2")
    report = run_attribution(args.output_root / args.run_id, args.repetitions, args.seed)
    print(report[report["unit_type"] == "group"].to_string(index=False))


if __name__ == "__main__":
    main()