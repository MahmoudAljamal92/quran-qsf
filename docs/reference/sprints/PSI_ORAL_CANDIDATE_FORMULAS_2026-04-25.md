# Psi_oral candidate-formula pre-mortem — 2026-04-25 (SUPERSEDED)

> **SUPERSEDED 2026-04-25 evening**: The actual formula was already in `SUBMISSION_READINESS_2026-04-25.md §1.1`:
> **Ψ_oral = H(harakat|rasm) / (2 · I(EL;CN)) = 1.964 / (2 · 1.175) = 0.83574**.
> My prior search missed it because the Greek `Ψ` character is mojibake-encoded as `Î¨`/`I"` in the file. The candidate enumeration below is therefore moot. The formula is now implemented in `experiments/expX1_psi_oral/run.py`, reproduces the locked Quran value to drift 3×10⁻⁵, and **falsifies** the cross-tradition universal at n=1 (see `experiments/expX1_psi_oral/SUMMARY.md` and retraction #28 in `RANKED_FINDINGS.md`). This file is preserved for the diagnostic record only.

---

# Psi_oral candidate-formula pre-mortem — 2026-04-25

**Purpose**: when the reviewer responds with the explicit closed form for `Psi_oral`, we want to recognize it within seconds and validate it on Hebrew + Greek + Sanskrit + Pali + Avestan immediately, instead of round-tripping for clarification.

**Reviewer's claim**:
> Psi_oral = 0.836, derived from the two locked constants of the project.

**Locked-constant universe** (from `results/integrity/results_lock.json`, the only file the reviewer could plausibly mean):

| Symbol | Value | Source | Tolerance |
|---|---:|---|---|
| EL_med (3-Abrahamic mean rhyme rate, exp104 / Supp_A) | 0.7071 | `Supp_A_EL_universal` | 1e-4 |
| R_diacritic (3-Abrahamic mean diacritic-channel ratio, A2) | 0.7050 | `expA2_diacritic_capacity_universal` | 1e-3 |
| H_harakat_given_rasm (locked Quran channel cap.) | 1.964 bits | `T7_harakat_capacity` | 0.005 |
| H_unit (Quran surah-level Hurst, v7.8) | 0.9139 | `expP4_hurst_universal_cross_tradition` | 5e-3 |
| gamma_gzip (length-controlled NCD residual) | 0.0716 | `exp41_gamma_locked` | 5e-4 |
| Phi_M T_squared (Hotelling, headline) | 3557 | `T2_phi_m_T2` | varies |

The reviewer wrote "two locked constants", so EL_med + R_diacritic are the leading candidates. We tabulate every dimensionless closed-form combination of (EL, R) we can think of, with (EL, R) = (0.7071, 0.7050).

## Distance-from-target ranking

```
target = 0.836  (reviewer's claim)
EL = 0.7071
R  = 0.7050
```

| Formula | Value | |delta| | Rank |
|---|---:|---:|:---:|
| sqrt(R) | 0.83964 | 0.00364 | 1 |
| sqrt(EL) | 0.84089 | 0.00489 | 2 |
| (1 + R) / 2 | 0.85250 | 0.01650 | 3 |
| 1 - sqrt((1-R)*(1-EL))/2 | 0.85303 | 0.01703 | 4 |
| (1 + EL) / 2 | 0.85355 | 0.01755 | 5 |
| 1 - 0.5 * sqrt((1-EL)^2 + (1-R)^2) | 0.79214 | 0.04386 | 6 |
| EL^R | 0.78322 | 0.05278 | 7 |
| R^EL | 0.78101 | 0.05499 | 8 |
| log2(1 + EL + R) / log2(3) | 0.80146 | 0.03454 | 9 |
| harmonic mean (EL, R) | 0.70605 | 0.12995 | 10 |
| arithmetic mean (EL, R) | 0.70605 | 0.12995 | 11 |
| geometric mean sqrt(EL*R) | 0.70605 | 0.12995 | 12 |
| 1 - (1-EL)*(1-R) | 0.91359 | 0.07759 | 13 |
| EL * R | 0.49851 | 0.33749 | 14 |
| sqrt(EL + R) | 1.18843 | — | (out of [0,1]) |

**Best single-input fit**: `sqrt(R) = 0.8396` (off by 0.0036). But the reviewer said "two locked constants", so this is unlikely to be the literal answer.

**Best two-input fit**: `(1 + R) / 2 = 0.8525` (delta = 0.0165) and `1 - sqrt((1-R)(1-EL))/2 = 0.8530` (delta = 0.0170) are nearly tied, both involving R and a constant 1.

**No closed-form combination of (EL, R) yields 0.836 to better than 0.0036 absolute.**

## Three-constant candidates (in case "two" was loose)

If we allow a third locked constant:

| Formula | Value | |delta| |
|---|---:|---:|
| H_unit * EL = 0.9139 * 0.7071 | 0.64614 | 0.18986 |
| H_unit * R = 0.9139 * 0.7050 | 0.64430 | 0.19170 |
| (H_unit + R) / 2 | 0.80945 | 0.02655 |
| (H_unit + EL) / 2 | 0.81050 | 0.02550 |
| sqrt(H_unit * EL) | 0.80388 | 0.03212 |
| sqrt(H_unit * R) | 0.80268 | 0.03332 |
| (H_unit + EL + R) / 3 | 0.77533 | 0.06067 |
| 1 - (1 - H_unit)(1 - R) | 0.97460 | 0.13860 |

**Best three-input fit**: `(H_unit + EL) / 2 = 0.8105` (delta = 0.0255). Still no exact match.

## Other interpretations

The 0.836 might not be a closed-form constant at all but a measured statistic on a corpus we don't have. Reasonable candidates:

1. **AUC of EL alone on a specific 2-corpus comparison** that yields 0.836. We have no such comparison locked at exactly that value.
2. **EL applied to Hebrew + Greek pooled** rather than mean. Hebrew EL = 0.125, Greek NT EL = 0.206 — neither close.
3. **The R3 path-minimality success rate** across N corpora — currently 5/8 = 0.625, not 0.836.
4. **A Hurst-derived figure of merit**: Quran H_unit = 0.9139, mean across our 5 oral corpora is (0.9139 + 0.7861 + 0.6732 + 0.6323 + ?) / 4 = roughly 0.75 — not exactly 0.836 either.

## Recommended response to reviewer

Send a single short message:

> "We could not locate `Psi_oral` in the codebase or documentation; could you provide the explicit closed-form? We tested ~20 natural combinations of (EL, R, H_unit) — best single-input is sqrt(R) = 0.8396, best two-input is (1+R)/2 = 0.8525; none match 0.836 within the tolerance of our locked constants. Once the formula is known we can validate Psi_oral on Hebrew, Greek, Pali, Vedic, Avestan within ~1 hour."

## Validation plan when formula arrives

1. Implement `psi_oral(corpus)` in `src/features.py` per the reviewer's formula.
2. Compute on the 7 corpora available: Quran, Hebrew, Greek NT, Iliad, Pali_MN, Rigveda, Avestan Yasna.
3. Pre-register the threshold the reviewer claims it must clear.
4. Write `experiments/expP4_psi_oral_universal/run.py` mirroring the structure of `expP4_cross_tradition_R3`.
5. Report SUPPORT / NO_SUPPORT verdict with BH-corrected p-values.

ETA from formula → verdict: ~ 1 hour.

---

*Generated 2026-04-25, derived numerically from `results/integrity/results_lock.json` constants. No new measurements; pure algebraic enumeration.*
