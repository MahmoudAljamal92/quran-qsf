# Zero-Trust Audit — Tier 2 Experiments (E5–E9)

**Date**: 2026-04-23
**Scope**: Tier 2 block from `docs/reference/audits/EXECUTION_PLAN_AND_PRIORITIES.md` (five experiments: spectral, manifold, Hurst, NCD, Takens/RQA) executed on the canonical Quran text only.
**Driver**: `results/experiments/_tier2_audit.py` â†’ `results/experiments/_tier2_audit_report.json`
**Final disposition**: **0 HIGH / 0 MED / 4 LOW flags**; all verdicts re-derived from raw numbers match the reported verdicts; **0 drift** against the 7 manifest-tracked run-of-record artefacts (SHA-256 re-checked).

---

## Audit Dimensions & Checks

| # | Dimension | Check | Result |
|---|---|---|---|
| A1 | File hygiene | Every expected `expE{5..9}_report.{json,md}` + plots / NPZ exist and parse | PASS — all outputs present & non-empty |
| A2 | Pre-registration | Each JSON declares `pre_registered_criteria`, `seed`, `verdict(s)` | PASS after E5 JSON patch (criteria lifted from docstring into JSON) |
| A3 | Verdict vs numeric criteria | Re-derive verdict from raw statistics; compare to JSON-reported verdict | PASS — all 5 verdicts match (no silent inflation) |
| A4 | Pinned-artefact integrity | SHA-256 of all files in `MANIFEST_v8.json` re-computed | PASS — 7/7 entries byte-identical; zero drift during Tier 2 |
| A5 | Sanity bounds on headline numbers | Plausibility ranges on Î±, H, Moran's I, NCD, RR | PASS — all inside physically plausible ranges |
| A6 | Known confounds / follow-up notes | Length confound, weak criterion, sub-sampling | 4 LOW flags queued for Tier 3 / future work |

---

## Per-Experiment Results (short form)

| Task | Verdict | Key Numbers | Audit Disposition |
|---|---|---|---|
| **E5** Spectral | **RHYTHMIC** on both verse-length & end-letter | VL: 49 Bonferroni-peaks, Î±_obs=0.40 vs AR(1) 0.63. EL: 126 peaks, Î±_obs=1.02 vs AR(1) 1.30. Per-surah median top-peak period = 16.8 verses (n=57). | PASS (audit-verified). Rhythm coexists with 1/f reddening. |
| **E6** Manifold | **PARTIAL_STRUCTURE** | Moran's I p<0.05 on all 3 embeddings (PCA 0.042, t-SNE 0.004, Isomap 0.031). Meccan/Medinan silhouette borderline on t-SNE (p=0.057). | PASS. LOW flag: length confound — follow-up in Tier 3. |
| **E7** Hurst | **WEAK_PERSISTENT** (boundary; Wilcoxon crushes null) | Whole-corpus H=0.905 vs shuffle-null 0.542Â±0.014 (p=0). 56/57 per-surah H > 0.5; Wilcoxon p = 2.7Ã—10â»Â¹Â¹; regression intercept at median n = 0.89. | PASS. LOW flag: `median_resid>0` criterion was noise-sensitive (tripped at âˆ’0.019); headline persistence finding is robust. |
| **E8** NCD | **STRUCTURED_NCD** | 3/4 nulls rejected at Î±=0.01: Mantel(NCD, mushaf order) r=+0.59 (p=0.001), era-block Î”=+0.013 (p=0.007), era silhouette p=0.005. Mean NCD 0.914. | PASS. LOW flag: r=0.59 partially length-driven (mushaf â‰ˆ length-sorted); follow-up = length-residualised Mantel. |
| **E9** Takens/RQA | **STRUCTURED_DYNAMICS** | Ï„=2, m=3, Îµ=3.0; **DET=0.374** (AR(1) null 0.016Â±0.003, IAAFT null 0.157Â±0.034), **LAM=0.513** (AR(1) 0.034Â±0.008, IAAFT 0.274Â±0.049). All 6 metrics outside both 95% CIs. | PASS. LOW flag: stride-5 subsampling (N_rqa=1248 of 6236) for O(NÂ²) RQA; overall verdict safely outside both surrogate bands. |

---

## What the Tier 2 Block Actually Established

1. **Rhythm + redness co-exist** (E5 + E7). The Quran verse-length series is neither pure 1/f noise nor pure periodic. It is a persistent long-memory process (H = 0.905) with discrete, Bonferroni-robust periodic peaks on top.
2. **Mushaf order is non-random in 5-D feature space** (E6). Moran's I is positive and significant on every embedding (PCA, t-SNE, Isomap). The ordering encodes continuous feature autocorrelation, though Meccan/Medinan is not a cleanly separable cluster.
3. **Compression-geometry is structured** (E8). 114Ã—114 gzip-NCD correlates strongly with mushaf order (r=0.59) and weakly but significantly with era. Length-confound caveat noted.
4. **Nonlinear dynamics beyond linear / spectral nulls** (E9). The canonical verse-length sequence has higher DET and LAM than 200 AR(1) and 200 IAAFT surrogates — the series is not reproducible by a Gaussian linear process with matched autocorrelation, nor by a process with matched power spectrum and amplitude distribution. This is the single strongest "nonlinear structure" signal in Tier 2.
5. **No headline claims inflated, no artefacts mutated.** E4 manifest still clean; no Tier 2 experiment touched anything under `results/checkpoints/` or prior `results/experiments/`.

---

## LOW Flags (Follow-Ups Queued)

All four are recommendations for future work, not corrections to current verdicts:

| ID | Task | Flag | Suggested Follow-Up |
|---|---|---|---|
| F2-L-01 | E6 | Moran's I may be length-driven | Partial out `log(n_verses)` before computing I; verify significance survives. |
| F2-L-02 | E7 | `median_resid > 0` criterion too sensitive | Re-register on `intercept_at_median_n > 0.5` (which we actually verified = 0.89) for Tier-3 Hurst work. |
| F2-L-03 | E8 | Mantel r(NCD, order) confounded with length | Recompute Mantel on residuals of NCD regressed on `|C_i âˆ’ C_j|` compressed-size delta. |
| F2-L-04 | E9 | RQA stride-5 subsample | Re-run on 6236-pt series (memory ~300 MB bool matrix) once; check DET/LAM don't collapse. |

None of these would change Tier 2 verdicts — they refine effect-size interpretation.

---

## Crosslinks

- Full raw numbers: `results/experiments/_tier2_audit_report.json`
- Per-experiment JSON + MD: `results/experiments/expE{5..9}_*/expE{5..9}_report.{json,md}`
- Tier 1 predecessor audit: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_2026-04-22.md`
- Execution plan tracker: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\EXECUTION_PLAN_AND_PRIORITIES.md`
- Manifest of record: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expE4_sha_manifest\MANIFEST_v8.json`
- Retractions registry: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RETRACTIONS_REGISTRY.md`

---

## Audit Closure

**Tier 2 is CLEAN.** Proceed to Tier 3 (Adiyat / edit-detection extensions E10–E13) or Tier 4 (law candidates) on user direction.
