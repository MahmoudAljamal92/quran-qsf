# -*- coding: utf-8 -*-
"""
expX1_psi_oral / run.py
=======================

Computes the reviewer's proposed Ψ_oral universal across the 8-corpus
cross-tradition universe of expP4_cross_tradition_R3.

    Ψ_oral := H(diac | base) / (2 · I(EL ; CN))

Sanity gate (PSI-S1): on the Quran, this reproduces the locked
1.964 / (2 · 1.175) = 0.83574 within drift < 5e-3.

Pre-registered: see ./PREREG.md (frozen before any cross-corpus
number is consulted).

Reads:
  data/corpora/ar/quran_vocal.txt      (Quran with harakat — for the canonical
                                        T7-style H(harakat|rasm) sanity)
  + the 8 corpus loaders' vocalised/diacritised verse text
    (data/corpora/{he,el,pi,sa,ae}/...)

Writes ONLY under results/experiments/expX1_psi_oral/:
  expX1_psi_oral.json
  self_check_<ts>.json
"""
from __future__ import annotations

import math
import re
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterable

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
    ARABIC_CONN,
    DIAC as ARABIC_DIAC,  # the project's explicit harakat set used by T7
    derive_stopwords,
    el_rate,
    cn_rate,
)

EXP = "expX1_psi_oral"
SEED = 42

# Locked sanity targets (from results_lock.json + paper §3.x)
QURAN_H_HARAKAT_RASM_LOCKED = 1.964
QURAN_I_EL_CN_LOCKED = 1.175
QURAN_PSI_LOCKED = QURAN_H_HARAKAT_RASM_LOCKED / (2.0 * QURAN_I_EL_CN_LOCKED)
PSI_SANITY_TOLERANCE = 5e-3

# Pre-registered band gates
TIGHT_CENTER = 5.0 / 6.0      # 0.83333...
TIGHT_HALF_WIDTH = 0.06       # → [0.7733, 0.8933]
LOOSE_LOW = 0.65
LOOSE_HIGH = 1.00

# Band-A filter (applied only to Quran I(EL;CN) for sanity reproduction)
BAND_A_MIN_VERSES = 15
BAND_A_MAX_VERSES = 100


# --------------------------------------------------------------------------- #
# Diacritic / base detection — language-agnostic via Unicode categories       #
# --------------------------------------------------------------------------- #
def _is_combining(c: str) -> bool:
    """True if c is a combining (non-spacing or spacing-combining) mark.

    Mn = combining marks like Arabic harakat, Hebrew niqqud, Latin macron.
    Mc = spacing combining marks like Devanagari mātrās.
    """
    return unicodedata.category(c) in ("Mn", "Mc")


def _is_base(c: str) -> bool:
    """True if c is a base character we want to condition diacritics on."""
    if c.isspace():
        return False
    if _is_combining(c):
        return False
    cat = unicodedata.category(c)
    # L* (letter) and No (other number, e.g. Devanagari numerals) accepted as bases.
    return cat[0] == "L"


def _h_diac_given_base(text: str, allowed_diac: set[str] | None = None) -> dict:
    """Walk NFD-normalised text, build (base, diacs) pairs, return H(d|b).

    If `allowed_diac` is provided, ONLY code points in that set count as
    diacritics (Arabic uses the project's explicit harakat set to match the
    locked T7 computation byte-faithfully). Otherwise we use the generic
    Unicode Mn/Mc category test.

    Returns dict with H_diac_given_base, marginal H_diac, n_pairs,
    vocab_diac, vocab_base.
    """
    if allowed_diac is None:
        # Generic path: NFD-normalise so composed accented characters split.
        text = unicodedata.normalize("NFD", text)

        def _is_diac(c: str) -> bool:
            return _is_combining(c)

        def _is_pair_base(c: str) -> bool:
            return _is_base(c)
    else:
        # Curated path (Arabic): NO NFD (T7 doesn't normalise; harakat are
        # already separate code points in quran_vocal.txt). A diacritic is
        # any char in the curated set; a base is any letter NOT in the set.
        def _is_diac(c: str) -> bool:
            return c in allowed_diac

        def _is_pair_base(c: str) -> bool:
            if c in allowed_diac:
                return False
            if c.isspace():
                return False
            return c.isalpha()

    pairs: list[tuple[str, str]] = []
    chars = list(text)
    i = 0
    while i < len(chars):
        c = chars[i]
        if not _is_pair_base(c):
            i += 1
            continue
        j = i + 1
        diacs: list[str] = []
        while j < len(chars) and _is_diac(chars[j]):
            diacs.append(chars[j])
            j += 1
        if allowed_diac is None:
            # Sort to canonical order (NFD already orders by combining class
            # but multi-mark sequences sometimes have ambiguity).
            diacs_str = "".join(sorted(diacs))
        else:
            # Match T7 exactly: source-order join, no sort.
            diacs_str = "".join(diacs)
        pairs.append((c, diacs_str if diacs_str else "<none>"))
        i = j

    total = len(pairs)
    if total == 0:
        return {
            "H_diac_given_base": 0.0,
            "H_diac_marginal": 0.0,
            "n_pairs": 0,
            "vocab_diac": 0,
            "vocab_base": 0,
        }

    cnt_diac = Counter(p[1] for p in pairs)
    cnt_pair = Counter(pairs)
    cnt_base = Counter(p[0] for p in pairs)

    H_d = -sum(
        (n / total) * math.log2(n / total) for n in cnt_diac.values() if n > 0
    )

    H_d_given_b = 0.0
    for b, nb in cnt_base.items():
        pb = nb / total
        # P(diac | base = b)
        h_row = 0.0
        for (bb, d), nbd in cnt_pair.items():
            if bb != b:
                continue
            p_d_given_b = nbd / nb
            if p_d_given_b > 0:
                h_row -= p_d_given_b * math.log2(p_d_given_b)
        H_d_given_b += pb * h_row

    return {
        "H_diac_given_base": float(H_d_given_b),
        "H_diac_marginal": float(H_d),
        "n_pairs": int(total),
        "vocab_diac": int(len(cnt_diac)),
        "vocab_base": int(len(cnt_base)),
    }


# --------------------------------------------------------------------------- #
# I(EL ; CN) — discrete plug-in MI on per-unit features, 10 quantile bins     #
# --------------------------------------------------------------------------- #
def _entropy(seq: Iterable) -> float:
    c = Counter(seq)
    n = sum(c.values())
    if n == 0:
        return 0.0
    return -sum((k / n) * math.log2(k / n) for k in c.values())


def _mi(xs: list, ys: list) -> float:
    n = len(xs)
    if n == 0:
        return 0.0
    cxy = Counter(zip(xs, ys))
    cx = Counter(xs)
    cy = Counter(ys)
    mi = 0.0
    for (x, y), nxy in cxy.items():
        pxy = nxy / n
        px = cx[x] / n
        py = cy[y] / n
        if pxy > 0 and px > 0 and py > 0:
            mi += pxy * math.log2(pxy / (px * py))
    return mi


def _i_el_cn(units, stops: set[str], use_band_a: bool) -> dict:
    """Per-unit EL and CN, then I(EL;CN) on 10 quantile bins."""
    el: list[float] = []
    cn: list[float] = []
    n_total = 0
    n_used = 0
    for u in units:
        n_total += 1
        if use_band_a and not (
            BAND_A_MIN_VERSES <= len(u.verses) <= BAND_A_MAX_VERSES
        ):
            continue
        n_used += 1
        el.append(float(el_rate(u.verses)))
        cn.append(float(cn_rate(u.verses, stops)))
    if n_used < 10:
        return {
            "I_EL_CN": float("nan"),
            "n_units": n_total,
            "n_units_used": n_used,
            "skipped": True,
            "reason": f"n_used={n_used} < 10",
        }
    el_arr = np.asarray(el)
    cn_arr = np.asarray(cn)
    # 10 quantile bins (np.digitize on interior cut points, identical to T7)
    el_cuts = np.quantile(el_arr, np.linspace(0, 1, 11)[1:-1])
    cn_cuts = np.quantile(cn_arr, np.linspace(0, 1, 11)[1:-1])
    el_bin = np.digitize(el_arr, el_cuts).tolist()
    cn_bin = np.digitize(cn_arr, cn_cuts).tolist()
    return {
        "I_EL_CN": _mi(el_bin, cn_bin),
        "H_EL": _entropy(el_bin),
        "H_CN": _entropy(cn_bin),
        "n_units": n_total,
        "n_units_used": n_used,
        "EL_mean": float(el_arr.mean()),
        "CN_mean": float(cn_arr.mean()),
        "skipped": False,
    }


# --------------------------------------------------------------------------- #
# Per-corpus driver                                                           #
# --------------------------------------------------------------------------- #
def _alphabet_of(name: str) -> str:
    return {
        "quran": "arabic",
        "hebrew_tanakh": "hebrew",
        "greek_nt": "greek",
        "iliad_greek": "greek",
        "pali_dn": "latin_iast",
        "pali_mn": "latin_iast",
        "rigveda": "devanagari",
        "avestan_yasna": "latin_geldner",
    }.get(name, "unknown")


def _tradition_class_of(name: str) -> str:
    """Same labels as expP4_cross_tradition_R3."""
    if name in {"quran", "pali_dn", "pali_mn", "rigveda", "avestan_yasna"}:
        return "oral_liturgical"
    if name in {"hebrew_tanakh", "greek_nt", "iliad_greek"}:
        return "narrative_or_mixed"
    return "unknown"


_GREEK_RANGE_RE = re.compile(
    r"[\u0370-\u03FF\u1F00-\u1FFF]+"
)


def _corpus_text_for_h_diac(name: str, units) -> str:
    """Return the vocalised / diacritised text used for H(diac|base).

    Loader-derived text is byte-faithful for Arabic, Hebrew, Pali, Devanagari
    and the Avestan Geldner transliteration, but the Greek loaders
    (`load_greek_nt`, `load_iliad`) extract LEMMAs / surface tokens that
    have been diacritic-stripped. For those we read the raw source file
    and keep every Greek-block character (U+0370-U+03FF, U+1F00-U+1FFF
    plus their combining marks).
    """
    if name == "quran":
        p = _ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt"
        if p.exists():
            return p.read_text("utf-8", errors="replace")
    elif name == "greek_nt":
        p = _ROOT / "data" / "corpora" / "el" / "opengnt_v3_3.csv"
        if p.exists():
            raw = p.read_text("utf-8", errors="replace")
            # Keep Greek-script runs only; this discards CSV markup but keeps
            # all polytonic accents and combining marks attached to letters.
            return " ".join(_GREEK_RANGE_RE.findall(raw))
    elif name == "iliad_greek":
        p = _ROOT / "data" / "corpora" / "el" / "iliad_perseus.xml"
        if p.exists():
            raw = p.read_text("utf-8", errors="replace")
            return " ".join(_GREEK_RANGE_RE.findall(raw))
    elif name == "avestan_yasna":
        # Loader returns text correctly; raw HTML would just add HTML tags.
        pass
    parts: list[str] = []
    for u in units:
        parts.extend(u.verses)
    return "\n".join(parts)


def _run_corpus(name: str, units) -> dict:
    """Compute H(diac|base), I(EL;CN), and Ψ_oral for one corpus."""
    t0 = time.time()
    if not units:
        return {"name": name, "skipped": True, "reason": "no units"}

    # -- H(diac | base) on full corpus text
    text = _corpus_text_for_h_diac(name, units)
    # Arabic uses the project's explicit DIAC set (matches the T7-locked
    # 1.964 bits byte-faithfully). All other scripts use generic Mn/Mc on
    # NFD-decomposed text.
    allowed = ARABIC_DIAC if name == "quran" else None
    h_block = _h_diac_given_base(text, allowed_diac=allowed)
    h_block["diac_set"] = (
        "explicit_DIAC_from_features.py (T7 anchor)"
        if allowed is not None else "unicode_Mn_Mc_after_NFD"
    )

    # -- I(EL;CN) on per-unit features
    if name == "quran":
        stops = ARABIC_CONN
        use_band_a = True  # required to reproduce the locked 1.175 numerator
    else:
        all_v = (v for u in units for v in u.verses)
        stops = derive_stopwords(all_v, top_n=20)
        use_band_a = False

    i_block = _i_el_cn(units, stops, use_band_a=use_band_a)

    # -- Combine into Ψ_oral
    H_d_b = h_block["H_diac_given_base"]
    I_ec = i_block.get("I_EL_CN", float("nan"))
    if I_ec is None or (isinstance(I_ec, float) and (math.isnan(I_ec) or I_ec <= 0)):
        psi = float("nan")
        psi_skipped_reason = (
            "I(EL;CN) <= 0 or NaN; Ψ_oral undefined for this corpus"
        )
    else:
        psi = H_d_b / (2.0 * I_ec)
        psi_skipped_reason = None

    return {
        "name": name,
        "alphabet": _alphabet_of(name),
        "tradition_class": _tradition_class_of(name),
        "n_units_total": len(units),
        "stops_size": len(stops),
        "use_band_a_for_I": use_band_a,
        "h_diac_given_base": h_block,
        "i_el_cn": i_block,
        "psi_oral": float(psi) if not math.isnan(psi) else None,
        "psi_oral_skipped_reason": psi_skipped_reason,
        "runtime_seconds": round(time.time() - t0, 2),
    }


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #
def main() -> int:
    out_dir = safe_output_dir(EXP)
    pre = self_check_begin()

    print(f"[{EXP}] loading corpora (cross-lang + cross-tradition)...")
    CORPORA = raw_loader.load_all(
        include_extras=True,
        include_cross_lang=True,
        include_cross_tradition=True,
    )

    corpus_order = [
        "quran",
        "hebrew_tanakh",
        "greek_nt",
        "iliad_greek",
        "pali_dn",
        "pali_mn",
        "rigveda",
        "avestan_yasna",
    ]

    per_corpus: dict = {}
    for name in corpus_order:
        units = CORPORA.get(name, [])
        print(
            f"[{EXP}]   {name:18s}  n_units={len(units):4d}  ",
            end="",
            flush=True,
        )
        per_corpus[name] = _run_corpus(name, units)
        psi = per_corpus[name].get("psi_oral")
        psi_str = f"{psi:.4f}" if isinstance(psi, float) else "nan"
        print(f"  Ψ_oral = {psi_str}")

    # ------------------ pre-registered gates ------------------
    quran_psi = per_corpus["quran"].get("psi_oral")
    if isinstance(quran_psi, float):
        sanity_drift = abs(quran_psi - QURAN_PSI_LOCKED)
        psi_s1 = "PASS" if sanity_drift < PSI_SANITY_TOLERANCE else "FAIL"
    else:
        sanity_drift = float("nan")
        psi_s1 = "FAIL"

    oral_test_set = [
        "hebrew_tanakh", "greek_nt", "pali_mn", "rigveda", "avestan_yasna",
    ]
    oral_psi = {
        n: per_corpus[n].get("psi_oral") for n in oral_test_set
    }

    def _in_loose(v):
        return isinstance(v, float) and LOOSE_LOW <= v <= LOOSE_HIGH

    def _in_tight(v):
        return (
            isinstance(v, float)
            and abs(v - TIGHT_CENTER) <= TIGHT_HALF_WIDTH
        )

    n_loose = sum(1 for v in oral_psi.values() if _in_loose(v))
    n_tight = sum(1 for v in oral_psi.values() if _in_tight(v))
    psi_1 = "PASS" if n_loose >= 3 else "FAIL"
    psi_2 = "PASS" if n_tight >= 3 else "FAIL"

    iliad_psi = per_corpus["iliad_greek"].get("psi_oral")
    psi_3 = "PASS" if (isinstance(iliad_psi, float) and not _in_tight(iliad_psi)) else "FAIL"

    # Verdict tree (matches PREREG)
    if psi_s1 == "FAIL":
        verdict = "INVALID"
    elif psi_2 == "PASS" and psi_3 == "PASS":
        verdict = "SUPPORT_TIGHT"
    elif psi_1 == "PASS":
        verdict = "SUPPORT_LOOSE"
    else:
        verdict = "NO_SUPPORT"

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "seed": SEED,
        "formula": "Ψ_oral = H(diac | base) / (2 · I(EL ; CN))",
        "locked_quran_anchor": {
            "H_harakat_rasm": QURAN_H_HARAKAT_RASM_LOCKED,
            "I_EL_CN": QURAN_I_EL_CN_LOCKED,
            "psi_oral_locked": QURAN_PSI_LOCKED,
            "sanity_tolerance": PSI_SANITY_TOLERANCE,
        },
        "thresholds": {
            "tight_center": TIGHT_CENTER,
            "tight_half_width": TIGHT_HALF_WIDTH,
            "loose_band": [LOOSE_LOW, LOOSE_HIGH],
            "band_a_min_verses": BAND_A_MIN_VERSES,
            "band_a_max_verses": BAND_A_MAX_VERSES,
        },
        "corpus_order": corpus_order,
        "per_corpus": per_corpus,
        "sanity": {
            "quran_psi_measured": quran_psi,
            "quran_psi_locked": QURAN_PSI_LOCKED,
            "drift_abs": sanity_drift,
            "tolerance": PSI_SANITY_TOLERANCE,
            "PSI_S1_verdict": psi_s1,
        },
        "predictions": {
            "PSI_1_loose_band_3_of_5": {
                "verdict": psi_1,
                "n_in_band": n_loose,
                "of_n_tested": len(oral_psi),
                "band": [LOOSE_LOW, LOOSE_HIGH],
                "per_corpus_psi": oral_psi,
            },
            "PSI_2_tight_band_3_of_5": {
                "verdict": psi_2,
                "n_in_band": n_tight,
                "of_n_tested": len(oral_psi),
                "band": [
                    TIGHT_CENTER - TIGHT_HALF_WIDTH,
                    TIGHT_CENTER + TIGHT_HALF_WIDTH,
                ],
                "per_corpus_psi": oral_psi,
            },
            "PSI_3_iliad_outside_tight": {
                "verdict": psi_3,
                "iliad_psi": iliad_psi,
                "tight_band": [
                    TIGHT_CENTER - TIGHT_HALF_WIDTH,
                    TIGHT_CENTER + TIGHT_HALF_WIDTH,
                ],
            },
        },
        "verdict": verdict,
        "interpretation": (
            "PSI-S1 sanity-check Quran reproduces locked 1.964/(2·1.175)=0.83574. "
            "PSI-1 tests whether at least 3 of 5 non-Quran oral-liturgical corpora "
            "produce Ψ in [0.65, 1.00] (loose). PSI-2 tightens that to ±0.06 around "
            "5/6 ≈ 0.8333. PSI-3 is the negative control: Iliad (epic narrative, "
            "not oral-mnemonic) should sit outside the tight band. Verdict mapping "
            "is in PREREG.md §Verdict."
        ),
    }

    # Write output JSON
    out_json = out_dir / f"{EXP}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        import json as _json
        _json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] wrote {out_json.relative_to(_ROOT)}")

    # Self-check (signature: self_check_end(pre, exp_name=None))
    self_check_end(pre, EXP)

    # Pretty summary
    print()
    print(f"[{EXP}] === verdict: {verdict} ===")
    print(f"[{EXP}]   PSI-S1 sanity (drift {sanity_drift:.5f} < {PSI_SANITY_TOLERANCE}):  {psi_s1}")
    print(f"[{EXP}]   PSI-1 loose 3/5 in [{LOOSE_LOW}, {LOOSE_HIGH}]:                  {psi_1}  ({n_loose}/5)")
    print(f"[{EXP}]   PSI-2 tight 3/5 in 5/6 ± 0.06:                                   {psi_2}  ({n_tight}/5)")
    print(f"[{EXP}]   PSI-3 Iliad outside tight band:                                  {psi_3}")
    print()
    print(f"[{EXP}]   per-corpus Ψ_oral:")
    for n in corpus_order:
        psi = per_corpus[n].get("psi_oral")
        h = per_corpus[n]["h_diac_given_base"]["H_diac_given_base"]
        i_block = per_corpus[n]["i_el_cn"]
        i_val = i_block.get("I_EL_CN", float("nan"))
        i_str = f"{i_val:.4f}" if isinstance(i_val, float) and not math.isnan(i_val) else "nan"
        psi_str = f"{psi:.4f}" if isinstance(psi, float) else "  nan"
        print(
            f"[{EXP}]     {n:18s}  H(d|b)={h:.4f} bits   "
            f"I(EL;CN)={i_str} bits   Ψ={psi_str}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
