"""
expParadigm2_continuation_ACD/run.py
=====================================
Paradigm-Stage 2 continuation — Paths A + C + D in one combined experiment.

PATH A — Edgeworth non-Gaussian correction to Hotelling T²
   Mardia tests rejected MVN at z = 6.6σ (Quran) and 185σ (ctrl pool) for the
   5-D feature data; therefore T² is only first-order optimal under MVN.
   Computes the leading Edgeworth-style correction term using the empirical
   multivariate skewness (Mardia b₁,p) and kurtosis (Mardia b₂,p):

       correction_factor ≈ 1 + (b2_p - p(p+2)) / (8 * n_eff)

   for the F-tail probability. Reports the magnitude of the correction and
   whether it materially changes the optimality conclusion.

PATH C — P2_OP4 redundancy regression
   For each of the 5 F6-family lag-k Spearman correlations (lag1..lag5,
   per Band-A Quran surah, n=68, from exp24_F6_autocorr), regress on the
   5-D matrix (EL, VL_CV, CN, H_cond, T) and report R². High R² means the
   additional feature is REDUNDANT with the 5-D triple — empirical
   evidence for minimal-sufficiency.

PATH D — Non-linear discriminators vs Hotelling T²
   Implements two non-linear two-sample test statistics with permutation
   nulls and compares discrimination power against Hotelling T²:

   - MMD² (Maximum Mean Discrepancy) with RBF kernel
   - Energy distance (multivariate, Szekely-Rizzo)

   For each: compute observed statistic, permutation null (B=2000),
   permutation p-value. Compare per-σ-equivalent strength to T².

   IMPORTANT CAVEAT: T² has σ-equivalent strength dominated by its
   exact F-tail p ≈ 10⁻⁴⁸⁰ (mpmath). Permutation null floors at
   1/(B+1) ≈ 5e-4. Therefore if MMD/energy hit the perm floor too, we
   cannot distinguish them from T² in σ-equivalent at this B; we'd need
   asymptotic-tail derivations of MMD/energy null distributions. This
   experiment provides the FINITE-B empirical comparison, not the
   asymptotic-tail derivation.

Reads (read-only):
  - results/checkpoints/phase_06_phi_m.pkl  (X_QURAN, X_CTRL_POOL)
  - results/experiments/exp24_F6_autocorr/exp24_F6_autocorr.json
    (per-surah lag1..lag5 Spearman correlations)

Writes:
  - results/experiments/expParadigm2_continuation_ACD/expParadigm2_continuation_ACD.json
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats

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

EXP = "expParadigm2_continuation_ACD"
RIDGE_LAMBDA = 1e-6
SEED = 42
N_PERM = 2_000  # for Path D MMD/energy permutation nulls


# ============================================================================
# PATH A — Edgeworth correction (Mardia b₁, b₂ → first-order tail correction)
# ============================================================================
def _mardia_moments(X: np.ndarray) -> tuple[float, float]:
    """Return (b1_p, b2_p) — multivariate skewness and kurtosis (Mardia 1970)."""
    n, p = X.shape
    Y = X - X.mean(0, keepdims=True)
    Sigma = Y.T @ Y / n
    S = np.linalg.inv(Sigma)
    M = Y @ S @ Y.T
    b1 = float((M ** 3).sum() / (n * n))
    b2 = float(np.diag(M ** 2).sum() / n)
    return b1, b2


def _hotelling_T2_pooled(X1: np.ndarray, X2: np.ndarray,
                         ridge: float = RIDGE_LAMBDA) -> dict:
    n1, p = X1.shape
    n2 = X2.shape[0]
    m1, m2 = X1.mean(0), X2.mean(0)
    S1 = np.cov(X1, rowvar=False, ddof=1)
    S2 = np.cov(X2, rowvar=False, ddof=1)
    Sp = ((n1 - 1) * S1 + (n2 - 1) * S2) / max(1, (n1 + n2 - 2))
    Spi = np.linalg.inv(Sp + ridge * np.eye(p))
    diff = m1 - m2
    n_eff = (n1 * n2) / (n1 + n2)
    quad = float(diff @ Spi @ diff)
    t2 = float(n_eff * quad)
    df1, df2 = p, n1 + n2 - p - 1
    F = ((n1 + n2 - p - 1) / ((n1 + n2 - 2) * p)) * t2
    p_F = float(stats.f.sf(F, df1, df2))
    return {
        "T2": t2, "F": F, "df1": int(df1), "df2": int(df2),
        "p_F_tail": p_F, "n_eff": float(n_eff), "p_dim": int(p),
    }


def _edgeworth_correction(b2_pooled: float, p: int, n_eff: float) -> dict:
    """Leading Edgeworth correction to the F-tail of T² under non-Gaussian
    data (cf. Mardia 1970; Hall 1992 §3.7).

    The leading-order correction modifies the asymptotic null distribution
    of T² from chi²(p) to a scaled chi² with effective degrees-of-freedom:

        chi² → (1 + δ) chi²(p)
    where  δ = (b₂_p - p(p+2)) / (4 * n_eff * p)

    For b₂ = p(p+2) (Gaussian case), δ = 0 → no correction. For non-
    Gaussian data with b₂ > p(p+2), δ > 0 inflates the null variance,
    making the F-tail HEAVIER and the corrected p-value LARGER.

    Returns the correction factor δ + 1, the corrected effective tail
    threshold, and a "p adjustment" factor that quantifies how much the
    F-tail probability is changed.
    """
    expected_b2_under_mvn = p * (p + 2)
    excess_b2 = b2_pooled - expected_b2_under_mvn
    delta = excess_b2 / (4.0 * n_eff * p)
    correction_factor = 1.0 + delta
    return {
        "expected_b2_under_mvn": float(expected_b2_under_mvn),
        "observed_b2_pooled":    float(b2_pooled),
        "excess_b2":             float(excess_b2),
        "delta":                 float(delta),
        "correction_factor_var_inflation": correction_factor,
        "interpretation": (
            "delta > 0 means the null distribution of T² has heavier "
            "tail than chi²(p) under Gaussianity. The F-tail p-value "
            "should be inflated by approximately (1 + delta) at "
            "first-order Edgeworth approximation."
        ),
    }


# ============================================================================
# PATH C — F6 lag1..lag5 redundancy regression on 5-D matrix
# ============================================================================
def _r_squared(y: np.ndarray, X: np.ndarray) -> float:
    """OLS R² of y on (1, X). Plain matrix algebra."""
    n = X.shape[0]
    X1 = np.column_stack([np.ones(n), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    y_pred = X1 @ beta
    ss_res = float(((y - y_pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    if ss_tot == 0:
        return float("nan")
    return 1.0 - ss_res / ss_tot


def _path_c_redundancy(X_Q: np.ndarray) -> dict:
    """Regress each F6 lag-k Spearman (per Band-A Quran surah) on X_Q
    (the 5-D feature matrix), report R²."""
    f6_path = (_ROOT / "results" / "experiments" / "exp24_F6_autocorr"
               / "exp24_F6_autocorr.json")
    if not f6_path.exists():
        return {"error": "exp24_F6_autocorr.json not found"}
    d = json.load(open(f6_path, "r", encoding="utf-8"))
    q = d["per_corpus"].get("quran", {})
    n_q = q.get("n", 0)
    if n_q != X_Q.shape[0]:
        return {
            "error": f"alignment mismatch: exp24 quran n={n_q} vs "
                     f"X_QURAN n={X_Q.shape[0]} — Band-A definition diverged"
        }
    rows = []
    for k in (1, 2, 3, 4, 5):
        vals = q.get(f"lag{k}_values", [])
        y = np.asarray(vals, dtype=float)
        # Drop NaNs (some short surahs cannot compute lag-k)
        mask = np.isfinite(y)
        if mask.sum() < X_Q.shape[1] + 2:
            rows.append({"lag": k, "n_valid": int(mask.sum()),
                         "R2": float("nan"), "redundant_at_0p95": None})
            continue
        y_clean = y[mask]
        X_clean = X_Q[mask]
        r2 = _r_squared(y_clean, X_clean)
        rows.append({
            "lag": int(k),
            "n_valid": int(mask.sum()),
            "R2": float(r2),
            "redundant_at_0p95": bool(r2 >= 0.95),
            "redundant_at_0p80": bool(r2 >= 0.80),
        })
    valid_r2 = [r["R2"] for r in rows if math.isfinite(r["R2"])]
    return {
        "feature_family": "F6 lag-k Spearman correlations on verse-length series",
        "per_lag": rows,
        "mean_R2_across_lags": (float(np.mean(valid_r2))
                                if valid_r2 else float("nan")),
        "n_lags_redundant_at_0p95": sum(
            1 for r in rows if r.get("redundant_at_0p95") is True
        ),
        "n_lags_redundant_at_0p80": sum(
            1 for r in rows if r.get("redundant_at_0p80") is True
        ),
        "interpretation": (
            "If mean_R2 across lags is high (e.g. > 0.5), the F6-family "
            "features are 'mostly explained' by the 5-D triple. R² > 0.95 "
            "would be 'almost-deterministically redundant'. This is "
            "EMPIRICAL evidence for minimal-sufficiency over the F6 "
            "family; the formal P2_OP4 claim requires this for ALL "
            "feature families, not just F6."
        ),
    }


# ============================================================================
# PATH D — Non-linear discriminators (MMD, energy distance)
#
# Optimisation: precompute the FULL n × n distance/kernel matrix over the
# pooled data ONCE; permutations only re-index, not re-compute.  This drops
# MMD/energy permutation cost from O(n² × n_perm) FLOPs to O(n² + n_perm × n²)
# index lookups, ~30× faster for n=2577.
# ============================================================================
def _full_distance_matrix(Z: np.ndarray) -> np.ndarray:
    """Pairwise Euclidean-distance matrix on Z (n × p)."""
    sq = (Z * Z).sum(axis=1)
    D2 = sq[:, None] + sq[None, :] - 2.0 * (Z @ Z.T)
    np.maximum(D2, 0.0, out=D2)
    return np.sqrt(D2)


def _rbf_kernel_from_dist(D: np.ndarray, sigma: float) -> np.ndarray:
    """RBF kernel k(a,b) = exp(-||a-b||² / (2 σ²)) from a precomputed
    pairwise distance matrix."""
    inv_2s2 = 1.0 / (2.0 * sigma * sigma)
    return np.exp(-(D * D) * inv_2s2)


def _mmd_squared_from_K(K: np.ndarray, idx_x: np.ndarray, idx_y: np.ndarray) -> float:
    """Unbiased MMD² given precomputed full kernel matrix K and partition
    indices."""
    n = idx_x.size
    m = idx_y.size
    if n < 2 or m < 2:
        return 0.0
    Kxx = K[np.ix_(idx_x, idx_x)]
    Kyy = K[np.ix_(idx_y, idx_y)]
    Kxy = K[np.ix_(idx_x, idx_y)]
    sum_xx = (Kxx.sum() - np.trace(Kxx)) / (n * (n - 1))
    sum_yy = (Kyy.sum() - np.trace(Kyy)) / (m * (m - 1))
    sum_xy = Kxy.sum() / (n * m)
    return float(sum_xx + sum_yy - 2 * sum_xy)


def _energy_distance_from_D(D: np.ndarray, idx_x: np.ndarray,
                            idx_y: np.ndarray) -> float:
    """Multivariate energy distance (Szekely-Rizzo) from precomputed
    distance matrix D."""
    e_xy = float(D[np.ix_(idx_x, idx_y)].mean())
    e_xx = float(D[np.ix_(idx_x, idx_x)].mean())
    e_yy = float(D[np.ix_(idx_y, idx_y)].mean())
    return 2.0 * e_xy - e_xx - e_yy


def _perm_p_full_K(stat_from_K, K_or_D, n1: int, n2: int,
                    n_perm: int = N_PERM, seed: int = SEED) -> dict:
    """Permutation p-value for an MMD/energy-style statistic on a
    precomputed K or D matrix."""
    n = n1 + n2
    idx_x_obs = np.arange(n1)
    idx_y_obs = np.arange(n1, n)
    obs = stat_from_K(K_or_D, idx_x_obs, idx_y_obs)
    rng = np.random.default_rng(seed)
    null_vals = np.empty(n_perm, dtype=float)
    n_ge = 0
    for i in range(n_perm):
        perm = rng.permutation(n)
        v = stat_from_K(K_or_D, perm[:n1], perm[n1:])
        null_vals[i] = v
        if v >= obs:
            n_ge += 1
    p = (n_ge + 1) / (n_perm + 1)
    return {
        "obs":           float(obs),
        "n_perm":        int(n_perm),
        "n_perm_ge_obs": int(n_ge),
        "p_perm":        float(p),
        "null_mean":     float(null_vals.mean()),
        "null_std":      float(null_vals.std(ddof=1)),
        "obs_z_under_null": float((obs - null_vals.mean())
                                   / max(null_vals.std(ddof=1), 1e-12)),
    }


def _perm_p_t2(X: np.ndarray, Y: np.ndarray,
               n_perm: int = N_PERM, seed: int = SEED) -> dict:
    """Permutation p-value for Hotelling T² (recomputes T² each perm; T² is
    fast so no need to precompute)."""
    n1 = X.shape[0]
    Z = np.vstack([X, Y])
    obs = _hotelling_T2_pooled(X, Y)["T2"]
    rng = np.random.default_rng(seed)
    null_vals = np.empty(n_perm, dtype=float)
    n_ge = 0
    for i in range(n_perm):
        idx = rng.permutation(Z.shape[0])
        v = _hotelling_T2_pooled(Z[idx[:n1]], Z[idx[n1:]])["T2"]
        null_vals[i] = v
        if v >= obs:
            n_ge += 1
    p = (n_ge + 1) / (n_perm + 1)
    return {
        "obs":           float(obs),
        "n_perm":        int(n_perm),
        "n_perm_ge_obs": int(n_ge),
        "p_perm":        float(p),
        "null_mean":     float(null_vals.mean()),
        "null_std":      float(null_vals.std(ddof=1)),
        "obs_z_under_null": float((obs - null_vals.mean())
                                   / max(null_vals.std(ddof=1), 1e-12)),
    }


# ============================================================================
# Main
# ============================================================================
def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    X_Q = np.asarray(state["X_QURAN"], dtype=float)
    X_C = np.asarray(state["X_CTRL_POOL"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])
    print(f"[{EXP}] X_Q {X_Q.shape}  X_C {X_C.shape}  feats {feat_cols}")

    # =========== PATH A ===========
    print(f"\n[{EXP}] === PATH A — Edgeworth non-Gaussian correction ===")
    t2_record = _hotelling_T2_pooled(X_Q, X_C)
    # Pooled covariance moments (use the full pooled sample — Q and C combined
    # under the H₀ "equal mean" pretence — to estimate the null moments).
    Z_pool = np.vstack([X_Q - X_Q.mean(0), X_C - X_C.mean(0)])  # mean-removed
    b1_pool, b2_pool = _mardia_moments(Z_pool)
    edge = _edgeworth_correction(b2_pool, X_Q.shape[1], t2_record["n_eff"])
    print(f"[{EXP}]   T² = {t2_record['T2']:.4f}  F = {t2_record['F']:.4f}  "
          f"df = ({t2_record['df1']}, {t2_record['df2']})")
    print(f"[{EXP}]   p_F (uncorrected, scipy) = {t2_record['p_F_tail']:.3e}")
    print(f"[{EXP}]   pooled b₁ = {b1_pool:.4f}   b₂ = {b2_pool:.4f}   "
          f"E[b₂|MVN] = {edge['expected_b2_under_mvn']:.4f}")
    print(f"[{EXP}]   Edgeworth δ = (b₂ - p(p+2)) / (4 n_eff p) = "
          f"{edge['delta']:+.6f}")
    print(f"[{EXP}]   variance-inflation factor (1+δ) = "
          f"{edge['correction_factor_var_inflation']:.6f}")
    if abs(edge["delta"]) < 0.05:
        edge_verdict = "EDGEWORTH_CORRECTION_NEGLIGIBLE_(<5%)"
    elif abs(edge["delta"]) < 0.20:
        edge_verdict = "EDGEWORTH_CORRECTION_MODERATE_(5-20%)"
    else:
        edge_verdict = "EDGEWORTH_CORRECTION_LARGE_(>20%)"
    print(f"[{EXP}]   verdict: {edge_verdict}")

    # =========== PATH C ===========
    print(f"\n[{EXP}] === PATH C — F6 lag1..lag5 redundancy regression ===")
    path_c = _path_c_redundancy(X_Q)
    if "error" in path_c:
        print(f"[{EXP}]   ERROR: {path_c['error']}")
    else:
        for r in path_c["per_lag"]:
            r2_str = f"{r['R2']:.4f}" if math.isfinite(r['R2']) else "NaN"
            print(f"[{EXP}]   lag{r['lag']}  n={r['n_valid']}  R²={r2_str}  "
                  f"redundant@0.95={r.get('redundant_at_0p95')}  "
                  f"redundant@0.80={r.get('redundant_at_0p80')}")
        print(f"[{EXP}]   mean R² across lags = "
              f"{path_c['mean_R2_across_lags']:.4f}")
        print(f"[{EXP}]   {path_c['n_lags_redundant_at_0p95']}/5 lags "
              f"redundant @ 0.95 ; "
              f"{path_c['n_lags_redundant_at_0p80']}/5 redundant @ 0.80")

    # =========== PATH D ===========
    print(f"\n[{EXP}] === PATH D — Non-linear discriminators "
          f"(MMD, energy) vs T² ===")
    print(f"[{EXP}]   precomputing pooled distance/kernel matrices "
          f"(n={X_Q.shape[0] + X_C.shape[0]})...", flush=True)
    t_path_d = time.time()
    Z = np.vstack([X_Q, X_C])
    n1 = X_Q.shape[0]
    n2 = X_C.shape[0]
    D_full = _full_distance_matrix(Z)  # ~50 MB at n=2577
    # σ for the RBF kernel: median of nonzero pairwise distances on a
    # subsample of 500 (matches the standard heuristic).
    rng_med = np.random.default_rng(SEED)
    sub_idx = rng_med.choice(Z.shape[0], size=min(500, Z.shape[0]),
                             replace=False)
    D_sub = D_full[np.ix_(sub_idx, sub_idx)]
    sigma_med = float(np.median(D_sub[D_sub > 0])) if (D_sub > 0).any() else 1.0
    K_full = _rbf_kernel_from_dist(D_full, sigma=sigma_med)
    print(f"[{EXP}]   precompute done in {time.time() - t_path_d:.1f}s "
          f"(σ_RBF = {sigma_med:.4f}, kernel matrix {K_full.shape[0]}²"
          f" = {K_full.size} entries)", flush=True)
    print(f"[{EXP}]   running {N_PERM} permutations on cached matrices...",
          flush=True)
    t_perm = time.time()
    mmd_record = _perm_p_full_K(_mmd_squared_from_K, K_full, n1, n2,
                                 n_perm=N_PERM, seed=SEED)
    print(f"[{EXP}]     MMD perm done in {time.time() - t_perm:.1f}s",
          flush=True)
    t_perm = time.time()
    energy_record = _perm_p_full_K(_energy_distance_from_D, D_full, n1, n2,
                                    n_perm=N_PERM, seed=SEED + 1)
    print(f"[{EXP}]     Energy perm done in {time.time() - t_perm:.1f}s",
          flush=True)
    t_perm = time.time()
    t2_perm = _perm_p_t2(X_Q, X_C, n_perm=N_PERM, seed=SEED + 2)
    print(f"[{EXP}]     T² perm done in {time.time() - t_perm:.1f}s",
          flush=True)
    print(f"[{EXP}]   total Path D wall = {time.time() - t_path_d:.1f}s")
    print(f"[{EXP}]   MMD²    obs={mmd_record['obs']:.6f}  "
          f"null mean±sd = {mmd_record['null_mean']:+.4e} ± "
          f"{mmd_record['null_std']:.4e}  "
          f"z={mmd_record['obs_z_under_null']:+.2f}σ  "
          f"p_perm={mmd_record['p_perm']:.4e}")
    print(f"[{EXP}]   Energy  obs={energy_record['obs']:.4f}  "
          f"null mean±sd = {energy_record['null_mean']:+.4f} ± "
          f"{energy_record['null_std']:.4f}  "
          f"z={energy_record['obs_z_under_null']:+.2f}σ  "
          f"p_perm={energy_record['p_perm']:.4e}")
    print(f"[{EXP}]   T²      obs={t2_perm['obs']:.4f}  "
          f"null mean±sd = {t2_perm['null_mean']:.4f} ± "
          f"{t2_perm['null_std']:.4f}  "
          f"z={t2_perm['obs_z_under_null']:+.2f}σ  "
          f"p_perm={t2_perm['p_perm']:.4e}")

    # Compare in σ-equivalent — strongest signal wins
    sigmas = {
        "MMD_RBF_squared": mmd_record["obs_z_under_null"],
        "Energy_distance": energy_record["obs_z_under_null"],
        "Hotelling_T2":    t2_perm["obs_z_under_null"],
    }
    winner = max(sigmas.items(), key=lambda kv: kv[1])
    print(f"[{EXP}]   strongest discriminator (σ vs perm null): "
          f"{winner[0]} at {winner[1]:+.2f}σ")
    if winner[0] != "Hotelling_T2" and winner[1] > sigmas["Hotelling_T2"]:
        path_d_verdict = "NONLINEAR_DISCRIMINATOR_BEATS_T2"
    elif abs(winner[1] - sigmas["Hotelling_T2"]) < 0.5:
        path_d_verdict = "T2_AND_NONLINEAR_TIE_AT_PERM_FLOOR"
    else:
        path_d_verdict = "T2_DOMINATES_OR_PERM_FLOOR_HIT"

    runtime = time.time() - t0
    report = {
        "experiment": EXP,
        "task_id": "Paradigm-Stage 2 — Paths A + C + D continuation",
        "title": (
            "Edgeworth non-Gaussian correction to T² (Path A) ; F6-lag-k "
            "redundancy regression (Path C, P2_OP4 partial) ; non-linear "
            "discriminators MMD/Energy vs T² (Path D, new direction)."
        ),
        "PATH_A_edgeworth_correction": {
            "T2_record":       t2_record,
            "pooled_skewness": b1_pool,
            "pooled_kurtosis": b2_pool,
            "edgeworth_terms": edge,
            "verdict":         edge_verdict,
        },
        "PATH_C_redundancy": path_c,
        "PATH_D_nonlinear_discriminators": {
            "n_perm": N_PERM,
            "MMD_RBF_squared":   mmd_record,
            "Energy_distance":   energy_record,
            "Hotelling_T2_perm": t2_perm,
            "z_sigma_under_perm_null": sigmas,
            "winner":            winner[0],
            "winner_sigma":      winner[1],
            "verdict":           path_d_verdict,
            "caveat": (
                "Permutation null floors at 1/(B+1) ≈ 5e-4 for B=2000. "
                "T²'s exact F-tail p ≈ 10⁻⁴⁸⁰ is not comparable at this "
                "B; the σ-equivalent under the SAME permutation null is "
                "the apples-to-apples comparison reported here. Larger B "
                "or asymptotic-tail derivations of MMD/energy null would "
                "tighten the comparison."
            ),
        },
        "runtime_seconds": round(runtime, 2),
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print()
    print(f"[{EXP}] -- summary --")
    print(f"[{EXP}]   PATH A verdict: {edge_verdict}")
    if "error" not in path_c:
        print(f"[{EXP}]   PATH C: F6-lag-k mean R² on (EL,VL_CV,CN,H_cond,T) = "
              f"{path_c['mean_R2_across_lags']:.4f}")
    print(f"[{EXP}]   PATH D winner: {winner[0]} at {winner[1]:+.2f}σ "
          f"({path_d_verdict})")
    print(f"[{EXP}]   runtime: {runtime:.1f}s")
    print(f"[{EXP}] wrote {out / f'{EXP}.json'}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
