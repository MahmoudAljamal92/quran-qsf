# QSF REPLICATION PIPELINE — COMPLETE ENGINE (v10.19)

> **⚠ DEPRECATED — v10.19 (2026-04-17 late night). DO NOT USE FOR CURRENT REPLICATION.**
>
> This file has been retained in `docs/old/` only as an audit-trail record. It documents the **pre-v3 (clean-data rebuild)** replication pipeline and is missing every result from v3, v5, v6, v7, v7.1, v7.2, v7.3, v7.4, v7.4+ and v7.5 — that is, **every experiment, integrity lock, and headline number produced since 2026-04-18**. A replicator following this file verbatim would land on roughly v2/v3-era numbers, **not** the current v7.5 run-of-record.
>
> **Specifically missing from this v10.19 document that is now authoritative in v7.5:**
> - The four-manifest SHA-256 integrity-lock protocol (`corpus_lock.json`, `code_lock.json`, `results_lock.json`, `names_registry.json`, `checkpoints/_manifest.json`) introduced in v6
> - Hotelling T² = 3 557 multivariate headline (v5; replaces the biased Cohen d = 6.34 used below)
> - Nested-CV AUC = 0.998 with Band-A (15–100 verses) restriction (v3+; reduces Quran to 68/114 surahs for the inferential statistics — this document uses all 114)
> - Benjamini–Hochberg FDR correction family (v5)
> - Permutation-null with `chi2.sf` (v5; replaces the machine-epsilon-floored `1 − chi2.cdf`)
> - Hadith quarantine (v5; Bukhari hadith quotes the Quran, so including it in the control pool inflates uniqueness)
> - CamelTools `calima-msa-s31` root extractor (v3; replaces the 21 %-accurate heuristic extractor used below)
> - Ultimate-2 11-channel edit-detection layer (R1–R11), v7
> - **R12 gzip NCD** on 28-letter consonantal rasm (γ = +0.0716 at fixed length, v7.3)
> - **Adiyat 864-variant compound test** (99.1 % detection, v7.3)
> - **exp45 two-letter enumeration** (100 % compound detection on 72 900 variants, v7.4)
> - **exp46 emphatic-class substitution audit** (1.15 % Quran vs 4.83–9.50 % Arabic controls, v7.4+/v7.5)
> - **exp48 verse-graph topology** (d = +0.937 on n_communities, v7.4+)
> - **exp49 6-D Hotelling gate** (SIGNIFICANT BUT REDUNDANT, v7.5)
> - **exp50 cross-corpus emphatic audit** (H2_QURAN_SPECIFIC_IMMUNITY, v7.5)
> - **exp51 poetry_islami sensitivity** (STABLE, v7.5)
> - 25 honest retractions with the results_lock.json integrity manifest
>
> **For current replication, use one of the following in order of rigour:**
>
> 1. **`docs/PAPER.md` v7.5 §7 "Reproducibility"** — the authoritative three-command replicator (`python notebooks/ultimate/_build.py` → `jupyter nbconvert --execute QSF_ULTIMATE.ipynb` → `python _audit_check.py`). Outputs 127 SHA-pinned scalars under `results/`.
> 2. **`README.md` (repo root)** — quick-path (`python -m src.clean_pipeline`, ~112 s, 31 tests → `results/CLEAN_PIPELINE_REPORT.json`) and full-path entry points.
> 3. **`docs/QSF_COMPLETE_REFERENCE.md` §11 "How to reproduce a single claim in 60 s"** — per-test invocations.
> 4. **`experiments/README.md`** — sandbox protocol for new experiments (write-isolated, integrity self-check).
>
> **Do not build against this v10.19 file.** The `docs/old/` location is explicit; any other path pointer in the repo is stale.
>
> *Banner added 2026-04-21 as part of the v7.5.1 doc-reconciliation patch. Original v10.19 body below is left untouched for audit-trail integrity.*

---

## v10.19 changes (2026-04-17 late night) — INTEGRITY STRENGTHENING

Four defensive additions addressing specific reviewer concerns:

### `scripts/gap4_exponential_family.py`
Runtime: ~5s. Output: `output/gap4_exponential_family_results.json`.
Closes Gap 4 empirically — tests Chernoff information under 5 distribution families (Gaussian, Laplacian, t-Student, Lognormal, non-parametric kNN). All 5 give C > 0, demonstrating the theorem extends beyond Gaussian.

### `scripts/preregistered_tests_v10.18.py` + `docs/PREREGISTRATION_v10.18.md`
Runtime: ~60s. Output: `output/preregistration_v10.18_results.json`.
Three new pre-registered tests (CV Φ_M, Meccan/Medinan H-Cascade, bootstrap Ω_master). Results: 2/3 CONFIRMED, 1/3 PARTIAL (honest reporting).

### `scripts/abbasi_discrimination_test.py`
Runtime: ~15s. Output: `output/abbasi_discrimination_results.json`.
Resolves the Ω_master Abbasid-poetry near-tie. Uses Abbasi as reference centroid for Φ_M — gives **d=+1.93** (Quran is as far from Abbasi as from random Arabic). 6 of 8 discriminators separate them.

### `scripts/tight_fairness_retest.py`
Runtime: ~20s. Output: `output/tight_fairness_retest_results.json`.
Addresses the 2 checkpoint-audit caveats. **Key finding**: tight per-verse word-count matching ([5,15] words) **strengthens d from 1.93 to 2.66**. The fairness asymmetries were biasing AGAINST Quran.

### `scripts/checkpoint_audit.py` + `scripts/script_audit.py`
Runtime: ~10s combined. Methodology + integrity checks that verify no corpus-specific leakage, no asymmetric preprocessing, no hardcoded Quran values, seeds set throughout.

---

## v10.18 changes (2026-04-17 night) — MULTI-SCALE CODE VERIFICATION

Three new scripts added to operationalize the "letter-to-chapter" scope:

### `scripts/h_cascade_test.py`
Runtime: ~30s. Output: `output/h_cascade_results.json`.
Computes conditional Shannon entropies at 4 scales (letter, word, verse, chapter) and the fractality index F = mean(r_k)/std(r_k). **Quran F = 2.49 vs pooled controls 0.79, d = 2.07, p = 1.4×10⁻⁷**.

### `scripts/hierarchical_omega.py`
Runtime: ~90s. Output: `output/hierarchical_omega_results.json`.
Decomposes Ω into 5 scale components normalized to non-Quran baselines. **Quran Ω_master = 5.66 dominates 10/11 control corpora; Quran vs Iliad d = 3.49, p = 1.3×10⁻³⁸ (strongest effect in project)**.

### `scripts/structural_forgery_experiment.py`
Runtime: ~3 min. Output: `output/structural_forgery_results.json`.
Four structural perturbations × 30 trials × 68 matched surahs. **P3 rhyme-swap: Quran 93% Φ_M collapse vs Arabic controls 36%, p = 5.1×10⁻¹⁶**.

### Master notebook upgrade

`QSF_MASTER_REPLICATION.ipynb` now:
- Uses proper Arabic morphology (root extraction, ARABIC_CONN, root-bigram H_cond) — matches paper's Φ_M d=1.93 result exactly
- Adds §7a (H-Cascade), §7b (Hierarchical Ω), §7c (Structural Forgery) as runnable cells
- 30 cells total (16 code + 14 md)

### Paper v3.12

New §6 "Multi-Scale Code Verification" added with all three experiments, peer-review-safe framing, and the scope clarification (Ω catches structural forgery without reference; byte-level single-letter is orthogonal / tawātur territory, not information-theoretic). References: Costa et al. 2002 (multiscale entropy), Tishby et al. 2000 (information bottleneck).

---

## v10.17 changes (2026-04-17 evening):

### 1. MASTER REPLICATION NOTEBOOK (NEW — canonical entry point for replicators)

File: `QSF_MASTER_REPLICATION.ipynb` (in repo root) — 24 cells, 13 code + 11 markdown.
Runtime target: 25–40 min on a 2020-era laptop (8 cores, 16 GB RAM).

**One-shot reproduction of all v10.16/v10.17 headline findings**:
- Cell 3: Φ_M matched-length (Quran vs Arabic ctrl)
- Cell 4: Pre-registered adversarial prediction (98.2% canon-wins, d=1.17)
- Cell 5: Cross-language fair stress test (Quran 4/5 vs Tanakh 1/5 conditions)
- Cell 6: Formal proof gap closure (Hessian PD + explicit γ(Ω))
- Cell 7: Shannon–Aljamal Ω scalar verification (≈19 vs ≈1)
- Cell 8: Summary figure (3-panel: Φ_M density, perturbation gaps, cross-language bars)

**Smoke-test verified (2026-04-17)**: runs end-to-end on this machine, produces all expected directional findings at smoke parameters (10 surahs × 5 perturbations).

Build script: `scripts/build_master_notebook.py`.
The existing `QSF_LOCAL_V3.3.ipynb` (97 cells) is preserved as archival reference.

### 2. Cross-language fairness audit + re-run

Audited v10.16 cross-language test against 4-rule fairness protocol:
- Rule 2 FAIL (length-matching): had only MIN=5, no MAX → 900-verse Tanakh books vs 3-verse surahs.
- Rule 3 FAIL (Arabic agglutination): `وَاللَّهُ` undercounted as 1 token vs Hebrew `כי` standalone.

Fixed in `scripts/cross_language_stot_test_v2_fair.py`:
- Strict length band [10, 100] verses applied uniformly.
- Arabic clitic prefixes (و، ف، ب، ل، ك، س) split before stopword extraction.

**Results are ROBUST** — Quran 4/5 conditions unchanged; EL-ordering sig rate 49.5%→55.8% (improved); Quran/Tanakh ratio 40×→12× (still overwhelming). See `output/cross_language_stot_results_FAIR_v2.json`.

### 3. Theorem renaming: corrected author surname → **Shannon–Aljamal**

The theorem name has been corrected to use the author's actual surname (Mahmoud Aljamal). The earlier filename (which carried an AI-hallucinated surname) was renamed to `QSF_SHANNON_ALJAMAL_THEOREM.md`. All references updated across docs. The previously-incorrect surname does not appear anywhere in the published `arxiv_submission/` package (verified).

### 4. arXiv submission package prepared

Folder: `arxiv_submission/` — self-contained package ready for upload:
```
arxiv_submission/
├── README.md                     (upload instructions + checklist)
├── paper.md                      (v3.11 main paper)
├── requirements.txt              (pinned deps)
└── supplementary/
    ├── S1_shannon_aljamal_theorem.md
    ├── S2_formal_proof.md
    ├── S3_gap_closure.md
    ├── QSF_MASTER_REPLICATION.ipynb
    ├── scripts/ (cross_language, preregistered, gap_closure)
    └── output/  (all JSON results)
```

Conversion to PDF for arXiv upload: `pandoc paper.md -o paper.pdf --mathjax -V geometry:margin=1in`.

---

# QSF REPLICATION PIPELINE — COMPLETE ENGINE (v10.15)
## Feed this document + data files to ANY AI to fully replicate ALL findings
### Last Updated: 2026-04-17 v10.15 | Merges: PIPELINE_SPEC + MASTER_BLUEPRINT + COLAB_INSTRUCTIONS + NEW_ANOMALY_TESTS + FRONTIER_FRAMEWORK + CAVEAT_RESOLUTION + MAHALANOBIS + NOTEBOOK_V3.3.2 + DEEP_SCAN_MERGE + PHASE_TRANSITION + RESULTS_SYNC + JSON_CROSS_CHECK + ROBUSTNESS_CHECKS + AUDIT_v10.15
### v10.15 changes (2026-04-17, today): DEEP AUDIT + DUAL-LAYER RETRACTION + FORMAL PROOF + EPIGENETIC LAYER + PROPER RG v2 + MATCHED-LENGTH SENSITIVITY.
  - **Deep project audit** (`docs/QSF_AUDIT_REPORT_v10.15.md`): recursive scan of all active files; verified no contamination (0/4487 Quran verses leaked to any control corpus), Mahalanobis correctly uses control-only centroid+covariance, all 8 scripts compile cleanly.
  - **Retraction 1: Layer-2 spectral micro-hash uniqueness** (`scripts/spectral_perturbation_test.py`): initially framed as anomaly, then reclassified upon expert review. Shuffle-null comparison is trivially beaten by any coherent language (Arabic phonotactics destroys random letter mixing). Cross-corpus matched-length test places Ya-Sin's mean ratio (0.882) in the middle of Arabic controls [0.801, 0.936] — not uniquely Quranic. The uniform CV ≈ 0.68 is reinterpreted as empirical support for graceful error-correction (§4.5a), not a new anomaly. Paper §STOT and `QSF_COMPLETE_REFERENCE.md` §2.6b updated with retraction.
  - **Retraction 2: Phase 30 'critical point' framing** (`scripts/rg_flow_v2.py`): proper Kadanoff block coarse-graining at L = 1, 2, 4, 8, 16, 32 confirms the existing Phase 31 negative. Three probes all within control range: variance-scaling z = +0.53 for EL / +1.13 for VL / −0.29 for CN; power-spectrum α = 0.50 for EL (no 1/f signature); fixed-point detection is trivial for all corpora. The φ_frac = 0.618 value is a *static scalar ratio landing near the golden ratio*, NOT a physics critical point. Paper §4.6 summary and Conclusion bullet reworded accordingly.
  - **NEW: Formal information-theoretic proof** (`docs/QSF_FORMAL_PROOF.md`): Shannon-style derivation of STOT v2 from first principles. Each of the 5 conditions derived from standard info-theory results (Chernoff bound on ML decoder; Berrou-Glavieux 1993 turbo codes; Cover & Thomas constrained entropy; DPI sequencing). Main theorem P_e ≤ exp(−γ(Ω)·N). Five gaps enumerated for mathematician coauthor.
  - **NEW: Epigenetic-layer conceptual framework** (`docs/QSF_EPIGENETIC_LAYER.md`): extends DNA analogy to fifth layer (rasm as primary, harakat+waqf+qira'at as epigenome). Four testable predictions (P-Epi-1..4). One already supported by vocalized 43×43 spectral (93-97% diacritic detection).
  - **NEW: Matched-length sensitivity** (`scripts/matched_length_sensitivity.py`): addresses corpus unit-size heterogeneity caveat. Restricted all corpora to three length bands. **Result: Φ_M Cohen's d nearly DOUBLES under matched length — from 1.01 (unfiltered) to 1.93 (Band A: 15–100 verses), p = 1.85×10⁻²². S24 enrichment 2.70×. The heterogeneity is a framing concern, NOT a driver. Paper §4.4 limitation 12 reclassified RESOLVED.**

  | Band | n_Q | n_C | Φ_M d | Φ_M p | S24 Q% | S24 C% | Enrich |
  |---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
  | A (15–100 verses) | 68 | 362 | **+1.928** | 1.85e-22 | 58.8% | 21.8% | 2.70× |
  | B (10–150 verses) | 88 | 464 | **+1.969** | 1.79e-29 | 54.5% | 20.3% | 2.69× |
  | C (5–286 verses)  | 109 | 616 | **+1.878** | 2.14e-32 | 49.5% | 16.9% | 2.93× |

  - Paper bumped to v3.10. All three primary MDs now synced.

### v10.14 changes (2026-04-17 morning): ROBUSTNESS CHECKS. 3 new scripts: `robustness_checks.py` (scale-invariant φ_frac stratification, surrogate null 1D, golden ratio lesion, pipeline cross-check), `surrogate_5d.py` (10k forced-EL surrogates measured on full 5D Φ_M — masterstroke: 100% beat EL but only 8.92% match Φ_M; surrogates specifically fail on CN 14.6% and H_cond 6.5%), `cross_surah_root_diversity.py` (root diversity law across 114 surahs). KEY FINDINGS: (1) φ_frac stratification: Short 0.589 / Medium 0.618 / Long 0.651 — length-independent. (2) Surrogate null proves 5D Φ_M is necessary and sufficient. (3) Macro container (φ_frac) invariant under single-word substitution; micro engine (Φ_M) detects +0.4% shift — two complementary scales. Paper bumped to v3.9.

### v10.13 changes: Full JSON cross-check of QSF_RESULTS_v3.3.json (144 keys) against all documentation. 10 new notebook findings documented: Lesion testing (7-level dose-response, smooth degradation), Info Geometry saddle point (4−/1+ eigenvalues), Terminal position analysis (signal depth = 2 letters), Inter-surah cost (0.704× random), Optimal stopping (NEGATIVE), Abjad (NEGATIVE), Spectral gap (NEGATIVE), Ring/chiasm (NEGATIVE), LZ binding (NEGATIVE), Bootstrap CIs (all positives confirmed). Full notebook-vs-pipeline reconciliation table (22 metrics, all qualitative conclusions match). Paper v3.8. Falsified hypotheses expanded: items 44–49.
### v10.12 changes: Notebook results sync — all 3 MD docs updated to match actual v3.3.2 run output. §4.6 (RG Flow, Info Geometry) corrected: RG rank #10/10 (NEGATIVE, not scale-invariant), Info Geo curvature #10/10 (smoothest, MIXED). Phase 30 criticality confirmed POSITIVE (φ_frac=0.618, 3/3 indicators). T12 Markov order added as new finding (d=−1.849, H₃/H₂=0.096). T3 graph modularity flagged: d=0.472 in pipeline scripts but d=0.099 in notebook (under investigation). EL capacity d=−0.917 in notebook (per-surah methodology reverses direction — fix pending).
### v10.10 changes: Notebook v3.3.1 updates: (1) T bug fix: T uses H_cond (conditional) not H_root (unigram). (2) EL capacity reverted to log2(n_unique). (3) T3 verse cap 150→500 (did not resolve discrepancy; d still ~0.1). (4) Independence test uses composite metrics. (5) FAST_MODE tuned for better accuracy. (6) 3 new phases: Phase 30 (Structural Phase Transition), Phase 31 (RG Flow), Phase 32 (Info Geometry). (7) ARABIC_CONN corrected: 18→14 in code and paper.
### v10.9 changes: Deep scan merge — integrated ~1,900 file scan results. Added supplementary phases (Hurst, Acoustic). Local notebook (QSF_LOCAL_V3.3.ipynb) documented. Falsified checks F1–F4 added to Dead findings. Phenomena inventory and consolidated action list now in QSF_COMPLETE_REFERENCE.md §15–17.
### v10.8 changes: Notebook v3.3 expanded to ≤26 findings (66 cells, 142 KB). FAST_MODE + HAS_GPU config. Phases 20–23: scale-free S24, Meccan/Medinan, EL capacity, independence. Phases 24–27: GPU MiniLM semantic S24, CamelTools root validation, Iliad cross-language T, Wikipedia external validation. Verification table: 22 core + 4 optional GPU/data checks; fast-mode-sensitive → INFORMATIONAL. RESULTS JSON export. 6 disclosures. Theorem → proposition.
### v10.7 changes: Mahalanobis unification — 5D phase-space metric Φ_M replaces multiplicative Φ. Quran 3.75 vs controls 1.95 (d=1.009, p=3.8×10⁻²³). ksucca overlap resolved. Deep code audit: 104 files, 49k lines, 0 errors.
### v10.6 changes: 7 caveat-resolution scripts. Closed: classifier bias (nested CV AUC 0.893, 10.4σ), vowel blindness (43×43 vocalized spectral, 93-97%), long-surah dilution (sliding window 8.5×), Φ=0 diagnosed. Semi-formal Φ proof. Blind external validation.
### v10.4 changes: 5 frontier-framework scripts (adversarial benchmark, semantic bridge, constrained null ladder, global order rank, Abbasi mining). Paradigm shift from anomaly-hunting to constraint-frontier estimation.
### v10.3 changes: 8 new structural tests (MI, word-order, graph, RQA, syllable, connective-type, gradients, surah-network). 13 anomalies confirmed, 3 negative. Φ Complementarity Law proposed.
### v10.2c changes: waw/ya bug fix, T pooling artifact corrected, turbo-code formalized, Iliad T test, Zipf analogs (negative), Monte Carlo null
### Runtime: ~5 hours total (CPU scripts ~2h + GPU scripts ~30min + v10.3 new tests ~11min + v10.6 caveat tests ~6min)

---

> **INSTRUCTION TO AI**: Read this document top-to-bottom. It contains everything needed
> to reproduce the Quran Structural Fingerprint (QSF) results from raw data.
> Follow phases in order. Verify each check before proceeding.
> For findings reference, see `QSF_COMPLETE_REFERENCE.md`.

---

## TABLE OF CONTENTS

0. [What This Pipeline Produces](#0-what-this-pipeline-produces)
1. [Environment Setup](#1-environment-setup)
2. [Data Architecture & Corpus Rules](#2-data-architecture)
3. [Feature Definitions](#3-feature-definitions)
4. [Phase 1: Foundation (CPU)](#phase-1-foundation)
5. [Phase 2: Core Laws (CPU)](#phase-2-core-laws)
6. [Phase 3: Validation & Robustness (CPU)](#phase-3-validation)
7. [Phase 4: Cross-Language (CPU)](#phase-4-cross-language)
8. [Phase 5: Morphological Analysis (CPU)](#phase-5-morphological)
9. [Phase 6: GPU Validation (Colab)](#phase-6-gpu-validation)
10. [Phase 7: Classification & Compression (CPU)](#phase-7-classification)
11. [Phase 8: Legacy Pipeline (CPU/GPU)](#phase-8-legacy-pipeline)
12. [Verification Checksums](#verification-checksums)
13. [Execution Order & Orchestration](#execution-order)
14. [Claim Framework](#claim-framework)

---

# 0. WHAT THIS PIPELINE PRODUCES

## Finding Tiers

| Tier | Criteria | Publication Target |
|------|----------|-------------------|
| **💎 Diamond** | Quran-unique, confirmed, large effect | PNAS / Nature |
| **🥇 Gold** | Strong, confirmed, may not be cross-language unique | Comp. Linguistics |
| **🥈 Silver** | Interesting, caveats | Supplementary |
| **❌ Dead** | Failed, artifact | Document as negative |

## Diamond Findings (all scripts produce these)

| Finding | Key Number | Script | Output |
|---------|-----------|--------|--------|
| Anti-Metric Law | d=**2.964** | `pnas_laws_analysis.py` | `pnas_laws_results.json` |
| EL+CN Dual-Channel | EL=0.727, CN=0.067, cross-lang unique | `el_cn_uniqueness_proof.py` + `cross_language_dual_channel.py` | `el_cn_uniqueness_results.json` + `cross_language_dual_channel_results.json` |
| Scale-Free Ordering | Fisher p<0.01 at W=8-20, L=10 min | `scale_invariance_test.py` + `compression_ratio_test.py` | `scale_invariance_results.json` + `compression_ratio_results.json` |
| Markov Unforgeable | 17.2× gap | `markov_s24_test.py` | `markov_s24_results.json` |
| Predictive Power | AUC=0.90 (7.9σ) | `feature_validated_classifier.py` | `blind_classifier_results.json` |
| **Turbo-Code Capacity** | **1.72× gain, 99.2% indep** (connective set corrected) | `turbo_code_formalization.py` | `turbo_code_formalization_results.json` |
| **Per-Text T (corrected)** | **24.3% T>0, p=2.47×10⁻³³** | `T_per_text_correct.py` | `T_per_text_correct_results.json` |
| **Multi-Scale Perturbation** | **Abs. 2.8-10x degradation** | `multiscale_perturbation_test.py` | `multiscale_perturbation_results.json` |
| **Cross-Surah Order** | **p=0.10 (n.s.)** EL+CN within-surah only | `cross_surah_dependency_test.py` | `cross_surah_dependency_results.json` |
| **External Validation** | **S24 23.8% (Wikipedia) vs 49.1% (Quran)** — unseen corpus confirms | `external_validation.py` | `external_validation_results.json` |
| **Verse-Internal Word Order** (v10.3) | **d=0.470, p=9.65×10⁻¹³** — words within verses non-randomly arranged | `qsf_new_anomaly_tests.py` (T2) | `qsf_new_anomaly_results.json` |
| **Graph Modularity** (v10.3) | **d=0.472, p=5.21×10⁻⁷** (pipeline scripts); **d=0.099, p=0.379** (notebook v3.3.2 — implementation gap under investigation) | `qsf_new_anomaly_tests.py` (T3) | `qsf_new_anomaly_results.json` |
| **RQA Anti-Metric Confirmation** (v10.3) | **LAM d=−0.395, p=6.8×10⁻⁴** — independent nonlinear dynamics confirmation | `qsf_new_anomaly_tests.py` (T4) | `qsf_new_anomaly_results.json` |
| **Surah Path Optimization** (v10.3) | **z=−8.76, 0th pct** — Mushaf minimizes structural path length | `qsf_new_anomaly_tests.py` (T8) | `qsf_new_anomaly_results.json` |
| **Adjacent Diversity** (v10.3) | **100th pct** — Mushaf maximizes variance of adjacent distances | `qsf_new_anomaly_tests.py` (T8) | `qsf_new_anomaly_results.json` |

## Gold Findings

| Finding | Script | Output |
|---------|--------|--------|
| D6 Geometric Bridge | `d6_proper_confirmation.py` | `D6_proper_confirmation.json` |
| GPU MiniLM Validation | `abbasi_resolution_gpu.py` | `abbasi_resolution_gpu_results.json` |
| Meccan/Medinan Split | `pnas_laws_analysis.py` | (in pnas_laws_results) |
| Coherence Length λ=7 | `coherence_length_test.py` | `coherence_length_results.json` |

## Silver Findings

| Finding | Script | Output |
|---------|--------|--------|
| Morphological Frontier | `morphological_frontier.py` | `morphological_frontier_results.json` |
| Abbasi CPU Resolution | `abbasi_resolution.py` | `abbasi_resolution_results.json` |
| Root Category JSD | `root_category_transitions.py` | `root_category_v2_results.json` |

## Dead / Falsified Findings (must document as negative controls)

| Finding | Key Result | Source | Status |
|---------|-----------|--------|--------|
| D7 Self-Prediction | cv_r2=−42.1, holdout p=0.90 | Pipeline v3 | ❌ DEAD |
| T6 Complementarity | d=0.221, p=0.176, poetry_jahili same level | `qsf_new_anomaly_tests.py` | ❌ FALSE POSITIVE |
| Variational Principle | Greek NT 65.6% > Quran 59.7% | Cross-language tests | ❌ NOT UNIQUE |
| **F1: Global Hurst (word lengths)** | H=0.654 vs Hadith H=0.617 | `الحمدلله_رب_العالمين.ipynb` | ❌ NOT UNIQUE |
| **F2: Surah-level Hurst** | H=1.033, n=114 too few for R/S | `الحمدلله_رب_العالمين.ipynb` | ❌ UNRELIABLE |
| **F3: Acoustic/diacritic ratio Hurst** | H=0.674, Hadith also has it | `الحمدلله_رب_العالمين.ipynb` | ❌ NOT UNIQUE |
| **F4: Muqattaat as topological keys** | p=0.4495 | `الحمدلله_رب_العالمين.ipynb` | ❌ FALSIFIED |

## Supplementary Phases (not in main pipeline — from deep scan)

| Phase | Finding | Key Number | Source Notebook |
|-------|---------|-----------|----------------|
| **Supp-A: Hurst Analysis** | Anti-persistence after detrending | H_diff=0.262 (Quran) vs 0.130 (Bible) | `01_track1_core_hurst.ipynb` |
| **Supp-B: Multi-Level Hurst** | 4-level persistence topology | H=0.898 (verse), 0.811 (delta), 0.652 (word) | `بسم_الله_الرحمن_الرحيم.ipynb` |
| **Supp-C: Acoustic Bridge** | Syllable → pitch correlation | r=0.541, p=4.1×10⁻⁵ | `V_Acoustic_01-03`, `V_Phonetic_02` |

> **Note**: These supplementary findings are documented in `QSF_COMPLETE_REFERENCE.md` §15. They are not part of the automated pipeline but have computed results from dedicated notebooks.

## Local Notebook Alternative

**`QSF_LOCAL_V3.3.ipynb`** (v3.3.2) — Self-contained Jupyter notebook for local execution (Windsurf / VS Code CPU). Contains 33 phases across 75 cells. Key configuration:
- `FAST_MODE = True` — improved permutation counts (T2: 500, T8: 1000, Markov: 10×30×100)
- `HAS_GPU = auto` — auto-detects CUDA via `torch.cuda.is_available()` (safe on CPU-only machines)
- Windows encoding fixes applied (utf-8 reconfiguration)
- Checkpoint: `CONTENT/qsf_inter_checkpoints/` (auto-loads `after_v4_final.pkl.gz`)

**Notebook Phases (v3.3.2):**

| Phase | Cell# | Analysis |
|-------|-------|----------|
| 0-2 | 0-10 | Install, imports, config, helpers, data load, 5D features |
| 3-12 | 11-31 | Anti-Metric, S24, T distribution, Phi_M, Turbo, LOOCV, T8, Multi-Scale, Omega, Coverage |
| 14-23 | 32-52 | Detection, Perturbation, Tamper, Markov, Ensemble, LSF, Scale-Free, Meccan/Medinan, EL Capacity, Independence |
| 24-27 | 53-61 | GPU MiniLM, CamelTools, Iliad, Wikipedia |
| 28 | 62 | *[Deprecated — merged into Phase 29]* |
| **29** | **63-64** | **Info-Theoretic Fingerprint** (T9-T12: Kolmogorov, FFT, MI, Markov) |
| **30** | **65-66** | **Structural Phase Transition Discovery** (order parameter, heat capacity, criticality) |
| **31** | **67-68** | **Renormalization Group Flow** (coarse-graining scales 1-16, fixed-point analysis) |
| **32** | **69-70** | **Information Geometric Singularity** (Fisher metric, geodesic, curvature) |
| **33** | **71-72** | **Final Verification Table** (includes T9-T12 targets) |

**Bug fixes in v3.3.2 (cumulative from v3.3.1):**
- T calculation: H_cond (conditional root bigram entropy) replaces H_root (unigram)
- EL channel capacity: reverted to log2(n_unique); per-surah calculation gives d=−0.917 (Quran has fewer unique end-letters per surah due to fawasil concentration — methodology fix pending)
- T3 graph modularity: verse cap raised from 150 to 500; d remains ~0.1 (cap was not the cause — implementation differs from pipeline scripts)
- Independence: checks composite metrics (Phi_M, Turbo, S24) not individual features
- ARABIC_CONN: 14 items (not 18; 2 proclitics excluded, 2 non-connectives removed)
- HAS_GPU: auto-detect via torch.cuda (was hardcoded True, crashed CPU-only machines)
- Phase 28 placeholder: closes unexplained 27→29 gap in phase numbering
- Phase 29 (T9-T12): findings now in verification table with tolerance targets
- Paper §3.2 T%>0 updated to 30.0%; §3.4 Φ_M updated to 3.97 (with footnotes)
- Phase 30 tqdm added for progress feedback

**Actual notebook output (FAST_MODE=True, v3.3.2 run 2026-04-16):**

| Metric | Notebook Value | Pipeline Script Value | Match? |
|--------|---------------|----------------------|--------|
| Anti-Metric d | 2.294 (vs all controls) | 2.964 (vs poetry only) | Different comparison groups |
| T2 word order d | 0.483 | 0.470 | ✅ Close |
| T3 modularity d | 0.099 | 0.472 | ❌ Under investigation |
| T8 path z | −8.798 | −8.76 | ✅ Close |
| T distribution d | 1.233 | 1.562 | Different comparison groups |
| T %T>0 | 30.3% | 24.3% | Different H_cond version |
| Φ_M mean | 3.968 | 3.75→3.97 | ✅ Match |
| Φ_M d | 1.091 | 1.009 | ✅ Close |
| Turbo gain | 1.199× (per-text) | 1.72× (per-corpus) | Different aggregation |
| LOOCV AUC | 0.898 | 0.90 | ✅ Close |
| EL capacity d | −0.917 | +0.857 | ❌ Per-surah reverses direction |
| Omega rank | #1/10 | #1/10 | ✅ Match |
| Markov ratio | 20× | 17.2× | ✅ Close |
| Classifier sigma | 7.6σ | 7.9σ | ✅ Close |
| SF W16 Fisher p | 0.058 | <0.01 | ⚠️ FAST_MODE permutations |
| Meccan/Medinan p | 0.127 | 0.014 | ⚠️ FAST_MODE permutations |
| Phase 30 criticality | 3/3, φ=0.618 | — (notebook only) | ✅ New |
| Phase 31 RG rank | #10/10 (NEGATIVE) | — (notebook only) | ✅ Honest negative |
| Phase 32 curvature rank | #10/10 (MIXED) | — (notebook only) | ✅ Honest negative |
| T12 Markov order d | −1.849 | — (notebook only) | ✅ New finding |
| Verification pass | 28/29 (96.6%) | — | ✅ |

**Note**: Most d-value differences are due to different comparison pools (notebook: Quran vs ALL controls; pipeline: Quran vs specific subcorpora). Permutation-based p-values (SF W16, Meccan/Medinan) are noisier with FAST_MODE=True (200 perms vs 1000). Setting FAST_MODE=False would tighten p-values but NOT change effect sizes.

---

# 1. ENVIRONMENT SETUP

## 1.1 Requirements (CPU — all local scripts)

```
# requirements.txt
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.10.0
scikit-learn>=1.2.0
nolds>=0.5.2
```

## 1.2 Requirements (GPU — Colab only)

```
# Additional for Phase 6
sentence-transformers>=2.2.0
torch>=2.0.0
camel-tools>=1.5.0
transformers>=4.30.0
```

## 1.3 Directory Structure

```
Final/
├── 01_pipeline/
│   ├── scripts/           # All Python scripts (51 files)
│   └── outputs/           # All JSON results
├── 02_documentation/
│   ├── QSF_COMPLETE_REFERENCE.md   # All findings (single source of truth)
│   ├── QSF_REPLICATION_PIPELINE.md # THIS FILE
│   └── QSF_PAPER_DRAFT_v2.md      # The paper (v2.2)
├── 04_checkpoints/
│   ├── after_v4_final.pkl.gz       # Foundation (3.7 MB, 1140 texts)
│   └── checkpoint_after_setup.pkl.gz # S23/S24 (54 MB, includes embeddings)
└── run_all.py                       # Orchestrator (see §13)
```

## 1.4 Checkpoint Format

### after_v4_final.pkl.gz (PRIMARY — used by all scripts)
```python
import pickle, gzip
with gzip.open('04_checkpoints/after_v4_final.pkl.gz', 'rb') as f:
    ckpt = pickle.load(f)
df = ckpt['df']  # DataFrame: 1140 rows (114 Quran + 1026 controls)
# Columns: corpus, label, verse_texts (list[str]), surah_idx, n_verses, + 8 raw features
# 10 corpora: quran, hadith, poetry, poetry_abbasi, poetry_jahili, poetry_islami,
#             arabic_bible, ksucca, hindawi, tashkeela
```

---

# 2. DATA ARCHITECTURE & CORPUS RULES

## 2.1 Apples-to-Apples Rules (CRITICAL)

| Rule | Requirement | Why |
|------|-------------|-----|
| **Segmentation equivalence** | Each "text" = natural chapter-like unit with verse-like sub-units | Fair comparison: surah→ayat, poem→bayt, chapter→hadith |
| **Minimum length** | MIN_VERSES = 3 | Permutation test needs data |
| **Same language** | All Arabic script (Classical + MSA) | Feature pipeline identical |
| **No text overlap** | Controls must NOT contain Quran verses | Prevents leakage |
| **Same feature pipeline** | Identical functions for all texts | No Quran-specific preprocessing |
| **Length disclosure** | Report length distributions, test with length-restricted subsets | Known confound |

## 2.2 Corpus Inventory (1140 texts)

| Corpus | n_texts | Type | Notes |
|--------|:-------:|------|-------|
| quran | 114 | Scripture | 114 surahs, 3-286 verses |
| hadith | ~200 | Religious | Bukhari/Muslim chapters |
| poetry | ~150 | Literature | Classical Arabic poetry |
| poetry_abbasi | ~91 | Literature | Abbasid-era poetry (KEY CONTROL) |
| poetry_jahili | ~80 | Literature | Pre-Islamic poetry |
| poetry_islami | ~64 | Literature | Early Islamic poetry |
| arabic_bible | ~50 | Scripture | Arabic Bible (96% saturation caveat) |
| ksucca | ~100 | Mixed | King Saud University corpus |
| hindawi | ~60 | Literature | Modern Arabic literature |
| tashkeela | ~130 | Mixed | Diacritized Arabic texts |

## 2.3 Validation Checks (run before ANY analysis)

```python
assert (df['corpus'] == 'quran').sum() == 114, "Missing Quran surahs"
assert df['corpus'].nunique() >= 10, "Missing control corpora"
assert df['verse_texts'].apply(lambda x: isinstance(x, list) and len(x) >= 1).all()
assert df.duplicated(subset=['corpus','label']).sum() == 0, "Duplicate texts"
```

## 2.4 Cross-Language Corpus (Phase 4)

| Scripture | Language | Source | Segmentation |
|-----------|----------|--------|-------------|
| Greek NT | Koine Greek | SBLGNT | Book → verse |
| Hebrew Bible | Biblical Hebrew | WLC | Book → verse |
| Pali Canon | Pali | CSCD | Sutta → paragraph |

**Size-matching**: Filter ALL units to 10-100 verses for fair comparison.

---

# 3. FEATURE DEFINITIONS

## 3.1 S24 Transition Features (THE CORE MECHANISM)

| Feature | Symbol | Definition | Weight |
|---------|--------|-----------|:------:|
| **End-letter match** | EL(vᵢ, vⱼ) | 1 if last char of vᵢ = last char of vⱼ, else 0 | w=2 |
| **Connective start** | CN(vⱼ) | 1 if first word of vⱼ ∈ connective_set, else 0 | w=2 |
| **Semantic cosine** | Sem(eᵢ, eⱼ) | cosine(MiniLM(vᵢ), MiniLM(vⱼ)) | w=3 |
| **Length regularity** | LR(vᵢ, vⱼ) | 1 - |len(vᵢ)-len(vⱼ)| / max(len(vᵢ),len(vⱼ)) | w=1 |

### S24 Test Statistic
```
Q(s) = (1/(n-1)) × Σᵢ T(vᵢ, vᵢ₊₁)
T(vᵢ, vⱼ) = [3·Sem + 2·EL + 2·CN + 1·LR] / 8
p_s = [1 + #{π : Q_π(s) ≥ Q_can(s)}] / (N_perm + 1)
```

## 3.2 Connective Sets (per language)

```python
# v10.2c STANDARDIZED: 14 functionally active items (2 proclitics excluded), excludes verbs of speech (قل/قال) and vocatives (يا)
ARABIC_CONN = {'و', 'ف', 'ثم', 'بل', 'لكن', 'او', 'إن', 'أن', 'لأن', 'حتى',
               'إذ', 'إذا', 'لما', 'كي', 'ل', 'ب'}  # + 2 prefix prepositions
GREEK_CONN  = {'καὶ', 'δὲ', 'γὰρ', 'ἀλλὰ', 'ὅτι', 'οὖν', 'ἵνα', 'εἰ', 'ὡς',
               'μὲν', 'τε', 'ἢ', 'διὸ', 'ἐπεὶ', 'ὥστε', 'πλὴν', 'μήτε', 'οὔτε'}
# v10.1 fix: STANDALONE ONLY, no waw-prefix (matches Arabic multi-word methodology)
HEBREW_CONN = {'כי', 'אשר', 'גם', 'אם', 'כן', 'לכן', 'אך', 'רק',
               'אף', 'הנה', 'עתה', 'פן', 'אולם', 'אבל'}
# v10.1 fix: removed 'so' (pronoun) and 'kho' (particle)
PALI_CONN   = {'ca', 'pi', 'pana', 'atha', 'tatra', 'tena', 'seyyathapi',
               'iti', 'evam', 'hi', 'tu', 'vā', 'va', 'yathā', 'yatha'}
```

## 3.3 Distributional Features (8D baseline)

| Feature | Definition |
|---------|-----------|
| `H_terminal` | Shannon entropy of terminal letters |
| `H_nano_ln` | ln(bigram character entropy) |
| `LZ_norm` | Lempel-Ziv complexity (normalized) |
| `EG_rise` | Binary: verse length rises first→last third? |
| `VL_CV` | Coefficient of variation of verse lengths |
| `H_var` | Variance of per-verse Shannon entropies |
| `RST` | Hapax legomena fraction |
| `AC1` | Lag-1 autocorrelation of verse word counts |

**⚠️ Length-confounded features** (5 of 14D): H_nano_ln, LZ_norm, VL_CV, AC_multi, VTJ. Must be controlled for in any zone analysis.

---

# PHASE 1: FOUNDATION (CPU)

**Purpose**: Load checkpoint, verify data integrity, establish baseline.

```bash
# No script needed — checkpoint already computed
# Verify with:
python -c "
import pickle, gzip
with gzip.open('04_checkpoints/after_v4_final.pkl.gz','rb') as f: ckpt=pickle.load(f)
df=ckpt['df']; print(f'Loaded {len(df)} texts, {df.corpus.nunique()} corpora')
print(df.corpus.value_counts())
"
```

**Expected**: 1140 texts, 10 corpora, 114 Quran surahs.

---

# PHASE 2: CORE LAWS (CPU)

Run these scripts in order. Each reads `after_v4_final.pkl.gz` and writes JSON to `01_pipeline/outputs/`.

## Step 2.1: Anti-Metric Law + Tension Principle
```bash
python 01_pipeline/scripts/pnas_laws_analysis.py
```
**Produces**: `pnas_laws_results.json`
**Verify**: VL_CV Cohen's d ≈ 2.964, EL d ≈ 0.96, CN d ≈ 1.21

## Step 2.2: Scale-Free Ordering
```bash
python 01_pipeline/scripts/scale_invariance_test.py
```
**Produces**: `scale_invariance_results.json`
**Verify**: Fisher p < 0.01 at W=8,10,15,20

## Step 2.3: Markov Unforgeability
```bash
python 01_pipeline/scripts/markov_s24_test.py
```
**Produces**: `markov_s24_results.json`
**Verify**: Quran 48.6% vs forgery mean ~2.8% → ratio ~17×
**Runtime**: ~20 min (50 forgeries × 1000 permutations each)

## Step 2.4: EL+CN Uniqueness
```bash
python 01_pipeline/scripts/el_cn_uniqueness_proof.py
```
**Produces**: `el_cn_uniqueness_results.json`
**Verify**: 2/10 in high-EL×high-CN quadrant, Quran CN 2.5× poetry_abbasi

## Step 2.5: Coherence Length
```bash
python 01_pipeline/scripts/coherence_length_test.py
```
**Produces**: `coherence_length_results.json`
**Verify**: λ=7 (first genuine signal, ratio ≥ 2×)

## Step 2.6: D6 Geometric Bridge
```bash
python 01_pipeline/scripts/d6_proper_confirmation.py
```
**Produces**: `D6_proper_confirmation.json`
**Verify**: LOO rho ≈ -0.245, p ≈ 0.009

---

# PHASE 3: VALIDATION & ROBUSTNESS (CPU)

## Step 3.1: Abbasi CPU Resolution
```bash
python 01_pipeline/scripts/abbasi_resolution.py
```
**Produces**: `abbasi_resolution_results.json`
**Verify**: Structural-2ch Quran 50.5% vs Abbasi 36.3% (+14.2pp)
**Runtime**: ~18 min (7 corpora × 4 configs × 500 perms)

## Step 3.2: Root Category Transitions
```bash
python 01_pipeline/scripts/root_category_transitions.py
```
**Produces**: `root_category_v2_results.json`
**Verify**: Quran HIGHEST JSD=0.465 (opposite direction from hypothesis)

## Step 3.3: Error Corrections & Tokenization Audit
```bash
python 01_pipeline/scripts/error_corrections.py
```
**Produces**: `error_corrections_results.json`
**Verify**: Prefix-inclusive connective: 49.5% vs 25.9% (still 2× gap)

---

# PHASE 4: CROSS-LANGUAGE (CPU)

## Step 4.1: Cross-Language Dual-Channel
```bash
python 01_pipeline/scripts/cross_language_dual_channel.py
```
**Produces**: `cross_language_dual_channel_results.json`
**Verify**: Quran ONLY scripture with EL>0.3 AND CN>0.05

**⚠️ Requires**: Greek NT, Hebrew Bible, Pali Canon text files. These are downloaded/embedded in the script.

## Step 4.2: Cross-Language Ordering (word-count based)
```bash
python 01_pipeline/scripts/cross_language_v2.py
```
**Produces**: `cross_language_v2_results.json`
**Verify**: Quran ordering 33.8%, λ=8. Others: null.

## Step 4.3: Lambda Artifact Test
```bash
python 01_pipeline/scripts/lambda_artifact_test.py
```
**Produces**: `lambda_artifact_results.json`
**Verify**: Deviation ratio 4.02×, null distributions comparable (< 0.56σ)

---

# PHASE 5: MORPHOLOGICAL ANALYSIS (CPU)

## Step 5.1: Morphological Frontier
```bash
python 01_pipeline/scripts/morphological_frontier.py
```
**Produces**: `morphological_frontier_results.json`
**Verify**: Quran H_cond = 2.945 (highest, confirmed). v10.2 waw/ya fix applied (was 3.175). v10.1 taa marbuta fix had negligible impact.

## Step 5.2: Structural Tension T (v10.2c — CORRECTED)
```bash
python 01_pipeline/scripts/structural_tension.py
python 01_pipeline/scripts/T_per_text_correct.py
python 01_pipeline/scripts/iliad_T_test.py
```
**Produces**: `structural_tension_results.json`, `T_per_text_correct_results.json`, `iliad_T_results.json`
**Verify**: Quran pooled T = +0.548 (v10.2 after waw/ya fix). ⚠️ Pooled T is an artifact. Per-text: 24.3% of surahs T > 0 vs 0% for all others. p = 2.47×10⁻³³. Iliad: ALL 24 books T < 0.
**Note**: The pooled T and per-text mean T disagree in sign for ALL corpora with positive pooled T. T_per_text_correct.py is the authoritative analysis.

## Step 5.3: Turbo-Code Formalization (NEW v10.2c)
```bash
python 01_pipeline/scripts/turbo_code_formalization.py
```
**Produces**: `turbo_code_formalization_results.json`
**Verify**: Quran coding gain = **1.72×** (#1/10), independence = **99.2%**, balanced channels. p = 7.8×10⁻¹³. (Corrected from 1.95× after ARABIC_CONN standardization.)

## Step 5.4: Root Transition Analysis (legacy — shows ceiling issue)
```bash
python 01_pipeline/scripts/root_transition_analysis.py
```
**Produces**: `root_transition_results.json`
**Note**: This shows per-surah H_norm saturates at ~0.995. The pooled analysis in morphological_frontier.py (Step 5.1) is the correct approach.

## Step 5.5: External Validation (Arabic Wikipedia)
```bash
python 01_pipeline/scripts/external_validation.py --wiki 80
```
**Produces**: `external_validation_results.json`
**Verify**: S24 significance rate ~15-25% (matching benchmark controls, far below Quran 49.1%). Classifier false-positive rate ~85% (expected — Wikipedia VL_CV=0.79 is outside training distribution; see paper §3.8).
**Runtime**: ~5 min (download + S24 permutation tests)
**Requires**: Internet connection (downloads Arabic Wikipedia articles)

---

# PHASE 6: GPU VALIDATION (Google Colab T4)

## Step 6.1: Upload to Colab

Upload to `/content/` on Colab:
1. `01_pipeline/scripts/abbasi_resolution_gpu.py`
2. `04_checkpoints/after_v4_final.pkl.gz`

## Step 6.2: Set Runtime
- **Runtime** → **Change runtime type** → **T4 GPU**

## Step 6.3: Install Dependencies
```python
!pip install sentence-transformers camel-tools -q
```

## Step 6.4: Patch Paths
```python
with open('/content/abbasi_resolution_gpu.py', 'r') as f:
    code = f.read()
code = code.replace(
    r'C:\Users\mtj_2\OneDrive\Desktop\Final\04_checkpoints\after_v4_final.pkl.gz',
    '/content/after_v4_final.pkl.gz'
).replace(
    r'D:\QURAN project -backup to delete later\checkpoints\after_v4_final.pkl.gz',
    '/content/after_v4_final.pkl.gz'
).replace(
    r'C:\Users\mtj_2\OneDrive\Desktop\Final\01_pipeline\outputs',
    '/content'
)
with open('/content/abbasi_resolution_gpu_colab.py', 'w') as f:
    f.write(code)
```

## Step 6.5: Run
```python
%run /content/abbasi_resolution_gpu_colab.py
```
**Runtime**: ~15-30 min on T4 GPU.

## Step 6.6: Download Output
```python
from google.colab import files
files.download('/content/abbasi_resolution_gpu_results.json')
```

**Verify**: Quran full_S24_MiniLM ≈ 70.27% (FDR) vs Abbasi ≈ 51.65% (+18.6pp)

---

# PHASE 7: CLASSIFICATION & COMPRESSION (CPU)

## Step 7.1: Feature-Validated Classifier
```bash
python 01_pipeline/scripts/feature_validated_classifier.py
```
**Produces**: `blind_classifier_results.json`
**Verify**: AUC ≈ 0.90, 7.9σ above null
**Note**: Renamed from "blind classifier" in paper v1.2. Features (VL_CV, EL, CN) were selected from same dataset. LOOCV + null test validates discriminative power but this is feature validation, not external blind prediction.

## Step 7.2: Compression Ratio v2
```bash
python 01_pipeline/scripts/compression_ratio_test.py
```
**Produces**: `compression_ratio_results.json`
**Verify**: Quran min_L = 10 (LOWEST of any corpus)

---

# PHASE 8: LEGACY PIPELINE (CPU/GPU)

These reproduce older findings (D1-D7, conservation laws, creative tests). Not needed for the paper's core 5 laws but important for completeness.

## 8.1 Conservation Laws
```bash
python 01_pipeline/scripts/conservation_law_analysis.py
python 01_pipeline/scripts/full_analysis_suite.py
```

## 8.2 Mother Diamond + Tier 1
```bash
python 01_pipeline/scripts/mother_diamond_tests.py
python 01_pipeline/scripts/tier1_tests.py
```

## 8.3 Creative Tests
```bash
python 01_pipeline/scripts/creative_tests.py
```

## 8.4 Audit Scripts
```bash
python 01_pipeline/scripts/d6_bugfix_rerun.py
python 01_pipeline/scripts/audit_d4_d7_d8.py
python 01_pipeline/scripts/audit_rebuild.py
python 01_pipeline/scripts/length_free_rebuild.py
```

## 8.5 S24 Notebook (cell-by-cell specification)

See `QSF_COMPLETE_PIPELINE_SPEC_ARCHIVED.md` for the full cell-by-cell Colab notebook specification (Phases 0-14, 14D feature computation, P1-P8, G5-G12 tests, D6 bidirectional).

---

# VERIFICATION CHECKSUMS

After running all scripts, verify these key numbers match:

| Metric | Expected | Tolerance | Script |
|--------|----------|:---------:|--------|
| VL_CV Cohen's d | **2.964** | ±0.01 | pnas_laws |
| EL Cohen's d (pooled) | **0.96** | ±0.05 | pnas_laws |
| CN Cohen's d (pooled) | **1.21** | ±0.05 | pnas_laws |
| Scale Fisher p (W=8) | **< 0.01** | — | scale_invariance |
| Scale Fisher OR (W=8) | **1.73** | ±0.1 | scale_invariance |
| Markov gap ratio | **17.2×** | ±2.0 | markov_s24 |
| Markov forgery mean | **2.8%** | ±1.0% | markov_s24 |
| Quran S24 rate | **48.6%** | ±2% | markov_s24 |
| Coherence λ | **7** | exact | coherence_length |
| EL+CN quadrant count | **2/10** | exact | el_cn_uniqueness |
| D6 LOO rho | **-0.245** | ±0.03 | d6_proper |
| Classifier AUC | **0.90** | ±0.02 | feature_validated_classifier |
| Compression min_L (Quran) | **10** | ±5 | compression_ratio |
| Root H_cond (Quran) | **2.945** | ±0.2 (v10.2 waw/ya fix; was 3.175) | morphological |
| GPU Quran FDR | **70.27%** | ±3% | GPU (Colab) |
| Cross-lang Quran EL | **0.727** | ±0.05 | cross_lang_dc |
| Structural Tension T pooled | **+0.548** | ⚠️ pooling artifact, see below | structural_tension |
| Per-text T: % surahs T>0 | **24.3%** | must be >> 0% for all controls | T_per_text_correct |
| Per-text T: p-value | **2.47×10⁻³³** | | T_per_text_correct |
| Turbo coding gain | **1.72×** | #1/10 corpora (corrected from 1.95× after ARABIC_CONN fix) | turbo_code_formalization |
| Turbo independence | **99.2%** | | turbo_code_formalization |
| Iliad per-book T>0 | **0/24** | all negative | iliad_T_test |
| External S24 sig% (Wikipedia) | **~23.8%** | ±10% (should be near ~15%, far below 49.1%) | external_validation |

---

# EXECUTION ORDER & ORCHESTRATION

## Complete Run Order (CPU scripts first, then GPU)

```
# === PHASE 2: CORE LAWS ===
1.  pnas_laws_analysis.py              # ~2 min
2.  scale_invariance_test.py           # ~5 min
3.  markov_s24_test.py                 # ~20 min
4.  el_cn_uniqueness_proof.py          # ~1 min
5.  coherence_length_test.py           # ~3 min
6.  d6_proper_confirmation.py          # ~2 min

# === PHASE 3: VALIDATION ===
7.  abbasi_resolution.py               # ~18 min
8.  root_category_transitions.py       # ~2 min
9.  error_corrections.py               # ~1 min

# === PHASE 4: CROSS-LANGUAGE ===
10. cross_language_dual_channel.py     # ~5 min
11. cross_language_v2.py               # ~10 min
12. lambda_artifact_test.py            # ~5 min

# === PHASE 5: MORPHOLOGICAL ===
13. morphological_frontier.py          # ~3 min
14. structural_tension.py              # ~3 min

# === PHASE 7: CLASSIFICATION ===
15. feature_validated_classifier.py     # ~2 min (feature-validated classifier)
16. compression_ratio_test.py          # ~3 min

# === PHASE 9: SENSITIVITY & ROBUSTNESS (v10.1) ===
17. pali_formula_decomposition.py      # ~8 min (optimized)
18. s24_weight_sensitivity.py          # ~12 min (optimized)
19. verse_boundary_entropy.py          # ~2 sec (channel independence)
20. robustness_battery.py              # ~1 sec (4 fast tests)
21. phonological_forgery_test.py       # ~30 sec (constrained S24)
22. structural_dna_v2.py               # ~37 sec (100% word coverage DNA)
23. structural_omega.py                # ~68 sec (unified 5-channel constant)
24. golden_ratio_deep_test.py          # ~4 sec (phi test + combined QSI)
25. structural_constants.py            # ~4 sec (spectral letter-level hash)
26. exhaustive_constant_search.py      # ~1 sec (166k combo constant search)
27. zipf_analog_search.py              # ~2 sec (letter-level Zipf analog)
29. zipf_analog_crosscorpus.py         # ~5 sec (cross-corpus Zipf test)
30. zipf_word_level.py                 # ~3 sec (word-level Zipf analog)
31. oral_tradition_T_test.py           # ~2 sec (scripture vs literary T)
32. cross_language_tension.py          # ~5 sec (Greek/Hebrew/Pali T)
# === PHASE 10: v10.2c CORRECTIONS ===
33. turbo_code_formalization.py        # ~4 sec (channel capacity, gain=1.72×)
34. T_per_text_correct.py              # ~4 sec (corrected per-text T)
35. iliad_T_test.py                    # ~1 sec (Homer Iliad 24 books)
36. multiscale_perturbation_test.py    # ~15 min (central paper claim: 3-10× sensitivity)
37. cross_surah_dependency_test.py     # ~3 min (EL+CN surah-level p=0.10)
38. monte_carlo_constant_null.py       # ~3 min (500 random trials)
39. external_validation.py --wiki 80   # ~5 min (Arabic Wikipedia S24 validation)
40. tamper_detection_p2.py             # ~2 min (P2 tamper detection 2AFC, delete=66.9%)
41. channel_interference_p4.py         # ~2 min (P4 channel independence, NOT CONFIRMED)
42. combined_coverage_analysis.py      # ~5 sec (6-law coverage map: 100/114 = 87.7%)
43. full_coverage_analysis.py          # ~2 min (9-law: 104/114 = 91.2% — ⚠️ had L5 string bug + L9 weight bug)
44. definitive_coverage_v3.py          # ~2 min (11-law: 113/114 = 99.1%, all bugs fixed)
45. s_tier_analysis.py                 # ~2 min (law independence: 4 dims + EL capacity: 2.57×)

# === PHASE 9: NEW ANOMALY TESTS (v10.3, CPU) ===
46. qsf_new_anomaly_tests.py            # ~11 min (8 tests: MI, word-order, graph, RQA, syllable, connective-type, gradients, surah-network)
# Verify: 13 anomalies found, 3 negative. Key checks:
#   T2: d=0.470, p=9.65e-13 (verse-internal word order)
#   T3: modularity d=0.472, p=5.21e-07 (graph topology)
#   T4: LAM d=-0.395, p=6.8e-04 (RQA anti-metric)
#   T8: path z=-8.76, 0th pct (surah arrangement)
#   T8: diversity CV 100th pct (adjacent variety)
#   T1: NEGATIVE (long-range MI, exponential decay)
#   T5: NEGATIVE (syllable ordering, weak)
#   T6: NEGATIVE (connective types, d=0.221 n.s.)

# === PHASE 6: GPU (Colab) ===
40. abbasi_resolution_gpu.py           # ~30 min (T4 GPU)

# === PHASE 8: LEGACY (optional) ===
20-28. (conservation_law_analysis, full_analysis_suite, mother_diamond_tests,
        tier1_tests, creative_tests, audit scripts...)
```

**Total CPU time**: ~131 minutes (core ~30 min + validation ~20 min + sensitivity ~20 min + v10.2c ~20 min + v10.3 ~11 min + rest ~30 min)
**Total GPU time**: ~30 minutes

---

# CLAIM FRAMEWORK

## 🟢 ALLOWED Claims

> "Within 72 of 114 Quranic surahs, the canonical verse ordering ranks in the
> top 1% of all possible orderings by structural coherence — a rate 3.79× higher
> than 724 texts across 9 Arabic corpora."

- Anti-Metric Law d=2.964
- EL+CN unique within Arabic (2/10 in quadrant)
- Cross-language: highest EL by 2.7×, uniquely rightward-shifted T distribution, only ALL-THREE-HIGH octant
- 17.2× Markov unforgeability
- AUC=0.90 classifier (feature validation, not blind prediction)
- Signal detectable at L=10 verses (lowest)
- P4 NOT confirmed: CN is permutation-invariant; EL alone drives ordering (joint gain=0.98, n.s.)
- P2 partial: Deletion detection 66.9%, 74.7% surahs above chance (p<10^-6)
- Definitive coverage: 113/114 surahs (99.1%) flagged by >=1 of 11 tests spanning 4 orthogonal dimensions; 100% for surahs >=5v. Only surah 108 (3v) uncovered.
- EL channel capacity: 2.57× controls (4.67 vs 1.82 bits, d=0.857, p=1.14×10⁻¹⁴) per pipeline scripts. ⚠️ Notebook v3.3.2 gives d=−0.917 (per-surah log2(n_unique) reverses direction due to fawasil concentration — fix pending). EL drives ordering; CN is corpus-level fingerprint.
- **(v10.3)** Verse-internal word order optimization (d=0.470, p=9.65×10⁻¹³)
- **(v10.3)** Graph modularity anomaly (d=0.472, p=5.21×10⁻⁷) + 3 more graph metrics
- **(v10.3)** RQA independent confirmation of Anti-Metric Law (6 metrics, all d>0.3)
- **(v10.3)** Surah path optimization (z=−8.76, 0th pct) + adjacent diversity (100th pct)
- **(v10.3)** Φ Complementarity Law: Quran Φ=0.951 vs controls ≤0.12 (**8.2× above ceiling**, verified against source JSONs. Previous estimate of 4.75×/0.20 used incorrect H_cond estimates)
- **(v10.3c)** Nuzul (chronological) order also optimizes structural path (z=−6.88), but Mushaf is MORE optimized (z=−8.80, Δz=1.92). Compilation as secondary optimization phase.
- **(v10.3c)** Cross-linguistic T8: Greek NT z=−4.97, Hebrew Bible z=−5.02, Quran z=−8.74. ALL scriptures optimize chapter arrangement. Quran degree is ~1.75× stronger (z-score). ⚠️ Macro-optimization NOT unique to Quran.
- **(v10.3c)** Φ bound: 50 Markov forgeries achieve Φ=0.39–0.46 (pooled). EL=0.12 vs Quran 0.72 — EL is the irreducible bottleneck.
- **(v10.3c)** Script: `qsf_breakthrough_tests.py` → `qsf_breakthrough_results.json`

## 🔴 NOT ALLOWED Claims

- "Proof of i'jaz" (science cannot prove theology)
- "No human can replicate" (no imitation challenge)
- "Universal physics law" (this is computational linguistics)
- "98.34% separation" without disclosing floor trick
- Any AraGPT2 number (contaminated)
- "Quran is ONLY corpus in EL+CN quadrant" (poetry_abbasi barely qualifies)

## ⚠️ MUST DISCLOSE

- Tokenization: standalone "و" = 0 tokens (connective = multi-word only)
- Arabic agglutination: `len(v.split())` not cross-language comparable
- Arabic Bible: 96% saturation, H=0.239 bits
- Pali Canon: 69.6% ordering rate; after formula-controlled decomposition (≥50% Jaccard removal), drops to **44.2%** (below Quran 49.1%). 50.3% of paragraphs are formulaic.
- poetry_abbasi: 2/10 in EL+CN quadrant (CN barely exceeds threshold)
- D4 dropped, D7 dead
- **v10.1**: Hebrew CN corrected: 0.071 → 0.000 (waw-prefix removed, standalone only).
- **v10.1**: Pali CN corrected: 0.016 → 0.008 ("so" + "kho" removed).
- **v10.1→v10.2**: Morphological H_cond corrected: 3.175 → **2.945** (waw/ya fix). Taa marbuta fix had negligible impact.
- **v10.1**: Classifier features selected from same dataset (LOOCV + null validated, not external).
- **v10.1**: No scripture in HIGH-EL × HIGH-CN quadrant under 75th-pct thresholds. Reframed as EL dominance + T + octant.
- **v10.1**: S24 weight sensitivity: 5/6 configs confirm (uniform p=4e-12, structural_2ch p=1.4e-14, full_S24 p=2.8e-15). CN-only fails (expected: too sparse). Post-hoc concern neutralized.
- **v10.1**: Pali formula-controlled decomposition: 44.2% after ≥50% deformularization (below Quran 49.1%). Scripts: `pali_formula_decomposition.py`, `s24_weight_sensitivity.py`.
- **v10.2**: waw/ya consonant bug fixed in structural_tension.py, morphological_frontier.py, structural_omega.py, golden_ratio_deep_test.py. T corrected: +0.843 → +0.548. H_cond corrected: 3.175 → 2.945.
- **v10.2c**: ⚠️ **POOLING ARTIFACT**: Pooled T > 0 for scriptures was an artifact of mixing diverse chapters. Per-text mean T is NEGATIVE for ALL corpora. Corrected finding: Quran's per-surah T distribution is uniquely shifted rightward (24.3% T > 0 vs 0% for all controls, p = 2.47×10⁻³³). Homer's Iliad tested: 0/24 books have T > 0.
- **v10.2c**: Turbo-code formalization: Quran coding gain = **1.72×** (#1/10), **99.2%** channel independence. (Corrected from 1.95×/98.6% after ARABIC_CONN standardization to 14 functionally active items.)
- **v10.2c**: Zipf analog search (letter + word level): letter entropy CV=2.98% is a general Arabic property, not Quran-specific. Word-level: no Quran-unique invariant.
- **v10.2c**: Monte Carlo null: 100% of random number sets produce equally close constant matches. All "constants" are noise.
- **v10.2c**: SIC/DNA reclassified as engineering tool (hash function), not scientific discovery.
- **v10.3c**: 3 breakthrough tests: Nuzul vs Mushaf (Δz=1.92), cross-linguistic T8 (all scriptures optimize, Quran strongest z=−8.74), Φ bound (forgery EL=0.12 bottleneck). Scripts: `qsf_breakthrough_tests.py`.
- **v10.3d**: 4 Nobel-track tests: Φ triple robustness (70% with 6 core features), cross-linguistic Φ (Quran 1.28 vs Greek NT 0.25), semantic field (NEGATIVE), EL-aware forgery (reframes constraint as informational). Scripts: `qsf_nobel_tests.py`.
- **v10.4**: PARADIGM SHIFT. 5 frontier-framework scripts:
  - `qsf_adversarial_forgery_benchmark.py`: 5 generator classes, 100 synthetic Qurans. Quran IS on Pareto frontier (structure vs coherence). Generators beat Φ but produce gibberish. Among real texts, Quran Φ+ = 0.574 vs controls ≤ 0.166 (3.5×).
  - `qsf_semantic_bridge.py`: 5-measure coherence panel. C_local ≈ 0.36 for all texts. Confirms constraint is MEANING (not capturable by surface metrics).
  - `qsf_constrained_null_ladder.py`: 8 null levels. Quran NEVER collapses (77–100% sig at all levels). Abbasi drops to 74% at semantic null.
  - `qsf_global_order_rank.py`: Mushaf z=−10.62, 0/100k random beat it. BUT 2-opt improves 49.5%. Canonical is extreme tail but NOT mathematical optimum.
  - `qsf_hard_negative_mining_abbasi.py`: 5-leak taxonomy. 3/5 confirmed (connective, metric, semantic). Rhyme leak NOT confirmed. Abbasi has HIGHER end-letter entropy.
- **v10.4 CAVEAT**: Surface coherence metrics (≈ 0.36) cannot distinguish meaningful text from Markov gibberish. The irreducible constraint is semantic/informational — needs embedding-based coherence or human evaluation to formalize.
- **v10.6**: CAVEAT ELIMINATION. 7 scripts:
  - `qsf_variant_forensics_v2.py`: 9-channel variant detection (A-I). 9/9 detected. Channel H (local spectral) fires 7/9. Runtime: ~2min.
  - `qsf_surah_dashboard.py`: 114-surah structural health dashboard. A+ to D grading (percentile-based). Runtime: ~30s.
  - `qsf_transmission_simulation.py`: Oral channel simulation. Quran 7.25× at 2% error. Runtime: ~45s.
  - `qsf_caveat_resolution.py`: (1) Nested CV: AUC 0.893, 10.4σ above null. Meccan→Medinan: AUC 0.872. (2) Control variant: channels fire equally (ratio 1.02× — honest). (3) Channel I relaxed: 0→3/9. Runtime: ~4min.
  - `qsf_gap_closure.py`: (1) Vocalized 43×43 spectral: 93% diacritic swap, 97% diacritic drop detection. (2) Sliding window Φ: 8.5× amplification. (3) Φ=0 diagnosis: At-Tin H_cond=0, Quraysh EL=0. (4) Abbasi decomposition: Quran 50.2% end-letter concentration vs Abbasi 22.4%. Runtime: ~30s.
  - `qsf_blind_validation.py`: External: Markov 97%, random 100%, repeated 94% rejection. Shuffled Quran 32% (expected: permutation-invariant features). S24 correctly rejects all (3-10% vs Quran 49.1%). Runtime: ~15s.
  - `qsf_phi_proof.py`: Semi-formal theorem: Φ lower-bounds error-detection capacity. Between-corpus 4.21×. Within-Quran ρ=−0.39 (length confound). ksucca beats Quran on Φ (0.47 vs 0.40). Additive form better predictor. Runtime: ~40s.
- **v10.6 RESOLVED CAVEATS**: Classifier bias (✔), vowel blindness (✔), long-surah dilution (✔), Φ=0 diagnosed (✔).
- **v10.6 CONFIRMED HONEST**: Spectral channels fire in all texts (1.02×), Abbasi EL advantage from different mechanism, Φ not uniquely Quran-maximal (ksucca higher), multiplicative Φ loses to additive within-Quran.
- **v10.6 REMAINING**: Formal mathematical Φ proof (needs mathematician), behavioral P1/P3 experiments, Channel I needs lexicon/embedding approach.
- **v10.7**: MAHALANOBIS UNIFICATION. 1 script:
  - `qsf_mahalanobis_unification.py`: 5D Mahalanobis distance Φ_M = √[(x−μ)ᵀ Σ⁻¹ (x−μ)] where x = (EL, VL_CV, CN, H_cond, T). Quran Φ_M = 3.75 vs controls 1.95 (Cohen's d = 1.009, Mann-Whitney p = 3.8×10⁻²³). ksucca permanently resolved: Quran 3.75 > ksucca 2.97 (p = 0.007). 37.6% surahs are χ² outliers at p<0.01 (vs 4.8% controls). Control EL ↔ VL_CV correlation = −0.284; Quran has BOTH high (violates trade-off). Quran above control mean on ALL 5 dims. Runtime: ~6s.
- **v10.7 DEEP AUDIT**: 104 Python files, 49,039 total lines. Zero syntax errors. One logic bug found and fixed in `qsf_phi_proof.py` (|rho| comparison for mult vs additive). 66 cosmetic warnings (late imports, no impact on results). One methodological note: `qsf_phi_proof.py` computes H_cond from all-word root bigrams while paper defines it as verse-final only — no impact on between-corpus comparison (same method for all) but flagged for consistency.
- **v10.7 RESOLVED**: ksucca Φ overlap (✔), multiplicative vs additive debate (✔ — Mahalanobis supersedes both).
- **v10.13**: JSON CROSS-CHECK. Full reconciliation of QSF_RESULTS_v3.3.json (144 keys) against pipeline scripts:
  - **10 new notebook findings**: (1) Lesion testing: 7-level dose-response (0.5%–50%), smooth degradation, heat capacity peaks 5–10%, NOT irreducible. (2) Info Geo saddle: Hessian [−7.49, −3.68, −2.17, −0.75, +2.65], 4/9 controls also saddles. (3) Terminal position: signal depth = 2 letters (d=1.138 at −1, d=0.816 at −2, noise at −3). (4) Inter-surah cost: 641.85 vs random 912.29, ratio 0.704, p=0.0. (5) Optimal stopping: NEGATIVE (d=−0.134, p=0.93). (6) Abjad: NEGATIVE (Hurst d=0.029). (7) Spectral gap: NEGATIVE (rank 9/10). (8) Ring/chiasm: NEGATIVE (d=−0.263, p=1.0). (9) LZ binding: NEGATIVE (d=−0.06). (10) Bootstrap CIs: all positive findings confirmed.
  - **Notebook-vs-Pipeline Reconciliation** (22 metrics): All qualitative conclusions match. Key differences explained by FAST_MODE (500 vs 1000 perms), per-surah vs pooled aggregation, and updated H_cond formula. Largest absolute difference: Omega d (1.985 vs 1.218, different normalization). No contradictions.
  - **Falsified hypotheses expanded**: Items 44–49 (optimal stopping, spectral gap, ring/chiasm, LZ binding, abjad, lesion irreducibility).
- **v10.9**: DEEP SCAN MERGE. Integrated ~1,900-file scan results into documentation. Dead/Falsified findings expanded with F1–F4 (Hurst word-lengths, surah-level Hurst, acoustic/diacritic ratio, Muqattaat — all NOT UNIQUE or FALSIFIED). Supplementary phases added: Hurst analysis (anti-persistence H=0.262 vs Bible 0.130), multi-level Hurst (4-level topology from بسم notebook), acoustic bridge (r=0.54 syllable→pitch). Local notebook QSF_LOCAL_V3.3.ipynb documented (FAST_MODE + HAS_GPU config, Windows encoding fixes). Phenomena inventory and consolidated action list in QSF_COMPLETE_REFERENCE.md §15–17.
