QSF — arXiv Submission Package
==============================

Target: arXiv.org, category cs.CL (computation and language), secondary stat.AP + math.IT.

Files in this folder
--------------------
paper.tex                      LaTeX source (generated via pypandoc — arXiv accepts .tex directly; THIS IS THE PRIMARY SUBMISSION)
paper.html                     HTML fallback (for print-to-PDF or quick preview; open in any browser)
THE_QURAN_FINDINGS.md          Supplementary material: single-doc extraction of every finding (review-ready handout)
README_arxiv.txt               This file

Note: paper.pdf is NOT pre-generated because xelatex is not installed on
this machine. arXiv compiles LaTeX internally, so the .tex file is the
correct submission format. If you want a local PDF for preview, pick ONE:

OPTION A (easiest, no install): open paper.html in a browser -> Ctrl+P -> "Save as PDF".

OPTION B (proper PDF via pandoc + LaTeX):
    pip install pypandoc[tinytex]    (bundles a minimal LaTeX engine)
    python -c "import pypandoc; pypandoc.convert_file('docs/PAPER.md','pdf',outputfile='_release/arxiv/paper.pdf',extra_args=['-s','--pdf-engine=xelatex'])"

OPTION C (system-wide, best quality):
    winget install --id JohnMacFarlane.Pandoc -e
    winget install --id MiKTeX.MiKTeX -e
    pandoc docs/PAPER.md -s -o _release/arxiv/paper.pdf --pdf-engine=xelatex

How to upload to arXiv (web, 20 minutes)
----------------------------------------
1. Create account at https://arxiv.org (free; ignore ORCID for now).
2. If you are not affiliated with a university, you need an ENDORSEMENT.
   - Email a colleague who is endorsed in cs.CL, ask them to endorse you (1-line email).
   - Or wait: arXiv sometimes auto-endorses based on first-submission quality review.
3. arXiv -> Submit -> New submission.
4. Primary archive: cs, category: cs.CL. Secondary: stat.AP, math.IT.
5. Title: "The Quranic Structural Fingerprint: A Reproducible Information-Theoretic Characterisation of a Multivariate Outlier in Classical-Arabic Prose, with an 8-Channel Authentication Ring"
6. Authors: M. Aljamal.
7. Abstract: paste the one-paragraph elevator summary (bottom of this file).
8. File upload: upload paper.pdf as the primary manuscript.
9. Ancillary file upload: upload THE_QURAN_FINDINGS.md in the "anc/" supplementary section.
10. In the "Comments" field, include the GitHub URL:
    "Code + data + receipts: https://github.com/YOUR_USERNAME/quran-qsf"
11. Submit. arXiv assigns an ID within ~48 h (e.g. 2605.12345).
12. Paste the arXiv ID into README.md and docs/PAPER.md where they say "arXiv_PENDING". Commit+push.

One-paragraph elevator summary (use as arXiv abstract)
------------------------------------------------------
The Quranic Structural Fingerprint project is a reproducible, SHA-256-locked characterisation of the Quran as a multivariate statistical outlier in classical-Arabic prose, with cross-tradition replications in 6 alphabets and 5 language families. Headline results include a 1-bit categorical universal (Quran is the unique corpus with verse-final-letter Shannon entropy below 1 bit), a universal 5.75-bit Shannon-Renyi-infinity gap invariant across 11 oral canons at CV = 1.94 %, a Mushaf-as-tour coherence finding (p <= 10^-7 at 10M permutations), a 3-axis multifractal fingerprint (pool-z = 4.2, LOO-z = 22.6), and an 8-channel authentication ring deployable as a single command-line tool. The project includes 66 honest retractions. All 70+ positive findings are reproducible from raw data; no claim relies on unaudited AI output despite the ~99 %-AI-pair-programmed authorship.
