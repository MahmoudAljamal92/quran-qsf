"""
exp74_eigenvalue_spectrum/run.py
=================================
H4: Eigenvalue Spectrum of the 5-D Covariance as a Power Law.

Motivation
    The 5-D covariance Sigma of the control pool has 5 eigenvalues.
    If they follow a power law lambda_k ~ k^(-alpha), alpha
    characterises the dimensionality of Arabic prose variation.

Protocol (frozen before execution)
    T1. Compute Sigma of 2509 control units in 5-D feature space.
    T2. Eigendecompose -> lambda_1 >= ... >= lambda_5.
    T3. Fit log(lambda_k) vs log(k) for power-law exponent alpha.
    T4. Marchenko-Pastur bound check (random matrix theory).
    T5. Effective dimensionality d_eff = (sum lambda)^2 / sum(lambda^2).
    T6. Quran's per-eigenmode contribution to Phi_M.
    T7. Repeat for Quran-only covariance (intra-Quran spectrum).
    T8. Bootstrap 10k for CI on alpha and d_eff.

Pre-registered thresholds
    POWER_LAW:     R^2 >= 0.95 for log-log fit
    SUGGESTIVE:    R^2 >= 0.80
    NULL:          R^2 < 0.80

Reads: phase_06_phi_m.pkl

Writes ONLY under results/experiments/exp74_eigenvalue_spectrum/
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

EXP = "exp74_eigenvalue_spectrum"
SEED = 42
N_BOOT = 10000


def _marchenko_pastur_bounds(n: int, p: int, sigma2: float = 1.0):
    """Marchenko-Pastur upper/lower bounds for eigenvalues of Wishart matrix.
    n = sample size, p = dimension, sigma2 = noise variance."""
    gamma = p / n
    lam_plus = sigma2 * (1 + math.sqrt(gamma)) ** 2
    lam_minus = sigma2 * (1 - math.sqrt(gamma)) ** 2 if gamma <= 1 else 0
    return lam_minus, lam_plus


def _fit_power_law(eigvals: np.ndarray):
    """Fit log(lambda_k) = -alpha * log(k) + c. Returns alpha, R^2, residuals."""
    k = np.arange(1, len(eigvals) + 1, dtype=float)
    log_k = np.log(k)
    log_lam = np.log(eigvals)
    slope, intercept, r_value, p_value, std_err = sp_stats.linregress(log_k, log_lam)
    alpha = -slope  # positive alpha means decay
    r2 = r_value ** 2
    predicted = slope * log_k + intercept
    residuals = log_lam - predicted
    return {
        "alpha": round(float(alpha), 4),
        "intercept": round(float(intercept), 4),
        "R2": round(float(r2), 6),
        "p_value": float(p_value),
        "std_err": round(float(std_err), 4),
        "residuals": [round(float(r), 4) for r in residuals],
    }


def _effective_dim(eigvals: np.ndarray) -> float:
    """Participation ratio: d_eff = (sum lambda)^2 / sum(lambda^2)."""
    s = eigvals.sum()
    s2 = (eigvals ** 2).sum()
    return float(s ** 2 / s2) if s2 > 0 else 0.0


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
    state = phi["state"]
    X_C = np.asarray(state["X_CTRL_POOL"], dtype=float)
    X_Q = np.asarray(state["X_QURAN"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])
    n_c, p = X_C.shape
    n_q = X_Q.shape[0]

    print(f"[{EXP}] Ctrl: {n_c}×{p}, Quran: {n_q}×{p}")
    print(f"[{EXP}] Features: {feat_cols}")

    # --- T1: Control covariance ---
    mu_c = X_C.mean(axis=0)
    Sigma_c = np.cov(X_C.T)

    # --- T2: Eigendecompose ---
    eigvals_c, eigvecs_c = np.linalg.eigh(Sigma_c)
    # Sort descending
    idx = eigvals_c.argsort()[::-1]
    eigvals_c = eigvals_c[idx]
    eigvecs_c = eigvecs_c[:, idx]

    print(f"\n[{EXP}] === T2: Control eigenvalues ===")
    for i, lam in enumerate(eigvals_c):
        pct = lam / eigvals_c.sum() * 100
        print(f"  λ{i+1} = {lam:.6f}  ({pct:.1f}%)")
    print(f"  Total variance: {eigvals_c.sum():.6f}")

    # Eigenvector loadings
    print(f"\n[{EXP}] === Eigenvector loadings (columns = PCs) ===")
    header = "  " + "  ".join(f"PC{i+1:d}" for i in range(p))
    print(header)
    for j, fname in enumerate(feat_cols):
        row = "  ".join(f"{eigvecs_c[j, i]:+.3f}" for i in range(p))
        print(f"  {fname:8s}  {row}")

    # --- T3: Power law fit ---
    print(f"\n[{EXP}] === T3: Power-law fit ===")
    pl = _fit_power_law(eigvals_c)
    print(f"  α = {pl['alpha']:.4f}, R² = {pl['R2']:.6f}")
    print(f"  Residuals: {pl['residuals']}")

    # --- T4: Marchenko-Pastur ---
    print(f"\n[{EXP}] === T4: Marchenko-Pastur bounds ===")
    # Under null: features are iid Gaussian with variance = mean eigenvalue
    mean_var = eigvals_c.mean()
    mp_lo, mp_hi = _marchenko_pastur_bounds(n_c, p, sigma2=mean_var)
    print(f"  Mean eigenvalue (σ²): {mean_var:.6f}")
    print(f"  MP bounds [λ−, λ+] = [{mp_lo:.6f}, {mp_hi:.6f}]")
    n_above_mp = sum(1 for lam in eigvals_c if lam > mp_hi)
    n_below_mp = sum(1 for lam in eigvals_c if lam < mp_lo)
    print(f"  Eigenvalues above MP upper: {n_above_mp}/5")
    print(f"  Eigenvalues below MP lower: {n_below_mp}/5")

    # More informative: compare to MP with unit variance (standardised)
    # Standardise eigenvalues by dividing by mean
    eigvals_std = eigvals_c / mean_var
    mp_lo_std, mp_hi_std = _marchenko_pastur_bounds(n_c, p, sigma2=1.0)
    print(f"  Standardised MP bounds: [{mp_lo_std:.6f}, {mp_hi_std:.6f}]")
    print(f"  Standardised eigenvalues: {[f'{e:.4f}' for e in eigvals_std]}")

    # --- T5: Effective dimensionality ---
    d_eff = _effective_dim(eigvals_c)
    print(f"\n[{EXP}] === T5: Effective dimensionality ===")
    print(f"  d_eff = {d_eff:.4f} (out of {p})")

    # --- T6: Quran per-eigenmode Phi_M contribution ---
    print(f"\n[{EXP}] === T6: Quran per-eigenmode Phi_M ===")
    mu_q = X_Q.mean(axis=0)
    delta = mu_q - mu_c
    # Project delta onto eigenvectors
    projections = eigvecs_c.T @ delta  # (p,) vector
    # Per-mode contribution to Mahalanobis: (proj_k)^2 / lambda_k
    mah_contributions = projections ** 2 / eigvals_c
    total_mah_sq = mah_contributions.sum()
    print(f"  Quran centroid offset (Δ): {[f'{d:.4f}' for d in delta]}")
    print(f"  Per-mode Φ² contributions:")
    for i in range(p):
        pct = mah_contributions[i] / total_mah_sq * 100
        print(f"    PC{i+1}: proj={projections[i]:+.4f}, "
              f"Φ²={mah_contributions[i]:.4f} ({pct:.1f}%)")
    print(f"  Total Φ² = {total_mah_sq:.4f}, Φ_M = {math.sqrt(total_mah_sq):.4f}")

    # --- T7: Quran internal spectrum ---
    print(f"\n[{EXP}] === T7: Quran-only eigenvalues ===")
    Sigma_q = np.cov(X_Q.T)
    eigvals_q = np.linalg.eigvalsh(Sigma_q)[::-1]
    pl_q = _fit_power_law(eigvals_q)
    d_eff_q = _effective_dim(eigvals_q)
    for i, lam in enumerate(eigvals_q):
        pct = lam / eigvals_q.sum() * 100
        print(f"  λ{i+1} = {lam:.6f}  ({pct:.1f}%)")
    print(f"  α_Quran = {pl_q['alpha']:.4f}, R² = {pl_q['R2']:.6f}")
    print(f"  d_eff_Quran = {d_eff_q:.4f}")

    # --- T8: Bootstrap ---
    print(f"\n[{EXP}] === T8: Bootstrap ({N_BOOT}x) ===")
    rng = np.random.RandomState(SEED)
    boot_alpha = np.empty(N_BOOT)
    boot_deff = np.empty(N_BOOT)
    for i in range(N_BOOT):
        idx = rng.choice(n_c, n_c, replace=True)
        Xb = X_C[idx]
        Sb = np.cov(Xb.T)
        ev = np.linalg.eigvalsh(Sb)[::-1]
        fit = _fit_power_law(ev)
        boot_alpha[i] = fit["alpha"]
        boot_deff[i] = _effective_dim(ev)

    alpha_lo, alpha_hi = np.percentile(boot_alpha, [2.5, 97.5])
    deff_lo, deff_hi = np.percentile(boot_deff, [2.5, 97.5])
    print(f"  α: median={np.median(boot_alpha):.4f}, "
          f"95% CI=[{alpha_lo:.4f}, {alpha_hi:.4f}]")
    print(f"  d_eff: median={np.median(boot_deff):.4f}, "
          f"95% CI=[{deff_lo:.4f}, {deff_hi:.4f}]")

    # --- Verdict ---
    r2 = pl["R2"]
    if r2 >= 0.95:
        verdict = "POWER_LAW"
    elif r2 >= 0.80:
        verdict = "SUGGESTIVE"
    else:
        verdict = "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Power-law R² = {r2:.6f} (threshold ≥ 0.95)")
    print(f"  α = {pl['alpha']:.4f} [{alpha_lo:.4f}, {alpha_hi:.4f}]")
    print(f"  d_eff = {d_eff:.4f} [{deff_lo:.4f}, {deff_hi:.4f}]")
    print(f"  MP violations: {n_above_mp} above upper bound")
    print(f"{'=' * 60}")

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H4 — Does the 5-D covariance eigenvalue spectrum "
                      "follow a power law?",
        "schema_version": 1,
        "control_spectrum": {
            "eigenvalues": [round(float(e), 6) for e in eigvals_c],
            "variance_explained_pct": [
                round(float(e / eigvals_c.sum() * 100), 2) for e in eigvals_c
            ],
            "eigenvectors": eigvecs_c.tolist(),
            "power_law_fit": pl,
            "d_eff": round(d_eff, 4),
        },
        "marchenko_pastur": {
            "mean_variance": round(float(mean_var), 6),
            "mp_lower": round(float(mp_lo), 6),
            "mp_upper": round(float(mp_hi), 6),
            "n_above_upper": n_above_mp,
            "n_below_lower": n_below_mp,
        },
        "quran_eigenmode_phi": {
            "delta": [round(float(d), 6) for d in delta],
            "projections": [round(float(p), 6) for p in projections],
            "mah_sq_per_mode": [round(float(m), 6) for m in mah_contributions],
            "total_phi_m": round(float(math.sqrt(total_mah_sq)), 4),
        },
        "quran_internal_spectrum": {
            "eigenvalues": [round(float(e), 6) for e in eigvals_q],
            "power_law_fit": pl_q,
            "d_eff": round(d_eff_q, 4),
        },
        "bootstrap": {
            "n_boot": N_BOOT,
            "alpha_median": round(float(np.median(boot_alpha)), 4),
            "alpha_ci": [round(float(alpha_lo), 4), round(float(alpha_hi), 4)],
            "deff_median": round(float(np.median(boot_deff)), 4),
            "deff_ci": [round(float(deff_lo), 4), round(float(deff_hi), 4)],
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
