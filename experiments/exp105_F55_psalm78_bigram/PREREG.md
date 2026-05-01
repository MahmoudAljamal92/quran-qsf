# exp105_F55_psalm78_bigram — PREREG

**Hypothesis ID**: H60
**Parent**: H43 (F55 universal symbolic forgery detector, `exp95j_bigram_shift_universal`, `PASS_universal_perfect_recall_zero_fpr`).
**Sibling**: H59c (`exp104c_F53_psalm78`, `FAIL_fpr_above_ceiling` / FN11) — same target chapter Psalm 78, different detector class (NCD-consensus vs analytic bigram-shift).
**Patch**: v7.9-cand patch H V3.3 (cross-tradition F55 pilot).
**Filed**: 2026-04-29 (UTC+02 night).

---

## 1. Hypothesis statement (locked)

Under the **bigram-shift detector with frozen analytic-bound τ = 2.0** (the F55 detector class, locked by the analytic theorem in `experiments/exp95j_bigram_shift_universal/PREREG.md` §3.2), single-Hebrew-consonant substitution forgeries on **Psalm 78** of the Westminster Leningrad Codex (תהלים, chapter עח) are detected at **per-variant recall = 1.000** with **per-(canon, peer)-pair FPR = 0.000** against the locked length-matched narrative-Hebrew peer pool, replicating the F55 result on Quran V1 in a different language family (Northwest Semitic / Hebrew vs Central Semitic / Quranic Arabic), different writing system (Hebrew square script vs Arabic abjad), different historical period (~1000 BCE editorial vs 7th-century CE), with **zero parameter change** between the Quran-side and Hebrew-side detector.

This is the third Phase-3 cross-tradition F-detector pilot (after FN10 + FN11 closed off-shelf F53 K=2 cross-tradition under locked Hebrew-narrative-pool calibration). H60 tests a **distinct detector class** (analytic bigram-shift, no calibration step) on the same Hebrew chapter the F53 attempt failed on; the calibration-collapse mechanism that produced FN11 is structurally inapplicable here because F55's τ = 2.0 is *not* calibrated.

---

## 2. Frozen constants (locked at PREREG seal time)

```
SEED                            = 42
TAU_HIGH                        = 2.0          # F55 analytic-bound, no calibration
AUDIT_TOL                       = 1e-9         # numeric float-compare tolerance
RECALL_FLOOR                    = 1.000        # per-variant; F55 paper-grade gate
FPR_CEIL                        = 0.000        # per-(canon,peer)-pair; F55 paper-grade gate
PARTIAL_FPR_BAND_HI             = 0.05         # for partial-PASS branch
LENGTH_MATCH_FRAC               = 0.30         # +/- 30% of Psalm 78 letter count (locked from exp104c)
TARGET_BOOK                     = "תהלים"      # Psalms (WLC, no yod)
TARGET_CHAPTER                  = "עח"          # Psalm 78 (ayin-chet = 70+8)
TARGET_MIN_LETTERS              = 1000          # locked from exp104 (anti-Psalm-19 floor)
TARGET_MIN_VERSES               = 10            # locked from exp104 (anti-Psalm-19 floor)
PEER_BOOKS                      = (             # locked from exp104 narrative whitelist
    "בראשית", "שמות", "יהושע", "שופטים",
    "שמואל א", "שמואל ב", "מלכים א", "מלכים ב",
)
TARGET_N_PEERS                  = 200           # cap (sample if exceeded)
PEER_AUDIT_FLOOR                = 100           # min peer pool size (locked from exp104c)
N_FPR_PEERS                     = "ALL"         # use the full peer pool, not a sample
```

The detector itself is a single-line decision: variant fires iff `0 < Δ_bigram(canon, variant) ≤ TAU_HIGH`; peer pair fires iff `0 < Δ_bigram(canon, peer) ≤ TAU_HIGH`.

`Δ_bigram(a, b) := ½ · Σ_k |count_a[k] − count_b[k]|` over the union of bigram keys k, where bigrams are *raw* (unnormalised) counts of consecutive 2-character substrings of the consonant skeleton (with verse-separating ASCII spaces; identical convention to `exp95j` where peer skeleton is `letters_28(" ".join(u.verses))`).

The Hebrew consonant skeleton is the locked 22-letter normaliser from `experiments/exp104_F53_tanakh_pilot/run.py::_hebrew_skeleton_with_spaces`: niqqud and te'amim are stripped; final-form letters are folded to base form (ך→כ, ם→מ, ן→נ, ף→פ, ץ→צ); only the 22 base Hebrew consonants survive; verses are joined with ASCII single spaces.

---

## 3. Frozen protocol (locked)

### 3.1 — Variant enumeration

For Psalm 78's no-space consonant skeleton `S` of length n_22 letters: enumerate **all n_22 × 21 single-letter substitutions** (every position × every other-of-22 substitute). Apply each substitution to the *with-space* skeleton at the corresponding mapped position (no-space-pos → with-space-pos lookup) to produce the variant string for Δ-scoring.

Predicted variant count: **2,384 × 21 = 50,064** (matches exp104c's 50,064).

### 3.2 — Variant scoring (analytic O(1) per call)

Use the same analytic-bound implementation as `experiments/exp95j_bigram_shift_universal/run.py::variant_delta_analytic`: only the (up to 4) bigrams touching the substituted position change; compute the L1 difference of those 4 bigrams and divide by 2.

A variant *fires* iff `0 < Δ ≤ TAU_HIGH`.

### 3.3 — Peer scoring (exact)

For each peer chapter `p` in the locked pool, compute `Δ_bigram(canon, p)` from the full bigram counters. A peer pair *fires* iff `0 < Δ ≤ TAU_HIGH`.

### 3.4 — Audit hooks (must all pass)

- **A1 — Variant theorem**: `max(variant_Δ) ≤ TAU_HIGH + AUDIT_TOL = 2.0 + 1e-9`. Theoretical certainty per the F55 PREREG theorem; this hook validates the implementation.
- **A2 — Peer pool size**: `n_peers ≥ PEER_AUDIT_FLOOR = 100`. Pre-stage diagnostic confirms 114 narrative-Hebrew chapters fall in the locked ±30% window [1,668, 3,099] letters around Psalm 78 (n_letters_22 = 2,384).
- **A3 — Target chapter floors**: `n_letters_22 ≥ TARGET_MIN_LETTERS = 1,000` and `n_verses ≥ TARGET_MIN_VERSES = 10`. Psalm 78 satisfies both (2,384 letters, 52 verses).
- **A4 — Sentinel determinism**: re-running the analytic variant scorer on a random sample of 100 (variant, peer) pairs must produce byte-identical Δ values across two passes (no compressor, so no environment dependency; this hook validates that the loader produces the same skeleton across runs).

### 3.5 — Pre-stage diagnostic (already executed, attached as evidence)

`scripts/_psalm78_bigram_sizing.py` (filed under `results/auxiliary/_psalm78_bigram_sizing.json`, run 2026-04-29 night) executed the variant theorem replication and the peer FPR-floor check **before** this PREREG was sealed:

| Probe | Result |
|---|---|
| Variant audit (N=500 sampled) | min Δ = 1.000, mean = 1.998, max = 2.000, n_above_τ = 0 |
| Peer audit (n=114 full pool) | min Δ = **680.5** (Joshua 9), p5 = 706.5, median = 814.5, max = 1 119 |
| Safety margin | peer_min / τ = **340.2×** (compare Arabic = 36.8× in exp95j) |

**Pre-stage verdict**: PROCEED_TO_PREREG. The analytic theorem holds on the Hebrew alphabet (22-consonant) and the peer-side Δ distribution sits orders of magnitude above τ. The full enumeration in §3.1 will resolve only the remaining open question of whether *any* of the 50,064 variants happens to land at Δ = 0 (substitution where the left+right bigrams coincide before/after) — see §4.4.

---

## 4. Verdict ladder (pre-registered, branches mutually exclusive)

The ladder is checked in order; the first matching branch fires.

1. **`BLOCKED_corpus_missing`** — `data/corpora/he/tanakh_wlc.txt` absent or unreadable. *No claim made.*
2. **`BLOCKED_psalm_78_too_short`** — `n_letters_22 < TARGET_MIN_LETTERS` OR `n_verses < TARGET_MIN_VERSES`. *Should be unreachable; locked Psalm 78 has 2,384 letters / 52 verses.*
3. **`FAIL_audit_peer_pool_size`** — n_peers < PEER_AUDIT_FLOOR after locked length-match. *Pre-stage diagnostic confirms 114; should be unreachable.*
4. **`FAIL_audit_theorem`** — A1 violation: at least one variant has Δ > 2.0 + 1e-9. *Mathematically impossible per F55 theorem; would indicate implementation bug.*
5. **`FAIL_recall_below_floor`** — variant_recall < 1.000. *Possible iff some variants land at Δ = 0 (bigram-coincidence substitutions); pre-stage saw 0/500.*
6. **`FAIL_fpr_above_ceiling`** — peer_fpr > 0.000. *Pre-stage min Δ = 680.5; would require an unprecedented peer chapter or a loader regression to fire.*
7. **`PARTIAL_fpr_below_band`** — variant_recall == 1.000 AND 0 < peer_fpr ≤ PARTIAL_FPR_BAND_HI. *Soft PASS, not paper-grade.*
8. **`PASS_universal_perfect_recall_zero_fpr`** — variant_recall == 1.000 AND peer_fpr == 0.000. **F-row candidate** (label TBD by `RANKED_FINDINGS.md` rules; reservation requested below).

### 4.1 — F-row reservation policy

If branch 8 fires AND all four audit hooks pass, the result will be filed as **F59** (next available F-row after F58 Φ_master). The F-row is provisional until the doc-update step (RANKED + PAPER + REGISTRY) lands. If branches 5/6 fire, the result will be filed as **FN12** (failed-null pre-registration, Category K of `RETRACTIONS_REGISTRY.md`); H60 stays a hypothesis row, never gets an F-row.

---

## 5. Honest scope statement

**Pre-committed before observing the receipt:** A `PASS_universal_perfect_recall_zero_fpr` outcome would establish:

- The **first cross-tradition POSITIVE F-detector finding** in the project. F55 was Quran-internal (114 surahs); a Hebrew Psalm 78 PASS adds **one** independent cross-language data point in a different alphabet.
- **F55 is alphabet-agnostic by construction**, but the *peer-side* FPR claim was previously only tested on Arabic non-Quran corpora. The Hebrew test fixes the empirical FPR claim for one chapter in one new language family.

It would NOT establish:

- That F55 generalises to "all canonical scriptures" — the Greek NT, Sanskrit Vedic, Pali, Avestan tests are separate hash-locked PREREGs. Each is a distinct empirical claim.
- That the *Quran-distinctiveness* result transfers to Hebrew — F55 is a *detector* (recall + FPR receipts), not a Quran-distinctiveness claim. A Hebrew PASS confirms the detector mechanism is universal; it does not say anything about Hebrew-vs-Quran ranking.
- That F53's failure on Hebrew (FN11) is "rescued" — F53 and F55 are different detector classes; F55 PASS does not un-retract any F53 retraction.

**Pre-committed before observing the receipt:** A FAIL outcome (any of branches 4–6) is publishable as **FN12** (failed-null pre-registration). It would tell us either (i) the F55 theorem implementation has a bug (branch 4 — would be alarming), (ii) Hebrew has bigram-coincidence substitutions where Δ = 0 unexpectedly often (branch 5), or (iii) some Hebrew narrative chapter has anomalously low Δ < τ vs Psalm 78 (branch 6 — extremely unlikely given pre-stage min = 680.5).

---

## 6. Hash-lock procedure

This file's SHA-256 hash is computed at seal time and stored at `experiments/exp105_F55_psalm78_bigram/PREREG_HASH.txt`. The accompanying `run.py` reads its expected hash from a constant `_PREREG_EXPECTED_HASH` literal; `run.py` refuses to execute if the in-file PREREG hash drifts from the locked expected value.

**Seal hash**: see `PREREG_HASH.txt`.

---

## 7. Receipt schema (locked)

```
{
  "experiment": "exp105_F55_psalm78_bigram",
  "hypothesis_id": "H60",
  "verdict": "<one of branch 1-8 above>",
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
      "n_chapters_total":     <int>,
      "target_book":          "תהלים",
      "target_chapter":       "עח",
      "target_n_verses":      <int>,
      "target_n_letters_22":  <int>,
      "target_n_chars_with_spaces": <int>,
      "peer_pool_size":       <int>,
      "peer_length_window":   [<int>, <int>],
      "max_variant_delta":    <float>,
      "min_peer_delta":       <float>,
      "n_variants_total":     <int>,
      "n_variants_fired":     <int>,
      "n_peer_pairs_total":   <int>,
      "n_peer_pairs_fired":   <int>,
      "variant_recall":       <float>,
      "peer_fpr":             <float>,
      "five_closest_peers":   [...],
      "sentinel_determinism": "OK" | "<error>"
    },
    "warnings": [...],
    "errors":   [...]
  },
  "pre_stage_diagnostic_receipt":
      "results/auxiliary/_psalm78_bigram_sizing.json"
}
```

---

## 8. Out of scope

- Greek NT, Sanskrit Vedic, Pali Canon, Avestan Yasna chapters — separate PREREGs each.
- Insertion or deletion forgeries (F55 V1 scope is substitution-only; theorem extends naturally to insertions/deletions but empirical test would need a fresh PREREG).
- Multi-letter forgeries (V2+ scope).
- Any τ != 2.0 (different detector class; not in F55 family).
- Any calibration step (the *whole point* is no calibration; we are testing precisely the off-shelf, un-tuned detector).
- LLM-generated forgeries (separate Phase-5+ PREREG).

---

## 9. Cross-references

- F55 detector definition: `experiments/exp95j_bigram_shift_universal/PREREG.md`
- F55 theorem 3.2: `experiments/exp95j_bigram_shift_universal/PREREG.md` §3.2
- Hebrew normaliser: `experiments/exp104_F53_tanakh_pilot/run.py::_hebrew_skeleton_with_spaces`
- Peer pool definition (locked): `experiments/exp104_F53_tanakh_pilot/run.py` constants `LENGTH_MATCH_FRAC`, `PEER_BOOKS`, `TARGET_N_PEERS`, `PEER_AUDIT_FLOOR`
- Sibling H59c (NCD-consensus, FN11): `experiments/exp104c_F53_psalm78/PREREG.md`
- Pre-stage diagnostic receipt: `results/auxiliary/_psalm78_bigram_sizing.json`
- Failure-mode contrast (F53 vs F55): `docs/PAPER.md` §4.43.2 (F55 universal detector) vs §4.42 (F53 Q:100 closure) vs §4.47.5 (cross-tradition pilot chain)
