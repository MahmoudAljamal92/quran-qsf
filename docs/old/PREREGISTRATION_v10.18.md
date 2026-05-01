# Pre-Registration Document — v10.18 (3 new tests)

**Date**: 2026-04-17 (evening)
**Author**: Mahmoud Aljamal
**Protocol**: All hypotheses, thresholds, seeds, and falsification criteria are locked below BEFORE running any of the three tests. Results will be reported honestly whether they confirm or falsify.

---

## Why three more pre-registrations

The v10.16 pre-registered adversarial prediction test (`scripts/preregistered_prediction_test.py`) was the first fully prospective test. Three more are added here to strengthen peer-review defensibility by demonstrating robustness to:
- Data partition (cross-validation)
- Historical period (Meccan vs Medinan)
- Resampling (bootstrap)

---

## Test A — Cross-Validation Robustness of Φ_M

**Hypothesis (H-A)**: The matched-length Φ_M effect (Cohen's d) is robust across every random 10-fold partition of the Quran corpus.

**Parameters (LOCKED)**:
- Seed: `42`
- Number of folds: `10`
- Length band: `[15, 100]` verses
- Fold method: `sklearn.model_selection.KFold(n_splits=10, shuffle=True, random_state=42)`
- Per-fold test: `stats.mannwhitneyu(phi_quran_fold, phi_ctrl_all, alternative='greater')`
- Cohen's d formula: pooled-SD standardized difference
- Primary statistic: **minimum Cohen's d across 10 folds**

**Confirmation threshold**: Minimum d across 10 folds ≥ **0.5** AND maximum p across 10 folds < **0.01**.

**Falsification**:
- Any single fold has d ≤ 0 → FALSIFIED
- Median d across folds < 0.5 → FALSIFIED
- Maximum p-value across folds > 0.05 → FALSIFIED

---

## Test B — Revelation-Period Invariance (H-Cascade)

**Hypothesis (H-B)**: The fractal H-Cascade signature (F > 1) holds BOTH for Meccan surahs and Medinan surahs separately. Revelation period does not determine the structural signature.

**Parameters (LOCKED)**:
- Seed: `42`
- Meccan surahs: traditional classification per standard Islamic scholarship (86 surahs: 1, 6-7, 10-19, 20-21, 23, 25-32, 34-46, 50-56, 67-114 — full list in test script)
- Medinan surahs: complement of Meccan (28 surahs: 2-5, 8-9, 22, 24, 33, 47-49, 57-66)
- Length band: `[15, 100]` verses (as in main test)
- Bundle size: 5 units per bundle
- F definition: mean(r_k) / std(r_k) where r_k = H_{k+1}/H_k (same as §6.1 in paper)
- Primary statistics: F_Meccan, F_Medinan (per-bundle means)

**Confirmation threshold**:
- F_Meccan_mean > **1.0** AND F_Medinan_mean > **1.0**
- AND F_Meccan - F_Medinan | < **1.5** (similar magnitude)
- AND both satisfy Mann-Whitney p < 0.05 against pooled control F

**Falsification**:
- Either F_Meccan_mean or F_Medinan_mean < 1.0 → FALSIFIED (structural signature absent in one period)
- |F_Meccan - F_Medinan| > 1.5 → FALSIFIED (period-dependent artifact)
- Either p > 0.05 → FALSIFIED

---

## Test C — Bootstrap Stability of Hierarchical Ω

**Hypothesis (H-C)**: Hierarchical Ω_master for the Quran is bootstrap-stable. In 1000 bootstrap resamples of the Quran's length-matched surahs, the geometric-mean Ω_master exceeds 2.0 in at least 95% of resamples.

**Parameters (LOCKED)**:
- Seed: `42`
- Number of bootstraps: `1000`
- Bootstrap method: sample with replacement, same size as original
- Length band: `[15, 100]` verses
- Baselines frozen at pre-computed values (from `hierarchical_omega.py` main run): spec=0.5355, root=0.5200, EL=0.2552, phi=1.6644
- Primary statistic: geometric mean of Ω_master across each bootstrap sample
- Report: fraction of bootstraps with Ω_master > 2.0

**Confirmation threshold**: At least **95%** of bootstraps yield Ω_master > **2.0**.

**Falsification**:
- < 95% of bootstraps exceed 2.0 → FALSIFIED (result not bootstrap-robust)
- 5th percentile Ω_master < 1.5 → FALSIFIED (tail too weak)

---

## Commitment Statement

The author commits that all three tests will be run with exactly the parameters above. Any deviation from these thresholds (e.g., changing seed, changing threshold after seeing data, excluding specific folds) constitutes a violation of this pre-registration and any reported result would be invalidated. Results from this pre-registration will be reported in `output/preregistration_v10.18_results.json` regardless of whether they confirm or falsify each hypothesis.

---

## Honest Limitations of This Pre-Registration

1. **Not time-stamped by a third party**: Unlike OSF pre-registration, this document is part of the same project repository. The safeguards are: (a) explicit commitments printed in the test scripts themselves, (b) versioned git history if the repo is version-controlled, and (c) reviewer can read this document and the test script together to verify the commitments were declared before the results.

2. **Data are not novel**: The tests use the same corpus as the primary findings. What IS novel is the partitioning criterion (random folds, revelation period, bootstrap resamples) — these operations have not been performed on the data before.

3. **Reproducibility check**: Any reviewer can re-run `scripts/preregistered_tests_v10.18.py` with the provided seeds and verify the exact numbers.
