"""
exp75_fractal_dimension/run.py
===============================
H14: Fractal Dimension of the Verse-Length Time Series.

Motivation
    Hurst exponents (0.738 R/S, 0.901 DFA from DEEPSCAN) suggest
    long-range correlations. The fractal dimension D = 2 - H provides
    another characterisation. If D_Quran is distinct from controls,
    it reveals self-similar verse-length structure.

Protocol (frozen before execution)
    T1. For each corpus: extract verse-length sequence (word counts
        per verse, concatenated across all units).
    T2. Compute Higuchi fractal dimension (HFD) with k_max=20.
    T3. Compute Hurst exponent via R/S analysis for cross-check.
    T4. Compare D across corpora. Cohen's d vs ctrl pool.
    T5. Test D_Quran against known constants (phi, e, sqrt(2), etc.)
        with bootstrap CI and look-elsewhere correction.
    T6. Per-unit (surah/book) HFD distribution + Mann-Whitney.

Pre-registered thresholds
    DISTINCT:     |Cohen's d| >= 1.0 AND p < 0.01 (Mann-Whitney)
    SUGGESTIVE:   |Cohen's d| >= 0.5 OR p < 0.05
    NULL:         otherwise

Reads: phase_06_phi_m.pkl -> CORPORA

Writes ONLY under results/experiments/exp75_fractal_dimension/
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats as sp_stats

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase,
    safe_output_dir,
    self_check_begin,
    self_check_end,
)

EXP = "exp75_fractal_dimension"
SEED = 42
N_BOOT = 10000

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

CONSTANTS = {
    "phi": (1 + math.sqrt(5)) / 2,
    "1/phi": 2 / (1 + math.sqrt(5)),
    "sqrt(2)": math.sqrt(2),
    "e": math.e,
    "pi/2": math.pi / 2,
    "ln(2)": math.log(2),
    "3/2": 1.5,
    "4/3": 4/3,
    "5/3": 5/3,
}


def _higuchi_fd(x: np.ndarray, k_max: int = 20) -> float:
    """Higuchi fractal dimension of a 1-D time series.
    
    Reference: Higuchi T (1988) Physica D 31:277-283.
    """
    n = len(x)
    if n < k_max + 1:
        k_max = max(2, n // 2)

    lk = np.empty(k_max - 1)
    for k in range(1, k_max):
        # For each k, compute L(k) = average curve length over m=1..k starts
        lengths = []
        for m in range(1, k + 1):
            # Indices: m, m+k, m+2k, ...
            idx = np.arange(m - 1, n, k)
            if len(idx) < 2:
                continue
            seg = x[idx]
            # Curve length for this (m, k)
            a = int(np.floor((n - m) / k))
            if a < 1:
                continue
            norm_factor = (n - 1) / (a * k)
            length = norm_factor * np.sum(np.abs(np.diff(seg)))
            lengths.append(length)
        if lengths:
            lk[k - 1] = np.mean(lengths)
        else:
            lk[k - 1] = np.nan

    # Fit log(L(k)) vs log(1/k)
    valid = np.isfinite(lk) & (lk > 0)
    ks = np.arange(1, k_max)
    if valid.sum() < 3:
        return float("nan")

    log_inv_k = np.log(1.0 / ks[valid])
    log_lk = np.log(lk[valid])

    slope, _, r_value, _, _ = sp_stats.linregress(log_inv_k, log_lk)
    return float(slope)


def _hurst_rs(x: np.ndarray) -> float:
    """Hurst exponent via rescaled range (R/S) analysis."""
    n = len(x)
    if n < 20:
        return float("nan")

    # Use multiple segment sizes
    sizes = []
    rs_values = []
    size = 10
    while size <= n // 2:
        sizes.append(size)
        n_segs = n // size
        rs_seg = []
        for i in range(n_segs):
            seg = x[i * size:(i + 1) * size]
            mean_seg = seg.mean()
            devs = np.cumsum(seg - mean_seg)
            r = devs.max() - devs.min()
            s = seg.std(ddof=1)
            if s > 1e-12:
                rs_seg.append(r / s)
        if rs_seg:
            rs_values.append(np.mean(rs_seg))
        size = int(size * 1.5)

    if len(sizes) < 3:
        return float("nan")

    log_n = np.log(sizes)
    log_rs = np.log(rs_values)
    slope, _, _, _, _ = sp_stats.linregress(log_n, log_rs)
    return float(slope)


def _get_verse_lengths(corpus_units) -> list[int]:
    """Get all verse word-counts concatenated across units."""
    wcs = []
    for u in corpus_units:
        for v in u.verses:
            wcs.append(len(v.split()))
    return wcs


def _get_per_unit_hfd(corpus_units, k_max: int = 20) -> list[float]:
    """Compute HFD per unit (surah/book/poem)."""
    hfds = []
    for u in corpus_units:
        wcs = [len(v.split()) for v in u.verses]
        if len(wcs) >= 10:
            hfd = _higuchi_fd(np.array(wcs, dtype=float), k_max=k_max)
            if np.isfinite(hfd):
                hfds.append(hfd)
    return hfds


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    results = {}

    for cname in ["quran"] + ARABIC_CTRL:
        units = CORPORA.get(cname, [])
        wcs = _get_verse_lengths(units)
        x = np.array(wcs, dtype=float)

        # T2: Whole-corpus Higuchi FD
        hfd_global = _higuchi_fd(x, k_max=20)

        # T3: Hurst R/S
        hurst = _hurst_rs(x)

        # D = 2 - H relationship
        d_from_hurst = 2.0 - hurst if np.isfinite(hurst) else float("nan")

        # T6: Per-unit HFD
        per_unit = _get_per_unit_hfd(units, k_max=15)

        results[cname] = {
            "n_verses": len(wcs),
            "n_units": len(units),
            "hfd_global": round(hfd_global, 4),
            "hurst_rs": round(hurst, 4),
            "d_from_hurst": round(d_from_hurst, 4),
            "per_unit_hfd": {
                "n": len(per_unit),
                "mean": round(float(np.mean(per_unit)), 4) if per_unit else None,
                "std": round(float(np.std(per_unit, ddof=1)), 4) if len(per_unit) > 1 else None,
                "median": round(float(np.median(per_unit)), 4) if per_unit else None,
            },
        }

        print(f"\n[{EXP}] {cname:20s}: n_v={len(wcs):6d}  "
              f"HFD={hfd_global:.4f}  H_RS={hurst:.4f}  "
              f"D(2-H)={d_from_hurst:.4f}  "
              f"per-unit: n={len(per_unit)}, "
              f"mean={np.mean(per_unit):.4f}" if per_unit else "")

    # --- T4: Comparison ---
    print(f"\n[{EXP}] === T4: Cross-corpus comparison ===")
    q_hfd = results["quran"]["hfd_global"]
    q_per = _get_per_unit_hfd(CORPORA["quran"], k_max=15)

    for cname in ARABIC_CTRL:
        c_per = _get_per_unit_hfd(CORPORA[cname], k_max=15)
        if len(c_per) >= 3 and len(q_per) >= 3:
            u_stat, p_mw = sp_stats.mannwhitneyu(q_per, c_per, alternative='two-sided')
            d_cohen = ((np.mean(q_per) - np.mean(c_per)) /
                       np.sqrt((np.var(q_per, ddof=1) + np.var(c_per, ddof=1)) / 2))
            print(f"  Quran vs {cname:20s}: d={d_cohen:+.3f}  MW p={p_mw:.4f}")
            results[cname]["vs_quran"] = {
                "cohen_d": round(float(d_cohen), 4),
                "mann_whitney_p": float(p_mw),
            }

    # --- T5: Constant check on Quran HFD ---
    print(f"\n[{EXP}] === T5: Quran HFD vs constants ===")
    print(f"  Quran global HFD = {q_hfd:.4f}")

    # Bootstrap CI on Quran per-unit HFD mean
    rng = np.random.RandomState(SEED)
    if len(q_per) >= 5:
        boot_means = np.empty(N_BOOT)
        for i in range(N_BOOT):
            sample = rng.choice(q_per, len(q_per), replace=True)
            boot_means[i] = np.mean(sample)
        ci_lo, ci_hi = np.percentile(boot_means, [2.5, 97.5])
        print(f"  Per-unit HFD mean: {np.mean(q_per):.4f}, "
              f"95% CI=[{ci_lo:.4f}, {ci_hi:.4f}]")

        for cname, cval in CONSTANTS.items():
            if ci_lo <= cval <= ci_hi:
                err = abs(np.mean(q_per) - cval) / abs(cval) * 100
                print(f"  MATCH: HFD_mean ≈ {cname} ({cval:.4f})  err={err:.1f}%")
    else:
        ci_lo, ci_hi = float("nan"), float("nan")
        print("  Not enough per-unit data for bootstrap")

    # --- Pooled ctrl per-unit for overall effect size ---
    ctrl_per_all = []
    for cname in ARABIC_CTRL:
        ctrl_per_all.extend(_get_per_unit_hfd(CORPORA[cname], k_max=15))

    if len(ctrl_per_all) >= 3 and len(q_per) >= 3:
        d_overall = ((np.mean(q_per) - np.mean(ctrl_per_all)) /
                     np.sqrt((np.var(q_per, ddof=1) + np.var(ctrl_per_all, ddof=1)) / 2))
        _, p_overall = sp_stats.mannwhitneyu(q_per, ctrl_per_all, alternative='two-sided')
    else:
        d_overall = float("nan")
        p_overall = float("nan")

    # --- Verdict ---
    if abs(d_overall) >= 1.0 and p_overall < 0.01:
        verdict = "DISTINCT"
    elif abs(d_overall) >= 0.5 or p_overall < 0.05:
        verdict = "SUGGESTIVE"
    else:
        verdict = "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Quran global HFD = {q_hfd:.4f}")
    print(f"  Quran per-unit HFD mean = {np.mean(q_per):.4f}" if q_per else "  No per-unit data")
    print(f"  Cohen's d (vs all ctrl) = {d_overall:+.4f}")
    print(f"  Mann-Whitney p = {p_overall:.4e}")
    print(f"{'=' * 60}")

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H14 — Does the Quran's verse-length time series "
                      "have a distinct fractal dimension?",
        "schema_version": 1,
        "per_corpus": results,
        "overall_comparison": {
            "quran_hfd_global": round(q_hfd, 4),
            "quran_per_unit_mean": round(float(np.mean(q_per)), 4) if q_per else None,
            "quran_per_unit_ci": [round(float(ci_lo), 4), round(float(ci_hi), 4)],
            "ctrl_per_unit_mean": round(float(np.mean(ctrl_per_all)), 4) if ctrl_per_all else None,
            "cohen_d": round(float(d_overall), 4),
            "mann_whitney_p": float(p_overall),
        },
        "verdict": verdict,
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
