# exp168_sonority_sequencing — PREREG (FROZEN 2026-05-01)

## Operating principle
Quran is the reference. Headline numbers intrinsic to the Quran.

## Hypothesis

The recited Quran is a sequence of phonemes drawn from a sonority-ranked
alphabet. The **sonority sequencing principle** (Steriade 1988, Clements 1990)
predicts that natural-language syllables exhibit a sonority-rise-then-fall
pattern (sonority peaks at the vowel, falls at margins). In a continuous
recited text, this should produce:

1. **Negative lag-1 autocorrelation** in the per-character sonority series
   (each character tends to be different in sonority from its neighbour).
2. **Distinctive PSD shape** — characteristic high-frequency power from the
   alternation between consonant (low sonority) and vowel (high sonority).

We test these intrinsically vs random-shuffle null:

- **T1**: lag-1 autocorrelation of `S = (s_1, s_2, ..., s_N)` where `s_i` is
  the sonority of character `i` in the cleaned vocalised text. Compare to
  shuffle null.
- **T2**: PSD spectral exponent β over inertial band [10⁻³, 10⁻¹] cycles
  per character. Compare β_obs to shuffle null.
- **T3**: peak-frequency ratio: position of the dominant spectral peak
  in PSD relative to total power. Compare to shuffle null.
- **T4**: vowel-consonant alternation rate: fraction of adjacent character
  pairs that have different sonority class. Compare to shuffle null.

## Frozen sonority table (Arabic, 4-class)

| Class           | Sonority | Code-points / chars                                |
|-----------------|---------:|----------------------------------------------------|
| Vowel           | 4        | fatha, kasra, damma, fathatan, kasratan, dammatan, |
|                 |          | superscript alef, subscript alef, hamza-below,     |
|                 |          | inverted damma, fatha-2-dots, alef ا (when not as  |
|                 |          | hamza-bearer; we treat ا as vowel always for       |
|                 |          | simplicity), maddah                                |
| Glide / liquid  | 3        | و ي ل ر                                             |
| Nasal           | 2        | م ن                                                |
| Obstruent       | 1        | all other consonants (stops, fricatives, glottals): |
|                 |          | ب ت ث ج ح خ د ذ ز س ش ص ض ط ظ ع غ ف ق ك ه ء أ إ آ ؤ ئ ة ى ٱ |

The sukun U+0652 is **dropped** from the sonority sequence (it marks
absence of vowel, not a phoneme). Shadda U+0651 doubles the preceding
consonant (we emit the prior class twice). Tanween (fathatan, etc.)
emits *vowel + nasal* (sonority 4 then 2). Cleanup uses the same strip
rules as exp167 (drop ASCII, Arabic-Indic digits, pause/sajdah marks,
tatweel, NBSP, ZW joiners).

## Procedure

1. Load Hafs vocalised text. Apply exp167 cleanup.
2. Walk the cleaned text character-by-character, emitting sonority values
   per the rules above. Result: `S` (length N ≈ 250–350 K characters).
3. Compute T1 (lag-1 ρ), T2 (PSD β), T3 (peak-freq ratio), T4 (alt rate).
4. Shuffle null: 5 000 random permutations of `S`. Re-compute the four
   statistics each. Compute z-scores and one-tailed p-values.
5. Window robustness for T2 (PSD β): nperseg ∈ {2048, 4096, 8192}.

## Frozen verdict criteria

Bonferroni correction: family α = 0.05 → per-test α = 0.0125.

- **PASS_SONORITY_PRINCIPLE_QURAN_REFERENCE** — at least 3 of 4 tests pass
  Bonferroni at α/4. Lag-1 autocorrelation must be one of the passing
  tests (it is the load-bearing structural prediction). All four T1–T4
  Quran observed values are published as locked Quran sonority constants.
- **PASS_PARTIAL** — only 1 or 2 of 4 tests pass.
- **FAIL** — 0 of 4 tests pass.

`frozen_at`: 2026-05-01.
