"""
expE16_lc2_signature — Memorization-Optimization Signature (LC2) formal test.

Hypothesis (from `LAW_CANDIDATES_ASSESSMENT.md`): oral-ritual texts jointly
minimize memorization cost AND maximize positional variety. Formally:

    M(x) = H_cond(root_{i+1} | root_i)     (low = predictable/memorable)
    V(x) = H(verse-final letter)           (high = varied; anti-forgetting)
    L(x; λ) = M(x) − λ·V(x)                 lower = more ritual-optimized

For λ > 0, an oral text should sit at low L vs prose controls.

PRE-REGISTRATION:
  Null hypothesis:
      Quran L-rank percentile > 5 (above bottom 5%) for every λ in grid.
  Pass conditions:
      LC2_SIGNATURE: Quran median L-rank among Band-A pool ≤ 5th percentile
                     for at least 3 of 5 λ values in {0.1, 0.5, 1, 2, 5}.
      WEAK_LC2: Quran median rank ≤ 10th pct for ≥ 3 λ values.
      NULL_NO_LC2: fewer λ meet even the 10th-pct threshold.
  Seed: 42.

Uses pre-computed FEATS (`H_cond`, `EL`) at unit level — both Band-A filtered
Quran surahs and the 6-corpus Arabic Band-A control pool. No new computation.
"""
from __future__ import annotations
import json, pickle, sys, time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUTDIR = ROOT / "results" / "experiments" / "expE16_lc2_signature"
OUTDIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

SEED = 42
LAMBDAS = [0.1, 0.5, 1.0, 2.0, 5.0]
ARABIC_CTRL = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
               "ksucca", "arabic_bible", "hindawi"]
FV_ORDER = ["EL", "VL_CV", "CN", "H_cond", "T"]
BAND_A_LO, BAND_A_HI = 15, 100

t0 = time.time()
state = pickle.load(open(ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl", "rb"))["state"]
assert state["FEAT_COLS"] == FV_ORDER

def collect(name: str):
    units, feats = state["CORPORA"].get(name, []), state["FEATS"].get(name, [])
    out = []
    for u, f in zip(units, feats):
        if BAND_A_LO <= len(u.verses) <= BAND_A_HI:
            out.append({
                "corpus": name,
                "label":  getattr(u, "label", ""),
                "M":      float(f["H_cond"]),
                "V":      float(f["EL"]),
                "T":      float(f["T"]),
                "nverses": len(u.verses),
            })
    return out

quran_rows  = collect("quran")
ctrl_rows   = []
for name in ARABIC_CTRL:
    ctrl_rows.extend(collect(name))
print(f"[E16] Quran Band-A units: {len(quran_rows)}   "
      f"Arabic control Band-A units: {len(ctrl_rows)}")

# --------------------------------------------------------------- λ sweep
# For each λ, compute L per unit, rank Quran units among the full Band-A pool
rng = np.random.default_rng(SEED)
pool = quran_rows + ctrl_rows           # combined pool
n_pool = len(pool)

per_lambda = {}
for lam in LAMBDAS:
    L_pool = np.array([r["M"] - lam * r["V"] for r in pool], dtype=float)
    order = np.argsort(L_pool)          # ascending
    rank_by_idx = np.zeros(n_pool, dtype=int)
    rank_by_idx[order] = np.arange(n_pool)  # rank 0 = lowest L = most LC2-optimized

    quran_idx = [i for i, r in enumerate(pool) if r["corpus"] == "quran"]
    ctrl_idx = [i for i, r in enumerate(pool) if r["corpus"] != "quran"]

    quran_ranks = rank_by_idx[quran_idx]
    quran_pct = (quran_ranks + 1) / n_pool * 100  # percentile in pool (lower = better)

    per_lambda[lam] = {
        "lambda":           lam,
        "n_pool":           n_pool,
        "L_q_mean":         float(np.mean([L_pool[i] for i in quran_idx])),
        "L_q_median":       float(np.median([L_pool[i] for i in quran_idx])),
        "L_ctrl_mean":      float(np.mean([L_pool[i] for i in ctrl_idx])),
        "L_ctrl_median":    float(np.median([L_pool[i] for i in ctrl_idx])),
        "quran_median_rank":     float(np.median(quran_ranks)),
        "quran_median_pct":      float(np.median(quran_pct)),
        "quran_min_rank":        int(quran_ranks.min()),
        "quran_max_rank":        int(quran_ranks.max()),
        "quran_mean_pct":        float(np.mean(quran_pct)),
        "frac_quran_in_bottom5": float(np.mean(quran_pct <= 5)),
        "frac_quran_in_bottom10": float(np.mean(quran_pct <= 10)),
    }
    print(f"  λ={lam:4.1f}: Quran median pct={per_lambda[lam]['quran_median_pct']:.2f}%, "
          f"mean pct={per_lambda[lam]['quran_mean_pct']:.2f}%, "
          f"frac in bottom-5%={per_lambda[lam]['frac_quran_in_bottom5']:.3f}")

# --------------------------------------------------------------- Verdict
n_lam_5pct  = sum(1 for lam, r in per_lambda.items() if r["quran_median_pct"] <= 5)
n_lam_10pct = sum(1 for lam, r in per_lambda.items() if r["quran_median_pct"] <= 10)
if n_lam_5pct >= 3:
    verdict = "LC2_SIGNATURE"
elif n_lam_10pct >= 3:
    verdict = "WEAK_LC2"
else:
    verdict = "NULL_NO_LC2"
print(f"\n[E16] {n_lam_5pct} / {len(LAMBDAS)} λ have Quran median ≤ 5th pct")
print(f"      {n_lam_10pct} / {len(LAMBDAS)} λ have Quran median ≤ 10th pct")
print(f"      Verdict: {verdict}")

# --------------------------------------------------------------- Outputs
report = {
    "experiment_id": "expE16_lc2_signature",
    "task":          "E16",
    "tier":          4,
    "title":         "Memorization-Optimization Signature (LC2) across λ grid",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "seed":          SEED,
    "lambdas":       LAMBDAS,
    "band_A":        [BAND_A_LO, BAND_A_HI],
    "M_definition": "H_cond(root_{i+1} | root_i) on verse-final roots (lower = more predictable = easier memorization)",
    "V_definition": "Shannon entropy of verse-final letter distribution (higher = more positional variety)",
    "n_quran_units_bandA":   len(quran_rows),
    "n_ctrl_units_bandA":    len(ctrl_rows),
    "n_lambda_at_5pct":      n_lam_5pct,
    "n_lambda_at_10pct":     n_lam_10pct,
    "per_lambda":            {str(k): v for k, v in per_lambda.items()},
    "verdict":               verdict,
    "pre_registered_criteria": {
        "null":           "Quran median L-rank > 5th pct for every λ in grid",
        "LC2_SIGNATURE":  "Quran median L-rank <= 5th pct for >= 3 of 5 λ values",
        "WEAK_LC2":       "Quran median L-rank <= 10th pct for >= 3 of 5 λ values",
        "NULL_NO_LC2":    "fewer λ meet 10th-pct threshold",
        "side_effects":   "no mutation of any pinned artefact; outputs under expE16 only",
    },
}
(OUTDIR / "expE16_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
)

# --------------------------------------------------------------- Plots
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Left: M vs V scatter + L contours
M_q = np.array([r["M"] for r in quran_rows])
V_q = np.array([r["V"] for r in quran_rows])
M_c = np.array([r["M"] for r in ctrl_rows])
V_c = np.array([r["V"] for r in ctrl_rows])
axes[0].scatter(V_c, M_c, s=8, c="C0", alpha=0.4, label=f"Arabic control (n={len(M_c)})")
axes[0].scatter(V_q, M_q, s=18, c="red", alpha=0.8, label=f"Quran (n={len(M_q)})")
axes[0].set_xlabel("V  = verse-final letter entropy (higher → more varied)")
axes[0].set_ylabel("M  = H_cond(root_{i+1} | root_i)  (lower → more memorable)")
axes[0].set_title("Quran vs Arabic controls in (V, M) space")
axes[0].legend(); axes[0].grid(True, alpha=0.3)

# Right: Quran median percentile vs lambda
lams = list(per_lambda.keys())
med_pcts = [per_lambda[lam]["quran_median_pct"] for lam in lams]
axes[1].plot(lams, med_pcts, "ro-", markersize=10, lw=2, label="Quran median pct")
axes[1].axhline(5, color="g", ls="--", alpha=0.5, label="5% threshold (LC2_SIGNATURE)")
axes[1].axhline(10, color="orange", ls="--", alpha=0.5, label="10% threshold (WEAK_LC2)")
axes[1].set_xscale("log")
axes[1].set_xlabel("λ")
axes[1].set_ylabel("Quran median percentile in L-pool (lower = more LC2-optimized)")
axes[1].set_title(f"LC2 signature across λ   |   verdict: {verdict}")
axes[1].legend(); axes[1].grid(True, alpha=0.3)
for lam, pct in zip(lams, med_pcts):
    axes[1].annotate(f"{pct:.1f}%", (lam, pct),
                     textcoords="offset points", xytext=(7, 5), fontsize=9)

fig.tight_layout()
fig.savefig(OUTDIR / "expE16_lc2_plot.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --------------------------------------------------------------- Markdown
md = [
    "# expE16 — Memorization-Optimization Signature (LC2)",
    "",
    f"**Generated (UTC)**: {report['generated_utc']}",
    f"**Seed**: {SEED}  |  **Band-A**: [{BAND_A_LO}, {BAND_A_HI}] verses",
    f"**Quran Band-A units**: {len(quran_rows)}  |  **Control Band-A units**: {len(ctrl_rows)}",
    "",
    "## Definitions",
    "",
    "- `M(x) = H_cond(root_{i+1} | root_i)` on verse-final roots (from `src/features.py:h_cond_roots`).",
    "  Lower M ⇒ more predictable transitions ⇒ more memorable.",
    "- `V(x) = H(verse-final letter)` Shannon entropy (from `src/features.py:h_el`).",
    "  Higher V ⇒ more positional variety ⇒ anti-forgetting.",
    "- `L(x; λ) = M(x) − λ · V(x)`. Lower L ⇒ better LC2 optimization.",
    "",
    "## Pre-registration",
    "",
    "- **Null**: Quran median L-rank > 5th pct for every λ in {0.1, 0.5, 1, 2, 5}.",
    "- **LC2_SIGNATURE**: median rank ≤ 5th pct for ≥ 3 λ values.",
    "- **WEAK_LC2**: median rank ≤ 10th pct for ≥ 3 λ values.",
    "- **NULL_NO_LC2**: fewer λ meet even the 10th-pct threshold.",
    "",
    f"## Verdict — **{verdict}**",
    "",
    "| λ | Quran median pct | Quran mean pct | frac in bottom 5% | L_q median | L_ctrl median |",
    "|---|--:|--:|--:|--:|--:|",
]
for lam, r in per_lambda.items():
    md.append(f"| {lam} | {r['quran_median_pct']:.2f}% | {r['quran_mean_pct']:.2f}% | "
              f"{r['frac_quran_in_bottom5']:.3f} | {r['L_q_median']:.4f} | {r['L_ctrl_median']:.4f} |")

md.append("")
md.append(f"**λ-count at median ≤ 5th pct**:  {n_lam_5pct} / {len(LAMBDAS)}")
md.append(f"**λ-count at median ≤ 10th pct**: {n_lam_10pct} / {len(LAMBDAS)}")

md.append("")
md.append("## Outputs")
md.append("")
md.append("- `expE16_report.json` — per-λ numbers + verdict")
md.append("- `expE16_lc2_plot.png` — (V, M) scatter + Quran pct vs λ curve")

(OUTDIR / "expE16_report.md").write_text("\n".join(md), encoding="utf-8")
print(f"Total runtime: {time.time()-t0:.1f}s")
