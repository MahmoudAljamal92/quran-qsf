# E20 — Un-Derived Structural Constant Hunt

**Target**: `VL_CV_FLOOR = 0.1962` from `archive/CascadeProjects_legacy_builders/build_pipeline_p1.py:96`
**Verdict**: **DERIVED_ANALYTIC**

## A. Direct recomputation against canonical Quran text

| Verse-length measure | min (surah) | 2nd smallest | 3rd smallest | #<target | pct<target |
|---|---|---|---|---|---|
| chars_nospace | 0.1321 (S110) | 0.1954 (S106) | 0.2107 (S93) | 2 | 1.75% |
| chars_all | 0.1388 (S110) | 0.2091 (S93) | 0.2092 (S106) | 1 | 0.88% |
| words | 0.1506 (S110) | 0.1936 (S93) | 0.2478 (S63) | 2 | 1.75% |

Under **chars_nospace** the floor falls between the 2nd (0.1954, Surah 106) and 3rd (0.2107, Surah 93) smallest VL_CV values — it excludes exactly Surah 110 and Surah 106.

## B. Sensitivity sweep (chars_nospace)

| FLOOR | # excluded | # included |
|---|---|---|
| 0.10 | 0 | 114 |
| 0.11 | 0 | 114 |
| 0.12 | 0 | 114 |
| 0.13 | 0 | 114 |
| 0.14 | 1 | 113 |
| 0.15 | 1 | 113 |
| 0.16 | 1 | 113 |
| 0.17 | 1 | 113 |
| 0.18 | 1 | 113 |
| 0.19 | 1 | 113 |
| 0.20 | 2 | 112 |
| 0.21 | 2 | 112 |
| 0.22 | 3 | 111 |
| 0.23 | 3 | 111 |
| 0.24 | 3 | 111 |
| 0.25 | 3 | 111 |

**±10% neighborhood** [0.1766, 0.2158]: exclusion counts in this range = **[1, 2, 3]**.
Stability (single count over whole neighborhood): **False**.

## C. Closed-form derivation attempts

| Expression | Value | \|Δ\| | Rel. err. |
|---|---|---|---|
| `1/sqrt(26)` | 0.196116 | 0.000084 | 0.043% |
| `1/(2*pi*0.81)` | 0.196488 | 0.000288 | 0.147% |
| `2nd_smallest_Quran_VL_CV_chars_nospace` | 0.195434 | 0.000766 | 0.390% |
| `2nd_smallest_Quran_VL_CV_words` | 0.193649 | 0.002551 | 1.300% |
| `1/(2*e)` | 0.183940 | 0.012260 | 6.249% |
| `ln(6)/π²` | 0.181543 | 0.014657 | 7.470% |
| `1/(π+e/2)` | 0.222186 | 0.025986 | 13.245% |

Tightest analytic match (1/sqrt(26)): relative error **0.043%** (threshold: 0.1%).

## D. Downstream Hotelling T² sensitivity (Band-A Quran vs control pool)

| Drop | n | Hotelling T² |
|---|---|---|
| lowest-0 | 68 | 4190.0 |
| lowest-1 | 67 | 4070.3 |
| lowest-2 | 66 | 3978.9 |
| lowest-3 | 65 | 3858.9 |
| lowest-5 | 63 | 3663.8 |

T²-ratio over the sensitivity series: max/min = 1.14 → downstream_stable = **True**.

## Interpretation

**DERIVED_ANALYTIC (numerical coincidence flag)** — the tightest closed-form match is `1/sqrt(26) = 0.196116`, which differs from the target by **0.043%** — well under the pre-registered 0.1% tolerance. By the letter of the pre-registered criteria this qualifies as an analytic derivation.

**Caveat (honest reading)**: the integer 26 has **no canonical grounding** in Arabic or Quranic quantities — the Arabic abjad has 28 base letters, the Quran has 114 surahs, 6236 verses, etc. None of these yields `1/√n` ≈ 0.1962 except n=26, which is a numeric coincidence. The 2nd-smallest actual Quran VL_CV (Surah 106, 0.1954) sits 0.39% below target — still not a zero-distance derivation, but semantically grounded.

**Downstream sensitivity**: Band-A Hotelling T² ratio over `drop {0,1,2,3,5} lowest-VL_CV surahs` is **1.14** (stable). The outlier claim does not hinge on the exact value of the floor inside a wide plateau.

**Recommendation**: publish as an **empirical parameter with a numeric coincidence note**. Do NOT claim analytic derivation unless a semantically-grounded derivation can be attached to `1/√26` or a closer grounded alternative is found.

## Crosslinks

- Source constant: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\CascadeProjects_legacy_builders\build_pipeline_p1.py:96`
- Spec: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\EXECUTION_PLAN_AND_PRIORITIES.md` §E20
- SCAN surface: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\SCAN_2026-04-21T07-30Z\07_CASCADE_PROJECTS_ADDENDUM.md` §D10
- Raw: `results/experiments/expE20_constant_hunt/expE20_report.json`
