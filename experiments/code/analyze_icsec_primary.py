"""Post-process the ICSEC primary reproduction without exporting profile text."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.code import exp_r1_ga_redecision as ga
from experiments.code.exp_lib import (
    BLOCKING_MISSED,
    PROFILES,
    build_nested_entity_split,
    nested_split_constants,
)
from experiments.code.run_gb_transformer_experiments import (
    FEATURE17_COLS,
    GA_WEIGHTS,
    KEY_COLS,
    labels_for,
    manual_decision,
    metric_with_cost,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def decision_metrics(decision: np.ndarray, labels: np.ndarray, constants: dict[str, int], weights: tuple[float, float, float]) -> dict[str, float]:
    match = decision == 2
    no_match = decision == 0
    tp = int((match & (labels == 1)).sum()) + constants["tp_exact"]
    fp = int((match & (labels == 0)).sum()) + constants["fp_exact"]
    fn = int((no_match & (labels == 1)).sum()) + constants["fn_blocking"]
    review = int((decision == 1).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / constants["total_pos"] if constants["total_pos"] else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    cfp, cfn, creview = weights
    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "REVIEW": review,
        "precision": precision,
        "recall": recall,
        "F1": f1,
        "weighted_cost": cfp * fp + cfn * fn + creview * review,
    }


def bootstrap_pairwise(
    decisions: dict[str, np.ndarray], labels: np.ndarray, constants: dict[str, int], weights: tuple[float, float, float], n_boot: int, seed: int,
) -> pd.DataFrame:
    """Conditional paired bootstrap of scored test candidates.

    Exact-tier and blocking-missed constants remain fixed. This estimates
    conditional uncertainty attributable to the scored sealed test instances.
    """
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    comparisons = [("GB-17", "GB-18"), ("GB-18", "GB-18-GA")]
    draws: dict[tuple[str, str], dict[str, list[float]]] = {
        pair: {metric: [] for metric in ("precision", "recall", "F1", "FP", "FN", "REVIEW", "weighted_cost")}
        for pair in comparisons
    }
    n = len(labels)
    for _ in range(n_boot):
        index = rng.integers(0, n, n)
        computed = {
            name: decision_metrics(code[index], labels[index], constants, weights)
            for name, code in decisions.items()
        }
        for left, right in comparisons:
            for metric in draws[(left, right)]:
                draws[(left, right)][metric].append(computed[right][metric] - computed[left][metric])
    for (left, right), metric_draws in draws.items():
        observed_left = decision_metrics(decisions[left], labels, constants, weights)
        observed_right = decision_metrics(decisions[right], labels, constants, weights)
        for metric, values in metric_draws.items():
            low, high = np.quantile(values, [0.025, 0.975])
            rows.append({
                "comparison": f"{right} - {left}",
                "metric": metric,
                "observed_difference": observed_right[metric] - observed_left[metric],
                "ci95_low": float(low),
                "ci95_high": float(high),
                "bootstrap_samples": n_boot,
                "bootstrap_type": "paired conditional bootstrap; exact/blocking constants fixed",
            })
    return pd.DataFrame(rows)


def availability(frame: pd.DataFrame, column: str) -> np.ndarray:
    return frame[column].fillna("").astype(str).str.strip().ne("").to_numpy()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=Path("experiments/icsec_final/primary_reproduction"))
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    analysis_dir = run_dir.parent / "statistical_analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "decisions").mkdir(parents=True, exist_ok=True)
    (run_dir / "error_analysis").mkdir(parents=True, exist_ok=True)

    cache = pd.read_parquet("experiments/scored_pairs_enriched.parquet")
    feat17 = pd.read_parquet("experiments/pair_features17.parquet")
    bert = pd.read_parquet("experiments/pair_bert_cos.parquet")
    assigned, split_manifest = build_nested_entity_split(cache, seed=42)
    scored = assigned.loc[assigned.decision_source != "AUTO_EXACT"].copy()
    work = scored[[*KEY_COLS, "experiment_split", "name_sim"]].merge(feat17, on=KEY_COLS, validate="one_to_one").merge(bert, on=KEY_COLS, validate="one_to_one")
    test = work.loc[work.experiment_split == "test"].copy().reset_index(drop=True)
    labels = labels_for(assigned, test[KEY_COLS], "test", allow_test=True)
    constants = nested_split_constants(assigned, seed=42)["test"]

    prob17 = pd.read_parquet(run_dir / "gb17_probabilities.parquet")
    prob18 = pd.read_parquet(run_dir / "gb18_probabilities.parquet")
    test = test.merge(prob17[[*KEY_COLS, "probability_gb17"]], on=KEY_COLS, validate="one_to_one").merge(prob18[[*KEY_COLS, "probability_gb18"]], on=KEY_COLS, validate="one_to_one")
    # The cached decisioning signal and the reconstructed feature share a name.
    # The experiment runner validates their equality before fitting; use the
    # cached decisioning signal to reproduce the GA policy exactly.
    test["name_sim"] = test["name_sim_x"]
    summary = json.loads((run_dir / "summary.json").read_text())
    genome_d = summary["selected_ga"]["selected_genome"]
    genome = np.array([genome_d[key] for key in ("t_m", "t_r", "c_promote", "c_demote")], dtype=float)
    decisions = {
        "GB-17": manual_decision(test.probability_gb17.to_numpy()),
        "GB-18": manual_decision(test.probability_gb18.to_numpy()),
        "GB-18-GA": ga.decide_code(test.probability_gb18.to_numpy(), test.name_sim.to_numpy(), genome),
    }
    code_to_name = np.array(["NO_MATCH", "REVIEW", "MATCH"])
    decision_export = test[[*KEY_COLS, "probability_gb17", "probability_gb18", "name_sim"]].copy()
    decision_export["actual"] = labels
    for method, code in decisions.items():
        decision_export[f"decision_{method.lower().replace('-', '_')}"] = code_to_name[code]
    decision_export.to_parquet(run_dir / "decisions" / "sealed_test_decisions.parquet", index=False)

    objective_weights = (GA_WEIGHTS.fp, GA_WEIGHTS.fn, GA_WEIGHTS.review)
    raw_metrics = []
    for method, code in decisions.items():
        raw_metrics.append({"method": method, **decision_metrics(code, labels, constants, objective_weights)})
    pd.DataFrame(raw_metrics).to_csv(run_dir / "raw_metrics_recomputed.csv", index=False)

    ci = bootstrap_pairwise(decisions, labels, constants, objective_weights, args.bootstrap_samples, 20260902)
    ci.to_csv(analysis_dir / "paired_bootstrap_ci.csv", index=False)

    scenarios = []
    for cfp in (1.0, 2.0, 5.0, 10.0):
        for creview in (0.02, 0.1, 0.5):
            per_method = {method: decision_metrics(code, labels, constants, (cfp, 1.0, creview)) for method, code in decisions.items()}
            winner = min(per_method, key=lambda method: per_method[method]["weighted_cost"])
            for method, metrics in per_method.items():
                scenarios.append({
                    "C_FP": cfp,
                    "C_FN": 1.0,
                    "C_REVIEW": creview,
                    "method": method,
                    "weighted_cost": metrics["weighted_cost"],
                    "winner_by_frozen_policy_cost": winner,
                    "post_hoc_only": True,
                    "note": "Policies were selected under historical C_FP=5,C_FN=1,C_REVIEW=0.02; this table does not retune GA or reuse test data for selection.",
                })
    sensitivity = pd.DataFrame(scenarios)
    sensitivity.to_csv(run_dir.parent / "cost_sensitivity.csv", index=False)

    profiles = pd.read_csv(PROFILES, usecols=["profile_row_id", "platform", "userName", "fullName", "bio", "location", "externalUrl_clean"], keep_default_na=False)
    profiles = profiles.set_index("profile_row_id")
    for side in ("a", "b"):
        index = test[f"profile_id_{side}"].to_numpy()
        for field in ("platform", "userName", "fullName", "bio", "location", "externalUrl_clean"):
            test[f"{field}_{side}"] = profiles[field].reindex(index).to_numpy()
    pair_names = test.apply(lambda row: " x ".join(sorted((str(row.platform_a), str(row.platform_b)))), axis=1)

    platform_rows = []
    for method, code in decisions.items():
        for pair in sorted(pair_names.unique()):
            mask = pair_names.to_numpy() == pair
            # These counts are scored-candidate counts only; no allocation of global exact/block constants.
            match = code[mask] == 2
            no_match = code[mask] == 0
            y = labels[mask]
            tp, fp, fn, review = int((match & (y == 1)).sum()), int((match & (y == 0)).sum()), int((no_match & (y == 1)).sum()), int((code[mask] == 1).sum())
            precision = tp / (tp + fp) if tp + fp else 0.0
            recall = tp / int((y == 1).sum()) if int((y == 1).sum()) else 0.0
            platform_rows.append({"method": method, "platform_pair": pair, "scope": "scored candidates only", "rows": int(mask.sum()), "positive_pairs": int((y == 1).sum()), "TP": tp, "FP": fp, "FN": fn, "REVIEW": review, "precision": precision, "recall": recall, "F1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0})
    pd.DataFrame(platform_rows).to_csv(run_dir / "error_analysis" / "platform_pair_scored_metrics.csv", index=False)

    # Aggregate missingness and failure categories only; do not export profile text.
    name_available = (availability(test, "userName_a") | availability(test, "fullName_a")) & (availability(test, "userName_b") | availability(test, "fullName_b"))
    bio_available = availability(test, "bio_a") & availability(test, "bio_b")
    location_available = availability(test, "location_a") & availability(test, "location_b")
    url_available = availability(test, "externalUrl_clean_a") & availability(test, "externalUrl_clean_b")
    strata = pd.DataFrame({"name_available": name_available, "bio_available": bio_available, "location_available": location_available, "url_available": url_available, "name_similarity_band": pd.cut(test.name_sim, bins=[-0.01, 0.5, 0.8, 1.0], labels=["low_<0.5", "medium_0.5-0.8", "high_>=0.8"]), "actual": labels})
    missing_rows = []
    for method, code in decisions.items():
        decision_name = code_to_name[code]
        frame = strata.copy()
        frame["decision"] = decision_name
        for grouping in ("name_available", "bio_available", "location_available", "url_available", "name_similarity_band"):
            grouped = frame.groupby([grouping, "decision", "actual"], observed=False).size().reset_index(name="count")
            grouped.insert(0, "method", method)
            grouped.insert(1, "grouping", grouping)
            missing_rows.append(grouped)
    pd.concat(missing_rows, ignore_index=True).to_csv(run_dir / "error_analysis" / "missingness_and_similarity_strata.csv", index=False)

    primary = decisions["GB-18-GA"]
    category_rows = []
    categories = {
        "false_positive_match": (primary == 2) & (labels == 0),
        "false_negative_no_match": (primary == 0) & (labels == 1),
        "review_positive": (primary == 1) & (labels == 1),
        "review_negative": (primary == 1) & (labels == 0),
    }
    for category, mask in categories.items():
        for band in ("low_<0.5", "medium_0.5-0.8", "high_>=0.8"):
            category_rows.append({"category": category, "attribute": "name_similarity_band", "value": band, "count": int((mask & (strata.name_similarity_band.astype(str).to_numpy() == band)).sum())})
        for field, available_values in {"name": name_available, "bio": bio_available, "location": location_available, "url": url_available}.items():
            category_rows.append({"category": category, "attribute": f"both_{field}_available", "value": "true", "count": int((mask & available_values).sum())})
            category_rows.append({"category": category, "attribute": f"both_{field}_available", "value": "false", "count": int((mask & ~available_values).sum())})
    pd.DataFrame(category_rows).to_csv(run_dir / "error_analysis" / "failure_category_counts.csv", index=False)

    bm = pd.read_csv(BLOCKING_MISSED)
    total_positive = 29243
    missed = 3312
    retrieval = pd.DataFrame([{
        "all_cross_platform_pairs": 449149239,
        "candidate_workflow_pairs": 2086245,
        "candidate_space_reduction": 1 - 2086245 / 449149239,
        "total_cross_platform_positive_pairs": total_positive,
        "candidate_covered_positive_pairs": total_positive - missed,
        "blocking_missed_positive_pairs": missed,
        "retrieval_recall": (total_positive - missed) / total_positive,
        "blocking_miss_artifact_rows": len(bm),
        "note": "Primary nested test metrics include split-specific blocking-missed false-negative constants; this table uses the cross-platform project scope.",
    }])
    retrieval.to_csv(run_dir / "error_analysis" / "candidate_retrieval_decomposition.csv", index=False)

    manifest = {
        "analysis_script": str(Path(__file__).resolve()),
        "analysis_script_sha256": sha256(Path(__file__).resolve()),
        "run_dir": str(run_dir),
        "source_hashes": {name: sha256(Path(path)) for name, path in {"cache": "experiments/scored_pairs_enriched.parquet", "features17": "experiments/pair_features17.parquet", "bert_cos": "experiments/pair_bert_cos.parquet", "profiles": PROFILES, "blocking_missed": BLOCKING_MISSED}.items()},
        "bootstrap_samples": args.bootstrap_samples,
        "privacy": "No usernames, names, biographies, locations, URLs, profile images, or other profile text are exported by this analysis.",
    }
    (analysis_dir / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
