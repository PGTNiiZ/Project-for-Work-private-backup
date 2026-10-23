"""Capture complete authoritative-run provenance and SHA-256 manifest."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "experiments" / "icsec_final" / "authoritative_run"

def write(name: str, content: str) -> None:
    (OUT / name).write_text(content, encoding="utf-8")

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> None:
    write("environment.txt", "\n".join([
        f"captured_utc={datetime.now(timezone.utc).isoformat()}",
        f"platform={platform.platform()}",
        f"machine={platform.machine()}",
        f"python={sys.executable}",
        f"python_implementation={platform.python_implementation()}",
        f"processor={platform.processor()}",
        f"cwd={Path.cwd()}",
    ]) + "\n")
    write("python_version.txt", sys.version + "\n")
    packages = []
    for dist in sorted(importlib.metadata.distributions(), key=lambda d: d.metadata["Name"].lower()):
        name = dist.metadata["Name"]
        if name:
            packages.append(f"{name}=={dist.version}")
    write("package_versions.txt", "\n".join(packages) + "\n")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    status = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=True).stdout
    write("git_commit.txt", commit + "\n")
    write("git_status.txt", status)
    files = [p for p in OUT.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"]
    lines = [f"{digest(p)}  {p.relative_to(OUT)}" for p in sorted(files)]
    write("SHA256SUMS.txt", "\n".join(lines) + "\n")
    print(f"hashed_files={len(files)}")
    print(f"git_commit={commit}")

if __name__ == "__main__":
    main()
