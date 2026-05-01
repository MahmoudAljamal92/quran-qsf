"""
exp98_vlcv_floor/run.py
========================
VL_CV floor invariant (H32).

Tests whether every Band-A Quran surah has VL_CV >= 0.1962 (the
un-derived structural constant flagged in the v7.7 CascadeProjects
addendum), and whether that floor discriminates against natural
Arabic controls.

Pre-registered verdict ladder:
    FAIL_sanity_phase06_drift   |VL_CV_recomp - VL_CV_phase06| > 0.01
    FAIL_floor_violated         any Q surah VL_CV < 0.1962
    FAIL_floor_unstable         bootstrap 95% CI width > 0.03
    FAIL_floor_not_specific     ctrl violation rate < 1%
    PARTIAL_floor_weak_specificity    1% <= ctrl violation < 5%
    PASS_floor_exact            PASS AND |min - 0.1962| <= 0.001
    PASS_floor_revised          PASS AND |min - 0.1962| > 0.001

Reads (integrity-checked):
    phase_06_phi_m.pkl -> state['CORPORA'], state['X_QURAN'], state['FEAT_COLS']

Writes ONLY under results/experiments/exp98_vlcv_floor/
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

EXP = "exp98_vlcv_floor"

# --- Frozen constants (mirror PREREG §7) -----------------------------------
SEED = 42
BAND_A_LO, BAND_A_HI = 15, 100
FLOOR_NOMINAL = 0.1962
FLOOR_EXACT_TOL = 0.001
FLOOR_CI_WIDTH_MAX = 0.03
CTRL_VIOLATION_MIN = 0.01
CTRL_VIOLATION_PARTIAL = 0.05
BOOTSTRAP_N = 10000

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ALPH_IDX = {c: i for i, c in enumerate(ARABIC_CONS_28)}
DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)
_FOLD = {
    "ء": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "ا", "ئ": "ا",
    "ة": "ه",
    "ى": "ي",
}


def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)


def _word_count(verse: str) -> int:
    """Match src.features.vl_cv: words = whitespace-tokenised verse,
    diacritics NOT stripped (per features_5d line 89: len(v.split())
    operates on the verse string as-is). We follow the exact call
    signature of features_5d.vl_cv.

    NOTE: src.features.vl_cv does NOT diacritic-strip. We match that.
    """
    return len(verse.split())


def _verse_len_arr(verses) -> np.ndarray:
    return np.asarray([_word_count(v) for v in verses], dtype=float)


def _vl_cv(verses) -> float:
    """Byte-equal to src.features.vl_cv (features_5d line 88-92)."""
    lens = _verse_len_arr(verses)
    if lens.size < 2 or lens.mean() == 0.0:
        return 0.0
    return float(lens.std(ddof=1) / lens.mean())


def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


def _corpus_vlcv(units) -> tuple[np.ndarray, list[str]]:
    vals, labels = [], []
    for u in units:
        vc = _vl_cv(u.verses)
        if np.isfinite(vc):
            vals.append(vc)
            labels.append(getattr(u, "label", ""))
    return np.asarray(vals, dtype=float), labels


def _summary(arr: np.ndarray) -> dict:
    if arr.size == 0:
        return {"n": 0}
    return {
        "n": int(arr.size),
        "min": float(arr.min()),
        "p5": float(np.percentile(arr, 5)),
        "median": float(np.median(arr)),
        "mean": float(arr.mean()),
        "p95": float(np.percentile(arr, 95)),
        "max": float(arr.max()),
        "std": float(arr.std(ddof=1)) if arr.size > 1 else 0.0,
    }


def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    if a.size < 2 or b.size < 2:
        return float("nan")
    va = float(a.var(ddof=1))
    vb = float(b.var(ddof=1))
    pooled = ((a.size - 1) * va + (b.size - 1) * vb) / (a.size + b.size - 2)
    if pooled <= 0:
        return float("nan")
    return float((a.mean() - b.mean()) / np.sqrt(pooled))


def _youden_threshold(q: np.ndarray, c: np.ndarray) -> tuple[float, float]:
    """Find VL_CV threshold maximising Youden's J = TPR - FPR
    (Q = positive, ctrl = negative). Higher VL_CV => Q side."""
    if q.size == 0 or c.size == 0:
        return float("nan"), float("nan")
    candidates = np.sort(np.unique(np.concatenate([q, c])))
    best_j, best_t = -1.0, float("nan")
    for t in candidates:
        tpr = float((q >= t).mean())
        fpr = float((c >= t).mean())
        j = tpr - fpr
        if j > best_j:
            best_j, best_t = j, float(t)
    return best_t, best_j


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] H32 — VL_CV floor invariant")
    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    CORPORA = state["CORPORA"]
    X_Q = np.asarray(state["X_QURAN"], dtype=float)
    FEAT_COLS = list(state["FEAT_COLS"])
    vl_cv_idx = FEAT_COLS.index("VL_CV")

    # --- Quran recomputation + phase_06 cross-check ---
    q_units = _band_a(CORPORA.get("quran", []))
    q_vlcv, q_labels = _corpus_vlcv(q_units)
    phase06_vlcv = X_Q[:, vl_cv_idx]

    # Align by position if possible; both should be 68-dim in surah order
    if q_vlcv.shape[0] == phase06_vlcv.shape[0]:
        max_diff = float(np.max(np.abs(q_vlcv - phase06_vlcv)))
    else:
        max_diff = float("inf")
    sanity_phase06_ok = max_diff <= 0.01
    print(f"[{EXP}] Quran Band-A n={q_vlcv.size}  "
          f"phase06 VL_CV max abs diff = {max_diff:.6f}  "
          f"(sanity {'OK' if sanity_phase06_ok else 'FAIL'})")

    q_summary = _summary(q_vlcv)
    q_min = q_summary["min"]
    floor_violated = bool(q_min < FLOOR_NOMINAL)
    n_below = int((q_vlcv < FLOOR_NOMINAL).sum())
    print(f"[{EXP}] Quran VL_CV: min={q_min:.6f}  median={q_summary['median']:.4f}  "
          f"max={q_summary['max']:.4f}")
    print(f"[{EXP}] # Q surahs below nominal floor 0.1962: {n_below} / {q_vlcv.size}")

    # --- Bootstrap ---
    rng = np.random.RandomState(SEED)
    boot_mins = np.zeros(BOOTSTRAP_N, dtype=float)
    for i in range(BOOTSTRAP_N):
        idx = rng.choice(q_vlcv.size, q_vlcv.size, replace=True)
        boot_mins[i] = float(q_vlcv[idx].min())
    ci_lo = float(np.percentile(boot_mins, 2.5))
    ci_hi = float(np.percentile(boot_mins, 97.5))
    ci_width = ci_hi - ci_lo
    print(f"[{EXP}] Bootstrap min 95% CI: [{ci_lo:.6f}, {ci_hi:.6f}]  "
          f"width={ci_width:.6f}")

    # --- Ctrl corpora ---
    ctrl_pool: list[float] = []
    ctrl_corpora_summaries: dict[str, dict] = {}
    ctrl_violation_counts: dict[str, int] = {}
    ctrl_violation_ns: dict[str, int] = {}
    for cname in ARABIC_CTRL:
        c_units = _band_a(CORPORA.get(cname, []))
        c_arr, _ = _corpus_vlcv(c_units)
        ctrl_corpora_summaries[cname] = _summary(c_arr)
        viol = int((c_arr < FLOOR_NOMINAL).sum())
        ctrl_violation_counts[cname] = viol
        ctrl_violation_ns[cname] = int(c_arr.size)
        ctrl_pool.extend(c_arr.tolist())
        print(f"[{EXP}] {cname:18s}  n={c_arr.size:4d}  min={c_arr.min() if c_arr.size else float('nan'):.4f}  "
              f"<{FLOOR_NOMINAL}: {viol} ({100.0 * viol / max(c_arr.size, 1):.1f}%)")

    ctrl_pool_arr = np.asarray(ctrl_pool, dtype=float)
    ctrl_summary = _summary(ctrl_pool_arr)
    ctrl_total_viol = int((ctrl_pool_arr < FLOOR_NOMINAL).sum())
    ctrl_violation_rate = float(ctrl_total_viol / max(ctrl_pool_arr.size, 1))
    print(f"[{EXP}] Ctrl pool  n={ctrl_pool_arr.size}  "
          f"{ctrl_total_viol} ({100.0 * ctrl_violation_rate:.2f}%) below {FLOOR_NOMINAL}")

    # --- Cohen d + Youden ---
    d_q_vs_ctrl = _cohens_d(q_vlcv, ctrl_pool_arr)
    youden_t, youden_j = _youden_threshold(q_vlcv, ctrl_pool_arr)
    # Floor-based specificity
    floor_tpr = float((q_vlcv >= FLOOR_NOMINAL).mean())
    floor_fpr = float((ctrl_pool_arr >= FLOOR_NOMINAL).mean())
    print(f"[{EXP}] Cohen d(Q vs ctrl pool) = {d_q_vs_ctrl:.4f}")
    print(f"[{EXP}] At floor 0.1962 : Q-pass={100.0*floor_tpr:.1f}%  "
          f"ctrl-pass={100.0*floor_fpr:.1f}%")
    print(f"[{EXP}] Youden-J best threshold={youden_t:.4f}  J={youden_j:.4f}")

    # --- Verdict ---
    floor_unstable = bool(ci_width > FLOOR_CI_WIDTH_MAX)
    floor_not_specific = bool(ctrl_violation_rate < CTRL_VIOLATION_MIN)
    floor_partial_spec = bool(
        CTRL_VIOLATION_MIN <= ctrl_violation_rate < CTRL_VIOLATION_PARTIAL
    )
    floor_exact = bool(abs(q_min - FLOOR_NOMINAL) <= FLOOR_EXACT_TOL)

    gates = {
        "sanity_phase06_ok": bool(sanity_phase06_ok),
        "floor_not_violated": bool(not floor_violated),
        "floor_stable": bool(not floor_unstable),
        "floor_specific": bool(not floor_not_specific),
        "floor_exact_match_nominal": bool(floor_exact),
    }

    if not sanity_phase06_ok:
        verdict = "FAIL_sanity_phase06_drift"
    elif floor_violated:
        verdict = "FAIL_floor_violated"
    elif floor_unstable:
        verdict = "FAIL_floor_unstable"
    elif floor_not_specific:
        verdict = "FAIL_floor_not_specific"
    elif floor_partial_spec:
        verdict = "PARTIAL_floor_weak_specificity"
    elif floor_exact:
        verdict = "PASS_floor_exact"
    else:
        verdict = "PASS_floor_revised"

    elapsed = time.time() - t0
    print(f"\n{'=' * 64}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    for k, v in gates.items():
        mark = "OK" if v is True else "FAIL"
        print(f"  {k:30s} {mark} ({v})")
    print(f"{'=' * 64}")

    report = {
        "experiment": EXP,
        "hypothesis": "H32 — VL_CV floor invariant (min_q VL_CV >= 0.1962)",
        "schema_version": 1,
        "prereg_document": "experiments/exp98_vlcv_floor/PREREG.md",
        "frozen_constants": {
            "seed": SEED, "band_a": [BAND_A_LO, BAND_A_HI],
            "floor_nominal": FLOOR_NOMINAL,
            "floor_exact_tol": FLOOR_EXACT_TOL,
            "floor_ci_width_max": FLOOR_CI_WIDTH_MAX,
            "ctrl_violation_min": CTRL_VIOLATION_MIN,
            "ctrl_violation_partial": CTRL_VIOLATION_PARTIAL,
            "bootstrap_n": BOOTSTRAP_N,
        },
        "phase06_sanity": {
            "n_phase06_rows": int(phase06_vlcv.shape[0]),
            "n_recomputed": int(q_vlcv.size),
            "max_abs_diff": max_diff,
            "within_tolerance": sanity_phase06_ok,
        },
        "quran": {
            **q_summary,
            "n_below_floor": n_below,
            "bootstrap_min_ci_95": {
                "lo": ci_lo, "hi": ci_hi, "width": ci_width,
                "n_boot": BOOTSTRAP_N,
            },
            "min_surah_label": q_labels[int(np.argmin(q_vlcv))] if q_labels else None,
            "all_vlcv_sorted": sorted([round(float(v), 6) for v in q_vlcv.tolist()]),
        },
        "ctrl_pool": {
            **ctrl_summary,
            "n_below_floor": ctrl_total_viol,
            "violation_rate": ctrl_violation_rate,
        },
        "ctrl_per_corpus": {
            cname: {
                **ctrl_corpora_summaries[cname],
                "n_below_floor": ctrl_violation_counts[cname],
                "violation_rate": (ctrl_violation_counts[cname]
                                    / max(ctrl_violation_ns[cname], 1)),
            }
            for cname in ARABIC_CTRL
        },
        "discrimination": {
            "cohen_d_q_vs_ctrl_pool": d_q_vs_ctrl,
            "youden_threshold": youden_t,
            "youden_j": youden_j,
            "floor_nominal_tpr_q": floor_tpr,
            "floor_nominal_tpr_ctrl": floor_fpr,
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
