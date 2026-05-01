# exp54_phonetic_law_full — Pre-Registration

**Date**: 2026-04-21 (scaffolded this session; executed in Step 3).
**Audit trail**: `docs/SCAN_2026-04-21T07-30Z/03_HYPOTHESIS_REGISTER.md` H1.

## Hypothesis (H1)

Across the 7 emphatic-class substitutions catalogued in `exp46_emphatic_substitution`, the 9-channel forensic detection rate is a **monotonically-decreasing** function of articulatory-phonetic distance between the original and substituted phoneme: detection is easier for phonetically-closer substitutions (they violate fewer expected phonotactic constraints) than for phonetically-distant ones.

## Why this experiment exists

`exp47_phonetic_distance_law` was pre-registered and executed, but its input was `exp46_emphatic_substitution/exp46_emphatic_substitution.json` produced in **FAST mode** (20 surahs, n_perm = 200) despite the pre-registered protocol requiring FULL mode (114 surahs, n_perm = 5000). The subsequent FULL-mode exp46 run is on disk but **exp47 was never re-executed against it**, so the `best_pearson_r = 0.7471` and `overall_verdict = SUGGESTIVE` are computed from stale sampling-noise. This experiment (exp54) re-runs the exp47 analysis verbatim against the current FULL-mode exp46 output.

**Cross-reference**: `docs/SCAN_2026-04-21T07-30Z/01_FINDINGS.md §R6` documents the stale-input finding in detail.

## Primary statistic

Pearson *r* and Spearman ρ between the per-class detection rate and each of six non-circular phonetic-distance / frequency predictors:

| ID | Predictor |
|----|-----------|
| M1 | Hamming on discretised articulatory features |
| M2 | Weighted Euclidean on continuous articulatory features |
| M3 | Unweighted Euclidean (IPA-chart) |
| M4 | `n_edits` (raw frequency proxy) |
| M5 | `log(n_edits)` |
| M6 | `M2 × M5` (phonetic × log-frequency) |

M7 (`max_z_median` from exp46) is included as a CIRCULAR calibration metric.

## Pre-registered thresholds (frozen before computation)

| Condition | Verdict |
|-----------|---------|
| \|r\| ≥ 0.85 on best non-circular metric | LAW_CONFIRMED |
| 0.70 ≤ \|r\| < 0.85 on best non-circular metric | SUGGESTIVE |
| \|r\| < 0.70 on best non-circular metric | FAILS |

Additional pre-registered requirements for LAW_CONFIRMED:
1. Sign of the correlation must match the prediction (detection rate DECREASES with phonetic distance for M1/M2/M3, INCREASES with log-frequency for M4/M5).
2. Spearman ρ must agree in sign with Pearson r.
3. No more than 2 of the 7 classes may invert the predicted direction.

## Falsifier

Spearman ρ > 0 on M1/M2/M3 OR spearman ρ ≤ 0 on M4/M5 OR three-or-more per-class direction reversals.

## Inputs

- `results/experiments/exp46_emphatic_substitution/exp46_emphatic_substitution.json` — must have `fast_mode: false` AND `n_surahs_tested: 114`. Verified at load time; any mismatch raises FileNotFoundError-style abort.

## Outputs

- `results/experiments/exp54_phonetic_law_full/exp54_phonetic_law_full.json`
- `results/experiments/exp54_phonetic_law_full/phonetic_distance_scatter.png`

## Supersedes

`results/experiments/exp47_phonetic_distance_law/exp47_phonetic_distance_law.json` (kept for audit trail; marked DEPRECATED via `experiments/exp47_phonetic_distance_law/STATUS.md` after Step 6 R6 is applied).

## Prereg hash

SHA-256 of this `PREREG.md` file is computed at run-time and stored in the output JSON under `prereg_hash`. Any change to this pre-registration after the first run produces a different hash and invalidates the pre-registration contract.
