# exp169_phoneme_class_markov — PREREG (FROZEN 2026-05-01)

## Operating principle
Quran is the reference. All quantities are intrinsic to the Quran.

## Hypothesis

The recited Quran exhibits structured **phoneme-class transitions**. Define
8 phoneme classes (frozen below). Compute the Markov-1 transition matrix
P(class_t = j | class_{t-1} = i) from the cleaned per-character sequence
of the Hafs vocalised text, then the conditional entropy

  H_1 = − ∑_i π_i ∑_j P_{ij} log₂ P_{ij}

where π is the stationary distribution. Compare to:

- **Shuffle null** (5 000 random permutations of the class sequence; same
  multiset, no temporal structure).
- **Single-symbol entropy H_0** = −∑ π_i log₂ π_i; the **mutual information
  I = H_0 − H_1** quantifies the predictive information one class carries
  about the next.

## Frozen 8-class scheme (Arabic phonemes)

| Class | Label             | Members                                         |
|------:|-------------------|-------------------------------------------------|
| 0     | short-vowel       | fatha, kasra, damma                             |
| 1     | tanween           | fathatan, kasratan, dammatan (counted as +nasal class) |
| 2     | madd / long-vowel | maddah, superscript alef, subscript alef, alef ا, alef-wasla ٱ, hamza-below, inverted damma, fatha-2-dots |
| 3     | nasal             | م ن                                              |
| 4     | liquid            | ل ر                                              |
| 5     | glide             | و ي                                              |
| 6     | emphatic          | ص ض ط ظ ق ع ح خ غ ء أ إ آ ؤ ئ ه                  |
| 7     | obstruent (other) | ب ت ث ج د ذ ز س ش ف ك ة ى                       |

Sukun U+0652 is dropped. Shadda U+0651 doubles the previous emitted class.
Cleanup uses the same strip rules as exp167.

## Tests (all intrinsic, vs shuffle null)

- **T1**: H_1 conditional entropy. One-tailed: Quran lower than null.
- **T2**: I = H_0 − H_1 mutual info. One-tailed: Quran higher than null.
- **T3**: maximum off-diagonal P_{ij} entry magnitude (peak transition
  preference). One-tailed: Quran higher than null.
- **T4**: spectral gap of P (1 − |λ_2|, where λ_2 is the second-largest
  eigenvalue). Smaller gap → stronger long-range memory.
  One-tailed: Quran's gap smaller than null.

## Verdict

Family α = 0.05; per-test α = 0.0125 Bonferroni.

- **PASS_MARKOV_STRUCTURE_QURAN_REFERENCE** — at least 3 of 4 pass and
  T1 (H_1) is one of the passing tests.
- **PASS_PARTIAL** — 1 or 2 pass.
- **FAIL** — 0 pass.

Locked observed values become published Quran phoneme-class
Markov constants regardless of verdict.

`frozen_at`: 2026-05-01.
