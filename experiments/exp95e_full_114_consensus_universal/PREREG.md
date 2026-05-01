# exp95e_full_114_consensus_universal — Pre-registration

**Hypothesis ID**: H37
**Status**: pre-registered, frozen 2026-04-26 night (Asia/Riyadh)
**Patch context**: v7.9-cand patch G — universal scaling of F53 (multi-compressor consensus closure of single-letter forgery detection across the entire Quran).
**Supersedes**: nothing yet — first universal run. Builds on `exp95c_multi_compressor_adiyat` (Q:100 closure) and `exp95d_multi_compressor_robust` (3-seed × Q:099 robustness).

---

## 1. Hypothesis (one paragraph)

**H37 (universal closure)**: Under K = 2 multi-compressor consensus across {gzip-9, bz2-9, lzma-preset-9, zstd-9} with τ values **frozen** from the `exp95c_multi_compressor_adiyat` ctrl-null calibration, single-letter consonant-substitution forgeries are detected with aggregate recall ≥ 0.999 and aggregate ctrl-null FPR ≤ 0.05, **on every one of the 114 canonical surahs** of the Quran (Hafs ʿan ʿĀṣim text), and the per-surah K = 2 recall floor is ≥ 0.99 across all 114 surahs.

**What this is NOT**: this is *not* a claim that the Quran is forgery-proof against *adversarial* edits (e.g. word-level rewriting, semantic-preserving substitutions, LLM-generated counterfeits). Those are tested separately in `exp92_genai_adversarial_forge` and are out of scope here. H37 covers exactly the same edit class as exp94 / exp95c / exp95d: substitute one Arabic consonant at one position with one of the other 27 Arabic consonants, on the canonical letter-folded sequence of a surah.

---

## 2. Why this experiment is needed

`exp95c` proved K = 2 closes Adiyat-864 at recall = 1.000 with ctrl FPR = 0.0248. `exp95d` showed Q:100 is fully seed-stable (3 seeds × 1.000) and Q:099 generalises at 998/999 = 0.998999. These two surahs are short (Q:100: 11 verses, 22-char first verse; Q:099: 8 verses). The "universal" claim that the multi-compressor ceiling is closed *for the entire Quran* still requires running the protocol on every surah and verifying that no surah falls below the per-surah floor. That is exactly H37.

If H37 passes, finding F53 widens from "Q:100, paper-grade; Q:099 partial" to "all 114 surahs, paper-grade", and the deployable `_detector.py` tool inherits a calibrated empirical recall curve for every surah class. If H37 partially fails, we obtain a per-surah landscape of where consensus breaks, which feeds directly into the design of `exp92` (adversarial forger) and into `exp97_crosscripture_t8` (cross-tradition replication of the consensus rule).

---

## 3. Frozen constants (lock these before reading §4)

| Symbol | Value | Source |
|---|---|---|
| `SEED` | 42 | `exp95c` (preserves protocol drift sentinel) |
| `N_PERT_PER_UNIT` | 20 | `exp95c` |
| `CTRL_N_UNITS` | 200 | `exp95c` |
| `GZIP_LEVEL` | 9 | `exp95c` |
| `BZ2_LEVEL` | 9 | `exp95c` |
| `LZMA_PRESET` | 9 | `exp95c` |
| `ZSTD_LEVEL` | 9 | `exp95c` |
| `FPR_TARGET` | 0.05 | `exp95c` |
| `BAND_A_LO`, `BAND_A_HI` | 15, 100 | `exp95c` (ctrl-pool gating) |
| `HEADLINE_K` | 2 | `exp95c` (PASS verdict requires K=2 closure) |
| `PROTOCOL_DRIFT_TOL` | 0.001 | `exp95c` |
| `tau_per_compressor` | **frozen, loaded from exp95c receipt** | see §3.1 |

### 3.1 τ values (must reproduce these to 1 e-12)

The four τ thresholds are **not recalibrated** by exp95e; they are loaded from the `exp95c_multi_compressor_adiyat` receipt at runtime. The expected values (verified against the receipt at 2026-04-26 night):

```
τ_gzip = 0.04960835509138381
τ_bz2  = 0.29584120982986767
τ_lzma = 0.02857142857142857
τ_zstd = 0.029978586723768737
```

**Drift sentinel**: at the start of every run, exp95e re-loads the exp95c receipt, extracts τ, and compares to a hash-locked snapshot embedded in `run.py::_LOCKED_TAU`. If the receipt's τ differs from the snapshot by more than 1 e-12 in any of the four values, the run aborts with `FAIL_tau_drift` *before any scoring*.

**Why frozen**: re-calibrating τ per surah (even across the same shared ctrl-null pool) introduces a degree of freedom that lets surah-specific recall be inflated by surah-specific FPR. The right design is one shared τ across all 114 surahs, calibrated once on Adiyat. This is the same convention exp95c+exp95d used.

---

## 4. Scope: V1 / SHORT / FULL (chosen at runtime)

The variant enumerator supports four scopes. The **default and headline scope is V1** (matches the exp95c "first verse" enumeration, scaled to all 114 surahs). The other three are diagnostic.

| Scope | Definition | Approx variants | Approx 8-core runtime |
|---|---|---:|---:|
| `V1` (default, **headline**) | first verse of each surah, every consonant position × all 27 substitutes | ~145 K | ~30 min – 2.5 h |
| `SHORT` | first three verses of each surah, same enumeration | ~377 K | ~2 – 6.5 h |
| `FULL` | every interior letter of every interior word of every interior verse (exp94 perturbation rule), all 27 substitutes | ~3.7 M | ~12 – 63 h |
| `SAMPLE` | uniform 10 % random sample of `FULL`, same RNG seed | ~370 K | ~2 – 6.5 h |

**The PASS / FAIL verdict (§5) is computed against the V1 scope**, since that is the protocol scope inherited from exp95c. SHORT, FULL, and SAMPLE produce diagnostic *consistency* receipts: they are flagged `CONSISTENT` if their per-surah recall agrees with V1 to ±0.005, otherwise `INCONSISTENT_DIAGNOSTIC` (which is informative, not a verdict failure). Pre-registering this asymmetry up front is what makes the V1 verdict honest.

---

## 5. Verdict ladder (evaluated in strict order; first match wins)

1. **`FAIL_tau_drift`** — any τ value loaded from the exp95c receipt differs from the locked snapshot by > 1 e-12.
2. **`FAIL_q100_drift`** — the embedded Q:100 regression sub-run (always executed; required for the protocol-drift sentinel) produces K = 2 recall ≠ 1.000 OR gzip-solo recall differing from the exp94 baseline (0.990741) by > `PROTOCOL_DRIFT_TOL`.
3. **`FAIL_consensus_overfpr`** — aggregate K = 2 ctrl-null FPR > 0.05 + 1 e-6.
4. **`FAIL_per_surah_floor`** — at least one of the 114 surahs has K = 2 recall < 0.99 on the V1 scope.
5. **`FAIL_aggregate_below_floor`** — aggregate K = 2 recall (variants pooled across all 114 surahs) < 0.999.
6. **`PARTIAL_per_surah_99_aggregate_99`** — every surah ≥ 0.99 AND aggregate ≥ 0.99 BUT aggregate < 0.999. Headline narrows to "K = 2 closes single-letter forgery to 99 % per surah, 99 %+ aggregate".
7. **`PASS_universal_999`** — every surah ≥ 0.99 AND aggregate ≥ 0.999. Headline widens to "K = 2 closes single-letter forgery on the entire Quran at recall ≥ 0.999".
8. **`PASS_universal_100`** — every surah K = 2 recall = 1.000 AND aggregate = 1.000. Headline widens to "K = 2 closes single-letter forgery on the entire Quran at perfect recall".

The verdict is computed on the V1 scope. SHORT / FULL / SAMPLE receive a separate `consistency_verdict ∈ {CONSISTENT, INCONSISTENT_DIAGNOSTIC}` for transparency; they cannot upgrade or downgrade the V1 verdict.

---

## 6. Inputs (read-only, integrity-checked)

- `phase_06_phi_m.pkl` (loaded via `experiments._lib.load_phase`, SHA-256 verified against checkpoint manifest)
- `results/experiments/exp95c_multi_compressor_adiyat/exp95c_multi_compressor_adiyat.json` (τ source + Q:100 regression target)
- `results/experiments/exp94_adiyat_864/exp94_adiyat_864.json` (gzip-solo Q:100 regression target = 0.990741)
- `experiments/_lib.py` (read-only loader + self-check)

The run uses **no external corpus and no network**. Every byte produced is a deterministic function of the corpus pickle, the locked τ, and the run-time scope flag.

## 7. Outputs (write-only under sandboxed dir)

All outputs are written under `results/experiments/exp95e_full_114_consensus_universal/<scope>/`, where `<scope> ∈ {v1, short, full, sample}`.

- `exp95e_full_114_consensus_universal.json` — main receipt: per-surah K = 1 / K = 2 recall + FPR, per-compressor solo recalls, missed-variant indices, verdict, runtime, hashes
- `missed_variants.csv` — every variant where `K_fired < 2`, with columns `surah, verse_idx, char_pos, orig, repl, ncd_gzip, ncd_bz2, ncd_lzma, ncd_zstd, K_fired`
- `per_surah_table.csv` — one row per surah: `surah_label, n_variants, recall_K1, recall_K2, recall_K3, recall_K4, recall_solo_gzip, recall_solo_bz2, recall_solo_lzma, recall_solo_zstd`
- `audit_report.json` — drift sentinels, fingerprint hashes, Q:100 regression sub-run, missed-variant clustering analysis (frequency by orig→repl letter pair)
- `self_check_<timestamp>.json` — protected-file integrity check (begin / end snapshots)

---

## 8. Audit hooks (always executed)

1. **τ-drift sentinel** (FAIL_tau_drift): see §3.1.
2. **Q:100 regression sub-run** (FAIL_q100_drift): re-run the exp95c protocol on Q:100 inside this run, expect K = 2 recall = 1.000 and gzip-solo recall = 0.990741 ± 0.001. Receipt logs both numbers.
3. **Self-check** (`experiments._lib.self_check_begin/end`): hash all protected files before and after; abort if any change.
4. **Fingerprint sentinel**: re-hash `PREREG.md` and `run.py` at run start; record both hashes in the receipt. The PREREG hash must match the value embedded in `run.py::_PREREG_EXPECTED_HASH` after the file is finalised (this PR will fix the value before the first run).
5. **Missed-variant clustering**: for every (orig, repl) consonant pair, compute the K = 2 miss rate. If any pair has miss-rate ≥ 0.10 in V1 scope, log it to the audit report under `cluster_warnings` (informational; not a verdict failure).
6. **Per-surah variant-count sanity check**: each surah's V1 variant count must equal `len(_letters_28(surah.verses[0])) * 27`; deviation aborts with `FAIL_enumeration_mismatch`.

---

## 9. Replication recipe (single command)

From repo root:

```bash
# Default V1 scope (headline; ~30 min – 2.5 h)
python -m experiments.exp95e_full_114_consensus_universal.run

# Diagnostic SHORT scope (first 3 verses)
python -m experiments.exp95e_full_114_consensus_universal.run --scope short

# Full FULL scope (overnight ~12-63h)
python -m experiments.exp95e_full_114_consensus_universal.run --scope full

# Tuning runtime knobs
python -m experiments.exp95e_full_114_consensus_universal.run --scope v1 --workers 8 --chunk 64
```

The run is fully deterministic given (corpus pickle SHA, scope, workers don't affect numerics). The receipt's `verdict` field plus `frozen_constants` plus `tau_per_compressor` are sufficient to reproduce on a different machine.

---

## 10. What this experiment does NOT claim

- It does **not** claim universal forgery resistance. It claims K = 2 detection of *single-consonant substitutions* in the Hafs ʿan ʿĀṣim canonical text. Word-level edits, insertions, deletions, swaps of canonical readings (qirāʾāt), and adversarial LLM forgeries are out of scope.
- It does **not** claim a *theorem*. There is no Shannon-capacity derivation here; this is an empirical universal scaling result. The theorem track is `expS_synth_geometric_info_theorem` and `expP18_shannon_capacity_el`.
- It does **not** redefine the term "Adiyat-864 ceiling". The original ceiling (99.07 % gzip-only recall) was a statement about a single compressor on Q:100; F53 closed it under K = 2 multi-compressor consensus. H37 widens the F53 closure from "Q:100" to "every Quran surah".
- It does **not** claim *replication*. Single-team single-codebase results require external two-team replication before they can be cited as community-validated.

---

## 11. Pre-registration locking checklist

- [x] §3 frozen constants pinned
- [x] §3.1 τ values pinned to exp95c receipt (verified 2026-04-26 night)
- [x] §5 verdict ladder pinned in strict-order form
- [x] §8 audit hooks listed
- [x] §10 explicit list of what is NOT claimed
- [ ] PREREG SHA-256 hash embedded in `run.py::_PREREG_EXPECTED_HASH` (filled after this file is finalised)
- [ ] First run executed and receipt produced (filled at run time)
