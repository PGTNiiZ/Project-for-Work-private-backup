from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)


def box(ax, xy, wh, text, color="#E8F0FE", edge="#315A8A", fontsize=9):
    x, y = xy; w, h = wh
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.015,rounding_size=0.02", fc=color, ec=edge, lw=1.2)
    ax.add_patch(patch); ax.text(x+w/2, y+h/2, text, ha="center", va="center", fontsize=fontsize)
    return patch


def arrow(ax, start, end, color="#444444"):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=11, lw=1.1, color=color))


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


fig, ax = plt.subplots(figsize=(7.1, 3.0)); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
steps = [(0.02, "Profiles\n3 platforms"), (0.20, "Candidate\nGeneration"), (0.38, "Pair Features\n17 handcrafted\n+ MiniLM cosine"), (0.59, "Gradient\nBoosting"), (0.77, "Isotonic\nCalibration")]
for x, label in steps: box(ax, (x, .62), (.16 if x != .38 else .19, .18), label, fontsize=7.2)
for left, right in zip(steps, steps[1:]):
    x1 = left[0] + (.19 if left[0] == .38 else .16); x2 = right[0]
    arrow(ax, (x1, .71), (x2, .71))
box(ax, (.40, .27), (.24, .18), "Three-Way Decision Policy", color="#FFF3CD", edge="#9A6A00")
arrow(ax, (.83, .62), (.64, .45))
for x, label, color in [(.12, "MATCH", "#DFF2E1"), (.42, "REVIEW", "#FFF3CD"), (.72, "NO_MATCH", "#F9DEDE")]:
    box(ax, (x, .02), (.16, .13), label, color=color, fontsize=9)
    arrow(ax, (.52, .27), (x+.08, .15))
save(fig, "system_pipeline")

fig, ax = plt.subplots(figsize=(7.1, 3.5)); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
roles = [("TRAIN", "Classifier fitting", .82), ("CALIBRATION", "Isotonic calibration", .62), ("POLICY_VALIDATION", "B1/B2/B3 selection", .42)]
for role, action, y in roles:
    box(ax, (.03, y), (.23, .11), role, color="#E8F0FE")
    box(ax, (.36, y), (.25, .11), action, color="#EEF6EE", edge="#397143")
    arrow(ax, (.26, y+.055), (.36, y+.055))
box(ax, (.03, .16), (.23, .11), "SEALED_TEST", color="#F9DEDE", edge="#9B3A3A")
box(ax, (.36, .16), (.20, .11), "Label-free\nprediction", color="#EEF6EE", edge="#397143", fontsize=7.5)
box(ax, (.63, .16), (.12, .11), "FREEZE", color="#FFF3CD", edge="#9A6A00")
box(ax, (.81, .16), (.17, .11), "FINAL_EVALUATION\nlabel reveal", color="#F9DEDE", edge="#9B3A3A", fontsize=8)
arrow(ax, (.26, .215), (.36, .215)); arrow(ax, (.56, .215), (.63, .215)); arrow(ax, (.75, .215), (.81, .215))
ax.text(.77, .88, "ZERO ENTITY OVERLAP", ha="center", fontsize=10, weight="bold", color="#9B3A3A")
ax.text(.77, .72, "PRE-FINAL TEST LABEL READS = 0", ha="center", fontsize=9.5, weight="bold", color="#9B3A3A")
ax.plot([.70, .70], [.33, .66], ls="--", lw=1.2, color="#9B3A3A")
ax.text(.72, .49, "sealed boundary", rotation=90, va="center", fontsize=8, color="#9B3A3A")
save(fig, "leakage_safe_design")
