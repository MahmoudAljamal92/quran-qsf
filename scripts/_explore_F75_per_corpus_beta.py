"""Exploratory: per-corpus (mu, beta) MaxEnt fit from empirical (p_max, H_EL) jointly.

Theoretical claim being tested: under the maxent stretched-exp form
    p_k ∝ exp(-mu·k^beta) / Z(mu, beta, A=28),  k = 1, ..., 28
the per-corpus pair (mu_c, beta_c) is uniquely determined by the joint
constraint (p_max(c), H_EL(c)). If beta_c clusters tightly around 1.5
across 11 corpora, the V3.20 modal beta = 1.5 has a first-principles
maxent-cognitive-channel justification.

This is exploratory; outputs determine whether to pre-register exp156.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECEIPT = ROOT / "results" / "experiments" / "exp154_F75_stretched_exp_derivation" / "exp154_F75_stretched_exp_derivation.json"

A = 28


def H_of_dist(probs):
    s = 0.0
    for p in probs:
        if p > 1e-15:
            s -= p * math.log2(p)
    return s


def fit_lambda(p_max_val, beta, A=28):
    """Bisect lambda such that p_1 = p_max_val. Returns (lam, probs).
    Identical to exp154's fit_stretched_exp.
    """
    lo, hi = 1e-9, 60.0
    for _ in range(200):
        mid = (lo + hi) / 2
        weights = [math.exp(-mid * (k ** beta)) for k in range(1, A + 1)]
        Z = sum(weights)
        p1 = weights[0] / Z
        if p1 > p_max_val:
            hi = mid
        else:
            lo = mid
    lam = (lo + hi) / 2
    weights = [math.exp(-lam * (k ** beta)) for k in range(1, A + 1)]
    Z = sum(weights)
    probs = [w_ / Z for w_ in weights]
    return lam, probs


def H_at_beta(p_max_val, beta, A=28):
    """Given (p_max, beta), find lambda by p_max constraint, then return H_EL."""
    _, probs = fit_lambda(p_max_val, beta, A)
    return H_of_dist(probs)


def fit_beta_from_pmax_H(p_max_val, H_emp, beta_lo=0.1, beta_hi=10.0, tol=1e-7):
    """Given (p_max, H_EL_empirical), bisect beta such that H(beta) = H_emp.
    
    Note: H(beta) is MONOTONIC in beta for fixed p_max:
    - At beta -> 0: distribution -> uniform on top-most-letters (high H)
    - At beta -> infty: distribution -> delta on k=1 (low H)
    
    Specifically, dH/dbeta < 0 in the Weibull regime we care about.
    So we bisect with H decreasing in beta.
    """
    H_lo = H_at_beta(p_max_val, beta_lo)  # high
    H_hi = H_at_beta(p_max_val, beta_hi)  # low

    if H_emp >= H_lo:
        return None, "H_emp_above_low_beta_limit"
    if H_emp <= H_hi:
        return None, "H_emp_below_high_beta_limit"

    for _ in range(200):
        mid = (beta_lo + beta_hi) / 2
        H_mid = H_at_beta(p_max_val, mid)
        if H_mid > H_emp:
            beta_lo = mid  # need higher beta to reduce H
        else:
            beta_hi = mid
        if abs(H_mid - H_emp) < tol:
            break
    return (beta_lo + beta_hi) / 2, "ok"


def main():
    r = json.load(open(RECEIPT, encoding="utf-8"))
    p_max = r["results"]["p_max_per_corpus"]
    H_EL = r["results"]["H_EL_per_corpus"]

    corpora = list(p_max.keys())

    print("Per-corpus MaxEnt fit: (p_max, H_EL) -> (mu, beta)")
    print(f"{'corpus':18s} | {'p_max':>7s} | {'H_EL':>7s} | {'beta':>8s} | {'lambda':>10s} | status")
    print("-" * 80)

    betas = []
    for c in corpora:
        beta, status = fit_beta_from_pmax_H(p_max[c], H_EL[c])
        if beta is None:
            print(f"{c:18s} | {p_max[c]:7.4f} | {H_EL[c]:7.4f} | {'---':>8s} | {'---':>10s} | {status}")
        else:
            lam, _ = fit_lambda(p_max[c], beta)
            print(f"{c:18s} | {p_max[c]:7.4f} | {H_EL[c]:7.4f} | {beta:>8.4f} | {lam:>10.4f} | {status}")
            betas.append((c, beta))

    if betas:
        beta_vals = [b for _, b in betas]
        print()
        print(f"=== beta distribution across {len(beta_vals)} corpora ===")
        print(f"  min:  {min(beta_vals):.4f}")
        print(f"  max:  {max(beta_vals):.4f}")
        print(f"  mean: {sum(beta_vals) / len(beta_vals):.4f}")
        n = len(beta_vals)
        m = sum(beta_vals) / n
        std = math.sqrt(sum((b - m) ** 2 for b in beta_vals) / (n - 1))
        print(f"  std:  {std:.4f}")
        print(f"  CV:   {std / m:.4f}")
        print()
        print(f"  median: {sorted(beta_vals)[n // 2]:.4f}")
        print()
        print(f"  Distance from beta=1.5: {abs(m - 1.5):.4f}")
        print(f"  Within [1.3, 1.7]?      {sum(1 for b in beta_vals if 1.3 <= b <= 1.7)}/{n}")
        print(f"  Within [1.0, 2.0]?      {sum(1 for b in beta_vals if 1.0 <= b <= 2.0)}/{n}")
        print(f"  Within [0.5, 2.5]?      {sum(1 for b in beta_vals if 0.5 <= b <= 2.5)}/{n}")
        print()
        print(f"  Sorted betas:")
        for c, b in sorted(betas, key=lambda x: x[1]):
            print(f"    {c:18s} {b:.4f}")


if __name__ == "__main__":
    main()
