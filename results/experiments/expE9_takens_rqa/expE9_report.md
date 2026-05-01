# expE9 — 3-D Takens embedding + RQA of Quran verse-length series

**Generated (UTC)**: 2026-04-23T18:58:04+00:00
**Seed**: 42  |  **N_orig**: 6236  |  **N_rqa (subsampled)**: 1248
**m**: 3  |  **tau (AMI first-min)**: 2  |  **eps (target RR=0.05)**: 3.0000
**Surrogates**: 200 AR(1) + 200 IAAFT

## Pre-registration (set before execution)

- **Null**: RQA metrics inside 95% CI of 500 AR(1) and 500 IAAFT surrogates.
- **STRUCTURED_DYNAMICS**: DET or LAM outside 95% CI on BOTH surrogate types.
- **PARTIAL_DYNAMICS**: DET or LAM outside 95% CI on exactly one surrogate type.
- **NULL_NO_DYNAMICS**: DET and LAM inside both bands.

## Verdict — **STRUCTURED_DYNAMICS**

## Observed RQA metrics

| Metric | Observed | AR(1) null mean ± sd | IAAFT null mean ± sd | p vs AR(1) | p vs IAAFT | Outside AR(1) 95% | Outside IAAFT 95% |
|---|--:|---|---|--:|--:|:-:|:-:|
| RR | 0.0565 | 0.0064 ± 0.0005 | 0.0389 ± 0.0026 | 0.0050 | 0.0050 | YES | YES |
| DET | 0.3737 | 0.0164 ± 0.0029 | 0.1569 ± 0.0344 | 0.0050 | 0.0050 | YES | YES |
| LAM | 0.5126 | 0.0344 ± 0.0079 | 0.2741 ± 0.0491 | 0.0050 | 0.0050 | YES | YES |
| L_max | 36.0000 | 4.1350 ± 0.8347 | 17.3550 ± 5.7331 | 0.0050 | 0.0199 | YES | YES |
| V_max | 56.0000 | 3.1300 ± 0.7022 | 20.5700 ± 8.1692 | 0.0050 | 0.0050 | YES | YES |
| ENTR | 3.1816 | 0.8397 ± 0.2043 | 2.1058 ± 0.2465 | 0.0050 | 0.0100 | YES | YES |

## Outputs

- `expE9_report.json` — all RQA numbers + surrogate p-values
- `expE9_embedding_rqa.npz` — Takens embedding arrays + AMI curve
- `expE9_recurrence_plot.png` — recurrence plot of observed series
- `expE9_surrogate_tests.png` — DET / LAM histograms vs observed
- `expE9_ami_curve.png` — auto mutual info lag scan