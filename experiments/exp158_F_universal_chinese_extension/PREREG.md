# exp158 — F-Universal cross-script extension to Classical Chinese (Daodejing N=11→12 first step)

**Hypothesis ID**: H103_F_Universal_LogographicExtension_Daodejing
**Parent**: H101 (V3.21 exp156, F75 first-principles MAXENT — 11 corpora, all alphabetic scripts)
**Authored**: 2026-04-30 evening (v7.9-cand patch H V3.22 candidate; companion to exp157 + PAPER §4.47.37)
**Status**: PREREG-LOCKED. Hash committed below; run.py reads this hash before executing.

---

## 1. Background and motivation

V3.21 / `exp156` established F-Universal (V3.22 PAPER §4.47.37 compaction of F75) at
`H₁(X) − H_∞(X) ≈ 1 bit` (mean = 0.943 b, CV = 12 %) across 11 oral-tradition canons
spanning **5 unrelated language families** (Semitic, Hellenic, Indo-Aryan, Iranian,
Indo-European) — all using **alphabetic / abjad / abugida** scripts. The verse-final
unit is always a **single phoneme** (Arabic letter, Hebrew letter, Greek letter,
IAST or Devanagari single character, etc.).

**Question (H103)**: does F-Universal extend to a logographic script — Classical
Chinese, Daodejing (王弼 Wang Bi recension, 81 chapters, 道德經) — where the
"verse-final unit" is necessarily a **character (morpheme/syllable)**, not a
phoneme?

This experiment is one of the user's **HIGH-1** (cross-tradition extension to
Classical Chinese) tasks promoted from the V3.22 ranked-opportunity list. It is
**NOT** the full N≥50 extension demanded by CRITICAL-1 (still blocked on data
acquisition for 38 more corpora); it is one step from N=11 to N=12, with explicit
acknowledgment that Daodejing is a **single corpus** and the result is therefore
an **existence proof / counter-example**, not a population claim.

---

## 2. Frozen hypothesis (PREREG-locked)

**H103 (locked)**: under three granularity choices for "verse-final unit" of the
Daodejing — (G-CHAPTER) the last non-punctuation character of each chapter,
(G-LINE) the last non-punctuation character of each newline-delimited line within
each chapter, (G-PHRASE) the character preceding each Chinese-punctuation mark
(`。`, `，`, `；`, `：`, `、`, `？`, `！`) — the F-Universal Shannon–Rényi-∞ gap
`Δ(X) = H₁(X) − H_∞(X)` lies in **[0.5, 1.5] bits** for at least one granularity.

The verdict is determined by **how many of the three granularities** satisfy
`0.5 ≤ Δ ≤ 1.5`:

| n granularities in band | Verdict |
|---:|---|
| 3 / 3 | `PASS_F_UNIVERSAL_EXTENDS_LOGOGRAPHIC_STRONG` |
| 2 / 3 | `PASS_F_UNIVERSAL_EXTENDS_LOGOGRAPHIC_MODERATE` |
| 1 / 3 | `PARTIAL_F_UNIVERSAL_EXTENDS_GRANULARITY_SPECIFIC` |
| 0 / 3 (all in [0.5, 2.5]) | `DIRECTIONAL_F_UNIVERSAL_LARGER_GAP_FOR_LOGOGRAPHIC` |
| 0 / 3 (any > 2.5 or < 0.0) | `FAIL_F_UNIVERSAL_DOES_NOT_EXTEND_TO_LOGOGRAPHIC` |

The narrow band `[0.5, 1.5]` brackets the V3.21 11-corpus mean `0.943 ± CV 12 %`
generously (`mean ± ~50 %`). The widened band `[0.5, 2.5]` allows for a
logographic-script systematic offset of up to 1 bit above the alphabetic mean
(`Δ_max ≤ 2.5 b` is still well below uniform-distribution gap of `log₂(A)` for
plausible A).

---

## 3. Frozen constants (PREREG-locked)

```
SEED = 42
CORPUS_PATH = "data/corpora/zh/daodejing_wangbi.txt"
CORPUS_EXPECTED_SHA256 = "<filled by run.py before computation; locked at run start>"

CHAPTER_REGEX = r"第[一二三四五六七八九十百零〇\d]+章"
PUNCTUATION_FOR_PHRASE_FINAL = "。，；：、？！"
WHITESPACE_AND_NEWLINES = " \t\n\r\u3000"  # incl. ideographic space U+3000
QUOTE_CHARS_TO_STRIP = "「」"  # Chinese quote brackets, not "verse-final letters"

EXPECTED_N_CHAPTERS = 81  # Wang Bi recension has exactly 81 chapters

GRANULARITIES = ["chapter_final", "line_final", "phrase_final"]

# F-Universal band (mirrors V3.21 mean ± ~50 %)
GAP_BAND_LO = 0.5
GAP_BAND_HI = 1.5
GAP_WIDENED_BAND_LO = 0.5
GAP_WIDENED_BAND_HI = 2.5

# Pool reference values from V3.21 (for comparison only, NOT thresholds)
V321_GAP_MEAN = 0.943
V321_GAP_CV = 0.12

# V3.21 pool MAXENT input scale
A_ALPHABETIC_REF = 28  # Arabic abjad; reference only, not used for Chinese MAXENT

EXP156_RECEIPT_PATH = "results/experiments/exp156_F75_beta_first_principles_derivation/exp156_F75_beta_first_principles_derivation.json"
EXP156_EXPECTED_SHA256 = "ff6f95611b1de5c81ed31f347264d3ecf0c8fde2176c4f6579e4474adadaaef6"
```

---

## 4. Pre-registered criteria

Each of the 3 granularities is independently evaluated against C1 (in-band) and
C2 (widened-in-band). The verdict is computed from C1 PASS counts.

### C1 (per granularity) — gap in band `[0.5, 1.5]`

PASS iff `0.5 ≤ Δ(X, granularity) ≤ 1.5`.

### C2 (per granularity) — gap in widened band `[0.5, 2.5]`

PASS iff `0.5 ≤ Δ(X, granularity) ≤ 2.5`.

### C3 — V3.21 byte-equivalence audit

PASS iff the V3.21 11-corpus β values from the exp156 receipt are byte-equivalent
to the locked SHA-256 (no re-fitting; pool reference only).

### C4 — chapter-count sanity

PASS iff the Daodejing chapter splitter yields **exactly 81** non-empty chapters
(Wang Bi recension invariant).

### C5 — granularity-monotonicity sanity

PASS iff the relationship `n(chapter_final_units) < n(line_final_units) <
n(phrase_final_units)` holds (each finer granularity must yield strictly more
verse-final samples; if violated, the splitter is broken).

C3, C4, C5 are **audit hooks**; they MUST pass for the run to be considered valid.
They do NOT contribute to the verdict count — the verdict is solely determined by
C1 PASS count across the 3 granularities.

---

## 5. Pre-registered audit hooks (must hold or run is invalid)

A1. The corpus file at `CORPUS_PATH` MUST exist; its SHA-256 is computed and
    locked at run start (no expected value baked in — this is the corpus's
    first-pass-into-experiments lock).

A2. The exp156 receipt's SHA-256 MUST match `EXP156_EXPECTED_SHA256`.

A3. No locked finding's PASS/PARTIAL/FAIL status MAY change as a side-effect of
    this run. F75 / F-Universal label / F46 / F55 / F66 / F67 / F76 / F77 / F78
    / F79 / LC2 / LC3 verdicts MUST remain byte-identical to the V3.22-pre
    `RANKED_FINDINGS.md` text.

A4. The F75 11-corpus PASS verdict (V3.18 PARTIAL → V3.19 PARTIAL+ → V3.20
    STRONG → V3.21 STRONG) MUST remain unchanged regardless of this experiment's
    outcome. F-Universal extension to N=12 (or its failure) does NOT retroactively
    affect the N=11 verdict.

A5. The Daodejing splitter MUST split exactly on the regex
    `第[一二三四五六七八九十百零〇\d]+章` (Chinese chapter marker pattern); any
    fallback heuristic that infers chapter boundaries by other means is forbidden.

A6. Quote characters `「` and `」` MUST be stripped before identifying
    "verse-final" characters (they are punctuation, not content). Whitespace
    including the ideographic space U+3000 MUST be stripped.

A7. Brown-Stouffer is NOT used; this experiment is purely empirical entropy
    computation on a single corpus plus a band-check.

---

## 6. Falsifiable predictions (commitments before run)

```
P1: at least one of the 3 granularities has gap Δ ∈ [0.5, 1.5]
P2: chapter_final has the smallest gap among the three (most concentrated)
P3: phrase_final has the largest gap (most diffuse, since most distinct chars)
P4: H_∞ (chapter_final) ≥ 3.5 b (since p_max ≤ ~0.07 from manual inspection)
P5: H_1 (chapter_final) ≤ log₂(81) = 6.34 b (entropy ≤ log of sample size)
```

If P1 fails (no granularity in band), the verdict drops to either DIRECTIONAL
or FAIL depending on whether all three are still in the widened band.

If P2 or P3 fails, the granularity-monotonicity sanity is violated (counter-
intuitive but not necessarily fatal — would warrant investigation).

If P4 or P5 fails, basic entropy arithmetic is broken (would be a code bug, not
a substantive result).

---

## 7. What this experiment does NOT claim

- It does **NOT** claim Daodejing is canonically an "oral-tradition" canon in
  the same recitational-liturgical sense as the 11 V3.21 corpora. Daodejing is
  primarily a **written philosophical text** with limited oral-recitation tradition
  (compared to Quran/Vedas/Tipiṭaka). The point of the experiment is to test
  whether F-Universal's 1-bit gap is a property of **oral canons specifically**
  or of **written-canonical literary corpora more generally**.
- It does **NOT** establish Sino-Tibetan family extension. One corpus (Daodejing)
  is **not** a family. To establish Sino-Tibetan extension would require at
  minimum the four canonical Confucian-Daoist texts (大學, 中庸, 論語, 孟子) plus
  Buddhist Chinese sutras, which are **out of scope**.
- It does **NOT** address the V3.21 MAXENT β framework. The β parameter requires
  a finite alphabet; logographic Chinese has a much larger character inventory
  than the Arabic abjad's 28 letters, and direct β-extraction would mix
  morpho-phonological structures incomparable to the alphabetic 11-corpus pool.
  This experiment ONLY tests F-Universal (the Shannon–Rényi gap), which is
  alphabet-cardinality-independent.
- It does **NOT** attempt to derive a romanisation / phonological transcription
  of the Daodejing. Such a transcription would require a phonological-reconstruction
  choice (Old Chinese / Middle Chinese / modern Mandarin pinyin / Cantonese
  jyutping) and would prejudge the result.

---

## 8. Counts impact (post-run, conditional on verdict)

| Verdict | Tier-C observations | Failed-null pre-regs | Retractions |
|---|---|---|---|
| `PASS_F_UNIVERSAL_EXTENDS_LOGOGRAPHIC_STRONG` | 13 → 14 (add O14) | unchanged | unchanged |
| `PASS_F_UNIVERSAL_EXTENDS_LOGOGRAPHIC_MODERATE` | 13 → 14 (add O14 MODERATE) | unchanged | unchanged |
| `PARTIAL_F_UNIVERSAL_EXTENDS_GRANULARITY_SPECIFIC` | 13 → 14 (add O14 PARTIAL) | unchanged | unchanged |
| `DIRECTIONAL_F_UNIVERSAL_LARGER_GAP_FOR_LOGOGRAPHIC` | unchanged | unchanged | unchanged |
| `FAIL_F_UNIVERSAL_DOES_NOT_EXTEND_TO_LOGOGRAPHIC` | unchanged | 25 → 26 (add FN29) | unchanged |

Note: this experiment is logically independent of `exp157` (H102, finite-buffer
MAXENT). Both feed into the V3.22 capsule; both can pass or fail independently.

---

## 9. Provenance and reproducibility

- This PREREG.md is hash-locked. SHA-256 of bytes up to and including the
  `_PREREG_LOCKED_BYTES_END` sentinel is committed in `run.py` as
  `_PREREG_EXPECTED_HASH`; drift aborts.
- The Daodejing corpus SHA-256 is computed and locked at run start (recorded in
  receipt as `corpus_sha256_locked_at_run_start`); subsequent runs verify byte-
  equivalence.
- The exp156 receipt is hash-pinned via A2.
- No external network calls; all computation uses only the Python stdlib +
  numpy for entropy arithmetic.
- Wall-time estimate: < 1 second.

---

## 10. PREREG-locked file hash

The SHA-256 of THIS FILE'S BYTES (excluding content after the
`_PREREG_LOCKED_BYTES_END` sentinel below) is committed in `run.py` as
`_PREREG_EXPECTED_HASH` and verified at run start.

_PREREG_LOCKED_BYTES_END
