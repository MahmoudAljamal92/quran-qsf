# E18 — Reed–Solomon-like Error-Correction Search

**Verdict**: **RS_STRUCTURE_DETECTED**
**Seed**: 42  ·  **Permutations**: 200  ·  **Max bytes / surah**: 2048
**GF(2⁸) primitive poly**: 0x11d  ·  **Primitive element**: 0x02

## Grid & Results

| (n, nsym) | # surahs | Fisher χ² | df | Fisher p | #sig @0.05 | #sig @0.01 | t (s) |
|---|---|---|---|---|---|---|---|
| (15, 4) | 114 | 114.9 | 228 | 1.000e+00 | 1 | 0 | 30.6 |
| (15, 6) | 114 | 88.3 | 228 | 1.000e+00 | 0 | 0 | 45.6 |
| (31, 8) | 114 | 515.6 | 228 | 0.000e+00 | 35 | 12 | 108.7 |
| (31, 12) | 114 | 447.8 | 228 | 2.220e-16 | 23 | 13 | 164.0 |
| (63, 16) | 114 | 244.2 | 228 | 2.205e-01 | 7 | 4 | 458.6 |

**Best single config**: (n=31, nsym=8) at Fisher p = 0.000e+00.
**Min Fisher p over grid**: 0.0000e+00.
**Bonferroni-corrected**: 0.0000e+00 (grid size = 5).

## Interpretation

**RS_STRUCTURE_DETECTED (unexpected)** — Bonferroni-corrected p ≤ 0.01. This would be a historic positive result. Replicate with independent GF primitives (0x11b, 0x165), denser grid, and external validation before claiming.

## Method

- Per surah: byte-stream of UTF-8 encoding (capped at 2048 bytes; skipped if < 64 bytes).
- For each (n, nsym): segment into ⌊L/n⌋ non-overlapping codeword-length-n blocks.
- Compute all nsym RS syndromes per block: s_i = Σⱼ r_j · α^(i·j) in GF(2⁸), Horner-evaluated.
- Test statistic: mean L₁-norm of syndromes across blocks (lower = more codeword-like).
- Null: 200 random full-buffer permutations per surah.
- Left-tail p per surah → Fisher combine across surahs per config → Bonferroni across grid.

## Crosslinks

- Spec: `docs/EXECUTION_PLAN_AND_PRIORITIES.md` §E18
- Raw: `results/experiments/expE18_reed_solomon/expE18_report.json`
