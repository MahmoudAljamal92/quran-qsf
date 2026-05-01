# exp120_unified_quran_code — Unified Quran-Code D_QSF (V3.12 PREREG)

**Hypothesis ID**: H75 (V3.12)
**Filed**: 2026-04-29 afternoon
**Status**: PRE-REGISTERED, NO RESULTS YET (PREREG hash locked at file seal)

## 1. Question

Is there a *single* multivariate distance statistic — computed on the
universal 5-D feature space already locked in `exp109_phi_universal_xtrad`
(VL_CV, p_max, H_EL, bigram_distinct_ratio, gzip_efficiency) — under
which the Quran is the **unique global extremum** across the 11-corpus
cross-tradition pool, with permutation p-value below the multiple-test
Bonferroni-adjusted alpha?

The hypothesis answers the user-stated demand for *unification*: instead
of 5 separate per-feature ranks (where the Quran is rank 1 on H_EL and
rank 11 on p_max but middle-pack on the other 3), is there a *single*
composite that ranks Quran #1 with statistical significance?

## 2. Definition of D_QSF (frozen at PREREG seal)

For each corpus c in the 11-corpus pool, take the per-corpus median of
each universal feature f_i. Standardise across corpora:

  μ_i = mean over 11 corpora of median(c, f_i)
  σ_i = std  over 11 corpora of median(c, f_i)
  z_i(c) = (median(c, f_i) - μ_i) / σ_i

Define the **Unified Quran-Code distance** as the squared z-score sum
(Euclidean distance from cross-tradition centroid in standardised space):

  D_QSF(c) = sqrt(z_VL_CV²(c) + z_p_max²(c) + z_H_EL²(c)
                + z_bigram_distinct_ratio²(c) + z_gzip_efficiency²(c))

This is mathematically equivalent to a Mahalanobis distance under the
identity covariance (no inter-feature decorrelation; chosen for robustness
since 11 samples are too few for a stable 5×5 inverse covariance).

## 3. Outcome variables (frozen)

- **D_QSF_quran**: the Quran's unified distance score
- **D_QSF_rank_quran**: the Quran's rank (1 = farthest from centroid)
- **D_QSF_margin**: D_QSF(rank-1) − D_QSF(rank-2) (in standardised units)
- **perm_p_quran_rank_1**: under random shuffling of corpus labels across
  the 11 × 5 feature matrix, probability of Quran ranking 1

## 4. Verdicts (locked decision rule, frozen at PREREG seal)

| Verdict | Condition |
|---|---|
| `PASS_unified_quran_code_quran_rank_1` | Quran rank 1 AND perm_p < 0.05 |
| `PARTIAL_quran_rank_1_perm_p_above_0p05` | Quran rank 1 AND perm_p ≥ 0.05 (rank-based saturation; documented as honest constraint) |
| `FAIL_quran_not_rank_1_under_DQSF` | another corpus has higher D_QSF; F72 NOT created; FN14 added to RETRACTIONS_REGISTRY |

## 5. Permutation null (clarified pre-execution)

The D_QSF formula is **invariant under row-permutation** (means and stds
are pooled across corpora; reordering rows does not change any z-score).
Therefore the only non-degenerate permutation null is **independent
column shuffling**: for each of the 5 feature columns independently,
permute its 11 values across the corpora, breaking the multivariate
signature while preserving the marginal feature distributions.

Procedure (frozen at PREREG seal):
- For each of N=10,000 permutations under SEED=42:
  - For each of the 5 feature columns j:
    - Sample a random permutation of {0..10}
    - Reassign feature j's values to the corpora in that order
  - Compute D_QSF on the (now-multivariate-scrambled) matrix
  - Record whether the row labelled "quran" still ranks 1
- perm_p = (# perms where Quran rank 1) / N_perms

Floor: 1 / 11 ≈ 0.091 (rank-saturation; documented in FN13). Reaching
perm_p < 0.05 requires extending the pool to ≥ 22 corpora — see deliverable
#3 in the V3.12 backlog.

## 6. Bootstrap CI (informational, not part of verdict)

Per-corpus median is computed via 1,000 bootstrap resamples of unit-level
feature values. Report 95 % bootstrap CI on D_QSF(Quran) and on
D_QSF_margin.

## 7. Inputs

- `results/auxiliary/_phi_universal_xtrad_sizing.json` (11 corpora, 5
  features, n_units per corpus) — the locked sizing receipt from exp109.
- No new data is loaded; this is a *re-analysis* of already-locked data
  through a unified composite formula.

## 8. Frozen constants

- `SEED = 42`
- `N_PERMUTATIONS = 10000`
- `PERM_ALPHA = 0.05`
- `FEATURE_NAMES = ['VL_CV', 'p_max', 'H_EL', 'bigram_distinct_ratio', 'gzip_efficiency']`
- `EXPECTED_CORPORA = ['quran', 'poetry_jahili', 'poetry_islami', 'poetry_abbasi', 'hindawi', 'ksucca', 'arabic_bible', 'hebrew_tanakh', 'greek_nt', 'pali', 'avestan_yasna']`

## 9. Honest scope

- D_QSF is **not** claimed as a "universal law"; it is a *unified composite
  of 5 already-locked features* that allows a single ranking statement
  across 11 cross-tradition corpora.
- The pool size N=11 floors perm_p at 1/11 ≈ 0.091 (rank-saturation
  problem documented in FN13). To reach perm_p < 0.05, the pool needs
  ≥ 22 corpora — see `exp123_cross_trad_pool_extension`.
- The "Quran-distinctiveness" claim from this experiment is *over the 11
  tested corpora only*; it does not constitute an "all-text" universality
  proof. Pre-Islamic Arabic *kāhin* oracles, classical Arabic qasida
  poetry per-bayt, and other rhyme-genre-specialist texts remain
  un-tested.
- This experiment does **not** include the letter-scale F55/F69 or the
  meso-scale F70 features as those require per-unit forgery-planting
  which is computationally heavy. A V3.13 follow-up `exp124_DQSF_full_8layer`
  would add those.

## 10. PREREG seal

This file's SHA-256 hash is computed and written into the experiment
receipt as `prereg_hash`. Any subsequent edit invalidates the seal.
