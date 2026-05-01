# Phase 5 — Implementation plan for the human-forgery protocol

**Status**: planning document. Companion to `docs/reference/HUMAN_FORGERY_PROTOCOL.md` (which defines *what* gets measured); this file defines *how to actually run it* (recruit authors, handle ethics, score deliveries, publish outcomes).

**Filed**: 2026-04-28 night, v7.9-cand patch H V3.2.
**Owner**: human researcher (Cascade cannot run this — it requires recruiting Arabic-fluent authors).
**Cost to project**: ~$3,000–$8,000 in author honoraria + ~6 months of calendar time + 1 IRB filing.

---

## 1. The unaddressed gap (why this matters now)

Per `PAPER.md §4.46.6` ("the cleanest defensible scientific sentence") and `HUMAN_FORGERY_PROTOCOL.md §1`, the Φ_master = 1,862 nats / BF ≈ 10⁸⁰⁹ headline is conditional on the null hypothesis being **"naturally-occurring Arabic prose"**. The honest null for a divinity-implication reading is **"the best deliberate human Arabic composition designed by knowledgeable authors with full disclosure of the Φ_master formula."** That null has never been measured.

`exp99_adversarial_complexity` measures vs **random Markov-3 forgeries** (0/10⁶ pass joint gate) — that's a strong adversarial-machine result but not an adversarial-human result. The locked exp93/exp94/exp95-series Quran-internal robustness, the Arabic-peer-corpus benchmarks, and the 5-riwayat-invariance receipts all measure structural properties of *existing* texts; none of them measures what a Quran-knowledgeable Arabic linguist would produce under maximum-effort conditions with the formula in hand.

**Until Phase 5 runs, every exp99 / Φ_master claim must carry the explicit caveat: "tested vs naturally-occurring and machine-randomised Arabic; not tested vs deliberate human forgery designed against the disclosed formula."** That caveat is currently in the PAPER but in our experience reviewers will probe it sharply.

---

## 2. What an honest, IRB-clearable Phase 5 looks like

### 2.1 Authors — who and how many

**Target**: 3–7 Arabic-fluent authors, recruited independently of each other (no collaboration between forgers), each producing one candidate independently. The N ≥ 3 minimum is so that any single FAIL outcome doesn't anchor on idiosyncrasy of one author; the N ≤ 7 maximum is for budget / coordination.

**Author qualifications** (locked before recruitment opens):

| Tier | Minimum profile | Expected effort budget per author |
|---|---|---|
| **Tier-A (preferred)** | Native Arabic speaker; PhD or equivalent in classical Arabic literature, Qur'anic studies, or Arabic linguistics; **prior published work involving saj' or Quran stylistics** | 40–80 hours |
| **Tier-B (acceptable)** | Native Arabic speaker; MA in Arabic / Islamic studies; demonstrated competence with `Maqamat al-Hariri`-style classical saj' OR contemporary Arabic poetry | 20–40 hours |
| **Tier-C (probe only)** | Fluent Arabic speaker; advanced student; no formal saj' track record | 5–15 hours |

Recruit **at least one Tier-A author**. The protocol explicitly does not require religious belief or non-belief — what matters is technical competence with classical Arabic, not theological position.

### 2.2 Recruitment channels (in roughly recommended order)

1. **Direct academic outreach**: Department-of-Arabic / Department-of-Islamic-Studies faculty at: SOAS London, Edinburgh, Leiden, Tübingen, Princeton NES, McGill IIS, AUB, Cairo Univ., Tunis Univ., Al-Azhar (delicate). Cold-email with the protocol document attached.
2. **Twitter / X academic Arabic-studies community** (hashtag `#ClassicalArabic`, `#Quranic_Studies`).
3. **Reddit r/AcademicQuran, r/arabic** (carefully — the project framing must NOT be confrontational).
4. **Prolific / Upwork**: paid platforms can reach Arabic-fluent contributors but the saj' competence floor is rarely met; use Tier-C tier only.
5. **IIS / AKU Aga Khan**: large Arabic-studies network; likely to refer Tier-A authors.

**Do NOT**: post to apologetics forums (will produce ideologically-motivated submissions that conflate "want to falsify the project" with "competence"); offer specific religious framing in the call.

### 2.3 Compensation

- **Tier-A**: $1,500–$2,500 honorarium (reflects 40–80 h at fair-rate-for-PhD-Arabic-linguist).
- **Tier-B**: $750–$1,200.
- **Tier-C**: $200–$400.
- Total budget for N = 3 (1A + 1B + 1C) to N = 7 mixed: $2,500–$8,000.
- **Pre-commit publication of all author submissions including FAILs**, so authors are credited regardless of outcome (paid for effort, not for "passing").

### 2.4 IRB / ethics

This is **minimal-risk human-subjects research** under U.S. 45 CFR 46.104(d)(2)(i) (research involving educational tests, surveys, interviews, or observation of public behaviour, with no identifiable private information beyond name/affiliation). The author submits a creative-text artifact that they consent to publish; no behavioural-experiment manipulation; no deception.

**Required IRB filings** (under most institutional rules):
- Institutional review (likely "exempt" status) at PI's home institution if the PI is academic. ~6 weeks lead time.
- If no PI institution: **OHRP-registered IRB on contract** (Advarra, WCG IRB, Pearl IRB; cost ~$500–$2,000). ~3 weeks.
- **NO IRB needed** if all authors are independent professional consultants writing under contract (commission model rather than research-subject model). This is the cleanest path.

**Recommended path: contract / commission model.** Each author signs a standard work-for-hire contract specifying:
- Compensation, deliverable (one Arabic surah of [5, 50] verses), deadline (loose, ≥ 60 days).
- IP: author retains authorship credit; project gets non-exclusive publication rights.
- Submission via signed PDF or git commit; published verbatim under author's preferred name.
- **No "you must beat Φ_master ≥ X to be paid" clause** — payment is for effort, not for outcome. This is essential for fairness.

### 2.5 Pre-registration of the human-forgery PREREG

**File before any author submission is opened**: `experiments/exp_phase5_human_forgery/PREREG.md`, hash-locked, mirroring the structure of `experiments/exp96a_phi_master/PREREG.md`. The PREREG specifies:
- The verdict ladder from `HUMAN_FORGERY_PROTOCOL.md §4` byte-for-byte (no relaxation).
- The scoring script `scripts/score_human_forgery.py` (committed before any author file is opened).
- An audit hook: SHA-256 of every author submission file is logged AT-RECEIPT-TIME and published. No submission is silently revised.
- A pre-commitment to publish ALL author results (including any that score above the project headline) in the next PAPER revision.

### 2.6 Implementation of `scripts/score_human_forgery.py`

Per `HUMAN_FORGERY_PROTOCOL.md §3` the script needs to:

1. Verify author file: UTF-8, [5, 50] verses, all-Arabic letters, SHA-256 logged.
2. Skeletonise to `letters_28` (re-uses `src/features.py::skeletonise`).
3. Compute 5-D Φ_M features (re-uses `src/features.py::features_5d`).
4. Compute T1 = 0.5 × Hotelling-T² of (forgery 5-D) vs locked Σ from expP7.
5. Compute T2 = log(p_max_verse_final / (1/28)) on forgery's verse-final letters.
6. Compute T3 = log(EL_AUC_forgery / 0.5) — single-text-vs-pool ROC. **Honest constraint**: with a single forgery surah the AUC is degenerate; protocol states T3 is computed by treating the forgery's EL value as a one-element class against the 4,719-unit Arabic peer pool (if forgery's EL > pool 95th percentile, AUC ≈ 1; else 0.5). This is by-design over-generous to the forgery (i.e., conservative for the project).
7. Compute T4 = log(EL_frag_forgery / pool_median).
8. Compute T5 = log(1/FPR_upper) iff forgery passes the F55 detector (bigram-shift Δ ≤ 2.0 from Quran-canonical AND Δ > 2.0 from every Arabic peer); else T5 = 0.
9. Skip T6 (5-riwayat unavailable).
10. Output: `Φ_master_human = T1+T2+T3+T4+T5` per author + verdict per `HUMAN_FORGERY_PROTOCOL.md §4`.

**Estimated implementation time**: ~6–8 hours of focused development, since 90 % of the code already exists in `experiments/exp96a_phi_master/run.py`. The new code is the file-validator and the per-author harness; the scoring math is unchanged.

**Test it BEFORE opening recruitment** by computing `Φ_master_human` on:
- The Quran itself (should reproduce the locked 1,858.96 nats sans T6).
- The first chapter of `Maqamat al-Hariri` (the project's locked Arabic-saj' control; expected to score ~25 nats per `exp95p_maqamat_hariri_v2`).
- A trivial randomly-shuffled-Quran-words baseline (expected to score ~0 nats).

These three sanity checks bound the script's behaviour before any human author sees it.

---

## 3. Timeline (calendar weeks)

| Phase | Activity | Owner | Calendar weeks |
|---|---|---|---|
| 5.0 | PREREG drafted + hash-locked + scoring script + sanity checks pass | PI | 2 |
| 5.1 | Recruitment opens + author contracts negotiated | PI | 4 |
| 5.2 | Authors compose (parallel; loose deadlines) | Authors | 8–16 |
| 5.3 | Submissions received + scored under PREREG | PI | 1 |
| 5.4 | Verdict published + PAPER amended | PI | 2 |
| **Total** | | | **17–25 calendar weeks** (~ 4–6 months) |

---

## 4. Outcome scenarios and what the project does

### 4.1 STRONG_PROJECT_CONFIRMATION (all authors < 100 nats)
**Probability the project's modal-prior puts on this**: ~30 %.
**Action**: PAPER §4.46.6 sentence is upgraded by replacing "tested vs naturally-occurring Arabic prose" with "tested vs naturally-occurring Arabic prose AND best-effort deliberate human forgery from N Tier-A authors with full formula disclosure." The headline BF figure is unchanged.

### 4.2 MODERATE / PARTIAL_NULL (some authors in [100, 1500] nats range)
**Probability**: ~50 %.
**Action**: PAPER §4.46.6 carries an honest caveat: "best deliberate human author achieves Φ_master = X nats, materially closer to the Quran than any naturally-occurring corpus, but still below the Quran's value by a factor of [Y]× / BF ratio [Z]." The project headline survives but is more nuanced.

### 4.3 WEAKENED_PROJECT_CLAIM (any author ≥ 1500 nats)
**Probability**: ~20 % (low but non-trivial — humans with full disclosure CAN do extraordinary things).
**Action**: PAPER §4.46.6 is **substantially amended**. The "BF > 10⁶⁵¹ vs ordinary Arabic" sentence is preserved (unchanged); the *uniqueness* sentence is replaced with: "Φ_master is achievable by a deliberate human author with full formula disclosure and N hours of effort; the Φ_master value is a structural property of saj'-trained Arabic-literary maximally-optimised text, not a unique feature of canonical scripture." The project's locked findings are preserved as **descriptive structural fingerprints**, NOT as **uniqueness claims**.

This third outcome is **a successful outcome of the project's honesty stance**, not a project failure. The PAPER, RANKED_FINDINGS, and PROGRESS docs all explicitly commit to publishing FAIL outcomes (R-rows, FN-rows, Section 5 non-reproductions). Phase 5's WEAKENED outcome would be added as an honest non-reproduction at the highest level.

### 4.4 NULL_AUTHORSHIP (no author submits anything by deadline)
**Probability**: ~5 %.
**Action**: project records the recruitment attempt; PAPER continues to carry the existing caveat unchanged. Future Phase 5.5 can re-attempt with different recruitment channels.

---

## 5. Critical pre-commitments (must be in the PREREG before authors are contacted)

1. **All author submissions will be published verbatim** with author's preferred name and a SHA-256 fingerprint, regardless of outcome. Submitted at OSF.
2. **Cascade / project authors will not score any submission until ALL submissions are received** (avoids early-result leakage to later authors).
3. **No author file is silently revised by authors after submission**. SHA-256 lock at receipt time.
4. **The verdict ladder cannot be amended after the first author file is received**. Only before recruitment opens.
5. **A FAIL outcome is published in the next PAPER revision** (PI commits in writing). No drawer-effect publication bias permitted.

---

## 6. Open questions for the human researcher

1. Does the PI have an institutional affiliation that gives access to a free IRB? If yes, that's the cleanest path. If not, contract / commission model is recommended.
2. What's the funding source for author honoraria? $2,500–$8,000 is a non-trivial sum; needs to come from somewhere.
3. Should authors be told that other authors are also being recruited? Pro: full transparency. Con: may chill submissions if competitive framing is uncomfortable.
4. Should the project commit to running Phase 5.5 (a second cohort) if Phase 5 returns NULL_AUTHORSHIP? This is a consideration for the authors who DO submit — they may want to know they're contributing to a project that will replicate.

---

## 7. Cross-references

- **Protocol scaffolding (what to measure)**: `docs/reference/HUMAN_FORGERY_PROTOCOL.md`
- **Φ_master headline**: `PAPER §4.46.6`, `HYPOTHESES_AND_TESTS.md` H49, `experiments/exp96a_phi_master/PREREG.md`
- **Robustness scaffolding (LOCO + bootstrap)**: `experiments/exp96b_bayes_factor/`
- **Adversarial-machine baseline**: `experiments/exp99_adversarial_complexity/`
- **Self-description meta-finding**: `experiments/exp96c_F57_meta/`, H51
- **Audit infrastructure**: `scripts/integrity_audit.py`, `scripts/zero_trust_audit.py`
- **Submission readiness**: `docs/reference/SUBMISSION_READINESS_2026-04-25.md` (Phase 5 is identified there as Package P3)
