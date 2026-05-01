# PREREG — `exp152_pinnacle_robustness`

**Hypothesis ID**: H97_5_Surah_Pinnacle_Trio
**Created**: 2026-04-30
**Sprint**: V3.17 (post-V3.16 audit-correction sweep)
**Status**: pre-registered before run

## Hypothesis (substantive)

The Quran's joint-T² extremum at the sūrah-pool resolution is structurally
characterised by a **stable trio of sūrahs** {Q:074, Q:073, Q:002} that spans
the entire Quranic revelation timeline (Nöldeke chronological ranks 2 → 3 → 84
out of 114 sūrahs) and is bimodal in mechanism (rhyme-density extreme
{Q:074, Q:073} + length extreme {Q:002}).

This is **a different hypothesis** from `exp151_QFootprint_Quran_Internal`'s
H95, which asked whether ONE clearly-dominant sūrah exists (verdict
`FAIL_quran_internal_indeterminate` at 1/3 PREREG criteria PASS — Q:074 vs
Q:073 are statistically tied at 1.023× joint-T² ratio). H97 asks the
**substantively-aligned trio question**: is the trio {Q:074, Q:073, Q:002}
robust as a set, anti-conservative in chronological span under shuffle null,
and structurally separable from rank-4 / rank-5?

The trio identity {Q:074, Q:073, Q:002} is **not chosen post-hoc**; it is the
top-3 by joint Hotelling T² recorded in `exp151_QFootprint_Quran_Internal`'s
locked receipt `sub_B_top10_T2`. This PREREG tests robustness of THAT specific
trio under criteria appropriate to a SET hypothesis.

## Pre-registered acceptance criteria

| # | Criterion | PASS threshold |
|---|-----------|----------------|
| **A1** | Trio {Q:074, Q:073, Q:002} appears as top-3 BY SET in bootstrap resamples | ≥ 90 % (N=1,000) |
| **A2** | Trio chronological-rank range across Nöldeke ordering | ≥ 80 (out of N=114) |
| **A3** | Chronological-rank shuffle null at N=10,000: probability of 3 random sūrahs having range ≥ trio's observed range | < 0.05 |
| **A4** | Trio's joint-T² gap to rank-4: T²[rank-3] / T²[rank-4] | ≥ 1.20 |
| **A5** | Bimodal-mechanism check: top-1 ∪ top-2 verse-final-letter Shannon entropy median ≤ 0.50 bits AND rank-3 verse-count rank ≥ 100 (out of 114) | both directions PASS |

**Verdict logic**:
- 5/5 PASS → `PASS_pinnacle_trio_robust`
- 4/5 PASS → `PARTIAL_pinnacle_trio_directional`
- ≤ 3/5 PASS → `FAIL_pinnacle_trio_indeterminate`

## Frozen constants

```
TRIO_SURAH_IDS         = (74, 73, 2)        # locked from exp151 sub_B
N_BOOTSTRAP            = 1000
N_CHRONO_SHUFFLE       = 10000
RIDGE                  = 1e-3
SEED                   = 42
ALPHABET_SIZE_AR       = 28
GAP_RANK4_FLOOR        = 1.20
TRIO_RANGE_FLOOR       = 80
TRIO_BOOT_FREQ_FLOOR   = 0.90
CHRONO_NULL_ALPHA      = 0.05
HEL_TOP12_BITS_CEILING = 0.50  # rhyme-extreme bimodal-mode test
RANK3_VERSECOUNT_FLOOR = 100   # length-extreme bimodal-mode test
```

## Locked feature-axis order (SHA-256 input)

```
AXES = ["H_EL_surah", "p_max_surah", "Delta_max_surah", "VL_CV_surah",
        "bigram_distinct_surah", "gzip_eff_surah", "n_verses_surah",
        "mean_verse_words_surah"]
```

## Audit guardrails

- `prereg_hash` written into the receipt is the SHA-256 of THIS file.
- `feature_matrix_sha256` must match `exp151`'s recorded `0b0e751b5358f3b045049985bb4c894afc592e7fea189d5ce4a7ee4791974e55`
  (locked replication of the same 114 × 8 sūrah feature matrix).
- F79 cross-check: median H_EL_surah must agree with F79's locked 0.969 bits
  to within 0.01 (same audit as exp151).
- No locked-receipt mutation; this is a NEW receipt at
  `results/experiments/exp152_pinnacle_robustness/`.
- This experiment uses ONLY Hotelling T² (Brown-formula-invariant); no
  Stouffer-Z helper from `exp138` / `exp141` / `exp143` is invoked. Therefore
  immune to the V3.16 audit-correction class.

## Expected outcomes (best-effort prior, NOT a constraint on verdict)

A1 expected PASS: exp151 reports `boot_top3_overlap_freq = 0.932` (lower bound
on trio-as-SET stability since it counts ANY overlap; the strict trio-set
metric will be ≥ 0.90 with high probability).

A2 PASS by direct measurement (chrono-range = 84 − 2 = 82 ≥ 80).

A3 expected PASS: probability of 3 random integers from {1..114} having range
≥ 82 is small (≈ 0.005 by quick analytic estimate).

A4 PASS by direct measurement (35.32 / 28.63 = 1.234 ≥ 1.20).

A5 expected PASS: Q:074 + Q:073 are short Meccan sūrahs with very low
verse-final-letter Shannon entropy (mono-rhyme); Q:002 is the longest sūrah at
286 verses (rank 1 of 114).

If 5/5 PASS, the trio finding becomes **F80** in `RANKED_FINDINGS.md`. If
4/5, **PARTIAL F80**. If ≤ 3/5, the trio finding is documented as **O8** Tier-C
observation only.

## Receipt location

`results/experiments/exp152_pinnacle_robustness/exp152_pinnacle_robustness.json`
