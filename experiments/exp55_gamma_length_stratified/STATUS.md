# exp55_gamma_length_stratified — STATUS

- **Created**: 2026-04-21 (SCAN_2026-04-21T07-30Z, Step 2).
- **Pre-registration**: `PREREG.md` (this directory).
- **Purpose**: apply formal decision rule (H3) to `exp41`'s existing `length_audit.json` per-decile data and add bootstrap CIs + sign-test.
- **Status**: **EXECUTED** 2026-04-21.
- **Verdict**: **LENGTH_DRIVEN** (5/10 deciles d > 0.30, sign-test p = 0.109; γ = +0.0716 remains strongly positive).
- **Result**: `results/experiments/exp55_gamma_length_stratified/exp55_gamma_length_stratified.json`
- **Depends on**: `results/experiments/exp41_gzip_formalised/length_audit.json` (already on disk).
- **Supersedes**: none (new analysis on existing data; does NOT supersede exp41 itself).

## Execution instruction

```powershell
python C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp55_gamma_length_stratified\run.py
```

Runtime estimate: under 10 seconds (reads existing JSON, applies decision rules, no heavy computation unless bootstrap requires replay).
