# pipeline/ — Universal Quran forgery detector

This folder hosts the **end-to-end orchestration** for the v7.9-cand patch G universal-closure pipeline. The actual pre-registered experiment lives at `experiments/exp95e_full_114_consensus_universal/`; this folder gives you a single notebook that drives it from start to finish, with explicit cell-level audit gates.

## Files

| File | Purpose |
|---|---|
| `full_quran_consensus.ipynb` | 11-cell Jupyter notebook (markdown intro + 10 cells) |
| `README.md` | This file |

## What the notebook does

The notebook orchestrates the H37 hypothesis test (universal scaling of F53 — the K=2 multi-compressor consensus closure of single-letter forgery detection) cell-by-cell:

| Cell | Role |
|---:|---|
| 0 (md) | Title + scope ladder table + reading order + honest-scope reminder |
| 1 | Imports + **SCOPE picker** (the only config cell) + tqdm import |
| 2 | τ-drift sentinel: load locked τ from exp95c receipt, abort if any value drifts |
| 3 | Corpus load + integrity self-check begin (SHA-256 verified pickle) |
| 4 | Variant enumeration — preview counts per surah before scoring |
| 5 | Parallel scoring loop with **live tqdm progress bar (%, ETA, rate)** |
| 6 | ctrl-null FPR re-computation (with tqdm) + Q:100 regression sub-result |
| 7 | Per-surah aggregate + verdict per PREREG ladder + 10 weakest surahs |
| 8 | Missed-variant clustering by (orig → repl) consonant pair |
| 9 | Deployable `is_quranic()` detector demo on canonical / forged / mismatched inputs |
| 10 | Persist JSON receipt + CSV outputs + audit report + self-check end |
| 11 | **Package everything into a zip + colour-coded one-click download button** |

## How to run

### From Jupyter

```powershell
# from repo root
jupyter notebook pipeline/full_quran_consensus.ipynb
```

Or VS Code's notebook UI; either works.

In **Cell 1** (the only config cell) set the `SCOPE` variable to one of:

| Scope     | Variants  | Runtime on i7-7700HQ (6 workers, AC) | Use case                                  |
|-----------|----------:|--------------------------------------|-------------------------------------------|
| `v1`      |  ~145 K   | **45 min – 1.5 h**                   | DEFAULT — pre-registered headline         |
| `short`   |  ~377 K   | 2 – 4 h                              | First 3 verses per surah                  |
| `sample`  |  ~370 K   | 2 – 4 h                              | Random 10 % of FULL                       |
| `quarter` |  ~925 K   | 5 – 8 h                              | Random 25 % of FULL                       |
| `half`    | ~1.85 M   | 10 – 18 h                            | Random 50 % of FULL (overnight)           |
| `full`    |  ~3.7 M   | 18 – 36 h                            | Every interior letter (overnight + day)   |

Set `SURAHS_FILTER = "Q:099,Q:100"` for a quick 2-surah sanity check before committing to all 114.

### From the command line (no notebook)

The same pipeline runs end-to-end without the notebook:

```powershell
# headline V1 run (default)
python -m experiments.exp95e_full_114_consensus_universal.run

# overnight half-sample run
python -m experiments.exp95e_full_114_consensus_universal.run --scope half --workers 6

# full overnight + day enumeration
python -m experiments.exp95e_full_114_consensus_universal.run --scope full --workers 6 --chunk 32
```

The CLI runs all the same audit gates and writes the same outputs; the notebook adds live progress bars (tqdm), the verdict-coloured download button, and per-cell inspection points.

## Outputs

All written under `results/experiments/exp95e_full_114_consensus_universal/<scope>/`:

| File | Contents |
|---|---|
| `exp95e_full_114_consensus_universal.json` | Main receipt: per-surah K=1..K=4 recall, ctrl-null FPR, verdict, audit, hashes |
| `per_surah_table.csv` | One row per surah: recall_K1..K4 + per-compressor solo recalls + NCD min/max |
| `missed_variants.csv` | Every variant where `K_fired < 2` (full meta + per-compressor NCD + fire flags) |
| `audit_report.json` | τ-drift sentinel, PREREG-hash check, Q:100 regression, missed-variant clusters, self-check timestamps |
| `exp95e_<scope>_results_<ts>.zip` | Auto-downloadable bundle of all of the above + `SUMMARY.txt` (only produced by the notebook) |

## Verdict ladder (from PREREG §5)

The verdict is computed in strict order; first match wins:

1. `FAIL_tau_drift` — locked τ != exp95c receipt
2. `FAIL_q100_drift` — Q:100 sub-result misses regression target
3. `FAIL_consensus_overfpr` — ctrl K=2 FPR > 0.05
4. `FAIL_per_surah_floor` — any surah K=2 recall < 0.99
5. `FAIL_aggregate_below_floor` — aggregate K=2 recall < 0.999
6. `PARTIAL_per_surah_99_aggregate_99` — per-surah ≥ 0.99 AND aggregate ≥ 0.99 BUT < 0.999
7. `PASS_universal_999` — per-surah ≥ 0.99 AND aggregate ≥ 0.999
8. `PASS_universal_100` — every surah recall = 1.000 AND aggregate = 1.000

## Honest-scope reminders (also in Cell 0)

- The detector covers **single-consonant substitutions on the Hafs ʿan ʿĀṣim canonical text only**. Word-level edits, semantic substitutions, LLM-generated counterfeits, and cross-qirāʾāt confusions are **out of scope** (see `exp92_genai_adversarial_forge`).
- A PASS verdict is *single-team single-codebase* evidence. Community-grade "universal forgery tool" requires external two-team replication.
- There is no Shannon-capacity theorem here. This is empirical universal scaling, not a derivation. The theorem track lives at `expS_synth_geometric_info_theorem` and `expP18_shannon_capacity_el`.

## Provenance chain

```
exp94_adiyat_864          (Q:100, gzip only) — recall = 0.990741, gzip ceiling
        ↓
exp95_phonetic_modulation (failed null FN01) — global phonetic factor cannot beat baseline
        ↓
exp95b_local_ncd_adiyat   (failed null FN02) — window-local NCD recall collapses to 0.399
        ↓
exp95c_multi_compressor_adiyat — K=2 consensus closes Q:100 at recall 1.000 (F53)
        ↓
exp95d_multi_compressor_robust  — 3-seed × Q:099 robustness (PARTIAL, Q:099 at 998/999)
        ↓
exp95e_full_114_consensus_universal — universal scaling across all 114 (this pipeline; H37)
        ↓
exp92_genai_adversarial_forge   — adversarial closure (LLM-aware forger; awaits credentials)
```

The chain shows the discipline: each step is pre-registered, each negative result is logged as a failed null (not a retraction), and only `exp95c` produced the headline closure that `exp95e` now scales to the entire Quran.

## Troubleshooting

- **`BrokenProcessPool` from Jupyter**: drop `WORKERS = 1` in Cell 1 to fall back to single-process mode. Slower but always works.
- **`FileNotFoundError: exp95c receipt missing`**: run `python -m experiments.exp95c_multi_compressor_adiyat.run` first to populate the τ source.
- **`IntegrityError: checkpoint SHA-256 mismatch`**: `phase_06_phi_m.pkl` has changed since the manifest was written. Restore from `archive/` or rebuild manifest.
- **`FAIL_q100_drift`**: a non-trivial result. The Q:100 sub-result inside this run does not reproduce the exp95c headline. Investigate before any wider claim.
- **Long runtime on FULL scope**: expected. Use `--scope sample` for a 10× speedup with a uniform random sample. Or run overnight on a workstation.
