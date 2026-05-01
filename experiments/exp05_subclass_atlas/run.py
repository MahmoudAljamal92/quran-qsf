"""
exp05_subclass_atlas/run.py
===========================
Sub-class atlas — generalises exp03 Q2 (oath-opening sūrahs) to multiple
pre-registered Qur'ānic sūra classes. Tests whether the 5-D features
recover each class as a coherent cluster WITHOUT any class supervision.

Sub-classes (pre-registered from classical Qur'ānic scholarship, fixed
before any cluster analysis):

  A) oath-opening  (وَ + noun, 15 sūrahs)
  B) muqaṭṭaʿāt     (disjoined letters opener, 29 sūrahs — alif-lām-mīm etc.)
  C) hāmīm          (ḥawāmīm, the seven حم-openers)
  D) story-dominant (narrative/قصص surahs with prophetic cycles, curated list)
  E) short-mufaṣṣal (sūrahs 93..114 — the short-late Meccan cluster)

For each class K we compute:
  - centroid μ_K in the 5-D space
  - local-covariance Mahalanobis distance of every member to μ_K
  - silhouette-like separation: median distance K->K vs K->not-K
  - permutation test: shuffle class labels 1000x, does the real within-
    class tightness beat the shuffled?

Reads (read-only):
  - phase_06_phi_m.pkl     (CORPORA, μ_ctrl, S_inv, X_CTRL_POOL)

Writes ONLY under results/experiments/exp05_subclass_atlas/:
  - exp05_subclass_atlas.json
  - fig_subclass_scatter.png         (first-two PCA projection)
  - fig_subclass_mahalanobis.png     (per-class distance distributions)
  - self_check_<ts>.json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase, safe_output_dir, self_check_begin, self_check_end,
)
from src import features as ft  # noqa: E402

EXP = "exp05_subclass_atlas"

# ---------------------------------------------------------------------------
# Pre-registered sub-classes (locked from classical Qur'ānic scholarship,
# not tuned to data).
# ---------------------------------------------------------------------------

# (A) Oath-opening (وَ + noun as first content word in verse 1)
CLASS_OATH = {37, 51, 52, 53, 77, 79, 85, 86, 89, 91, 92, 93, 95, 100, 103}

# (B) Muqaṭṭaʿāt — sūrahs opening with disjoined letters (29 sūrahs).
CLASS_MUQATTAAT = {
    2, 3, 7, 10, 11, 12, 13, 14, 15, 19, 20, 26, 27, 28, 29, 30, 31, 32,
    36, 38, 40, 41, 42, 43, 44, 45, 46, 50, 68,
}

# (C) Hāmīm (ḥawāmīm) — the 7 حم-opening sūrahs
CLASS_HAMIM = {40, 41, 42, 43, 44, 45, 46}

# (D) Story-dominant — sūrahs with extended narrative cycles (curated
#     from canonical tafsīr: Yūsuf, al-Anbiyāʾ, al-Qaṣaṣ, Maryam, Ṣād,
#     etc.). Fixed list.
CLASS_STORY = {7, 11, 12, 18, 19, 20, 21, 27, 28, 37, 38, 71}

# (E) Short-mufaṣṣal — the short Meccan tail (sūrahs 93..114, 22 sūrahs)
CLASS_SHORT_MUFASSAL = set(range(93, 115))

SUBCLASSES = {
    "oath_opening":     CLASS_OATH,
    "muqattaat":        CLASS_MUQATTAAT,
    "hamim":            CLASS_HAMIM,
    "story_dominant":   CLASS_STORY,
    "short_mufassal":   CLASS_SHORT_MUFASSAL,
}


def _surah_num(label: str) -> int | None:
    try:
        return int(str(label).split(":")[-1])
    except Exception:
        return None


def _mahalanobis_many(X: np.ndarray, mu: np.ndarray, S_inv: np.ndarray) -> np.ndarray:
    d = X - mu[None, :]
    return np.sqrt(np.maximum(np.einsum("ij,jk,ik->i", d, S_inv, d), 0.0))


def _class_tightness(X_class: np.ndarray, X_rest: np.ndarray,
                     ridge: float = 1e-6) -> tuple[float, float, np.ndarray, np.ndarray]:
    """Return (median_in, median_out, d_in, d_out) using class-local
    Mahalanobis metric (S_inv from X_class itself)."""
    if len(X_class) < 2:
        return math.nan, math.nan, np.array([]), np.array([])
    mu = X_class.mean(axis=0)
    S = np.cov(X_class, rowvar=False, ddof=1) + ridge * np.eye(X_class.shape[1])
    S_inv = np.linalg.pinv(S)
    d_in = _mahalanobis_many(X_class, mu, S_inv)
    d_out = _mahalanobis_many(X_rest, mu, S_inv)
    return float(np.median(d_in)), float(np.median(d_out)), d_in, d_out


def _perm_test(X_all: np.ndarray, mask: np.ndarray, n_perm: int = 1000,
               seed: int = 42) -> dict:
    """Permutation test for within-class tightness: shuffle class
    membership n_perm times, compute median d_in each time, return the
    fraction of shuffles with median d_in <= observed."""
    rng = np.random.default_rng(seed)
    k = int(mask.sum())
    if k < 2 or k > len(X_all) - 2:
        return {"n_perm": 0, "observed_median_d_in": math.nan,
                "null_median": math.nan, "p": math.nan}

    X_class = X_all[mask]
    X_rest = X_all[~mask]
    med_obs, _, _, _ = _class_tightness(X_class, X_rest)

    null_vals = np.empty(n_perm)
    idx = np.arange(len(X_all))
    for i in range(n_perm):
        rng.shuffle(idx)
        m = np.zeros(len(X_all), dtype=bool)
        m[idx[:k]] = True
        med_i, _, _, _ = _class_tightness(X_all[m], X_all[~m])
        null_vals[i] = med_i

    # p = fraction of shuffles as tight or tighter than observed
    p = float((np.sum(null_vals <= med_obs) + 1) / (n_perm + 1))
    return {
        "n_perm": n_perm,
        "observed_median_d_in": med_obs,
        "null_median": float(np.median(null_vals)),
        "null_5pct": float(np.percentile(null_vals, 5)),
        "null_95pct": float(np.percentile(null_vals, 95)),
        "p": p,
    }


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    CORPORA = state["CORPORA"]
    mu_ctrl = np.asarray(state["mu"])
    S_inv_ctrl = np.asarray(state["S_inv"])
    feat_cols = list(state["FEAT_COLS"])

    # Extract 5-D for all 114 Quran surahs
    quran_units = CORPORA["quran"]
    X, labels, nums = [], [], []
    for u in quran_units:
        X.append(ft.features_5d(u.verses))
        labels.append(u.label)
        nums.append(_surah_num(u.label))
    X = np.asarray(X, dtype=float)
    labels = np.asarray(labels)
    nums = np.asarray(nums)

    # Per-class analyses
    class_results = {}
    for name, members in SUBCLASSES.items():
        mask = np.isin(nums, list(members))
        found = nums[mask].tolist()
        X_class = X[mask]
        X_rest = X[~mask]
        med_in, med_out, d_in, d_out = _class_tightness(X_class, X_rest)
        ptest = _perm_test(X, mask, n_perm=1000, seed=42)

        class_results[name] = {
            "expected_members": sorted(members),
            "found_members": sorted(found),
            "n_expected": len(members),
            "n_found": int(len(found)),
            "centroid_5d": dict(zip(feat_cols, X_class.mean(axis=0).tolist())) if len(X_class) else None,
            "median_d_in_local_maha": med_in,
            "median_d_out_local_maha": med_out,
            "separation_ratio": (med_out / med_in) if med_in and med_in > 0 else None,
            "perm_test": ptest,
        }

    # ---------- Plots ----------
    # PCA projection (centered on full Quran)
    Xc = X - X.mean(axis=0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    PC = Xc @ Vt.T[:, :2]
    var_ratio = (S ** 2) / (S ** 2).sum()

    # Assign a colour per class; membership is mutually non-exclusive, so
    # we prioritise: hamim > muqattaat > oath > story > short_mufassal > other.
    colour = np.full(len(X), "other", dtype=object)
    for name in ["short_mufassal", "story_dominant", "oath_opening",
                 "muqattaat", "hamim"]:
        members = SUBCLASSES[name]
        mask = np.isin(nums, list(members))
        colour[mask] = name

    palette = {
        "hamim":            "#d62728",  # red
        "muqattaat":        "#1f77b4",  # blue
        "oath_opening":     "#2ca02c",  # green
        "story_dominant":   "#ff7f0e",  # orange
        "short_mufassal":   "#9467bd",  # purple
        "other":            "#bbbbbb",  # grey
    }

    fig, ax = plt.subplots(figsize=(8, 6))
    for name, col in palette.items():
        mask = (colour == name)
        ax.scatter(PC[mask, 0], PC[mask, 1],
                   color=col, edgecolor="black", linewidth=0.3,
                   s=50 if name != "other" else 15,
                   alpha=0.85 if name != "other" else 0.5,
                   label=f"{name} (n={int(mask.sum())})")
    ax.set_xlabel(f"PC1 ({var_ratio[0]*100:.1f}% var)")
    ax.set_ylabel(f"PC2 ({var_ratio[1]*100:.1f}% var)")
    ax.set_title("Quran sūra sub-classes in 5-D PCA projection")
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(out / "fig_subclass_scatter.png", dpi=130)
    plt.close(fig)

    # Mahalanobis tightness per class
    fig, ax = plt.subplots(figsize=(8, 4.5))
    xs = list(class_results.keys())
    med_ins = [class_results[k]["median_d_in_local_maha"] for k in xs]
    med_outs = [class_results[k]["median_d_out_local_maha"] for k in xs]
    perm_ps = [class_results[k]["perm_test"]["p"] for k in xs]
    w = 0.35
    idx_arr = np.arange(len(xs))
    ax.bar(idx_arr - w/2, med_ins, width=w, color="#2b8cbe",
           label="median d_in (within class)")
    ax.bar(idx_arr + w/2, med_outs, width=w, color="#888",
           label="median d_out (non-class)")
    for i, p in enumerate(perm_ps):
        ax.text(i, max(med_ins[i], med_outs[i]) * 1.05,
                f"p={p:.3f}", ha="center", fontsize=8)
    ax.set_xticks(idx_arr)
    ax.set_xticklabels(xs, rotation=20, ha="right")
    ax.set_ylabel("Local-Maha distance to sub-class centroid")
    ax.set_title("Sub-class tightness (lower d_in = tighter cluster)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(out / "fig_subclass_mahalanobis.png", dpi=130)
    plt.close(fig)

    # ---------- JSON ----------
    report = {
        "experiment": EXP,
        "description": (
            "Sub-class atlas. Tests whether pre-registered Qur'ānic sub-classes "
            "(oath_opening, muqattaat, hamim, story_dominant, short_mufassal) "
            "form coherent clusters in the 5-D feature space of the locked "
            "pipeline. Uses local-class Mahalanobis + permutation test (1000 "
            "shuffles) on 114 surahs."
        ),
        "preregistered_class_definitions": {
            k: sorted(v) for k, v in SUBCLASSES.items()
        },
        "feature_cols": feat_cols,
        "n_quran_surahs": int(len(X)),
        "classes": class_results,
        "pca": {
            "variance_explained_ratio": var_ratio.tolist(),
            "pc1_loadings": Vt[0].tolist(),
            "pc2_loadings": Vt[1].tolist(),
        },
    }
    with open(out / "exp05_subclass_atlas.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Console
    print(f"[{EXP}] 5 pre-registered Qur'ānic sub-classes on 114 surahs:")
    for name, r in class_results.items():
        ratio = r["separation_ratio"]
        p = r["perm_test"]["p"]
        print(f"  {name:18s}  n={r['n_found']:2d}/{r['n_expected']:<2d}  "
              f"d_in={r['median_d_in_local_maha']:.3f}  "
              f"d_out={r['median_d_out_local_maha']:.3f}  "
              f"ratio={ratio if ratio is None else f'{ratio:.2f}'}"
              f"  perm_p={p:.4f}")
    print(f"[{EXP}] wrote: {out}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
