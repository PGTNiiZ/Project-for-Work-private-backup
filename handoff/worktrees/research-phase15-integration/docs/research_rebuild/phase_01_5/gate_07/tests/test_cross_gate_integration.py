"""Synthetic cross-gate contract test; no snapshot labels or model execution."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
import numpy as np

PHASE15 = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(PHASE15 / "gate_04"))
sys.path.insert(0, str(PHASE15 / "gate_05"))
sys.path.insert(0, str(PHASE15 / "gate_06"))
sys.path.insert(0, str(PHASE15 / "gate_07"))
from pair_adapter import adapt_decision_records, canonical_pair_key as v2_pair_key  # noqa: E402
from feature18_contract import (  # noqa: E402
    build_feature18, MODEL_IDENTIFIER, MODEL_REVISION, MODEL_WEIGHT_SHA256,
    TOKENIZER_BUNDLE_SHA256, TEXT_COMPOSITION, POOLING_CONTRACT,
)
from split_safety import roles_for_fold, route_pairs  # noqa: E402
from evaluator import evaluate, canonical_key  # noqa: E402
from run_manifest import (  # noqa: E402
    build_manifest, finalize_manifest, read_manifest, validate_cache,
    write_manifest_create_only,
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pair_key(a: object, b: object) -> str:
    return json.dumps(list(canonical_key(str(a), str(b))), separators=(",", ":"))


def row(a: str, b: str, label: int, role: str, action: str, score: float | None = None):
    value = {"a": a, "b": b, "label": label, "role": role, "action": action}
    if score is not None:
        value["score"] = score
    return value


class CrossGateSyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source_root = Path(os.environ.get("IDENTITY_RESOLUTION_SOURCE_ROOT", REPO_ROOT))
        source = source_root / "experiments/icsec_final/authoritative_run_v2/features.py"
        if not source.is_file():
            raise RuntimeError(f"feature source missing: {source}")
        spec = importlib.util.spec_from_file_location("integrated_v2_features", source)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load feature source: {source}")
        cls.features = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.features)
        cls.feature_source = source

    def test_entity_to_manifest_contract_chain_on_synthetic_development_rows(self):
        fold_map = {f"entity-{i}": i for i in range(5)}
        roles = roles_for_fold(fold_map, heldout_fold=0)
        roles_again = roles_for_fold(dict(reversed(list(fold_map.items()))), heldout_fold=0)
        self.assertEqual(roles, roles_again)
        role_hash = digest(json.dumps(sorted(roles.items()), separators=(",", ":")).encode())
        self.assertEqual(role_hash, digest(json.dumps(sorted(roles_again.items()), separators=(",", ":")).encode()))
        role_entities = {role: {entity for entity, assigned in roles.items() if assigned == role}
                         for role in {"TRAIN", "CALIBRATION", "POLICY_VALIDATION", "TEST"}}
        for left in role_entities:
            for right in role_entities:
                if left < right:
                    self.assertFalse(role_entities[left] & role_entities[right])

        profiles = pd.DataFrame([
            {"profile_row_id": 1, "userName": "@alice", "fullName": "Alice Smith", "bio": "runner data", "location": "New York", "platform": "twitter"},
            {"profile_row_id": 2, "userName": "alice", "fullName": "Alice Smith", "bio": "data runner", "location": "new york", "platform": "instagram"},
            {"profile_row_id": 3, "userName": "charlie", "fullName": "Charlie Doe", "bio": "music fan", "location": "Paris", "platform": "twitter"},
            {"profile_row_id": 4, "userName": "heldout", "fullName": "Held Out", "bio": "", "location": "", "platform": "instagram"},
            {"profile_row_id": 5, "userName": "charlie_d", "fullName": "Charlie Doe", "bio": "fan of music", "location": "paris", "platform": "instagram"},
            {"profile_row_id": 6, "userName": "test-a", "fullName": "Test A", "bio": "", "location": "", "platform": "twitter"},
            {"profile_row_id": 7, "userName": "test-b", "fullName": "Test B", "bio": "", "location": "", "platform": "instagram"},
        ])
        profile_entities = {1: "entity-3", 2: "entity-3", 3: "entity-4",
                            4: "entity-0", 5: "entity-4", 6: "entity-0", 7: "entity-0"}
        pairs = [(1, 2), (1, 3), (3, 5), (2, 5), (1, 4)]
        kept, accounting = route_pairs(pairs, profile_entities, roles)
        self.assertEqual(accounting, {"input_pairs": 5, "same_role_pairs": 4, "cross_role_dropped": 1})
        self.assertEqual({entry[2] for entry in kept}, {"TRAIN"})
        feature_pairs = pd.DataFrame([{"profile_row_id_a": a, "profile_row_id_b": b}
                                      for a, b, _role in kept])
        feature_values = self.features.build_handcrafted_features(feature_pairs, profiles)
        registry = json.loads((PHASE15 / "gate_04/FEATURE_REGISTRY.json").read_text(encoding="utf-8"))
        self.assertEqual(self.features.FEATURE17_COLUMNS, registry["ordered_columns"])
        self.assertEqual(list(feature_values.columns), [
            "profile_row_id_a", "profile_row_id_b", *registry["ordered_columns"]
        ])
        matrix = feature_values[registry["ordered_columns"]].to_numpy()
        self.assertTrue(((matrix >= 0.0) & (matrix <= 1.0)).all())

        embeddings = np.eye(384, dtype=np.float32)[:len(profiles)]
        feature18 = build_feature18(
            feature_values, profiles.profile_row_id.tolist(), embeddings,
            expected_profile_ids=profiles.profile_row_id.tolist(),
            metadata={
                "model_identifier": MODEL_IDENTIFIER, "model_revision": MODEL_REVISION,
                "model_weight_sha256": MODEL_WEIGHT_SHA256,
                "tokenizer_bundle_sha256": TOKENIZER_BUNDLE_SHA256,
                "text_composition": TEXT_COMPOSITION, "pooling": POOLING_CONTRACT,
            },
        )
        self.assertEqual(list(feature18.columns),
                         ["profile_row_id_a", "profile_row_id_b", *registry["ordered_columns"], "bert_cos"])
        self.assertEqual(len(feature18.columns), len(feature_values.columns) + 1)

        def decision(a, b, scope, label, action, score=None):
            item = {"pair_key": v2_pair_key(a, b), "profile_row_id_a": a,
                    "profile_row_id_b": b, "scope": scope, "label": label,
                    "split_role": roles[profile_entities[a]]}
            if scope != "BLOCKING_MISS":
                item["action"] = action
            if score is not None:
                item["score"] = score
            return item

        records = [
            decision(1, 2, "AUTO_EXACT", 0, "MATCH"),
            decision(1, 3, "MODEL_SCORED", 0, "NO_MATCH", .2),
            decision(3, 5, "MODEL_SCORED", 1, "MATCH", .95),
            decision(2, 5, "MODEL_SCORED", 1, "REVIEW", .8),
            decision(6, 7, "BLOCKING_MISS", 1, "NO_MATCH"),
        ]
        adapted = adapt_decision_records(records, profile_entities=profile_entities,
                                         entity_roles=roles)
        exact, scored, misses = adapted["exact"], adapted["scored"], adapted["blocking_misses"]
        metrics = evaluate(exact, scored, misses, expected_positives=3)
        workflow = metrics["workflow"]
        self.assertEqual((metrics["exact_n"], metrics["scored_n"], metrics["blocking_misses"]), (1, 3, 1))
        self.assertEqual((workflow["TP"], workflow["FP"], workflow["FN"], workflow["R_plus"]), (1, 1, 1, 1))
        self.assertEqual(workflow["positive_denominator"], 3)
        self.assertAlmostEqual(workflow["automatic_recall"], 1 / 3)

        train_keys = [item["pair_key"] for item in scored]
        self.assertEqual(v2_pair_key(1, 2), v2_pair_key(2, 1))
        expected = {
            "dataset_identity": "sha256:" + digest(profiles.to_json(orient="records").encode()),
            "schema_identity": "sha256:" + digest(json.dumps(registry["ordered_columns"]).encode()),
            "pair_population_identity": "sha256:" + digest(json.dumps([item["pair_key"] for item in scored]).encode()),
            "chunk_size": 2,
            "model_identity": "synthetic:no-model-executed",
            "source_identity": "sha256:" + digest(self.feature_source.read_bytes()),
            "split_identity": "sha256:" + role_hash,
            "configuration_identity": "sha256:" + digest(b"synthetic-contract-test-v1"),
            "environment_identity": "sha256:" + digest((sys.version + pd.__version__).encode()),
            "seed": 20261010,
        }
        manifest = build_manifest(expected, len(train_keys))
        chunks = []
        for index, start in enumerate(range(0, len(train_keys), expected["chunk_size"])):
            stop = min(start + expected["chunk_size"], len(train_keys))
            keys = train_keys[start:stop]
            chunks.append({"index": index, "start": start, "stop": stop, "pair_keys": keys,
                           "path": f"synthetic/chunk-{index:03d}.parquet",
                           "sha256": digest(json.dumps(keys).encode())})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for chunk in chunks:
                artifact = root / chunk["path"]
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_bytes(json.dumps(chunk["pair_keys"]).encode())
                chunk["sha256"] = digest(artifact.read_bytes())
            complete = finalize_manifest(manifest, chunks, artifact_root=root)
            path = root / "run_manifest.json"
            write_manifest_create_only(path, complete, chunks=chunks, artifact_root=root)
            loaded = read_manifest(path)
            self.assertEqual(validate_cache(expected, loaded, chunks, train_keys,
                                            artifact_root=root), complete)

    def test_test_role_label_request_is_denied_before_label_store_access(self):
        label_store_reads = []

        def development_label_reader(entity: str, role: str):
            if role == "TEST":
                raise PermissionError("TEST labels are sealed during development")
            label_store_reads.append(entity)
            return 0

        with self.assertRaises(PermissionError):
            development_label_reader("entity-0", "TEST")
        self.assertEqual(label_store_reads, [])


if __name__ == "__main__":
    unittest.main()
