"""
exp95e_full_114_consensus_universal/_enumerate.py
=================================================
Variant enumeration for the four pre-registered scopes.

Each generator yields tuples of the form
    (surah_label, canonical_letters_28, variant_letters_28, meta)
where `meta` is a small dict carrying provenance:
    {"surah": "Q:001", "verse_idx": 0, "char_pos_in_canon": 17,
     "orig": "ب", "repl": "و", "scope": "v1"}

Every variant is a single-consonant substitution. The canonical and variant
letter strings are produced by `letters_28(...)` from `run.py` so the
enumerator output can be fed straight into the NCD primitives without any
further normalisation.

This module is byte-equal to exp95c's enumeration on the V1 scope when the
input is Q:100 (verified by the regression sub-run in `run.py`).
"""
from __future__ import annotations

import random
from typing import Callable, Iterator

# The 28-consonant Arabic alphabet, in the order the project has used since
# exp41. Every variant generated here substitutes one consonant with one of
# the OTHER 27 consonants from this set.
ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"

# Diacritics + tashkīl that get stripped to produce the letter-only canonical
# form before NCD computation.
DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)

# Hamza-bearing variants and tāʾ marbūṭa fold into base consonants for the
# 28-letter representation. ʾalif maqṣūra → yāʾ.
_FOLD = {
    "ء": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "ا", "ئ": "ا",
    "ة": "ه",
    "ى": "ي",
}

_ALPH_IDX = {c: i for i, c in enumerate(ARABIC_CONS_28)}


def strip_diacritics(s: str) -> str:
    """Remove all Arabic diacritics from a string."""
    return "".join(c for c in str(s) if c not in DIAC)


def letters_28(text: str) -> str:
    """Project a string onto the 28-consonant Arabic alphabet.

    Drops diacritics, folds hamza-bearing variants and final tāʾ marbūṭa,
    and discards every other character (whitespace, punctuation, digits).

    Byte-equal to exp95c's `_letters_28` (verified by regression).
    """
    out: list[str] = []
    for c in strip_diacritics(text):
        if c in _FOLD:
            out.append(_FOLD[c])
        elif c in _ALPH_IDX:
            out.append(c)
    return "".join(out)


# ---------------------------------------------------------------------------
# Per-surah enumerators
# ---------------------------------------------------------------------------
def enumerate_v1(canon_verses: list[str]) -> list[dict]:
    """V1 scope: enumerate all single-consonant substitutions in the FIRST
    verse only, all 27 substitutes per consonant position.

    The canonical text passed to the NCD is `letters_28(" ".join(canon_verses))`,
    i.e. the full surah; the variant differs from canonical only at the
    substituted position in v1.

    Returns a list of variant specs:
        {"verse_idx": 0, "char_pos_in_v1": <int>,
         "orig": <consonant>, "repl": <consonant>,
         "v1_variant": <new v1 string>}
    """
    if not canon_verses:
        return []
    v1 = canon_verses[0]
    out: list[dict] = []
    # Walk the original v1 string (with diacritics intact) and for every
    # consonant position, generate 27 substituted variants. We substitute on
    # the un-folded character if it is in ARABIC_CONS_28; hamza-bearing
    # forms fold to ا anyway, so they are not separately substituted.
    for pos, ch in enumerate(v1):
        if ch not in ARABIC_CONS_28:
            continue
        for repl in ARABIC_CONS_28:
            if repl == ch:
                continue
            new_v1 = v1[:pos] + repl + v1[pos + 1:]
            out.append({
                "verse_idx": 0,
                "char_pos_in_v1": pos,
                "orig": ch,
                "repl": repl,
                "v1_variant": new_v1,
            })
    return out


def enumerate_short(canon_verses: list[str], max_verses: int = 3) -> list[dict]:
    """SHORT scope: enumerate all single-consonant substitutions in the first
    `max_verses` verses, all 27 substitutes per consonant position.

    Each variant is anchored at (verse_idx, char_pos_in_verse). The variant
    string for that verse is held in `verse_variant`; the rest of the surah
    is left intact.
    """
    out: list[dict] = []
    for vi in range(min(len(canon_verses), max_verses)):
        verse = canon_verses[vi]
        for pos, ch in enumerate(verse):
            if ch not in ARABIC_CONS_28:
                continue
            for repl in ARABIC_CONS_28:
                if repl == ch:
                    continue
                new_verse = verse[:pos] + repl + verse[pos + 1:]
                out.append({
                    "verse_idx": vi,
                    "char_pos_in_verse": pos,
                    "orig": ch,
                    "repl": repl,
                    "verse_variant": new_verse,
                })
    return out


def enumerate_full(canon_verses: list[str]) -> list[dict]:
    """FULL scope: enumerate every single-consonant substitution that the
    exp94 perturbation rule would touch — interior verses, interior words
    (with ≥ 3 alpha chars), interior letter positions — at all 27 substitutes.

    The exp94 rule has been the standing perturbation rule for ctrl-null
    calibration since exp43; here we apply its eligibility predicate
    deterministically (rather than randomly) to enumerate every reachable
    variant.

    Surahs with fewer than 5 verses produce ZERO FULL variants (they fail
    the ``nv >= 5`` guard, byte-equal to exp94's `_apply_perturbation`).
    Those surahs are reported as `n_variants: 0` in the receipt and are
    NOT counted toward the per-surah floor (since the rule itself has no
    eligible position to flag).
    """
    nv = len(canon_verses)
    if nv < 5:
        return []
    out: list[dict] = []
    for vi in range(1, nv - 1):
        verse_stripped = strip_diacritics(canon_verses[vi])
        toks = verse_stripped.split()
        if len(toks) < 3:
            continue
        for wi in range(1, len(toks) - 1):
            w = toks[wi]
            alpha_positions = [i for i, c in enumerate(w) if c.isalpha()]
            if len(alpha_positions) < 3:
                continue
            interior = alpha_positions[1:-1]
            for pos_in_word in interior:
                ch = w[pos_in_word]
                if ch not in ARABIC_CONS_28:
                    continue
                for repl in ARABIC_CONS_28:
                    if repl == ch:
                        continue
                    new_w = w[:pos_in_word] + repl + w[pos_in_word + 1:]
                    new_toks = list(toks)
                    new_toks[wi] = new_w
                    new_verse = " ".join(new_toks)
                    out.append({
                        "verse_idx": vi,
                        "word_idx": wi,
                        "char_pos_in_word": pos_in_word,
                        "orig": ch,
                        "repl": repl,
                        "verse_variant": new_verse,
                    })
    return out


def enumerate_sample(
    canon_verses: list[str], rate: float = 0.10, seed: int = 42
) -> list[dict]:
    """SAMPLE scope (and the building block for QUARTER / HALF):
    uniform `rate`-fraction random sample of FULL.

    Identical seed → identical sample, so the run is reproducible.
    """
    full = enumerate_full(canon_verses)
    if not full:
        return []
    rng = random.Random(seed)
    rng.shuffle(full)
    n_keep = max(1, int(round(len(full) * rate)))
    return full[:n_keep]


def enumerate_quarter(canon_verses: list[str]) -> list[dict]:
    """QUARTER scope: uniform 25 % random sample of FULL (seed=42).
    Approx ~925 K variants total across the 114 surahs (~5–8 h on 8 cores)."""
    return enumerate_sample(canon_verses, rate=0.25, seed=42)


def enumerate_half(canon_verses: list[str]) -> list[dict]:
    """HALF scope: uniform 50 % random sample of FULL (seed=42).
    Approx ~1.85 M variants (~10–18 h on 8 cores). Pre-registered as a
    diagnostic scope; verdict is computed against V1 only."""
    return enumerate_sample(canon_verses, rate=0.50, seed=42)


# ---------------------------------------------------------------------------
# Materialise (canonical_letters_28, variant_letters_28) pairs
# ---------------------------------------------------------------------------
def materialise(
    surah_label: str,
    canon_verses: list[str],
    variant_specs: list[dict],
    scope: str,
) -> Iterator[tuple[str, str, str, dict]]:
    """Yield ``(surah_label, canonical_letters_28, variant_letters_28, meta)``
    tuples for every variant spec.

    For V1 scope, `variant_letters_28` is computed once per variant by
    substituting v1 in the surah and re-projecting the whole surah onto the
    28-letter alphabet.

    For SHORT / FULL / SAMPLE scopes, the substitution is at (vi, pos), and
    the variant is built by replacing only that verse and re-projecting.
    """
    canon_text = " ".join(canon_verses)
    canon_letters = letters_28(canon_text)
    for spec in variant_specs:
        if scope == "v1":
            new_v1 = spec["v1_variant"]
            var_verses = [new_v1] + list(canon_verses[1:])
        else:  # short, full, sample
            vi = spec["verse_idx"]
            new_verse = spec["verse_variant"]
            var_verses = list(canon_verses)
            var_verses[vi] = new_verse
        var_text = " ".join(var_verses)
        var_letters = letters_28(var_text)
        meta = {"surah": surah_label, "scope": scope, **spec}
        # Drop the bulky variant string from meta (already encoded in
        # var_letters); keep only the spec metadata.
        meta.pop("v1_variant", None)
        meta.pop("verse_variant", None)
        yield surah_label, canon_letters, var_letters, meta


# ---------------------------------------------------------------------------
# Scope dispatcher
# ---------------------------------------------------------------------------
SCOPE_ENUMERATORS: dict[str, Callable[[list[str]], list[dict]]] = {
    "v1":      enumerate_v1,
    "short":   lambda verses: enumerate_short(verses, max_verses=3),
    "sample":  lambda verses: enumerate_sample(verses, rate=0.10, seed=42),
    "quarter": enumerate_quarter,
    "half":    enumerate_half,
    "full":    enumerate_full,
}


def enumerate_for_scope(scope: str, canon_verses: list[str]) -> list[dict]:
    """Dispatch to the per-scope generator. Raises KeyError on unknown scope."""
    if scope not in SCOPE_ENUMERATORS:
        raise KeyError(
            f"Unknown scope {scope!r}. Available: {sorted(SCOPE_ENUMERATORS.keys())}"
        )
    return SCOPE_ENUMERATORS[scope](canon_verses)
