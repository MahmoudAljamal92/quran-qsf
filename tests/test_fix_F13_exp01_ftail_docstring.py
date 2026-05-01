"""Regression test for Finding F13 - exp01_ftail interpretation comments
must correctly identify the locked Phi_M_hotelling_T2 = 3557.34 as the
classical TWO-SAMPLE Hotelling T^2 (not the one-sample sum-of-Mahalanobis,
which is ~5239).

The bug was a docstring/comment swap: the prior "interpretation" array said
the one_sample sum_of_maha_sq "reproduces the 3557.34 scalar" when in fact
the two_sample T^2 reproduces it; the print label "(locked 3557.34)" was
attached to the one_sample value (5239) instead of the two_sample value.

This test does NOT change any numerical result; it only verifies the
narrative is corrected.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent


def test_exp01_ftail_source_attributes_locked_t2_to_two_sample() -> None:
    """The interpretation array in exp01_ftail/run.py must say two_sample T^2
    reproduces the locked 3557.34, NOT the one_sample sum-of-Mahalanobis."""
    src = _REPO_ROOT / "experiments" / "exp01_ftail" / "run.py"
    text = src.read_text(encoding="utf-8")
    assert "two_sample T^2" in text and "reproduces" in text and "3557.34" in text, (
        "exp01_ftail must explicitly state two_sample T^2 reproduces locked 3557.34"
    )
    assert "F13 fix" in text, (
        "F13 fix marker must remain in source for traceability"
    )
    assert "one_sample sum_of_maha_sq reproduces the 3557.34" not in text, (
        "Buggy comment 'one_sample sum_of_maha_sq reproduces the 3557.34' "
        "must be removed."
    )


def test_exp01_ftail_print_label_for_one_sample_is_corrected() -> None:
    """The print label '(locked 3557.34)' must NOT be attached to the
    one_sample sum_of_maha_sq line. The corrected version states explicitly
    that the one-sample number is a different statistic."""
    src = _REPO_ROOT / "experiments" / "exp01_ftail" / "run.py"
    text = src.read_text(encoding="utf-8")
    assert 'NOT the locked 3557.34' in text, (
        "exp01_ftail print label for one-sample sum-of-Mahalanobis must "
        "explicitly state it is NOT the locked 3557.34."
    )


def test_exp01_ftail_receipt_two_sample_matches_locked() -> None:
    """If the receipt exists, two_sample T^2 must match locked 3557.34
    within numerical precision and the one_sample sum must NOT match it."""
    receipt = (
        _REPO_ROOT
        / "results"
        / "experiments"
        / "exp01_ftail"
        / "exp01_ftail.json"
    )
    if not receipt.exists():
        pytest.skip("exp01_ftail receipt not present; run experiment first.")
    r = json.loads(receipt.read_text(encoding="utf-8"))
    locked = r["locked_baseline"]["Phi_M_hotelling_T2"]
    two_sample_t2 = r["two_sample_hotelling_T2_pooled_cov"]["T2"]
    one_sample_sum = r[
        "one_sample_sum_of_maha_sq_against_fixed_mu_ctrl"
    ]["sum_maha_sq"]
    assert abs(two_sample_t2 - locked) < 1e-3, (
        f"two_sample T^2 = {two_sample_t2} should match locked = {locked}"
    )
    assert abs(one_sample_sum - locked) > 100.0, (
        f"one_sample sum = {one_sample_sum} should NOT match locked = "
        f"{locked} (difference > 100)"
    )
