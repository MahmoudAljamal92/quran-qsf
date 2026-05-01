# exp103_cross_compressor_gamma — Pre-registration

**Frozen**: 2026-04-22 (before any run).
**Hypothesis ID**: H35a — The Quran-indicator γ in the log-linear NCD regression is a universal quantity across compression-algorithm families, not a gzip artefact.

> *Note (added 2026-04-26 night under v7.9-cand patch G doc-hygiene)*: this experiment was originally registered as **H35** on 2026-04-22. The label H35 was later (2026-04-26) re-used by `exp95c_multi_compressor_adiyat` for a *different* hypothesis (multi-compressor consensus closes the Adiyat-864 ceiling). To resolve the collision, this experiment is relabelled **H35a** (γ-universality variant) and `HYPOTHESES_AND_TESTS.md` row 39 retains H35 for the multi-compressor consensus claim. **The measured numerics, verdict (`FAIL_not_universal`), and audit trail are unchanged.** See `RETRACTIONS_REGISTRY.md::R51` and `AUDIT_MEMO_2026-04-26_RISK_VECTORS.md` §4.
**Parent experiment**: `exp41_gzip_formalised` + `length_audit.py` (γ_gzip = +0.0716, 95 % CI [+0.066, +0.078]).
**Programme context**: this is the **empirical falsifier for Theorem 1** of `docs/PREREG_GAMMA_KOLMOGOROV.md`. If this experiment fails its PASS gate, Theorem 1 (finite-length NCD ≈ NCD_K bound) is NOT universal across compressors, and the Kolmogorov-derivation programme must be scoped to "gzip-specific" or abandoned. If this experiment passes, the programme's mathematician-recruitment phase is justified.

## 1. Claim under test

Let `Z` range over four general-purpose lossless compressors:
- **gzip** (LZ77 + Huffman, 32 KB window) — Python stdlib
- **bzip2** (BWT + MTF + Huffman) — Python stdlib
- **zstd --ultra -22** (FSE + finite-state entropy) — `zstandard` package (optional)
- **brotli** (static dictionary + Huffman) — `brotli` package (optional)

Define `γ_Z` as the Quran-indicator coefficient in the log-linear regression

```
log NCD_Z = α_Z + β_Z · log(n_letters) + γ_Z · I(group = Quran) + ε
```

evaluated byte-equal to `exp41_gzip_formalised/length_audit.py` (same 68 Band-A Quran + 200 matched-length Band-A Arabic-ctrl units, same internal-edit perturbation policy, N_PERT = 20, same 28-letter consonantal rasm, same `compresslevel=9` where applicable).

**The H35 claim** is that `γ_Z` is approximately **invariant** across the four compressors, quantified by the coefficient of variation

```
CV_γ = σ(γ_Z) / mean(γ_Z)
```

over the set of available compressors.

## 2. Formula (pre-registered)

For each available compressor `Z`:

```
Z_Z(s)                   = len(compress_Z(s.encode("utf-8"), maximum_level))
NCD_Z(a, b)              = (Z_Z(a ⧺ b) − min(Z_Z(a), Z_Z(b))) / max(Z_Z(a), Z_Z(b))
γ_Z                      = coef of I(Quran) in OLS fit of
                           log NCD_Z(canon, edit) ~ log(n_letters_canon) + I(Quran)
γ_Z_se                   = OLS standard error of γ_Z
γ_Z_CI95                 = γ_Z ± 1.96 · γ_Z_se
```

Then across compressors:

```
γ_mean  = mean over available Z of γ_Z
γ_sd    = std  over available Z of γ_Z   (ddof = 0, since the 4 compressors are the whole population of interest, not a sample)
CV_γ    = γ_sd / γ_mean
```

## 3. Evaluation protocol

**Step 1 — Probe available compressors**. Try to import `gzip`, `bz2`, `zstandard`, `brotli`. Log which are available. Require ≥ 2 to proceed.

**Step 2 — Reproduce gzip baseline first**. Compute `γ_gzip`. Sanity-check it against the `exp41_gzip_formalised/length_audit.json` locked value (`+0.0716`) within ± 0.01 tolerance. If the reproduction deviates by more than 0.01, the experiment aborts with `FAIL_gzip_reproduction` — the corpus or code has drifted and any new-compressor comparison is meaningless.

**Step 3 — Compute γ_Z for each remaining compressor** using the same 5 360 perturbations (1 360 Q + 4 000 ctrl), same seed (42), same perturbation policy. The ONLY thing that changes is the compressor function.

**Step 4 — Cross-compressor statistics**. Compute `γ_mean`, `γ_sd`, `CV_γ`.

**Step 5 — Per-compressor CI exclusion check**. For each available Z, report whether its 95 % CI on γ_Z excludes zero. A single compressor's CI including zero is a per-compressor failure (signal absent under that algorithm family).

**Step 6 — Verdict dispatch**.

## 4. Pre-registered verdicts (evaluated in order)

| Code | Condition |
|---|---|
| `FAIL_n_compressors` | fewer than 2 compressors importable |
| `FAIL_gzip_reproduction` | `|γ_gzip_measured − 0.0716|` > 0.01 vs `exp41` locked value |
| `FAIL_any_compressor_null` | any available Z has γ_Z 95 % CI including zero |
| `FAIL_not_universal` | `CV_γ > 0.20` — γ is not universal; Theorem 1 must be restated per-compressor or programme aborts |
| `PARTIAL_weakly_universal` | `0.10 < CV_γ ≤ 0.20` — directional agreement holds but the constant is compressor-dependent |
| `PASS_universal` | `CV_γ ≤ 0.10` AND all available Z have γ_Z > 0 at p ≤ 0.05 |

## 5. Honesty clauses

- **HC1 — Compressors are not drawn from a random population**. The four compressors span two distinct algorithm families (LZ77-derived: gzip, brotli, zstd in dictionary mode; BWT: bzip2). Using `ddof = 0` in `γ_sd` reflects that we're summarising a finite fixed population, not estimating a population variance.
- **HC2 — "compresslevel" is not the same across algorithms**. gzip/bzip2 use `compresslevel = 9`; zstd uses `level = 22` (ultra); brotli uses `quality = 11`. Each is the algorithm's published "maximum compression" setting. The goal is to test structural-signal universality across algorithms at their tightest, not to tune a joint hyperparameter.
- **HC3 — CV_γ threshold of 0.20 is a calibration choice, not a theorem**. This threshold was chosen pre-registered to be lenient; a professional algorithmic-information-theorist may prefer a tighter gate. The gate here is "mathematician-recruitment threshold", not "Theorem-1 proof threshold".
- **HC4 — Single-letter edit only**. This experiment does NOT test multi-letter or word-level edits. Generalisation to `exp45_two_letter_746k` is a downstream replication, not part of H35.
- **HC5 — Does not falsify `exp55 LENGTH_DRIVEN`**. The `exp55` length-stratified pre-reg test on gzip specifically found LENGTH_DRIVEN on the sign-test metric (the γ regression coefficient remained highly significant). This experiment reports γ regression coefficients only; it does not re-run the decile sign-test.

## 6. Locks not touched

No modification to any file under `results/integrity/`, `results/checkpoints/`, or `notebooks/ultimate/`. Writes ONLY under `results/experiments/exp103_cross_compressor_gamma/`.

## 7. Frozen constants

```python
SEED = 42
N_PERT_PER_UNIT = 20
CTRL_N_UNITS = 200
BAND_A_LO, BAND_A_HI = 15, 100
GZIP_LEVEL = 9
BZIP2_LEVEL = 9
ZSTD_LEVEL = 22
BROTLI_QUALITY = 11

GAMMA_LOCKED_GZIP_EXP41 = 0.0716
GAMMA_REPRODUCTION_TOL = 0.01

CV_GAMMA_PASS = 0.10
CV_GAMMA_PARTIAL = 0.20

MIN_COMPRESSORS = 2
```

## 8. Provenance

- Reads (integrity-checked): `results/checkpoints/phase_06_phi_m.pkl`
- Reads (receipt, locked reference): `results/experiments/exp41_gzip_formalised/length_audit.json` (or `exp41_gzip_formalised.json`) — used only for the γ_gzip reproduction sanity check
- Writes only: `results/experiments/exp103_cross_compressor_gamma/exp103_cross_compressor_gamma.json`
- Paper hook: Theorem-1 falsifier row in `docs/PREREG_GAMMA_KOLMOGOROV.md` §3.1

## 9. Decision outcomes for the broader programme

- **PASS_universal** → Theorem 1 is worth formal proof work. Proceed to collaborator recruitment (Kolmogorov-tier or MDL-tier) per `docs/PREREG_GAMMA_KOLMOGOROV.md` §5.
- **PARTIAL_weakly_universal** → Theorem 1 is gzip-biased but the γ direction is robust. Re-scope the programme to "γ is a positive constant for all LZ-family compressors" — a weaker but still publishable claim. Proceed with a weaker collaborator tier (MDL statistician) rather than a full Kolmogorov-theorist.
- **FAIL_not_universal** → γ is a gzip-specific artefact. **Abort the Kolmogorov-derivation programme**. The γ = +0.0716 headline survives (it's still a reproducible empirical scalar for gzip) but is re-framed in the paper as a "compressor-calibrated edit-detection parameter" rather than a candidate information-theoretic constant.
- **FAIL_any_compressor_null** → at least one compression family does not see the Quran signal. This is a **negative result** for universality but also scientifically interesting — it suggests the signal lives in LZ77-specific dictionary-growth patterns rather than general Kolmogorov complexity. The programme reframes as *"identify which compression mechanism captures γ; use that mechanism's theory for Theorem 1"*.

---

*Pre-registered 2026-04-22 late. Prereg hash is computed at run-time and stored in the output JSON under `prereg_hash`.*
