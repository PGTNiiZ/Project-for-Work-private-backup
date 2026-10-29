"""Hashable provenance primitives for the v2 run package."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(paths: list[str | Path], destination: str | Path) -> dict[str, str]:
    """Write deterministic path→SHA-256 manifest; missing inputs fail closed."""
    manifest: dict[str, str] = {}
    for raw_path in sorted((str(Path(path)) for path in paths)):
        path = Path(raw_path)
        if not path.is_file():
            raise FileNotFoundError(f"cannot hash missing provenance input: {path}")
        manifest[raw_path] = sha256_file(path)
    Path(destination).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
