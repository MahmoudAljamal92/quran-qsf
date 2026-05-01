"""
experiments/_ultimate2_helpers.py
=================================
Shared, read-only helpers for the Ultimate-2 pipeline (R1–R11 + MASTER).

Everything a letter-level detector needs, in one place:

  * Arabic normalisation (rasm-preserving, diacritic-stripped)
  * Letter-level and word-level tokenisers
  * Single-letter edit generators (swap / insert / delete) at position
  * Fast character n-gram language model (pure NumPy, no torch)
  * Generic null-generators (N0–N7) for the null-ladder test
  * Corpus accessors that reuse the Ultimate-1 phase_06_phi_m checkpoint

No mutation. Every function is deterministic given its seed.

See:
  * experiments/_lib.py           — integrity-checked checkpoint loader
  * experiments/LOST_GEMS_AND_NOBEL_PATH.md — the scientific plan
"""
from __future__ import annotations

import hashlib
import math
import random
import re
from collections import Counter, defaultdict
from typing import Iterable, Sequence

import numpy as np

# ---------------------------------------------------------------------------
# Schema version (bumped whenever result JSON shape changes)
# ---------------------------------------------------------------------------
# v3 = 2026-04-20 AUDIT ROUND 2 (whitespace-preserving nulls, per-edit-type
#      null distributions, MASTER split into edit_detection vs
#      corpus_authenticity, Greek-aware R3, calibrated rates, proper R9
#      bootstrap, R6 equalised FAST edge-cap).
# v2 = 2026-04-20 audit-fix pass (fixes F-1..F-13, F-16 + listed WARNs).
# v1 = original Ultimate-2 pipeline (pre-audit).
SCHEMA_VERSION: int = 3

# ---------------------------------------------------------------------------
# Arabic alphabet & normalisation
# ---------------------------------------------------------------------------
ARABIC_CONSONANTS: str = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"  # 28
ARABIC_EXTRA: str = "ىءؤئة"                              # hamza-bearers + ta-marbuta
DIACRITICS: str = "\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0653\u0654\u0655\u0670"
TATWEEL: str = "\u0640"

# Greek letter range (for the F-ULT2-R3a audit-round-2 fix): when R3 runs
# the canonical-path test on ``iliad_greek`` the default Arabic normaliser
# strips every Greek character to whitespace, producing a degenerate test.
# ``normalize_greek_strict`` is a Greek-aware counterpart used only by R3.
GREEK_LETTERS_RE = re.compile(r"[^\u0370-\u03FF\u1F00-\u1FFF\s]")
_GREEK_DIACRITICS_RE = re.compile(r"[\u0300-\u036F]")

# Folded (="rasm-lossy") map: hamza variants + alef-maqsura + ta-marbuta all
# collapse to their base. Used by normalize_rasm_folded (the historical default).
_FOLD_MAP = {
    "أ": "ا", "إ": "ا", "آ": "ا",   # hamza-on-alef → alef
    "ٱ": "ا",                         # wasla-alef → alef
    "ى": "ي",                         # alef-maqsura → ya (controversial but standard)
    "ؤ": "و", "ئ": "ي",               # hamza-bearers
    "ة": "ه",                         # ta-marbuta → ha
}

# Strict (="rasm-preserving") map: only unambiguous orthographic variants of
# alef are folded; ى, ة, ؤ, ئ are kept distinct from ي, ه, و, ي. Used by
# detectors that rely on rasm fidelity (F-39).
_FOLD_MAP_STRICT = {
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
}

# Hamza-preserving map (audit 2026-04-24, B14): folds NOTHING for alef.
# Keeps every alef variant (ا أ إ آ ٱ) mutually distinct so the exp46 E7
# confound can be split into phonologically-separate sub-classes:
#     E7a_ayn_bare_alef   ع ↔ ا
#     E7b_ayn_hamza_alef  ع ↔ أ / إ
#     E7c_ayn_madda       ع ↔ آ
_FOLD_MAP_HAMZA_PRESERVING: dict[str, str] = {}

_STRIP_RE = re.compile(f"[{DIACRITICS}{TATWEEL}]")
_NON_ARABIC_RE = re.compile(r"[^\u0621-\u064A\s]")


def _normalize_with(text: str, fold_map: dict[str, str]) -> str:
    t = _STRIP_RE.sub("", text)
    t = t.replace("ـ", "")
    for k, v in fold_map.items():
        t = t.replace(k, v)
    t = _NON_ARABIC_RE.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalize_rasm(text: str) -> str:
    """Legacy (folded) normaliser.

    Strips diacritics + tatweel; folds hamza-bearing variants, alef-maqsura
    (ى→ي) and ta-marbuta (ة→ه). This is **rasm-lossy** — it collapses
    characters that the Uthmani rasm keeps distinct. Kept for backwards
    compatibility of downstream channels that were calibrated against it.
    For rasm-fidelity-sensitive work use ``normalize_rasm_strict``.
    """
    return _normalize_with(text, _FOLD_MAP)


def normalize_rasm_strict(text: str) -> str:
    """Rasm-preserving normaliser (audit-pass F-39).

    Strips diacritics + tatweel; folds only the four alef variants
    (أ إ آ ٱ → ا). Keeps ى, ة, ؤ, ئ distinct so that letter-level
    tampering detectors operate on the same alphabet as the Uthmani rasm.
    """
    return _normalize_with(text, _FOLD_MAP_STRICT)


def normalize_rasm_hamza_preserving(text: str) -> str:
    """Hamza-preserving normaliser (audit 2026-04-24, B14).

    Strips diacritics + tatweel ONLY. Folds nothing — keeps ا, أ, إ,
    آ, ٱ mutually distinct. Used by exp46 for the B14 3-way E7 sub-class
    breakdown where the classic ع ↔ all-alef E7 confound (which mixes
    bare-alef substitution with hamza-bearing-alef substitution) is split
    into three phonologically-separable sub-classes:
        E7a_ayn_bare_alef   ع ↔ ا
        E7b_ayn_hamza_alef  ع ↔ أ / إ
        E7c_ayn_madda       ع ↔ آ
    """
    return _normalize_with(text, _FOLD_MAP_HAMZA_PRESERVING)


def letters_only(text: str) -> str:
    """Return only Arabic letters (folded), no whitespace."""
    return re.sub(r"\s+", "", normalize_rasm(text))


def letters_only_strict(text: str) -> str:
    """Return only Arabic letters under the rasm-preserving fold."""
    return re.sub(r"\s+", "", normalize_rasm_strict(text))


# ---- Greek normalisation (audit-round-2 fix F-ULT2-R3a) -------------------
def normalize_greek_strict(text: str) -> str:
    """Greek-aware normaliser used by R3 on ``iliad_greek`` / ``greek_nt``.

    Strips combining diacritics (Greek accents/breathings live in U+0300-
    U+036F after NFKD) and non-Greek characters. Keeps both the standard
    Greek block (U+0370-U+03FF) and the polytonic supplement (U+1F00-
    U+1FFF) so Homeric Greek isn't silently erased by the Arabic regex.
    """
    import unicodedata
    t = unicodedata.normalize("NFKD", text)
    t = _GREEK_DIACRITICS_RE.sub("", t)
    t = GREEK_LETTERS_RE.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t


def letters_only_greek(text: str) -> str:
    """Greek letters only, no whitespace."""
    return re.sub(r"\s+", "", normalize_greek_strict(text))


def letter_bigram_set_greek(text: str) -> set[tuple[str, str]]:
    """Greek bigram set (used by R3 when the corpus is Greek)."""
    t = letters_only_greek(text)
    return set(zip(t, t[1:]))


def bigram_jaccard_distance_greek(a: str, b: str) -> float:
    """Jaccard distance for Greek texts."""
    A = letter_bigram_set_greek(a)
    B = letter_bigram_set_greek(b)
    if not (A | B):
        return 0.0
    return 1.0 - len(A & B) / len(A | B)


def canonical_path_length_bigram_greek(units: list[list[str]]) -> float:
    """Greek-aware canonical-path length (sum of adjacent bigram-Jaccard
    distances). Mirrors ``canonical_path_length_bigram`` but uses the Greek
    alphabet.
    """
    if len(units) < 2:
        return 0.0
    total = 0.0
    for i in range(len(units) - 1):
        a = " ".join(units[i])
        b = " ".join(units[i + 1])
        total += bigram_jaccard_distance_greek(a, b)
    return total


def words(text: str) -> list[str]:
    return normalize_rasm(text).split()


# ---------------------------------------------------------------------------
# Letter-level edits (swap / insert / delete) at a chosen position
# ---------------------------------------------------------------------------
CONFUSION_PAIRS = [
    ("ض", "ص"), ("ح", "خ"), ("د", "ذ"), ("س", "ش"), ("ت", "ث"),
    ("ر", "ز"), ("ك", "ق"), ("ع", "غ"), ("ه", "ة"), ("ا", "ى"),
    ("ل", "ن"), ("ب", "ت"), ("ط", "ظ"), ("ي", "ى"), ("و", "ؤ"),
]


def letter_swap(text: str, pos: int, new: str) -> str:
    """Replace the consonant at absolute letter-index `pos` with `new`."""
    if pos < 0 or pos >= len(text):
        return text
    return text[:pos] + new + text[pos + 1:]


def random_single_letter_swap(text: str, rng: random.Random) -> tuple[str, int, str, str]:
    """
    Swap one random letter with a plausibly-confusable partner.
    Returns (new_text, position, original_letter, new_letter).

    Whitespace in ``text`` is preserved (only consonant positions are
    candidates for the swap). The caller is responsible for passing
    text in the correct normalised form (typically the output of
    ``normalize_rasm``).
    """
    letters_positions = [i for i, ch in enumerate(text) if ch in ARABIC_CONSONANTS]
    if not letters_positions:
        return text, -1, "", ""
    pos = rng.choice(letters_positions)
    orig = text[pos]
    # 70% of the time choose confusion-partner, 30% random consonant
    partner = None
    for a, b in CONFUSION_PAIRS:
        if orig == a:
            partner = b
            break
        if orig == b:
            partner = a
            break
    if partner is None or rng.random() < 0.30:
        alt = [c for c in ARABIC_CONSONANTS if c != orig]
        partner = rng.choice(alt)
    return letter_swap(text, pos, partner), pos, orig, partner


# ---- Deletion / insertion / word-level edits (audit-round-2 F-ULT2-R1n1) --
def random_single_letter_delete(
    text: str, rng: random.Random
) -> tuple[str, int, str]:
    """Delete one consonant at a random position. Whitespace preserved.
    Returns (new_text, position, deleted_letter).
    """
    letters_positions = [i for i, ch in enumerate(text) if ch in ARABIC_CONSONANTS]
    if not letters_positions:
        return text, -1, ""
    pos = rng.choice(letters_positions)
    deleted = text[pos]
    return text[:pos] + text[pos + 1:], pos, deleted


def random_single_letter_insert(
    text: str, rng: random.Random
) -> tuple[str, int, str]:
    """Insert one random consonant at a random intra-word position.
    Whitespace preserved.
    Returns (new_text, position, inserted_letter).
    """
    if not text:
        return text, -1, ""
    # Candidate positions: between two existing consonants (to avoid
    # creating word boundaries or stranded letters across spaces).
    candidates = [
        i for i in range(1, len(text))
        if text[i - 1] in ARABIC_CONSONANTS and text[i] in ARABIC_CONSONANTS
    ]
    if not candidates:
        # Fallback: any position next to a consonant.
        candidates = [
            i for i, ch in enumerate(text) if ch in ARABIC_CONSONANTS
        ]
        if not candidates:
            return text, -1, ""
    pos = rng.choice(candidates)
    inserted = rng.choice(ARABIC_CONSONANTS)
    return text[:pos] + inserted + text[pos:], pos, inserted


def random_single_word_delete(
    text: str, rng: random.Random
) -> tuple[str, int, str]:
    """Delete one random word from ``text``. Returns (new_text, word_index,
    deleted_word). Word separator is a single space.
    """
    ws = text.split()
    if len(ws) < 2:
        return text, -1, ""
    i = rng.randrange(len(ws))
    deleted = ws[i]
    return " ".join(ws[:i] + ws[i + 1:]), i, deleted


def random_multi_word_replace(
    text: str, rng: random.Random, n: int = 2
) -> tuple[str, int, list[str]]:
    """Replace ``n`` contiguous words in ``text`` with ``n`` random
    words sampled from the same ``text``. Returns (new_text, start_index,
    replaced_words).
    """
    ws = text.split()
    if len(ws) < max(n * 2, 2):
        return text, -1, []
    start = rng.randrange(len(ws) - n + 1)
    replaced = ws[start:start + n]
    # Sample replacements from the same verse, avoiding the replaced span.
    pool = ws[:start] + ws[start + n:]
    if not pool:
        return text, -1, replaced
    sampled = [rng.choice(pool) for _ in range(n)]
    new_ws = ws[:start] + sampled + ws[start + n:]
    return " ".join(new_ws), start, replaced


def detect_edit_type(orig: str, var: str) -> str:
    """Classify an ``orig -> var`` edit into one of:

      ``null``, ``swap``, ``delete``, ``insert``,
      ``word_delete``, ``word_insert``, ``multi_word``.

    Inputs should already be rasm-normalised. Used by R1 to route each
    canonical variant to the correct null distribution.

    Heuristic:
      * If the word count differs, the edit is at the word level
        (``word_delete`` or ``word_insert``).
      * If the word count is equal and **exactly one** word differs, the
        edit is letter-level on that word (``swap``, ``delete``, ``insert``
        depending on the intra-word length delta).
      * If two or more words differ, the edit is ``multi_word``.
      * An identical pair returns ``null``.
    """
    if orig == var:
        return "null"
    o_words = orig.split()
    v_words = var.split()
    if len(o_words) != len(v_words):
        return "word_delete" if len(o_words) > len(v_words) else "word_insert"
    diffs = [(a, b) for a, b in zip(o_words, v_words) if a != b]
    if not diffs:
        return "null"
    if len(diffs) > 1:
        return "multi_word"
    a, b = diffs[0]
    if len(a) > len(b):
        return "delete"
    if len(a) < len(b):
        return "insert"
    return "swap"


def positional_letter_edit(text: str, rng: random.Random, region: str) -> tuple[str, int, str, str]:
    """
    Region ∈ {'beginning', 'middle', 'end'} of text.
    """
    n = len(text)
    if n == 0:
        return text, -1, "", ""
    if region == "beginning":
        lo, hi = 0, max(1, n // 3)
    elif region == "end":
        lo, hi = min(n - 1, 2 * n // 3), n
    else:
        lo, hi = n // 3, 2 * n // 3
    pos = rng.randint(lo, max(lo, hi - 1))
    if text[pos] not in ARABIC_CONSONANTS:
        return random_single_letter_swap(text, rng)
    orig = text[pos]
    alt = [c for c in ARABIC_CONSONANTS if c != orig]
    new = rng.choice(alt)
    return letter_swap(text, pos, new), pos, orig, new


# ---------------------------------------------------------------------------
# Character n-gram LM (pure NumPy; trains in seconds on MBs of text)
# ---------------------------------------------------------------------------
class CharNGramLM:
    """
    Back-off character n-gram LM with add-δ smoothing, trained on a
    *letters-only* stream (spaces kept as their own token).

    Gives log P(text) per character and supports cross-entropy deltas
    under a single-letter swap.
    """
    def __init__(self, n: int = 4, delta: float = 0.1):
        self.n = n
        self.delta = delta
        self.ctx: dict[str, Counter] = defaultdict(Counter)
        self.vocab: set[str] = set()
        self._trained = False

    def fit(self, texts: Iterable[str]) -> "CharNGramLM":
        for t in texts:
            t = " " + normalize_rasm(t) + " "
            self.vocab.update(t)
            for i in range(self.n - 1, len(t)):
                ctx = t[i - self.n + 1:i]
                ch = t[i]
                self.ctx[ctx][ch] += 1
        self._trained = True
        return self

    def log_prob(self, text: str) -> float:
        """Return sum of log-probs over all chars in text (in nats)."""
        assert self._trained, "fit() first"
        V = max(1, len(self.vocab))
        t = " " + normalize_rasm(text) + " "
        lp = 0.0
        for i in range(self.n - 1, len(t)):
            ctx = t[i - self.n + 1:i]
            ch = t[i]
            counter = self.ctx.get(ctx)
            if counter is None:
                # back off to uniform over vocab
                lp += math.log(1.0 / V)
            else:
                total = sum(counter.values())
                c = counter.get(ch, 0)
                p = (c + self.delta) / (total + self.delta * V)
                lp += math.log(p)
        return lp

    def per_char_lp(self, text: str) -> float:
        t_len = max(1, len(normalize_rasm(text)))
        return self.log_prob(text) / t_len


# ---------------------------------------------------------------------------
# Null generators (N0–N7) for R8 null-ladder
# ---------------------------------------------------------------------------
def N0_random_shuffle(verses: list[str], rng: random.Random) -> list[str]:
    """Full random shuffle (the weakest null)."""
    v = list(verses)
    rng.shuffle(v)
    return v


def N1_length_preserving(verses: list[str], rng: random.Random) -> list[str]:
    """Shuffle within length buckets (preserve per-position verse length)."""
    idx = list(range(len(verses)))
    lengths = [len(v) for v in verses]
    buckets = defaultdict(list)
    for i, L in enumerate(lengths):
        buckets[L // 20].append(i)  # bucket width 20 chars
    out = [None] * len(verses)
    for _, ids in buckets.items():
        perm = ids[:]
        rng.shuffle(perm)
        for src, dst in zip(ids, perm):
            out[dst] = verses[src]
    return out


def _end_letter(v: str) -> str:
    t = letters_only(v)
    return t[-1] if t else ""


def N3_EL_hist_preserving(verses: list[str], rng: random.Random) -> list[str]:
    """Shuffle within end-letter classes (preserve EL histogram AND positions)."""
    idx_by_el = defaultdict(list)
    for i, v in enumerate(verses):
        idx_by_el[_end_letter(v)].append(i)
    out = [None] * len(verses)
    for el, ids in idx_by_el.items():
        perm = ids[:]
        rng.shuffle(perm)
        for src, dst in zip(ids, perm):
            out[dst] = verses[src]
    return out


def N6_word_count_preserving(verses: list[str], rng: random.Random) -> list[str]:
    """Shuffle within word-count buckets."""
    out = [None] * len(verses)
    wc_groups = defaultdict(list)
    for i, v in enumerate(verses):
        wc_groups[len(words(v)) // 3].append(i)
    for _, ids in wc_groups.items():
        perm = ids[:]
        rng.shuffle(perm)
        for src, dst in zip(ids, perm):
            out[dst] = verses[src]
    return out


def N7_triple_preserving(verses: list[str], rng: random.Random) -> list[str]:
    """Preserve (EL, word-count-bucket, length-bucket) triple."""
    out = [None] * len(verses)
    groups = defaultdict(list)
    for i, v in enumerate(verses):
        key = (_end_letter(v), len(words(v)) // 3, len(v) // 25)
        groups[key].append(i)
    for _, ids in groups.items():
        perm = ids[:]
        rng.shuffle(perm)
        for src, dst in zip(ids, perm):
            out[dst] = verses[src]
    return out


# ---- Additional nulls (audit-fix F-14: honest N0–N7 ladder) ---------------
def N2_letter_freq_preserving(verses: list[str], rng: random.Random) -> list[str]:
    """Shuffle within letter-frequency-signature buckets.

    Per verse, compute a sorted tuple of the top-3 most frequent letters; keep
    verses with the same top-3 signature together. Preserves first-order
    letter statistics at the verse level while breaking sequence order.
    """
    def sig(v: str) -> tuple:
        c = Counter(letters_only(v))
        return tuple(ch for ch, _ in c.most_common(3))
    groups = defaultdict(list)
    for i, v in enumerate(verses):
        groups[sig(v)].append(i)
    out = [None] * len(verses)
    for _, ids in groups.items():
        perm = ids[:]
        rng.shuffle(perm)
        for src, dst in zip(ids, perm):
            out[dst] = verses[src]
    return out


def N4_EL_len_preserving(verses: list[str], rng: random.Random) -> list[str]:
    """Preserve (end-letter, length-bucket) joint."""
    out = [None] * len(verses)
    groups = defaultdict(list)
    for i, v in enumerate(verses):
        groups[(_end_letter(v), len(v) // 25)].append(i)
    for _, ids in groups.items():
        perm = ids[:]
        rng.shuffle(perm)
        for src, dst in zip(ids, perm):
            out[dst] = verses[src]
    return out


def N5_EL_wc_preserving(verses: list[str], rng: random.Random) -> list[str]:
    """Preserve (end-letter, word-count-bucket) joint."""
    out = [None] * len(verses)
    groups = defaultdict(list)
    for i, v in enumerate(verses):
        groups[(_end_letter(v), len(words(v)) // 3)].append(i)
    for _, ids in groups.items():
        perm = ids[:]
        rng.shuffle(perm)
        for src, dst in zip(ids, perm):
            out[dst] = verses[src]
    return out


NULLS = {
    "N0_random":          N0_random_shuffle,
    "N1_len":             N1_length_preserving,
    "N2_letter_freq":     N2_letter_freq_preserving,
    "N3_el_hist":         N3_EL_hist_preserving,
    "N4_el_len":          N4_EL_len_preserving,
    "N5_el_wc":           N5_EL_wc_preserving,
    "N6_wc":              N6_word_count_preserving,
    "N7_triple":          N7_triple_preserving,
}


# ---------------------------------------------------------------------------
# Small Mahalanobis helper (Ultimate-1 compatible)
# ---------------------------------------------------------------------------
def mahalanobis2(x: np.ndarray, mu: np.ndarray, S_inv: np.ndarray) -> float:
    d = x - mu
    return float(d @ S_inv @ d)


# ---------------------------------------------------------------------------
# Non-degenerate string metrics (audit-fix F-2)
# ---------------------------------------------------------------------------
# The historical `_canonical_path_length` used **letter-SET Jaccard** between
# adjacent units. For any long Arabic unit the letter set is approximately the
# full 28-letter alphabet, so the distance collapses to ~0 regardless of
# ordering and cannot distinguish canonical vs shuffled. The bigram-set
# Jaccard below has 28² = 784 possible entries and is substantially more
# discriminative for any unit shorter than a few thousand letters.

def letter_bigram_set(text: str, strict: bool = True) -> set[tuple[str, str]]:
    """Return the set of adjacent-letter bigrams in ``text``.

    ``strict=True`` uses the rasm-preserving normaliser (recommended).
    """
    t = letters_only_strict(text) if strict else letters_only(text)
    return set(zip(t, t[1:]))


def bigram_jaccard_distance(a: str, b: str, strict: bool = True) -> float:
    """Jaccard distance between the bigram sets of ``a`` and ``b``."""
    A = letter_bigram_set(a, strict=strict)
    B = letter_bigram_set(b, strict=strict)
    if not (A | B):
        return 0.0
    return 1.0 - len(A & B) / len(A | B)


def canonical_path_length_bigram(
    units: list[list[str]], strict: bool = True
) -> float:
    """Sum of adjacent-unit bigram-Jaccard distances — non-degenerate replacement
    for the letter-SET version used pre-audit.
    """
    if len(units) < 2:
        return 0.0
    total = 0.0
    for i in range(len(units) - 1):
        a = " ".join(units[i])
        b = " ".join(units[i + 1])
        total += bigram_jaccard_distance(a, b, strict=strict)
    return total


# ---------------------------------------------------------------------------
# Statistical utilities (audit-fix F-17, F-24)
# ---------------------------------------------------------------------------
def percentile_rank(null_vals: Iterable[float], v: float) -> float:
    """Fraction of ``null_vals`` that are <= ``v``. Returns 0..1."""
    arr = np.asarray(list(null_vals), dtype=float)
    if arr.size == 0:
        return 0.0
    return float((arr <= v).mean())


def bootstrap_ci(
    values: Sequence[float], n: int = 1000, alpha: float = 0.05,
    rng: random.Random | None = None,
) -> tuple[float, float]:
    """Percentile-bootstrap confidence interval for the mean."""
    v = np.asarray(list(values), dtype=float)
    if v.size < 2:
        return (float("nan"), float("nan"))
    r = rng or random.Random(0)
    means = np.empty(n, dtype=float)
    idx_pool = np.arange(v.size)
    for i in range(n):
        # deterministic-with-seed resample
        sample_idx = [r.randrange(v.size) for _ in range(v.size)]
        means[i] = v[sample_idx].mean()
    lo = float(np.quantile(means, alpha / 2))
    hi = float(np.quantile(means, 1 - alpha / 2))
    return (lo, hi)


def benjamini_hochberg(p_values: Sequence[float], alpha: float = 0.05) -> list[bool]:
    """Return a boolean list of rejections under Benjamini–Hochberg at level alpha.
    Order of the returned list matches the order of ``p_values``.
    """
    p = np.asarray(list(p_values), dtype=float)
    m = p.size
    if m == 0:
        return []
    order = np.argsort(p)
    ranked = p[order]
    threshold = alpha * (np.arange(1, m + 1) / m)
    passes = ranked <= threshold
    # k = largest i such that passes[i] is True
    if not passes.any():
        k = -1
    else:
        k = int(np.max(np.where(passes)[0]))
    reject = np.zeros(m, dtype=bool)
    if k >= 0:
        reject[order[: k + 1]] = True
    return reject.tolist()


# ---- Rate calibration (audit-round-2 fixes F-ULT2-M1 / F-ULT2-R10a) -------
def calibrate_rate_above_null(rate: float, null_baseline: float) -> float:
    """Map a raw detection rate onto [0, 1] with 0 == null baseline.

    ``null_baseline`` is the expected value of ``rate`` under H0 (no
    tampering). If ``rate <= null_baseline``, the calibrated rate is 0;
    otherwise it scales linearly to 1 as ``rate`` approaches 1.

    This is the audit-round-2 replacement for ``MASTER``'s implicit
    "null-channels contribute 0.5" coding that saturates the
    independence upper bound (F-ULT2-M1).
    """
    if null_baseline >= 1.0 - 1e-9:
        return 0.0
    if rate is None or not np.isfinite(rate):
        return 0.0
    excess = max(0.0, float(rate) - float(null_baseline))
    denom = 1.0 - float(null_baseline)
    return float(min(1.0, excess / denom)) if denom > 0 else 0.0


def auc_to_rate(auc: float | None) -> float:
    """Map an AUC onto [0, 1] so that AUC=0.5 (random baseline) -> 0.

    Uses the Gini coefficient ``2*AUC - 1`` clipped to [0, 1]. AUCs below
    0.5 (a systematically-worse-than-random classifier) return 0.
    """
    if auc is None or not np.isfinite(auc):
        return 0.0
    return float(max(0.0, min(1.0, 2.0 * float(auc) - 1.0)))


def signal_from_log_ratio_ci(ci_lo: float | None) -> float:
    """Map the lower bound of a log-ratio bootstrap CI onto [0, 1].

    Returns 0 when ``ci_lo <= 0`` (the CI includes no signal) and rises
    monotonically to 1 as the lower bound grows. Replaces the previous
    ``0.5 + 0.5*tanh(lo)`` coding which put uninformative channels at
    0.5 and saturated the MASTER composite.
    """
    if ci_lo is None or not np.isfinite(ci_lo):
        return 0.0
    lo = float(ci_lo)
    if lo <= 0.0:
        return 0.0
    return float(math.tanh(lo))


# Under R1's |z|>2 rule with 9 (near-)independent channels, the chance of
# >=3 firing by accident is ~Bin(9, 0.0456).sf(2) ≈ 0.011. We use that as
# the null baseline when calibrating R1's headline_single_letter_rate.
R1_NULL_BASELINE_3OF9: float = 0.011


# ---------------------------------------------------------------------------
# Utility: hash a string (for deterministic identifiers)
# ---------------------------------------------------------------------------
def shorthash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:8]


# ---------------------------------------------------------------------------
# Standard corpus accessor
# ---------------------------------------------------------------------------
def load_corpora() -> dict[str, list]:
    """Return the CORPORA dict from the Ultimate-1 phase_06 checkpoint.
    Read-only; SHA-256 is verified by experiments._lib.load_phase().
    """
    from experiments._lib import load_phase
    phi = load_phase("phase_06_phi_m")
    return phi["state"]["CORPORA"]


def load_phi_state() -> dict:
    """Return the full state dict from phase_06_phi_m (μ, S⁻¹, bands, feature matrices)."""
    from experiments._lib import load_phase
    return load_phase("phase_06_phi_m")["state"]


def extract_verses(unit) -> list[str]:
    """Robust extractor: accept raw_loader.Unit, dict, list, or str."""
    if hasattr(unit, "verses"):
        return [str(v) for v in unit.verses]
    if isinstance(unit, list):
        return [str(v) for v in unit]
    if isinstance(unit, dict):
        for key in ("verses", "ayat", "text"):
            if key in unit:
                v = unit[key]
                return [str(x) for x in v] if isinstance(v, list) else [str(v)]
        return [str(unit)]
    return [str(unit)]


def unit_label(unit) -> str:
    """Return label of a raw_loader.Unit or best-effort for other types."""
    if hasattr(unit, "label"):
        return str(unit.label)
    if isinstance(unit, dict) and "label" in unit:
        return str(unit["label"])
    return str(id(unit))


# ---------------------------------------------------------------------------
# Self-test (run `python -m experiments._ultimate2_helpers`)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    s = "إِنَّ اللَّهَ رَبَّنَا وَرَبُّكُمْ"
    print("original :", s)
    print("rasm     :", normalize_rasm(s))
    print("letters  :", letters_only(s))
    rng = random.Random(0)
    swapped, pos, a, b = random_single_letter_swap(letters_only(s), rng)
    print(f"swap@{pos}: {a}→{b}  ::  {swapped}")
    lm = CharNGramLM(n=3).fit([letters_only(s)] * 5)
    print("lm log_prob:", lm.log_prob(letters_only(s)))
