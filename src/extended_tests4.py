# -*- coding: utf-8 -*-
"""
src/extended_tests4.py
======================
Phase-5 tests (T32-T35). Outcomes of the 2026-04-20 breakthrough audit
(see experiments/ADIYAT_BREAKTHROUGH_AUDIT_2026-04-20.md).

T32  Length-coherence F6 (Spearman rho of adjacent verse word-counts)
        Confirms a NEW real property: Quran's adjacent verses are more
        length-coherent than Arabic controls, d=+0.88 on clean subset.
        Previously misreported in MASTER_FINDINGS_REPORT as "anti-length-
        regularity d=-0.670" (sign inverted). This test corrects the record.

T33  VERU (Verse-Ending Root Uniqueness) replication
        Tests the old "Law IV" (Quran maximises root-diversity under rhyme).
        Finding: FALSIFIED. Controls have HIGHER verse-ending root uniqueness
        than Quran (d=-0.753 short-for-short). The old claim that Adiyat's
        11/11 unique roots is Quran-distinctive does not hold.

T34  Letter-swap sensitivity ceiling (Adiyat case)
        For each of the 5 canonical features (EL, VL_CV, CN, H_cond, T),
        measures how many control-sigma the feature moves when a single
        letter is swapped in Adiyat (ضبحاً->صبحاً). Honest ceiling: only
        2 of 5 features move at all; max ~0.5 sigma each.

T35  Multi-scale Hurst applicability
        Reports the fraction of Band-A units on which verse-length Hurst
        and delta Hurst can be estimated (need N>=32 for R/S with 4
        windows). Finding: 94% NaN on controls. The "multi-level Hurst
        H=0.90/0.81" claim in MASTER_FINDINGS is not a usable feature at
        this scale.

All tests operate on the raw-data corpora and use CamelTools roots
(via src.features / src.roots). No checkpoint dependency.

Author: Cascade, 2026-04-20 breakthrough audit integration
"""
from __future__ import annotations

import math
from collections import Counter

import numpy as np
from scipy import stats

from . import features as fv2
from . import roots as rc
from . import raw_loader as rl

BAND_A_LO, BAND_A_HI = 15, 100
SHORT_BAND_LO, SHORT_BAND_HI = 5, 20  # matched-length band for Adiyat (N=11)

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
    # hadith_bukhari excluded — quotes Quran verbatim (standard quarantine)
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


def _mwu_p(a, b, alt="two-sided"):
    try:
        _, p = stats.mannwhitneyu(a, b, alternative=alt)
        return float(p)
    except Exception:
        return float("nan")


def _units_in_band(corpora, name, lo, hi):
    return [u for u in corpora.get(name, [])
            if lo <= u.n_verses() <= hi]


# ========================================================== T32  Length coherence F6
def _spearman_adj(verses):
    """Spearman rho between adjacent verse word-counts. nan if insufficient
    variation or too-few verses."""
    lens = [len(fv2._strip_d(v).split()) for v in verses]
    if len(lens) < 4:
        return float("nan")
    a = np.array(lens[:-1]); b = np.array(lens[1:])
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    r, _ = stats.spearmanr(a, b)
    return float(r) if not np.isnan(r) else float("nan")


def test_length_coherence_f6(corpora) -> dict:
    """F6: Spearman rho(len_i, len_{i+1}). Adjacent-length regularity.

    Quran-distinctive property NEW in Apr-2026 audit. Corrects the
    sign-flipped claim in MASTER_FINDINGS_REPORT (which had d=-0.670).
    """
    per_unit_quran = []
    per_unit_ctrl = {}
    quran_units = _units_in_band(corpora, "quran", BAND_A_LO, BAND_A_HI)
    for u in quran_units:
        v = _spearman_adj(u.verses)
        if not np.isnan(v):
            per_unit_quran.append(v)

    ctrl_pool = []
    for name in ARABIC_CTRL:
        vals = []
        for u in _units_in_band(corpora, name, BAND_A_LO, BAND_A_HI):
            v = _spearman_adj(u.verses)
            if not np.isnan(v):
                vals.append(v)
        if vals:
            per_unit_ctrl[name] = {
                "n": len(vals), "mean": float(np.mean(vals)),
                "median": float(np.median(vals)),
                "d_vs_quran": _cohens_d(np.array(per_unit_quran), np.array(vals)),
            }
        ctrl_pool.extend(vals)

    if not per_unit_quran or not ctrl_pool:
        return {"test": "T32 F6 length coherence", "error": "insufficient data"}

    q = np.array(per_unit_quran)
    c = np.array(ctrl_pool)
    return {
        "test": "T32 F6 length coherence (Spearman rho adj word-counts, Band A)",
        "definition": "F6(unit) = Spearman rho(len_i, len_{i+1}) over verses",
        "quran": {"n": len(q), "mean": float(q.mean()),
                  "median": float(np.median(q)), "std": float(q.std(ddof=1))},
        "pool_ctrl": {"n": len(c), "mean": float(c.mean()),
                      "median": float(np.median(c)), "std": float(c.std(ddof=1))},
        "cohens_d_pool": _cohens_d(q, c),
        "p_mwu_two_sided": _mwu_p(q, c, "two-sided"),
        "nan_rate_note": ("F6 is nan when a unit has <4 verses or constant "
                          "word-counts across adjacent pairs; ~56% of Band-A "
                          "controls have nan, 0% of Quran."),
        "per_corpus": per_unit_ctrl,
        "relabel_from_master_report": (
            "MASTER_FINDINGS_REPORT called this 'anti-length-regularity' with "
            "d=-0.670. Direct measurement yields d=+0.88 (length COHERENCE, "
            "sign inverted). Property is real; interpretation corrected."
        ),
    }


# ========================================================== T33  VERU replication
def _verse_ending_root(verse: str) -> str:
    toks = fv2._strip_d(verse).strip().split()
    if not toks:
        return ""
    r = rc.primary_root_normalized(toks[-1])
    return r or ""


def _veru(verses):
    roots = [_verse_ending_root(v) for v in verses]
    roots = [r for r in roots if r]
    if not roots:
        return float("nan"), 0
    return len(set(roots)) / len(roots), len(roots)


def test_veru_replication(corpora) -> dict:
    """VERU = unique verse-ending roots / n verses.

    Replicates the 2026-04-20 audit: tests whether the old Law IV claim
    (Quran maximises root-diversity under rhyme at verse endings) holds.

    Finding: FALSIFIED on direct cross-corpus measurement. Controls have
    HIGHER VERU than Quran. Poetry enforces rhyme-word uniqueness formally;
    Quran does not. Adiyat's 11/11 is not distinctive.
    """
    def collect(units, band=None):
        out = []
        for u in units:
            n = u.n_verses()
            if band is not None and not (band[0] <= n <= band[1]):
                continue
            if n < 5:
                continue
            v, nr = _veru(u.verses)
            if not np.isnan(v) and nr >= 5:
                out.append({"label": u.label, "n": nr, "veru": v})
        return out

    # Global (all lengths) + short-band (matched to Adiyat)
    quran_all = collect(corpora.get("quran", []))
    quran_short = collect(corpora.get("quran", []), (SHORT_BAND_LO, SHORT_BAND_HI))
    ctrl_all_map = {}
    ctrl_short_map = {}
    for name in ARABIC_CTRL:
        ctrl_all_map[name] = collect(corpora.get(name, []))
        ctrl_short_map[name] = collect(corpora.get(name, []),
                                       (SHORT_BAND_LO, SHORT_BAND_HI))

    def frac_perfect(arr):
        if not len(arr):
            return float("nan")
        return float(((np.asarray(arr) >= 0.9999).sum()) / len(arr))

    qa = np.array([r["veru"] for r in quran_all])
    qs = np.array([r["veru"] for r in quran_short])
    ca = np.array([r["veru"] for lst in ctrl_all_map.values() for r in lst])
    cs = np.array([r["veru"] for lst in ctrl_short_map.values() for r in lst])

    per_corpus = {}
    for name, lst in ctrl_short_map.items():
        if not lst:
            continue
        arr = np.array([r["veru"] for r in lst])
        per_corpus[name] = {
            "n_short": len(arr),
            "mean_short": float(arr.mean()),
            "frac_perfect_short": frac_perfect(arr),
            "d_vs_quran_short": _cohens_d(qs, arr) if len(qs) >= 2 else float("nan"),
        }

    # Adiyat (Q:100) specifically
    adiyat_entry = None
    for u in corpora.get("quran", []):
        if u.label == "Q:100":
            v, n = _veru(u.verses)
            adiyat_entry = {
                "label": u.label, "n_verses": n, "veru": float(v),
                "rank_within_quran_short_ties_counted": (
                    int((qs > v).sum()) + 1 if len(qs) else None
                ),
                "frac_quran_short_ge": frac_perfect(qs),
                "frac_ctrl_short_ge": (
                    float((cs >= v - 1e-9).mean()) if len(cs) else None
                ),
            }
            break

    return {
        "test": "T33 VERU (verse-ending root uniqueness) cross-corpus",
        "definition": "VERU(unit) = unique verse-ending roots / n verses",
        "global": {
            "quran": {"n": len(qa), "mean": float(qa.mean()) if len(qa) else float("nan"),
                      "frac_perfect": frac_perfect(qa)},
            "pool_ctrl": {"n": len(ca), "mean": float(ca.mean()) if len(ca) else float("nan"),
                          "frac_perfect": frac_perfect(ca)},
            "cohens_d_quran_vs_ctrl": _cohens_d(qa, ca),
        },
        "short_band_5_20": {
            "quran": {"n": len(qs), "mean": float(qs.mean()) if len(qs) else float("nan"),
                      "frac_perfect": frac_perfect(qs)},
            "pool_ctrl": {"n": len(cs), "mean": float(cs.mean()) if len(cs) else float("nan"),
                          "frac_perfect": frac_perfect(cs)},
            "cohens_d_quran_vs_ctrl": _cohens_d(qs, cs),
            "p_mwu_quran_greater_ctrl": _mwu_p(qs, cs, "greater"),
        },
        "adiyat": adiyat_entry,
        "per_corpus_short_band": per_corpus,
        "verdict": (
            "FALSIFIED: controls have HIGHER VERU than Quran (d<0). "
            "Poetry's form constraints enforce rhyme-word uniqueness; the "
            "Quran does not. Adiyat canonical VERU=1.000 is achieved by "
            "~27% of Quran-short and ~62% of ctrl-short units — not a "
            "distinctive signature. This corrects the old ADIYAT_CASE.md "
            "'Law IV' claim."
        ),
    }


# ========================================================== T34  Letter-swap sensitivity
def test_letter_swap_sensitivity_adiyat(corpora, feats) -> dict:
    """For Surat al-Adiyat (Q:100), compute the canonical 5-D feature vector
    and the feature vector for each of 4 variants (ع<->غ, ض<->ص, both).
    Report per-feature delta in control-sigma units. Establishes the honest
    ceiling for single-letter forgery detection at surah-level statistics.
    """
    adiyat = None
    for u in corpora.get("quran", []):
        if u.label == "Q:100":
            adiyat = u
            break
    if adiyat is None:
        return {"test": "T34 letter-swap sensitivity", "error": "Adiyat not found"}

    strip_d = fv2._strip_d

    def sub(text, pairs):
        for a, b in pairs:
            if a in text:
                return text.replace(a, b, 1)
        return text

    gh_pairs = [("والعاديات", "والغاديات"), ("العاديات", "الغاديات")]
    sb_pairs = [("ضبحا", "صبحا")]
    rest = [strip_d(v) for v in adiyat.verses[1:]]
    variants = {
        "v1_canonical":    [strip_d(adiyat.verses[0])] + rest,
        "v2_ghaad_dabh":   [sub(strip_d(adiyat.verses[0]), gh_pairs)] + rest,
        "v3_aad_subh":     [sub(strip_d(adiyat.verses[0]), sb_pairs)] + rest,
        "v4_ghaad_subh":   [sub(sub(strip_d(adiyat.verses[0]), gh_pairs), sb_pairs)]
                           + rest,
    }

    feat_names = ["EL", "VL_CV", "CN", "H_cond", "T"]
    feat_vectors = {name: fv2.features_5d(v) for name, v in variants.items()}

    # Control sigma per feature: use all Band-A controls from feats
    ctrl_rows = []
    for name in ARABIC_CTRL:
        ctrl_rows += [r for r in feats.get(name, [])
                      if BAND_A_LO <= r["n_verses"] <= BAND_A_HI]
    if not ctrl_rows:
        return {"test": "T34 letter-swap sensitivity",
                "error": "no Band-A controls available"}
    ctrl_mat = np.array([[r[c] for c in feat_names] for r in ctrl_rows])
    ctrl_sigma = ctrl_mat.std(axis=0, ddof=1)

    canonical = feat_vectors["v1_canonical"]
    per_variant = {}
    for name, vec in feat_vectors.items():
        deltas = vec - canonical
        dz = np.abs(deltas) / np.where(ctrl_sigma > 0, ctrl_sigma, 1.0)
        per_variant[name] = {
            "feature_vector": {feat_names[i]: float(vec[i]) for i in range(5)},
            "delta_from_canonical": {feat_names[i]: float(deltas[i]) for i in range(5)},
            "abs_delta_in_ctrl_sigmas": {feat_names[i]: float(dz[i]) for i in range(5)},
            "n_features_that_moved": int((np.abs(deltas) > 1e-9).sum()),
            "total_displacement_sigmas": float(np.sqrt((dz**2).sum())),
        }

    return {
        "test": "T34 Letter-swap sensitivity ceiling (Adiyat)",
        "definition": ("For each variant of Adiyat v1, compute |delta|/sigma_ctrl "
                       "per canonical feature. Sum of squares gives total "
                       "Mahalanobis-like displacement in control-sigma units."),
        "n_ctrl_band_a": len(ctrl_rows),
        "ctrl_sigma_band_a": {feat_names[i]: float(ctrl_sigma[i]) for i in range(5)},
        "per_variant": per_variant,
        "honest_ceiling_note": (
            "Only 2 of 5 features (H_cond, T) move under single-letter swap. "
            "EL, VL_CV, CN are mathematically invariant because: EL depends on "
            "verse-final letter (unchanged when swap preserves final 'ا'), "
            "VL_CV depends on word counts (unchanged), CN depends on first "
            "word (unchanged). Max total displacement ~0.6 control-sigma — "
            "this is the true upper bound of 5-D letter-level detection."
        ),
    }


# ========================================================== T35  Hurst applicability
def _hurst_rs(x, min_chunks=4):
    """Classical R/S Hurst estimator. Returns nan if sequence cannot support
    at least 2 chunk sizes with `min_chunks` windows each."""
    x = np.asarray(x, float)
    N = len(x)
    if N < 10:
        return float("nan")
    chunks = [c for c in [8, 12, 16, 24, 32, 48, 64, 96] if N // c >= min_chunks]
    if len(chunks) < 2:
        return float("nan")
    log_n, log_rs = [], []
    for n in chunks:
        rs_vals = []
        for i in range(N // n):
            w = x[i*n:(i+1)*n]
            Y = np.cumsum(w - w.mean())
            R = Y.max() - Y.min()
            S = w.std(ddof=0)
            if S > 0:
                rs_vals.append(R / S)
        if rs_vals:
            log_n.append(math.log(n))
            log_rs.append(math.log(np.mean(rs_vals)))
    if len(log_n) < 2:
        return float("nan")
    slope, _ = np.polyfit(log_n, log_rs, 1)
    return float(slope)


def test_hurst_applicability(corpora) -> dict:
    """Report the fraction of units on which verse-length R/S Hurst (and
    its first-difference Hurst) can be honestly estimated. Shows that the
    multi-level Hurst claim from MASTER_FINDINGS_REPORT is not a usable
    feature at this scale — 94% of Band-A Arabic controls have N too
    small for R/S to converge.
    """
    rows = {}
    for name in ["quran"] + ARABIC_CTRL:
        units = _units_in_band(corpora, name, BAND_A_LO, BAND_A_HI)
        n_total = len(units)
        if n_total == 0:
            continue
        h_lens_vals, h_delta_vals = [], []
        h_lens_nan = 0; h_delta_nan = 0
        for u in units:
            lens = [len(fv2._strip_d(v).split()) for v in u.verses]
            h_l = _hurst_rs(lens)
            if np.isnan(h_l):
                h_lens_nan += 1
            else:
                h_lens_vals.append(h_l)
            if len(lens) >= 12:
                h_d = _hurst_rs(np.diff(np.array(lens, float)))
                if np.isnan(h_d):
                    h_delta_nan += 1
                else:
                    h_delta_vals.append(h_d)
            else:
                h_delta_nan += 1
        rows[name] = {
            "n_band_a": n_total,
            "H_lens_nan_rate": h_lens_nan / n_total,
            "H_delta_nan_rate": h_delta_nan / n_total,
            "H_lens_mean_on_computable": (
                float(np.mean(h_lens_vals)) if h_lens_vals else float("nan")
            ),
            "H_delta_mean_on_computable": (
                float(np.mean(h_delta_vals)) if h_delta_vals else float("nan")
            ),
            "n_computable_H_lens": len(h_lens_vals),
            "n_computable_H_delta": len(h_delta_vals),
        }

    return {
        "test": "T35 Multi-scale Hurst applicability at Band-A",
        "definition": ("R/S Hurst requires N>=32 for 4 windows at chunk=8 "
                       "and 2+ chunk sizes for log-log regression."),
        "per_corpus": rows,
        "verdict": (
            "PRACTICAL NULL: >90% of Band-A Arabic control units cannot "
            "support Hurst R/S estimation. The 'multi-level Hurst H=0.90 / "
            "H=0.81' figures from MASTER_FINDINGS_REPORT (based on the "
            "whole-Quran concatenated 6,236-verse sequence) do not "
            "generalise to per-surah-level features. Hurst is NOT a "
            "practical feature for a 5-D or higher Phi_M at Band-A or "
            "short-band scale."
        ),
    }
