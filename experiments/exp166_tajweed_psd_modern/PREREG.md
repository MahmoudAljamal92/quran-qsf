# exp166_tajweed_psd_modern — PREREG (FROZEN 2026-05-01)

## Operating principle for sound-axis experiments going forward

**The Quran is the reference.** External corpora were used to *measure* its
distinctness on every previously-locked axis (F-Universal, Hotelling T²=3 557,
LC2 Rigveda z=−18.93, Maqamat saj' AUC=0.9902, etc.). With those measurements
locked in our favour, we now invert the telescope:

  *Whatever value the Quran takes on a sound-axis observable becomes the
  reference value for that observable.* Controls are reported only to calibrate
  the metric; they are not the headline.

This experiment instantiates the principle on the simplest text-derived sound
substrate: the deterministic word-level tajweed phoneme-duration time series.

## Hypothesis (frozen before computation)

Let `D = (d_1, d_2, ..., d_W)` be the word-level tajweed duration sequence of
the Quran in canonical Mushaf order, where `d_i ∈ ℕ⁺` is the count of harakaat
in word `i` under the per-character Hafs 'an 'Asim model below.

Let `S(f) = |Welch-PSD(D)|` be the Welch power spectral density.
Let `β` be the negative log-log slope of `S(f)` over the inertial decade
`f ∈ [10^−3, 10^−1]` cycles/word.

**Primary claim**: `β ∈ [0.8, 1.2]` ("pink noise"), the spectral signature of
self-organised structured natural systems (heartbeats, music, Bach, neural
firing, geological strata).

**Secondary claim**: the structure is in the *ordering*, not the multiset.
Random word-permutation null pushes `β → 0`.

**Tertiary claim**: the sound rhythm is a property of the *text*, not of any
particular reciter — proven intrinsically by computing `β` for each of the
five canonical riwayat (Warsh, Qalun, Duri, Shuba, Sousi) versus the Hafs
baseline. The CV of `β` across readings should be small.

## Frozen tajweed phoneme-duration model (Hafs 'an 'Asim, v1, per-character)

Identical to the STF_v7 archive prototype (`TAJWEED_WEIGHTS`); promoted here
into the modern frozen-PREREG infrastructure.

| Code point | Glyph     | Role                | Harakaat |
|-----------:|:---------:|:--------------------|:---------|
| —          | consonant | base                | 1        |
| U+064E     | ◌َ         | fatha               | +1       |
| U+0650     | ◌ِ         | kasra               | +1       |
| U+064F     | ◌ُ         | damma               | +1       |
| U+064B     | ◌ً         | fathatan            | +2       |
| U+064C     | ◌ٌ         | dammatan            | +2       |
| U+064D     | ◌ٍ         | kasratan            | +2       |
| U+0651     | ◌ّ         | shadda (gemination) | +1       |
| U+0653     | ◌ٓ         | maddah marker       | +2       |
| U+0652     | ◌ْ         | sukun               | +1 (closed-syllable)
| U+0670     | ◌ٰ         | superscript alef    | +2       |

Word duration `d_i = max(1, sum_{c ∈ word_i} weight(c))`. Whitespace and
non-Arabic characters are skipped. Verse separators are dropped (we work on
a continuous word sequence; verse-boundary effects deferred to future work).

This model is a coarse but deterministic approximation. It does not implement
context-dependent rules (madd-wajib, madd-jaiz, ghunnah upgrade on
shadda+nun/meem, idgham, ikhfa). Those refinements are pre-registered for a
future v2 model and are out-of-scope here.

## Frozen procedure

1. Load `data/corpora/ar/quran_vocal.txt`. Verify ≥ 70 000 words (sanity).
2. Compute `D` via the model above.
3. Compute Welch PSD with `nperseg = 2048, noverlap = 1024, window='hann',
   fs = 1.0`. Drop the DC bin.
4. Restrict to `f ∈ [10^−3, 10^−1]`. Linear regress `log10(PSD)` on
   `log10(f)`. Slope `m`. Define `β = −m`.
5. Block-bootstrap 95 % CI on `β`: 1 000 resamples of contiguous blocks of
   size 700 words.
6. Shuffle null: 5 000 random permutations of `D`. Recompute β each.
   p-value `p_shuffle = 1/N + #{β_null ≥ β_obs}/N`.
7. Window-robustness: repeat step 4 for `nperseg ∈ {1024, 2048, 4096}`.
   All three β must lie within `±0.10` of the 2048 estimate.
8. Riwayat invariance: repeat steps 1-4 for each of the five
   `data/corpora/ar/riwayat/{warsh,qalun,duri,shuba,sousi}.txt`. Report
   `β_riwayat` and `CV_β = std/mean` across all six readings (Hafs + 5).

## Frozen verdict criteria

Bonferroni correction across the 4 sub-tests (T1–T4) at family α = 0.05.

- **PASS_PINK_NOISE_QURAN_REFERENCE** — `β_obs ∈ [0.8, 1.2]` AND
  `p_shuffle < 0.0125` (Bonferroni) AND `CV_β < 0.05` AND windows all agree.
  → publish β as the locked Quran rhythm constant.
- **PASS_STRUCTURED_BUT_NOT_PINK** — `β_obs ∉ [0.8, 1.2]` BUT
  `p_shuffle < 0.0125` AND `CV_β < 0.05` AND windows agree.
  → publish β as the locked Quran rhythm constant; reject pink-noise prior;
  whatever value emerged becomes the reference value of the recited substrate.
- **FAIL_NO_INTRINSIC_STRUCTURE** — `p_shuffle ≥ 0.0125`. The ordering
  carries no spectral signature beyond the multiset; rhythm is statistical,
  not encoded.
- **AMBIGUOUS** — windows disagree by more than ±0.10, or CV_β ≥ 0.05 (i.e.,
  the riwayat disagree, suggesting model artefacts).

Whatever the verdict, the per-Quran β value becomes a published reference
constant: it is what the Quran-as-standard says about the spectrum of a
text-deterministic recited duration sequence. External corpora are *not*
tested here for the headline; if they are tested at all in this experiment
it is only to calibrate the metric (e.g., sanity check that white-noise
random text gives β ≈ 0).

## Locked outputs

`receipt.json` with all primary numbers; `fig_psd.png`; `fig_riwayat.png`;
`fig_shuffle_null.png`. No code or table changes after `frozen_at` timestamp
without an explicit pre-registered amendment in this file.

`frozen_at`: 2026-05-01.
