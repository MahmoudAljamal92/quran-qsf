# C4 / C5 Fresh Op-Test Candidates — Brainstorm Doc

> **Status**: brainstorm document, 2026-04-28 evening (patch H V3.1).
> **Purpose**: enumerate fresh operationalisations for the two not-yet-operationalised Quranic self-claims so that `exp96c_F57_meta` (Phase 2) can either be re-tested against new data (improving S_obs from 4 / 6 toward 6 / 6) or honestly retired with the current 4 / 6.
> **Decision pending**: the project owner picks 1–2 candidates per claim. Each chosen candidate then becomes its own hash-locked PREREG before any data is opened.

---

## Background

| Claim | Verse | Reading we test | Failed op-tests | Rejection mode |
|---|---|---|---|---|
| **C4** | 11:1 (آيات أحكمت) | "verses are made precise / inviolably fitted" | FN03 (`exp98` per-verse MDL rate, Quran 4/7) + FN05 (`exp100` root density + bigram surprisal, Quran 5/7, audit fired) | The chosen metrics didn't capture "precision". |
| **C5** | 39:23 (متشابها مثاني) | "self-similar / mutually-resembling" | FN04 (`exp97` multifractal Δα, Quran 6/7, Hurst audit fired) + FN06 (`exp101` cross-scale cosine distance, Quran 7/7) | The Quran's Meccan/Medinan length split *defeats* metrics that demand global homogeneity. |

**Honest framing**: "C4 and C5 are not-yet-operationalised" is **not** "C4 and C5 are false". The *claims as stated by the Quran* are about what the Quran *is*; what we have shown is that two specific operational definitions of each claim do not pick out the Quran from the 7-Arabic-corpus pool. Better operationalisations may exist; this doc enumerates candidates.

---

## C4 — "verses made precise" (11:1) — five fresh candidates

### C4-I — Inflectional substitution invariance (recommended for first try)

**Hypothesis**: a "precisely-fitted" verse is one whose information content is *not* preserved when an inflectional morpheme (case ending, gender, number) is swapped for an alternative. Operationally: for each Quran verse, enumerate every single-inflection-swap variant, compute the per-verse `Δ_NCD` against the canonical surah, and rank corpora by the **median Δ_NCD per swap**.

**Direction**: Quran has the **largest** median Δ_NCD per inflection swap → "every inflection is load-bearing".

**Why fresh**: not the same axis as MDL rate (which compresses content) or root density (which counts roots).

**Testability**: existing 5-D pipeline + the K=2 multi-compressor consensus rule from F53 already handles single-letter substitutions; inflection swaps are a small extension.

**Risk**: poetry has dense inflection too. Need to control for genre. **Direction may not pick out Quran rank 1**.

---

### C4-II — Verse-internal redundancy ratio

**Hypothesis**: a precise verse is one where every word *is needed*. Operationalise as: for each verse, drop one word at a time, compute the change in cross-surah perplexity using a frozen Arabic LM. The drop-one perplexity-delta distribution should be *narrower and higher* for the Quran than for controls (every word matters about equally, and matters a lot).

**Direction**: Quran has the **smallest CV of drop-one perplexity-delta** AND the **highest median delta** simultaneously.

**Why fresh**: cross-cuts MDL (which compresses) and root density (which counts).

**Testability**: needs a frozen Arabic LM (e.g. AraGPT2, locked SHA + version). Model availability is an issue and would have to be solved in PREREG.

**Risk**: LM bias (any LM trained on Arabic has been heavily exposed to Quran).

---

### C4-III — Surah-level paraphrase distance ceiling

**Hypothesis**: if verses are "made precise / inviolably fitted", the *closest paraphrase that preserves meaning* is structurally very far from the canonical. Generate K paraphrases per verse via a paraphrase model (frozen), measure minimum edit-distance to the canonical. Quran has the **largest minimum edit distance** (paraphrase-resistant).

**Direction**: Quran rank 1 (largest minimum-distance-to-paraphrase).

**Why fresh**: this is closer to the user-intuition reading of أحكمت — "fixed in a way that resists rewording".

**Testability**: needs a paraphrase model or human-generated paraphrases. Costly. Could subsample to 100 verses for a pilot.

**Risk**: paraphrase models trained on Arabic Quranic data have a heavy prior against rewording.

---

### C4-IV — Letter-position-stability under deletion

**Hypothesis**: in a precise verse, removing any single letter produces a verse that is *not gracefully recoverable* — the closest valid Arabic word recovers to a word that changes the verse's NCD signature outside the locked Quran cluster. Operationalise as: for each verse, delete each letter, find the nearest-edit-distance valid Arabic dictionary word, recompute the surah's 5-D fingerprint, measure displacement.

**Direction**: Quran has the **largest mean displacement** under single-letter deletion.

**Why fresh**: an *integrity* axis distinct from MDL or root density.

**Testability**: needs an Arabic dictionary (e.g. Hindawi Arabic word list); letter deletion is fast.

**Risk**: tightly coupled to F55 (which is similar but for substitution); the new test must be substantively different from F55.

---

### C4-V — Closest-canonical-rasm-shift count

**Hypothesis**: a verse is "precise" iff perturbing it by one letter produces a rasm pattern that is *not seen elsewhere in classical Arabic* (i.e., the perturbed rasm is anomalous). Operationalise: for each single-letter substitution variant of each Quran verse, count the number of times the perturbed rasm pattern appears in the locked Arabic peer pool. Quran has the **lowest median count** (most anomaly-creating perturbations).

**Direction**: Quran rank 1 (lowest median).

**Why fresh**: an anomaly-detection axis on the perturbed text, not the canonical text.

**Testability**: requires a rasm-pattern index of the peer pool; can be built from existing locked corpora.

**Risk**: rasm patterns of length n are sparse for large n; need to fix a useful n.

---

## C5 — "self-similar / mutually-resembling" (39:23) — five fresh candidates

### C5-I — Per-letter rate stability across surahs (recommended for first try)

**Hypothesis**: every Quran surah has approximately the same 28-letter usage distribution; controls have surah-internal variation that exceeds Quran's. Operationalise as: for each corpus, compute per-unit (per-surah for Quran, per-chapter for controls) 28-letter letter rate vector; report **median pairwise Jensen-Shannon divergence** across all unit pairs within the corpus. Quran rank 1 = lowest median JSD.

**Direction**: Quran has the **smallest median pairwise JSD** of letter-rate vectors → most internally letter-rate-uniform.

**Why fresh**: cross-cuts cosine-of-5-D-features (FN06) and Δα (FN04). This is a much simpler, single-axis test.

**Testability**: trivially fast; no new dependencies.

**Risk**: if Meccan/Medinan rasm differences dominate, this fails for the same reason FN06 did. But unlike FN06, the metric is letter-level not feature-level, so it could survive.

---

### C5-II — Bigram-distribution invariance under random partition

**Hypothesis**: take any 30 % subset of Quran surahs, compute the bigram distribution; compare to whole-Quran via JSD; repeat n=1000. The **maximum** JSD is small for Quran, larger for controls. "Self-similar" = "any half resembles the whole".

**Direction**: Quran has the **smallest 95th-percentile JSD across 1000 random 30 % partitions**.

**Why fresh**: a partition-invariance axis, not a centroid axis (FN06).

**Testability**: fast; bigrams are cheap.

**Risk**: small surahs dominate JSD noise; need to require minimum subset letter count.

---

### C5-III — Cross-surah motif-recurrence rate

**Hypothesis**: if surahs "resemble each other" semantically, the same lexical motifs (n-gram phrases like "إن الله غفور رحيم", "يا أيها الذين آمنوا") appear in multiple surahs. Quran has the highest median motif-recurrence rate. Operationalise as: count distinct trigrams that appear in at least k surahs; normalise by total trigram count.

**Direction**: Quran has the **highest fraction of trigrams appearing in ≥ 3 distinct surahs** of all 7 corpora.

**Why fresh**: a recurrence/refrain axis. Closes the gap left by FN04 / FN06 (which both used continuous metrics).

**Testability**: trivial bigram/trigram counting.

**Risk**: poetry corpora may have similar recurrence. Need direction check vs. each control.

---

### C5-IV — Theme-cluster mutual-resemblance score

**Hypothesis**: under a frozen topic-modelling pipeline (LDA with k = 20 topics, locked seed), each Quran surah has a topic distribution that significantly overlaps with multiple other surahs (cosine similarity > τ on at least 5 sibling surahs). Quran has the highest median sibling-overlap count.

**Direction**: Quran rank 1 (highest median number of sibling surahs above τ).

**Why fresh**: a topic-level resemblance axis, deeper than letter or bigram.

**Testability**: needs LDA. Costly but pre-registrable cleanly.

**Risk**: topic-modelling has many free parameters; locking them all in a PREREG is essential and hard.

---

### C5-V — Recursive sub-verse self-similarity

**Hypothesis**: within a single Quran surah, half-surah feature centroids are close to each other (median half-vs-half cosine distance is low); within a control corpus chapter, half-chapter centroids are far apart. This is the *intra-unit* version of FN06's *inter-unit* test, which failed.

**Direction**: Quran has the **smallest median intra-surah half-half cosine distance** across all 114 surahs.

**Why fresh**: inverts the scale at which FN06 looked. FN06 measured "long-vs-short surah" (large scale); C5-V measures "first-half-vs-second-half within a single surah" (small scale).

**Testability**: existing 5-D feature extraction works on half-surahs.

**Risk**: half-surah feature estimates are noisier; n_verses / 2 may be too few for stable estimates on short surahs.

---

## Recommendations

### For C4: **C4-I (inflectional swap invariance)** as the first try

- Closest to the intuition of "fitted / precise" without requiring an LLM.
- Reuses the F53/F55 infrastructure for single-letter perturbations (just at the inflection level instead).
- Quick to implement and run.

### For C5: **C5-I (per-letter JSD)** as the first try

- The simplest possible test for "self-similar".
- Uses no LLM, no LDA, no morphology — only 28-letter counts.
- Bit-reproducible; cheap to run on existing locked corpora.
- If C5-I FAILS, C5-II is the next try (partition-invariance) — it tests a related but distinct property.

---

## Process for promoting a candidate to a PREREG

1. Project owner selects one candidate per claim from the menu above (or proposes a new one).
2. Cascade drafts a hash-locked PREREG (`experiments/expXXX_<name>/PREREG.md`) with:
   - Hypothesis ID (next available H-number; H60 onward)
   - Frozen constants (per-claim-specific)
   - Verdict ladder (PASS / PARTIAL / FAIL with strict order, first-match-wins)
   - Audit hooks (PREREG-hash sentinel, corpus-hash sentinel, etc.)
   - Honesty clauses (no re-roll, no metric switch, no compressor change)
3. Owner reviews and approves.
4. PREREG_HASH.txt is written.
5. Run.py is built, enforcing `_PREREG_EXPECTED_HASH`.
6. Experiment runs; receipt produced.
7. Verdict propagates to:
   - `RANKED_FINDINGS.md` (header version bump, F-number if PASS)
   - `RETRACTIONS_REGISTRY.md` (FN-number if FAIL)
   - `HYPOTHESES_AND_TESTS.md` (H-row updated)
   - `PROGRESS.md` + `CHANGELOG.md` (patch entry)
   - `PAPER.md §4.46.4` (claims table updated)

---

## What if every fresh op-test also fails?

Then C4 and C5 stay **not-yet-operationalised** indefinitely. The honest read is: "the Quran says of itself it is *muḥkam* (C4) and *mutashābih mathānī* (C5); modern computational operationalisations of these claims do not pick out the Quran from a 7-Arabic-corpus pool. We do not assert these claims are false; we only show that the chosen operationalisations failed."

This is the same honesty discipline that produced the 53 retractions and 7 failed-null pre-registrations on record. F57 stays at 4/6 PASS regardless.

---

*Authority: this is a brainstorm document, not a frozen claim. No experiment is run from this file. The PREREG, when one is filed, is the locked record.*
