# expP15_riwayat_invariance — Pre-Registration

**Frozen**: 2026-04-26
**Author**: v7.9-cand patch E sprint
**Status**: pre-registered before any data look

## Background

External feedback (PNAS-class) requested Riwayat invariance: are the
project's headline claims specific to the Hafs rasm, or do they survive
the 4 most-circulated alternative riwayat (Warsh, Qalun, Duri, Khalaf)?
The 5-D Φ_M and EL claims should hold across riwayat because the rasm
(consonantal skeleton) is shared; only diacritics + a small number of
graphemic differences vary.

## Hypothesis

**H1**: For each non-Hafs riwayat:
- |T²_riwayat − T²_Hafs| / T²_Hafs < 0.05 (within 5% relative drift)
- |EL_riwayat − EL_Hafs| / EL_Hafs < 0.02 (within 2% relative drift)
- Quran-vs-Arabic-ctrl AUC ≥ 0.97 (i.e., classifier still works)

## Pre-registered decision rule

| Outcome | Verdict |
|---|---|
| All 3 conditions met for all riwayat | `INVARIANT` (Hafs-claim → Uthmanic-skeleton-claim, +1 paper-class strengthening) |
| 2/3 conditions met | `NEAR_INVARIANT` (with caveats) |
| ≤ 1/3 conditions met | `RIWAYAT_DEPENDENT` (claims are Hafs-specific; significant retraction risk) |

## Protocol

1. Download Warsh, Qalun, Duri text from Tanzil.net (or GitHub mirror).
2. Save as `data/corpora/ar/riwayat/<name>.txt`.
3. Compute 5-D features per surah for each riwayat.
4. Compute T² + EL AUC vs the locked Arabic control pool.
5. Report drift table.

## Reproduction

```powershell
python -X utf8 -u experiments\expP15_riwayat_invariance\run.py
```
