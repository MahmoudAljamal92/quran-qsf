"""
exp90_cross_language_el/run.py
===============================
Cross-language EL convergence test. Language-agnostic EL (verse-final
rhyme rate) computed per Band-A unit across Arabic / Hebrew / Greek.

Pre-registered in PREREG.md. Tests whether Quran's near-saturating EL
(~0.71) has a cross-language scripture analogue in Hebrew Tanakh and
Greek NT, relative to Iliad (secular Greek) and secular Arabic.

Reads (integrity-checked):
    phase_06_phi_m.pkl                  -> Arabic Band-A (Quran + controls)
    data/corpora/he/tanakh_wlc.txt      -> via raw_loader
    data/corpora/el/opengnt_v3_3.csv    -> via raw_loader
    data/corpora/el/iliad_perseus.xml   -> via raw_loader

Writes ONLY under results/experiments/exp90_cross_language_el/
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

EXP = "exp90_cross_language_el"
BAND_LO, BAND_HI = 15, 100
EL_THRESHOLD = 0.3642  # From LC3-70-U: 1.5221 / 4.1790 at T=0
COHEN_D_CUT = 0.5
CROSSING_CUT = 0.25

# Pre-registered corpus groupings (frozen in PREREG.md)
ARABIC_SECULAR = ["poetry_jahili", "poetry_islami", "poetry_abbasi", "ksucca", "hindawi"]
ARABIC_SCRIPTURE = ["quran", "arabic_bible"]
CROSSLANG_SCRIPTURE = ["hebrew_tanakh", "greek_nt"]
CROSSLANG_SECULAR = ["iliad_greek"]


def cohen_d(a: np.ndarray, b: np.ndarray) -> float:
    """Pooled-SD standardised mean difference, ddof=1. Returns d_{a vs b}."""
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


def summarize(arr: np.ndarray) -> dict:
    arr = np.asarray(arr, dtype=float)
    if arr.size == 0:
        return {"n": 0, "mean": None, "std": None, "median": None,
                "ci_lo": None, "ci_hi": None, "min": None, "max": None,
                "frac_over_threshold": None}
    lo = float(np.percentile(arr, 2.5)) if arr.size >= 2 else float(arr.min())
    hi = float(np.percentile(arr, 97.5)) if arr.size >= 2 else float(arr.max())
    return {
        "n": int(arr.size),
        "mean": round(float(arr.mean()), 6),
        "std": round(float(arr.std(ddof=1)) if arr.size >= 2 else 0.0, 6),
        "median": round(float(np.median(arr)), 6),
        "ci_lo": round(lo, 6),
        "ci_hi": round(hi, 6),
        "min": round(float(arr.min()), 6),
        "max": round(float(arr.max()), 6),
        "frac_over_threshold": round(float((arr >= EL_THRESHOLD).mean()), 6),
    }


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    from src import raw_loader  # noqa: E402
    from src.features import el_rate  # noqa: E402

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    # ---------------- Arabic: reuse phase_06_phi_m.pkl Band-A features ---------
    print(f"[{EXP}] Loading phase_06_phi_m.pkl for Arabic Band-A EL values...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    feat_cols = list(state["FEAT_COLS"])
    el_idx = feat_cols.index("EL")
    X_Q = np.asarray(state["X_QURAN"], dtype=float)
    X_C = np.asarray(state["X_CTRL_POOL"], dtype=float)
    ctrl_pool = list(state["ARABIC_CTRL_POOL"])
    feats = state["FEATS"]
    band_lo = int(state.get("BAND_A_LO", BAND_LO))
    band_hi = int(state.get("BAND_A_HI", BAND_HI))

    # Walk ctrl_pool to align EL values with corpus names
    per_corpus_EL = {}
    per_corpus_EL["quran"] = X_Q[:, el_idx].tolist()
    offset = 0
    for cname in ctrl_pool:
        recs = [r for r in feats.get(cname, [])
                if band_lo <= r["n_verses"] <= band_hi]
        n = len(recs)
        if n == 0:
            per_corpus_EL[cname] = []
            continue
        per_corpus_EL[cname] = X_C[offset:offset + n, el_idx].tolist()
        offset += n

    for cname, els in per_corpus_EL.items():
        if els:
            print(f"[{EXP}]   {cname:18s}  n={len(els):4d}  "
                  f"mean EL = {np.mean(els):.4f}")

    # ---------------- Cross-language: load via raw_loader ----------------------
    print(f"\n[{EXP}] Loading cross-language corpora (Tanakh, Greek NT, Iliad)...")
    CORPORA = raw_loader.load_all(include_extras=True, include_cross_lang=True)
    for cname in ["hebrew_tanakh", "greek_nt", "iliad_greek"]:
        units = CORPORA.get(cname, [])
        if not units:
            print(f"[{EXP}] WARN: {cname} missing from raw_loader.load_all()")
            per_corpus_EL[cname] = []
            continue
        band_a_units = [u for u in units if BAND_LO <= len(u.verses) <= BAND_HI]
        print(f"[{EXP}]   {cname:18s}  total={len(units)}  band-A={len(band_a_units)}  "
              f"(BAND_A [{BAND_LO}, {BAND_HI}])")
        els = [float(el_rate(u.verses)) for u in band_a_units]
        per_corpus_EL[cname] = els
        if els:
            print(f"[{EXP}]     mean EL = {np.mean(els):.4f}  "
                  f"(std = {np.std(els, ddof=1):.4f})")

    # ---------------- Per-corpus summary ---------------------------------------
    per_corpus = {
        cname: summarize(np.asarray(els)) for cname, els in per_corpus_EL.items()
    }

    # ---------------- Pooled groups --------------------------------------------
    def pool(names: list[str]) -> np.ndarray:
        vals = []
        for n in names:
            vals.extend(per_corpus_EL.get(n, []))
        return np.asarray(vals, dtype=float)

    pool_arabic_secular = pool(ARABIC_SECULAR)
    pool_arabic_scripture = pool(ARABIC_SCRIPTURE)
    pool_crosslang_scripture = pool(CROSSLANG_SCRIPTURE)

    tanakh_el = np.asarray(per_corpus_EL.get("hebrew_tanakh", []), dtype=float)
    nt_el = np.asarray(per_corpus_EL.get("greek_nt", []), dtype=float)
    iliad_el = np.asarray(per_corpus_EL.get("iliad_greek", []), dtype=float)
    poetry_el = np.asarray(
        per_corpus_EL.get("poetry_jahili", [])
        + per_corpus_EL.get("poetry_islami", [])
        + per_corpus_EL.get("poetry_abbasi", []),
        dtype=float,
    )

    # ---------------- Hypothesis tests -----------------------------------------
    d_nt_vs_iliad = cohen_d(nt_el, iliad_el)
    d_tanakh_vs_arab_sec = cohen_d(tanakh_el, pool_arabic_secular)
    d_tanakh_vs_iliad = cohen_d(tanakh_el, iliad_el)
    d_quran_vs_arab_sec = cohen_d(
        np.asarray(per_corpus_EL["quran"]), pool_arabic_secular)
    d_bible_vs_arab_sec = cohen_d(
        np.asarray(per_corpus_EL.get("arabic_bible", [])), pool_arabic_secular)

    frac_tanakh_over = (
        float((tanakh_el >= EL_THRESHOLD).mean())
        if tanakh_el.size > 0 else None)
    frac_nt_over = (
        float((nt_el >= EL_THRESHOLD).mean()) if nt_el.size > 0 else None)
    frac_iliad_over = (
        float((iliad_el >= EL_THRESHOLD).mean()) if iliad_el.size > 0 else None)
    frac_poetry_over = (
        float((poetry_el >= EL_THRESHOLD).mean()) if poetry_el.size > 0 else None)

    # ---------------- Pre-registered verdict ladder ----------------------------
    # Step 1: FAIL_iliad_high
    iliad_mean = float(iliad_el.mean()) if iliad_el.size > 0 else float("nan")
    arab_sec_mean = (float(pool_arabic_secular.mean())
                     if pool_arabic_secular.size > 0 else float("nan"))
    iliad_high = (
        np.isfinite(iliad_mean) and np.isfinite(arab_sec_mean)
        and iliad_mean > arab_sec_mean
    )

    # Step 2 candidates
    greek_scripture_passes = (
        np.isfinite(d_nt_vs_iliad) and d_nt_vs_iliad >= COHEN_D_CUT
        and frac_nt_over is not None and frac_nt_over >= CROSSING_CUT
    )
    hebrew_scripture_passes = (
        np.isfinite(d_tanakh_vs_arab_sec) and d_tanakh_vs_arab_sec >= COHEN_D_CUT
        and frac_tanakh_over is not None and frac_tanakh_over >= CROSSING_CUT
    )

    if iliad_high:
        verdict = "FAIL_iliad_high"
    elif greek_scripture_passes and hebrew_scripture_passes:
        verdict = "PASS_full_convergence"
    elif greek_scripture_passes or hebrew_scripture_passes:
        verdict = "PASS_partial_convergence"
    elif (not greek_scripture_passes and not hebrew_scripture_passes):
        verdict = "FAIL_no_convergence"
    else:
        verdict = "MIXED"

    # ---------------- Print ---------------------------------------------------
    print(f"\n{'=' * 72}")
    print(f"[{EXP}] CROSS-LANGUAGE EL SUMMARY (Band-A [{BAND_LO}, {BAND_HI}])")
    print(f"{'=' * 72}")
    for cname in ["quran", "arabic_bible",
                  "poetry_jahili", "poetry_islami", "poetry_abbasi",
                  "ksucca", "hindawi",
                  "hebrew_tanakh", "greek_nt", "iliad_greek"]:
        s = per_corpus[cname]
        if s["n"] == 0:
            print(f"  {cname:18s}  (empty)")
            continue
        pct_over = (s['frac_over_threshold'] * 100
                    if s['frac_over_threshold'] is not None else 0.0)
        print(f"  {cname:18s}  n={s['n']:4d}  EL mean={s['mean']:.4f}  "
              f"std={s['std']:.4f}  "
              f"%>={EL_THRESHOLD:.3f}: {pct_over:5.1f}%")
    print()
    print(f"  Cohen d (Greek NT > Iliad):           {d_nt_vs_iliad:+.3f}   (cut {COHEN_D_CUT})")
    print(f"  Cohen d (Tanakh > arab-secular pool): {d_tanakh_vs_arab_sec:+.3f}")
    print(f"  Cohen d (Tanakh > Iliad):             {d_tanakh_vs_iliad:+.3f}")
    print(f"  Cohen d (Quran > arab-secular pool):  {d_quran_vs_arab_sec:+.3f}")
    print(f"  Cohen d (arabic_bible > arab-sec):    {d_bible_vs_arab_sec:+.3f}")
    print(f"  Greek NT % over EL=0.364:  "
          f"{(frac_nt_over*100 if frac_nt_over else 0):5.1f}%  (cut {CROSSING_CUT*100:.0f}%)")
    print(f"  Tanakh   % over EL=0.364:  "
          f"{(frac_tanakh_over*100 if frac_tanakh_over else 0):5.1f}%")
    print(f"  Iliad    % over EL=0.364:  "
          f"{(frac_iliad_over*100 if frac_iliad_over else 0):5.1f}%")
    print(f"  Poetry   % over EL=0.364:  "
          f"{(frac_poetry_over*100 if frac_poetry_over else 0):5.1f}%")
    print()
    print(f"  Iliad mean EL = {iliad_mean:.4f}  vs arab-secular pool mean EL = {arab_sec_mean:.4f}  "
          f"-> Iliad > arab-secular: {iliad_high}")
    print(f"{'=' * 72}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    print(f"{'=' * 72}")

    elapsed = time.time() - t0

    report = {
        "experiment": EXP,
        "hypothesis": "H-EL-CONV — cross-language EL convergence across scriptures",
        "schema_version": 1,
        "prereg_document": "experiments/exp90_cross_language_el/PREREG.md",
        "prereg_constants": {
            "BAND_LO": BAND_LO,
            "BAND_HI": BAND_HI,
            "EL_THRESHOLD": EL_THRESHOLD,
            "COHEN_D_CUT": COHEN_D_CUT,
            "CROSSING_CUT": CROSSING_CUT,
        },
        "per_corpus": per_corpus,
        "effect_sizes": {
            "d_greek_nt_vs_iliad": round(d_nt_vs_iliad, 4),
            "d_tanakh_vs_arab_secular": round(d_tanakh_vs_arab_sec, 4),
            "d_tanakh_vs_iliad": round(d_tanakh_vs_iliad, 4),
            "d_quran_vs_arab_secular": round(d_quran_vs_arab_sec, 4),
            "d_arabic_bible_vs_arab_secular": round(d_bible_vs_arab_sec, 4),
        },
        "crossing_rates": {
            "greek_nt_frac_over_0_364": frac_nt_over,
            "tanakh_frac_over_0_364": frac_tanakh_over,
            "iliad_frac_over_0_364": frac_iliad_over,
            "arabic_poetry_frac_over_0_364": frac_poetry_over,
        },
        "pooled_means": {
            "arabic_scripture_n": int(pool_arabic_scripture.size),
            "arabic_scripture_mean_EL": (
                round(float(pool_arabic_scripture.mean()), 6)
                if pool_arabic_scripture.size > 0 else None),
            "arabic_secular_n": int(pool_arabic_secular.size),
            "arabic_secular_mean_EL": (
                round(arab_sec_mean, 6)
                if np.isfinite(arab_sec_mean) else None),
            "crosslang_scripture_n": int(pool_crosslang_scripture.size),
            "crosslang_scripture_mean_EL": (
                round(float(pool_crosslang_scripture.mean()), 6)
                if pool_crosslang_scripture.size > 0 else None),
        },
        "prereg_tests": {
            "iliad_higher_than_arabic_secular": bool(iliad_high),
            "greek_nt_scripture_convergence_passes": bool(greek_scripture_passes),
            "tanakh_scripture_convergence_passes": bool(hebrew_scripture_passes),
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
