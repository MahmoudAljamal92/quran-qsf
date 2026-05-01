# exp88 — LC3-70 Fisher-Optimal Linear Boundary (figure + receipt)

**Purpose**: Re-emit the LC3-70 boundary as a single publishable figure (Fig. 7 of PAPER.md §4.35). Performs **zero new computation**. Reads three already-locked JSONs:

- `results/experiments/exp60_lc3_parsimony_theorem/exp60_lc3_parsimony_theorem.json`
- `results/experiments/exp70_decision_boundary/exp70_decision_boundary.json`
- `results/experiments/exp74_eigenvalue_spectrum/exp74_subspace_test.json`

Also needs the (T, EL) feature coordinates. These are in the standard pipeline checkpoint:

- `results/checkpoints/phase_06_phi_m.pkl` (loaded via `src.features`)

**Outputs**:

- `fig7_lc3_70_pareto.png` — scatter + boundary + margin lines (Fig. 7)
- `fig7_data.csv` — 2 577-row coordinate dump (for reproducibility)
- `receipt.json` — SHA-256 of the three source JSONs + the checkpoint pickle + output files

**Does not write to**: any file outside this directory. No `results_lock.json`, no canonical doc, no locked experiment JSON.

**Run**:

```powershell
python experiments/exp88_lc3_70_u/run.py
```

Runtime: ~ 5 seconds (no numerics beyond a scatter plot).
