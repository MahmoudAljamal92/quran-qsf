"""
exp74 addendum: Subspace Mahalanobis test on PC4+PC5 (the "blind spot").

Two tests:
  1. Compute Mahalanobis T² using ONLY the lowest-variance eigenvectors
     (PC4, PC5) and run a permutation test (10k).
  2. Compute pairwise correlations between PCs in the control pool to
     test whether PC4 (EL) is anti-correlated with PC1 (T/H_cond).

If the subspace T² is still significant (p < 0.001), the Quran's
anomaly is provably concentrated in the control pool's blind spot.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
from scipy import stats as sp_stats

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
from experiments._lib import load_phase, safe_output_dir, self_check_begin, self_check_end

EXP = "exp74_subspace"
SEED = 42
N_PERM = 10000


def main():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir("exp74_eigenvalue_spectrum")
    pre = self_check_begin()
    t0 = time.time()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    X_C = np.asarray(state["X_CTRL_POOL"], dtype=float)
    X_Q = np.asarray(state["X_QURAN"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])
    n_c, p = X_C.shape
    n_q = X_Q.shape[0]

    # Eigendecompose control covariance
    mu_c = X_C.mean(axis=0)
    Sigma_c = np.cov(X_C.T)
    eigvals, eigvecs = np.linalg.eigh(Sigma_c)
    idx = eigvals.argsort()[::-1]
    eigvals = eigvals[idx]
    eigvecs = eigvecs[:, idx]

    print(f"[{EXP}] Features: {feat_cols}")
    print(f"[{EXP}] Eigenvalues: {[f'{e:.6f}' for e in eigvals]}")
    for i in range(p):
        dominant = feat_cols[np.argmax(np.abs(eigvecs[:, i]))]
        print(f"  PC{i+1}: λ={eigvals[i]:.6f} ({eigvals[i]/eigvals.sum()*100:.1f}%) "
              f"dominant={dominant}")

    # ================================================================
    # TEST 1: Subspace Mahalanobis on PC4+PC5 only
    # ================================================================
    print(f"\n{'='*60}")
    print(f"[{EXP}] TEST 1: Subspace Mahalanobis (PC4 + PC5 only)")
    print(f"{'='*60}")

    # Project all data onto PC4 and PC5
    blind_pcs = [3, 4]  # 0-indexed: PC4, PC5
    V_blind = eigvecs[:, blind_pcs]  # (5, 2)
    lam_blind = eigvals[blind_pcs]   # (2,)

    # Project centered data
    X_C_centered = X_C - mu_c
    X_Q_centered = X_Q - mu_c

    Z_C = X_C_centered @ V_blind  # (n_c, 2)
    Z_Q = X_Q_centered @ V_blind  # (n_q, 2)

    # Subspace Mahalanobis: use eigenvalues as variances (already diagonal)
    S_inv_blind = np.diag(1.0 / lam_blind)

    # Per-Quran-surah subspace T²
    q_sub_t2 = np.array([float(z @ S_inv_blind @ z) for z in Z_Q])

    # Quran centroid subspace T²
    mu_q_blind = Z_Q.mean(axis=0)
    centroid_t2 = float(mu_q_blind @ S_inv_blind @ mu_q_blind)

    print(f"  PC4+PC5 eigenvalues: {lam_blind} ({lam_blind/eigvals.sum()*100} % of total)")
    print(f"  Quran centroid subspace T² = {centroid_t2:.2f}")
    print(f"  Quran centroid subspace Φ_M = {np.sqrt(centroid_t2):.4f}")
    print(f"  Per-surah subspace T²: mean={q_sub_t2.mean():.2f}, "
          f"median={np.median(q_sub_t2):.2f}, max={q_sub_t2.max():.2f}")

    # Full-space centroid T² for comparison
    S_inv_full = np.diag(1.0 / eigvals)
    mu_q_full = (X_Q.mean(axis=0) - mu_c)
    Z_Q_full = mu_q_full @ eigvecs
    centroid_t2_full = float(Z_Q_full @ S_inv_full @ Z_Q_full)
    print(f"\n  Full-space centroid T² = {centroid_t2_full:.2f}")
    print(f"  Blind-spot fraction: {centroid_t2/centroid_t2_full*100:.1f}% of total T²")

    # Also compute for PC1+PC2+PC3 (the "normal" space)
    normal_pcs = [0, 1, 2]
    V_normal = eigvecs[:, normal_pcs]
    lam_normal = eigvals[normal_pcs]
    S_inv_normal = np.diag(1.0 / lam_normal)
    mu_q_normal = (X_Q.mean(axis=0) - mu_c) @ V_normal
    centroid_t2_normal = float(mu_q_normal @ S_inv_normal @ mu_q_normal)
    print(f"  Normal-space (PC1-3) T² = {centroid_t2_normal:.2f}")
    print(f"  Normal-space fraction: {centroid_t2_normal/centroid_t2_full*100:.1f}%")

    # Permutation test: shuffle Quran/Ctrl labels
    print(f"\n  Permutation test ({N_PERM}x)...")
    rng = np.random.RandomState(SEED)
    X_all = np.vstack([X_Q, X_C])
    n_all = len(X_all)
    perm_t2 = np.empty(N_PERM)

    for i in range(N_PERM):
        perm_idx = rng.permutation(n_all)
        X_Q_perm = X_all[perm_idx[:n_q]]
        X_C_perm = X_all[perm_idx[n_q:]]
        mu_c_perm = X_C_perm.mean(axis=0)
        cov_perm = np.cov(X_C_perm.T)
        ev_perm, evec_perm = np.linalg.eigh(cov_perm)
        idx_p = ev_perm.argsort()[::-1]
        ev_perm = ev_perm[idx_p]
        evec_perm = evec_perm[:, idx_p]
        V_b = evec_perm[:, blind_pcs]
        lam_b = ev_perm[blind_pcs]
        mu_diff = (X_Q_perm.mean(axis=0) - mu_c_perm) @ V_b
        Si = np.diag(1.0 / np.clip(lam_b, 1e-12, None))
        perm_t2[i] = float(mu_diff @ Si @ mu_diff)

    p_perm = float(np.mean(perm_t2 >= centroid_t2))
    print(f"  Observed blind-spot T² = {centroid_t2:.2f}")
    print(f"  Perm null: mean={perm_t2.mean():.2f}, "
          f"p95={np.percentile(perm_t2, 95):.2f}, "
          f"p99={np.percentile(perm_t2, 99):.2f}, "
          f"max={perm_t2.max():.2f}")
    print(f"  p-value = {p_perm:.6f}")

    sigma_equiv = sp_stats.norm.isf(p_perm / 2) if p_perm > 0 else float("inf")
    print(f"  Equivalent σ = {sigma_equiv:.1f}" if np.isfinite(sigma_equiv) else
          f"  Equivalent σ > {sp_stats.norm.isf(0.5/N_PERM):.1f} (beyond resolution)")

    # ================================================================
    # TEST 2: PC correlations in control pool (trade-off hypothesis)
    # ================================================================
    print(f"\n{'='*60}")
    print(f"[{EXP}] TEST 2: Inter-PC correlations in control pool")
    print(f"{'='*60}")

    # Project controls onto PCs
    PC_scores = X_C_centered @ eigvecs  # (n_c, 5)
    print(f"\n  Correlation matrix of PC scores (should be ~diagonal):")
    corr = np.corrcoef(PC_scores.T)
    for i in range(p):
        row = "  ".join(f"{corr[i,j]:+.4f}" for j in range(p))
        print(f"    PC{i+1}: {row}")

    # Test specific: is PC4 anti-correlated with PC1?
    r_14, p_14 = sp_stats.pearsonr(PC_scores[:, 0], PC_scores[:, 3])
    print(f"\n  PC1 ↔ PC4 correlation: r={r_14:.4f}, p={p_14:.4e}")

    # Also test in ORIGINAL feature space: EL vs T correlation
    el_idx = feat_cols.index("EL")
    t_idx = feat_cols.index("T")
    r_el_t, p_el_t = sp_stats.pearsonr(X_C[:, el_idx], X_C[:, t_idx])
    print(f"  EL ↔ T (raw features): r={r_el_t:.4f}, p={p_el_t:.4e}")

    # Test whether pushing EL high degrades semantic features
    # Look at top-10% EL controls vs bottom-90%
    el_vals = X_C[:, el_idx]
    p90 = np.percentile(el_vals, 90)
    high_el = X_C[el_vals >= p90]
    low_el = X_C[el_vals < p90]
    print(f"\n  High-EL controls (top 10%, n={len(high_el)}) vs rest:")
    for j, fname in enumerate(feat_cols):
        d = (high_el[:, j].mean() - low_el[:, j].mean()) / np.sqrt(
            (high_el[:, j].var(ddof=1) + low_el[:, j].var(ddof=1)) / 2)
        print(f"    {fname:8s}: high_mean={high_el[:,j].mean():.4f}  "
              f"low_mean={low_el[:,j].mean():.4f}  d={d:+.3f}")

    # ================================================================
    # Verdict
    # ================================================================
    if p_perm < 0.001:
        subspace_verdict = "DETERMINATE"
    elif p_perm < 0.05:
        subspace_verdict = "SIGNIFICANT"
    else:
        subspace_verdict = "NOT_SIGNIFICANT"

    elapsed = time.time() - t0

    print(f"\n{'='*60}")
    print(f"[{EXP}] SUBSPACE VERDICT: {subspace_verdict}")
    print(f"  Blind-spot T² = {centroid_t2:.2f} ({centroid_t2/centroid_t2_full*100:.1f}% of total)")
    print(f"  Permutation p = {p_perm:.6f}")
    print(f"  PC1↔PC4 r = {r_14:.4f}")
    print(f"  EL↔T r = {r_el_t:.4f}")
    print(f"{'='*60}")

    report = {
        "experiment": "exp74_subspace_test",
        "parent": "exp74_eigenvalue_spectrum",
        "schema_version": 1,
        "subspace_test": {
            "pcs_used": ["PC4", "PC5"],
            "variance_fraction_pct": round(float(lam_blind.sum() / eigvals.sum() * 100), 2),
            "centroid_t2_blindspot": round(centroid_t2, 4),
            "centroid_t2_full": round(centroid_t2_full, 4),
            "centroid_t2_normal": round(centroid_t2_normal, 4),
            "blindspot_fraction_pct": round(centroid_t2 / centroid_t2_full * 100, 1),
            "perm_p_value": p_perm,
            "perm_null_mean": round(float(perm_t2.mean()), 2),
            "perm_null_p99": round(float(np.percentile(perm_t2, 99)), 2),
        },
        "correlation_test": {
            "pc1_pc4_r": round(float(r_14), 6),
            "pc1_pc4_p": float(p_14),
            "el_t_raw_r": round(float(r_el_t), 6),
            "el_t_raw_p": float(p_el_t),
        },
        "verdict": subspace_verdict,
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / "exp74_subspace_test.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[{EXP}] Wrote {outfile}")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")


if __name__ == "__main__":
    main()
