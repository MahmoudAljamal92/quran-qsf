# E19 — Feature-Level Ring Composition Test

**Run date**: run-of-record
**Seed**: 42
**Verdict**: **NULL_NO_RING**

## Design

- 5-D per-verse features: (chars, words, connector_count, unique_letters, mean_word_length).
- z-score each feature **within surah** so distance is scale-invariant.
- Test statistic per surah: `D_obs = mean_{i<n/2} ||V[i] - V[n-1-i]||²`.
- Null: 1000 random verse-order permutations per surah (seed 42).
- Combiner: Fisher's method over 79 surahs with n ≥ 20.
- Pre-reg falsifier: combined p > 0.01 ⇒ NULL.

## Results

| Quantity | Value |
|---|---|
| Surahs tested | 79 |
| Surahs with p ≤ 0.05 | 6 (expected 4.0 under null) |
| Surahs with p ≤ 0.01 | 0 (expected 0.8 under null) |
| Fisher χ² | 152.70 |
| Fisher df | 158 |
| **Fisher combined p** | **6.0412e-01** |

## Interpretation

**NULL_NO_RING** — Fisher-combined p > 0.05. At the 5-D per-verse feature level, mirror-position verses are not systematically more similar than random. Consistent with H20 (lexical ring = NULL at exp86); closes the door on the Excel-R3 ring-composition claim at two independent representation levels.

## Crosslinks

- Spec: `docs/EXECUTION_PLAN_AND_PRIORITIES.md` §E19
- Prior H20 test (lexical): `docs/HYPOTHESES_AND_TESTS.md` H20
- Raw output: `results/experiments/expE19_ring_composition/expE19_report.json`
