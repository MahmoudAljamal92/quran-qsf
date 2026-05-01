"""
exp82_transfer_entropy/run.py
==============================
H11: Transfer Entropy Between Features Across Surah Order.

Motivation
    The 5 features (EL, VL_CV, CN, H_cond, T) per surah may show
    directed information flow across the canonical ordering. If TE is
    significant, the mushaf ordering is information-theoretically
    optimized for cross-feature coherence.

Protocol (frozen before execution)
    T1. Compute features_5d for each of 114 surahs in canonical order.
    T2. For all 20 directed pairs (i->j): compute binned TE.
    T3. Shuffle null: permute surah order 10k times, recompute TE.
    T4. p-value = fraction of shuffled TE >= observed.
    T5. BH correction for 20 tests.
    T6. Compare canonical vs reverse ordering.

TE definition (binned)
    TE(X -> Y | lag=1) = H(Y_t | Y_{t-1}) - H(Y_t | Y_{t-1}, X_{t-1})
    Discretise each feature into 3 equal-frequency bins.

Pre-registered thresholds
    SIGNIFICANT:  >= 3 directed pairs with BH-corrected p < 0.05
    SUGGESTIVE:   >= 1 pair with raw p < 0.01
    NULL:         otherwise

Reads: phase_06_phi_m.pkl -> CORPORA['quran']
"""
from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter
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

EXP = "exp82_transfer_entropy"
SEED = 42
N_PERM = 10000
N_BINS = 3
FEAT_NAMES = ["EL", "VL_CV", "CN", "H_cond", "T"]


def _compute_features_fast(units) -> np.ndarray:
    """Compute 5D features per unit WITHOUT CamelTools (fast proxy).
    Uses h_cond_initials instead of h_cond_roots to avoid CamelTools."""
    from src.features import (
        el_rate, vl_cv, cn_rate, h_el, ARABIC_CONN,
        h_cond_initials,
    )
    feats = []
    for u in units:
        el = el_rate(u.verses)
        cv = vl_cv(u.verses)
        cn = cn_rate(u.verses, ARABIC_CONN)
        hc = h_cond_initials(u.verses)
        he = h_el(u.verses)
        T = hc - he
        feats.append([el, cv, cn, hc, T])
    return np.array(feats)


def _binned(x: np.ndarray, n_bins: int = N_BINS) -> np.ndarray:
    """Equal-frequency binning."""
    percentiles = np.linspace(0, 100, n_bins + 1)[1:-1]
    edges = np.percentile(x, percentiles)
    return np.digitize(x, edges)


def _entropy_1d(x: np.ndarray) -> float:
    c = Counter(x)
    total = sum(c.values())
    return -sum((n / total) * math.log2(n / total)
                for n in c.values() if n > 0)


def _joint_entropy(x: np.ndarray, y: np.ndarray) -> float:
    pairs = list(zip(x, y))
    c = Counter(pairs)
    total = sum(c.values())
    return -sum((n / total) * math.log2(n / total)
                for n in c.values() if n > 0)


def _joint_entropy_3(x, y, z) -> float:
    triples = list(zip(x, y, z))
    c = Counter(triples)
    total = sum(c.values())
    return -sum((n / total) * math.log2(n / total)
                for n in c.values() if n > 0)


def _transfer_entropy(x_src: np.ndarray, y_tgt: np.ndarray, lag: int = 1) -> float:
    """TE(X -> Y) = H(Y_t, Y_{t-1}) + H(Y_{t-1}, X_{t-1}) - H(Y_{t-1})
                    - H(Y_t, Y_{t-1}, X_{t-1})
    Using chain rule: TE = H(Y_t | Y_{t-1}) - H(Y_t | Y_{t-1}, X_{t-1})
    """
    n = len(y_tgt)
    if n < lag + 2:
        return 0.0

    Y_t = y_tgt[lag:]
    Y_tm1 = y_tgt[:-lag]
    X_tm1 = x_src[:-lag]

    # TE = H(Y_t, Y_{t-1}) - H(Y_{t-1}) - H(Y_t, Y_{t-1}, X_{t-1}) + H(Y_{t-1}, X_{t-1})
    h_yt_ytm1 = _joint_entropy(Y_t, Y_tm1)
    h_ytm1 = _entropy_1d(Y_tm1)
    h_yt_ytm1_xtm1 = _joint_entropy_3(Y_t, Y_tm1, X_tm1)
    h_ytm1_xtm1 = _joint_entropy(Y_tm1, X_tm1)

    te = h_yt_ytm1 - h_ytm1 - h_yt_ytm1_xtm1 + h_ytm1_xtm1
    return max(0.0, te)  # TE >= 0 by definition


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]
    q_units = CORPORA["quran"]

    # T1: Compute features
    print(f"[{EXP}] Computing 5D features for {len(q_units)} surahs...")
    feats = _compute_features_fast(q_units)
    print(f"[{EXP}] Features shape: {feats.shape}")

    # Bin features
    binned = np.zeros_like(feats, dtype=int)
    for j in range(feats.shape[1]):
        binned[:, j] = _binned(feats[:, j])

    # T2: Compute TE for all 20 directed pairs
    print(f"\n[{EXP}] === T2: Transfer entropy (canonical order) ===")
    te_results = {}
    for i in range(5):
        for j in range(5):
            if i == j:
                continue
            pair = f"{FEAT_NAMES[i]}->{FEAT_NAMES[j]}"
            te = _transfer_entropy(binned[:, i], binned[:, j])
            te_results[pair] = {"te": round(te, 6)}

    # T3: Permutation null
    print(f"[{EXP}] Running {N_PERM} permutations...")
    rng = np.random.RandomState(SEED)
    perm_counts = {pair: 0 for pair in te_results}

    for p in range(N_PERM):
        perm_idx = rng.permutation(len(q_units))
        binned_perm = binned[perm_idx]
        for i in range(5):
            for j in range(5):
                if i == j:
                    continue
                pair = f"{FEAT_NAMES[i]}->{FEAT_NAMES[j]}"
                te_perm = _transfer_entropy(binned_perm[:, i], binned_perm[:, j])
                if te_perm >= te_results[pair]["te"]:
                    perm_counts[pair] += 1

    # T4: p-values
    for pair in te_results:
        p_val = (perm_counts[pair] + 1) / (N_PERM + 1)
        te_results[pair]["p_perm"] = round(p_val, 6)

    # T5: BH correction
    pairs_sorted = sorted(te_results.keys(),
                          key=lambda k: te_results[k]["p_perm"])
    m = len(pairs_sorted)
    for rank, pair in enumerate(pairs_sorted, 1):
        p_raw = te_results[pair]["p_perm"]
        p_bh = min(1.0, p_raw * m / rank)
        te_results[pair]["p_bh"] = round(p_bh, 6)
        te_results[pair]["bh_rank"] = rank

    # Print results
    print(f"\n[{EXP}] === Results (sorted by p-value) ===")
    print(f"  {'Pair':20s}  {'TE':>8s}  {'p_perm':>8s}  {'p_BH':>8s}  sig?")
    n_sig_bh = 0
    n_sig_raw = 0
    for pair in pairs_sorted:
        r = te_results[pair]
        sig = "***" if r["p_bh"] < 0.05 else ("*" if r["p_perm"] < 0.01 else "")
        if r["p_bh"] < 0.05:
            n_sig_bh += 1
        if r["p_perm"] < 0.01:
            n_sig_raw += 1
        print(f"  {pair:20s}  {r['te']:8.6f}  {r['p_perm']:8.4f}  {r['p_bh']:8.4f}  {sig}")

    # T6: Compare canonical vs reverse
    print(f"\n[{EXP}] === T6: Canonical vs reverse ordering ===")
    binned_rev = binned[::-1]
    te_canon_sum = sum(r["te"] for r in te_results.values())
    te_rev_sum = 0
    for i in range(5):
        for j in range(5):
            if i == j:
                continue
            te_rev_sum += _transfer_entropy(binned_rev[:, i], binned_rev[:, j])

    print(f"  Total TE (canonical): {te_canon_sum:.6f}")
    print(f"  Total TE (reverse):   {te_rev_sum:.6f}")
    print(f"  Ratio canonical/reverse: {te_canon_sum / te_rev_sum:.4f}" if te_rev_sum > 0 else "  Reverse TE = 0")

    # --- Verdict ---
    if n_sig_bh >= 3:
        verdict = "SIGNIFICANT"
    elif n_sig_raw >= 1:
        verdict = "SUGGESTIVE"
    else:
        verdict = "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  BH-significant pairs: {n_sig_bh}/20")
    print(f"  Raw p<0.01 pairs: {n_sig_raw}/20")
    print(f"  Total TE canonical: {te_canon_sum:.6f}")
    print(f"{'=' * 60}")

    report = {
        "experiment": EXP,
        "hypothesis": "H11 — Does the canonical surah ordering carry directed information flow?",
        "schema_version": 1,
        "n_surahs": len(q_units),
        "n_bins": N_BINS,
        "n_perm": N_PERM,
        "te_pairs": te_results,
        "summary": {
            "n_sig_bh": n_sig_bh,
            "n_sig_raw_p01": n_sig_raw,
            "total_te_canonical": round(te_canon_sum, 6),
            "total_te_reverse": round(te_rev_sum, 6),
        },
        "verdict": verdict,
        "runtime_seconds": round(elapsed, 2),
        "note": "Features computed with h_cond_initials (fast proxy) not CamelTools h_cond_roots",
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
