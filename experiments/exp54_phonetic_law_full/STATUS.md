# exp54_phonetic_law_full — STATUS

- **Created**: 2026-04-21 (SCAN_2026-04-21T07-30Z, Step 2).
- **Pre-registration**: `PREREG.md` (this directory).
- **Purpose**: fix R6 — `exp47_phonetic_distance_law` consumed FAST-mode `exp46` input. Re-run the analysis against the current FULL-mode `exp46` output.
- **Status**: **EXECUTED** 2026-04-21.
- **Verdict**: **LAW_CONFIRMED** (M1_hamming r = +0.929, Spearman ρ = +0.742).
- **Result**: `results/experiments/exp54_phonetic_law_full/exp54_phonetic_law_full.json`
- **Depends on**: `results/experiments/exp46_emphatic_substitution/exp46_emphatic_substitution.json` with `fast_mode: false` (already on disk).
- **Supersedes**: `exp47_phonetic_distance_law` output once executed.

## Execution instruction

```powershell
python C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp54_phonetic_law_full\run.py
```

Runtime estimate: under 30 seconds (pure numpy/scipy correlation over 7 data points).
