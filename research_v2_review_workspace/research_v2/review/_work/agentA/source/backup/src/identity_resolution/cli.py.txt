"""Single command-line entry point for the ML lifecycle."""

from __future__ import annotations

import importlib
import sys


STAGES = {
    "prepare": "identity_resolution.stages.prepare",
    "pairs": "identity_resolution.stages.pairs",
    "features": "identity_resolution.stages.features",
    "train": "identity_resolution.stages.train_multimodal",
    "train-neural": "identity_resolution.stages.train_neural",
    "evaluate": "identity_resolution.stages.evaluate",
    "predict": "identity_resolution.workflows.full_candidate",
    "resolve": "identity_resolution.workflows.crm",
}


def usage() -> str:
    stages = "\n".join(f"  {name}" for name in STAGES)
    return (
        "usage: identity-ml <stage> [stage options]\n\n"
        "Canonical ML lifecycle stages:\n"
        f"{stages}\n\n"
        "Run `identity-ml <stage> --help` for stage-specific options."
    )


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print(usage())
        return
    stage = sys.argv[1]
    module_name = STAGES.get(stage)
    if module_name is None:
        raise SystemExit(f"Unknown stage: {stage}\n\n{usage()}")
    module = importlib.import_module(module_name)
    sys.argv = [f"identity-ml {stage}", *sys.argv[2:]]
    module.main()
