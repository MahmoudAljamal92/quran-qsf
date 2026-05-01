## exp119 — F70 Universal-Language Scope of F55 Forgery Detector

**Status:** PRE-REGISTERED (locked before run).
**Hypothesis ID:** H74.
**Date sealed:** 2026-04-29 (UTC).

---

### Scientific question

F55 (single-letter substitution detector via bigram-histogram L1 distance) was
formulated and validated on Arabic Quran + Arabic peers. The multi-letter
generalisation (F69, exp118) proves that **for any sequence of symbols**, a
k-letter substitution gives Δ_bigram ≤ 2k. This bound is **alphabet-independent
and language-independent** by construction.

The remaining empirical question is **scope of the detector's usefulness**:

> When applied with the same definition (bigram on letter-skeleton, Δ ≤ 2)
> to **other natural-language sacred / canonical corpora**, does F55 retain
> its (a) theorem-tightness, (b) recall = 1 on planted single-letter edits,
> and (c) discrimination against peer chapters within the same corpus?

We test five language traditions already locked in the project's corpus
inventory:

| Tradition | Alphabet | n_units | Source | Normaliser |
|---|---|---|---|---|
| Quran | Arabic 28 | 114 sūrahs | `data/corpora/ar/quran_bare.txt` | `_normalise_arabic` |
| Hebrew Tanakh | Hebrew 22 | ~929 chapters | `data/corpora/he/tanakh_wlc.txt` | `_normalise_hebrew` |
| Greek NT | Greek 24 | ~260 chapters | `data/corpora/el/opengnt_v3_3.csv` | `_normalise_greek` |
| Pali Tipiṭaka | IAST 31 | ~186 suttas (DN+MN) | `data/corpora/pi/{dn,mn}/*.json` | `_normalise_pali` |
| Rigveda | Devanagari ~50 | ~1028 sūktas | `data/corpora/sa/rigveda_mandala_*.json` | sanskrit (added here) |

The **universal claim** (theorem) is alphabet-independent. The **operational
claim** (recall, FPR) requires per-corpus testing.

---

### Locked design

#### Constants

| Symbol | Value | Meaning |
|---|---|---|
| K_VALUES | [1, 2, 3] | Number of letters substituted per planted edit |
| N_SUBS_PER_UNIT | 200 | Random substitutions per unit per k |
| N_FPR_PAIRS | 2000 | Random within-corpus chapter pairs per k for FPR |
| SEED_BASE | 1119 | Frozen RNG seed |
| RECALL_FLOOR | 0.99 | Per-corpus, per-k minimum required recall |
| FPR_CEILING | 0.05 | Per-corpus, per-k maximum allowed FPR |

#### Forms

**Form 1 — Theorem universality.**
For every (corpus, k) pair, every planted k-letter substitution must give
Δ_bigram ≤ 2k. *Mathematical certainty; we report `n_violations` which must
equal 0 by Theorem F69.*

**Form 2 — Per-tradition recall.**
For every (corpus, k), with detection threshold τ_k = 2k, recall ≥ 0.99.
"recall" = fraction of substitutions where 0 < Δ ≤ 2k (strict positive: the
substitution is detected and the bound holds).

**Form 3 — Per-tradition peer-FPR.**
For every (corpus, k), draw N_FPR_PAIRS random pairs of *distinct* chapters
within the corpus. FPR = fraction with Δ ≤ 2k. Required FPR ≤ 0.05 to
declare F55 *useful* in that tradition (i.e., distinct chapters are
distinguishable from k-letter edits).

**Form 4 — Cross-tradition Quran-edge sharpness (descriptive).**
Compute per-corpus edge metric:

    Edge(C) = peer_min_Δ(C) / median_chapter_length(C)

The Quran's Edge will be reported alongside other traditions; *not* a pass/fail
criterion (descriptive only — Form 4 is exploratory).

#### Decision rules

The verdict aggregates Forms 1, 2, 3 across all 5 traditions:

| Pattern | Verdict |
|---|---|
| All Form 1 PASS, all Form 2 PASS, all Form 3 PASS | `PASS_F55_universal_across_5_traditions` |
| Form 1 fails for any (corpus, k) | `FAIL_theorem_violated` (would falsify F69) |
| Form 2 fails ≥1 tradition | `PARTIAL_PASS_recall_uneven` |
| Form 3 fails ≥1 tradition | `PARTIAL_PASS_FPR_too_high_in_some_traditions` |

Form 4 is **exploratory** — reported but does not affect verdict.

#### Pre-specified honest framings

- **If verdict is PASS:** "F55 detector is alphabet-independent: bigram-Δ ≤ 2k
  holds and detects k-letter edits with ≥99% recall and ≤5% FPR across 5
  unrelated language traditions (Arabic, Hebrew, Greek, Pali-IAST, Sanskrit-Devanagari)."
- **If FPR fails for some tradition:** "F55 is universal in *theorem*, but its
  *operational* recall vs. FPR trade-off depends on within-corpus chapter
  similarity. Quran's value is therefore not just universality but the *sharpness*
  of its edge."

---

### Auxiliaries

- Receipt: `results/experiments/exp119_universal_F55_scope/exp119_universal_F55_scope.json`
- Writes per-corpus sub-receipts under same dir.
- Reuses normalisers from `scripts/_phi_universal_xtrad_sizing.py`.
- Reuses unit loaders from `scripts/_phi_universal_xtrad_sizing.py`.
- Adds Sanskrit normaliser (skeleton: Devanagari base letters, NFD-strip
  combining marks) — same definition as `scripts/_rigveda_loader_v2.py`.

### Audit hooks

- `prereg_sha256` + `frozen_constants` recorded in receipt.
- `n_units_per_corpus`, `n_letters_skeleton_median` recorded for sizing audit.
- `theorem_violations_per_corpus_per_k` recorded — must be 0.
