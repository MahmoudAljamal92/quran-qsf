"""exp180 — F90 = F86 closed-form Lagrangian + 2-opt KKT analysis.

Escalates F86 from 'empirical Pareto-optimum' to 'analytical 2-opt KKT extremum'
by deriving the Mushaf's implicit Lagrange multiplier lambda* and verifying that
Mushaf satisfies the local KKT conditions of the constrained optimisation

    minimise  L(sigma) = sum of adjacency distances
    subject to  diff(sigma) = mean_classical_d - mean_nonclassical_d  >=  delta_target

for any delta_target in the observed Mushaf interval.

Method:
  1. For the fixed 114-surah feature set (F1_det, 28-D, locked per exp176/F81),
     compute the Mushaf's L and diff exactly as F81/F82 do.

  2. Enumerate all C(113, 2) = 6,328 possible 2-opt swaps from the Mushaf tour.
     For each swap (i, j) compute (ΔL, Δdiff) analytically:
         ΔL   = [d(σ_i, σ_j) + d(σ_{i+1}, σ_{j+1})]
                - [d(σ_i, σ_{i+1}) + d(σ_j, σ_{j+1})]
         Δdiff = f(Δd_i, Δd_j, is_classical(i), is_classical(j))
     where f accounts for the per-slot weight in diff (1/K_c on classical
     slots, -1/K_nc on non-classical slots).

  3. Classify each swap:
       dominating_both  : ΔL < 0 AND Δdiff > 0  (should be empty for Pareto-opt)
       dominated_both   : ΔL > 0 AND Δdiff < 0
       trade-off        : (ΔL < 0 AND Δdiff < 0) OR (ΔL > 0 AND Δdiff > 0)
       neutral          : either Δ == 0

  4. If #dominating_both == 0, the Mushaf is **2-opt Pareto-locally-optimal**.
     Derive the KKT Lagrange multiplier range:
         λ_lower = sup_{swaps with Δdiff > 0 and ΔL > 0} (ΔL / Δdiff)
                  -> highest λ at which we still reject a diff-increasing swap
         λ_upper = inf_{swaps with Δdiff < 0 and ΔL < 0} (ΔL / Δdiff)
                  -> lowest λ at which we still reject a diff-decreasing swap
     If λ_lower <= λ_upper, the closed-form KKT multiplier is λ* ∈ [λ_lower, λ_upper].

  5. Report the interval, and test whether the empirical F86 Pareto point is
     analytically consistent with this multiplier.

This converts F86 from 'Mushaf is empirically Pareto-optimal' to the stronger
claim: 'Mushaf is a 2-opt KKT stationary point of the constrained optimisation
L - λ·diff for a specific closed-form interval of Lagrange multipliers λ*.'
"""
from __future__ import annotations
import io
import json
import sys
from collections import Counter
from pathlib import Path
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"
OUT_DIR = ROOT / "results" / "experiments" / "exp180_F86_lagrangian_KKT"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ARABIC_LETTERS = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
ARABIC_LETTERS_SET = set(ARABIC_LETTERS)
MEDINAN = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 55, 57, 58, 59, 60,
           61, 62, 63, 64, 65, 66, 76, 98, 99, 110}
# Locked 17 classical-pair ADJACENCY-slot indices (0-indexed, on the Mushaf tour)
CLASSICAL_SLOTS = [1, 7, 54, 66, 72, 74, 76, 80, 82, 86, 90, 92, 98, 102, 104, 110, 112]


def load_F1_det():
    s = {i: [] for i in range(1, 115)}
    for line in DATA.read_text(encoding="utf-8").splitlines():
        x = line.split("|", 2)
        if len(x) < 3 or not x[0].strip().isdigit():
            continue
        k = int(x[0])
        if 1 <= k <= 114:
            s[k].append(x[2].strip())
    F1 = np.zeros((114, 28))
    Nlet = np.zeros(114)
    for i in range(1, 115):
        at = "".join("".join(c for c in v if c in ARABIC_LETTERS_SET) for v in s[i])
        n = len(at)
        Nlet[i - 1] = n
        if n > 0:
            counts = Counter(at)
            F1[i - 1] = np.array([counts.get(c, 0) / n for c in ARABIC_LETTERS])
    logN = np.log(Nlet)
    md = np.array([1 if (i + 1) in MEDINAN else 0 for i in range(114)])
    X = np.column_stack([np.ones(114), logN, logN**2, logN**3, md])
    F1_det = np.zeros_like(F1)
    for k in range(28):
        b = np.linalg.lstsq(X, F1[:, k], rcond=None)[0]
        F1_det[:, k] = F1[:, k] - X @ b
    return F1_det


def compute_slot_weights(K_total: int, classical_slots: list[int]) -> np.ndarray:
    """Weight vector w[k] such that diff = sum_k w[k] * d[k].
    
    K_total = 113 (number of adjacency slots).
    w[k] = 1/K_c  if k in classical, -1/K_nc otherwise.
    """
    K_c = len(classical_slots)
    K_nc = K_total - K_c
    w = np.full(K_total, -1.0 / K_nc)
    for k in classical_slots:
        w[k] = 1.0 / K_c
    return w


def main():
    print("=" * 72)
    print("exp180 — F90 = Closed-form Lagrangian KKT for Mushaf Pareto position")
    print("=" * 72)

    F1_det = load_F1_det()
    D = np.linalg.norm(F1_det[:, None, :] - F1_det[None, :, :], axis=-1)
    # Mushaf tour: identity permutation on 114 surahs
    sigma = np.arange(114)  # σ[k] = surah index - 1
    K_total = 113  # number of adjacency slots
    w = compute_slot_weights(K_total, CLASSICAL_SLOTS)

    # Current adjacency distances d_k = D[σ[k], σ[k+1]]
    d = np.array([D[sigma[k], sigma[k+1]] for k in range(K_total)])
    L_mushaf = float(d.sum())
    diff_mushaf = float(np.sum(w * d))
    print(f"\n# Mushaf baseline:")
    print(f"  L    = {L_mushaf:.6f}")
    print(f"  diff = {diff_mushaf:+.6f}")
    print(f"  #classical slots K_c = {len(CLASSICAL_SLOTS)}, w_c = {1/len(CLASSICAL_SLOTS):.6f}")
    print(f"  #non-class slots K_nc = {K_total - len(CLASSICAL_SLOTS)}, w_nc = {-1/(K_total - len(CLASSICAL_SLOTS)):.6f}")

    # Enumerate all 2-opt swaps (i, j) with 0 <= i < j <= K_total - 1 (i.e., i < j ≤ 112)
    # The 2-opt swap reverses the sub-path σ[i+1..j]. Only positions i and j
    # change their adjacency distance.
    #
    # If j < K_total - 1 (i.e., j < 112), the j-edge goes to σ[j+1]. If j == 112,
    # there is no j-edge (it's the last position). We require j <= K_total - 1
    # = 112, and the swap changes edge i (between σ[i] and σ[i+1]) and edge j
    # (between σ[j] and σ[j+1]). For j = 112, edge j doesn't exist, so we need
    # i < j < K_total => j <= 111.

    # Important: a 2-opt swap at (i, j) reverses the sub-path σ[i+1..j].
    # This means:
    #   - Slot i gets new distance D[σ[i], σ[j]] (was d[i] = D[σ[i], σ[i+1]])
    #   - Slot j gets new distance D[σ[i+1], σ[j+1]] (was d[j] = D[σ[j], σ[j+1]])
    #   - For slots k ∈ (i, j) (strictly interior), the NEW distance at slot k
    #     equals the OLD distance at slot (i+j-k) — the mirror position in the
    #     reversed segment. Since d is symmetric, the SUM over interior slots
    #     is preserved (so ΔL depends only on the two cut-edges), but the
    #     DIFF statistic IS affected because w[k] (classical/non-classical)
    #     differs across the segment.
    #
    # Vectorised Δ-computation over all C(113, 2) = 6328 swaps:
    records = []
    n_swaps = 0
    for i in range(K_total - 1):  # i = 0..111
        for j in range(i + 1, K_total):  # j = i+1..112
            # Cut-edge changes (always affect both L and diff)
            a_i_old = d[i]
            a_j_old = d[j]
            a_i_new = D[sigma[i], sigma[j]]
            a_j_new = D[sigma[i+1], sigma[j+1]]
            delta_d_i = a_i_new - a_i_old
            delta_d_j = a_j_new - a_j_old
            delta_L = delta_d_i + delta_d_j  # ΔL unaffected by middle shuffle
            delta_diff_cut = w[i] * delta_d_i + w[j] * delta_d_j
            # Middle-segment reversal contribution to Δdiff
            # For k in (i, j): new d_k = d[i + j - k], so change = d[i+j-k] - d[k]
            delta_diff_mid = 0.0
            if j - i >= 2:  # at least one interior slot
                for k in range(i + 1, j):
                    delta_diff_mid += w[k] * (d[i + j - k] - d[k])
            delta_diff = delta_diff_cut + delta_diff_mid
            records.append((i, j, delta_L, delta_diff))
            n_swaps += 1
    print(f"\n# Enumerated {n_swaps} 2-opt swaps from Mushaf")

    rec = np.array(records)  # columns: i, j, deltaL, deltadiff
    dL = rec[:, 2]
    dDiff = rec[:, 3]

    # Classify
    dominating = (dL < -1e-12) & (dDiff > 1e-12)  # improves both (should be empty)
    dominated = (dL > 1e-12) & (dDiff < -1e-12)   # hurts both
    tradeoff_plus = (dL < -1e-12) & (dDiff < -1e-12)  # lower L, lower diff
    tradeoff_minus = (dL > 1e-12) & (dDiff > 1e-12)   # higher L, higher diff
    neutral = ~(dominating | dominated | tradeoff_plus | tradeoff_minus)

    print(f"\n=== 2-opt swap classification from Mushaf ===")
    print(f"  Dominating both  (ΔL<0 AND Δdiff>0): {int(dominating.sum()):6d}  <-- SHOULD BE 0 FOR PARETO-OPT")
    print(f"  Dominated both   (ΔL>0 AND Δdiff<0): {int(dominated.sum()):6d}")
    print(f"  Trade-off (ΔL<0, Δdiff<0) (sacrifice diff): {int(tradeoff_plus.sum()):6d}")
    print(f"  Trade-off (ΔL>0, Δdiff>0) (buy diff):       {int(tradeoff_minus.sum()):6d}")
    print(f"  Neutral / boundary:                         {int(neutral.sum()):6d}")

    n_dom = int(dominating.sum())
    if n_dom == 0:
        print(f"\n  >>> MUSHAF IS 2-OPT PARETO-LOCALLY-OPTIMAL <<<")
        print(f"  >>> No single 2-opt swap improves both L and diff simultaneously <<<")
    else:
        print(f"\n  !!! Mushaf is NOT 2-opt Pareto-locally-optimal: {n_dom} dominating swaps exist !!!")

    # ---------- KKT Lagrange multiplier derivation ----------
    # Mushaf is 2-opt KKT stationary for problem:
    #     minimise L(σ) + λ * (−diff(σ))   [λ >= 0]
    # iff for every 2-opt swap:  ΔL - λ * Δdiff >= 0
    #     <=>  λ * Δdiff <= ΔL
    #     case Δdiff > 0:  λ <= ΔL / Δdiff      -> upper bound on λ
    #     case Δdiff < 0:  λ >= ΔL / Δdiff      -> lower bound on λ
    #     case Δdiff = 0:  require ΔL >= 0      -> no λ constraint
    #
    # Therefore:  λ_lower_all  =  max_{Δdiff<0} (ΔL / Δdiff)
    #             λ_upper_all  =  min_{Δdiff>0} (ΔL / Δdiff)
    # If λ_lower_all <= λ_upper_all, KKT multiplier range is [λ_lower, λ_upper].

    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = dL / dDiff
    mask_pos = dDiff > 1e-12
    mask_neg = dDiff < -1e-12

    if mask_neg.any():
        lambda_lower = float(ratio[mask_neg].max())
    else:
        lambda_lower = float("-inf")
    if mask_pos.any():
        lambda_upper = float(ratio[mask_pos].min())
    else:
        lambda_upper = float("+inf")

    print(f"\n=== Closed-form KKT Lagrange multiplier ===")
    print(f"  From swaps with Δdiff < 0: λ_lower = max(ΔL/Δdiff) = {lambda_lower:.6f}")
    print(f"  From swaps with Δdiff > 0: λ_upper = min(ΔL/Δdiff) = {lambda_upper:.6f}")
    if lambda_lower <= lambda_upper:
        print(f"\n  >>> CLOSED-FORM λ* INTERVAL:  [{lambda_lower:.6f}, {lambda_upper:.6f}] <<<")
        print(f"  >>> Width: {lambda_upper - lambda_lower:.6f} <<<")
        kkt_satisfied = True
    else:
        print(f"\n  !!! No consistent λ* interval exists (lower > upper) !!!")
        kkt_satisfied = False

    # Sanity check: the KKT must be consistent with no-dominating-swap
    # (Pareto-optimal) above
    if n_dom == 0 and not kkt_satisfied:
        print("  NOTE: Pareto-optimal but KKT interval empty is possible if the")
        print("        problem is non-convex — the 2-opt neighbourhood may still")
        print("        not admit a single consistent λ.")

    # ---------- Derived scalars for F86 / F90 comparison ----------
    # F86 empirically reported Mushaf at L = 7.593 and diff = +0.0349.
    # F86 also reported: Mushaf is 39.7% above F81 unconstrained minimum (L_min_2opt),
    #                    Mushaf captures 36.4% of F82 ceiling.
    # F90's contribution: the closed-form λ* and the fact that a finite interval exists.

    # Compute the Lagrangian value at the Mushaf for midpoint λ
    if kkt_satisfied:
        lambda_mid = 0.5 * (lambda_lower + lambda_upper) if np.isfinite(lambda_lower) and np.isfinite(lambda_upper) else (lambda_upper if np.isfinite(lambda_upper) else lambda_lower)
        lagrangian_mid = L_mushaf - lambda_mid * diff_mushaf
        print(f"\n  Lagrangian L - λ·diff at midpoint λ = {lambda_mid:.6f}: {lagrangian_mid:.6f}")

    # Mushaf position summary
    summary = dict(
        experiment="exp180_F86_lagrangian_KKT",
        finding_id="F90",
        L_mushaf=L_mushaf,
        diff_mushaf=diff_mushaf,
        K_total=K_total,
        K_classical=len(CLASSICAL_SLOTS),
        K_nonclassical=K_total - len(CLASSICAL_SLOTS),
        n_2opt_swaps_enumerated=n_swaps,
        n_dominating=int(dominating.sum()),
        n_dominated=int(dominated.sum()),
        n_tradeoff_buy_diff=int(tradeoff_minus.sum()),
        n_tradeoff_sell_diff=int(tradeoff_plus.sum()),
        n_neutral=int(neutral.sum()),
        is_2opt_pareto_optimal=bool(n_dom == 0),
        kkt_lambda_lower=lambda_lower,
        kkt_lambda_upper=lambda_upper,
        kkt_interval_exists=bool(kkt_satisfied),
        kkt_interval_width=(lambda_upper - lambda_lower) if kkt_satisfied and np.isfinite(lambda_lower) and np.isfinite(lambda_upper) else None,
        kkt_lambda_midpoint=(0.5 * (lambda_lower + lambda_upper)) if kkt_satisfied and np.isfinite(lambda_lower) and np.isfinite(lambda_upper) else None,
        interpretation=(
            "For any λ* in the reported interval, the Mushaf is a 2-opt KKT "
            "stationary point of the constrained optimisation minimise L - λ·diff "
            "under adjacent-swap perturbation. This converts F86 from empirical "
            "Pareto-optimality to analytical KKT-stationarity with a closed-form "
            "Lagrange multiplier range."
        ),
        note_on_2opt_scope=(
            "2-opt is a neighbourhood of size O(n^2) = 6,328 moves. A k-opt "
            "neighbourhood for k > 2 would test stronger Pareto-optimality. This "
            "result establishes Mushaf's KKT-stationarity in the 2-opt sense; "
            "escalation to 3-opt / Or-opt is future work."
        ),
    )

    # Count how many swaps are in each Δdiff-sign band for report
    summary["n_dDiff_positive"] = int(mask_pos.sum())
    summary["n_dDiff_negative"] = int(mask_neg.sum())

    # KKT ratio distribution (for audit)
    if mask_pos.any():
        summary["kkt_upper_stats"] = dict(
            min_ratio_at_lambda_upper=float(ratio[mask_pos].min()),
            median_pos=float(np.median(ratio[mask_pos])),
            max_pos=float(ratio[mask_pos].max()),
        )
    if mask_neg.any():
        summary["kkt_lower_stats"] = dict(
            max_ratio_at_lambda_lower=float(ratio[mask_neg].max()),
            median_neg=float(np.median(ratio[mask_neg])),
            min_neg=float(ratio[mask_neg].min()),
        )

    out_path = OUT_DIR / "exp180_F86_lagrangian_KKT.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nReceipt: {out_path}")

    # ---------- Figure: Pareto-frontier visualisation ----------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 8))
        # Scatter all 2-opt neighbours in (L, diff) space
        L_neighbour = L_mushaf + dL
        diff_neighbour = diff_mushaf + dDiff
        ax.scatter(L_neighbour, diff_neighbour, s=8, c="0.6", alpha=0.4,
                   label=f"Mushaf 2-opt neighbours ({n_swaps})")
        # Mushaf point
        ax.scatter([L_mushaf], [diff_mushaf], s=200, c="C3", marker="*",
                   edgecolors="k", linewidth=1.0, zorder=5, label="Mushaf")
        ax.axhline(diff_mushaf, color="C3", ls="--", lw=0.8, alpha=0.5)
        ax.axvline(L_mushaf, color="C3", ls="--", lw=0.8, alpha=0.5)
        ax.set_xlabel("L = sum of adjacency distances (F81 axis)")
        ax.set_ylabel(r"diff = mean$_\mathrm{classical}$ − mean$_\mathrm{non-classical}$ (F82 axis)")
        pareto_text = "2-opt Pareto-optimal" if n_dom == 0 else f"Not Pareto-opt ({n_dom} dominate)"
        lambda_text = f"KKT λ* ∈ [{lambda_lower:.3f}, {lambda_upper:.3f}]" if kkt_satisfied else "no λ interval"
        ax.set_title(
            f"F90 — Mushaf 2-opt Pareto neighbourhood\n"
            f"{pareto_text}   |   {lambda_text}"
        )
        ax.legend(loc="upper right", fontsize=10)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig_path = OUT_DIR / "pareto_2opt_neighbourhood.png"
        fig.savefig(fig_path, dpi=130)
        print(f"Wrote {fig_path}")
    except Exception as e:
        print(f"(figure skipped: {e})")


if __name__ == "__main__":
    main()
