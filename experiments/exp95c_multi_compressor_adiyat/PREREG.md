# exp95c_multi_compressor_adiyat — Pre-registration

**Frozen**: 2026-04-26 (before any run).
**Hypothesis ID**: H35 — Multi-compressor consensus NCD lifts the Adiyat-864 ceiling above 0.999 without violating FPR.
**Origin**: External-AI reviewer feedback 2026-04-26 ("Step 1: phonetic-modulated R12, expected to close 99.07 % → 99.9 %"). The literal phonetic-modulated formulation was already executed as `exp95_phonetic_modulation` (verdict `FAIL_ctrl_stratum_overfpr`). This experiment tests the alternative root cause: **gzip's 32 KB sliding-window has compressibility artifacts that miss subtle long-range repetition changes**, while bz2 (BWT, no fixed window), lzma (~64 MB context), and zstd (training-data-based) have different compressibility profiles. A consensus rule across 4 compressors should catch artifacts that any single one misses.
**Parent experiments**:
- `exp41_gzip_formalised` — gzip-only NCD, ctrl-p95 ≈ 0.0495
- `exp94_adiyat_864` — gzip R12-only flat baseline = 0.990741 (856/864), 8 misses
- `exp95_phonetic_modulation` — bucketed-tau approach FAILED; misses are NOT phonetic-distance-correlated
- `exp95b_local_ncd_adiyat` — window-local NCD alternative (sister experiment, run independently)

## 1. Claim under test

For each Adiyat-864 variant, compute **four parallel NCDs** using independent compressors with different compressibility profiles:

```
NCD_gzip(canon, variant)  — gzip level 9 (32 KB sliding window; byte-equal to exp41)
NCD_bz2(canon, variant)   — bzip2 level 9 (Burrows-Wheeler, no fixed window)
NCD_lzma(canon, variant)  — lzma preset 9 (LZMA2; ~64 MB context)
NCD_zstd(canon, variant)  — zstandard level 9 (training-window; very different model)
```

For each compressor `c ∈ {gzip, bz2, lzma, zstd}` calibrate an independent ctrl-p95 threshold `τ_c` over the same 4 000-edit ctrl null. A variant **fires at consensus rule K** if at least K of 4 compressors flag it (`NCD_c ≥ τ_c`).

**Pre-registered headline**: K = 2 (majority-of-half).

**Three sub-claims**:

- **C1 — K=2 consensus lifts recall above 0.999**: Adiyat-864 recall under K=2 ≥ 0.999.
- **C2 — Ctrl FPR at K=2 is controlled**: empirical ctrl-pool FPR under K=2 ≤ 0.05 + 1e-6. (Independent thresholds give per-compressor FPR ≈ 0.05 each; the K=2 joint FPR depends on between-compressor correlation. If too high, the consensus has bought specificity at the cost of calibration — FAIL.)
- **C3 — At least one alternative compressor lifts recall vs gzip**: among `{gzip, bz2, lzma, zstd}` solo at K=1-equivalent (single-compressor ctrl-p95), at least one shows recall > exp94's gzip baseline 0.990741. (Diagnostic: which compressor moved the needle.)

## 2. Formula (pre-registered, no parameter scan)

For canonical surah `x` and a single-letter-edited variant `x'`:

```
For each c in {gzip, bz2, lzma, zstd}:
    τ_c             = empirical 95th percentile of NCD_c on the
                       same 4 000-edit ctrl-pool (byte-equal to exp94 setup)
    fires_c(x, x')  = (NCD_c(x, x') ≥ τ_c)

DETECT_K(x, x') = (#{c : fires_c(x, x')} ≥ K)

Headline: K = 2.
Reported also: K = 1 (any-of-4), K = 3, K = 4 (all-four).
```

## 3. Compressor settings (frozen)

| Name | Library | Level | Notes |
|---|---|:--:|---|
| `gzip` | `gzip` (stdlib) | 9 | byte-equal to exp41/94 |
| `bz2` | `bz2` (stdlib) | 9 | BWT block size 900 kB |
| `lzma` | `lzma` (stdlib) | preset=9 | LZMA2; default extreme=False |
| `zstd` | `zstandard` 0.25.0 | 9 | no dictionary; default chunk |

If any of these libraries fails to import, the verdict is `FAIL_compressor_unavailable` and the run aborts before producing partial results.

## 4. Evaluation protocol

**Step 1 — Null calibration (4 compressors)**: byte-equal to `exp94` Step 1, except for each ctrl edit compute all 4 NCDs in parallel. Build 4 independent ctrl-p95 thresholds τ_c.

**Step 2 — Adiyat-864 scoring**: enumerate the 864 single-letter substitutions of Surah 100 v1 (byte-equal to exp43/94/95). For each variant compute all 4 NCDs and the per-compressor fire flags.

**Step 3 — Consensus computation**: for K ∈ {1, 2, 3, 4} compute (a) Adiyat recall and (b) ctrl-pool false-positive rate using the same K rule.

**Step 4 — Diagnostic — per-compressor solo recall and lift**: report the recall of each compressor independently at K=1-equivalent. If `recall_lzma > recall_gzip`, that's the actionable finding.

**Step 5 — Pairwise correlation audit**: report the Spearman rank correlation of NCDs across the ctrl null between each compressor pair. High correlation (ρ > 0.95) means the compressors are not independent and K=2 buys little; low correlation (ρ < 0.7) means consensus has real signal.

**Step 6 — Self-check**: protected files unchanged at start vs end (via `_lib.self_check_begin/end`).

## 5. Pre-registered verdicts (evaluated in order)

| Code | Condition |
|---|---|
| `FAIL_exp94_baseline_missing` | `results/experiments/exp94_adiyat_864/exp94_adiyat_864.json` not on disk |
| `FAIL_compressor_unavailable` | any of `{gzip, bz2, lzma, zstd}` import fails |
| `FAIL_protocol_drift` | gzip-only recall (this experiment's reproduction of exp94) deviates from 0.990741 by more than 0.001 |
| `FAIL_consensus_overfpr` | K=2 ctrl-pool FPR > 0.05 + 1e-6 |
| `FAIL_consensus_no_lift` | K=2 recall ≤ exp94 baseline 0.990741 |
| `PARTIAL_consensus_lifts_below_999` | K=2 recall > baseline AND K=2 recall < 0.999 |
| `PASS_consensus_999` | K=2 recall ≥ 0.999 AND K=2 FPR ≤ 0.05 |
| `PASS_consensus_100` | K=2 recall == 1.0 AND K=2 FPR ≤ 0.05 |

## 6. Honesty clauses

- **HC1 — K is frozen at 2 for the headline verdict**. Reporting K=1, 3, 4 is informational; the verdict is based on K=2 alone.
- **HC2 — Per-compressor thresholds are independent ctrl-p95 quantiles**. No threshold optimisation / no joint-distribution model. The "consensus" is purely combinatorial.
- **HC3 — Compressor settings are frozen at level 9 / preset 9 across all 4**. No level scan. Different levels would constitute different experiments.
- **HC4 — Adiyat-864 is a single-surah benchmark**. A PASS does NOT generalise to other surahs.
- **HC5 — Honest negative is acceptable**. If K=2 does not lift above 0.991, the verdict is `FAIL_consensus_no_lift` and the negative is published.
- **HC6 — Cross-compressor correlation is reported as a diagnostic, not a gate**. Even if all four compressors are highly correlated (ρ > 0.95), the verdict is determined by K=2 recall and FPR; the correlation is for interpretation only.

## 7. Locks not touched

No modification to any file under `results/integrity/`, `results/checkpoints/`, or `notebooks/ultimate/`. All new scalars tagged `(v7.10 cand.)`. The `exp94`, `exp95`, `exp95b`, and `exp41` receipts are read-only.

## 8. Frozen constants

```python
SEED = 42
N_PERT_PER_UNIT = 20
CTRL_N_UNITS = 200
GZIP_LEVEL = 9
BZ2_LEVEL = 9
LZMA_PRESET = 9
ZSTD_LEVEL = 9
FPR_TARGET = 0.05
BAND_A_LO, BAND_A_HI = 15, 100
ADIYAT_LABEL = "Q:100"
EXPECTED_N_VARIANTS = 864
HEADLINE_K = 2
PROTOCOL_DRIFT_TOL = 0.001
```

## 9. Provenance

- Reads (integrity-checked): `results/checkpoints/phase_06_phi_m.pkl`
- Reads (receipt): `results/experiments/exp94_adiyat_864/exp94_adiyat_864.json`
- Reads (receipt): `results/experiments/exp95_phonetic_modulation/exp95_phonetic_modulation.json` (cross-reference for negative-result sister experiment)
- Writes only: `results/experiments/exp95c_multi_compressor_adiyat/exp95c_multi_compressor_adiyat.json`
- Paper hook: candidate `docs/PAPER.md` §4.25 (Adiyat 864) footnote on multi-compressor consensus.

---

*Pre-registered 2026-04-26 night. Prereg hash is computed at run-time and stored in the output JSON under `prereg_hash`. Authored in response to external-AI reviewer feedback documented in `docs/REVIEWER_FEEDBACK_2026-04-26.md`.*
