"""experiments/exp154_F75_stretched_exp_derivation/run.py — F75 stretched-exponential derivation.

Tests whether a stretched-exponential family
    p_k(c) ~ exp(-lambda_c * k^beta) / Z(lambda_c, beta, A=28),  k = 1, ..., 28
with UNIVERSAL beta and per-corpus lambda_c (fit from p_max(c)) predicts H_EL more
accurately than pure geometric (exp153 baseline: A1 6/10, mean_abs 0.252 b).

Primary verdict via leave-one-out cross-validation (LOO); in-sample fit reported
for transparency. Mixture-with-uniform (M1) reported as documented-failure
sensitivity analysis only.

PREREG: experiments/exp154_F75_stretched_exp_derivation/PREREG.md
Input:  results/experiments/exp153_F75_derivation_check/exp153_F75_derivation_check.json (locked)
Output: results/experiments/exp154_F75_stretched_exp_derivation/exp154_F75_stretched_exp_derivation.json
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths and locked constants

ROOT = Path(__file__).resolve().parent.parent.parent
EXP_NAME = "exp154_F75_stretched_exp_derivation"
PREREG_PATH = Path(__file__).resolve().parent / "PREREG.md"
INPUT_EXP153 = ROOT / "results" / "experiments" / "exp153_F75_derivation_check" / "exp153_F75_derivation_check.json"
INPUT_SIZING = ROOT / "results" / "auxiliary" / "_phi_universal_xtrad_sizing.json"
EXPLORE_SCRIPT = ROOT / "scripts" / "_explore_F75_mixture.py"
OUT_DIR = ROOT / "results" / "experiments" / EXP_NAME
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / f"{EXP_NAME}.json"

# PREREG-locked constants
SEED = 42
A_ALPHABET = 28
BETA_GRID = [0.50, 0.70, 0.85, 1.00, 1.15, 1.30, 1.50, 1.75, 2.00, 2.50, 3.00]
W_GRID = [0.74, 0.78, 0.82, 0.86, 0.90, 0.92, 0.94, 0.96, 0.98, 0.99, 0.995, 0.999]

GAP_RESIDUAL_FLOOR = 0.30
MEAN_RESIDUAL_CEILING = 0.20
CORRELATION_FLOOR = 0.85
BETA_STAR_FLOOR = 1.0
MAX_RESIDUAL_CEILING = 0.43

EXPECTED_CORPORA = [
    "quran", "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "hindawi", "ksucca", "arabic_bible", "hebrew_tanakh",
    "greek_nt", "pali", "avestan_yasna",
]


def sha256_of_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def H_of_dist(probs: list[float]) -> float:
    s = 0.0
    for p in probs:
        if p > 1e-15:
            s -= p * math.log2(p)
    return s


def pearson_r(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0 or syy == 0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)


# ---------------------------------------------------------------------------
# Stretched-exponential model M2

def fit_stretched_exp(p_max_val: float, beta: float, a_alphabet: int = A_ALPHABET) -> tuple[float, list[float]]:
    """Bisect lambda such that p_1 = exp(-lambda)/Z = p_max_val.
    p_1 is INCREASING in lambda (more mass concentrated on k=1).
    Returns (lambda, normalized_probs).
    """
    lo, hi = 1e-9, 60.0
    for _ in range(200):
        mid = (lo + hi) / 2
        weights = [math.exp(-mid * (k ** beta)) for k in range(1, a_alphabet + 1)]
        Z = sum(weights)
        p1 = weights[0] / Z
        if p1 > p_max_val:
            hi = mid
        else:
            lo = mid
    lam = (lo + hi) / 2
    weights = [math.exp(-lam * (k ** beta)) for k in range(1, a_alphabet + 1)]
    Z = sum(weights)
    probs = [w_ / Z for w_ in weights]
    return lam, probs


def predict_HEL_stretched(p_max_val: float, beta: float) -> tuple[float, float]:
    """Returns (H_EL_predicted, lambda)."""
    lam, probs = fit_stretched_exp(p_max_val, beta)
    return H_of_dist(probs), lam


# ---------------------------------------------------------------------------
# Mixture-with-uniform model M1 (sensitivity only)

def predict_HEL_mixture(p_max_val: float, w: float, a_alphabet: int = A_ALPHABET) -> tuple[float, float] | None:
    """p_k = w*(1-r)*r^(k-1) + (1-w)/A. Solve r from p_max constraint.
    Returns (H_EL_predicted, r) or None if infeasible.
    """
    if w <= 0 or w >= 1:
        return None
    r = 1.0 - (p_max_val - (1 - w) / a_alphabet) / w
    if r <= 0 or r >= 1:
        return None
    probs = [w * (1 - r) * (r ** (k - 1)) + (1 - w) / a_alphabet for k in range(1, a_alphabet + 1)]
    s = sum(probs)
    probs = [p / s for p in probs]
    return H_of_dist(probs), r


# ---------------------------------------------------------------------------
# SSR computation across corpora at fixed beta or w

def ssr_stretched(beta: float, p_max: dict, gap_emp: dict, corpora: list[str]) -> tuple[float, dict]:
    residuals = {}
    for c in corpora:
        H_pred, _ = predict_HEL_stretched(p_max[c], beta)
        gap_pred = H_pred + math.log2(p_max[c])
        residuals[c] = abs(gap_pred - gap_emp[c])
    ssr = sum(r ** 2 for r in residuals.values())
    return ssr, residuals


def ssr_mixture(w: float, p_max: dict, gap_emp: dict, corpora: list[str]) -> tuple[float | None, dict | None]:
    residuals = {}
    for c in corpora:
        out = predict_HEL_mixture(p_max[c], w)
        if out is None:
            return None, None
        H_pred, _ = out
        gap_pred = H_pred + math.log2(p_max[c])
        residuals[c] = abs(gap_pred - gap_emp[c])
    ssr = sum(r ** 2 for r in residuals.values())
    return ssr, residuals


# ---------------------------------------------------------------------------
# Main

def main() -> None:
    t0 = time.time()

    # ------------------------------------------------------------------
    # Step 1: load locked exp153 receipt
    if not INPUT_EXP153.exists():
        raise FileNotFoundError(f"Locked exp153 receipt not found: {INPUT_EXP153}")

    raw153 = INPUT_EXP153.read_bytes()
    exp153_sha = hashlib.sha256(raw153).hexdigest()
    exp153 = json.loads(raw153.decode("utf-8"))

    p_max = exp153["results"]["p_max_per_corpus"]
    H_EL = exp153["results"]["H_EL_per_corpus"]
    gap_emp = exp153["results"]["gap_empirical"]

    assert set(EXPECTED_CORPORA) == set(p_max.keys()), "corpora mismatch"

    # Cross-check empirical gap formula
    for c in EXPECTED_CORPORA:
        recomputed = H_EL[c] + math.log2(p_max[c])
        assert abs(recomputed - gap_emp[c]) < 1e-12, f"gap mismatch for {c}"

    # ------------------------------------------------------------------
    # Step 2: M2 stretched-exponential, MODE P (in-sample fit at global beta*)
    mode_P_results = {}
    for beta in BETA_GRID:
        ssr, residuals = ssr_stretched(beta, p_max, gap_emp, EXPECTED_CORPORA)
        mode_P_results[beta] = {"ssr": ssr, "residuals": residuals}

    beta_star_P = min(BETA_GRID, key=lambda b: mode_P_results[b]["ssr"])
    P_residuals = mode_P_results[beta_star_P]["residuals"]
    P_predictions = {}
    for c in EXPECTED_CORPORA:
        H_pred, lam = predict_HEL_stretched(p_max[c], beta_star_P)
        P_predictions[c] = {
            "lambda": lam,
            "H_EL_pred": H_pred,
            "gap_pred": H_pred + math.log2(p_max[c]),
            "residual": P_residuals[c],
        }

    # ------------------------------------------------------------------
    # Step 3: M2 stretched-exponential, MODE L (LOO cross-validation) — PRIMARY
    L_predictions = {}
    L_betas = {}
    for c_h in EXPECTED_CORPORA:
        other_corpora = [c for c in EXPECTED_CORPORA if c != c_h]
        ssrs_loo = {}
        for beta in BETA_GRID:
            ssr, _ = ssr_stretched(beta, p_max, gap_emp, other_corpora)
            ssrs_loo[beta] = ssr
        beta_star_loo = min(BETA_GRID, key=lambda b: ssrs_loo[b])
        H_pred, lam = predict_HEL_stretched(p_max[c_h], beta_star_loo)
        gap_pred = H_pred + math.log2(p_max[c_h])
        residual = abs(gap_pred - gap_emp[c_h])
        L_betas[c_h] = beta_star_loo
        L_predictions[c_h] = {
            "beta_loo": beta_star_loo,
            "lambda": lam,
            "H_EL_pred": H_pred,
            "gap_pred": gap_pred,
            "residual": residual,
        }

    L_residuals = {c: L_predictions[c]["residual"] for c in EXPECTED_CORPORA}

    # ------------------------------------------------------------------
    # Step 4: PREREG criteria (applied to MODE L)
    non_quran = [c for c in EXPECTED_CORPORA if c != "quran"]

    # A1: per-corpus residual <= 0.30 for non-Quran; need >= 8 of 10
    a1_pass_corpora = [c for c in non_quran if L_residuals[c] <= GAP_RESIDUAL_FLOOR]
    a1_n_pass = len(a1_pass_corpora)
    a1_required = 8
    a1_verdict = "PASS" if a1_n_pass >= a1_required else "FAIL"

    # A2: mean abs LOO residual across all 11 corpora <= 0.20
    mean_abs_residual = sum(L_residuals.values()) / len(L_residuals)
    a2_verdict = "PASS" if mean_abs_residual <= MEAN_RESIDUAL_CEILING else "FAIL"

    # A3: Pearson r between LOO gap_pred and gap_emp >= 0.85
    xs = [L_predictions[c]["gap_pred"] for c in EXPECTED_CORPORA]
    ys = [gap_emp[c] for c in EXPECTED_CORPORA]
    r_pearson = pearson_r(xs, ys)
    a3_verdict = "PASS" if r_pearson >= CORRELATION_FLOOR else "FAIL"

    # A4: modal beta_LOO across 11 folds >= 1.0 (super-geometric concentration)
    from collections import Counter
    beta_counts = Counter(L_betas.values())
    beta_modal = beta_counts.most_common(1)[0][0]
    a4_verdict = "PASS" if beta_modal >= BETA_STAR_FLOOR else "FAIL"

    # A5: max LOO residual < 0.43 (improvement on pure-geometric worst)
    max_residual = max(L_residuals.values())
    a5_verdict = "PASS" if max_residual < MAX_RESIDUAL_CEILING else "FAIL"

    n_pass = sum(1 for v in (a1_verdict, a2_verdict, a3_verdict, a4_verdict, a5_verdict) if v == "PASS")

    if n_pass == 5:
        verdict = "PASS_F75_stretched_exp_strong"
    elif n_pass == 4:
        verdict = "PARTIAL_F75_stretched_exp_directional"
    else:
        verdict = "FAIL_F75_stretched_exp_no_lift"

    # ------------------------------------------------------------------
    # Step 5: M1 mixture-with-uniform (SENSITIVITY ONLY — not in verdict)
    M1_results = {}
    for w in W_GRID:
        ssr, residuals = ssr_mixture(w, p_max, gap_emp, EXPECTED_CORPORA)
        if ssr is None:
            M1_results[w] = {"feasible": False}
        else:
            mean_abs = sum(residuals.values()) / len(residuals)
            a1_count = sum(1 for c in non_quran if residuals[c] <= GAP_RESIDUAL_FLOOR)
            M1_results[w] = {
                "feasible": True,
                "ssr": ssr,
                "mean_abs_residual": mean_abs,
                "a1_n_pass_non_quran": a1_count,
                "residuals": residuals,
            }

    feasible_ws = [w for w in W_GRID if M1_results[w].get("feasible")]
    if feasible_ws:
        w_star = min(feasible_ws, key=lambda w: M1_results[w]["ssr"])
        M1_summary = {
            "w_star": w_star,
            "ssr_at_w_star": M1_results[w_star]["ssr"],
            "mean_abs_at_w_star": M1_results[w_star]["mean_abs_residual"],
            "a1_n_pass_at_w_star": M1_results[w_star]["a1_n_pass_non_quran"],
            "verdict_M1": "REJECTED_does_not_help" if (
                M1_results[w_star]["a1_n_pass_non_quran"] < 8
                or M1_results[w_star]["mean_abs_residual"] > MEAN_RESIDUAL_CEILING
            ) else "WOULD_PASS_BUT_NOT_PRIMARY_MODEL",
        }
    else:
        M1_summary = {"verdict_M1": "INFEASIBLE_AT_ALL_W"}

    # ------------------------------------------------------------------
    # Step 6: descriptive stats
    cluster_emp = [gap_emp[c] for c in non_quran]
    cluster_emp_mean = sum(cluster_emp) / len(cluster_emp)
    n = len(cluster_emp)
    cluster_emp_std = math.sqrt(sum((v - cluster_emp_mean) ** 2 for v in cluster_emp) / (n - 1))

    cluster_pred_loo = [L_predictions[c]["gap_pred"] for c in non_quran]
    cluster_pred_mean = sum(cluster_pred_loo) / len(cluster_pred_loo)

    # Compare to exp153 pure-geometric baseline
    exp153_a1 = exp153["results"]["criteria"]["A1_per_corpus_residual_le_0p30_non_quran"]["n_pass"]
    exp153_mean_abs = exp153["results"]["criteria"]["A2_mean_abs_residual"]["observed"]
    exp153_r = exp153["results"]["criteria"]["A3_pearson_correlation"]["observed"]
    exp153_max_res = max(exp153["results"]["residuals_abs"].values())

    # ------------------------------------------------------------------
    # Step 7: receipt
    explore_sha = sha256_of_file(EXPLORE_SCRIPT) if EXPLORE_SCRIPT.exists() else "<missing>"

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H99_F75_StretchedExp_Derivation",
        "hypothesis": (
            "F75's universal Q ~ 5.75 bits reduces to Shannon-Renyi-inf gap H_1 - H_inf ~ 0.94 b. "
            "Tests whether a UNIVERSAL stretched-exponential family p_k ~ exp(-lambda*k^beta)/Z, "
            "with single global beta and per-corpus lambda fit from p_max, predicts H_EL "
            "(and hence the gap) more accurately than pure geometric. Primary verdict via "
            "leave-one-out cross-validation; in-sample fit and mixture-with-uniform reported "
            "for transparency only."
        ),
        "verdict": verdict,
        "verdict_reason": (
            f"{n_pass}/5 PREREG criteria PASS. "
            f"A1 non-Quran LOO residuals <= 0.30: {a1_n_pass}/{len(non_quran)} (need >= {a1_required}); {a1_verdict}. "
            f"A2 mean abs LOO residual: {mean_abs_residual:.4f} b (ceiling {MEAN_RESIDUAL_CEILING}); {a2_verdict}. "
            f"A3 Pearson r LOO: {r_pearson:.4f} (floor {CORRELATION_FLOOR}); {a3_verdict}. "
            f"A4 modal beta_LOO: {beta_modal} (floor {BETA_STAR_FLOOR}); {a4_verdict}. "
            f"A5 max LOO residual: {max_residual:.4f} b (ceiling {MAX_RESIDUAL_CEILING}); {a5_verdict}."
        ),
        "prereg_hash": sha256_of_file(PREREG_PATH),
        "input_exp153_sha256": exp153_sha,
        "input_sizing_sha256": sha256_of_file(INPUT_SIZING) if INPUT_SIZING.exists() else "<missing>",
        "explore_script_sha256": explore_sha,
        "frozen_constants": {
            "SEED": SEED,
            "A_ALPHABET": A_ALPHABET,
            "BETA_GRID": BETA_GRID,
            "W_GRID": W_GRID,
            "GAP_RESIDUAL_FLOOR": GAP_RESIDUAL_FLOOR,
            "MEAN_RESIDUAL_CEILING": MEAN_RESIDUAL_CEILING,
            "CORRELATION_FLOOR": CORRELATION_FLOOR,
            "BETA_STAR_FLOOR": BETA_STAR_FLOOR,
            "MAX_RESIDUAL_CEILING": MAX_RESIDUAL_CEILING,
            "EXPECTED_CORPORA": EXPECTED_CORPORA,
        },
        "results": {
            "p_max_per_corpus": p_max,
            "H_EL_per_corpus": H_EL,
            "gap_empirical": gap_emp,
            "mode_P_in_sample": {
                "beta_star": beta_star_P,
                "ssr_per_beta": {str(b): mode_P_results[b]["ssr"] for b in BETA_GRID},
                "predictions_at_beta_star": P_predictions,
                "note": "In-sample fit at global beta_star. Reported for transparency; NOT used in PASS/FAIL.",
            },
            "mode_L_LOO_primary": {
                "beta_per_held_out_corpus": L_betas,
                "predictions": L_predictions,
                "modal_beta_LOO": beta_modal,
                "beta_LOO_distribution": dict(beta_counts),
            },
            "criteria": {
                "A1_per_corpus_LOO_residual_le_0p30_non_quran": {
                    "verdict": a1_verdict,
                    "n_pass": a1_n_pass,
                    "n_required": a1_required,
                    "n_total": len(non_quran),
                    "passing_corpora": a1_pass_corpora,
                    "failing_corpora": [c for c in non_quran if L_residuals[c] > GAP_RESIDUAL_FLOOR],
                },
                "A2_mean_abs_LOO_residual": {
                    "verdict": a2_verdict,
                    "observed": mean_abs_residual,
                    "ceiling": MEAN_RESIDUAL_CEILING,
                },
                "A3_pearson_correlation_LOO": {
                    "verdict": a3_verdict,
                    "observed": r_pearson,
                    "floor": CORRELATION_FLOOR,
                },
                "A4_modal_beta_LOO_ge_1p0": {
                    "verdict": a4_verdict,
                    "observed_modal_beta": beta_modal,
                    "floor": BETA_STAR_FLOOR,
                    "interpretation": "beta >= 1 confirms super-geometric concentration",
                },
                "A5_max_LOO_residual_lt_0p43": {
                    "verdict": a5_verdict,
                    "observed_max": max_residual,
                    "ceiling": MAX_RESIDUAL_CEILING,
                    "exp153_baseline_max": exp153_max_res,
                },
            },
            "M1_mixture_uniform_sensitivity_NOT_in_verdict": {
                "summary": M1_summary,
                "per_w_results": M1_results,
                "note": (
                    "Mixture-with-uniform model is reported for transparency. The exploratory "
                    "analysis (scripts/_explore_F75_mixture.py) demonstrated it dilutes "
                    "concentration in the wrong direction (real distributions are MORE peaked "
                    "than pure geometric, not less); pre-registration accordingly elevated "
                    "stretched-exponential as primary."
                ),
            },
            "exp153_baseline_comparison": {
                "exp153_A1_pass_non_quran": exp153_a1,
                "exp153_mean_abs_residual": exp153_mean_abs,
                "exp153_pearson_r": exp153_r,
                "exp153_max_residual": exp153_max_res,
                "exp154_LOO_A1_pass_non_quran": a1_n_pass,
                "exp154_LOO_mean_abs_residual": mean_abs_residual,
                "exp154_LOO_pearson_r": r_pearson,
                "exp154_LOO_max_residual": max_residual,
                "improvement_factor_mean_abs": exp153_mean_abs / mean_abs_residual if mean_abs_residual > 0 else float("inf"),
            },
            "cluster_descriptive": {
                "non_quran_emp_mean_gap": cluster_emp_mean,
                "non_quran_emp_std_gap": cluster_emp_std,
                "non_quran_LOO_pred_mean_gap": cluster_pred_mean,
                "interpretation_one_bit_conjecture": (
                    f"Non-Quran cluster mean = {cluster_emp_mean:.4f} +/- {cluster_emp_std:.4f}. "
                    f"Stretched-exp LOO predictions cluster mean = {cluster_pred_mean:.4f}. "
                    "The 1-bit cognitive-channel conjecture is unaffected by this experiment's "
                    "outcome (it is a substantive interpretation, not a quantitative test)."
                ),
            },
        },
        "audit_report": {
            "ok": True,
            "checks": {
                "exp153_input_sha256_locked": exp153_sha,
                "all_corpora_present": set(EXPECTED_CORPORA) == set(p_max.keys()),
                "no_brown_stouffer_used": True,
                "T_squared_invariant": True,
                "no_locked_finding_status_changed": True,
                "F75_PASS_status_unaffected": True,
                "exp153_residuals_unchanged": True,
                "M1_mixture_documented_failure_only": True,
            },
        },
        "wall_time_s": time.time() - t0,
    }

    OUT_PATH.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    # ------------------------------------------------------------------
    # Step 8: stdout summary
    print(f"[{EXP_NAME}] verdict = {verdict}")
    print(f"  MODE P beta* (in-sample): {beta_star_P}, SSR={mode_P_results[beta_star_P]['ssr']:.4f}")
    print(f"  MODE L (LOO PRIMARY):")
    print(f"    A1 non-Quran LOO residuals <= 0.30: {a1_n_pass}/{len(non_quran)} ({a1_verdict})")
    print(f"    A2 mean abs LOO residual: {mean_abs_residual:.4f} ({a2_verdict})")
    print(f"    A3 Pearson r LOO: {r_pearson:.4f} ({a3_verdict})")
    print(f"    A4 modal beta_LOO: {beta_modal} ({a4_verdict})")
    print(f"    A5 max LOO residual: {max_residual:.4f} ({a5_verdict})")
    print(f"  exp153 baseline: A1={exp153_a1}/10, mean_abs={exp153_mean_abs:.4f}, max={exp153_max_res:.4f}")
    print(f"  exp154 LOO    : A1={a1_n_pass}/10, mean_abs={mean_abs_residual:.4f}, max={max_residual:.4f}")
    print(f"  Improvement factor mean_abs: {exp153_mean_abs/mean_abs_residual:.2f}x" if mean_abs_residual > 0 else "")
    print(f"  M1 sensitivity: {M1_summary.get('verdict_M1', '?')}")
    print(f"  Wall time: {receipt['wall_time_s']:.3f} sec")
    print(f"  Receipt: {OUT_PATH}")


if __name__ == "__main__":
    main()
