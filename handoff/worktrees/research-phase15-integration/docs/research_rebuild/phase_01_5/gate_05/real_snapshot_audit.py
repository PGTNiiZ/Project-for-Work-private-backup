"""Read-only Phase 1.5 snapshot/feature lineage audit; writes only the report path."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

PHASE15 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PHASE15 / "gate_05"))
sys.path.insert(0, str(PHASE15 / "gate_06"))
from snapshot_split import route_pair_iter, verify_snapshot_split
from pair_adapter import canonical_pair_key

EXPECTED_SNAPSHOT_SHA256 = "17a95f754cb7f43cc28fd63a7ced2dcf59c57945d5a782fa9e3a057d45b182b1"
TOKENIZER_FILES = ("tokenizer.json", "vocab.txt", "tokenizer_config.json", "special_tokens_map.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pair_batches(path: Path):
    parquet = pq.ParquetFile(path)
    for batch in parquet.iter_batches(
        columns=["profile_row_id_a", "profile_row_id_b", "pair_type"], batch_size=50000
    ):
        columns = batch.to_pydict()
        yield from zip(columns["profile_row_id_a"], columns["profile_row_id_b"], columns["pair_type"])


def build_report(source_root: Path) -> dict:
    snapshot = source_root / "data_for_project/normalized_profiles_with_profile_id.csv"
    audit = verify_snapshot_split(snapshot, expected_sha256=EXPECTED_SNAPSHOT_SHA256,
                                  expected_unmapped_rows=3)
    v2 = source_root / "experiments/icsec_final/authoritative_run_v2"
    candidate_path = v2 / "candidates/workflow.parquet"
    routing = route_pair_iter(pair_batches(candidate_path), audit["profile_entities"],
                              audit["entity_roles"])

    registry = json.loads((Path(__file__).resolve().parents[1] / "gate_04/FEATURE_REGISTRY.json")
                          .read_text(encoding="utf-8"))
    gb17_path, bert_path = v2 / "features/gb17.parquet", v2 / "features/bert_cos.parquet"
    gb17_schema = pq.ParquetFile(gb17_path).schema_arrow.names
    bert_schema = pq.ParquetFile(bert_path).schema_arrow.names
    if gb17_schema != ["profile_row_id_a", "profile_row_id_b", *registry["ordered_columns"]]:
        raise ValueError("persisted Feature17 schema differs from registry")
    if bert_schema != ["profile_row_id_a", "profile_row_id_b", "bert_cos"]:
        raise ValueError("persisted Feature18 artifact must contain endpoints and bert_cos only")
    gb17_keys = pq.read_table(gb17_path, columns=["profile_row_id_a", "profile_row_id_b"])
    bert_keys = pq.read_table(bert_path, columns=["profile_row_id_a", "profile_row_id_b"])
    pair_order_equal = (np.array_equal(gb17_keys.column(0).to_numpy(), bert_keys.column(0).to_numpy())
                        and np.array_equal(gb17_keys.column(1).to_numpy(), bert_keys.column(1).to_numpy()))
    if not pair_order_equal:
        raise ValueError("persisted Feature17 and Feature18 endpoint order mismatch")
    bert_values = pq.read_table(bert_path, columns=["bert_cos"])["bert_cos"].to_numpy()
    if not np.isfinite(bert_values).all() or (bert_values < -1.0001).any() or (bert_values > 1.0001).any():
        raise ValueError("persisted bert_cos contains non-finite or out-of-range values")

    profile_ids_path = source_root / "experiments/profile_embeddings_minilm_ids.npy"
    embeddings_path = source_root / "experiments/profile_embeddings_minilm.npy"
    profile_ids = np.load(profile_ids_path, allow_pickle=False)
    embeddings = np.load(embeddings_path, mmap_mode="r", allow_pickle=False)
    snapshot_ids = pd.read_csv(snapshot, usecols=["profile_row_id"])["profile_row_id"].astype("int64").to_numpy()
    ids_match = np.array_equal(profile_ids, snapshot_ids)
    if not ids_match:
        raise ValueError("MiniLM embedding profile IDs do not match snapshot row ordering")
    norms = np.linalg.norm(embeddings, axis=1)

    # Recompute a bounded sample of bert_cos from persisted normalized vectors.
    id_to_row = {int(value): index for index, value in enumerate(profile_ids)}
    sample_pairs = gb17_keys.slice(0, 16).to_pydict()
    sample_stored = pq.read_table(bert_path, columns=["bert_cos"]).slice(0, 16)["bert_cos"].to_numpy()
    sample_cosine = np.asarray([
        np.dot(embeddings[id_to_row[int(a)]], embeddings[id_to_row[int(b)]])
        for a, b in zip(sample_pairs["profile_row_id_a"], sample_pairs["profile_row_id_b"])
    ])
    sample_cosine_match = bool(np.allclose(sample_stored, sample_cosine, atol=2e-6, rtol=0.0))
    if not sample_cosine_match:
        raise ValueError("sampled bert_cos values differ from normalized profile-vector dot products")

    # Verify the source-defined one-way pair key can be rejoined to explicit
    # candidate endpoint columns. Blocking misses are absent by construction.
    decision_path = v2 / "scientific_outputs/outer_101/decisions/B0_workflow.parquet"
    pair_key_source = v2 / "real_adapters.py"
    decisions = pq.read_table(decision_path, columns=["pair_key", "pair_type"]).to_pandas()
    candidate_keys = set(decisions.loc[decisions.pair_type != "BLOCKING_MISS", "pair_key"].astype(str))
    found: set[str] = set()
    duplicates = 0
    for batch in pq.ParquetFile(candidate_path).iter_batches(
        columns=["profile_row_id_a", "profile_row_id_b"], batch_size=50000
    ):
        values = batch.to_pydict()
        for a, b in zip(values["profile_row_id_a"], values["profile_row_id_b"]):
            key = canonical_pair_key(a, b)
            if key in candidate_keys:
                if key in found:
                    duplicates += 1
                found.add(key)
    if found != candidate_keys or duplicates:
        raise ValueError("historical exact/scored pair-key endpoint join is incomplete or ambiguous")

    model_dir = (Path.home() / ".cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2"
                 / "snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41")
    tokenizer_hashes = {name: sha256_file(model_dir / name) for name in TOKENIZER_FILES}
    tokenizer_bundle_hash = hashlib.sha256(json.dumps(
        tokenizer_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    pooling = json.loads((model_dir / "1_Pooling/config.json").read_text(encoding="utf-8"))
    modules = json.loads((model_dir / "modules.json").read_text(encoding="utf-8"))
    model_weight_sha = sha256_file(model_dir / "model.safetensors")
    expected_contract = json.loads((PHASE15 / "gate_04/FEATURE18_CONTRACT_V1.json").read_text(encoding="utf-8"))
    if model_dir.name != expected_contract["model"]["revision"]:
        raise ValueError("local MiniLM revision differs from pinned Feature18 contract")
    if model_weight_sha != expected_contract["model"]["weights_sha256"]:
        raise ValueError("local MiniLM weights differ from pinned Feature18 contract")
    if tokenizer_hashes != expected_contract["model"]["tokenizer_files"]:
        raise ValueError("local tokenizer file hashes differ from pinned Feature18 contract")
    if tokenizer_bundle_hash != expected_contract["model"]["tokenizer_bundle_sha256"]:
        raise ValueError("local tokenizer bundle hash differs from pinned Feature18 contract")
    if not pooling["pooling_mode_mean_tokens"] or pooling["pooling_mode_cls_token"]:
        raise ValueError("local pooling configuration differs from Feature18 contract")
    if [item["type"].rsplit(".", 1)[-1] for item in modules] != ["Transformer", "Pooling", "Normalize"]:
        raise ValueError("local sentence-transformers module graph differs from Feature18 contract")
    report = {
        "verification_kind": "technical candidate snapshot and read-only artifact verification",
        "approved_snapshot": False,
        "snapshot": audit["summary"],
        "pair_routing": routing,
        "candidate_artifact": {"path": str(candidate_path), "rows": pq.ParquetFile(candidate_path).metadata.num_rows,
                               "sha256": sha256_file(candidate_path)},
        "feature_alignment": {
            "feature17_columns_match_registry": gb17_schema == ["profile_row_id_a", "profile_row_id_b", *registry["ordered_columns"]],
            "feature17_rows": pq.ParquetFile(gb17_path).metadata.num_rows,
            "feature18_pair_columns": bert_schema,
            "feature18_rows": pq.ParquetFile(bert_path).metadata.num_rows,
            "feature17_feature18_pair_order_equal": pair_order_equal,
            "persisted_bert_cos_sample_dot_product_rows": 16,
            "persisted_bert_cos_sample_matches_embedding_dot_products": sample_cosine_match,
            "gb17_sha256": sha256_file(gb17_path), "bert_cos_sha256": sha256_file(bert_path),
        },
        "minilm_artifacts": {
            "model_identifier": "sentence-transformers/all-MiniLM-L6-v2",
            "local_snapshot_revision": model_dir.name,
            "weights_sha256": model_weight_sha,
            "tokenizer_file_sha256": tokenizer_hashes,
            "tokenizer_bundle_sha256": tokenizer_bundle_hash,
            "pooling_config": pooling,
            "module_types": [item["type"].rsplit(".", 1)[-1] for item in modules],
            "embedding_shape": list(embeddings.shape),
            "embedding_dtype": str(embeddings.dtype),
            "embedding_ids_sha256": sha256_file(profile_ids_path),
            "embedding_ids_match_snapshot_order": ids_match,
            "embedding_norm_min": float(norms.min()), "embedding_norm_max": float(norms.max()),
            "historical_text_serialization": "NOT VERIFIED: persisted documents specify fields and [empty], but encoder preprocessing implementation/manifest is absent",
            "historical_embedding_to_model_revision_lineage": "NOT VERIFIED: local model cache is identified, but embedding artifact has no binding manifest",
            "weights_downloaded_or_replaced": False,
        },
        "historical_pair_key_rejoin": {
            "decision_artifact": str(decision_path), "decision_artifact_sha256": sha256_file(decision_path),
            "pair_key_source": str(pair_key_source), "pair_key_source_sha256": sha256_file(pair_key_source),
            "pair_key_scheme": "sha256('v2-pair:<lower-profile_row_id>:<higher-profile_row_id>')",
            "exact_and_scored_keys": len(candidate_keys), "matched_explicit_endpoint_keys": len(found),
            "ambiguous_endpoint_keys": duplicates,
            "blocking_miss_rows_without_candidate_endpoint_mapping": int((decisions.pair_type == "BLOCKING_MISS").sum()),
            "metric_replay_performed": False,
            "historical_split_role_manifest": "NOT VERIFIED; new candidate fold roles are not substituted for historical roles",
        },
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path("/Users/thawaree.kha/Project-for-Work"))
    parser.add_argument("--output", type=Path, required=True,
                        help="new report path; must be in the isolated integration worktree")
    args = parser.parse_args()
    report = build_report(args.source_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"report_path": str(args.output), "snapshot_sha256": report["snapshot"]["snapshot_sha256"],
                      "rows": report["snapshot"]["rows"], "eligible_rows": report["snapshot"]["eligible_rows"],
                      "candidate_pair_routing": report["pair_routing"],
                      "historical_mapped_keys": report["historical_pair_key_rejoin"]["matched_explicit_endpoint_keys"],
                      "feature18_order_match": report["feature_alignment"]["feature17_feature18_pair_order_equal"],
                      "model_revision": report["minilm_artifacts"]["local_snapshot_revision"]}, sort_keys=True))


if __name__ == "__main__":
    main()
