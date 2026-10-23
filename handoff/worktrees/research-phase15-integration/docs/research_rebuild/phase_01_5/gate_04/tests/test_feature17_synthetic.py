"""Synthetic checks against corrected-v2 feature code; no project records used.

Set IDENTITY_RESOLUTION_SOURCE_ROOT to a checkout that contains
experiments/icsec_final/authoritative_run_v2/features.py.
"""
from __future__ import annotations

import importlib
import importlib.util
import os
from pathlib import Path
import unittest

SOURCE = Path(os.environ.get("IDENTITY_RESOLUTION_SOURCE_ROOT", ".")) / "experiments/icsec_final/authoritative_run_v2/features.py"
HAS_DEPS = importlib.util.find_spec("rapidfuzz") is not None and importlib.util.find_spec("pandas") is not None

@unittest.skipUnless(SOURCE.is_file() and HAS_DEPS, "set source-root and install declared project test dependencies")
class Feature17SyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("corrected_v2_features", SOURCE)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load feature source: {SOURCE}")
        cls.features = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.features)
        cls.pd = importlib.import_module("pandas")

    def _inputs(self):
        profiles = self.pd.DataFrame([
            {"profile_row_id": 1, "userName": "@Alice", "fullName": "Alice Smith", "bio": "runner data", "location": "New York", "platform": "twitter"},
            {"profile_row_id": 2, "userName": "alice", "fullName": "Alice Smith", "bio": "data runner", "location": "new york", "platform": "instagram"},
            {"profile_row_id": 3, "userName": None, "fullName": float("nan"), "bio": None, "location": "", "platform": ""},
        ])
        pairs = self.pd.DataFrame([
            {"profile_row_id_a": 1, "profile_row_id_b": 2},
            {"profile_row_id_a": 2, "profile_row_id_b": 1},
            {"profile_row_id_a": 1, "profile_row_id_b": 3},
        ])
        return pairs, profiles

    def test_schema_ranges_missingness_and_order(self):
        pairs, profiles = self._inputs()
        result = self.features.build_handcrafted_features(pairs, profiles)
        self.assertEqual(list(result.columns), ["profile_row_id_a", "profile_row_id_b", *self.features.FEATURE17_COLUMNS])
        values = result[self.features.FEATURE17_COLUMNS].to_numpy()
        self.assertTrue(self.pd.notna(result).all().all())
        self.assertTrue(((values >= 0.0) & (values <= 1.0)).all())
        self.assertEqual(float(result.loc[2, "bio_jaccard"]), 0.0)
        self.assertEqual(float(result.loc[2, "location_exact"]), 0.0)

    def test_pairwise_handcrafted_features_are_symmetric(self):
        pairs, profiles = self._inputs()
        result = self.features.build_handcrafted_features(pairs.iloc[:2], profiles)
        left = result.loc[0, self.features.FEATURE17_COLUMNS].to_numpy(dtype=float)
        right = result.loc[1, self.features.FEATURE17_COLUMNS].to_numpy(dtype=float)
        self.assertTrue(self.pd.Series(left).equals(self.pd.Series(right)))

    def test_cross_field_name_similarity_normalizes_and_handles_missing(self):
        got = self.features.corrected_name_sim(["@Alice", None], ["Alice Smith", float("nan")], ["alice", ""], ["Alice Smith", None])
        self.assertEqual(got[0], 1.0)
        self.assertEqual(got[1], 0.0)

    def test_name_inputs_must_be_pair_aligned(self):
        with self.assertRaises(ValueError):
            self.features.corrected_name_sim(["a"], ["a", "b"], ["a"], ["a"])

if __name__ == "__main__":
    unittest.main()
