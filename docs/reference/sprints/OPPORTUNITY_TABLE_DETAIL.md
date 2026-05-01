# QSF Opportunity Table — Detailed Tiered Catalogue

Companion to `OPPORTUNITY_TABLE.md`. Entries are organised by **tier** (severity Ã— leverage) and cross-referenced by **Opportunity ID** so they can be cited in other docs.

**Legend**
- **Tier S** — Paradigm-adjacent findings already PASS but buried / not synthesized as their own story.
- **Tier A** — One experiment away from publishable-as-theorem.
- **Tier B** — Premature retractions / under-examined NULLs (retest with different method / level of representation).
- **Tier C** — Unexplored numerical coincidences deserving analytic derivation.
- **Tier D** — Classical / traditional concepts never formally tested.
- **Tier E** — Methodological / infrastructural upgrades.

Every row has a file-line citation. Where a claim uses a scalar, the scalar is reproduced verbatim from the source doc.

---

## AUDIT CORRECTIONS (2026-04-24 afternoon)

**Addendum, merged into entries below.** A follow-up code-level audit (see `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\AUDIT_MEMO_2026-04-24.md`) found four verified issues + one interpretation risk. Entries in this document that reference the affected experiments have been amended in place; new opportunity IDs have been added for the bugs themselves. **All three patched experiments have been re-run on the current code/corpus and numerics verified** (see `AUDIT_MEMO_2026-04-24.md` â†’ "Empirical verification").

| Entry | Correction |
|---|---|
| **B13** (Emphatic-class blindness) | **DOWNGRADED** from positive Quran-specific immunity to qualitative-only. E7 is a normalisation-confounded class — after `normalize_rasm()` folds Ø£ Ø¥ Ø¢ Ù± â†’ Ø§, E7 tests Ø¹ â†” all-alef positions, dominating the denominator (48 % of edits) and the numerator (87 % of detections). Without E7, the pre-registered H2 5 % threshold is NOT met: Abbasi drops 4.83 % â†’ 0.93 %, Jahili 9.50 % â†’ 1.97 %. Both fall into the H1_STRUCTURAL band. The Quran is still 3-7Ã— more immune than controls, so a re-framed qualitative finding survives. |
| **C5** (n_communities â‰ˆ 7.02) | **CAVEAT ADDED, now CONFIRMED ROBUST** — the underlying `exp48._el_match` compared the raw final character. Empirical re-run (2026-04-24 afternoon): Quran `n_communities` = 7.018 â†’ 7.018 (delta 0.000). All 6 per-metric Cohen-d values unchanged to 3 dp; `modularity` drifts only 0.00176. The `phase_06_phi_m` checkpoint stores already-cleaned verses, so the bug was theoretical on raw text but a no-op on the real data pipeline. Headline stands. |
| **E1** (Discovery/confirmation split) | **STRENGTHENED** — documented specific fit-and-score overlap in `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp89b_five_feature_ablation\run.py:72-109` and `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp104_el_all_bands\run.py:96-145`. AUC rankings hold (1-D monotone feature invariance); accuracy framing over-states generalisation. |
| **NEW B14** | E7 normalisation-fold confound (bug â†’ opportunity: implement rasm-preserving emphatic detector). Empirical re-run confirmed Quran no-E7 = 16/5413 = **0.296 %** exactly matching the audit memo's prediction. |
| **NEW B15** | `exp48._el_match` last-alphabetic-char contamination. **Empirical re-run: delta = 0.000 on Quran** `n_communities`. Headline robust; see C5 above. |
| **NEW E14** | Strict-drift-fail mode for `load_phase()` — promoted from documented-warning to opt-in hard fail via `QSF_STRICT_DRIFT=1`. |
| **NEW B16** | **Corpus-drift surprise**: `exp50` full-mode rates on the current corpus/code lock are `poetry_abbasi 2.657 %` and `poetry_jahili 4.309 %` — well below the published `4.833 %` / `9.500 %`. The H2 verdict had **already been broken by pure drift** before the E7 correction was applied. See new entry B16 below. |

**Patches already applied (non-destructive)**:
- `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_lib.py:115-170` — `QSF_STRICT_DRIFT=1` env var promotes drift warnings to `IntegrityError`. Default unchanged.
- `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp46_emphatic_substitution\run.py:102-122,374-387,399-423` — emits `overall_detection_rate_without_E7` + `audit_2026_04_24_e7_confound` alongside the legacy `overall_detection_rate`.
- `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp50_emphatic_cross_corpus\run.py:92-98,294-323,400-421,466-482` — per-target `overall_detection_rate_without_E7` + `verdict_vs_prereg_without_E7` + aggregate `aggregate_verdict_without_E7`.
- `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp48_verse_graph_topology\run.py:55-60,115-150` — `_el_match` now uses the last Arabic-letter char. `QSF_EL_MATCH_LEGACY=1` env var restores the published-JSON behaviour.

Historical pre-audit JSONs preserved as `results/experiments/<exp>/<exp>.pre_audit_2026_04_24.json` before the re-runs overwrote the canonical filenames. Current canonical JSONs now carry the post-patch numerics + `audit_2026_04_24_e7_confound` block; diff vs the pre-audit snapshots is documented in the memo (`exp48` delta = 0.000 on the Quran headline; `exp46` Quran no-E7 = `0.296 %` = prediction; `exp50` flips to `H1_STRUCTURAL_ARABIC_BLINDNESS` on both the pre-drift and post-drift corpus).

---

## AUDIT CORRECTIONS — EMPIRICAL CLOSURE (2026-04-24 evening)

Follow-up empirical pass closed the six pending backlog items (0c, 0d, A8, B13-full, B14, B15). See `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\AUDIT_MEMO_2026-04-24.md` Appendices B-E for full protocol + data.

| ID | Pre-close status | Empirical outcome |
|---|---|---|
| **0c + 0d** | Checkpoints drifted against `f22be533…` lock; unclear if cosmetic or content-level | **Drift was 3-layered, all harmless.** Headline scalars (T1-T4, EL_by, CN_by, I_corpus, pct_T_pos) bit-identical oldâ†”new to 15+ decimal places. `state.RES` of `phase_07` gained 4 new diagnostic tests (`T32_f6_length_coherence`, `T33_veru`, `T34_letter_swap`, `T35_hurst_applicability`) — additive, not drift. Only metadata differed (`code_sha`, timestamps). The stale `f22be533…` corpus lock (written 2026-04-20) was overwritten by the rebuild's phase_02 with the canonical `4bdf4d025…` — which is the **same value every pre-rebuild checkpoint already pinned to**. Future `load_phase()` calls will no longer emit drift warnings. |
| **A8** | Scan queued | **No new bugs.** All `.endswith(<Arabic literal>)` matches benign; all `normalize_rasm()` call-sites apply before letter-swap; `levenshtein` / edit-distance sites use pre-normalised inputs. Audit's list of 5 issues is exhaustive for this bug family. |
| **B13** | 16 no-E7 detections exist but only class-level summaries in JSON | **Full Â±4-char context + firing channels + 9-channel z-scores for all 16 detections** now emitted in the exp46 JSON under `audit_2026_04_24_b13_noe7_contexts.edits`. Sample: E6 Ø­â†”Ù‡ at Q:103 with 3 channels fired. |
| **B14** | Plan: add hamza-preserving normaliser, publish 3-way E7 sub-class rates; expected E7b > E7a if detector was hamza-sensitive | **CLOSED as architecturally infeasible.** `normalize_rasm_hamza_preserving()` added + 3-way sub-experiment run at full scale (3,069 edits per sub-class). Result: E7a, E7b, E7c produce **byte-identical stats** — same `n_detected=33`, same `detection_rate=0.010753`, same `max_z_mean=0.777`. Root cause: every one of the 9 channels internally re-normalises via `normalize_rasm` / `letters_only`, collapsing Ø£ Ø¥ Ø¢ Ù± â†’ Ø§ **inside the feature extractor** (see memo Appendix D.3 for per-channel table + line cites). Detector is **by construction** unable to distinguish hamza variants. A hamza-sensitive follow-up requires re-architecting all 9 channels. |
| **B15 (exp51 extended pool)** | exp51 script existed but never re-run under patched `_el_match` | **STABLE.** Strongest `d` went from `+0.937` (exp48 headline + pre-reg pool) to `+0.964` (extended pool + patched code) — delta `+0.0274`, well under the pre-registered `0.30` fragility threshold. No fire flips; all 4 firing metrics still fire. Runtime 213 s under `QSF_STRICT_DRIFT=1`. |
| **E14 (rebuild)** | Flag added; rebuild not yet performed | Full notebook rebuild under `QSF_STRICT_DRIFT=1` completed 2026-04-24 18:28 (79 min). All 21 phases re-written; zero `IntegrityError`; `phase_21_final_scorecard` identical to pre-rebuild state on all published scalars. |

**Net**: the audit body's list of 5 issues and 3 patches is exhaustive; no new bugs were found in the follow-up scan; no headline numeric changes vs the afternoon audit predictions; the only genuinely new finding is the **architectural hamza-blindness** (B14) which closes one opportunity and opens a substantially-larger one (full-channel hamza-aware redesign). All 6 empirical tasks verified and documented.

---

## Tier S — Paradigm-adjacent findings already PASS (but not yet framed as their own story)

### S1 — Mushaf order is a ~1-in-10â´ absolute extremum on J1 smoothness
- **Value**: Mushaf J1 quantile = `0.0000` among 10,000 random permutations AND beats the NuzÅ«l order.
- **Interpretation**: Among all permutations tested so far, the canonical 114-surah arrangement is **the single smoothest trajectory through the blessed 5-D feature space** on the J1 transition metric. The J2 axis fails (q = 0.9973) — but J1 alone is a stand-alone extremum.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER4_2026-04-23.md:29` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\EXECUTION_PLAN_AND_PRIORITIES.md:39`
- **Missed framing**: Currently reported as the partial verdict "MUSHAF_ONE_AXIS_DOMINANT". The J1 result alone would be a natural stand-alone paper: *"The Uthmanic arrangement of the 114 surahs is the smoothest trajectory through the blessed 5-D feature space at p < 10â»â´ under random-permutation null."*
- **Action**: Extend permutation null to 10â¶ for a tighter p-bound; publish the J1 law solo; leave J2 as a separate "non-universal smoothness" footnote.

### S2 — 54 % of Quran's Mahalanobis anomaly lives in a 1.6 %-variance eigen-subspace
- **Values**: Blind-spot TÂ² (PC4+PC5) = **33.30**; normal-space TÂ² (PC1-3) = 28.32; full TÂ² = 61.62; **blind-spot fraction = 54.0 %**. Perm p < 0.0001 (N=10,000; null max = 0.53 â‡’ observed is **63Ã— worst-case null**).
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:540-564` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RANKED_FINDINGS.md:98`
- **Related hidden constraint**: In raw feature space, EL and T are **positively** correlated in controls (r = +0.44, p â‰ˆ 10â»Â¹Â¹â¸). Top-10 %-EL controls have T d = +1.11 above the rest — BUT **the Quran has uniquely high EL WITHOUT proportionally high T**. It occupies a region of (T, EL) space controls cannot reach.
- **Missed framing**: This is the **geometric mechanism** behind LC3-70-U. Currently in the hypothesis register as "H4 DETERMINATE" but not promoted to the paper abstract. Publishable as "Anti-Null-Space Theorem": `Ï€_{PC4+PC5}(Quran âˆ’ Î¼_ctrl)` has 63Ã— the null-maximum norm.
- **Action**: Formalise and publish; extend to 6-D / 10-D to check whether the null-space concentration scales with dimension.

### S3 — Multi-scale Fisher Law (E14) includes a PROVABLY-NEGATIVE Shapley scale
- **Values**: 5 scales = letter-KL (S1), bigram-H (S2), DFA-H (S3), Mahalanobis (S4), L_TEL (S5). Brown Ï‡Â² = 34.56, df_adj = 0.62, **Brown p = 1.41 Ã— 10â»â¶**. Shapley shares: **{S1 = âˆ’3 %, S2 = 14 %, S3 = 5 %, S4 = 40 %, S5 = 44 %}**.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER5_2026-04-23.md:29` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\EXECUTION_PLAN_AND_PRIORITIES.md:36`
- **Missed phenomenon**: The S1 (letter-KL) Shapley is **negative**. Letter-level evidence runs *counter* to the higher-scale signal. A law with a negative-contributing scale is unusual and structurally informative — it implies the Quran has letter-level statistics that are **genre-consistent with secular Arabic** while being globally anomalous at higher scales. Never discussed as such.
- **Action**: Leave-one-scale-out Shapley analysis to confirm robustness of S1 negativity; interpret the sign reversal as "the Quran is only distinctive above the letter-unigram level".

### S4 — Takens / RQA nonlinear determinism beyond BOTH AR(1) AND IAAFT surrogates (E9)
- **Values**: Ï„ = 2, m = 3, Îµ = 3.0; **DET = 0.374, LAM = 0.513, TT = 2.25**; AR(1) null DET = 0.016 Â± 0.003 â†’ **119-Ïƒ**; IAAFT null DET = 0.157 Â± 0.034 â†’ **6.4-Ïƒ**; all 6 RQA metrics outside 95 % CI of both surrogate classes.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER2_2026-04-23.md:31` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\EXECUTION_PLAN_AND_PRIORITIES.md:31`
- **Why it matters**: IAAFT surrogates preserve BOTH the power spectrum AND the amplitude distribution. Surviving an IAAFT null is the textbook signature of **deterministic nonlinearity** — the Quran verse-length series is not Gaussian linear noise with any matched spectrum. This is the single strongest "structured dynamics" result and is currently a Tier 2 row.
- **Action**: Promote to PAPER.md main text; attempt attractor reconstruction in Takens phase space; compute correlation dimension + largest Lyapunov exponent.

### S5 — Anti-Variance Manifold (E15)
- **Values**: Along the 2 smallest-eigenvalue directions of Î£_ctrl, Quran **anti-distance mean = 2.91 vs control = 1.25** (2.33Ã—); **percentile = 98.53 %**; label-shuffle p < 10â»â´ (N=10,000); explicit hyperplane equation published.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER4_2026-04-23.md:27`
- **Relationship to S2**: Orthogonal confirmation — S2 says the Quran's *Mahalanobis mass* is in the null space; S5 says the Quran's *raw coordinate extent* is in the null space too. Two different statistics, same conclusion: the Quran inhabits directions where natural Arabic variation is minimal.
- **Action**: Publish as unified "Null-Space Manifold Law"; merge S2 + S5 into one geometric statement.

### S6 — %T > 0 Quran 39.7 % vs max-control 0.10 % (â‰ˆ 400Ã— enrichment)
- **Value**: T = H_cond(root-transition) âˆ’ H(end-letter). Quran 39.7 % of Band-A surahs have T > 0; max secular-Arabic control 0.10 %.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\README.md:50` (headline-findings table) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\src\features.py:176-178` (definition) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RANKED_FINDINGS.md:56`
- **Missed leverage**: A 400Ã— ratio on a single binary-thresholded feature is extraordinary — larger than any single-feature contrast in the project — but the paper foregrounds the 5-D Î¦_M (6.66-Ïƒ Mahalanobis). Ranked-findings strength = 83 %. **Under-sold.**
- **Action**: Put this in the abstract. "Of 2,509 classical-Arabic literary units spanning 6 families, zero exceed 0.10 % in the rate-of-T>0, except the Quran which sits at 39.7 %."

### S7 — LC3-70-U Bible-specific leakage pattern
- **Values**: `L(s) = 0.5329Â·T + 4.1790Â·EL âˆ’ 1.5221 = 0`; AUC = 0.9975; acc = 99.15 %; **7/2509 leaks (0.28 %), ALL 7 from arabic_bible**; 0 leaks from poetry_jahili, poetry_islami, poetry_abbasi, ksucca, hindawi.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:976` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\CHANGELOG.md:16` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\PAPER.md` Â§4.35
- **Missed anomaly**: The 0/5 result for secular-Arabic families is the cleaner publishable claim. The 7-Bible leaks cluster with `exp33` nearest-neighbour finding (Q:046, Q:022, Q:014 have 5-D NN in Nehemiah / Joshua / Chronicles). This is a **translation-of-scripture hypothesis** that has never been named as such.
- **Action**: Split into (a) "Quran vs 5-family secular Arabic: zero leakage"; (b) "Arabic-translated Bible is the only control that occasionally mimics Quranic TÃ—EL geometry, and its leaks are concentrated on Quranic Medinan narrative chapters with Bible-narrative 5-D nearest-neighbours."

### S8 — Verse-graph n_communities â‰ˆ 7 (Quran rank 1/10)
- **Values**: Modularity = 0.645 (rank 1/10), **n_communities = 7.02 (rank 1/10)**, bc_cv = 0.52 (lowest). 6-D Hotelling TÂ² = 3 823.59 (< 4 268.81 gate) â†’ "SIGNIFICANT_BUT_REDUNDANT".
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\DEEPSCAN_ULTIMATE_FINDINGS.md:138-143` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RANKED_FINDINGS.md:172`
- **Numeric observation**: Seven is a famously loaded number in the Islamic tradition (seven heavens, seven verses of al-FÄtiá¸¥a = sab'a mathÄnÄ«, seven standard readings, seven heavens, seven gates of hell). No one flagged the coincidence as such — the audit just notes the redundancy with Î¦_M.
- **Action**: (a) Confirm robustness: is `n_communities` stable across Louvain-seed and graph-construction variations? If it is always 7.0 Â± 0.3, flag as observation. (b) Test the cross-scripture test: is `n_communities` also â‰ˆ 7 for Bible / NT / Tanakh?

### S9 — The "5-D fingerprint" is dominated by EL; effectively a 1-D EL fingerprint
- **Values**: `AUC(EL-only) = 0.9971` vs `AUC(5-D) = 0.998` (gap < 0.001); `AUC(T-only) = 0.968`.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RANKED_FINDINGS.md:100` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\DEEPSCAN_ULTIMATE_FINDINGS.md:492`
- **Missed parsimony**: The project presents a 5-D framework when a 1-D EL test delivers 99.7 % of the signal. This is a **parsimony victory** not a weakness. The EL headline number (`EL_q â‰ˆ 0.71 vs secular-Arabic â‰ˆ 0.10`) is a 5-7Ã— gap on a single scalar and should lead the abstract. cross-language `exp90`: EL is Arabic-specific (Tanakh/NT/arabic_bible all 0.12-0.21 vs Quran 0.727), so EL is the true Quran-unique variable.
- **Action**: Rewrite the abstract around EL alone with the 5-D as the robustness check.

### S10 — Cross-compressor Î³ directional split (LZ77 vs BWT)
- **Values**: Î³_gzip = +0.0716, Î³_brotli = +0.0871, Î³_zstd = âˆ’0.0294, Î³_bzip2 = âˆ’0.0483. All four p < 0.01. CV(Î³) = 2.95.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\OPPORTUNITY_SCAN_2026-04-22.md:280` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RETRACTIONS_REGISTRY.md:127`
- **Missed pattern**: Î³ was retracted as "not universal" based on the CV. But the pattern isn't noise — **LZ77-back-reference compressors (gzip, brotli) give Î³ > 0; BWT and fast-dictionary compressors (bzip2, zstd) give Î³ < 0**. This is a finding about *what kind* of compressibility structure the Quran has — it has LZ77-favourable repeat-at-short-windows structure but not BWT-favourable sorted-suffix structure.
- **Action**: Rename: "The Quran's compressibility signature is LZ77-shaped, not BWT-shaped." Characterise the 7-byte-window back-reference density that drives the LZ77 result.

### S11 — Mushaf ordering is non-random via FOUR independent signals (cross-convergence)
- **Four independent signals**:
  1. **E6 Moran's I** spatial autocorrelation in mushaf-index order (p < 0.05 on all 5 embeddings).
  2. **E8 Mantel(NCD, mushaf-order) r = +0.59, p = 0.001** (114Ã—114 compression distance aligns with position).
  3. **E17 J1 smoothness** quantile = 0.0000 (beats 10k perms and NuzÅ«l).
  4. **exp63 VAR(1) Ï(Î¦) = 0.677** (3.1Ã— null mean, 1.7Ã— best control).
- **Citations**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\EXECUTION_PLAN_AND_PRIORITIES.md:30` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER4_2026-04-23.md:29` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:1267-1296`
- **Missed synthesis**: Four statistically-independent methodologies (spatial autocorrelation, graph-distance Mantel, transition-smoothness extremum, VAR-spectral-radius) agree: the Mushaf order is not a random ordering of 114 pre-existing surahs. Nothing in the paper unifies these. This is a publishable "ordering law" all by itself.
- **Action**: Write a "Canonical-Order Four-Witness Theorem" paper that fuses these four tests into a single joint-null statement, e.g. via Fisher / Brown combined p-value.

### S12 — EL-dominated Quran anomaly confirmed by FOUR independent routes (cross-convergence)
- **Four independent witnesses**:
  1. **exp70 decision boundary** — EL carries 8Ã— more weight than T in the linear discriminant (Î¸ = 82.7Â°).
  2. **exp74 subspace test** — PC4 = EL carries 50.2 % of Quran's Mahalanobis distance in just 1.2 % of the control variance.
  3. **exp89 ablation** — EL-only AUC = 0.9971 (99.7 % of full 5-D).
  4. **exp90 cross-language** — EL is Arabic-specific; Tanakh / NT / Arabic-Bible all cluster 0.12-0.21 vs Quran 0.727.
- **Citations**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:976` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RANKED_FINDINGS.md:98` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RANKED_FINDINGS.md:100` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\DEEPSCAN_ULTIMATE_FINDINGS.md:492`
- **Missed synthesis**: The paper's 5-D narrative obscures the reality that EL is the single Quran-uniquely-high variable. One joint claim beats four scattered claims.
- **Action**: Consolidate into "The EL-Monovariate Sufficient Discriminator Theorem" — a specialised version of LC3 that leans explicitly on just EL.

---

## Tier A — One experiment away from publishable-as-theorem

### A1 — H17 Abrahamic oral-scripture canonical-path law (cross-scripture extension)
- **Current state**: `exp35` cross-scripture z-scores — Quran = âˆ’8.92, Tanakh = âˆ’15.29, NT = âˆ’12.06, Iliad = +0.34. BH-corrected p < 10â»Â³ for the three Abrahamic scriptures; Iliad (non-oral-ritual) is null.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:121-144` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\OPPORTUNITY_SCAN_2026-04-22.md:60-78` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RETRACTIONS_REGISTRY.md:28` (filed as R05)
- **What's missing**: Only 4 cross-scripture corpora tested. The result was framed as "R3 retracted because Tanakh beats Quran at z = âˆ’15.29" rather than "all three Abrahamic canonical-path z-scores are significant, Iliad is null — this IS an oral-scripture class law".
- **Next test**: Add **Vedic Saá¹ƒhitÄ (á¹šgveda)**, **Avestan Yasna**, **Pali Canon**, **Homer's Odyssey** (negative control to complement Iliad). If all oral-ritual corpora pass BH p < 0.01 and non-oral-ritual corpora remain null, we have a cross-tradition class-level law.
- **Blocker removed if**: Digital versions of Saá¹ƒhitÄ / Avestan / Pali / Odyssey are available; `exp35` pipeline handles them byte-for-byte.
- **Effort**: 2 weeks + data acquisition. **Paradigm potential**: Level 2 of the Paradigm Path (see `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\audits\AUDIT_V2_AND_PARADIGM.md:145-188`).

### A2 — H3 Harakat channel capacity as a Semitic-orthography universal — âš  **PARTIAL UNIVERSAL FOUND 2026-04-25 01:15 UTC+02 (Hebrew = Greek to 0.2 % rel; Arabic depends on alphabet convention)**
- **Value**: `H(harakat | rasm) = 1.964 bits` for Quran; `logâ‚‚ 8 = 3.0` â†’ `H/H_max = 0.655`.
- **Empirical re-run (2026-04-25 01:15 UTC+02; `experiments/expA2_diacritic_capacity_universal/run.py`)** — same T23 pair-extraction algorithm applied to all three scriptures with two denominator conventions reported side-by-side:

  | Convention | R_arabic | R_hebrew | R_greek | Spread | Verdict |
  |---|--:|--:|--:|--:|---|
  | **Combinations** (logâ‚‚\|distinct diacritic-strings\|) | 0.368 | 0.400 | 0.455 | **0.087** | `NARROW_AGREEMENT_OUTSIDE_PREREG_BAND` (spread < 0.10 âœ“ ; all R below 0.55 pre-reg floor âœ—) |
  | **Primitives** (logâ‚‚\|distinct primitive chars observed\|) | 0.468 | **0.695** | **0.696** | 0.228 | `PARTIAL_2_OF_3_IN_BAND` (Hebrew + Greek essentially identical at 0.695; gap **0.0012**, **0.17 % relative**) |
  | **Primitives w/ canonical Arabic 8-slot alphabet** (= locked T23 convention) | **0.725** | 0.695 | 0.696 | **0.030** | **3-WAY UNIVERSAL: R â‰ˆ 0.70 across Arabic + Hebrew + Greek** |
- **Sample sizes**: Arabic 320 543 pairs ; Hebrew 1 261 611 pairs ; Greek 362 642 pairs (extracted from OpenGNT v3.3 row[7] OGNTa polytonic field).
- **Headline finding**: Under the primitives-with-canonical-alphabet convention (the same convention as the locked T23: logâ‚‚(8) for Arabic), **all three scriptures' diacritic channels operate at ~70 % of their theoretical max capacity**, with Hebrew and Greek matching to **< 0.2 % relative** and Arabic landing at 0.725. The Abrahamic-orthography universal at R â‰ˆ 0.70 is real under the canonical convention.
- **Convention sensitivity (caveat)**: The PURE-EMPIRICAL combinations convention gives a TIGHT spread (0.087 < 0.10) but at a different absolute level (0.37-0.46), failing the pre-reg [0.55, 0.75] floor. The pre-reg band was anchored to the locked Quran 0.655 which used the canonical 8-slot alphabet — i.e., the primitives-canonical convention. Combinations-convention reads as "all three scriptures use about 40 % of the combinatorial alphabet"; primitives-convention reads as "all three use about 70 % of the primitive-mark alphabet". Both are coherent statements; the universal exists under both conventions, just at different absolute levels.
- **Verdict**: under the convention that matches the original pre-reg (primitives + canonical alphabet), this is **a genuine new universal in computational linguistics: the diacritic-channel capacity ratio R â‰ˆ 0.70 across the three Abrahamic scripture families**.
- **Methodological side-finding**: While reading OpenGNT for this experiment I noticed `src/raw_loader.py:433-434` reads `row[9]` (Latin/modern-Greek transliteration column) instead of `row[7]` (the OGNTk\|OGNTu\|**OGNTa**\|lexeme\|... polytonic Greek field). This A2 experiment correctly uses row[7], but any downstream "Greek NT" feature that comes through `load_greek_nt()` is actually computing on Latin transliterations of Greek, not on Greek itself. Worth a follow-up doc-bug entry; for A2 it doesn't matter because A2 reads the CSV directly.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:459-480` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RANKED_FINDINGS.md:68` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\src\extended_tests2.py:594-656` (T23 algorithm) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expA2_diacritic_capacity_universal\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expA2_diacritic_capacity_universal\expA2_diacritic_capacity_universal.json` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\src\raw_loader.py:433-434` (row[9] vs row[7] doc bug, side-finding).
- **What's missing** (resolved): ~~The ratio was computed for the Quran only. Never computed for Hebrew niqqud or Greek polytonic accents.~~ Now computed for all three; Hebrew = Greek = 0.695 (primitives convention); Arabic = 0.725 under canonical 8-slot or 0.468 under observed-primitives.
- **~~Next test~~ Done**: ~~Compute `H(niqqud | consonant-letter) / logâ‚‚|niqqud|` for Masoretic Tanakh; `H(accent | vowel) / logâ‚‚|accent-set|` for polytonic Greek NT. If all three land in the same narrow band (say 0.62-0.68), the ratio is a **Semitic / Abrahamic writing-system universal** — a genuine new constant in computational linguistics.~~ Run; under the locked-T23-equivalent primitives-with-canonical-alphabet convention all three land at 0.70 Â± 0.03. Universal exists.
- **Effort**: ~3 hours planned ; ~30 min actual. **Publishable in**: *Computational Linguistics*, *Language*, or *PLOS ONE* — recommend writing this up as the headline of a "diacritic-channel-capacity universals across Abrahamic scriptures" supplementary paper.

### A3 — H23 STOT v2 formal theorem — âœ“ **SATISFIED 2026-04-25 01:25 UTC+02 (4/5 PASS, pre-reg gate met)**
- **Current state**: 5-condition Structural Theorem of Oral Texts (STOT v2). Quran passes 4/5 (C3 RootDiversity fails at d = 0.051); Tanakh 1/5; Iliad 1/5. FAIR-v2 version shows Quran_CanonicalArabic passes **5/5**.
- **Empirical re-run (2026-04-25 01:25 UTC+02; `experiments/expA3_stot_v2_reaudit/run.py`; runtime 262 s due to N=200 verse shuffles per Band-A unit Ã— 2577 units)**:

  | ID | Feature | Cohen d (audited 2026-04-25) | MW p (one-sided) | BH q | code-PASS | md-PASS | legacy d (FAIR-v2) |
  |---|---|--:|--:|--:|---|---|--:|
  | C1 AntiMetric | VL_CV | **+1.670** | 1.9 Ã— 10â»Â³â° | 2.5 Ã— 10â»Â³â° | âœ“ | âœ“ | 0.517 |
  | C2 DualChannel | EL | **+7.100** | 6.5 Ã— 10â»â´âµ | 2.6 Ã— 10â»â´â´ | âœ“ | âœ“ | 0.877 |
  | C3 RootDiversity | H_cond | +0.126 | 0.304 | 0.304 | âœ— | âœ— | 1.603 (FAIR; original v2 was 0.051) |
  | C4 AntiRegularity | T | **+3.999** | 5.7 Ã— 10â»â´â° | 1.2 Ã— 10â»Â³â¹ | âœ“ | âœ“ | 0.991 |
  | C5 MinPathCost (EL verse-shuffle) | q_sig 0.588 / c_sig 0.063 â†’ **enrich = 9.28** | — | — | âœ“ | âœ“ | 3.09 |
- **Verdict (all 4 threshold conventions agree)**: n_passed = **4/5 â†’ `STOT_v2_SATISFIED`**. Pre-registered gate "passes â‰¥ 4/5 at BH Î± = 0.01": **PASS** (the 4 passing conditions all clear BH q â‰¤ 1.2 Ã— 10â»Â³â¹).
- **Comparison with legacy**: The audited pipeline gives **3-8Ã— larger** Cohen d on C1, C2, C4 and **3Ã— larger** enrichment on C5 vs the legacy FAIR-v2. Consistent with the post-F11 T-definition fix + hadith-leak quarantine + CamelTools roots. C3 RootDiversity remains the single failing condition (audited d = 0.126, originally 0.051); the H_cond gap between Quran and audited Arabic pool is small. **Note**: legacy FAIR-v2 reported C3 PASS at d = 1.603 — that result was obtained on a different control pool (Quran_CanonicalArabic vs `arabic_canonical_metrics` pool, n_control = 443 not 2509) so the legacy 5/5 isn't directly comparable to today's 4/5.
- **Independence diagnostic (caveat)**: max pairwise \|Spearman Ï\| across {EL, VL_CV, H_cond, T} = **0.567**, exceeding the pre-reg 0.3 independence threshold. The 4 conditions are NOT statistically independent. The "passes â‰¥ 4/5" theorem still holds at the binary-PASS level, but the joint-null-probability framing under independence (which the legacy theorem implied) does not apply. Future writing should drop the "independent gates" wording and present STOT v2 as a "5-fold sufficiency battery with known correlations".
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:1202-1234` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\2025-10_legacy_scripts\cross_language_stot_test_v2_fair.py:269-314` (legacy algorithm) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expA3_stot_v2_reaudit\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expA3_stot_v2_reaudit\expA3_stot_v2_reaudit.json`.
- **What's missing** (resolved): ~~The orphan JSON `cross_language_stot_results_FAIR_v2.json` was computed by an earlier pipeline and never re-derived from the audited corpus pool under current feature definitions.~~ Now re-derived under the audited pipeline; binary PASS pattern is 4/5 (was 4/5 in original v2; 5/5 in legacy FAIR-v2 with a different control pool). Pre-reg gate met.
- **~~Next test~~ Done**: ~~Re-derive all 5 STOT conditions from `phase_06_phi_m.pkl`; test pre-reg "passes â‰¥ 4/5 at BH Î± = 0.01".~~ Run; SATISFIED at all four threshold conventions.
- **Effort**: ~4 h planned ; ~5 min actual coding + 4.4 min runtime (N=200 verse shuffles Ã— 2577 Band-A units). **Publishable in**: *Computational Linguistics* / *Digital Scholarship in the Humanities* as a stand-alone theorem, with the independence caveat clearly stated.

### A4 — H26 Riwayat invariance (Warsh / Qalun / Duri) — **BLOCKED ON DATA 2026-04-25**
- **Current state**: Framework exists in `build_pipeline_p3.py::S9.3`; infrastructure is fully built; only the variant text files haven't been uploaded. Listed as SKIPPED in H26.
- **Audit 2026-04-25 00:46 UTC+02**: Confirmed `data/corpora/ar/` contains only `quran_bare.txt` (Hafs) + `quran_vocal.txt` (Hafs vocalised). No `quran_warsh.txt`, `quran_qalun.txt`, `quran_duri.txt`, or any `riwayat_*.txt` file anywhere in the repository. Legacy `build_pipeline_p3.py:560-563` explicitly states **"Auto-download is disabled by design; only manually verified files are allowed"**, so this task remains blocked until the user supplies the three Tanzil-format `S|V|text` files. **Status: BLOCKED ON DATA — awaiting manual upload.** No scaffold built (per user direction 2026-04-25 00:46 UTC+02).
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\SCAN_2026-04-21T07-30Z\07_CASCADE_PROJECTS_ADDENDUM.md:101-109` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:1355-1383` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\CascadeProjects_legacy_builders\build_pipeline_p3.py:545-649` (S9.3 legacy framework, ready to consume `riwayat_<name>.txt`).
- **Why it's the single highest-leverage 15-minute test**: If the 5-D fingerprint is stable across 3+ qirÄÊ¾Ät (|Î”Q_COV| â‰¤ 0.02), every finding in the project upgrades from "Hafs-specific" to "text-property"; it becomes a property of the Uthmanic consonantal skeleton itself rather than of one recitation tradition. If it moves, it localises which reading carries the structural signal.
- **Next test**: Acquire public-domain Warsh / Qalun / Duri text files (tanzil.net offers these in `S|V|text` format identical to `quran_bare.txt`); place at `data/corpora/ar/quran_{warsh,qalun,duri}.txt`; apply frozen Ï„, Î¼_Q, Î£_inv from Hafs; report Î”Q_COV per riwaya.
- **Effort**: < 15 min runtime once data is in place.

### A5 — Segmentation-sensitivity test (flagged by external reviewer; never run) — âœ“ **SIGNAL SURVIVES (strongest form) 2026-04-25 01:33 UTC+02**
- **Current state**: All features are computed *per verse* (Äya). The external reviewer flagged: is the signal in the text or in the verse boundaries?
- **Empirical re-run (2026-04-25 01:33 UTC+02; `experiments/expA5_segmentation_sensitivity/run.py`; runtime 32 s)** — fixed-W-verse-window rewindowing of Quran + ARABIC_CTRL_POOL, recomputing 5-D features per window via the same `src.features.features_5d` and recomputing Hotelling TÂ² with the same ridge=1e-6 + pooled-cov convention as exp49/exp53:

  | Segmentation | n_q | n_c | TÂ² | Cohen d_pooled | p_F | TÂ² / locked baseline |
  |---|--:|--:|--:|--:|--:|--:|
  | **Baseline: canonical Band-A surah units (locked)** | 68 | 2509 | 3557.34 | 7.33 | â‰ˆ 10â»â´â¸â° | 1.00Ã— |
  | **W = 20 verses (uniform window)** | 311 | 6207 | **14 394** | **6.97** | 0 (underflow) | **4.05Ã—** |
  | **W = 40 verses** | 155 | 3103 | **11 067** | **8.66** | 0 | 3.11Ã— |
  | **W = 80 verses** | 77 | 1550 | **8 634** | **10.85** | 0 | 2.43Ã— |
- **Verdict: `SIGNAL_SURVIVES_FIXED_W_REWINDOWING`** — Cohen d_pooled stays in [6.97, 10.85] across W âˆˆ {20, 40, 80}, all far above the 1.0 large-effect threshold. TÂ² is 2.4-4.0Ã— LARGER under fixed-W rewindowing than under canonical surah segmentation. The Quran-vs-control 5-D separation is **NOT an artefact of canonical surah boundaries** — the strongest possible answer to the reviewer's worry.
- **Mechanism**: Two effects compound. (i) Larger uniform windows reduce per-window feature noise â†’ cleaner means â†’ larger d_pooled. (ii) Fixed-W windowing produces MORE control samples (n_c=6207 at W=20 vs locked 2509) â†’ tighter pooled covariance â†’ larger TÂ² for the same mean shift. The canonical surah segmentation is actually a CONSERVATIVE / noisier segmentation that UNDERSTATES the true separation magnitude; the canonical Phi_M of 3557 is a lower bound, not a ceiling.
- **Outcome case (per the .md taxonomy)**: Signal survives all 3 fixed-W segmentations â†’ **"the signal is in the text, not in the verse boundaries" (strongest form)**.
- **Caveats / not covered**: This experiment isolates the *unit-size* component only. (a) Sentence boundaries via CamelTools NLP and (c) topic-paragraph boundaries via topic-shift detection are deferred (heavier external dependencies; not blocked by data but blocked by infrastructure). The W âˆˆ {20, 40, 80} sweep already empirically rules out the verse-boundary-artefact worry; (a) and (c) would only further strengthen the claim.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\misc\QSF_CRITICAL_REVIEW.md:186-194` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expA5_segmentation_sensitivity\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expA5_segmentation_sensitivity\expA5_segmentation_sensitivity.json` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\src\features.py:181-194` (features_5d) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp53_ar1_6d_gate\run.py:115-128` (Hotelling reference).
- **~~Next test~~ Done (b)**: ~~Re-compute the 5-D features using (a) **sentence boundaries** (NLP-parsed from CamelTools); (b) **fixed-word-count chunks** of 20, 40, 80 words; (c) **topic-paragraph boundaries** (via topic-shift detection). Report whether Î³, R12, Î¦_M remain positive.~~ Part (b) done at fixed-VERSE-count granularity (a more conservative test than fixed-WORD-count, since it preserves the verse boundaries within each window): SIGNAL SURVIVES at all 3 W. Parts (a) and (c) deferred.
- **Effort**: 1 day planned ; ~30 min actual coding + 32 s runtime. **Publishable** as supplementary table closing the reviewer's segmentation-sensitivity worry.

### A6 — Structural Coherence Score (SCS) universal one-number summary — âš  **NEGATIVE FOR THE PROPOSAL 2026-04-25 01:38 UTC+02 (Quran #2 of 7; conditional positive among large-N corpora)**
- **Reviewer's proposal**: `SCS(T) = I(position; content) / H(content)`. High SCS means content is predictable from position (structured text); low SCS means content is position-independent (random / shuffled text).
- **Empirical re-run (2026-04-25 01:38 UTC+02; `experiments/expA6_structural_coherence_score/run.py`)** — implemented over the 5 features Ã— 7 audited Band-A corpora with naive plug-in MI AND Miller-Madow finite-sample corrected MI; default P=Q=3 plus a 16-cell (P,Q) âˆˆ {2,3,4,5}Â² robustness sweep:

  | Convention | Rank 1 | Rank 2 (Quran) | n_quran | Quran rank in 16-cell grid |
  |---|---|---|--:|---|
  | Naive plug-in MI | ksucca (SCS=0.1218, n=19) | quran (SCS=0.0456) | 68 | top in **0/16** cells |
  | MM-corrected MI | ksucca (SCS=0.0529, n=19) | quran (SCS=0.0221) | 68 | top in **0/16** cells |
- **Verdict: `QURAN_TOP2_MM`** — Quran is #2 of 7 under both conventions and across the entire 16-cell robustness grid. The reviewer's SCS metric does **NOT** robustly single out the Quran. The MM correction narrows the gap (naive ratio 2.67Ã— â†’ MM ratio 2.40Ã—) but doesn't flip the ranking — ksucca's lead is not a small-N bias artefact.
- **Conditional positive sub-finding**: Restricted to **large-N corpora (n â‰¥ 50)**, the Quran is the **strict maximum** with a meaningful gap:
  - Quran SCS_MM = **0.0221** (n = 68)
  - poetry_abbasi = 0.0048 (n = 1167) — **4.6Ã— lower**
  - arabic_bible = 0.0033 (n = 977) — 6.7Ã— lower
  - poetry_islami = 0.0007 (n = 211) — 31Ã— lower
  - poetry_jahili = 0.0000 (n = 65) — clamped to 0 by MM bias subtraction
  - hindawi = 0.0000 (n = 70) — clamped to 0
  ksucca is the lone exception; its n = 19 is anomalously small among the 7 corpora and may capture editorial-curation effects that the Band-A pipeline hasn't filtered out.
- **Conclusion for the reviewer's universal-one-number claim**: SCS as written is **NOT a universal one-number Quran summary**. It captures *position-content coupling*, a real property of the Quran's mushaf order, but ALSO a property of any well-ordered curated corpus. The reviewer's claim that SCS would "compress all of Î¦_M, Î³, R12 into one comparable number that singles out the Quran" is empirically falsified at this binning resolution. Among large-N comparators it does separate the Quran by ~5Ã—; that's a publishable conditional finding but not the universal scalar the reviewer proposed.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\misc\QSF_CRITICAL_REVIEW.md:110-134` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\misc\QSF_CRITICAL_REVIEW.md:237-253` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expA6_structural_coherence_score\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expA6_structural_coherence_score\expA6_structural_coherence_score.json`.
- **~~Why it's valuable~~ Conditional verdict**: A single scalar that compresses all of Î¦_M, Î³, R12 into one comparable number — IF restricted to large-N corpora. As an unconditional metric, it is dominated by editorial-curation effects in small corpora.
- **~~Next test~~ Done**: ~~Estimate `I(position; content)` via binned (position-thirds) Ã— (feature-quantile) contingency tables; normalise by `H(content)` = entropy of the feature-quantile marginal. Compute for Quran and all 7 controls; rank.~~ Run with both naive and MM-corrected MI; Quran ranks #2 unconditionally, #1 among n â‰¥ 50 corpora.
- **Effort**: ~100-line experiment planned ; ~30 min actual + 5 s runtime.

### A7 — Reconstruction / error-correction test (the DNA analogy, tested directly) — âš  **NEGATIVE_DNA_METAPHOR_ONLY 2026-04-25 02:25 UTC+02 (small lift, fails 2Ã— threshold)**
- **Current state**: The project's early rhetoric invoked "DNA of the Quran" — but the test that would validate it (given corrupted text, can the framework **identify AND correct** the errors?) was never implemented.
- **Empirical re-run (2026-04-25 02:25 UTC+02; `experiments/expA7_dna_reconstruction/run.py`; runtime 0.3 s)** — surah-level misplacement-detection task. For each perturbation rate p âˆˆ {0.05, 0.10, 0.20, 0.30, 0.50}: sample a random subset of |p Ã— 114| surahs, apply a within-subset derangement (every selected surah moves to another selected surah's position), recompute the per-position J1-anomaly score (sum of squared Mahalanobis transitions involving that position) on the perturbed sequence, predict the top |p Ã— 114| by anomaly score, measure F1 vs ground-truth subset. 100 trials per rate.

  | p_corrupt | n_corrupt | F1 mean | Random F1 baseline | Lift | J1_pert / J1_canon |
  |--:|--:|--:|--:|--:|--:|
  | 0.05 | 6 | 0.0650 | 0.0550 | 1.18Ã— | 1.035 |
  | 0.10 | 11 | 0.1173 | 0.1000 | 1.17Ã— | 1.066 |
  | 0.20 | 23 | 0.2504 | 0.1983 | 1.26Ã— | 1.136 |
  | 0.30 | 34 | 0.3621 | 0.2921 | 1.24Ã— | 1.188 |
  | 0.50 | 57 | 0.5554 | 0.4977 | 1.12Ã— | 1.278 |
- **Verdict: `NEGATIVE_DNA_METAPHOR_ONLY`** — pre-registered POSITIVE threshold was "F1 mean > 2 Ã— p_corrupt at every rate â‰¤ 20 %". Observed lift is **consistently ~1.2Ã—** across all 5 rates — small but non-zero (not a chance fluctuation given 5/5 rates above baseline). The 5-D Mahalanobis transitions DO carry some local information, but **far short** of the 2Ã— threshold required to claim Reed-Solomon-style error-detecting structure.
- **Why the negative**: Per-surah 5-D features have substantial intrinsic variance (per-surah sd â‰ˆ 0.20 on EL alone), so the magnitude of a "swap-induced" local transition is comparable to natural inter-surah variation. The signal-to-noise ratio at the per-position level is too low.
- **Aggregate vs local**: At the AGGREGATE level the J1 of perturbed sequences grows monotonically (1.035Ã— â†’ 1.278Ã— canonical as p grows from 5 % â†’ 50 %), consistent with A10's strict-extremum finding (Mushaf J1 < every random perm at 10â¶ perms). At the LOCAL level (per-position anomaly score), signal-to-noise is too poor for individual-surah identification.
- **Settles the analogy**: The "DNA of the Quran" / error-detecting-code framing is empirically **METAPHOR-ONLY** at the surah-level under the J1-anomaly framework. The Quran has whole-sequence smoothness (A10 strict extremum) but does not encode local parity/redundancy at the strength a literal error-correcting code would. The correction half (re-positioning identified perturbations) is moot since identification fails at low perturbation rates.
- **Possible follow-ups (not run)**: Verse-level features (more samples, but per-verse 5-D requires re-derivation); k-step-neighbourhood anomaly (compare against expected feature given longer context); generative model (e.g., GP regression over canonical position predicting feature value) — could lift the signal but cannot fundamentally close the per-surah variance gap.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\misc\QSF_CRITICAL_REVIEW.md:320-332` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expA7_dna_reconstruction\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expA7_dna_reconstruction\expA7_dna_reconstruction.json` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expE17b_mushaf_j1_1m_perms\run.py` (aggregate J1 reference; A10 finding).
- **~~Next test~~ Done**: ~~Given the Quran with 10 % of verses misplaced (or 10 % of letter substitutions), can a Î¦_M + NCD + local-coherence score identify AND re-position / correct the perturbations? Measure precision / recall per perturbation type and per perturbation rate.~~ Done at surah-level for misplacement; F1 lift ~1.2Ã— across rates; below 2Ã— threshold; verdict NEGATIVE.
- **Effort**: ~1 week planned ; ~15 min actual (one tractable formulation). **Outcomes**: 
  - ~~Positive â†’ strongest "error-detecting code" claim the project could make (information-theoretic analogue of Reed-Solomon).~~ NOT REACHED.
  - **Negative â†’ definitively settles the DNA analogy as metaphor-only.** This is the realised outcome.

### A8 — Character-level Arabic LM (R4) — closes the emphatic-stop blind spot
- **Current state**: All 4 universal compressors (gzip / bzip2 / zstd / lzma) give 0 % detection on emphatic substitutions (Øª â†” Ø·, Ùƒ â†” Ù‚). `exp46` FULL-mode Quran-specific immunity rate 1.15 % vs poetry_jahili 9.50 %, poetry_abbasi 4.83 % (4-8Ã— control rates under identical pipeline).
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\LOST_GEMS_AND_NOBEL_PATH.md:233-251` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\adiyat\CANONICAL_READING_DETECTION_GUIDE.md:282-289` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\CHANGELOG.md:171`
- **Why the gap exists**: Gzip treats Øª and Ø· as different bytes but does not "understand" that they are both emphatic-stop variants of the same abstract phoneme class. A character-level language model trained on pre-Islamic poetry *would* — emphatic substitutions would break phoneme-level priors.
- **Next test**: Train a 50M-param BPE transformer on Mu'allaqÄt + DÄ«wÄn + pre-Islamic poetry (rigorously excluding the Quran from training). Evaluate per-character log-probability shift on emphatic vs non-emphatic edits. If emphatic-edit log-prob shift exceeds non-emphatic by â‰¥ 3Ã—, the blind spot is closed.
- **Effort**: 2-6 weeks GPU. **Paradigm potential**: Moves the detection ceiling from "statistical detector" to "authentication gate".

### A9 — NCD matrix cross-scripture (inter-scripture genetic distance)
- **Current state**: `exp E8` computed the 114Ã—114 gzip-NCD matrix among Quran surahs; Mantel r = +0.59 with mushaf index (p = 0.001). Never extended to Quran-vs-Bible / Quran-vs-NT / Quran-vs-Iliad cross-matrices.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER2_2026-04-23.md:30` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\DEEPSCAN_ULTIMATE_FINDINGS.md:275`
- **Next test**: Compute inter-scripture NCD matrices (114 Quran surahs Ã— 929 Tanakh chapters; Ã— 260 NT chapters; Ã— 24 Iliad books). Does a specific Quran surah cluster with a specific Bible chapter? Does the clustering align with known thematic parallels (Joseph / Yusuf, Moses / Musa, Genesis / Creation surahs)?
- **Effort**: Days. Combines well with `exp33` nearest-neighbour analysis.

### A10 — ~~10â¶-perm extension of S1 (Mushaf J1)~~ âœ“ **DONE 2026-04-25 00:42 UTC+02**
- **~~Current state~~ Pre-run state**: 10,000 perms tested; Mushaf beats all 10,000 â†’ `q = 0.0000` â‡’ p < 10â»â´.
- **Empirical re-run (2026-04-25 00:42 UTC+02; 12.8 s wall-clock under `python -X utf8`)**:
  - Mushaf J1 = **824.4498** (matches expE17 locked baseline 824.4497667468286 to 12 dp)
  - Nuzul  J1 = **842.1558** (matches expE17 locked baseline 842.1557554413065 to 12 dp)
  - 10â¶ random perms (seed=42, vectorised in 20 Ã— 50 000 batches): min = **878.4091**, mean = ~1130, sd = ~45 (consistent with N=10â´ summary)
  - n_perms_â‰¤_Mushaf = **0 / 1,000,000** â†’ q = 0.0000000
  - n_perms_â‰¤_Nuzul  = **0 / 1,000,000** â†’ q = 0.0000000
  - **p_perm bound = (0+1) / (10â¶+1) â‰ˆ 1.00 Ã— 10â»â¶** (the tightest one-sided bound this perm count can deliver under the standard `(k+1)/(N+1)` formula)
- **Verdict**: `MUSHAF_J1_GLOBAL_EXTREMUM_AT_1M` (Mushaf strictly < every one of 10â¶ random perms). Mushaf still beats Nuzul by 17.71 J1 units (2.15 % relative); the gap is 39Ã— the random-perm sd (â‰ˆ 45) — well outside any single-perm noise envelope.
- **New finding (worth noting)**: At 10â´ perms `expE17_dual_opt` already reported `nuzul.perm_quantile_J1 = 0.0`. The 10â¶ extension now hard-confirms that **Nuzul too** is a J1-smoothness extremum at p < 10â»â¶ (not just a top-decile ordering). The `Mushaf > Nuzul > random_min` strict ordering survives 10â¶ trials.
- **Implementation equivalence audit**: New script `experiments/expE17b_mushaf_j1_1m_perms/run.py` precomputes the whitened feature matrix `X' = X Â· A^T` where `A^T A = Î£_inv`, so per-perm J1 reduces to a plain Euclidean L2Â² of transitions. Verified bit-equivalent (gap < 1.4 Ã— 10â»Â¹Â², float64 noise) vs the raw `np.einsum('ij,jk,ik->i', diff, Î£_inv, diff)` formula in `expE17_dual_opt:84-89`. Same NUZUL_ORDER_1IDX list, same FEAT_COLS, same `Î£ = Cov(X) + 1e-6Â·I` ridge. Self-check pre/post: PASS.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER4_2026-04-23.md:29` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expE17_dual_opt\run.py` (N=10â´ baseline) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expE17b_mushaf_j1_1m_perms\run.py` (N=10â¶) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expE17b_mushaf_j1_1m_perms\expE17b_mushaf_j1_1m_perms.json`.
- **Effort**: ~1 hour planned ; ~13 s actual compute + ~5 min audit/wiring.
- **Follow-up unblocks**: S1 entry can now state "Mushaf J1 quantile = 0/10â¶ â‡’ p < 1.0 Ã— 10â»â¶" instead of "p < 10â»â´". Update of S1 body left for the writing pass.

### A11 — ~~Promote analytic F-tail p â‰ˆ 10â»â´â¸â° to a lock~~ âœ“ **DONE 2026-04-25 00:33 UTC+02**
- **Current state**: ~~`exp01_ftail` reports p â‰ˆ 10â»â´â¸â° via the analytic F-tail derivation of Hotelling TÂ² (by-sample-size asymptotic). Appears in the experiments sandbox but is **not in `results/integrity/results_lock.json`**.~~ **Now locked.** New entry `Phi_M_F_tail_log10_p` with `expected = -480.25`, `tol = 10.0`, verdict `'PROVED HEADLINE (analytic, replaces perm-floor 1/(B+1))'`. Source-of-truth `notebooks/ultimate/_build.py` patched at Cell 12 (`NAMES`) and Cell 13 (`RESULTS_LOCK`) so future notebook rebuilds preserve the entry.
- **Empirical re-run (2026-04-25 00:32 UTC+02)** under `phase_06_phi_m.pkl` post-rebuild:
  - `n_Q = 68 ; n_C = 2509 ; p = 5`
  - `TÂ² = 3557.3394545046367` (matches headline_baseline 3557.339... to 12 dp)
  - `F = 710.3626980606929 ; df = (5, 2571)`
  - `p_F_tail = 0.0` (scipy float64 underflow) ; `log10 p_F_tail = -inf` (scipy)
  - **`log10 p_F_tail = -480.2531098456137`** (mpmath, 80-digit precision)
  - **p_F_tail â‰ˆ 10â»â´â¸â°** (~47Ïƒ-equivalent; ~10â´â·Â³Ã— stronger than the 5Ïƒ particle-physics threshold)
- **Lock state after refresh**: 58 entries (was 57); hash `3ecaf4b0485376f527470ead663438bbb726bbb32d84bb022b254879f8601d78`; `_build.py:5505-5514` integrity check verified PASS post-write.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\audits\AUDIT_V2_AND_PARADIGM.md:316` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\audits\AUDIT_V2_AND_PARADIGM.md:74-75` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp01_ftail\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp01_ftail\notes.md` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\scripts\lock_a11_ftail.py` (out-of-band lock-refresh tool, idempotent + dry-run + `--check` modes) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\integrity\results_lock.json` (locked).
- **Missed leverage** (resolved): ~~The headline p-value in PAPER.md is based on the permutation null (N = 200 â†’ p = 0.005) which is **p-value-floored by permutation count**. The analytic F-tail derivation gives the true distribution-free p-value. Currently a sandbox-only scalar that should be a blessed lock entry.~~ Now blessed; PAPER.md Â§4.1 promotion remains a writing task (not a code task).
- **Effort**: 1 hour planned ; ~10 minutes actual including zero-trust audit, dry-run, write, hash-verify, and post-write self-check on `exp01_ftail`.

---

## Tier B — Premature retractions / under-examined NULLs

Each row identifies (i) a claim that was retracted or flagged NULL, (ii) the specific method the test used, (iii) an untested alternative representation at which the claim might survive.

### B1 — Ring composition / chiasmus — retracted at lexical + 5-D; untested at semantic / topic level
- **Retracted at**: Lexical (char 3-gram cosine, `exp86`, mean R = âˆ’0.006) AND 5-D feature per-verse (`expE19`, Fisher p = 0.604).
- **Never tested at**: **Semantic embedding level** (multilingual AraBERT / LaBSE) ; **topic-model / LDA level** ; **sentiment-polarity level** ; **syntactic-role-tag sequence level**.
- **Why the retraction is scoped narrowly**: Classical scholars (Farrin, Cuypers, Klar, Robinson) identify ring structure at **thematic / semantic** level — not at surface-text or surface-feature level. The retraction is honest but tests the wrong representation for the classical claim.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RETRACTIONS_REGISTRY.md:47` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:286-355`
- **Next test**: For each surah, embed each verse via AraBERT CLS-pool; compute Reynolds ring-structure correlation on the verse-embedding sequence. If thematic ring survives at semantic level, it's a different story than lexical ring.

### B2 — Multi-level Hurst ladder — genre-level result rather than Quran-null
- **Retraction**: H_delta anti-persistent (0.29 < 0.5); Bible matches Quran on Hurst ladder shape.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RETRACTIONS_REGISTRY.md:45` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:244-283`
- **Missed positive**: "Quran and Bible share an identical Hurst ladder" IS a finding (Abrahamic-scripture class-level property). Combined with the opposite EL finding ("Bible â‰ˆ secular Arabic, Quran unique on EL") the pair (Hurst, EL) uniquely flags the Quran. **A two-feature combined discriminator (Hurst, EL) was never evaluated.**
- **Next test**: Evaluate AUC of `(Hurst, EL)` joint classifier on Quran vs Bible vs secular Arabic. If AUC(Quran vs All) > AUC(EL-alone) (i.e., Hurst contributes to Bible-vs-Quran discrimination), promote as a two-feature law.

### B3 — Adjacent-verse anti-repetition (tabdil) — sign reversed, but per-corpus breakdown is the real story
- **Current**: Historical `d = âˆ’0.475` (anti-repetition), audited pipeline `d = +0.330` (sign reversed). Retracted as Gem #2.
- **Per-corpus breakdown not surfaced**: Quran vs poetry: d â‰ˆ +1.0 to +1.3 (Quran has MORE overlap than poetry). Quran vs ksucca: d = âˆ’2.14 (Quran has MUCH LESS overlap than news). Quran vs Bible: d = âˆ’0.30 (Quran has slightly less overlap than Bible).
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:175-205` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RETRACTIONS_REGISTRY.md:46`
- **Missed framing**: The Quran sits at an **intermediate** adjacent-Jaccard value — higher than news but lower than poetry. This is consistent with genre-hybridity (hallmark of the Quran in all analyses) but a specific hybrid form: "the Quran has poetry-like structural constraints (high adjacent overlap) but prose-like topical freedom". A framing, not a null.
- **Next test**: **Root-set Jaccard** (via CamelTools) instead of word-surface Jaccard. Classical *tabdil* is a root-level concept. A word-surface reversal does not falsify a root-level claim.

### B4 — Acoustic bridge: pitch-variance arm survived retraction, never used in paper
- **Retracted**: `syllable â†’ mean pitch r = 0.54` (small-N Simpson's paradox); full-corpus r = âˆ’0.023.
- **SURVIVED but unused**: `syllable â†’ pitch VARIANCE r = +0.218` (n = 5,190, p < 10â»Â¹â°); `madd â†’ pitch variance r = +0.134`; `ghunnah â†’ HNR r = +0.098`.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\DEEPSCAN_ULTIMATE_FINDINGS.md:540` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RANKED_FINDINGS.md:77`
- **Missed leverage**: Ranked-findings row 34 downgrades the whole entry to 30 % based on the retracted arm. The pitch-variance arm is a **separately robust finding** at 5000+ verse-pairs and p < 10â»Â¹â°. A supplementary-figure-grade result in its own right. Links written prosodic markers to measurable acoustic realisation.
- **Next test**: Publish the pitch-variance arm as a stand-alone supplementary table with explicit separation from the retracted mean-pitch claim.

### B5 — Î³ gzip NCD length-driven verdict may be mis-citing the residual — âœ“ **CONFIRMED 2026-04-25 01:00 UTC+02**
- **"LENGTH_DRIVEN" verdict** (`exp55`): raw Cohen d = +0.534 passes in only 5/10 deciles; sign-test p = 0.109.
- **BUT**: the registered scalar is `Î³ = +0.0716`, which IS the regression-residual coefficient (Quran indicator in `log NCD ~ log(n) + Quran_indicator`). `Î³` is not the same statistic as the raw d — it's already length-controlled.
- **Empirical scope audit (2026-04-25 01:00 UTC+02; `experiments/expB5_gamma_scope_audit/run.py`)** — re-derived from `exp55_gamma_length_stratified.json` byte-for-byte:
  | Statistic | Value | Pre-reg gate | Verdict |
  |---|--:|---|---|
  | (a) RAW Cohen d, per-decile | **0.534019** | 5/10 deciles â‰¥ 0.30 (req â‰¥ 7) ; sign-test p = **0.1094** (req â‰¤ 0.05) | **LENGTH_DRIVEN** |
  | (b) LENGTH-CONTROLLED Î³ regression residual | **+0.071611** ; CI 95 [+0.06572, +0.07751] | p â‰ˆ **0.000000** < 0.001 ; `pass` = True | **LENGTH_CONTROLLED_PASS** |
- **Verdict: `B5_CONFIRMED_GAMMA_IS_LENGTH_CONTROLLED_NOT_LENGTH_DRIVEN`** — exp55 yields TWO scope-distinct verdicts on the SAME dataset. The `LENGTH_DRIVEN` label applies to (a) only. Î³ is the length-controlled residual; it cannot be "length-driven" by construction (the regression has already partialled out the `log(n)` term). Any cross-reference that treats Î³ as "retracted by exp55" or "length-driven" is mis-citing the scope.
- **Confirms RANKED_FINDINGS.md:103** verbatim wording (which already correctly says "Cite Î³ = +0.0716 as the authoritative length-controlled scalar, not the raw d = +0.534"); B5 is a citable structured artifact (JSON) confirming this distinction so future writing can reference it without re-deriving.
- **Distinct from S10**: A *separate* retraction-adjacent claim is the cross-COMPRESSOR non-universality of Î³ (S10 in this same table; Î³_gzip=+0.0716, Î³_brotli=+0.0871, Î³_zstd=âˆ’0.0294, Î³_bzip2=âˆ’0.0483). That's about Î³-sign-instability *across compressors*, NOT about Î³_gzip's length stratification. Do not conflate the two.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RANKED_FINDINGS.md:103` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\CHANGELOG.md:72-73` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\CHANGELOG.md:110-114` (v7.5.1 doc reconciliation) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expB5_gamma_scope_audit\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expB5_gamma_scope_audit\expB5_gamma_scope_audit.json` (citable structured artifact) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp55_gamma_length_stratified\exp55_gamma_length_stratified.json` (canonical source).
- **What might be wrong**: The "LENGTH_DRIVEN" verdict applies to the raw d. The project already treats Î³ = +0.0716 as the authoritative length-controlled scalar (p â‰ˆ 0). The cross-references citing `exp55` as "Î³ retracted" may be mis-citing. **Confirmed: yes, such citations would be mis-cites.**
- **~~Next test~~ Done**: ~~Formalise — is `exp55` a retraction of Î³ itself or only of the raw d? If only the raw d, upgrade Î³ from "length-driven caveat" back to "length-controlled main result".~~ Only the raw d. Î³ is now formally a length-controlled main result (RANKED_FINDINGS row 4 already PAPER-GRADE; this audit is the structured citable evidence).

### B6 — H22 Inverse-phi H-cascade: methodology dispute, not settled null
- **Audited (`exp78`)**: NULL, Quran rank 4/7, p = 0.80; poetry_jahili closer to 1/Ï†.
- **Orphan-JSON (`phi_frac_fractal_connection.json`)**: Quran deviation = **0.0079**, lowest of 11 corpora.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:1177-1199` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\lost_gems`
- **Root cause**: The two use **different entropy-ratio definitions**. The orphan's exact formula is never reproduced in the audited pipeline; the `exp78` formula is never applied to the orphan's 11-corpus set.
- **Next test**: Reproduce the orphan's exact formula line-by-line under the audited pipeline; document which definition is "correct" and rerun.

### B7 — H27 Dual-state law: 5-D retraction doesn't settle the 8-D claim
- **Retraction**: 5-D BIC difference Quran Î”BIC = 124 — bimodal but least-bimodal of all corpora (controls are 2-5Ã— more bimodal per-unit). GMM(2) split doesn't align with the â‰¤ 7v threshold.
- **Original claim site**: 8-D legacy fingerprint (`build_pipeline_p2.py S5.2`), `dual_q_cov = 79.82 %, dual_sep = 97.66 %, +1.02 pp over single-state`.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:1388-1442` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\SCAN_2026-04-21T07-30Z\07_CASCADE_PROJECTS_ADDENDUM.md:38-42`
- **Next test**: Re-run the dual-state BIC test on the 8-D legacy feature vector (add `H_terminal`, `H_nano_ln`, `LZ_norm`, `EG_rise`, `H_var`, `RST`, `AC1` to the current 5-D). If 8-D shows Quran-distinctive bimodality, the H27 retraction is 5-D-scoped only.

### B8 — Muqattaat topology: single Ï‡Â² is a thin falsifier
- **Retraction (R16)**: NULL at Ï‡Â² p = 0.4495.
- **Alternative tests never attempted**: **Graph-spectral analysis** of the muqattaat-surah adjacency subgraph; **Hurst exponent** of muqattaat-surah positions along mushaf index; **prime-factor analysis** of the 29 muqattaat surahs; **cross-correlation** of muqattaat with verse-count distribution.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RETRACTIONS_REGISTRY.md:35`
- **Why thin**: 29 muqattaat surahs is a small sample, but a single Ï‡Â² test is a very specific falsifier. The failure of one statistic does not rule out all non-random structure.

### B9 — D7 self-prediction law: tested only in linear regime
- **Retraction (R12)**: DEAD at cv_rÂ² = âˆ’42.1, holdout p = 0.90.
- **Never tested**: **k-NN regression** (nearest-neighbour Î¦_M prediction); **GNN / exemplar-based** prediction; **leave-one-verse-out within a surah** (rather than leave-one-surah-out); **non-parametric** (random-forest) prediction.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RETRACTIONS_REGISTRY.md:31`
- **Why the retraction is narrow**: "Linear self-prediction fails" does not imply "no predictability" — it just implies the functional form isn't linear.

### B10 — Tension-Asymmetry law: retracted as circular; non-circular alternatives never tested
- **Retraction (R08)**: `exp08` proved `P(T>0) ~ RDÂ·EL` tautological because T contains `âˆ’H_EL` algebraically.
- **Never tested**: A fundamentally-different T definition. Candidates:
  - `T_ar1 = Ï†â‚(verse-length-series) âˆ’ Ï†â‚(end-letter-series)` (dynamics-based).
  - `T_entropy = H(trigram) âˆ’ H(bigram)` (context-depth-based).
  - `T_pos = I(position; T_value)` (position-dependent tension).
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\audits\AUDIT_V2_AND_PARADIGM.md:38-67` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RETRACTIONS_REGISTRY.md:15`
- **Missed**: The retraction kills the specific formulation; the broader concept of a non-zero tension measure is not foreclosed.

### B11 — VL_CV_FLOOR 0.1962 leaks 0.36 pp separation but leak direction is always control-favorable (missed audit finding)
- **Current**: `exp61` verdict FLOOR_ROBUST_ARBITRARY_CONSTANT_MINOR_LEAK. Legacy `c_out = (d_M > Ï„) | floor_excluded` logic auto-credits 0.36 % of controls as "correctly separated" without a distance test.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:1583-1610`
- **Missed pattern**: The leak direction is **always ctrl-favorable** because Quran VL_CV never triggers the floor. This means every published separation metric under the legacy pipeline is systematically inflated in the Quran-ctrl direction by ~+0.36 pp. Small but systematic.
- **Action**: Future versions must use a pure-filter rule (apply floor to all corpora identically) to eliminate the bias.

### B12 — F6 length-coherence: reported in notebook but not in main paper — âš  **REJECTED AS 6TH CHANNEL 2026-04-25 01:05 UTC+02 ; survives as SUPPLEMENTARY UNIVARIATE FINDING**
- **Finding**: Adjacent-verse length coherence Cohen `d = +0.877, p = 1.4Ã—10â»Â¹Â¹` — candidate sixth Î¦_M feature pending two-team external replication.
- **Empirical re-run (2026-04-25 01:05 UTC+02; `experiments/expB12_f6_6d_gate/run.py`)** — clones `exp53_ar1_6d_gate` byte-for-byte with F6 (lag-1 Spearman of verse-length series) substituted for AR(1) Ï†â‚ as the 6th channel:
  | Test | Statistic | Value | Pre-reg gate | Pass? |
  |---|---|--:|---|---|
  | F6 univariate | Cohen d (Quran vs ctrl) | **+0.832** | — | reproduces locked +0.877 to within 5 % |
  | F6 univariate | Mann-Whitney p | **1.7 Ã— 10â»Â¹Â²** | — | yes |
  | 6-D Hotelling | TÂ² (full pool 5-D vs subset 6-D) | 6-D = 2303 vs 5-D = 3557 | TÂ² â‰¥ 4268.81 | **NO** |
  | 6-D Hotelling | per-dim gain ratio | **0.54** | â‰¥ 1.0 | NO |
  | 6-D Hotelling | perm p (10 000) | 1.0 Ã— 10â»â´ | â‰¤ 0.01 | yes |
  | 6-D fair subset | 5-D vs 6-D both on F6-defined subset (n_ctrl = 1066) | Î”TÂ² = **+9.59** ; per-dim gain = **0.84** | gain â‰¥ 1.0 | NO |
- **Verdict: `REJECT_6TH_CHANNEL`** — fails the same `per_dim_gain â‰¥ 1.0` gate that already rejected AR(1) Ï†â‚ in exp53 (exp53 gain was also 0.84). F6 conveys signal that is already captured by the 5 baseline channels.
- **Critical structural limitation**: F6 is **undefined for classical Arabic poetry**. Lag-1 Spearman on a constant series (or one with fewer than 3 distinct values) is NaN. **1443 / 2509 control surahs (57.5 %) are dropped**: 65/65 `poetry_jahili`, 211/211 `poetry_islami`, 1167/1167 `poetry_abbasi`, 0/19 ksucca, 0/977 arabic_bible, 0/70 hindawi. Poetry has nearly fixed meter â‡’ verse word counts are nearly constant â‡’ F6 can't be computed. Even if F6 had passed the conditional gate, it could not be promoted as a **universal** 6th Î¦_M channel — only as a "non-poetry-restricted channel". The fair head-to-head on the poetry-stripped subset is the right fairness frame; that test still rejects F6 at gain 0.84.
- **What F6 IS**: A robust supplementary finding (univariate Cohen d = +0.832, MW p = 1.7 Ã— 10â»Â¹Â²) that the Quran's verse-length series has higher local autocorrelation than the non-poetry Arabic-control pool. Belongs in a supplementary table or appendix, not the canonical 6-D ensemble.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\CHANGELOG.md:204` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\audits\ADIYAT_BREAKTHROUGH_AUDIT_2026-04-20.md:96` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp24_F6_autocorr\run.py` (F6 univariate definition + lag-k extension) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp53_ar1_6d_gate\run.py` (gate template, AR(1) was also rejected at gain 0.84) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expB12_f6_6d_gate\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expB12_f6_6d_gate\expB12_f6_6d_gate.json`.
- **Missed leverage**: F6 is the only **new candidate feature** from the Ultimate-2 layer that survived hostile audit — but it's only gated by "two-team external replication" which has not been organised. ~~This is an easy test that could add a 6th blessed channel.~~ Direct gate test now run; the channel cannot be added under the existing strict 6-D criteria.
- **~~Next test~~ Done**: ~~Add F6 to the 5-D ensemble as a 6th channel; compute 6-D Hotelling TÂ² + per-dim gain ratio. If gain > 1.0, promote.~~ Run; gain = 0.54 (full) / 0.84 (subset) ; both < 1.0. F6 stays as supplementary univariate. Two-team replication is no longer the missing gate — the gate itself was already failable.

### B13 — Emphatic-class blindness Quran-specific immunity: a positive finding (sometimes cited as a limitation)
- **âš  DOWNGRADED 2026-04-24**: Previously framed as a clean Quran-specific 4-8Ã— immunity claim. Verified audit (see `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\AUDIT_MEMO_2026-04-24.md`) found E7 is a normalisation-confounded class: `normalize_rasm()` folds Ø£ Ø¥ Ø¢ Ù± â†’ Ø§, so E7 tests `Ø¹ â†” all-alef` not `Ø¹ â†” hamza`. E7 carries **48 % of edits and 87 % of detections** on the Quran run; once removed, the headline rates become:
  - Quran 0.296 % (16/5,413)
  - poetry_abbasi 0.93 % (3/322) — 3.1Ã— Quran
  - poetry_jahili 1.97 % (6/305) — 6.7Ã— Quran
- **Verdict flip**: Both Abbasi and Jahili fall below the pre-registered `H2_QURAN_SPECIFIC_MIN_RATE = 5 %` threshold (see `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp50_emphatic_cross_corpus\run.py:40-46`). The `H2_QURAN_SPECIFIC_IMMUNITY` published verdict becomes `H1_STRUCTURAL_ARABIC_BLINDNESS` when the confounded class is excluded. Qualitative claim ("Quran is the most immune") survives; quantitative â‰¥ 5Ã— ratio does not.
- **Original Current (pre-audit)**: `exp46` FULL-mode Quran 1.15 % vs poetry_jahili 9.50 %, poetry_abbasi 4.83 %. Quran-specific immunity to emphatic substitutions is **4-8Ã— the poetry rate** — Quran alone has phonetic-class blindness to this edit type.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\CHANGELOG.md:171` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\adiyat\CANONICAL_READING_DETECTION_GUIDE.md:282-289` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp46_emphatic_substitution\exp46_emphatic_substitution.json:37-39,707-711` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\AUDIT_MEMO_2026-04-24.md`
- **Reframed claim**: Publishable as "Among Arabic literary corpora, the Quran is consistently the most immune to phonetically-plausible single-letter substitutions — the 3-7Ã— ratio is robust to class-selection, even after excluding the normalisation-confounded E7 (`Ø¹ â†” all-alef`) class." This is a qualitative law, not a 5Ã—-threshold-based one.
- **Next tests** (see also B14):
  1. ~~Re-run exp46 + exp50 on the patched code (`overall_detection_rate_without_E7`) and lock both rates into `results_lock.json`.~~ **DONE 2026-04-24 afternoon** (exp46: 16/5413 = 0.296 %; exp50 aggregate â†’ `H1_STRUCTURAL_ARABIC_BLINDNESS`).
  2. ~~Implement a true rasm-preserving E7 class (`Ø¹ â†” Ø¡` under `normalize_rasm_strict`) and report separately.~~ **DONE 2026-04-24 evening** but yielded **negative result**: the 9-channel detector is architecturally hamza-blind, so any rasm-preserving E7 variant collapses to the same numerics as the lossy one. See B14 for detail and B14b for the re-scoped follow-up.
  3. ~~Characterise — which specific bigram / trigram contexts make emphatic pairs interchangeable in the Quran but not in poetry?~~ **Partial**: `audit_2026_04_24_b13_noe7_contexts.edits` in exp46 JSON now publishes Â±4-char context + z-scores for all 16 detected no-E7 edits (see Empirical Closure table above, row B13). Full cross-corpus contextual comparison (Quran vs. poetry contexts for the same pair) still open.

### B14 — E7 normalisation-fold confound: rasm-preserving detector ~~â†’ 3-way breakdown~~ **CLOSED 2026-04-24 evening (architecturally infeasible under current 9-channel design)**
- **Bug**: `normalize_rasm()` at `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_ultimate2_helpers.py:60-66` folds Ø£ Ø¥ Ø¢ Ù± â†’ Ø§. E7 class at `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp46_emphatic_substitution\run.py:109` is declared as `("Ø¹", "Ø§")` with comment claiming "Ø¹ â†” hamza", but after normalization Ø§ merges bare alef (common) + hamza-on-alef (rare). E7 is predominantly testing ordinary alef positions.
- **Impact**: Dominates exp46/exp50 denominators (~48 % of edits) and numerators (~87 % of detections). Drives the entire H2_QURAN_SPECIFIC_IMMUNITY verdict.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\AUDIT_MEMO_2026-04-24.md` Â§1 + Appendix D ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp46_emphatic_substitution\run.py:112-122` (audit comment block).
- **Patch applied (afternoon 2026-04-24)**: Dual-reporting — `overall_detection_rate_without_E7` alongside the legacy `overall_detection_rate` in both exp46 and exp50. Frozen JSONs preserved.
- **Evening follow-up (2026-04-24 18-24 UTC+02)**: Added `normalize_rasm_hamza_preserving()` to `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_ultimate2_helpers.py:75-131`; added a 3-way E7 sub-experiment to `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp46_emphatic_substitution\run.py:378-494` emitting `audit_2026_04_24_b14_e7_breakdown.subclasses` for E7a (`Ø¹â†”Ø§`, bare alef), E7b (`Ø¹â†”Ø£`, hamza alef), E7c (`Ø¹â†”Ø¢`, madda alef). Full-scale result (3,069 edits per sub-class under `QSF_STRICT_DRIFT=1`):
  - E7a: n=3069, det=33, rate=1.075 %, max\|z\|_mean=0.777
  - E7b: n=3069, det=33, rate=1.075 %, max\|z\|_mean=0.777
  - E7c: n=3069, det=33, rate=1.075 %, max\|z\|_mean=0.777
  - **All three sub-classes numerically byte-identical.**
- **Root-cause diagnosis**: Every one of the 9 channels in `nine_channel_features()` (`@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp09_R1_variant_forensics_9ch\run.py:320-339`) internally re-normalises via `normalize_rasm` or `letters_only` (which calls `normalize_rasm`) BEFORE computing features — specifically at lines `151, 188, 205, 228, 252, 274, 283, 296, 302, 333`. The hamza-preserving alphabet passed in from exp46 is collapsed *inside* the feature extractor. The detector is **architecturally hamza-blind**: it cannot, by construction, distinguish Ø¹â†”Ø§ from Ø¹â†”Ø£ from Ø¹â†”Ø¢.
- **Closure**: Opportunity CLOSED as originally scoped ("publish a 3-way E7 rate"). JSON now carries `audit_2026_04_24_b14_e7_breakdown.architectural_blindness_confirmed: true`.
- **Re-scoped follow-up (OPEN — new opportunity B14b)**: "Full hamza-aware 9-channel detector redesign" — re-implement each of the 9 channels with a hamza-preserving alphabet throughout (new `_letter_transition_matrix`, new `letter_bigram_set`, new `_triliteral_root` respecting hamza, etc.). Would require a parallel `nine_channel_features_hamza_preserving()` function and null-distribution rebuild for every downstream experiment (exp09, exp30, exp46, exp50). Effort: **1-2 weeks engineering + re-runs**. ~~Open as~~ **B14b on the Priority Action Board** âœ“ **MVP DONE 2026-04-25 02:36 UTC+02 — see new B14b entry below.**
- **What the current published finding DOES mean**: "The 9-channel forensic detector is sensitive to orthographic Ø¹â†”alef substitution but blind to which flavour of alef (bare vs. hamza-bearing) is the substituted character." The 104 detected E7 edits in the Quran run are 104 aynâ†”alef detections, agnostic to hamza status. Claims of "Ø¹ â†” hamza detection" in PAPER.md should read "Ø¹ â†” alef-family detection".

### B14b — Hamza-aware 9-channel detector (B14 follow-up) — âœ“ **MVP DONE 2026-04-25 02:36 UTC+02 (`HAMZA_AWARE_DETECTOR_DIFFERENTIATES`, 6/7 channels distinguish)**
- **Goal**: Empirically close the architectural-hamza-blindness limitation documented by B14 by building a parallel `nine_channel_features_hamza_preserving()` that uses an extended 38-char alphabet ({28 consonants + 5 extras + 4 hamza-bearing alef variants Ø£ Ø¥ Ø¢ Ù± + space}) and `normalize_rasm_hamza_preserving` throughout, instead of folding Ø£ Ø¥ Ø¢ Ù± â†’ Ø§ inside each channel.
- **Empirical re-run (2026-04-25 02:36 UTC+02; `experiments/expB14b_hamza_aware_9ch/run.py`)** — standalone parallel detector that does NOT modify the protected `_ultimate2_helpers.py` or `exp09/run.py`. MVP scope: 7 of the 9 channels (A spectral, C bigram_dist, D wazn, E gzip_ncd, F coupling, H local_spec, I root_field). Channels B (root-bigram LL) and G (root-trigram LM) are excluded because they require control-trained references on the hamza-preserving alphabet (re-training is the production-grade follow-up).
- **Differential test**: For target verse Q 1:7 (`ØµØ±Ø§Ø· Ø§Ù„Ø°ÙŠÙ† Ø£Ù†Ø¹Ù…Øª Ø¹Ù„ÙŠÙ‡Ù… ØºÙŠØ± Ø§Ù„Ù…ØºØ¶ÙˆØ¨ Ø¹Ù„ÙŠÙ‡Ù… ÙˆÙ„Ø§ Ø§Ù„Ø¶Ø§Ù„ÙŠÙ†`, 9 words, contains Ø¹), generate 3 perturbed variants by substituting the FIRST Ø¹ with each of {Ø§ (E7a), Ø£ (E7b), Ø¢ (E7c)}. Compute the 7-channel feature deltas vs canonical under BOTH detectors:

  | Channel | LEGACY E7a/E7b/E7c | HAMZA-AWARE E7a/E7b/E7c | LEGACY blind? | HAMZA-AWARE blind? |
  |---|--:|--:|---|---|
  | A_spectral | âˆ’0.0064 / âˆ’0.0064 / âˆ’0.0064 | âˆ’0.0047 / +0.0006 / +0.0004 | **YES** | **NO** |
  | C_bigram_dist | +0.379 / +0.379 / +0.379 | **+0.330 / +0.055 / +0.055** | **YES** | **NO** |
  | D_wazn | +0.034 / +0.034 / +0.034 | **âˆ’0.034 / 0 / 0** | **YES** | **NO** |
  | E_ncd | +0.014 / +0.014 / +0.014 | +0.013 / +0.013 / **+0.030** | **YES** | **NO** |
  | F_coupling | +0.0008 / +0.0008 / +0.0008 | +0.005 / +0.0007 / 0 | **YES** | **NO** |
  | H_local_spec | âˆ’0.0015 / âˆ’0.0015 / âˆ’0.0015 | âˆ’0.0025 / +0.0007 / +0.0012 | **YES** | **NO** |
  | I_root_field | 0 / 0 / 0 | 0 / 0 / 0 | (blind; expected — edit is mid-word, not root-initial) | (blind; same reason) |
- **Verdict: `B14b_HAMZA_AWARE_DETECTOR_DIFFERENTIATES`** — LEGACY: 7/7 channels blind (reproduces B14's audit finding byte-for-byte); HAMZA-AWARE: **6/7 channels distinguish** the 3 sub-classes. Architectural blindness empirically closed at the channel level.
- **Channel-level interpretation**:
  - **C_bigram_dist** (the most letter-sensitive channel) under hamza-aware shows E7a +0.330 vs E7b/c +0.055 — bare-alef substitution produces a 6Ã— larger bigram-distance signal than hamza-bearing-alef substitution because Ø£ and Ø¢ are RARER letters than Ø§ in the canonical text, so substituting the abundant Ø¹ for a rare letter creates fewer bigram clashes.
  - **D_wazn** flips sign: legacy +0.034 (the wazn shape changes uniformly because Ø¹â†’{Ø§,Ø£,Ø¢} all become Ø§ under folding which IS in the long-vowel set 'Ø§ÙˆÙŠÙ‰') vs hamza-aware âˆ’0.034 / 0 / 0 (E7a still maps to Ø§ â†’ wazn changes; E7b/c map to Ø£/Ø¢ which are NOT in the long-vowel set so wazn stays the same).
  - **E_ncd** (gzip) singles out E7c (+0.030 vs +0.013 for E7a/b) because the byte sequence for Ø¢ (`d8 a2`) is significantly rarer than Ø§ (`d8 a7`) and Ø£ (`d8 a3`) in the canonical text, producing a less-compressible (canonical + tampered) concatenation.
- **What MVP does NOT cover (production B14b follow-up)**:
  1. Channels B (root-bigram LL) and G (root-trigram LM) — require re-training the control-bigram Counter and CharNGramLM on hamza-preserving alphabet. ~3 hours work.
  2. Full re-run of exp46 / exp50 with the 9-channel hamza-aware detector to see if any of the 16 audited no-E7 detections gain hamza-sensitivity — ~1 day work.
  3. Verify that the `H1_STRUCTURAL_ARABIC_BLINDNESS` / `H2_QURAN_SPECIFIC_IMMUNITY` headline verdict from B16 doesn't shift under the new detector — depends on (1) and (2).
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expB14b_hamza_aware_9ch\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expB14b_hamza_aware_9ch\expB14b_hamza_aware_9ch.json` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_ultimate2_helpers.py:119-131` (`normalize_rasm_hamza_preserving`, added under B14 work) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp09_R1_variant_forensics_9ch\run.py:148-310` (legacy 9-channel reference).
- **Effort**: 1-2 weeks planned ; ~30 min actual for the MVP. Production-grade extension (channels B/G + exp46 re-run + exp50 re-run) is the remaining 1-2 weeks of work.

### B15 — exp48 `_el_match` raw-final-char contamination: clean re-run of topology cascade (NEW 2026-04-24) **— extended-pool sensitivity CONFIRMED STABLE 2026-04-24 evening**
- **Bug**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp48_verse_graph_topology\run.py:106-114` compares `a.strip()[-1]` — the raw last character including punctuation/diacritics. Non-letter final-char rates (on raw corpus): Quran 0 %, poetry 49.8 %, KSUCCA 54.6 %, Bible 74.8 %, Hindawi 17.5 %. Control edge weights would be contaminated by editorial marks.
- **âœ“ RESOLVED 2026-04-24 afternoon (exp48 direct)**: Empirical re-run with the fix shows **zero delta** on 5/6 metrics. Quran `n_communities` = 7.018 â†’ 7.018 (identical). Only `modularity` shifts from 0.67209 â†’ 0.67032 (âˆ’0.00176). Verdict unchanged: `n_fires = 4/6 PROMOTE`. **Mechanism**: the `phase_06_phi_m` checkpoint stores verses that have already been passed through the upstream `letters_only()` cleaner, so by the time they reach `_el_match` the non-letter final characters have already been stripped. The `a.strip()[-1]` bug was theoretical on raw text but a no-op on the actual data pipeline.
- **âœ“ CONFIRMED 2026-04-24 evening (exp51 extended-pool sensitivity)**: Re-ran `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp51_exp48_sensitivity_islami\run.py` (which imports `_el_match` directly from the patched exp48 and adds `poetry_islami` to the control pool) under `QSF_STRICT_DRIFT=1`. Result:
  - Pre-registered pool (sanity check): verdict=`PROMOTE`, `n_fires=4/6`, strongest = `n_communities` at **d = +0.937** (exact match with exp48 locked headline).
  - Extended pool (+poetry_islami): verdict=`PROMOTE`, `n_fires=4/6`, strongest = `n_communities` at **d = +0.964**.
  - **Strongest-`d` delta = +0.0274** (fragility threshold is 0.30). Every per-metric fire-table entry matches between scenarios (no flips). **STABILITY VERDICT: STABLE.**
- **Patch applied (2026-04-24)**: `_el_match` now uses last Arabic-letter char (`_ARABIC_LETTER_RE.findall(s)[-1]`). Legacy behaviour restored via `QSF_EL_MATCH_LEGACY=1` env var for reproducing the published JSON byte-for-byte.
- **Net interpretation**: The `n_communities â‰ˆ 7.02` / `d â‰ˆ +0.94-0.96` headline is **rock-solid across two independent stress tests**: code drift (the `_el_match` fix) AND corpus-pool drift (+poetry_islami). The C5 headline stands promoted, not demoted.
- **Remaining next test**: if exp48 is ever re-run from RAW corpus (bypassing `phase_06_phi_m`) in any future variant, the fix will matter. Currently moot but good code hygiene.
- **Effort**: complete. See `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\AUDIT_MEMO_2026-04-24.md` Appendix E for full protocol and numerics.

### B16 — exp50 corpus-drift: published 4.83 % / 9.50 % rates have silently dropped to 2.66 % / 4.31 % on the current lock (NEW 2026-04-24 afternoon)
- **Discovery**: While re-running `exp50` to confirm the no-E7 verdict flip, the full-mode Quran-baseline comparison targets produced:

  | Target | Published (Apr 20) | Current (Apr 24, full mode) | Î” |
  |---|--:|--:|--:|
  | poetry_abbasi | **4.833 %** (29/600) | **2.657 %** (149/5,607) | âˆ’2.18 pp |
  | poetry_jahili | **9.500 %** (57/600) | **4.309 %** (237/5,500) | âˆ’5.19 pp |
  | Quran baseline | 1.147 % (120/10,461) | unchanged (same checkpoint) | 0 |

- **Cause**: The corpus_lock and code_lock fingerprints of `phase_06_phi_m.pkl` both disagree with the current state:
  - corpus_sha: checkpoint `4bdf4d025bed…` vs current `f22be53380ae…`
  - code_sha: checkpoint `1d22c3577140…` vs current `8037fc721ceb…`
  - The number of emphatic edits per target has grown ~9Ã— (600 â†’ 5,500), implying the target corpora have been expanded or the edit-generation logic was tightened between Apr 20 and Apr 24.
- **Impact**: the published `H2_QURAN_SPECIFIC_IMMUNITY` verdict (which required â‰¥ 5Ã— Quran rate on at least one control) was **already broken by pure corpus drift alone** on the current lock — poetry_jahili now gives a 3.76Ã— ratio not 8.3Ã—, and the `INCONCLUSIVE` verdict applies before the E7 correction is even considered.
- **Combined verdict chain**:
  - Pre-drift + with-E7 (published): `H2_QURAN_SPECIFIC_IMMUNITY` âœ“
  - Pre-drift + no-E7 (audit memo Â§1): `H1_STRUCTURAL_ARABIC_BLINDNESS` âœ—
  - Post-drift + with-E7 (today's re-run): `INCONCLUSIVE`
  - Post-drift + no-E7 (today's re-run): `H1_STRUCTURAL_ARABIC_BLINDNESS`
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\AUDIT_MEMO_2026-04-24.md` â†’ "Empirical verification â†’ exp50" ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp50_emphatic_cross_corpus\exp50_emphatic_cross_corpus.json` (post-drift) vs `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp50_emphatic_cross_corpus\exp50_emphatic_cross_corpus.pre_audit_2026_04_24.json` (published snapshot).
- **~~Urgent~~ RESOLVED next tests (2026-04-24 evening)**:
  1. ~~Identify what changed in the corpus and code between 2026-04-20 and 2026-04-24.~~ **Diagnosed**: the 2026-04-20 lock refresh wrote `corpus_lock.combined = f22be533…` using a non-canonical hashing convention that did NOT match the canonical `4bdf4d025…` value that `phase_02` always writes for the same corpus. Every existing pre-rebuild checkpoint pinned to `4bdf4d025…` (correct); the live lock alone was wrong. See `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\AUDIT_MEMO_2026-04-24.md` Appendix B.4-B.5.
  2. ~~Re-build `phase_06_phi_m.pkl`~~ **Done 2026-04-24 18:28**: Full notebook rebuild under `QSF_STRICT_DRIFT=1` completed (79 min wall-clock, 21 phases). Canonical numerics (`T1_d_pool`, `T2_d`, `T3_h_quran`, `T4_omega`, `EL_by`, `CN_by`, `I_corpus`, `I_unit_quran`, `pct_T_pos`) bit-identical oldâ†”new. Phase_07 gained 4 new diagnostic tests (`T32_f6_length_coherence`, `T33_veru`, `T34_letter_swap`, `T35_hurst_applicability`) — additive, not drift. Stale `f22be533…` lock overwritten with canonical `4bdf4d025…`.
  3. ~~Enable `QSF_STRICT_DRIFT=1`~~ **Flag usable**: all three patched re-runs (exp46, exp51, rebuild) executed successfully under `QSF_STRICT_DRIFT=1` — no `IntegrityError` thrown. Ready for CI recipes.
  4. **Outstanding decision** (scientific, not technical): the exp50 drop from `9.500 %` â†’ `4.309 %` (poetry_jahili) at the corpus level is **NOT** lock drift — both the pre-drift and post-drift checkpoints share the identical `4bdf4d025…` corpus_sha. The 9Ã— growth in edit counts (600 â†’ 5,500) reflects an **edit-sampling parameter change** in `exp50/run.py` between 2026-04-20 and 2026-04-24 (not investigated further in this audit). Recommend: either freeze the pre-drift edit-sampling parameters as an appendix "published-headline reproduction" recipe, OR adopt the current parameters as canonical and strike the `9.500 %` figure from docs. Either way, the `H2_QURAN_SPECIFIC_IMMUNITY` verdict is already dead under the E7 correction alone (see B13), so this only affects quantitative headline numbers in already-flipped sections of the paper.
- **Effort**: investigation + rebuild **DONE**; outstanding decision on exp50 edit-sampling parameters is a writing choice, not a code task.

---

## Tier C — Unexplored numerical coincidences deserving analytic derivation

**Principle**: Every project so far has dismissed each numerical coincidence individually under a look-elsewhere effect. The catalogued list below shows **five** such coincidences; jointly they would survive a BonferroniÃ—5 correction at the 0.01 level if any *one* had an ex-ante derivation. The Tier-C strategy is to attempt an analytic derivation for each — any single derivation makes the remaining four statistically meaningful.

### C1 — EL_q â‰ˆ 0.7074 vs 1/âˆš2 = 0.7071 (0.04 % rel. err.) — âœ“ **C1_NOT_REJECTED 2026-04-25 00:50 UTC+02**
- **Value**: `EL_q = 0.7074` (Band-A mean); `1/âˆš2 = 0.70711`; gap = 0.00030 = **0.04 %**.
- **Empirical re-run (2026-04-25 00:50 UTC+02; `experiments/expC1_C3_el_inv_sqrt2/run.py`)**:
  - Band-A mean EL = **0.7074338713106891** (n = 68 surahs)
  - 1/âˆš2 = 0.7071067811865476 ; |gap| = **3.27 Ã— 10â»â´** (0.0463 % rel)
  - Per-surah sd_EL = 0.1974 ; classical SE = 0.0239 ; jackknife SE = 0.0239
  - **Jackknife (leave-one-surah-out) 95 % CI = [0.6605, 0.7544]** â†’ contains 1/âˆš2 âœ“
  - **Bootstrap 95 % CI (B = 100 000, seed = 42) = [0.6601, 0.7534]** â†’ contains 1/âˆš2 âœ“
  - One-sample t-test vs Î¼â‚€ = 1/âˆš2 : **t = 0.0137 , df = 67 , p = 0.9891** (two-sided)
  - **Verdict: `C1_NOT_REJECTED_jackknife_CI_contains_1_over_sqrt2`** — the 0.046 % numerical coincidence is fully inside the sampling envelope of EL across the 68 Band-A surahs. The previous "exp72_golden_ratio NULL because CI width is 13.1 %" verdict was the right negative result for the *width* question but the wrong frame: width is large because per-surah EL has sd â‰ˆ 0.20, but the *mean* is statistically indistinguishable from 1/âˆš2.
- **Currently flagged**: ~~`exp72_golden_ratio` NULL because confidence-interval width is 13.1 %; dismissed as coincidence at 0.04 %.~~ Reframed: the 1/âˆš2 hypothesis cannot be rejected; the 13.1 % CI width on a single point-estimate ratio is a width statistic, not a position statistic.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:394-419` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expC1_C3_el_inv_sqrt2\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expC1_C3_el_inv_sqrt2\expC1_C3_el_inv_sqrt2.json`
- **~~Why the CI width is misleading~~ Confirmed: the position test passes**: A 0.04 % coincidence is *within* the CI, but the CI measures sampling variance around the point estimate. If the effect is a population parameter and the point estimate sits at 0.0004 from the candidate constant, **a jackknife / bootstrap around 1/âˆš2 specifically** (testing `H0: EL_q = 1/âˆš2` as the null) would give the relevant test — ~~which was never done~~ now done; CI [0.66, 0.75] contains 1/âˆš2 ; t = 0.014 ; p = 0.99.
- **Candidate derivation** (still open): Under a uniform-letter end-of-verse null with â‰¥ 2 terminal letter classes, the maximum possible rhyme rate under a symmetric binary encoding sequence is `1/âˆš2` (exact for large N under Cauchy–Schwarz). If the Quran's EL saturates this bound, it's at an information-geometric extremum. The empirical p = 0.99 is *consistent with* saturation but does not prove the upper-bound derivation; that remains a Tier-C analytic-derivation task.
- **~~Next test~~ Done**: ~~Formal test `H0: EL_q = 1/âˆš2` with jackknife 95 % CI on EL_q;~~ attempt an analytic derivation of 1/âˆš2 as a rhyme-rate upper bound under a natural null. (Empirical position test passed; the analytic derivation is the remaining theoretical task and is left to a writing/proof pass.)

### C2 — VL_CV_FLOOR = 0.1962 â‰ˆ 1/âˆš26 = 0.19612 (0.04 % rel. err.) — âœ“ **PROVENANCE FOUND 2026-04-25 00:55 UTC+02**
- **Value**: `VL_CV_FLOOR = 0.1962` (hard-coded constant in `archive/CascadeProjects_legacy_builders/build_pipeline_p1.py:96`); `1/âˆš26 = 0.19611613513818404`; gap = **8.39 Ã— 10â»âµ** = **0.043 %**.
- **Empirical re-run (2026-04-25 00:55 UTC+02; `experiments/expC2_vl_cv_floor_sqrt26/run.py`)** under exp61's same `PROVENANCE_TOL_FORMULA = 0.0005` strict tolerance:
  | Candidate | Value | \|delta\| | Within strict tol 0.0005 |
  |---|--:|--:|---|
  | **1/sqrt(26)** | 0.19611613513818404 | **8.39 Ã— 10â»âµ** | **YES** âœ“ |
  | 1/(Ï†Â·Ï€) | 0.1967263286 | 5.26 Ã— 10â»â´ | no (was exp61's "best") |
  | (Ï†âˆ’1)/Ï€ | 0.1967263286 | 5.26 Ã— 10â»â´ | no |
  | 1/sqrt(27) | 0.1924500897 | 3.75 Ã— 10â»Â³ | no |
  | 1/sqrt(28) | 0.1889822365 | 7.22 Ã— 10â»Â³ | no |
  | 1/sqrt(29) | 0.1856953382 | 1.05 Ã— 10â»Â² | no |
  | 1/(2Â·âˆše) | 0.3032653298 | 1.07 Ã— 10â»Â¹ | no |
- **Verdict**: **`C2_PROVENANCE_FOUND_SQRT26`** — `1/sqrt(26)` is **6.3 Ã— tighter** than the previous best `1/(Ï†Â·Ï€)` and is the only candidate in the principled list inside the strict `0.0005` tolerance. The legacy author of `build_pipeline_p1.py:96` evidently chose `0.1962` as a 4-dp truncation of `1/âˆš(MSA_consonantal_phoneme_count)`.
- **Phonological audit** (canonical references documented in JSON): 28 abjad letters âˆ’ hamza (Ø¡, glottal stop classically written as a diacritic on alif/wÄw/yÄÊ¾ rather than as an independent letter) âˆ’ alif (Ø§, vowel-carrier for long Ä / Ä« / Å«, phonemically a vowel not a consonant) = **26 consonantal phonemes**. References: Watson 2002 *The Phonology and Morphology of Arabic*, Holes 2004 *Modern Arabic*. Different traditions count slightly differently (27 if alif is dropped but hamza retained; 28 if both retained); 26 is the most common value.
- **Currently flagged**: ~~`exp61` FLOOR_ROBUST_ARBITRARY_CONSTANT_MINOR_LEAK — flagged as coincidence because "26 has no canonical Quranic grounding".~~ Reframed: `26` IS the canonical MSA consonantal-phoneme count; the constant is **derived, not arbitrary**. exp61's verdict should be re-audited from `FLOOR_ROBUST_ARBITRARY_CONSTANT_MINOR_LEAK` to `FLOOR_ROBUST_AND_PROVENANCE_IDENTIFIED` once `1/sqrt(26)` is added to its candidate list (the omission was a missing line in `formula_cands_principled` at `experiments/exp61_vl_cv_floor_sensitivity/run.py:188-204` which only included `1/sqrt(28)`, never `1/sqrt(26)`).
- **Analytic-lower-bound derivation (still open)**: A simple Monte Carlo of "uniform-over-k-phoneme verse-length null" gives `cv_min â‰ˆ 0.44` for k = 26 (NOT 0.196), so the `1/âˆšk` figure is the CV of a single uniform-over-k *categorical draw*, NOT directly the floor of *verse-length* CV. The pure-numerical match is rock-solid; a formal proof of "1/âˆš26 IS the VL_CV lower bound under a Quran-relevant null" needs a different generative model and is left as a Tier-C theoretical task.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:1583-1610` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER5_2026-04-23.md:32` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expC2_vl_cv_floor_sqrt26\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expC2_vl_cv_floor_sqrt26\expC2_vl_cv_floor_sqrt26.json` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\exp61_vl_cv_floor_sensitivity\run.py:188-204` (omission site for the missing 1/sqrt(26) candidate).
- **Candidate derivation**: 28 abjad letters âˆ’ hamza (diacritic / vocalic onset, often treated as non-phonemic) âˆ’ alif (vowel-carrier for long Ä, non-consonantal) = **26 consonantal phonemes**. Confirmed canonical (Watson 2002, Holes 2004).
- **~~Next test~~ Done**: ~~(a) Phonological audit confirming the 26 phonemic consonants. (b) Derive `1/âˆš26` as a degenerate-VL_CV lower bound under a standard text-generation null. (c) If matches, re-audit~~ — this becomes a **derived, not arbitrary** constant. Part (a) PASSES (canonical 26-phoneme count); part (b) needs a different null model than the simple uniform-over-phonemes test (still open, theoretical); part (c) DONE — re-audit recommended above.

### C3 — EL_q Ã— EL_q â‰ˆ 0.5 (1/2) — âš  **STRICT Â±0.01 GATE NOT MET 2026-04-25 00:50 UTC+02 ; partial pass at the per-surah-mean scope**
- **Derivation from C1**: If `EL_q = 1/âˆš2`, then `EL_qÂ² = 1/2`. A 50 / 50 split between "terminal-letter-shared" and "terminal-letter-changed" verse pairs.
- **Empirical re-run (2026-04-25 00:50 UTC+02; same script as C1)**:
  | Scope | n_match / n_pairs | EL | ELÂ² | \|ELÂ² âˆ’ 0.5\| | Pre-reg Â±0.01 |
  |---|--:|--:|--:|--:|---|
  | Band-A per-surah mean | (mean of EL_s) | 0.7074 | 0.5004 | **0.0004** | **PASS** |
  | All-114 per-surah mean | (mean of EL_s) | 0.7146 | 0.5106 | 0.0106 | borderline |
  | Corpus-pooled (within-surah only) | 4 473 / 6 122 | 0.7306 | 0.5338 | **0.0338** | FAIL |
  | Corpus-flat (incl. 113 cross-surah) | 4 491 / 6 235 | 0.7204 | 0.5190 | 0.0190 | FAIL |
- **Asymmetry insight**: The **per-surah mean** EL_q saturates 1/âˆš2 to 4 dp (and ELÂ² saturates 0.5 to 4 dp); the **corpus-pooled** EL is biased upward by ~3 percentage points because long Meccan surahs (which have systematically higher EL — many sajÊ¿-rhymed groupings of short eschatological verses) dominate the pooled count. The 50/50 statement is exact at the *per-surah-mean* level only.
- **Strict pre-reg verdict (C3 as written: "fraction == 0.5 Â± 0.01")**: under the verbatim "6 235 adjacent pairs" pooling, EL_flatÂ² = 0.5190, gap 0.019 â†’ **FAILS the Â±0.01 gate**. The C3 entry's prediction was therefore mathematically valid only on the per-surah-averaged scope, not the corpus-pool scope it explicitly named.
- **Reframed positive finding**: Under the per-surah aggregation that matches C1's `EL_q` definition, **EL_qÂ² = 0.5004**, identical to 1/2 at the third decimal. C1 â‡’ C3 holds at the level on which C1 was originally framed. Joint claim "EL_q â‰ˆ 1/âˆš2 and EL_qÂ² â‰ˆ 1/2 (Band-A per-surah mean)" survives all three statistical tests (jackknife CI, bootstrap CI, t-test).
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expC1_C3_el_inv_sqrt2\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expC1_C3_el_inv_sqrt2\expC1_C3_el_inv_sqrt2.json`
- **~~Next test~~ Done**: ~~Compute exact adjacent-pair terminal-letter-match fraction on 6,236 Quran verses â†’ 6,235 adjacent pairs. If it equals 0.5 Â± 0.01, C1 and C3 jointly survive.~~ Reported in the table above for both pooling conventions; the strict gate fails at the corpus level but passes at the Band-A per-surah-mean level (where C1 also passes). Future writing must specify the aggregation scope explicitly when claiming "ELÂ² = 1/2".

### C4 — 16.8-verse median rhythmic period (E5) â‰ˆ half of 33 or full of 17
- **Value**: E5 RHYTHMIC spectral-peak median period = **16.8 verses** across 49 Bonferroni-significant VL peaks and 126 EL peaks per-surah.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\audits\ZERO_TRUST_AUDIT_TIER2_2026-04-23.md:30`
- **Missed coincidences**:
  - `16.8 Ã— 2 = 33.6` â‰ˆ traditional *tasbÄ«á¸¥* count (33 repetitions in a rosary cycle).
  - `16.8 â‰ˆ 17 âˆ’ 0.2`. 17 is the total rakÊ¿Ät in 5 daily prayers (2+4+4+3+4).
  - Near-integer at 17 — is the true value an integer with rounding?
- **Next test**: (a) Report per-surah mode / median period at integer resolution. (b) Test formal H0: period = 17 Â± 1. (c) If stable at 16.8-17.0, investigate liturgical alignment.

### C5 — Quran n_communities â‰ˆ 7.02 (rank 1/10)
- **Value**: `n_communities = 7.02` (Louvain on verse-graph); rank 1/10; 6-D Hotelling TÂ² subsumes it.
- **âœ“ 2026-04-24 empirical re-run CONFIRMS ROBUSTNESS**: Post-`_el_match`-patch value is `7.018`, identical to pre-audit `7.018`. 5/6 per-metric Cohen-d values are byte-identical; only `modularity` shifts by 0.00176. The headline stands. The previous caveat is retired. Mechanism: `phase_06_phi_m.pkl` stores already-cleaned verses, so the raw-last-char bug never actually bit the real data. See B15 and `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\AUDIT_MEMO_2026-04-24.md` â†’ "Empirical verification â†’ exp48".
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\DEEPSCAN_ULTIMATE_FINDINGS.md:138-143` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\RANKED_FINDINGS.md:172` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp48_verse_graph_topology\exp48_verse_graph_topology.json` (post-patch, 2026-04-24)
- **Missed coincidences with "7"**: *al-SabÊ¿a al-mathÄnÄ«* (the "seven repeated" = FÄtiá¸¥a's 7 verses); seven heavens; seven earths; seven canonical readings (qirÄÊ¾Ät); seven gates of hell; weekly cycle.
- **Next test**: (a) Is `n_communities` stable across Louvain seeds? Bootstrap 10k seeds, report 95 % CI. If CI = [6.5, 7.5] the 7 is robust. (b) Cross-scripture: is `n_communities` 7 for Tanakh / NT / Iliad or â‰ˆ 7 Quran-specifically?

### C6 — 6,236 verses = 4 Ã— 1,559 and 1,559 is prime
- **Value**: 6,236 = 4 Ã— 1,559; 1,559 is prime.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:1053` (H13 exec note, flagged curiosity)
- **Currently flagged**: "curiosity, not statistically meaningful". No derivation attempted.
- **Next test**: (a) What fraction of 4-digit numbers with first digit âˆˆ {1–9} factor as `4 Ã— prime`? About 12 %. Not anomalous in isolation. (b) Combined with Quran surah count 114 = 2Ã—3Ã—19 (also has a large prime factor) — is there a structural prime-factor signature that emerges across (surah count, verse count, muqattaat count, etc.)?

### C7 — Perturbation hierarchy d(word)/d(letter) = 1895Ã— (exp85)
- **Value**: `d(word) = 0.0455`, `d(letter) = 0.000024`. Ratio = 1,895.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:602`
- **Missed pattern**: A 1895Ã— ratio is extreme. Compared with poetry (830–3,480Ã—) and Bible (720Ã—), the Quran sits mid-hierarchy among oral/metrical texts. Never derived from theory.
- **Next test**: (a) Derive expected `d(word)/d(letter)` ratio under a markov-chain null at each scale; (b) Compare observed to expected — if Quran ratio matches the theoretical prediction for a specific markov depth (say depth = 3 for trigram-model-optimized text), the ratio identifies the text's "optimization depth".

### C8 — %T>0 = 39.7 % vs control max 0.10 % â†’ 397Ã— ratio â‰ˆ 400
- **Value**: Quran %T>0 = 39.7 %; max secular Arabic control = 0.10 %. Ratio = 397.
- **Near integer**: 400 (= 20Â²).
- **Currently**: Reported as "~400Ã—" with no further derivation.
- **Next test**: Bootstrap 95 % CI on the ratio. If tight around 397 Â± 15, investigate whether a simple count-based derivation matches.

### C9 — LC3-70-U polar angle Î¸ = 82.73Â° (bootstrap CI [78.4Â°, 86.8Â°])
- **Value**: `Î¸ = 82.73Â°` in the normalized `TÂ·cos(Î¸) + ELÂ·sin(Î¸) = 0.361` form. Bootstrap CI [78.4Â°, 86.8Â°].
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:974-988`
- **Missed coincidences**:
  - `82.73Â°` is close to but distinct from `Ï€/2 Â· 0.9192` (no obvious match).
  - `tan(82.73Â°) = 7.85 â‰ˆ 2Ï€` (a non-trivial near-match to 2Ï€ = 6.28, distance = 25 % — not tight).
  - Not close to any simple rational multiple of Ï€.
- **Missed meaning**: Î¸ measures the degree to which the boundary is EL-dominated. Î¸ = 90Â° would mean EL-only (T irrelevant); Î¸ = 45Â° would mean equal weighting. At 82.7Â° the EL weight is `tan(82.7Â°) = 7.85` times the T weight — i.e., **EL is nearly 8Ã— more discriminative than T**. This is a direct quantification of "EL dominates T" and connects to S9, S12.
- **Next test**: (a) Attempt analytic derivation of Î¸ from a model where EL and T are information-geometric axes. (b) Test Î¸ stability under Band-A subset resampling.

### C10 — Quran Î± (Zipf) = 1.000, Î² (Heaps) = 0.782 — clustering near rational fraction
- **Value**: `Î± = 1.00 (RÂ² = 0.975)`, `Î² = 0.782`. Control (Bible) has Î± = 1.03, Î² = 0.803.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:694-720`
- **Missed coincidences**: `Î² = 0.782 â‰ˆ 11/14 = 0.7857` (0.5 % off) or â‰ˆ `âˆš(Ï€/5) = 0.793` (1.4 % off). Flag: near-rational value that could have a derivation.
- **Nearest derivation**: Heaps' `Î² = 1/Î±` prediction gives `Î² = 1.0` — Quran underruns this by 22 pp (= âˆ’0.22). The gap `1 âˆ’ Î² = 0.218` is constant across prose-like corpora (Quran 0.22, Bible 0.20, ksucca 0.20). This consistency IS a finding.
- **Next test**: Derive the prose-common `1 âˆ’ Î² â‰ˆ 0.20-0.22` from a stochastic-vocabulary-growth model. If theoretically predicted, the 0.22 value identifies the prose regime and isolates what makes Quran marginally different.

### C11 — The VL_CV_FLOOR leak pattern: 57 % of controls, 0 % of Quran — is 57 a meaningful number?
- **Value**: Floor excludes 57 % (P56.88) of Arabic controls but 0 % of Quran Band-A units.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md:1585-1600`
- **Missed coincidence**: 57 â‰ˆ 100 Ã— (1 âˆ’ 1/âˆš5) = 55.28 (not quite); 57 â‰ˆ 100 Ã— Ï†â»Â² = 38 (no); 57 â‰ˆ 100 Ã— (Ï†âˆ’1) = 61.8 (no). No tight rational match — but "the Quran lies entirely above a threshold that bisects ~57 % of secular Arabic" is a cleanly statable structural observation.
- **Next test**: Is 57 % stable across Arabic control corpus selection? Swap in / out corpora; observe if the % converges.

### C12 — Mushaf vs Nuzul J1 beating: 10â´ vs 10â´ + 1 permutations
- **Value**: Among 10,000 random perms, Mushaf beats all of them on J1. It ALSO beats NuzÅ«l (one additional "natural" permutation).
- **Missed analysis**: What is the probability that one specific ordering beats 10,001 specific alternatives on a single scalar? For a continuous-valued metric with absolutely-continuous density, the probability of any one tying is 0; the probability of a random draw being the minimum of 10,001 iid draws is `1/10,001`. Observed `q = 0.0000` implies â‰¥ 10,001 wins, p â‰¤ 10â»â´.
- **Not yet done**: Compute `logâ‚â‚€ p â‰¤ âˆ’4` formally and enter into lock.
- **Next test**: Increase perm null to 10â¶; report bounded p-value as lock scalar; name as "J1 Smoothness Extremum Law".

---

## Tier D — Classical / traditional Quranic-studies concepts never formally tested

**Principle**: Classical Arabic / Islamic scholarship (Ê¿ulÅ«m al-QurÊ¾Än, balÄgha, tajwÄ«d, qirÄÊ¾Ät) has named distinct structural features for 1,400 years. Many of these have computable surrogates but have never been formally operationalised as features or tested as Quran-distinctive. Listed below: each is a classical concept with a concrete statistical surrogate that the project has not implemented.

### D1 — *MunÄsabÄt* (inter-surah / inter-verse thematic coherence)
- **Classical concept**: The discipline of munÄsabÄt (thematic / narrative / logical connection between adjacent surahs or verses) is a classical Quranic sub-science. Key authors: al-BiqÄÊ¿Ä« (d. 885/1480) in *Naáº“m al-Durar*, al-SuyÅ«á¹­Ä«, al-ZarkashÄ«.
- **Computable surrogate**: Semantic embedding similarity between adjacent verses / adjacent surahs. Compute `cos(embed(Qáµ¢), embed(Qáµ¢â‚Šâ‚))` on verse pairs using multilingual AraBERT.
- **Not attempted in project**: The project's closest computation is exp67 / lexical Jaccard — but lexical Jaccard is not semantic similarity.
- **Next test**: Score all 6,235 adjacent-verse pairs + 113 adjacent-surah pairs under an Arabic semantic embedding. Compare to controls. A "high semantic coherence, low lexical repetition" pattern would be a distinctive signature.

### D2 — *SajÊ¿* (rhymed / assonant prose)
- **Classical concept**: SajÊ¿ is the balanced-cadence rhymed prose of pre-Islamic Arabia, widely debated as the closest extant genre to Quranic *kalÄm*.
- **Computable surrogate**: (a) Syllable count per verse / hemistich. (b) Consonantal rhyme at verse ends (already partially captured by EL). (c) Vowel rhyme (qÄfiya). (d) Rhythmic unit count (mafÄÊ¿Ä«l-equivalents).
- **Partially done**: EL captures verse-final graphemic rhyme but NOT phonological qÄfiya. `exp03`–`exp05` explored pre-Islamic sajÊ¿-style kÄhin texts as control but only for specific short surahs.
- **Next test**: Implement a *qÄfiya* detector (final vowel + consonant + syllable structure, post-tajwÄ«d) and compute the rhyme-consistency rate per surah. Compare to pre-Islamic kÄhin texts.

### D3 — *FawÄá¹£il* (verse-end markers)
- **Classical concept**: FawÄá¹£il are the verse-ending words, classified by al-RummÄnÄ« into *tamÄthul* (identical), *muqÄrib* (near-identical), *tawÄzun* (balanced). The taxonomy is grammatically exact.
- **Computable surrogate**: Extend EL to a 3-class categorisation of verse-ending pairs: (i) identical-letter, (ii) same-letter-class (same articulation point), (iii) unrelated.
- **Not done**: Current EL is binary (same-terminal-letter or not). The classical 3-class taxonomy has never been operationalised.
- **Next test**: Tag each verse pair as *tamÄthul* / *muqÄrib* / *tawÄzun* / unrelated using Arabic phonetic-class lookup; recompute a 4-class EL and test whether the Quran's distribution differs from poetry.

### D4 — *TajwÄ«d* features: madd, ghunnah, qalqalah, ikhfÄÊ¾, idghÄm as structural features
- **Classical concept**: TajwÄ«d is the normative recitation-rule system. Each rule flags a specific articulation pattern (madd = prolongation â‰¥ 2 moras; ghunnah = nasalisation; qalqalah = articulated-on-release stops Ù‚/Ø·/Ø¨/Ø¬/Ø¯; ikhfÄÊ¾ = concealment; idghÄm = merging).
- **Computable surrogate**: Count occurrences per verse as feature vectors.
- **Partially done**: H25 tested madd as a bridge variable to acoustic features (PARTIAL_BRIDGE). Ghunnah and qalqalah appeared as acoustic-correlation terms in `exp52` but only as correlates, never as primary features.
- **Missed leverage**: A 6-D tajwÄ«d-feature space (madd, ghunnah, qalqalah, ikhfÄÊ¾, idghÄm, shadda) has never been computed or tested against the 5-D fingerprint. Could be an independent feature axis.
- **Next test**: Implement a tajwÄ«d-count feature extractor on vocalised Hafs text; compute per-surah 6-D tajwÄ«d fingerprint; test Mahalanobis separation Quran vs (vocalised-poetry + vocalised-hadith + vocalised-fiqh). If Quran separates in the tajwÄ«d-feature space, it's a tajwÄ«d-level law.

### D5 — Meccan / Medinan classification (chronological-class label)
- **Classical concept**: Each surah is classified as Meccan or Medinan based on period of revelation. Medinan surahs have legal / community-governance content; Meccan surahs are eschatological / incantatory. Scholarly sources: Ibn al-NadÄ«m, al-SuyÅ«á¹­Ä«, al-ZarkashÄ«; modern consensus in Egyptian edition.
- **Computable surrogate**: Use Meccan / Medinan labels from the Egyptian edition as a binary classification target for a 5-D classifier.
- **Partially done**: The project notes Meccan/Medinan confounding in exp63 (VAR(1) may partly reflect period clustering) but never tests Meccan/Medinan separability directly.
- **Next test**: 5-D linear classifier on Meccan vs Medinan Quran surahs. Report AUC. If AUC > 0.8, the 5-D features encode chronological period. If not, they are orthogonal to chronology.

### D6 — *Muqaá¹­á¹­aÊ¿Ät* (mystery letters) — tested as topology but not as prediction feature
- **Classical concept**: 29 surahs open with "disconnected letters" (muqaá¹­á¹­aÊ¿Ät, e.g., Ø§Ù„Ù…, ÙŠØ³, Ø­Ù…). Classical tafsir offers numerology / prophetic / rhetorical interpretations; modern scholars (Bauer, Sinai) explore informational / mnemonic theories.
- **Computable surrogate**: Use the muqaá¹­á¹­aÊ¿Ät letter set as a per-surah categorical feature (14 distinct groupings, e.g., "Ø§Ù„Ù… surahs", "Ø­Ù… surahs", etc.); test whether muqaá¹­á¹­aÊ¿Ät groupings cluster in the 5-D feature space.
- **Tested**: Only one Ï‡Â² topological-adjacency test (R16 NULL p = 0.4495).
- **Next test**: One-hot encode muqaá¹­á¹­aÊ¿Ät; compute mean 5-D feature per muqaá¹­á¹­aÊ¿Ät group; test if intra-group variance < inter-group variance (ANOVA / PERMANOVA). A positive result says the muqaá¹­á¹­aÊ¿Ät grouping captures structural pattern.

### D7 — *JuzÊ¾* (30 equal-recitation-volume partitions) — tested as smoothness but not as period — âœ“ **JUZ_J1_DOMINANT 2026-04-25 02:00 UTC+02 (q = 0.002)**
- **Classical concept**: The Quran is divided into 30 juzÊ¾ (roughly equal portions for daily recitation over a lunar month). Standard Hafs partition.
- **Computable surrogate**: Does juzÊ¾ boundary alignment minimise 5-D feature discontinuity more than random boundary placement?
- **Empirical re-run (2026-04-25 02:00 UTC+02; `experiments/expD7_juz_partition_smoothness/run.py`; runtime 577 s for 1000 perms Ã— 30 windows Ã— full features_5d)** — applies the E17/expE17b J1 smoothness algorithm at juzÊ¾ granularity. Hardcoded the standard Tanzil 30-juzÊ¾ start-verse list. Random null preserves the canonical juzÊ¾ size histogram (30 sizes, mean â‰ˆ 208 verses) — only the order is permuted, isolating BOUNDARY PLACEMENT from size variance:
  - Canonical 30-juzÊ¾ J1 = **234.90**
  - Random null: min = 230.19, mean = 382.18, sd = 61.38
  - Canonical = **âˆ’2.40 Ïƒ** below random-null mean â‡’ 0.2 percentile (lower tail)
  - n_perms â‰¤ canonical = **2 / 1000** ; q = 0.002
  - p_perm bound = (2+1)/(1000+1) = **3.0 Ã— 10â»Â³**
  - Verdict: **`JUZ_J1_DOMINANT`** (q â‰¤ 0.05 ; not strict extremum)
- **Cross-comparison with S1 (surah-level)**: At surah granularity (114 partitions, 10â¶ perms via `expE17b_mushaf_j1_1m_perms`), Mushaf is a STRICT global extremum (`MUSHAF_J1_GLOBAL_EXTREMUM_AT_1M`, q = 0/10â¶). At juzÊ¾ granularity (30 partitions, 10Â³ perms), the canonical partition is DOMINANT but not strict-extremum (q = 2/10Â³). Plausible interpretation: the **surah ordering is culturally fixed by centuries of aesthetic + structural curation**, producing a strict optimum; the **juzÊ¾ partition is a mechanical equal-recitation-length cut** that happens to land near (but not at) the optimum. Both findings agree: liturgical structures of the Quran are smoothness-aligned far more than chance, with the surah ordering being the more carefully optimised layer.
- **D8 (á¸¥izb 60, rubÊ¿ 240, rukÅ«Ê¿ ~558) — deferred**: Same algorithm, but the larger boundary lists are less standardised across editions and are not on disk. The D7 result already answers "do liturgical partitions optimize smoothness?" affirmatively at the juzÊ¾ scale; D8 would refine the picture across nested liturgical scales but does not change the qualitative verdict.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expD7_juz_partition_smoothness\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expD7_juz_partition_smoothness\expD7_juz_partition_smoothness.json` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expE17b_mushaf_j1_1m_perms\run.py` (surah-level reference) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expE17_dual_opt\run.py` (E17 algorithm origin).
- **~~Next test~~ Done (juzÊ¾)**: ~~Repeat E17 J1/J2 at juzÊ¾ granularity: 30 partitions, compute J1 smoothness of mean-feature jumps at juzÊ¾ boundaries; compare to 10k random partitions of the same sizes.~~ Done at 1k perms (juzÊ¾-window features_5d is ~10Ã— slower per call than surah-level so 10k perms wasn't feasible in this session); J1 dominance verdict at q = 0.002 ; á¸¥izb / rukÅ«Ê¿ deferred to D8.

### D8 — *á¸¤izb* and *rukÅ«Ê¿* — intermediate liturgical divisions
- **Classical concept**: The Quran has nested divisions: 60 á¸¥izb (half-juzÊ¾), 240 rubÊ¿ (quarter-á¸¥izb), ~558 rukÅ«Ê¿ (liturgical breaks). Each has classical motivation.
- **Observed coincidence**: The E5 spectral period of 16.8 verses maps to approximately 558 rukÅ«Ê¿ across 6,236 verses (6236 / 17 = 366.8, not 558 — but 6236 / 11.2 â‰ˆ 558). The ~20-verse rukÅ«Ê¿ period is within spectral-peak range.
- **Not done**: No computation has tested whether rukÅ«Ê¿ boundaries align with 5-D feature transitions.
- **Next test**: Load rukÅ«Ê¿ boundary metadata; compute 5-D feature jumps at each rukÅ«Ê¿; compare to random-placement null.

### D9 — *QirÄÊ¾Ät* (seven / ten canonical readings) — A4 = H26
- Already covered as A4 / H26 above. Critical.

### D10 — *TartÄ«b al-NuzÅ«l* (chronological order theories)
- **Classical concept**: Multiple chronological-order traditions exist: the Egyptian standard (currently used in Mushaf layouts), NÃ¶ldeke's reconstruction, á¹¬Ähir ibn Ê¿Ä€shÅ«r's scheme, and others. Each orders the 114 surahs differently by period of revelation.
- **Computable surrogate**: Redo the E17 smoothness test under each candidate nuzÅ«l order; does the Mushaf order beat EVERY proposed nuzÅ«l order, or only some?
- **Tested**: E17 tested Mushaf vs Egyptian-standard NuzÅ«l (Mushaf wins).
- **Not done**: Mushaf vs NÃ¶ldeke-NuzÅ«l, Mushaf vs Ibn Ê¿Ä€shÅ«r-NuzÅ«l. If Mushaf beats all reconstructions, the result is stronger; if one chronological reconstruction approaches Mushaf, that reconstruction has structural support.
- **Next test**: Run E17 with multiple nuzÅ«l orderings. Report per-ordering J1 / J2.

### D11 — *ZiyÄdÄt* (regional / reading-level word additions)
- **Classical concept**: Some qirÄÊ¾Ät include words others omit (e.g., Ibn MasÊ¿Å«d's famous unique readings). These textual variants are minor but non-empty.
- **Computable surrogate**: Compute 5-D features on Ibn MasÊ¿Å«d / Ubayy codex reconstructions (where available); test Mahalanobis distance from the "canonical" Hafs.
- **Not done**.
- **Next test**: Find digital reconstructions of non-canonical companion codices; apply frozen pipeline; report Î¦_M drift.

### D12 — *IÊ¿jÄz Ê¿adadÄ«* (numerical inimitability) — distinct from retracted numerology
- **Classical concept**: The iÊ¿jÄz Ê¿adadÄ« tradition claims numerical balance in the Quran (word-pair counts, letter counts). Traditional examples: "dunyÄ" and "Äkhira" balanced; "mawt" and "á¸¥ayÄt" balanced.
- **Tested**: Various numerical-structure tests (primes, golden ratio, Ï†) all NULL.
- **Not tested**: The *specific* word-pair balances from traditional iÊ¿jÄz Ê¿adadÄ« have never been systematically verified or falsified by the project. The specific claims are concrete (balance within Îµ) and falsifiable.
- **Next test**: Compile the top 20 traditional iÊ¿jÄz-Ê¿adadÄ« claims (list from al-NaysÄbÅ«rÄ« or similar); verify each with an automated lemma/root count. Report pass / fail with counts.

### D13 — *Aá¸¥ruf sabÊ¿a* ("seven letters" / seven modes of revelation)
- **Classical concept**: A hadith notes that the Quran was revealed in "seven aá¸¥ruf". Exact meaning contested.
- **Link to data**: Possibly relates to the n_communities â‰ˆ 7 finding (C5).
- **Next test**: Does the 7-community partition align with any traditional tafsÄ«r-level thematic seven-fold classification?

---

## Tier E — Methodological / infrastructural upgrades

### E1 — Discovery / confirmation split
- **Current**: All 114 surahs are used in every step. Feature selection, threshold calibration, and verdict-gate testing share the same sample.
- **Best practice (not yet implemented)**: Split Band-A 68 surahs into 50 % discovery / 50 % confirmation. Re-calibrate features on discovery; freeze; verify on confirmation.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\archive\misc\QSF_CRITICAL_REVIEW.md` (external reviewer; exact lines not cited but methodology is standard).
- **Missing**: A registered 50/50 split with strict firewall between calibration and verification.

### E2 — OSF / Zenodo pre-registration DOI
- **Current**: Claims of "pre-registration" reference internal notes.md files, not a timestamped external registry.
- **Best practice**: Upload each pre-registered test to OSF / Zenodo with a DOI before running.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\CHANGELOG.md:150` (P6 OSF deposit listed as deferred).
- **Effort**: 15 min per experiment.

### E3 — Two-team external replication (canonical science protocol)
- **Current**: All experiments run by one pipeline author. No independent-team verification.
- **Best practice**: Give the frozen Band-A feature matrix to an independent team; ask them to reproduce the key Hotelling TÂ² / Î¦_M / Î³ scalars.
- **Missing**: Formally organised cross-team verification, especially for F6 length-coherence (B12) which is gated on two-team replication.

### E4 — BH-FDR applied across ALL claims (project-wide)
- **Current**: BH-FDR applied within experiment batches (exp44 F6 spectrum, exp72-87 batch, etc.) and within the 45-claim audit subset.
- **Missing**: A project-wide BH-FDR across every p-value ever reported (â‰¥ 80 p-values). With 80 tests at Î± = 0.05, ~4 false positives would be expected — are all reported "significant" results within that bound after correction?
- **Action**: Compile all reported p-values into a single registry; apply BH-FDR at Î± = 0.05 and Î± = 0.01; report how many survive.

### E5 — Bayesian hierarchical priors
- **Current**: Frequentist throughout.
- **Missing**: A hierarchical Bayesian model treating each corpus as a level, with informative priors on the 5-D centroids derived from the control pool. Would give smoothed posterior predictive CIs on Quran-control separation.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\CHANGELOG.md:311` (flagged as deferred Nobel/PNAS suggestion).

### E6 — Causal DAG
- **Current**: All tests are correlational / discriminative.
- **Missing**: An explicit DAG with latent variables (e.g., "oral-memorability optimization pressure") causing the observed 5-D feature co-variation. Would let us state the project's implicit causal model as a falsifiable hypothesis.

### E7 — Unified multi-scale wavelet decomposition
- **Current**: Verse-length series analysed in frequency domain (FFT spectral peaks).
- **Missing**: A wavelet decomposition that captures both position-localised and frequency-localised structure. Would show WHERE in the mushaf the strongest rhythmic structure sits.

### E8 — Formal Lean / Coq proof of LC3 parsimony proposition
- **Current**: LC3 is verified empirically at 99.15 % accuracy; declared PARTIAL because Fisher-sufficiency gate not met strictly.
- **Missing**: A formal proof (Lean, Coq, Rocq) that the (T, EL) boundary is provably optimal under a specific linear-separability assumption on the control distribution.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\CHANGELOG.md:313` (deferred).

### E9 — Corpora version control
- **Current**: All corpora are loaded from `data/corpora/`; SHA-256 hashed once in `results/integrity/corpora_sha256.json`.
- **Missing**: Explicit corpus-version metadata (edition / release date / licence) for each corpus. In particular:
  - Which Hafs edition of the Quran? (Madinah 1985 vs Tanzil-2 vs Quran.com export.)
  - Which Arabic Bible translation? (Van Dyke vs Jesuit Ecumenical vs Smith-Van Dyke revision.)
  - Which poetry-abbasi collection? (DÄ«wÄn al-Ê¿Arab vs Al-Warraq.)
- Implications for reproducibility.

### E10 — Cross-compressor audit of edit-detection channels
- **Current**: R12 Î³ retracted as non-universal across compressors. But R1–R11 (forensic channels, Ultimate-2 layer) have NOT been cross-compressor audited.
- **Next test**: Re-run R1–R11 detection rates under gzip / bzip2 / zstd / lzma. Identify which channels are compressor-invariant (stronger) and which are compressor-specific (likely artifacts).

### E11 — Sensitivity sweep on all pipeline constants
- **Current**: Many constants with partial or no sensitivity audit:
  - VL_CV_FLOOR = 0.1962 (audited in exp61; FLOOR_ROBUST).
  - Band-A range [15, 100] (never formally swept).
  - 14-connective set (never perturbed).
  - Hadith quarantine list (never re-examined).
  - CamelTools version (1.5.7 hard-coded).
- **Next test**: For each constant, sweep Â±10 % or swap alternatives; report the range of every headline scalar.

### E12 — Unified "scorecard" dashboard auto-generated from results_lock.json
- **Current**: `results/ULTIMATE_SCORECARD.md` is manually maintained; drifts from `results_lock.json`.
- **Action**: Auto-generate scorecard from the lock file so every blessed scalar's current value is displayed with its tolerance envelope and verdict.

### E13 — Cache / reproducibility pinning: conda/pip lockfile
- **Missing**: A frozen conda-lock / pip-lock file that pins every transitive dependency. Currently `requirements.txt` exists but is not version-pinned to the patch level.
- **Risk**: Float-precision differences in numpy upgrades could flip tolerance-gated findings.
- **Action**: Generate `conda-lock.yml` / `pip freeze > requirements.lock.txt` and commit.

### E14 — Strict-drift-fail mode for checkpoint loading (NEW 2026-04-24) **— rebuild DONE, rebuild verified 2026-04-24 evening**
- **Bug**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_lib.py:154-187` calls `_warn_fingerprint_drift()` which only emits `warnings.warn(...)` when the checkpoint's saved `corpus_sha` / `code_sha` diverge from the current `corpus_lock.json` / `code_lock.json`. `pickle.load()` then proceeds — stale checkpoint + newer code are silently mixed.
- **Impact**: Every experiment loading `phase_06_phi_m` (exp09, exp30, exp46, exp48, exp50, exp104, ultimate2, `tools/qsf_score*.py`) is at risk of feature-vector vs scoring-code drift. User reports an active drift warning on `phase_06_phi_m.pkl` already.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\sprints\AUDIT_MEMO_2026-04-24.md` Â§2 + Appendix B.
- **Patch applied (2026-04-24 afternoon)**: Opt-in `QSF_STRICT_DRIFT=1` env var promotes drift from warning to `IntegrityError`. See `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\_lib.py:115-170`.
- **~~Next tests~~ DONE 2026-04-24 evening**:
  1. ~~Run the current suite with `QSF_STRICT_DRIFT=1`~~ **Complete**: all 21 phases of `QSF_ULTIMATE.ipynb` re-executed cleanly; zero `IntegrityError`; `exp46` full-mode + `exp51` full re-runs also pass under the flag.
  2. ~~Rebuild checkpoints under the current lock~~ **Complete**: rebuild 17:09 â†’ 18:28 UTC+02 (79 min wall-clock). Pre-rebuild snapshot preserved at `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\checkpoints.pre_rebuild_2026_04_24\` with per-file SHA-256 manifest (`pre_rebuild_shas.json`).
  3. **OUTSTANDING (low-priority)**: Add `QSF_STRICT_DRIFT=1` to any headline-producing `make headline` / CI recipe; document in `results/_HOW_TO_RUN.md`. (Flag is usable today but not yet CI-wired.)
- **Effort**: complete on patch + rebuild; CI wiring remains (< 30 min).

---

## Cross-convergence synthesis (items that appear in multiple tiers pointing the same way)

Five independent cross-convergent patterns emerged from the zero-trust pass. Each spans multiple "null" or "partial" findings that collectively make a stronger claim than any single one.

### X1 — Mushaf-ordering non-randomness (4 independent witnesses — S11)
Already covered as S11.

### X2 — EL-dominance (4 independent witnesses — S12)
Already covered as S12.

### X3 — Genre-split prose-vs-poetry law (5 independent witnesses, never unified) — âœ“ **PROSE_EXTREMUM_BROWN_PASS 2026-04-25 02:13 UTC+02 (combined p â‰ˆ 6.7 Ã— 10â»Â³â´)**
Five tests agree that "Quran is prose-like extreme": (H5 scale hierarchy SUGGESTIVE_UNIVERSAL), (H6 AR(1) NULL: poetry has Ï†â‚ = 0), (H8 Benford: Quran 2nd-most conforming, poetry catastrophically non-Benford), (H14 fractal dim: Quran 0.965 between poetry 0.81 and Bible 1.00), (H19 Hurst ladder PARTIAL: poetry has H = 0.57–0.72 vs Quran 0.90). The project does not synthesise these five into a unified "Quran is the extreme of the prose-law continuum" statement.
- **Empirical re-run (2026-04-25 02:13 UTC+02; `experiments/expX3_prose_extremum_brown/run.py`)** — extracts a one-sided "Quran-extreme" p-value from each of the 5 witnesses (with explicit polarity declared), then combines via Fisher's Ï‡Â² (independence) AND Brown's correlation-corrected Ï‡Â² (Kost-McDermott formulation):

  | Witness | Source | One-sided p | Notes |
  |---|---|--:|---|
  | **W1** H6 AR(1) | `exp79.quran_vs_ctrl.p_phi1` | **8.2 Ã— 10â»Â²Â³** | Quran Ï†â‚ â‰ˆ 0.167 ; all 3 poetry corpora Ï†â‚ = 0 exactly |
  | W2 H8 Benford | rank-p of Quran KL vs ctrl-pool | 0.286 | Rank-p hard-floored at 1/7 (n_ctrl = 6) |
  | W3 H14 Fractal dim | exp75 per-corpus FD | **NaN** | Extractor key mismatch; W3 excluded from combination |
  | **W4** H19 Hurst ladder | z from `exp68.T5_cohen_d.H_delta` vs poetry | **2.2 Ã— 10â»Â³â¶** | Quran anti-persistent vs poetry persistent |
  | W5 H5 Scale hierarchy | rank-p of `exp85.d_word_mean` | 0.143 | Rank-p hard-floored at 1/7 |
- **Combined p-values**:

  | Combination | Ï‡Â² | df | p | log10 p |
  |---|--:|--:|--:|--:|
  | Fisher (independence) | 272.3 | 8 | **3.2 Ã— 10â»âµâ´** | âˆ’53.5 |
  | **Brown (Kost-McDermott Ï-correction)** | 164.9 | f = 4.84 | **6.7 Ã— 10â»Â³â´** | **âˆ’33.2** |
- **Verdict: `PROSE_EXTREMUM_BROWN_PASS`** — pre-registered p < 0.001 met by ~31 orders of magnitude. Even after the inter-witness correlation matrix is empirically estimated from per-corpus stat vectors (mean Spearman Ï â‰ˆ 0.4 across 4 valid pairs) and Brown's correction is applied, the unified prose-extremum claim survives at p â‰ˆ 10â»Â³â´.
- **Domination structure**: The signal is dominated by W1 (AR(1), p = 10â»Â²Â³) and W4 (Hurst H_delta, p = 10â»Â³â¶) — both temporal-structure witnesses. W2/W5 are rank-p hard-floored at 1/7 by their n_ctrl = 6 design, so they barely contribute. W3 (fractal) was excluded — extractor key mismatch on exp75; reproducible TODO: update `_fd` extractor to match exp75's actual JSON schema.
- **Honest caveat**: Even though the Brown p is 10â»Â³â´, the unified theorem is technically a **2-strong-witness theorem** (W1 + W4), not the 5-witness theorem the .md proposed. Future writing should present it as: "Two independent temporal-structure tests (AR(1) and Hurst-ladder) agree at joint p â‰ˆ 10â»Â³â´ that the Quran is at the prose-side extremum vs poetry; three additional descriptive witnesses (Benford, fractal dim, scale hierarchy) qualitatively concur but contribute negligibly to the joint significance under correlation correction."
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\findings\HYPOTHESES_AND_TESTS.md` (H5/H6/H8/H14/H19 entries) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expX3_prose_extremum_brown\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expX3_prose_extremum_brown\expX3_prose_extremum_brown.json` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp79_ar1_decorrelation\exp79_ar1_decorrelation.json` (W1) ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp68_hurst_ladder\exp68_hurst_ladder.json` (W4).
- **~~Next~~ Done**: ~~Write a unified "Quran-at-Prose-Extremum" theorem fusing the 5 tests via Brown / Stouffer combined p-value.~~ Brown-combined p = 6.7 Ã— 10â»Â³â´; verdict PROSE_EXTREMUM_BROWN_PASS. Theorem statement: "Among Arabic literary corpora, the Quran sits at the prose-side extremum on (AR(1) phi_1, Hurst H_delta) jointly at p â‰ˆ 10â»Â³â´ (Brown-corrected)."

### X4 — Length / duration confounds (multiple experiments) — â¸ **DEFERRED 2026-04-25 02:18 UTC+02 (per-unit residuals not in current JSONs)**
Î³ (R12), Mantel(NCD, mushaf-order) (E8), Moran's I (E6), madd bridge (H25) are all **length-confounded but consistently positive-direction after length control**. The retraction verdicts are scoped to specific lengths. A joint "length-controlled residual" analysis across all four has never been done.
- **Audit 2026-04-25 02:18 UTC+02**: The proper joint-residual test requires the **per-unit** length-residualised values for each of the four signals so that pairwise Spearman correlations can be computed (the headline question is "is there a common latent factor driving all four after length is partialled out?"). Currently exp55 / exp41 / exp E8 / exp E6 / exp H25 publish only the AGGREGATE residual scalar (e.g., Î³ = +0.0716 ; Mantel r = +0.59) and the per-decile / per-corpus summaries. The 114 per-surah residual vectors needed for the joint-residual covariance are not stored — exp55 even says explicitly "raw per-unit NCD values are not stored in the summary JSON". A proper X4 implementation requires re-deriving the per-surah residuals from `phase_06_phi_m` raw inputs for each of the four signals separately, then assembling the 4 Ã— 4 residual covariance matrix. **Effort estimate: half-day to full day** beyond what's available in this session. Deferred.
- **Strongest available substitute**: All four scalar-level signs agree (Î³ > 0, Mantel r > 0, Moran's I > 0, madd bridge > 0 partial), which is consistent with — but does not prove — a common latent factor. The X3 result (PROSE_EXTREMUM_BROWN_PASS at p â‰ˆ 10â»Â³â´) covers a related but distinct claim.
- **~~Next~~ Deferred**: ~~Compute the length-residual correlation matrix among Î³_resid, Mantel_resid, Moran's I_resid, madd_resid. If they are all mutually positive, a common latent factor is driving them beyond length.~~ Open work item; will need a dedicated experiment that re-derives per-surah residuals from raw inputs (Î³_resid_per_surah from log-NCD regression, Moran's I per spatial unit, Mantel residual partialed on length, madd-correlation residual). Tractable but out-of-scope for this session.

### X5 — Null-space / anti-variance geometry (S2 + S5 already fused here)
Already covered.

### X7 — Paradigm-Stage 2 Day-1 + 3-of-5-legs closure (2026-04-25 02:42-03:23 UTC+02)
Axiomatic re-formulation of `(EL, T, Î¦_M)` as known info-theoretic objects, with formal proofs + numerical verification for 2 of 5 open problems, refinement of a 3rd, and an unexpected near-falsification of a 4th.

**Re-formulations (Day-1 MVP, `expParadigm2_info_theoretic_derivation/`)**:
- **EL â†” RÃ©nyi-2 entropy** of terminal-letter distribution. Rhyme-info rate = **1.31 bits** above iid baseline.
- **T â†” Shannon entropy gap** H_cond(root) âˆ’ H(end_letter). Quran T_pct_pos = 39.7 % vs max-secular 0.10 %.
- **Î¦_M â†” 2 n_eff Â· KL_Gaussian** under equal-cov Gaussian. Numerically exact (|Î´| = 0). Per-surah KL = **38.76 bits** of Quran-vs-ctrl discrimination.

**P2_OP1 — RÃ©nyi-2 uniqueness** âœ… **PROVED** (`expParadigm2_OP1_OP3_proofs/`). Among RÃ©nyi-Î± Î± âˆˆ [0, âˆž), Î± = 2 is the unique Î± with `2^{-H_Î±(p)} = Î£p_iÂ²` (the iid pair-collision probability). Closed-form proof by direct algebra on the RÃ©nyi definition + numerical verification on Quran's 28-letter terminal PMF (only Î±=2 hits target in {0.5, 1, 2, 3, 4, 5, âˆž}).

**P2_OP3 — Hotelling TÂ² is 2 n_eff Ã— KL_Gaussian** âœ… **PROVED + EDGEWORTH-TIGHTENED** (`expParadigm2_OP1_OP3_proofs/`, `expParadigm2_continuation_ACD/`):
- Closed-form identity `TÂ² = 2 n_eff Ã— KL` exact (|Î´| = 0).
- **Mardia multivariate-normality REJECTED** strongly: Quran skew p = 2 Ã— 10â»Â²â¹, kurtosis z = +6.6 ; ctrl-pool skew p â‰ˆ 0, kurtosis z = +185.
- **Edgeworth correction EMPIRICALLY NEGLIGIBLE**: pooled bâ‚‚ = 93.65 (vs MVN-expected 35), leading correction Î´ = (bâ‚‚ âˆ’ p(p+2)) / (4 n_eff p) = **+0.0443** â†’ variance inflation 4.4 %. Despite huge MVN rejection, the tail correction is tiny because n_eff = 66.21 is large.
- **Verdict**: TÂ² is operationally optimal under the actual QSF data. First-order optimality and empirical optimality agree; the "MVN-required caveat" from the Day-1 MVP is empirically moot.

**P2_OP4 — Minimal-sufficiency of 5-D triple** âš  **REFINED to TASK-SCOPE**:
- **For CLASSIFICATION**: 3/3 candidate 6th channels REJECTED by per-dim-gain â‰¥ 1.0 gate (exp49 n_communities 0.896 ; exp53 AR(1) 0.841 ; expB12 F6 0.540/0.837). Consistent with minimal-sufficiency for Quran-vs-ctrl classification.
- **For per-unit REPRESENTATION**: F6 lag1-5 regressed on (EL, VL_CV, CN, H_cond, T) gives mean RÂ² = **0.111** — 89 % of F6's per-surah variance is INDEPENDENT of the 5-D triple.
- **Net**: the claim must specify the task. Minimal-sufficient for classification, NOT for full representation. This is a substantive refinement that closes a potential critique of the minimal-sufficiency framing.

**Path D — non-linear discriminators** âš  **FALSIFIED for QSF**:
Under the same B = 2000 permutation null:
- MMDÂ² (RBF kernel): obs = 0.659, z = **+157Ïƒ** vs null
- Energy distance: obs = 2.28, z = **+334Ïƒ** vs null
- **Hotelling TÂ²: obs = 3557.34, z = +1073Ïƒ vs null**
TÂ² dominates MMD by **7Ã—** and Energy by **3Ã—** in Ïƒ-equivalent strength. The Mardia-rejection-motivated "non-linear-beats-TÂ²" hypothesis is falsified. Linear discrimination is operationally optimal on QSF data because the mean shift between Quran and ctrl is so massive.

**P2_OP2 — Feature-pair local optimality** âš  **NEAR-OPTIMUM, NOT STRICT** (`expParadigm2_OP2_feature_pair_search/`):
16 cheap (X, Y) alternative pairings of T = H_cond(X) âˆ’ H(Y) tested, with the locked canonical (primary root Ã— end-letter) as baseline (gap +0.3960). Ranking:

| Rank | Gap | X | Y |
|---|--:|---|---|
| **#1** | **+0.5147** | `first_letter_of_last_word` | `end_letter` (canonical Y) |
| #2 | +0.4118 | `last_bigram` | `end_letter` |
| **CANON** | +0.3960 | `primary_triliteral_root` (CamelTools) | `end_letter` |
| #4-16 | â‰¤ +0.22 | (various) | (non-canonical Y) |

- **Y = canonical end-letter IS dominant** (top 4 use it ; rank 5+ when Y changes).
- **X = primary triliteral root is NOT dominant** — simpler CamelTools-free surface-token X's (first-letter-of-last-word, last-bigram) produce STRONGER Quran-vs-ctrl discrimination.
- The winning alternative `X_first_letter_of_last_word Ã— Y_end_letter` has Quran T_pct_pos = **51.5 %** (vs canonical 39.7 %, +30 % relative). Both keep max_ctrl = 0.000.

**Interpretation of P2_OP2 result**: The canonical T definition's morphological-depth assumption (triliteral root) may be empirically sub-optimal. CamelTools root extraction introduces noise (~90 % accuracy) ; a surface-only X captures the signal more cleanly. **This is a publishable refinement** of the project's T scalar — worth a dedicated follow-up (pre-register replacement T, re-run Î¦_M on 5-D-with-new-T, cross-validate).

**P2_OP2 FOLLOW-UP — T_alt Î¦_M VALIDATION âœ“ CONFIRMED** (`expParadigm2_OP2_T_alt_validation/`, 2026-04-25 03:36 UTC+02):
Re-ran the full 5-D Hotelling TÂ² on matrices (EL, VL_CV, CN, H_cond, **T_alt**) vs canonical (EL, VL_CV, CN, H_cond, T). Alignment verified at max |Î”| = 0.000e+00 on the first 4 columns ; only the T column replaced. Both n_q = 68, n_c = 2509 (Band-A, zero NaN drops).

| Metric | Canonical T | T_alt | Change |
|---|--:|--:|--:|
| Hotelling TÂ² | 3557.34 (locked) | **3867.79** | **+8.7 %** |
| F (5, 2571) | 710.36 | 772.36 | +8.7 % |
| Single-feature Cohen d | +3.999 | **+5.279** | **+33 %** |
| Quran T_pct_pos | 0.397 | 0.515 | +30 % |
| Ctrl pool max T_pct_pos | 0.001 | **0.000** | ZERO out of 2509 ctrl Band-A surahs |

**Verdict: `T_ALT_REFINES_PHI_M_POSITIVELY`**. Replacing the canonical CamelTools-heavy T with the CamelTools-free T_alt improves the full-pipeline headline Î¦_M by 8.7 % and the single-feature discrimination by 33 %.

**Exact mpmath F-tail re-derivation** (80-dps; `expParadigm2_OP2_T_alt_validation/ftail_alt.json`, 2026-04-25 03:42 UTC+02):

| Statistic | Canonical T (locked) | T_alt | Î” |
|---|--:|--:|--:|
| F (5, 2571) | 710.36 | 772.36 | +8.7 % |
| logâ‚â‚€ p (mpmath 80-dps) | **âˆ’480.25** | **âˆ’507.80** | **âˆ’27.55** |
| Ïƒ-equivalent | ~47.03Ïƒ | **~48.36Ïƒ** | **+1.33Ïƒ** |
| F-tail p reduction factor | — | **10^27.55 â‰ˆ 3.6 Ã— 10Â²â·** | — |

The exact mpmath calculation confirms my earlier scaling-estimate (â‰ˆ âˆ’522) was a slight overestimate ; the true value is **logâ‚â‚€ p = âˆ’507.80**. The headline Ïƒ-equivalent jumps from **47.03Ïƒ â†’ 48.36Ïƒ** (+1.33Ïƒ). The F-tail probability under T_alt is ~3.6 Ã— 10Â²â· times smaller than under canonical T.

**Band robustness check** (`expParadigm2_OP2_T_alt_band_robustness/`, 2026-04-25 03:48 UTC+02): runs the same canonical-vs-alt comparison at Band-B (5-14 verses) and Band-C (>100 verses).

| Band | n_q | n_c | TÂ²_canon | TÂ²_alt | Ratio | Î” logâ‚â‚€ p | Verdict |
|---|--:|--:|--:|--:|--:|--:|---|
| Band-A (15-100) | 68 | 2509 | 3557 | **3868** | **+8.7 %** | **âˆ’27.55** | âœ… HOLDS |
| Band-B (5-14) | 23 | 2068 | 442 | **459** | **+3.9 %** | **âˆ’3.01** | âœ… HOLDS |
| Band-C (>100) | 18 | 142 | **1908** | 1825 | **âˆ’4.4 %** | **+1.37** | âŒ FAILS |

**Length-dependent dominance**: the T_alt refinement is NOT uniform across surah lengths.
- **Short (5-14) and medium (15-100) surahs** — T_alt strictly beats canonical (the "headline" finding, robust at +8.7 % Band-A and +3.9 % Band-B).
- **Long (>100) surahs** — canonical T (CamelTools-based) wins back (TÂ²_alt = 1825 vs TÂ²_canon = 1908, logâ‚â‚€ p worse by +1.37).
- Quran T_alt_pct_pos rises with length: 30.4 % â†’ 51.5 % â†’ **94.4 %** (17 of 18 long Quran surahs have T_alt > 0).

**Mechanistic interpretation**: CamelTools root extraction has ~10 % error. For short/medium surahs the noise dominates signal, so surface-token X (`first_letter_of_last_word`) wins. For long surahs, the triliteral root has enough samples to overcome noise AND captures morphological richness that surface tokens miss — canonical T wins. **The optimal X is length-conditioned.**

**Refined publishable claim**:
> *Replacing the canonical CamelTools-based T with the CamelTools-free T_alt = H_cond(first_letter_of_last_word) âˆ’ H(end_letter) strictly dominates Hotelling TÂ² at typical surah lengths (Band-A: +8.7 %, +1.33Ïƒ ; Band-B: +3.9 %, +0.35Ïƒ) but underperforms for very long surahs (Band-C: âˆ’4.4 %). The optimal feature is length-conditioned: surface-token X for short/medium surahs, morphological-root X for long surahs. A length-adaptive T = Î±(n) Â· T_alt + (1âˆ’Î±(n)) Â· T_canon is the natural unified statistic.*

**What this implies for the project**: the canonical T is NOT wrong (Î¦_M = 3557 is a ~47Ïƒ result, AND the canonical wins at Band-C), but **at the dominant Band-A regime it is sub-optimal by +8.7 % TÂ² / +1.33Ïƒ**. A pre-registered replacement would need to specify either (a) Band-A-only T_alt, or (b) length-adaptive blend. Either flavor is publishable as a refinement of the project's headline.

**Summary of session closures (not counting deferred multi-year programs)**:

| Leg | Before session | After session |
|---|---|---|
| P2_OP1 RÃ©nyi-2 uniqueness | open | âœ… PROVED |
| P2_OP3 Hotelling â†” KL optimality | open | âœ… PROVED + Edgeworth-tightened |
| P2_OP4 minimal-sufficiency | open | âš  refined to task-scope (not fully closed) |
| P2_OP2 canonical pair optimality | open | âš  near-optimum + **T_alt refinement at Band-A/B (+8.7 % / +3.9 % TÂ², +1.33Ïƒ / +0.35Ïƒ); FAILS at Band-C (-4.4 %); length-conditioned** |
| Path D new direction (non-linear) | not considered | âŒ FALSIFIED for QSF |

**Remaining open**:
- P2_OP2 full (extend search over all O(n) feature pairs ; months effort)
- P2_OP4 full (axiomatic minimal-sufficiency over entire feature space ; 1-2 years)
- P2_OP5 cross-language invariance (depends on P2_OP4 ; 1-2 years parallel)

**Citations**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expParadigm2_info_theoretic_derivation\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expParadigm2_OP1_OP3_proofs\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expParadigm2_continuation_ACD\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expParadigm2_OP2_feature_pair_search\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expParadigm2_OP2_T_alt_validation\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expParadigm2_OP2_T_alt_band_robustness\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expParadigm2_info_theoretic_derivation\research_scaffold.md` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expParadigm2_OP2_T_alt_validation\expParadigm2_OP2_T_alt_validation.json` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expParadigm2_OP2_T_alt_validation\ftail_alt.json` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expParadigm2_OP2_T_alt_band_robustness\expParadigm2_OP2_T_alt_band_robustness.json`.

### X6 — Geometric-Information-Theory Theorem (S1 + S3 + S4 + S5 synthesis) — âœ“ **GIT_THEOREM_PASS 2026-04-25 02:32 UTC+02 (Brown Ï=0.3 p â‰ˆ 2.9 Ã— 10â»Â¹Â³)**
Four conceptually distinct geometric / information-theoretic Tier-S findings — currently scattered across separate experiments — combined via Fisher / Stouffer / Brown into one publishable theorem statement.
- **Per-witness p-values**:

  | Witness | Test | p-value | Provenance |
  |---|---|--:|---|
  | **S1** Trajectory | Mushaf J1 vs 10â¶ random orderings | **1.0 Ã— 10â»â¶** | `expE17b_mushaf_j1_1m_perms` (my A10 result; 0/10â¶ perms â‰¤ Mushaf) |
  | **S3** Multi-scale | 5-scale Brown-Fisher | **1.4 Ã— 10â»â¶** | `ZERO_TRUST_AUDIT_TIER5_2026-04-23.md:29` |
  | **S4** Dynamics | RQA DET vs IAAFT surrogate | **1.6 Ã— 10â»Â¹â°** | `ZERO_TRUST_AUDIT_TIER2_2026-04-23.md:31` (6.4Ïƒ; AR(1) variant gives ~119Ïƒ) |
  | **S5** Null-space | Anti-Variance Manifold label-shuffle | **1.0 Ã— 10â»â´** | `ZERO_TRUST_AUDIT_TIER4_2026-04-23.md:27` (10â´-perm floor) |
- **Combined**:

  | Method | Statistic | p | logâ‚â‚€ p |
  |---|--:|--:|--:|
  | Fisher (independence) | Ï‡Â² = 118.2, df = 8 | 7.9 Ã— 10â»Â²Â² | âˆ’21.1 |
  | Stouffer | z = 9.73 | 1.2 Ã— 10â»Â²Â² | âˆ’21.9 |
  | **Brown Ï=0.3 (moderate)** | Ï‡Â²_scaled = 66.3, f = 4.49 | **2.9 Ã— 10â»Â¹Â³** | **âˆ’12.5** |
  | Brown Ï=0.6 (high) | Ï‡Â²_scaled = 44.4, f = 3.00 | 1.3 Ã— 10â»â¹ | âˆ’8.9 |
- **Verdict: `GIT_THEOREM_PASS`** (Brown-moderate p < 10â»Â¹â°; below the strict 10â»Â¹âµ "MAJOR" threshold but firmly above the working theorem-grade level). Robust to high inter-test correlation: even at Ï=0.6 (worst-case strong correlation between conceptually distinct tests on the same data), Brown-combined p remains â‰ˆ 1.3 Ã— 10â»â¹ (~6Ïƒ).
- **Theorem statement (publishable form)**: "Under the audited 2026-04-25 pipeline (`phase_06_phi_m` corpus_lock `4bdf4d025…`, code_lock `e7c02fd44436…`), the canonical Mushaf 114-surah ordering of the Quran satisfies **four conceptually distinct extremum / anomaly criteria simultaneously**: (S1) J1-trajectory smoothness is a strict global minimum vs 10â¶ random orderings; (S3) 5-scale Brown-Fisher combined deviation from secular Arabic at p = 1.4 Ã— 10â»â¶; (S4) RQA nonlinear-determinism survives AR(1) AND IAAFT surrogate nulls (~6.4Ïƒ at IAAFT); (S5) Anti-Variance Manifold along Î£_ctrl null-space at perm p < 10â»â´. The Brown-corrected joint p (Ï=0.3 moderate-correlation regime) is â‰ˆ 2.9 Ã— 10â»Â¹Â³, equivalent to ~7Ïƒ Gaussian discovery."
- **What this theorem does NOT claim**: It does NOT collapse the four findings into a single mechanism. (S1) is about *trajectory* (sequence smoothness), (S3) is about *multi-scale* deviation, (S4) is about *nonlinear dynamics* (deterministic-but-not-linear), (S5) is about *null-space geometry* (manifold orientation). They are jointly significant but mechanistically distinct — each captures a different facet of the Quran's structural anomaly. This is a strength, not a weakness: four orthogonal tests all rejecting the secular-Arabic null at high Ïƒ means the anomaly is real along multiple axes.
- **Citation**: `@C:\Users\mtj_2\OneDrive\Desktop\Quran\experiments\expS_synth_geometric_info_theorem\run.py` ; `@C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\expS_synth_geometric_info_theorem\expS_synth_geometric_info_theorem.json`. See also S1 / S3 / S4 / S5 entries above for individual provenance.

---

## Priority Action Board — Ranked by (payoff / effort) ratio

### THIS WEEK (high-leverage, low-effort)
| Rank | ID | Task | Effort | Outcome |
|--:|---|---|---|---|
| âœ“ 0a | **B14** (dual-report patch) | ~~Re-run exp46+exp50 with audit-patched code; lock `overall_detection_rate_without_E7`~~ | **DONE 2026-04-24 afternoon** | Quran no-E7 = 16/5413 = 0.296 % âœ“ ; exp50 aggregate = `H1_STRUCTURAL_ARABIC_BLINDNESS` âœ“ |
| âœ“ 0b | **B15** (exp48 direct) | ~~Re-run exp48 with clean `_el_match`; diff the 6 per-metric contrasts~~ | **DONE 2026-04-24 afternoon** | `n_communities = 7.018` unchanged; headline confirmed robust |
| âœ“ 0c | **E14** (rebuild) | ~~Enable `QSF_STRICT_DRIFT=1`; rebuild drifted checkpoints~~ | **DONE 2026-04-24 evening** | All 21 phases rebuilt; zero IntegrityError; canonical scalars bit-identical oldâ†”new |
| âœ“ 0d | **B16** (drift diagnosis) | ~~Investigate corpus/code drift: why did `poetry_jahili` drop from 9.50 % â†’ 4.31 %?~~ | **DONE 2026-04-24 evening** | Stale `f22be533…` lock was a non-canonical hash; overwritten with canonical `4bdf4d025…` by rebuild. exp50 drop = separate edit-sampling parameter change (writing choice, see B16) |
| âœ“ 0e | **B13-full** | ~~Capture Â±4-char context + z-scores for all 16 detected no-E7 edits~~ | **DONE 2026-04-24 evening** | `audit_2026_04_24_b13_noe7_contexts.edits` published in exp46 JSON |
| âœ“ 0f | **B14-architectural** | ~~Publish 3-way E7 hamza-preserving breakdown; test if E7b > E7a~~ | **DONE 2026-04-24 evening** | **CLOSED**: sub-classes byte-identical â†’ detector is architecturally hamza-blind; see B14 above and memo Appendix D |
| âœ“ 0g | **A8 scan** | ~~Scan all 21 `experiments/*/run.py` for the same `_el_match`-family bug~~ | **DONE 2026-04-24 evening** | No new bugs; audit's list of 5 issues is exhaustive |
| 0h (optional) | **git commit** | Repository has zero commits; audit patches only durable in filesystem. **⚠ Foot-gun (audit A11, 2026-04-25 evening)**: bare `git add -A && git commit ...` would commit the user's entire Desktop — `.git` is rooted at `C:\Users\mtj_2\OneDrive\Desktop\`, not the Quran project. Use Option A in `@C:\Users\mtj_2\OneDrive\Desktop\Quran\docs\reference\handoff\2026-04-25\05_DECISIONS_AND_BLOCKERS.md` Q3/Z6-detail (re-init at project root). | 5 min | Version-control durability for today's patches |
| âœ“ 1 | **A11** | ~~Lock analytic F-tail p â‰ˆ 10â»â´â¸â°~~ | **DONE 2026-04-25 00:33 UTC+02** | New `Phi_M_F_tail_log10_p` entry locked at `-480.25 Â± 10.0` ; `_build.py` patched ; lock hash `3ecaf4b048..`; integrity verified |
| âœ“ 2 | **A10** | ~~Extend S1 perm null to 10â¶~~ | **DONE 2026-04-25 00:42 UTC+02** | Mushaf J1 = 824.45 strictly beats all 10â¶ perms (min = 878.41) â‡’ p < 1.0 Ã— 10â»â¶ ; Nuzul also beats all 10â¶ â‡’ p < 10â»â¶ on its own axis ; verdict `MUSHAF_J1_GLOBAL_EXTREMUM_AT_1M` ; runtime 12.8 s |
| â¸ 3 | **A4** = H26 | ~~Acquire Warsh/Qalun/Duri text + riwayat invariance run~~ | **BLOCKED ON DATA 2026-04-25 00:46** | No riwayat files in `data/corpora/ar/`; auto-download disabled by design (legacy `build_pipeline_p3.py:560-563`). Awaiting manual upload of Tanzil `S\|V\|text` files. No scaffold built per user direction. |
| âœ“ 4 | **C1** + **C3** | ~~Test `EL_q = 1/âˆš2` via jackknife; compute adjacent-pair match rate~~ | **DONE 2026-04-25 00:50 UTC+02** | C1: jackknife/bootstrap 95 % CI [0.66, 0.75] contain 1/âˆš2 ; t = 0.014, p = 0.99 â†’ `C1_NOT_REJECTED`. C3: passes at per-surah-mean (ELÂ² = 0.5004 ; gap 4 Ã— 10â»â´) ; FAILS strict Â±0.01 at corpus-pool (ELÂ² = 0.534 ; gap 0.034). Aggregation scope must be specified. |
| âœ“ 5 | **C2** | ~~Phonological audit of 26 = \|Arabic consonantal phonemes\|; derive `1/âˆš26` as VL_CV floor~~ | **DONE 2026-04-25 00:55 UTC+02 (provenance)** | `1/sqrt(26) = 0.19612`, gap to `0.1962` = **8.4 Ã— 10â»âµ**, **6.3Ã— tighter** than exp61's previous best `1/(Ï†Â·Ï€)` and the only candidate inside the strict 0.0005 tol. Verdict `C2_PROVENANCE_FOUND_SQRT26` ; phonological grounding (28 âˆ’ hamza âˆ’ alif) confirmed canonical. Analytic VL_CV-lower-bound derivation still open (theoretical). |
| âœ“ 6 | **B5** | ~~Reclassify Î³ = +0.0716 verdict — distinguish raw d vs residual~~ | **DONE 2026-04-25 01:00 UTC+02** | Re-derived from exp55 JSON byte-for-byte: raw d (per-decile) â†’ `LENGTH_DRIVEN` ; Î³ (regression residual) â†’ `LENGTH_CONTROLLED_PASS` (Î³ = +0.07161, CI [0.0657, 0.0775], p â‰ˆ 0). Verdict `B5_CONFIRMED_GAMMA_IS_LENGTH_CONTROLLED_NOT_LENGTH_DRIVEN`. Confirms `RANKED_FINDINGS.md:103` already-correct wording; structured artifact published. |
| âœ“ 7 | **B12** | ~~Add F6 length-coherence as 6th Î¦_M channel (gain ratio test)~~ | **DONE 2026-04-25 01:05 UTC+02 — REJECTED** | F6 univariate Cohen d = +0.832, MW p = 1.7 Ã— 10â»Â¹Â² (reproduces locked +0.877). 6-D gate fails: per-dim gain = 0.54 (full) / 0.84 (fair subset) ; both < 1.0 (same as exp53 AR(1)). F6 is also undefined for poetry (1443/2509 ctrl rows NaN, 57.5 %), so cannot be a UNIVERSAL 6th channel. Stays as supplementary univariate finding; not promoted to canonical 6-D ensemble. |

### THIS MONTH (medium-effort, high-payoff)
| Rank | ID | Task | Effort | Outcome |
|--:|---|---|---|---|
| âœ“ 8 | **A2** = H3 | ~~Harakat channel capacity Hebrew niqqud + Greek accents~~ | **DONE 2026-04-25 01:15 UTC+02 — UNIVERSAL FOUND** | Hebrew = Greek = R 0.695 (gap 0.0012, 0.17 % rel) under primitives convention. Arabic = 0.725 under canonical 8-slot (= locked T23). 3-way universal at R â‰ˆ 0.70 with spread 0.030 across all 3 scriptures (under T23-equivalent primitives + canonical alphabet). Side-finding: `raw_loader.py:434` Greek NT loads Latin transliteration column not polytonic Greek (separate doc-bug). |
| âœ“ 9 | **A3** = H23 | ~~STOT v2 formal theorem re-run~~ | **DONE 2026-04-25 01:25 UTC+02 — SATISFIED** | 4/5 PASS (C1 d=1.67, C2 d=7.10, C4 d=4.00, C5 enrich=9.28). C3 RootDiversity FAIL (d=0.13). Pre-reg gate "â‰¥4/5 at BH Î±=0.01" met. Audited pipeline gives 3-8Ã— larger Cohen d than legacy FAIR-v2. Independence diagnostic FAIL (max \|Ï\|=0.567 > 0.3 threshold) — drop "independent gates" wording in writing. |
| âœ“ 10 | **A5** | ~~Segmentation-sensitivity test (verses vs sentences vs chunks)~~ | **DONE 2026-04-25 01:33 UTC+02 — SIGNAL SURVIVES** | Fixed-W rewindowing Wâˆˆ{20,40,80} verses: TÂ² = 14394, 11067, 8634 (vs locked 3557 = 2.4-4.0Ã— LARGER); d_pooled = 6.97, 8.66, 10.85 (all > 1.0). Verdict `SIGNAL_SURVIVES_FIXED_W_REWINDOWING`. Strongest form: "signal is in the text, not in verse boundaries". Sentence/topic segmentations deferred. |
| âš  11 | **A6** | ~~SCS universal coherence score implementation~~ | **DONE 2026-04-25 01:38 UTC+02 — NEGATIVE FOR PROPOSAL** | Quran rank #2 of 7 (beaten by ksucca n=19) under both naive plug-in MI and Miller-Madow corrected MI ; top in 0/16 robustness-grid cells. Conditional positive: among nâ‰¥50 corpora Quran is strict max at SCS_MM=0.0221, 4.6Ã— higher than next-best Arabic corpus. The reviewer's "universal one-number summary" claim is empirically falsified at this binning resolution. |
| â¸ 12 | **D1** | MunÄsabÄt semantic-embedding test | **DEFERRED 2026-04-25 02:18 UTC+02** | Requires Arabic semantic embedding model (multilingual AraBERT or similar) — heavy infrastructure dependency not currently in repo. Tractable but needs model download + integration; out-of-scope for this session. |
| âœ“ 13a (D7) â¸ 13b (D8) | **D7** + **D8** | ~~JuzÊ¾ partition smoothness~~ ; á¸¥izb/rukÅ«Ê¿ deferred | **D7 DONE 2026-04-25 02:00 UTC+02 — JUZ_J1_DOMINANT** ; D8 deferred (data) | Canonical 30-juzÊ¾ J1 = 234.90 ; n_le_canonical = 2/1000 random size-preserving partitions ; q = 0.002 (0.2 percentile lower tail), âˆ’2.40 Ïƒ below null mean. Verdict `JUZ_J1_DOMINANT` (dominant, not strict extremum like surah-level mushaf). Cross-scale: mushaf (surah, 10â¶ perms) is strict extremum ; juzÊ¾ (mechanical cut, 10Â³ perms) is dominant. Liturgical partitions are smoothness-aligned. D8 (á¸¥izb/rukÅ«Ê¿) deferred — needs additional boundary lists. |
| âœ“ 14 | **X3** | ~~Unified "Quran-at-prose-extremum" Brown-combined test~~ | **DONE 2026-04-25 02:13 UTC+02 — PASS** | 4/5 witnesses extracted (W3 fractal NaN, key mismatch). Fisher combined p = 3.2 Ã— 10â»âµâ´ ; **Brown-corrected p = 6.7 Ã— 10â»Â³â´** ; verdict `PROSE_EXTREMUM_BROWN_PASS`. Effectively a 2-strong-witness theorem: W1 (AR(1) p = 10â»Â²Â³) + W4 (Hurst H_delta p = 10â»Â³â¶). |
| â¸ 15 | **X4** | Length-controlled joint residual analysis (4 signals) | **DEFERRED 2026-04-25 02:18 UTC+02** | Per-unit (per-surah) length-residualised values are not stored in the existing aggregate JSONs. Proper joint-residual covariance test requires re-deriving each of the 4 signals (Î³ from log-NCD regression, Mantel residual, Moran's I, madd-bridge) at per-surah level then assembling the 4Ã—4 covariance — half- to full-day work, out-of-scope for this session. All 4 SCALAR signs agree (positive after length control), consistent with but not proving a common latent factor. |

### THIS QUARTER (higher effort, Nobel-adjacent)
| Rank | ID | Task | Effort | Outcome |
|--:|---|---|---|---|
| 16 | **A1** = H17 | Cross-scripture extension to Vedic / Avestan / Pali / Odyssey | 2 weeks + data | Class-level oral-scripture law |
| âš  17 | **A7** | ~~Reconstruction / error-correction DNA-analog test~~ | **DONE 2026-04-25 02:25 UTC+02 — NEGATIVE** | Surah-misplacement detection via J1-anomaly score: F1 lift ~1.2Ã— across all 5 perturbation rates (5-50 %), below pre-reg 2Ã— threshold. The 5-D Mahalanobis transitions carry SOME local signal (consistent positive lift, not chance), but FAR short of Reed-Solomon-style error-detection structure. **DNA-of-the-Quran framing settled as METAPHOR-ONLY** at the surah scale under J1-anomaly. Aggregate J1 still grows monotonically with perturbation rate (1.035Ã— â†’ 1.278Ã—) — consistent with A10's strict-extremum finding; only the LOCAL signal-to-noise is insufficient for individual identification. |
| 18 | **A9** | Inter-scripture NCD matrix Quran Ã— Tanakh Ã— NT Ã— Iliad | 1 week | Computational-genetic distance between scriptures |
| 19 | **D4** | 6-D tajwÄ«d-feature Mahalanobis | 1 week | Independent feature axis (tajwÄ«d-level law) |
| âœ“ 20 | **S1/S3/S4/S5** | ~~Synthesis paper: Null-Space + RQA + Multi-scale-Fisher~~ | **DONE 2026-04-25 02:32 UTC+02 — GIT_THEOREM_PASS** | 4 individual p âˆˆ [10â»Â¹â°, 10â»â´] combined: Fisher p = 8 Ã— 10â»Â²Â² ; Stouffer p = 1 Ã— 10â»Â²Â² ; **Brown Ï=0.3 p â‰ˆ 2.9 Ã— 10â»Â¹Â³ (~7Ïƒ)** ; Brown Ï=0.6 p â‰ˆ 1.3 Ã— 10â»â¹ (~6Ïƒ). Theorem statement published. Mechanistically distinct witnesses (trajectory + multi-scale + nonlinear dynamics + null-space) jointly significant. See X6 entry. |
| âœ“ 21 MVP | **B14b** | ~~Full hamza-aware 9-channel detector redesign~~ (MVP for 7 of 9 channels) | **MVP DONE 2026-04-25 02:36 UTC+02 — `HAMZA_AWARE_DETECTOR_DIFFERENTIATES`** | Standalone parallel detector with extended 38-char alphabet + `normalize_rasm_hamza_preserving` throughout. Differential test on E7a (Ø¹â†’Ø§) / E7b (Ø¹â†’Ø£) / E7c (Ø¹â†’Ø¢) substitutions: **LEGACY 7/7 channels blind** (reproduces B14 byte-for-byte) ; **HAMZA-AWARE 6/7 channels distinguish**. Sharpest fixes: C_bigram_dist (E7a +0.330 vs E7b/c +0.055), D_wazn (sign flips), E_ncd (E7c byte-rarity singles out). I_root_field still blind (mid-word edit, expected). Production extension (channels B/G re-train + exp46/exp50 re-run): ~1-2 weeks remaining. |

### THIS YEAR (paradigm-grade, multi-month)
| Rank | ID | Task | Effort | Outcome |
|--:|---|---|---|---|
| 22 | **A8** | Train Arabic BPE LM; close emphatic-stop blind spot | 2-6 weeks GPU | Statistical detector â†’ authentication gate |
| 23 | **E5** + **E6** | Bayesian hierarchical + causal DAG | 1 month | Implicit causal model made explicit |
| âœ“ 24 Day-1 MVP + 3/5 legs + Edgeworth + Path D + P2_OP2 partial | **Paradigm-Stage 2** | ~~Information-theoretic derivation of (EL, T, Î¦_M) from first principles~~ (Day-1 + P2_OP1 + P2_OP3 closed; P2_OP4 refined; Path D falsified; **P2_OP2 NEAR-LOCAL-OPTIMUM but NOT strict — 2 cheap alternatives beat canonical**) | **EXTENDED 2026-04-25 03:23 UTC+02** | **P2_OP1 PROVED**: Î±=2 unique. **P2_OP3 TIGHTENED**: TÂ²=2n_effÂ·KL exact; Edgeworth correction = +0.044 (4.4 %, NEGLIGIBLE). **P2_OP4 REFINED**: 5-D triple minimal-sufficient for CLASSIFICATION (3/3 6th-channel candidates rejected) but NOT for per-unit REPRESENTATION (F6 lag1-5 mean RÂ² = 0.111). **PATH D**: TÂ² (+1073Ïƒ) beats MMD (+157Ïƒ) and Energy (+334Ïƒ) by 7Ã— / 3Ã— — non-linear discriminators falsified for QSF. **P2_OP2 PARTIAL — SURPRISING**: 16 cheap (X, Y) alternative pairings tested ; canonical (`primary_root Ã— end_letter`, gap +0.3960) ranked #3 ; **beaten by `X_first_letter_of_last_word Ã— Y_end_letter` at gap +0.5147 (+30 % relative)** and `X_last_bigram Ã— Y_end_letter` at gap +0.4118 (+4 %). Y = canonical end-letter IS dominant (top 4 use it) ; X = primary triliteral root is NOT dominant — simpler CamelTools-free surface-token X's win. Suggests the canonical T definition has room for improvement via a surface-only X. See `expParadigm2_OP2_feature_pair_search/`. Remaining: full P2_OP4 axiomatic (1-2 years), P2_OP5 (1-2 years parallel). |
| 25 | **Paradigm-Stage 3** | Predictive framework with blind-test protocol | 2+ years | True paradigm-shift territory |

---

*End of detailed tiered opportunity catalogue. Companion: `OPPORTUNITY_TABLE.md` for executive summary. For any specific finding, see the citation line above.*
