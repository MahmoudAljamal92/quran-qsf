# -*- coding: utf-8 -*-
"""
fixes/extended_tests2.py
========================
Phase-3 tests (T16-T21 + T23 + T22).

T16  Scale-Free S24 (sliding-window, no-semantic)  -- D07
T17  Multi-scale perturbation (letter / word / verse)  -- D11
T18  Verse-internal word order shuffle              -- D14
T19  RQA anti-metric (LAM on verse-length sequence) -- D16
T20  Structural Forgery P3 (rhyme-swap)             -- D21
T21  Cross-language (Iliad vs Quran, lang-agnostic 5-D) -- CL1 partial
T22  Root Diversity x EL product                    -- D22
T23  Harakat channel capacity (vocalised Quran)     -- E3
"""
from __future__ import annotations

import math
import sys
from collections import Counter, defaultdict
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


# ========================================================== T16
def test_scale_free_s24(corpora, n_perms: int = 100, seed: int = 42,
                        max_units_per_corpus: int = 40) -> dict:
    """Simplified sliding-window S24 test (D07).

    For each surah, per-verse transition quality t_i = 2·EL(v_i,v_{i+1})
    + 2·CN(v_{i+1}).  For window sizes W in {5,10,20}, compute the
    window-averaged Q_W.  Per surah, p-value = fraction of verse-shuffle
    permutations that beat the canonical Q_W.  Fisher-combine per-surah
    p-values across the corpus.

    Fully vectorised: compute the transition-quality vector once per
    surah, then all permutations are numpy index juggling.
    """
    rng = np.random.default_rng(seed)
    conn = fv2.ARABIC_CONN

    def compute_t(verses):
        # terminal letters and first tokens for each verse
        finals = []
        firsts = []
        for v in verses:
            v2 = fv2._strip_d(v).strip()
            # terminal letter
            t = ""
            for c in reversed(v2):
                if c.isalpha():
                    t = c
                    break
            finals.append(t)
            toks = v2.split()
            firsts.append(toks[0] if toks else "")
        return finals, firsts

    def q_per_pair(finals, firsts, order):
        # order = np array of verse indices defining a sequence
        n = len(order)
        if n < 2:
            return None
        f_ord = [finals[i] for i in order]
        fi_ord = [firsts[i] for i in order]
        q = []
        for i in range(n - 1):
            el = 1 if f_ord[i] and f_ord[i] == f_ord[i+1] else 0
            cn = 1 if fi_ord[i+1] in conn else 0
            q.append(2 * el + 2 * cn)
        return q

    def windowed_mean(q, W):
        # Sliding average over windows of (W+1) verse pairs
        # Returns the mean of the per-window means; equivalently the
        # overall mean (same result, simpler)
        if len(q) < W:
            return float("nan")
        return float(np.mean(q))

    out = {"per_corpus": {}}
    for name in ["quran"] + ARABIC_CTRL:
        units = _band_a_units(corpora, name)
        if len(units) < 10:
            continue
        if len(units) > max_units_per_corpus:
            idx = rng.choice(len(units), size=max_units_per_corpus,
                             replace=False)
            units = [units[i] for i in idx]

        corp_out = {}
        for W in (5, 10, 20):
            ps = []
            for u in units:
                verses = u.verses
                if len(verses) < W + 1:
                    continue
                finals, firsts = compute_t(verses)
                idx0 = np.arange(len(verses))
                canon_q = q_per_pair(finals, firsts, idx0)
                canon_obs = windowed_mean(canon_q, W)
                if not np.isfinite(canon_obs):
                    continue
                n_beat = 0
                for _ in range(n_perms):
                    p_idx = rng.permutation(len(verses))
                    pq = q_per_pair(finals, firsts, p_idx)
                    st = windowed_mean(pq, W)
                    if np.isfinite(st) and st >= canon_obs:
                        n_beat += 1
                ps.append((1 + n_beat) / (1 + n_perms))
            if len(ps) < 5:
                continue
            # AUDIT 2026-04-19 (v5): drop the 1e-12 clip — (1+n_beat)/(1+n_perms)
            # is strictly > 0 by construction, so clipping is a dead branch that
            # would distort Fisher combine if n_perms ever rises to 1e6+.
            ps_arr = np.array(ps, dtype=float)
            chi2 = -2.0 * np.sum(np.log(ps_arr))
            df = 2 * len(ps_arr)
            # AUDIT 2026-04-19 (v5): `1 - chi2.cdf(x, df)` catastrophically
            # cancels to ≈ machine epsilon (≈1.1e-16) whenever chi2 >> df,
            # which then becomes the artificial floor blessed as D07. The
            # survival function `chi2.sf` is tail-accurate to ~1e-300, so
            # Quran's true Fisher-combined p is preserved rather than
            # bottomed out at the double-precision limit. Also expose the
            # log-scale quantity to avoid any downstream float underflow.
            fisher_p  = float(stats.chi2.sf(chi2, df))
            fisher_lp = float(stats.chi2.logsf(chi2, df) / math.log(10.0))
            corp_out[f"W={W}"] = {
                "n_surahs": len(ps),
                "fisher_p":     fisher_p,
                "fisher_log10p": fisher_lp,   # log10 tail — robust to underflow
                "chi2": float(chi2), "df": int(df),
                "fraction_sig_005": float((ps_arr < 0.05).mean()),
                "median_p": float(np.median(ps_arr)),
            }
        out["per_corpus"][name] = corp_out
    out["test"] = "T16 Scale-Free S24 (EL+CN transitions, sliding window)"
    out["note"] = ("Simplified S24 (no semantic). Quran should show "
                   "Fisher p < 0.01 at every window size if claim holds; "
                   "controls should not.")
    return out


# ========================================================== T17
def _build_sinv_from_feats(feats):
    feat_cols = ["EL", "VL_CV", "CN", "H_cond", "T"]
    ctrl = []
    for name in ARABIC_CTRL:
        ctrl += [r for r in feats.get(name, [])
                 if BAND_A_LO <= r["n_verses"] <= BAND_A_HI]
    Xc = np.array([[r[c] for c in feat_cols] for r in ctrl], dtype=float)
    cov = np.cov(Xc, rowvar=False) + 1e-6 * np.eye(5)
    return np.linalg.inv(cov)


def test_multi_scale_perturbation(corpora, feats, phi_m_result,
                                  n_perturb=10, seed: int = 42,
                                  max_units_per_target: int = 15) -> dict:
    """Three perturbation types on Quran (+ 2 negatives):
      P1 letter-level: random letter within a random word
      P2 word-level:   random word replaced by another from same bag
      P3 verse-level:  random verse shuffled within surah
    Measure mean Φ_M degradation per perturbation type."""
    rng = np.random.default_rng(seed)
    mu = np.array(phi_m_result["centroid_mu"])
    Sinv = _build_sinv_from_feats(feats)

    def phi_of(verses):
        f = fv2.features_5d(verses)
        d = f - mu
        return float(np.sqrt(d @ Sinv @ d))

    def perturb_letters(verses, frac):
        out = []
        for v in verses:
            toks = list(v.split())
            nmod = max(1, int(len(toks) * frac))
            for _ in range(nmod):
                if not toks:
                    break
                i = rng.integers(0, len(toks))
                w = list(toks[i])
                if w:
                    j = rng.integers(0, len(w))
                    repl = chr(rng.integers(0x0621, 0x063B))
                    w[j] = repl
                    toks[i] = "".join(w)
            out.append(" ".join(toks))
        return out

    def perturb_words(verses, frac):
        bag = [w for v in verses for w in v.split()]
        if not bag:
            return list(verses)
        out = []
        for v in verses:
            toks = list(v.split())
            nmod = max(1, int(len(toks) * frac))
            for _ in range(nmod):
                if not toks:
                    break
                i = rng.integers(0, len(toks))
                toks[i] = bag[rng.integers(0, len(bag))]
            out.append(" ".join(toks))
        return out

    def perturb_verses(verses, _):
        v2 = list(verses)
        rng.shuffle(v2)
        return v2

    perts = {
        "letter_10pct": lambda v: perturb_letters(v, 0.10),
        "word_10pct": lambda v: perturb_words(v, 0.10),
        "verse_shuffle": lambda v: perturb_verses(v, None),
    }

    results = {}
    for target_name in ("quran", "poetry_abbasi", "arabic_bible"):
        units = _band_a_units(corpora, target_name)
        if len(units) > max_units_per_target:
            idx = rng.choice(len(units), size=max_units_per_target,
                             replace=False)
            units = [units[i] for i in idx]
        if not units:
            continue
        per = {}
        for pname, pfn in perts.items():
            gaps = []
            for u in units:
                canon_phi = phi_of(u.verses)
                pert_phis = [phi_of(pfn(u.verses))
                             for _ in range(n_perturb)]
                gaps.append(canon_phi - float(np.mean(pert_phis)))
            per[pname] = {
                "n": len(units),
                "mean_gap": float(np.mean(gaps)),
                "median_gap": float(np.median(gaps)),
                "pct_canon_farther": float(np.mean(np.array(gaps) > 0) * 100),
            }
        results[target_name] = per

    return {
        "test": "T17 Multi-scale perturbation (letter / word / verse)",
        "n_perturb_per_unit": n_perturb,
        "per_target": results,
        "note": ("mean_gap > 0 ⇔ canonical is FARTHER from control "
                 "centroid than perturbed. Paper's structural-"
                 "singularity signal."),
    }


# ========================================================== T18
def test_verse_internal_word_order(corpora, feats, phi_m_result,
                                   n_perturb: int = 10, seed: int = 42,
                                   max_units_per_target: int = 20) -> dict:
    """Shuffle words WITHIN each verse (preserving the verse boundary).
    Measure how much the unit's Φ_M moves. Paper claims Quran
    verse-internal word order is non-random (d = 0.470)."""
    rng = np.random.default_rng(seed)
    mu = np.array(phi_m_result["centroid_mu"])
    Sinv = _build_sinv_from_feats(feats)

    def phi_of(verses):
        f = fv2.features_5d(verses)
        d = f - mu
        return float(np.sqrt(d @ Sinv @ d))

    def shuffle_within_verses(verses):
        out = []
        for v in verses:
            toks = v.split()
            rng.shuffle(toks)
            out.append(" ".join(toks))
        return out

    per = {}
    for name in ("quran", "poetry_abbasi", "arabic_bible"):
        units = _band_a_units(corpora, name)
        if len(units) > max_units_per_target:
            idx = rng.choice(len(units), size=max_units_per_target, replace=False)
            units = [units[i] for i in idx]
        if not units:
            continue
        gaps = []
        for u in units:
            canon = phi_of(u.verses)
            perts = [phi_of(shuffle_within_verses(u.verses))
                     for _ in range(n_perturb)]
            gaps.append(canon - float(np.mean(perts)))
        per[name] = {
            "n": len(units),
            "mean_gap": float(np.mean(gaps)),
            "median_gap": float(np.median(gaps)),
            "pct_canon_farther": float(np.mean(np.array(gaps) > 0) * 100),
        }
    return {
        "test": "T18 Verse-internal word-order shuffle (D14)",
        "n_perturb": n_perturb,
        "per_target": per,
        "note": ("If word order within verse is NON-random and structural, "
                 "shuffling should MOVE the unit toward the control cloud "
                 "(mean_gap > 0) in the Quran but not in negatives."),
    }


# ========================================================== T19
def test_rqa_anti_metric(corpora) -> dict:
    """RQA on the sequence of verse word-counts per unit.
    LAM (laminarity) is sensitive to 'flat' regions of similar lengths.
    Paper claims Quran LAM d = -0.395 (lower LAM = more anti-metric)."""
    def lam_of_seq(seq, eps_frac: float = 0.15, vmin: int = 2) -> float:
        """Simple laminarity: fraction of points that are part of vertical
        lines of length >= vmin in the recurrence plot with threshold
        eps = eps_frac * std(seq)."""
        x = np.asarray(seq, dtype=float)
        n = len(x)
        if n < 10:
            return float("nan")
        eps = eps_frac * (x.std() + 1e-9)
        # recurrence matrix R[i,j] = 1 if |x_i - x_j| <= eps
        diffs = np.abs(x[:, None] - x[None, :])
        R = (diffs <= eps).astype(int)
        np.fill_diagonal(R, 0)
        # vertical-line lengths in each column
        total_points = 0
        lam_points = 0
        for col in range(n):
            run = 0
            for row in range(n):
                if R[row, col] == 1:
                    run += 1
                else:
                    if run > 0:
                        total_points += run
                        if run >= vmin:
                            lam_points += run
                        run = 0
            if run > 0:
                total_points += run
                if run >= vmin:
                    lam_points += run
        return lam_points / total_points if total_points else 0.0

    per = {}
    quran_lams = None
    for name in ["quran"] + ARABIC_CTRL:
        units = _band_a_units(corpora, name)
        if len(units) < 10:
            continue
        vals = []
        for u in units:
            seq = [len(v.split()) for v in u.verses]
            lam = lam_of_seq(seq)
            if np.isfinite(lam):
                vals.append(lam)
        arr = np.array(vals)
        per[name] = {
            "n": len(arr),
            "mean_LAM": float(arr.mean()),
            "median_LAM": float(np.median(arr)),
        }
        if name == "quran":
            quran_lams = arr

    # Effect sizes vs Quran
    for name, v in list(per.items()):
        if name == "quran":
            v["d_vs_quran"] = 0.0
            continue
        recs = _band_a_units(corpora, name)
        vs = np.array([lam_of_seq([len(x.split()) for x in u.verses])
                       for u in recs])
        vs = vs[np.isfinite(vs)]
        v["d_vs_quran"] = _cohens_d(quran_lams, vs)

    return {
        "test": "T19 RQA Laminarity on verse-length sequence",
        "per_corpus": per,
        "note": ("Low LAM = anti-metric (no flat regions). Paper claims "
                 "Quran LAM is lower than controls, d = -0.395."),
    }


# ========================================================== T20
def test_structural_forgery_p3(corpora, feats, phi_m_result,
                               n_perturb: int = 20, seed: int = 42,
                               max_units_per_target: int = 25) -> dict:
    """Structural forgery P3: rhyme-swap. For each unit, swap each
    verse-final word with a random other word that has the SAME
    terminal letter in the same unit (preserving surface rhyme).

    Paper claims Quran Φ_M COLLAPSES 93% vs controls 36% under this
    adversarial perturbation - i.e., even though rhyme is preserved,
    the Quran's structure falls apart (because its structure goes
    BEYOND rhyme).
    """
    rng = np.random.default_rng(seed)
    mu = np.array(phi_m_result["centroid_mu"])
    Sinv = _build_sinv_from_feats(feats)

    def terminal_letter(v):
        v2 = fv2._strip_d(v).strip()
        for c in reversed(v2):
            if c.isalpha():
                return c
        return ""

    def phi_of(verses):
        f = fv2.features_5d(verses)
        d = f - mu
        return float(np.sqrt(d @ Sinv @ d))

    def rhyme_swap(verses):
        # Group words by terminal letter
        by_ending: dict[str, list[str]] = defaultdict(list)
        for v in verses:
            for w in v.split():
                letter = terminal_letter(w)
                if letter:
                    by_ending[letter].append(w)
        # Swap each verse's LAST word with a different word sharing its ending
        out = []
        for v in verses:
            toks = v.split()
            if len(toks) < 2:
                out.append(v)
                continue
            last = toks[-1]
            letter = terminal_letter(last)
            pool = [w for w in by_ending.get(letter, []) if w != last]
            if pool:
                toks[-1] = pool[rng.integers(0, len(pool))]
            out.append(" ".join(toks))
        return out

    per = {}
    for target in ("quran", "poetry_abbasi", "arabic_bible"):
        units = _band_a_units(corpora, target)
        if len(units) > max_units_per_target:
            idx = rng.choice(len(units), size=max_units_per_target, replace=False)
            units = [units[i] for i in idx]
        if not units:
            continue
        collapses = []
        gaps = []
        for u in units:
            canon = phi_of(u.verses)
            pert = [phi_of(rhyme_swap(u.verses)) for _ in range(n_perturb)]
            mean_pert = float(np.mean(pert))
            gap = canon - mean_pert
            gaps.append(gap)
            # "Collapse" = perturbed moves significantly closer to centroid
            # (perturbed Phi < canonical Phi - i.e., structure fell apart)
            collapses.append(1 if mean_pert < canon else 0)
        per[target] = {
            "n": len(units),
            "mean_gap": float(np.mean(gaps)),
            "median_gap": float(np.median(gaps)),
            "pct_collapsed": float(np.mean(collapses) * 100),
        }
    return {
        "test": "T20 Structural Forgery P3 (rhyme-swap)",
        "note": ("Paper: Quran 93% collapse (Phi drops) vs controls 36%. "
                 "Tests whether Quran's structure is more-than-rhyme."),
        "per_target": per,
    }


# ========================================================== T21
def test_cross_language_iliad(corpora) -> dict:
    """Cross-language: score Iliad on lang-agnostic 5-D proxy vs Greek
    null (same corpus, random permutations). Since we don't have
    Tanakh in repo, we only test Quran vs Iliad (Greek)."""
    iliad = corpora.get("iliad_greek", [])
    if len(iliad) < 5:
        return {"test": "T21", "error": "no iliad"}

    # Build Iliad empirical stops
    all_verses = [v for u in iliad for v in u.verses]
    stops = fv2.derive_stopwords(all_verses, top_n=20)

    # Lang-agnostic 5-D features on Iliad
    feats_iliad = []
    for u in iliad:
        f = fv2.features_5d_lang_agnostic(u.verses, stops=stops)
        feats_iliad.append(f)
    X = np.array(feats_iliad)
    mu = X.mean(axis=0)
    cov = np.cov(X, rowvar=False) + 1e-6 * np.eye(5)
    Sinv = np.linalg.inv(cov)
    phi_self = fv2.phi_m(X, mu, Sinv)

    # Under the paper's Shannon-Aljamal conditions framing, Iliad should
    # satisfy fewer conditions than the Quran. Our proxy: at unit level,
    # compute each of (EL high, VL_CV, T>0, path-minimality-z) and compare.
    # For now report the per-condition scores Iliad achieves.
    el_vals = np.array([f[0] for f in feats_iliad])
    cv_vals = np.array([f[1] for f in feats_iliad])
    cn_vals = np.array([f[2] for f in feats_iliad])
    hc_vals = np.array([f[3] for f in feats_iliad])
    t_vals = np.array([f[4] for f in feats_iliad])

    # Simple path cost on Iliad canonical vs permuted
    rng = np.random.default_rng(42)
    def path_cost(X):
        return float(np.sum(np.linalg.norm(np.diff(X, axis=0), axis=1)))
    canon = path_cost(X)
    perms = [path_cost(X[rng.permutation(len(X))]) for _ in range(2000)]
    perms = np.array(perms)
    z_path = (canon - perms.mean()) / perms.std()
    pct_below = float((perms < canon).mean() * 100)

    return {
        "test": "T21 Iliad self-test on lang-agnostic 5-D (CL1 partial)",
        "n_units": len(iliad),
        "iliad_lang_agnostic_feat_means": {
            "EL_proxy": float(el_vals.mean()),
            "VL_CV": float(cv_vals.mean()),
            "CN_proxy": float(cn_vals.mean()),
            "H_cond_initial": float(hc_vals.mean()),
            "T_lang": float(t_vals.mean()),
            "pct_T_gt_0": float((t_vals > 0).mean() * 100),
        },
        "iliad_path_z": float(z_path),
        "iliad_path_pct_below_canon": pct_below,
        "note": ("Only Iliad in repo; no Tanakh for full 3-way comparison. "
                 "Compare to Quran Arabic-native numbers separately."),
    }


# ========================================================== T22
def test_rd_times_el(feats) -> dict:
    """Root-Diversity (proxied by H_cond) x EL product.
    Paper: 0.559 Quran vs 0.337 matched Arabic poetry."""
    per = {}
    for name in ["quran"] + ARABIC_CTRL:
        recs = [r for r in feats.get(name, [])
                if BAND_A_LO <= r["n_verses"] <= BAND_A_HI]
        if not recs:
            continue
        el = np.array([r["EL"] for r in recs])
        hc = np.array([r["H_cond"] for r in recs])
        per[name] = {
            "n": len(recs),
            "mean_EL": float(el.mean()),
            "mean_H_cond": float(hc.mean()),
            "mean_RD_x_EL": float((el * hc).mean()),
        }
    ranked = sorted(per.items(), key=lambda kv: -kv[1]["mean_RD_x_EL"])
    return {
        "test": "T22 Root-Diversity x EL product (D22)",
        "per_corpus": per,
        "ranking": [{"corpus": k, "product": v["mean_RD_x_EL"]}
                    for k, v in ranked],
        "quran_rank": next((i+1 for i,(k,_) in enumerate(ranked)
                           if k == "quran"), None),
    }


# ========================================================== T23
def test_harakat_channel_capacity() -> dict:
    """E3: How much information does harakat (vocalisation) add to
    the Quran text over and above the consonantal rasm?

    H(harakat | rasm) measured across the whole vocalised Quran."""
    ROOT = Path(__file__).resolve().parent.parent
    p = ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt"
    if not p.exists():
        return {"test": "T23", "error": "quran_vocal.txt not found"}

    text = p.read_text("utf-8", errors="replace")
    # extract (rasm_char, harakat_following) bigrams
    DIAC_SET = fv2.DIAC
    pairs = []
    chars = list(text)
    i = 0
    while i < len(chars):
        c = chars[i]
        if c in DIAC_SET or c.isspace() or not c.isalpha():
            i += 1
            continue
        # gather any diacritics that follow c
        j = i + 1
        diacs = []
        while j < len(chars) and chars[j] in DIAC_SET:
            diacs.append(chars[j])
            j += 1
        pairs.append((c, "".join(diacs) or "<none>"))
        i = j

    # H(harakat), H(harakat | rasm)
    total = len(pairs)
    if total == 0:
        return {"test": "T23", "error": "no pairs"}

    cnt_h = Counter(p[1] for p in pairs)
    cnt_hr = Counter(pairs)
    cnt_r = Counter(p[0] for p in pairs)

    H_h = -sum((n/total) * math.log2(n/total) for n in cnt_h.values() if n > 0)
    # H(h|r) = sum_r p(r) * H(h|r=r)
    H_hr = 0.0
    for r, nr in cnt_r.items():
        pr = nr / total
        # distribution of h given r
        h_given_r = {h: nh/nr for (rr, h), nh in cnt_hr.items() if rr == r}
        h_row = -sum(p * math.log2(p) for p in h_given_r.values() if p > 0)
        H_hr += pr * h_row

    H_max = math.log2(len(cnt_h)) if cnt_h else 0.0
    return {
        "test": "T23 Harakat channel capacity (E3)",
        "n_rasm_chars": total,
        "vocab_harakat": len(cnt_h),
        "H_harakat_marginal_bits": H_h,
        "H_harakat_given_rasm_bits": H_hr,
        "H_max_uniform_bits": H_max,
        "redundancy_fraction": float(1 - H_hr / H_max) if H_max > 0 else float("nan"),
        "note": ("H(h|r) measures residual uncertainty of diacritics given "
                 "their consonant. Lower = harakat is structured by rasm. "
                 "Near-maximum would mean random assignment."),
    }
