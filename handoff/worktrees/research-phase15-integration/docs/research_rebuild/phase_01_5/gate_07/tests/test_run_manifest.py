import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_manifest import (  # noqa: E402
    COMPATIBILITY_FIELDS, ManifestError, assert_cache_compatible,
    build_manifest, canonical_json, finalize_manifest, read_manifest,
    validate_cache, validate_chunks, write_manifest_create_only,
)


class RunManifestTests(unittest.TestCase):
    def setUp(self):
        self.artifact_tmp = tempfile.TemporaryDirectory()
        self.artifact_root = Path(self.artifact_tmp.name)
        self.key = {
            "dataset_identity": "sha256:dataset",
            "schema_identity": "sha256:schema",
            "pair_population_identity": "sha256:pairs",
            "chunk_size": 2,
            "model_identity": "sha256:model",
            "source_identity": "git:abc123",
            "split_identity": "sha256:split",
            "configuration_identity": "sha256:config",
            "environment_identity": "sha256:environment",
            "seed": 17,
        }

    def tearDown(self):
        self.artifact_tmp.cleanup()

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
                changed[field] = (3 if field == "chunk_size" else
                                  self.key[field] + ":changed" if isinstance(self.key[field], str) else
                                  self.key[field] + 1)
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


    def _complete_cache(self):
        manifest = build_manifest(self.key, 3)
        chunks = []
        for index, (start, stop, keys) in enumerate(((0, 2, ["a", "b"]), (2, 3, ["c"]))):
            relative = f"chunk-{index:03d}.parquet"
            payload = json.dumps(keys, separators=(",", ":")).encode()
            (self.artifact_root / relative).write_bytes(payload)
            chunks.append({"index": index, "start": start, "stop": stop,
                           "pair_keys": keys, "path": relative,
                           "sha256": hashlib.sha256(payload).hexdigest()})
        return finalize_manifest(manifest, chunks, artifact_root=self.artifact_root), chunks

    def test_writer_output_is_schema_valid_and_reader_accepts_it(self):
        manifest = build_manifest(self.key, 0)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            write_manifest_create_only(path, manifest)
            self.assertEqual(read_manifest(path), manifest)

    def test_reader_rejects_invalid_schema_version(self):
        manifest = build_manifest(self.key, 0)
        manifest["manifest_schema"] = 2
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ManifestError, "schema version"):
                read_manifest(path)

    def test_wrong_dataset_hash_invalidates_cache(self):
        manifest, chunks = self._complete_cache()
        wrong = dict(self.key, dataset_identity="sha256:other-dataset")
        with self.assertRaisesRegex(ManifestError, "dataset_identity"):
            validate_cache(wrong, manifest, chunks, ["a", "b", "c"], artifact_root=self.artifact_root)

    def test_wrong_feature_schema_invalidates_cache(self):
        manifest, chunks = self._complete_cache()
        wrong = dict(self.key, schema_identity="sha256:other-schema")
        with self.assertRaisesRegex(ManifestError, "schema_identity"):
            validate_cache(wrong, manifest, chunks, ["a", "b", "c"], artifact_root=self.artifact_root)

    def test_stale_chunk_pair_population_is_rejected(self):
        manifest, chunks = self._complete_cache()
        stale = [dict(chunks[0], pair_keys=["a", "old"]), chunks[1]]
        with self.assertRaisesRegex(ManifestError, "stale chunk"):
            validate_cache(self.key, manifest, stale, ["a", "b", "c"], artifact_root=self.artifact_root)

    def test_writer_rejects_complete_manifest_without_chunk_witness(self):
        manifest, _chunks = self._complete_cache()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            with self.assertRaisesRegex(ManifestError, "requires validated chunks"):
                write_manifest_create_only(path, manifest)
            self.assertFalse(path.exists())

    def test_partial_run_cannot_be_finalized_complete(self):
        manifest = build_manifest(self.key, 3)
        partial = [{"index": 0, "start": 0, "stop": 2, "pair_keys": ["a", "b"],
                    "path": "chunk-000.parquet", "sha256": "a" * 64}]
        with self.assertRaisesRegex(ManifestError, "partial or extra"):
            finalize_manifest(manifest, partial)
        self.assertEqual(manifest["state"], "CREATED")

    def test_complete_cache_requires_expected_pair_key_order(self):
        manifest, chunks = self._complete_cache()
        self.assertEqual(validate_cache(self.key, manifest, chunks, ["a", "b", "c"], artifact_root=self.artifact_root), manifest)
        with self.assertRaisesRegex(ManifestError, "stale chunk"):
            validate_cache(self.key, manifest, chunks, ["b", "a", "c"], artifact_root=self.artifact_root)


if __name__ == "__main__":
    unittest.main()
