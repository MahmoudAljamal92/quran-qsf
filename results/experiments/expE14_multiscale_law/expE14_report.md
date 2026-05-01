# expE14 — Multi-scale Fisher combination law

**Generated (UTC)**: 2026-04-23T20:09:56+00:00
**Seed**: 42  |  **Null pool size**: 2335 Band-A control units (leave-one-out per scale)

## Scales tested

| # | Scale | Statistic |
|---|---|---|
| S1 | letter | KL(letter unigram ‖ pooled control) |
| S2 | root proxy | letter-bigram conditional entropy |
| S3 | verse | \|DFA-H − 0.5\| on verse-length series |
| S4 | surah | mean Mahalanobis (5-D) of Quran units vs control centroid |
| S5 | corpus | \|L_TEL_Q − L_TEL_ctrl\| (§4.36 weights) |

## Observed p-values per scale

| Scale | Observed stat | p (empirical, vs control pool) |
|---|--:|--:|
| S1_letter_KL | 0.0178 | 0.879281 |
| S2_bigram_H | 0.3275 | 0.075771 |
| S3_DFA_H | 0.4054 | 0.426798 |
| S4_Mahalanobis | 8.8119 | 0.001284 |
| S5_L_TEL | 3.6355 | 0.000856 |

## Combined statistics

- **Fisher χ²₁₀ (no correction)**: 34.56  →  p = 1.483e-04
- **Brown-corrected χ² = 34.56, df_adj = 0.62**  →  **p = 1.413e-06**

## Shapley decomposition

| Scale | φ (Shapley) | % of combined evidence |
|---|--:|--:|
| S1_letter_KL | -0.1955 | -3.3% |
| S2_bigram_H | 0.8479 | 14.5% |
| S3_DFA_H | 0.3094 | 5.3% |
| S4_Mahalanobis | 2.3304 | 39.8% |
| S5_L_TEL | 2.5575 | 43.7% |

**Max single-scale share = 43.7%**

## Verdict — **MULTISCALE_LAW**

## Outputs

- `expE14_report.json` — all stats + R + Shapley
- `expE14_shapley_and_R.png` — Shapley bar chart + R heatmap