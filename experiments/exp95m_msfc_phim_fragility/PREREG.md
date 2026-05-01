# PREREG — exp95m_msfc_phim_fragility (H46)

**Hypothesis ID**: H46
**Filed**: 2026-04-27 morning (v7.9-cand patch G post-V1-vi)
**Pre-registered before any per-corpus Φ_M edit-fragility scoring is performed.**

---

## 1. Background

`exp95k_msfc_amplification` (H44) tested whether the Δ_bigram safety
margin is amplified for Quran-as-canon among 7 Arabic corpora. Verdict:
`FAIL_quran_not_top_1` — Quran ranked 4 of 7 (margin 55.0).

`exp95l_msfc_el_fragility` (H45) tested whether the verse-final-letter
substitution detectability is amplified for Quran-as-canon. Verdict:
`PASS_quran_strict_max` — Quran rank 1 with `EL_fragility = 0.5009`,
margin ratio = 2.04× over poetry_islami (0.2453).

This pre-registered experiment H46 closes the third candidate Gate-2A
replacement: per-corpus 5-D `Φ_M` Mahalanobis edit-fragility. Each
corpus has its own multivariate centroid and covariance in 5-D feature
space (`[EL, VL_CV, CN, H_cond_roots, T]` from `src.features.features_5d`).
A 1-letter substitution shifts the unit's feature vector by a small
amount `Δφ`. Whether the shift is detectable depends on the corpus's
own natural feature spread: tight corpora (small covariance ⇒ large
Sinv eigenvalues) amplify the shift in Mahalanobis units; spread
corpora attenuate it.

The hypothesis: the Quran's natural feature cluster is sufficiently
tight that 1-letter substitutions produce the **largest median
Mahalanobis displacement** among the 7 Arabic corpora, beating the
ratio-test threshold `EPS_TOP1 = 1.5×` over the next-ranked corpus.

---

## 2. Hypothesis

**H46** (one-sided, hash-locked).

Fix the corpus pool `{quran, poetry_jahili, poetry_islami,
poetry_abbasi, ksucca, arabic_bible, hindawi}`.

For each corpus C:

1. Compute `X_C ∈ R^{n_C × 5}`, the per-unit 5-D feature matrix using
   `src.features.features_5d(verses, ARABIC_CONN)`.
2. Estimate the corpus centroid `μ_C = mean(X_C)` and the inverse
   pooled covariance `S_C^{-1} = pinv(cov(X_C, ddof=1))`.
3. Pick `K_CANON = 3` canon units per corpus: the units with median
   total-letter count (frozen rule below).
4. For each canon unit `u`, generate `N_EDITS = 20` random
   single-consonant substitutions: pick a random verse, a random
   alphabetic position in that verse, and substitute with a random
   letter ≠ original from `ARABIC_CONS_28`. Compute `φ_edit` on the
   modified verses.
5. The unit's edit-fragility statistic is the median over the `N_EDITS`
   edits of `d_M(φ_canon, φ_edit; S_C^{-1}) = sqrt(Δφ^T S_C^{-1} Δφ)`,
   the Mahalanobis displacement in the corpus's natural metric.
6. The corpus's edit-fragility is the median over the `K_CANON` units.

Define `phim_fragility(C)` = step 6's median.

**H46**: among the 7 Arabic corpora, the Quran has the strictly largest
`phim_fragility`, by a margin > 1.5× over the next-ranked corpus.

This establishes a Quran-distinctive MSFC sub-gate at the multivariate
fingerprint level: 1-letter edits displace the canon furthest in
standardised feature space when canon = Quran, supporting the
"fingerprint-fragility" framing.

---

## 3. Verdict ladder (strict order)

The first matching branch fires.

1. `FAIL_audit_features_drift` — recomputed Quran-band-A T² differs
   from `expP7_phi_m_full_quran` locked value 3,557.34 by more than
   30.0 (sanity for the feature pipeline).
2. `FAIL_quran_not_top_1` — Quran is not strictly the largest
   `phim_fragility`.
3. `PARTIAL_quran_top_1_within_eps` — Quran is rank 1 but margin ≤
   1.5× (`EPS_TOP1`).
4. `PASS_quran_strict_max` — Quran's `phim_fragility` is > 1.5× the
   next-ranked corpus.

---

## 4. Frozen constants

- `EPS_TOP1 = 1.5` (margin ratio for `PASS_quran_strict_max`).
- `K_CANON = 3` (canon units per corpus; median total-letter count
  rule below).
- `N_EDITS = 20` (random substitutions per canon unit).
- `MIN_VERSES_PER_UNIT = 5` (units with fewer verses are skipped from
  the canon-pick pool).
- `RNG_SEED = 95_000` (frozen seed for reproducibility).
- Corpus pool: `{quran, poetry_jahili, poetry_islami, poetry_abbasi,
  ksucca, arabic_bible, hindawi}`.
- Canon-pick rule: per corpus, sort eligible units by total letter
  count after `letters_28`, take 3 around the median index
  `[idx_50 - 1, idx_50, idx_50 + 1]` (clipped to bounds).
- Substitution alphabet: `ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"`.
- Substitution position: pick uniformly among positions in the verse
  where the character maps to a consonant in `ARABIC_CONS_28`
  (after diacritic stripping and folding). This excludes
  punctuation, whitespace, digits.
- Stopwords: `ARABIC_CONN` (paper §2.2 conservative 14-item list).
- T2 audit target: `T2_quran_bandA = 3557.34 ± 30.0`.

---

## 5. Audit hooks

- `audit_t2_quran_bandA_reproduction`: a band-A subset reproduction of
  the locked Quran-vs-Arabic-controls T² must lie within ±30.0 of
  3557.34. This catches drift in the feature pipeline.
- `audit_min_units_per_corpus`: every corpus must have ≥ `K_CANON`
  eligible units (`n_verses ≥ MIN_VERSES_PER_UNIT`).
- `audit_finite_mahalanobis`: all `K_CANON × N_EDITS` displacements
  must be finite (non-NaN, non-inf). Inf indicates a singular
  covariance and triggers `FAIL_audit_singular_cov`.

---

## 6. Reproduction

```powershell
python -m experiments.exp95m_msfc_phim_fragility.run
```

Single-process; in-memory; ~5-10 min wall-time on a single core
(dominated by per-unit `features_5d` computation across 4 833 Arabic
units).

Outputs:

- `results/experiments/exp95m_msfc_phim_fragility/exp95m_msfc_phim_fragility.json`
- `results/experiments/exp95m_msfc_phim_fragility/per_corpus_summary.csv`

---

## 7. Scope and disclaimers

- **What this PREREG closes** (if PASS): the Quran-amplification claim
  for MSFC sub-gate 2D (full-corpus Φ_M Mahalanobis fragility). It
  does NOT address sub-gate 2B (R2 sliding-window), which would
  require additional pre-registration (H47).

- **What this PREREG does NOT establish**: a cross-tradition claim
  (corpus pool is Arabic-only); a forgery-detection FPR/recall
  receipt (this is an *amplification* statement, not a detector); a
  structural Quran-uniqueness *law*.

- **Falsification clause**: if the verdict ladder fires
  `FAIL_quran_not_top_1`, the MSFC sub-gate 2D amplification claim is
  retracted and corpus-level multivariate edit-fragility is
  documented as universal (potentially favouring corpora with smaller
  natural variance regardless of their identity). The Quran's locked
  multivariate outlier status (T² = 3,557, AUC = 0.998) is unaffected.

---

*PREREG locked at this file's SHA-256 in `PREREG_HASH.txt`. Any change
to this file invalidates the lock and prevents `run.py` from
executing.*
