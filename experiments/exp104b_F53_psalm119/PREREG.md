# exp104b_F53_psalm119 — Amendment PREREG (Phase 3, single-chapter cross-tradition F53 pilot)

**Hypothesis ID**: H59b (amendment of H59)
**Status**: pre-registered, hash-locked **before** the run is executed.
**Patch context**: v7.9-cand patch H V3.2 — direct amendment of `exp104_F53_tanakh_pilot` after its first execution returned `BLOCKED_psalm_19_too_short` (Psalm 19 had only 533 consonant-skeleton letters; the original PREREG floor was 1,000).
**Supersedes**: nothing — the original `exp104_F53_tanakh_pilot` receipt remains preserved as the protocol-correct BLOCKED outcome on Psalm 19. This is a new pre-registration with a different target chapter.

---

## 0. Why this exists (one paragraph)

The original `exp104_F53_tanakh_pilot` (PREREG hash `30694bfb…`, run 2026-04-28 night) executed against Psalm 19 (target locked in PREREG §2.1) and returned `BLOCKED_psalm_19_too_short` because the locked floor of 1,000 consonant-skeleton letters was not met (actual = 533 letters). The receipt is preserved at `results/experiments/exp104_F53_tanakh_pilot/exp104_F53_tanakh_pilot.json` as the honest pre-registration outcome. This **amendment PREREG** moves the target chapter to **Psalm 119** (110 verses, 5,104 consonant-skeleton letters; the longest Psalm by an order of magnitude, traditionally known as the "alphabet psalm" with 22 stanzas of 8 verses each, one stanza per Hebrew consonant). All other locked decision rules are inherited unchanged. The substantive question (does F53 generalise to a non-Arabic oral-liturgical scripture?) is unchanged; only the operationalisation chapter is changed because the original chapter failed the chapter-length floor that the original PREREG itself locked.

**No re-roll is performed**: Psalm 119 was selected on the basis of being the **longest** Psalm (objectively rank-ordered by consonant-skeleton length, top of `scripts/_psalm_lengths.py` output), not on the basis of any expected verdict outcome. Psalms 78 (2,384 letters), 18 (1,720), 89 (1,687) etc. were viable alternatives; we picked the longest to maximise statistical power for the K=2 consensus rule. Psalm 119 is also independently interesting because of its acrostic structure — a deliberately constrained Hebrew composition — which may have an analogue effect to the Quran's verse-final-letter constraint and is therefore the harder rather than easier test case.

---

## 1. Hypothesis (one paragraph)

**H59b (F53 cross-tradition Hebrew Psalm 119 pilot)**: Under the K=2 multi-compressor consensus rule with τ thresholds calibrated *on the Hebrew narrative-peer pool* (per-compressor 5th percentile of length-matched ctrl-Δ NCD distribution; identical recipe to `exp95c` and to the original `exp104` PREREG §2.3), single-consonant substitution on **Psalm 119** (Westminster Leningrad Codex; 110 verses, 5,104 consonant-skeleton letters) achieves **recall ≥ 0.999** with **FPR ≤ 0.05** against the same calibration peer pool. Equivalently: every single-letter substitution on Psalm 119 must produce K=2-consensus NCD shifts that exceed the locked Hebrew τ on at least 2 of 4 compressors {gzip-9, bz2-9, lzma-preset-9, zstd-9}.

**Pilot scope**: one Tanakh chapter only (Psalm 119). Generalisation to whole Tanakh / whole Torah / whole Psalter is OUT of scope here.

---

## 2. Locked decision rules

### 2.1 Frozen target text

- **Target chapter**: **Psalm 119** in the Westminster Leningrad Codex (WLC) edition (the longest Psalm; an acrostic with 22 stanzas of 8 verses each). Pulled from the project's existing locked Hebrew corpus `data/corpora/he/tanakh_wlc.txt` via the local loader in `experiments/exp104_F53_tanakh_pilot/run.py::_load_tanakh_chapters` (book whitelist + strict chapter regex; verified against WLC structure 2026-04-28 night by `scripts/_psalm_lengths.py`).
- **Letter normalisation**: Hebrew consonant skeleton (22 letters), final-form letters folded to base form (mem-sofit → mem, etc.). **Niqqud and te'amim are stripped** before scoring (analogue to the Arabic 28-letter rasm). The exact normalisation function is `_hebrew_skeleton` in the run.py file inherited from `exp104_F53_tanakh_pilot`.
- **Why Psalm 119**: longest Psalm (110 verses, 5,104 consonant-skeleton letters); deliberately-constrained acrostic structure (analogous-but-different to the Quran's verse-final constraint, making it the harder rather than easier comparison); canonically bounded; widely-cited.

### 2.2 Frozen peer pool (inherited from exp104 PREREG §2.2, unchanged)

- **Hebrew narrative peer pool**: chapters of the Hebrew Bible *outside* the Psalter, drawn from Genesis, Exodus, Joshua, Judges, Samuel-Kings narrative books. Target n_units = 200, length-matched to Psalm 119 ± 30 % (i.e. 3,573–6,635 letters per peer chapter — narrower set than for Psalm 19 because Psalm 119 is much longer; the `LENGTH_MATCH_FRAC = 0.30` constant is unchanged from the original PREREG, but the absolute window shifts because the target letter count shifts).
- **Why narrative not poetic**: the calibration peer pool should be of the same broad rhetorical class as the target's surrounding non-target chapters; pure-poetic peers would over-tighten τ. Narrative biblical Hebrew is the natural ctrl class for "is this a Psalm-like passage?".
- **Note on peer-pool size at the longer length window**: it is possible that fewer than 200 narrative chapters fall in the [3,573, 6,635]-letter window (most Tanakh chapters are shorter than Psalm 119). If so, `BLOCKED_no_peers_in_band` may fire under the existing branch 3 audit floor (`n_peer_units < 100`). This outcome is acceptable and would be the protocol-correct response.

### 2.3 Frozen τ-calibration protocol (identical to exp104 §2.3)

For each compressor c ∈ {gzip-9, bz2-9, lzma-preset-9, zstd-9}, compute on the peer pool:

1. For each peer chapter, sample `N_CALIB_VARIANTS_PER_PEER = 30` single-consonant substitution variants (random.Random seeded; locked seed inherited).
2. For each (peer, variant), compute `Δ_c = NCD_c(peer, peer_with_variant) − NCD_c(peer, peer)`.
3. The locked Hebrew τ_c is the **5th percentile** of the resulting `Δ_c` distribution across all peer-variant pairs.
4. The K=2 rule fires on a Psalm 119 variant iff at least 2 of 4 compressors have `Δ_c ≥ τ_c`.

**Symmetry with Arabic side**: this is the same calibration recipe used for Arabic in `exp95c`; we are deliberately keeping it identical so a cross-language *failure* cannot be blamed on a calibration-protocol difference.

**No τ transfer from Arabic**: the locked Arabic τ from `exp95c` is **NOT** used. Calibration is from-scratch on Hebrew peers. This is essential because compressor behaviour is alphabet-dependent.

### 2.4 Verdict ladder (strict order; first match wins; identical to exp104 §2.4)

| # | Branch | Trigger | Implication |
|---|---|---|---|
| 1 | `BLOCKED_corpus_missing` | `data/corpora/he/tanakh_wlc.txt` missing or chapter-segmentation fails | Acquire / fix loader |
| 2 | `BLOCKED_psalm_119_too_short` | After normalisation, Psalm 119 has < 1,000 letters or < 10 verses | Choose a different pilot chapter via amendment PREREG (highly unlikely — pre-run check shows 5,104 / 110) |
| 3 | `FAIL_audit_peer_pool_size` | `n_peer_units < 100` after length-matching | Widen length window via amendment OR pick different peer subset |
| 4 | `FAIL_audit_tau_unstable` | Bootstrap of τ_c (200 resamples) shows any τ has CV > 0.30 | Calibration too noisy; widen peer pool via amendment |
| 5 | `FAIL_recall_below_floor` | K=2 consensus recall on Psalm 119 single-letter variants < 0.999 | F53 rule does NOT close on Hebrew Psalm 119 at the locked floor; report cleanly |
| 6 | `FAIL_fpr_above_ceiling` | K=2 consensus FPR (peer-vs-peer pairs sampled at length-match) > 0.05 | Specificity insufficient; report cleanly |
| 7 | `PARTIAL_recall_above_99` | Recall ∈ [0.99, 0.999) AND FPR ≤ 0.05 | Partial closure; report as "indicative; not paper-grade" |
| 8 | **`PASS_consensus_100`** | Recall ≥ 0.999 AND FPR ≤ 0.05 | F53 rule generalises to Hebrew Psalm 119 at full pilot-grade |

### 2.5 What promotion does NOT mean (inherited from exp104 §2.5)

A `PASS_consensus_100` verdict on this pilot does **NOT**:

- Establish that F53 generalises to "all canonical scriptures" or "all oral-liturgical traditions". The pilot is one chapter (Psalm 119 in particular has known structural peculiarities — the acrostic — that may not be representative).
- Reverse R53 (the Quran-side universal-scaling failure).
- Promote the pilot to a paper-grade finding without independent two-team replication.

Follow-up experiments (each a fresh hash-locked PREREG) would be:
- `exp104c`: same protocol on Psalm 78 (next-longest Psalm; replication within Hebrew without acrostic).
- `exp104d`: same protocol on a Greek New Testament chapter — generalises across language.
- `exp104e`: same protocol on a Sanskrit Vedic hymn — generalises across language family.

---

## 3. Frozen constants (all inherited from exp104 unless noted)

- Compressor levels: `gzip-9`, `bz2-9`, `lzma-preset-9`, `zstd-9` (identical to `exp95c`).
- Consensus K = **2** (identical to `exp95c` and original exp104).
- τ percentile: **5th** of length-matched ctrl-Δ distribution (identical).
- Length-match window: target ± 30 % (identical fractional window; absolute window shifts to [3,573, 6,635] letters because target shifts).
- Hebrew letter inventory: 22 consonants, finals folded; niqqud + te'amim stripped (identical normaliser).
- Seed: `SEED = 42`.
- Bootstrap n: 200 (for τ stability check).
- **CHANGED from exp104**: `TARGET_CHAPTER = "קיט"` (Psalm 119, in Hebrew letter notation: qof-yod-tet = 100+10+9 = 119).
- **CHANGED from exp104**: `PSALM_19_MIN_LETTERS` and `PSALM_19_MIN_VERSES` are renamed `TARGET_MIN_LETTERS` and `TARGET_MIN_VERSES` to keep the constant names accurate; their numerical values (1,000 / 10) are unchanged.

---

## 4. Audit hooks (inherited from exp104 §4, unchanged)

- **Corpus-hash sentinel**: SHA-256 of `data/corpora/he/tanakh_wlc.txt` must match the value in `corpus_lock.json` (same as exp104).
- **PREREG-hash sentinel**: SHA-256 of THIS PREREG.md must match `_PREREG_EXPECTED_HASH` in run.py (when run.py is written).
- **Normaliser-fingerprint sentinel**: SHA-256 of the normalisation function source code is logged; mismatch on re-run flags drift.
- **Compressor-version sentinel**: Python `gzip` / `bz2` / `lzma` / `zstd` library versions logged; major-version drift is a warning, not a failure.
- **τ-stability sentinel**: bootstrap CV of each τ_c ≤ 0.30; otherwise branch 4 fires.
- **No-leak sentinel**: τ calibration uses peer-vs-peer comparisons only; no Psalm 119 variant is allowed to leak into the calibration sample.

---

## 5. Honesty clauses (inherited from exp104 §5, with amendments)

### 5.1 No re-roll on chapter selection (after this amendment)

Psalm 119 is locked. If the verdict is FAIL on Psalm 119, we do **not** rerun on Psalm 78 to "rescue" the cross-tradition story. A different chapter is a different experiment with its own PREREG.

### 5.2 No τ transfer from Arabic (unchanged)

The locked Arabic τ from `exp95c` is **NOT** used. Calibration is from-scratch on Hebrew peers.

### 5.3 No selective compressor reporting (unchanged)

All four compressors run; their per-pair Δ values are recorded in the receipt regardless of whether they make it through the K=2 gate.

### 5.4 No post-hoc consensus-K change (unchanged)

K = 2 is locked. We do not switch to K = 1 or K = 3.

### 5.5 Honest declaration: this is a chapter amendment, not a redo

The original `exp104_F53_tanakh_pilot` receipt remains preserved as a BLOCKED outcome on Psalm 19. This amendment does NOT delete or modify it. The amendment exists because the original PREREG locked a chapter (Psalm 19) whose actual length under the locked normaliser was below the locked floor — a discoverable fact that the original PREREG was honest enough to ladder to BLOCKED rather than silently lower the floor. This amendment is filed with a fresh hash lock under a separate experiment ID (`exp104b_F53_psalm119`) so the amendment chain is fully auditable.

---

## 6. Reproduction recipe

```powershell
# 1. Verify Hebrew corpus
python scripts/_verify_corpus_lock.py
# 2. Run pilot
python -m experiments.exp104b_F53_psalm119.run
# 3. Audit
python scripts/integrity_audit.py
python scripts/zero_trust_audit.py
```

Receipt: `results/experiments/exp104b_F53_psalm119/exp104b_F53_psalm119.json`.

---

## 7. Cross-references

- Original Psalm-19 pilot (BLOCKED outcome): `results/experiments/exp104_F53_tanakh_pilot/exp104_F53_tanakh_pilot.json`.
- Quran-side F53 receipt: `results/experiments/exp95c_multi_compressor_adiyat/exp95c_multi_compressor_adiyat.json`.
- Quran-side F54 retraction: `RETRACTIONS_REGISTRY.md` Category L, R53.
- BLOCKED parent (cross-tradition for all 5 traditions): `experiments/expP4_F53_cross_tradition/PREREG.md` (H38).
- Hebrew loader (local strict variant): `experiments/exp104_F53_tanakh_pilot/run.py::_load_tanakh_chapters` (re-used unchanged).

---

## 8. Frozen-time fingerprint

This document's SHA-256 is computed **after** all text above is final and **before** any Hebrew compression call is issued. The hash is written to `experiments/exp104b_F53_psalm119/PREREG_HASH.txt`. **No `run.py` exists at the time of this PREREG-lock**, by design. When `run.py` is added, its `_PREREG_EXPECTED_HASH` must match this file's hash; mismatch invalidates the run.
