# exp172_saj_rhyme — PREREG (FROZEN 2026-05-01)

## Operating principle
Quran is the reference. All quantities intrinsic to the Quran.

## Hypothesis

The Quran is famous for **saj'** (rhymed prose): most consecutive verses
end in the same or phonetically similar rhyme letter (fasilah). We test
this intrinsically vs random permutations.

Define `R = (r_1, r_2, ..., r_{6236})` where `r_v` is the "rhyme class" of
verse `v`: the last non-diacritic, non-hamza-seat Arabic letter of that
verse's cleaned text. Group the 28 Arabic letters into a frozen
7-class rhyme-family scheme (below).

## Frozen 7-class rhyme-family scheme

Arabic rhyme practice groups letters by shared point/manner of
articulation. We use a conservative 7-class scheme:

| Class | Label       | Letters                                     |
|------:|-------------|---------------------------------------------|
| 0     | long-vowel  | ا و ي (alef, waw, yaa) + ى (alef-maksura)   |
| 1     | nasal       | م ن                                          |
| 2     | liquid      | ل ر                                          |
| 3     | coronal     | ت ث د ذ ز س ش ص ض ط ظ                       |
| 4     | labial      | ب ف                                          |
| 5     | dorsal      | ج ك ق خ غ                                    |
| 6     | guttural    | ح ع ه ء                                      |

Tied/glottalised and tanween are resolved to their underlying letter.
Tashkeel and pause marks are stripped before extraction.

## Tests

- **T1 (rhyme density)**: fraction of consecutive verse pairs with the
  **same rhyme class**. One-tailed: Quran higher than shuffle null.
- **T2 (long-run structure)**: mean run length of consecutive
  same-rhyme verses (geometric runs under null). One-tailed upper.
- **T3 (max run length)**: longest run of consecutive same-rhyme verses.
  One-tailed upper.
- **T4 (within-surah rhyme purity)**: for each surah, compute the
  fraction of verses whose rhyme class matches the surah's **modal
  rhyme**. Headline = mean across the 114 surahs. One-tailed upper.
- **T5 (rhyme entropy)**: Shannon entropy of the 7-class rhyme
  distribution of the full sequence. Compared to shuffle null.
  Two-tailed (Quran can be either more concentrated or more uniform).

Shuffle null: 5 000 random permutations of the rhyme-class sequence.
Bonferroni per-test α = 0.05 / 5 = 0.01.

## Verdict

- **PASS_SAJ_QURAN_REFERENCE** — ≥ 3 of 5 tests pass Bonferroni, and T1
  (rhyme density) is one of the passing tests.
- **PASS_PARTIAL** — 1 or 2 tests pass.
- **FAIL** — 0 tests pass.

`frozen_at`: 2026-05-01.
