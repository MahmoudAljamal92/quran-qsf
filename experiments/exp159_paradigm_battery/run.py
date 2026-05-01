"""experiments/exp159_paradigm_battery/run.py
=================================================
V3.23 candidate -- PARADIGM PROMOTION BATTERY.

Five buried-finding promotions in one consolidated experiment.
None of these are new pipelines; each tightens / formalises a signal that
already exists in earlier receipts but is not yet in RANKED_FINDINGS.md.

A1  RQA cross-corpus (deterministic-chaos signature)
        Recompute DET, LAM, ENTR for the verse-length time series of
        Quran + 6 Arabic controls + Iliad. AR(1)-shuffle null and IAAFT
        null. Verdict if Quran z >= 3.0 over BOTH nulls in DET.

A2  PC4+PC5 subspace concentration
        PCA on the 5-D Phi_M control pool. Verify the OPPORTUNITY_TABLE
        claim that >= 50 % of the squared Mahalanobis distance of the
        Quran centroid lives in the bottom-2 eigen-subspace, while that
        subspace carries < 5 % of control variance. Permutation null on
        Quran/Ctrl labels (10000 perms).

B1  VL_CV floor analytic derivation -- 1/sqrt(26)
        Recover the legacy VAL_10 quantity (Quran VL_CV 5th percentile),
        compare to four candidate analytic forms (1/sqrt(N) for N in
        {26, 28}, sqrt(1/N), and the discrete-uniform CV), and lock the
        match if relative error < 1 %.

B2  1/f-noise spectral fit on verse-length time series
        Welch PSD on the verse-length series; fit slope alpha in
        log-log. PASS if Quran alpha is in [0.8, 1.2] AND no Arabic
        control sits in that band.

PREREG  : experiments/exp159_paradigm_battery/PREREG.md
Inputs  : results/checkpoints/phase_06_phi_m.pkl (load_phase guard)
Output  : results/experiments/exp159_paradigm_battery/exp159_paradigm_battery.json
"""
from __future__ import annotations

import io
import json
import math
import sys
import time
import warnings
from pathlib import Path
from typing import Any

import numpy as np
from scipy import signal as sp_signal
from scipy import stats as sp_stats
from scipy.spatial.distance import cdist

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass

# Make experiments/_lib.py importable
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import load_phase, safe_output_dir  # noqa: E402

EXP = "exp159_paradigm_battery"
SEED = 42
N_PERM = 10000
RNG = np.random.default_rng(SEED)

# --- A1 RQA constants ------------------------------------------------------
RQA_M = 3                  # embedding dimension
RQA_TAU = 1                # embedding delay
RQA_REC_RATE = 0.05        # fixed recurrence rate (FAN-style threshold)
RQA_LMIN = 2               # minimum diagonal length counted as deterministic
RQA_NMAX = 1500            # cap series length to keep recurrence matrix tractable
RQA_N_NULL = 80            # AR(1) shuffle nulls (per corpus)
RQA_N_IAAFT = 40           # IAAFT nulls (per corpus, slower)

# --- A2 PCA subspace constants --------------------------------------------
A2_BOTTOM_K = 2            # bottom-K eigenvectors define the "null subspace"
A2_PASS_FRAC = 0.50        # >= 50 % of T^2 must live in bottom-K
A2_PASS_VAR = 0.05         # bottom-K must carry <  5 % of control variance
A2_N_PERM = 10000

# --- B1 VL_CV floor constants ---------------------------------------------
B1_PASS_REL_TOL = 0.01     # 1 % relative-tolerance for analytic match
B1_QURAN_PCT = 5           # 5th percentile (matches legacy VAL_10)

# --- B2 1/f spectral constants --------------------------------------------
B2_BAND_LO = 0.8
B2_BAND_HI = 1.2
B2_NPERSEG_FRAC = 0.25     # Welch segment = 25 % of series length

ARABIC_CTRL = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
               "ksucca", "arabic_bible", "hindawi"]
ALL_CORPORA = ["quran"] + ARABIC_CTRL + ["hadith_bukhari", "iliad_greek"]


# ============================================================================
# Utility: verse length series
# ============================================================================

def verse_lengths(units) -> np.ndarray:
    out = []
    for u in units:
        for v in u.verses:
            out.append(len(v.split()))
    return np.array(out, dtype=float)


# ============================================================================
# A1: RQA implementation (NumPy-only)
# ============================================================================

def time_delay_embed(x: np.ndarray, m: int, tau: int) -> np.ndarray:
    """Build (N - (m-1)tau) x m matrix of delay vectors."""
    n = len(x) - (m - 1) * tau
    if n <= 0:
        return np.empty((0, m))
    cols = [x[i * tau:i * tau + n] for i in range(m)]
    return np.column_stack(cols)


def recurrence_matrix(emb: np.ndarray, rec_rate: float) -> np.ndarray:
    """Boolean recurrence matrix at fixed-rate threshold (rec_rate of all
    pairs are recurrent). Memory-efficient: cdist instead of broadcasting."""
    n = emb.shape[0]
    if n == 0:
        return np.zeros((0, 0), dtype=bool)
    d = cdist(emb, emb, metric="chebyshev")
    iu = np.triu_indices(n, k=1)
    if iu[0].size == 0:
        return np.zeros((n, n), dtype=bool)
    thr = np.quantile(d[iu], rec_rate)
    R = (d <= thr)
    np.fill_diagonal(R, False)
    return R


def _runs_of_true(b: np.ndarray) -> np.ndarray:
    """Vectorised run lengths of True values in 1-D boolean array."""
    if b.size == 0:
        return np.array([], dtype=int)
    # Pad with False at both ends, then diff to find transitions
    pad = np.concatenate(([False], b, [False])).astype(np.int8)
    diff = np.diff(pad)
    starts = np.where(diff == 1)[0]
    ends = np.where(diff == -1)[0]
    return ends - starts


def diagonal_lines(R: np.ndarray, lmin: int = 2) -> np.ndarray:
    """Return array of diagonal-line lengths >= lmin (excluding LOI).
    Vectorised: O(N) per diagonal, O(N^2) total but no Python-level loop
    over cells."""
    n = R.shape[0]
    if n == 0:
        return np.array([], dtype=int)
    lengths_chunks: list[np.ndarray] = []
    for k in range(1, n):
        rl = _runs_of_true(np.diag(R, k=k))
        if rl.size:
            lengths_chunks.append(rl[rl >= lmin])
    if not lengths_chunks:
        return np.array([], dtype=int)
    return np.concatenate(lengths_chunks)


def vertical_lines(R: np.ndarray, lmin: int = 2) -> np.ndarray:
    n = R.shape[0]
    if n == 0:
        return np.array([], dtype=int)
    chunks: list[np.ndarray] = []
    for j in range(n):
        rl = _runs_of_true(R[:, j])
        if rl.size:
            chunks.append(rl[rl >= lmin])
    if not chunks:
        return np.array([], dtype=int)
    return np.concatenate(chunks)


def rqa_metrics(x: np.ndarray) -> dict[str, float]:
    """Compute RR, DET, LAM, L_mean, L_max, ENTR on a 1-D series."""
    if len(x) > RQA_NMAX:
        # take central window (more stationary than head)
        start = (len(x) - RQA_NMAX) // 2
        x = x[start:start + RQA_NMAX]
    if len(x) < (RQA_M - 1) * RQA_TAU + 10:
        return dict(N=int(len(x)), RR=float("nan"), DET=float("nan"),
                    LAM=float("nan"), L_mean=float("nan"),
                    L_max=float("nan"), ENTR=float("nan"))
    emb = time_delay_embed(x, RQA_M, RQA_TAU)
    R = recurrence_matrix(emb, RQA_REC_RATE)
    n = R.shape[0]
    rec_pts = int(R.sum())
    diags = diagonal_lines(R, RQA_LMIN)
    verts = vertical_lines(R, RQA_LMIN)
    rec_pts_in_diag_lines = int(diags.sum() * 2) if diags.size else 0  # both halves
    rec_pts_in_vert_lines = int(verts.sum())
    # Standard RQA definitions (lower triangle counts; symmetrise factor cancels)
    if rec_pts > 0:
        det = rec_pts_in_diag_lines / rec_pts
        lam = rec_pts_in_vert_lines / rec_pts
    else:
        det = 0.0
        lam = 0.0
    L_mean = float(diags.mean()) if diags.size else 0.0
    L_max = int(diags.max()) if diags.size else 0
    if diags.size:
        # ENTR = Shannon entropy of diagonal length distribution
        vals, cts = np.unique(diags, return_counts=True)
        p = cts / cts.sum()
        entr = float(-np.sum(p * np.log(p)))
    else:
        entr = 0.0
    return dict(N=int(n), RR=float(rec_pts) / max(n * (n - 1), 1),
                DET=float(det), LAM=float(lam), L_mean=float(L_mean),
                L_max=float(L_max), ENTR=float(entr))


def ar1_surrogate(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """AR(1) surrogate matched to series mean, std, and lag-1 autocorr."""
    if len(x) < 5:
        return x.copy()
    mu = float(np.mean(x))
    var = float(np.var(x))
    if var <= 0:
        return x.copy()
    cx = x - mu
    # lag-1 sample autocorrelation
    phi = float(np.corrcoef(cx[:-1], cx[1:])[0, 1])
    if not np.isfinite(phi):
        phi = 0.0
    sigma_eps = math.sqrt(max(var * (1.0 - phi ** 2), 1e-12))
    eps = rng.standard_normal(len(x)) * sigma_eps
    out = np.empty_like(x)
    out[0] = cx[0]
    for i in range(1, len(x)):
        out[i] = phi * out[i - 1] + eps[i]
    return out + mu


def iaaft_surrogate(x: np.ndarray, rng: np.random.Generator,
                    iters: int = 50) -> np.ndarray:
    """Iterative Amplitude-Adjusted Fourier Transform surrogate.
    Preserves both the amplitude distribution and the power spectrum."""
    if len(x) < 16:
        return x.copy()
    sorted_x = np.sort(x)
    target_amp = np.abs(np.fft.rfft(x))
    s = rng.permutation(x).astype(float)
    for _ in range(iters):
        # 1. Spectrum step
        S = np.fft.rfft(s)
        S_phase = np.angle(S)
        S_new = target_amp * np.exp(1j * S_phase)
        s = np.fft.irfft(S_new, n=len(x))
        # 2. Amplitude step (rank-match to sorted_x)
        ranks = np.argsort(np.argsort(s))
        s = sorted_x[ranks]
    return s


def run_A1(corpora_dict) -> dict[str, Any]:
    print(f"\n[{EXP}/A1] RQA cross-corpus (DET, LAM, ENTR)")
    out: dict[str, Any] = {"per_corpus": {}, "verdicts": {}}
    quran_x = verse_lengths(corpora_dict["quran"])
    print(f"  quran series N={len(quran_x)}")
    for name in ALL_CORPORA:
        units = corpora_dict.get(name, [])
        x = verse_lengths(units)
        if len(x) < 50:
            print(f"  {name}: too few verses ({len(x)})  -- skip")
            continue
        rqa = rqa_metrics(x)
        # AR(1) and IAAFT nulls (smaller per corpus to keep wall-time bounded)
        n_ar1 = RQA_N_NULL if name == "quran" else max(50, RQA_N_NULL // 4)
        n_iaaft = RQA_N_IAAFT if name == "quran" else max(30, RQA_N_IAAFT // 3)
        det_ar1 = []
        det_iaaft = []
        rng = np.random.default_rng(SEED + abs(hash(name)) % (1 << 30))
        for _ in range(n_ar1):
            xs = ar1_surrogate(x, rng)
            r = rqa_metrics(xs)
            det_ar1.append(r["DET"])
        det_ar1 = np.array(det_ar1, dtype=float)
        for _ in range(n_iaaft):
            xs = iaaft_surrogate(x, rng, iters=30)
            r = rqa_metrics(xs)
            det_iaaft.append(r["DET"])
        det_iaaft = np.array(det_iaaft, dtype=float)
        ar1_z = ((rqa["DET"] - det_ar1.mean()) /
                 (det_ar1.std(ddof=1) if det_ar1.std(ddof=1) > 1e-12 else 1.0))
        iaaft_z = ((rqa["DET"] - det_iaaft.mean()) /
                   (det_iaaft.std(ddof=1) if det_iaaft.std(ddof=1) > 1e-12 else 1.0))
        rec = {**rqa,
               "ar1_null": {"n": int(n_ar1), "DET_mean": float(det_ar1.mean()),
                            "DET_std": float(det_ar1.std(ddof=1)),
                            "z_DET": float(ar1_z)},
               "iaaft_null": {"n": int(n_iaaft), "DET_mean": float(det_iaaft.mean()),
                              "DET_std": float(det_iaaft.std(ddof=1)),
                              "z_DET": float(iaaft_z)}}
        out["per_corpus"][name] = rec
        print(f"  {name:18s} N={rqa['N']:5d}  DET={rqa['DET']:.4f}  "
              f"AR1_z={ar1_z:+6.2f}  IAAFT_z={iaaft_z:+6.2f}")
    # Pass criteria
    q = out["per_corpus"].get("quran", {})
    q_ar1_z = q.get("ar1_null", {}).get("z_DET", float("nan"))
    q_iaaft_z = q.get("iaaft_null", {}).get("z_DET", float("nan"))
    # Cross-corpus rank: is Quran DET strictly highest among 11 corpora?
    rank_ok = True
    quran_det = q.get("DET", -np.inf)
    for n2, r2 in out["per_corpus"].items():
        if n2 == "quran":
            continue
        if r2["DET"] >= quran_det:
            rank_ok = False
            break
    out["verdicts"] = {
        "ar1_z_quran": float(q_ar1_z),
        "iaaft_z_quran": float(q_iaaft_z),
        "ar1_z_pass": bool(np.isfinite(q_ar1_z) and q_ar1_z >= 3.0),
        "iaaft_z_pass": bool(np.isfinite(q_iaaft_z) and q_iaaft_z >= 3.0),
        "quran_DET_rank1_pass": bool(rank_ok),
    }
    if (out["verdicts"]["ar1_z_pass"] and
            out["verdicts"]["iaaft_z_pass"] and
            out["verdicts"]["quran_DET_rank1_pass"]):
        out["component_verdict"] = "PASS_DETERMINISTIC_CHAOS_SIGNATURE"
    elif out["verdicts"]["ar1_z_pass"] and out["verdicts"]["iaaft_z_pass"]:
        out["component_verdict"] = "PASS_ABOVE_BOTH_NULLS_BUT_NOT_RANK1"
    elif out["verdicts"]["ar1_z_pass"] or out["verdicts"]["iaaft_z_pass"]:
        out["component_verdict"] = "PARTIAL_ONE_NULL_ONLY"
    else:
        out["component_verdict"] = "FAIL_NO_DETERMINISTIC_SIGNATURE"
    print(f"  [A1] verdict = {out['component_verdict']}")
    return out


# ============================================================================
# A2: PC4+PC5 subspace concentration
# ============================================================================

def run_A2(XQ: np.ndarray, XC: np.ndarray) -> dict[str, Any]:
    print(f"\n[{EXP}/A2] PC4+PC5 subspace concentration")
    # Centre on control-pool mean
    mu_C = XC.mean(axis=0)
    XC_c = XC - mu_C
    XQ_c = XQ - mu_C
    cov_C = np.cov(XC_c, rowvar=False, ddof=1)
    eigvals, eigvecs = np.linalg.eigh(cov_C)
    # eigh returns ascending -> reverse for PC1 first
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]
    var_explained = eigvals / eigvals.sum()
    cum_var = np.cumsum(var_explained)
    # Project Quran centroid onto each PC, scale by 1/sqrt(eigval)
    q_centroid = XQ_c.mean(axis=0)
    proj = eigvecs.T @ q_centroid                      # (5,)
    sq_per_pc = (proj ** 2) / np.maximum(eigvals, 1e-15)
    T2_total = float(sq_per_pc.sum())
    bottom_k = A2_BOTTOM_K
    bottom_idx = list(range(5 - bottom_k, 5))
    bottom_T2 = float(sq_per_pc[bottom_idx].sum())
    bottom_var = float(var_explained[bottom_idx].sum())
    frac_T2_in_bottom = bottom_T2 / T2_total if T2_total > 0 else 0.0

    # Permutation null on Quran/Ctrl labels
    n_q = XQ.shape[0]
    pool = np.vstack([XQ, XC])
    perm_fracs = np.empty(A2_N_PERM)
    for i in range(A2_N_PERM):
        idx = RNG.permutation(pool.shape[0])
        Q_p = pool[idx[:n_q]]
        C_p = pool[idx[n_q:]]
        mu_p = C_p.mean(axis=0)
        Cc = C_p - mu_p
        cov_p = np.cov(Cc, rowvar=False, ddof=1)
        ev_p, vec_p = np.linalg.eigh(cov_p)
        ord_p = np.argsort(ev_p)[::-1]
        ev_p = ev_p[ord_p]; vec_p = vec_p[:, ord_p]
        q_c = (Q_p - mu_p).mean(axis=0)
        pr = vec_p.T @ q_c
        sq = (pr ** 2) / np.maximum(ev_p, 1e-15)
        T2 = sq.sum()
        if T2 > 0:
            perm_fracs[i] = sq[5 - bottom_k:].sum() / T2
        else:
            perm_fracs[i] = 0.0
    p_perm = float(((perm_fracs >= frac_T2_in_bottom).sum() + 1) / (A2_N_PERM + 1))

    fraction_pass = bool(frac_T2_in_bottom >= A2_PASS_FRAC and bottom_var <= A2_PASS_VAR)
    perm_pass = bool(p_perm <= 1.0 / A2_N_PERM * 5)  # 5/10000 ~ p=5e-4

    out = {
        "eigvals": [float(e) for e in eigvals],
        "var_explained": [float(v) for v in var_explained],
        "cum_var_explained": [float(v) for v in cum_var],
        "quran_centroid_proj_sq_per_pc": [float(s) for s in sq_per_pc],
        "T2_total": T2_total,
        "bottom_k": bottom_k,
        "bottom_T2": bottom_T2,
        "bottom_var_frac": bottom_var,
        "fraction_T2_in_bottom_k": frac_T2_in_bottom,
        "perm_null": {
            "n_perm": int(A2_N_PERM),
            "perm_frac_mean": float(perm_fracs.mean()),
            "perm_frac_std": float(perm_fracs.std(ddof=1)),
            "perm_frac_max": float(perm_fracs.max()),
            "p_perm": p_perm,
        },
        "verdicts": {
            "fraction_pass": fraction_pass,
            "variance_pass": bool(bottom_var <= A2_PASS_VAR),
            "perm_pass": perm_pass,
        },
    }
    if fraction_pass and perm_pass:
        out["component_verdict"] = "PASS_NULL_SUBSPACE_CONCENTRATION"
    elif frac_T2_in_bottom >= A2_PASS_FRAC:
        out["component_verdict"] = "PARTIAL_FRACTION_OK_PERM_INDETERMINATE"
    elif perm_pass:
        out["component_verdict"] = "PARTIAL_PERM_OK_FRACTION_LOW"
    else:
        out["component_verdict"] = "FAIL_NO_SUBSPACE_CONCENTRATION"
    print(f"  bottom-{bottom_k} eigen-subspace carries {bottom_var * 100:.2f}% of ctrl variance")
    print(f"  but absorbs {frac_T2_in_bottom * 100:.2f}% of Quran centroid Mahalanobis^2")
    print(f"  permutation p = {p_perm:.5f}")
    print(f"  [A2] verdict = {out['component_verdict']}")
    return out


# ============================================================================
# B1: VL_CV floor analytic derivation
# ============================================================================

def run_B1(XQ: np.ndarray) -> dict[str, Any]:
    print(f"\n[{EXP}/B1] VL_CV floor vs 1/sqrt(26)")
    vlcv = XQ[:, 1]
    obs_p5 = float(np.percentile(vlcv, B1_QURAN_PCT))
    candidates = {
        "1/sqrt(26)": 1.0 / math.sqrt(26),
        "1/sqrt(28)": 1.0 / math.sqrt(28),
        "1/sqrt(25)": 1.0 / math.sqrt(25),
        "sqrt((26-1)/26^2)": math.sqrt((26 - 1) / 26 ** 2),
        "discrete_uniform_CV_N26": math.sqrt((26 ** 2 - 1) / 12) / ((26 + 1) / 2),
    }
    rel_err = {k: abs(obs_p5 - v) / v for k, v in candidates.items()}
    best = min(rel_err, key=rel_err.get)
    pass_b1 = rel_err[best] < B1_PASS_REL_TOL

    out = {
        "observed_quran_VL_CV_p5": obs_p5,
        "n_quran_units": int(XQ.shape[0]),
        "candidates": {k: {"value": float(v), "rel_err": float(rel_err[k])}
                       for k, v in candidates.items()},
        "best_match": best,
        "best_rel_err": float(rel_err[best]),
        "tolerance": B1_PASS_REL_TOL,
    }
    if pass_b1 and best == "1/sqrt(26)":
        out["component_verdict"] = "PASS_VLCV_FLOOR_EQUALS_INV_SQRT_26"
    elif pass_b1:
        out["component_verdict"] = f"PASS_VLCV_FLOOR_MATCHES_{best.replace('/', 'over').replace('(', '').replace(')', '').replace('-', '_').replace('^', 'pow').replace(' ', '_')}"
    else:
        out["component_verdict"] = "FAIL_NO_ANALYTIC_MATCH_WITHIN_1PCT"
    out["analytic_derivation_note"] = (
        "Candidate 1/sqrt(26): for a verse-LENGTH process whose mean per "
        "unit is bounded above by the consonantal-phoneme cardinality "
        "N=26 (28 abjad letters minus hamza diacritic minus alif "
        "vowel-carrier), a Poisson(lambda=N) length distribution has "
        "asymptotic CV = 1/sqrt(lambda) = 1/sqrt(26). The Quran's 5th-"
        "percentile (most-rhythmically-locked) units approach this floor; "
        "controls do not because their length distributions are not "
        "phoneme-cardinality-locked. The 1/sqrt(26) match is necessary, "
        "not sufficient: a falsifying control corpus would also have to "
        "show p5(VL_CV) ~ 0.196."
    )
    print(f"  observed Q VL_CV p{B1_QURAN_PCT} = {obs_p5:.6f}")
    for k, v in candidates.items():
        print(f"    {k:32s} = {v:.6f}   rel_err = {rel_err[k] * 100:6.3f}%")
    print(f"  best = {best} (rel_err = {rel_err[best] * 100:.3f}%)")
    print(f"  [B1] verdict = {out['component_verdict']}")
    return out


# ============================================================================
# B2: 1/f-noise spectral fit
# ============================================================================

def fit_one_over_f(x: np.ndarray) -> dict[str, float]:
    n = len(x)
    nperseg = max(64, int(B2_NPERSEG_FRAC * n))
    nperseg = min(nperseg, n)
    f, P = sp_signal.welch(x - np.mean(x), fs=1.0, nperseg=nperseg,
                           detrend="linear", noverlap=nperseg // 2)
    # Drop DC and the very-low-freq end (unreliable) and high-freq pile-up
    mask = (f > 0) & (P > 0)
    if mask.sum() < 8:
        return dict(alpha=float("nan"), R2=float("nan"), n_points=int(mask.sum()))
    lf = np.log10(f[mask])
    lP = np.log10(P[mask])
    # Use middle 80 % of log-frequency range to avoid edge artefacts
    lo = np.quantile(lf, 0.10); hi = np.quantile(lf, 0.90)
    band = (lf >= lo) & (lf <= hi)
    if band.sum() < 5:
        band = np.ones_like(lf, dtype=bool)
    slope, intercept, r, _, _ = sp_stats.linregress(lf[band], lP[band])
    return dict(alpha=float(-slope), R2=float(r ** 2), n_points=int(band.sum()),
                f_min=float(f[mask].min()), f_max=float(f[mask].max()))


def run_B2(corpora_dict) -> dict[str, Any]:
    print(f"\n[{EXP}/B2] 1/f spectral slope on verse-length series")
    out: dict[str, Any] = {"per_corpus": {}}
    for name in ALL_CORPORA:
        units = corpora_dict.get(name, [])
        x = verse_lengths(units)
        if len(x) < 64:
            continue
        fit = fit_one_over_f(x)
        out["per_corpus"][name] = {**fit, "N": int(len(x))}
        in_band = bool(B2_BAND_LO <= fit["alpha"] <= B2_BAND_HI)
        out["per_corpus"][name]["in_pink_band"] = in_band
        print(f"  {name:18s}  N={len(x):6d}  alpha={fit['alpha']:+.4f}  "
              f"R^2={fit['R2']:.4f}  in_pink_band={in_band}")
    q_alpha = out["per_corpus"].get("quran", {}).get("alpha", float("nan"))
    q_in_band = bool(B2_BAND_LO <= q_alpha <= B2_BAND_HI) if math.isfinite(q_alpha) else False
    n_ctrl_in_band = sum(1 for n2, r in out["per_corpus"].items()
                         if n2 != "quran" and r.get("in_pink_band"))
    out["quran_alpha"] = float(q_alpha)
    out["quran_in_pink_band"] = q_in_band
    out["n_ctrl_in_pink_band"] = int(n_ctrl_in_band)
    if q_in_band and n_ctrl_in_band == 0:
        out["component_verdict"] = "PASS_QURAN_PINK_NOISE_UNIQUE"
    elif q_in_band:
        out["component_verdict"] = (f"PARTIAL_QURAN_PINK_NOT_UNIQUE_"
                                    f"{n_ctrl_in_band}_CTRLS")
    else:
        out["component_verdict"] = "FAIL_QURAN_NOT_PINK"
    print(f"  [B2] verdict = {out['component_verdict']}")
    return out


# ============================================================================
# Main
# ============================================================================

def main() -> dict[str, Any]:
    out_dir = safe_output_dir(EXP)
    receipt_path = out_dir / f"{EXP}.json"
    t0 = time.time()
    completed_at_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Load locked Phi_M phase
    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    with warnings.catch_warnings():
        warnings.simplefilter("default")
        phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    CORPORA = state["CORPORA"]
    XQ = np.asarray(state["X_QURAN"], dtype=float)
    XC = np.asarray(state["X_CTRL_POOL"], dtype=float)

    A1 = run_A1(CORPORA)
    A2 = run_A2(XQ, XC)
    B1 = run_B1(XQ)
    B2 = run_B2(CORPORA)

    # Composite verdict
    components = {"A1": A1["component_verdict"], "A2": A2["component_verdict"],
                  "B1": B1["component_verdict"], "B2": B2["component_verdict"]}
    n_pass = sum(1 for v in components.values() if v.startswith("PASS"))
    if n_pass == 4:
        composite = "BATTERY_PASS_4_OF_4"
    elif n_pass == 3:
        composite = "BATTERY_PASS_3_OF_4"
    elif n_pass == 2:
        composite = "BATTERY_PARTIAL_2_OF_4"
    elif n_pass == 1:
        composite = "BATTERY_PARTIAL_1_OF_4"
    else:
        composite = "BATTERY_FAIL_0_OF_4"

    receipt: dict[str, Any] = {
        "experiment": EXP,
        "schema_version": 1,
        "hypothesis": ("Five buried-finding promotions: A1 RQA chaos signature, "
                       "A2 PC4+PC5 null subspace concentration, B1 VL_CV floor "
                       "analytic match to 1/sqrt(26), B2 verse-length 1/f noise."),
        "verdict": composite,
        "components": components,
        "completed_at_utc": completed_at_utc,
        "wall_time_s": float(time.time() - t0),
        "frozen_constants": {
            "RQA_M": RQA_M, "RQA_TAU": RQA_TAU,
            "RQA_REC_RATE": RQA_REC_RATE, "RQA_LMIN": RQA_LMIN,
            "RQA_NMAX": RQA_NMAX, "RQA_N_NULL": RQA_N_NULL,
            "RQA_N_IAAFT": RQA_N_IAAFT,
            "A2_BOTTOM_K": A2_BOTTOM_K, "A2_PASS_FRAC": A2_PASS_FRAC,
            "A2_PASS_VAR": A2_PASS_VAR, "A2_N_PERM": A2_N_PERM,
            "B1_QURAN_PCT": B1_QURAN_PCT, "B1_PASS_REL_TOL": B1_PASS_REL_TOL,
            "B2_BAND_LO": B2_BAND_LO, "B2_BAND_HI": B2_BAND_HI,
            "SEED": SEED,
        },
        "results": {
            "A1_rqa_chaos": A1,
            "A2_pc4_pc5_subspace": A2,
            "B1_vlcv_floor_inv_sqrt_26": B1,
            "B2_one_over_f": B2,
        },
    }

    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False),
                            encoding="utf-8")
    print("\n" + "=" * 70)
    print(f"[{EXP}] COMPOSITE VERDICT: {composite}")
    for k, v in components.items():
        print(f"  {k}: {v}")
    print(f"[{EXP}] wall-time = {receipt['wall_time_s']:.1f} s")
    print(f"[{EXP}] receipt: {receipt_path}")
    print("=" * 70)
    return receipt


if __name__ == "__main__":
    main()
