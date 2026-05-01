# exp24 — F6 extension to lag-k autocorrelation

**Status**: scaffolded 2026-04-20, runnable end-to-end.
**Outputs**: `results/experiments/exp24_F6_autocorr/exp24_F6_autocorr.json`.

## Why this exists

The locked F6 finding is lag-1 only: Spearman ρ(|v_i|, |v_{i+1}|) is
higher in the Quran than in Arabic controls
(d ≈ +0.877, MW p ≈ 1.4·10⁻¹¹;
`archive/audits/ADIYAT_BREAKTHROUGH_AUDIT_2026-04-20.md`).

External review (2026-04-20) asked whether the effect persists at lag-2,
lag-3, etc. A multi-step autocorrelation would unify F6 with T12
bigram-sufficiency (Markov-2 structure is enough for the Quran).

## Protocol

- Per Band-A Arabic unit: `lens[i] = word_count(verse_i)`.
- For k ∈ {1, 2, 3, 4, 5}: compute Spearman ρ(lens[:-k], lens[k:]).
- Per-lag Cohen d of Quran distribution vs pooled Arabic control pool
  (hadith quarantined).
- Per-lag one-sided Mann-Whitney p.

## How to run

```powershell
python -m experiments.exp24_F6_autocorr.run
```

Expected runtime: < 30 s.

## Interpretation

- **lag-1 d ≈ 0.877** → reproduction of locked F6 (sanity check).
- **lag-2 d > 0.5 AND lag-3 d > 0.3 with p < 0.001** → multi-step
  coherence confirmed; add to `docs/PAPER.md` §4.17 as strengthened F6,
  link to T12 as unification.
- **lag-2 already drops to noise** → F6 is a one-step phenomenon
  (still valid, but does not unify with T12).
