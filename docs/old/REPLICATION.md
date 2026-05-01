# QSF Replication Pipeline — Methods & Operations Guide

**Version**: 3.0 (clean-data rebuild, 2026-04-17)
**Supersedes**: `QSF_REPLICATION_PIPELINE.md`, `PREREGISTRATION_v10.18.md`, `REMAINING_GAPS_v10.19.md`, `QSF_AUDIT_REPORT_v10.15.md`, `QSF_COMPLETE_REFERENCE.md`

**Companion to**: `docs/PAPER.md` (results and discussion), `docs/FINDINGS_SCORECARD.md` (ranked findings)

---

## 1 Quick start

```powershell
# From the repo root:
python -X utf8 -u -m src.clean_pipeline

# Total runtime ≈ 102 s on a laptop.
# Produces results/CLEAN_PIPELINE_REPORT.{json,md}.

# To step through interactively with plots:
jupyter notebook notebooks/QSF_REPRODUCE.ipynb
```

Required Python packages are in `requirements.txt`; the key ones are `numpy`, `scipy`, `pandas`, `scikit-learn`, `camel-tools==1.5.7`, `openpyxl`, `matplotlib`.

---

## 2 Philosophy: one entry point, no checkpoints

The v2 pipeline relied on `after_v4_final.pkl.gz` as its cached master file. An audit found two corpus-level corruptions inside that pickle (see `docs/PAPER.md §10.1`). The v3 pipeline **never pickles intermediate data**. Every test reads from raw text files on every run, after passing the G1–G5 sanity gate (`src/verify_corpora.py`). This is slower (102 s vs 30 s) but eliminates the single largest class of silent failures.

```
┌──────────────────────────────────────────────────────────────┐
│  Raw files  →  Loader  →  Sanity gate  →  Feature extraction │
│  (data/corpora/)   (src/raw_loader.py)   (src/verify_corpora) │
│                                          (src/roots.py +      │
│                                           src/features.py)    │
│                              │                                │
│                              ▼                                │
│                   23 tests (src/extended_tests*.py)           │
│                              │                                │
│                              ▼                                │
│                  results/CLEAN_PIPELINE_REPORT.json           │
└──────────────────────────────────────────────────────────────┘
```

No module reads from `results/`, `archive/`, or any pickle; every datum originates in `data/`.

---

## 3 Repository layout

```
Quran/
├── README.md                        entry point with reproduction commands
├── CHANGELOG.md                     audit journey, v2 → v3 transition
├── requirements.txt
├── notebooks/
│   └── QSF_REPRODUCE.ipynb          single auditable notebook, all 23 tests
├── src/
│   ├── __init__.py
│   ├── raw_loader.py                read data/corpora/<lang>/* -> Unit objects
│   ├── verify_corpora.py            G1-G5 sanity gate
│   ├── roots.py                     CamelTools root extraction, cached
│   ├── features.py                  5-D feature extraction (EL, VL_CV, CN, H_cond, T)
│   ├── extended_tests.py            T5-T15
│   ├── extended_tests2.py           T16-T23
│   ├── clean_pipeline.py            single entrypoint, runs all 23 tests
│   └── cache/
│       └── cameltools_root_cache.pkl.gz  3.1k entries, ~4 MB
├── docs/
│   ├── PAPER.md                     the paper (results, discussion, retractions)
│   ├── REPLICATION.md               this file
│   ├── FINDINGS_SCORECARD.md        ranked 35-row findings table
│   ├── ADIYAT_CASE.md               Sūra 100 sharpshooter case
│   └── ADIYAT_ANALYSIS_AR.pdf       Arabic typeset appendix
├── data/
│   └── corpora/
│       ├── ar/                       Arabic (8 corpora)
│       │   ├── quran_bare.txt
│       │   ├── quran_vocal.txt       (vocalised, used only by T23)
│       │   ├── poetry_raw.csv
│       │   ├── poetry.txt            (unused in pipeline; retained for reference)
│       │   ├── ksucca.txt
│       │   ├── arabic_bible.xlsx
│       │   ├── hadith.json
│       │   ├── hindawi.txt
│       │   └── tashkeela.txt         (unused; retained for reference)
│       ├── he/
│       │   └── tanakh_wlc.txt        (Westminster Leningrad Codex)
│       ├── el/
│       │   ├── iliad_perseus.xml
│       │   └── opengnt_v3_3.csv
│       └── wiki/                     (80 Arabic Wikipedia articles, planned D13)
├── results/
│   ├── CLEAN_PIPELINE_REPORT.json   latest run, SHA-256-pinned corpora
│   ├── CLEAN_PIPELINE_REPORT.md     human-readable summary
│   └── figures/                      notebook-generated plots
├── arxiv_submission/                 synced paper + supplementary
└── archive/                          everything pre-v3 is here
    ├── 2025-10_legacy_scripts/       28 scripts that produced v2 numbers
    ├── 2025-10_legacy_output/        23 JSONs from v2 runs
    ├── 2025-legacy_notebooks/        QSF_LOCAL_V3.3, QSF_MASTER_REPLICATION
    ├── 2025-legacy_fixes/            early audit run scripts (run01-run06)
    ├── 2026-04-17_audit_rounds/      audit tables, verdict tables
    ├── 2026-04-17_docs_merged/       10 docs that were merged into PAPER + REPLICATION
    └── 2026-04-17_intermediate_output/  F05-F09 JSONs from intermediate runs
```

---

## 4 Data integrity (SHA-256 pinning)

Every `clean_pipeline.py` run computes and stores a SHA-256 fingerprint of each corpus file in `results/CLEAN_PIPELINE_REPORT.json.corpus_fingerprint`. Current pins (first 12 hex chars):

| Corpus | SHA-256 [:12] | Units | Role |
|---|---|:-:|---|
| quran | `e5e6ccb9083c` | 114 | target |
| poetry_jahili | `328a4cac108b` | 133 | Arabic ctrl |
| poetry_islami | `baf8244d1307` | 465 | Arabic ctrl |
| poetry_abbasi | `ec5c5160a7fb` | 2,823 | Arabic ctrl |
| ksucca | `b2604438bd5c` | 41 | Arabic ctrl |
| arabic_bible | `2467b701ae1f` | 1,183 | Arabic ctrl |
| hadith_bukhari | `c623a7431b51` | 95 | Arabic ctrl |
| hindawi | `afab15ce9b2c` | 74 | Arabic ctrl |
| iliad_greek | `25f8f65e55c1` | 24 | cross-lang |

**If any pin changes and the findings change, the corpus has been tampered with.** This check would have detected the v2 pickle corruption in one run.

---

## 5 Feature extraction (details)

### 5.1 Diacritic stripping

Arabic harakat (short vowels, shadda, sukun) are stripped by `src/features._strip_d()` before computing EL, CN, H_cond. Codepoints dropped: U+0610..U+061A, U+064B..U+065F, U+0670, U+06D6..U+06ED. The consonantal rasm is the feature substrate.

### 5.2 End-letter rhyme rate (EL)

For each unit's verse list v₁, …, v_n, EL = (1/(n-1)) × #{i : terminal-letter(v_i) == terminal-letter(v_{i+1})}. "Terminal letter" = last Arabic letter after stripping punctuation and diacritics.

### 5.3 Verse-length CV

VL_CV = σ(#tokens(v_i)) / μ(#tokens(v_i)).

### 5.4 Connective-start rate (CN)

For each verse, check whether its first token after diacritic-stripping is in the 13-word set

```
و ف ثم إذ إذا لما حين قد لقد إن أن أما فأما
```

(wa, fa, thumma, idh, idha, lamma, hina, qad, laqad, inna, anna, amma, fa-amma). CN = fraction of verses that do.

### 5.5 Conditional root-bigram entropy (H_cond)

Let the token sequence for a unit be t_1, ..., t_N (concatenating all verses). Replace each t_k by primary_root(t_k) from CamelTools, dropping tokens with no analysis. Let P(r | r') be the empirical bigram transition. Then

H_cond = − Σ_r' P(r') · Σ_r P(r|r') log₂ P(r|r')

Implementation in `src/features.py::h_cond_roots`.

### 5.6 Structural tension T

T = mean over verses of |Δω(v_i)|, where ω(v) = (#tokens(v))^(1/2) − (mean token length in v). This is an "orthogonal-feature tension" and was the most empirically distinctive feature on clean data: Quran 39.7 % of verses have T > 0; all non-scripture controls are at 0.0–0.1 %.

---

## 6 Test catalogue

Each test has a dedicated function; all return a dict that is aggregated into `results/CLEAN_PIPELINE_REPORT.json`.

### 6.1 Core (T1-T6) — src/clean_pipeline.py

| Name | Function | Purpose | Expected |
|---|---|---|---|
| T1 | `test_anti_metric` | VL_CV Quran vs Arabic pool, Cohen's d | d > 0.8 |
| T2 | `test_phi_m` | Mahalanobis separation | d > 2.0 |
| T3 | `test_hcond_by_corpus` | H_cond ranks | (reports only) |
| T4 | `test_omega_rebuild` | Ω with control-mean denominators | Quran rank #1 |
| T5 | `test_tautology_check` | canon-wins > perturbed | Quran > 75 %, controls < 75 % |
| T6 | `test_hcascade` | F cross-scale fractality | d > 0.5 |

### 6.2 Extensions (T7-T15) — src/extended_tests.py

| Name | Function | Purpose | Expected |
|---|---|---|---|
| T7 | `test_el_cn_dual` | EL, CN, G_turbo ranks, I(EL;CN) | ranks #1; I small |
| T8 | `test_path_minimality` | path-z, adjacent-diversity pctile | z < −2 |
| T9 | `test_markov_unforgeability` | bigram root LM shuffle-test | z > 10 |
| T10 | `test_t_distribution` | %T > 0 per corpus | Quran >> controls |
| T11 | `test_bigram_sufficiency` | H₃/H₂ ratio | Quran lowest |
| T12 | `test_cv_phi_m` | 10-fold CV Φ_M | min d > 0.5 |
| T13 | `test_meccan_medinan` | sub-analysis F | both > 1 (retracted) |
| T14 | `test_bootstrap_omega` | 1,000-bootstrap Ω | 95 % > 2 |
| T15 | `test_classifier_auc` | 5-fold logistic AUC | > 0.85 |

### 6.3 Last-mile (T16-T23) — src/extended_tests2.py

| Name | Function | Purpose | Expected |
|---|---|---|---|
| T16 | `test_scale_free_s24` | Fisher-combined p across W | p < 0.01 at all W |
| T17 | `test_multi_scale_perturbation` | letter/word/verse gap | all gaps > 0 for Quran |
| T18 | `test_verse_internal_word_order` | shuffle within verse | Quran 100 % farther |
| T19 | `test_rqa_anti_metric` | LAM on verse-length seq | Quran low |
| T20 | `test_structural_forgery_p3` | rhyme-swap collapse rate | Q > ctrl (not reproduced) |
| T21 | `test_cross_language_iliad` | Iliad lang-agnostic path-z | Iliad z ≈ 0 |
| T22 | `test_rd_times_el` | H_cond × EL product | Quran 3-38× ctrl |
| T23 | `test_harakat_channel_capacity` | H(harakat \| rasm) | sub-maximal |

---

## 7 Pre-registration (inherited from v10.18)

The v2 pre-registration (`archive/2026-04-17_docs_merged/PREREGISTRATION_v10.18.md`) specified three pass / fail rules:

- **Rule A**: Φ_M d vs Arabic pool ≥ 0.8 → **PASS (d = 6.34)**
- **Rule B**: Meccan AND Medinan both F > 1 → **FAIL (F_M = 0.80, F_D = 0.84)**
- **Rule C**: Bootstrap Ω ≥ 95 % > 2.0 → **PASS (100 % > 2.0)**

Rule B fails on clean data. This is a pre-registered negative result and is reported as such in `docs/PAPER.md §10` point 5. The F > 1 threshold is retracted.

---

## 8 Formal-proof gap status (updated April 2026)

| Gap | Version 2 status | Version 3 status |
|:-:|---|---|
| G1 | Bennett bound for heavy-tailed Φ_M | CLOSED — Hill α ≥ 1.8 on all 5 features |
| G2 | 5-channel MI independence | CLOSED — max normalised MI ≤ 0.3 |
| G3 | Hessian PD | **FALSIFIED BY MATH** — H = 2·Σ⁻¹ is PD by construction |
| G4 | Exponential-family generalisation | OPEN |
| G5 | γ(Ω) = a + b·Ω linear form | **FALSIFIED BY MATH** — algebraic identity |

Two of the five "closures" were mathematical tautologies (see `docs/PAPER.md §10` point 6). v3 reports **2 / 5 genuinely closed**.

---

## 9 Reproduce a single claim

Each composite-ranked finding in `docs/FINDINGS_SCORECARD.md` maps to exactly one test function. To reproduce, e.g., the AUC finding in isolation:

```python
from src import raw_loader, features, extended_tests
corpora = raw_loader.load_all(include_extras=True)
feats = {...}   # extract with features.features_5d per unit
print(extended_tests.test_classifier_auc(feats))
```

The `notebooks/QSF_REPRODUCE.ipynb` has one cell per test with this pattern, so readers can execute tests independently.

---

## 10 Environment

- Python ≥ 3.11
- CamelTools 1.5.7 (with MSA-calima-s31 DB installed by `camel_data --install morphology-db-msa-s31`)
- NumPy 1.26+, SciPy 1.11+, scikit-learn 1.3+, pandas 2.0+, openpyxl 3.1+

On first run, `src/roots.py` builds a CamelTools root cache (~4 MB) at `src/cache/cameltools_root_cache.pkl.gz`. This is reusable across invocations.

---

## 11 Development workflow

- **Add a new test**: write `test_<name>(corpora, feats, …) -> dict` in `src/extended_tests2.py`, then add a single block in `src/clean_pipeline.py::run_clean_pipeline`.
- **Add a new corpus**: drop the raw file under `data/corpora/<lang>/`, add a loader in `src/raw_loader.py`, call it from `load_all()`. The sanity gate will catch gross problems automatically.
- **Extend features**: add to `src/features.py::features_5d()` return vector (and consider renaming to `features_nd`). Update `BAND_A_LO, BAND_A_HI` only if the new feature changes length sensitivity.

---

## 12 Known remaining work

| # | Item | Priority |
|:-:|---|:-:|
| 1 | Rhyme-swap (T20) — re-implement v2's exact metric to see whether 93 % vs 36 % reproduces | med |
| 2 | Cross-language — run 5-D lang-agnostic on Hebrew Tanakh + Greek NT | med |
| 3 | Arabic Wikipedia validation — D13 external test on `data/corpora/wiki/` | low |
| 4 | Gap G4 — information-geometric / exponential-family proof | low (needs coauthor) |
| 5 | Qira'at / waqf (E1, E2, E4) — require additional corpora not in repo | low |

None of these would move the composite ≥ 55 findings downward.
