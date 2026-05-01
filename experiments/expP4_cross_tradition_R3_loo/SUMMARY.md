# expP4_cross_tradition_R3_loo — Summary

**Date**: 2026-04-25
**Type**: Post-hoc robustness analysis of `expP4_cross_tradition_R3`.
**Method**: Deterministic — re-evaluates LC2 pre-registered gates and BH adjustment on each 7-corpus subset of the parent's 8-corpus result. No new permutations needed (per-corpus z-scores are statistically independent).

## Verdict

**8 of 8 single-corpus drops still produce a SUPPORT verdict** for the LC2 universal.

| Dropped corpus | Class | Dropped z_path | LC2 verdict on remaining 7 |
|---|---|---:|---|
| `quran` | oral_liturgical | −8.92 | **SUPPORT** |
| `hebrew_tanakh` | narrative_or_mixed | −15.29 | **SUPPORT** |
| `greek_nt` | narrative_or_mixed | −12.06 | **SUPPORT** |
| `iliad_greek` | narrative_or_mixed | +0.34 | **SUPPORT** (PRED-LC2.3 vacuous: no neg. control left) |
| `pali_dn` | oral_liturgical | −0.26 | **SUPPORT** (3/3 remaining new-oral pass) |
| `pali_mn` | oral_liturgical | −3.46 | **SUPPORT** |
| `rigveda` | oral_liturgical | −18.93 | **SUPPORT** (verdict survives even without the strongest signal) |
| `avestan_yasna` | oral_liturgical | −3.98 | **SUPPORT** |

Fragile drops: **none**.

## Why this matters

Two natural reviewer objections to the parent SUPPORT verdict are:

1. *"Rigveda's z = −18.93 is so dominant that the BH-pooled significance might collapse without it."* — Falsified: dropping Rigveda still yields BH-min p < 0.05 with 2 of 3 remaining new-oral corpora at z < −2.
2. *"The pali_dn failure (n = 34, z = −0.26) is dragging the headline down; restricting to the 'good' 3 new-oral would inflate the apparent universality."* — Falsified the other way: dropping pali_dn the verdict is still SUPPORT (and *stronger*: 3 of 3 remaining new-oral pass), so the headline is not propped up by hand-picking.

The LC2 verdict is therefore robust against both directions of single-corpus pressure.

## Caveats

- This is a leave-**one**-out at the **corpus** level. It does not test leave-out at the *unit* (sutta / sūkta / chapter) level within each corpus — that would require re-permutation and is the natural next robustness check.
- The pre-registered PRED-LC2.1 floor used here (≥ 2 of new-oral at z < −2) is the parent's own pre-registered "two_of_four" threshold. Tightening it to 3-of-3 would naturally make the avestan + pali_mn drops fragile, but that would be moving the goalpost relative to PREREG.

## Files

```
experiments/expP4_cross_tradition_R3_loo/run.py                     this script
results/experiments/expP4_cross_tradition_R3_loo/expP4_*_loo.json   full LOO matrix
```

Parent JSON SHA-256 pinned in the output: see `parent_json_sha256`.
