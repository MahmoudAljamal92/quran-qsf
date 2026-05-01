# PREREG — exp112_F55_daodejing_bigram: F55 universal forgery detector on Classical Chinese Daodejing (Chapter 1)

**Status**: SEALED 2026-04-29 morning, v7.9-cand patch H V3.8.
**Hypothesis ID**: H67.
**Pairs with**: F55 (`exp95j_bigram_shift_universal`, Quran-side; locked) + F59 (Hebrew Psalm 78) + F60 (Greek Mark 1) + F61 (Pāli DN 1) + F62 (Avestan Yasna 28).
**Author intent**: extend F55 from 5 alphabetic / abjad / IAST-transliterated traditions to the **first logographic / character-based writing system** tested. Validates F55 as **script-architecture-agnostic** (alphabet-free), not just language-family-agnostic.

---

## 0. Honest disclosure (pre-run, locked at PREREG seal)

1. **F55 is a mathematical theorem** (Theorem 3.2 in `exp95j_bigram_shift_universal/PREREG.md`): for any unit U over an arbitrary discrete alphabet, any single-token substitution V satisfies Δ_bigram(U, V) ≤ 2. The theorem is alphabet-free and applies equally to logographic, syllabic, abjad, alphabetic, and any other discrete tokenisation system. **F55 will pass on Daodejing by theorem.** The empirical question is whether peer-pool FPR = 0, i.e., whether different chapters of the Daodejing have sufficiently different character-bigram distributions that none of them fall within τ = 2.0 of each other.

2. **This is NOT a Quran-distinctiveness claim.** F55 is detector deployment-readiness — it works on any natural-language discrete-token corpus. exp112 establishes that F55's mathematical theorem deploys on the 6th language family / first logographic system tested. F55 cross-tradition results (F59-F62, exp112) are infrastructure validation; the cross-tradition Quran-distinctiveness claim is F63/F64 (separate experiment family).

3. **Target = Chapter 1 of the Daodejing** (Wang Bi recension, 王弼本; 道可道，非常道...). Selected for protocol consistency with the F55 cross-tradition convention of targeting the FIRST chapter (Mark 1 in F60, DN 1 in F61, Yasna 28 in F62 was the first Gatha, Psalm 78 was a length-feasible exception). The chapter is short (~80 Chinese characters after punctuation strip) but F55's analytic theorem holds independent of length.

---

## 1. Question

Does F55 (analytic-bound bigram-shift detector with frozen τ = 2.0, no calibration) generalise off-shelf to **Classical Chinese Daodejing Chapter 1** with per-variant recall = 1.000 and per-(canon, peer) FPR = 0.000 against the 80-chapter Daodejing peer pool, in the **logographic Chinese-character alphabet** (corpus-attested distinct CJK Unified Ideographs from Daodejing only), **zero parameter change** from prior F55 runs?

---

## 2. Data — locked

**Source**: Project Gutenberg eBook #7337, Wang Bi recension of the Daodejing (Traditional Chinese, 繁體). Public-domain. Prepared by Ching-yi Chen.

**File**: `data/corpora/zh/daodejing_wangbi.txt` (21,643 bytes).
**SHA-256**: `a05c5cb00650263e61d107dbeb7f8b887752bcc82fd42fd286b928d2a4d527bd` (locked in `data/corpora/zh/manifest.json`).
**Total chapters**: 81.

**Skeleton normaliser (locked)**: keep ONLY characters in CJK Unified Ideographs (U+4E00–U+9FFF) and CJK Unified Ideographs Extension A (U+3400–U+4DBF) and CJK Compatibility Ideographs (U+F900–U+FAFF). Strip all punctuation (中文標點 like ，。！？﹔「」『』〈〉《》『』『』), whitespace, line breaks, ASCII, and any other non-CJK-ideograph characters. This produces a flat string of Han characters per chapter.

**Target unit**: Chapter 1 (道可道，非常道...). Skeleton length expected ~60-80 characters.
**Peer pool**: chapters 2-81 (80 chapters). No length matching (mirroring F60 / F61 / F62 protocol).

**F55-family `PEER_AUDIT_FLOOR`**: 50 (per F62 PREREG §2.1 amendment). Daodejing has 80 peer chapters, comfortably above floor.

---

## 3. Protocol

Identical to `exp95j_bigram_shift_universal/run.py` with three protocol deltas:
- Replace Arabic `letters_28` normaliser with the CJK-ideograph skeleton above.
- Replace `quran_bare.txt` loader with Daodejing chapter loader (split on `第N章` markers; index by chapter number; chapter 1 is the target).
- Replace 28-letter Arabic alphabet with the corpus-attested distinct CJK character set from Daodejing only (each character that appears in the corpus skeleton).

Frozen constant: τ = 2.0 (analytic theorem upper bound).

### 3.1 Variant generation (recall test)

**F55 firing rule (inherited byte-exact from `exp95j_bigram_shift_universal/run.py:182`)**: the detector fires when `0 < Δ_bigram ≤ τ_HIGH = 2.0`. τ is an UPPER BOUND on Δ, not a lower bound — by theorem any single-character substitution produces Δ ≤ 2, so the firing condition `Δ ≤ τ` separates "single-char variants" (Δ ∈ (0, 2]) from "different texts" (Δ ≫ 2). Recall = fraction of variants that fire (target: 1.000 by theorem). Peer FPR = fraction of peer pairs that fire (target: 0.000, i.e., no peer chapter is mistaken for a single-char variant of the target).

For Chapter 1 skeleton string `s` of length `n`:
- For each position `i` in 0..n-1:
  - For each character `c'` in (corpus_attested_chars - {s[i]}):
    - Construct variant `s_var = s[:i] + c' + s[i+1:]`
    - Compute Δ_bigram(s, s_var) = ‖hist_2(s) − hist_2(s_var)‖_1 / 2
    - Detector fires if `0 < Δ_bigram ≤ τ = 2.0`.
- Total variants: `n × (|corpus_attested_chars| - 1)`.

### 3.2 Peer FPR test

For each peer chapter c ∈ chapters 2-81:
- Compute Δ_bigram(s_chapter_1_skeleton, s_chapter_c_skeleton)
- Detector fires if `0 < Δ_bigram ≤ τ = 2.0` (this would be a FALSE POSITIVE — the detector mistakes a different chapter for a single-char variant of the target).
- Total peer comparisons: 80.

### 3.3 Decision rule (locked)

PASS iff:
1. **Recall** (variants): all variants fire under (0 < Δ ≤ τ). (n_variants_firing / n_variants_total = 1.000000)
2. **FPR** (peers): no peer pair fires under (0 < Δ ≤ τ). (n_peer_firing / n_peers = 0.000000)
3. **Theorem audit hook A1**: max(variant Δ over all variants) ≤ 2.000000 + 1e-9.
4. **Peer pool size audit hook A2**: |peers| ≥ 50.
5. **Target floor audit hook A3**: target chapter 1 skeleton has ≥ 30 ideographs (post-normalisation; lowered from F60's 1,000-letter floor because Daodejing chapters are short by tradition; F62 / Avestan Yasna 28 was 1,658 letters which is comparable scale post-normalisation; Daodejing chapter 1 is shorter still).
6. **Determinism audit hook A4**: re-score 10 randomly-chosen variants and verify identical Δ values byte-for-byte.
7. **Skeleton sentinel A5**: chapter 1 normalised skeleton starts with `道可道非常道名可名非常名...` (the canonical opener with punctuation stripped).

### 3.4 Verdict ladder

- **PASS_universal_perfect_recall_zero_fpr** if §3.3 conditions 1-7 hold.
- **FAIL_recall_below_unity** if §3.3 condition 1 fails (would invalidate the theorem; methodologically improbable).
- **FAIL_peer_fpr_nonzero** if §3.3 condition 2 fails (some peer chapter pair compresses similarly enough to fire; substantive informative result).
- **FAIL_audit_*** for any audit hook failing.

---

## 4. Reporting — locked at PREREG seal

The receipt MUST report:
- Variant recall (n_pass / n_total), peer FPR (n_fail / n_peers)
- max(variant Δ) and min(peer Δ)
- Per-peer Δ for the 5 closest peer chapters
- Length-normalised per-character safety margin (min(peer Δ) / target_skeleton_length)
- Skeleton character count, distinct-character count
- Wall-time
- PREREG hash match

---

## 5. What this experiment does NOT establish

- That F55 is Quran-distinctive cross-tradition (F55 is mathematical-theorem-driven; F63/F64 is the actual cross-tradition Quran-distinctiveness claim).
- That F55 generalises to ALL logographic systems (only Classical Chinese Daodejing tested; Egyptian hieroglyphic, Sumerian cuneiform, Mayan, Tangut, Naxi Dongba, etc. remain).
- That F55 generalises to vertical-traditional or oracle-bone Chinese (Wang Bi text in modern Traditional Chinese is the editorial reconstruction; not direct attestation of pre-Qin Chinese).
- That the Daodejing is a "short" or "long" canonical text — F55 is length-agnostic by theorem.
- That this is a Quran-related claim of any kind — it is a 6th-language-family deployment-readiness test of a mathematical-theorem-driven detector.

---

## 6. Sealed prereg hash (auto-computed by run.py at execution time)

To be filled in by execution.

---

**END PREREG (sealed pre-run; no edits permitted).**
