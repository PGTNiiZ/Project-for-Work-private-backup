"""Versioned pair-record adapter for evaluator inputs.

Pair keys use the V2 canonical identifier ``sha256('v2-pair:<lo>:<hi>')``.
Opaque hashes are never inverted: endpoints must be present in the record or
provided in an explicit key-to-endpoints mapping, then the key is recomputed.
"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable, Mapping
from numbers import Integral
from typing import Any

ADAPTER_VERSION = "pair-evaluator-adapter.v1"
PAIR_KEY_SCHEME = "v2-sha256-profile-row-id-pair"
VALID_SPLIT_ROLES = {"TRAIN", "CALIBRATION", "POLICY_VALIDATION", "TEST", "SEALED_TEST"}
SCOPE_MAP = {
    "exact": "exact", "auto_exact": "exact", "exact_tier": "exact",
    "scored": "scored", "model_scored": "scored",
    "blocking_miss": "blocking_miss", "blocking_missed": "blocking_miss",
}
ACTIONS = {"MATCH", "REVIEW", "NO_MATCH"}


class AdapterError(ValueError):
    """Invalid, ambiguous, or role-inconsistent pair record."""


def _profile_row_id(value: Any) -> int:
    if isinstance(value, bool):
        raise AdapterError("endpoint ID must be an integer profile_row_id")
    if isinstance(value, Integral):
        number = int(value)
    elif isinstance(value, str) and value.isdigit() and str(int(value)) == value:
        number = int(value)
    else:
        raise AdapterError("endpoint ID must be a canonical integer profile_row_id")
    if number < 0:
        raise AdapterError("endpoint ID must be nonnegative")
    return number


def _extract_endpoints(record: Mapping[str, Any]) -> tuple[int, int] | None:
    pairs = (("endpoint_a", "endpoint_b"), ("profile_row_id_a", "profile_row_id_b"), ("a", "b"))
    found = []
    for left, right in pairs:
        has_left, has_right = left in record, right in record
        if has_left != has_right:
            raise AdapterError(f"both {left} and {right} are required together")
        if has_left:
            found.append((_profile_row_id(record[left]), _profile_row_id(record[right])))
    if not found:
        return None
    canonical = {tuple(sorted(pair)) for pair in found}
    if len(canonical) != 1:
        raise AdapterError("record contains conflicting endpoint representations")
    return found[0]


def canonical_pair_key(endpoint_a: Any, endpoint_b: Any) -> str:
    """Return the existing V2 key for an unordered pair of profile-row IDs."""
    a, b = _profile_row_id(endpoint_a), _profile_row_id(endpoint_b)
    if a == b:
        raise AdapterError("self-pairs are invalid")
    low, high = sorted((a, b))
    return hashlib.sha256(f"v2-pair:{low}:{high}".encode("utf-8")).hexdigest()


def _mapping_rows(endpoint_mapping: Any) -> list[tuple[str, int, int]]:
    if endpoint_mapping is None:
        return []
    if isinstance(endpoint_mapping, Mapping):
        rows = []
        for key, endpoints in endpoint_mapping.items():
            if not isinstance(endpoints, (tuple, list)) or len(endpoints) != 2:
                raise AdapterError("endpoint mapping values must be endpoint pairs")
            rows.append((str(key), _profile_row_id(endpoints[0]), _profile_row_id(endpoints[1])))
        return rows
    try:
        iterator = iter(endpoint_mapping)
    except TypeError as exc:
        raise AdapterError("endpoint_mapping must be an iterable of keyed endpoint rows") from exc
    rows = []
    for row in iterator:
        if not isinstance(row, Mapping) or "pair_key" not in row:
            raise AdapterError("mapping rows require pair_key and explicit endpoint IDs")
        endpoints = _extract_endpoints(row)
        if endpoints is None:
            raise AdapterError("mapping rows require explicit endpoint IDs")
        rows.append((str(row["pair_key"]), endpoints[0], endpoints[1]))
    return rows


def adapt_decision_records(
    records: Iterable[Mapping[str, Any]],
    *,
    profile_entities: Mapping[int, str],
    entity_roles: Mapping[str, str],
    endpoint_mapping: Any = None,
) -> dict[str, Any]:
    """Validate keyed future decision records and return evaluator tier lists.

    Each record must carry a recognized canonical pair_key and either both
    endpoint_a/endpoint_b or neither. If endpoints are omitted, an explicit
    unique endpoint_mapping entry is mandatory. Endpoint IDs are then checked
    against the key algorithm, profile→entity map, and entity→split-role map.
    Labels are passed through, never synthesized. A blocking miss must already
    have label=1 and cannot carry a decision action.
    """
    mapping: dict[str, tuple[int, int]] = {}
    for key, a, b in _mapping_rows(endpoint_mapping):
        if key in mapping:
            raise AdapterError(f"duplicate or ambiguous endpoint mapping for {key}")
        if canonical_pair_key(a, b) != key:
            raise AdapterError("endpoint mapping does not reproduce canonical pair key")
        mapping[key] = (a, b)

    exact: list[dict[str, Any]] = []
    scored: list[dict[str, Any]] = []
    misses: list[dict[str, Any]] = []
    keys_seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise AdapterError(f"record {index} must be a mapping")
        key = record.get("pair_key")
        if not isinstance(key, str) or len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
            raise AdapterError(f"record {index} has invalid canonical pair_key")
        if key in keys_seen:
            raise AdapterError(f"duplicate pair_key across scopes: {key}")
        keys_seen.add(key)
        direct = _extract_endpoints(record)
        if direct is not None:
            a, b = direct
            if key in mapping and set((a, b)) != set(mapping[key]):
                raise AdapterError("direct endpoints disagree with explicit endpoint mapping")
        else:
            if key not in mapping:
                raise AdapterError("missing endpoints and no explicit endpoint mapping")
            a, b = mapping[key]
        if canonical_pair_key(a, b) != key:
            raise AdapterError("pair_key does not match supplied endpoints")
        a, b = sorted((a, b))
        if a not in profile_entities or b not in profile_entities:
            raise AdapterError("endpoint is absent from profile-to-entity mapping")
        entity_a, entity_b = profile_entities[a], profile_entities[b]
        if not isinstance(entity_a, str) or not entity_a.strip() or not isinstance(entity_b, str) or not entity_b.strip():
            raise AdapterError("endpoint has missing/invalid entity mapping")
        role_a, role_b = entity_roles.get(entity_a), entity_roles.get(entity_b)
        if role_a not in VALID_SPLIT_ROLES or role_b not in VALID_SPLIT_ROLES:
            raise AdapterError("endpoint entity has missing/invalid role mapping")
        if role_a != role_b:
            raise AdapterError("pair endpoints belong to different split roles")
        declared_role = record.get("split_role")
        if declared_role is not None and declared_role != role_a:
            raise AdapterError("declared split role disagrees with endpoint entities")
        label = record.get("label")
        if isinstance(label, bool) or label not in (0, 1):
            raise AdapterError("label must be an observed integer 0 or 1")
        scope = record.get("scope")
        if not isinstance(scope, str) or scope.casefold() not in SCOPE_MAP:
            raise AdapterError(f"record {index} has invalid scope")
        tier = SCOPE_MAP[scope.casefold()]
        base = {"a": str(a), "b": str(b), "label": int(label), "pair_key": key,
                "split_role": role_a}
        if tier == "blocking_miss":
            if label != 1:
                raise AdapterError("blocking misses must have observed positive label=1")
            if "action" in record:
                raise AdapterError("blocking misses cannot carry a model decision")
            misses.append(base)
            continue
        action = record.get("action")
        if action not in ACTIONS:
            raise AdapterError("decision action must be MATCH, REVIEW, or NO_MATCH")
        output = {**base, "role": tier, "action": action}
        if tier == "scored":
            score = record.get("score")
            if isinstance(score, bool):
                raise AdapterError("scored rows require a finite score in [0,1]")
            try:
                score = float(score)
            except (TypeError, ValueError) as exc:
                raise AdapterError("scored rows require a finite score in [0,1]") from exc
            if not math.isfinite(score) or not 0.0 <= score <= 1.0:
                raise AdapterError("scored rows require a finite score in [0,1]")
            output["score"] = score
        exact_or_scored = exact if tier == "exact" else scored
        exact_or_scored.append(output)

    return {"adapter_version": ADAPTER_VERSION, "pair_key_scheme": PAIR_KEY_SCHEME,
            "exact": exact, "scored": scored, "blocking_misses": misses,
            "pair_keys": [r["pair_key"] for r in exact + scored + misses]}
