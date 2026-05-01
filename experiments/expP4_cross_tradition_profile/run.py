"""
expP4_cross_tradition_profile/run.py
=====================================
Synthesises the four prior cross-tradition experiments into a single
per-corpus 3-D profile (R3, A2, Hurst) and asks whether the 8 corpora
occupy a coherent design space.

Sources:
  axis 1: R3 z_path  -> expP4_cross_tradition_R3
  axis 2: A2 R_prim  -> expP4_diacritic_capacity_cross_tradition (+ gap-fill)
  axis 3: Hurst z    -> expP4_quran_hurst_forensics (+ verse-level fallback)

For Iliad and Pali_DN we gap-fill A2 directly; for unit-level Hurst they
are skipped (n too small) and we substitute verse-level Hurst with its
own permutation null.

Reads only:
  results/experiments/expP4_cross_tradition_R3/expP4_cross_tradition_R3.json
  results/experiments/expP4_diacritic_capacity_cross_tradition/expP4_diacritic_capacity_cross_tradition.json
  results/experiments/expP4_quran_hurst_forensics/expP4_quran_hurst_forensics.json
  data/corpora/...     (only for gap-fills)

Writes ONLY under results/experiments/expP4_cross_tradition_profile/.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
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
from src.extended_tests4 import _hurst_rs  # noqa: E402

# Pair extractors for gap-fills
from experiments.expA2_diacritic_capacity_universal.run import (  # noqa: E402
    _conditional_entropy_bits,
    greek_pairs,
)
from experiments.expP4_diacritic_capacity_cross_tradition.run import (  # noqa: E402
    _latin_iast_pairs,
)

EXP = "expP4_cross_tradition_profile"
SEED = 42
N_PERM = 5000


# --------------------------------------------------------------------------- #
def _safe_h(seq) -> float:
    h = _hurst_rs(np.asarray(seq, dtype=float))
    return float(h) if not np.isnan(h) else float("nan")


def _verse_hurst_z(units, seed: int) -> tuple[float, float, float, float]:
    """Compute verse-level Hurst on word-count series + 5000 permutation
    null. Returns (h_canon, perm_mean, perm_std, z)."""
    if not units:
        return (float("nan"),) * 4
    rc_words = [len(v.split()) for u in units for v in u.verses]
    arr = np.array(rc_words, dtype=float)
    n = len(arr)
    if n < 32:
        return (float("nan"),) * 4
    h_canon = _safe_h(arr)
    if np.isnan(h_canon):
        return (float("nan"),) * 4
    rng = np.random.default_rng(seed)
    perms = []
    for _ in range(N_PERM):
        h = _safe_h(arr[rng.permutation(n)])
        if not np.isnan(h):
            perms.append(h)
    if len(perms) < 100:
        return (h_canon, float("nan"), float("nan"), float("nan"))
    arr_p = np.array(perms, dtype=float)
    perm_mean = float(arr_p.mean())
    perm_std = float(arr_p.std())
    z = (h_canon - perm_mean) / (perm_std if perm_std > 0 else 1.0)
    return float(h_canon), perm_mean, perm_std, float(z)


# --------------------------------------------------------------------------- #
def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    # ----- Load cross-tradition results -----
    r3_json = json.loads((_ROOT / "results" / "experiments"
                          / "expP4_cross_tradition_R3"
                          / "expP4_cross_tradition_R3.json"
                          ).read_text("utf-8"))
    a2_json = json.loads((_ROOT / "results" / "experiments"
                          / "expP4_diacritic_capacity_cross_tradition"
                          / "expP4_diacritic_capacity_cross_tradition.json"
                          ).read_text("utf-8"))
    hf_json = json.loads((_ROOT / "results" / "experiments"
                          / "expP4_quran_hurst_forensics"
                          / "expP4_quran_hurst_forensics.json"
                          ).read_text("utf-8"))

    canonical_order = [
        "quran", "hebrew_tanakh", "greek_nt", "iliad_greek",
        "pali_dn", "pali_mn", "rigveda", "avestan_yasna",
    ]
    tradition_class = {
        "quran":         "oral_liturgical",
        "hebrew_tanakh": "narrative_or_mixed",
        "greek_nt":      "narrative_or_mixed",
        "iliad_greek":   "narrative_or_mixed",
        "pali_dn":       "oral_liturgical",
        "pali_mn":       "oral_liturgical",
        "rigveda":       "oral_liturgical",
        "avestan_yasna": "oral_liturgical",
    }
    # mapping from our canonical_order keys to keys in the source experiments
    a2_key = {
        "quran":           "quran_arabic",
        "hebrew_tanakh":   "tanakh_hebrew",
        "greek_nt":        "nt_greek",
        # iliad_greek and pali_dn handled below as gap-fills
        "rigveda":         "rigveda_devanagari",
        "avestan_yasna":   "avestan_geldner",
    }

    print(f"[{EXP}] gathering profile axes for 8 corpora...")

    # ----- Gap-fill: Iliad A2 (Greek polytonic) -----
    iliad_path = _ROOT / "data" / "corpora" / "el" / "iliad_perseus.xml"
    pali_dn_units = []
    if iliad_path.exists():
        # The Iliad xml format isn't the same as opengnt_v3_3.csv. Easiest
        # path: walk the Iliad as plain text, extract Greek vowels with NFD
        # combining marks (mirrors the Greek-NT pair extractor format).
        from src.raw_loader import load_iliad
        iliad_units = load_iliad()
        # Build text from the loaded units (this preserves the polytonic
        # Greek if present in the source)
        iliad_text = "\n".join(v for u in iliad_units for v in u.verses)
        # Use a Greek-vowel pair extractor compatible with what greek_pairs
        # does internally on tokens. We adapt by writing a similar walker.
        import unicodedata
        from collections import Counter as _C
        _GREEK_VOWELS = set("αεηιουωΑΕΗΙΟΥΩ")
        nfd = unicodedata.normalize("NFD", iliad_text)
        chars = list(nfd)
        ip: _C = _C()
        i = 0
        nch = len(chars)
        while i < nch:
            c = chars[i]
            if c not in _GREEK_VOWELS:
                i += 1
                continue
            base = c.lower()
            j = i + 1
            diacs: list[str] = []
            while j < nch and unicodedata.category(chars[j]) == "Mn":
                diacs.append(chars[j])
                j += 1
            ip[(base, "".join(diacs) or "<none>")] += 1
            i = j
        iliad_a2 = _conditional_entropy_bits(ip)
    else:
        iliad_a2 = {"ratio_R_primitives": float("nan"), "n_pairs": 0}

    # ----- Gap-fill: Pali_DN A2 (Latin-IAST) -----
    CORPORA = raw_loader.load_all(
        include_extras=False, include_cross_lang=True,
        include_cross_tradition=True,
    )
    pali_dn_units = CORPORA.get("pali_dn", [])
    pali_dn_text = "\n".join(v for u in pali_dn_units for v in u.verses)
    pali_dn_a2 = _conditional_entropy_bits(_latin_iast_pairs(pali_dn_text))

    # ----- Pull axis-1 (R3 z_path) -----
    r3 = {}
    for c in canonical_order:
        rec = r3_json["per_corpus"].get(c, {})
        r3[c] = float(rec.get("z_path", float("nan")))

    # ----- Pull axis-2 (A2 R_primitives) -----
    a2 = {}
    for c in canonical_order:
        if c in a2_key:
            rec = a2_json["results_per_corpus"].get(a2_key[c], {})
            a2[c] = float(rec.get("ratio_R_primitives", float("nan")))
        elif c == "iliad_greek":
            a2[c] = float(iliad_a2.get("ratio_R_primitives", float("nan")))
        elif c == "pali_dn":
            a2[c] = float(pali_dn_a2.get("ratio_R_primitives", float("nan")))
        elif c == "pali_mn":
            # The original experiment had a combined pali_iast = DN+MN.
            # We compute MN-only here for consistency with the canonical
            # 8-corpus split.
            mn_units = CORPORA.get("pali_mn", [])
            mn_text = "\n".join(v for u in mn_units for v in u.verses)
            mn_a2 = _conditional_entropy_bits(_latin_iast_pairs(mn_text))
            a2[c] = float(mn_a2.get("ratio_R_primitives", float("nan")))
        else:
            a2[c] = float("nan")

    # ----- Pull axis-3 (Hurst z) -----
    hurst_z = {}
    hurst_h_canon = {}
    for c in canonical_order:
        rec = hf_json["results_per_corpus"].get(c, {})
        if rec.get("skipped"):
            # Use verse-level Hurst as fallback (n_verse always >= 1000)
            units = CORPORA.get(c, [])
            h_canon, _, _, z = _verse_hurst_z(
                units, seed=SEED + canonical_order.index(c)
            )
            hurst_z[c] = z
            hurst_h_canon[c] = h_canon
        else:
            hurst_z[c] = float(rec.get("z_canon_vs_null", float("nan")))
            hurst_h_canon[c] = float(rec.get("H_canon", float("nan")))

    # ----- Build profile matrix (8 x 3) -----
    # Sign convention: more "religious-canon-like" -> more positive on every
    # axis. profile_R3 = -R3_z (negative z is path-minimal),
    # profile_A2 = +A2_R, profile_H = +Hurst_z.
    raw_rows = []
    for c in canonical_order:
        raw_rows.append([
            -r3[c],         # profile_R3: more positive = more path-minimal
            a2[c],          # profile_A2
            hurst_z[c],     # profile_Hurst
        ])
    raw_mat = np.array(raw_rows, dtype=float)

    # Z-score each axis across the 8 corpora (handle NaNs by mean-imputing
    # to the column mean of valid values)
    standardised = raw_mat.copy()
    col_stats = []
    for j in range(3):
        col = raw_mat[:, j]
        valid = ~np.isnan(col)
        if not valid.any():
            col_stats.append({"mean": 0.0, "std": 1.0, "n_valid": 0})
            continue
        mu = float(col[valid].mean())
        sd = float(col[valid].std())
        if sd == 0:
            sd = 1.0
        # Impute NaNs to the column mean before z-scoring
        col_imputed = col.copy()
        col_imputed[~valid] = mu
        standardised[:, j] = (col_imputed - mu) / sd
        col_stats.append({
            "mean": mu, "std": sd, "n_valid": int(valid.sum()),
            "n_imputed": int((~valid).sum()),
        })

    # ----- Pairwise distances + cluster analysis -----
    n_corp = len(canonical_order)
    D = np.zeros((n_corp, n_corp), dtype=float)
    for i in range(n_corp):
        for j in range(n_corp):
            D[i, j] = float(np.linalg.norm(standardised[i] - standardised[j]))

    oral_idx = [k for k, c in enumerate(canonical_order)
                if tradition_class[c] == "oral_liturgical"]
    narr_idx = [k for k, c in enumerate(canonical_order)
                if tradition_class[c] == "narrative_or_mixed"]

    # mean within-class distances (excluding self-distances which are 0)
    def _mean_pairwise(D, idx):
        if len(idx) < 2:
            return float("nan")
        vals = []
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                vals.append(D[idx[a], idx[b]])
        return float(np.mean(vals))

    def _mean_between(D, idx_a, idx_b):
        if not idx_a or not idx_b:
            return float("nan")
        vals = []
        for a in idx_a:
            for b in idx_b:
                vals.append(D[a, b])
        return float(np.mean(vals))

    mean_oral_oral = _mean_pairwise(D, oral_idx)
    mean_narr_narr = _mean_pairwise(D, narr_idx)
    mean_oral_narr = _mean_between(D, oral_idx, narr_idx)

    # Isolation index: each corpus's mean distance to all others
    isolation = {
        canonical_order[i]: float(np.mean(D[i, [k for k in range(n_corp) if k != i]]))
        for i in range(n_corp)
    }

    # Profile norm from origin (centroid is at 0 after z-score, so this is
    # just |row|)
    profile_norm = {
        canonical_order[i]: float(np.linalg.norm(standardised[i]))
        for i in range(n_corp)
    }

    # PCA: SVD of the standardised matrix
    U, S, Vt = np.linalg.svd(standardised, full_matrices=False)
    var_explained = (S ** 2) / (S ** 2).sum()
    pc1_loadings = Vt[0].tolist()  # the loading vector of PC1
    pc1_scores = (standardised @ Vt[0]).tolist()

    # ----- Pre-registered outcomes -----
    pred_pro_1 = "PASS" if (mean_oral_oral < mean_oral_narr) else "FAIL"

    # PRED-PRO-2: Iliad has the largest isolation
    iliad_iso = isolation["iliad_greek"]
    pred_pro_2 = "PASS" if all(
        iliad_iso >= isolation[c] for c in canonical_order
    ) else "FAIL"
    most_isolated = max(isolation, key=isolation.get)

    # PRED-PRO-3: Rigveda has the longest profile norm
    rv_norm = profile_norm["rigveda"]
    pred_pro_3 = "PASS" if all(
        rv_norm >= profile_norm[c] for c in canonical_order
    ) else "FAIL"
    longest_norm = max(profile_norm, key=profile_norm.get)

    # PRED-PRO-4: R3 is the highest-loading axis on PC1 (in absolute value)
    abs_loadings = [abs(x) for x in pc1_loadings]
    top_axis_idx = int(np.argmax(abs_loadings))
    axis_names = ["profile_R3", "profile_A2", "profile_Hurst"]
    pred_pro_4 = "PASS" if top_axis_idx == 0 else "FAIL"

    overall = (
        "STRONG_SUPPORT" if (pred_pro_1 == "PASS" and pred_pro_2 == "PASS"
                             and pred_pro_3 == "PASS")
        else "PARTIAL_SUPPORT" if (pred_pro_1 == "PASS" or pred_pro_2 == "PASS"
                                   or pred_pro_3 == "PASS")
        else "NO_SUPPORT"
    )

    # ----- Pack the report -----
    profile_per_corpus = {}
    for i, c in enumerate(canonical_order):
        profile_per_corpus[c] = {
            "tradition_class": tradition_class[c],
            "raw_R3_z_path": r3[c],
            "raw_A2_R_primitives": a2[c],
            "raw_Hurst_z": hurst_z[c],
            "raw_Hurst_H_canon": hurst_h_canon[c],
            "profile_R3_standardised":     float(standardised[i, 0]),
            "profile_A2_standardised":     float(standardised[i, 1]),
            "profile_Hurst_standardised":  float(standardised[i, 2]),
            "profile_norm":      profile_norm[c],
            "isolation_index":   isolation[c],
            "pc1_score":         float(pc1_scores[i]),
        }

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "title": ("Multi-axis profile vector synthesis of the four prior "
                  "cross-tradition experiments. 8 corpora x 3 axes "
                  "(R3 path-minimality, A2 diacritic capacity, "
                  "unit-level Hurst z-vs-permutation-null)."),
        "axes": {
            "axis_1_R3":    "negated R3 z_path (more positive = more path-minimal)",
            "axis_2_A2":    "A2 R_primitives (more positive = more diacritic-saturated)",
            "axis_3_Hurst": "Hurst z vs empirical permutation null (more positive = more long-range memory)",
        },
        "n_corpora": n_corp,
        "canonical_order": canonical_order,
        "tradition_class": tradition_class,
        "profile_per_corpus": profile_per_corpus,
        "column_stats": dict(zip(axis_names, col_stats)),
        "pairwise_distance_matrix": D.tolist(),
        "cluster_analysis": {
            "mean_within_oral_liturgical": mean_oral_oral,
            "mean_within_narrative_or_mixed": mean_narr_narr,
            "mean_between_classes": mean_oral_narr,
            "diff_between_minus_within_oral": mean_oral_narr - mean_oral_oral,
        },
        "PCA": {
            "variance_explained_per_component": [float(v) for v in var_explained],
            "pc1_loadings_per_axis": dict(zip(axis_names, pc1_loadings)),
            "pc1_dominant_axis": axis_names[top_axis_idx],
        },
        "pre_registered_outcomes": {
            "PRED_PRO_1_oral_cluster_tighter": pred_pro_1,
            "PRED_PRO_1_mean_oral_oral":  mean_oral_oral,
            "PRED_PRO_1_mean_oral_narr":  mean_oral_narr,
            "PRED_PRO_2_iliad_most_isolated": pred_pro_2,
            "PRED_PRO_2_actual_most_isolated_corpus": most_isolated,
            "PRED_PRO_3_rigveda_longest_norm": pred_pro_3,
            "PRED_PRO_3_actual_longest_norm_corpus": longest_norm,
            "PRED_PRO_4_R3_dominates_PC1": pred_pro_4,
            "PRED_PRO_4_actual_dominant_axis": axis_names[top_axis_idx],
            "overall_verdict": overall,
        },
        "interpretation": [
            "If PRED-PRO-1 PASSES, the 4 oral-liturgical corpora form a "
            "coherent cluster in the 3-D profile space, distinct from "
            "the narrative_or_mixed class. This is the multi-axis "
            "version of the LC2 hypothesis.",
            "If PRED-PRO-2 PASSES, the Iliad is uniquely isolated -- "
            "consistent with it being the only NON-religious-text "
            "corpus in our sample.",
            "If PRED-PRO-3 PASSES, the Rigveda's whole-corpus extremity "
            "(documented in expP4_rigveda_deepdive) generalises beyond "
            "any single axis -- it is the corner of the design space.",
            "If PRED-PRO-4 PASSES, R3 path-minimality is the single best "
            "summary axis of the cross-tradition design space, "
            "consistent with R3 being the cleanest discriminator between "
            "oral-liturgical and narrative-or-mixed corpora.",
        ],
        "extends": {
            "experiment_R3":    "expP4_cross_tradition_R3",
            "experiment_A2":    "expP4_diacritic_capacity_cross_tradition",
            "experiment_Hurst": "expP4_quran_hurst_forensics",
            "relationship": ("synthesises the three prior experiments "
                             "into a unified profile space; gap-fills "
                             "Iliad A2, Pali_DN A2, and verse-level "
                             "Hurst for n<10 corpora."),
        },
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ---------------- console summary ----------------
    print()
    print(f"[{EXP}] -- per-corpus 3-axis profile (raw + standardised) --")
    print(f"   {'corpus':<18s}  {'class':<22s}  "
          f"{'R3z':>8s}  {'A2R':>6s}  {'Hz':>7s}  "
          f"{'P-R3':>7s}  {'P-A2':>7s}  {'P-Hz':>7s}  "
          f"{'norm':>6s}  {'iso':>6s}")
    for i, c in enumerate(canonical_order):
        p = profile_per_corpus[c]
        def _f(x, w=7, prec=3):
            return ("nan" if (x is None or (isinstance(x, float) and np.isnan(x)))
                    else f"{x:+.{prec}f}").rjust(w)
        print(f"   {c:<18s}  {tradition_class[c]:<22s}  "
              f"{_f(p['raw_R3_z_path'], 8, 2)}  "
              f"{_f(p['raw_A2_R_primitives'], 6, 3)}  "
              f"{_f(p['raw_Hurst_z'], 7, 2)}  "
              f"{_f(p['profile_R3_standardised'], 7, 2)}  "
              f"{_f(p['profile_A2_standardised'], 7, 2)}  "
              f"{_f(p['profile_Hurst_standardised'], 7, 2)}  "
              f"{p['profile_norm']:>6.2f}  "
              f"{p['isolation_index']:>6.2f}")
    print()
    print(f"[{EXP}] -- cluster analysis --")
    print(f"[{EXP}]   mean within oral_liturgical    = {mean_oral_oral:.3f}")
    print(f"[{EXP}]   mean within narrative_or_mixed = {mean_narr_narr:.3f}")
    print(f"[{EXP}]   mean between classes           = {mean_oral_narr:.3f}")
    print(f"[{EXP}]   diff (between - within oral)   = "
          f"{mean_oral_narr - mean_oral_oral:+.3f}")
    print()
    print(f"[{EXP}] -- PCA --")
    for k, ax in enumerate(axis_names):
        print(f"[{EXP}]   PC{k+1}  variance explained = {var_explained[k]:.4f}")
    print(f"[{EXP}]   PC1 loadings:")
    for ax, ld in zip(axis_names, pc1_loadings):
        print(f"[{EXP}]     {ax:<20s}  loading = {ld:+.4f}")
    print()
    print(f"[{EXP}] -- pre-registered outcomes --")
    print(f"[{EXP}]   PRED-PRO-1 (oral cluster tighter):  {pred_pro_1}")
    print(f"[{EXP}]   PRED-PRO-2 (Iliad most isolated):   {pred_pro_2}  "
          f"(actual: {most_isolated})")
    print(f"[{EXP}]   PRED-PRO-3 (Rigveda longest norm):  {pred_pro_3}  "
          f"(actual: {longest_norm})")
    print(f"[{EXP}]   PRED-PRO-4 (R3 dominates PC1):      {pred_pro_4}  "
          f"(actual: {axis_names[top_axis_idx]})")
    print(f"[{EXP}]   OVERALL: {overall}")
    print(f"[{EXP}] wrote {outfile}")

    self_check_end(pre, exp_name=EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
