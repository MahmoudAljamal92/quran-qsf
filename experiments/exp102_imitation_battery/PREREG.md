# exp102_imitation_battery — Pre-registration

**Hypothesis ID**: H40
**Status**: pre-registered, frozen 2026-04-28 evening (Asia/Riyadh).
**Patch context**: v7.9-cand patch H V3.1 — Phase 5 scaffolding, immediately follows the Integrity-Protocol patch.
**Supersedes**: nothing. New experiment.

---

## 0. Why this exists (one paragraph)

The existing project shows that the Quran sits at the extreme of a 7-corpus comparison pool of naturally-occurring Arabic texts (`expP7_phi_m_full_quran` T² = 3,685; `exp89b` 1-feature AUC = 0.9971; `exp99_adversarial_complexity` 0/10⁶ Markov-3 forgeries pass joint gate). What it has **never** scored is the historical and modern set of **alleged human-authored Arabic imitations** of the Quran — texts written explicitly to reproduce some property of Quranic style. The most-cited examples are *Furqan al-Haqq / al-Forghan al-Hagh* (1999, Christian counter-text in 77 sura-like sections), the documented Musaylimah ibn Habib fragments (~7th century), Rashad Khalifa's "Authorized English / Arabic" version (revisionist Quran), and on-demand LLM-generated "Quran-style" output. Where do they fall in the locked 5-D `Φ_M` feature space relative to the Quran cluster vs the 2,509 naturally-occurring Arabic control units? **`exp102` answers this with a pre-registered ranking — not a re-fit, not a re-train.** The locked Quran centroid + covariance from `expP7` is the reference; imitations are scored as out-of-sample test points only.

---

## 1. Hypothesis (one paragraph)

**H40 (imitation distinguishability)**: Under the locked 5-D feature pipeline `features_5d(verses, stops)` (`@C:\Users\mtj_2\OneDrive\Desktop\Quran\src\features.py`) and the locked Quran-vs-control classifier (locked Φ_M centroid + Σ⁻¹ from `expP7`, AUC = 0.998), every available human-authored or AI-generated Arabic imitation text scores **outside** the Quran cluster — defined operationally as **Mahalanobis distance from Quran centroid > the 95th-percentile of the locked Quran-surah Mahalanobis distribution** AND **classifier output favours `arabic_control` over `quran` class**. Equivalently: the imitations cluster with the 2,509 Arabic control units, not with the 114 Quran surahs.

If H40 holds for **every** imitation in the battery, the locked classifier's discrimination claim is corroborated against deliberate forgery attempts. If even **one** imitation crosses inside the Quran cluster, the classifier's claim is materially weakened and a follow-on PREREG must investigate which single-feature axis was matched.

---

## 2. Locked decision rules

### 2.1 Frozen inputs

- **5-D feature extractor**: `src.features.features_5d(verses, stops)` — exact bit-for-bit signature locked by `MANIFEST_v8.json`.
- **Stops set**: derived from project Arabic corpora via `src.features.derive_stopwords(all_verses, top_n=20)` against the existing locked `data/corpora/ar/` pool. Identical to what `expP7` and `exp89b` use.
- **Reference centroid + Σ⁻¹**: loaded from `results/experiments/expP7_phi_m_full_quran/expP7_phi_m_full_quran.json` field `centroids.quran_5d` and `phi_m_inputs.S_inv` (or recomputed from the locked Quran 114-surah feature matrix; either path bit-reproduces).
- **Cluster threshold** (frozen *before* any imitation is scored): the **95th percentile** of `Φ_M(quran_surah_i)` across all 114 Quran surahs under the same centroid + Σ⁻¹. Call this `tau_inside`.
- **Imitation directory**: `data/corpora/imitations/` (created by this PREREG). Each subdirectory is one imitation; each contains either a single `text.txt` (one verse per line) or a structured `verses.json` (`{"surahs": [{"label": "F:001", "verses": ["..."]}, ...]}`).

### 2.2 Imitations battery (initial set; expandable post-PREREG via amendment only)

| ID | Imitation | Source | Scope | Acquisition |
|---|---|---|---|---|
| **I1** | Furqan al-Haqq (1999, "True Furqan") | archive.org / answering-islam | 77 surah-like sections | manual (PDF → TXT extract or copy from any plaintext mirror) |
| **I2** | Musaylimah ibn Habib fragments | classical citations (Tabari, Ibn Kathir) | small fragments only (~3–10 short "verses") | manual transcription from cited classical sources |
| **I3** | Rashad Khalifa "Authorized" Quran (Arabic) | masjidtucson.org / submission.org | 114 surahs, with Khalifa's per-verse selections | manual (HTML scrape with consent of source) |
| **I4** | LLM-generated "Quran-style" Arabic text | fresh generation by a frontier LLM with explicit style prompt | ~50 short pseudo-surahs | author-supplied; prompt+model+temperature must be logged in `data/corpora/imitations/I4_llm_generated/SOURCE.json` |
| **I5** | Markov-3 generated baseline | reproduced from `experiments/exp99_adversarial_complexity` Markov-3 forgery pool | 100 sampled forgeries | already on disk via `exp99` (sub-sampled receipt) |

The battery is **append-only**: after this PREREG is hash-locked, additional imitations may only be added via a separate amendment PREREG that lists each new imitation and its source. The decision rules below apply to whatever is on disk at run time; missing imitations are reported in the receipt as `MISSING` with no inference made about their absence.

### 2.3 Verdict ladder (strict order; first match wins)

| # | Branch | Trigger | Implication |
|---|---|---|---|
| 1 | `BLOCKED_pipeline_dependency_missing` | `src.features.features_5d` cannot be imported, OR `expP7` receipt missing, OR locked stops set unavailable | Re-run after dependencies are restored |
| 2 | `BLOCKED_no_imitations_on_disk` | `data/corpora/imitations/` has zero subdirectories | Acquire at least I1 + I5 before re-running |
| 3 | `FAIL_audit_unit_invariant` | Any imitation has `< 5` non-empty verses or no usable Arabic letters | Imitation is logged as malformed; rest of battery proceeds |
| 4 | `FAIL_imitation_inside_cluster` | At least one imitation has `Φ_M ≤ tau_inside` AND classifier favours `quran` class | Quran-vs-control discrimination is challenged; open follow-on PREREG to identify which feature axis matched |
| 5 | `PARTIAL_imitation_borderline` | Every imitation has `Φ_M > tau_inside` BUT at least one has `Φ_M < 2 × tau_inside` | Imitations are outside but in the immediate boundary region; reportable as a soft-pass with caveats |
| 6 | **`PASS_all_imitations_outside_cluster`** | Every imitation has `Φ_M > 2 × tau_inside` AND classifier favours `arabic_control` for every imitation | H40 fully confirmed at the locked threshold |

### 2.4 What promotion does NOT mean

A `PASS_all_imitations_outside_cluster` verdict does **NOT**:

- Promote any new finding to paper grade. exp102 is an *adversarial corroboration* of the existing classifier (F-row entries 1, 2 in `RANKED_FINDINGS.md`), not a new finding.
- Establish that the Quran is "unforgeable in principle". The battery is bounded by the imitations actually scored. Future imitations, especially clean-room LLM forgeries (deferred to the future Phase-5 clean-room test), can still falsify.
- Affect the F57 meta-finding (Phase 2). exp102 measures structural fingerprint, not Quranic self-claims.

### 2.5 What failure does NOT mean

A `FAIL_imitation_inside_cluster` verdict does **NOT** retract any locked classifier scalar. It opens a follow-on PREREG to investigate the specific axis that the imitation matched, and may downgrade the classifier's claim from "any Arabic prose vs Quran" to a more scoped statement.

---

## 3. Frozen constants

- **Seed (RNG)**: `SEED = 42` (matches project default).
- **5-D feature names (in canonical order)**: `(EL, VL_CV, CN, H_cond, T)`.
- **Stops list**: derived once from the locked `data/corpora/ar/` pool, top-20 most-frequent words. Cached in the receipt.
- **`tau_inside`**: not a free parameter. Computed at run time as the 95th percentile of `Φ_M` over the locked 114-surah Quran feature matrix using the same centroid + Σ⁻¹.
- **Imitation directory expected layout**:
    ```
    data/corpora/imitations/
        I1_furqan_al_haqq/
            verses.json   OR   text.txt
            SOURCE.json    (free-form provenance: URL, fetch date, sha256)
        I2_musaylimah/
            ...
        I3_khalifa/
            ...
        I4_llm_generated/
            verses.json
            SOURCE.json
        I5_markov3_baseline/
            verses.json   (sampled from exp99 forgery pool)
            SOURCE.json   (pointer to exp99 receipt)
    ```

---

## 4. Audit hooks (must reproduce these in the receipt)

- **Pipeline-import sentinel**: `from src.features import features_5d` must succeed; failure aborts and fires branch 1.
- **expP7-centroid sentinel**: receipt-loaded centroid must reproduce the locked `expP7` centroid to abs-diff ≤ 1·10⁻⁹; failure aborts.
- **PREREG-hash sentinel**: SHA-256 of `experiments/exp102_imitation_battery/PREREG.md` must match `_PREREG_EXPECTED_HASH` in `run.py`.
- **Stops-list-fingerprint sentinel**: SHA-256 of the stops list (sorted + concatenated) must be logged; mismatch on re-run flags a corpus drift.
- **`tau_inside` sanity**: `tau_inside ∈ [0, +∞)` AND p99 of locked Quran Φ_M is finite; otherwise abort.

---

## 5. Honesty clauses

### 5.1 No re-fit

The classifier centroid and Σ⁻¹ are loaded from `expP7`. The Quran's 114-surah feature matrix is *not* recomputed inside `exp102`; it is loaded from the locked `expP7` receipt or from the `phase_06_phi_m` pickle, whichever is canonical. **No imitation is allowed to influence the classifier or the threshold.**

### 5.2 No selective reporting

Every imitation that runs *must* appear in the receipt with its full per-axis 5-D vector and its classifier output. Imitations cannot be silently excluded post-hoc.

### 5.3 LLM-generated samples (I4) — provenance discipline

If I4 is included, the prompt, model name, model version, temperature, and any sampling parameters must be logged in `SOURCE.json`. Re-runs with different prompts are *different imitations*, not rerunnable replicates. **Re-prompting until the result is favourable is forbidden.** Samples are committed to disk before scoring; any post-scoring sample swap is a protocol violation.

### 5.4 Markov-3 baseline (I5)

I5 is included as a *sanity floor*: we already know from `exp99` that 0/10⁶ Markov-3 forgeries pass the joint Gate-1 ∧ F55 ∧ F56 detector. I5 should land far outside the Quran cluster. If I5 sits inside, something is wrong with the pipeline and the entire receipt is suspect.

---

## 6. Reproduction recipe

```powershell
# 1. Acquire imitation texts (manual; SOURCE.json each):
#    - I1: archive.org/details/the-true-furqan-alforghan-alhagh
#    - I2: classical citations (e.g. al-Tabari, Ibn Kathir)
#    - I3: masjidtucson.org/quran/frames/ (with proper attribution)
#    - I4: prompt a frontier LLM in Arabic to generate ~50 short surah-like
#          fragments; log prompt+model+temperature
#    - I5: subsample 100 forgeries from
#          results/experiments/exp99_adversarial_complexity/<sub>.json
#
# 2. Place each under data/corpora/imitations/<I_id>_<name>/ with either
#    `verses.json` (preferred) or `text.txt`.
#
# 3. Run the experiment:
python -m experiments.exp102_imitation_battery.run
#
# 4. Receipt:
#    results/experiments/exp102_imitation_battery/exp102_imitation_battery.json
#
# 5. Audit:
python scripts/integrity_audit.py
```

---

## 7. Cross-references

- 5-D feature definitions: `src/features.py::features_5d` (locked).
- Quran centroid + Σ⁻¹ source: `results/experiments/expP7_phi_m_full_quran/expP7_phi_m_full_quran.json`.
- Markov-3 forgery pool reference: `results/experiments/exp99_adversarial_complexity/exp99_adversarial_complexity.json`.
- Phi_M classifier locked verdict: `RANKED_FINDINGS.md` row 1 (AUC = 0.998), row 2 (T² = 3,557 / 3,685).
- F57 meta-finding (independent; not affected by exp102): `PAPER.md §4.46`.

---

## 8. Frozen-time fingerprint

This document's SHA-256 is computed **after** all text above is final and **before** any imitation is scored. The hash is written to:

- `experiments/exp102_imitation_battery/PREREG_HASH.txt` (one line, lowercase hex).
- The eventual receipt's `prereg_hash` field.

A diff between this PREREG and the receipt's `prereg_hash` automatically invalidates any verdict on this experiment.
