# exp89_lc3_ablation — PRE-REGISTRATION

**Timestamp**: 2026-04-21 (late evening, v7.7)
**Status**: Frozen BEFORE any run. No numerical result is seen before this document is committed.

---

## 1. Source of the commitment

`docs/RANKED_FINDINGS.md §3 Tier A, row 3` ("Path to 100 %" item (c)):

> (c) pre-register ablation commitment ("AUC(T only) < 0.95 AND AUC(EL only) < 0.95 AND AUC(T, EL) ≥ 0.99") before running — rules out cherry-pick.

This has been a standing open item on `LC3` since `docs/PAPER.md §4.22` and is reiterated in `§4.35 LC3-70-U` Path to PROVED (v7.7). This experiment closes it.

## 2. Hypothesis

**H-LC3-ABL** — LC3-70-U's (T, EL) 2-feature sufficiency implies:
- Neither `T` alone nor `EL` alone achieves AUC ≥ 0.95 on the Band-A 68 Q + 2 509 ctrl pool.
- The 2-feature (T, EL) combination achieves AUC ≥ 0.99 (and reproduces `exp70`'s 0.9975 byte-exactly by construction).

## 3. Pre-registered verdict ladder

Evaluated in this exact order (first match wins):

1. **FAIL_sanity_exp70_drift** — `|AUC(T, EL) − 0.9975| > 0.001` → methodology bug, result invalid, re-run or debug.
2. **FAIL_joint_weak** — `AUC(T, EL) < 0.99` → impossible if sanity passed (exp70 fit); indicates deeper issue.
3. **FAIL_T_dominates** — `AUC(T only) ≥ 0.95` → sufficiency is 1-D in T, not 2-D (would be a simpler, stronger claim).
4. **FAIL_EL_dominates** — `AUC(EL only) ≥ 0.95` → sufficiency is 1-D in EL, not 2-D.
5. **PASS** — `AUC(T only) < 0.95` AND `AUC(EL only) < 0.95` AND `AUC(T, EL) ≥ 0.99`. Both single features must fail the 0.95 bar AND the pair must clear 0.99.
6. **MIXED** — anything else (should not occur by construction).

## 4. Methodology (frozen, no deviation permitted)

- **Data**: `state["X_QURAN"]` (68 × 5) and `state["X_CTRL_POOL"]` (2 509 × 5) from `results/checkpoints/phase_06_phi_m.pkl` via `experiments._lib.load_phase("phase_06_phi_m")`. Band-A (15 ≤ n_verses ≤ 100) already applied by `_build.py` upstream.
- **Labels**: Quran = 1, Ctrl = 0.
- **Classifier**: `sklearn.svm.SVC(kernel="linear", C=1.0, random_state=42)` — byte-identical to `exp70_decision_boundary/run.py:109`.
- **Scoring**: `roc_auc_score(y, svm.decision_function(X))` — in-sample, matching `exp70` methodology. No cross-validation by design — the comparison target is `exp70`'s own in-sample AUC = 0.9975.
- **Three fits**:
  1. `T_only`: X[:, [T_idx]] (1 column) where `T_idx = FEAT_COLS.index("T")` = 4.
  2. `EL_only`: X[:, [EL_idx]] (1 column) where `EL_idx = FEAT_COLS.index("EL")` = 0.
  3. `TEL_joint`: X[:, [T_idx, EL_idx]] (2 columns).
- **Bootstrap**: 1 000 resamples with replacement (within-class, preserving `n_q` and `n_c`) for 95 % CI on each AUC. `N_BOOT = 1_000` (not 10 000 like `exp70`, since this is a sanity test and thresholds are well-separated).
- **Output**: single JSON at `results/experiments/exp89_lc3_ablation/exp89_lc3_ablation.json` with all three AUCs, bootstrap CIs, sanity check, and verdict string.

## 5. Built-in sanity check

The `TEL_joint` AUC must equal `exp70_decision_boundary.json::svm.auc = 0.9975` within absolute tolerance 0.001. This is a **methodology fingerprint** — any drift indicates either a different random seed path, a different band-A filter, or a scikit-learn version change. If triggered, the run is invalid and no verdict should be reported until resolved.

## 6. Stakes

- **PASS** → closes `RANKED_FINDINGS.md §3 row 3` Path-to-100% item (c). Row-3 strength 92 % → can argue 93 %. Row 3 joins row 1 in Tier A. `PAPER.md §4.35` gains a "Path to PROVED item (b) confirmed" footnote.
- **FAIL_T_dominates** — interesting: T alone is a 1-D classifier ≥ 95 %. Theorem simplifies to `LC3-T-Only`. Would supersede LC3-70-U with a stronger 1-D claim.
- **FAIL_EL_dominates** — similar, but less consistent with prior 5-D ranked-findings (EL was always descriptive, not predictive). Would be a surprise and trigger a second audit.
- **FAIL_sanity / FAIL_joint_weak** — pipeline bug, not a scientific result. Debug.
- **MIXED** — should not occur by construction; if it does, investigate pre-reg wording.

## 7. No further parameter tuning

Once this PREREG is committed, `SVM_C = 1.0`, `SEED = 42`, `N_BOOT = 1000`, `THRESHOLD_SINGLE = 0.95`, `THRESHOLD_JOINT = 0.99`, `EXP70_AUC = 0.9975`, `EXP70_AUC_TOL = 0.001` are frozen. Any deviation requires a new experiment number and a new PREREG. This doc is the audit trail.

---

*Pre-registration committed 2026-04-21. Results to follow in `exp89_lc3_ablation.json` and `NOTES.md`.*
