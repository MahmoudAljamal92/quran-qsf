"""
expE17_dual_opt — Canonical-order dual-optimization verification.
Test whether the Mushaf surah ordering Pareto-dominates both the Nuzul
(chronological) ordering and 1000 random permutations on two objectives.

PRE-REGISTRATION:
  Objectives (lower = better for both):
    J1 = sum of squared Mahalanobis transitions between adjacent surahs in the
         ordering, using the pooled Quran-covariance (inter-surah smoothness).
    J2 = Shannon entropy of the signed-transition-direction sequence under
         a 5-dimensional sign vector (sign(x_{i+1} − x_i) in each of the 5
         features). Lower entropy = more rhythmically uniform shifts.
  Null hypothesis:
    Mushaf ordering is NOT Pareto-better than Nuzul + ≥95 % of random perms.
  Pass conditions:
    MUSHAF_PARETO_DOMINANT: Mushaf beats Nuzul AND beats ≥95% of random perms
                            on both J1 AND J2 jointly (Pareto strict).
    MUSHAF_ONE_AXIS_DOMINANT: beats ≥95% of randoms on exactly one axis.
    NULL_NO_DUAL_OPT: below both.
  Seed: 42.

Nuzul order = Egyptian Standard Edition chronological sequence (Azhar).
Source: archive/scripts_pipeline/scripts/qsf_breakthrough_tests.py (validated
114-unique 1-indexed list). Caveat: true historical chronology is uncertain;
Egyptian ordering is the most widely-cited standard reconstruction.
"""
from __future__ import annotations
import json
import pickle
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import entropy as shannon_entropy

ROOT = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUTDIR = ROOT / "results" / "experiments" / "expE17_dual_opt"
OUTDIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

SEED = 42
N_PERM = 10_000
FV_ORDER = ["EL", "VL_CV", "CN", "H_cond", "T"]

NUZUL_ORDER_1IDX = [
    96, 68, 73, 74, 1, 111, 81, 87, 92, 89, 93, 94, 103, 100, 108, 102,
    107, 109, 105, 113, 114, 112, 53, 80, 97, 91, 85, 95, 106, 101, 75,
    104, 77, 50, 90, 86, 54, 38, 7, 72, 36, 25, 35, 19, 20, 56, 26, 27,
    28, 17, 10, 11, 12, 15, 6, 37, 31, 34, 39, 40, 41, 42, 43, 44, 45,
    46, 51, 88, 18, 16, 71, 14, 21, 23, 32, 52, 67, 69, 70, 78, 79, 82,
    84, 30, 29, 83, 2, 8, 3, 33, 60, 4, 99, 57, 47, 13, 55, 76, 65, 98,
    59, 24, 22, 63, 58, 49, 66, 64, 61, 62, 48, 5, 9, 110,
]
assert len(NUZUL_ORDER_1IDX) == 114 and set(NUZUL_ORDER_1IDX) == set(range(1, 115))

# --------------------------------------------------------------- Load state
t0 = time.time()
state = pickle.load(open(ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl", "rb"))["state"]
assert state["FEAT_COLS"] == FV_ORDER

# Per-surah 5-D features, indexed 1..114 by surah number
feat_by_surah = {}
for i, u in enumerate(state["CORPORA"]["quran"]):
    label = getattr(u, "label", f"Q:{i+1}")
    sn = int(str(label).replace("Q:", "").strip())
    feat_by_surah[sn] = [state["FEATS"]["quran"][i][c] for c in FV_ORDER]

assert set(feat_by_surah.keys()) == set(range(1, 115)), \
    f"Missing surahs: {set(range(1, 115)) - set(feat_by_surah.keys())}"

# Matrix in mushaf order (row i = surah i+1)
X_all = np.array([feat_by_surah[s] for s in range(1, 115)], dtype=float)
print(f"[E17] X_all: {X_all.shape}")

# --------------------------------------------------------------- Standardise + Mahalanobis setup
mu = X_all.mean(axis=0)
Z = X_all - mu
Sigma = np.cov(Z, rowvar=False) + 1e-6 * np.eye(5)
Sigma_inv = np.linalg.pinv(Sigma)

def J1_maha_smoothness(order_1idx):
    """Sum of squared Mahalanobis transition distances in the given ordering."""
    rows = np.array([feat_by_surah[s] for s in order_1idx], dtype=float)
    diffs = rows[1:] - rows[:-1]                                 # (113, 5)
    d2 = np.einsum("ij,jk,ik->i", diffs, Sigma_inv, diffs)       # (113,)
    return float(d2.sum())

def J2_sign_entropy(order_1idx):
    """Entropy of the 5-bit sign-direction sequence of feature transitions.

    For each of the 113 adjacent pairs, form a 5-bit signature
    (+1 / 0 / −1 per feature → mapped to trinary digit). The sequence has
    3^5 = 243 possible codes. Count frequencies, compute Shannon entropy.
    Lower entropy = more rhythmic (same transition pattern recurring)."""
    rows = np.array([feat_by_surah[s] for s in order_1idx], dtype=float)
    diffs = rows[1:] - rows[:-1]                                 # (113, 5)
    sign = np.sign(diffs).astype(int) + 1                        # shift to {0, 1, 2}
    # base-3 code
    code = (sign[:, 0] * 81 + sign[:, 1] * 27 + sign[:, 2] * 9
            + sign[:, 3] * 3  + sign[:, 4]).tolist()
    cnt = Counter(code)
    freqs = np.array(list(cnt.values()), dtype=float)
    freqs /= freqs.sum()
    return float(shannon_entropy(freqs, base=2))

# --------------------------------------------------------------- Scoring
mushaf_order = list(range(1, 115))
nuzul_order  = list(NUZUL_ORDER_1IDX)

J1_mushaf = J1_maha_smoothness(mushaf_order)
J2_mushaf = J2_sign_entropy(mushaf_order)
J1_nuzul  = J1_maha_smoothness(nuzul_order)
J2_nuzul  = J2_sign_entropy(nuzul_order)
print(f"[E17] Mushaf: J1={J1_mushaf:.4f}, J2={J2_mushaf:.4f}")
print(f"[E17] Nuzul:  J1={J1_nuzul:.4f},  J2={J2_nuzul:.4f}")

# --------------------------------------------------------------- 10 000 random perms
rng = np.random.default_rng(SEED)
perm_J1 = np.zeros(N_PERM)
perm_J2 = np.zeros(N_PERM)
for i in range(N_PERM):
    perm = list(rng.permutation(114) + 1)
    perm_J1[i] = J1_maha_smoothness(perm)
    perm_J2[i] = J2_sign_entropy(perm)
print(f"[E17] random perms: J1 mean={perm_J1.mean():.4f} sd={perm_J1.std(ddof=1):.4f}")
print(f"              J2 mean={perm_J2.mean():.4f} sd={perm_J2.std(ddof=1):.4f}")

# --------------------------------------------------------------- Quantiles
q_J1_mushaf = float((perm_J1 <= J1_mushaf).mean())   # fraction of perms with SMALLER-or-equal J1 → want SMALL
q_J1_nuzul  = float((perm_J1 <= J1_nuzul ).mean())
q_J2_mushaf = float((perm_J2 <= J2_mushaf).mean())
q_J2_nuzul  = float((perm_J2 <= J2_nuzul ).mean())

print("\n[E17] Quantile among random perms (lower = better):")
print(f"  Mushaf J1 quantile: {q_J1_mushaf:.4f}   (J1={J1_mushaf:.3f})")
print(f"  Mushaf J2 quantile: {q_J2_mushaf:.4f}   (J2={J2_mushaf:.3f})")
print(f"  Nuzul  J1 quantile: {q_J1_nuzul:.4f}   (J1={J1_nuzul:.3f})")
print(f"  Nuzul  J2 quantile: {q_J2_nuzul:.4f}   (J2={J2_nuzul:.3f})")

# --------------------------------------------------------------- Pareto check
# Mushaf beats a competitor c iff (J1_m <= J1_c AND J2_m <= J2_c) AND at least one strict.
def pareto_beats(m_J1, m_J2, c_J1, c_J2):
    return (m_J1 <= c_J1) and (m_J2 <= c_J2) and ((m_J1 < c_J1) or (m_J2 < c_J2))

mushaf_beats_nuzul = bool(pareto_beats(J1_mushaf, J2_mushaf, J1_nuzul, J2_nuzul))
frac_mushaf_beats_perm = float(np.mean(
    (perm_J1 > J1_mushaf) & (perm_J2 > J2_mushaf)   # strict Pareto dominance over perm
    | ((perm_J1 >= J1_mushaf) & (perm_J2 > J2_mushaf))
    | ((perm_J1 > J1_mushaf) & (perm_J2 >= J2_mushaf))
))

print(f"\n[E17] Mushaf strictly Pareto-beats Nuzul:            {mushaf_beats_nuzul}")
print(f"[E17] Fraction of perms Mushaf Pareto-beats:         {frac_mushaf_beats_perm:.4f}")

# --------------------------------------------------------------- Verdict
beats_95_J1 = q_J1_mushaf <= 0.05
beats_95_J2 = q_J2_mushaf <= 0.05
if mushaf_beats_nuzul and beats_95_J1 and beats_95_J2:
    verdict = "MUSHAF_PARETO_DOMINANT"
elif beats_95_J1 or beats_95_J2:
    verdict = "MUSHAF_ONE_AXIS_DOMINANT"
else:
    verdict = "NULL_NO_DUAL_OPT"
print(f"\nVerdict: {verdict}")

# --------------------------------------------------------------- OUTPUT
report = {
    "experiment_id":  "expE17_dual_opt",
    "task":           "E17",
    "tier":           4,
    "title":          "Canonical-order dual-optimization: Mushaf vs Nuzul vs random perms",
    "generated_utc":  datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "seed":           SEED,
    "n_permutations": N_PERM,
    "feature_order":  FV_ORDER,
    "objectives": {
        "J1": "sum of squared Mahalanobis transitions between adjacent surahs (lower = smoother)",
        "J2": "Shannon entropy (bits) of 5-bit sign-direction sequence over adjacent transitions (lower = more rhythmic)",
    },
    "mushaf": {"J1": J1_mushaf, "J2": J2_mushaf,
               "perm_quantile_J1": q_J1_mushaf, "perm_quantile_J2": q_J2_mushaf},
    "nuzul":  {"J1": J1_nuzul,  "J2": J2_nuzul,
               "perm_quantile_J1": q_J1_nuzul,  "perm_quantile_J2": q_J2_nuzul},
    "random_perm_summary": {
        "J1_mean": float(perm_J1.mean()), "J1_sd": float(perm_J1.std(ddof=1)),
        "J2_mean": float(perm_J2.mean()), "J2_sd": float(perm_J2.std(ddof=1)),
        "J1_q05":  float(np.quantile(perm_J1, 0.05)),
        "J1_q95":  float(np.quantile(perm_J1, 0.95)),
        "J2_q05":  float(np.quantile(perm_J2, 0.05)),
        "J2_q95":  float(np.quantile(perm_J2, 0.95)),
    },
    "mushaf_strictly_pareto_beats_nuzul": mushaf_beats_nuzul,
    "mushaf_pareto_beats_frac_of_perms":  frac_mushaf_beats_perm,
    "verdict": verdict,
    "nuzul_source": "Egyptian Standard Edition (Azhar) chronological ordering, 114-unique validated list",
    "caveat": "Historical chronology is uncertain; the Egyptian standard is the most widely-cited reconstruction, used here as best available.",
    "pre_registered_criteria": {
        "null":                     "Mushaf not Pareto-better than Nuzul + >=95% of random perms",
        "MUSHAF_PARETO_DOMINANT":   "Mushaf Pareto-beats Nuzul AND J1-quantile <= 0.05 AND J2-quantile <= 0.05",
        "MUSHAF_ONE_AXIS_DOMINANT": "Mushaf quantile <= 0.05 on exactly one of J1, J2",
        "NULL_NO_DUAL_OPT":         "neither axis at <= 0.05",
        "side_effects":             "no mutation of any pinned artefact; outputs under expE17 only",
    },
}
(OUTDIR / "expE17_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
)

# --------------------------------------------------------------- Plot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(9, 6))
ax.scatter(perm_J1, perm_J2, s=3, c="0.6", alpha=0.35, label=f"random perms (n={N_PERM})")
ax.scatter([J1_mushaf], [J2_mushaf], s=200, c="red", marker="*",
           edgecolor="black", linewidth=1.2, label=f"Mushaf (J1 q={q_J1_mushaf:.3f}, J2 q={q_J2_mushaf:.3f})", zorder=5)
ax.scatter([J1_nuzul], [J2_nuzul], s=200, c="blue", marker="D",
           edgecolor="black", linewidth=1.2, label=f"Nuzul (J1 q={q_J1_nuzul:.3f}, J2 q={q_J2_nuzul:.3f})", zorder=5)
ax.set_xlabel("J1 — sum of squared Mahalanobis transitions (lower = smoother)")
ax.set_ylabel("J2 — sign-direction-sequence entropy (bits; lower = rhythmic)")
ax.set_title(f"Mushaf vs Nuzul vs {N_PERM} random perms   |   verdict: {verdict}")
ax.legend(loc="best", fontsize=9); ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(OUTDIR / "expE17_pareto_scatter.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --------------------------------------------------------------- Markdown
md = [
    "# expE17 — Canonical-order dual-optimization",
    "",
    f"**Generated (UTC)**: {report['generated_utc']}",
    f"**Seed**: {SEED}  |  **N random perms**: {N_PERM}",
    "",
    "## Objectives (lower = better)",
    "",
    "- **J1**: sum of squared Mahalanobis transitions between adjacent surahs,",
    "  using Σ = Cov(Quran 5-D features over 114 surahs). Measures inter-surah",
    "  smoothness of the ordering.",
    "- **J2**: Shannon entropy (bits) of the 5-bit sign-direction sequence over",
    "  the 113 adjacent transitions. Codes 3^5 = 243 possible sign patterns.",
    "  Lower entropy = more rhythmic repetition of the same transition pattern.",
    "",
    "## Pre-registration",
    "",
    "- **Null**: Mushaf is not Pareto-better than Nuzul or ≥ 95 % of random perms.",
    "- **MUSHAF_PARETO_DOMINANT**: Mushaf Pareto-beats Nuzul AND has q ≤ 0.05 on BOTH axes.",
    "- **MUSHAF_ONE_AXIS_DOMINANT**: q ≤ 0.05 on exactly one of J1, J2.",
    "- **NULL_NO_DUAL_OPT**: neither.",
    "",
    f"## Verdict — **{verdict}**",
    "",
    "## Numbers",
    "",
    "| Ordering | J1 | J2 | J1 quantile among random | J2 quantile among random |",
    "|---|--:|--:|--:|--:|",
    f"| Mushaf | {J1_mushaf:.4f} | {J2_mushaf:.4f} | {q_J1_mushaf:.4f} | {q_J2_mushaf:.4f} |",
    f"| Nuzul (Egyptian) | {J1_nuzul:.4f} | {J2_nuzul:.4f} | {q_J1_nuzul:.4f} | {q_J2_nuzul:.4f} |",
    f"| Random (mean ± sd) | {perm_J1.mean():.4f} ± {perm_J1.std(ddof=1):.4f} | {perm_J2.mean():.4f} ± {perm_J2.std(ddof=1):.4f} | — | — |",
    "",
    f"- **Mushaf Pareto-beats Nuzul**: {mushaf_beats_nuzul}",
    f"- **Fraction of perms Mushaf Pareto-beats**: {frac_mushaf_beats_perm:.4f}",
    "",
    "## Caveats",
    "",
    "- Nuzul order is the Egyptian Standard Edition (Azhar) — the most widely-cited",
    "  reconstruction but NOT a uniquely-verified historical chronology.",
    "- The choice of `Σ` (pooled Quran-only covariance) means J1 measures smoothness",
    "  *relative to the Quran's own feature distribution*, not relative to an external pool.",
    "",
    "## Outputs",
    "",
    "- `expE17_report.json` — numbers + verdict",
    "- `expE17_pareto_scatter.png` — (J1, J2) scatter with Mushaf / Nuzul / random perms",
]
(OUTDIR / "expE17_report.md").write_text("\n".join(md), encoding="utf-8")
print(f"Total runtime: {time.time()-t0:.1f}s")
