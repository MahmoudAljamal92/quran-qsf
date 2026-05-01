# exp95d_multi_compressor_robust — pre-registration

**Pre-registration frozen**: 2026-04-26 night
**Status**: scaffolded immediately after exp95c PASS_consensus_100
**Author**: QSF lab (automated agent; hash-locked)
**Parent experiment**: `experiments/exp95c_multi_compressor_adiyat/` (PASS, K=2 recall = 1.000, FPR = 0.0248)

> ⚠ **Honesty clause.** This is a robustness-only experiment. It does **not**
> introduce a new claim. It tests whether the exp95c result generalises across
> (a) random-seed reshuffles of the ctrl-null pool and (b) a different short
> Quranic surah of comparable size. A null result here would force exp95c's
> headline claim to be reframed from "ceiling closed" to "ceiling closed for
> Q:100 only under seed=42."

## 1. Hypothesis

**H36** — The K=2 multi-compressor consensus rule established in exp95c (4
compressors {gzip-9, bz2-9, lzma-preset-9, zstd-9} with per-compressor ctrl-p95
thresholds) closes the Adiyat-style single-letter detection ceiling to recall
≥ 0.999 with consensus-FPR ≤ 0.05 **regardless** of:

- the random seed used for ctrl-null calibration (seed sensitivity), and
- the choice of short Meccan surah (cross-surah generalisation; the corpus label `Q:099` corresponds to al-Zalzalah).

A failure here pre-registers exactly which mechanism breaks: seed drift,
surah-specific structure, or both.

## 2. Parent experiments (read-only)

- `exp94_adiyat_864` — gzip-only baseline 0.9907
- `exp95_phonetic_modulation` — FAIL_ctrl_stratum_overfpr (recall 0.985)
- `exp95b_local_ncd_adiyat` — FAIL_window_overfpr (recall 0.399)
- **`exp95c_multi_compressor_adiyat`** — **PASS_consensus_100** (recall 1.000, FPR 0.0248)

All four pre-registrations are hash-locked. No earlier receipt is rewritten.

## 3. Claims under test

- **C1 (seed-stability)**: Across seed ∈ {42, 137, 2024} on Q:100, K=2 recall
  variance ≤ 0.005 and all three sub-runs achieve K=2 recall ≥ 0.999 with K=2
  ctrl FPR ≤ 0.05.
- **C2 (cross-surah)**: With seed=42, applied to Q:099 al-Zalzalah (similar
  Meccan oath-style, 8 verses, comparable v1 size; the corpus label is
  zero-padded `Q:099`), K=2 recall ≥ 0.999 with K=2 ctrl FPR ≤ 0.05.
- **C3 (no compressor monoculture)**: Across all sub-runs, at least 2 of the 4
  compressors maintain solo recall ≥ 0.95. (Diagnostic; not pass/fail.)

## 4. Protocol

For each sub-run i ∈ {(42, Q:100), (137, Q:100), (2024, Q:100), (42, Q:099)}:

1. Reproduce **exactly** the exp95c protocol — same compressor settings, same
   ctrl-corpus pool, same `_apply_perturbation`, same `_doc_ncd`, same
   `_enumerate_864`, same per-compressor ctrl-p95 thresholding, same K=2
   consensus rule.
2. Substitute only `(SEED, ADIYAT_LABEL)` for the sub-run.
3. Compute: per-compressor τ, ctrl FPR by K, solo recall, consensus recall by
   K, per-position audit, gzip-protocol drift vs. parent baseline.

Sub-run 1 (seed=42, Q:100) is **not re-executed** — the exp95c receipt is
loaded as-is and its sub-receipt block is included verbatim in the aggregator
output. This protects the locked exp95c receipt and ensures the headline
result cannot be silently overwritten.

Sub-runs 2, 3, 4 are executed fresh; their full sub-receipts (per-variant
audit included) are saved alongside the aggregator.

## 5. Pre-registered verdict ladder

Evaluated in **strict order** (first match wins):

1. **`FAIL_protocol_drift_any`** — the **seed=42 Q:100** sub-run shows |gzip
   recall − exp94 baseline| > 0.001. *Bug-fix note (2026-04-26 night):* the
   first run of this experiment incorrectly applied this sentinel to all
   sub-runs, which fires on any seed swap because gzip-solo recall depends on
   the ctrl-null pool. The corrected sentinel applies only to the seed=42
   Q:100 sub-run, where we have a hash-locked expected value from exp94 /
   exp95c. Drifts on other seeds are reported as diagnostic in the receipt
   under `summary.diagnostic_drifts` but do not trigger fail. A regression
   test (re-running with seed=42 Q:100) preserves the sentinel intent.
2. **`FAIL_seed_unstable`** — among Q:100 sub-runs at seeds 42/137/2024:
   max(K=2 recall) − min(K=2 recall) > 0.005, indicating that the exp95c
   recall=1.000 was a single-seed artefact.
3. **`FAIL_seed_overfpr`** — any Q:100 sub-run has K=2 ctrl FPR > 0.05 + 1e-6.
4. **`FAIL_seed_belowfloor`** — any Q:100 sub-run has K=2 recall < 0.999
   (the C1 hard-floor is broken even though variance is small enough).
5. **`PARTIAL_seed_only`** — C1 holds (seed-stable on Q:100, all three
   sub-runs ≥ 0.999) but C2 fails (Q:099 has K=2 recall < 0.999 OR K=2 FPR >
   0.05). Headline claim narrows to "Q:100 specifically."
6. **`PASS_robust`** — C1 ∧ C2 hold. Headline claim widens to: "K=2 consensus
   closes the single-letter detection ceiling on short Meccan surahs across
   independent ctrl-null seeds."

Note: a Q:099 failure produces `PARTIAL_seed_only`, not a fail — the exp95c
result for Q:100 is unaffected. Only a Q:100 failure can override the parent
finding.

## 6. Honesty clauses

- We will not retroactively raise the FPR target above 0.05 to rescue a
  sub-run; if K=2 FPR drifts above 0.05 + 1e-6, the verdict ladder fires.
- A `PARTIAL_seed_only` outcome is **fine** — it just means the universal
  claim narrows, and exp95c is preserved as-is for Q:100 specifically. We do
  not retract exp95c on this basis.
- The 0.005 seed-stability tolerance is set a priori. If max−min lands in
  [0.001, 0.005], the verdict still passes but the headline downstream paper
  text must report the per-seed range, not just the seed=42 number.
- The cross-surah test uses Q:099 al-Zalzalah (chosen for size match and
  stylistic kinship; 8 verses, oath-genre Meccan). It is **not** chosen to
  maximise our chances. Any other short Meccan surah (Q:101, Q:103, Q:104)
  would have been an equally valid alternative; we pre-commit to Q:099 here.

## 7. Locks not touched

- `results_lock.json` — untouched
- `phi_M_v3.json` — untouched
- `phase_*.pkl` checkpoints — untouched (read-only via `_lib.load_phase`)
- All earlier `experiments/exp*/PREREG.md` and receipts — untouched
- `docs/PAPER.md` — untouched until docs propagation phase

## 8. Frozen constants

```
COMPRESSOR_SET     = ("gzip", "bz2", "lzma", "zstd")
GZIP_LEVEL         = 9
BZ2_LEVEL          = 9
LZMA_PRESET        = 9
ZSTD_LEVEL         = 9
N_PERT_PER_UNIT    = 20
CTRL_N_UNITS       = 200
FPR_TARGET         = 0.05
BAND_A             = (15, 100)   # ctrl-pool unit-size band
HEADLINE_K         = 2
PROTOCOL_DRIFT_TOL = 0.001       # gzip vs exp94 baseline
SEED_STABILITY_TOL = 0.005       # max(K=2 recall) − min(K=2 recall) on Q:100
SUBRUNS = [
    {"seed":   42, "label": "Q:100", "source": "exp95c_receipt"},
    {"seed":  137, "label": "Q:100", "source": "fresh"},
    {"seed": 2024, "label": "Q:100", "source": "fresh"},
    {"seed":   42, "label": "Q:099", "source": "fresh"},
]
```

## 9. Provenance

- exp95c receipt: `results/experiments/exp95c_multi_compressor_adiyat/exp95c_multi_compressor_adiyat.json`
- exp94 baseline source (gzip-only ceiling 0.9907): `results/experiments/exp94_adiyat_864/exp94_adiyat_864.json`
- Phase checkpoint loaded read-only: `phase_06_phi_m.pkl`
- Output directory: `results/experiments/exp95d_multi_compressor_robust/`
- Code: `experiments/exp95d_multi_compressor_robust/run.py`
