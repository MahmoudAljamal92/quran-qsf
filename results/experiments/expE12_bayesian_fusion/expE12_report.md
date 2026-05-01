# expE12 — Bayesian channel fusion (Adiyat 864)

**Generated (UTC)**: 2026-04-23T19:54:35+00:00
**Seed**: 42  |  **Window N**: 5  |  **Variants**: 864
**Channels**: NCD, LEN_DIFF, UNI_L1, BI_L1, TRI_L1, WLEN_DIFF, SPEC, ENT_DIFF, VLCV_DIFF
**Max residual |ρ|**: 0.8582  |  **Copula correction used**: True

## Pre-registration (set before execution)

- **Null**: Bayesian Brier ≥ logistic-vote Brier (complexity not justified).
- **BAYES_CALIBRATED**: Bayesian Brier ≤ voting Brier − 0.01 AND ECE ≤ 0.10.
- **NULL_NO_CALIBRATION_GAIN**: below that threshold.

## Verdict — **BAYES_CALIBRATED** (Brier Δ = +0.1250, ECE(best bayes) = 0.0000)

## Model comparison

| Model | AUC | Brier | log-loss | ECE |
|---|--:|--:|--:|--:|
| L2 logistic (baseline) | 1.0000 | 0.1250 | 0.3466 | 0.2500 |
| KDE naive Bayes | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| KDE + Gaussian copula | 1.0000 | 0.0000 | 0.0000 | 0.0000 |

## Outputs

- `expE12_report.json` — numbers + verdict
- `expE12_calibration_plots.png` — ROC + reliability diagram