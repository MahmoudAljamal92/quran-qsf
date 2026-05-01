# exp104_el_all_bands — Pre-registration

**Frozen**: 2026-04-22 (before any run).
**Hypothesis ID**: H36 — EL-alone classifier generalises beyond Band-A and provides a **literally universal Task-A detector** across all 114 Quran surahs.
**Parent experiments**:
- `exp89b_five_feature_ablation` (EL-alone AUC = 0.9971 on Band-A only)
- `exp90_cross_language_el` (Quran-EL elevation is Arabic-specific, not scripture-class; verdict `FAIL_no_convergence`)
- `exp70_decision_boundary` (locked linear discriminant `L = 0.5329·T + 4.1790·EL − 1.5221`, Band-A only)

## 1. Motivation — closing the Task-A universality gap

Docs `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\RANKED_FINDINGS.md:17` and `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md:857` lock the parsimony result: EL alone classifies **68 Band-A Quran surahs** vs. **2 509 Band-A Arabic controls** at `AUC = 0.9971 ± 0.0006` across 5 seeds (`exp89b`). The 46 non-Band-A surahs (≤ 14 or > 100 verses) have **never been scored with this single-feature classifier**. The paper-grade claim is therefore structurally restricted to Band-A.

`src.features.el_rate` is a per-verse-pair statistic with **no length requirement** (it reduces to 0 for `n_verses < 2`, and is well-defined for every unit with `n_verses ≥ 2`). There is no mathematical obstruction to evaluating it on **all 114 Quran surahs** against the **full Arabic ctrl pool** at any length. This experiment measures whether the EL signal is genuinely length-invariant (as a population statistic on the Quran's terminal-letter distribution) or length-dependent.

**Either outcome is publishable**:
- **PASS_universal** → EL alone is the simplest literal-universal Task-A detector the project has ever produced, enabling a §4.37' paper section with a 10-line reference implementation.
- **PARTIAL_length_dependent** → honest, pre-registered length envelope of the EL signal; same data, different framing; rejects the "universal" reading while keeping the Band-A result.

## 2. Formula (pre-registered)

```
EL(x) = fraction of consecutive verse pairs (v_i, v_{i+1})
         with _terminal_alpha(v_i) == _terminal_alpha(v_{i+1}) != ""
         where _terminal_alpha strips DIAC and returns the last
         alphabetic character of the verse.
         [byte-equal to src.features.el_rate]

Classifier: sklearn SVC(kernel='linear', C=1.0, class_weight='balanced',
                       random_state=SEED) on the 1-D feature X = [EL].
AUC via sklearn.metrics.roc_auc_score on the SVM decision function.
```

No multivariate covariance. No morphological analyser. No diacritic signal. One number per text.

## 3. Evaluation protocol

**Step 1 — Load full CORPORA** (no Band-A gate).
Read `phase_06_phi_m.pkl` and extract `state['CORPORA']`. Keep every unit with `n_verses ≥ 2` (required for EL to be well-defined). Group into three length bands for stratified reporting:

- **Band-B (short)**: `2 ≤ n_verses < 15` (short Meccan surahs incl. Al-Adiyat).
- **Band-A (current paper scope)**: `15 ≤ n_verses ≤ 100`.
- **Band-C (long)**: `n_verses > 100`.

**Step 2 — Compute EL per unit**. Call `src.features.el_rate` on every Quran surah and every Arabic-ctrl unit in `ARABIC_CTRL = {poetry_jahili, poetry_islami, poetry_abbasi, ksucca, arabic_bible, hindawi}`. Record `(corpus, label, n_verses, band, el)`.

**Step 3 — Overall classifier**.
Fit linear SVM on `X = [el_rate]` over the full pool (all Quran units with `n_verses ≥ 2` vs all Arabic-ctrl units with `n_verses ≥ 2`). Report:
- `auc_overall`
- `accuracy_overall`
- `svm_w`, `svm_b` (the explicit 1-D discriminant `w·EL + b = 0`)
- `bootstrap CI on AUC` (n_boot = 500, resample Quran and ctrl independently with replacement)

**Step 4 — Per-band classifier**.
For each band ∈ {Band-B, Band-A, Band-C}, fit a separate linear SVM on the subset and report per-band AUC + accuracy + bootstrap CI. Also report AUC when the **Band-A-trained SVM** is evaluated on Band-B and Band-C test subsets (held-out generalisation — the strongest universality test).

**Step 5 — Sanity vs. exp89b**.
On the Band-A subset, the measured AUC must reproduce `exp89b.single_feature["EL"].auc = 0.9971 ± 0.005`. If not, `FAIL_exp89b_reproduction_broken` — indicates a data-loading bug, not a hypothesis failure.

**Step 6 — Per-band-per-corpus coverage**.
Report how many units of each corpus fall in each band, and the per-band median EL for Quran vs each ctrl family. A reviewer should be able to read off which band the signal lives in.

## 4. Pre-registered verdicts (evaluated in order)

| Code | Condition |
|---|---|
| `FAIL_exp89b_reproduction_broken` | Band-A EL-alone AUC differs from `exp89b` by > 0.005 (data loading bug) |
| `FAIL_not_universal` | `auc_overall` < 0.95 |
| `PARTIAL_length_dependent` | `0.95 ≤ auc_overall < 0.99` OR any single band has `auc_band < 0.95` |
| `PASS_universal_strong` | `auc_overall ≥ 0.99` AND every band has `auc_band ≥ 0.95` |
| `PASS_universal_uniform` | `auc_overall ≥ 0.99` AND every band has `auc_band ≥ 0.99` (strongest outcome) |

**Expected outcome** (honest pre-run prediction, documented here to check calibration):

| Scenario | Prior probability |
|---|---:|
| PASS_universal_uniform | ~25% — EL is conceptually length-agnostic; rhyme rate is a per-verse-pair statistic; controls are bimodal (poetry high-EL short; prose low-EL long), so the signal may survive |
| PASS_universal_strong | ~40% — Band-B surahs are typically very short (2–11 verses), EL variance on 1–10 pairs is high, some ctrl poetry units have high EL at short length |
| PARTIAL_length_dependent | ~30% — Band-C surahs (long) have a different terminal-letter distribution (narrative Medinan prose), may drift toward Arabic-bible |
| FAIL_not_universal | ~5% — hedged; highly unlikely given Band-A AUC of 0.9971 and the exp90 measurement that the raw Quran EL mean (0.71) is 3× every single control family |

## 5. Honesty clauses

- **HC1 — Test set identity**. This experiment uses **no held-out split**; the full pool is both train and evaluation, mirroring `exp89b`'s descriptive framing. A reviewer who demands held-out numbers should cite `exp36_TxEL_seed_metaCI` (0.9971 ± 0.0006 across 5 outer seeds × 5 folds); cross-validating on this broader pool would be appropriate only if PASS fires and the result goes to paper.
- **HC2 — EL is not a new feature**. EL is already blessed (`results/integrity/results_lock.json`). This experiment is about its **domain of applicability**, not its definition.
- **HC3 — Cross-language silence**. `exp90_cross_language_el` showed EL does NOT generalise to Hebrew Tanakh, Greek NT, or `arabic_bible`. This experiment does not re-open that question — it is strictly intra-Arabic, across all three length bands.
- **HC4 — Corpus-level classification only**. This is Task A (is this text Quranic?). It says nothing about edit detection (Task B, §4.25 R12). A PASS here does not speak to the exp95 / exp104 edit-detection gap.
- **HC5 — No Band-A definitional flex**. Bands are `[2, 14]`, `[15, 100]`, `[101, ∞)` on `n_verses`. Quran surahs under 2 verses (there is one: Surah 108 Al-Kawthar with 3 verses, all ≥ 2 anyway) are included in Band-B. No surah is dropped.

## 6. Locks not touched

No modification to any file under `results/integrity/`, `results/checkpoints/`, or `notebooks/ultimate/`. All new scalars tagged `(v7.9 cand.)`. Integrity `self_check_end` must pass.

## 7. Frozen constants

```python
SEED = 42
SVM_C = 1.0
N_BOOT = 500
BAND_B = (2, 14)        # short
BAND_A = (15, 100)      # current paper scope
BAND_C = (101, 10**9)   # long
MIN_VERSES = 2          # EL is undefined for n_verses < 2
ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
EXP89B_REPRODUCTION_TOL = 0.005
```

## 8. Provenance

- Reads (integrity-checked): `results/checkpoints/phase_06_phi_m.pkl` (CORPORA only)
- Reads (receipt, sanity): `results/experiments/exp89b_five_feature_ablation/exp89b_five_feature_ablation.json` (for AUC reproduction tolerance)
- Imports: `src.features.el_rate` (no modification)
- Writes only: `results/experiments/exp104_el_all_bands/exp104_el_all_bands.json` and `self_check_*.json`
- Paper hook: candidate `docs/PAPER.md §4.37'` — *Universal Task-A EL classifier across all 114 surahs*

---

*Pre-registered 2026-04-22. Prereg hash is computed at run-time and stored in the output JSON under `prereg_hash`.*
