# expP4_rigveda_deepdive — pre-registered prediction

**Date authored:** 2026-04-25, before any compute on this experiment.

**Status:** PREREG. The hypothesis below was authored **before** the run.py
ever produced an output for the per-maṇḍala or Hurst measures.

---

## 1. Background — the Rigveda double-extreme

In two parallel tests today the Rigveda Saṃhitā emerged as #1 on both:

| Test | Quran | Hebrew | Greek | **Rigveda** | Pali_MN | Avestan |
|---|---:|---:|---:|---:|---:|---:|
| `expP4_cross_tradition_R3` z_path | −8.92 | −15.29 | −12.06 | **−18.93** | −3.47 | −0.87 |
| `expP4_diacritic_capacity_cross_tradition` R_primitives | 0.47 | 0.69 | 0.70 | **0.92** | 0.20 | 0.21 |

The Rigveda is **the most extreme oral-mnemonic-coding signal in our entire corpus universe**. This deep-dive triangulates that finding by decomposing the Rigveda into its 10 canonical maṇḍalas and asking which ones drive the headline.

## 2. Rigveda structural background (for prediction calibration)

The 10 maṇḍalas are not homogeneous:

- **Maṇḍalas 2–7** ("family books"): the **oldest** stratum, attributed to specific ṛṣi families. Tightly metered, ritually-deployed.
- **Maṇḍalas 1, 10**: late strata; longer, philosophical, includes Nāsadīya Sūkta (10.129).
- **Maṇḍala 8**: mixed — partly old (Kāṇvas) but also late additions.
- **Maṇḍala 9**: **entirely Soma hymns** — mantric, repetitive, ritually homogeneous.

If LC2 (oral-mnemonic optimisation) is correct and the Rigveda is its purest example, the *family-book + Soma* maṇḍalas (2–7, 9) should drive the signal.

## 3. Pre-registered predictions

> **PRED-DD-1**: Maṇḍala 9 (Soma) shows the **strongest** path-minimality (most negative z_path) of any single maṇḍala when each is analysed independently. This is the most ritually-homogeneous corpus in the entire Rigveda.
>
> **PRED-DD-2**: At least 7 of 10 maṇḍalas individually show z_path < −2 with empirical p < 0.025. (i.e. the −18.93 whole-corpus signal is NOT carried by a single outlier maṇḍala but is broadly distributed.)
>
> **PRED-DD-3**: The Rigveda Hurst exponent on the verse-word-count sequence (18 079 ṛc-s in canonical order) is H > 0.6, indicating long-range positive memory comparable to or stronger than the Quran's locked H = 0.738 on its 6 236 ayāt.
>
> **PRED-DD-4**: Across the 10 maṇḍalas, the per-maṇḍala R_primitives (diacritic capacity) and the per-maṇḍala |z_path| are **positively correlated** (Spearman ρ > 0.4). I.e. maṇḍalas that are more path-minimal also use more of their diacritic-channel capacity. This would be the first cross-feature *internal* validation of the LC2 conjecture.

## 4. Falsifiers

- **F1**: Maṇḍala 9 (Soma) does NOT show the strongest z (e.g. it ranks 6th or worse) AND no single ritually-explainable pattern emerges. Falsifies PRED-DD-1.
- **F2**: < 4 of 10 maṇḍalas individually show z_path < −2 at p<0.025. Falsifies PRED-DD-2 (the whole-corpus signal is fragile).
- **F3**: Rigveda H ≤ 0.55 on any of the three tested time-series. Indicates the long-range memory does not extend to the Vedic.
- **F4**: ρ(R_prim, |z_path|) across maṇḍalas is null or negative. Falsifies PRED-DD-4 (the two extremes are independent, not co-driven by oral-mnemonic optimality).

## 5. Method (locked)

- **Per-maṇḍala R3**: For each maṇḍala m ∈ {1..10}, take the sūktas of m in canonical order; build the 5-D `features_lang_agnostic` matrix; z-score within m; compute canonical path cost; permute 5000× with seed = 42 + m; report z_path, p_one_sided.
- **Per-maṇḍala A2 R_prim**: For each maṇḍala m, run the same Devanagari pair extractor used in `expP4_diacritic_capacity_cross_tradition` on the verses-of-m only; report R_combinations and R_primitives.
- **Hurst (R/S)**: Three sequences, all in canonical order:
  1. Verse word-count sequence (length 18 079 ṛc-s).
  2. Sūkta word-count sequence (length 1024).
  3. Sūkta EL sequence (length 1024).
  Each estimator uses `src/extended_tests4.py:_hurst_rs` byte-for-byte.
- **Cross-correlation**: Spearman ρ between (per-maṇḍala R_primitives) and (per-maṇḍala |z_path|), across the 10 maṇḍalas.

## 6. Reads / writes

- Reads only: `data/corpora/sa/rigveda_mandala_*.json` via `raw_loader.load_vedic()`.
- Writes only under `results/experiments/expP4_rigveda_deepdive/`.

## 7. Recovery / supersession

This experiment **explores** the Rigveda result; it does not supersede `expP4_cross_tradition_R3` or `expP4_diacritic_capacity_cross_tradition`. Both locked results stand. The whole-corpus z_path = −18.93 must be reproducible from the per-maṇḍala data + the canonical maṇḍala ordering (sanity check, not strict identity since the whole-corpus z is computed with a different per-maṇḍala-z-score normalisation).
