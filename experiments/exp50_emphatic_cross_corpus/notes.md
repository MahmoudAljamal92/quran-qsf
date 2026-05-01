# exp50 -- Cross-corpus emphatic substitution audit

**Status**: scaffolded 2026-04-21, pre-registered, runnable end-to-end.
**Outputs**: `results/experiments/exp50_emphatic_cross_corpus/exp50_emphatic_cross_corpus.json`.
**Dependencies**: inherits exp46 / exp09 helpers (nothing new).

## Why this exists

`exp46_emphatic_substitution` found that the 9-channel R1 detector
fires on only **1.15 %** of exhaustive Quran emphatic substitutions
(full mode, 114 surahs, 10 461 edits, >= 3-of-9 |z| > 2 rule). Two
competing explanations:

- **H1 STRUCTURAL** — any Arabic corpus would score the same ~ 1 %;
  the blindness is baked into Arabic phonology (emphatic/plain pairs
  differ by a single articulatory feature, so bigram / root / wazn
  channels hardly see the edit).
- **H2 QURAN-SPECIFIC** — Arabic controls subjected to the *same*
  enumeration score much higher; the Quran's rhyme/word-length
  structure truly resists phonetically plausible forgery.

exp50 runs the exact exp46 pipeline on two major Arabic controls:
`poetry_abbasi` (2 823 units, multi-century corpus) and
`poetry_jahili` (133 pre-Islamic odes) and reports their rates side
by side.

## Pre-registration (frozen before any run)

### Protocol

For each `target` in `{poetry_abbasi, poetry_jahili}`:

1. Build 9-channel reference stats (`ref_bi`, `root_lm`) from the
   other five Arabic controls (leave-target-out). Matches exp46
   (Quran used 5 controls excluding Quran itself).
2. Build the swap-type null from `target` units (same sample size
   as exp46's Quran null).
3. Enumerate every emphatic-class substitution in a sample of
   `target` units (fast: 20; full: 60). Cap 100 edits per unit to
   bound runtime.
4. Score each edit through `exp09.nine_channel_features`, compute
   z-scores vs the null, and declare DETECTED if >= 3 of 9 channels
   have |z| > 2.

### Decision rule (pre-registered)

Let `R_X` = target's overall detection rate. The pre-reg thresholds:

- `R_X <= 0.020`   ⇒  `H1_STRUCTURAL_ARABIC_BLINDNESS`
- `R_X >= 0.050`   ⇒  `H2_QURAN_SPECIFIC_IMMUNITY` (controls score
  >= 4.3x Quran's 1.15 %)
- `0.020 < R_X < 0.050`  ⇒  `INCONCLUSIVE`

The aggregate verdict uses `max(R_poetry_abbasi, R_poetry_jahili)`
under the same rule (a single control breaching 5 % is enough to
support H2).

## How to run

Fast (~6 min, 2 corpora x 20 units):
```powershell
python -X utf8 -u experiments\exp50_emphatic_cross_corpus\run.py --fast
```

Full (~40 min, 2 corpora x 60 units):
```powershell
python -X utf8 -u experiments\exp50_emphatic_cross_corpus\run.py
```

## Interpretation

If H1 is supported, the exp46 result becomes "Arabic-structural"; the
paper should frame emphatic-class blindness as a property of the
language, not the Quran. If H2 is supported, exp46 and exp50 jointly
support the claim "Quran is notably immune to phonetically plausible
single-letter forgery" — a stronger statement about structural
distinctness than even the 5-D Phi_M Hotelling separation.

## References

- Quran baseline: `experiments/exp46_emphatic_substitution/run.py`,
  result in `results/experiments/exp46_emphatic_substitution/exp46_emphatic_substitution.json`.
- Detector: `experiments/exp09_R1_variant_forensics_9ch/run.py`.
- Helpers: `experiments/_ultimate2_helpers.py`.
