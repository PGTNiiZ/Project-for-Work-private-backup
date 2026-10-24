import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_manifest import (  # noqa: E402
    COMPATIBILITY_FIELDS, ManifestError, assert_cache_compatible,
    build_manifest, canonical_json, validate_chunks, write_manifest_create_only,
)


class RunManifestTests(unittest.TestCase):
    def setUp(self):
        self.key = {
            "dataset_identity": "sha256:dataset",
            "schema_identity": "sha256:schema",
            "pair_population_identity": "sha256:pairs",
            "chunk_size": 2,
            "model_identity": "sha256:model",
            "source_identity": "git:abc123",
            "split_identity": "sha256:split",
        }

    def test_manifest_is_deterministic_and_stable_json(self):
        first = build_manifest(self.key, 3)
        second = build_manifest(dict(reversed(list(self.key.items()))), 3)
        self.assertEqual(first, second)
        self.assertEqual(canonical_json(first), canonical_json(second))

    def test_manifest_publication_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            manifest = build_manifest(self.key, 0)
            write_manifest_create_only(path, manifest)
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                write_manifest_create_only(path, build_manifest(self.key, 4))
            self.assertEqual(path.read_bytes(), before)

    def test_each_single_compatibility_field_change_invalidates_cache(self):
        for field in COMPATIBILITY_FIELDS:
            with self.subTest(field=field):
                changed = dict(self.key)
                changed[field] = 3 if field == "chunk_size" else self.key[field] + ":changed"
                with self.assertRaises(ManifestError):
                    assert_cache_compatible(self.key, changed)

    def test_valid_complete_chunks_include_short_final_chunk(self):
        chunks = [
            {"index": 0, "start": 0, "stop": 2, "pair_keys": ["a", "b"]},
            {"index": 1, "start": 2, "stop": 3, "pair_keys": ["c"]},
        ]
        self.assertEqual(validate_chunks(3, 2, chunks), chunks)

    def test_reject_duplicate_chunk_index(self):
        row = {"index": 0, "start": 0, "stop": 1, "pair_keys": ["a"]}
        with self.assertRaisesRegex(ManifestError, "duplicate chunk index"):
            validate_chunks(1, 1, [row, row])

    def test_reject_duplicate_pair_key_across_chunks(self):
        chunks = [
            {"index": 0, "start": 0, "stop": 1, "pair_keys": ["same"]},
            {"index": 1, "start": 1, "stop": 2, "pair_keys": ["same"]},
        ]
        with self.assertRaisesRegex(ManifestError, "duplicate pair key"):
            validate_chunks(2, 1, chunks)

    def test_reject_missing_chunk_partial_run(self):
        with self.assertRaisesRegex(ManifestError, "partial or extra"):
            validate_chunks(3, 2, [
                {"index": 0, "start": 0, "stop": 2, "pair_keys": ["a", "b"]},
            ])

    def test_reject_gap_overlap_or_wrong_range(self):
        with self.assertRaisesRegex(ManifestError, "gap, overlap"):
            validate_chunks(2, 1, [
                {"index": 0, "start": 0, "stop": 1, "pair_keys": ["a"]},
                {"index": 1, "start": 0, "stop": 2, "pair_keys": ["b", "c"]},
            ])

    def test_reject_wrong_chunk_row_count(self):
        with self.assertRaisesRegex(ManifestError, "row count"):
            validate_chunks(2, 2, [
                {"index": 0, "start": 0, "stop": 2, "pair_keys": ["only-one"]},
            ])


if __name__ == "__main__":
    unittest.main()
