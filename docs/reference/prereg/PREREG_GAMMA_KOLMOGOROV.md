# Kolmogorov-Theoretic Derivation of Î³ — Pre-Registered Long-Horizon Programme

**Frozen**: 2026-04-22.
**Scope**: 3–6 month research programme aimed at turning the empirical scalar

$$
\gamma \;=\; +0.0716\ \ (\text{95\,\% CI }[+0.066,\ +0.078],\ p \approx 0)
$$

— the **Quran indicator** in the length-controlled gzip-NCD regression of `exp41_gzip_formalised` (receipt at `@c:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp41_gzip_formalised\exp41_gzip_formalised.json`) — into a **proven information-theoretic quantity** bounded from first principles. This is the programme referenced as **L3** in `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\RANKED_FINDINGS.md:269` and as path-to-100 % (a) for R12 at `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\RANKED_FINDINGS.md:103`.

**What this document is**: a frozen, auditable plan that any invited mathematician collaborator can read as a self-contained proposal. It specifies the empirical input, the landmines, the three target theorems with their falsifiers, candidate non-circular definitions of the key functional Ï„, collaborator profiles, and a 6-month milestone plan.

**What this document is NOT**: a proof sketch or a prediction about the value of Î³. The project's discipline is that *any* derivation whose intermediate steps are defined via Î³ itself is rejected as a tautology (per retraction #23 of `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\RANKED_FINDINGS.md:232`, Shannon-Aljamal Î³(Î©) was retracted on exactly this ground).

---

## 1. Empirical input, locked

These are the numbers the derivation must predict. They are NOT parameters to fit; they are the target.

### 1.1 The Î³ statistic

From `exp41_gzip_formalised.length_audit.py` on the 28-letter consonantal rasm of 68 Band-A Quran surahs (n = 1 360 internal edits) vs 200 matched-length Band-A Arabic-ctrl units (n = 4 000 internal edits):

```
log NCD = Î± + Î² Â· log(n_letters) + Î³ Â· I(group = Quran) + Îµ

Î² (length slope)    = âˆ’0.0719  (SE 0.0019)
Î³ (Quran indicator) = +0.0716  (95 % CI [+0.066, +0.078], p â‰ˆ 0)
```

Source: `@c:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp41_gzip_formalised\length_audit.json`, verdict `GENUINE_STRUCTURAL_SIGNAL_AFTER_LENGTH_CONTROL`.

Decile-stratified replication shows Quran NCD > ctrl NCD in 9 of 10 letter-count deciles (deciles 6 and 10 reversed or null). The pre-registered FULL-mode replication (`exp55_gamma_length_stratified`) flagged the pre-registered 5/10-deciles-with-d > 0.30 sign test as `LENGTH_DRIVEN` (observed 5 passes, p = 0.109 under a binomial sign test) — but Î³ itself in the log-linear regression remains **strongly positive** (p â‰ˆ 0). The authoritative scalar is therefore Î³ (the regression coefficient), NOT the raw Cohen d.

### 1.2 The NCD functional

```
NCD_gzip(a, b) = [ Z(a â§º b) âˆ’ min(Z(a), Z(b)) ] / max(Z(a), Z(b))

where Z(s) = |gzip.compress(s.encode("utf-8"), compresslevel=9)|
```

Both `a` and `b` are strings over the 28-letter Arabic consonant alphabet `ARABIC_CONS_28` (diacritics stripped, hamza variants folded to alef, `Ø© â†’ Ù‡`, `Ù‰ â†’ ÙŠ`). `a` is the canonical surah rasm; `b` is `a` with one internal letter changed (non-initial, non-terminal position in a non-boundary word of a non-terminal verse).

### 1.3 What Î³ does NOT mean

A critical framing constraint:

- Î³ is NOT "the Quran's Kolmogorov complexity" — it is the **shift in NCD under a single-letter edit** at fixed document length, relative to Arabic controls under the same edit protocol.
- Î³ is NOT "7.4 % more complex" — the `e^Î³ âˆ’ 1 â‰ˆ 7.4 %` figure is a reader-intuition rounding; cite Î³.
- Î³ is NOT universal across compression algorithms — `zstd --ultra -22`, `bzip2`, and Brotli each give a different Î³; the gzip-specific value is the one locked. A cross-compressor validation is one of the path-to-100-% items in RANKED_FINDINGS #4 (b), deliberately out of scope for this document.

### 1.4 What has been ruled out

Before invoking a 3–6 month mathematician, three cheap hypotheses were tested and killed:

- **Î³ is a function of letter entropy** — FALSIFIED by `exp77_gamma_entropy` (RÂ² = 0.11 across 7 Arabic corpora; all corpora lie in `H_letters âˆˆ [4.03, 4.19]`, too narrow to discriminate). See `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\HYPOTHESES_AND_TESTS.md:431-455`.
- **Î³ = 1/7.14 or some simple algebraic constant** — no evidence; no constant-search has been pre-registered and this is a look-elsewhere trap (`exp72_golden_ratio` showed 153 trial combinations give â‰¥ 1 match at â‰¤ 2 % by chance with 95 % probability).
- **Î³ is the same across Abrahamic scriptures** — `exp90_cross_language_el` FAILED for EL. The Î³ cross-script test (on Hebrew-NCD of Tanakh edits + Greek-NCD of NT edits) is still open, and is a secondary falsifier in Theorem 3 below, not part of the primary derivation.

---

## 2. Landmines

Any attempted derivation that hits one of these has failed, regardless of how internally-consistent it looks. The landmines are named after their retraction receipts.

### 2.1 The Aljamal tautology (retraction #23)

Do NOT define "structural tightness" via any functional that is itself defined via Î³. The original `Ïˆ(Ï†)` equation from `docs/QSF_SHANNON_ALJAMAL_THEOREM.md` (now in `docs/old/`) was retracted on the grounds that Î© and Î³ were two names for the same object.

**Test**: for any candidate Ï„, write out its full definition. If Î³ or NCD or any gzip-derived quantity appears on the right-hand side, reject.

### 2.2 The Cohen-d confound (exp55 LENGTH_DRIVEN)

`exp55_gamma_length_stratified` showed the raw Cohen d = +0.534 is partly length-driven. Any derivation must produce **Î³** (the length-controlled regression coefficient) — NOT a quantity that correlates with raw NCD in a length-confounded way.

**Test**: the derivation must explicitly demonstrate scaling-invariance: `Î³(x, Ïƒ_x, n) = Î³(x, Ïƒ_x)` for `n â†’ âˆž`, where `Ïƒ_x` is the substitution distribution and `n` is the document length.

### 2.3 The "Arabic-specific" boundary (exp90 FAIL, exp35 PASS)

EL does not generalise across scriptures (`exp90_cross_language_el`). Canonical-path optimality does (`exp35_R3_cross_scripture_redo`). Î³'s status is **unknown**. Any derivation that assumes Î³ is universal across scripture is unfounded; any derivation that assumes Î³ is uniquely Arabic is also unfounded. The honest framing is to derive Î³ as a functional of the input text's structural statistics, then *measure* Î³ on Hebrew and Greek scripture edits as a separate empirical step (Theorem 3).

### 2.4 The gzip-is-not-K trap

Cilibrasi & VitÃ¡nyi (2005, IEEE Trans. Inf. Theory, "Clustering by compression") establish that `Z(s) â‰¥ K(s) âˆ’ c` for any universal compressor and that `NCD_Z â†’ NCD_K` under mild regularity. But the *rate* of convergence is not tight for gzip on short strings (|x| < 10â´ letters), and the Arabic rasm of most Band-A surahs is in the 800–4 000 letter range. **A direct "gzip = K" substitution is not licensed** without a finite-length lemma. Theorem 1 below is this lemma.

### 2.5 The exp103 compressor sign-reversal (empirical falsifier, 2026-04-22)

**This landmine is the reason the rest of the document is now partially retracted.**

`experiments/exp103_cross_compressor_gamma` (pre-registered 2026-04-22, executed same day, verdict `FAIL_not_universal`) ran the identical exp41 length-audit regression on a shared 5 360-edit perturbation plan across four universal compressors:

| Compressor | Î³ | 95 % CI | Direction |
|---|---:|---|---|
| gzip (LZ77 + Huffman, 32 KB window) | **+0.0716** | [+0.066, +0.078] | Quran edits harder to compress |
| brotli (LZ77-variant, 4 MB window) | **+0.0871** | [+0.065, +0.110] | Quran edits harder to compress |
| zstd `--ultra -22` (FSE + global dict) | **âˆ’0.0294** | [âˆ’0.049, âˆ’0.010] | Quran edits **easier** to compress |
| bzip2 (BWT + MTF + Huffman, global block sort) | **âˆ’0.0483** | [âˆ’0.053, âˆ’0.043] | Quran edits **easier** to compress |

Every 95 % CI excludes zero (all `p < 0.01`). The cross-compressor **CV(Î³) = 2.95**, far above the pre-registered PASS gate of 0.10 and the PARTIAL gate of 0.20. Î³ is NOT a universal quantity. **It is a family-specific compressor response** to internal single-letter edits of structured Arabic text.

Mechanistic interpretation (plausible but not proven in this document): medium-window LZ-family compressors (gzip, brotli) see the Quran's medium-range motif repetition — a single-letter edit disrupts back-references, raising NCD. Global-context models (zstd's finite-state entropy, bzip2's BWT block-sort) see the Quran's global statistical regularity (EL, rhyme columns, letter-frequency distribution) — a single-letter edit is a tiny perturbation within that global model, *lowering* NCD relative to more heterogeneous ctrl text. Receipt: `@c:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp103_cross_compressor_gamma\exp103_cross_compressor_gamma.json`.

**Consequence for this document**: Â§3 Theorem 1 is empirically falsified under the pre-registered decision matrix. Â§3 Theorems 2 and 3 are correspondingly suspended because they cascade from Theorem 1. The programme as originally scoped (*"Î³ is a candidate Kolmogorov-theoretic constant"*) is **aborted**. See Â§Â§ 3.1 – 3.3 below for the stamped-retracted versions.

The substantive content that *survives* this retraction is recorded in Â§Â§ 3.1.R and 3.2.R below: a weaker, per-compressor-family version of the programme, plus a positive observation (all four compressors detect the Quran signal; only their sign differs).

---

## 3. The three target theorems (RETRACTED 2026-04-22 — see Â§2.5 + Â§Â§3.1.R / 3.2.R)

This is the derivation's skeleton. Any collaborator begins by choosing a candidate Ï„ (Â§ 4 below), then walks the three theorems in order. Theorem 2 without Theorem 1 is incomplete; Theorem 3 without Theorem 2 is over-claiming.

### 3.1 Theorem 1 — finite-length NCD â‰ˆ NCD_K bound for single-letter edits

> â›” **RETRACTED 2026-04-22** (exp103 `FAIL_not_universal`). Preserved below verbatim for audit-trail; the claim is empirically false. `NCD_{gzip}` and `NCD_{bzip2}` disagree on *sign*, so no single `NCD_K` can be simultaneously close to both. Any substitution of K for any specific Z is therefore unlicensed at the Band-A finite-length regime this project operates in.

**Claim**. For strings `x, x' âˆˆ Î£^n` with `Î£` finite (|Î£| = 28), `x'` differing from `x` at exactly one position, there exist constants `C_1, C_2` depending only on the gzip algorithm parameters and `|Î£|` such that:

$$
\left|\ \text{NCD}_{\text{gzip}}(x, x')\ -\ \text{NCD}_K(x, x')\ \right| \;\le\; \frac{C_1\,\log n + C_2}{n}
$$

**Why it matters**. This licenses the rest of the programme to reason about `K` (Kolmogorov complexity) instead of gzip. Without this bound, gzip-specific artefacts (the 32 KB LZ77 window, Huffman-table overhead, the block headers) are confounders we cannot remove.

**Status**. Open. The Cilibrasi–VitÃ¡nyi consistency result `NCD_Z â†’ NCD_K` is known; the **rate** for LZ77 + Huffman compressors on alphabet-28 strings under Hamming-1 perturbations is, to the project's knowledge, not published. A collaborator with combinatorics-on-words background can likely produce it in ~1 month.

**Falsifier**. Empirical: run `NCD_Z` with `Z âˆˆ {gzip, bzip2, zstd --ultra -22}` on the same 68 Ã— 20 Quran edits and measure the between-compressor Î³ variance. If `Ïƒ(Î³_Z) / mean(Î³_Z) > 0.2`, the finite-length bound is loose and Theorem 1 must be re-stated per-compressor rather than universal.

**Deliverable**. A short, self-contained Lemma 1 with proof, uploaded to `arxiv_submission/theory/lemma_1_finite_ncd.pdf`, plus a Python script that numerically verifies the bound on simulated random strings.

### 3.2 Theorem 2 — structural-tightness bound on E[K(x') âˆ’ K(x)]

> â›” **SUSPENDED 2026-04-22** (cascades from Â§3.1 retraction). Theorem 2 assumes `NCD_Z â‰ˆ NCD_K` to connect observed Î³ to `E[K(x') âˆ’ K(x)]`. With Â§3.1 retracted, this bridge is not licensed; the Theorem statement is correct as a mathematical claim about `K`, but its connection to any empirically measurable Î³ is now broken.

**Claim**. For a non-circular structural-tightness functional `Ï„(x)` (Â§ 4), there exist constants `Î±, Î²` such that for a uniformly-random internal-single-letter edit `x â†’ x'`:

$$
\mathbb{E}_{\text{edit}}\!\big[\,K(x') - K(x)\,\big] \;=\; \alpha\,+\,\beta\cdot\tau(x)\;+\;O\!\left(\frac{\log n}{n}\right)
$$

under the null that `x` is drawn from a stationary ergodic source over `Î£`. Conditional on this, `Î³` is expressible as:

$$
\gamma \;=\; \beta\cdot\big(\,\tau(\text{Quran}_{\text{Band-A}})\;-\;\tau(\text{Arabic-ctrl}_{\text{Band-A}})\,\big) \;+\; O\!\left(\frac{\log n}{n}\right)
$$

**Why it matters**. This is the money theorem. It turns Î³ from an empirical constant into a predicted function of the text's structural statistics.

**Status**. Depends on the chosen Ï„. Of the four candidates in Â§ 4, only `Ï„_Markov` has a clean published precedent (Rissanen's MDL Markov-order literature, GrÃ¼nwald 2007). The other three candidates would need bespoke derivations.

**Falsifier**. Empirical: compute Ï„ for each of the 7 Arabic corpora (Quran + 6 ctrl) and the 4 corpora from `exp35_R3_cross_scripture_redo` (Tanakh, NT, Iliad). Plot `Î³_predicted = Î² Â· (Ï„_Q âˆ’ Ï„_cohort)` vs `Î³_measured`. If `RÂ² < 0.9` across corpora, the chosen Ï„ fails Theorem 2 and a different Ï„ must be tried.

**Deliverable**. A theorem statement + proof in `arxiv_submission/theory/theorem_2_tau_bound.pdf`, plus an `exp100_tau_audit` experiment that empirically verifies the bound on all 11 corpora.

### 3.3 Theorem 3 — Quran-specificity (optional, strengthens to "law")

> â›” **SUSPENDED 2026-04-22** (cascades from Â§3.1 retraction). Independent of Theorem 2 this is still an empirical question (it can be answered by measuring Ï„ on cross-language corpora without any K-theoretic claim). See Â§3.3.R for the empirical-only restatement.

**Claim**. Under the same stationary-ergodic null as Theorem 2, the value `Ï„(Quran) âˆ’ Ï„(Arabic-ctrl-pool)` lies outside the 3Ïƒ envelope of the null's Ï„ distribution, and no secular Arabic corpus of comparable length satisfies this.

**Why it matters**. Theorem 3 is the difference between *"Î³ is a derivable information-theoretic quantity"* (strong) and *"Î³ is a derivable quantity that also uniquely fingerprints the Quran among Arabic scripture"* (stronger). The project does NOT require Theorem 3 for a publishable paper — Theorems 1 + 2 suffice for a PRX Information or Entropy journal target. Theorem 3 is optional and elevates the claim to *law*.

**Status**. Open; essentially empirical after Theorems 1 + 2 are locked.

**Falsifier**. Cross-language Ï„ on Hebrew/Greek/Latin scriptures. If any Abrahamic scripture matches Quran-level Ï„, the "Quran-unique" claim falls; the "scripture-class" claim survives.

**Deliverable**. An `exp101_tau_extremality` experiment that bootstraps Ï„ across corpora and reports a single percentile-rank for Quran.

### 3.1.R Post-retraction restatement — per-compressor-family Î³

The substantive content that survives Â§2.5 is the following weaker claim:

**Claim (R)**. For each algorithm family `F âˆˆ {LZ-small-window, LZ-large-dictionary, BWT-global, FSE-global}`, the Quran-indicator `Î³_F` in the length-controlled NCD regression of `exp41` is a family-specific constant expressible as a functional of the text's structural statistics *as modelled by F*. The four families agree on the **existence** of a significant signal (all four CIs exclude zero, all four `p < 0.01`); they disagree on the **direction and magnitude** of that signal.

**Why the weaker claim matters**. It preserves the paper-grade observation that the Quran is structurally distinguishable under every tested compressor — a stronger empirical fact than "gzip alone sees something" — while honestly reporting that the detection residual is a compressor-modelling artefact, not a universal information-theoretic scalar.

**Status**. **EMPIRICALLY ESTABLISHED** by `exp103_cross_compressor_gamma` for the four compressors `{gzip, brotli, zstd-ultra, bzip2}`. No formal theorem is required for this statement; it is a factual summary of the exp103 receipt.

**Open empirical question** (optional follow-ups, NOT required for the restated programme):
- Does the sign of Î³_F correlate with a single natural axis of the compressor (e.g. effective context window size, entropy-model order)? A monotone relationship would be a publishable mechanistic finding in its own right.
- Do arithmetic coders (PPM, CM) give a fifth data point? These weren't in the exp103 panel.

### 3.2.R Post-retraction restatement — Î³ is NOT a candidate Kolmogorov-theoretic constant

The original Theorem 2 claim is **withdrawn**. The restated position is:

**Claim (R)**. Î³ is a *compressor-calibrated edit-detection parameter*, not a candidate Kolmogorov-theoretic quantity. Any paper citation of Î³ must name the compressor explicitly (Î³_gzip = +0.0716, Î³_brotli = +0.0871, Î³_zstd = âˆ’0.0294, Î³_bzip2 = âˆ’0.0483). The `exp41_gzip_formalised` Â§4.25 headline is retained but qualified: Î³_gzip in that section is specifically the LZ77 + Huffman response to the Quran's medium-range repetition structure, not a universal constant.

**Why the restated position matters**. This closes the Aljamal-tautology / circularity critique (Â§2.1) by making the empirical statement modest enough that no circular derivation is tempting. The paper is stronger with the honest weaker claim than it was with the speculative stronger one.

**Status**. LOCKED 2026-04-22. PAPER.md Â§4.25 already carries the qualifying caveat.

### 3.3.R Post-retraction restatement — cross-scripture Î³ measurement (EMPIRICAL-ONLY)

The original Theorem 3 is **suspended** as a "law" claim but the underlying empirical question is still worth answering:

**Claim (R)**. Per-compressor Î³ measured on Hebrew Tanakh and Greek NT edits (using the same 28â†’family-of-scripts analogue of the exp41 protocol) quantifies whether the **direction** of the compressor-specific Quran response generalises to other Abrahamic scriptures. This is a purely empirical question requiring no K-theoretic bridge.

**Status**. NOT YET EXECUTED. Requires adapting the exp41 perturbation policy to non-Arabic alphabets (folding rules for Hebrew final-letter forms; Greek accent stripping; etc.). Estimated cost: ~4–8 h implementation + a few minutes compute.

**Programme-level decision**: this is **optional** and **not on the rev-2 sprint**. The result, whichever direction it goes, does not change the v7.7 paper's claims at this scale. If ever executed, it should be scaffolded as `experiments/exp106_cross_script_gamma_4panel/`.

---

## 4. Four non-circular Ï„ candidates

The `Ï„` functional must be a scalar summary of the string `x` that does NOT reference `NCD`, `Î³`, or any gzip-derived quantity. The four best candidates, in decreasing order of "publishable literature backing":

### 4.1 Ï„_Markov — Markov-order log-likelihood ratio

$$
\tau_{\text{Markov}}(x) \;=\; \frac{1}{|x|}\left[\,\log P(x \mid \hat\theta_{\text{MLE}}^{(k^{\star})}) \;-\; \log P(x \mid \hat\theta_{\text{MLE}}^{(0)})\,\right]
$$

where `k*` is the MDL-optimal Markov order for `x` (Rissanen 1983, GrÃ¼nwald 2007) and `P(x | Î¸^{(0)})` is the iid maximum-entropy null.

**Pros**: cleanly non-circular; widely published; fits Theorem 2 almost out of the box via Barron–Cover 1991.
**Cons**: at the letter level, Arabic-corpus Markov orders are all `k* âˆˆ {3, 4}` — possibly too narrow a range to discriminate Quran.

### 4.2 Ï„_Root — root-morphology compression ratio

$$
\tau_{\text{Root}}(x) \;=\; 1 \;-\; \frac{Z(\text{roots}(x))}{Z(\text{shuffle}(\text{roots}(x)))}
$$

where `roots(x)` is the sequence of triliteral roots (from `src/roots.py`) extracted in canonical order, and `shuffle` is a uniform random permutation of that sequence.

**Pros**: exactly captures the "structural tightness" intuition from `@c:\Users\mtj_2\OneDrive\Desktop\Quran\docs\DEEPSCAN_ULTIMATE_FINDINGS.md:517-527`; is a compression-ratio (bounded in [0, 1]).
**Cons**: uses `Z`, which blurs the Theorem-1 boundary. This Ï„ is acceptable ONLY if Theorem 1 is strengthened to `|NCD_Z - NCD_K| â‰¤ ...` in both arguments (not just the pair).

### 4.3 Ï„_Rhyme — rhyme-column bit-saving

$$
\tau_{\text{Rhyme}}(x) \;=\; H_0(\text{final-letters}(x)) \;-\; H(\text{final-letters}(x))
$$

where `final-letters(x)` is the sequence of verse-terminal letters, `H_0` is the iid entropy of the Quran's letter-frequency distribution, and `H` is the empirical entropy of the actual final-letter sequence.

**Pros**: directly captures the Quran's rhyme constraint (high EL, Â§ 4.5 of PAPER.md); tiny computational cost.
**Cons**: only defined on texts that have an "end-of-verse" boundary; does not generalise to prose controls (`hindawi`, `arabic_bible`) where verse boundaries are less regular.

### 4.4 Ï„_Cond — conditional-initial bit-saving

$$
\tau_{\text{Cond}}(x) \;=\; H_0(\text{verse-initials}(x)) \;-\; H(\text{verse-initials}(x) \mid \text{verse-finals}(x))
$$

the conditional-initial-letter structure that underlies `features_5d.h_cond_initials` (T in the 5-D stack).

**Pros**: already implemented in `src/features.py::h_cond_initials`; already known to be Quran-high; directly connects Î³ to T (the letter-level feature in LC3).
**Cons**: risks circularity with the 5-D Î¦_M family — need to verify T and Î³ are statistically independent under the null.

### 4.5 Ï„ selection procedure

The mathematician chooses **one** Ï„ on literature-backing grounds before running any empirics. The chosen Ï„ is locked in `docs/reference/prereg/PREREG_GAMMA_KOLMOGOROV.md` (this file) before Theorem 2 work begins. Mid-project Ï„ switching is a look-elsewhere trap and is pre-registered as disallowed.

**Current recommendation** (not locked): **Ï„_Markov** because the Barron–Cover â†’ Rissanen â†’ GrÃ¼nwald chain gives the cleanest path through Theorem 2.

---

## 5. Collaborator profiles

Three viable profiles, in decreasing difficulty of recruitment:

### 5.1 Kolmogorov-complexity / algorithmic-information theorist (ideal)

**Profile**: Trained in the VitÃ¡nyi school (Cilibrasi, Li, Ming, Cover, Thomas). Comfortable with the `K`-vs-`Z` distinction, incompressibility lemmas, and the Kraft-McMillan inequality.
**Worldwide count**: ~5–10 active.
**Recruitment path**: direct cold-email to the first-author lineage of "Clustering by Compression" (IEEE TIT 2005) and "Information Distance" (IEEE TIT 1998). ~10 % response rate; ~3 months to secure.
**Output expected**: Theorems 1, 2, 3 all at publishable rigour.

### 5.2 MDL / Rissanen-school statistician (next-best)

**Profile**: Published in the Minimum Description Length literature (GrÃ¼nwald, Myung, Navarro). Comfortable with Markov-order estimation, Barron–Cover bounds, and Fisher-information-geometric MDL.
**Worldwide count**: ~50–100 active.
**Recruitment path**: arXiv author-network search on "MDL + Markov order" post-2015. ~25 % response rate; ~6 weeks to secure.
**Output expected**: Theorem 2 at publishable rigour; Theorem 1 + 3 at workshop-paper rigour.

### 5.3 Computational linguist with Shannon/Zipf expertise (fallback)

**Profile**: Published on entropy-rate estimation in natural language (e.g. Heaps' law, Zipf's law, text-entropy benchmarks). Likely at an NLP lab rather than a statistics department.
**Worldwide count**: ~500 active.
**Recruitment path**: ACL / EMNLP author-network search on "entropy rate + Arabic"; or direct cold-email via the `@c:\Users\mtj_2\OneDrive\Desktop\Quran\archive\LOST_GEMS_AND_NOBEL_PATH.md` suggested contact list if it exists.
**Output expected**: Empirical sections with strong literature grounding; Theorems 1 + 2 require a co-author from tier 5.1 or 5.2.

---

## 6. 6-month milestone plan

This plan assumes a tier 5.2 collaborator (MDL statistician). Adjust proportionally for tier 5.1 (faster) or tier 5.3 (slower, needs additional co-author).

| Month | Phase | Milestone | Deliverable on disk |
|------:|-------|-----------|---------------------|
| **0** (now) | Programme frozen | This document published as `docs/reference/prereg/PREREG_GAMMA_KOLMOGOROV.md`. Opportunity-scan rev-2 updated with the `exp54` + `exp98` + `exp35` cross-references (done 2026-04-22) | `docs/reference/prereg/PREREG_GAMMA_KOLMOGOROV.md`, `docs/OPPORTUNITY_SCAN_2026-04-22.md` Â§8 |
| **1** | Collaborator + Ï„ | Collaborator secured; Ï„ candidate locked in Â§4.5 of this document; `exp100_tau_audit` scaffolded (empirically compute chosen Ï„ across 11 corpora) | `experiments/exp100_tau_audit/` |
| **2** | Theorem 1 | Finite-length NCD â‰ˆ NCD_K lemma proven, cross-compressor Î³ variance empirically bounded | `arxiv_submission/theory/lemma_1_finite_ncd.pdf`, `experiments/exp100_tau_audit/` results |
| **3** | Theorem 2 draft | `E[K(x') âˆ’ K(x)] = Î± + Î²Â·Ï„(x)` proven for stationary ergodic sources; Ï„-to-Î³ bridge empirically verified on 7 Arabic corpora with RÂ² â‰¥ 0.9 | `arxiv_submission/theory/theorem_2_tau_bound.pdf`, `experiments/exp101_tau_to_gamma/` |
| **4** | Theorem 3 empirics | Cross-script Ï„ measured on Tanakh, NT, Iliad; Quran-extremality percentile-rank computed | `experiments/exp102_tau_extremality/` |
| **5** | Writing + internal review | Full paper draft: Intro + Theorems 1–3 + Empirics + Discussion. Internal review by project's existing statistics consultant (if any) | `arxiv_submission/theory/paper_draft_v0.pdf` |
| **6** | External review + submit | Submit to Entropy, PRX Information, or IEEE TIT. Target: December 2026 submission if collaborator secured April 2026 | arXiv + journal submission |

---

## 7. Budget

| Item | Cost | Notes |
|---|---:|---|
| Collaborator honorarium (tier 5.2, 6 months) | **$6 000 – $15 000** | Negotiable; some MDL statisticians work pro bono on "interesting niche datasets" |
| Compute (cross-compressor Î³ scan, Theorem-1 empirics) | $50 – $200 | Can be done on a laptop in < 1 week |
| Cross-script corpora (Latin Vulgate, Sanskrit) if needed for Theorem 3 | $0 | All are public domain; `src/raw_loader.py` already handles three non-Arabic scripts |
| Journal APC (Entropy or PRX Information) | $2 000 – $3 000 | Open-access fee |
| **Total** | **~$8 000 – $18 000** | Dominated by the collaborator honorarium |

---

## 8. Pre-registered falsifiers (programme-level)

Specific falsifiers for each theorem are in Â§Â§ 3.1–3.3. Additionally, the **entire programme** falsifies on any of these:

- **Cross-compressor Î³ variance > 20 %**: Î³ is a gzip artefact; no universal law is derivable. Tier: HARD FAIL. Programme restarts with compressor-specific framing.
- **`Ï„(Quran_Band-A)` lies within the null's 3Ïƒ envelope at all four candidate Ï„**: Î³ cannot be explained by any of the proposed structural-tightness functionals. Tier: SOFT FAIL. Programme declares Theorems 1 + 2 unachievable and recommends switching to an empirical-phenomenology paper instead.
- **Collaborator concludes no non-circular Ï„ exists**: Î³ is a tautological quantity in its own definition. Tier: HARD FAIL. Programme marks Î³ = +0.0716 as a permanent "empirical constant of unknown origin" in the paper, same category as Ï€-in-the-Bible speculation. Do not pursue further.

**Hard-FAIL clauses are binding**: if any of the three hard-FAIL conditions fire, the project retracts any claim beyond "Î³ is a reproducible empirical scalar" and does NOT pursue further derivation work.

---

## 9. Relationship to other open items in the project

| Open item | Relationship to Î³ derivation |
|---|---|
| `exp95_phonetic_modulation` (H33) | Empirical; independent of Î³ derivation. If exp95 PASSES with recall â‰¥ 0.999, it closes the Adiyat-864 practical ceiling without needing Theorem 2. |
| `exp97_crosscripture_t8` (H34) | Provides the corpus-scale p-value for Â§4.37. The Î³ derivation does not depend on it. |
| `exp98_vlcv_floor` (DONE, PASS_floor_revised) | Independent; VL_CV is a verse-level scalar, Î³ is a letter-level scalar. |
| Â§4.37 Multi-Scale Stack Law draft | The Â§4.37 Fisher combiner uses Î³ as its letter-scale term *empirically*; a derivation strengthens Â§4.37 but is not required for its writing. |
| `exp92_genai_adversarial_forge` | Falsifies the "Quran is forgery-robust" claim. If an LLM produces a high-Î³ synthetic surah, the Quran-uniqueness interpretation of Î³ falls — but the derivation itself does not. |

---

## 10. Out of scope

The following are explicitly NOT part of this programme:

- **Any claim that Î³ is a universal constant of physics**. Î³ is a compression-residual of Arabic scripture edits; it has no a-priori connection to physical constants.
- **Any claim that Î³ proves Quranic divine authorship**. This document and the broader project make no such claim; the Î³ derivation is a mathematical question about compressibility, not a theological one.
- **Nobel-grade framing**. Per `@c:\Users\mtj_2\OneDrive\Desktop\Quran\archive\LOST_GEMS_AND_NOBEL_PATH.md:282-316` and the opportunity scan Â§7 honest ceiling, a Nobel-category finding is not reachable from this corpus. The Î³ derivation's ceiling is a strong information-theory paper (Entropy / PRX Information / IEEE TIT).
- **Theological interpretation of whatever Ï„ emerges**. Ï„ is a mathematical functional; its theological interpretation is left to the reader.

---

## 11. Signature

This pre-registration is binding on the project's future direction in the following sense:

- Theorems 1–3 defined above, including their falsifiers, are the ONLY claims the programme is allowed to make about Î³.
- Any future paper that claims Î³ is derived must cite this document and demonstrate compliance with all three theorem specifications.
- Any mid-programme Ï„-switching requires a dated amendment to Â§4.5.

**Frozen** 2026-04-22. SHA-256 of this file at freeze time is computed and logged in the first `exp100_tau_audit` run, and any future edit to Â§Â§ 1–8 breaks the freeze.

---

## 12. Programme retraction addendum (2026-04-22 late)

This section was added on the same day the document was first frozen, because the pre-registered falsifier for Theorem 1 (`experiments/exp103_cross_compressor_gamma`) was executed same-day and returned `FAIL_not_universal` with CV(Î³) = 2.95 (four-compressor panel: gzip +0.0716, brotli +0.0871, zstd âˆ’0.0294, bzip2 âˆ’0.0483; all four `p < 0.01`; two positive, two negative).

**Programme status after this receipt**:

- The **Kolmogorov-derivation programme as originally scoped is aborted**. Theorems 1–3 are stamped-retracted (see banners at Â§Â§ 3.1, 3.2, 3.3).
- The **paper retains Î³ = +0.0716** as a **gzip-calibrated edit-detection parameter** (not a Kolmogorov constant). PAPER.md Â§4.25 has been updated to explicitly qualify this.
- The **substantive observation** is promoted to the restated form in Â§Â§ 3.1.R / 3.2.R: *"Four universal compressors disagree on both the magnitude and sign of the Quran's edit-detection residual; the signal is real under every family; its direction is compressor-modelling-dependent."*
- The **budget committed to this programme is reduced from ~$8–18 k / 6 months / mathematician-collaborator to $0**. The restated programme is purely empirical and already complete.
- The **collaborator recruitment** track is cancelled. No tier 5.1 / 5.2 / 5.3 collaborator needs to be recruited on the Î³ derivation.

**What remains open after this retraction**:

- Optional follow-up: `exp106_cross_script_gamma_4panel` — measure Î³ across the four compressors on Tanakh + NT + Iliad corpus edits, to quantify whether the **sign-by-family** pattern generalises. Low-priority, deferred.
- Optional follow-up: sign-monotonicity check across a 6+ compressor panel (add PPM, CM arithmetic coders) to test whether Î³ sign maps cleanly onto effective context-window size. Publishable on its own if it does.

**Lesson for project process**: this document's rev-1 state was a perfectly reasonable pre-registration, and its same-day empirical falsification was the pre-registration's own pre-registered mechanism working as intended. The PREREG-then-run-the-falsifier-first-before-recruiting-collaborators discipline saved the project from a ~6-month wrong direction. This pattern should be the default for any future "derive X theoretically" proposal: **empirical falsifier first, mathematician second**.

---

*For the practical / empirical upgrades that do NOT require the Î³ derivation (and can ship within one week), see `docs/OPPORTUNITY_SCAN_2026-04-22.md` Â§8. This document handles the long-horizon mathematical work; the opportunity scan handles the short-horizon empirical work. They are complementary, not competing.*
