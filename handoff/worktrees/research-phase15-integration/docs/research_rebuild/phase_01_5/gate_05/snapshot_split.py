"""Read-only hash-gated snapshot assignment and pair-role audit (Phase 1.5)."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

from split_safety import assign_folds, roles_for_fold

FOLD_COUNT = 5
DEFAULT_SEED = 20261010
ROLE_NAMES = ("TRAIN", "CALIBRATION", "POLICY_VALIDATION", "TEST")
REQUIRED_COLUMNS = {"profile_row_id", "user_folder", "platform"}


class SnapshotSplitError(ValueError):
    """Snapshot identity, mapping, or pair routing violates the split contract."""


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stable_json_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                ensure_ascii=False).encode("utf-8")).hexdigest()


def verify_snapshot_split(
    snapshot_path: str | Path,
    *,
    expected_sha256: str,
    expected_unmapped_rows: int,
    seed: int = DEFAULT_SEED,
    heldout_fold: int = 0,
) -> dict[str, Any]:
    """Hash-check CSV bytes before parsing; exclude only null entity mappings.

    Returns aggregate audit metadata plus in-memory profile/entity role maps.
    The JSON-safe ``summary`` omits raw entity and profile identifiers.
    """
    path = Path(snapshot_path)
    if len(expected_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_sha256):
        raise SnapshotSplitError("expected_sha256 must be lowercase SHA-256 hex")
    actual_sha = _file_sha256(path)
    if actual_sha != expected_sha256:
        raise SnapshotSplitError(f"snapshot SHA-256 mismatch: expected {expected_sha256}, got {actual_sha}")
    if heldout_fold not in range(FOLD_COUNT):
        raise SnapshotSplitError("heldout_fold must be in [0,4]")
    frame = pd.read_csv(path)
    missing_columns = REQUIRED_COLUMNS - set(frame.columns)
    if missing_columns:
        raise SnapshotSplitError(f"snapshot missing columns: {sorted(missing_columns)}")
    if frame.profile_row_id.isna().any() or frame.profile_row_id.duplicated().any():
        raise SnapshotSplitError("profile_row_id must be non-null and globally unique")
    if frame.platform.isna().any() or frame.platform.astype(str).str.strip().eq("").any():
        raise SnapshotSplitError("platform must be present for every row")
    unmapped = frame.user_folder.isna() | frame.user_folder.astype("string").str.strip().eq("")
    unmapped_count = int(unmapped.sum())
    if unmapped_count != expected_unmapped_rows:
        raise SnapshotSplitError(f"unmapped entity rows {unmapped_count} != expected {expected_unmapped_rows}")
    eligible = frame.loc[~unmapped, ["profile_row_id", "user_folder", "platform"]].copy()
    eligible["user_folder"] = eligible.user_folder.astype(str).str.strip()
    eligible["platform"] = eligible.platform.astype(str).str.strip()

    profile_to_entity: dict[int, str] = {}
    for row in eligible.itertuples(index=False):
        profile_id = int(row.profile_row_id)
        entity = row.user_folder
        if profile_id in profile_to_entity and profile_to_entity[profile_id] != entity:
            raise SnapshotSplitError("profile_row_id maps to conflicting entities")
        profile_to_entity[profile_id] = entity
    entity_platform_rows = list(zip(eligible.user_folder, eligible.platform))
    folds = assign_folds(entity_platform_rows, seed=seed)
    reverse_folds = assign_folds(reversed(entity_platform_rows), seed=seed)
    if folds != reverse_folds:
        raise SnapshotSplitError("entity fold assignment changes with input row order")
    if len(folds) != eligible.user_folder.nunique():
        raise SnapshotSplitError("entity fold assignment is not one-to-one")
    entity_roles = roles_for_fold(folds, heldout_fold)
    if set(entity_roles.values()) - set(ROLE_NAMES):
        raise SnapshotSplitError("invalid role emitted by split contract")
    profile_roles = {profile_id: entity_roles[entity]
                     for profile_id, entity in profile_to_entity.items()}
    # Explicitly verify entity atomicity and profile-to-role completeness.
    role_per_entity = eligible.assign(role=eligible.user_folder.map(entity_roles)).groupby("user_folder").role.nunique()
    if not role_per_entity.eq(1).all() or len(profile_roles) != len(eligible):
        raise SnapshotSplitError("entity-disjoint role assignment invariant failed")

    entity_role_counts = {role: int(sum(v == role for v in entity_roles.values())) for role in ROLE_NAMES}
    profile_role_counts = {role: int(sum(v == role for v in profile_roles.values())) for role in ROLE_NAMES}
    hashed_fold_pairs = sorted((hashlib.sha256(e.encode("utf-8")).hexdigest(), f)
                               for e, f in folds.items())
    excluded_ids = sorted(str(int(v)) for v in frame.loc[unmapped, "profile_row_id"])
    summary = {
        "snapshot_path": str(path), "snapshot_sha256": actual_sha,
        "rows": int(len(frame)), "columns": int(len(frame.columns)),
        "eligible_rows": int(len(eligible)), "excluded_unmapped_rows": unmapped_count,
        "excluded_profile_row_ids_sha256": _stable_json_hash(excluded_ids),
        "profile_row_id_unique": int(frame.profile_row_id.nunique()),
        "entity_count": int(len(entity_roles)), "fold_count": FOLD_COUNT,
        "split_seed": int(seed), "heldout_fold": int(heldout_fold),
        "entity_atomic": True, "deterministic": True,
        "entity_fold_assignment_sha256": _stable_json_hash(hashed_fold_pairs),
        "entity_role_assignment_sha256": _stable_json_hash(sorted(
            (hashlib.sha256(e.encode("utf-8")).hexdigest(), role)
            for e, role in entity_roles.items())),
        "profile_role_counts": profile_role_counts,
        "entity_role_counts": entity_role_counts,
        "platform_counts_eligible": {str(k): int(v) for k, v in
                                      eligible.platform.value_counts().sort_index().items()},
        "approved_snapshot": False,
        "approval_note": "Technical verification only; human snapshot/exclusion approval is not asserted.",
    }
    return {"summary": summary, "entity_folds": folds, "entity_roles": entity_roles,
            "profile_entities": profile_to_entity, "profile_roles": profile_roles}


def route_pair_iter(
    pairs: Iterable[tuple[Any, Any, str]],
    profile_entities: Mapping[int, str],
    entity_roles: Mapping[str, str],
    *,
    collect_routed: bool = False,
) -> dict[str, Any]:
    """Count unique pair routes; reject unknown IDs, keep same-role endpoints only."""
    seen: set[tuple[int, int]] = set()
    kept_by_type: dict[str, int] = {}
    dropped_by_type: dict[str, int] = {}
    routed_pairs: list[tuple[int, int, str, str]] = []
    total = 0
    for raw_a, raw_b, pair_type in pairs:
        try:
            a, b = int(raw_a), int(raw_b)
        except (TypeError, ValueError, OverflowError) as exc:
            raise SnapshotSplitError("pair endpoints must be integer profile_row_id values") from exc
        if a == b:
            raise SnapshotSplitError("self-pair is invalid")
        key = tuple(sorted((a, b)))
        if key in seen:
            raise SnapshotSplitError("duplicate canonical endpoint pair")
        seen.add(key)
        if a not in profile_entities or b not in profile_entities:
            raise SnapshotSplitError("pair endpoint missing from eligible snapshot")
        ea, eb = profile_entities[a], profile_entities[b]
        ra, rb = entity_roles.get(ea), entity_roles.get(eb)
        if ra not in ROLE_NAMES or rb not in ROLE_NAMES:
            raise SnapshotSplitError("pair endpoint entity lacks a valid role")
        kind = str(pair_type)
        total += 1
        if ra == rb:
            kept_by_type[kind] = kept_by_type.get(kind, 0) + 1
            if collect_routed:
                routed_pairs.append((a, b, kind, ra))
        else:
            dropped_by_type[kind] = dropped_by_type.get(kind, 0) + 1
    kept, dropped = sum(kept_by_type.values()), sum(dropped_by_type.values())
    if kept + dropped != total:
        raise SnapshotSplitError("pair routing accounting mismatch")
    result = {"input_pairs": total, "same_role_pairs": kept,
              "cross_role_dropped": dropped, "same_role_by_pair_type": kept_by_type,
              "cross_role_dropped_by_pair_type": dropped_by_type}
    if collect_routed:
        result["routed_pairs"] = routed_pairs
    return result
