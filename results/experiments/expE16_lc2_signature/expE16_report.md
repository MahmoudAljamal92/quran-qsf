# expE16 — Memorization-Optimization Signature (LC2)

**Generated (UTC)**: 2026-04-23T20:19:34+00:00
**Seed**: 42  |  **Band-A**: [15, 100] verses
**Quran Band-A units**: 68  |  **Control Band-A units**: 2509

## Definitions

- `M(x) = H_cond(root_{i+1} | root_i)` on verse-final roots (from `src/features.py:h_cond_roots`).
  Lower M ⇒ more predictable transitions ⇒ more memorable.
- `V(x) = H(verse-final letter)` Shannon entropy (from `src/features.py:h_el`).
  Higher V ⇒ more positional variety ⇒ anti-forgetting.
- `L(x; λ) = M(x) − λ · V(x)`. Lower L ⇒ better LC2 optimization.

## Pre-registration

- **Null**: Quran median L-rank > 5th pct for every λ in {0.1, 0.5, 1, 2, 5}.
- **LC2_SIGNATURE**: median rank ≤ 5th pct for ≥ 3 λ values.
- **WEAK_LC2**: median rank ≤ 10th pct for ≥ 3 λ values.
- **NULL_NO_LC2**: fewer λ meet even the 10th-pct threshold.

## Verdict — **WEAK_LC2**

| λ | Quran median pct | Quran mean pct | frac in bottom 5% | L_q median | L_ctrl median |
|---|--:|--:|--:|--:|--:|
| 0.1 | 44.57% | 47.28% | 0.029 | 0.7822 | 0.8367 |
| 0.5 | 23.22% | 30.36% | 0.147 | 0.5009 | 0.7850 |
| 1.0 | 6.40% | 15.19% | 0.426 | 0.1383 | 0.7256 |
| 2.0 | 1.49% | 3.99% | 0.779 | -0.6358 | 0.6186 |
| 5.0 | 1.42% | 1.68% | 0.971 | -2.7268 | 0.3159 |

**λ-count at median ≤ 5th pct**:  2 / 5
**λ-count at median ≤ 10th pct**: 3 / 5

## Outputs

- `expE16_report.json` — per-λ numbers + verdict
- `expE16_lc2_plot.png` — (V, M) scatter + Quran pct vs λ curve