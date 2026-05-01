# PREREG — exp97_multifractal_spectrum (H52; closes C5 of F57)

**Hypothesis ID**: H52
**Filed**: 2026-04-27 afternoon (v7.9-cand patch H pre-V2)
**Pre-registered before any MFDFA computation is run.**

**Scope directive**: Whole 114-surah Quran. Per-corpus
single-time-series of length-of-verse counts (no band restrictions).

---

## 1. Background

The Quran (Q 39:23) describes itself as "كِتَابًا مُّتَشَابِهًا
مَّثَانِيَ" — "a self-similar (mutashābih), oft-repeated book."
"Self-similar across scales" is a precise mathematical concept: a
time series with **multifractal scaling** has a non-trivial
Hölder-exponent spectrum, and the **width** of that spectrum
quantifies how much the local scaling fluctuates. A monofractal
series has a narrow spectrum (one dominant Hölder exponent); a
multifractal series has a wide spectrum.

The QSF project's existing Hurst-ladder finding (`Supp_A_Hurst`,
H = 0.7) gives a single global Hurst exponent for the Quran but
does not measure the **Hölder spectrum**. A narrower spectrum than
all 6 controls — i.e. "more monofractal" — would
operationalise the 39:23 self-similarity claim.

---

## 2. Hypothesis (H52)

**H52** (one-sided, hash-locked).

For each Arabic corpus `C`, construct the time series of
verse-letter-counts in canonical reading order (Quran: 6,236 verses
in Hafs reading; controls: their natural unit ordering). Apply
**Multifractal Detrended Fluctuation Analysis (MFDFA)** with
moments `q ∈ [-5, 5]` to obtain the Hölder spectrum `f(α)`. Compute
the **spectrum width** as

```
Δα(C) = α_max(C) − α_min(C)
```

where `α_max` and `α_min` are the Hölder exponents at which `f(α)`
falls below `0.5`.

**H52**: among the 7 Arabic corpora `{quran, poetry_jahili,
poetry_islami, poetry_abbasi, ksucca, arabic_bible, hindawi}`,
Quran has **strictly the smallest** `Δα` (i.e. the narrowest
multifractal spectrum, equivalent to "most monofractal" /
"most self-similar across scales").

`H52 PASS` ↔ `Quran rank == 1 AND margin > 5 %`
(i.e. next-ranked corpus has Δα ≥ 1.05 × Quran's Δα).

If H52 PASS, claim C5 (verse 39:23 self-similar) of F57 is
**CONFIRMED**.

---

## 3. Frozen constants

```python
ARABIC_POOL = ["quran", "poetry_jahili", "poetry_islami",
               "poetry_abbasi", "ksucca", "arabic_bible", "hindawi"]
SERIES_VARIABLE      = "letters_28_per_verse"  # length of letters_28-skeletonised verse
Q_GRID               = list(range(-5, 6))      # 11 q-values: -5, -4, ..., 5
SCALE_GRID_MIN       = 16
SCALE_GRID_MAX_FRAC  = 0.25                    # max scale = 0.25 * series length
N_SCALES             = 16
DETREND_ORDER        = 1                       # linear detrend per window
F_ALPHA_THRESHOLD    = 0.5
MARGIN_FRACTION      = 0.05                    # 5 % over next-ranked Δα
RNG_SEED             = 97000
LIBRARY              = "MFDFA"                  # PyPI; or hand-rolled fallback
```

---

## 4. Audit hooks

1. **A1** All 7 corpora produce a finite, non-degenerate Δα.
2. **A2** Quran's H value (estimated as α at f(α)=max) is within ±0.15 of `Supp_A_Hurst = 0.7` from `results_lock.json`.
3. **A3** Series length ≥ 200 for every corpus (MFDFA stability).
4. **A4** Δα > 0.01 for at least 5 of 7 corpora (sanity: not all near-monofractal noise).

---

## 5. Verdict ladder

1. `FAIL_audit_<hook>` — any audit hook fired.
2. `FAIL_quran_not_top_1` — Quran is not strictly minimum Δα.
3. `PARTIAL_top_1_within_eps` — Quran rank 1 but margin ≤ 5 %.
4. `PASS_quran_strict_min_delta_alpha` — Quran rank 1 AND margin > 5 %.

---

## 6. What this PREREG does NOT claim

- Does not assert universal monofractal-class for sacred texts (Hebrew / Greek / Sanskrit untested; that's Phase 3).
- Does not stamp F57; only updates the `exp96c_F57_meta` partial count.

---

## 7. Outputs

- `results/experiments/exp97_multifractal_spectrum/exp97_multifractal_spectrum.json` — per-corpus Δα, full f(α) curve, audit hooks, verdict.
- Optional figure: `results/figures/exp97_falpha_curves.png`.
