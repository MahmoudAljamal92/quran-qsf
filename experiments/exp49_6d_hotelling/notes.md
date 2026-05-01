# exp49 -- 6-D Hotelling T^2 gate for exp48 verse-graph promotion

**Status**: scaffolded 2026-04-21, pre-registered, runnable end-to-end.
**Outputs**: `results/experiments/exp49_6d_hotelling/exp49_6d_hotelling.json`.
**Dependencies**: `networkx>=3.0`, `scipy`, optional `mpmath` (for
high-precision F-tail p when scipy underflows).

## Why this exists

`exp48_verse_graph_topology` promoted n_communities as the strongest
surviving verse-graph metric (d = +0.937, MW p = 1.2e-12, Quran rank
1/6). The pre-registered §"6-D Hotelling rule" in
`exp48/notes.md` guards against redundancy: a metric that duplicates
information already in the 5-D Phi_M cannot pass a dimension-penalty
threshold. This script is that gate.

## Pre-registration (frozen before any run)

### Protocol

1. Load `X_QURAN` (68×5) and `X_CTRL_POOL` (2509×5) from the SHA-
   pinned `phase_06_phi_m.pkl` state.
2. For every Band-A unit (`15 ≤ n_verses ≤ 100`) in Quran + the
   6 Arabic controls (`poetry_jahili, poetry_islami, poetry_abbasi,
   ksucca, arabic_bible, hindawi`), compute `n_communities` on the
   same verse-transition graph `exp48` builds:
   - nodes = verse indices,
   - edges (i ↔ i+1) weighted `0.5·EL_match + 0.5·length_ratio`,
   - `nx.community.greedy_modularity_communities` on the
     undirected view.
   Iteration order exactly follows `_build.py::_X_for` (the order
   records appear in `FEATS[name]` after the Band-A filter).
3. Assert that the first 5 columns of the 6-D matrices are byte-
   identical to `phase_06 X_QURAN / X_CTRL_POOL`. A drift raises
   `AssertionError` and the run aborts.
4. Compute the two-sample Hotelling T^2 with pooled covariance and
   ridge `lambda = 1e-6 * I_6`. This matches `_build.py` Cell 29
   and `exp01_ftail` exactly.
5. Report F-statistic, df, analytic F-tail p, high-precision fallback
   via mpmath when scipy underflows.

### Decision rule (pre-registered)

- `T2_6D >= 3557.34 * 6/5 = 4268.8`  ⇒  `PROMOTE_6TH_CHANNEL`
- otherwise                         ⇒  `SIGNIFICANT_BUT_REDUNDANT`

## How to run

```powershell
pip install networkx>=3.0 scipy
python -X utf8 -u experiments\exp49_6d_hotelling\run.py
```

Expected runtime 2–5 min. Only one graph metric per unit (vs 6 in
exp48), so ~6× faster.

## Interpretation

- `PROMOTE_6TH_CHANNEL` ⇒ n_communities is the 6th independent channel.
  Update the Phi_M definition and the paper §3.3 table.
- `SIGNIFICANT_BUT_REDUNDANT` ⇒ exp48 stays as a supplementary finding.
  Do NOT promote. The dimension penalty is working as intended.

## References

- Pre-reg doc: `experiments/exp48_verse_graph_topology/notes.md`
  §"6-D Hotelling rule".
- 5-D baseline: `results/experiments/exp01_ftail/exp01_ftail.json`
  (T2 = 3557.3394545...).
- Locked Phase-7 computation: `notebooks/ultimate/_build.py` Cell 29.
