"""scripts/_phi_master_xtrad_sizing.py
==========================================
Pre-PREREG sizing diagnostic for exp110 (3-term Φ_master cross-tradition).

Computes the 3-term portable Φ_3 = MI(EL) + MI(VL_CV) + MI(p_max) per corpus
on the 6-corpus real-verse-only pool. Reports observed values so the PREREG
can lock thresholds tighter than them.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._phi_universal_xtrad_sizing import (  # noqa: E402
    _load_quran,
    _load_arabic_peers,
    _load_hebrew_tanakh,
    _load_greek_nt,
    _load_pali,
    _load_avestan,
    _features_universal,
)


def _discretise(x: np.ndarray, n_bins: int = 5,
                edges: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Equal-width binning over the FULL JOINT range. Returns bin index per
    sample and the bin edges used (for reproducibility)."""
    if edges is None:
        lo, hi = float(np.min(x)), float(np.max(x))
        if hi == lo:
            edges = np.array([lo, hi + 1e-9])
        else:
            edges = np.linspace(lo, hi, n_bins + 1)
    idx = np.clip(np.digitize(x, edges[1:-1], right=False), 0, n_bins - 1)
    return idx, edges


def _mi_binary(F_idx: np.ndarray, Y: np.ndarray, n_bins_F: int = 5) -> float:
    """Discrete mutual information I(F; Y) where F is multi-bin and Y is binary.
    Returns MI in nats. Plug-in (no smoothing)."""
    n = len(F_idx)
    pY = np.bincount(Y, minlength=2) / n
    pF = np.bincount(F_idx, minlength=n_bins_F) / n
    pFY = np.zeros((n_bins_F, 2))
    for i in range(n):
        pFY[F_idx[i], Y[i]] += 1.0
    pFY /= n
    mi = 0.0
    for i in range(n_bins_F):
        for j in range(2):
            if pFY[i, j] <= 0 or pF[i] <= 0 or pY[j] <= 0:
                continue
            mi += pFY[i, j] * np.log(pFY[i, j] / (pF[i] * pY[j]))
    return float(max(mi, 0.0))


def main() -> dict:
    print("# === sizing for exp110_phi_master_xtrad ===\n")
    print("# 1. loading corpora ...")
    quran = _load_quran()
    arabic = _load_arabic_peers()
    arabic_bible = arabic.get("arabic_bible", [])
    hebrew = _load_hebrew_tanakh()
    greek = _load_greek_nt()
    pali = _load_pali()
    avestan = _load_avestan()
    CORPORA = ["quran", "arabic_bible", "hebrew_tanakh", "greek_nt",
               "pali", "avestan_yasna"]
    units_by_corpus = {
        "quran": quran,
        "arabic_bible": arabic_bible,
        "hebrew_tanakh": hebrew,
        "greek_nt": greek,
        "pali": pali,
        "avestan_yasna": avestan,
    }
    for c in CORPORA:
        print(f"#   {c}: {len(units_by_corpus[c])} units")

    print("\n# 2. extracting features ...")
    feats = {c: [] for c in CORPORA}
    for c in CORPORA:
        for u in units_by_corpus[c]:
            try:
                feats[c].append(_features_universal(u))
            except Exception:
                pass
        print(f"#   {c}: {len(feats[c])} units passed")

    # Stack all features into (n_total, 3) matrix
    EL = []  # using p_max as EL per PREREG §3.1
    VL = []
    PM = []
    origin = []
    for c in CORPORA:
        for f in feats[c]:
            EL.append(f["p_max"])
            VL.append(f["VL_CV"])
            PM.append(f["p_max"])
            origin.append(c)
    EL = np.array(EL); VL = np.array(VL); PM = np.array(PM)
    origin = np.array(origin)
    n_total = len(origin)
    print(f"\n# 3. discretising over n_total = {n_total} units (5 bins, equal width)")

    EL_idx, EL_edges = _discretise(EL, 5)
    VL_idx, VL_edges = _discretise(VL, 5)
    PM_idx, PM_edges = _discretise(PM, 5)
    print(f"#   EL bin edges:    {EL_edges.tolist()}")
    print(f"#   VL_CV bin edges: {VL_edges.tolist()}")
    print(f"#   p_max bin edges: {PM_edges.tolist()}")

    print("\n# 4. computing 3-term Phi_3 per corpus")
    print(f"# {'corpus':<14s}  {'n':>5s}  {'MI_EL':>8s}  {'MI_VL':>8s}  {'MI_pmax':>8s}  {'Phi_3':>8s}")
    phi3 = {}
    for c in CORPORA:
        Y = (origin == c).astype(int)
        mi_el = _mi_binary(EL_idx, Y, 5)
        mi_vl = _mi_binary(VL_idx, Y, 5)
        mi_pm = _mi_binary(PM_idx, Y, 5)
        s = mi_el + mi_vl + mi_pm
        phi3[c] = {"mi_el": mi_el, "mi_vl_cv": mi_vl, "mi_p_max": mi_pm,
                   "phi_3_nats": s, "n_units": int(np.sum(Y))}
        print(f"# {c:<14s}  {int(np.sum(Y)):>5d}  "
              f"{mi_el:>8.4f}  {mi_vl:>8.4f}  {mi_pm:>8.4f}  {s:>8.4f}")

    qphi = phi3["quran"]["phi_3_nats"]
    others = [(c, phi3[c]["phi_3_nats"]) for c in CORPORA if c != "quran"]
    nh_corpus, nh_val = max(others, key=lambda t: t[1])
    print(f"\n# Quran Phi_3 = {qphi:.4f} nats; next-highest = {nh_corpus} = {nh_val:.4f}")
    if nh_val > 0:
        ratio = qphi / nh_val
        print(f"# Quran/next ratio = {ratio:.4f}")
    else:
        ratio = float("inf")
        print(f"# Quran/next ratio = inf (next is zero)")

    out = {
        "audit": "phi_master_xtrad_sizing",
        "corpora": CORPORA,
        "n_units_per_corpus": {c: len(feats[c]) for c in CORPORA},
        "n_total": int(n_total),
        "bin_edges": {
            "EL": EL_edges.tolist(),
            "VL_CV": VL_edges.tolist(),
            "p_max": PM_edges.tolist(),
        },
        "phi_3_per_corpus": phi3,
        "quran_phi_3": qphi,
        "next_highest_corpus": nh_corpus,
        "next_highest_phi_3": nh_val,
        "quran_to_next_ratio": ratio,
    }
    out_path = ROOT / "results" / "auxiliary" / "_phi_master_xtrad_sizing.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"\n# receipt: {out_path}")
    return out


if __name__ == "__main__":
    main()
