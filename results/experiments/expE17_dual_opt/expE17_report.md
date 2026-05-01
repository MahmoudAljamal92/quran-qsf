# expE17 — Canonical-order dual-optimization

**Generated (UTC)**: 2026-04-23T20:15:06+00:00
**Seed**: 42  |  **N random perms**: 10000

## Objectives (lower = better)

- **J1**: sum of squared Mahalanobis transitions between adjacent surahs,
  using Σ = Cov(Quran 5-D features over 114 surahs). Measures inter-surah
  smoothness of the ordering.
- **J2**: Shannon entropy (bits) of the 5-bit sign-direction sequence over
  the 113 adjacent transitions. Codes 3^5 = 243 possible sign patterns.
  Lower entropy = more rhythmic repetition of the same transition pattern.

## Pre-registration

- **Null**: Mushaf is not Pareto-better than Nuzul or ≥ 95 % of random perms.
- **MUSHAF_PARETO_DOMINANT**: Mushaf Pareto-beats Nuzul AND has q ≤ 0.05 on BOTH axes.
- **MUSHAF_ONE_AXIS_DOMINANT**: q ≤ 0.05 on exactly one of J1, J2.
- **NULL_NO_DUAL_OPT**: neither.

## Verdict — **MUSHAF_ONE_AXIS_DOMINANT**

## Numbers

| Ordering | J1 | J2 | J1 quantile among random | J2 quantile among random |
|---|--:|--:|--:|--:|
| Mushaf | 824.4498 | 4.7381 | 0.0000 | 0.8399 |
| Nuzul (Egyptian) | 842.1558 | 4.7975 | 0.0000 | 0.9431 |
| Random (mean ± sd) | 1130.1440 ± 45.3395 | 4.6362 ± 0.1031 | — | — |

- **Mushaf Pareto-beats Nuzul**: True
- **Fraction of perms Mushaf Pareto-beats**: 0.1601

## Caveats

- Nuzul order is the Egyptian Standard Edition (Azhar) — the most widely-cited
  reconstruction but NOT a uniquely-verified historical chronology.
- The choice of `Σ` (pooled Quran-only covariance) means J1 measures smoothness
  *relative to the Quran's own feature distribution*, not relative to an external pool.

## Outputs

- `expE17_report.json` — numbers + verdict
- `expE17_pareto_scatter.png` — (J1, J2) scatter with Mushaf / Nuzul / random perms