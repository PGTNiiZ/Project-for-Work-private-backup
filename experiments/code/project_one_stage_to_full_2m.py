"""Project validation-frozen one-stage policies over the complete 2.086M pair cache."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from experiments.code.run_feature_aware_ga_pipeline import (
    ONE_STAGE_POLICY_FEATURES,
    decision_metrics,
    decisions,
    one_stage_decisions,
    one_stage_policy_score,
)
from experiments.code.run_one_stage_weighted_ga_experiment import (
    POLICY_LEGACY_NAME,
    POLICY_ONE_STAGE,
    POLICY_SCORE_ONLY,
    expanded_metrics,
)
from identity_resolution.settings import PROJECT_ROOT


SOURCE = PROJECT_ROOT / "experiments" / "scored_pairs_enriched.parquet"
FEATURE_SOURCE = PROJECT_ROOT / "artifacts" / "decisioning" / "feature_aware_ga" / "full_2m"
FREEZE_SOURCE = (
    PROJECT_ROOT / "artifacts" / "decisioning" / "feature_aware_ga"
    / "one_stage_weighted_full_20260914" / "frozen_policies_before_test.json"
)
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "artifacts" / "decisioning" / "feature_aware_ga"
    / "one_stage_weighted_full_2m_20260914"
)
DECISION_NAMES = np.asarray(["NO_MATCH", "REVIEW", "MATCH"])


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def score_and_mask_matrices(chunk: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Build the frozen eight-input schema; absent evidence stays unavailable."""
    scores, masks, absent = [], [], []
    for feature in ONE_STAGE_POLICY_FEATURES:
        if feature == "probability":
            scores.append(chunk["probability"].to_numpy(float))
            masks.append(np.ones(len(chunk), dtype=float))
            continue
        score_column = f"{feature}_score"
        mask_column = f"{feature}_available"
        if score_column not in chunk or mask_column not in chunk:
            scores.append(np.zeros(len(chunk), dtype=float))
            masks.append(np.zeros(len(chunk), dtype=float))
            absent.append(feature)
        else:
            scores.append(chunk[score_column].to_numpy(float))
            masks.append(chunk[mask_column].to_numpy(float))
    return np.column_stack(scores), np.column_stack(masks), sorted(set(absent))


def run_projection(output: Path, feature_source: Path, freeze_source: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    feature_manifest = json.loads((feature_source / "full_feature_manifest.json").read_text(encoding="utf-8"))
    freeze = json.loads(freeze_source.read_text(encoding="utf-8"))
    source_hash = sha256_file(SOURCE)
    if source_hash != feature_manifest["source_sha256"]:
        raise RuntimeError("full feature cache does not match scored_pairs_enriched.parquet")

    source = pd.read_parquet(SOURCE)
    scored_mask = source["decision_source"].to_numpy() != "AUTO_EXACT"
    scored_source = source.loc[scored_mask].reset_index(drop=True)
    expected_rows = int(feature_manifest["exported_scored_rows"])
    if len(scored_source) != expected_rows:
        raise RuntimeError("model-scored source count differs from feature manifest")

    genomes = {
        policy: np.asarray(record["genome"], dtype=float)
        for policy, record in freeze["policies"].items()
    }
    projected = {policy: [] for policy in genomes}
    projected_scores = {policy: [] for policy in genomes}
    absent_features: set[str] = set()
    cursor = 0
    for index, item in enumerate(feature_manifest["chunks"], start=1):
        path = Path(item["path"])
        chunk = pd.read_parquet(path)
        stop = cursor + len(chunk)
        expected = scored_source.iloc[cursor:stop]
        if not np.array_equal(chunk["profile_row_id_a"].to_numpy(), expected["profile_id_a"].to_numpy()):
            raise RuntimeError(f"left pair keys differ in chunk {path.name}")
        if not np.array_equal(chunk["profile_row_id_b"].to_numpy(), expected["profile_id_b"].to_numpy()):
            raise RuntimeError(f"right pair keys differ in chunk {path.name}")
        scores, masks, absent = score_and_mask_matrices(chunk)
        absent_features.update(absent)
        for policy, genome in genomes.items():
            if policy == POLICY_LEGACY_NAME:
                decision = decisions(
                    chunk["probability"].to_numpy(float),
                    chunk["name_score"].to_numpy(float),
                    chunk["name_available"].to_numpy(np.int8),
                    genome,
                )
                score = chunk["probability"].to_numpy(float)
            else:
                decision = one_stage_decisions(scores, masks, genome)
                score = one_stage_policy_score(scores, masks, genome[2:])
            projected[policy].append(decision.astype(np.int8))
            projected_scores[policy].append(score.astype(np.float32))
        cursor = stop
        print(f"[{index:02d}/{len(feature_manifest['chunks']):02d}] projected {cursor:,}/{expected_rows:,}", flush=True)
    if cursor != expected_rows:
        raise RuntimeError("projected feature row count is incomplete")

    full_decisions: dict[str, np.ndarray] = {}
    full_scores: dict[str, np.ndarray] = {}
    for policy in genomes:
        values = np.full(len(source), 2, dtype=np.int8)  # Keep exact tier frozen as MATCH.
        values[scored_mask] = np.concatenate(projected[policy])
        scores = source["score"].to_numpy(dtype=np.float32, copy=True)
        scores[scored_mask] = np.concatenate(projected_scores[policy])
        full_decisions[policy] = values
        full_scores[policy] = scores
    original = source["decision"].map({"NO_MATCH": 0, "REVIEW": 1, "MATCH": 2}).to_numpy(np.int8)
    full_decisions["original_pipeline"] = original
    full_scores["original_pipeline"] = source["score"].to_numpy(np.float32)

    export = source[["profile_id_a", "profile_id_b", "split", "actual", "decision_source", "score"]].copy()
    for policy, values in full_decisions.items():
        export[f"{policy}_score"] = full_scores[policy]
        export[f"{policy}_decision_code"] = values
        export[f"{policy}_decision"] = DECISION_NAMES[values]
    export_path = output / "full_2m_pair_decisions.parquet"
    export.to_parquet(export_path, index=False)

    labels = source["actual"].to_numpy(np.int8)
    rows = []
    for split_name in ("val", "test", "drop", "all"):
        selected = np.ones(len(source), dtype=bool) if split_name == "all" else source["split"].to_numpy() == split_name
        for policy, values in full_decisions.items():
            rows.append({
                "split": split_name,
                "policy": policy,
                "rows": int(selected.sum()),
                "positive_support": int(labels[selected].sum()),
                **expanded_metrics(values[selected], labels[selected]),
            })
    metrics = pd.DataFrame(rows)
    metrics.to_csv(output / "full_2m_metrics_by_split.csv", index=False)

    coverage_rows = []
    for feature in ONE_STAGE_POLICY_FEATURES:
        if feature == "probability":
            available_rows = int(scored_mask.sum())
        elif f"{feature}_available" in export.columns:
            available_rows = int(export[f"{feature}_available"].sum())
        else:
            available_rows = 0
        coverage_rows.append({
            "feature": feature,
            "available_scored_rows": available_rows,
            "scored_rows": expected_rows,
            "coverage": available_rows / expected_rows,
            "absent_from_full_cache": feature in absent_features,
        })
    coverage = pd.DataFrame(coverage_rows)
    # Derive exact coverage from feature chunks without retaining their columns in the output.
    coverage_lookup = {feature: 0 for feature in ONE_STAGE_POLICY_FEATURES[1:]}
    for item in feature_manifest["chunks"]:
        schema = set(pq.ParquetFile(Path(item["path"])).schema.names)
        columns = [f"{feature}_available" for feature in coverage_lookup if f"{feature}_available" in schema]
        if columns:
            part = pd.read_parquet(Path(item["path"]), columns=columns)
            for column in columns:
                coverage_lookup[column.removesuffix("_available")] += int(part[column].sum())
    for index, row in coverage.iterrows():
        feature = str(row.feature)
        if feature in coverage_lookup:
            coverage.loc[index, "available_scored_rows"] = coverage_lookup[feature]
            coverage.loc[index, "coverage"] = coverage_lookup[feature] / expected_rows
    coverage.to_csv(output / "full_2m_feature_coverage.csv", index=False)

    overall = metrics[metrics.split == "all"].sort_values(["cost", "fp", "fn", "review"])
    lines = "\n".join(
        f"| {row.policy} | {row.cost:,.1f} | {row.precision:.4f} | {row.recall:.4f} | {row.f1:.4f} | {int(row.fp):,} | {int(row.fn):,} | {int(row.review):,} |"
        for row in overall.itertuples(index=False)
    )
    one_stage_splits = metrics[metrics.policy == POLICY_ONE_STAGE]
    split_lines = "\n".join(
        f"| {row.split} | {int(row.rows):,} | {row.cost:,.1f} | {row.precision:.4f} | {row.recall:.4f} | {row.f1:.4f} | {int(row.fp):,} | {int(row.fn):,} | {int(row.review):,} |"
        for row in one_stage_splits.itertuples(index=False)
    )
    frozen_one_stage = freeze["policies"].get(POLICY_ONE_STAGE, {})
    genome = np.asarray(frozen_one_stage.get("genome", []), dtype=float)
    validation_rows = int(freeze.get("validation_rows", 0))
    if len(genome) == 2 + len(ONE_STAGE_POLICY_FEATURES):
        threshold_text = f"t_match={genome[0]:.6f}, t_review={genome[1]:.6f}"
        weight_lines = "\n".join(
            f"| {feature} | {weight:.6f} |"
            for feature, weight in zip(ONE_STAGE_POLICY_FEATURES, genome[2:])
        )
    else:
        threshold_text = "ไม่พบ genome แบบ 10 genes"
        weight_lines = "| - | - |"
    selection_text = (
        f"GA จูนและเลือก policy จาก validation population ของ full cache จำนวน {validation_rows:,} model-scored คู่"
        if validation_rows else
        "นำ policy ที่ freeze จาก labeled validation ภายนอกมา project โดยไม่ tune เพิ่ม"
    )
    report = f"""# One-Stage Weighted GA บนข้อมูล 2.086 ล้านคู่

{selection_text} แล้ว freeze ก่อนเปิด test จากนั้น project กับ
`scored_pairs_enriched.parquet` ทั้งหมด {len(source):,} คู่ ประกอบด้วย model-scored
{expected_rows:,} คู่และ exact tier {int((~scored_mask).sum()):,} คู่. Exact tier คงคำตัดสิน MATCH เดิม.

Thresholds: `{threshold_text}`

| Feature | Frozen weight |
|---|---:|
{weight_lines}

## ผลรวมทุกคู่

| Policy | Cost | Precision | Recall | F1 | FP | FN | REVIEW |
|---|---:|---:|---:|---:|---:|---:|---:|
{lines}

## One-Stage แยกตาม Split ของ Full Cache

| Split | Rows | Cost | Precision | Recall | F1 | FP | FN | REVIEW |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{split_lines}

Full feature cache รุ่นนี้ไม่มี feature `social` และ location ไม่มี observation; ทั้งสองตัวจึง inactive.
สูตร normalize น้ำหนักใหม่เฉพาะ feature ที่มีข้อมูลต่อคู่. Test ถูกอ่านหลังเขียน freeze manifest และ
ไม่ได้ใช้ย้อนกลับไปปรับ genome.
"""
    (output / "FULL_2M_ONE_STAGE_REPORT_TH.md").write_text(report, encoding="utf-8")
    result = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": str(SOURCE),
        "source_sha256": source_hash,
        "feature_manifest": str(feature_source / "full_feature_manifest.json"),
        "freeze_manifest": str(freeze_source),
        "freeze_manifest_sha256": sha256_file(freeze_source),
        "total_rows": int(len(source)),
        "model_scored_rows": expected_rows,
        "exact_rows": int((~scored_mask).sum()),
        "projection_tuning_performed": False,
        "frozen_policy_validation_rows": validation_rows,
        "absent_policy_features": sorted(absent_features),
        "overall_metrics": overall.to_dict(orient="records"),
        "artifacts": {
            "report": "FULL_2M_ONE_STAGE_REPORT_TH.md",
            "pair_decisions": export_path.name,
            "metrics_by_split": "full_2m_metrics_by_split.csv",
            "feature_coverage": "full_2m_feature_coverage.csv",
        },
    }
    (output / "full_2m_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--feature-source", type=Path, default=FEATURE_SOURCE)
    parser.add_argument("--freeze-source", type=Path, default=FREEZE_SOURCE)
    args = parser.parse_args()
    result = run_projection(args.output.resolve(), args.feature_source.resolve(), args.freeze_source.resolve())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
