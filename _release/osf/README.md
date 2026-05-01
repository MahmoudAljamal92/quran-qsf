# Quranic Structural Fingerprint (QSF)

> A reproducible, SHA-256-locked, deterministic-seed characterisation of the Quran as a **multivariate statistical outlier against classical-Arabic prose baselines**, with cross-tradition replications in 6 alphabets and 5 language families. 70+ positive findings, 63 honest retractions, 2 deployable tools (IFS fractal portrait + 8-channel Authentication Ring), project-closure audit at 0 CRITICAL.

**Current version**: **v7.9-cand patch H V3.30** (project closure, 2026-05-01).

---

## Start here (reading order)

1. **`docs/THE_QURAN_FINDINGS.md`** — **the single-document extraction** of every positive finding, every retraction, the 2 tools, reproducibility map, and AI-disclosure. ~50 KB, ~18 pages, self-contained. **Reviewer-ready; read this first.**
2. **`docs/PUBLISHING_PLAN.md`** — how to release to GitHub + arXiv + OSF + OpenTimestamps, dual-license (AGPL + CC-BY-SA), theft protection, AI-disclosure template, 10-day executable checklist.
3. **`results/audit/TOP_FINDINGS_AUDIT.md`** — project-closure audit of 8 top headline numbers, independently re-run from raw data. All PASS. Zero fabrication.
4. `docs/README.md` — navigation map for the rest of the `docs/` folder.

---

## Headline numbers (all reproduce to ≤10⁻⁴ drift from raw data; see `results/audit/TOP_FINDINGS_AUDIT.md`)

| Finding | Locked value | Meaning | Exp |
| ------- | ------------ | ------- | --- |
| median verse-final-letter entropy **H_EL** | **0.9685 bits** | Below 1-bit categorical universal; Quran is the unique 11-pool corpus below this threshold | `exp124_one_bit_threshold_universal` |
| median modal-letter rate **p_max** | **0.7273** | 73 % of Quran verses end in nūn (ن) — the dominant rāwī | `scripts/_phi_universal_xtrad_sizing.py` |
| channel utilisation **C_Ω = 1 − H_EL/log₂ 28** | **0.7985** | Quran uses ~80 % of the Arabic alphabet's Shannon capacity for rhyme; peers 27 – 58 % | `exp115_C_Omega_single_constant` |
| alphabet-corrected gap **D_max = log₂ 28 − H_EL** | **3.84 bits** | Quran is the unique corpus with D_max ≥ 3.5 bits across 6 alphabets + 6 traditions | `exp124c_alphabet_corrected_universal_with_rigveda` |
| F-Universal invariant (Shannon–Rényi-∞ gap) | Quran **5.316 bits**; pool mean **5.75 ± 0.11 bits** at CV **1.94 %** | Universal across 11 oral canons in 5 unrelated language families | `exp122_zipf_equation_hunt` |
| Mushaf-as-Tour coherence **L_Mushaf** | **7.5929** (null min 7.7380; z = −5.14; **p ≤ 10⁻⁷** at 10M perms) | Canonical 1→114 order is the empirically-rarest joint F81+F82 permutation | `exp176_mushaf_tour` + `exp179_F85_escalation_10M` |
| Multifractal fingerprint (HFD, Δα, cos_short_long) | (0.9653, 0.510, 0.208); **pool-z 4.20, LOO-z 22.59** | 3-axis geometric fingerprint unique to Quran in 7-corpus pool | `exp177_quran_multifractal_fingerprint` |
| Authentication Ring composite score | **1.000** (8/8 PASS) on Quran; **0.556** on hindawi; **0.333** on poetry | 8-channel unified forgery / authenticity tool; composite ∈ [0, 1] | `exp183_quran_authentication_ring` |
| T² Φ_M Mahalanobis separation (legacy; band-A) | **3 557.34** (bootstrap 95 % CI [3 127, 4 313]); AUC = **0.998** | 5-D Mahalanobis distance Quran vs 2 509 Arabic controls | `notebooks/ultimate/QSF_ULTIMATE.ipynb` |
| Total SHA-256-locked scalars | **127** | integrity-pinned in `results/integrity/results_lock.json` | — |
| Honest retractions catalogued | **63** (R1 – R63) + **27+ failed-null pre-regs** | append-only ledger | `docs/RETRACTIONS_REGISTRY.md` |

## Citation (pending public deposit)

```
Aljamal, M. (2026). The Quranic Structural Fingerprint —
  A Reproducible Information-Theoretic Characterisation of a Multivariate Outlier
  Against Classical-Arabic Prose Baselines, with an 8-Channel Authentication Ring.
  v7.9-cand patch H V3.30 (project closure, 2026-05-01).
  OSF DOI: 10.17605/OSF.IO/N46Y5 (see docs/PUBLISHING_PLAN.md §2.1).
  arXiv: PENDING (see docs/PUBLISHING_PLAN.md §2.2).
  Code SHA-256 (deposit): 2f90a87a0fa0ac42057dbd6785e591355b075a14ab0bfd52cc49d396ca7f0205
```

## Reproduce any headline number from raw data

```powershell
# Environment
python -m pip install -r requirements.txt

# Project-closure audit (8 top findings, ~30 s)
python scripts/_audit_top_findings.py

# Authentication Ring (8-channel, self-test on locked Quran — expect 8/8 PASS, composite 1.000)
python experiments/exp183_quran_authentication_ring/run.py data/corpora/ar/quran_bare.txt

# IFS fractal portrait (~60 s; produces 3 PNGs)
python experiments/exp182_quran_ifs_fractal/run.py

# Quick-path 31-test pipeline (~112 s)
python -X utf8 -u -m src.clean_pipeline

# Full-path Ultimate-1 (~70 min FAST / 3.5 h NORMAL)
jupyter lab notebooks/ultimate/QSF_ULTIMATE.ipynb
```

Every command is deterministic (seed = 20260501). Every output has an SHA-256 integrity lock. First run builds a CamelTools root cache (~4 MB, ~60 s); subsequent runs complete in ~30 s.

## AI-disclosure

This project was produced in heavy collaboration with large-language-model coding assistants (Windsurf / Cascade using Anthropic Claude-class models Opus-4.x / Sonnet-4.x and Kimi-2.6). **No locked scalar relies on unaudited AI output**: every headline number was independently re-verified by re-running the underlying experiment from raw data at project closure. The project's methodological claim is that locked scalars are reproducible by any honest auditor — human or AI — because every step is deterministic and every scalar is cryptographically pinned. See `docs/PUBLISHING_PLAN.md §6` for the full disclosure and `docs/THE_QURAN_FINDINGS.md §9` for the scientific statement.

---

## Earlier-version headline (V3.14, preserved for continuity)

**V3.14 (2026-04-29 night) — CATEGORICAL 1-BIT UNIVERSAL F76 + LDA UNIFICATION F77 PARTIAL**: **F76** (`exp124_one_bit_threshold_universal::PASS_one_bit_categorical_universal`) — Quran is the **unique** literary corpus in the locked 11-pool with verse-final-letter Shannon entropy `H_EL < 1 bit` (Quran 0.969 bits, gap to runner-up Pāli 1.121 bits, ratio 2.16×); first **categorical universal** in the project. **F77 PARTIAL** — supervised LDA unified formula full-pool Quran \|z\|=10.21 / Fisher J=10.43; LOO not robust at N=11.

**V3.13 (2026-04-29 evening) — FIRST ZIPF-CLASS UNIVERSAL INFORMATION-THEORETIC REGULARITY**: systematic search over 585 candidate closed-form relations returned **F74** (sqrt(H_EL) distinguishes Quran at \|z\| = 5.39) and **F75** (H_EL + log₂(p_max·A) = 5.75 ± 0.11 bits at CV 1.94 % across 11 corpora in 5 unrelated language families).

Full version history patch-by-patch in `CHANGELOG.md`.

---

## What you're looking at

- **The paper** — `docs/PAPER.md` (v7.5). Full-scale manuscript with every number re-derived from raw data.
- **The reference handbook** — `docs/REFERENCE.md` (v7.5). Rankings, methodology, deprecations, 127 locked scalars, all cross-references.
- **Ranked findings + roadmap** — `docs/reference/findings/RANKED_FINDINGS.md` (v1.1, v7.5 sync). 40 findings with strength %, provenance, and the specific experiments that would elevate each toward 100 %.
- **Adiyat case study (English)** — `docs/reference/adiyat/ADIYAT_CASE_SUMMARY.md` (v7.5). Single paper-grade answer to the 864-variant question.
- **Adiyat case study (Arabic, plain-language)** — `docs/reference/adiyat/ADIYAT_AR.md` (v7.5 sync, includes exp50 cross-corpus result and the boxed 1-of-865 framework summary).
- **Adiyat case study (Arabic, technical)** — `docs/old/ADIYAT_ANALYSIS_AR.md`. Full Arabic long-form analysis (v7.1–v7.3 technical record, preserved for provenance).
- **Deep-scan meta-report** — `docs/DEEPSCAN_ULTIMATE_FINDINGS.md`. 2026-04-21 inventory: blessed findings, unpromoted gems, law candidates, retractions.
- **Changelog** — `CHANGELOG.md`. Full v2 → v7.8-candidate audit and release history.
- **Repository map** — see the **Canonical documentation**, **Legacy doc-name index**, **Integrity files**, and **Where to look when…** appendix sections below.
- **Pipeline** — `src/` (8 modules, 1 entrypoint `src.clean_pipeline`, 31 tests).
- **Notebooks** — `notebooks/ultimate/QSF_ULTIMATE.ipynb` (Ultimate-1 run-of-record) + `QSF_ULTIMATE_2.ipynb` (Ultimate-2 edit-detection).
- **Experiments sandbox** — `experiments/exp{NN}_*/run.py`. 34 write-isolated experiments (read-only checkpoints, guarded output path, integrity self-check). See `experiments/README.md`.
- **CLI / UI scorer** — `tools/qsf_score.py` + `tools/qsf_score_app.py`. Stand-alone 5-D scorers (see `tools/README.md`).
- **Data** — `data/corpora/` (9 raw corpora in Arabic / Hebrew / Greek + 80 Arabic Wikipedia articles, all SHA-256-pinned in `results/integrity/corpus_lock.json`).
- **Integrity** — `results/integrity/` (corpus + code + results + names-registry + pre-registration + FDR audit, all SHA-pinned).
- **Run-of-record outputs** — `results/ULTIMATE_REPORT.json`, `results/ULTIMATE_SCORECARD.md`, `results/CLEAN_PIPELINE_REPORT.json`, `results/checkpoints/*.pkl`, `results/experiments/expNN_*/*.json`.
- **Frozen submission snapshot** — `arxiv_submission/` (v3.0 from 2026-04-17; `arxiv_submission/paper.md` carries a top-of-file **DEPRECATED banner** pointing to `docs/PAPER.md` v7.5 as the current paper; see `arxiv_submission/STATUS.md`).
- **Audit trail** — `archive/` (every pre-v7 document, ad-hoc scripts, legacy notebooks, historical results — preserved, do not edit).

---

## Headline findings (v7.9-cand patch E, 2026-04-26)

| Metric | Value | Source |
|---|---|---|
| Φ_M Mahalanobis separation, **all 114 Quran surahs** (no Band gate) vs 4 814 Arabic+cross-tradition ctrl | **T² = 3 685.45**, AUC = 0.9932; bootstrap 95 % CI **[3 127, 4 313]** (median 3 693) → STABLE; band-A T² = 3 557 inside CI (statistically indistinguishable) | `expP7_phi_m_full_quran` (v7.9-cand patch B) + `expP12_bootstrap_t2_ci` (patch E) |
| Φ_M Mahalanobis separation (68 Band-A Quran vs 2 509 Arabic ctrl) | **T² = 3 557.34**, d = 6.66, perm p ≤ 5·10⁻³, MW p = 1.75·10⁻⁴⁴ | `PAPER.md §4.1`; locked 3 557.34 ± 5.0 (patch B integrity-hole closure) |
| EL one-feature classifier, **all 114 surahs** | **AUC = 0.9813**, EL boundary = 0.314, `PASS_arabic_only` (Pali drop); **LOCO min AUC = 0.9796** (drop poetry_abbasi) → ROBUST_STRONG | `exp104_el_all_bands` + `expP13_loco_el` (patch E) |
| EL classifier holdout: **Quran vs Hadith Bukhari** (formal pre-registration) | **AUC = 0.9718**, MW p = 4.05·10⁻³², bootstrap 95 % CI [0.947, 0.992] → PASS_STRONG | `expP10_hadith_N1_prereg` (patch E) |
| EL classifier vs **Arabic saj' (Maqamat al-Hariri)** — direct PNAS-reviewer challenge | Maqamat: EL = 0.1013, p(ن) = 0.066, top letter ه (p_max = 0.147); **AUC = 0.9902, MW p = 2.39·10⁻³⁸ → QURAN_DISTINCT_FROM_SAJ** | `expP16_maqamat_hariri` (patch E) |
| EL classifier under **5 alternative riwayat** (Warsh, Qaloun, Douri, Shuba, Sousi) | All 5 keep **AUC ≥ 0.97**; T² drift in [-10.5 %, +3.4 %]; EL drift in [-3.4 %, -0.4 %]; 3 of 5 pass strict 3-condition test (Duri, Shuba, Sousi); Warsh has largest drift | `expP15_riwayat_invariance` (patch E) |
| ن-dominance: Quran p(ن) = **0.5010** vs next Arabic ≤ **0.109** (ن-frequency specifically) | **4.6× ratio** for ن-rate; **6.7× hadith Bukhari**; for **dominant-letter-of-any-kind** the ratio is **2.43×** (Quran p_max 0.501 vs poetry_islami p_max(ا) 0.206); Greek Iliad p_max(ν) = 0.274 (Greek nominative ending) | `expP9.NEW2 / N7` (patch C); `expP14_cross_script_dominant_letter` (patch E) |
| Bible ن rate (audit patch D correction; was claimed 14.7 %) | **7.53 %** of 31 083 verse-finals → **42.6-pp gap** is verse-end-selection | `audit_patch.json::patch_4_bible_noon_rate_correction` |
| Brown joint p (EL + R3 + J1 + Hurst), conservative ρ=0.5 prior | **2.95·10⁻⁵** (audit-corrected from 3.28·10⁻⁵) | `audit_patch.json::patch_3_brown_synthesis` |
| Brown joint p, **empirical R** (patch-E re-derivation with v7.9-cand individual p-values) | **5.24·10⁻²⁷** (~22 orders of magnitude tighter than the conservative-prior version) | `expP11_brown_empirical_corr` (patch E) |
| Shannon i.i.d. floor for EL on 28-letter Arabic abjad (theorem) | EL_iid_floor = Σ p̂(letter)² = **0.295**; Quran's actual EL = **0.720** → **structural rhyme excess = +0.425** (≈ 3.6× the next-highest control's excess); to reach EL = 0.72 by i.i.d. sampling alone, p_max ≥ **0.85** required (Quran has only 0.501) → +0.425 must be carried by adjacent-verse rhyme correlations | `expP18_shannon_capacity_el` (patch E) |
| Classifier AUC (nested 5-fold CV, 5-D, Band-A) | **0.998** | `PAPER.md §4.2` |
| (T, EL) 2-feature sufficiency meta-CI | AUC = **0.9971 ± 0.0006** across 25 seed·fold | `exp36_TxEL_seed_metaCI` |
| R12 gzip NCD length-controlled residual | γ = **+0.0716**, 95 % CI [+0.066, +0.078], p ≈ 0 (≈ 7.4 % at fixed length, rounded) | `exp41_gzip_formalised` |
| Adiyat 864-variant compound detection | **99.1 %** fire at ctrl-p95; 0/864 exceed canonical Φ_M | `exp43_adiyat_864_compound` |
| Two-letter enumeration (72 900 variants FAST) | **100 %** compound detection | `exp45_two_letter_746k` |
| Perturbation scale hierarchy | d(word)=**2.45** > d(verse)=1.77 > d(letter)=0.80 | `PAPER.md §4.3` |
| Cross-scripture path optimality (R3) | z(Q)=−8.92, z(Tnk)=**−15.29**, z(NT)=−12.06, z(Iliad)=+0.34 | `exp35_R3_cross_scripture_redo` |
| Cross-corpus emphatic audit (v7.5) | Quran **1.15 %** vs poetry_jahili **9.50 %** / poetry_abbasi **4.83 %** → `H2_QURAN_SPECIFIC_IMMUNITY` | `exp50_emphatic_cross_corpus` |
| 6-D Hotelling gate for `n_communities` (v7.5) | T²_6D = 3 823.59 **<** 4 268.81 gate → **SIGNIFICANT BUT REDUNDANT** | `exp49_6d_hotelling` |
| %T > 0 (Quran vs max 0.10 % controls; T = H_cond − H_el per `src/features.py`) | **39.7 %** | `PAPER.md §4.5` |
| Harakat channel capacity (Arabic-textology constant) | H(harakat|rasm) = **1.964 bits** | `PAPER.md §4.9` |
| Total SHA-256-locked scalars | **127** | `results/integrity/results_lock.json` |
| Honest retractions preserved as methodological asset | **47** (canonical ledger; 28 highlighted in `RANKED_FINDINGS §5`) | `docs/reference/findings/RETRACTIONS_REGISTRY.md` |

See `docs/reference/findings/RANKED_FINDINGS.md` for all 40 findings ranked by strength-to-science % with the specific experiments needed to reach 100 %.

---

## Quick start

```powershell
# 1. Clone / download, then from the repo root:
python -m pip install -r requirements.txt

# 2. Quick pipeline (raw data → 31 tests → report in ~112 s)
python -X utf8 -u -m src.clean_pipeline

# 3. Full Ultimate-1 run-of-record (~70 min FAST mode)
jupyter lab notebooks/ultimate/QSF_ULTIMATE.ipynb

# 4. Ultimate-2 edit-detection layer
jupyter lab notebooks/ultimate/QSF_ULTIMATE_2.ipynb

# 5. Single-text scorer (file input)
python -X utf8 tools/qsf_score.py --file path/to/arabic.txt
```

First run builds a CamelTools root cache (~4 MB, ~60 s). Subsequent runs complete in ~30 s.

---

## Repository layout

```
Quran/
├── README.md                           (this file ; entry point + repo map appendix)
├── CHANGELOG.md                        full v2 → v7.8-candidate audit + release history
├── requirements.txt
├── docs/                               current canonical documentation
│   ├── PAPER.md                        v7.5 manuscript
│   ├── QSF_COMPLETE_REFERENCE.md       v7.5 reference handbook
│   ├── RANKED_FINDINGS.md              v1.1 — 40 findings + roadmap to 100 %
│   ├── ADIYAT_CASE_SUMMARY.md          v7.5 single-page Adiyat answer (English)
│   ├── ADIYAT_AR.md                    plain-language Arabic Adiyat doc (v7.5 sync)
│   ├── DEEPSCAN_ULTIMATE_FINDINGS.md   2026-04-21 deep-scan meta-report
│   └── old/                            pre-v7 drafts + quarantined legacy docs (each carries a DEPRECATED banner)
├── src/                                core pipeline
│   ├── raw_loader.py                   reads data/corpora/<lang>/*
│   ├── verify_corpora.py               G1–G5 sanity gate
│   ├── roots.py                        CamelTools root extraction, cached
│   ├── features.py                     5-D features (EL, VL_CV, CN, H_cond, T)
│   ├── extended_tests.py               T5–T15
│   ├── extended_tests2.py              T16–T23
│   ├── extended_tests3.py              T24–T31
│   ├── extended_tests4.py              T32+ (2026-04)
│   ├── clean_pipeline.py               entrypoint: raw → 31 tests → report
│   └── cache/                          CamelTools root cache (auto-populated)
├── notebooks/
│   └── ultimate/
│       ├── QSF_ULTIMATE.ipynb          Ultimate-1 run-of-record
│       ├── QSF_ULTIMATE_2.ipynb        Ultimate-2 edit-detection
│       ├── _build.py                   deterministic Ultimate-1 regenerator
│       ├── _build_ultimate2.py         deterministic Ultimate-2 regenerator
│       ├── _audit_check.py             77-marker regression sentinel
│       └── README.md                   full-pipeline operation guide
├── experiments/                        34 write-isolated experiments
│   ├── README.md                       sandbox rules + integrity protocol
│   ├── _lib.py                         read-only loader + output guard + self-check
│   ├── _ultimate2_helpers.py           Ultimate-2 shared utilities
│   ├── ultimate2_pipeline.py           R2–R11 + MASTER implementations
│   └── exp{01..47}_*/                  one folder per experiment
├── data/
│   └── corpora/
│       ├── ar/                         Arabic corpora (9 files, ~25 MB)
│       ├── he/                         Hebrew Tanakh (~5.5 MB)
│       ├── el/                         Greek Iliad + NT (~46 MB)
│       └── wiki/                       80 Arabic Wikipedia articles
├── results/
│   ├── ULTIMATE_REPORT.json            127 locked scalars, Ultimate-1 run-of-record
│   ├── ULTIMATE_SCORECARD.md           human-readable scorecard
│   ├── CLEAN_PIPELINE_REPORT.json      31-test quick-path report
│   ├── checkpoints/                    SHA-pinned pickles + _manifest.json
│   ├── experiments/expNN_*/            per-experiment JSONs + self-check receipts
│   ├── integrity/                      4 locks + pre-registration + FDR audit
│   └── figures/                        6 diagnostic figures (generated)
├── scripts/                            small utility scripts
│   ├── gem_scanner.py                  satellite-scan for lost-gem finding IDs
│   └── _verify_orphan_findings.py      verify claim IDs against registry
├── tools/                              stand-alone 5-D scorers
│   ├── qsf_score.py                    CLI
│   ├── qsf_score_app.py                Streamlit UI
│   └── README.md
├── arxiv_submission/                   frozen v3.0 submission snapshot (see STATUS.md)
└── archive/                            everything pre-v7 + ad-hoc scripts (do not edit)
```

---

## The v2 â†’ v7.5 story in one paragraph

In April 2026 a forensic audit found that v2's pipeline silently corrupted two control corpora (Arabic Bible, Ksucca) inside a cached pickle; four numerical claims were inflated by hardcoded Î© denominators; two "closed" formal-proof gaps (G3, G5) were mathematical tautologies; and the heuristic root extractor matched only 21 % of a hand-annotated gold set vs CamelTools 1.5.7 at 63 %. The clean-data rebuild (v3–v6) hardened the pipeline with a four-manifest SHA-256 integrity protocol, pre-registration, nested CV, and band-A length matching. v7 (April 2026) added the **Ultimate-2 edit-detection layer** (11 channels R1–R11, two hostile-audit rounds, R2 sliding-window and R3 cross-scripture both PASS pre-registered targets). v7.3 added **R12 gzip NCD** (length-controlled Î³ = +0.0716, p â‰ˆ 0) and closed the Adiyat 864-variant single-letter question at paper grade. v7.4 closed **two-letter** (100 % compound detection, `exp45`) and characterised the **emphatic-class residual** — full-mode `exp46` on all 114 surahs gives 1.1 % overall and **0 % for voiceless stops tta/ta and qaf/kaf**, an R1 blind spot (the v7.4 FAST mode's 31.3 % headline was a 120-sample-null artefact, now retracted in `PAPER.md Â§4.30`). v7.4+ (2026-04-21) ported the archive Gem #3 verse-graph modularity test (`exp48`, d = +0.937 on n_communities, 4/6 metrics fire, PROMOTE verdict pending 6-D Hotelling). **v7.5 (2026-04-21 evening)** closed three resolution experiments: the **6-D Hotelling gate** (`exp49`) ruled `n_communities` **SIGNIFICANT BUT REDUNDANT** (TÂ²_6D = 3 823.59 < 4 268.81, so the 5-D Î¦_M already spans that axis); the **cross-corpus emphatic audit** (`exp50`) returned **H2_QURAN_SPECIFIC_IMMUNITY** (poetry_jahili 9.50 %, poetry_abbasi 4.83 % vs Quran 1.15 %, retracting the v7.4 "Arabic-structural" framing); and the **poetry_islami sensitivity** (`exp51`) confirmed exp48 as **STABLE** under the corrected pool (Î”d = +0.027). The **v7.5.1 doc-reconciliation patch** (this revision, 2026-04-21) tightened `T = H_cond âˆ’ H_el` in `PAPER.md Â§3.1`, normalised Î³ = +0.0716 everywhere, annotated Â§4.31 as closed by Â§4.32, disambiguated T29 `phi_frac = âˆ’0.915` from legacy `T13_phi_frac = 0.618`, and added DEPRECATED banners on `arxiv_submission/paper.md`, `docs/old/PAPER.md`, and `docs/old/QSF_REPLICATION_PIPELINE.md`. Across all versions: 127 scalars SHA-256-locked, **50 honest retractions** as of v7.9-cand patch E (canonical `RETRACTIONS_REGISTRY.md`; 28 originally highlighted in `RANKED_FINDINGS §5`), 130+ sandbox experiments. Full release history in `CHANGELOG.md`.

---

## Canonical documentation (as of v7.7)

| Doc | Path | Role |
|---|---|---|
| Project state dashboard | `docs/reference/findings/01_PROJECT_STATE.md` | Current claim-control dashboard ; standing / partial / retracted / pending status for headline claims |
| Paper | `docs/PAPER.md` | Full manuscript (v7.7 ; includes §4.35 LC3-70-U) |
| Reference handbook | `docs/REFERENCE.md` | Rankings, methodology, 57 tolerance-gated + 127 total scalars |
| Ranked findings + roadmap | `docs/reference/findings/RANKED_FINDINGS.md` | 43 findings with strength % + path to 100 % |
| Adiyat / authentication master | `docs/reference/adiyat/03_ADIYAT_AND_AUTHENTICATION.md` | Current Adiyat status including `exp95`, `exp105`, `exp106`, Tier 3 gate, OOD limitations |
| Adiyat case (English) | `docs/reference/adiyat/ADIYAT_CASE_SUMMARY.md` | Single paper-grade Adiyat answer |
| Adiyat case (Arabic, plain) | `docs/reference/adiyat/ADIYAT_AR.md` | Arabic summary with boxed خلاصة (v7.5.1) |
| Adiyat case (Arabic, technical) | `docs/old/ADIYAT_ANALYSIS_AR.md` | Preserved technical Arabic (pre-v7.5) |
| Opportunity backlog | `docs/reference/sprints/OPPORTUNITY_TABLE_DETAIL.md` | 1 030-line tiered backlog (S / A / B / C / D / E) with 2026-04-25 closures |
| Submission readiness | `docs/reference/sprints/SUBMISSION_READINESS_2026-04-25.md` | 5 publishable packages (P1–P3, P7) ; venue ladder ; decision points (§4.4 LOCKED C1 2026-04-25) |
| 2026-04-24 audit memo | `docs/reference/sprints/AUDIT_MEMO_2026-04-24.md` | E7 confound + B14 / B15 / B16 patches |
| Cross-tradition findings | `docs/reference/sprints/CROSS_TRADITION_FINDINGS_2026-04-25.md` | 8 cross-tradition experiments ; LC2 R3 SUPPORT + LOO 8/8 |
| External-AI handoff pack | `docs/reference/handoff/2026-04-25/` | 7-file self-contained snapshot for external review |
| Release history | `CHANGELOG.md` | v2 → v7.8-candidate |
| Pre-registration (v10.18) | `results/integrity/preregistration.json` | Frozen 2026-04-18 |
| Pre-registration addendum (v7.3) | `arxiv_submission/preregistration_v73_addendum.md` | Post-hoc code-state lock for v7.3 tests |
| OSF deposit checklist | `docs/reference/prereg/OSF_UPLOAD_CHECKLIST.md` | 15-min upload procedure for the v7.3 OSF DOI |

---

## Legacy doc-name index

If you are looking for one of these older names, it is either quarantined under `docs/old/` (superseded), in `arxiv_submission/supplementary/` (frozen v3.0 snapshot), or archived under `archive/`. **Nothing was deleted** — every legacy name resolves below.

| Legacy name | Where it lives now |
|---|---|
| `docs/REPLICATION.md` | `arxiv_submission/supplementary/REPLICATION.md` (frozen v3.0) |
| `docs/FINDINGS_SCORECARD.md` | `arxiv_submission/supplementary/FINDINGS_SCORECARD.md` (frozen v3.0) — superseded by `docs/reference/findings/RANKED_FINDINGS.md` |
| `docs/ADIYAT_CASE.md` | `arxiv_submission/supplementary/ADIYAT_CASE.md` (frozen v3.0) — superseded by `docs/reference/adiyat/ADIYAT_CASE_SUMMARY.md` |
| `docs/AUDIT_CORRECTIONS_2026-04-18.md` | `docs/old/` (superseded by v5 / v6 / v7 audits in `archive/audits/`) |
| `docs/QSF_PAPER_DRAFT_v2.md` | `docs/old/` |
| `docs/QSF_REPLICATION_PIPELINE.md` | `docs/old/` |
| `docs/QSF_AUDIT_REPORT_v10.15.md` | `docs/old/` |
| `docs/QSF_FORMAL_PROOF.md` | `docs/old/` (gaps G3, G5 now falsified ; see `PAPER.md §4.13`) |
| `docs/QSF_FORMAL_PROOF_GAPS_CLOSED.md` | `docs/old/` |
| `docs/QSF_SHANNON_ALJAMAL_THEOREM.md` | `docs/old/` (retracted as tautology ; see `RANKED_FINDINGS.md §5`) |
| `docs/QSF_EPIGENETIC_LAYER.md` | `docs/old/` |
| `docs/PREREGISTRATION_v10.18.md` | `docs/old/` (current is `results/integrity/preregistration.json`) |
| `docs/REMAINING_GAPS_v10.19.md` | `docs/old/` |
| `notebooks/QSF_REPRODUCE.ipynb` | `arxiv_submission/supplementary/QSF_REPRODUCE.ipynb` (frozen v3.0) — current is `notebooks/ultimate/QSF_ULTIMATE.ipynb` |
| Any audit-round file `AUDIT_*.md` | `archive/audits/` (Ultimate-1 + Ultimate-2 rounds 1–2) |
| Any `QSF_*_v10.*` manuscript | `docs/old/` |
| `LOST_GEMS_AND_NOBEL_PATH.md` | `archive/LOST_GEMS_AND_NOBEL_PATH.md` |
| `LAW_CANDIDATES_ASSESSMENT.md` | `archive/LAW_CANDIDATES_ASSESSMENT.md` |
| `HOW_TO_CONTINUE.md` | `archive/HOW_TO_CONTINUE.md` (thread-survival guide) |
| `MASTER_FINDINGS_REPORT.md` | `archive/deep_scan_results/MASTER_FINDINGS_REPORT.md` |
| `docs/MASTER_01_FINDINGS_AND_BACKLOG.md` | `archive/2026-04-25_consolidation_pass2/` (archived 2026-04-25) |
| `docs/MASTER_02_AUTHENTICATION.md` | `archive/2026-04-25_consolidation_pass2/` |
| `docs/MASTER_04_ROADMAP_AND_SUBMISSION.md` | `archive/2026-04-25_consolidation_pass2/` |
| `docs/_INDEX_CARD.md` | `archive/2026-04-25_consolidation_pass2/` (superseded by `docs/README.md` — the 1-page nav card) |
| `docs/DEEPSCAN_ULTIMATE_FINDINGS.md` | `archive/2026-04-25_consolidation/DEEPSCAN_ULTIMATE_FINDINGS.md` (superseded by `docs/reference/sprints/OPPORTUNITY_TABLE_DETAIL.md`) |
| `docs/OPPORTUNITY_SCAN_2026-04-22.md` | `archive/2026-04-25_consolidation/OPPORTUNITY_SCAN_2026-04-22.md` (strict subset of OPPORTUNITY_TABLE_DETAIL) |
| `docs/SCAN_2026-04-21T07-30Z/` (8 files) | `archive/2026-04-25_consolidation/SCAN_2026-04-21T07-30Z/` (absorbed into `CHANGELOG.md §[7.6]` reconciliations R1–R13) |
| `PROJECT_MAP.md` (root) | **MERGED into this README on 2026-04-26** as the four appendix sections you are reading right now. See `CHANGELOG.md` for the merge entry. |

---

## Integrity files

The locks under `results/integrity/` are the project's tamper-evidence layer. **Never edit any of these manually** — they are regenerated by the pipeline.

| Lock | What it protects |
|---|---|
| `corpus_lock.json` | SHA of every raw corpus (blocks silent data tampering) |
| `code_lock.json` | SHA of every notebook cell + `src/*.py` |
| `results_lock.json` | 59 expected-value / tolerance / verdict triples (57 original + 2 v7.6 6-D Hotelling) |
| `names_registry.json` | Whitelist of every legal finding ID (T, D, S, G, L, E, R, F) |
| `checkpoints/_manifest.json` | Per-pickle SHA (refuse-to-deserialise on drift) |
| `headline_baselines.json` | ±5 % envelope around `Phi_M_hotelling_T2` and `Phi_M_perm_p_value` |
| `preregistration.json` | Pre-registered tests A, B, C (frozen 2026-04-18) |
| `fdr_coverage_audit.json` | Benjamini–Hochberg family + in / out status |

**Docs-level integrity artefacts** (human-readable, not machine locks):

| Doc | What it protects |
|---|---|
| `docs/reference/findings/RETRACTIONS_REGISTRY.md` | Canonical single source of truth for all **47** retracted / falsified / deprecated claims across the project. Append-only. Re-openings get a new row with `[REOPENED]` prefix. |
| `archive/2026-04-25_consolidation/MANIFEST.json` | Cryptographic ledger for the 2026-04-25 docs/ consolidation: pre-move + post-move SHA-256 + size + reason + successor-file pointers for every archived file. Self-verifying via `Get-FileHash` re-check. |
| `archive/2026-04-25_consolidation/COVERAGE.md` | Human-readable section-level mapping: every heading of every archived file → new canonical location. |
| `docs/reference/audits/EXECUTION_PLAN_AND_PRIORITIES.md` | 20-task gap-closure tracker. **CLOSED 2026-04-23**: all 20 tasks executed + audited ; 17 shipped PASS / PARTIAL + 3 pre-reg NULL closures ; 0 HIGH / 1 MED / 24 LOW cumulative audit flags. |
| `docs/reference/audits/ZERO_TRUST_AUDIT_2026-04-22.md` | Tier 1 + §4.36 audit — independence correction, manifest drift, cross-doc verdict sync. |
| `docs/reference/audits/ZERO_TRUST_AUDIT_TIER2_2026-04-23.md` | Tier 2 audit (E5–E9): 0 HIGH / 0 MED / 4 LOW flags ; 7/7 pinned-artefact hashes match. |
| `docs/reference/audits/ZERO_TRUST_AUDIT_TIER3_2026-04-23.md` | Tier 3 audit (E10–E13, Adiyat 864): 0 HIGH / 0 MED / 4 LOW. |
| `docs/reference/audits/ZERO_TRUST_AUDIT_TIER4_2026-04-23.md` | Tier 4 audit (E15 / E16 / E17): 0 HIGH / 0 MED / 4 LOW. |
| `docs/reference/audits/ZERO_TRUST_AUDIT_TIER5_2026-04-23.md` | Tier 5 + E14 closure audit: 0 HIGH / 0 MED / 8 LOW. **Plan closure audit.** |
| `docs/reference/handoff/2026-04-25/06_CROSS_DOC_AUDIT.md` | 2026-04-25 / 04-26 cross-doc audit (10 findings: A1–A11 incl. version drift, retraction count, §4.4 T_alt → C1 LOCKED, git-topology foot-gun A11). |

---

## Where to look when…

| Question | Go to |
|---|---|
| **"I just opened the project after a gap, where do I start?"** | **`docs/README.md`** (1-page nav card) then **`docs/PROGRESS.md`** (everything-synthesis) |
| "What does finding X claim?" | `docs/PAPER.md §4` or `docs/REFERENCE.md §3` |
| "How strong is finding X and what would make it stronger?" | `docs/reference/findings/RANKED_FINDINGS.md` |
| "What did v2 / v3 / v5 / v6 / v7 change?" | `CHANGELOG.md` |
| "Is there a universal law?" | `docs/reference/findings/RANKED_FINDINGS.md §0` + `archive/LAW_CANDIDATES_ASSESSMENT.md` + `docs/reference/sprints/SUBMISSION_READINESS_2026-04-25.md §8` |
| "What's the current status of the Adiyat case?" | `docs/reference/adiyat/03_ADIYAT_AND_AUTHENTICATION.md` (with §2.5 paradigm-stage updates) |
| "How do I reproduce the paper numbers?" | `README.md` §Quick start (above) |
| "How do I add a new experiment?" | `experiments/README.md` |
| "How do I add a new corpus?" | `README.md` §Testing and extension (below) |
| "What findings have been retracted?" | **`docs/reference/findings/RETRACTIONS_REGISTRY.md`** (canonical **50-entry** registry; R47 added 2026-04-23, R48–R49 patch B, R50 patch E) |
| "What are the lost gems?" | `archive/LOST_GEMS_AND_NOBEL_PATH.md` + `docs/reference/findings/RANKED_FINDINGS.md §3 Tier D` |
| "What's the OSF deposit fingerprint?" | `arxiv_submission/osf_deposit_v73/osf_deposit_manifest.json` |
| "What was Ultimate-1 vs Ultimate-2?" | `notebooks/ultimate/README.md` |
| "What is in `archive/2026-04-25_consolidation/`?" | `archive/2026-04-25_consolidation/README.md` (recovery protocol) + `MANIFEST.json` + `COVERAGE.md` |
| "What's the submission plan?" | `docs/reference/sprints/SUBMISSION_READINESS_2026-04-25.md` (5 publishable packages) |
| "Are there open decisions or blockers?" | `docs/reference/handoff/2026-04-25/05_DECISIONS_AND_BLOCKERS.md` (Q1 §4.4 LOCKED C1 ; Q2 OSF upload pending ; Q3-Z6 git topology — see audit `A11`) |

---

## Testing and extension

- **Add a new test**: write `test_<name>(corpora, feats, …) -> dict` in `src/extended_tests{2,3,4}.py`, register in `src.clean_pipeline.run_clean_pipeline`, add an entry to `results/integrity/names_registry.json`.
- **Add a new experiment**: create `experiments/expNN_<name>/run.py` using the template in `experiments/README.md` (read-only loader, `safe_output_dir`, `self_check_begin/end`). Output goes to `results/experiments/expNN_<name>/` and cannot leak.
- **Add a new corpus**: drop raw file in `data/corpora/<lang>/`, add loader in `src/raw_loader.py`, call from `load_all()`. The G1–G5 gate auto-rejects contamination.
- **Swap root extractor**: only `src/roots.py` depends on CamelTools; all other modules call `primary_root()`.

**Do NOT** edit files inside `notebooks/ultimate/QSF_ULTIMATE*.ipynb`, `results/checkpoints/`, `results/integrity/`, `results/ULTIMATE_REPORT.json`, `results/ULTIMATE_SCORECARD.md`, `results/CLEAN_PIPELINE_REPORT.json`, or anything under `archive/`. Those are SHA-pinned run-of-record artefacts.

---

## Citing

Work in progress; cite as:

> Aljamal, M. (2026). *The Quranic Structural Fingerprint — A Reproducible 5-Dimensional Characterisation of the Quran as a Multivariate Outlier Against Classical-Arabic Prose Baselines, with Integrity-Locked Replication*. v7.7 (paper-grade) / v7.8-candidate, `docs/PAPER.md`.

---

## License

- **Code** (`src/`, `notebooks/`, `experiments/`, `tools/`, `scripts/`): MIT.
- **Corpora** (`data/corpora/`): each subject to its upstream licence; see individual `data/corpora/<lang>/README.md` where present.
- **Docs** (`docs/*.md`): CC-BY 4.0.
