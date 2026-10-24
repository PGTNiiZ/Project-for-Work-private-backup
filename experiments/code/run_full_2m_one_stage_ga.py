"""Tune the ten-gene one-stage policy on the full-cache validation population."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.code.project_one_stage_to_full_2m import (
    DEFAULT_OUTPUT,
    FEATURE_SOURCE,
    SOURCE,
    run_projection,
    score_and_mask_matrices,
    sha256_file,
)
from experiments.code.run_feature_aware_ga_pipeline import (
    ONE_STAGE_POLICY_FEATURES,
    decisions,
    decision_metrics,
    one_stage_decisions,
    optimize_one_stage_policy,
    optimize_policy,
)
from experiments.code.run_one_stage_weighted_ga_experiment import (
    POLICY_LEGACY_NAME,
    POLICY_ONE_STAGE,
    POLICY_SCORE_ONLY,
)


def load_validation(feature_source: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    manifest = json.loads((feature_source / "full_feature_manifest.json").read_text(encoding="utf-8"))
    if sha256_file(SOURCE) != manifest["source_sha256"]:
        raise RuntimeError("feature cache does not match the current 2M scored source")
    columns = [
        "split_name", "label", "probability",
        *[f"{feature}_score" for feature in ONE_STAGE_POLICY_FEATURES[1:] if feature != "social"],
        *[f"{feature}_available" for feature in ONE_STAGE_POLICY_FEATURES[1:] if feature != "social"],
    ]
    parts = []
    for index, item in enumerate(manifest["chunks"], start=1):
        path = Path(item["path"])
        parts.append(pd.read_parquet(path, columns=columns, filters=[("split_name", "==", "val")]))
        print(f"[{index:02d}/{len(manifest['chunks']):02d}] loaded validation rows", flush=True)
    validation = pd.concat(parts, ignore_index=True)
    return validation, manifest


def run(
    output: Path,
    feature_source: Path,
    seeds: tuple[int, ...],
    population_size: int,
    generations: int,
    elite_size: int,
) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    validation, manifest = load_validation(feature_source)
    scores, masks, absent = score_and_mask_matrices(validation)
    labels = validation["label"].to_numpy(np.int8)
    active = masks.astype(bool).any(axis=0)
    active[0] = True
    score_only = np.zeros(len(ONE_STAGE_POLICY_FEATURES), dtype=bool)
    score_only[0] = True
    rows = []
    histories: dict[str, dict[str, list[dict]]] = {
        POLICY_ONE_STAGE: {}, POLICY_SCORE_ONLY: {}, POLICY_LEGACY_NAME: {},
    }
    for seed in seeds:
        for policy, active_mask in ((POLICY_SCORE_ONLY, score_only), (POLICY_ONE_STAGE, active)):
            genome, history = optimize_one_stage_policy(
                scores, masks, labels, seed,
                active_mask=active_mask,
                population_size=population_size,
                generations=generations,
                elite_size=elite_size,
                candidate_batch_size=8,
            )
            metric = decision_metrics(one_stage_decisions(scores, masks, genome), labels)
            rows.append({
                "policy": policy, "seed": seed, "genome": json.dumps(genome.tolist()), **metric,
            })
            histories[policy][str(seed)] = history
            print(f"completed {policy} seed {seed}: validation cost {metric['cost']:.1f}", flush=True)
        genome, history = optimize_policy(
            validation["probability"].to_numpy(float),
            validation["name_score"].to_numpy(float),
            validation["name_available"].to_numpy(np.int8),
            labels, seed,
            population_size=population_size,
            generations=generations,
            elite_size=elite_size,
            candidate_batch_size=8,
        )
        metric = decision_metrics(
            decisions(
                validation["probability"].to_numpy(float),
                validation["name_score"].to_numpy(float),
                validation["name_available"].to_numpy(np.int8), genome,
            ), labels,
        )
        rows.append({
            "policy": POLICY_LEGACY_NAME, "seed": seed,
            "genome": json.dumps(genome.tolist()), **metric,
        })
        histories[POLICY_LEGACY_NAME][str(seed)] = history
        print(f"completed {POLICY_LEGACY_NAME} seed {seed}: validation cost {metric['cost']:.1f}", flush=True)
    trials = pd.DataFrame(rows)
    trials.to_csv(output / "full_2m_validation_trials.csv", index=False)
    (output / "full_2m_generation_history.json").write_text(json.dumps(histories, indent=2), encoding="utf-8")

    frozen = {}
    for policy, group in trials.groupby("policy", sort=False):
        best = group.sort_values(["cost", "fp", "fn", "review", "seed"]).iloc[0]
        frozen[policy] = {
            "seed": int(best.seed),
            "genome": json.loads(best.genome),
            "validation_metrics": {
                key: (int(best[key]) if key in {"fp", "fn", "review"} else float(best[key]))
                for key in ("precision", "recall", "f1", "cost", "fp", "fn", "review")
            },
        }
    freeze = {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "source": str(SOURCE),
        "source_sha256": manifest["source_sha256"],
        "selection_split": "val",
        "validation_rows": int(len(validation)),
        "test_read_before_freeze": False,
        "genome_order": ["t_match", "t_review", *[f"w_{x}" for x in ONE_STAGE_POLICY_FEATURES]],
        "active_features": dict(zip(ONE_STAGE_POLICY_FEATURES, active.tolist())),
        "absent_features": absent,
        "ga": {
            "seeds": list(seeds), "population_size": population_size,
            "generations": generations, "elite_size": elite_size,
        },
        "policies": frozen,
    }
    freeze_path = output / "full_2m_frozen_policies_before_test.json"
    freeze_path.write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    result = run_projection(output, feature_source, freeze_path)
    result["full_cache_validation_tuning_performed"] = True
    result["validation_trials"] = "full_2m_validation_trials.csv"
    result["generation_history"] = "full_2m_generation_history.json"
    (output / "full_2m_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def parse_seeds(value: str) -> tuple[int, ...]:
    return tuple(int(item) for item in value.split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--feature-source", type=Path, default=FEATURE_SOURCE)
    parser.add_argument("--seeds", type=parse_seeds, default=(42, 43, 44))
    parser.add_argument("--population-size", type=int, default=64)
    parser.add_argument("--generations", type=int, default=60)
    parser.add_argument("--elite-size", type=int, default=8)
    args = parser.parse_args()
    result = run(
        args.output.resolve(), args.feature_source.resolve(), args.seeds,
        args.population_size, args.generations, args.elite_size,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
