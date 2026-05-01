# PREREG — `exp153_F75_derivation_check`

**Hypothesis ID**: H98_F75_Geometric_Derivation
**Created**: 2026-04-30
**Sprint**: V3.18 (post-V3.17, partial theoretical derivation of F75)
**Status**: pre-registered before run

## Theoretical claim being tested

F75 (`exp122_zipf_equation_hunt::PASS_zipf_class_equation_found`) discovered that
across 11 oral-canon corpora in 5 unrelated language families, the quantity

$$Q(c) := H_{EL}(c) + \log_2(p_{\max}(c) \cdot 28) \approx 5.75 \pm 0.117 \text{ bits} \quad (CV = 2.04 \%)$$

This is **algebraically equivalent** to the Shannon-Rényi-∞ gap being approximately
constant at the universal value `H_1 - H_∞ ≈ 0.943 bits` (independent of any
choice of "28"), since:

$$Q(c) = H_{EL}(c) + \log_2(p_{\max}(c)) + \log_2(28)
       = H_1(c) - H_\infty(c) + \log_2(28)
       \implies H_1(c) - H_\infty(c) = Q(c) - \log_2(28)$$

The CV of the gap itself (without the 4.81-bit constant offset) is **19 %**, NOT 2 %.
The 2 % CV is an artifact of the +log₂(28) shift inflating the denominator of CV.

## Proposed theoretical derivation (PARTIAL; falsifiable per-corpus)

**Theorem**: For any **geometric distribution** `p_k = (1 - r) \cdot r^{k-1}` with
parameter `r ∈ (0, 1)` over an alphabet of size A → ∞ (or A finite with negligible
truncation tail):

$$H_1 - H_\infty = \frac{r}{1 - r} \cdot \log_2\!\left(\frac{1}{r}\right)$$

Equivalently in terms of `p_max = 1 - r`:

$$H_1 - H_\infty = \frac{1 - p_{\max}}{p_{\max}} \cdot \log_2\!\left(\frac{1}{1 - p_{\max}}\right)$$

This function `gap_geom(p_max)` has a **maximum at p_max = 0.5 of exactly 1.00 bit**.

**Conjecture (H98)**: oral-canon verse-final-letter distributions follow approximately
geometric structure at the corpus-pooled level, and the peak of `gap_geom` at
`p_max ≈ 0.5` explains why F75's universal gap ≈ 1 bit across 10 of 11 corpora.

The Quran is the **only outlier** because its p_max = 0.7271 (well above the
geometric-peak p_max = 0.5), giving a predicted gap of `gap_geom(0.7271) = 0.699 bits`,
within 0.19 bits of the empirical Quran gap = 0.51 bits.

## Pre-registered acceptance criteria

| # | Criterion | PASS threshold |
|---|-----------|----------------|
| **A1** | For each non-Quran corpus, the geometric-predicted gap matches empirical within ±0.30 bits | ≥ 8 of 10 corpora PASS |
| **A2** | Mean absolute residual `\|gap_emp - gap_geom\|` across all 11 corpora | ≤ 0.25 bits |
| **A3** | Pearson correlation between geometric-predicted gap and empirical gap across 11 corpora | r ≥ 0.70 |
| **A4** | Geometric prediction at p_max = 0.5 is exactly 1.00 bit | exact |
| **A5** | Quran is correctly identified as the lowest-gap outlier under geometric prediction | gap_geom(Quran) is rank-11/11 lowest |

**Verdict logic**:
- 5/5 PASS → `PASS_F75_geometric_derivation_strong`
- 4/5 PASS → `PARTIAL_F75_geometric_derivation_directional`
- ≤ 3/5 PASS → `FAIL_F75_geometric_derivation_no_match`

## Frozen constants

```
N_CORPORA              = 11
SEED                   = 42
GAP_RESIDUAL_FLOOR     = 0.30  # per-corpus residual threshold (A1)
MEAN_RESIDUAL_CEILING  = 0.25  # cross-corpus mean residual (A2)
CORRELATION_FLOOR      = 0.70  # Pearson r (A3)
LOG2_28                = 4.807354922057604  # F75's reference offset
```

## Empirical inputs (locked from `exp122_zipf_equation_hunt` receipt)

```
Q_per_corpus = {
    "quran":         5.31644412745751,
    "poetry_jahili": 5.667642099278081,
    "poetry_islami": 5.6887218755408675,
    "poetry_abbasi": 5.751629167387822,
    "hindawi":       5.841472820982165,
    "ksucca":        5.878837869278973,
    "arabic_bible":  5.851181638195952,
    "hebrew_tanakh": 5.809818932517963,
    "greek_nt":      5.656063621523095,
    "pali":          5.840863027773002,
    "avestan_yasna": 5.5103956321284695,
}
```

(Per-corpus `p_max` values are locked from `exp109_phi_universal_xtrad`'s
feature matrix; the experiment loads them directly.)

## Audit guardrails

- `prereg_hash` written into the receipt is the SHA-256 of THIS file.
- `q_per_corpus_sha256` of the input dictionary above must match.
- `feature_matrix_sha256` from `exp109_phi_universal_xtrad` must be loaded (no re-computation).
- This experiment performs NO modifications to F75's locked status; it adds a
  THEORETICAL DERIVATION CHECK as a Tier-C observation O9 (or upgrade-PASS row).
- No Brown-Stouffer formula is invoked. T²-formula-invariant.

## What this experiment cannot claim

- A proof that all oral canons HAVE geometric verse-final-letter distributions.
  The geometric form is an APPROXIMATION; true distributions have multi-modal structure
  (e.g. Quran has 14 dominant letters across 114 sūrahs). The geometric derivation
  is **at the pooled corpus level only**, and explains only the Q ≈ 1 bit aggregate.
- A first-principles derivation of why oral canons SHOULD be geometric. Geometric
  emergence may follow from (a) Zipfian word-frequency natural-language regularity,
  (b) cognitive memory constraints, or (c) some other mechanism — pinning this down
  is BEYOND scope of this experiment.
- A claim that geometric is the BEST parametric family. Other families (e.g. log-series,
  truncated Zipf with α≈2) could also fit; we test geometric specifically.

## Receipt location

`results/experiments/exp153_F75_derivation_check/exp153_F75_derivation_check.json`
