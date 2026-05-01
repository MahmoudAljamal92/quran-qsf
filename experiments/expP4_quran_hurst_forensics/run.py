"""
expP4_quran_hurst_forensics/run.py
==================================
Forensics on the surprising Quran H_unit_words = 0.914 finding from
`expP4_hurst_universal_cross_tradition`.

Concern: the canonical Mushaf order is roughly "Fātiḥa-first, then
descending length", and a strictly monotonic sequence would trivially
produce H ≈ 1.0. We must rule out the trivial-monotonic explanation.

Three orthogonal checks per corpus:
  1. H_canon vs 5000-permutation null (z, p_one_sided)
  2. H_descending: monotonic ceiling on the same word-counts
  3. H_residual: R/S Hurst on residuals after linear detrending

Sanity: Quran H_canon must reproduce 0.914 (the value from yesterday).

Reads only:
    All corpora via raw_loader.load_all(...).
Writes ONLY under results/experiments/expP4_quran_hurst_forensics/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    safe_output_dir,
    self_check_begin,
    self_check_end,
)
from src import raw_loader  # noqa: E402
from src.extended_tests4 import _hurst_rs  # noqa: E402

EXP = "expP4_quran_hurst_forensics"
N_PERM = 5000
SEED_BASE = 42


def _safe_h(seq) -> float:
    h = _hurst_rs(np.asarray(seq, dtype=float))
    return float(h) if not np.isnan(h) else float("nan")


def _detrend_linear(seq: np.ndarray) -> np.ndarray:
    """Subtract least-squares linear fit y = a + b*i. Return residuals."""
    n = len(seq)
    if n < 3:
        return seq.copy()
    i = np.arange(n, dtype=float)
    b, a = np.polyfit(i, seq, 1)
    return seq - (a + b * i)


def _forensics_for_corpus(name: str, units, seed: int) -> dict:
    """Run all 4 Hurst measurements for one corpus."""
    if not units:
        return {"n_units": 0, "skipped": True, "reason": "no units"}
    word_counts = np.array([u.n_words() for u in units], dtype=float)
    n = len(word_counts)
    if n < 10:
        return {"n_units": n, "skipped": True, "reason": "n<10"}

    # 1. Canonical
    h_canon = _safe_h(word_counts)
    if np.isnan(h_canon):
        return {"n_units": n, "skipped": True,
                "reason": "Hurst undefined on this length"}

    # 2. Permutation null
    rng = np.random.default_rng(seed)
    perm_h = []
    for _ in range(N_PERM):
        idx = rng.permutation(n)
        h = _safe_h(word_counts[idx])
        if not np.isnan(h):
            perm_h.append(h)
    perm_h_arr = np.array(perm_h, dtype=float)
    n_valid_perms = len(perm_h_arr)
    if n_valid_perms < 100:
        return {"n_units": n, "skipped": True,
                "reason": f"insufficient valid perms ({n_valid_perms})"}
    perm_mean = float(perm_h_arr.mean())
    perm_std = float(perm_h_arr.std())
    z = (h_canon - perm_mean) / (perm_std if perm_std > 0 else 1.0)
    pct_above = float((perm_h_arr >= h_canon).mean())
    p_one_sided = max(pct_above, 1.0 / (n_valid_perms + 1))

    # 3. Strict descending-length ordering (monotonic ceiling)
    sorted_desc = np.sort(word_counts)[::-1]
    h_desc = _safe_h(sorted_desc)

    # 4. Linear-detrended canonical
    residuals = _detrend_linear(word_counts)
    h_residual = _safe_h(residuals)

    return {
        "n_units": int(n),
        "n_valid_perms": int(n_valid_perms),
        "H_canon": float(h_canon),
        "perm_mean": perm_mean,
        "perm_std": perm_std,
        "z_canon_vs_null": float(z),
        "pct_perms_above_canon": pct_above,
        "p_one_sided": float(p_one_sided),
        "H_descending_ceiling": float(h_desc) if not np.isnan(h_desc) else None,
        "H_residual_after_linear_detrend": (
            float(h_residual) if not np.isnan(h_residual) else None
        ),
        "word_count_summary": {
            "min": float(word_counts.min()),
            "max": float(word_counts.max()),
            "mean": float(word_counts.mean()),
            "median": float(np.median(word_counts)),
        },
    }


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    print(f"[{EXP}] loading corpora...")
    CORPORA = raw_loader.load_all(
        include_extras=True,
        include_cross_lang=True,
        include_cross_tradition=True,
    )

    canonical_order = [
        "quran",
        "hebrew_tanakh",
        "greek_nt",
        "iliad_greek",
        "pali_dn",
        "pali_mn",
        "rigveda",
        "avestan_yasna",
    ]

    print(f"[{EXP}] running per-corpus Hurst forensics ({N_PERM} perms each)...")
    results = {}
    for k, name in enumerate(canonical_order):
        units = CORPORA.get(name, [])
        r = _forensics_for_corpus(name, units, seed=SEED_BASE + k)
        results[name] = r
        if r.get("skipped"):
            print(f"[{EXP}]   {name:<18s}  SKIPPED: {r.get('reason')}")
            continue
        print(f"[{EXP}]   {name:<18s}  n={r['n_units']:>4d}  "
              f"H_canon={r['H_canon']:+.4f}  "
              f"perm_mean={r['perm_mean']:+.4f}±{r['perm_std']:.4f}  "
              f"z={r['z_canon_vs_null']:+7.3f}  "
              f"p={r['p_one_sided']:.4f}  "
              f"H_desc={r['H_descending_ceiling']:+.4f}  "
              f"H_resid={r['H_residual_after_linear_detrend']:+.4f}")

    # ---- Sanity ----
    locked_quran = 0.914  # from expP4_hurst_universal_cross_tradition
    quran_h = results["quran"].get("H_canon")
    quran_drift = (abs(quran_h - locked_quran) if quran_h is not None
                   else float("nan"))
    quran_sanity = bool((quran_drift is not None) and quran_drift < 1e-3)

    # ---- Pre-registered outcomes ----
    qr = results["quran"]
    pred_q1 = "PASS" if (qr.get("z_canon_vs_null", 0) > 3.0
                         and qr.get("p_one_sided", 1.0) < 0.001) else "FAIL"
    pred_q2 = "PASS" if ((qr.get("H_descending_ceiling") or 0) > 0.95) else "FAIL"
    pred_q3 = "PASS" if ((qr.get("H_residual_after_linear_detrend") or 0)
                         > 0.6) else "FAIL"
    n_other_pass = 0
    for c in canonical_order[1:]:
        rc = results[c]
        if rc.get("skipped"):
            continue
        if rc.get("z_canon_vs_null", 0) > 3.0:
            n_other_pass += 1
    pred_q4 = "PASS" if n_other_pass >= 5 else "FAIL"

    overall = (
        "STRONG_SUPPORT" if (pred_q1 == "PASS" and pred_q3 == "PASS"
                             and pred_q4 == "PASS")
        else "PARTIAL_SUPPORT" if (pred_q1 == "PASS" or pred_q3 == "PASS")
        else "NO_SUPPORT"
    )

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "title": ("Forensic check on Quran H_unit_words = 0.914 from "
                  "expP4_hurst_universal_cross_tradition: rule out the "
                  "trivial descending-length monotonic explanation."),
        "n_perm": N_PERM,
        "seed_base": SEED_BASE,
        "results_per_corpus": results,
        "sanity": {
            "quran_H_canon": quran_h,
            "expected_from_locked_universal_test": locked_quran,
            "abs_drift": quran_drift,
            "ok_within_1e-3": quran_sanity,
        },
        "pre_registered_outcomes": {
            "PRED_Q1_canon_vs_perm_null": pred_q1,
            "PRED_Q2_descending_ceiling_above_0.95": pred_q2,
            "PRED_Q3_detrended_residual_above_0.6": pred_q3,
            "PRED_Q4_other_corpora_canonical_significant": pred_q4,
            "PRED_Q4_n_other_corpora_significant_z_above_3": n_other_pass,
            "overall_verdict": overall,
        },
        "interpretation": [
            "If PRED-Q1 PASSES, the canonical Mushaf order is genuinely "
            "more Hurst-extreme than random permutations of the same "
            "word-counts -- the 0.914 is structural.",
            "If PRED-Q3 PASSES (detrended residual H > 0.6), then the "
            "Hurst is NOT solely the trivial descending-length effect "
            "-- there is genuine long-range memory in the residuals.",
            "If PRED-Q4 PASSES, the canonical-order Hurst is a cross-"
            "tradition phenomenon, not a Quran-specific artefact.",
            "If all three PASS, the new Quran finding is robust and "
            "joins the cross-tradition LC-Hurst universal candidate "
            "with strong supporting evidence.",
        ],
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ---------------- summary ----------------
    print()
    print(f"[{EXP}] -- pre-registered outcomes --")
    print(f"[{EXP}]   PRED-Q1 (canon z > 3 vs 5000 perm null): {pred_q1}")
    if not qr.get("skipped"):
        print(f"[{EXP}]      Quran z = {qr['z_canon_vs_null']:+.3f}  "
              f"p_one_sided = {qr['p_one_sided']:.4f}")
        print(f"[{EXP}]      Permutation null: mean = "
              f"{qr['perm_mean']:.4f}  std = {qr['perm_std']:.4f}")
    print(f"[{EXP}]   PRED-Q2 (descending ceiling H > 0.95): {pred_q2}  "
          f"actual = {qr.get('H_descending_ceiling', 'nan')}")
    print(f"[{EXP}]   PRED-Q3 (detrended residual H > 0.6): {pred_q3}  "
          f"actual = {qr.get('H_residual_after_linear_detrend', 'nan')}")
    print(f"[{EXP}]   PRED-Q4 (≥5/7 other corpora z > 3): {pred_q4}  "
          f"({n_other_pass}/7)")
    print(f"[{EXP}]   OVERALL: {overall}")
    print()
    print(f"[{EXP}] -- sanity --")
    print(f"[{EXP}]   Quran H_canon reproduction drift "
          f"({quran_h:.4f} vs {locked_quran}) = {quran_drift:.2e}  "
          f"({'OK' if quran_sanity else 'DRIFT'})")
    print(f"[{EXP}] wrote {outfile}")

    self_check_end(pre, exp_name=EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
