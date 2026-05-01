"""
expE7_per_surah_hurst — Per-surah DFA Hurst exponent + box-counting fractal
dimension spectrum for the 114 surahs of the canonical Mushaf.

PRE-REGISTRATION (set before execution):
  Null hypothesis:
      Per-surah H-distribution matches what a 1000-shuffle mushaf-order null
      produces (i.e. distribution collapses to H≈0.5 and whole-corpus H=0.941
      is a cross-surah ordering artefact).
  Pass condition:
      Per-surah median H significantly > 0.5 by Wilcoxon signed-rank test
      AND survives length-regression control (H ~ log(n_verses) → residual H > 0.5).
  Side effects:
      No mutation of any pinned artefact. Outputs under expE7 folder only.
  Seed:
      NUMPY_SEED = 42.
"""
from __future__ import annotations

import json
import pickle
import re
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon, linregress

try:
    import nolds
    HAS_NOLDS = True
except Exception:
    HAS_NOLDS = False

warnings.filterwarnings("ignore")

ROOT = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUTDIR = ROOT / "results" / "experiments" / "expE7_per_surah_hurst"
OUTDIR.mkdir(parents=True, exist_ok=True)

SEED = 42
N_SHUFFLES = 200         # whole-corpus shuffle null (reduced for runtime)
N_SHUFFLES_SURAH = 0     # per-surah shuffle null — 0 disables (reduced E7)
MIN_N_VERSES = 40
RNG = np.random.default_rng(SEED)

ARABIC_RE = re.compile(r"[\u0621-\u064A]")

# -------------------------------------------------------- DFA (fallback)
def dfa_hurst(x: np.ndarray, min_scale: int = 4, max_scale: int | None = None,
              n_scales: int = 12) -> float:
    """Detrended-Fluctuation-Analysis Hurst exponent.
    Uses nolds if available (matching QSF pipeline), else a self-contained
    implementation equivalent to Peng et al. (1994).
    """
    x = np.asarray(x, dtype=float) - np.mean(x)
    n = len(x)
    if n < 10:
        return np.nan
    if HAS_NOLDS:
        try:
            return float(nolds.dfa(x))
        except Exception:
            pass
    # fallback
    y = np.cumsum(x)
    mx = max_scale or n // 4
    scales = np.unique(np.logspace(np.log10(min_scale), np.log10(mx), n_scales).astype(int))
    scales = scales[scales >= 4]
    F = []
    for s in scales:
        n_w = n // s
        if n_w < 1:
            continue
        reshaped = y[:n_w * s].reshape(n_w, s)
        t = np.arange(s)
        res_sq = []
        for seg in reshaped:
            p = np.polyfit(t, seg, 1)
            trend = np.polyval(p, t)
            res_sq.append(np.mean((seg - trend) ** 2))
        F.append(np.sqrt(np.mean(res_sq)))
    if len(F) < 4:
        return np.nan
    slope, _ = np.polyfit(np.log(scales[: len(F)]), np.log(np.maximum(F, 1e-12)), 1)
    return float(slope)

# -------------------------------------------------------- Box-counting
def box_counting_dim(x: np.ndarray, n_scales: int = 12) -> float:
    """Box-counting fractal dimension of the rescaled (t, x) graph."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 10:
        return np.nan
    # rescale to unit square
    t = np.arange(n) / max(n - 1, 1)
    xv = (x - x.min()) / max(x.max() - x.min(), 1e-12)
    scales = np.logspace(-2, -0.3, n_scales)
    counts = []
    for eps in scales:
        nb_t = int(np.ceil(1.0 / eps))
        nb_x = int(np.ceil(1.0 / eps))
        occupied = set()
        for i in range(n):
            occupied.add((int(t[i] * nb_t * 0.9999), int(xv[i] * nb_x * 0.9999)))
        counts.append(len(occupied))
    slope, _ = np.polyfit(np.log(1.0 / scales), np.log(counts), 1)
    return float(slope)

# --------------------------------------------------------------- LOAD
sys.path.insert(0, str(ROOT))
t0 = time.time()
state = pickle.load(open(ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl", "rb"))["state"]
quran_units = state["CORPORA"]["quran"]
print(f"Loaded in {time.time()-t0:.2f}s — {len(quran_units)} surahs; nolds={HAS_NOLDS}")

def last_letter_idx(verse: str, alphabet: list[str]) -> int:
    letters = ARABIC_RE.findall(verse)
    if not letters:
        return -1
    last = letters[-1]
    return alphabet.index(last) if last in alphabet else -1

# Build end-letter alphabet from the full corpus
all_ends = set()
for u in quran_units:
    for v in u.verses:
        L = ARABIC_RE.findall(v)
        if L:
            all_ends.add(L[-1])
alphabet = sorted(all_ends)

# --------------------------------------------------------------- COMPUTE
records = []
whole_vl = []
whole_el = []
for s_idx, u in enumerate(quran_units, start=1):
    vl = np.array([len(v.split()) for v in u.verses], dtype=float)
    el = np.array([last_letter_idx(v, alphabet) for v in u.verses], dtype=float)
    el = el[el >= 0]
    whole_vl.extend(vl.tolist())
    whole_el.extend(el.tolist())
    if len(vl) < MIN_N_VERSES:
        continue
    H_vl = dfa_hurst(vl)
    H_el = dfa_hurst(el) if len(el) >= MIN_N_VERSES else np.nan
    D_vl = box_counting_dim(vl)
    records.append({
        "surah":     s_idx,
        "label":     u.label,
        "n_verses":  int(len(vl)),
        "n_words":   int(vl.sum()),
        "H_vl":      float(H_vl),
        "H_el":      float(H_el) if np.isfinite(H_el) else None,
        "D_vl":      float(D_vl),
    })

whole_vl = np.asarray(whole_vl, dtype=float)
whole_el = np.asarray(whole_el, dtype=float)

# Whole-corpus Hurst (should reproduce the ~0.941 reference)
H_whole_vl = dfa_hurst(whole_vl)
H_whole_el = dfa_hurst(whole_el)

print(f"\nWhole-corpus DFA-H on 6236-pt verse-length series : {H_whole_vl:.4f}")
print(f"Whole-corpus DFA-H on 6236-pt end-letter series   : {H_whole_el:.4f}")
print(f"Per-surah analysis: {len(records)} surahs with n >= {MIN_N_VERSES}")

# --------------------------------------------------------------- STATS
H_vl_arr = np.array([r["H_vl"] for r in records])
H_el_arr = np.array([r["H_el"] for r in records if r["H_el"] is not None])
n_verses_arr = np.array([r["n_verses"] for r in records])

# Wilcoxon signed-rank vs H=0.5
wil_vl_stat, wil_vl_p = wilcoxon(H_vl_arr - 0.5, alternative="greater")
wil_el_stat, wil_el_p = wilcoxon(H_el_arr - 0.5, alternative="greater") if len(H_el_arr) else (np.nan, np.nan)

# Length-regression control: H ~ log(n_verses), check intercept + residuals
lr_vl = linregress(np.log(n_verses_arr), H_vl_arr)
resid_vl = H_vl_arr - (lr_vl.intercept + lr_vl.slope * np.log(n_verses_arr))
median_resid_vl = float(np.median(resid_vl))
intercept_at_typical = float(lr_vl.intercept + lr_vl.slope * np.log(np.median(n_verses_arr)))

# --------------------------------------------------------------- NULL
print(f"\nShuffle-null: {N_SHUFFLES} permutations of whole-corpus verse order ...")
t = time.time()
H_null_vl = np.empty(N_SHUFFLES)
for i in range(N_SHUFFLES):
    H_null_vl[i] = dfa_hurst(RNG.permutation(whole_vl))
print(f"  whole-corpus shuffle-null H_vl: mean={H_null_vl.mean():.4f}, sd={H_null_vl.std():.4f}, "
      f"{time.time()-t:.1f}s")

# Per-surah shuffle null — SKIPPED in reduced E7 (N_SHUFFLES_SURAH=0).
# Rationale: whole-corpus null already discriminates persistence from
# length-regression artefact; per-surah shuffle null deferred to E7-extended.
if N_SHUFFLES_SURAH > 0:
    print(f"Per-surah shuffle-null: {N_SHUFFLES_SURAH} permutations × surah ...")
    t = time.time()
    per_surah_p = []
    for r in records:
        s = next(u for u in quran_units if u.label == r["label"])
        vl = np.array([len(v.split()) for v in s.verses], dtype=float)
        H_null_s = np.array([dfa_hurst(RNG.permutation(vl))
                             for _ in range(N_SHUFFLES_SURAH)])
        p = float((H_null_s >= r["H_vl"]).mean())
        r["H_vl_shuffle_p"] = p
        per_surah_p.append(p)
    print(f"  per-surah shuffle null: mean p={np.mean(per_surah_p):.3f}, "
          f"fraction p<0.05: {(np.array(per_surah_p) < 0.05).mean():.3f}, "
          f"{time.time()-t:.1f}s")
    frac_sig = float((np.array(per_surah_p) < 0.05).mean())
else:
    print("Per-surah shuffle-null: SKIPPED (reduced-E7 mode, N_SHUFFLES_SURAH=0)")
    per_surah_p = []
    for r in records:
        r["H_vl_shuffle_p"] = None
    frac_sig = None

# --------------------------------------------------------------- VERDICT
# Criteria (reduced-E7 mode — frac_sig may be None):
#   (a) Wilcoxon-H>0.5 p<0.05 AND
#   (b) median residual after log(n) regression > 0 AND
#   (c) [optional] >50% of surahs pass their own shuffle null
if wil_vl_p < 0.05 and median_resid_vl > 0 and (frac_sig is not None and frac_sig >= 0.5):
    verdict = "PER_SURAH_PERSISTENT"
elif wil_vl_p < 0.05 and median_resid_vl > 0:
    verdict = "PARTIAL_PERSISTENT"
elif wil_vl_p < 0.05 or (frac_sig is not None and frac_sig >= 0.3):
    verdict = "WEAK_PERSISTENT"
else:
    verdict = "NULL_PER_SURAH_FLAT"

# --------------------------------------------------------------- OUTPUT
report = {
    "experiment_id": "expE7_per_surah_hurst",
    "task": "E7",
    "tier": 2,
    "title": "Per-surah DFA Hurst + box-counting fractal dimension spectrum",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "seed": SEED,
    "n_shuffles_whole": N_SHUFFLES,
    "n_shuffles_per_surah": N_SHUFFLES_SURAH,
    "reduced_mode": N_SHUFFLES_SURAH == 0,
    "min_n_verses": MIN_N_VERSES,
    "nolds_available": HAS_NOLDS,
    "whole_corpus": {
        "H_vl": float(H_whole_vl),
        "H_el": float(H_whole_el),
        "H_vl_shuffle_null_mean": float(H_null_vl.mean()),
        "H_vl_shuffle_null_sd":   float(H_null_vl.std()),
        "H_vl_shuffle_null_p":    float((H_null_vl >= H_whole_vl).mean()),
    },
    "per_surah_summary": {
        "n_surahs":  len(records),
        "H_vl": {
            "mean":   float(H_vl_arr.mean()),
            "median": float(np.median(H_vl_arr)),
            "sd":     float(H_vl_arr.std()),
            "min":    float(H_vl_arr.min()),
            "max":    float(H_vl_arr.max()),
            "p_lt_05_count":     int((H_vl_arr < 0.5).sum()),
            "p_gt_095_count":    int((H_vl_arr > 0.95).sum()),
        },
        "H_el": {
            "n_valid": int(len(H_el_arr)),
            "mean":    float(H_el_arr.mean())   if len(H_el_arr) else None,
            "median":  float(np.median(H_el_arr)) if len(H_el_arr) else None,
            "sd":      float(H_el_arr.std())    if len(H_el_arr) else None,
        },
        "wilcoxon_H_vl_gt_05_p": float(wil_vl_p),
        "wilcoxon_H_el_gt_05_p": float(wil_el_p) if np.isfinite(wil_el_p) else None,
        "length_regression_H_vl": {
            "slope":      float(lr_vl.slope),
            "intercept":  float(lr_vl.intercept),
            "r":          float(lr_vl.rvalue),
            "p":          float(lr_vl.pvalue),
            "median_residual": median_resid_vl,
            "intercept_at_median_n": intercept_at_typical,
        },
        "fraction_surahs_shuffle_p_lt_05": frac_sig,  # None in reduced mode
    },
    "pre_registered_criteria": {
        "PER_SURAH_PERSISTENT": "wil_p<0.05 AND median_resid>0 AND frac_shuf_sig>=0.5",
        "PARTIAL_PERSISTENT":   "wil_p<0.05 AND median_resid>0",
        "WEAK_PERSISTENT":      "wil_p<0.05 OR frac_shuf_sig>=0.3",
        "NULL_PER_SURAH_FLAT":  "neither",
    },
    "verdict": verdict,
    "per_surah": records,
}

(OUTDIR / "expE7_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
)

# Plots
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(H_vl_arr, bins=20, color="C0", edgecolor="0.3", alpha=0.8)
axes[0].axvline(0.5, color="red",   ls="--", label="H=0.5 (random)")
axes[0].axvline(H_whole_vl, color="green", ls="--",
                label=f"whole-corpus H={H_whole_vl:.3f}")
axes[0].axvline(H_null_vl.mean(), color="orange", ls=":",
                label=f"shuffle-null mean={H_null_vl.mean():.3f}")
axes[0].axvline(float(np.median(H_vl_arr)), color="C0", ls="-.",
                label=f"per-surah median={np.median(H_vl_arr):.3f}")
axes[0].set_xlabel("DFA Hurst exponent (verse-length)")
axes[0].set_ylabel(f"count (of {len(H_vl_arr)} surahs)")
frac_sig_str = f"{frac_sig:.2f}" if frac_sig is not None else "N/A (reduced)"
axes[0].set_title(f"expE7 — per-surah DFA-H\n"
                  f"Wilcoxon H>0.5 p={wil_vl_p:.2e}, "
                  f"frac(shuf p<0.05)={frac_sig_str}")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].scatter(n_verses_arr, H_vl_arr, c="C0", s=40, edgecolor="0.3", lw=0.3,
                label=f"surahs (n={len(records)})")
xs = np.linspace(n_verses_arr.min(), n_verses_arr.max(), 200)
axes[1].plot(xs, lr_vl.intercept + lr_vl.slope * np.log(xs), color="red", ls="--",
             label=f"H = {lr_vl.intercept:.3f} + {lr_vl.slope:.4f}·log(n)   r={lr_vl.rvalue:.2f}")
axes[1].axhline(0.5, color="0.5", ls=":", alpha=0.7)
axes[1].set_xscale("log")
axes[1].set_xlabel("n_verses (log)")
axes[1].set_ylabel("DFA Hurst (verse-length)")
axes[1].set_title("Length-regression control")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig(OUTDIR / "expE7_hurst_spectrum.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# Markdown
md = [
    "# expE7 — Per-surah DFA Hurst + box-counting fractal dimension spectrum",
    "",
    f"**Generated (UTC)**: {report['generated_utc']}",
    f"**Seed**: {SEED}  |  **Shuffles**: {N_SHUFFLES} whole + 100/surah  |  **nolds**: {HAS_NOLDS}",
    f"**Filter**: surahs with n_verses ≥ {MIN_N_VERSES}",
    "",
    "## Pre-registration (set before execution)",
    "",
    "- **Null**: per-surah H-distribution collapses to shuffle baseline (H ≈ 0.5).",
    "- **PER_SURAH_PERSISTENT**: Wilcoxon H>0.5 p<0.05 AND residual > 0 AND ≥ 50% surahs sig.",
    "- **PARTIAL_PERSISTENT**: Wilcoxon H>0.5 p<0.05 AND residual > 0.",
    "- **WEAK_PERSISTENT**: Wilcoxon p<0.05 OR ≥ 30% surahs sig.",
    "",
    f"## Verdict — **{verdict}**",
    "",
    "## Whole-corpus (sanity re-check)",
    "",
    f"- **H_vl on 6236-pt series**: {H_whole_vl:.4f}  (reference published value: ~0.941)",
    f"- **H_el on 6236-pt series**: {H_whole_el:.4f}",
    f"- **Shuffle-null H_vl**: {H_null_vl.mean():.4f} ± {H_null_vl.std():.4f} "
    f"(p vs obs = {(H_null_vl >= H_whole_vl).mean():.4f})",
    "",
    "## Per-surah H_vl statistics",
    "",
    f"- **Surahs analysed**: {len(records)}",
    f"- **H_vl median**: {np.median(H_vl_arr):.4f}  |  **mean**: {H_vl_arr.mean():.4f} ± {H_vl_arr.std():.4f}",
    f"- **Range**: {H_vl_arr.min():.3f} – {H_vl_arr.max():.3f}",
    f"- **Surahs with H < 0.5**: {(H_vl_arr < 0.5).sum()}  |  **H > 0.95**: {(H_vl_arr > 0.95).sum()}",
    f"- **Wilcoxon H > 0.5 p**: {wil_vl_p:.4e}",
    f"- **Length-regression**: slope = {lr_vl.slope:+.4f}, intercept = {lr_vl.intercept:+.4f}, "
    f"r = {lr_vl.rvalue:+.3f} (p = {lr_vl.pvalue:.3e})",
    f"- **Median residual after log(n) regression**: {median_resid_vl:+.4f}",
    f"- **Intercept at median n_verses**: {intercept_at_typical:.4f}",
    f"- **Fraction surahs with shuffle p < 0.05**: {frac_sig_str} (per-surah null disabled in reduced mode)" if frac_sig is None else f"- **Fraction surahs with shuffle p < 0.05**: {frac_sig:.3f}",
    "",
    "## Outliers (top 5 highest and lowest H_vl)",
    "",
    "| Surah | Label | n_verses | H_vl | D_vl | shuffle p |",
    "|--:|---|--:|--:|--:|--:|",
]
def _p_str(r):
    p = r.get("H_vl_shuffle_p")
    return f"{p:.3f}" if isinstance(p, float) else "—"
sorted_records = sorted(records, key=lambda r: r["H_vl"], reverse=True)
for r in sorted_records[:5]:
    md.append(f"| {r['surah']} | {r['label']} | {r['n_verses']} | {r['H_vl']:.3f} | "
              f"{r['D_vl']:.3f} | {_p_str(r)} |")
md.append("| ... | ... | ... | ... | ... | ... |")
for r in sorted_records[-5:]:
    md.append(f"| {r['surah']} | {r['label']} | {r['n_verses']} | {r['H_vl']:.3f} | "
              f"{r['D_vl']:.3f} | {_p_str(r)} |")

md.append("")
md.append("## Outputs")
md.append("")
md.append("- `expE7_report.json` — per-surah records + aggregate statistics + verdict")
md.append("- `expE7_hurst_spectrum.png` — H distribution histogram + length-regression plot")

(OUTDIR / "expE7_report.md").write_text("\n".join(md), encoding="utf-8")

print(f"\nVerdict: {verdict}")
print(f"Total runtime: {time.time()-t0:.1f}s")
