# exp25 — Farasa root-extractor sensitivity (skeleton)

**Status**: skeleton only (2026-04-20). Fails CLOSED if Farasa is not
installed; self-check always completes.
**Outputs**: `results/experiments/exp25_farasa_sensitivity/exp25_farasa_sensitivity.json`.

## Why this exists

Φ_M's fourth feature (`H_cond`) depends on `src.arabic_roots`, which
uses CamelTools. External review (2026-04-20) flagged that CamelTools'
Arabic root analysis has a documented ~63 % gold-set ceiling; any
quantitative claim built on H_cond inherits that ceiling.

If an alternative root analyser (Farasa, AraComLex) returns effectively
the same H_cond values, the claim is analyser-robust; if not, it is
not, and any H_cond-dependent number must be flagged.

## Protocol (once Farasa is wired)

1. Re-extract verse-final roots under Farasa for every Band-A Arabic
   unit.
2. Recompute `H_cond` per unit using the Farasa roots.
3. Pearson r(H_cond_CamelTools, H_cond_Farasa) per corpus.
4. Replace feature #4 in each 5-D vector with the Farasa H_cond;
   recompute `X'` and compute a paired |ΔT²| against the locked
   Hotelling T² baseline.
5. Report: |ΔT²| per corpus and the pairwise r.

## How to install Farasa

- Install Java 8+ (`java -version` must print 1.8+).
- Either:
  - Download the Farasa JARs from <https://farasa.qcri.org/> and place
    the segmenter/lemmatiser JARs on PATH, then wrap via a subprocess
    call; OR
  - `pip install farasapy` (community Python wrapper; verify it is
    up-to-date with your Farasa version).
- Edit `run.py::_root_via_farasa(word)` to return a consonantal root
  string in the same convention as
  `src.arabic_roots.primary_root_normalized`.

## How to run

```powershell
# Before Farasa install: this fails CLOSED with a clear message.
python -m experiments.exp25_farasa_sensitivity.run
```

## Interpretation (once Farasa wired)

- **All |ΔT²| / T² < 5 %** and per-corpus Pearson r ≥ 0.85 → add a
  §4.18 "Analyser-robustness" paragraph to `docs/PAPER.md`: the Φ_M
  headline is stable under Farasa substitution.
- **Any |ΔT²| / T² > 15 %** → downgrade the H_cond-dependent claims to
  "CamelTools-specific" in `docs/PAPER.md` §5 and
  `docs/QSF_COMPLETE_REFERENCE.md` §3.4.
- **Middle range** → report as supplementary sensitivity appendix.
