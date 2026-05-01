"""scripts/_explore_F75_mixture.py — Pre-PREREG numerical exploration.

Purpose: Determine FEASIBILITY of mixture-with-uniform model and stretched-
exponential model BEFORE pre-registering exp154. This script is exploratory and
its output does NOT enter any locked receipt; it only informs PREREG threshold
calibration.

Reads exp153 receipt (locked p_max, H_EL per corpus), tries:
  Model M1: p_k = w*(1-r)*r^(k-1) + (1-w)/A   [user-specified mixture]
  Model M2: p_k ~ exp(-lam*k^beta)             [stretched exponential]

For each, sweeps universal parameter (w or beta) and per-corpus parameter
(r or lam), computes predicted H_EL, residuals.
"""
from __future__ import annotations
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP153 = ROOT / "results" / "experiments" / "exp153_F75_derivation_check" / "exp153_F75_derivation_check.json"
A = 28

data = json.loads(EXP153.read_text(encoding="utf-8"))
p_max = data["results"]["p_max_per_corpus"]
H_EL = data["results"]["H_EL_per_corpus"]
gap_emp = data["results"]["gap_empirical"]
corpora = list(p_max.keys())


def H_of_dist(probs):
    s = 0.0
    for p in probs:
        if p > 1e-15:
            s -= p * math.log2(p)
    return s


# ------------------------------------------------------------------
# Model M1: p_k = w*(1-r)*r^(k-1) + (1-w)/A, k=1..A
# Solve r from p_max constraint: p_max = w*(1-r) + (1-w)/A
#   => r = 1 - (p_max - (1-w)/A) / w
# Feasible: r in (0, 1)  <=> p_max > (1-w)/A  AND  p_max < w + (1-w)/A
# ------------------------------------------------------------------
def m1_predict_HEL(p_max_val, w):
    if w <= 0 or w >= 1:
        return None
    r = 1.0 - (p_max_val - (1 - w) / A) / w
    if r <= 0 or r >= 1:
        return None
    probs = [w * (1 - r) * (r ** (k - 1)) + (1 - w) / A for k in range(1, A + 1)]
    s = sum(probs)
    probs = [p / s for p in probs]  # renormalize for finite truncation
    return H_of_dist(probs), r


print("=" * 70)
print("MODEL M1: p_k = w*(1-r)*r^(k-1) + (1-w)/A")
print("=" * 70)
print(f"{'w':>6} | {'feas':>4} | {'SSR':>8} | {'mean_abs':>8} | {'A1@0.30':>7}")
for w in [0.74, 0.78, 0.82, 0.86, 0.90, 0.92, 0.94, 0.96, 0.98, 0.99, 0.995, 0.999]:
    residuals = {}
    feasible = True
    for c in corpora:
        out = m1_predict_HEL(p_max[c], w)
        if out is None:
            feasible = False
            break
        H_pred, _ = out
        gap_pred = H_pred + math.log2(p_max[c])
        residuals[c] = abs(gap_pred - gap_emp[c])
    if not feasible:
        print(f"{w:>6.3f} | {'X':>4} | {'-':>8} | {'-':>8} | {'-':>7}")
        continue
    ssr = sum(r ** 2 for r in residuals.values())
    mean_abs = sum(residuals.values()) / len(residuals)
    a1_pass = sum(1 for c in corpora if c != "quran" and residuals[c] <= 0.30)
    print(f"{w:>6.3f} | {'OK':>4} | {ssr:>8.4f} | {mean_abs:>8.4f} | {a1_pass:>5}/10")


# ------------------------------------------------------------------
# Model M2: p_k ~ exp(-lam*k^beta) / Z, k=1..A
# Per corpus: solve lam such that p_1/Z = p_max
#   => p_max = exp(-lam) / Z
#   => Z * p_max = exp(-lam)
# Numerical: bisect lam given (p_max, beta)
# ------------------------------------------------------------------
def m2_predict_HEL(p_max_val, beta):
    # p_k = exp(-lam * k^beta) / Z, with Z = sum exp(-lam * k^beta)
    # p_1 = exp(-lam) / Z = p_max
    # Bisect lam in (1e-6, 50)
    lo, hi = 1e-6, 50.0
    for _ in range(100):
        mid = (lo + hi) / 2
        weights = [math.exp(-mid * (k ** beta)) for k in range(1, A + 1)]
        Z = sum(weights)
        p1 = weights[0] / Z
        # p_1 is INCREASING in lam (more concentration). To drop p_1, decrease lam.
        if p1 > p_max_val:
            hi = mid
        else:
            lo = mid
    lam = (lo + hi) / 2
    weights = [math.exp(-lam * (k ** beta)) for k in range(1, A + 1)]
    Z = sum(weights)
    probs = [w_ / Z for w_ in weights]
    return H_of_dist(probs), lam


print()
print("=" * 70)
print("MODEL M2: p_k ~ exp(-lam*k^beta) / Z")
print("=" * 70)
print(f"{'beta':>6} | {'feas':>4} | {'SSR':>8} | {'mean_abs':>8} | {'A1@0.30':>7}")
for beta in [0.5, 0.7, 0.85, 1.0, 1.15, 1.3, 1.5, 1.75, 2.0, 2.5, 3.0]:
    residuals = {}
    feasible = True
    for c in corpora:
        try:
            H_pred, _ = m2_predict_HEL(p_max[c], beta)
        except Exception:
            feasible = False
            break
        gap_pred = H_pred + math.log2(p_max[c])
        residuals[c] = abs(gap_pred - gap_emp[c])
    if not feasible:
        print(f"{beta:>6.2f} | {'X':>4} | {'-':>8} | {'-':>8} | {'-':>7}")
        continue
    ssr = sum(r ** 2 for r in residuals.values())
    mean_abs = sum(residuals.values()) / len(residuals)
    a1_pass = sum(1 for c in corpora if c != "quran" and residuals[c] <= 0.30)
    print(f"{beta:>6.2f} | {'OK':>4} | {ssr:>8.4f} | {mean_abs:>8.4f} | {a1_pass:>5}/10")
