"""
expP12_bootstrap_t2_ci/run.py
=============================
Bootstrap 95% CI on the full-Quran 5-D Hotelling T² (locked point estimate
3 685.45 from expP7).

Pre-registered in PREREG.md (frozen 2026-04-26, v7.9-cand patch E).

Reads:  phase_06_phi_m.pkl ::state[CORPORA]
Writes: results/experiments/expP12_bootstrap_t2_ci/expP12_bootstrap_t2_ci.json
"""
from __future__ import annotations

import hashlib
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
    load_phase, safe_output_dir, self_check_begin, self_check_end,
)
from src.features import features_5d  # noqa: E402

EXP = "expP12_bootstrap_t2_ci"
SEED = 42
N_BOOT = 1000
MIN_VERSES = 2
# LOCKED_T2_BANDA / LOCKED_T2_FULL are the PRE-FIX historical baselines
# (computed with hadith in ARABIC_CTRL). After F3a (2026-04-26) hadith is
# dropped; the new point estimate is expected to be HIGHER (controls move
# away from Quran). Verdict relative to the locked baseline therefore
# defaults to "STRENGTHENED".
LOCKED_T2_BANDA = 3557.34
LOCKED_T2_FULL = 3685.45  # from expP7
# AUDIT FIX F3a (2026-04-26): `hadith_bukhari` REMOVED from ARABIC_CTRL.
# Rationale (matches src/clean_pipeline.ARABIC_CORPORA_FOR_CONTROL,
# src/extended_tests*.py, and the notebook quarantine policy at v5):
#   Sahih al-Bukhari quotes the Quran verbatim by design (it is the
#   Prophetic tradition *about* the Quran). Including it in the control
#   pool biases the Hotelling T² statistic DOWNWARD because the control
#   centroid gets pulled toward the Quran. The L1 audit caught this leak
#   (notebooks/ultimate/_audit_check.py).
ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _hotelling_t2(X_quran: np.ndarray, X_ctrl: np.ndarray) -> float:
    nq, p = X_quran.shape
    nc = X_ctrl.shape[0]
    mu_q = X_quran.mean(axis=0)
    mu_c = X_ctrl.mean(axis=0)
    Sq = np.cov(X_quran, rowvar=False, ddof=1) if nq > 1 else np.zeros((p, p))
    Sc = np.cov(X_ctrl, rowvar=False, ddof=1) if nc > 1 else np.zeros((p, p))
    Spool = ((nq - 1) * Sq + (nc - 1) * Sc) / max(nq + nc - 2, 1)
    Sinv = np.linalg.pinv(Spool)
    diff = mu_q - mu_c
    return float((nq * nc / (nq + nc)) * (diff @ Sinv @ diff))


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    print(f"[{EXP}] Computing 5-D features per unit ...")
    Xq, Xc = [], []
    for u in CORPORA.get("quran", []):
        if len(u.verses) >= MIN_VERSES:
            Xq.append(features_5d(list(u.verses)))
    for name in ARABIC_CTRL:
        for u in CORPORA.get(name, []):
            if len(u.verses) >= MIN_VERSES:
                Xc.append(features_5d(list(u.verses)))
    Xq = np.array(Xq, dtype=float)
    Xc = np.array(Xc, dtype=float)
    finite_q = np.isfinite(Xq).all(axis=1)
    finite_c = np.isfinite(Xc).all(axis=1)
    Xq = Xq[finite_q]
    Xc = Xc[finite_c]
    nq, nc = Xq.shape[0], Xc.shape[0]
    print(f"[{EXP}] n_quran={nq}  n_ctrl={nc}")

    # Point estimate sanity
    point_T2 = _hotelling_t2(Xq, Xc)
    print(f"[{EXP}] Point estimate T² = {point_T2:.2f}  (expected ≈ {LOCKED_T2_FULL:.2f})")

    # Bootstrap
    rng = np.random.RandomState(SEED)
    T2s = np.empty(N_BOOT, dtype=float)
    for b in range(N_BOOT):
        iq = rng.choice(nq, nq, replace=True)
        ic = rng.choice(nc, nc, replace=True)
        T2s[b] = _hotelling_t2(Xq[iq], Xc[ic])
        if (b + 1) % 100 == 0:
            print(f"[{EXP}]   boot {b+1}/{N_BOOT}  median so far = {np.median(T2s[:b+1]):.1f}")

    median = float(np.median(T2s))
    ci_lo = float(np.percentile(T2s, 2.5))
    ci_hi = float(np.percentile(T2s, 97.5))
    bias = float(np.mean(T2s)) - point_T2

    if ci_lo > LOCKED_T2_BANDA:
        verdict = "STRENGTHENED"
    elif ci_hi < LOCKED_T2_BANDA:
        verdict = "WEAKENED"
    else:
        verdict = "STABLE"

    print(f"[{EXP}] Bootstrap T² 95% CI: [{ci_lo:.1f}, {ci_hi:.1f}], median {median:.1f}")
    print(f"[{EXP}] vs locked band-A T² = {LOCKED_T2_BANDA}  -> verdict: {verdict}")
    print(f"[{EXP}] Bias (mean_boot - point) = {bias:+.2f}")

    record = {
        "experiment": EXP,
        "prereg_sha256": _prereg_hash(),
        "n_quran": nq, "n_ctrl": nc,
        "n_boot": N_BOOT,
        "point_estimate_T2": point_T2,
        "locked_band_A_T2": LOCKED_T2_BANDA,
        "locked_full_T2": LOCKED_T2_FULL,
        "bootstrap_median": median,
        "bootstrap_ci_lo_2.5": ci_lo,
        "bootstrap_ci_hi_97.5": ci_hi,
        "bias_mean_minus_point": bias,
        "verdict": verdict,
        "wall_time_s": time.time() - t0,
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] -> {out / (EXP + '.json')}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
