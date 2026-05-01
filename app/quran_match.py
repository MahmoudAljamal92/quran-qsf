"""quran_match.py — verbatim and fuzzy locator against the canonical Uthmani corpus.

Pipeline used by the unified Ring-of-Truth app:

    1. verbatim_locate(text)
         exact normalised-substring search against the full Quran.
         O(N) time. Returns the surah/verse range if found, else None.

    2. fuzzy_locate(text)
         finds the closest passage in the Quran when the input is *almost*
         Quranic (e.g. 1-letter changed, a word misspelled, a verse re-ordered).
         Two stages:
            (a) trigram-Jaccard prefilter over verse-windows
            (b) pure-Python Levenshtein over the top candidates
         Returns the closest passage, edit distance, character-level diff, and a
         deviation percentage = edit_distance / len(input).

Both functions operate on the canonical locked Arabic normaliser
(`_normalise_arabic` from `scripts/_phi_universal_xtrad_sizing.py`) so results
are byte-comparable to the rest of the project's findings.

The verse table is loaded once and cached at module level.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

# Reuse the canonical locked Arabic normaliser used everywhere else in the project.
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._phi_universal_xtrad_sizing import _normalise_arabic  # noqa: E402

QURAN_TXT = ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"


# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Verse:
    surah: int
    verse: int
    raw: str          # original (unnormalised) verse text
    norm: str         # normalised (letter-only) verse text


@lru_cache(maxsize=1)
def load_quran() -> tuple[list[Verse], str, list[int]]:
    """Load the canonical Quran corpus once.

    Returns
    -------
    verses : list[Verse]
        All 6,236 verses with raw + normalised text.
    flat_norm : str
        Concatenation of every normalised verse (no separators) — used for
        verbatim substring search across verse boundaries.
    verse_starts : list[int]
        Cumulative character offsets of each verse's start in `flat_norm`.
        verse_starts[i] = start offset of verses[i] in flat_norm.
        Final entry = total length.
    """
    verses: list[Verse] = []
    if not QURAN_TXT.exists():
        return verses, "", [0]

    for line in QURAN_TXT.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        try:
            s, v = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        raw = parts[2]
        norm = _normalise_arabic(raw)
        verses.append(Verse(surah=s, verse=v, raw=raw, norm=norm))

    flat_norm_parts = []
    verse_starts = [0]
    for v in verses:
        flat_norm_parts.append(v.norm)
        verse_starts.append(verse_starts[-1] + len(v.norm))
    flat_norm = "".join(flat_norm_parts)
    return verses, flat_norm, verse_starts


def normalise(text: str) -> str:
    """Canonical Arabic letter-only normalisation."""
    return _normalise_arabic(text)


# ----------------------------------------------------------------------
# Verbatim substring locator
# ----------------------------------------------------------------------

@dataclass
class VerbatimHit:
    surah_start: int
    verse_start: int
    surah_end: int
    verse_end: int
    char_offset: int
    n_verses_spanned: int


def _verse_index_at(offset: int, verse_starts: list[int]) -> int:
    """Binary-search the verse index whose normalised text contains `offset`."""
    lo, hi = 0, len(verse_starts) - 2
    while lo <= hi:
        mid = (lo + hi) // 2
        if verse_starts[mid] <= offset < verse_starts[mid + 1]:
            return mid
        if offset < verse_starts[mid]:
            hi = mid - 1
        else:
            lo = mid + 1
    return max(0, min(len(verse_starts) - 2, lo))


def verbatim_locate(text: str) -> Optional[VerbatimHit]:
    """Return location if the normalised input is an exact substring of the Quran.

    Matches across verse boundaries. Returns None if no exact match found.
    Empty / very short inputs (< 3 letters) are rejected to avoid trivial hits.
    """
    verses, flat_norm, verse_starts = load_quran()
    qry = normalise(text)
    if len(qry) < 3 or not flat_norm:
        return None
    pos = flat_norm.find(qry)
    if pos < 0:
        return None
    end = pos + len(qry) - 1
    i_start = _verse_index_at(pos, verse_starts)
    i_end = _verse_index_at(end, verse_starts)
    return VerbatimHit(
        surah_start=verses[i_start].surah,
        verse_start=verses[i_start].verse,
        surah_end=verses[i_end].surah,
        verse_end=verses[i_end].verse,
        char_offset=pos,
        n_verses_spanned=i_end - i_start + 1,
    )


# ----------------------------------------------------------------------
# Pure-Python Levenshtein with backtrace for diff
# ----------------------------------------------------------------------

def levenshtein(a: str, b: str) -> int:
    """Standard O(n*m) Levenshtein edit distance. Returns the integer distance."""
    if a == b:
        return 0
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n
    prev = list(range(m + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * m
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur[j] = min(prev[j] + 1,        # deletion
                         cur[j - 1] + 1,     # insertion
                         prev[j - 1] + cost) # substitution
        prev = cur
    return prev[m]


def levenshtein_with_ops(a: str, b: str) -> tuple[int, list[tuple[str, str, str]]]:
    """Edit distance + alignment ops. Returns (distance, ops).

    Each op is (kind, char_a, char_b) where kind in {"=", "sub", "ins", "del"}.
    Used to render a side-by-side character diff for the UI.
    """
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        ai = a[i - 1]
        for j in range(1, m + 1):
            cost = 0 if ai == b[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1,
                           dp[i][j - 1] + 1,
                           dp[i - 1][j - 1] + cost)
    # Backtrace
    ops: list[tuple[str, str, str]] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and a[i - 1] == b[j - 1]:
            ops.append(("=", a[i - 1], b[j - 1])); i -= 1; j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            ops.append(("sub", a[i - 1], b[j - 1])); i -= 1; j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            ops.append(("del", a[i - 1], "")); i -= 1
        else:
            ops.append(("ins", "", b[j - 1])); j -= 1
    ops.reverse()
    return dp[n][m], ops


# ----------------------------------------------------------------------
# Fuzzy locator (trigram prefilter + Levenshtein on top candidates)
# ----------------------------------------------------------------------

@dataclass
class FuzzyHit:
    surah_start: int
    verse_start: int
    surah_end: int
    verse_end: int
    candidate_norm: str       # normalised canonical passage
    candidate_raw: str        # raw canonical passage (with diacritics)
    edit_distance: int
    deviation_pct: float      # edit_distance / max(len(input), len(candidate))
    ops: list[tuple[str, str, str]]   # alignment ops (input vs canonical)
    n_verses_spanned: int


def _kgram_anchor_offsets(qry: str, flat_norm: str, *, k: int = 5,
                          max_anchors: int = 400) -> list[int]:
    """Find candidate alignment offsets in `flat_norm` for `qry`.

    Strategy: for every distinct k-gram of qry, find every occurrence in
    flat_norm; each occurrence at position p with k-gram starting at qry[i:i+k]
    suggests an alignment offset of (p - i) in flat_norm. Robust to single
    or few edits, because most k-grams of qry remain intact in the canonical
    text near the true match position.

    Returns at most `max_anchors` candidate offsets (deduplicated, clipped to
    valid range).
    """
    if len(qry) < k:
        # Treat the whole qry as the anchor
        anchors = []
        idx = 0
        while len(anchors) < max_anchors:
            p = flat_norm.find(qry, idx)
            if p < 0:
                break
            anchors.append(p)
            idx = p + 1
        return anchors

    seen_offsets: set[int] = set()
    seen_kgrams: set[str] = set()
    for i in range(len(qry) - k + 1):
        kg = qry[i:i + k]
        if kg in seen_kgrams:
            continue
        seen_kgrams.add(kg)
        idx = 0
        while True:
            p = flat_norm.find(kg, idx)
            if p < 0:
                break
            anchor = p - i
            if 0 <= anchor < len(flat_norm):
                seen_offsets.add(anchor)
            idx = p + 1
            if len(seen_offsets) >= max_anchors:
                break
        if len(seen_offsets) >= max_anchors:
            break
    return sorted(seen_offsets)


def _verse_index_range_for(start_off: int, end_off: int,
                           verse_starts: list[int]) -> tuple[int, int]:
    """Return inclusive (verse_idx_start, verse_idx_end) covering byte range."""
    i_start = _verse_index_at(start_off, verse_starts)
    i_end = _verse_index_at(max(start_off, end_off - 1), verse_starts)
    return i_start, i_end


def fuzzy_locate(text: str, *, max_anchors: int = 400) -> Optional[FuzzyHit]:
    """Find the closest Quranic passage to `text`.

    Strategy
    --------
    1. Build candidate alignment offsets via k-gram anchor scan over the
       flat normalised corpus. Robust to single-letter and few-letter edits.
    2. For each candidate offset, extract a window of size len(qry) (with a
       small +/- margin) around the offset and compute Levenshtein.
    3. Return the candidate with the smallest edit distance, along with
       alignment ops for diff rendering.

    Returns None if input is empty or shorter than 3 normalised letters, or if
    the corpus is unavailable.
    """
    verses, flat_norm, verse_starts = load_quran()
    if not verses or not flat_norm:
        return None
    qry = normalise(text)
    L = len(qry)
    if L < 3:
        return None

    # Adaptive k-gram size: shorter for tiny inputs, longer for big inputs
    # (keeps anchor count manageable).
    if L < 8:
        k = 3
    elif L < 30:
        k = 4
    elif L < 100:
        k = 5
    else:
        k = 6

    anchors = _kgram_anchor_offsets(qry, flat_norm, k=k, max_anchors=max_anchors)
    if not anchors:
        return None

    # Margin allowed in window length to absorb insertions/deletions
    margin = max(2, L // 10)

    # Scan: keep the best edit-distance window. Skip near-duplicate offsets
    # (within margin) to save time.
    best_d = None
    best_off = None
    best_win_len = None
    last_kept_off = -10**9
    for off in anchors:
        if off - last_kept_off < max(1, margin // 2):
            continue
        last_kept_off = off
        # Try window lengths from L-margin to L+margin
        for win_len in (L, L - margin, L + margin):
            start = max(0, off)
            end = min(len(flat_norm), start + win_len)
            if end - start < 3:
                continue
            cand = flat_norm[start:end]
            # Cheap upper bound: if the trivial Hamming-style char-set diff
            # is already >> best, skip Levenshtein.
            if best_d is not None and abs(len(cand) - L) > best_d:
                continue
            d = levenshtein(qry, cand)
            if best_d is None or d < best_d:
                best_d = d
                best_off = start
                best_win_len = end - start
                if d == 0:
                    break
        if best_d == 0:
            break

    if best_d is None or best_off is None:
        return None

    # The char-precise window in flat_norm gives the truthful edit distance.
    # We snap whole-verse boundaries ONLY for reporting which surah/verses
    # overlap the match; we do NOT recompute distance against snapped text,
    # because Quran corpora prepend a basmala to verse 1 of each surah, which
    # would otherwise inflate the distance for short inputs that don't include
    # the basmala.
    end_off = best_off + best_win_len
    cand_norm = flat_norm[best_off:end_off]
    d_actual, ops = levenshtein_with_ops(qry, cand_norm)
    deviation = d_actual / max(L, len(cand_norm), 1)

    i_start, i_end = _verse_index_range_for(best_off, end_off, verse_starts)
    cand_raw = " ".join(verses[j].raw for j in range(i_start, i_end + 1))
    return FuzzyHit(
        surah_start=verses[i_start].surah,
        verse_start=verses[i_start].verse,
        surah_end=verses[i_end].surah,
        verse_end=verses[i_end].verse,
        candidate_norm=cand_norm,
        candidate_raw=cand_raw,
        edit_distance=d_actual,
        deviation_pct=deviation,
        ops=ops,
        n_verses_spanned=i_end - i_start + 1,
    )


# ----------------------------------------------------------------------
# Top-level convenience: classify input
# ----------------------------------------------------------------------

@dataclass
class Classification:
    verdict: str        # "QURAN_VERBATIM" | "MODIFIED_QURAN" | "NOT_QURAN"
    deviation_pct: float
    verbatim: Optional[VerbatimHit]
    fuzzy: Optional[FuzzyHit]
    n_input_letters: int

    @property
    def is_quran(self) -> bool:
        return self.verdict == "QURAN_VERBATIM"

    @property
    def is_modified_quran(self) -> bool:
        return self.verdict == "MODIFIED_QURAN"


# Threshold: if normalised edit distance / length < this, classify as MODIFIED_QURAN.
# 0.20 = up to 20% letters changed. Beyond that, the text has diverged enough
# from any canonical passage that the structural-fingerprint test is the right
# tool, not edit-distance.
DEVIATION_THRESHOLD = 0.20


def classify(text: str) -> Classification:
    """Top-level: run verbatim then fuzzy, return one classification."""
    qry = normalise(text)
    n = len(qry)

    vh = verbatim_locate(text)
    if vh is not None:
        return Classification(
            verdict="QURAN_VERBATIM",
            deviation_pct=0.0,
            verbatim=vh,
            fuzzy=None,
            n_input_letters=n,
        )

    fh = fuzzy_locate(text)
    if fh is not None and fh.deviation_pct < DEVIATION_THRESHOLD:
        return Classification(
            verdict="MODIFIED_QURAN",
            deviation_pct=fh.deviation_pct,
            verbatim=None,
            fuzzy=fh,
            n_input_letters=n,
        )

    return Classification(
        verdict="NOT_QURAN",
        deviation_pct=fh.deviation_pct if fh else 1.0,
        verbatim=None,
        fuzzy=fh,
        n_input_letters=n,
    )
