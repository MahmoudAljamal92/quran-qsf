"""
exp89b_five_feature_ablation/run.py
====================================
Characterise AUC of all 5 single features and all 10 two-feature pairs on
Band-A 68 Q + 2 509 Arabic ctrl (same data as exp70, exp89). Identifies
which blessed feature(s) are paper-grade single-feature classifiers.

Pre-registered in PREREG.md as a descriptive experiment, not a hypothesis
test. Reports AUC, accuracy, bootstrap CI for each fit.

Reads (integrity-checked):
    phase_06_phi_m.pkl -> X_QURAN, X_CTRL_POOL, FEAT_COLS

Writes ONLY under results/experiments/exp89b_five_feature_ablation/
"""
from __future__ import annotations

import itertools
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

EXP = "exp89b_five_feature_ablation"
SEED = 42
SVM_C = 1.0
N_BOOT = 500


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
    n_q, n_c = X_Q.shape[0], X_C.shape[0]
    print(f"[{EXP}] Quran={n_q}, Ctrl={n_c}, FEAT_COLS={feat_cols}")

    X_all = np.vstack([X_Q, X_C])
    y_all = np.array([1] * n_q + [0] * n_c)

    # --- Fit helper ---
    def fit_svm(sel_idx: list[int]) -> dict:
        svm = SVC(kernel="linear", C=SVM_C, random_state=SEED)
        svm.fit(X_all[:, sel_idx], y_all)
        dec = svm.decision_function(X_all[:, sel_idx])
        auc = float(roc_auc_score(y_all, dec))
        acc = float(accuracy_score(y_all, svm.predict(X_all[:, sel_idx])))
        return {
            "features": [feat_cols[i] for i in sel_idx],
            "auc": round(auc, 6),
            "accuracy": round(acc, 6),
            "w": [round(float(x), 6) for x in svm.coef_[0].tolist()],
            "b": round(float(svm.intercept_[0]), 6),
        }

    def bootstrap_auc(sel_idx: list[int]) -> dict:
        rng = np.random.RandomState(SEED)
        aucs = []
        for _ in range(N_BOOT):
            idx_q = rng.choice(n_q, n_q, replace=True)
            idx_c = rng.choice(n_c, n_c, replace=True)
            Xb = np.vstack([X_Q[idx_q], X_C[idx_c]])
            yb = np.array([1] * n_q + [0] * n_c)
            svm = SVC(kernel="linear", C=SVM_C, random_state=SEED)
            try:
                svm.fit(Xb[:, sel_idx], yb)
                dec = svm.decision_function(Xb[:, sel_idx])
                aucs.append(float(roc_auc_score(yb, dec)))
            except Exception:
                aucs.append(float("nan"))
        arr = np.array([a for a in aucs if np.isfinite(a)])
        if arr.size == 0:
            return {"median": None, "ci_lo": None, "ci_hi": None, "n_valid": 0}
        lo, hi = np.percentile(arr, [2.5, 97.5])
        return {
            "median": round(float(np.median(arr)), 6),
            "ci_lo": round(float(lo), 6),
            "ci_hi": round(float(hi), 6),
            "n_valid": int(arr.size),
        }

    # --- Single-feature fits ---
    print(f"\n[{EXP}] === 5 single-feature SVM fits ===")
    single_results = []
    for i, fname in enumerate(feat_cols):
        r = fit_svm([i])
        r["ci"] = bootstrap_auc([i])
        single_results.append(r)
        print(f"[{EXP}]   {fname:10s} AUC={r['auc']:.4f}  acc={r['accuracy']:.4f}  "
              f"CI=[{r['ci']['ci_lo']:.4f}, {r['ci']['ci_hi']:.4f}]")

    # Rank
    single_ranked = sorted(single_results, key=lambda r: -r["auc"])
    print(f"\n[{EXP}] === Single-feature ranking ===")
    for rank, r in enumerate(single_ranked, 1):
        print(f"[{EXP}]   #{rank}  {r['features'][0]:10s} AUC={r['auc']:.4f}")

    # --- Two-feature pairs ---
    print(f"\n[{EXP}] === 10 two-feature pair SVM fits ===")
    pair_results = []
    for i, j in itertools.combinations(range(len(feat_cols)), 2):
        r = fit_svm([i, j])
        r["ci"] = bootstrap_auc([i, j])
        pair_results.append(r)
        fn = "+".join(r["features"])
        print(f"[{EXP}]   {fn:20s} AUC={r['auc']:.4f}  acc={r['accuracy']:.4f}  "
              f"CI=[{r['ci']['ci_lo']:.4f}, {r['ci']['ci_hi']:.4f}]")

    pair_ranked = sorted(pair_results, key=lambda r: -r["auc"])
    print(f"\n[{EXP}] === Top-3 pairs ===")
    for rank, r in enumerate(pair_ranked[:3], 1):
        fn = "+".join(r["features"])
        print(f"[{EXP}]   #{rank}  {fn:20s} AUC={r['auc']:.4f}")

    # --- Full 5-D fit (sanity) ---
    print(f"\n[{EXP}] === 5-D full fit (sanity vs headline AUC ~ 0.998) ===")
    full = fit_svm(list(range(len(feat_cols))))
    full["ci"] = bootstrap_auc(list(range(len(feat_cols))))
    print(f"[{EXP}]   ALL 5    AUC={full['auc']:.4f}  acc={full['accuracy']:.4f}  "
          f"CI=[{full['ci']['ci_lo']:.4f}, {full['ci']['ci_hi']:.4f}]")

    # --- Comparative headline ---
    best_single = single_ranked[0]
    best_pair = pair_ranked[0]
    delta_best_pair_minus_best_single = best_pair["auc"] - best_single["auc"]
    delta_full_minus_best_single = full["auc"] - best_single["auc"]

    print(f"\n{'=' * 68}")
    print(f"[{EXP}] HEADLINE")
    print(f"  Best single:  {best_single['features'][0]:10s} AUC={best_single['auc']:.4f}")
    print(f"  Best pair:    {'+'.join(best_pair['features']):20s} AUC={best_pair['auc']:.4f}")
    print(f"  Full 5-D:     {'ALL 5':20s} AUC={full['auc']:.4f}")
    print(f"  Δ (best pair − best single) = {delta_best_pair_minus_best_single:+.4f}")
    print(f"  Δ (5-D       − best single) = {delta_full_minus_best_single:+.4f}")
    print(f"{'=' * 68}")

    # --- Interpretation helpers ---
    # Which single features clear 0.95? 0.99?
    cleared_0_95 = [r["features"][0] for r in single_results if r["auc"] >= 0.95]
    cleared_0_99 = [r["features"][0] for r in single_results if r["auc"] >= 0.99]
    # Is the best pair within 0.005 AUC of the best single?
    joint_is_redundant = delta_best_pair_minus_best_single < 0.005
    # Is the 5-D fit within 0.005 AUC of the best single?
    full_is_redundant = delta_full_minus_best_single < 0.005

    print(f"[{EXP}] Single features clearing 0.95: {cleared_0_95}")
    print(f"[{EXP}] Single features clearing 0.99: {cleared_0_99}")
    print(f"[{EXP}] Best pair adds < 0.005 AUC to best single: {joint_is_redundant}")
    print(f"[{EXP}] Full 5-D adds < 0.005 AUC to best single: {full_is_redundant}")

    elapsed = time.time() - t0

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H-5FA — descriptive 5-feature ablation AUC profile (single, pairs, full)",
        "schema_version": 1,
        "prereg_document": "experiments/exp89b_five_feature_ablation/PREREG.md",
        "data": {
            "n_quran_bandA": n_q,
            "n_ctrl_bandA": n_c,
            "feat_cols": feat_cols,
        },
        "single_feature": single_results,
        "single_feature_ranked": [r["features"][0] for r in single_ranked],
        "two_feature_pairs": pair_results,
        "two_feature_ranked_top3": [
            "+".join(r["features"]) for r in pair_ranked[:3]
        ],
        "full_5D": full,
        "headline": {
            "best_single_feature": best_single["features"][0],
            "best_single_auc": best_single["auc"],
            "best_pair": "+".join(best_pair["features"]),
            "best_pair_auc": best_pair["auc"],
            "full_5D_auc": full["auc"],
            "delta_best_pair_minus_best_single": round(delta_best_pair_minus_best_single, 6),
            "delta_full_minus_best_single": round(delta_full_minus_best_single, 6),
            "single_features_over_0_95": cleared_0_95,
            "single_features_over_0_99": cleared_0_99,
            "best_pair_is_redundant_vs_best_single": bool(joint_is_redundant),
            "full_5D_is_redundant_vs_best_single": bool(full_is_redundant),
        },
        "n_boot": N_BOOT,
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
