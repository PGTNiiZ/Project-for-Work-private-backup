"""Standalone deterministic run-manifest and chunk-cache validation contract."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

COMPATIBILITY_FIELDS = (
    "dataset_identity",
    "schema_identity",
    "pair_population_identity",
    "chunk_size",
    "model_identity",
    "source_identity",
    "split_identity",
)


class ManifestError(ValueError):
    """Invalid manifest, artifact collision, or incompatible cache."""


def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ManifestError(f"not canonical-JSON serializable: {exc}") from exc


def compatibility_key(values: Mapping[str, Any]) -> dict[str, Any]:
    missing = [field for field in COMPATIBILITY_FIELDS if field not in values]
    if missing:
        raise ManifestError(f"missing compatibility fields: {', '.join(missing)}")
    key = {field: values[field] for field in COMPATIBILITY_FIELDS}
    for field in COMPATIBILITY_FIELDS:
        value = key[field]
        if field == "chunk_size":
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ManifestError("chunk_size must be a positive integer")
        elif not isinstance(value, str) or not value.strip():
            raise ManifestError(f"{field} must be a nonempty string")
    return key


def build_manifest(values: Mapping[str, Any], pair_count: int) -> dict[str, Any]:
    if isinstance(pair_count, bool) or not isinstance(pair_count, int) or pair_count < 0:
        raise ManifestError("pair_count must be a nonnegative integer")
    key = compatibility_key(values)
    core = {"manifest_schema": 1, "compatibility": key, "pair_count": pair_count}
    run_id = hashlib.sha256(canonical_json(core)).hexdigest()
    return {**core, "run_id": run_id}


def write_manifest_create_only(path: str | Path, manifest: Mapping[str, Any]) -> None:
    """Publish complete canonical bytes without replacing any existing path."""
    target = Path(path)
    payload = canonical_json(manifest) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(target, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        # Never remove a path that might have been replaced by another actor.
        raise


def assert_cache_compatible(expected: Mapping[str, Any], cached: Mapping[str, Any]) -> None:
    expected_key = compatibility_key(expected)
    cached_key = compatibility_key(cached)
    mismatches = [name for name in COMPATIBILITY_FIELDS if expected_key[name] != cached_key[name]]
    if mismatches:
        raise ManifestError(f"cache incompatible fields: {', '.join(mismatches)}")


def validate_chunks(pair_count: int, chunk_size: int,
                    chunks: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Check complete ordered coverage and global pair-key uniqueness.

    Each chunk contains `index`, `start`, `stop`, `pair_keys`; boundaries are
    exact expected half-open ranges and pair_keys contains one key per row.
    """
    if isinstance(pair_count, bool) or not isinstance(pair_count, int) or pair_count < 0:
        raise ManifestError("pair_count must be a nonnegative integer")
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ManifestError("chunk_size must be a positive integer")
    rows = list(chunks)
    expected_n = (pair_count + chunk_size - 1) // chunk_size
    by_index: dict[int, Mapping[str, Any]] = {}
    for chunk in rows:
        idx = chunk.get("index")
        if isinstance(idx, bool) or not isinstance(idx, int) or idx < 0:
            raise ManifestError("chunk index must be a nonnegative integer")
        if idx in by_index:
            raise ManifestError(f"duplicate chunk index: {idx}")
        by_index[idx] = chunk
    if len(by_index) != expected_n or set(by_index) != set(range(expected_n)):
        raise ManifestError("chunk count/index coverage mismatch (partial or extra run)")
    seen: set[Any] = set()
    ordered = []
    for idx in range(expected_n):
        chunk = by_index[idx]
        start, stop = idx * chunk_size, min((idx + 1) * chunk_size, pair_count)
        if chunk.get("start") != start or chunk.get("stop") != stop:
            raise ManifestError(f"chunk {idx} has a gap, overlap, or invalid boundary")
        keys = chunk.get("pair_keys")
        if not isinstance(keys, (list, tuple)) or len(keys) != stop - start:
            raise ManifestError(f"chunk {idx} row count mismatch")
        for key in keys:
            try:
                if key in seen:
                    raise ManifestError(f"duplicate pair key: {key!r}")
                seen.add(key)
            except TypeError as exc:
                raise ManifestError("pair keys must be hashable") from exc
        ordered.append(chunk)
    return ordered
