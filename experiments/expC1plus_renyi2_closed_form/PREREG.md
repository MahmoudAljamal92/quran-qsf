# expC1plus_renyi2_closed_form — pre-registered prediction document

**Date authored:** 2026-04-26 PRE-RUN.
**Status:** PREREG. Frozen before any compute.

---

## 1. Motivation

`expC1_C3_el_inv_sqrt2` (`@experiments/expC1_C3_el_inv_sqrt2/run.py:212-232`)
established that the Quran's Band-A mean rhyme rate

```
EL_q  =  0.7074
1/√2  =  0.70711...
|gap| =  0.0003   (0.04 % rel)
```

with the jackknife and bootstrap 95 % CIs both containing 1/√2
(verdict `C1_NOT_REJECTED`).

This is, however, a *null result*: it says "the Quran's EL is consistent
with 1/√2", not "the Quran's EL **must** be 1/√2 for a deep reason".

The handoff pack (`docs/reference/handoff/2026-04-25/03_NOBEL_AND_PNAS_OPPORTUNITIES.md` Tier C, item C1) flags

> "C1 (EL_q ≈ 1/√2) is the most natural target [...] cleanest information-
> geometric framing (Cauchy–Schwarz upper bound on rhyme-rate under
> symmetric binary terminal-letter null)."

The X7 P2_OP1 closed-form result (`@experiments/expParadigm2_OP1_OP3_proofs/`)
already proves the **mathematical identity**

```
α = 2  is the unique Rényi parameter for which
       EL_iid(p)  =  Σpᵢ²  =  2^{-H₂(p)}
       (the iid pair-collision probability of a PMF p)
```

This experiment **promotes C1 from "0.7074 ≈ 0.7071 numerical coincidence"
to a closed-form information-theoretic statement** about the Quran's
verse-final-letter PMF:

> **Closed-form claim**: the verse-final-letter PMF `p̂_quran` has
> **Rényi-2 entropy `H₂(p̂_quran) = 1.000 ± ε` bits**, equivalent to
> `Σp̂² = 0.500 ± ε`. Bootstrap-CI-tested against the analytic
> reference 1/2.

This is **not** a "spooky coincidence" framing — it is a quantitative
property of the Quran's terminal-letter alphabet usage stated in
information-theoretic language, with explicit closed-form null.

---

## 2. Hypotheses

**H-C1plus-A** (closed-form identity): the Quran's verse-final-letter
PMF has `Σp̂² ∈ [0.495, 0.505]` (i.e. its Rényi-2 entropy is
`H₂ ∈ [0.985, 1.015]` bits, within ±1.5 % of 1.000 bit).

**H-C1plus-B** (cross-control distinguishability): every Arabic
control corpus (`poetry_jahili`, `poetry_islami`, `poetry_abbasi`,
`ksucca`, `arabic_bible`, `hindawi`) has `H₂` outside [0.985, 1.015]
bits.

**H-C1plus-C** (algebraic equivalence): the empirical relationship
`EL_q ≈ √(Σp̂²) ≈ 1/√2` is a per-text numerical relationship that is
**within bootstrap CI** of the closed-form identity for the Quran but
NOT for any control.

---

## 3. Method (locked)

### 3.1 Quran terminal-letter PMF
- Strip diacritics (DIAC set per `src/features.py:48-52`).
- For each of 6 236 Quran verses, extract the verse-final alphabetic
  character via `_terminal_alpha`.
- Build empirical PMF `p̂_i = count(letter_i) / total_count` over
  the 28-letter Arabic abjad.

### 3.2 Closed-form quantities
```
Σp̂²       = Σ_i p̂_i²                      (iid pair-collision prob)
H₂(p̂)     = −log₂(Σp̂²)                    (Rényi-2 entropy, bits)
H_shannon = −Σ p̂_i log₂(p̂_i)              (Shannon entropy, bits)
H_max     = log₂(28) = 4.807               (uniform-28 entropy)
```

### 3.3 Bootstrap CI on Σp̂²
- Resample 6 236 verse-final letters with replacement, B = 100 000
  resamples, seed = 42.
- For each resample, compute `Σp̂_b²`.
- Report median, 2.5 %, 97.5 %, p_left (frac < 0.5), p_right
  (frac > 0.5), p_two_sided (extremity vs 0.5).

### 3.4 Cross-control comparison
For each Arabic-ctrl corpus and each of the 4 cross-tradition
non-Arabic corpora that have terminal-letter data, compute the same
`Σp̂²`, `H₂`, `EL_observed` and bootstrap CI. Tabulate side-by-side.

### 3.5 Optional: per-Band-A surah Rényi-2
Compute per-surah `H₂(p̂_s)` for the 68 Band-A surahs and report the
mean and bootstrap CI. The locked Band-A mean EL = 0.7074 should be
empirically explained by `2^{-H₂(p̂_s)}` plus a within-surah-clustering
residual `c_s = EL_observed_s − Σp̂_s²`. Quantify the clustering
residual: `mean(c_s)` is the "rhyme excess over iid".

---

## 4. Pre-registered verdicts (evaluated in this order)

| Code | Condition |
|---|---|
| `PASS_RENYI2_IDENTITY_AND_DISTINCT` | Quran `Σp̂² ∈ [0.495, 0.505]` AND every Arabic-ctrl corpus is OUTSIDE this band |
| `PASS_RENYI2_IDENTITY_QURAN_ONLY` | Quran `Σp̂² ∈ [0.495, 0.505]` AND ≥ 1 Arabic-ctrl is also INSIDE this band (Quran is in a small set, not unique) |
| `PARTIAL_NEAR_HALF` | Quran `Σp̂² ∈ [0.48, 0.52]` but outside [0.495, 0.505] |
| `FAIL_NOT_HALF` | Quran `Σp̂² < 0.48` OR `> 0.52` (the 0.04 % numerical match was a sample-size artefact) |

---

## 5. Falsifiers

- **F1** — `FAIL_NOT_HALF`: Σp̂² is more than 4 % away from 0.5. The
  C1 numerical coincidence was a sample-size artefact at the per-surah
  mean scope; the closed-form Rényi-2 statement is wrong.
- **F2** — Quran `Σp̂²` outside the [0.495, 0.505] band but within
  [0.48, 0.52]: PARTIAL.

---

## 6. Reads / writes

- **Reads only**: `data/corpora/{ar,he,el,pi,sa,ae}/...` via
  `raw_loader.load_all`; `results/checkpoints/phase_06_phi_m.pkl`
  for the locked Band-A surah identifier list.
- **Writes only** under
  `results/experiments/expC1plus_renyi2_closed_form/`:
  - `expC1plus_renyi2_closed_form.json`
  - `self_check_<ts>.json`

---

## 7. No locks touched

No modification to `results/integrity/`, `results/checkpoints/`,
or `notebooks/ultimate/`. `self_check_end` must pass.

---

## 8. Frozen constants

```python
SEED = 42
N_BOOTSTRAP = 100_000
RENYI2_IDENTITY_BAND = (0.495, 0.505)   # PASS region for Σp̂²
RENYI2_NEAR_HALF_BAND = (0.480, 0.520)  # PARTIAL region
ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
CROSS_TRADITION_NON_ARABIC = [
    "hebrew_tanakh", "greek_nt", "iliad_greek",
    "pali_dn", "pali_mn", "rigveda", "avestan_yasna",
]
```

---

## 9. What this experiment does NOT claim

- Does NOT claim `EL_q = 1/√2` is **derivable** from Arabic phonotactics
  alone (the H_LING hypothesis is empirically falsified by Arabic poetry's
  EL ≈ 0.10–0.20).
- Does NOT claim Quran is the only text in any language with `H₂ = 1
  bit` (cross-tradition test is exploratory, no locked verdict).
- Does claim, IF the closed-form identity holds, that the Quran's
  verse-final-letter distribution is information-theoretically as
  far from uniform-28 as a maximally-mixed binary distribution is:
  `H₂(p̂_quran) ≈ 1 bit` vs `H₂(uniform-28) ≈ 4.81 bits`.

---

*Pre-registered 2026-04-26 PRE-RUN. Prereg hash computed at run-time
and stored in the output JSON.*
