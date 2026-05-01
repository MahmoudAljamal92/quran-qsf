# expP17_markov_saj_adversarial — Pre-Registration

**Frozen**: 2026-04-26
**Author**: v7.9-cand patch E sprint
**Status**: pre-registered before any data look

## Background

The §4.40.4 EL Simplicity Law claims: "for any Arabic prose corpus,
EL ≥ 0.314 + AUC ≥ 0.95 cannot be jointly achieved by a 1-D classifier
unless the corpus IS the Quran." This is an empirical proposition. A
necessary stress test: try to FORGE a corpus that defeats it using a
character-level Markov model trained on the highest-EL Arabic-prose
control families.

## Hypothesis

**H1 (claim defended)**: Markov-generated corpora trained to maximise EL
under the rhyme constraint will fall **below** the EL = 0.314 boundary
(or, equivalently, will be classified as Quran with AUC < 0.95 — i.e.,
the forgery is detectable). This means the EL Simplicity Law survives
this attack.

**Alternative (claim falsified)**: a Markov model can saturate EL ≥ 0.40
on a synthetic corpus, in which case the EL law's "uniqueness" claim is
qualified to "uniquely high *natural*-Arabic EL" and the §4.40.4 falsifier
must be reformulated to require a content-validity check (not just EL
arithmetic).

## Pre-registered decision rule

| Outcome | Verdict |
|---|---|
| max(EL_Markov) < 0.40 across 100 generations | `EL_LAW_DEFENDED` |
| 0.40 ≤ max(EL_Markov) < 0.55 | `EL_LAW_QUALIFIED` (saj‛ can come close; corpus-source caveat needed) |
| max(EL_Markov) ≥ 0.55 | `EL_LAW_FALSIFIED` (need content-validity layer) |

## Protocol

1. Train a character-level order-3 Markov model on poetry_islami +
   poetry_abbasi + poetry_jahili (the 3 highest-EL control families).
2. Generate 100 surah-length samples (avg 50 verses, ~10 words/verse).
3. Compute EL per sample.
4. Report distribution.
5. Side-experiment: train a similar order-3 Markov model on Quran itself
   and check whether ITS samples reach EL ≈ 0.50 (sanity).

## Reproduction

```powershell
python -X utf8 -u experiments\expP17_markov_saj_adversarial\run.py
```
