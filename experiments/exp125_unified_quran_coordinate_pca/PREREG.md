# exp125_unified_quran_coordinate_pca — Pre-Registration

**Status**: PRE-EXECUTION (2026-04-29 evening, V3.14 candidate sprint, sub-task 2 of 3)
**Hypothesis ID**: H79
**Owner**: Cascade
**PREREG hash**: locked at experiment seal time

---

## 1. The question

Do the 5 universal features (`VL_CV, p_max, H_EL, bigram_distinct_ratio, gzip_efficiency`) collapse to a **single principal direction** PC1 in feature space, with the Quran as the unique extremum on that direction?

If yes, the PC1 loading vector IS the **unified linear formula** that subsumes Φ_M (5-D Mahalanobis), F58 (Φ_master), F66/F67 (EL extrema), F75 (Shannon-Rényi-∞ gap) into a single coordinate per corpus.

This is the "higher-grade universal" candidate — a single linear combination of measurable features that places the Quran at a strict outlier position relative to all 10 other tested corpora across 5 language families.

## 2. Pool

Identical to exp122 / exp124:
- **Corpora (N=11)**: `{quran, poetry_jahili, poetry_islami, poetry_abbasi, hindawi, ksucca, arabic_bible, hebrew_tanakh, greek_nt, pali, avestan_yasna}`
- **Features (D=5)**: `{VL_CV, p_max, H_EL, bigram_distinct_ratio, gzip_efficiency}`
- **Per-corpus values**: per-corpus median of each feature. Frozen at `_phi_universal_xtrad_sizing.json` SHA-256 = `0f8dcf0f…`.

## 3. Procedure

### Stage A — Standardise

For each feature `f`:
- Compute `μ_f, σ_f` across all 11 corpora.
- Replace each value `x_{c,f}` with `z_{c,f} = (x_{c,f} − μ_f) / σ_f`.

Result: `Z` is an 11×5 matrix of z-scores (per-feature mean = 0, per-feature std = 1).

### Stage B — Eigendecompose covariance

Compute the 5×5 sample covariance matrix `C = Z^T Z / (N−1)`. Eigendecompose:
- `λ_1 ≥ λ_2 ≥ … ≥ λ_5`: eigenvalues (variances).
- `v_1, v_2, …, v_5`: corresponding eigenvectors (length 5 each, unit norm).

`v_1` is the PC1 loading vector. Sign convention: choose sign of `v_1` such that `v_1^T z_quran < 0` (Quran scores negative on PC1, matching the F75 / F66 sign convention for Quran-distinctiveness).

### Stage C — Project + score

For each corpus `c`:
- `pc1_score(c) := v_1^T z_c` (scalar).

Compute:
- `var_explained_pc1 := λ_1 / sum(λ_i)`.
- `mean_pc1_non_quran := mean over c≠quran of pc1_score(c)`.
- `std_pc1_non_quran := std over c≠quran of pc1_score(c)`.
- `z_quran_pc1 := (pc1_score(quran) − mean_pc1_non_quran) / std_pc1_non_quran`.
- `cv_pc1_non_quran := std_pc1_non_quran / |mean_pc1_non_quran|`.
- `max_other_abs_z_pc1 := max over c≠quran of |z_c|` (where z_c is computed using the same mean/std).

### Stage D — Cross-check via direct linear formula

Once `v_1` is known, the **unified linear formula** is:

```
α(c) = v_1[0]·z_VL_CV(c) + v_1[1]·z_p_max(c) + v_1[2]·z_H_EL(c)
     + v_1[3]·z_bigram_distinct(c) + v_1[4]·z_gzip_eff(c)
```

This is a single number per corpus. The receipt records `α(c)` for all 11 corpora as the "unified Quran-coordinate".

## 4. Acceptance criteria (pre-registered, frozen)

A unification is **PASS_unified** iff **all three**:
- **(a) Single direction dominance**: `var_explained_pc1 ≥ 0.60` (PC1 captures ≥ 60 % of total variance — single direction is sufficient summary).
- **(b) Quran extremum**: `|z_quran_pc1| ≥ 5.0`.
- **(c) No competing outlier**: `max_other_abs_z_pc1 ≤ 2.0`.

**PASS_strong_unified** iff **all four**:
- (a)-(c) above
- **(d)** `var_explained_pc1 ≥ 0.80` (PC1 captures ≥ 80 % — strong dominance).

**PARTIAL_quran_extremum_no_dominance** iff (b) AND (c) but `0.40 ≤ var_explained_pc1 < 0.60` — Quran is extremum but feature space is essentially 2-dimensional.

**FAIL_no_unification** iff (b) fails — Quran is not a strict outlier on PC1.

**FAIL_audit_*** for SHA mismatch, etc.

## 5. Why these thresholds

- 60 % single-direction dominance is a standard PCA cutoff for "1-D summary is acceptable" (cf. Joliffe 2002 *Principal Component Analysis* §6.1).
- 80 % is the stricter "single direction dominates" threshold.
- 5σ Quran outlier matches exp122 / F75's bar.
- 2σ no-competitor matches exp122.

## 6. Theoretical context (mathematical unification answer)

This experiment **operationalises** the unification claim:

> All 5 stylometric features are ultimately f-divergences between the observed text and a canonical reference. By Pinsker's inequality, the L1 bigram distance (F55) is upper-bounded by `√(2·D_KL)`. Φ_M is the Gaussian KL between two Gaussian models with equal covariance. F75's `H_EL + log₂(p_max·A)` is the KL divergence between the empirical letter distribution and the uniform distribution, plus a constant. **All collapse to weighted KL divergences at multiple scales.**

PCA discovers the optimal *linear* combination of the 5 features that captures maximum variance. If that combination places the Quran as the unique outlier, the linear PC1 IS the practical realisation of the multi-scale KL divergence's leading eigenvector.

## 7. Audit hooks

- **A1**: input sizing receipt SHA-256 must match `0f8dcf0f69106020fac6c596716b4729d78fdece828ebb83aba3aa2b0a79fc22`.
- **A2**: feature names match `FEATURE_NAMES` exactly.
- **A3**: corpus names match `EXPECTED_CORPORA` exactly (N=11).
- **A4**: PCA is deterministic — re-run produces byte-identical receipt (numpy seed not needed; eigendecomposition is deterministic up to sign convention which is fixed in §3 Stage B).
- **A5**: numerical sanity — `sum(λ_i) ≈ 5.0` (expected from standardised data with 5 features) within 1e-6.

## 8. What this experiment does NOT do

- It does **not** discover a non-linear unified manifold — only the optimal *linear* 1-D summary. Non-linear unification (kernel PCA, autoencoders) is out of scope.
- It does **not** include the RG-scaling exponent α(c). That's a separate Stage-E of a future exp125b which requires verse-level access. PREREG locked to the per-corpus median input.
- It does **not** make N≥18 claims — only N=11 result, with Path-C extension scheduled.

## 9. Honest scope

If **PASS_strong_unified**: the project gains its **first single-formula universal** (linear PC1 of 5 features) — directly answers the user's question "can old + new toolkit be unified?" Promotion: **F77 candidate** (PARTIAL strength at N=11, awaiting Path-C confirmation).

If **PASS_unified** but not strong: weaker but still PASS. F77 candidate at PARTIAL_dominance level.

If **PARTIAL_quran_extremum_no_dominance**: the Quran is an outlier but feature space is essentially 2-D — unification needs both PC1 and PC2. Document as PARTIAL F77 (2-D unification).

If **FAIL_no_unification**: no single linear coordinate captures Quran-distinctiveness. F75 + F76 + Φ_M remain separate findings. Honest negative datum.

## 10. Output

Receipt: `results/experiments/exp125_unified_quran_coordinate_pca/exp125_unified_quran_coordinate_pca.json` containing:
- `verdict` (one of the 5 ladder values)
- `eigenvalues` (5 sorted descending)
- `var_explained_per_pc` (5 fractions summing to 1)
- `pc1_loading` (5-vector, the unified formula's coefficients)
- `pc2_loading` (5-vector, for context)
- `pc1_score_per_corpus` (11-element dict: corpus → α(c))
- `pc2_score_per_corpus`
- `z_quran_pc1`, `cv_pc1_non_quran`, `max_other_abs_z_pc1`
- `unified_formula_string` (human-readable — e.g. "α(c) = -0.42·z_VL_CV + 0.61·z_p_max - 0.55·z_H_EL + 0.21·z_bigram + 0.32·z_gzip")
- `audit_report`
- `prereg_hash`, `wall_time_s`

## 11. Wall-time estimate

Pure numpy eigendecomposition of a 5×5 matrix. Expected wall-time: < 0.1 s.

---

**Filed**: 2026-04-29 evening (V3.14 candidate sprint, sub-task 2)
