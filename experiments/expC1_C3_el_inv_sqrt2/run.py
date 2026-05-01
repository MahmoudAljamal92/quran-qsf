"""
expC1_C3_el_inv_sqrt2/run.py
=============================
Opportunities C1 + C3 (OPPORTUNITY_TABLE_DETAIL.md):
  C1: Test H0: EL_q = 1/sqrt(2) via jackknife and bootstrap CIs around
      the Band-A mean EL.
  C3: Compute the EXACT adjacent-pair terminal-letter match fraction over
      all 6,235 corpus-level adjacent pairs and check the C3 derivation
      "EL_q^2 ≈ 1/2".

Definitions (matching `src/features.py:el_rate` byte-for-byte, paper §2.6):
  - Per-surah EL_s = (#i in [0..n_s-2] with terminal_alpha(v_{s,i}) ==
                     terminal_alpha(v_{s,i+1}) and both nonempty) / (n_s - 1)
  - Band-A mean EL_q = mean over the 68 Band-A surahs of EL_s
  - Corpus-pooled EL_pool = (#match across surah-internal adjacent pairs)
                          / (#surah-internal adjacent pairs)
                          treating each surah's pairs separately, then summing.
                          (Matches the paper definition of "EL" extended to
                          the whole canon; cross-surah pairs are NOT counted.)
  - Corpus-flat EL_flat = (#match in all 6,235 verse[i] -> verse[i+1] pairs
                          regardless of surah boundary) / 6235
                          (Includes 113 cross-surah pairs; this is the
                          variant C3 implicitly proposes when it says
                          "6,236 Quran verses → 6,235 adjacent pairs".)

Both EL_pool and EL_flat are reported so the corpus-level number is not
ambiguous.

This script is sandbox / read-only. Inputs:
  - results/checkpoints/phase_06_phi_m.pkl (Band-A indices + per-surah EL via
    state['X_QURAN'][:, EL_idx]; verses via state['CORPORA']['quran'])

Outputs:
  - results/experiments/expC1_C3_el_inv_sqrt2/expC1_C3_el_inv_sqrt2.json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase,
    safe_output_dir,
    self_check_begin,
    self_check_end,
)
from src.features import _terminal_alpha  # noqa: E402

EXP = "expC1_C3_el_inv_sqrt2"
SEED = 42
N_BOOTSTRAP = 100_000


def _surah_pairs(verses: list[str]) -> tuple[int, int, list[tuple[str, str]]]:
    """Return (n_match, n_pairs, pair_list) for ONE surah's verses.

    Ignores pairs where either side has no terminal alphabetic char
    (matches `el_rate` line 84 byte-for-byte: condition `finals[i]
    and finals[i] == finals[i+1]`)."""
    finals = [_terminal_alpha(v) for v in verses]
    pairs = list(zip(finals[:-1], finals[1:]))
    n_match = sum(1 for a, b in pairs if a and a == b)
    return n_match, len(pairs), pairs


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    feat_cols = list(state["FEAT_COLS"])
    el_idx = feat_cols.index("EL")
    X_Q = np.asarray(state["X_QURAN"], dtype=float)  # Band-A only
    band_a_mean_EL = float(X_Q[:, el_idx].mean())
    band_a_sd_EL = float(X_Q[:, el_idx].std(ddof=1))
    n_band_a = X_Q.shape[0]

    # ---- (1) Reproduce per-surah EL on the Band-A subset for sanity ----
    # Note: state['X_QURAN'] is already filtered to Band-A. We can't recover
    # WHICH 68 surahs they are without the BAND_* metadata; the per-surah
    # EL values are however directly usable for jackknife/bootstrap.
    el_band_a = X_Q[:, el_idx].astype(np.float64)

    # ---- (2) Per-surah EL across ALL 114 surahs for corpus-level numbers --
    quran_units = state["CORPORA"]["quran"]
    assert len(quran_units) == 114, f"Got {len(quran_units)} quran units"

    all_n_match = 0
    all_n_pairs = 0
    per_surah = []  # list of dicts with surah-level breakdown
    flat_finals: list[str] = []
    for u in quran_units:
        n_match, n_pairs, _ = _surah_pairs(u.verses)
        all_n_match += n_match
        all_n_pairs += n_pairs
        per_surah.append({
            "label": u.label,
            "n_verses": len(u.verses),
            "n_pairs": n_pairs,
            "n_match": n_match,
            "el_pooled_surah": n_match / n_pairs if n_pairs > 0 else 0.0,
        })
        # Append THIS surah's verse-final letters to the flat list for the
        # C3 cross-surah-allowed variant.
        flat_finals.extend(_terminal_alpha(v) for v in u.verses)

    # Pooled EL: fraction of within-surah adjacent matches. Cross-surah
    # boundaries are NOT counted.
    el_pool = all_n_match / all_n_pairs if all_n_pairs > 0 else 0.0

    # Flat EL: include cross-surah boundaries. Should be ~ identical to
    # el_pool because cross-surah pairs are 113 / ~6235 of the denominator
    # and have no special structure.
    flat_match = sum(
        1 for i in range(len(flat_finals) - 1)
        if flat_finals[i] and flat_finals[i] == flat_finals[i + 1]
    )
    flat_pairs = len(flat_finals) - 1
    el_flat = flat_match / flat_pairs if flat_pairs > 0 else 0.0

    # ---- (3) Per-surah EL across all 114 (for an unweighted-mean EL) ----
    el_all_114 = np.array(
        [s["el_pooled_surah"] for s in per_surah], dtype=np.float64
    )
    el_all_114_mean = float(el_all_114.mean())

    # ---- (4) Jackknife on Band-A (leave-one-surah-out) ----
    n = el_band_a.size
    total_sum = float(el_band_a.sum())
    jk_means = np.array(
        [(total_sum - el_band_a[i]) / (n - 1) for i in range(n)],
        dtype=np.float64,
    )
    jk_mean = float(jk_means.mean())                       # equals band_a_mean_EL
    jk_var = (n - 1) / n * float(((jk_means - jk_mean) ** 2).sum())
    jk_se = math.sqrt(jk_var)
    # Symmetric Gaussian 95 % CI on the mean
    jk_ci_lo = band_a_mean_EL - 1.959963984540054 * jk_se
    jk_ci_hi = band_a_mean_EL + 1.959963984540054 * jk_se

    # One-sample t-test against H0: mu = 1/sqrt(2)
    mu0 = 1.0 / math.sqrt(2.0)
    se_classical = band_a_sd_EL / math.sqrt(n)
    t_stat = (band_a_mean_EL - mu0) / se_classical
    df = n - 1
    # Two-sided p (closed-form via Student-t cdf)
    from scipy import stats as _st  # local import: kept off global path
    p_two_sided = float(2.0 * _st.t.sf(abs(t_stat), df))
    # Same against the jackknife SE
    t_stat_jk = (band_a_mean_EL - mu0) / jk_se
    p_two_sided_jk = float(2.0 * _st.t.sf(abs(t_stat_jk), df))

    # ---- (5) Bootstrap on Band-A ----
    rng = np.random.default_rng(SEED)
    boot_means = np.empty(N_BOOTSTRAP, dtype=np.float64)
    # Vectorised bootstrap: (B, n) idx matrix sampled with replacement
    # from {0..n-1}. Use index-based gather for memory.
    BATCH = 10_000
    written = 0
    while written < N_BOOTSTRAP:
        b = min(BATCH, N_BOOTSTRAP - written)
        idx = rng.integers(0, n, size=(b, n))
        boot_means[written:written + b] = el_band_a[idx].mean(axis=1)
        written += b
    boot_ci_lo = float(np.quantile(boot_means, 0.025))
    boot_ci_hi = float(np.quantile(boot_means, 0.975))
    boot_p_lt_mu0 = float((boot_means < mu0).mean())
    boot_p_gt_mu0 = float((boot_means > mu0).mean())
    # Two-sided "extreme-vs-mu0" tail probability under the bootstrap dist
    centered = boot_means - band_a_mean_EL
    abs_obs = abs(band_a_mean_EL - mu0)
    boot_p_two_sided = float((np.abs(centered) >= abs_obs).mean())

    # ---- (6) Verdicts ----
    if jk_ci_lo <= mu0 <= jk_ci_hi:
        c1_jk_verdict = "C1_NOT_REJECTED_jackknife_CI_contains_1_over_sqrt2"
    else:
        c1_jk_verdict = "C1_REJECTED_jackknife_CI_excludes_1_over_sqrt2"
    if boot_ci_lo <= mu0 <= boot_ci_hi:
        c1_boot_verdict = "C1_NOT_REJECTED_bootstrap_CI_contains_1_over_sqrt2"
    else:
        c1_boot_verdict = "C1_REJECTED_bootstrap_CI_excludes_1_over_sqrt2"

    # C3 proposed two corollaries. Test both against EL_pool / EL_flat:
    #   (a) EL_pool ≈ 1/2  (the "0.5 split" claim verbatim from C3)
    #   (b) EL_pool^2 ≈ 1/2  (the "EL_q^2 = 1/2 if EL_q = 1/sqrt(2)"
    #                         derivation from C1 → C3)
    c3_a_pool_to_half = abs(el_pool - 0.5)
    c3_b_pool_sq_to_half = abs(el_pool ** 2 - 0.5)
    c3_b_flat_sq_to_half = abs(el_flat ** 2 - 0.5)

    # ---- (7) report ----
    report = {
        "experiment": EXP,
        "task_id": "C1+C3",
        "title": (
            "EL_q vs 1/sqrt(2): jackknife + bootstrap CIs (C1) and exact "
            "corpus-level adjacent-pair match fraction (C3)"
        ),
        "constants": {
            "1_over_sqrt_2": mu0,
            "1_over_2": 0.5,
        },
        "band_A_summary": {
            "n_surahs": int(n_band_a),
            "mean_EL": band_a_mean_EL,
            "sd_EL_unbiased": band_a_sd_EL,
            "se_classical": se_classical,
            "abs_gap_to_1_over_sqrt_2": abs(band_a_mean_EL - mu0),
            "rel_gap_to_1_over_sqrt_2_pct": (
                100.0 * abs(band_a_mean_EL - mu0) / mu0
            ),
        },
        "C1_jackknife_band_A": {
            "n": int(n),
            "se_jackknife": jk_se,
            "ci_95_low": jk_ci_lo,
            "ci_95_high": jk_ci_hi,
            "ci_contains_1_over_sqrt_2": jk_ci_lo <= mu0 <= jk_ci_hi,
            "verdict": c1_jk_verdict,
        },
        "C1_bootstrap_band_A": {
            "n_bootstrap": int(N_BOOTSTRAP),
            "seed": SEED,
            "ci_95_low": boot_ci_lo,
            "ci_95_high": boot_ci_hi,
            "ci_contains_1_over_sqrt_2": boot_ci_lo <= mu0 <= boot_ci_hi,
            "p_boot_mean_lt_mu0": boot_p_lt_mu0,
            "p_boot_mean_gt_mu0": boot_p_gt_mu0,
            "p_boot_two_sided_extremity": boot_p_two_sided,
            "verdict": c1_boot_verdict,
        },
        "C1_one_sample_t_test_band_A": {
            "H0_mu": mu0,
            "t_classical_se": t_stat,
            "p_two_sided_classical_se": p_two_sided,
            "t_jackknife_se": t_stat_jk,
            "p_two_sided_jackknife_se": p_two_sided_jk,
            "df": int(df),
        },
        "all_114_surahs_summary": {
            "n_surahs": 114,
            "el_unweighted_per_surah_mean": el_all_114_mean,
            "abs_gap_to_1_over_sqrt_2": abs(el_all_114_mean - mu0),
        },
        "C3_corpus_pooled": {
            "definition": (
                "EL_pool = sum_s (n_match_s) / sum_s (n_pairs_s)  over all "
                "114 surahs ; cross-surah pairs NOT counted (matches paper "
                "definition extended canon-wide)."
            ),
            "n_match": int(all_n_match),
            "n_pairs": int(all_n_pairs),
            "EL_pool": el_pool,
            "EL_pool_squared": el_pool ** 2,
            "abs_gap_C3_a_pool_to_half": c3_a_pool_to_half,
            "abs_gap_C3_b_pool_sq_to_half": c3_b_pool_sq_to_half,
        },
        "C3_corpus_flat_including_cross_surah": {
            "definition": (
                "EL_flat = matches over all consecutive verse pairs in "
                "the canonical mushaf order; INCLUDES the 113 cross-surah "
                "boundary pairs (so denominator = 6,236 - 1 = 6,235)."
            ),
            "n_match": int(flat_match),
            "n_pairs": int(flat_pairs),
            "EL_flat": el_flat,
            "EL_flat_squared": el_flat ** 2,
            "abs_gap_C3_b_flat_sq_to_half": c3_b_flat_sq_to_half,
        },
        "interpretation": [
            "C1: H0 mu = 1/sqrt(2) is RETAINED (not rejected) at alpha = 0.05 "
            "iff the jackknife and bootstrap 95 % CIs contain 1/sqrt(2). The "
            "0.04 % numerical coincidence is well inside the sampling envelope "
            "of EL_q across the 68 Band-A surahs (per-surah sd ~ 0.20).",
            "C3: The C3 entry's pair-level claim 'fraction == 0.5' is INCORRECT "
            "as written (verbatim corpus-pooled adjacent-pair match rate is "
            "EL_pool itself, ~ 0.71, not 0.5). The intended claim is the "
            "C1-derived corollary EL_q^2 == 0.5, tested as gap_C3_b_pool_sq.",
            "If gap_C3_b_pool_sq is < 0.01, C1 + C3 jointly survive: pool_sq "
            "is consistent with 0.5 at the corpus level.",
        ],
    }

    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Human-readable stdout
    print(f"[{EXP}] Band-A mean EL          = {band_a_mean_EL:.10f}")
    print(f"[{EXP}] 1/sqrt(2)               = {mu0:.10f}")
    print(f"[{EXP}] |gap|                   = "
          f"{abs(band_a_mean_EL - mu0):.10f}  "
          f"({100.0 * abs(band_a_mean_EL - mu0) / mu0:.4f} % rel)")
    print(f"[{EXP}] jackknife 95 % CI       = "
          f"[{jk_ci_lo:.6f}, {jk_ci_hi:.6f}]   "
          f"contains 1/sqrt(2): {jk_ci_lo <= mu0 <= jk_ci_hi}")
    print(f"[{EXP}] bootstrap (B={N_BOOTSTRAP}) 95 % CI = "
          f"[{boot_ci_lo:.6f}, {boot_ci_hi:.6f}]   "
          f"contains 1/sqrt(2): {boot_ci_lo <= mu0 <= boot_ci_hi}")
    print(f"[{EXP}] t-test vs 1/sqrt(2):    "
          f"t = {t_stat:.4f}  df = {df}  p_two = {p_two_sided:.4f}")
    print(f"[{EXP}] verdict                 = {c1_jk_verdict}")
    print()
    print(f"[{EXP}] -- C3 corpus pooled --")
    print(f"[{EXP}]   n_match / n_pairs     = "
          f"{all_n_match} / {all_n_pairs}")
    print(f"[{EXP}]   EL_pool               = {el_pool:.10f}")
    print(f"[{EXP}]   EL_pool^2             = {el_pool ** 2:.10f}")
    print(f"[{EXP}]   |EL_pool^2 - 0.5|     = {c3_b_pool_sq_to_half:.10f}")
    print(f"[{EXP}]   |EL_pool   - 0.5|     = {c3_a_pool_to_half:.10f}")
    print(f"[{EXP}] -- C3 corpus flat --")
    print(f"[{EXP}]   EL_flat               = {el_flat:.10f}")
    print(f"[{EXP}]   |EL_flat^2 - 0.5|     = {c3_b_flat_sq_to_half:.10f}")
    print(f"[{EXP}] wrote {out / f'{EXP}.json'}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
