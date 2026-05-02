# Pristine — the Quran fingerprint detector

A four-layer interactive app that compares any input text against the
**whole-Quran corpus-pooled** fingerprint, with no per-surah cherry-picked
thresholds, no learned weights, and no hidden corpus access.

## Run locally

```powershell
pip install streamlit numpy
python -m streamlit run app/pristine.py
```

The app boots in ~2 seconds: it SHA-256-verifies the canonical Hafs
corpus (`data/corpora/ar/quran_bare.txt`), then computes the eight
reference axes once and caches them.

## What it detects

| Editing operation | Detected by | Guarantee |
|---|---|---|
| 1-letter substitution | Layer A2 + C1 (F69 bigram-shift Δ ∈ [1,2]) | 100% on canonical corpus |
| Multi-letter substitution (k ≤ 5) | Layer A2 + C1 | Δ ≤ 2k (theorem) |
| Word substitution | Layer A2 (Levenshtein) | yes |
| Verse swap within surah | Layer C2 (gzip-NCD) | F70: 88.4% recall |
| Combined verse + letter edits | A + B + C composite | yes |
| Pure imitation (Quran-style new text) | Layer B (8 axes mismatch) | yes |
| Cross-language paste | script detection + Layer B mismatch | yes |
| Diacritic-only edit | — | invisible by design (Hafs/Warsh equivalent) |

## The four layers

1. **Layer A — Identity** (verbatim + fuzzy lookup against the canonical
   Hafs corpus). Returns `exact`, `fuzzy`, or `miss`.
2. **Layer B — Whole-Quran fingerprint** (8 corpus-pooled axes). Per-axis
   match% + composite + deciding-axis spotlight.
3. **Layer C — Tampering forensics** (only if Layer A flagged near-Quran).
   F55 bigram-shift + F70 gzip-NCD.
4. **Layer D — Cross-tradition** (scoped for a future release).

## The eight Layer B axes

All eight are **whole-corpus pooled** (computed at startup on the
concatenated 6,236 verses). No subset is selected anywhere.

| Symbol | Name | Formula |
|---|---|---|
| H_EL | Verse-final entropy | Shannon entropy of verse-final letter histogram |
| p_max | Rhyme concentration | most common verse-final letter / total |
| C_Ω | Channel utilisation | 1 − H_EL / log₂(28) |
| F75 | Universal invariant | H_EL + log₂(p_max · 28) |
| D_max | Redundancy gap | log₂(28) − H_EL |
| d_info | IFS fractal dimension | H_nats / log(1/0.18) |
| HFD | Higuchi fractal dimension | Higuchi 1988 on verse-length series |
| Δα | Multifractal width | MFDFA on verse-length series |

## Self-audit

```powershell
python app/pristine_audit.py
```

Runs nine checks (corpus integrity, reproducibility, no sharpshooter,
no learned weights, no extra corpus access, match-formula honesty,
F69 theorem, verbatim soundness, examples). Writes `pristine_AUDIT.md`.

Current verdict: **9/9 PASS** (see `pristine_AUDIT.md`).

## Honest scope — what this tool does NOT do

- Does **not** decide canonicity or which qira'a (reading) is correct.
- Does **not** make theological or metaphysical claims.
- Does **not** authenticate manuscripts.
- Does **not** detect semantic correctness — a fake passage with valid
  rhyme will pass Layer B (only Layer A catches it as not-in-corpus).
- Does **not** use machine-learned weights or neural networks.
- **Diacritic-only** and **hamza-variant** edits are intentionally
  invisible — by design, because the canonical Quran has multiple valid
  readings (Hafs, Warsh, Qalun, ...) that differ only in those marks.

## Why we never use per-surah subsets

Saying *"47 of 109 Quranic surahs satisfy property X"* is **sharpshooter
logic**: it implies 62 surahs *don't* satisfy X, which means X is not
actually a property of the Quran — it is a property of a hand-picked
subset.

Pristine compares your text against the **whole-Quran corpus-pooled**
value of every axis (one number per axis, computed on all 6,236 verses
concatenated). The Quran is treated as a single object on every axis.
No subset is ever selected to make a stronger claim.

This intentionally differs from earlier project receipts (exp183 used
per-chapter medians; exp177 used per-surah aggregates). Those receipts
remain valid in their own scope but were flagged as carrying
sharpshooter risk in the project's own audit (see
`experiments/exp143_QFootprint_Sharpshooter_Audit/PREREG.md`).

## File layout

```
app/
├── pristine.py                      # Streamlit UI (4 layers + sidebar)
├── pristine_lib/
│   ├── __init__.py
│   ├── constants.py                 # locked numbers + provenance + SHA verify
│   ├── normalize.py                 # Arabic 28-letter rasm normaliser
│   ├── corpus.py                    # Quran loader + verbatim/fuzzy lookup
│   ├── metrics.py                   # 8 axes + bigram-shift + gzip-NCD
│   └── examples.py                  # 7 demo presets
├── pristine_audit.py                # 9-check self-audit
├── pristine_AUDIT.md                # generated audit report
└── PRISTINE_README.md               # this file
```
