# Ranked Findings Table — confidence × effect

Every testable paper claim, sorted from strongest to weakest by `composite = sqrt(confidence × effect)`.

- **Confidence %** — based on p-value robustness (p < 10⁻³⁰ → 99 %, p < 10⁻⁵ → 92 %, p < 0.05 → 65 %, n.s. → 15 %)
- **Effect %** — based on Cohen's d (d ≥ 10 → 95 %, d ≥ 3 → 75 %, d ≥ 1 → 50 %, d < 0.2 → 10 %) or equivalent for ratios
- **Composite** — geometric mean, 100 = maximum; 0 = falsified

| Rank | ID | Finding | Paper | Clean-data result | Verdict | Conf % | Eff % | Comp |
|:-:|:-:|---|---|---|:-:|:-:|:-:|:-:|
| 1 | D09 | Predictive classifier AUC (Quran vs Arabic ctrl) | AUC = 0.90 | AUC = 0.998, z = 128.5 | PROVED STRONGER | 100 | 100 | **100** |
| 2 | D10 | %T>0 Quran-unique tension | 24.3% | Quran 39.7%, controls max 0.10% | PROVED STRONGER | 100 | 95 | **97** |
| 3 | D14 | Verse-internal word order non-random | d = 0.470 | Quran gap = +5.80, 100% canon farther | PROVED STRONGER | 99 | 95 | **97** |
| 4 | D26 | Bootstrap Ω stability (pre-reg C) | ≥ 95% > 2.0 | 100% > 2.0; median = 10.0 | PROVED STRONGER | 100 | 90 | **95** |
| 5 | D11 | Multi-scale perturbation (letter/word/verse) | d ≈ 2.8–10 | Quran gaps +0.78/+2.48/+1.76 (93–100% canon farther); controls ≈ 0 | PROVED STRONGER | 97 | 92 | **94** |
| 6 | D02 | Φ_M Mahalanobis separation (Quran vs Arabic ctrl) | d = 1.93 | d = 6.34, δ = 0.99 | PROVED STRONGER | 100 | 85 | **92** |
| 7 | S1 | S1: Multivariate separation | max Φ_M | d = 6.34 | PROVED STRONGER | 100 | 85 | **92** |
| 8 | D27 | Abbasi discrimination (Quran vs Abbasi) | d = +1.93 | d = 7.95 | PROVED STRONGER | 100 | 85 | **92** |
| 9 | D28 | Tight-fairness retest | d 1.93 → 2.66 | Band A already length-matches; d = 6.34 | PROVED STRONGER | 99 | 85 | **92** |
| 10 | D07 | Scale-Free Ordering at all window sizes | p < 0.01 at W=8–20 | Fisher p = 1.1e-16 at W=10 (also W=5, 20) | PROVED STRONGER | 97 | 85 | **91** |
| 11 | D23 | Pre-registered adversarial canon-wins | 98.2% canon-wins | Quran 100%, Abbasi 60%, Bible 22% | PROVED (+ retracts F-05) | 97 | 85 | **91** |
| 12 | D24 | Φ_M 10-fold CV robustness | min d ≥ 0.5, max p < 0.01 | min d = 5.08, median = 6.89 | PROVED STRONGER | 85 | 85 | **85** |
| 13 | D22 | Root-Diversity × EL product | 0.559 Q vs 0.337 poetry (1.66×) | Q = 0.632 vs next-best 0.179 (3.5× lead) | PROVED STRONGER | 99 | 65 | **80** |
| 14 | D03 | EL rhyme rate Quran-unique | 0.727 #1 | Quran 0.707 vs next-best 0.156 (4.5× lead) | PROVED | 99 | 65 | **80** |
| 15 | D17 | Canonical path minimality | z = −8.76 (0th pctile) | z = -3.96, 0/2000 perms beat canon | PROVED | 92 | 65 | **77** |
| 16 | E3 | Harakat channel capacity (epigenetic E3) | non-maximal predicted | H(h|r) = 1.96 bits, redundancy = 58.2% | PROVED | 95 | 58 | **74** |
| 17 | S5 | S5: Path minimality (Shannon-Aljamal) | minimises Σd | z = -3.96, 0/2000 perms beat | PROVED | 92 | 60 | **74** |
| 18 | G1 | Gap 1: Heavy-tail Bennett bound | CLOSED | Hill α ≥ 1.8 on all 5 features | PROVED | 85 | 60 | **71** |
| 19 | G2 | Gap 2: 5-channel MI independence | CLOSED | Max normalised MI ≤ 0.3 | PROVED | 85 | 60 | **71** |
| 20 | D01 | Anti-Metric VL_CV (pool) | d = 2.96 | d = 1.40 pool (vs poetry d = 2.5) | WEAKENED | 100 | 50 | **71** |
| 21 | D04 | CN connective rate Quran-unique | 0.067 #1 | Quran 0.086 vs next-best 0.034 (2.5× lead) | PROVED | 97 | 50 | **70** |
| 22 | D08 | Markov unforgeability (bigram root LM) | 17.2× gap | Quran z = 44.9; poetry_abbasi z = 47.9 (higher) | WEAKENED | 85 | 55 | **68** |
| 23 | D16 | RQA Laminarity vs controls | d = −0.395 | vs poetry d = -14.1; vs Bible d = +0.96 | WEAKENED | 85 | 55 | **68** |
| 24 | S4 | S4: Bigram sufficiency H₃/H₂ | → 0 for Quran | Quran ratio = 0.222 (#1 lowest); next 0.258 | PROVED (partial S4) | 85 | 55 | **68** |
| 25 | D19 | H-Cascade cross-scale F | d = 2.07 | d = 0.76; hadith & ksucca exceed Quran | WEAKENED | 92 | 35 | **57** |
| 26 | D20 | Hierarchical Ω_master rank | 5.66 (20× ctrl) | Quran Ω = 7.89, ksucca 7.20 (9% margin) | WEAKENED | 80 | 35 | **53** |
| 27 | D06 | Turbo-code gain G_turbo | 1.72× #1 | Quran 1.644 (#1); next 1.628 (margin 1.0%) | WEAKENED | 65 | 25 | **40** |
| 28 | D25 | Meccan/Medinan both F > 1 (pre-reg B) | both F > 1 | F_M = 0.80, F_D = 0.84 | FALSIFIED | 65 | 15 | **31** |
| 29 | D05 | I(EL;CN) orthogonality at unit level | ≈ 0 | Quran I = 1.17 bits (HIGHEST); min ctrl 0.00 | FALSIFIED at unit level | 85 | 0 | **0** |
| 30 | D18 | Adjacent diversity percentile | 100th pctile | Quran at 10.6th pctile | FALSIFIED | 95 | 0 | **0** |
| 31 | D21 | Structural Forgery P3 rhyme-swap | Q 93% vs ctrl 36% | Q 32% vs Bible 60% (opposite direction) | NOT REPRODUCED | 40 | 0 | **0** |
| 32 | S2 | S2: Channel Orthogonality | I(EL;CN) → 0 | Falsified at unit level (D05 duplicate) | FALSIFIED | 85 | 0 | **0** |
| 33 | S3 | S3: Constrained entropy (H_cond max) | Quran #1 on H_cond | Quran H_cond = 0.87 (#3); ksucca 1.17 (#1) | FALSIFIED | 90 | 0 | **0** |
| 34 | G3 | Gap 3: Hessian PD closure | closed | Tautology: H = 2·Σ⁻¹ is PD by construction | FALSIFIED by math | 100 | 0 | **0** |
| 35 | G5 | Gap 5: γ(Ω) = a + b·Ω | closed | Algebraic identity | FALSIFIED by math | 100 | 0 | **0** |

## T24–T31 — re-tests of v10.10–v10.13 notebook findings (added 2026-04-18)

| Rank | ID | Finding | Notebook claim | Clean-data result | Verdict | Conf % | Eff % | Comp |
|:-:|:-:|---|---|---|:-:|:-:|:-:|:-:|
| A | T26 | Terminal position signal depth | d(−1)=1.14, d(−2)=0.82, depth=2 | d(−1)=1.43, d(−2)=2.40, d(−3)=0.65, depth=3 | PROVED STRONGER | 99 | 85 | **92** |
| B | T24 | Lesion dose-response (smooth) | smooth, HC peak 5–10% | EL drops 6→10→19→35→74% at 1/5/10/20/50% | PROVED | 97 | 75 | **85** |
| C | T31 | Fisher-metric curvature (smoothest manifold) | rank 10/10 lowest | curvature rank 1/8 lowest, volume rank 1/8 | PROVED (topological) | 90 | 70 | **79** |
| D | T25 | Info-geometry saddle point | 4/9 controls saddle | 7/8 corpora saddle (near-universal) | PROVED but LESS distinctive | 95 | 50 | **69** |
| E | T27 | Inter-surah structural cost | ratio 0.704, p ≈ 0 | ratio 0.856, p = 0.001 | SURVIVES (weaker) | 92 | 35 | **57** |
| F | T30 | RG flow (scale-invariance) | rank 10/10, NEGATIVE | α=0.85, rank 3/8 — still no scale invariance | NEGATIVE confirmed | 85 | — | **—** |
| G | T28 | Markov-order H₂/H₁ sufficiency (T12) | d = −1.85, p = 1.9e-6 | Q=0.111 vs ctrl=0.114, d = −0.03 | NOT REPRODUCED | 50 | 5 | **16** |
| H | T29 | φ_frac = 0.618 golden-ratio phase transition | φ ≈ 0.618, 3/3 criticality | φ_frac = −0.915 (not near golden) | NOT REPRODUCED | 50 | 0 | **0** |

**Breakdown**: T24, T25, T26, T27, T31 survive as positive findings (some stronger, some weaker). T30 correctly confirms the notebook's own NEGATIVE result. T28 and T29 do not reproduce on clean data — treat as retracted.

## Interpretation guide

- **Composite ≥ 90** — strongest evidence for Quran distinctiveness
- **Composite 75–90** — strong; would survive peer review
- **Composite 55–75** — real effect, needs careful framing
- **Composite 30–55** — weak or paper-overstated
- **Composite < 30** — falsified, retracted, or pure math tautology