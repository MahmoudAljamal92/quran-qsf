# exp28 — Scale-invariant Markov-1 law audit (4-scale unifier)

**Status**: scaffolded 2026-04-20, runnable end-to-end.
**Outputs**: `results/experiments/exp28_scale_invariant_law/exp28_scale_invariant_law.json`.

## Why this exists

The 2026-04-20 external review proposed that the Quran might exhibit
**bigram / Markov-1 sufficiency at every scale simultaneously**:

| Scale | Metric | Locked result | Source |
|---|---|---|---|
| L0 char (intra-word) | H_char H3/H2 | **NEW — exp27** | `results/experiments/exp27_hchar_bigram/` |
| L1 root (verse boundary) | root H3/H2 = 0.222, Quran rank 1/6 | locked T11 | `src/extended_tests.py:test_bigram_sufficiency` |
| L1b root (Markov order) | H2/H1 d = +0.42, p_less ≈ 1.0 | locked T28 | `src/extended_tests3.py:test_markov_order_sufficiency` |
| L2 verse-length coherence | F6 lag-1 d = +0.83, p ≈ 4·10⁻¹² | locked T32 | `src/extended_tests4.py::F6` |
| L3 surah-order path | z ≈ −3.96, 0 / 2000 perms beat canon | locked T8 | `src/extended_tests.py:test_path_optimality` |

If all four are Quran-extremal, that is a **Zipf-class universal
law**. This experiment's job is to audit that claim honestly.

## Protocol

- Zero new computation of the underlying tests — everything is read
  from `results/CLEAN_PIPELINE_REPORT.json` (locked, SHA-256-pinned by
  `self_check`) and `results/experiments/exp27_hchar_bigram/
  exp27_hchar_bigram.json` (exp27 output).
- One dict per scale with identical structure
  `(scale, metric, direction, law_supported, source)`.
- `law_supported` is computed from each scale's own sign convention:
  the feedback's proposed effect direction (Quran more Markov-1) AND
  a p-value criterion (p < 0.05) AND, where applicable, Quran rank 1.
- Verdict rubric:
  - 5/5 -> `SCALE_INVARIANT_LAW_HOLDS`
  - 3-4/5 -> `PARTIAL_LAW_HOLDS_AT_MAJORITY_SCALES`
  - 2/5 -> `LAW_HOLDS_AT_MINORITY_SCALES`
  - 0-1/5 -> `LAW_DOES_NOT_HOLD`

## Secondary analysis — char-root GAP

Even when the uniform law fails, the *ratio of Markov-1 sufficiency
across scales* may itself be a Quran signature. Define:

    gap(corpus) = H_char_3/H_char_2 (pooled) − H_root_3/H_root_2 (pooled)

A large positive gap = "this corpus is far more Markov-1-organized at
the root level than at the character level." If the Quran ranks **1st**
on this gap, it is a **new scale-dependent fingerprint** that does not
contradict any locked claim. It would still require its own permutation
test + cross-scripture panel before paper promotion.

## How to run

```powershell
python -m experiments.exp27_hchar_bigram.run         # produce L0 input
python -m experiments.exp28_scale_invariant_law.run  # this experiment
```

Expected runtime: < 2 s (pure JSON aggregation).

## Interpretation templates

- **5/5 HOLDS**: draft a new paper §4.NEW titled "Scale-invariant
  Markov-1 sufficiency" with the 4-row table above. Commit to a
  cross-scripture replication before promoting to headline.
- **3-4/5 PARTIAL**: redraft the feedback paragraph: the Quran is
  Markov-1 dominant at the scales that pass, but not uniformly. Each
  passing scale is independently reportable.
- **≤ 2/5 FAILS** (this is the expected outcome given exp27's negative
  character-scale result): write up the honest negative. The R1
  9-channel and Φ_M 5-D already dominate the literature on Quran
  separation; claiming a new universal law on top of them requires
  more than intuition. The char-root GAP analysis provides a
  SECONDARY angle that may still yield a publishable scale-
  DEPENDENT finding.

## Zero-trust audit

Identical protocol to exp27: `self_check_begin/end` snapshots every
protected file (including `CLEAN_PIPELINE_REPORT.json` which this
experiment reads but never writes to) pre and post run, and
`_verify_all.py` at the end of the session confirms no protected SHA
has drifted.
