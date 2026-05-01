# exp104c_F53_psalm78 — Amendment PREREG (Phase 3, single-chapter cross-tradition F53 pilot)

**Hypothesis ID**: H59c (amendment of H59 / H59b)
**Status**: pre-registered, hash-locked **before** the run is executed.
**Patch context**: v7.9-cand patch H V3.2 — second amendment of `exp104_F53_tanakh_pilot` after exp104 (Psalm 19) returned `BLOCKED_psalm_19_too_short` and exp104b (Psalm 119) returned `FAIL_audit_peer_pool_size`. This amendment selects **Psalm 78** as the target chapter — the **second-longest** Psalm at 2,384 consonant-skeleton letters, mid-range enough that the locked ±30% peer-window naturally yields 114 narrative-Hebrew peer chapters (verified pre-run by `scripts/_psalm78_peer_sizing.py`, well above the locked floor of 100).
**Supersedes**: nothing — both prior receipts (`exp104_F53_tanakh_pilot` BLOCKED on Psalm 19; `exp104b_F53_psalm119` FAIL_audit_peer_pool_size on Psalm 119) remain preserved as protocol-correct pre-registration outcomes. This is the third filed PREREG in the H59 amendment chain, NOT a re-run.

---

## 0. Why this exists (one paragraph)

Two prior PREREG-locked attempts to test F53 on a Hebrew Psalm produced honest pre-registration outcomes that left the **substantive cross-tradition question unanswered**: exp104 hit branch 2 (Psalm 19 below the chapter-length floor); exp104b hit branch 3 (Psalm 119 above the peer-window upper bound — the longest Psalm has almost no length-matched narrative peers). Psalm 78 (52 verses, 2,384 consonant-skeleton letters; the **second-longest Psalm**, well above the 1,000-letter floor and with abundant length-matched peers) is the cleanest candidate to actually exercise the locked protocol. Pre-run sizing diagnostic confirms **114 narrative-Hebrew chapters** fall in the locked ±30% window [1,668, 3,099] letters around Psalm 78 — comfortably above the floor of 100 and below the cap of 200.

**No re-roll selection bias**: Psalm 78 is the *second-longest* Psalm objectively (after the now-failed Psalm 119); selecting it is forced by the length-floor + peer-pool-size constraints, not by any expected-outcome consideration. Psalm 78 is also independently interesting because it is a long historical-narrative-style Psalm (rather than a wisdom or acrostic Psalm), making it the most stylistically-similar-to-narrative-Hebrew test case — i.e., the *harder* test, since the peer pool is naturally close in style. This makes any successful K=2 closure on Psalm 78 stronger evidence than the same closure on a shorter, stylistically-distinctive Psalm would be.

---

## 1. Hypothesis (one paragraph)

**H59c (F53 cross-tradition Hebrew Psalm 78 pilot)**: Under the K=2 multi-compressor consensus rule with τ thresholds calibrated *on the Hebrew narrative-peer pool* (per-compressor 5th percentile of length-matched ctrl-Δ NCD distribution; identical recipe to `exp95c`, exp104, and exp104b), single-consonant substitution on **Psalm 78** (Westminster Leningrad Codex; 52 verses, 2,384 consonant-skeleton letters) achieves **recall ≥ 0.999** with **FPR ≤ 0.05** against the same calibration peer pool. Equivalently: every single-letter substitution on Psalm 78 must produce K=2-consensus NCD shifts that exceed the locked Hebrew τ on at least 2 of 4 compressors {gzip-9, bz2-9, lzma-preset-9, zstd-9}.

**Pilot scope**: one Tanakh chapter only (Psalm 78). Generalisation to whole Tanakh / whole Torah / whole Psalter is OUT of scope here.

---

## 2. Locked decision rules (all inherited from exp104 §2; only the target chapter changes)

### 2.1 Frozen target text

- **Target chapter**: **Psalm 78** in the Westminster Leningrad Codex (WLC) edition. Pulled via `experiments/exp104_F53_tanakh_pilot/run.py::_load_tanakh_chapters`.
- **Letter normalisation**: Hebrew consonant skeleton (22 letters), final-form letters folded to base form, niqqud + te'amim stripped (identical normaliser, `_hebrew_skeleton`).
- **Why Psalm 78**: second-longest Psalm; 52 verses; 2,384 consonant-skeleton letters; abundant length-matched narrative peers (114 chapters in locked ±30% window — verified pre-run); historical-narrative style maximises stylistic overlap with the peer pool, making any successful closure the harder rather than easier test.

### 2.2 Frozen peer pool (identical to exp104 §2.2 by design — ONLY the chapter target changes)

- Hebrew narrative pool: chapters of the Hebrew Bible *outside* the Psalter, drawn from Genesis, Exodus, Joshua, Judges, Samuel-Kings narrative books.
- Length-matched to Psalm 78 ± 30 % (i.e. **[1,668, 3,099]** letters per peer chapter).
- Pre-run sizing: **114 narrative chapters** fall in this window; the random-shuffle subset of 200 is naturally capped at the available 114 (no upper-bound binding).

### 2.3 Frozen τ-calibration protocol (identical to exp104 §2.3)

For each compressor c ∈ {gzip-9, bz2-9, lzma-preset-9, zstd-9}, compute on the peer pool:

1. For each peer chapter, sample `N_CALIB_VARIANTS_PER_PEER = 30` single-consonant substitution variants.
2. For each (peer, variant), compute `Δ_c = NCD_c(peer, peer_with_variant) − NCD_c(peer, peer)`.
3. The locked Hebrew τ_c is the **5th percentile** of the resulting `Δ_c` distribution.
4. The K=2 rule fires on a Psalm 78 variant iff at least 2 of 4 compressors have `Δ_c ≥ τ_c`.

### 2.4 Verdict ladder (strict order; first match wins; identical to exp104 §2.4 with chapter substitution)

| # | Branch | Trigger | Implication |
|---|---|---|---|
| 1 | `BLOCKED_corpus_missing` | WLC missing or chapter not found | Acquire / fix loader |
| 2 | `BLOCKED_psalm_78_too_short` | Psalm 78 has < 1,000 letters or < 10 verses (highly unlikely — pre-run confirms 2,384 / 52) | Choose a different chapter via amendment |
| 3 | `FAIL_audit_peer_pool_size` | `n_peer_units < 100` (very unlikely — pre-run confirms 114) | Widen window via amendment OR pick different peer subset |
| 4 | `FAIL_audit_tau_unstable` | Bootstrap of τ_c (200 resamples) shows any τ has CV > 0.30 | Calibration too noisy; widen pool via amendment |
| 5 | `FAIL_recall_below_floor` | K=2 consensus recall on Psalm 78 single-letter variants < 0.999 | F53 rule does NOT close on Hebrew Psalm 78 at the locked floor; report cleanly |
| 6 | `FAIL_fpr_above_ceiling` | K=2 consensus FPR (peer-vs-peer pairs sampled at length-match) > 0.05 | Specificity insufficient |
| 7 | `PARTIAL_recall_above_99` | Recall ∈ [0.99, 0.999) AND FPR ≤ 0.05 | Partial closure; not paper-grade |
| 8 | **`PASS_consensus_100`** | Recall ≥ 0.999 AND FPR ≤ 0.05 | F53 rule generalises to Hebrew Psalm 78 at full pilot-grade |

### 2.5 What promotion does NOT mean (inherited)

A `PASS_consensus_100` verdict on this pilot does **NOT** establish that F53 generalises to "all canonical scriptures" or "all oral-liturgical traditions". The pilot is one chapter, one tradition, one language. It WOULD however establish the first **single-chapter cross-language** F53 datapoint, and would justify follow-up PREREGs (exp104d Greek NT, exp104e Sanskrit Vedic, exp104f Pali Canon).

---

## 3. Frozen constants (identical to exp104 except target chapter)

- All compressor levels, K=2, τ-percentile, length-match-frac, normaliser, seeds, bootstrap-N: identical to exp104.
- **CHANGED**: `TARGET_CHAPTER = "עח"` (Psalm 78, in Hebrew letter notation: ayin-chet = 70+8 = 78).
- All other PREREG-locked constants from exp104_F53_tanakh_pilot/PREREG.md §3 are inherited verbatim.

---

## 4. Audit hooks (identical to exp104 §4, unchanged)

- Corpus-hash, PREREG-hash, normaliser-fingerprint, compressor-version, τ-stability, no-leak — all sentinels carried over.

---

## 5. Honesty clauses

### 5.1 Pre-run sizing was an objective check, not a fishing expedition

The peer-window-size diagnostic (`scripts/_psalm78_peer_sizing.py`, run 2026-04-28 night BEFORE this PREREG was hash-locked) tested all Psalms ranked by length and confirmed Psalm 78 yields 114 peers at ±30%. This is a **size diagnostic**, NOT a verdict diagnostic — it does not predict whether the K=2 closure will pass; it only confirms the protocol is *executable* on this chapter.

### 5.2 No re-roll on chapter selection (after this amendment)

Psalm 78 is locked. If the verdict is FAIL on Psalm 78, we do **not** rerun on a different Psalm to "rescue" the cross-tradition story. A different chapter is a different experiment with its own PREREG.

### 5.3 No τ transfer from Arabic (unchanged)

Locked Arabic τ from `exp95c` is **NOT** used. Calibration is from-scratch on Hebrew peers.

### 5.4 No selective compressor reporting / no post-hoc K change (unchanged)

K = 2 is locked; all 4 compressors run; per-pair Δ values logged regardless of K-2 gate outcome.

### 5.5 Honest declaration: this is the third filed PREREG in the H59 chain

The amendment chain is:
- `exp104_F53_tanakh_pilot` (H59, Psalm 19) → `BLOCKED_psalm_19_too_short` (chapter-length floor)
- `exp104b_F53_psalm119` (H59b, Psalm 119) → `FAIL_audit_peer_pool_size` (peer-window upper-bound)
- `exp104c_F53_psalm78` (H59c, Psalm 78) → this PREREG; first chapter that satisfies BOTH the chapter-length floor AND the peer-window count requirement under the locked ±30% rule

All three receipts are preserved unchanged. The chain is auditable: each step's failure mode informed the next step's chapter choice; no rule was relaxed; only the chapter target moved.

---

## 6. Reproduction recipe

```powershell
# 1. Verify Hebrew corpus
python scripts/_verify_corpus_lock.py
# 2. Run pilot
python -m experiments.exp104c_F53_psalm78.run
# 3. Audit
python scripts/integrity_audit.py
python scripts/zero_trust_audit.py
```

Receipt: `results/experiments/exp104c_F53_psalm78/exp104c_F53_psalm78.json`.

---

## 7. Cross-references

- Original Psalm-19 BLOCKED: `results/experiments/exp104_F53_tanakh_pilot/exp104_F53_tanakh_pilot.json`
- Psalm-119 FAIL_audit: `results/experiments/exp104b_F53_psalm119/exp104b_F53_psalm119.json`
- Quran-side F53: `results/experiments/exp95c_multi_compressor_adiyat/exp95c_multi_compressor_adiyat.json`
- Quran-side F54 retraction: `RETRACTIONS_REGISTRY.md` Category L, R53
- Hebrew loader (re-used unchanged): `experiments/exp104_F53_tanakh_pilot/run.py::_load_tanakh_chapters`

---

## 8. Frozen-time fingerprint

This document's SHA-256 is computed **after** all text above is final and **before** any Hebrew compression call is issued. The hash is written to `experiments/exp104c_F53_psalm78/PREREG_HASH.txt`. **No `run.py` exists at the time of this PREREG-lock**, by design. When `run.py` is added, its `_PREREG_EXPECTED_HASH` must match this file's hash; mismatch invalidates the run.
