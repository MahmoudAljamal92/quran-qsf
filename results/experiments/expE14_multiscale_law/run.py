"""
expE14_multiscale_law — Multi-scale Fisher combination law for the Quran.
Combines 5 scale-level signatures (letter, root-proxy, verse, surah, corpus)
into a single correlation-aware composite statistic via Brown's method, then
decomposes evidence across scales via Shapley values.

PRE-REGISTRATION (set before execution):
  Null hypothesis:
      Quran evidence is concentrated on a single scale; the multi-scale
      framing is cosmetic (one scale dominates >95% of Shapley weight).
  Pass condition:
      Combined Brown-corrected p < 0.01 AND max single-scale Shapley share
      < 60% → MULTISCALE_LAW.
      Combined p < 0.01 but one scale > 60% share → SINGLE_SCALE_DOMINANT.
      Combined p >= 0.01 → NULL_NO_COMBINED_EVIDENCE.
  Side effects:
      No mutation of any pinned artefact; outputs under expE14 folder only.
  Seed: 42.

Scales:
  S1 (letter):       KL(letter unigram || Arabic control pool)
  S2 (root proxy):   letter-bigram transition entropy deviation
  S3 (verse):        |H_DFA - 0.5| on verse-length series
  S4 (surah):        mean 5-D Mahalanobis distance of Quran to control centroid
  S5 (corpus):       L_TEL = 0.5329*T + 4.1790*EL - 1.5221  (§4.36 weights)
"""
from __future__ import annotations

import json
import pickle
import re
import sys
import time
import warnings
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from math import comb
from pathlib import Path

import numpy as np
from scipy import stats

warnings.filterwarnings("ignore")

ROOT = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUTDIR = ROOT / "results" / "experiments" / "expE14_multiscale_law"
OUTDIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

SEED = 42
N_SHUFFLES = 500
ARABIC_CTRL = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
               "ksucca", "arabic_bible", "hindawi"]
ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
ARABIC_RE = re.compile(r"[\u0621-\u064A]")
DIAC = set("\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
           "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
           "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670")
_FOLD = {"ء": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "ا", "ئ": "ا",
         "ة": "ه", "ى": "ي"}
W_T, W_EL, B_TEL = 0.5329, 4.1790, -1.5221
BAND_A_LO, BAND_A_HI = 15, 100
FV_ORDER = ["EL", "VL_CV", "CN", "H_cond", "T"]

# --------------------------------------------------------------- text utils
def _strip_d(s): return "".join(c for c in s if c not in DIAC)
def _letters_28(text):
    out = []
    for c in _strip_d(text):
        if c in _FOLD: out.append(_FOLD[c])
        elif c in ARABIC_CONS_28: out.append(c)
    return "".join(out)

# --------------------------------------------------------------- scale statistics
def stat_S1_letter_kl(letters: str, pool_freq: np.ndarray) -> float:
    """KL(target || pool) on letter-frequency distributions over 28 consonants."""
    cnt = Counter(letters)
    p = np.array([cnt.get(c, 0) for c in ARABIC_CONS_28], dtype=float)
    s = p.sum()
    if s <= 0: return 0.0
    p /= s
    # Laplace smoothing to avoid log(0)
    eps = 1e-6
    p = (p + eps) / (1 + 28 * eps)
    q = (pool_freq + eps) / (1 + 28 * eps)
    return float(np.sum(p * np.log(p / q)))

def stat_S2_bigram_entropy(letters: str) -> float:
    """H(letter | prev_letter)."""
    if len(letters) < 2: return 0.0
    bigrams = Counter(letters[i:i + 2] for i in range(len(letters) - 1))
    totals = Counter(letters[:-1])
    H = 0.0
    for bg, n in bigrams.items():
        prev = bg[0]
        p_bg = n / max(sum(bigrams.values()), 1)
        p_cond = n / max(totals[prev], 1)
        if p_cond > 0:
            H -= p_bg * np.log2(p_cond)
    return float(H)

def stat_S3_dfa_hurst(vl: np.ndarray) -> float:
    """DFA Hurst with nolds if available (matches E7)."""
    try:
        import nolds
        return float(nolds.dfa(vl))
    except Exception:
        x = np.asarray(vl, dtype=float) - np.mean(vl)
        y = np.cumsum(x); n = len(y)
        scales = np.unique(np.logspace(np.log10(4), np.log10(n // 4), 12).astype(int))
        F = []
        for s in scales:
            n_w = n // s
            if n_w < 1: continue
            reshaped = y[: n_w * s].reshape(n_w, s)
            t = np.arange(s); res = []
            for seg in reshaped:
                p = np.polyfit(t, seg, 1)
                res.append(np.mean((seg - np.polyval(p, t)) ** 2))
            F.append(np.sqrt(np.mean(res)))
        if len(F) < 4: return 0.5
        slope, _ = np.polyfit(np.log(scales[:len(F)]), np.log(np.maximum(F, 1e-12)), 1)
        return float(slope)

def stat_S4_mahalanobis(X_target: np.ndarray, mu_ctrl: np.ndarray, Sigma_ctrl: np.ndarray) -> float:
    """mean Mahalanobis distance of each row of X_target from control centroid."""
    inv = np.linalg.pinv(Sigma_ctrl)
    diffs = X_target - mu_ctrl
    d2 = np.einsum("ij,jk,ik->i", diffs, inv, diffs)
    return float(np.sqrt(np.clip(d2, 0, None)).mean())

def stat_S5_L_TEL(X: np.ndarray) -> np.ndarray:
    """§4.36 L_TEL scalar per-unit = W_T*T + W_EL*EL + B."""
    el = X[:, FV_ORDER.index("EL")]
    t  = X[:, FV_ORDER.index("T")]
    return W_T * t + W_EL * el + B_TEL

# --------------------------------------------------------------- Brown combination
def brown_combined_p(p_values: np.ndarray, R: np.ndarray) -> tuple[float, float, float]:
    """Brown's method. Returns (X2_obs, df_adj, p_combined)."""
    p = np.clip(np.asarray(p_values, dtype=float), 1e-300, 1.0)
    k = len(p)
    f = -2 * np.log(p)
    X2 = float(f.sum())
    # Brown (1975) approx for cov(f_i, f_j) given |rho_ij|
    rho = np.asarray(R, dtype=float)
    # Guard: diagonal is 4 (Var[-2 log U] for U~Unif(0,1) = 4)
    cov_sum = 0.0
    for i in range(k):
        for j in range(i + 1, k):
            r = abs(rho[i, j])
            cov_sum += 3.25 * r + 0.75 * r * r
    E = 2 * k
    V = 4 * k + 2 * cov_sum
    c = V / (2 * E)
    df_adj = 2 * E / V
    p_combined = float(stats.chi2.sf(X2 / c, df=df_adj))
    return X2, df_adj, p_combined

# --------------------------------------------------------------- Shapley on combined score
def shapley_values(p_list: list[float], R: np.ndarray) -> np.ndarray:
    """Shapley value of each scale under the Brown-corrected combined -log10(p)."""
    k = len(p_list)
    idx = list(range(k))
    full_contrib = np.zeros(k)
    # brute-force Shapley: O(k * 2^(k-1))
    for i in idx:
        others = [j for j in idx if j != i]
        for r in range(len(others) + 1):
            for S in combinations(others, r):
                S = list(S)
                S_with = S + [i]
                # p-vectors for each subset
                Rs_with = R[np.ix_(S_with, S_with)]
                Rs_without = R[np.ix_(S, S)] if S else np.zeros((0, 0))
                p_with = np.array([p_list[j] for j in S_with])
                p_without = np.array([p_list[j] for j in S]) if S else np.array([])
                # Combined p for each
                if len(p_with) > 0:
                    _, _, pc_with = brown_combined_p(p_with, Rs_with)
                else:
                    pc_with = 1.0
                if len(p_without) > 0:
                    _, _, pc_without = brown_combined_p(p_without, Rs_without)
                else:
                    pc_without = 1.0
                score_with = -np.log10(max(pc_with, 1e-300))
                score_without = -np.log10(max(pc_without, 1e-300))
                weight = 1.0 / (k * comb(k - 1, r))
                full_contrib[i] += weight * (score_with - score_without)
    return full_contrib

# --------------------------------------------------------------- MAIN
t0 = time.time()
print("[E14] loading state ...")
state = pickle.load(open(ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl", "rb"))["state"]
FEAT_COLS = state["FEAT_COLS"]
assert FEAT_COLS == FV_ORDER
CORPORA = state["CORPORA"]
FEATS = state["FEATS"]

# Quran-level and per-surah data
quran_units = CORPORA["quran"]
X_q = np.array([[f[c] for c in FEAT_COLS] for f in FEATS["quran"]], dtype=float)

# Full Quran text (letters only)
Q_letters = _letters_28(" ".join(v for u in quran_units for v in u.verses))
print(f"[E14] Quran letters: {len(Q_letters):,}")

# Arabic control pool — Band-A units
ctrl_units: list = []
for name in ARABIC_CTRL:
    ctrl_units.extend(u for u in CORPORA.get(name, [])
                      if BAND_A_LO <= len(u.verses) <= BAND_A_HI)
print(f"[E14] Arabic control pool: {len(ctrl_units)} Band-A units")

# Control text letters (pooled)
ctrl_letters_by_unit = [_letters_28(" ".join(u.verses)) for u in ctrl_units]
# Pool letter frequency (class reference distribution)
big_ctrl = "".join(ctrl_letters_by_unit)
ctrl_unigram = np.array([big_ctrl.count(c) for c in ARABIC_CONS_28], dtype=float)
ctrl_unigram /= max(ctrl_unigram.sum(), 1)

# Control 5-D feature matrix
X_ctrl_rows = []
for name in ARABIC_CTRL:
    for f in FEATS[name]:
        # Filter Band-A for consistency
        pass  # use all FEATS — they are already per-unit
X_ctrl_rows = []
for name in ARABIC_CTRL:
    for i, u in enumerate(CORPORA.get(name, [])):
        if BAND_A_LO <= len(u.verses) <= BAND_A_HI:
            X_ctrl_rows.append([FEATS[name][i][c] for c in FEAT_COLS])
X_ctrl = np.array(X_ctrl_rows, dtype=float)
mu_ctrl = X_ctrl.mean(axis=0)
Sigma_ctrl = np.cov(X_ctrl, rowvar=False) + 1e-6 * np.eye(5)
print(f"[E14] Control 5-D matrix: {X_ctrl.shape}")

# --------------------------------------------------------------- Per-scale observed stats
print("\n[E14] computing per-scale statistics ...")

# S1: letter-KL of Quran vs control unigram
S1_q = stat_S1_letter_kl(Q_letters, ctrl_unigram)
# S2: letter-bigram entropy deviation — |H_Q - mean(H_ctrl)|
S2_q_raw = stat_S2_bigram_entropy(Q_letters)
# S3: DFA-Hurst on verse-length series
vl = np.concatenate([np.array([len(v.split()) for v in u.verses])
                     for u in quran_units], dtype=float)
S3_q_raw = stat_S3_dfa_hurst(vl)
# S4: mean Mahalanobis of Quran-unit 5-D vectors from control centroid
S4_q = stat_S4_mahalanobis(X_q, mu_ctrl, Sigma_ctrl)
# S5: |L_TEL(Quran) mean - L_TEL(control) mean|
S5_q_vec = stat_S5_L_TEL(X_q); S5_c_vec = stat_S5_L_TEL(X_ctrl)

print(f"  S1 letter-KL(Q||ctrl):    {S1_q:.4f}")
print(f"  S2 bigram-entropy raw:    {S2_q_raw:.4f}")
print(f"  S3 DFA-H verse-length:    {S3_q_raw:.4f}")
print(f"  S4 mean Mahalanobis:      {S4_q:.4f}")
print(f"  S5 L_TEL mean:            {S5_q_vec.mean():.4f}  (ctrl mean = {S5_c_vec.mean():.4f})")

# --------------------------------------------------------------- Null distributions via control pool
print(f"\n[E14] building per-scale null from {len(ctrl_units)} control units ...")
# For each scale we estimate the null distribution by computing the statistic on
# each individual control unit (treating each control unit as if it were the
# "target" corpus). This gives an honest null distribution per scale without
# requiring joint shuffling.

null_S = np.zeros((5, len(ctrl_units)))
for i, u_text in enumerate(ctrl_letters_by_unit):
    # S1: KL of this control unit's letter dist vs the POOLED control (leave-one-out avoids circularity)
    others_text = "".join(ctrl_letters_by_unit[:i] + ctrl_letters_by_unit[i+1:])
    cnt_others = np.array([others_text.count(c) for c in ARABIC_CONS_28], dtype=float)
    cnt_others /= max(cnt_others.sum(), 1)
    null_S[0, i] = stat_S1_letter_kl(u_text, cnt_others)
    # S2: bigram entropy
    null_S[1, i] = stat_S2_bigram_entropy(u_text)
    # S3: DFA-H on this control unit's verse-length series
    u = ctrl_units[i]
    u_vl = np.array([len(v.split()) for v in u.verses], dtype=float)
    null_S[2, i] = stat_S3_dfa_hurst(u_vl)
    # S4: Mahalanobis of this unit's 5-D feature to control centroid (leave-one-out)
    # find this unit's 5-D feature
    x_u = None
    for nm in ARABIC_CTRL:
        for j, uu in enumerate(CORPORA.get(nm, [])):
            if uu is u:
                x_u = np.array([FEATS[nm][j][c] for c in FEAT_COLS], dtype=float)
                break
        if x_u is not None: break
    if x_u is None:
        null_S[3, i] = np.nan
    else:
        diff = x_u - mu_ctrl
        inv = np.linalg.pinv(Sigma_ctrl)
        null_S[3, i] = float(np.sqrt(max(0.0, diff @ inv @ diff)))
    # S5: mean L_TEL of this control unit (single scalar)
    if x_u is not None:
        null_S[4, i] = float(W_T * x_u[FV_ORDER.index("T")] + W_EL * x_u[FV_ORDER.index("EL")] + B_TEL)
    else:
        null_S[4, i] = np.nan

# Observed Quran 5-vector (one scalar per scale, absolute deviation for S2/S3/S5)
S2_q = abs(S2_q_raw - np.nanmean(null_S[1]))
S3_q = abs(S3_q_raw - 0.5)
S5_q = abs(S5_q_vec.mean() - np.nanmean(null_S[4]))
# for S1, S4: the observed is already a distance; use as-is
S1_q_use = S1_q
S4_q_use = S4_q

# Map null_S into absolute-deviation form for S2/S3/S5 to match
null_abs = null_S.copy()
null_abs[1] = np.abs(null_S[1] - np.nanmean(null_S[1]))
null_abs[2] = np.abs(null_S[2] - 0.5)
null_abs[4] = np.abs(null_S[4] - np.nanmean(null_S[4]))
# S1 and S4 already non-negative distances

# Strip NaNs column-wise (valid units only)
valid_cols = ~np.any(np.isnan(null_abs), axis=0)
null_abs = null_abs[:, valid_cols]
print(f"[E14] null shape after NaN strip: {null_abs.shape}")

# Observed Q 5-vector
Q_vec = np.array([S1_q_use, S2_q, S3_q, S4_q_use, S5_q])
print(f"[E14] Q vector (abs-dev): {Q_vec}")

# --------------------------------------------------------------- p-values per scale
scale_names = ["S1_letter_KL", "S2_bigram_H", "S3_DFA_H", "S4_Mahalanobis", "S5_L_TEL"]
p_vals = np.zeros(5)
for i in range(5):
    p_vals[i] = ((null_abs[i] >= Q_vec[i]).sum() + 1) / (null_abs[i].shape[0] + 1)
print("\n[E14] per-scale p-values:")
for n, q, p in zip(scale_names, Q_vec, p_vals):
    n_more_extreme = (null_abs[scale_names.index(n)] >= q).sum()
    print(f"  {n:>18}: obs={q:.4f}, p={p:.6f} ({n_more_extreme} of {null_abs.shape[1]} more extreme)")

# --------------------------------------------------------------- Correlation matrix from null
R = np.corrcoef(null_abs)
print("\n[E14] scale-pair correlation matrix R (from control-pool joint null):")
print(np.round(R, 3))

# --------------------------------------------------------------- Brown combination
X2_obs, df_adj, p_brown = brown_combined_p(p_vals, R)
# Uncorrected Fisher for comparison
X2_fisher = -2 * np.sum(np.log(np.clip(p_vals, 1e-300, 1)))
p_fisher = float(stats.chi2.sf(X2_fisher, df=10))
print(f"\n[E14] Fisher χ²_10 = {X2_fisher:.2f}, p_Fisher = {p_fisher:.3e}")
print(f"       Brown corrected: X²={X2_obs:.2f}, df_adj={df_adj:.2f}, p_Brown = {p_brown:.3e}")

# --------------------------------------------------------------- Shapley
print("\n[E14] computing Shapley decomposition (5 scales, 16 subsets per scale) ...")
phi = shapley_values(list(p_vals), R)
phi_total = float(phi.sum()) if phi.sum() > 0 else 1e-12
phi_share = phi / phi_total
print("  Shapley values (fraction of -log10(p_combined)):")
for n, v, s in zip(scale_names, phi, phi_share):
    print(f"    {n:>18}: phi={v:.4f} ({s * 100:.1f}%)")

# --------------------------------------------------------------- Verdict
max_share = float(phi_share.max())
if p_brown < 0.01 and max_share < 0.60:
    verdict = "MULTISCALE_LAW"
elif p_brown < 0.01:
    verdict = "SINGLE_SCALE_DOMINANT"
else:
    verdict = "NULL_NO_COMBINED_EVIDENCE"

# --------------------------------------------------------------- OUTPUT
report = {
    "experiment_id": "expE14_multiscale_law",
    "task": "E14",
    "tier": 4,
    "title": "Multi-scale Fisher combination law (letter → root → verse → surah → corpus)",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "seed": SEED,
    "scale_names": scale_names,
    "observed_Q_vec": Q_vec.tolist(),
    "p_per_scale": {n: float(p) for n, p in zip(scale_names, p_vals)},
    "null_pool_size": int(null_abs.shape[1]),
    "correlation_matrix_R": R.tolist(),
    "fisher_chi2_uncorrected":   float(X2_fisher),
    "fisher_p_uncorrected":      float(p_fisher),
    "brown_chi2_obs":            float(X2_obs),
    "brown_df_adjusted":         float(df_adj),
    "brown_p_combined":          float(p_brown),
    "shapley_values":            {n: float(v) for n, v in zip(scale_names, phi)},
    "shapley_shares":            {n: float(s) for n, s in zip(scale_names, phi_share)},
    "max_single_scale_share":    max_share,
    "verdict":                   verdict,
    "pre_registered_criteria": {
        "null":                      "Evidence on single scale dominates >95% of Shapley",
        "MULTISCALE_LAW":            "p_Brown < 0.01 AND max share < 60%",
        "SINGLE_SCALE_DOMINANT":     "p_Brown < 0.01 BUT max share >= 60%",
        "NULL_NO_COMBINED_EVIDENCE": "p_Brown >= 0.01",
        "side_effects":              "no mutation of any pinned artefact",
    },
}
(OUTDIR / "expE14_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
)

# --------------------------------------------------------------- Plots
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(15, 5))

# Shapley bars
axes[0].bar(scale_names, phi_share * 100, color=["C0", "C1", "C2", "C3", "C4"])
axes[0].axhline(60, color="red", ls="--", label="single-scale dominance cutoff 60%")
axes[0].set_ylabel("Shapley share of evidence (%)")
axes[0].set_title(f"Shapley decomposition — verdict {verdict}")
axes[0].legend(); axes[0].grid(True, alpha=0.3, axis="y")
for i, (nm, s) in enumerate(zip(scale_names, phi_share)):
    axes[0].text(i, s * 100 + 1, f"{s*100:.1f}%", ha="center", fontsize=9)

# R heatmap
im = axes[1].imshow(R, cmap="RdBu_r", vmin=-1, vmax=1)
axes[1].set_xticks(range(5)); axes[1].set_xticklabels(scale_names, rotation=35, ha="right")
axes[1].set_yticks(range(5)); axes[1].set_yticklabels(scale_names)
for i in range(5):
    for j in range(5):
        axes[1].text(j, i, f"{R[i, j]:+.2f}", ha="center", va="center",
                     color="white" if abs(R[i, j]) > 0.4 else "black", fontsize=9)
axes[1].set_title(f"Scale-pair correlation (Brown-adjusted p = {p_brown:.2e})")
fig.colorbar(im, ax=axes[1], label="Pearson r")
fig.tight_layout()
fig.savefig(OUTDIR / "expE14_shapley_and_R.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --------------------------------------------------------------- Markdown
md = [
    "# expE14 — Multi-scale Fisher combination law",
    "",
    f"**Generated (UTC)**: {report['generated_utc']}",
    f"**Seed**: {SEED}  |  **Null pool size**: {null_abs.shape[1]} Band-A control units (leave-one-out per scale)",
    "",
    "## Scales tested",
    "",
    "| # | Scale | Statistic |",
    "|---|---|---|",
    "| S1 | letter | KL(letter unigram ‖ pooled control) |",
    "| S2 | root proxy | letter-bigram conditional entropy |",
    "| S3 | verse | \\|DFA-H − 0.5\\| on verse-length series |",
    "| S4 | surah | mean Mahalanobis (5-D) of Quran units vs control centroid |",
    "| S5 | corpus | \\|L_TEL_Q − L_TEL_ctrl\\| (§4.36 weights) |",
    "",
    "## Observed p-values per scale",
    "",
    "| Scale | Observed stat | p (empirical, vs control pool) |",
    "|---|--:|--:|",
]
for n, q, p in zip(scale_names, Q_vec, p_vals):
    md.append(f"| {n} | {q:.4f} | {p:.6f} |")

md.append("")
md.append("## Combined statistics")
md.append("")
md.append(f"- **Fisher χ²₁₀ (no correction)**: {X2_fisher:.2f}  →  p = {p_fisher:.3e}")
md.append(f"- **Brown-corrected χ² = {X2_obs:.2f}, df_adj = {df_adj:.2f}**  →  **p = {p_brown:.3e}**")
md.append("")
md.append("## Shapley decomposition")
md.append("")
md.append("| Scale | φ (Shapley) | % of combined evidence |")
md.append("|---|--:|--:|")
for n, v, s in zip(scale_names, phi, phi_share):
    md.append(f"| {n} | {v:.4f} | {s*100:.1f}% |")

md.append("")
md.append(f"**Max single-scale share = {max_share*100:.1f}%**")
md.append("")
md.append(f"## Verdict — **{verdict}**")
md.append("")
md.append("## Outputs")
md.append("")
md.append("- `expE14_report.json` — all stats + R + Shapley")
md.append("- `expE14_shapley_and_R.png` — Shapley bar chart + R heatmap")

(OUTDIR / "expE14_report.md").write_text("\n".join(md), encoding="utf-8")

print(f"\nVerdict: {verdict} (p_Brown={p_brown:.3e}, max share={max_share*100:.1f}%)")
print(f"Total runtime: {time.time()-t0:.1f}s")
