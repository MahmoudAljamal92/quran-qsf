# 05 — Decisions and Blockers

**Direct answers** to the user's open questions, plus a complete tracker of every decision and external blocker on the critical path. Each row has an explicit "do this / don't do this" recommendation.

---

## Q1 — §4.4 T_alt decision — RESOLVED (C1 LOCKED 2026-04-25 evening)

**Decision**: **C1 — Keep T_canon as canonical** (locked 2026-04-25, UTC+02). T_alt becomes the headline of P7 (atomic methodology paper); `results_lock.json` is unchanged; Φ_M = 3 557 / ~47σ-equivalent remains the v7.7+ headline.

**Why C1**: at Φ_M ≈ 47σ-equivalent, the +1.33σ refinement to 48.36σ is statistically inert for any reviewer (both numbers are ~10× above the particle-physics 5σ discovery threshold). C1 unblocks P2 + P7 writing immediately with zero `results_lock.json` churn. T_alt's value is preserved as the headline of P7 (CamelTools-free single-feature methodology paper to *PLOS ONE*).

**Reopen rule**: revisit only if the project re-targets from Option A/C (5 atomic papers / Hybrid) to Option B (single PRX / TIT / PNAS umbrella paper). Bookkeeping cost of migration to C2: ~1–2 days.

**The remainder of this section is preserved as a decision record for audit purposes.**

### What §4.4 actually decided

§4.4 of `SUBMISSION_READINESS_2026-04-25.md` resolved a 3-way choice for the canonical T definition:

| Choice | What it means | Verdict |
|---|---|---|
| **C1 — Keep T_canon** | All papers cite Φ_M = 3 557 / 47.03σ ; T_alt becomes a P7 standalone supplementary | ✅ **CHOSEN 2026-04-25** |
| **C2 — Promote T_alt at Band-A** | New headline Φ_M_Band-A = 3 868 / 48.36σ ; T_canon retained for Band-C ; lock + downstream JSON updates | ❌ NOT TAKEN ; reopen iff Option B / PRX / TIT / PNAS becomes the target |
| **C3 — Length-adaptive blend** | Define `α(n)·T_alt + (1−α(n))·T_canon` ; new locked scalar | ❌ DEFERRED to a follow-up P8 methodology paper |

### Significance analysis (the user's actual question)

The honest delta:

| Metric | T_canon | T_alt | Δ |
|---|--:|--:|--:|
| Hotelling T² (Band-A) | 3 557 | 3 868 | +8.7 % |
| log10 p_F (mpmath 80-dps) | −480.25 | −507.80 | −27.55 |
| σ-equivalent | ~47.03 σ | ~48.36 σ | **+1.33 σ** |

**At p ≈ 10⁻⁴⁸⁰, going to 10⁻⁵⁰⁷ is statistically meaningless** — both are ~100× the particle-physics 5σ discovery threshold (which is at p ≈ 10⁻⁷). The difference matters for **venue optics**, not for science:

- **Option A (5 atomic papers, *PLOS ONE* / *Entropy* / *Computational Linguistics*)** — reviewer doesn't care about +1.33σ; both numbers are equally "obviously significant". **Pick C1, save the bookkeeping cost.**
- **Option B (one combined paper to *PRX Information* / *IEEE TIT*)** — reviewer optics matter; the +1.33σ is a real refinement that closes the "CamelTools-dependent" reviewer objection. **Pick C2, accept the 1-2 day bookkeeping cost.**
- **PNAS stretch (with P4 cross-tradition headline)** — same as Option B; pick C2.

### Recommendation (preserved for audit)

The project default at decision time was Option C (Hybrid) without committed Option B targeting; under that default C1 was the right pick. C1 was chosen 2026-04-25 evening.

### Bottom line

> **§4.4 T_alt decision is now closed**. C1 is locked. P2 + P7 writing is unblocked. T_alt feeds P7 only ; P2/P3 keep Φ_M = 3 557 as canonical. Decision is reversible by user if Option B / PRX / TIT / PNAS becomes the explicit target later.

---

## Q2 — Do I still need to do OSF pre-registration upload (15 min)?

**Short answer**: **YES. This is the single highest-ROI external action remaining. Do it before any submission.**

### Why it matters

Currently every paper draft says "Pre-registration: `OSF_DOI_PENDING`" with the deposit SHA `2f90a87a0fa0ac42057dbd6785e591355b075a14ab0bfd52cc49d396ca7f0205` referencing `arxiv_submission/osf_deposit_v73/qsf_v73_deposit.zip`. **Without an actual OSF DOI**, the pre-registration claim is paper-internal only — reviewers at *PRX* / *PNAS* / *Entropy* / *PLOS ONE* will flag this as a credibility risk.

The deposit zip is already prepared. The procedure is in `docs/reference/prereg/OSF_UPLOAD_CHECKLIST.md`. The action is literally:

1. Create OSF account (if not already).
2. Upload the zip.
3. Get the DOI.
4. Replace `OSF_DOI_PENDING` with the real DOI in `PAPER.md`.

### ROI analysis

Per `RANKED_FINDINGS.md §6 immediate item 1`: this **moves RSOS-grade from 88 % → 94 %** for a 15-minute action. There is no other 15-minute action in the project with a 6-percentage-point acceptance lift.

It also **unblocks P3 submission** to *PLOS ONE* (which checks pre-reg DOIs in their automated submission gate) and unblocks the "submission-ready" status of all 5 publishable packages per `SUBMISSION_READINESS_2026-04-25.md` Bottom-line table.

### Recommendation

> **DO IT TODAY.** Highest ROI of any remaining task. 15 minutes of admin → 6 percentage points of acceptance probability across 5 papers. No downside.

---

## Q3 — Other live blockers (full tracker)

| ID | Blocker | Owner | Time | Unblocks | Recommendation |
|---|---|---|---:|---|---|
| ~~Z1~~ | ~~§4.4 T_alt C1/C2/C3~~ | ~~user~~ | ~~5 min~~ | P2 + P7 writing | **RESOLVED 2026-04-25 evening: C1 LOCKED**. P2 + P7 writing now unblocked. |
| **Z2** | OSF pre-registration upload | user | 15 min | P3 submission ; promotes RSOS-grade 88→94 % | **DO IT NOW** |
| **Z3** | Riwayat data (Warsh / Qalun / Duri) | user / external | 0 min admin once data on disk ; 15 min runtime | P6 (riwayat invariance) | Acquire from `tanzil.net` in `S\|V\|text` format ; place at `data/corpora/ar/quran_{warsh,qalun,duri}.txt` |
| **Z4** | Two-team external replication | external coordination | 2-4 weeks | every "law" claim upgrades to externally-validated | Required for PRX / IEEE TIT / PNAS stretch ; not required for Entropy / PLOS ONE / Comp. Ling. |
| **Z5** | Ψ_oral formula from reviewer | external | unknown | (closed 2026-04-25 via own-derivation + falsification) | **Now resolved** — formula was found in own docs ; ran `expX1_psi_oral` ; falsified ; no further action |
| **Z6** | git commit of audit patches | user | 5 min (Option A) / 15 min (Option B) | version-control durability | **⚠ Topology issue discovered 2026-04-25 evening**: `.git` lives at `C:\Users\mtj_2\OneDrive\Desktop\` (parent), **not** at the Quran project root. Running `git add -A` from anywhere inside Quran/ would commit the user's entire Desktop (Cover Letter.docx, Games/, Softwares/, MS Office lock files, …). **Two safe paths** — see audit `A11` and the inline notes below this table. |

### Z6 detail — git topology and safe commit options

**Verified 2026-04-25 evening** (`git -C "...\Quran" rev-parse --show-toplevel` → `C:/Users/mtj_2/OneDrive/Desktop`; `Test-Path "...\Quran\.git"` → False; `Test-Path "...\Desktop\.git"` → True).

**What this means**: today, the user's Desktop is one big un-committed git working tree with **zero commits**, and `Quran/` is just one untracked subfolder among ~19 unrelated personal items (BIM MODELER/, Games/, Cover Letter.docx, ~$\* Office lock files, etc.). The recommendation that previously read `git add -A && git commit ...` would have ingested all of that on the first commit.

#### Option A — Re-init a clean repo at the project root **(recommended, ~5 min)**

```powershell
# 1. Convince yourself nothing in Desktop\.git was important (no commits exist anyway):
git -C "C:\Users\mtj_2\OneDrive\Desktop" log --oneline -n 5
# (expect: "fatal: your current branch 'master' does not have any commits yet")

# 2. Remove the parent .git so it stops shadowing the project:
Remove-Item -Recurse -Force "C:\Users\mtj_2\OneDrive\Desktop\.git"

# 3. Init fresh inside the project:
git init "C:\Users\mtj_2\OneDrive\Desktop\Quran"
git -C "C:\Users\mtj_2\OneDrive\Desktop\Quran" add .
git -C "C:\Users\mtj_2\OneDrive\Desktop\Quran" commit -m "QSF v7.7 + audit 2026-04-24/25 + §4.4 LOCKED C1"
```

This is safe because the parent repo had **zero commits** (no history to lose). After this, `Quran/` is a self-contained git repo with a single initial commit.

#### Option B — Keep parent repo, scope commits to `Quran/` only (~15 min, fragile)

```powershell
# From Desktop, only stage the Quran subtree:
git -C "C:\Users\mtj_2\OneDrive\Desktop" add Quran
git -C "C:\Users\mtj_2\OneDrive\Desktop" commit -m "QSF v7.7 + audit 2026-04-24/25 + §4.4 LOCKED C1"
```

**Caveat**: every future commit from inside `Quran/` will have to remember to scope to `Quran/` only, or the user's entire Desktop will pour into the next commit. **This is fragile and not recommended unless the user has a specific reason to keep the Desktop-rooted repo.**

#### Recommendation

> **Pick Option A.** No history is lost (parent has zero commits), the resulting topology is what every other doc in the project assumes (`docs/reference/...` paths are project-relative), and a fresh `Quran/.git` makes future audit cycles trivially safe. Total time: 5 minutes including verification.

---

## Q4 — The five publishable packages and their ship-now status (post cross-tradition phase)

| ID | Package | Locked scalars | Blocker | Recommendation |
|---|---|---|---|---|
| **P1** | Abrahamic-script diacritic typology (was "universal") | R ∈ [0.55, 0.70] for Arabic/Hebrew/Greek; Devanagari R = 0.918; Latin R = 0.20 | Writing only (reframe from "universal" → "typology") | Submit to *Computational Linguistics* in 4-6 weeks |
| **P2** | Quran geometric-info-theoretic theorem | X6 GIT p ≈ 2.9·10⁻¹³; X3 prose-extremum p ≈ 6.7·10⁻³⁴; A10 J1 p < 10⁻⁶; D7 juzʾ q = 0.002; A3 STOT 4/5 PASS | Writing only (§4.4 LOCKED C1 2026-04-25 ; Φ_M = 3 557 canonical) | Submit to *Entropy* (~95 % accept) or *PRX Inf* (~70-80 % accept post X7) |
| **P3** | LC3-70-U single-feature classifier (EL-monovariate) | AUC 0.9975; 7/2509 leaks all from arabic_bible | OSF DOI + writing | Submit to *PLOS ONE* in 2-3 weeks |
| **P4** | Cross-tradition extension (Vedic + Avestan + Pali) | LC2 R3 SUPPORT + LOO 8/8; A2 R = typology not universal | Writing only (8 experiments executed 2026-04-25) | Submit to *Language* (with re-framed headline) ; PNAS stretch with P2 |
| **P5** | Ψ_oral cross-corpus measurement | NO_SUPPORT (cross-corpus spread 0–26) | (no submission) | n=1 numerical coincidence ; not publishable |
| **P7** | T_alt methodology refinement (NEW from X7 P2_OP2) | Φ_M 3 557 → 3 868 (+8.7 %); +1.33σ at Band-A; FAILS at Band-C | Writing only (§4.4 LOCKED C1 2026-04-25 ; T_alt is P7 headline) | Submit to *PLOS ONE* methodology in 2-3 weeks |
| **P6** | Riwayat invariance | – | Z3 data | 6+ months out (data-blocked) |

---

## Q5 — One-hour user todo (if you only have one hour)

In strict ROI order:

1. ~~**Decide §4.4 T_alt** (5 min)~~ — **DONE 2026-04-25 evening: C1 LOCKED**.
2. **Upload OSF deposit** (15 min) — single highest-ROI external action remaining.
3. **Decide Option A vs B vs C** (5 min) — recommend Option C (Hybrid).
4. **Start P3 outline** (30 min) — fastest venue ; uses one locked scalar (AUC 0.9975) ; it's the dress rehearsal that catches writing-style issues cheaply.
5. **`git commit` the audit + C1-lock patches via Option A** (5 min) — version-control durability for today's work. **⚠ Use the Option A commands in Q3/Z6** (re-init at project root); the older "`git add -A && git commit`" recommendation is a foot-gun because `.git` lives at the Desktop, not the project root. See audit `A11` in `06_CROSS_DOC_AUDIT.md`.

With §4.4 already resolved, steps 2–5 in one sitting move **all five publishable packages from "writing-only" to "submission-ready"** in ~55 minutes.

---

## Q6 — What NOT to do this week

- ❌ Do not start P2 synthesis writing until P3 is submitted (P3 is the dress rehearsal).
- ❌ Do not propose new cross-tradition corpora until LC2 paper is in review.
- ❌ Do not propose a "Ψ_oral re-curation with hand-built per-script rules" — it's well-defined work but not on the critical path.
- ❌ Do not promote any retracted claim from `04_RETRACTIONS_LEDGER.md` without fresh data + fresh methodology.
- ❌ Do not frame any submission around "Quran is unique on every dimension" — the cross-tradition phase falsified that.

---

*Sources: `docs/reference/sprints/SUBMISSION_READINESS_2026-04-25.md §4 + §4.4 + §8`, `docs/reference/sprints/CROSS_TRADITION_FINDINGS_2026-04-25.md §7 + §8`, `docs/reference/findings/RANKED_FINDINGS.md §6`, `arxiv_submission/osf_deposit_v73/`.*
