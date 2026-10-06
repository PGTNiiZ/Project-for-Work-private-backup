"""Failure-injection and integrity tests for the v2r1 repaired runner."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from experiments.icsec_final.authoritative_run_v2.final_runner import (
    FinalRunnerError, make_synthetic_fixture,
)
from experiments.icsec_final.authoritative_run_v2r1.final_runner_r1 import (
    IntegrityRepairedRunner, validate_input_artifacts_label_free,
)
from experiments.icsec_final.authoritative_run_v2r1.sealed_guard import (
    GUARD, SealedLabelGuard, SealedLabelViolation, sealed_artifact_metadata, sealed_pair_keys,
)

SEED = 17
BUDGET = 16


def _sealed_fixture(tmp_path: Path) -> dict:
    """Synthetic fixture converted to on-disk sealed/development artifacts."""
    fixture = make_synthetic_fixture()
    # LazySealedLabelStore requires 64-hex safe pair keys; remap synthetic keys.
    remap = {k: hashlib.sha256(f"v2r1-test:{k}".encode()).hexdigest()
             for k in fixture["rows"].pair_key}
    fixture["rows"]["pair_key"] = fixture["rows"].pair_key.map(remap)
    fixture["sealed_labels"] = {remap[k]: v for k, v in fixture["sealed_labels"].items()}
    sealed_dir = tmp_path / "sealed"; sealed_dir.mkdir()
    sealed = pd.DataFrame({"pair_key": list(fixture["sealed_labels"]),
                           "actual": list(fixture["sealed_labels"].values())})
    sealed_path = sealed_dir / "labels.parquet"
    sealed.to_parquet(sealed_path, index=False)
    dev_rows = []
    rows = fixture["rows"]
    for role, labels in fixture["development_labels"].items():
        keys = rows.loc[(rows.role == role) & (rows.pair_type == "MODEL_SCORED"), "pair_key"].tolist()
        dev_rows += [{"pair_key": k, "actual": l, "role": role} for k, l in zip(keys, labels)]
    dev_path = tmp_path / "development.parquet"
    pd.DataFrame(dev_rows).to_parquet(dev_path, index=False)
    miss = rows.loc[rows.pair_type == "BLOCKING_MISS", ["pair_key", "pair_type"]]
    miss_path = tmp_path / "blocking.parquet"
    miss.to_parquet(miss_path, index=False)
    fixture.pop("sealed_labels")
    fixture["sealed_label_path"] = str(sealed_path)
    fixture["development_label_paths"] = {r: str(dev_path) for r in fixture["development_labels"]}
    fixture["blocking_miss_path"] = str(miss_path)
    return fixture


@pytest.fixture(autouse=True)
def fresh_guard():
    GUARD.uninstall()
    GUARD.sealed_paths.clear()
    GUARD.events.clear()
    GUARD.phase = "PREPARATION"
    yield
    GUARD.uninstall()
    GUARD.sealed_paths.clear()
    GUARD.events.clear()
    GUARD.phase = "PREPARATION"


def _run(tmp_path: Path) -> IntegrityRepairedRunner:
    fixture = _sealed_fixture(tmp_path)
    GUARD.install()
    GUARD.register(fixture["sealed_label_path"])
    runner = IntegrityRepairedRunner(fixture, tmp_path / "out", seed=SEED, budget=BUDGET)
    return runner


def test_full_run_passes_and_audit_is_zero(tmp_path):
    runner = _run(tmp_path)
    result = runner.run()
    assert result["PRE-FINAL SEALED LABEL VALUE MATERIALIZATIONS"] == 0
    assert result["FINAL_EVALUATION LABEL VALUE MATERIALIZATIONS"] >= 1
    assert result["prediction_immutability"]["match"] is True
    report = json.loads((tmp_path / "out" / "process_label_access_audit.json").read_text())
    assert report["pre_final_label_value_materializations"] == 0
    manifest = json.loads((tmp_path / "out" / "pre_label_prediction_freeze.json").read_text())
    assert manifest["phase"] == "PRE_LABEL_PREDICTION_FREEZE"
    # Freeze manifest must be part of the final hash closure.
    assert "pre_label_prediction_freeze.json" in (tmp_path / "out" / "SHA256SUMS.txt").read_text()


def test_pre_final_label_materialization_raises(tmp_path):
    runner = _run(tmp_path)
    with pytest.raises(SealedLabelViolation):
        pd.read_parquet(runner.fixture["sealed_label_path"])  # helper bypass attempt


def test_pre_final_label_column_request_raises(tmp_path):
    runner = _run(tmp_path)
    with pytest.raises(SealedLabelViolation):
        pd.read_parquet(runner.fixture["sealed_label_path"], columns=["pair_key", "actual"])


def test_label_free_inspection_is_allowed_pre_final(tmp_path):
    runner = _run(tmp_path)
    meta = sealed_artifact_metadata(runner.fixture["sealed_label_path"])
    assert set(meta["columns"]) == {"pair_key", "actual"} and meta["row_count"] > 0
    keys = sealed_pair_keys(runner.fixture["sealed_label_path"])
    assert len(keys) == meta["row_count"]
    assert GUARD.pre_final_materializations() == 0


def test_final_evaluation_requires_freeze_manifest(tmp_path):
    runner = _run(tmp_path)
    runner.validate_inputs(); runner.validate_roles(); runner.train_and_calibrate()
    runner.select_policies(); runner.assert_fairness(); runner.freeze_pre_test()
    runner.generate_sealed_predictions()
    (runner.output / IntegrityRepairedRunner.FREEZE_MANIFEST).unlink()
    with pytest.raises(FinalRunnerError, match="not pre-label hashed"):
        runner.final_evaluate()


def test_prediction_tamper_between_freeze_and_evaluation_fails(tmp_path):
    runner = _run(tmp_path)
    runner.validate_inputs(); runner.validate_roles(); runner.train_and_calibrate()
    runner.select_policies(); runner.assert_fairness(); runner.freeze_pre_test()
    runner.generate_sealed_predictions()
    path = runner.output / IntegrityRepairedRunner.PREDICTION_RELPATH
    frame = pd.read_parquet(path)
    frame.loc[0, "decision"] = 2
    frame.to_parquet(path, index=False)
    with pytest.raises(FinalRunnerError, match="changed after pre-label freeze"):
        runner.final_evaluate()


def test_pair_key_tamper_detected(tmp_path):
    runner = _run(tmp_path)
    runner.validate_inputs(); runner.validate_roles(); runner.train_and_calibrate()
    runner.select_policies(); runner.assert_fairness(); runner.freeze_pre_test()
    runner.generate_sealed_predictions()
    manifest_path = runner.output / IntegrityRepairedRunner.FREEZE_MANIFEST
    manifest = json.loads(manifest_path.read_text())
    manifest["pair_key_hash"] = hashlib.sha256(b"tampered").hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    with pytest.raises(FinalRunnerError):
        runner.final_evaluate()


def test_unfrozen_policy_rejected(tmp_path):
    runner = _run(tmp_path)
    runner.validate_inputs(); runner.validate_roles(); runner.train_and_calibrate()
    runner.select_policies(); runner.assert_fairness(); runner.freeze_pre_test()
    runner.policies["B1"] = (0.999, 0.999)  # mutate after freeze
    with pytest.raises(FinalRunnerError, match="freeze artifact changed"):
        runner.generate_sealed_predictions()


def test_stale_lineage_hash_rejected(tmp_path):
    fixture = _sealed_fixture(tmp_path)
    metadata = {
        "artifacts": {
            "development": {"path": fixture["development_label_paths"]["TRAIN"],
                            "sha256": "0" * 64},
        },
        "global_blocking_invariant": {"covered_plus_missed_equals_all": True},
    }
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(metadata))
    from experiments.icsec_final.authoritative_run_v2.artifact_producers import ArtifactProducerError
    with pytest.raises(ArtifactProducerError, match="hash differs"):
        validate_input_artifacts_label_free(meta_path)


def test_label_free_validation_does_not_materialize(tmp_path, monkeypatch):
    """The v2r1 validator must never load sealed label values."""
    fixture = _sealed_fixture(tmp_path)
    sealed_path = Path(fixture["sealed_label_path"])
    dev_path = Path(fixture["development_label_paths"]["TRAIN"])
    miss_path = Path(fixture["blocking_miss_path"])
    routes_path = tmp_path / "routes.parquet"
    pd.DataFrame(columns=["pair_key", "pair_type", "role"]).to_parquet(routes_path, index=False)

    def record(path: Path) -> dict:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return {"path": str(path.resolve()), "sha256": digest, "bytes": path.stat().st_size,
                "row_count": int(len(pd.read_parquet(path)))}

    metadata = {"artifacts": {"development": record(dev_path), "sealed_test": record(sealed_path),
                              "blocking_miss": record(miss_path), "blocking_miss_routes": record(routes_path)},
                "global_blocking_invariant": {"covered_plus_missed_equals_all": True}}
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(metadata))
    GUARD.install()
    GUARD.register(sealed_path)
    validate_input_artifacts_label_free(meta_path)  # must not raise
    assert GUARD.pre_final_materializations() == 0


def test_duplicate_final_join_keys_rejected(tmp_path):
    runner = _run(tmp_path)
    runner.validate_inputs(); runner.validate_roles(); runner.train_and_calibrate()
    runner.select_policies(); runner.assert_fairness(); runner.freeze_pre_test()
    runner.generate_sealed_predictions()
    path = runner.output / IntegrityRepairedRunner.PREDICTION_RELPATH
    frame = pd.read_parquet(path)
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    frame.to_parquet(path, index=False)
    with pytest.raises(FinalRunnerError):
        runner.final_evaluate()


def test_guard_counts_are_derived_not_hardcoded():
    guard = SealedLabelGuard()
    guard.phase = "TRAINING"
    guard._audit(resource="x", operation="o", columns=None, materialized=True, allowed=True)
    assert guard.pre_final_materializations() == 1
    guard.phase = "FINAL_EVALUATION"
    guard._audit(resource="x", operation="o", columns=None, materialized=True, allowed=True)
    assert guard.final_materializations() == 1
