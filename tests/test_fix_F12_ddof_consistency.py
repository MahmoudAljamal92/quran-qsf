"""Regression test for Finding F12 - cross-corpus z-score denominators
must use unbiased sample std (ddof=1), not biased population std (ddof=0).

For an N-element non-Quran cluster, ddof=0 std is biased downward by factor
sqrt((N-1)/N), inflating |z| by sqrt(N/(N-1)). For N=10, |z| inflation is
~5.4 %; for N=11, ~4.9 %. Most "5σ" thresholds in this project have margin
much larger than 5 %, so verdicts do not flip — but the convention should
be consistent (ddof=1 across all cross-corpus z-scores).

Sites fixed:
- experiments/exp122_zipf_equation_hunt/run.py:293 (Zipf-class candidate scoring)
- experiments/exp125b_unified_quran_coordinate_lda/run.py:137 (full-pool LDA z)
- experiments/exp125b_unified_quran_coordinate_lda/run.py:253 (LOO LDA z)

Sites intentionally left at ddof=0 (per minimal-diff guardrail):
- experiments/exp138_Quran_Footprint_Joint_Z/run.py:144 (per-unit verse-length
  CV, where the unit's verses ARE the population for that unit)
- experiments/exp125b_unified_quran_coordinate_lda/run.py:185 (standardisation
  step before LDA fitting, methodologically ambiguous)
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent


def test_ddof_inflation_factor_n11() -> None:
    """For N=11 non-Quran corpora, ddof=1 std is sqrt(11/10) ≈ 1.0488×
    larger than ddof=0; |z| therefore drops by 1/1.0488 ≈ 0.953."""
    n = 11
    inflation = math.sqrt(n / (n - 1))
    assert inflation == pytest.approx(1.04881, abs=1e-4)
    z_buggy = 5.39
    z_corrected = z_buggy / inflation
    assert z_corrected == pytest.approx(5.139, abs=0.01)
    assert z_corrected > 5.0, (
        "Even after ddof=1 correction, exp122 sqrt(H_EL) Quran |z|=5.14 "
        "should still exceed the 5σ threshold."
    )


def test_exp122_source_uses_unbiased_variance() -> None:
    src = _REPO_ROOT / "experiments" / "exp122_zipf_equation_hunt" / "run.py"
    text = src.read_text(encoding="utf-8")
    assert "(n_o - 1)" in text, (
        "exp122 must use (n_o - 1) divisor for unbiased variance"
    )
    assert "/ len(others)" not in text or text.count("/ len(others)") <= 1, (
        "exp122 must not divide squared deviations by len(others) (biased ddof=0)"
    )


def test_exp125b_source_uses_ddof_1_for_cross_corpus_z() -> None:
    src = _REPO_ROOT / "experiments" / "exp125b_unified_quran_coordinate_lda" / "run.py"
    text = src.read_text(encoding="utf-8")
    assert text.count("np.std(non_quran, ddof=1)") >= 1, (
        "exp125b project_and_score must use ddof=1"
    )
    assert text.count("np.std(non_quran_full, ddof=1)") >= 1, (
        "exp125b LOO loop must use ddof=1"
    )
    assert "np.std(non_quran, ddof=0)" not in text, (
        "Buggy ddof=0 z-score denominator removed from project_and_score"
    )
    assert "np.std(non_quran_full, ddof=0)" not in text, (
        "Buggy ddof=0 z-score denominator removed from LOO loop"
    )


def test_exp125b_standardisation_left_as_documented() -> None:
    """Per minimal-diff guardrail, the standardisation step at sigma_full
    is documented as intentionally ddof=0 (methodologically ambiguous,
    not a cross-corpus z-score)."""
    src = _REPO_ROOT / "experiments" / "exp125b_unified_quran_coordinate_lda" / "run.py"
    text = src.read_text(encoding="utf-8")
    assert "sigma_full = X.std(axis=0, ddof=0)" in text, (
        "Standardisation step ddof=0 is intentionally preserved (out of "
        "F12 minimal-diff scope)"
    )
