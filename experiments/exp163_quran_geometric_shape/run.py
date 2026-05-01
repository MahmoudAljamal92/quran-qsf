"""experiments/exp163_quran_geometric_shape/run.py
=====================================================
V3.24 candidate -- IS THE QURAN'S 114-SURAH POINT CLOUD GEOMETRICALLY DISTINCT?

Three framings, all on the canonical 5-D Phi_M feature space:
    Framing A  -- Internal cloud-shape descriptors (7 frozen metrics)
                  on each corpus's per-unit cloud, matched-n bootstrap
                  null from the combined Phi_M pool. Bonferroni-Holm
                  correction over the 7-test family at alpha = 0.01.

    Framing B  -- Trajectory descriptors of the 114-surah polyline under
                  three canonical orderings (Mushaf, Nuzul, length-asc).
                  Permutation null vs random orderings; Bonferroni-Holm
                  correction over 5 descriptors x 3 orderings = 15
                  tests at alpha = 0.01.

    Framing C  -- "Findings polytope": each corpus is a point in 6-D
                  z-space (5 Phi_M means + F-Universal-gap). Project to
                  2D and 3D via SVD, save PNG figures. No formal verdict.

Question reframe: instead of asking *whether* the Quran is an extremum
in feature space (already established at Hotelling T^2 = 3,557, AUC =
0.998 in F76 / LC3), this experiment asks whether the *shape* of the
Quran's per-surah cloud, or the *trajectory* of canonical orderings,
is geometrically distinct from controls beyond just centroid offset.

Frozen constants:
    SEED               = 42
    N_BOOTSTRAP        = 10_000
    N_SUBSAMPLE        = 200
    ALPHA_BHL          = 0.01    (family-wise alpha after Bonferroni-Holm)
    FEAT_COLS          = ['EL', 'VL_CV', 'CN', 'H_cond', 'T']
    N_QURAN_TARGET     = state['X_QURAN'].shape[0]  (Band-A: 68)

PREREG  : experiments/exp163_quran_geometric_shape/PREREG.md
Inputs  : phase_06_phi_m.pkl (CORPORA + FEATS + X_QURAN + X_CTRL_POOL)
Output  : results/experiments/exp163_quran_geometric_shape/
            exp163_quran_geometric_shape.json
            frame_A_radar.png
            frame_B_trajectories.png
            frame_C_polytope_2d.png
            frame_C_polytope_3d.png
"""
from __future__ import annotations

import io
import json
import math
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial.distance import cdist

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import load_phase, safe_output_dir  # noqa: E402

EXP = "exp163_quran_geometric_shape"
SEED = 42
N_BOOTSTRAP = 10_000
N_SUBSAMPLE = 200
ALPHA_BHL = 0.01
FEAT_COLS = ["EL", "VL_CV", "CN", "H_cond", "T"]

# Egyptian-Standard-Edition Nuzul order (same source as expE17b:72-80)
NUZUL_ORDER_1IDX = [
    96, 68, 73, 74, 1, 111, 81, 87, 92, 89, 93, 94, 103, 100, 108, 102,
    107, 109, 105, 113, 114, 112, 53, 80, 97, 91, 85, 95, 106, 101, 75,
    104, 77, 50, 90, 86, 54, 38, 7, 72, 36, 25, 35, 19, 20, 56, 26, 27,
    28, 17, 10, 11, 12, 15, 6, 37, 31, 34, 39, 40, 41, 42, 43, 44, 45,
    46, 51, 88, 18, 16, 71, 14, 21, 23, 32, 52, 67, 69, 70, 78, 79, 82,
    84, 30, 29, 83, 2, 8, 3, 33, 60, 4, 99, 57, 47, 13, 55, 76, 65, 98,
    59, 24, 22, 63, 58, 49, 66, 64, 61, 62, 48, 5, 9, 110,
]
assert len(NUZUL_ORDER_1IDX) == 114 and set(NUZUL_ORDER_1IDX) == set(range(1, 115))

CORPORA_FOR_FRAME_A = [
    "quran", "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hadith_bukhari", "hindawi",
]
# Iliad, Tanakh, NT, Pali, Avestan are not in FEATS dict (they were not
# Phi_M-fitted because they require non-Arabic feature pipeline).

ARABIC_28 = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
A28_SET = set(ARABIC_28)
DIACRITIC_RANGES = (
    (0x0610, 0x061A), (0x064B, 0x065F), (0x06D6, 0x06ED),
    (0x0670, 0x0670),
)
TATWEEL = "\u0640"
HAMZA_FOLD = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
              "ئ": "ي", "ؤ": "و", "ء": "",
              "ة": "ه", "ى": "ي"}


# =========================================================================
#  Helpers: feature-matrix construction
# =========================================================================

def per_corpus_matrix(state: dict, corpus_name: str) -> np.ndarray:
    """Build N x 5 feature matrix from state['FEATS'][corpus_name]."""
    feats = state["FEATS"][corpus_name]
    return np.array([[u[c] for c in FEAT_COLS] for u in feats],
                    dtype=np.float64)


def per_surah_matrix_in_mushaf_order(state: dict) -> np.ndarray:
    """114 x 5 Quran feature matrix, row i = surah (i+1) (canonical Mushaf)."""
    feat_by_surah: dict[int, list[float]] = {}
    for i, u in enumerate(state["CORPORA"]["quran"]):
        label = getattr(u, "label", f"Q:{i + 1}")
        sn = int(str(label).replace("Q:", "").strip())
        feat_by_surah[sn] = [state["FEATS"]["quran"][i][c] for c in FEAT_COLS]
    return np.array([feat_by_surah[s] for s in range(1, 115)], dtype=np.float64)


def whitening_transform(X: np.ndarray, ridge: float = 1e-6) -> np.ndarray:
    """Mahalanobis-equivalent whitening (same as expE17b:103-123)."""
    mu = X.mean(axis=0)
    Z = X - mu
    Sigma = np.cov(Z, rowvar=False) + ridge * np.eye(X.shape[1])
    w, V = np.linalg.eigh(Sigma)
    w_inv = 1.0 / w
    A = (V * np.sqrt(w_inv)).T
    return X @ A.T


# =========================================================================
#  Framing A: cloud-shape descriptors
# =========================================================================

def shape_descriptors(X: np.ndarray) -> dict[str, float]:
    """Compute the seven frozen shape descriptors for an n x d cloud."""
    n, d = X.shape
    if n < d + 1:
        return {k: float("nan") for k in (
            "sphericity_log10", "isotropy", "intrinsic_dim_95pct",
            "anisotropy_westin", "linearity_westin", "planarity_westin",
            "symmetry_score", "regularity_NN_CV", "logvol",
        )}
    Xc = X - X.mean(axis=0)
    cov = np.cov(Xc, rowvar=False)
    eig = np.linalg.eigvalsh(cov)
    eig = np.sort(eig)[::-1]
    eig = np.maximum(eig, 1e-12)

    sphericity_log10 = float(math.log10(eig[0] / eig[-1]))
    isotropy = float(eig[-1] / eig[0])
    cumvar = np.cumsum(eig) / eig.sum()
    intrinsic_dim_95pct = int(np.searchsorted(cumvar, 0.95) + 1)
    aniso = float((eig[0] - eig[-1]) / (eig[0] + eig[-1]))
    linearity = float((eig[0] - eig[1]) / eig[0]) if d >= 2 else 0.0
    planarity = (float((eig[1] - eig[-1]) / eig[0])
                 if d >= 3 else 0.0)

    # Symmetry: distance from each point to nearest -reflected counterpart
    Xref = -Xc
    D = cdist(Xc, Xref)
    nn_to_ref = D.min(axis=1)
    pdist = cdist(Xc, Xc)
    iu = np.triu_indices(n, k=1)
    median_pd = float(np.median(pdist[iu])) if iu[0].size else 1.0
    if median_pd <= 0:
        median_pd = 1.0
    sym_score = float(nn_to_ref.mean() / median_pd)

    # Regularity: CV of nearest-neighbour distances (lower = more even)
    np.fill_diagonal(pdist, np.inf)
    nn_dists = pdist.min(axis=1)
    regularity = (float(nn_dists.std() / nn_dists.mean())
                  if nn_dists.mean() > 0 else float("nan"))

    # Hyper-volume proxy: log10 of sqrt(det(cov))
    logvol = float(0.5 * np.sum(np.log10(eig)))

    return {
        "sphericity_log10": sphericity_log10,
        "isotropy": isotropy,
        "intrinsic_dim_95pct": intrinsic_dim_95pct,
        "anisotropy_westin": aniso,
        "linearity_westin": linearity,
        "planarity_westin": planarity,
        "symmetry_score": sym_score,
        "regularity_NN_CV": regularity,
        "logvol": logvol,
    }


SEVEN_FROZEN_DESC = [
    "sphericity_log10", "isotropy", "intrinsic_dim_95pct",
    "anisotropy_westin", "linearity_westin", "planarity_westin",
    "symmetry_score",
]


def two_sided_p(observed: float, null_array: np.ndarray) -> float:
    if null_array.size == 0 or not np.isfinite(observed):
        return float("nan")
    p_low = float((null_array <= observed).mean())
    p_high = float((null_array >= observed).mean())
    return min(1.0, 2 * min(p_low, p_high))


def bonferroni_holm(p_named: list[tuple[str, float]],
                    alpha: float) -> list[str]:
    """Return list of names that survive Bonferroni-Holm at family-wise
    alpha."""
    sorted_p = sorted(p_named, key=lambda x: x[1])
    n = len(sorted_p)
    survived: list[str] = []
    for i, (name, p) in enumerate(sorted_p):
        if not np.isfinite(p):
            break
        thr = alpha / (n - i)
        if p <= thr:
            survived.append(name)
        else:
            break
    return survived


def run_frame_A(state: dict, rng: np.random.Generator,
                out_dir: Path) -> dict[str, Any]:
    """Internal cloud-shape descriptors with bootstrap-from-pool null."""
    X_QURAN = state["X_QURAN"].astype(np.float64)
    n_target = X_QURAN.shape[0]
    print(f"  [A] N_QURAN_TARGET = {n_target}, FEAT_COLS = {FEAT_COLS}")

    # Per-corpus 5-D matrices (FULL clouds, then we subsample)
    full_clouds = {c: per_corpus_matrix(state, c) for c in CORPORA_FOR_FRAME_A}
    full_clouds["quran"] = X_QURAN  # use Band-A filtered for fair comparison

    # Per-corpus descriptor (median across N_SUBSAMPLE replicates if larger)
    per_corpus_desc: dict[str, dict[str, float]] = {}
    per_corpus_desc_std: dict[str, dict[str, float]] = {}
    for cname, X in full_clouds.items():
        if cname == "quran":
            d_obs = shape_descriptors(X)
            per_corpus_desc[cname] = d_obs
            per_corpus_desc_std[cname] = {k: 0.0 for k in d_obs}
            continue
        if X.shape[0] < n_target:
            d_obs = shape_descriptors(X)
            per_corpus_desc[cname] = d_obs
            per_corpus_desc_std[cname] = {k: 0.0 for k in d_obs}
            continue
        descs = []
        for _ in range(N_SUBSAMPLE):
            idx = rng.choice(X.shape[0], size=n_target, replace=False)
            descs.append(shape_descriptors(X[idx]))
        agg = {k: float(np.median([d[k] for d in descs])) for k in descs[0]}
        agg_std = {k: float(np.std([d[k] for d in descs])) for k in descs[0]}
        per_corpus_desc[cname] = agg
        per_corpus_desc_std[cname] = agg_std

    # Bootstrap-from-pool null
    pool = np.vstack([X_QURAN, state["X_CTRL_POOL"].astype(np.float64)])
    print(f"  [A] Bootstrap pool size = {pool.shape[0]} rows; "
          f"running {N_BOOTSTRAP} bootstraps of n={n_target} ...")
    t1 = time.time()
    null_descs: list[dict[str, float]] = []
    for k in range(N_BOOTSTRAP):
        idx = rng.choice(pool.shape[0], size=n_target, replace=False)
        null_descs.append(shape_descriptors(pool[idx]))
        if (k + 1) % 2000 == 0:
            print(f"    [A] bootstrap {k + 1}/{N_BOOTSTRAP}  "
                  f"elapsed {time.time() - t1:.1f}s")
    print(f"  [A] bootstrap done in {time.time() - t1:.1f} s")

    # Compute Quran p-value vs bootstrap null for each descriptor
    quran_p: dict[str, dict[str, float]] = {}
    for k in per_corpus_desc["quran"]:
        nulls = np.array([d[k] for d in null_descs], dtype=np.float64)
        nulls = nulls[np.isfinite(nulls)]
        obs = per_corpus_desc["quran"][k]
        p2 = two_sided_p(obs, nulls)
        quran_p[k] = {
            "observed": obs,
            "null_median": float(np.median(nulls)) if nulls.size else float("nan"),
            "null_std": float(nulls.std()) if nulls.size else float("nan"),
            "null_p25": float(np.percentile(nulls, 25)) if nulls.size else float("nan"),
            "null_p75": float(np.percentile(nulls, 75)) if nulls.size else float("nan"),
            "p_two_sided_vs_bootstrap": p2,
        }

    # Bonferroni-Holm over the 7 frozen descriptors
    p_pairs = [(k, quran_p[k]["p_two_sided_vs_bootstrap"])
               for k in SEVEN_FROZEN_DESC]
    bhl_survivors = bonferroni_holm(p_pairs, ALPHA_BHL)

    # Quran rank vs the 7 controls (rank 1 = lowest descriptor value)
    quran_rank: dict[str, dict[str, Any]] = {}
    for k in per_corpus_desc["quran"]:
        ordered = sorted(
            per_corpus_desc.items(),
            key=lambda kv: (
                kv[1][k] if np.isfinite(kv[1][k]) else float("inf")
            ),
        )
        rank_low = next(i for i, (cn, _) in enumerate(ordered)
                        if cn == "quran") + 1
        ordered_high = sorted(
            per_corpus_desc.items(),
            key=lambda kv: (
                -kv[1][k] if np.isfinite(kv[1][k]) else float("inf")
            ),
        )
        rank_high = next(i for i, (cn, _) in enumerate(ordered_high)
                         if cn == "quran") + 1
        quran_rank[k] = {"rank_low": rank_low, "rank_high": rank_high,
                         "out_of": len(per_corpus_desc)}

    # Render radar PNG (each axis is a descriptor; each corpus a polygon)
    radar_path = out_dir / "frame_A_radar.png"
    try:
        _render_frame_A_radar(per_corpus_desc, radar_path)
        radar_status = "ok"
    except Exception as e:
        radar_status = f"fail: {e}"

    return {
        "n_target": int(n_target),
        "per_corpus_descriptors": per_corpus_desc,
        "per_corpus_desc_subsample_std": per_corpus_desc_std,
        "quran_vs_bootstrap_pool_null": quran_p,
        "quran_rank_in_8_corpora": quran_rank,
        "bhl_alpha": ALPHA_BHL,
        "bhl_survivors_among_7_descriptors": bhl_survivors,
        "n_bhl_survivors": len(bhl_survivors),
        "seven_frozen_descriptors": SEVEN_FROZEN_DESC,
        "radar_png": str(radar_path),
        "radar_status": radar_status,
    }


def _render_frame_A_radar(per_corpus_desc: dict[str, dict[str, float]],
                          out_png: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    descs = SEVEN_FROZEN_DESC
    # Normalise each axis to [0, 1] across corpora for visual comparability
    matrix = []
    corpora = list(per_corpus_desc.keys())
    for cn in corpora:
        matrix.append([per_corpus_desc[cn][d] for d in descs])
    M = np.array(matrix, dtype=np.float64)
    M = np.nan_to_num(M, nan=0.0, posinf=0.0, neginf=0.0)
    Mmin = M.min(axis=0)
    Mmax = M.max(axis=0)
    rng_ = np.where((Mmax - Mmin) > 1e-12, Mmax - Mmin, 1.0)
    Mn = (M - Mmin) / rng_

    angles = np.linspace(0, 2 * np.pi, len(descs), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(11, 9), subplot_kw={"projection": "polar"})
    colors = plt.cm.tab10(np.linspace(0, 1, len(corpora)))
    for i, cn in enumerate(corpora):
        vals = Mn[i].tolist() + [Mn[i, 0]]
        lw = 3.0 if cn == "quran" else 1.4
        ls = "-" if cn == "quran" else "--"
        alpha = 1.0 if cn == "quran" else 0.7
        ax.plot(angles, vals, color=colors[i], linewidth=lw,
                linestyle=ls, label=cn, alpha=alpha)
        ax.fill(angles, vals, color=colors[i], alpha=0.05)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([d.replace("_", "\n") for d in descs], fontsize=8)
    ax.set_yticklabels([])
    ax.set_title("Frame A — 7 cloud-shape descriptors, normalised across corpora\n"
                 "(Quran in solid bold; controls dashed)",
                 fontsize=11, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.45, 1.05), fontsize=9)
    fig.tight_layout()
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


# =========================================================================
#  Framing B: trajectory descriptors under canonical orderings
# =========================================================================

def trajectory_descriptors(X_ord: np.ndarray) -> dict[str, float]:
    """Compute trajectory descriptors for an n x d ordered point sequence."""
    n, d = X_ord.shape
    if n < 3:
        return {k: float("nan") for k in (
            "arc_length", "mean_curvature_rad", "curvature_variance",
            "closure_ratio_0closed_1straight", "smoothness_curvature_var",
        )}
    diffs = np.diff(X_ord, axis=0)
    seg = np.linalg.norm(diffs, axis=1)
    arc = float(seg.sum())

    angles: list[float] = []
    for i in range(n - 2):
        v1 = diffs[i]; v2 = diffs[i + 1]
        n1 = float(np.linalg.norm(v1)); n2 = float(np.linalg.norm(v2))
        if n1 > 1e-12 and n2 > 1e-12:
            cos_t = float(np.clip((v1 @ v2) / (n1 * n2), -1.0, 1.0))
            angles.append(math.acos(cos_t))
    mean_curv = float(np.mean(angles)) if angles else float("nan")
    var_curv = float(np.var(angles)) if angles else float("nan")
    end_to_end = float(np.linalg.norm(X_ord[-1] - X_ord[0]))
    closure = float(end_to_end / arc) if arc > 0 else float("nan")

    return {
        "arc_length": arc,
        "mean_curvature_rad": mean_curv,
        "curvature_variance": var_curv,
        "closure_ratio_0closed_1straight": closure,
        "smoothness_curvature_var": var_curv,  # alias for clarity
    }


FIVE_TRAJ_DESC = [
    "arc_length", "mean_curvature_rad", "curvature_variance",
    "closure_ratio_0closed_1straight", "smoothness_curvature_var",
]


def run_frame_B(state: dict, rng: np.random.Generator,
                out_dir: Path) -> dict[str, Any]:
    """Trajectory geometry under Mushaf, Nuzul, length orderings."""
    X = per_surah_matrix_in_mushaf_order(state)
    Xp = whitening_transform(X)  # Mahalanobis-isometric Euclidean space

    n_verses_by_idx = np.array(
        [state["FEATS"]["quran"][i]["n_verses"] for i in range(114)]
    )
    length_order = np.argsort(n_verses_by_idx).tolist()
    nuzul_zero_idx = [s - 1 for s in NUZUL_ORDER_1IDX]
    mushaf = list(range(114))

    orderings = {
        "mushaf": mushaf,
        "nuzul":  nuzul_zero_idx,
        "length_asc": length_order,
    }

    print(f"  [B] Computing trajectory descriptors for 3 orderings; "
          f"permutation null with {N_BOOTSTRAP} permutations ...")
    t1 = time.time()
    null_descs: list[dict[str, float]] = []
    for k in range(N_BOOTSTRAP):
        perm = rng.permutation(114)
        null_descs.append(trajectory_descriptors(Xp[perm]))
        if (k + 1) % 2000 == 0:
            print(f"    [B] perm {k + 1}/{N_BOOTSTRAP}  "
                  f"elapsed {time.time() - t1:.1f}s")

    obs_per_ordering: dict[str, dict[str, Any]] = {}
    p_named_all: list[tuple[str, float]] = []
    for ord_name, order in orderings.items():
        obs = trajectory_descriptors(Xp[order])
        p_for_ordering: dict[str, dict[str, float]] = {}
        for k in obs:
            nulls = np.array([d[k] for d in null_descs], dtype=np.float64)
            nulls = nulls[np.isfinite(nulls)]
            p2 = two_sided_p(obs[k], nulls)
            p_for_ordering[k] = {
                "observed": obs[k],
                "null_median": float(np.median(nulls)) if nulls.size else float("nan"),
                "null_std": float(nulls.std()) if nulls.size else float("nan"),
                "p_two_sided_vs_random_orderings": p2,
            }
            if k in FIVE_TRAJ_DESC:
                p_named_all.append((f"{ord_name}/{k}", p2))
        obs_per_ordering[ord_name] = {
            "descriptors": obs,
            "p_values": p_for_ordering,
        }

    bhl_survivors = bonferroni_holm(p_named_all, ALPHA_BHL)

    # Render trajectory PNG (2D PCA projection of the 5-D whitened cloud)
    traj_png = out_dir / "frame_B_trajectories.png"
    try:
        _render_frame_B_trajectories(Xp, orderings, traj_png)
        traj_status = "ok"
    except Exception as e:
        traj_status = f"fail: {e}"

    return {
        "n_surahs": 114,
        "orderings": list(orderings.keys()),
        "n_permutations": N_BOOTSTRAP,
        "per_ordering": obs_per_ordering,
        "bhl_alpha": ALPHA_BHL,
        "bhl_survivors": bhl_survivors,
        "n_bhl_survivors": len(bhl_survivors),
        "five_traj_descriptors": FIVE_TRAJ_DESC,
        "trajectory_png": str(traj_png),
        "trajectory_status": traj_status,
    }


def _render_frame_B_trajectories(Xp: np.ndarray,
                                 orderings: dict[str, list[int]],
                                 out_png: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    Xc = Xp - Xp.mean(axis=0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    pc2 = U[:, :2] * S[:2]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, (name, order) in zip(axes, orderings.items()):
        traj = pc2[order]
        ax.plot(traj[:, 0], traj[:, 1], "-", lw=0.6, color="grey", alpha=0.6)
        sc = ax.scatter(traj[:, 0], traj[:, 1],
                        c=np.arange(114), cmap="viridis", s=20)
        ax.scatter(traj[0, 0], traj[0, 1], color="red", s=80,
                   marker="^", label="start", zorder=5)
        ax.scatter(traj[-1, 0], traj[-1, 1], color="black", s=80,
                   marker="s", label="end", zorder=5)
        ax.set_title(f"{name} order trajectory in Phi_M PC1-PC2 (whitened)")
        ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
        ax.legend(loc="best", fontsize=8)
    fig.colorbar(sc, ax=axes, label="position in ordering",
                 fraction=0.02, pad=0.02)
    fig.suptitle("Frame B — 114-surah trajectories in 5-D Phi_M (whitened, 2D PCA projection)",
                 fontsize=12)
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


# =========================================================================
#  Framing C: findings polytope
# =========================================================================

def is_diacritic(ch: str) -> bool:
    cp = ord(ch)
    for lo, hi in DIACRITIC_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def to_28_letters(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    out: list[str] = []
    for ch in text:
        if is_diacritic(ch) or ch == TATWEEL:
            continue
        if ch in HAMZA_FOLD:
            ch = HAMZA_FOLD[ch]
            if not ch:
                continue
        if ch in A28_SET:
            out.append(ch)
    return "".join(out)


def f_universal_gap(units: list) -> float:
    """Return H_letter (bits) + log2(p_max_letter) for a corpus."""
    counts: dict[str, int] = {c: 0 for c in ARABIC_28}
    total = 0
    for u in units:
        verses = getattr(u, "verses", None)
        if verses is None and isinstance(u, dict):
            verses = u.get("verses", [])
        if not verses:
            continue
        joined = " ".join(verses)
        for ch in to_28_letters(joined):
            counts[ch] += 1
            total += 1
    if total == 0:
        return float("nan")
    p = np.array([counts[c] / total for c in ARABIC_28], dtype=np.float64)
    p = p[p > 0]
    H = float(-np.sum(p * np.log2(p)))
    p_max = float(p.max())
    return H + math.log2(p_max)


def run_frame_C(state: dict, out_dir: Path) -> dict[str, Any]:
    """Build per-corpus z-vectors and project to 2D / 3D."""
    print("  [C] Computing per-corpus mean Phi_M + F-Universal gap ...")
    rows = []
    names = []
    for cname in CORPORA_FOR_FRAME_A:
        X = per_corpus_matrix(state, cname)
        units = state["CORPORA"].get(cname, [])
        gap = f_universal_gap(units)
        rows.append([*X.mean(axis=0).tolist(), gap])
        names.append(cname)

    arr = np.array(rows, dtype=np.float64)
    feat_names = FEAT_COLS + ["F_universal_gap"]
    print(f"  [C] corpus x feature shape: {arr.shape}")

    # z-score each column across corpora
    mu = np.nanmean(arr, axis=0)
    sd = np.nanstd(arr, axis=0) + 1e-12
    Z = (arr - mu) / sd

    # 2D and 3D MDS via SVD on centered Z
    Zc = Z - Z.mean(axis=0)
    U, S, Vt = np.linalg.svd(Zc, full_matrices=False)
    var_explained = (S ** 2) / np.sum(S ** 2)
    emb_2d = U[:, :2] * S[:2]
    emb_3d = U[:, :3] * S[:3]

    pdist = cdist(Z, Z)
    q_idx = names.index("quran")
    other_idx = [i for i in range(len(names)) if i != q_idx]
    sorted_others = sorted(other_idx, key=lambda i: pdist[q_idx, i])
    nearest = names[sorted_others[0]]
    farthest = names[sorted_others[-1]]
    print(f"  [C] Quran nearest neighbour : {nearest}  "
          f"(d = {pdist[q_idx, sorted_others[0]]:.3f})")
    print(f"  [C] Quran farthest neighbour: {farthest}  "
          f"(d = {pdist[q_idx, sorted_others[-1]]:.3f})")

    poly2d_png = out_dir / "frame_C_polytope_2d.png"
    poly3d_png = out_dir / "frame_C_polytope_3d.png"
    try:
        _render_frame_C_2d(emb_2d, names, var_explained, poly2d_png)
        c2d = "ok"
    except Exception as e:
        c2d = f"fail: {e}"
    try:
        _render_frame_C_3d(emb_3d, names, var_explained, poly3d_png)
        c3d = "ok"
    except Exception as e:
        c3d = f"fail: {e}"

    return {
        "names": names,
        "feat_names": feat_names,
        "raw_means_per_corpus": arr.tolist(),
        "z_vectors_per_corpus": Z.tolist(),
        "svd_var_explained": var_explained.tolist(),
        "embedding_2d": emb_2d.tolist(),
        "embedding_3d": emb_3d.tolist(),
        "pairwise_z_distances": pdist.tolist(),
        "quran_nearest": nearest,
        "quran_farthest": farthest,
        "polytope_2d_png": str(poly2d_png),
        "polytope_2d_status": c2d,
        "polytope_3d_png": str(poly3d_png),
        "polytope_3d_status": c3d,
    }


def _render_frame_C_2d(emb: np.ndarray, names: list[str],
                       var_explained: np.ndarray, out_png: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.spatial import ConvexHull

    fig, ax = plt.subplots(figsize=(10, 9))
    for i, name in enumerate(names):
        is_q = name == "quran"
        ax.scatter(emb[i, 0], emb[i, 1],
                   s=400 if is_q else 200,
                   c="red" if is_q else "steelblue",
                   edgecolors="black", linewidths=2.0 if is_q else 0.8,
                   zorder=5 if is_q else 3)
        ax.annotate(name, (emb[i, 0], emb[i, 1]),
                    xytext=(8, 6), textcoords="offset points",
                    fontsize=11 if is_q else 9,
                    weight="bold" if is_q else "normal")
    # Convex hull
    if len(emb) >= 3:
        hull = ConvexHull(emb)
        for simplex in hull.simplices:
            ax.plot(emb[simplex, 0], emb[simplex, 1],
                    "k--", lw=0.8, alpha=0.6)
    ax.axhline(0, color="grey", lw=0.4)
    ax.axvline(0, color="grey", lw=0.4)
    ax.set_xlabel(f"PC1 ({var_explained[0] * 100:.1f}% var)")
    ax.set_ylabel(f"PC2 ({var_explained[1] * 100:.1f}% var)")
    ax.set_title("Frame C — Findings polytope (corpus z-vectors in 6D, 2D MDS)\n"
                 "Axes: EL, VL_CV, CN, H_cond, T, F-Universal-gap; Quran in red")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _render_frame_C_3d(emb: np.ndarray, names: list[str],
                       var_explained: np.ndarray, out_png: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    fig = plt.figure(figsize=(11, 9))
    ax = fig.add_subplot(111, projection="3d")
    for i, name in enumerate(names):
        is_q = name == "quran"
        ax.scatter(emb[i, 0], emb[i, 1], emb[i, 2],
                   s=400 if is_q else 200,
                   c="red" if is_q else "steelblue",
                   edgecolors="black", linewidths=2.0 if is_q else 0.8)
        ax.text(emb[i, 0], emb[i, 1], emb[i, 2], "  " + name,
                fontsize=11 if is_q else 9,
                weight="bold" if is_q else "normal")
    # All pairwise edges (semi-transparent)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ax.plot([emb[i, 0], emb[j, 0]],
                    [emb[i, 1], emb[j, 1]],
                    [emb[i, 2], emb[j, 2]],
                    "k--", lw=0.4, alpha=0.25)
    ax.set_xlabel(f"PC1 ({var_explained[0] * 100:.1f}%)")
    ax.set_ylabel(f"PC2 ({var_explained[1] * 100:.1f}%)")
    ax.set_zlabel(f"PC3 ({var_explained[2] * 100:.1f}%)")
    ax.set_title("Frame C — Findings polytope, 3D MDS (corpus z-vectors)\n"
                 "Axes: EL, VL_CV, CN, H_cond, T, F-Universal-gap")
    fig.tight_layout()
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


# =========================================================================
#  Main
# =========================================================================

def main() -> dict[str, Any]:
    out_dir = safe_output_dir(EXP)
    out_path = out_dir / f"{EXP}.json"
    t0 = time.time()
    completed_at_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rng = np.random.default_rng(SEED)

    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]

    print(f"[{EXP}] === Framing A: cloud-shape descriptors ===")
    frame_A = run_frame_A(state, rng, out_dir)
    print(f"[{EXP}] Frame A BHL survivors: {frame_A['bhl_survivors_among_7_descriptors']}")

    print(f"[{EXP}] === Framing B: trajectory geometry ===")
    frame_B = run_frame_B(state, rng, out_dir)
    print(f"[{EXP}] Frame B BHL survivors: {frame_B['bhl_survivors']}")

    print(f"[{EXP}] === Framing C: findings polytope ===")
    frame_C = run_frame_C(state, out_dir)

    # Composite verdict
    a_pass = frame_A["n_bhl_survivors"] >= 1
    b_pass = frame_B["n_bhl_survivors"] >= 1

    if a_pass and b_pass:
        verdict = "PASS_GEOMETRY_AND_TRAJECTORY_DISTINCT"
    elif a_pass:
        verdict = "PASS_CLOUD_GEOMETRY_DISTINCT"
    elif b_pass:
        verdict = "PASS_TRAJECTORY_DISTINCT"
    else:
        # report finer-grained partial verdicts
        any_p_below_05_A = any(
            frame_A["quran_vs_bootstrap_pool_null"][k][
                "p_two_sided_vs_bootstrap"
            ] < 0.05
            for k in SEVEN_FROZEN_DESC
            if np.isfinite(
                frame_A["quran_vs_bootstrap_pool_null"][k][
                    "p_two_sided_vs_bootstrap"
                ]
            )
        )
        any_rank1_A = any(
            frame_A["quran_rank_in_8_corpora"][k]["rank_low"] == 1
            or frame_A["quran_rank_in_8_corpora"][k]["rank_high"] == 1
            for k in SEVEN_FROZEN_DESC
        )
        any_p_below_05_B = any(
            frame_B["per_ordering"][o]["p_values"][k][
                "p_two_sided_vs_random_orderings"
            ] < 0.05
            for o in frame_B["orderings"]
            for k in FIVE_TRAJ_DESC
            if np.isfinite(
                frame_B["per_ordering"][o]["p_values"][k][
                    "p_two_sided_vs_random_orderings"
                ]
            )
        )
        if any_rank1_A and any_p_below_05_A:
            verdict = "PARTIAL_QURAN_GEOMETRY_RANK1_BUT_NOT_BHL_SIGNIFICANT"
        elif any_p_below_05_B:
            verdict = "PARTIAL_TRAJECTORY_NOMINAL_p05_NOT_BHL_SIGNIFICANT"
        else:
            verdict = "FAIL_NO_GEOMETRIC_DISTINCTION_BEYOND_CENTROID"

    receipt: dict[str, Any] = {
        "experiment": EXP,
        "schema_version": 1,
        "hypothesis": (
            "Beyond the already-locked Hotelling T^2 = 3,557 centroid offset, "
            "the Quran's per-surah point cloud in 5-D Phi_M space has "
            "geometrically distinct shape (Frame A) or its canonical "
            "orderings (Mushaf, Nuzul, length) trace a notably non-random "
            "trajectory through that space (Frame B). Frame C generates "
            "diagnostic 2D/3D figures of the corpus polytope."
        ),
        "verdict": verdict,
        "completed_at_utc": completed_at_utc,
        "wall_time_s": float(time.time() - t0),
        "frozen_constants": {
            "SEED": SEED, "N_BOOTSTRAP": N_BOOTSTRAP,
            "N_SUBSAMPLE": N_SUBSAMPLE, "ALPHA_BHL": ALPHA_BHL,
            "FEAT_COLS": FEAT_COLS,
            "CORPORA_FOR_FRAME_A": CORPORA_FOR_FRAME_A,
            "SEVEN_FROZEN_DESC": SEVEN_FROZEN_DESC,
            "FIVE_TRAJ_DESC": FIVE_TRAJ_DESC,
        },
        "frame_A": frame_A,
        "frame_B": frame_B,
        "frame_C": frame_C,
    }
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    print("\n" + "=" * 70)
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Frame A BHL survivors ({frame_A['n_bhl_survivors']}/7): "
          f"{frame_A['bhl_survivors_among_7_descriptors']}")
    print(f"  Frame B BHL survivors ({frame_B['n_bhl_survivors']}/15): "
          f"{frame_B['bhl_survivors']}")
    print(f"  Frame C Quran NN: {frame_C['quran_nearest']}; "
          f"farthest: {frame_C['quran_farthest']}")
    print(f"  PNGs: A={frame_A['radar_status']}, "
          f"B={frame_B['trajectory_status']}, "
          f"C2D={frame_C['polytope_2d_status']}, "
          f"C3D={frame_C['polytope_3d_status']}")
    print(f"  wall-time = {receipt['wall_time_s']:.1f} s")
    print(f"  receipt: {out_path}")
    print("=" * 70)
    return receipt


if __name__ == "__main__":
    main()
