# expE11 — Local-window amplification scan (Adiyat 864)

**Generated (UTC)**: 2026-04-23T19:44:51+00:00
**Seed**: 42  |  **Variants**: 864  |  **Design**: within-variant null (window at V_FAR=10)
**Channels**: NCD, LEN_DIFF, UNI_L1, BI_L1, TRI_L1, WLEN_DIFF, SPEC, ENT_DIFF, VLCV_DIFF

## Verdict — **LOCAL_AMPLIFICATION** (Δ best − baseline@N=13 = +0.5673)

| Window N | AUC (5-fold) | F1 (5-fold) | Best single-channel AUC |
|--:|--:|--:|---|
| 1 | 0.9838 ± 0.0095 | 0.6594 | UNI_L1 (1.0000) |
| 2 | 0.9977 ± 0.0032 | 0.9988 | UNI_L1 (1.0000) |
| 3 | 0.9873 ± 0.0075 | 0.9936 | UNI_L1 (1.0000) |
| 5 | 1.0000 ± 0.0000 | 0.6667 | NCD (1.0000) |
| 8 | 1.0000 ± 0.0000 | 0.6667 | NCD (1.0000) |
| 13 | 0.4327 ± 0.0251 | 0.4531 | NCD (0.5000) |

## Per-letter-class AUC (composite score, best window)

- **guttural**: AUC = 1.0000
- **labial**: AUC = 1.0000
- **emphatic**: AUC = 1.0000
- **other**: AUC = 1.0000

## Outputs

- `expE11_report.json` — all numbers + per-window coefs + per-class AUCs
- `expE11_auc_vs_N.png` — AUC(N) curve with error bars