"""Build full-candidate evidence and optimize a sealed feature-aware policy.

The frozen production probability is never retrained here. This workflow exports
policy evidence for every model-scored candidate, selects a policy on validation,
then evaluates the frozen winner on test exactly once and projects it to all rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from rapidfuzz import fuzz

from experiments.code import exp_lib
from experiments.code.run_feature_aware_ga_pipeline import (
    GROUPS,
    coverage_audit,
    decision_metrics,
    decisions,
    derive_decisioning_features,
    load_profile_evidence,
    optimize_weighted_policy,
    selector_experiments,
    status,
)
from identity_resolution.core.business_cost import CRM_COST_POLICY_VERSION, CRM_COST_WEIGHTS
from identity_resolution.settings import PROJECT_ROOT


SCORED_SOURCE = PROJECT_ROOT / "experiments" / "scored_pairs_enriched.parquet"
PROFILE_EMBEDDINGS = PROJECT_ROOT / "experiments" / "profile_embeddings_minilm.npy"
PROFILE_EMBEDDING_IDS = PROJECT_ROOT / "experiments" / "profile_embeddings_minilm_ids.npy"
IMAGE_PROFILES = PROJECT_ROOT / "data" / "final" / "profiles_with_images.parquet"
DEFAULT_OUTPUT = PROJECT_ROOT / "artifacts" / "decisioning" / "feature_aware_ga" / "full_2m"
EXPECTED_TOTAL_ROWS = 2_086_245
EXPECTED_SCORED_ROWS = 2_073_842
EXPECTED_EXACT_ROWS = 12_403
EXPORT_COLUMNS = [
    "split_name",
    "pair_type",
    "label",
    "probability",
    "profile_row_id_a",
    "profile_row_id_b",
    *[f"{group}_score" for group in GROUPS],
    *[f"{group}_available" for group in GROUPS],
    "original_decision",
    "decision_source",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_state(output: Path, phase: str, completed_rows: int, total_rows: int, detail: str) -> None:
    progress = 5 + round(70 * completed_rows / max(total_rows, 1))
    record = {
        "phase": phase,
        "progress": progress,
        "completed_rows": int(completed_rows),
        "total_rows": int(total_rows),
        "detail": detail,
        "pid": os.getpid(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    (output / "status.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"[{progress:3d}%] {phase}: {detail}", flush=True)


def load_scored_source(max_rows: int | None = None) -> tuple[pd.DataFrame, dict[str, object]]:
    required = {"profile_id_a", "profile_id_b", "score", "decision", "decision_source", "actual", "split"}
    scored_all = pd.read_parquet(SCORED_SOURCE)
    missing = sorted(required - set(scored_all.columns))
    if missing:
        raise ValueError(f"Full scored cache is missing columns: {missing}")
    if scored_all.duplicated(["profile_id_a", "profile_id_b"]).any():
        raise ValueError("Full scored cache contains duplicate pair keys")
    source_counts = scored_all["decision_source"].value_counts().to_dict()
    exact_rows = int(source_counts.get("AUTO_EXACT", 0))
    scored = scored_all[scored_all["decision_source"] != "AUTO_EXACT"].copy()
    if max_rows is None:
        if len(scored_all) != EXPECTED_TOTAL_ROWS or len(scored) != EXPECTED_SCORED_ROWS or exact_rows != EXPECTED_EXACT_ROWS:
            raise ValueError(
                "Full-cache row counts changed: "
                f"total={len(scored_all):,}, scored={len(scored):,}, exact={exact_rows:,}"
            )
    else:
        scored = scored.head(max_rows).copy()
    scored = scored.reset_index(drop=True)
    metadata = {
        "source_rows": int(len(scored_all)),
        "exported_scored_rows": int(len(scored)),
        "exact_rows": exact_rows,
        "source_decision_counts": {str(key): int(value) for key, value in source_counts.items()},
        "source_split_counts": {str(key): int(value) for key, value in scored_all["split"].value_counts().items()},
        "exported_split_counts": {str(key): int(value) for key, value in scored["split"].value_counts().items()},
        "scope": "full" if max_rows is None else f"smoke_first_{max_rows}",
    }
    return scored, metadata


def prepare_text_context(output: Path):
    from identity_resolution.stages import train_base as base

    profiles = base.load_profiles()
    selected_ids = profiles.loc[profiles["profile_id"].notna(), "profile_row_id"].astype(int).tolist()
    embeddings = np.load(PROFILE_EMBEDDINGS, mmap_mode="r")
    embedding_ids = np.load(PROFILE_EMBEDDING_IDS, mmap_mode="r")
    if len(embeddings) != len(embedding_ids):
        raise ValueError("MiniLM embeddings and ID index have different row counts")
    positions = {int(profile_id): index for index, profile_id in enumerate(embedding_ids)}
    missing = [profile_id for profile_id in selected_ids if profile_id not in positions]
    if missing:
        raise ValueError(f"MiniLM cache is missing {len(missing)} eligible profiles")
    cache_dir = output / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    aligned_path = cache_dir / "sbert_embeddings_aligned.npy"
    if not aligned_path.exists():
        aligned = np.asarray(embeddings[[positions[profile_id] for profile_id in selected_ids]], dtype=np.float32)
        np.save(aligned_path, aligned)
    aligned_shape = np.load(aligned_path, mmap_mode="r").shape
    if aligned_shape != (len(selected_ids), embeddings.shape[1]):
        raise ValueError(f"Aligned embedding cache has unexpected shape {aligned_shape}")
    base.SBERT_EMBEDDINGS_PATH = aligned_path
    bundle = base.make_profile_bundle(profiles)
    return base, profiles, bundle


def clean_image_text(value: object) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"", "nan", "none"} else text


def load_image_lookup(profiles: pd.DataFrame) -> dict[int, dict[str, str]]:
    image = pd.read_parquet(IMAGE_PROFILES, columns=["profile_id", "platform", "phash", "caption_en", "has_image"])
    image["profile_id"] = image["profile_id"].map(clean_image_text)
    image["platform"] = image["platform"].map(lambda value: clean_image_text(value).lower())
    image["phash"] = image["phash"].map(clean_image_text)
    image["caption_en"] = image["caption_en"].map(lambda value: clean_image_text(value).lower())
    image["has_image"] = pd.to_numeric(image["has_image"], errors="coerce").fillna(0).astype(np.int8)
    image = image.sort_values(["has_image", "phash", "caption_en"], ascending=False).drop_duplicates(["profile_id", "platform"])
    by_key = image.set_index(["profile_id", "platform"])[["phash", "caption_en", "has_image"]].to_dict("index")
    lookup: dict[int, dict[str, str]] = {}
    for row in profiles[["profile_row_id", "user_folder", "platform"]].itertuples(index=False):
        key = (clean_image_text(row.user_folder), clean_image_text(row.platform).lower())
        value = by_key.get(key)
        if value:
            lookup[int(row.profile_row_id)] = {
                "phash": clean_image_text(value["phash"]),
                "caption": clean_image_text(value["caption_en"]).lower(),
            }
    return lookup


def hash_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    distance = sum(char_left != char_right for char_left, char_right in zip(left, right))
    return 1.0 - distance / max(len(left), len(right), 1)


def add_image_evidence(
    raw_features: pd.DataFrame,
    pairs: pd.DataFrame,
    records: dict[int, dict],
    image_lookup: dict[int, dict[str, str]],
) -> pd.DataFrame:
    rows = []
    for pair in pairs.itertuples(index=False):
        left_id = int(pair.profile_row_id_a)
        right_id = int(pair.profile_row_id_b)
        left_image = image_lookup.get(left_id, {})
        right_image = image_lookup.get(right_id, {})
        left_caption = left_image.get("caption", "")
        right_caption = right_image.get("caption", "")
        left_record = records[left_id]
        right_record = records[right_id]
        rows.append({
            "image_both_local": int(bool(left_image.get("phash")) and bool(right_image.get("phash"))),
            "image_caption_any": int(bool(left_caption) or bool(right_caption)),
            "image_phash_sim": hash_similarity(left_image.get("phash", ""), right_image.get("phash", "")),
            "image_dhash_sim": 0.0,
            "image_caption_bio_sbert_cross": 0.0,
            "image_caption_fullname_token_cross": max(
                fuzz.token_sort_ratio(left_caption, right_record["fullName_norm"]) / 100.0 if left_caption else 0.0,
                fuzz.token_sort_ratio(right_caption, left_record["fullName_norm"]) / 100.0 if right_caption else 0.0,
            ),
            "image_caption_username_token_cross": max(
                fuzz.token_sort_ratio(left_caption, right_record["userName_norm"]) / 100.0 if left_caption else 0.0,
                fuzz.token_sort_ratio(right_caption, left_record["userName_norm"]) / 100.0 if right_caption else 0.0,
            ),
        })
    return pd.concat([raw_features.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def compute_evidence_chunk(
    source_chunk: pd.DataFrame,
    base,
    profile_bundle: dict[str, object],
    profile_evidence: pd.DataFrame,
    image_lookup: dict[int, dict[str, str]],
) -> pd.DataFrame:
    pairs = pd.DataFrame({
        "profile_row_id_a": source_chunk["profile_id_a"].to_numpy(dtype=np.int64),
        "profile_row_id_b": source_chunk["profile_id_b"].to_numpy(dtype=np.int64),
        "label": source_chunk["actual"].to_numpy(dtype=np.int8),
        "pair_type": "candidate",
        "split_name": source_chunk["split"].to_numpy(),
        "profile_id": -1,
    })
    raw_features, _ = base.compute_features(pairs, profile_bundle)
    raw_features = add_image_evidence(raw_features, pairs, profile_bundle["records"], image_lookup)
    raw_features["probability"] = source_chunk["score"].to_numpy(dtype=float)
    evidence = derive_decisioning_features(raw_features, profile_evidence, include_model_features=False)
    evidence["original_decision"] = source_chunk["decision"].to_numpy()
    evidence["decision_source"] = source_chunk["decision_source"].to_numpy()
    return evidence[EXPORT_COLUMNS]


def chunk_path(output: Path, start: int, stop: int) -> Path:
    return output / "feature_chunks" / f"decisioning_features_{start:09d}_{stop:09d}.parquet"


def manifest_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def validate_chunk(path: Path, expected_rows: int) -> None:
    if pq.ParquetFile(path).metadata.num_rows != expected_rows:
        raise ValueError(f"Existing chunk has wrong row count: {path}")
    schema = set(pq.read_schema(path).names)
    missing = sorted(set(EXPORT_COLUMNS) - schema)
    if missing:
        raise ValueError(f"Existing chunk is missing columns {missing}: {path}")


def export_features(output: Path, chunk_size: int, max_rows: int | None) -> dict[str, object]:
    scored, source_metadata = load_scored_source(max_rows)
    feature_dir = output / "feature_chunks"
    feature_dir.mkdir(parents=True, exist_ok=True)
    status(output, "PREFLIGHT", 2, f"validated source cache; exporting {len(scored):,} scored candidates")
    base, profiles, profile_bundle = prepare_text_context(output)
    profile_evidence = load_profile_evidence()
    image_lookup = load_image_lookup(profiles)
    completed = 0
    chunk_records = []
    for start in range(0, len(scored), chunk_size):
        stop = min(start + chunk_size, len(scored))
        path = chunk_path(output, start, stop)
        if path.exists():
            validate_chunk(path, stop - start)
        else:
            evidence = compute_evidence_chunk(
                scored.iloc[start:stop], base, profile_bundle, profile_evidence, image_lookup
            )
            temporary = path.with_suffix(".tmp.parquet")
            evidence.to_parquet(temporary, index=False)
            temporary.replace(path)
            validate_chunk(path, stop - start)
        completed += stop - start
        chunk_records.append({"path": manifest_path(path), "start": start, "stop": stop, "rows": stop - start})
        write_state(output, "EXPORT", completed, len(scored), f"completed chunk {len(chunk_records)}: {start:,}-{stop:,}")
    manifest = {
        "version": "full_feature_aware_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": str(SCORED_SOURCE.relative_to(PROJECT_ROOT)),
        "source_sha256": sha256_file(SCORED_SOURCE),
        **source_metadata,
        "chunk_size": int(chunk_size),
        "chunk_count": len(chunk_records),
        "chunks": chunk_records,
        "evidence_groups": list(GROUPS),
        "image_evidence": "pHash plus caption-to-opposite-name token similarity; unavailable caption-SBERT and dHash are explicit zeros",
        "missingness": "availability masks are stored separately; missing evidence is not interpreted as similarity zero by policy",
    }
    (output / "full_feature_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def load_exported_features(output: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    manifest_path = output / "full_feature_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Run export first; missing {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_sha256") != sha256_file(SCORED_SOURCE):
        raise ValueError("Frozen scored source changed after feature export; existing chunks are stale")
    chunks = []
    expected_start = 0
    for record in manifest["chunks"]:
        if int(record["start"]) != expected_start or int(record["stop"]) <= expected_start:
            raise ValueError(f"Feature chunk ranges are not contiguous at {record}")
        path = Path(record["path"])
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        validate_chunk(path, int(record["rows"]))
        chunks.append(pd.read_parquet(path))
        expected_start = int(record["stop"])
    if expected_start != int(manifest["exported_scored_rows"]):
        raise ValueError("Feature chunks do not cover the complete exported row range")
    cache = pd.concat(chunks, ignore_index=True)
    if len(cache) != int(manifest["exported_scored_rows"]):
        raise ValueError("Exported feature row count does not match manifest")
    if cache.duplicated(["profile_row_id_a", "profile_row_id_b"]).any():
        raise ValueError("Exported feature chunks contain duplicate pair keys")
    actual_splits = {str(key): int(value) for key, value in cache["split_name"].value_counts().items()}
    expected_splits = manifest.get("exported_split_counts")
    if expected_splits is None and manifest.get("scope") == "full":
        source_splits = pd.read_parquet(SCORED_SOURCE, columns=["decision_source", "split"])
        source_splits = source_splits[source_splits["decision_source"] != "AUTO_EXACT"]
        expected_splits = {str(key): int(value) for key, value in source_splits["split"].value_counts().items()}
    if expected_splits is None or actual_splits != expected_splits:
        raise ValueError(f"Exported split counts changed: cache={actual_splits}, manifest={expected_splits}")
    return cache, manifest


def freeze_policy(selector_winner: dict, weighted: dict) -> dict[str, object]:
    selector_cost = float(selector_winner["validation_cost"])
    weighted_cost = float(weighted["validation_metrics"]["cost"])
    if weighted_cost < selector_cost:
        return {
            "policy": "weighted_evidence",
            "validation_cost": weighted_cost,
            "active_groups": weighted["active_groups"],
            "thresholds": weighted["thresholds"],
            "weights": weighted["weights"],
        }
    return {
        "policy": f"selector:{selector_winner['guard']}",
        "validation_cost": selector_cost,
        "guard": selector_winner["guard"],
        "thresholds": json.loads(selector_winner["genome"]),
    }


def apply_frozen_policy(cache: pd.DataFrame, policy: dict[str, object]) -> np.ndarray:
    thresholds = np.asarray(policy["thresholds"], dtype=float)
    if policy["policy"] == "weighted_evidence":
        groups = list(policy["active_groups"])
        scores = cache[[f"{group}_score" for group in groups]].to_numpy(float)
        masks = cache[[f"{group}_available" for group in groups]].to_numpy(float)
        weights = np.asarray([policy["weights"][group] for group in groups], dtype=float)
        numerator = (scores * masks * weights).sum(axis=1)
        denominator = (masks * weights).sum(axis=1)
        evidence = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0)
        available = (denominator > 0).astype(np.int8)
    else:
        guard = str(policy["guard"])
        if guard == "score_only":
            evidence = np.zeros(len(cache))
            available = np.zeros(len(cache), dtype=np.int8)
        else:
            evidence = cache[f"{guard}_score"].to_numpy(float)
            available = cache[f"{guard}_available"].to_numpy(np.int8)
    return decisions(cache["probability"].to_numpy(float), evidence, available, thresholds)


def system_metrics(values: dict[str, int | float]) -> dict[str, int | float]:
    result = dict(values)
    result["cost"] = CRM_COST_WEIGHTS.cost(
        fp=int(result["FP"]),
        fn=int(result["FN"]),
        review=int(result["REVIEW"]),
    )
    return result


def write_full_report(
    output: Path,
    manifest: dict[str, object],
    audit: pd.DataFrame,
    selector: pd.DataFrame,
    policy: dict[str, object],
    result: dict[str, object],
) -> None:
    coverage_lines = "\n".join(
        f"| {row.group} | {row.availability_coverage:.2%} | {int(row.available_positive_support):,} | {row.high_score_positive_rate:.4f} |"
        for row in audit.itertuples(index=False)
    )
    selector_lines = "\n".join(
        f"| {row.guard} | {row.validation_cost:.2f} | {row.validation_precision:.4f} | {row.validation_recall:.4f} | {int(row.validation_fp)} | {int(row.validation_fn)} | {int(row.validation_review):,} |"
        for row in selector.itertuples(index=False)
    )
    text = f"""# Full 2M Feature-Aware GA Report

## Scope

- Source rows: {manifest['source_rows']:,}
- Model-scored candidates: {manifest['exported_scored_rows']:,}
- Exact tier held constant: {manifest['exact_rows']:,}
- Feature chunks: {manifest['chunk_count']:,}
- Policy selection: validation only
- Held-out test: evaluated once after policy freeze

## Evidence coverage on validation

| Group | Coverage | Positive support | High-score positive rate |
|---|---:|---:|---:|
{coverage_lines}

## Selector GA on validation

| Guard | Cost | Precision | Recall | FP | FN | REVIEW |
|---|---:|---:|---:|---:|---:|---:|
{selector_lines}

## Frozen winner

```json
{json.dumps(policy, indent=2)}
```

## Sealed test and full projection

```json
{json.dumps(result, indent=2)}
```

## Interpretation

ผล test แบบ `system_test_metrics` รวม exact-tier constants และ blocking-missed false negatives แล้ว ส่วน `scored_test_metrics` วัดเฉพาะคู่ที่ model เคย score. Full projection ใช้ policy ที่ freeze แล้วกับ scored candidates ทั้งหมดโดยไม่มีการ tune เพิ่ม

Image evidence รุ่นนี้ใช้ pHash และ caption-to-name token similarity เท่านั้น เนื่องจาก historical caption embedding cache ไม่มีและ dimension ของ legacy paths ไม่สอดคล้องกัน ข้อจำกัดนี้ถูกบันทึกใน manifest และ missing evidence ถูกควบคุมด้วย availability masks
"""
    (output / "FULL_2M_REPORT_TH.md").write_text(text, encoding="utf-8")


def optimize_full_policy(
    output: Path,
    *,
    feature_source: Path | None = None,
    evaluate_test: bool = True,
) -> dict[str, object]:
    cache, manifest = load_exported_features(feature_source or output)
    if manifest["scope"] != "full":
        raise ValueError("Optimization is blocked for smoke exports; rerun export without --max-rows")
    status(output, "AUDIT", 76, f"loaded {len(cache):,} scored candidates from resumable chunks")
    audit = coverage_audit(cache, output)
    selector, selector_winner = selector_experiments(cache, audit, output)
    weighted = optimize_weighted_policy(cache, audit, output)
    policy = freeze_policy(selector_winner, weighted)
    policy["cost_policy_version"] = CRM_COST_POLICY_VERSION
    policy["cost_weights"] = CRM_COST_WEIGHTS.as_dict()
    policy["selection_rule"] = "lower validation decision cost; no test metric was read before freeze"
    (output / "frozen_policy.json").write_text(json.dumps(policy, indent=2), encoding="utf-8")
    selection = {
        "policy": policy,
        "feature_source": str((feature_source or output).resolve()),
        "population_rows": int(len(cache)),
        "selection_split": "val",
        "test_evaluated": False,
    }
    (output / "validation_selection.json").write_text(json.dumps(selection, indent=2), encoding="utf-8")
    if not evaluate_test:
        status(output, "DONE", 100, "validation policy frozen; test intentionally not evaluated")
        return selection
    status(output, "SEALED_TEST", 97, f"applying frozen {policy['policy']} policy once")
    all_decisions = apply_frozen_policy(cache, policy)
    source = pd.read_parquet(SCORED_SOURCE)
    scored_source = source[source["decision_source"] != "AUTO_EXACT"].reset_index(drop=True)
    if not np.array_equal(cache["profile_row_id_a"].to_numpy(), scored_source["profile_id_a"].to_numpy()) or not np.array_equal(cache["profile_row_id_b"].to_numpy(), scored_source["profile_id_b"].to_numpy()):
        raise ValueError("Feature export order no longer matches the frozen scored source")
    constants = exp_lib.split_constants(source)
    test_mask = cache["split_name"].to_numpy() == "test"
    test_decisions = all_decisions[test_mask]
    test_labels = cache.loc[test_mask, "label"].to_numpy(np.int8)
    result = {
        "policy": policy,
        "scored_test_metrics": decision_metrics(test_decisions, test_labels),
        "system_test_metrics": system_metrics(exp_lib.evaluate(test_decisions, test_labels, constants["test"])),
        "full_projection_metrics": system_metrics(exp_lib.evaluate(all_decisions, cache["label"].to_numpy(np.int8), constants["full"])),
        "test_evaluation_count": 1,
    }
    (output / "sealed_test_and_projection.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_full_report(output, manifest, audit, selector, policy, result)
    status(output, "DONE", 100, "full feature-aware GA, sealed test, projection, and Thai report completed")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run resumable feature-aware GA over the full 2.07M scored-candidate population.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--stage", choices=("all", "export", "optimize"), default="all")
    parser.add_argument("--chunk-size", type=int, default=50_000)
    parser.add_argument("--max-rows", type=int, help="Smoke-test export only; optimization is intentionally blocked.")
    parser.add_argument("--feature-source", type=Path, help="Reuse a completed full feature cache from another run directory.")
    parser.add_argument("--evaluate-test", action="store_true", help="Evaluate the previously held-out test after validation freeze. Omit for new protocol development.")
    args = parser.parse_args()
    if args.chunk_size <= 0:
        parser.error("--chunk-size must be positive")
    if args.max_rows is not None and args.max_rows <= 0:
        parser.error("--max-rows must be positive")
    if args.feature_source is not None and args.stage in {"all", "export"}:
        parser.error("--feature-source is valid only with --stage optimize")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    required = [SCORED_SOURCE, PROFILE_EMBEDDINGS, PROFILE_EMBEDDING_IDS, IMAGE_PROFILES]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing full-run prerequisites: {missing}")
    if args.stage in {"all", "export"}:
        export_features(output, args.chunk_size, args.max_rows)
    if args.stage in {"all", "optimize"}:
        if args.max_rows is not None:
            parser.error("--max-rows cannot be combined with optimization")
        optimize_full_policy(
            output,
            feature_source=args.feature_source.resolve() if args.feature_source else None,
            evaluate_test=args.evaluate_test,
        )


if __name__ == "__main__":
    main()