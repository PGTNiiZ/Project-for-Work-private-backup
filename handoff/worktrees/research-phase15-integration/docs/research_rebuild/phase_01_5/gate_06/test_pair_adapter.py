import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pair_adapter import AdapterError, adapt_decision_records, canonical_pair_key


class PairAdapterTests(unittest.TestCase):
    def setUp(self):
        self.entities = {1: "E1", 2: "E2", 3: "E3", 4: "E4", 5: "E5", 6: "E6"}
        self.roles = {"E1": "TRAIN", "E2": "TRAIN", "E3": "TEST",
                      "E4": "TEST", "E5": "TEST", "E6": "TEST"}

    def test_future_a_f_pair_record_accepts_profile_row_endpoints(self):
        pair = {"pair_key": canonical_pair_key(1, 2), "scope": "scored",
                "label": 1, "action": "REVIEW", "score": .5,
                "profile_row_id_a": 1, "profile_row_id_b": 2}
        result = adapt_decision_records([pair], profile_entities=self.entities,
                                        entity_roles=self.roles)
        self.assertEqual(result["scored"][0]["a"], "1")
        self.assertEqual(result["scored"][0]["b"], "2")

    def test_valid_records_preserve_exact_scored_miss_scopes(self):
        records = [
            {"pair_key": canonical_pair_key(1, 2), "endpoint_a": 1, "endpoint_b": 2,
             "scope": "AUTO_EXACT", "label": 1, "action": "MATCH"},
            {"pair_key": canonical_pair_key(3, 4), "endpoint_a": 3, "endpoint_b": 4,
             "scope": "MODEL_SCORED", "label": 1, "action": "REVIEW", "score": 0.8},
            {"pair_key": canonical_pair_key(5, 6), "endpoint_a": 5, "endpoint_b": 6,
             "scope": "BLOCKING_MISS", "label": 1},
        ]
        result = adapt_decision_records(records, profile_entities=self.entities,
                                        entity_roles=self.roles)
        self.assertEqual(len(result["exact"]), 1)
        self.assertEqual(result["exact"][0]["action"], "MATCH")
        self.assertEqual(result["scored"][0]["action"], "REVIEW")
        self.assertEqual(result["blocking_misses"][0]["label"], 1)
        self.assertEqual(result["pair_keys"], [r["pair_key"] for r in records])

    def test_positive_and_negative_review_rows_are_preserved(self):
        records = [
            {"pair_key": canonical_pair_key(1, 2), "endpoint_a": 1, "endpoint_b": 2,
             "scope": "scored", "label": 1, "action": "REVIEW", "score": 0.8},
            {"pair_key": canonical_pair_key(3, 4), "endpoint_a": 3, "endpoint_b": 4,
             "scope": "scored", "label": 0, "action": "REVIEW", "score": 0.2},
        ]
        result = adapt_decision_records(records, profile_entities=self.entities,
                                        entity_roles=self.roles)
        self.assertEqual([r["label"] for r in result["scored"]], [1, 0])
        self.assertEqual([r["action"] for r in result["scored"]], ["REVIEW", "REVIEW"])

    def test_explicit_mapping_resolves_endpoints_and_is_order_invariant(self):
        key = canonical_pair_key(1, 2)
        rows = [{"pair_key": key, "scope": "scored", "label": 1,
                 "action": "REVIEW", "score": 0.7}]
        mapping = [{"pair_key": key, "endpoint_a": 2, "endpoint_b": 1}]
        adapted = adapt_decision_records(rows, profile_entities=self.entities,
                                         entity_roles=self.roles, endpoint_mapping=mapping)
        self.assertEqual((adapted["scored"][0]["a"], adapted["scored"][0]["b"]), ("1", "2"))

    def test_rejects_missing_mapping_and_opaque_or_wrong_hash(self):
        row = {"pair_key": "a" * 64, "scope": "scored", "label": 1,
               "action": "MATCH", "score": 0.9}
        with self.assertRaises(AdapterError):
            adapt_decision_records([row], profile_entities=self.entities,
                                   entity_roles=self.roles)
        wrong_key_row = {"pair_key": canonical_pair_key(1, 3), "endpoint_a": 1,
                         "endpoint_b": 2, "scope": "scored", "label": 1,
                         "action": "MATCH", "score": 0.9}
        with self.assertRaises(AdapterError):
            adapt_decision_records([wrong_key_row], profile_entities=self.entities,
                                   entity_roles=self.roles)

    def test_rejects_ambiguous_mapping_duplicate_records_unknown_endpoint(self):
        key = canonical_pair_key(1, 2)
        row = {"pair_key": key, "scope": "scored", "label": 1,
               "action": "MATCH", "score": 0.9}
        duplicate_map = [
            {"pair_key": key, "endpoint_a": 1, "endpoint_b": 2},
            {"pair_key": key, "endpoint_a": 2, "endpoint_b": 3},
        ]
        with self.assertRaises(AdapterError):
            adapt_decision_records([row], profile_entities=self.entities,
                                   entity_roles=self.roles, endpoint_mapping=duplicate_map)
        direct = dict(row, endpoint_a=1, endpoint_b=2)
        with self.assertRaises(AdapterError):
            adapt_decision_records([direct, direct], profile_entities=self.entities,
                                   entity_roles=self.roles)
        unknown = dict(row, pair_key=canonical_pair_key(1, 99), endpoint_a=1, endpoint_b=99)
        with self.assertRaises(AdapterError):
            adapt_decision_records([unknown], profile_entities=self.entities,
                                   entity_roles=self.roles)

    def test_rejects_cross_role_mismatch_and_invalid_missed_positive(self):
        cross_role = {"pair_key": canonical_pair_key(1, 3), "endpoint_a": 1,
                      "endpoint_b": 3, "scope": "scored", "label": 1,
                      "action": "MATCH", "score": 0.9}
        with self.assertRaises(AdapterError):
            adapt_decision_records([cross_role], profile_entities=self.entities,
                                   entity_roles=self.roles)
        mismatch = {"pair_key": canonical_pair_key(1, 2), "endpoint_a": 1,
                    "endpoint_b": 2, "scope": "scored", "split_role": "TEST",
                    "label": 1, "action": "MATCH", "score": 0.9}
        with self.assertRaises(AdapterError):
            adapt_decision_records([mismatch], profile_entities=self.entities,
                                   entity_roles=self.roles)
        negative_miss = {"pair_key": canonical_pair_key(5, 6), "endpoint_a": 5,
                         "endpoint_b": 6, "scope": "blocking_miss", "label": 0}
        with self.assertRaises(AdapterError):
            adapt_decision_records([negative_miss], profile_entities=self.entities,
                                   entity_roles=self.roles)


if __name__ == "__main__":
    unittest.main()
