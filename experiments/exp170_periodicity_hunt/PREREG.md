# exp170_periodicity_hunt — PREREG (FROZEN 2026-05-01)

## Operating principle
Quran is the reference. All quantities intrinsic to the Quran.

## Hypothesis

If the Quran's recited substrate carries hidden periodicities — at any
period, including culturally-loaded ones — the autocorrelation function
of any of the three intrinsic sequences

  D = word-level tajweed-duration sequence (v2 model from exp167)
  S = per-character sonority sequence (4-class, from exp168)
  C = per-character phoneme-class sequence (8-class, from exp169)

will show a peak at the corresponding lag, significantly above the
random-shuffle null. **Three orthogonal sequences cross-confirm a real
periodicity.**

We test:

- **Lag-by-lag scan**: for each pre-registered lag L, compute the
  autocorrelation of each sequence at lag L and compare to the shuffle
  null distribution at the same lag.
- **Cross-sequence corroboration**: a finding at lag L is paradigm-grade
  only if it survives Bonferroni-Holm in **at least 2 of 3** sequences.
- **Spectral concentration**: spectral power at frequency f = 1/L vs the
  median spectral power, expected ratio under shuffle ≈ 1.

## Pre-registered lags

| Lag | Cultural / numeric significance                                 |
|----:|----------------------------------------------------------------|
| 7   | 7 oft-repeated verses; 7 heavens; 7 levels of recitation       |
| 11  | Arabic alphabet half (~14)                                     |
| 14  | 14 disjoint letters                                            |
| 19  | "Code 19" hypothesis (Khalifa)                                 |
| 28  | Arabic alphabet length                                         |
| 29  | Number of disjoint-letter surahs                               |
| 30  | 30 ajzaa division                                              |
| 50  | Mid-range null                                                 |
| 60  | Mid-range null                                                 |
| 100 | Even decimal control                                           |
| 114 | Total surah count                                              |

11 lags total. Family α = 0.05 → per-lag-per-sequence α = 0.05 / 33 =
0.00152 (Bonferroni over 11 lags × 3 sequences).

## Procedure

1. Load Hafs vocalised text. Build D, S, C using exp167/168/169 cleanup.
2. For each sequence X ∈ {D, S, C} and each lag L:
   a. ρ_obs(X, L) = lag-L autocorrelation of X.
   b. Spectral power ratio R(X, L) = PSD(X) at f = 1/L divided by median PSD.
3. Shuffle null (2 000 perms): for each X and each L, compute
   ρ_null(X, L) and R_null(X, L). One-tailed p-values:
   p_ρ(X, L) = #{|ρ_null| ≥ |ρ_obs|} / N
   p_R(X, L) = #{R_null ≥ R_obs} / N
4. Bonferroni-Holm at family α = 0.05 over the full 33-cell lag×sequence
   grid. Report which lags survive.

## Verdict

- **PASS_PERIODIC_QURAN_REFERENCE** — at least 1 lag survives BHL in
  ≥ 2 of 3 sequences (cross-sequence corroborated). Each surviving
  (sequence, lag) pair publishes its observed |ρ| and R as a locked
  Quran periodicity constant.
- **PASS_SINGLE_SEQUENCE** — at least 1 (sequence, lag) cell survives
  BHL but no cross-sequence corroboration; report as suggestive.
- **FAIL** — no cell survives BHL.

`frozen_at`: 2026-05-01.
