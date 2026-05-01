# expP11_brown_empirical_corr — Pre-Registration

**Frozen**: 2026-04-26
**Author**: v7.9-cand patch E sprint
**Status**: pre-registered before any data look

## Background

`audit_patch.json::patch_3_brown_synthesis` reports the joint Brown p
for the 4-channel combo (EL + R3 + J1 + Hurst) as **2.95·10⁻⁵** under a
*conservative* off-diagonal correlation prior of ρ = 0.5 in a 4×4
covariance Σ. Brown's method (1975) is exact when the empirical
correlation matrix is plugged in. This experiment computes the empirical
4×4 correlation matrix from the control corpora and re-runs the Brown
synthesis to deliver a **tighter** (or equal) joint p.

## Hypothesis

**H1**: With empirical Σ, Brown joint p ≤ 2.95·10⁻⁵ (one-sided non-decrease
in stringency vs the conservative prior). If empirical Σ implies more
positive cross-channel correlation, p will *loosen*; if less (or
negative), p will *tighten*.

## Pre-registered decision rule

| Outcome | Verdict |
|---|---|
| p_empirical ≤ 1·10⁻⁶ | `TIGHTENED_STRONG` |
| 1·10⁻⁶ < p_empirical ≤ 2.95·10⁻⁵ | `TIGHTENED` |
| 2.95·10⁻⁵ < p_empirical ≤ 1·10⁻⁴ | `LOOSENED_MILD` |
| p_empirical > 1·10⁻⁴ | `LOOSENED_STRONG` (qualifies §4.41.7 claim) |

## Frozen protocol

1. Compute per-corpus EL, R3 (path-minimality z-score), J1 (Mushaf-ordering
   permutation deviation), Hurst exponent on each control corpus that has
   all 4 channels available.
2. Compute the 4×4 Pearson correlation matrix R from the per-corpus
   z-scored channel values (excluding Quran).
3. Convert to Σ via diagonal of unit variances.
4. Plug into Brown synthesis:
   `c = (2k - 2·tr(R²) + tr(R)²) / (2k)` ... [Brown 1975]
5. Compare Fisher chi-squared `−2·Σ ln(p_i)` to a chi² with effective df
   `2·c`.
6. Output empirical p, conservative p, and ratio.

## Frozen reporting

Output JSON contains:
- `R_empirical`: 4×4 correlation matrix from controls
- `R_conservative`: 4×4 with ρ=0.5 off-diagonals (sanity)
- `c_empirical`, `c_conservative`: Brown scaling constants
- `p_joint_empirical`, `p_joint_conservative`
- `ratio` (empirical / conservative)
- `verdict`

## Reproduction

```powershell
python -X utf8 -u experiments\expP11_brown_empirical_corr\run.py
```
