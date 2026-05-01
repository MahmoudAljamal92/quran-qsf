# exp27 — Character-bigram sufficiency within words (H_char)

**Status**: scaffolded 2026-04-20, runnable end-to-end.
**Outputs**: `results/experiments/exp27_hchar_bigram/exp27_hchar_bigram.json`.

## Why this exists

External review (2026-04-20) identified an entire measurement axis that the
locked 5-D profile cannot see: **intra-word character statistics**. EL reads
terminal letters, CN reads opening words, VL_CV counts words, H_cond reads
root transitions between verses, T is their difference. None of them look
at what happens *inside* a word. A single letter change in verse 1 of
العاديات → الغاديات contributes roughly `1 / n_letters_in_surah ≈ 0.1–1%`
of the surah-level signal and disappears into noise.

The hypothesis is that at the character scale the Quran exhibits the same
**bigram-sufficiency** property already established at other scales:

| Scale                 | Metric                 | Quran vs ctrl (locked)        |
|-----------------------|------------------------|-------------------------------|
| Root (verse-boundary) | T11 H3/H2              | 0.096, rank 1/6 (paper §4.11) |
| Root (Markov order)   | T28 H2/H1              | d = −1.849 (paper §4.28)      |
| Verse-length          | F6 lag-1 ρ             | d = +0.877 (paper §4.17)      |
| Surah-order           | T8 path minimality     | 0/2000 perms beat canon       |

If the character-scale ratio is ALSO near zero AND ranks Quran extremal,
we have a **scale-invariant Markov-1 law** holding at **4 independent
scales simultaneously** — a Zipf-class universal-law claim.

## Protocol

- **Inputs**:  `phase_06_phi_m.pkl` (SHA-256 verified by `load_phase`).
- **Cohort**:  Arabic Band-A `[15, 100]` verses per unit (`BAND_A_LO = 15`,
  `BAND_A_HI = 100`, same as `src/extended_tests.py` T11).
- **Corpora**:
  - `quran` (68 Band-A surahs)
  - `ARABIC_CTRL` = poetry_jahili / poetry_islami / poetry_abbasi / ksucca
    / arabic_bible / hindawi — **hadith_bukhari intentionally quarantined**
    (pre-registered in `preregistration.json`; quotes Quran by design).
  - Cross-scripture: `iliad_greek` (24 books, no band filter because
    books are hundreds of lines each).
- **Normalisation**: strip Arabic diacritics (DIAC set from
  `src/features.py`), then keep only `.isalpha()` characters per word.
- **Intra-word only**: sequences use a `#` separator between words;
  any bigram or trigram containing `#` is **dropped** so cross-word
  dependencies cannot leak into the estimate.
- **Statistics**: pooled (T11 parity) *and* per-unit distributions.
  - `H_n = H(n-gram) − H((n-1)-gram)` via Shannon entropy on counts
    (byte-exact parity with `src/extended_tests.py::_entropy`).
  - Report H1, H2, H3, H2/H1, H3/H2 per corpus (pooled) and per unit.
  - Quran vs pooled Arabic ctrl: Cohen d, one-sided Mann-Whitney p
    (`alternative='less'`), percentile bootstrap 95% CI (n_boot = 2000,
    seed 42).

## How to run

```powershell
python -m experiments.exp27_hchar_bigram.run
```

Expected runtime: < 20 s on a modern laptop. Self-check at end.

## Interpretation

| Outcome                                             | Conclusion |
|-----------------------------------------------------|------------|
| Quran pooled H3/H2 ranks **1st (lowest)** AND per-unit Cohen d < −0.5 AND MW p_less < 0.01 | **Scale-invariant Markov-1 law confirmed at character scale.** Promote to paper §4.NEW as the 4th scale; feed exp28. |
| Quran ranks 1st but Cohen d in [−0.5, −0.2]        | Directionally confirmed but weak. Report in SUPPLEMENTARY, not headline. |
| Quran ranks 2nd or 3rd, no clean signal             | Law does **not** hold at character scale. Honest negative; still publishable as ceiling on the cascade. |
| Stream too short (n_chars < 50 for > half of units) | Methodological failure. Revisit normalisation. |

## What this experiment does NOT test

- PFD (articulatory feature distribution) — intentionally skipped per
  user decision 2026-04-20: Quran-specific phonology is already
  distinctive.
- H_tajweed rule entropy — intentionally skipped (same reason).
- Cross-word bigrams — by construction, excluded via `#` separator to
  keep the "within words" framing honest.

## Zero-trust audit

- `self_check_begin()` snapshots every protected file SHA-256 **before**
  any computation.
- `load_phase('phase_06_phi_m')` refuses to proceed if the checkpoint
  drifted from `_manifest.json`.
- Output is confined to `results/experiments/exp27_hchar_bigram/` by
  `safe_output_dir`.
- `self_check_end()` re-hashes everything and **raises `IntegrityError`**
  if any protected file changed; a `self_check_<timestamp>.json`
  receipt is written to the output folder.
- `python -m experiments._verify_all` at the end of the session
  confirms every receipt is PASS and no protected SHA drifted.
