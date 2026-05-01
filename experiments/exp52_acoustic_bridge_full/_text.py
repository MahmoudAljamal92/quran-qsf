"""
exp52 text utilities.

Loads the Uthmani corpus, computes per-verse text features (syllable, madd,
emphatic, ghunnah), and normalises text for CTC forced alignment against the
jonatasgrosman/wav2vec2-large-xlsr-53-arabic tokenizer (vocab = 51 tokens).

Maintains a back_index: clean_position i -> original Uthmani position j so
per-character CTC timestamps can be reported in the original vocalised text.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

# --- Uthmani / Arabic codepoint sets (all single chars) ---
SHORT_VOWELS = set("\u064E\u064F\u0650")            # fatha, damma, kasra
TANWEEN      = set("\u064B\u064C\u064D")            # fathatain, dammatain, kasratain
SHADDA       = "\u0651"
SUKUN        = "\u0652"
MADD_MARKS   = set("\u0670\u0653")                  # small alif, madda above
PAUSE_MARKS  = set(chr(c) for c in range(0x06D6, 0x06DD))  # waqf marks
QURAN_EXTRAS = set(chr(c) for c in range(0x06DF, 0x06E9)) | \
               set(chr(c) for c in range(0x06EA, 0x06EE))  # various recitation marks
HAMZA_EXTRA  = set("\u0654\u0655\u0656")            # hamza above / below / open

# Chars not in the xlsr-53-arabic vocab. We STRIP pause marks, rasm extras,
# and hamza-placement marks — they don't correspond to their own sound.
# MADD_MARKS are NOT stripped — see below.
CTC_OOV = (PAUSE_MARKS | QURAN_EXTRAS | HAMZA_EXTRA)

# Alif wasla (U+0671) -> plain alif (U+0627) for CTC.
# Superscript alif (ٰ, U+0670) and madd-above (ٓ, U+0653) -> plain alif (ا).
# This is CRUCIAL: these marks represent the sustained long-ā vowel sound.
# If we stripped them (as OOV), the madd audio would be absorbed into CTC
# blanks and never attributed to a letter. By remapping to 'ا' (which IS in
# the vocab), the long vowel gets its own aligned timestamp -> H4 is testable.
ALIF_WASLA       = "\u0671"
PLAIN_ALIF       = "\u0627"
SMALL_ALIF       = "\u0670"
MADD_ABOVE       = "\u0653"
# The letter tatweel (ـ, U+0640) is purely typographic; strip it.
TATWEEL          = "\u0640"

# Emphatic consonants (ص ض ط ظ ق) — relevant for H6 and exp47 cross-reference
EMPHATIC = set("\u0635\u0636\u0637\u0638\u0642")           # ص ض ط ظ ق (strict set)
EMPHATIC_FULL = EMPHATIC | set("\u062E\u063A")            # + خ غ (classical isti`lā')

# Nasal letters for ghunnah (ن م)
NASAL = set("\u0646\u0645")

# Long-vowel letters for natural madd detection: alif / waw / ya.
# In Uthmani Qur'anic text, natural madd happens when:
#   alif (ا) preceded by fatha
#   waw  (و) preceded by damma
#   ya   (ي) preceded by kasra
# These aren't marked with ٰ or ٓ in the text — they're implicit.
ALIF = "\u0627"
WAW  = "\u0648"
YA   = "\u064A"
FATHA = "\u064E"
DAMMA = "\u064F"
KASRA = "\u0650"

# Diacritic-strip regex for word counting
_DIAC_RE = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u0671\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]')


# -------------------------------------------------------------------------
# Corpus loader
# -------------------------------------------------------------------------
def load_quran_vocal(path: str | Path) -> Dict[int, List[Tuple[int, str]]]:
    """
    Parse quran_vocal.txt (pipe-separated: surah|verse|text_uthmani).
    Returns {surah_num: [(verse_num, text), ...]}.
    """
    out: Dict[int, List[Tuple[int, str]]] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if len(parts) < 3:
                continue
            try:
                s = int(parts[0])
                v = int(parts[1])
            except ValueError:
                continue
            text = "|".join(parts[2:]).strip()
            out.setdefault(s, []).append((v, text))
    for s in out:
        out[s].sort(key=lambda x: x[0])
    return out


# -------------------------------------------------------------------------
# Text features (per verse, computed on the ORIGINAL Uthmani string)
# -------------------------------------------------------------------------
def count_syllables(text: str) -> int:
    """
    NARROW (original, replicates archived V_Acoustic_02):
        max(1, n_short_vowels + n_madd_marks).
    Does NOT count tanween. Keep for replication compatibility.
    """
    n_short = sum(1 for c in text if c in SHORT_VOWELS)
    n_madd  = sum(1 for c in text if c in MADD_MARKS)
    return max(1, n_short + n_madd)


def count_syllables_full(text: str) -> int:
    """
    FULL phonological definition:
        max(1, short_vowels + tanween + madd_marks).
    Tanween (ًٌٍ) represents a CV-n coda = a full syllable ('un'/'an'/'in').
    """
    n_short   = sum(1 for c in text if c in SHORT_VOWELS)
    n_tanween = sum(1 for c in text if c in TANWEEN)
    n_madd    = sum(1 for c in text if c in MADD_MARKS)
    return max(1, n_short + n_tanween + n_madd)


def count_madd(text: str) -> int:
    """
    NARROW (original, replicates archived V_Acoustic_02):
    only explicit madd marks (small-alif ٰ + madda-above ٓ).
    """
    return sum(1 for c in text if c in MADD_MARKS)


def count_madd_full(text: str) -> int:
    """
    FULL tajweed definition: explicit-marked madd + natural madd
    (alif after fatha, waw after damma, ya after kasra).
    """
    n_explicit = sum(1 for c in text if c in MADD_MARKS)
    n_natural = 0
    for i in range(1, len(text)):
        prev = text[i - 1]; cur = text[i]
        if (cur == ALIF and prev == FATHA) or \
           (cur == WAW  and prev == DAMMA) or \
           (cur == YA   and prev == KASRA):
            n_natural += 1
    return n_explicit + n_natural


def count_words(text: str) -> int:
    bare = _DIAC_RE.sub("", text)
    return len(bare.split())


def count_emphatic(text: str) -> int:
    """STRICT set: ص ض ط ظ ق only."""
    return sum(1 for c in text if c in EMPHATIC)


def count_emphatic_full(text: str) -> int:
    """FULL isti`lā' set: ص ض ط ظ ق + خ غ."""
    return sum(1 for c in text if c in EMPHATIC_FULL)


def count_ghunnah(text: str) -> int:
    """
    Approximation: tanween + (ن|م) followed by shadda.
    Does NOT include bare-nun idgham cases.
    """
    n_tanween = sum(1 for c in text if c in TANWEEN)
    n_nasal_shadda = sum(1 for i in range(len(text) - 1)
                         if text[i] in NASAL and text[i + 1] == SHADDA)
    return n_tanween + n_nasal_shadda


def text_features(text: str) -> Dict[str, int]:
    """
    Per-verse feature dict. Contains both NARROW (original, for replication)
    and FULL (phonologically correct) variants of syllable/madd/emphatic so
    downstream correlation analysis can compare.
    """
    return {
        "char_count":          len(text),
        "word_count":          count_words(text),
        "syllable_count":      count_syllables(text),       # narrow (replication)
        "syllable_count_full": count_syllables_full(text),  # adds tanween
        "madd_count":          count_madd(text),            # narrow (explicit marks)
        "madd_count_full":     count_madd_full(text),       # adds natural madds
        "emphatic_count":      count_emphatic(text),        # strict set
        "emphatic_count_full": count_emphatic_full(text),   # full isti`lā' set
        "ghunnah_count":       count_ghunnah(text),
    }


# -------------------------------------------------------------------------
# CTC normalisation (strip OOV chars, keep reverse index)
# -------------------------------------------------------------------------
def normalize_for_ctc(text: str) -> Tuple[str, List[int]]:
    """
    Normalise Uthmani text for the xlsr-53-arabic tokenizer (vocab = 51 tokens).

      * ٱ (alif wasla)        -> ا  (same pronunciation, in vocab)
      * ٰ (superscript alif)  -> ا  (long ā, gets its own CTC timestamp)
      * ٓ (madd above)        -> ا  (prolongation, long ā)
      * ـ (tatweel)           : stripped (typographic only)
      * pause / rasm marks    : stripped (not sound-bearing)
      * hamza position marks  : stripped (written metadata)
      * multiple spaces       : collapsed

    Returns (clean_text, back_index) where back_index[i] is the ORIGINAL
    Uthmani position of the i-th char of clean_text. Remapped chars keep the
    index of their source Uthmani char (so the letter csv can still show
    the original ٰ or ٓ in uthmani_char).
    """
    clean: List[str] = []
    back: List[int]  = []
    prev_space = False
    for i, c in enumerate(text):
        if c in CTC_OOV or c == TATWEEL:
            continue
        # Remappings: keep the ORIGINAL index (we want to know the char was a
        # madd marker when we post-process).
        if c == ALIF_WASLA:
            c = PLAIN_ALIF
        elif c == SMALL_ALIF:
            c = PLAIN_ALIF
        elif c == MADD_ABOVE:
            c = PLAIN_ALIF
        if c == " ":
            if prev_space:
                continue
            prev_space = True
        else:
            prev_space = False
        clean.append(c)
        back.append(i)
    return "".join(clean).strip(), back


# -------------------------------------------------------------------------
# Preamble strings (fixed for all Minshawi Murattal surahs)
# -------------------------------------------------------------------------
TAAWUDH  = "\u0623\u064E\u0639\u064F\u0648\u0630\u064F \u0628\u0650\u0627\u0644\u0644\u0651\u064E\u0647\u0650 \u0645\u0650\u0646\u064E \u0627\u0644\u0634\u0651\u064E\u064A\u0652\u0637\u064E\u0627\u0646\u0650 \u0627\u0644\u0631\u0651\u064E\u062C\u0650\u064A\u0645\u0650"
BASMALAH = "\u0628\u0650\u0633\u0652\u0645\u0650 \u0627\u0644\u0644\u0651\u064E\u0647\u0650 \u0627\u0644\u0631\u0651\u064E\u062D\u0652\u0645\u064E\u0627\u0646\u0650 \u0627\u0644\u0631\u0651\u064E\u062D\u0650\u064A\u0645\u0650"


def build_alignment_target(surah_num: int, verses: List[Tuple[int, str]]
                           ) -> List[Tuple[int, str]]:
    """
    Prepend taawudh as a pseudo-verse (verse_no = -1) so the CTC aligner can
    handle the leading taawudh audio. The pseudo-verse is filtered out of
    analysis later.

    IMPORTANT: quran_vocal.txt (Tanzil Uthmani) embeds the basmalah inside verse
    1 of every surah EXCEPT 1 (where basmalah IS verse 1) and 9 (no basmalah).
    So we must NOT add another basmalah pseudo-verse — that would duplicate
    text in the CTC target and shift verse-1 timings by one basmalah's worth of
    characters. See experiments/exp52_acoustic_bridge_full/_audit.py::C_bug1.

    Convention:
      surah 1  : no preamble. Minshawi's recording starts basmalah at ~2.7 s;
                 the leading silence is implicitly absorbed by CTC.
      surah 9  : taawudh only. Verse 1 has no basmalah in corpus or audio.
      others   : taawudh only. Corpus v1 already contains the basmalah.
    """
    if surah_num == 1:
        return list(verses)
    return [(-1, TAAWUDH)] + list(verses)
