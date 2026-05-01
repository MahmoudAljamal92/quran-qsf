# expE8 — 114×114 gzip Normalised Compression Distance (NCD) matrix

**Generated (UTC)**: 2026-04-23T18:53:56+00:00
**Seed**: 42  |  **Permutations per test**: 1000  |  **Compression**: gzip level 9

## Pre-registration (set before execution)

- **H0-a (Mantel order)**: NCD uncorrelated with |i-j|.
- **H0-b (Era block)**: Mean NCD within-era == between-era.
- **H0-c (Silhouette)**: Era label silhouette inside shuffle-null CI.
- **STRUCTURED_NCD**: ≥ 2 of 4 nulls rejected at α = 0.01.

## Verdict — **STRUCTURED_NCD** (n significant = 3 / 4)

## NCD matrix summary

- **Off-diagonal**: min = 0.415, max = 0.996, mean = 0.914, median = 0.928, sd = 0.069
- **Compressed sizes**: median = 1,173 bytes (min 103, max 15,037)

## Null-hypothesis tests

| Test | Statistic | Obs | Null mean | Null sd | p | Reject α=0.01 |
|---|---|--:|--:|--:|--:|:-:|
| H0-a Mantel vs mushaf order  | r | +0.5901 | -0.0007 | 0.0217 | 0.0010 | YES |
| H0-a Mantel vs era adjacency | r | +0.0896 | +0.0005 | 0.0305 | 0.0120 | no |
| H0-b Era block diff (between − within) | Δ | +0.01275 | -0.00001 | 0.00429 | 0.0070 | YES |
| H0-c Era silhouette (one-sided) | s | +0.0125 | -0.0002 | 0.0032 | 0.0050 | YES |

## Hierarchical clustering (average linkage, 2 clusters): silhouette = +0.0743

## Outputs

- `expE8_ncd_matrix.npz` — 114×114 NCD matrix + per-surah C sizes + metadata
- `expE8_report.json` — all null-test numbers + verdict
- `expE8_ncd_heatmap.png` — colour heatmap
- `expE8_ncd_vs_order.png` — NCD vs |i-j| scatter + Mantel r