# Pre-Registration: exp62_adiyat_2d_retest

**Hypothesis**: Adiyat (Surah 100) anomaly re-test under the 2D (T, EL) parsimony model from exp60.

**Filed**: 2026-04-21 (before any computation)

---

## Motivation

exp60 showed (T, EL) capture >99% of the class-conditional information (Fisher TE
fraction = 100.9%, negative cross-term). The remaining features (VL_CV, CN, H_cond)
are mildly antagonistic in aggregate. This raises a critical question: is Adiyat's
anomaly status in the Mahalanobis ranking **driven by (T, EL) or by the residual 3D?**

## Tests

### T1 — 2D vs 5D Mahalanobis for Surah 100
Compute Φ_M in both 5-D (full) and 2-D (T, EL only) for all 114 surahs.
Report Surah 100's rank in both.

### T2 — Rank correlation
Spearman correlation between the 114-surah Φ_M_5D and Φ_M_2D rankings.

### T3 — Anomaly survival
Is Surah 100's Φ_M_2D still above the control pool's 95th percentile?

## Pre-registered thresholds

- **ANOMALY_SURVIVES** ⟺ Φ_M_2D(Surah 100) > ctrl_pool_2D 95th percentile AND
                           rank_2D ≤ rank_5D × 1.5 (doesn't drop much)
- **ANOMALY_WEAKENS**  ⟺ Φ_M_2D(Surah 100) < ctrl_pool_2D 95th percentile
- **ANOMALY_STRENGTHENS** ⟺ rank_2D < rank_5D (improves in 2D)

## Output

- `results/experiments/exp62_adiyat_2d_retest/exp62_adiyat_2d_retest.json`
