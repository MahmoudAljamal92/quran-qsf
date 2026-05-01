# exp95e_full_114_consensus_universal

**Status**: pre-registered, frozen 2026-04-26 night
**Hypothesis**: H37 — universal scaling of F53
**Patch**: v7.9-cand patch G (universal closure run)

## What this experiment is

`exp95c_multi_compressor_adiyat` showed that K = 2 multi-compressor consensus across {gzip-9, bz2-9, lzma-preset-9, zstd-9} closes the Adiyat-864 detection ceiling on Q:100 at recall = 1.000. `exp95d_multi_compressor_robust` confirmed seed-stability on Q:100 (3 seeds × 1.000) and partial generalisation to Q:099 al-Zalzalah at 998/999 = 0.998999.

`exp95e` is the **universal scaling**: same protocol, same locked τ, every Quran surah. If the K = 2 rule continues to hold across all 114, finding F53 widens from "Q:100, paper-grade; Q:099 partial" to "every Quran surah, paper-grade", and the deployable `_detector.py` tool inherits a calibrated empirical recall curve for every surah.

## Files in this directory

| File | Purpose |
|---|---|
| `PREREG.md` | Frozen pre-registration (verdict ladder, τ, scopes, audit hooks) |
| `run.py` | Main pipeline (parallelized, multi-scope, audit-aware) |
| `_enumerate.py` | Variant generators (V1 / SHORT / FULL / SAMPLE) |
| `_audit.py` | τ-drift, PREREG-hash, missed-variant clustering, Q:100 regression |
| `_detector.py` | Deployable `is_quranic()` forgery detector |
| `__init__.py` | Package marker |
| `README.md` | This file |

## Running it

The experiment supports four scopes, chosen at runtime. **V1 is the headline scope** — it matches exp95c's "first verse" enumeration scaled to all 114 surahs and is the only scope evaluated for the formal PASS/FAIL verdict (per PREREG §4).

| Scope | Variants | 8-core runtime (rough) | Use case |
|---|---:|---:|---|
| `v1` (default) | ~145 K | 30 min – 2.5 h | Headline pre-registered run |
| `short` | ~377 K | 2 – 6.5 h | Diagnostic: first 3 verses |
| `full` | ~3.7 M | 12 – 63 h | Full exp94-rule enumeration (overnight) |
| `sample` | ~370 K | 2 – 6.5 h | Random 10 % of full |

```powershell
# headline V1 (recommended first run)
python -m experiments.exp95e_full_114_consensus_universal.run

# diagnostic SHORT (3 verses per surah)
python -m experiments.exp95e_full_114_consensus_universal.run --scope short

# overnight FULL run (every interior letter, exp94 rule)
python -m experiments.exp95e_full_114_consensus_universal.run --scope full

# subset run (e.g. only Q:100 + Q:099)
python -m experiments.exp95e_full_114_consensus_universal.run --surahs Q:099,Q:100

# tune workers / chunk size
python -m experiments.exp95e_full_114_consensus_universal.run --workers 8 --chunk 32
```

The orchestration notebook at `pipeline/full_quran_consensus.ipynb` wraps this with cell-level progress, audit display, and per-surah / missed-variant tables.

## Outputs

All written under `results/experiments/exp95e_full_114_consensus_universal/<scope>/`:

- `exp95e_full_114_consensus_universal.json` — main receipt: per-surah recall, K-of fires, ctrl-null FPR, verdict, audit report, hashes
- `per_surah_table.csv` — one row per surah with K=1..K=4 recall + per-compressor solo recalls
- `missed_variants.csv` — every variant with `K_fired < 2` (CSV columns: surah, scope, verse_idx, char_pos, orig, repl, K_fired, NCDs, fires)
- `audit_report.json` — drift sentinels, PREREG-hash check, Q:100 regression, missed-variant clustering, self-check timestamps

## Reading the verdict

The verdict ladder in PREREG §5 is evaluated in strict order; first match wins:

| Verdict | Meaning | Action |
|---|---|---|
| `FAIL_tau_drift` | τ values drifted from exp95c receipt | Re-run exp95c; do NOT trust the receipt |
| `FAIL_q100_drift` | Q:100 sub-result missed regression target | Investigate before any wider claim |
| `FAIL_consensus_overfpr` | aggregate K=2 ctrl FPR > 0.05 | Recalibrate τ pool; do NOT pass the run |
| `FAIL_per_surah_floor` | at least one surah K=2 recall < 0.99 | Inspect per-surah table; cluster missed variants |
| `FAIL_aggregate_below_floor` | aggregate K=2 < 0.999 | Same; deeper failure |
| `PARTIAL_per_surah_99_aggregate_99` | per-surah ≥ 0.99 AND aggregate ≥ 0.99 BUT < 0.999 | Headline narrows; F53 still holds with caveat |
| `PASS_universal_999` | per-surah ≥ 0.99 AND aggregate ≥ 0.999 | F53 widens to "every surah at recall ≥ 0.999" |
| `PASS_universal_100` | every surah recall = 1.000 AND aggregate = 1.000 | F53 widens to "perfect single-letter detection across the entire Quran" |

## Deployable forgery detector

The `_detector.py` module exposes a single API:

```python
from experiments.exp95e_full_114_consensus_universal._detector import is_quranic

result = is_quranic(candidate_text, "Q:100")
# {
#   "verdict": "AUTHENTIC" | "FORGED" | "AMBIGUOUS",
#   "K_fired": 0..4,
#   "fires": {"gzip": bool, ...},
#   "ncd": {...},
#   "tau_used": {...},
#   "confidence": 0..1,
#   "explanation": "...",
#   ...
# }
```

The detector is **stateless** apart from the locked τ table. It is callable from any environment that has the four compressor libraries installed (`gzip` / `bz2` / `lzma` are stdlib; `zstandard` is `pip install zstandard`).

CLI for spot checks:

```powershell
python -m experiments.exp95e_full_114_consensus_universal._detector \
    --surah Q:100 \
    --candidate-file path\to\candidate.txt
```

## Limitations & honest framing

1. The detector covers **single-consonant substitutions on the Hafs ʿan ʿĀṣim canonical text only**. Word-level edits, semantic substitutions, LLM-generated counterfeits, and cross-qirāʾāt confusions are out of scope (see `exp92_genai_adversarial_forge` for the LLM-aware track).
2. Even a `PASS_universal_100` verdict is **single-team single-codebase** evidence. The community standard for "universal forgery tool" requires external two-team replication.
3. There is no Shannon-capacity theorem here. The universal scaling is empirical. The theorem track lives at `expS_synth_geometric_info_theorem` and `expP18_shannon_capacity_el`.
4. The headline verdict is on the V1 scope. SHORT / FULL / SAMPLE produce diagnostic consistency receipts only (PREREG §4).

## Provenance

This experiment depends on:

- `phase_06_phi_m.pkl` (corpus pickle, integrity-verified by `_lib`)
- `results/experiments/exp94_adiyat_864/exp94_adiyat_864.json` (gzip-only Q:100 baseline = 0.990741)
- `results/experiments/exp95c_multi_compressor_adiyat/exp95c_multi_compressor_adiyat.json` (locked τ + K = 2 Q:100 target = 1.000)

If any of those receipts is missing the run aborts immediately.
