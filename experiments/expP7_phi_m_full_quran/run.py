"""
expP7_phi_m_full_quran/run.py
=============================
H37: The 5-D Hotelling T² and 5-D classifier headline (v7.7: T² = 3 557 on
band-A 68) survives when the Quran sample is expanded from band-A (68 surahs)
to ALL 114 surahs and the control pool is expanded to the full 4 719-unit
Arabic-prose pool.

Pre-registered in PREREG.md (frozen 2026-04-26).

Reads (integrity-checked):
    phase_06_phi_m.pkl                                    state['CORPORA']
    results/integrity/results_lock.json::Phi_M_hotelling_T2  band-A sanity

Writes ONLY under results/experiments/expP7_phi_m_full_quran/
"""
from __future__ import annotations

import hashlib
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
from src.features import features_5d  # noqa: E402

EXP = "expP7_phi_m_full_quran"

SEED = 42
SVM_C = 1.0
N_BOOT = 500
BAND_B = (2, 14)
BAND_A = (15, 100)
BAND_C = (101, 10**9)
MIN_VERSES = 2
ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
LOCKED_T2_BANDA = 3557.34
LOCKED_T2_TOL = 5.0


def _band_of(n_verses: int) -> str:
    if BAND_B[0] <= n_verses <= BAND_B[1]:
        return "B_short"
    if BAND_A[0] <= n_verses <= BAND_A[1]:
        return "A_paper"
    if BAND_C[0] <= n_verses <= BAND_C[1]:
        return "C_long"
    return "out_of_range"


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _hotelling_t2(X_quran: np.ndarray, X_ctrl: np.ndarray) -> dict:
    """Two-sample Hotelling T² of Quran vs control 5-D feature matrices.
    Pooled covariance with ddof=1; inverse via numpy.linalg.pinv to be
    safe in case of near-singular covariance at small bands."""
    nq, p = X_quran.shape
    nc = X_ctrl.shape[0]
    mu_q = X_quran.mean(axis=0)
    mu_c = X_ctrl.mean(axis=0)
    Sq = np.cov(X_quran, rowvar=False, ddof=1) if nq > 1 else np.zeros((p, p))
    Sc = np.cov(X_ctrl, rowvar=False, ddof=1) if nc > 1 else np.zeros((p, p))
    Spool = ((nq - 1) * Sq + (nc - 1) * Sc) / max(nq + nc - 2, 1)
    Sinv = np.linalg.pinv(Spool)
    diff = mu_q - mu_c
    T2 = float((nq * nc / (nq + nc)) * (diff @ Sinv @ diff))
    # Analytical F-tail log10 p-value via mpmath if available.
    try:
        import mpmath as mp
        mp.mp.dps = 80
        F = T2 * (nq + nc - p - 1) / (p * max(nq + nc - 2, 1))
        df1, df2 = p, nq + nc - p - 1
        if df2 > 0 and F > 0:
            sf = 1.0 - mp.betainc(
                df1 / mp.mpf(2),
                df2 / mp.mpf(2),
                0,
                df1 * F / (df1 * F + df2),
                regularized=True,
            )
            log10p = float(mp.log10(sf)) if sf > 0 else None
        else:
            log10p = None
    except Exception:
        log10p = None
    return {"T2": T2, "F_tail_log10_p": log10p, "n_q": nq, "n_c": nc, "p": p}


def _fit_svm_5d(X: np.ndarray, y: np.ndarray, seed: int = SEED) -> dict:
    """Fit a linear SVM on (X, y) and report AUC on the same (X, y).

    H5 (2026-04-26): the returned ``"auc"`` and ``"accuracy"`` keys are
    IN-SAMPLE (no train/test split, no CV). Honest naming is exposed
    via the new ``"auc_in_sample"`` and ``"accuracy_in_sample"`` keys;
    legacy keys are preserved as backward-compatible aliases.
    """
    from sklearn.svm import SVC
    from sklearn.metrics import accuracy_score, roc_auc_score
    svm = SVC(kernel="linear", C=SVM_C, class_weight="balanced",
              random_state=seed)
    svm.fit(X, y)
    dec = svm.decision_function(X)
    pred = svm.predict(X)
    auc_is = float(roc_auc_score(y, dec))
    acc_is = float(accuracy_score(y, pred))
    return {
        # H5: honest in-sample labels + legacy aliases.
        "auc_in_sample": auc_is,
        "accuracy_in_sample": acc_is,
        "auc": auc_is,
        "accuracy": acc_is,
        "w": [float(c) for c in svm.coef_[0]],
        "b": float(svm.intercept_[0]),
        "svm": svm,
    }


def _bootstrap_auc_5d(X_q: np.ndarray, X_c: np.ndarray,
                      n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Bootstrap CI on the IN-SAMPLE AUC of the 5-D linear SVM. Each
    replicate fits on the bootstrap-resampled (Xb, yb) and scores AUC
    on the SAME (Xb, yb). H5: this is a CI on training-fit AUC, not on
    out-of-sample generalisation."""
    from sklearn.svm import SVC
    from sklearn.metrics import roc_auc_score
    rng = np.random.RandomState(seed)
    aucs: list[float] = []
    nq, nc = X_q.shape[0], X_c.shape[0]
    for _ in range(n_boot):
        iq = rng.choice(nq, nq, replace=True)
        ic = rng.choice(nc, nc, replace=True)
        Xb = np.vstack([X_q[iq], X_c[ic]])
        yb = np.concatenate([np.ones(nq), np.zeros(nc)])
        svm = SVC(kernel="linear", C=SVM_C, class_weight="balanced",
                  random_state=seed)
        try:
            svm.fit(Xb, yb)
            aucs.append(float(roc_auc_score(yb, svm.decision_function(Xb))))
        except Exception:
            aucs.append(float("nan"))
    arr = np.array([a for a in aucs if np.isfinite(a)])
    if arr.size == 0:
        return {"median": None, "ci_lo": None, "ci_hi": None, "n_valid": 0}
    return {
        "median": float(np.median(arr)),
        "ci_lo": float(np.percentile(arr, 2.5)),
        "ci_hi": float(np.percentile(arr, 97.5)),
        "n_valid": int(arr.size),
    }


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] H37 -- 5-D Phi_M on ALL 114 Quran surahs vs full 4 719-unit Arabic ctrl pool")

    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    rows: list[dict] = []
    q_units = CORPORA.get("quran", [])
    for u in q_units:
        nv = len(u.verses)
        if nv < MIN_VERSES:
            continue
        rows.append({
            "corpus": "quran", "label": getattr(u, "label", ""),
            "n_verses": nv, "band": _band_of(nv),
            "feat": features_5d(list(u.verses)),
            "y": 1,
        })
    for name in ARABIC_CTRL:
        for u in CORPORA.get(name, []):
            nv = len(u.verses)
            if nv < MIN_VERSES:
                continue
            rows.append({
                "corpus": name, "label": getattr(u, "label", ""),
                "n_verses": nv, "band": _band_of(nv),
                "feat": features_5d(list(u.verses)),
                "y": 0,
            })

    n_q = sum(1 for r in rows if r["y"] == 1)
    n_c = sum(1 for r in rows if r["y"] == 0)
    print(f"[{EXP}] n_quran={n_q}  n_ctrl={n_c}")

    X_all = np.vstack([r["feat"] for r in rows])
    y_all = np.array([r["y"] for r in rows], dtype=int)
    bands = np.array([r["band"] for r in rows], dtype=object)

    # Drop any units with non-finite features (e.g. n_verses=2 produces NaN
    # H_cond at very small samples in some corpora).
    finite = np.isfinite(X_all).all(axis=1)
    if (~finite).any():
        print(f"[{EXP}]   dropping {(~finite).sum()} units with NaN/inf features")
    X_all = X_all[finite]
    y_all = y_all[finite]
    bands = bands[finite]

    n_q_fin = int((y_all == 1).sum())
    n_c_fin = int((y_all == 0).sum())

    # --- Overall ---
    print(f"\n[{EXP}] === Overall (full 114 vs full pool) ===")
    X_q = X_all[y_all == 1]
    X_c = X_all[y_all == 0]
    overall_T2 = _hotelling_t2(X_q, X_c)
    overall_fit = _fit_svm_5d(X_all, y_all)
    overall_ci = _bootstrap_auc_5d(X_q, X_c)
    print(f"[{EXP}]   T2 = {overall_T2['T2']:.2f}  "
          f"AUC = {overall_fit['auc']:.4f}  acc = {overall_fit['accuracy']:.4f}")
    if overall_T2["F_tail_log10_p"] is not None:
        print(f"[{EXP}]   F-tail log10 p = {overall_T2['F_tail_log10_p']:.2f}")

    # --- Per-band ---
    per_band: dict[str, dict] = {}
    print(f"\n[{EXP}] === Per-band ===")
    for band in ("B_short", "A_paper", "C_long"):
        mask = bands == band
        if mask.sum() == 0:
            per_band[band] = {"skipped": "no units"}
            continue
        Xb = X_all[mask]
        yb = y_all[mask]
        n_qb = int((yb == 1).sum())
        n_cb = int((yb == 0).sum())
        if n_qb < 2 or n_cb < 2:
            per_band[band] = {"skipped": f"too few (n_q={n_qb} n_c={n_cb})",
                              "n_quran": n_qb, "n_ctrl": n_cb}
            continue
        T2b = _hotelling_t2(Xb[yb == 1], Xb[yb == 0])
        fitb = _fit_svm_5d(Xb, yb)
        cib = _bootstrap_auc_5d(Xb[yb == 1], Xb[yb == 0])
        per_band[band] = {
            "n_quran": n_qb, "n_ctrl": n_cb,
            "T2": T2b["T2"], "F_tail_log10_p": T2b["F_tail_log10_p"],
            "auc": fitb["auc"], "accuracy": fitb["accuracy"],
            "w": fitb["w"], "b": fitb["b"],
            "bootstrap_ci": {
                "median": cib["median"], "ci_lo": cib["ci_lo"],
                "ci_hi": cib["ci_hi"],
            },
        }
        print(f"[{EXP}]   {band:10s} n_Q={n_qb:3d} n_C={n_cb:4d}  "
              f"T2 = {T2b['T2']:9.2f}  AUC = {fitb['auc']:.4f}  "
              f"acc = {fitb['accuracy']:.4f}")

    # --- Band-A locked sanity ---
    bA = per_band.get("A_paper", {})
    if "T2" in bA:
        within_tol = abs(bA["T2"] - LOCKED_T2_BANDA) <= LOCKED_T2_TOL
        sanity = {
            "locked_expected_T2": LOCKED_T2_BANDA,
            "tol": LOCKED_T2_TOL,
            "observed_T2": bA["T2"],
            "within_tol": bool(within_tol),
        }
        print(f"\n[{EXP}] band-A locked sanity: T2 = {bA['T2']:.2f} (expected "
              f"{LOCKED_T2_BANDA} ± {LOCKED_T2_TOL}) -> "
              f"{'OK' if within_tol else 'DRIFT'}")
    else:
        sanity = {"skipped": "band-A subset missing"}

    # --- Generalisation: train on band-A only, evaluate on B and C ---
    print(f"\n[{EXP}] === Generalisation ===")
    mask_A = bands == "A_paper"
    if mask_A.sum() > 0:
        from sklearn.svm import SVC
        from sklearn.metrics import roc_auc_score, accuracy_score
        svmA = SVC(kernel="linear", C=SVM_C, class_weight="balanced",
                   random_state=SEED)
        svmA.fit(X_all[mask_A], y_all[mask_A])
        gen: dict[str, dict] = {}
        for tb in ("B_short", "C_long"):
            mt = bands == tb
            if mt.sum() == 0:
                gen[tb] = {"skipped": "no units"}; continue
            Xt = X_all[mt]; yt = y_all[mt]
            try:
                auc = float(roc_auc_score(yt, svmA.decision_function(Xt)))
                acc = float(accuracy_score(yt, svmA.predict(Xt)))
            except ValueError:
                auc, acc = float("nan"), float("nan")
            gen[tb] = {"n_quran": int((yt == 1).sum()),
                       "n_ctrl": int((yt == 0).sum()),
                       "auc_held_out": auc, "accuracy_held_out": acc}
            print(f"[{EXP}]   bandA -> {tb:8s}  AUC = {auc:.4f}  acc = {acc:.4f}")
        generalisation = {
            "train": {"auc_on_bandA": float("nan"), "w": [float(c) for c in svmA.coef_[0]],
                      "b": float(svmA.intercept_[0])},
            "evaluated": gen,
        }
    else:
        generalisation = {"skipped": "no band-A units"}

    # --- Verdict ---
    T2_full = overall_T2["T2"]
    AUC_full = overall_fit["auc"]
    if T2_full >= 2500 and AUC_full >= 0.99:
        verdict = "PASS_full_quran_5D"
    elif T2_full >= 1000 and AUC_full >= 0.97:
        verdict = "PARTIAL_band_A_dominated"
    else:
        verdict = "FAIL_5D_band_specific"

    payload = {
        "experiment": EXP,
        "schema_version": 1,
        "prereg_document": "experiments/expP7_phi_m_full_quran/PREREG.md",
        "prereg_hash": _prereg_hash(),
        "frozen_constants": {
            "seed": SEED, "svm_C": SVM_C, "n_boot": N_BOOT,
            "band_B": list(BAND_B), "band_A": list(BAND_A),
            "band_C": [BAND_C[0]],
            "min_verses": MIN_VERSES, "arabic_ctrl": ARABIC_CTRL,
            "locked_t2_band_a": LOCKED_T2_BANDA, "locked_t2_tol": LOCKED_T2_TOL,
        },
        "n_quran_units": n_q_fin,
        "n_ctrl_units": n_c_fin,
        "n_total_dropped_nonfinite": int((~finite).sum()),
        "overall": {
            "T2": overall_T2["T2"],
            "F_tail_log10_p": overall_T2["F_tail_log10_p"],
            # H5: explicit honest labels + legacy aliases.
            "auc_in_sample": overall_fit["auc_in_sample"],
            "accuracy_in_sample": overall_fit["accuracy_in_sample"],
            "auc": overall_fit["auc"],
            "accuracy": overall_fit["accuracy"],
            "w": overall_fit["w"], "b": overall_fit["b"],
            "bootstrap_ci_in_sample_auc": {
                "median": overall_ci["median"],
                "ci_lo": overall_ci["ci_lo"],
                "ci_hi": overall_ci["ci_hi"],
            },
            "bootstrap_ci": {  # H5: legacy alias
                "median": overall_ci["median"],
                "ci_lo": overall_ci["ci_lo"],
                "ci_hi": overall_ci["ci_hi"],
            },
        },
        "per_band": per_band,
        "band_a_sanity_lock": sanity,
        "generalisation_bandA_trained": generalisation,
        "verdict": verdict,
        "runtime_seconds": round(time.time() - t0, 2),
    }

    out_path = out / f"{EXP}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, allow_nan=True)
    print(f"\n[{EXP}] wrote {out_path}")
    print(f"[{EXP}] verdict = {verdict}")
    print(f"[{EXP}] runtime = {payload['runtime_seconds']} s")

    self_check_end(pre, exp_name=EXP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
