import unittest

from identity_resolution.core.name_similarity import (
    char_ngram_cosine,
    damerau_similarity,
    handle_features,
    latin_soundex_match,
    normalize_name,
    token_set_similarity,
)


class NameSimilarityTests(unittest.TestCase):
    def test_normalize_name_handles_unicode_case_and_whitespace(self):
        self.assertEqual(normalize_name(" @  Cafe\u0301   SMITH "), "café smith")

    def test_empty_names_are_zero_similarity(self):
        self.assertEqual(damerau_similarity("", ""), 0.0)
        self.assertEqual(token_set_similarity(None, "Ann"), 0.0)
        self.assertEqual(char_ngram_cosine("", "Ann"), 0.0)

    def test_damerau_recovers_adjacent_transposition(self):
        self.assertGreater(damerau_similarity("martha", "marhta"), 0.80)

    def test_token_set_ignores_full_name_order(self):
        self.assertEqual(token_set_similarity("Ada Lovelace", "Lovelace Ada"), 1.0)

    def test_handle_features_ignore_separator_and_marker(self):
        features = handle_features("@john_smith", "john-smith")
        self.assertEqual(features["exact"], 1.0)
        self.assertEqual(features["available"], 1.0)
        self.assertEqual(features["length_ratio"], 1.0)

    def test_latin_soundex_does_not_apply_to_thai_text(self):
        self.assertEqual(latin_soundex_match("Robert", "Rupert"), 1.0)
        self.assertEqual(latin_soundex_match("สมชาย", "สมชาย"), 0.0)


if __name__ == "__main__":
    unittest.main()