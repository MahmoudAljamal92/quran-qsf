"""normalize.py — Arabic 28-letter skeleton normaliser.

Drops diacritics, hamza marks, ta-marbuta, alif variants — the same
"rasm-skeleton" normalisation used across every locked experiment.

This is intentional: the canonical Quran has multiple valid readings
(Hafs, Warsh, Qalun, ...) that differ only in those marks. The
mathematical fingerprint operates on the rasm-skeleton because that
is the part shared by all canonical readings.

This file is the single source of truth for "what counts as an
Arabic letter" inside the app. Used by both Layer A (corpus lookup)
and Layer B (axis computation).
"""
from __future__ import annotations

import re
import unicodedata

from .constants import ARABIC_28

# ----- Unicode classes we strip ---------------------------------------------
_AR_DIAC = re.compile(r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06ED\u0670]")
_AR_TATWEEL = "\u0640"
_ARABIC_SET = set(ARABIC_28)

# Alif / ya / ta-marbuta / hamza-bearer foldings (canonical rasm).
_FOLD_MAP = {
    "\u0622": "\u0627",     # آ -> ا
    "\u0623": "\u0627",     # أ -> ا
    "\u0625": "\u0627",     # إ -> ا
    "\u0671": "\u0627",     # ٱ -> ا
    "\u0649": "\u064a",     # ى -> ي
    "\u0629": "\u0647",     # ة -> ه
    "\u0624": "\u0648",     # ؤ -> و
    "\u0626": "\u064a",     # ئ -> ي
    "\u0621": "",           # standalone ء -> drop
}


def normalize_arabic(s: str, keep_spaces: bool = True) -> str:
    """28-letter skeleton normaliser.

    Args:
        s: raw Arabic text (any unicode form).
        keep_spaces: if True, preserve word boundaries; if False, collapse to
                     pure letter stream.

    Returns:
        A string containing ONLY characters from ARABIC_28 (and optional spaces).
    """
    if not s:
        return ""
    s = s.replace(_AR_TATWEEL, "")
    s = _AR_DIAC.sub("", s)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    for src, dst in _FOLD_MAP.items():
        s = s.replace(src, dst)
    keep = _ARABIC_SET | ({" ", "\n"} if keep_spaces else set())
    s = "".join(c if c in keep else (" " if keep_spaces else "") for c in s)
    if keep_spaces:
        s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_arabic_letters_only(s: str) -> str:
    """Return only the 28 Arabic letters; no spaces, no anything else."""
    return normalize_arabic(s, keep_spaces=False)


def split_into_verses(raw: str) -> list[str]:
    """Heuristic verse splitter.

    Order of precedence:
      1. lines of the form `surah|verse|text` (canonical Hafs format)
      2. pipe-separated verses
      3. one verse per non-empty line

    Returns a list of verse strings (still raw; not normalised).
    """
    raw = raw.strip()
    if not raw:
        return []

    # Format 1 — canonical Quran corpus pipe-format
    canonical_lines = []
    for line in raw.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
            canonical_lines.append(parts[2].strip())
    if canonical_lines and len(canonical_lines) >= max(2, 0.5 * len(raw.splitlines())):
        return canonical_lines

    # Format 2 — single line(s) with pipe separators between verses
    if "|" in raw and "\n" not in raw.strip():
        parts = [p.strip() for p in raw.split("|") if p.strip()]
        if len(parts) >= 2:
            return parts

    # Format 3 — one verse per line
    parts = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    return parts


def detect_script(s: str) -> str:
    """Return a coarse script tag for the input text.

    Returns one of:
      'ar'    Arabic
      'he'    Hebrew
      'el'    Greek
      'sa'    Devanagari
      'latin' Latin (likely IAST/transliteration; treated as Pali/Avestan)
      'mixed' multiple scripts roughly equal
      'empty' nothing usable
    """
    if not s:
        return "empty"
    counts = {"ar": 0, "he": 0, "el": 0, "sa": 0, "latin": 0}
    for c in s:
        cp = ord(c)
        if 0x0600 <= cp <= 0x06FF:
            counts["ar"] += 1
        elif 0x0590 <= cp <= 0x05FF:
            counts["he"] += 1
        elif 0x0370 <= cp <= 0x03FF or 0x1F00 <= cp <= 0x1FFF:
            counts["el"] += 1
        elif 0x0900 <= cp <= 0x097F:
            counts["sa"] += 1
        elif (0x0041 <= cp <= 0x005A) or (0x0061 <= cp <= 0x007A):
            counts["latin"] += 1
    total = sum(counts.values())
    if total == 0:
        return "empty"
    sorted_counts = sorted(counts.items(), key=lambda kv: -kv[1])
    top, second = sorted_counts[0], sorted_counts[1]
    if top[1] / total < 0.6:
        return "mixed"
    return top[0]


__all__ = [
    "normalize_arabic", "normalize_arabic_letters_only",
    "split_into_verses", "detect_script",
]
