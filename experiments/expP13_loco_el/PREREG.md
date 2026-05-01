# expP13_loco_el — Pre-Registration

**Frozen**: 2026-04-26
**Author**: v7.9-cand patch E sprint

## Background

`exp104_el_all_bands` reports overall AUC = 0.9813 for the EL one-feature
classifier on all 114 Quran surahs vs the 6-corpus Arabic-control pool.
Existing LOFO is at the family level (poetry / prose / hadith). This LOCO
ablation drops one *corpus* at a time to test whether any single corpus
is driving the result.

## Hypothesis

**H1**: For every leave-one-corpus-out variant, AUC ≥ 0.95.

## Pre-registered decision rule

| Outcome | Verdict |
|---|---|
| min LOCO AUC ≥ 0.97 | `ROBUST_STRONG` |
| 0.95 ≤ min LOCO AUC < 0.97 | `ROBUST` |
| 0.90 ≤ min LOCO AUC < 0.95 | `ROBUST_WEAK` (single corpus dominates) |
| min LOCO AUC < 0.90 | `FRAGILE` (qualifies §4.40.4 EL law) |

## Protocol

- For each of {poetry_jahili, poetry_islami, poetry_abbasi, ksucca,
  arabic_bible, hindawi, hadith_bukhari}: drop it, fit EL classifier on
  remainder, evaluate AUC.
- Train / eval on Quran (all 114) vs the 6 remaining corpora.
- SVM linear, C=1.0, class_weight='balanced', seed 42.

## Reproduction

```powershell
python -X utf8 -u experiments\expP13_loco_el\run.py
```
