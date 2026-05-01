# expP7_phi_m_full_quran — pre-registration

**Frozen**: 2026-04-26
**Hypothesis**: H37 — The 5-D Hotelling T² and 5-D classifier headline ("v7.7 Φ_M T² = 3 557 on band-A 68") survives, possibly with attenuated magnitude, when the Quran sample is expanded from band-A (68 surahs) to ALL 114 surahs and the control pool is expanded from 2 509 band-A units to the full 4 719-unit Arabic-prose pool (no length gate).

## Rationale

`exp104_el_all_bands` (v7.9 cand) showed that EL alone on all 114 surahs gives AUC = 0.9813 (length-stratified: B 0.93, A 0.997, C 1.00). The natural follow-up is whether the **5-D ellipsoid** retains its multivariate magnitude when band-B short surahs (28 of them, n_verses ∈ [2, 14]) are included. Three outcomes are pre-registered:

1. **PASS_full_quran_5D**: full-114 5-D T² ≥ 2 500 AND full-114 5-D AUC ≥ 0.99 → the 5-D ellipsoid is a property of the whole Quran, not just band-A. The v7.9-cand abstract reframe (EL = headline, 5-D = envelope) holds with the multivariate envelope strengthened.
2. **PARTIAL_band_A_dominated**: full-114 T² ∈ [1 000, 2 500) OR AUC ∈ [0.97, 0.99) → the 5-D headline shrinks substantially when short surahs are included; report honestly.
3. **FAIL_5D_band_specific**: full-114 T² < 1 000 OR AUC < 0.97 → the 5-D headline is band-A-specific. EL becomes the *only* whole-Quran headline. The v7.7 multivariate framing is retracted as length-gated.

## Method (frozen)

- Inputs: `phase_06_phi_m.pkl` `state['CORPORA']` (SHA-pinned via `_manifest.json`).
- Quran sample: ALL 114 surahs with `n_verses ≥ 2`. No length gate.
- Control pool: union of `poetry_jahili`, `poetry_islami`, `poetry_abbasi`, `ksucca`, `arabic_bible`, `hindawi`, all units with `n_verses ≥ 2`.
- Feature vector: `features_5d` from `src/features.py` (`EL`, `VL_CV`, `CN`, `H_cond_roots`, `T = H_cond_roots − H_EL`).
- Multivariate distance: Hotelling T² on z-scored features with `ddof=1`. Inverse covariance from the **pooled control sample** (consistent with v7.7 `phi_m`).
- Classifier: linear SVM on the same 5-D features, `class_weight='balanced'`, `C=1.0`, `SEED=42`.
- Bootstrap: 500 resamples for AUC CI95.
- Per-band stratification: B = 2–14 verses, A = 15–100 verses, C = >100 verses (same band definitions as `exp104`).
- Generalisation: train 5-D classifier on band-A only; evaluate on B and C without re-fitting.

## Locked sanity check

Band-A subset (68 vs 2 509) must reproduce the locked Hotelling T² = 3 557.34 ± 5.0 (`results_lock.json::Phi_M_hotelling_T2`).

## Frozen constants

```
SEED = 42
SVM_C = 1.0
N_BOOT = 500
BAND_B = (2, 14)
BAND_A = (15, 100)
BAND_C = (101, 10**9)
MIN_VERSES = 2
ARABIC_CTRL = ["poetry_jahili","poetry_islami","poetry_abbasi","ksucca","arabic_bible","hindawi"]
LOCKED_T2_BANDA = 3557.34
LOCKED_T2_TOL = 5.0
```

## Output

`results/experiments/expP7_phi_m_full_quran/expP7_phi_m_full_quran.json` with:
- `n_quran_units`, `n_ctrl_units`
- `overall`: T², T²_F_tail_log10_p, AUC, w (5 coefs), b
- `per_band`: same per band {B, A, C}
- `generalisation_bandA_trained`: AUC on B and C from band-A-only fit
- `band_a_sanity_lock`: observed band-A T², expected 3 557.34, within_tol
- `verdict` ∈ {PASS_full_quran_5D, PARTIAL_band_A_dominated, FAIL_5D_band_specific}
