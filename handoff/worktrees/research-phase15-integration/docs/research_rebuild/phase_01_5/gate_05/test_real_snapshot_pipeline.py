import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

PHASE15 = Path(__file__).resolve().parent.parent
REPO_ROOT = Path(os.environ.get("IDENTITY_RESOLUTION_SOURCE_ROOT", "/Users/thawaree.kha/Project-for-Work"))
sys.path.insert(0, str(PHASE15 / "gate_05"))
sys.path.insert(0, str(PHASE15 / "gate_06"))
from snapshot_split import route_pair_iter, verify_snapshot_split
from pair_adapter import canonical_pair_key


class RealSnapshotPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.REPO_ROOT = REPO_ROOT
        cls.snapshot = REPO_ROOT / "data_for_project/normalized_profiles_with_profile_id.csv"
        cls.v2 = REPO_ROOT / "experiments/icsec_final/authoritative_run_v2"
        cls.model = (Path.home() / ".cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2"
                     / "snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41")

    def test_candidate_snapshot_split_routes_all_explicit_candidate_endpoints(self):
        if not self.snapshot.is_file():
            self.skipTest("candidate snapshot unavailable")
        audited = verify_snapshot_split(
            self.snapshot,
            expected_sha256="17a95f754cb7f43cc28fd63a7ced2dcf59c57945d5a782fa9e3a057d45b182b1",
            expected_unmapped_rows=3,
        )
        candidate = self.v2 / "candidates/workflow.parquet"
        parquet = pq.ParquetFile(candidate)
        def pairs():
            for batch in parquet.iter_batches(columns=["profile_row_id_a", "profile_row_id_b", "pair_type"],
                                              batch_size=50000):
                columns = batch.to_pydict()
                yield from zip(columns["profile_row_id_a"], columns["profile_row_id_b"],
                               columns["pair_type"])
        routing = route_pair_iter(pairs(), audited["profile_entities"], audited["entity_roles"])
        self.assertEqual(routing["input_pairs"], parquet.metadata.num_rows)
        self.assertEqual(routing["same_role_pairs"] + routing["cross_role_dropped"],
                         routing["input_pairs"])
        self.assertEqual(audited["summary"]["rows"], 36807)
        self.assertEqual(audited["summary"]["eligible_rows"], 36804)

    def test_cached_embedding_identity_and_decision_endpoint_join_are_keyed(self):
        if not (self.snapshot.is_file() and self.model.is_dir()):
            self.skipTest("snapshot or locally cached MiniLM snapshot unavailable")
        snapshot_ids = pd.read_csv(self.snapshot, usecols=["profile_row_id"])["profile_row_id"].astype("int64").to_numpy()
        # Use the persisted ID vector as the explicit embedding-order witness.
        profile_ids = np.load(self.REPO_ROOT / "experiments/profile_embeddings_minilm_ids.npy",
                              allow_pickle=False)
        embeddings = np.load(self.REPO_ROOT / "experiments/profile_embeddings_minilm.npy",
                             mmap_mode="r", allow_pickle=False)
        expected_ids = snapshot_ids.astype(np.int64)
        self.assertEqual(profile_ids.tolist(), expected_ids.tolist())
        self.assertEqual(embeddings.shape, (36807, 384))
        self.assertTrue(np.allclose(np.linalg.norm(embeddings, axis=1), 1.0, atol=1e-4))

        features_path = self.v2 / "features/gb17.parquet"
        bert_path = self.v2 / "features/bert_cos.parquet"
        f17_schema = pq.ParquetFile(features_path).schema_arrow.names
        registry = json.loads((PHASE15 / "gate_04/FEATURE_REGISTRY.json").read_text(encoding="utf-8"))
        self.assertEqual(f17_schema, ["profile_row_id_a", "profile_row_id_b", *registry["ordered_columns"]])
        self.assertEqual(pq.ParquetFile(bert_path).schema_arrow.names,
                         ["profile_row_id_a", "profile_row_id_b", "bert_cos"])
        f17_ids = pq.read_table(features_path, columns=["profile_row_id_a", "profile_row_id_b"])
        bert_ids = pq.read_table(bert_path, columns=["profile_row_id_a", "profile_row_id_b"])
        self.assertTrue(np.array_equal(f17_ids.column(0).to_numpy(), bert_ids.column(0).to_numpy()))
        self.assertTrue(np.array_equal(f17_ids.column(1).to_numpy(), bert_ids.column(1).to_numpy()))

        id_to_row = {int(value): index for index, value in enumerate(profile_ids)}
        sample = f17_ids.slice(0, 16).to_pydict()
        stored = pq.read_table(bert_path, columns=["bert_cos"]).slice(0, 16)["bert_cos"].to_numpy()
        recomputed = np.asarray([
            np.dot(embeddings[id_to_row[int(a)]], embeddings[id_to_row[int(b)]])
            for a, b in zip(sample["profile_row_id_a"], sample["profile_row_id_b"])
        ])
        self.assertTrue(np.allclose(stored, recomputed, atol=2e-6, rtol=0.0))

        # Rejoin only exact/scored historical rows by the source-defined hash key.
        decisions_path = self.v2 / "scientific_outputs/outer_101/decisions/B0_workflow.parquet"
        decisions = pq.read_table(decisions_path, columns=["pair_key", "pair_type"]).to_pandas()
        wanted = set(decisions.loc[decisions.pair_type != "BLOCKING_MISS", "pair_key"].astype(str))
        found = {}
        candidates = pq.ParquetFile(self.v2 / "candidates/workflow.parquet")
        for batch in candidates.iter_batches(columns=["profile_row_id_a", "profile_row_id_b"],
                                             batch_size=50000):
            columns = batch.to_pydict()
            for a, b in zip(columns["profile_row_id_a"], columns["profile_row_id_b"]):
                key = canonical_pair_key(a, b)
                if key in wanted:
                    if key in found:
                        self.fail("historical pair key maps to duplicate endpoint rows")
                    found[key] = (int(a), int(b))
        self.assertEqual(set(found), wanted)
        self.assertEqual(int((decisions.pair_type == "BLOCKING_MISS").sum()), 1034)
        self.assertEqual(len(wanted), 193692)

        weight = self.model / "model.safetensors"
        tokenizer = self.model / "tokenizer.json"
        self.assertEqual(self.model.name, "1110a243fdf4706b3f48f1d95db1a4f5529b4d41")
        self.assertTrue(weight.is_file() and tokenizer.is_file())
        pooling = json.loads((self.model / "1_Pooling/config.json").read_text(encoding="utf-8"))
        self.assertTrue(pooling["pooling_mode_mean_tokens"])
        self.assertFalse(pooling["pooling_mode_cls_token"])
        modules = json.loads((self.model / "modules.json").read_text(encoding="utf-8"))
        self.assertEqual([module["type"].rsplit(".", 1)[-1] for module in modules],
                         ["Transformer", "Pooling", "Normalize"])


if __name__ == "__main__":
    unittest.main()
