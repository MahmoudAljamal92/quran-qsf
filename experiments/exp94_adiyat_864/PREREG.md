# exp94_adiyat_864 — Pre-registration

**Frozen**: 2026-04-22 (before any fit or evaluation).
**Version**: 1.0
**Hypothesis ID**: H30b — Unified Stack Law on canonical Adiyat-864

## 1. Claim under test

On the **canonical Adiyat 864-variant enumeration** (32 consonant
positions in Surah 100 verse 1 × 27 alternative consonants; identical
to `exp23_adiyat_MC` and `exp43_adiyat_864_compound`), the unified
stack formula from `exp93_unified_stack` (Stage 2) achieves
`recall ≥ 99.0 %` at the exp41 control-p95 NCD threshold.

The pre-registered PAPER.md §4.35-adjacent headline
("99.1 % of 864 single-letter variants fire gzip NCD at 5 % FPR")
is a **single-layer** `R12`-only claim. This experiment tests whether
the **single closed-form unified formula** replicates or exceeds
that figure.

## 2. Closed-form formulas (pre-registered, mirror of exp93)

Given canonical verses `C` and a variant `V` that differs in exactly
one consonant at position `p`:

```
dL(C, V)      = L_TEL(V) - L_TEL(C)                   # LC3-70-U delta
                where L_TEL = 0.5329*T + 4.1790*EL - 1.5221
NCD_edit(C,V) = gzip NCD(letters_28(C), letters_28(V)) # R12 doc-scale
dPhi(C, V)    = || features_5d(V) - features_5d(C) || # 5-D delta
```

### Unified formula A — Logistic stack (frozen coefficients from exp93 Stage 2)
```
z_dL     = (|dL|     - mu_ctrl_dL)     / sd_ctrl_dL
z_NCD    = (NCD_edit - mu_ctrl_NCD)    / sd_ctrl_NCD
z_dPhi   = (|dPhi|   - mu_ctrl_dPhi)   / sd_ctrl_dPhi
logit(P) = b0 + w_dL*z_dL + w_NCD*z_NCD + w_dPhi*z_dPhi
```
`b0, w_dL, w_NCD, w_dPhi` are the **fold-averaged coefficients** from
`exp93_unified_stack.json["stage2_edit_detection"]["logistic_stack"]
["fold_coefficients"]`. As observed in v1.0: `w_dL = w_dPhi = 0`
in every fold, so the stack structurally collapses to `σ(w_NCD*z_NCD + b0)`.

### Unified formula B — Fisher χ²₆ combiner (parameter-free)
```
p_dL   = ECDF_null(|dL|)         # upper-tail empirical p vs ctrl-edit null
p_NCD  = ECDF_null(NCD_edit)
p_dPhi = ECDF_null(|dPhi|)
X^2(V) = -2 * (ln p_dL + ln p_NCD + ln p_dPhi)  ~ chi^2_6 under H0_indep
P_Fisher(V) = 1 - chi2.cdf(X^2(V), df=6)
```

### Unified formula C — Naive scalar sum (null baseline)
```
S_naive(V) = z_dL + z_NCD + z_dPhi    # reviewer's "apples and airplanes"
```
Included to show that even the naive formula works, as long as the
layers are first z-scored against a common null. `S_naive` has no
closed-form null distribution and must be calibrated empirically.

## 3. Evaluation protocol (frozen)

**Step 1 — null calibration**: regenerate exp41's 4 000 control
perturbations (200 ctrl units × 20 internal single-letter swaps,
byte-exact match to `exp41_gzip_formalised.run._apply_perturbation`,
`SEED = 42`). For each ctrl-edit compute `(dL, NCD_edit, dPhi)`.

**Step 2 — Adiyat enumeration**: iterate all 864 canonical variants
of Surah 100 verse 1 via `exp43_adiyat_864_compound`'s enumeration
(32 consonant positions × 27 alternatives). For each Adiyat variant
compute `(dL, NCD_edit, dPhi)`.

**Step 3 — per-formula thresholds**: set the detection threshold τ_F
for each unified formula F at the **95th percentile of the 4 000
control-edit scores** (5 % FPR, matching exp41 calibration).

**Step 4 — recall**: for each formula F, report
`recall_F = (# Adiyat variants with F ≥ τ_F) / 864`.

## 4. Pre-registered verdicts (evaluated in order)

| Code | Condition |
|---|---|
| `FAIL_sanity_R12_replication` | recall(R12-only) < 0.98 on 864 (must replicate exp43's 99.1 %) |
| `FAIL_n_variants` | enumerated variant count ≠ 864 (sanity on Surah 100 structure) |
| `PASS_unified_99` | recall(logistic) ≥ 0.99 **OR** recall(Fisher) ≥ 0.99 |
| `PARTIAL_below_99_above_R12` | best unified recall ≥ recall(R12-only) but < 0.99 |
| `FAIL_unified_below_R12` | best unified recall < recall(R12-only) − 0.005 |

## 5. Honesty clauses

- **HC1 — No predictive content beyond R12**: if `w_dL = w_dPhi = 0`
  in the exp93 Stage-2 coefficients (as observed in exp93 v1.0), the
  logistic stack is mathematically equivalent to R12-only; a PASS
  here is not a strict improvement over the single-layer claim.
  This is an **expected and honest** finding on internal single-letter
  edits given exp29's byte-blindness of `features_5d`.
- **HC2 — Canonical-only scope**: this test covers Surah 100 verse 1
  single-letter edits only. Two-letter edits (variant "C" of the
  hand-picked Adiyat triad), cross-verse edits, and out-of-Adiyat
  surah variants are explicitly out of scope.
- **HC3 — Reviewer-baseline `S_naive`**: reported as a *null-baseline*
  number. If `S_naive` achieves comparable recall, this demonstrates
  that even the reviewer's "impossible" algebraic sum works once
  the three layers are brought to a common scale.

## 6. Locks not touched

No modification to `results_lock.json`, `code_lock.json`,
`corpus_lock.json`, `headline_baselines.json`, `_manifest.json`, or
any `.ipynb`. All new scalars are tagged `(v7.8 cand.)`.

## 7. Provenance

- Reads (integrity-checked): `results/checkpoints/phase_06_phi_m.pkl`
- Reads (by-path): `results/experiments/exp41_gzip_formalised/exp41_gzip_formalised.json`
- Reads (by-path): `results/experiments/exp93_unified_stack/exp93_unified_stack.json`
- Enumeration: byte-equal to `experiments/exp43_adiyat_864_compound/run.py` §main
- Perturbation: byte-equal to `experiments/exp41_gzip_formalised/run.py::_apply_perturbation`
- Writes only: `results/experiments/exp94_adiyat_864/exp94_adiyat_864.json`

## 8. Frozen constants

```python
SEED = 42
N_PERT_PER_UNIT = 20
CTRL_N_UNITS = 200
GZIP_LEVEL = 9
FPR_TARGET = 0.05
W_T, W_EL, B_TEL = 0.5329, 4.1790, -1.5221
BAND_A_LO, BAND_A_HI = 15, 100
ADIYAT_LABEL = "Q:100"
EXPECTED_N_VARIANTS = 864    # = 32 consonant positions x 27 alternatives
RECALL_GATE = 0.99
SANITY_R12_MIN_RECALL = 0.98   # must replicate exp43's 99.1%
```

---

*Pre-registered 2026-04-22. If any constant or formula is changed
after this file is committed, the experiment is renamed `exp94b_*`
and this file marked SUPERSEDED.*
