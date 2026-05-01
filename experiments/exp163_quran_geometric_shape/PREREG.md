# PREREG — exp163 Quran Geometric Shape

**Hypothesis** (frozen 2026-05-01, before observing any data):

The 114-surah Quran point cloud in 5-D `Φ_M` space (or its 68-surah Band-A
filtered version) has at least ONE shape descriptor (out of 7 frozen
descriptors below) on which the Quran is **rank-1 across all 8 control
corpora at Bonferroni-Holm corrected p < 0.01** under a bootstrap-from-
combined-pool null. If yes → **PASS_QURAN_GEOMETRY_DISTINCT**. Multiple
descriptors at significance is informative but not required.

## Frozen constants

```
SEED            = 42
N_BOOTSTRAP     = 10000
N_SUBSAMPLE     = 200    # per-control subsample replicates
ALPHA_BHL       = 0.01   # Bonferroni-Holm family-wise alpha
FEAT_COLS       = ['EL', 'VL_CV', 'CN', 'H_cond', 'T']
N_QURAN_TARGET  = 68     # Band-A filtered surahs (matches X_QURAN)
```

## Framing A — Cloud-shape descriptors (frozen list)

For an n × 5 point cloud X, all descriptors computed on centered X
(X - mean(X, axis=0)):

1. **`sphericity_log10`** = log10(λ_max / λ_min) of cov(X). Lower =
   rounder. Reported as log10 for permutation-null stability.
2. **`isotropy`** = λ_min / λ_max. Higher = rounder. ∈ [0, 1].
3. **`intrinsic_dim_95pct`** = number of PCs needed for ≥ 95 % cumulative
   variance. Integer, lower = lives on lower-D manifold.
4. **`anisotropy_westin`** = (λ_max − λ_min) / (λ_max + λ_min). ∈ [0, 1].
5. **`linearity_westin`** = (λ_max − λ_2) / λ_max. ∈ [0, 1].
6. **`planarity_westin`** = (λ_2 − λ_min) / λ_max. ∈ [0, 1].
7. **`symmetry_score`** = mean over points x ∈ X_centered of
   distance(x, nearest neighbour in -X_centered) / median pairwise
   distance. Lower = more centrally symmetric.

(Two additional metrics tracked for inspection but **NOT** in the
seven-test multiple-comparison family):

- regularity_NN_CV: CV of nearest-neighbour distances within X.
- volume_log10: log determinant of cov(X) / 2 (proxy for hypervolume).

## Framing B — Trajectory descriptors under canonical orderings

For the 114-surah ordering by:

1. **Mushaf order** (canonical 1, 2, …, 114).
2. **Nuzul order** (revelation chronology from `data/registries/`).
3. **Length order** (n_verses ascending).

Compute the 5-D polyline trajectory descriptors:

- arc_length, mean_curvature, curvature_variance, closure_ratio,
  smoothness_curvature_variance.

Permutation null: shuffle the surah ordering 10,000 times, recompute.
The actual ordering must beat 99 % of shuffles on at least one
descriptor for that ordering to be flagged "geometrically smooth".

Equivalent computation for Iliad books (n=24) and Bible chapters
(n=1183, capped at first 100) where ordering is also canonical.

## Framing C — Findings polytope

Build a 9-corpus × K-feature matrix where each row is a corpus's
mean (z-scored vs combined pool) on each of K = 6 axes:
EL, VL_CV, CN, H_cond, T, F-Universal-gap. (F-Universal-gap is the
H_letter + log2(p_max) shifted to ≈ 1 bit; computable per corpus
from F_letter histograms in the registry.)

Project to 2-D MDS and 3-D MDS, save PNGs. Compute:

- pairwise corpus-corpus distance matrix in z-space
- Quran nearest neighbour and farthest neighbour
- whether the Quran is on a corner of the convex hull of corpora

This is mostly a visualisation; no formal verdict, but report the
hull / NN structure.

## Audit hooks

- A1: `len(X_QURAN) == 68` (Band-A invariant).
- A2: each control corpus subsample is exactly n=68.
- A3: bootstrap pool size = 68 + sum(matched controls), recomputed
  per permutation.
- A4: per-descriptor Quran rank against {bootstrap, controls} dual.

## Output

`results/experiments/exp163_quran_geometric_shape/exp163_quran_geometric_shape.json`
plus three PNGs:

- `frame_A_radar.png` — radar plot of 7 descriptors × 9 corpora.
- `frame_B_trajectories.png` — Mushaf/Nuzul/Length trajectories in 2-D PCA.
- `frame_C_polytope_2d.png` — 2-D MDS of corpora in z-space.
- `frame_C_polytope_3d.png` — 3-D MDS rotated PNG (matplotlib 3D).

## Multiple comparisons

Framing A: 7 descriptors → Bonferroni-Holm at α = 0.01.
Framing B: 5 descriptors × 3 orderings = 15 tests → Bonferroni-Holm at
α = 0.01.

PASS criteria (any of):

- Framing A: at least 1 BHL-significant Quran rank-1 descriptor.
- Framing B: Mushaf or Nuzul produces a BHL-significant smoother
  trajectory than 99 % of random shuffles on at least 1 descriptor.

Anything weaker than this is reported as PARTIAL or FAIL.
