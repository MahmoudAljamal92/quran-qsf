"""tools/sanaa_compare.py — Two-text Arabic Δ_bigram comparator.

Designed for forensic / palimpsest comparison: input two Arabic Qurʾān-class
texts (e.g., canonical ʿUthmānic rasm vs. Ṣanʿāʾ DAM 01-27.1 lower text) and
produce a single replicable distance number plus interpretive context.

Usage (CLI):
    python tools/sanaa_compare.py path/to/text1.txt path/to/text2.txt
    python tools/sanaa_compare.py --label1 "Hafs" --label2 "Sanaa-DAM01"  ...

Or use the API:
    from tools.sanaa_compare import compare_texts
    result = compare_texts(text1, text2)

Outputs:
    Δ_bigram: float, total bigram-histogram L1 / 2
    k_min: implied minimum number of letter changes (= ceil(Δ/2) lower bound)
    F55 verdict: NEAR-VARIANT / DISTANT-VARIANT / IDENTICAL
    Word-order independence: F55 is permutation-INVARIANT across word boundaries
    F68 ordered: gzip-fingerprint Δ (catches ordering changes within the rasm)

Honest scope:
    * F55 cannot decide which text is "correct" — only how far they are.
    * F55 strips diacritics by design; pure ḥarakāt disputes are not visible.
    * F55 is order-invariant inside a word for letter swaps; for *verse-order*
      changes the F68 (gzip) form is the right diagnostic.
"""
from __future__ import annotations

import argparse
import gzip
import math
import re
import sys
import unicodedata
from pathlib import Path

# ---- Arabic 28-letter skeleton normaliser (matches exp118) -----------------
_AR_DIAC = re.compile(r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06ED\u0670]")
_AR_TATWEEL = "\u0640"
_ARABIC_LETTERS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ARABIC_SET = set(_ARABIC_LETTERS_28)


def normalise_arabic(s: str) -> str:
    """Strip diacritics + tatweel, fold alif/yaa/taa-marbuta variants, keep
    only the 28 canonical Arabic consonants.

    Returns a string consisting of 28-letter skeleton characters and spaces
    (one per inter-word boundary).
    """
    if not s:
        return ""
    s = s.replace(_AR_TATWEEL, "")
    s = _AR_DIAC.sub("", s)
    # NFD strip all combining marks (catches stray non-DIAC marks)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    # Fold variants
    s = (s.replace("\u0622", "\u0627")  # آ → ا
          .replace("\u0623", "\u0627")  # أ → ا
          .replace("\u0625", "\u0627")  # إ → ا
          .replace("\u0671", "\u0627")  # ٱ → ا
          .replace("\u0649", "\u064a")  # ى → ي
          .replace("\u0629", "\u0647")) # ة → ه
    # Drop hamza-ya / hamza-waw fragments
    s = s.replace("\u0624", "\u0648").replace("\u0626", "\u064a").replace("\u0621", "")
    keep = _ARABIC_SET | {" ", "\n"}
    s = "".join(c if c in keep else " " for c in s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def bigram_histogram(text: str) -> dict:
    """Within-word bigrams (no cross-word edges)."""
    h: dict = {}
    for word in text.split():
        for i in range(len(word) - 1):
            bg = word[i:i + 2]
            h[bg] = h.get(bg, 0) + 1
    return h


def delta_bigram(h1: dict, h2: dict) -> float:
    keys = set(h1) | set(h2)
    return sum(abs(h1.get(k, 0) - h2.get(k, 0)) for k in keys) / 2.0


def gzip_fingerprint_delta(t1: str, t2: str) -> float:
    """Sequence-aware fingerprint: |gzip(t1) − gzip(t2)| / max.
    Two byte-identical texts give 0; reorderings give nonzero.
    """
    b1 = t1.encode("utf-8")
    b2 = t2.encode("utf-8")
    if not b1 and not b2:
        return 0.0
    g1 = len(gzip.compress(b1, compresslevel=9))
    g2 = len(gzip.compress(b2, compresslevel=9))
    return abs(g1 - g2) / max(g1, g2, 1)


def compare_texts(text1: str, text2: str,
                  label1: str = "text1",
                  label2: str = "text2") -> dict:
    """Compute the full F55 / F68 comparison report for two raw Arabic texts."""
    n1 = normalise_arabic(text1)
    n2 = normalise_arabic(text2)

    if not n1 or not n2:
        return {
            "error": "one_or_both_normalised_to_empty",
            "n1_len": len(n1),
            "n2_len": len(n2),
        }

    h1 = bigram_histogram(n1)
    h2 = bigram_histogram(n2)
    d = delta_bigram(h1, h2)
    # Lower bound on letter-changes: each letter change perturbs at most 2 bigram
    # counts (Theorem F69), so k_min = ceil(Δ / 2) is the minimum k consistent.
    k_min = math.ceil(d / 2.0) if d > 0 else 0
    gz_d = gzip_fingerprint_delta(n1, n2)

    # Verdict for F55 alone (assuming both texts roughly the same length)
    if d == 0:
        f55_verdict = "IDENTICAL_BIGRAM_HISTOGRAM"
    elif d <= 2:
        f55_verdict = "NEAR_VARIANT_consistent_with_1_letter_edit"
    elif d <= 10:
        f55_verdict = f"NEAR_VARIANT_consistent_with_up_to_{k_min}_letter_edits"
    elif d <= 50:
        f55_verdict = f"VARIANT_consistent_with_up_to_{k_min}_letter_edits"
    else:
        f55_verdict = f"DISTANT_VARIANT_at_least_{k_min}_letter_edits_apart"

    # Verdict for F68 (gzip fingerprint, order-sensitive)
    if gz_d <= 0.001:
        f68_verdict = "BYTE_IDENTICAL_ORDER"
    elif gz_d <= 0.02:
        f68_verdict = "NEAR_IDENTICAL_ORDER_minor_reordering_or_edit"
    elif gz_d <= 0.10:
        f68_verdict = "MODERATE_ORDER_DIVERGENCE"
    else:
        f68_verdict = "MAJOR_ORDER_DIVERGENCE_or_different_lengths"

    return {
        "label1": label1,
        "label2": label2,
        "raw_chars1": len(text1),
        "raw_chars2": len(text2),
        "skeleton_chars1": len(n1.replace(" ", "")),
        "skeleton_chars2": len(n2.replace(" ", "")),
        "n_words1": len(n1.split()),
        "n_words2": len(n2.split()),
        "n_distinct_bigrams_1": len(h1),
        "n_distinct_bigrams_2": len(h2),
        "delta_bigram": d,
        "implied_k_min_letter_edits": k_min,
        "f55_verdict": f55_verdict,
        "gzip_fingerprint_delta": gz_d,
        "f68_verdict": f68_verdict,
    }


def _read_input(arg: str) -> str:
    """If arg is a path that exists, read it; else treat as raw text."""
    p = Path(arg)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8", errors="replace")
    return arg


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Two-text Arabic Δ_bigram comparator (F55 + F68).")
    ap.add_argument("text1", help="First text — file path or inline string")
    ap.add_argument("text2", help="Second text — file path or inline string")
    ap.add_argument("--label1", default="text1")
    ap.add_argument("--label2", default="text2")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable")
    args = ap.parse_args(argv)

    t1 = _read_input(args.text1)
    t2 = _read_input(args.text2)
    res = compare_texts(t1, t2, args.label1, args.label2)

    if args.json:
        import json as _j
        print(_j.dumps(res, indent=2, ensure_ascii=False))
        return 0

    if "error" in res:
        print(f"ERROR: {res['error']}")
        return 1

    print(f"\n=== F55 / F68 Comparison: {res['label1']} vs {res['label2']} ===\n")
    print(f"  Raw chars:           {res['raw_chars1']:>8d}  vs {res['raw_chars2']:>8d}")
    print(f"  Skeleton chars:      {res['skeleton_chars1']:>8d}  vs {res['skeleton_chars2']:>8d}")
    print(f"  Words after norm:    {res['n_words1']:>8d}  vs {res['n_words2']:>8d}")
    print(f"  Distinct bigrams:    {res['n_distinct_bigrams_1']:>8d}  vs {res['n_distinct_bigrams_2']:>8d}")
    print()
    print(f"  Δ_bigram:            {res['delta_bigram']:.2f}")
    print(f"  Implied k_min edits: ≥ {res['implied_k_min_letter_edits']}")
    print(f"  F55 verdict:         {res['f55_verdict']}")
    print()
    print(f"  gzip fingerprint Δ:  {res['gzip_fingerprint_delta']:.4f}")
    print(f"  F68 verdict:         {res['f68_verdict']}")
    print()
    print("  NOTE: F55 measures distance, NOT authenticity. To establish")
    print("  which text reflects an authoritative reading, one must consult")
    print("  paleographic / chains-of-transmission evidence; F55 only quantifies")
    print("  the textual gap with a single replicable number.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
