"""
expP8_T_pos_cross_tradition/run.py
==================================
Cross-tradition extension of the locked %T_pos = 39.7 % Quran finding
(D14 / S6 / row-14 of RANKED_FINDINGS).

Tests whether the Quran's 397x %T_pos enrichment over Arabic controls
under T_canon (CamelTools roots) survives:
  (a) the language-agnostic surrogate T_lang = H_cond_initials - H_el
  (b) cross-tradition replication on Hebrew, Greek, Pali, Sanskrit,
      and Avestan oral / narrative corpora.

Pre-registered in PREREG.md (2026-04-26 PRE-RUN).

Reads:
  - 8 cross-tradition corpora via raw_loader.load_all(...)
  - 6 Arabic ctrl corpora via the same call
  - phase_06_phi_m.pkl (sanity x-check of locked 39.7 % under T_canon)

Writes ONLY under results/experiments/expP8_T_pos_cross_tradition/:
  - expP8_T_pos_cross_tradition.json
  - self_check_<ts>.json
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
    safe_output_dir,
    self_check_begin,
    self_check_end,
)
from src import raw_loader  # noqa: E402
from src.features import (  # noqa: E402
    h_cond_initials,
    h_cond_roots,
    h_el,
)

EXP = "expP8_T_pos_cross_tradition"
SEED = 42
N_BOOTSTRAP = 5000
BAND_A_LO = 15
BAND_A_HI = 100
MIN_VERSES = 2

ORAL_LITURGICAL_CORPORA = {
    "quran", "pali_dn", "pali_mn", "rigveda", "avestan_yasna",
}
NARRATIVE_OR_MIXED_CORPORA = {
    "hebrew_tanakh", "greek_nt", "iliad_greek",
}
ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
CROSS_TRADITION = [
    "quran", "hebrew_tanakh", "greek_nt", "iliad_greek",
    "pali_dn", "pali_mn", "rigveda", "avestan_yasna",
]


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _t_lang(verses: list[str]) -> float:
    """Language-agnostic T = H_cond_initials - H_el. Defined for any
    Unicode-text corpus; no morphology required."""
    return h_cond_initials(verses) - h_el(verses)


def _t_canon(verses: list[str]) -> float:
    """Arabic-only T = H_cond_roots - H_el. Requires CamelTools."""
    return h_cond_roots(verses) - h_el(verses)


def _band_of(n: int) -> str:
    if BAND_A_LO <= n <= BAND_A_HI:
        return "A"
    if n < BAND_A_LO:
        return "B_short"
    return "C_long"


def _per_unit_T(units, mode: str) -> list[dict]:
    """Compute per-unit T (T_lang or T_canon) for a list of corpus
    units. Returns list of dicts with label, n_verses, band, t."""
    rows: list[dict] = []
    for u in units:
        nv = len(u.verses)
        if nv < MIN_VERSES:
            continue
        verses = list(u.verses)
        try:
            if mode == "T_lang":
                t = _t_lang(verses)
            elif mode == "T_canon":
                t = _t_canon(verses)
            else:
                raise ValueError(f"Unknown mode: {mode}")
        except Exception as e:
            t = float("nan")
            print(f"[{EXP}]   warn: {mode} failed on {getattr(u, 'label', '?')}"
                  f" (n_v={nv}): {type(e).__name__}: {e}",
                  file=sys.stderr)
            continue
        rows.append({
            "label": getattr(u, "label", ""),
            "n_verses": nv,
            "band": _band_of(nv),
            "t": float(t),
        })
    return rows


def _pct_t_pos(rows: list[dict], scope: str) -> dict:
    """Compute %T_pos in the given scope ('all_units' or 'band_a').

    Returns: {n, n_pos, pct, mean_t, median_t}.
    """
    if scope == "band_a":
        sel = [r for r in rows if r["band"] == "A"]
    elif scope == "all_units":
        sel = list(rows)
    else:
        raise ValueError(f"Unknown scope: {scope}")
    if not sel:
        return {
            "scope": scope, "n": 0, "n_pos": 0, "pct": float("nan"),
            "mean_t": float("nan"), "median_t": float("nan"),
        }
    ts = np.array([r["t"] for r in sel], dtype=float)
    n = int((~np.isnan(ts)).sum())
    finite = ts[~np.isnan(ts)]
    if n == 0:
        return {
            "scope": scope, "n": 0, "n_pos": 0, "pct": float("nan"),
            "mean_t": float("nan"), "median_t": float("nan"),
        }
    n_pos = int((finite > 0).sum())
    pct = n_pos / n
    return {
        "scope": scope, "n": n, "n_pos": n_pos, "pct": float(pct),
        "mean_t": float(finite.mean()),
        "median_t": float(np.median(finite)),
    }


def _bootstrap_pct(rows: list[dict], scope: str, n_boot: int = N_BOOTSTRAP,
                   seed: int = SEED) -> dict:
    """Bootstrap CI on %T_pos. Resample units with replacement n_boot
    times; report median, 2.5 %, 97.5 %."""
    if scope == "band_a":
        sel = [r for r in rows if r["band"] == "A"]
    else:
        sel = list(rows)
    ts = np.array([r["t"] for r in sel if not np.isnan(r["t"])],
                  dtype=float)
    n = ts.size
    if n == 0:
        return {"median": None, "ci_lo": None, "ci_hi": None, "n_used": 0}
    rng = np.random.default_rng(seed)
    pcts = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        sample = ts[idx]
        pcts[b] = (sample > 0).mean()
    return {
        "median": float(np.median(pcts)),
        "ci_lo": float(np.percentile(pcts, 2.5)),
        "ci_hi": float(np.percentile(pcts, 97.5)),
        "n_used": int(n),
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

    print(f"[{EXP}] Loading 14 corpora "
          f"(8 cross-tradition + 6 Arabic ctrl)...")
    CORPORA = raw_loader.load_all(
        include_extras=True,
        include_cross_lang=True,
        include_cross_tradition=True,
    )

    all_corpora = CROSS_TRADITION + ARABIC_CTRL
    per_corpus_lang: dict = {}
    per_corpus_canon: dict = {}

    for name in all_corpora:
        units = CORPORA.get(name, [])
        if not units:
            print(f"[{EXP}]   {name:18s}  MISSING", file=sys.stderr)
            per_corpus_lang[name] = {"missing": True}
            continue
        rows_lang = _per_unit_T(units, mode="T_lang")
        per_corpus_lang[name] = {
            "n_units": len(rows_lang),
            "tradition_class": (
                "oral_liturgical" if name in ORAL_LITURGICAL_CORPORA
                else "narrative_or_mixed" if name in NARRATIVE_OR_MIXED_CORPORA
                else "arabic_ctrl"
            ),
            "all_units": _pct_t_pos(rows_lang, "all_units"),
            "band_a": _pct_t_pos(rows_lang, "band_a"),
            "all_units_bootstrap": _bootstrap_pct(rows_lang, "all_units"),
            "band_a_bootstrap": _bootstrap_pct(rows_lang, "band_a"),
            "rows": rows_lang,
        }
        # T_canon only for Arabic-script corpora
        if name == "quran" or name in ARABIC_CTRL:
            print(f"[{EXP}]   {name:18s}  T_canon "
                  f"(CamelTools, may be slow)...")
            try:
                rows_canon = _per_unit_T(units, mode="T_canon")
                per_corpus_canon[name] = {
                    "n_units": len(rows_canon),
                    "all_units": _pct_t_pos(rows_canon, "all_units"),
                    "band_a": _pct_t_pos(rows_canon, "band_a"),
                    "all_units_bootstrap": _bootstrap_pct(
                        rows_canon, "all_units"),
                    "band_a_bootstrap": _bootstrap_pct(
                        rows_canon, "band_a"),
                }
            except Exception as e:
                print(f"[{EXP}]   {name:18s}  T_canon failed: "
                      f"{type(e).__name__}: {e}", file=sys.stderr)
                per_corpus_canon[name] = {"failed": str(e)}

    # ---------------- Class summary ----------------
    def _pct_band_a(name: str) -> float | None:
        rec = per_corpus_lang.get(name, {})
        if rec.get("missing") or "band_a" not in rec:
            return None
        return rec["band_a"]["pct"]

    oral_pcts = [
        _pct_band_a(n) for n in CROSS_TRADITION
        if n in ORAL_LITURGICAL_CORPORA
    ]
    oral_pcts = [p for p in oral_pcts if p is not None and not np.isnan(p)]
    narr_pcts = [
        _pct_band_a(n) for n in CROSS_TRADITION
        if n in NARRATIVE_OR_MIXED_CORPORA
    ]
    narr_pcts = [p for p in narr_pcts if p is not None and not np.isnan(p)]
    ctrl_pcts = [
        _pct_band_a(n) for n in ARABIC_CTRL
    ]
    ctrl_pcts = [p for p in ctrl_pcts if p is not None and not np.isnan(p)]

    class_summary = {
        "oral_liturgical": {
            "n_corpora": len(oral_pcts),
            "median_pct": float(np.median(oral_pcts)) if oral_pcts else None,
            "max_pct": float(np.max(oral_pcts)) if oral_pcts else None,
            "min_pct": float(np.min(oral_pcts)) if oral_pcts else None,
        },
        "narrative_or_mixed": {
            "n_corpora": len(narr_pcts),
            "median_pct": float(np.median(narr_pcts)) if narr_pcts else None,
            "max_pct": float(np.max(narr_pcts)) if narr_pcts else None,
            "min_pct": float(np.min(narr_pcts)) if narr_pcts else None,
        },
        "arabic_ctrl": {
            "n_corpora": len(ctrl_pcts),
            "median_pct": float(np.median(ctrl_pcts)) if ctrl_pcts else None,
            "max_pct": float(np.max(ctrl_pcts)) if ctrl_pcts else None,
        },
    }

    # ---------------- Pre-registered verdict ----------------
    quran_pct_lang = _pct_band_a("quran")
    next_highest_non_quran = None
    next_highest_non_quran_corpus = None
    for name in CROSS_TRADITION + ARABIC_CTRL:
        if name == "quran":
            continue
        pct = _pct_band_a(name)
        if pct is None or np.isnan(pct):
            continue
        if next_highest_non_quran is None or pct > next_highest_non_quran:
            next_highest_non_quran = pct
            next_highest_non_quran_corpus = name

    quran_max_ctrl_ratio = None
    arabic_max_pct = max(ctrl_pcts) if ctrl_pcts else None
    if (quran_pct_lang is not None and arabic_max_pct is not None
            and arabic_max_pct > 0):
        quran_max_ctrl_ratio = quran_pct_lang / arabic_max_pct

    quran_unique = (
        quran_pct_lang is not None
        and not np.isnan(quran_pct_lang)
        and quran_pct_lang >= 0.10
        and (next_highest_non_quran is None
             or quran_pct_lang >= 5.0 * next_highest_non_quran)
    )

    median_oral = class_summary["oral_liturgical"]["median_pct"]
    median_narr = class_summary["narrative_or_mixed"]["median_pct"]
    oral_class_law = (
        median_oral is not None and median_narr is not None
        and median_narr > 0
        and median_oral >= 2.0 * median_narr
        and quran_pct_lang is not None
        and arabic_max_pct is not None
        and arabic_max_pct >= 0
        and (arabic_max_pct == 0
             or quran_pct_lang >= 5.0 * arabic_max_pct)
    )

    if (quran_pct_lang is None or np.isnan(quran_pct_lang)
            or quran_pct_lang < 0.10):
        if (next_highest_non_quran is not None and quran_pct_lang is not None
                and next_highest_non_quran > quran_pct_lang):
            verdict = "FAIL_QURAN_NOT_HIGHEST_AND_NO_ENRICHMENT"
        else:
            verdict = "FAIL_NO_ENRICHMENT_UNDER_T_LANG"
    elif (next_highest_non_quran is not None
          and next_highest_non_quran > quran_pct_lang):
        verdict = "FAIL_QURAN_NOT_HIGHEST"
    elif quran_unique and oral_class_law:
        verdict = "PASS_BOTH"
    elif quran_unique:
        verdict = "PASS_QURAN_UNIQUE"
    elif oral_class_law:
        verdict = "PASS_ORAL_CLASS_LAW"
    else:
        verdict = "PARTIAL_LANG_AGNOSTIC_DOWNGRADE"

    # ---------------- Sanity: T_canon Quran vs locked 39.7 % ----------------
    sanity = {
        "locked_T_canon_pct_quran_band_a": 0.397,
        "tol": 0.05,
        "observed": None,
        "within_tol": None,
    }
    if "quran" in per_corpus_canon and "band_a" in per_corpus_canon["quran"]:
        obs = per_corpus_canon["quran"]["band_a"]["pct"]
        sanity["observed"] = obs
        sanity["within_tol"] = (
            obs is not None
            and abs(obs - 0.397) <= sanity["tol"]
        )

    # ---------------- Console headline ----------------
    print(f"\n{'='*72}")
    print(f"[{EXP}] %T_pos cross-tradition headline (band_a, T_lang)")
    print(f"{'='*72}")
    print(f"   {'corpus':<18s}  {'class':<22s}  "
          f"{'n_BA':>5s}  {'%T_pos':>8s}  {'CI95_lo':>8s}  {'CI95_hi':>8s}")
    for name in CROSS_TRADITION + ARABIC_CTRL:
        rec = per_corpus_lang.get(name, {})
        if rec.get("missing"):
            print(f"   {name:<18s}  MISSING")
            continue
        ba = rec.get("band_a", {})
        bc = rec.get("band_a_bootstrap", {})
        pct = ba.get("pct")
        if pct is None or (isinstance(pct, float) and np.isnan(pct)):
            print(f"   {name:<18s}  {rec.get('tradition_class', '?'):<22s}  "
                  f"{ba.get('n', 0):>5d}  -- (no Band-A units)")
            continue
        print(f"   {name:<18s}  {rec.get('tradition_class', '?'):<22s}  "
              f"{ba['n']:>5d}  {pct*100:>7.2f}%  "
              f"{(bc.get('ci_lo') or 0)*100:>7.2f}%  "
              f"{(bc.get('ci_hi') or 0)*100:>7.2f}%")

    print(f"\n[{EXP}] Class summary (T_lang, Band-A %T_pos):")
    for cls, s in class_summary.items():
        if s["n_corpora"] == 0:
            continue
        print(f"   {cls:<22s}  median = "
              f"{(s['median_pct'] or 0)*100:6.2f}%  "
              f"max = {(s['max_pct'] or 0)*100:6.2f}%  "
              f"(n_corpora = {s['n_corpora']})")

    print(f"\n[{EXP}] Quran(Band-A) %T_lang_pos          = "
          f"{(quran_pct_lang or 0)*100:7.2f}%")
    if next_highest_non_quran is not None:
        print(f"[{EXP}] Next-highest non-Quran corpus     = "
              f"{(next_highest_non_quran)*100:7.2f}%  "
              f"({next_highest_non_quran_corpus})")
        if quran_pct_lang and next_highest_non_quran > 0:
            print(f"[{EXP}] Quran / next-highest ratio        = "
                  f"{quran_pct_lang / next_highest_non_quran:7.2f}x")
    if arabic_max_pct is not None and arabic_max_pct >= 0:
        print(f"[{EXP}] Max Arabic-ctrl %T_lang_pos       = "
              f"{arabic_max_pct*100:7.2f}%")
        if quran_max_ctrl_ratio is not None:
            print(f"[{EXP}] Quran / max-Arabic-ctrl ratio     = "
                  f"{quran_max_ctrl_ratio:7.2f}x  "
                  f"(locked T_canon ratio = 397x)")

    if sanity["observed"] is not None:
        print(f"\n[{EXP}] === T_canon sanity (Quran Band-A) ===")
        print(f"[{EXP}]   locked  %T_canon_pos = {0.397*100:6.2f}%")
        print(f"[{EXP}]   observed %T_canon_pos = "
              f"{(sanity['observed'] or 0)*100:6.2f}%")
        print(f"[{EXP}]   within tol {sanity['tol']}: "
              f"{sanity['within_tol']}")

    print(f"\n{'='*72}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    print(f"{'='*72}\n")

    elapsed = time.time() - t0

    # Strip the per-row arrays so the JSON stays compact.
    per_corpus_lang_clean = {}
    for name, rec in per_corpus_lang.items():
        rec2 = dict(rec)
        rec2.pop("rows", None)
        per_corpus_lang_clean[name] = rec2

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "prereg_document": "experiments/expP8_T_pos_cross_tradition/PREREG.md",
        "prereg_hash": _prereg_hash(),
        "frozen_constants": {
            "seed": SEED,
            "n_bootstrap": N_BOOTSTRAP,
            "band_a_lo": BAND_A_LO,
            "band_a_hi": BAND_A_HI,
            "min_verses": MIN_VERSES,
            "oral_liturgical": sorted(ORAL_LITURGICAL_CORPORA),
            "narrative_or_mixed": sorted(NARRATIVE_OR_MIXED_CORPORA),
            "arabic_ctrl": ARABIC_CTRL,
        },
        "feature_definitions": {
            "T_lang": "h_cond_initials(verses) - h_el(verses)  "
                      "(language-agnostic; src/features.py:200-235)",
            "T_canon": "h_cond_roots(verses) - h_el(verses)  "
                       "(Arabic-only via CamelTools; src/features.py:139-178)",
        },
        "per_corpus_T_lang": per_corpus_lang_clean,
        "per_corpus_T_canon": per_corpus_canon,
        "class_summary_band_a_T_lang": class_summary,
        "headline": {
            "quran_band_a_pct_T_lang": quran_pct_lang,
            "next_highest_non_quran_pct_T_lang": next_highest_non_quran,
            "next_highest_non_quran_corpus": next_highest_non_quran_corpus,
            "quran_over_next_highest_ratio": (
                quran_pct_lang / next_highest_non_quran
                if (quran_pct_lang and next_highest_non_quran
                    and next_highest_non_quran > 0)
                else None
            ),
            "max_arabic_ctrl_pct_T_lang": arabic_max_pct,
            "quran_over_max_arabic_ratio": quran_max_ctrl_ratio,
        },
        "T_canon_sanity_quran_band_a_locked_0.397": sanity,
        "pre_registered_verdict": verdict,
        "interpretation": (
            "PASS_QURAN_UNIQUE means the Quran is the unique enrichment "
            "outlier under the language-agnostic T surrogate; PASS_ORAL_"
            "CLASS_LAW means the enrichment is a class property of "
            "oral-liturgical canons (in which case Quran is the strongest "
            "instance per the 5x-Arabic-ctrl gate); PARTIAL_LANG_"
            "AGNOSTIC_DOWNGRADE means the enrichment exists but is "
            "smaller under T_lang than under T_canon; FAIL_NO_ENRICHMENT_"
            "UNDER_T_LANG means the locked 39.7 % is a CamelTools "
            "morphological-analyser artefact, not a structural property."
        ),
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=float)
    print(f"[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
