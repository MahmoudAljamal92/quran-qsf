# expP10_hadith_N1_prereg — Pre-Registration

**Frozen**: 2026-04-26
**Author**: v7.9-cand patch E sprint
**Status**: pre-registered before any data look

## Background

Audit patch D (`audit_patch.json::patch_5_hadith_disclosure`) flagged the
hadith Bukhari result (AUC = 0.972 from `expP9.NEW3`) as post-hoc
exploratory because hadith was added to the corpus pool *during* the
v7.9-cand sprint, after EL had already been computed on the original
Arabic-control pool. This pre-registration moves hadith from exploratory
→ formal pre-registered evidence.

## Hypothesis

**H1**: The 1-D EL classifier `f(x) = w·EL(x) + b`, fit on the full 114
Quran surahs vs. the 6-corpus Arabic control pool (poetry × 3 + ksucca +
arabic_bible + hindawi, n_ctrl = 4 605 units after band-A filter relax),
generalises to **hadith Bukhari** (held out completely from the training
set) with AUC ≥ 0.95.

## Pre-registered decision rule

| AUC bin | Verdict |
|---|---|
| AUC ≥ 0.97 | `PASS_STRONG` |
| 0.95 ≤ AUC < 0.97 | `PASS` |
| 0.90 ≤ AUC < 0.95 | `PASS_WEAK` (still useful, but weakens claim) |
| AUC < 0.90 | `FAIL` (hadith is too Quran-like for EL to distinguish) |

A `FAIL` verdict would NOT retract the EL one-feature law; it would
qualify it as "Quran-vs-secular-Arabic only", excluding Quran-quotation-
heavy religious-prose corpora.

## Frozen sample size + computational protocol

- Quran units: all 114 surahs (from `phase_06_phi_m.pkl::CORPORA[quran]`)
- Arabic control units: 4 605 from {poetry_jahili, poetry_islami,
  poetry_abbasi, ksucca, arabic_bible, hindawi}
- Hadith Bukhari: all chapters from `phase_06_phi_m.pkl::CORPORA[hadith_bukhari]`
- Min verses per unit: 2 (relaxed from band-A's 15 for full-114 coverage)
- SVM: linear kernel, C = 1.0, class_weight='balanced', random_state = 42
- Boundary fit on Quran ⊕ Arabic-ctrl ONLY; hadith evaluated as held-out test.
- Bootstrap CI on AUC: 500 paired resamples, seed 42.

## Frozen reporting

Output JSON `expP10_hadith_N1_prereg.json` contains:
- `auc_holdout_hadith`: AUC of (Quran=1, hadith=0) under the Quran-vs-Arabic-ctrl-trained boundary
- `auc_holdout_hadith_ci`: 95% bootstrap CI
- `mw_p_quran_vs_hadith`: Mann-Whitney U p-value, alternative='greater' (Quran EL > hadith EL)
- `n_quran`, `n_ctrl`, `n_hadith`
- `verdict`: one of {PASS_STRONG, PASS, PASS_WEAK, FAIL}
- `el_quran_mean`, `el_hadith_mean`, `el_ctrl_mean`
- `prereg_sha256`: SHA-256 of this PREREG.md (locks the hypothesis)

## Reproduction

```powershell
python -X utf8 -u experiments\expP10_hadith_N1_prereg\run.py
```

## Authority chain

- Supersedes the post-hoc claim in `expP9.NEW3` (now reframed as exploratory; this run is the formal binding test).
- Cited from `docs/PAPER.md §4.41.x` (after run completes).
