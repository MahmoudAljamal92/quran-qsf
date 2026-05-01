"""
exp77_gamma_entropy/run.py
===========================
H2: Compression Residual gamma as a Function of Entropy and Redundancy.

Motivation
    The gzip NCD residual gamma = +0.0716 measures how much extra
    compression distance a single-letter edit creates. H2 asks if gamma
    is a function of the corpus's letter entropy H and redundancy R.

Protocol (frozen before execution)
    T1. For each corpus: compute letter frequency on 28-letter rasm.
    T2. Compute H(letters) = Shannon entropy of letter distribution.
    T3. Compute R = 1 - H / H_max where H_max = log2(28).
    T4. Compute gzip NCD perturbation mean per corpus (reuse exp41 logic,
        but lighter: 10 perturbations per unit, Band-A only).
    T5. Fit gamma_i vs R_i (and H_i) with linear, power, and log models.
    T6. Report R², residuals, and whether the Quran is an outlier to
        the fit.
    T7. Bootstrap CI on fit parameters.

Pre-registered thresholds
    FUNCTIONAL:   R² >= 0.80 for best fit
    SUGGESTIVE:   R² >= 0.50
    NULL:         R² < 0.50

Reads: phase_06_phi_m.pkl -> CORPORA

Writes ONLY under results/experiments/exp77_gamma_entropy/
"""
from __future__ import annotations

import gzip
import json
import math
import random
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

EXP = "exp77_gamma_entropy"
SEED = 42
N_PERT = 10
GZIP_LEVEL = 9
BAND_A_LO, BAND_A_HI = 15, 100

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ALPH_IDX = {c: i for i, c in enumerate(ARABIC_CONS_28)}
DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)
_FOLD = {
    "ء": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "ا", "ئ": "ا",
    "ة": "ه", "ى": "ي",
}
H_MAX = math.log2(28)


def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)


def _letters_28(text: str) -> str:
    out = []
    for c in _strip_d(text):
        if c in _FOLD:
            out.append(_FOLD[c])
        elif c in _ALPH_IDX:
            out.append(c)
    return "".join(out)


def _gz_len(s: str) -> int:
    return len(gzip.compress(s.encode("utf-8"), compresslevel=GZIP_LEVEL))


def _ncd(a: str, b: str) -> float:
    if not a and not b:
        return 0.0
    za, zb = _gz_len(a), _gz_len(b)
    zab = _gz_len(a + b)
    return (zab - min(za, zb)) / max(1, max(za, zb))


def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


def _apply_perturbation(verses, rng):
    """Single internal letter swap."""
    nv = len(verses)
    if nv < 5:
        return None
    cons = list(ARABIC_CONS_28)
    vi_choices = list(range(1, nv - 1))
    rng.shuffle(vi_choices)
    for vi in vi_choices:
        toks = _strip_d(verses[vi]).split()
        if len(toks) < 3:
            continue
        wi_choices = list(range(1, len(toks) - 1))
        rng.shuffle(wi_choices)
        for wi in wi_choices:
            w = toks[wi]
            alpha_pos = [i for i, c in enumerate(w) if c.isalpha()]
            if len(alpha_pos) < 3:
                continue
            interior = alpha_pos[1:-1]
            if not interior:
                continue
            pos = rng.choice(interior)
            orig = w[pos]
            cands = [c for c in cons if c != orig]
            if not cands:
                continue
            repl = rng.choice(cands)
            new_w = w[:pos] + repl + w[pos + 1:]
            new_toks = list(toks)
            new_toks[wi] = new_w
            new_v = list(verses)
            new_v[vi] = " ".join(new_toks)
            return new_v, vi
    return None


def _letter_entropy(units) -> tuple[float, dict]:
    """Compute Shannon entropy of 28-letter rasm distribution."""
    counter = Counter()
    for u in units:
        for v in u.verses:
            for c in _letters_28(v):
                counter[c] += 1
    total = sum(counter.values())
    if total == 0:
        return 0.0, {}
    probs = {c: n / total for c, n in counter.items()}
    H = -sum(p * math.log2(p) for p in probs.values() if p > 0)
    return H, probs


def _corpus_gamma(units, n_pert=N_PERT) -> list[float]:
    """Compute per-unit mean NCD for single-letter perturbations."""
    ba = _band_a(units)
    ncds = []
    rng = random.Random(SEED)
    for u in ba:
        rng_u = random.Random(rng.randrange(1 << 30))
        for _ in range(n_pert):
            result = _apply_perturbation(u.verses, rng_u)
            if result is None:
                continue
            pert_v, vi = result
            a = _letters_28(" ".join(u.verses))
            b = _letters_28(" ".join(pert_v))
            ncds.append(_ncd(a, b))
    return ncds


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

        # T1-T3: Letter entropy
        H, probs = _letter_entropy(units)
        R = 1.0 - H / H_MAX if H_MAX > 0 else 0

        # T4: NCD perturbation gamma
        ncds = _corpus_gamma(units)
        gamma = float(np.mean(ncds)) if ncds else float("nan")
        gamma_std = float(np.std(ncds, ddof=1)) if len(ncds) > 1 else float("nan")

        results[cname] = {
            "n_units_bandA": len(_band_a(units)),
            "n_perturbations": len(ncds),
            "H_letters": round(H, 4),
            "H_max": round(H_MAX, 4),
            "R_redundancy": round(R, 4),
            "gamma_mean": round(gamma, 6),
            "gamma_std": round(gamma_std, 6),
        }

        dt = time.time() - t_start
        print(f"[{EXP}] {cname:20s}: H={H:.4f}  R={R:.4f}  "
              f"γ={gamma:.6f}±{gamma_std:.6f}  n_pert={len(ncds)}  ({dt:.1f}s)")

    # --- T5: Fit gamma vs R and H ---
    print(f"\n[{EXP}] === T5: Fitting gamma = f(R) and gamma = f(H) ===")

    names = list(results.keys())
    gammas = np.array([results[n]["gamma_mean"] for n in names])
    Rs = np.array([results[n]["R_redundancy"] for n in names])
    Hs = np.array([results[n]["H_letters"] for n in names])

    valid = np.isfinite(gammas) & np.isfinite(Rs)
    g_v, R_v, H_v = gammas[valid], Rs[valid], Hs[valid]
    names_v = [n for n, v in zip(names, valid) if v]

    # Linear: gamma = a * R + b
    if len(g_v) >= 3:
        slope_R, intercept_R, r_R, p_R, se_R = sp_stats.linregress(R_v, g_v)
        r2_R = r_R ** 2
        print(f"  Linear γ = {slope_R:.6f}·R + {intercept_R:.6f}  R²={r2_R:.4f}  p={p_R:.4e}")

        slope_H, intercept_H, r_H, p_H, se_H = sp_stats.linregress(H_v, g_v)
        r2_H = r_H ** 2
        print(f"  Linear γ = {slope_H:.6f}·H + {intercept_H:.6f}  R²={r2_H:.4f}  p={p_H:.4e}")

        # Power: gamma = a * R^c
        try:
            def _power(x, a, c):
                return a * np.power(x, c)
            popt_p, _ = curve_fit(_power, R_v, g_v, p0=[0.1, 1.0], maxfev=5000)
            pred_p = _power(R_v, *popt_p)
            ss_res = np.sum((g_v - pred_p) ** 2)
            ss_tot = np.sum((g_v - g_v.mean()) ** 2)
            r2_power = 1 - ss_res / ss_tot if ss_tot > 0 else 0
            print(f"  Power γ = {popt_p[0]:.6f}·R^{popt_p[1]:.4f}  R²={r2_power:.4f}")
        except Exception as e:
            r2_power = float("nan")
            popt_p = [float("nan"), float("nan")]
            print(f"  Power fit failed: {e}")

        # Residuals for Quran
        if "quran" in names_v:
            qi = names_v.index("quran")
            pred_q_lin = slope_R * R_v[qi] + intercept_R
            resid_q = g_v[qi] - pred_q_lin
            print(f"\n  Quran residual from linear fit: {resid_q:+.6f}")
            print(f"  Quran observed γ = {g_v[qi]:.6f}, predicted = {pred_q_lin:.6f}")
    else:
        r2_R = r2_H = float("nan")
        slope_R = intercept_R = p_R = float("nan")
        slope_H = intercept_H = p_H = float("nan")
        r2_power = float("nan")
        popt_p = [float("nan"), float("nan")]

    # --- T6: Quran outlier from fit ---
    print(f"\n[{EXP}] === T6: Per-corpus table ===")
    print(f"  {'Corpus':20s}  {'H':>7s}  {'R':>7s}  {'γ':>10s}  {'γ_pred':>10s}  {'resid':>10s}")
    residuals = {}
    for n in names_v:
        r = results[n]
        pred = slope_R * r["R_redundancy"] + intercept_R
        res = r["gamma_mean"] - pred
        residuals[n] = round(res, 6)
        flag = " ***" if n == "quran" else ""
        print(f"  {n:20s}  {r['H_letters']:7.4f}  {r['R_redundancy']:7.4f}  "
              f"{r['gamma_mean']:10.6f}  {pred:10.6f}  {res:+10.6f}{flag}")

    # --- Verdict ---
    best_r2 = max(r2_R, r2_H, r2_power) if all(np.isfinite([r2_R, r2_H])) else 0
    if best_r2 >= 0.80:
        verdict = "FUNCTIONAL"
    elif best_r2 >= 0.50:
        verdict = "SUGGESTIVE"
    else:
        verdict = "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Best R² = {best_r2:.4f}")
    print(f"  γ = {slope_R:.6f}·R + {intercept_R:.6f} (R²={r2_R:.4f})")
    print(f"  γ = {slope_H:.6f}·H + {intercept_H:.6f} (R²={r2_H:.4f})")
    print(f"{'=' * 60}")

    report = {
        "experiment": EXP,
        "hypothesis": "H2 — Is gamma (gzip NCD residual) a function of letter entropy?",
        "schema_version": 1,
        "per_corpus": results,
        "fits": {
            "linear_R": {
                "slope": round(float(slope_R), 6),
                "intercept": round(float(intercept_R), 6),
                "R2": round(float(r2_R), 4),
                "p": float(p_R),
            },
            "linear_H": {
                "slope": round(float(slope_H), 6),
                "intercept": round(float(intercept_H), 6),
                "R2": round(float(r2_H), 4),
                "p": float(p_H),
            },
            "power_R": {
                "a": round(float(popt_p[0]), 6),
                "c": round(float(popt_p[1]), 4),
                "R2": round(float(r2_power), 4),
            },
        },
        "residuals": residuals,
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
