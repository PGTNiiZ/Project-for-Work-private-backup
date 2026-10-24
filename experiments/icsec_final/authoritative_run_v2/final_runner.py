"""Leakage-safe final sealed-evaluation execution primitives for v2."""
from __future__ import annotations

import hashlib
import json
import pickle
import platform
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression

from .features import FEATURE17_COLUMNS, FEATURE18_COLUMNS
from .label_sealing import LabelAccessError, SealedLabels
from .real_adapters import AdapterError, LazySealedLabelStore, safe_final_join
from .policies import B0_FIXED, BOUNDS, b0_decide, b1_search, b2_sobol_search, b3_ga_search, decide_four_parameter
from .provenance import sha256_file

FINAL_BUDGET = 12000
GB_PARAMS = {"n_estimators": 300, "learning_rate": 0.05, "max_depth": 6, "random_state": 42}
ROLES = ("TRAIN", "CALIBRATION", "POLICY_VALIDATION", "SEALED_TEST")
TRAIN_NEGATIVE_RATIO = 3.0


def deterministic_sample_indices(labels: np.ndarray, *, ratio: float, seed: int) -> np.ndarray:
    """Apply the frozen deterministic positive-plus-negative undersampling."""
    rng = np.random.default_rng(seed)
    positive = np.where(labels == 1)[0]
    negative = np.where(labels == 0)[0]
    count = min(len(negative), int(len(positive) * ratio))
    sampled_negative = rng.choice(negative, size=count, replace=False)
    keep = np.concatenate([positive, sampled_negative])
    rng.shuffle(keep)
    return keep


class FinalRunnerError(RuntimeError):
    pass


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else str(x))


def _digest_value(value: Any) -> str:
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _metrics(frame: pd.DataFrame) -> dict[str, float | int]:
    d, y = frame["decision"].to_numpy(), frame["actual"].to_numpy()
    tp = int(((d == 2) & (y == 1)).sum())
    fp = int(((d == 2) & (y == 0)).sum())
    fn = int(((d == 0) & (y == 1)).sum())
    review = int((d == 1).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {"TP": tp, "FP": fp, "FN": fn, "REVIEW": review, "precision": precision, "recall": recall,
            "F1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            "U": 2 * fp + fn + 0.1 * review}


class FinalSealedEvaluationRunner:
    """Runs one explicitly authorized v2 outer split; fixture mode is non-evidence."""

    def __init__(self, fixture: dict[str, Any], output_dir: str | Path, *, seed: int, budget: int = FINAL_BUDGET):
        if budget not in ({FINAL_BUDGET, 16} if fixture.get("NOT_MANUSCRIPT_EVIDENCE") else {FINAL_BUDGET}):
            raise FinalRunnerError("budget violates frozen protocol")
        self.fixture, self.seed, self.budget = fixture, seed, budget
        self.output = Path(output_dir)
        self.output.mkdir(parents=True, exist_ok=True)
        self.phase = "initial"
        self.audit: list[dict[str, Any]] = []
        sealed_path = fixture.get("sealed_label_path")
        self.sealer = LazySealedLabelStore(sealed_path) if sealed_path else SealedLabels(dict(fixture["sealed_labels"]))
        self.development_label_paths = {role: Path(path) for role, path in fixture.get("development_label_paths", {}).items()}
        self.blocking_miss_path = Path(fixture["blocking_miss_path"]) if fixture.get("blocking_miss_path") else None
        self.rows = fixture["rows"].copy()
        self.roles = {role: set(fixture["roles"][role]) for role in ROLES}
        self.policies: dict[str, tuple[float, ...]] = {}
        self.policy_metadata: dict[str, Any] = {}
        self.models: dict[str, Any] = {}
        self.calibrators: dict[str, Any] = {}
        self.freeze_hashes: dict[str, str] = {}
        self.summary: dict[str, Any] = {}
        self.required_inputs = [self.output / "fixture_input.json"]
        self.required_inputs[0].write_text(_json({"seed": seed, "roles": {k: sorted(v) for k, v in self.roles.items()}, "rows": self.rows.to_dict("records")}) + "\n")

    def sealed_labels(self, keys: list[str], *, phase: str) -> list[int]:
        try:
            if isinstance(self.sealer, LazySealedLabelStore):
                values = self.sealer.read(keys, phase=phase)["actual"].tolist()
            else:
                values = self.sealer.join(keys, phase=phase)
            return values
        except (LabelAccessError, AdapterError) as error:
            self.audit.extend(self.sealer.audit[-1:])
            raise FinalRunnerError(f"sealed labels denied before final evaluation: {error}") from error

    def validate_inputs(self) -> None:
        if self.fixture.get("legacy_name_sim_reachable"):
            raise FinalRunnerError("legacy name similarity path is prohibited")
        if list(self.fixture["features17"].columns) != FEATURE17_COLUMNS:
            raise FinalRunnerError("GB-17 feature schema must contain exactly frozen 17 features")
        if list(self.fixture["bert"].columns) != ["bert_cos"] or FEATURE18_COLUMNS != FEATURE17_COLUMNS + ["bert_cos"]:
            raise FinalRunnerError("GB-18 must be GB-17 plus bert_cos only")
        if not self.rows["pair_key"].is_unique or set(self.rows["role"]) - set(ROLES):
            raise FinalRunnerError("invalid pair/role input")
        self.phase = "inputs_validated"

    def validate_roles(self) -> None:
        for i, left in enumerate(ROLES):
            for right in ROLES[i + 1:]:
                if self.roles[left] & self.roles[right]:
                    raise FinalRunnerError(f"entity overlap between {left} and {right}")
        assigned = self.rows["entity"].map({entity: role for role, values in self.roles.items() for entity in values})
        if assigned.isna().any() or not (assigned == self.rows["role"]).all():
            raise FinalRunnerError("cross-role or unassigned pair is not permitted")
        self.phase = "roles_validated"

    def _role_frame(self, role: str) -> pd.DataFrame:
        return self.rows.loc[(self.rows.role == role) & (self.rows.pair_type == "MODEL_SCORED")].copy()

    def _role_labels(self, frame: pd.DataFrame, role: str) -> np.ndarray:
        if role not in {"TRAIN", "CALIBRATION", "POLICY_VALIDATION"}:
            raise FinalRunnerError("only explicit development roles may provide pre-final labels")
        if self.development_label_paths:
            path = self.development_label_paths.get(role)
            if path is None or not path.is_file():
                raise FinalRunnerError(f"missing development-label artifact for {role}")
            labels = pd.read_parquet(path)
            if set(labels.columns) != {"pair_key", "actual", "role"} or not set(labels.role).issubset({"TRAIN", "CALIBRATION", "POLICY_VALIDATION"}):
                raise FinalRunnerError(f"wrong role labels supplied to {role}")
            labels = labels.loc[labels.role == role, ["pair_key", "actual"]]
            joined = frame[["pair_key"]].merge(labels, on="pair_key", how="left", validate="one_to_one", sort=False)
            if joined.actual.isna().any() or len(joined) != len(frame):
                raise FinalRunnerError(f"incomplete development labels for {role}")
            return joined.actual.to_numpy(dtype=np.int8)
        values = self.fixture["development_labels"].get(role)
        if values is None or len(values) != len(frame):
            raise FinalRunnerError(f"missing role labels for {role}")
        return np.asarray(values, dtype=np.int8)

    def _feature_indices(self, frame: pd.DataFrame) -> np.ndarray:
        return frame["feature_index"].to_numpy(dtype=int) if "feature_index" in frame.columns else frame.index.to_numpy(dtype=int)

    def train_and_calibrate(self) -> None:
        train, calibration = self._role_frame("TRAIN"), self._role_frame("CALIBRATION")
        y_train, y_calibration = self._role_labels(train, "TRAIN"), self._role_labels(calibration, "CALIBRATION")
        train_index, calibration_index = self._feature_indices(train), self._feature_indices(calibration)
        sampled = deterministic_sample_indices(y_train, ratio=TRAIN_NEGATIVE_RATIO, seed=self.seed)
        sampled_train_index, sampled_y_train = train_index[sampled], y_train[sampled]
        if len(np.unique(y_train)) != 2 or len(np.unique(y_calibration)) != 2:
            raise FinalRunnerError("training and calibration require both classes")
        for name, columns in (("GB-17", FEATURE17_COLUMNS), ("GB-18", FEATURE18_COLUMNS)):
            x_train = pd.concat([self.fixture["features17"], self.fixture["bert"]], axis=1)[columns].iloc[sampled_train_index].to_numpy(np.float32)
            x_cal = pd.concat([self.fixture["features17"], self.fixture["bert"]], axis=1)[columns].iloc[calibration_index].to_numpy(np.float32)
            model = GradientBoostingClassifier(**GB_PARAMS).fit(x_train, sampled_y_train)
            raw = model.predict_proba(x_cal)[:, 1]
            calibrator = IsotonicRegression(out_of_bounds="clip").fit(raw, y_calibration)
            self.models[name], self.calibrators[name] = model, calibrator
            model_dir = self.output / "models"; model_dir.mkdir(exist_ok=True)
            for artifact, value in ((f"{name}_model.pkl", model), (f"{name}_calibrator.pkl", calibrator)):
                with (model_dir / artifact).open("wb") as stream: pickle.dump(value, stream)
        self.training_provenance = {"configuration": GB_PARAMS, "train_negative_ratio": TRAIN_NEGATIVE_RATIO,
            "training_rows_before_sampling": int(len(y_train)), "training_rows_after_sampling": int(len(sampled_y_train)),
            "training_class_counts_after_sampling": {"positive": int((sampled_y_train == 1).sum()), "negative": int((sampled_y_train == 0).sum())},
            "sampled_training_pair_key_hash": _digest_value(train.iloc[sampled]["pair_key"].tolist()),
            "feature_schema_hash": _digest_value(FEATURE17_COLUMNS),
            "gb18_schema_hash": _digest_value(FEATURE18_COLUMNS), "training_entity_manifest_hash": _digest_value(sorted(self.roles["TRAIN"])),
            "source_code_hash": sha256_file(Path(__file__))}
        (self.output / "training.json").write_text(_json(self.training_provenance) + "\n")
        self.phase = "calibrated"

    def select_policies(self) -> None:
        validation = self._role_frame("POLICY_VALIDATION")
        y = self._role_labels(validation, "POLICY_VALIDATION")
        validation_index = self._feature_indices(validation)
        x18 = pd.concat([self.fixture["features17"], self.fixture["bert"]], axis=1)[FEATURE18_COLUMNS].iloc[validation_index].to_numpy(np.float32)
        p = self.calibrators["GB-18"].predict(self.models["GB-18"].predict_proba(x18)[:, 1])
        name = self.fixture["features17"].iloc[validation_index]["name_sim"].to_numpy()
        self.policies["B0"] = B0_FIXED
        self.policies["B1"], b1 = b1_search(p, y, budget=self.budget)
        self.policies["B3"], b3 = b3_ga_search(p, name, y, budget=self.budget, seed=self.seed)
        self.policies["B2"], b2 = b2_sobol_search(p, name, y, budget=b3["realized_evaluations"], seed=self.seed)
        self.policy_metadata = {"B0": {"class": "simple_fixed", "optimizer": None},
            "B1": {"class": "simple_two_threshold", "optimizer": "sobol", **b1},
            "B2": {"class": "expanded_four_parameter", "optimizer": "sobol", "bounds": BOUNDS.tolist(), **b2},
            "B3": {"class": "expanded_four_parameter", "optimizer": "seeded_ga", "bounds": BOUNDS.tolist(), "seed": self.seed, **b3}}
        for name_, override in self.fixture.get("policy_override", {}).items(): self.policy_metadata[name_].update(override)
        (self.output / "policies.json").write_text(_json({"parameters": self.policies, "metadata": self.policy_metadata}) + "\n")
        self.phase = "policies_selected"

    def assert_fairness(self) -> None:
        b2, b3 = self.policy_metadata["B2"], self.policy_metadata["B3"]
        passed = b2["class"] == b3["class"] and b2["bounds"] == b3["bounds"] and b2["realized_evaluations"] == b3["realized_evaluations"] == self.budget
        self.fairness = {"passed": passed, "policy_class_equal": b2["class"] == b3["class"], "bounds_equal": b2["bounds"] == b3["bounds"],
                         "decision_implementation": "decide_four_parameter", "objective": "2*FP+FN+0.1*REVIEW",
                         "validation_dataset_hash": _digest_value(self._role_frame("POLICY_VALIDATION")["pair_key"].tolist()), "budget": self.budget}
        (self.output / "fairness.json").write_text(_json(self.fairness) + "\n")
        if not passed: raise FinalRunnerError("B2/B3 fairness assertion failed")

    def freeze_pre_test(self) -> None:
        paths = list((self.output / "models").glob("*.pkl")) + [self.output / "policies.json", self.output / "training.json", self.output / "fairness.json"]
        self.freeze_hashes = {str(path.relative_to(self.output)): sha256_file(path) for path in sorted(paths)}
        self.freeze_hashes["__policy_state__"] = _digest_value(self.policies)
        (self.output / "pre_test_freeze.json").write_text(_json({"artifacts": self.freeze_hashes, "phase": "PRE_TEST"}) + "\n")
        self.phase = "frozen"

    def _verify_freeze(self) -> None:
        state_hash = self.freeze_hashes.get("__policy_state__")
        file_hashes = {path: value for path, value in self.freeze_hashes.items() if path != "__policy_state__"}
        if (not file_hashes or _digest_value(self.policies) != state_hash
                or any(sha256_file(self.output / path) != value for path, value in file_hashes.items())):
            raise FinalRunnerError("pre-test freeze artifact changed")

    def generate_sealed_predictions(self) -> None:
        self._verify_freeze()
        test = self._role_frame("SEALED_TEST")
        test_index = self._feature_indices(test)
        all_features = pd.concat([self.fixture["features17"], self.fixture["bert"]], axis=1)
        x18 = all_features[FEATURE18_COLUMNS].iloc[test_index].to_numpy(np.float32)
        probability = self.calibrators["GB-18"].predict(self.models["GB-18"].predict_proba(x18)[:, 1])
        x17 = all_features[FEATURE17_COLUMNS].iloc[test_index].to_numpy(np.float32)
        probability17 = self.calibrators["GB-17"].predict(self.models["GB-17"].predict_proba(x17)[:, 1])
        name = self.fixture["features17"].iloc[test_index]["name_sim"].to_numpy()
        predictions = [pd.DataFrame({"pair_key": test.pair_key.to_numpy(), "model_policy": "GB17_B0",
                                     "calibrated_probability": probability17, "decision": b0_decide(probability17, B0_FIXED)})]
        for policy, params in self.policies.items():
            decision = b0_decide(probability, params) if policy in {"B0", "B1"} else decide_four_parameter(probability, name, params)
            predictions.append(pd.DataFrame({"pair_key": test.pair_key.to_numpy(), "model_policy": policy, "calibrated_probability": probability, "decision": decision}))
        out = pd.concat(predictions, ignore_index=True); directory = self.output / "sealed_predictions"; directory.mkdir(exist_ok=True)
        out.to_parquet(directory / "predictions.parquet", index=False)
        self.phase = "sealed_predictions_frozen"

    def final_evaluate(self) -> None:
        if self.phase != "sealed_predictions_frozen": raise FinalRunnerError("final evaluation requires frozen sealed predictions")
        prediction = pd.read_parquet(self.output / "sealed_predictions" / "predictions.parquet")
        test_rows = self.rows.loc[self.rows.role == "SEALED_TEST", ["pair_key", "pair_type"]]
        decisions_dir = self.output / "decisions"; decisions_dir.mkdir(exist_ok=True)
        self.summary = {}
        for policy, scored in prediction.groupby("model_policy", sort=True):
            if isinstance(self.sealer, LazySealedLabelStore):
                candidate_rows = test_rows.loc[test_rows.pair_type != "BLOCKING_MISS"].copy()
                static = candidate_rows.loc[candidate_rows.pair_type != "MODEL_SCORED"].copy()
                static["decision"] = np.where(static.pair_type == "AUTO_EXACT", 2, 0)
                static["calibrated_probability"] = np.nan
                complete = pd.concat([scored.drop(columns="model_policy"), static[["pair_key", "decision", "calibrated_probability"]]], ignore_index=True)
                model = safe_final_join(complete, self.sealer, phase="FINAL_EVALUATION").merge(candidate_rows, on="pair_key", how="left", validate="one_to_one", sort=False)
                self.audit.extend(self.sealer.audit[-1:])
                misses = test_rows.loc[test_rows.pair_type == "BLOCKING_MISS", ["pair_key", "pair_type"]].copy()
                if not misses.empty:
                    if self.blocking_miss_path is None or not self.blocking_miss_path.is_file():
                        raise FinalRunnerError("blocking-miss artifact is required for workflow evaluation")
                    blocking = pd.read_parquet(self.blocking_miss_path)
                    if set(blocking.columns) != {"pair_key", "pair_type"} or set(blocking.pair_type) != {"BLOCKING_MISS"}:
                        raise FinalRunnerError("blocking-miss artifact has invalid scope")
                    misses = misses.merge(blocking, on=["pair_key", "pair_type"], how="inner", validate="one_to_one")
                    if len(misses) != int((test_rows.pair_type == "BLOCKING_MISS").sum()):
                        raise FinalRunnerError("blocking-miss artifact omits workflow positives")
                    misses["actual"], misses["decision"], misses["calibrated_probability"] = 1, 0, np.nan
                    model = pd.concat([model, misses], ignore_index=True)
            else:
                labels = self.sealed_labels(test_rows.pair_key.tolist(), phase="final_evaluation")
                self.audit.extend(self.sealer.audit[-1:])
                labeled = test_rows.assign(actual=labels)
                model = labeled.merge(scored.drop(columns="model_policy"), on="pair_key", how="left", validate="one_to_one")
                model.loc[model.pair_type == "AUTO_EXACT", "decision"] = 2
                model.loc[model.pair_type == "BLOCKING_MISS", "decision"] = 0
            model["decision"] = model.decision.astype(np.int8)
            for scope, frame in (("exact_tier", model[model.pair_type == "AUTO_EXACT"]), ("model_scored", model[model.pair_type == "MODEL_SCORED"]), ("workflow", model)):
                frame = frame.copy()
                frame["metric_scope"] = scope.upper()
                frame.to_parquet(decisions_dir / f"{policy}_{scope}.parquet", index=False)
            self.summary[policy] = _metrics(model)
        (self.output / "summary.json").write_text(_json(self.summary) + "\n")
        (self.output / "label_access_audit.json").write_text(_json(self.audit) + "\n")
        if sum(not row["allowed"] for row in self.audit) != 0: raise FinalRunnerError("pre-final sealed-label reads were allowed")
        self.phase = "final_evaluated"

    def independent_recompute(self) -> None:
        independent = {policy: _metrics(pd.read_parquet(self.output / "decisions" / f"{policy}_workflow.parquet")) for policy in self.summary}
        if _json(independent) != _json(self.summary): raise FinalRunnerError("independent metric recomputation disagrees with runner summary")
        (self.output / "independent_metrics.json").write_text(_json(independent) + "\n")
        self.phase = "independently_recomputed"

    def capture_provenance(self) -> None:
        if not self.required_inputs or any(not path.is_file() for path in self.required_inputs): raise FinalRunnerError("required provenance input is missing")
        manifest = {str(path.relative_to(self.output)): sha256_file(path) for path in self.output.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"}
        (self.output / "SHA256SUMS.txt").write_text("".join(f"{value}  {path}\n" for path, value in sorted(manifest.items())))
        self.phase = "complete"

    def verify_hashes(self) -> None:
        manifest = {line.split("  ", 1)[1].strip(): line.split("  ", 1)[0] for line in (self.output / "SHA256SUMS.txt").read_text().splitlines()}
        if any(not (self.output / path).is_file() or sha256_file(self.output / path) != value for path, value in manifest.items()): raise FinalRunnerError("final hash verification failed")

    def run(self) -> dict[str, Any]:
        self.validate_inputs(); self.validate_roles(); self.train_and_calibrate(); self.select_policies(); self.assert_fairness(); self.freeze_pre_test()
        self.generate_sealed_predictions(); self.final_evaluate(); self.independent_recompute(); self.capture_provenance(); self.verify_hashes()
        return {"NOT_MANUSCRIPT_EVIDENCE": bool(self.fixture.get("NOT_MANUSCRIPT_EVIDENCE")), "PRE-FINAL TEST LABEL READS": 0,
                "independent_metrics_match": True, "fairness": self.fairness}


def make_synthetic_fixture() -> dict[str, Any]:
    rng = np.random.default_rng(17); rows = []; features = []
    roles = {role: {f"e{i}" for i in range(start, start + 4)} for role, start in zip(ROLES, range(0, 16, 4))}
    development_labels: dict[str, list[int]] = {}; sealed_labels: dict[str, int] = {}
    i = 0
    for role, entities in roles.items():
        labels = []
        for entity in sorted(entities):
            for label in (0, 1):
                key = f"p{i}"; kind = "MODEL_SCORED"; rows.append({"pair_key": key, "entity": entity, "role": role, "pair_type": kind})
                base = np.full(17, 0.15 + .7 * label) + rng.normal(0, .02, 17); base[6] = .2 + .6 * label
                features.append(np.clip(base, 0, 1)); labels.append(label)
                if role == "SEALED_TEST": sealed_labels[key] = label
                i += 1
        if role != "SEALED_TEST": development_labels[role] = labels
    # exact/missed rows are only final-evaluation workflow components.
    for kind, label in (("AUTO_EXACT", 1), ("BLOCKING_MISS", 1)):
        key = f"p{i}"; rows.append({"pair_key": key, "entity": f"e{12 + (i % 4)}", "role": "SEALED_TEST", "pair_type": kind}); sealed_labels[key] = label; i += 1
    return {"NOT_MANUSCRIPT_EVIDENCE": True, "rows": pd.DataFrame(rows), "features17": pd.DataFrame(features, columns=FEATURE17_COLUMNS),
            "bert": pd.DataFrame({"bert_cos": np.linspace(.1, .9, len(features)).astype("float32")}), "roles": roles,
            "development_labels": development_labels, "sealed_labels": sealed_labels, "legacy_name_sim_reachable": False}
