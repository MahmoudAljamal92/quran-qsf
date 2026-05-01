# exp30 — R1 9-channel cascade on internal-letter substitutions

**Status**: scaffolded 2026-04-20, runnable end-to-end.
**Outputs**: `results/experiments/exp30_cascade_R1_9ch/exp30_cascade_R1_9ch.json`.

## Why this exists

`exp29_cascade_product_code` empirically showed that the Phi_M 5-D
channels (L1/L2/L3) are byte-exact invariant under single-letter
*internal* substitutions — a structural property of boundary-reading
features (EL reads terminal letters only, CN opens-words only, VL_CV
word-counts only, H_cond verse-final-roots only). P_composite collapsed
to 0.137 vs the feedback's 0.82–0.90 estimate.

The Ultimate-2 **R1 9-channel** pipeline includes three surah-level
channels that DO read internal letters:

- **A_spectral** — top-2 SVD ratio of a 34×34 letter-transition matrix.
- **C_bigram_dist** — L2 distance between canonical and tampered
  letter-bigram-count vectors (tautologically responsive to any letter
  edit).
- **E_ncd** — gzip normalised compression distance vs canonical.

And six more (B_root_bigram, D_wazn, F_coupling, G_root_trigram,
H_local_spec, I_root_field), some of which reach into internal word
structure via crude triliteral-root proxies.

`exp09_R1_variant_forensics_9ch` calibrated R1 on *random* letter swaps
at any position (50% fire rate at ≥ 3 channels, 45× above chance). That
calibration does not guarantee non-zero sensitivity for the restricted
"non-initial, non-terminal letter in non-boundary word of non-terminal
verse" class that exp29 measured. **This experiment measures it
directly.**

## Protocol

- **Input**: same Band-A [15, 100] Quran cohort (68 surahs) and sampled
  Arabic-ctrl pool (200 units out of 2 509) as exp29.
- **Perturbation**: byte-parity with `exp29._apply_perturbation` — pick
  non-terminal verse, non-boundary word (≥ 3 letters), non-initial
  non-terminal letter, substitute with a random distinct Arabic
  consonant from the 28-letter set.
- **N per unit**: 10 perturbations per Quran surah (680 total), 5 per
  ctrl unit (1 000 total). Smaller than exp29 because R1 is ~10–20×
  slower per call (SVD + gzip + LM log-prob on every perturbation).
- **Reference statistics**: R1's control-trained ref_bi
  (root-bigram counter) and root_lm (char 4-gram LM), loaded from
  `exp09_R1_variant_forensics_9ch.run._train_control_references(...)`
  — same protocol as the locked R1, same non-Quran corpora.
- **Null**: 95th percentile of the ctrl |delta_ch| distribution, per
  channel.
- **Detection rate p_ch**: fraction of Quran perturbations with
  |delta_ch| > ctrl q95.
- **Composite**: P = 1 − Π_k (1 − p_k) over the 9 channels.
- **Fire rate**: fraction of perturbations with ≥ 3 channels at
  |z| > 2, computed per exp09 definition (z-score relative to ctrl
  delta distribution mean/std).
- **Adiyat-specific sub-test**: A (ع→غ), B (ض→ص), C (both) injected
  post-normalisation into surah 100; per-channel delta and z reported.
  This row directly closes the "not directly tested for variant A"
  caveat in `docs/ADIYAT_ANALYSIS_AR.md §13.3`.

## How to run

```powershell
python -m experiments.exp30_cascade_R1_9ch.run
```

Expected runtime: **20–40 min** on a modern laptop. R1 computes SVD +
gzip + LM log-prob on every canonical and perturbed surah; 1 680
perturbations × 2 calls × 9 channels ≈ ~15 000 surah-level feature
evaluations.

## Interpretation rubric

| Fire rate (Quran) | Meaning | Action |
|---|---|---|
| < 0.10 | R1 is also mostly blind to internal edits | cascade framing confirmed dead across 5D + R1 |
| 0.10 – 0.30 | R1 catches some | report as "R1 partial sensitivity: X% at ≥3 channels"; Adiyat §13.3 rows flip from "not tested" to measured number |
| 0.30 – 0.60 | R1 meaningful contributor | paper §4.20 should cite it as the cascade's only non-blind layer |
| > 0.60 | matches feedback's 0.50 estimate and exp09's calibration | cascade rescued at the R1 layer |

Adiyat variants are reported separately with per-channel z-scores, so
the outcome for the specific ع→غ substitution in Al-Adiyat verse 1 is
visible even if the aggregate rate is low.

## What this experiment does NOT test

- Does not attempt R4 (char-LM), R11 (Φ_sym), or E_harakat. Those
  remain "not directly tested" in Adiyat §13.3 after this run.
- Does not compute R2 sliding-window — exp29 already showed Φ_M 5D is
  byte-exact invariant on internal edits, and R2 is Φ_M 5D on a 10-
  verse window.
- Does not run against Hebrew / Greek corpora.

## Zero-trust audit

Same as exp27/28/29: `self_check_begin/end` snapshots every protected
file SHA-256 pre and post run, `load_phase` refuses on drift, output
confined to `results/experiments/exp30_cascade_R1_9ch/` via
`safe_output_dir`.
