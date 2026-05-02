"""per_surah_ref.py — per-surah reference statistics + length-bucketed lookup.

Loads (or builds, if missing) a CSV of axis values for every one of the 114
surahs in the SHA-locked Hafs corpus, and exposes a percentile lookup for an
input value against Quran surahs of similar length.

This is a SECOND, complementary reference to the sliding-window calibration in
calibration.py:

  - calibration.py compares against every N-verse sliding window inside every
    Quranic surah.  Best for "how typical is my N-verse value among all
    contiguous Quranic N-verse runs?"

  - per_surah_ref.py compares against the values of *whole Quran surahs of
    similar size to the input*.  Best for "how does my text rank among real
    Quran chapters of comparable length?"

Both are used by the Extremum Challenge panel: percentile-vs-similar-surahs is
the headline interpretability number; sliding-window is the stability/typical
range cross-check.

The CSV is regenerated whenever the corpus SHA changes.  See
build_per_surah_stats() — it runs on import if the CSV is missing or stale.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from . import metrics
from .constants import verify_quran_corpus
from .corpus import _load_verses, surah_verses
from .normalize import normalize_arabic_letters_only

# CSV lives next to the corpus calibration cache.
_CSV = Path(__file__).resolve().parent.parent.parent / "data" / "quran_per_surah_stats.csv"


# Axes pre-computed for every Quranic surah.  These mirror the input axes the
# Extremum Challenge tests, plus useful descriptive fields.
_CSV_FIELDS = [
    "surah", "n_verses", "n_words", "n_letters",
    "p_max", "H_EL_raw", "H_EL_mm", "C_Omega", "F75", "D_max",
    "VL_CV_letters", "VL_CV_words",
    "d_info", "HFD", "Delta_alpha",
]


@dataclass(frozen=True)
class SurahStats:
    surah: int
    n_verses: int
    n_words: int
    n_letters: int
    p_max: float
    H_EL_raw: float
    H_EL_mm: float
    C_Omega: float
    F75: float
    D_max: float
    VL_CV_letters: float
    VL_CV_words: float
    d_info: float
    HFD: float
    Delta_alpha: float


# ----- Build / load --------------------------------------------------------
def _compute_one_surah(s: int) -> SurahStats:
    verses = surah_verses(s)
    raws = [v.raw for v in verses]
    skel = "".join(v.skeleton for v in verses)
    n_verses = len(verses)
    n_words = sum(len(v.raw.split()) for v in verses)
    n_letters = len(skel)

    helpmap = metrics.pooled_H_EL_pmax(raws, bias_correct=False)
    helpmap_mm = metrics.pooled_H_EL_pmax(raws, bias_correct=True)
    p_max = helpmap["p_max"]
    H_raw = helpmap["H_EL_raw"]
    H_mm = helpmap["H_EL_mm"]
    # C_Omega / F75 / D_max are reported using the RAW H_EL to match the
    # locked exp75/exp101/exp115 reference values.  (The Miller-Madow column
    # is exposed separately for short-N comparisons.)
    C_Omega = helpmap["C_Omega"]
    F75 = helpmap["F75"]
    D_max = helpmap["D_max"]
    VLcv_l = metrics.verse_length_cv(raws, unit="letters")
    VLcv_w = metrics.verse_length_cv(raws, unit="words")
    di = metrics.d_info(skel)
    lens = np.array([len(v.skeleton) for v in verses], dtype=float)
    HFD = metrics.higuchi_fd(lens) if lens.size >= 32 else float("nan")
    Da = metrics.delta_alpha_mfdfa(lens) if lens.size >= 64 else float("nan")
    return SurahStats(
        surah=s, n_verses=n_verses, n_words=n_words, n_letters=n_letters,
        p_max=p_max, H_EL_raw=H_raw, H_EL_mm=H_mm,
        C_Omega=C_Omega, F75=F75, D_max=D_max,
        VL_CV_letters=VLcv_l, VL_CV_words=VLcv_w,
        d_info=di, HFD=HFD, Delta_alpha=Da,
    )


def build_per_surah_stats(force: bool = False) -> Path:
    """(Re)build the per-surah stats CSV.  Returns the path written.

    If the CSV exists and the corpus SHA stamped in its header line matches
    the live corpus SHA, this is a no-op unless force=True.
    """
    sha = verify_quran_corpus().sha256_actual
    if (not force) and _CSV.is_file():
        try:
            with _CSV.open("r", encoding="utf-8") as fh:
                first = fh.readline().strip()
            if first.startswith("# corpus_sha256=") and first.endswith(sha):
                return _CSV
        except OSError:
            pass
    verses = _load_verses()
    surahs = sorted({v.surah for v in verses})
    rows: List[SurahStats] = [_compute_one_surah(s) for s in surahs]
    _CSV.parent.mkdir(parents=True, exist_ok=True)
    with _CSV.open("w", encoding="utf-8", newline="") as fh:
        fh.write(f"# corpus_sha256={sha}\n")
        w = csv.writer(fh)
        w.writerow(_CSV_FIELDS)
        for r in rows:
            w.writerow([
                r.surah, r.n_verses, r.n_words, r.n_letters,
                f"{r.p_max:.8f}", f"{r.H_EL_raw:.8f}", f"{r.H_EL_mm:.8f}",
                f"{r.C_Omega:.8f}", f"{r.F75:.8f}", f"{r.D_max:.8f}",
                f"{r.VL_CV_letters:.8f}", f"{r.VL_CV_words:.8f}",
                f"{r.d_info:.8f}", f"{r.HFD:.8f}", f"{r.Delta_alpha:.8f}",
            ])
    return _CSV


@lru_cache(maxsize=1)
def load_per_surah_stats() -> List[SurahStats]:
    """Read the per-surah stats CSV, rebuilding it if missing or stale."""
    build_per_surah_stats(force=False)
    rows: List[SurahStats] = []
    with _CSV.open("r", encoding="utf-8") as fh:
        # Skip SHA header line.
        first = fh.readline()
        if not first.startswith("#"):
            fh.seek(0)
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(SurahStats(
                surah=int(row["surah"]),
                n_verses=int(row["n_verses"]),
                n_words=int(row["n_words"]),
                n_letters=int(row["n_letters"]),
                p_max=float(row["p_max"]),
                H_EL_raw=float(row["H_EL_raw"]),
                H_EL_mm=float(row["H_EL_mm"]),
                C_Omega=float(row["C_Omega"]),
                F75=float(row["F75"]),
                D_max=float(row["D_max"]),
                VL_CV_letters=float(row["VL_CV_letters"]),
                VL_CV_words=float(row["VL_CV_words"]),
                d_info=float(row["d_info"]),
                HFD=float(row["HFD"]),
                Delta_alpha=float(row["Delta_alpha"]),
            ))
    return rows


# ----- Length-bucketed percentile lookup -----------------------------------
# Bins are chosen to match the project's published surah-scale analyses
# (F84 explicitly grouped at 5+, juz', corpus).  Each bin needs a minimum
# sample size; if the exact-N or narrow-bin pool has < MIN_SAMPLES, we widen.
_MIN_SAMPLES = 8
_LENGTH_BINS = [
    (3, 4),       # very short — Mufaṣṣal tail (Kawthar / ʿAṣr / Naṣr ...)
    (5, 9),       # short
    (10, 19),     # short-medium
    (20, 39),     # medium
    (40, 79),     # medium-long
    (80, 159),    # long
    (160, 1000),  # very long (Baqarah / al-ʿImrān / al-Nisāʾ ...)
]


def _bin_for(n: int) -> Tuple[int, int]:
    for lo, hi in _LENGTH_BINS:
        if lo <= n <= hi:
            return lo, hi
    return _LENGTH_BINS[0]


def _value(row: SurahStats, axis: str) -> float:
    return getattr(row, axis)


@dataclass(frozen=True)
class SimilarLengthRef:
    axis: str
    input_value: float
    n_verses_input: int
    bin_lo: int
    bin_hi: int
    n_samples: int
    median: float
    p10: float
    p90: float
    vmin: float
    vmax: float
    percentile: float       # 0..100  (where input ranks among bin)
    note: str               # explanation of bin widening, if any


def percentile_in_similar_length(axis: str,
                                  input_value: float,
                                  n_verses_input: int) -> Optional[SimilarLengthRef]:
    """Rank `input_value` of `axis` among Quran surahs of similar length.

    Strategy: pick the nearest length bin; if it has < _MIN_SAMPLES rows with a
    finite value, widen to neighbouring bins until the pool is large enough or
    the whole 114-surah corpus is used.  Returns None if no comparable Quran
    surahs exist for this axis at any length (e.g., HFD with Quran's 32-verse
    floor and no surahs reach it — won't happen in practice).
    """
    if axis not in SurahStats.__annotations__:
        raise ValueError(f"Unknown axis: {axis}")
    if not np.isfinite(input_value):
        return None

    rows = load_per_surah_stats()
    bin_lo, bin_hi = _bin_for(n_verses_input)
    note = f"compared against Quran surahs with {bin_lo} ≤ n_verses ≤ {bin_hi}"

    def _pool_for(lo: int, hi: int) -> List[float]:
        return [
            _value(r, axis) for r in rows
            if lo <= r.n_verses <= hi and np.isfinite(_value(r, axis))
        ]

    pool = _pool_for(bin_lo, bin_hi)
    if len(pool) < _MIN_SAMPLES:
        # Widen by progressively merging neighbouring bins.
        idx = next(i for i, (lo, _) in enumerate(_LENGTH_BINS) if lo == bin_lo)
        lo_lo, hi_hi = bin_lo, bin_hi
        while len(pool) < _MIN_SAMPLES and (idx > 0 or idx < len(_LENGTH_BINS) - 1):
            grew = False
            if idx > 0:
                idx -= 1
                lo_lo = _LENGTH_BINS[idx][0]
                grew = True
            if len(_pool_for(lo_lo, hi_hi)) < _MIN_SAMPLES and idx < len(_LENGTH_BINS) - 1:
                next_idx = next(
                    (i for i, (lo, _) in enumerate(_LENGTH_BINS) if lo == bin_lo),
                    idx,
                )
                if next_idx + 1 < len(_LENGTH_BINS):
                    hi_hi = _LENGTH_BINS[next_idx + 1][1]
                    grew = True
            new_pool = _pool_for(lo_lo, hi_hi)
            if len(new_pool) <= len(pool) and not grew:
                break
            pool = new_pool
        if len(pool) < _MIN_SAMPLES:
            # Final fallback: use ALL surahs with a finite value on this axis.
            pool = [_value(r, axis) for r in rows if np.isfinite(_value(r, axis))]
            lo_lo, hi_hi = 1, max(r.n_verses for r in rows)
            note = (f"too few Quran surahs near n_verses = {n_verses_input}; "
                    f"comparing against ALL {len(pool)} surahs with this axis defined")
        else:
            note = (f"narrow length bin had < {_MIN_SAMPLES} surahs; widened to "
                    f"{lo_lo} ≤ n_verses ≤ {hi_hi} ({len(pool)} surahs)")
        bin_lo, bin_hi = lo_lo, hi_hi

    if not pool:
        return None
    arr = np.asarray(sorted(pool), dtype=float)
    pct = 100.0 * float(np.searchsorted(arr, input_value, side="right")) / arr.size
    return SimilarLengthRef(
        axis=axis,
        input_value=float(input_value),
        n_verses_input=n_verses_input,
        bin_lo=bin_lo,
        bin_hi=bin_hi,
        n_samples=int(arr.size),
        median=float(np.median(arr)),
        p10=float(np.percentile(arr, 10)),
        p90=float(np.percentile(arr, 90)),
        vmin=float(arr.min()),
        vmax=float(arr.max()),
        percentile=pct,
        note=note,
    )


__all__ = [
    "SurahStats",
    "SimilarLengthRef",
    "build_per_surah_stats",
    "load_per_surah_stats",
    "percentile_in_similar_length",
]
