# exp121_trigram_verse_reorder — Closing the F70 7 % gap (V3.12 PREREG)

**Hypothesis ID**: H76 (V3.12)
**Filed**: 2026-04-29 afternoon
**Status**: PRE-REGISTERED, NO RESULTS YET (PREREG hash locked at file seal)

## 1. Question

The F70 verse-reorder detector (exp117) achieved combined Form-4 recall =
0.930, which falls 0.020 short of the pre-registered 0.95 floor. The
remaining ~7 % of 2-verse swaps escape detection because they (a) preserve
verse-final letter (very common in Quran due to high ن concentration;
73 % of verses end in ن), AND (b) yield nearly-identical gzip-compressed
length, AND (c) preserve every inter-word bigram count under the 29-symbol
(28 letters + 1 space) alphabet.

This experiment tests whether a **trigram-with-verse-boundary-token**
detector closes that gap. The verse-boundary token forces every 2-verse
swap to perturb O(constant) trigrams crossing the swap points, regardless
of whether the verse-final letter or compressed length is preserved.

## 2. Definition of the Form-5 trigram detector (frozen at PREREG seal)

Define the **30-symbol alphabet**: 28 Arabic consonants (ا ب ت ث ج ح خ د ذ
ر ز س ش ص ض ط ظ ع غ ف ق ك ل م ن ه و ي) + space (` `) + verse-boundary
token `#`. Total `|Σ|` = 30.

Build the sūrah string: concatenate each verse's normalised skeleton (28
letters + space, joined by space), and insert `#` at the *start* and *end*
of each verse: `#v1#v2#v3#...#vn#`. Each verse is padded with `#` on both
sides; this guarantees that swapping verses i and j changes the trigram
content at exactly four `#` boundaries (the two pre-boundaries and two
post-boundaries of the swapped verses).

Compute the **trigram histogram** `H_3(text)` = Counter of all length-3
substrings of the boundary-tagged sūrah string. The Form-5 detector fires
on swap (i, j) iff:

  Δ_trigram_boundary(orig, swap) := (1/2) Σ_t |H_3(orig)[t] − H_3(swap)[t]| > 0

(L1 distance between trigram histograms, divided by 2.) This captures any
change to the inter-verse trigram structure.

## 3. Theorem (Form-5 sensitivity to verse-swap)

**Claim**: for any 2-verse swap (i, j) where verses v_i and v_j have
distinct skeletons, the boundary-tagged trigram histogram changes by
Δ_trigram_boundary ≥ 1.

**Proof sketch**: the trigram immediately following the opening `#` of
verse i in the original (`# c_1 c_2` where c_1, c_2 are the first two
characters of verse i) is replaced in the swap by `# c'_1 c'_2` where
c'_1, c'_2 are the first two characters of verse j. If the verses differ
in their first two characters, the trigram count changes; symmetric for
the closing `#`. With 4 boundary trigrams per swap and verse skeletons of
typical length ≥ 5, the probability of all 4 being preserved (verse
skeletons identical at first 2 + last 2 positions) is empirically near 0.

Empirical verification: `exp121_trigram_verse_reorder/run.py` measures
Δ_trigram_boundary on the same 79-sūrah × 100-swap battery as exp117 and
reports the per-swap recall.

## 4. Outcome variables (frozen)

- **form5_trigram_boundary_recall**: fraction of (sūrah, swap) pairs where
  Δ_trigram_boundary > 0
- **form6_combined_F1_or_F3_or_F5_recall**: union of EL-transition,
  gzip-fingerprint, and trigram-boundary detectors
- **form5_mean_delta**: mean Δ_trigram_boundary across all swaps
- **delta_recall_vs_F70_form4**: form6_recall − exp117 form4_recall
  (positive means trigram closes the gap)

## 5. Verdicts (locked decision rule, frozen at PREREG seal)

| Verdict | Condition |
|---|---|
| `PASS_F70_gap_closed_by_trigram_boundary` | form5 alone has recall ≥ 0.95 OR form6 combined recall ≥ 0.95 |
| `PARTIAL_F70_gap_partially_closed` | form6 combined > exp117 form4 (0.930) AND < 0.95 |
| `FAIL_F70_gap_not_closed_by_trigram` | form6 ≤ exp117 form4 (no marginal gain); FN14 added |

## 6. Inputs

- `results/checkpoints/phase_06_phi_m.pkl` (Quran 114 sūrahs with verses)
- Same battery as exp117: 79 sūrahs with ≥ 20 verses, 100 random 2-verse
  swaps each, SEED = 42

## 7. Frozen constants

- `SEED = 42`
- `MIN_VERSES = 20` (matches exp117)
- `N_SWAPS_PER_SURA = 100` (matches exp117)
- `RECALL_FLOOR = 0.95`
- `BOUNDARY_TOKEN = "#"`
- `ALPHABET_SIZE = 30` (28 consonants + space + #)

## 8. Honest scope

- This test does NOT extend the F71 universal-scope claim (cross-tradition
  trigram-with-boundary not tested); that would be a separate experiment.
- This test does NOT improve the letter-substitution detection (F55/F69
  remain authoritative for that scale).
- A pass at 0.95 closes the F70 verse-reorder gap; a fail logs the
  honest non-finding and the 7 % gap remains documented as a known
  limitation in `DETECTION_COVERAGE_MATRIX.md`.

## 9. PREREG seal

This file's SHA-256 hash is computed and written into the experiment
receipt as `prereg_hash`.
