"""Integrity-repaired final runner for v2r1.

Scientific behavior (features, GB config, sampling, calibration, policies,
bounds, budgets, seeds, metric formulas) is inherited UNCHANGED from the
frozen v2 implementation. Only integrity mechanics differ:

1. Sealed-label artifacts are validated pre-final WITHOUT materializing the
   ``actual`` column (hash + parquet schema/row-count + pair-key-only read).
2. Sealed-test predictions are canonicalized and SHA-256 hashed into a
   PRE-LABEL FREEZE MANIFEST before any label access; FINAL_EVALUATION
   refuses to start without it and re-verifies the hash afterwards.
3. The process-wide SealedLabelGuard provides the runtime access audit; no
   audit count is hard-coded.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from experiments.icsec_final.authoritative_run_v2.artifact_producers import (
    ArtifactProducerError, DEVELOPMENT_ROLES, _record, _sha256,
)
from experiments.icsec_final.authoritative_run_v2.final_runner import (
    FINAL_BUDGET, FinalRunnerError, FinalSealedEvaluationRunner,
)
from experiments.icsec_final.authoritative_run_v2.provenance import sha256_file

from .sealed_guard import GUARD, sealed_artifact_metadata, sealed_pair_keys

LABEL_COLUMNS = {"pair_key", "actual"}


def validate_input_artifacts_label_free(metadata_path: str | Path) -> dict[str, Any]:
    """v2r1 replacement for v2 ``validate_input_artifacts``.

    Identical checks, EXCEPT the sealed-test artifact is inspected without
    loading label values: SHA-256, parquet schema, row count, and a
    pair-key-only read for the overlap check.
    """
    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    artifacts = metadata["artifacts"]
    for name, value in artifacts.items():
        path = Path(value["path"])
        if _sha256(path) != value["sha256"]:
            raise ArtifactProducerError(f"artifact hash differs: {name}")
    development = pd.read_parquet(artifacts["development"]["path"])
    blocking = pd.read_parquet(artifacts["blocking_miss"]["path"])
    sealed_meta = sealed_artifact_metadata(artifacts["sealed_test"]["path"])
    if set(development.columns) != {"pair_key", "actual", "role"} or not set(development.role).issubset(DEVELOPMENT_ROLES):
        raise ArtifactProducerError("development artifact has invalid role/scope")
    if set(sealed_meta["columns"]) != LABEL_COLUMNS:
        raise ArtifactProducerError("sealed artifact has invalid role/scope")
    if sealed_meta["row_count"] != artifacts["sealed_test"].get("row_count", sealed_meta["row_count"]):
        raise ArtifactProducerError("sealed artifact row count differs from manifest")
    if set(blocking.columns) != {"pair_key", "pair_type"} or (not blocking.empty and set(blocking.pair_type) != {"BLOCKING_MISS"}):
        raise ArtifactProducerError("blocking-miss artifact has invalid scope")
    keys = sealed_pair_keys(artifacts["sealed_test"]["path"])
    if keys.duplicated().any():
        raise ArtifactProducerError("duplicate sealed-label pair key")
    if set(development.pair_key) & set(keys):
        raise ArtifactProducerError("development and sealed artifact pair overlap")
    invariant = metadata["global_blocking_invariant"]
    if not invariant["covered_plus_missed_equals_all"]:
        raise ArtifactProducerError("blocking-miss invariant fails")
    return metadata


def build_real_fixture_label_free(metadata_path: str | Path, routed_workflow: pd.DataFrame,
                                  features17: pd.DataFrame, bert: pd.DataFrame) -> dict[str, Any]:
    """v2r1 fixture builder — identical output to v2 ``build_real_fixture``
    but validated via the label-free path."""
    metadata = validate_input_artifacts_label_free(metadata_path)
    artifacts = metadata["artifacts"]
    development = pd.read_parquet(artifacts["development"]["path"])
    del development  # scope check done in validation; roles read lazily later
    routes = pd.read_parquet(artifacts["blocking_miss_routes"]["path"])
    rows = routed_workflow[["pair_key", "pair_type", "role"]].copy()
    if not routes.empty:
        rows = pd.concat([rows, routes], ignore_index=True)
    rows["entity"] = rows.role.map(lambda role: f"role:{role}")
    development_paths = {role: str(artifacts["development"]["path"]) for role in DEVELOPMENT_ROLES}
    scored = rows.loc[rows.pair_type.eq("MODEL_SCORED"), ["pair_key"]].merge(
        routed_workflow[["pair_key", "profile_row_id_a", "profile_row_id_b"]], on="pair_key", validate="one_to_one")
    rows["feature_index"] = rows.pair_key.map({key: index for index, key in enumerate(scored.pair_key.tolist())})
    left = scored.merge(features17, on=["profile_row_id_a", "profile_row_id_b"], validate="one_to_one", sort=False)
    combined = left.merge(bert, on=["profile_row_id_a", "profile_row_id_b"], validate="one_to_one", sort=False)
    feature_columns = [column for column in features17.columns if column not in {"profile_row_id_a", "profile_row_id_b"}]
    return {"NOT_MANUSCRIPT_EVIDENCE": True, "rows": rows, "features17": combined[feature_columns].reset_index(drop=True),
            "bert": combined[["bert_cos"]].reset_index(drop=True), "scored_pair_keys": combined.pair_key.tolist(),
            "roles": {role: {f"role:{role}"} for role in ("TRAIN", "CALIBRATION", "POLICY_VALIDATION", "SEALED_TEST")},
            "development_label_paths": development_paths,
            "sealed_label_path": artifacts["sealed_test"]["path"], "blocking_miss_path": artifacts["blocking_miss"]["path"],
            "input_artifact_manifest": str(Path(metadata_path).resolve()),
            "legacy_name_sim_reachable": False}


class IntegrityRepairedRunner(FinalSealedEvaluationRunner):
    """v2 runner with pre-label prediction freeze and guard-driven audit."""

    PREDICTION_RELPATH = Path("sealed_predictions") / "predictions.parquet"
    FREEZE_MANIFEST = "pre_label_prediction_freeze.json"

    # ---- lifecycle phases exposed to the guard ---------------------------
    def train_and_calibrate(self) -> None:
        GUARD.set_phase("TRAINING")
        super().train_and_calibrate()

    def select_policies(self) -> None:
        GUARD.set_phase("POLICY_SELECTION")
        super().select_policies()

    def _prediction_path(self) -> Path:
        return self.output / self.PREDICTION_RELPATH

    def generate_sealed_predictions(self) -> None:
        GUARD.set_phase("PREDICTION_GENERATION")
        super().generate_sealed_predictions()
        # Canonicalize: deterministic row order for a stable hash.
        path = self._prediction_path()
        frame = pd.read_parquet(path).sort_values(["model_policy", "pair_key"], kind="mergesort").reset_index(drop=True)
        frame.to_parquet(path, index=False)
        manifest = {
            "phase": "PRE_LABEL_PREDICTION_FREEZE",
            "prediction_artifact": str(path.relative_to(self.output)),
            "prediction_sha256": sha256_file(path),
            "row_count": int(len(frame)),
            "pair_key_hash": hashlib.sha256(json.dumps(sorted(set(frame.pair_key)), sort_keys=True).encode()).hexdigest(),
            "model_identifiers": sorted(self.models),
            "policy_identifiers": sorted({"GB17_B0", *self.policies}),
            "pre_test_freeze_hashes": self.freeze_hashes,
            "generated_at": time.time(),
        }
        (self.output / self.FREEZE_MANIFEST).write_text(
            json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        # Verify the manifest round-trips and matches on-disk bytes.
        recorded = json.loads((self.output / self.FREEZE_MANIFEST).read_text(encoding="utf-8"))
        if recorded["prediction_sha256"] != sha256_file(path):
            raise FinalRunnerError("pre-label prediction freeze verification failed")
        self.prediction_freeze = recorded
        self.phase = "sealed_predictions_frozen"

    def final_evaluate(self) -> None:
        manifest_path = self.output / self.FREEZE_MANIFEST
        if not manifest_path.is_file():
            raise FinalRunnerError("final evaluation refused: predictions were not pre-label hashed")
        recorded = json.loads(manifest_path.read_text(encoding="utf-8"))
        path = self._prediction_path()
        if sha256_file(path) != recorded["prediction_sha256"]:
            raise FinalRunnerError("prediction artifact changed after pre-label freeze")
        self._pre_label_prediction_sha = recorded["prediction_sha256"]
        GUARD.set_phase("FINAL_EVALUATION")
        try:
            super().final_evaluate()
        finally:
            GUARD.set_phase("POST_EVALUATION")
        post_sha = sha256_file(path)
        if post_sha != self._pre_label_prediction_sha:
            raise FinalRunnerError("prediction pre/post label-access hash mismatch")
        current_keys = hashlib.sha256(json.dumps(sorted(set(pd.read_parquet(path).pair_key)), sort_keys=True).encode()).hexdigest()
        if current_keys != recorded["pair_key_hash"]:
            raise FinalRunnerError("prediction safe pair keys changed")
        self.prediction_immutability = {
            "pre_label_sha256": self._pre_label_prediction_sha,
            "post_evaluation_sha256": post_sha,
            "match": True,
        }
        (self.output / "prediction_immutability.json").write_text(
            json.dumps(self.prediction_immutability, indent=2) + "\n", encoding="utf-8")

    def run(self) -> dict[str, Any]:
        result = super().run()
        report = GUARD.report()
        (self.output / "process_label_access_audit.json").write_text(
            json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
        pre_final = report["pre_final_label_value_materializations"]
        if pre_final != 0:
            raise FinalRunnerError(f"pre-final sealed label value materializations: {pre_final}")
        result["PRE-FINAL SEALED LABEL VALUE MATERIALIZATIONS"] = pre_final
        result["FINAL_EVALUATION LABEL VALUE MATERIALIZATIONS"] = report["final_evaluation_label_value_materializations"]
        result["prediction_immutability"] = self.prediction_immutability
        result.pop("PRE-FINAL TEST LABEL READS", None)
        # Re-run capture so the two new integrity artifacts enter SHA256SUMS.
        self.capture_provenance()
        self.verify_hashes()
        return result
