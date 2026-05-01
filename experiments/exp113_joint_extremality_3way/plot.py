"""Generate scatter figure for exp113 joint extremality test."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent.parent
RECEIPT = ROOT / "results" / "experiments" / "exp113_joint_extremality_3way" / "exp113_joint_extremality_3way.json"

d = json.load(open(RECEIPT, encoding="utf-8"))
metrics = d["metrics_per_tradition"]
trads = list(metrics.keys())
labels = {
    "quran": "Quran",
    "hebrew_tanakh": "Hebrew Tanakh\n(Psalm 78)",
    "greek_nt": "Greek NT\n(Mark 1)",
    "pali": "Pāli\n(DN 1)",
    "avestan_yasna": "Avestan\n(Yasna 28)",
}

f55 = [metrics[t]["F55_safety_per_char"] for t in trads]
pmax = [metrics[t]["F63_p_max"] for t in trads]
lc2 = [metrics[t]["LC2_z"] for t in trads]

# 3-panel figure: F55 vs F63_p_max, F55 vs LC2, F63_p_max vs LC2
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

panels = [
    (f55, pmax, "F55 safety / char", "F63 p_max", "F55 × F63 (ρ=+0.30, near-indep.)"),
    (f55, lc2, "F55 safety / char", "LC2 z (path-min)", "F55 × LC2 (ρ=−0.20, near-indep.)"),
    (pmax, lc2, "F63 p_max", "LC2 z (path-min)", "F63 × LC2 (ρ=+0.70, correlated)"),
]

colors = ["red" if t == "quran" else "steelblue" for t in trads]
sizes = [200 if t == "quran" else 100 for t in trads]

for ax, (x, y, xl, yl, title) in zip(axes, panels):
    ax.scatter(x, y, c=colors, s=sizes, edgecolors="black", linewidths=1, zorder=3)
    for xi, yi, t in zip(x, y, trads):
        offset_x, offset_y = (10, 5) if t != "quran" else (15, -25)
        ax.annotate(labels[t], (xi, yi), xytext=(offset_x, offset_y), textcoords="offset points",
                    fontsize=9, fontweight=("bold" if t == "quran" else "normal"))
    ax.set_xlabel(xl, fontsize=11)
    ax.set_ylabel(yl, fontsize=11)
    ax.set_title(title, fontsize=11)
    ax.grid(True, alpha=0.3)

fig.suptitle(
    "exp113 — Joint extremality of the Quran on three structural axes\n"
    f"Quran is rank 1 on F55 + F63 (perm-p = 0.041); rank 3 on LC2 (Tanakh & NT beat it)",
    fontsize=12,
)
fig.tight_layout()

out_path = RECEIPT.parent / "fig_joint_extremality_pairwise.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"Saved: {out_path.relative_to(ROOT)}")
