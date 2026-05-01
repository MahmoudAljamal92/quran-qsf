# exp89_lc3_ablation

Pre-registered single-feature ablation of the `LC3-70-U` (T, EL) sufficiency claim — closes `RANKED_FINDINGS.md §3 row 3` Path-to-100% item (c).

## What it tests

Three linear-SVM fits on the Band-A 68 Q + 2 509 Arabic-ctrl pool:

1. **T only** — is T alone a ≥ 95 %-AUC classifier?
2. **EL only** — is EL alone a ≥ 95 %-AUC classifier?
3. **(T, EL) joint** — does the pair clear ≥ 99 % AUC (and reproduce `exp70`'s 0.9975 as a sanity check)?

## Pre-reg rule (frozen in `PREREG.md`)

| Verdict | Condition |
|---|---|
| `PASS` | `AUC_T < 0.95` AND `AUC_EL < 0.95` AND `AUC_TEL ≥ 0.99` |
| `FAIL_T_dominates` | `AUC_T ≥ 0.95` |
| `FAIL_EL_dominates` | `AUC_EL ≥ 0.95` |
| `FAIL_joint_weak` | `AUC_TEL < 0.99` |
| `FAIL_sanity_exp70_drift` | `|AUC_TEL − 0.9975| > 0.001` |
| `MIXED` | any other combination (should not occur) |

## How to reproduce

```powershell
python experiments/exp89_lc3_ablation/run.py
```

Runtime ≈ 30 s (linear-SVM fit × 3 + 1 000 bootstrap resamples × 3).

## Outputs

- `results/experiments/exp89_lc3_ablation/exp89_lc3_ablation.json` — all three AUCs, bootstrap 95 % CIs, sanity check, verdict string.
- Stdout — human-readable verdict block.

## Methodology fingerprint

Byte-identical to `exp70_decision_boundary/run.py` SVM config (`kernel="linear"`, `C=1.0`, `random_state=42`). The `TEL_joint` AUC reproduces `exp70`'s 0.9975 to within ±0.001 by construction; drift invalidates the run.

## Stakes

- `PASS` → `LC3-70-U` strengthens; ablation item (c) closed; row-3 strength 92→93 %.
- Any `FAIL_*_dominates` → sufficiency collapses to 1-D (different but stronger theorem).
- `FAIL_sanity` / `FAIL_joint_weak` → pipeline bug; no scientific result.

See `PREREG.md` for the full commitment and rationale.
