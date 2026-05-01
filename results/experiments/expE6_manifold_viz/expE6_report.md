# expE6 — 2-D embeddings of 114×5 Quran feature matrix

**Generated (UTC)**: 2026-04-23T18:11:24+00:00
**Seed**: 42  |  **Shuffles**: 1000  |  **Embeddings**: PCA, t-SNE, Isomap
**Features**: EL, VL_CV, CN, H_cond, T  |  **z-score ref**: Arabic control pool (4719 units)

## Pre-registration (set before execution)

- **Null**: Moran's I and silhouette inside 95% CI of 1000 label shuffles.
- **POSITIVE_STRUCTURE**: both metrics significant on ≥ 2 of 3 embeddings.
- **PARTIAL_STRUCTURE**: ≥ 2 embeddings significant on one metric.
- **WEAK_STRUCTURE**: ≥ 1 embedding significant on any metric.

## Verdict — **PARTIAL_STRUCTURE**

| Embedding | Moran's I | Moran's I p | Silhouette | Silhouette p |
|---|---:|---:|---:|---:|
| PCA | +0.1182 | 0.0420 | +0.0083 | 0.3530 |
| TSNE | +0.2065 | 0.0040 | +0.0338 | 0.0570 |
| ISO | +0.1342 | 0.0310 | +0.0043 | 0.3890 |

## PCA — explained-variance ratio: PC1=0.498, PC2=0.246, sum=0.743

## Meccan vs Medinan (Al-Azhar classification)

- Meccan:  86 surahs
- Medinan: 28 surahs

## Outputs

- `expE6_report.json` — permutation-test results
- `expE6_embeddings.npz` — all embedding arrays + metadata
- `expE6_embedding_PCA.png` — PCA figure (order + era)
- `expE6_embedding_TSNE.png` — t-SNE figure (order + era)
- `expE6_embedding_ISO.png` — Isomap figure (order + era)