# Pre-Registration: exp87_unified_probe

**Hypothesis**: H21 — Unified Two-Scale Law: I_total = macro_z + α × micro_z ≥ C

**Filed**: 2026-04-21 (before any computation)

---

## Claim

A single linear combination of macro structural score (5-D Mahalanobis LOO margin)
and micro phonetic score (4 tashkeel-based features: madd_density, sukun_entropy,
shadda_density, tashkeel_markov_entropy) maintains a stable floor across all 114
Quran surahs while falling below that floor for vocalized non-Quran controls.

## Data Sources (all read-only from archive)

- `archive/archive_old_jsons/LOO_TAU_MAX_results.json` — per-surah macro margins
- `archive/archive_old_jsons/QSF_S10_results.json` — per-surah micro composite
- `archive/helpers/tashkeela_fiqh_vocal.txt` — vocalized control (fiqh prose)
- `archive/helpers/poetry_vocal.txt` — vocalized control (classical poetry)

## Tests

### T1 — Alpha fitting (Quran-only, anti-circular)
Find α that maximises min(I_total) across all 114 Quran surahs.

### T2 — External control exclusion
Build pseudo-surahs from vocalized controls, compute micro features,
apply frozen (α, C) and measure exclusion rate.

### T3 — Hard failure rescue
Check whether macro hard-failures (surahs 73, 74, 106) are rescued by
elevated micro_z under the unified law.

## Pre-registered thresholds

- **STRONG** ⟺ external control exclusion ≥ 70%
- **MODERATE** ⟺ exclusion 40–70%
- **WEAK** ⟺ exclusion < 40% (collapses to macro-only)

## Falsifier

If micro composite for controls has mean ≥ Quran mean, the micro axis
provides no discriminating power and the unified law is meaningless.

## Output

- `results/experiments/exp87_unified_probe/exp87_unified_probe.json`
- `results/experiments/exp87_unified_probe/self_check_*.json`
