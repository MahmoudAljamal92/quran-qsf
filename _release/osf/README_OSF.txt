QSF — OSF Deposit (minimal, self-contained)
============================================

This folder is a LIGHTWEIGHT deposit suitable for the Open Science Framework (https://osf.io). It contains the 10 essential documents that let any reviewer understand, verify, and cite the project. The **full** code + data + receipts live on GitHub at the URL printed below.

How to upload (web, 10 minutes)
-------------------------------
1. Go to https://osf.io  -> Sign up (free, takes 30 s, email-only).
2. Click "Create new project". Title: "Quranic Structural Fingerprint (QSF)".
3. Description: paste the one-paragraph elevator summary at the bottom of this file.
4. Add storage → OSF Storage → drag ALL files from THIS folder into the browser. Upload.
5. Make the project Public (toggle at top).
6. Click "Register" (left sidebar) → choose template "OSF Preregistration" → confirm → DONE.
7. OSF will assign a permanent DOI (e.g. 10.17605/OSF.IO/ABCDE).
   - Copy the DOI.
   - Paste it into README.md and docs/PAPER.md where they say "OSF_DOI_PENDING".
   - Commit+push that change to GitHub.

Files in this deposit
---------------------
THE_QURAN_FINDINGS.md     Single-doc extraction of every positive finding (~50 KB, 18 pages; the review-ready handout)
PAPER.md                  Full manuscript (the paper itself; ~450 KB, 100 pages)
PUBLISHING_PLAN.md        This plan (so reviewers can see the release rationale)
RANKED_FINDINGS.md        91-row findings ledger with ranks and receipts
RETRACTIONS_REGISTRY.md   66-row retractions ledger (the integrity proof)
CHANGELOG.md              Full version history back to project start
README.md                 Top-level project README
requirements.txt          Python dependencies
TOP_FINDINGS_AUDIT.md     Raw-data re-verification audit (8 top findings independently re-run)
README_OSF.txt            This file

GitHub mirror
-------------
The full repository (code, corpora, 200+ receipts, figures, archive of earlier sprints) is pushed to:
    https://github.com/YOUR_USERNAME/quran-qsf
    (tag: v1.0.0-project-closure)

Clone it with:
    git clone https://github.com/YOUR_USERNAME/quran-qsf.git
    cd quran-qsf
    pip install -r requirements.txt
    python scripts/_audit_top_findings.py

That command re-verifies the 8 top findings from raw corpus data in ~30 seconds.

One-paragraph elevator summary (for the OSF project description)
----------------------------------------------------------------
The Quranic Structural Fingerprint project is a reproducible, SHA-256-locked characterisation of the Quran as a multivariate statistical outlier in classical-Arabic prose, with cross-tradition replications in 6 alphabets and 5 language families. Headline results include a 1-bit categorical universal (Quran is the unique corpus with verse-final-letter Shannon entropy below 1 bit), a universal 5.75-bit Shannon–Rényi-∞ gap invariant across 11 oral canons at CV = 1.94 %, a Mushaf-as-tour coherence finding (p ≤ 10⁻⁷ at 10M permutations), a 3-axis multifractal fingerprint (pool-z = 4.2, LOO-z = 22.6), and an 8-channel authentication ring deployable as a single command-line tool. The project includes 66 honest retractions. All 70+ positive findings are reproducible from raw data; no claim relies on unaudited AI output despite the ~99 %-AI-pair-programmed authorship.
