# expE13 — 1-of-865 authentication gate (Adiyat)

**Generated (UTC)**: 2026-04-23T19:56:14+00:00
**Window N**: 5  |  **Seeds**: [42, 43, 44, 45, 46]  |  **Texts**: 865 (1 canonical + 864 variants)
**Channels**: NCD, LEN_DIFF, UNI_L1, BI_L1, TRI_L1, WLEN_DIFF, SPEC, ENT_DIFF, VLCV_DIFF

## Gate definition

```
s(text) = log P(no_edit | channel_features(canon, text))
        - log P(edit    | channel_features(canon, text))
```

where `channel_features` is the 9-vector from expE11 at window N=5, and
`log P(·)` comes from a KDE Naive-Bayes model trained on the 864 variants
(class 1 = edit-in-window) vs their far-window counterparts (class 0).

## Pre-registration (set before execution)

- **Null**: canonical text rank = 1 with probability 1/865 ≈ 0.00116 under uniform prior.
- **GATE_SOLID**: rank = 1 on all 5 seeds AND empirical p ≤ 0.01.
- **GATE_USEFUL**: rank ≤ 10 on all 5 seeds.
- **NULL_GATE_FAILS**: any seed rank > 10.

## Verdict — **GATE_SOLID**

| Seed | canonical rank / 865 | empirical p |
|---|--:|--:|
| 42 | 1 | 1.1561e-03 |
| 43 | 1 | 1.1561e-03 |
| 44 | 1 | 1.1561e-03 |
| 45 | 1 | 1.1561e-03 |
| 46 | 1 | 1.1561e-03 |

- **Mean rank**: 1.00 / 865
- **Max rank**:  1 / 865
- **Mean empirical p**: 1.1561e-03
- **Theoretical uniform p**: 1.1561e-03

## Outputs

- `expE13_report.json` — gate stats + verdict
- `expE13_gate_histogram.png` — canonical vs variants histogram