# exp167_tajweed_psd_v2 — PREREG (FROZEN 2026-05-01)

## Operating principle
Quran is the reference. Headline numbers are intrinsic to the Quran;
external corpora calibrate the metric only. Same as exp166.

## Why this exists
exp166 v1 model returned β = 0.158 (refuted pink noise) but failed riwayat
invariance (CV = 0.376). The character-set diagnostic showed that the
riwayat divergence is a v1 unicode-coverage gap, not a real Quran-internal
inconsistency. v2 fixes the coverage gap and adds the two highest-impact
tajweed context rules. **Pre-committed thresholds before running.**

## Frozen v2 tajweed phoneme-duration model

### Pre-processing
1. Drop all ASCII characters (codepoint < 128) — strips Hafs metadata
   columns, ASCII transliteration, and the `surah|verse|` prefix.
2. Drop Arabic-Indic digits U+0660–U+0669 (٠–٩).
3. Drop Arabic-Indic decimal separators U+066B–U+066C if present.
4. Drop tatweel U+0640 (kashida — no phonetic value).
5. Drop pause/sajdah/marker codepoints:
   U+06D6, U+06D7, U+06D8, U+06D9, U+06DA, U+06DB, U+06DC, U+06DD,
   U+06DE, U+06DF, U+06E0, U+06E1, U+06E2, U+06E3, U+06E4, U+06E5,
   U+06E6, U+06E7, U+06E8, U+06E9, U+06EA, U+06EB, U+06EC, U+06ED.
6. Drop NBSP U+00A0 and zero-width joiners (U+200C–U+200F).
7. Drop sajdah marker ۩ (U+06E9), end-of-ayah ۝ (U+06DD).

### Per-character durations (v2 table)
Identical to v1 plus four new diacritic codepoints:

| Codepoint | Glyph | Role           | Harakaat |
|-----------|:-----:|----------------|:---------|
| U+064E    | ◌َ     | fatha          | +1       |
| U+0650    | ◌ِ     | kasra          | +1       |
| U+064F    | ◌ُ     | damma          | +1       |
| U+064B    | ◌ً     | fathatan       | +2       |
| U+064C    | ◌ٌ     | dammatan       | +2       |
| U+064D    | ◌ٍ     | kasratan       | +2       |
| U+0651    | ◌ّ     | shadda         | +1       |
| U+0653    | ◌ٓ     | maddah         | +2       |
| U+0652    | ◌ْ     | sukun          | +1       |
| U+0670    | ◌ٰ     | superscript ᵃ  | +2       |
| **U+0655**| ◌ٕ     | hamza-below    | **+1**   |
| **U+0656**| ◌ٖ     | subscript ᵃ    | **+2**   |
| **U+0657**| ◌ٗ     | inverted damma | **+1**   |
| **U+065E**| ◌ٞ     | fatha + 2 dots | **+1**   |

### Consonants
The consonant alphabet is `ابتثجحخدذرزسشصضطظعغفقكلمنهويءأإآؤئةى`
**plus** alef-wasla U+0671 (ٱ, treated as alef = +1). Each consonant adds
+1 harakah.

### Context rules
1. **Madd-wajib detection**: if a word contains *both* a madd-context
   long-vowel (alif U+0627 or U+0671, waw U+0648, yaa U+064A) preceded by
   a sukun U+0652 or by maddah U+0653, *and* a hamza letter
   (U+0621, U+0623, U+0624, U+0625, U+0626) anywhere in the same word
   then add **+3 harakat** to the word total (one madd-wajib elongation
   per word, not per occurrence — conservative).
2. **Ghunnah upgrade**: for each occurrence of shadda U+0651 immediately
   followed by noon U+0646 or meem U+0645 (or preceded by — both orders
   in source text are scanned) within a word, add **+1 harakah** to that
   word total.

These two rules are the highest-impact tajweed context elongations in
Hafs; full tajweed has ~20 sub-rules but they are second-order corrections.

`d_word = max(1, sum(per-character durations) + (3 if madd-wajib else 0)
                                              + (#ghunnah-upgrades))`

## Frozen procedure (identical infrastructure to exp166)

1. Apply pre-processing to vocalised text.
2. Compute word-level duration sequence `D_v2`.
3. Welch PSD with nperseg = 2048, noverlap = 1024, hann window, fs = 1.0.
4. Drop DC bin. Restrict to inertial band f ∈ [10⁻³, 10⁻¹] cycles/word.
5. Linear regress log10(PSD) on log10(f); β = −slope.
6. Block-bootstrap 95 % CI (1 000 resamples, blocks of size 700).
7. Shuffle null (5 000 perms): p_shuffle.
8. Window robustness (nperseg ∈ {1024, 2048, 4096}): max |Δβ| < 0.10.
9. Riwayat invariance: repeat for Hafs + Warsh + Qalun + Duri + Shuba +
   Sousi. CV = std/|mean| across the 6 readings.

## Pre-committed thresholds (locked before run)

| Threshold        | Value         | Reasoning                              |
|------------------|--------------:|----------------------------------------|
| sanity drift     | \|β_v2 − β_v1\| < 0.5  | v2 should not radically change the spectrum from v1; if it does, that itself is a finding |
| pink-band        | β_v2 ∈ [0.8, 1.2]      | classic 1/f signature                  |
| shuffle-sig      | p_shuffle < 0.0125     | Bonferroni α/4                         |
| window-robust    | max\|Δβ\| < 0.10        | spectral estimator stability           |
| riwayat-CV       | CV < 0.05              | text-deterministic structure must converge across readings (this is the gate that v1 failed) |

## Frozen verdict criteria

- **PASS_PINK_QURAN_REFERENCE** — β_v2 ∈ [0.8, 1.2], all four gates pass.
  → publish β_v2 as Quran rhythm constant; pink noise hypothesis confirmed
  at higher fidelity model. **Paradigm-grade promotion candidate.**
- **PASS_STRUCTURED_QURAN_REFERENCE** — gates pass but β_v2 ∉ [0.8, 1.2].
  → publish β_v2 as the locked Quran rhythm constant; pink-noise prior
  rejected; whatever β_v2 is becomes the published reference value.
- **FAIL_NO_INTRINSIC_STRUCTURE** — p_shuffle ≥ 0.0125.
- **AMBIGUOUS_RIWAYAT_DRIFT** — riwayat CV ≥ 0.05 (means v2 still has a
  coverage gap; would need exp167b).
- **AMBIGUOUS_WINDOWS** — window robustness fails.
- **AMBIGUOUS_DRIFT** — \|β_v2 − β_v1\| ≥ 0.5; flag for code review.

`frozen_at`: 2026-05-01.
