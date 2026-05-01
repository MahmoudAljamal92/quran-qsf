# E18 — Reed–Solomon-like Error-Correction Search (FINAL, with controls)

**FINAL verdict**: **NULL_UTF8_CONFOUND**

**Pre-registered falsifier**: *Bonferroni-corrected min fisher_p > 0.05 ⇒ NULL_NO_RS_STRUCTURE*

## TL;DR

The primary UTF-8 pipeline produced Fisher p = 0 at (n=31, nsym ∈ {8, 12}) —
raw-bytes reading: "Reed–Solomon structure detected".  We then ran the
**identical** pipeline on a compact Arabic alphabet (each letter mapped to a
single byte in 1..32, UTF-8 positional structure stripped).  The signal
**vanished**: p = 0.63 at (31, 8), p = 0.15 at (31, 12).  This is conclusive
evidence that the original signal was a UTF-8 encoding artefact, not content
structure.

## Results

### Arm A — Quran (UTF-8 bytes, primary pre-registered pipeline)

| (n, nsym) | units | Fisher χ² | df | Fisher p | sig @0.05 | sig @0.01 |
|---|---|---|---|---|---|---|
| (15, 4) | 114 | 114.9 | 228 | 1.000e+00 | 1 | 0 |
| (31, 8) | 114 | 518.9 | 228 | 0.000e+00 | 35 | 11 |
| (31, 12) | 114 | 455.1 | 228 | 0.000e+00 | 25 | 13 |
| (63, 16) | 114 | 243.2 | 228 | 2.334e-01 | 5 | 3 |

### Arm B — Quran (compact 32-letter alphabet; UTF-8 stripped)

| (n, nsym) | units | Fisher χ² | df | Fisher p | sig @0.05 | sig @0.01 |
|---|---|---|---|---|---|---|
| (15, 4) | 114 | 224.1 | 228 | 5.603e-01 | 5 | 2 |
| (31, 8) | 114 | 220.2 | 228 | 6.326e-01 | 4 | 0 |
| (31, 12) | 114 | 249.8 | 228 | 1.541e-01 | 10 | 2 |
| (63, 16) | 114 | 269.3 | 228 | 3.142e-02 | 5 | 3 |

### Arm C — Poetry (UTF-8, 1 unit; chunker issue)

| (n, nsym) | units | Fisher χ² | df | Fisher p |
|---|---|---|---|---|
| (15, 4) | 1 | 5.80 | 2 | 5.500e-02 |
| (31, 8) | 1 | 3.67 | 2 | 1.600e-01 |
| (31, 12) | 1 | 4.00 | 2 | 1.350e-01 |
| (63, 16) | 1 | 0.37 | 2 | 8.300e-01 |

## Decisive A-vs-B contrasts

| (n, nsym) | p (A: UTF-8) | p (B: compact) | B kills signal? |
|---|---|---|---|
| (31, 8) | 0.000e+00 | 0.633 | **True** |
| (31, 12) | 0.000e+00 | 0.154 | **True** |

## Interpretation

The primary UTF-8 pipeline showed Fisher p ≈ 0 at (n=31, nsym∈{8, 12}), but the SAME pipeline run on a compact 32-letter alphabet (every Arabic consonant mapped to a distinct byte, UTF-8 positional structure stripped) yields p = 0.63 at (31, 8) and p = 0.15 at (31, 12) — both NULL.

The signal was therefore **not** Reed–Solomon parity structure in the content.  It was driven by the lead-byte / continuation-byte interleave of UTF-8-encoded Arabic, which random byte-level shuffles destroy.  The pre-registered E18 claim is cleanly closed as NULL_UTF8_CONFOUND — the Reed–Solomon self-correcting-code claim is retired.

## Mechanism of the confound

UTF-8 encoding of Arabic text has a strict lead-byte / continuation-byte
interleave:

    Arabic letter ا  → bytes  0xD8 0xA7
    Arabic letter ب  → bytes  0xD8 0xA8
    space           → byte   0x20
    newline         → byte   0x0A

Under byte-level shuffling, the probability that position 2k lands a
continuation byte (0x80–0xBF) is uniform over the marginal distribution —
the ordered lead→continuation pattern is destroyed.  This changes the
GF(256) syndrome statistic distribution even though no "codeword" is
involved.  The compact-alphabet arm preserves every content byte but
places all of them in {1..32}, eliminating the positional high-bit /
low-bit interleave.  Signal vanishes → confound confirmed.

## What this retires

Pre-registered closure of the Reed–Solomon self-correcting-code hypothesis
for the Quranic text.  Combined with H20 (lexical ring composition, NULL)
and E19 (feature-level ring composition, NULL), all three "hidden-code"
style claims that circulate in popular literature now carry explicit
pre-registered null closures.

## Crosslinks

- Spec: `docs/EXECUTION_PLAN_AND_PRIORITIES.md` §E18
- Primary run: `results/experiments/expE18_reed_solomon/expE18_report.json`
- Controls run: `results/experiments/expE18_reed_solomon/expE18_controls_report.json`
- Final report: `results/experiments/expE18_reed_solomon/expE18_FINAL_report.json`
- E19 (ring composition, NULL): `results/experiments/expE19_ring_composition/expE19_report.md`
- RETRACTIONS_REGISTRY entries for Reed–Solomon / numerological codes
