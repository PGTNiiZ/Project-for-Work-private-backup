import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feature18_contract import (
    FEATURE17_COLUMNS, Feature18ContractError, build_feature18,
    MODEL_IDENTIFIER, MODEL_REVISION, MODEL_WEIGHT_SHA256, TOKENIZER_BUNDLE_SHA256,
    TEXT_COMPOSITION, POOLING_CONTRACT, compose_profile_text,
)


class Feature18ContractTests(unittest.TestCase):
    def setUp(self):
        self.feature17 = pd.DataFrame({
            "profile_row_id_a": [1, 2], "profile_row_id_b": [2, 3],
            **{column: np.array([0.1, 0.2], dtype=np.float32)
               for column in FEATURE17_COLUMNS},
        })
        self.embeddings = np.zeros((3, 384), dtype=np.float32)
        self.embeddings[0, 0] = 1.0
        self.embeddings[1, 1] = 1.0
        self.embeddings[2, :2] = np.sqrt(0.5)
        self.metadata = {
            "model_identifier": MODEL_IDENTIFIER,
            "model_revision": MODEL_REVISION,
            "model_weight_sha256": MODEL_WEIGHT_SHA256,
            "tokenizer_bundle_sha256": TOKENIZER_BUNDLE_SHA256,
            "text_composition": TEXT_COMPOSITION,
            "pooling": POOLING_CONTRACT,
        }

    def build(self, **kwargs):
        return build_feature18(self.feature17, [1, 2, 3], self.embeddings,
                               expected_profile_ids=[1, 2, 3],
                               metadata={**self.metadata, **kwargs})

    def test_profile_text_composition_is_exact_and_empty_uses_sentinel(self):
        self.assertEqual(compose_profile_text("  Alice   SMITH ", " data   science ", "NEW   YORK"),
                         "alice smith data science new york")
        self.assertEqual(compose_profile_text(None, "  ", float("nan")), "[empty]")
        self.assertEqual(compose_profile_text(pd.NA, None, ""), "[empty]")

    def test_adds_exactly_one_cosine_column_with_pair_alignment(self):
        result = self.build()
        self.assertEqual(list(result.columns),
                         ["profile_row_id_a", "profile_row_id_b", *FEATURE17_COLUMNS, "bert_cos"])
        self.assertEqual(len(result.columns), len(self.feature17.columns) + 1)
        self.assertAlmostEqual(float(result.bert_cos.iloc[0]), 0.0, places=6)
        self.assertAlmostEqual(float(result.bert_cos.iloc[1]), 0.7071067, places=6)

    def test_rejects_wrong_embedding_dimension(self):
        with self.assertRaisesRegex(Feature18ContractError, "384-dimensional"):
            build_feature18(self.feature17.iloc[:1], [1, 2], np.eye(2, dtype=np.float32),
                            expected_profile_ids=[1, 2], metadata=self.metadata)

    def test_rejects_non_integer_profile_ids_in_embedding_lineage(self):
        with self.assertRaisesRegex(Feature18ContractError, "integer row identifiers"):
            build_feature18(self.feature17, [1.0, 2, 3], self.embeddings,
                            expected_profile_ids=[1, 2, 3], metadata=self.metadata)

    def test_rejects_unpinned_model_or_unverified_profile_order(self):
        with self.assertRaises(Feature18ContractError):
            self.build(model_revision="unknown")
        with self.assertRaises(Feature18ContractError):
            build_feature18(self.feature17, [2, 1, 3], self.embeddings,
                            expected_profile_ids=[1, 2, 3], metadata=self.metadata)

    def test_rejects_incorrect_model_hashes_text_pooling_and_missing_endpoint(self):
        for bad in ({"model_identifier": "other/model"},
                    {"model_weight_sha256": "not-a-hash"},
                    {"text_composition": "username only"},
                    {"pooling": "CLS"}):
            with self.subTest(bad=bad), self.assertRaises(Feature18ContractError):
                self.build(**bad)
        missing = self.feature17.copy()
        missing.loc[0, "profile_row_id_a"] = 99
        with self.assertRaises(Feature18ContractError):
            build_feature18(missing, [1, 2, 3], self.embeddings,
                            expected_profile_ids=[1, 2, 3], metadata=self.metadata)


if __name__ == "__main__":
    unittest.main()
