# exp53_ar1_6d_gate — Pre-Registration

**Date**: 2026-04-21 (scaffolded this session; executed in Step 4).
**Audit trail**: `docs/SCAN_2026-04-21T07-30Z/03_HYPOTHESIS_REGISTER.md` H2.

## Hypothesis (H2)

The per-surah **AR(1) φ₁ coefficient** on the verse-length series adds independent multivariate separation on top of the 5-D Φ_M baseline — specifically, the 6-D Hotelling T² clears the 6/5 dimension-penalty gate (T²(6D) ≥ T²(5D) × 6/5).

**Motivation**: `exp44_F6_spectrum` already shows that lag-1 Pearson autocorrelation on verse lengths is strongly Quran-characteristic (Cohen's d = +0.79, Mann-Whitney p = 2 × 10⁻¹⁰). `exp49_6d_hotelling` tested `n_communities` as the 6th candidate channel and returned SIGNIFICANT_BUT_REDUNDANT (gate-ratio = 1.075 < 1.2 threshold). AR(1) φ₁ is a completely different signal family (temporal-rhythmic vs topological) and is a stronger candidate for genuine non-redundancy with the 5-D (EL, VL_CV, CN, H_cond, T).

## Construction

Clone exp49's 6-D Hotelling machinery verbatim and swap the 6th feature:

- 5-D baseline features: `(EL, VL_CV, CN, H_cond, T)` from `phase_06_phi_m`.
- 6th feature (new): `phi1_ar1_vlen`, computed as the OLS-fit AR(1) coefficient on the mean-centred per-verse word-count sequence of each Band-A unit (same construction as `exp44_F6_spectrum._ar_fit(lens, p=1)[0]`).
- Band-A filter, iteration order, ridge λ, gate threshold — all identical to exp49.

## Primary statistic

Two-sample Hotelling T² on the (68 Quran × 2509 Arabic-control) Band-A matrix, pooled covariance with ridge 1e-6·I. Report also:

- 5-D baseline T² (locked-scalar sanity check; must match `results_lock.json` within 1e-9).
- Per-dimension gain ratio: `(T²(6D)/6) / (T²(5D)/5)`.
- Permutation p-value with 10 000 label shuffles on (6D T² ≥ observed) — the significance test under the null.
- Cohen's d of `phi1_ar1_vlen` between Quran and Arabic-control pool (diagnostic).

## Pre-registered thresholds (frozen before computation)

| Condition | Verdict |
|-----------|---------|
| T²(6D) ≥ T²(5D) × 6/5 AND permutation p ≤ 0.01 AND per-dim gain ≥ 1.0 | **PROMOTE_6TH_CHANNEL** |
| T²(6D) ≥ T²(5D) × 6/5 AND permutation p > 0.01 | **GATE_PASS_UNCERTAIN** |
| T²(6D) ≥ T²(5D) (weaker) AND permutation p ≤ 0.05 but fails 6/5 gate | **SIGNIFICANT_BUT_REDUNDANT** |
| otherwise | **REJECT_6TH_CHANNEL** |

## Falsifier

T²(6D) ≤ T²(5D) (inclusion of AR(1) does not increase the statistic) OR per-dim gain < 0.95 (adding AR(1) dilutes the 5-D signal).

## Expected result (from exp44 effect sizes, NOT binding)

Given exp44 lag-1 Cohen's d = +0.79 (pooled), a rough back-of-envelope estimate for the marginal T² contribution is 20-60 units. The 5-D baseline is T² = 3557.34, so a 6-D estimate of ~3580-3620 would fall between **SIGNIFICANT_BUT_REDUNDANT** and **GATE_PASS_UNCERTAIN**. A clean PROMOTE verdict (T² ≥ 4269) is unlikely but not ruled out if AR(1) captures structure genuinely orthogonal to VL_CV.

## Inputs

- `results/checkpoints/phase_06_phi_m.pkl` — SHA-pinned, verified via `_lib.load_phase`.
- `experiments/exp44_F6_spectrum/run.py::_ar_fit` — function imported directly (no drift concern since it's imported at run-time from a protected experiment directory).

## Outputs

- `results/experiments/exp53_ar1_6d_gate/exp53_ar1_6d_gate.json`
- `results/experiments/exp53_ar1_6d_gate/phi1_distribution.png`

## If PROMOTE

Requires R9 follow-up: append `hotelling_T2_6d_ar1` and `hotelling_T2_6d_ar1_perm_p` to `results/integrity/results_lock.json`. Gated behind explicit user approval (integrity-zone write).

## Prereg hash

SHA-256 of this file is computed at run-time and stored in the output JSON under `prereg_hash`.
