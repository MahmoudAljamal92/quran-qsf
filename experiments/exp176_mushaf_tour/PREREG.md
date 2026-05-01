# exp176 — Mushaf-as-Tour Coherence (PREREG, frozen 2026-05-01)

## Question

Is the canonical Mushaf order a low-distortion 1-D embedding of surah
letter/bigram-frequency space — i.e. does the sum of feature-space
distances between consecutive surahs in Mushaf order

    L_obs = Σ_{s=1..113} || f(S_s) − f(S_{s+1}) ||

lie below what would be expected from a random permutation of the
same 114 surahs, after controlling for known confounds (surah length,
Meccan/Medinan label)?

## Pre-committed framing

- The 114 surahs are treated as a permutation of a fixed multiset of
  per-surah feature vectors. Re-ordering does **not** change any per-
  surah feature; only the adjacencies change. So the test is purely
  about the *order* the Mushaf imposes on the surahs.

- Two feature families are committed to in advance:
  - **F1**: 28-D length-normalised letter-frequency vector (one entry
    per Arabic consonant in `ا ب ت ث ج ح خ د ذ ر ز س ش ص ض ط ظ ع غ ف ق ك ل م ن ه و ي`).
  - **F2**: 50-D length-normalised top-50 character-bigram vector
    (top-50 chosen by global Quran frequency).

  Both are computed from the bare (`quran_bare.txt`) text using only
  the 28 Arabic letters above (whitespace, punctuation, and diacritics
  are stripped).

## Statistic

For each feature family F ∈ {F1, F2} and each metric d ∈ {L2, cosine}:

    L(F, d) = Σ_{s=1..113} d(F_s, F_{s+1})

Pre-committed primary statistic: **L(F1, L2) on logN+M/D-detrended F1**.
Pre-committed secondary statistics: F1+L2 raw, F2+L2 detrended, F2+cos raw.

## Confound controls

Because letter frequencies vary smoothly with surah length and depend on
revelation period, we apply a per-feature OLS detrender:

    f_k(s) = β0 + β1·logN(s) + β2·logN²(s) + β3·logN³(s) + β4·1[Medinan]

and use the residuals as the feature vector. The Medinan label set is
the standard mushaf classification:
{2,3,4,5,8,9,22,24,33,47,48,49,55,57,58,59,60,61,62,63,64,65,66,76,98,99,110}.

## Null models

- **Null A** (primary): uniformly random permutations of the 114 surahs,
  applied to the same (detrended) feature matrix. B = 5000 permutations.
- **Null B**: random permutations *within* the M/D label
  (M-positions stay M, D-positions stay D), so adjacency-of-revelation-
  period structure is preserved at the position level. B = 5000.

For each null we compute the same statistic and report:
- z = (L_obs − ⟨L⟩_null) / std(L_null)
- p = (#{L_null ≤ L_obs} + 1) / (B + 1)   (one-sided, "shorter tour")
- fraction of nulls strictly below L_obs

## Pre-committed verdict thresholds

CONFIRM (paradigm-level architectural claim) iff **all** hold:
1. On the primary statistic (F1, L2, detrended), z ≤ −4 and p ≤ 0.001
   under both Null A and Null B.
2. On at least one of the secondary statistics, z ≤ −4 and p ≤ 0.001
   under Null A.
3. The fraction of Null A draws strictly below L_obs is ≤ 1 / B.

CONFIRM_WEAK iff (1) holds at z ≤ −2.5 and p ≤ 0.01 but (2) or (3) fail.

REFUTE otherwise.

## What this test is **not** claiming

- It does *not* claim Mushaf is the global 1-D minimum. A greedy
  nearest-neighbour tour beats it by ≈ 30 %. The claim is that Mushaf
  is *significantly* below the random-permutation distribution after
  M/D + length controls.
- It does *not* claim divine origin or semantic content.
- It does *not* address the revelation-order vs Mushaf-order debate.

The result is purely a quantitative architectural statement: the
canonical 1-D ordering preserves vocabulary-coherence between adjacent
surahs at a level that no random reshuffling (and no M/D-respecting
reshuffling) reaches.

## Frozen parameters

- B = 5000 permutations per null.
- Detrender: cubic in logN, linear in M/D dummy, OLS, per feature axis.
- Random seed: 20260501.
- Letter set: `ا ب ت ث ج ح خ د ذ ر ز س ش ص ض ط ظ ع غ ف ق ك ل م ن ه و ي`.
- Top-50 bigrams: chosen from the bare-text global concatenation.
- Distance: L2 (primary), cosine (secondary).
- Tie-handling: not applicable (continuous statistic).
