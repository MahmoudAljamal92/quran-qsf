# exp174_muqattaat_enrichment — PREREG (FROZEN 2026-05-01)

## Operating principle

Quran is the reference. All statistics intrinsic to the Quran.

## Context

The 29 surahs opened by **muqatta'at** (disjoint letters, الحروف المقطعة)
use 14 unique letters — exactly half of the 28-letter Arabic alphabet:

  ا  ح  ر  س  ص  ط  ع  ق  ك  ل  م  ن  ه  ي

A famous ≈ 14-century-old claim (documented systematically by
El-Naggar 1976, Khalifa 1974) holds that **each disjoint letter is
statistically over-represented in the surah(s) it heads**, after
stripping the opener itself and the basmalah.

The only prior test in this project (F4 / R16, chi-squared on
"topological keys" framing, p = 0.4495, FALSIFIED) did NOT test the
enrichment claim directly. This experiment is the first rigorous,
pre-registered, shuffle-null-calibrated intrinsic test of that claim.

## Data cleaning (frozen)

Source: `data/corpora/ar/quran_bare.txt` (no diacritics, 6236 verses).

1. Strip the basmalah `بسم الله الرحمن الرحيم` from verse 1 of every
   surah **except surah 1 (Al-Fatiha, where the basmalah is v1 itself)
   and surah 9 (At-Tawba, which has no basmalah)**.
2. For each muqatta'at surah, after the basmalah strip, remove the
   **specific muqatta'at opener letters** (listed in §3). For surah 42,
   strip `حم` from v1 and `عسق` from v2.
3. Letters considered = the 28-letter Arabic alphabet:
   ا ب ت ث ج ح خ د ذ ر ز س ش ص ض ط ظ ع غ ف ق ك ل م ن ه و ي
   plus normalisation: `أ إ آ ا ٱ` → `ا`, `ى` → `ي`, `ة` → `ه`.
   Hamza-on-seat variants `ؤ ئ ء` are dropped (not counted as a
   distinct alphabet letter).

## Muqatta'at opener table (frozen, Hafs standard)

| Surah(s)                        | Opener |
|---------------------------------|--------|
| 2, 3, 29, 30, 31, 32 (6 surahs) | الم    |
| 7                               | المص   |
| 10, 11, 12, 14, 15 (5 surahs)   | الر    |
| 13                              | المر   |
| 19                              | كهيعص  |
| 20                              | طه     |
| 26, 28 (2 surahs)               | طسم    |
| 27                              | طس     |
| 36                              | يس     |
| 38                              | ص      |
| 40, 41, 43, 44, 45, 46 (6 surahs)| حم    |
| 42                              | حم / عسق (v1/v2 split) |
| 50                              | ق      |
| 68                              | ن      |

Total: 29 surahs; 78 (surah, opener-letter) pairs.

## Statistics (frozen)

For each surah `s` and each letter `ℓ`, define:

  f_s(ℓ)       = count(ℓ, surah s body) / total letters in surah s body
  f_~s(ℓ)      = count(ℓ, outside surah s) / total letters outside surah s
  E(s, ℓ)      = f_s(ℓ) / f_~s(ℓ)   — **enrichment ratio**
  log_E(s, ℓ)  = log₂(E(s, ℓ))      — **log enrichment**

Aggregate observables over the 78 observed (s, ℓ) pairs:

- **T1** — **mean log-enrichment**: `⟨log₂ E⟩_obs`. One-tailed upper.
- **T2** — **fraction of pairs with E > 1**. Expected under null = 0.5.
  One-tailed upper.
- **T3** — **pooled-by-letter enrichment**: for each of the 14 unique
  disjoint letters, compute
    E_pool(ℓ) = [∑ over surahs headed by ℓ: count(ℓ, s)]
                / [∑ over surahs headed by ℓ: total letters in s]
                divided by the same ratio computed over the surahs ℓ
                does NOT head.
  Count the number of letters with E_pool > 1 (expected under null = 7).
  One-tailed upper.
- **T4** — **per-letter BHL survivors**: of the 14 unique letters, how
  many pass Bonferroni-Holm at family α = 0.05 (per-letter α = 0.05/14)
  on their pooled one-tailed z-score? Report count.
- **T5** — **top-rank-within-surah**: for each muqatta'at surah, is at
  least one of its opener letters in the top-3 most frequent letters
  of the surah body? Tally 29 surahs; compare to null.

## Shuffle nulls (frozen)

**Null B (surah permutation, primary)**: keep the 14 letters and the
opener-group structure fixed (e.g., "ALM" applies to 6 surahs). Randomly
permute which 29 surahs from the 114 get each opener group, preserving
group sizes. 10,000 permutations. Recompute T1–T5 each time.

**Null A (letter permutation, sanity)**: keep the 29 headed surahs and
opener-group structure fixed. Randomly choose 14 of 28 alphabet letters
to be "disjoint" and randomly assign them to the opener groups
respecting the observed group structure (3 letters in an "ALM"-size
group, 4 in "ALMS"-size, etc.). 10,000 permutations.

## Pre-registered verdict criteria

Bonferroni across 5 tests, family α = 0.05 → per-test α = 0.01.

- **PASS_MUQATTAAT_ENRICHMENT_PARADIGM** — all 5 tests pass α = 0.01
  under BOTH nulls AND the observed effect size is non-trivial
  (⟨log₂ E⟩_obs > 0.05 — i.e., mean enrichment ≥ 3.5 %).
- **PASS_STRONG** — ≥ 3 of 5 tests pass under primary Null B at α = 0.01.
- **PASS_PARTIAL** — 1 or 2 tests pass under Null B.
- **FAIL** — 0 tests pass under Null B.

If PASS_MUQATTAAT_ENRICHMENT_PARADIGM, the experiment resolves (in the
positive direction) a 14-century-old linguistic puzzle intrinsically,
which would be paradigm-grade.

If FAIL, the famous claim is cleanly retired — also valuable, extending
the R16 prior retraction with a second independent framing.

`frozen_at`: 2026-05-01.
