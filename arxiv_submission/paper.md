# The Quranic Structural Fingerprint (QSF)

> **⚠ DEPRECATED FOR SUBMISSION — FROZEN v3.0 SNAPSHOT, DO NOT EDIT, DO NOT CITE AS CURRENT.**
>
> This file (`arxiv_submission/paper.md`) is a **frozen 2026-04-17 snapshot** preserved for citation of the v3.0 arXiv preprint and for OSF-deposit SHA integrity. **The current paper is `docs/PAPER.md` (v7.5, 2026-04-21 evening)** — an ~880-line manuscript with a fundamentally different analytical framework: Hotelling T² = 3 557 (this v3.0 uses Cohen's d = 6.34 as the multivariate headline, which is now **deprecated as biased**; see `docs/PAPER.md §3.8`), nested-CV AUC = 0.998 with an explicit Band-A (15–100 verses) restriction reducing the Quran to 68/114 surahs (this v3.0 uses the full 114), R12 gzip NCD γ = +0.0716 single-letter edit-detection, 99.1 % Adiyat 864-variant compound detection, exp46 / exp48 / exp49 / exp50 / exp51 experiments, R12 gzip NCD channel, and the `H2_QURAN_SPECIFIC_IMMUNITY` cross-corpus emphatic result. **None of those findings is in this v3.0 file.** A journal submission using this file instead of `docs/PAPER.md` would present an internally inconsistent ~3-major-versions-behind paper.
>
> **Decision rule for any external use:**
> - Want the **current paper**? Use `docs/PAPER.md` (v7.5).
> - Need to cite the v3.0 arXiv preprint verbatim? This file, frozen.
> - Need to reconcile v3.0 ↔ v7.5 numbers? See `CHANGELOG.md` entries `[3.0.0]` → `[7.5.0]` and the retraction list in `docs/PAPER.md §5` (25 retractions).
>
> **Key divergences from v7.5 to flag if this file is ever cited:**
> 1. **Multivariate headline**: this v3.0 reports Cohen's d = 6.34; v7.5 reports Hotelling T² = 3 557 (perm p = 4.98·10⁻³, Mann–Whitney p = 1.75·10⁻⁴⁴). Cohen's d on Φ_M is formally deprecated in v5+ as biased-upward univariate.
> 2. **Band-A restriction**: v7.5 computes Φ_M on 68 band-A (15–100 verses) Quran surahs; this v3.0 uses all 114. The Band-A number is the peer-review-defensible headline.
> 3. **Missing in v3.0 but in v7.5**: R12 gzip NCD γ = +0.0716 (edit-detection channel, `docs/PAPER.md §4.25`), Adiyat 864-variant compound test (§4.26), exp46 full-mode emphatic audit (§4.30), exp48–exp51 verse-graph + cross-corpus resolution experiments (§§4.31–4.34), results_lock.json integrity manifest over 127 SHA-pinned scalars (§3.7), `H2_QURAN_SPECIFIC_IMMUNITY` cross-corpus result.
> 4. **The abstract's "AUC = 0.998" is preserved in v7.5**, but every other headline number either strengthened or was formally deprecated. See `docs/RANKED_FINDINGS.md §5` for the 25-item retraction ledger.
>
> **Companion files:** `arxiv_submission/STATUS.md` (v7.5-aware snapshot status) and `arxiv_submission/preregistration_v73_addendum.md` (v7.3 post-hoc code-state lock).

---

## A Reproducible 5-Dimensional Characterisation Robust to Adversarial Perturbation

**Version**: 3.0 (clean-data rebuild, 2026-04-17)
**Supersedes**: all QSF_PAPER_DRAFT_v* and associated QSF_*_v10.* documents
**Status**: **SUPERSEDED by `docs/PAPER.md` v7.5 (2026-04-21 evening)**. This file is preserved as a frozen citation target; do not edit it and do not use it for new submissions.

---

## Abstract

We present a 5-dimensional structural feature vector — **end-letter rhyme rate (EL), verse-length coefficient of variation (VL_CV), connective-word start rate (CN), conditional root-bigram entropy (H_cond), and structural tension (T)** — and show that the Quranic corpus separates from a length-matched 2,570-unit Arabic control pool (spanning pre-Islamic, early-Islamic, and Abbasid poetry; historical chronicle; Arabic Bible; Bukhari ḥadīth; and modern literature) at **Mahalanobis distance d = 6.34** (Cliff's δ = 0.99, Mann-Whitney p = 3·10⁻⁴⁴). A logistic classifier on the 5 features achieves **AUC = 0.998** on 5-fold cross-validation. All four perturbation types applied to canonical text — letter 10 %, word 10 %, verse shuffle, and verse-internal word shuffle — move Quran surahs toward the control centroid in **93–100 %** of units, while the same perturbations applied to Abbasid poetry and Arabic Bible have mean displacement indistinguishable from zero. The canonical surah order is path-minimal in 5-D space (z = −3.96, 0 of 2,000 random permutations achieve a shorter total distance). Under a scale-free sliding-window test, Quran surahs achieve Fisher-combined p ≈ 10⁻¹⁶ at window sizes W ∈ {5, 10, 20}; no control corpus achieves p < 10⁻³ at any window size.

We show that 17 of 29 testable predictions from earlier versions of this paper **survive the audit at clean-data level or stronger**, 6 are **weakened but directionally correct**, and 6 are **falsified or retracted** (including one previously labelled "closed" that we now accept is a mathematical tautology). We publish the full ranked-findings table (§7, `docs/FINDINGS_SCORECARD.md`), the raw pipeline (`src/clean_pipeline.py`), and a single-file reproducibility notebook (`notebooks/QSF_REPRODUCE.ipynb`) so that every number can be regenerated from the raw corpus files in ≤ 2 minutes.

**Important**: §10 lists every previously-published claim that this audit retracts.

---

## 1 Introduction

Claims that the Quran has distinctive structural properties have been made for centuries from multiple traditions; quantitative studies since the 1970s (Bakr, Khalifa, Tabataba'i, de Blois, Stewart) have identified features such as end-rhyme density, root-vocabulary richness, and verse-length variability. The v1 and v2 drafts of this work (2024–2025) attempted to unify these into a single "structural fingerprint" (Φ_M) with a notebook-driven pipeline. A forensic audit in April 2026 revealed that the pipeline's checkpoint file corrupted two control corpora (Arabic Bible and Ksucca chronicle), that several proof-gap closures were mathematical identities rather than empirical results, and that four numerical claims were inflated by hardcoded denominators. This paper replaces v2 and reports only numbers regenerable from the raw `data/corpora/` files.

### 1.1 Contributions

1. A self-contained 5-D structural fingerprint reproducible end-to-end from raw corpora in 102 s on a laptop (`src/clean_pipeline.py`).
2. A 23-test verification suite that individually addresses every previously-published claim.
3. A standardised sanity-check gate (G1-G5) that would have caught the v2 data corruption.
4. A published scorecard (§7) ranking every testable finding by composite strength; this permits readers to reproduce a strict subset (flagship-grade only) or the full set.
5. An honest retraction of 6 specific claims.

---

## 2 Data

### 2.1 Corpora

Every corpus is a newline-separated raw text file or structured file (xlsx/json/xml) living in `data/corpora/<lang>/`. No preprocessing pickle is used. SHA-256 hashes are pinned at pipeline run time and stored in the report JSON.

| Corpus | File | Language | Units | Verses | Role |
|---|---|:-:|:-:|:-:|---|
| Quran | `ar/quran_bare.txt` | Ar | 114 | 6,236 | target |
| Poetry (Jahili) | `ar/poetry_raw.csv` | Ar | 133 | — | Arabic ctrl |
| Poetry (Islami) | `ar/poetry_raw.csv` | Ar | 465 | — | Arabic ctrl |
| Poetry (Abbasi) | `ar/poetry_raw.csv` | Ar | 2,823 | — | Arabic ctrl |
| Ksucca (Ta'rikh al-Sudan) | `ar/ksucca.txt` | Ar | 41 | — | Arabic ctrl |
| Arabic Bible (Smith-Van Dyke) | `ar/arabic_bible.xlsx` | Ar | 1,183 | — | Arabic ctrl |
| Ḥadīth (Bukhari) | `ar/hadith.json` | Ar | 95 | — | Arabic ctrl |
| Hindawi modern fiction | `ar/hindawi.txt` | Ar | 74 | — | Arabic ctrl |
| Iliad (Perseus TEI) | `el/iliad_perseus.xml` | Gk | 24 | — | cross-lang |
| Greek NT (OpenGNT v3.3) | `el/opengnt_v3_3.csv` | Gk | 260 | — | cross-lang |
| Hebrew Tanakh (WLC) | `he/tanakh_wlc.txt` | He | 929 | — | cross-lang |
| Arabic Wikipedia (sample) | `wiki/` | Ar | 80 | — | external val |

A **unit** is a surah (Quran), poem (poetry), chapter (Bible/ḥadīth/Tanakh), story (Hindawi), or book (Iliad). Ksucca units are split on historical chapter markers (`ذكر`).

### 2.2 Sanity-check gate (G1–G5)

Every corpus must pass the following before entering the pipeline (`src/verify_corpora.py`):

- **G1**: ≥ 10 units
- **G2**: no unit has > 80 % single-token verses (rules out meter labels)
- **G3**: no unit has > 50 % identical verses (rules out "Genesis"-repetition pickle bug of v2)
- **G4**: corpus-level verse-word-count CV ∈ [0.05, 3.0]
- **G5**: mean Arabic-script ratio > 0.40 for Arabic corpora

**All 9 corpora pass all 5 checks on raw files.** The v2 pickle would have failed G2 (Ksucca) and G3 (Bible).

### 2.3 Matched-length restriction (Band A)

For every direct Quran-vs-control comparison we restrict to units of 15–100 verses ("Band A"). This matches the Quran's empirical range and reduces length confounding. The paper's inferential statistics are all computed on Band A.

---

## 3 Feature extraction

### 3.1 The five features

For a unit consisting of verses v₁, …, v_n:

| # | Name | Formula | Intuition |
|:-:|---|---|---|
| 1 | **EL** | fraction of adjacent verse pairs sharing terminal letter | rhyme density |
| 2 | **VL_CV** | σ(‖v_i‖) / μ(‖v_i‖) across verses | verse-length variability |
| 3 | **CN** | fraction of verses starting with a classical Arabic connective (wa, fa, thumma, etc.) | discourse connective rate |
| 4 | **H_cond** | conditional entropy of root at position t given root at position t−1 | residual root-bigram uncertainty |
| 5 | **T** | mean(\|Δω(v_i)\|) with ω = orthogonal-feature magnitude | structural "tension" |

Root extraction is done with CamelTools 1.5.7 (`calima-msa-s31`) as the authoritative morphological analyser. v1/v2 used a heuristic root extractor that we re-validated in April 2026 against a 50-word hand-annotated gold set: heuristic = 21 % match, CamelTools = 63 % match. H_cond and T are sensitive to this choice and we use CamelTools throughout (`src/roots.py` with on-disk cache at `src/cache/`).

### 3.2 Diacritics policy

The consonantal rasm (ب, ت, ج, …) is the feature substrate. Harakat (short vowels, shadda, sukun) are stripped before computing EL, CN, H_cond. We retain the vocalised text for the E3 harakat-channel-capacity analysis only (see §6.7). Mixing vocalised and unvocalised forms was an earlier data-hygiene bug (now prevented by the vectorised `_strip_d()` helper in `src/features.py`).

---

## 4 Φ_M: the Mahalanobis fingerprint

### 4.1 Definition

Let μ, Σ be the mean and covariance of the 5-D feature vectors over the Band-A Arabic control pool. For any unit u with feature vector x_u:

$$ \Phi_M(u) = \sqrt{ (x_u - \mu)^\top \Sigma^{-1} (x_u - \mu) } $$

This is the Mahalanobis distance from u to the control centroid. High Φ_M means u is an outlier relative to the control cloud.

### 4.2 Empirical result (T2)

On 2,570 Band-A Arabic control units vs 80 Band-A Quran surahs:

| Statistic | Value |
|---|---|
| Quran mean Φ_M | 8.43 |
| Control mean Φ_M | 2.11 |
| Cohen's d | **6.34** |
| Cliff's δ | **0.99** |
| Mann-Whitney U p | 3·10⁻⁴⁴ |
| 10-fold CV: min d | 5.08 |
| 10-fold CV: median d | 6.89 |
| 10-fold CV: max p | 2·10⁻⁵ |

### 4.3 Classifier AUC (T15)

A logistic classifier on the 5 features, 5-fold CV, stratified:

- **AUC = 0.998** (z ≈ 128 σ over chance, 4-way stratified CV)
- Each surah is held out and correctly classified in all 5 folds.

The paper's v2 claim was d = 1.93, AUC = 0.90. On clean data both flagship numbers are dramatically higher. The v2 numbers were suppressed by including the "Genesis × 7" Bible chapters and meter-label-contaminated Ksucca units as legitimate Arabic controls; these look like statistical outliers in different directions, dragging the cloud mean toward the Quran and masking the real separation.

---

## 5 Shannon-Aljamal sufficiency (five conditions)

The v2 theorem posited five jointly-sufficient conditions for what we called "structural singularity":

| # | Condition | Empirical result on clean data | Survives? |
|:-:|---|---|:-:|
| S1 | Multivariate separation (max Φ_M) | d = 6.34 | ✅ strong |
| S2 | Channel orthogonality I(EL; CN) → 0 | Quran I = 1.17 bits (**highest** at unit level) | ❌ falsified at unit level |
| S3 | Constrained entropy (Quran #1 on H_cond) | Quran H_cond = 0.87; ksucca 1.17 (#1) | ❌ Quran is #3 |
| S4 | VL_CV extremal AND H₃/H₂ → 0 | VL_CV weakened (pool d = 1.40); H₃/H₂ = 0.222 (#1) | ⚠️ partial |
| S5 | Path minimality on canonical ordering | z = −3.96, 0 / 2000 perms beat canon | ✅ |

Two of the five conditions fail at unit level on clean data. We therefore retract the **joint-sufficiency** claim as currently stated. The weaker claim **"S1 + S5 + partial-S4 jointly characterise the Quran among Arabic corpora"** is supported, and is what §6.5's "reframed headline" consolidates.

---

## 6 Test catalogue — results

All 23 tests are implemented in `src/clean_pipeline.py`, `src/extended_tests.py`, `src/extended_tests2.py`. Full row-by-row with composite ranks is in **`docs/FINDINGS_SCORECARD.md`**. Summarised:

### 6.1 T1–T4: Core separation

| T | Name | Result | Verdict |
|:-:|---|---|:-:|
| T1 | Anti-Metric VL_CV (pool) | d = 1.40 | ⚠️ |
| T2 | Φ_M Mahalanobis | d = 6.34 | ✅✅ |
| T3 | H_cond by corpus | Quran rank #3 | ❌ |
| T4 | Ω hierarchical rebuild (no hardcoded constants) | Quran Ω = 7.89 (#1); ksucca 7.20 | ⚠️ rank ok, magnitude inflated in v2 |

### 6.2 T5–T6: Adversarial

| T | Name | Result | Verdict |
|:-:|---|---|:-:|
| T5 | Pre-reg canon-vs-perturbed | Quran 100 %, Abbasi 60 %, Bible 22.5 % | ✅ |
| T6 | H-Cascade fractality F | d = 0.76 (hadith + ksucca exceed Quran) | ⚠️ |

### 6.3 T7–T9: Dual-channel

| T | Name | Result | Verdict |
|:-:|---|---|:-:|
| T7 | EL/CN dual-channel ranks | Quran #1 EL, #1 CN, #1 G_turbo | ✅ |
| T8 | Path minimality + adjacent diversity | z = −3.96 ✓; adj-diversity 10.6th pctile (not 100th) | ✅ partial |
| T9 | Markov unforgeability (bigram root LM) | Quran z = 44.9; Abbasi z = 47.9 (higher) | ⚠️ not Quran-unique |

### 6.4 T10–T15: Robustness

| T | Name | Result | Verdict |
|:-:|---|---|:-:|
| T10 | %T > 0 | Quran 39.7 %; controls 0.0–0.1 % | ✅✅ |
| T11 | H₃/H₂ bigram-sufficiency | Quran 0.222 (lowest) | ✅ |
| T12 | 10-fold CV Φ_M | min d = 5.08, max p = 2·10⁻⁵ | ✅✅ |
| T13 | Meccan/Medinan sub-analysis | F_M = 0.80, F_D = 0.84 | ❌ F > 1 threshold fails |
| T14 | Bootstrap Ω | 100 % > 2, median 10.0 | ✅✅ |
| T15 | Classifier AUC | 0.998, z = 128 | ✅✅ |

### 6.5 T16–T18: Scale-free + perturbation (the sharpest findings)

| T | Name | Result | Verdict |
|:-:|---|---|:-:|
| T16 | Scale-Free Sliding-Window Ordering | Quran Fisher p = 10⁻¹⁶ at W ∈ {5, 10, 20}; all controls p ≳ 0.5 | ✅✅ |
| T17 | Multi-scale perturbation | Quran gaps +0.78 / +2.48 / +1.76 (letter / word / verse), 93–100 % canon farther; controls ≈ 0 | ✅✅ |
| T18 | Verse-internal word-order shuffle | Quran gap +5.79, 100 % canon farther; Abbasi +0.13, Bible +0.06 | ✅✅ |

### 6.6 T19–T22: Cross-corpus sanity

| T | Name | Result | Verdict |
|:-:|---|---|:-:|
| T19 | RQA Laminarity | Quran LAM = 0.305; poetry ≈ 0.997; Bible 0.153 | ⚠️ vs poetry only |
| T20 | Structural forgery P3 (rhyme-swap) | Q 32 %, Bible 60 % collapse (opposite of v2's 93 %/36 %) | ❌ not reproduced with our metric |
| T21 | Cross-language Iliad | Iliad path-z = +0.65 (NOT optimised), vs Quran −3.96 | ⚠️ partial |
| T22 | RD × EL product | Quran 0.632 (3.5 – 38× any control) | ✅✅ |

### 6.7 T23: Epigenetic layer (harakat channel)

| T | Name | Result | Verdict |
|:-:|---|---|:-:|
| T23 | Harakat channel capacity H(harakat \| rasm) | 1.96 bits / 4.70 max ≙ 58 % redundancy | ✅ non-random |

### 6.8 Composite scorecard

The headline numbers (composite ≥ 85, using `sqrt(conf × effect)` where conf and effect are p-value and Cohen's-d-based percentiles, see `docs/FINDINGS_SCORECARD.md`):

1. D09 Classifier AUC — 100
2. D10 %T > 0 — 97
3. D14 Verse-internal word-order — 97
4. D26 Bootstrap Ω — 95
5. D11 Multi-scale perturbation — 94
6. D02 Φ_M separation — 92
7. D27 Abbasi discrimination — 92
8. D07 Scale-free ordering — 91
9. D23 Pre-reg adversarial — 91
10. D24 10-fold CV Φ_M — 85

---

## 7 The five-bullet honest headline

1. **5-D Mahalanobis separation**: Quran surahs sit at d = 6.34 (δ = 0.99, p = 3·10⁻⁴⁴) from a 2,570-unit Arabic control pool spanning seven genres. Logistic classifier AUC = 0.998.
2. **Dual-channel rhyme+connective code**: EL rate 0.707 (5-10× any control); CN rate 0.086 (2-3× any control); RD × EL product 0.632 vs 0.02-0.18 (3-38× any control).
3. **Multi-scale structural sensitivity**: letter, word, verse, and verse-internal-word perturbations all move Quran surahs toward the control centroid in 93-100 % of units. Same perturbations on matched Abbasid poetry and Arabic Bible: mean displacement ≈ 0.
4. **Canonical ordering is path-minimal**: z = −3.96, 0 / 2,000 random permutations beat canon. Not unique to the Quran (Bukhari hadith also minimal, z = −4.85) but Iliad is NOT (z = +0.65).
5. **Pre-registered adversarial test**: Quran 100 % canon-wins, Abbasi poetry 60 %, Arabic Bible 22.5 %.

---

## 8 Cross-language (partial)

Under the language-agnostic 5-D proxy (replace EL with rhyme-at-nth-character, replace roots with character-initials):

| Corpus | path-z | pct T > 0 (language-agnostic) |
|---|---:|---:|
| Quran (Arabic) | −3.96 | 39.7 % (root-based T) |
| Iliad (Greek) | +0.65 | 100 % (char-init T; not comparable) |

Hebrew Tanakh and Greek NT are now in the repository (`data/corpora/he/`, `data/corpora/el/`) but the lang-agnostic fingerprint has not yet been run on them. The v2 claim "Quran 4/5 conditions vs Tanakh 1/5 vs Iliad 1/5" is therefore marked 🔒 untested pending the v3.1 update.

---

## 9 Epigenetic layer

The "epigenetic" layer is the superset of structural information carried by:
- **E1** Waqf (pause) placement — untested here (waqf-annotated corpus not available)
- **E2** Qira'at (seven/ten canonical recitations) — untested here (only Hafs is in the repo)
- **E3** Harakat (vocalisation) — **tested**: H(h | rasm) = 1.96 bits, redundancy 58.2 %. Harakat is structured by rasm, consistent with the "encoded epigenetic channel" hypothesis.
- **E4** Cross-layer MI — untested (requires E1+E2)

---

## 10 Retractions and errata

This paper supersedes QSF_PAPER_DRAFT_v2 and retracts the following specific claims:

1. **Ω_master = 19.2 (20× control lead)** → correct value is **Ω = 7.89** (9 % margin over ksucca at #2). The v2 value came from four hardcoded reference constants in `scripts/build_master_notebook.py:508-513` (`ref_phi=1.0, ref_H=2.8, ref_VL=0.29, r5=1.72`). These are all set to produce a denominator smaller than the actual Arabic-control mean, which inflates the reported Ω by ≈ 2.4×.
2. **"Morphological Frontier — Quran #1 on H_cond"** → correct rank is **#3**. Ksucca 1.17 and Arabic Bible 0.95 both exceed Quran's 0.87. Ksucca's rank inflates to #1 because it has exceptionally rich historical vocabulary.
3. **"Adjacent diversity at 100th percentile"** → correct percentile is **10.6th**. The v2 number was the complement (i.e., the claim was stated in the wrong direction).
4. **"I(EL; CN) ≈ 0 orthogonality at unit level"** → Quran has the **highest** mutual information among all corpora at unit level (1.17 bits). The claim may survive at verse level with a re-formulation; we flag S2 as falsified until this is done.
5. **"Meccan/Medinan sub-analysis: both F > 1"** → F_M = 0.80, F_D = 0.84 under our F definition. The pattern "both ≥ all Arabic controls" still holds but the F > 1 threshold does not.
6. **"5 of 5 formal-proof gaps closed"** → repo `docs/QSF_FORMAL_PROOF_GAPS_CLOSED.md` already admits 3 / 5. Of the two that were labelled "closed": **G3** (Hessian positive-definiteness) reduces to H = 2·Σ⁻¹, which is PD by construction for any invertible Σ — a tautology. **G5** (γ(Ω) = a + b·Ω linear form) reduces to regressing a quantity that is algebraically 2·(canon − pert) on ω = canon — an identity. Both are **falsified by mathematics**, not by data.
7. **"Root extractor agreement ≥ 90 %"** → the v1/v2 heuristic extractor matches **21 %** of a hand-annotated gold set; CamelTools 1.5.7 matches 63 %. All H_cond and T numbers in v2 used the 21 % extractor. All numbers in v3 use CamelTools.

### 10.1 Why the audit diverged from v2 at the result level

The single root cause was **pickle-checkpoint corruption in v2's preprocessing stage**: Arabic Bible chapters were serialised with every verse replaced by the string "تكوين" (= "Genesis"); Ksucca units had Arabic-poetry-meter labels interleaved with actual prose. Every `scripts/*.py` that loaded `after_v4_final.pkl.gz` inherited this contamination. The raw files on disk (`data/corpora/ar/*`) were always fine; bypassing the pickle restored correct behaviour. The pickle has been deleted as part of the v3 cleanup and sanity-check gate G1-G5 would have caught it.

---

## 11 Reproducibility

From a clean git checkout, running:

```powershell
python -X utf8 -u -m src.clean_pipeline
```

regenerates `results/CLEAN_PIPELINE_REPORT.json` in ≈ 102 seconds on a laptop. Corpus fingerprints (SHA-256) are pinned in that file. Cross-checking the ranked table in `docs/FINDINGS_SCORECARD.md` to that JSON is the canonical verification step.

`notebooks/QSF_REPRODUCE.ipynb` runs the same pipeline cell-by-cell with inline visualisations and is the recommended entry point for reviewers.

---

## 12 Limitations and future work

- The classifier AUC of 0.998 on 80 Band-A Quran surahs vs 2,570 Band-A Arabic controls raises concern about feature leakage via length or diacritics; we have audited both (length is explicitly Band-restricted; diacritics stripped uniformly). Independent validation on ≥ 3 additional out-of-sample Arabic corpora (Wikipedia, news, legal) is called for; Arabic Wikipedia is now in `data/corpora/wiki/` and should be added to T15 in v3.1.
- Cross-language evaluation on Hebrew Tanakh and Greek NT is now feasible (data present) but not yet implemented.
- The exponential-family generalisation of the 5-D fingerprint to arbitrary vocalised-script corpora (paper's Gap 4) remains mathematically open.
- Rhyme-swap forgery test (D21) does not reproduce v2's asymmetric Quran-vs-control pattern under our implementation of the perturbation; the v2 method differs and we have not re-implemented it exactly.

---

## References

See `archive/2026-04-17_docs_merged/` for the original source documents:

- `QSF_PAPER_DRAFT_v2.md` — previous version (122 KB)
- `QSF_FORMAL_PROOF.md`, `QSF_FORMAL_PROOF_GAPS_CLOSED.md` — formal sketch
- `QSF_SHANNON_ALJAMAL_THEOREM.md` — 5-condition statement
- `QSF_EPIGENETIC_LAYER.md` — E1–E4 definitions
- `QSF_REPLICATION_PIPELINE.md` — legacy pipeline description (superseded by `docs/REPLICATION.md`)
- `PREREGISTRATION_v10.18.md` — pre-registration protocol
- `REMAINING_GAPS_v10.19.md`, `QSF_AUDIT_REPORT_v10.15.md` — earlier gap status
- `QSF_COMPLETE_REFERENCE.md` — 144 KB reference

The forensic audit record (April 2026) is at `archive/2026-04-17_audit_rounds/`.

---

## Appendix A — feature implementations

See `src/features.py`. Each of the five features is a pure function of a list of verse strings, runs in < 20 ms for any realistic unit, and has a regression test in `src/verify_corpora.py`'s G4 (verse-length CV) and in the CamelTools coverage report in `src/cache/cameltools_root_cache.pkl.gz`.

## Appendix B — Ādiyāt sharpshooter

Sūra 100 (al-Ādiyāt) was pre-registered as a sharpshooter case before the audit. See `docs/ADIYAT_CASE.md`.
