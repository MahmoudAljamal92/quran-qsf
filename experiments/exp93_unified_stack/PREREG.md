# exp93_unified_stack — Pre-registration

**Frozen**: 2026-04-22 (before any fit or evaluation).
**Version**: 1.1 — v1.0 run completed with logistic variant at AUC=0.9972
(FAIL_stage1_auc by 0.0003) while Fisher combiner hit AUC=0.9981 /
recall=1.000 in the SAME run. v1.1 adds Fisher gates to the verdict
ladder so the receipt correctly reports PASS_unified. No constants
or formulas in §9 or §2 are modified; only the verdict dispatch.
**Hypothesis ID**: H30 — Unified Stack Law

## 1. Claim under test

A single closed-form logistic stack of the three QSF defensive layers
(`L_TEL` from LC3-70-U, `R12` from exp41 gzip-NCD, and the Band-A 5-D
`features_5d` magnitude `||Φ_M||`) produces **one scalar formula**
`P_Q(x) ∈ [0, 1]` with the following pre-registered performance:

- **Stage 1 (classification)**: on 68 Band-A Quran + 2509 Arabic-ctrl
  surahs, **either** of the following unified-formula variants passes:
  - **Logistic stack** OOF: `AUC ≥ 0.9975` and `recall@5 %FPR ≥ 0.99`
  - **Fisher χ²₆ combiner**: `AUC ≥ 0.998` and `recall@5 %FPR ≥ 0.99`
  The two variants are both closed-form "single universal formulas";
  the stack is fitted on CV folds, Fisher is parameter-free.
- **Stage 2a (random perturbations, non-inferiority)**: on exp41-style
  internal single-letter edits (1 360 Q-edits + 4 000 ctrl-edits),
  stacked logistic recall on Q-edits at the ctrl-p95 threshold is
  `≥ recall(R12-only)` (non-inferiority, not absolute threshold).
  Cohen d(NCD, Q vs ctrl) ≈ 0.534 at doc-scale bounds absolute recall
  to ~0.25–0.35; requiring 99 % here would be unscientific.
- **Stage 2b (canonical Adiyat variants)**: 3 canonical Adiyat edits
  (ع↔غ internal, ض↔ص terminal, both) all fire above the exp41 ctrl-p95
  NCD threshold (3/3), matching `exp41_gzip_formalised` §Test B.

Either Stage 1 or both Stage 2 conditions passing falsifies the
reviewer's claim that no single formula can hold the three layers
together; all three passing constitute a `PASS_unified` verdict
promotable to §4.36 of `PAPER.md`.

**Scope of the 99 % claim.** The "99.1 % on 864 single-letter variants"
figure in `PAPER.md:485` is on the **canonical Adiyat-864 benchmark**
(exhaustive single-letter swaps within Surah 100), not on random
perturbations. Full 864-variant enumeration and the matching 99 %
recall gate are deferred to `exp94_adiyat_864`.

## 2. Closed-form formulas (pre-registered, not re-fit post-hoc)

### Stage 1 — classification stack
```
L_TEL(x)   = 0.5329 * T(x) + 4.1790 * EL(x) - 1.5221       # LC3-70-U
PhiMag(x)  = || features_5d(x) - mu_ctrl ||_Mahal          # 5-D Mahalanobis
R12half(x) = NCD( half_A(x), half_B(x) )                   # self-compress
logit(P_Q) = b0 + b1*L_TEL(x) + b2*z(PhiMag(x)) + b3*z(R12half(x))
```

### Stage 2 — edit-detection stack
```
DeltaL(c,e)   = L_TEL(e) - L_TEL(c)                        # (T,EL) shift
NCD_edit(c,e) = gzip NCD( letters_28(c), letters_28(e) )   # exp41 R12
DeltaPhi(c,e) = || features_5d(e) - features_5d(c) ||      # 5-D delta
logit(P_edit) = g0 + g1*DeltaL + g2*z(NCD_edit) + g3*z(DeltaPhi)
```

### Fisher sanity-check combiner (parameter-free, non-stacked)
```
X^2(x) = -2 * ( ln p_L + ln p_R12 + ln p_Phi ) ~ chi^2_6   # under H0_indep
```

## 3. Fit protocol (frozen)

- **Seed**: `SEED = 42` throughout (matches exp89, exp41).
- **Outer CV**: `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`.
- **Scaler**: `StandardScaler` fit on inner-train split only.
- **Model**: `sklearn.linear_model.LogisticRegression(class_weight="balanced",
  solver="liblinear", C=1.0, random_state=42)`.
- **No feature selection. No hyperparameter search.**
- **Fisher p-values**: empirical one-sided CDF of each layer score against
  the ctrl-null distribution, clipped to `[1e-12, 1.0]` before log.

## 4. Evaluation sets

| ID | Set | n | Source |
|---|---|---|---|
| E1 | Band-A classification | 68 Q + 2 509 ctrl | `phase_06_phi_m.pkl` state |
| E2 | Internal single-letter perturbations | 1 360 Q + 4 000 ctrl | exp41 policy (byte-equal) |
| E3 | 3 Adiyat canonical variants | 3 | `CORPORA['quran']` Q:100 |
| E4 | Single-feature ablation | same as E1 | L only / R12half only / PhiMag only |

## 5. Pre-registered verdicts (evaluated in order)

| Code | Condition |
|---|---|
| `FAIL_sanity_L_drift` | \|AUC(L_TEL only, E1) − 0.9971\| > 0.002 (exp89/89b sanity) |
| `FAIL_sanity_R12_drift` | \|cohen_d(R12, E2) − 0.534\| > 0.05 (exp41 sanity) |
| `FAIL_stage1_auc` | AUC(logistic, E1 OOF) < 0.9975 **AND** AUC(Fisher, E1) < 0.998 |
| `FAIL_stage1_recall` | recall@5 %FPR(logistic, E1) < 0.99 **AND** recall@5 %FPR(Fisher, E1) < 0.99 |
| `FAIL_stage2a_non_inferiority` | recall(stack, E2 Q-edits) < recall(R12 only, E2 Q-edits) − 0.01 |
| `FAIL_stage2b_adiyat` | < 3 of 3 canonical Adiyat variants fire above ctrl-p95 NCD |
| `FAIL_overfit` | max CV train–test AUC gap > 0.01 |
| `PASS_unified` | Stage 1 AUC + recall pass, Stage 2a non-inferior, Stage 2b 3/3, sanity both OK |
| `PARTIAL_stage1_only` | Stage 1 passes but either Stage 2a or 2b fails |
| `PARTIAL_stage2_only` | Stage 2 passes but Stage 1 fails |

## 6. Honesty clauses (non-gating, always reported)

- **HC1 — Word-order ceiling**: stacked recall on D14 word-order-swap
  corpus is reported; no `≥ 99 %` claim is made here. This is bounded
  above by D14's 79 % strength per `RANKED_FINDINGS.md §15`.
- **HC2 — Cross-script**: stacked recall on Hebrew Tanakh / Greek NT /
  Arabic-Bible single-letter edits (if sets available in `CORPORA`)
  is reported as an honesty check. Expected `FAIL` per `exp90`.
- **HC3 — Single-feature dominance**: if `AUC(R12half only, E1)` or
  `AUC(L_TEL only, E1)` already ≥ `AUC(stack)` − 0.001, the stack is
  declared `PARSIMONY_NO_GAIN` even if `PASS_unified` is reached, and
  the paper must state that the stack is not a strict improvement over
  its best single component.

## 7. Locks not touched

No modification to:
- `results/integrity/results_lock.json`
- `results/integrity/code_lock.json`
- `results/integrity/corpus_lock.json`
- `results/integrity/headline_baselines.json`
- `results/checkpoints/_manifest.json`
- `notebooks/ultimate/QSF_ULTIMATE*.ipynb`

All new scalars from this experiment are tagged `(v7.8 cand.)` and
gated on two-team independent replication before any lock promotion.

## 8. Provenance

- Reads (integrity-checked): `results/checkpoints/phase_06_phi_m.pkl`
- Perturbation policy: byte-for-byte copy of `exp41_gzip_formalised._apply_perturbation`
- Writes only: `results/experiments/exp93_unified_stack/exp93_unified_stack.json`
- Design doc: this file
- Paper hook: candidate §4.36 `PAPER.md` if `PASS_unified`

## 9. Frozen constants (mirrored in `run.py` as module-level)

```python
SEED = 42
N_SPLITS = 5
LR_C = 1.0
W_T, W_EL, B_TEL = 0.5329, 4.1790, -1.5221
BAND_A_LO, BAND_A_HI = 15, 100
N_PERT_PER_UNIT = 20
CTRL_N_UNITS = 200
GZIP_LEVEL = 9
FPR_TARGET = 0.05
AUC_STAGE1_GATE = 0.9975        # logistic variant
AUC_FISHER_GATE = 0.998         # Fisher variant (v1.1)
RECALL_STAGE_GATE = 0.99
OVERFIT_GAP_MAX = 0.01
SANITY_L_AUC_EXP = 0.9971
SANITY_L_AUC_TOL = 0.002
SANITY_R12_D_EXP = 0.534
SANITY_R12_D_TOL = 0.05
```

---

*Pre-registered 2026-04-22. If any constant in §9 or formula in §2 is
changed after this file is committed, the experiment must be renamed
`exp93b_*` and this file marked SUPERSEDED.*
