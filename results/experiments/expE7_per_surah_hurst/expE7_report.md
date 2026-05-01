# expE7 — Per-surah DFA Hurst + box-counting fractal dimension spectrum

**Generated (UTC)**: 2026-04-23T18:51:49+00:00
**Seed**: 42  |  **Shuffles**: 1000 whole + 100/surah  |  **nolds**: True
**Filter**: surahs with n_verses ≥ 40

## Pre-registration (set before execution)

- **Null**: per-surah H-distribution collapses to shuffle baseline (H ≈ 0.5).
- **PER_SURAH_PERSISTENT**: Wilcoxon H>0.5 p<0.05 AND residual > 0 AND ≥ 50% surahs sig.
- **PARTIAL_PERSISTENT**: Wilcoxon H>0.5 p<0.05 AND residual > 0.
- **WEAK_PERSISTENT**: Wilcoxon p<0.05 OR ≥ 30% surahs sig.

## Verdict — **WEAK_PERSISTENT**

## Whole-corpus (sanity re-check)

- **H_vl on 6236-pt series**: 0.9054  (reference published value: ~0.941)
- **H_el on 6236-pt series**: 1.2195
- **Shuffle-null H_vl**: 0.5407 ± 0.0138 (p vs obs = 0.0000)

## Per-surah H_vl statistics

- **Surahs analysed**: 57
- **H_vl median**: 0.8358  |  **mean**: 0.8815 ± 0.1895
- **Range**: 0.483 – 1.539
- **Surahs with H < 0.5**: 1  |  **H > 0.95**: 17
- **Wilcoxon H > 0.5 p**: 2.7127e-11
- **Length-regression**: slope = -0.1449, intercept = +1.5189, r = -0.371 (p = 4.474e-03)
- **Median residual after log(n) regression**: -0.0169
- **Intercept at median n_verses**: 0.8878
- **Fraction surahs with shuffle p < 0.05**: 0.193

## Outliers (top 5 highest and lowest H_vl)

| Surah | Label | n_verses | H_vl | D_vl | shuffle p |
|--:|---|--:|--:|--:|--:|
| 74 | Q:074 | 56 | 1.539 | 0.826 | 0.070 |
| 69 | Q:069 | 52 | 1.277 | 0.627 | 0.000 |
| 33 | Q:033 | 73 | 1.235 | 0.702 | 0.160 |
| 22 | Q:022 | 78 | 1.208 | 0.740 | 0.120 |
| 38 | Q:038 | 88 | 1.176 | 0.803 | 0.050 |
| ... | ... | ... | ... | ... | ... |
| 21 | Q:021 | 112 | 0.665 | 0.764 | 0.780 |
| 26 | Q:026 | 227 | 0.665 | 1.017 | 0.420 |
| 5 | Q:005 | 120 | 0.664 | 0.803 | 0.830 |
| 41 | Q:041 | 54 | 0.636 | 0.562 | 0.690 |
| 78 | Q:078 | 40 | 0.483 | 0.608 | 0.930 |

## Outputs

- `expE7_report.json` — per-surah records + aggregate statistics + verdict
- `expE7_hurst_spectrum.png` — H distribution histogram + length-regression plot