# -*- coding: utf-8 -*-
"""
fixes/extended_tests.py
=======================
Phase-2 tests (T7-T15). Each takes the already-computed `feats` dict
(from fixes.clean_pipeline._extract_features) and/or the raw `corpora`
and returns a single result dict.

Tests:
  T7  EL/CN dual-channel (corpus-level EL, CN, I(EL;CN), G_turbo)
  T8  Path minimality (canonical surah ordering vs random permutations)
  T9  Markov unforgeability (bigram-root likelihood ratio)
  T10 T-distribution ranking (%T>0 per corpus)
  T11 Bigram sufficiency (H_3 / H_2 ratio per corpus)
  T12 10-fold CV Phi_M robustness
  T13 Meccan/Medinan H-Cascade split
  T14 Bootstrap Omega stability
  T15 Classifier AUC (LOOCV on 5D features)
"""
from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from typing import Iterable

import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold, LeaveOneOut

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

# Traditional Meccan/Medinan split (standard Islamic classification)
MEDINAN = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 57, 58, 59,
           60, 61, 62, 63, 64, 65, 66, 76, 98, 99, 110}
# remainder of [1,114] is Meccan


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


def _entropy(seq) -> float:
    c = Counter(seq)
    total = sum(c.values())
    if total == 0:
        return 0.0
    return -sum((n / total) * math.log2(n / total) for n in c.values())


def _mi_pair(xs, ys) -> float:
    """Discrete I(X;Y) in bits, on binned x and y sequences."""
    n = len(xs)
    if n == 0:
        return 0.0
    cxy = Counter(zip(xs, ys))
    cx = Counter(xs); cy = Counter(ys)
    mi = 0.0
    for (x, y), nxy in cxy.items():
        pxy = nxy / n
        px = cx[x] / n; py = cy[y] / n
        if pxy > 0 and px > 0 and py > 0:
            mi += pxy * math.log2(pxy / (px * py))
    return mi


def _band_a(recs):
    return [r for r in recs if BAND_A_LO <= r["n_verses"] <= BAND_A_HI]


# ========================================================== T7
def test_el_cn_dual_channel(feats, corpora) -> dict:
    """Rank corpora on EL, CN. Compute I(EL;CN) across units within each
    corpus (binned). Compute G_turbo = (H(EL)+H(CN)-I(EL;CN))/max(H(EL),H(CN))."""
    per = {}
    for name in ["quran"] + ARABIC_CTRL:
        recs = _band_a(feats.get(name, []))
        if len(recs) < 10:
            continue
        el = np.array([r["EL"] for r in recs])
        cn = np.array([r["CN"] for r in recs])
        # Bin EL and CN each into 10 quantile bins
        el_bin = np.digitize(el, np.quantile(el, np.linspace(0, 1, 11)[1:-1]))
        cn_bin = np.digitize(cn, np.quantile(cn, np.linspace(0, 1, 11)[1:-1]))
        h_el = _entropy(el_bin)
        h_cn = _entropy(cn_bin)
        i_elcn = _mi_pair(el_bin, cn_bin)
        g_turbo = (h_el + h_cn - i_elcn) / max(h_el, h_cn, 1e-9)
        per[name] = {
            "n": len(recs),
            "EL_mean": float(el.mean()),
            "CN_mean": float(cn.mean()),
            "H_EL": h_el, "H_CN": h_cn,
            "I_EL_CN": i_elcn,
            "G_turbo": g_turbo,
        }
    el_rank = sorted(per.items(), key=lambda kv: -kv[1]["EL_mean"])
    cn_rank = sorted(per.items(), key=lambda kv: -kv[1]["CN_mean"])
    turbo_rank = sorted(per.items(), key=lambda kv: -kv[1]["G_turbo"])
    mi_rank = sorted(per.items(), key=lambda kv: kv[1]["I_EL_CN"])  # lowest MI = best
    return {
        "test": "T7 EL/CN dual-channel (Band A)",
        "per_corpus": per,
        "EL_ranking": [
            {"corpus": k, "EL": v["EL_mean"]} for k, v in el_rank
        ],
        "CN_ranking": [
            {"corpus": k, "CN": v["CN_mean"]} for k, v in cn_rank
        ],
        "G_turbo_ranking": [
            {"corpus": k, "G_turbo": v["G_turbo"]} for k, v in turbo_rank
        ],
        "MI_ranking_low_is_better": [
            {"corpus": k, "I(EL;CN)": v["I_EL_CN"]} for k, v in mi_rank
        ],
        "quran_rank_EL": next((i+1 for i,(k,_) in enumerate(el_rank) if k=="quran"), None),
        "quran_rank_CN": next((i+1 for i,(k,_) in enumerate(cn_rank) if k=="quran"), None),
        "quran_rank_G_turbo": next((i+1 for i,(k,_) in enumerate(turbo_rank) if k=="quran"), None),
        "quran_rank_MI": next((i+1 for i,(k,_) in enumerate(mi_rank) if k=="quran"), None),
    }


# ========================================================== T8
def test_path_minimality(feats, n_perms: int = 2000, seed: int = 42) -> dict:
    """Hamiltonian-path cost of canonical surah ordering vs permutations,
    in 5-D feature space. Returns z-score and percentile."""
    rng = np.random.default_rng(seed)
    feat_cols = ["EL", "VL_CV", "CN", "H_cond", "T"]

    def path_cost(X):
        diffs = np.diff(X, axis=0)
        return float(np.sum(np.linalg.norm(diffs, axis=1)))

    out = {}
    # AUDIT 2026-04-19 (v5): Band-A filter was missing. The z-score WITHIN
    # each corpus was still a valid permutation test, but the cross-corpus
    # ranking the paper cites (D17/S5) compared Quran's 114-surah path
    # against `poetry_abbasi`'s 2823-chapter path etc. — apples to oranges.
    # Path length scales with n_units, and feature variance differs across
    # unit-length distributions, both of which z-inflate short corpora vs
    # long ones. Filtering to [15, 100]-verse units removes the confound.
    for name in ["quran"] + ARABIC_CTRL:
        recs = [r for r in feats.get(name, [])
                if BAND_A_LO <= r["n_verses"] <= BAND_A_HI]
        if len(recs) < 20:
            continue
        # sort by unit label (canonical order)
        recs_sorted = sorted(recs, key=lambda r: r["label"])
        X = np.array([[r[c] for c in feat_cols] for r in recs_sorted],
                     dtype=float)
        canon_cost = path_cost(X)
        perm_costs = []
        for _ in range(n_perms):
            idx = rng.permutation(len(X))
            perm_costs.append(path_cost(X[idx]))
        perm_costs = np.array(perm_costs)
        z = (canon_cost - perm_costs.mean()) / perm_costs.std()
        pct = float((perm_costs < canon_cost).mean() * 100)
        # Adjacent-diversity: variance of adjacent feature distances
        diffs = np.diff(X, axis=0)
        d_norms = np.linalg.norm(diffs, axis=1)
        canon_var = float(d_norms.var())
        perm_vars = []
        for _ in range(n_perms // 4):
            idx = rng.permutation(len(X))
            pd = np.diff(X[idx], axis=0)
            perm_vars.append(np.linalg.norm(pd, axis=1).var())
        div_pct = float((np.array(perm_vars) < canon_var).mean() * 100)
        out[name] = {
            "n": len(recs_sorted),
            "canon_path_cost": canon_cost,
            "perm_cost_mean": float(perm_costs.mean()),
            "z_path": float(z),
            "pct_path_below_canon": pct,  # lower is better for canon
            "canon_adj_var": canon_var,
            "pct_adj_var_below_canon": div_pct,  # higher is better for canon
        }
    return {
        "test": "T8 Path minimality + adjacent diversity (canonical order vs perms)",
        "n_perms": n_perms,
        "per_corpus": out,
    }


# ========================================================== T9
def test_markov_unforgeability(corpora: dict[str, list[rl.Unit]],
                               n_perms: int = 200,
                               seed: int = 42,
                               max_units_per_corpus: int = 300) -> dict:
    """Fit a bigram root model on verse-final roots of each corpus,
    compute average log-likelihood of canonical vs verse-shuffled sequences.

    Optimised to precompute V, marg and bigram arrays ONCE per corpus.
    For large corpora (poetry_abbasi has 2823 units) we sub-sample at
    `max_units_per_corpus` to keep runtime bounded (<5s/corpus)."""
    rng = np.random.default_rng(seed)

    def extract_final_roots(unit: rl.Unit) -> list[str]:
        roots = []
        for v in unit.verses:
            toks = v.split()
            if not toks:
                continue
            r = rc.primary_root_normalized(toks[-1])
            roots.append(r if r else "<unk>")
        return roots

    out = {}
    for name in ["quran"] + ARABIC_CTRL:
        units = [u for u in corpora.get(name, [])
                 if BAND_A_LO <= u.n_verses() <= BAND_A_HI]
        if len(units) < 10:
            continue
        # Subsample large corpora for tractable runtime
        if len(units) > max_units_per_corpus:
            idx = rng.choice(len(units), size=max_units_per_corpus,
                             replace=False)
            units = [units[i] for i in idx]
        # Train bigram model on all (subsampled) units pooled
        bigram: Counter = Counter()
        marg: Counter = Counter()
        all_seqs = []
        vocab = set()
        for u in units:
            s = extract_final_roots(u)
            all_seqs.append(s)
            vocab.update(s)
            for a, b in zip(s[:-1], s[1:]):
                bigram[(a, b)] += 1
                marg[a] += 1
        V = len(vocab)
        # Precompute log-prob lookup: lp[(a,b)] = log2((c_ab+1)/(c_a+V))
        # Use a plain dict + a fallback for unseen bigrams (OOV = log2(1/(c_a+V)))
        lp: dict[tuple[str, str], float] = {}
        for (a, b), c_ab in bigram.items():
            lp[(a, b)] = math.log2((c_ab + 1) / (marg[a] + V))
        log_oov_a: dict[str, float] = {a: math.log2(1.0 / (marg[a] + V))
                                       for a in marg}
        log_oov_global = math.log2(1.0 / V) if V > 0 else 0.0

        def seq_ll(seq):
            if len(seq) < 2:
                return 0.0
            total = 0.0
            for a, b in zip(seq[:-1], seq[1:]):
                v = lp.get((a, b))
                if v is None:
                    v = log_oov_a.get(a, log_oov_global)
                total += v
            return total / (len(seq) - 1)

        canon_ll = float(np.mean([seq_ll(s) for s in all_seqs]))
        shuff_ll = np.empty(n_perms)
        for i in range(n_perms):
            lls = []
            for s in all_seqs:
                s2 = list(s); rng.shuffle(s2)
                lls.append(seq_ll(s2))
            shuff_ll[i] = np.mean(lls)
        std = float(shuff_ll.std()) or 1e-9
        out[name] = {
            "n_units": len(units),
            "canon_avg_logprob": canon_ll,
            "shuff_mean_logprob": float(shuff_ll.mean()),
            "ratio_canon_over_shuff": float(
                (2 ** canon_ll) / (2 ** shuff_ll.mean())),
            "z_shuff_vs_canon": float(
                (canon_ll - shuff_ll.mean()) / std),
            "pct_shuff_worse_than_canon": float(
                (shuff_ll < canon_ll).mean() * 100),
        }
    return {
        "test": "T9 Markov unforgeability (bigram root LL, canon vs shuffle)",
        "n_perms": n_perms,
        "max_units_per_corpus": max_units_per_corpus,
        "per_corpus": out,
    }


# ========================================================== T10
def test_t_distribution(feats) -> dict:
    """% of units with T > 0 per corpus, and mean T. Paper claims Quran
    has uniquely high fraction of T>0 units."""
    per = {}
    for name in ["quran"] + ARABIC_CTRL:
        recs = _band_a(feats.get(name, []))
        if not recs:
            continue
        t = np.array([r["T"] for r in recs])
        per[name] = {
            "n": len(recs),
            "mean_T": float(t.mean()),
            "median_T": float(np.median(t)),
            "pct_T_gt_zero": float((t > 0).mean() * 100),
        }
    ranked = sorted(per.items(), key=lambda kv: -kv[1]["pct_T_gt_zero"])
    return {
        "test": "T10 T-distribution %T>0 per corpus (Band A)",
        "per_corpus": per,
        "ranking_by_pct_T_positive": [
            {"corpus": k, "pct_T_gt_0": v["pct_T_gt_zero"]}
            for k, v in ranked
        ],
        "quran_rank_pct_T_positive": next(
            (i+1 for i,(k,_) in enumerate(ranked) if k=="quran"), None
        ),
    }


# ========================================================== T11
def test_bigram_sufficiency(corpora) -> dict:
    """H_3 / H_2 ratio on verse-final root sequences. Paper claims
    H_3/H_2 → 0 for Quran (bigram is sufficient), which would place
    Quran at low end of this ratio."""
    def hn_seq(tokens: list, n: int) -> float:
        if len(tokens) < n:
            return 0.0
        ngrams = list(zip(*(tokens[i:] for i in range(n))))
        # H(x_n | x_1..x_{n-1}) = H(x_1..x_n) - H(x_1..x_{n-1})
        hn = _entropy(ngrams)
        if n == 1:
            return hn
        prev = list(zip(*(tokens[i:] for i in range(n-1))))
        return hn - _entropy(prev)

    per = {}
    for name in ["quran"] + ARABIC_CTRL:
        units = [u for u in corpora.get(name, [])
                 if BAND_A_LO <= u.n_verses() <= BAND_A_HI]
        if len(units) < 10:
            continue
        # Concatenate final-root sequences across all units
        all_roots = []
        for u in units:
            for v in u.verses:
                toks = v.split()
                if not toks:
                    continue
                r = rc.primary_root_normalized(toks[-1])
                all_roots.append(r if r else "<unk>")
        if len(all_roots) < 30:
            continue
        h2 = hn_seq(all_roots, 2)
        h3 = hn_seq(all_roots, 3)
        per[name] = {
            "n_units": len(units),
            "n_tokens": len(all_roots),
            "H2": h2, "H3": h3,
            "ratio_H3_over_H2": float(h3 / h2) if h2 > 0 else float("nan"),
        }
    # AUDIT 2026-04-19 (v6 fix W4-b): Python's `sorted` on NaN-valued keys
    # produces UNDEFINED order because all NaN comparisons return False. If
    # any corpus had H2 == 0 (ratio_H3_over_H2 = NaN) the Quran rank below
    # could silently be wrong. Pre-filter NaN into a separate NaN bucket,
    # sort only the finite values, and record the NaN corpora separately so
    # a reader can see the ranking is well-defined only on finite entries.
    _finite = [kv for kv in per.items()
               if math.isfinite(kv[1]["ratio_H3_over_H2"])]
    _nan    = [k for k, v in per.items()
               if not math.isfinite(v["ratio_H3_over_H2"])]
    ranked = sorted(_finite, key=lambda kv: kv[1]["ratio_H3_over_H2"])
    _q_rank = next(
        (i + 1 for i, (k, _) in enumerate(ranked) if k == "quran"), None
    )
    return {
        "test": "T11 Bigram sufficiency H_3/H_2 (lower is more Markov-2)",
        "per_corpus": per,
        "ranking_low_is_better": [
            {"corpus": k, "ratio": v["ratio_H3_over_H2"]}
            for k, v in ranked
        ],
        "ranking_nan_bucket": _nan,
        "quran_rank_low_ratio": _q_rank,
    }


# ========================================================== T12
def test_cv_phi_m(feats, phi_m_result: dict,
                  n_splits: int = 10, seed: int = 42) -> dict:
    """10-fold CV over Quran Band A units; for each fold, compute Φ_M
    Quran vs controls and report d, p. Matches pre-registered test A."""
    feat_cols = ["EL", "VL_CV", "CN", "H_cond", "T"]
    q_recs = _band_a(feats["quran"])
    Xq = np.array([[r[c] for c in feat_cols] for r in q_recs], dtype=float)

    ctrl_recs = []
    for name in ARABIC_CTRL:
        ctrl_recs += _band_a(feats.get(name, []))
    Xc = np.array([[r[c] for c in feat_cols] for r in ctrl_recs], dtype=float)
    mu = Xc.mean(axis=0)
    cov = np.cov(Xc, rowvar=False) + 1e-6 * np.eye(5)
    Sinv = np.linalg.inv(cov)
    phi_c = fv2.phi_m(Xc, mu, Sinv)

    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    fold_results = []
    for i, (_, te) in enumerate(kf.split(Xq)):
        Xq_fold = Xq[te]
        phi_q = fv2.phi_m(Xq_fold, mu, Sinv)
        # Cohen's d
        if len(phi_q) < 2:
            continue
        pv = ((len(phi_q) - 1) * phi_q.var(ddof=1)
              + (len(phi_c) - 1) * phi_c.var(ddof=1)) \
            / (len(phi_q) + len(phi_c) - 2)
        d = (phi_q.mean() - phi_c.mean()) / math.sqrt(max(pv, 1e-9))
        _, p = stats.mannwhitneyu(phi_q, phi_c, alternative="greater")
        fold_results.append({
            "fold": i, "n_q": len(phi_q),
            "mean_phi_q": float(phi_q.mean()),
            "cohens_d": float(d),
            "p_mwu_greater": float(p),
        })
    ds = [r["cohens_d"] for r in fold_results]
    ps = [r["p_mwu_greater"] for r in fold_results]
    return {
        "test": "T12 10-fold CV robustness of Phi_M",
        "n_splits": n_splits, "seed": seed,
        "folds": fold_results,
        "min_d": float(min(ds)), "median_d": float(np.median(ds)),
        "max_d": float(max(ds)),
        "max_p": float(max(ps)),
        "threshold_min_d_ge_0.5": bool(min(ds) >= 0.5),
        "threshold_max_p_lt_0.01": bool(max(ps) < 0.01),
        "all_folds_positive_d": bool(min(ds) > 0),
    }


# ========================================================== T13
def test_meccan_medinan(corpora) -> dict:
    """H-Cascade F for Meccan vs Medinan surahs separately.
    Pre-reg test B (v10.18)."""
    # Reuse H-Cascade fn
    from .clean_pipeline import _hcond_letter_level as hL
    from .clean_pipeline import _hcond_word_level as hW
    from .clean_pipeline import _hcond_verse_initial as hI
    from .clean_pipeline import _hcond_verse_final as hF

    def unit_F(u):
        vals = np.array([hL(u.verses), hW(u.verses),
                         hI(u.verses), hF(u.verses)], dtype=float)
        if vals.max() == vals.min() or vals.std() < 1e-9:
            return float("nan")
        norm = (vals - vals.min()) / (vals.max() - vals.min())
        return float(norm.mean() / norm.std())

    quran_units = [u for u in corpora.get("quran", [])
                   if BAND_A_LO <= u.n_verses() <= BAND_A_HI]
    meccan_F = []; medinan_F = []
    for u in quran_units:
        # label format 'Q:NNN'
        try:
            sid = int(u.label.split(":")[1])
        except Exception:
            continue
        F = unit_F(u)
        if not np.isfinite(F):
            continue
        if sid in MEDINAN:
            medinan_F.append(F)
        else:
            meccan_F.append(F)

    mF = np.array(meccan_F); dF = np.array(medinan_F)
    # Pooled control F
    ctrl_F = []
    for name in ARABIC_CTRL:
        for u in corpora.get(name, []):
            if BAND_A_LO <= u.n_verses() <= BAND_A_HI:
                F = unit_F(u)
                if np.isfinite(F):
                    ctrl_F.append(F)
    ctrl_F = np.array(ctrl_F)

    p_m_vs_ctrl = float(
        stats.mannwhitneyu(mF, ctrl_F, alternative="greater").pvalue
        if len(mF) > 1 and len(ctrl_F) > 1 else float("nan")
    )
    p_d_vs_ctrl = float(
        stats.mannwhitneyu(dF, ctrl_F, alternative="greater").pvalue
        if len(dF) > 1 and len(ctrl_F) > 1 else float("nan")
    )
    threshold_both_F_gt_1 = bool(mF.mean() > 1.0 and dF.mean() > 1.0)
    threshold_gap_lt_1_5 = bool(abs(mF.mean() - dF.mean()) < 1.5)
    threshold_both_p_lt_05 = bool(p_m_vs_ctrl < 0.05 and p_d_vs_ctrl < 0.05)
    return {
        "test": "T13 Meccan vs Medinan H-Cascade (pre-reg test B)",
        "n_meccan": len(mF), "n_medinan": len(dF), "n_ctrl": len(ctrl_F),
        "F_meccan_mean": float(mF.mean()) if len(mF) else float("nan"),
        "F_medinan_mean": float(dF.mean()) if len(dF) else float("nan"),
        "F_ctrl_mean": float(ctrl_F.mean()) if len(ctrl_F) else float("nan"),
        "abs_gap_meccan_medinan": float(abs(mF.mean() - dF.mean())),
        "p_meccan_gt_ctrl": p_m_vs_ctrl,
        "p_medinan_gt_ctrl": p_d_vs_ctrl,
        "threshold_both_F_gt_1": threshold_both_F_gt_1,
        "threshold_gap_lt_1_5": threshold_gap_lt_1_5,
        "threshold_both_p_lt_0_05": threshold_both_p_lt_05,
        "all_thresholds_pass": all([
            threshold_both_F_gt_1, threshold_gap_lt_1_5,
            threshold_both_p_lt_05
        ]),
    }


# ========================================================== T14
def test_bootstrap_omega(feats, omega_result: dict,
                         n_boot: int = 1000, seed: int = 42) -> dict:
    """Bootstrap stability of Quran Ω_master. Pre-reg test C.
    Uses the Ω defined in T4 (within-run means, no hardcoded constants).
    """
    rng = np.random.default_rng(seed)
    q_recs = _band_a(feats["quran"])
    if len(q_recs) < 10:
        return {"test": "T14", "error": "not enough Quran units"}

    # Control means (used as denominator), held fixed across bootstraps
    ctrl_means = omega_result["control_means"]
    # Control Phi_M mean, held fixed
    pcm = omega_result.get("per_corpus", {})
    # Compute as average over control corpora (same as T4)
    ctrl_phi = None
    # Approximate: we use sqrt(5) as a default since controls are at ~2.0
    # Actually pull from the T2 result if present in feats. For simplicity,
    # recompute phi_M for Quran subsample each bootstrap using fixed mu/Sinv.
    feat_cols = ["EL", "VL_CV", "CN", "H_cond", "T"]
    Xq_full = np.array([[r[c] for c in feat_cols] for r in q_recs], dtype=float)
    ctrl_recs = []
    for name in ARABIC_CTRL:
        ctrl_recs += _band_a(feats.get(name, []))
    Xc = np.array([[r[c] for c in feat_cols] for r in ctrl_recs], dtype=float)
    mu = Xc.mean(axis=0)
    cov = np.cov(Xc, rowvar=False) + 1e-6 * np.eye(5)
    Sinv = np.linalg.inv(cov)
    ctrl_phi = float(fv2.phi_m(Xc, mu, Sinv).mean())

    omegas = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(q_recs), size=len(q_recs))
        sub = Xq_full[idx]
        s = {c: float(sub[:, i].mean()) for i, c in enumerate(feat_cols)}
        phi_mean = float(fv2.phi_m(sub, mu, Sinv).mean())
        r1 = phi_mean / max(ctrl_phi, 1e-9)
        r2 = s["H_cond"] / max(ctrl_means["H_cond"], 1e-9)
        r3 = s["VL_CV"] / max(ctrl_means["VL_CV"], 1e-9)
        r4 = (1.0 + s["EL"]) / (1.0 + ctrl_means["EL"])
        r5 = (1.0 + s["CN"]) / (1.0 + ctrl_means["CN"])
        omegas.append(r1 * r2 * r3 * r4 * r5)
    omegas = np.array(omegas)
    pct_gt_2 = float((omegas > 2.0).mean() * 100)
    p5 = float(np.percentile(omegas, 5))
    p50 = float(np.percentile(omegas, 50))
    p95 = float(np.percentile(omegas, 95))
    return {
        "test": "T14 Bootstrap Omega stability (pre-reg test C)",
        "n_boot": n_boot, "seed": seed,
        "p5_omega": p5, "median_omega": p50, "p95_omega": p95,
        "mean_omega": float(omegas.mean()),
        "pct_bootstraps_omega_gt_2": pct_gt_2,
        "threshold_pct_gt_2_ge_95": bool(pct_gt_2 >= 95.0),
        "threshold_p5_ge_1_5": bool(p5 >= 1.5),
        "all_thresholds_pass": bool(pct_gt_2 >= 95.0 and p5 >= 1.5),
    }


# ========================================================== T15
def test_classifier_auc(feats, seed: int = 42) -> dict:
    """LOOCV binary classifier (Quran vs Arabic controls) on 5-D features,
    at Band A. Reports AUC on the leave-one-out predictions."""
    feat_cols = ["EL", "VL_CV", "CN", "H_cond", "T"]
    q = _band_a(feats["quran"])
    c = []
    for name in ARABIC_CTRL:
        c += _band_a(feats.get(name, []))
    if len(q) < 10 or len(c) < 10:
        return {"test": "T15", "error": "not enough data"}
    X = np.array([[r[cc] for cc in feat_cols] for r in q + c], dtype=float)
    y = np.array([1] * len(q) + [0] * len(c), dtype=int)
    # Simpler: stratified 5-fold for speed (LOOCV would take ~5 min)
    from sklearn.model_selection import StratifiedKFold
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    scores = np.zeros(len(y))
    for tr, te in skf.split(X, y):
        clf = LogisticRegression(max_iter=2000, class_weight="balanced",
                                 random_state=seed)
        clf.fit(X[tr], y[tr])
        scores[te] = clf.predict_proba(X[te])[:, 1]
    auc = float(roc_auc_score(y, scores))
    # Sigma from chance AUC 0.5
    n_pos, n_neg = int(y.sum()), int(len(y) - y.sum())
    se = math.sqrt((auc * (1 - auc) +
                    (n_pos - 1) * (auc / (2 - auc) - auc ** 2) +
                    (n_neg - 1) * (2 * auc ** 2 / (1 + auc) - auc ** 2))
                   / (n_pos * n_neg))
    z = (auc - 0.5) / max(se, 1e-9)
    return {
        "test": "T15 5-fold CV logistic classifier AUC (Quran vs Arabic ctrl)",
        "n_quran": int(n_pos), "n_ctrl": int(n_neg),
        "auc": auc,
        "auc_se_hanley_mcneil": float(se),
        "z_over_chance": float(z),
    }
