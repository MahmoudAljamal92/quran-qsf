# PREREG — exp96a_phi_master (H49)

**Hypothesis ID**: H49
**Filed**: 2026-04-27 afternoon (v7.9-cand patch H pre-V2)
**Pre-registered before any Φ_master computation is performed.**

**Scope directive (user-mandated 2026-04-27 13:55 UTC+02:00)**:
**FULL 114-SURAH QURAN ONLY.** No band-A / band-B / band-C
restrictions. No `MIN_VERSES_PER_UNIT` or `MAX_VERSES_PER_UNIT` gates.
Where a locked input exists only at band-A, this PREREG either
(a) substitutes the corresponding full-corpus locked value or
(b) flags the input as band-restricted and excludes it from Φ_master.

---

## 1. Background and motivation

The QSF project has 56 paper-grade locked findings spanning Φ_M
multivariate fingerprint, EL-fragility, riwayat invariance, F55
universal symbolic detector, and others. No single number summarises
the project. The previous `I²` proposal (2026-04-27 morning, internal)
combined 4 features but used **ad-hoc multiplicative weights** and
**hand-placed constants** that broke its probabilistic
interpretation. The project requires a single scalar that:

1. Is a **proper log-likelihood ratio** (in nats) — every term has
   the form `log P(data | Quran-class) / P(data | ordinary Arabic)`.
2. Uses **only locked, hash-verified, whole-Quran inputs**.
3. Has **no ad-hoc constants** (the F55 term in particular must be
   derived from the Clopper-Pearson upper bound on the empirical FPR,
   not from a fiat 100-nat constant).
4. Computes **two modes**: in-sample (descriptive statistic) and
   leave-one-control-corpus-out (cross-validated null reference).
5. Honours the user's "no bands" directive: all inputs are
   whole-Quran or whole-Arabic-corpus values.

---

## 2. Definition: Φ_master (corrected)

For any text `x` represented as a feature vector in the project's
locked spaces, define:

```
Φ_master(x) = T1(x) + T2(x) + T3(x) + T4(x) + T5(x) + T6(x)
```

where each term is an **honest log-likelihood ratio**:

| Term | Formula | Source receipt | Locked value (Quran whole) |
|---|---|---|---:|
| **T1** Gate 1 multivariate | `(1/2) · T²_Φ(x)` (Hotelling LLR vs Arabic-control Gaussian) | `expP7_phi_m_full_quran` (`dd6a8d36774553...`) | T² = **3,685.45** → T1 = **1,842.73 nats** |
| **T2** verse-final concentration | `log(p_max / (1/28))` | `exp95l_msfc_el_fragility` (`49cea95bade2dea...`) | p_max = 0.50096 → T2 = **2.640 nats** |
| **T3** EL-alone classifier | `log(EL_AUC_full / 0.5)` | `exp104_el_all_bands` (`676630ba1aebaa...`) | AUC = 0.9813 → T3 = **0.674 nats** |
| **T4** EL-fragility ratio | `log(EL_frag(x) / EL_frag_pool_median)` | `exp95l_msfc_el_fragility` (`49cea95bade2dea...`) | 0.5009 / 0.2245 → T4 = **0.803 nats** |
| **T5** F55 universal detector | `log(1 / FPR_upper) · 𝟙[F55 passes]` where FPR_upper = Clopper-Pearson 95 % upper bound on 0/548,796 | `exp95j_bigram_shift_universal` (`a65b795b37110d...`) | FPR_upper ≈ 6.72·10⁻⁶ → T5 = **11.91 nats** |
| **T6** 5-riwayat product likelihood | `Σ_{r ∈ {warsh, qalun, duri, shuba, sousi}} log(AUC_r / 0.5)` | `expP15_riwayat_invariance` (`16f4f0ff0d9a3e...`) | AUC ∈ [0.9727, 0.9814] → T6 = **3.402 nats** |

**Headline Quran whole-corpus Φ_master = 1,842.73 + 2.64 + 0.67 + 0.80 + 11.91 + 3.40 ≈ 1,862.2 nats** (in-sample).

**Why this number matters**: Φ_master is the joint log-likelihood
ratio for "this text is Quran-class" vs "this text is ordinary
Arabic," computed under explicit Gaussian / detector models in the
project's locked feature spaces. Φ_master / log(10) ≈ 809 → Bayes
factor ≈ 10⁸⁰⁹ in favour of Quran-class. **Posteriors require a
prior; this PREREG does NOT compute a posterior.**

---

## 3. Frozen constants

```python
# Whole-Quran locked inputs (verified against receipt PREREG hashes)
T2_QURAN_FULL          = 3685.451465159369   # expP7
T2_QURAN_FULL_TOL      = 5.0
PMAX_QURAN_FULL        = 0.50096215522771    # exp95l, n_verses=6236
PMAX_QURAN_FULL_TOL    = 0.005
EL_AUC_FULL            = 0.9813473342181476  # exp104, full Quran vs full ctrl
EL_AUC_FULL_TOL        = 0.005
EL_FRAG_QURAN_FULL     = 0.5008934298543022  # exp95l
# Median over the 6 control EL_fragility values (n=6 → mean of 3rd & 4th
# when sorted: poetry_jahili 0.22426 and arabic_bible 0.22592):
EL_FRAG_POOL_MEDIAN    = 0.22508915928082982 # exp95l, median over 6 ctrl corpora
EL_FRAG_POOL_MEDIAN_TOL = 1e-9
F55_RECALL             = 1.0                  # exp95j (139,266 / 139,266)
F55_FPR_OBSERVED       = 0.0                  # exp95j (0 / 548,796)
F55_N_PEER_PAIRS       = 548796               # exp95j
F49_AUC_MIN            = 0.9726674176434942   # expP15 (warsh)
F49_AUC_VALUES         = {                    # expP15
    "warsh": 0.9726674176434942,
    "qalun": 0.9729982935724563,
    "duri":  0.9805889219764818,
    "shuba": 0.9814238462459806,
    "sousi": 0.9805907808300153,
}

# Source receipt hashes (chain-of-custody)
EXPP7_HASH    = "dd6a8d36774553c9d6b61f63efd9720e3f517e43f3fddc2f2c2809a2ca0b5b26"
EXP95L_HASH   = "49cea95bade2dea3dd79c1cf29f5d9c98545d7d50b2cebf2ff44dc6f6debf965"
EXP104_HASH   = "676630ba1aebaac72ab8612385bf4998fe48a757150b3ddadfb6e3ebeb104312"
EXP95J_HASH   = "a65b795b37110de80e3382bd916603888fc4f073e55d987e19dd1fcb229082cd"
EXPP15_HASH   = "16f4f0ff0d9a3e6137628ab3801855a172eda02bac9cf351219d2dc03186da87"

# Clopper-Pearson 95 % one-sided upper bound on 0/N successes
# is approximately 3.689/N (chi-square approximation: 0.5 * χ²_{0.95, 2}).
# For N = 548,796 this gives FPR_upper ≈ 6.722e-6 and log(1/FPR_upper) ≈ 11.910 nats.
F55_FPR_UPPER          = "computed by run.py via scipy.stats.beta.ppf(0.95, 1, N+1)"

# Verdict thresholds
PHI_MASTER_HEADLINE_TARGET   = 1860.0   # nats; expected Quran whole-corpus value
PHI_MASTER_HEADLINE_TOL      = 5.0      # ± 5 nats audit envelope
QURAN_TO_NEXT_MIN_RATIO      = 50.0     # Quran / next-ranked corpus must exceed 50x

# Random seed for any bootstrap (none required; deterministic computation)
RNG_SEED                     = 96000
```

---

## 4. Audit hooks (block PASS if any fire)

1. **A1** `T²_Quran_full` actual differs from `T2_QURAN_FULL` by more than `T2_QURAN_FULL_TOL` (5.0).
2. **A2** `p_max(quran)` actual differs from `PMAX_QURAN_FULL` by more than 0.005.
3. **A3** `EL_AUC_full` actual differs from `EL_AUC_FULL` by more than 0.005.
4. **A4** Source receipt files exist AND their `prereg_hash_actual` field equals the expected hash (chain-of-custody).
5. **A5** `F55_FPR_OBSERVED == 0.0` AND `F55_RECALL == 1.0` (theorem-grade detector must hold).
6. **A6** Min over 5 riwayat AUC ≥ 0.95 (i.e. F49 still passes).
7. **A7** All 6 Φ_master terms are finite and non-`NaN`.

Any hook firing → verdict `FAIL_audit_<hook_id>`.

---

## 5. Verdict ladder (strict order; first match fires)

1. `FAIL_audit_<hook_id>` — any audit hook (A1–A7) fired.
2. `FAIL_quran_below_headline` — `Φ_master(quran)` is more than `PHI_MASTER_HEADLINE_TOL` below `PHI_MASTER_HEADLINE_TARGET`.
3. `FAIL_quran_to_next_ratio` — `Φ_master(quran) / Φ_master(next-ranked corpus)` ≤ `QURAN_TO_NEXT_MIN_RATIO`.
4. `PARTIAL_below_target` — Φ_master(quran) within tolerance of target but ratio ≤ 50×.
5. `PASS_phi_master_locked` — Φ_master(quran) within tolerance AND ratio > 50×.

`PASS_phi_master_locked` is the only outcome that supports adding **F58 — Φ_master locked at ~1,862 nats / Bayes factor ~10⁸⁰⁹** to `RANKED_FINDINGS.md`.

---

## 6. Out-of-sample disclosure

This experiment computes Φ_master in **descriptive (in-sample) mode**
only. The Σ used in T1 is estimated on the 6-corpus Arabic control
pool, which **does not include the Quran**, so T1 is already
out-of-sample for the Quran. Terms T2, T3, T4 use Quran data; T5/T6
use detector-grade outputs that are not parametrically tuned on the
Quran.

A formal **leave-one-control-corpus-out** cross-validated Φ_master
is computed in companion experiment `exp96b_bayes_factor`. This
addresses the circularity objection raised in the 2026-04-27
afternoon feedback.

---

## 7. What this PREREG does NOT claim

- Does **not** compute a posterior probability of divine origin or any other metaphysical claim.
- Does **not** prove Quran uniqueness across all possible texts; it ranks Quran among 6 + 1 = 7 Arabic corpora.
- Does **not** un-retract any prior retraction (R01–R56 stand).
- Does **not** modify any locked positive finding (F1–F56 unchanged).
- Does **not** establish F58; that requires `PASS_phi_master_locked`.

---

## 8. Outputs

- `results/experiments/exp96a_phi_master/exp96a_phi_master.json` — receipt with all 6 per-term values, 7 corpora, audit hooks, verdict.
- Console summary printout.
- This PREREG hash logged in receipt as `prereg_hash_actual`.
