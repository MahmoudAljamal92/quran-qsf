# PREREG — exp110_phi_master_xtrad: 3-term Φ_master cross-tradition replication

**Status**: SEALED 2026-04-29 morning, v7.9-cand patch H V3.8.
**Hypothesis ID**: H65.
**Pairs with**: F58 (`exp96a_phi_master`, Arabic-internal Φ_master = 1,862.31 nats; locked) + F63 (`exp109_phi_universal_xtrad`, cross-tradition Quran rhyme-extremum; PASSED with 0/10,000 perm null).
**Author intent**: extend F58 from Arabic-internal to cross-tradition by computing a 3-term portable Φ_master on the 6 cross-tradition real-verse-only corpora used in F63's R1 robustness check.

---

## 0. Honest disclosure (pre-run, locked at PREREG seal)

1. **The full 6-term Φ_master is not portable.** Φ_master = sum of 6 mutual-information terms each weighted by a non-redundancy factor; 3 of the 6 terms (CN-rate, root-bigram entropy, hadith-style discourse markers) require Arabic-specific morphology and are NOT portable to non-Arabic traditions. We compute the 3 portable terms only: I(EL; verse), I(VL_CV; verse), I(p_max; verse) — derived from the same EL / VL_CV / p_max scalars already in F63.

2. **This is a CONFIRMATORY-REPLICATION expecting a FAIL_quran_not_argmax verdict**. Sizing diagnostic (`scripts/_phi_master_xtrad_sizing.py`, receipt `results/auxiliary/_phi_master_xtrad_sizing.json`) was executed BEFORE this PREREG was sealed and revealed: **Quran is NOT the 3-term Φ_3 extremum**; observed Φ_3 = 0.1929 nats ranks 3/6 (behind Pāli at 0.2832 and Hebrew Tanakh at 0.2177). The per-feature breakdown shows the Quran is rank 1 on MI(EL) and MI(p_max) (both = 0.0838 nats — Quran's rhyme distribution is the most separable from the rest of the cross-tradition pool on rhyme features), but is mid-pack on MI(VL_CV) = 0.0253 nats (Pāli at 0.1328 dominates because its sutta-length distribution is highly bimodal). The 3-term portable Φ_3 thus collapses to a VL_CV-dominated statistic on which Quran is NOT extremum. We pre-register the FAIL_quran_not_argmax verdict and run the experiment to (a) lock the negative result formally as FN12 in `RETRACTIONS_REGISTRY.md`, (b) provide the per-feature MI breakdown which RECONFIRMS F63's claim that "the Quran's cross-tradition distinctiveness lives specifically on the rhyme axis", and (c) demonstrate that simple aggregation of universal features does NOT preserve Quran-distinctiveness — the rhyme-specific finding is structural, not aggregable.

3. **No new data, no new normalisers, no new alphabets.** All corpora, normalisers, and unit definitions are byte-exact inherited from F63's R1 audit (`scripts/_audit_f63_real_verse_only_perm.py`). No tuning loop is permitted.

---

## 1. Question

Of the 6 cross-tradition canonical religious texts (Quran, Hebrew Tanakh, Greek NT, Pāli DN+MN, Avestan Yasna, Arabic Bible), is the Quran the **3-term Φ_master extremum**?

3-term Φ_master(corpus) = MI(EL_per_unit; corpus_indicator) + MI(VL_CV_per_unit; corpus_indicator) + MI(p_max_per_unit; corpus_indicator)

Computed via discretised mutual information (5-bin equal-width on each feature; corpus indicator = 1 for that corpus, 0 for all others; nats; non-negative).

Higher Φ_master = the corpus is more separable from the rest of the cross-tradition pool on the structural feature axes.

---

## 2. Data — locked

Inherited byte-exact from F63 R1 (`results/auxiliary/_f63_real_verse_only_perm.json`):

- quran (114 surahs, real ayat) — SHA-256 prefix `228df2a7…`
- arabic_bible (1,183 chapters, Smith Van Dyke; PUBLIC DOMAIN) — SHA-256 prefix `5b57b622…`
- hebrew_tanakh (921 chapters, WLC; PUBLIC DOMAIN) — SHA-256 prefix `f317b359…`
- greek_nt (260 chapters, OpenGNT v3.3; CC-BY-SA-4.0) — SHA-256 prefix `d2853da4…`
- pali (186 suttas, SuttaCentral Mahāsaṅgīti; CC0-1.0) — SHA-256 aggregate prefix `70fd2b21…`
- avestan_yasna (67 chapters, Avesta.org Geldner-1896; PUBLIC DOMAIN) — SHA-256 aggregate prefix `cb0aadc4…`

**Total units**: 2,731 (vs F63's 5,963 because synthetic-chunked Arabic peers are excluded).

---

## 3. Protocol

### 3.1 Feature extraction (locked, byte-exact inherited from F63)

For each unit `u` in each corpus `c`, compute three scalars:
- `EL(u)` = top-end-letter frequency (= `p_max` in F63; range [0, 1]).
- `VL_CV(u)` = std(verse_lengths_in_words) / mean(verse_lengths_in_words).
- `p_max(u)` = same as EL above (kept as a separate term to mirror the original 6-term Φ_master structure where these are different in Arabic).

(EL = p_max here because both are computed identically; in the original Arabic 6-term, "EL" was the rate of any of the top-3 letters, whereas p_max is just the top-1. For cross-tradition portability, we collapse to the simpler p_max form for both terms, while still summing them as 2 of the 3 portable terms — equivalent to weighting p_max-based MI 2×. This is locked at PREREG seal and matches F63's universal feature definition.)

### 3.2 Discretisation

Each scalar is binned into K = 5 equal-width bins on the joint range across ALL 2,731 units. Bin edges are computed once per scalar from the joint range; same bin edges apply to all corpora.

### 3.3 Mutual information

For each corpus `c`:
- Define indicator variable `Y_c[u] = 1 if unit u belongs to corpus c else 0`.
- For each feature F ∈ {EL, VL_CV, p_max}:
  - Compute `MI(F_binned, Y_c) = sum_{i,j} p(F=i, Y_c=j) · log[p(F=i, Y_c=j) / (p(F=i) p(Y_c=j))]`, in nats.
- Sum: `Φ_3(c) = MI_EL(c) + MI_VL_CV(c) + MI_p_max(c)`.

### 3.4 Decision rule (locked TIGHTER than the sizing-observed values)

A sizing diagnostic (`scripts/_phi_master_xtrad_sizing.py`) was executed BEFORE this PREREG was sealed and revealed observed Φ_3 values. Locked thresholds for PASS:

1. **Strict argmax**: `argmax_c Φ_3(c) == "quran"` over the 6 corpora.
2. **Margin floor**: `Φ_3(quran) / Φ_3(next_highest_corpus) ≥ 1.5`. **Pre-registered expected outcome (sizing-observed)**: this margin is NOT met (sizing shows ratio = 0.6814; Quran is rank 3/6). The locked floor is published anyway because the FAIL is the publishable negative result — we are PREREG-locking the FAIL_quran_not_argmax verdict + the per-feature MI breakdown that explains it.
3. **Permutation null**: 10,000 random label-shuffles of the 2,731 unit-to-corpus assignments (preserving per-corpus unit counts; seed = 42). For each shuffle, recompute Φ_3 medians per fake-corpus; check if any fake-corpus achieves Quran's Φ_3-extremum at the locked margin.
4. **Bonferroni-corrected α** = 0.001 / 1 = 1e-3 (single comparison, since this is one Φ_3 statistic per corpus, not K=2 like F63).
5. **Audit hook A1**: corpus byte-fingerprints captured; loader determinism check against the F63 R1 audit's manifest.
6. **Audit hook A2**: feature parity — re-compute Quran's median EL, VL_CV, p_max and verify byte-exact match against F63 R1 receipt within 1e-9. (This guards against silent loader drift between F63 and exp110.)
7. **Audit hook A3**: discretisation determinism — bin edges captured in receipt for reproducibility.

### 3.5 Verdict ladder

- **PASS_quran_phi_master_xtrad_extremum** if §3.4 conditions 1-2 + perm-p < 1e-3 + A1+A2+A3 all hold.
- **PASS_quran_phi_master_xtrad_argmax_no_margin** if §3.4 condition 1 holds but condition 2 (margin) does not — PARTIAL.
- **FAIL_quran_not_argmax** if §3.4 condition 1 fails — Quran is NOT the cross-tradition Φ_3 extremum.
- **FAIL_audit_*** for any audit hook failing — methodological flaw, not substantive falsification.

---

## 4. Reporting — locked at PREREG seal

The receipt MUST report:
- Per-corpus n_units, mean & median EL, VL_CV, p_max
- Per-corpus 3-term Φ_3 (in nats), and breakdown by 3 components
- argmax corpus, margin ratio
- Empirical perm-p
- All 3 audit hook outcomes
- Wall-time
- PREREG hash match

---

## 5. What this experiment does NOT establish

- Φ_master full 6-term cross-tradition (only 3 portable terms used; Arabic-specific morphology terms remain Arabic-internal).
- Quran-distinctiveness against Sanskrit Vedic / Tamil Sangam / Classical Chinese / cuneiform corpora (separate hash-locked PREREGs).
- A theological claim of any kind — this is a structural-stylometric mutual-information calculation.
- That this paper's Φ_master = 1,862.31 nats Arabic-internal is reproducible cross-tradition. F58's 1,862-nat figure is computed under the full 6-term formula on 7 Arabic corpora; exp110's Φ_3 is a different (smaller, portable) statistic on a 6-corpus pool.

---

## 6. Sealed prereg hash (auto-computed by run.py at execution time)

To be filled in by execution.

---

## 7. Stop conditions

- If A1 fails (byte-fingerprint drift): STOP, do not run; investigate corpus loader.
- If A2 fails (feature parity drift > 1e-9 from F63 R1): STOP, do not run; investigate feature pipeline drift.
- If A3 fails (bin edge non-determinism): STOP, do not run; fix randomness control.

---

**END PREREG (sealed pre-run; no edits permitted).**
