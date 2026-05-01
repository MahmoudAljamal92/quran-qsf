# exp53_ar1_6d_gate — STATUS

- **Created**: 2026-04-21 (SCAN_2026-04-21T07-30Z, Step 2).
- **Pre-registration**: `PREREG.md` (this directory).
- **Purpose**: test H2 — AR(1) φ₁ on verse-length as 6th Φ_M channel.
- **Status**: **EXECUTED** 2026-04-21.
- **Verdict**: **SIGNIFICANT_BUT_REDUNDANT** (T²_6D = 3 591.5 < 4 268.8 gate; per-dim gain 0.84 < 1.0).
- **Result**: `results/experiments/exp53_ar1_6d_gate/exp53_ar1_6d_gate.json`
- **Depends on**: `phase_06_phi_m.pkl` (SHA-pinned, already on disk); `experiments/exp44_F6_spectrum/run.py` (for `_ar_fit` import).
- **Supersedes**: none (new experiment slot).
- **May trigger R9**: if PROMOTE verdict, requires integrity-zone write to append locked scalar (gated behind user approval).

## Execution instruction

```powershell
python C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp53_ar1_6d_gate\run.py
```

Runtime estimate: 3-8 minutes (68 Quran + ~2509 control units × AR(1) OLS fit + 10 000-shuffle permutation test).
