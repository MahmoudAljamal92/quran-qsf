"""
expA5_segmentation_sensitivity/run.py
=====================================
Opportunity A5 (OPPORTUNITY_TABLE_DETAIL.md):
  Test whether the 5-D Phi_M signal survives when the unit of analysis is
  re-defined from "size-variable canonical surah" to "fixed-W-verse window".

  External reviewer's question (QSF_CRITICAL_REVIEW.md:186-194):
      "Is the signal in the text or in the verse boundaries?"

  This experiment isolates the *unit-size* component. The 5-D features
  (EL, VL_CV, CN, H_cond, T) are reach-aggregations over a verse list, so
  they require multi-verse units. We hold verse boundaries fixed but vary
  the WINDOW SIZE W in {20, 40, 80} verses, computing features per
  W-window for the Quran AND each control corpus, then re-evaluating the
  Quran-vs-control Hotelling T^2 and Cohen-d_pooled at each W.

  Outcomes:
    - T^2_W stays in the thousands at all W -> signal is unit-size-robust
      (the reviewer's worry is empirically discounted).
    - T^2_W collapses at large W (Quran centroid drifts toward control
      centroid as we average over more verses) -> the signal IS partly
      tied to surah-scale aggregation; report this honestly.
    - T^2_W amplifies at large W (variance shrinks faster than mean
      separation) -> the signal is robust AND scale-cooperative.

NOT covered (deferred):
  - Sentence boundaries via CamelTools NLP parsing.
  - Topic-paragraph boundaries via LDA / topic-shift detection.
  Both require heavy external dependencies and are bigger projects.

Reads (read-only):
  - results/checkpoints/phase_06_phi_m.pkl  (CORPORA, ARABIC_CTRL_POOL)
Writes:
  - results/experiments/expA5_segmentation_sensitivity/expA5_segmentation_sensitivity.json
"""

from __future__ import annotations

import json
import math
import sys
import time
from dataclasses import dataclass
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
from src.features import features_5d, ARABIC_CONN  # noqa: E402

EXP = "expA5_segmentation_sensitivity"
WINDOW_SIZES = [20, 40, 80]
RIDGE_LAMBDA = 1e-6


@dataclass
class _Window:
    corpus: str
    label: str
    verses: list[str]


def _make_windows(units, W: int, corpus: str) -> list[_Window]:
    """Concatenate all verses across all units of one corpus, then chunk
    into non-overlapping W-verse windows."""
    all_verses: list[str] = []
    for u in units:
        all_verses.extend(getattr(u, "verses", []) or [])
    out: list[_Window] = []
    n = len(all_verses)
    n_full = n // W
    for i in range(n_full):
        out.append(_Window(
            corpus=corpus,
            label=f"{corpus}:W{W}:{i:04d}",
            verses=all_verses[i * W : (i + 1) * W],
        ))
    return out


def _features_matrix(wins: list[_Window]) -> np.ndarray:
    """Compute 5-D features per window. Skips windows whose features are
    not finite (all 5 values must be finite)."""
    rows = []
    for w in wins:
        try:
            v = features_5d(w.verses, ARABIC_CONN)
        except Exception:
            continue
        if not np.all(np.isfinite(v)):
            continue
        rows.append(v)
    return np.array(rows, dtype=float)


def _hotelling_t2(XA: np.ndarray, XB: np.ndarray, ridge: float = RIDGE_LAMBDA):
    nA, p = XA.shape
    nB = XB.shape[0]
    mA, mB = XA.mean(0), XB.mean(0)
    SA = np.cov(XA.T, ddof=1)
    SB = np.cov(XB.T, ddof=1)
    Sp = ((nA - 1) * SA + (nB - 1) * SB) / max(1, (nA + nB - 2))
    Spi = np.linalg.inv(Sp + ridge * np.eye(p))
    diff = mA - mB
    T2 = float((nA * nB / (nA + nB)) * diff @ Spi @ diff)
    df1, df2 = p, nA + nB - p - 1
    F = ((nA + nB - p - 1) / ((nA + nB - 2) * p)) * T2 if df2 > 0 else float("nan")
    p_F = float(stats.f.sf(F, df1, df2)) if df2 > 0 else float("nan")
    d2 = float(diff @ Spi @ diff)
    cohen_d_pooled = math.sqrt(max(d2, 0.0))
    return {
        "T2": T2,
        "F": F,
        "df1": int(df1),
        "df2": int(df2),
        "p_F_tail": p_F,
        "cohen_d_pooled": cohen_d_pooled,
        "n_target": int(nA),
        "n_control": int(nB),
    }


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    corpora = state["CORPORA"]
    ctrl_pool = list(state["ARABIC_CTRL_POOL"])

    print(f"[{EXP}] ctrl_pool: {ctrl_pool}")

    results_per_W = []
    for W in WINDOW_SIZES:
        print(f"[{EXP}] -- W = {W} verses --")
        # Quran windows
        q_wins = _make_windows(corpora.get("quran", []), W, "quran")
        XQ = _features_matrix(q_wins)
        print(f"[{EXP}]   Quran : {len(q_wins)} windows; features OK = {XQ.shape}")
        # Control pool windows (concatenated)
        c_wins: list[_Window] = []
        for name in ctrl_pool:
            c_wins.extend(_make_windows(corpora.get(name, []), W, name))
        XC = _features_matrix(c_wins)
        print(f"[{EXP}]   Ctrl  : {len(c_wins)} windows; features OK = {XC.shape}")

        if XQ.shape[0] < 5 or XC.shape[0] < 5:
            print(f"[{EXP}]   too few rows; skipping W={W}")
            continue

        ht = _hotelling_t2(XQ, XC)
        # Per-feature Cohen d (target vs control)
        per_feat = {}
        feat_names = ["EL", "VL_CV", "CN", "H_cond", "T"]
        for j, fn in enumerate(feat_names):
            a = XQ[:, j]; b = XC[:, j]
            s2 = ((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / max(
                1, len(a) + len(b) - 2
            )
            s = math.sqrt(s2) if s2 > 0 else float("nan")
            d = (a.mean() - b.mean()) / s if s and math.isfinite(s) and s > 1e-12 else float("nan")
            per_feat[fn] = {
                "quran_mean": float(a.mean()),
                "ctrl_mean":  float(b.mean()),
                "quran_sd":   float(a.std(ddof=1)),
                "ctrl_sd":    float(b.std(ddof=1)),
                "cohen_d":    float(d) if math.isfinite(d) else None,
            }

        results_per_W.append({
            "W": int(W),
            "n_quran_windows": int(XQ.shape[0]),
            "n_ctrl_windows":  int(XC.shape[0]),
            "hotelling": ht,
            "per_feature": per_feat,
        })
        print(f"[{EXP}]   T^2 = {ht['T2']:.3f}   F = {ht['F']:.3f}   "
              f"d_pooled = {ht['cohen_d_pooled']:.3f}   p_F = {ht['p_F_tail']:.3e}")

    # ---- Comparison with locked Phi_M baseline (verse-segmented = surah units) ----
    locked_phi_m = {
        "T2_baseline_per_surah": 3557.339454504635,
        "n_quran_baseline":      68,   # Band-A Quran
        "n_ctrl_baseline":       2509, # Band-A Arabic ctrl
        "note": (
            "Locked Phi_M Hotelling T^2 = 3557.34 was computed on Band-A "
            "surah units (15-100 verses), not on fixed-W windows. Direct "
            "T^2 comparison is not apples-to-apples because the unit count "
            "and unit-size distributions differ; we report the per-W "
            "T^2 absolute value AND its per-window normalisation "
            "T^2 / (n_q + n_c) to allow rough cross-W comparability."
        ),
    }

    for r in results_per_W:
        ht = r["hotelling"]
        n = ht["n_target"] + ht["n_control"]
        r["t2_per_unit_pair"] = ht["T2"] / n if n else float("nan")

    # ---- Pre-registered verdict ----
    # Reviewer asked: does the signal survive different unit boundaries?
    # PASS if Cohen's d_pooled remains > 1.0 (large effect by Cohen's
    # convention) at every W tested. Documented cutoff.
    d_min = min((r["hotelling"]["cohen_d_pooled"] for r in results_per_W),
                default=float("nan"))
    d_max = max((r["hotelling"]["cohen_d_pooled"] for r in results_per_W),
                default=float("nan"))
    if all(r["hotelling"]["cohen_d_pooled"] > 1.0 for r in results_per_W) and len(results_per_W) >= 2:
        verdict = "SIGNAL_SURVIVES_FIXED_W_REWINDOWING"
    elif any(r["hotelling"]["cohen_d_pooled"] > 1.0 for r in results_per_W):
        verdict = "SIGNAL_PARTIALLY_SURVIVES"
    else:
        verdict = "SIGNAL_COLLAPSES_UNDER_REWINDOWING"

    runtime = time.time() - t0
    report = {
        "experiment": EXP,
        "task_id": "A5",
        "title": (
            "Segmentation-sensitivity: 5-D Phi_M signal under fixed-W-verse "
            "rewindowing of Quran + control corpora."
        ),
        "method": (
            "For each W in [20, 40, 80]: (1) flatten each corpus's verse "
            "list across all its native units, (2) regroup into "
            "non-overlapping W-verse windows, (3) compute 5-D features "
            "via src.features.features_5d on each window, (4) compute "
            "Hotelling T^2 of Quran-windows vs ARABIC_CTRL_POOL-windows "
            "with pooled covariance + ridge=1e-6 (matching exp49/exp53 "
            "byte-for-byte)."
        ),
        "window_sizes_tested": WINDOW_SIZES,
        "ridge_lambda": RIDGE_LAMBDA,
        "results_per_W": results_per_W,
        "locked_phi_m_baseline": locked_phi_m,
        "summary": {
            "min_cohen_d_pooled": d_min,
            "max_cohen_d_pooled": d_max,
            "verdict": verdict,
        },
        "interpretation": [
            "If `verdict = SIGNAL_SURVIVES_FIXED_W_REWINDOWING`, the "
            "Quran's 5-D fingerprint is NOT an artefact of canonical "
            "surah boundaries; the same separation appears under a "
            "uniform-W segmentation. This is the strongest defence "
            "against the reviewer's worry.",
            "If `verdict = SIGNAL_COLLAPSES_UNDER_REWINDOWING`, the "
            "5-D fingerprint depends on the surah-scale aggregation; "
            "future writing must specify that Phi_M is a property of "
            "the canonical surah segmentation rather than a "
            "segmentation-invariant text feature.",
            "Sentence-boundary and topic-shift segmentations are not "
            "covered here (heavier external dependencies; deferred).",
        ],
        "runtime_seconds": round(runtime, 2),
    }

    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Stdout
    print()
    print(f"[{EXP}] -- summary --")
    print(f"[{EXP}]   verse-segmented (locked) T^2 = {locked_phi_m['T2_baseline_per_surah']:.3f}")
    for r in results_per_W:
        ht = r["hotelling"]
        print(f"[{EXP}]   W={r['W']:3d} verses  T^2 = {ht['T2']:10.3f}  "
              f"d_pooled = {ht['cohen_d_pooled']:5.3f}   "
              f"p_F = {ht['p_F_tail']:.3e}   "
              f"n_q={ht['n_target']}  n_c={ht['n_control']}")
    print(f"[{EXP}] verdict: {verdict}  "
          f"(d_pooled in [{d_min:.3f}, {d_max:.3f}] across W)")
    print(f"[{EXP}] runtime: {runtime:.1f}s")
    print(f"[{EXP}] wrote {out / f'{EXP}.json'}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
