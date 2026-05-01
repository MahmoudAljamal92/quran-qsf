# exp21 — E1 EL-rate survival (reframe of Cell 103)

**Status**: scaffolded 2026-04-20, runnable end-to-end.
**Touches the main notebook?** No.
**Writes to locked results?** No.
**Outputs**: `results/experiments/exp21_E1_EL_survival/exp21_E1_EL_survival.json`.

## Why this exists

`notebooks/ultimate/QSF_ULTIMATE.ipynb` Cell 103 (Phase 18, E1) reports
per-token substitution rate `P_e` under synthetic noise. `_p_error()`
literally counts tokens that differ — this is a tautology of the noise
model (the injected eps), not a property of the Quran.

External review (2026-04-20) recommends replacing `P_e` with
**EL-rate survival**: after eps-noise, what fraction of Band-A surahs
retain EL above the pre-noise median? This asks a real question about
the Quran's rhyme-channel robustness.

## Protocol (pre-registered here, 2026-04-20)

- eps ∈ {0.01, 0.02, 0.05, 0.10}
- Same noise model as Cell 97 (per-token single-letter substitution by
  a uniformly random Arabic consonant)
- Per corpus in ARABIC_FAMILY (Quran + 6 controls), Band A [15, 200]:
  1. `EL_before[u] = ft.el_rate(u.verses)`
  2. For each eps: inject noise, recompute `EL_after[u]`
  3. Report `fraction_retained = P(EL_after >= median(EL_before))`
- Pooled Cohen d of `EL_after_Quran` vs `EL_after_ctrl` at each eps
- Seed = 42 (deterministic)

## How to run

```powershell
python -m experiments.exp21_E1_EL_survival.run
```

Expected runtime: < 3 min. Self-check at the end guarantees no protected
file (including `results_lock.json`) was touched.

## What to do with the numbers

- **If `fraction_retained_Quran > fraction_retained_ctrl` at eps ≥ 0.05**:
  add a paragraph to `docs/PAPER.md` §4.1 (E1 reframe) and update the
  Cell 103 print to report this metric instead of `P_e`.
- **If not**: report as NULL in `docs/PAPER.md` §5 and retire the E1
  claim entirely.
