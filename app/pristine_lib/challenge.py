"""challenge.py — the Quran Extremum Challenge.

For ANY input text — Quran, classical poetry, modern Arabic, anything in
Arabic rasm — this module asks the question:

   *Does your text reach the Quran's locked extremum thresholds, and
    where can it not even be tested at the length you provided?*

Every threshold is locked from the published findings in docs/RANKED_FINDINGS.md
and docs/THE_QURAN_FINDINGS.md.  Every threshold has an explicit length
floor below which the test is not run.  Nothing is fitted to the input;
nothing is selected post-hoc.

Three categories of test are returned:

  1. CLASS thresholds (5 axes: F75, p_max, C_Omega, H_EL, D_max)
     - Pass/Fail at locked Quran-corpus values.
     - These are *cheap to satisfy* with monorhyme classical poetry, so
       passing them is "consistent with the rhymed-scripture class", not
       "Quran-extremum".
     - Reported with a length-matched percentile against actual Quran
       surahs of similar size (per_surah_ref).

  2. F87 PARTIAL joint test (single-text, requires N >= 64 verses)
     - HFD in [0.95, 1.00]   AND
     - Delta_alpha >= 0.50
     - cos_short_long requires a multi-surah corpus, NOT a single text.
       It is reported as "cannot test on single text" with an explanation.
     - Passing the partial joint at N >= 64 in a single text is the
       strongest single-text Quran-extremum claim available.

  3. CORPUS-LEVEL claims (F67 C_Omega rank-1, F76 H_EL<1bit, F79 D_max>=3.5,
     F87 full joint, F89 Mushaf permutation extremum)
     - These compare a WHOLE TRADITION to other whole traditions.
     - They are reported with explicit "requires multi-surah corpus" gates
       and cannot be tested on a single text.

Outputs are pure data (dicts).  Rendering is in pristine.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import log2
from typing import Dict, List, Optional, Sequence

import numpy as np

from . import metrics
from .constants import ALPHABET_SIZE, LOG2_A
from .normalize import normalize_arabic_letters_only
from .per_surah_ref import (
    SimilarLengthRef, percentile_in_similar_length,
)


# ---------------------------------------------------------------------------
# Locked thresholds.  Provenance for every number is in the comment.
# Update only by editing this file *and* the corresponding receipt; never
# from input text.
# ---------------------------------------------------------------------------
# IMPORTANT: statistic convention.
#
# The Quran project publishes TWO DIFFERENT locked statistics that both
# answer "what's the Quran's value for axis X?", and they are legitimately
# different quantities (confirmed in docs/THE_QURAN_FINDINGS.md:34-51 and
# docs/RANKED_FINDINGS.md:268 for F56 p_max_pooled = 0.5010):
#
#   (A) PER-CHAPTER MEDIAN — compute the axis value separately on each of
#       the 114 surahs, then take the median.  F76 H_EL = 0.9685 and F48
#       p_max = 0.7273 quoted in THE_QURAN_FINDINGS.md ARE per-chapter
#       medians.  F75 = 5.316 and F79 D_max = 3.84 derive from these.
#
#   (B) WHOLE-CORPUS POOLED — pool all 6,236 verse-finals into one bag
#       and compute entropy / modal fraction.  F56 p_max_pooled = 0.5010
#       (2.04× margin over next corpus) is locked from exp95l.  Pooled
#       H_EL ≈ 2.47 bits (implied by p_max_pooled ≈ 0.50).
#
# For THIS APP, the user's input is treated as one candidate "chapter"
# and compared against the PER-CHAPTER MEDIAN basis (A) — that is what
# the `pooled_H_EL_pmax(input_verses)` call in metrics.py actually
# computes: "if this input were a surah, what would its axis values be?"
#
# Previously (before 2026-05-02 review) the app silently used basis (A)
# in challenge.py while the audit computed basis (B) from the full
# corpus, producing the three-way mismatch the reviewer flagged.  That
# is now fixed: both code paths state their basis explicitly, and the
# audit reports BOTH statistics.
QURAN_LOCKED: Dict[str, float] = {
    # axis:        per-chapter MEDIAN value (basis A)
    "F75":         5.316,    # F75 invariant per-chapter; exp122
    "p_max":       0.7273,   # F48 per-chapter median; THE_QURAN_FINDINGS:35
    "C_Omega":     0.7985,   # F67 per-chapter median; exp115
    "H_EL":        0.9685,   # F76 per-chapter median; THE_QURAN_FINDINGS:34
    "D_max":       3.84,     # F79 per-chapter median; exp124c
    "HFD":         0.965,    # F87 axis 1; mean per-surah HFD (exp75)
    "Delta_alpha": 0.510,    # F87 axis 2; pool mean (exp97)
    "cos_short_long": 0.10,  # F87 axis 3 floor (corpus-level, exp101)
    # R_R (Rhyme-Rhythm Product, 2026-05-02 post-review addition).
    # R_R = p_max × verse_length_CV_letters, the joint invariant proposed
    # by the reviewer: captures "high rhyme concentration AND non-trivial
    # verse-length variation simultaneously", a region of (rhyme, rhythm)
    # space that classical metered poetry (high p_max, low CV) and modern
    # prose (low p_max, low CV) both FAIL to enter.  Empirical Quran
    # per-surah distribution (all 114 surahs):
    #   min = 0.077, p10 = 0.153, median = 0.305, p90 = 0.531, max = 1.394.
    # Works at every N ≥ 3 — no length gate needed beyond that.
    "R_R":         0.305,    # per-surah median R_R across 114 Quran surahs
}

# Whole-corpus pooled values, for cross-check display only.  These are
# NOT used as thresholds — they're shown in the audit report so the user
# can see both legitimate locked numbers side by side.
QURAN_LOCKED_POOLED: Dict[str, float] = {
    "p_max":   0.5010,   # F56 pooled (exp95l); 2.04× margin over runner-up.
    "H_EL":    2.468,    # implied by pooled p_max ≈ 0.50 on 28-letter alphabet.
}

# Pass thresholds.  Every threshold is published, not derived from the input.
# class-pass = "inside the rhymed-scripture class envelope"
# strict-pass = "matches Quran's locked extremum value"
THRESHOLDS = {
    "F75":     {"class_pass": (4.81, 5.92),  # CV 7% band around 5.316 (F84)
                "strict_pass": (5.20, 5.42),  # CV 1.94% band (F75 corpus)
                "min_n": 5},
    "p_max":   {"class_pass": (0.50, 1.0),    # F48 class floor 0.5
                "strict_pass": (0.73, 1.0),   # corpus-median (F48)
                "min_n": 3},
    "C_Omega": {"class_pass": (0.43, 1.0),    # F67 cross-tradition floor
                "strict_pass": (0.79, 1.0),   # F67 Quran rank-1 value
                "min_n": 5},
    "H_EL":    {"class_pass": (0.0, 1.50),    # weak — many surahs are < 1.5
                "strict_pass": (0.0, 1.0),    # F76 Quran corpus-aggregate
                "min_n": 5},
    "D_max":   {"class_pass": (3.0, LOG2_A),  # weak alphabet floor
                "strict_pass": (3.5, LOG2_A), # F79 alphabet-corrected floor
                "min_n": 5},
    "HFD":     {"class_pass": (0.90, 1.05),
                "strict_pass": (0.95, 1.00),  # F87 axis 1
                "min_n": 32},
    "Delta_alpha": {"class_pass": (0.30, 2.0),
                    "strict_pass": (0.50, 2.0),  # F87 axis 2
                    "min_n": 64},
    # R_R bands derived from the empirical Quran per-surah distribution.
    # Class floor 0.10 safely sits between modern prose (~0.09) and
    # Quranic min (0.077); we set class at 0.10 to mean "inside the
    # joint rhyme+rhythm corner". Strict floor 0.153 is Quran's own p10 —
    # every Quranic surah above the 10th percentile passes.  Upper
    # bound 2.0 is a theoretical loose ceiling (R_R is unbounded above).
    "R_R":     {"class_pass": (0.10, 2.0),
                "strict_pass": (0.15, 2.0),
                "min_n": 3},
}


# ---------------------------------------------------------------------------
# Result dataclasses.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AxisChallenge:
    axis: str
    locked: float                  # Quran's locked value (target)
    your_value: float              # input text's value
    min_n: int                     # length floor for this axis
    n_input: int                   # input N (verses)
    can_test: bool                 # whether input meets length floor
    class_pass: Optional[bool]     # in class envelope?  None if can_test=False
    strict_pass: Optional[bool]    # at Quran-extremum threshold?  None if can_test=False
    class_band: tuple              # (lo, hi) for class envelope
    strict_band: tuple             # (lo, hi) for strict
    similar_length_ref: Optional[SimilarLengthRef]
    why_blocked: str = ""          # human-readable reason if can_test=False
    unstable: bool = False         # CI flag for short N
    note: str = ""


@dataclass(frozen=True)
class JointF87Challenge:
    """Single-text partial F87 joint: HFD ∈ band AND Δα ≥ floor.

    cos_short_long is the third F87 axis but is corpus-level (centroid of
    short surahs vs long surahs), not single-text.  This is reported
    explicitly so users know the single-text fingerprint is, at best, a
    PARTIAL F87 test.
    """
    can_test: bool                 # input N >= 64
    n_input: int
    hfd_pass: Optional[bool]
    da_pass: Optional[bool]
    hfd_value: float
    da_value: float
    joint_pass: Optional[bool]     # AND of the two
    why_blocked: str = ""
    cos_short_long_status: str = (
        "F87 axis 3 (cos_short_long) is a CORPUS statistic — cosine "
        "distance between the mean feature vector of short surahs and "
        "the mean feature vector of long surahs.  It is not defined for a "
        "single text; submit a multi-surah collection to test it."
    )


@dataclass(frozen=True)
class CorpusLevelClaim:
    """Whole-tradition findings that are NOT testable on a single text."""
    name: str
    requirement: str               # what's needed to test it
    quran_value: str               # the Quran's locked rank/value as a string


@dataclass(frozen=True)
class ChallengeResult:
    n_verses: int
    is_arabic: bool
    axis_results: List[AxisChallenge]
    joint_f87: Optional[JointF87Challenge]
    corpus_only_claims: List[CorpusLevelClaim]
    # Summary roll-ups (computed after the per-axis results are built):
    n_class_passed: int
    n_class_testable: int
    n_strict_passed: int
    n_strict_testable: int
    headline: str                  # one-line plain-English verdict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _verse_lengths(verses: Sequence[str]) -> np.ndarray:
    return np.asarray(
        [len(normalize_arabic_letters_only(v)) for v in verses],
        dtype=float,
    )


def _bias_correction_unstable(M: int, n: int) -> bool:
    """Heuristic: bias correction is non-trivial -> H_EL is unstable."""
    if n <= 0:
        return True
    # Miller-Madow term in bits = (M-1) / (2 N ln 2).  Flag UNSTABLE when
    # the correction exceeds 0.05 bits — meaningfully shifts the value.
    return (M - 1) / (2.0 * n * 0.6931471805599453) > 0.05


def _make_axis(axis: str, your_value: float, n_input: int) -> AxisChallenge:
    cfg = THRESHOLDS[axis]
    locked = QURAN_LOCKED[axis]
    min_n = int(cfg["min_n"])
    can_test = (n_input >= min_n) and np.isfinite(your_value)
    if not can_test:
        return AxisChallenge(
            axis=axis, locked=locked, your_value=your_value,
            min_n=min_n, n_input=n_input,
            can_test=False, class_pass=None, strict_pass=None,
            class_band=cfg["class_pass"], strict_band=cfg["strict_pass"],
            similar_length_ref=None,
            why_blocked=(
                f"requires N ≥ {min_n} verses; your input has N = {n_input}"
                if n_input < min_n
                else "metric returned NaN (likely insufficient data)"
            ),
        )
    cl_lo, cl_hi = cfg["class_pass"]
    st_lo, st_hi = cfg["strict_pass"]
    class_pass = bool(cl_lo <= your_value <= cl_hi)
    strict_pass = bool(st_lo <= your_value <= st_hi)
    # Map H_EL_raw axis name to the per-surah CSV's H_EL_raw column.
    axis_in_csv = {"H_EL": "H_EL_raw"}.get(axis, axis)
    ref = percentile_in_similar_length(axis_in_csv, your_value, n_input)
    return AxisChallenge(
        axis=axis, locked=locked, your_value=your_value,
        min_n=min_n, n_input=n_input,
        can_test=True, class_pass=class_pass, strict_pass=strict_pass,
        class_band=(cl_lo, cl_hi), strict_band=(st_lo, st_hi),
        similar_length_ref=ref,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def run_challenge(verses: Sequence[str], is_arabic: bool = True) -> ChallengeResult:
    """Run the full Extremum Challenge on a list of raw verses.

    `verses` should already be split (one verse per item).  All Arabic
    normalisation is done internally.

    For non-Arabic inputs, this returns an empty challenge with the
    `is_arabic=False` flag set so the UI can explain that the locked
    thresholds (which are defined on the 28-letter Arabic rasm) do not
    apply.
    """
    n_input = len(verses)
    if not is_arabic:
        return ChallengeResult(
            n_verses=n_input, is_arabic=False,
            axis_results=[], joint_f87=None,
            corpus_only_claims=_corpus_level_claims(),
            n_class_passed=0, n_class_testable=0,
            n_strict_passed=0, n_strict_testable=0,
            headline=("Extremum thresholds are defined on the 28-letter Arabic "
                      "rasm.  Your input is not in Arabic script — the "
                      "challenge does not apply."),
        )

    # Class axes -----------------------------------------------------------
    pooled = metrics.pooled_H_EL_pmax(verses, bias_correct=False)
    pooled_mm = metrics.pooled_H_EL_pmax(verses, bias_correct=True)
    H_EL = pooled["H_EL_raw"]
    p_max = pooled["p_max"]
    C_Omega = pooled["C_Omega"]
    F75 = pooled["F75"]
    D_max = pooled["D_max"]

    # Verse-length series for fractal axes.
    lens = _verse_lengths(verses)
    HFD = metrics.higuchi_fd(lens) if lens.size >= 32 else float("nan")
    Da = metrics.delta_alpha_mfdfa(lens) if lens.size >= 64 else float("nan")

    # R_R: Rhyme-Rhythm Product (joint scale-invariant).
    VL_CV_letters = metrics.verse_length_cv(verses, unit="letters")
    R_R = (p_max * VL_CV_letters
           if (np.isfinite(p_max) and np.isfinite(VL_CV_letters))
           else float("nan"))

    axis_results: List[AxisChallenge] = []
    for axis, val in [
        ("R_R", R_R),  # joint axis first (it's the new headline discriminator)
        ("F75", F75), ("p_max", p_max), ("C_Omega", C_Omega),
        ("H_EL", H_EL), ("D_max", D_max),
        ("HFD", HFD), ("Delta_alpha", Da),
    ]:
        ar = _make_axis(axis, val, n_input)
        # Mark UNSTABLE when Miller-Madow correction is large for H_EL-derived
        # axes at small N.
        if axis in ("H_EL", "C_Omega", "F75", "D_max") and ar.can_test:
            unstable = _bias_correction_unstable(
                pooled["n_distinct_finals"], pooled["n_finals"])
            note = ""
            if unstable:
                gap = abs(pooled["H_EL_mm"] - pooled["H_EL_raw"])
                note = (f"H_EL has small-N bias of {gap:.3f} bits "
                        f"(Miller-Madow corrected = {pooled['H_EL_mm']:.3f}). "
                        "Treat this axis as UNSTABLE at this length.")
            ar = AxisChallenge(
                axis=ar.axis, locked=ar.locked, your_value=ar.your_value,
                min_n=ar.min_n, n_input=ar.n_input,
                can_test=ar.can_test, class_pass=ar.class_pass,
                strict_pass=ar.strict_pass,
                class_band=ar.class_band, strict_band=ar.strict_band,
                similar_length_ref=ar.similar_length_ref,
                why_blocked=ar.why_blocked,
                unstable=unstable, note=note,
            )
        axis_results.append(ar)

    # Single-text partial F87 joint --------------------------------------
    if n_input >= 64 and np.isfinite(HFD) and np.isfinite(Da):
        hfd_lo, hfd_hi = THRESHOLDS["HFD"]["strict_pass"]
        da_lo, _da_hi = THRESHOLDS["Delta_alpha"]["strict_pass"]
        hfd_pass = bool(hfd_lo <= HFD <= hfd_hi)
        da_pass = bool(Da >= da_lo)
        joint = JointF87Challenge(
            can_test=True, n_input=n_input,
            hfd_pass=hfd_pass, da_pass=da_pass,
            hfd_value=float(HFD), da_value=float(Da),
            joint_pass=bool(hfd_pass and da_pass),
        )
    else:
        why = (f"requires N ≥ 64 verses; your input has N = {n_input}"
               if n_input < 64 else
               "fractal axes returned NaN (likely degenerate verse-length series)")
        joint = JointF87Challenge(
            can_test=False, n_input=n_input,
            hfd_pass=None, da_pass=None,
            hfd_value=float(HFD), da_value=float(Da),
            joint_pass=None, why_blocked=why,
        )

    # Roll-up ------------------------------------------------------------
    n_class_testable = sum(1 for a in axis_results if a.can_test)
    n_class_passed = sum(1 for a in axis_results if a.can_test and a.class_pass)
    n_strict_testable = n_class_testable
    n_strict_passed = sum(1 for a in axis_results if a.can_test and a.strict_pass)

    headline = _build_headline(n_input, n_class_passed, n_class_testable,
                               n_strict_passed, n_strict_testable, joint)

    return ChallengeResult(
        n_verses=n_input, is_arabic=True,
        axis_results=axis_results,
        joint_f87=joint,
        corpus_only_claims=_corpus_level_claims(),
        n_class_passed=n_class_passed,
        n_class_testable=n_class_testable,
        n_strict_passed=n_strict_passed,
        n_strict_testable=n_strict_testable,
        headline=headline,
    )


def _build_headline(n: int, cp: int, ct: int, sp: int, st: int,
                    joint: JointF87Challenge) -> str:
    if ct == 0:
        return (f"At N = {n} verses, no extremum axis is testable. "
                "Provide at least 5 verses to begin testing.")
    parts = [f"At N = {n} verses: passes {cp}/{ct} class envelopes, "
             f"{sp}/{st} strict Quran-extremum thresholds."]
    if joint.can_test:
        if joint.joint_pass:
            parts.append("F87 partial joint (HFD + Δα): PASSES — "
                         "single-text fingerprint matches the Quran's locked extremum.")
        else:
            failed = []
            if joint.hfd_pass is False:
                failed.append(f"HFD = {joint.hfd_value:.3f} ∉ [0.95, 1.00]")
            if joint.da_pass is False:
                failed.append(f"Δα = {joint.da_value:.3f} < 0.50")
            parts.append("F87 partial joint: FAILS on " + ", ".join(failed) + ".")
    else:
        parts.append("F87 partial joint cannot be tested at this length "
                     "(needs N ≥ 64).")
    return "  ".join(parts)


def _corpus_level_claims() -> List[CorpusLevelClaim]:
    """The whole-tradition findings that need a multi-surah corpus."""
    return [
        CorpusLevelClaim(
            name="F67 C_Ω rank-1 across 12 corpora",
            requirement="A whole tradition (≥ 100 surahs / chapters / poems) "
                        "in any rhymed alphabetic script.",
            quran_value="C_Ω = 0.7985 (rank 1; gap 0.36 to runner-up Rigveda).",
        ),
        CorpusLevelClaim(
            name="F76 H_EL < 1 bit at corpus aggregate",
            requirement="A whole tradition pooled across all its rhymed units.",
            quran_value="H_EL = 0.9685 bits (only corpus < 1 bit; runner-up "
                        "1.121 bits).",
        ),
        CorpusLevelClaim(
            name="F79 D_max ≥ 3.5 bits alphabet-corrected",
            requirement="A whole tradition in any of 6+ tested alphabets.",
            quran_value="D_max = 3.84 bits (rank 1; gap 0.57 to runner-up).",
        ),
        CorpusLevelClaim(
            name="F87 full joint (HFD + Δα + cos_short_long)",
            requirement="A multi-surah corpus with ≥ 10 short and ≥ 10 long "
                        "surahs (so the cos_short_long centroid split is "
                        "well-defined).",
            quran_value="HFD = 0.965, Δα = 0.51, cos_short_long = 0.21 "
                        "(LOO-z = 22.59 vs 6 other Arabic-rasm corpora).",
        ),
        CorpusLevelClaim(
            name="F89 Mushaf permutation extremum",
            requirement="A whole 114-surah collection arranged in a fixed "
                        "order; tested against 10⁷ random permutations.",
            quran_value="Mushaf order is rank 1 of 10⁷ permutations on the "
                        "joint F81 + F82 statistic (empirical p ≤ 10⁻⁷).",
        ),
    ]


__all__ = [
    "AxisChallenge", "JointF87Challenge", "CorpusLevelClaim", "ChallengeResult",
    "QURAN_LOCKED", "THRESHOLDS",
    "run_challenge",
]
