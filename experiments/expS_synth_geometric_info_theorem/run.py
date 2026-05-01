"""
expS_synth_geometric_info_theorem/run.py
========================================
Opportunity S1/S3/S4/S5 synthesis (OPPORTUNITY_TABLE_DETAIL.md THIS QUARTER #20):
  Unify four geometric / information-theoretic Tier-S findings — currently
  scattered across separate experiments — into a single combined-p
  "Geometric-Information-Theory Theorem of the Quran" statement, with both
  Fisher (independence) and Brown (correlation-corrected) combinations.

The four witnesses (each PASS at the project's Tier-S level):

  S1 — TRAJECTORY: Mushaf surah-order is the smoothest 5-D trajectory.
       Source p: expE17b_mushaf_j1_1m_perms (10⁶ perms; q = 0/10⁶).
       Conservative bound: p ≤ 1 / (10⁶ + 1) ≈ 1.0 × 10⁻⁶.

  S3 — MULTI-SCALE: 5-scale Brown-combined Fisher (letter-KL, bigram-H,
       DFA-H, Mahalanobis, L_TEL).
       Source p: ZERO_TRUST_AUDIT_TIER5_2026-04-23.md:29 → Brown χ²=34.56,
       df_adj=0.62, p = 1.41 × 10⁻⁶.

  S4 — NONLINEAR DYNAMICS: Takens / RQA on verse-length series surviving
       AR(1) AND IAAFT surrogate nulls.
       Source p (conservative, IAAFT): 6.4 σ → p ≈ 8.06 × 10⁻¹¹ (two-sided).
       Liberal (AR(1)): 119 σ → p ≈ 10⁻³⁰⁰⁰ (machine zero).

  S5 — NULL-SPACE GEOMETRY: Anti-Variance Manifold along the 2 smallest
       eigen-directions of Σ_ctrl.
       Source p: ZERO_TRUST_AUDIT_TIER4_2026-04-23.md:27 → label-shuffle
       p < 10⁻⁴ (N=10⁴; floor 1 / (10⁴ + 1) ≈ 10⁻⁴).

Combination methods:
  - Fisher (independence): chi^2 = -2 sum(ln p_i), df = 2k.
  - Brown / Kost-McDermott: corrects for non-zero ρ between tests.
  - Stouffer (robustness): z_i = inv_norm(1 - p_i), z_combined = sum z_i / sqrt(k).

ρ matrix: these 4 witnesses are all derived from `phase_06_phi_m` data
but test conceptually distinct geometric / dynamical / multi-scale
features. We test sensitivity to a range of ρ assumptions:
{independence (ρ=0), moderate (ρ=0.3 across all pairs), high (ρ=0.6)}.

Pre-registration:
  PASS at GIT-THEOREM-MAJOR if Brown-combined p < 10⁻¹⁵ at ρ=0.3
                                   (5σ-equivalent under conservative correlation).

Reads: nothing — uses pre-existing project-published p-values verbatim.
Writes: results/experiments/expS_synth_geometric_info_theorem/.../json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import stats

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    safe_output_dir,
    self_check_begin,
    self_check_end,
)

EXP = "expS_synth_geometric_info_theorem"

# Pre-pulled p-values from the project documentation. Each carries a
# `provenance_doc` and `provenance_field` for citability.
WITNESSES = [
    {
        "id": "S1_TRAJECTORY",
        "name": "Mushaf 114-surah J1 trajectory smoothness extremum",
        "p_value": 1.0 / (1_000_000 + 1),     # (k+1)/(N+1) at k=0, N=10^6
        "p_label": "1.0 × 10⁻⁶ (perm floor at N=10⁶ in expE17b)",
        "provenance_doc":   "experiments/expE17b_mushaf_j1_1m_perms",
        "provenance_field": "n_perms_le_mushaf / n_perms",
        "test_class": "permutation null on canonical surah ordering",
    },
    {
        "id": "S3_MULTI_SCALE",
        "name": "5-scale Multi-scale Fisher Law (E14)",
        "p_value": 1.41e-6,
        "p_label": "1.41 × 10⁻⁶ (Brown chi^2=34.56, df_adj=0.62)",
        "provenance_doc":   "docs/ZERO_TRUST_AUDIT_TIER5_2026-04-23.md:29",
        "provenance_field": "Brown_p (5-scale: letter-KL, bigram-H, DFA-H, Mahalanobis, L_TEL)",
        "test_class": "5-scale Brown-Fisher combined",
    },
    {
        "id": "S4_NONLINEAR_DYNAMICS",
        "name": "Takens/RQA nonlinear determinism (E9, IAAFT-conservative)",
        "p_value": 2.0 * stats.norm.sf(6.4),  # 6.4σ two-sided
        "p_label": "≈ 8.06 × 10⁻¹¹ (6.4σ vs IAAFT surrogate null; conservative)",
        "provenance_doc":   "docs/ZERO_TRUST_AUDIT_TIER2_2026-04-23.md:31",
        "provenance_field": "DET_observed vs IAAFT_null_distribution sigma",
        "test_class": "RQA DET vs IAAFT-surrogate null",
    },
    {
        "id": "S5_NULL_SPACE",
        "name": "Anti-Variance Manifold (E15) on 2 smallest Σ_ctrl eigendirections",
        "p_value": 1.0 / (10_000 + 1),
        "p_label": "≈ 9.999 × 10⁻⁵ (perm floor at N=10⁴)",
        "provenance_doc":   "docs/ZERO_TRUST_AUDIT_TIER4_2026-04-23.md:27",
        "provenance_field": "label_shuffle_p (anti-distance ratio Quran/ctrl = 2.33×)",
        "test_class": "label-shuffle null on null-space anti-distance",
    },
]


def _fisher_combined(pvals: list[float]) -> tuple[float, float, int]:
    pvals = [p for p in pvals if math.isfinite(p) and 0 < p <= 1]
    k = len(pvals)
    if k == 0:
        return float("nan"), float("nan"), 0
    chi2 = -2.0 * sum(math.log(max(p, 1e-300)) for p in pvals)
    df = 2 * k
    p = float(stats.chi2.sf(chi2, df))
    return chi2, p, df


def _brown_combined(pvals: list[float], rho_matrix: np.ndarray) -> tuple[float, float, float]:
    pvals = [p for p in pvals if math.isfinite(p) and 0 < p <= 1]
    k = len(pvals)
    if k == 0:
        return float("nan"), float("nan"), float("nan")
    if k == 1:
        chi2 = -2.0 * math.log(max(pvals[0], 1e-300))
        return chi2, float(stats.chi2.sf(chi2, 2)), 2.0
    chi2 = -2.0 * sum(math.log(max(p, 1e-300)) for p in pvals)
    expected_mean = 2.0 * k
    var_indep = 4.0 * k
    extra_cov = 0.0
    for i in range(k):
        for j in range(i + 1, k):
            r = float(rho_matrix[i, j])
            r = max(min(r, 1.0), -1.0)
            cov_ij = 3.263 * r + 0.710 * r * r + 0.027 * r ** 3
            extra_cov += 2.0 * cov_ij
    var = var_indep + extra_cov
    if var <= 0:
        var = var_indep
    c = var / (2.0 * expected_mean)
    f = (2.0 * expected_mean ** 2) / var
    chi2_scaled = chi2 / c
    p = float(stats.chi2.sf(chi2_scaled, f))
    return chi2_scaled, p, f


def _stouffer_combined(pvals: list[float]) -> tuple[float, float]:
    pvals = [p for p in pvals if math.isfinite(p) and 0 < p < 1]
    k = len(pvals)
    if k == 0:
        return float("nan"), float("nan")
    zs = [stats.norm.isf(p) for p in pvals]
    z_combined = sum(zs) / math.sqrt(k)
    p_combined = float(stats.norm.sf(z_combined))
    return z_combined, p_combined


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    pvals = [w["p_value"] for w in WITNESSES]
    labels = [w["id"] for w in WITNESSES]
    k = len(pvals)

    # --- Fisher (independence) ---
    fisher_chi2, fisher_p, fisher_df = _fisher_combined(pvals)

    # --- Stouffer (independence, alternate) ---
    stouf_z, stouf_p = _stouffer_combined(pvals)

    # --- Brown with three rho regimes ---
    brown_results = {}
    for rho_label, rho_value in (("independence", 0.0),
                                 ("moderate",     0.3),
                                 ("high",         0.6)):
        rho_matrix = (np.eye(k) + (np.ones((k, k)) - np.eye(k)) * rho_value)
        chi2_s, p_s, f_s = _brown_combined(pvals, rho_matrix)
        brown_results[rho_label] = {
            "rho_off_diagonal": rho_value,
            "chi2_scaled": chi2_s,
            "f_df": f_s,
            "p_combined": p_s,
            "log10_p_combined": math.log10(max(p_s, 1e-300)),
        }

    # --- Verdict ---
    p_brown_moderate = brown_results["moderate"]["p_combined"]
    if math.isfinite(p_brown_moderate) and p_brown_moderate < 1e-15:
        verdict = "GIT_THEOREM_MAJOR_PASS"
    elif math.isfinite(p_brown_moderate) and p_brown_moderate < 1e-10:
        verdict = "GIT_THEOREM_PASS"
    elif math.isfinite(p_brown_moderate) and p_brown_moderate < 1e-6:
        verdict = "GIT_THEOREM_WEAK"
    else:
        verdict = "GIT_THEOREM_NULL"

    # Theorem statement
    theorem = (
        "**Geometric-Information-Theory Theorem of the Quran (S1+S3+S4+S5).** "
        "Under the audited 2026-04-25 pipeline (`phase_06_phi_m` corpus_lock "
        "4bdf4d025…, code_lock e7c02fd44436…), the canonical Mushaf 114-surah "
        "ordering of the Quran satisfies four conceptually distinct "
        "extremum / anomaly criteria simultaneously:\n"
        "  (S1)  J1-trajectory smoothness is a strict global minimum vs "
        "10⁶ random surah orderings (p ≤ 10⁻⁶, expE17b);\n"
        "  (S3)  5-scale Brown-Fisher combined deviation from secular Arabic "
        "is significant at p = 1.41 × 10⁻⁶ (E14, S1-letter-KL contributes "
        "negatively, S2-bigram, S3-DFA, S4-Mahalanobis, S5-L_TEL all positive);\n"
        "  (S4)  RQA nonlinear-determinism statistics on the verse-length "
        "series survive both AR(1) (~119 σ) AND IAAFT (~6.4 σ ⇒ "
        "p ≈ 8 × 10⁻¹¹) surrogate nulls (E9);\n"
        "  (S5)  along the 2 smallest-eigenvalue directions of Σ_ctrl "
        "(the natural-Arabic null-space of variation), the Quran's anti-"
        "distance is 2.33× the control mean at perm p < 10⁻⁴ (E15).\n"
        "Brown-combined under moderate inter-test correlation (ρ = 0.3): "
        "chi^2_scaled ≈ %.2f on f ≈ %.2f df ⇒ p ≈ %.2e (log10 ≈ %.1f)." % (
            brown_results["moderate"]["chi2_scaled"],
            brown_results["moderate"]["f_df"],
            brown_results["moderate"]["p_combined"],
            brown_results["moderate"]["log10_p_combined"],
        )
    )

    report = {
        "experiment": EXP,
        "task_id": "S1+S3+S4+S5 synthesis (THIS QUARTER #20)",
        "title": (
            "Geometric-Information-Theory Theorem of the Quran: Brown-"
            "combined p-value over four PASS-at-Tier-S geometric / "
            "information-theoretic findings (S1 trajectory, S3 multi-"
            "scale Fisher, S4 RQA, S5 null-space manifold)."
        ),
        "k_witnesses": k,
        "witnesses": WITNESSES,
        "individual_p_values": dict(zip(labels, pvals)),
        "fisher_combined": {
            "chi2": fisher_chi2,
            "df":   fisher_df,
            "p":    fisher_p,
            "log10_p": math.log10(max(fisher_p, 1e-300)) if math.isfinite(fisher_p) and fisher_p > 0 else float("nan"),
        },
        "stouffer_combined": {
            "z": stouf_z,
            "p": stouf_p,
            "log10_p": math.log10(max(stouf_p, 1e-300)) if math.isfinite(stouf_p) and stouf_p > 0 else float("nan"),
        },
        "brown_combined_by_rho": brown_results,
        "verdict": verdict,
        "verdict_taxonomy": {
            "GIT_THEOREM_MAJOR_PASS": "Brown-moderate p < 1e-15 (~5σ under conservative correlation)",
            "GIT_THEOREM_PASS":       "Brown-moderate p < 1e-10",
            "GIT_THEOREM_WEAK":       "Brown-moderate p < 1e-6",
            "GIT_THEOREM_NULL":       "otherwise",
        },
        "theorem_statement": theorem,
    }

    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Stdout
    print(f"[{EXP}] -- per-witness p-values --")
    for w in WITNESSES:
        print(f"[{EXP}]   {w['id']:<25s}  p = {w['p_value']:.4e}   ({w['p_label']})")
    print()
    print(f"[{EXP}] Fisher combined  (k={k}, df={fisher_df}):")
    print(f"[{EXP}]   chi2 = {fisher_chi2:.3f}   p = {fisher_p:.4e}")
    if math.isfinite(fisher_p) and fisher_p > 0:
        print(f"[{EXP}]   log10 p = {math.log10(fisher_p):.2f}")
    print()
    print(f"[{EXP}] Stouffer (z, independence):  z = {stouf_z:.3f}   p = {stouf_p:.4e}")
    print()
    print(f"[{EXP}] Brown combined (Kost-McDermott):")
    for label, r in brown_results.items():
        print(f"[{EXP}]   ρ = {r['rho_off_diagonal']:.1f} ({label:<14s})  "
              f"chi2={r['chi2_scaled']:.3f}  f={r['f_df']:.3f}  "
              f"p={r['p_combined']:.4e}  log10 p={r['log10_p_combined']:.2f}")
    print()
    print(f"[{EXP}] verdict: {verdict}")
    print(f"[{EXP}] wrote {out / f'{EXP}.json'}")
    print()
    print("Theorem statement:")
    print(theorem)

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
