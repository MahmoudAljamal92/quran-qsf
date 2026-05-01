# expE15 — Anti-Variance Manifold

**Generated (UTC)**: 2026-04-23T20:12:43+00:00
**Seed**: 42  |  **N perm**: 10000
**Quran units (Band-A)**: 68  |  **Arabic control units (Band-A)**: 2509
**Feature order**: ['EL', 'VL_CV', 'CN', 'H_cond', 'T']

## Pre-registration

- **Null**: Quran anti-distance percentile < 95 relative to controls.
- **ANTI_VARIANCE_LAW**: percentile >= 95 AND label-shuffle p <= 0.01.
- **WEAK_ANTI_VARIANCE**: percentile >= 75 but < 95.
- **NULL_NO_ANTI_VARIANCE**: below that.

## Verdict — **ANTI_VARIANCE_LAW**

## Key numbers

- **Quran mean anti-distance**:   2.9096
- **Control mean anti-distance**: 1.2458
- **Quran percentile vs controls**: 98.53 %
- **Label-shuffle p (N=10000)**: 9.999e-05
- **Σ_ctrl eigenvalues (ascending)**: ['0.28634', '0.78258', '0.92632', '1.02768', '1.97707']

## Anti-basis (2 smallest eigenvectors of Σ_ctrl, rows = eigenvectors)

```
[[-0.4015  0.2558]
 [-0.0307 -0.8917]
 [ 0.004   0.2   ]
 [-0.5613  0.1907]
 [ 0.7231  0.2511]]
```

## Formal statement

Let `x ∈ R⁵` be the 5-D feature vector of a unit in order `(EL, VL_CV, CN, H_cond, T)`.
Define the standardised feature `z = (x − μ_ctrl) / σ_ctrl`, where `μ_ctrl` and `σ_ctrl` are
the mean and standard deviation vectors over the 6-corpus Band-A Arabic control pool.
Let `A ∈ R^{5×2}` be the two eigenvectors of `Σ_ctrl = Cov(z_ctrl)` with the smallest
eigenvalues `λ₁ ≤ λ₂`. The **anti-distance** of unit `x` is

```
d_anti(x) = || diag(1/√λ_anti) · Aᵀ · z ||_2
```

Empirically,
- μ_ctrl = [ 0.1108  0.2003  0.0277  0.8252 -2.4449]
- σ_ctrl = [0.0788 0.1672 0.04   0.3329 0.4667]
- λ_anti = [0.286343 0.782578]

## Outputs

- `expE15_report.json` — all numbers including hyperplane coefficients.
- `expE15_anti_manifold.png` — 2-D anti-projection scatter + distance histogram.