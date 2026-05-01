# exp171_surah_constants — PREREG (FROZEN 2026-05-01)

## Operating principle
Quran is the reference. All quantities intrinsic to the Quran.

## Hypothesis

The locked Quran constants identified in exp167–exp169 (β_v2, ρ_lag1,
alt_rate, I) are PROPERTIES OF THE CANONICAL MUSHAF AS A WHOLE. This
experiment tests whether they are also well-defined at the surah
granularity, and whether the 114 per-surah values reveal:

- **H1 (structural invariance)** — small between-surah variance (CV < 0.1
  for at least 2 of 4 constants). Each constant is a corpus-level
  invariant, replicated at the surah scale.
- **H2 (outlier surahs)** — at most a handful of surahs are |z| > 3 on
  any single constant, and fewer than 5 are |z| > 3 on ≥ 2 constants.
  (Too many outliers means the constants are dominated by surah-specific
  content, not Quran-level substrate.)
- **H3 (length robustness)** — constants computed on short surahs are
  consistent with those computed on long surahs: Spearman |ρ| between
  each constant and `log(N_words_surah)` is less than 0.30.
- **H4 (positional drift)** — no linear drift of any constant with
  surah index 1..114: Spearman |ρ| between constant and surah index < 0.30.

## Observables (same as exp167–169)

- `β_v2`(surah) — word-duration PSD exponent (compute β directly if surah
  has ≥ 1024 words; else report NaN)
- `ρ_lag1_S`(surah) — lag-1 autocorrelation of the per-character sonority
  sequence restricted to that surah
- `alt_rate_S`(surah) — alternation rate of sonority
- `I`(surah) — mutual info H_0 − H_1 of 8-class phoneme sequence

## Procedure

1. Parse `quran_vocal.txt` into 114 surah blocks (using `surah|verse|text`
   prefix).
2. For each surah, compute the four constants using the v2 model.
3. Compute:
   a. mean, std, CV per constant;
   b. z-scores per surah;
   c. Spearman correlations of each constant with `log(N_words_surah)`
      and with surah index;
   d. outlier counts.
4. No shuffle null — this is a descriptive test of internal structure.
   The hypothesis tests are explicit threshold checks on the statistics.

## Frozen verdict criteria

| Test                                 | Pass iff                                                    |
|--------------------------------------|-------------------------------------------------------------|
| H1 invariance                        | ≥ 2 of 4 constants have CV < 0.10 (excluding β with NaNs)   |
| H2 multi-constant outliers           | < 5 surahs with \|z\| > 3 on ≥ 2 of 4 constants             |
| H3 length robustness                 | all 4 constants have \|ρ_Spearman(C, log-W)\| < 0.30        |
| H4 positional drift                  | all 4 constants have \|ρ_Spearman(C, idx)\| < 0.30          |

- **PASS_SURAH_CONSTANTS_INVARIANT** — all 4 tests pass. Constants are
  genuine corpus-level substrate invariants, replicated at surah scale.
  Publishes all 4 × 114 = 456 per-surah values as locked references.
- **PASS_PARTIAL** — 2 or 3 of 4 tests pass.
- **FAIL** — ≤ 1 tests pass.

`frozen_at`: 2026-05-01.
