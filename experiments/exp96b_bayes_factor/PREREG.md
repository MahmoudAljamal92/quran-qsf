# PREREG — exp96b_bayes_factor (H50)

**Hypothesis ID**: H50
**Filed**: 2026-04-27 afternoon (v7.9-cand patch H pre-V2)
**Pre-registered before any leave-one-out / bootstrap computation.**

**Scope directive**: Whole 114-surah Quran. No band gates.

---

## 1. Background

`exp96a_phi_master` (H49) computes the project's master log-likelihood
ratio `Φ_master(quran) ≈ 1,862 nats` using locked, hash-verified,
whole-corpus inputs. The dominant term `T1 = (1/2)·T²` is
**already out-of-sample for the Quran** because the 5-D Φ_M Σ is
estimated on the 6-corpus Arabic control pool (n = 4,719) which
**does not include any Quran data**.

The 2026-04-27 afternoon feedback raised a sharper concern: the Σ
itself depends on the *composition* of the control pool. If one
control corpus dominates Σ, the headline T² could be inflated. This
PREREG addresses that by computing `T²` and `Φ_master` under
**leave-one-control-corpus-out** (LOCO) cross-validation, plus a
non-parametric bootstrap CI.

---

## 2. Hypotheses

**H50** (one-sided, hash-locked).

The headline `Φ_master(quran)` from `exp96a` is robust to:

- **(a) LOCO-min**: leaving out any single control corpus and
  recomputing T² and Φ_master keeps `Φ_master_LOCO_min ≥ 1,500 nats`
  (≥ 80 % of the headline). Falsification: any LOCO split drops
  Φ_master below 1,500 nats.

- **(b) Bootstrap-95-low**: a non-parametric bootstrap of the
  control pool (resample with replacement, n_boot = 500 replicates,
  recompute Σ, recompute T² each replicate) keeps the bootstrap
  5th-percentile `Φ_master_boot_p05 ≥ 1,500 nats`. Falsification:
  bootstrap p05 below 1,500 nats.

- **(c) Bayes-factor floor**: with `Φ_master_LOCO_min ≥ 1,500 nats`,
  the Bayes factor floor BF_floor = exp(1,500) ≈ 10⁶⁵¹ in favour of
  Quran-class. **The PREREG computes BF; it does NOT supply a prior
  and does NOT compute a posterior.**

If (a) AND (b) hold, the headline `Φ_master ≈ 1,862` is locked
against control-pool-composition drift, and the **Φ_master headline
is honestly out-of-sample / cross-validated** for the Gate 1 term.

---

## 3. Frozen constants

```python
# Whole-Quran scope (no bands)
MIN_VERSES = 2                       # all 114 surahs in
ARABIC_CTRL = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
               "ksucca", "arabic_bible", "hindawi"]
N_BOOT = 500                         # bootstrap replicates
RNG_SEED = 96100                     # deterministic seed

# Locked headline (must match exp96a)
PHI_MASTER_HEADLINE = 1862.31        # nats; from exp96a receipt
PHI_MASTER_HEADLINE_TOL = 5.0

# Robustness thresholds
LOCO_MIN_FLOOR = 1500.0              # nats; floor for ANY LOCO split
BOOT_P05_FLOOR = 1500.0              # nats; floor for bootstrap 5th pct

# Source receipt hashes (chain-of-custody verified at run time)
EXP96A_HASH_EXPECTED = "ab816b3e81bd1bfc7be0bb349ee4e3e49b7db56f288ac7c792ecc861d847db3e"
PHASE_06_PHI_M_PKL_REQUIRED = True   # integrity-checked via _lib.load_phase
```

---

## 4. Audit hooks (block PASS if any fire)

1. **A1** Source `exp96a_phi_master.json` exists, has `verdict = "PASS_phi_master_locked"`, and reports `phi_master_quran_nats` within ±5 of 1862.31.
2. **A2** `phase_06_phi_m.pkl` integrity check passes (handled by `_lib.load_phase`).
3. **A3** All 114 Quran surahs and ≥ 4,500 control units load with finite 5-D features.
4. **A4** Each LOCO computation produces a finite T².
5. **A5** Bootstrap completes ≥ 95 % of replicates without numerical failure.

Any hook firing → verdict `FAIL_audit_<hook_id>`.

---

## 5. Verdict ladder (strict order)

1. `FAIL_audit_<hook_id>` — any audit hook fired.
2. `FAIL_loco_min_below_floor` — `Φ_master_LOCO_min < 1,500 nats`.
3. `FAIL_boot_p05_below_floor` — `Φ_master_boot_p05 < 1,500 nats`.
4. `PARTIAL_one_robustness_floor_held` — exactly one of (LOCO-min, boot-p05) ≥ floor.
5. `PASS_robust_oos_locked` — both LOCO-min ≥ 1,500 AND boot-p05 ≥ 1,500.

`PASS_robust_oos_locked` supports the joint
`exp96a` + `exp96b` claim: **Φ_master(quran) is locked at
~1,862 nats with a robust out-of-sample / bootstrap floor of ≥
1,500 nats (Bayes-factor floor of ≥ 10⁶⁵¹) against control-pool
composition drift.**

---

## 6. Out-of-sample claim

This PREREG explicitly addresses the circularity objection by
computing the **Gate 1 contribution to Φ_master under leave-one-
control-corpus-out cross-validation**. The Quran is held out from Σ
estimation in *every* split (it is class 1, not part of the null Σ),
and additionally one control corpus is held out per split. The
LOCO-min is therefore a doubly-out-of-sample lower bound on the
Gate 1 LLR contribution.

Terms T2–T6 of Φ_master do not depend on Σ and are taken directly
from `exp96a` — they are not re-cross-validated here because they
each correspond to a different statistical structure (counts, AUC,
ratios, theorem-grade detector, riwayat product) that is not
parametrically tuned on the Quran.

---

## 7. What this PREREG does NOT claim

- Does **not** supply a prior probability of any kind.
- Does **not** compute a posterior probability.
- Does **not** re-derive T2–T6 (which are not Σ-dependent).
- Does **not** modify any locked positive finding.

---

## 8. Outputs

- `results/experiments/exp96b_bayes_factor/exp96b_bayes_factor.json` — receipt with 6 LOCO splits, bootstrap distribution, audit hooks, verdict.
- This PREREG hash logged in receipt as `prereg_hash_actual`.
