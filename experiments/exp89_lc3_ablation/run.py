"""
exp89_lc3_ablation/run.py
==========================
Pre-registered single-feature ablation of LC3-70-U's (T, EL) sufficiency.

Protocol (frozen in PREREG.md, committed before any run)
    Fit three linear SVMs (same C=1.0, same SEED=42 as exp70):
      (1) T only        (2) EL only         (3) (T, EL) joint
    Report AUC and accuracy for each. 1 000-sample bootstrap CIs.

Pre-registered verdicts (evaluated in order):
    FAIL_sanity_exp70_drift  |AUC_TEL - 0.9975| > 0.001
    FAIL_joint_weak          AUC_TEL < 0.99
    FAIL_T_dominates         AUC_T  >= 0.95
    FAIL_EL_dominates        AUC_EL >= 0.95
    PASS                     AUC_T < 0.95 AND AUC_EL < 0.95 AND AUC_TEL >= 0.99
    MIXED                    any other outcome (should not occur)

Reads (integrity-checked):
    phase_06_phi_m.pkl -> X_QURAN, X_CTRL_POOL, FEAT_COLS

Writes ONLY under results/experiments/exp89_lc3_ablation/
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

EXP = "exp89_lc3_ablation"
SEED = 42
SVM_C = 1.0
N_BOOT = 1_000

# --- Pre-registered thresholds (DO NOT MODIFY; see PREREG.md) ---
THRESHOLD_SINGLE = 0.95
THRESHOLD_JOINT = 0.99
EXP70_AUC_EXPECTED = 0.9975
EXP70_AUC_TOL = 0.001


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    from sklearn.svm import SVC
    from sklearn.metrics import accuracy_score, roc_auc_score

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    # --- Load ---
    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    X_Q = np.asarray(state["X_QURAN"], dtype=float)
    X_C = np.asarray(state["X_CTRL_POOL"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])

    t_idx = feat_cols.index("T")
    el_idx = feat_cols.index("EL")
    n_q, n_c = X_Q.shape[0], X_C.shape[0]
    print(f"[{EXP}] Quran={n_q}, Ctrl={n_c}, FEAT_COLS={feat_cols}")
    print(f"[{EXP}] t_idx={t_idx}, el_idx={el_idx}")

    X_all = np.vstack([X_Q, X_C])
    y_all = np.array([1] * n_q + [0] * n_c)

    # --- Three SVM fits ---
    def fit_svm(X_sel: np.ndarray, name: str) -> dict:
        svm = SVC(kernel="linear", C=SVM_C, random_state=SEED)
        svm.fit(X_sel, y_all)
        dec = svm.decision_function(X_sel)
        auc = float(roc_auc_score(y_all, dec))
        acc = float(accuracy_score(y_all, svm.predict(X_sel)))
        print(f"[{EXP}] {name:15s}  AUC={auc:.4f}  acc={acc:.4f}")
        return {
            "auc": round(auc, 6),
            "accuracy": round(acc, 6),
            "w": [round(float(x), 8) for x in svm.coef_[0].tolist()],
            "b": round(float(svm.intercept_[0]), 8),
            "n_support": {
                "quran": int(svm.n_support_[1]),
                "ctrl": int(svm.n_support_[0]),
            },
        }

    print(f"\n[{EXP}] === Three linear-SVM fits (C={SVM_C}, seed={SEED}) ===")
    res_T = fit_svm(X_all[:, [t_idx]], "T only")
    res_EL = fit_svm(X_all[:, [el_idx]], "EL only")
    res_TEL = fit_svm(X_all[:, [t_idx, el_idx]], "T, EL joint")

    # --- Bootstrap ---
    print(f"\n[{EXP}] === Bootstrap AUC ({N_BOOT}x, within-class resample) ===")
    rng = np.random.RandomState(SEED)
    sel_map = {"T": [t_idx], "EL": [el_idx], "TEL": [t_idx, el_idx]}
    boot: dict[str, list[float]] = {k: [] for k in sel_map}
    n_fail = 0
    for _ in range(N_BOOT):
        idx_q = rng.choice(n_q, n_q, replace=True)
        idx_c = rng.choice(n_c, n_c, replace=True)
        Xb = np.vstack([X_Q[idx_q], X_C[idx_c]])
        yb = np.array([1] * n_q + [0] * n_c)
        for key, sel in sel_map.items():
            svm_b = SVC(kernel="linear", C=SVM_C, random_state=SEED)
            try:
                svm_b.fit(Xb[:, sel], yb)
                dec_b = svm_b.decision_function(Xb[:, sel])
                boot[key].append(float(roc_auc_score(yb, dec_b)))
            except Exception:
                boot[key].append(float("nan"))
                n_fail += 1

    def _ci(arr_key: str) -> dict:
        arr = np.array([a for a in boot[arr_key] if np.isfinite(a)])
        if arr.size == 0:
            return {"median": None, "ci_lo": None, "ci_hi": None, "n_valid": 0}
        lo, hi = np.percentile(arr, [2.5, 97.5])
        return {
            "median": round(float(np.median(arr)), 6),
            "ci_lo": round(float(lo), 6),
            "ci_hi": round(float(hi), 6),
            "n_valid": int(arr.size),
        }

    ci_T = _ci("T")
    ci_EL = _ci("EL")
    ci_TEL = _ci("TEL")
    print(f"[{EXP}] T only   95% CI=[{ci_T['ci_lo']:.4f}, {ci_T['ci_hi']:.4f}]  (n={ci_T['n_valid']})")
    print(f"[{EXP}] EL only  95% CI=[{ci_EL['ci_lo']:.4f}, {ci_EL['ci_hi']:.4f}]  (n={ci_EL['n_valid']})")
    print(f"[{EXP}] T, EL    95% CI=[{ci_TEL['ci_lo']:.4f}, {ci_TEL['ci_hi']:.4f}]  (n={ci_TEL['n_valid']})")
    if n_fail:
        print(f"[{EXP}] WARN: {n_fail} bootstrap fits failed (total attempts {3 * N_BOOT}).")

    # --- Pre-registered verdict ladder ---
    auc_T, auc_EL, auc_TEL = res_T["auc"], res_EL["auc"], res_TEL["auc"]
    sanity = abs(auc_TEL - EXP70_AUC_EXPECTED) <= EXP70_AUC_TOL
    T_under = auc_T < THRESHOLD_SINGLE
    EL_under = auc_EL < THRESHOLD_SINGLE
    joint_over = auc_TEL >= THRESHOLD_JOINT

    if not sanity:
        verdict = "FAIL_sanity_exp70_drift"
    elif not joint_over:
        verdict = "FAIL_joint_weak"
    elif not T_under:
        verdict = "FAIL_T_dominates"
    elif not EL_under:
        verdict = "FAIL_EL_dominates"
    elif T_under and EL_under and joint_over:
        verdict = "PASS"
    else:
        verdict = "MIXED"

    elapsed = time.time() - t0

    # --- Summary ---
    print(f"\n{'=' * 64}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    print(f"  AUC(T only)   = {auc_T:.4f}   threshold < {THRESHOLD_SINGLE}  -> {'OK' if T_under else 'VIOLATED'}")
    print(f"  AUC(EL only)  = {auc_EL:.4f}   threshold < {THRESHOLD_SINGLE}  -> {'OK' if EL_under else 'VIOLATED'}")
    print(f"  AUC(T, EL)    = {auc_TEL:.4f}   threshold >= {THRESHOLD_JOINT} -> {'OK' if joint_over else 'VIOLATED'}")
    print(f"  exp70 sanity  = {'OK' if sanity else 'DRIFT'} (expected {EXP70_AUC_EXPECTED} +/- {EXP70_AUC_TOL})")
    print(f"{'=' * 64}")

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H-LC3-ABL — Pre-registered 1-vs-2 feature ablation of LC3-70-U (T, EL) sufficiency",
        "schema_version": 1,
        "prereg_document": "experiments/exp89_lc3_ablation/PREREG.md",
        "prereg_thresholds": {
            "single_feature_max_auc": THRESHOLD_SINGLE,
            "joint_feature_min_auc": THRESHOLD_JOINT,
            "sanity_exp70_auc_expected": EXP70_AUC_EXPECTED,
            "sanity_exp70_tol": EXP70_AUC_TOL,
        },
        "data": {
            "n_quran_bandA": n_q,
            "n_ctrl_bandA": n_c,
            "feat_cols": feat_cols,
            "t_idx": t_idx,
            "el_idx": el_idx,
        },
        "T_only": res_T,
        "EL_only": res_EL,
        "TEL_joint": res_TEL,
        "bootstrap": {
            "n_boot": N_BOOT,
            "T_only_ci": ci_T,
            "EL_only_ci": ci_EL,
            "TEL_joint_ci": ci_TEL,
            "n_fit_failures": n_fail,
        },
        "sanity_check": {
            "exp70_auc_expected": EXP70_AUC_EXPECTED,
            "exp70_auc_observed": auc_TEL,
            "abs_diff": round(abs(auc_TEL - EXP70_AUC_EXPECTED), 6),
            "within_tolerance": sanity,
        },
        "prereg_test": {
            "T_only_under_threshold": bool(T_under),
            "EL_only_under_threshold": bool(EL_under),
            "TEL_over_threshold": bool(joint_over),
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
