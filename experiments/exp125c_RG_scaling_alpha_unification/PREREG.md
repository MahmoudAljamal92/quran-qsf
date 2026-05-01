# exp125c_RG_scaling_alpha_unification — Pre-Registration

**Status**: PRE-EXECUTION (2026-04-29 night, V3.14.1 follow-up sprint, sub-task 2 of 2)
**Hypothesis ID**: H83
**Owner**: Cascade
**PREREG hash**: locked at experiment seal time

---

## 1. The question

`exp116_RG_scaling_collapse` (F68) showed that Quran's RG-scaling exponents differ from peer mean by 2-8σ on every feature, but only on **6 Arabic peers**. The cross-tradition extension to the **11-corpus pool** (V3.14: Arabic poetry × 3, hindawi, ksucca, arabic_bible, hebrew_tanakh, greek_nt, pali, avestan_yasna + Quran) was deferred for V3.14.

**Question**: does the per-corpus 4-vector of RG-scaling exponents `α(c) = (α_EL, α_p_max, α_H_EL, α_VL_CV)` give a **unified Quran-distinctive single coordinate** across the 11-corpus pool? Specifically, is there a single linear combination of the 4 α values that places the Quran as a strict outlier (|z| ≥ 5) with no competing outlier (max other |z| ≤ 2)?

If yes, this is the **higher-grade unification** — α(c) is a single intrinsic scaling exponent per corpus, mechanistically interpretable (RG-flow under verse-coarse-graining), and would constitute F68's promotion from "Quran-distinctive on Arabic" to "universal cross-tradition Quran-distinctive scaling exponent".

## 2. Pool

Identical to F76 / F77 (locked V3.14 11-corpus pool):
- **Corpora (N=11)**: `{quran, poetry_jahili, poetry_islami, poetry_abbasi, hindawi, ksucca, arabic_bible, hebrew_tanakh, greek_nt, pali, avestan_yasna}`
- **Per-corpus units**: each loaded via the cross-tradition loaders in `scripts/_phi_universal_xtrad_sizing.py` (already cached at SHA `0f8dcf0f…` for the per-corpus medians).
- **Floor**: only chapters/units with ≥ MIN_VERSES_FOR_RG = 32 verses contribute to the RG-scaling fit.

## 3. Procedure

### Stage A — Coarse-grained features per scale per chapter

For each unit with `n_verses >= 32`, compute features at scales L ∈ {1, 2, 4, 8, 16} (matches exp116). At each scale L:

1. Group consecutive L verses into super-verses (concatenate with space).
2. Compute 4 features on the super-verse list:
   - `EL_rate` (modal end-letter frequency)
   - `p_max` (top end-letter probability — equals EL_rate at chapter scale)
   - `H_EL` (end-letter Shannon entropy in bits)
   - `VL_CV` (CV of super-verse character lengths)
3. Skip if fewer than 2 super-verses at this L.

This mirrors `exp116_RG_scaling_collapse.features_at_scale()` exactly.

### Stage B — Per-corpus per-scale medians

For each (corpus, scale, feature), compute the median across all qualifying chapters:

`f_corpus_scale[c][L][feature] := median over chapters of feature(chapter, L)`

### Stage C — Power-law fit per (corpus, feature)

For each (corpus, feature), fit:

`log(median_feature(L)) = log(A) + α · log(L) + ε`

via least-squares regression on the 5 (L, median) pairs. The slope α is the RG-scaling exponent.

Result: 11 × 4 matrix of α values.

### Stage D — α-vector LDA unification

Treat the 11 × 4 α matrix as the input to LDA with classes {Quran (1 sample), rest (10 samples)}. Mirror exp125b exactly:

1. Standardise per feature (z-score across 11 corpora).
2. Fit Fisher LDA: `w ∝ S_W^{-1} (μ_Q − μ_R)`.
3. Project all 11 corpora onto `w_LDA`.
4. Compute Quran z-score, max competing |z|, Fisher ratio J.

### Stage E — Mandatory LOO robustness

For each held-out non-Quran corpus, refit LDA on the remaining 10. Project all 11 onto the new direction. Record min Quran |z|_LOO, max competing |z|_LOO.

## 4. Acceptance criteria (pre-registered, frozen)

A unification is **PASS_alpha_lda_strong_unified** iff **all three**:
- **(a) Quran extremum**: `|z_quran_alpha_LDA| ≥ 5.0`
- **(b) No competing outlier**: `max_other_abs_z_alpha_LDA ≤ 2.0`
- **(c) Fisher ratio**: `J ≥ 5.0`

**PASS_alpha_lda_strong_AND_LOO_ROBUST** iff (a) AND (b) AND (c) AND LOO:
- `min over c_h of |z_quran|_LOO ≥ 4.0`
- `max over c_h of max_other|z|_LOO ≤ 2.5`

**PARTIAL_alpha_lda_strong_BUT_LOO_NOT_ROBUST** iff full-pool PASS but LOO fails (mirrors F77).

**PARTIAL_alpha_lda_directional** iff `|z_quran| ≥ 3` but `< 5` AND no competing outlier.

**FAIL_no_alpha_unification** otherwise.

## 5. Audit hooks

- **A1**: per-corpus pool sizes match expected: hindawi 70+, hebrew_tanakh 920+, greek_nt 250+, pali 180+, avestan_yasna 70+ (exact value computed at runtime; PREREG locks order-of-magnitude).
- **A2**: each (corpus, feature, scale) median is finite (no NaN). Skip corpora with < 2 qualifying chapters at any scale.
- **A3**: power-law fit r² > 0.5 on at least 3 of 4 features per corpus (ensures the slope is meaningful).
- **A4**: LDA `S_W` non-singular (det > 0 with ridge ε = 1e-6).
- **A5**: re-run produces byte-identical α matrix.

## 6. What this experiment does NOT do

- It does NOT recompute the Arabic-peer α values from exp116 (they're already locked at `results/experiments/exp116_RG_scaling_collapse/`). exp125c uses ALL 11 corpora freshly through the cross-tradition loaders to ensure a uniform pipeline.
- It does NOT include hindawi-specific or ksucca-specific synthetic-unit caveats from V3.9 genre-scope audit; the RG-scaling test runs on whatever units the loaders return, with the ≥ 32 verses floor.
- It does NOT do the F68 universal-collapse test (already FALSIFIED at F68); this experiment focuses on the unification question.

## 7. Honest scope

If **PASS_alpha_lda_strong_AND_LOO_ROBUST**: the project gains its **strongest unification** — F78 candidate, full PASS, ROBUST. Subsumes Φ_M, F55, F75, F77 in a single mechanistically-interpretable scaling exponent per corpus.

If **PARTIAL_alpha_lda_strong_BUT_LOO_NOT_ROBUST** (mirrors F77): the unification exists at full pool but is overfitted to the specific 10 non-Quran corpora; F78 PARTIAL pending Path-C N≥18.

If **PARTIAL_alpha_lda_directional**: weaker than 5σ but Quran is directionally distinctive on the α-direction. Honest informational result.

If **FAIL_no_alpha_unification**: the per-feature α values, while individually distinctive (F68 result), don't combine into a single linear direction that subsumes Quran-distinctiveness. Honest negative datum; F77 LDA on raw features remains the headline unification candidate.

## 8. Output

Receipt: `results/experiments/exp125c_RG_scaling_alpha_unification/exp125c_RG_scaling_alpha_unification.json` containing:
- `verdict` (full + LOO, mirrors exp125b structure)
- `per_corpus_n_qualifying_chapters` (counts of chapters with ≥ 32 verses)
- `per_corpus_alpha_matrix` (11 × 4 dict)
- `per_corpus_per_feature_r2` (fit quality)
- `lda_loading_alpha` (4-vector, the unified α-formula)
- `alpha_LDA_score_per_corpus`
- `z_quran_alpha_LDA`, `max_other_abs_z_alpha_LDA`, `fisher_ratio_J_alpha`
- `loo_results` (10 LOO refits)
- `audit_report`
- `prereg_hash`, `wall_time_s`

## 9. Wall-time estimate

- Loading 11 corpora: **30-60 s** (cached file I/O for most; openpyxl for arabic_bible is the slow one).
- Coarse-graining + features at 5 scales × 11 corpora: **~30-60 s**.
- Power-law fits: **<1 s**.
- LDA + LOO: **<1 s**.

**Expected total wall-time: 1-3 minutes** on the user's machine.

---

**Filed**: 2026-04-29 night (V3.14.1 sub-task 2)
