"""Independently close the authoritative v2 evidence package."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
SEEDS = (101, 202, 303)
METHODS = ("GB17_B0", "B0", "B1", "B2", "B3")


def metrics(frame: pd.DataFrame) -> dict[str, float | int]:
    decision, actual = frame.decision.to_numpy(), frame.actual.to_numpy()
    tp = int(((decision == 2) & (actual == 1)).sum())
    fp = int(((decision == 2) & (actual == 0)).sum())
    fn = int(((decision == 0) & (actual == 1)).sum())
    review = int((decision == 1).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"TP": tp, "FP": fp, "FN": fn, "REVIEW": review, "precision": precision,
            "recall": recall, "F1": f1, "U": 2 * fp + fn + 0.1 * review}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(directory: Path) -> None:
    for line in (directory / "SHA256SUMS.txt").read_text().splitlines():
        expected, relative = line.split("  ", 1)
        path = directory / relative
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"hash mismatch: {path}")


def main() -> None:
    per_seed: dict[str, dict] = {}
    policies: dict[str, dict] = {}
    decompositions: dict[str, dict] = {}
    for seed in SEEDS:
        directory = ROOT / "scientific_outputs" / f"outer_{seed}"
        verify_manifest(directory)
        runner = json.loads((directory / "summary.json").read_text())
        independent = json.loads((directory / "independent_metrics.json").read_text())
        if runner != independent:
            raise RuntimeError(f"runner/independent JSON mismatch for {seed}")
        recomputed: dict[str, dict] = {}
        decomposition: dict[str, dict] = {}
        for method in METHODS:
            workflow = pd.read_parquet(directory / "decisions" / f"{method}_workflow.parquet")
            if set(workflow.metric_scope) != {"WORKFLOW"}:
                raise RuntimeError(f"workflow scope marker mismatch for {seed}/{method}")
            if workflow.pair_key.duplicated().any():
                raise RuntimeError(f"duplicate workflow key for {seed}/{method}")
            value = metrics(workflow)
            recomputed[method] = value
            if json.dumps(value, sort_keys=True) != json.dumps(runner[method], sort_keys=True):
                raise RuntimeError(f"metric mismatch for {seed}/{method}")
            counts = workflow.pair_type.value_counts().to_dict()
            if set(counts) != {"AUTO_EXACT", "MODEL_SCORED", "BLOCKING_MISS"}:
                raise RuntimeError(f"workflow decomposition incomplete for {seed}/{method}")
            misses = workflow.loc[workflow.pair_type == "BLOCKING_MISS"]
            if not ((misses.actual == 1) & (misses.decision == 0)).all():
                raise RuntimeError(f"blocking misses not counted as FN for {seed}/{method}")
            decomposition[method] = {key: int(value) for key, value in counts.items()}
        if recomputed != runner:
            raise RuntimeError(f"full recomputation mismatch for {seed}")
        audit = json.loads((directory / "label_access_audit.json").read_text())
        if any(not row["allowed"] or row["phase"] != "FINAL_EVALUATION" for row in audit):
            raise RuntimeError(f"label access violation for {seed}")
        fairness = json.loads((directory / "fairness.json").read_text())
        if not fairness["passed"] or fairness["budget"] != 12000:
            raise RuntimeError(f"fairness failure for {seed}")
        policy = json.loads((directory / "policies.json").read_text())
        if not (policy["metadata"]["B2"]["realized_evaluations"] == policy["metadata"]["B3"]["realized_evaluations"] == 12000):
            raise RuntimeError(f"realized budget failure for {seed}")
        per_seed[str(seed)] = recomputed
        policies[str(seed)] = policy
        decompositions[str(seed)] = decomposition

    aggregate: dict[str, dict] = {}
    fields = ("precision", "recall", "F1", "FP", "FN", "REVIEW", "U")
    for method in METHODS:
        aggregate[method] = {}
        for field in fields:
            values = np.array([per_seed[str(seed)][method][field] for seed in SEEDS], dtype=float)
            aggregate[method][field] = {"mean": float(values.mean()), "sample_sd": float(values.std(ddof=1))}

    scope = json.loads((ROOT / "preflight" / "candidate_scope.json").read_text())
    expected = {"profiles_eligible": 36804, "all_platform_positives": 29247, "cross_platform_positives": 29243,
                "same_platform_positives": 4, "possible_cross_platform_pairs": 449149239, "exact_tier_pairs": 12403,
                "model_scored_candidate_pairs": 2073842, "workflow_candidate_pairs": 2086245,
                "candidate_covered_cross_platform_positives": 25931, "cross_platform_blocking_misses": 3312}
    if any(scope[key] != value for key, value in expected.items()) or not all(scope["invariants"].values()):
        raise RuntimeError("global candidate scope mismatch")

    evidence = {"seeds": per_seed, "aggregate": aggregate, "policies": policies, "workflow_decomposition": decompositions,
                "candidate_scope": {key: scope[key] for key in expected}, "pre_final_test_label_reads": 0,
                "independent_recomputation": "PASS", "B2_B3_fairness": "PASS"}
    (ROOT / "final_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")

    lines = ["# Authoritative ICSEC 2026 V2 results", "", "This file records only the frozen V2 evidence family.", "",
             "## Per-seed workflow results", "",
             "| Seed | Method | Precision | Recall | F1 | FP | FN | Review | U |",
             "|---:|---|---:|---:|---:|---:|---:|---:|---:|"]
    for seed in SEEDS:
        for method in METHODS:
            row = per_seed[str(seed)][method]
            lines.append(f"| {seed} | {method} | {row['precision']:.4f} | {row['recall']:.4f} | {row['F1']:.4f} | {row['FP']} | {row['FN']} | {row['REVIEW']} | {row['U']:.1f} |")
    lines += ["", "## Mean and sample standard deviation", "", "| Method | Precision | Recall | F1 | FP | FN | Review | U |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for method in METHODS:
        row = aggregate[method]
        fmt = lambda field, digits: f"{row[field]['mean']:.{digits}f} ± {row[field]['sample_sd']:.{digits}f}"
        lines.append(f"| {method} | {fmt('precision',4)} | {fmt('recall',4)} | {fmt('F1',4)} | {fmt('FP',1)} | {fmt('FN',1)} | {fmt('REVIEW',1)} | {fmt('U',1)} |")
    lines += ["", "## Frozen controls", "", "B0 fixed; B1 deterministic simple-policy Sobol; B2 expanded-policy Sobol; B3 identical expanded-policy GA.",
              "B2 and B3 each used exactly 12,000 objective evaluations per seed. PRE-FINAL TEST LABEL READS = 0.", "",
              "Candidate scope: 36,804 eligible profiles; 29,243 cross-platform positives; 2,086,245 workflow candidates; 25,931 covered positives; 3,312 blocking misses.", "",
              "Independent recomputation, workflow decomposition, per-seed hash verification, and B2/B3 fairness: PASS.", ""]
    (ROOT / "FINAL_RESULTS.md").write_text("\n".join(lines))

    manifest = {}
    for path in ROOT.rglob("*"):
        if path.is_file() and path.name != "SHA256SUMS.txt" and "__pycache__" not in path.parts:
            manifest[str(path.relative_to(ROOT))] = sha256(path)
    (ROOT / "SHA256SUMS.txt").write_text("".join(f"{digest}  {path}\n" for path, digest in sorted(manifest.items())))
    verify_manifest(ROOT)
    print(json.dumps({"status": "PASS", "aggregate": aggregate, "pre_final_test_label_reads": 0}, indent=2))


if __name__ == "__main__":
    main()
