# Handoff for the Next AI Editor (or Human)

**Last updated**: 2026-05-01
**Project state**: V3.31 PUBLISHED — OSF registered, GitHub live, Streamlit deployed (pending)
**Owner**: Mahmoud Aljamal (`MahmoudAljamal92` on GitHub)

---

## Who are you reading this?

If you are an AI coding assistant (Cascade / Claude / GPT / any other model) opening a new chat
in this workspace, welcome. This doc tells you everything you need to pick up the project
without asking the user 20 questions.

---

## One-paragraph project summary

The Quranic Structural Fingerprint project (QSF) is a frozen, SHA-256-locked computational
study showing that the Quran exhibits a reproducible 8-dimensional information-theoretic
fingerprint (rhyme concentration, verse-ending entropy, fractal complexity, universal
cross-tradition invariant, and 4 others) that distinguishes it from 11 other canonical
scriptures and from a 2,509-unit Arabic peer pool. All findings are cryptographically
reproducible; every PREREG.md is SHA-locked; 66 retractions are filed transparently.
Closure audit re-ran 8 top findings from raw data: 8/8 PASS. Two zero-trust audits return
0 CRITICAL on 214 receipts.

## Publication record (DO NOT BREAK THESE LINKS)

| Artefact | Location | Status |
|---|---|---|
| OSF deposit + DOI | https://doi.org/10.17605/OSF.IO/N46Y5 | PERMANENT, LIVE |
| GitHub repo | https://github.com/MahmoudAljamal92/quran-qsf | LIVE, commit `main` HEAD |
| Streamlit live app | `app/ring_of_truth.py` deployed to Streamlit Cloud | deployed/pending |
| arXiv pre-print | (not yet submitted; awaiting endorsement) | PENDING |
| OpenTimestamps blockchain stamp | (not yet done; optional belt-and-suspenders) | OPTIONAL |

## Standard workflow (memorise this)

For ANY edit — documentation, app, code, experiment — the workflow is:

```powershell
cd C:\Users\mtj_2\OneDrive\Desktop\Quran
git add --all
git commit -m "describe what changed in one short line"
git push
```

Streamlit Cloud auto-rebuilds from `main` after every push; OSF and the DOI are frozen
(immutable); GitHub history is append-only. You cannot lose work by pushing — only by
failing to push.

If `git push` asks for a password, use the user's stored GitHub Personal Access Token.
Windows Credential Manager caches it after the first successful push.

## File layout (high level)

```
Quran/
├── README.md                          user-facing overview
├── docs/
│   ├── PAPER.md                       the formal paper (V3.31)
│   ├── THE_QURAN_FINDINGS.md          single-doc synthesis
│   ├── RANKED_FINDINGS.md             numbered findings F1..F91 + retractions
│   ├── RETRACTIONS_REGISTRY.md        66 honest retractions (append-only)
│   ├── PUBLISHING_PLAN.md             the release checklist
│   ├── CHANGELOG.md                   V1.0 → V3.31 history
│   └── NEXT_AI_HANDOFF.md             ← THIS FILE
├── app/
│   └── ring_of_truth.py               the live Streamlit app (THE user-facing tool)
├── src/                               core feature-extraction library
├── scripts/                           integrity auditors, normalisers, one-off tools
├── experiments/expNN_*/               each experiment with its own PREREG.md
├── data/corpora/                      all input corpora, SHA-256 locked
├── results/                           per-experiment receipts
├── _release/
│   ├── arxiv/                         arXiv-ready .tex + .html
│   ├── osf/                           mirror of docs for OSF upload
│   └── opentimestamps/                Bitcoin-blockchain stamp (optional, not done yet)
└── requirements.txt
```

## Locked scalars (DO NOT change these numbers without running the audit)

| Scalar | Value | Source |
|---|---|---|
| Quran median H_EL (verse-end entropy) | 0.9685 bits | F76 |
| Quran median p_max (dominant end-letter rate) | 0.7273 | F76 |
| Quran C_Ω (rhyme channel util) | 0.7985 | F67 |
| Quran D_max (alphabet gap) | 3.84 bits | F79 |
| Quran F75 invariant | 5.316 bits (pool mean 5.75 ± 0.11) | F75 |
| Quran IFS d_info | 1.667 | F87-linked |
| Hotelling T² (legacy band-A) | 3,557 | V3.22 |
| Cross-val AUC | 0.998 | V3.22 |
| F89 permutation p-value | ≤ 10⁻⁷ (0 / 10⁷ perms) | F89 |
| Mushaf-as-Tour z | −5.14 | F81 |

## Guardrails (what NOT to do)

1. **Do not edit locked Quran reference values** in `app/ring_of_truth.py` (the
   `QURAN_*_REF` constants near the top). They are the published numbers.
2. **Do not silently fix bugs** in experiment receipts — file a retraction in
   `docs/RETRACTIONS_REGISTRY.md` and leave the old receipt in place (append-only).
3. **Do not delete any PREREG.md** — they are part of the scientific record.
4. **Do not bypass the normaliser** (`scripts/_phi_universal_xtrad_sizing.py`) — it is
   SHA-256 locked and applied identically to every corpus.
5. **Do not add any number to a .md file that is not present in a result receipt** — all
   claims must be grounded in a re-runnable experiment.
6. **Do not store API keys, passwords, or tokens in the repo.** The user already had
   one leak (resolved); `.env.example` is the pattern.

## Common edits the user is likely to ask for

### "Change the app's font / colours / layout"
Edit the `<style>...</style>` block near the top of the UI section in
`app/ring_of_truth.py` (around line ~515). Push. Streamlit rebuilds in 2 minutes.

### "Add a new built-in example to the Streamlit app"
Add an entry to `_EXAMPLES` in `app/ring_of_truth.py` (around line ~454). Format:
`_EXAMPLES["key"] = ("Display name", "lang_code", "the raw text...")`. Push.

### "Translate the app UI to Arabic / another language"
Wrap every user-facing string in a simple `_T()` lookup function; add a language
selector in the sidebar. Do NOT translate the internal code comments or the locked
scalar labels.

### "Write a new README / blog post / announcement"
Read `docs/PAPER.md` §0 (AI disclosure) and §Abstract first. Keep the AI disclosure
verbatim in any new user-facing artefact — it is a legal/ethical requirement.

### "Add a new experiment"
Create `experiments/expNNN_descriptive_name/` with: `PREREG.md` (hypothesis + decision
rule, SHA-256 locked), `run.py` (deterministic seed 20260501), `README.md`. Run
`scripts/integrity_audit.py` before committing.

## How to verify nothing has been broken

```powershell
cd C:\Users\mtj_2\OneDrive\Desktop\Quran
python scripts/integrity_audit.py
python scripts/zero_trust_audit.py
```

Both should report **0 CRITICAL**. If either fails, STOP and ask the user before pushing.

## If in doubt

Read `docs/PAPER.md` §0 (AI disclosure + reproducibility) and §Methods first, then ask
the user. The paper is the ground truth for every scientific claim.

---

_End of handoff._
