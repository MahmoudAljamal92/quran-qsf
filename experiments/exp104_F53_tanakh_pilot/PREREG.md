# exp104_F53_tanakh_pilot — Pre-registration (Phase 3, DESIGN-ONLY pilot)

**Hypothesis ID**: H59
**Status**: pre-registered, **DESIGN-ONLY** as of 2026-04-28 evening (Asia/Riyadh). No run script has been executed; no receipt has been produced. **This is a Phase 3 pilot**: the substantive question is "does F53 generalise to a non-Arabic oral-liturgical scripture?", and the design pins down which scripture, which peer corpora, which τ-calibration protocol, and which verdict ladder. Hash-locked before any cross-tradition data is opened.
**Patch context**: v7.9-cand patch H V3.1 — succeeds the BLOCKED H38 (`expP4_F53_cross_tradition`) by replacing the unscoped "test all 5 traditions" plan with a single-tradition pilot.
**Supersedes**: nothing. (H38 stays BLOCKED until its own corpus-acquisition plan is fulfilled; H59 is a parallel pilot with a tighter scope.)

---

## 0. Why this exists (one paragraph)

The locked F53 finding (`exp95c_multi_compressor_adiyat`, K=2 multi-compressor consensus closes single-letter forgery on the Quran's Q:100 al-`Ādiyāt at recall = 1.000, FPR = 0.0248) is a **Quran-vs-Arabic-peers** detector. The retracted F54 (`exp95e` V1, R53) showed the rule does **not** trivially extend to all 114 Quran surahs. The natural follow-up is whether F53 (the *rule*, not the *τ*) is a property of the Quran specifically or of canonical oral-liturgical scriptures in general. **`exp104` answers this with a single, focused pilot on the Hebrew Tanakh**: pick one short canonically-bounded Tanakh chapter (target: a Psalm), use multi-compressor consensus K=2 with τ **calibrated on Hebrew peer corpora** (NOT transferred from Arabic), and report whether F53 closes the same forensic gap on a different language and a different scripture. If yes, F53 is a class property of canonical oral-liturgical text. If no, F53 is Quran-specific (or Arabic-specific) and the locked finding remains correctly scoped as such.

---

## 1. Hypothesis (one paragraph)

**H59 (F53 cross-tradition Hebrew pilot)**: Under the K=2 multi-compressor consensus rule with τ thresholds calibrated *on the Hebrew peer pool* (per-compressor 5th percentile of length-matched ctrl-Δ NCD distribution), single-consonant substitution on a designated Tanakh chapter (target: **Psalm 19**, 14 verses, ~1,800 Hebrew letters) achieves **recall ≥ 0.999** with **FPR ≤ 0.05** against the same calibration peer pool. Equivalently: every single-letter substitution on Psalm 19 must produce K=2-consensus NCD shifts that exceed the locked Hebrew τ on at least 2 of 4 compressors {gzip-9, bz2-9, lzma-preset-9, zstd-9}.

**Pilot scope**: one Tanakh chapter only. Generalisation to whole Tanakh / whole Torah / whole Psalter is OUT of scope here and would require a separate PREREG.

---

## 2. Locked decision rules

### 2.1 Frozen target text

- **Target chapter**: **Psalm 19** in the Westminster Leningrad Codex (WLC) edition. Pulled from the project's existing locked Hebrew corpus `data/corpora/he/tanakh_wlc.txt` (loaded by `src.raw_loader.load_hebrew_tanakh`).
- **Letter normalisation**: Hebrew consonant skeleton (22 letters), final-form letters folded to base form (mem-sofit → mem, etc.). **Niqqud and te'amim are stripped** before scoring (analogue to the Arabic 28-letter rasm). The exact normalisation function is locked in `frozen_constants.normaliser`.
- **Why Psalm 19**: short enough (~1,800 letters) to enumerate every single-consonant substitution at reasonable wall-clock cost; canonically bounded; widely-cited; theologically anodyne.

### 2.2 Frozen peer pool

- **Hebrew narrative peer pool**: chapters of the Hebrew Bible *outside* the Psalter, drawn from Genesis, Exodus, Joshua, Judges, Samuel-Kings narrative books. Target n_units = 200, length-matched to Psalm 19 ± 30 % (i.e. 1,260–2,340 letters per peer chapter).
- **Why narrative not poetic**: the calibration peer pool should be of the *same broad rhetorical class as the target's surrounding non-target chapters*; pure-poetic peers would over-tighten τ. Narrative biblical Hebrew is the natural ctrl class for "is this a Psalm-like passage?".
- **Acquisition**: the WLC corpus is already on disk; the chapter-level segmentation must be extracted by a small loader (`src.raw_loader.load_hebrew_tanakh_chapters`, to be added when run.py is written).

### 2.3 Frozen τ-calibration protocol

For each compressor c ∈ {gzip-9, bz2-9, lzma-preset-9, zstd-9}, compute on the peer pool:

1. For each peer chapter, generate every single-consonant substitution variant.
2. For each (peer, variant), compute `Δ_c = NCD_c(peer, peer_with_variant) - NCD_c(peer, peer)`.
3. The locked Hebrew τ_c is the 5th percentile of the resulting `Δ_c` distribution across all peer-variant pairs.
4. The K=2 rule fires on a Psalm 19 variant iff at least 2 of 4 compressors have `Δ_c ≥ τ_c`.

**Symmetry with Arabic side**: this is the same calibration recipe used for Arabic in `exp95c`; we are deliberately keeping it identical so a cross-language *failure* cannot be blamed on a calibration-protocol difference.

### 2.4 Verdict ladder (strict order; first match wins)

| # | Branch | Trigger | Implication |
|---|---|---|---|
| 1 | `BLOCKED_corpus_missing` | `data/corpora/he/tanakh_wlc.txt` missing or chapter-segmentation fails | Acquire / fix loader |
| 2 | `BLOCKED_psalm_19_too_short` | After normalisation, Psalm 19 has < 1,000 letters or < 10 verses | Choose a different pilot chapter via amendment PREREG |
| 3 | `FAIL_audit_peer_pool_size` | `n_peer_units < 100` after length-matching | Widen length window via amendment OR pick different peer subset |
| 4 | `FAIL_audit_tau_unstable` | Bootstrap of τ_c (200 resamples) shows any τ has CV > 0.30 | Calibration too noisy; widen peer pool via amendment |
| 5 | `FAIL_recall_below_floor` | K=2 consensus recall on Psalm 19 single-letter variants < 0.999 | F53 rule does NOT close on Hebrew Psalm 19 at the locked floor; report cleanly |
| 6 | `FAIL_fpr_above_ceiling` | K=2 consensus FPR (peer-vs-peer pairs sampled at length-match) > 0.05 | Specificity insufficient; report cleanly |
| 7 | `PARTIAL_recall_above_99` | Recall ∈ [0.99, 0.999) AND FPR ≤ 0.05 | Partial closure; report as "indicative; not paper-grade" |
| 8 | **`PASS_consensus_100`** | Recall ≥ 0.999 AND FPR ≤ 0.05 | F53 rule generalises to Hebrew Psalm 19 at full pilot-grade |

### 2.5 What promotion does NOT mean

A `PASS_consensus_100` verdict on this pilot does **NOT**:

- Establish that F53 generalises to "all canonical scriptures" or "all oral-liturgical traditions". The pilot is one chapter, one tradition, one language.
- Reverse R53 (the Quran-side universal-scaling failure). Cross-tradition Hebrew success and within-Quran scaling failure are mutually consistent; the rule may be a class property without being a uniform property.
- Promote the pilot to a paper-grade finding without independent two-team replication.

If `PASS_consensus_100` fires, the natural follow-up is:
- `exp104b`: same protocol on a different Tanakh chapter (e.g. Psalm 23 or Psalm 1) — *replicates* within Hebrew.
- `exp104c`: same protocol on a Greek New Testament chapter — *generalises* across language.
- `exp104d`: same protocol on a Sanskrit Vedic hymn — *generalises* across language family.

Each follow-up is a fresh hash-locked PREREG.

---

## 3. Frozen constants

- Compressor levels: `gzip-9`, `bz2-9`, `lzma-preset-9`, `zstd-9` (identical to `exp95c`).
- Consensus K = **2** (identical to `exp95c`).
- τ percentile: **5th** of length-matched ctrl-Δ distribution (identical to `exp95c`).
- Length-match window: target ± 30 % (identical to `exp95c`).
- Hebrew letter inventory: 22 consonants, finals folded; niqqud + te'amim stripped.
- Seed: `SEED = 42`.
- Bootstrap n: 200 (for τ stability check).

---

## 4. Audit hooks

- **Corpus-hash sentinel**: SHA-256 of `data/corpora/he/tanakh_wlc.txt` must match the value in `corpus_lock.json`.
- **PREREG-hash sentinel**: SHA-256 of this PREREG.md must match `_PREREG_EXPECTED_HASH` in run.py (when run.py is written).
- **Normaliser-fingerprint sentinel**: SHA-256 of the normalisation function source code is logged; mismatch on re-run flags drift.
- **Compressor-version sentinel**: Python `gzip` / `bz2` / `lzma` / `zstd` library versions logged; major-version drift is a warning, not a failure (NCD is robust to minor zlib changes by design).
- **τ-stability sentinel**: bootstrap CV of each τ_c ≤ 0.30; otherwise branch 4 fires.
- **No-leak sentinel**: τ calibration uses peer-vs-peer comparisons only; no Psalm 19 variant is allowed to leak into the calibration sample.

---

## 5. Honesty clauses

### 5.1 No re-roll on chapter selection

Psalm 19 is locked. If the verdict is FAIL on Psalm 19, we do **not** rerun on Psalm 23 to "rescue" the cross-tradition story. A different chapter is a different experiment with its own PREREG.

### 5.2 No τ transfer from Arabic

The locked Arabic τ from `exp95c` is **NOT** used. Calibration is from-scratch on Hebrew peers. This is essential because compressor behaviour is alphabet-dependent.

### 5.3 No selective compressor reporting

All four compressors run; their per-pair Δ values are recorded in the receipt regardless of whether they make it through the K=2 gate. Reporting cannot omit a compressor that disagrees.

### 5.4 No post-hoc consensus-K change

K = 2 is locked. We do not switch to K = 1 or K = 3 to find a kinder verdict. (K = 1 / K = 3 are pre-allowed as *reported metrics* in the receipt for transparency, but the verdict is K = 2.)

---

## 6. Reproduction recipe (when run.py is built)

```powershell
# 1. Verify Hebrew corpus
python scripts/_verify_corpus_lock.py
# 2. Run pilot
python -m experiments.exp104_F53_tanakh_pilot.run
# 3. Audit
python scripts/integrity_audit.py
```

Receipt: `results/experiments/exp104_F53_tanakh_pilot/exp104_F53_tanakh_pilot.json`.

---

## 7. Cross-references

- Quran-side F53 receipt: `results/experiments/exp95c_multi_compressor_adiyat/exp95c_multi_compressor_adiyat.json`.
- Quran-side F54 retraction: `RETRACTIONS_REGISTRY.md` Category L, R53.
- BLOCKED parent (cross-tradition for all 5 traditions): `experiments/expP4_F53_cross_tradition/PREREG.md` (H38).
- Hebrew loader: `src/raw_loader.py::load_hebrew_tanakh` (existing); chapter-segmenter: TBD.

---

## 8. Frozen-time fingerprint

This document's SHA-256 is computed **after** all text above is final and **before** any Hebrew compression call is issued. The hash is written to `experiments/exp104_F53_tanakh_pilot/PREREG_HASH.txt`. **No `run.py` exists at the time of this PREREG-lock**, by design. When `run.py` is added, its `_PREREG_EXPECTED_HASH` must match this file's hash; mismatch invalidates the run.
