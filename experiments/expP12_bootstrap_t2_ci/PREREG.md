# expP12_bootstrap_t2_ci — Pre-Registration

**Frozen**: 2026-04-26
**Author**: v7.9-cand patch E sprint
**Status**: pre-registered before any data look

## Background

`expP7_phi_m_full_quran` reports the headline `T² = 3 685.45` as a point
estimate on all 114 Quran surahs vs full Arabic+cross-tradition control
pool. PNAS-class reviewers will demand a 95% confidence interval. This
experiment provides one via stratified pair-bootstrap.

## Hypothesis

**H1**: The bootstrap 95% CI of T² across 1 000 paired resamples does not
include the historical band-A value of 3 557.34, confirming that adding
B+C surahs strengthens the multivariate separation rather than just
shifting it.

## Pre-registered decision rule

| Outcome | Verdict |
|---|---|
| 95% CI lower bound > 3 557.34 | `STRENGTHENED` (B+C surahs add signal) |
| 95% CI includes 3 557.34 | `STABLE` (B+C surahs neutral) |
| 95% CI upper bound < 3 557.34 | `WEAKENED` (B+C surahs hurt; would retract patch B headline) |

## Frozen protocol

- 1 000 paired bootstrap resamples
- Per resample: draw 114 Quran surahs (with replacement) and an equal-
  size 4 719 control sample (with replacement); compute T² with pooled
  cov + Moore-Penrose pseudoinverse
- Report median, 2.5/97.5 percentiles
- Report bias = (mean_bootstrap - point_estimate)
- Seed 42

## Reproduction

```powershell
python -X utf8 -u experiments\expP12_bootstrap_t2_ci\run.py
```
