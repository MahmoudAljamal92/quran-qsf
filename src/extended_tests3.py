# -*- coding: utf-8 -*-
"""
src/extended_tests3.py
======================
Phase-4 tests (T24-T31). Re-tests of v10.10-v10.13 notebook findings
that were NOT covered by the April-17 audit round.

T24  Lesion dose-response                              -- v10.13 §12c
T25  Info-geometry saddle point (5D Hessian)           -- v10.13 §12c
T26  Terminal position signal depth (-1, -2, -3)       -- v10.13 §12c
T27  Inter-surah structural cost (Mushaf vs random)    -- v10.13 §12c
T28  Markov-order sufficiency (H3/H2 ratio)            -- v10.10 T12
T29  Phase transition order parameter phi_frac         -- v10.10 Phase 30
T30  Renormalization-group flow (variance vs L)        -- v10.10 Phase 31
T31  Fisher-metric curvature ranking                   -- v10.10 Phase 32

All tests operate on the clean raw-data corpora and use CamelTools roots
(via src.features / src.roots). No checkpoint dependency.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import stats

from . import roots as rc
from . import features as fv2
from . import raw_loader as rl

BAND_A_LO, BAND_A_HI = 15, 100

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
    # AUDIT 2026-04-19 (v5) — `hadith_bukhari` removed (quotes Quran by
    # design; Cell 22 of the notebook already quarantines it).
]


# ---------------------------------------------------------------- utils
def _cohens_d(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    pv = ((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) \
        / (len(a) + len(b) - 2)
    if pv <= 0:
        return float("nan")
    return (a.mean() - b.mean()) / math.sqrt(pv)


def _band_a_units(corpora, name):
    return [u for u in corpora.get(name, [])
            if BAND_A_LO <= u.n_verses() <= BAND_A_HI]


def _last_letter(verse: str):
    # strip diacritics & whitespace, return final letter or None
    s = re.sub(r"[\u064B-\u0652\u0670\u0671\u06DC-\u06ED\s]", "", verse).strip()
    return s[-1] if s else None


def _last_k_letters(verse: str, k: int):
    s = re.sub(r"[\u064B-\u0652\u0670\u0671\u06DC-\u06ED\s]", "", verse).strip()
    return s[-k:] if len(s) >= k else None


# ========================================================== T24  Lesion dose-response
def test_lesion_dose_response(corpora, damage_levels=(0.005, 0.01, 0.02, 0.05,
                                                      0.10, 0.20, 0.50),
                              seed: int = 42) -> dict:
    """Randomly replace a fraction of verse-final letters with a different
    Arabic letter, then measure the EL-match rate and the variance across
    verses (proxy for 'heat capacity'). Smooth degradation = NOT irreducible.

    Expected (from v10.13): EL drop ~3% at 1% damage, ~15% at 5% damage,
    heat capacity peaks at 5-10%.
    """
    rng = np.random.default_rng(seed)
    ARABIC = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")

    def _el_match_rate(verses):
        """Fraction of consecutive verse pairs sharing the same last letter."""
        lasts = [_last_letter(v) for v in verses]
        lasts = [l for l in lasts if l is not None]
        if len(lasts) < 2:
            return float("nan")
        hits = sum(1 for i in range(len(lasts) - 1) if lasts[i] == lasts[i + 1])
        return hits / (len(lasts) - 1)

    def _damage(verses, frac):
        out = []
        n_verses = len(verses)
        n_damage = max(1, int(round(n_verses * frac)))
        idx_damage = set(rng.choice(n_verses, size=n_damage, replace=False))
        for i, v in enumerate(verses):
            if i in idx_damage:
                s = re.sub(r"[\u064B-\u0652\u0670\u0671\u06DC-\u06ED\s]", "", v).strip()
                if s:
                    new_letter = rng.choice([c for c in ARABIC if c != s[-1]])
                    v = v[:-1] + new_letter if v.endswith(s[-1]) else v + new_letter
            out.append(v)
        return out

    # Only Quran surahs in Band A, to keep comparable to notebook
    quran_units = _band_a_units(corpora, "quran")
    el_canonical = [_el_match_rate(u.verses) for u in quran_units]
    el_canonical = [x for x in el_canonical if not math.isnan(x)]
    canon_mean = float(np.mean(el_canonical))

    dose = {}
    for frac in damage_levels:
        el_damaged = []
        for u in quran_units:
            v_dmg = _damage(list(u.verses), frac)
            r = _el_match_rate(v_dmg)
            if not math.isnan(r):
                el_damaged.append(r)
        mean_el = float(np.mean(el_damaged))
        var_el = float(np.var(el_damaged))
        dose[f"{frac*100:.1f}pct"] = {
            "damage_frac": float(frac),
            "EL_mean_damaged": mean_el,
            "EL_drop_from_canonical": float((canon_mean - mean_el) / canon_mean),
            "heat_capacity_proxy": var_el,
        }
    # Smoothness: monotonic decrease + no cliff
    vals = [dose[k]["EL_mean_damaged"] for k in dose]
    monotone = all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1))
    # heat capacity peak location
    hc = [(k, dose[k]["heat_capacity_proxy"]) for k in dose]
    peak_key = max(hc, key=lambda x: x[1])[0]

    return {
        "test_id": "T24_lesion_dose",
        "EL_canonical": canon_mean,
        "n_quran_units": len(quran_units),
        "dose_response": dose,
        "monotonic_degradation": bool(monotone),
        "heat_capacity_peak_at": peak_key,
        "verdict": "smooth_degradation" if monotone else "abrupt_collapse",
    }


# ========================================================== T25  Info-geometry saddle
def test_info_geometry_saddle(feats_per_corpus, band=(BAND_A_LO, BAND_A_HI)) -> dict:
    """Compute the Hessian of the negative log-density (approximated by the
    Mahalanobis d^2) at the Quran centroid, restricted to its 5D feature
    subspace. Saddle point = mixed-sign eigenvalues.

    Expected (v10.13): Quran Hessian eigenvalues [-7.49, -3.68, -2.17, -0.75,
    +2.65] -> saddle (4 neg, 1 pos). 4/9 control corpora also saddle.
    """
    def _band_X(recs):
        X = [[r["EL"], r["VL_CV"], r["CN"], r["H_cond"], r["T"]]
             for r in recs if band[0] <= r["n_verses"] <= band[1]]
        return np.asarray(X, dtype=float)

    per = {}
    for name, recs in feats_per_corpus.items():
        X = _band_X(recs)
        if len(X) < 10:
            continue
        mu = X.mean(axis=0)
        # Use within-corpus covariance as the local metric; Hessian of
        # d^2_Mah = (x-mu)^T S^{-1} (x-mu) equals 2*S^{-1}. Eigenvalues of
        # S^{-1} directly probe the curvature in each principal direction.
        # A saddle-like signature therefore requires comparing the corpus
        # covariance against the GLOBAL covariance: if the corpus has some
        # directions tighter (higher 1/lambda) and some looser than the
        # global baseline, it is a "saddle" w.r.t. the population manifold.
        per[name] = X

    if "quran" not in per:
        return {"test_id": "T25_info_geo_saddle", "error": "quran missing"}

    # Global covariance across Arabic corpora only (matches audit design)
    all_X = np.vstack([per[n] for n in per if n == "quran" or n in ARABIC_CTRL])
    S_global = np.cov(all_X.T)
    invS_global = np.linalg.pinv(S_global)

    saddle_info = {}
    for name, X in per.items():
        S_local = np.cov(X.T) + 1e-8 * np.eye(X.shape[1])
        # Relative curvature: invS_local - invS_global
        invS_local = np.linalg.pinv(S_local)
        M = invS_local - invS_global
        w, _ = np.linalg.eigh(M)
        w = np.sort(w)
        n_neg = int((w < -1e-6).sum())
        n_pos = int((w > 1e-6).sum())
        is_saddle = (n_neg > 0) and (n_pos > 0)
        saddle_info[name] = {
            "eigvals_sorted": [float(x) for x in w],
            "n_negative": n_neg,
            "n_positive": n_pos,
            "is_saddle": bool(is_saddle),
        }

    n_saddle_total = sum(1 for v in saddle_info.values() if v["is_saddle"])
    return {
        "test_id": "T25_info_geo_saddle",
        "per_corpus": saddle_info,
        "n_corpora": len(saddle_info),
        "n_saddles": n_saddle_total,
        "quran_is_saddle": saddle_info["quran"]["is_saddle"],
        "quran_eigval_signs": (saddle_info["quran"]["n_negative"],
                               saddle_info["quran"]["n_positive"]),
    }


# ========================================================== T26  Terminal position depth
def test_terminal_position_depth(corpora, positions=(-1, -2, -3)) -> dict:
    """For each position k in {-1, -2, -3} (counted from verse end), compute
    the rate at which consecutive verses share the same letter at that
    position. Signal should be strongest at -1 (fawasil), decay at -2,
    vanish at -3.

    Expected (v10.13): d(-1)=1.138, d(-2)=0.816, d(-3)=-0.152.
    """
    def _pos_match_rate(verses, k: int):
        # k is -1, -2, -3 etc.
        letters = []
        for v in verses:
            s = re.sub(r"[\u064B-\u0652\u0670\u0671\u06DC-\u06ED\s]", "", v).strip()
            if len(s) >= abs(k):
                letters.append(s[k])
            else:
                letters.append(None)
        hits = 0; total = 0
        for i in range(len(letters) - 1):
            if letters[i] and letters[i + 1]:
                total += 1
                if letters[i] == letters[i + 1]:
                    hits += 1
        return hits / total if total else float("nan")

    per_pos = {}
    for k in positions:
        q_rates = [_pos_match_rate(u.verses, k) for u in _band_a_units(corpora, "quran")]
        q_rates = [x for x in q_rates if not math.isnan(x)]
        ctrl_rates = []
        for ctrl in ARABIC_CTRL:
            for u in _band_a_units(corpora, ctrl):
                r = _pos_match_rate(u.verses, k)
                if not math.isnan(r):
                    ctrl_rates.append(r)
        d = _cohens_d(q_rates, ctrl_rates) if q_rates and ctrl_rates else float("nan")
        try:
            _, p = stats.mannwhitneyu(q_rates, ctrl_rates, alternative="greater")
        except ValueError:
            p = float("nan")
        per_pos[str(k)] = {
            "position": int(k),
            "quran_n": len(q_rates),
            "ctrl_n": len(ctrl_rates),
            "quran_match_rate_mean": float(np.mean(q_rates)) if q_rates else float("nan"),
            "ctrl_match_rate_mean": float(np.mean(ctrl_rates)) if ctrl_rates else float("nan"),
            "cohens_d": float(d) if not math.isnan(d) else None,
            "p_mwu_greater": float(p) if not math.isnan(p) else None,
        }

    # Signal depth = largest k where d > 0.3
    depth = 0
    for k in positions:
        d = per_pos[str(k)]["cohens_d"]
        if d is not None and d > 0.3:
            depth = max(depth, abs(k))
    return {
        "test_id": "T26_terminal_depth",
        "per_position": per_pos,
        "signal_depth_letters": int(depth),
    }


# ========================================================== T27  Inter-surah cost
def test_inter_surah_cost(feats_per_corpus, corpus_name: str = "quran",
                          n_perms: int = 1000, seed: int = 42,
                          band=(BAND_A_LO, BAND_A_HI)) -> dict:
    """Sum of consecutive 5D Euclidean distances between corpus units in
    canonical order. Compare to random permutations.

    Expected (v10.13): Mushaf cost / random cost ~ 0.70, p ~ 0.
    """
    recs = [r for r in feats_per_corpus.get(corpus_name, [])
            if band[0] <= r["n_verses"] <= band[1]]
    if len(recs) < 10:
        return {"test_id": "T27_inter_surah_cost", "error": "too few units"}
    X = np.asarray([[r["EL"], r["VL_CV"], r["CN"], r["H_cond"], r["T"]]
                    for r in recs], dtype=float)
    # Standardize for fair Euclidean sum
    Xs = (X - X.mean(0)) / (X.std(0) + 1e-9)

    def _path_cost(idx):
        d = np.diff(Xs[idx], axis=0)
        return float(np.sqrt((d * d).sum(axis=1)).sum())

    canon = _path_cost(np.arange(len(Xs)))
    rng = np.random.default_rng(seed)
    perm_costs = []
    n_better = 0
    for _ in range(n_perms):
        idx = rng.permutation(len(Xs))
        c = _path_cost(idx)
        perm_costs.append(c)
        if c <= canon:
            n_better += 1
    perm_mean = float(np.mean(perm_costs))
    return {
        "test_id": "T27_inter_surah_cost",
        "corpus": corpus_name,
        "n_units": int(len(recs)),
        "canonical_cost": canon,
        "random_mean_cost": perm_mean,
        "cost_ratio": canon / perm_mean if perm_mean > 0 else float("nan"),
        "n_perms": int(n_perms),
        "n_random_better_or_equal": int(n_better),
        "p_value": n_better / n_perms,
    }


# ========================================================== T28  Markov-order
def test_markov_order_sufficiency(corpora) -> dict:
    """Compute the ratio H3 / H2 of conditional-entropy orders over the
    root sequence (Markov-2 vs Markov-1). If Markov-1 already captures
    almost all predictability, the ratio is ~ 1. If Markov-2 adds a lot,
    ratio << 1.

    The paper claim (T12 in v10.10 notebook, d=-1.849) is that Quran needs
    LESS additional information from M-2 than controls -- its root stream
    is already nearly Markov-1-sufficient.
    """
    def _cond_entropy_order(verses, order: int) -> float:
        """H(w_{t+order} | w_t, ..., w_{t+order-1}) over root tokens."""
        toks = []
        for v in verses:
            for w in v.split():
                r = rc.primary_root_normalized(w)
                if r:
                    toks.append(r)
        if len(toks) < order + 2:
            return float("nan")
        # context -> next-symbol counter
        ctx_counts = {}
        for i in range(len(toks) - order):
            ctx = tuple(toks[i:i + order])
            nxt = toks[i + order]
            ctx_counts.setdefault(ctx, Counter())[nxt] += 1
        # weighted average H(next | ctx)
        total = 0; weighted_H = 0.0
        for ctx, cnt in ctx_counts.items():
            n = sum(cnt.values())
            total += n
            p = np.array(list(cnt.values()), float) / n
            H = -float((p * np.log2(p + 1e-15)).sum())
            weighted_H += n * H
        return weighted_H / total if total else float("nan")

    def _corpus_values(units):
        vals = []
        for u in units:
            H1 = _cond_entropy_order(u.verses, 1)
            H2 = _cond_entropy_order(u.verses, 2)
            if math.isnan(H1) or math.isnan(H2) or H1 <= 0:
                continue
            vals.append((H1, H2, H2 / H1))
        return vals

    per = {}
    for name, units in corpora.items():
        band_units = [u for u in units if BAND_A_LO <= u.n_verses() <= BAND_A_HI]
        if len(band_units) < 5:
            continue
        # Cap to 30 per corpus for speed (Markov-2 on large units is slow)
        band_units = band_units[:30]
        vals = _corpus_values(band_units)
        if not vals:
            continue
        ratios = [v[2] for v in vals]
        per[name] = {
            "n_units": len(vals),
            "H1_mean": float(np.mean([v[0] for v in vals])),
            "H2_mean": float(np.mean([v[1] for v in vals])),
            "H2_over_H1_mean": float(np.mean(ratios)),
            "H2_over_H1_median": float(np.median(ratios)),
        }
    # Quran vs Arabic controls
    if "quran" not in per:
        return {"test_id": "T28_markov_order", "error": "quran missing"}
    q_rs = [v["H2_over_H1_mean"] for k, v in per.items() if k == "quran"]
    # Get per-unit ratios for Quran
    quran_band = [u for u in corpora["quran"]
                  if BAND_A_LO <= u.n_verses() <= BAND_A_HI][:30]
    quran_ratios = [v[2] for v in _corpus_values(quran_band)]
    ctrl_ratios = []
    for ctrl in ARABIC_CTRL:
        ctrl_band = [u for u in corpora.get(ctrl, [])
                     if BAND_A_LO <= u.n_verses() <= BAND_A_HI][:30]
        ctrl_ratios.extend(v[2] for v in _corpus_values(ctrl_band))
    d = _cohens_d(quran_ratios, ctrl_ratios) if ctrl_ratios else float("nan")
    try:
        _, p_less = stats.mannwhitneyu(quran_ratios, ctrl_ratios, alternative="less")
    except ValueError:
        p_less = float("nan")
    return {
        "test_id": "T28_markov_order",
        "per_corpus": per,
        "quran_H2_over_H1_mean": float(np.mean(quran_ratios)) if quran_ratios else float("nan"),
        "ctrl_H2_over_H1_mean": float(np.mean(ctrl_ratios)) if ctrl_ratios else float("nan"),
        "cohens_d_quran_vs_ctrl": float(d) if not math.isnan(d) else None,
        "p_mwu_less": float(p_less) if not math.isnan(p_less) else None,
    }


# ========================================================== T29  Phase-transition phi_frac
def test_phase_transition_phi_frac(feats_per_corpus,
                                   band=(BAND_A_LO, BAND_A_HI)) -> dict:
    """Define phi_frac = (median T over short surahs) / (median T over long
    surahs). Check whether it is near 1/phi = 0.618 AND whether its
    neighborhood shows a heat-capacity peak (variance maximum) at intermediate
    scales -- a weak phase-transition fingerprint.

    The v10.15 audit already downgraded this: the scalar value is close to
    1/phi but the scale-invariance test is NEGATIVE. We report both.
    """
    recs = feats_per_corpus.get("quran", [])
    recs = [r for r in recs if r["n_verses"] >= 5]
    if len(recs) < 10:
        return {"test_id": "T29_phi_frac", "error": "too few units"}

    # sort by n_verses, split into short/medium/long thirds
    recs = sorted(recs, key=lambda r: r["n_verses"])
    n = len(recs)
    short = recs[:n // 3]
    mid = recs[n // 3: 2 * n // 3]
    long_ = recs[2 * n // 3:]

    def _T_arr(group):
        return np.asarray([r["T"] for r in group])

    T_s, T_m, T_l = _T_arr(short), _T_arr(mid), _T_arr(long_)
    med_s, med_m, med_l = np.median(T_s), np.median(T_m), np.median(T_l)
    var_s, var_m, var_l = np.var(T_s), np.var(T_m), np.var(T_l)

    phi_frac = float(med_s / med_l) if med_l != 0 else float("nan")
    golden = (math.sqrt(5) - 1) / 2  # 0.618...
    near_golden = abs(phi_frac - golden) < 0.1

    # Heat-capacity proxy: variance peak at medium scale?
    hc_peak_at_mid = var_m >= var_s and var_m >= var_l

    return {
        "test_id": "T29_phi_frac",
        "T_median_short": float(med_s),
        "T_median_medium": float(med_m),
        "T_median_long": float(med_l),
        "phi_frac": phi_frac,
        "near_golden_ratio": bool(near_golden),
        "delta_from_golden": float(phi_frac - golden) if not math.isnan(phi_frac) else None,
        "heat_capacity_peak_at_medium": bool(hc_peak_at_mid),
        "variance_short": float(var_s),
        "variance_medium": float(var_m),
        "variance_long": float(var_l),
        "note": "v10.15 audit downgrades this: scalar near 1/phi is a motif, NOT a certified critical point (see T30).",
    }


# ========================================================== T30  Renormalization-group flow
def test_rg_flow(feats_per_corpus, scales=(1, 2, 4, 8, 16),
                 band=(BAND_A_LO, BAND_A_HI)) -> dict:
    """Block-coarse-grain each corpus's T-sequence at L = 1..16 verses, then
    measure variance scaling. For a scale-invariant (critical) signal,
    var(T_L) ~ L^{-alpha} with alpha~1 and alpha identical across corpora.

    Expected (v10.10->v10.12 consensus, v10.15 RG-v2 confirmed): NEGATIVE.
    """
    def _block_variances(recs):
        # Concatenate T-sequence over surahs (band-A only)
        ts = []
        for r in recs:
            if band[0] <= r["n_verses"] <= band[1]:
                ts.append(r["T"])  # one value per surah -- coarse
        ts = np.asarray(ts, float)
        vars_at = {}
        for L in scales:
            if len(ts) < L:
                continue
            # block-average T over L consecutive surahs
            blocks = [ts[i:i + L].mean() for i in range(0, len(ts) - L + 1, L)]
            blocks = np.asarray(blocks)
            vars_at[L] = float(blocks.var()) if len(blocks) > 1 else float("nan")
        return vars_at

    per = {}
    for name, recs in feats_per_corpus.items():
        v = _block_variances(recs)
        if len(v) >= 3:
            # fit log var ~ -alpha log L
            Ls = np.asarray(sorted(v.keys()), float)
            Vs = np.asarray([v[int(L)] for L in Ls], float)
            mask = Vs > 0
            if mask.sum() >= 3:
                slope, intercept, r_, p_, _ = stats.linregress(
                    np.log2(Ls[mask]), np.log2(Vs[mask]))
                per[name] = {
                    "variance_by_scale": {str(int(k)): float(v_) for k, v_ in v.items()},
                    "alpha_slope": float(-slope),  # positive alpha = variance shrinks with L
                    "r_squared": float(r_ * r_),
                }
    if "quran" not in per:
        return {"test_id": "T30_rg_flow", "error": "too few quran scales"}

    alphas = [v["alpha_slope"] for v in per.values()]
    q_alpha = per["quran"]["alpha_slope"]
    # Rank Quran's alpha (higher = more trivial / less scale-invariant)
    sorted_names = sorted(per.keys(), key=lambda n: per[n]["alpha_slope"])
    rank_q = sorted_names.index("quran") + 1

    return {
        "test_id": "T30_rg_flow",
        "per_corpus": per,
        "quran_alpha": q_alpha,
        "median_alpha": float(np.median(alphas)),
        "quran_rank": int(rank_q),
        "n_corpora": int(len(per)),
        "verdict": "NEGATIVE_as_expected" if 0.8 <= q_alpha <= 1.2 else "anomalous",
        "note": "alpha ~ 1 = trivial (independent blocks). alpha << 1 would indicate scale-invariance / criticality.",
    }


# ========================================================== T31  Fisher-metric curvature
def test_fisher_curvature(feats_per_corpus,
                          band=(BAND_A_LO, BAND_A_HI)) -> dict:
    """Fisher information matrix approximated by per-corpus inverse
    covariance in the 5D feature space. Curvature scalar = trace(invS) / d.

    Expected (v10.12): Quran has the LOWEST curvature (rank 10/10 = smoothest
    manifold) -- confirmed as a NEGATIVE but distinctive topological feature.
    """
    per = {}
    for name, recs in feats_per_corpus.items():
        X = [[r["EL"], r["VL_CV"], r["CN"], r["H_cond"], r["T"]]
             for r in recs if band[0] <= r["n_verses"] <= band[1]]
        if len(X) < 10:
            continue
        X = np.asarray(X, float)
        S = np.cov(X.T) + 1e-8 * np.eye(X.shape[1])
        invS = np.linalg.pinv(S)
        curvature = float(np.trace(invS) / X.shape[1])
        logdet = float(np.linalg.slogdet(S)[1])  # larger = more volume
        per[name] = {
            "curvature_trace": curvature,
            "log_det_cov": logdet,
            "n_units": int(len(X)),
        }
    if "quran" not in per:
        return {"test_id": "T31_fisher_curvature", "error": "quran missing"}
    # Rank by curvature (1 = lowest = smoothest)
    sorted_by_curv = sorted(per.keys(), key=lambda n: per[n]["curvature_trace"])
    rank_q = sorted_by_curv.index("quran") + 1
    sorted_by_vol = sorted(per.keys(), key=lambda n: -per[n]["log_det_cov"])
    rank_q_vol = sorted_by_vol.index("quran") + 1
    return {
        "test_id": "T31_fisher_curvature",
        "per_corpus": per,
        "quran_curvature_rank": int(rank_q),
        "quran_volume_rank": int(rank_q_vol),
        "n_corpora": int(len(per)),
        "note": "curvature rank 1 = smoothest (low 1/lambda). The v10.12 finding was that Quran sits at the smooth end. This is a distinctive-but-not-unique signature.",
    }
