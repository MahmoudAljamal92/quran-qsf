# exp23 — Adiyat single-letter Monte Carlo (v0 scaffold)

**Status**: v0 scaffolded 2026-04-20, runnable end-to-end with a
**purely positional** substitution policy (no root-validity gate).
**Outputs**: `results/experiments/exp23_adiyat_MC/exp23_adiyat_MC.json`.

## Why this exists

`docs/ADIYAT_ANALYSIS_AR.md` evaluates three hand-picked alternative
readings (al-ghadiyat / al-badiyat / al-hadiyat). External review
(2026-04-20) flagged the "cherry-picked three" risk: if the canonical
reading ranks highly across **all** single-letter substitutions of
verse 1, the claim is structurally robust; if not, it's vulnerable.

## Protocol (v0, 2026-04-20)

- Locate Q:100 in `CORPORA["quran"]`.
- For each consonant position in verse 1, for each of the 27 remaining
  Arabic consonants: build a variant verse 1, recompute the 5-D
  features for the full surah (only verse 1 changes), compute Φ_M to
  the locked μ_ctrl.
- Report: distribution of Φ_M across all (pos × repl) pairs; percentile
  of the canonical reading.

## v0 caveat (important)

The v0 substitution policy is **purely positional**; many variants are
linguistically implausible (broken roots, non-words). Two cleaner v1
policies to implement next:

- **v1a (roots-whitelist)**: keep only variants where CamelTools returns
  a known root for every token of the new verse 1.
- **v1b (CharLM gate)**: keep only variants whose Farasa CharLM score is
  within some threshold of the canonical.

Until a v1 policy is wired, v0 results should be reported as
DESCRIPTIVE ONLY in the paper (not as a formal Monte Carlo test of
edit-detection).

## How to run

```powershell
python -m experiments.exp23_adiyat_MC.run
```

Expected runtime: < 2 min (≈ 30 positions × 27 consonants = ~800
variants × one 5-D feature-extraction each).

## Interpretation

- `canonical_percentile_below < 10 %` → canonical sits near the bottom
  of the Φ_M distribution = **poor outlier status** under v0; trust
  only if v1 roots-whitelist concurs.
- `canonical_percentile_below > 90 %` → canonical is an outlier even
  under the maximally permissive policy = robust claim.
- Middle values → inconclusive; wait for v1.
