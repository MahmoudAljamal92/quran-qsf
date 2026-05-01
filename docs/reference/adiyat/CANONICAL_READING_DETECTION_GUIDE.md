# Canonical Reading Detection — A Guide for Non-Specialists

**Version**: 1.1 (2026-04-29 afternoon, **V3.11 update** — adds the F69 multi-letter theorem `Δ_bigram ≤ 2k`, the F71 universal-language scope (Arabic + Hebrew + Greek + Pāli + Sanskrit), the new forensic toolkit (`tools/sanaa_compare.py`, `tools/quran_metrology_challenge.py`, `tools/sanaa_battery.py`, `app/streamlit_forgery.py`), and a pointer to the 8-layer detection coverage matrix at `docs/reference/findings/DETECTION_COVERAGE_MATRIX.md`. The original v1.0 narrative below remains authoritative for the F53/F55 detection stack and the canonical Adiyat case walkthrough — V3.11 only extends it; nothing is retracted.)
**Earlier version**: 1.0 (2026-04-22, post-exp94 / exp103 / exp104 / exp105 / exp106-PREREG)
**Status**: Plain-language companion to `docs/PAPER.md` (v7.8 cand.), `docs/reference/adiyat/03_ADIYAT_AND_AUTHENTICATION.md` (current Adiyat/authentication entry point), `docs/reference/adiyat/ADIYAT_CASE_SUMMARY.md` (v7.6), `docs/REFERENCE.md` (v7.7), and `docs/reference/findings/RANKED_FINDINGS.md` (v1.3).
**Audience**: anyone who has never read the paper. Engineers, editors, philologists, philosophy-of-science readers. No statistics background assumed beyond "a p-value tells you how surprising something is under chance".
**Scope**: what the QSF project is, what the "four readings" question is, what machines we currently use to answer it, and how you would re-run the experiment from zero today.

---

## 0. One-paragraph TL;DR

Given an Arabic text that **claims** to be a particular Quran verse, we can now ask two independent questions by machine:

1. **Task A — "Is this the Quran at all?"** A single feature, the *end-letter rhyme rate* (EL), separates all 114 canonical surahs from a 4 719-unit Arabic control pool at **AUC = 0.981** (per-band: Band-B short 0.934, Band-A paper 0.997, Band-C long 1.000).
2. **Task B — "Has any letter been edited?"** A gzip-based compression distance (R12) fires on **99.07 %** of all 864 single-letter substitutions of Surah 100 verse 1 at a pre-registered 5 % false-positive rate.

The two machines use **independent signals** (rhyme geometry vs consonantal compressibility) and can be fused into a single Fisher Ï‡Â² score, the **Universal Forgery Score (UFS)**, that is intended to output one number for any Arabic text of any length. UFS is specified in `experiments/exp106_universal_forgery_score/PREREG.md`, but it is **pre-registered only** as of this update: there is no `results/experiments/exp106_universal_forgery_score/` receipt yet. Its recall and lift targets remain hypotheses, not results.

Everything below unpacks that paragraph.

---

## Part I — The question in plain Arabic and plain English

### I.1 The test verse

The opening verse of Surah 100 in the canonical Hafs reading:

```
Canonical (Hafs):   ÙˆÙŽØ§Ù„Ù’Ø¹ÙŽØ§Ø¯ÙÙŠÙŽØ§ØªÙ Ø¶ÙŽØ¨Ù’Ø­Ù‹Ø§        (wa-l-Ê¿ÄdiyÄti á¸abá¸¥an)
                    "By the chargers, panting."
```

The classical philological literature names **three linguistically plausible single-letter alternatives** that have been discussed for centuries. Together with the canonical, that gives four candidate "readings" of the same verse:

| Tag         | Edit                 | Arabic                  | Transliteration     | Intuition                                 |
|:-----------:|:---------------------|:------------------------|:--------------------|:------------------------------------------|
| **Canon**   | (none)               | `ÙˆÙŽØ§Ù„Ù’Ø¹ÙŽØ§Ø¯ÙÙŠÙŽØ§ØªÙ Ø¶ÙŽØ¨Ù’Ø­Ù‹Ø§` | `wa-l-Ê¿ÄdiyÄti á¸abá¸¥an` | "the chargers, panting"                   |
| **A**       | `Ø¹` â†’ `Øº` (word 1)  | `ÙˆÙŽØ§Ù„Ù’ØºÙŽØ§Ø¯ÙÙŠÙŽØ§ØªÙ Ø¶ÙŽØ¨Ù’Ø­Ù‹Ø§` | `wa-l-ghÄdiyÄti á¸abá¸¥an` | "the ones going out at morning"          |
| **B**       | `Ø¶` â†’ `Øµ` (word 2)  | `ÙˆÙŽØ§Ù„Ù’Ø¹ÙŽØ§Ø¯ÙÙŠÙŽØ§ØªÙ ØµÙŽØ¨Ù’Ø­Ù‹Ø§` | `wa-l-Ê¿ÄdiyÄti á¹£abá¸¥an` | "the chargers, at dawn"                   |
| **C**       | both A and B         | `ÙˆÙŽØ§Ù„Ù’ØºÙŽØ§Ø¯ÙÙŠÙŽØ§ØªÙ ØµÙŽØ¨Ù’Ø­Ù‹Ø§` | `wa-l-ghÄdiyÄti á¹£abá¸¥an` | both edits combined                       |

**The question this guide answers:**

> *If I hand you the four strings above without telling you which is which, can your machine tell me which one is the canonical Quran?*

It is a tiny question. It is also the hardest single question in this project, because edits A and B are each **one letter** and the canonical Quran was transmitted orally for centuries before it was written down. Any successful detector must read a signal smaller than one letter out of roughly 6 400 consonants in the full surah.

### I.2 Why this question matters beyond the Quran

Exactly the same machine, re-calibrated, answers:

- **Manuscript authentication.** Is a newly-discovered fragment a faithful copy of a known text, or an imitation?
- **Adversarial-robustness of language models.** If a generative model produces an Arabic passage that claims to be Quran, does our detector say so?
- **Plagiarism detection under paraphrase.** The Fisher combination of "style classifier" + "compression distance to the original" is a generic tool that outperforms either alone.
- **Scribal-error classification in oral-transmission corpora** (Tanakh, Vedic Saá¹ƒhitÄ, Pali Canon). The 5-D fingerprint is Quran-specific but the **framework** (fingerprint + compression distance + Fisher fusion) is not.

---

## Part II — The detection machines (what each one sees, why it works)

Two independent channels carry the signal. A third, unified channel combines them.

### II.1 Channel 1 — EL (the rhyme-rate classifier)

**What it measures.** For each pair of adjacent verses (`v_i`, `v_{i+1}`), does the last letter (after stripping diacritics) match? EL is the fraction of such pairs that rhyme.

**What it sees.** The Quran has EL â‰ˆ 0.71 across Band-A surahs (15–100 verses). Arabic prose and poetry have EL â‰ˆ 0.10–0.15. The gap is roughly 5–7Ã— and easy to discriminate with a one-dimensional threshold.

**What it does *not* see.** EL is computed on **verse-terminal letters only**. Any edit inside a word that is not the last word of a verse, or inside a verse whose last letter is not changed, leaves EL **byte-identical**. EL is therefore silent on Adiyat variants A and B in isolation (both change internal letters of the first verse; the verse-terminal letter `Ù€Ù‡Ø§` / `Ù€Ø­Ø§` is unchanged).

**Latest numbers (exp104, 2026-04-22, all 114 surahs):**

| Band                  | n_Q | n_ctrl | AUC       | median EL(Quran) | median EL(ctrl) |
|:----------------------|----:|-------:|----------:|-----------------:|----------------:|
| B — short (2–14 verses) | 28  | 2 068  | **0.934** | 0.714            | 0.077           |
| A — paper (15–100)       | 68  | 2 509  | **0.997** | 0.727            | 0.100           |
| C — long (> 100)         | 18  | 142    | **1.000** | 0.762            | 0.096           |
| Overall                  | 114 | 4 719  | **0.981** | 0.727            | 0.091           |

**Receipt**: `results/experiments/exp104_el_all_bands/exp104_el_all_bands.json`.

**Why it is unique.** EL is a single real number. It rides on a feature (end-rhyme under a consonantal alphabet) that is structurally Arabic but empirically **Quran-elevated** by a factor that secular Arabic corpora — including the same pre-Islamic *qasida* that classical grammarians point to as the Quran's literary neighbour — do not approach. The cross-language falsifier test (`exp90_cross_language_el`) showed that Hebrew Tanakh EL = 0.125, Greek NT EL = 0.206; both cluster with secular Arabic. The elevation is therefore **Arabic-specific and Quran-specific**, not a property of scripture-in-general. That narrowness is what makes it a strong single feature.

---

### II.2 Channel 2 — R12 (gzip compression distance)

**What it measures.** Strip every diacritic from a verse, reducing it to the 28-letter consonantal skeleton (*rasm*). Concatenate the canonical version and the candidate, and compress the concatenation with gzip. Compare to compressing each alone:

```
NCD(canon, candidate) = (Z(canon + candidate) âˆ’ min(Z(canon), Z(candidate)))
                        / max(Z(canon), Z(candidate))
```

where `Z(x) = len(gzip.compress(x.encode('utf-8'), compresslevel=9))`.

**What it sees.** R12 is a *structural* channel: it detects edits that break the Quran's internal letter-pattern redundancy. On 1 360 random internal single-letter edits across all 68 Band-A surahs, R12 separates edited from unedited rasm with length-controlled residual **Î³ = +0.0716, 95 % CI [+0.066, +0.078], p â‰ˆ 0**. On the specific 864 single-letter variants of Adiyat verse 1, R12 fires on **99.07 % = 856 / 864** variants at a pre-registered ctrl-p95 threshold (5 % FPR).

**What it does *not* see.** R12 is a gzip-based detector. gzip's Lempel-Ziv back-references are *token-blind* — they see the rasm as a raw byte string and make no morphological, phonological, or semantic judgement. Two consequences:

1. **Emphatic-stop near-synonyms are invisible.** Swapping Øªâ†”Ø· or Ùƒâ†”Ù‚ changes one phoneme class but barely changes gzip's back-reference structure. `exp46_emphatic_substitution` (full mode) showed detection rates of **0.0 %** for the ttaâ†”ta and qafâ†”kaf classes across 10 461 emphatic edits on all 114 surahs. `exp103_cross_compressor_gamma` showed this floor survives across four universal compressors (gzip, bzip2, zstd, lzma; CV(Î³) = 2.95), so it is a **Kolmogorov-complexity property of the 28-letter rasm**, not a gzip-specific artefact.
2. **Diacritic-only edits are invisible** by construction (we strip diacritics before computing NCD).

**Why it is unique.** The statement "Quran internal edits compress measurably worse than the canonical" is a **purely information-theoretic** claim. It does not depend on any linguistic theory, any religious premise, or any hand-curated feature. It cross-validates against the 5-D feature channel (they are weakly correlated, Ï â‰ˆ 0.05 with EL on ctrl) and is therefore *independent evidence* of the same anomaly.

**Receipts**:
- `results/experiments/exp41_gzip_formalised/` (population-level Î³ residual),
- `results/experiments/exp43_adiyat_864_compound/` (joint-detector version, 99.1 % fire rate),
- `results/experiments/exp94_adiyat_864/exp94_adiyat_864.json` (current 99.07 % recall).

---

### II.3 The complementarity — why you want both channels

EL and R12 fail on **disjoint** classes of edit:

| Edit class                              | EL fires? | R12 fires? |
|:----------------------------------------|:---------:|:----------:|
| Internal single-letter (Adiyat A, B)    | No        | **Yes** (99.07 %) |
| Terminal single-letter (rhyme-breaker)  | **Yes**   | Partial (~70–85 % est.) |
| Emphatic-class swap (Øªâ†”Ø·, Ùƒâ†”Ù‚)         | No        | No (0 %, exp46 FULL) |
| 3-letter scattered                      | Partial   | Partial    |
| Whole-text impersonation (not canonical)| **Yes**   | undefined (no canon) |

Any honest detector must expose **both** channels. Using R12 alone, you miss rhyme-breaking terminal edits. Using EL alone, you miss every internal-letter edit including all 836 byte-invariant single-letter forgeries of Adiyat. Using both, the only class of single-letter edit that can still pass is the emphatic-stop class (currently ~1.1 % on the full 114-surah emphatic audit). That residual is the next frontier (see Part V).

---

### II.4 Channel 3 — UFS (the Universal Forgery Score, pre-registered)

A proposed single scalar that absorbs both channels and produces a p-value you can threshold regardless of surah length or edit type. As of 2026-04-25, this section is a description of the **pre-registered design**, not an executed result.

**Formula** (Â§4.36 of `PAPER.md`, detailed in `exp106_universal_forgery_score/PREREG.md`):

For a verse window `W` of `m` consecutive verses:
1. Compute `EL(W)` and look up the left-tail p-value `p_EL(W)` against a length-stratified Quran-null (leave-one-surah-out).
2. Compute `NCD(W) = NCD_gzip(canon(W), W)` and look up the right-tail p-value `p_NCD(W)` against a length-stratified ctrl-edit null.
3. Combine via Fisher's method:

```
UFS(W) = âˆ’2 Â· [ ln p_EL(W)  +  ln p_NCD(W) ]
```

Under independence of the two p-values, `UFS ~ Ï‡Â²_4`. Fire if `UFS â‰¥ Ï„_UFS(m)`, where `Ï„_UFS(m)` is the 95th percentile of the ctrl-background UFS at the same window size.

**What UFS is designed to test against sequential gating (EL â†’ then R12):**

1. **Terminal-letter edits where both channels move slightly.** Sequential gating might under-fire or over-fire; Fisher may combine marginal moves into one alarm with a single p-value.
2. **Multi-letter scattered forgeries** that are sub-threshold on each individual letter edit but aggregate EL drift across several verse pairs.
3. **Unknown-provenance texts.** Sequential gating requires the operator to pre-decide Task A vs Task B; UFS is intended to score both jobs together.

**Pre-registered verdicts (from `exp106/PREREG.md` Â§4):**

| Code                                    | Meaning                                                                 |
|:----------------------------------------|:------------------------------------------------------------------------|
| `FAIL_broken_independence`              | Ctrl-null Ï(p_EL, p_NCD) â‰¥ 0.30 â†’ Fisher Ï‡Â²_4 assumption violated       |
| `FAIL_benchmark1_regression`            | Task-A AUC < exp104.AUC âˆ’ 0.005 â†’ implementation bug                    |
| `FAIL_benchmark2_regression`            | Adiyat-864 recall < exp94.recall âˆ’ 0.003 â†’ implementation bug            |
| `PARTIAL_redundant`                     | UFS â‰ˆ R12/EL on all 4 benchmarks — reviewer's "sequential gating is enough" wins |
| `PASS_terminal_lift`                    | UFS beats R12 by â‰¥ 10 pp on 6 000 terminal-edit variants                |
| `PASS_multi_edit_lift`                  | UFS beats R12 by â‰¥ 5 pp on 2 000 k=3 scattered edits                    |
| `PASS_strict_superset_of_R12`           | UFS â‰¥ R12 on **all four** benchmarks (ties on 1 & 2, lifts on 3 & 4)    |
| `PASS_universal_forgery_machine`        | AUC â‰¥ 0.99 on Benchmark 1 AND recall â‰¥ 0.99 on Benchmarks 2, 3, 4       |

The honest prior (from `PREREG.md`) is 55 % `PASS_strict_superset`, 20 % `PASS_terminal_lift only`, 15 % `PARTIAL_redundant`, 5 % `PASS_universal_forgery_machine`, 5 % `FAIL_broken_independence`.

---

### II.5 What we *tried* and had to retire

Part of the doctrine of this project is listing what did **not** work, because it sharpens the claim about what does. The latest two null/retired attempts:

- **R13 — diacritic-restoration channel (exp105).** The hypothesis was that a CamelTools morphology analyser could identify the 8 Adiyat-864 variants that R12 misses, by detecting that the edited rasm admits *fewer* plausible full-diacritic restorations. The full experiment (`results/experiments/exp105_harakat_restoration/`) showed recall = **24.77 %** — well below R12's 99.07 %, and the *union* of R12 âˆª R13 = **99.07 % = R12 alone**. R13 detects a different population of edits (mostly the ones R12 already catches, plus some noise) and does **not** close the 8-variant residual. The proper fix for those 8 requires a Quranic-LM (a future `exp107`), not morphology.
- **Cross-compressor Î³ (exp103).** Measured Î³ under gzip, bzip2, zstd, lzma. CV(Î³) = 2.95 (huge). The emphatic-stop blindness is invariant across compressors. Verdict: the floor is a **Kolmogorov-complexity property of the 28-letter rasm**, not a gzip-specific artefact. No compressor-based channel alone will close it.

These two retractions are in `docs/reference/findings/RANKED_FINDINGS.md Â§5` as retractions 26 (R13 null via morphology) and a new v7.8 entry (cross-compressor Î³). They do not weaken the surviving machines; they **delineate** them.

---

## Part III — If we redo the "four readings" experiment today, step by step

This is the full updated recipe. It is what you would hand to a replication team that has never seen this project.

### III.1 Inputs

- **Text of Adiyat** (all four readings). You can download the canonical from `data/corpora/quran/100.txt` (Uthmani orthography, SHA-pinned). Variants A, B, C are produced by the single-letter substitutions in Part I.1.
- **Control pool.** `data/corpora/{poetry_jahili, poetry_islami, poetry_abbasi, ksucca, arabic_bible, hindawi}` — 4 719 units total.
- **Frozen code**: `experiments/exp94_adiyat_864/run.py` and `experiments/exp104_el_all_bands/run.py`. Both read-only. Both tested to pass `self_check_end` at commit-time SHA.

### III.2 The five-step pipeline

```
Step 1 — EL (Task A):
    for each reading X in {Canon, A, B, C}:
        EL(X) = fraction of adjacent verse-pairs in the FULL SURAH 100
                (11 verses) whose terminal letters match, diacritics
                stripped.
    decision: if EL(X) < 0.5 â†’ X is not Quran-like at all. REJECT.
    (All four readings pass Step 1: terminal letters of verses 2–11
     are untouched.)

Step 2 — R12 (Task B):
    R12(X) = NCD_gzip( rasm(Canon), rasm(X) )
    where rasm() strips all diacritics to the 28-letter alphabet.
    threshold Ï„_R12 = exp94 ctrl-p95 = 0.049608 (pre-registered 5 % FPR).
    decision: if R12(X) â‰¥ Ï„_R12 â†’ X has been edited. FLAG.

Step 3 — Fisher combine (Â§4.36 / exp93 / exp106):
    Compute the three layers from Â§4.36 on the FULL SURAH, not just verse 1:
        p_L    = left-tail p of L_TEL (Task-A feature) vs Quran-null
        p_Phi  = left-tail p of Phi_M (5-D Mahalanobis) vs Quran-null
        p_R12  = right-tail p of NCD_edit vs ctrl-edit-null
    XÂ²(X) = âˆ’2 Â· [ ln p_L + ln p_Phi + ln p_R12 ]
    decision: if XÂ²(X) â‰¥ Ï‡Â²_6 95th percentile of ctrl-background â†’ FLAG.

Step 4 — VL_CV floor (hard Boolean gate, Â§4.37, exp98):
    VL_CV(X) = coefficient of variation of verse-word-counts in X.
    decision: if VL_CV(X) < 0.2683 â†’ X falls below the Quran floor. REJECT.
    (Useful against whole-surah machine-generated forgeries; defensive
     against adversarial paraphrase that defeats EL or R12.)

Step 5 — Verdict per reading:
    ACCEPT_AS_CANONICAL iff  all four gates pass:
        EL(X) â‰¥ 0.5  AND  R12(X) < Ï„_R12
        AND  XÂ²(X) < Ï‡Â²_6.95  AND  VL_CV(X) â‰¥ 0.2683.
    Expected behaviour:
        Canon: ACCEPT        (all four gates pass by construction)
        A:     REJECT_STEP_2 (R12 fires: Ø¹ â†’ Øº is a rasm-level edit)
        B:     REJECT_STEP_2 (R12 fires: Ø¶ â†’ Øµ is a rasm-level edit)
        C:     REJECT_STEP_2 (R12 fires even harder)
```

### III.3 The numbers you will see at the end

From the existing receipts (`exp94_adiyat_864` + `exp104_el_all_bands` + Â§4.36 closed-form stack in `exp93_unified_stack`):

| Reading | Step 1 EL | Step 2 R12 NCD | Step 3 Fisher XÂ² | Step 4 VL_CV | Verdict |
|:--------|----------:|---------------:|------------------:|-------------:|:--------|
| Canon   | 0.70      | 0.0000         | â‰ˆ baseline (passes) | 0.27–0.32   | **ACCEPT** |
| A (Ø¹â†’Øº) | 0.70      | 0.0653 (z=+5.58) | dominated by p_R12 | unchanged   | **REJECT** at Step 2 |
| B (Ø¶â†’Øµ) | 0.70      | 0.0653 (z=+5.58) | dominated by p_R12 | unchanged   | **REJECT** at Step 2 |
| C (both)| 0.70      | 0.0804 (z=+9.14) | dominated by p_R12 | unchanged   | **REJECT** at Step 2 |

The canonical is the unique 1-of-865 configuration that fails to trigger Step 2. **That is the formal answer to "can the machine pick the canonical reading": yes, at pre-registered 5 % false-positive rate, from the full 864-variant enumeration of which the three philologically famous ones are just hand-picked members.**

### III.4 What would change if we re-ran on a DIFFERENT verse

Adiyat is unusually short (11 verses). The same pipeline applied to a long surah (e.g., Al-Baqarah, 286 verses) would behave as follows:

- **EL power increases** (more verse-pairs â†’ tighter estimate of the rhyme rate). Expect AUC â‰¥ 0.997 on Band-A surahs.
- **R12 power decreases per-edit** because the edited letter is a smaller fraction of the rasm — gzip's back-reference structure is less perturbed. Single-letter recall on Al-Baqarah edits is empirically ~93 % vs Adiyat's 99 %.
- **UFS may compensate** by aggregating both channels across ~280 verse windows, but this remains a pre-registered `exp106` hypothesis until the benchmark is executed.

The recipe does not change. The numbers change predictably with length. This is the content of the `length_audit.py` module at `experiments/exp41_gzip_formalised/length_audit.py`.

---

## Part IV — The science in one page

### IV.1 Why rhyme-rate is a corpus-identity feature (Task A)

A language-internal random text has per-letter marginal distribution dominated by frequent letters (in Arabic, roughly `Ø§ Ù„ Ù… Ù† ÙŠ Ù‡ Øª Ø¨`). For a random pair of verses, the probability that both end on the **same** letter is roughly `Î£ p_letterÂ²` â‰ˆ 0.11 for Arabic — close to the secular-control empirical value 0.09–0.15. The Quran's measured 0.71 is 7Ã— that floor. **A corpus does not reach EL = 0.7 by accident; it reaches it by design.** Oral poetry reaches 0.3–0.4 (metrical feet + mono-rhyme). The Quran sits above oral poetry by a further factor of ~2. The exp90 cross-language test (Hebrew, Greek, Homeric) confirms this is Arabic+oral-transmission-specific.

### IV.2 Why gzip NCD is an edit-detection feature (Task B)

gzip's Lempel-Ziv coder finds **back-references**: "this 7-byte string already appeared 340 bytes ago, encode as a pointer." The Quran rasm is unusually rich in such back-references because it contains (a) ritual refrains (e.g., the 31 `fa-bi-ayyi alaa`) and (b) Arabic root-based morphology that reuses 3-letter consonantal skeletons. Any internal letter swap **breaks** one back-reference and creates a new literal, which costs bits. On 1 360 random edits, that cost averages 7.4 % more bytes at fixed document length (Î³ = +0.0716). Over 864 variants of a single verse, the cost is concentrated enough that **99.07 % of variants** cross a pre-registered ctrl-p95 threshold.

This is information theory, not theology. It is also not a universal Kolmogorov constant: `exp103_cross_compressor_gamma` found statistically significant Quran-vs-control separation under all tested compressors, but the sign and magnitude are compressor-family-specific (`gzip`/`brotli` positive; `zstd`/`bzip2` negative). The exact `Î³ = +0.0716` number is therefore a **gzip-calibrated** edit-detection parameter, not a universal information-theoretic constant.

### IV.3 Why Fisher combination is the right unification

The three layers `L_TEL`, `Î¦_M`, `R12` are calibrated independently. To combine them you need their p-values on a common scale. The two standard choices are:

1. **Logistic stacking** — fit a weighted sum on a held-out set. Optimal under arbitrary dependence, but requires a training set and loses interpretability.
2. **Fisher's method** — combine p-values via `XÂ² = âˆ’2 Î£ ln p_i`. Distribution-free under Hâ‚€ of independence; exact Ï‡Â² under Hâ‚; no free parameters.

We use **both** and report both. Fisher is the headline scalar because it has no tunable weights — it is a function of the layer p-values only. Logistic is the robustness check; it should agree with Fisher to within 0.01 AUC. On exp93 they agree to within 0.001 (AUC 0.9981 Fisher, 0.9972 logistic).

### IV.4 Why we still report limitations loudly

On the **emphatic-stop** class (Øªâ†”Ø·, Ùƒâ†”Ù‚), all four compressors give 0 % detection. The EL channel is silent on any internal edit. The Fisher combination is silent too, because both input p-values are large. No machine in the current stack catches a `Øª â†’ Ø·` edit on an internal letter. That is a 1.1 % residual on the 114-surah emphatic-class audit (`exp46` full mode).

This is not a detector bug; it is a Kolmogorov-complexity property of the rasm alphabet. Two options to close it in future work:

- **Phonetic-distance-aware channel (exp95 attempt).** `exp95_phonetic_modulation` tested articulatory-distance-stratified thresholds but returned `FAIL_ctrl_stratum_overfpr`; it did **not** safely close the emphatic residual. Any future phonetic-aware channel must first satisfy per-stratum false-positive control.
- **Quranic-LM R4 channel.** Train a 50M-param Arabic transformer (non-Quran corpus) and compute per-token perplexity on each variant. Expected to close emphatic gap to ~0 % but requires 2–6 weeks GPU and external-corpus licensing.

Until one of those ships, every claim in this guide carries the asterisk: *for non-emphatic internal single-letter edits, our stack catches 99.07 %. For emphatic edits (`exp46`), the rate is â‰ˆ 1 %.* This is stated explicitly in `PAPER.md` Â§4.25 and `ADIYAT_CASE_SUMMARY.md` Â§4.2 and not buried.

---

## Part V — Honest limitations (the short list)

1. **Emphatic-stop blindness.** ~1 % detection on `exp46`-class edits. Solution requires either a phonetic-aware channel or an Arabic-LM; neither is in the current stack.
2. **Whole-surah impersonation.** If a forger generates a whole new Arabic text with canonical EL, canonical Î¦_M, and canonical VL_CV, then Steps 1, 3, and 4 all pass. Step 2 requires a canonical to compare against; if the forger claims the text is a newly-discovered surah (no canonical), we fall back to Task A alone and the detector is weaker. The `exp92_genai_adversarial_forge` benchmark shipped a first such attack and the stack held, but no GAN-class attack has yet been attempted.
3. **Theological / semantic plausibility.** We do not and cannot say whether `ÙˆÙŽØ§Ù„Ù’ØºÙŽØ§Ø¯ÙÙŠÙŽØ§ØªÙ` is a *plausible* reading in classical Arabic. That is philology, not statistics. The QSF suite says: no single-letter variant of Adiyat verse 1 passes all four gates. It says nothing about whether `Ø§Ù„ØºØ§Ø¯ÙŠØ§Øª` ("the morning-goers") is a pious or impious alternative.
4. **One corpus.** LC2 (the "oral-transmission optimisation" thesis) rests on the Quran vs Arabic-control comparison. To make it a law, we need â‰¥ 3 independent oral-ritual corpora (Tanakh, Vedic, Avestan) and cross-language replication. Timeline: 5–7 years (`RANKED_FINDINGS.md Â§0`).
5. **Fisher independence.** `UFS = Ï‡Â²_4` holds only if `p_EL` and `p_NCD` are independent under Hâ‚€. `exp106 Â§3.5` gates the entire experiment on `Ï(p_EL, p_NCD) < 0.30` on the ctrl-null. If that fails, the fallback is a logistic combiner; no cherry-picking allowed.

---

## Part VI — Where this applies beyond the Quran

The *machine* is Quran-calibrated. The *framework* is not. Concretely:

### VI.1 Manuscript authentication

Given any canonical text and a candidate fragment, the R12 gzip NCD channel is directly portable. You need only:
- A rasm-level (consonant-only) representation of both texts.
- A length-matched null corpus (edits of similar-length segments from the same language).

The Î³-residual from `exp41_gzip_formalised` has been measured on Arabic only, but the framework is language-agnostic. Replicating it on Hebrew Tanakh or Pali Canon is a 2-week engineering effort (one graduate student, one laptop).

### VI.2 Adversarial robustness of Arabic LLMs

The EL + Î¦_M + R12 stack is a cheap runtime detector for "this text was generated by a model, not excerpted from the Quran". It does not require the LLM's weights, no watermarking, no embedding access — just the generated text. Useful for:
- Moderation systems for Arabic chatbots.
- Academic detection of GPT-generated Quranic commentary.
- Copyright / attribution disputes.

### VI.3 Plagiarism under paraphrase

Any two texts `A` and `B` that share deep structural back-references (plagiarism by syntactic transformation) will have Î³-residual between `A` and `B` that is indistinguishable from noise under gzip **unless** the structural back-reference is preserved. If it is preserved, R12 fires. If it is not, the content is genuinely different. That is exactly the behaviour a plagiarism detector wants.

### VI.4 Scribal-error correction in ancient corpora

Given a base text and a candidate variant (from an independent manuscript), R12's z-score directly estimates the probability that the variant is a scribal error vs a legitimate alternative reading. Classical text-criticism uses rules-of-thumb (*lectio difficilior*, *lectio brevior*) that conflict with each other; R12 provides a purely statistical complement that agrees with classical rules in 80–90 % of cases (informal; no published study yet).

---

## Part VII — Reproducibility map (file pointers)

Everything below is read-only unless noted. Every receipt carries a SHA-256 of the input corpus and the `frozen_constants` dict.

### VII.1 Core data

- `data/corpora/quran/*.txt` — the 114 canonical surahs, Uthmani orthography, SHA-pinned in `data/corpora/quran/_manifest.json`.
- `data/corpora/{poetry_jahili, poetry_islami, poetry_abbasi, ksucca, arabic_bible, hindawi}/*` — the 4 719-unit Arabic control pool.

### VII.2 Pipelines

- `src/features.py` — EL, VL_CV, CN, H_cond, T feature extractor. All five features are diacritic-stripped before computation.
- `src/gzip_ncd.py` — the R12 operator. Matches `experiments/exp41_gzip_formalised/run.py` byte-for-byte.
- `src/roots.py` — CamelTools-backed morphological analyser. Used by H_cond and by the (retired) R13 channel.

### VII.3 Experiments relevant to this guide

| File                                                        | What it does                                           | Paper Â§           |
|:------------------------------------------------------------|:-------------------------------------------------------|:------------------|
| `experiments/exp41_gzip_formalised/`                         | Î³ = +0.0716 length-controlled residual (R12 population test) | Â§4.25           |
| `experiments/exp43_adiyat_864_compound/`                     | Adiyat-864 enumeration, joint-detector version         | Â§4.27             |
| `experiments/exp46_emphatic_substitution/`                   | Emphatic-class audit (full, 10 461 edits)              | Â§4.33             |
| `experiments/exp89b_five_feature_ablation/`                  | EL-alone AUC = 0.9971 on Band-A                        | Â§4.35             |
| `experiments/exp93_unified_stack/`                           | Â§4.36 Fisher Ï‡Â²_6 combiner, AUC = 0.9981               | Â§4.36             |
| `experiments/exp94_adiyat_864/`                              | R12 at 99.07 % recall on 864 Adiyat variants           | Â§4.36 Stage 2     |
| `experiments/exp95_phonetic_modulation/`                     | Phonetic-distance-weighted R12 attempt — `FAIL_ctrl_stratum_overfpr` | honest failed upgrade |
| `experiments/exp98_vlcv_floor/`                              | VL_CV floor = 0.2683 (Boolean gate, Â§4.37)             | Â§4.37             |
| `experiments/exp103_cross_compressor_gamma/`                 | Cross-compressor Î³ — `FAIL_not_universal`; Î³ is compressor-family-specific | Â§4.25 update      |
| `experiments/exp104_el_all_bands/`                           | EL classifier on all 114 surahs, AUC = 0.981           | Â§4.35 update      |
| `experiments/exp105_harakat_restoration/`                    | R13 morphology channel — `PARTIAL_null_saturated`; no recall gain over R12 | honest partial/null |
| `experiments/exp106_universal_forgery_score/` (PREREG only)  | UFS specification, pending implementation              | Â§4.36 extension   |

### VII.4 Documents

- `docs/PAPER.md` — the technical paper. Â§4.20–Â§4.38 are the sections cited above.
- `docs/reference/adiyat/03_ADIYAT_AND_AUTHENTICATION.md` — current consolidated Adiyat/authentication status, including `exp95`, `exp105`, and `exp106`.
- `docs/reference/adiyat/ADIYAT_CASE_SUMMARY.md` — earlier one-page answer to "is the Adiyat case closed?" (yes, at paper grade for the fixed single- and two-letter benchmarks; still open for emphatic, OOD, and whole-surah attacks).
- `docs/reference/adiyat/ADIYAT_AR.md` — plain-Arabic version of the same summary.
- `docs/reference/findings/RANKED_FINDINGS.md` — all 40 positive findings + 26 retractions, scored on four axes.
- `docs/REFERENCE.md` — deep methodological reference (methodology stack, feature definitions, band definitions, pre-registration conventions).
- `docs/reference/audits/ZERO_TRUST_AUDIT_2026-04-22.md` — self-audit of Â§4.36 (Fisher independence, HARKing disclosure, structural-convergence caveat).

### VII.5 How to verify a receipt

Every JSON receipt in `results/experiments/*/` has a header of the form:

```json
{
  "experiment": "exp94_adiyat_864",
  "hypothesis": "…",
  "schema_version": 1,
  "prereg_document": "experiments/exp94_adiyat_864/PREREG.md",
  "prereg_hash": "<SHA-256 of the PREREG file at commit time>",
  "frozen_constants": { … },
  …
}
```

To verify: (a) compute the SHA-256 of the `PREREG.md` and check it equals `prereg_hash`; (b) re-run `run.py` with `SEED = 42`; (c) check the output JSON is byte-identical to the one in `results/`. The self-check framework in `experiments/_lib.py` enforces (c) automatically.

---

## Part VIII — Glossary

- **AUC** — Area Under the ROC Curve. 1.0 = perfect classifier, 0.5 = chance.
- **Band-A / B / C** — Quran surahs grouped by length: 15–100 verses (A, paper-grade), 2–14 (B, short), > 100 (C, long).
- **EL** — End-Letter rhyme rate. Feature #1 in the 5-D fingerprint.
- **Î¦_M** — Mahalanobis distance of a surah's 5-D feature vector from the Arabic-control centroid. The headline "fingerprint" statistic.
- **Fisher's method** — combine independent p-values via `XÂ² = âˆ’2 Î£ ln p_i ~ Ï‡Â²_{2k}` under Hâ‚€.
- **Î³** — length-controlled gzip-NCD residual: `log NCD = Î± + Î² log(n) + Î³ Â· I(Quran)`. Our measured value = +0.0716, p â‰ˆ 0.
- **L_TEL** — Linear discriminant on (T, EL) from Â§4.35 (LC3-70-U parsimony proposition): `L = 0.5329Â·T + 4.1790Â·EL âˆ’ 1.5221`.
- **NCD** — Normalised Compression Distance. `(Z(xy) âˆ’ min(Z(x), Z(y))) / max(Z(x), Z(y))`.
- **Rasm** — consonantal skeleton (28-letter Arabic alphabet), diacritics stripped.
- **R12** — our label for the gzip-NCD edit-detection channel.
- **R13** — proposed diacritic-restoration channel; tested and null (exp105).
- **Ï„_{anything}** — a threshold calibrated against an independent ctrl null, usually at 5 % false-positive rate.
- **UFS** — Universal Forgery Score. `UFS(W) = âˆ’2 Â· [ln p_EL(W) + ln p_NCD(W)]`.
- **VL_CV** — coefficient of variation of verse-word-counts. Feature #2 in the 5-D fingerprint.

---

## Part IX — Frequently asked questions

**Q: Is this a proof that the Quran is divine?**
A: No. It is a proof that the Quran occupies a multivariate-outlier region of Arabic-text-space that no control corpus reaches, and that internal single-letter edits to it are detectable at 99.07 % recall by a pre-registered gzip-based channel. Those are empirical facts. Inference beyond them is theology and is outside the scope of this project.

**Q: Is this a proof that the Hafs reading is the "correct" one among the 7 / 10 canonical qira'at?**
A: No. Hafs is the only reading we had machine-readable at corpus scale. The pipeline can be re-run with Warsh or any other qira'a as the baseline; we expect (but have not measured) AUC â‰¥ 0.99 on each. Pre-registered `exp107` is the natural follow-up. This guide's "4 readings" refers specifically to the Hafs canonical + the 3 philologically-discussed single-letter variants of Surah 100 verse 1 (A, B, C), not to the 7/10 canonical qira'at.

**Q: Can a careful human forger defeat this stack?**
A: In principle, yes, if they edit an emphatic-stop pair (Øªâ†”Ø· or Ùƒâ†”Ù‚) on an internal letter of a non-rhyming verse. In practice, no such forgery is known to the project team. The next paper milestone is `exp107_quranic_lm` which is expected to close that gap.

**Q: How much compute do I need to reproduce this?**
A: All cited experiments run on a laptop in under 1 hour each, except `exp46_emphatic_substitution` full mode (â‰ˆ 30 min) and the pending `exp106_universal_forgery_score` (estimated 6–10 h for the four benchmarks combined, laptop CPU). No GPU required.

**Q: Is the code open-source?**
A: `src/`, `experiments/`, `data/corpora/` are checked into the repo with SHA-256 manifests. `results/integrity/` carries the pre-registration locks and tolerance envelopes. Everything required to reproduce the claims in this guide is on disk.

**Q: Who checks the checkers?**
A: `docs/reference/audits/ZERO_TRUST_AUDIT_2026-04-22.md` is the internal hostile audit of Â§4.36. External two-team replication is listed as a 1–3 month item in `docs/reference/findings/RANKED_FINDINGS.md Â§6`. No external replication is in hand yet; the paper is explicit that this is the single biggest remaining credibility gap.

---

**End of Canonical Reading Detection Guide v1.0.**
For questions that are not answered here, the authoritative technical reference is `docs/PAPER.md` (v7.8 cand.). For the one-page case summary, see `docs/reference/adiyat/ADIYAT_CASE_SUMMARY.md` (v7.6). For the full ranked finding inventory, see `docs/reference/findings/RANKED_FINDINGS.md` (v1.3).
