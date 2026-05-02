# Pristine — self-audit report

**Generated**: 2026-05-02 11:39 UTC
**Verdict**: ✅ ALL CHECKS PASSED  (9/9 passing)

## What this audit verifies

1. **Corpus integrity** — quran_bare.txt SHA-256 matches the locked hash.
2. **Reference reproducibility** — every Quran reference shown by the app is recomputable from the corpus alone.
3. **No sharpshooter selection** — the code never selects per-surah subsets to define a Quran property.
4. **No learned weights** — Layers B and C are pure information-theoretic math; no sklearn fit, no neural nets, no learned classifiers.
5. **Corpus access** — only quran_bare.txt is read; no other corpus is touched at runtime.
6. **Match-formula honesty** — the percentage shown for each axis is the pure ratio `1 − |you − quran| / tolerance`, not a learned score.
7. **F69 theorem** — single-letter edits produce Δ_bigram ∈ [1, 2] on the canonical corpus (the central forensic guarantee of Layer C1).
8. **Verbatim lookup** — random Quranic verses are found verbatim by the corpus index.
9. **Examples reproduce expected outcomes** — preset texts trigger the expected layer responses.

## Detailed findings

### ✅ Check 1 — Corpus integrity

`quran_bare.txt` SHA-256 verified against the locked hash. Size: 781,176 bytes.

```
sha256 = 228df2a717671aeb9d2ff573002bd28d6b3f973f4bc7153554e3a81663d67610
locked = 228df2a717671aeb9d2ff573002bd28d6b3f973f4bc7153554e3a81663d67610
```

### ✅ Check 2 — Reference reproducibility

Recomputed every axis from quran_bare.txt + analytic helpers. All values are deterministic and reproducible from this corpus alone.

```
  H_EL         = 2.470720
  p_max        = 0.500962
  C_Omega      = 0.486054
  F75          = 6.280849
  D_max        = 2.336635
  d_info       = 1.636781
  HFD          = 0.958587
  Delta_alpha  = 0.686157
```

### ✅ Check 3 — No sharpshooter selection

Greps for per-surah median / hand-tuned-threshold / cherry-pick patterns in `pristine_lib/*.py` and `pristine.py` returned no hits. All references are whole-corpus pooled.

```
patterns checked:
  median.*per_surah
  per_surah.*median
  median.*per_chapter
  if\s+H_EL\s*<\s*1\.0
  if\s+p_max\s*>=?\s*0\.7
  \bcherry[ _]?pick
```

### ✅ Check 4 — No learned weights / external models

No imports of sklearn / torch / tensorflow / xgboost found, and no `.fit(` or `.train(` calls. Layers B and C are pure information-theoretic mathematics with no fitted parameters.

### ✅ Check 5 — Corpus access

Only `data/corpora/ar/quran_bare.txt` is referenced in the codebase. No other corpus (poetry, hindawi, ksucca, tanakh, NT, etc.) is touched at runtime — the app cannot 'leak' control-corpus content into its scoring.

### ✅ Check 6 — Match formula honesty

The per-axis match% follows the documented pure ratio `max(0, 100 * (1 - |you - quran| / tolerance))`. Tested at six boundary points; all match exactly.

### ✅ Check 7 — F69 bigram-shift theorem

On 200 random single-letter edits, Δ_bigram ∈ [1, 2] in 100.0% of cases. The F69 theorem holds on the canonical corpus, validating Layer C1's edit-detection guarantee.

```
min=2.00  median=2.00  mean=2.00  max=2.00
```

### ✅ Check 8 — Verbatim lookup soundness

50 random Quranic verses sampled. Every one is found verbatim in the corpus index. Layer A1 is sound.

### ✅ Check 9 — Examples reproduce expected outcomes

All 7 preset texts produce the expected Layer A outcome.

```
  verbatim_quran            -> exact
  one_letter_edit           -> fuzzy
  verse_swap                -> fuzzy
  muallaqa                  -> miss
  modern_prose              -> miss
  psalm_23                  -> skip_nonarabic
  tiny                      -> skip_nonarabic
```
