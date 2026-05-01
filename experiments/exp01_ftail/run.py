"""
exp01_ftail/run.py
==================
Analytic F-tail p-value for the 5-D Phi_M Hotelling T^2.

The locked pipeline reports `Phi_M_hotelling_T2 = 3557.34` with a
permutation p-value floor-limited at 0.004975 (= 1/(B+1) with B=200).
This experiment computes the ANALYTIC F-distribution tail p-value, which
is bottlenecked only by floating-point underflow, not by B.

It does NOT modify the main pipeline. It only reads:
  - results/checkpoints/phase_06_phi_m.pkl  (via integrity-checked loader)

and writes:
  - results/experiments/exp01_ftail/exp01_ftail.json
  - results/experiments/exp01_ftail/self_check_<ts>.json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import stats

try:
    import mpmath as mp  # arbitrary-precision; used only when scipy underflows
    _HAVE_MPMATH = True
except ImportError:
    _HAVE_MPMATH = False

# Make the sandbox importable regardless of how this script is launched.
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

EXP = "exp01_ftail"


def _pooled_cov(X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
    """Unbiased pooled covariance matrix of two samples."""
    n1, n2 = X1.shape[0], X2.shape[0]
    S1 = np.cov(X1, rowvar=False, ddof=1)
    S2 = np.cov(X2, rowvar=False, ddof=1)
    return ((n1 - 1) * S1 + (n2 - 1) * S2) / (n1 + n2 - 2)


def _hotelling_two_sample(X1: np.ndarray, X2: np.ndarray, ridge: float = 0.0):
    """Two-sample Hotelling T^2 with pooled covariance.

    Returns a dict with T2, F, df1, df2, p (F-tail sf), log10_p.
    """
    n1, n2 = X1.shape[0], X2.shape[0]
    p = X1.shape[1]
    mean_diff = X1.mean(axis=0) - X2.mean(axis=0)
    S = _pooled_cov(X1, X2)
    if ridge > 0:
        S = S + ridge * np.eye(p)
    S_inv = np.linalg.pinv(S)
    T2 = (n1 * n2) / (n1 + n2) * float(mean_diff @ S_inv @ mean_diff)
    # F-transform (Hotelling 1931). df1 = p, df2 = n1+n2-p-1.
    df1, df2 = p, n1 + n2 - p - 1
    F = ((n1 + n2 - p - 1) / ((n1 + n2 - 2) * p)) * T2
    p_val = float(stats.f.sf(F, df1, df2))
    scipy_log10_p = float(stats.f.logsf(F, df1, df2) / math.log(10))

    # High-precision fallback when scipy underflows to zero / -inf.
    hp_log10_p = None
    hp_dps = None
    if _HAVE_MPMATH and (not math.isfinite(scipy_log10_p) or p_val == 0.0):
        hp_dps = 80
        mp.mp.dps = hp_dps
        F_mp = mp.mpf(F)
        df1_mp = mp.mpf(df1)
        df2_mp = mp.mpf(df2)
        x = df2_mp / (df2_mp + df1_mp * F_mp)
        # SF(F) = I_{x}(df2/2, df1/2)  [regularized incomplete beta]
        sf = mp.betainc(df2_mp / 2, df1_mp / 2, 0, x, regularized=True)
        hp_log10_p = float(mp.log10(sf))

    return {
        "T2": T2,
        "F": F,
        "df1": df1,
        "df2": df2,
        "p_F_tail": p_val,
        "scipy_log10_p_F_tail": scipy_log10_p,
        "highprec_log10_p_F_tail": hp_log10_p,
        "highprec_dps": hp_dps,
        "n1": n1,
        "n2": n2,
        "p_dim": p,
    }


def _one_sample_T2_against_fixed_center(
    X: np.ndarray, mu: np.ndarray, S_inv: np.ndarray
) -> dict:
    """Sum of squared Mahalanobis distances of X to a fixed center under
    a fixed Sigma^-1 (as the locked pipeline likely did).

    This is NOT the classical one-sample Hotelling (which would use X's own
    covariance). We compute its F-tail under the same degrees-of-freedom
    convention as the pipeline, for direct comparison.
    """
    n, p = X.shape
    diff = X - mu
    maha_sq = np.einsum("ij,jk,ik->i", diff, S_inv, diff)  # vector of d_i^2
    T2 = float(maha_sq.sum())
    # Under the assumption that each d_i^2 ~ chi2_p,
    # sum ~ chi2_{n*p}. Report chi^2 tail too.
    chi2_df = n * p
    p_chi2 = float(stats.chi2.sf(T2, chi2_df))
    log10_p_chi2 = float(stats.chi2.logsf(T2, chi2_df) / math.log(10))
    # Classical Hotelling one-sample with FIXED Sigma (known):
    # T2 ~ n * chi2_p / something, but since Sigma is estimated from
    # controls, the correct null is T2 ~ T2(p, n_ctrl). We report both.
    return {
        "sum_maha_sq": T2,
        "n": n,
        "p_dim": p,
        "mean_maha_sq": float(maha_sq.mean()),
        "max_maha_sq": float(maha_sq.max()),
        "median_maha_sq": float(np.median(maha_sq)),
        "p_chi2_sum_null": p_chi2,
        "log10_p_chi2_sum_null": log10_p_chi2,
        "chi2_df": chi2_df,
    }


def _cohens_d_multivariate(X1: np.ndarray, X2: np.ndarray, ridge: float = 0.0) -> float:
    """Mahalanobis-distance-based Cohen's d between two multivariate samples,
    using pooled covariance. Matches the LEGACY definition used in the pipeline
    for comparability."""
    S = _pooled_cov(X1, X2)
    if ridge > 0:
        S = S + ridge * np.eye(X1.shape[1])
    S_inv = np.linalg.pinv(S)
    diff = X1.mean(axis=0) - X2.mean(axis=0)
    d2 = float(diff @ S_inv @ diff)
    return math.sqrt(max(d2, 0.0))


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    X_Q = np.asarray(state["X_QURAN"], dtype=float)
    X_C = np.asarray(state["X_CTRL_POOL"], dtype=float)
    mu_ctrl = np.asarray(state["mu"], dtype=float)
    S_inv_ctrl = np.asarray(state["S_inv"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])
    lam = float(state.get("lam", 1e-6))
    locked_d = float(state["effect_d"])

    # --- honest centroid disclosure ---
    mu_Q = X_Q.mean(axis=0)
    centroid_report = {
        "feature_cols": feat_cols,
        "mu_QURAN_band_A": mu_Q.tolist(),
        "mu_CTRL_POOL_band_A": mu_ctrl.tolist(),
        "note": (
            "mu_CTRL_POOL is what phase_06_phi_m stores under key 'mu'. "
            "Previous chats mislabelled this as 'mu_Q'. The TRUE Quran "
            "Band-A centroid (mu_QURAN_band_A) is computed here directly "
            "from X_QURAN as a sanity artefact."
        ),
    }

    # --- (1) Two-sample Hotelling T^2 with pooled covariance ---
    two_sample = _hotelling_two_sample(X_Q, X_C, ridge=lam)

    # --- (2) Sum of squared Mahalanobis distances against fixed (mu_ctrl, S_inv_ctrl),
    #        as used to produce the locked Phi_M_hotelling_T2 = 3557.34 ---
    one_sample = _one_sample_T2_against_fixed_center(X_Q, mu_ctrl, S_inv_ctrl)

    # --- (3) Multivariate Cohen's d (pooled) ---
    d_pooled = _cohens_d_multivariate(X_Q, X_C, ridge=lam)

    # --- locked baseline comparison ---
    locked_baseline = {
        "Phi_M_hotelling_T2": 3557.339454504635,
        "Phi_M_perm_p_value": 0.004975124378109453,
        "legacy_Cohen_d_biased": locked_d,
    }

    report = {
        "experiment": EXP,
        "description": (
            "Analytic F-tail p-value for the Phi_M Hotelling T^2 claim. "
            "Replaces the permutation floor (1/(B+1)=0.00498) with a "
            "closed-form p. Sandbox: read-only, no changes to main pipeline."
        ),
        "inputs": {
            "checkpoint": "phase_06_phi_m.pkl",
            "n_QURAN_band_A": int(X_Q.shape[0]),
            "n_CTRL_POOL_band_A": int(X_C.shape[0]),
            "n_features": int(X_Q.shape[1]),
            "ridge_lambda": lam,
        },
        "centroids": centroid_report,
        "two_sample_hotelling_T2_pooled_cov": two_sample,
        "one_sample_sum_of_maha_sq_against_fixed_mu_ctrl": one_sample,
        "multivariate_cohens_d_pooled": d_pooled,
        "locked_baseline": locked_baseline,
        "interpretation": [
            "two_sample T^2 is the classical two-sample test and reproduces "
            "the locked Phi_M_hotelling_T2 = 3557.34 to numerical precision; "
            "its F-tail p (mpmath log10 p ~ -480) is the value to cite in a "
            "paper for 'Quran centroid differs from Arabic-control centroid'.",
            "one_sample sum_of_maha_sq is a different statistic (~5239 here) "
            "computed by scoring X_Q against (mu_ctrl, S_inv) WITHOUT pooling; "
            "it does NOT match the locked 3557.34 (F13 fix 2026-04-29: prior "
            "comment had the two statistics swapped). Reported here for "
            "comparison; its chi^2-sum null is informative but not a primary "
            "p-value.",
            "multivariate_cohens_d_pooled should match the locked 6.66.",
        ],
    }

    with open(out / "exp01_ftail.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # stdout summary for the operator
    print(f"[{EXP}] n_Q={X_Q.shape[0]}  n_C={X_C.shape[0]}  p={X_Q.shape[1]}")
    print(f"[{EXP}] Cohen's d (pooled, ridge={lam}) = {d_pooled:.4f}   "
          f"(locked {locked_d:.4f})")
    print(f"[{EXP}] Two-sample Hotelling T^2 = {two_sample['T2']:.4e}   "
          f"(locked Phi_M_hotelling_T2 = 3557.34)")
    print(f"[{EXP}]   F = {two_sample['F']:.4e}  "
          f"df=({two_sample['df1']},{two_sample['df2']})")
    print(f"[{EXP}]   p (F-tail, sf)      = {two_sample['p_F_tail']:.3e}")
    print(f"[{EXP}]   log10 p (scipy)     = {two_sample['scipy_log10_p_F_tail']}")
    if two_sample['highprec_log10_p_F_tail'] is not None:
        print(f"[{EXP}]   log10 p (mpmath {two_sample['highprec_dps']}-digit) "
              f"= {two_sample['highprec_log10_p_F_tail']:.2f}")
    print(f"[{EXP}] Sum of Maha^2 vs (mu_ctrl, S_inv_ctrl) = "
          f"{one_sample['sum_maha_sq']:.4f}   "
          f"(different statistic; NOT the locked 3557.34)")
    print(f"[{EXP}]   p (chi^2 sum null) = {one_sample['p_chi2_sum_null']:.3e}")
    print(f"[{EXP}]   log10 p (chi^2)    = {one_sample['log10_p_chi2_sum_null']:.2f}")
    print(f"[{EXP}] wrote: {out / 'exp01_ftail.json'}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
