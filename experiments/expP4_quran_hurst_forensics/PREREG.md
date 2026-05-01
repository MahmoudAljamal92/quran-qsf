# expP4_quran_hurst_forensics — pre-registered prediction

**Date authored:** 2026-04-25, before any compute on this experiment.

**Status:** PREREG. The hypothesis below was authored **before** any null
distribution or detrended Hurst was computed.

---

## 1. Background and concern

`expP4_hurst_universal_cross_tradition` (today, earlier) reports the
surah-level word-count R/S Hurst for the Quran as **H = 0.914** — the
highest single Hurst value of any corpus / series we have measured in
the entire 8-corpus universe.

But there is an obvious confounder. **The canonical Mushaf order is
roughly "Sūrat al-Fātiḥa first, then surahs in DESCENDING length order"**,
with many local violations of that rule. The descending-length component
alone, if perfectly monotonic, would yield H ≈ 1.0 (the maximum) —
because monotonic sequences are perfectly self-similar at every scale.

Before claiming the Quran's H = 0.914 as a structural property of the
Mushaf order, we must rule out the trivial-monotonic explanation. That
is what this experiment does, with three orthogonal checks.

## 2. Pre-registered predictions

> **PRED-Q1 (canonical vs random permutation)**: The canonical Mushaf
> H_unit_words = 0.914 is significantly higher than the uniform-random
> permutation null of 5000 shuffles of the same 114 word-counts.
> Specifically: z = (0.914 − null_mean) / null_std > +3.0 with
> empirical p_one_sided < 0.001 (less than 5 of 5000 shuffles produce
> H ≥ 0.914).
>
> **PRED-Q2 (monotonic ceiling)**: A strict descending-length ordering
> of the same 114 word-counts (the "ideal anti-monotonic") yields
> H > 0.95.
>
> **PRED-Q3 (residual Hurst after detrending)**: After removing the
> linear trend in the canonical word-count sequence (`y[i] = a + b * i + r[i]`),
> the residual sequence r[i] still shows R/S Hurst > 0.6 — meaning the
> long-range memory is NOT entirely accounted for by the descending-
> length trend.
>
> **PRED-Q4 (cross-corpus generality)**: The same canonical-vs-permutation
> Hurst test on the other 7 corpora (Tanakh, NT, Iliad, Pali_DN, Pali_MN,
> Rigveda, Avestan) shows that ≥ 5 of the 7 also yield significant
> z > +3 — i.e. the canonical-order Hurst signal is broadly real across
> traditions, not a Quran-specific artefact.

## 3. Falsifiers

- **F1**: Canonical Mushaf H z-score against null permutations is < +2
  (i.e. the canonical 0.914 is within typical permutation variance).
  This would indicate the apparent signal is just an estimator artefact
  on the small (n=114) sample.
- **F2**: The detrended residual H drops to ≤ 0.50. The surah-level
  Hurst is *entirely* a descending-length trivial-monotonic effect; the
  Quran-specific arrangement carries no long-range memory beyond the
  obvious length sort.
- **F3**: < 3 of the 7 non-Quran corpora yield significant z > +3 on
  this same test. This would indicate the canonical-order Hurst is a
  Quran-specific artefact, not a cross-tradition universal.

## 4. Method (locked)

For each corpus C with units in canonical order, denote
y_C = unit-word-count sequence in canonical order.

  1. **H_canon**: R/S Hurst of y_C (matches today's earlier experiment).
  2. **H_perm distribution**: 5000 RNG-shuffled orderings of the same
     y_C, R/S Hurst of each, seed = 42 + corpus_index. Report null
     mean, std, and the z-score of H_canon vs null. Empirical
     p_one_sided = fraction of shuffles with H ≥ H_canon, with
     conservative floor 1 / (5001).
  3. **H_descending**: y_C sorted in strictly descending order, R/S
     Hurst (the monotonic ceiling).
  4. **H_residual**: detrend y_C with a linear regression i → a + b*i,
     extract residuals r_i = y_C[i] − (a + b*i), R/S Hurst of r.

Sanity check: H_canon for the Quran must reproduce 0.914 ± 1e-5
(same data, same estimator, same code path).

## 5. Reads / writes

- Reads only: all corpora via `raw_loader.load_all(...)`.
- Writes only under `results/experiments/expP4_quran_hurst_forensics/`.

## 6. Recovery / supersession

This experiment **scrutinises** the Quran H_unit = 0.914 finding from
`expP4_hurst_universal_cross_tradition`. Outcomes here decide whether
the new finding stands as a structural property of the Mushaf or
collapses into the descending-length trivial-monotonic effect.
