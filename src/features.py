# -*- coding: utf-8 -*-
"""
Canonical 5-D feature extractor (audit rebuild, 2026-04-17).

Fixes the following issues from the forensic audit:
  F-06 : Arabic root extraction now uses CamelTools (1.5.7) instead of the
         36%-accurate consonant-skeleton heuristic.
  F-11 : `T` is defined EXACTLY as in QSF_PAPER_DRAFT_v2 §2.6 —
         T = H(root_transition) - H(end_letter) — in EVERY script that
         imports this module. No more `T = VL_CV * H_cond` alternate form.
  F-12 : the module does NOT define a "control" pool; it only returns
         features. Selecting controls is the caller's responsibility so
         the control-pool-contamination issue cannot sneak in here.

Provided functions:
  el_rate(verses)       : fraction of consecutive verses sharing terminal letter
  vl_cv(verses)         : coefficient of variation of verse word counts
  cn_rate(verses, stops): fraction of verses starting with a connective
  h_cond_roots(verses)  : conditional entropy H(root_{i+1} | root_i) on verse-final words
                          using CamelTools plurality root, '#'-stripped (primary_root_normalized)
  h_el(verses)          : Shannon entropy of verse-final letter distribution
  t_tension(verses)     : T = h_cond_roots(verses) - h_el(verses)     [paper §2.6]
  features_5d(verses, stops) -> np.ndarray of length 5  (EL, VL_CV, CN, H_cond, T)

Language-agnostic helpers (for Hebrew / Greek cross-language work):
  h_cond_initials(verses) : old paper-§2.6 "language-agnostic proxy"
  features_5d_lang_agnostic(verses, stops) : EL, VL_CV, CN, H_cond_initials,
                                             T_lang = H_cond_initials - h_el
         This is the ONLY 5-D function that does not rely on Arabic morphology;
         use it for Hebrew Tanakh and Greek Iliad where CamelTools does not
         apply. Note: T_lang is NOT interchangeable with T in the Arabic-specific
         form; any script that mixes them is reintroducing F-11.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Iterable

import numpy as np

from . import roots as _rc  # relative import within src/

# ----------------------------------------------------------------------
# Shared constants
# ----------------------------------------------------------------------
# Diacritics we strip before ANY feature computation.
DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)

# Discourse connectives — same set used by the paper §2.2 (14 items).
# This is the "conservative" list that EXCLUDES proclitics ل/ب (per paper).
ARABIC_CONN = set(
    "و ف ثم بل لكن او إن أن لأن حتى إذ إذا لما كي".split()
)


def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)


# ----------------------------------------------------------------------
# Core features (language-specific: uses CamelTools for H_cond)
# ----------------------------------------------------------------------
def _terminal_alpha(verse: str) -> str:
    v = _strip_d(verse).strip()
    for c in reversed(v):
        if c.isalpha():
            return c
    return ""


def el_rate(verses: list[str]) -> float:
    if len(verses) < 2:
        return 0.0
    finals = [_terminal_alpha(v) for v in verses]
    n_pairs = len(finals) - 1
    if n_pairs == 0:
        return 0.0
    return sum(
        1 for i in range(n_pairs) if finals[i] and finals[i] == finals[i + 1]
    ) / n_pairs


def vl_cv(verses: list[str]) -> float:
    lens = np.array([len(v.split()) for v in verses], dtype=float)
    if len(lens) < 2 or lens.mean() == 0.0:
        return 0.0
    return float(lens.std(ddof=1) / lens.mean())


def cn_rate(verses: list[str], stops: set[str]) -> float:
    """Fraction of verses (after the first) whose first token is in `stops`.
    Matches paper §2.2 definition over the SURAH-level connective rate:
    counts `n - 1` transitions, not `n`. `stops` is typically ARABIC_CONN
    for Arabic; for cross-language work, pass the top-N corpus-derived
    function words."""
    n = len(verses)
    if n < 2:
        return 0.0
    hits = 0
    for v in verses[1:]:
        toks = _strip_d(v).split()
        if toks and toks[0] in stops:
            hits += 1
    return hits / (n - 1)


def h_el(verses: list[str]) -> float:
    """Shannon entropy of the verse-final letter distribution (matches
    paper §2.6 H(end_letter) exactly)."""
    finals = [_terminal_alpha(v) for v in verses if _terminal_alpha(v)]
    if not finals:
        return 0.0
    c = Counter(finals)
    total = sum(c.values())
    h = 0.0
    for n in c.values():
        p = n / total
        if p > 0:
            h -= p * math.log2(p)
    return h


def _final_root(verse: str) -> str:
    """Verse-final root via CamelTools, with weak-radical '#' stripped
    so hollow verbs (قال -> ق#ل) collapse to ql the consonantal root.
    '' if CamelTools has no analysis."""
    v = _strip_d(verse).strip()
    toks = v.split()
    if not toks:
        return ""
    return _rc.primary_root_normalized(toks[-1])


def h_cond_roots(verses: list[str]) -> float:
    """Conditional entropy H(root_{i+1} | root_i) on the sequence of
    verse-final roots. Uses CamelTools (F-06 fix).

    Words whose CamelTools analysis returns no root are represented by an
    explicit `<unk>` symbol so they still contribute a transition edge
    (otherwise we would silently drop them and distort the entropy).
    """
    roots: list[str] = []
    for v in verses:
        r = _final_root(v)
        roots.append(r if r else "<unk>")
    if len(roots) < 2:
        return 0.0
    bigrams: dict[str, Counter] = defaultdict(Counter)
    marg: Counter = Counter()
    for a, b in zip(roots[:-1], roots[1:]):
        bigrams[a][b] += 1
        marg[a] += 1
    total = sum(marg.values())
    if total == 0:
        return 0.0
    h = 0.0
    for a, nexts in bigrams.items():
        p_a = marg[a] / total
        row_total = sum(nexts.values())
        if row_total == 0:
            continue
        row_h = 0.0
        for n in nexts.values():
            p = n / row_total
            if p > 0:
                row_h -= p * math.log2(p)
        h += p_a * row_h
    return h


def t_tension(verses: list[str]) -> float:
    """T = H_cond(root_transition) - H(end_letter). Paper §2.6."""
    return h_cond_roots(verses) - h_el(verses)


def features_5d(
    verses: list[str], stops: set[str] | None = None
) -> np.ndarray:
    """Canonical 5-D feature vector for Arabic. stops defaults to
    ARABIC_CONN (14-word connective set, paper §2.2)."""
    if stops is None:
        stops = ARABIC_CONN
    el = el_rate(verses)
    cv = vl_cv(verses)
    cn = cn_rate(verses, stops)
    hc = h_cond_roots(verses)
    he = h_el(verses)
    T = hc - he
    return np.array([el, cv, cn, hc, T], dtype=float)


# ----------------------------------------------------------------------
# Language-agnostic helpers for Hebrew / Greek
# ----------------------------------------------------------------------
def h_cond_initials(verses: list[str]) -> float:
    """Conditional entropy of word-initial character transitions
    (cross-language proxy; old paper §2.6 for non-Arabic corpora).
    Explicitly NAMED differently from h_cond_roots so no script can
    confuse the two."""
    initials = []
    for v in verses:
        for w in _strip_d(v).split():
            if w and w[0].isalpha():
                initials.append(w[0])
    if len(initials) < 2:
        return 0.0
    pairs = Counter(zip(initials[:-1], initials[1:]))
    first = Counter(initials[:-1])
    total = sum(first.values())
    if total == 0:
        return 0.0
    h = 0.0
    # P(a,b) * log P(a,b)/P(a) summed is H(b|a) * P(a)... redo carefully
    # Use the standard H(B|A) = sum_a P(a) H(B|A=a) formula by rebuilding
    # from the pair counts.
    by_a: dict[str, Counter] = defaultdict(Counter)
    for (a, b), n in pairs.items():
        by_a[a][b] += n
    for a, row in by_a.items():
        p_a = first[a] / total
        row_total = sum(row.values())
        if row_total == 0:
            continue
        row_h = 0.0
        for n in row.values():
            p = n / row_total
            if p > 0:
                row_h -= p * math.log2(p)
        h += p_a * row_h
    return h


def derive_stopwords(all_verses: Iterable[str], top_n: int = 20) -> set[str]:
    """Top-N most-frequent tokens as empirical function words (needed for
    Hebrew / Greek where ARABIC_CONN does not apply)."""
    c: Counter = Counter()
    for v in all_verses:
        c.update(_strip_d(v).split())
    return set(w for w, _ in c.most_common(top_n))


def features_5d_lang_agnostic(
    verses: list[str], stops: set[str]
) -> np.ndarray:
    """For Hebrew / Greek cross-language work. T here is defined on the
    language-agnostic proxy `h_cond_initials - h_el`; it is NOT comparable
    to the Arabic T above and MUST NOT be pooled with it (F-11)."""
    el = el_rate(verses)
    cv = vl_cv(verses)
    cn = cn_rate(verses, stops)
    hc = h_cond_initials(verses)
    he = h_el(verses)
    T = hc - he
    return np.array([el, cv, cn, hc, T], dtype=float)


# ----------------------------------------------------------------------
# Convenience Mahalanobis helper (caller supplies centroid + cov)
# ----------------------------------------------------------------------
def phi_m(feats: np.ndarray, mu: np.ndarray, Sinv: np.ndarray) -> np.ndarray:
    """Mahalanobis distance of each row of `feats` from `mu` under
    inverse-covariance `Sinv`. Works for 1-D and 2-D input."""
    feats = np.atleast_2d(feats)
    d = feats - mu[None, :]
    return np.sqrt(np.einsum("ij,jk,ik->i", d, Sinv, d))


if __name__ == "__main__":
    # Quick smoke test on the first Quran surah
    import gzip
    import pickle
    import sys
    from pathlib import Path

    sys.stdout.reconfigure(encoding="utf-8")

    ROOT = Path(__file__).resolve().parent.parent
    with gzip.open(ROOT / "after_v4_final.pkl.gz", "rb") as f:
        df = pickle.load(f)["data"]["df"]
    surah = df[df.corpus == "quran"].iloc[1]  # Al-Baqarah
    verses = list(surah["verse_texts"])
    f = features_5d(verses)
    print("Al-Baqarah (", len(verses), "verses)")
    print("  features_5d = EL, VL_CV, CN, H_cond, T")
    print(f"             = {f[0]:.4f}, {f[1]:.4f}, {f[2]:.4f}, "
          f"{f[3]:.4f}, {f[4]:+.4f}")
    _rc.flush_cache()
