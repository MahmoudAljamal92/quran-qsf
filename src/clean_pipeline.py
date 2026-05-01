# -*- coding: utf-8 -*-
"""
src/clean_pipeline.py
=====================
Single entrypoint that reproduces (or falsifies) every surviving paper claim
from raw-data files only. No pickle checkpoints, no hardcoded constants.

Steps:
  1. Load raw corpora from data/corpora/ar/  (src/raw_loader.py)
  2. Sanity-check gate                        (src/verify_corpora.py)
  3. CamelTools root extraction (cached)      (src/roots.py)
  4. 5-D feature extraction                   (src/features.py)
  5. Thirty-five tests T1-T35 against the raw data
       T1-T23  core + extensions (audit round Apr 2026)
       T24-T31 re-tests of v10.10-v10.13 notebook findings (Apr 18 2026)
       T32-T35 2026-04-20 breakthrough audit (extended_tests4.py):
                 T32 F6 length coherence (NEW real finding)
                 T33 VERU replication (falsifies old Law IV)
                 T34 Letter-swap sensitivity (Adiyat, honest ceiling)
                 T35 Multi-scale Hurst applicability (practical null)
  6. Report: results/CLEAN_PIPELINE_REPORT.json + .md

Run:   python -X utf8 -u -m src.clean_pipeline
"""
from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

import numpy as np
from scipy import stats

from . import roots as rc
from . import extended_tests as et
from . import extended_tests2 as et2
from . import extended_tests3 as et3
from . import extended_tests4 as et4
from . import features as fv2
from . import raw_loader as rl
from . import verify_corpora as vc

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ARABIC_CORPORA_FOR_CONTROL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
    # AUDIT 2026-04-19 (v5) — `hadith_bukhari` QUARANTINED: Sahih al-Bukhari
    # quotes the Quran verbatim by design (it is the Prophetic tradition
    # *about* the Quran). Including it in the control pool biases every
    # Mahalanobis-to-centroid statistic (D02, D11, D17, D22, Ω) upward
    # because the control centroid gets pulled toward the Quran. The
    # notebook's own Cell 22 already quarantines it — this module was the
    # silent leak. Matches notebook.ARABIC_CTRL_POOL exactly.
]
BAND_A_LO, BAND_A_HI = 15, 100  # paper's "matched length" band

# ----------------------------------------------------------------------
# Audit-fix L4 (2026-04-26): explicit corpus -> feature-extractor mapping.
# Previously the only check was `lang_agnostic = (name == "iliad_greek")`,
# which silently routed any future cross-lang or cross-tradition corpus
# through the Arabic CamelTools `features_5d` and produced garbage. The
# pipeline now classifies each loaded corpus into exactly one of two sets
# and aborts loudly on an unknown name (forcing the maintainer to declare
# intent before the run).
#
# To add a new corpus, append its name to one of the two sets below
# AND keep `src/raw_loader.load_all` in sync.
# ----------------------------------------------------------------------
ARABIC_CAMELTOOLS_CORPORA = frozenset({
    "quran",
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible",
    "hadith_bukhari",   # extras=True only; quarantined from controls
    "hindawi",          # extras=True only
})
LANG_AGNOSTIC_CORPORA = frozenset({
    "iliad_greek",                        # extras=True only
    "hebrew_tanakh", "greek_nt",          # include_cross_lang=True
    "rigveda", "avestan_yasna",           # include_cross_tradition=True
    # Pali splits dynamically into pali_dn, pali_mn, ... (one per Nikaya
    # collection); matched by the `pali_` prefix in `_classify_corpus`.
})


def _classify_corpus(name: str) -> str:
    """Return ``"arabic"`` or ``"lang_agnostic"``; raise ``RuntimeError``
    when the name is not declared in either set (fail-closed: the audit
    spec forbids silent fall-through to the Arabic extractor)."""
    if name in ARABIC_CAMELTOOLS_CORPORA:
        return "arabic"
    if name in LANG_AGNOSTIC_CORPORA or name.startswith("pali_"):
        return "lang_agnostic"
    raise RuntimeError(
        f"Unknown corpus name {name!r}: not in ARABIC_CAMELTOOLS_CORPORA "
        f"and not in LANG_AGNOSTIC_CORPORA. Add it to one of those sets "
        f"in src/clean_pipeline.py and keep src/raw_loader.load_all in "
        f"sync. Refusing to silently route through the Arabic extractor."
    )


# ======================================================================
# 1. Load + sanity
# ======================================================================
def _fingerprint_corpora(corpora: dict[str, list[rl.Unit]]) -> dict:
    """A deterministic hash of what we're analysing (for the report)."""
    fp = {}
    for name, units in corpora.items():
        m = sha256()
        for u in units:
            m.update(u.label.encode("utf-8"))
            for v in u.verses:
                m.update(v.encode("utf-8"))
                m.update(b"\n")
            m.update(b"||")
        fp[name] = {
            "n_units": len(units),
            "n_verses": sum(u.n_verses() for u in units),
            "n_words": sum(u.n_words() for u in units),
            "sha256_12": m.hexdigest()[:12],
        }
    return fp


# ======================================================================
# 2. Feature extraction (cached)
# ======================================================================
def _extract_features(
    corpora: dict[str, list[rl.Unit]]
) -> dict[str, list[dict]]:
    """For each unit, compute 5-D features. Arabic corpora use the
    CamelTools-backed features; Greek uses the lang-agnostic proxy."""
    out: dict[str, list[dict]] = {}
    for name, units in corpora.items():
        print(f"  [features] {name:<22s} {len(units):>5d} units", end="",
              flush=True)
        t0 = time.time()
        # L4 (2026-04-26): set-based corpus -> extractor classification.
        # Fails closed on unknown names; previously a single-corpus equality
        # check silently routed Hebrew/Greek-NT/Pali/Vedic/Avestan through
        # the Arabic CamelTools extractor.
        lang_agnostic = (_classify_corpus(name) == "lang_agnostic")
        if lang_agnostic:
            stops = fv2.derive_stopwords(
                (v for u in units for v in u.verses), top_n=20
            )
        recs: list[dict] = []
        for u in units:
            if lang_agnostic:
                f = fv2.features_5d_lang_agnostic(u.verses, stops=stops)
            else:
                f = fv2.features_5d(u.verses)
            recs.append({
                "label": u.label,
                "n_verses": u.n_verses(),
                "n_words": u.n_words(),
                "EL": float(f[0]), "VL_CV": float(f[1]), "CN": float(f[2]),
                "H_cond": float(f[3]), "T": float(f[4]),
            })
        out[name] = recs
        print(f"   ({time.time() - t0:.1f}s)")
    rc.flush_cache()
    return out


# ======================================================================
# Helper: robust stats
# ======================================================================
def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, float); b = np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    pooled_var = ((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) \
        / (len(a) + len(b) - 2)
    if pooled_var <= 0:
        return float("nan")
    return (a.mean() - b.mean()) / math.sqrt(pooled_var)


def _cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    """Non-parametric effect size; |δ| in [0,1], sign = direction."""
    a = np.sort(np.asarray(a, float))
    b = np.asarray(b, float)
    # Count pairs where a > b and a < b
    gt = sum(np.searchsorted(a, x, side="left") for x in b)
    lt = sum(len(a) - np.searchsorted(a, x, side="right") for x in b)
    n = len(a) * len(b)
    if n == 0:
        return float("nan")
    return (lt - gt) / n


def _mwu_pvalue(a: np.ndarray, b: np.ndarray, alt="greater") -> float:
    try:
        _, p = stats.mannwhitneyu(a, b, alternative=alt)
        return float(p)
    except Exception:
        return float("nan")


def _band_a_mask(recs: list[dict]) -> np.ndarray:
    n = np.array([r["n_verses"] for r in recs])
    return (n >= BAND_A_LO) & (n <= BAND_A_HI)


# ======================================================================
# T1 -- Anti-Metric Law
# ======================================================================
def test_anti_metric(feats: dict[str, list[dict]]) -> dict:
    # AUDIT 2026-04-19 (v5): Band-A filter was missing here — the only T-test
    # in the pipeline that compared Quran vs controls WITHOUT length matching.
    # VL_CV is length-sensitive (the CV of verse lengths depends on the number
    # of verses sampled: Var[CV] ~ 1/N). Quran's 114 surahs span 3..286 verses;
    # controls span vastly different ranges per book chapter. Without Band A
    # [15, 100] the D01 effect is length-confounded. Every other test in this
    # pipeline already applies Band A — T1 is brought into line here.
    def _ba(recs):
        return [r for r in recs if BAND_A_LO <= r["n_verses"] <= BAND_A_HI]

    q = np.array([r["VL_CV"] for r in _ba(feats["quran"])])
    ctrl_vals = []
    per_corpus = {}
    for name in ARABIC_CORPORA_FOR_CONTROL:
        if name not in feats:
            continue
        recs_ba = _ba(feats[name])
        if len(recs_ba) < 3:
            # not enough Band-A units in this control — skip rather than pool
            continue
        v = np.array([r["VL_CV"] for r in recs_ba])
        ctrl_vals.append(v)
        per_corpus[name] = {
            "n": len(v), "mean": float(v.mean()), "std": float(v.std()),
            "d_vs_quran": _cohens_d(q, v),
        }
    if not ctrl_vals:
        return {"test": "Anti-Metric Law (VL_CV, Band A)",
                "error": "no controls with >=3 Band-A units"}
    pool = np.concatenate(ctrl_vals)
    return {
        "test": "Anti-Metric Law (VL_CV, Band A [15,100])",
        "quran": {"n": len(q), "mean": float(q.mean()), "std": float(q.std())},
        "pool_ctrl": {
            "n": len(pool), "mean": float(pool.mean()), "std": float(pool.std())
        },
        "cohens_d_pool": _cohens_d(q, pool),
        "cliffs_delta_pool": _cliffs_delta(q, pool),
        "p_mwu_greater": _mwu_pvalue(q, pool, "greater"),
        "per_corpus": per_corpus,
    }


# ======================================================================
# T2 -- Phi_M on Arabic-only controls, Band A
# ======================================================================
def test_phi_m(feats: dict[str, list[dict]]) -> dict:
    # Build Arabic control pool at Band A
    feat_cols = ["EL", "VL_CV", "CN", "H_cond", "T"]
    q_recs = [r for r in feats["quran"] if BAND_A_LO <= r["n_verses"] <= BAND_A_HI]
    ctrl_recs = []
    for name in ARABIC_CORPORA_FOR_CONTROL:
        if name not in feats:
            continue
        ctrl_recs += [r for r in feats[name]
                      if BAND_A_LO <= r["n_verses"] <= BAND_A_HI]
    Xq = np.array([[r[c] for c in feat_cols] for r in q_recs], dtype=float)
    Xc = np.array([[r[c] for c in feat_cols] for r in ctrl_recs], dtype=float)

    mu = Xc.mean(axis=0)
    cov = np.cov(Xc, rowvar=False) + 1e-6 * np.eye(5)
    Sinv = np.linalg.inv(cov)
    phi_q = fv2.phi_m(Xq, mu, Sinv)
    phi_c = fv2.phi_m(Xc, mu, Sinv)
    d = _cohens_d(phi_q, phi_c)
    p = _mwu_pvalue(phi_q, phi_c, "greater")

    # Per-corpus breakdown
    per_corpus = {}
    for name in ARABIC_CORPORA_FOR_CONTROL:
        recs = [r for r in feats.get(name, [])
                if BAND_A_LO <= r["n_verses"] <= BAND_A_HI]
        if len(recs) < 3:
            continue
        X = np.array([[r[c] for c in feat_cols] for r in recs], dtype=float)
        phi = fv2.phi_m(X, mu, Sinv)
        per_corpus[name] = {
            "n": len(recs), "mean_phi": float(phi.mean()),
            "median_phi": float(np.median(phi)),
            "d_vs_quran": _cohens_d(phi_q, phi),
        }

    return {
        "test": "Phi_M Mahalanobis (Band A [15,100], Arabic-only ctrl)",
        "n_quran": len(q_recs), "n_ctrl": len(ctrl_recs),
        "mean_phi_quran": float(phi_q.mean()),
        "mean_phi_ctrl": float(phi_c.mean()),
        "median_phi_quran": float(np.median(phi_q)),
        "median_phi_ctrl": float(np.median(phi_c)),
        "cohens_d": d, "p_mwu_greater": p,
        "cliffs_delta": _cliffs_delta(phi_q, phi_c),
        "centroid_mu": mu.tolist(),
        "Sinv": Sinv.tolist(),
        "per_corpus": per_corpus,
    }


# ======================================================================
# T3 -- H_cond per corpus
# ======================================================================
def test_hcond_by_corpus(feats: dict[str, list[dict]]) -> dict:
    per = {}
    q = np.array([r["H_cond"] for r in feats["quran"]
                  if BAND_A_LO <= r["n_verses"] <= BAND_A_HI])
    for name, recs in feats.items():
        v = np.array([r["H_cond"] for r in recs
                      if BAND_A_LO <= r["n_verses"] <= BAND_A_HI])
        if len(v) < 3:
            continue
        per[name] = {
            "n": len(v), "mean": float(v.mean()),
            "median": float(np.median(v)),
            "d_vs_quran": _cohens_d(q, v) if name != "quran" else 0.0,
        }
    ranked = sorted(per.items(), key=lambda kv: -kv[1]["mean"])
    return {
        "test": "H_cond (root bigrams, verse-final, Band A)",
        "per_corpus": per,
        "ranking": [
            {"corpus": name, "mean": d["mean"], "n": d["n"]}
            for name, d in ranked
        ],
        "quran_rank": next(
            (i + 1 for i, (nm, _) in enumerate(ranked) if nm == "quran"),
            None,
        ),
    }


# ======================================================================
# T4 -- Omega without hardcoded constants
# ======================================================================
def test_omega(feats: dict[str, list[dict]],
               phi_m_result: dict) -> dict:
    """Omega = product of five within-run ratios, all using CORPUS MEANS
    (no hardcoded 1.0 / 2.8 / 0.29 / 1.72 references).
        r1 = Phi_M_corpus_mean / mean(control_phis)
        r2 = H_cond_corpus_mean / mean(control_Hcond)
        r3 = VL_CV_corpus_mean / mean(control_VL_CV)
        r4 = (1 + EL_corpus_mean) / (1 + mean(control_EL))
        r5 = (1 + CN_corpus_mean) / (1 + mean(control_CN))
    """
    # reconstruct per-corpus Phi_M means from phi_m_result
    pcm = phi_m_result["per_corpus"]
    ctrl_phi = np.mean([pcm[k]["mean_phi"] for k in ARABIC_CORPORA_FOR_CONTROL
                        if k in pcm])
    ctrl_phi_q = phi_m_result["mean_phi_quran"]

    def corpus_stats(name):
        recs = [r for r in feats.get(name, [])
                if BAND_A_LO <= r["n_verses"] <= BAND_A_HI]
        if not recs:
            return None
        arr = {c: np.array([r[c] for r in recs]) for c in
               ["EL", "VL_CV", "CN", "H_cond", "T"]}
        return {c: float(v.mean()) for c, v in arr.items()}

    q_s = corpus_stats("quran")
    ctrl_means = {}
    for c in ["EL", "VL_CV", "CN", "H_cond", "T"]:
        vals = []
        for name in ARABIC_CORPORA_FOR_CONTROL:
            s = corpus_stats(name)
            if s is None:
                continue
            vals.append(s[c])
        ctrl_means[c] = float(np.mean(vals))

    def omega_for(name, phi_mean):
        s = corpus_stats(name)
        if s is None:
            return None
        r1 = phi_mean / max(ctrl_phi, 1e-9)
        r2 = s["H_cond"] / max(ctrl_means["H_cond"], 1e-9)
        r3 = s["VL_CV"] / max(ctrl_means["VL_CV"], 1e-9)
        r4 = (1.0 + s["EL"]) / (1.0 + ctrl_means["EL"])
        r5 = (1.0 + s["CN"]) / (1.0 + ctrl_means["CN"])
        return {
            "r1_phi": r1, "r2_hcond": r2, "r3_vl": r3,
            "r4_el": r4, "r5_cn": r5,
            "omega": r1 * r2 * r3 * r4 * r5,
        }

    per = {"quran": omega_for("quran", ctrl_phi_q)}
    for name in ARABIC_CORPORA_FOR_CONTROL:
        if name in pcm:
            per[name] = omega_for(name, pcm[name]["mean_phi"])

    per = {k: v for k, v in per.items() if v is not None}
    ranked = sorted(per.items(), key=lambda kv: -kv[1]["omega"])
    return {
        "test": "Omega (no hardcoded constants; ratios vs within-run ctrl mean)",
        "control_means": ctrl_means,
        "per_corpus": per,
        "ranking": [
            {"corpus": k, "omega": v["omega"]} for k, v in ranked
        ],
        "quran_rank": next(
            (i + 1 for i, (n, _) in enumerate(ranked) if n == "quran"),
            None,
        ),
    }


# ======================================================================
# T5 -- Pre-reg tautology check
# ======================================================================
def test_tautology(
    feats: dict[str, list[dict]],
    corpora: dict[str, list[rl.Unit]],
    phi_m_result: dict,
    n_perturb: int = 30,
    perturb_frac: float = 0.10,
    seed: int = 42,
) -> dict:
    """Run the canon-vs-perturb protocol on Quran AND on two negatives
    (poetry_abbasi + arabic_bible). The test claims to prove the Quran
    is structurally optimised; if non-Quran outliers also pass it at
    >=75% canon-wins, the test is tautological."""
    feat_cols = ["EL", "VL_CV", "CN", "H_cond", "T"]
    mu = np.array(phi_m_result["centroid_mu"])
    # Rebuild Sinv the same way test_phi_m did (from Arabic controls Band A)
    ctrl_recs = []
    for name in ARABIC_CORPORA_FOR_CONTROL:
        ctrl_recs += [r for r in feats.get(name, [])
                      if BAND_A_LO <= r["n_verses"] <= BAND_A_HI]
    Xc = np.array([[r[c] for c in feat_cols] for r in ctrl_recs], dtype=float)
    cov = np.cov(Xc, rowvar=False) + 1e-6 * np.eye(5)
    Sinv = np.linalg.inv(cov)
    rng = np.random.default_rng(seed)

    def run_one(target_name: str, sample_size: int = 40) -> dict:
        units = [u for u in corpora[target_name]
                 if BAND_A_LO <= u.n_verses() <= BAND_A_HI]
        if len(units) == 0:
            return {"target": target_name, "n": 0, "canon_wins_pct": None}
        if len(units) > sample_size:
            idx = rng.choice(len(units), size=sample_size, replace=False)
            units = [units[i] for i in idx]
        wins = 0
        gaps = []
        for u in units:
            bag = [w for v in u.verses for w in v.split()] or ["x"]
            canon_feat = fv2.features_5d(u.verses)
            canon_phi = float(np.sqrt((canon_feat - mu) @ Sinv @ (canon_feat - mu)))
            perturbed = []
            for _ in range(n_perturb):
                # perturb: replace `perturb_frac` of tokens with random bag items
                verses_p = []
                for v in u.verses:
                    toks = v.split()
                    if not toks:
                        verses_p.append(v); continue
                    mask = rng.random(len(toks)) < perturb_frac
                    for i, m in enumerate(mask):
                        if m:
                            toks[i] = bag[rng.integers(0, len(bag))]
                    verses_p.append(" ".join(toks))
                pf = fv2.features_5d(verses_p)
                perturbed.append(
                    float(np.sqrt((pf - mu) @ Sinv @ (pf - mu)))
                )
            p_mean = float(np.mean(perturbed))
            gap = canon_phi - p_mean
            gaps.append(gap)
            if canon_phi > p_mean:
                wins += 1
        return {
            "target": target_name, "n": len(units),
            "canon_wins_pct": 100.0 * wins / len(units),
            "gap_mean": float(np.mean(gaps)),
            "gap_median": float(np.median(gaps)),
        }

    out = {
        "test": "Pre-reg tautology check (canon > perturbed?)",
        "threshold_pct": 75.0,
        "note": "Any non-Quran outlier passing at >=75% implies the test "
                "is tautological for multivariate outliers.",
        "results": [
            run_one("quran"),
            run_one("poetry_abbasi"),
            run_one("arabic_bible"),
        ],
    }
    rc.flush_cache()
    return out


# ======================================================================
# T6 -- H-Cascade fractality
# ======================================================================
def _hcond_letter_level(verses: list[str]) -> float:
    """Conditional entropy on letter bigrams within flattened text."""
    text = " ".join(verses)
    letters = [c for c in text if c.isalpha()]
    return _hcond_seq(letters)


def _hcond_word_level(verses: list[str]) -> float:
    words = [w for v in verses for w in v.split()]
    return _hcond_seq(words)


def _hcond_verse_initial(verses: list[str]) -> float:
    firsts = [v.split()[0] for v in verses if v.split()]
    return _hcond_seq(firsts)


def _hcond_verse_final(verses: list[str]) -> float:
    finals = [v.split()[-1] for v in verses if v.split()]
    return _hcond_seq(finals)


def _hcond_seq(tokens: list) -> float:
    if len(tokens) < 2:
        return 0.0
    pairs = Counter(zip(tokens[:-1], tokens[1:]))
    first = Counter(tokens[:-1])
    total = sum(first.values())
    if total == 0:
        return 0.0
    by_a = defaultdict(Counter)
    for (a, b), n in pairs.items():
        by_a[a][b] += n
    h = 0.0
    for a, row in by_a.items():
        p_a = first[a] / total
        rt = sum(row.values())
        if rt == 0:
            continue
        rh = 0.0
        for n in row.values():
            p = n / rt
            if p > 0:
                rh -= p * math.log2(p)
        h += p_a * rh
    return h


def test_h_cascade(corpora: dict[str, list[rl.Unit]]) -> dict:
    """F = mean/std ratio of normalized entropies across 4 scales.
    Quran is expected to have a tighter cross-scale ratio distribution
    (higher F -> more 'cross-scale regularity')."""
    def unit_F(u: rl.Unit) -> float:
        hL = _hcond_letter_level(u.verses)
        hW = _hcond_word_level(u.verses)
        hI = _hcond_verse_initial(u.verses)
        hF = _hcond_verse_final(u.verses)
        vals = np.array([hL, hW, hI, hF], dtype=float)
        # normalize to [0,1] per unit (relative cross-scale fingerprint)
        if vals.max() == vals.min():
            return 0.0
        norm = (vals - vals.min()) / (vals.max() - vals.min())
        if norm.std() < 1e-9:
            return float("inf")
        return float(norm.mean() / norm.std())

    def corpus_Fs(name):
        units = [u for u in corpora.get(name, [])
                 if BAND_A_LO <= u.n_verses() <= BAND_A_HI]
        return np.array([unit_F(u) for u in units], dtype=float)

    q = corpus_Fs("quran")
    q = q[np.isfinite(q)]
    per = {}
    for name in ARABIC_CORPORA_FOR_CONTROL:
        v = corpus_Fs(name); v = v[np.isfinite(v)]
        if len(v) < 3: continue
        per[name] = {
            "n": len(v), "mean_F": float(v.mean()),
            "median_F": float(np.median(v)),
            "d_vs_quran": _cohens_d(q, v),
        }
    pool = np.concatenate([corpus_Fs(n) for n in ARABIC_CORPORA_FOR_CONTROL
                           if n in corpora])
    pool = pool[np.isfinite(pool)]
    return {
        "test": "H-Cascade cross-scale fractality F",
        "quran": {"n": len(q), "mean_F": float(q.mean()),
                  "median_F": float(np.median(q))},
        "pool_ctrl": {"n": len(pool), "mean_F": float(pool.mean())},
        "cohens_d": _cohens_d(q, pool),
        "cliffs_delta": _cliffs_delta(q, pool),
        "p_mwu_greater": _mwu_pvalue(q, pool, "greater"),
        "per_corpus": per,
    }


def _check_corpus_lock_drift(live_fp: dict) -> None:
    """AUDIT FIX 2026-04-21: warn if live corpus fingerprint diverges from
    the committed corpus_lock.json. Does not abort — just makes drift visible."""
    import warnings
    lock_path = ROOT / "results" / "integrity" / "corpus_lock.json"
    if not lock_path.exists():
        return
    try:
        with open(lock_path, "r", encoding="utf-8") as f:
            lock = json.load(f)
        locked_combined = lock.get("combined", "")
        live_combined = live_fp.get("combined", "")
        if locked_combined and live_combined and locked_combined != live_combined:
            warnings.warn(
                f"[CORPUS DRIFT] Live corpus fingerprint {live_combined[:16]}... "
                f"!= committed corpus_lock {locked_combined[:16]}...\n"
                f"  Results may not match the locked evidence base.",
                stacklevel=2,
            )
        else:
            print(f"[lock ] corpus fingerprint matches committed lock  OK")
    except Exception:
        pass


# ======================================================================
# Orchestrator
# ======================================================================
def run_clean_pipeline() -> dict:
    t_start = time.time()
    print("=" * 72)
    print("CLEAN PIPELINE - run from raw data, no checkpoint")
    print("=" * 72)

    print("\nStep 1 / 6 - Load raw corpora")
    corpora = rl.load_all(include_extras=True)
    fp = _fingerprint_corpora(corpora)

    # AUDIT FIX 2026-04-21: compare live fingerprint to committed corpus_lock.
    _check_corpus_lock_drift(fp)

    print("\nStep 2 / 6 - Sanity-check gate")
    sanity = vc.verify_all(corpora)
    if any(not v["ok"] for v in sanity.values()):
        print("[!] Sanity gate FAILED - aborting.")
        return {"status": "aborted", "sanity": sanity}

    print("\nStep 3 / 6 - Feature extraction (CamelTools-backed)")
    feats = _extract_features(corpora)

    print("\nStep 4 / 6 - Six tests")
    results = {}
    print("  T1 Anti-Metric Law ...", end="", flush=True)
    t0 = time.time()
    results["T1_anti_metric"] = test_anti_metric(feats)
    print(f" ({time.time()-t0:.1f}s)  d={results['T1_anti_metric']['cohens_d_pool']:.3f}")

    print("  T2 Phi_M Mahalanobis ...", end="", flush=True)
    t0 = time.time()
    results["T2_phi_m"] = test_phi_m(feats)
    print(f" ({time.time()-t0:.1f}s)  d={results['T2_phi_m']['cohens_d']:.3f}")

    print("  T3 H_cond by corpus ...", end="", flush=True)
    t0 = time.time()
    results["T3_hcond"] = test_hcond_by_corpus(feats)
    print(f" ({time.time()-t0:.1f}s)  Quran rank: #{results['T3_hcond']['quran_rank']}")

    print("  T4 Omega rebuild ...", end="", flush=True)
    t0 = time.time()
    results["T4_omega"] = test_omega(feats, results["T2_phi_m"])
    print(f" ({time.time()-t0:.1f}s)  Quran rank: #{results['T4_omega']['quran_rank']}")

    print("  T5 Pre-reg tautology check ...", end="", flush=True)
    t0 = time.time()
    results["T5_tautology"] = test_tautology(
        feats, corpora, results["T2_phi_m"]
    )
    print(f" ({time.time()-t0:.1f}s)")
    for r in results["T5_tautology"]["results"]:
        print(f"      {r['target']:<18s} canon_wins={r['canon_wins_pct']}%")

    print("  T6 H-Cascade fractality ...", end="", flush=True)
    t0 = time.time()
    results["T6_hcascade"] = test_h_cascade(corpora)
    print(f" ({time.time()-t0:.1f}s)  d={results['T6_hcascade']['cohens_d']:.3f}")

    # -------- Phase 2: extended tests --------
    print("  T7 EL/CN dual-channel ...", end="", flush=True)
    t0 = time.time()
    results["T7_el_cn_dual"] = et.test_el_cn_dual_channel(feats, corpora)
    print(f" ({time.time()-t0:.1f}s)  "
          f"EL rank={results['T7_el_cn_dual']['quran_rank_EL']}, "
          f"CN rank={results['T7_el_cn_dual']['quran_rank_CN']}, "
          f"G_turbo rank={results['T7_el_cn_dual']['quran_rank_G_turbo']}")

    print("  T8 Path minimality ...", end="", flush=True)
    t0 = time.time()
    results["T8_path"] = et.test_path_minimality(feats, n_perms=2000)
    pq = results["T8_path"]["per_corpus"].get("quran", {})
    print(f" ({time.time()-t0:.1f}s)  "
          f"Quran z={pq.get('z_path', float('nan')):.2f}, "
          f"pct<canon={pq.get('pct_path_below_canon', float('nan')):.1f}%")

    print("  T9 Markov unforgeability ...", end="", flush=True)
    t0 = time.time()
    results["T9_markov"] = et.test_markov_unforgeability(corpora, n_perms=200)
    mq = results["T9_markov"]["per_corpus"].get("quran", {})
    print(f" ({time.time()-t0:.1f}s)  "
          f"Quran z={mq.get('z_shuff_vs_canon', float('nan')):.2f}")

    print("  T10 T-distribution ...", end="", flush=True)
    t0 = time.time()
    results["T10_t_dist"] = et.test_t_distribution(feats)
    print(f" ({time.time()-t0:.1f}s)  "
          f"Quran rank (pct T>0) = "
          f"#{results['T10_t_dist']['quran_rank_pct_T_positive']}")

    print("  T11 Bigram sufficiency ...", end="", flush=True)
    t0 = time.time()
    results["T11_bigram_suf"] = et.test_bigram_sufficiency(corpora)
    print(f" ({time.time()-t0:.1f}s)  "
          f"Quran rank (low H3/H2) = "
          f"#{results['T11_bigram_suf']['quran_rank_low_ratio']}")

    print("  T12 10-fold CV Phi_M ...", end="", flush=True)
    t0 = time.time()
    results["T12_cv_phi_m"] = et.test_cv_phi_m(feats, results["T2_phi_m"])
    r = results["T12_cv_phi_m"]
    print(f" ({time.time()-t0:.1f}s)  "
          f"min d={r['min_d']:.2f}, median d={r['median_d']:.2f}, "
          f"max p={r['max_p']:.3g}")

    print("  T13 Meccan vs Medinan ...", end="", flush=True)
    t0 = time.time()
    results["T13_meccan_medinan"] = et.test_meccan_medinan(corpora)
    r = results["T13_meccan_medinan"]
    print(f" ({time.time()-t0:.1f}s)  "
          f"F_meccan={r['F_meccan_mean']:.2f}, "
          f"F_medinan={r['F_medinan_mean']:.2f}, "
          f"all pass={r['all_thresholds_pass']}")

    print("  T14 Bootstrap Omega ...", end="", flush=True)
    t0 = time.time()
    results["T14_bootstrap_omega"] = et.test_bootstrap_omega(
        feats, results["T4_omega"], n_boot=1000
    )
    r = results["T14_bootstrap_omega"]
    print(f" ({time.time()-t0:.1f}s)  "
          f"median Ω={r['median_omega']:.2f}, "
          f"pct>2 = {r['pct_bootstraps_omega_gt_2']:.1f}%")

    print("  T15 Classifier AUC ...", end="", flush=True)
    t0 = time.time()
    results["T15_classifier"] = et.test_classifier_auc(feats)
    r = results["T15_classifier"]
    print(f" ({time.time()-t0:.1f}s)  AUC={r.get('auc', float('nan')):.3f}")

    # -------- Phase 3: last-mile tests --------
    print("  T16 Scale-Free S24 ...", end="", flush=True)
    t0 = time.time()
    results["T16_scale_free"] = et2.test_scale_free_s24(
        corpora, n_perms=100, max_units_per_corpus=40
    )
    q_w10 = results["T16_scale_free"]["per_corpus"].get("quran", {}).get("W=10", {})
    print(f" ({time.time()-t0:.1f}s)  "
          f"Quran W=10 Fisher p={q_w10.get('fisher_p', float('nan')):.3g}")

    print("  T17 Multi-scale perturbation ...", end="", flush=True)
    t0 = time.time()
    results["T17_multi_scale_pert"] = et2.test_multi_scale_perturbation(
        corpora, feats, results["T2_phi_m"], n_perturb=10,
        max_units_per_target=15
    )
    q = results["T17_multi_scale_pert"]["per_target"].get("quran", {})
    print(f" ({time.time()-t0:.1f}s)  "
          f"Quran verse_shuffle_gap={q.get('verse_shuffle',{}).get('mean_gap', float('nan')):.2f}")

    print("  T18 Verse-internal word order ...", end="", flush=True)
    t0 = time.time()
    results["T18_verse_internal"] = et2.test_verse_internal_word_order(
        corpora, feats, results["T2_phi_m"], n_perturb=10,
        max_units_per_target=20
    )
    q = results["T18_verse_internal"]["per_target"].get("quran", {})
    print(f" ({time.time()-t0:.1f}s)  "
          f"Quran mean_gap={q.get('mean_gap', float('nan')):.3f}, "
          f"pct_canon_farther={q.get('pct_canon_farther', float('nan')):.1f}%")

    print("  T19 RQA Laminarity ...", end="", flush=True)
    t0 = time.time()
    results["T19_rqa"] = et2.test_rqa_anti_metric(corpora)
    q = results["T19_rqa"]["per_corpus"].get("quran", {})
    print(f" ({time.time()-t0:.1f}s)  "
          f"Quran LAM={q.get('mean_LAM', float('nan')):.3f}")

    print("  T20 Structural Forgery P3 (rhyme-swap) ...", end="", flush=True)
    t0 = time.time()
    results["T20_forgery_p3"] = et2.test_structural_forgery_p3(
        corpora, feats, results["T2_phi_m"], n_perturb=15,
        max_units_per_target=25
    )
    q = results["T20_forgery_p3"]["per_target"].get("quran", {})
    p = results["T20_forgery_p3"]["per_target"].get("poetry_abbasi", {})
    b = results["T20_forgery_p3"]["per_target"].get("arabic_bible", {})
    print(f" ({time.time()-t0:.1f}s)  "
          f"Q={q.get('pct_collapsed', float('nan')):.0f}%, "
          f"abbasi={p.get('pct_collapsed', float('nan')):.0f}%, "
          f"bible={b.get('pct_collapsed', float('nan')):.0f}%")

    print("  T21 Cross-language Iliad ...", end="", flush=True)
    t0 = time.time()
    results["T21_cross_lang"] = et2.test_cross_language_iliad(corpora)
    r = results["T21_cross_lang"]
    print(f" ({time.time()-t0:.1f}s)  "
          f"Iliad path z={r.get('iliad_path_z', float('nan')):.2f}, "
          f"pct T>0={r.get('iliad_lang_agnostic_feat_means',{}).get('pct_T_gt_0', float('nan')):.1f}%")

    print("  T22 RD x EL product ...", end="", flush=True)
    t0 = time.time()
    results["T22_rd_el"] = et2.test_rd_times_el(feats)
    print(f" ({time.time()-t0:.1f}s)  "
          f"Quran rank=#{results['T22_rd_el']['quran_rank']}")

    print("  T23 Harakat channel capacity ...", end="", flush=True)
    t0 = time.time()
    results["T23_harakat"] = et2.test_harakat_channel_capacity()
    r = results["T23_harakat"]
    if "error" in r:
        print(f" ({time.time()-t0:.1f}s)  ERROR: {r['error']}")
    else:
        print(f" ({time.time()-t0:.1f}s)  "
              f"H(h|r)={r['H_harakat_given_rasm_bits']:.3f} bits, "
              f"redundancy={r['redundancy_fraction']:.1%}")

    # -------- Phase 4: re-tests of v10.10-v10.13 notebook findings --------
    print("  T24 Lesion dose-response ...", end="", flush=True)
    t0 = time.time()
    results["T24_lesion"] = et3.test_lesion_dose_response(corpora)
    r = results["T24_lesion"]
    d1 = r["dose_response"].get("1.0pct", {})
    d5 = r["dose_response"].get("5.0pct", {})
    print(f" ({time.time()-t0:.1f}s)  "
          f"EL drop @1%={d1.get('EL_drop_from_canonical', float('nan'))*100:.1f}%, "
          f"@5%={d5.get('EL_drop_from_canonical', float('nan'))*100:.1f}%, "
          f"peak={r.get('heat_capacity_peak_at','?')}")

    print("  T25 Info-geometry saddle ...", end="", flush=True)
    t0 = time.time()
    results["T25_info_geo_saddle"] = et3.test_info_geometry_saddle(feats)
    r = results["T25_info_geo_saddle"]
    if "error" in r:
        print(f" ({time.time()-t0:.1f}s)  ERROR: {r['error']}")
    else:
        neg, pos = r["quran_eigval_signs"]
        print(f" ({time.time()-t0:.1f}s)  "
              f"Quran saddle={r['quran_is_saddle']} ({neg}-/{pos}+), "
              f"total saddles={r['n_saddles']}/{r['n_corpora']}")

    print("  T26 Terminal position depth ...", end="", flush=True)
    t0 = time.time()
    results["T26_terminal_depth"] = et3.test_terminal_position_depth(corpora)
    r = results["T26_terminal_depth"]
    d1 = r["per_position"]["-1"]["cohens_d"]
    d2 = r["per_position"]["-2"]["cohens_d"]
    d3 = r["per_position"]["-3"]["cohens_d"]
    print(f" ({time.time()-t0:.1f}s)  "
          f"d(-1)={d1:.2f}, d(-2)={d2:.2f}, d(-3)={d3:.2f}, "
          f"depth={r['signal_depth_letters']} letters")

    print("  T27 Inter-surah cost ...", end="", flush=True)
    t0 = time.time()
    results["T27_inter_surah_cost"] = et3.test_inter_surah_cost(feats, "quran", n_perms=1000)
    r = results["T27_inter_surah_cost"]
    if "error" in r:
        print(f" ({time.time()-t0:.1f}s)  ERROR: {r['error']}")
    else:
        print(f" ({time.time()-t0:.1f}s)  "
              f"ratio={r['cost_ratio']:.3f}, p={r['p_value']:.4f}")

    print("  T28 Markov-order sufficiency ...", end="", flush=True)
    t0 = time.time()
    results["T28_markov_order"] = et3.test_markov_order_sufficiency(corpora)
    r = results["T28_markov_order"]
    if "error" in r:
        print(f" ({time.time()-t0:.1f}s)  ERROR: {r['error']}")
    else:
        print(f" ({time.time()-t0:.1f}s)  "
              f"Q H2/H1={r['quran_H2_over_H1_mean']:.3f}, "
              f"ctrl={r['ctrl_H2_over_H1_mean']:.3f}, "
              f"d={(r['cohens_d_quran_vs_ctrl'] or float('nan')):.2f}")

    print("  T29 Phase transition phi_frac ...", end="", flush=True)
    t0 = time.time()
    results["T29_phi_frac"] = et3.test_phase_transition_phi_frac(feats)
    r = results["T29_phi_frac"]
    if "error" in r:
        print(f" ({time.time()-t0:.1f}s)  ERROR: {r['error']}")
    else:
        print(f" ({time.time()-t0:.1f}s)  "
              f"phi_frac={r['phi_frac']:.3f}, "
              f"near_golden={r['near_golden_ratio']}, "
              f"HC_peak_mid={r['heat_capacity_peak_at_medium']}")

    print("  T30 RG flow ...", end="", flush=True)
    t0 = time.time()
    results["T30_rg_flow"] = et3.test_rg_flow(feats)
    r = results["T30_rg_flow"]
    if "error" in r:
        print(f" ({time.time()-t0:.1f}s)  ERROR: {r['error']}")
    else:
        print(f" ({time.time()-t0:.1f}s)  "
              f"Q alpha={r['quran_alpha']:.2f}, "
              f"rank={r['quran_rank']}/{r['n_corpora']}, "
              f"{r['verdict']}")

    print("  T31 Fisher curvature ...", end="", flush=True)
    t0 = time.time()
    results["T31_fisher_curvature"] = et3.test_fisher_curvature(feats)
    r = results["T31_fisher_curvature"]
    if "error" in r:
        print(f" ({time.time()-t0:.1f}s)  ERROR: {r['error']}")
    else:
        print(f" ({time.time()-t0:.1f}s)  "
              f"Q curv rank={r['quran_curvature_rank']}/{r['n_corpora']}, "
              f"Q volume rank={r['quran_volume_rank']}")

    # -------- Phase 5: 2026-04-20 breakthrough audit (T32-T35) --------
    print("  T32 F6 length coherence ...", end="", flush=True)
    t0 = time.time()
    results["T32_f6_length_coherence"] = et4.test_length_coherence_f6(corpora)
    r = results["T32_f6_length_coherence"]
    if "error" in r:
        print(f" ({time.time()-t0:.1f}s)  ERROR: {r['error']}")
    else:
        print(f" ({time.time()-t0:.1f}s)  "
              f"Quran mean={r['quran']['mean']:+.3f}, "
              f"ctrl mean={r['pool_ctrl']['mean']:+.3f}, "
              f"d={r['cohens_d_pool']:+.3f}")

    print("  T33 VERU replication ...", end="", flush=True)
    t0 = time.time()
    results["T33_veru"] = et4.test_veru_replication(corpora)
    r = results["T33_veru"]
    if "error" in r:
        print(f" ({time.time()-t0:.1f}s)  ERROR: {r['error']}")
    else:
        sb = r["short_band_5_20"]
        print(f" ({time.time()-t0:.1f}s)  "
              f"Q_short mean={sb['quran']['mean']:.3f}, "
              f"ctrl_short mean={sb['pool_ctrl']['mean']:.3f}, "
              f"d={sb['cohens_d_quran_vs_ctrl']:+.3f}")

    print("  T34 Letter-swap sensitivity (Adiyat) ...", end="", flush=True)
    t0 = time.time()
    results["T34_letter_swap"] = et4.test_letter_swap_sensitivity_adiyat(
        corpora, feats
    )
    r = results["T34_letter_swap"]
    if "error" in r:
        print(f" ({time.time()-t0:.1f}s)  ERROR: {r['error']}")
    else:
        v3 = r["per_variant"]["v3_aad_subh"]
        print(f" ({time.time()-t0:.1f}s)  "
              f"subh_variant: {v3['n_features_that_moved']}/5 feats move, "
              f"total disp={v3['total_displacement_sigmas']:.3f} sigma")

    print("  T35 Hurst applicability ...", end="", flush=True)
    t0 = time.time()
    results["T35_hurst_applicability"] = et4.test_hurst_applicability(corpora)
    r = results["T35_hurst_applicability"]
    if "error" in r:
        print(f" ({time.time()-t0:.1f}s)  ERROR: {r['error']}")
    else:
        pc = r["per_corpus"].get("quran", {})
        c_rate = np.mean([
            r["per_corpus"][k]["H_lens_nan_rate"]
            for k in r["per_corpus"] if k != "quran"
        ])
        print(f" ({time.time()-t0:.1f}s)  "
              f"Q nan={pc.get('H_lens_nan_rate', float('nan'))*100:.0f}%, "
              f"ctrl nan={c_rate*100:.0f}%")

    elapsed = time.time() - t_start
    print(f"\nTotal pipeline time: {elapsed:.1f}s")

    out = {
        "status": "ok",
        "run_elapsed_seconds": elapsed,
        "corpus_fingerprint": fp,
        "sanity": sanity,
        "results": results,
    }

    out_path = OUT_DIR / "CLEAN_PIPELINE_REPORT.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nWritten: {out_path}")
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run_clean_pipeline()
