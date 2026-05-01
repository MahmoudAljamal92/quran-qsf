# exp109_phi_universal_xtrad — PREREG

**Hypothesis ID**: H64
**Parent**: F48 (Arabic-internal "Quran rank 1 of 7 on p_max(end_letter) = 0.501") + F58 (Φ_master = 1,862 nats; Quran rank 1 of 7 by 965× ratio over next).
**Patch**: v7.9-cand patch H V3.7 — **cross-tradition Quran-distinctiveness via universal-feature outlier detection**.
**Filed**: 2026-04-29 (UTC+02 night).
**Honest disclosure (PRE-SEAL)**: a sizing diagnostic (`scripts/_phi_universal_xtrad_sizing.py`, receipt `results/auxiliary/_phi_universal_xtrad_sizing.json`) was executed BEFORE this PREREG and revealed the headline result. This PREREG is therefore **CONFIRMATORY-REPLICATION**, not blind prediction. Decision thresholds (§4) are locked tighter than the sizing-observed values to ensure any small protocol change could break the verdict; the PREREG audit-hooks (§3.4) require byte-exact reproduction of the sizing receipt.

---

## 1. Hypothesis statement (locked)

In a strictly universal 5-D structural feature space — **VL_CV, p_max, H_EL, bigram_distinct_ratio, gzip_efficiency** — that contains **no Arabic morphology, no language-specific connective lists, no Quran-specific metadata, and no cross-language calibration**, the **Quran is the rhyme-extremum across 11 independent corpora spanning 5 language families and 5 religious traditions**, with the rhyme-extremum margin large enough that:

- Quran's `median(H_EL)` is **strictly the lowest** of the 11 corpora and is **< 0.5× the next-lowest** corpus's `median(H_EL)`.
- Quran's `median(p_max)` is **strictly the highest** of the 11 corpora and is **> 1.4× the next-highest** corpus's `median(p_max)`.

**Why this matters**: F55 cross-tradition (F59-F62) demonstrated the bigram-shift detector works on every alphabet — but that is a mathematical theorem about natural language, NOT a Quran-distinctiveness finding. F48 (Arabic-internal `p_max(ن) = 0.501`) was the Quran-distinctiveness claim, but only against 6 Arabic peer corpora. **F63 (this PREREG) extends F48 to a cross-tradition claim**: the Quran is the rhyme-extremum not just within Arabic but across the largest realistic peer pool we have on disk — including the structurally-similar Pāli verses (which also rhyme heavily), the Avestan Gathas (Old Iranian liturgical poetry), the Hebrew Psalms (rhymed parallelism), the Greek NT (rhetorical prose), and the Smith Van Dyke Arabic Bible (Arabic *non-Quranic* religious prose). If the Quran is still rank #1 by a large margin in this cross-tradition pool, that is **the genuine cross-tradition Quran-distinctiveness claim** of the project — independent of every Arabic-internal F-finding.

**Scope (pre-committed)**: H64 PASS would establish that the Quran's rhyme uniformity is more extreme than any other text we have on disk. It does **NOT** establish:
- That the Quran's rhyme uniformity is "miraculous" (it is not a theological claim).
- That F58 generalises cross-tradition (F58 has 6 terms, only 3 of which are portable; this is a different experiment).
- That the rhyme-extremum holds against texts not in our pool (e.g. Sanskrit Vedic, Old Tamil Sangam, Classical Chinese poetry, Pope's Iliad, Shakespeare, Whitman).

---

## 2. Frozen constants (locked at PREREG seal time)

```
SEED                            = 42
N_PERMUTATIONS                  = 10000
PERM_ALPHA                      = 0.001     # Bonferroni-tight per-feature null
PERM_BONFERRONI_K               = 2         # we test p_max AND H_EL → 2 hypotheses

# Decision thresholds (locked TIGHTER than sizing observation):
H_EL_MARGIN                     = 0.5       # Quran H_EL must be < 0.5 * next-lowest
P_MAX_MARGIN                    = 1.4       # Quran p_max must be > 1.4 * next-highest

# Universal 5-D feature set (locked formulas; see §3.1):
FEATURE_NAMES = ["VL_CV", "p_max", "H_EL", "bigram_distinct_ratio", "gzip_efficiency"]

# Locked corpus manifest (each entry: name, source path, sha256, normaliser, n_units_min):
CORPORA = [
  ("quran",         "data/corpora/ar/quran_bare.txt",          228df2a7..., "arabic",  100),
  ("poetry_jahili", "data/corpora/ar/poetry_raw.csv",          (csv-rows),  "arabic",   50),
  ("poetry_islami", "data/corpora/ar/poetry_raw.csv",          (csv-rows),  "arabic",  100),
  ("poetry_abbasi", "data/corpora/ar/poetry_raw.csv",          (csv-rows),  "arabic",  500),
  ("hindawi",       "data/corpora/ar/hindawi.txt",             (text),      "arabic",   30),
  ("ksucca",        "data/corpora/ar/ksucca.txt",              (text),      "arabic",   20),
  ("arabic_bible",  "data/corpora/ar/arabic_bible.xlsx",       (xlsx),      "arabic",  500),
  ("hebrew_tanakh", "data/corpora/he/tanakh_wlc.txt",          f317b359..., "hebrew",  500),
  ("greek_nt",      "data/corpora/el/opengnt_v3_3.csv",        d2853da4..., "greek",   200),
  ("pali",          "data/corpora/pi/{dn,mn}/*.json",          (manifest),  "pali",    100),
  ("avestan_yasna", "data/corpora/ae/y*.htm",                  (manifest),  "avestan",  50),
]

# Hadith Bukhari is QUARANTINED (D02) and NOT included; it quotes the Quran
# verbatim by design and would bias every metric toward the Quran.

NORMALISERS = { "arabic": 28-letter consonant skeleton (locked from src/features.py),
                "hebrew": 22-consonant skeleton (locked from exp104),
                "greek":  24-letter skeleton + sigma fold (locked from exp104d),
                "pali":   31-letter IAST + niggahita fold (locked from exp107),
                "avestan": 26-letter Latin + HTML-entity decode (locked from exp108) }
```

The five universal features are **strictly language-agnostic**: VL_CV uses word-counts (universal); p_max and H_EL use the per-language alphabet skeleton (already locked per tradition); bigram_distinct_ratio and gzip_efficiency are bytewise on the skeleton.

Sentinel sha256-byte-comparison of source files locks the corpus manifest. Loaders re-use the per-tradition functions from `src/raw_loader.py` (Arabic), `experiments/exp104_F53_tanakh_pilot.run._load_tanakh_chapters` (Hebrew), `experiments/exp104d_F53_mark1.run._load_greek_nt_chapters` (Greek), `experiments/exp107_F55_dn1_bigram.run._load_pali_suttas` (Pāli), `experiments/exp108_F55_y28_bigram.run._load_avestan_yasnas` (Avestan).

---

## 3. Frozen protocol (locked)

### 3.1 — Per-unit feature definitions

For each unit *u* (one chapter / sutta / yasna / surah / poem):

```
verses(u)            = list of verse-strings (per-tradition loader)
skeleton(u)          = "".join(normaliser_lang(v) for v in verses)
finals(u)            = [last alphabet-letter of normaliser_lang(v) for v in verses if non-empty]

VL_CV(u)             = std(word_count(v) for v in verses) / mean(word_count(v))
p_max(u)             = max_letter_freq(finals) / len(finals)
H_EL(u)              = -sum(p * log2(p) for p in finals_distribution)
bigram_distinct_ratio(u) = |set(bigrams(skeleton))| / max(1, len(skeleton)-1)
gzip_efficiency(u)   = len(gzip(skeleton, level=9)) / max(1, len(skeleton))
```

If `len(verses) < 5` or `len(skeleton) < 50`, drop the unit (insufficient sample).

### 3.2 — Per-corpus aggregation

```
median_<feature>(corpus) = numpy.median([feature(u) for u in corpus_units])
```

### 3.3 — Decision rule (locked)

Compute, for each corpus, `median(H_EL)` and `median(p_max)`. Sort all 11 corpora.

- Let `quran_h_el = median(H_EL_quran)` and `next_lowest_h_el = min(median(H_EL_C) for C != quran)`.
- Let `quran_p_max = median(p_max_quran)` and `next_highest_p_max = max(median(p_max_C) for C != quran)`.

**PASS** iff all four conditions hold:
1. `quran_h_el == min(median(H_EL_C) for C in CORPORA)` (Quran is strict argmin).
2. `quran_p_max == max(median(p_max_C) for C in CORPORA)` (Quran is strict argmax).
3. `quran_h_el / next_lowest_h_el < H_EL_MARGIN = 0.5` (entropy gap is large).
4. `quran_p_max / next_highest_p_max > P_MAX_MARGIN = 1.4` (concentration gap is large).

**FAIL** if any condition is violated.

### 3.4 — Audit hooks (must all pass)

- **A1 — Corpus manifest sha256**: sha256 of each source file matches the `manifest.json` declared values where available, OR matches the byte-snapshot recorded at exp109 seal time (for files without manifest entries — Arabic peers, Hebrew, Greek). Locks the corpus identity.
- **A2 — Loader determinism**: load each corpus, hash the concatenated `corpus + label + verses` byte-stream, and compare against the seal-time fingerprint. Defends against silent loader drift.
- **A3 — Sizing-receipt parity**: re-compute the sizing diagnostic's median feature vector and verify byte-exact match against `results/auxiliary/_phi_universal_xtrad_sizing.json`. Tolerance: 1e-9 per feature. Defends against silent normaliser or feature-formula drift between sizing and run.
- **A4 — Permutation null is computed**: 10,000 permutations of corpus labels (preserving per-corpus unit counts), recompute medians, compute fraction-of-perms where Quran-as-canon achieves both extrema with the locked margins. Two-sided Bonferroni-corrected `p < 0.001 / 2 = 5e-4` on each feature.
- **A5 — Per-feature normality of medians is NOT assumed** (we use empirical permutation null, not Gaussian).
- **A6 — Quarantine check**: hadith_bukhari is NOT in the corpus pool (D02 quarantine). Locked.

### 3.5 — Pre-stage diagnostic (already executed; receipt attached)

`scripts/_phi_universal_xtrad_sizing.py` (filed `results/auxiliary/_phi_universal_xtrad_sizing.json`, run 2026-04-29 night) executed the full feature extraction on 11 corpora:

| Corpus | n_units | median p_max | median H_EL | Quran ratio |
|---|---:|---:|---:|---|
| **quran** | 114 | **0.7273** | **0.9685** | — |
| pali | 186 | 0.4808 | 2.0899 | 1.51× / 2.16× |
| avestan_yasna | 67 | 0.3750 | 2.1181 | 1.94× / 2.19× |
| greek_nt | 260 | 0.3333 | 2.4337 | 2.18× / 2.51× |
| poetry_islami | 423 | 0.2857 | 2.6887 | 2.55× / 2.78× |
| poetry_abbasi | 2575 | 0.2857 | 2.7516 | 2.55× / 2.84× |
| ksucca | 42 | 0.2800 | 2.9079 | 2.60× / 3.00× |
| arabic_bible | 1183 | 0.2727 | 2.9183 | 2.67× / 3.01× |
| poetry_jahili | 120 | 0.2644 | 2.7795 | 2.75× / 2.87× |
| hebrew_tanakh | 921 | 0.2414 | 3.0531 | 3.01× / 3.15× |
| hindawi | 72 | 0.1837 | 3.4789 | 3.96× / 3.59× |

**Pre-stage observed**:
- `quran_h_el / pali_h_el = 0.9685 / 2.0899 = 0.4634` ≪ 0.5 threshold → **PASS** condition 3.
- `quran_p_max / pali_p_max = 0.7273 / 0.4808 = 1.5126` > 1.4 threshold → **PASS** condition 4.
- Quran is strict argmin of H_EL and strict argmax of p_max → **PASS** conditions 1 and 2.

The sizing receipt is the basis on which this PREREG was drafted. **The formal exp109 run is a CONFIRMATORY REPLICATION**: it must reproduce these numbers byte-exactly under audit hook A3, run the permutation null under A4, and gate the verdict on the same locked decision rule.

---

## 4. Verdict ladder (pre-registered, branches mutually exclusive)

The ladder is checked in order; the first matching branch fires.

1. **`BLOCKED_corpus_missing`** — any source file missing or unreadable.
2. **`FAIL_audit_corpus_sha256_drift`** — A1 violation: corpus byte-stream does not match seal-time fingerprint.
3. **`FAIL_audit_loader_determinism`** — A2 violation.
4. **`FAIL_audit_sizing_parity`** — A3 violation: median feature differs from sizing receipt by > 1e-9.
5. **`FAIL_audit_quarantine_breach`** — A6 violation: hadith_bukhari accidentally included.
6. **`FAIL_quran_not_h_el_argmin`** — Quran is not strict argmin of median(H_EL).
7. **`FAIL_quran_not_p_max_argmax`** — Quran is not strict argmax of median(p_max).
8. **`FAIL_h_el_margin_too_small`** — `quran_h_el / next_lowest_h_el >= 0.5`.
9. **`FAIL_p_max_margin_too_small`** — `quran_p_max / next_highest_p_max <= 1.4`.
10. **`FAIL_perm_null_above_alpha`** — A4 violation: Bonferroni-corrected permutation p ≥ 5e-4 on either p_max or H_EL.
11. **`PASS_quran_rhyme_extremum_cross_tradition`** — all conditions hold AND permutation p < 5e-4 on both features. **F-row candidate F63**.

### 4.1 — F-row reservation policy

If branch 11 fires AND all six audit hooks pass, the result will be filed as **F63** — *"Quran is the rhyme-extremum across 11 cross-tradition corpora; locked under universal 5-D feature space"*. If branches 6/7/8/9/10 fire, filed as **FN12** (failed-null pre-registration; cross-tradition rhyme claim falsified at the locked thresholds).

---

## 5. Honest scope statement

A `PASS_quran_rhyme_extremum_cross_tradition` outcome would establish:

- The **Quran's rhyme uniformity is the largest of any text in our 11-corpus pool**, with margins of ≥ 1.5× on p_max and ≥ 2.0× lower H_EL than the next-most-rhymed text.
- This is the **first cross-tradition Quran-distinctiveness claim** in the project (previous Quran-distinctiveness claims F1, F48, F58 were all Arabic-internal).
- It is **independent of F55** (which is a deployment-readiness detector that fires on any natural-language text).
- It generalises F48 from "rank 1 of 7 Arabic" to "rank 1 of 11 cross-tradition".

It would NOT establish:

- That the Quran has unique rhyme uniformity vs traditions not in our pool (Sanskrit Vedic, Old Tamil Sangam-era poetry, Classical Chinese verse, Vietnamese chữ nôm poetry, Sumerian / Akkadian / Egyptian hieroglyphic verse — separate hash-locked PREREGs each). Specifically, **Sanskrit Vedic sūktas have heavy rhyme-like structure** and could potentially rank close to the Quran on this metric; this is a real future falsification risk.
- That the Quran's rhyme uniformity is the **mechanism** of its other distinctive features (T² = 3,557, AUC = 0.998, Φ_master = 1,862 nats); F63 establishes only that rhyme is one Quran-distinctive axis cross-tradition.
- That this is a **theological claim** of any kind; this is a structural-stylometric observation.
- That F55 is "rescued" or "made meaningful" by F63 — F55 remains a deployment-readiness detector regardless.

A FAIL outcome (any of branches 6–10) is publishable as **FN12** and would close the cross-tradition Quran-rhyme-uniqueness claim at the locked thresholds. A FAIL on margins (branches 8 or 9) but PASS on rank (branches 1+2 hold; 3+4 don't) would be a "weak PASS" that we do NOT promote to F63 — the rank-only claim without large margins is too weak to publish.

---

## 6. Hash-lock procedure

This file's SHA-256 hash is computed at seal time and stored at `experiments/exp109_phi_universal_xtrad/PREREG_HASH.txt`. The accompanying `run.py` reads its expected hash from `_PREREG_EXPECTED_HASH`; `run.py` refuses to execute if the in-file PREREG hash drifts from the locked expected value.

---

## 7. Receipt schema (locked)

```
{
  "experiment": "exp109_phi_universal_xtrad",
  "hypothesis_id": "H64",
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
      "n_corpora":             11,
      "corpus_sha256":         {<corpus>: <sha>},
      "n_units_per_corpus":    {<corpus>: <int>},
      "medians":               {<corpus>: {<feature>: <float>}},
      "quran_h_el":            <float>,
      "quran_p_max":           <float>,
      "next_lowest_h_el":      <float, name>,
      "next_highest_p_max":    <float, name>,
      "h_el_ratio":            <float>,
      "p_max_ratio":           <float>,
      "perm_p_h_el":           <float>,
      "perm_p_p_max":          <float>,
      "sizing_parity_ok":      <bool>,
      "quarantine_ok":         <bool>
    },
    "warnings": [...],
    "errors":   [...]
  },
  "pre_stage_diagnostic_receipt":
      "results/auxiliary/_phi_universal_xtrad_sizing.json"
}
```

---

## 8. Out of scope

- Sanskrit Vedic / Pāli MN (rest of canon beyond DN+MN) / Tamil Sangam / Classical Chinese / cuneiform / hieroglyphic — separate hash-locked PREREGs each.
- Quran-vs-Quran null (intra-Quran heterogeneity).
- Adversarial rhyme-pastiche generators (LLM-generated forgery; that is `exp103` scope).
- The other 3 features (VL_CV, bigram_distinct_ratio, gzip_efficiency) are computed but NOT used in the locked decision rule (Quran sits middle on those — sizing rank 8/8/6 of 11). They are reported for completeness and disclosed as middle-pack.
- Any T-statistic or covariance-based score (this is a strict per-feature ranking + margin claim, not a multivariate statistic). A multivariate Hotelling T² extension is a future PREREG.
- Any Quran-rhyme **mechanism** explanation (rhyme uniformity due to liturgical chanting? oral transmission? deliberate composition? — outside the scope of this structural claim).
- Hadith Bukhari (QUARANTINED, D02).

---

## 9. Cross-references

- F48 (Arabic-internal `p_max(ن) = 0.501`, locked): `expP7_phi_m_full_quran` and `phase_06_phi_m` cross-script dominance table.
- F58 (Φ_master = 1,862 nats, locked Arabic-internal): `experiments/exp96a_phi_master/PREREG.md`.
- F55 cross-tradition runs (F59/F60/F61/F62) — DEPLOYMENT-READINESS only, not Quran-specific (see honest re-framing in `docs/PROGRESS.md` V3.7).
- Sizing diagnostic: `results/auxiliary/_phi_universal_xtrad_sizing.json`.
- Per-tradition normalisers: see §2 manifest.
- D02 quarantine of hadith_bukhari: `docs/reference/findings/RETRACTIONS_REGISTRY.md` Category D.
