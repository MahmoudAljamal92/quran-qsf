"""
expP4_diacritic_capacity_cross_tradition/run.py
================================================
Cross-TRADITION extension of `expA2_diacritic_capacity_universal`.

Adds three pre/non-Abrahamic religious orthographies to the original
3-corpus diacritic-channel capacity test:

    Existing (expA2, locked):
        Quran (Arabic harakat over rasm)
        Tanakh (Hebrew niqqud over consonant)
        NT (Greek combining marks over vowel)

    New (this experiment, P4):
        Rigveda Saṃhitā  (Devanagari mātrās + svaras over consonant)
        Pāli Tipiṭaka    (Latin-IAST combining marks, NFD-decomposed)
        Avestan Yasna    (Latin-Geldner combining marks, NFD-decomposed)

Reuses the entropy helpers from expA2 byte-for-byte; the 3-corpus subset
must reproduce the locked A2 values to ≤ 1e-6 (sanity check).

Reads only:
    data/corpora/ar/quran_vocal.txt
    data/corpora/he/tanakh_wlc.txt
    data/corpora/el/opengnt_v3_3.csv
    data/corpora/sa/rigveda_mandala_*.json     (via loader)
    data/corpora/pi/{dn,mn}/*_root-pli-ms.json (via loader)
    data/corpora/ae/y*.htm                     (via loader)

Writes ONLY under results/experiments/expP4_diacritic_capacity_cross_tradition/.
"""
from __future__ import annotations

import json
import math
import sys
import unicodedata
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    safe_output_dir,
    self_check_begin,
    self_check_end,
)

# Reuse expA2's helpers + Arabic/Hebrew/Greek pair extractors verbatim
from experiments.expA2_diacritic_capacity_universal.run import (  # noqa: E402
    _conditional_entropy_bits,
    quran_pairs,
    hebrew_pairs,
    greek_pairs,
)

from src import raw_loader  # noqa: E402

EXP = "expP4_diacritic_capacity_cross_tradition"
PRE_REG_BAND_LO = 0.55
PRE_REG_BAND_HI = 0.75
PRE_REG_MAX_SPREAD_6 = 0.30   # PRED-A2-EXT-2: 6-corpus spread ≤ 0.30


# ---------------------------------------------------------------------------
# Devanagari (Vedic) pair extractor
# ---------------------------------------------------------------------------
# The Devanagari diacritic channel:
#   Base letter (rasm-like): consonant U+0915..U+0939 (ka..ha) +
#                            independent vowel U+0905..U+0914
#   Diacritic (harakat-like): vowel sign U+093E..U+094C, virama U+094D,
#                             nukta U+093C, anusvāra U+0902, visarga U+0903,
#                             Vedic accents U+0951..U+0954 (udātta, anudātta,
#                             svarita, dīrgha-svarita).
# Note: independent vowels carry their own anusvāra/visarga/svaras too, so
# they DO participate in the diacritic-channel; we treat them as base letters.
def _is_devanagari_base(c: str) -> bool:
    cp = ord(c)
    if 0x0905 <= cp <= 0x0914:   # independent vowels
        return True
    if 0x0915 <= cp <= 0x0939:   # consonants
        return True
    return False


def _is_devanagari_diacritic(c: str) -> bool:
    cp = ord(c)
    if 0x093C == cp:              # nukta
        return True
    if 0x093E <= cp <= 0x094D:    # vowel signs + virama
        return True
    if 0x0951 <= cp <= 0x0954:    # Vedic accents
        return True
    if cp == 0x0902 or cp == 0x0903:  # anusvāra, visarga
        return True
    return False


def vedic_pairs() -> Counter:
    """Walk the Rigveda Saṃhitā joined-verse text and collect
    (devanagari-base, mātrā/svara/anusvara/visarga-string) pairs."""
    units = raw_loader.load_vedic()
    text = "\n".join(v for u in units for v in u.verses)
    pairs: Counter = Counter()
    chars = list(text)
    i = 0
    n = len(chars)
    while i < n:
        c = chars[i]
        if _is_devanagari_diacritic(c) or c.isspace() or not c.isalpha():
            i += 1
            continue
        if not _is_devanagari_base(c):
            i += 1
            continue
        j = i + 1
        diacs: list[str] = []
        while j < n and _is_devanagari_diacritic(chars[j]):
            diacs.append(chars[j])
            j += 1
        pairs[(c, "".join(diacs) or "<none>")] += 1
        i = j
    return pairs


# ---------------------------------------------------------------------------
# Latin-script (Pāli, Avestan) pair extractor — NFD-decomposed
# ---------------------------------------------------------------------------
# After NFD, Pāli "ā" -> "a" + U+0304 (combining macron), etc.
# Avestan precomposed ə (U+0259) and ŋ (U+014B) do NOT decompose; treat as
# their own base letters with no diacritic.
# We want to compare to the Greek convention which uses (vowel, accent).
# Choice: treat all Latin a-z (case-folded) AS base letters, and combining
# marks (Mn category) as diacritics. This is the most permissive Latin
# analogue and parallels Greek's vowel+accent treatment but with a larger
# base alphabet (consonants included).
def _latin_iast_pairs(text: str) -> Counter:
    pairs: Counter = Counter()
    nfd = unicodedata.normalize("NFD", text)
    chars = list(nfd)
    i = 0
    n = len(chars)
    while i < n:
        c = chars[i]
        # Skip non-letter, non-Mn characters (punctuation, digits, etc.)
        cat = unicodedata.category(c)
        if cat == "Mn":
            i += 1
            continue
        if not c.isalpha():
            i += 1
            continue
        # Case-fold so 'A' and 'a' are the same base letter
        base = c.lower()
        # We use Latin-script letters: a-z plus precomposed special letters
        # like 'ə' (U+0259) and 'ŋ' (U+014B). These are still .isalpha() and
        # cat == 'Ll' / 'Lo' so they pass the filter.
        # We DON'T restrict to a-z; the corpus's own script is the alphabet.
        j = i + 1
        diacs: list[str] = []
        while j < n and unicodedata.category(chars[j]) == "Mn":
            diacs.append(chars[j])
            j += 1
        pairs[(base, "".join(diacs) or "<none>")] += 1
        i = j
    return pairs


def pali_pairs() -> Counter:
    units = raw_loader.load_pali()
    text = "\n".join(v for u in units for v in u.verses)
    return _latin_iast_pairs(text)


def avestan_pairs() -> Counter:
    units = raw_loader.load_avestan()
    text = "\n".join(v for u in units for v in u.verses)
    return _latin_iast_pairs(text)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    paths = {
        "quran_arabic":  _ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt",
        "tanakh_hebrew": _ROOT / "data" / "corpora" / "he" / "tanakh_wlc.txt",
        "nt_greek":      _ROOT / "data" / "corpora" / "el" / "opengnt_v3_3.csv",
    }
    for k, p in paths.items():
        if not p.exists():
            raise FileNotFoundError(f"Missing data file for {k}: {p}")

    print(f"[{EXP}] computing capacity for 6 corpora...")

    # ----- 3 locked Abrahamic corpora (must reproduce locked A2) -----
    print(f"[{EXP}]   Arabic   Quran (Hafs vocalised)")
    arabic = _conditional_entropy_bits(quran_pairs(paths["quran_arabic"]))
    arabic["base_letter_alphabet"] = "Arabic rasm (U+0621-U+064A)"
    arabic["diacritic_alphabet"] = "Arabic harakat (U+064B-U+065F + Quranic annotations)"

    print(f"[{EXP}]   Hebrew   WLC Tanakh (cantillation stripped)")
    hebrew = _conditional_entropy_bits(hebrew_pairs(paths["tanakh_hebrew"]))
    hebrew["base_letter_alphabet"] = "Hebrew consonants (U+05D0-U+05EA)"
    hebrew["diacritic_alphabet"] = "Hebrew niqqud (U+05B0-U+05BC,U+05BF,U+05C1-U+05C2,U+05C7)"

    print(f"[{EXP}]   Greek    OpenGNT v3.3 polytonic")
    greek = _conditional_entropy_bits(greek_pairs(paths["nt_greek"]))
    greek["base_letter_alphabet"] = "Greek vowels α/ε/η/ι/ο/υ/ω (case-folded)"
    greek["diacritic_alphabet"] = "Greek combining marks (Unicode Mn category, NFD)"

    # ----- 3 NEW cross-tradition corpora -----
    print(f"[{EXP}]   Devanagari Rigveda Saṃhitā (consonants+matras+svaras)")
    vedic = _conditional_entropy_bits(vedic_pairs())
    vedic["base_letter_alphabet"] = ("Devanagari consonants U+0915-U+0939 + "
                                     "independent vowels U+0905-U+0914")
    vedic["diacritic_alphabet"] = ("Devanagari nukta + matras + virama + "
                                   "Vedic accents + anusvara + visarga "
                                   "(U+093C, U+093E-U+094D, U+0951-U+0954, "
                                   "U+0902-U+0903)")

    print(f"[{EXP}]   Latin-IAST Pāli (DN+MN, NFD-decomposed)")
    pali = _conditional_entropy_bits(pali_pairs())
    pali["base_letter_alphabet"] = "Latin a-z + IAST precomposed letters (case-folded)"
    pali["diacritic_alphabet"] = "Combining marks Mn (NFD-decomposed: macron, dot, tilde, ring, etc.)"

    print(f"[{EXP}]   Latin-Geldner Avestan Yasna (NFD-decomposed)")
    avestan = _conditional_entropy_bits(avestan_pairs())
    avestan["base_letter_alphabet"] = "Latin a-z + Avestan precomposed (ə, ŋ, others)"
    avestan["diacritic_alphabet"] = "Combining marks Mn (NFD-decomposed)"

    # ----- Universal-band verdict (6-corpus, both denominator conventions) -----
    def _verdict_for(label: str, results: dict) -> dict:
        names = list(results.keys())
        rs = [results[n][f"ratio_R_{label}"] for n in names]
        in_band = [PRE_REG_BAND_LO <= r <= PRE_REG_BAND_HI for r in rs]
        R_min, R_max = min(rs), max(rs)
        spread = R_max - R_min
        return {
            "denominator_convention": label,
            "R_per_corpus": dict(zip(names, [float(r) for r in rs])),
            "in_band_per_corpus": dict(zip(names, in_band)),
            "n_in_band": int(sum(in_band)),
            "n_total": len(rs),
            "R_min": float(R_min),
            "R_max": float(R_max),
            "spread": float(spread),
            "passes_PRED_A2_EXT_1": (
                "PASS" if any(in_band[3:]) else "FAIL"
            ),  # at least one NEW corpus (Vedic, Pali, Avestan) in band
            "passes_PRED_A2_EXT_2": (
                "PASS" if spread <= PRE_REG_MAX_SPREAD_6 else "FAIL"
            ),  # 6-corpus spread ≤ 0.30
        }

    all6 = {
        "quran_arabic":  arabic,
        "tanakh_hebrew": hebrew,
        "nt_greek":      greek,
        "rigveda_devanagari": vedic,
        "pali_iast":         pali,
        "avestan_geldner":   avestan,
    }
    verdict_combo = _verdict_for("combinations", all6)
    verdict_prim = _verdict_for("primitives", all6)

    # PRED-A2-EXT-3: Vedic primitives R is the LOWEST or near-lowest
    prim_rs = sorted(
        verdict_prim["R_per_corpus"].items(), key=lambda kv: kv[1]
    )
    vedic_rank_low = next(
        (i for i, (k, _) in enumerate(prim_rs) if k == "rigveda_devanagari"),
        None,
    )
    pred_ext_3 = (
        "PASS" if vedic_rank_low is not None and vedic_rank_low <= 1
        else "FAIL"
    )

    # ---- Sanity: 3-Abrahamic-subset reproduces locked A2 ----
    locked_path = (_ROOT / "results" / "experiments"
                   / "expA2_diacritic_capacity_universal"
                   / "expA2_diacritic_capacity_universal.json")
    locked_drift = None
    if locked_path.exists():
        try:
            locked = json.loads(locked_path.read_text("utf-8"))
            for conv in ("combinations", "primitives"):
                key = f"ratio_R_{conv}"
                drift_arabic = abs(
                    locked["results"]["quran_arabic"][key] - arabic[key]
                )
                drift_hebrew = abs(
                    locked["results"]["tanakh_hebrew"][key] - hebrew[key]
                )
                drift_greek = abs(
                    locked["results"]["nt_greek"][key] - greek[key]
                )
                if locked_drift is None:
                    locked_drift = {}
                locked_drift[conv] = {
                    "drift_arabic": float(drift_arabic),
                    "drift_hebrew": float(drift_hebrew),
                    "drift_greek": float(drift_greek),
                    "max_drift": float(max(drift_arabic, drift_hebrew, drift_greek)),
                    "ok": bool(max(drift_arabic, drift_hebrew, drift_greek) < 1e-6),
                }
        except (json.JSONDecodeError, OSError, KeyError) as e:
            locked_drift = {"error": str(e)}

    # Overall verdict
    pred_1_combo = verdict_combo["passes_PRED_A2_EXT_1"]
    pred_1_prim  = verdict_prim["passes_PRED_A2_EXT_1"]
    pred_2_combo = verdict_combo["passes_PRED_A2_EXT_2"]
    pred_2_prim  = verdict_prim["passes_PRED_A2_EXT_2"]
    overall = (
        "STRONG_SUPPORT" if (pred_1_prim == "PASS" and pred_2_prim == "PASS"
                             and pred_ext_3 == "PASS")
        else "PARTIAL_SUPPORT" if (pred_1_prim == "PASS" or pred_2_prim == "PASS")
        else "NO_SUPPORT"
    )

    report = {
        "experiment": EXP,
        "task_id": "P4 / A2 cross-tradition extension",
        "schema_version": 1,
        "title": ("Diacritic-channel capacity ratio across 6 religious "
                  "orthographies: Arabic + Hebrew + Greek + Devanagari "
                  "(Vedic) + Latin-IAST (Pāli) + Latin-Geldner (Avestan)."),
        "pre_reg": {
            "band_lo": PRE_REG_BAND_LO,
            "band_hi": PRE_REG_BAND_HI,
            "max_spread_6": PRE_REG_MAX_SPREAD_6,
            "PRED_A2_EXT_1": "≥1 of 3 new corpora primitives R ∈ [0.55, 0.75]",
            "PRED_A2_EXT_2": "6-corpus primitives spread ≤ 0.30",
            "PRED_A2_EXT_3": "Vedic primitives R is lowest or 2nd-lowest of 6",
        },
        "results_per_corpus": {
            "quran_arabic":       arabic,
            "tanakh_hebrew":      hebrew,
            "nt_greek":           greek,
            "rigveda_devanagari": vedic,
            "pali_iast":          pali,
            "avestan_geldner":    avestan,
        },
        "universal_band_combinations": verdict_combo,
        "universal_band_primitives":   verdict_prim,
        "pre_registered_outcomes": {
            "PRED_A2_EXT_1_combinations": pred_1_combo,
            "PRED_A2_EXT_1_primitives":   pred_1_prim,
            "PRED_A2_EXT_2_combinations": pred_2_combo,
            "PRED_A2_EXT_2_primitives":   pred_2_prim,
            "PRED_A2_EXT_3_vedic_low_primitives": pred_ext_3,
            "vedic_primitives_rank_from_low": vedic_rank_low,
            "overall_verdict": overall,
        },
        "sanity_check_3_corpus_subset_reproduces_locked_A2": locked_drift,
        "extends": {
            "experiment": "expA2_diacritic_capacity_universal",
            "relationship": ("strict superset: 3 locked corpora + 3 new ones; "
                             "the 3-corpus subset must reproduce the locked "
                             "A2 R values to within 1e-6."),
        },
        "provenance": {
            "data_sources": {
                "rigveda_devanagari": "github.com/bhavykhatri/DharmicData",
                "pali_iast":          "github.com/suttacentral/bilara-data",
                "avestan_geldner":    "avesta.org/yasna/ (Geldner 1896)",
            },
        },
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ---------------- console summary ----------------
    print()
    print(f"[{EXP}] -- per-corpus R --")
    print(f"   {'corpus':<22s}  {'n_pairs':>8s}  {'|base|':>7s}  "
          f"{'|combo|':>8s}  {'|prim|':>7s}  {'H(d|c)':>7s}  "
          f"{'R_combo':>8s}  {'R_prim':>8s}")
    for name, r in all6.items():
        print(f"   {name:<22s}  "
              f"{r.get('n_pairs', 0):>8d}  "
              f"{r.get('n_distinct_base_letters', 0):>7d}  "
              f"{r.get('n_distinct_diacritic_strings', 0):>8d}  "
              f"{r.get('n_distinct_primitive_diacritics', 0):>7d}  "
              f"{r.get('H_diacritic_given_base_bits', 0):>7.4f}  "
              f"{r.get('ratio_R_combinations', 0):>8.4f}  "
              f"{r.get('ratio_R_primitives', 0):>8.4f}")
    print()
    print(f"[{EXP}] -- COMBINATIONS convention (6-corpus) --")
    print(f"[{EXP}]   spread = {verdict_combo['spread']:.4f}  "
          f"in_band = {verdict_combo['n_in_band']}/{verdict_combo['n_total']}  "
          f"PRED-EXT-1 = {pred_1_combo}  PRED-EXT-2 = {pred_2_combo}")
    print(f"[{EXP}] -- PRIMITIVES convention (6-corpus) --")
    print(f"[{EXP}]   spread = {verdict_prim['spread']:.4f}  "
          f"in_band = {verdict_prim['n_in_band']}/{verdict_prim['n_total']}  "
          f"PRED-EXT-1 = {pred_1_prim}  PRED-EXT-2 = {pred_2_prim}")
    print(f"[{EXP}]   PRED-EXT-3 (Vedic R_prim is lowest/2nd-lowest): "
          f"{pred_ext_3}  (rank = {vedic_rank_low})")
    print(f"[{EXP}] OVERALL verdict: {overall}")
    if locked_drift and "primitives" in locked_drift:
        ok = locked_drift["primitives"]["ok"]
        print(f"[{EXP}] sanity (locked-A2 subset reproduction): "
              f"{'OK' if ok else 'DRIFT'} "
              f"(max drift = {locked_drift['primitives']['max_drift']:.2e})")
    print(f"[{EXP}] wrote {outfile}")

    self_check_end(pre, exp_name=EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
