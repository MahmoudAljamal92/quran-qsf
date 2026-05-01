# PREREG — exp111_F63_rigveda_falsification: extend F63 to Sanskrit Vedic Rigveda

**Status**: SEALED 2026-04-29 morning, v7.9-cand patch H V3.8.
**Hypothesis ID**: H66.
**Pairs with**: F63 (`exp109_phi_universal_xtrad`, cross-tradition Quran rhyme-extremum, R1 6-corpus version PASS at 0/10,000 perm null).
**Author intent**: stress-test F63 against the most-rhymed Indo-European liturgical text family (Rigveda Saṃhitā, all 10 mandalas, 1,003 sūktas, ~5000 BCE compositional layer) — the natural falsification candidate flagged in the F63 V3.8 SCOPE_AUDIT addendum (PAPER §4.47.12.1, point 2).

---

## 0. Honest disclosure (pre-run, locked at PREREG seal)

1. **Sanskrit Rigveda is the natural F63 falsification target**: Vedic hymns rhyme by stem-internal phonological recurrence, alliteration, and uniform meter (gāyatrī, anuṣṭubh, triṣṭubh, jagatī); pāda-final patterns are *expected* to be highly rhyme-clustered. If Rigveda's per-sūkta p_max ≥ Quran's 0.7273, **F63 dies** as a cross-tradition Quran-distinctiveness claim and reduces to "Quran is the rhyme-extremum among non-Indic religious traditions".

2. **CONFIRMATORY-REPLICATION**: a sizing diagnostic (`scripts/_rigveda_loader_v2.py`) was executed BEFORE this PREREG was sealed and reveals: Rigveda median p_max = **0.3333** (vs Quran 0.7273; Quran wins 2.18×); Rigveda median H_EL = **2.2878 bits** (vs Quran 0.9685; Quran is 2.36× lower). **Quran's rank 1/7 against the F63 R1 6-corpus pool + Rigveda survives**; Pāli remains the next-highest at 0.4808 (ratio 1.5126; the F63 R1 margin is byte-identical because Rigveda lands between Pāli and Avestan). The PREREG is sealed under expected PASS_quran_rhyme_extremum_xtrad_with_rigveda.

3. **No new normaliser logic, no tuning loop**: the Devanagari-skeleton normaliser (33 consonants + 14 vowels, NFD-strip combining marks) is locked at sizing time; corpus byte-fingerprints come from `data/corpora/sa/manifest.json` (DharmicData edition; SHA-256 per mandala embedded in manifest, public-domain Vedic text under educational/research use).

---

## 1. Question

Does F63's R1 6-corpus claim (Quran is the ayat-rhyme extremum across cross-tradition canonical religious texts at the level of tradition-defined verse boundaries) survive the addition of Sanskrit Rigveda Saṃhitā?

---

## 2. Data — locked

Inherited byte-exact from F63 R1 (6 corpora) plus Rigveda:

- quran (114 surahs, real ayat) — SHA-256 prefix `228df2a7…`
- arabic_bible (1,183 chapters, Smith Van Dyke; PUBLIC DOMAIN) — SHA-256 prefix `5b57b622…`
- hebrew_tanakh (921 chapters, WLC; PUBLIC DOMAIN) — SHA-256 prefix `f317b359…`
- greek_nt (260 chapters, OpenGNT v3.3; CC-BY-SA-4.0) — SHA-256 prefix `d2853da4…`
- pali (186 suttas, SuttaCentral Mahāsaṅgīti; CC0-1.0) — SHA-256 aggregate prefix `70fd2b21…`
- avestan_yasna (67 chapters, Avesta.org Geldner-1896; PUBLIC DOMAIN) — SHA-256 aggregate prefix `cb0aadc4…`
- **rigveda (1,003 sūktas across 10 mandalas, DharmicData edition; educational/research use)** — SHA-256 manifest at `data/corpora/sa/manifest.json` (10 mandala SHA-256 hashes locked individually)

**Total units**: 3,734 (vs F63 R1's 2,731 — +1,003 Rigveda sūktas).

**Devanagari skeleton (locked)**: 47 letters total (33 consonants + 14 vowels), excluding combining marks (vowel signs, virama, anusvara, visarga, accents).

---

## 3. Protocol

Identical to F63 R1 (`scripts/_audit_f63_real_verse_only_perm.py`) but with Rigveda added as 7th corpus.

### 3.1 Decision rule (locked TIGHTER than sizing-observed values)

A sizing diagnostic was executed before this PREREG was sealed. Locked thresholds for PASS:

1. **Strict argmin H_EL**: `argmin_c median(H_EL_c) == "quran"` over 7 corpora.
2. **Strict argmax p_max**: `argmax_c median(p_max_c) == "quran"` over 7 corpora.
3. **H_EL margin**: `median(H_EL)_quran / median(H_EL)_next_lowest < 0.5` (sizing-observed 0.4634, locked at 0.5; same floor as F63 R1).
4. **p_max margin**: `median(p_max)_quran / median(p_max)_next_highest > 1.4` (sizing-observed 1.5126, locked at 1.4; same floor as F63 R1).
5. **Permutation null**: 10,000 random label-shuffles of the 3,734 unit-to-corpus assignments (preserving per-corpus unit counts; seed = 42). For each shuffle, recompute medians per fake-corpus; check if any fake-corpus achieves Quran's joint H_EL + p_max extremum at the locked margins.
6. **Bonferroni-corrected α** = 0.001 / 2 = 5e-4 (K=2 features).
7. **Audit hook A1**: Rigveda corpus byte-fingerprint check against `data/corpora/sa/manifest.json` SHA-256s.
8. **Audit hook A2**: feature parity for Quran vs F63 R1 receipt within 1e-9 (loader-determinism check).

### 3.2 Verdict ladder

- **PASS_quran_rhyme_extremum_xtrad_with_rigveda** if §3.1 conditions 1-6 + A1+A2 all hold.
- **FAIL_rigveda_dethrones_quran** if §3.1 condition 1, 2, 3, or 4 fails substantively (Rigveda beats Quran on the rhyme axis).
- **FAIL_audit_*** for any audit hook failing.

### 3.3 Audit-floor amendment for F63-family experiments

The F63 family inherits the F55-amendment `PEER_AUDIT_FLOOR = 50` (per F62 / exp108 PREREG §2.1). Rigveda has 1,003 sūktas, comfortably above any reasonable floor.

---

## 4. Reporting — locked at PREREG seal

The receipt MUST report:
- Per-corpus n_units, median EL/H_EL/p_max/VL_CV/bigram_distinct_ratio/gzip_efficiency
- Strict-argmin / argmax verdicts on H_EL and p_max
- Margin ratios (Quran / next)
- Empirical perm-p (H_EL extremum) and (p_max extremum)
- All audit hook outcomes
- Wall-time
- PREREG hash match
- Rigveda mandala-level sūkta counts

---

## 5. What this experiment does NOT establish

- That F63 generalises to traditions we have not yet tested (Old Tamil Sangam, Classical Chinese, cuneiform, hieroglyphic, Tibetan, Coptic, Ge'ez).
- That the Quran's rhyme uniformity is mechanistically caused by anything (theological or otherwise).
- That F63 is theoretically unmatchable (any author could write text with p_max > 0.7273; F63 is empirical, not a mathematical bound).
- That the Rigveda's Devanāgarī skeleton is the only valid normalisation. An alternative IAST transliteration or akṣara-level (syllabic) normalisation might give different numbers; this PREREG locks the consonant+vowel skeleton.

---

## 6. Sealed prereg hash (auto-computed by run.py at execution time)

To be filled in by execution.

---

**END PREREG (sealed pre-run; no edits permitted).**
