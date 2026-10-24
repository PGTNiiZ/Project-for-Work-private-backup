from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

OUT = Path(__file__).parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# Restrained, grayscale-safe visual system shared by all figures.
INK = "#263238"
MUTED = "#6f787d"
GRID = "#d9dddf"
MODEL = "#506b7b"
MODEL_LIGHT = "#edf2f4"
DECISION = "#8a725d"
DECISION_LIGHT = "#f4f0ec"
OPTIM = "#607970"
OPTIM_LIGHT = "#edf2f0"
WHITE = "#ffffff"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 7.5,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    }
)


def rounded(ax, xy, width, height, text, *, edge=INK, face=WHITE, size=7.0, weight="normal", radius=0.03, lw=0.8):
    x, y = xy
    patch = FancyBboxPatch(
        (x, y), width, height,
        boxstyle=f"round,pad=0.006,rounding_size={radius}",
        facecolor=face, edgecolor=edge, linewidth=lw,
    )
    ax.add_patch(patch)
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=size, weight=weight)
    return patch


def flow(ax, start, end, *, color=INK, lw=0.8, connectionstyle="arc3"):
    ax.add_patch(
        FancyArrowPatch(
            start, end, arrowstyle="-|>", mutation_scale=6.5,
            linewidth=lw, color=color, connectionstyle=connectionstyle,
            shrinkA=1.2, shrinkB=1.2,
        )
    )


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure — one small, secondary, compact pipeline orientation diagram.
# The only conceptual figure retained in the manuscript.
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(3.45, 1.05))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

stages = [
    ("Candidate\ngeneration", MODEL, MODEL_LIGHT),
    ("Multi-feature\nscoring", MODEL, MODEL_LIGHT),
    ("Calibration", MODEL, WHITE),
    ("Policy\ndecision", DECISION, DECISION_LIGHT),
]
n = len(stages)
w, gap, h = 0.205, 0.028, 0.46
x0 = 0.012
for i, (label, edge, face) in enumerate(stages):
    x = x0 + i * (w + gap)
    rounded(ax, (x, 0.30), w, h, label, edge=edge, face=face, size=6.3, weight="normal", radius=0.05, lw=0.8)
    if i < n - 1:
        flow(ax, (x + w + 0.004, 0.53), (x + w + gap - 0.004, 0.53), color=MUTED, lw=0.75)

ax.text(x0 + n * (w + gap) - gap + 0.02, 0.53, "match / review /\nno match", fontsize=5.9, va="center", color=INK)
ax.text(0.5, 0.11, "calibrated evidence is acted on under a three-way operating policy", fontsize=5.6, color=MUTED, ha="center")

save(fig, "system_pipeline")


# ---------------------------------------------------------------------------
# Figure — empirical model-family development screen (real repository data).
# Source: train_data/stage7_8_rebuilt_experiment_tuned/best_run.json
# Development-stage evidence only; not authoritative V2 test evidence.
# ---------------------------------------------------------------------------
families = ["Gradient\nBoosting", "Random\nForest", "Logistic\nregression"]
val_ap = [0.9782547323557295, 0.9768579815647073, 0.9403920109449398]
val_auc = [0.9701167998667455, 0.9681406525857952, 0.9197338781804767]
fam_colors = [MODEL, MUTED, MUTED]

fig, ax = plt.subplots(figsize=(3.45, 1.95))
y = np.arange(len(families))
bar_h = 0.32

ax.barh(y + bar_h / 2 + 0.02, val_ap, height=bar_h, color=[MODEL_LIGHT if c == MODEL else "#eceeef" for c in fam_colors],
        edgecolor=[MODEL if c == MODEL else MUTED for c in fam_colors], linewidth=0.9, zorder=2)
ax.barh(y - bar_h / 2 - 0.02, val_auc, height=bar_h, color=WHITE,
        edgecolor=[MODEL if c == MODEL else MUTED for c in fam_colors], linewidth=0.9, hatch="////", zorder=2)

for i, v in enumerate(val_ap):
    ax.text(v + 0.004, y[i] + bar_h / 2 + 0.02, f"{v:.3f}", va="center", fontsize=6.0)
for i, v in enumerate(val_auc):
    ax.text(v + 0.004, y[i] - bar_h / 2 - 0.02, f"{v:.3f}", va="center", fontsize=6.0)

ax.set_yticks(y, families, fontsize=6.6)
ax.set_xlim(0.90, 1.01)
ax.set_xlabel("validation score", fontsize=6.8)
ax.set_xticks([0.90, 0.94, 0.98])
ax.tick_params(axis="both", labelsize=6.3, length=2.5, width=0.6)
ax.spines[["top", "right"]].set_visible(False)
ax.spines["left"].set_color(GRID)
ax.spines["bottom"].set_color(GRID)
ax.grid(axis="x", color=GRID, linewidth=0.55, zorder=0)
ax.invert_yaxis()

ax.legend(
    handles=[
        Rectangle((0, 0), 1, 1, facecolor=MODEL_LIGHT, edgecolor=MODEL, linewidth=0.8, label="average precision"),
        Rectangle((0, 0), 1, 1, facecolor=WHITE, edgecolor=MUTED, linewidth=0.8, hatch="////", label="AUC"),
    ],
    loc="lower center", bbox_to_anchor=(0.5, -0.42), ncol=2, frameon=False, fontsize=5.8, handlelength=1.2, handleheight=1.0,
)

fig.tight_layout()
save(fig, "model_family_development")


# ---------------------------------------------------------------------------
# Figure — candidate-generation retrieval ceiling (real repository data).
# Source: authoritative_run_v2 candidate-generation accounting (Section III.A).
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(3.45, 1.55))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# Proportional single-row stacked bar of the 29,243 cross-platform positives.
covered, missed = 25931, 3312
total = covered + missed
bar_x0, bar_x1, bar_y, bar_h = 0.02, 0.98, 0.46, 0.20
covered_w = (bar_x1 - bar_x0) * covered / total
ax.add_patch(FancyBboxPatch((bar_x0, bar_y), covered_w, bar_h, boxstyle="round,pad=0,rounding_size=0.006",
                             facecolor=MODEL_LIGHT, edgecolor=MODEL, linewidth=0.9))
ax.add_patch(FancyBboxPatch((bar_x0 + covered_w, bar_y), (bar_x1 - bar_x0) - covered_w, bar_h,
                             boxstyle="round,pad=0,rounding_size=0.006",
                             facecolor=DECISION_LIGHT, edgecolor=DECISION, linewidth=0.9))

ax.text(bar_x0 + covered_w / 2, bar_y + bar_h / 2, f"covered\n{covered:,}", fontsize=6.1, ha="center", va="center", color=MODEL, weight="bold")
ax.text(bar_x0 + covered_w + ((bar_x1 - bar_x0) - covered_w) / 2, bar_y + bar_h / 2, f"missed\n{missed:,}", fontsize=6.0, ha="center", va="center", color=DECISION, weight="bold")

ax.text(0.5, 0.80, f"{total:,} cross-platform positives", fontsize=6.6, ha="center", weight="bold")
ax.text(0.5, 0.30, "candidate generation from 449,149,239 possible pairs", fontsize=5.9, ha="center", color=MUTED)
ax.text(0.5, 0.12, "retrieval recall 88.6742%  ·  a downstream scorer cannot recover a missed pair", fontsize=5.8, ha="center", color=INK)

save(fig, "candidate_ceiling")


# ---------------------------------------------------------------------------
# Figure — controlled authoritative results (real V2 evidence). Main empirical
# figure: connected point/interval plots across the feature and policy stages.
# ---------------------------------------------------------------------------
labels = ["17-feature", "+ MiniLM", "Tuned", "Sobol", "Genetic"]
x = np.arange(len(labels))
f1 = np.array([0.8494361, 0.8509648, 0.8910374, 0.8901489, 0.8902928])
f1_sd = np.array([0.0256980, 0.0235251, 0.0024151, 0.0016020, 0.0014811])
u = np.array([2351.97, 2364.20, 1864.57, 1860.03, 1858.23])
u_sd = np.array([212.33, 212.01, 45.88, 27.07, 29.96])
point_colors = [MODEL, MODEL, DECISION, OPTIM, OPTIM]
markers = ["o", "s", "D", "s", "o"]

fig, axes = plt.subplots(2, 1, figsize=(3.45, 2.68), gridspec_kw={"hspace": 0.42})

for ax in axes:
    ax.axvspan(-0.35, 1.35, color=MODEL_LIGHT, alpha=0.75, zorder=0)
    ax.axvspan(1.65, 4.35, color=OPTIM_LIGHT, alpha=0.70, zorder=0)
    ax.axvline(1.5, color=GRID, linewidth=0.8, linestyle=(0, (2, 2)), zorder=0)
    ax.grid(axis="y", color=GRID, linewidth=0.55, zorder=0)
    ax.set_xlim(-0.35, 4.35)
    ax.set_xticks(x, labels, fontsize=6.4)
    ax.tick_params(axis="x", length=0, pad=3)
    ax.tick_params(axis="y", labelsize=6.3, length=2.5, width=0.6)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.spines["bottom"].set_linewidth(0.7)

axes[0].plot(x, f1, color=MUTED, linewidth=0.75, zorder=2)
axes[1].plot(x, u, color=MUTED, linewidth=0.75, zorder=2)
for i in range(len(x)):
    axes[0].errorbar(x[i], f1[i], yerr=f1_sd[i], fmt="none", ecolor="#a8afb3", elinewidth=0.7, capsize=2.2, capthick=0.7, zorder=1)
    axes[1].errorbar(x[i], u[i], yerr=u_sd[i], fmt="none", ecolor="#a8afb3", elinewidth=0.7, capsize=2.2, capthick=0.7, zorder=1)
    axes[0].scatter(x[i], f1[i], s=24, marker=markers[i], facecolor=WHITE if i in (0, 3) else point_colors[i], edgecolor=point_colors[i], linewidth=1.0, zorder=3)
    axes[1].scatter(x[i], u[i], s=24, marker=markers[i], facecolor=WHITE if i in (0, 3) else point_colors[i], edgecolor=point_colors[i], linewidth=1.0, zorder=3)

axes[0].set_ylim(0.815, 0.905)
axes[0].set_yticks([0.82, 0.85, 0.88, 0.90])
axes[0].set_ylabel("workflow F1  ↑", fontsize=6.7, weight="bold")
axes[0].text(-0.32, 0.902, "a", fontsize=7.2, weight="bold")
axes[1].set_ylim(1500, 2650)
axes[1].set_yticks([1600, 2000, 2400, 2600])
axes[1].set_ylabel("objective U  ↓", fontsize=6.7, weight="bold")
axes[1].text(-0.32, 2615, "b", fontsize=7.2, weight="bold")

axes[0].text(0.5, 0.908, "model / feature", fontsize=5.9, weight="bold", color=MODEL, ha="center", va="bottom")
axes[0].text(3.0, 0.908, "policy", fontsize=5.9, weight="bold", color=OPTIM, ha="center", va="bottom")
axes[0].annotate("+0.0015", xy=(1, f1[1]), xytext=(0.50, 0.858), fontsize=5.8, color=MODEL, ha="center", arrowprops=dict(arrowstyle="-", color=MODEL, lw=0.55))
axes[0].annotate("+0.0401", xy=(2, f1[2]), xytext=(1.52, 0.885), fontsize=5.8, color=DECISION, ha="center", arrowprops=dict(arrowstyle="-", color=DECISION, lw=0.55))
axes[0].text(3.5, 0.896, "Δ ≈ +0.00014", fontsize=5.7, color=OPTIM, ha="center")
axes[1].text(3.5, 1930, "ΔU = −1.8", fontsize=5.8, color=OPTIM, ha="center")
axes[1].plot([3, 4], [1900, 1900], color=OPTIM, linewidth=0.6)
axes[1].text(3.5, 1540, "same 4-D policy · equal 12k budget", fontsize=5.5, color=MUTED, ha="center")

save(fig, "controlled_results")
