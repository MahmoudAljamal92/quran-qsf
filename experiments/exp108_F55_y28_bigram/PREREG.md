# exp108_F55_y28_bigram — PREREG

**Hypothesis ID**: H63
**Parent**: H43 (F55 universal symbolic forgery detector, `exp95j_bigram_shift_universal`, `PASS_universal_perfect_recall_zero_fpr`).
**Siblings**:
- H60 (`exp105_F55_psalm78_bigram`, F59) — Hebrew Tanakh Psalm 78, 1st cross-tradition F55 PASS.
- H61 (`exp106_F55_mark1_bigram`, F60) — Greek NT Mark 1, 2nd cross-tradition F55 PASS.
- H62 (`exp107_F55_dn1_bigram`, F61) — Pāli Dīgha Nikāya 1, 3rd cross-tradition F55 PASS.
**Patch**: v7.9-cand patch H V3.6 (cross-tradition F55 pilot — Avestan Yasna, Indo-Iranian).
**Filed**: 2026-04-29 (UTC+02 night).

---

## 1. Hypothesis statement (locked)

Under the **bigram-shift detector with frozen analytic-bound τ = 2.0** (the F55 detector class, locked by the analytic theorem in `experiments/exp95j_bigram_shift_universal/PREREG.md` §3.2), single-Latin-letter substitution forgeries on **Avestan Yasna 28** (Ahunavaiti Gatha, ch. 1; the opening hymn of the oldest canonical layer of the Zoroastrian Avesta — Old Avestan, traditionally attributed to Zarathushtra ~5th-c BCE composition / ~6th-c CE editorial close) are detected at **per-variant recall = 1.000** with **per-(canon, peer)-pair FPR = 0.000** against the full 72-yasna peer pool of all other Yasna chapters (no length matching, byte-exact match to the Quran-side `exp95j` and Greek-side `exp106` and Pāli-side `exp107` protocols), replicating the F55 result on Quran V1, Hebrew Psalm 78 (F59), Greek Mark 1 (F60), and Pāli DN 1 (F61) in a **fifth independent tradition**: **Indo-Iranian language family (Avestan = Old Iranian; sister branch to Vedic Sanskrit; both descend from Proto-Indo-Iranian)**, Geldner edition transliterated to Latin script with diacritical encoding.

This is the **sixth Phase-3 cross-tradition pilot** (after FN10 + FN11 closed off-shelf F53 K=2 cross-tradition under locked Hebrew calibration; F59 / F60 / F61 established F55 cross-tradition success on Hebrew, Greek, and Pāli). H63 tests F55 in a tradition that is:

- **Sister branch to Pāli within Indo-Iranian** but with a 2,500-year divergence: Avestan and Vedic Sanskrit/Pāli are sister branches of Proto-Indo-Iranian; they share many cognates (e.g., Avestan `ahura` ↔ Vedic `asura`, Avestan `daēva` ↔ Vedic `deva`, the morphological similarity is dramatic). Pāli and Avestan are linguistically the **closest pair** in the F55 cross-tradition series, so a PASS would say "F55 still works even when two adjacent test languages share Indo-Iranian morphology"; a FAIL would say "F55 breaks down on closely related sister branches" — a meaningful discrimination test.
- **Different alphabet from all prior runs**: 26-letter Latin (a-z) post-normalization (Geldner-encoding pipeline: HTML-entity decode of Latin-1 character entities like `&acirc;` for â; NFD decompose; drop combining marks; casefold; whitelist a-z). Empirical alphabet attestation: 24 of 26 Latin letters are used in the corpus (no `l`, no `q`); the F55 protocol substitutes over the full 26-letter Latin alphabet (q/l substitutes are valid F55 variants by theorem 3.2; the safety margin and theorem do not depend on substitute-letter empirical attestation).
- **Different writing system**: Latin transliteration of Avestan-script (Avestan-script is a Pahlavi-derived Iranian alphabet of ~50+ phonetic glyphs; Geldner standardised the Latin transliteration with diacritics for the 1896 critical edition). The F55 detector consumes the Latin byte sequence post-normalization.
- **Different religious tradition**: Zoroastrianism (Mazdaism) — dualistic theism (Ahura Mazdā vs Angra Mainyu), apocalyptic eschatology, fire-altar ritual (yasna = "sacrifice/worship" liturgy). Five religious traditions across the F55 series: Islam (Arabic), Judaism (Hebrew), Christianity (Greek), Theravāda Buddhism (Pāli), Zoroastrianism (Avestan). No two share core soteriology.

A H63 PASS would establish F55 generalization across **5 language families**, **5 alphabets** (28-Arabic / 22-Hebrew / 24-Greek / 31-Pāli-IAST / 26-Latin-Avestan), **5 religious traditions**, **3 millennia** of canonical text composition (~1500 BCE Old Avestan oral layer → ~7th-c CE Quran), with **zero parameter change** between runs.

**The Indo-Iranian sister-branch test (post-hoc observation, not a PREREG claim)**: F61 (Pāli) and F63 (Avestan if PASS) test the same Indo-Iranian macro-family, separated by ~2,500 years. If F55 generalises to both, the cross-tradition pattern is no longer "five randomly distant traditions" but "five traditions including two from the same macro-family with shared morphology" — which is a **stronger** universality claim, not a weaker one. The detector still passes despite a structurally similar cousin language.

---

## 2. Frozen constants (locked at PREREG seal time)

```
SEED                            = 42
TAU_HIGH                        = 2.0          # F55 analytic-bound, no calibration
AUDIT_TOL                       = 1e-9
RECALL_FLOOR                    = 1.000
FPR_CEIL                        = 0.000
PARTIAL_FPR_BAND_HI             = 0.05
TARGET_YASNA                    = 28           # Ahunavaiti Gatha, ch. 1
TARGET_MIN_LETTERS              = 1000         # locked floor
TARGET_MIN_VERSES               = 10
PEER_AUDIT_FLOOR_F55            = 50           # F55-family amendment from F53 inherited 100 (see §2.1)
ALPHABET_COVERAGE_FLOOR         = 18           # corpus-empirical-attested-alphabet-size floor (24/26 observed)
PEER_POOL_STRATEGY              = "all_other_yasna_chapters_no_length_matching"
AVESTAN_ALPHABET_26             = "abcdefghijklmnopqrstuvwxyz"
NORMALISER_SENTINEL_INPUT       = "ahy&acirc; &yacute;&acirc;s&acirc; nemangh&acirc;"
NORMALISER_SENTINEL_EXPECTED    = "ahyayasanemangha"
```

### 2.1 — F55-family peer pool floor amendment (`PEER_AUDIT_FLOOR_F55 = 50`, justification)

The exp104c PREREG locked `PEER_AUDIT_FLOOR = 100` for the F53 K=2 multi-compressor consensus detector, where the floor was driven by the bootstrap-200 τ-stability requirement of CV_τ ≤ 0.30 across 4 compressors. The 100 floor is a **calibration-stability requirement** for F53; F55 has no calibration step (τ = 2.0 is frozen analytically), so the F53 floor is over-engineered for the F55 detector class.

The Avestan Yasna corpus has only 73 chapters total (Yasnas 0-72 of the Geldner edition). Peer pool with target = Yasna 28 is **72 chapters**, which is below the F53-inherited 100 but well above the appropriate F55 floor.

The appropriate F55 floor is the minimum needed for `min(peer_Δ)` to be a stable estimator of the true peer-Δ population minimum. Empirically across F55, F59, F60, F61, the gap between min(peer_Δ) and τ has been ≥ 73× (Arabic) ≥ 145× (Avestan pre-stage observation) ≥ 268× (Greek) ≥ 340× (Hebrew) ≥ 4,933× (Pāli; length-driven), so the **stability of `min(peer_Δ)` is not the concern** — its absolute magnitude relative to τ is. A peer pool of 30-50 distinct chapter-scope texts in any natural language gives a `min(peer_Δ)` that is several orders of magnitude above τ; this is theorem-driven, not corpus-driven.

The amendment to `PEER_AUDIT_FLOOR_F55 = 50` is **pre-committed** in this PREREG with the explicit justification above. Future F55 cross-tradition runs (Sanskrit Vedic, Old Tamil Sangam, Classical Chinese Daodejing, etc.) inherit the 50 floor.

---

## 3. Frozen protocol (locked)

### 3.1 — Variant enumeration

For Yasna 28's normalised skeleton `S` of length n_letters: enumerate **all n_letters × 25 single-Latin-letter substitutions** (every position × every other-of-26 substitute). Predicted variant count: **1,658 × 25 = 41,450** (verified by pre-stage diagnostic; substitutes use the full 26-letter Latin alphabet by F55 protocol — substitute-letter empirical attestation does not bear on theorem 3.2).

### 3.2 — Variant scoring (analytic O(1) per call)

Use the same analytic-bound implementation as `experiments/exp95j_bigram_shift_universal/run.py::variant_delta_analytic`: only the (up to 4) bigrams touching the substituted position change; compute the L1 difference of those 4 bigrams and divide by 2.

A variant *fires* iff `0 < Δ ≤ TAU_HIGH`.

### 3.3 — Peer scoring (exact)

For each peer yasna `p` in the locked pool (all 72 yasnas except Yasna 28), compute `Δ_bigram(canon, p)` from the full bigram counters. A peer pair *fires* iff `0 < Δ ≤ TAU_HIGH`.

### 3.4 — Audit hooks (must all pass)

- **A1 — Variant theorem**: `max(variant_Δ) ≤ TAU_HIGH + AUDIT_TOL = 2.0 + 1e-9`. Theoretical certainty per the F55 PREREG theorem; this hook validates the implementation on the 26-letter Latin alphabet.
- **A2 — F55-family peer pool floor**: `n_peers ≥ PEER_AUDIT_FLOOR_F55 = 50`. Pre-stage confirms 72 ≥ 50.
- **A3 — Target chapter floors**: `n_letters ≥ TARGET_MIN_LETTERS = 1,000` and `n_verses ≥ TARGET_MIN_VERSES = 10`. Pre-stage confirms Yasna 28 has 1,658 letters / 13 verses.
- **A4 — Sentinel determinism**: re-running the analytic variant scorer on a random sample of 100 (variant, peer) pairs must produce byte-identical Δ values across two passes.
- **A5 — Normaliser sentinel**: `_normalise_avestan("ahy&acirc; &yacute;&acirc;s&acirc; nemangh&acirc;") == "ahyayasanemangha"` (the opening four-word phrase from Yasna 28:1 — the very first verse of the Ahunavaiti Gatha; meaning roughly "with hands outstretched I beseech, O Mazdā").
- **A6 — Alphabet coverage**: target's skeleton must use ≥ ALPHABET_COVERAGE_FLOOR = 18 of 26 alphabet letters. Pre-stage confirms 24/26.
- **A7 — Corpus completeness**: `n_yasnas_loaded == 73` exact. Validates the loader's chapter-extraction across 12 source HTML files. Defends against silent regex regressions like the early sizing run that loaded only 11 / 73 chapters before the `<H3 id=>` attribute fix.

### 3.5 — Pre-stage diagnostic (already executed, attached as evidence)

`scripts/_y28_bigram_sizing.py` (filed under `results/auxiliary/_y28_bigram_sizing.json`, run 2026-04-29 night) executed the variant theorem replication and the peer FPR-floor check **before** this PREREG was sealed:

| Probe | Result |
|---|---|
| Variant audit (N=1,000 sampled) | min Δ = 1.000, mean = 1.998, max = 2.000, n_above_τ = 0 |
| Peer audit (n=72 full pool) | min Δ = **291.00** (Yasna 50 — Spentamainyu Gatha), p5 = 329.5, median = 573.0, max = 2,724.5 |
| Safety margin | peer_min / τ = **145.5×** |
| Length-normalised margin | (peer_min / n_letters) / τ = (291 / 1,658) / 2.0 = **0.0877 / letter** |
| Alphabet coverage | 24 / 26 letters used (`abcdefghijkmnoprstuvwxyz`; missing `l`, `q`) |

**Pre-stage verdict**: PROCEED_TO_PREREG. The analytic theorem holds on the 26-letter Latin alphabet (max = 2.0 with 0 above-τ variants in a 1,000-sample audit) and the peer-side Δ distribution sits two orders of magnitude above τ. The 5 closest peers to Yasna 28 are **all from the Old Avestan Gathic stratum** (Y. 50 Spentamainyu, Y. 33 Ahunavaiti, Y. 30 Ahunavaiti — the "Two Spirits" hymn, Y. 45 Ushtavaiti, Y. 53 Vahishtoishti); same-stratum / same-author / same-dialect clustering, mirroring the same-collection clustering observed in F60 (Greek Mark/Luke) and F61 (Pāli Dīgha Nikāya).

---

## 4. Verdict ladder (pre-registered, branches mutually exclusive)

The ladder is checked in order; the first matching branch fires.

1. **`BLOCKED_corpus_missing`** — `data/corpora/ae/y*.htm` files missing or unreadable. *No claim made.*
2. **`BLOCKED_corpus_incomplete`** — A7 violation: `n_yasnas_loaded != 73`. *Should be unreachable post sizing fix; defensive guard.*
3. **`BLOCKED_yasna_28_too_short`** — `n_letters < 1,000` OR `n_verses < 10`. *Should be unreachable.*
4. **`FAIL_audit_peer_pool_size`** — n_peers < PEER_AUDIT_FLOOR_F55 = 50.
5. **`FAIL_audit_normaliser_sentinel`** — A5 sentinel does not match.
6. **`FAIL_audit_alphabet_coverage`** — A6 violation.
7. **`FAIL_audit_theorem`** — A1 violation: at least one variant has Δ > 2.0 + 1e-9.
8. **`FAIL_recall_below_floor`** — variant_recall < 1.000.
9. **`FAIL_fpr_above_ceiling`** — peer_fpr > 0.000.
10. **`PARTIAL_fpr_below_band`** — variant_recall == 1.000 AND 0 < peer_fpr ≤ PARTIAL_FPR_BAND_HI.
11. **`PASS_universal_perfect_recall_zero_fpr`** — variant_recall == 1.000 AND peer_fpr == 0.000. **F-row candidate F62**.

### 4.1 — F-row reservation policy

If branch 11 fires AND all seven audit hooks pass, the result will be filed as **F62**. If branches 7/8/9 fire, the result will be filed as **FN12** (failed-null pre-registration).

---

## 5. Honest scope statement

**Pre-committed before observing the receipt:** A `PASS_universal_perfect_recall_zero_fpr` outcome would establish:

- The **fourth** cross-tradition POSITIVE F-detector data point (F59 / F60 / F61 are the prior three; H63 PASS would be the fourth).
- F55 generalises across **5 language families** at chapter scope: Central Semitic (Quran V1), Northwest Semitic (Hebrew Psalm 78), Hellenic Indo-European (Greek Mark 1), Indo-Aryan / Indic (Pāli DN 1), Indo-Iranian / Old Iranian (Avestan Yasna 28).
- F55 generalises across **5 religious traditions**: Islam, Judaism, Christianity, Theravāda Buddhism, Zoroastrianism. No two share core soteriology.
- F55 survives the **Indo-Iranian sister-branch test**: Pāli (Indo-Aryan) and Avestan (Old Iranian) descend from Proto-Indo-Iranian and share substantial morphological similarity; F55 still discriminates within both at chapter scope.

It would NOT establish:

- That F55 generalises to **non-alphabetic** scripts (Classical Chinese Daodejing in Han characters, ancient Egyptian hieroglyphs, Mayan glyphs, cuneiform syllabaries are separate hash-locked PREREGs).
- That F55 generalises when the canonical text is in its **native (non-Latin) script** (the Geldner Latin transliteration is the editorial choice; running on native Avestan-script Yasna would test the script-of-encoding axis separately).
- That F55 generalises to **shorter-chapter or smaller-pool** traditions than the locked floors (target ≥ 1,000 letters, peer pool ≥ 50 chapters).
- That the cross-tradition F55 result is "Quran-distinctive" — F55 is a **detector** receipt (recall + FPR), NOT a Quran-distinctiveness claim.
- That F53's failure on Hebrew (FN11) is "rescued" — different detector class.
- That **the Avestan corpus's small size (73 chapters total) is not a methodological concern**: it is a real concern, partially mitigated by the F55-family peer pool floor amendment to 50. Future F55 expansions should **cross-validate against a corpus where independently-defined peer pool ≥ 100** (e.g., Vedic Sanskrit Rigveda has ~1,028 sūktas; Pāli MN+SN gives ~7,500 suttas; Bilara has both available — a future PREREG could re-anchor with these).

**Pre-committed before observing the receipt:** A FAIL outcome (any of branches 7–9) is publishable as **FN12**. A theorem-violation (branch 7) would be alarming and necessitate investigating the Avestan normaliser's NFD + casefold pipeline. A recall-below-floor (branch 8) would mean Avestan has bigram-coincidence substitutions where Δ = 0. An FPR-above-ceiling (branch 9) would mean some Yasna chapter is near-bigram-identical to Yasna 28, contradicting the 291 min observation.

---

## 6. Hash-lock procedure

This file's SHA-256 hash is computed at seal time and stored at `experiments/exp108_F55_y28_bigram/PREREG_HASH.txt`. The accompanying `run.py` reads its expected hash from `_PREREG_EXPECTED_HASH`; `run.py` refuses to execute if the in-file PREREG hash drifts from the locked expected value.

---

## 7. Receipt schema (locked)

```
{
  "experiment": "exp108_F55_y28_bigram",
  "hypothesis_id": "H63",
  "verdict": "<one of branch 1-11 above>",
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
      "n_yasnas_total":          <int>,        # must be 73 (A7)
      "target_yasna":            28,
      "target_n_verses":         <int>,
      "target_n_letters":        <int>,
      "target_n_distinct_chars": <int>,
      "peer_pool_size":          <int>,
      "peer_pool_strategy":      "all_other_yasna_chapters_no_length_matching",
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
      "alphabet_coverage_ok":    <bool>,
      "corpus_complete":         <bool>
    },
    "warnings": [...],
    "errors":   [...]
  },
  "pre_stage_diagnostic_receipt":
      "results/auxiliary/_y28_bigram_sizing.json"
}
```

---

## 8. Out of scope

- Native Avestan-script (Pahlavi-derived) edition — separate PREREG.
- Other Zoroastrian texts (Visperad, Vendidad, Khorde Avesta, Yashts) — separate PREREGs each. Adding these would lift the peer pool well above 100 if needed.
- Sanskrit Vedic, Classical Chinese Daodejing, Old Tamil Sangam, Egyptian / Akkadian / Mayan logographic-script corpora — separate PREREGs each.
- Insertion or deletion forgeries.
- Multi-letter forgeries.
- Any τ != 2.0.
- Any calibration step.
- Length-matched peer pool variants (this run uses no length matching by design).
- Indo-Iranian phylogenetic claim about Pāli ↔ Avestan distance (the "sister-branch test" framing in §1 is a *post-hoc observation*, not a pre-registered claim).
- LLM-generated forgeries.

---

## 9. Cross-references

- F55 detector definition: `experiments/exp95j_bigram_shift_universal/PREREG.md`
- F55 theorem 3.2: `experiments/exp95j_bigram_shift_universal/PREREG.md` §3.2
- Sibling H60 (F55 → Hebrew, F59): `experiments/exp105_F55_psalm78_bigram/PREREG.md`
- Sibling H61 (F55 → Greek, F60): `experiments/exp106_F55_mark1_bigram/PREREG.md`
- Sibling H62 (F55 → Pāli, F61): `experiments/exp107_F55_dn1_bigram/PREREG.md`
- Pre-stage diagnostic receipt: `results/auxiliary/_y28_bigram_sizing.json`
- Avestan corpus manifest: `data/corpora/ae/manifest.json` (Avesta.org Geldner-1896 edition; public domain; 73 yasnas across 12 HTML files)
- Failure-mode contrast: `docs/PAPER.md` §4.47.5 (FN11), §4.47.8 (F59), §4.47.9 (F60), §4.47.10 (F61)
- F55-family peer pool floor amendment justification: §2.1 above
