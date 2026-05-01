# exp22 — (T, EL) two-feature classifier

**Status**: scaffolded 2026-04-20, runnable end-to-end.
**Outputs**: `results/experiments/exp22_TxEL_classifier/exp22_TxEL_classifier.json`.

## Why this exists

D09 (5-D classifier AUC = 0.998, nested 5-fold) uses all five features:
EL, VL_CV, CN, H_cond, T. The (T, EL) pair carries the two
information-theoretic quantities that depend **least** on external
resources: T is a pure entropy difference, EL is a terminal-letter rate.
Neither uses CamelTools or a hand-curated ARABIC_CONN stopword set.

If the pair alone achieves AUC ≥ 0.97, we have a Zipf-level parsimony
win: two scalars, no root analyser, no stopword list — a dramatically
more reproducible headline than the full 5-D.

## Protocol

- Features: `(T, EL)` from `src.features.features_5d(...)`
- Band A [15, 200] only (same gate as D09)
- StratifiedKFold(5), per-fold StandardScaler (no leakage),
  LogisticRegression
- Seed 42; report AUC per fold, mean ± std
- Compare to D09 = 0.998 locked

## How to run

```powershell
python -m experiments.exp22_TxEL_classifier.run
```

Expected runtime: < 30 s. Self-check at the end.

## Interpretation

- **AUC ≥ 0.97** → add a new §4.16 paragraph to `docs/PAPER.md`
  presenting `(T, EL)` as the parsimonious alternative; the full 5-D
  stays as the headline but gains a "minimal sufficient feature set"
  sibling result.
- **0.90 ≤ AUC < 0.97** → report as SUPPLEMENTARY (two features
  dominate but do not replace the full 5-D).
- **AUC < 0.90** → the full 5-D machinery is required; report as
  negative finding ("(T, EL) alone is insufficient").
