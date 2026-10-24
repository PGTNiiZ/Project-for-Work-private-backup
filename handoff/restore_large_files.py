"""Reassemble large files in this private transfer snapshot."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).with_name("large_files.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for entry in entries:
        target = ROOT / entry["path"]
        if target.exists() and target.stat().st_size == entry["size"] and sha256(target) == entry["sha256"]:
            print(f"OK {entry['path']}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".restore.tmp")
        try:
            with temporary.open("wb") as output:
                for part in entry["parts"]:
                    source = ROOT / part["path"]
                    if source.stat().st_size != part["size"] or sha256(source) != part["sha256"]:
                        raise ValueError(f"Invalid part: {part['path']}")
                    with source.open("rb") as stream:
                        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                            output.write(chunk)
            if temporary.stat().st_size != entry["size"] or sha256(temporary) != entry["sha256"]:
                raise ValueError(f"Reassembled file failed SHA-256: {entry['path']}")
            os.replace(temporary, target)
            print(f"RESTORED {entry['path']}")
        finally:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
