# exp105_harakat_restoration — Pre-registration

**Frozen**: 2026-04-22 (before any run).
**Hypothesis ID**: H37 — A diacritic-restoration edit-detection channel (R13) operates outside the 28-letter rasm and closes the voiceless-emphatic-stop blind spot (ط↔ت, ق↔ك) that R12 / gzip NCD cannot recover under any compressor tested in `exp103`.
**Parent experiments**:
- `exp41_gzip_formalised` (R12 γ = +0.0716, 28-letter rasm, length-audited)
- `exp43_adiyat_864_compound` / `exp94_adiyat_864` (R12 fires on 99.07% of Adiyat 864 variants at ctrl-p95)
- `exp54_phonetic_law_full` (LAW_CONFIRMED: detection rate per class = 0.007265·d_hamming − 0.002388; **E3 ط↔ת = 0/848, E5 ق↔ך = 0/1211 in full mode exp46**)
- `exp95_phonetic_modulation` (`FAIL_ctrl_stratum_overfpr`: phonetic-distance-modulated R12 thresholds cannot recover these misses because NCD is phonetic-distance-blind)
- `exp103_cross_compressor_gamma` (`FAIL_not_universal`: four universal compressors all hit the same d=1 floor on the 28-letter rasm; CV(γ) = 2.95)

## 1. Motivation — why R12 provably cannot close the d=1 gap

Per `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PREREG_GAMMA_KOLMOGOROV.md:89-109` §2.5 and `@c:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp103_cross_compressor_gamma\exp103_cross_compressor_gamma.json`, the Quran-indicator γ on the 28-letter consonantal rasm has CV(γ) = 2.95 across {gzip, brotli, zstd-ultra, bzip2} — two compressors yield γ > 0, two yield γ < 0. By Cilibrasi–Vitányi asymptotic consistency `NCD_Z → NCD_K`, this cross-compressor disagreement is the **Kolmogorov floor of the 28-letter rasm**, not a compressor-specific artefact. `exp95`'s FAIL verdict confirmed that stratifying the same R12 detector by phonetic distance cannot move the floor — the input is unchanged.

Any detector that closes this gap must therefore **leave the 28-letter rasm** and consume information stripped out of it. Two natural extensions exist:

1. **Morphological / semantic** (expensive): char-LM or BPE-LM on pre-Islamic poetry, 2–6 weeks GPU.
2. **Diacritic** (cheap, immediate): the harakat layer that `src/raw_loader.py:62` strips via the `_AR_DIAC` regex. `H(harakat | rasm) = 1.964 bits` per letter is already a locked scalar (`@c:\Users\mtj_2\OneDrive\Desktop\Quran\results\integrity\results_lock.json`, corpus-level, cited at `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\DEEPSCAN_ULTIMATE_FINDINGS.md:67`), but nobody has operationalised it as a per-edit detection channel.

This experiment builds the minimal R13 channel, benchmarks it on Adiyat-864, and measures specifically whether it recovers the 8 exp94 misses — 7 of which are concentrated at `d_hamming ∈ {1, 2}` per `@c:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp95_phonetic_modulation\exp95_phonetic_modulation.json:110-200` stratum audit.

## 2. Formula (pre-registered)

For a canonical word `w_c` and an edited word `w_e` (single letter change in the consonantal rasm):

```
rasm(w)     = strip diacritics + fold hamza + ة→ه + ى→ي
              (byte-equal to src/roots.py::_norm_word, no lemma truncation)

analyses(r) = CamelTools Analyzer.analyze(r), the same MSA morphological
              analyser that src/roots.py uses for H_cond in features_5d.
              Returns a list of candidate analyses; each has a `diac`
              field (full diacritized surface form) and a `root` field.

plur_diac(r) = argmax_{d} count_i(analyses(r)[i]['diac'].replace('#','') == d)
               i.e., the plurality-voted diacritization, ties broken
               lexicographically. Empty string if analyses(r) is empty.

n_an(r)      = len(analyses(r)).

lev(a, b)    = standard Levenshtein edit distance on two unicode strings.
```

**R13 raw score for a single word-edit** (canonical word `w_c` vs. edited word `w_e`):

```
s_R13(w_c, w_e) = lev( plur_diac(rasm(w_c)), plur_diac(rasm(w_e)) )
                  + alpha * max(0, n_an(rasm(w_c)) - n_an(rasm(w_e)))
                                 / max(1, n_an(rasm(w_c)))
```

with `alpha = len(plur_diac(rasm(w_c)))` so the analysis-collapse term scales to the same order as the Levenshtein distance. **This is the sum of two non-negative orthogonal signals**: (a) divergence of the reconstructed diacritization, (b) drop in number of valid morphological analyses (a non-word gives `n_an = 0`).

**R13 per-variant score** (aggregating over the whole surah for Adiyat-864; over the single edited word for ctrl calibration): `s_R13(variant) = s_R13(w_c_edited, w_e_edited)`. Only the word that was actually perturbed contributes; every other word contributes exactly 0 and is skipped.

**Calibration**: R13 fires iff `s_R13 ≥ τ_R13`, where `τ_R13 = p95(s_R13_ctrl_null)` from the same 4 000 ctrl-edit perturbation plan used in `exp41` / `exp94` / `exp95`.

**Orthogonality to R12**: `exp103` showed all four universal compressors read the same 28-letter rasm and hit the same d=1 floor. R13 reads `analyses(rasm(w))`, which depends on the **morphological dictionary** (a piece of prior knowledge learned from MSA corpora, totally outside the rasm-compression framework). Any edit that produces a non-word (or a word of a different wazn) gives a large `s_R13`, independent of byte-compression behaviour.

## 3. Evaluation protocol

**Step 0 — Sanity pre-load**. Import CamelTools `MorphologyDB.builtin_db()` + `Analyzer`. If import fails, emit `FAIL_cameltools_missing`. The existing `src/roots.py` uses exactly this analyser; the cache at `src/cache/cameltools_root_cache.pkl.gz` is irrelevant here (we need `diac`, not `root`), so this experiment will re-query the analyser uncached.

**Step 1 — Ctrl-null calibration** (4 000 ctrl-edits, 200 Arabic-ctrl Band-A units × 20 internal-letter perturbations). Byte-equal perturbation policy to `exp41` / `exp94` / `exp95`: non-initial / non-terminal letter in a non-boundary word of a non-terminal verse, replacement from `ARABIC_CONS_28 \ {original}`, uniform random. For each edit, identify the single perturbed word `w_e` and its canonical form `w_c`; compute `s_R13(w_c, w_e)`. Record all 4 000 values. Compute `τ_R13 = p95(s_R13_ctrl_null)` and its bootstrap 95 % CI (n_boot = 1 000).

**Step 2 — Adiyat-864 scoring**. Enumerate all 864 single-letter substitutions of Surah 100 v1 (byte-equal to `exp43`). For each variant:
- Identify the perturbed word (the word in verse 1 whose rasm changed).
- Compute `s_R13(w_c, w_e)`.
- Record `d_hamming(orig, repl)` from the exp95 PHONETIC_FEATURES table (for per-stratum audit, not used in the R13 threshold).
- `fires_R13 = (s_R13 ≥ τ_R13)`.
- Also load the 864 R12 fire-flags from the `exp94_adiyat_864.json` receipt and record the conjunction / union / exclusive rates.

**Step 3 — Voiceless-stop recovery audit**. This is the headline test. Restrict to variants where `orig ∈ {ت, ط}` AND `repl ∈ {ت, ط}` (E3 ط↔ת pair; expected n ≈ few across the 32 positions of v1) plus `orig ∈ {ك, ق}` AND `repl ∈ {ك, ق}` (E5 ق↔ך). Report the R13 fire rate specifically on these edits. exp54's LAW_CONFIRMED prediction is that R12 fires at ~0% on these; if R13 fires at ≥ 50 % and FPR at 5 %, the gap is closed.

**Step 4 — Per-stratum and per-d-hamming breakdown**. For each `d ∈ {1, 2, 3, 4, 5}`: report {n_variants, n_fired_R12, n_fired_R13, recall_R12, recall_R13, recall_union, recall_intersection}. The 8 exp94 misses should clump at low `d`; `exp95` FAILED to recover them; we measure whether R13 succeeds.

**Step 5 — Null calibration quality check**. Report the ctrl-null distribution summary: `{mean, sd, p95, max}`. If more than 5 % of ctrl-edits produce `s_R13 = 0` because CamelTools had no analyses for either form (`n_an(rasm(w_c)) == 0`), the null is saturated at zero and the threshold is unstable — emit a `PARTIAL_null_saturated` tag.

**Step 6 — Self-check**. Prereg hash and all integrity locks unchanged.

## 4. Pre-registered verdicts (evaluated in order)

| Code | Condition |
|---|---|
| `FAIL_cameltools_missing` | CamelTools import or `MorphologyDB.builtin_db()` fails |
| `FAIL_exp94_baseline_missing` | `exp94_adiyat_864.json` not on disk |
| `FAIL_null_saturated` | > 50 % of ctrl-null edits give `s_R13 = 0` (threshold unstable) |
| `PARTIAL_null_saturated` | 5 % < (ctrl `s_R13 = 0`) ≤ 50 % (threshold noisy; results are suggestive) |
| `PARTIAL_no_voiceless_lift` | on E3 ∪ E5 variants, R13 fire rate ≤ 20 % (no closure of the d=1 gap) |
| `PARTIAL_partial_voiceless_lift` | E3 ∪ E5 R13 fire rate ∈ (20 %, 50 %] |
| `PASS_closes_voiceless_gap` | E3 ∪ E5 R13 fire rate ≥ 50 % AND overall ctrl-p95 FPR ≤ 0.07 (measured on held-out ctrl subset) |
| `PASS_universal_edit_coverage` | PASS_closes_voiceless_gap AND union(R12, R13) recall on full 864 ≥ 0.999 (≤ 1 missed variant) |

**Expected outcome** (honest pre-run prediction):

| Scenario | Prior probability |
|---|---:|
| PASS_universal_edit_coverage | ~20% — optimistic; requires R13 to catch ~all of the 8 exp94 misses without introducing new misses at high-d strata |
| PASS_closes_voiceless_gap | ~40% — R13 is morphologically motivated specifically for emphatic↔plain swaps, so E3/E5 closure is likely |
| PARTIAL_partial_voiceless_lift | ~25% — CamelTools' ~63 % root agreement (§6.5 limitation 6) may leak through for some ط↔ת variants |
| PARTIAL_no_voiceless_lift | ~10% — possible if the Adiyat v1 perturbed word happens to be morphologically permissive under MSA |
| FAIL / edge cases | ~5% |

## 5. Honesty clauses

- **HC1 — CamelTools is MSA, not Quranic**. The analyser is trained on Modern Standard Arabic and has ~63 % gold-set agreement on root extraction (paper §6.5 limitation 6). Any edit that happens to produce a rare-but-valid MSA word — e.g., a 7th-century noun that survived into MSA with different semantics — will not fire R13 even if the Quranic reading would reject it. This is a **systematic ceiling, not a bug**; the honest claim is "R13 closes the d=1 gap to within the resolving power of the MSA morphological analyser", not "R13 is a complete edit detector".
- **HC2 — `diac` plurality is a lossy proxy**. CamelTools returns many analyses per word, often with different diacritizations that differ only in case-endings (marfū‘ / manṣūb / majrūr). The plurality-voted `diac` collapses this variation into a single string; a reviewer who wants the full joint distribution should read the raw analyses from the per-variant receipt.
- **HC3 — The `alpha * analysis-collapse` term is additive by choice**. An alternative weighting (product, max, or log) would give a different R13. The additive form is pre-registered here; any post-hoc reweighting would be a new experiment (exp105b).
- **HC4 — R13 is not a stand-alone classifier**. Unlike EL (a corpus-level Task-A classifier) or R12 (a population-level Task-B edit detector), R13 is scoped strictly to **single-letter edits with phonetic-distance ≤ 2 on the 28-letter rasm**. A PASS here does not claim R13 is a general-purpose detector.
- **HC5 — No lock modification**. No change to `results/integrity/`, `results/checkpoints/`, or any `phase_*.pkl`. Integrity `self_check_end` must pass.
- **HC6 — Ctrl-null policy identity**. The 4 000 ctrl-edits are byte-equal to `exp41_gzip_formalised` / `exp94_adiyat_864`: same SEED, same N_PERT_PER_UNIT, same perturbation policy. Any deviation would invalidate the threshold comparison with R12 at the same 5 % FPR.

## 6. Locks not touched

All new scalars tagged `(v7.9 cand.)`. No modification to any file under `results/integrity/`, `results/checkpoints/`, or `notebooks/ultimate/`. Integrity `self_check_end` must pass.

## 7. Frozen constants

```python
SEED = 42
N_PERT_PER_UNIT = 20
CTRL_N_UNITS = 200
FPR_TARGET = 0.05
BAND_A_LO, BAND_A_HI = 15, 100
ADIYAT_LABEL = "Q:100"
EXPECTED_N_VARIANTS = 864
ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
# CamelTools analyser: same DB as src/roots.py (MorphologyDB.builtin_db(), MSA).
# No cache: we need `diac`, not `root`, so src/cache/cameltools_root_cache.pkl.gz
# is irrelevant.
VOICELESS_STOP_PAIRS = [("ت", "ط"), ("ط", "ت"), ("ك", "ق"), ("ق", "ك")]
```

## 8. Provenance

- Reads (integrity-checked): `results/checkpoints/phase_06_phi_m.pkl` (for CORPORA verses — ctrl-null calibration + canonical Adiyat v1 diacritized form)
- Reads (receipt): `results/experiments/exp94_adiyat_864/exp94_adiyat_864.json` (R12 fire-flags per variant for union / intersection reporting)
- Reads (receipt, optional): `results/experiments/exp95_phonetic_modulation/exp95_phonetic_modulation.json` (per-variant `d_hamming` + exp94 miss locations)
- Imports: `camel_tools.morphology.{database, analyzer}` (system dependency, same as `src/roots.py`)
- Writes only: `results/experiments/exp105_harakat_restoration/exp105_harakat_restoration.json` + `self_check_*.json`
- Paper hook: candidate `docs/PAPER.md §4.25a` — *R13: Diacritic-restoration edit-detection channel orthogonal to R12*; also a `§4.36` addition to the Fisher stack as a **fourth** layer.

---

*Pre-registered 2026-04-22. Prereg hash is computed at run-time and stored in the output JSON under `prereg_hash`. CamelTools availability is a hard gate; if import fails the experiment halts before any computation and emits `FAIL_cameltools_missing` with a non-zero exit code.*
