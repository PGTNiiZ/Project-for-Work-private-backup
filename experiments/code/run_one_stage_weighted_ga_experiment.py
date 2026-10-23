"""Validation-only experiment for a 10-gene, one-stage weighted GA policy.

The historical policy uses two probability thresholds plus two name-similarity
cutoffs.  This experiment removes the name promote/demote cutoffs and learns a
single availability-conditioned policy score from eight weighted inputs before
applying only MATCH and REVIEW thresholds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from experiments.code.run_feature_aware_ga_pipeline import (
    ONE_STAGE_POLICY_FEATURES,
    ONE_STAGE_POLICY_VERSION,
    SOURCE,
    decision_metrics,
    decisions,
    derive_decisioning_features,
    load_profile_evidence,
    one_stage_decisions,
    one_stage_policy_score,
    optimize_one_stage_policy,
    optimize_policy,
)
from identity_resolution.core.business_cost import CRM_COST_POLICY_VERSION, CRM_COST_WEIGHTS
from identity_resolution.settings import PROJECT_ROOT


DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "artifacts"
    / "decisioning"
    / "feature_aware_ga"
    / ONE_STAGE_POLICY_VERSION
)
DEFAULT_SEEDS = tuple(range(42, 52))
POLICY_ONE_STAGE = "one_stage_weighted_10gene"
POLICY_SCORE_ONLY = "score_only_2threshold"
POLICY_LEGACY_NAME = "legacy_name_guard_4threshold"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_status(output: Path, phase: str, detail: str, progress: int) -> None:
    payload = {
        "phase": phase,
        "detail": detail,
        "progress": int(progress),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    (output / "status.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[{progress:3d}%] {phase}: {detail}", flush=True)


def load_split_cache(split_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read and derive one explicitly requested split."""
    if split_name not in {"val", "test"}:
        raise ValueError("split_name must be val or test")
    pairs = pd.read_parquet(SOURCE, filters=[("split_name", "==", split_name)])
    if pairs.empty or set(pairs["split_name"].unique()) != {split_name}:
        raise ValueError(f"parquet filter returned an unexpected {split_name} split")
    profiles = load_profile_evidence()
    cache = derive_decisioning_features(pairs, profiles, include_model_features=False)
    return cache.reset_index(drop=True), pairs.reset_index(drop=True)


def load_validation_cache() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read validation rows only; retained as the validation-only public entry point."""
    return load_split_cache("val")


def load_all_cache() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Derive policy evidence for every row in the labeled dataset."""
    pairs = pd.read_parquet(SOURCE)
    expected = {"train", "val", "test"}
    if pairs.empty or set(pairs["split_name"].unique()) != expected:
        raise ValueError(f"full dataset must contain exactly these splits: {sorted(expected)}")
    profiles = load_profile_evidence()
    cache = derive_decisioning_features(pairs, profiles, include_model_features=False)
    return cache.reset_index(drop=True), pairs.reset_index(drop=True)


def policy_inputs(cache: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    score_columns = [
        "probability" if feature == "probability" else f"{feature}_score"
        for feature in ONE_STAGE_POLICY_FEATURES
    ]
    scores = cache[score_columns].to_numpy(dtype=float)
    mask_columns = [
        np.ones(len(cache), dtype=float)
        if feature == "probability"
        else cache[f"{feature}_available"].to_numpy(dtype=float)
        for feature in ONE_STAGE_POLICY_FEATURES
    ]
    return scores, np.column_stack(mask_columns)


def policy_matrices(
    cache: pd.DataFrame,
    labels: np.ndarray,
    *,
    min_coverage: float,
    min_positive_support: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    scores, masks = policy_inputs(cache)
    if not np.isfinite(scores).all() or np.any((scores < 0.0) | (scores > 1.0)):
        raise ValueError("one-stage policy scores must be finite and normalized to [0, 1]")
    active = np.zeros(len(ONE_STAGE_POLICY_FEATURES), dtype=bool)
    for index, feature in enumerate(ONE_STAGE_POLICY_FEATURES):
        available = masks[:, index].astype(bool)
        active[index] = bool(
            feature == "probability"
            or (
                available.any()
                and available.mean() >= min_coverage
                and int(labels[available].sum()) >= min_positive_support
            )
        )
    if not active[0]:
        raise ValueError("frozen probability must always be active")
    return scores, masks, active


def expanded_metrics(decision: np.ndarray, labels: np.ndarray) -> dict[str, int | float | bool]:
    base = decision_metrics(decision, labels)
    match = decision == 2
    no_match = decision == 0
    positive = labels == 1
    negative = ~positive
    values: dict[str, int | float | bool] = {
        "tp": int((match & positive).sum()),
        "tn": int((no_match & negative).sum()),
        **base,
    }
    values["precision_gate_pass"] = bool(base["precision"] >= 0.99)
    values["recall_gate_pass"] = bool(base["recall"] >= 0.70)
    values["basic_quality_gates_pass"] = bool(
        values["precision_gate_pass"] and values["recall_gate_pass"]
    )
    return values


def one_stage_trial(
    policy: str,
    seed: int,
    scores: np.ndarray,
    masks: np.ndarray,
    labels: np.ndarray,
    active: np.ndarray,
    population_size: int,
    generations: int,
    elite_size: int,
) -> tuple[dict[str, object], list[dict], np.ndarray]:
    genome, history = optimize_one_stage_policy(
        scores,
        masks,
        labels,
        seed,
        active_mask=active,
        population_size=population_size,
        generations=generations,
        elite_size=elite_size,
    )
    decision = one_stage_decisions(scores, masks, genome)
    row: dict[str, object] = {
        "policy": policy,
        "seed": seed,
        "genome": json.dumps(genome.tolist()),
        "t_match": float(genome[0]),
        "t_review": float(genome[1]),
        "c_promote": np.nan,
        "c_demote": np.nan,
    }
    row.update({f"w_{feature}": float(value) for feature, value in zip(ONE_STAGE_POLICY_FEATURES, genome[2:])})
    row.update(expanded_metrics(decision, labels))
    return row, history, decision


def legacy_name_trial(
    seed: int,
    cache: pd.DataFrame,
    labels: np.ndarray,
    population_size: int = 60,
    generations: int = 40,
    elite_size: int = 12,
) -> tuple[dict[str, object], list[dict], np.ndarray]:
    probability = cache["probability"].to_numpy(dtype=float)
    evidence = cache["name_score"].to_numpy(dtype=float)
    available = cache["name_available"].to_numpy(dtype=np.int8)
    genome, history = optimize_policy(
        probability, evidence, available, labels, seed,
        population_size=population_size, generations=generations, elite_size=elite_size,
    )
    decision = decisions(probability, evidence, available, genome)
    row: dict[str, object] = {
        "policy": POLICY_LEGACY_NAME,
        "seed": seed,
        "genome": json.dumps(genome.tolist()),
        "t_match": float(genome[0]),
        "t_review": float(genome[1]),
        "c_promote": float(genome[2]),
        "c_demote": float(genome[3]),
    }
    row.update({f"w_{feature}": np.nan for feature in ONE_STAGE_POLICY_FEATURES})
    row.update(expanded_metrics(decision, labels))
    return row, history, decision


def feature_coverage(scores: np.ndarray, masks: np.ndarray, labels: np.ndarray, active: np.ndarray) -> pd.DataFrame:
    rows = []
    for index, feature in enumerate(ONE_STAGE_POLICY_FEATURES):
        available = masks[:, index].astype(bool)
        high = available & (scores[:, index] >= 0.5)
        rows.append({
            "feature": feature,
            "validation_rows": len(labels),
            "available_rows": int(available.sum()),
            "availability_coverage": float(available.mean()),
            "available_positive_support": int(labels[available].sum()),
            "high_score_rows": int(high.sum()),
            "high_score_positive_rate": float(labels[high].mean()) if high.any() else 0.0,
            "active_in_ga": bool(active[index]),
        })
    return pd.DataFrame(rows)


def summarize_trials(trials: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for policy, group in trials.groupby("policy", sort=False):
        best = group.sort_values(["cost", "fp", "fn", "review", "seed"]).iloc[0]
        rows.append({
            "policy": policy,
            "seeds": int(len(group)),
            "median_cost": float(group["cost"].median()),
            "best_cost": float(group["cost"].min()),
            "worst_cost": float(group["cost"].max()),
            "median_precision": float(group["precision"].median()),
            "median_recall": float(group["recall"].median()),
            "median_f1": float(group["f1"].median()),
            "gate_pass_seeds": int(group["basic_quality_gates_pass"].sum()),
            "best_seed": int(best["seed"]),
            "best_genome": best["genome"],
        })
    return pd.DataFrame(rows).sort_values(["median_cost", "best_cost"]).reset_index(drop=True)


def weight_summary(trials: pd.DataFrame) -> pd.DataFrame:
    selected = trials[trials["policy"] == POLICY_ONE_STAGE]
    best = selected.sort_values(["cost", "fp", "fn", "review", "seed"]).iloc[0]
    rows = []
    for feature in ONE_STAGE_POLICY_FEATURES:
        values = selected[f"w_{feature}"].astype(float)
        rows.append({
            "feature": feature,
            "best_seed_weight": float(best[f"w_{feature}"]),
            "median_weight": float(values.median()),
            "mean_weight": float(values.mean()),
            "std_weight": float(values.std(ddof=0)),
            "min_weight": float(values.min()),
            "max_weight": float(values.max()),
        })
    return pd.DataFrame(rows)


def bootstrap_intervals(
    policy_decisions: dict[str, np.ndarray],
    labels: np.ndarray,
    samples: int,
    seed: int = 20260901,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for policy, decision in policy_decisions.items():
        draws: dict[str, list[float]] = {key: [] for key in ("precision", "recall", "f1", "cost")}
        for _ in range(samples):
            index = rng.integers(0, len(labels), len(labels))
            metrics = decision_metrics(decision[index], labels[index])
            for key in draws:
                draws[key].append(float(metrics[key]))
        for metric, values in draws.items():
            low, high = np.quantile(values, [0.025, 0.975])
            rows.append({
                "policy": policy,
                "metric": metric,
                "bootstrap_samples": samples,
                "ci95_low": float(low),
                "ci95_high": float(high),
            })
    return pd.DataFrame(rows)


def platform_metrics(
    pairs: pd.DataFrame,
    labels: np.ndarray,
    policy_decisions: dict[str, np.ndarray],
) -> pd.DataFrame:
    platform_pair = pairs.apply(
        lambda row: " x ".join(sorted((str(row["platform_a"]), str(row["platform_b"])))),
        axis=1,
    ).to_numpy()
    rows = []
    for policy, decision in policy_decisions.items():
        for pair_name in sorted(set(platform_pair)):
            selected = platform_pair == pair_name
            values = expanded_metrics(decision[selected], labels[selected])
            rows.append({
                "policy": policy,
                "platform_pair": pair_name,
                "rows": int(selected.sum()),
                "positive_support": int(labels[selected].sum()),
                **values,
            })
    return pd.DataFrame(rows)


def best_decisions(
    trials: pd.DataFrame,
    cache: pd.DataFrame,
    scores: np.ndarray,
    masks: np.ndarray,
) -> dict[str, np.ndarray]:
    result = {}
    for policy, group in trials.groupby("policy", sort=False):
        best = group.sort_values(["cost", "fp", "fn", "review", "seed"]).iloc[0]
        genome = np.asarray(json.loads(best["genome"]), dtype=float)
        if policy == POLICY_LEGACY_NAME:
            result[policy] = decisions(
                cache["probability"].to_numpy(dtype=float),
                cache["name_score"].to_numpy(dtype=float),
                cache["name_available"].to_numpy(dtype=np.int8),
                genome,
            )
        else:
            result[policy] = one_stage_decisions(scores, masks, genome)
    return result


def write_report(
    output: Path,
    trials: pd.DataFrame,
    summary: pd.DataFrame,
    weights: pd.DataFrame,
    coverage: pd.DataFrame,
    intervals: pd.DataFrame,
) -> None:
    new_best = trials[trials.policy == POLICY_ONE_STAGE].sort_values(
        ["cost", "fp", "fn", "review", "seed"]
    ).iloc[0]
    legacy_best = trials[trials.policy == POLICY_LEGACY_NAME].sort_values(
        ["cost", "fp", "fn", "review", "seed"]
    ).iloc[0]
    score_best = trials[trials.policy == POLICY_SCORE_ONLY].sort_values(
        ["cost", "fp", "fn", "review", "seed"]
    ).iloc[0]
    summary_lines = "\n".join(
        f"| {row.policy} | {row.median_cost:.2f} | {row.best_cost:.2f} | {row.worst_cost:.2f} | {row.median_precision:.4f} | {row.median_recall:.4f} | {row.median_f1:.4f} | {int(row.gate_pass_seeds)}/{int(row.seeds)} |"
        for row in summary.itertuples(index=False)
    )
    weight_lines = "\n".join(
        f"| {row.feature} | {row.best_seed_weight:.6f} | {row.median_weight:.6f} | {row.std_weight:.6f} |"
        for row in weights.itertuples(index=False)
    )
    coverage_lines = "\n".join(
        f"| {row.feature} | {row.availability_coverage:.2%} | {int(row.available_positive_support):,} | {row.high_score_positive_rate:.4f} | {'yes' if row.active_in_ga else 'no'} |"
        for row in coverage.itertuples(index=False)
    )
    ci = intervals[intervals.policy == POLICY_ONE_STAGE].set_index("metric")
    inactive = coverage.loc[~coverage.active_in_ga, "feature"].tolist()
    eligibility_note = (
        "ทุก feature เปิดให้ GA เรียนรู้น้ำหนักได้; น้ำหนักศูนย์ในผลลัพธ์เป็นค่าที่ GA เลือกเอง."
        if not inactive else
        "Feature ที่ไม่มีข้อมูลหรือไม่ผ่าน coverage/support ตาม protocol.json ถูกบังคับน้ำหนักศูนย์: " + ", ".join(inactive)
    )
    text = f"""# ผลทดลอง One-Stage Weighted GA: 2 Thresholds + 8 Feature Weights

## สิ่งที่เปลี่ยน

กฎเดิมใช้ genome 4 ค่า `[t_match, t_review, c_promote, c_demote]` และนำ `name_sim`
ไปเทียบทั้ง promote/demote cutoffs ใน review band. รอบนี้ตัด `c_promote/c_demote` ออกและใช้
genome 10 ค่า:

```text
[t_match, t_review,
 w_probability, w_name, w_bio, w_url,
 w_location, w_social, w_image, w_style]
```

คะแนนทั้งแปดตัวถูกถ่วงน้ำหนักและ normalize เฉพาะ feature ที่ available ต่อคู่ จากนั้นตัดสิน
เพียงครั้งเดียวด้วยสอง threshold. `probability` ถูกเก็บเป็นหนึ่งในแปด input เพื่อไม่ทิ้งสัญญาณ
non-linear จาก frozen pair model. ผลทั้งหมดด้านล่างใช้ **validation {int(coverage.validation_rows.iloc[0]):,} คู่เท่านั้น** และไม่ได้อ่าน
หรือประเมิน held-out test.

## ผลหลาย Seed

| Policy | Median cost | Best | Worst | Median P | Median R | Median F1 | ผ่าน P>=.99 และ R>=.70 |
|---|---:|---:|---:|---:|---:|---:|---:|
{summary_lines}

ผู้ชนะ one-stage ตาม cost คือ seed **{int(new_best.seed)}**: thresholds
`[{new_best.t_match:.6f}, {new_best.t_review:.6f}]`, cost **{new_best.cost:.2f}**,
Precision **{new_best.precision:.4f}**, Recall **{new_best.recall:.4f}**, F1 **{new_best.f1:.4f}**,
FP={int(new_best.fp)}, FN={int(new_best.fn)}, REVIEW={int(new_best.review):,}.

เทียบ best legacy name guard: cost เปลี่ยน {new_best.cost - legacy_best.cost:+.2f},
FP {int(new_best.fp - legacy_best.fp):+d}, FN {int(new_best.fn - legacy_best.fn):+d},
REVIEW {int(new_best.review - legacy_best.review):+d}. เทียบ score-only: costเปลี่ยน
{new_best.cost - score_best.cost:+.2f}.

Bootstrap 95% CI ของ best one-stage: Precision
[{ci.loc['precision', 'ci95_low']:.4f}, {ci.loc['precision', 'ci95_high']:.4f}], Recall
[{ci.loc['recall', 'ci95_low']:.4f}, {ci.loc['recall', 'ci95_high']:.4f}], F1
[{ci.loc['f1', 'ci95_low']:.4f}, {ci.loc['f1', 'ci95_high']:.4f}] และ cost
[{ci.loc['cost', 'ci95_low']:.2f}, {ci.loc['cost', 'ci95_high']:.2f}].

## น้ำหนักที่ GA เรียนรู้

| Feature | Best-seed weight | Median {int(summary.seeds.iloc[0])} seeds | Std. |
|---|---:|---:|---:|
{weight_lines}

น้ำหนักเหล่านี้คือ **decision-policy weights** ไม่ใช่ feature importance หรือ coefficient ภายใน
pair model. ค่ามัธยฐานและส่วนเบี่ยงเบนใช้ดูความเสถียร; ห้ามตีความจาก best seed เพียงค่าเดียว.

## Coverage และ Support

| Feature | Coverage | Positive support | Positive rate เมื่อ score>=0.5 | Active |
|---|---:|---:|---:|---|
{coverage_lines}

{eligibility_note}
Social ใช้ `max(mention_jaccard, hashtag_jaccard)` และ mask เปิดเมื่อทั้งสอง profile มี
mention/hashtag evidence. อ่าน coverage ในตารางประกอบการตีความน้ำหนัก.

## ข้อสรุป

ผลนี้เป็น **validation-only experiment** ซึ่งเลือกและวัด best seed บนชุดเดียวกัน;
bootstrap CI ไม่ได้รวมความไม่แน่นอนจากการเลือก policy. Legacy ใช้ population 60, generations 40
ขณะที่ one-stage และ score-only ใช้งบตาม protocol.json จึงไม่ใช่การเทียบด้วยงบค้นหาเท่ากัน.
การที่ policy มี cost ต่ำไม่ได้แปลว่าพร้อม production;
ต้องผ่าน precision/recall gates, ตรวจทุก platform pair, กำหนด review capacity และ freeze policy
ก่อนใช้ fresh audit test. Historical test เดิมไม่ได้ถูกเปิดซ้ำในรอบนี้.
"""
    (output / "REPORT_TH.md").write_text(text, encoding="utf-8")


def evaluate_frozen_policies_on_test(
    output: Path,
    trials: pd.DataFrame,
    active: np.ndarray,
    bootstrap_samples: int,
    source_sha256: str,
) -> dict[str, object]:
    """Freeze validation-selected genomes, then evaluate the held-out test split."""
    frozen: dict[str, dict[str, object]] = {}
    for policy, group in trials.groupby("policy", sort=False):
        best = group.sort_values(["cost", "fp", "fn", "review", "seed"]).iloc[0]
        frozen[policy] = {
            "seed": int(best.seed),
            "genome": json.loads(best.genome),
            "validation_metrics": {
                key: (bool(best[key]) if key.endswith("pass") else float(best[key]))
                for key in ("precision", "recall", "f1", "cost", "fp", "fn", "review", "basic_quality_gates_pass")
            },
        }
    freeze = {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "selection_split": "val",
        "selection_rule": "minimum validation cost, then FP, FN, REVIEW, and seed",
        "test_rows_read_before_freeze": False,
        "source": str(SOURCE),
        "source_sha256": source_sha256,
        "active_features_frozen_from_validation": dict(zip(ONE_STAGE_POLICY_FEATURES, active.tolist())),
        "policies": frozen,
    }
    freeze_path = output / "frozen_policies_before_test.json"
    freeze_path.write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    freeze_sha256 = sha256_file(freeze_path)

    write_status(output, "TEST", "policies frozen; reading held-out test once", 90)
    if sha256_file(SOURCE) != source_sha256:
        raise RuntimeError("source parquet changed between validation selection and test evaluation")
    test_cache, test_pairs = load_split_cache("test")
    labels = test_cache["label"].to_numpy(dtype=np.int8)
    scores, masks = policy_inputs(test_cache)
    decisions_by_policy = best_decisions(trials, test_cache, scores, masks)

    metric_rows = []
    for policy, decision in decisions_by_policy.items():
        metric_rows.append({"policy": policy, "test_rows": len(labels), **expanded_metrics(decision, labels)})
    metrics = pd.DataFrame(metric_rows).sort_values(["cost", "fp", "fn", "review"]).reset_index(drop=True)
    metrics.to_csv(output / "heldout_test_metrics.csv", index=False)

    intervals = bootstrap_intervals(decisions_by_policy, labels, bootstrap_samples, seed=20260914)
    intervals.to_csv(output / "heldout_test_bootstrap_intervals.csv", index=False)
    platform = platform_metrics(test_pairs, labels, decisions_by_policy)
    platform.to_csv(output / "heldout_test_platform_metrics.csv", index=False)
    feature_coverage(scores, masks, labels, active).to_csv(output / "heldout_test_feature_coverage.csv", index=False)

    names = {0: "NO_MATCH", 1: "REVIEW", 2: "MATCH"}
    one_stage = decisions_by_policy[POLICY_ONE_STAGE]
    transition_rows = []
    for baseline in (POLICY_SCORE_ONLY, POLICY_LEGACY_NAME):
        baseline_decision = decisions_by_policy[baseline]
        for before in (0, 1, 2):
            for after in (0, 1, 2):
                selected = (baseline_decision == before) & (one_stage == after)
                transition_rows.append({
                    "baseline": baseline,
                    "baseline_decision": names[before],
                    "one_stage_decision": names[after],
                    "rows": int(selected.sum()),
                    "positives": int(labels[selected].sum()),
                    "negatives": int(selected.sum() - labels[selected].sum()),
                })
    pd.DataFrame(transition_rows).to_csv(output / "heldout_test_decision_transitions.csv", index=False)

    metric_index = metrics.set_index("policy")
    one = metric_index.loc[POLICY_ONE_STAGE]
    val_one = frozen[POLICY_ONE_STAGE]["validation_metrics"]
    ci = intervals[intervals.policy == POLICY_ONE_STAGE].set_index("metric")
    comparison_lines = "\n".join(
        f"| {row.policy} | {row.cost:.1f} | {row.precision:.4f} | {row.recall:.4f} | {row.f1:.4f} | {int(row.fp)} | {int(row.fn)} | {int(row.review):,} |"
        for row in metrics.itertuples(index=False)
    )
    delta_lines = "\n".join(
        f"| {baseline} | {one.cost - metric_index.loc[baseline, 'cost']:+.1f} | {int(one.fp - metric_index.loc[baseline, 'fp']):+d} | {int(one.fn - metric_index.loc[baseline, 'fn']):+d} | {int(one.review - metric_index.loc[baseline, 'review']):+d} |"
        for baseline in (POLICY_SCORE_ONLY, POLICY_LEGACY_NAME)
    )
    report = f"""# ผลทดลองเต็มรูปแบบ: One-Stage Weighted GA

## Protocol

GA เลือก genome จาก validation เท่านั้น จำนวน {len(trials.seed.unique())} seeds โดยทุก policy ใช้
population และ generations เท่ากัน จากนั้นเขียน `frozen_policies_before_test.json` ก่อนอ่าน held-out
test. ไฟล์ freeze มี SHA-256 `{freeze_sha256}` และ source hash ถูกตรวจซ้ำก่อนประเมิน test.

## ผล Held-out Test ({len(labels):,} คู่; positive {int(labels.sum()):,})

| Policy | Cost | Precision | Recall | F1 | FP | FN | REVIEW |
|---|---:|---:|---:|---:|---:|---:|---:|
{comparison_lines}

ความต่างของ one-stage เทียบ baseline (ค่าติดลบลดลง):

| Baseline | ΔCost | ΔFP | ΔFN | ΔREVIEW |
|---|---:|---:|---:|---:|
{delta_lines}

One-stage ผ่าน gate รวมบน test: **{'ผ่าน' if bool(one.basic_quality_gates_pass) else 'ไม่ผ่าน'}**
(Precision ≥ .99 และ Recall ≥ .70). Bootstrap 95% CI: Precision
[{ci.loc['precision', 'ci95_low']:.4f}, {ci.loc['precision', 'ci95_high']:.4f}], Recall
[{ci.loc['recall', 'ci95_low']:.4f}, {ci.loc['recall', 'ci95_high']:.4f}], F1
[{ci.loc['f1', 'ci95_low']:.4f}, {ci.loc['f1', 'ci95_high']:.4f}], Cost
[{ci.loc['cost', 'ci95_low']:.1f}, {ci.loc['cost', 'ci95_high']:.1f}].

## Validation-to-Test Generalization

One-stage: cost {float(val_one['cost']):.1f} → {one.cost:.1f}, precision
{float(val_one['precision']):.4f} → {one.precision:.4f}, recall
{float(val_one['recall']):.4f} → {one.recall:.4f}, F1 {float(val_one['f1']):.4f} → {one.f1:.4f}.

ผลราย platform, coverage, bootstrap และ transition ระหว่างคำตัดสินอยู่ใน CSV ข้างรายงานนี้.
การประเมินนี้ครอบคลุม labeled pair population ใน `train_all.parquet`; ยังไม่ใช่การ project policy
ไปยัง full candidate cache ประมาณ 2.07 ล้านคู่ และ review capacity ยังไม่ได้กำหนด.
"""
    (output / "FULL_REPORT_TH.md").write_text(report, encoding="utf-8")
    result = {
        "policy_version": ONE_STAGE_POLICY_VERSION,
        "validation_selection_complete": True,
        "test_evaluated": True,
        "freeze_manifest": freeze_path.name,
        "freeze_manifest_sha256": freeze_sha256,
        "test_rows": int(len(labels)),
        "test_positive_support": int(labels.sum()),
        "test_metrics": metrics.to_dict(orient="records"),
        "one_stage_test_gate_pass": bool(one.basic_quality_gates_pass),
        "artifacts": {
            "report": "FULL_REPORT_TH.md",
            "metrics": "heldout_test_metrics.csv",
            "bootstrap": "heldout_test_bootstrap_intervals.csv",
            "platform_metrics": "heldout_test_platform_metrics.csv",
            "feature_coverage": "heldout_test_feature_coverage.csv",
            "decision_transitions": "heldout_test_decision_transitions.csv",
        },
    }
    (output / "full_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def project_frozen_policies_to_all_dataset(output: Path) -> dict[str, object]:
    """Apply already-frozen policies to train, validation, and test rows without tuning."""
    freeze_path = output / "frozen_policies_before_test.json"
    if not freeze_path.exists():
        raise FileNotFoundError("run validation selection and freeze policies before full-dataset projection")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if sha256_file(SOURCE) != freeze["source_sha256"]:
        raise RuntimeError("source parquet does not match the frozen-policy manifest")

    write_status(output, "PROJECT_ALL", "deriving evidence for every dataset row", 92)
    cache, pairs = load_all_cache()
    scores, masks = policy_inputs(cache)
    labels = cache["label"].to_numpy(dtype=np.int8)
    probability = cache["probability"].to_numpy(dtype=float)
    name_score = cache["name_score"].to_numpy(dtype=float)
    name_available = cache["name_available"].to_numpy(dtype=np.int8)

    decisions_by_policy: dict[str, np.ndarray] = {}
    policy_scores: dict[str, np.ndarray] = {}
    for policy, record in freeze["policies"].items():
        genome = np.asarray(record["genome"], dtype=float)
        if policy == POLICY_LEGACY_NAME:
            decisions_by_policy[policy] = decisions(
                probability, name_score, name_available, genome
            )
            policy_scores[policy] = probability
        else:
            decisions_by_policy[policy] = one_stage_decisions(scores, masks, genome)
            policy_scores[policy] = one_stage_policy_score(scores, masks, genome[2:])

    export = pairs[[
        "split_name", "pair_type", "label", "profile_row_id_a", "profile_row_id_b",
        "platform_a", "platform_b", "probability",
    ]].copy()
    label_names = np.asarray(["NO_MATCH", "REVIEW", "MATCH"])
    for policy, decision in decisions_by_policy.items():
        export[f"{policy}_score"] = policy_scores[policy]
        export[f"{policy}_decision_code"] = decision
        export[f"{policy}_decision"] = label_names[decision]
    export.to_parquet(output / "all_dataset_decisions.parquet", index=False)

    rows = []
    for split_name in ("train", "val", "test", "all"):
        selected = np.ones(len(cache), dtype=bool) if split_name == "all" else (
            cache["split_name"].to_numpy() == split_name
        )
        for policy, decision in decisions_by_policy.items():
            rows.append({
                "split_name": split_name,
                "policy": policy,
                "rows": int(selected.sum()),
                "positive_support": int(labels[selected].sum()),
                **expanded_metrics(decision[selected], labels[selected]),
            })
    metrics = pd.DataFrame(rows)
    metrics.to_csv(output / "all_dataset_metrics_by_split.csv", index=False)
    platform_metrics(pairs, labels, decisions_by_policy).to_csv(
        output / "all_dataset_platform_metrics.csv", index=False
    )

    overall = metrics[metrics.split_name == "all"].sort_values(["cost", "fp", "fn", "review"])
    lines = "\n".join(
        f"| {row.policy} | {int(row.rows):,} | {row.cost:.1f} | {row.precision:.4f} | {row.recall:.4f} | {row.f1:.4f} | {int(row.fp):,} | {int(row.fn):,} | {int(row.review):,} |"
        for row in overall.itertuples(index=False)
    )
    split_lines = "\n".join(
        f"| {row.split_name} | {int(row.rows):,} | {row.cost:.1f} | {row.precision:.4f} | {row.recall:.4f} | {row.f1:.4f} | {int(row.fp):,} | {int(row.fn):,} | {int(row.review):,} |"
        for row in metrics[metrics.policy == POLICY_ONE_STAGE].itertuples(index=False)
    )
    report = f"""# ผลการรัน Frozen GA Policy กับ Dataset ทั้งหมด

ใช้ genome ที่เลือกจาก validation และ freeze ไว้แล้วกับทุกแถวใน `train_all.parquet`
จำนวน {len(cache):,} คู่ โดยไม่มีการ train หรือปรับ threshold/weight เพิ่มจาก train หรือ test.

## ผลรวมทุก Split

| Policy | Rows | Cost | Precision | Recall | F1 | FP | FN | REVIEW |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{lines}

## One-Stage แยกตาม Split

| Split | Rows | Cost | Precision | Recall | F1 | FP | FN | REVIEW |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{split_lines}

แถวระดับคู่พร้อม score และคำตัดสินของทั้งสาม policy อยู่ใน
`all_dataset_decisions.parquet`. ค่า metrics รวม train มีไว้บอกผลการ apply policy ครบ dataset;
ใช้ held-out test ใน `FULL_REPORT_TH.md` สำหรับสรุปความสามารถในการ generalize.
"""
    (output / "ALL_DATASET_REPORT_TH.md").write_text(report, encoding="utf-8")
    result = {
        "policy_version": ONE_STAGE_POLICY_VERSION,
        "projection_only": True,
        "policy_tuning_performed": False,
        "source_sha256_verified": True,
        "dataset_rows": int(len(cache)),
        "split_rows": {str(k): int(v) for k, v in cache["split_name"].value_counts().items()},
        "overall_metrics": overall.to_dict(orient="records"),
        "artifacts": {
            "report": "ALL_DATASET_REPORT_TH.md",
            "pair_decisions": "all_dataset_decisions.parquet",
            "metrics_by_split": "all_dataset_metrics_by_split.csv",
            "platform_metrics": "all_dataset_platform_metrics.csv",
        },
    }
    (output / "all_dataset_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_status(output, "DONE", "frozen policies applied to all dataset rows", 100)
    return result


def run_experiment(
    output: Path,
    seeds: tuple[int, ...],
    population_size: int,
    generations: int,
    elite_size: int,
    bootstrap_samples: int,
    min_coverage: float,
    min_positive_support: int,
    evaluate_test: bool = False,
) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    write_status(output, "LOAD", "reading validation split and deriving eight policy inputs", 5)
    cache, pairs = load_validation_cache()
    labels = cache["label"].to_numpy(dtype=np.int8)
    scores, masks, active = policy_matrices(
        cache,
        labels,
        min_coverage=min_coverage,
        min_positive_support=min_positive_support,
    )
    coverage = feature_coverage(scores, masks, labels, active)
    coverage.to_csv(output / "feature_coverage.csv", index=False)

    protocol = {
        "policy_version": ONE_STAGE_POLICY_VERSION,
        "genome_order": ["t_match", "t_review", *[f"w_{feature}" for feature in ONE_STAGE_POLICY_FEATURES]],
        "feature_order": list(ONE_STAGE_POLICY_FEATURES),
        "score_formula": "sum(mask * weight * score) / sum(mask * weight)",
        "decision_rule": "MATCH if score >= t_match; NO_MATCH if score < t_review; REVIEW otherwise",
        "selection_split": "val",
        "validation_rows": int(len(cache)),
        "test_evaluated": False,
        "source": str(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "cost_policy_version": CRM_COST_POLICY_VERSION,
        "cost_weights": CRM_COST_WEIGHTS.as_dict(),
        "seeds": list(seeds),
        "population_size": population_size,
        "generations": generations,
        "elite_size": elite_size,
        "active_features": dict(zip(ONE_STAGE_POLICY_FEATURES, active.tolist())),
        "feature_eligibility": {
            "minimum_validation_coverage": min_coverage,
            "minimum_available_positive_support": min_positive_support,
            "probability_is_always_active": True,
            "features_without_observations_are_inactive": True,
        },
        "quality_gates_reported_not_optimized": {"precision_min": 0.99, "recall_min": 0.70},
    }
    (output / "protocol.json").write_text(json.dumps(protocol, indent=2), encoding="utf-8")

    rows: list[dict[str, object]] = []
    histories: dict[str, dict[str, list[dict]]] = {
        POLICY_SCORE_ONLY: {},
        POLICY_LEGACY_NAME: {},
        POLICY_ONE_STAGE: {},
    }
    score_only_active = np.zeros(len(ONE_STAGE_POLICY_FEATURES), dtype=bool)
    score_only_active[0] = True
    total_runs = len(seeds) * 3
    completed = 0
    for seed in seeds:
        row, history, _ = one_stage_trial(
            POLICY_SCORE_ONLY,
            seed,
            scores,
            masks,
            labels,
            score_only_active,
            population_size,
            generations,
            elite_size,
        )
        rows.append(row)
        histories[POLICY_SCORE_ONLY][str(seed)] = history
        completed += 1
        write_status(output, "GA", f"completed {POLICY_SCORE_ONLY} seed {seed}", 10 + round(75 * completed / total_runs))

        row, history, _ = legacy_name_trial(
            seed, cache, labels, population_size, generations, elite_size,
        )
        rows.append(row)
        histories[POLICY_LEGACY_NAME][str(seed)] = history
        completed += 1
        write_status(output, "GA", f"completed {POLICY_LEGACY_NAME} seed {seed}", 10 + round(75 * completed / total_runs))

        row, history, _ = one_stage_trial(
            POLICY_ONE_STAGE,
            seed,
            scores,
            masks,
            labels,
            active,
            population_size,
            generations,
            elite_size,
        )
        rows.append(row)
        histories[POLICY_ONE_STAGE][str(seed)] = history
        completed += 1
        write_status(output, "GA", f"completed {POLICY_ONE_STAGE} seed {seed}", 10 + round(75 * completed / total_runs))

    trials = pd.DataFrame(rows)
    trials.to_csv(output / "seed_results.csv", index=False)
    (output / "generation_history.json").write_text(json.dumps(histories, indent=2), encoding="utf-8")
    summary = summarize_trials(trials)
    summary.to_csv(output / "policy_summary.csv", index=False)
    weights = weight_summary(trials)
    weights.to_csv(output / "weight_stability.csv", index=False)

    selected_decisions = best_decisions(trials, cache, scores, masks)
    intervals = bootstrap_intervals(selected_decisions, labels, bootstrap_samples)
    intervals.to_csv(output / "bootstrap_intervals.csv", index=False)
    by_platform = platform_metrics(pairs, labels, selected_decisions)
    by_platform.to_csv(output / "platform_pair_metrics.csv", index=False)
    write_report(output, trials, summary, weights, coverage, intervals)

    new_best = trials[trials.policy == POLICY_ONE_STAGE].sort_values(
        ["cost", "fp", "fn", "review", "seed"]
    ).iloc[0]
    one_stage_platform = by_platform[
        (by_platform["policy"] == POLICY_ONE_STAGE)
        & (by_platform["positive_support"] >= 100)
    ]
    platform_precision_gate_pass = bool(
        len(one_stage_platform) > 0
        and (one_stage_platform["precision"] >= 0.98).all()
    )
    basic_gates_pass = bool(new_best.basic_quality_gates_pass)
    result = {
        "policy_version": ONE_STAGE_POLICY_VERSION,
        "validation_only": True,
        "test_evaluated": False,
        "best_seed": int(new_best.seed),
        "best_genome": json.loads(new_best.genome),
        "thresholds": [float(new_best.t_match), float(new_best.t_review)],
        "weights": {feature: float(new_best[f"w_{feature}"]) for feature in ONE_STAGE_POLICY_FEATURES},
        "validation_metrics": {
            "fp": int(new_best.fp),
            "fn": int(new_best.fn),
            "review": int(new_best.review),
            "precision": float(new_best.precision),
            "recall": float(new_best.recall),
            "f1": float(new_best.f1),
            "cost": float(new_best.cost),
            "precision_gate_pass": bool(new_best.precision_gate_pass),
            "recall_gate_pass": bool(new_best.recall_gate_pass),
            "basic_quality_gates_pass": basic_gates_pass,
            "platform_precision_gate_pass": platform_precision_gate_pass,
        },
        "validation_status": (
            "BASIC_AND_PLATFORM_GATES_PASSED_REVIEW_CAPACITY_UNSET"
            if basic_gates_pass and platform_precision_gate_pass
            else "VALIDATION_GATES_NOT_PASSED"
        ),
        "artifacts": {
            "report": "REPORT_TH.md",
            "trials": "seed_results.csv",
            "summary": "policy_summary.csv",
            "weights": "weight_stability.csv",
            "coverage": "feature_coverage.csv",
            "bootstrap": "bootstrap_intervals.csv",
            "platform_metrics": "platform_pair_metrics.csv",
        },
    }
    (output / "validation_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if evaluate_test:
        full_result = evaluate_frozen_policies_on_test(
            output, trials, active, bootstrap_samples, protocol["source_sha256"]
        )
        write_status(output, "DONE", "validation selection and held-out test evaluation completed", 100)
        return full_result
    write_status(output, "DONE", "validation-only one-stage experiment and report completed", 100)
    return result


def parse_seeds(value: str) -> tuple[int, ...]:
    seeds = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    if not seeds:
        raise argparse.ArgumentTypeError("provide at least one integer seed")
    return seeds


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the validation-only 2-threshold + 8-weight GA experiment.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seeds", type=parse_seeds, default=DEFAULT_SEEDS)
    parser.add_argument("--population-size", type=int, default=128)
    parser.add_argument("--generations", type=int, default=100)
    parser.add_argument("--elite-size", type=int, default=16)
    parser.add_argument("--bootstrap-samples", type=int, default=1000)
    parser.add_argument("--min-coverage", type=float, default=0.05)
    parser.add_argument("--min-positive-support", type=int, default=100)
    parser.add_argument("--evaluate-test", action="store_true", help="freeze validation-selected policies, then evaluate held-out test")
    parser.add_argument("--project-all-from-freeze", action="store_true", help="apply existing frozen policies to every train/val/test row without tuning")
    args = parser.parse_args()
    if args.project_all_from_freeze:
        result = project_frozen_policies_to_all_dataset(args.output.resolve())
        print(json.dumps(result, indent=2))
        return
    if args.population_size < 4:
        parser.error("--population-size must be at least 4")
    if not 1 <= args.elite_size < args.population_size:
        parser.error("--elite-size must be between 1 and population-size - 1")
    if args.generations < 1 or args.bootstrap_samples < 1:
        parser.error("--generations and --bootstrap-samples must be positive")
    if not 0.0 <= args.min_coverage <= 1.0 or args.min_positive_support < 0:
        parser.error("feature eligibility requires coverage in [0, 1] and non-negative support")
    result = run_experiment(
        args.output.resolve(),
        args.seeds,
        args.population_size,
        args.generations,
        args.elite_size,
        args.bootstrap_samples,
        args.min_coverage,
        args.min_positive_support,
        args.evaluate_test,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
