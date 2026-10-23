"""Independent evaluator for authoritative row-level decision artifacts."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "experiments" / "icsec_final" / "authoritative_run"
SEEDS = [101, 202, 303]
METHODS = ["GB-17", "GB-18", "GB-18-GA"]


def metric(frame: pd.DataFrame) -> dict[str, float | int]:
    tp = int(((frame.actual == 1) & (frame.decision == "MATCH")).sum())
    fp = int(((frame.actual == 0) & (frame.decision == "MATCH")).sum())
    fn = int(((frame.actual == 1) & (frame.decision == "NO_MATCH")).sum())
    review = int((frame.decision == "REVIEW").sum())
    review_positive = int(((frame.actual == 1) & (frame.decision == "REVIEW")).sum())
    positives = int((frame.actual == 1).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / positives if positives else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    utility = 2 * fp + fn + 0.1 * review
    assert tp + fn + review_positive == positives
    assert fp + int(((frame.actual == 0) & (frame.decision != "MATCH")).sum()) == int((frame.actual == 0).sum())
    return {"TP": tp, "FP": fp, "FN": fn, "REVIEW": review,
            "precision": precision, "recall": recall, "F1": f1,
            "utility": utility}


def main() -> None:
    scope = json.loads((OUT / "candidates" / "candidate_scope.json").read_text())
    assert scope["exact_tier_pairs"] + scope["model_scored_candidate_pairs"] == scope["workflow_candidate_pairs"]
    assert scope["candidate_covered_cross_platform_positives"] + scope["cross_platform_blocking_misses"] == scope["cross_platform_positives"]
    rows = []
    checks = []
    for seed in SEEDS:
        seed_dir = OUT / f"outer_{seed}"
        for method in METHODS:
            md = seed_dir / method.replace("-", "_")
            exact = pd.read_parquet(md / "exact_tier_decisions.parquet")
            scored = pd.read_parquet(md / "model_scored_decisions.parquet")
            blocking = pd.read_parquet(md / "blocking_missed_positives.parquet")
            workflow = pd.read_parquet(md / "workflow_decisions.parquet")
            assert set(exact.columns) >= {"profile_id_a", "profile_id_b", "actual", "decision", "scope"}
            assert set(scored.columns) >= {"profile_id_a", "profile_id_b", "actual", "decision", "scope"}
            assert set(blocking.columns) >= {"profile_id_a", "profile_id_b", "actual", "decision", "scope"}
            assert len(set(map(tuple, exact[["profile_id_a", "profile_id_b"]].to_numpy())) & set(map(tuple, scored[["profile_id_a", "profile_id_b"]].to_numpy()))) == 0
            assert len(set(map(tuple, exact[["profile_id_a", "profile_id_b"]].to_numpy())) & set(map(tuple, blocking[["profile_id_a", "profile_id_b"]].to_numpy()))) == 0
            assert len(set(map(tuple, scored[["profile_id_a", "profile_id_b"]].to_numpy())) & set(map(tuple, blocking[["profile_id_a", "profile_id_b"]].to_numpy()))) == 0
            expected = pd.concat([exact, scored, blocking], ignore_index=True).sort_values(["profile_id_a", "profile_id_b", "scope"]).reset_index(drop=True)
            observed = workflow.sort_values(["profile_id_a", "profile_id_b", "scope"]).reset_index(drop=True)
            assert expected.equals(observed), f"workflow decomposition mismatch: {seed}/{method}"
            assert (exact.decision == "MATCH").all()
            assert (blocking.actual == 1).all() and (blocking.decision == "NO_MATCH").all()
            m = metric(workflow)
            rows.append({"outer_seed": seed, "method": method, **m,
                         "exact_rows": len(exact), "model_scored_rows": len(scored),
                         "blocking_missed_rows": len(blocking), "workflow_rows": len(workflow),
                         "workflow_positive_rows": int(workflow.actual.sum())})
            checks.append({"outer_seed": seed, "method": method, "confusion_identity": True,
                           "decomposition_identity": True, "workflow_rows": len(workflow)})
    raw = pd.DataFrame(rows)
    raw.to_csv(OUT / "raw_metrics_by_outer.csv", index=False)
    numeric = ["precision", "recall", "F1", "FP", "FN", "REVIEW", "utility"]
    agg = raw.groupby("method", sort=False)[numeric].agg(["mean", "std"]).reset_index()
    agg.to_csv(OUT / "aggregate_metrics.csv", index=False)
    (OUT / "consistency_report.json").write_text(json.dumps({
        "status": "PASS", "scope_invariants": scope["invariants"],
        "row_level_checks": checks, "rows_evaluated": len(raw),
        "metric_source": "new authoritative row-level decisions only",
    }, indent=2), encoding="utf-8")
    print(raw.to_string(index=False))
    print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
