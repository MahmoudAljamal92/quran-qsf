# exp55_gamma_length_stratified — Pre-Registration

**Date**: 2026-04-21 (scaffolded this session; executed in Step 5).
**Audit trail**: `docs/SCAN_2026-04-21T07-30Z/03_HYPOTHESIS_REGISTER.md` H3.

## Hypothesis (H3)

The Band-A doc-scale gzip NCD Cohen's d = +0.534 (from `exp41_gzip_formalised`) is **not length-driven** — the Quran-vs-control difference survives when surahs are matched by letter-count decile.

## Why this experiment exists

`exp41` already includes a `length_audit.json` with per-decile Cohen's d and a log-linear regression with a Quran indicator term (γ = +0.072, p ≈ 0). However:

1. The per-decile picture is **heterogeneous**: 8/10 deciles positive, 2/10 negative (decile 6: d = −0.55, decile 10: d = −1.50).
2. No **formal pre-registered decision rule** was applied. The existing verdict (`GENUINE_STRUCTURAL_SIGNAL_AFTER_LENGTH_CONTROL`) was post-hoc.
3. No **bootstrap CIs** on the per-decile Cohen's d values were reported.
4. No **sign-test** was reported.

This experiment applies a formal decision rule to the existing data plus runs a bootstrap on the per-decile d values.

## Primary statistic

From `exp41_gzip_formalised/length_audit.json`:

1. **Sign test**: out of 10 deciles, how many have Cohen's d > 0? Binomial test under H₀ = 0.5.
2. **Majority d > 0.30**: count of deciles with d > 0.30.
3. **Bootstrap 95% CI on per-decile Cohen's d** (resampled from the per-unit NCD values within each decile, B = 2000).
4. **Log-linear γ (Quran indicator)**: already available; confirm γ > 0 and p < 0.001.

## Pre-registered thresholds (frozen before computation)

| Condition | Verdict |
|-----------|---------|
| ≥ 7 of 10 deciles with d > 0.30 AND sign-test p ≤ 0.05 AND γ > 0 | **LENGTH_INDEPENDENT** |
| 4–6 deciles with d > 0.30 AND sign-test p ≤ 0.10 | **PARTIALLY_LENGTH_DRIVEN** |
| ≤ 3 deciles with d > 0.30 OR sign-test p > 0.10 | **LENGTH_DRIVEN** (retract d = +0.534 as headline) |

## Falsifier

Majority of deciles (≥ 6 of 10) with d ≤ 0, i.e. sign-test yields n_positive ≤ 4 with sign-test p > 0.10.

## Inputs

- `results/experiments/exp41_gzip_formalised/length_audit.json` (already on disk).
- `results/experiments/exp41_gzip_formalised/exp41_gzip_formalised.json` (for headline d value cross-check).
- `phase_06_phi_m.pkl` (for bootstrap: per-unit NCD values via replay of exp41's perturbation logic if raw values not available; otherwise use the summary stats for CI approximation).

## Outputs

- `results/experiments/exp55_gamma_length_stratified/exp55_gamma_length_stratified.json`

## Prereg hash

SHA-256 of this file computed at run-time.
