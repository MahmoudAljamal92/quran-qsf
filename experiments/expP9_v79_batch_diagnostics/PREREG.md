# expP9_v79_batch_diagnostics — pre-registration

**Frozen**: 2026-04-26
**Hypothesis bundle**: 6 sub-tests packaged into a single deterministic script for runtime efficiency. Each writes its own result JSON.

## Sub-tests

### N1 — Cross-tradition EL-alone test
Question: does EL alone separate the Quran from non-Arabic religious-text canons (Hebrew Tanakh, Greek NT, Iliad, Pali Dīgha, Pali Majjhima, Rigveda, Avestan Yasna) at AUC ≥ 0.95?

Predicted verdicts:
- `PASS_quran_specific_cross_script`: AUC ≥ 0.95 vs each of the 7 non-Arabic corpora → EL is Quran-distinctive across scripts.
- `PASS_arabic_only`: AUC ≥ 0.95 only when controls are Arabic; cross-script AUC < 0.95 → EL captures Arabic-rhymed-prose, not Quran.
- `FAIL_class_property`: AUC < 0.95 vs at least one religious-text canon → EL is a property of rhymed-canon prose in general.

### N4 — Per-surah EL boundary-distance ranking
For each of the 114 Quran surahs, compute `Δ_EL = EL − 0.314` (distance from the locked exp104 band-A boundary). Rank ascending. The 5 lowest are the project's "most ambiguous" surahs and need explicit reporting in the tool's confidence output.

### N6 — Bag-of-verses null (per-surah Σp̂² ≈ 0.5 vs corpus-pool iid)
For each Quran surah of size n_v, draw n_v verse-final letters iid from the corpus-pool PMF (`Σp̂²` = 0.295) and compute simulated EL. Compare observed EL to the iid-pool null distribution. This formally tests the §4.40.3 hypothesis "the per-surah `Σp̂² ≈ 0.5` is achieved by per-surah dominant-final lock-on, not by sampling from the corpus PMF."

Predicted verdict:
- `PASS_per_surah_lock_on`: observed EL >> iid-pool null in ≥ 95 % of surahs → per-surah dominant-final lock-on is confirmed.
- `FAIL_consistent_with_pool_iid`: observed EL within iid-pool 95 % CI → no per-surah structure beyond corpus PMF.

### N8 — EL stress curve under terminal-letter corruption
Corrupt fraction `f ∈ {0.01, 0.05, 0.10, 0.20, 0.50}` of Quranic verse-finals with random Arabic letters drawn iid from the *uniform* 28-letter alphabet (worst-case noise model). Measure 5-D AUC degradation. Output the maximum `f*` such that AUC ≥ 0.95.

### N9 — Brown joint-anomaly synthesis on full-114 witnesses
Combine four whole-Quran one-sided p-values via Brown's method with the empirical 4×4 correlation matrix (estimated on the 6 Arabic controls under bootstrap):
- p_EL: from `exp104` overall AUC = 0.9813 (114 vs 4 719) → AUC-derived z
- p_R3: from `expP4_cross_tradition_R3` Quran z = −8.92 → one-sided p
- p_J1: from `expE17b_mushaf_j1_1m_perms` mushaf-J1 smoothness perm-p
- p_Hurst: from `expP4_quran_hurst_forensics` H = 0.914 perm-p

Brown's method handles correlated channels; Stouffer's would over-state significance.

### NEW2 — Per-corpus dominant-final-letter forensics
From `expC1plus` PMF data, extract for each of 14 corpora: alphabet size, dominant final letter (argmax), max-mass `p_max`, `p_max²` (lower bound on per-pair-collision EL), `Σp̂²` (Rényi-2 collision probability). The Quran's `ن`-dominance hypothesis is confirmed if `(argmax_quran, p_max_quran)` is uniquely high relative to all 6 Arabic controls.

### expC1plus_v2 — Per-surah Σp̂² ≈ 0.5 bootstrap test
For the 68 band-A surahs, compute `Σp̂²` per surah (already in expC1plus.json mean=0.541). Run a 10 000-bootstrap test of `H_0: median(Σp̂²) = 0.5` vs `H_1: median(Σp̂²) ≠ 0.5`. Verdict `PASS_at_half` if 95 % CI for median includes 0.5.

## Frozen constants

```
SEED = 42
MIN_VERSES = 2
N_BOOT_AUC = 500
N_BOOT_RENYI2_PER_SURAH = 10000
N_SIM_BAG_OF_VERSES = 5000
CORRUPTION_LEVELS = [0.01, 0.05, 0.10, 0.20, 0.50]
ARABIC_ALPHABET = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"  # 28 letters
EL_BOUNDARY_LOCKED = 0.314  # exp104 band-A SVM
```

## Outputs

`results/experiments/expP9_v79_batch_diagnostics/`:
- `N1_cross_tradition_el.json`
- `N4_boundary_distance.json`
- `N6_bag_of_verses_null.json`
- `N8_stress_curve.json`
- `N9_brown_synthesis.json`
- `NEW2_dominant_final_forensics.json`
- `expC1plus_v2_per_surah.json`
- `summary.json` (verdicts roll-up)
