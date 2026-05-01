# exp51 -- exp48 sensitivity: poetry_islami added to the control pool

**Status**: scaffolded 2026-04-21, pre-registered, runnable end-to-end.
**Outputs**: `results/experiments/exp51_exp48_sensitivity_islami/exp51_exp48_sensitivity_islami.json`.
**Dependencies**: inherits `exp48_verse_graph_topology` (same
networkx graph code).

## Why this exists

The exp48 pre-registration set

```python
CONTROL_CORPORA = {
    "poetry_abbasi", "poetry_jahili", "hindawi", "ksucca", "arabic_bible",
}
```

omitted `poetry_islami`, which `_build.py::Cell 22` treats as a
first-class Arabic control (`ARABIC_CTRL_POOL`). The exp48 headline
result (n_communities d=+0.937, n_fires=4, verdict=PROMOTE) is the
**locked, pre-registered finding** and is not changed by this
experiment.

This is a transparency sensitivity appendix: it quantifies how much
the headline would have moved had the pre-reg been complete.

## Pre-registration (frozen before any run)

### Protocol

1. Load `phase_06_phi_m.CORPORA` (same SHA-pinned source exp48 uses).
2. Recompute all six per-unit graph metrics using `exp48._unit_metrics`
   (bit-exact import; no re-implementation).
3. Compute Quran-vs-pooled Cohen d + Mann-Whitney p under TWO pools:
   - `EXP48_PREREG_POOL` (sanity check — must reproduce exp48 exactly).
   - `EXTENDED_POOL = EXP48_PREREG_POOL ∪ {poetry_islami}`.
4. Apply exp48's frozen FIRE / PROMOTE rule unchanged.

### Decision rule (pre-registered)

Let

- `V_ext` = verdict under `EXTENDED_POOL`,
- `Δd`    = `strongest_d_ext − 0.937` (exp48 headline d).

Then

- `STABLE`   iff `V_ext == PROMOTE` **and** `|Δd| < 0.30`.
- `FRAGILE`  otherwise (paper **must** report the softening / tightening).

`|Δd| < 0.30` is a generous band: `n_communities` means change by
~0.5 units per corpus, so a 0.30-d drift would correspond to almost
the entire spread of the control pool.

## How to run

```powershell
python -X utf8 -u experiments\exp51_exp48_sensitivity_islami\run.py
```

Expected runtime 5–15 min (same as exp48; no optimisation attempted).

## Interpretation

- `STABLE` ⇒ the exp48 headline is robust to the corpus-inclusion
  accident; we simply disclose the correction in a footnote.
- `FRAGILE` ⇒ the exp48 headline *may* need softening (d moved
  ≥ 0.30) or tightening (d moved ≥ 0.30 in the favourable direction).
  Either way the paper must disclose the delta and re-discuss the
  promotion decision honestly.

## References

- Parent experiment: `experiments/exp48_verse_graph_topology/`.
- exp48 locked result:
  `results/experiments/exp48_verse_graph_topology/exp48_verse_graph_topology.json`.
- Authoritative Arabic control pool: `notebooks/ultimate/_build.py`
  Cell 22 (`ARABIC_CTRL_POOL`).
