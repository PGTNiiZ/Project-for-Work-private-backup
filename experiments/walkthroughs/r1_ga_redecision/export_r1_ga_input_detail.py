"""Export the real R1 GA-validation rows with a column-by-column decision trace.

This is a teaching artifact.  It reads the frozen scored-pair cache and the
recorded selected genome; it does not retrain or rerun the genetic algorithm.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
SOURCE_CACHE = ROOT / "experiments" / "scored_pairs_enriched.parquet"
SOURCE_PROFILES = ROOT / "data_for_project" / "normalized_profiles_with_profile_id.csv"
SOURCE_SUMMARY = (
    ROOT / "experiments" / "automation" / "r1_nested_primary_20260809" / "summary.json"
)
SOURCE_CONFIG = (
    ROOT / "experiments" / "automation" / "r1_nested_primary_20260809" / "config.json"
)
OUTPUT_DIR = Path(__file__).resolve().parent / "data"

NESTED_SPLIT_VERSION = "entity_nested_v1"
NESTED_SPLIT_SEED = 42
SCORE_FLOOR = 0.5
# Historical R1 replay weights; current policy is crm_derived_v1 (2.0, 1.0, 0.1).
W_FP, W_FN, W_REVIEW = 5.0, 1.0, 0.02


def nested_role(entity_key: str) -> str:
    encoded = f"{NESTED_SPLIT_VERSION}:{NESTED_SPLIT_SEED}:{entity_key}".encode("utf-8")
    bucket = int(hashlib.md5(encoded).hexdigest(), 16) % 100
    if bucket < 70:
        return "model_train"
    if bucket < 85:
        return "model_calibration"
    return "ga_validation"


def entity_keys_by_profile() -> pd.Series:
    profiles = pd.read_csv(SOURCE_PROFILES, keep_default_na=False, low_memory=False)
    profiles["profile_row_id"] = pd.to_numeric(profiles["profile_row_id"], errors="coerce")
    profiles = profiles.loc[profiles["profile_row_id"].notna()].copy()
    profiles["profile_row_id"] = profiles["profile_row_id"].astype("int64")
    profiles = profiles.set_index("profile_row_id")
    folders = profiles["user_folder"].fillna("").astype(str).str.strip()
    keys = folders.where(folders != "", "pid:" + folders.index.astype(str))
    keys.name = "entity_key"
    return keys


def selected_genome() -> tuple[dict, dict]:
    summary = json.loads(SOURCE_SUMMARY.read_text(encoding="utf-8"))
    selected = summary["aggregates"]["A_current"]["best_genome_selected_by_validation_cost_only"]
    genome = {
        "t_m": float(selected["t_m"]),
        "t_r": float(selected["t_r"]),
        "c_promote": float(selected["c_promote"]),
        "c_demote": float(selected["c_demote"]),
    }
    return genome, summary


def build_detail() -> tuple[pd.DataFrame, dict]:
    cache = pd.read_parquet(SOURCE_CACHE)
    keys = entity_keys_by_profile()
    a_key = cache["profile_id_a"].map(keys)
    b_key = cache["profile_id_b"].map(keys)
    if a_key.isna().any() or b_key.isna().any():
        raise ValueError("Some scored-pair profile ids are absent from the profile table")

    a_role = a_key.map(nested_role)
    b_role = b_key.map(nested_role)
    validation = cache.loc[
        (cache["split"] == "val")
        & (a_role == "ga_validation")
        & (b_role == "ga_validation")
        & (cache["decision_source"] != "AUTO_EXACT")
    ].copy()
    validation = validation.reset_index(drop=True)

    genome, recorded_summary = selected_genome()
    t_m = genome["t_m"]
    t_r = genome["t_r"]
    c_p = genome["c_promote"]
    c_d = genome["c_demote"]
    p = validation["score"]
    s = validation["name_sim"]

    detail = pd.DataFrame({
        "row_id": validation.index + 1,
        "profile_id_a": validation["profile_id_a"].astype("int64"),
        "profile_id_b": validation["profile_id_b"].astype("int64"),
        "experiment_split": "ga_validation",
        "probability": p,
        "name_similarity": s,
        "actual_code": validation["actual"].astype("int8"),
        "actual_label": validation["actual"].map({0: "NO_MATCH", 1: "MATCH"}),
        "r0_decision_label": validation["decision"],
        "entered_run_ga": p >= SCORE_FLOOR,
        "t_m": t_m,
        "t_r": t_r,
        "c_promote": c_p,
        "c_demote": c_d,
        "prob_ge_t_m": p >= t_m,
        "prob_lt_t_r": p < t_r,
        "prob_in_band": (p >= t_r) & (p < t_m),
        "name_ge_c_promote": s >= c_p,
        "name_lt_c_demote": s < c_d,
    })

    detail["probability_route"] = "BETWEEN_THRESHOLDS"
    detail.loc[detail["prob_ge_t_m"], "probability_route"] = "DIRECT_MATCH"
    detail.loc[detail["prob_lt_t_r"], "probability_route"] = "DIRECT_NO_MATCH"

    detail["name_route"] = "NOT_USED"
    band = detail["prob_in_band"]
    detail.loc[band, "name_route"] = "REVIEW_ZONE"
    detail.loc[band & detail["name_ge_c_promote"], "name_route"] = "PROMOTE_TO_MATCH"
    detail.loc[band & detail["name_lt_c_demote"], "name_route"] = "DEMOTE_TO_NO_MATCH"

    detail["ga_decision_code"] = 1
    detail.loc[detail["prob_lt_t_r"], "ga_decision_code"] = 0
    detail.loc[band & detail["name_ge_c_promote"], "ga_decision_code"] = 2
    detail.loc[band & detail["name_lt_c_demote"], "ga_decision_code"] = 0
    detail.loc[detail["prob_ge_t_m"], "ga_decision_code"] = 2
    detail["ga_decision_label"] = detail["ga_decision_code"].map(
        {0: "NO_MATCH", 1: "REVIEW", 2: "MATCH"}
    )

    baseline_code = detail["r0_decision_label"].map({"NO_MATCH": 0, "REVIEW": 1, "MATCH": 2})
    if baseline_code.isna().any():
        raise ValueError("R0 contains an unknown decision label")
    detail["r0_decision_code"] = baseline_code.astype("int8")
    detail["r0_is_false_positive"] = (
        (detail["r0_decision_code"] == 2) & (detail["actual_code"] == 0)
    )
    detail["r0_is_false_negative"] = (
        (detail["r0_decision_code"] == 0) & (detail["actual_code"] == 1)
    )
    detail["r0_is_review"] = detail["r0_decision_code"] == 1
    detail["r0_row_cost"] = (
        detail["r0_is_false_positive"].astype(float) * W_FP
        + detail["r0_is_false_negative"].astype(float) * W_FN
        + detail["r0_is_review"].astype(float) * W_REVIEW
    )

    detail["is_false_positive"] = (
        (detail["ga_decision_code"] == 2) & (detail["actual_code"] == 0)
    )
    detail["is_false_negative"] = (
        (detail["ga_decision_code"] == 0) & (detail["actual_code"] == 1)
    )
    detail["is_review"] = detail["ga_decision_code"] == 1
    detail["fp_cost"] = detail["is_false_positive"].astype(float) * W_FP
    detail["fn_cost"] = detail["is_false_negative"].astype(float) * W_FN
    detail["review_cost"] = detail["is_review"].astype(float) * W_REVIEW
    detail["row_total_cost"] = detail[["fp_cost", "fn_cost", "review_cost"]].sum(axis=1)
    detail["decision_changed"] = detail["ga_decision_code"] != detail["r0_decision_code"]
    detail["cost_delta_ga_minus_r0"] = detail["row_total_cost"] - detail["r0_row_cost"]
    detail["ga_effect"] = "SAME_COST"
    detail.loc[detail["cost_delta_ga_minus_r0"] < 0, "ga_effect"] = "IMPROVED"
    detail.loc[detail["cost_delta_ga_minus_r0"] > 0, "ga_effect"] = "WORSENED"
    detail["search_row_cost"] = detail["row_total_cost"].where(detail["entered_run_ga"], 0.0)
    detail["constant_below_floor_cost"] = detail["fn_cost"].where(~detail["entered_run_ga"], 0.0)

    recorded_config = json.loads(SOURCE_CONFIG.read_text(encoding="utf-8"))
    fixed = recorded_config["split"]["validation"]
    selected = recorded_summary["aggregates"]["A_current"][
        "best_genome_selected_by_validation_cost_only"
    ]
    export_summary = {
        "source": "R1 nested primary ga_validation",
        "selected_seed": int(selected["seed"]),
        "selected_genome": genome,
        "weights": {"W_FP": W_FP, "W_FN": W_FN, "W_REVIEW": W_REVIEW},
        "row_counts": {
            "all_scored_ga_validation": int(len(detail)),
            "entered_run_ga_score_ge_0_5": int(detail["entered_run_ga"].sum()),
            "handled_as_constant_score_below_0_5": int((~detail["entered_run_ga"]).sum()),
        },
        "chromosome_counts": {
            "FP": int(detail["is_false_positive"].sum()),
            "FN": int(detail["is_false_negative"].sum()),
            "REVIEW": int(detail["is_review"].sum()),
        },
        "row_level_comparison_with_r0": {
            "r0_scored_rows_cost": float(detail["r0_row_cost"].sum()),
            "ga_scored_rows_cost": float(detail["row_total_cost"].sum()),
            "net_cost_delta_ga_minus_r0": float(detail["cost_delta_ga_minus_r0"].sum()),
            "decision_changed_rows": int(detail["decision_changed"].sum()),
            "improved_rows": int((detail["ga_effect"] == "IMPROVED").sum()),
            "worsened_rows": int((detail["ga_effect"] == "WORSENED").sum()),
            "same_cost_rows": int((detail["ga_effect"] == "SAME_COST").sum()),
        },
        "cost_reconciliation": {
            "search_rows_cost": float(detail["search_row_cost"].sum()),
            "constant_below_floor_fn_cost": float(detail["constant_below_floor_cost"].sum()),
            "objective_validation_cost": float(detail["row_total_cost"].sum()),
            "fixed_blocking_missed_fn": int(fixed["fn_blocking"]),
            "fixed_exact_tier_fp": int(fixed["fp_exact"]),
            "reported_full_validation_cost": float(selected["val_cost"]),
        },
    }
    return detail, export_summary


def branch_examples(detail: pd.DataFrame) -> pd.DataFrame:
    routes = [
        ("DIRECT_MATCH", detail["probability_route"] == "DIRECT_MATCH"),
        ("PROMOTE_TO_MATCH", detail["name_route"] == "PROMOTE_TO_MATCH"),
        ("REVIEW_ZONE", detail["name_route"] == "REVIEW_ZONE"),
        ("DEMOTE_TO_NO_MATCH", detail["name_route"] == "DEMOTE_TO_NO_MATCH"),
        ("DIRECT_NO_MATCH", (detail["probability_route"] == "DIRECT_NO_MATCH")
         & detail["entered_run_ga"]),
    ]
    examples = []
    for route, mask in routes:
        subset = detail.loc[mask]
        if subset.empty:
            continue
        examples.append(subset.iloc[0])
    return pd.DataFrame(examples).reset_index(drop=True)


def changed_examples(detail: pd.DataFrame) -> pd.DataFrame:
    """Return concrete improvements plus one honest counterexample when available."""
    cases = [
        ("REVIEW_TO_CORRECT_MATCH",
         (detail["r0_decision_label"] == "REVIEW")
         & (detail["ga_decision_label"] == "MATCH")
         & (detail["actual_label"] == "MATCH")),
        ("REVIEW_TO_CORRECT_NO_MATCH",
         (detail["r0_decision_label"] == "REVIEW")
         & (detail["ga_decision_label"] == "NO_MATCH")
         & (detail["actual_label"] == "NO_MATCH")),
        ("NO_MATCH_TO_CORRECT_MATCH",
         (detail["r0_decision_label"] == "NO_MATCH")
         & (detail["ga_decision_label"] == "MATCH")
         & (detail["actual_label"] == "MATCH")),
        ("NO_MATCH_TO_REVIEW_RECOVER_MATCH",
         (detail["r0_decision_label"] == "NO_MATCH")
         & (detail["ga_decision_label"] == "REVIEW")
         & (detail["actual_label"] == "MATCH")),
        ("MATCH_TO_SAFER_REVIEW",
         (detail["r0_decision_label"] == "MATCH")
         & (detail["ga_decision_label"] == "REVIEW")
         & (detail["actual_label"] == "NO_MATCH")),
        ("GA_WORSENED_ROW", detail["ga_effect"] == "WORSENED"),
    ]
    rows = []
    for case, mask in cases:
        subset = detail.loc[mask].sort_values("cost_delta_ga_minus_r0")
        if subset.empty:
            continue
        row = subset.iloc[-1] if case == "GA_WORSENED_ROW" else subset.iloc[0]
        row = row.copy()
        row["comparison_case"] = case
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    columns = ["comparison_case", *[column for column in out.columns if column != "comparison_case"]]
    return out.loc[:, columns].reset_index(drop=True)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    detail, summary = build_detail()
    examples = branch_examples(detail)
    comparisons = changed_examples(detail)
    transitions = (
        detail.groupby(["r0_decision_label", "ga_decision_label", "actual_label"], dropna=False)
        .agg(
            rows=("row_id", "size"),
            r0_cost=("r0_row_cost", "sum"),
            ga_cost=("row_total_cost", "sum"),
            cost_delta_ga_minus_r0=("cost_delta_ga_minus_r0", "sum"),
        )
        .reset_index()
        .sort_values("cost_delta_ga_minus_r0")
    )
    run_input = detail.loc[detail["entered_run_ga"], [
        "row_id", "profile_id_a", "profile_id_b", "probability", "name_similarity",
        "actual_code", "actual_label",
    ]]
    objective = summary["cost_reconciliation"]["objective_validation_cost"]
    fixed_cost = (
        summary["cost_reconciliation"]["fixed_blocking_missed_fn"] * W_FN
        + summary["cost_reconciliation"]["fixed_exact_tier_fp"] * W_FP
    )
    reported = summary["cost_reconciliation"]["reported_full_validation_cost"]
    if abs((objective + fixed_cost) - reported) > 1e-9:
        raise AssertionError("Exported row costs do not reconcile to the recorded validation cost")
    detail.to_csv(OUTPUT_DIR / "r1_ga_validation_chromosome_detail.csv", index=False)
    run_input.to_csv(OUTPUT_DIR / "r1_ga_run_input.csv", index=False)
    examples.to_csv(OUTPUT_DIR / "r1_ga_branch_examples.csv", index=False)
    comparisons.to_csv(OUTPUT_DIR / "r1_ga_changed_examples.csv", index=False)
    transitions.to_csv(OUTPUT_DIR / "r1_ga_transition_summary.csv", index=False)
    (OUTPUT_DIR / "r1_ga_validation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
