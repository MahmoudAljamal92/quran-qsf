# expP14_cross_script_dominant_letter — Pre-Registration

**Frozen**: 2026-04-26
**Author**: v7.9-cand patch E sprint

## Background

`audit_patch.json::patch_1_per_corpus_noon_rate` reports per-Arabic-corpus
ن-finals fractions. The companion §4.41.8 forensics also reports the
Bible (Hebrew Tanakh + Greek NT etc.) overall ن rate. PNAS-class reviewers
will demand a **single uniform table** comparing all 13+ corpora on the
same statistic. This experiment produces it.

## Hypothesis

**H1**: For each corpus, compute the *dominant terminal-letter fraction*
`p_max = max_letter p̂(letter | terminal)`. The Quran's `p_max(ن) ≈ 0.50`
exceeds every other natural-letter `p_max` in the comparison set, with a
ratio ≥ 4× over the second-highest natural-letter dominance.

## Pre-registered decision rule

| Outcome | Verdict |
|---|---|
| ratio ≥ 4× over 2nd | `QURAN_DOMINANCE_CONFIRMED` |
| 2× ≤ ratio < 4× | `QURAN_DOMINANCE_PARTIAL` |
| ratio < 2× | `QURAN_DOMINANCE_REJECTED` |

(Excluding transliteration markers like `.`, `,`, `॥` from "natural letters".)

## Protocol

For each of: quran, hadith_bukhari, poetry_jahili, poetry_islami,
poetry_abbasi, ksucca, arabic_bible, hindawi, hebrew_tanakh, greek_nt,
iliad_greek, pali_mn, vedic_rigveda, avesta_yasna —
1. Concatenate all unit verses
2. Extract terminal alphabetic character per verse (skip non-alpha)
3. Compute frequency distribution
4. Report top-5 letters + their frequencies + p_max

## Reproduction

```powershell
python -X utf8 -u experiments\expP14_cross_script_dominant_letter\run.py
```
