"""
exp91_meccan_medinan_stability/run.py
======================================
Pre-registered diachronic-stability test for LC3-70-U: does the locked
linear discriminant `L = 0.5329*T + 4.1790*EL - 1.5221` classify Meccan
and Medinan surahs at comparable rates?

See PREREG.md for the frozen verdict ladder.

Reads (integrity-checked):
    phase_06_phi_m.pkl -> X_QURAN, FEAT_COLS, FEATS['quran'] (ordering)

Writes ONLY under results/experiments/exp91_meccan_medinan_stability/
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

EXP = "exp91_meccan_medinan_stability"

# Pre-registered constants (from PREREG.md; DO NOT MODIFY)
BAND_LO, BAND_HI = 15, 100
W_T = 0.5329
W_EL = 4.1790
B_CONST = -1.5221
CROSSING_GAP_MAX = 0.25
COHEN_D_MAX = 1.0

# Canonical Meccan/Medinan split (src/extended_tests.py:47-49)
MEDINAN = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 57, 58, 59,
           60, 61, 62, 63, 64, 65, 66, 76, 98, 99, 110}
# Everything else in [1, 114] is Meccan.


def cohen_d(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    va = float(np.var(a, ddof=1))
    vb = float(np.var(b, ddof=1))
    pooled = np.sqrt(((len(a) - 1) * va + (len(b) - 1) * vb) / (len(a) + len(b) - 2))
    if pooled == 0:
        return float("nan")
    return float((a.mean() - b.mean()) / pooled)


def summarize(arr: np.ndarray, label: str) -> dict:
    if arr.size == 0:
        return {"label": label, "n": 0}
    return {
        "label": label,
        "n": int(arr.size),
        "mean": round(float(arr.mean()), 6),
        "std": round(float(arr.std(ddof=1)) if arr.size >= 2 else 0.0, 6),
        "median": round(float(np.median(arr)), 6),
        "min": round(float(arr.min()), 6),
        "max": round(float(arr.max()), 6),
        "frac_over_zero": round(float((arr > 0).mean()), 6),
        "n_over_zero": int((arr > 0).sum()),
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

    # ---------------- Load ----------------
    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    X_Q = np.asarray(state["X_QURAN"], dtype=float)
    feat_cols = list(state["FEAT_COLS"])
    feats = state["FEATS"]
    band_lo = int(state.get("BAND_A_LO", BAND_LO))
    band_hi = int(state.get("BAND_A_HI", BAND_HI))

    t_idx = feat_cols.index("T")
    el_idx = feat_cols.index("EL")

    # Recover surah indices for the 68 Band-A rows in X_QURAN.
    # The phase-06 build iterates FEATS['quran'] in canonical order (surah 1..114);
    # Band-A filter 15 <= n_verses <= 100 is applied row-wise, preserving order.
    quran_feats = feats.get("quran", [])
    if not quran_feats:
        raise RuntimeError(f"[{EXP}] FEATS['quran'] is empty/missing; cannot recover surah indices.")
    print(f"[{EXP}] FEATS['quran'] has {len(quran_feats)} records (expected 114).")

    band_a_indices = []  # 1-based surah index for each Band-A row
    for i, rec in enumerate(quran_feats, start=1):
        n_v = int(rec.get("n_verses", -1))
        if band_lo <= n_v <= band_hi:
            band_a_indices.append(i)

    print(f"[{EXP}] Band-A surah count = {len(band_a_indices)}  (X_QURAN has {X_Q.shape[0]} rows)")

    # Pre-reg sanity: index count must match X_QURAN
    if len(band_a_indices) != X_Q.shape[0]:
        raise RuntimeError(
            f"[{EXP}] FAIL_sanity_count_drift: index count {len(band_a_indices)} "
            f"!= X_QURAN row count {X_Q.shape[0]}. Surah-to-row alignment broken."
        )

    # ---------------- Compute L per surah ----------------
    T_vals = X_Q[:, t_idx]
    EL_vals = X_Q[:, el_idx]
    L_vals = W_T * T_vals + W_EL * EL_vals + B_CONST

    is_medinan = np.array([i in MEDINAN for i in band_a_indices])
    medinan_mask = is_medinan
    meccan_mask = ~is_medinan

    n_med = int(medinan_mask.sum())
    n_mec = int(meccan_mask.sum())
    print(f"[{EXP}] Band-A split: Meccan={n_mec}, Medinan={n_med}, total={n_mec + n_med}")

    # ---------------- Per-group summaries ----------------
    L_med = L_vals[medinan_mask]
    L_mec = L_vals[meccan_mask]
    T_med = T_vals[medinan_mask]
    T_mec = T_vals[meccan_mask]
    EL_med = EL_vals[medinan_mask]
    EL_mec = EL_vals[meccan_mask]

    summary_meccan = summarize(L_mec, "meccan")
    summary_medinan = summarize(L_med, "medinan")

    summary_meccan.update({
        "mean_T": round(float(T_mec.mean()), 6) if T_mec.size else None,
        "mean_EL": round(float(EL_mec.mean()), 6) if EL_mec.size else None,
    })
    summary_medinan.update({
        "mean_T": round(float(T_med.mean()), 6) if T_med.size else None,
        "mean_EL": round(float(EL_med.mean()), 6) if EL_med.size else None,
    })

    # Per-surah table (for audit)
    per_surah = []
    for idx, (s_idx, t_v, el_v, L_v) in enumerate(
        zip(band_a_indices, T_vals, EL_vals, L_vals)
    ):
        per_surah.append({
            "surah": int(s_idx),
            "label": "medinan" if s_idx in MEDINAN else "meccan",
            "T": round(float(t_v), 6),
            "EL": round(float(el_v), 6),
            "L": round(float(L_v), 6),
            "Q_side": bool(L_v > 0),
        })

    # ---------------- Effect-size & verdict ----------------
    d_mec_vs_med = cohen_d(L_mec, L_med)
    frac_mec_over = float((L_mec > 0).mean()) if L_mec.size else 0.0
    frac_med_over = float((L_med > 0).mean()) if L_med.size else 0.0
    crossing_gap = abs(frac_mec_over - frac_med_over)

    mean_L_mec = float(L_mec.mean()) if L_mec.size else 0.0
    mean_L_med = float(L_med.mean()) if L_med.size else 0.0
    opposite_signs = (mean_L_mec * mean_L_med) < 0

    # Pre-registered ladder
    if (n_mec + n_med) != X_Q.shape[0]:
        verdict = "FAIL_sanity_count_drift"
    elif opposite_signs:
        verdict = "FAIL_opposite_signs"
    elif crossing_gap > CROSSING_GAP_MAX:
        verdict = "FAIL_crossing_gap"
    elif np.isfinite(d_mec_vs_med) and abs(d_mec_vs_med) > COHEN_D_MAX:
        verdict = "FAIL_large_cohen_d"
    elif (
        (not opposite_signs)
        and (crossing_gap <= CROSSING_GAP_MAX)
        and (np.isfinite(d_mec_vs_med) and abs(d_mec_vs_med) <= COHEN_D_MAX)
    ):
        verdict = "PASS_stable"
    else:
        verdict = "MIXED"

    elapsed = time.time() - t0

    # ---------------- Print ----------------
    print(f"\n{'=' * 72}")
    print(f"[{EXP}] DIACHRONIC STABILITY — LC3-70-U on Meccan vs Medinan")
    print(f"{'=' * 72}")
    print(f"  Meccan  (n={n_mec:3d})  mean T={T_mec.mean():+.4f}  mean EL={EL_mec.mean():.4f}  "
          f"mean L={mean_L_mec:+.4f}  frac(L>0)={frac_mec_over:.3f}  ({int((L_mec>0).sum())}/{n_mec})")
    print(f"  Medinan (n={n_med:3d})  mean T={T_med.mean():+.4f}  mean EL={EL_med.mean():.4f}  "
          f"mean L={mean_L_med:+.4f}  frac(L>0)={frac_med_over:.3f}  ({int((L_med>0).sum())}/{n_med})")
    print(f"  Cohen d (Meccan vs Medinan on L) = {d_mec_vs_med:+.4f}  (threshold |d| <= {COHEN_D_MAX})")
    print(f"  |crossing-rate gap|              = {crossing_gap:.4f}  (threshold <= {CROSSING_GAP_MAX})")
    print(f"  opposite signs?                  = {opposite_signs}")
    print(f"{'=' * 72}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    print(f"{'=' * 72}")

    # ---------------- Report ----------------
    report = {
        "experiment": EXP,
        "hypothesis": "H-MM-STABILITY — LC3-70-U diachronic stability across 23-year composition arc",
        "schema_version": 1,
        "prereg_document": "experiments/exp91_meccan_medinan_stability/PREREG.md",
        "prereg_constants": {
            "BAND_LO": BAND_LO,
            "BAND_HI": BAND_HI,
            "w_T": W_T,
            "w_EL": W_EL,
            "b": B_CONST,
            "CROSSING_GAP_MAX": CROSSING_GAP_MAX,
            "COHEN_D_MAX": COHEN_D_MAX,
        },
        "medinan_set": sorted(MEDINAN),
        "n_medinan_in_bandA": n_med,
        "n_meccan_in_bandA": n_mec,
        "n_total_bandA": n_mec + n_med,
        "meccan_summary": summary_meccan,
        "medinan_summary": summary_medinan,
        "comparison": {
            "cohen_d_meccan_vs_medinan_on_L": round(d_mec_vs_med, 6) if np.isfinite(d_mec_vs_med) else None,
            "crossing_rate_gap": round(crossing_gap, 6),
            "opposite_signs": bool(opposite_signs),
            "mean_L_meccan": round(mean_L_mec, 6),
            "mean_L_medinan": round(mean_L_med, 6),
        },
        "per_surah": per_surah,
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
