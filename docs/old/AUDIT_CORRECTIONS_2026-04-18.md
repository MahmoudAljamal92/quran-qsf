# Audit Corrections — 2026-04-18 (v3.1 Extended)

This document is the **only** overlay you need to read on top of the restored v2 documentation. It lists every v10.10–v10.13 claim that the April 2026 forensic audit re-tested on **clean raw data** (no pickle checkpoint), with a survive/retract/retain verdict.

Everything else in `docs/QSF_COMPLETE_REFERENCE.md`, `docs/QSF_PAPER_DRAFT_v2.md`, `docs/QSF_REPLICATION_PIPELINE.md`, and the supporting MDs stands as originally written **except where this document states otherwise**.

Source of truth for numbers below: `results/CLEAN_PIPELINE_REPORT.json`, tests T24–T31, pipeline run 2026-04-18, 112.3 s, 31/31 tests passed.

---

## Summary table

| v10.10–v10.13 claim | Notebook value | Clean-data value | Verdict |
|---|---|---|---|
| **Lesion smooth degradation** (§12c) | EL drop 3.1 % @1 %, 15 % @5 %, heat-capacity peak at 5–10 % | EL drop **6.1 % @1 %**, **9.9 % @5 %**, **peak at 1 %** | ✅ **Survives (weaker profile)** — structure NOT irreducible; the peak shifts to lower damage under per-verse (not per-letter) damage model |
| **Info-geometry saddle point** (§12c) | Quran saddle (eigenvalue signs 4−/1+), 4/9 controls also saddle | Quran saddle confirmed (**4−/1+**), **7/8 corpora saddle** | ✅ **Survives BUT less distinctive than reported** — saddle structure is a near-universal feature of Arabic-text manifolds, not a Quran-specific signature |
| **Terminal position signal depth** (§12c) | d(−1)=1.14, d(−2)=0.82, d(−3)=−0.15 → depth 2 letters | d(−1)=**1.43**, d(−2)=**2.40**, d(−3)=**0.65** → depth **3 letters** | ✅ **Stronger than notebook** — signal extends one letter deeper (verse-internal morphological endings, e.g. -ين, -ون, -ات, plus preceding vowel pattern) |
| **Inter-surah structural cost** (§12c) | Mushaf cost 641.85, random 912.29, ratio 0.704, p ≈ 0 | Standardised-5D ratio **0.856**, p = **0.001** | ✅ **Survives but weaker** — different distance metric (5-D standardised vs 6-D raw) narrows the gap but canonical order is still significantly lower than random (n=1000 perms) |
| **Markov-order sufficiency T12** (v10.10) | Quran H₂/H₁ << controls, **d = −1.849**, p = 1.9×10⁻⁶ | Quran H₂/H₁ = **0.111**, controls = **0.114**, **d = −0.03** | ❌ **DOES NOT REPRODUCE** — the notebook effect was an artifact of the corrupted pickle's token-stream bundling; on clean roots the Quran has essentially the same Markov-order profile as controls |
| **Phase transition φ_frac = 0.618** (Phase 30) | Golden-ratio-adjacent φ with 3/3 criticality indicators | φ_frac = **−0.915**, not near 0.618; heat capacity IS peaked at medium length | ❌ **DOES NOT REPRODUCE** on the short/long-T median ratio implementation used here — consistent with v10.15's own downgrade of Phase 30 (§2.6d RG-Flow v2 already flagged this as "likely not a critical point"). Retain only the qualitative heat-capacity peak at medium scale. |
| **RG flow rank 10/10 (NEGATIVE)** (Phase 31) | Quran ranked LAST on RG-flow scale invariance | Quran α = **0.85** (trivial-block regime), rank **3/8** | ✅ **Still NEGATIVE** — Quran is NOT anomalously scale-invariant (α ≈ 1 = uncorrelated blocks). This confirms v10.12's honest-negative. |
| **Fisher-curvature rank 10/10 (lowest)** (Phase 32) | Quran has smoothest 5-D manifold | Quran curvature rank **1/8** (smoothest), volume rank **1/8** (largest) | ✅ **Survives** — Quran IS the smoothest local density in 5-D feature space. This is a genuine topological signature, but (as the v10.15 audit already flagged) NOT a superiority claim — a smooth manifold is what you'd expect from a highly-regularised signal. |

Final tally: **5 survive**, **1 survive as negative**, **2 do not reproduce** (T28 Markov-order, T29 phi_frac-as-golden-ratio).

---

## What this changes in the paper

### Add to `docs/QSF_COMPLETE_REFERENCE.md §12c` (or any future paper draft)

- **Saddle-point finding must include the 7/8 control count.** Call it "a distinctive-but-common topological signature in Arabic-text manifolds" — **do not** imply it is Quran-specific.
- **Terminal-position depth is now a 3-letter claim** with d(−1)=1.43, d(−2)=2.40, d(−3)=0.65 — stronger than originally reported.
- **Inter-surah-cost numerator drops from 0.70× to 0.86×.** Keep it as a positive finding but note the metric-dependence.

### Retract / demote

- **Drop Markov-order-sufficiency T12 entirely** from the PAPER unless someone can show the notebook's H₂/H₁ computation used a different token stream than clean CamelTools roots. Current evidence: coincidental effect on the corrupted token bundling.
- **Demote Phase 30 "phase transition" / φ_frac = 0.618 claim** from a flagship finding to a motivational remark. The golden-ratio motif is not confirmed on raw data; only the heat-capacity peak at medium length survives.

### Retain unchanged

- All T1–T23 verdicts from `docs/FINDINGS_SCORECARD.md` (April 17 audit).
- Lesion-smoothness, saddle-existence, terminal-depth, inter-surah-cost-lower-than-random, Fisher-smoothest-manifold — all five are now **clean-data corroborated**.

---

## How to reproduce

```
python -X utf8 -u -m src.clean_pipeline
```

Inspect:

```
results/CLEAN_PIPELINE_REPORT.json    # machine-readable, all 31 tests
results/CLEAN_PIPELINE_REPORT.md      # human-readable summary (auto-generated)
```

Every number in the table above is the value stored under `results.TXX_*` in the JSON, rounded to 2–3 decimals. Re-running on the same raw corpora will bit-reproduce identical numbers (seeds are fixed to 42 in `src/extended_tests3.py`).
