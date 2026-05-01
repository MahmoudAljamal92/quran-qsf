# exp48 — Verse-graph topology (port of DEEPSCAN Gem #4 / "word-graph modularity")

**Status**: scaffolded 2026-04-21, pre-registered, runnable end-to-end.
**Outputs**: `results/experiments/exp48_verse_graph_topology/exp48_verse_graph_topology.json`.
**Dependencies**: requires `networkx>=3.0` (added to `requirements.txt`).

## Why this exists

`archive/pipeline2_backup/qsf_new_anomaly_tests.py` TEST 3 (lines 350-470)
reported on a legacy Pipeline-2 checkpoint that Quran per-surah
verse-transition graphs show:

- modularity (greedy-community) = 0.645, rank 1/10
- n_communities = 7.02, rank 1/10
- bc_cv (betweenness-centrality CV) = 0.52, lowest across corpora
- overall Cohen d = +0.47, MW p = 5.2·10⁻⁷

The current `ultimate2_pipeline.run_R6` (writing to
`results/experiments/exp14_R6_word_graph_modularity/`) uses a **different
graph** (word-as-node, custom one-level Louvain, one-graph-per-corpus,
modularity only) and scores 0.143 vs the 0.50 uniform-null target. R6
does **not** reproduce the gem.

This experiment re-implements the original archive method on the current
SHA-locked clean-data corpora. Three outcomes are possible:

1. Replicates with d > 0.3 on ≥ 3 of 6 metrics → candidate 6th independent
   channel. Next step: 6-D Hotelling T².
2. Fires but is redundant with the 5-D Φ_M (6-D T² not ≥ 5-D × 6/5) →
   significant-but-not-new; report as supplementary.
3. Does not replicate → clean-data null. Important negative result; add
   to `docs/RANKED_FINDINGS.md §5` retractions.

## Pre-registration (frozen 2026-04-21, before any run)

### Protocol

For every unit `u` in every corpus in `load_phase("phase_06_phi_m")["state"]["CORPORA"]`:

1. If `len(u.verses) < 5` → skip (graph metrics unreliable).
2. Build directed graph `G`: nodes = verse indices, edges = (i, i+1) AND
   (i+1, i) with weight `0.5 * el_match(v_i, v_{i+1}) + 0.5 * (1 - |w_i - w_{i+1}| / max(w_i, w_{i+1}))`
   where `w` = word count, `el_match` = 1 iff last letter matches.
3. Convert to undirected and compute six metrics:
   - `clustering`            : `nx.average_clustering(weight="weight")`
   - `avg_path_norm`         : `nx.average_shortest_path_length / n_verses`
     (on largest connected component if disconnected)
   - `modularity`            : `nx.community.modularity` over
     `greedy_modularity_communities`
   - `n_communities`         : `len(greedy_modularity_communities)`
   - `bc_cv`                 : `std(bc) / max(mean(bc), 1e-10)` on
     `nx.betweenness_centrality(weight="weight")`
   - `small_world_sigma`     : `(C / C_rand) * (L_rand / L)` with
     `watts_strogatz_graph(n, 2, 0.5, seed=42)` as the random reference.

### Aggregation

Per-corpus: arithmetic mean across units.

### Decision rule (pre-registered)

For each metric, compute Cohen d and two-sided Mann-Whitney p between
Quran units and pooled Arabic control units (poetry_abbasi, poetry_jahili,
hindawi, ksucca, arabic_bible — hadith quarantined to match v7.4 policy).

**Promotion rule**:

- `FIRE`  = `|d| > 0.3  AND  p < 0.01` on a single metric.
- `VERDICT = "PROMOTE"`     iff `n_fires >= 3 of 6`.
- `VERDICT = "NOT PROMOTED"` otherwise.

### 6-D Hotelling rule (separate follow-up, also pre-registered here)

If `VERDICT = "PROMOTE"`, pick the metric with the largest `|d|`. Add it
to the 5-D Φ_M feature vector on Band-A matched data and compute the 6-D
Hotelling T² with the same Σ-regularisation (1·10⁻⁶ · I) as in §3.3 of
the paper.

- **Promote to 6th channel** iff `T²_6D >= 5-D T² × 6/5 = 3 557 × 1.2 = 4 269`.
- Otherwise → `"SIGNIFICANT BUT REDUNDANT"`, do not promote.

## How to run

```powershell
pip install networkx>=3.0
python -X utf8 -u experiments\exp48_verse_graph_topology\run.py
```

Expected runtime: 5–15 min (2 577 units × 6 graph metrics;
`greedy_modularity_communities` dominates).

## Why this pre-registration matters

The original d = 0.47 was discovered post-hoc on a Pipeline-2 checkpoint
that was later shown to have contaminated controls (the April-2026
audit). On clean data the result may not replicate. Locking the decision
rule here rules out cherry-picking a metric that happened to fire.

## Interpretation

- All ≥ 3 metrics fire → fully replicates gem. Proceed to 6-D Hotelling.
- 1-2 metrics fire with |d| > 0.3 but < 3 of 6 → partial replication;
  report as SUGGESTIVE, keep in sandbox.
- 0 metrics fire → gem did not survive clean-data audit; log as a new
  retraction in `docs/RANKED_FINDINGS.md §5` and update row 33 strength
  to 0.

## References

- Original: `archive/pipeline2_backup/qsf_new_anomaly_tests.py` TEST 3.
- Failed current implementation: `experiments/ultimate2_pipeline.py::run_R6`.
- Ranked in: `docs/RANKED_FINDINGS.md` row 33 (Gem #3, strength 57 %).
- DEEPSCAN reference: `docs/DEEPSCAN_ULTIMATE_FINDINGS.md` §3.1 GEM 4.
