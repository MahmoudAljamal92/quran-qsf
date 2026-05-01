# exp106_F55_mark1_bigram — PREREG

**Hypothesis ID**: H61
**Parent**: H43 (F55 universal symbolic forgery detector, `exp95j_bigram_shift_universal`, `PASS_universal_perfect_recall_zero_fpr`).
**Sibling**: H60 (`exp105_F55_psalm78_bigram`, `PASS_universal_perfect_recall_zero_fpr` / F59) — Hebrew Tanakh Psalm 78, same detector class, second cross-tradition F55 pilot. H61 is the third.
**Patch**: v7.9-cand patch H V3.4 (cross-tradition F55 pilot — Greek NT, Indo-European).
**Filed**: 2026-04-29 (UTC+02 night).

---

## 1. Hypothesis statement (locked)

Under the **bigram-shift detector with frozen analytic-bound τ = 2.0** (the F55 detector class, locked by the analytic theorem in `experiments/exp95j_bigram_shift_universal/PREREG.md` §3.2), single-Greek-letter substitution forgeries on **Mark 1** of the Greek New Testament (OpenGNT v3.3, book = 41, chapter = 1) are detected at **per-variant recall = 1.000** with **per-(canon, peer)-pair FPR = 0.000** against the full Greek NT peer pool of all 259 other chapters (no length matching, byte-exact match to the Quran-side `exp95j` protocol), replicating the F55 result on Quran V1 and on Hebrew Psalm 78 (F59) in a third independent tradition: **Indo-European language family, Greek script, ~1st-century CE composition**.

This is the **fourth Phase-3 cross-tradition pilot** (after FN10 + FN11 closed off-shelf F53 K=2 cross-tradition under locked Hebrew calibration, and F59 established F55 cross-tradition success on Hebrew Psalm 78). H61 tests F55 in a tradition that is:

- Different language family from both Quran (Central Semitic) and Hebrew Psalm 78 (Northwest Semitic): Greek is **Hellenic / Indo-European**.
- Different alphabet: 24 lowercase Greek letters (post-normaliser; sigma forms folded) vs 28 Arabic consonants vs 22 Hebrew consonants.
- Different writing system: Greek script (left-to-right, vowels written) vs Arabic abjad (right-to-left, vowels optional) vs Hebrew abjad (right-to-left, vowels via niqqud).
- Different historical period from both: ~1st-century CE Koine Greek vs ~7th-century CE Classical Arabic vs ~1000 BCE editorial Biblical Hebrew.

A H61 PASS would establish F55 generalisation across **3 language families** and **3 millennia** with **zero parameter change** between the three runs. This is the strongest cross-tradition replication pattern available to the project at chapter scope.

---

## 2. Frozen constants (locked at PREREG seal time)

```
SEED                            = 42
TAU_HIGH                        = 2.0          # F55 analytic-bound, no calibration
AUDIT_TOL                       = 1e-9         # numeric float-compare tolerance
RECALL_FLOOR                    = 1.000        # per-variant; F55 paper-grade gate
FPR_CEIL                        = 0.000        # per-(canon, peer)-pair; F55 paper-grade gate
PARTIAL_FPR_BAND_HI             = 0.05         # for partial-PASS branch
TARGET_BOOK_NUMBER              = 41           # Mark in OpenGNT v3.3 internal numbering
TARGET_CHAPTER                  = 1            # Mark 1
TARGET_MIN_LETTERS              = 1000         # locked from exp104/105 chapter-length floor
TARGET_MIN_VERSES               = 10
PEER_POOL_STRATEGY              = "all_other_greek_nt_chapters_no_length_matching"
PEER_AUDIT_FLOOR                = 100          # min peer pool size (locked from exp104c)
GREEK_LETTERS_24                = "αβγδεζηθικλμνξοπρστυφχψω"
NORMALISER_SENTINEL_INPUT       = "Ἐν ἀρχῇ ἦν ὁ λόγος"
NORMALISER_SENTINEL_EXPECTED    = "εναρχηηνολογοσ"
```

The detector itself is a single-line decision: variant fires iff `0 < Δ_bigram(canon, variant) ≤ TAU_HIGH`; peer pair fires iff `0 < Δ_bigram(canon, peer) ≤ TAU_HIGH`.

`Δ_bigram(a, b) := ½ · Σ_k |count_a[k] − count_b[k]|` over the union of bigram keys k, where bigrams are *raw* (unnormalised) counts of consecutive 2-character substrings of the consonant skeleton (whitelist-only, drop everything outside the 24-letter alphabet; matches exp95j Arabic-side and exp105 Hebrew-side conventions).

The Greek normaliser is the locked function from `experiments/exp104d_F53_mark1/run.py::_normalise_greek` (PREREG hash `48ddbef186060365e7bb6db4b71bd1b6e31621effab283b994eb093fb8e139e3`, sentinel-verified):

1. Unicode NFD decomposition.
2. Drop all combining marks (Unicode category 'Mn').
3. `casefold()` to lowercase (Greek-aware).
4. Fold all sigma variants (`ς`, `ϲ`, `Ϲ`) → medial `σ`.
5. Whitelist only the 24 lowercase Greek letters; drop everything else (whitespace, punctuation, digits, Latin letters, etc.).

The OpenGNT v3.3 loader is the locked function `experiments/exp104d_F53_mark1/run.py::_load_greek_nt_chapters` (handles Japanese-bracket compound fields `〔...〕`, fullwidth-pipe inner separator `｜`, lunate sigma `ϲ` in OGNTk column).

---

## 3. Frozen protocol (locked)

### 3.1 — Variant enumeration

For Mark 1's normalised skeleton `S` of length n_letters: enumerate **all n_letters × 23 single-Greek-letter substitutions** (every position × every other-of-24 substitute). Predicted variant count: **3,530 × 23 = 81,190** (verified by pre-stage diagnostic).

### 3.2 — Variant scoring (analytic O(1) per call)

Use the same analytic-bound implementation as `experiments/exp95j_bigram_shift_universal/run.py::variant_delta_analytic`: only the (up to 4) bigrams touching the substituted position change; compute the L1 difference of those 4 bigrams and divide by 2.

A variant *fires* iff `0 < Δ ≤ TAU_HIGH`.

### 3.3 — Peer scoring (exact)

For each peer chapter `p` in the locked pool (all 259 Greek NT chapters except Mark 1), compute `Δ_bigram(canon, p)` from the full bigram counters. A peer pair *fires* iff `0 < Δ ≤ TAU_HIGH`.

### 3.4 — Audit hooks (must all pass)

- **A1 — Variant theorem**: `max(variant_Δ) ≤ TAU_HIGH + AUDIT_TOL = 2.0 + 1e-9`. Theoretical certainty per the F55 PREREG theorem; this hook validates the implementation.
- **A2 — Peer pool size**: `n_peers ≥ PEER_AUDIT_FLOOR = 100`. Pre-stage confirms 259 ≥ 100.
- **A3 — Target chapter floors**: `n_letters ≥ TARGET_MIN_LETTERS = 1,000` and `n_verses ≥ TARGET_MIN_VERSES = 10`. Pre-stage confirms Mark 1 has 3,530 letters / 45 verses.
- **A4 — Sentinel determinism**: re-running the analytic variant scorer on a random sample of 100 (variant, peer) pairs must produce byte-identical Δ values across two passes. Validates loader + normaliser determinism.
- **A5 — Normaliser sentinel**: `_normalise_greek("Ἐν ἀρχῇ ἦν ὁ λόγος") == "εναρχηηνολογοσ"`. Validates the locked normaliser; identical to exp104d's A5.

### 3.5 — Pre-stage diagnostic (already executed, attached as evidence)

`scripts/_mark1_bigram_sizing.py` (filed under `results/auxiliary/_mark1_bigram_sizing.json`, run 2026-04-29 night) executed the variant theorem replication and the peer FPR-floor check **before** this PREREG was sealed:

| Probe | Result |
|---|---|
| Variant audit (N=1,000 sampled) | min Δ = 1.000, mean = 1.999, max = 2.000, n_above_τ = 0 |
| Peer audit (n=259 full pool) | min Δ = **535.50** (Mark 5), p5 = 683.0, median = 943.0, max = 1,438 |
| Safety margin | peer_min / τ = **267.8×** (compare Hebrew 340.2× / Arabic 36.8×) |

**Pre-stage verdict**: PROCEED_TO_PREREG. The analytic theorem holds on the 24-letter Greek alphabet and the peer-side Δ distribution sits orders of magnitude above τ. The 5 closest peers to Mark 1 are all from Mark itself or Luke (same-author / same-genre clustering); all are ≥ 267× over τ.

---

## 4. Verdict ladder (pre-registered, branches mutually exclusive)

The ladder is checked in order; the first matching branch fires.

1. **`BLOCKED_corpus_missing`** — `data/corpora/el/opengnt_v3_3.csv` absent or unreadable. *No claim made.*
2. **`BLOCKED_mark_1_too_short`** — `n_letters < TARGET_MIN_LETTERS` OR `n_verses < TARGET_MIN_VERSES`. *Should be unreachable; locked Mark 1 has 3,530 letters / 45 verses.*
3. **`FAIL_audit_peer_pool_size`** — n_peers < PEER_AUDIT_FLOOR. *Pre-stage confirms 259 ≥ 100; should be unreachable.*
4. **`FAIL_audit_normaliser_sentinel`** — A5 sentinel does not match. *Validates normaliser; would indicate code drift from exp104d.*
5. **`FAIL_audit_theorem`** — A1 violation: at least one variant has Δ > 2.0 + 1e-9. *Mathematically impossible per F55 theorem; would indicate implementation bug.*
6. **`FAIL_recall_below_floor`** — variant_recall < 1.000. *Possible iff some variants land at Δ = 0 (bigram-coincidence substitutions); pre-stage saw 0/1,000.*
7. **`FAIL_fpr_above_ceiling`** — peer_fpr > 0.000. *Pre-stage min Δ = 535.5; would require a Greek NT chapter to be near-bigram-identical to Mark 1, which is statistically impossible.*
8. **`PARTIAL_fpr_below_band`** — variant_recall == 1.000 AND 0 < peer_fpr ≤ PARTIAL_FPR_BAND_HI. *Soft PASS, not paper-grade.*
9. **`PASS_universal_perfect_recall_zero_fpr`** — variant_recall == 1.000 AND peer_fpr == 0.000. **F-row candidate** (label TBD by `RANKED_FINDINGS.md` rules; reservation requested below).

### 4.1 — F-row reservation policy

If branch 9 fires AND all five audit hooks pass, the result will be filed as **F60** (next available F-row after F59 cross-tradition Hebrew). The F-row is provisional until the doc-update step (RANKED + PAPER + REGISTRY) lands. If branches 5/6/7 fire, the result will be filed as **FN12** (failed-null pre-registration, Category K of `RETRACTIONS_REGISTRY.md`); H61 stays a hypothesis row, never gets an F-row.

---

## 5. Honest scope statement

**Pre-committed before observing the receipt:** A `PASS_universal_perfect_recall_zero_fpr` outcome would establish:

- The **second** cross-tradition POSITIVE F-detector data point (F59 was the first; H61 PASS would be the second).
- F55 generalises across **3 language families** at chapter scope: Central Semitic (Quran V1, exp95j), Northwest Semitic (Hebrew Psalm 78, exp105 / F59), Hellenic Indo-European (Greek Mark 1, this run / candidate F60).
- F55's discriminative power is plausibly **alphabet-agnostic and language-family-agnostic** for any substitution-cipher attack model where the alphabet has ≥ ~20 distinct letters, the chapter has ≥ ~1,000 letters, and there are ≥ 100 peer chapters in the corpus.

It would NOT establish:

- That F55 generalises to non-Indo-European, non-Semitic traditions (Sanskrit Vedic, Pali Canon, Avestan Yasna are separate hash-locked PREREGs).
- That F55 generalises to chapter-shorter-than-1,000-letters traditions or peer-pool-smaller-than-100 traditions (separate amendment regime).
- That the cross-tradition F55 result is "Quran-distinctive" — F55 is a **detector** receipt (recall + FPR), NOT a Quran-distinctiveness claim. F60 confirms detector-mechanism universality; says nothing about Quran-vs-other ranking.
- That F53's failure on Hebrew (FN11) is "rescued" — different detector class entirely.

**Pre-committed before observing the receipt:** A FAIL outcome (any of branches 5–7) is publishable as **FN12**. A theorem-violation (branch 5) would be alarming and would necessitate investigating the Greek normaliser. A recall-below-floor (branch 6) would mean Greek has bigram-coincidence substitutions where Δ = 0. An FPR-above-ceiling (branch 7) would mean some Greek NT chapter is near-bigram-identical to Mark 1, which contradicts the pre-stage observation.

---

## 6. Hash-lock procedure

This file's SHA-256 hash is computed at seal time and stored at `experiments/exp106_F55_mark1_bigram/PREREG_HASH.txt`. The accompanying `run.py` reads its expected hash from a constant `_PREREG_EXPECTED_HASH` literal; `run.py` refuses to execute if the in-file PREREG hash drifts from the locked expected value.

**Seal hash**: see `PREREG_HASH.txt`.

---

## 7. Receipt schema (locked)

```
{
  "experiment": "exp106_F55_mark1_bigram",
  "hypothesis_id": "H61",
  "verdict": "<one of branch 1-9 above>",
  "verdict_reason": "<short string>",
  "started_at_utc": "...",
  "completed_at_utc": "...",
  "wall_time_s": <float>,
  "prereg_hash": "<sha256>",
  "prereg_expected_hash": "<sha256>",
  "frozen_constants": { ... §2 verbatim ... },
  "audit_report": {
    "ok": <bool>,
    "checks": {
      "n_chapters_total":      <int>,
      "target_book_number":    41,
      "target_chapter":        1,
      "target_n_verses":       <int>,
      "target_n_letters":      <int>,
      "peer_pool_size":        <int>,
      "peer_pool_strategy":    "all_other_greek_nt_chapters_no_length_matching",
      "max_variant_delta":     <float>,
      "min_peer_delta":        <float>,
      "n_variants_total":      <int>,
      "n_variants_fired":      <int>,
      "n_peer_pairs_total":    <int>,
      "n_peer_pairs_fired":    <int>,
      "variant_recall":        <float>,
      "peer_fpr":              <float>,
      "five_closest_peers":    [...],
      "sentinel_determinism":  "OK" | "<error>",
      "normaliser_sentinel":   "OK" | "<error>"
    },
    "warnings": [...],
    "errors":   [...]
  },
  "pre_stage_diagnostic_receipt":
      "results/auxiliary/_mark1_bigram_sizing.json"
}
```

---

## 8. Out of scope

- Sanskrit Vedic, Pali Canon, Avestan Yasna chapters — separate PREREGs each.
- Insertion or deletion forgeries (F55 V1 scope is substitution-only).
- Multi-letter forgeries (V2+ scope).
- Any τ != 2.0 (different detector class; not in F55 family).
- Any calibration step (the *whole point* is no calibration).
- Length-matched peer pool variants (this run uses no length matching by design, matching exp95j).
- LLM-generated forgeries (separate Phase-5+ PREREG).

---

## 9. Cross-references

- F55 detector definition: `experiments/exp95j_bigram_shift_universal/PREREG.md`
- F55 theorem 3.2: `experiments/exp95j_bigram_shift_universal/PREREG.md` §3.2
- Greek normaliser + OpenGNT loader: `experiments/exp104d_F53_mark1/run.py` (sentinel-locked)
- Sibling H60 (F55 → Hebrew, F59): `experiments/exp105_F55_psalm78_bigram/PREREG.md`
- Pre-stage diagnostic receipt: `results/auxiliary/_mark1_bigram_sizing.json`
- Failure-mode contrast: `docs/PAPER.md` §4.47.5 (FN11 F53 Hebrew calibration-collapse), §4.47.8 (F59 F55 Hebrew PASS)
