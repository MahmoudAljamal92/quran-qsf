"""
exp68_hurst_ladder/run.py
==========================
H19: Multi-Level Hurst Ladder — Unifying AR(1), VL_CV, and Long-Memory.

Motivation
    MASTER_FINDINGS_REPORT §3, §11B reports a four-level Hurst ladder:
    H_verse=0.898 → H_delta=0.811 → H_word=0.652 → H_alif_gap=0.676.
    This experiment replicates and cross-validates the ladder across
    all corpora using both R/S and DFA methods.

Protocol (frozen before execution)
    T1. For each surah/unit (≥20 verses), compute Hurst at 4 levels:
        - H_verse: verse-length (word count) sequence
        - H_delta: first-differenced verse-lengths
        - H_word:  per-word character counts (concatenated)
        - H_alif:  gaps between alif (ا) in stripped rasm
    T2. Use both R/S (nolds.hurst_rs) and DFA (nolds.dfa).
    T3. Aggregate per corpus: median and IQR at each level.
    T4. Test pre-registered claims:
        a) Monotone ladder: H_verse > H_delta for Quran
        b) H_delta(Quran) < H_delta(controls) by ≥ 2×
    T5. Cohen's d for Quran vs each control at each level.

Pre-registered thresholds
    LADDER_CONFIRMED:  monotone H_verse > H_delta for Quran AND
                       H_delta(Q) < H_delta(Bible) by ≥ 2× AND
                       preserved on ≥ 2 controls
    PARTIAL:           monotone for Quran only
    FAILS:             non-monotone OR no cross-corpus gap

Reads (integrity-checked):
    phase_06_phi_m.pkl -> CORPORA

Writes ONLY under results/experiments/exp68_hurst_ladder/
"""
from __future__ import annotations

import json
import math
import re
import sys
import time
import warnings
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

EXP = "exp68_hurst_ladder"

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

MIN_VERSES = 20        # Minimum verses for reliable Hurst estimation
MIN_SERIES_LEN = 20    # Minimum data points for nolds
SEED = 42

# Arabic letter range for rasm stripping
_ARABIC_LETTERS = re.compile(r'[\u0621-\u064A]')
_ALIF = 'ا'


# ---------------------------------------------------------------------------
# Sequence extraction
# ---------------------------------------------------------------------------
def _verse_lengths(verses: list[str]) -> np.ndarray:
    """Word counts per verse."""
    return np.array([len(v.split()) for v in verses], dtype=float)


def _delta_lengths(lens: np.ndarray) -> np.ndarray:
    """First differences of verse lengths."""
    return np.diff(lens)


def _word_char_lengths(verses: list[str]) -> np.ndarray:
    """Character count per word (all words concatenated)."""
    words = []
    for v in verses:
        words.extend(v.split())
    return np.array([len(w) for w in words], dtype=float)


def _alif_gaps(verses: list[str]) -> np.ndarray:
    """Gaps (in character positions) between consecutive alif in rasm."""
    rasm = ''.join(_ARABIC_LETTERS.findall(' '.join(verses)))
    positions = [i for i, c in enumerate(rasm) if c == _ALIF]
    if len(positions) < 2:
        return np.array([], dtype=float)
    return np.diff(positions).astype(float)


# ---------------------------------------------------------------------------
# Hurst estimators
# ---------------------------------------------------------------------------
def _hurst_rs(series: np.ndarray) -> float:
    """R/S Hurst exponent via nolds."""
    if len(series) < MIN_SERIES_LEN:
        return float("nan")
    try:
        import nolds
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return float(nolds.hurst_rs(series))
    except Exception:
        return float("nan")


def _hurst_dfa(series: np.ndarray) -> float:
    """DFA Hurst exponent via nolds."""
    if len(series) < MIN_SERIES_LEN:
        return float("nan")
    try:
        import nolds
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return float(nolds.dfa(series))
    except Exception:
        return float("nan")


# ---------------------------------------------------------------------------
# Per-unit computation
# ---------------------------------------------------------------------------
def _compute_ladder(verses: list[str]) -> dict | None:
    """Compute 4-level Hurst ladder for one unit."""
    if len(verses) < MIN_VERSES:
        return None

    lens = _verse_lengths(verses)
    deltas = _delta_lengths(lens)
    wlens = _word_char_lengths(verses)
    agaps = _alif_gaps(verses)

    result = {}

    # H_verse
    result["H_verse_rs"] = _hurst_rs(lens)
    result["H_verse_dfa"] = _hurst_dfa(lens)

    # H_delta
    if len(deltas) >= MIN_SERIES_LEN:
        result["H_delta_rs"] = _hurst_rs(deltas)
        result["H_delta_dfa"] = _hurst_dfa(deltas)
    else:
        result["H_delta_rs"] = float("nan")
        result["H_delta_dfa"] = float("nan")

    # H_word
    result["H_word_rs"] = _hurst_rs(wlens)
    result["H_word_dfa"] = _hurst_dfa(wlens)

    # H_alif
    if len(agaps) >= MIN_SERIES_LEN:
        result["H_alif_rs"] = _hurst_rs(agaps)
        result["H_alif_dfa"] = _hurst_dfa(agaps)
    else:
        result["H_alif_rs"] = float("nan")
        result["H_alif_dfa"] = float("nan")

    result["n_verses"] = len(verses)
    return result


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------
def _median_iqr(vals: list[float]) -> dict:
    v = [x for x in vals if math.isfinite(x)]
    if not v:
        return {"median": float("nan"), "q25": float("nan"),
                "q75": float("nan"), "n": 0}
    return {
        "median": round(float(np.median(v)), 4),
        "q25": round(float(np.percentile(v, 25)), 4),
        "q75": round(float(np.percentile(v, 75)), 4),
        "n": len(v),
    }


def _cohen_d(a: list[float], b: list[float]) -> float:
    a = [x for x in a if math.isfinite(x)]
    b = [x for x in b if math.isfinite(x)]
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    ma, mb = np.mean(a), np.mean(b)
    sa, sb = np.std(a, ddof=1), np.std(b, ddof=1)
    sp = math.sqrt((sa**2 + sb**2) / 2)
    return float((ma - mb) / sp) if sp > 1e-12 else 0.0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    # --- T1: Compute Hurst ladder for all corpora ---
    levels = ["H_verse", "H_delta", "H_word", "H_alif"]
    methods = ["rs", "dfa"]
    keys = [f"{lv}_{m}" for lv in levels for m in methods]

    corpus_data = {}
    for cname in ["quran"] + ARABIC_CTRL:
        units = CORPORA.get(cname, [])
        rows = []
        for u in units:
            r = _compute_ladder(u.verses)
            if r is not None:
                r["label"] = u.label
                rows.append(r)
        corpus_data[cname] = rows
        print(f"[{EXP}] {cname:20s}: {len(rows):5d} units (≥{MIN_VERSES}v)")

    # --- T3: Aggregate per corpus ---
    print(f"\n[{EXP}] === Hurst Ladder (median ± IQR) ===")
    agg = {}
    for cname in ["quran"] + ARABIC_CTRL:
        rows = corpus_data[cname]
        entry = {}
        for k in keys:
            vals = [r[k] for r in rows]
            entry[k] = _median_iqr(vals)
        agg[cname] = entry

    # Print R/S ladder
    header = f"{'Corpus':20s}"
    for lv in levels:
        header += f"  {lv+'_rs':>12s}"
    print(header)
    print("-" * len(header))
    for cname in ["quran"] + ARABIC_CTRL:
        line = f"{cname:20s}"
        for lv in levels:
            med = agg[cname][f"{lv}_rs"]["median"]
            n = agg[cname][f"{lv}_rs"]["n"]
            line += f"  {med:12.4f}" if math.isfinite(med) else f"  {'NaN':>12s}"
        print(line)

    # Print DFA ladder
    print()
    header = f"{'Corpus':20s}"
    for lv in levels:
        header += f"  {lv+'_dfa':>12s}"
    print(header)
    print("-" * len(header))
    for cname in ["quran"] + ARABIC_CTRL:
        line = f"{cname:20s}"
        for lv in levels:
            med = agg[cname][f"{lv}_dfa"]["median"]
            line += f"  {med:12.4f}" if math.isfinite(med) else f"  {'NaN':>12s}"
        print(line)

    # --- T4: Pre-registered tests ---
    print(f"\n[{EXP}] === T4: Pre-registered tests ===")

    q_rows = corpus_data["quran"]

    # T4a: Monotone ladder for Quran (H_verse > H_delta)
    q_h_verse_rs = [r["H_verse_rs"] for r in q_rows if math.isfinite(r["H_verse_rs"])]
    q_h_delta_rs = [r["H_delta_rs"] for r in q_rows if math.isfinite(r["H_delta_rs"])]
    q_h_word_rs = [r["H_word_rs"] for r in q_rows if math.isfinite(r["H_word_rs"])]

    med_verse = float(np.median(q_h_verse_rs)) if q_h_verse_rs else float("nan")
    med_delta = float(np.median(q_h_delta_rs)) if q_h_delta_rs else float("nan")
    med_word = float(np.median(q_h_word_rs)) if q_h_word_rs else float("nan")

    monotone_q = (med_verse > med_delta)
    print(f"[{EXP}] Quran R/S ladder: H_verse={med_verse:.4f} > "
          f"H_delta={med_delta:.4f} → {'MONOTONE' if monotone_q else 'NOT MONOTONE'}")

    # T4b: H_delta(Quran) vs H_delta(Bible)
    bible_rows = corpus_data.get("arabic_bible", [])
    b_h_delta_rs = [r["H_delta_rs"] for r in bible_rows
                    if math.isfinite(r["H_delta_rs"])]
    med_delta_bible = float(np.median(b_h_delta_rs)) if b_h_delta_rs else float("nan")

    if math.isfinite(med_delta) and math.isfinite(med_delta_bible) and med_delta_bible > 0:
        ratio = med_delta / med_delta_bible
        ratio_test = ratio <= 0.5  # Quran is ≤ half of Bible = ≥ 2× gap
    else:
        ratio = float("nan")
        ratio_test = False

    print(f"[{EXP}] H_delta: Quran={med_delta:.4f}, Bible={med_delta_bible:.4f}, "
          f"ratio={ratio:.4f} → {'≥2× gap' if ratio_test else 'NO 2× gap'}")

    # T4c: Monotone preserved in ≥ 2 controls
    n_monotone_ctrl = 0
    for cname in ARABIC_CTRL:
        rows_c = corpus_data[cname]
        c_verse = [r["H_verse_rs"] for r in rows_c if math.isfinite(r["H_verse_rs"])]
        c_delta = [r["H_delta_rs"] for r in rows_c if math.isfinite(r["H_delta_rs"])]
        if c_verse and c_delta:
            mv = float(np.median(c_verse))
            md = float(np.median(c_delta))
            mono = mv > md
            if mono:
                n_monotone_ctrl += 1
            print(f"  {cname:20s}: verse={mv:.4f}, delta={md:.4f} → "
                  f"{'MONO' if mono else 'NOT'}")
    print(f"[{EXP}] Monotone in {n_monotone_ctrl} controls (threshold ≥ 2)")

    # --- T5: Cohen's d at each level ---
    print(f"\n[{EXP}] === T5: Cohen's d (Quran vs each corpus) ===")
    d_results = {}
    for lv in levels:
        k_rs = f"{lv}_rs"
        q_vals = [r[k_rs] for r in q_rows]
        d_row = {}
        for cname in ARABIC_CTRL:
            c_vals = [r[k_rs] for r in corpus_data[cname]]
            d_val = _cohen_d(q_vals, c_vals)
            d_row[cname] = round(d_val, 4)
        d_results[lv] = d_row

    # Print d table
    header = f"{'Level':12s}"
    for cname in ARABIC_CTRL:
        header += f"  {cname[:12]:>12s}"
    print(header)
    print("-" * len(header))
    for lv in levels:
        line = f"{lv:12s}"
        for cname in ARABIC_CTRL:
            d_val = d_results[lv][cname]
            line += f"  {d_val:+12.3f}" if math.isfinite(d_val) else f"  {'NaN':>12s}"
        print(line)

    # --- Verdict ---
    if monotone_q and ratio_test and n_monotone_ctrl >= 2:
        verdict = "LADDER_CONFIRMED"
    elif monotone_q:
        verdict = "PARTIAL"
    else:
        verdict = "FAILS"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Monotone (Quran): {monotone_q}")
    print(f"  H_delta ratio (Q/Bible): {ratio:.4f} (threshold ≤ 0.5)")
    print(f"  Monotone controls: {n_monotone_ctrl}/6 (threshold ≥ 2)")
    print(f"{'=' * 60}")

    # --- Report ---
    report = {
        "experiment": EXP,
        "hypothesis": "H19 — Multi-level Hurst ladder: does the Quran show a "
                      "monotone-descending Hurst ladder with unique anti-persistence?",
        "schema_version": 1,
        "data": {
            "min_verses": MIN_VERSES,
            "levels": levels,
            "methods": methods,
        },
        "per_corpus_aggregate": agg,
        "quran_ladder_rs": {
            "H_verse": med_verse,
            "H_delta": med_delta,
            "H_word": med_word,
        },
        "T4_tests": {
            "monotone_quran": monotone_q,
            "delta_ratio_q_over_bible": round(ratio, 4) if math.isfinite(ratio) else None,
            "delta_ratio_test_pass": ratio_test,
            "n_monotone_controls": n_monotone_ctrl,
        },
        "T5_cohen_d": d_results,
        "verdict": {
            "verdict": verdict,
            "prereg": {
                "LADDER_CONFIRMED": "monotone Q AND H_delta ratio ≤ 0.5 AND ≥2 ctrl monotone",
                "PARTIAL": "monotone Q only",
                "FAILS": "non-monotone Q",
            },
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
