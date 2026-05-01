# PREREG — exp165 Quran Intrinsic Geometry

**Hypothesis** (frozen 2026-05-01, before any computation):

The 114-surah Quran point cloud, examined **intrinsically** (against
random nulls of the same n, NOT against control corpora), exhibits at
least one rare geometric or topological property at p ≤ 0.01 (Bonferroni-
Holm-corrected over the 13 frozen tests at family-wise α = 0.01).

This experiment deliberately has **no control corpora**. The user reframed
the geometric question as "does the Quran *itself* trace a coherent shape"
rather than "is the Quran's shape distinct from poetry / Bible / etc.".
All nulls are intrinsic: random uniform-cube point clouds at matched n,
random permutations of the same 114 surahs, random shuffles of the same
verse-count multiset.

## Frozen constants

```
SEED                  = 44
N_NULL_CLOUDS         = 5000     # random uniform-cube clouds for cloud-topology nulls
N_PERMUTATIONS        = 10000    # random permutations for trajectory & numerology nulls
ALPHA_BHL             = 0.01     # family-wise Bonferroni-Holm
N_QURAN_TARGET        = 114      # full Mushaf, NOT Band-A filtered (intrinsic test, no length filter needed)
FEAT_COLS             = ['EL', 'VL_CV', 'CN', 'H_cond', 'T']
KNN_K_VALUES          = [3, 5, 7]
PCA_2D_FOR_TRAJECTORY = True     # render trajectory in PC1-PC2 of whitened cloud
```

## Test family (13 frozen tests, BHL @ family-wise α = 0.01)

### Sub-A — k-NN graph topology (4 tests)

For each k ∈ {3, 5, 7}, build the symmetric k-NN graph on 114 surahs in
**whitened 5-D Φ_M** (Mahalanobis-equivalent isotropic Euclidean):

- **A.1** `is_planar_at_k5`: whether the 5-NN graph is planar (via Kuratowski / `networkx.check_planarity`).
- **A.2** `clustering_coefficient_at_k5`: average clustering coefficient of the 5-NN graph.
- **A.3** `modularity_at_k5`: Louvain modularity of the 5-NN graph.
- **A.4** `spectral_gap_at_k5`: algebraic connectivity (λ₂ of normalised Laplacian) of the 5-NN graph.

Null: 5,000 random uniform-cube point clouds in [0, 1]⁵ at n = 114, same k. Two-sided p
for continuous descriptors; one-sided fraction for the binary planarity test.

### Sub-B — Mushaf trajectory intrinsic descriptors (3 tests)

114-surah polyline in whitened 5-D Φ_M space, ordered by Mushaf:

- **B.1** `closure_ratio`: end-to-end distance / arc length. Null: 10,000 random
  permutations of the same 114 surahs.
- **B.2** `self_intersection_count_2d`: number of self-intersections in the 2-D
  PCA projection of the trajectory. Null: 10,000 random permutations.
- **B.3** `kl_divergence_to_uniform`: KL divergence of the empirical turning-
  angle distribution (binned to 10 bins on [0, π]) from uniform. Higher = more
  structured. Null: 10,000 random permutations.

### Sub-C — Manifold intrinsic dimension (2 tests)

- **C.1** `twonn_intrinsic_dim`: TwoNN estimator (Facco, Rodriguez, d'Errico,
  Laio 2017) on the 114 surahs in whitened 5-D Φ_M. Null: 5,000 random 5-D
  isotropic Gaussian clouds at n = 114 (expected dim ≈ 5).
- **C.2** `correlation_dim`: correlation-integral exponent (Grassberger-Procaccia)
  fitted on log-log correlation integral over the middle 50 % of the radius
  range. Null: 5,000 random 5-D Gaussian clouds.

### Sub-D — Mushaf-ordered verse-count spectrum (4 tests)

Mushaf-order verse-count vector `n_v = (n_v[0], n_v[1], …, n_v[113])`:

- **D.1** `peak_freq_period`: dominant period (1 / argmax-frequency excluding DC) of
  the FFT power spectrum. Null: 10,000 random permutations of the same
  verse-count multiset.
- **D.2** `peak_power_ratio`: ratio of peak-FFT-power to mean-non-DC FFT power.
  Higher = sharper resonance. Null: 10,000 random permutations.
- **D.3** `power_at_period_19`: FFT power at exactly period-19 (the most-cited
  Quran-numerology period). Null: 10,000 random permutations.
- **D.4** `power_at_period_7`: FFT power at exactly period-7. Null: 10,000 random
  permutations.

## Audit hooks

- A1: cloud is exactly 114 surahs (full Mushaf, no Band-A filter for this experiment).
- A2: whitening transforms pool covariance to identity within `1e-6`.
- A3: per-surah verse counts loaded directly from `state['CORPORA']['quran']`,
  no synthetic substitution.
- A4: random nulls use `numpy.random.default_rng(SEED)` with explicit seed
  for reproducibility; per-test sub-streams via `rng.spawn(...)`.

## Output

```
results/experiments/exp165_quran_intrinsic_geometry/
   exp165_quran_intrinsic_geometry.json
   sub_A_knn_graph_k5.png       # 2D PCA projection with 5-NN edges drawn
   sub_B_mushaf_trajectory.png  # trajectory + closure + self-intersections highlighted
   sub_C_intrinsic_dim.png      # TwoNN scaling plot
   sub_D_verse_spectrum.png     # FFT power spectrum with period-7, period-19 marked
```

## Verdict criteria

- **`PASS_QURAN_INTRINSIC_GEOMETRY_DISTINCT`** — at least 2 BHL-significant
  tests across at least 2 sub-families (A, B, C, D).
- **`PARTIAL_INTRINSIC_GEOMETRY_PRESENT`** — exactly 1 BHL-significant test,
  OR ≥ 2 nominal-p<0.05 tests but none surviving BHL.
- **`FAIL_NO_INTRINSIC_GEOMETRIC_STRUCTURE`** — zero nominally-significant
  tests at p < 0.05.

This experiment is **purely exploratory** — no F-row promotion is on the table
regardless of outcome. Any positive result would feed into a separate
sensitivity-gate experiment before any promotion is even discussed.
