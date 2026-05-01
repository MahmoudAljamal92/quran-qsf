# exp95f_short_envelope_replication — Pre-registration

**Hypothesis ID**: H39
**Status**: pre-registered, frozen 2026-04-26 night (Asia/Riyadh), **before opening the SHORT-scope receipt of `exp95e_full_114_consensus_universal`**.
**Patch context**: v7.9-cand patch G post-V1 — pre-registered replication of the post-hoc envelope observation surfaced by the V1-scope receipt of `exp95e_full_114_consensus_universal`.
**Supersedes**: nothing. Sits alongside `exp95e_full_114_consensus_universal` (H37, falsified at V1 scope; receipt at `results/experiments/exp95e_full_114_consensus_universal/v1/`).

---

## 0. Why this exists (1 paragraph)

The V1-scope run of `exp95e_full_114_consensus_universal` (2026-04-26 night) fired pre-registered verdict `FAIL_per_surah_floor`. Inspecting the per-surah K = 2 recall as a function of surah length surfaced a **post-hoc** mechanistic pattern: across all 114 surahs, `log10(total_letters_28) → per-surah K=2 recall` Pearson r = −0.85 (Spearman ρ = −0.85), with a sharp phase boundary in `total_letters_28 ∈ [188, 873]`. Because the pattern was discovered on the V1 receipt itself, it **cannot be reported as a finding** without an independent test on a different perturbation set. The `exp95e` SHORT-scope re-run (first 3 verses × 27 substitutes × 114 surahs, ≈ 355 K variants) is in flight and writes to `results/experiments/exp95e_full_114_consensus_universal/short/`. **This document locks H39's substantive claim and decision rules before the SHORT receipt is opened.**

---

## 1. Hypothesis (one paragraph)

**H39 (envelope replication)**: Under K = 2 multi-compressor consensus across {gzip-9, bz2-9, lzma-preset-9, zstd-9} with τ values **frozen identically from `exp95c_multi_compressor_adiyat`** (the same τ used in `exp95e` V1), the SHORT-scope receipt of `exp95e_full_114_consensus_universal` will exhibit:

1. **(H39.1) Monotone envelope**: Pearson `r(log10(total_letters_28), per-surah K=2 recall) ≤ −0.70` across all 114 surahs.
2. **(H39.2) Phase boundary**: All surahs with `total_letters_28 ≤ 188` will satisfy `K=2 ≥ 0.90`; all surahs with `total_letters_28 ≥ 873` will satisfy `K=2 ≤ 0.10`.

If both H39.1 and H39.2 hold on the independent SHORT receipt, the envelope observation is promoted from "post-hoc V1 observation" to a **candidate finding F55** (operating envelope of F53 governed by total surah letter count) suitable for paragraph-level inclusion in `PAPER.md §4.43.0` as a *replicated* observation. If either fails, the V1 envelope observation is logged in `RANKED_FINDINGS.md` as a single-corpus exploratory pattern only and **no F55 finding is opened**.

---

## 2. Locked decision rules (the substantive claim is fixed; numeric tolerances are loose so that the test cannot be tuned post-hoc)

### 2.1 Phase boundary ranges

The V1 receipt produced a sharp boundary: **all 8** K=2-perfect surahs at `total_letters_28 ≤ 188`; **all 70** K=2-zero surahs at `total_letters_28 ≥ 873`. We deliberately loosen the SHORT-scope verdict to `K=2 ≥ 0.90` for `total ≤ 188` and `K=2 ≤ 0.10` for `total ≥ 873` — i.e., a **30 % slack on each end** — so that the test rejects "envelope breaks completely" but allows for SHORT-scope perturbation-set differences (different verses targeted, larger sample size).

### 2.2 Verdict ladder (strict order; first match wins)

| # | Branch | Trigger | Implication |
|---|---|---|---|
| 1 | `FAIL_short_run_did_not_complete` | `results/experiments/exp95e_full_114_consensus_universal/short/exp95e_full_114_consensus_universal.json` is missing or malformed | Re-run before assessing H39 |
| 2 | `FAIL_short_tau_drift` | Any τ in the SHORT receipt drifts from the locked `exp95c` τ snapshot by `> 1·10⁻¹²` | Stop; investigate τ-loading before continuing |
| 3 | `FAIL_q100_drift_short` | Embedded Q:100 regression sub-run inside the SHORT receipt does not reproduce K=2 ≥ 0.99 and gzip-solo ≥ 0.98 | Stop; investigate corpus / pipeline drift |
| 4 | `FAIL_envelope_correlation` | Pearson `r(log10 total_letters_28, per-surah K=2)` `> −0.70` (i.e., correlation weaker than threshold) | H39.1 fails; observation does not replicate |
| 5 | `FAIL_envelope_phase_boundary` | At least one surah with `total ≤ 188` has K=2 `< 0.90`, OR at least one surah with `total ≥ 873` has K=2 `> 0.10` | H39.2 fails; phase boundary does not replicate |
| 6 | `PARTIAL_envelope_replicates` | H39.1 holds AND H39.2 holds AND Pearson `r ∈ (−0.85, −0.70]` (correlation present but weaker than V1) | Envelope replicates partially; F55 candidate but with explicit weakening note |
| 7 | **`PASS_envelope_replicates`** | H39.1 holds AND H39.2 holds AND Pearson `r ≤ −0.85` | Envelope replicates at full V1 strength; promote to F55 candidate finding |

### 2.3 What promotion to F55 means (and does NOT mean)

A `PASS_envelope_replicates` verdict promotes the envelope observation to a **candidate finding F55** in the v7.9-cand `RANKED_FINDINGS.md` and the §4.43.0 paragraph in `PAPER.md`. It does **NOT**:

- Promote F54 (universal scaling of F53) back from FALSIFIED — H37/F54 is retracted as R53 and stays retracted regardless of H39's outcome.
- Promote F55 to a *closed* / paper-grade finding — F55 would still need (a) external two-team replication, (b) a formal mechanistic derivation linking compressor window size to phase-boundary location, (c) a cross-tradition test on another long-canon scripture (e.g. Tanakh) before any cross-tradition language is used.
- Justify any retraction of the `exp95c`-frozen τ thresholds — those τ remain locked at the values they had on 2026-04-26 day; F55 would simply describe the regime in which they are effective.

---

## 3. Frozen constants (lock these before reading §4)

All τ thresholds and compressor levels are **identical to `exp95e_full_114_consensus_universal`** (which inherited them from `exp95c_multi_compressor_adiyat`):

```
gzip_level     = 9
bz2_level      = 9
lzma_preset    = 9
zstd_level     = 9
fpr_target     = 0.05
headline_K     = 2
protocol_drift_tol = 0.001

τ_gzip = 0.04960835509138381
τ_bz2  = 0.29584120982986767
τ_lzma = 0.02857142857142857
τ_zstd = 0.029978586723768737
```

The SHORT receipt is generated by re-running `python -m experiments.exp95e_full_114_consensus_universal.run --scope short --workers 6` (already in flight as of this PREREG's freeze time). No modification is made to the `exp95e` codepath; this experiment is purely an *analysis* of the SHORT receipt against a pre-registered envelope test.

---

## 4. Protocol (deterministic)

1. Wait for the SHORT-scope run of `exp95e_full_114_consensus_universal` to complete and write its receipt to `results/experiments/exp95e_full_114_consensus_universal/short/exp95e_full_114_consensus_universal.json`.
2. Run `python scripts/analyse_exp95e_envelope.py --scope short` (the `--scope` argument will be added if not already present at run time; default behaviour reads V1).
3. The script produces an envelope table and Pearson / Spearman correlations on the SHORT receipt.
4. A small verdict-applier (to be added as `scripts/verdict_h39_envelope.py` *only after this PREREG is hash-locked*) reads the SHORT envelope table and produces the H39 verdict against the ladder in §2.2. The verdict is written to `results/experiments/exp95f_short_envelope_replication/exp95f_short_envelope_replication.json` with `prereg_hash` matching this document's SHA-256.
5. `RANKED_FINDINGS.md` and `PAPER.md §4.43.0` are updated **only after** the verdict is written.

---

## 5. Honesty clauses

### 5.1 No τ recalibration

The same locked τ from `exp95c` is used. If a reader argues "the envelope would disappear if you recalibrated τ per surah", that is true — and is exactly why this experiment is reported under the *fixed-τ* regime. Per-surah τ recalibration is a different experiment; if filed it would be `exp95g`, not `exp95f`.

### 5.2 No re-fitting

The phase-boundary thresholds `total_letters_28 ∈ [188, 873]` are taken **literally from the V1 receipt's observed extremes** (the largest `total_letters_28` among the 8 K=2-perfect surahs, and the smallest `total_letters_28` among the 70 K=2-zero surahs). They are not optimised on SHORT data.

### 5.3 No data-fishing reframe

If both branches 4 and 5 of the ladder fail, the envelope observation is logged as a V1-only exploratory pattern in `RANKED_FINDINGS.md` and is not elevated to a finding. **No replacement hypothesis is allowed to be invented post-hoc on the SHORT receipt under the H39 banner**; any further envelope work must be filed as a new pre-registration with a new H-number.

### 5.4 The Q:100 closure F53 is independent

The `exp95e` SHORT receipt re-runs the embedded Q:100 regression sub-run. If that sub-run drifts (verdict ladder branch 3), the entire H39 test is suspended until the drift is investigated. **F53's Q:100 closure does not depend on H39**; H39 is purely about the envelope around F53.

---

## 6. Audit hooks (must reproduce these in the SHORT receipt before the H39 verdict is computed)

Inherited from `exp95e_full_114_consensus_universal`:

- τ-drift sentinel: `max_drift ≤ 1·10⁻¹²` against the locked `exp95c` τ snapshot.
- PREREG-hash sentinel: SHA-256 of `experiments/exp95e_full_114_consensus_universal/PREREG.md` matches `_PREREG_EXPECTED_HASH` in the run module (`ec14a1f6dcb81c3a54b0daeafa2b10f8707457ee4305de07d58ee7ede568e9a7`).
- Embedded Q:100 regression: K=2 ≥ 0.99, gzip-solo ≥ 0.98 inside the SHORT receipt's `q100_regression` block.
- Variant-count sanity: SHORT-scope `n_variants_total ∈ [300_000, 500_000]` (V1's 139 K is too few; FULL's 3.7 M is too many).

The H39 verdict will not be applied if any of these audit hooks fails on the SHORT receipt.

---

## 7. Reproduction recipe

```powershell
# 1. From repo root, with the SHORT receipt already produced by the in-flight
#    `python -m experiments.exp95e_full_114_consensus_universal.run --scope short --workers 6`:
python scripts/analyse_exp95e_envelope.py --scope short
# (after this PREREG.md is hash-locked, the verdict applier is created and run:)
python scripts/verdict_h39_envelope.py
# verdict appears at:
#   results/experiments/exp95f_short_envelope_replication/exp95f_short_envelope_replication.json
```

---

## 8. Cross-references

- Parent V1 result: `results/experiments/exp95e_full_114_consensus_universal/v1/exp95e_full_114_consensus_universal.json` (verdict `FAIL_per_surah_floor`).
- V1 envelope table: `results/experiments/exp95e_full_114_consensus_universal/v1/envelope_table.csv`.
- V1 envelope analysis tool: `scripts/analyse_exp95e_envelope.py`.
- F54 row (FALSIFIED): `docs/reference/findings/RANKED_FINDINGS.md` row 54.
- R53 retraction: `docs/reference/findings/RETRACTIONS_REGISTRY.md` Category L row R53.
- Paper section: `docs/PAPER.md §4.43` and §4.43.0 (envelope observation paragraph).
- Hypothesis ledger: `docs/reference/findings/HYPOTHESES_AND_TESTS.md` row H39.

---

## 9. Frozen-time fingerprint

This document's SHA-256 is computed **after** all text above is final and **before** the SHORT-scope receipt of `exp95e_full_114_consensus_universal` is opened. The hash is logged in:

- `experiments/exp95f_short_envelope_replication/PREREG_HASH.txt` (one line, lowercase hex).
- The eventual receipt's `prereg_hash` field.

A diff between this PREREG and the receipt's `prereg_hash` indicates the substantive claim has been altered post-hoc and **automatically invalidates the F55 candidate-promotion path**.
