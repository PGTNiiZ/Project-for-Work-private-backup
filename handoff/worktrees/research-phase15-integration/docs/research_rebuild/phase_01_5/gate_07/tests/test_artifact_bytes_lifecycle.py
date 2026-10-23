import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_manifest import (
    ManifestError, build_manifest, finalize_manifest, read_manifest,
    validate_cache, write_manifest_create_only,
)


class ArtifactBytesLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.identity_tmp = tempfile.TemporaryDirectory()
        self.identity_root = Path(self.identity_tmp.name)
        self.identity_files = {
            "dataset_identity": ("dataset.bin", b"safe synthetic dataset fixture v1"),
            "pair_population_identity": ("pair_keys.json", b'["p1","p2","p3"]'),
            "schema_identity": ("schema.json", (Path(__file__).resolve().parents[1]
                                                  / "RUN_MANIFEST_SCHEMA.json").read_bytes()),
            "source_identity": ("source.py", (Path(__file__).resolve().parents[1]
                                                / "run_manifest.py").read_bytes()),
        }
        identity_hashes = {}
        for field, (filename, payload) in self.identity_files.items():
            target = self.identity_root / filename
            target.write_bytes(payload)
            identity_hashes[field] = "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()
        self.compatibility = {
            **identity_hashes, "chunk_size": 2,
            "model_identity": "synthetic:no-model-executed",
            "split_identity": "sha256:split", "configuration_identity": "sha256:config",
            "environment_identity": "sha256:environment", "seed": 7,
        }

    def tearDown(self):
        self.identity_tmp.cleanup()

    def test_dataset_source_schema_and_pair_population_identities_are_byte_hashes(self):
        for field, (filename, _payload) in self.identity_files.items():
            actual = hashlib.sha256((self.identity_root / filename).read_bytes()).hexdigest()
            self.assertEqual(self.compatibility[field], "sha256:" + actual)

    def test_complete_manifest_requires_an_artifact_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = b"existing isolated artifact"
            path = Path(tmp) / "chunk.bin"
            path.write_bytes(payload)
            chunk = [{"index": 0, "start": 0, "stop": 1, "pair_keys": ["p1"],
                      "path": "chunk.bin", "sha256": hashlib.sha256(payload).hexdigest()}]
            with self.assertRaisesRegex(ManifestError, "artifact_root is required"):
                finalize_manifest(build_manifest(self.compatibility, 1), chunk)

    def test_real_bytes_writer_reader_and_cache_accept_complete_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            chunks = []
            for index, (start, stop, keys) in enumerate(((0, 2, ["p1", "p2"]),
                                                          (2, 3, ["p3"]))):
                relative = f"chunks/{index}.bin"
                artifact = root / relative
                artifact.parent.mkdir(exist_ok=True)
                payload = f"non-sensitive chunk {index}".encode()
                artifact.write_bytes(payload)
                chunks.append({"index": index, "start": start, "stop": stop,
                               "pair_keys": keys, "path": relative,
                               "sha256": hashlib.sha256(payload).hexdigest()})
            manifest = finalize_manifest(build_manifest(self.compatibility, 3), chunks,
                                         artifact_root=root)
            manifest_path = root / "manifest.json"
            write_manifest_create_only(manifest_path, manifest, chunks=chunks,
                                       artifact_root=root)
            loaded = read_manifest(manifest_path)
            self.assertEqual(loaded, manifest)
            self.assertEqual(validate_cache(self.compatibility, loaded, chunks,
                                            ["p1", "p2", "p3"], artifact_root=root), loaded)

    def test_rejects_changed_artifact_bytes_and_wrong_declared_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = b"real bytes"
            (root / "chunk.bin").write_bytes(payload)
            chunks = [{"index": 0, "start": 0, "stop": 1, "pair_keys": ["p1"],
                       "path": "chunk.bin", "sha256": hashlib.sha256(payload).hexdigest()}]
            manifest = finalize_manifest(build_manifest(self.compatibility, 1), chunks,
                                         artifact_root=root)
            (root / "chunk.bin").write_bytes(b"tampered")
            with self.assertRaisesRegex(ManifestError, "SHA-256"):
                validate_cache(self.compatibility, manifest, chunks, ["p1"], artifact_root=root)

    def test_rejects_missing_bytes_path_escape_duplicate_and_partial_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = build_manifest(self.compatibility, 1)
            missing = [{"index": 0, "start": 0, "stop": 1, "pair_keys": ["p1"],
                        "path": "missing.bin", "sha256": "0" * 64}]
            with self.assertRaisesRegex(ManifestError, "artifact file"):
                finalize_manifest(base, missing, artifact_root=root)
            escaped = [dict(missing[0], path="../outside.bin")]
            with self.assertRaisesRegex(ManifestError, "inside artifact_root"):
                finalize_manifest(base, escaped, artifact_root=root)
            with self.assertRaisesRegex(ManifestError, "partial or extra"):
                finalize_manifest(build_manifest(self.compatibility, 3), [
                    {"index": 0, "start": 0, "stop": 2, "pair_keys": ["p1", "p2"],
                     "path": "x", "sha256": "0" * 64}], artifact_root=root)
            duplicate = [
                {"index": 0, "start": 0, "stop": 1, "pair_keys": ["p1"]},
                {"index": 1, "start": 1, "stop": 2, "pair_keys": ["p1"]},
            ]
            duplicate_compatibility = dict(self.compatibility, chunk_size=1)
            with self.assertRaisesRegex(ManifestError, "duplicate pair key"):
                finalize_manifest(build_manifest(duplicate_compatibility, 2), duplicate,
                                  artifact_root=root)


if __name__ == "__main__":
    unittest.main()
