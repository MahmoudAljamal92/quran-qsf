# QSF ULTIMATE — Reproduction & Discovery Pipeline

`QSF_ULTIMATE.ipynb` is a single, self-validating Jupyter notebook that reproduces **every testable finding** in the QSF project from raw data, re-tests all flip-flopped claims cleanly, closes previously-retracted formal-proof gaps honestly, and explores **seven universal-law candidates** (L1–L7) with pre-registered falsification criteria.

The legacy `../QSF_REPRODUCE.ipynb` is kept untouched for reference. This is the authoritative replacement.

## Quick start

```powershell
cd C:\Users\mtj_2\OneDrive\Desktop\Quran
python -m pip install -r requirements.txt
jupyter lab notebooks/ultimate/QSF_ULTIMATE.ipynb
```

Run **Cell 0** to set run-mode, then **Kernel → Restart & Run All**.

| Mode       | Permutations / bootstrap | Laptop runtime (CPU) |
|------------|--------------------------|----------------------|
| `FAST`     | 200 / 500                | ~ 60 min             |
| `NORMAL`   | 2 000 / 5 000            | ~ 3 h 30 min         |

Well under the 6-hour ceiling even on `NORMAL`.

## The four integrity locks (Phase 2)

All four are written to `results/integrity/` at the start of every run and verified at the end. Any drift raises a fatal `HallucinationError` or `UnknownFindingError`.

| Lock file | Contents | Purpose |
|---|---|---|
| `corpus_lock.json`   | SHA-256 of the 10 raw corpus files + combined hash | Detect silent data tampering |
| `code_lock.json`     | SHA-256 of every `.py` in `src/` + `git rev-parse HEAD` | Detect silent code drift |
| `results_lock.json`  | 45+ flagship scalars `{id, name, expected, tol, verdict_expected}` | Detect AI-fabricated numbers |
| `names_registry.json`| Whitelist of every legal finding ID (T1–T31, D01–D28, S1–S5, G1–G5, L1–L7, E-series, Supp-A/B/C) | Detect hallucinated finding names |

### Re-blessing after a genuine code change

If you change a feature definition or a test and a locked scalar legitimately shifts:

1. Edit the offending entry in `results/integrity/results_lock.json` and update its `expected`, `tol`, or `verdict_expected`.
2. Run Cell 0 with `UPDATE_LOCK = True`.
3. Re-run **Restart & Run All**. The notebook will re-hash the lock, write a new signature, and proceed.
4. Commit the new lock + the code change together.

Never edit `expected` values silently — the lock exists precisely to prevent that.

## Resume behaviour (checkpoints)

Every critical phase saves `results/checkpoints/phase_<id>.pkl` with:

```python
{ "corpus_sha256":  ...,   # current corpus_lock combined hash
  "code_sha256":    ...,   # current code_lock combined hash
  "phase_id":       ...,
  "fast_mode":      ...,
  "results":        ...,
  "env":            ...,   # numpy/scipy/sklearn versions
  "timestamp":      ...,
  "seed":           42 }
```

On startup the notebook scans `results/checkpoints/` and loads any checkpoint whose `{corpus, code, fast_mode, seed}` fingerprint matches the current run — skipping re-computation. Delete the directory or flip `FORCE_RERUN = True` to force a clean run.

## Cell layout (22 phases, ~130 cells)

| Phase | Cells | Topic |
|:-:|:-:|---|
| 0  | 1–4     | Preamble & run-mode config |
| 1  | 5–8     | Environment + dependency pin |
| 2  | 9–14    | Pre-registration + 4 integrity locks |
| 3  | 15–19   | Data integrity + pickle-bug sanity simulation |
| 4  | 20–23   | Leakage audit (exact + partial-quote) |
| 5  | 24–27   | CamelTools warm-up + heuristic falsification |
| 6  | 28–33   | Apples-to-apples Band A/B/C + CamelTools-Φ_M re-run |
| 7  | 34–40   | Core separation (T1–T4, T10, D03–D05) |
| 8  | 41–46   | Scale-free + path + coherence |
| 9  | 47–51   | Markov + bigram + S24 sensitivity |
| 10 | 52–56   | Dual-channel + turbo + EL capacity |
| 11 | 57–63   | Adversarial + forgery + null ladder + 100 synthetic Qurans |
| 12 | 64–69   | Robustness (CV, Meccan/Medinan, matched-length sensitivity) |
| 13 | 70–74   | Classifier + nested CV + Meccan→Medinan transfer |
| 14 | 75–84   | Topology (RQA, lesion, saddle, phi_frac, RG, Fisher, Hurst) |
| 15 | 85–89   | Epigenetic layer E3 + variant forensics + waqf |
| 16 | 90–96   | Cross-language + cross-scripture STOT |
| 17 | 97–101  | External + oral sim + per-surah dashboard |
| 18 | 102–112 | **Discovery Lab — L1–L7 + transmission-noise sim + Csiszár-Körner + Berry-Esseen** |
| 19 | 113–118 | Adiyat + surrogate null + behavioural proxies |
| 20 | 119–124 | Formal-proof gap closures (G1–G5 honest) |
| 21 | 125–130 | Scorecard + lock verify + 6 diagnostic figures + ZIP export |

Each phase ends with a `_verify_<phase>()` helper that asserts expected ranges and prints `[OK]` / `[WARN]` / `[FATAL]`.

## What was intentionally left out

- **Qira'at stress test** — removed per user direction; we focus strictly on Hafs + harakat (E3).
- **Constructive STOT (E4)** — the "synthesise a text satisfying 4/5 conditions" experiment was skipped as too speculative.
- **Purely aesthetic figures** — only **6 diagnostic figures** that reveal structure invisible in tables are generated (controlled by `GENERATE_FIGURES`).

## Outputs

On a successful run you get:

```
results/
├── integrity/
│   ├── corpus_lock.json
│   ├── code_lock.json
│   ├── results_lock.json
│   └── names_registry.json
├── checkpoints/
│   └── phase_<00..21>.pkl
├── figures/
│   ├── fig1_phi_m_boxplot.png
│   ├── fig2_perturbation_heatmap.png
│   ├── fig3_error_exponent.png
│   ├── fig4_cross_scripture_psi.png
│   ├── fig5_saddle_eigenvalues.png
│   └── fig6_multilevel_hurst.png
├── ULTIMATE_SCORECARD.md
├── ULTIMATE_REPORT.json
└── QSF_ULTIMATE_<YYYYMMDD_HHMMSS>.zip   ← final bundle
```

The ZIP contains the notebook, all results, all checkpoints, all locks, and the scorecard.

## Honest-reporting policy

This notebook prints **NEGATIVE** and **NOT REPRODUCED** findings just as prominently as positive ones. Examples you will see:

- **D21** (rhyme-swap P3) — `NOT REPRODUCED`, direction opposite to paper.
- **D25** (Meccan/Medinan F>1) — `FALSIFIED` by pre-registered test B.
- **D18** (Adjacent diversity) — `FALSIFIED` (10.6th pct vs claimed 100th).
- **T28, T29** — `NOT REPRODUCED` on clean data (pickle-bundling artifact + golden-ratio cherry-pick).
- **G3, G5** — Previously "closed", now correctly labelled `FALSIFIED by math` (algebraic tautologies). Replaced by **real transmission-noise simulation** (Phase 18 E1).

If any **POSITIVE** flagship scalar drifts > 5 % from the docs/FINDINGS_SCORECARD.md baseline without a lock update, Cell 130 raises `HallucinationError`.

## Contact & version

Generated by the `_build.py` script in this directory. To rebuild the notebook from source:

```powershell
python notebooks/ultimate/_build.py
```

This regenerates `QSF_ULTIMATE.ipynb` deterministically. Always rebuild (not hand-edit) — the `_build.py` source is the ground truth.
