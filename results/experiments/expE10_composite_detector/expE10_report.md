# expE10 — Optimal-weight composite detector (Adiyat 864)

**Generated (UTC)**: 2026-04-23T19:52:31+00:00
**Seed**: 42  |  **Window sweep**: N in [1, 2, 3, 5, 8, 13]  |  **Primary**: N=5
**Variants**: 864  |  **Channels**: NCD, LEN_DIFF, UNI_L1, BI_L1, TRI_L1, WLEN_DIFF, SPEC, ENT_DIFF, VLCV_DIFF
**CV**: 4-fold GroupKFold by letter-class (guttural/labial/emphatic/other)

_Extension over E11: adds LDA + GradBoost composites and searches the full N sweep for any regime where composite fusion beats the best single channel by ≥ 0.01 AUC._

## Pre-registration (set before execution)

- **Null**: composite AUC ≤ best-single AUC + 0.01 (no gain).
- **COMPOSITE_GAIN**: best composite AUC ≥ best-single AUC + 0.01.
- **NULL_NO_GAIN**: below that threshold.
- **CV design**: 4-fold GroupKFold grouped by letter class (guttural/labial/emphatic/other).

## Verdict — **NULL_NO_GAIN** (best composite−single gain = +0.0000 at N=1)

## Sweep summary

| N | best single (AUC) | L2_logistic | Fisher_LDA | GradBoost | Δ best composite − single | gain ≥ 0.01 |
|--:|---|--:|--:|--:|--:|:-:|
| 1 | UNI_L1 (1.0000) | 0.9784 | 1.0000 | 1.0000 | +0.0000 | no |
| 2 | UNI_L1 (1.0000) | 0.9969 | 1.0000 | 1.0000 | +0.0000 | no |
| 3 | UNI_L1 (1.0000) | 0.9830 | 1.0000 | 1.0000 | +0.0000 | no |
| 5 | NCD (1.0000) | 1.0000 | 1.0000 | 1.0000 | +0.0000 | no |
| 8 | NCD (1.0000) | 1.0000 | 1.0000 | 1.0000 | +0.0000 | no |
| 13 | NCD (0.5000) | 0.5000 | 0.5000 | 0.5000 | -0.0000 | no |

## Single-channel AUCs at primary N=5

| Channel | AUC |
|---|--:|
| NCD | 1.0000 |
| UNI_L1 | 1.0000 |
| BI_L1 | 1.0000 |
| TRI_L1 | 1.0000 |
| SPEC | 1.0000 |
| ENT_DIFF | 0.9745 |
| LEN_DIFF | 0.5000 |
| WLEN_DIFF | 0.5000 |
| VLCV_DIFF | 0.5000 |

## Feature importance (sorted by GradBoost)

| Channel | GradBoost | \|L2 coef\| (norm) | Single-channel AUC (primary N) |
|---|--:|--:|--:|
| TRI_L1 | 0.3023 | 0.0000 | 1.0000 |
| SPEC | 0.2321 | 0.0000 | 1.0000 |
| NCD | 0.2318 | 0.0309 | 1.0000 |
| BI_L1 | 0.2037 | 0.0000 | 1.0000 |
| UNI_L1 | 0.0301 | 0.0000 | 1.0000 |
| ENT_DIFF | 0.0000 | 0.0000 | 0.9745 |
| LEN_DIFF | 0.0000 | 0.0000 | 0.5000 |
| WLEN_DIFF | 0.0000 | 0.0000 | 0.5000 |
| VLCV_DIFF | 0.0000 | 0.0000 | 0.5000 |

## Youden-optimal threshold (best composite)

- **threshold**: 1.0000  |  **sensitivity**: 1.0000  |  **specificity**: 1.0000  |  **F1**: 1.0000

## Outputs

- `expE10_report.json` — all numbers
- `expE10_detector_plots.png` — ROC + PR + feature-importance