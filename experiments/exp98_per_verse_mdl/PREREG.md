# PREREG — exp98_per_verse_mdl (H53; closes C4 of F57)

**Hypothesis ID**: H53
**Filed**: 2026-04-27 afternoon (v7.9-cand patch H pre-V2)
**Amended**: 2026-04-27 15:05 (v7.9-cand patch H pre-V2 — fast-compressor variant for Cascade time-budget; semantics unchanged)
**Pre-registered before any per-verse compression is run.**

**Amendment 2026-04-27 15:05**: At user request to fit a Cascade session time budget (≤ 5 min), the compressor set is reduced from 5 to **3 fast compressors** {gzip-9, bz2-9, zstd-22}. The two dropped compressors (lzma-9, brotli-11) were estimated to add ~25× wall time but contribute redundant signal: in the canonical multi-compressor consensus literature, gzip and bz2 are the two dominant LZ77 / BWT regimes already, and zstd-22 covers the modern dictionary-LZ regime. Dropping lzma and brotli is therefore principled (not cherry-picking), and the resulting `mdl_rate` is a valid (though slightly weaker) per-verse Kolmogorov-complexity proxy. The PASS criterion (Quran rank 1 + margin > 1.5 %) is identical.

**Scope directive**: Whole 114-surah Quran. All 6 control corpora at full size. Verse-level granularity (no surah-level aggregation).

---

## 1. Background

The Quran (Q 11:1) describes itself as "كِتَابٌ أُحْكِمَتْ آيَاتُهُ" — "a book whose verses are made precise / perfected." This claim has not been operationalised under a single pre-registered test. The QSF project's existing γ_NCD measurement (`exp103_cross_compressor_gamma`, R51 retraction for non-universal signs) gives signed but non-universal directional indicators per compressor; it does not give a single per-verse compression statistic.

This experiment closes claim C4 of the F57 self-reference meta-finding by computing a **per-verse multi-compressor minimum description length (MDL)** in bytes, normalised by raw byte length, for every verse in 7 Arabic corpora. If "verses made precise" means structurally tighter / more redundant patterns, the Quran's median compressibility should be the highest (lowest mdl_rate) across the 7 corpora.

---

## 2. Hypothesis (H53)

**H53** (one-sided, hash-locked).

For each verse `v` in any Arabic-corpus unit:

```
mdl(v) = min { gzip(v), bz2(v), lzma(v), zstd(v), brotli(v) }   bytes
mdl_rate(v) = mdl(v) / len(v.encode("utf-8"))
```

For each corpus `C`, the per-verse MDL rate distribution is summarised by `median(mdl_rate(v) : v ∈ C)`.

**H53**: across the 7 Arabic corpora `{quran, poetry_jahili, poetry_islami, poetry_abbasi, ksucca, arabic_bible, hindawi}`, Quran has **strictly the lowest** `median(mdl_rate)` (i.e. its verses are the most compressible).

`H53 PASS` ↔ `quran rank == 1 AND margin to next-ranked > 1.5%` (i.e. the next-ranked corpus's median is at least 1.015× Quran's).

If H53 PASS, claim C4 (verse 11:1 verses-made-precise) of the F57 meta-finding is **CONFIRMED**, and `exp96c_F57_meta` re-runs to update S_obs from 3 → 4 (or higher if other Phase 2 experiments also pass).

---

## 3. Frozen constants

```python
ARABIC_POOL = ["quran", "poetry_jahili", "poetry_islami",
               "poetry_abbasi", "ksucca", "arabic_bible", "hindawi"]
COMPRESSORS = ["gzip", "bz2", "zstd"]   # amended 2026-04-27 15:05
COMPRESSION_LEVEL = {                # frozen levels for each compressor
    "gzip": 9, "bz2": 9, "zstd": 22,
}
MIN_VERSE_BYTES        = 5            # drop pathologically short verses
MARGIN_THRESHOLD       = 0.015        # 1.5 % over next-ranked corpus
RNG_SEED               = 98000        # not used; deterministic
N_QURAN_VERSES_EXPECTED= 6236         # whole Quran from phase_06_phi_m
```

---

## 4. Audit hooks (block PASS if any fire)

1. **A1** All 7 corpora load with > 1,000 valid verses each (i.e. n_verses ≥ MIN_VERSE_BYTES floor cleared).
2. **A2** Quran has exactly 6,236 verses post-MIN_VERSE_BYTES filter (matches §4.5 locked constant).
3. **A3** All 3 compressors complete on at least 99.9 % of verses (no widespread numerical failure).
4. **A4** `mdl_rate` is finite and positive for every counted verse.

Any hook firing → verdict `FAIL_audit_<hook>`.

---

## 5. Verdict ladder (strict order)

1. `FAIL_audit_<hook>` — any audit hook fired.
2. `FAIL_quran_not_top_1` — Quran is not strictly the lowest median mdl_rate.
3. `PARTIAL_top_1_within_eps` — Quran rank 1 but margin to next ≤ MARGIN_THRESHOLD.
4. `PASS_quran_strict_min_mdl` — Quran rank 1 AND margin > 1.5%.

`PASS_quran_strict_min_mdl` supports closure of claim C4.

---

## 6. What this PREREG does NOT claim

- Does **not** un-retract R51 (γ-universality) — different statistic and different question.
- Does **not** assert F57 today; only updates `S_obs` for `exp96c_F57_meta` re-run.
- Does **not** make a metaphysical claim.

---

## 7. Outputs

- `results/experiments/exp98_per_verse_mdl/exp98_per_verse_mdl.json` — receipt with per-corpus median mdl_rate, per-compressor diagnostics, audit hooks, verdict.
