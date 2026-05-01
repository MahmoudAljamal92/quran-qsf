# expP16_maqamat_hariri — Pre-Registration

**Frozen**: 2026-04-26
**Author**: v7.9-cand patch E sprint
**Status**: pre-registered before any data look

## Background

The single highest-leverage external test of the §4.40-§4.41 EL one-feature
law is whether Quran's EL ≈ 0.71 / ن-rate ≈ 0.50 distinguish it from
**Arabic rhymed prose (saj‛)**. Maqamat al-Hariri (50 maqāmāt by Abū
Muḥammad al-Qāsim al-Ḥarīrī, d. 1122) is the canonical example of saj‛
and the strongest natural challenger to the Quran's claim of unique
terminal-letter concentration in Arabic prose.

## Hypothesis

**H1 (strong)**: EL_Maqamat < 0.40 (i.e., even the strongest natural
saj‛ corpus does not reach the Quran's EL = 0.70 territory).
**H2**: ن-rate(Maqamat) < 0.20 (less than half of Quran's 0.50).
**H3**: AUC of EL classifier (Quran vs Maqamat) ≥ 0.95.

## Pre-registered decision rule

| Outcome | Verdict |
|---|---|
| EL_Maqamat < 0.40 AND p(ن|Maqamat) < 0.20 AND AUC ≥ 0.95 | `QURAN_DISTINCT_FROM_SAJ` |
| EL_Maqamat ≥ 0.40 OR p(ن|Maqamat) ≥ 0.30 | `SAJ_PARTIALLY_OVERLAPS` (qualifies §4.40 claim significantly) |
| AUC < 0.85 | `EL_LAW_FAILS_VS_SAJ` (would retract the §4.40.4 EL Simplicity Law) |

## Protocol

1. Download Maqamat al-Hariri Arabic text from Hindawi.org or Wikisource
   (public domain).
2. Parse to verses (each maqāmā has clear paragraph breaks; saj‛ verses
   are typically delimited by `.` or rhyme-line breaks).
3. Compute EL, ن-rate, 5-D features.
4. Compute Quran-vs-Maqamat AUC under the §4.40.4 boundary.

## Reproduction

```powershell
python -X utf8 -u experiments\expP16_maqamat_hariri\run.py
```
