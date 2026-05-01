"""
exp35_R3_cross_scripture_redo/run.py
====================================
Honest redo of R3 (cross-scripture path minimality) now that the Hebrew
Tanakh (Westminster Leningrad Codex, tanakh_wlc.txt) and Greek NT
(OpenGNT v3.3, opengnt_v3_3.csv) are present on disk and the raw_loader
supports them via `include_cross_lang=True`.

The previous R3 write-up in PAPER.md §4.16 / QSF §16.2 quoted
    z_Quran = −8.74, z_GreekNT = −4.97, z_Tanakh = −5.02
inherited from the v10.3c `qsf_breakthrough_tests.py` pipeline that is
NOT in the current repo (the generating script was deleted during
repo cleanup, and the corpus_lock.json entries for tanakh/greek_nt
pointed to files that did not exist at the declared paths). This
experiment supersedes that claim with a fully reproducible measurement.

Protocol
    Corpora (all in a single canonical ordering):
        quran         - 114 surahs, Uthmanic order
        hebrew_tanakh - book-chapter units, WLC order
        greek_nt      - book-chapter units, canonical NT book order
        iliad_greek   - 24 books (negative control, narrative-chrono
                        ordering, not expected to optimise)
    Features (language-agnostic 5-D, features_5d_lang_agnostic):
        EL, VL_CV, CN, H_cond_initials, T_lang = H_cond_initials - H_el
        (T_lang is *not* interchangeable with T; cross-language use only.)
    Per-scripture pre-processing:
        * compute 5-D feature vector per unit (chapter/surah/book)
        * z-score the 5-D matrix within each scripture -- so absolute
          Euclidean path cost is directly comparable across languages
          with different scales
    Metric: Euclidean sum of adjacent-unit distances in a given order.
    Null:   RNG-shuffle of unit order, N_PERM = 5000 per scripture,
            seed = 42.
    Statistic:
        canon_cost, perm_mean, perm_std -> z = (canon - perm_mean)/perm_std
        empirical one-sided p = frac(perm_cost < canon_cost)
    Pooled: Benjamini-Hochberg FDR on the 4 one-sided p-values.

Reads only (integrity-checked):
    data/corpora/ar/quran_bare.txt       (via raw_loader)
    data/corpora/he/tanakh_wlc.txt       (via raw_loader)
    data/corpora/el/opengnt_v3_3.csv     (via raw_loader)
    data/corpora/el/iliad_perseus.xml    (via raw_loader)

Writes ONLY under results/experiments/exp35_R3_cross_scripture_redo/:
    exp35_R3_cross_scripture_redo.json
    self_check_<ts>.json
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

EXP = "exp35_R3_cross_scripture_redo"
SEED = 42
N_PERM = 5000


# --------------------------------------------------------------------------- #
# Language-agnostic per-unit 5-D feature vector                               #
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
    """Column-wise z-score with NaN-safe median imputation, matches the
    archival `jzscore` style used by the original T8 so pathcost is
    scale-invariant across scriptures."""
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
    """Benjamini-Hochberg pooling for 1-sided p-values across scriptures."""
    n = len(p_values)
    order = np.argsort(p_values)
    adj = np.empty(n, dtype=float)
    prev = 1.0
    for rank_idx, i in enumerate(reversed(order)):
        k = n - rank_idx  # rank counting from largest p
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
# Per-scripture driver                                                        #
# --------------------------------------------------------------------------- #
def _run_scripture(
    name: str, units, stops: set[str], rng: np.random.Generator,
) -> dict:
    """Compute features, canonical path, and permutation null."""
    t0 = time.time()
    X_raw = np.array(
        [_features_lang_agnostic(u.verses, stops) for u in units],
        dtype=float,
    )
    n = X_raw.shape[0]
    if n < 4:
        return {"n": n, "skipped": True, "reason": "n < 4"}

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
    p_one_sided = max(pct_below, 1.0 / (N_PERM + 1))  # conservative floor
    return {
        "n_units": n,
        "alphabet": (
            "arabic" if name == "quran" else
            "hebrew" if name == "hebrew_tanakh" else
            "greek"
        ),
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


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #
def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    print(f"[{EXP}] loading corpora (include_cross_lang=True)...")
    CORPORA = raw_loader.load_all(
        include_extras=True, include_cross_lang=True,
    )

    # Build per-scripture stop-word sets. Quran uses ARABIC_CONN (paper
    # §2.2); cross-language corpora use empirical top-20 stopwords so
    # CN is language-appropriate (matches src/features.py docstring).
    scriptures = {
        "quran":          CORPORA.get("quran", []),
        "hebrew_tanakh":  CORPORA.get("hebrew_tanakh", []),
        "greek_nt":       CORPORA.get("greek_nt", []),
        "iliad_greek":    CORPORA.get("iliad_greek", []),
    }

    per_scripture_results: dict = {}
    rng = np.random.default_rng(SEED)

    for name, units in scriptures.items():
        if name == "quran":
            stops = ARABIC_CONN
        else:
            all_v = (v for u in units for v in u.verses)
            stops = derive_stopwords(all_v, top_n=20)
        print(f"[{EXP}]   {name:18s}  n={len(units):4d} units  "
              f"stops={len(stops)}")
        per_scripture_results[name] = _run_scripture(name, units, stops, rng)

    # BH-pool across the 4 tests
    valid_names = [
        n for n, r in per_scripture_results.items()
        if not r.get("skipped")
    ]
    p_list = [per_scripture_results[n]["p_one_sided"] for n in valid_names]
    bh = _one_sided_p_bh(p_list)
    bh["per_scripture"] = dict(zip(valid_names, bh["bh_adjusted"]))

    # Verdict: among the 3 Abrahamic + Iliad, which scriptures pass BH
    # at alpha=0.05? Quran claim survives iff Quran passes.
    alpha = 0.05
    verdict_per = {
        n: ("passes_BH" if pv < alpha else "fails_BH")
        for n, pv in zip(valid_names, bh["bh_adjusted"])
    }
    quran_z = per_scripture_results["quran"].get("z_path")
    largest_abs_z_scripture = None
    largest_abs_z = 0.0
    for n, r in per_scripture_results.items():
        if r.get("z_path") is None:
            continue
        if abs(r["z_path"]) > largest_abs_z:
            largest_abs_z = abs(r["z_path"])
            largest_abs_z_scripture = n

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "seed": SEED,
        "n_perm": N_PERM,
        "metric": "Euclidean path cost over within-scripture z-scored "
                  "5-D features_lang_agnostic (EL, VL_CV, CN, "
                  "H_cond_initials, T_lang)",
        "per_scripture": per_scripture_results,
        "BH_pooling": bh,
        "verdict_per_scripture_BH_alpha_0.05": verdict_per,
        "quran_z_path": quran_z,
        "largest_abs_z_scripture": largest_abs_z_scripture,
        "largest_abs_z_value": largest_abs_z,
        "interpretation": (
            "Each scripture's canonical chapter/surah/book ordering is "
            "compared to 5000 uniform random permutations of that same "
            "scripture's unit sequence on its own 5-D language-agnostic "
            "feature space (z-scored within scripture). A negative z "
            "means the canonical order is shorter than random -- "
            "consistent with the historical 'path-minimality' claim. "
            "Honesty note: this supersedes the v10.3c numbers quoted in "
            "the pre-v7.2 PAPER.md §4.16 (z_Quran=-8.74, z_NT=-4.97, "
            "z_Tanakh=-5.02) which were not reproducible from the "
            "current repo because the generating script and the exact "
            "corpus-file paths were deleted during the v3->v5->v7 "
            "cleanup. The NEW numbers reported here are the authoritative "
            "v7.2 R3 measurements; they should replace the pre-v7.2 "
            "numbers verbatim."
        ),
        "supersedes": {
            "location": "docs/PAPER.md §4.16 (pre-v7.2) + docs/QSF_COMPLETE_REFERENCE.md §16.2",
            "old_claim": (
                "z_Quran=-8.74, z_GreekNT=-4.97, z_Tanakh=-5.02, "
                "BH-pooled p=0.002, N_PERM=5000"
            ),
            "reason_unreproducible": (
                "Original script (qsf_breakthrough_tests.py) and original "
                "corpus paths (data/corpora/he/tanakh.txt, "
                "data/corpora/el/greek_nt.txt) are absent from current repo."
            ),
        },
        "provenance": {
            "corpora_loaded": list(scriptures.keys()),
            "quran_stops": "ARABIC_CONN (14 items, paper §2.2)",
            "nonquran_stops": "derive_stopwords(verses, top_n=20)",
        },
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # -------------------- console ---------------------------------------- #
    print(f"[{EXP}] wrote {outfile}")
    print(f"[{EXP}] --- per-scripture headline ---")
    for n, r in per_scripture_results.items():
        if r.get("skipped"):
            print(f"   {n:18s}  SKIPPED ({r.get('reason')})")
            continue
        print(f"   {n:18s}  n={r['n_units']:4d}  "
              f"z={r['z_path']:+.3f}  "
              f"p={r['p_one_sided']:.4f}  "
              f"BH={verdict_per[n]}")
    print(f"[{EXP}] pooled min BH p = {bh['min_bh']:.4f}")
    print(f"[{EXP}] largest |z|: {largest_abs_z_scripture} "
          f"({largest_abs_z:+.3f})")
    print(f"[{EXP}] Quran z_path = {quran_z:+.3f}  "
          f"(previously claimed -8.74 in PAPER.md §4.16)")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
