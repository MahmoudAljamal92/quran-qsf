# PREREG — exp101_self_similarity (H56; re-tests C5 of F57)

**Hypothesis ID**: H56
**Filed**: 2026-04-27 (v7.9-cand patch H pre-V2)
**Pre-registered before any analysis is run.**

**Scope directive**: Whole 114-surah Quran, all 7 Arabic corpora. This is a second-attempt operationalisation of C5 (39:23, "self-similar" / *mutashābih*) after the first attempt (exp97, multifractal Δα) failed with FN04.

---

## 1. Background

The Quran (Q 39:23) describes itself as "كِتَابًا مُتَشَابِهًا"
— "a Book that is mutashābih (self-resembling / consistent throughout)."
The root ش-ب-ه means "resembling"; the form *mutashābih* implies
internal self-consistency — parts resemble each other.

**exp97** attempted to operationalise this via multifractal
singularity spectrum width (MFDFA on verse-letter-count series).
It failed: Quran ranked 6 of 7, and the Hurst estimate was unstable
(audit hook A2 fired). MFDFA requires long stationary series and
is sensitive to trend; the Quran's 6,236 verses may be too short.

This experiment uses a more direct operationalisation:

**Cross-scale structural stability**: measure how stable the
Quran's 5-D fingerprint (EL, VL_CV, CN, H_cond, T) is across
surahs of very different lengths. If the Quran is truly
"self-similar," then short surahs (3–20 verses) should have a
similar fingerprint to long surahs (50–286 verses). In a
non-self-similar text, the fingerprint would drift with scale.

Specifically: split each corpus's units into **short** (below
median verse count) and **long** (above median), compute the 5-D
feature vector for each group's pooled verses, and measure the
**cosine distance** between the short-group centroid and long-group
centroid. The most self-similar corpus has the **smallest** cosine
distance (its parts look alike regardless of scale).

---

## 2. Hypothesis (H56)

**H56** (hash-locked).

For each corpus `c`:

1. Compute `features_5d(u)` for every unit `u` with ≥ 2 verses.
2. Split units into `SHORT` (below-median verse count) and `LONG`
   (above-median).
3. Compute centroid `μ_short = mean(features_5d(u) for u in SHORT)`
   and `μ_long = mean(features_5d(u) for u in LONG)`.
4. Compute cosine distance: `D(c) = 1 - cos(μ_short, μ_long)`.
5. Rank all 7 corpora by `D(c)` ascending (smallest = most
   self-similar).

**H56 PASS criterion**: Quran ranks **1st** (smallest D) among
all 7 corpora.

**H56 STRICT criterion**: Quran ranks 1st AND the effect size
(ratio of Quran D to next-ranked D) is ≥ 1.5×.

---

## 3. Secondary metric — Feature CV across units

As a robustness check, also compute for each corpus:

- **Intra-corpus CV**: for each of the 5 features, compute the
  coefficient of variation across all units; then take the mean
  of the 5 CVs. Lower mean CV = more internally consistent =
  more "self-similar."

Rank all 7 corpora. Report alongside the primary metric.

---

## 4. Frozen constants

```python
CORPORA           = ["quran", "poetry_jahili", "poetry_islami",
                     "poetry_abbasi", "ksucca", "arabic_bible", "hindawi"]
MIN_VERSES        = 2           # units with fewer verses are dropped
FEATURE_DIM       = 5           # [EL, VL_CV, CN, H_cond, T]
SEED              = 101000
```

---

## 5. Audit hooks

1. **A1** All 7 corpora load successfully with ≥ 10 units each.
2. **A2** Feature extraction succeeds on ≥ 99 % of units (no NaN/Inf).
3. **A3** Each corpus has ≥ 5 units in both SHORT and LONG groups.
4. **A4** Per-corpus unit counts, median verse counts, and
   SHORT/LONG split sizes are logged.

---

## 6. Verdict ladder

1. `FAIL_audit_<hook>`
2. `FAIL_not_rank_1` — Quran does not have smallest cosine distance
3. `PASS_H56_rank_1` — Quran has smallest cosine distance
4. `PASS_H56_strict` — Quran rank 1 AND ratio ≥ 1.5×

If verdict is PASS, C5 is re-confirmed under the new
operationalisation, and FN04 remains as an honest record of the
first failed attempt.

---

## 7. What this PREREG does NOT claim

- Does **not** retroactively un-fail exp97 or erase FN04.
- Does **not** use multifractal analysis (MFDFA was unstable).
- Does **not** claim *mutashābih* has only one meaning — this is
  the "structural self-resemblance across scales" reading.
- The secondary CV metric is a robustness check, not part of the
  primary verdict.

---

## 8. Outputs

- `results/experiments/exp101_self_similarity/exp101_self_similarity.json`
  — per-corpus cosine distances, ranks, CV metrics, audit hooks, verdict.
