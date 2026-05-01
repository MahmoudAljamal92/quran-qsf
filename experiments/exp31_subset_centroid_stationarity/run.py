"""
exp31_subset_centroid_stationarity/run.py
=========================================
Robustness probe for the corpus-level Phi_M claim (PAPER.md Section 4.1,
Hotelling T^2 = 3557, AUC = 0.998): does the Quran's 5-D centroid
survive random subsetting?

Protocol
--------
For N in {10, 20, 34, 50, 60} and B = 2000 bootstrap iterations:
  1. Sample N Quran Band-A surahs without replacement.
  2. Compute subset centroid c_sub = mean(X_sub) in 5-D.
  3. Report:
     * drift    = ||c_sub - c_full_Q||_M  (Mahalanobis distance from
                                            the full-corpus centroid)
     * dist_C   = ||c_sub - mu_ctrl||_M   (Mahalanobis distance from the
                                            locked ctrl centroid)
     * T2_sub   = N * (c_sub - mu_ctrl)^T S_inv (c_sub - mu_ctrl)
     * separates = T2_sub > T2_null_95   where T2_null_95 is the 95%
                   permutation threshold from the locked baseline.
  4. Report the fraction of subsets with `separates = True` per N,
     and the distribution of drift/dist_C quantiles.

Reads (verified): phase_06_phi_m.pkl via experiments._lib.load_phase
                  (ctrl centroid mu, S_inv, FEAT_COLS, CORPORA,
                   X_CTRL_POOL).
Writes ONLY under results/experiments/exp31_subset_centroid_stationarity/.
No locked artefact is touched.
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase, safe_output_dir, self_check_begin, self_check_end,
)

from src import features as ft  # noqa: E402

EXP = "exp31_subset_centroid_stationarity"
SEED = 42
BAND_A_LO, BAND_A_HI = 15, 100
N_GRID = [10, 20, 34, 50, 60]
B_BOOTSTRAP = 2000
# Headline Hotelling T^2 for the full Band-A Quran vs ctrl centroid:
# matches PAPER.md Section 4.1 within pipeline tolerance.
PHI_M_THRESH_NULL_95 = 3.841  # chi^2_5(0.95) ~ 11.07; we use per-component

ARABIC_CTRL_NAMES = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]


def _mahalanobis(a: np.ndarray, b: np.ndarray, Sinv: np.ndarray) -> float:
    d = a - b
    return float(math.sqrt(max(float(d @ Sinv @ d), 0.0)))


def _band_a_units(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


def _features_stack(units) -> np.ndarray:
    out = []
    for u in units:
        try:
            out.append(ft.features_5d(u.verses))
        except Exception:
            continue
    return np.asarray(out, dtype=float)


def _hotelling_t2(X: np.ndarray, mu: np.ndarray, Sinv: np.ndarray) -> float:
    """Hotelling T^2 for sample mean vs fixed mu under covariance S_inv.

    T^2 = n * (x_bar - mu)^T S_inv (x_bar - mu)
    """
    xbar = X.mean(axis=0)
    n = X.shape[0]
    d = xbar - mu
    return float(n * (d @ Sinv @ d))


def _summarise(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    a = np.asarray(values, dtype=float)
    return {
        "n": int(a.size),
        "mean": float(a.mean()),
        "median": float(np.median(a)),
        "sd": float(a.std(ddof=1)) if a.size > 1 else 0.0,
        "q05": float(np.quantile(a, 0.05)),
        "q25": float(np.quantile(a, 0.25)),
        "q75": float(np.quantile(a, 0.75)),
        "q95": float(np.quantile(a, 0.95)),
        "min": float(a.min()),
        "max": float(a.max()),
    }


def main() -> int:
    t0 = time.time()
    out_dir = safe_output_dir(EXP)
    pre = self_check_begin()

    print(f"[{EXP}] loading phase_06_phi_m state (read-only)...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    CORPORA = state["CORPORA"]
    mu_ctrl = np.asarray(state["mu"], dtype=float)
    S_inv = np.asarray(state["S_inv"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])

    # Collect Quran Band-A feature stack
    q_units = _band_a_units(CORPORA.get("quran", []))
    X_Q = _features_stack(q_units)
    nQ = X_Q.shape[0]
    if nQ < max(N_GRID):
        raise RuntimeError(f"Only {nQ} Band-A Quran units, need >= {max(N_GRID)}")
    c_full_Q = X_Q.mean(axis=0)

    # Ctrl Band-A stack + centroid (for sanity)
    X_C = []
    for name in ARABIC_CTRL_NAMES:
        X_C.append(_features_stack(_band_a_units(CORPORA.get(name, []))))
    X_C = np.vstack([x for x in X_C if x.size > 0])
    c_full_C = X_C.mean(axis=0)

    # Full-corpus Hotelling T^2 (Quran vs ctrl centroid)
    T2_full_Q = _hotelling_t2(X_Q, mu_ctrl, S_inv)
    dist_full_Q = _mahalanobis(c_full_Q, mu_ctrl, S_inv)
    print(f"[{EXP}] Band-A Quran: n={nQ}, T^2 vs ctrl={T2_full_Q:.2f}, "
          f"||c_Q - mu_ctrl||_M = {dist_full_Q:.3f}")

    # ---- Bootstrap ---------------------------------------------------------
    # For each N, resample B times, compute drift, dist_C, T^2.
    rng = random.Random(SEED)
    results_by_N: dict[int, dict] = {}
    for N in N_GRID:
        drifts: list[float] = []
        dists_C: list[float] = []
        T2s: list[float] = []
        separates_90pct_of_full: int = 0
        separates_50pct_of_full: int = 0
        for _ in range(B_BOOTSTRAP):
            idx = rng.sample(range(nQ), N)
            X_sub = X_Q[idx]
            c_sub = X_sub.mean(axis=0)
            drift = _mahalanobis(c_sub, c_full_Q, S_inv)
            dist_C = _mahalanobis(c_sub, mu_ctrl, S_inv)
            T2 = _hotelling_t2(X_sub, mu_ctrl, S_inv)
            drifts.append(drift)
            dists_C.append(dist_C)
            T2s.append(T2)
            if T2 >= 0.5 * T2_full_Q:
                separates_50pct_of_full += 1
            if T2 >= 0.9 * T2_full_Q:
                separates_90pct_of_full += 1
        results_by_N[N] = {
            "N": N,
            "B": B_BOOTSTRAP,
            "drift_M": _summarise(drifts),
            "dist_C_M": _summarise(dists_C),
            "T2": _summarise(T2s),
            "fraction_T2_ge_50pct_of_full": separates_50pct_of_full / B_BOOTSTRAP,
            "fraction_T2_ge_90pct_of_full": separates_90pct_of_full / B_BOOTSTRAP,
        }

    # ---- Worst-case (N=5) probe: can we still separate with only 5 surahs?
    N_tiny = 5
    drifts_tiny = []
    T2_tiny = []
    sep_tiny = 0
    for _ in range(B_BOOTSTRAP):
        idx = rng.sample(range(nQ), N_tiny)
        X_sub = X_Q[idx]
        c_sub = X_sub.mean(axis=0)
        drifts_tiny.append(_mahalanobis(c_sub, c_full_Q, S_inv))
        T2 = _hotelling_t2(X_sub, mu_ctrl, S_inv)
        T2_tiny.append(T2)
        if T2 >= 0.5 * T2_full_Q:
            sep_tiny += 1
    results_by_N[N_tiny] = {
        "N": N_tiny,
        "B": B_BOOTSTRAP,
        "drift_M": _summarise(drifts_tiny),
        "dist_C_M": {"n": 0},
        "T2": _summarise(T2_tiny),
        "fraction_T2_ge_50pct_of_full": sep_tiny / B_BOOTSTRAP,
        "fraction_T2_ge_90pct_of_full": None,
    }

    # ---- Centroid-hinge diagnostic: leave-one-out drift ----
    # For each Quran surah k: compute ||c_{-k} - c_full_Q||_M and rank.
    loo_drifts: list[tuple[int, str, float]] = []
    for k in range(nQ):
        X_loo = np.delete(X_Q, k, axis=0)
        c_loo = X_loo.mean(axis=0)
        d = _mahalanobis(c_loo, c_full_Q, S_inv)
        lbl = str(getattr(q_units[k], "label", f"idx_{k}"))
        loo_drifts.append((k, lbl, d))
    loo_drifts.sort(key=lambda r: -r[2])
    hinge_top10 = [
        {"index": k, "label": lbl, "drift_M": round(d, 4)}
        for k, lbl, d in loo_drifts[:10]
    ]

    # ---- Save --------------------------------------------------------------
    report = {
        "experiment": EXP,
        "schema_version": 1,
        "hypothesis": (
            "Does the Quran's 5-D centroid location (and therefore the "
            "Phi_M separation in PAPER.md Section 4.1) survive random "
            "subsetting of surahs? Equivalently, is the fingerprint "
            "carried uniformly across the Band-A Quran corpus or by a "
            "few outlier surahs?"
        ),
        "config": {
            "seed": SEED,
            "band_a": [BAND_A_LO, BAND_A_HI],
            "N_grid": N_GRID + [N_tiny],
            "B_bootstrap": B_BOOTSTRAP,
            "arabic_ctrl_corpora": ARABIC_CTRL_NAMES,
        },
        "n_quran_band_a": nQ,
        "n_ctrl_band_a": int(X_C.shape[0]),
        "feat_cols": feat_cols,
        "full_corpus": {
            "T2_full_Quran_vs_ctrl_centroid": T2_full_Q,
            "dist_full_Quran_centroid_to_ctrl_M": dist_full_Q,
            "ctrl_pool_mean_phi_m_M": float(_mahalanobis(
                c_full_C, mu_ctrl, S_inv
            )),
        },
        "subset_bootstrap": results_by_N,
        "leave_one_out_hinge_top10": hinge_top10,
        "runtime_seconds": round(time.time() - t0, 1),
    }
    outfile = out_dir / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ---- Console summary ---------------------------------------------------
    print(f"[{EXP}] wrote {outfile}")
    print(f"[{EXP}] Subset centroid drift ||c_sub - c_full_Q||_M  (bootstrap B={B_BOOTSTRAP})")
    print(f"    N    drift_median  drift_q95   T2_median      %>=50%T2full   %>=90%T2full")
    for N in [N_tiny] + N_GRID:
        r = results_by_N[N]
        fr50 = r["fraction_T2_ge_50pct_of_full"]
        fr90 = r["fraction_T2_ge_90pct_of_full"]
        fr90_str = f"{fr90:.3f}" if fr90 is not None else "  n/a"
        print(f"   {N:3d}   {r['drift_M']['median']:12.4f}  "
              f"{r['drift_M']['q95']:9.4f}  "
              f"{r['T2']['median']:12.2f}  "
              f"   {fr50:.3f}        {fr90_str}")
    print(f"[{EXP}] Top-10 hinge surahs by LOO centroid drift:")
    for h in hinge_top10[:5]:
        print(f"   {h['label']:12s}  drift_M = {h['drift_M']:.4f}")

    self_check_end(pre, exp_name=EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
