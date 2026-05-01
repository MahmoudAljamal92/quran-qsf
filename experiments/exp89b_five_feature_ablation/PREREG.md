# exp89b_five_feature_ablation — PRE-REGISTRATION

**Timestamp**: 2026-04-21 (late evening, v7.7)
**Status**: Frozen BEFORE any run. Extends `exp89_lc3_ablation` (which fired `FAIL_T_dominates` — but the real story is `EL alone AUC = 0.9971`) to all 5 blessed features.

---

## 1. Motivation

`exp89` revealed that EL alone reaches AUC = 0.9971 (within bootstrap CI of the 2-feature joint AUC = 0.9975). This prompts the honest question: **which of the 5 blessed features (EL, VL_CV, CN, H_cond, T) are paper-grade single-feature classifiers, and by how much?**

`exp60_lc3_parsimony_theorem` answered this at the *conditional-MI* level (residual CMI ≤ 0.089 bits), but not at the *predictive-AUC* level per-feature. This experiment closes that gap.

## 2. Hypotheses

**H-5FA-1** — At least one single feature achieves AUC ≥ 0.95.
**H-5FA-2** — Multiple single features achieve AUC ≥ 0.95 (signalling broad redundancy).
**H-5FA-3** — No 2-feature pair beats the best single feature by more than 0.005 AUC (confirms the LC3 "no joint gain" observation).

These are **descriptive hypotheses**, not pass/fail gates. The experiment's job is to characterise the AUC profile across all 5 features; the data will determine which of H-5FA-1/2/3 hold.

## 3. Methodology (frozen)

- **Data**: same as `exp89` — Band-A 68 Q + 2 509 Arabic ctrl from `phase_06_phi_m.pkl`.
- **Classifier**: `sklearn.svm.SVC(kernel="linear", C=1.0, random_state=42)` — matches `exp70` and `exp89`.
- **Scoring**: in-sample `roc_auc_score(y, svm.decision_function(X))`.
- **Fits**: 5 single-feature + 10 all-two-feature-pairs + 1 full 5-D = **16 fits total**.
- **Bootstrap**: 500 resamples per fit (within-class), seed 42.

## 4. Pre-registered output structure

Report every single feature's and pair's AUC, accuracy, and bootstrap 95 % CI. Rank all 5 single features by AUC. Report the best-single and best-pair AUCs and their delta.

## 5. No pass/fail gate

This is a **characterisation run**, not a hypothesis test. Scientific follow-up depends on what the ranking reveals:
- If EL dominates by > 0.05 AUC over all other single features → the theorem simplifies to 1-D EL.
- If two or three features are within 0.02 AUC of each other → LC3 is a multi-1D "family" of near-equivalent sufficient statistics.
- If no single feature exceeds 0.95 → the original 2-feature framing was right after all and `exp89`'s FAIL was a threshold artefact.

## 6. Stakes

Feeds directly into:
- Whether `PAPER.md §4.35 LC3-70-U` should be renamed `LC3-EL` or retained.
- Whether `RANKED_FINDINGS row 3` strength 92 % should rise (if 1-D theorem) or fall (if ambiguous).
- Whether cross-language `exp90` should test EL alone or a specific feature combination.

---

*Pre-registered 2026-04-21 post-exp89. No numerical result seen before this document committed.*
