"""
exp60_lc3_parsimony_theorem/run.py
===================================
H16: The LC3 Parsimony Theorem — (T, EL) as Asymptotic Sufficient Statistics.

Motivation
    exp36_TxEL_seed_metaCI established AUC(T, EL) = 0.9971 ± 0.0006 across
    25 independent seed·fold measurements, while AUC(5-D) = 0.998. The gap is
    below within-fold SD. This experiment formalises WHY: it tests whether (T, EL)
    are *information-theoretically sufficient* for the class label — meaning the
    remaining three features (CN, VL_CV, H_cond) carry negligible conditional MI.

    If proved, this is publishable in IEEE Trans. Information Theory as a pure
    parsimony/sufficiency result, independently of any Quran-specific claim.

Protocol (frozen in PREREG.md before execution)
    T1. Eigendecomposition overlap: compute the pooled 5-D covariance of the
        control pool, eigendecompose, and measure what fraction of the top-2
        eigenvector variance projects onto the (T, EL) subspace.
    T2. Conditional MI: for each k in {CN, VL_CV, H_cond}, compute
        I(class; feature_k | T, EL) via binned estimator with Miller-Madow debias.
    T3. Fisher Information Ratio: fit a 2-class Gaussian model (equal cov) in 5-D,
        compute Fisher discriminant info along (T,EL) vs residual directions.
    T4. Bootstrap CI: 10,000 resamples of T2 for publication-grade CIs.

Pre-registered thresholds
    THEOREM_SUPPORTED:  all 3 cond-MIs < 0.01 bits AND eigvec overlap >= 0.80
                        AND Fisher ratio (residual/total) < 0.05
    PARTIAL:            cond-MIs < 0.05 bits OR overlap >= 0.60
    FAILS:              any cond-MI > 0.10 bits OR overlap < 0.50

Reads (integrity-checked):
    phase_06_phi_m.pkl  →  X_QURAN, X_CTRL_POOL, FEAT_COLS, CORPORA

Writes ONLY under results/experiments/exp60_lc3_parsimony_theorem/:
    exp60_lc3_parsimony_theorem.json
    self_check_<ts>.json
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

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

EXP = "exp60_lc3_parsimony_theorem"

# Indices of T and EL in the canonical FEAT_COLS = [EL, VL_CV, CN, H_cond, T]
IDX_EL = 0
IDX_T  = 4
IDX_TE = [IDX_T, IDX_EL]          # the (T, EL) subspace
IDX_RESID = [1, 2, 3]             # VL_CV, CN, H_cond — the residual dims

N_BOOTSTRAP = 10_000
N_BINS_MI = 8                      # bins per continuous variable for MI estimation
SEED = 42


# ---------------------------------------------------------------------------
# T1: Eigendecomposition overlap onto (T, EL) subspace
# ---------------------------------------------------------------------------
def _eigen_overlap(X_ctrl: np.ndarray, feat_cols: list[str]) -> dict:
    """Compute how much of the top-k eigenvariance projects onto (T, EL)."""
    Sigma = np.cov(X_ctrl.T, ddof=1)
    eigvals, eigvecs = np.linalg.eigh(Sigma)
    # eigh returns ascending; flip to descending
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]

    total_var = eigvals.sum()
    explained_ratio = eigvals / total_var

    # For each eigenvector, compute its squared projection onto the (T,EL) subspace
    # = sum of squared components in the T and EL dimensions
    overlaps = []
    for k in range(len(eigvals)):
        v = eigvecs[:, k]
        proj_sq = v[IDX_T]**2 + v[IDX_EL]**2  # fraction of this eigvec in (T,EL)
        overlaps.append(float(proj_sq))

    # Weighted overlap: sum over all eigenvectors of (explained_ratio_k * overlap_k)
    weighted_overlap = float(np.dot(explained_ratio, overlaps))

    # Top-2 eigenvector overlap (what fraction of top-2 variance lives in T,EL)
    top2_overlap = float(
        (explained_ratio[0] * overlaps[0] + explained_ratio[1] * overlaps[1])
        / (explained_ratio[0] + explained_ratio[1])
    )

    return {
        "eigenvalues": eigvals.tolist(),
        "explained_variance_ratio": explained_ratio.tolist(),
        "per_eigvec_TE_overlap": overlaps,
        "weighted_TE_overlap": weighted_overlap,
        "top2_TE_overlap": top2_overlap,
        "feature_cols": feat_cols,
        "TE_indices": IDX_TE,
        "note": (
            "per_eigvec_TE_overlap[k] = fraction of eigenvector k's unit norm "
            "that lies in the (T, EL) subspace (squared L2). "
            "top2_TE_overlap = variance-weighted mean of the first two."
        ),
    }


# ---------------------------------------------------------------------------
# T2: Conditional MI via binned estimator with Miller-Madow debias
# ---------------------------------------------------------------------------
def _discretize(x: np.ndarray, n_bins: int) -> np.ndarray:
    """Equal-frequency binning into n_bins quantile bins."""
    edges = np.percentile(x, np.linspace(0, 100, n_bins + 1))
    edges[0] -= 1e-10
    edges[-1] += 1e-10
    return np.digitize(x, edges[1:-1])


def _entropy_mm(counts: np.ndarray) -> float:
    """Shannon entropy with Miller-Madow bias correction."""
    n = counts.sum()
    if n == 0:
        return 0.0
    p = counts / n
    p = p[p > 0]
    H = -float(np.sum(p * np.log2(p)))
    m = int((p > 0).sum())
    mm_correction = (m - 1) / (2 * n * math.log(2)) if n > 0 else 0.0
    return H + mm_correction


def _joint_counts(a: np.ndarray, b: np.ndarray, na: int, nb: int) -> np.ndarray:
    """2-D contingency table."""
    table = np.zeros((na, nb), dtype=int)
    for i, j in zip(a, b):
        table[i, j] += 1
    return table


def _conditional_mi_single(
    y: np.ndarray, xk: np.ndarray,
    t_bins: np.ndarray, el_bins: np.ndarray,
    n_bins_cond: int,
) -> float:
    """I(class; feature_k | T_bin, EL_bin) via chain rule.

    = H(class | T,EL) - H(class | T,EL,feature_k)
    = sum over (t,el) strata of P(t,el) * [H(class|t,el) - H(class|t,el,k)]

    Uses Miller-Madow debiased entropy at each stratum.
    """
    xk_bins = _discretize(xk, n_bins_cond)

    # Unique (T,EL) strata
    strata = {}
    for idx in range(len(y)):
        key = (int(t_bins[idx]), int(el_bins[idx]))
        if key not in strata:
            strata[key] = []
        strata[key].append(idx)

    n_total = len(y)
    cmi = 0.0
    for key, indices in strata.items():
        indices = np.array(indices)
        p_stratum = len(indices) / n_total

        y_s = y[indices]
        xk_s = xk_bins[indices]

        # H(class | T=t, EL=el)
        class_counts = np.bincount(y_s, minlength=2)
        h_class_given_te = _entropy_mm(class_counts)

        # H(class | T=t, EL=el, feature_k)
        xk_unique = np.unique(xk_s)
        h_class_given_tek = 0.0
        for xv in xk_unique:
            mask = xk_s == xv
            p_xv = mask.sum() / len(indices)
            if p_xv > 0:
                cc = np.bincount(y_s[mask], minlength=2)
                h_class_given_tek += p_xv * _entropy_mm(cc)

        cmi += p_stratum * max(0.0, h_class_given_te - h_class_given_tek)

    return cmi


def _compute_conditional_mis(
    X: np.ndarray, y: np.ndarray, feat_cols: list[str]
) -> dict:
    """Compute I(class; feature_k | T, EL) for k in {VL_CV, CN, H_cond}."""
    rng = np.random.RandomState(SEED)

    t_bins = _discretize(X[:, IDX_T], N_BINS_MI)
    el_bins = _discretize(X[:, IDX_EL], N_BINS_MI)

    results = {}
    for k_idx, k_name in [(1, "VL_CV"), (2, "CN"), (3, "H_cond")]:
        cmi = _conditional_mi_single(y, X[:, k_idx], t_bins, el_bins, N_BINS_MI)
        results[k_name] = {
            "conditional_MI_bits": cmi,
            "n_bins_per_dim": N_BINS_MI,
            "note": f"I(class; {k_name} | T, EL) with Miller-Madow debias",
        }

    return results


# ---------------------------------------------------------------------------
# T3: Fisher Information Ratio
# ---------------------------------------------------------------------------
def _fisher_info_ratio(X: np.ndarray, y: np.ndarray) -> dict:
    """Compute the Fisher discriminant information along (T,EL) vs residual.

    Under equal-covariance Gaussian assumption:
      Fisher criterion = (mu1 - mu0)^T Sigma^{-1} (mu1 - mu0)
    We decompose this into contributions from the (T,EL) subspace and the
    residual (VL_CV, CN, H_cond) subspace.
    """
    X0, X1 = X[y == 0], X[y == 1]
    n0, n1 = len(X0), len(X1)
    mu0, mu1 = X0.mean(0), X1.mean(0)
    S0, S1 = np.cov(X0.T, ddof=1), np.cov(X1.T, ddof=1)
    Sp = ((n0 - 1) * S0 + (n1 - 1) * S1) / (n0 + n1 - 2)
    Sp_inv = np.linalg.inv(Sp + 1e-8 * np.eye(5))

    diff = mu1 - mu0
    fisher_total = float(diff @ Sp_inv @ diff)

    # Project onto (T, EL) subspace: zero out the residual components of diff
    diff_te = np.zeros_like(diff)
    diff_te[IDX_TE] = diff[IDX_TE]
    fisher_te = float(diff_te @ Sp_inv @ diff_te)

    # Residual subspace
    diff_resid = np.zeros_like(diff)
    diff_resid[IDX_RESID] = diff[IDX_RESID]
    fisher_resid = float(diff_resid @ Sp_inv @ diff_resid)

    # Cross-term (due to off-diagonal covariance)
    fisher_cross = fisher_total - fisher_te - fisher_resid

    return {
        "fisher_total": fisher_total,
        "fisher_TE_subspace": fisher_te,
        "fisher_residual_subspace": fisher_resid,
        "fisher_cross_term": fisher_cross,
        "fisher_TE_fraction": fisher_te / max(fisher_total, 1e-12),
        "fisher_residual_fraction": fisher_resid / max(fisher_total, 1e-12),
        "fisher_cross_fraction": fisher_cross / max(fisher_total, 1e-12),
        "note": (
            "Fisher discriminant decomposed into (T,EL) and (VL_CV,CN,H_cond) "
            "subspaces. Cross-term arises from off-diagonal covariance. "
            "If fisher_residual_fraction < 0.05, the residual dims carry <5% "
            "of the discriminant information."
        ),
    }


# ---------------------------------------------------------------------------
# T4: Bootstrap CI on conditional MIs
# ---------------------------------------------------------------------------
def _bootstrap_cmi(
    X: np.ndarray, y: np.ndarray, n_boot: int = N_BOOTSTRAP
) -> dict:
    """Bootstrap 10k resamples of the conditional MI for each residual feature."""
    rng = np.random.RandomState(SEED)
    n = len(y)

    boot_results = {name: [] for name in ["VL_CV", "CN", "H_cond"]}

    for b in range(n_boot):
        idx = rng.choice(n, n, replace=True)
        Xb, yb = X[idx], y[idx]

        t_bins = _discretize(Xb[:, IDX_T], N_BINS_MI)
        el_bins = _discretize(Xb[:, IDX_EL], N_BINS_MI)

        for k_idx, k_name in [(1, "VL_CV"), (2, "CN"), (3, "H_cond")]:
            cmi = _conditional_mi_single(yb, Xb[:, k_idx], t_bins, el_bins, N_BINS_MI)
            boot_results[k_name].append(cmi)

    summary = {}
    for k_name, vals in boot_results.items():
        arr = np.array(vals)
        summary[k_name] = {
            "bootstrap_mean": float(arr.mean()),
            "bootstrap_std": float(arr.std(ddof=1)),
            "ci_2_5": float(np.percentile(arr, 2.5)),
            "ci_97_5": float(np.percentile(arr, 97.5)),
            "ci_0_5": float(np.percentile(arr, 0.5)),
            "ci_99_5": float(np.percentile(arr, 99.5)),
            "fraction_below_001": float((arr < 0.01).mean()),
            "fraction_below_005": float((arr < 0.05).mean()),
            "n_bootstrap": n_boot,
        }
    return summary


# ---------------------------------------------------------------------------
# Verdict logic
# ---------------------------------------------------------------------------
def _compute_verdict(eigen_res: dict, cmi_res: dict, fisher_res: dict,
                     boot_res: dict) -> dict:
    """Apply pre-registered thresholds."""
    max_cmi = max(
        cmi_res["VL_CV"]["conditional_MI_bits"],
        cmi_res["CN"]["conditional_MI_bits"],
        cmi_res["H_cond"]["conditional_MI_bits"],
    )
    all_below_001 = bool(max_cmi < 0.01)
    all_below_005 = bool(max_cmi < 0.05)
    any_above_010 = bool(max_cmi > 0.10)

    overlap = eigen_res["top2_TE_overlap"]
    fisher_resid = fisher_res["fisher_residual_fraction"]

    if all_below_001 and overlap >= 0.80 and fisher_resid < 0.05:
        verdict = "THEOREM_SUPPORTED"
    elif all_below_005 or overlap >= 0.60:
        verdict = "PARTIAL"
    elif any_above_010 or overlap < 0.50:
        verdict = "FAILS"
    else:
        verdict = "PARTIAL"

    # Formal theorem statement attempt
    theorem_statement = None
    if verdict == "THEOREM_SUPPORTED":
        theorem_statement = (
            "Under the class-conditional Gaussian model p(x|c) = N(mu_c, Sigma) "
            "with the observed Sigma eigenstructure of the 2,509-unit Arabic "
            "control pool, the features (T, EL) are asymptotic sufficient "
            "statistics for the class label c at AUC -> 1. The conditional "
            "mutual information I(c; {CN, VL_CV, H_cond} | T, EL) < 0.01 bits "
            "for each residual feature, and the top-2 eigenvectors of the pooled "
            "covariance project >= 80% of their variance onto the (T, EL) subspace."
        )

    return {
        "verdict": verdict,
        "max_conditional_MI_bits": max_cmi,
        "all_cmi_below_001_bits": all_below_001,
        "all_cmi_below_005_bits": all_below_005,
        "any_cmi_above_010_bits": any_above_010,
        "top2_TE_overlap": overlap,
        "fisher_residual_fraction": fisher_resid,
        "theorem_statement": theorem_statement,
        "prereg_thresholds": {
            "THEOREM_SUPPORTED": "all CMI < 0.01 AND overlap >= 0.80 AND fisher_resid < 0.05",
            "PARTIAL": "all CMI < 0.05 OR overlap >= 0.60",
            "FAILS": "any CMI > 0.10 OR overlap < 0.50",
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    # --- Load SHA-pinned state ---
    print(f"[{EXP}] Loading phase_06_phi_m.pkl (SHA-verified)...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    X_Q = np.asarray(state["X_QURAN"], dtype=float)
    X_C = np.asarray(state["X_CTRL_POOL"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])

    n_q, n_c = X_Q.shape[0], X_C.shape[0]
    print(f"[{EXP}] X_QURAN {X_Q.shape}, X_CTRL_POOL {X_C.shape}")
    print(f"[{EXP}] FEAT_COLS = {feat_cols}")

    # Combined matrix with labels
    X_all = np.vstack([X_Q, X_C])
    y_all = np.concatenate([np.ones(n_q, dtype=int), np.zeros(n_c, dtype=int)])

    # --- T1: Eigendecomposition ---
    print(f"\n[{EXP}] === T1: Eigendecomposition overlap ===")
    eigen_res = _eigen_overlap(X_C, feat_cols)
    print(f"[{EXP}] Eigenvalues: {['%.4f' % v for v in eigen_res['eigenvalues']]}")
    print(f"[{EXP}] Explained ratio: {['%.4f' % v for v in eigen_res['explained_variance_ratio']]}")
    print(f"[{EXP}] Per-eigvec (T,EL) overlap: {['%.4f' % v for v in eigen_res['per_eigvec_TE_overlap']]}")
    print(f"[{EXP}] Weighted (T,EL) overlap = {eigen_res['weighted_TE_overlap']:.6f}")
    print(f"[{EXP}] Top-2 (T,EL) overlap    = {eigen_res['top2_TE_overlap']:.6f}")

    # --- T2: Conditional MI ---
    print(f"\n[{EXP}] === T2: Conditional MI (binned, Miller-Madow) ===")
    cmi_res = _compute_conditional_mis(X_all, y_all, feat_cols)
    for k_name, v in cmi_res.items():
        print(f"[{EXP}] I(class; {k_name:6s} | T, EL) = {v['conditional_MI_bits']:.6f} bits")

    # --- T3: Fisher Information ---
    print(f"\n[{EXP}] === T3: Fisher Information Ratio ===")
    fisher_res = _fisher_info_ratio(X_all, y_all)
    print(f"[{EXP}] Fisher total          = {fisher_res['fisher_total']:.6f}")
    print(f"[{EXP}] Fisher (T,EL)         = {fisher_res['fisher_TE_subspace']:.6f} "
          f"({fisher_res['fisher_TE_fraction']:.4f})")
    print(f"[{EXP}] Fisher residual       = {fisher_res['fisher_residual_subspace']:.6f} "
          f"({fisher_res['fisher_residual_fraction']:.4f})")
    print(f"[{EXP}] Fisher cross-term     = {fisher_res['fisher_cross_term']:.6f} "
          f"({fisher_res['fisher_cross_fraction']:.4f})")

    # --- T4: Bootstrap CI ---
    print(f"\n[{EXP}] === T4: Bootstrap CI ({N_BOOTSTRAP} resamples) ===")
    boot_res = _bootstrap_cmi(X_all, y_all, N_BOOTSTRAP)
    for k_name, v in boot_res.items():
        print(f"[{EXP}] {k_name:6s} CMI boot: "
              f"mean={v['bootstrap_mean']:.6f}  "
              f"95% CI=[{v['ci_2_5']:.6f}, {v['ci_97_5']:.6f}]  "
              f"P(<0.01)={v['fraction_below_001']:.3f}")

    # --- Verdict ---
    verdict_res = _compute_verdict(eigen_res, cmi_res, fisher_res, boot_res)
    elapsed = time.time() - t0

    print(f"\n{'='*60}")
    print(f"[{EXP}] VERDICT: {verdict_res['verdict']}")
    if verdict_res['theorem_statement']:
        print(f"[{EXP}] THEOREM:")
        print(f"  {verdict_res['theorem_statement']}")
    print(f"{'='*60}")

    # --- Assemble report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H16 — LC3 Parsimony Theorem: (T, EL) as sufficient statistics",
        "schema_version": 1,
        "data": {
            "n_quran_bandA": n_q,
            "n_ctrl_bandA": n_c,
            "feat_cols": feat_cols,
            "TE_indices": IDX_TE,
            "residual_indices": IDX_RESID,
        },
        "T1_eigendecomposition": eigen_res,
        "T2_conditional_MI": cmi_res,
        "T3_fisher_information": fisher_res,
        "T4_bootstrap_CI": boot_res,
        "verdict": verdict_res,
        "baseline_reference": {
            "exp36_AUC_TxEL": "0.9971 ± 0.0006 (25 seed·fold)",
            "exp36_AUC_5D": "0.998",
            "note": "This experiment explains WHY the 2-D AUC equals the 5-D AUC",
        },
        "parameters": {
            "n_bins_MI": N_BINS_MI,
            "n_bootstrap": N_BOOTSTRAP,
            "seed": SEED,
        },
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    # --- Self-check ---
    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED — no protected files mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
