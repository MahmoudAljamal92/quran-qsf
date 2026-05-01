"""
exp96b_bayes_factor — Out-of-sample robustness check on Φ_master.

Purpose
-------
Address the circularity objection raised in the 2026-04-27 afternoon
feedback by computing the Gate 1 contribution to Φ_master under
leave-one-control-corpus-out (LOCO) cross-validation and a
non-parametric bootstrap of the control pool.

Inputs
------
- `results/experiments/exp96a_phi_master/exp96a_phi_master.json`
  (chain-of-custody hash on its PREREG)
- `phase_06_phi_m.pkl` via the integrity-checked `_lib.load_phase`

Output
------
- `results/experiments/exp96b_bayes_factor/exp96b_bayes_factor.json`

Scope
-----
Whole 114-surah Quran. No band gates. MIN_VERSES = 2.

PREREG: experiments/exp96b_bayes_factor/PREREG.md
PREREG hash: 39d6d977d964e1d4c1319edbc62fba9826ea41f0937206d98d4ff25a26af150a
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Pathing / imports
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments._lib import load_phase, safe_output_dir, self_check_begin, self_check_end  # noqa: E402
from src.features import features_5d  # noqa: E402

EXP = "exp96b_bayes_factor"
PREREG_HASH_EXPECTED = "39d6d977d964e1d4c1319edbc62fba9826ea41f0937206d98d4ff25a26af150a"

# ---------------------------------------------------------------------------
# Frozen constants (must match PREREG.md §3)
# ---------------------------------------------------------------------------
MIN_VERSES   = 2
ARABIC_CTRL  = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
                "ksucca", "arabic_bible", "hindawi"]
N_BOOT       = 500
RNG_SEED     = 96100

PHI_MASTER_HEADLINE      = 1862.31
PHI_MASTER_HEADLINE_TOL  = 5.0
LOCO_MIN_FLOOR           = 1500.0
BOOT_P05_FLOOR           = 1500.0

EXP96A_HASH_EXPECTED = "ab816b3e81bd1bfc7be0bb349ee4e3e49b7db56f288ac7c792ecc861d847db3e"

RESULTS = ROOT / "results"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def hotelling_t2(X_q: np.ndarray, X_c: np.ndarray) -> float:
    """Two-sample Hotelling T² with pooled covariance (ddof=1) and
    pseudo-inverse for safety."""
    nq, p = X_q.shape
    nc = X_c.shape[0]
    mu_q = X_q.mean(axis=0)
    mu_c = X_c.mean(axis=0)
    Sq = np.cov(X_q, rowvar=False, ddof=1) if nq > 1 else np.zeros((p, p))
    Sc = np.cov(X_c, rowvar=False, ddof=1) if nc > 1 else np.zeros((p, p))
    Spool = ((nq - 1) * Sq + (nc - 1) * Sc) / max(nq + nc - 2, 1)
    Sinv = np.linalg.pinv(Spool)
    diff = mu_q - mu_c
    return float((nq * nc / (nq + nc)) * (diff @ Sinv @ diff))


def load_features():
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    rows = []
    # Quran (label = 1)
    for u in CORPORA.get("quran", []):
        nv = len(u.verses)
        if nv < MIN_VERSES:
            continue
        rows.append({"corpus": "quran", "y": 1, "n_verses": nv,
                     "feat": features_5d(list(u.verses))})
    # Controls (label = 0, with corpus name retained for LOCO)
    for name in ARABIC_CTRL:
        for u in CORPORA.get(name, []):
            nv = len(u.verses)
            if nv < MIN_VERSES:
                continue
            rows.append({"corpus": name, "y": 0, "n_verses": nv,
                         "feat": features_5d(list(u.verses))})
    X = np.vstack([r["feat"] for r in rows])
    y = np.array([r["y"] for r in rows], dtype=int)
    corpus = np.array([r["corpus"] for r in rows], dtype=object)
    finite = np.isfinite(X).all(axis=1)
    return X[finite], y[finite], corpus[finite]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out_dir = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    # --- PREREG hash check ---------------------------------------------------
    prereg_hash_actual = sha256_of(HERE / "PREREG.md")
    print(f"[{EXP}] PREREG hash: {prereg_hash_actual}")
    audit_failures = []

    if prereg_hash_actual != PREREG_HASH_EXPECTED:
        audit_failures.append(
            f"PREREG drift: actual={prereg_hash_actual} expected={PREREG_HASH_EXPECTED}"
        )

    # --- Audit A1: exp96a receipt sanity ------------------------------------
    exp96a_path = RESULTS / "experiments" / "exp96a_phi_master" / "exp96a_phi_master.json"
    exp96a = None
    if not exp96a_path.exists():
        audit_failures.append(f"A1: exp96a receipt missing at {exp96a_path}")
    else:
        with open(exp96a_path, "r", encoding="utf-8") as f:
            exp96a = json.load(f)
        if exp96a.get("verdict") != "PASS_phi_master_locked":
            audit_failures.append(
                f"A1_verdict: exp96a verdict = {exp96a.get('verdict')!r}, expected PASS_phi_master_locked"
            )
        if exp96a.get("prereg_hash_actual") != EXP96A_HASH_EXPECTED:
            audit_failures.append(
                f"A1_hash: exp96a PREREG hash = {exp96a.get('prereg_hash_actual')}, "
                f"expected {EXP96A_HASH_EXPECTED}"
            )
        phi_obs = exp96a.get("headline", {}).get("phi_master_quran_nats")
        if phi_obs is None or abs(phi_obs - PHI_MASTER_HEADLINE) > PHI_MASTER_HEADLINE_TOL:
            audit_failures.append(
                f"A1_phi_master: exp96a phi_master = {phi_obs}, "
                f"expected {PHI_MASTER_HEADLINE} +- {PHI_MASTER_HEADLINE_TOL}"
            )

    # If audit A1 fired, write a FAIL receipt and exit cleanly.
    if audit_failures:
        receipt = {
            "experiment": EXP,
            "schema_version": "1.0",
            "hypothesis": "H50",
            "verdict": "FAIL_audit_A1",
            "audit_failures": audit_failures,
            "prereg_hash_expected": PREREG_HASH_EXPECTED,
            "prereg_hash_actual": prereg_hash_actual,
            "wall_time_s": time.time() - t0,
        }
        out_path = out_dir / f"{EXP}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2, ensure_ascii=False)
        print(f"[{EXP}] AUDIT FAIL: {audit_failures}")
        print(f"[{EXP}] receipt: {out_path}")
        return 1

    # --- A2/A3: load features, integrity-checked ---------------------------
    print(f"[{EXP}] loading phase_06_phi_m features ...")
    X, y, corpus = load_features()
    n_q = int((y == 1).sum())
    n_c = int((y == 0).sum())
    print(f"[{EXP}] n_quran = {n_q}, n_ctrl = {n_c} (whole-corpus, MIN_VERSES={MIN_VERSES})")
    if n_q != 114 or n_c < 4500:
        audit_failures.append(f"A3: n_quran={n_q} (expected 114), n_ctrl={n_c} (expected >= 4500)")

    if audit_failures:
        receipt = {
            "experiment": EXP, "schema_version": "1.0", "hypothesis": "H50",
            "verdict": "FAIL_audit_A3",
            "audit_failures": audit_failures,
            "prereg_hash_expected": PREREG_HASH_EXPECTED,
            "prereg_hash_actual": prereg_hash_actual,
            "wall_time_s": time.time() - t0,
        }
        out_path = out_dir / f"{EXP}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2, ensure_ascii=False)
        print(f"[{EXP}] AUDIT FAIL: {audit_failures}")
        return 1

    X_q = X[y == 1]
    X_c = X[y == 0]
    corpus_c = corpus[y == 0]

    # --- Headline T² (full pool) ------------------------------------------
    T2_full = hotelling_t2(X_q, X_c)
    T1_full_nats = 0.5 * T2_full
    print(f"[{EXP}] T2(full pool, all 6 ctrl) = {T2_full:.3f}  -> T1 = {T1_full_nats:.3f} nats")

    # --- Reuse exp96a's T2..T6 sum (they don't depend on Σ here) ----------
    quran_row = exp96a["per_corpus"]["quran"]
    T_other_sum_nats = (
        quran_row["T2_pmax_log_ratio"]
        + quran_row["T3_el_auc_log_ratio"]
        + quran_row["T4_el_frag_log_ratio"]
        + quran_row["T5_f55_clopper_pearson_log"]
        + quran_row["T6_riwayat_sum_log_ratio"]
    )
    print(f"[{EXP}] T2..T6 sum (from exp96a) = {T_other_sum_nats:.3f} nats")

    phi_master_full = T1_full_nats + T_other_sum_nats
    print(f"[{EXP}] Phi_master(full pool) = {phi_master_full:.3f} nats")

    # --- Leave-one-control-corpus-out (LOCO) ------------------------------
    print(f"\n[{EXP}] === LOCO leave-one-control-corpus-out ===")
    loco = {}
    for hold_out in ARABIC_CTRL:
        keep = corpus_c != hold_out
        n_kept = int(keep.sum())
        n_held = int((~keep).sum())
        try:
            T2_loco = hotelling_t2(X_q, X_c[keep])
        except Exception as e:
            T2_loco = float("nan")
            print(f"[{EXP}]   LOCO {hold_out}: numeric failure ({e})")
        T1_loco_nats = 0.5 * T2_loco
        phi_loco = T1_loco_nats + T_other_sum_nats
        loco[hold_out] = {
            "n_held_out": n_held,
            "n_remaining": n_kept,
            "T2": T2_loco,
            "T1_nats": T1_loco_nats,
            "phi_master_nats": phi_loco,
            "log10_bayes_factor": phi_loco / math.log(10.0),
        }
        print(f"[{EXP}]   hold-out {hold_out:18s} n_held={n_held:5d} -> "
              f"T2={T2_loco:9.2f}  Phi_master={phi_loco:9.2f} nats")

    loco_phi = [v["phi_master_nats"] for v in loco.values() if math.isfinite(v["phi_master_nats"])]
    loco_min = min(loco_phi)
    loco_max = max(loco_phi)
    loco_med = float(np.median(loco_phi))
    print(f"[{EXP}] LOCO Phi_master: min={loco_min:.2f}  median={loco_med:.2f}  max={loco_max:.2f}")

    # --- Non-parametric bootstrap of the control pool ---------------------
    print(f"\n[{EXP}] === Bootstrap (n_boot = {N_BOOT}) ===")
    rng = np.random.RandomState(RNG_SEED)
    boot_t2 = []
    n_failed = 0
    for b in range(N_BOOT):
        idx = rng.choice(n_c, n_c, replace=True)
        X_cb = X_c[idx]
        try:
            T2b = hotelling_t2(X_q, X_cb)
            if math.isfinite(T2b):
                boot_t2.append(T2b)
            else:
                n_failed += 1
        except Exception:
            n_failed += 1
    if n_failed > 0:
        print(f"[{EXP}]   bootstrap: {n_failed} numerical failures dropped (of {N_BOOT})")
    boot_arr = np.array(boot_t2)
    boot_phi = 0.5 * boot_arr + T_other_sum_nats
    boot_p05 = float(np.percentile(boot_phi, 5)) if boot_phi.size else float("nan")
    boot_p50 = float(np.percentile(boot_phi, 50)) if boot_phi.size else float("nan")
    boot_p95 = float(np.percentile(boot_phi, 95)) if boot_phi.size else float("nan")
    print(f"[{EXP}] bootstrap Phi_master: p05={boot_p05:.2f}  p50={boot_p50:.2f}  p95={boot_p95:.2f}")

    # Audit A5: bootstrap completion rate
    if boot_arr.size < 0.95 * N_BOOT:
        audit_failures.append(
            f"A5_boot_completion: only {boot_arr.size}/{N_BOOT} bootstrap replicates valid"
        )

    # --- Verdict ladder ----------------------------------------------------
    if audit_failures:
        verdict = "FAIL_audit_" + audit_failures[0].split(":", 1)[0].split("_")[0]
    elif loco_min < LOCO_MIN_FLOOR:
        verdict = "FAIL_loco_min_below_floor"
    elif boot_p05 < BOOT_P05_FLOOR:
        verdict = "FAIL_boot_p05_below_floor"
    else:
        verdict = "PASS_robust_oos_locked"

    # --- Write receipt -----------------------------------------------------
    receipt = {
        "experiment": EXP,
        "schema_version": "1.0",
        "hypothesis": "H50",
        "verdict": verdict,
        "prereg_hash_expected": PREREG_HASH_EXPECTED,
        "prereg_hash_actual": prereg_hash_actual,
        "frozen_constants": {
            "MIN_VERSES": MIN_VERSES,
            "ARABIC_CTRL": ARABIC_CTRL,
            "N_BOOT": N_BOOT,
            "RNG_SEED": RNG_SEED,
            "PHI_MASTER_HEADLINE": PHI_MASTER_HEADLINE,
            "LOCO_MIN_FLOOR": LOCO_MIN_FLOOR,
            "BOOT_P05_FLOOR": BOOT_P05_FLOOR,
        },
        "source_receipts": {
            "exp96a_phi_master": EXP96A_HASH_EXPECTED,
        },
        "n_quran_units": n_q,
        "n_ctrl_units": n_c,
        "T_other_sum_nats_from_exp96a": T_other_sum_nats,
        "headline_full_pool": {
            "T2": T2_full,
            "T1_nats": T1_full_nats,
            "phi_master_nats": phi_master_full,
            "log10_bayes_factor": phi_master_full / math.log(10.0),
        },
        "loco": loco,
        "loco_summary": {
            "phi_master_min_nats":    loco_min,
            "phi_master_median_nats": loco_med,
            "phi_master_max_nats":    loco_max,
            "n_splits": len(ARABIC_CTRL),
        },
        "bootstrap": {
            "n_boot": N_BOOT,
            "n_valid": int(boot_arr.size),
            "n_failed": n_failed,
            "phi_master_p05_nats":  boot_p05,
            "phi_master_p50_nats":  boot_p50,
            "phi_master_p95_nats":  boot_p95,
            "phi_master_log10_BF_p05":  boot_p05 / math.log(10.0),
            "phi_master_log10_BF_p50":  boot_p50 / math.log(10.0),
            "phi_master_log10_BF_p95":  boot_p95 / math.log(10.0),
        },
        "audit_failures": audit_failures,
        "wall_time_s": time.time() - t0,
    }
    out_path = out_dir / f"{EXP}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, ensure_ascii=False)

    print(f"\n[{EXP}] verdict = {verdict}")
    print(f"[{EXP}] LOCO min Phi_master  = {loco_min:.2f} nats   (floor {LOCO_MIN_FLOOR})")
    print(f"[{EXP}] boot p05 Phi_master  = {boot_p05:.2f} nats   (floor {BOOT_P05_FLOOR})")
    print(f"[{EXP}] receipt: {out_path}")

    self_check_end(pre, exp_name=EXP)
    return 0 if verdict == "PASS_robust_oos_locked" else 2


if __name__ == "__main__":
    sys.exit(main())
