"""
expP4_cross_tradition_R3/run.py
================================
Cross-TRADITION extension of R3 (path-cost minimality of canonical
chapter ordering), per the LC2 universal-extension hypothesis.

This experiment adds three pre/non-Abrahamic oral-liturgical corpora
to the original 4-corpus exp35 universe:

    Existing (exp35, locked):
        quran           (Arabic)            114 surahs
        hebrew_tanakh   (Hebrew, WLC)        book-chapter units
        greek_nt        (Greek, OpenGNT)     book-chapter units
        iliad_greek     (Greek, Perseus)     24 books

    New (this experiment, P4):
        pali_dn         (Pali, SuttaCentral) 34 Dīgha Nikāya suttas
        pali_mn         (Pali, SuttaCentral) 152 Majjhima Nikāya suttas
        rigveda         (Vedic, DharmicData) 1024 sūktas (10 maṇḍalas)
        avestan_yasna   (Avestan, Geldner)   69 Yasna chapters

The 4-corpus subset reproduces exp35 (sanity check); the 4 NEW corpora
constitute the actual P4 test of LC2.

PROTOCOL
--------
Identical to exp35_R3_cross_scripture_redo, just over 8 corpora:
  * 5-D language-agnostic features (EL, VL_CV, CN, H_cond_initials, T_lang)
  * within-corpus z-score before path-cost
  * Euclidean adjacent-pair distance summed over the canonical order
  * 5000 RNG-shuffled-order permutations, seed = 42
  * z, empirical one-sided p, BH pool across all 8 tests

Stopwords:
  * quran:         ARABIC_CONN (paper §2.2)
  * everything else: derive_stopwords(verses, top_n=20)

Reads only:
  * data/corpora/ar/quran_bare.txt
  * data/corpora/he/tanakh_wlc.txt
  * data/corpora/el/{opengnt_v3_3.csv, iliad_perseus.xml}
  * data/corpora/pi/{dn,mn}/*_root-pli-ms.json
  * data/corpora/sa/rigveda_mandala_*.json
  * data/corpora/ae/y*.htm

Writes ONLY under results/experiments/expP4_cross_tradition_R3/:
  * expP4_cross_tradition_R3.json
  * self_check_<ts>.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    safe_output_dir,
    self_check_begin,
    self_check_end,
)
from src import raw_loader  # noqa: E402
from src.features import (  # noqa: E402
    ARABIC_CONN,
    derive_stopwords,
    el_rate,
    vl_cv,
    cn_rate,
    h_cond_initials,
    h_el,
)

EXP = "expP4_cross_tradition_R3"
SEED = 42
N_PERM = 5000


# --------------------------------------------------------------------------- #
# Language-agnostic per-unit 5-D feature vector (identical to exp35).         #
# --------------------------------------------------------------------------- #
def _features_lang_agnostic(verses: list[str], stops: set[str]) -> np.ndarray:
    """EL, VL_CV, CN, H_cond_initials, T_lang = H_cond_initials - h_el."""
    el = el_rate(verses)
    cv = vl_cv(verses)
    cn = cn_rate(verses, stops)
    hc = h_cond_initials(verses)
    he = h_el(verses)
    t = hc - he
    return np.array([el, cv, cn, hc, t], dtype=float)


def _path_cost(X: np.ndarray) -> float:
    """Euclidean sum of adjacent-row distances. X already z-scored."""
    if len(X) < 2:
        return 0.0
    diffs = np.diff(X, axis=0)
    return float(np.sum(np.linalg.norm(diffs, axis=1)))


def _z_score_matrix(X: np.ndarray) -> np.ndarray:
    """Column-wise z-score with NaN-safe median imputation."""
    X = X.astype(float).copy()
    for j in range(X.shape[1]):
        col = X[:, j]
        m = np.isnan(col)
        if m.any():
            col[m] = np.nanmedian(col)
            X[:, j] = col
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd == 0] = 1.0
    return (X - mu) / sd


def _one_sided_p_bh(p_values: list[float]) -> dict:
    """Benjamini-Hochberg pooling for 1-sided p-values."""
    n = len(p_values)
    if n == 0:
        return {"raw": [], "bh_adjusted": [], "min_bh": 1.0, "n_tests": 0}
    order = np.argsort(p_values)
    adj = np.empty(n, dtype=float)
    prev = 1.0
    for rank_idx, i in enumerate(reversed(order)):
        k = n - rank_idx
        bh = p_values[i] * n / k
        prev = min(prev, bh)
        adj[i] = min(prev, 1.0)
    return {
        "raw": list(map(float, p_values)),
        "bh_adjusted": list(map(float, adj)),
        "min_bh": float(adj.min()),
        "n_tests": n,
    }


# --------------------------------------------------------------------------- #
# Per-corpus driver                                                           #
# --------------------------------------------------------------------------- #
def _run_corpus(
    name: str, units, stops: set[str], rng: np.random.Generator,
) -> dict:
    """Compute features, canonical path, and permutation null."""
    t0 = time.time()
    if not units:
        return {"n_units": 0, "skipped": True, "reason": "no units"}
    X_raw = np.array(
        [_features_lang_agnostic(u.verses, stops) for u in units],
        dtype=float,
    )
    n = X_raw.shape[0]
    if n < 4:
        return {"n_units": n, "skipped": True, "reason": "n < 4"}

    X = _z_score_matrix(X_raw)
    canon_cost = _path_cost(X)
    perm_costs = np.empty(N_PERM, dtype=float)
    for b in range(N_PERM):
        idx = rng.permutation(n)
        perm_costs[b] = _path_cost(X[idx])

    perm_mean = float(perm_costs.mean())
    perm_std = float(perm_costs.std())
    z = (canon_cost - perm_mean) / (perm_std if perm_std > 0 else 1.0)
    pct_below = float((perm_costs < canon_cost).mean())
    p_one_sided = max(pct_below, 1.0 / (N_PERM + 1))
    return {
        "n_units": n,
        "alphabet": _alphabet_of(name),
        "tradition_class": _tradition_class_of(name),
        "canonical_path_cost": float(canon_cost),
        "perm_mean": perm_mean,
        "perm_std": perm_std,
        "z_path": float(z),
        "pct_perms_below_canon": pct_below,
        "p_one_sided": float(p_one_sided),
        "n_perm": N_PERM,
        "runtime_seconds": round(time.time() - t0, 2),
        "feature_means_before_zscore": X_raw.mean(axis=0).tolist(),
        "feature_stds_before_zscore": X_raw.std(axis=0).tolist(),
    }


def _alphabet_of(name: str) -> str:
    return {
        "quran": "arabic",
        "hebrew_tanakh": "hebrew",
        "greek_nt": "greek",
        "iliad_greek": "greek",
        "pali_dn": "latin_iast",
        "pali_mn": "latin_iast",
        "rigveda": "devanagari",
        "avestan_yasna": "latin_geldner",
    }.get(name, "unknown")


def _tradition_class_of(name: str) -> str:
    """LC2 pre-registration: which corpora are 'oral-liturgical' vs
    'narrative-non-mnemonic' (negative control)?"""
    oral_liturgical = {
        "quran", "pali_dn", "pali_mn", "rigveda", "avestan_yasna",
    }
    narrative_or_mixed = {
        "hebrew_tanakh", "greek_nt", "iliad_greek",
    }
    if name in oral_liturgical:
        return "oral_liturgical"
    if name in narrative_or_mixed:
        return "narrative_or_mixed"
    return "unknown"


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #
def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    print(f"[{EXP}] loading corpora ("
          f"include_cross_lang=True, include_cross_tradition=True)...")
    CORPORA = raw_loader.load_all(
        include_extras=True,
        include_cross_lang=True,
        include_cross_tradition=True,
    )

    # Canonical 8-corpus universe in fixed order
    corpus_order = [
        "quran",
        "hebrew_tanakh",
        "greek_nt",
        "iliad_greek",
        "pali_dn",
        "pali_mn",
        "rigveda",
        "avestan_yasna",
    ]
    corpora_to_run = {c: CORPORA.get(c, []) for c in corpus_order}

    per_corpus_results: dict = {}
    rng = np.random.default_rng(SEED)

    for name in corpus_order:
        units = corpora_to_run[name]
        if name == "quran":
            stops = ARABIC_CONN
        else:
            all_v = (v for u in units for v in u.verses)
            stops = derive_stopwords(all_v, top_n=20)
        print(f"[{EXP}]   {name:18s}  n={len(units):4d} units  "
              f"stops={len(stops)}")
        per_corpus_results[name] = _run_corpus(name, units, stops, rng)

    # BH-pool across all corpora that produced a p-value
    valid_names = [
        n for n, r in per_corpus_results.items()
        if not r.get("skipped")
    ]
    p_list = [per_corpus_results[n]["p_one_sided"] for n in valid_names]
    bh = _one_sided_p_bh(p_list)
    bh["per_corpus"] = dict(zip(valid_names, bh["bh_adjusted"]))

    alpha = 0.05
    verdict_per = {
        n: ("passes_BH" if pv < alpha else "fails_BH")
        for n, pv in zip(valid_names, bh["bh_adjusted"])
    }

    # PRED-LC2.1: ≥ 2 of 4 new oral-liturgical corpora pass z < -2
    new_oral = ["pali_dn", "pali_mn", "rigveda", "avestan_yasna"]
    new_oral_passes = sum(
        1 for n in new_oral
        if not per_corpus_results[n].get("skipped")
        and per_corpus_results[n].get("z_path", 0) < -2.0
        and per_corpus_results[n].get("p_one_sided", 1.0) < 0.025
    )
    pred_lc2_1 = "PASS" if new_oral_passes >= 2 else "FAIL"

    # PRED-LC2.2: BH min p < 0.05
    pred_lc2_2 = "PASS" if bh["min_bh"] < alpha else "FAIL"

    # PRED-LC2.3: Iliad remains non-significant (BH p > 0.05)
    iliad_bh = (bh["per_corpus"].get("iliad_greek", 1.0)
                if not per_corpus_results["iliad_greek"].get("skipped")
                else 1.0)
    pred_lc2_3 = "PASS" if iliad_bh > alpha else "FAIL"

    overall_lc2 = (
        "SUPPORT" if (pred_lc2_1 == "PASS" and pred_lc2_2 == "PASS")
        else "PARTIAL_SUPPORT" if (pred_lc2_1 == "PASS" or pred_lc2_2 == "PASS")
        else "FALSIFIED"
    )

    # Group summary by tradition class
    z_by_class = {"oral_liturgical": [], "narrative_or_mixed": []}
    for n, r in per_corpus_results.items():
        if r.get("skipped"):
            continue
        z_by_class[r["tradition_class"]].append(r["z_path"])
    class_summary = {}
    for cls, zs in z_by_class.items():
        if zs:
            arr = np.array(zs)
            class_summary[cls] = {
                "n_corpora": int(len(zs)),
                "mean_z": float(arr.mean()),
                "median_z": float(np.median(arr)),
                "n_negative": int((arr < 0).sum()),
                "n_significantly_negative_z_lt_minus_2": int((arr < -2.0).sum()),
            }

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "seed": SEED,
        "n_perm": N_PERM,
        "metric": ("Euclidean path cost over within-corpus z-scored "
                   "5-D features_lang_agnostic (EL, VL_CV, CN, "
                   "H_cond_initials, T_lang)"),
        "corpus_order": corpus_order,
        "per_corpus": per_corpus_results,
        "BH_pooling": bh,
        "verdict_per_corpus_BH_alpha_0.05": verdict_per,
        "pre_registered_predictions": {
            "PRED_LC2_1_two_of_four_new_oral_z_lt_minus_2": pred_lc2_1,
            "PRED_LC2_2_BH_pool_min_p_lt_0.05": pred_lc2_2,
            "PRED_LC2_3_iliad_negative_control": pred_lc2_3,
            "n_new_oral_passes": new_oral_passes,
            "iliad_BH_adjusted_p": iliad_bh,
            "overall_LC2_verdict": overall_lc2,
        },
        "tradition_class_summary": class_summary,
        "interpretation": (
            "Each corpus's canonical chapter/sutta/sūkta/Yasna ordering "
            "is compared to 5000 uniform random permutations of that "
            "corpus's unit sequence, in its own 5-D language-agnostic "
            "feature space (z-scored within corpus). A negative z means "
            "the canonical order is shorter than random -- consistent "
            "with the 'path-minimality' claim. The pre-registered "
            "LC2 hypothesis predicts that ORAL-LITURGICAL corpora "
            "(Quran, Pāli Tipiṭaka, Rigveda Saṃhitā, Avestan Yasna) "
            "should all show negative z, while NARRATIVE-OR-MIXED "
            "corpora (Iliad in particular) should not. See the full "
            "PREREG.md for falsifiers."
        ),
        "extends": {
            "experiment": "exp35_R3_cross_scripture_redo",
            "relationship": ("strict superset: this experiment runs the "
                             "same 4 corpora plus 4 new ones, using "
                             "identical seed and metric. The 4-corpus "
                             "z values must reproduce exp35's locked "
                             "values to numerical precision."),
        },
        "provenance": {
            "corpora_loaded": corpus_order,
            "quran_stops": "ARABIC_CONN (14 items, paper §2.2)",
            "nonquran_stops": "derive_stopwords(verses, top_n=20)",
            "data_sources": {
                "pali_dn":       "github.com/suttacentral/bilara-data",
                "pali_mn":       "github.com/suttacentral/bilara-data",
                "rigveda":       "github.com/bhavykhatri/DharmicData",
                "avestan_yasna": "avesta.org/yasna/ (Geldner 1896)",
            },
        },
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # -------------------- console ---------------------------------------- #
    print(f"[{EXP}] wrote {outfile}")
    print(f"[{EXP}] --- per-corpus headline ---")
    print(f"   {'corpus':<18s}  {'class':<22s}  "
          f"{'n':>5s}  {'z_path':>8s}  {'p_1s':>8s}  BH")
    for n in corpus_order:
        r = per_corpus_results[n]
        if r.get("skipped"):
            print(f"   {n:<18s}  SKIPPED ({r.get('reason')})")
            continue
        print(f"   {n:<18s}  {r['tradition_class']:<22s}  "
              f"{r['n_units']:>5d}  {r['z_path']:>+8.3f}  "
              f"{r['p_one_sided']:>8.4f}  {verdict_per[n]}")
    print(f"[{EXP}] BH min adjusted p = {bh['min_bh']:.4f}")
    print(f"[{EXP}] PRED-LC2.1 (≥2 of 4 new corpora z<-2 at p<0.025): "
          f"{pred_lc2_1} ({new_oral_passes}/4)")
    print(f"[{EXP}] PRED-LC2.2 (BH min p<0.05): {pred_lc2_2}")
    print(f"[{EXP}] PRED-LC2.3 (Iliad BH p>0.05): {pred_lc2_3} "
          f"(iliad BH={iliad_bh:.4f})")
    print(f"[{EXP}] OVERALL LC2 verdict: {overall_lc2}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
