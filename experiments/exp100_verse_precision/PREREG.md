# PREREG — exp100_verse_precision (H55; re-tests C4 of F57)

**Hypothesis ID**: H55
**Filed**: 2026-04-27 (v7.9-cand patch H pre-V2)
**Pre-registered before any analysis is run.**

**Scope directive**: Whole 114-surah Quran, all 7 Arabic corpora. This is a second-attempt operationalisation of C4 (11:1, "verses made precise") after the first attempt (exp98, per-verse multi-compressor MDL) failed with FN03.

---

## 1. Background

The Quran (Q 11:1) describes itself as "كِتَابٌ أُحْكِمَتْ آيَاتُهُ"
— "a Book whose verses have been made precise." The Arabic root
ح-ك-م (*uhkimat*) implies tight, unambiguous, firmly constructed.

**exp98** attempted to operationalise this via per-verse compression
ratio (gzip/bz2/zstd). It failed: the Quran ranked 4 of 7 (ksucca
news corpus led at 0.52 vs Quran 0.82). Compression ratio measures
*redundancy*, not *precision*. A news wire is repetitive (low
compression ratio) but not "precise" in the Quranic sense.

This experiment uses two better operationalisations:

1. **Semantic density**: unique root types per word (type-token ratio
   on Arabic roots, per verse, averaged across surah). "Precise"
   text packs more distinct meanings per word — fewer filler words,
   less repetition within a verse.

2. **Predictive tightness**: mean surprisal of each word given the
   previous words in the same verse, using a simple bigram word
   model trained on the corpus's own vocabulary. "Precise" text
   has low internal redundancy but high constraint — each word
   is tightly determined by context.

Both are computed per-verse and averaged per corpus unit (surah for
Quran, document/poem for controls), then the Quran's median is
ranked against all 7 corpora.

---

## 2. Hypothesis (H55)

**H55** (two-pronged, hash-locked).

For each corpus unit `u` (surah or control document), compute:

- **Metric A — Root density**: For each verse `v` in `u`, compute
  `RD(v) = n_unique_roots(v) / n_words(v)`. Average over all verses
  in `u` to get `RD(u)`. Rank the 7 corpus-level medians.

- **Metric B — Predictive tightness**: Train a corpus-internal bigram
  word model on all verses of corpus `c`. For each verse `v` in `u`,
  compute mean surprisal `S(v) = -1/(n-1) · Σ_{i=2}^{n} log P(w_i | w_{i-1})`.
  Average over all verses in `u` to get `S(u)`. Rank the 7
  corpus-level medians. LOWER surprisal = more predictable = more
  "tightly constrained."

**H55 PASS criterion**: Quran ranks **1st** (highest root density
AND lowest within-verse surprisal) among all 7 corpora on **at
least one** of the two metrics.

**H55 STRICT criterion**: Quran ranks 1st on **both** metrics.

---

## 3. Frozen constants

```python
CORPORA           = ["quran", "poetry_jahili", "poetry_islami",
                     "poetry_abbasi", "ksucca", "arabic_bible", "hindawi"]
MIN_VERSES        = 2           # units with fewer verses are dropped
MIN_WORDS_PER_V   = 3           # verses shorter than this are dropped
SEED              = 100000
BIGRAM_SMOOTHING  = 1e-8        # Laplace-like floor for unseen bigrams
```

---

## 4. Audit hooks

1. **A1** All 7 corpora load successfully with ≥ 10 units each.
2. **A2** Root extraction via CamelTools succeeds on ≥ 95 % of words
   (remainder mapped to `<unk>`; `<unk>` tokens excluded from RD
   numerator but included in denominator).
3. **A3** Per-corpus unit counts and verse counts are logged.
4. **A4** Effect size (Cohen's d) between Quran and next-ranked
   corpus is reported for each metric.

---

## 5. Verdict ladder

1. `FAIL_audit_<hook>`
2. `FAIL_both_metrics` — Quran is NOT rank 1 on either metric
3. `PARTIAL_one_metric` — Quran is rank 1 on exactly one metric
4. `PASS_H55_both_metrics` — Quran is rank 1 on both metrics

If verdict is PASS or PARTIAL, C4 is re-confirmed under the new
operationalisation, and FN03 remains as an honest record of the
first failed attempt.

---

## 6. What this PREREG does NOT claim

- Does **not** retroactively un-fail exp98 or erase FN03.
- Does **not** use compression ratios (those are a poor proxy for "precision").
- Does **not** claim "precision" is the only possible reading of أُحْكِمَتْ — this is one reasonable operationalisation among several.

---

## 7. Outputs

- `results/experiments/exp100_verse_precision/exp100_verse_precision.json`
  — per-corpus medians, ranks, effect sizes, audit hooks, verdict.
