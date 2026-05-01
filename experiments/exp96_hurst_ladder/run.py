"""
exp96_hurst_ladder/run.py
==========================
Multi-Scale Hurst Ladder Scaling Law (H31).

Tests whether the Quran's four-scale Hurst exponents
(letter, word, delta, verse) follow a closed-form log-scaling law
    H(k) = alpha + beta * log2(k),   k in {1, 2, 3, 4}
with R² >= 0.95 AND beta < -0.05, and whether beta matches any of a
pre-registered short list of physics constants within +/- 0.03.

Backup evidence (Gem #4, LOST_GEMS §4): H_verse ~ 0.898, H_delta ~
0.811, H_word ~ 0.652, H_letter ~ 0.537 (monotone decrease).

Pre-registered verdict ladder (see PREREG.md §5):
    FAIL_insufficient_data            n_q with all 4 finite H < 40
    FAIL_not_monotone                 Quran H(k) not strictly decreasing
    FAIL_low_r2                       scaling-law fit R² < 0.95
    PARTIAL_monotone_no_scaling       monotone, low R²
    PASS_scaling_law                  monotone AND R² >= 0.95 AND beta < -0.05
    PASS_scaling_law_plus_constant    PASS + beta matches a physics target
    QURAN_SPECIFIC (orthogonal flag)  Quran beta differs from every ctrl by >= 2 SE

Reads (integrity-checked):
    phase_06_phi_m.pkl -> state['CORPORA']

Writes ONLY under results/experiments/exp96_hurst_ladder/
"""
from __future__ import annotations

import json
import math
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

EXP = "exp96_hurst_ladder"

# --- Frozen constants (mirror PREREG §9) -----------------------------------
SEED = 42
BAND_A_LO, BAND_A_HI = 15, 100
N_MIN_RS = 8
N_MIN_SERIES = 16
RS_WINDOW_LOG_STEPS = 8
BOOTSTRAP_N = 1000
MONOTONE_TOL = 0.02
R2_GATE = 0.95
BETA_CONSTANT_TOL = 0.03
QURAN_SPECIFIC_SE_K = 2.0

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ALPH_IDX = {c: i + 1 for i, c in enumerate(ARABIC_CONS_28)}  # 1..28
DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)
_FOLD = {
    "ء": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "ا", "ئ": "ا",
    "ة": "ه",
    "ى": "ي",
}

SCALE_NAMES = ["letter", "word", "delta", "verse"]  # k=1,2,3,4
SCALE_K = {"letter": 1, "word": 2, "delta": 3, "verse": 4}

# Pre-registered physics-constant targets for beta
_PHI = (1.0 + math.sqrt(5.0)) / 2.0
EULER_MASCHERONI = 0.5772156649015329
BETA_TARGETS = {
    "neg_one_over_2pi":       -1.0 / (2.0 * math.pi),
    "neg_log10_e":            -math.log10(math.e),
    "neg_one_over_pi":        -1.0 / math.pi,
    "neg_one_over_phi":       -1.0 / _PHI,
    "neg_one_over_e":         -1.0 / math.e,
    "neg_euler_mascheroni":   -EULER_MASCHERONI,
    "neg_one_half":           -0.5,
    "neg_one_third":          -1.0 / 3.0,
}


# --- Text primitives (byte-equal to exp41/exp43/exp93) ---------------------
def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)


def _letters_stream_28(text: str) -> list[int]:
    """Return the 1..28 consonant-index stream of a text (no spaces)."""
    out: list[int] = []
    for c in _strip_d(text):
        if c in _FOLD:
            out.append(_ALPH_IDX[_FOLD[c]])
        elif c in _ALPH_IDX:
            out.append(_ALPH_IDX[c])
    return out


def _word_length_seq(verses: list[str]) -> list[int]:
    """Length-in-letters of each whitespace-delimited word, verse-flattened."""
    out: list[int] = []
    for v in verses:
        for w in _strip_d(v).split():
            n = sum(1 for c in w if c in _ALPH_IDX or c in _FOLD)
            if n > 0:
                out.append(n)
    return out


def _verse_len_seq(verses: list[str]) -> list[int]:
    """Length-in-letters of each verse."""
    return [len(_letters_stream_28(v)) for v in verses]


def _delta_seq(verse_lens: list[int]) -> list[int]:
    """Adjacent differences of a verse-length sequence."""
    return [verse_lens[i + 1] - verse_lens[i] for i in range(len(verse_lens) - 1)]


def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


# --- Hurst estimators ------------------------------------------------------
def _rs_hurst(x: np.ndarray, n_min: int = N_MIN_RS) -> float:
    """Classical R/S Hurst via log-log regression over log-spaced window sizes."""
    x = np.asarray(x, dtype=float)
    N = x.size
    if N < max(n_min * 2, N_MIN_SERIES):
        return float("nan")
    # log-spaced window sizes from n_min to N // 2
    n_max = N // 2
    if n_max < n_min:
        return float("nan")
    ns = np.unique(np.round(np.logspace(
        math.log10(n_min), math.log10(n_max), RS_WINDOW_LOG_STEPS
    )).astype(int))
    ns = ns[(ns >= n_min) & (ns <= n_max)]
    if ns.size < 3:
        return float("nan")
    log_rs_means = []
    log_ns_kept = []
    for n in ns:
        n_wins = N // n
        if n_wins < 1:
            continue
        rs_samples = []
        for w in range(n_wins):
            seg = x[w * n:(w + 1) * n]
            mu = seg.mean()
            y = np.cumsum(seg - mu)
            R = y.max() - y.min()
            S = seg.std(ddof=1)
            if S > 0:
                rs_samples.append(R / S)
        if rs_samples:
            log_rs_means.append(math.log(float(np.mean(rs_samples))))
            log_ns_kept.append(math.log(float(n)))
    if len(log_ns_kept) < 3:
        return float("nan")
    slope, _intercept = np.polyfit(log_ns_kept, log_rs_means, 1)
    return float(slope)


def _dfa_hurst(x: np.ndarray, n_min: int = N_MIN_RS) -> float:
    """Detrended Fluctuation Analysis Hurst (Peng et al. 1994)."""
    x = np.asarray(x, dtype=float)
    N = x.size
    if N < max(n_min * 2, N_MIN_SERIES):
        return float("nan")
    y = np.cumsum(x - x.mean())
    n_max = N // 2
    if n_max < n_min:
        return float("nan")
    ns = np.unique(np.round(np.logspace(
        math.log10(n_min), math.log10(n_max), RS_WINDOW_LOG_STEPS
    )).astype(int))
    ns = ns[(ns >= n_min) & (ns <= n_max)]
    if ns.size < 3:
        return float("nan")
    log_fs, log_ns_kept = [], []
    for n in ns:
        n_wins = N // n
        if n_wins < 1:
            continue
        resid_sq = []
        for w in range(n_wins):
            seg = y[w * n:(w + 1) * n]
            t = np.arange(n, dtype=float)
            # linear detrend
            slope, intercept = np.polyfit(t, seg, 1)
            trend = slope * t + intercept
            resid = seg - trend
            resid_sq.append(np.mean(resid ** 2))
        if resid_sq:
            F = math.sqrt(float(np.mean(resid_sq)))
            if F > 0:
                log_fs.append(math.log(F))
                log_ns_kept.append(math.log(float(n)))
    if len(log_ns_kept) < 3:
        return float("nan")
    slope, _intercept = np.polyfit(log_ns_kept, log_fs, 1)
    return float(slope)


# --- Per-surah ladder ------------------------------------------------------
def _ladder_for_unit(u) -> dict:
    """Compute 4-scale H for one surah-like unit. Returns dict of
    {scale: {H_RS, H_DFA, n_points}} plus NaN if too short."""
    letter_seq = _letters_stream_28(" ".join(u.verses))
    word_seq = _word_length_seq(u.verses)
    verse_seq = _verse_len_seq(u.verses)
    delta_seq = _delta_seq(verse_seq)

    streams = {
        "letter": letter_seq,
        "word": word_seq,
        "delta": delta_seq,
        "verse": verse_seq,
    }
    out = {}
    for name, seq in streams.items():
        arr = np.asarray(seq, dtype=float)
        if arr.size < N_MIN_SERIES:
            out[name] = {
                "H_RS": float("nan"), "H_DFA": float("nan"),
                "n_points": int(arr.size),
            }
            continue
        out[name] = {
            "H_RS": _rs_hurst(arr),
            "H_DFA": _dfa_hurst(arr),
            "n_points": int(arr.size),
        }
    return out


# --- Scaling-law fit -------------------------------------------------------
def _fit_scaling_law(Hk_mean: dict[str, float]) -> dict:
    """Fit H(k) = alpha + beta * log2(k) over k ∈ {1..4}.
    Returns alpha, beta, r2, predicted values, residuals."""
    xs, ys = [], []
    for name in SCALE_NAMES:
        k = SCALE_K[name]
        h = Hk_mean.get(name, float("nan"))
        if np.isfinite(h):
            xs.append(math.log2(k))
            ys.append(h)
    if len(xs) < 3:
        return {
            "alpha": float("nan"), "beta": float("nan"),
            "r2": float("nan"), "n": len(xs),
        }
    xs_arr = np.asarray(xs, dtype=float)
    ys_arr = np.asarray(ys, dtype=float)
    slope, intercept = np.polyfit(xs_arr, ys_arr, 1)
    y_pred = slope * xs_arr + intercept
    ss_res = float(np.sum((ys_arr - y_pred) ** 2))
    ss_tot = float(np.sum((ys_arr - ys_arr.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return {
        "alpha": float(intercept),
        "beta": float(slope),
        "r2": float(r2),
        "n": int(len(xs)),
        "residuals": {name: float(Hk_mean[name] - (slope * math.log2(SCALE_K[name]) + intercept))
                      for name in SCALE_NAMES if name in Hk_mean and np.isfinite(Hk_mean[name])},
    }


def _bootstrap_scaling(per_unit_H: dict[str, np.ndarray], n_boot: int, rng_seed: int):
    """Bootstrap the scaling-law fit by resampling surahs with replacement."""
    names = SCALE_NAMES
    # stack into (n_units, 4) where NaN indicates missing
    all_arrs = [per_unit_H[name] for name in names]
    M = np.column_stack([np.asarray(a, dtype=float) for a in all_arrs])
    n_units = M.shape[0]
    if n_units < 10:
        return None
    rng = np.random.RandomState(rng_seed)
    alphas, betas, r2s = [], [], []
    for _ in range(n_boot):
        idx = rng.choice(n_units, n_units, replace=True)
        boot = M[idx]
        # per-scale mean ignoring NaN
        means = {}
        for j, name in enumerate(names):
            col = boot[:, j]
            col = col[np.isfinite(col)]
            means[name] = float(col.mean()) if col.size else float("nan")
        fit = _fit_scaling_law(means)
        if np.isfinite(fit["beta"]):
            alphas.append(fit["alpha"])
            betas.append(fit["beta"])
            r2s.append(fit["r2"])
    if not betas:
        return None
    q = lambda arr, p: float(np.quantile(arr, p))
    return {
        "n_boot_valid": len(betas),
        "alpha": {"mean": float(np.mean(alphas)), "ci_lo": q(alphas, 0.025),
                  "ci_hi": q(alphas, 0.975), "se": float(np.std(alphas, ddof=1))},
        "beta": {"mean": float(np.mean(betas)), "ci_lo": q(betas, 0.025),
                 "ci_hi": q(betas, 0.975), "se": float(np.std(betas, ddof=1))},
        "r2": {"mean": float(np.mean(r2s)), "ci_lo": q(r2s, 0.025),
               "ci_hi": q(r2s, 0.975)},
    }


def _per_corpus_ladder(units) -> dict:
    """Compute 4-scale ladder for every unit in a list, return per-unit H matrix
    AND per-scale mean + scaling-law fit."""
    per_unit = {name: [] for name in SCALE_NAMES}
    per_unit_dfa = {name: [] for name in SCALE_NAMES}
    for u in units:
        lad = _ladder_for_unit(u)
        for name in SCALE_NAMES:
            per_unit[name].append(lad[name]["H_RS"])
            per_unit_dfa[name].append(lad[name]["H_DFA"])

    per_unit_arr = {name: np.asarray(per_unit[name], dtype=float) for name in SCALE_NAMES}
    per_unit_dfa_arr = {name: np.asarray(per_unit_dfa[name], dtype=float) for name in SCALE_NAMES}

    Hk_mean = {
        name: float(np.nanmean(per_unit_arr[name])) for name in SCALE_NAMES
    }
    Hk_mean_dfa = {
        name: float(np.nanmean(per_unit_dfa_arr[name])) for name in SCALE_NAMES
    }
    n_finite_all4 = int(np.sum(
        np.isfinite(per_unit_arr["letter"]) & np.isfinite(per_unit_arr["word"])
        & np.isfinite(per_unit_arr["delta"]) & np.isfinite(per_unit_arr["verse"])
    ))
    fit_rs = _fit_scaling_law(Hk_mean)
    fit_dfa = _fit_scaling_law(Hk_mean_dfa)
    boot = _bootstrap_scaling(per_unit_arr, BOOTSTRAP_N, SEED)

    return {
        "n_units": len(units),
        "n_units_with_all4_finite": n_finite_all4,
        "H_mean_RS": {name: round(v, 6) if np.isfinite(v) else None
                      for name, v in Hk_mean.items()},
        "H_mean_DFA": {name: round(v, 6) if np.isfinite(v) else None
                       for name, v in Hk_mean_dfa.items()},
        "fit_RS": {k: (round(v, 6) if isinstance(v, float) else v)
                   for k, v in fit_rs.items() if k != "residuals"},
        "fit_RS_residuals": fit_rs.get("residuals", {}),
        "fit_DFA": {k: (round(v, 6) if isinstance(v, float) else v)
                    for k, v in fit_dfa.items() if k != "residuals"},
        "bootstrap_RS": boot,
        "per_unit_H_RS": {name: [float(v) if np.isfinite(v) else None
                                  for v in per_unit_arr[name].tolist()]
                          for name in SCALE_NAMES},
    }


# --- Physics-constant matching --------------------------------------------
def _match_constants(beta: float, tol: float = BETA_CONSTANT_TOL) -> list[dict]:
    if not np.isfinite(beta):
        return []
    hits = []
    for name, target in BETA_TARGETS.items():
        if abs(beta - target) <= tol:
            hits.append({
                "name": name,
                "target": round(target, 6),
                "observed": round(beta, 6),
                "abs_diff": round(abs(beta - target), 6),
                "within_tol": True,
                "tol": tol,
            })
    return hits


# --- Verdict dispatch ------------------------------------------------------
def _verdict(quran: dict, ctrl_results: dict) -> tuple[str, dict, list[dict]]:
    gates = {}
    # (a) data sufficiency
    n_q_ok = quran["n_units_with_all4_finite"]
    gates["sufficient_data"] = bool(n_q_ok >= 40)

    # (b) monotone ladder
    Hk = quran["H_mean_RS"]
    vals = [Hk[name] for name in SCALE_NAMES]
    # require H_letter < H_word < H_delta < H_verse (strictly decreasing in k→1, so increasing with name order letter<word<delta<verse)
    monotone = all(
        (vals[i + 1] is not None and vals[i] is not None
         and vals[i + 1] > vals[i] + MONOTONE_TOL)
        for i in range(len(vals) - 1)
    )
    gates["monotone_ladder"] = bool(monotone)

    # (c) scaling-law fit
    fit = quran["fit_RS"]
    r2 = fit.get("r2", float("nan"))
    beta = fit.get("beta", float("nan"))
    gates["r2_pass"] = bool(r2 is not None and r2 >= R2_GATE)
    gates["beta_negative"] = bool(np.isfinite(beta) and beta < -0.05)

    # (d) physics-constant matching
    constant_hits = _match_constants(beta)
    gates["constant_match"] = bool(len(constant_hits) > 0)

    # (e) Quran-specificity via bootstrap SE of Quran vs each ctrl
    boot_q = quran["bootstrap_RS"]
    quran_specific_details = []
    if boot_q is not None:
        q_beta = boot_q["beta"]["mean"]
        q_se = boot_q["beta"]["se"]
        differs_all = True
        for cname, cres in ctrl_results.items():
            boot_c = cres.get("bootstrap_RS")
            if boot_c is None:
                continue
            c_beta = boot_c["beta"]["mean"]
            c_se = boot_c["beta"]["se"]
            pooled_se = math.sqrt(q_se ** 2 + c_se ** 2) if (q_se > 0 or c_se > 0) else 0.0
            if pooled_se == 0:
                diff_se = float("inf")
            else:
                diff_se = abs(q_beta - c_beta) / pooled_se
            quran_specific_details.append({
                "ctrl": cname,
                "ctrl_beta": round(c_beta, 6),
                "pooled_SE": round(pooled_se, 6),
                "diff_SE": round(diff_se, 3),
            })
            if diff_se < QURAN_SPECIFIC_SE_K:
                differs_all = False
        gates["quran_specific"] = bool(differs_all and len(quran_specific_details) > 0)
    else:
        gates["quran_specific"] = None

    if not gates["sufficient_data"]:
        v = "FAIL_insufficient_data"
    elif not gates["monotone_ladder"]:
        v = "FAIL_not_monotone"
    elif not gates["r2_pass"]:
        if gates["monotone_ladder"]:
            v = "PARTIAL_monotone_no_scaling"
        else:
            v = "FAIL_low_r2"
    elif not gates["beta_negative"]:
        v = "PARTIAL_r2_ok_beta_nonneg"
    elif gates["constant_match"]:
        v = "PASS_scaling_law_plus_constant"
    else:
        v = "PASS_scaling_law"

    return v, gates, constant_hits


# --- Main ------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] H31 — Multi-Scale Hurst Ladder Scaling Law")
    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    q_units = _band_a(CORPORA.get("quran", []))
    print(f"[{EXP}] Band-A Quran: n={len(q_units)}")

    # --- Quran ladder ---
    t1 = time.time()
    quran_res = _per_corpus_ladder(q_units)
    print(f"[{EXP}] Quran ladder done in {time.time()-t1:.1f}s  "
          f"(n_all4_finite={quran_res['n_units_with_all4_finite']})")
    Hk = quran_res["H_mean_RS"]
    print(f"[{EXP}] H_mean_RS: letter={Hk['letter']}  word={Hk['word']}  "
          f"delta={Hk['delta']}  verse={Hk['verse']}")
    fit = quran_res["fit_RS"]
    print(f"[{EXP}] Fit:     alpha={fit['alpha']}  beta={fit['beta']}  "
          f"R²={fit['r2']}")
    if quran_res["bootstrap_RS"] is not None:
        bs = quran_res["bootstrap_RS"]
        print(f"[{EXP}] Boot95:  alpha ∈ [{bs['alpha']['ci_lo']:.4f}, "
              f"{bs['alpha']['ci_hi']:.4f}]  "
              f"beta ∈ [{bs['beta']['ci_lo']:.4f}, "
              f"{bs['beta']['ci_hi']:.4f}]  "
              f"R² ∈ [{bs['r2']['ci_lo']:.4f}, {bs['r2']['ci_hi']:.4f}]")

    # --- Ctrl corpora ladders ---
    ctrl_results: dict[str, dict] = {}
    for cname in ARABIC_CTRL:
        c_units = _band_a(CORPORA.get(cname, []))
        if not c_units:
            print(f"[{EXP}] ctrl {cname:18s}  empty")
            continue
        tc = time.time()
        res = _per_corpus_ladder(c_units)
        ctrl_results[cname] = res
        Hkc = res["H_mean_RS"]
        fitc = res["fit_RS"]
        print(f"[{EXP}] ctrl {cname:18s}  n={res['n_units']}  "
              f"letter={Hkc['letter']}  word={Hkc['word']}  "
              f"delta={Hkc['delta']}  verse={Hkc['verse']}  "
              f"| beta={fitc['beta']}  R²={fitc['r2']}  "
              f"(dt={time.time()-tc:.1f}s)")

    # --- Verdict ---
    verdict, gates, constant_hits = _verdict(quran_res, ctrl_results)
    elapsed = time.time() - t0

    print(f"\n{'=' * 64}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    for k, v in gates.items():
        mark = "OK" if v is True else ("--" if v is None else "FAIL")
        print(f"  {k:26s} {mark} ({v})")
    if constant_hits:
        print(f"  constant matches:")
        for h in constant_hits:
            print(f"    - {h['name']}: target={h['target']}  "
                  f"observed={h['observed']}  diff={h['abs_diff']}")
    print(f"{'=' * 64}")

    # --- Compact receipt ---
    def _strip_per_unit(corpus_res: dict) -> dict:
        out = dict(corpus_res)
        out.pop("per_unit_H_RS", None)  # keep receipt manageable
        return out

    report = {
        "experiment": EXP,
        "hypothesis": "H31 — Multi-Scale Hurst Ladder Scaling Law "
                      "(H(k) = alpha + beta*log2(k) across 4 scales)",
        "schema_version": 1,
        "prereg_document": "experiments/exp96_hurst_ladder/PREREG.md",
        "frozen_constants": {
            "seed": SEED, "band_a": [BAND_A_LO, BAND_A_HI],
            "n_min_rs": N_MIN_RS, "n_min_series": N_MIN_SERIES,
            "rs_window_log_steps": RS_WINDOW_LOG_STEPS,
            "bootstrap_n": BOOTSTRAP_N,
            "monotone_tol": MONOTONE_TOL,
            "r2_gate": R2_GATE,
            "beta_constant_tol": BETA_CONSTANT_TOL,
            "quran_specific_se_k": QURAN_SPECIFIC_SE_K,
        },
        "scale_k_mapping": SCALE_K,
        "beta_constant_targets": {k: round(v, 6) for k, v in BETA_TARGETS.items()},
        "quran": _strip_per_unit(quran_res),
        "ctrl_corpora": {c: _strip_per_unit(r) for c, r in ctrl_results.items()},
        "constant_hits": constant_hits,
        "prereg_gates": gates,
        "verdict": verdict,
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=float)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
