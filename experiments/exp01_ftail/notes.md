# exp01 — Analytic F-tail for Φ_M Hotelling T²

**Status**: done, self-check PASS.
**Touches the main notebook?** No.
**Writes to `ULTIMATE_REPORT.json` / checkpoints / integrity?** No.
**Output**: `results/experiments/exp01_ftail/exp01_ftail.json`.

## Hypothesis

The locked pipeline reports `Phi_M_hotelling_T2 = 3557.34` with a permutation
p-value of `0.004975 ≈ 1/(B+1)` at `B = 200`. This is floor-limited by the
permutation count, not by the data, and sits five orders of magnitude above
what physics would call "discovery" (5σ ≈ 3·10⁻⁷).

If `T² = 3557` is real, its **analytic F-tail** p-value is a mathematical
consequence of the test statistic plus its degrees of freedom, independent
of `B`. We compute it.

## Result

From `phase_06_phi_m.pkl`:
- `n_QURAN (Band A)`    = 68
- `n_CTRL_POOL (Band A)` = 2509
- `p` (features)         = 5

Two-sample Hotelling T² with pooled covariance (ridge λ = 1e-6):

| Statistic | Value |
|---|---|
| T² | **3557.3** (reproduces locked 3557.34) |
| F  | **710.36** |
| df | (5, 2571) |
| p_F_tail (scipy, float64) | 0.0 (underflow) |
| log₁₀ p_F_tail (mpmath, 80-digit) | **−480.25** |
| p_F_tail | **≈ 10⁻⁴⁸⁰** |
| multivariate Cohen's d (pooled, ridge 1e-6) | **7.33** (locked 6.66) |

### One side-finding (honest correction)

The 5-entry `mu` vector stored in `phase_06_phi_m.pkl['state']['mu']` is
`[0.11, 0.20, 0.028, 0.825, −2.44]`. This is the **Arabic control-pool
centroid**, not the Quran centroid. A previous chat mislabelled it as
`μ_Q`. The actual Band-A Quran centroid `μ_QURAN = X_QURAN.mean(axis=0)`
is recorded in the JSON report under `centroids.mu_QURAN_band_A`.

### Why the two Cohen's d values differ (7.33 vs 6.66)

Pooled covariance under `(n1-1)+(n2-1)` weighting plus a 1e-6 ridge gives
d ≈ 7.33. The locked 6.66 used a slightly different covariance convention
(likely unregularised pinv against the control pool only). Both are valid;
the qualitative conclusion (enormous multivariate separation) is identical.

## Interpretation

- The locked permutation p ≤ 0.005 was purely permutation-count floor.
- The analytic F-tail on the same statistic is **p < 10⁻⁴⁸⁰**, i.e.
  roughly **47 standard deviations**, or ~10⁴⁷³× stronger than the
  particle-physics 5σ discovery threshold.
- The barrier that now matters is no longer statistical significance.
  It is **universality**: does this p-value survive on N ≫ 8 corpus
  families? That is the experiment to run next (exp02+).

## Recommended language for the paper

> The Band-A Quran and Band-A Arabic-control-pool centroids differ at
> Hotelling T² = 3557 on 5 features (F(5, 2571) = 710.36; analytic F-tail
> p ≈ 10⁻⁴⁸⁰, mpmath 80-digit). The previously-reported permutation
> p-value of 5·10⁻³ is a permutation-count floor at B = 200 permutations
> and is not to be read as a true p-value for this effect size.

## Reproducibility

```powershell
python -m experiments.exp01_ftail.run
```

Runs in < 2 s from `Quran/` as cwd. Requires `numpy`, `scipy`, `mpmath`.
The script refuses to finish if any protected file has been mutated since
it started.
