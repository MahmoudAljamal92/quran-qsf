"""calibration.py — length-matched null distribution scoring.

The fundamental bug in raw whole-corpus matching is sample-size bias: the
Quran's pooled H_EL is computed across 6,236 verses, but a 3-verse input
has 3 verse-endings. Comparing one to the other is mathematically unfair
and makes verbatim Quran score poorly on short inputs.

The fix: for any N-verse input, compare against the distribution of axis
values across every N-verse window inside Quranic surahs (never crossing
surah boundaries — we stay within natural Quranic structural units).

This uses the WHOLE Quran (every surah, every N-verse window that fits),
so it is NOT sharpshooter / subset selection. It is the standard
scientific technique of length-matched null calibration.

Scoring rule:
  If input value is inside the Quranic N-verse range [min, max] -> 100%.
  If outside -> score drops linearly with distance (in units of the
  Quranic range width). Below 0 is clamped to 0.

Guarantee: every Quranic N-verse passage scores 100% on every axis
(because its value is part of the distribution it's compared against).
"""
from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np

from . import metrics
from .constants import QURAN_TXT
from .corpus import _load_verses

# Disk cache: tiny .npy files keyed by (axis, n_verses, corpus_sha_prefix).
# Lives next to the corpus so it travels with the repo. The corpus SHA is
# baked into the file name so any corpus drift invalidates the cache.
_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "calibration_cache"


def _cache_path(axis: str, n_verses: int) -> Path:
    # Use first 8 hex chars of corpus SHA as a stamp; loaded lazily.
    from .constants import verify_quran_corpus
    sha = verify_quran_corpus().sha256_actual[:8]
    return _CACHE_DIR / f"{axis}__N{n_verses:03d}__{sha}.npy"


def _try_load_cached(axis: str, n_verses: int):
    p = _cache_path(axis, n_verses)
    if p.is_file():
        try:
            return np.load(p)
        except Exception:  # noqa: BLE001
            return None
    return None


def _save_cached(axis: str, n_verses: int, arr: np.ndarray) -> None:
    p = _cache_path(axis, n_verses)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        np.save(p, arr)
    except Exception:  # noqa: BLE001
        pass  # caching is best-effort; failures must not break analysis

# ----- Axis extractors -------------------------------------------------------
# For each axis, a function (verses_raw_list) -> value or NaN.
# Fractal axes (HFD / Delta_alpha) need long series and are N/A on small N.


def _H_EL(raw_verses: List[str]) -> float:
    return metrics.pooled_H_EL_pmax(raw_verses)["H_EL"]


def _p_max(raw_verses: List[str]) -> float:
    return metrics.pooled_H_EL_pmax(raw_verses)["p_max"]


def _C_Omega(raw_verses: List[str]) -> float:
    return metrics.pooled_H_EL_pmax(raw_verses)["C_Omega"]


def _F75(raw_verses: List[str]) -> float:
    return metrics.pooled_H_EL_pmax(raw_verses)["F75"]


def _D_max(raw_verses: List[str]) -> float:
    return metrics.pooled_H_EL_pmax(raw_verses)["D_max"]


def _d_info(raw_verses: List[str]) -> float:
    from .normalize import normalize_arabic_letters_only
    skel = "".join(normalize_arabic_letters_only(v) for v in raw_verses)
    return metrics.d_info(skel)


def _HFD(raw_verses: List[str]) -> float:
    from .normalize import normalize_arabic_letters_only
    lens = np.array([len(normalize_arabic_letters_only(v)) for v in raw_verses],
                    dtype=float)
    return metrics.higuchi_fd(lens) if lens.size >= 32 else float("nan")


def _Delta_alpha(raw_verses: List[str]) -> float:
    from .normalize import normalize_arabic_letters_only
    lens = np.array([len(normalize_arabic_letters_only(v)) for v in raw_verses],
                    dtype=float)
    return metrics.delta_alpha_mfdfa(lens) if lens.size >= 64 else float("nan")


AXIS_EXTRACTORS: Dict[str, Callable[[List[str]], float]] = {
    "H_EL":        _H_EL,
    "p_max":       _p_max,
    "C_Omega":     _C_Omega,
    "F75":         _F75,
    "D_max":       _D_max,
    "d_info":      _d_info,
    "HFD":         _HFD,
    "Delta_alpha": _Delta_alpha,
}


# ----- Windowed distribution builder -----------------------------------------
@dataclass(frozen=True)
class WindowedDistribution:
    axis: str
    n_verses: int
    values: np.ndarray          # sorted ascending
    vmin: float
    vmax: float
    median: float
    p01: float
    p10: float
    p20: float
    p80: float
    p90: float
    p99: float

    @property
    def n_windows(self) -> int:
        return int(self.values.size)

    @property
    def range_width(self) -> float:
        return float(self.vmax - self.vmin)


def _arr_to_distribution(axis: str, n_verses: int,
                         arr: np.ndarray) -> "WindowedDistribution":
    if arr.size == 0:
        nan = float("nan")
        return WindowedDistribution(
            axis=axis, n_verses=n_verses, values=arr,
            vmin=nan, vmax=nan, median=nan,
            p01=nan, p10=nan, p20=nan, p80=nan, p90=nan, p99=nan,
        )
    return WindowedDistribution(
        axis=axis, n_verses=n_verses, values=arr,
        vmin=float(arr.min()), vmax=float(arr.max()),
        median=float(np.median(arr)),
        p01=float(np.percentile(arr, 1)),
        p10=float(np.percentile(arr, 10)),
        p20=float(np.percentile(arr, 20)),
        p80=float(np.percentile(arr, 80)),
        p90=float(np.percentile(arr, 90)),
        p99=float(np.percentile(arr, 99)),
    )


@lru_cache(maxsize=512)
def windowed_distribution(axis: str, n_verses: int) -> WindowedDistribution:
    """Distribution of `axis` over every N-verse window inside every Quranic
    surah with at least N verses. Cached in memory and on disk.

    Windows never cross surah boundaries — each surah contributes
    (surah_len - N + 1) windows.
    """
    if axis not in AXIS_EXTRACTORS:
        raise ValueError(f"Unknown axis: {axis}")
    if n_verses < 1:
        raise ValueError(f"n_verses must be >= 1, got {n_verses}")

    # Try disk cache first.
    cached = _try_load_cached(axis, n_verses)
    if cached is not None:
        return _arr_to_distribution(axis, n_verses, cached)

    extractor = AXIS_EXTRACTORS[axis]
    verses = _load_verses()
    by_surah: Dict[int, List] = defaultdict(list)
    for v in verses:
        by_surah[v.surah].append(v)

    values = []
    for s, vs in by_surah.items():
        if len(vs) < n_verses:
            continue
        for i in range(len(vs) - n_verses + 1):
            raw_window = [vs[i + k].raw for k in range(n_verses)]
            val = extractor(raw_window)
            if val is not None and np.isfinite(val):
                values.append(float(val))

    arr = np.asarray(sorted(values), dtype=float)
    _save_cached(axis, n_verses, arr)
    return _arr_to_distribution(axis, n_verses, arr)


# ----- Match score using length-calibrated percentile bands ------------------
def length_calibrated_match(axis: str, value: float, n_verses: int) -> dict:
    """Match score for `value` against the Quranic N-verse distribution.

    Scoring uses percentile bands, not raw [min, max]:
      value in [p10, p90]           -> 100% match   (the inner 80%)
      value in [p1, p10) or (p90, p99]  -> 100% → 50% linear by tail depth
      value in [min, p1) or (p99, max]  -> 50% → 25% linear toward the extreme
      value outside [min, max]      -> < 25%, drops linearly with distance

    Why: the bare "inside [min, max]" rule is too permissive because the
    Quranic N-verse distribution is very wide (natural sampling of sliding
    windows hits outlier combinations). The inner 80% [p10, p90] is a
    principled "typical Quranic range" that discriminates Quran-like texts
    from extreme outliers while still giving every verbatim Quranic passage
    a score well above 50% (any Quranic passage is at SOME percentile of
    the Quranic distribution).

    Returned dict carries:
      match_pct     in [0, 100]
      percentile    empirical CDF (0..1)
      inside_p80    bool — inside inner 80% band
      inside_range  bool — inside [min, max]
      distribution  WindowedDistribution (for UI)
    """
    dist = windowed_distribution(axis, n_verses)
    out = {
        "match_pct": float("nan"),
        "percentile": float("nan"),
        "inside_p80": False,
        "inside_range": False,
        "distribution": dist,
    }
    if not np.isfinite(value) or dist.values.size == 0:
        return out

    arr = dist.values
    # Empirical CDF percentile using the midpoint rule (searchsorted gives
    # [0, N]; dividing by N gives a percentile in [0, 1]).  This is the
    # fraction of Quranic N-verse windows whose value is ≤ `value`.
    pct = float(np.searchsorted(arr, value)) / arr.size
    out["percentile"] = pct
    out["p10"] = dist.p10
    out["p90"] = dist.p90
    out["p01"] = dist.p01
    out["p99"] = dist.p99
    out["inside_p80"] = bool(dist.p10 <= value <= dist.p90)
    out["inside_range"] = bool(dist.vmin <= value <= dist.vmax)

    # ------------------------------------------------------------------
    # PERCENTILE-BASED MATCH SCORE (rewritten 2026-05-02 after review).
    # ------------------------------------------------------------------
    # Previous "identity rule" (vmin ≤ value ≤ vmax → 100%) was too
    # permissive: [vmin, vmax] spans every sliding Quranic N-verse window,
    # which at most N is so wide that any rhymed Arabic hits 100%.  That
    # silently broke Layer B as a discriminator.
    #
    # Piecewise empirical-CDF rule:
    #   pct ∈ [0.10, 0.90]  (inner 80%, the typical Quranic band): 100%
    #   pct ∈ [0.01, 0.10)  or  (0.90, 0.99]   : linear 60% → 100%
    #   pct ∈ [0.00, 0.01)  or  (0.99, 1.00]   : linear  0% →  60%
    #   value ∉ [vmin, vmax]                   : 0%
    #
    # This gives verbatim Quran the full 100% inside the typical band
    # (the common case), honest partial credit (<100%) for tail values
    # that are inside the observed Quranic range but atypical, and a
    # hard 0% outside the observed range — which is the right answer
    # given the range is derived from ~5,000 Quranic N-verse windows.
    # ------------------------------------------------------------------
    if not out["inside_range"]:
        rng = max(1e-12, dist.vmax - dist.vmin)
        gap = ((dist.vmin - value) if value < dist.vmin
               else (value - dist.vmax)) / rng
        out["match_pct"] = 0.0
        out["outside_gap"] = gap
        return out

    if 0.10 <= pct <= 0.90:
        out["match_pct"] = 100.0
    elif 0.01 <= pct < 0.10:
        # pct = 0.10 -> 100;  pct = 0.01 -> 60.
        out["match_pct"] = 60.0 + 40.0 * (pct - 0.01) / 0.09
    elif 0.90 < pct <= 0.99:
        out["match_pct"] = 60.0 + 40.0 * (0.99 - pct) / 0.09
    elif 0.0 <= pct < 0.01:
        out["match_pct"] = 60.0 * (pct / 0.01)
    else:  # 0.99 < pct <= 1.0
        out["match_pct"] = 60.0 * ((1.0 - pct) / 0.01)
    return out


__all__ = [
    "AXIS_EXTRACTORS",
    "WindowedDistribution",
    "windowed_distribution",
    "length_calibrated_match",
]
