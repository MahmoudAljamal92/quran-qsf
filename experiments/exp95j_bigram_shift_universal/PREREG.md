# exp95j_bigram_shift_universal — Pre-registration

**Hypothesis ID**: H43
**Status**: pre-registered, frozen 2026-04-26 night, **before any frozen-τ scoring on V1**.
**Patch context**: v7.9-cand patch G post-V1, rescue-path C-strict (analytic bound; no τ calibration).
**Predecessor**: `exp95i_bigram_shift_detector` (H42) returned `FAIL_audit_hook_violated` due to Q:108 (62 letters) lacking length-matched peers in `[0.5n, 1.5n]`. The exp95i receipt empirically confirms that **every** V1 variant has `Δ_bigram ∈ [1.0, 2.0]` and **every** length-matched peer pair has `Δ_bigram ≥ 58.5`, but the per-surah ctrl-coverage hook locked in H42 PREREG correctly fired and the receipt honors it. exp95j replaces data-calibrated τ with a theorem-derived τ = 2.0.

---

## 1. Hypothesis

**H43**: under detector "fire iff `0 < Δ_bigram(canon_X, candidate) ≤ 2.0`", single-consonant-substitution forgeries on every Quran surah are detected at per-surah recall = 1.000 with global FPR (against full non-Quran peer pool, all `(surah, peer)` pairs) ≤ 0.05.

---

## 2. What this is and is not

**This IS**: an analytic-ceiling, calibration-free, length-independent symbolic forgery detector. τ = 2.0 is fixed by a theorem about bigram counts under single-character substitution.

**This is NOT**: a claim about Quranic structural distinctiveness; a replacement for Levenshtein/SHA-256; a re-litigation of R53; a cross-tradition claim.

---

## 3. Statistic and theorem

### 3.1 Bigram statistic
`hist_2(s) = Counter(s[i:i+2] for i in range(len(s)-1))` on `letters_28(s)`. `Δ_bigram(a, b) = ||hist_2(a) − hist_2(b)||_1 / 2`.

### 3.2 Theorem: max Δ_bigram for single substitution = 2.0

**Statement**: For any string `c` of length `n ≥ 2` and any single-character substitution at position `p` producing `v`, `Δ_bigram(c, v) ≤ 2`.

**Proof**: Interior `p`: 2 bigrams removed, 2 added → L1 ≤ 4 → /2 ≤ 2. Edge `p ∈ {0, n−1}`: 1 removed, 1 added → L1 ≤ 2 → /2 ≤ 1. ∎

### 3.3 Frozen detector
`τ_high = 2.0`. Fire iff `0 < Δ_bigram(canon_X, candidate) ≤ 2.0`.

### 3.4 Variant set
V1 from `experiments.exp95e_full_114_consensus_universal._enumerate.enumerate_v1`.

### 3.5 Peer pool
Full non-Quran `CORPORA`, no length matching. τ is frozen so calibration is moot; length-mismatched pairs only increase Δ, never enter the fire window.

---

## 4. Verdict ladder (first-match wins)

1. `FAIL_audit_hook_violated` — some V1 variant has `Δ > 2.0 + 1e−9` (theorem violated)
2. `FAIL_recall_below_floor` — aggregate recall < 1.0 (cannot fire if theorem holds)
3. `FAIL_per_surah_floor` — some surah recall < 1.0 (cannot fire if theorem holds)
4. `FAIL_global_fpr_overflow` — global FPR > 0.05
5. `PARTIAL_fpr_band_5_to_50pct` — global FPR ∈ (0.05, 0.50]
6. `PASS_universal_perfect_recall` — recall = 1.0 ∧ FPR ≤ 0.05
7. `PASS_universal_perfect_recall_zero_fpr` — recall = 1.0 ∧ FPR = 0.0

---

## 5. Honesty clauses

- **5.1 No τ tuning**: τ frozen at 2.0; any change requires a fresh PREREG.
- **5.2 No selective peer pool**: full non-Quran CORPORA in iteration order.
- **5.3 No re-running on FAIL_***: if branch 1 fires, investigate the pipeline.
- **5.4 PASS does not un-retract R53**: H43 is a different detector class (symbolic bigram, not NCD).
- **5.5 PASS does not promise cross-tradition universality**: empirical FPR is for Quran-vs-Arabic-peers on this corpus only.
- **5.6 Insertions/deletions**: have Δ ≤ 1.5 by extension of theorem 3.2; same τ catches them, but V1 is substitutions only.

---

## 6. Frozen constants

- Variant enumeration: `_enumerate.enumerate_v1`
- Letter normalisation: `letters_28`
- Corpus checkpoint: `phase_06_phi_m` (SHA-256 verified)
- `τ_high = 2.0` (no calibration)
- Audit tolerance: `1e−9`
- Recall floor: `1.000` (theorem-locked)
- FPR floor: `0.05`

---

## 7. Protocol

1. Load `phase_06_phi_m`, verify SHA-256.
2. For each of 114 surahs: compute `canon_letters`, `canon_bg`. Enumerate V1 variants; for each, compute `Δ_var = Δ_bigram(canon, variant)`.
3. Audit hook: if `max(Δ_var) > 2.0 + 1e−9`, verdict `FAIL_audit_hook_violated`.
4. Detector: variant fires iff `0 < Δ_var ≤ 2.0`. Per-surah recall = mean fire rate.
5. Build full non-Quran peer pool. Cache `bigrams_of(peer)` per peer.
6. For each `(surah, peer)` pair: compute `Δ_peer`. Pair fires iff `0 < Δ_peer ≤ 2.0`.
7. Global FPR = firing pairs / (114 × |peer_pool|).
8. Apply verdict ladder.
9. Write receipt with `prereg_hash_actual` matching this document's SHA-256.

---

## 8. Reproduction

```powershell
python experiments\exp95j_bigram_shift_universal\run.py
```

Wall-time: ~3–8 min (variant Δ analytic; peer Δ via cached counters; ~549 K peer pairs).

---

## 9. Cross-references

- Predecessor: `experiments/exp95i_bigram_shift_detector/PREREG.md` (H42), receipt at `results/experiments/exp95i_bigram_shift_detector/`.
- Sibling: `exp95h` (H41, FAIL_no_clean_split_p90), `exp95f` (H39, in flight).
- V1 receipt: `results/experiments/exp95e_full_114_consensus_universal/v1/`.
- Planning doc: `docs/reference/sprints/POST_V1_PATHS_FORWARD_2026-04-26.md` §2.3.

---

## 10. Frozen-time fingerprint

This document's SHA-256 is computed **after** all text above is final and **before** any scoring. Logged in:
- `experiments/exp95j_bigram_shift_universal/PREREG_HASH.txt`
- The receipt's `prereg_hash_actual` field.
