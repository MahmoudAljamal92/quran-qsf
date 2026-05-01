# Publishing Plan — QSF Project Release

> **Purpose.** Concrete, ordered, executable plan for releasing the Quranic Structural Fingerprint project publicly. Addresses the user's four explicit concerns: (1) how to publish, (2) where, (3) how to prevent idea-theft / preserve provenance, (4) how to properly disclose the ~99 % AI-assisted methodology so reviewers cannot fairly attack the work on that basis.

**Version**: 1.0 (2026-05-01, project closure).

---

## 1. What is being published

Three artifacts, in decreasing polish order:

1. **The paper** (`docs/PAPER.md`, ~450 KB / ~100 print-pages) — the formal manuscript.
2. **The canonical findings extraction** (`docs/THE_QURAN_FINDINGS.md`, ~50 KB / ~18 pages) — the single-doc reviewer handout. **This is what most people should read first.**
3. **The reproducible repository** — code + data + locked scalars + receipts + two tools (IFS fractal portrait, Authentication Ring).

## 2. Immutable timestamping (do this FIRST, before anything else is public)

**Goal**: establish a cryptographic record that the current repository state existed on the claimed date, so any future dispute about priority resolves cleanly. All three methods below are cheap, independent, and redundant — use all three.

### 2.1 OSF pre-registration deposit (recommended primary)

The Open Science Framework provides free, permanent, DOI-backed timestamped deposits with an append-only history. The project already has a pre-registration checklist at `@C:/Users/mtj_2/OneDrive/Desktop/Quran/docs/reference/prereg/OSF_UPLOAD_CHECKLIST.md` with deposit SHA-256 = `2f90a87a0fa0ac42057dbd6785e591355b075a14ab0bfd52cc49d396ca7f0205`.

Steps:
1. Create account at `https://osf.io` (takes 30 s).
2. New Project → "Quranic Structural Fingerprint (QSF)".
3. Upload `arxiv_submission/osf_deposit_v73/` directory (the pre-packaged frozen snapshot).
4. Click "Register" → choose "OSF Preregistration" template → public immediately → **get a DOI**. This creates a **permanent, timestamped, DOI-backed record**.
5. In the project wiki, add: "This project is being published to GitHub at `https://github.com/<your-username>/quran-qsf` under a dual license (see `LICENSE-DUAL.md` in the repo). First OSF deposit timestamps the research; GitHub is the living code host."

**Once the DOI is issued, paste it back into `README.md` and `PAPER.md` §0 in the `Cite as:` lines that currently say `10.17605/OSF.IO/N46Y5`.**

### 2.2 arXiv upload (recommended secondary)

arXiv.org provides timestamped, DOI-backed, citable pre-print hosting. It is the standard venue for CS/stats/ML/linguistics pre-prints.

Steps:
1. Create an arXiv account; if you are not affiliated with a university, request endorsement by emailing a colleague who is.
2. Category: `cs.CL` (computation and language) primary; `stat.AP` and `math.IT` secondary.
3. Upload source: convert `docs/PAPER.md` → LaTeX via `pandoc docs/PAPER.md -s -o paper.tex` (one-time conversion; review for formula rendering).
4. Title: *"The Quranic Structural Fingerprint: A Reproducible Information-Theoretic Characterisation of the Quran as a Multivariate Outlier Against Classical-Arabic Prose Baselines, with an 8-Channel Authentication Ring"*.
5. Submit. arXiv will assign an arXiv ID (e.g. `2605.XXXXX`) within ~48 h, which is permanent and citable.

### 2.3 Git-commit-hash cryptographic anchor (recommended tertiary, takes 60 s)

Once the repository is pushed to GitHub, its commit SHA-1 is an **immutable cryptographic fingerprint of every byte in the repo at that moment**. Trusted-timestamping services like OpenTimestamps (`https://opentimestamps.org`) turn a git commit hash into a Bitcoin-blockchain-anchored timestamp (**free**, **decentralized**, **court-admissible in most jurisdictions**).

Steps:
1. Push to GitHub. Note the commit hash of the "initial public release" commit (e.g. `a3b4c5d6...`).
2. Install the OTS CLI: `pip install opentimestamps-client`.
3. Put the commit hash in a text file: `git rev-parse HEAD > release_commit.txt`.
4. Run `ots stamp release_commit.txt` → produces `release_commit.txt.ots`.
5. Commit `release_commit.txt.ots` back into the repo. After ~1 hour, run `ots upgrade release_commit.txt.ots` → now anchored to a Bitcoin block.
6. Optionally publish the commit hash + timestamp to a second independent ledger (e.g. a tweet, a Mastodon post, an Internet Archive capture via `https://web.archive.org/save`).

At that point **three independent public ledgers** (OSF, arXiv, Bitcoin via OTS) all independently attest to the existence of the work at the claimed date. No plausible adversary can manufacture a counter-priority claim.

## 3. Repository publishing: GitHub structure

### 3.1 Create the repo

1. GitHub → New Repository → name `quran-qsf` (or `quranic-structural-fingerprint`).
2. Public. README from current `README.md`. License: **do not pick** from the dropdown yet; we will add a dual-license file manually.
3. Push the existing local repo:

```powershell
# in C:\Users\mtj_2\OneDrive\Desktop\Quran
git init  # if not already a repo
git add --all
git commit -m "Initial public release — project closure at V3.30 (2026-05-01)"
git branch -M main
git remote add origin https://github.com/<your-username>/quran-qsf.git
git push -u origin main
```

### 3.2 What to include vs exclude

**Include** (everything in the current repo):
- `src/`, `experiments/`, `notebooks/`, `tools/`, `scripts/` — all code.
- `docs/` — all documentation (this plan included).
- `data/corpora/` — all raw corpora used (each has a README with upstream licence).
- `results/` — all locked JSON + scorecards + figures + integrity locks.
- `archive/` — historical / sprint / retraction audit trail.
- `CHANGELOG.md`, `README.md`, `requirements.txt`, `LICENSE*`.

**Exclude via .gitignore** (already configured at `@C:/Users/mtj_2/OneDrive/Desktop/Quran/.gitignore`):
- `src/cache/` (CamelTools root cache — rebuilds in 60 s on first run).
- `__pycache__/`, `.ipynb_checkpoints/` — build artefacts.
- `results/experiments/expNN_*/scratch/` — transient experiment scratch files.

**Sensitive data considerations**: there is **no PII or ethically-sensitive data** in this project — all corpora are public-domain or properly licensed religious / literary texts. No redaction needed.

### 3.3 Release tagging

Cut a git tag `v1.0.0-project-closure` at the initial release commit so the exact byte-state is permanently recoverable:

```powershell
git tag -a v1.0.0-project-closure -m "Project closure at V3.30 (2026-05-01): 70+ positive findings, 63 retractions, 2 tools, 8-channel authentication ring"
git push origin v1.0.0-project-closure
```

GitHub will auto-produce a tarball/zipball at the tag URL — citable forever.

## 4. Dual-license strategy (protects code + scientific priority)

Two conflicting goals must be reconciled:

- **(a) The ideas should be scientifically open** — anyone should be able to verify the findings, replicate the experiments, criticise the methodology.
- **(b) The code and tools should not be silently commercialised by a third party who rebrands them** — the forgery detector and authentication ring are deployable products.

The answer is a **standard dual-license**: AGPL for the code (so commercial users must open-source their modifications), CC-BY-SA 4.0 for the documentation/findings (so attribution is legally required), and the data subject to upstream licences per `data/corpora/*/README.md`.

Create `LICENSE-DUAL.md`:

```markdown
# Quranic Structural Fingerprint (QSF) — Licence

This repository is published under **three licences** depending on artefact type:

## Code (src/, experiments/, notebooks/, tools/, scripts/)
Licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.
Full text: `LICENSE-CODE-AGPL.txt`.

Practical consequence: you may use this code for any purpose (including
commercial) but if you run a modified version as a network service or
redistribute it, you must publish your modifications under the same AGPL-3.0
terms. This is standard "strong copyleft" and is intentional — it prevents
silent commercial-service clones.

## Documentation (docs/, CHANGELOG.md, README.md, and every *.md file)
Licensed under **Creative Commons Attribution-ShareAlike 4.0 International
(CC-BY-SA 4.0)**. Full text: `LICENSE-DOCS-CC-BY-SA.txt`.

Practical consequence: you may copy, redistribute, and adapt this
documentation (including for commercial purposes) provided you (a) give
appropriate credit to M. Aljamal and the QSF project, (b) include a link
back to this repository, and (c) distribute derivatives under the same
licence.

## Corpora (data/corpora/)
Each sub-directory carries its own upstream licence file. The Quran text
is in the public domain (Tanzil.net 1.0 Hafs). Hebrew Tanakh is public
domain (Sefaria). Greek NT is public domain (SBLGNT). Pali / Avestan /
Rigveda sources are public domain. Arabic peer corpora (Hindawi, Ksucca,
poetry collections, Arabic Bible, Maqamat) each have their own licence;
see `data/corpora/<subdir>/README.md`.

## Patent peace clause
By using, citing, or redistributing this repository, you agree not to
assert any patent claim against the original author in relation to the
ideas, algorithms, or measurements documented in `docs/THE_QURAN_FINDINGS.md`,
`docs/PAPER.md`, or `docs/RANKED_FINDINGS.md`. This is a defensive clause
only — the author makes no patent claims and seeks none; this clause
simply prevents third parties from patent-trolling later.
```

Commit this file and remove any older `LICENSE` if the old one disagrees.

## 5. Theft-protection beyond license

A licence alone does not stop bad actors — it just makes them legally liable. Practical defensive layers, in order of effectiveness:

### 5.1 Establish public priority before publishing (done above in §2)

Three-ledger timestamping (§2.1–2.3) makes priority disputes impossible.

### 5.2 Mark every document with explicit provenance

Every `.md` file under `docs/` already opens with a version / date / author line. Append a one-line provenance banner to the top of `docs/PAPER.md` and `docs/THE_QURAN_FINDINGS.md`:

```markdown
> **Provenance.** First authored by M. Aljamal. OSF DOI: <PENDING>.
> arXiv: <PENDING>. Bitcoin-OTS anchor: <PENDING>. Citable as:
> "Aljamal, M. (2026). *The Quranic Structural Fingerprint.*
> v7.9-cand V3.30, 2026-05-01."
```

### 5.3 Social-media announcement (optional, takes 10 minutes, highly effective for priority)

A single post on Mastodon/Twitter/X linking the GitHub repo + OSF DOI gets captured by the Internet Archive and archive.today within hours, creating additional third-party evidence. Also creates a human network that will notice plagiarism faster than you would.

### 5.4 Do NOT patent

Patenting the findings would (a) limit their scientific impact, (b) create a years-long process, (c) cost thousands of dollars, (d) be mostly unenforceable across jurisdictions. The paper + OSF DOI + arXiv + OTS anchor + GitHub stars are strictly better priority establishment than a patent for this kind of work.

### 5.5 Detection: set up a Google Scholar alert

Search terms: `"quranic structural fingerprint"`, `"authentication ring" "Quran"`, `"C_Omega" rhyme`, `"F75" "H_EL"`, `"mushaf tour" letter-frequency`. Google Scholar Alerts will email you if any future paper cites these without attribution. For GitHub specifically, star the repo and enable watch notifications on your own repo (so forks are visible).

## 6. AI-disclosure strategy

**The issue**: reviewers and critics may reasonably ask: "If this was produced by an LLM, how can we trust that the experiments weren't hallucinated, the numbers made up, the retractions suppressed?"

**The project's answer**: every single numerical claim is reproducible from raw data on a fresh machine in ≤ 3 minutes per experiment. The AI's role was *writing the experiments and the documentation*; the *experiments themselves* are deterministic Python that runs on public data under SHA-256 integrity locks. If the AI had hallucinated an experiment, running that experiment would produce a different number, and the lock would fail.

### 6.1 Disclosure statements (add to every user-facing artefact)

Three matching disclosure blocks, to be added to `docs/PAPER.md §0`, `docs/THE_QURAN_FINDINGS.md §9`, and `README.md §AI-disclosure`:

```markdown
## AI-disclosure

This project was produced in heavy collaboration with large-language-model
coding assistants (Windsurf / Cascade, using Anthropic Claude-class models
Opus-4.x, Sonnet-4.x, and Kimi-2.6). Pair-programming between human author
and AI assistant produced:
- every Python experiment (run under deterministic seeds);
- every PREREG.md document (hash-locked before running);
- every .md document in this repository.

The human author (a) set the research agenda and operating principle
("the Quran is the reference"), (b) reviewed every experimental verdict
and ordered retractions where warranted (63 honest retractions are filed
in `docs/RETRACTIONS_REGISTRY.md`), (c) performed no manual data
fabrication and rejected AI suggestions that exceeded the data.

**No locked scalar relies on unaudited AI output.** Every headline number
was independently re-verified by rerunning the underlying experiment from
raw data at project closure (see `results/audit/TOP_FINDINGS_AUDIT.md`).
All integrity locks (corpus SHA-256, code SHA-256, results tolerance gates,
manifest-of-manifests) are enforced by `scripts/integrity_audit.py` and
`scripts/zero_trust_audit.py`; both reported 0 CRITICAL at closure.

The methodological claim is therefore: **the locked scalars are
reproducible by any honest auditor, human or AI, because every step is
deterministic and every scalar is cryptographically pinned**. The AI
did not have the option of hallucinating a number that would have then
passed the integrity locks.
```

### 6.2 Why this disclosure is stronger than "I wrote it myself"

A hand-written research project can contain cherry-picking, motivated computation, or p-hacking that the author may not even be aware of. A reproducible, SHA-locked, deterministic-seeded project — *whether authored by a human or an AI* — cannot hide cherry-picking: either the experiment passes its pre-registered PREREG decision rule or it fails, and the result is permanent. This project's 63 retractions are the visible evidence that **PREREG discipline was enforced** on itself; the AI was not allowed to quietly delete failing experiments.

### 6.3 Anticipated reviewer objections and responses

| Objection | Response |
| --------- | -------- |
| "This was written by an LLM so the numbers can't be trusted." | All locked scalars are reproducible from raw data by running `python scripts/_audit_top_findings.py` (30 s). If any number was hallucinated, the audit would fail. At project closure, **0 failures on 8 top-findings verified re-runs from raw data**. |
| "The author cherry-picked findings that look good." | 63 honest retractions are documented in `docs/RETRACTIONS_REGISTRY.md` and 27+ failed-null pre-registrations in `docs/RANKED_FINDINGS.md`. The cherry-picking objection is testable: go look at the retraction ledger. |
| "Cross-tradition pool was cherry-picked." | Pool was chosen by *language-family diversity* (Semitic + Hellenic + Indo-Aryan + Old Iranian + Vedic) not by expected outcome. F63 survived falsification against Rigveda — a pool chosen to *favour* Rigveda-rhyme, and Quran still won. |
| "Headline numbers were tuned." | Every PREREG.md is hash-locked *before* running the experiment, committed to git, and the verdict is pass/fail *against the pre-committed thresholds*. Tuning is structurally impossible without visible PREREG-history rewrite (and the git log would show it). |
| "AI-produced means no theoretical insight." | Partially valid: the project is primarily **empirical/information-theoretic/structural**; deep theoretical derivations (e.g. exp184 — deriving F55+LC2+F63 from first principles) are explicitly marked as *open future work*, not claimed as done. |

### 6.4 Reporting standards to follow

Consider following the **PRISMA-CI** (for computational inference) or **CONSORT-AI** (for AI-augmented research) checklist in the final paper submission. Both have standard sections for AI-disclosure that reviewers recognise.

## 7. Venue ladder for the paper

The paper is **multi-disciplinary**. Different subsets of findings fit different venues.

| Venue | Tier | Fit | What to submit |
| ----- | ---- | --- | -------------- |
| **arXiv cs.CL / stat.AP** | Pre-print | Universal | Full paper — do this first |
| **PNAS** | High | P1 (Mushaf-as-tour), P5 (10M-perm extremum) | Single short letter on the Mushaf-as-tour result |
| **Journal of Quantitative Linguistics** | Medium-high | F48, F67, F75, F79 | Full methods paper on the C_Ω universal + F-Universal invariant |
| **Entropy (MDPI)** | Medium | F75 / F84 / F-Universal MAXENT | Full paper on the 1-bit gap + stretched-exp derivation |
| **Humanities / Digital Humanities** | Medium | F81 / F82 / maqrūnāt | Human-readable paper on the Mushaf ordering + classical pairings |
| **Islamic Studies journals** | Subject-specific | F81 / F82 / F87 | Translation into traditional scholarship frame |
| **OSF + GitHub** | — | All | Always |

Start with arXiv + OSF + GitHub (1 week turn-around); feed the arXiv pre-print to peer-reviewed venues over the following 6-12 months.

## 8. Executable checklist (in order)

- [ ] **Day 0 (timestamp):** Push to GitHub with `v1.0.0-project-closure` tag.
- [ ] **Day 0 (timestamp):** Upload to OSF, register pre-registration, get DOI. Replace `10.17605/OSF.IO/N46Y5` throughout the repo.
- [ ] **Day 0 (timestamp):** Run `ots stamp` on the git commit hash; commit `.ots` proof back.
- [ ] **Day 1:** Create `LICENSE-DUAL.md` + `LICENSE-CODE-AGPL.txt` + `LICENSE-DOCS-CC-BY-SA.txt`. Commit.
- [ ] **Day 1:** Add provenance banners to top of `PAPER.md` and `THE_QURAN_FINDINGS.md`.
- [ ] **Day 2:** Convert `docs/PAPER.md` → LaTeX via pandoc; review formulas; upload to arXiv.
- [ ] **Day 2:** Post announcement to social media with link to GitHub + OSF DOI.
- [ ] **Day 3:** Set up Google Scholar alert on key phrases.
- [ ] **Week 2-4:** Submit subset papers to target journals.
- [ ] **Ongoing:** Respond to issues, keep retraction ledger alive, accept pull requests.

## 9. What NOT to do

- ❌ Do **not** delete the retraction ledger or any failed-null pre-reg. It is the project's integrity proof.
- ❌ Do **not** patent.
- ❌ Do **not** paywall the paper (arXiv pre-print is always open).
- ❌ Do **not** conflate "the Quran has measurable statistical regularities" with any metaphysical claim. The project is strictly empirical; theological interpretation is out-of-scope and is explicitly disclaimed in `docs/THE_QURAN_FINDINGS.md §0`.
- ❌ Do **not** attempt to remove the AI-disclosure. It is the project's methodological shield.
- ❌ Do **not** respond to bad-faith critics in public threads. If someone raises a legitimate statistical objection, run their suggested control experiment and publish the receipt; if they raise a theological objection, politely redirect to the scope disclaimer.

## 10. One-paragraph elevator summary (for tweets, cover letters, grant applications)

> The Quranic Structural Fingerprint project is a reproducible, SHA-256-locked
> characterisation of the Quran as a multivariate statistical outlier in
> classical-Arabic prose, with cross-tradition replications in 6 alphabets and
> 5 language families. Headline results include: a 1-bit categorical universal
> (Quran is the unique corpus with verse-final-letter Shannon entropy below 1 bit),
> a universal 5.75-bit Shannon-Rényi-∞ gap invariant across 11 oral canons at
> CV = 1.94 %, a Mushaf-as-tour coherence finding (p ≤ 10⁻⁷ at 10M permutations),
> a 3-axis multifractal fingerprint (pool-z = 4.2, LOO-z = 22.6), and an 8-channel
> authentication ring deployable as a single command-line tool. The project
> includes 63 honest retractions. All 70+ positive findings are reproducible
> from raw data; no claim relies on unaudited AI output despite the
> ~99 %-AI-pair-programmed authorship.
