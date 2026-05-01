# Reviewer Feedback — 2026-04-26 (post-patch-E external read)

**Status**: Substantive external critique. **Acted on at memo + SUBMISSION_READINESS + RANKED_FINDINGS-callout level**. Deeper actions (PAPER.md re-frame, new LC2 experiments) are proposed but not yet committed.

**Authority**: This memo is institutional memory only. Authoritative response state is reflected in:
- `@C:/Users/mtj_2/OneDrive/Desktop/Quran/docs/reference/sprints/SUBMISSION_READINESS_2026-04-25.md` (Package P0 added)
- `@C:/Users/mtj_2/OneDrive/Desktop/Quran/docs/reference/findings/RANKED_FINDINGS.md` (master-table callout added)
- `@C:/Users/mtj_2/OneDrive/Desktop/Quran/CHANGELOG.md` (this memo logged)

---

## 1. The feedback (verbatim summary, 3 claims)

> ⚠ **External AI evaluation of the v7.9-cand patch E findings record, 2026-04-26 evening.**

**Claim 1 — Venue misalignment.** The findings are significant within their domain. The domain is "quantitative stylometry of a single Arabic text vs a curated control pool." That is a legitimate scientific domain. **It is not physics.** The numbers look like physics — T² = 3,557, p ≈ 10⁻⁴⁸⁰ — but the null models are stylometry-class, not Standard-Model-class. The Quran vs 2,509 Arabic texts is not the same epistemic structure as a Higgs boson vs QCD background. Reviewers at physics journals will say this immediately. The right venues are **computational linguistics, information theory, and digital humanities** — not Physical Review.

**Claim 2 — The EL finding is "known intuitively for 1,400 years."** What QSF adds is the precise quantification, the rigorous comparison pool, the falsification discipline, and the Shannon-theoretic scaffolding showing it can't be explained by letter-frequency effects alone. That upgrade from "known intuitively" to "known precisely with error bars" is a genuine scientific contribution, but it's not surprising to domain experts the way the Higgs discovery was surprising to physicists. **The "WHY" is not answered.** The Quran's EL elevation could reflect intentional compositional design, single-author convention, oral-composition constraints, transmission preservation effects, or some combination. QSF doesn't and can't distinguish these.

**Claim 3 — LC2 is the answer for significance.** The cross-tradition result — that path-minimality in feature space is a **shared property of oral-liturgical canons** across four continents, four scripts, and three millennia of independent tradition — is the finding that would make a non-specialist want to read the paper. It implies something about the cognitive-cultural pressures on how religious communities organize their canonical texts for oral transmission. **THAT is what PNAS means by "significance beyond the specific domain."** The paper currently treats LC2 as one finding among 52. **It should be the frame for the entire paper.** The Quran is not the most extreme case of LC2 — the Rigveda is — but it's the one we have the most detailed stylometric fingerprint for. Written that way, the title becomes:
>
> *"Canonical ordering in oral-liturgical scriptures minimizes structural path cost: a cross-tradition information-theoretic study"*
>
> with the Quran as the **anchor case**, not the universal claim.

---

## 2. Project response — claim-by-claim

### Claim 1 (venue misalignment) — **PRE-EMPTED, BUT WORTH CONFIRMING IN PAPER.md**

This was already our position; see `@C:/Users/mtj_2/OneDrive/Desktop/Quran/docs/reference/sprints/SUBMISSION_READINESS_2026-04-25.md:7`:

> "Honest ceiling is top-tier domain journal, **not** Nobel."

And explicitly: *"PNAS stretch + PRX Information / IEEE Trans. Info. Theory / Phys. Rev. E. Nobel-tier framing has been formally ruled out by the project lead."*

**Action**: confirm in `PAPER.md §1` (introduction) that we are positioning as a **computational-linguistics + information-theory + digital-humanities** paper. Possibly add a one-line "scope note" in the abstract.

### Claim 2 (EL is precision over intuition) — **HONESTLY ALIGNS WITH OUR FRAMING; NEEDS EXPLICIT WORDING**

This is the right framing. We do already say it implicitly in §4.40 — but the abstract still reads as if EL is a *new* finding. The reviewer is asking us to **front-load** the qualifier "precise quantification of a known phenomenon, not discovery of a new one." That's an honest pivot.

The genuinely *new* contribution layer (which the reviewer praises) is the **Shannon-capacity scaffolding** — `expP18` shows EL_iid_floor = 0.295, Quran's actual EL = 0.720, structural rhyme excess = +0.425 — the +0.425 *cannot* come from letter-frequency concentration alone. That's the part that is genuinely new (not a 1,400-year intuition) and should be the weight-bearing scientific claim of the abstract.

**Action**: rewrite `PAPER.md` abstract paragraph 1 to lead with: "**Arabic philological tradition has long observed that the Quran's verse-endings exhibit a characteristic concentration of terminal letters (the *fawāṣil* phenomenon). We provide the first information-theoretically rigorous quantification of this:** EL = 0.720 vs i.i.d. Shannon floor 0.295 — a structural-rhyme-correlation excess of +0.425 that is not explainable by letter-frequency effects."

### Claim 3 (LC2 should be the frame) — **THE GENUINELY NEW STRATEGIC INSIGHT**

This is the one item where the reviewer is telling us something we **haven't already said in our own self-assessment**. Currently:
- LC2 is finding #13 of 52 in `RANKED_FINDINGS.md` (strength % = 88)
- Quran-AUC findings are #1, #2, #3 (strength % = 92-93)
- The paper is structured around the Quran fingerprint with LC2 as a §4.36-§4.39 cross-tradition supplement

The reviewer is proposing the **paper structure flips**: LC2 becomes the headline cross-tradition universal claim; the Quran 5-D fingerprint becomes the most-detailed *anchor case study* supporting it. This is a pure framing change — no new scientific claim is required. It's identical to the existing data, presented under a different organizing thesis.

**Why this is the strongest move available**: LC2 is the only finding in the project where the *non-specialist* significance is obvious. It says something about *human cognition and oral-transmission cultural evolution*, not just about one specific text. That's the PNAS-significance test the reviewer cited.

**Status**: documented + scaffolded but **not yet committed as a structural rewrite**. Awaits user decision.

---

## 3. Action register

| ID | Action | Effort | Status |
|---|---|---|---|
| A1 | This memo | 15 min | ✅ DONE 2026-04-26 |
| A2 | Add "Package P0 — LC2 cross-tradition paper" to `SUBMISSION_READINESS_2026-04-25.md` with venue ladder | 30 min | ✅ DONE 2026-04-26 |
| A8 | Add publication-strategy callout to `RANKED_FINDINGS.md §2` master-table header noting LC2 is the recommended headline despite not being the highest-strength-% finding | 15 min | ✅ DONE 2026-04-26 |
| A3 | Draft new abstract + §1 skeleton in `docs/PAPER_LC2_FRAME.md` (separate file, doesn't touch `PAPER.md`) | 1.5 h | **PROPOSED** — awaits user commit |
| A4 | `expP19_lc2_corpus_extension` — add 2-3 more oral-liturgical corpora (Adi Granth/Sikh, Mahabharata, Coptic Liturgy, or Egyptian Book of the Dead) → push n from 6 to 8-9 | 4-6 h compute + 1 day data sourcing | **PROPOSED** |
| A5 | `expP20_lc2_shannon_capacity_sketch` — closed-form prediction: which of {R3, J1, Hurst, AR(1)} should minimize under noisy-channel Shannon-capacity? | 1 day for sketch, 6-12 months for full proof | **PROPOSED** |
| A6 | `expP21_lc2_ordering_strength_predictor` — meta-regression of z-score against canon properties (era, oral/written ratio, alphabet size, etc.) | 1 day | **PROPOSED** |
| A7 | `expP22_lc2_stricter_null` — within-corpus style-preserving permutation null replacing book-shuffle | 3 days | **PROPOSED** |

**Forbidden until user commits**: editing `PAPER.md` itself for the LC2 frame. The current `PAPER.md` is the run-of-record for the Quran-anchored paper (P3 in the submission table) and must remain coherent under that frame until/unless we commit to the pivot.

---

## 4. Decision points for the project lead

1. **Is the LC2 framing pivot worth committing to?** This is a publication-strategy decision: do we publish (a) a defensible Quran-stylometry paper at a CL/DH venue, or (b) an ambitious cross-tradition oral-transmission paper at a PNAS/Cogn-Sci venue with the Quran as anchor?
   - **(a)** is safer, lower-ceiling, and the data fully supports it today.
   - **(b)** is higher-ceiling, requires the framing rewrite (A3), and benefits from but does not strictly require the new experiments (A4-A7).
   - **Both** are also possible — submit P0 (LC2 frame) to PNAS / Cogn-Sci and P3 (Quran frame) to a CL/DH venue as a companion paper. They share data; they differ only in thesis.

2. **If (b) or (both): which experiments do we commission?** A5 (Shannon-capacity sketch, 1 day) is the highest-leverage single addition because it provides the *theoretical* underpinning the reviewer flagged as a strength of the EL section. A4 (corpus extension to n=8-9) is the strongest empirical reinforcement.

3. **Should A8 reorder the master table** (promote LC2 from #13 to #1)? The current implementation is a callout, not a reorder. A reorder would require restating LC2's strength % at 90+, which is defensible only under the publication-strategy pivot, not under the raw stat × rob × gen × pub axes. Keeping the callout-not-reorder is the conservative move; promote when/if (b) is committed.

---

## 5. Cross-references

- `@C:/Users/mtj_2/OneDrive/Desktop/Quran/docs/reference/findings/RANKED_FINDINGS.md` (LC2 = finding #13, strength 88 %)
- `@C:/Users/mtj_2/OneDrive/Desktop/Quran/docs/reference/sprints/SUBMISSION_READINESS_2026-04-25.md` (Package P0 added)
- `@C:/Users/mtj_2/OneDrive/Desktop/Quran/docs/reference/sprints/CROSS_TRADITION_FINDINGS_2026-04-25.md` (LC2 source data: Rigveda z=−18.93, Tanakh z=−15.29, NT z=−12.06, Quran z=−8.92, Avestan z=−3.98, Pali_MN z=−3.46, Iliad z=+0.34 control fail, LOO 8/8 robust)
- `@C:/Users/mtj_2/OneDrive/Desktop/Quran/CHANGELOG.md` patch E entry (Shannon-capacity scaffolding via `expP18`)
- `@C:/Users/mtj_2/OneDrive/Desktop/Quran/results/experiments/expP4_cross_tradition_R3/expP4_cross_tradition_R3.json` (the LC2 numbers themselves)

---

*This memo is append-only. Reopenings or status updates get a dated subsection at the bottom of §3 with the action ID and new status.*
