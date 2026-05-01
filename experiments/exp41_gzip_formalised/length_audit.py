"""
exp41_gzip_formalised/length_audit.py
=====================================
Audit patch for exp41's d=+0.534 result: is it a genuine structural
signal or a length confound?

NCD(canonical, canonical-with-1-letter-edit) ~ const / Z(canonical),
so shorter documents mechanically produce higher NCD. If Band-A Quran
surahs are systematically shorter than Band-A ctrl units in letter
count, the positive Cohen d could be an artefact.

This script:
  1. Recomputes NCD per (unit, perturbation) paired with the unit's
     letter count.
  2. Reports Spearman rho(NCD, letter_count) pooled and per group.
  3. Stratifies units into letter-count deciles and reports
     within-decile median NCD for Quran vs ctrl.
  4. Fits log-linear regression
        log NCD = alpha + beta * log(n_letters) + gamma * I(group=Quran)
     and reports gamma with 95% CI. A non-zero gamma after length
     control is the structural signal.

Writes to results/experiments/exp41_gzip_formalised/length_audit.json
(separate from the main JSON).
"""
from __future__ import annotations

import gzip
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
from scipy import stats

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase, safe_output_dir,
)

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
BAND_A_LO, BAND_A_HI = 15, 100
SEED = 42
N_PERT = 20
CTRL_N_UNITS = 200
GZIP_LEVEL = 9

ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ALPH_IDX = {c: i for i, c in enumerate(ARABIC_CONS_28)}
DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)
_FOLD = {"ء": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "ا", "ئ": "ا",
         "ة": "ه", "ى": "ي"}


def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)


def _letters_28(text: str) -> str:
    out: list[str] = []
    for c in _strip_d(text):
        if c in _FOLD:
            out.append(_FOLD[c])
        elif c in _ALPH_IDX:
            out.append(c)
    return "".join(out)


def _gz_len(s: str) -> int:
    return len(gzip.compress(s.encode("utf-8"), compresslevel=GZIP_LEVEL))


def ncd(a: str, b: str) -> float:
    za = _gz_len(a); zb = _gz_len(b); zab = _gz_len(a + b)
    denom = max(1, max(za, zb))
    return (zab - min(za, zb)) / denom


def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


def _apply_perturbation(verses, rng):
    nv = len(verses)
    if nv < 5:
        return None
    vi_choices = list(range(1, nv - 1))
    rng.shuffle(vi_choices)
    cons = list(ARABIC_CONS_28)
    for vi in vi_choices:
        toks = _strip_d(verses[vi]).split()
        if len(toks) < 3:
            continue
        wi_choices = list(range(1, len(toks) - 1))
        rng.shuffle(wi_choices)
        for wi in wi_choices:
            w = toks[wi]
            ap = [i for i, c in enumerate(w) if c.isalpha()]
            if len(ap) < 3:
                continue
            interior = ap[1:-1]
            if not interior:
                continue
            pos = rng.choice(interior)
            original = w[pos]
            repl = rng.choice([c for c in cons if c != original])
            new_w = w[:pos] + repl + w[pos + 1:]
            new_toks = list(toks); new_toks[wi] = new_w
            new_v = list(verses); new_v[vi] = " ".join(new_toks)
            return new_v, vi
    return None


def _unit_rows(units, group: str, rng_seed: int) -> list[dict]:
    rng = random.Random(rng_seed)
    rows: list[dict] = []
    for u in units:
        rng_u = random.Random(rng.randrange(1 << 30))
        canon = _letters_28(" ".join(u.verses))
        n_let = len(canon)
        if n_let < 50:
            continue
        for _ in range(N_PERT):
            out_p = _apply_perturbation(u.verses, rng_u)
            if out_p is None:
                continue
            pert, _vi = out_p
            edited = _letters_28(" ".join(pert))
            v = ncd(canon, edited)
            if math.isfinite(v):
                rows.append({
                    "group": group,
                    "n_letters": n_let,
                    "ncd": v,
                    "unit_label": getattr(u, "label", ""),
                })
    return rows


def main() -> int:
    out = safe_output_dir("exp41_gzip_formalised")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    q_units = _band_a(CORPORA.get("quran", []))
    ctrl_pool = []
    for name in ARABIC_CTRL:
        ctrl_pool.extend(_band_a(CORPORA.get(name, [])))
    rng = random.Random(SEED + 1)
    rng.shuffle(ctrl_pool)
    ctrl_units = ctrl_pool[:CTRL_N_UNITS]

    q_rows = _unit_rows(q_units, "quran", SEED)
    c_rows = _unit_rows(ctrl_units, "ctrl", SEED + 2)

    # -------- 1. Per-group letter-count distribution -------- #
    q_n = [r["n_letters"] for r in q_rows]
    c_n = [r["n_letters"] for r in c_rows]
    q_ncd = [r["ncd"] for r in q_rows]
    c_ncd = [r["ncd"] for r in c_rows]

    print(f"[length_audit] Band-A unit letter-count stats:")
    print(f"   Quran  median n_letters = {np.median(q_n):.0f}  "
          f"iqr = {np.percentile(q_n, 25):.0f}..{np.percentile(q_n, 75):.0f}")
    print(f"   Ctrl   median n_letters = {np.median(c_n):.0f}  "
          f"iqr = {np.percentile(c_n, 25):.0f}..{np.percentile(c_n, 75):.0f}")

    # -------- 2. Spearman rho(NCD, n_letters) -------- #
    rho_q, p_rho_q = stats.spearmanr(q_ncd, q_n)
    rho_c, p_rho_c = stats.spearmanr(c_ncd, c_n)
    rho_all, p_rho_all = stats.spearmanr(
        q_ncd + c_ncd, q_n + c_n,
    )
    print(f"[length_audit] Spearman rho(NCD, n_letters):")
    print(f"   Quran only: rho = {rho_q:+.3f}  p = {p_rho_q:.3e}")
    print(f"   Ctrl only:  rho = {rho_c:+.3f}  p = {p_rho_c:.3e}")
    print(f"   Pooled:     rho = {rho_all:+.3f}  p = {p_rho_all:.3e}")

    # -------- 3. Stratified by letter-count deciles -------- #
    all_n = np.array(q_n + c_n)
    all_groups = np.array([r["group"] for r in q_rows + c_rows])
    all_ncd = np.array(q_ncd + c_ncd)
    deciles = np.percentile(all_n, np.arange(0, 101, 10))
    decile_rows = []
    print(f"[length_audit] Decile-stratified NCD medians:")
    print(f"   {'decile':>6s}  {'n_let_range':>20s}  "
          f"{'Q_n':>4s}  {'Q_med':>8s}  {'C_n':>5s}  {'C_med':>8s}  "
          f"{'d_Q-C':>7s}  {'MW_pg':>10s}")
    for i in range(10):
        lo, hi = deciles[i], deciles[i + 1]
        mask = (all_n >= lo) & (all_n <= hi)
        g_mask = all_groups[mask]
        n_mask = all_n[mask]
        v_mask = all_ncd[mask]
        q_in = v_mask[g_mask == "quran"]
        c_in = v_mask[g_mask == "ctrl"]
        nq, nc = len(q_in), len(c_in)
        q_med = float(np.median(q_in)) if nq else float("nan")
        c_med = float(np.median(c_in)) if nc else float("nan")
        if nq >= 3 and nc >= 3:
            try:
                pg = float(stats.mannwhitneyu(
                    q_in, c_in, alternative="greater",
                ).pvalue)
            except ValueError:
                pg = float("nan")
            if len(q_in) >= 2 and len(c_in) >= 2:
                pv = ((len(q_in) - 1) * np.var(q_in, ddof=1) +
                      (len(c_in) - 1) * np.var(c_in, ddof=1)) / \
                     (len(q_in) + len(c_in) - 2)
                d_qc = float((np.mean(q_in) - np.mean(c_in)) /
                             math.sqrt(pv)) if pv > 0 else float("nan")
            else:
                d_qc = float("nan")
        else:
            pg, d_qc = float("nan"), float("nan")
        decile_rows.append({
            "decile": i + 1,
            "n_letters_lo": float(lo), "n_letters_hi": float(hi),
            "n_q": nq, "n_ctrl": nc,
            "q_median_ncd": q_med, "ctrl_median_ncd": c_med,
            "cohen_d": d_qc, "mw_p_greater": pg,
        })
        print(f"   {i+1:>6d}  {int(lo):>8d}..{int(hi):<10d}  "
              f"{nq:>4d}  {q_med:>8.4f}  {nc:>5d}  {c_med:>8.4f}  "
              f"{d_qc:>+7.3f}  {pg:>10.3e}")

    # -------- 4. Log-linear regression -------- #
    # log NCD = alpha + beta * log(n_letters) + gamma * I(Quran)
    n_arr = np.asarray(all_n, dtype=float)
    v_arr = np.asarray(all_ncd, dtype=float)
    g_arr = np.asarray([1.0 if g == "quran" else 0.0 for g in all_groups])
    # drop any zeros
    keep = (v_arr > 0) & (n_arr > 0)
    n_log = np.log(n_arr[keep])
    v_log = np.log(v_arr[keep])
    g_k = g_arr[keep]
    X = np.column_stack([np.ones_like(n_log), n_log, g_k])
    beta_hat, res, rank, sv = np.linalg.lstsq(X, v_log, rcond=None)
    resid = v_log - X @ beta_hat
    dof = len(v_log) - X.shape[1]
    s2 = float((resid @ resid) / dof)
    cov = s2 * np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    gamma = float(beta_hat[2])
    gamma_se = float(se[2])
    # 95% CI
    tcrit = stats.t.ppf(0.975, dof)
    gamma_lo = gamma - tcrit * gamma_se
    gamma_hi = gamma + tcrit * gamma_se
    # Two-sided p for H0: gamma=0
    tstat = gamma / gamma_se if gamma_se > 0 else float("nan")
    p_gamma = float(2 * (1 - stats.t.cdf(abs(tstat), dof))) \
        if math.isfinite(tstat) else float("nan")
    print(f"[length_audit] Log-linear regression "
          f"log NCD = a + b*log(n_letters) + gamma*I(Q):")
    print(f"   beta (length slope) = {float(beta_hat[1]):+.4f}  "
          f"se = {float(se[1]):.4f}")
    print(f"   gamma (Q effect after length control) = {gamma:+.4f}  "
          f"95% CI = [{gamma_lo:+.4f}, {gamma_hi:+.4f}]  p = {p_gamma:.3e}")

    result = {
        "purpose": "Audit the d=+0.534 gzip NCD result for length confound",
        "band": {"lo": BAND_A_LO, "hi": BAND_A_HI},
        "n_quran_units": len(q_units),
        "n_ctrl_units": len(ctrl_units),
        "letter_count_dist": {
            "quran_median": float(np.median(q_n)),
            "quran_iqr_lo": float(np.percentile(q_n, 25)),
            "quran_iqr_hi": float(np.percentile(q_n, 75)),
            "ctrl_median": float(np.median(c_n)),
            "ctrl_iqr_lo": float(np.percentile(c_n, 25)),
            "ctrl_iqr_hi": float(np.percentile(c_n, 75)),
        },
        "spearman_ncd_vs_nletters": {
            "quran": {"rho": float(rho_q), "p": float(p_rho_q)},
            "ctrl":  {"rho": float(rho_c), "p": float(p_rho_c)},
            "pooled":{"rho": float(rho_all), "p": float(p_rho_all)},
        },
        "decile_stratified": decile_rows,
        "log_linear_regression": {
            "formula": "log NCD = alpha + beta*log(n_letters) + gamma*I(Quran)",
            "beta_length_slope": float(beta_hat[1]),
            "beta_length_se": float(se[1]),
            "gamma_quran_effect": gamma,
            "gamma_se": gamma_se,
            "gamma_ci95": [gamma_lo, gamma_hi],
            "gamma_p_two_sided": p_gamma,
            "n_obs": int(X.shape[0]),
            "dof": int(dof),
        },
        "verdict": (
            "GENUINE_STRUCTURAL_SIGNAL_AFTER_LENGTH_CONTROL"
            if math.isfinite(p_gamma) and p_gamma < 0.05 and gamma > 0
            else "LENGTH_CONFOUND" if math.isfinite(p_gamma) and p_gamma >= 0.05
            else "REVERSES_AFTER_LENGTH_CONTROL" if math.isfinite(p_gamma) and gamma < 0
            else "INCONCLUSIVE"
        ),
    }
    outfile = out / "length_audit.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[length_audit] VERDICT: {result['verdict']}")
    print(f"[length_audit] wrote {outfile}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
