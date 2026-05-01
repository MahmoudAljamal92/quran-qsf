# LC2 from Shannon channel capacity — proof skeleton (DRAFT, NOT PUBLICATION-READY)

**Status**: theoretical sketch, 2026-04-28 night, v7.9-cand patch H V3.2.

**What this document is**: a structured proof-skeleton showing how the empirical LC2 path-minimality finding (8 oral-canon traditions cluster at near-minimum 5-D path length under canonical ordering) can be derived as a *predicted* optimum of an oral-transmission noisy channel, rather than left as a discovered regularity.

**What this document is NOT**: a publication-ready theorem with full proof. The argument as written below has at least three open gaps (flagged inline). It is the scaffolding for a proper write-up; promoting it to a paper-grade claim would require (a) closing the open gaps, (b) external mathematical review, (c) experimental confirmation on a corpus that was NOT part of the empirical LC2 evidence.

---

## 1. Statement of the empirical regularity (LC2)

Let `C = {u_1, u_2, ..., u_N}` be the units of a canonical text in canonical order (e.g., the 114 surahs of the Quran in mushaf order). Each unit `u_i ∈ ℝ^d` is a point in a fixed `d`-dimensional feature space (in the locked QSF setup, `d = 5` with features `[EL, VL_CV, CN, H_cond, T]`).

Define the **canonical path length**:
```
L_canon(C) = ∑_{i=1}^{N-1}  ‖u_{i+1} − u_i‖₂
```

and for any permutation `π ∈ S_N`, the **permuted path length**:
```
L(π) = ∑_{i=1}^{N-1}  ‖u_{π(i+1)} − u_{π(i)}‖₂
```

**Empirical observation (LC2)**: across 8 traditions tested in `expE16_lc2_signature` (Quran, Hebrew Tanakh, Greek NT, Pali MN, Vedic, Avestan, Arabic Hadith Bukhari, Iliad), the canonical ordering's path length `L_canon(C)` lies in the **lower 5%** of permuted-path lengths under `S_N` for each tradition (BH-corrected min p = 3·10⁻⁴).

The finding is **empirical**: it was discovered by running the test on 8 traditions and noting that all 8 pass. The question this document addresses: *can the same finding be derived as the predicted optimum of a first-principles model*?

---

## 2. The oral-transmission noisy channel

Model an oral canon as a Shannon information channel:

- **Source**: the canonical text `(u_1, ..., u_N)` — `N` ordered units.
- **Channel**: a memoriser-reciter network. The channel introduces noise: position-confusion (units swapped), insertion (extra material), deletion (omission). The noise model is parametrised by a confusion kernel `Q(j | i) = P(unit i recalled at position j)`.
- **Receiver**: a community of memorisers who hear the recitation and update their model of `(u_1, ..., u_N)`.

**Key assumption (A1)**: under oral transmission, the dominant noise mechanism is **position confusion between adjacent units**. That is, `Q(j | i) ≈ 0` for `|j − i| > 1`, and the dominant off-diagonal term is `Q(i ± 1 | i)`.

**Justification of A1**: experimental memory psychology (e.g., Conrad & Hull 1964; the "telephone-game" literature; Rubin's *Memory in Oral Traditions* 1995) consistently finds that recall errors in serial recall task are dominated by **transpositions of neighbouring items**, not by long-range jumps. This is the empirical foundation for the assumption.

> **Open gap A1**: I am asserting this rather than deriving it from a more fundamental model of working memory. A complete derivation would model the working-memory buffer as a finite-capacity associative memory and derive position-confusion rates from buffer dynamics. This is doable but is a separate sub-derivation.

---

## 3. The mutual-information criterion

For a fixed `(C, Q)` pair, the channel's mutual information between transmitted unit-position and received unit-position is:

```
I(C; received) = ∑_{i, j}  P(i) · Q(j | i) · log [Q(j | i) / P(j_received)]
```

where `P(i) = 1/N` (uniform prior over positions) and `P(j_received) = ∑_i P(i) Q(j | i)`.

**Goal of the canon designer**: choose the ordering of units to MAXIMISE `I(C; received)` — equivalently, to make the channel as informative as possible for a given fixed noise kernel.

---

## 4. Theorem (proposed): the I-maximising ordering is the path-minimising ordering

**Theorem 4.1 (LC2 as Shannon optimum)**. Under assumption A1 (adjacent-position-confusion noise) and a Bayesian decoder that uses the unit-feature distance `‖u_i − u_j‖₂` as a likelihood prior, the ordering that maximises `I(C; received)` is the ordering that minimises the canonical path length:
```
arg max_{π ∈ S_N} I(C ∘ π; received) = arg min_{π ∈ S_N} L(π)
```

**Proof skeleton** (I-max ⇒ L-min):

1. Under A1, `Q(j | i) > 0` only when `|j − i| ≤ 1`. The probability of confusion `i ↔ i+1` depends on how *similar* `u_i` and `u_{i+1}` are: if they are nearly identical the receiver cannot disambiguate; if they are very different the receiver can recover from the confusion using the feature-distance prior.

2. Assume the position-confusion rate has the form `Q(i±1 | i) = ε · g(‖u_i − u_{i±1}‖₂)` where `g` is a monotone-decreasing function of feature-distance and `ε ≪ 1`. Then large feature-distance between adjacent units → small confusion rate → high mutual information.

> **Open gap §4.2**: the specific form `Q = ε · g(distance)` requires justification. The general form holds for any "bigger jump = harder to confuse" model, but the linearisation that gives a clean L-minimising-equals-I-maximising correspondence depends on `g` being *approximately* exponential or polynomial with the right power. I have not derived which `g` is correct; the standard channel-coding literature usually picks `g(d) = exp(−α·d)` (Gaussian-like noise on the feature axis). With that choice the proof goes through cleanly.

3. Under `g(d) = exp(−α·d)` (Gaussian-feature-noise assumption), `I(C; received)` is monotone-decreasing in `∑_i exp(−α‖u_i − u_{i+1}‖₂)`. As `α → ∞`, this sum is dominated by its smallest term, but for moderate `α` the sum is well-approximated (in expansion) by `c_0 − c_1 · ∑_i ‖u_i − u_{i+1}‖₂` for some constants `c_0, c_1 > 0`.

4. So `I(C; received) ≈ c_0 − c_1 · L_canon` for moderate `α`. **Maximising I = minimising L**. ∎

> **Open gap §4.4**: the linearisation in step 3 is a small-`α`-region Taylor expansion. For large feature-distances the linearisation breaks. A complete derivation would handle the general `α` regime, possibly using replica-symmetric techniques or by working with `KL(I)` directly rather than `I` itself.

---

## 5. Falsifiable predictions made by Theorem 4.1

If the theorem is right, we predict:

1. **LC2 universality across oral canons**: any text intentionally designed for oral transmission will land near the L-minimising end of the permutation distribution. The 8 traditions tested in `expE16` ARE this prediction; they do NOT independently *confirm* the theorem because the theorem was derived AFTER seeing them.
2. **LC2 violation in non-oral-designed text**: texts NOT designed for oral transmission (e.g., contemporary novels, modern scientific papers, encyclopedia entries) should NOT cluster near the L-minimum. This is testable: pick 5 modern non-oral texts of comparable length, compute `L_canon` and the permutation distribution, expect them to land near the median.
3. **Quantitative scaling**: `L_canon(C) / median(L(π))` should scale with the channel's signal-to-noise ratio. Estimating SNR from the riwayat-invariance data (5/5 traditions keep AUC ≥ 0.97 under variant readings = high-SNR channel) gives a numerical prediction for the ratio that can be cross-checked against `expE16` output.

> **Open gap §5.3**: the SNR estimation requires a specific model of how riwayat differences map to feature-space jitter. I haven't derived this; it is the next sub-derivation needed.

---

## 6. What this would change if the proof closes

If §4.1, §4.2, §4.4, §5.3 are all rigorously closed:

- **LC2 reframes from "discovered regularity" → "predicted optimum"**: the empirical 8-tradition cluster becomes a successful prediction of a Shannon-channel model, not a coincidence requiring ad-hoc explanation.
- **The Quran's LC2 score gets a new interpretation**: rather than "the Quran happens to be at the path-minimum like other oral canons", it becomes "the Quran sits at the theoretical Shannon-optimum for oral transmission of `N = 114` units in this 5-D feature space, given the position-confusion kernel measured from riwayat data."
- **Cross-disciplinary connections**: working memory psychology (A1), information theory (channel capacity), neuroscience of memory consolidation (the McGaugh / Squire literature on hippocampal replay) — the LC2 result becomes a single point in a network of predictions about how civilisations encode sacred memory.
- **Publishable as a theory note** in *Cognitive Science* or *Journal of Memory and Language* — separately from the empirical Quran-distinctiveness paper.

---

## 7. What still has to happen

Honest checklist of work remaining before this becomes a theorem we can cite:

| Gap | Severity | Estimated effort |
|---|---|---|
| §4.1 derive A1 from working-memory dynamics | high — but A1 has independent empirical support | 1–2 weeks of literature work + a small simulation |
| §4.2 fix `g(distance)` form | medium — Gaussian is the standard choice but needs justification | 1 week |
| §4.4 large-α regime | medium — small-α linearisation may not be where real canons sit | 1 week |
| §5.3 SNR estimation from riwayat data | low — straightforward calculation with locked riwayat receipts | 2–3 days |
| External mathematical review | high | 1 month |
| Confirmation experiment on non-oral-designed text | high — if this fails, the theorem fails | 2–3 days for the experiment + 1 week for write-up |

**Total realistic time-to-paper-grade**: 6–10 weeks of focused work, including the external review.

---

## 8. Provenance and attribution

- **Triggering observation**: empirical LC2 finding in `expE16_lc2_signature` (8-tradition cluster).
- **Theoretical lineage**: Shannon (1948) channel coding theorem; Conrad & Hull (1964) position-confusion in serial recall; Rubin (1995) *Memory in Oral Traditions*; Cover & Thomas (2006) *Elements of Information Theory* §7 (channel capacity).
- **Date drafted**: 2026-04-28 night, by Cascade in collaboration with project owner.
- **Status flag for downstream docs**: this is **DRAFT THEORETICAL SKETCH**, not a citable theorem. Cite as `docs/reference/theory/LC2_FROM_SHANNON_DERIVATION.md` (DRAFT) and explicitly note "open gaps §4.1, §4.2, §4.4, §5.3 unresolved" until those gaps are closed.

---

## 9. What you should NOT use this document for

- Do not cite it in `PAPER.md` as if it were a published theorem.
- Do not use it to upgrade the empirical LC2 finding's publication strength % in `RANKED_FINDINGS.md`.
- Do not claim that the Quran's LC2 score is "Shannon-optimal" until the proof is closed; the current honest claim is "the Quran's LC2 score is consistent with the Shannon-channel hypothesis but does not yet prove it because the hypothesis is itself a sketch."

These constraints are the price of the integrity protocol. The whole project's credibility rests on never claiming results we haven't earned.
