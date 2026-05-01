# expP8_T_pos_cross_tradition — pre-registered prediction document

**Date authored:** 2026-04-26 PRE-RUN. The hypotheses below are frozen
**before** any compute on this experiment.

**Status:** PREREG. Subsequent edits to this PREREG.md must be visible
in `git diff` against the pre-bless commit.

---

## 1. Motivation

The single largest Quran-vs-control contrast in the project is

```
%T_pos(Quran)        =  39.7 %     (Band-A, T_canon, CamelTools roots)
%T_pos(any control)  ≤   0.10 %    (max across 6 Arabic control families)

→ ratio  =  397×  ≈  400×          (locked, exp_T7 / D14)
```

This is reported in `docs/PAPER.md §3.1` as the largest single-scalar
Quran-vs-Arabic contrast in the project (no other scalar has a 400×
ratio). It uses the **Arabic-specific** definition

```
T_canon(s) = H_cond_roots(s) − H_el(s)       (paper §2.6, F-11 fix)
```

which depends on CamelTools morphological analysis and therefore
**cannot** be evaluated on Hebrew, Greek, Pāli, Sanskrit, or Avestan.

For a cross-tradition test, the project provides a parallel
**language-agnostic** definition (`src/features.py:200-235`):

```
T_lang(s) = H_cond_initials(s) − H_el(s)
```

where `H_cond_initials` is the conditional entropy of word-initial
character transitions across all words in the unit (no morphology
required). `T_lang` is well-defined for any Unicode-text corpus.

The honest open question this experiment closes is:

> **Is the 397× %T_pos enrichment of the Quran a property of the
> Quran's *Arabic-morphology* signal (T_canon, CamelTools) or does it
> survive in a language-agnostic surrogate (T_lang) and replicate in
> other oral-liturgical canons (Rigveda, Pāli, Avestan, Tanakh, NT)?**

This is exactly the cross-tradition test the handoff pack flagged as
"single biggest bang for the buck, 2 hours of compute"
(`docs/reference/handoff/2026-04-25/03_NOBEL_AND_PNAS_OPPORTUNITIES.md`,
%T_pos / S6 row).

---

## 2. Hypotheses (descriptive + pre-registered verdicts)

**H-P8-A** — `%T_lang_pos(Quran)` is statistically distinguishable
from `%T_lang_pos` of every other corpus in the 8-corpus cross-
tradition universe (Quran is the unique outlier under the
language-agnostic surrogate).

**H-P8-B** — `%T_lang_pos` median of the *oral-liturgical class*
(Quran, Pali_DN, Pali_MN, Rigveda, Avestan_yasna) exceeds the
*narrative-or-mixed class* median (Tanakh, Greek NT, Iliad) by ≥ 2×.

**H-P8-C** — `%T_lang_pos(Quran)` ≥ 10 % under T_lang (i.e., the
Quran's enrichment is **not** purely a CamelTools artefact).

These are descriptive; the verdicts table assigns labels.

---

## 3. Pre-registered verdicts (evaluated in this order)

| Code | Condition |
|---|---|
| `PASS_QURAN_UNIQUE` | %T_lang_pos(Quran) ≥ 5× the next-highest non-Quran corpus AND %T_lang_pos(Quran) ≥ 0.10 |
| `PASS_ORAL_CLASS_LAW` | Median %T_lang_pos(oral-liturgical) ≥ 2× median %T_lang_pos(narrative-or-mixed) AND Quran ≥ 5× any Arabic-control corpus |
| `PASS_BOTH` | both PASS_QURAN_UNIQUE and PASS_ORAL_CLASS_LAW conditions hold |
| `PARTIAL_LANG_AGNOSTIC_DOWNGRADE` | %T_lang_pos(Quran) ≥ 0.10 BUT < 5× next-highest non-Quran corpus |
| `FAIL_NO_ENRICHMENT_UNDER_T_LANG` | %T_lang_pos(Quran) < 0.10 (the 39.7 % is a CamelTools artefact under T_canon) |
| `FAIL_QURAN_NOT_HIGHEST` | another corpus has higher %T_lang_pos than Quran |

**Expected outcome** (honest pre-run prediction documented for
calibration; total ≤ 100 %):

| Scenario | Prior probability |
|---|---:|
| PASS_BOTH | ~25 % |
| PASS_QURAN_UNIQUE only | ~25 % |
| PASS_ORAL_CLASS_LAW only | ~10 % |
| PARTIAL_LANG_AGNOSTIC_DOWNGRADE | ~25 % |
| FAIL_QURAN_NOT_HIGHEST | ~10 % (Rigveda is a real risk given R3 z = −18.93 strongest) |
| FAIL_NO_ENRICHMENT_UNDER_T_LANG | ~5 % |

---

## 4. Method (locked)

- **Corpora**: 8 cross-tradition (`quran`, `hebrew_tanakh`, `greek_nt`,
  `iliad_greek`, `pali_dn`, `pali_mn`, `rigveda`, `avestan_yasna`) +
  6 Arabic controls (`poetry_jahili`, `poetry_islami`, `poetry_abbasi`,
  `ksucca`, `arabic_bible`, `hindawi`). Loaded via
  `raw_loader.load_all(include_extras=True, include_cross_lang=True,
  include_cross_tradition=True)` to match `expP4_cross_tradition_R3`.
- **Stopwords for CN**: `ARABIC_CONN` for the Quran and 6 Arabic ctrls
  (paper §2.2), `derive_stopwords(verses, top_n=20)` for every
  non-Arabic corpus. (Stopwords are not used in T_lang computation;
  retained only for parity with `_run_corpus`.)
- **Feature**: `T_lang(s) = h_cond_initials(s) − h_el(s)` exactly as
  defined in `src/features.py:200-235`. No morphological analyser.
  No diacritic signal. Pure character-level statistics.
- **Band gating**: %T_lang_pos reported in two scopes:
  - `all_units`: every unit in the corpus with `n_verses ≥ 2`.
  - `band_a`: units with `15 ≤ n_verses ≤ 100` (matches paper Band-A).
  All-units numbers are reported alongside Band-A numbers; Band-A is
  the locked-paper-comparable scope.
- **Comparison anchor**: also compute `T_canon(s) = h_cond_roots(s) −
  h_el(s)` for the Quran and the 6 Arabic controls (CamelTools is
  available for Arabic only) to verify the locked 39.7 % number
  reproduces. This is the sanity check.
- **Bootstrap CI**: 5 000 resamples per corpus per scope, seed = 42.
  Report median, 2.5 %, 97.5 % %T_pos.
- **Class summary**: aggregate %T_lang_pos by tradition class
  (`oral_liturgical` / `narrative_or_mixed` per
  `expP4_cross_tradition_R3:_tradition_class_of`).

---

## 5. Reads / writes

- **Reads only** (integrity-checked):
  - `data/corpora/{ar,he,el,pi,sa,ae}/...` via `raw_loader.load_all`
  - `results/checkpoints/phase_06_phi_m.pkl` for cross-validation of
    the locked Band-A subset (Quran and Arabic ctrls)
- **Writes only** under `results/experiments/expP8_T_pos_cross_tradition/`:
  - `expP8_T_pos_cross_tradition.json`
  - `self_check_<ts>.json`

---

## 6. Falsifiers

Any of:

- **F1** — `FAIL_NO_ENRICHMENT_UNDER_T_LANG`: %T_lang_pos(Quran) < 0.10.
  This would falsify the cross-language framing of %T_pos as a
  "Quran-distinctive scalar"; the 39.7 % becomes a CamelTools artefact.
- **F2** — `FAIL_QURAN_NOT_HIGHEST`: any other corpus has %T_lang_pos
  > Quran's. Falsifies the "Quran is the unique enrichment outlier"
  framing; reframe as class property if PASS_ORAL_CLASS_LAW survives.
- **F3** — Both F1 and F2 simultaneously: %T_pos is not a useful
  cross-tradition scalar; the locked 397× ratio under T_canon is
  Arabic-morphology-specific, not generalisable.

---

## 7. No locks touched

No modification under `results/integrity/`, `results/checkpoints/`,
or `notebooks/ultimate/`. All new scalars tagged `(v7.9 cand.)`.
`self_check_end` must pass.

---

## 8. Frozen constants

```python
SEED = 42
N_BOOTSTRAP = 5000
BAND_A_LO = 15
BAND_A_HI = 100
MIN_VERSES = 2
ORAL_LITURGICAL_CORPORA = {
    "quran", "pali_dn", "pali_mn", "rigveda", "avestan_yasna",
}
NARRATIVE_OR_MIXED_CORPORA = {
    "hebrew_tanakh", "greek_nt", "iliad_greek",
}
ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
```

---

*Pre-registered 2026-04-26 PRE-RUN. Prereg hash computed at run-time
and stored in the output JSON under `prereg_hash`.*
