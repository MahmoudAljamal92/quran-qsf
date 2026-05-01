# exp125b_unified_quran_coordinate_lda — Pre-Registration

**Status**: PRE-EXECUTION (2026-04-29 evening, V3.14 candidate sprint, sub-task 4 — follow-up to exp125 PCA `FAIL_no_unification`)
**Hypothesis ID**: H81
**Owner**: Cascade
**PREREG hash**: locked at experiment seal time

---

## 1. The question

`exp125_unified_quran_coordinate_pca` returned `FAIL_no_unification` because **unsupervised PCA's PC1 captured Pāli-vs-poetry variance rather than Quran-vs-rest variance** (PC1 explained 57.46 % but Quran was only at z = −1.29 on it). However, PC2 (33.62 % variance) had Quran at z = +3.98 — the Quran-distinctive direction exists, but PCA didn't surface it as the dominant axis because the Quran is one corpus out of eleven and Pāli's distinctness from poetry is the bigger numerical-variance source.

Question: **Does Linear Discriminant Analysis (LDA) — the supervised analogue of PCA, designed to maximise between-class separation — find a single linear coordinate that places the Quran as a strict outlier with all other corpora tightly clustered?**

If LDA yields such a coordinate, it IS the **unified linear formula** answering the user's "old + new toolkit unification" question — derived under explicit Quran-vs-rest supervision.

## 2. Pool

Identical to exp122 / exp124 / exp125 (locked 11-corpus × 5-feature matrix).

## 3. Procedure (Fisher's Linear Discriminant — closed-form)

### Stage A — Standardise

Same as exp125 Stage A: build standardised 11×5 matrix `Z` with per-feature `z = (x − μ_f) / σ_f`.

### Stage B — Class means + within-class scatter

Define two classes:
- **Class Q (Quran-only)**: 1 sample, mean `μ_Q = z_quran`
- **Class R (rest)**: 10 samples, mean `μ_R = mean over c≠quran of z_c`

Within-class scatter (only the rest class has within-class variance — Q has 1 sample):
- `S_W = Σ_{c≠quran} (z_c − μ_R)(z_c − μ_R)^T`  (5×5 matrix, sum over 10 corpora)

Add small ridge `ε·I` (ε=1e-6) for numerical stability since `S_W` may be near-singular when D=5 features with N=10 samples.

### Stage C — Fisher direction (closed form)

The Fisher discriminant direction is:

```
w_LDA = S_W^{-1} · (μ_Q − μ_R)
```

Normalise `w_LDA` to unit length (so coefficients are interpretable).

### Stage D — Project + score

Same projection as PCA Stage D:
- `lda_score(c) := w_LDA^T z_c` for each corpus.
- Compute `mean_lda_non_quran`, `std_lda_non_quran`, `z_quran_lda`, `cv_lda_non_quran`, `max_other_abs_z_lda`.

### Stage E — Variance explained (informational)

LDA does not have a "variance explained" metric like PCA. Instead, report **Fisher ratio**:
- `J(w_LDA) := (w_LDA^T (μ_Q − μ_R))² / w_LDA^T S_W w_LDA`

This is the classical between-class / within-class variance ratio.

## 4. Acceptance criteria (pre-registered, frozen)

A unification is **PASS_lda_strong_unified** iff **all three**:
- **(a) Quran extremum**: `|z_quran_lda| ≥ 5.0`
- **(b) No competing outlier**: `max_other_abs_z_lda ≤ 2.0`
- **(c) Fisher ratio**: `J(w_LDA) ≥ 10.0` (between-class separation is ≥ 10× within-class scatter; standard LDA "well-separated" threshold)

**PASS_lda_unified** iff (a) AND (b) AND `J ≥ 5.0`.

**PARTIAL_lda_quran_extremum_low_J** iff (a) AND (b) AND `J ≥ 1.0` — separation exists but isn't strong.

**FAIL_no_lda_unification** otherwise.

## 5. Honest scope — caveats of LDA with N=1 in the focal class

This is essentially a **prototype-distance-based classifier** because the Quran class has only 1 sample. The receipt explicitly notes:

> **Caveat**: LDA with N_Q = 1 cannot estimate within-Quran variance. The Fisher direction reduces to `S_W^{-1} (z_quran − μ_R)`, the **Mahalanobis-distance-direction** from the non-Quran centroid to Quran. This is mathematically well-defined, but the Quran's z-score against the LDA-projected non-Quran cluster will be **inflated by construction** — LDA is *designed* to maximise this.

> **Honest interpretation**: a PASS here means "there exists a single linear combination that separates Quran from the cluster"; it does NOT mean "this combination is robust under N_Q > 1". For paper-grade, exp125b should be cross-validated by:
>  - LDA-by-leave-one-other-out: drop each of the 10 non-Quran corpora in turn, refit LDA, check if Quran still scores at |z|≥5 on the held-out direction.
>  - That's a **mandatory follow-up** if PASS.

LOO-cross-validation IS implemented in this experiment (Stage F).

### Stage F — Leave-one-out robustness

For each held-out corpus `c_h` (10 iterations):
- Refit LDA on the remaining 10 corpora (1 Quran + 9 non-Quran).
- Project all 11 corpora onto the new LDA direction.
- Record `z_quran_lda_loo[c_h]` and `max_other_abs_z_lda_loo[c_h]`.

Acceptance for **LDA_robust**: `min over c_h of |z_quran_lda_loo[c_h]| ≥ 4.0` AND `max over c_h of max_other_abs_z_lda_loo[c_h] ≤ 2.5`.

If LDA_robust holds: the unification is reproducible; promote candidate to F77.
If LDA_robust fails: the LDA unification is overfitted to the specific 10 non-Quran corpora; demote to PARTIAL.

## 6. Audit hooks

- **A1**: input sizing receipt SHA-256 must match `0f8dcf0f69106020fac6c596716b4729d78fdece828ebb83aba3aa2b0a79fc22`.
- **A2/A3**: feature/corpus presence checks identical to exp125.
- **A4**: deterministic — closed-form linear algebra, no random seed.
- **A5**: numerical sanity — `det(S_W + ε·I) > 0`; if not, fail with `FAIL_audit_singular_S_W`.

## 7. Output

Receipt: `results/experiments/exp125b_unified_quran_coordinate_lda/exp125b_unified_quran_coordinate_lda.json` containing:
- `verdict` (one of 5 ladder values)
- `lda_loading` (5-vector — the unified linear formula's coefficients)
- `lda_score_per_corpus`
- `quran_lda_score`, `z_quran_lda`, `max_other_abs_z_lda`, `cv_lda_non_quran`
- `fisher_ratio_J`
- `lda_loo_results` — 10 LOO iterations with z_quran and max_other |z| per iteration
- `lda_robust_verdict` (PASS / FAIL)
- `unified_formula_string`
- `audit_report`
- `prereg_hash`, `wall_time_s`

## 8. Wall-time estimate

Pure numpy (5×5 matrix inversion + 10 LOO refits). Expected wall-time: < 0.5 s.

---

**Filed**: 2026-04-29 evening (V3.14 candidate sprint, sub-task 4 — exp125 follow-up)
