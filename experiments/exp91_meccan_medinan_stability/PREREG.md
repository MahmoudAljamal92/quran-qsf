# exp91_meccan_medinan_stability — PRE-REGISTRATION

**Timestamp**: 2026-04-21 (late evening, v7.7)
**Status**: Frozen BEFORE any run. No numerical result seen before this doc committed.

---

## 1. Motivation

External review critique: *"The text was generated over 23 years. The early texts (Meccan) are short and poetic. The late texts (Medinan) are long and legalistic. Does your fingerprint actually survive across both genres, or is your score just an average of two different styles?"*

This is a **diachronic stability** challenge for the LC3-70-U parsimony proposition. `PAPER.md §5` already honestly retracts an older "Joint Meccan-Medinan F > 1" pre-registration that failed. This experiment tests a **different** and more specific claim: does the LC3-70-U linear discriminant `L = 0.5329·T + 4.1790·EL − 1.5221` classify Meccan and Medinan surahs correctly at comparable rates?

## 2. Hypothesis

**H-MM-STABILITY** — Under the canonical Meccan/Medinan split (`src/extended_tests.py:47-49`: Medinan = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 76, 98, 99, 110}), both Band-A groups:

(i) cross the `L > 0` Quran-side boundary at comparable rates (fraction difference ≤ 25 percentage points);
(ii) have mean `L` values of the same sign (both positive = both on the Quran side);
(iii) show Cohen d(L_meccan vs L_medinan) ≤ 1.0 (modest or smaller effect — LC3-70-U is not simply an "early vs late" detector).

## 3. Pre-registered verdict ladder (evaluated in order)

1. **FAIL_sanity_count_drift** — `n_meccan + n_medinan ≠ 68` (should match exp70's locked Band-A count).
2. **FAIL_opposite_signs** — `mean(L_meccan)` and `mean(L_medinan)` have opposite signs (one group is on Quran side, other on control side on average). Indicates genre-stratification rather than Quran-specificity.
3. **FAIL_crossing_gap** — `|frac_meccan_over_0 − frac_medinan_over_0| > 0.25` (one group's Quran-side rate is more than 25 pp above the other).
4. **FAIL_large_cohen_d** — `|d(L_meccan, L_medinan)| > 1.0` (large effect size suggests LC3-70-U is heavily genre-dependent).
5. **PASS_stable** — all three conditions in §2 hold; LC3-70-U is diachronically stable across the 23-year composition arc.
6. **MIXED** — any other combination (should not occur by construction).

## 4. Methodology (frozen)

- **Data**: `state["X_QURAN"]` (68 × 5) from `phase_06_phi_m.pkl`. Surah indices recovered from `state["FEATS"]["quran"]` iteration order (surah 1 to 114; Band-A filter 15 ≤ n_verses ≤ 100 applied row-wise preserves ordering).
- **M/M split**: hard-coded `MEDINAN = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 76, 98, 99, 110}` from `src/extended_tests.py`. All other surahs in [1, 114] are Meccan.
- **Discriminant**: `L(s) = 0.5329·T + 4.1790·EL − 1.5221` from `exp70_decision_boundary.json`. No re-fitting; use the locked coefficients exactly.
- **Per-group statistics**: n, mean T, mean EL, mean L, std L, frac(L > 0), min L, max L.
- **Cohen d**: `d(L_meccan, L_medinan)` with pooled SD, `ddof=1`.

## 5. Stakes

- **PASS_stable** → reviewer's diachronic-stability critique directly defused; LC3-70-U classifies consistently across Meccan/Medinan despite massive shifts in topic, length, and real-world context. Direct evidence the mathematical engine did not drift over 23 years of composition.
- **FAIL_** → honest finding; the 5-D fingerprint is stratified by chronology and the classifier's performance is partly a chronology/genre effect. Would require new framing in `PAPER.md §4.35` and downstream docs.

## 6. No re-tuning

Thresholds (25 pp, Cohen d 1.0), MEDINAN set, and discriminant coefficients are frozen. Any deviation requires a new experiment number and new PREREG.

---

*Pre-registration committed 2026-04-21 post-exp90. No result seen before this file was written.*
