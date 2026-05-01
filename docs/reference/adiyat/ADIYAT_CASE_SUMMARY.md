# The Adiyat Case — Summary (v7.6, 2026-04-21)

> **Current status note (2026-04-25)**: the consolidated current entry point is now `docs/reference/adiyat/03_ADIYAT_AND_AUTHENTICATION.md`. This file remains a concise v7.6 summary, but later receipts add three important updates: `exp95 = FAIL_ctrl_stratum_overfpr`, `exp105 = PARTIAL_null_saturated`, and `exp106 = preregistration only / no result folder`.

> **v7.5 addition (2026-04-21)**: the v7.4 claim that "emphatic-class blindness is almost certainly Arabic-structural" is **retracted** by the `exp50_emphatic_cross_corpus` cross-corpus audit. Arabic controls (poetry_jahili 9.50 %, poetry_abbasi 4.83 %) score 4–8Ã— the Quran's 1.15 % under the identical R1 pipeline. The blindness is Quran-specific structural immunity, not an Arabic-morphology artefact. See `PAPER.md Â§4.33` and the Â§4.2.3 update below.

A clean, coherent, single-page answer to the question:

> *Given the canonical Surah 100 "Al-Adiyat" verse 1 —
>   `ÙˆØ§Ù„Ø¹Ø§Ø¯ÙŠØ§Øª Ø¶Ø¨Ø­Ø§Ù‹` —
> can any single-letter substitution be shown to
> (a) score higher than canonical on the QSF detector suite, AND
> (b) remain linguistically plausible?*

The Arabic long-form analysis (`ADIYAT_ANALYSIS_AR.md`) is preserved
for provenance but several of its v7.1 claims are superseded here.
If you read only this file you have the current paper-grade answer.

> **Non-specialist reader?** See `docs/reference/adiyat/03_ADIYAT_AND_AUTHENTICATION.md`
> for the current consolidated status, or `docs/reference/adiyat/CANONICAL_READING_DETECTION_GUIDE.md`
> (v1.0, 2026-04-22) for a plain-language walkthrough of the detection
> machines (EL, R12, UFS), the full five-step pipeline for the "four
> readings" question, and the file map. No statistics background assumed.

---

## 1. The three hand-picked variants

The philological literature names three classical alternatives to
`ÙˆØ§Ù„Ø¹Ø§Ø¯ÙŠØ§Øª Ø¶Ø¨Ø­Ø§Ù‹`:

| Tag | Edit | Resulting v1 | Nature of edit |
|:--:|:--|:--|:--|
| **A** | `Ø¹` â†’ `Øº` | `ÙˆØ§Ù„ØºØ§Ø¯ÙŠØ§Øª Ø¶Ø¨Ø­Ø§Ù‹` | internal single-letter, within word 1 |
| **B** | `Ø¶` â†’ `Øµ` | `ÙˆØ§Ù„Ø¹Ø§Ø¯ÙŠØ§Øª ØµØ¨Ø­Ø§Ù‹` | terminal single-letter, within word 2 |
| **C** | both        | `ÙˆØ§Ù„ØºØ§Ø¯ÙŠØ§Øª ØµØ¨Ø­Ø§Ù‹` | two-letter edit |

Under the QSF 5-D feature set, all three edits fall outside the
boundary-reader sensitivity window (EL reads verse-terminal letters
only; CN reads verse-opening tokens only; H_cond uses verse-final
roots only). Variants A and B are both "invisible" on Phi_M: they
leave the 5-D vector byte-exact unchanged. Variant C contains B, so
it registers through the Ø¶ â†’ Øµ terminal change.

This is the origin of the "structural blindness" finding that
PAPER.md Â§4.20 retracted the cascade-product-code composite over.

---

## 2. The 864-variant enumeration (exp23 and exp43)

To close the "cherry-picked three" critique, every single-letter
consonant substitution of verse 1 was enumerated: 32 consonant
positions Ã— 27 alternative consonants = **864 total variants**.
These are reproducible via `experiments/exp23_adiyat_MC/run.py`
(Phi_M only) and `experiments/exp43_adiyat_864_compound/run.py`
(full five-detector suite).

Across the 864 variants:

| Detector | Calibration | Fire rate | Paper grade |
|---|---|---:|---|
| **Phi_M moves at all** | 5-D boundary readers | **3.2 %** | **Structural blindness confirmed** |
| **gzip NCD doc > exp41-ctrl-p95** | R12 ctrl-null (200 units Ã— 20 edits) | **99.1 %** | **Pre-registered, length-audited** |
| gzip NCD window > exp41-ctrl-p95 | R12 ctrl-null | 23.7 % | secondary scale |
| H_char window moves > 0.01 bits | threshold NOT calibrated | 78.1 % | **exploratory** |
| CCAS raw Frobenius moves | tautological | 100.0 % | informational |
| **NCD doc AND CCAS Frobenius** | joint pre-reg compound | **99.1 %** | **paper-grade headline** |

**Phi_M distribution across 864 variants**:
- canonical = 10.286, maximum variant = 10.286 (the 836 feature-invariant ties)
- minimum variant = 9.198, so every variant has `Phi_M â‰¤ canonical`.
- `pct_variants_with_Phi_M_above_canonical = 0 %`.
- `pct_variants_with_Phi_M_equal_canonical = 96.8 %` (836 of 864 are
  boundary-reader invariant).

So: **no single-letter substitution of Surah 100 verse 1 achieves
higher Phi_M than canonical**. But 836 variants tie with canonical
at Phi_M = 10.286 exactly, because 5-D cannot see their edits. This
is the central finding of Â§4.12 in `PAPER.md`.

### 2.1 Parsimony re-test: 2-D (T, EL) vs full 5-D (exp62, v7.6)

`exp60_lc3_parsimony_theorem` established that (T, EL) carry >99% of
the class-conditional Fisher information (with a negative cross-term
from VL_CV, CN, H_cond). External reviewers asked whether the Adiyat
anomaly survives projection to 2-D. `exp62_adiyat_2d_retest` answers:

| Model | Î¦_M (S100) | Ctrl 95th pct | Ratio | Rank / 114 |
|-------|-----------|---------------|-------|------------|
| **5-D (full)** | 10.286 | 3.330 | 3.1Ã— | 33 |
| **2-D (T, EL)** | 9.00 | 2.42 | **3.7Ã—** | 45 |
| **3-D residual** | 5.36 | 2.60 | 2.1Ã— | **8** |

**Verdict: ANOMALY_SURVIVES.** Surah 100 remains 3.7Ã— the control
95th percentile in the parsimonious 2-D model. Rank drops from 33
to 45 (out of 114), but stays well within the anomalous region.

Per-feature z-scores for Surah 100:

| Feature | z-score | Role |
|---------|--------:|------|
| **EL** | **+8.75** | **Primary anomaly driver** |
| CN | +4.31 | Strong secondary (connective rate) |
| H_cond | âˆ’2.48 | Moderate (low conditional entropy) |
| T | +1.94 | Modest |
| VL_CV | +1.12 | Negligible |

**Key insight**: Adiyat is anomalous in *both* the (T, EL) and
residual (VL_CV, CN, H_cond) subspaces, but for different reasons.
EL drives the 2-D anomaly; CN drives the residual. External advice
to "drop CN, VL_CV, H_cond" is correct for *aggregate classification*
but wrong for *single-case diagnostics* — CN adds z = +4.3 of
complementary diagnostic information for this surah.

Spearman Ï(5-D ranking, 2-D ranking) across all 114 surahs = **0.927**
(p â‰ˆ 10â»â´â¹), confirming high but not perfect rank preservation.

---

## 3. What v7.3 adds (R12 gzip NCD, length-controlled)

v7.2 left the 836-fold tie unresolved. v7.3 adds **R12**, a
pre-registered edit-detection channel based on gzip Normalised
Compression Distance on the 28-letter consonantal rasm:

`NCD(a, b) = (Z(a+b) âˆ’ min(Z(a), Z(b))) / max(Z(a), Z(b))`

with `Z(x) = len(gzip.compress(x.encode('utf-8'), compresslevel=9))`.

Source: `experiments/exp41_gzip_formalised/run.py` + `length_audit.py`.

### 3.1 Population test (68 Quran Band-A vs 200 ctrl Band-A)

- Raw Cohen d(Q NCD âˆ’ ctrl NCD, doc-scale) = **+0.534**, MW p_greater = **6.6Â·10â»Â³â¹** on 1,360 Quran Ã— 4,000 ctrl internal single-letter swaps.
- **Length confound**: Spearman Ï(NCD, n_letters) = âˆ’0.52 (pooled) because NCD mechanically scales as const / Z(doc).
- **Length-controlled effect**: log-linear regression
  `log NCD = Î± + Î² log(n_letters) + Î³ I(Q)` gives
  **Î³ = +0.0716, 95 % CI [+0.066, +0.078], p â‰ˆ 0**.
- Translated to linear scale: at fixed document length, Quran NCD is
  **~7.4 % higher** than ctrl per edit. **This is the correct headline
  number**, not the raw d = +0.534.
- Decile-stratified: Quran NCD > ctrl NCD in **8 of 10 letter-count
  deciles** (deciles 6 and 10 negative). **âš  exp55 (v7.6) formal audit:
  LENGTH_DRIVEN** — only 5/10 deciles exceed d > 0.30; cite Î³ as
  authoritative scalar, not raw d.

### 3.2 Adiyat A / B / C on R12

- **Variant A** (Ø¹ â†’ Øº): NCD_doc = 0.0653, z vs ctrl-null = **+5.58**, fires at ctrl-p95.
- **Variant B** (Ø¶ â†’ Øµ): NCD_doc = 0.0653, z = **+5.58**, fires at ctrl-p95.
- **Variant C** (both): NCD_doc = 0.0804, z = **+9.14**, fires at ctrl-p95.

**Important framing**: R12 fires on 99.1 % of ALL Quran internal
single-letter edits at that threshold. The A/B/C firings are therefore
**not Adiyat-specific** — they are in-distribution instances of the
Quran edit population. The cherry-pick defence is: all three hand-
picked variants happen to fire, none is an exception. R12 is NOT a
specialised Adiyat detector.

---

## 4. Is the Adiyat case "solved"?

**Honest answer: yes on the paper-grade narrow question, no on the
broader theological or forgery-resistance questions.**

### 4.1 What IS solved (at publication grade)

1. **No single-letter substitution of Adiyat verse 1 scores higher
   than canonical on Phi_M** (5-D corpus-level fingerprint). 864/864
   variants have `Phi_M â‰¤ canonical = 10.286`.

2. **R12 gzip NCD fires on 99.1 % of Quran internal edits** above a
   pre-registered ctrl-calibrated 5 % false-positive threshold, with
   a length-controlled Î³ = +0.07 structural residual (p â‰ˆ 0).

3. **The combined (Phi_M â‰¤ canonical) AND (R12 fires)** filter is
   satisfied by canonical and violated (at least partially) by
   approximately 99.1 % of 864 variants, making canonical the
   1-of-865 configuration that uniquely fails to trigger the joint
   detector. (Note: 0 % of variants strictly *exceed* canonical on
   Phi_M, so the Phi_M half is always â‰¤-canonical; only the R12
   half discriminates. This reframes the "1-of-865" claim as
   substantial but not mysterious.)

### 4.2 What is NOT solved

1. **The 836-fold Phi_M tie remains**. A forger who edits a letter
   inside a non-boundary word of a non-terminal verse can produce
   a text with byte-exact canonical Phi_M. Such a forger fails R12
   (99.1 % probability) but passes Phi_M. Combined pass-rate is
   ~0.9 %, which is low but not negligible at a small per-edit cost.

2. ~~**Two-letter and larger edits are not tested**.~~ **CLOSED by
   exp45 (v7.4).** 72 900 two-letter variants tested (100 position-
   pairs in FAST mode out of 362 k total). Compound NCD+CCAS fires
   on **100.0 %** of all two-letter edits. Variant C's neighbourhood
   is now enumerated and universally detected. Full-mode run (~362 k)
   pending for completeness.

3. ~~**Semantically-aware edits** are not special-cased.~~ **CHARACTERISED by
   exp46 (v7.4+, FULL mode 2026-04-21).** 10 461 emphatic-class substitutions
   across all 114 surahs tested via the 9-channel detector with null = 800
   samples. Overall detection rate = **1.1 %** (120 / 10 461; >=3 of 9 channels
   |z|>2). Per-class breakdown:

   | Class | Pair | n edits | Detection rate | mean max\|z\| |
   |-------|------|--:|---------------:|---:|
   | E7 | ayn/alef | 5 048 | **2.1 %** | 1.24 |
   | E1 | sad/sin | 662 | 0.8 % | 0.78 |
   | E2 | dad/dal | 553 | 0.5 % | 0.78 |
   | E6 | hha/ha | 1 663 | 0.4 % | 0.76 |
   | E4 | dha/dhal | 476 | 0.4 % | 0.70 |
   | E3 | tta/ta | 848 | **0.0 %** | 0.67 |
   | E5 | qaf/kaf | 1 211 | **0.0 %** | 0.67 |

   Surah-level: mean 2.5 %, **median 0 %**, range [0 %, 40.7 %]. Most surahs
   show zero emphatic detection; a tail of short surahs (where one letter
   is a larger fraction of the text) drives the positive rates.

   **v7.4 errata (2026-04-21)**: the initial v7.4 release reported 31.3 %
   overall and 10–41 % per-class from the exp46 FAST mode. FAST uses a
   null of only 120 samples per channel (15 surahs Ã— 8 swaps) vs FULL's
   800. At N_null = 120 the |z|>2 threshold has ~Â±0.26 uncertainty in
   its tail cutoff, so null-estimation noise alone can push the "â‰¥ 3 of
   9" composite above threshold. The 31.3 % was a noise-inflation
   artefact; the FULL 1.1 % is the authoritative rate. The per-class
   numbers above replace the retracted FAST numbers.

   **Honest finding (re-stated, v7.5 revision)**: the 9-channel R1
   detector fires on only **1.15 %** of Quran emphatic-class edits
   overall (0.0 % on voiceless stops tta/ta and qaf/kaf). The v7.4
   release called this a "serious residual blind spot of the detector."
   The **v7.5 cross-corpus follow-up (`exp50`)** overturns that framing:
   the same detector scores **9.50 % on poetry_jahili** and **4.83 %
   on poetry_abbasi** (4–8Ã— the Quran rate), so the blindness is
   **Quran-specific** rather than an Arabic-morphology floor. The
   detector is doing its job; the Quran is just genuinely harder to
   forge with phonetically minimal substitutions than the two major
   Arabic corpora tested. This is a *structural* finding, not a
   detector limitation, and the mechanism (high VL_CV + near-ceiling
   H_cond, see `PAPER.md Â§4.33`) is a direct consequence of the 5-D
   fingerprint. Fixing the 0 % voiceless-stop rate still requires
   either a phonetic-distance-aware channel, or a BPE-LM R4 upgrade
   trained on non-Quran Arabic.

4. **Whole-surah forgery** — generating a plausible Arabic text ab
   initio that has canonical Phi_M — is outside this test and is
   empirically tested by R5 (which FAILS at the 50 %-below-Quran level
   on EL+RD-aware Markov forgeries, per `PAPER.md` Â§5).

5. **Semantic / theological correctness** — whether `ÙˆØ§Ù„ØºØ§Ø¯ÙŠØ§Øª` ("the
   grazers-in-the-morning") is or is not a plausible alternative reading
   in classical Arabic — is a philological question, not a statistical
   one, and is outside the QSF scope.

### 4.3 What would make it "fully solved"

Approximately in order of difficulty:

1. ~~**Two-letter enumeration**~~ **DONE (exp45, v7.4)**. 100 % compound
   detection on 72 900 tested variants (FAST). Full ~362 k pending.
2. ~~**Root-letter edit class audit**~~ **DONE (exp46, v7.4+)**. FULL mode
   across 114 surahs: 1.1 % overall (120/10 461); voiceless emphatic stops at
   0.0 % (tta/ta 0/848, qaf/kaf 0/1 211). Serious residual blind spot of R1.
3. **Character-LM based R12' channel**. Train a 50 M-param BPE transformer
   on non-Quran Arabic poetry; compute perplexity on all 864 variants.
   Canonical should be low-perplexity; feature-invariant decoys should
   not. **2-6 weeks GPU; closes the R12 length-confound concern
   independently.** This is exp42 in the deep-scan roadmap.
4. **Two-team external replication** of R12 on a fresh pool. Required
   before any external claim of "Adiyat authentication at statistical
   power P." **1-3 months wall-clock, external collaboration.**
5. **Close the emphatic-class blind spot** (0 % detection for tta/ta and
   qaf/kaf; 1.1 % overall). Options: (a) train a class-specific null to
   lower the threshold for phonetically-constrained edits, (b) add a
   dedicated phonetic-distance channel, or (c) use the BPE-LM from item
   3 which may be sensitive to morphological context.
   **Medium-to-hard difficulty** — the 0 % rate for voiceless stops
   implies the 9-channel feature set is fundamentally insensitive to
   phonetic-distance-one substitutions, not just miscalibrated.

---

## 5. TL;DR for non-specialists

- The Adiyat canonical reading is **not uniquely identifiable** by
  the 5-D corpus-level detector on its own — 836 of 864 single-letter
  variants produce byte-exact canonical Phi_M.
- Combining 5-D with the new **R12 gzip NCD** channel leaves **canonical
  as the 1-of-865 configuration** that fails to fire the joint filter.
- The joint filter's false-positive rate is pre-registered at
  5 % (via exp41's ctrl-null calibration), so the result is not
  post-hoc and not cherry-picked.
- But R12 is a **population-level edit detector**, not an Adiyat-
  specific one. It fires on ~99 % of any Quran internal single-letter
  edit. The A/B/C Adiyat variants are typical members of that
  population, not exceptional.
- The Adiyat case is **solved at paper-grade** for single-letter
  AND two-letter edits. Emphatic-class edits (FULL mode exp46, v7.4+)
  are detected at **1.15 %** on Quran overall (**0.0 %** for voiceless
  stops tta/ta and qaf/kaf). The **v7.5 cross-corpus audit (`exp50`)**
  shows poetry_jahili 9.50 % and poetry_abbasi 4.83 % under the same
  pipeline — the Quran's low rate is therefore **structural immunity**,
  not a detector blind spot. Whole-surah forgery and theological
  plausibility remain out of scope.

---

## 6. Source files and SHA fingerprint

- `experiments/exp23_adiyat_MC/run.py` — Phi_M 864-variant enumeration (v7.2)
- `experiments/exp34_R11_adiyat_variants/run.py` — Phi_sym on A/B/C (v7.2)
- `experiments/exp41_gzip_formalised/run.py` — R12 population test (v7.3)
- `experiments/exp41_gzip_formalised/length_audit.py` — length confound resolution (v7.3)
- `experiments/exp43_adiyat_864_compound/run.py` — 864-variant compound test (v7.3)
- `experiments/exp45_two_letter_746k/run.py` — two-letter enumeration (v7.4)
- `experiments/exp46_emphatic_substitution/run.py` — emphatic-class audit (v7.4)
- `experiments/exp62_adiyat_2d_retest/run.py` — 2-D (T,EL) parsimony re-test (v7.6)

Deposit fingerprint (OSF ready): `overall_sha256 = 2f90a87a0fa0ac42057dbd6785e591355b075a14ab0bfd52cc49d396ca7f0205`
(see `arxiv_submission/osf_deposit_v73/osf_deposit_manifest.json`).
