"""Standalone deterministic run-manifest and chunk-cache validation contract."""
from __future__ import annotations

import hashlib
import json
import os
import re
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
    "configuration_identity",
    "environment_identity",
    "seed",
)


class ManifestError(ValueError):
    """Invalid manifest, artifact collision, or incompatible cache."""


def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ManifestError(f"not canonical-JSON serializable: {exc}") from exc


def _schema_errors(value: Any, schema: Mapping[str, Any], location: str = "$",) -> list[str]:
    """Validate the JSON Schema keywords used by RUN_MANIFEST_SCHEMA.json."""
    errors: list[str] = []
    if "const" in schema and value != schema["const"]:
        return [f"{location} must equal {schema['const']!r}"]
    if "enum" in schema and value not in schema["enum"]:
        return [f"{location} must be one of {schema['enum']!r}"]
    expected_type = schema.get("type")
    type_ok = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
    }.get(expected_type, True)
    if not type_ok:
        return [f"{location} must be {expected_type}"]
    if expected_type == "string":
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{location} is shorter than minLength")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            errors.append(f"{location} does not match pattern")
    if expected_type == "integer" or expected_type == "number":
        if value < schema.get("minimum", float("-inf")):
            errors.append(f"{location} is below minimum")
    if expected_type == "object":
        for name in schema.get("required", []):
            if name not in value:
                errors.append(f"{location}.{name} is required")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = set(value) - set(props)
            if extras:
                errors.append(f"{location} has additional properties: {sorted(extras)}")
        for name, child in props.items():
            if name in value:
                errors.extend(_schema_errors(value[name], child, f"{location}.{name}"))
    if expected_type == "array" and "items" in schema:
        for index, item in enumerate(value):
            errors.extend(_schema_errors(item, schema["items"], f"{location}[{index}]"))
    return errors


def verify_artifact_bytes(chunks: Iterable[Mapping[str, Any]], artifact_root: str | Path) -> None:
    """Verify declared chunk digests against real bytes below an isolated root."""
    root = Path(artifact_root).resolve()
    for chunk in chunks:
        relative = chunk.get("path")
        expected = chunk.get("sha256")
        if not isinstance(relative, str) or not relative:
            raise ManifestError("artifact path must be a nonempty relative path")
        candidate = Path(relative)
        if candidate.is_absolute():
            raise ManifestError("artifact path must be inside artifact_root")
        resolved = (root / candidate).resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ManifestError("artifact path must be inside artifact_root") from exc
        if not resolved.is_file():
            raise ManifestError(f"artifact file is missing or not regular: {relative}")
        if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
            raise ManifestError(f"artifact SHA-256 is malformed: {relative}")
        digest = hashlib.sha256()
        with resolved.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != expected:
            raise ManifestError(f"artifact SHA-256 does not match bytes: {relative}")


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate one v1 manifest against the adjacent JSON Schema and run ID."""
    if not isinstance(manifest, Mapping):
        raise ManifestError("manifest must be a JSON object")
    version = manifest.get("manifest_schema")
    if isinstance(version, bool) or version != 1:
        raise ManifestError(f"unsupported manifest schema version: {version!r}")
    schema = json.loads(Path(__file__).with_name("RUN_MANIFEST_SCHEMA.json").read_text(encoding="utf-8"))
    errors = _schema_errors(dict(manifest), schema)
    if errors:
        raise ManifestError("manifest schema invalid: " + "; ".join(errors))
    core = {"manifest_schema": 1, "compatibility": dict(manifest["compatibility"]),
            "pair_count": manifest["pair_count"]}
    if manifest["run_id"] != hashlib.sha256(canonical_json(core)).hexdigest():
        raise ManifestError("run_id does not match manifest compatibility and pair_count")
    expected_chunks = (manifest["pair_count"] + manifest["compatibility"]["chunk_size"] - 1) // manifest["compatibility"]["chunk_size"]
    if manifest["state"] == "COMPLETE" and len(manifest["artifacts"]) != expected_chunks:
        raise ManifestError("complete manifest artifact count does not cover all chunks")
    if manifest["state"] != "COMPLETE" and len(manifest["artifacts"]) > expected_chunks:
        raise ManifestError("incomplete manifest has more artifacts than declared chunks")


def compatibility_key(values: Mapping[str, Any]) -> dict[str, Any]:
    missing = [field for field in COMPATIBILITY_FIELDS if field not in values]
    if missing:
        raise ManifestError(f"missing compatibility fields: {', '.join(missing)}")
    key = {field: values[field] for field in COMPATIBILITY_FIELDS}
    for field in COMPATIBILITY_FIELDS:
        value = key[field]
        if field in {"chunk_size", "seed"}:
            minimum = 1 if field == "chunk_size" else 0
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise ManifestError(f"{field} must be an integer >= {minimum}")
        elif not isinstance(value, str) or not value.strip():
            raise ManifestError(f"{field} must be a nonempty string")
    return key


def build_manifest(values: Mapping[str, Any], pair_count: int) -> dict[str, Any]:
    if isinstance(pair_count, bool) or not isinstance(pair_count, int) or pair_count < 0:
        raise ManifestError("pair_count must be a nonnegative integer")
    key = compatibility_key(values)
    core = {"manifest_schema": 1, "compatibility": key, "pair_count": pair_count}
    manifest = {**core, "run_id": hashlib.sha256(canonical_json(core)).hexdigest(),
                "state": "CREATED", "artifacts": []}
    validate_manifest(manifest)
    return manifest


def write_manifest_create_only(path: str | Path, manifest: Mapping[str, Any],
                               *, chunks: Iterable[Mapping[str, Any]] | None = None,
                               artifact_root: str | Path | None = None) -> None:
    """Publish a schema-valid manifest without replacing an existing path."""
    if manifest.get("state") == "COMPLETE":
        if chunks is None:
            raise ManifestError("complete manifest requires validated chunks")
        seed_manifest = {**dict(manifest), "state": "CREATED", "artifacts": []}
        finalized = finalize_manifest(seed_manifest, chunks, artifact_root=artifact_root)
        if finalized != dict(manifest):
            raise ManifestError("complete manifest does not match validated chunks")
    else:
        validate_manifest(manifest)
    target = Path(path)
    payload = canonical_json(dict(manifest)) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(target, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        raise


def read_manifest(path: str | Path) -> dict[str, Any]:
    """Read and validate a manifest; unsupported versions fail closed."""
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read manifest: {exc}") from exc
    if not isinstance(value, dict):
        raise ManifestError("manifest must be a JSON object")
    validate_manifest(value)
    return value


def finalize_manifest(manifest: Mapping[str, Any],
                      chunks: Iterable[Mapping[str, Any]], *,
                      artifact_root: str | Path | None = None) -> dict[str, Any]:
    """Return COMPLETE only after full coverage and byte hashes match isolated artifacts."""
    validate_manifest(manifest)
    if manifest["state"] not in {"CREATED", "RUNNING"}:
        raise ManifestError("only CREATED or RUNNING manifests may be finalized")
    ordered = validate_chunks(manifest["pair_count"],
                              manifest["compatibility"]["chunk_size"], chunks)
    if artifact_root is None:
        raise ManifestError("artifact_root is required to finalize a COMPLETE manifest")
    verify_artifact_bytes(ordered, artifact_root)
    artifacts = []
    for chunk in ordered:
        path, digest = chunk.get("path"), chunk.get("sha256")
        artifact = {"path": path, "sha256": digest}
        errors = _schema_errors(artifact, json.loads(Path(__file__).with_name("RUN_MANIFEST_SCHEMA.json").read_text(encoding="utf-8"))["properties"]["artifacts"]["items"])
        if errors:
            raise ManifestError("chunk artifact metadata invalid: " + "; ".join(errors))
        artifacts.append(artifact)
    completed = {**dict(manifest), "state": "COMPLETE", "artifacts": artifacts}
    validate_manifest(completed)
    return completed


def assert_cache_compatible(expected: Mapping[str, Any], cached: Mapping[str, Any]) -> None:
    expected_key = compatibility_key(expected)
    cached_key = compatibility_key(cached)
    mismatches = [name for name in COMPATIBILITY_FIELDS if expected_key[name] != cached_key[name]]
    if mismatches:
        raise ManifestError(f"cache incompatible fields: {', '.join(mismatches)}")


def validate_cache(expected: Mapping[str, Any], manifest: Mapping[str, Any],
                   chunks: Iterable[Mapping[str, Any]],
                   expected_pair_keys: Iterable[str], *,
                   artifact_root: str | Path | None = None) -> dict[str, Any]:
    """Accept only a complete, schema-valid cache over exact expected pair keys."""
    validate_manifest(manifest)
    if manifest["state"] != "COMPLETE":
        raise ManifestError("incomplete run cannot be used as a cache")
    assert_cache_compatible(expected, manifest["compatibility"])
    expected_keys = list(expected_pair_keys)
    if len(expected_keys) != manifest["pair_count"]:
        raise ManifestError("expected pair-key count does not match manifest")
    ordered = validate_chunks(manifest["pair_count"],
                              manifest["compatibility"]["chunk_size"], chunks)
    if artifact_root is None:
        raise ManifestError("artifact_root is required to validate a COMPLETE cache")
    verify_artifact_bytes(ordered, artifact_root)
    actual_keys = [key for chunk in ordered for key in chunk["pair_keys"]]
    if actual_keys != expected_keys:
        raise ManifestError("stale chunk pair population or ordering")
    chunk_artifacts = [{"path": chunk.get("path"), "sha256": chunk.get("sha256")}
                       for chunk in ordered]
    if chunk_artifacts != manifest["artifacts"]:
        raise ManifestError("manifest artifacts do not match validated chunks")
    return dict(manifest)


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
            if not isinstance(key, str) or not key.strip():
                raise ManifestError("pair keys must be nonempty strings")
            if key in seen:
                raise ManifestError(f"duplicate pair key: {key!r}")
            seen.add(key)
        ordered.append(chunk)
    return ordered
