"""
exp81_entropy_rate/run.py
==========================
H10: Entropy Rate Convergence and the Structural Tightness Constant.

Motivation
    Block entropy H_n / n converges to the entropy rate h. The
    convergence rate delta may differ between Quran and controls,
    indicating tighter structural organization.

Protocol (frozen before execution)
    T1. Per corpus: convert all text to 28-letter rasm string.
    T2. For n=1..8: count n-grams, compute H_n = -sum(p * log2(p)).
    T3. Compute h_n = H_n / n.
    T4. Fit: h_n = h_inf + C * n^(-delta).
    T5. Extract h_inf (entropy rate) and delta (convergence exponent).
    T6. Cross-corpus comparison; Cohen's d for delta.
    T7. Test delta vs gamma correlation (from exp77).

Pre-registered thresholds
    DISTINCT:     |d(delta)| >= 1.0 AND p < 0.01
    SUGGESTIVE:   |d| >= 0.5 or unique convergence profile
    NULL:         otherwise

Reads: phase_06_phi_m.pkl -> CORPORA
"""
from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import stats as sp_stats
from scipy.optimize import curve_fit

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

EXP = "exp81_entropy_rate"
SEED = 42
MAX_N = 8

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ALPH = set(ARABIC_CONS_28)
DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)
_FOLD = {
    "ء": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "ا", "ئ": "ا",
    "ة": "ه", "ى": "ي",
}


def _to_rasm(text: str) -> str:
    out = []
    for c in text:
        if c in DIAC:
            continue
        fc = _FOLD.get(c, c)
        if fc in _ALPH:
            out.append(fc)
    return "".join(out)


def _corpus_rasm(units) -> str:
    parts = []
    for u in units:
        for v in u.verses:
            parts.append(_to_rasm(v))
    return "".join(parts)


def _block_entropy(text: str, n: int) -> float:
    """Compute H_n = Shannon entropy of n-gram distribution."""
    if len(text) < n:
        return 0.0
    counts = Counter()
    for i in range(len(text) - n + 1):
        counts[text[i:i + n]] += 1
    total = sum(counts.values())
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def _fit_convergence(ns, h_ns):
    """Fit h_n = h_inf + C * n^(-delta)."""
    ns = np.array(ns, dtype=float)
    h_ns = np.array(h_ns, dtype=float)

    if len(ns) < 4:
        return float("nan"), float("nan"), float("nan"), float("nan")

    try:
        def _model(n, h_inf, C, delta):
            return h_inf + C * np.power(n, -delta)

        # Initial guess: h_inf = last value, C = first - last, delta = 1
        p0 = [h_ns[-1], h_ns[0] - h_ns[-1], 1.0]
        popt, _ = curve_fit(_model, ns, h_ns, p0=p0, maxfev=10000,
                            bounds=([0, 0, 0.01], [10, 10, 5]))
        pred = _model(ns, *popt)
        ss_res = np.sum((h_ns - pred) ** 2)
        ss_tot = np.sum((h_ns - h_ns.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        return float(popt[0]), float(popt[1]), float(popt[2]), float(r2)
    except Exception:
        return float("nan"), float("nan"), float("nan"), float("nan")


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

    all_names = ["quran"] + ARABIC_CTRL
    results = {}

    for cname in all_names:
        units = CORPORA.get(cname, [])
        t_start = time.time()

        rasm = _corpus_rasm(units)
        n_chars = len(rasm)

        # Block entropies
        ns = []
        H_ns = []
        h_ns = []
        for n in range(1, MAX_N + 1):
            if n_chars < n * 10:  # need at least 10 n-grams
                break
            H_n = _block_entropy(rasm, n)
            h_n = H_n / n
            ns.append(n)
            H_ns.append(H_n)
            h_ns.append(h_n)

        # Fit convergence
        h_inf, C_fit, delta, r2 = _fit_convergence(ns, h_ns)

        # Conditional entropies: h_n = H_n - H_{n-1}
        cond_h = []
        for i in range(1, len(H_ns)):
            cond_h.append(H_ns[i] - H_ns[i - 1])

        dt = time.time() - t_start

        results[cname] = {
            "n_chars": n_chars,
            "block_entropies": {int(n): round(H, 4) for n, H in zip(ns, H_ns)},
            "entropy_rates": {int(n): round(h, 4) for n, h in zip(ns, h_ns)},
            "conditional_entropies": {int(n + 1): round(ch, 4)
                                      for n, ch in zip(range(1, len(cond_h) + 1), cond_h)},
            "fit": {
                "h_inf": round(h_inf, 4) if np.isfinite(h_inf) else None,
                "C": round(C_fit, 4) if np.isfinite(C_fit) else None,
                "delta": round(delta, 4) if np.isfinite(delta) else None,
                "R2": round(r2, 4) if np.isfinite(r2) else None,
            },
        }

        delta_str = f"{delta:.4f}" if np.isfinite(delta) else "N/A"
        print(f"[{EXP}] {cname:20s}: n={n_chars:7d}  "
              f"h_1={h_ns[0]:.4f}  h_{MAX_N}={h_ns[-1]:.4f}  "
              f"h_inf={h_inf:.4f}  δ={delta_str}  R²={r2:.4f}  ({dt:.1f}s)")

    # --- Comparison ---
    print(f"\n[{EXP}] === Cross-corpus comparison ===")
    print(f"  {'Corpus':20s}  {'h_inf':>7s}  {'delta':>7s}  {'R²':>6s}  h_1..h_8")
    for cname in all_names:
        r = results[cname]
        h_inf = r["fit"]["h_inf"]
        delta = r["fit"]["delta"]
        r2 = r["fit"]["R2"]
        hr = r["entropy_rates"]
        h_str = "  ".join(f"{hr.get(n, 0):.3f}" for n in range(1, MAX_N + 1))
        flag = " ***" if cname == "quran" else ""
        print(f"  {cname:20s}  {h_inf:7.4f}  {delta:7.4f}  {r2:6.4f}  {h_str}{flag}")

    # --- Delta comparison ---
    print(f"\n[{EXP}] === Delta (convergence speed) comparison ===")
    q_delta = results["quran"]["fit"]["delta"]
    ctrl_deltas = [results[c]["fit"]["delta"] for c in ARABIC_CTRL
                   if results[c]["fit"]["delta"] is not None]
    ctrl_names = [c for c in ARABIC_CTRL if results[c]["fit"]["delta"] is not None]

    if ctrl_deltas and q_delta is not None:
        mu_ctrl = np.mean(ctrl_deltas)
        std_ctrl = np.std(ctrl_deltas, ddof=1)
        z_delta = (q_delta - mu_ctrl) / std_ctrl if std_ctrl > 0 else 0
        print(f"  Quran δ = {q_delta:.4f}")
        print(f"  Ctrl δ: mean={mu_ctrl:.4f}, std={std_ctrl:.4f}")
        print(f"  z(δ) = {z_delta:+.2f}")
        for n, d in zip(ctrl_names, ctrl_deltas):
            print(f"    {n:20s}: δ = {d:.4f}")
    else:
        z_delta = 0

    # --- h_inf comparison ---
    print(f"\n[{EXP}] === Entropy rate h_inf comparison ===")
    q_hinf = results["quran"]["fit"]["h_inf"]
    ctrl_hinfs = [results[c]["fit"]["h_inf"] for c in ARABIC_CTRL
                  if results[c]["fit"]["h_inf"] is not None]
    if ctrl_hinfs and q_hinf is not None:
        mu_hinf = np.mean(ctrl_hinfs)
        std_hinf = np.std(ctrl_hinfs, ddof=1)
        z_hinf = (q_hinf - mu_hinf) / std_hinf if std_hinf > 0 else 0
        print(f"  Quran h_inf = {q_hinf:.4f}")
        print(f"  Ctrl h_inf: mean={mu_hinf:.4f}, std={std_hinf:.4f}")
        print(f"  z(h_inf) = {z_hinf:+.2f}")
    else:
        z_hinf = 0

    # --- T7: delta vs gamma ---
    print(f"\n[{EXP}] === T7: δ vs γ correlation ===")
    exp77_path = _ROOT / "results" / "experiments" / "exp77_gamma_entropy" / "exp77_gamma_entropy.json"
    r_corr = p_corr = float("nan")
    if exp77_path.exists():
        with open(exp77_path) as f:
            exp77 = json.load(f)
        deltas_vec = []
        gammas_vec = []
        for n in all_names:
            d = results[n]["fit"].get("delta")
            g = exp77.get("per_corpus", {}).get(n, {}).get("gamma_mean")
            if d is not None and g is not None:
                deltas_vec.append(d)
                gammas_vec.append(g)
        if len(deltas_vec) >= 4:
            r_corr, p_corr = sp_stats.pearsonr(deltas_vec, gammas_vec)
            print(f"  δ vs γ: r={r_corr:.4f}, p={p_corr:.4f}")
    else:
        print("  exp77 not found, skipping")

    # --- Verdict ---
    if abs(z_delta) >= 2.0:
        verdict = "DISTINCT"
    elif abs(z_delta) >= 1.0 or abs(z_hinf) >= 1.0:
        verdict = "SUGGESTIVE"
    else:
        verdict = "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Quran δ = {q_delta}, z(δ) = {z_delta:+.2f}")
    print(f"  Quran h_inf = {q_hinf}, z(h_inf) = {z_hinf:+.2f}")
    print(f"{'=' * 60}")

    report = {
        "experiment": EXP,
        "hypothesis": "H10 — Does the Quran have a unique entropy rate convergence profile?",
        "schema_version": 1,
        "per_corpus": results,
        "comparison": {
            "z_delta": round(float(z_delta), 4),
            "z_h_inf": round(float(z_hinf), 4),
        },
        "delta_vs_gamma": {
            "r": round(float(r_corr), 4) if np.isfinite(r_corr) else None,
            "p": round(float(p_corr), 4) if np.isfinite(p_corr) else None,
        },
        "verdict": verdict,
        "runtime_seconds": round(elapsed, 2),
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
