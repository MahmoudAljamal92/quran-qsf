"""
exp70_decision_boundary/run.py
================================
H12: The (T, EL) Decision Boundary as a Maximum-Margin Hyperplane.

Motivation
    LC3 (exp60) showed (T, EL) is the sufficient 2-D subspace.
    The linear SVM boundary in (T, EL) space gives an explicit
    equation separating Quran from controls — "the Quranic equation."

Protocol (frozen before execution)
    T1. Extract (T, EL) for Quran and all controls from phase_06.
    T2. Fit linear SVM (C=1.0) on Band-A data.
    T3. Extract boundary: w1*T + w2*EL + b = 0.
    T4. Normalise: T*cos(θ) + EL*sin(θ) = d.
    T5. Compute margin width M = 2/||w||.
    T6. Bootstrap 10k for CI on θ, d, M.
    T7. Logistic regression as cross-check.
    T8. Report accuracy, AUC, support vectors.
    T9. Per-corpus: which controls are closest / inside the margin?

Reads (integrity-checked):
    phase_06_phi_m.pkl -> X_QURAN, X_CTRL_POOL, FEAT_COLS, FEATS

Writes ONLY under results/experiments/exp70_decision_boundary/
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

EXP = "exp70_decision_boundary"

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

SEED = 42
N_BOOT = 10000
SVM_C = 1.0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    from sklearn.svm import SVC
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, roc_auc_score

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    # --- Load ---
    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    X_Q_5D = np.asarray(state["X_QURAN"], dtype=float)
    X_C_5D = np.asarray(state["X_CTRL_POOL"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])
    feats = state["FEATS"]
    ctrl_pool = list(state["ARABIC_CTRL_POOL"])
    band_lo = int(state.get("BAND_A_LO", 15))
    band_hi = int(state.get("BAND_A_HI", 100))

    # Extract T and EL indices
    t_idx = feat_cols.index("T")
    el_idx = feat_cols.index("EL")
    print(f"[{EXP}] FEAT_COLS={feat_cols}, T={t_idx}, EL={el_idx}")

    # 2-D subsets
    X_Q_2D = X_Q_5D[:, [t_idx, el_idx]]  # columns: T, EL
    X_C_2D = X_C_5D[:, [t_idx, el_idx]]
    n_q, n_c = X_Q_2D.shape[0], X_C_2D.shape[0]
    print(f"[{EXP}] Quran={n_q}, Ctrl={n_c} (Band-A)")

    # Labels: Quran=1, Ctrl=0
    X_all = np.vstack([X_Q_2D, X_C_2D])
    y_all = np.array([1]*n_q + [0]*n_c)

    # --- T2: Fit SVM ---
    print(f"\n[{EXP}] === T2: Linear SVM (C={SVM_C}) ===")
    svm = SVC(kernel="linear", C=SVM_C, random_state=SEED)
    svm.fit(X_all, y_all)

    w = svm.coef_[0]
    b_svm = svm.intercept_[0]
    w_norm = np.linalg.norm(w)

    # --- T3: Boundary equation ---
    # w[0]*T + w[1]*EL + b = 0
    print(f"\n[{EXP}] === T3: Decision boundary ===")
    print(f"  Raw: {w[0]:+.6f}*T + {w[1]:+.6f}*EL + {b_svm:+.6f} = 0")

    # Normalise so coefficients sum to ||w||=1
    w_hat = w / w_norm
    d_norm = -b_svm / w_norm
    print(f"  Normalised: {w_hat[0]:+.6f}*T + {w_hat[1]:+.6f}*EL = {d_norm:+.6f}")

    # --- T4: Polar form ---
    theta = math.atan2(w[1], w[0])
    theta_deg = math.degrees(theta)
    print(f"\n[{EXP}] === T4: Polar form ===")
    print(f"  θ = {theta_deg:.2f}° (atan2(w_EL, w_T))")
    print(f"  d = {d_norm:.6f}")
    print(f"  Equation: T·cos({theta_deg:.1f}°) + EL·sin({theta_deg:.1f}°) = {d_norm:.4f}")

    # --- T5: Margin ---
    margin = 2.0 / w_norm
    print(f"\n[{EXP}] === T5: Margin ===")
    print(f"  ||w|| = {w_norm:.6f}")
    print(f"  Margin M = 2/||w|| = {margin:.6f}")
    n_sv = svm.n_support_
    print(f"  Support vectors: Quran={n_sv[1]}, Ctrl={n_sv[0]}")

    # Accuracy and AUC
    y_pred = svm.predict(X_all)
    acc = accuracy_score(y_all, y_pred)
    dec = svm.decision_function(X_all)
    auc = roc_auc_score(y_all, dec)
    print(f"  Accuracy = {acc:.4f}, AUC = {auc:.4f}")

    # --- T6: Bootstrap ---
    print(f"\n[{EXP}] === T6: Bootstrap ({N_BOOT}x) ===")
    rng = np.random.RandomState(SEED)
    boot_theta = np.empty(N_BOOT)
    boot_d = np.empty(N_BOOT)
    boot_margin = np.empty(N_BOOT)

    for i in range(N_BOOT):
        idx_q = rng.choice(n_q, n_q, replace=True)
        idx_c = rng.choice(n_c, n_c, replace=True)
        Xb = np.vstack([X_Q_2D[idx_q], X_C_2D[idx_c]])
        yb = np.array([1]*n_q + [0]*n_c)
        try:
            svm_b = SVC(kernel="linear", C=SVM_C, random_state=SEED)
            svm_b.fit(Xb, yb)
            wb = svm_b.coef_[0]
            bb = svm_b.intercept_[0]
            wn = np.linalg.norm(wb)
            boot_theta[i] = math.degrees(math.atan2(wb[1], wb[0]))
            boot_d[i] = -bb / wn
            boot_margin[i] = 2.0 / wn
        except Exception:
            boot_theta[i] = float("nan")
            boot_d[i] = float("nan")
            boot_margin[i] = float("nan")

    def _ci(arr, name):
        v = arr[np.isfinite(arr)]
        lo, hi = np.percentile(v, [2.5, 97.5])
        med = np.median(v)
        print(f"  {name}: median={med:.4f}, 95% CI=[{lo:.4f}, {hi:.4f}]")
        return {"median": round(float(med), 4),
                "ci_lo": round(float(lo), 4),
                "ci_hi": round(float(hi), 4)}

    ci_theta = _ci(boot_theta, "θ (degrees)")
    ci_d = _ci(boot_d, "d (normalised)")
    ci_margin = _ci(boot_margin, "Margin M")

    # --- T7: Logistic regression cross-check ---
    print(f"\n[{EXP}] === T7: Logistic regression cross-check ===")
    lr = LogisticRegression(C=SVM_C, solver="lbfgs", random_state=SEED,
                            max_iter=1000)
    lr.fit(X_all, y_all)
    w_lr = lr.coef_[0]
    b_lr = lr.intercept_[0]
    theta_lr = math.degrees(math.atan2(w_lr[1], w_lr[0]))
    y_prob = lr.predict_proba(X_all)[:, 1]
    auc_lr = roc_auc_score(y_all, y_prob)
    acc_lr = accuracy_score(y_all, lr.predict(X_all))
    print(f"  LR boundary: {w_lr[0]:+.6f}*T + {w_lr[1]:+.6f}*EL + {b_lr:+.6f} = 0")
    print(f"  LR θ = {theta_lr:.2f}°")
    print(f"  LR accuracy = {acc_lr:.4f}, AUC = {auc_lr:.4f}")

    # --- T9: Per-corpus distance from boundary ---
    print(f"\n[{EXP}] === T9: Per-corpus distance from boundary ===")
    per_corpus = {}
    ctrl_feats = feats
    offset = 0
    for cname in ctrl_pool:
        recs = [r for r in ctrl_feats.get(cname, [])
                if band_lo <= r["n_verses"] <= band_hi]
        n_this = len(recs)
        if n_this == 0:
            continue
        Xc = X_C_2D[offset:offset+n_this]
        dists = (w[0]*Xc[:, 0] + w[1]*Xc[:, 1] + b_svm) / w_norm
        # Positive = Quran side, negative = ctrl side
        n_quran_side = int(np.sum(dists > 0))
        per_corpus[cname] = {
            "n": n_this,
            "mean_dist": round(float(dists.mean()), 4),
            "min_dist": round(float(dists.min()), 4),
            "n_quran_side": n_quran_side,
            "pct_quran_side": round(float(n_quran_side / n_this * 100), 1),
        }
        print(f"  {cname:20s}: n={n_this:5d}  mean_dist={dists.mean():+.3f}  "
              f"inside_quran={n_quran_side} ({n_quran_side/n_this*100:.1f}%)")
        offset += n_this

    # Quran distances from boundary
    q_dists = (w[0]*X_Q_2D[:, 0] + w[1]*X_Q_2D[:, 1] + b_svm) / w_norm
    n_q_correct = int(np.sum(q_dists > 0))
    print(f"  {'Quran':20s}: n={n_q:5d}  mean_dist={q_dists.mean():+.3f}  "
          f"correct_side={n_q_correct} ({n_q_correct/n_q*100:.1f}%)")

    # --- T, EL statistics ---
    print(f"\n[{EXP}] === Feature statistics ===")
    print(f"  Quran  T: mean={X_Q_2D[:,0].mean():.4f}, std={X_Q_2D[:,0].std():.4f}")
    print(f"  Quran EL: mean={X_Q_2D[:,1].mean():.4f}, std={X_Q_2D[:,1].std():.4f}")
    print(f"  Ctrl   T: mean={X_C_2D[:,0].mean():.4f}, std={X_C_2D[:,0].std():.4f}")
    print(f"  Ctrl  EL: mean={X_C_2D[:,1].mean():.4f}, std={X_C_2D[:,1].std():.4f}")

    elapsed = time.time() - t0

    # --- Summary ---
    print(f"\n{'=' * 60}")
    print(f"[{EXP}] THE QURANIC EQUATION (SVM, Band-A)")
    print(f"  {w[0]:+.6f}·T + {w[1]:+.6f}·EL + {b_svm:+.6f} = 0")
    print(f"  θ = {theta_deg:.2f}° ± [{ci_theta['ci_lo']:.2f}, {ci_theta['ci_hi']:.2f}]")
    print(f"  Margin = {margin:.4f}")
    print(f"  Accuracy = {acc:.2%}, AUC = {auc:.4f}")
    print(f"  Quran correct: {n_q_correct}/{n_q} ({n_q_correct/n_q*100:.1f}%)")
    print(f"{'=' * 60}")

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H12 — (T, EL) decision boundary as maximum-margin "
                      "hyperplane",
        "schema_version": 1,
        "data": {
            "n_quran_bandA": n_q,
            "n_ctrl_bandA": n_c,
            "features": ["T", "EL"],
            "T_idx": t_idx,
            "EL_idx": el_idx,
        },
        "svm": {
            "C": SVM_C,
            "kernel": "linear",
            "equation_raw": {
                "w_T": round(float(w[0]), 8),
                "w_EL": round(float(w[1]), 8),
                "b": round(float(b_svm), 8),
                "form": "w_T*T + w_EL*EL + b = 0",
            },
            "equation_normalised": {
                "w_hat_T": round(float(w_hat[0]), 8),
                "w_hat_EL": round(float(w_hat[1]), 8),
                "d": round(float(d_norm), 8),
                "form": "w_hat_T*T + w_hat_EL*EL = d",
            },
            "polar": {
                "theta_deg": round(theta_deg, 4),
                "d": round(float(d_norm), 6),
            },
            "margin": round(margin, 6),
            "w_norm": round(w_norm, 6),
            "n_support_vectors": {"quran": int(n_sv[1]),
                                   "ctrl": int(n_sv[0])},
            "accuracy": round(acc, 4),
            "auc": round(auc, 4),
            "quran_correct": n_q_correct,
            "quran_total": n_q,
        },
        "bootstrap": {
            "n_boot": N_BOOT,
            "theta": ci_theta,
            "d": ci_d,
            "margin": ci_margin,
        },
        "logistic_regression": {
            "w_T": round(float(w_lr[0]), 8),
            "w_EL": round(float(w_lr[1]), 8),
            "b": round(float(b_lr), 8),
            "theta_deg": round(theta_lr, 4),
            "accuracy": round(acc_lr, 4),
            "auc": round(auc_lr, 4),
        },
        "per_corpus": per_corpus,
        "quran_side": {
            "mean_dist": round(float(q_dists.mean()), 4),
            "min_dist": round(float(q_dists.min()), 4),
            "n_correct": n_q_correct,
        },
        "feature_stats": {
            "quran_T_mean": round(float(X_Q_2D[:, 0].mean()), 4),
            "quran_EL_mean": round(float(X_Q_2D[:, 1].mean()), 4),
            "ctrl_T_mean": round(float(X_C_2D[:, 0].mean()), 4),
            "ctrl_EL_mean": round(float(X_C_2D[:, 1].mean()), 4),
        },
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
