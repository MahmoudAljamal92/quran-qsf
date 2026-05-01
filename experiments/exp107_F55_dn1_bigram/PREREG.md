# exp107_F55_dn1_bigram — PREREG

**Hypothesis ID**: H62
**Parent**: H43 (F55 universal symbolic forgery detector, `exp95j_bigram_shift_universal`, `PASS_universal_perfect_recall_zero_fpr`).
**Siblings**:
- H60 (`exp105_F55_psalm78_bigram`, `PASS_universal_perfect_recall_zero_fpr` / F59) — Hebrew Tanakh Psalm 78, second cross-tradition F55 pilot.
- H61 (`exp106_F55_mark1_bigram`, `PASS_universal_perfect_recall_zero_fpr` / F60) — Greek NT Mark 1, third cross-tradition F55 pilot.
**Patch**: v7.9-cand patch H V3.5 (cross-tradition F55 pilot — Pāli Tipiṭaka, Indo-Aryan / Indic).
**Filed**: 2026-04-29 (UTC+02 night).

---

## 1. Hypothesis statement (locked)

Under the **bigram-shift detector with frozen analytic-bound τ = 2.0** (the F55 detector class, locked by the analytic theorem in `experiments/exp95j_bigram_shift_universal/PREREG.md` §3.2), single-Pāli-letter substitution forgeries on **Dīgha Nikāya 1 (DN 1, the Brahmajāla Sutta)** of the Pāli Tipiṭaka (SuttaCentral root-pli-ms Bilara edition; Mahāsaṅgīti ed., CC0-1.0) are detected at **per-variant recall = 1.000** with **per-(canon, peer)-pair FPR = 0.000** against the full DN+MN peer pool of all 185 other suttas (no length matching, byte-exact match to the Quran-side `exp95j` and Greek-side `exp106` protocol), replicating the F55 result on Quran V1, Hebrew Psalm 78 (F59), and Greek NT Mark 1 (F60) in a fourth independent tradition: **Indo-Aryan / Indic language family, Roman-IAST-transliterated Pāli, ~5th-century BCE composition / 1st-century BCE editorial close**.

This is the **fifth Phase-3 cross-tradition pilot** (after FN10 + FN11 closed off-shelf F53 K=2 cross-tradition under locked Hebrew calibration; F59 established F55 cross-tradition success on Hebrew Psalm 78; F60 extended F55 to Greek NT Mark 1). H62 tests F55 in a tradition that is:

- **Different language family** from all three prior runs: Pāli is **Indo-Aryan** (Indic branch of Indo-European; sister to Sanskrit), distinct from Central Semitic (Quran), Northwest Semitic (Hebrew), and Hellenic Indo-European (Greek). Pāli is the closest relative of Sanskrit but predates the Vedic literary canon's Prakrit shift and is a "Middle Indo-Aryan" tongue with retroflex consonants (ṭ, ḍ, ṇ, ḷ) and a niggahīta nasal (ṁ) absent in Greek/Latin/Hebrew/Arabic.
- **Different alphabet**: 31 lowercase IAST/PTS Roman-Pāli letters (8 vowels + 22 consonants + 1 niggahīta) vs 24 Greek vs 28 Arabic vs 22 Hebrew. Pāli is the largest alphabet of the four.
- **Different writing system**: SuttaCentral edition is **Roman-IAST transliterated** (left-to-right, vowels written as full letters, retroflex/dental distinction encoded by combining diacritics). The native script is variously Sinhalese, Burmese, Thai Khom, Khmer, or Devanagari depending on regional manuscript tradition; SuttaCentral standardises on IAST Roman as the editorial layer. The detector consumes the IAST Roman byte sequence, so this run tests F55 on a Brahmi-derived alphabet *via* Romanisation; the underlying phonological inventory is Indic.
- **Different historical period** from all prior runs: Pāli Canon's oral composition layer dates to ~5th-century BCE (Buddha's lifetime ~563–483 BCE); editorial close at the Fourth Buddhist Council (Sri Lanka, ~1st century BCE) under Aluvihāra. Vs ~1st-century CE Koine Greek (Mark), ~7th-century CE Classical Arabic (Quran), ~1000 BCE editorial Biblical Hebrew (Psalms).
- **Different religious / cultural tradition**: Theravāda Buddhism (non-theistic, anātman doctrine) vs Christianity vs Islam vs Judaism. Different mythological corpus, different soteriology, different liturgical context.

A H62 PASS would establish F55 generalisation across **4 language families** and **2.5 millennia** with **zero parameter change** between the four runs. Combined with F59 (Hebrew) and F60 (Greek), this would lift F55 from "validated across 3 Mediterranean-rim language families" to "validated across the Mediterranean rim AND South Asia, with one Indo-European Hellenic, one Indo-Aryan Indic, two Semitic, no language-family overlap pairs". This is the strongest cross-tradition replication pattern available to the project at chapter scope short of a 6+ tradition expansion (Sanskrit Vedic, Avestan Yasna, Classical Chinese Daodejing, etc.).

**Caveat (pre-committed)**: DN 1 is ~17× larger than Mark 1 (60,542 letters vs 3,530) and ~25× larger than Psalm 78 (60,542 vs 2,384). Because the bigram-shift Δ scales linearly with raw letter counts (raw L1 / 2), the empirical safety margin (peer_min / τ) on Pāli will be much larger than on Greek/Hebrew/Arabic *as a chapter-length artefact, not as evidence of stronger Pāli structure*. The F55 PASS / FAIL question is unaffected (the theorem floor is τ = 2.0 regardless of canon length), but post-hoc safety-margin comparisons across the four traditions must be normalised by `n_letters` to be meaningful. This caveat is logged here pre-seal and will be carried into PAPER §4.47.10.

---

## 2. Frozen constants (locked at PREREG seal time)

```
SEED                            = 42
TAU_HIGH                        = 2.0          # F55 analytic-bound, no calibration
AUDIT_TOL                       = 1e-9         # numeric float-compare tolerance
RECALL_FLOOR                    = 1.000        # per-variant; F55 paper-grade gate
FPR_CEIL                        = 0.000        # per-(canon, peer)-pair; F55 paper-grade gate
PARTIAL_FPR_BAND_HI             = 0.05         # for partial-PASS branch
TARGET_SUTTA_ID                 = "dn1"        # Brahmajāla Sutta (canonical Pāli Canon opener)
TARGET_COLLECTION               = "dn"         # Dīgha Nikāya
TARGET_MIN_LETTERS              = 1000         # locked from exp104/105/106 chapter-length floor
TARGET_MIN_SEGMENTS             = 10           # Bilara segments analogous to Greek/Hebrew verses
PEER_POOL_STRATEGY              = "all_other_dn_mn_suttas_no_length_matching"
PEER_AUDIT_FLOOR                = 100          # min peer pool size (locked from exp104c)
PALI_ALPHABET_31                = "aāiīuūeokgṅcjñṭḍṇtdnpbmyrlḷvshṁ"
                                #  8 vowels + 22 cons + 1 niggahīta = 31 (verified by sentinel)
NIGGAHITA_FOLD_TABLE            = { "ṃ" (U+1E43): "ṁ" (U+1E41) }
NORMALISER_SENTINEL_INPUT       = "Evaṁ me sutaṁ"
NORMALISER_SENTINEL_EXPECTED    = "evaṁmesutaṁ"
```

The detector itself is a single-line decision: variant fires iff `0 < Δ_bigram(canon, variant) ≤ TAU_HIGH`; peer pair fires iff `0 < Δ_bigram(canon, peer) ≤ TAU_HIGH`.

`Δ_bigram(a, b) := ½ · Σ_k |count_a[k] − count_b[k]|` over the union of bigram keys k, where bigrams are *raw* (unnormalised) counts of consecutive 2-character substrings of the Pāli skeleton (whitelist-only, drop everything outside the 31-letter alphabet; matches exp95j Arabic-side, exp105 Hebrew-side, and exp106 Greek-side conventions).

The Pāli normaliser is a new locked function `experiments/exp107_F55_dn1_bigram/run.py::_normalise_pali` (sentinel-verified; identical implementation as `scripts/_dn1_bigram_sizing.py`):

1. Unicode NFC composition (canonical-composed; "ā" stays as one codepoint U+0101, not "a" + U+0304).
2. `casefold()` to lowercase.
3. Niggahīta fold: replace `ṃ` (U+1E43, m + dot below) → `ṁ` (U+1E41, m + dot above). Both denote anusvāra in Pāli; SuttaCentral's Bilara edition uses U+1E41 throughout so we fold to that form. Without this fold, identical Pāli words written in different editions would produce different bigrams.
4. Whitelist only the 31 IAST Pāli letters; drop everything else (whitespace, punctuation, em-dashes, digits, sutta-reference-IDs, etc.).

The Pāli loader is a new locked function `experiments/exp107_F55_dn1_bigram/run.py::_load_pali_suttas` (Bilara JSON → list-of-dicts, one per sutta, scanning `data/corpora/pi/dn/` and `data/corpora/pi/mn/` for `*_root-pli-ms.json` files; concatenates `data.values()` in insertion order to produce the per-sutta raw text stream).

---

## 3. Frozen protocol (locked)

### 3.1 — Variant enumeration

For DN 1's normalised skeleton `S` of length n_letters: enumerate **all n_letters × 30 single-Pāli-letter substitutions** (every position × every other-of-31 substitute). Predicted variant count: **60,542 × 30 = 1,816,260** (verified by pre-stage diagnostic).

### 3.2 — Variant scoring (analytic O(1) per call)

Use the same analytic-bound implementation as `experiments/exp95j_bigram_shift_universal/run.py::variant_delta_analytic`: only the (up to 4) bigrams touching the substituted position change; compute the L1 difference of those 4 bigrams and divide by 2.

A variant *fires* iff `0 < Δ ≤ TAU_HIGH`.

### 3.3 — Peer scoring (exact)

For each peer sutta `p` in the locked pool (all 185 DN+MN suttas except DN 1), compute `Δ_bigram(canon, p)` from the full bigram counters. A peer pair *fires* iff `0 < Δ ≤ TAU_HIGH`.

### 3.4 — Audit hooks (must all pass)

- **A1 — Variant theorem**: `max(variant_Δ) ≤ TAU_HIGH + AUDIT_TOL = 2.0 + 1e-9`. Theoretical certainty per the F55 PREREG theorem; this hook validates the implementation on the 31-letter Pāli alphabet.
- **A2 — Peer pool size**: `n_peers ≥ PEER_AUDIT_FLOOR = 100`. Pre-stage confirms 185 ≥ 100.
- **A3 — Target chapter floors**: `n_letters ≥ TARGET_MIN_LETTERS = 1,000` and `n_segments ≥ TARGET_MIN_SEGMENTS = 10`. Pre-stage confirms DN 1 has 60,542 letters / 662 segments.
- **A4 — Sentinel determinism**: re-running the analytic variant scorer on a random sample of 100 (variant, peer) pairs must produce byte-identical Δ values across two passes. Validates loader + normaliser determinism.
- **A5 — Normaliser sentinel**: `_normalise_pali("Evaṁ me sutaṁ") == "evaṁmesutaṁ"`. Validates the locked normaliser.
- **A6 — Alphabet coverage**: the target sutta's skeleton must use ≥ 25 of the 31 alphabet letters (rejects pathological underused-alphabet inputs). Pre-stage confirms DN 1 uses all 31/31.

### 3.5 — Pre-stage diagnostic (already executed, attached as evidence)

`scripts/_dn1_bigram_sizing.py` (filed under `results/auxiliary/_dn1_bigram_sizing.json`, run 2026-04-29 night) executed the variant theorem replication and the peer FPR-floor check **before** this PREREG was sealed:

| Probe | Result |
|---|---|
| Variant audit (N=1,000 sampled) | min Δ = 1.000, mean = 1.997, max = 2.000, n_above_τ = 0 |
| Peer audit (n=185 full pool) | min Δ = **9,867** (DN 2, Sāmaññaphala), p5 = 16,055, median = 24,582, max = 29,870 |
| Safety margin | peer_min / τ = **4,933.5×** (compare Greek 267.8× / Hebrew 340.2× / Arabic 36.8×) |
| Length-normalised safety margin | (peer_min / n_letters) / τ = (9,867 / 60,542) / 2.0 = **0.0815 per-letter** vs Greek 0.0758 / Hebrew 0.143 / Arabic 0.014 |

**Pre-stage verdict**: PROCEED_TO_PREREG. The analytic theorem holds on the 31-letter Pāli alphabet (max = 2.0 with 0 above-τ variants in a 1,000-sample audit) and the peer-side Δ distribution sits five orders of magnitude above τ. The 5 closest peers to DN 1 are all from Dīgha Nikāya (DN 2, DN 33, DN 34, DN 23, DN 24) — same-collection same-author clustering, exactly as one would expect for the long-discourse nikāya. The headline 4,933× safety margin is largely a chapter-length artefact (DN 1 is ~17× longer than Mark 1); the length-normalised "margin per letter" is 0.082 / letter, comparable to Greek (0.076) and somewhat below Hebrew (0.143), and well above Arabic's 0.014. This is **published with the PREREG** so that the post-run report can never be accused of cherry-picking a flattering metric.

---

## 4. Verdict ladder (pre-registered, branches mutually exclusive)

The ladder is checked in order; the first matching branch fires.

1. **`BLOCKED_corpus_missing`** — `data/corpora/pi/dn/dn1_root-pli-ms.json` absent or unreadable. *No claim made.*
2. **`BLOCKED_dn1_too_short`** — `n_letters < TARGET_MIN_LETTERS` OR `n_segments < TARGET_MIN_SEGMENTS`. *Should be unreachable; locked DN 1 has 60,542 letters / 662 segments.*
3. **`FAIL_audit_peer_pool_size`** — n_peers < PEER_AUDIT_FLOOR. *Pre-stage confirms 185 ≥ 100; should be unreachable.*
4. **`FAIL_audit_normaliser_sentinel`** — A5 sentinel does not match. *Validates normaliser; would indicate code drift.*
5. **`FAIL_audit_alphabet_coverage`** — A6 violation: target uses < 25 of 31 alphabet letters. *Pre-stage confirms 31/31; should be unreachable.*
6. **`FAIL_audit_theorem`** — A1 violation: at least one variant has Δ > 2.0 + 1e-9. *Mathematically impossible per F55 theorem; would indicate implementation bug.*
7. **`FAIL_recall_below_floor`** — variant_recall < 1.000. *Possible iff some variants land at Δ = 0 (bigram-coincidence substitutions); pre-stage saw 0/1,000.*
8. **`FAIL_fpr_above_ceiling`** — peer_fpr > 0.000. *Pre-stage min Δ = 9,867; would require a Pāli sutta to be near-bigram-identical to DN 1, which is statistically impossible at 60K+ letters.*
9. **`PARTIAL_fpr_below_band`** — variant_recall == 1.000 AND 0 < peer_fpr ≤ PARTIAL_FPR_BAND_HI. *Soft PASS, not paper-grade.*
10. **`PASS_universal_perfect_recall_zero_fpr`** — variant_recall == 1.000 AND peer_fpr == 0.000. **F-row candidate** (label TBD by `RANKED_FINDINGS.md` rules; reservation requested below).

### 4.1 — F-row reservation policy

If branch 10 fires AND all six audit hooks pass, the result will be filed as **F61** (next available F-row after F60 cross-tradition Greek). The F-row is provisional until the doc-update step (RANKED + PAPER + REGISTRY) lands. If branches 6/7/8 fire, the result will be filed as **FN12** (failed-null pre-registration, Category K of `RETRACTIONS_REGISTRY.md`); H62 stays a hypothesis row, never gets an F-row.

---

## 5. Honest scope statement

**Pre-committed before observing the receipt:** A `PASS_universal_perfect_recall_zero_fpr` outcome would establish:

- The **third** cross-tradition POSITIVE F-detector data point (F59 was the first, F60 was the second; H62 PASS would be the third).
- F55 generalises across **4 language families** at chapter scope: Central Semitic (Quran V1, exp95j), Northwest Semitic (Hebrew Psalm 78, exp105 / F59), Hellenic Indo-European (Greek NT Mark 1, exp106 / F60), Indo-Aryan / Indic (Pāli DN 1, this run / candidate F61).
- F55's discriminative power is plausibly **alphabet-agnostic and language-family-agnostic** for any substitution-cipher attack model where the alphabet has ≥ ~20 distinct letters, the chapter has ≥ ~1,000 letters, and there are ≥ 100 peer chapters in the corpus. The four-corpus replication crosses two non-overlapping macro-family pairs (Semitic, Indo-European) and adds an Indic data point that breaks the "all Mediterranean" framing of the prior three runs.

It would NOT establish:

- That F55 generalises to non-Brahmi-script-derived, non-Indo-European, non-Semitic traditions (Avestan Yasna in Pahlavi script, Classical Chinese Daodejing in Han characters, Sanskrit Vedic in native Devanagari are separate hash-locked PREREGs).
- That F55 generalises when the canonical text is in its native (non-Roman) script (the Pāli IAST Romanisation is the SuttaCentral editorial choice; running on native Sinhalese, Burmese, Thai Khom, or Khmer Pāli would test the script-of-encoding axis separately).
- That F55 generalises to chapter-shorter-than-1,000-letters traditions or peer-pool-smaller-than-100 traditions (separate amendment regime).
- That the cross-tradition F55 result is "Quran-distinctive" — F55 is a **detector** receipt (recall + FPR), NOT a Quran-distinctiveness claim. F61 confirms detector-mechanism universality; says nothing about Quran-vs-other ranking.
- That F53's failure on Hebrew (FN11) is "rescued" — different detector class entirely.
- That Pāli has a "stronger" cross-tradition fingerprint than Hebrew or Greek — the apparent 4,933× safety margin is a chapter-length artefact (DN 1 is ~17× longer than Mark 1); length-normalised, the per-letter margin is comparable to Greek/Hebrew.

**Pre-committed before observing the receipt:** A FAIL outcome (any of branches 6–8) is publishable as **FN12**. A theorem-violation (branch 6) would be alarming and would necessitate investigating the Pāli normaliser's NFC + casefold + niggahīta-fold pipeline. A recall-below-floor (branch 7) would mean Pāli has bigram-coincidence substitutions where Δ = 0 (mechanistically possible but unobserved in pre-stage). An FPR-above-ceiling (branch 8) would mean some DN/MN sutta is near-bigram-identical to DN 1, contradicting the 9,867 min observation.

---

## 6. Hash-lock procedure

This file's SHA-256 hash is computed at seal time and stored at `experiments/exp107_F55_dn1_bigram/PREREG_HASH.txt`. The accompanying `run.py` reads its expected hash from a constant `_PREREG_EXPECTED_HASH` literal; `run.py` refuses to execute if the in-file PREREG hash drifts from the locked expected value.

**Seal hash**: see `PREREG_HASH.txt`.

---

## 7. Receipt schema (locked)

```
{
  "experiment": "exp107_F55_dn1_bigram",
  "hypothesis_id": "H62",
  "verdict": "<one of branch 1-10 above>",
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
      "n_suttas_total":          <int>,
      "n_dn":                    <int>,
      "n_mn":                    <int>,
      "target_sutta_id":         "dn1",
      "target_collection":       "dn",
      "target_n_segments":       <int>,
      "target_n_letters":        <int>,
      "target_n_distinct_chars": <int>,
      "peer_pool_size":          <int>,
      "peer_pool_strategy":      "all_other_dn_mn_suttas_no_length_matching",
      "max_variant_delta":       <float>,
      "min_peer_delta":          <float>,
      "n_variants_total":        <int>,
      "n_variants_fired":        <int>,
      "n_peer_pairs_total":      <int>,
      "n_peer_pairs_fired":      <int>,
      "variant_recall":          <float>,
      "peer_fpr":                <float>,
      "five_closest_peers":      [...],
      "sentinel_determinism":    "OK" | "<error>",
      "normaliser_sentinel":     "OK" | "<error>",
      "alphabet_coverage_ok":    <bool>
    },
    "warnings": [...],
    "errors":   [...]
  },
  "pre_stage_diagnostic_receipt":
      "results/auxiliary/_dn1_bigram_sizing.json"
}
```

---

## 8. Out of scope

- Avestan Yasna, Classical Chinese Daodejing, Sanskrit Vedic, native-script (Sinhalese / Burmese / Thai / Khmer / Devanagari) Pāli — separate PREREGs each.
- Insertion or deletion forgeries (F55 V1 scope is substitution-only).
- Multi-letter forgeries (V2+ scope).
- Any τ != 2.0 (different detector class; not in F55 family).
- Any calibration step (the *whole point* is no calibration).
- Length-matched peer pool variants (this run uses no length matching by design, matching exp95j / exp106).
- Pāli vs Sanskrit / Pāli vs other-Buddhist-canon comparison (separate study).
- LLM-generated forgeries (separate Phase-5+ PREREG).

---

## 9. Cross-references

- F55 detector definition: `experiments/exp95j_bigram_shift_universal/PREREG.md`
- F55 theorem 3.2: `experiments/exp95j_bigram_shift_universal/PREREG.md` §3.2
- Sibling H60 (F55 → Hebrew, F59): `experiments/exp105_F55_psalm78_bigram/PREREG.md`
- Sibling H61 (F55 → Greek, F60): `experiments/exp106_F55_mark1_bigram/PREREG.md`
- Pre-stage diagnostic receipt: `results/auxiliary/_dn1_bigram_sizing.json`
- Pāli corpus manifest: `data/corpora/pi/manifest.json` (SuttaCentral Bilara root-pli-ms; CC0-1.0)
- Failure-mode contrast: `docs/PAPER.md` §4.47.5 (FN11 F53 Hebrew calibration-collapse), §4.47.8 (F59 F55 Hebrew PASS), §4.47.9 (F60 F55 Greek PASS)
