"""Regression test for Finding F1 - exp138 Brown-Stouffer formula correction.

The buggy formula `Z = sum_z / sqrt(K^2 / sum_R)` is the Cheverud / Li-Ji
M_eff intended for *Bonferroni* family-wise alpha adjustment, NOT for
combining z-scores. The correct Brown-Stouffer denominator under correlated
axes is sqrt(Var(sum_z)) = sqrt(sum_R), since for z_i ~ N(0, 1) with pairwise
correlation R_ij we have Var(sum_i z_i) = sum_{i, j} R_{i, j} = sum_R.

This test verifies (a) the algebraic identity at the iid endpoint where the
two formulas agree, (b) the divergence under perfect correlation, (c) the
Monte Carlo variance under correlated draws, and (d) the source code of
exp138/run.py uses the corrected divisor at both call-sites.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest


def _buggy_brown_z(sum_z: float, K: int, sum_R: float) -> float:
    K_eff = (K * K) / max(sum_R, 1e-12)
    return sum_z / math.sqrt(K_eff)


def _correct_brown_z(sum_z: float, K: int, sum_R: float) -> float:
    return sum_z / math.sqrt(max(sum_R, 1e-12))


def test_iid_axes_both_formulas_agree() -> None:
    """At sum_R = K (orthogonal axes) buggy and correct formulas coincide."""
    K = 8
    sum_R = float(K)
    sum_z = 16.0
    assert math.isclose(
        _buggy_brown_z(sum_z, K, sum_R),
        _correct_brown_z(sum_z, K, sum_R),
        rel_tol=1e-12,
    )


def test_perfectly_correlated_axes_buggy_inflates_by_factor_K() -> None:
    """At sum_R = K^2 the buggy formula returns sum_z (Var = K^2);
    the correct formula returns sum_z / K (Var = 1)."""
    K = 8
    sum_R = float(K * K)
    sum_z = 16.0
    assert math.isclose(_buggy_brown_z(sum_z, K, sum_R), sum_z, rel_tol=1e-12)
    assert math.isclose(_correct_brown_z(sum_z, K, sum_R), sum_z / K, rel_tol=1e-12)


def test_exp138_empirical_quran_corrected_z_matches_2_651() -> None:
    """With sum_R = 36.667 (from exp138 receipt) and Quran sum_z = 16.054
    the corrected Brown-Stouffer Z must be 2.651, not 12.149."""
    K = 8
    sum_R = 36.66667450091043
    sum_z = 16.054118527247164  # = quran_Z_raw * sqrt(K) from receipt
    assert _correct_brown_z(sum_z, K, sum_R) == pytest.approx(2.651, abs=0.01)
    assert _buggy_brown_z(sum_z, K, sum_R) == pytest.approx(12.149, abs=0.01)


def test_monte_carlo_correct_formula_has_unit_variance_under_correlation() -> None:
    """Simulate K = 8 correlated z's with rho = 0.5; correct formula Z must
    be N(0, 1) (var ~ 1); buggy formula must be inflated (var > 2)."""
    rng = np.random.default_rng(20260429)
    K = 8
    rho = 0.5
    n_sims = 30_000
    R = rho * np.ones((K, K)) + (1.0 - rho) * np.eye(K)
    sum_R = float(R.sum())
    L = np.linalg.cholesky(R)
    z = rng.standard_normal((n_sims, K)) @ L.T
    sum_z = z.sum(axis=1)
    correct = sum_z / math.sqrt(sum_R)
    buggy = sum_z / math.sqrt((K * K) / sum_R)
    assert correct.var() == pytest.approx(1.0, abs=0.05), (
        f"correct Brown-Stouffer Z should have Var = 1 under H0, "
        f"got Var = {correct.var():.4f}"
    )
    assert buggy.var() > 2.0, (
        f"buggy formula should be inflated under correlation, "
        f"got Var = {buggy.var():.4f}"
    )


def test_exp138_source_uses_sum_R_divisor() -> None:
    """Source-code regression: exp138/run.py must divide Z_brown by
    sqrt(sum_R) at both the actual Quran site (line ~255) and the
    permutation null site (line ~304)."""
    src = (
        Path(__file__).resolve().parent.parent
        / "experiments"
        / "exp138_Quran_Footprint_Joint_Z"
        / "run.py"
    )
    text = src.read_text(encoding="utf-8")
    assert "Z_brown = Z_sums / math.sqrt(max(sum_R, 1e-12))" in text, (
        "exp138 actual-Z line must use sqrt(sum_R) divisor, not sqrt(K_eff)"
    )
    assert "M_perm.sum(axis=1) / math.sqrt(max(sum_R, 1e-12))" in text, (
        "exp138 permutation-null line must use sqrt(sum_R) divisor"
    )
    assert "Z_brown = Z_sums / math.sqrt(K_eff)" not in text, (
        "buggy formula 'Z_brown = Z_sums / math.sqrt(K_eff)' must be removed"
    )


def test_exp141_helper_uses_sum_R_divisor() -> None:
    """exp141 propagation: stouffer_z_brown helper must divide by sqrt(sumR)."""
    src = (
        Path(__file__).resolve().parent.parent
        / "experiments"
        / "exp141_QFootprint_Dual_Pool"
        / "run.py"
    )
    text = src.read_text(encoding="utf-8")
    assert "math.sqrt(max(sumR, 1e-12))" in text, (
        "exp141 stouffer_z_brown must divide by sqrt(sumR)"
    )
    assert "z_subset_row.sum() / math.sqrt(K_eff)" not in text, (
        "exp141 buggy formula 'z_subset_row.sum() / math.sqrt(K_eff)' must be removed"
    )


def test_exp143_helper_uses_sum_R_divisor() -> None:
    """exp143 propagation: stouffer_z_brown helper must divide by sqrt(sumR)."""
    src = (
        Path(__file__).resolve().parent.parent
        / "experiments"
        / "exp143_QFootprint_Sharpshooter_Audit"
        / "run.py"
    )
    text = src.read_text(encoding="utf-8")
    assert "math.sqrt(max(sumR, 1e-12))" in text, (
        "exp143 stouffer_z_brown must divide by sqrt(sumR)"
    )
    assert "z_subset_row.sum() / math.sqrt(K_eff)" not in text, (
        "exp143 buggy formula 'z_subset_row.sum() / math.sqrt(K_eff)' must be removed"
    )
