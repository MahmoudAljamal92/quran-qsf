# Audit Memo — Stage-2 F1 Brown-Stouffer divisor correction

**Date**: 2026-04-29 night
**Sprint label**: V3.15.2 → V3.15.3 patch (Stage-2 audit response)
**Auditor**: external Stage-1+2 adversarial code review (audit prompt; user-driven)
**Approver**: project owner (explicit "Accept all 3, file R61/R62/R63" decision)
**Scope**: a single mathematical correction in three experiment scripts
**Result**: three retraction R-rows (R61, R62, R63) filed in
[`RETRACTIONS_REGISTRY.md`](../findings/RETRACTIONS_REGISTRY.md#category-n)

---

## 1. The bug

Three experiment scripts implemented Brown-Stouffer's combined-Z under
correlated test statistics with the wrong denominator.

```python
# BUGGY (pre-fix):
K_eff = (K * K) / max(sum_R, 1e-12)
Z_brown = sum_z / math.sqrt(K_eff)

# CORRECT (post-fix):
Z_brown = sum_z / math.sqrt(max(sum_R, 1e-12))
```

The quantity `K_eff = K² / sum_R` is the **Cheverud (2001) / Li-Ji (2005)
M_eff** — the *effective number of independent tests*, used to adjust
family-wise α in Bonferroni-style correction under correlation.

It is **not** the variance of the sum of correlated z-scores.

For z_i ~ N(0, 1) with pairwise correlation matrix R (R_ii = 1, R_ij = ρ_ij),
the correct combined-Z (Strube 1985, Whitlock 2005) is:

```
Var(Σ_i z_i) = Σ_{i,j} Cov(z_i, z_j) = Σ_{i,j} R_{i,j} = sum_R
SD(Σ_i z_i) = sqrt(sum_R)
Z_combined  = (Σ_i z_i) / sqrt(sum_R)    ~ N(0, 1) under H0
```

The buggy formula coincides with the correct one only at the iid endpoint
(sum_R = K). Under correlation the buggy formula inflates Z by factor
`sum_R / K`. With K = 8 and sum_R = 36.667 (the exp138 value), the
inflation factor is **4.585×**.

## 2. The empirical impact

| Receipt | BEFORE | AFTER | Δ | Verdict change |
|---|---|---|---|---|
| `exp138.sub_C.quran_Z_brown` | 12.149σ | **2.651σ** | −9.498σ | PARTIAL → **FAIL** |
| `exp138.sub_C.gap_Z_brown_quran_to_rank2` | 2.947 | 0.643 | −2.304 | A3 already failing |
| `exp138.criteria.n_pass_of_6` | 4 | 3 | −1 | trips FAIL ladder |
| `exp141.A.quran_Z` (Arabic-only) | 35.142σ | 9.649σ | −25.493σ | A1 (≥10) PASS → FAIL |
| `exp141.B.quran_Z` (non-Arabic) | 7.865σ | 1.816σ | −6.049σ | A2 (≥5) PASS → FAIL |
| `exp141.C.quran_Z` (combined) | 12.149σ | 2.651σ | −9.498σ | A3 (≥8) PASS → FAIL |
| `exp141.criteria.n_pass_of_5` | 4 | 0 | −4 | PARTIAL → **FAIL** |
| `exp143.sub_A.min_LOAO_Z` | 8.94σ | 2.29σ | −6.65σ | A1 PASS → FAIL |
| `exp143.sub_B.frac_q_Z≥12.149` | 0.911 | 0.000 | −0.911 | A2 FAIL → PASS (vacuous) |
| `exp143.sub_C.max_non_q_inverse_Z` | 14.44 | 4.00 | −10.44 | A3 FAIL → PASS (vacuous) |
| `exp143.criteria.n_pass_of_3_core` | 1 | 2 | +1 | FAIL → **PARTIAL** (vacuous) |

**Empirical column-shuffle p_Z values are unchanged** at every site
(exp138 p_Z = 0.0001, exp141 Pool A p_Z < 1e-5, Pool B p_Z = 0.0231, Pool C
p_Z = 0.0001). The permutation null is invariant to the formula because
both the actual and the shuffled corpora use the same divisor.

## 3. What is preserved across the correction

- **exp138**: Quran rank-1 of 12 by joint Brown-Stouffer Z (corrected),
  Quran rank-1 by Hotelling T² (= 154.75 vs runner-up 8.87, ratio 17.4×;
  T² is invariant to the Brown formula), column-shuffle p_Z = 0.0001.
- **exp141**: Quran rank-1 in all three pools by both Z and T². Hotelling T²
  ratios are spectacularly preserved: Arabic-only ratio 7,884×, non-Arabic
  ratio 2,216×, combined ratio 17.4×.
- **exp143**: Quran rank-1 in 99.20 % of random K = 8 subsets from the
  20-axis pool (this fraction is also invariant to the Brown formula —
  it's a rank statistic, not a magnitude statistic).

## 4. What is killed by the correction

- The "Quran joint Z = 12.149σ pinnacle" headline (RANKED_FINDINGS O6/O7).
- The parametric "p ≈ 10⁻³³" reading attached to that headline.
- The bilateral Z_min ≥ 5σ claim of exp141 / FN23.
- The literal A1, A2, A3 PREREG criteria that are calibrated to the
  inflated 12.149 / 35.142 / 7.865 scale.

## 5. What is **not** killed

- **The locked Φ_M Hotelling T² = 3,557 finding** is unaffected. T² uses a
  different (correctly-implemented) statistic.
- **F55 universal forgery detector** is unaffected (theorem-derived, not
  Brown-combined).
- **F76 / F78 / F79 categorical universal claims** are unaffected (single-
  feature thresholds, not joint Z).
- **All retractions R01–R60** are unaffected.
- **Quran's rank-1 dominance under the joint statistics** survives the
  correction; only the σ scale is corrected.

## 6. Files changed

- `experiments/exp138_Quran_Footprint_Joint_Z/run.py` (lines ~250-255 and
  ~304): replaced `math.sqrt(K_eff)` with `math.sqrt(max(sum_R, 1e-12))`
  at both the actual-Z site and the permutation-null site.
- `experiments/exp141_QFootprint_Dual_Pool/run.py` (helper `stouffer_z_brown`,
  lines 61-69): same one-line fix in the helper function used by all three
  pools.
- `experiments/exp143_QFootprint_Sharpshooter_Audit/run.py` (helper
  `stouffer_z_brown`, lines 176-184): same one-line fix.

## 7. Regression test

- `tests/test_fix_F1_brown_stouffer.py` (5 mathematical tests + 3
  source-pattern tests). All pass on the fixed code; the source-pattern
  tests fail on the pre-fix code.

## 8. Receipts re-generated

- `results/experiments/exp138_Quran_Footprint_Joint_Z/exp138_Quran_Footprint_Joint_Z.json`
  (43.8 s wall, verdict `FAIL_q_footprint_no_joint_pinnacle`).
- `results/experiments/exp141_QFootprint_Dual_Pool/exp141_QFootprint_Dual_Pool.json`
  (47.3 s wall, verdict `FAIL_dual_pool_inhomogeneous`).
- `results/experiments/exp143_QFootprint_Sharpshooter_Audit/exp143_QFootprint_Sharpshooter_Audit.json`
  (38.8 s wall, verdict `PARTIAL_low_sharpshooter_risk` — VACATED in R63).

PREREG hashes are unchanged; pre-registrations were not modified.

## 9. Recommended next action

**`exp143b_sharpshooter_audit_corrected` (new pre-registration)** — re-ask
the sharpshooter question against the *corrected* Quran Z = 2.651σ as the
threshold. Preliminary numbers suggest the corrected median random K = 8
subset Z = 3.19σ exceeds Quran's 2.65σ, which would be a substantive
sharpshooter PASS (i.e., the original 8 axes do *not* dominate the random
20-axis pool when re-asked at the corrected scale). This is exploratory
until pre-registered.

The downstream RANKED_FINDINGS rows for F1 audit, O6, O7, FN20, FN22, FN23
all need narrative correction; that work is tracked under the F3 / F5 / F6
narrative-cleanup passes in the same Stage-2 fix sprint.

---

*This memo is the canonical Source reference cited from R61, R62, R63
in [`RETRACTIONS_REGISTRY.md`](../findings/RETRACTIONS_REGISTRY.md).*
