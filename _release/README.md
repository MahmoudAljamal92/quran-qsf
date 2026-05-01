# QSF Release Packages

**Four sub-folders, each maps to one upload target.** None of them duplicates the large project tree — each either (a) contains only the small subset required for that platform, or (b) contains a short instructions file that tells you exactly what to click / push.

| Folder | What to upload | Platform | Time |
|---|---|---|---|
| `github/` | The **whole repo at project root** (this folder only holds the checklist) | GitHub (new public repo `quran-qsf`) | 15 min |
| `osf/`    | All 10 files inside `osf/` (small: ~500 KB total) | OSF preregistration + DOI | 10 min |
| `arxiv/`  | `paper.pdf` + `THE_QURAN_FINDINGS.md` supplement | arXiv `cs.CL` | 20 min |
| `opentimestamps/` | `release_commit.txt.ots` after you stamp | Bitcoin blockchain (free) | 5 min |

Do them in this order: **GitHub → OSF → arXiv → OpenTimestamps**.

Full rationale is in `../docs/PUBLISHING_PLAN.md`. This folder is the **hands-on checklist**; the plan is the **why**.
