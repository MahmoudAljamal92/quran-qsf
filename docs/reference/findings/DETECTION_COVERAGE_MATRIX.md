# QSF Detection-Coverage Matrix — 10-layer forgery-detection stack

**Status**: SUMMARY (2026-04-29 afternoon, **V3.12 update** — adds layers 9 (F73 trigram-boundary) and 10 (F72 D_QSF unified single-statistic)). Compiled in response to the user-asked question *"why are we using only F-things?"*

**Purpose**: a single page mapping every forgery-detection layer in the project to (a) the *scale* of forgery it catches, (b) the *statistic* it computes, (c) the *receipt* and pass/fail status. Resolves the cross-doc audit finding that earlier framings under-stated the project's coverage by treating only F44–F71 as the "forgery toolkit" while ignoring the legacy 5-D Φ_M results (rows 1–17 of `RANKED_FINDINGS.md`) which carry the macro-scale and word-reorder findings.

---

## 1. The 10 detection layers

The project's forgery-detection coverage spans **four scales** (letter / word / verse / sūrah) crossed with **three metric families** (pointwise distance, multivariate ellipsoid, unified single-statistic). Each layer has its own *receipt* and its own *failure mode*.

| # | Scale | Forgery type | Detector | Statistic | Verdict | Receipt |
|---|---|---|---|---|---|---|
| **1** | letter (interior) | 1 letter substituted, mid-word | **F55** | `Δ_bigram ≥ 2` (analytic τ = 2.0) | PASS — recall 1.000, FPR 0.000 (139,266 variants × 114 sūrahs) | `exp95j_bigram_shift_universal` |
| **2** | letter (k-letter) | k letters substituted anywhere | **F69** | `Δ_bigram ≤ 2k` *theorem* + `τ_k = 2k` | PASS_F55_multi_k_universal — recall ≥ 99.999%, FPR = 0%, 570k variants × 5 k-values | `exp118_multi_letter_F55_theorem` |
| **3** | word (internal) | Letters within a word reordered | **F55** (catches as side-effect) | within-word bigrams change | PASS by inheritance from F55 | `exp95j` |
| **4** | word (whole-word reorder within verse) | Words moved across boundaries; verse-final word changes | **D14 / 5D Φ_M multi-scale perturbation** | Cohen `d = 2.45`, +5.80 gap, 100% canon-farther | PROVED+ (97% paper-grade, row 15 of RANKED) | `phase_06_phi_m`, PAPER §4.3 |
| **5** | word (whole-word reorder within verse, verse-final preserved) | Word-swap that keeps verse-final letter | **F70 Form-3 (gzip fingerprint)** | sequence-sensitive compression Δ | recall 0.884 (single form); 0.930 combined OR | `exp117_verse_reorder_detector` |
| **6** | verse (2-verse swap) | Whole verses reordered within sūrah | **F70 Form-4 (combined OR(F1, F3)) + F73 Form-6 (V3.12 add)** | OR(EL-Markov, gzip, **trigram+#**) | F70 recall 0.930 → **F73 combined recall 0.946** (PARTIAL; closes 24 % of residual 0.07 gap) | `exp117`, `exp121_trigram_verse_reorder` |
| **7** | sūrah (structural) | Significant content / style change | **F1/F2/F3 / 5D Φ_M (legacy headline)** | Hotelling T² = 3,557; nested-CV AUC = 0.998 | PASS by 7 σ over Arabic peer pool, perm p < 1·10⁻⁴ | `expP7_phi_m_full_quran`, `phase_06_phi_m` |
| **8** | universal (alphabet-independent) | Apply F55+F69 to non-Arabic traditions | **F71** | recall = 1, FPR = 0 in 5 alphabets | PASS_F55_universal_across_5_traditions | `exp119_universal_F55_scope` |
| **9** *(V3.12)* | verse (2-verse swap, verse-final + gzip preserved) | Closes part of the F70 7 % gap | **F73 (trigram+verse-boundary, NEW)** | `Δ_trigram_boundary > 0` over 30-symbol alphabet (28 + space + #) | PARTIAL_PASS_F70_gap_partially_closed — Form-5 standalone 0.487, Form-6 combined 0.946 | `exp121_trigram_verse_reorder` |
| **10** *(V3.12)* | unified (all scales) | "Is the candidate text Quran-extremal in the cross-tradition pool?" | **F72 (D_QSF, NEW)** | `D_QSF(c) = √(Σ z²) ≥ Quran` (standardised Euclidean distance from 11-corpus centroid in 5-D universal space) | **PARTIAL — D_QSF(Quran) = 3.71 rank 1/11 with 23.7 % margin**; perm_p = 0.0931 just above 0.05 due to N=11 floor | `exp120_unified_quran_code` |

## 2. Coverage analysis: which forgery scales are covered?

| Forgery scale | Layers that catch it | Aggregate verdict |
|---|---|---|
| Single-letter substitution (any position) | 1 (F55), 2 (F69), 7 (5D Φ_M Hotelling for verse-final-affecting cases only) | ✅ caught (recall 1, FPR 0) |
| Multi-letter substitution (k ∈ {2, 3, 4, 5}) | 2 (F69) | ✅ caught (recall ≥ 99.999%, FPR 0) |
| Word-internal anagram | 1 (F55), 2 (F69) | ✅ caught |
| Word-reorder within verse (verse-final word changes) | 4 (D14 / 5D Φ_M) | ✅ caught (Cohen d = 2.45) |
| Word-reorder within verse (verse-final word PRESERVED) | 5 (F70 Form-3 gzip) | ✅ caught at 0.884 recall |
| 2-verse swap within sūrah | 6 (F70 Form-4 combined) | ⚠️ PARTIAL_PASS at 0.930 recall |
| Whole-sūrah forgery | 7 (5D Φ_M corpus-level) + 1+2 (per-sūrah letter-level) | ✅ caught (T² = 3,557, AUC 0.998) |
| Cross-language extension | 8 (F71) | ✅ caught (5 alphabets, 5 traditions) |
| Diacritics-only (ḥarakāt) edits | none — stripped by design | ❌ by design |
| Hamza-variant only (`أ`/`إ`/`آ`/`ٱ`) | none — folded by normaliser | ❌ by design |

## 3. The remaining (small) gap

After all 8 layers are deployed together, the only forgery type that escapes detection is **the intersection of**:
- 2-verse swap that *preserves* verse-final letter (very common in Quran due to high ن density), AND
- *preserves* gzip-fingerprint (similar compressed length), AND
- does NOT cross word boundaries within a verse (so the word-reorder-within-verse Cohen-d gap doesn't fire).

This intersection is empirically **~7%** of random 2-verse swaps (Form-4 misses 0.07 in `exp117_verse_reorder_detector`). To close the remaining ~7%, future work would add a trigram or LC2 path-cost detector at meso scale.

For Ṣanʿāʾ-style audits where verse-order is rarely in dispute (the disputes are letter-level), this gap is academic — the canonical detection toolkit (layers 1, 2, 4, 7, 8) catches everything.

## 4. Why we use both "F-things" and the 5D Φ_M

The legacy ranked table rows 1–43 (with named-finding tags F1/F2/F3 = T² / AUC / EL-classifier) and the F44–F71 modern bullet rows are **complementary, not competing**:

- **F1/F2/F3 (5D Φ_M / Hotelling T² / AUC = 0.998)** = the *macro-scale* multivariate fingerprint. Catches sūrah-level changes and word-reorderings that affect the verse-final-word (D14, Cohen d = 2.45).

- **F55 / F69 (bigram-shift theorem)** = the *micro-scale* letter-level detector. Catches arbitrary letter-substitution forgeries with mathematical guarantee `Δ ≤ 2k`.

- **F70 (sequence-aware verse-reorder)** = the *meso-scale* detector. Catches verse-reorderings that F55 is permutation-invariant to.

- **F71 (universal-scope)** = empirical proof that F55 + F69 are *alphabet-independent*. Generalises layer 1+2 to 5 traditions.

- **F63/F64/F66/F67 (rhyme-extremum)** = *cross-tradition Quran-distinctiveness* claims. Not forgery detectors per se, but the locked extrema that the metrology challenger (`tools/quran_metrology_challenge.py`) compares any candidate text against.

Together these are **8 detection layers + 4 distinctiveness claims** = 12 statistical receipts spanning the full forgery-detection problem.

## 5. Operational deployment

The `tools/` directory ships three command-line auditing tools that wrap the above:

- `tools/sanaa_compare.py` — two-text Δ_bigram + F68 gzip-fingerprint comparator (layers 1, 2, 6).
- `tools/quran_metrology_challenge.py` — Quran-as-reference-standard challenger (layers 4, 7) with corpus-median challenge OR paired comparison modes.
- `tools/sanaa_battery.py` — variant-fixture-driven audit on `data/external/sanaa_variants.json` (layers 1, 2, 5, 6 in one report).

The web UI `app/streamlit_forgery.py` exposes the detection layers in three modes: compare two texts / plant a k-letter edit / verse-reorder test.

## 6. What the toolkit cannot decide

For every layer, the verdict is *distance*, not *authenticity*. F55/F69 + 5D Φ_M + F70 + F71 + the metrology challenger together provide a **single replicable distance number** between any candidate text and the canonical Quran on each scale, plus an answer to *"does the candidate match or beat the Quran's extremum on the locked features?"*. They do **not** decide:

- Which reading is canonical / correct / prophetically-transmitted.
- The historical authorship of any text.
- Theological / spiritual / metaphysical questions.

These are paleographic / chains-of-transmission / theological questions, outside the project's empirical methodology. The toolkit's job is to *quantify the gap* objectively; the *interpretation* of that gap belongs to the human reader.
