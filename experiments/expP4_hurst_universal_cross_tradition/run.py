"""
expP4_hurst_universal_cross_tradition/run.py
=============================================
Cross-tradition R/S Hurst extension. Tests whether long-range positive
memory in canonical chapter orderings is a property of every oral-
liturgical religious-text corpus, or only the Quran + Rigveda subset
already shown today.

Corpora (8 in canonical order, identical to expP4_cross_tradition_R3):
    quran           (Arabic)            114 surahs
    hebrew_tanakh   (Hebrew, WLC)       921 book-chapters
    greek_nt        (Greek, OpenGNT)    260 book-chapters
    iliad_greek     (Greek, Perseus)     24 books   (Hurst on books may be NaN)
    pali_dn         (Pāli, SuttaCentral) 34 suttas (Hurst on units likely NaN)
    pali_mn         (Pāli, SuttaCentral) 152 suttas
    rigveda         (Vedic, DharmicData) 1024 sūktas
    avestan_yasna   (Avestan, Geldner)   69 chapters

For each corpus, compute three R/S Hurst exponents on canonical-order
time-series:
    H_verse_words : verse-word-count over all verses (verses-within-
                    units, units-in-canonical-order).
    H_unit_words  : unit-word-count sequence (length = n_units).
    H_unit_EL     : unit EL-rate sequence (length = n_units).

Sanity check: Rigveda values must reproduce expP4_rigveda_deepdive
exactly (H_verse_words = 0.7332, H_unit_words = 0.7861, H_unit_EL = 0.5958).

Reads only:
    All corpora via raw_loader.load_all(...).
Writes ONLY under results/experiments/expP4_hurst_universal_cross_tradition/.
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
from src.features import el_rate  # noqa: E402
from src.extended_tests4 import _hurst_rs  # noqa: E402

EXP = "expP4_hurst_universal_cross_tradition"
LOCKED_QURAN_RS_HURST = 0.7381  # Supp_A_Hurst from ULTIMATE_SCORECARD
LOCKED_RIGVEDA_DD = {
    "H_verse_words": 0.7332,
    "H_unit_words":  0.7861,
    "H_unit_EL":     0.5958,
}
HURST_FLOOR = 0.6
NEG_CONTROL_CEILING = 0.55


# --------------------------------------------------------------------------- #
def _safe_hurst(seq) -> float:
    """Wrap _hurst_rs to return Python float (or nan)."""
    h = _hurst_rs(np.asarray(seq, dtype=float))
    return float(h) if not np.isnan(h) else float("nan")


def _three_hurst(units) -> dict:
    """Compute the 3 canonical-order Hurst series for one corpus."""
    if not units:
        return {
            "n_units": 0,
            "n_verses": 0,
            "H_verse_words": float("nan"),
            "H_unit_words":  float("nan"),
            "H_unit_EL":     float("nan"),
        }
    rc_words = [len(v.split()) for u in units for v in u.verses]
    unit_words = [u.n_words() for u in units]
    unit_el = [el_rate(u.verses) for u in units]
    return {
        "n_units":  int(len(units)),
        "n_verses": int(len(rc_words)),
        "H_verse_words": _safe_hurst(rc_words),
        "H_unit_words":  _safe_hurst(unit_words),
        "H_unit_EL":     _safe_hurst(unit_el),
    }


# --------------------------------------------------------------------------- #
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
    tradition_class = {
        "quran":         "oral_liturgical",
        "hebrew_tanakh": "narrative_or_mixed",
        "greek_nt":      "narrative_or_mixed",
        "iliad_greek":   "narrative_or_mixed",
        "pali_dn":       "oral_liturgical",
        "pali_mn":       "oral_liturgical",
        "rigveda":       "oral_liturgical",
        "avestan_yasna": "oral_liturgical",
    }

    print(f"[{EXP}] computing R/S Hurst for each corpus...")
    per_corpus: dict = {}
    for name in canonical_order:
        units = CORPORA.get(name, [])
        h = _three_hurst(units)
        h["tradition_class"] = tradition_class[name]
        per_corpus[name] = h
        def _fmt(x):
            return "nan" if np.isnan(x) else f"{x:+.4f}"
        print(f"[{EXP}]   {name:<18s}  n_unit={h['n_units']:>4d}  "
              f"n_verse={h['n_verses']:>6d}  "
              f"H_verse={_fmt(h['H_verse_words'])}  "
              f"H_unit={_fmt(h['H_unit_words'])}  "
              f"H_EL={_fmt(h['H_unit_EL'])}")

    # ---------------- sanity checks ----------------
    rv = per_corpus["rigveda"]
    rv_drift = {
        "H_verse_words": abs(rv["H_verse_words"] - LOCKED_RIGVEDA_DD["H_verse_words"]),
        "H_unit_words":  abs(rv["H_unit_words"]  - LOCKED_RIGVEDA_DD["H_unit_words"]),
        "H_unit_EL":     abs(rv["H_unit_EL"]     - LOCKED_RIGVEDA_DD["H_unit_EL"]),
    }
    rv_drift["max"] = float(max(rv_drift.values()))
    rv_drift["ok"] = bool(rv_drift["max"] < 1e-6)

    quran_h_verse = per_corpus["quran"]["H_verse_words"]
    quran_drift_vs_locked = float(abs(quran_h_verse - LOCKED_QURAN_RS_HURST))
    quran_sanity_ok = bool(quran_drift_vs_locked < 0.05)  # ±0.05 tolerance

    # ---------------- pre-registered predictions ----------------
    new_oral_corpora = ("pali_mn", "rigveda", "avestan_yasna")
    pred_hu_1_passes = []  # which oral corpora pass H>0.6 on at least one series
    for c in ("quran",) + new_oral_corpora:
        h = per_corpus[c]
        h_max = max(
            x for x in (h["H_verse_words"], h["H_unit_words"], h["H_unit_EL"])
            if not np.isnan(x)
        ) if any(not np.isnan(x) for x in (
            h["H_verse_words"], h["H_unit_words"], h["H_unit_EL"]
        )) else float("nan")
        h["H_max"] = float(h_max) if not np.isnan(h_max) else None
        h["passes_HU1_floor_0.6"] = bool(
            (not np.isnan(h_max)) and h_max > HURST_FLOOR
        )
        pred_hu_1_passes.append((c, h["passes_HU1_floor_0.6"]))
    pred_hu_1 = "PASS" if all(v for _, v in pred_hu_1_passes) else "FAIL"

    iliad_h_verse = per_corpus["iliad_greek"]["H_verse_words"]
    pred_hu_2 = (
        "PASS" if (not np.isnan(iliad_h_verse)
                   and iliad_h_verse <= NEG_CONTROL_CEILING)
        else "FAIL"
    )

    n_above_quran = 0
    for c in new_oral_corpora:
        h = per_corpus[c]
        if h.get("H_max") is not None and h["H_max"] > LOCKED_QURAN_RS_HURST:
            n_above_quran += 1
    pred_hu_3 = "PASS" if n_above_quran >= 3 else "FAIL"

    overall = (
        "STRONG_SUPPORT" if (pred_hu_1 == "PASS" and pred_hu_2 == "PASS"
                             and pred_hu_3 == "PASS")
        else "PARTIAL_SUPPORT" if (pred_hu_1 == "PASS" or pred_hu_2 == "PASS"
                                   or pred_hu_3 == "PASS")
        else "NO_SUPPORT"
    )

    # ---------------- summary table ----------------
    by_class_summary: dict = {}
    for cls in ("oral_liturgical", "narrative_or_mixed"):
        h_max_values = []
        for c in canonical_order:
            if tradition_class[c] != cls:
                continue
            hm = per_corpus[c].get("H_max")
            if hm is not None:
                h_max_values.append(hm)
        if h_max_values:
            arr = np.array(h_max_values)
            by_class_summary[cls] = {
                "n_corpora": int(len(h_max_values)),
                "mean_H_max":   float(arr.mean()),
                "median_H_max": float(np.median(arr)),
                "min_H_max":    float(arr.min()),
                "max_H_max":    float(arr.max()),
                "n_above_0.6":  int((arr > HURST_FLOOR).sum()),
            }

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "title": ("R/S Hurst exponent across all 8 cross-tradition "
                  "religious-text corpora, on three canonical-order "
                  "time-series (verse word-count, unit word-count, "
                  "unit EL-rate)."),
        "n_corpora": len(canonical_order),
        "canonical_order": canonical_order,
        "per_corpus": per_corpus,
        "by_tradition_class": by_class_summary,
        "sanity_checks": {
            "rigveda_drift_vs_expP4_rigveda_deepdive": rv_drift,
            "quran_H_verse_vs_locked_Supp_A_Hurst": {
                "locked_value": LOCKED_QURAN_RS_HURST,
                "current_H_verse_words": quran_h_verse,
                "abs_drift": quran_drift_vs_locked,
                "tolerance": 0.05,
                "ok": quran_sanity_ok,
            },
        },
        "pre_registered_outcomes": {
            "PRED_HU_1_universal_oral_corpora_H_above_0.6": pred_hu_1,
            "PRED_HU_1_per_corpus_pass_status": dict(pred_hu_1_passes),
            "PRED_HU_2_iliad_negative_control_H_at_or_below_0.55": pred_hu_2,
            "PRED_HU_2_iliad_H_verse_words": iliad_h_verse,
            "PRED_HU_3_three_of_three_above_quran": pred_hu_3,
            "PRED_HU_3_n_above_locked_quran": n_above_quran,
            "overall_verdict": overall,
        },
        "interpretation": [
            "If PRED-HU-1 PASSES (all 4 oral corpora exceed H=0.6 on at "
            "least one canonical series) and PRED-HU-2 PASSES (Iliad "
            "stays at H≤0.55 as negative control), then long-range "
            "positive memory is a robust property of oral-liturgical "
            "religious canon orderings — a NEW universality candidate "
            "to add to LC1 alongside the LC2 path-minimality finding.",
            "If PRED-HU-3 PASSES (all 3 cross-tradition oral corpora "
            "exceed the locked Quran Hurst), then the Quran is the "
            "FLOOR of the oral-liturgical Hurst distribution, not the "
            "ceiling. This would be a major reframe of the Quran-as-"
            "extreme-outlier narrative.",
        ],
        "extends": {
            "expP4_rigveda_deepdive": ("Rigveda Hurst values must reproduce "
                                       "exactly (drift < 1e-6)."),
            "Supp_A_Hurst (locked)":  ("Quran R/S Hurst H = 0.7381 must "
                                       "reproduce within ±0.05 on H_verse_words. "
                                       "Different chunk grid / window choice "
                                       "may add small drift."),
        },
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ---------------- console summary ----------------
    print()
    print(f"[{EXP}] -- per-corpus headline (max-of-3 series) --")
    print(f"   {'corpus':<18s}  {'class':<22s}  {'n_unit':>6s}  "
          f"{'H_verse':>9s}  {'H_unit':>9s}  {'H_EL':>9s}  HU1")
    for c in canonical_order:
        h = per_corpus[c]
        def _f(x): return "  nan   " if np.isnan(x) else f"{x:+.4f}"
        print(f"   {c:<18s}  {tradition_class[c]:<22s}  "
              f"{h['n_units']:>6d}  "
              f"{_f(h['H_verse_words']):>9s}  "
              f"{_f(h['H_unit_words']):>9s}  "
              f"{_f(h['H_unit_EL']):>9s}  "
              f"{'pass' if h.get('passes_HU1_floor_0.6', False) else '----'}")
    print()
    print(f"[{EXP}] -- pre-registered outcomes --")
    print(f"[{EXP}]   PRED-HU-1 (4 oral corpora H>0.6 on ≥1 series): {pred_hu_1}")
    for c, ok in pred_hu_1_passes:
        h = per_corpus[c]
        h_max = h.get("H_max")
        h_max_str = "nan" if h_max is None else f"{h_max:.4f}"
        flag = "pass" if ok else "FAIL"
        print(f"[{EXP}]       {c:<18s}  H_max = {h_max_str:>10s}  {flag}")
    print(f"[{EXP}]   PRED-HU-2 (Iliad H_verse ≤ 0.55): {pred_hu_2}  "
          f"(actual = {iliad_h_verse:+.4f})")
    print(f"[{EXP}]   PRED-HU-3 (3 of 3 new oral exceed locked Quran 0.7381): "
          f"{pred_hu_3}  ({n_above_quran}/3)")
    print(f"[{EXP}]   OVERALL verdict: {overall}")
    print()
    print(f"[{EXP}] -- sanity --")
    print(f"[{EXP}]   Rigveda DD reproduction max drift = {rv_drift['max']:.2e}  "
          f"({'OK' if rv_drift['ok'] else 'DRIFT'})")
    print(f"[{EXP}]   Quran H_verse vs locked Supp_A_Hurst: "
          f"{quran_h_verse:+.4f} vs {LOCKED_QURAN_RS_HURST}  "
          f"drift {quran_drift_vs_locked:.4f}  "
          f"({'OK' if quran_sanity_ok else 'OUTSIDE_TOLERANCE'})")
    print(f"[{EXP}] wrote {outfile}")

    self_check_end(pre, exp_name=EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
