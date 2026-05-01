# exp104d_F53_mark1 — PREREG (Phase 3, single-chapter cross-tradition F53 pilot, fourth in the H59 chain — Greek NT Mark 1)

**Hypothesis ID**: H59d
**Status**: pre-registered, hash-locked **before** any Greek compression call is issued.
**Patch context**: v7.9-cand patch H V3.2 (or later). Pre-staged 2026-04-28 night while `exp104c_F53_psalm78` is in flight; this PREREG is independent of `exp104c`'s outcome and stands as a separate cross-tradition datapoint regardless of whether H59c PASSes or FAILs.
**Position in chain**: fourth filed PREREG in the H59 amendment / extension chain. The first three (H59 Psalm 19 BLOCKED, H59b Psalm 119 FAIL_audit_peer_pool_size, H59c Psalm 78 PENDING) all target Hebrew Tanakh chapters. **H59d is the first non-Semitic chapter in the chain** — Indo-European (Greek), Koine (~50-100 CE).

---

## 0. Why this exists (one paragraph)

Even if H59c (Psalm 78) PASSes, a single Hebrew datapoint is insufficient to claim cross-tradition F53 generalisation: Hebrew and Arabic are both Semitic-family languages with consonant-skeleton orthography and triliteral root morphology. A genuine cross-tradition test requires at least one **non-Semitic** language. Greek Koine is the obvious next step: it is (a) a different language family (Indo-European), (b) a different script (Greek alphabet, 24 letters, with vowels written as letters), (c) a different morphology (inflectional rather than root-pattern), and (d) the canonical language of an oral-liturgical tradition (early Christian) of the same epoch and similar genre (narrative gospel) as the existing Hebrew test. Mark 1 is the opening chapter of the shortest Synoptic gospel — short enough to enumerate variants exhaustively in reasonable wall-time, long enough to clear the locked chapter-length floor, and stylistically representative of NT narrative.

This PREREG is filed and hash-locked **before any Greek compression call is issued** to ensure the protocol cannot be adjusted post-hoc. The amendment chain is fully auditable (H59 → H59b → H59c → H59d) and no rule has been relaxed at any step; only the target chapter (and, for H59d, the language and corpus) has changed.

---

## 1. Hypothesis (one paragraph)

**H59d (F53 cross-tradition Koine Greek Mark 1 pilot)**: Under the K=2 multi-compressor consensus rule with τ thresholds calibrated *on a Greek-NT-narrative peer pool* (per-compressor 5th percentile of length-matched ctrl-Δ NCD distribution; identical recipe to `exp95c`, `exp104`, `exp104b`, `exp104c`), single-letter substitution on **Mark 1** (24-letter Greek alphabet, diacritics-stripped Unicode NFD lower-cased; OpenGNT v3.3 source) achieves **recall ≥ 0.999** with **FPR ≤ 0.05** against the same calibration peer pool. Equivalently: every single-letter substitution on Mark 1 must produce K=2-consensus NCD shifts that exceed the locked Greek τ on at least 2 of 4 compressors {gzip-9, bz2-9, lzma-preset-9, zstd-9}.

**Pilot scope**: one NT chapter only (Mark 1). Generalisation to whole NT / whole Synoptics / whole Pauline corpus is OUT of scope here.

---

## 2. Locked decision rules (frozen text, byte-exact)

### 2.1 Frozen target text

- **Target chapter**: **Mark 1** of the Greek New Testament (OpenGNT version 3.3, file `data/corpora/el/opengnt_v3_3.csv`, OpenGNT internal identifier `«Book|Chapter|Verse» = 41|1|1` through `41|1|45`). Verse count: 45 verses.
- **Surface-form column**: column `«OGNTk|OGNTu|OGNTa|lexeme|rmac|sn»`, sub-field **OGNTk** (Koine Greek primary surface form, no diacritics) per token, concatenated with single ASCII spaces between tokens, ASCII space between verses (no verse markers in the compression input).
- **Letter normalisation**: Unicode NFD decomposition, strip all combining diacritical marks (Unicode category `Mn` and code points U+0300–U+036F + U+1DC0–U+1DFF), lowercase via Greek-aware `casefold()`, retain only the 24 lowercase Greek letters {α β γ δ ε ζ η θ ι κ λ μ ν ξ ο π ρ σ τ υ φ χ ψ ω}, drop final-sigma fold (ς → σ), drop all whitespace and punctuation. The resulting "Greek skeleton" is a pure 24-letter consonant-and-vowel string with no inter-token separators (parallel to the Hebrew 22-consonant skeleton in exp104, but Greek includes vowels because Greek alphabet writes vowels).
- **Why Mark 1**: Mark is the shortest Synoptic gospel (16 chapters); Mark 1 is its narrative opening (John the Baptist, baptism, calling of disciples, healings); 45 verses; estimated 3,500–4,500 letter-skeleton characters under the locked normaliser. Pre-run sizing diagnostic (deferred until after PREREG-hash lock; protocol-correct because the diagnostic only filters the peer pool count, not the verdict) will confirm the chapter clears the locked 1,000-letter floor and that ≥ 100 length-matched NT-narrative peers exist.

### 2.2 Frozen peer pool

- Greek NT narrative pool: chapters of the Greek New Testament *outside Mark*, drawn from books 40 (Matthew), 42 (Luke), 43 (John), 44 (Acts), and 58 (Hebrews narrative-style passages) — these constitute the canonical narrative-genre subset of the NT, parallel to the Genesis/Exodus/Joshua/Judges/Samuel/Kings narrative pool used as the Hebrew peer set in exp104. Total candidate chapters: 28+24+21+28+13 = 114 NT-narrative chapters outside Mark.
- Length-matched to Mark 1 ± 30 % (locked window fraction inherited from exp104). The `±30 %` window is determined *after* PREREG-hash lock by computing Mark 1's letter-skeleton length empirically.
- Random shuffle of length-matched candidates, take first `TARGET_N_PEERS = 200` (or all candidates if fewer than 200; locked from exp104 §2.2).
- **Audit floor**: peer pool size must be ≥ 100. If not, the verdict is `FAIL_audit_peer_pool_size` (parallel to FN10 / `exp104b`).

### 2.3 Frozen τ-calibration protocol (identical to exp104 §2.3)

For each compressor c ∈ {gzip-9, bz2-9, lzma-preset-9, zstd-9}, compute on the Greek-NT-narrative peer pool:

1. For each peer chapter, sample `N_CALIB_VARIANTS_PER_PEER = 30` single-letter substitution variants (random position × random letter from the 24-letter Greek alphabet, excluding the original letter at that position).
2. For each (peer, variant), compute `Δ_c = NCD_c(peer, peer_with_variant) − NCD_c(peer, peer)`.
3. The locked Greek τ_c is the **5th percentile** of the resulting `Δ_c` distribution.
4. The K=2 rule fires on a Mark 1 variant iff at least 2 of 4 compressors have `Δ_c ≥ τ_c`.

### 2.4 Verdict ladder (strict order; first match wins; identical to exp104 §2.4 with chapter substitution)

| # | Branch | Trigger | Implication |
|---|---|---|---|
| 1 | `BLOCKED_corpus_missing` | OpenGNT CSV missing or Mark 1 not found | Acquire / fix loader |
| 2 | `BLOCKED_mark1_too_short` | Mark 1 has < 1,000 letters or < 10 verses (highly unlikely — pre-run estimate ≥ 3,500 / 45) | Choose a different chapter via amendment |
| 3 | `FAIL_audit_peer_pool_size` | `n_peer_units < 100` | Widen window via amendment OR pick different peer subset |
| 4 | `FAIL_audit_tau_unstable` | Bootstrap of τ_c (200 resamples) shows any τ has CV > 0.30 | Calibration too noisy; widen pool via amendment |
| 5 | `FAIL_recall_below_floor` | K=2 consensus recall on Mark 1 single-letter variants < 0.999 | F53 rule does NOT close on Mark 1 at the locked floor; report cleanly |
| 6 | `FAIL_fpr_above_ceiling` | K=2 consensus FPR (peer-vs-peer pairs sampled at length-match) > 0.05 | Specificity insufficient |
| 7 | `PARTIAL_recall_above_99` | Recall ∈ [0.99, 0.999) AND FPR ≤ 0.05 | Partial closure; not paper-grade |
| 8 | **`PASS_consensus_100`** | Recall ≥ 0.999 AND FPR ≤ 0.05 | F53 rule generalises to Greek NT Mark 1 at full pilot-grade |

### 2.5 What promotion does NOT mean

A `PASS_consensus_100` verdict on this pilot does **NOT** establish that F53 generalises to:

- "All Greek canonical scriptures" (Septuagint, Apostolic Fathers, Patristic corpus all unaddressed)
- "All Indo-European canonical scriptures" (Sanskrit Vedic, Avestan Yasna, Pali Canon all unaddressed)
- "Quran is uniquely positioned across all texts" (this PREREG only tests whether the F53 *detector* fires on Mark 1; it makes no comparison between Quran and Mark 1 on any other axis)

A PASS on H59d combined with a PASS on H59c would be **two cross-language F53 datapoints (Hebrew + Greek)**, justifying follow-up PREREGs for Sanskrit Vedic and Pali Canon. A FAIL on either is publishable as an honest negative result bounding F53's transfer scope.

---

## 3. Frozen constants (identical to exp104 except target language and corpus)

- All compressor levels (gzip-9, bz2-9, lzma-preset-9, zstd-9), K=2, τ-percentile = 5, length-match-frac = 0.30, normaliser-recipe (NFD strip + casefold + alphabet whitelist), seeds (`SEED = 42`), bootstrap-N = 200, bootstrap-CV-ceil = 0.30, recall-floor = 0.999, partial-recall-floor = 0.99, FPR-ceil = 0.05, n-FPR-pairs = 1,000, n-calib-variants-per-peer = 30, target-n-peers = 200, peer-audit-floor = 100: **all inherited verbatim** from `experiments/exp104_F53_tanakh_pilot/PREREG.md` §3.
- **CHANGED constants**:
  - `TARGET_LANG = "el"` (Greek)
  - `TARGET_BOOK_NUMBER = 41` (Mark, OpenGNT internal numbering)
  - `TARGET_CHAPTER = 1`
  - `CORPUS_PATH = "data/corpora/el/opengnt_v3_3.csv"`
  - `CORPUS_FORMAT = "OpenGNT_v3_3_csv"` (column-mapping per §2.1)
  - `LETTER_ALPHABET = "αβγδεζηθικλμνξοπρστυφχψω"` (24 lowercase Greek letters; final-sigma ς is folded to σ at normalisation time, NOT included in the substitution alphabet)
  - `PEER_BOOK_NUMBERS = [40, 42, 43, 44, 58]` (Matthew, Luke, John, Acts, Hebrews)

---

## 4. Audit hooks (carried over from exp104 §4 with Greek-language additions)

1. **Corpus-hash sentinel**: SHA-256 of `data/corpora/el/opengnt_v3_3.csv` must match a value computed at first run and stored in `experiments/exp104d_F53_mark1/CORPUS_HASH.txt`. Drift aborts the run with verdict `BLOCKED_corpus_drift`.
2. **PREREG-hash sentinel**: SHA-256 of this PREREG.md must match `_PREREG_EXPECTED_HASH` in `run.py`. Mismatch raises before any compression call.
3. **Normaliser-fingerprint sentinel**: a small reference string `"Ἐν ἀρχῇ ἦν ὁ λόγος"` (John 1:1, classical accented Greek) must normalise to `"εναρχηηνολογοσ"` (14 letters; final medial sigma `σ` after the §2.1 ς→σ fold rule applies to the original final-sigma in λόγος) under the locked normaliser. Drift aborts with `FAIL_audit_normaliser_drift`. **Erratum (2026-04-28 night, caught at pre-stage time before any compression call)**: the original draft of this sentinel mistakenly preserved the final-sigma `ς` in the expected output and gave the count as 16 letters; the corrected expected output ends in `σ` (medial sigma) per the §2.1 fold rule and is 14 letters. The fix is a one-character documentation correction with zero substantive protocol impact; the run script's `_NORMALISER_SENTINEL_EXPECTED` constant matches the corrected value. Caught by `scripts/_mark1_peer_sizing.py` during pre-stage diagnostic.
4. **Compressor-version sentinel**: compressor versions logged in receipt; no version-pinning enforced (parallel to exp104).
5. **τ-stability sentinel**: bootstrap CV ≤ 0.30 per compressor (branch 4 of the verdict ladder).
6. **No-leak sentinel**: Mark itself (book 41) is excluded from the peer pool by construction. The peer-pool builder verifies `41` is not in `PEER_BOOK_NUMBERS`.

---

## 5. Honesty clauses

### 5.1 Pre-run sizing was an objective check, not a fishing expedition

If pre-run sizing reveals Mark 1 is too short OR has too few peers, the verdict is BLOCKED / FAIL_audit per the ladder. The chapter is **not re-rolled** to "find" one that meets the constraints. An amendment PREREG with a different chapter is required, parallel to the H59 → H59b → H59c chain.

### 5.2 No τ transfer from Arabic, Hebrew, or any prior language

Locked Arabic τ from `exp95c` is **NOT** used. Locked Hebrew τ from `exp104c` is **NOT** used. Calibration is from-scratch on Greek-NT-narrative peers. Each language's τ is independent.

### 5.3 No selective compressor reporting / no post-hoc K change

K = 2 is locked; all 4 compressors run; per-pair Δ values logged regardless of K-2 gate outcome. The receipt always reports K=1, K=2, K=3, K=4 recalls; the verdict applier reads K=2 only.

### 5.4 No claim about Mark 1's content, theology, or authorship

This PREREG tests only whether the F53 multi-compressor-consensus detector fires on single-letter substitutions of Mark 1's surface text. It does not address authorship, dating, theological content, or any other aspect of Mark.

### 5.5 Honest scope: Greek NT chapters share strong stylistic cohesion

The peer pool is Greek NT outside Mark. A PASS may partly reflect **NT-internal stylistic cohesion** (Mark, Matthew, Luke, John, Acts share Koine register and gospel-narrative genre conventions) rather than canon-detection per se. This is the same risk as in exp104 (Tanakh narrative as peer pool for Psalm 78). The within-canon stylistic cohesion is acknowledged as a confound; expanding the peer pool to Apostolic Fathers + Septuagint Greek narrative would isolate canon-detection from genre-detection but requires corpus acquisition and a separate amendment PREREG.

---

## 6. Reproduction recipe

```powershell
# 1. Verify Greek corpus
python scripts/_verify_corpus_lock.py
# 2. Run pilot
python -m experiments.exp104d_F53_mark1.run
# 3. Audit
python scripts/integrity_audit.py
python scripts/zero_trust_audit.py
```

Receipt path: `results/experiments/exp104d_F53_mark1/exp104d_F53_mark1.json`.
Live progress (Python-managed flushing): `results/experiments/exp104d_F53_mark1/progress.log`.

---

## 7. Cross-references

- Hebrew chapters in same chain: `experiments/exp104_F53_tanakh_pilot/` (Psalm 19 BLOCKED), `experiments/exp104b_F53_psalm119/` (Psalm 119 FAIL_audit_peer_pool_size, FN10), `experiments/exp104c_F53_psalm78/` (Psalm 78 PENDING)
- Quran-side F53: `experiments/exp95c_multi_compressor_adiyat/` (Q:100 PASS_consensus_100)
- Quran-side F54 retraction: `RETRACTIONS_REGISTRY.md` Category L, R53
- Phase-3 cross-tradition framework: `experiments/expP4_F53_cross_tradition/PREREG.md` (BLOCKED stub from patch G; H59d is the first chapter-level instantiation in Greek)
- PAPER §4.47.5 (chain narrative)
- HYPOTHESES_AND_TESTS.md row H59 (will be extended to H59d on receipt write)

---

## 8. Status at PREREG-lock time

- `run.py` does **not** exist at this PREREG's hash-lock time, by design.
- **Pre-staged only**; the run is intended to be launched **after** `exp104c_F53_psalm78` completes (regardless of H59c verdict) so that the H59 amendment chain has clean sequential audit timestamps.
- Implementation note for `run.py`: the cleanest implementation is a thin wrapper around `experiments/exp104_F53_tanakh_pilot/run.py` that overrides only `_load_chapters()`, `_normaliser()`, and `_alphabet()` — same approach as `exp104b` / `exp104c` use to inherit from `exp104`. The Greek loader must parse OpenGNT v3.3 CSV using the column-mapping documented in §2.1.

---

## 9. Frozen-time fingerprint

This document's SHA-256 is computed **after** all text above is final and **before** any Greek compression call is issued. The hash is written to `experiments/exp104d_F53_mark1/PREREG_HASH.txt`. **No `run.py` exists at the time of this PREREG-lock**, by design. When `run.py` is added, its `_PREREG_EXPECTED_HASH` must match this file's hash; mismatch invalidates the run.

**Estimated wall-time when run is launched**: by parallel reasoning to exp104c (Hebrew Psalm 78, 2,384 letters, ~155 min total at the observed Python-NCD compute rate of ~353 _per_compressor_deltas calls / minute on this machine), Mark 1 (~3,500–4,500 letters → ~73,500–94,500 single-letter variants) will likely require 220–280 min wall-time end-to-end. The constant is target-chapter-letter-count × 21 substitutions per position; Greek's 24-letter alphabet means 23 substitutions per position vs Hebrew's 22 (21 substitutions per position), a marginal 10 % uplift.
