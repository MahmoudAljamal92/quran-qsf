"""
exp79_ar1_decorrelation/run.py
================================
H6: The AR(1) Decorrelation Law for Oral Texts.

Motivation
    Quran phi_1 = +0.141 (d = +1.095): strong lag-1 but rapid
    decorrelation ("punchy" pattern). H6 asks whether phi_1 * k*
    (where k* = decorrelation lag) is a conserved quantity.

Protocol (frozen before execution)
    T1. Per unit: fit AR(1) to verse-length sequence -> phi_1.
    T2. Per unit: compute lag-k Pearson autocorrelation for k=1..20,
        find k* = first lag where |rho_k| < 0.05.
    T3. Per corpus: aggregate phi_1 and k*.
    T4. Test phi_1 * k* = constant across corpora.
    T5. 2D (phi_1, k*) outlier test for Quran.
    T6. Cohen's d for phi_1 and k* separately.

Pre-registered thresholds
    CONSERVATION_LAW:  CV(phi_1 * k*) < 0.15 across corpora
    SUGGESTIVE:        Quran is >1σ outlier in (phi_1, k*) space
    NULL:              otherwise

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

EXP = "exp79_ar1_decorrelation"
SEED = 42
MAX_LAG = 20
MIN_VERSES = 15

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]


def _ar1_fit(x: np.ndarray) -> float:
    """AR(1) coefficient via OLS: x[t] = phi * x[t-1] + eps."""
    if len(x) < 5:
        return float("nan")
    x_lag = x[:-1]
    x_now = x[1:]
    x_lag_dm = x_lag - x_lag.mean()
    x_now_dm = x_now - x_now.mean()
    denom = np.dot(x_lag_dm, x_lag_dm)
    if denom < 1e-12:
        return 0.0
    return float(np.dot(x_lag_dm, x_now_dm) / denom)


def _decorrelation_lag(x: np.ndarray, max_lag: int = MAX_LAG,
                        threshold: float = 0.05) -> int:
    """Find first lag k where |rho_k| < threshold."""
    n = len(x)
    if n < max_lag + 2:
        max_lag = max(1, n - 2)
    x_dm = x - x.mean()
    var = np.dot(x_dm, x_dm) / n
    if var < 1e-12:
        return 1
    for k in range(1, max_lag + 1):
        rho = np.dot(x_dm[:n - k], x_dm[k:]) / (n * var)
        if abs(rho) < threshold:
            return k
    return max_lag + 1  # never decorrelated within range


def _analyse_unit(verses) -> dict | None:
    """Compute phi_1 and k* for one unit."""
    wcs = [len(v.split()) for v in verses]
    if len(wcs) < MIN_VERSES:
        return None
    x = np.array(wcs, dtype=float)
    phi1 = _ar1_fit(x)
    kstar = _decorrelation_lag(x)
    product = phi1 * kstar
    return {"phi1": phi1, "kstar": kstar, "product": product}


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
        phi1s = []
        kstars = []
        products = []

        for u in units:
            r = _analyse_unit(u.verses)
            if r is None:
                continue
            phi1s.append(r["phi1"])
            kstars.append(r["kstar"])
            products.append(r["product"])

        phi1_arr = np.array(phi1s)
        kstar_arr = np.array(kstars)
        prod_arr = np.array(products)

        results[cname] = {
            "n_units": len(phi1s),
            "phi1_mean": round(float(phi1_arr.mean()), 4) if phi1s else None,
            "phi1_std": round(float(phi1_arr.std(ddof=1)), 4) if len(phi1s) > 1 else None,
            "phi1_median": round(float(np.median(phi1_arr)), 4) if phi1s else None,
            "kstar_mean": round(float(kstar_arr.mean()), 2) if kstars else None,
            "kstar_median": round(float(np.median(kstar_arr)), 1) if kstars else None,
            "product_mean": round(float(prod_arr.mean()), 4) if products else None,
            "product_std": round(float(prod_arr.std(ddof=1)), 4) if len(products) > 1 else None,
            "_phi1s": phi1s,
            "_kstars": kstars,
            "_products": products,
        }

        print(f"[{EXP}] {cname:20s}: n={len(phi1s):4d}  "
              f"φ₁={phi1_arr.mean():.4f}±{phi1_arr.std(ddof=1):.4f}  "
              f"k*={kstar_arr.mean():.2f}  "
              f"φ₁·k*={prod_arr.mean():.4f}±{prod_arr.std(ddof=1):.4f}")

    # --- T4: Conservation test ---
    print(f"\n[{EXP}] === T4: phi_1 * k* conservation test ===")
    corpus_products = [results[n]["product_mean"] for n in all_names
                       if results[n]["product_mean"] is not None]
    corpus_names = [n for n in all_names if results[n]["product_mean"] is not None]

    prod_mean = np.mean(corpus_products)
    prod_std = np.std(corpus_products, ddof=1)
    prod_cv = prod_std / abs(prod_mean) if abs(prod_mean) > 0 else float("inf")
    print(f"  Cross-corpus φ₁·k*: mean={prod_mean:.4f}, std={prod_std:.4f}, CV={prod_cv:.4f}")
    for n, p in zip(corpus_names, corpus_products):
        print(f"    {n:20s}: φ₁·k* = {p:.4f}")

    # --- T5: 2D outlier test ---
    print(f"\n[{EXP}] === T5: 2D (φ₁, k*) comparison ===")
    q_phi1 = results["quran"]["_phi1s"]
    q_kstar = results["quran"]["_kstars"]

    for cname in ARABIC_CTRL:
        c_phi1 = results[cname]["_phi1s"]
        c_kstar = results[cname]["_kstars"]
        if len(c_phi1) >= 3 and len(q_phi1) >= 3:
            d_phi1 = ((np.mean(q_phi1) - np.mean(c_phi1)) /
                      np.sqrt((np.var(q_phi1, ddof=1) + np.var(c_phi1, ddof=1)) / 2))
            d_kstar = ((np.mean(q_kstar) - np.mean(c_kstar)) /
                       np.sqrt((np.var(q_kstar, ddof=1) + np.var(c_kstar, ddof=1)) / 2))
            print(f"  Quran vs {cname:20s}: d(φ₁)={d_phi1:+.3f}  d(k*)={d_kstar:+.3f}")
            results[cname]["vs_quran_d_phi1"] = round(float(d_phi1), 4)
            results[cname]["vs_quran_d_kstar"] = round(float(d_kstar), 4)

    # --- T6: Pooled ctrl comparison ---
    print(f"\n[{EXP}] === T6: Quran vs pooled ctrl ===")
    ctrl_phi1 = []
    ctrl_kstar = []
    ctrl_prod = []
    for cname in ARABIC_CTRL:
        ctrl_phi1.extend(results[cname]["_phi1s"])
        ctrl_kstar.extend(results[cname]["_kstars"])
        ctrl_prod.extend(results[cname]["_products"])

    d_phi1_all = ((np.mean(q_phi1) - np.mean(ctrl_phi1)) /
                  np.sqrt((np.var(q_phi1, ddof=1) + np.var(ctrl_phi1, ddof=1)) / 2))
    d_kstar_all = ((np.mean(q_kstar) - np.mean(ctrl_kstar)) /
                   np.sqrt((np.var(q_kstar, ddof=1) + np.var(ctrl_kstar, ddof=1)) / 2))
    d_prod_all = ((np.mean(results["quran"]["_products"]) - np.mean(ctrl_prod)) /
                  np.sqrt((np.var(results["quran"]["_products"], ddof=1) +
                           np.var(ctrl_prod, ddof=1)) / 2))
    _, p_phi1 = sp_stats.mannwhitneyu(q_phi1, ctrl_phi1, alternative='two-sided')
    _, p_kstar = sp_stats.mannwhitneyu(q_kstar, ctrl_kstar, alternative='two-sided')

    print(f"  d(φ₁) = {d_phi1_all:+.4f}, MW p = {p_phi1:.4e}")
    print(f"  d(k*) = {d_kstar_all:+.4f}, MW p = {p_kstar:.4e}")
    print(f"  d(φ₁·k*) = {d_prod_all:+.4f}")

    # --- Verdict ---
    if prod_cv < 0.15:
        verdict = "CONSERVATION_LAW"
    elif abs(d_phi1_all) > 1.0 or abs(d_kstar_all) > 1.0:
        verdict = "SUGGESTIVE"
    else:
        verdict = "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  φ₁·k* CV = {prod_cv:.4f} (threshold < 0.15 for conservation law)")
    print(f"  Quran φ₁ = {results['quran']['phi1_mean']}, "
          f"k* = {results['quran']['kstar_mean']}, "
          f"product = {results['quran']['product_mean']}")
    print(f"  d(φ₁) vs ctrl = {d_phi1_all:+.4f}, d(k*) = {d_kstar_all:+.4f}")
    print(f"{'=' * 60}")

    # Clean internal lists before saving
    report_results = {}
    for k, v in results.items():
        report_results[k] = {kk: vv for kk, vv in v.items() if not kk.startswith("_")}

    report = {
        "experiment": EXP,
        "hypothesis": "H6 — Is phi_1 * k* a conserved quantity across corpora?",
        "schema_version": 1,
        "per_corpus": report_results,
        "conservation_test": {
            "cross_corpus_product_mean": round(float(prod_mean), 4),
            "cross_corpus_product_std": round(float(prod_std), 4),
            "cross_corpus_product_cv": round(float(prod_cv), 4),
        },
        "quran_vs_ctrl": {
            "d_phi1": round(float(d_phi1_all), 4),
            "p_phi1": float(p_phi1),
            "d_kstar": round(float(d_kstar_all), 4),
            "p_kstar": float(p_kstar),
            "d_product": round(float(d_prod_all), 4),
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
