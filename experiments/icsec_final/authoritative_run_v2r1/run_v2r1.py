"""Canonical v2r1 integrity-repaired verification rerun CLI.

Reuses the FROZEN v2 scientific inputs (candidates, features, routing,
splits, scientific_inputs) verbatim — verified by SHA-256 against the v2
manifests — and executes the identical scientific computation with the
integrity-repaired runner, writing ONLY to authoritative_run_v2r1/.

Usage:
    python -m experiments.icsec_final.authoritative_run_v2r1.run_v2r1 \
        --mode scientific-final --authorize-final-scientific-run \
        --outer-seeds 101 202 303
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd

from experiments.icsec_final.authoritative_run_v2.final_runner import FINAL_BUDGET, FinalRunnerError
from experiments.icsec_final.authoritative_run_v2.provenance import sha256_file
from experiments.icsec_final.authoritative_run_v2r1.final_runner_r1 import (
    IntegrityRepairedRunner, build_real_fixture_label_free, validate_input_artifacts_label_free,
)
from experiments.icsec_final.authoritative_run_v2r1.sealed_guard import GUARD

ROOT = _REPO_ROOT
V2 = ROOT / "experiments" / "icsec_final" / "authoritative_run_v2"
V2R1 = ROOT / "experiments" / "icsec_final" / "authoritative_run_v2r1"
PROFILES_PATH = ROOT / "data_for_project" / "normalized_profiles_with_profile_id.csv"
SEEDS = [101, 202, 303]

FROZEN_INPUTS = [
    "candidates/exact_tier.parquet", "candidates/model_scored.parquet", "candidates/workflow.parquet",
    "features/gb17.parquet", "features/bert_cos.parquet",
    "splits/outer_101.json", "splits/outer_202.json", "splits/outer_303.json",
    "routing/outer_101/workflow.parquet", "routing/outer_202/workflow.parquet", "routing/outer_303/workflow.parquet",
]
SOURCES = [
    "experiments/code/run_icsec_authoritative_v2.py",
    "experiments/icsec_final/authoritative_run_v2/features.py",
    "experiments/icsec_final/authoritative_run_v2/policies.py",
    "experiments/icsec_final/authoritative_run_v2/final_runner.py",
    "experiments/icsec_final/authoritative_run_v2/artifact_producers.py",
    "experiments/icsec_final/authoritative_run_v2/real_adapters.py",
    "experiments/icsec_final/authoritative_run_v2/label_sealing.py",
    "experiments/icsec_final/authoritative_run_v2r1/final_runner_r1.py",
    "experiments/icsec_final/authoritative_run_v2r1/sealed_guard.py",
    "experiments/icsec_final/authoritative_run_v2r1/run_v2r1.py",
    "experiments/icsec_final/authoritative_run_v2r1/PROTOCOL_V2R1.md",
]


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unavailable"


def minilm_revision() -> dict[str, object]:
    """Recover the transformer revision backing the frozen bert_cos cache
    from the local HuggingFace cache. Never downloads or recomputes."""
    info: dict[str, object] = {"model_identifier": "sentence-transformers/all-MiniLM-L6-v2",
                               "frozen_cache_sha256": sha256_file(V2 / "features" / "bert_cos.parquet")}
    hub = Path.home() / ".cache" / "huggingface" / "hub" / "models--sentence-transformers--all-MiniLM-L6-v2"
    snapshots = sorted((hub / "snapshots").glob("*")) if (hub / "snapshots").is_dir() else []
    refs = hub / "refs" / "main"
    if refs.is_file():
        info["revision"] = refs.read_text().strip()
        info["revision_source"] = "local huggingface hub refs/main"
    elif len(snapshots) == 1:
        info["revision"] = snapshots[0].name
        info["revision_source"] = "single local snapshot directory"
    else:
        info["revision"] = None
        info["revision_source"] = ("unresolved: from-scratch model revision provenance could not be "
                                   "recovered; the frozen feature cache is retained by SHA-256")
    return info


def capture_provenance() -> dict[str, object]:
    manifest = {
        "run": "authoritative_run_v2r1",
        "lifecycle": "artifact preparation -> seal -> scientific runner (no test-label-value "
                     "materialization) -> predictions frozen/hashed -> final label reveal",
        "git_commit": _git("rev-parse", "HEAD"),
        "git_branch": _git("branch", "--show-current"),
        "git_dirty": bool(_git("status", "--porcelain=v1", "-uno")),
        "git_untracked_present": bool(_git("status", "--porcelain=v1")),
        "python": sys.version,
        "platform": platform.platform(),
        "dataset": {"path": str(PROFILES_PATH), "sha256": sha256_file(PROFILES_PATH)},
        "frozen_inputs": {rel: sha256_file(V2 / rel) for rel in FROZEN_INPUTS},
        "sources": {rel: sha256_file(ROOT / rel) for rel in SOURCES},
        "minilm": minilm_revision(),
        "scientific_input_manifests": {},
        "sealed_label_artifacts": {},
        "development_label_artifacts": {},
        "blocking_miss_artifacts": {},
    }
    for seed in SEEDS:
        meta_path = V2 / "scientific_inputs" / f"outer_{seed}" / "input_artifact_manifest.json"
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        manifest["scientific_input_manifests"][str(seed)] = {"path": str(meta_path), "sha256": sha256_file(meta_path)}
        arts = metadata["artifacts"]
        manifest["sealed_label_artifacts"][str(seed)] = arts["sealed_test"]["sha256"]
        manifest["development_label_artifacts"][str(seed)] = arts["development"]["sha256"]
        manifest["blocking_miss_artifacts"][str(seed)] = arts["blocking_miss"]["sha256"]
    out = V2R1 / "provenance"
    out.mkdir(parents=True, exist_ok=True)
    (out / "v2r1_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    return manifest


def validate_gate(seeds: list[int]) -> None:
    if seeds != SEEDS:
        raise FinalRunnerError("scientific-final mode requires exactly outer seeds 101 202 303")
    if FINAL_BUDGET != 12000:
        raise FinalRunnerError("frozen B2/B3 budget differs")
    lock_path = V2 / "scientific_inputs" / "frozen_protocol_hashes.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    for raw, expected_hash in lock.items():
        if sha256_file(ROOT / raw) != expected_hash:
            raise FinalRunnerError(f"frozen protocol hash differs: {raw}")
    for seed in seeds:
        metadata = V2 / "scientific_inputs" / f"outer_{seed}" / "input_artifact_manifest.json"
        validate_input_artifacts_label_free(metadata)  # label-free by construction


def execute(seeds: list[int]) -> dict[str, object]:
    GUARD.install()
    GUARD.set_phase("PREPARATION")
    # Register every sealed-label artifact BEFORE any validation.
    for seed in SEEDS:
        metadata = json.loads((V2 / "scientific_inputs" / f"outer_{seed}" / "input_artifact_manifest.json").read_text(encoding="utf-8"))
        GUARD.register(metadata["artifacts"]["sealed_test"]["path"])
    validate_gate(seeds)
    provenance = capture_provenance()
    outputs: dict[str, object] = {"provenance_manifest": str(V2R1 / "provenance" / "v2r1_manifest.json")}
    for seed in seeds:
        routed = pd.read_parquet(V2 / "routing" / f"outer_{seed}" / "workflow.parquet")
        fixture = build_real_fixture_label_free(
            V2 / "scientific_inputs" / f"outer_{seed}" / "input_artifact_manifest.json", routed,
            pd.read_parquet(V2 / "features" / "gb17.parquet"), pd.read_parquet(V2 / "features" / "bert_cos.parquet"))
        fixture["NOT_MANUSCRIPT_EVIDENCE"] = False
        runner = IntegrityRepairedRunner(fixture, V2R1 / "scientific_outputs" / f"outer_{seed}", seed=seed, budget=FINAL_BUDGET)
        outputs[str(seed)] = runner.run()
        GUARD.set_phase("PREPARATION")  # next seed starts label-closed again
    del provenance
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("scientific-final",), required=True)
    parser.add_argument("--authorize-final-scientific-run", action="store_true")
    parser.add_argument("--outer-seeds", nargs="+", type=int, default=[])
    args = parser.parse_args()
    if not args.authorize_final_scientific_run:
        raise SystemExit("fail-closed: pass --authorize-final-scientific-run")
    print(json.dumps(execute(args.outer_seeds), indent=2, default=str))


if __name__ == "__main__":
    main()
