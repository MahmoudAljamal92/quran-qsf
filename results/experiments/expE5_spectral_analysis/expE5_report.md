# expE5 — Fourier + multitaper spectral analysis

**Generated (UTC)**: 2026-04-23T18:07:34+00:00
**Seed**: 42  |  **Shuffles**: 1000  |  **Multitaper**: DPSS K=7, NW=4
**Input**: `results/checkpoints/phase_06_phi_m.pkl → state['CORPORA']['quran']` (114 surahs, 6236 verses)

## Pre-registration (set before execution)

- **Null**: Shuffled PSD envelope indistinguishable from observed; series is 1/f^α persistent noise with no discrete rhythm.
- **Pass**: ≥ 1 frequency bin survives Bonferroni shuffle null AND obs/shuffle_p95 > 1.5.
- **RHYTHMIC** verdict if ≥ 6 such peaks; **SUGGESTIVE** if 1–5; **NULL_CHAOTIC_PERSISTENT** if 0.

## Verdicts

| Series | Verdict | α_obs | α_shuffle | α_AR(1) | sig bins / n_freq | big peaks |
|---|---|---:|---:|---:|---:|---:|
| verse-length | **RHYTHMIC** | 0.397 | -0.000 ± 0.018 | 0.630 ± 0.019 | 50 / 3119 | 49 |
| end-letter | **RHYTHMIC** | 1.017 | -0.000 ± 0.019 | 1.295 ± 0.018 | 128 / 3119 | 126 |

## Verse-length — top peaks

| # | Freq (1/verse) | Period (verses) | PSD | shuffle p95 | obs/p95 | p_shuffle | Bonferroni |
|--:|---:|---:|---:|---:|---:|---:|:--:|
| 1 | 0.00048 | 2078.67 | 6.573e-04 | 6.849e-06 | 95.97 | 0.00e+00 | ✔ |
| 2 | 0.00016 | 6236.00 | 7.110e-04 | 7.461e-06 | 95.30 | 0.00e+00 | ✔ |
| 3 | 0.00032 | 3118.00 | 6.043e-04 | 7.389e-06 | 81.79 | 0.00e+00 | ✔ |
| 4 | 0.00064 | 1559.00 | 4.809e-04 | 7.300e-06 | 65.89 | 0.00e+00 | ✔ |
| 5 | 0.00080 | 1247.20 | 2.071e-04 | 7.517e-06 | 27.56 | 0.00e+00 | ✔ |
| 6 | 0.00144 | 692.89 | 1.553e-04 | 7.531e-06 | 20.62 | 0.00e+00 | ✔ |
| 7 | 0.00160 | 623.60 | 1.488e-04 | 7.715e-06 | 19.28 | 0.00e+00 | ✔ |
| 8 | 0.00176 | 566.91 | 1.454e-04 | 7.702e-06 | 18.88 | 0.00e+00 | ✔ |
| 9 | 0.00112 | 890.86 | 1.312e-04 | 7.518e-06 | 17.44 | 0.00e+00 | ✔ |
| 10 | 0.00128 | 779.50 | 1.302e-04 | 7.576e-06 | 17.18 | 0.00e+00 | ✔ |

## End-letter — top peaks

| # | Freq (1/verse) | Period (verses) | PSD | shuffle p95 | obs/p95 | p_shuffle | Bonferroni |
|--:|---:|---:|---:|---:|---:|---:|:--:|
| 1 | 0.00112 | 890.86 | 4.864e-04 | 7.804e-06 | 62.33 | 0.00e+00 | ✔ |
| 2 | 0.00080 | 1247.20 | 4.245e-04 | 7.855e-06 | 54.04 | 0.00e+00 | ✔ |
| 3 | 0.00096 | 1039.33 | 4.140e-04 | 7.866e-06 | 52.63 | 0.00e+00 | ✔ |
| 4 | 0.00160 | 623.60 | 3.851e-04 | 7.603e-06 | 50.66 | 0.00e+00 | ✔ |
| 5 | 0.00176 | 566.91 | 3.771e-04 | 7.488e-06 | 50.35 | 0.00e+00 | ✔ |
| 6 | 0.00144 | 692.89 | 3.792e-04 | 7.800e-06 | 48.62 | 0.00e+00 | ✔ |
| 7 | 0.00128 | 779.50 | 3.467e-04 | 7.829e-06 | 44.28 | 0.00e+00 | ✔ |
| 8 | 0.00064 | 1559.00 | 3.220e-04 | 7.727e-06 | 41.68 | 0.00e+00 | ✔ |
| 9 | 0.00016 | 6236.00 | 3.213e-04 | 7.863e-06 | 40.86 | 0.00e+00 | ✔ |
| 10 | 0.00032 | 3118.00 | 2.892e-04 | 7.382e-06 | 39.18 | 0.00e+00 | ✔ |

## Per-surah scan (verse-length series, surahs with ≥ 40 verses)

- **Surahs analysed**: 57
- **Median top-peak period**: 16.80 verses
- **Mean top-peak period**: 41.24 verses
- **Range**: 2.05–286.00 verses

## Outputs

- `expE5_report.json` — machine-readable summary
- `expE5_spectra.npz` — full PSD arrays + shuffle envelopes + input series
- `expE5_psd_verse_length.png` — PSD figure for verse-length series
- `expE5_psd_end_letter.png` — PSD figure for end-letter series