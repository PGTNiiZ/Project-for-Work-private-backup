"""Real-artifact entity routing and lazy sealed-label boundary for v2."""
from __future__ import annotations

import hashlib
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pandas as pd

ROLES = ("TRAIN", "CALIBRATION", "POLICY_VALIDATION", "SEALED_TEST")
PAIR_COLUMNS = ("profile_row_id_a", "profile_row_id_b", "pair_type")
FORBIDDEN_LABEL_COLUMNS = {"actual", "label", "ground_truth"}


class AdapterError(RuntimeError):
    pass


def entity_digest(entity: object) -> str:
    value = str(entity).strip()
    if not value:
        raise AdapterError("missing entity")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_pair_key(left: object, right: object) -> str:
    try:
        a, b = int(left), int(right)
    except (TypeError, ValueError) as error:
        raise AdapterError("invalid profile-row identifier") from error
    if a == b:
        raise AdapterError("pair cannot contain the same profile twice")
    lo, hi = sorted((a, b))
    return hashlib.sha256(f"v2-pair:{lo}:{hi}".encode("utf-8")).hexdigest()


def build_entity_role_map(profiles: pd.DataFrame, manifest: dict, *, entity_hash: Callable[[object], str] = entity_digest) -> dict[int, str]:
    required = {"profile_row_id", "user_folder"}
    if not required.issubset(profiles.columns):
        raise AdapterError(f"profiles missing {sorted(required - set(profiles.columns))}")
    if tuple(manifest.get("roles", ())) != ROLES:
        raise AdapterError("manifest has invalid roles")
    grouped = manifest.get("entity_role_hashes")
    if not isinstance(grouped, dict):
        raise AdapterError("manifest lacks entity_role_hashes")
    entity_roles: dict[str, str] = {}
    for role in ROLES:
        keys = grouped.get(role)
        if not isinstance(keys, list):
            raise AdapterError(f"manifest missing role {role}")
        for key in keys:
            if key in entity_roles:
                raise AdapterError(f"conflicting role assignment for entity hash {key}")
            entity_roles[key] = role
    if profiles.profile_row_id.duplicated().any():
        raise AdapterError("duplicate profile-row identifier")
    result: dict[int, str] = {}
    for row in profiles[["profile_row_id", "user_folder"]].itertuples(index=False):
        entity = str(row.user_folder).strip()
        if not entity:
            raise AdapterError("missing entity in profile routing input")
        role = entity_roles.get(entity_hash(entity))
        if role is None:
            raise AdapterError("unknown entity in frozen role manifest")
        result[int(row.profile_row_id)] = role
    return result


def route_pairs(pairs: pd.DataFrame, profiles: pd.DataFrame, entity_roles: dict[int, str]) -> tuple[pd.DataFrame, dict[str, int]]:
    if not set(PAIR_COLUMNS).issubset(pairs.columns):
        raise AdapterError(f"pairs missing {sorted(set(PAIR_COLUMNS) - set(pairs.columns))}")
    if FORBIDDEN_LABEL_COLUMNS.intersection(pairs.columns):
        raise AdapterError("label-dependent role routing is forbidden")
    routed: list[dict[str, object]] = []
    drops = 0
    for row in pairs[list(PAIR_COLUMNS)].itertuples(index=False):
        a, b = int(row.profile_row_id_a), int(row.profile_row_id_b)
        if a not in entity_roles or b not in entity_roles:
            raise AdapterError("unknown profile entity in candidate pair")
        left, right = entity_roles[a], entity_roles[b]
        if left != right:
            drops += 1
            continue
        routed.append({"profile_row_id_a": a, "profile_row_id_b": b, "pair_type": row.pair_type,
                       "pair_key": canonical_pair_key(a, b), "role": left})
    result = pd.DataFrame(routed, columns=[*PAIR_COLUMNS, "pair_key", "role"])
    if result.pair_key.duplicated().any():
        raise AdapterError("duplicate canonical pair key")
    if not set(result.role).issubset(ROLES):
        raise AdapterError("invalid routed role")
    report = {role: int((result.role == role).sum()) for role in ROLES}
    report["cross_role_dropped"] = drops
    report["input_pairs"] = int(len(pairs))
    report["same_role_pairs"] = int(len(result))
    if report["input_pairs"] != report["same_role_pairs"] + drops:
        raise AdapterError("pair routing accounting mismatch")
    return result, report


@dataclass
class LazySealedLabelStore:
    """The only loader that may open a real sealed-test label artifact."""

    path: str | Path
    audit: list[dict[str, object]] = field(default_factory=list)
    file_reads: int = 0

    def read(self, pair_keys: list[str], *, phase: str) -> pd.DataFrame:
        allowed = phase == "FINAL_EVALUATION"
        self.audit.append({"phase": phase, "resource": "sealed_test_labels", "allowed": allowed,
                           "source": f"{inspect.getmodule(self).__name__}.LazySealedLabelStore.read"})
        if not allowed:
            raise AdapterError("sealed labels may be opened only during FINAL_EVALUATION")
        path = Path(self.path)
        if not path.is_file():
            raise AdapterError("sealed label artifact is missing")
        labels = pd.read_parquet(path)
        self.file_reads += 1
        if set(labels.columns) != {"pair_key", "actual"}:
            raise AdapterError("sealed label artifact has invalid schema")
        if labels.pair_key.duplicated().any():
            raise AdapterError("duplicate sealed-label pair key")
        requested = pd.DataFrame({"pair_key": pair_keys})
        if requested.pair_key.duplicated().any():
            raise AdapterError("duplicate prediction pair key")
        joined = requested.merge(labels, on="pair_key", how="left", validate="one_to_one", sort=False)
        if joined.actual.isna().any() or len(joined) != len(requested):
            raise AdapterError("missing expected sealed-test label")
        return joined

    @property
    def pre_final_reads(self) -> int:
        return self.file_reads - sum(bool(row["allowed"]) for row in self.audit)


def assert_label_free_artifacts(paths: list[str | Path]) -> None:
    """Reject alternate label-bearing candidate, feature, or prediction caches."""
    for raw in paths:
        path = Path(raw)
        if not path.is_file():
            raise AdapterError(f"required public artifact is missing: {path}")
        columns = set(pd.read_parquet(path).columns)
        hidden = FORBIDDEN_LABEL_COLUMNS.intersection(columns)
        if hidden:
            raise AdapterError(f"hidden test-label cache path: {path.name} contains {sorted(hidden)}")


def safe_final_join(predictions: pd.DataFrame, labels: LazySealedLabelStore, *, phase: str) -> pd.DataFrame:
    if FORBIDDEN_LABEL_COLUMNS.intersection(predictions.columns):
        raise AdapterError("sealed prediction input contains a label column")
    if "pair_key" not in predictions.columns or predictions.pair_key.duplicated().any():
        raise AdapterError("duplicate or missing prediction pair key")
    if not predictions.pair_key.astype(str).str.fullmatch(r"[0-9a-f]{64}").all():
        raise AdapterError("invalid safe pair key")
    label_rows = labels.read(predictions.pair_key.astype(str).tolist(), phase=phase)
    result = predictions.merge(label_rows, on="pair_key", how="left", validate="one_to_one", sort=False)
    if len(result) != len(predictions) or result.actual.isna().any():
        raise AdapterError("incomplete final label join")
    return result
