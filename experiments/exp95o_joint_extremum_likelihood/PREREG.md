# PREREG — exp95o_joint_extremum_likelihood (H48)

**Hypothesis ID**: H48
**Filed**: 2026-04-27 morning (v7.9-cand patch G post-V1-v successor)
**Pre-registered before any per-corpus rank-of-Quran is computed under the panel below.**

---

## 1. Background and motivation

The project has produced a tight cluster of locked, paper-grade
Quran-distinctive findings:

- 5-D Hotelling T² = 3,557 vs control mean 178; AUC = 0.998 (`§4.1`)
- F55 universal 1-letter forgery detector by theorem (`§4.43.2`)
- F56 EL-fragility amplification: Quran rank 1 by 2.04× (`§4.44.3`)
- And a number of single-feature Quran rank 1 results scattered
  across `§4.5`, `§4.40.4`, `§4.5.1`, etc.

But the project has **also** produced honest negative results where
the Quran is NOT rank 1:

- R54 (sub-gate 2A): bigram-shift safety margin, Quran rank 4 of 7
- R55 (sub-gate 2D, letter-level form): Quran rank 6 of 7

The user's open question is: **"Is there anything more to advance the
experiment further or prove the Quran's uniqueness — beyond science?"**

This experiment occupies the exact boundary between science and
philosophy. It does not "prove" anything beyond what it computes. It
**does** produce the cleanest defensible *number* for joint-extremum
behaviour across the project's two locked feature spaces, with an
explicit permutation-based dependency correction so the answer is
honest about correlation structure.

The result, whatever it is, will be:

- A scientific calculation (not a proof).
- A premise for further philosophical / Bayesian arguments (which
  are outside science).
- A locked, reproducible number that future readers can verify.

---

## 2. Hypothesis

**H48** (one-sided, hash-locked).

Define a **panel of K = 10 features** drawn from the project's two
locked feature spaces:

**5-D Φ_M (verse-aggregate, locked in `phase_06_phi_m`)**:

1. `el_rate` = mean per-unit verse-final dominant-letter rate
2. `vl_cv` = mean per-unit verse-length coefficient of variation
3. `cn_rate` = mean per-unit connective rate
4. `h_cond_roots` = mean per-unit conditional root-bigram entropy
5. `h_el` = mean per-unit verse-final-letter Shannon entropy

**5-D Ψ_L (letter-level, locked in `exp95n_msfc_letter_level_fragility`)**:

6. `H_2` = mean per-unit bigram (letter-pair) Shannon entropy
7. `H_3` = mean per-unit trigram (letter-triple) Shannon entropy
8. `Gini` = mean per-unit unigram-letter Gini coefficient
9. `gzip_ratio` = mean per-unit |gzip(letters_28)| / |letters_28|
10. `log10_nb` = mean per-unit log10(n_distinct_bigrams)

For each feature φ_k and each corpus C in the Arabic pool of 7
(`{quran, poetry_jahili, poetry_islami, poetry_abbasi, ksucca,
arabic_bible, hindawi}`), compute the **corpus mean**
`μ_k(C) = mean over units u in C of φ_k(u)`. Build the 7×10 matrix
`M[c, k] = μ_k(c)`.

For each feature k, define `rank_k(C) ∈ {1, 2, ..., 7}` as the
descending rank of corpus C on feature k (1 = largest). A corpus is
**at extremum** on feature k if `rank_k(C) ∈ {1, 7}` — either the
largest or the smallest.

Define the **observed extremum count**
`S_obs := |{k : rank_k(quran) ∈ {1, 7}}|` ∈ {0, 1, ..., 10}.

Under the null hypothesis "Quran is statistically exchangeable with
the other 6 Arabic corpora" and uniform random independent ranks,
`S_obs` is binomial with parameters `(K = 10, p = 2/7)`. Naive null
expectation: `E[S_obs] = 10 × 2/7 ≈ 2.857`.

But the features are *not* independent — they cover the same 7
corpora and have non-trivial correlation structure. A correctly
calibrated null requires permutation testing.

**Permutation null** (frozen procedure):

For each of `N_PERM = 100,000` permutations, draw a uniformly random
permutation `π` of the 7 corpus labels. For each candidate
"Quran-position" `c* ∈ {1, ..., 7}` (the position to which Quran's
features are permuted), compute the extremum count
`S_perm[c*, π] := |{k : rank_k(c*) ∈ {1, 7} after permutation π}|`.

The empirical p-value for the observed Quran extremum count is

```
p_perm = (1 / N_PERM) × Σ_π 1{ max over c* of S_perm[c*, π] ≥ S_obs }
```

This is the **probability under random label assignment** that *some*
corpus would achieve at least as many extremum positions as Quran did.
It is correctly calibrated against the panel's correlation structure.

**H48**: the Quran's `S_obs` is large enough that `p_perm < 0.01`.

---

## 3. Verdict ladder (strict order; first match fires)

1. `FAIL_audit_features_finite` — any unit produces non-finite (NaN /
   Inf) value in any of the 10 features. Inherits the `exp95n` audit hook.
2. `FAIL_audit_panel_completeness` — the 7×10 corpus-mean matrix has
   any `NaN` cell after corpus-mean reduction (e.g., a corpus has 0
   units passing `MIN_VERSES_PER_UNIT = 2`).
3. `FAIL_no_extremum` — `S_obs < 4` (Quran is at extremum on fewer
   than 4 of 10 dimensions; the joint-extremum claim fails on its
   face).
4. `PARTIAL_moderate_extremum` — `S_obs ≥ 4` AND `p_perm ∈ [0.01, 0.05)`
   (substantively suggestive but not significant at 0.01).
5. `PASS_joint_extremum` — `S_obs ≥ 4` AND `p_perm < 0.01`.
6. `PASS_strong_joint_extremum` — `S_obs ≥ 6` AND `p_perm < 0.001`.

---

## 4. Frozen constants

- `N_PERM = 100_000` (permutation count for empirical null).
- `RNG_SEED = 95_000` (frozen seed; matches `exp95n` family).
- `MIN_VERSES_PER_UNIT = 2` (matches `expP7` and `exp95n`).
- Corpus pool: `{quran, poetry_jahili, poetry_islami, poetry_abbasi,
  ksucca, arabic_bible, hindawi}` (the 7 Arabic corpora in
  `phase_06_phi_m`).
- Panel: 10 features as enumerated in §2 above.
- Extremum definition: rank ∈ {1, 7} (two-sided).
- gzip compression level: 9 (matches `exp95n`).

---

## 5. Audit hooks

- `audit_features_finite`: every unit's 10-feature vector must be
  finite. Inherits structurally from `exp95n` for 5 letter-level
  features; new check for 5 Φ_M features.
- `audit_panel_completeness`: the 7×10 corpus-mean matrix has no
  `NaN` cells.
- `audit_min_units_per_corpus`: every corpus has ≥ 5 eligible units
  (sanity floor; well below typical n_units ≥ 41).
- `audit_phi_m_locked_quran_match`: Quran's corpus-mean of `el_rate`
  must match `PAPER §4.5` locked target `0.7271 ± 0.02` (verifies
  the project's locked verse-final letter rate). If this audit
  fails, the build is drifted and the run aborts.
- `audit_p_max_quran_match`: `p_max(quran)` (from F56's analytic
  computation) must match `PAPER §4.5` locked target `0.501 ± 0.02`.

---

## 6. Reproduction

```powershell
$env:PYTHONIOENCODING="utf-8"; python -m experiments.exp95o_joint_extremum_likelihood.run
```

Single-process; in-memory; ~3-5 min wall-time on a single core
(letter-level features dominate; permutation step is < 1 s).

Outputs:

- `results/experiments/exp95o_joint_extremum_likelihood/exp95o_joint_extremum_likelihood.json`
- `results/experiments/exp95o_joint_extremum_likelihood/per_feature_ranking.csv`

---

## 7. Scope and disclaimers

- **What this PREREG closes** (if PASS): a defensible *probabilistic*
  statement that the Quran's joint-extremum behaviour across the
  project's two locked feature spaces is unlikely under
  exchangeability with the 6 other Arabic corpora, with explicit
  correlation correction. The number is `p_perm < 0.01` (or whatever
  the empirical p turns out to be).

- **What this PREREG does NOT establish**:
  - A claim of divine authorship (that's a metaphysical question
    outside any experiment's scope).
  - A claim of cross-tradition uniqueness (corpus pool is Arabic-only).
  - A complete Bayesian likelihood ratio (this provides the
    **likelihood under one explicit null**; it does NOT supply the
    prior, which is philosophical).
  - Independence of the panel from the 5-D classifier statement
    (Gate 1's AUC = 0.998 is a multivariate separation; this is a
    per-dimension joint-extremum count — they are related but
    distinct statistics).

- **Honest negative anchoring**: the panel includes 5 letter-level
  features (Ψ_L) on which Quran was **independently observed** to
  rank 6 of 7 by Mahalanobis displacement (`exp95n` / R55). If
  Quran's per-feature ranks on Ψ_L are also non-extremum (rank 2-6
  on most), the panel will honestly count those as non-extremum,
  bringing `S_obs` down. This is the design's anti-cherry-pick safety.

- **Falsification clause**: if `S_obs < 4` or `p_perm ≥ 0.05`, the
  joint-extremum hypothesis is retracted (R56) and the project
  documents that per-dimension joint extremum is NOT a defensible
  Quran-distinctiveness claim across the two locked feature spaces.
  The locked Gate 1 multivariate fingerprint, F55 detector, and F56
  EL-fragility amplification are all unaffected (different statistics,
  different claims).

---

## 8. What this experiment can and cannot say about "uniqueness"

This is a **probability calculation**, not a proof of anything beyond
the calculation itself. The output is one number, with one explicit
null, on one explicit panel, on one explicit corpus pool. The reader
is then free to:

(a) Cite this number as a *premise* in a wider Bayesian or
    philosophical argument (which is outside science).
(b) Demand stronger or different statistical scaffolding (more
    panels, more nulls, more corpora — future work).
(c) Take the number as one piece of evidence among many, weighted by
    their prior, to update their belief about Quranic distinctiveness.

The project does NOT, and cannot, take the metaphysical step. It
provides the strongest defensible number it can, and stops there.

---

*PREREG locked at this file's SHA-256 in `PREREG_HASH.txt`. Any change
to this file invalidates the lock and prevents `run.py` from
executing.*
