# exp52 — Acoustic / Phonetic Bridge, Full Quran

> Scales **Gem #1** (`DEEPSCAN_ULTIMATE_FINDINGS.md` §3.1 / §14) from the 2-surah
> proof-of-concept (`archive/archive_old_jsons/acoustic_v3_results_2026-04-02.json`,
> syllable → pitch r = 0.541, n = 63) to the full 114-surah Al-Minshawi Murattal
> recitation with **character-level forced alignment** and pre-registered
> falsifiable hypotheses.

---

## 1. Audio source

| Item | Value |
|---|---|
| Reciter | محمد صديق المنشاوي (Mohammed Siddiq Al-Minshawi) |
| Style | Murattal (medium-paced, not Mujawwad) |
| Files | `D:\القرآن الكريم\Mohammed_Siddiq_Al-Minshawi\001.mp3` … `114.mp3` |
| Total | 114 files, 1.67 GB, ≈ 29 h of audio |
| Format | MP3, 16 kHz mono after resample |

## 2. Text source

| Item | Value |
|---|---|
| Corpus | `data/corpora/ar/quran_vocal.txt` |
| Schema | `surah|verse|text_uthmani_diacritized` |
| Verses | 6 236 |
| Diacritics | Full Uthmani (ٌ ً ٍ ّ ْ ـَ ـُ ـِ ٰ ٓ ۖ ۗ …) |

## 3. Models

| Role | Model | Size | VRAM |
|---|---|---|---|
| CTC forced alignment (char-level) | `jonatasgrosman/wav2vec2-large-xlsr-53-arabic` | 1.26 GB | ~2 GB fp16 |
| (optional) rough ASR / verification | `tarteel-ai/whisper-base-arabic-quran` | 0.29 GB | ~0.8 GB fp16 |
| F0 / intensity / HNR | Praat 6.4 via `praat-parselmouth` | — | CPU |
| MP3 decoder | `librosa.load` + `imageio_ffmpeg` bundled ffmpeg | — | CPU |

## 4. Pipeline

```
Audio prep  →  Text prep   →  CTC forced align  →  Basmalah / taawudh anchor
                                                     ↓
Per-verse acoustic feature extraction  ←  Letter-level timestamps
                                                     ↓
Text features (syllable, madd, emphatic, ghunnah)    ↓
                                                     ↓
Correlation matrix, verse-shuffle null, per-surah aggregate
```

### 4.1 Text prep for CTC

The Wav2Vec2 tokenizer has 51 tokens (37 Arabic letters + 6 diacritics + `|` + specials).
It **lacks** some Uthmani-only marks. We:

1. Strip chars not in the vocab: `ٰ ٓ ۖ ۗ ۘ ۙ ۚ ۛ ۜ ۟ ۡ ۢ ۤ ۥ ۦ` and other rasm pointers.
2. Strip superscript small-alif after long vowels.
3. Keep a `back_index[i] → j` mapping from CTC-space char `i` to Uthmani char `j` so letter
   timestamps can be reported in the **original** vocalized text.

### 4.2 Basmalah / taawudh anchor

Al-Minshawi Murattal audio convention:

| Surah | Audio begins with |
|---|---|
| 1 (Al-Fatiha) | basmalah (**which is verse 1 itself**) |
| 9 (At-Tawbah) | taawudh, then verse 1 (no basmalah) |
| all others | taawudh, then basmalah, then verse 1 |

We prepend the known fixed strings to the alignment target:

```
TAAWUDH  = "أعوذ بالله من الشيطان الرجيم"
BASMALAH = "بسم الله الرحمن الرحيم"
```

and mark them as pseudo-verses (`-1` and `0`). They drop out of the correlation
analysis but give us **the exact t₀ for verse 1** from CTC timestamps — which directly
answers the user's "start from basmalah wherever it is" requirement.

### 4.3 Chunking strategy (for long surahs)

Pilot surahs (1, 103, 108, 112, 114) are all < 2 min — single-pass alignment.

For the full run, surahs > 3 min are processed as 30 s sliding windows with 5 s
overlap. For each chunk, alignment runs against the full surah text, and only the
central 25 s of each chunk's alignment is kept. Chunk boundaries are chosen on low-
energy frames (silence) detected by librosa's `effects.split`, so we never cut mid-word.

### 4.4 Acoustic features (per verse)

| Feature | Tool | Notes |
|---|---|---|
| `Duration_s` | verse-end − verse-start from CTC | — |
| `Mean_Pitch_Hz` | Praat `to_pitch(floor=75, ceil=500)` | male reciter range |
| `Pitch_Variance`, `Pitch_Range` | same | contour spread |
| `Mean_Intensity_dB` | Praat `to_intensity()` | loudness |
| `HNR_dB` | Praat `to_harmonicity_cc()` | voice quality / tajweed proxy |
| `Spectral_Centroid_Hz`, `Spectral_Rolloff85` | librosa | timbre |
| `Silence_before_s` | gap between previous verse end and this verse start | fawasil / pause test |

### 4.5 Text features (per verse)

Already in the archived `V_Acoustic_02` pipeline, now extended:

- `syllable_count` — short/long vowel count
- `madd_count` — elongation markers (ٓ ٰ) + known madd letters
- `word_count`, `char_count`
- `emphatic_count` — ص ض ط ظ ق (complements `exp46`/`exp47`)
- `ghunnah_count` — nasal marks (ن with shadda, م with shadda, tanween before ب/م)

## 5. Pre-registered hypotheses

| # | Claim | Threshold | Source |
|---|---|---|---|
| **H1** | syllable → mean pitch (pooled across 6 236 verses) | r ≥ 0.30, p < 10⁻¹⁰ | replicates Gem #1 at 100× scale |
| **H2** | madd → mean pitch | r ≥ 0.25, p < 10⁻⁵ | Gem #1 bridge |
| **H3** | shuffled-verse null: within-surah verse-order permutation collapses r by ≥ 3 σ | per-surah test | signal is structural, not artefact |
| **H4** | madd vowel duration median ≥ 1.8 × short-vowel median | ratio ≥ 1.8, bootstrap CI excludes 1.0 | empirical tajweed validation |
| **H5** | verse-final silence ≥ internal silence (Cohen's d ≥ 0.5) | d ≥ 0.5, p < 10⁻⁵ | fawasil / EL-channel prosodic validation |
| **H6** | emphatic consonants (ص ض ط ظ ق) held longer than non-emphatic pairs (س ت ث ك) | mean duration diff ≥ 20 ms, p < 0.01 | complements `exp47` phonetic-distance law |

## 6. Timing budget on GTX 1060 (6 GB)

| Stage | Rate (× real-time) | Full Quran wall-clock |
|---|---|---|
| MP3 decode | 60× | ~30 min |
| Wav2Vec2 CTC align (fp16, 30 s chunks) | 10-15× | ~2-3 h |
| Praat F0 + HNR + intensity | 5-8× | ~4-5 h (**bottleneck, CPU**) |
| Aggregate stats + figures | — | < 5 min |
| **Total** | | **~8-14 h** (plan to run overnight) |

Pilot on 5 short surahs (≈ 3 min audio): wall-clock ≈ **4 min**.

## 7. Output

All writes go under `results/experiments/exp52_acoustic_bridge_full/`:

- `pilot_results.json` — aggregate statistics, per-H verdicts, pilot surahs only
- `pilot_per_verse.csv` — one row per verse
- `pilot_per_letter.csv` — one row per aligned character
- `pilot_fig_scatter.png` — syllable vs pitch, 5-surah scatter
- `pilot_fig_alignment.png` — CTC alignment strip-plot for surah 1 (visual QC)
- `full_results.json`, `full_per_verse.csv`, `full_per_letter.csv`, `full_fig_*.png` — after the overnight run

## 8. What changes on paper if H1 replicates at n = 6 236

- `docs/DEEPSCAN_ULTIMATE_FINDINGS.md` PART 14 Gem #1: promoted from "PENDING" to "LOCKED".
- `docs/RANKED_FINDINGS.md` row 34: strength % jumps from 56 → ~80 (single-corpus full-scale replication).
- Qualitatively reframes the paper: from "the Quran is statistically different" to
  "**the text encodes its own oral delivery**". This is the strongest argument for the
  oral-transmission-optimisation law candidate LC2 (`RANKED_FINDINGS.md` LC-2).

## 9. Extensions (out of scope for pilot)

- Cross-reciter test: rerun on Al-Husary, Al-Ajmi, Al-Ghamdi (also in `D:\القرآن الكريم\`).
- Cross-corpus test: Abbasi poetry recitation, news broadcasts in MSA.
- Per-letter intensity → emphatic-consonant articulation law (refinement of `exp47`).
- Mujawwad vs Murattal style comparison on same surahs (stylistic invariance test).
