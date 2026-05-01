"""
exp26_perm_sensitivity/run.py
=============================
Phase-7 permutation-p sensitivity. The locked `Phi_M_perm_p_value` is
4.975e-3 under N_PERM = 200 (p-floor = 1/201 = 0.00498). External
review (2026-04-20) recommends N_PERM >= 10 000 so the reported p is
not floor-limited.

This script does NOT modify results_lock.json. It loads phase_06_phi_m
(X_QURAN, X_CTRL_POOL) and reruns the label-swap Hotelling T^2
permutation at N_PERM in {500, 2000, 10000}, reporting the empirical
p at each level. This is a supplementary sensitivity appendix, not a
lock rebless.

If the N_PERM = 10 000 p is <= 1 / 10 001 (i.e., no permuted T^2
reaches the observed), the finding is 'null-constrained at floor' and
the only honest reporting is 'p < 1e-4'. If any permuted T^2 exceeds
the observed under a higher N_PERM, the p-value is estimated from that
count.

Reads (integrity-checked):
  - phase_06_phi_m.pkl   (X_QURAN, X_CTRL_POOL)

Writes ONLY under results/experiments/exp26_perm_sensitivity/:
  - exp26_perm_sensitivity.json
"""
from __future__ import annotations

import json
import sys
import time
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

EXP = "exp26_perm_sensitivity"
SEED = 42 + 101  # matches _build.py Phase-7 rng seed for bit-exact parity at N=200
N_PERM_LEVELS = [500, 2000, 10000]


def _hotelling_t2(XA: np.ndarray, XB: np.ndarray) -> float:
    """Pooled-covariance Hotelling T^2 — byte-exact copy of
    _build.py::_hotelling_t2 (Cell 22, lines 1635-1655). Uses ridge 1e-6
    on S_pool (not pseudo-inverse) for bit-equal parity with the locked
    Phase-7 computation."""
    nA, p = XA.shape
    nB = XB.shape[0]
    if nA < 2 or nB < 2:
        return float("nan")
    mA, mB = XA.mean(0), XB.mean(0)
    SA = np.cov(XA.T, ddof=1)
    SB = np.cov(XB.T, ddof=1)
    Sp = ((nA - 1) * SA + (nB - 1) * SB) / max(1, (nA + nB - 2))
    try:
        Spi = np.linalg.inv(Sp + 1e-6 * np.eye(p))
    except np.linalg.LinAlgError:
        return float("nan")
    diff = mA - mB
    return float((nA * nB / (nA + nB)) * diff @ Spi @ diff)


def _perm_p(XA: np.ndarray, XB: np.ndarray, n_perm: int, seed: int
            ) -> tuple[float, int, float]:
    """Return (p, n_hits, wall_seconds). p = (hits + 1) / (n_perm + 1)."""
    T2_obs = _hotelling_t2(XA, XB)
    all_X = np.vstack([XA, XB])
    nA = len(XA)
    total = len(all_X)
    rng = np.random.default_rng(seed)
    hits = 0
    t0 = time.time()
    for _ in range(n_perm):
        idx = rng.permutation(total)
        T2_null = _hotelling_t2(all_X[idx[:nA]], all_X[idx[nA:]])
        if np.isfinite(T2_null) and T2_null >= T2_obs:
            hits += 1
    wall = time.time() - t0
    p = float((hits + 1) / (n_perm + 1))
    return p, hits, wall


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    X_Q = np.asarray(state["X_QURAN"], dtype=float)
    X_C = np.asarray(state["X_CTRL_POOL"], dtype=float)
    T2_obs = _hotelling_t2(X_Q, X_C)

    results = {}
    for n in N_PERM_LEVELS:
        p, hits, wall = _perm_p(X_Q, X_C, n_perm=n, seed=SEED)
        results[f"N={n}"] = {
            "n_perm": n,
            "hits_ge_observed": hits,
            "p_value": p,
            "p_floor": 1.0 / (n + 1),
            "wall_seconds": wall,
        }
        print(
            f"[{EXP}] N={n:>6d}   hits={hits:>3d}   p={p:.4e}   "
            f"floor={1.0/(n+1):.4e}   wall={wall:5.1f}s"
        )

    report = {
        "experiment": EXP,
        "seed_base": SEED,
        "n_quran": int(len(X_Q)),
        "n_ctrl": int(len(X_C)),
        "d": int(X_Q.shape[1]),
        "T2_observed": T2_obs,
        "locked_p_at_N200": 0.004975124378109453,
        "per_level": results,
        "note": (
            "Supplementary permutation-sensitivity appendix. Does NOT modify "
            "phase_07_core.pkl or results_lock.json. Shares the exact seed "
            "(SEED + 101) as the locked Phase-7 run so N=500 extends the same "
            "permutation sequence as N=200. If hits_ge_observed stays 0 as N "
            "grows, the reportable statement is 'p < 1/(N+1)'; we cannot "
            "infer a sharper value."
        ),
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
