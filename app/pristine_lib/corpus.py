"""corpus.py — Hafs Quran loader, verbatim & fuzzy lookup.

The canonical Quran corpus is loaded once at startup, normalised once,
indexed for fast lookups, and exposed via three operations:

  exact_match(text)   -> list of (surah, verse, span) where the input
                          appears verbatim in the canonical Hafs text.
  fuzzy_match(text)   -> single best near-match passage with Levenshtein
                          edit distance and the canonical text alongside.
  surah_verses(s)     -> the canonical verses of surah `s`.

All operations work on the 28-letter rasm-skeleton (see normalize.py).
The raw Arabic (with diacritics) is also kept so the UI can display
the canonical version unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple

from .constants import QURAN_TXT, verify_quran_corpus
from .normalize import normalize_arabic_letters_only


@dataclass(frozen=True)
class Verse:
    surah: int
    ayah: int
    raw: str               # original line content (with diacritics)
    skeleton: str          # 28-letter rasm-only

    @property
    def label(self) -> str:
        return f"{self.surah}:{self.ayah}"


@dataclass(frozen=True)
class ExactHit:
    surah: int
    ayah_start: int
    ayah_end: int
    n_letters: int
    n_verses: int


@dataclass(frozen=True)
class FuzzyHit:
    surah: int
    ayah_start: int
    ayah_end: int
    edit_distance: int
    n_letters_canonical: int
    n_letters_input: int
    deviation_pct: float
    canonical_skeleton: str
    canonical_raw: str


# ----- Eager (cached) loader -----------------------------------------------
@lru_cache(maxsize=1)
def _load_verses() -> Tuple[Verse, ...]:
    """Load and parse the canonical Hafs corpus once. SHA-verified."""
    verify_quran_corpus()
    raw_text = QURAN_TXT.read_text(encoding="utf-8")
    out: List[Verse] = []
    for line in raw_text.splitlines():
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        try:
            s, a = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        body = parts[2].strip()
        skel = normalize_arabic_letters_only(body)
        out.append(Verse(surah=s, ayah=a, raw=body, skeleton=skel))
    return tuple(out)


@lru_cache(maxsize=1)
def _load_full_skeleton() -> str:
    """The entire Quran as one rasm-only stream (no spaces)."""
    return "".join(v.skeleton for v in _load_verses())


@lru_cache(maxsize=1)
def _load_full_skeleton_with_word_breaks() -> str:
    """The entire Quran as one rasm stream with single-space word breaks
    preserved between verses. Used for verbatim lookup with word context."""
    parts = []
    for v in _load_verses():
        # we use `space + skeleton + space` so word boundaries between
        # verses survive the concatenation
        parts.append(v.skeleton)
    return " ".join(parts)


@lru_cache(maxsize=1)
def _load_per_surah_skeleton() -> dict:
    """Map: surah_no -> concatenated skeleton of that surah's verses."""
    out: dict = {}
    for v in _load_verses():
        out.setdefault(v.surah, []).append(v.skeleton)
    return {s: "".join(vs) for s, vs in out.items()}


@lru_cache(maxsize=1)
def _verse_offsets() -> List[Tuple[int, int, int, int]]:
    """For each verse: (start_offset_in_full_skeleton, end_offset, surah, ayah).
    Lets us map an offset in the full stream back to a (surah, ayah) pair.
    """
    offs: List[Tuple[int, int, int, int]] = []
    p = 0
    for v in _load_verses():
        n = len(v.skeleton)
        offs.append((p, p + n, v.surah, v.ayah))
        p += n
    return offs


def all_verses() -> Tuple[Verse, ...]:
    return _load_verses()


def surah_verses(s: int) -> List[Verse]:
    return [v for v in _load_verses() if v.surah == s]


def n_chapters() -> int:
    return max(v.surah for v in _load_verses())


def total_letters() -> int:
    return len(_load_full_skeleton())


# ----- Exact verbatim lookup ------------------------------------------------
def exact_match(input_skeleton: str) -> Optional[ExactHit]:
    """Return the first verbatim occurrence of `input_skeleton` (rasm-only,
    no spaces) inside the canonical full-corpus skeleton. None if no match.
    """
    if not input_skeleton:
        return None
    full = _load_full_skeleton()
    pos = full.find(input_skeleton)
    if pos < 0:
        return None
    n = len(input_skeleton)
    end = pos + n
    offs = _verse_offsets()
    s_start, a_start, s_end, a_end = None, None, None, None
    for st, en, s, a in offs:
        if st <= pos < en and s_start is None:
            s_start, a_start = s, a
        if st < end <= en:
            s_end, a_end = s, a
            break
    if s_start is None or s_end is None:
        return None
    # Count verses whose stored range [st, en) overlaps [pos, end).
    n_verses = sum(
        1 for st, en, s, a in offs
        if st < end and en > pos
    )
    return ExactHit(
        surah=s_start,
        ayah_start=a_start,
        ayah_end=a_end,
        n_letters=n,
        n_verses=n_verses,
    )


# ----- Fuzzy near-match -----------------------------------------------------
def _levenshtein(a: str, b: str, max_dist: int) -> int:
    """Bounded Levenshtein. Returns max_dist+1 if exceeded."""
    la, lb = len(a), len(b)
    if abs(la - lb) > max_dist:
        return max_dist + 1
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        lo = max(1, i - max_dist)
        hi = min(lb, i + max_dist)
        for j in range(1, lb + 1):
            if j < lo or j > hi:
                cur[j] = max_dist + 1
                continue
            cost = 0 if a[i-1] == b[j-1] else 1
            cur[j] = min(prev[j] + 1, cur[j-1] + 1, prev[j-1] + cost)
        if min(cur[1:]) > max_dist:
            return max_dist + 1
        prev = cur
    return prev[lb]


_KGRAM_K = 6  # seed length for fuzzy candidate retrieval


@lru_cache(maxsize=1)
def _kgram_index() -> dict:
    """Build a k-gram -> sorted list of positions index on the full skeleton.

    A 1-letter edit destroys at most `k` consecutive k-grams; every other
    k-gram of the input is preserved verbatim somewhere in the canonical
    stream (if the input is near-Quran). That lets us find candidate
    starting offsets in O(|input|) without scanning the whole corpus.
    """
    full = _load_full_skeleton()
    idx: dict = {}
    n = len(full)
    k = _KGRAM_K
    for i in range(n - k + 1):
        gram = full[i : i + k]
        idx.setdefault(gram, []).append(i)
    return idx


def _offset_to_verse(offset: int) -> Tuple[int, int, int]:
    """Map a character offset in the full skeleton to (surah, ayah, verse_idx)."""
    offs = _verse_offsets()
    # Binary search would be cleaner; verse count ~6k so a linear scan is fine.
    for vi, (st, en, s, a) in enumerate(offs):
        if st <= offset < en:
            return s, a, vi
    # After last verse -> clip to last.
    last = offs[-1]
    return last[2], last[3], len(offs) - 1


def fuzzy_match(input_skeleton: str,
                max_pct_deviation: float = 0.10) -> Optional[FuzzyHit]:
    """Find the Quranic span that is closest to the input by Levenshtein
    distance, capped at `max_pct_deviation` of the input length.

    Strategy: k-gram seed retrieval. Pick several k-grams from the input
    (start, middle, end, and a uniform sprinkle). For each seed, find
    every position where it occurs in the canonical skeleton; that gives
    a candidate starting offset (seed_position - seed_offset_in_input).
    Test bounded Levenshtein on each candidate span whose length is near
    the input's. Early-exit when distance drops to 1.

    This handles:
      - inputs that start mid-verse (including after the Basmala prefix
        that the corpus prepends to verse 1 of every surah);
      - single-letter edits (at least one seed survives);
      - multi-seed edits across the input (uniform sprinkle).
    """
    if not input_skeleton:
        return None
    target_len = len(input_skeleton)
    max_dist = max(1, int(round(max_pct_deviation * target_len)))
    k = _KGRAM_K

    if target_len < k:
        return None

    full = _load_full_skeleton()
    full_len = len(full)
    idx = _kgram_index()
    offs = _verse_offsets()

    # --- Pick seeds: start, end, middle, plus a sprinkle every ~k letters.
    seed_positions = set()
    n_seeds = max(4, target_len // (k * 2))
    for t in range(n_seeds):
        p = int(t * (target_len - k) / max(1, n_seeds - 1))
        seed_positions.add(p)
    # Always include start and end seeds.
    seed_positions.add(0)
    seed_positions.add(max(0, target_len - k))

    # --- Gather candidate starting offsets in the canonical stream.
    candidates: set = set()
    for sp in seed_positions:
        gram = input_skeleton[sp : sp + k]
        for pos in idx.get(gram, ()):  # every place this gram appears
            start = pos - sp
            if 0 <= start <= full_len - (target_len - max_dist):
                candidates.add(start)

    if not candidates:
        return None

    # --- Test each candidate with a short span of length ~target_len.
    best: Optional[FuzzyHit] = None
    best_dist = max_dist + 1

    # Test spans of length target_len, target_len-1, target_len+1, etc.
    # to absorb indel edits. Up to ±max_dist.
    length_deltas = [0] + [d for pair in
                           zip(range(1, max_dist + 1), range(-1, -max_dist - 1, -1))
                           for d in pair]

    # To avoid pathological O(N) scans, cap to a safety budget.
    MAX_CANDIDATES = 20000
    cand_list = sorted(candidates)
    if len(cand_list) > MAX_CANDIDATES:
        # Keep evenly-spaced subsample; fine because near-Quran inputs
        # produce << 20k candidates.
        step = len(cand_list) // MAX_CANDIDATES + 1
        cand_list = cand_list[::step]

    for start in cand_list:
        for dl in length_deltas:
            end = start + target_len + dl
            if end > full_len or end <= start:
                continue
            cand_skel = full[start:end]
            d = _levenshtein(input_skeleton, cand_skel, best_dist - 1)
            if d < best_dist:
                best_dist = d
                # Map [start:end] back to verse range.
                s_s, a_s, vi_s = _offset_to_verse(start)
                s_e, a_e, vi_e = _offset_to_verse(max(start, end - 1))
                verses = _load_verses()
                cand_raw = " ".join(verses[k_].raw for k_ in range(vi_s, vi_e + 1))
                best = FuzzyHit(
                    surah=s_s,
                    ayah_start=a_s,
                    ayah_end=a_e,
                    edit_distance=d,
                    n_letters_canonical=len(cand_skel),
                    n_letters_input=target_len,
                    deviation_pct=100.0 * d / max(1, target_len),
                    canonical_skeleton=cand_skel,
                    canonical_raw=cand_raw,
                )
                if best_dist == 0:
                    return best  # perfect (unreachable — exact_match caught it)

    if best is None or best_dist > max_dist:
        return None
    return best


__all__ = [
    "Verse", "ExactHit", "FuzzyHit",
    "all_verses", "surah_verses", "n_chapters", "total_letters",
    "exact_match", "fuzzy_match",
]
