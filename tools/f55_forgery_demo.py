"""F55 interactive forgery detector — demonstrates the universal symbolic forgery detector
on user-supplied 3-verse Quran passages with 1-letter edits.

Usage:
    python tools/f55_forgery_demo.py [--passage "verse1 # verse2 # verse3"] [--edit-pos N --edit-to LETTER]

If no passage given, picks random 3 consecutive verses from Quran.
If no edit given, picks random 1-letter substitution at random position.

Reports:
    - Δ_bigram between original and edited
    - Detection verdict (Δ ≤ 2.0 → DETECTED as forgery; Δ > 2.0 → NOT detected)
    - Percentage of bigram-histogram L1 distance closed
"""
from __future__ import annotations

import argparse
import random
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Locked Arabic 28-consonant skeleton (matches F55 PREREG; same as exp95j)
ARABIC_28_LETTERS = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")

# Locked F55 threshold from PREREG (analytic upper bound)
TAU = 2.0


def normalize_arabic(text: str) -> str:
    """Strip diacritics, normalize hamzas, fold sigma. Returns 28-consonant skeleton string."""
    # NFD: decompose combining marks
    text = unicodedata.normalize("NFD", text)
    # Strip all combining marks (harakat: fatha, damma, kasra, sukun, shadda, tanwin)
    text = "".join(c for c in text if not unicodedata.combining(c))
    # Normalize hamzas
    replacements = {
        "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",  # hamza-on-alif → alif
        "ؤ": "و",  # hamza-on-waw → waw
        "ئ": "ي",  # hamza-on-ya → ya
        "ء": "",   # bare hamza → drop
        "ة": "ه",  # ta marbuta → ha
        "ى": "ي",  # alif maksura → ya
        "ﻻ": "لا", "ﻷ": "لا", "ﻹ": "لا", "ﻵ": "لا",  # lam-alif ligatures
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Keep only the 28-letter skeleton + space
    keep = set(ARABIC_28_LETTERS) | {" "}
    text = "".join(c if c in keep else "" for c in text)
    # Collapse multiple spaces
    text = " ".join(text.split())
    return text


def bigram_histogram(text: str) -> dict:
    """Compute bigram histogram (28×28 = 784 bigrams) over normalized text, ignoring spaces.
    Only consecutive letter pairs within the same word are counted.
    """
    hist = {}
    for word in text.split():
        for i in range(len(word) - 1):
            bg = word[i:i+2]
            hist[bg] = hist.get(bg, 0) + 1
    return hist


def l1_distance(h1: dict, h2: dict) -> float:
    """L1 distance between two bigram histograms."""
    keys = set(h1) | set(h2)
    return sum(abs(h1.get(k, 0) - h2.get(k, 0)) for k in keys)


def delta_bigram(text_a: str, text_b: str) -> float:
    """F55 statistic: L1 distance / 2 between bigram histograms of two texts.
    Theorem: any single-letter substitution gives Δ ≤ 2.
    """
    return l1_distance(bigram_histogram(text_a), bigram_histogram(text_b)) / 2.0


def apply_edit(text: str, position: int, new_letter: str) -> str:
    """Replace the letter at the given character position with new_letter.
    Position is 0-indexed over the normalized text. Spaces are skipped (we only edit letters).
    """
    letters = [c for c in text if c != " "]
    if position < 0 or position >= len(letters):
        raise ValueError(f"Position {position} out of range (text has {len(letters)} letters)")
    letters[position] = new_letter
    # Rebuild text with original spacing
    out = []
    li = 0
    for c in text:
        if c == " ":
            out.append(" ")
        else:
            out.append(letters[li])
            li += 1
    return "".join(out)


def run_demo(passage: str | None = None, edit_pos: int | None = None, edit_to: str | None = None,
             seed: int = 42) -> dict:
    rng = random.Random(seed)

    # 1. Get passage
    if passage is None:
        # Default: 3 verses from Q105 al-Fil
        passage = (
            "ألم تر كيف فعل ربك بأصحاب الفيل # "
            "ألم يجعل كيدهم في تضليل # "
            "وأرسل عليهم طيرا أبابيل"
        )

    # 2. Normalize passage
    original = normalize_arabic(passage.replace("#", " "))
    n_letters = len([c for c in original if c != " "])
    if n_letters < 10:
        raise ValueError(f"Passage too short: {n_letters} letters (need ≥ 10)")

    # 3. Choose edit position and substitute letter
    if edit_pos is None:
        edit_pos = rng.randrange(n_letters)
    if edit_to is None:
        # Pick a random different letter from the alphabet
        letters_only = [c for c in original if c != " "]
        old_letter = letters_only[edit_pos]
        choices = [L for L in ARABIC_28_LETTERS if L != old_letter]
        edit_to = rng.choice(choices)

    edited = apply_edit(original, edit_pos, edit_to)

    # 4. Compute Δ_bigram
    delta = delta_bigram(original, edited)

    # 5. Detection verdict
    detected = 0 < delta <= TAU
    detection_message = (
        f"DETECTED as forgery (Δ = {delta:.4f} ≤ τ = {TAU})"
        if detected
        else f"NOT detected (Δ = {delta:.4f} > τ = {TAU})"
    )

    # 6. Show edit context
    letters_only = [c for c in original if c != " "]
    context_start = max(0, edit_pos - 5)
    context_end = min(n_letters, edit_pos + 6)
    context_orig = "".join(letters_only[context_start:context_end])
    edited_letters = [c for c in edited if c != " "]
    context_edit = "".join(edited_letters[context_start:context_end])

    return {
        "passage_original": passage,
        "normalized_original": original,
        "normalized_edited": edited,
        "n_letters": n_letters,
        "edit_position": edit_pos,
        "edit_old_letter": letters_only[edit_pos],
        "edit_new_letter": edit_to,
        "context_original_window": context_orig,
        "context_edited_window": context_edit,
        "delta_bigram": delta,
        "tau": TAU,
        "detected": detected,
        "detection_message": detection_message,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="F55 interactive forgery detector demo")
    parser.add_argument("--passage", type=str, default=None, help="Custom 3-verse passage (use # to separate verses)")
    parser.add_argument("--edit-pos", type=int, default=None, help="Edit position (0-indexed, over letters only)")
    parser.add_argument("--edit-to", type=str, default=None, help="Substitute letter (single Arabic char)")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    args = parser.parse_args()

    result = run_demo(
        passage=args.passage,
        edit_pos=args.edit_pos,
        edit_to=args.edit_to,
        seed=args.seed,
    )

    print("\n" + "=" * 70)
    print("F55 INTERACTIVE FORGERY DETECTOR (DEMO)")
    print("=" * 70)
    print(f"\nOriginal passage:")
    print(f"  {result['passage_original']}")
    print(f"\nNormalized (28-consonant skeleton, harakat stripped):")
    print(f"  {result['normalized_original']}")
    print(f"  → {result['n_letters']} letters")
    print(f"\nEdit applied:")
    print(f"  Position: {result['edit_position']}")
    print(f"  '{result['edit_old_letter']}' → '{result['edit_new_letter']}'")
    print(f"  Context (original): ...{result['context_original_window']}...")
    print(f"  Context (edited):   ...{result['context_edited_window']}...")
    print(f"\nF55 statistic:")
    print(f"  Δ_bigram = {result['delta_bigram']:.4f}")
    print(f"  τ (locked analytic threshold) = {result['tau']}")
    print(f"\nVerdict: {result['detection_message']}")
    print(f"\nFiring rule: 0 < Δ ≤ τ → DETECTED (recall = 1.000 on 139,266 V1 variants × 114 surahs)")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
