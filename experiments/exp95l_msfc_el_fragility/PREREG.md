# PREREG — exp95l_msfc_el_fragility (H45)

**Hypothesis ID**: H45
**Filed**: 2026-04-27 morning (v7.9-cand patch G post-V1-v)
**Pre-registered before any per-corpus EL_fragility scoring is performed.**

---

## 1. Background

`exp95k_msfc_amplification` (H44) tested whether the Δ_bigram safety
margin is amplified for Quran-as-canon among 7 Arabic corpora in
`phase_06_phi_m`. The verdict was `FAIL_quran_not_top_1`: Quran ranked
4th of 7 (margin 55.0), behind ksucca (427), hindawi (100), and
arabic_bible (84). The bigram-shift detector is universal mathematics
with no Quran-distinctive amplification.

This pre-registered experiment H45 closes a different sub-gate of the
Multi-Scale Forgery Cascade (MSFC). Sub-gate 2C ("EL drift detection")
fires when a verse-final-letter substitution alters the corpus's
verse-final letter distribution. The forgery question: given a
canonical text, what fraction of single-letter substitutions at random
verse-final positions actually disturb the EL count?

This fraction is **monotone in `p_max(C)`**, the canonical proportion
of verses ending in the most-common verse-final letter. Quran's
`p_max ≈ 0.501` (locked in `PAPER.md §4.5`) is the highest in the
Arabic-corpus pool. If H45 confirms the analytical ranking, sub-gate
2C provides a Quran-amplified MSFC layer to replace the failed
sub-gate 2A.

---

## 2. Hypothesis

**H45** (one-sided, hash-locked).

For a canonical Arabic corpus C with verse-final letters drawn from
the 28-letter Arabic alphabet, define:

```
EL_fragility(C) := p_max(C) × (27/28) + (1 − p_max(C)) × (1/28)
```

where `p_max(C)` is the maximum verse-final-letter frequency
(fraction of verses in C ending in the most common verse-final
letter) over the 28 Arabic consonants.

`EL_fragility(C)` is the analytical probability that a uniformly
random 1-letter substitution at a uniformly random verse-final
position changes whether the verse ends with the canon `p_max`
letter. It captures the per-edit detectability of forgeries that
disturb the rhyme-letter count.

**H45**: among the 7 Arabic corpora in `phase_06_phi_m`
(`quran`, `poetry_jahili`, `poetry_islami`, `poetry_abbasi`, `ksucca`,
`arabic_bible`, `hindawi`), the Quran has the strictly largest
`EL_fragility`, by a margin of > 1.5× over the next-ranked corpus.

This establishes a Quran-distinctive MSFC sub-gate at the rhyme-letter
level: per-edit forgery detectability of verse-final-letter
substitutions is uniquely amplified for `canon = Quran`.

---

## 3. Verdict ladder (strict order)

The first matching branch fires.

1. `FAIL_audit_pmax_quran_drift` — `p_max(quran)` differs from the
   `PAPER.md §4.5` locked value 0.501 by more than 0.02.
2. `FAIL_quran_not_top_1` — Quran is not strictly the largest
   `EL_fragility` across the 7 Arabic corpora.
3. `PARTIAL_quran_top_1_within_eps` — Quran is rank 1 but margin to
   next-ranked corpus is ≤ 1.5× (`EPS_TOP1`).
4. `PASS_quran_strict_max` — Quran's `EL_fragility` is > 1.5× the
   next-ranked corpus.

`PASS_quran_strict_max` supports the MSFC sub-gate 2C amplification
claim: the per-edit detectability of verse-final substitutions is
maximised when canon = Quran.

---

## 4. Frozen constants

- `EPS_TOP1 = 1.5` (margin ratio for `PASS_quran_strict_max`).
- `MIN_VERSES_PER_CORPUS = 100` (corpora with fewer total verses are
  reported but excluded from the verdict rank to avoid degenerate
  sample sizes).
- Corpus pool: `{quran, poetry_jahili, poetry_islami, poetry_abbasi,
  ksucca, arabic_bible, hindawi}`. `hadith_bukhari` and `iliad_greek`
  excluded per project conventions.
- Verse-final letter normalisation: the canonical 28-letter Arabic
  consonant set, identical to the `letters_28` pipeline used in
  `PAPER.md §4.5` and `exp95j`.
- `p_max(quran)` audit target: `0.501 ± 0.02` (matches `§4.5`).
- Bootstrap diagnostics (1000 resamples per corpus) are reported but
  not part of the verdict rule, which is computed from point estimates.

---

## 5. Audit hooks

- `audit_pmax_quran_reproduction`: must reproduce
  `p_max(quran) ∈ [0.481, 0.521]`.
- `audit_min_verses_per_corpus`: every corpus included in the
  rank-comparison must have ≥ 100 verses with valid verse-final
  consonants.
- `audit_empirical_matches_analytical`: empirical `EL_fragility` from
  10,000 random verse-final substitutions per corpus must agree with
  the analytical formula to within ±0.01 (sample size sufficient).

---

## 6. Reproduction

```powershell
python -m experiments.exp95l_msfc_el_fragility.run
```

Single-process; in-memory; ~seconds wall-time on a single core.

Outputs:

- `results/experiments/exp95l_msfc_el_fragility/exp95l_msfc_el_fragility.json`
- `results/experiments/exp95l_msfc_el_fragility/per_corpus_summary.csv`

---

## 7. Scope and disclaimers

- **What this PREREG closes** (if PASS): the Quran-amplification claim
  for MSFC sub-gate 2C only. Sub-gate 2A (Δ_bigram safety margin) is
  retracted by H44; sub-gate 2B (R2 sliding-window amplification) is
  separately tested under H46/H47 (`exp95m_msfc_phim_fragility`) and
  not addressed here.

- **What this PREREG does NOT establish**: a cross-tradition claim
  (corpus pool is Arabic-only); a forgery-detection FPR/recall
  guarantee (this is an *amplification* statement, not a detector
  receipt); a structural Quran-uniqueness *law* (all retracted laws
  remain retracted).

- **Falsification clause**: if the verdict ladder fires
  `FAIL_quran_not_top_1`, the MSFC sub-gate 2C amplification claim is
  retracted and EL-disturbance detection is documented as a universal
  mechanism with no Quran-specific amplification beyond the locked
  `EL = 0.7271` baseline.

---

*PREREG locked at this file's SHA-256 in `PREREG_HASH.txt`. Any change
to this file invalidates the lock and prevents `run.py` from
executing.*
