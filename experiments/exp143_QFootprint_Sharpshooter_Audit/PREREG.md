# Pre-Registration — exp143 — Q-Footprint Sharpshooter Audit

**Status**: PRE-REGISTERED V3.15.2 final-pinnacle batch (sub-experiment 1 of 3)
**Author**: project leader (Cascade-assisted)
**Pre-reg date**: 2026-04-29 night

## 1. Background and motivation

V3.15.1's `exp138_Quran_Footprint_Joint_Z` (FN20) reported the project's pinnacle joint Quran-distinctiveness statistic: Stouffer Z (Brown-adjusted) = **+12.149σ** rank-1 of 12 corpora across K=8 pre-registered universal-feature axes, with column-shuffle null p_Z < 10⁻⁴. The K=8 axes were drawn from already-locked pre-V3.15.1 findings (F44, F46, F47, F50, F67, F76, F78, V3.9.2) and the PREREG was hash-locked before the joint Z was computed. **However**, the project has accumulated ≥ 20 plausible feature axes since V3.0, and a critical reviewer could argue that the 8 axes were the most Quran-favorable subset selected post-hoc from a larger pool of considered features. This is the **sharpshooter fallacy** — the risk that any sufficiently large axis pool will contain at least one K=8 subset on which the target is rank-1 by chance.

This experiment is the formal sharpshooter audit. It tests whether the 12.149σ result survives three independent threats:
1. **Robustness to single-axis removal** (LOAO): is any single axis "carrying" the result?
2. **Robustness to random axis subset** (random K=8 from extended pool): if we draw K=8 axes UNIFORMLY AT RANDOM from a 20-axis pool, what fraction yield Quran joint Z ≥ 12.149?
3. **Inverse test** (per-corpus best-K=8): if every corpus is allowed to pick its own best K=8 axes, does Quran still produce the highest joint Z?

## 2. Hypothesis

**H93-Sharpshooter** (pre-registered): The Q-Footprint joint Z = 12.149σ is structurally Quran-specific, not a sharpshooter artefact. Specifically:
1. Leave-one-axis-out (LOAO): at least 7 of 8 LOAO recomputations yield Quran joint Z_brown ≥ 8.0, AND minimum LOAO Z_brown ≥ 6.0.
2. Random K=8 from a 20-axis extended pool: under N=10,000 uniformly random K=8 subsets, fewer than 1% of subsets yield Quran joint Z ≥ 12.149.
3. Inverse test: for each non-Quran corpus c, c's best-of-pool K=8 joint Z (using c's own optimal axis subset chosen to maximize c's |Z|) is less than Quran's actual 12.149.

## 3. The 20-axis extended pool (declared before any computation)

| # | Axis | Definition | Quran-extreme direction (default sign) |
|---|---|---|---|
| 1 | `HEL_pool` | pooled H_EL | LOW → Quran (-1) |
| 2 | `pmax_pool` | pooled p_max | HIGH → Quran (+1) |
| 3 | `bigram_distinct_pool` | pooled bigram-distinct ratio | LOW → Quran (-1) |
| 4 | `gzip_eff_pool` | pooled gzip ratio | LOW → Quran (-1) |
| 5 | `Delta_pool` | log₂(A) − H_EL_pool | HIGH → Quran (+1) |
| 6 | `HEL_unit_p10` | 10th percentile per-unit H_EL | LOW → Quran (-1) |
| 7 | `HEL_unit_p25` | 25th percentile per-unit H_EL | LOW → Quran (-1) |
| 8 | `HEL_unit_median` | median per-unit H_EL | LOW → Quran (-1) |
| 9 | `HEL_unit_p75` | 75th percentile per-unit H_EL | LOW → Quran (-1) |
| 10 | `HEL_unit_mean` | mean per-unit H_EL | LOW → Quran (-1) |
| 11 | `pmax_unit_p25` | 25th percentile per-unit p_max | HIGH → Quran (+1) |
| 12 | `pmax_unit_median` | median per-unit p_max | HIGH → Quran (+1) |
| 13 | `pmax_unit_p75` | 75th percentile per-unit p_max | HIGH → Quran (+1) |
| 14 | `pmax_unit_mean` | mean per-unit p_max | HIGH → Quran (+1) |
| 15 | `VL_CV_unit_p25` | 25th percentile per-unit VL_CV | HIGH → Quran (+1) |
| 16 | `VL_CV_unit_median` | median per-unit VL_CV | HIGH → Quran (+1) |
| 17 | `VL_CV_unit_p75` | 75th percentile per-unit VL_CV | HIGH → Quran (+1) |
| 18 | `Delta_unit_p25` | log₂(A) − p25(H_EL_u) | HIGH → Quran (+1) |
| 19 | `Delta_unit_median` | log₂(A) − median(H_EL_u) (= F79) | HIGH → Quran (+1) |
| 20 | `Delta_unit_p10` | log₂(A) − p10(H_EL_u) (strictest) | HIGH → Quran (+1) |

**Of these 20 axes, 8 are the original exp138 axes** (axes 1, 2, 3, 4, 7, 8, 16, 19 in the new numbering) and 12 are extensions. The pool is principled: only first-order aggregations of the 5 locked universal features + one alphabet correction. No supervised or composite axes (LDA/PCA excluded).

## 4. Sub-tasks

**Sub-task A — Leave-one-axis-out (LOAO)**: For each of the original 8 axes, drop that axis from the K=8 set and recompute Quran joint Stouffer Z (Brown-adjusted) on the remaining 7. Report 8 LOAO Z values. Identify the dominant axis (largest drop in Z when removed).

**Sub-task B — Random K=8 from 20-pool null**: Under SEED=42, draw N=10,000 uniformly random size-8 subsets from the 20-axis pool. For each subset, compute Quran's joint Stouffer Z (Brown-adjusted, using the pre-assigned per-axis Quran-extreme signs). Report (a) the empirical distribution of Quran joint Z across random subsets, (b) the fraction of subsets where Quran Z ≥ 12.149 (= original exp138 result), (c) the maximum and 99th percentile Quran Z achievable.

**Sub-task C — Inverse test (per-corpus best K=8)**: For each non-Quran corpus c, compute c's z-score on each of the 20 axes (using non-c mean/std for that axis), take the absolute value (sign-free; each corpus can be extreme in either direction), and identify c's top-8 axes by |z_c|. Compute c's "best achievable joint |Z|" using these 8 axes (Brown-adjusted with K_eff computed from non-c rows). Repeat for Quran and report the comparison.

**Sub-task D — Combined verdict**: Pass criterion is (A1: ≥7/8 LOAO Z ≥ 8.0 AND min ≥ 6.0) AND (B1: fraction < 1%) AND (C1: max non-Quran best-Z < Quran's actual 12.149).

## 5. Acceptance criteria

A1: LOAO — at least 7 of 8 LOAO Z_brown ≥ 8.0, AND min LOAO Z_brown ≥ 6.0.  
A2: Random K=8 — fraction of subsets where Quran Z_brown ≥ 12.149 is < 0.01.  
A3: Inverse — max over 11 non-Quran corpora of (best-achievable joint |Z| using each corpus's optimal K=8 from the 20-pool) < Quran's actual 12.149.  
A4 (bonus): under random K=8 draws, Quran is rank-1 of 12 (highest joint |Z| among all corpora) in ≥ 99% of subsets.  
A5 (bonus): the dominant axis (largest LOAO drop) is identified and is one of the per-unit H_EL axes (NOT a single pooled axis), confirming the per-unit structural mechanism.

Verdict ladder:
- A1 + A2 + A3 PASS → `PASS_no_sharpshooter` → 12.149σ headline confirmed sharpshooter-clean
- 2 of {A1, A2, A3} PASS → `PARTIAL_low_sharpshooter_risk`
- ≤ 1 PASS → `FAIL_sharpshooter_risk_present` (would force retraction of O6 to FN20-only-data status)

## 6. Audit hooks

- `prereg_hash` SHA256 of this file written into receipt.
- `frozen_constants`: AXIS_POOL list, N_RANDOM_SUBSETS=10000, SEED=42.
- `audit_report`: SHA256 of the 20-axis raw feature matrix M_raw (12×20); LOAO Z_brown values; random-subset distribution percentiles.

## 7. Honest scope

This experiment audits the K=8 PREREG choice in exp138 against a 20-axis extended pool. It does NOT prove the Quran's distinctiveness against ALL possible feature axes (an infinite space). The 20-axis pool is finite, principled, and pre-registered. A FAIL outcome would be substantively informative: it would mean the 12.149σ headline is not robust under axis-set perturbation and should be downgraded to "the headline scalar under the specific 8-axis pre-registration".
