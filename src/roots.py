# -*- coding: utf-8 -*-
"""
CamelTools-backed root extractor with on-disk cache.

Fixes F-06 (root-extraction validity). Unlike the 36%-agreement heuristic,
this module queries CamelTools' MSA morphological analyzer and returns the
full set of candidate roots for each word. Downstream code picks the
plurality-voted root (with ties broken alphabetically) via primary_root()
or primary_root_normalized() (which additionally strips '#' weak-radical
markers). H_cond computation in features.py uses the single plurality root
(normalized, '#'-stripped) for verse-final bigram transitions.

Cache lives at:  src/cache/cameltools_root_cache.pkl.gz

Author: Cascade forensic-audit rebuild, 2026-04-17
"""
from __future__ import annotations

import gzip
import pickle
from collections import Counter
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_PATH = CACHE_DIR / "cameltools_root_cache.pkl.gz"

# Same diacritic + hamza normalisation as the other scripts, so that two
# spellings that map to the same rasm produce the same cache key.
_DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)
_HAMZA_MAP = str.maketrans("\u0623\u0625\u0624\u0626\u0622", "\u0621" * 5)


def _strip_d(s: str) -> str:
    return "".join(c for c in s if c not in _DIAC)


def _norm_word(w: str) -> str:
    return _strip_d(str(w)).translate(_HAMZA_MAP).strip()


# ----------------------------------------------------------------------
# Cache access
# ----------------------------------------------------------------------
_MEM_CACHE: dict[str, tuple[tuple[str, ...], int]] | None = None


def _load_cache() -> dict[str, tuple[tuple[str, ...], int]]:
    """On-disk cache: word -> (tuple of candidate roots sorted by frequency,
    number of CamelTools analyses)."""
    global _MEM_CACHE
    if _MEM_CACHE is not None:
        return _MEM_CACHE
    if CACHE_PATH.exists():
        with gzip.open(CACHE_PATH, "rb") as f:
            _MEM_CACHE = pickle.load(f)
    else:
        _MEM_CACHE = {}
    return _MEM_CACHE


def _save_cache(cache: dict[str, tuple[tuple[str, ...], int]]) -> None:
    with gzip.open(CACHE_PATH, "wb") as f:
        pickle.dump(cache, f, protocol=pickle.HIGHEST_PROTOCOL)


# ----------------------------------------------------------------------
# CamelTools wrapper
# ----------------------------------------------------------------------
_ANALYZER = None


def _get_analyzer():
    global _ANALYZER
    if _ANALYZER is not None:
        return _ANALYZER
    from camel_tools.morphology.database import MorphologyDB
    from camel_tools.morphology.analyzer import Analyzer
    db = MorphologyDB.builtin_db()
    _ANALYZER = Analyzer(db)
    return _ANALYZER


def _normalize_ct_root(r: str) -> str:
    """CamelTools roots are dot-delimited: 'ع.ل.م' -> 'علم'. '#' denotes a
    weak/missing position; preserve it so weak-root-aware code can detect
    it."""
    if not r:
        return ""
    s = _strip_d(str(r)).translate(_HAMZA_MAP)
    s = s.replace(".", "").replace("-", "").replace(" ", "")
    return s


def _query_cameltools(word: str) -> tuple[tuple[str, ...], int]:
    """Returns (candidate_roots_sorted_by_frequency, total_analyses).

    `candidate_roots_sorted_by_frequency` is a tuple of normalized root
    strings from most-frequent to least-frequent across CamelTools analyses;
    `total_analyses` is the raw analysis count returned by CamelTools.
    If no analyses or no root field, returns ((), 0) and the caller should
    fall back (e.g. to the heuristic as a last resort)."""
    analyzer = _get_analyzer()
    w = _norm_word(word)
    if not w:
        return ((), 0)
    try:
        results = analyzer.analyze(w)
    except Exception:
        return ((), 0)
    roots = []
    for r in results:
        rn = _normalize_ct_root(r.get("root", ""))
        if rn:
            roots.append(rn)
    if not roots:
        return ((), 0)
    counted = Counter(roots).most_common()
    ordered = tuple(root for root, _ in counted)
    return (ordered, len(roots))


def roots_for(word: str) -> tuple[tuple[str, ...], int]:
    """Public API. Returns (candidate roots tuple, n_analyses). Cached."""
    cache = _load_cache()
    key = _norm_word(word)
    if not key:
        return ((), 0)
    if key in cache:
        return cache[key]
    r = _query_cameltools(key)
    cache[key] = r
    return r


def flush_cache() -> None:
    """Write the in-memory cache to disk."""
    if _MEM_CACHE is None:
        return
    _save_cache(_MEM_CACHE)


def primary_root(word: str) -> str:
    """Plurality-voted root (with '#' preserved), or '' if CamelTools has
    no analysis. Downstream code that insists on a single root per word
    uses this."""
    roots, _ = roots_for(word)
    return roots[0] if roots else ""


def primary_root_normalized(word: str) -> str:
    """Same as primary_root but with '#' placeholders stripped out.
    Weak/hollow Arabic verbs (قال 'he said') have roots like 'ق#ل'
    in CamelTools notation where '#' marks the weak radical slot.
    Stripping '#' conflates weak roots with their consonantal skeleton
    (ق#ل -> قل). Use this for H_cond / bigram counting where you want
    weak-root-weak-root collisions to increase, not distort, entropy.
    """
    r = primary_root(word)
    if not r:
        return ""
    return r.replace("#", "")


def coverage_report(words: list[str]) -> dict:
    """For diagnostics: how many of these words does CamelTools cover?"""
    n = len(words)
    if n == 0:
        return {"n": 0, "covered": 0, "covered_pct": 0.0}
    covered = sum(1 for w in words if roots_for(w)[1] > 0)
    return {"n": n, "covered": covered, "covered_pct": 100.0 * covered / n}


def warm_cache(
    words: list[str], verbose: bool = True, save_every: int = 2000
) -> dict:
    """Pre-populate the cache for a list of words. Returns coverage stats.
    Intended to be called once per corpus to bulk-load roots, then
    flush_cache() to persist the results. Periodically flushes to disk
    so we don't lose progress on Ctrl-C."""
    import sys as _sys
    cache = _load_cache()
    uniq = list({_norm_word(w) for w in words if _norm_word(w)})
    n_before = len(cache)
    n_uniq = len(uniq)
    miss = [w for w in uniq if w not in cache]
    if verbose:
        print(
            f"[roots_cameltools] warming cache: {n_uniq} unique words, "
            f"{n_uniq - len(miss)} already cached, {len(miss)} new to query",
            flush=True,
        )
    t0 = __import__("time").time()
    for i, w in enumerate(miss):
        # roots_for() itself caches; no need to call _query_cameltools twice.
        roots_for(w)
        if verbose and (i + 1) % 200 == 0:
            elapsed = __import__("time").time() - t0
            rate = (i + 1) / elapsed if elapsed > 0 else 0.0
            eta = (len(miss) - i - 1) / rate if rate > 0 else 0.0
            print(
                f"  ...{i+1}/{len(miss)}  "
                f"({rate:.0f} w/s, ETA {eta:.0f}s)",
                flush=True,
            )
            _sys.stdout.flush()
        if (i + 1) % save_every == 0:
            flush_cache()
    flush_cache()
    cache = _load_cache()
    covered = sum(1 for w in uniq if cache.get(w, ((), 0))[1] > 0)
    if verbose:
        print(
            f"[roots_cameltools] cache size: {n_before} -> {len(cache)}; "
            f"coverage {covered}/{n_uniq} = {100.0*covered/n_uniq:.1f}%",
            flush=True,
        )
    return {"n_unique": n_uniq, "covered": covered,
            "covered_pct": 100.0 * covered / n_uniq, "cache_size": len(cache)}


if __name__ == "__main__":
    # Smoke test
    test_words = ["والعاديات", "ضبحا", "المجيد", "وعد", "قال",
                  "فالمغيرات", "يعلمون", "الله", "بسم", "الرحمن"]
    for w in test_words:
        roots, n = roots_for(w)
        print(f"  {w:<15s}  n={n:>2}   top-3={list(roots[:3])}")
    flush_cache()
    print(f"[OK] cache at {CACHE_PATH}")
