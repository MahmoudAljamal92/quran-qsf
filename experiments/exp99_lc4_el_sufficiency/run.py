"""
exp99_lc4_el_sufficiency/run.py
================================
LC4 — EL Asymptotic Sufficiency Theorem (numeric verification).

Pure-math theorem from PREREG.md §1. This script computes every
quantity in PREREG.md §2 and evaluates every verdict gate in §3. No
new data is generated; everything is a deterministic function of
`phase_06_phi_m`'s X_QURAN, X_CTRL_POOL, and FEAT_COLS.

Claim (LC4): given the pooled within-class covariance of the v7.7
Band-A Arabic-prose pool, the Fisher discriminant direction for
{Quran vs Arabic-ctrl} classification aligns with the EL coordinate
axis to within cos-similarity ≥ 0.95 (pre-registered gate), and
therefore the 1-D EL projection achieves classification AUC within
0.005 of the optimal 5-D LDA classifier.

This is a mathematical claim about a specific observed dataset. It
is falsifiable (α_EL < 0.95 kills it) and portable (any replicator
can recompute Σ̂ and check α_EL).

Pre-registered verdict ladder (see PREREG.md §3):
    FAIL_covariance_singular      min_eig(Σ̂) < 1e-8
    FAIL_alignment_below_gate     α_EL < 0.95
    FAIL_prediction_mismatch_EL   |AUC_pred(EL) − 0.9971| > 0.003
    FAIL_gap_too_large            |AUC(w*) − AUC(EL)| > 0.005
    PASS_LC4                      α_EL ≥ 0.95, all tolerances OK
    PASS_LC4_tight                α_EL ≥ 0.99 AND all AUC gaps < 0.001

Reads (integrity-checked):
    phase_06_phi_m.pkl -> state['X_QURAN'], state['X_CTRL_POOL'],
                         state['FEAT_COLS']

Writes ONLY under results/experiments/exp99_lc4_el_sufficiency/
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

EXP = "exp99_lc4_el_sufficiency"

# --- Frozen constants (mirror PREREG §8) -----------------------------------
SEED = 42
BAND_A_LO, BAND_A_HI = 15, 100
FEAT_NAMES = ["EL", "VL_CV", "CN", "H_cond", "T"]
MIN_EIG_GATE = 1e-8
ALIGNMENT_GATE = 0.95
ALIGNMENT_GATE_TIGHT = 0.99
AUC_MATCH_TOL = 0.003
AUC_GAP_TOL = 0.005
AUC_GAP_TOL_TIGHT = 0.001
OBSERVED_AUC_EL = 0.9971
OBSERVED_AUC_5D = 0.998
BOOTSTRAP_N = 1000


# --- Core math -------------------------------------------------------------
def _pooled_within_class_cov(X_Q: np.ndarray, X_C: np.ndarray) -> np.ndarray:
    """Σ̂ = ((n_Q − 1)·Σ̂_Q + (n_C − 1)·Σ̂_C) / (n_Q + n_C − 2)."""
    n_Q, n_C = X_Q.shape[0], X_C.shape[0]
    S_Q = np.cov(X_Q, rowvar=False, ddof=1)
    S_C = np.cov(X_C, rowvar=False, ddof=1)
    return ((n_Q - 1) * S_Q + (n_C - 1) * S_C) / (n_Q + n_C - 2)


def _fisher_direction(mu_Q: np.ndarray, mu_C: np.ndarray,
                      Sigma: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Returns (w*_raw, w*_unit)."""
    Sigma_inv = np.linalg.inv(Sigma)
    delta_mu = mu_Q - mu_C
    w = Sigma_inv @ delta_mu
    w_unit = w / np.linalg.norm(w)
    return w, w_unit


def _mahalanobis_separation(mu_Q: np.ndarray, mu_C: np.ndarray,
                             Sigma: np.ndarray) -> float:
    """Δ = √((μ_Q − μ_C)ᵀ Σ⁻¹ (μ_Q − μ_C))."""
    delta_mu = mu_Q - mu_C
    Sigma_inv = np.linalg.inv(Sigma)
    return float(math.sqrt(delta_mu @ Sigma_inv @ delta_mu))


def _alignment_cosines(w_unit: np.ndarray, n_feats: int = 5) -> dict:
    """Cosine alignment of w_unit with each standard basis vector e_i."""
    return {FEAT_NAMES[i]: float(abs(w_unit[i])) for i in range(n_feats)}


def _lda_predicted_auc(alpha: float, delta: float) -> float:
    """Under Gaussian LDA with class-conditional means at distance Δ (Mahalanobis)
    along w*, the 1-D projection along a unit vector u yields AUC = Φ(α·Δ/2)
    where α = cos(u, w*). See Anderson 1984 §6.8 or Fukunaga 1990 §4.2."""
    return float(stats.norm.cdf(alpha * delta / 2.0))


# --- Empirical AUC (re-verification, not locked input) ---------------------
def _empirical_auc_1d(scores_Q: np.ndarray, scores_C: np.ndarray) -> float:
    """One-dimensional AUC via Mann–Whitney U (exact rank-sum formulation)."""
    from sklearn.metrics import roc_auc_score
    y = np.concatenate([np.ones(scores_Q.size, dtype=int),
                        np.zeros(scores_C.size, dtype=int)])
    s = np.concatenate([scores_Q, scores_C])
    return float(roc_auc_score(y, s))


# --- Verdict dispatch ------------------------------------------------------
def _verdict(gates: dict) -> str:
    if not gates["covariance_pd"]:
        return "FAIL_covariance_singular"
    if not gates["alignment_pass"]:
        return "FAIL_alignment_below_gate"
    if not gates["prediction_match_EL"]:
        return "FAIL_prediction_mismatch_EL"
    if not gates["gap_within_tol"]:
        return "FAIL_gap_too_large"
    if gates["alignment_tight"] and gates["gap_tight"]:
        return "PASS_LC4_tight"
    return "PASS_LC4"


# --- Main ------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] LC4 — EL Asymptotic Sufficiency Theorem")
    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    X_Q = np.asarray(state["X_QURAN"], dtype=float)
    X_C = np.asarray(state["X_CTRL_POOL"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])
    if feat_cols != FEAT_NAMES:
        print(f"[{EXP}] NOTE: FEAT_COLS={feat_cols} "
              f"reordering to theorem canonical {FEAT_NAMES}")
        order = [feat_cols.index(n) for n in FEAT_NAMES]
        X_Q = X_Q[:, order]
        X_C = X_C[:, order]
    print(f"[{EXP}] n_Q={X_Q.shape[0]}, n_C={X_C.shape[0]}, "
          f"features={FEAT_NAMES}")

    # --- Means and pooled covariance ---
    mu_Q = X_Q.mean(axis=0)
    mu_C = X_C.mean(axis=0)
    Sigma = _pooled_within_class_cov(X_Q, X_C)

    # --- Covariance PD check ---
    eigvals = np.linalg.eigvalsh(Sigma)
    min_eig = float(eigvals.min())
    max_eig = float(eigvals.max())
    cond_num = float(max_eig / max(min_eig, 1e-30))
    covariance_pd = bool(min_eig > MIN_EIG_GATE)
    print(f"[{EXP}] Σ̂ eigenvalues: min={min_eig:.3e}  max={max_eig:.3e}  "
          f"κ={cond_num:.2e}  ({'PD' if covariance_pd else 'SINGULAR'})")

    if not covariance_pd:
        verdict = "FAIL_covariance_singular"
        report = {
            "experiment": EXP,
            "verdict": verdict,
            "error": "Σ̂ not positive definite within MIN_EIG_GATE",
            "min_eig": min_eig, "max_eig": max_eig,
        }
        with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        self_check_end(pre, EXP)
        return 0

    # --- Fisher direction and alignments ---
    w_raw, w_unit = _fisher_direction(mu_Q, mu_C, Sigma)
    alignments = _alignment_cosines(w_unit)
    alpha_EL = alignments["EL"]
    alignment_pass = bool(alpha_EL >= ALIGNMENT_GATE)
    alignment_tight = bool(alpha_EL >= ALIGNMENT_GATE_TIGHT)
    print(f"[{EXP}] Fisher direction ŵ* = "
          f"[{', '.join(f'{w_unit[i]:+.4f}' for i in range(5))}]")
    print(f"[{EXP}] Alignments |⟨ŵ*, e_i⟩|:")
    for name, a in alignments.items():
        print(f"    e_{name:<8s} = {a:.6f}")
    print(f"[{EXP}] α_EL = {alpha_EL:.6f}  "
          f"(gate ≥ {ALIGNMENT_GATE}; tight ≥ {ALIGNMENT_GATE_TIGHT})  "
          f"{'PASS' if alignment_pass else 'FAIL'}")

    # --- Mahalanobis separation ---
    delta = _mahalanobis_separation(mu_Q, mu_C, Sigma)
    print(f"[{EXP}] Mahalanobis Δ = {delta:.6f}")

    # --- Predicted AUCs under LDA ---
    pred_auc_EL = _lda_predicted_auc(alpha_EL, delta)
    pred_auc_w = _lda_predicted_auc(1.0, delta)
    print(f"[{EXP}] Predicted AUC(EL alone) = Φ(α·Δ/2) = {pred_auc_EL:.6f}")
    print(f"[{EXP}] Predicted AUC(w*)       = Φ(Δ/2)   = {pred_auc_w:.6f}")

    # --- Empirical AUCs (re-verification from the same data) ---
    emp_auc_EL = _empirical_auc_1d(X_Q[:, FEAT_NAMES.index("EL")],
                                    X_C[:, FEAT_NAMES.index("EL")])
    score_Q_w = X_Q @ w_unit
    score_C_w = X_C @ w_unit
    emp_auc_w = _empirical_auc_1d(score_Q_w, score_C_w)
    print(f"[{EXP}] Empirical AUC(EL alone)  = {emp_auc_EL:.6f}")
    print(f"[{EXP}] Empirical AUC(w* proj)   = {emp_auc_w:.6f}")
    print(f"[{EXP}] Pre-registered           : AUC(EL) ≈ {OBSERVED_AUC_EL} "
          f"(exp89b); AUC(5-D) ≈ {OBSERVED_AUC_5D} (§4.1)")

    # --- Gates ---
    pred_obs_diff_EL = abs(pred_auc_EL - emp_auc_EL)
    pred_prereg_diff_EL = abs(pred_auc_EL - OBSERVED_AUC_EL)
    auc_gap_emp = abs(emp_auc_w - emp_auc_EL)
    auc_gap_pred = abs(pred_auc_w - pred_auc_EL)
    prediction_match_EL = bool(
        pred_prereg_diff_EL <= AUC_MATCH_TOL
        and pred_obs_diff_EL <= AUC_MATCH_TOL
    )
    gap_within_tol = bool(auc_gap_emp <= AUC_GAP_TOL and auc_gap_pred <= AUC_GAP_TOL)
    gap_tight = bool(auc_gap_emp <= AUC_GAP_TOL_TIGHT and auc_gap_pred <= AUC_GAP_TOL_TIGHT)

    # --- Bootstrap α_EL and AUC gap (optional robustness) ---
    rng = np.random.RandomState(SEED)
    boot_alphas, boot_auc_gaps = [], []
    for _ in range(BOOTSTRAP_N):
        iQ = rng.choice(X_Q.shape[0], X_Q.shape[0], replace=True)
        iC = rng.choice(X_C.shape[0], X_C.shape[0], replace=True)
        Xb_Q, Xb_C = X_Q[iQ], X_C[iC]
        mu_Qb = Xb_Q.mean(axis=0); mu_Cb = Xb_C.mean(axis=0)
        Sb = _pooled_within_class_cov(Xb_Q, Xb_C)
        try:
            _, wb = _fisher_direction(mu_Qb, mu_Cb, Sb)
            boot_alphas.append(float(abs(wb[FEAT_NAMES.index("EL")])))
            db = _mahalanobis_separation(mu_Qb, mu_Cb, Sb)
            boot_auc_gaps.append(float(abs(_lda_predicted_auc(1.0, db)
                                           - _lda_predicted_auc(boot_alphas[-1], db))))
        except np.linalg.LinAlgError:
            continue
    boot_alphas = np.asarray(boot_alphas, dtype=float)
    boot_gaps = np.asarray(boot_auc_gaps, dtype=float)
    alpha_ci = (
        float(np.percentile(boot_alphas, 2.5)),
        float(np.percentile(boot_alphas, 97.5)),
    )
    gap_ci = (
        float(np.percentile(boot_gaps, 2.5)),
        float(np.percentile(boot_gaps, 97.5)),
    )
    print(f"[{EXP}] Bootstrap α_EL 95% CI: [{alpha_ci[0]:.6f}, {alpha_ci[1]:.6f}]  "
          f"(n_boot_valid={boot_alphas.size})")
    print(f"[{EXP}] Bootstrap AUC(w*)-AUC(EL) 95% CI: "
          f"[{gap_ci[0]:.6f}, {gap_ci[1]:.6f}]")

    # --- Verdict dispatch ---
    gates = {
        "covariance_pd": covariance_pd,
        "alignment_pass": alignment_pass,
        "alignment_tight": alignment_tight,
        "prediction_match_EL": prediction_match_EL,
        "gap_within_tol": gap_within_tol,
        "gap_tight": gap_tight,
    }
    verdict = _verdict(gates)

    elapsed = time.time() - t0

    print(f"\n{'=' * 64}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    for k, v in gates.items():
        mark = "OK" if v is True else ("--" if v is None else "FAIL")
        print(f"  {k:26s} {mark} ({v})")
    print(f"{'=' * 64}")

    # --- Receipt ---
    report = {
        "experiment": EXP,
        "hypothesis": "LC4 — EL Asymptotic Sufficiency Theorem "
                      "(α_EL ≥ 0.95 under pooled Σ̂)",
        "schema_version": 1,
        "prereg_document": "experiments/exp99_lc4_el_sufficiency/PREREG.md",
        "frozen_constants": {
            "seed": SEED, "band_a": [BAND_A_LO, BAND_A_HI],
            "feat_names": FEAT_NAMES,
            "min_eig_gate": MIN_EIG_GATE,
            "alignment_gate": ALIGNMENT_GATE,
            "alignment_gate_tight": ALIGNMENT_GATE_TIGHT,
            "auc_match_tol": AUC_MATCH_TOL,
            "auc_gap_tol": AUC_GAP_TOL,
            "auc_gap_tol_tight": AUC_GAP_TOL_TIGHT,
            "observed_auc_EL_prereg": OBSERVED_AUC_EL,
            "observed_auc_5D_prereg": OBSERVED_AUC_5D,
            "bootstrap_n": BOOTSTRAP_N,
        },
        "means": {
            "mu_Q": {FEAT_NAMES[i]: float(mu_Q[i]) for i in range(5)},
            "mu_C": {FEAT_NAMES[i]: float(mu_C[i]) for i in range(5)},
            "delta_mu": {FEAT_NAMES[i]: float(mu_Q[i] - mu_C[i])
                         for i in range(5)},
        },
        "covariance": {
            "eigvals_sorted": [float(v) for v in np.sort(eigvals)],
            "min_eig": min_eig, "max_eig": max_eig,
            "cond_number": cond_num,
            "pd_ok": covariance_pd,
        },
        "fisher_direction": {
            "w_raw": [float(v) for v in w_raw.tolist()],
            "w_unit": [float(v) for v in w_unit.tolist()],
            "alignments_abs_cos": {k: round(v, 6)
                                   for k, v in alignments.items()},
            "alpha_EL": round(alpha_EL, 6),
            "bootstrap_alpha_EL_95ci": {
                "lo": round(alpha_ci[0], 6), "hi": round(alpha_ci[1], 6),
                "width": round(alpha_ci[1] - alpha_ci[0], 6),
            },
        },
        "mahalanobis_separation": {
            "Delta": round(delta, 6),
            "Delta_squared": round(delta ** 2, 6),
        },
        "predictions_lda": {
            "auc_EL_predicted": round(pred_auc_EL, 6),
            "auc_w_predicted":  round(pred_auc_w, 6),
            "predicted_gap":    round(auc_gap_pred, 6),
        },
        "empirical": {
            "auc_EL_empirical": round(emp_auc_EL, 6),
            "auc_w_empirical":  round(emp_auc_w, 6),
            "empirical_gap":    round(auc_gap_emp, 6),
            "observed_auc_EL_frozen_prereg": OBSERVED_AUC_EL,
            "observed_auc_5D_frozen_prereg": OBSERVED_AUC_5D,
        },
        "prediction_match": {
            "pred_vs_empirical_EL_diff": round(pred_obs_diff_EL, 6),
            "pred_vs_prereg_EL_diff": round(pred_prereg_diff_EL, 6),
            "tolerance": AUC_MATCH_TOL,
        },
        "bootstrap_auc_gap_95ci": {
            "lo": round(gap_ci[0], 6), "hi": round(gap_ci[1], 6),
            "width": round(gap_ci[1] - gap_ci[0], 6),
            "n_boot_valid": int(boot_alphas.size),
        },
        "prereg_gates": gates,
        "verdict": verdict,
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=float)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
