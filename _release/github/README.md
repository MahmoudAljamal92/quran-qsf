# GitHub Release — Step-by-Step

You do **NOT** copy the repo into this folder. The repo at `C:\Users\mtj_2\OneDrive\Desktop\Quran` is already the GitHub release. This folder is just the checklist.

## Step 1 — Create the empty GitHub repo (web, 2 min)

1. Go to https://github.com/new (log in first; if no account, click "Sign up" → use email + password, no card needed).
2. **Repository name**: `quran-qsf` (or `quranic-structural-fingerprint`).
3. **Description**: "Reproducible information-theoretic characterisation of the Quran as a multivariate statistical outlier (V3.31 closure, 91 findings, 66 retractions, dual-licence AGPL-3.0 + CC-BY-SA-4.0)."
4. **Public** (required for arXiv citation).
5. **Do NOT** tick "Initialize with README" or "Add licence" (we already have those).
6. Click **Create repository**.
7. Copy the URL shown, it looks like `https://github.com/YOUR_USERNAME/quran-qsf.git`.

## Step 2 — Push your local repo (PowerShell, 3 min)

Open PowerShell and paste these commands **one line at a time**, replacing `YOUR_USERNAME`:

```powershell
cd C:\Users\mtj_2\OneDrive\Desktop\Quran

# init the local repo if not already
git init
git add --all
git commit -m "Initial public release — project closure at V3.31 (2026-05-01)"
git branch -M main

# point it at your GitHub repo
git remote add origin https://github.com/YOUR_USERNAME/quran-qsf.git
git push -u origin main
```

If the push asks for credentials, use your GitHub username + a **personal access token** (GitHub → Settings → Developer settings → Personal access tokens → Generate new → scope: `repo` only → copy, paste as password).

## Step 3 — Tag the release (1 min)

```powershell
git tag -a v1.0.0-project-closure -m "Project closure V3.31: 91 findings, 66 retractions, 2 tools, 8-channel authentication ring"
git push origin v1.0.0-project-closure
```

GitHub will auto-build a tarball + zipball at the tag URL. That is the permanently-citable snapshot.

## Step 4 — Grab the commit hash for OpenTimestamps (30 s)

```powershell
git rev-parse HEAD > ..\_release\opentimestamps\release_commit.txt
```

(That file will now contain e.g. `a3b4c5d6e7f8...`; you'll stamp it in the OpenTimestamps step.)

## What is actually pushed

The `.gitignore` at the repo root already excludes:
- `src/cache/` (CamelTools cache, rebuilds in 60 s on first run)
- `__pycache__/`, `.ipynb_checkpoints/`
- `results/experiments/expNN_*/scratch/`
- `_release/` itself (you can remove the ignore line for it if you want to push the release scaffolding too; default is to keep it local)

Everything else — `src/`, `experiments/`, `data/corpora/`, `results/`, `archive/`, `docs/`, the two tools, all 66 retractions, all receipts, `LICENSE-DUAL.md` — is pushed.

## Troubleshooting

- **"remote rejected ... shallow update not allowed"**: run `git fetch --unshallow`, then retry the push.
- **push is huge / slow**: that's normal first-time; repo is ~1 GB with corpora and receipts. Later pushes are incremental.
- **"Permission denied (publickey)"**: you're using SSH. Switch to HTTPS URL (starts with `https://`) — it'll prompt for the token.
