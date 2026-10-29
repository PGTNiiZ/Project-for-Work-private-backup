"""Generate reproducible figures for the final Identity Resolution report."""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FuncFormatter

from identity_resolution.core.business_cost import CRM_COST_WEIGHTS


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "manuscript" / "figures"
EVALUATION = ROOT / "artifacts" / "evaluation" / "current_model_evaluation.json"
DECISION_SUMMARY = ROOT / "artifacts" / "decisioning" / "analysis_decision_matrix" / "summary.json"
FEATURE_AWARE = ROOT / "artifacts" / "decisioning" / "feature_aware_ga" / "automated_20260831_final"
FULL_FEATURE_AWARE = ROOT / "artifacts" / "decisioning" / "feature_aware_ga" / "full_2m"
MODEL_COMPARISON = ROOT / "pub_multi" / "res" / "model_cmp.csv"
FEATURE_IMPORTANCE = ROOT / "pub_multi" / "res" / "feat_imp.csv"
BLOCKING = ROOT / "pub_multi" / "res" / "blocking.csv"
TIERS = ROOT / "pub_multi" / "res" / "tiers.csv"
R_SERIES = ROOT / "experiments" / "r0_r5_summary_tidy.csv"
PRIVACY = ROOT / "experiments" / "r4_privacy_tradeoff.json"
NAME_RUNS = ROOT / "artifacts" / "evaluation" / "name_similarity"
PROFILES = ROOT / "data_for_project" / "normalized_profiles_with_profile_id.csv"
THAI_FONT = Path("/System/Library/Fonts/Supplemental/Thonburi.ttc")

COLORS = {
    "navy": "#17324D",
    "blue": "#2878B5",
    "teal": "#2A9D8F",
    "gold": "#E9C46A",
    "orange": "#F4A261",
    "red": "#D1495B",
    "gray": "#7A8793",
    "light": "#E8EEF2",
}


def setup() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "figure.dpi": 130,
        "savefig.dpi": 180,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 14,
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
        "axes.titlepad": 14,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def save(figure: plt.Figure, filename: str) -> None:
    figure.tight_layout()
    figure.savefig(OUTPUT / filename, bbox_inches="tight")
    plt.close(figure)


def percent_axis(value: float, _position: int) -> str:
    return f"{value:.0%}"


def figure_end_to_end_architecture() -> None:
    """Render a simple top-to-bottom view of the complete identity workflow."""
    font = FontProperties(fname=str(THAI_FONT)) if THAI_FONT.exists() else FontProperties()
    figure, axis = plt.subplots(figsize=(10, 15))
    axis.set_xlim(0, 10)
    axis.set_ylim(0, 15)
    axis.axis("off")

    def box(x: float, y: float, width: float, height: float, title: str, detail: str = "", color: str = "#2878B5") -> None:
        axis.add_patch(patches.Rectangle((x, y), width, height, facecolor="white", edgecolor=color, linewidth=1.5))
        axis.text(x + width / 2, y + height * (0.62 if detail else 0.5), title, ha="center", va="center", fontsize=10, color=COLORS["navy"], fontproperties=font)
        if detail:
            axis.text(x + width / 2, y + height * 0.27, detail, ha="center", va="center", fontsize=7.6, color="#52616b", fontproperties=font)

    def diamond(x: float, y: float, width: float, height: float, title: str) -> None:
        points = [(x + width / 2, y + height), (x + width, y + height / 2), (x + width / 2, y), (x, y + height / 2)]
        axis.add_patch(patches.Polygon(points, closed=True, facecolor="#fff3df", edgecolor=COLORS["orange"], linewidth=1.6))
        axis.text(x + width / 2, y + height / 2, title, ha="center", va="center", fontsize=9, color=COLORS["navy"], fontproperties=font)

    def arrow(start: tuple[float, float], end: tuple[float, float], label: str = "", curve: float = 0.0) -> None:
        axis.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "-|>", "color": COLORS["blue"], "lw": 1.25, "connectionstyle": f"arc3,rad={curve}"})
        if label:
            axis.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.08, label, ha="center", fontsize=7, color="#52616b", fontproperties=font, bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.5})

    def routed_arrow(points: list[tuple[float, float]], label: str = "") -> None:
        xs, ys = zip(*points)
        axis.plot(xs[:-1], ys[:-1], color=COLORS["blue"], linewidth=1.25)
        axis.annotate("", xy=points[-1], xytext=points[-2], arrowprops={"arrowstyle": "-|>", "color": COLORS["blue"], "lw": 1.25})
        if label:
            axis.text(points[1][0], points[1][1] + 0.08, label, ha="center", fontsize=7, color="#52616b", fontproperties=font, bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.5})

    center_x, width, height = 3.65, 2.7, 0.62
    main_nodes = [
        (13.75, "Raw social profiles", "Twitter | Google+ | Instagram", COLORS["blue"]),
        (12.65, "Clean & normalize", "IDs | text | URL | image", COLORS["blue"]),
        (11.55, "Candidate retrieval", "exact + blocking keys", COLORS["blue"]),
        (10.45, "Pair feature computation", "name | bio | URL | image | style", COLORS["blue"]),
        (9.35, "Entity-aware split", "train | validation | test", COLORS["blue"]),
        (8.25, "Train pair model", "Gradient Boosting on train", COLORS["teal"]),
        (7.15, "Raw probability", "model.predict_proba", COLORS["teal"]),
        (6.05, "Isotonic calibration", "fit on validation", COLORS["teal"]),
        (4.95, "Frozen calibrated score", "model + scaler + calibrator", COLORS["teal"]),
    ]
    for y, title, detail, color in main_nodes:
        box(center_x, y, width, height, title, detail, color)
    for (upper_y, *_), (lower_y, *__) in zip(main_nodes, main_nodes[1:]):
        arrow((5.0, upper_y), (5.0, lower_y + height))

    # Side branches that support the main path.
    box(7.15, 12.05, 2.4, 0.62, "Ground truth labels", "user_folder + label audit", COLORS["gray"])
    arrow((6.35, 12.96), (7.15, 12.36), curve=0.18)
    arrow((7.15, 12.24), (6.35, 9.66), "labels", curve=0.18)
    box(0.45, 11.55, 2.45, 0.62, "Exact match tier", "username / URL exact", COLORS["gray"])
    arrow((3.65, 12.96), (2.9, 11.86), curve=-0.18)

    box(0.45, 4.95, 2.45, 0.62, "Pair-model benchmark", "binary threshold = 0.35", COLORS["orange"])
    arrow((3.65, 5.26), (2.9, 5.26), "evaluation only")
    box(7.15, 4.95, 2.4, 0.62, "Evidence cache", "score + availability mask", COLORS["orange"])
    arrow((6.35, 5.26), (7.15, 5.26))

    diamond(4.0, 3.65, 2.0, 0.9, "GA decision policy")
    arrow((5.0, 4.95), (5.0, 4.55), "frozen score")
    arrow((7.15, 5.05), (5.95, 4.29), "evidence", curve=0.12)

    box(1.0, 2.65, 2.15, 0.62, "MATCH edges", "auto-match + exact tier", COLORS["red"])
    box(3.93, 2.65, 2.15, 0.62, "Human review", "manual decision queue", COLORS["orange"])
    box(6.85, 2.65, 2.15, 0.62, "NO_MATCH", "rejected pair", COLORS["gray"])
    arrow((4.25, 3.87), (2.08, 3.27), "MATCH", curve=0.12)
    arrow((5.0, 3.65), (5.0, 3.27), "REVIEW")
    arrow((5.75, 3.87), (7.93, 3.27), "NO_MATCH", curve=-0.12)
    routed_arrow([(1.67, 11.55), (0.20, 11.15), (0.20, 3.05), (1.0, 2.96)], "exact bypass")

    box(1.0, 1.55, 2.15, 0.62, "Entity graph", "Union-Find + merge safety", COLORS["red"])
    box(3.93, 1.55, 2.15, 0.62, "Unified profile", "canonical customer identity", COLORS["red"])
    box(6.85, 1.55, 2.15, 0.62, "CRM & monitoring", "Customer 360 | drift | rollback", COLORS["red"])
    arrow((2.08, 2.65), (2.08, 2.17))
    arrow((3.15, 1.86), (3.93, 1.86))
    arrow((6.08, 1.86), (6.85, 1.86))

    axis.text(5.0, 14.72, "IDENTITY RESOLUTION: END-TO-END FLOW", ha="center", fontsize=18, fontweight="bold", color=COLORS["navy"])
    axis.text(5.0, 14.40, "Data clean -> model training -> calibration -> GA decision -> entity -> CRM", ha="center", fontsize=9.5, color="#52616b")
    axis.text(5.0, 0.92, "GA changes the decision rule, not the frozen model or calibrated probability", ha="center", fontsize=8.5, color=COLORS["red"], fontproperties=font)
    figure.savefig(OUTPUT / "00_end_to_end_architecture.png", bbox_inches="tight", facecolor="white")
    plt.close(figure)


def write_data_audit() -> None:
    frame = pd.read_csv(PROFILES, keep_default_na=False, low_memory=False)
    profile_row_id = pd.to_numeric(frame["profile_row_id"], errors="coerce")
    profile_id = pd.to_numeric(frame["profile_id"], errors="coerce")
    valid = frame[profile_row_id.notna() & profile_id.notna()].copy()
    all_pairs = 0
    cross_platform_pairs = 0
    for _, group in valid.groupby("user_folder"):
        platforms = group["platform"].astype(str).str.lower().tolist()
        for left, right in combinations(platforms, 2):
            all_pairs += 1
            cross_platform_pairs += int(left != right)
    field_nonempty = {}
    for field in ("userName", "fullName", "bio", "location", "externalUrl_clean", "external_domain"):
        clean = frame[field].astype(str).str.strip()
        available = ~clean.isin(("", "nan", "None"))
        field_nonempty[field] = {"count": int(available.sum()), "coverage": float(available.mean())}
    payload = {
        "source": str(PROFILES.relative_to(ROOT)),
        "input_rows": int(len(frame)),
        "eligible_rows": int(len(valid)),
        "excluded_invalid_id_rows": int(len(frame) - len(valid)),
        "unique_entities": int(valid["user_folder"].astype(str).replace("", pd.NA).nunique()),
        "platform_counts_input": frame["platform"].astype(str).str.lower().value_counts().to_dict(),
        "platform_counts_eligible": valid["platform"].astype(str).str.lower().value_counts().to_dict(),
        "ground_truth_pairs_all": all_pairs,
        "ground_truth_pairs_cross_platform": cross_platform_pairs,
        "ground_truth_pairs_same_platform": all_pairs - cross_platform_pairs,
        "field_nonempty": field_nonempty,
    }
    (ROOT / "manuscript" / "report_data_audit.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def figure_search_space() -> None:
    blocking = pd.read_csv(BLOCKING).set_index("item")["value"]
    stages = ["All cross-platform\npairs", "Blocked candidates\n+ exact tier", "Ground-truth pairs\ncovered"]
    values = [
        float(blocking["all_cross_platform_pairs"]),
        float(blocking["candidate_pairs_for_model"] + blocking["exact_match_pairs"]),
        float(blocking["ground_truth_positive_pairs"] * blocking["ground_truth_coverage_pct"] / 100.0),
    ]
    figure, axis = plt.subplots(figsize=(9, 4.8))
    bars = axis.bar(stages, values, color=[COLORS["navy"], COLORS["blue"], COLORS["teal"]], width=0.62)
    axis.set_yscale("log")
    axis.set_ylabel("Number of pairs (log scale)")
    axis.set_title("Candidate Retrieval Reduces 449M Comparisons to 2.09M")
    axis.grid(axis="y", color=COLORS["light"], linewidth=0.8)
    for bar, value in zip(bars, values):
        axis.text(bar.get_x() + bar.get_width() / 2, value * 1.18, f"{value:,.0f}", ha="center", fontweight="bold")
    axis.text(0.5, 0.88, f"{blocking['search_space_reduction_pct']:.2f}% search-space reduction", transform=axis.transAxes, ha="center", color=COLORS["red"], fontweight="bold")
    save(figure, "01_search_space_funnel.png")


def figure_model_comparison() -> None:
    frame = pd.read_csv(MODEL_COMPARISON)
    labels = frame["name"].str.replace("strict_noleak_", "", regex=False).str.replace("_report", "", regex=False)
    positions = np.arange(len(frame))
    width = 0.25
    figure, axis = plt.subplots(figsize=(11, 5.5))
    axis.bar(positions - width, frame["test_precision"], width, label="Precision", color=COLORS["navy"])
    axis.bar(positions, frame["test_recall"], width, label="Recall", color=COLORS["teal"])
    axis.bar(positions + width, frame["test_f1"], width, label="F1", color=COLORS["orange"])
    axis.set_xticks(positions, labels, rotation=22, ha="right")
    axis.set_ylim(0.7, 1.01)
    axis.set_ylabel("Score")
    axis.set_title("Pair-Model Performance Across Model Families")
    axis.grid(axis="y", color=COLORS["light"])
    axis.legend(ncol=3, frameon=False, loc="lower left")
    save(figure, "02_model_comparison.png")


def figure_feature_importance() -> None:
    frame = pd.read_csv(FEATURE_IMPORTANCE).nlargest(15, "importance").sort_values("importance")
    figure, axis = plt.subplots(figsize=(9, 6.4))
    colors = [COLORS["teal"] if "image" not in name else COLORS["orange"] for name in frame["feature"]]
    axis.barh(frame["feature"], frame["importance"], color=colors)
    axis.set_xlabel("Normalized feature importance")
    axis.set_title("Top 15 Features in the 41-Feature Production Model")
    axis.grid(axis="x", color=COLORS["light"])
    save(figure, "03_feature_importance.png")


def figure_platform_performance() -> None:
    payload = json.loads(EVALUATION.read_text(encoding="utf-8"))["test"]["by_platform_pair"]
    frame = pd.DataFrame(payload).T
    labels = [name.replace("googleplus", "Google+").replace("instagram", "Instagram").replace("twitter", "Twitter") for name in frame.index]
    metrics = ["precision", "recall", "f1"]
    matrix = frame[metrics].to_numpy()
    figure, axis = plt.subplots(figsize=(7.8, 4.5))
    image = axis.imshow(matrix, cmap="YlGnBu", vmin=0.88, vmax=0.97, aspect="auto")
    axis.set_xticks(range(len(metrics)), [metric.title() for metric in metrics])
    axis.set_yticks(range(len(labels)), labels)
    axis.set_title("Test Performance by Platform Pair")
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            axis.text(column_index, row_index, f"{matrix[row_index, column_index]:.3f}", ha="center", va="center", color="white" if matrix[row_index, column_index] > 0.93 else COLORS["navy"], fontweight="bold")
    figure.colorbar(image, ax=axis, fraction=0.035, pad=0.04)
    save(figure, "04_platform_pair_performance.png")


def figure_difficulty_slices() -> None:
    slices = json.loads(EVALUATION.read_text(encoding="utf-8"))["test"]["by_slice"]
    names = list(slices)
    recall = [slices[name]["recall"] for name in names]
    positives = [slices[name]["n_pos"] for name in names]
    figure, axis = plt.subplots(figsize=(8.6, 4.8))
    bars = axis.bar(names, recall, color=[COLORS["teal"], COLORS["gold"], COLORS["red"]], width=0.58)
    axis.set_ylim(0, 1.05)
    axis.yaxis.set_major_formatter(FuncFormatter(percent_axis))
    axis.set_ylabel("Recall")
    axis.set_title("Recall Collapses as Lexical Evidence Weakens")
    axis.grid(axis="y", color=COLORS["light"])
    for bar, score, count in zip(bars, recall, positives):
        axis.text(bar.get_x() + bar.get_width() / 2, score + 0.035, f"{score:.1%}\n(n={count:,})", ha="center", fontweight="bold")
    save(figure, "05_difficulty_slice_recall.png")


def figure_decision_tiers() -> None:
    frame = pd.read_csv(TIERS)
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    axes[0].bar(frame["tier"].str.upper(), frame["count"], color=[COLORS["teal"], COLORS["blue"], COLORS["gold"]])
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Pairs (log scale)")
    axes[0].set_title("Decision-Tier Volume")
    axes[0].grid(axis="y", color=COLORS["light"])
    for index, row in frame.iterrows():
        axes[0].text(index, row["count"] * 1.15, f"{int(row['count']):,}", ha="center", fontweight="bold")
    axes[1].bar(frame["tier"].str.upper(), frame["precision"], color=[COLORS["teal"], COLORS["blue"], COLORS["gold"]])
    axes[1].set_ylim(0, 1.05)
    axes[1].yaxis.set_major_formatter(FuncFormatter(percent_axis))
    axes[1].set_title("Precision by Decision Tier")
    axes[1].grid(axis="y", color=COLORS["light"])
    for index, row in frame.iterrows():
        axes[1].text(index, row["precision"] + 0.035, f"{row['precision']:.1%}", ha="center", fontweight="bold")
    save(figure, "06_decision_tiers.png")


def figure_error_taxonomy() -> None:
    summary = json.loads(DECISION_SUMMARY.read_text(encoding="utf-8"))
    categories = ["Blocking\nmiss", "Scored\nfalse negative", "Auto-match\nfalse positive", "Review\nfalse positive"]
    values = [3316, summary["fn_nomatch_but_actually_yes"]["n"], summary["fp_match_but_actually_no"]["n"], summary["review_actual_nomatch"]["n"]]
    figure, axis = plt.subplots(figsize=(9, 4.8))
    bars = axis.bar(categories, values, color=[COLORS["red"], COLORS["orange"], COLORS["navy"], COLORS["gold"]], width=0.62)
    axis.set_yscale("log")
    axis.set_ylabel("Pairs (log scale)")
    axis.set_title("Operational Error and Workload Taxonomy")
    axis.grid(axis="y", color=COLORS["light"])
    for bar, value in zip(bars, values):
        axis.text(bar.get_x() + bar.get_width() / 2, value * 1.18, f"{value:,}", ha="center", fontweight="bold")
    save(figure, "07_error_taxonomy.png")


def figure_r_series() -> None:
    frame = pd.read_csv(R_SERIES)
    test = frame[(frame["split"] == "test") & (frame["exp"].isin(["R0", "R1", "R2", "R3"]))].drop_duplicates("exp")
    positions = np.arange(len(test))
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    bars = axes[0].bar(test["exp"], test["F1"], color=[COLORS["gray"], COLORS["blue"], COLORS["gold"], COLORS["teal"]])
    axes[0].set_ylim(0.70, 0.86)
    axes[0].set_ylabel("Test F1")
    axes[0].set_title("R0-R3 Accuracy Progression")
    axes[0].grid(axis="y", color=COLORS["light"])
    for bar, value in zip(bars, test["F1"]):
        axes[0].text(bar.get_x() + bar.get_width() / 2, value + 0.006, f"{value:.4f}", ha="center", fontweight="bold")
    axes[1].bar(positions, test["REVIEW"], color=[COLORS["gray"], COLORS["blue"], COLORS["gold"], COLORS["teal"]])
    axes[1].set_xticks(positions, test["exp"])
    axes[1].set_ylabel("Review pairs")
    axes[1].set_title("Manual-Review Burden")
    axes[1].grid(axis="y", color=COLORS["light"])
    for position, value in zip(positions, test["REVIEW"]):
        axes[1].text(position, value + max(test["REVIEW"]) * 0.025, f"{int(value):,}", ha="center", fontweight="bold")
    save(figure, "08_r_series_progression.png")


def figure_feature_aware_ga() -> None:
    leaderboard = pd.read_csv(FEATURE_AWARE / "selector_leaderboard.csv").sort_values("validation_cost", ascending=False)
    coverage = pd.read_csv(FEATURE_AWARE / "coverage_reliability.csv")
    figure, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    guard_colors = [COLORS["red"] if guard == "name" else COLORS["teal"] if guard == "bio" else COLORS["blue"] for guard in leaderboard["guard"]]
    axes[0].barh(leaderboard["guard"], leaderboard["validation_cost"], color=guard_colors)
    axes[0].set_xlabel("Validation business cost")
    axes[0].set_title("Feature-Aware GA Guard Comparison")
    axes[0].grid(axis="x", color=COLORS["light"])
    for index, value in enumerate(leaderboard["validation_cost"]):
        axes[0].text(value + 5, index, f"{value:.1f}", va="center", fontweight="bold")
    axes[1].bar(coverage["group"], coverage["availability_coverage"], color=COLORS["orange"])
    axes[1].set_ylim(0, 1.05)
    axes[1].yaxis.set_major_formatter(FuncFormatter(percent_axis))
    axes[1].set_ylabel("Availability")
    axes[1].set_title("Evidence Availability on Validation")
    axes[1].tick_params(axis="x", rotation=25)
    axes[1].grid(axis="y", color=COLORS["light"])
    save(figure, "09_feature_aware_ga.png")


def figure_name_similarity_ablation() -> None:
    run_labels = {
        "N0": "Baseline",
        "N1": "Damerau",
        "N2": "Char 3-gram",
        "N3": "Token set",
        "N4": "Handle",
        "N5": "Cross-field",
        "N6": "3-gram + handle",
    }
    rows = []
    for run_id, label in run_labels.items():
        payload = json.loads((NAME_RUNS / run_id / "validation_metrics.json").read_text(encoding="utf-8"))
        values = payload["validation_metrics"]
        rows.append({"run": run_id, "label": label, "ap": values["average_precision"], "f1": values["f1"]})
    frame = pd.DataFrame(rows)
    positions = np.arange(len(frame))
    width = 0.36
    figure, axis = plt.subplots(figsize=(11, 5.2))
    axis.bar(positions - width / 2, frame["ap"], width, label="Average precision", color=COLORS["navy"])
    axis.bar(positions + width / 2, frame["f1"], width, label="F1", color=COLORS["teal"])
    axis.set_xticks(positions, [f"{row.run}\n{row.label}" for row in frame.itertuples(index=False)])
    axis.set_ylim(0.93, 0.995)
    axis.set_ylabel("Validation score")
    axis.set_title("Name-Similarity Ablation: N0-N6")
    axis.grid(axis="y", color=COLORS["light"])
    axis.legend(frameon=False, ncol=2, loc="lower right")
    save(figure, "10_name_similarity_ablation.png")


def figure_privacy_utility() -> None:
    payload = json.loads(PRIVACY.read_text(encoding="utf-8"))
    lengths = payload["L_values"]
    manual_f1 = [payload["per_L"][str(length)]["R4_manual"]["test"]["F1"] for length in lengths]
    ga_f1 = [payload["per_L"][str(length)]["R5_ga"]["test"]["F1"] for length in lengths]
    figure, axis = plt.subplots(figsize=(8.8, 4.8))
    axis.plot(lengths, manual_f1, marker="o", linewidth=2.4, label="R4 manual thresholds", color=COLORS["orange"])
    axis.plot(lengths, ga_f1, marker="o", linewidth=2.4, label="R5 GA decision", color=COLORS["teal"])
    axis.invert_xaxis()
    axis.set_xlabel("Bloom-filter length L (smaller = more collisions)")
    axis.set_ylabel("Test F1")
    axis.set_ylim(0.70, 0.85)
    axis.set_title("Privacy Representation Requires Decision Re-optimization")
    axis.grid(color=COLORS["light"])
    axis.legend(frameon=False)
    save(figure, "11_privacy_utility.png")


def figure_full_feature_aware_tradeoff() -> None:
    historical = pd.read_csv(R_SERIES)
    historical = historical[(historical["split"] == "full") & historical["exp"].isin(("R0", "R3"))].drop_duplicates("exp")
    full_result = json.loads((FULL_FEATURE_AWARE / "sealed_test_and_projection.json").read_text(encoding="utf-8"))["full_projection_metrics"]
    rows = []
    for experiment, label in (("R0", "R0 baseline"), ("R3", "R3 name GA")):
        row = historical[historical["exp"] == experiment].iloc[0]
        rows.append({
            "label": label,
            "precision": row["precision"],
            "recall": row["recall"],
            "f1": row["F1"],
            "cost": CRM_COST_WEIGHTS.cost(fp=int(row["FP"]), fn=int(row["FN"]), review=int(row["REVIEW"])),
        })
    rows.append({
        "label": "Historical style GA",
        "precision": full_result["precision"],
        "recall": full_result["recall"],
        "f1": full_result["F1"],
        "cost": CRM_COST_WEIGHTS.cost(
            fp=int(full_result["FP"]),
            fn=int(full_result["FN"]),
            review=int(full_result["REVIEW"]),
        ),
    })
    frame = pd.DataFrame(rows)
    positions = np.arange(len(frame))
    width = 0.24
    figure, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    axes[0].bar(positions - width, frame["precision"], width, label="Precision", color=COLORS["navy"])
    axes[0].bar(positions, frame["recall"], width, label="Recall", color=COLORS["orange"])
    axes[0].bar(positions + width, frame["f1"], width, label="F1", color=COLORS["teal"])
    axes[0].set_xticks(positions, frame["label"])
    axes[0].set_ylim(0.4, 1.03)
    axes[0].set_ylabel("Full-projection metric")
    axes[0].set_title("Accuracy Trade-off")
    axes[0].grid(axis="y", color=COLORS["light"])
    axes[0].legend(frameon=False, ncol=3, loc="lower left")
    cost_bars = axes[1].bar(frame["label"], frame["cost"], color=[COLORS["gray"], COLORS["blue"], COLORS["red"]])
    axes[1].set_ylabel("Business cost (lower is better)")
    axes[1].set_title("CRM-Derived Cost Trade-off")
    axes[1].grid(axis="y", color=COLORS["light"])
    for bar, value in zip(cost_bars, frame["cost"]):
        axes[1].text(bar.get_x() + bar.get_width() / 2, value + 180, f"{value:,.0f}", ha="center", fontweight="bold")
    save(figure, "12_full_feature_aware_tradeoff.png")


def main() -> None:
    setup()
    required = [PROFILES, EVALUATION, DECISION_SUMMARY, MODEL_COMPARISON, FEATURE_IMPORTANCE, BLOCKING, TIERS, R_SERIES, PRIVACY, FEATURE_AWARE / "selector_leaderboard.csv", FEATURE_AWARE / "coverage_reliability.csv", FULL_FEATURE_AWARE / "sealed_test_and_projection.json"]
    required.extend(NAME_RUNS / run_id / "validation_metrics.json" for run_id in ("N0", "N1", "N2", "N3", "N4", "N5", "N6"))
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required report artifacts: {missing}")
    write_data_audit()
    print("generated report_data_audit.json")
    generators = [
        figure_end_to_end_architecture,
        figure_search_space,
        figure_model_comparison,
        figure_feature_importance,
        figure_platform_performance,
        figure_difficulty_slices,
        figure_decision_tiers,
        figure_error_taxonomy,
        figure_r_series,
        figure_feature_aware_ga,
        figure_name_similarity_ablation,
        figure_privacy_utility,
        figure_full_feature_aware_tradeoff,
    ]
    for generator in generators:
        generator()
        print(f"generated {generator.__name__}")
    print(f"Figures written to {OUTPUT}")


if __name__ == "__main__":
    main()