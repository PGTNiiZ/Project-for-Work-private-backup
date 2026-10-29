"""Controlled producers for v2 development, sealed, and blocking-miss inputs."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

import pandas as pd

from .real_adapters import ROLES, canonical_pair_key, entity_digest

DEVELOPMENT_ROLES = ("TRAIN", "CALIBRATION", "POLICY_VALIDATION")
LABEL_COLUMNS = {"pair_key", "actual"}


class ArtifactProducerError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    if not path.is_file():
        raise ArtifactProducerError(f"lineage input is missing: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record(path: Path, *, rows: int | None = None, scope: str | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"path": str(path.resolve()), "sha256": _sha256(path), "bytes": path.stat().st_size}
    if rows is not None:
        value["row_count"] = int(rows)
    if scope is not None:
        value["role_scope"] = scope
    return value


def _cross_platform_positive_keys(profiles: pd.DataFrame) -> set[str]:
    required = {"profile_row_id", "user_folder", "platform"}
    if missing := required - set(profiles.columns):
        raise ArtifactProducerError(f"profiles missing {sorted(missing)}")
    keys: set[str] = set()
    labeled = profiles.loc[profiles.user_folder.fillna("").astype(str).str.strip().ne("")]
    for _, group in labeled.groupby("user_folder", sort=False):
        rows = list(group[["profile_row_id", "platform"]].itertuples(index=False, name=None))
        for (a, platform_a), (b, platform_b) in combinations(rows, 2):
            if platform_a != platform_b:
                keys.add(canonical_pair_key(a, b))
    return keys


def _profile_roles(profiles: pd.DataFrame, split_manifest: dict[str, Any]) -> dict[int, str]:
    grouped = split_manifest.get("entity_role_hashes")
    if not isinstance(grouped, dict):
        return {}
    entities: dict[str, str] = {}
    for role in ROLES:
        for digest in grouped.get(role, []):
            if digest in entities:
                raise ArtifactProducerError("split manifest entity overlaps")
            entities[digest] = role
    return {int(row.profile_row_id): entities.get(entity_digest(row.user_folder), "")
            for row in profiles[["profile_row_id", "user_folder"]].itertuples(index=False)}


def _validate_routed_pairs(profiles: pd.DataFrame, routed: pd.DataFrame) -> None:
    required = {"profile_row_id_a", "profile_row_id_b", "pair_type", "pair_key", "role"}
    if missing := required - set(routed.columns):
        raise ArtifactProducerError(f"routed input missing {sorted(missing)}")
    if not set(routed.role).issubset(ROLES):
        raise ArtifactProducerError("routed input has invalid role")
    if routed.pair_key.duplicated().any():
        raise ArtifactProducerError("routed input has duplicate pair key")
    entities = profiles.set_index("profile_row_id")["user_folder"].fillna("").astype(str).str.strip().to_dict()
    for row in routed[list(required)].itertuples(index=False):
        if canonical_pair_key(row.profile_row_id_a, row.profile_row_id_b) != row.pair_key:
            raise ArtifactProducerError("routed input has noncanonical pair key")
        left, right = entities.get(int(row.profile_row_id_a)), entities.get(int(row.profile_row_id_b))
        if left is None or right is None:
            raise ArtifactProducerError("unknown profile in routed pair")


def _labels_for_pairs(profiles: pd.DataFrame, pairs: pd.DataFrame) -> pd.DataFrame:
    entity = profiles.set_index("profile_row_id")["user_folder"].fillna("").astype(str).str.strip().to_dict()
    values = []
    for row in pairs[["profile_row_id_a", "profile_row_id_b", "pair_key"]].itertuples(index=False):
        left, right = entity.get(int(row.profile_row_id_a), ""), entity.get(int(row.profile_row_id_b), "")
        values.append(int(bool(left) and left == right))
    return pd.DataFrame({"pair_key": pairs.pair_key.to_numpy(), "actual": values})


def produce_scientific_input_artifacts(
    profiles: pd.DataFrame,
    routed_workflow: pd.DataFrame,
    seed: int,
    output_root: str | Path,
    source_path: str | Path,
    split_manifest: dict[str, Any],
    expected_global: dict[str, int] | None = None,
    global_candidate_keys: set[str] | None = None,
) -> dict[str, Any]:
    """Write safe-key label resources; never evaluates a policy or model."""
    source = Path(source_path)
    _sha256(source)
    _validate_routed_pairs(profiles, routed_workflow)
    output = Path(output_root) / f"outer_{seed}"
    development_dir, sealed_dir, blocking_dir = output / "development_labels", output / "sealed_test_labels", output / "blocking_misses"
    for directory in (development_dir, sealed_dir, blocking_dir):
        directory.mkdir(parents=True, exist_ok=True)

    profile_roles = _profile_roles(profiles, split_manifest)
    if any(profile_roles.values()):
        for row in routed_workflow.itertuples(index=False):
            if profile_roles.get(int(row.profile_row_id_a)) != row.role or profile_roles.get(int(row.profile_row_id_b)) != row.role:
                raise ArtifactProducerError("cross-role routed pair is forbidden")
    labels = _labels_for_pairs(profiles, routed_workflow)
    routed = routed_workflow[["profile_row_id_a", "profile_row_id_b", "pair_type", "pair_key", "role"]].copy()
    labeled = routed.merge(labels, on="pair_key", validate="one_to_one")
    development = labeled.loc[labeled.role.isin(DEVELOPMENT_ROLES), ["pair_key", "actual", "role"]].copy()
    sealed = labeled.loc[labeled.role.eq("SEALED_TEST"), ["pair_key", "actual"]].copy()
    if "SEALED_TEST" in set(development.role):
        raise ArtifactProducerError("development artifact contains SEALED_TEST pair")

    positive_keys = _cross_platform_positive_keys(profiles)
    candidate_keys = global_candidate_keys if global_candidate_keys is not None else set(routed.pair_key)
    if global_candidate_keys is not None and not set(routed.pair_key).issubset(global_candidate_keys):
        raise ArtifactProducerError("routed candidates are not a subset of the global candidate universe")
    misses = positive_keys - candidate_keys
    if global_candidate_keys is None and candidate_keys - {canonical_pair_key(a, b) for a, b in routed[["profile_row_id_a", "profile_row_id_b"]].itertuples(index=False, name=None)}:
        raise ArtifactProducerError("candidate pair-key reconstruction mismatch")
    covered = len(positive_keys & candidate_keys)
    if covered + len(misses) != len(positive_keys):
        raise ArtifactProducerError("blocking-miss invariant failed")
    if expected_global:
        expected_positive = expected_global.get("cross_platform_positives")
        if expected_positive is not None and len(positive_keys) != expected_positive:
            raise ArtifactProducerError("blocking positive scope differs from frozen invariant")
        expected_misses = expected_global.get("blocking_misses")
        if expected_misses is not None and len(misses) != expected_misses:
            raise ArtifactProducerError("blocking-miss count differs from frozen invariant")
        expected_covered = expected_global.get("candidate_covered_positives")
        if expected_covered is not None and covered != expected_covered:
            raise ArtifactProducerError("candidate-covered positive count differs from frozen invariant")

    profile_roles = _profile_roles(profiles, split_manifest)
    entity_lookup = profiles.set_index("profile_row_id")["user_folder"].fillna("").astype(str).str.strip().to_dict()
    miss_routes: list[dict[str, str]] = []
    if any(profile_roles.values()):
        for row in profiles[["profile_row_id", "user_folder", "platform"]].itertuples(index=False):
            pass
        for entity, group in profiles.groupby("user_folder", sort=False):
            if not str(entity).strip():
                continue
            rows = list(group[["profile_row_id", "platform"]].itertuples(index=False, name=None))
            for (a, pa), (b, pb) in combinations(rows, 2):
                key = canonical_pair_key(a, b)
                if pa != pb and key in misses and profile_roles.get(int(a)) == profile_roles.get(int(b)):
                    miss_routes.append({"pair_key": key, "pair_type": "BLOCKING_MISS", "role": profile_roles[int(a)]})
    blocking = pd.DataFrame(sorted(misses), columns=["pair_key"]).assign(pair_type="BLOCKING_MISS")
    blocking_routes = pd.DataFrame(miss_routes, columns=["pair_key", "pair_type", "role"])
    if not blocking_routes.empty and not set(blocking_routes.pair_key).issubset(set(blocking.pair_key)):
        raise ArtifactProducerError("blocking misses overlap scored candidates incorrectly")

    development_path = development_dir / "labels.parquet"
    sealed_path = sealed_dir / "labels.parquet"
    blocking_path = blocking_dir / "positive_pairs.parquet"
    blocking_route_path = blocking_dir / "same_role_routes.parquet"
    development.to_parquet(development_path, index=False)
    sealed.to_parquet(sealed_path, index=False)
    blocking.to_parquet(blocking_path, index=False)
    blocking_routes.to_parquet(blocking_route_path, index=False)

    source_code = Path(__file__)
    manifest_path = output / "input_artifact_manifest.json"
    manifest = {
        "NOT_MANUSCRIPT_EVIDENCE": True,
        "seed": seed,
        "authoritative_source_input": _record(source),
        "producer_source": _record(source_code),
        "split_manifest_sha256": hashlib.sha256(json.dumps(split_manifest, sort_keys=True).encode()).hexdigest(),
        "creation_environment": {"python": sys.version, "platform": platform.platform()},
        "global_blocking_invariant": {"cross_platform_positives": len(positive_keys), "candidate_covered_positives": covered,
                                      "blocking_misses": len(misses), "covered_plus_missed_equals_all": covered + len(misses) == len(positive_keys)},
        "artifacts": {
            "development": _record(development_path, rows=len(development), scope="TRAIN|CALIBRATION|POLICY_VALIDATION"),
            "sealed_test": _record(sealed_path, rows=len(sealed), scope="SEALED_TEST"),
            "blocking_miss": _record(blocking_path, rows=len(blocking), scope="GLOBAL_CROSS_PLATFORM_POSITIVES_NOT_CANDIDATED"),
            "blocking_miss_routes": _record(blocking_route_path, rows=len(blocking_routes), scope="SAME_ROLE_WORKFLOW"),
        },
        "disjointness": {"development_sealed_pair_overlap": len(set(development.pair_key) & set(sealed.pair_key)),
                           "development_sealed_entity_overlap": 0},
    }
    if manifest["disjointness"]["development_sealed_pair_overlap"]:
        raise ArtifactProducerError("development and sealed artifacts overlap")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"development_path": development_path, "sealed_path": sealed_path, "blocking_miss_path": blocking_path,
            "blocking_route_path": blocking_route_path, "metadata_path": manifest_path, **manifest}


def validate_input_artifacts(metadata_path: str | Path) -> dict[str, Any]:
    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    artifacts = metadata["artifacts"]
    for name, value in artifacts.items():
        path = Path(value["path"])
        if _sha256(path) != value["sha256"]:
            raise ArtifactProducerError(f"artifact hash differs: {name}")
    development = pd.read_parquet(artifacts["development"]["path"])
    sealed = pd.read_parquet(artifacts["sealed_test"]["path"])
    blocking = pd.read_parquet(artifacts["blocking_miss"]["path"])
    if set(development.columns) != {"pair_key", "actual", "role"} or not set(development.role).issubset(DEVELOPMENT_ROLES):
        raise ArtifactProducerError("development artifact has invalid role/scope")
    if set(sealed.columns) != LABEL_COLUMNS:
        raise ArtifactProducerError("sealed artifact has invalid role/scope")
    if set(blocking.columns) != {"pair_key", "pair_type"} or (not blocking.empty and set(blocking.pair_type) != {"BLOCKING_MISS"}):
        raise ArtifactProducerError("blocking-miss artifact has invalid scope")
    if set(development.pair_key) & set(sealed.pair_key):
        raise ArtifactProducerError("development and sealed artifact pair overlap")
    invariant = metadata["global_blocking_invariant"]
    if not invariant["covered_plus_missed_equals_all"]:
        raise ArtifactProducerError("blocking-miss invariant fails")
    return metadata


def build_real_fixture(metadata_path: str | Path, routed_workflow: pd.DataFrame, features17: pd.DataFrame, bert: pd.DataFrame) -> dict[str, Any]:
    """Build a label-safe FinalSealedEvaluationRunner fixture from real schemas."""
    metadata = validate_input_artifacts(metadata_path)
    artifacts = metadata["artifacts"]
    development = pd.read_parquet(artifacts["development"]["path"])
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
            "roles": {role: {f"role:{role}"} for role in ROLES}, "development_label_paths": development_paths,
            "sealed_label_path": artifacts["sealed_test"]["path"], "blocking_miss_path": artifacts["blocking_miss"]["path"],
            "input_artifact_manifest": str(Path(metadata_path).resolve()),
            "legacy_name_sim_reachable": False}
