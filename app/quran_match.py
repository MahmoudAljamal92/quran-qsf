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
    occurrences: int = 1     # how many places in the Quran contain this exact substring


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


def count_verbatim_occurrences(text: str, *, max_count: int = 10_000) -> int:
    """Count overlapping occurrences of the normalised input in the Quran corpus.

    This is a distinctiveness signal: a short phrase that occurs hundreds of
    times is a common Arabic formula, not a specific Quranic fingerprint.
    """
    _, flat_norm, _ = load_quran()
    qry = normalise(text)
    if not qry or not flat_norm:
        return 0
    count = 0
    idx = 0
    while count < max_count:
        p = flat_norm.find(qry, idx)
        if p < 0:
            break
        count += 1
        idx = p + 1   # allow overlapping occurrences
    return count


def verbatim_locate(text: str) -> Optional[VerbatimHit]:
    """Return location if the normalised input is an exact substring of the Quran.

    Matches across verse boundaries. Returns None if no exact match found or if
    the normalised input is empty.  Very-short inputs still return a hit here;
    the length/distinctiveness judgement is made by `classify()`, not this
    function, so callers can always see the raw facts.
    """
    verses, flat_norm, verse_starts = load_quran()
    qry = normalise(text)
    if not qry or not flat_norm:
        return None
    pos = flat_norm.find(qry)
    if pos < 0:
        return None
    end = pos + len(qry) - 1
    i_start = _verse_index_at(pos, verse_starts)
    i_end = _verse_index_at(end, verse_starts)
    # Count all occurrences for the distinctiveness signal.
    occurrences = 0
    idx = 0
    while True:
        p = flat_norm.find(qry, idx)
        if p < 0:
            break
        occurrences += 1
        idx = p + 1
        if occurrences >= 10_000:
            break
    return VerbatimHit(
        surah_start=verses[i_start].surah,
        verse_start=verses[i_start].verse,
        surah_end=verses[i_end].surah,
        verse_end=verses[i_end].verse,
        char_offset=pos,
        n_verses_spanned=i_end - i_start + 1,
        occurrences=occurrences,
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
    # Possible verdicts:
    #   "QURAN_VERBATIM"              -> exact substring AND long enough / unique enough
    #   "QURAN_SUBSTRING_AMBIGUOUS"   -> exact substring but short / very common
    #   "MODIFIED_QURAN"              -> fuzzy match within deviation threshold, long enough
    #   "NOT_QURAN"                   -> no close Quranic match; fingerprint test is appropriate
    #   "TOO_SHORT"                   -> input below any inference threshold, no match either
    verdict: str
    deviation_pct: float
    verbatim: Optional[VerbatimHit]
    fuzzy: Optional[FuzzyHit]
    n_input_letters: int
    occurrence_count: int = 0
    confidence: str = "low"           # "high" | "medium" | "low"
    rationale: str = ""               # one-sentence honest explanation

    @property
    def is_quran(self) -> bool:
        return self.verdict == "QURAN_VERBATIM"

    @property
    def is_modified_quran(self) -> bool:
        return self.verdict == "MODIFIED_QURAN"

    @property
    def is_ambiguous(self) -> bool:
        return self.verdict in ("QURAN_SUBSTRING_AMBIGUOUS", "TOO_SHORT")


# ----------------------------------------------------------------------
# Specificity thresholds (policy choices, not theorems)
# ----------------------------------------------------------------------
#
# We combine TWO independent signals to decide whether an exact substring
# match against the Quranic corpus is evidence of Quranic origin:
#
#   (a) LENGTH  — number of normalised Arabic letters in the input.
#                 Longer strings are exponentially less likely to appear
#                 in arbitrary non-Quranic Arabic by chance.
#
#   (b) OCCURRENCE COUNT — how many distinct positions of the Quran
#                 contain this exact substring.  Single common words
#                 ("الله" appears 2,729 times in the Quran) are NOT
#                 distinctive — they are ubiquitous in any Arabic text.
#                 A substring that appears once in the Quran is a much
#                 sharper fingerprint than one appearing 100+ times.
#
# Calibration against user-specified ground-truth:
#
#   • "والعاديات ضبحا"  (13 letters, 1 occurrence)  → QURAN_VERBATIM
#   • "مدهامتان"        (8  letters, 1 occurrence)  → QURAN_VERBATIM
#   • "الرحمن"          (6  letters, 160 occurrences) → AMBIGUOUS
#   • "بسم الله الرحمن الرحيم" (19 letters, 114 occurrences) → AMBIGUOUS
#   • "الله"            (4  letters, 2,729 occurrences) → AMBIGUOUS
#   • "كتب"             (3  letters) → TOO_SHORT
#
# Rule: we call a verbatim match QURAN_VERBATIM iff either
#   (i)  n >= 20  AND occurrences <= 50   (long enough, not a super-common formula), OR
#   (ii) n >=  8  AND occurrences <=  5   (medium-length AND rare in the Quran).
#
# Everything else that still matches as a substring is flagged
# QURAN_SUBSTRING_AMBIGUOUS with occurrence count and rationale shown.
MIN_LETTERS_FOR_ANY_INFERENCE = 4       # below this, refuse to rule anything in/out

MIN_LETTERS_LONG_VERBATIM   = 20        # long-phrase arm
MAX_OCC_LONG_VERBATIM       = 50

MIN_LETTERS_MEDIUM_VERBATIM = 8         # medium-phrase arm (requires rareness)
MAX_OCC_MEDIUM_VERBATIM     = 5

MIN_LETTERS_FOR_MODIFIED    = 8         # below this, fuzzy match is not trustworthy

# Threshold: if normalised edit distance / length < this, classify as MODIFIED_QURAN.
# 0.20 = up to 20% letters changed. Beyond that, the text has diverged enough
# from any canonical passage that the structural-fingerprint test is the right
# tool, not edit-distance.
DEVIATION_THRESHOLD = 0.20


def _confidence_for_length(n: int) -> str:
    if n >= 30:
        return "high"
    if n >= MIN_LETTERS_LONG_VERBATIM:
        return "medium"
    return "low"


def _is_verbatim_unambiguous(n: int, occ: int) -> bool:
    """Two-arm rule: (long enough) OR (medium + rare in Quran)."""
    long_arm   = (n >= MIN_LETTERS_LONG_VERBATIM   and occ <= MAX_OCC_LONG_VERBATIM)
    medium_arm = (n >= MIN_LETTERS_MEDIUM_VERBATIM and occ <= MAX_OCC_MEDIUM_VERBATIM)
    return long_arm or medium_arm


def classify(text: str) -> Classification:
    """Top-level: run verbatim then fuzzy, then apply distinctiveness guards.

    Returns one `Classification` whose `verdict` reflects both the match facts
    *and* the distinctiveness of the input.  Short / common inputs are labelled
    honestly (TOO_SHORT or QURAN_SUBSTRING_AMBIGUOUS) instead of falsely
    claiming Quranic origin from a coincidental substring match.
    """
    raw_len = len(text.strip())
    qry = normalise(text)
    n = len(qry)

    # ------------------------------------------------------------------
    # Case 0: raw text has real content but normalises to almost nothing
    # (e.g. English text, emojis, pure punctuation). This is NOT_QURAN,
    # not TOO_SHORT — we know it's not Arabic.
    # ------------------------------------------------------------------
    if raw_len >= 8 and n < MIN_LETTERS_FOR_ANY_INFERENCE:
        return Classification(
            verdict="NOT_QURAN",
            deviation_pct=1.0,
            verbatim=None,
            fuzzy=None,
            n_input_letters=n,
            occurrence_count=0,
            confidence="high",
            rationale=(
                f"Input has {raw_len} raw characters but only {n} Arabic letters "
                "after normalisation. The text is not in Arabic script, so it "
                "cannot be Quranic and the fingerprint test is the appropriate "
                "next step."
            ),
        )

    # ------------------------------------------------------------------
    # Layer 1: exact substring match (always run, always report facts).
    # ------------------------------------------------------------------
    vh = verbatim_locate(text)
    occ = vh.occurrences if vh is not None else 0

    # Case A: too short for any inference.
    if n < MIN_LETTERS_FOR_ANY_INFERENCE:
        return Classification(
            verdict="TOO_SHORT",
            deviation_pct=1.0,
            verbatim=vh,
            fuzzy=None,
            n_input_letters=n,
            occurrence_count=occ,
            confidence="low",
            rationale=(
                f"Input is only {n} normalised Arabic letter(s); far too short to "
                "establish Quranic origin. Any 1–3 letter string will match "
                "somewhere in any large Arabic corpus."
            ),
        )

    # Case B: exact substring found → apply distinctiveness rule.
    if vh is not None:
        if _is_verbatim_unambiguous(n, occ):
            return Classification(
                verdict="QURAN_VERBATIM",
                deviation_pct=0.0,
                verbatim=vh,
                fuzzy=None,
                n_input_letters=n,
                occurrence_count=occ,
                confidence=_confidence_for_length(n),
                rationale=(
                    f"Input is {n} normalised letters and appears at {occ} "
                    f"position(s) in the Quran. At this length/rareness the "
                    "match is statistically unlikely to arise by chance in "
                    "general Arabic."
                ),
            )
        # Short OR very common: be honest, do not claim origin.
        reason_bits = []
        if n < MIN_LETTERS_MEDIUM_VERBATIM:
            reason_bits.append(
                f"only {n} normalised letter(s) (below the "
                f"{MIN_LETTERS_MEDIUM_VERBATIM}-letter specificity floor)"
            )
        elif n < MIN_LETTERS_LONG_VERBATIM and occ > MAX_OCC_MEDIUM_VERBATIM:
            reason_bits.append(
                f"only {n} letters and appears {occ} times in the Quran "
                f"(> {MAX_OCC_MEDIUM_VERBATIM}, common formula)"
            )
        elif occ > MAX_OCC_LONG_VERBATIM:
            reason_bits.append(
                f"appears {occ} times in the Quran (> {MAX_OCC_LONG_VERBATIM}, "
                "common liturgical formula)"
            )
        reason = "; ".join(reason_bits) if reason_bits else "ambiguous by thresholds"
        return Classification(
            verdict="QURAN_SUBSTRING_AMBIGUOUS",
            deviation_pct=0.0,
            verbatim=vh,
            fuzzy=None,
            n_input_letters=n,
            occurrence_count=occ,
            confidence="low",
            rationale=(
                f"The input is a substring of the Quran, but {reason}. "
                "Such a string also appears in everyday Arabic (news, poetry, "
                "speech), so a substring match alone is not proof of Quranic "
                "origin."
            ),
        )

    # ------------------------------------------------------------------
    # Layer 2: no exact substring → fuzzy match.
    # ------------------------------------------------------------------
    fh = fuzzy_locate(text)

    if n < MIN_LETTERS_FOR_MODIFIED:
        return Classification(
            verdict="TOO_SHORT",
            deviation_pct=fh.deviation_pct if fh else 1.0,
            verbatim=None,
            fuzzy=fh,
            n_input_letters=n,
            occurrence_count=0,
            confidence="low",
            rationale=(
                f"Input has {n} normalised letters, below the "
                f"{MIN_LETTERS_FOR_MODIFIED}-letter threshold required before a "
                "fuzzy match can be trusted as evidence of a modified Quranic "
                "passage."
            ),
        )

    if fh is not None and fh.deviation_pct < DEVIATION_THRESHOLD:
        return Classification(
            verdict="MODIFIED_QURAN",
            deviation_pct=fh.deviation_pct,
            verbatim=None,
            fuzzy=fh,
            n_input_letters=n,
            occurrence_count=0,
            confidence=_confidence_for_length(n),
            rationale=(
                f"Closest Quranic passage differs by {fh.edit_distance} letter(s) "
                f"({fh.deviation_pct*100:.2f}% of the input). Below the "
                f"{DEVIATION_THRESHOLD*100:.0f}% deviation threshold, so the input "
                "is treated as a modified Quranic passage."
            ),
        )

    return Classification(
        verdict="NOT_QURAN",
        deviation_pct=fh.deviation_pct if fh else 1.0,
        verbatim=None,
        fuzzy=fh,
        n_input_letters=n,
        occurrence_count=0,
        confidence=_confidence_for_length(n),
        rationale=(
            "No close match to any Quranic passage. The 8-dimensional structural "
            "fingerprint is the appropriate test for texts at this distance."
        ),
    )
