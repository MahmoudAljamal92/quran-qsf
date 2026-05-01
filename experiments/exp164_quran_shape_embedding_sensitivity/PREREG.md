# PREREG — exp164 Quran Shape Embedding Sensitivity

**Hypothesis** (frozen 2026-05-01, before observing any data outside what is
already locked in `exp163`):

The three BHL-significant cloud-shape descriptors from `exp163`
(`linearity_westin`, `planarity_westin`, `symmetry_score`) on which the Quran's
68-Band-A surah cloud was rank 1/8 across Arabic corpora and BHL-significant
at family-wise α = 0.01 vs a 10,000-bootstrap pool null in the **raw 5-D Φ_M**
embedding **continue to flag the Quran as rank 1 / BHL-significant** in at
least one **independent** embedding (whitened-Φ_M and/or alphabet-frequency-PCA).

Decision rule:

- **`PASS_PORTABLE_GEOMETRY`** — Quran is BHL-significant (family-wise α = 0.01
  over 9 tests = 3 descriptors × 3 embeddings) on **at least 2 descriptors in
  at least 2 embeddings**, with at least one of those embeddings being
  alphabet-frequency-PCA (i.e., independent of the Φ_M feature pipeline).
- **`PARTIAL_NON_PORTABLE_GEOMETRY`** — at least 1 descriptor BHL-significant
  in at least 1 non-raw embedding, but not the full PASS criterion.
- **`FAIL_PIPELINE_SPECIFIC`** — only the raw-Φ_M embedding gives BHL-significant
  results; the geometric distinctness from `exp163` is an artefact of the
  specific pipeline.

## Frozen constants

```
SEED            = 43      (different from exp163 to avoid shared-RNG drift)
N_BOOTSTRAP     = 10000
N_SUBSAMPLE     = 200
ALPHA_BHL       = 0.01    (family-wise alpha over 9 tests)
N_QURAN_TARGET  = 68      (matches exp163 Band-A filter)
PCA_DIMS        = 5       (for alphabet-frequency embedding)
TARGET_DESC     = ['linearity_westin', 'planarity_westin', 'symmetry_score']
```

## Embeddings tested

1. **`raw_phi_m`** — 5-D `(EL, VL_CV, CN, H_cond, T)` per surah, no transform.
   This is the `exp163` baseline; included as a sanity check.
2. **`whitened_phi_m`** — same 5-D features but Mahalanobis-whitened using the
   covariance of the **combined pool** (Quran ∪ all 7 Arabic controls,
   N_pool = 2,577). After this transform the pool is unit-isotropic; the
   Quran's residual shape is the part not explained by pool covariance.
3. **`alphabet_freq_pca5`** — independent feature pipeline. For each unit
   (surah / pseudo-surah / chapter), compute the 28-Arabic-letter frequency
   vector (folded to 28 letters via the same canonical fold as `exp95j`).
   Project all 2,577 units onto the top-5 PCs of the pool covariance.
   This embedding does **not** use any of the Φ_M features.

## Test family

For each (embedding, descriptor) pair (9 tests total):

- Compute the Quran cloud's observed descriptor on the 68 Band-A surahs.
- Bootstrap null: 10,000 draws of n = 68 from the combined pool in that
  embedding; descriptor distribution under random sampling.
- Two-sided p-value.
- Quran's rank against the 7 control corpora (each subsampled 200× to n = 68
  in that embedding, descriptor median taken).

Bonferroni-Holm correction applied across all 9 tests at family-wise α = 0.01.

## Audit hooks

- A1: `len(X_QURAN_band_A) == 68` reproduced.
- A2: `whitened_phi_m` projection of the pool has covariance ≈ I_5 (unit
  isotropy within ε = 1e-6 after ridge).
- A3: `alphabet_freq_pca5` PCA computed on combined-pool letter vectors;
  cumulative variance of top-5 PCs reported.
- A4: per-corpus N_units count cross-checked vs `exp163` for sanity.

## Expected counts-impact

- If `PASS_PORTABLE_GEOMETRY` → **F80 promotion is justified**; recommend the
  user lock it as a new F-row.
- If `PARTIAL` → finding stands as Tier-C observation; F-row promotion deferred
  pending more embeddings.
- If `FAIL` → original `exp163` result is real but pipeline-specific; remove
  F80 candidacy, keep `exp163` as a pipeline-internal observation.
