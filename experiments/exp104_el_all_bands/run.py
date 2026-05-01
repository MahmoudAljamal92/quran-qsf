"""
exp104_el_all_bands/run.py
==========================
H36: EL-alone classifier preserves `AUC >= 0.99` across all 114 Quran
surahs (vs. the full Arabic ctrl pool) without the Band-A length gate.

Replicates `exp89b_five_feature_ablation`'s single-feature EL SVM, but
(a) drops the `15 <= n_verses <= 100` filter and (b) stratifies by length
band {Band-B 2..14, Band-A 15..100, Band-C 101+}. Reports overall AUC,
per-band AUC, Band-A-trained / Band-B+C-evaluated generalisation AUC,
and the explicit 1-D discriminant `w * EL + b = 0`.

Pre-registered in PREREG.md (frozen 2026-04-22).

Reads (integrity-checked):
    phase_06_phi_m.pkl                                    state['CORPORA']
    results/experiments/exp89b_five_feature_ablation/...json  Band-A EL AUC sanity

Writes ONLY under results/experiments/exp104_el_all_bands/
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
from src.features import el_rate  # noqa: E402

EXP = "exp104_el_all_bands"

# --- Frozen constants (mirror PREREG §7) -----------------------------------
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
EXP89B_REPRODUCTION_TOL = 0.005


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


def _load_exp89b_baseline() -> dict | None:
    path = (_ROOT / "results" / "experiments"
            / "exp89b_five_feature_ablation"
            / "exp89b_five_feature_ablation.json")
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        j = json.load(f)
    for r in j.get("single_feature", []):
        if r["features"] == ["EL"]:
            return {"auc": float(r["auc"]), "accuracy": float(r["accuracy"])}
    return None


def _fit_svm_1d(EL: np.ndarray, y: np.ndarray, seed: int = SEED):
    """Fit a 1-D linear SVM with class_weight='balanced'. Returns dict with
    auc, accuracy, w, b, and the decision-function array."""
    from sklearn.svm import SVC
    from sklearn.metrics import accuracy_score, roc_auc_score
    X = EL.reshape(-1, 1)
    svm = SVC(kernel="linear", C=SVM_C, class_weight="balanced",
              random_state=seed)
    svm.fit(X, y)
    dec = svm.decision_function(X)
    pred = svm.predict(X)
    return {
        "auc": float(roc_auc_score(y, dec)),
        "accuracy": float(accuracy_score(y, pred)),
        "w": float(svm.coef_[0][0]),
        "b": float(svm.intercept_[0]),
        "dec": dec,
        "svm": svm,
    }


def _bootstrap_auc_1d(EL_q: np.ndarray, EL_c: np.ndarray,
                      n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Bootstrap CI on 1-D SVM AUC by resampling Quran and ctrl
    independently with replacement. Returns median, 2.5/97.5 percentiles."""
    from sklearn.svm import SVC
    from sklearn.metrics import roc_auc_score
    rng = np.random.RandomState(seed)
    aucs: list[float] = []
    nq, nc = len(EL_q), len(EL_c)
    for _ in range(n_boot):
        iq = rng.choice(nq, nq, replace=True)
        ic = rng.choice(nc, nc, replace=True)
        EL_b = np.concatenate([EL_q[iq], EL_c[ic]]).reshape(-1, 1)
        y_b = np.concatenate([np.ones(nq), np.zeros(nc)])
        svm = SVC(kernel="linear", C=SVM_C, class_weight="balanced",
                  random_state=seed)
        try:
            svm.fit(EL_b, y_b)
            aucs.append(float(roc_auc_score(y_b, svm.decision_function(EL_b))))
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

    print(f"[{EXP}] H36 -- EL-alone classifier across all 114 surahs")

    # --- Load CORPORA (full, no Band-A gate) ---
    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    rows: list[dict] = []

    # Quran (all 114)
    q_units = CORPORA.get("quran", [])
    for u in q_units:
        nv = len(u.verses)
        if nv < MIN_VERSES:
            continue
        rows.append({
            "corpus": "quran",
            "label": getattr(u, "label", ""),
            "n_verses": nv,
            "band": _band_of(nv),
            "el": float(el_rate(list(u.verses))),
            "y": 1,
        })

    # Ctrl (full Arabic pool, all lengths)
    for name in ARABIC_CTRL:
        for u in CORPORA.get(name, []):
            nv = len(u.verses)
            if nv < MIN_VERSES:
                continue
            rows.append({
                "corpus": name,
                "label": getattr(u, "label", ""),
                "n_verses": nv,
                "band": _band_of(nv),
                "el": float(el_rate(list(u.verses))),
                "y": 0,
            })

    n_q = sum(1 for r in rows if r["y"] == 1)
    n_c = sum(1 for r in rows if r["y"] == 0)
    print(f"[{EXP}] n_quran={n_q}  n_ctrl={n_c}  (band split: "
          + "  ".join(
              f"{b}=Q{sum(1 for r in rows if r['y']==1 and r['band']==b)}/"
              f"C{sum(1 for r in rows if r['y']==0 and r['band']==b)}"
              for b in ("B_short", "A_paper", "C_long", "out_of_range")
          ) + ")")

    EL_all = np.array([r["el"] for r in rows], dtype=float)
    y_all = np.array([r["y"] for r in rows], dtype=int)
    EL_q = EL_all[y_all == 1]
    EL_c = EL_all[y_all == 0]

    # --- Overall fit ---
    print(f"\n[{EXP}] === Overall SVM (all 114 Q vs full Arabic ctrl) ===")
    overall = _fit_svm_1d(EL_all, y_all)
    overall_ci = _bootstrap_auc_1d(EL_q, EL_c)
    print(f"[{EXP}]   AUC = {overall['auc']:.4f}  "
          f"acc = {overall['accuracy']:.4f}")
    print(f"[{EXP}]   discriminant: w*EL + b = 0  -> "
          f"w = {overall['w']:+.4f}  b = {overall['b']:+.4f}")
    ci_lo = overall_ci["ci_lo"]
    ci_hi = overall_ci["ci_hi"]
    print(f"[{EXP}]   bootstrap CI95 AUC = "
          f"[{ci_lo:.4f}, {ci_hi:.4f}]"
          if ci_lo is not None else f"[{EXP}]   CI: n/a")

    # --- Per-band fits ---
    per_band: dict[str, dict] = {}
    print(f"\n[{EXP}] === Per-band SVMs ===")
    for band in ("B_short", "A_paper", "C_long"):
        mask = np.array([r["band"] == band for r in rows])
        if mask.sum() == 0:
            per_band[band] = {"skipped": "no units in band"}
            continue
        EL_b = EL_all[mask]
        y_b = y_all[mask]
        n_qb = int((y_b == 1).sum())
        n_cb = int((y_b == 0).sum())
        if n_qb == 0 or n_cb == 0:
            per_band[band] = {
                "skipped": f"one class empty (n_q={n_qb} n_c={n_cb})",
                "n_quran": n_qb, "n_ctrl": n_cb,
            }
            continue
        fit = _fit_svm_1d(EL_b, y_b)
        ci = _bootstrap_auc_1d(EL_b[y_b == 1], EL_b[y_b == 0])
        per_band[band] = {
            "n_quran": n_qb,
            "n_ctrl": n_cb,
            "auc": fit["auc"],
            "accuracy": fit["accuracy"],
            "w": fit["w"],
            "b": fit["b"],
            "bootstrap_ci": {
                "median": ci["median"],
                "ci_lo": ci["ci_lo"],
                "ci_hi": ci["ci_hi"],
            },
            "median_el_quran": float(np.median(EL_b[y_b == 1])),
            "median_el_ctrl": float(np.median(EL_b[y_b == 0])),
        }
        print(f"[{EXP}]   {band:10s} n_Q={n_qb:3d}  n_C={n_cb:4d}  "
              f"AUC = {fit['auc']:.4f}  acc = {fit['accuracy']:.4f}  "
              f"med(EL_Q)={per_band[band]['median_el_quran']:.3f}  "
              f"med(EL_C)={per_band[band]['median_el_ctrl']:.3f}")

    # --- Band-A-trained / Band-B+C-evaluated generalisation ---
    print(f"\n[{EXP}] === Generalisation: train on Band-A, evaluate on B and C ===")
    mask_A = np.array([r["band"] == "A_paper" for r in rows])
    mask_BC = np.array([r["band"] in ("B_short", "C_long") for r in rows])
    bandA_trained = None
    generalisation: dict[str, dict] = {}
    if mask_A.sum() > 0 and mask_BC.sum() > 0:
        from sklearn.metrics import roc_auc_score
        bandA_trained = _fit_svm_1d(EL_all[mask_A], y_all[mask_A])
        for test_band in ("B_short", "C_long"):
            mask_T = np.array([r["band"] == test_band for r in rows])
            if mask_T.sum() == 0:
                generalisation[test_band] = {"skipped": "no units"}
                continue
            EL_T = EL_all[mask_T].reshape(-1, 1)
            y_T = y_all[mask_T]
            n_qT = int((y_T == 1).sum())
            n_cT = int((y_T == 0).sum())
            if n_qT == 0 or n_cT == 0:
                generalisation[test_band] = {
                    "skipped": f"one class empty (n_q={n_qT} n_c={n_cT})",
                    "n_quran": n_qT, "n_ctrl": n_cT,
                }
                continue
            dec = bandA_trained["svm"].decision_function(EL_T)
            auc_T = float(roc_auc_score(y_T, dec))
            generalisation[test_band] = {
                "n_quran": n_qT,
                "n_ctrl": n_cT,
                "auc_held_out": auc_T,
            }
            print(f"[{EXP}]   Band-A -> {test_band:10s}  "
                  f"n_Q={n_qT:3d}  n_C={n_cT:4d}  AUC_held_out = {auc_T:.4f}")

    # --- exp89b sanity reproduction (Band-A only) ---
    exp89b = _load_exp89b_baseline()
    sanity: dict = {"expected": None, "observed": None,
                    "within_tol": None, "tol": EXP89B_REPRODUCTION_TOL}
    if exp89b is not None and "A_paper" in per_band and "auc" in per_band["A_paper"]:
        sanity["expected"] = exp89b["auc"]
        sanity["observed"] = per_band["A_paper"]["auc"]
        sanity["within_tol"] = (
            abs(sanity["observed"] - sanity["expected"])
            <= EXP89B_REPRODUCTION_TOL
        )
        print(f"\n[{EXP}] === exp89b reproduction sanity (Band-A only) ===")
        print(f"[{EXP}]   expected EL-AUC: {sanity['expected']:.4f}")
        print(f"[{EXP}]   observed EL-AUC: {sanity['observed']:.4f}")
        print(f"[{EXP}]   within tol {EXP89B_REPRODUCTION_TOL}: "
              f"{sanity['within_tol']}")

    # --- Verdict ---
    def _auc_of(band: str) -> float | None:
        rec = per_band.get(band, {})
        return rec.get("auc") if "auc" in rec else None

    a_b = _auc_of("B_short")
    a_a = _auc_of("A_paper")
    a_c = _auc_of("C_long")
    all_auc = [overall["auc"]] + [x for x in (a_b, a_a, a_c) if x is not None]
    min_band_auc = min([x for x in (a_b, a_a, a_c) if x is not None],
                       default=float("inf"))

    if sanity["within_tol"] is False:
        verdict = "FAIL_exp89b_reproduction_broken"
    elif overall["auc"] < 0.95:
        verdict = "FAIL_not_universal"
    elif overall["auc"] >= 0.99 and min_band_auc >= 0.99:
        verdict = "PASS_universal_uniform"
    elif overall["auc"] >= 0.99 and min_band_auc >= 0.95:
        verdict = "PASS_universal_strong"
    else:
        verdict = "PARTIAL_length_dependent"

    print(f"\n{'=' * 68}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    print(f"  AUC_overall  = {overall['auc']:.4f}  "
          f"(CI95 [{overall_ci['ci_lo']}, {overall_ci['ci_hi']}])")
    for band in ("B_short", "A_paper", "C_long"):
        a = _auc_of(band)
        if a is None:
            continue
        print(f"  AUC_{band:10s} = {a:.4f}")
    for test_band in ("B_short", "C_long"):
        g = generalisation.get(test_band, {})
        if "auc_held_out" in g:
            print(f"  AUC_generalisation[A->{test_band:10s}] "
                  f"= {g['auc_held_out']:.4f}")
    print(f"{'=' * 68}")

    elapsed = time.time() - t0

    # Purge non-JSON-serialisable entries from the per_band fits
    for b, rec in per_band.items():
        rec.pop("dec", None)
        rec.pop("svm", None)
    bandA_trained_clean = None
    if bandA_trained is not None:
        bandA_trained_clean = {
            "auc_on_bandA_train": bandA_trained["auc"],
            "accuracy_on_bandA_train": bandA_trained["accuracy"],
            "w": bandA_trained["w"],
            "b": bandA_trained["b"],
        }

    report = {
        "experiment": EXP,
        "hypothesis": (
            "H36 -- EL-alone classifier preserves AUC >= 0.99 across all "
            "114 Quran surahs vs. the full Arabic ctrl pool (no Band-A gate)."
        ),
        "schema_version": 1,
        "prereg_document": "experiments/exp104_el_all_bands/PREREG.md",
        "prereg_hash": _prereg_hash(),
        "frozen_constants": {
            "seed": SEED,
            "svm_C": SVM_C,
            "n_boot": N_BOOT,
            "band_B": list(BAND_B),
            "band_A": list(BAND_A),
            "band_C": [BAND_C[0]],
            "min_verses": MIN_VERSES,
            "arabic_ctrl": ARABIC_CTRL,
            "exp89b_reproduction_tol": EXP89B_REPRODUCTION_TOL,
        },
        "n_quran_units": n_q,
        "n_ctrl_units": n_c,
        "overall": {
            "auc": overall["auc"],
            "accuracy": overall["accuracy"],
            "w": overall["w"],
            "b": overall["b"],
            "bootstrap_ci": {
                "median": overall_ci["median"],
                "ci_lo": overall_ci["ci_lo"],
                "ci_hi": overall_ci["ci_hi"],
            },
            "median_el_quran": float(np.median(EL_q)),
            "median_el_ctrl": float(np.median(EL_c)),
        },
        "per_band": per_band,
        "generalisation_bandA_trained": {
            "train": bandA_trained_clean,
            "evaluated": generalisation,
        },
        "exp89b_sanity": sanity,
        "units": rows,
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
