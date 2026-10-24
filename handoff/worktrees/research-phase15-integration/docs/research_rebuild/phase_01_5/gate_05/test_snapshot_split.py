import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from snapshot_split import SnapshotSplitError, route_pair_iter, verify_snapshot_split


class SnapshotSplitTests(unittest.TestCase):
    def test_snapshot_hash_is_checked_before_assignment_and_unmapped_rows_excluded(self):
        frame = pd.DataFrame([
            {"profile_row_id": 10, "user_folder": "entity-a", "platform": "twitter"},
            {"profile_row_id": 11, "user_folder": "entity-a", "platform": "instagram"},
            {"profile_row_id": 12, "user_folder": "entity-b", "platform": "twitter"},
            {"profile_row_id": 13, "user_folder": None, "platform": "twitter"},
        ])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "snapshot.csv"
            frame.to_csv(path, index=False)
            expected = hashlib.sha256(path.read_bytes()).hexdigest()
            report = verify_snapshot_split(path, expected_sha256=expected,
                                           expected_unmapped_rows=1)
            self.assertEqual(report["summary"]["excluded_unmapped_rows"], 1)
            self.assertEqual(len(report["entity_roles"]), 2)
            self.assertEqual(len(report["profile_roles"]), 3)
            with self.assertRaises(SnapshotSplitError):
                verify_snapshot_split(path, expected_sha256="0" * 64,
                                      expected_unmapped_rows=1)

    def test_duplicate_profile_ids_and_unexpected_unmapped_count_rejected(self):
        frame = pd.DataFrame([
            {"profile_row_id": 1, "user_folder": "a", "platform": "x"},
            {"profile_row_id": 1, "user_folder": "b", "platform": "y"},
        ])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            frame.to_csv(path, index=False)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(SnapshotSplitError):
                verify_snapshot_split(path, expected_sha256=digest,
                                      expected_unmapped_rows=0)

    def test_pair_routing_checks_both_endpoint_roles_and_duplicate_keys(self):
        profile_entities = {1: "a", 2: "b", 3: "c"}
        entity_roles = {"a": "TRAIN", "b": "TRAIN", "c": "TEST"}
        result = route_pair_iter([(1, 2, "MODEL_SCORED"), (1, 3, "MODEL_SCORED")],
                                 profile_entities, entity_roles, collect_routed=True)
        self.assertEqual(result["same_role_pairs"], 1)
        self.assertEqual(result["cross_role_dropped"], 1)
        self.assertEqual(result["routed_pairs"], [(1, 2, "MODEL_SCORED", "TRAIN")])
        with self.assertRaises(SnapshotSplitError):
            route_pair_iter([(1, 2, "MODEL_SCORED"), (2, 1, "MODEL_SCORED")],
                             profile_entities, entity_roles)

    def test_real_v2_candidate_snapshot_hash_mapping_and_deterministic_folds(self):
        path = Path("/Users/thawaree.kha/Project-for-Work/data_for_project/normalized_profiles_with_profile_id.csv")
        if not path.is_file():
            self.skipTest("real candidate snapshot unavailable on this host")
        report = verify_snapshot_split(
            path,
            expected_sha256="17a95f754cb7f43cc28fd63a7ced2dcf59c57945d5a782fa9e3a057d45b182b1",
            expected_unmapped_rows=3,
        )
        summary = report["summary"]
        self.assertEqual(summary["rows"], 36807)
        self.assertEqual(summary["eligible_rows"], 36804)
        self.assertEqual(summary["entity_count"], 15297)
        self.assertEqual(summary["profile_row_id_unique"], 36807)
        self.assertTrue(summary["deterministic"])
        self.assertTrue(summary["entity_atomic"])


if __name__ == "__main__":
    unittest.main()
