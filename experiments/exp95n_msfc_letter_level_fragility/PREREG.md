# PREREG — exp95n_msfc_letter_level_fragility (H47)

**Hypothesis ID**: H47
**Filed**: 2026-04-27 morning (v7.9-cand patch G post-V1-iv successor)
**Pre-registered before any per-corpus letter-level Mahalanobis fragility scoring is performed.**

---

## 1. Background

`exp95m_msfc_phim_fragility` (H46) attempted to test the MSFC sub-gate
2D Quran-amplification claim using the canonical 5-D Φ_M features
(`el_rate`, `vl_cv`, `cn_rate`, `h_cond_roots`, `h_el`). The verdict was
`FAIL_audit_features_drift` (T² audit) AND, independently, all 7 corpora
produced `phim_fragility = 0.0000` because the canonical 5-D features
are sensitive only to verse-final letter changes and verse-first-word
changes — > 96 % of random consonant substitutions are mid-verse-and-mid-word
and don't move any feature. This is consistent with `PAPER.md §4.20 / R5`:
the canonical 5-D Φ_M operates at the rhyme / structural-coherence
scale, not the letter-substitution scale.

This pre-registered experiment H47 closes the same Quran-amplification
question using a **letter-level 5-D feature set** that responds to
interior consonant substitutions by design. The features are
language-agnostic (no Arabic morphology, no CamelTools, no
verse-final-aware statistics) and operate on the unit's
`letters_28`-normalised consonant skeleton.

---

## 2. Hypothesis

**H47** (one-sided, hash-locked).

Define the letter-level 5-D feature vector `Ψ_L(u) ∈ R^5` of a unit
`u` over its `letters_28`-normalised consonant skeleton `s = letters_28(u)`:

```
Ψ_L_1(u) = H_2(s) := Shannon entropy of letter-pair (bigram) distribution
                     over the 28-letter alphabet (log_2 units, 0–log2(784) range).
Ψ_L_2(u) = H_3(s) := Shannon entropy of letter-triple (trigram) distribution
                     over the 28-letter alphabet.
Ψ_L_3(u) = Gini(s) := Gini coefficient of unigram letter-frequency
                      distribution. 0 = uniform, 1 = single-letter dominance.
Ψ_L_4(u) = gzip_ratio(s) := |gzip(s)| / |s|, with gzip level 9.
Ψ_L_5(u) = log10(n_distinct_bigrams(s)) := log of the count of distinct
                      letter-pairs observed in `s`.
```

For each corpus C in the Arabic pool of 7
(`{quran, poetry_jahili, poetry_islami, poetry_abbasi, ksucca,
arabic_bible, hindawi}`):

1. Compute `X_C ∈ R^{n_C × 5}` per-unit feature matrix.
2. Compute centroid `μ_C = mean(X_C)` and inverse pooled covariance
   `S_C^{-1} = pinv(cov(X_C, ddof=1))`.
3. Pick `K_CANON = 3` canon units per corpus: the units with median
   total-letter count after `letters_28` (frozen rule).
4. For each canon unit `u`, generate `N_EDITS = 20` random
   single-consonant substitutions: pick a uniformly random verse, a
   uniformly random alphabetic position in that verse, and substitute
   with a uniformly random letter ≠ original from `ARABIC_CONS_28`.
   This is **interior-permitting** — every consonant position in every
   verse is eligible (not just verse-final).
5. Compute `Ψ_L(canon)` and `Ψ_L(edit)` for each edit, then
   `d_M(canon, edit; S_C^{-1}) = sqrt(Δψ^T S_C^{-1} Δψ)`.
6. The unit's edit-fragility statistic is the **median** over the 20
   edits of `d_M`. The corpus's edit-fragility is the **median**
   over the 3 canon units.

Define `phim_lvl_fragility(C)` = step 6's median.

**H47**: among the 7 Arabic corpora, the Quran has the strictly largest
`phim_lvl_fragility`, by margin > 1.5× over the next-ranked corpus.

This establishes a Quran-distinctive MSFC sub-gate at the *letter-level*
multivariate fingerprint level — an amplification claim that the 5-D
canonical Φ_M (verse-aggregate features) cannot test by design.

---

## 3. Verdict ladder (strict order)

The first matching branch fires.

1. `FAIL_audit_features_finite` — any unit produces a non-finite (NaN /
   Inf) value in any of the 5 features. Sanity hook for the entropy /
   gzip / Gini computations.
2. `FAIL_audit_singular_cov` — the per-corpus covariance matrix is
   numerically singular (smallest eigenvalue < 1e-12) for any corpus
   in the rank pool. Indicates degenerate features for that corpus.
3. `FAIL_audit_zero_displacement` — > 50 % of (canon, edit) pairs in
   any corpus produce `d_M = 0`. Sanity hook against the `exp95m`
   structural insensitivity failure mode.
4. `FAIL_quran_not_top_1` — Quran is not strictly the largest
   `phim_lvl_fragility` across the 7 Arabic corpora.
5. `PARTIAL_quran_top_1_within_eps` — Quran is rank 1 but margin ≤
   1.5× (`EPS_TOP1`).
6. `PASS_quran_strict_max` — Quran's `phim_lvl_fragility` is > 1.5×
   the next-ranked corpus.

---

## 4. Frozen constants

- `EPS_TOP1 = 1.5` (margin ratio for `PASS_quran_strict_max`).
- `K_CANON = 3` (canon units per corpus).
- `N_EDITS = 20` (random substitutions per canon unit).
- `MIN_VERSES_PER_UNIT = 2` (matches `expP7` to keep control pool consistent).
- `RNG_SEED = 95_000` (frozen seed for reproducibility).
- Corpus pool: `{quran, poetry_jahili, poetry_islami, poetry_abbasi,
  ksucca, arabic_bible, hindawi}`.
- Substitution alphabet: `ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"`.
- Substitution position rule: pick uniformly among positions in the
  verse where the character is in
  `ARABIC_CONS_28 ∪ {"ء", "أ", "إ", "آ", "ؤ", "ئ", "ة", "ى"}` (i.e.,
  any consonant or hamza/ta-marbuta-bearing variant). Excludes
  punctuation, whitespace, digits, diacritics.
- gzip compression level: 9 (default `compresslevel=9` in Python
  `gzip.compress`).
- Trigram alphabet: 28-letter (so trigram space size up to 21,952; in
  practice ~hundreds per unit).

---

## 5. Audit hooks

- `audit_features_finite`: every entry of every X_C must be finite.
- `audit_min_units_per_corpus`: every corpus must have ≥ `K_CANON`
  eligible units (`n_verses ≥ MIN_VERSES_PER_UNIT`).
- `audit_min_smallest_eigenvalue`: per-corpus covariance smallest
  eigenvalue must be ≥ `1e-12` for every corpus in the rank pool.
- `audit_d_M_finite`: every per-edit `d_M` must be finite (non-NaN,
  non-Inf).
- `audit_zero_displacement_fraction`: per corpus, fraction of
  (canon, edit) pairs with `d_M = 0` must be ≤ 0.5. Catches the
  `exp95m` structural insensitivity failure mode.

---

## 6. Reproduction

```powershell
$env:PYTHONIOENCODING="utf-8"; python -m experiments.exp95n_msfc_letter_level_fragility.run
```

Single-process; in-memory; ~5 min wall-time on a single core (gzip is
the dominant per-call cost).

Outputs:

- `results/experiments/exp95n_msfc_letter_level_fragility/exp95n_msfc_letter_level_fragility.json`
- `results/experiments/exp95n_msfc_letter_level_fragility/per_corpus_summary.csv`

---

## 7. Scope and disclaimers

- **What this PREREG closes** (if PASS): the Quran-amplification claim
  for MSFC sub-gate 2D under a letter-level feature set that does
  respond to interior 1-letter substitutions. Resolves the H46 design
  gap.

- **What this PREREG does NOT establish**: a cross-tradition claim
  (corpus pool is Arabic-only); a forgery-detection FPR/recall
  receipt (this is an *amplification* statement, not a detector); a
  structural Quran-uniqueness *law*. Does NOT replace the locked
  Gate 1 multivariate fingerprint (T² = 3,557, AUC = 0.998); does NOT
  modify F55 or F56.

- **Falsification clause**: if the verdict ladder fires
  `FAIL_quran_not_top_1`, the MSFC sub-gate 2D amplification claim is
  retracted (R55 in `RETRACTIONS_REGISTRY.md`) and corpus-level
  letter-level edit-fragility is documented as universal — the
  Quran's locked multivariate outlier status (Gate 1) and EL-fragility
  amplification (Gate 2C / F56) are unaffected.

---

*PREREG locked at this file's SHA-256 in `PREREG_HASH.txt`. Any change
to this file invalidates the lock and prevents `run.py` from
executing.*
