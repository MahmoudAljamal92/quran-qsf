# expP18_shannon_capacity_el — Pre-Registration

**Frozen**: 2026-04-26
**Author**: v7.9-cand patch E sprint
**Status**: pre-registered before any data look

## Background

The §4.40.4 EL Simplicity Law is presented as an *empirical* proposition.
This experiment computes the Shannon-information-theoretic upper bounds
on EL given (a) the 28-letter Arabic alphabet + (b) the empirical letter
unigram distribution of Arabic prose. The goal is to provide partial
theoretical scaffolding for §4.40.4: under what alphabet-and-distribution
constraints is EL = 0.71 even reachable?

## Hypothesis

**H1 (theoretical)**: The maximum achievable EL under independent
letter sampling from the empirical Arabic terminal-letter distribution
(`p̂(letter)`) of the 6-corpus pool is `Σ_letter p̂(letter)²` (= probability
two i.i.d. samples agree). This is the Shannon-floor; an actual corpus
achieves higher EL by deviating from i.i.d.

**H2 (theorem-class)**: For a corpus to reach EL ≥ 0.50 under any
distribution on a 28-letter alphabet, the dominant letter's mass must
satisfy `p_max ≥ 0.50` (since Σ_l p_l² ≤ p_max · 1 and the off-dominant
contributions cannot exceed `(1 - p_max)`). The Quran's `p(ن) = 0.501`
saturates this bound, while the next Arabic corpus reaches only
`p_max = 0.21`, yielding theoretical Σ p_l² ≤ 0.21·1 = 0.21 — well below
EL = 0.50.

## Protocol

1. Compute empirical `p̂(letter | terminal)` for each Arabic control
   corpus + the Quran.
2. Compute `EL_iid_floor = Σ_letter p̂² = (1 / e^{H₂})` where `H₂` is
   the Rényi-2 entropy.
3. Compute the actual EL and report the gap `EL - EL_iid_floor` (this
   is the "structural rhyme excess").
4. Compute the upper-bound theorem: max EL achievable on a 28-letter
   alphabet for a given `p_max` is `p_max² + (1-p_max)²/27` (worst case
   when the off-dominant 27 letters are uniformly distributed).
5. Verify the Quran saturates the upper bound while controls do not.

## Pre-registered decision rule

This is a derivation experiment; outcome is the **theorem statement** +
empirical confirmation table (no fail/pass).

## Reproduction

```powershell
python -X utf8 -u experiments\expP18_shannon_capacity_el\run.py
```
