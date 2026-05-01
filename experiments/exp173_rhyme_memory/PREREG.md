# exp173_rhyme_memory — PREREG (FROZEN 2026-05-01)

## Operating principle
Quran is the reference. All quantities intrinsic to the Quran.

## Hypothesis

The 6,236-verse rhyme sequence R from exp172 is not Markov-1. There is
**higher-order memory**: knowing the last K rhyme classes predicts the
next rhyme substantially better than knowing only the last one.

The incremental predictability drop is

  ΔH(K) = H_{K-1} − H_K  = conditional entropy reduction when moving
  from order K−1 to order K memory.

**Saj'-only prediction**: ΔH(1) is large (simple rhyme-run persistence).
**Higher-order prediction**: ΔH(K > 1) is substantially > 0.

We also test **surah-level rhyme cycle structure**: each surah has a
modal rhyme; is the sequence of surah modal rhymes itself structured, or
random? The 114-surah modal-rhyme sequence is M = (m_1, ..., m_114).

## Tests

All on the 7-class rhyme alphabet from exp172.

- **T1**: ΔH(1) = H_0 − H_1. Report value; significant vs shuffle.
- **T2**: ΔH(2) = H_1 − H_2. Test whether Markov-2 adds meaningful
  predictability. Compare to shuffle null (which has zero information
  at any order above the marginal); test whether ΔH(2) > ΔH(2)_null
  by Bonferroni α = 0.01.
- **T3**: ΔH(3) = H_2 − H_3.
- **T4**: total compressibility H_0 − H_3. Fraction of single-symbol
  entropy eliminated by 3rd-order memory.
- **T5**: Surah modal-rhyme sequence M_1..M_114: lag-1 autocorrelation.
  Adjacent surahs tend to share modal rhyme? One-tailed upper vs shuffle.

## Procedure

- Build R from exp172 extraction logic (locked).
- Compute H_K via block counting with Laplace α = 1. For K ≥ 2, use
  sliding (K+1)-grams; entropy H_K = H((K+1)-gram) − H(K-gram).
- Shuffle null: 2 000 permutations. Compute ΔH(K) for K = 1, 2, 3.

## Frozen verdict criteria

α = 0.01 per test (Bonferroni over 5 tests).

- **PASS_HIGHER_ORDER_RHYME_MEMORY** — ΔH(2) and ΔH(3) both pass at
  α = 0.01. Implies Quran rhyme has genuine multi-verse memory beyond
  saj' persistence.
- **PASS_SAJ_MARKOV1_ONLY** — only ΔH(1) passes (rhyme is Markov-1).
- **PASS_SURAH_CYCLE** — T5 passes regardless of higher-order tests.
- **FAIL** — no tests pass.

`frozen_at`: 2026-05-01.
