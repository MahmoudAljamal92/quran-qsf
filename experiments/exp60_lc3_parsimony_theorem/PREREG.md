# Pre-Registration: exp60_lc3_parsimony_theorem

**Hypothesis**: H16 — The LC3 Parsimony Theorem — (T, EL) as Asymptotic Sufficient Statistics

**Filed**: 2026-04-21 (before any computation)

---

## Claim

Under the observed 5-D covariance structure of the Arabic control pool,
the two features (T, EL) are **asymptotic sufficient statistics** for the
Quran-vs-control classification task — i.e., the remaining three features
(CN, VL_CV, H_cond) carry negligible additional information about the
class label once (T, EL) are known.

## Empirical basis

`exp36_TxEL_seed_metaCI` established AUC(T, EL) = 0.9971 ± 0.0006 across
25 independent seed·fold measurements vs AUC(5-D) = 0.998. The gap is
below within-fold SD.

## Tests

### T1 — Eigendecomposition overlap
Compute pooled Σ of the 2,509-unit Arabic control pool in 5-D.
Eigendecompose. Measure what fraction of the top-2 eigenvector variance
projects onto the (T, EL) subspace.

### T2 — Conditional Mutual Information
For each k ∈ {CN, VL_CV, H_cond}:
  I(class; feature_k | T, EL) via binned estimator with Miller–Madow debias.

### T3 — Fisher Information Ratio
Fit a 2-component Gaussian (Quran vs ctrl) in 5-D. Compute the Fisher
information matrix at the Bayes-optimal decision boundary. Measure the
ratio of Fisher information along the (CN, VL_CV, H_cond) directions vs
the (T, EL) directions.

### T4 — Bootstrap CI
10,000 bootstrap resamples of the conditional MI computation (T2) to get
publication-grade CIs.

## Pre-registered thresholds

- **THEOREM_SUPPORTED** ⟺
    (a) ALL 3 conditional MIs < 0.01 bits, AND
    (b) top-2 eigenvector overlap onto (T,EL) subspace ≥ 0.80, AND
    (c) Fisher info ratio (residual / total) < 0.05

- **PARTIAL** ⟺
    conditional MIs < 0.05 bits OR overlap ≥ 0.60

- **FAILS** ⟺
    any conditional MI > 0.10 bits OR overlap < 0.50

## Falsifier

Any single feature k ∈ {CN, VL_CV, H_cond} with I(class; k | T, EL) > 0.10 bits
would mean (T, EL) are NOT sufficient — the full 5-D carries real
independent information.

## Dependencies

- `results/checkpoints/phase_06_phi_m.pkl` (SHA-pinned)
- No external data needed

## Output

- `results/experiments/exp60_lc3_parsimony_theorem/exp60_lc3_parsimony_theorem.json`
- `results/experiments/exp60_lc3_parsimony_theorem/self_check_*.json`
