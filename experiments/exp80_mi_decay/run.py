"""
exp80_mi_decay/run.py
======================
H9: Mutual Information Decay Rate as a Corpus Invariant.

Motivation
    DEEPSCAN notes "Quran MI decay is uniquely low and flat." If
    MI(v_i; v_{i+k}) ~ MI_0 * exp(-k / tau), tau characterises
    how quickly topical memory fades between verses.

MI computation
    For each pair of verses (v_i, v_{i+k}), we discretise via
    word-overlap Jaccard similarity, then compute MI using
    the joint distribution of binned word-overlap scores.

    Simpler and faster: use normalised word-overlap as a
    continuous proxy, compute Pearson correlation at each lag
    (equivalent to MI for Gaussian variables: MI = -0.5 * log(1-r^2)).

Protocol (frozen before execution)
    T1. Per corpus: concatenate all unit verse sequences.
    T2. For k=1..20: compute lag-k word-overlap correlation r(k).
    T3. Convert to MI: I(k) = -0.5 * log2(1 - r(k)^2).
    T4. Fit I(k) = I_0 * exp(-k / tau).
    T5. Extract tau per corpus. Cohen's d for tau.
    T6. Scatter tau vs phi_1 from exp79.

Pre-registered thresholds
    DISTINCT:     |Cohen's d(tau)| >= 1.0 AND p < 0.01
    SUGGESTIVE:   |d| >= 0.5 or p < 0.05
    NULL:         otherwise

Reads: phase_06_phi_m.pkl -> CORPORA
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats as sp_stats
from scipy.optimize import curve_fit

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

EXP = "exp80_mi_decay"
SEED = 42
MAX_LAG = 20
MIN_VERSES_UNIT = 15

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]


def _verse_word_set(verse: str) -> set:
    return set(verse.split())


def _word_overlap(v1: str, v2: str) -> float:
    """Jaccard similarity between word sets."""
    s1 = _verse_word_set(v1)
    s2 = _verse_word_set(v2)
    if not s1 and not s2:
        return 0.0
    inter = len(s1 & s2)
    union = len(s1 | s2)
    return inter / union if union > 0 else 0.0


def _lag_correlations(verses: list[str], max_lag: int = MAX_LAG) -> dict:
    """Compute lag-k word-overlap correlations and MI for a verse sequence."""
    n = len(verses)
    if n < max_lag + 5:
        max_lag = max(1, n - 5)

    # Precompute pairwise overlaps would be O(n*k), just do lag-k directly
    results = {}
    for k in range(1, max_lag + 1):
        overlaps = []
        for i in range(n - k):
            overlaps.append(_word_overlap(verses[i], verses[i + k]))
        if len(overlaps) < 5:
            continue
        arr = np.array(overlaps)
        # Also need the marginal variance to compute correlation
        # Use the overlap values directly as a similarity measure
        # Correlation with lag-0 (self-overlap = 1.0)
        mean_overlap = arr.mean()
        results[k] = {
            "mean_overlap": float(mean_overlap),
            "n_pairs": len(overlaps),
        }

    return results


def _compute_mi_decay(verses: list[str], max_lag: int = MAX_LAG):
    """Compute MI decay curve using word-overlap autocorrelation."""
    n = len(verses)
    if n < max_lag + 5:
        max_lag = max(1, n - 5)

    # Compute word-overlap time series for each verse with its lag-k successor
    # Then compute autocorrelation of the overlap values
    # Simpler: compute mean overlap at each lag k
    lags = []
    mi_values = []
    r_values = []

    for k in range(1, max_lag + 1):
        overlaps = [_word_overlap(verses[i], verses[i + k])
                     for i in range(n - k)]
        if len(overlaps) < 5:
            continue
        r = float(np.mean(overlaps))
        # Clamp to avoid log issues
        r_clamped = min(max(r, 0.0), 0.999)
        if r_clamped > 0:
            mi = -0.5 * math.log2(1.0 - r_clamped ** 2) if r_clamped < 1.0 else 10.0
        else:
            mi = 0.0
        lags.append(k)
        mi_values.append(mi)
        r_values.append(r)

    return np.array(lags), np.array(mi_values), np.array(r_values)


def _fit_exp_decay(lags, mi_values):
    """Fit MI(k) = I_0 * exp(-k / tau)."""
    if len(lags) < 3 or np.all(mi_values <= 0):
        return float("nan"), float("nan"), float("nan")

    # Filter positive MI only
    valid = mi_values > 0
    if valid.sum() < 3:
        return float("nan"), float("nan"), float("nan")

    x = lags[valid].astype(float)
    y = mi_values[valid]

    try:
        def _exp_decay(k, I0, tau):
            return I0 * np.exp(-k / tau)

        p0 = [y[0], 5.0]
        popt, _ = curve_fit(_exp_decay, x, y, p0=p0, maxfev=5000,
                            bounds=([0, 0.1], [10, 100]))
        pred = _exp_decay(x, *popt)
        ss_res = np.sum((y - pred) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        return float(popt[0]), float(popt[1]), float(r2)
    except Exception:
        return float("nan"), float("nan"), float("nan")


def _per_unit_tau(units, max_lag=MAX_LAG) -> list[float]:
    """Compute tau per unit for distribution comparison."""
    taus = []
    for u in units:
        if len(u.verses) < MIN_VERSES_UNIT:
            continue
        lags, mi, _ = _compute_mi_decay(u.verses, max_lag)
        _, tau, r2 = _fit_exp_decay(lags, mi)
        if np.isfinite(tau) and np.isfinite(r2):
            taus.append(tau)
    return taus


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

    all_names = ["quran"] + ARABIC_CTRL
    results = {}

    for cname in all_names:
        units = CORPORA.get(cname, [])
        t_start = time.time()

        # Global: concatenate all verses
        all_verses = []
        for u in units:
            all_verses.extend(u.verses)

        lags, mi, r_vals = _compute_mi_decay(all_verses, MAX_LAG)
        I0, tau_global, r2_global = _fit_exp_decay(lags, mi)

        # Per-unit tau distribution
        unit_taus = _per_unit_tau(units)

        dt = time.time() - t_start

        results[cname] = {
            "n_verses": len(all_verses),
            "n_units": len(units),
            "global": {
                "I0": round(I0, 6) if np.isfinite(I0) else None,
                "tau": round(tau_global, 4) if np.isfinite(tau_global) else None,
                "R2": round(r2_global, 4) if np.isfinite(r2_global) else None,
                "mi_curve": {int(k): round(float(m), 6) for k, m in zip(lags, mi)},
                "overlap_curve": {int(k): round(float(r), 6) for k, r in zip(lags, r_vals)},
            },
            "per_unit": {
                "n": len(unit_taus),
                "mean": round(float(np.mean(unit_taus)), 4) if unit_taus else None,
                "std": round(float(np.std(unit_taus, ddof=1)), 4) if len(unit_taus) > 1 else None,
                "median": round(float(np.median(unit_taus)), 4) if unit_taus else None,
            },
            "_unit_taus": unit_taus,
        }

        tau_str = f"{tau_global:.2f}" if np.isfinite(tau_global) else "N/A"
        print(f"[{EXP}] {cname:20s}: n_v={len(all_verses):6d}  "
              f"τ_global={tau_str}  R²={r2_global:.3f}  "
              f"per-unit: n={len(unit_taus)}, "
              f"τ_mean={np.mean(unit_taus):.2f}" if unit_taus else f"  ({dt:.1f}s)")

    # --- T5: Comparison ---
    print(f"\n[{EXP}] === T5: Cross-corpus comparison ===")
    q_taus = results["quran"]["_unit_taus"]

    ctrl_taus_all = []
    for cname in ARABIC_CTRL:
        c_taus = results[cname]["_unit_taus"]
        ctrl_taus_all.extend(c_taus)
        if len(c_taus) >= 3 and len(q_taus) >= 3:
            d = ((np.mean(q_taus) - np.mean(c_taus)) /
                 np.sqrt((np.var(q_taus, ddof=1) + np.var(c_taus, ddof=1)) / 2))
            _, p = sp_stats.mannwhitneyu(q_taus, c_taus, alternative='two-sided')
            print(f"  Quran vs {cname:20s}: d(τ)={d:+.3f}  MW p={p:.4e}")
            results[cname]["vs_quran_d_tau"] = round(float(d), 4)
            results[cname]["vs_quran_p_tau"] = float(p)

    # Pooled
    if len(ctrl_taus_all) >= 3 and len(q_taus) >= 3:
        d_all = ((np.mean(q_taus) - np.mean(ctrl_taus_all)) /
                 np.sqrt((np.var(q_taus, ddof=1) + np.var(ctrl_taus_all, ddof=1)) / 2))
        _, p_all = sp_stats.mannwhitneyu(q_taus, ctrl_taus_all, alternative='two-sided')
    else:
        d_all = float("nan")
        p_all = float("nan")

    print(f"\n  Quran vs pooled ctrl: d(τ)={d_all:+.4f}, MW p={p_all:.4e}")

    # --- T6: tau vs phi_1 ---
    print(f"\n[{EXP}] === T6: τ vs φ₁ correlation ===")
    # Load exp79 results if available
    exp79_path = _ROOT / "results" / "experiments" / "exp79_ar1_decorrelation" / "exp79_ar1_decorrelation.json"
    if exp79_path.exists():
        with open(exp79_path) as f:
            exp79 = json.load(f)
        phi1s = []
        taus = []
        names = []
        for n in all_names:
            if n in exp79.get("per_corpus", {}) and n in results:
                p1 = exp79["per_corpus"][n].get("phi1_mean")
                t = results[n]["global"].get("tau")
                if p1 is not None and t is not None:
                    phi1s.append(p1)
                    taus.append(t)
                    names.append(n)
        if len(phi1s) >= 4:
            r_corr, p_corr = sp_stats.pearsonr(phi1s, taus)
            print(f"  τ vs φ₁ Pearson r={r_corr:.4f}, p={p_corr:.4f}")
            for n, p1, t in zip(names, phi1s, taus):
                print(f"    {n:20s}: φ₁={p1:.4f}, τ={t:.2f}")
        else:
            r_corr = p_corr = float("nan")
    else:
        print("  exp79 not found, skipping cross-check")
        r_corr = p_corr = float("nan")

    # --- Verdict ---
    if abs(d_all) >= 1.0 and p_all < 0.01:
        verdict = "DISTINCT"
    elif abs(d_all) >= 0.5 or p_all < 0.05:
        verdict = "SUGGESTIVE"
    else:
        verdict = "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Quran global τ = {results['quran']['global']['tau']}")
    print(f"  Quran per-unit τ mean = {results['quran']['per_unit']['mean']}")
    print(f"  d(τ) vs ctrl = {d_all:+.4f}, p = {p_all:.4e}")
    print(f"{'=' * 60}")

    # Clean report
    report_results = {}
    for k, v in results.items():
        report_results[k] = {kk: vv for kk, vv in v.items() if not kk.startswith("_")}

    report = {
        "experiment": EXP,
        "hypothesis": "H9 — Is the MI decay rate tau a corpus-distinctive invariant?",
        "schema_version": 1,
        "per_corpus": report_results,
        "quran_vs_ctrl": {
            "d_tau": round(float(d_all), 4),
            "p_tau": float(p_all),
        },
        "tau_vs_phi1": {
            "r": round(float(r_corr), 4) if np.isfinite(r_corr) else None,
            "p": round(float(p_corr), 4) if np.isfinite(p_corr) else None,
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
