"""metrics.py — eight whole-corpus-pooled fingerprint axes + tampering tests.

Every axis is computed *the same way* on the input and on the canonical
Quran. There are no per-surah / per-juz' / cherry-picked subsets here.

Axes (Layer B):
  H_EL          Shannon entropy of verse-final letter distribution
  p_max         most-frequent verse-final letter share
  C_Omega       1 - H_EL / log2(28)
  F75           H_EL + log2(p_max * 28)
  D_max         log2(28) - H_EL
  d_info        H_nats(letter freq) / log(1/0.18)
  HFD           Higuchi fractal dimension on the verse-length series
  Delta_alpha   multifractal spectrum width (MFDFA on verse-length series)

Tampering tests (Layer C):
  bigram_shift_delta(a, b)  -> Δ_bigram = sum |h_a - h_b| / 2
  gzip_ncd(a, b)            -> normalised compression distance

All inputs are 28-letter rasm skeletons (use normalize.normalize_arabic).
"""
from __future__ import annotations

import gzip
from collections import Counter
from math import log, log2, sqrt
from typing import Dict, List, Sequence

import numpy as np

from .constants import ARABIC_28, ALPHABET_SIZE, LOG2_A
from .normalize import normalize_arabic_letters_only


# ============================================================================
# Layer B — eight whole-corpus-pooled fingerprint axes
# ============================================================================
def _final_letter(skeleton: str) -> str:
    """Last letter of a normalised skeleton (or '' if empty)."""
    if not skeleton:
        return ""
    return skeleton[-1] if skeleton[-1] in ARABIC_28 else (
        skeleton.rstrip()[-1] if skeleton.rstrip() else ""
    )


def pooled_H_EL_pmax(verses: Sequence[str],
                     bias_correct: bool = False) -> Dict[str, float]:
    """Pooled verse-final entropy and p_max.

    Pools ALL verse-final letters of the input into one bag, then computes:
       p_max = most_common_count / total
       H_EL  = -sum p_i log2(p_i)              (plug-in)
       H_EL_mm = H_EL + (M-1)/(2 * N * ln 2)   (Miller-Madow corrected)
       C_Omega = 1 - H_EL / log2(28)
       F75   = H_EL + log2(p_max * 28)
       D_max = log2(28) - H_EL

    M is the number of distinct verse-final letters observed; N is the number
    of valid verse-finals.  The Miller-Madow correction adds the standard
    small-sample plug-in bias adjustment for Shannon entropy and is only
    meaningful when N is small (it vanishes as 1/N).

    If bias_correct=True, the returned H_EL / C_Omega / F75 / D_max use the
    Miller-Madow-corrected H_EL.  H_EL_raw is always returned alongside.

    Returns NaN values if fewer than 3 valid verse-finals are present.
    """
    finals = []
    for v in verses:
        skel = normalize_arabic_letters_only(v)
        f = _final_letter(skel)
        if f:
            finals.append(f)
    n = len(finals)
    if n < 3:
        return {
            "n_finals": n,
            "n_distinct_finals": 0,
            "H_EL": float("nan"),
            "H_EL_raw": float("nan"),
            "H_EL_mm": float("nan"),
            "p_max": float("nan"),
            "C_Omega": float("nan"),
            "F75": float("nan"),
            "D_max": float("nan"),
        }
    counts = Counter(finals)
    total = float(n)
    probs = np.array([c / total for c in counts.values() if c > 0])
    H_raw = float(-(probs * np.log2(probs)).sum())
    M = int(probs.size)
    # Miller-Madow plug-in bias correction (1955).
    H_mm = H_raw + (M - 1) / (2.0 * total * log(2.0)) if total > 0 else H_raw
    H_EL = H_mm if bias_correct else H_raw
    p_max = float(max(counts.values()) / total)
    C_Omega = 1.0 - H_EL / LOG2_A
    F75 = H_EL + log2(p_max * ALPHABET_SIZE)
    D_max = LOG2_A - H_EL
    return {
        "n_finals": n,
        "n_distinct_finals": M,
        "H_EL": H_EL,
        "H_EL_raw": H_raw,
        "H_EL_mm": H_mm,
        "p_max": p_max,
        "C_Omega": C_Omega,
        "F75": F75,
        "D_max": D_max,
    }


def verse_length_cv(verses: Sequence[str], unit: str = "letters") -> float:
    """Coefficient of variation of verse lengths (std / mean).

    unit:  "letters" (default) measures rasm-skeleton length per verse;
           "words"   measures whitespace-split word count per verse.

    Returns NaN if fewer than 3 verses or mean ≤ 0.
    """
    if unit not in ("letters", "words"):
        raise ValueError(f"unit must be 'letters' or 'words', got {unit!r}")
    if len(verses) < 3:
        return float("nan")
    if unit == "letters":
        lens = np.asarray(
            [len(normalize_arabic_letters_only(v)) for v in verses],
            dtype=float,
        )
    else:
        lens = np.asarray(
            [len(v.split()) for v in verses],
            dtype=float,
        )
    if lens.size < 3 or lens.mean() <= 0:
        return float("nan")
    return float(lens.std(ddof=1) / lens.mean())


def d_info(letter_skeleton: str, contraction: float = 0.18) -> float:
    """IFS information dimension of letter-frequency distribution.

    d_info = H_nats(p) / log(1/c)
    where p is the empirical frequency over ARABIC_28 letters and c is the
    canonical contraction factor (0.18 from exp182).

    Returns NaN if input has fewer than 100 letters.
    """
    if len(letter_skeleton) < 100:
        return float("nan")
    counts = Counter(letter_skeleton)
    total = sum(counts[c] for c in ARABIC_28)
    if total == 0:
        return float("nan")
    p = np.array([counts.get(c, 0) / total for c in ARABIC_28])
    p_nz = p[p > 0]
    H_nats = float(-(p_nz * np.log(p_nz)).sum())
    return H_nats / log(1.0 / contraction)


# ----- Higuchi fractal dimension --------------------------------------------
def higuchi_fd(series: Sequence[float], k_max: int = 16) -> float:
    """Higuchi (1988) fractal dimension on a 1-D series.

    series:  the verse-length sequence (or any 1-D series of length ≥ 32).
    k_max:   capped at min(k_max, N // 4).

    Returns NaN if the series is too short.
    """
    x = np.asarray(series, dtype=float)
    N = x.size
    if N < 32:
        return float("nan")
    k_max = max(2, min(k_max, N // 4))
    Lk = []
    log_inv_k = []
    for k in range(1, k_max + 1):
        Lm = []
        for m in range(k):
            n = (N - m - 1) // k
            if n < 1:
                continue
            idx = m + np.arange(n + 1) * k
            seg = x[idx]
            length = np.abs(np.diff(seg)).sum()
            length = length * (N - 1) / (n * k)
            Lm.append(length)
        if not Lm:
            continue
        Lk.append(np.mean(Lm))
        log_inv_k.append(log(1.0 / k))
    if len(Lk) < 4:
        return float("nan")
    log_L = np.log(Lk)
    slope = np.polyfit(log_inv_k, log_L, 1)[0]
    return float(slope)


# ----- Multifractal spectrum width (MFDFA, simplified) ----------------------
def delta_alpha_mfdfa(series: Sequence[float],
                      q_values: Sequence[float] = None,
                      poly_order: int = 2) -> float:
    """Multifractal DFA spectrum width Δα = α_max - α_min.

    Implements the standard Kantelhardt et al. (2002) MFDFA on the input
    1-D series at log-spaced scales, fitting a polynomial of `poly_order`
    in each segment, computing F_q(s) for each q, then h(q), τ(q), α(q).

    Returns NaN if the series is too short for a stable fit.
    """
    x = np.asarray(series, dtype=float)
    N = x.size
    if N < 64:
        return float("nan")
    if q_values is None:
        q_values = np.arange(-5, 5.5, 0.5)
    q_values = np.asarray([q for q in q_values if abs(q) > 1e-6], dtype=float)
    Y = np.cumsum(x - x.mean())
    s_min = max(8, int(N // 32))
    s_max = max(s_min + 4, N // 4)
    n_scales = 12
    scales = np.unique(np.round(np.geomspace(s_min, s_max, n_scales)).astype(int))
    if scales.size < 4:
        return float("nan")

    log_F = {q: [] for q in q_values}
    log_s = []
    for s in scales:
        Ns = N // s
        if Ns < 4:
            continue
        # forward + reverse segmentation for stability
        F2_segs = []
        for direction in (0, 1):
            for v in range(Ns):
                if direction == 0:
                    seg = Y[v*s:(v+1)*s]
                else:
                    seg = Y[N - (v+1)*s : N - v*s]
                t = np.arange(s)
                coeffs = np.polyfit(t, seg, poly_order)
                trend = np.polyval(coeffs, t)
                F2_segs.append(np.mean((seg - trend) ** 2))
        F2_segs = np.asarray(F2_segs)
        if F2_segs.size == 0 or np.any(F2_segs <= 0):
            F2_segs = F2_segs[F2_segs > 0]
            if F2_segs.size == 0:
                continue
        log_s.append(log(s))
        for q in q_values:
            Fq = np.mean(F2_segs ** (q / 2.0)) ** (1.0 / q)
            log_F[q].append(log(Fq) if Fq > 0 else np.nan)
    if len(log_s) < 4:
        return float("nan")
    log_s = np.asarray(log_s)
    h_q = []
    for q in q_values:
        y = np.asarray(log_F[q])
        if np.any(~np.isfinite(y)):
            return float("nan")
        slope = np.polyfit(log_s, y, 1)[0]
        h_q.append(slope)
    h_q = np.asarray(h_q)
    tau_q = q_values * h_q - 1.0
    # α(q) = dτ/dq via numerical gradient
    alpha = np.gradient(tau_q, q_values)
    if np.any(~np.isfinite(alpha)):
        return float("nan")
    return float(alpha.max() - alpha.min())


# ============================================================================
# Layer C — tampering forensics
# ============================================================================
def bigram_histogram(skeleton: str) -> Counter:
    """Bigram histogram of a letter-only skeleton (no spaces)."""
    return Counter(skeleton[i:i+2] for i in range(len(skeleton) - 1))


def bigram_shift_delta(a: str, b: str) -> float:
    """L1 / 2 distance between two bigram histograms.

    Locked theorem (F69): a single-letter substitution causes Δ ∈ [1, 2].
    A multi-letter substitution of k letters causes Δ ≤ 2k.
    """
    h_a = bigram_histogram(a)
    h_b = bigram_histogram(b)
    keys = set(h_a) | set(h_b)
    return float(sum(abs(h_a.get(k, 0) - h_b.get(k, 0)) for k in keys)) / 2.0


def _gzip_size(data: bytes) -> int:
    """Length of gzip-compressed bytes."""
    return len(gzip.compress(data, compresslevel=6))


def gzip_ncd(a: str, b: str) -> float:
    """Normalised compression distance using gzip.

    NCD(a,b) = (C(a+b) - min(C(a), C(b))) / max(C(a), C(b))

    Range: [0, 1+]. NCD ≈ 0 means a, b are highly compressible together
    (i.e., same content). NCD close to 1 means they share little structure.
    """
    if not a or not b:
        return float("nan")
    ba = a.encode("utf-8")
    bb = b.encode("utf-8")
    Ca = _gzip_size(ba)
    Cb = _gzip_size(bb)
    Cab = _gzip_size(ba + bb)
    return (Cab - min(Ca, Cb)) / max(Ca, Cb)


# ============================================================================
# Composite scoring helper — distance into match%
# ============================================================================
def match_pct(your_value: float, quran_value: float, tolerance: float) -> float:
    """Convert a per-axis (input, reference) pair into a 0-100% match score.

    match_pct = max(0, 100 * (1 - |you - quran| / tolerance))

    The tolerance is an axis-specific natural scale used to map distance
    into a percentage; it is NOT a pre-registered cutoff. See
    constants.DISPLAY_TOLERANCES.
    """
    if not (np.isfinite(your_value) and np.isfinite(quran_value) and tolerance > 0):
        return float("nan")
    gap = abs(your_value - quran_value)
    raw = 1.0 - gap / tolerance
    return max(0.0, min(100.0, 100.0 * raw))


__all__ = [
    "pooled_H_EL_pmax", "verse_length_cv", "d_info",
    "higuchi_fd", "delta_alpha_mfdfa",
    "bigram_histogram", "bigram_shift_delta", "gzip_ncd",
    "match_pct",
]
