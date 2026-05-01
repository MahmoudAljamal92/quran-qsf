"""
exp63_var1_cross_feature/run.py
================================
H24: Multivariate AR(1) Cross-Feature Dynamics — Does the Canonical Surah
Ordering Maximize Cross-Feature Coupling?

Motivation
    exp44 computed scalar AR(1) on verse-length sequences only. The SCAN
    register notes that exp44's code also computes multivariate coefficients,
    but they were never documented or analysed. This experiment extends the
    analysis to the full 5-D feature space via a VAR(1) model:

        X_{t+1} = Phi @ X_t + epsilon

    where X_t in R^5 = z-scored (EL, VL_CV, CN, H_cond, T) at surah t.
    The 5x5 transition matrix Phi captures within-feature persistence
    (diagonal) and cross-feature temporal dynamics (off-diagonal).

    If canonical ordering maximizes cross-feature coupling (spectral radius
    or off-diagonal Frobenius norm vs permutation null), the Mushaf ordering
    is information-theoretically optimized *across* features — a stronger
    result than any single-feature temporal test (exp44, H6).

Protocol (frozen before execution)
    T1. Compute 5x5 VAR(1) Phi for Quran's 114 canonical surahs.
    T2. Spectral radius rho(Phi) = max|eig(Phi)|.
    T3. Permutation null: shuffle surah order 5000x; recompute rho and
        off-diagonal Frobenius norm. p = frac(null >= observed).
    T4. Off-diagonal Frobenius norm = cross-feature coupling strength.
    T5. Same VAR(1) for each Arabic control corpus (natural text order).
        Compare spectral radii and coupling norms.
    T6. Per exp60 guidance: also report 2D (T, EL) sub-model results.
    T7. Identify strongest off-diagonal cross-feature dynamics.

Pre-registered thresholds
    CANONICAL_OPTIMIZED:  p(rho) <= 0.01 AND p(offdiag_F) <= 0.01
    SIGNIFICANT:          p(rho) <= 0.05 OR p(offdiag_F) <= 0.05
    NULL:                 both p > 0.10

Reads (integrity-checked):
    phase_06_phi_m.pkl -> CORPORA, FEAT_COLS

Writes ONLY under results/experiments/exp63_var1_cross_feature/:
    exp63_var1_cross_feature.json
    self_check_<ts>.json
"""
from __future__ import annotations

import json
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
from src import features as ft  # noqa: E402

EXP = "exp63_var1_cross_feature"

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

# Feature indices: FEAT_COLS = [EL, VL_CV, CN, H_cond, T]
IDX_EL = 0
IDX_T = 4
IDX_TE = [IDX_T, IDX_EL]

N_PERM = 5000
MIN_UNITS_FOR_VAR = 15          # skip corpora with fewer units
RIDGE = 1e-6                     # Tikhonov regularisation for OLS
SEED = 42


# ---------------------------------------------------------------------------
# VAR(1) helpers
# ---------------------------------------------------------------------------
def _standardize(X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Z-score each column using the sequence's own mean/std.
    Returns (X_std, mu, sigma). Columns with sigma < 1e-12 are left
    unscaled (set sigma=1) to avoid division-by-zero."""
    mu = X.mean(axis=0)
    sigma = X.std(axis=0, ddof=1)
    sigma = np.where(sigma < 1e-12, 1.0, sigma)
    return (X - mu) / sigma, mu, sigma


def _fit_var1(X_std: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Fit VAR(1) on z-scored sequential data WITHOUT intercept.

    Model: X_std[t+1] = Phi @ X_std[t] + eps
    OLS:   Phi = (Z'Z + ridge*I)^{-1} Z'Y   (ridge for numerical stability)

    Returns (Phi, residuals).
    Phi[i, j] = effect of feature i at time t on feature j at time t+1.
    """
    Y = X_std[1:]    # (n-1, d)
    Z = X_std[:-1]   # (n-1, d)
    d = Z.shape[1]
    ZtZ = Z.T @ Z + RIDGE * np.eye(d)
    ZtY = Z.T @ Y
    Phi = np.linalg.solve(ZtZ, ZtY)   # (d, d)
    residuals = Y - Z @ Phi
    return Phi, residuals


def _spectral_radius(Phi: np.ndarray) -> float:
    return float(np.max(np.abs(np.linalg.eigvals(Phi))))


def _offdiag_frobenius(Phi: np.ndarray) -> float:
    """Frobenius norm of off-diagonal entries = cross-feature coupling."""
    mask = ~np.eye(Phi.shape[0], dtype=bool)
    return float(np.sqrt(np.sum(Phi[mask] ** 2)))


def _diag_norm(Phi: np.ndarray) -> float:
    """L2 norm of diagonal = within-feature persistence."""
    return float(np.sqrt(np.sum(np.diag(Phi) ** 2)))


def _var_summary(Phi: np.ndarray, feat_cols: list[str]) -> dict:
    """Full summary of a VAR(1) transition matrix."""
    eigvals = np.linalg.eigvals(Phi)
    # Sort by magnitude descending
    order = np.argsort(-np.abs(eigvals))
    eigvals = eigvals[order]

    return {
        "Phi": Phi.tolist(),
        "spectral_radius": _spectral_radius(Phi),
        "offdiag_frobenius": _offdiag_frobenius(Phi),
        "diag_norm": _diag_norm(Phi),
        "eigenvalues_real": [float(e.real) for e in eigvals],
        "eigenvalues_imag": [float(e.imag) for e in eigvals],
        "eigenvalues_abs": [float(abs(e)) for e in eigvals],
        "diagonal": {feat_cols[i]: float(Phi[i, i])
                     for i in range(len(feat_cols))},
        "feature_cols": feat_cols,
    }


def _strongest_offdiag(Phi: np.ndarray, feat_cols: list[str],
                       top_k: int = 5) -> list[dict]:
    """Top-k off-diagonal entries by absolute value."""
    d = Phi.shape[0]
    entries = []
    for i in range(d):
        for j in range(d):
            if i != j:
                entries.append({
                    "from": feat_cols[i],
                    "to": feat_cols[j],
                    "coef": float(Phi[i, j]),
                    "abs_coef": float(abs(Phi[i, j])),
                })
    entries.sort(key=lambda x: x["abs_coef"], reverse=True)
    return entries[:top_k]


# ---------------------------------------------------------------------------
# Permutation test
# ---------------------------------------------------------------------------
def _permutation_test(X_raw: np.ndarray, n_perm: int,
                      feat_cols: list[str]) -> dict:
    """Permutation test on canonical vs shuffled orderings.

    X_raw: (n, d) UNstandardized features in canonical order.
    We standardize inside (same mean/std for all permutations — fair
    because permuting rows does not change the column means/stds).
    """
    rng = np.random.RandomState(SEED)
    X_std, _, _ = _standardize(X_raw)

    Phi_canon, resid_canon = _fit_var1(X_std)
    rho_canon = _spectral_radius(Phi_canon)
    frob_canon = _offdiag_frobenius(Phi_canon)

    n = X_std.shape[0]
    rho_null = np.empty(n_perm)
    frob_null = np.empty(n_perm)

    for b in range(n_perm):
        perm = rng.permutation(n)
        Phi_b, _ = _fit_var1(X_std[perm])
        rho_null[b] = _spectral_radius(Phi_b)
        frob_null[b] = _offdiag_frobenius(Phi_b)

    p_rho = float(np.mean(rho_null >= rho_canon))
    p_frob = float(np.mean(frob_null >= frob_canon))

    return {
        "rho_canonical": rho_canon,
        "frob_canonical": frob_canon,
        "p_rho": p_rho,
        "p_frob": p_frob,
        "rho_null_mean": float(rho_null.mean()),
        "rho_null_std": float(rho_null.std(ddof=1)),
        "rho_null_p5": float(np.percentile(rho_null, 5)),
        "rho_null_p95": float(np.percentile(rho_null, 95)),
        "frob_null_mean": float(frob_null.mean()),
        "frob_null_std": float(frob_null.std(ddof=1)),
        "frob_null_p5": float(np.percentile(frob_null, 5)),
        "frob_null_p95": float(np.percentile(frob_null, 95)),
        "n_permutations": n_perm,
        "Phi_canonical": _var_summary(Phi_canon, feat_cols),
        "strongest_offdiag": _strongest_offdiag(Phi_canon, feat_cols),
        "residual_std_per_feat": {
            feat_cols[j]: float(resid_canon[:, j].std(ddof=1))
            for j in range(resid_canon.shape[1])
        },
    }


# ---------------------------------------------------------------------------
# Feature computation
# ---------------------------------------------------------------------------
def _compute_features_ordered(units: list, corpus_name: str,
                              feat_cols: list[str]) -> tuple[np.ndarray, list[str]]:
    """Compute 5-D features for a list of units in their given order.
    Returns (X, labels) where X is (n_valid, 5)."""
    X_list, labels = [], []
    for u in units:
        if len(u.verses) < 3:
            # Skip units with < 3 verses — features are undefined or
            # degenerate (EL needs >=2 pairs, VL_CV needs >=2 values).
            continue
        try:
            f = ft.features_5d(u.verses)
            if np.any(np.isnan(f)) or np.any(np.isinf(f)):
                continue
            X_list.append(f)
            labels.append(u.label)
        except Exception:
            continue
    if not X_list:
        return np.empty((0, 5)), []
    return np.array(X_list, dtype=float), labels


def _sort_quran_units(units: list) -> list:
    """Sort Quran units by surah number (extracted from label 'Q:NNN')."""
    def _surah_num(u):
        lab = u.label
        if ":" in lab:
            try:
                return int(lab.split(":")[1])
            except ValueError:
                return 9999
        return 9999
    return sorted(units, key=_surah_num)


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------
def _compute_verdict(perm_5d: dict, perm_2d: dict | None) -> dict:
    p_rho = perm_5d["p_rho"]
    p_frob = perm_5d["p_frob"]

    if p_rho <= 0.01 and p_frob <= 0.01:
        verdict = "CANONICAL_OPTIMIZED"
    elif p_rho <= 0.05 or p_frob <= 0.05:
        verdict = "SIGNIFICANT"
    elif p_rho > 0.10 and p_frob > 0.10:
        verdict = "NULL"
    else:
        verdict = "INCONCLUSIVE"

    out = {
        "verdict": verdict,
        "p_rho_5D": p_rho,
        "p_frob_5D": p_frob,
        "rho_5D": perm_5d["rho_canonical"],
        "frob_5D": perm_5d["frob_canonical"],
        "prereg_thresholds": {
            "CANONICAL_OPTIMIZED": "p(rho) <= 0.01 AND p(offdiag_F) <= 0.01",
            "SIGNIFICANT": "p(rho) <= 0.05 OR p(offdiag_F) <= 0.05",
            "NULL": "both p > 0.10",
        },
    }
    if perm_2d is not None:
        out["p_rho_2D_TE"] = perm_2d["p_rho"]
        out["p_frob_2D_TE"] = perm_2d["p_frob"]
        out["rho_2D_TE"] = perm_2d["rho_canonical"]
    return out


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

    # --- Load data ---
    print(f"[{EXP}] Loading phase_06_phi_m.pkl (SHA-verified)...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    CORPORA = state["CORPORA"]
    feat_cols = list(state["FEAT_COLS"])
    print(f"[{EXP}] FEAT_COLS = {feat_cols}")

    # --- Quran: 114 surahs in canonical order ---
    quran_units = _sort_quran_units(CORPORA["quran"])
    print(f"[{EXP}] Computing 5-D features for {len(quran_units)} Quran surahs...")
    X_quran, q_labels = _compute_features_ordered(quran_units, "quran", feat_cols)
    n_q = X_quran.shape[0]
    n_dropped = len(quran_units) - n_q
    print(f"[{EXP}] {n_q} Quran surahs with valid features")
    if n_dropped > 0:
        print(f"[{EXP}] WARNING: {n_dropped} surahs dropped — SEQUENCE GAPS "
              f"may weaken VAR(1) temporal interpretation.")
    n_p_ratio = (n_q - 1) / (len(feat_cols) ** 2)  # (n-1) observations, d^2 params
    print(f"[{EXP}] n/p ratio = {n_p_ratio:.1f} "
          f"(n-1={n_q-1} obs, d^2={len(feat_cols)**2} params)")

    if n_q < 30:
        print(f"[{EXP}] ERROR: too few valid surahs ({n_q}). Aborting.")
        return 1

    # --- T1-T4: 5-D VAR(1) + permutation test ---
    print(f"\n[{EXP}] === T1-T4: 5-D VAR(1) + permutation test ({N_PERM}x) ===")
    perm_5d = _permutation_test(X_quran, N_PERM, feat_cols)

    rho = perm_5d["rho_canonical"]
    frob = perm_5d["frob_canonical"]
    print(f"[{EXP}] Spectral radius (canonical)  = {rho:.6f}")
    print(f"[{EXP}] Spectral radius (null mean)  = {perm_5d['rho_null_mean']:.6f} "
          f"(std={perm_5d['rho_null_std']:.6f})")
    print(f"[{EXP}] p(rho)                       = {perm_5d['p_rho']:.4f}")
    print(f"[{EXP}] Off-diag Frob (canonical)    = {frob:.6f}")
    print(f"[{EXP}] Off-diag Frob (null mean)    = {perm_5d['frob_null_mean']:.6f} "
          f"(std={perm_5d['frob_null_std']:.6f})")
    print(f"[{EXP}] p(frob)                      = {perm_5d['p_frob']:.4f}")

    print(f"\n[{EXP}] Diagonal (within-feature persistence):")
    for feat, val in perm_5d["Phi_canonical"]["diagonal"].items():
        print(f"  {feat:8s}: {val:+.4f}")

    print(f"\n[{EXP}] Strongest off-diagonal cross-feature dynamics:")
    for entry in perm_5d["strongest_offdiag"]:
        print(f"  {entry['from']:8s} -> {entry['to']:8s}: {entry['coef']:+.4f}")

    print(f"\n[{EXP}] Eigenvalues of Phi (by |lambda|):")
    for i, (re, im, ab) in enumerate(zip(
        perm_5d["Phi_canonical"]["eigenvalues_real"],
        perm_5d["Phi_canonical"]["eigenvalues_imag"],
        perm_5d["Phi_canonical"]["eigenvalues_abs"],
    )):
        cpx = f" + {im:.4f}i" if abs(im) > 1e-6 else ""
        print(f"  lambda_{i+1}: {re:+.4f}{cpx}  (|lambda| = {ab:.4f})")

    # --- T6: 2-D (T, EL) sub-model ---
    print(f"\n[{EXP}] === T6: 2-D (T, EL) VAR(1) + permutation test ===")
    X_quran_2d = X_quran[:, IDX_TE]
    feat_cols_2d = [feat_cols[i] for i in IDX_TE]
    perm_2d = _permutation_test(X_quran_2d, N_PERM, feat_cols_2d)

    print(f"[{EXP}] 2D rho (canonical) = {perm_2d['rho_canonical']:.6f}, "
          f"p = {perm_2d['p_rho']:.4f}")
    print(f"[{EXP}] 2D offdiag Frob    = {perm_2d['frob_canonical']:.6f}, "
          f"p = {perm_2d['p_frob']:.4f}")

    # --- T5: Control corpora ---
    print(f"\n[{EXP}] === T5: Control corpora VAR(1) ===")
    ctrl_results = {}
    for cname in ARABIC_CTRL:
        units = CORPORA.get(cname, [])
        X_ctrl, c_labels = _compute_features_ordered(units, cname, feat_cols)
        n_c = X_ctrl.shape[0]
        if n_c < MIN_UNITS_FOR_VAR:
            print(f"[{EXP}] {cname:20s}: {n_c:4d} units — SKIPPED (< {MIN_UNITS_FOR_VAR})")
            ctrl_results[cname] = {
                "n_units": n_c,
                "skipped": True,
                "reason": f"fewer than {MIN_UNITS_FOR_VAR} units with valid features",
            }
            continue

        X_std, _, _ = _standardize(X_ctrl)
        Phi_c, _ = _fit_var1(X_std)
        rho_c = _spectral_radius(Phi_c)
        frob_c = _offdiag_frobenius(Phi_c)
        diag_c = _diag_norm(Phi_c)

        print(f"[{EXP}] {cname:20s}: {n_c:4d} units  "
              f"rho={rho_c:.4f}  offdiag_F={frob_c:.4f}  diag={diag_c:.4f}")

        ctrl_results[cname] = {
            "n_units": n_c,
            "skipped": False,
            "spectral_radius": rho_c,
            "offdiag_frobenius": frob_c,
            "diag_norm": diag_c,
            "Phi_summary": _var_summary(Phi_c, feat_cols),
        }

    # --- Verdict ---
    verdict_res = _compute_verdict(perm_5d, perm_2d)
    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict_res['verdict']}")
    print(f"  5-D: rho={verdict_res['rho_5D']:.4f} p={verdict_res['p_rho_5D']:.4f}, "
          f"frob={verdict_res['frob_5D']:.4f} p={verdict_res['p_frob_5D']:.4f}")
    if "rho_2D_TE" in verdict_res:
        print(f"  2-D (T,EL): rho={verdict_res['rho_2D_TE']:.4f} "
              f"p={verdict_res['p_rho_2D_TE']:.4f}")
    print(f"{'=' * 60}")

    # --- Assemble report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H24 — Multivariate AR(1) cross-feature dynamics: "
                      "does canonical surah ordering maximize cross-feature coupling?",
        "schema_version": 1,
        "data": {
            "n_quran_surahs_valid": n_q,
            "n_quran_surahs_total": len(quran_units),
            "n_surahs_dropped": n_dropped,
            "n_p_ratio": round(n_p_ratio, 2),
            "feat_cols": feat_cols,
            "quran_labels": q_labels,
            "ridge_regularization": RIDGE,
            "note_n_p": (
                f"n/p = {n_p_ratio:.1f}. With {n_q-1} temporal observations "
                f"and {len(feat_cols)**2} free parameters in Phi, the VAR(1) "
                f"fit is borderline. Ridge regularization (1e-6) ensures "
                f"numerical stability. The permutation test is valid because "
                f"both canonical and shuffled fits share the same n/p ratio."
            ),
        },
        "T1_T4_5D_var1": perm_5d,
        "T6_2D_TE_var1": perm_2d,
        "T5_control_corpora": ctrl_results,
        "verdict": verdict_res,
        "parameters": {
            "n_permutations": N_PERM,
            "min_units_for_var": MIN_UNITS_FOR_VAR,
            "ridge": RIDGE,
            "seed": SEED,
        },
        "limitations": {
            "no_nuzul_ordering": (
                "No nuzul (chronological revelation) ordering file was found "
                "on disk. The canonical vs nuzul comparison from H24's original "
                "specification could not be run. We use a permutation null "
                "(random surah orderings) instead, which is a stricter test."
            ),
            "short_surahs": (
                f"Surahs with < 3 verses were excluded ({len(quran_units) - n_q} "
                f"dropped). Remaining short surahs (3-10 verses) contribute "
                f"noisy feature estimates but are retained to preserve the "
                f"sequential ordering."
            ),
            "control_ordering": (
                "Control pseudo-surah orderings reflect the natural text order "
                "in each source file. For poetry corpora this may not be a "
                "meaningful sequential ordering. Interpret control spectral "
                "radii cautiously."
            ),
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
