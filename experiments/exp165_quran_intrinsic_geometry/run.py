"""experiments/exp165_quran_intrinsic_geometry/run.py
==========================================================
V3.26 candidate -- INTRINSIC geometry of the Quran (no controls).

The user reframed the geometric question: not "is the Quran's shape
distinct from poetry/Bible/etc." but "does the Quran *itself* trace a
coherent geometric form against an intrinsic null". This experiment
takes that reframe seriously: NO control corpora are touched. All
nulls are intrinsic (random uniform-cube clouds, random permutations,
random Gaussian clouds).

13 frozen tests across 4 sub-families:
    Sub-A: k-NN graph topology of the 114-surah cloud (4 tests)
    Sub-B: Mushaf trajectory intrinsic descriptors (3 tests)
    Sub-C: manifold intrinsic dimension (2 tests)
    Sub-D: Mushaf-ordered verse-count FFT spectrum (4 tests)

Bonferroni-Holm at family-wise alpha = 0.01 over 13 tests.

PREREG : experiments/exp165_quran_intrinsic_geometry/PREREG.md
Inputs : phase_06_phi_m.pkl (CORPORA + FEATS + X_QURAN)
Output : results/experiments/exp165_quran_intrinsic_geometry/
            exp165_quran_intrinsic_geometry.json + 4 PNGs
"""
from __future__ import annotations

import io
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import networkx as nx
from networkx.algorithms.community.louvain import louvain_communities
from networkx.algorithms.community.quality import modularity as nx_modularity
from networkx.algorithms.planarity import check_planarity
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

EXP = "exp165_quran_intrinsic_geometry"
SEED = 44
N_NULL_CLOUDS = 5_000
N_PERMUTATIONS = 10_000
ALPHA_BHL = 0.01
N_QURAN_TARGET = 114
FEAT_COLS = ["EL", "VL_CV", "CN", "H_cond", "T"]
KNN_K_VALUES = [3, 5, 7]


# =========================================================================
#  Data loaders
# =========================================================================

def per_surah_matrix_in_mushaf_order(state: dict) -> np.ndarray:
    """114 x 5 Quran feature matrix, row i = surah (i+1) in Mushaf order."""
    feat_by_surah: dict[int, list[float]] = {}
    for i, u in enumerate(state["CORPORA"]["quran"]):
        label = getattr(u, "label", f"Q:{i + 1}")
        sn = int(str(label).replace("Q:", "").strip())
        feat_by_surah[sn] = [state["FEATS"]["quran"][i][c] for c in FEAT_COLS]
    return np.array([feat_by_surah[s] for s in range(1, 115)], dtype=np.float64)


def per_surah_verse_counts(state: dict) -> np.ndarray:
    """Length-114 vector of verse counts in Mushaf order."""
    counts_by_surah: dict[int, int] = {}
    for i, u in enumerate(state["CORPORA"]["quran"]):
        label = getattr(u, "label", f"Q:{i + 1}")
        sn = int(str(label).replace("Q:", "").strip())
        verses = getattr(u, "verses", None)
        if verses is None and isinstance(u, dict):
            verses = u.get("verses", [])
        counts_by_surah[sn] = len(verses) if verses else 0
    return np.array([counts_by_surah[s] for s in range(1, 115)], dtype=np.int64)


def whitening_transform(X: np.ndarray, ridge: float = 1e-6) -> np.ndarray:
    """Mahalanobis-equivalent whitening so squared Euclidean = squared
    Mahalanobis. Pool covariance after this is ~ I."""
    mu = X.mean(axis=0)
    Z = X - mu
    Sigma = np.cov(Z, rowvar=False) + ridge * np.eye(X.shape[1])
    w, V = np.linalg.eigh(Sigma)
    A = (V * np.sqrt(1.0 / w)).T
    return X @ A.T


def two_sided_p(observed: float, null: np.ndarray) -> float:
    null = null[np.isfinite(null)]
    if null.size == 0 or not np.isfinite(observed):
        return float("nan")
    p_low = float((null <= observed).mean())
    p_high = float((null >= observed).mean())
    return min(1.0, 2 * min(p_low, p_high))


def bonferroni_holm(p_named: list[tuple[str, float]],
                    alpha: float) -> list[str]:
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


# =========================================================================
#  Sub-A : k-NN graph topology
# =========================================================================

def build_knn_graph(X: np.ndarray, k: int) -> nx.Graph:
    """Symmetric k-NN graph: connect i-j if either is in the other's top-k."""
    n = X.shape[0]
    D = cdist(X, X)
    np.fill_diagonal(D, np.inf)
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for i in range(n):
        nn = np.argsort(D[i])[:k]
        for j in nn:
            G.add_edge(i, int(j))
    return G


def graph_descriptors(G: nx.Graph) -> dict[str, float]:
    n = G.number_of_nodes()
    if n < 2:
        return dict.fromkeys((
            "is_planar", "clustering_coefficient", "modularity",
            "spectral_gap", "n_components",
        ), float("nan"))
    is_planar, _ = check_planarity(G)
    clust = float(nx.average_clustering(G))
    try:
        comms = louvain_communities(G, seed=0)
        mod = float(nx_modularity(G, comms))
    except Exception:
        mod = float("nan")
    n_comp = nx.number_connected_components(G)
    if n_comp == 1 and n >= 3:
        try:
            L = nx.normalized_laplacian_matrix(G).toarray()
            eigvals = np.sort(np.linalg.eigvalsh(L))
            spectral_gap = float(eigvals[1])
        except Exception:
            spectral_gap = float("nan")
    else:
        spectral_gap = 0.0
    return {
        "is_planar": float(is_planar),
        "clustering_coefficient": clust,
        "modularity": mod,
        "spectral_gap": spectral_gap,
        "n_components": float(n_comp),
    }


def run_sub_A(X_white: np.ndarray, rng: np.random.Generator,
              out_dir: Path) -> dict[str, Any]:
    """k-NN graph topology with uniform-cube cloud null."""
    n = X_white.shape[0]
    d = X_white.shape[1]

    # Quran observed at each k
    obs_per_k: dict[int, dict[str, float]] = {}
    for k in KNN_K_VALUES:
        G = build_knn_graph(X_white, k)
        obs_per_k[k] = graph_descriptors(G)

    # Null at k=5 only (the 4 frozen tests are all at k=5; report others as exploratory)
    print(f"  [A] generating {N_NULL_CLOUDS} uniform-cube null clouds (n={n}, d={d}) ...")
    t1 = time.time()
    null_descs: list[dict[str, float]] = []
    # Place uniform cube to span observed bounding box for fair comparison
    lo = X_white.min(axis=0)
    hi = X_white.max(axis=0)
    rng_arr = (hi - lo)
    for kk in range(N_NULL_CLOUDS):
        Xr = rng.random(size=(n, d)) * rng_arr + lo
        G = build_knn_graph(Xr, 5)
        null_descs.append(graph_descriptors(G))
        if (kk + 1) % 1000 == 0:
            print(f"    [A] null {kk + 1}/{N_NULL_CLOUDS}  elapsed {time.time() - t1:.1f}s")
    print(f"  [A] null done in {time.time() - t1:.1f} s")

    null_arr_clust = np.array([d_["clustering_coefficient"] for d_ in null_descs])
    null_arr_mod = np.array([d_["modularity"] for d_ in null_descs])
    null_arr_gap = np.array([d_["spectral_gap"] for d_ in null_descs])
    null_planar_frac = float(np.mean([d_["is_planar"] for d_ in null_descs]))

    obs5 = obs_per_k[5]
    A_results = {
        "A.1_is_planar_at_k5": {
            "observed": bool(obs5["is_planar"]),
            "null_planar_fraction": null_planar_frac,
            "p_one_sided_planar_or_more": (
                null_planar_frac if obs5["is_planar"] else 1 - null_planar_frac
            ),
        },
        "A.2_clustering_coefficient_at_k5": {
            "observed": obs5["clustering_coefficient"],
            "null_median": float(np.median(null_arr_clust)),
            "null_std": float(null_arr_clust.std()),
            "p_two_sided": two_sided_p(obs5["clustering_coefficient"], null_arr_clust),
        },
        "A.3_modularity_at_k5": {
            "observed": obs5["modularity"],
            "null_median": float(np.median(null_arr_mod)),
            "null_std": float(null_arr_mod.std()),
            "p_two_sided": two_sided_p(obs5["modularity"], null_arr_mod),
        },
        "A.4_spectral_gap_at_k5": {
            "observed": obs5["spectral_gap"],
            "null_median": float(np.median(null_arr_gap)),
            "null_std": float(null_arr_gap.std()),
            "p_two_sided": two_sided_p(obs5["spectral_gap"], null_arr_gap),
        },
        "exploratory_other_k": {str(k): obs_per_k[k] for k in KNN_K_VALUES if k != 5},
    }

    # Render
    knn_png = out_dir / "sub_A_knn_graph_k5.png"
    try:
        _render_sub_A(X_white, build_knn_graph(X_white, 5), knn_png)
        knn_status = "ok"
    except Exception as e:
        knn_status = f"fail: {e}"
    A_results["png"] = str(knn_png)
    A_results["png_status"] = knn_status
    return A_results


def _render_sub_A(X_white: np.ndarray, G: nx.Graph, out_png: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    Xc = X_white - X_white.mean(axis=0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    pc = U[:, :2] * S[:2]
    fig, ax = plt.subplots(figsize=(11, 9))
    for u, v in G.edges():
        ax.plot([pc[u, 0], pc[v, 0]], [pc[u, 1], pc[v, 1]],
                "-", color="grey", lw=0.5, alpha=0.5)
    ax.scatter(pc[:, 0], pc[:, 1], c=np.arange(len(pc)),
               cmap="viridis", s=60, edgecolors="black", linewidths=0.5)
    for i in range(len(pc)):
        ax.annotate(str(i + 1), (pc[i, 0], pc[i, 1]),
                    fontsize=6, alpha=0.7)
    ax.set_xlabel("PC1 (whitened)")
    ax.set_ylabel("PC2 (whitened)")
    ax.set_title("Sub-A — 114-surah 5-NN graph (whitened Phi_M, 2D PCA projection)")
    fig.tight_layout()
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


# =========================================================================
#  Sub-B : Mushaf trajectory intrinsic descriptors
# =========================================================================

def trajectory_metrics(X_ord: np.ndarray) -> dict[str, float]:
    n = X_ord.shape[0]
    diffs = np.diff(X_ord, axis=0)
    seg = np.linalg.norm(diffs, axis=1)
    arc = float(seg.sum())
    end_to_end = float(np.linalg.norm(X_ord[-1] - X_ord[0]))
    closure = float(end_to_end / arc) if arc > 0 else float("nan")
    angles: list[float] = []
    for i in range(n - 2):
        v1 = diffs[i]; v2 = diffs[i + 1]
        n1 = float(np.linalg.norm(v1)); n2 = float(np.linalg.norm(v2))
        if n1 > 1e-12 and n2 > 1e-12:
            cos_t = float(np.clip((v1 @ v2) / (n1 * n2), -1.0, 1.0))
            angles.append(math.acos(cos_t))
    angles_arr = np.array(angles) if angles else np.array([0.0])
    bins, _ = np.histogram(angles_arr, bins=10, range=(0, math.pi))
    p = bins / max(bins.sum(), 1)
    p = p + 1e-12
    p = p / p.sum()
    uniform = np.ones_like(p) / p.size
    kl = float(np.sum(p * np.log(p / uniform)))
    return {"arc_length": arc, "closure_ratio": closure,
            "kl_divergence_to_uniform": kl}


def trajectory_self_intersections_2d(traj_2d: np.ndarray) -> int:
    """Count self-intersections of a 2-D polyline."""
    def segments_intersect(p1, p2, p3, p4):
        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
        return (ccw(p1, p3, p4) != ccw(p2, p3, p4)
                and ccw(p1, p2, p3) != ccw(p1, p2, p4))
    n = len(traj_2d)
    cnt = 0
    for i in range(n - 1):
        for j in range(i + 2, n - 1):
            if i == 0 and j == n - 2:
                continue  # share endpoints
            if segments_intersect(traj_2d[i], traj_2d[i + 1],
                                  traj_2d[j], traj_2d[j + 1]):
                cnt += 1
    return cnt


def run_sub_B(X_white: np.ndarray, rng: np.random.Generator,
              out_dir: Path) -> dict[str, Any]:
    n = X_white.shape[0]
    Xc = X_white - X_white.mean(axis=0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    pc2 = U[:, :2] * S[:2]
    mushaf = list(range(n))

    obs_metrics = trajectory_metrics(X_white[mushaf])
    obs_self_int = trajectory_self_intersections_2d(pc2[mushaf])

    print(f"  [B] running {N_PERMUTATIONS} random-permutation null ...")
    t1 = time.time()
    null_closure: list[float] = []
    null_self_int: list[int] = []
    null_kl: list[float] = []
    for k in range(N_PERMUTATIONS):
        perm = rng.permutation(n)
        m = trajectory_metrics(X_white[perm])
        null_closure.append(m["closure_ratio"])
        null_kl.append(m["kl_divergence_to_uniform"])
        null_self_int.append(trajectory_self_intersections_2d(pc2[perm]))
        if (k + 1) % 2000 == 0:
            print(f"    [B] perm {k + 1}/{N_PERMUTATIONS}  elapsed {time.time() - t1:.1f}s")
    print(f"  [B] perm done in {time.time() - t1:.1f} s")

    closure_arr = np.array(null_closure)
    kl_arr = np.array(null_kl)
    si_arr = np.array(null_self_int, dtype=np.float64)

    B_results = {
        "B.1_closure_ratio": {
            "observed": obs_metrics["closure_ratio"],
            "null_median": float(np.median(closure_arr)),
            "null_std": float(closure_arr.std()),
            "p_two_sided": two_sided_p(obs_metrics["closure_ratio"], closure_arr),
        },
        "B.2_self_intersection_count_2d": {
            "observed": int(obs_self_int),
            "null_median": float(np.median(si_arr)),
            "null_std": float(si_arr.std()),
            "p_two_sided": two_sided_p(float(obs_self_int), si_arr),
        },
        "B.3_kl_divergence_to_uniform": {
            "observed": obs_metrics["kl_divergence_to_uniform"],
            "null_median": float(np.median(kl_arr)),
            "null_std": float(kl_arr.std()),
            "p_two_sided": two_sided_p(obs_metrics["kl_divergence_to_uniform"], kl_arr),
        },
    }

    traj_png = out_dir / "sub_B_mushaf_trajectory.png"
    try:
        _render_sub_B(pc2, mushaf, obs_self_int, B_results, traj_png)
        traj_status = "ok"
    except Exception as e:
        traj_status = f"fail: {e}"
    B_results["png"] = str(traj_png)
    B_results["png_status"] = traj_status
    return B_results


def _render_sub_B(pc2: np.ndarray, mushaf: list[int],
                  obs_self_int: int, results: dict, out_png: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(11, 9))
    traj = pc2[mushaf]
    ax.plot(traj[:, 0], traj[:, 1], "-", lw=0.6, color="grey", alpha=0.7)
    sc = ax.scatter(traj[:, 0], traj[:, 1], c=np.arange(len(traj)),
                    cmap="viridis", s=40, edgecolors="black", linewidths=0.4)
    ax.scatter(traj[0, 0], traj[0, 1], color="red", s=180, marker="^",
               label="Q:1 (start)", zorder=10)
    ax.scatter(traj[-1, 0], traj[-1, 1], color="black", s=180, marker="s",
               label="Q:114 (end)", zorder=10)
    plt.colorbar(sc, ax=ax, label="surah index in Mushaf order")
    ax.set_xlabel("PC1 (whitened)")
    ax.set_ylabel("PC2 (whitened)")
    cl = results["B.1_closure_ratio"]
    si = results["B.2_self_intersection_count_2d"]
    kl = results["B.3_kl_divergence_to_uniform"]
    ax.set_title(
        "Sub-B — 114-surah Mushaf trajectory (whitened Phi_M, 2D PCA)\n"
        f"closure={cl['observed']:.3f} (p={cl['p_two_sided']:.4f}) | "
        f"self-int={si['observed']} (p={si['p_two_sided']:.4f}) | "
        f"KL_to_uniform={kl['observed']:.3f} (p={kl['p_two_sided']:.4f})"
    )
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


# =========================================================================
#  Sub-C : intrinsic dimension
# =========================================================================

def twonn_dim(X: np.ndarray) -> float:
    """TwoNN estimator (Facco et al. 2017): for each point, take ratio
    mu_i = r2_i / r1_i where r1, r2 are 1st and 2nd NN distances; fit
    -log(1 - F(mu)) = d * log(mu) on lower 90 % of points to get d."""
    n = X.shape[0]
    D = cdist(X, X)
    np.fill_diagonal(D, np.inf)
    s = np.sort(D, axis=1)
    r1 = s[:, 0]
    r2 = s[:, 1]
    mu = r2 / np.maximum(r1, 1e-12)
    mu = mu[mu > 1.0001]
    if mu.size < 10:
        return float("nan")
    mu_sorted = np.sort(mu)
    F = np.arange(1, mu_sorted.size + 1) / (mu_sorted.size + 1)
    cutoff = int(0.9 * mu_sorted.size)
    x = np.log(mu_sorted[:cutoff])
    y = -np.log(1 - F[:cutoff])
    slope = float(np.sum(x * y) / np.sum(x * x))  # forced through origin
    return slope


def correlation_dim(X: np.ndarray) -> float:
    """Grassberger-Procaccia correlation dimension on middle 50% of radius range."""
    n = X.shape[0]
    D = cdist(X, X)
    iu = np.triu_indices(n, k=1)
    pd = D[iu]
    pd = pd[pd > 0]
    if pd.size < 10:
        return float("nan")
    r_lo, r_hi = np.percentile(pd, 25), np.percentile(pd, 75)
    radii = np.geomspace(r_lo, r_hi, 20)
    C = np.array([(pd <= r).mean() for r in radii])
    valid = C > 0
    if valid.sum() < 4:
        return float("nan")
    log_r = np.log(radii[valid])
    log_C = np.log(C[valid])
    slope, _ = np.polyfit(log_r, log_C, 1)
    return float(slope)


def run_sub_C(X_white: np.ndarray, rng: np.random.Generator,
              out_dir: Path) -> dict[str, Any]:
    n, d = X_white.shape
    obs_twonn = twonn_dim(X_white)
    obs_corr = correlation_dim(X_white)

    print(f"  [C] generating {N_NULL_CLOUDS} random Gaussian d={d} clouds (n={n}) ...")
    t1 = time.time()
    null_twonn = np.zeros(N_NULL_CLOUDS)
    null_corr = np.zeros(N_NULL_CLOUDS)
    for k in range(N_NULL_CLOUDS):
        Xr = rng.standard_normal(size=(n, d))
        null_twonn[k] = twonn_dim(Xr)
        null_corr[k] = correlation_dim(Xr)
        if (k + 1) % 1000 == 0:
            print(f"    [C] null {k + 1}/{N_NULL_CLOUDS}  elapsed {time.time() - t1:.1f}s")
    print(f"  [C] null done in {time.time() - t1:.1f} s")

    twonn_finite = null_twonn[np.isfinite(null_twonn)]
    corr_finite = null_corr[np.isfinite(null_corr)]
    C_results = {
        "C.1_twonn_intrinsic_dim": {
            "observed": obs_twonn,
            "null_median": float(np.median(twonn_finite)),
            "null_std": float(twonn_finite.std()),
            "p_two_sided": two_sided_p(obs_twonn, twonn_finite),
            "ambient_dim": d,
        },
        "C.2_correlation_dim": {
            "observed": obs_corr,
            "null_median": float(np.median(corr_finite)),
            "null_std": float(corr_finite.std()),
            "p_two_sided": two_sided_p(obs_corr, corr_finite),
            "ambient_dim": d,
        },
    }

    dim_png = out_dir / "sub_C_intrinsic_dim.png"
    try:
        _render_sub_C(obs_twonn, obs_corr, twonn_finite, corr_finite, d, dim_png)
        dim_status = "ok"
    except Exception as e:
        dim_status = f"fail: {e}"
    C_results["png"] = str(dim_png)
    C_results["png_status"] = dim_status
    return C_results


def _render_sub_C(obs_twonn: float, obs_corr: float,
                  null_twonn: np.ndarray, null_corr: np.ndarray,
                  ambient_dim: int, out_png: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    ax = axes[0]
    ax.hist(null_twonn, bins=40, alpha=0.6, color="grey",
            label=f"null (Gaussian d={ambient_dim})")
    ax.axvline(obs_twonn, color="red", lw=2,
               label=f"Quran obs = {obs_twonn:.2f}")
    ax.axvline(ambient_dim, color="black", lw=1, linestyle="--",
               label=f"ambient dim = {ambient_dim}")
    ax.set_xlabel("intrinsic dimension (TwoNN)")
    ax.set_ylabel("null count")
    ax.set_title(f"Sub-C.1 — TwoNN intrinsic dim\n"
                 f"obs = {obs_twonn:.3f}, null median = {np.median(null_twonn):.3f}")
    ax.legend()
    ax = axes[1]
    ax.hist(null_corr, bins=40, alpha=0.6, color="grey",
            label=f"null (Gaussian d={ambient_dim})")
    ax.axvline(obs_corr, color="red", lw=2, label=f"Quran obs = {obs_corr:.2f}")
    ax.axvline(ambient_dim, color="black", lw=1, linestyle="--",
               label=f"ambient dim = {ambient_dim}")
    ax.set_xlabel("correlation dimension (Grassberger-Procaccia)")
    ax.set_ylabel("null count")
    ax.set_title(f"Sub-C.2 — Correlation dim\n"
                 f"obs = {obs_corr:.3f}, null median = {np.median(null_corr):.3f}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


# =========================================================================
#  Sub-D : Mushaf-ordered verse-count FFT spectrum
# =========================================================================

def fft_descriptors(seq: np.ndarray) -> dict[str, float]:
    """Compute FFT descriptors of a 1-D sequence (after demeaning)."""
    n = len(seq)
    x = seq.astype(np.float64) - seq.mean()
    X = np.fft.rfft(x)
    power = np.abs(X) ** 2
    if len(power) <= 1:
        return {k: float("nan") for k in (
            "peak_freq_period", "peak_power_ratio",
            "power_at_period_19", "power_at_period_7",
        )}
    p_nondc = power[1:]
    if p_nondc.size == 0 or p_nondc.sum() == 0:
        return {k: float("nan") for k in (
            "peak_freq_period", "peak_power_ratio",
            "power_at_period_19", "power_at_period_7",
        )}
    peak_idx = int(np.argmax(p_nondc)) + 1   # absolute index in power
    peak_period = float(n / peak_idx) if peak_idx > 0 else float("nan")
    peak_ratio = float(power[peak_idx] / p_nondc.mean())
    # Map period 19 -> closest non-DC bin; period = n/k, k=round(n/period)
    k19 = max(1, int(round(n / 19)))
    k7 = max(1, int(round(n / 7)))
    pp19 = float(power[k19] if k19 < len(power) else 0.0)
    pp7 = float(power[k7] if k7 < len(power) else 0.0)
    norm_total = float(p_nondc.sum())
    return {
        "peak_freq_period": peak_period,
        "peak_power_ratio": peak_ratio,
        "power_at_period_19": pp19 / norm_total,
        "power_at_period_7": pp7 / norm_total,
    }


def run_sub_D(verse_counts: np.ndarray, rng: np.random.Generator,
              out_dir: Path) -> dict[str, Any]:
    n = len(verse_counts)
    obs = fft_descriptors(verse_counts)

    print(f"  [D] running {N_PERMUTATIONS} random-permutation null ...")
    t1 = time.time()
    null_peak_period = np.zeros(N_PERMUTATIONS)
    null_peak_ratio = np.zeros(N_PERMUTATIONS)
    null_p19 = np.zeros(N_PERMUTATIONS)
    null_p7 = np.zeros(N_PERMUTATIONS)
    for k in range(N_PERMUTATIONS):
        perm = rng.permutation(n)
        m = fft_descriptors(verse_counts[perm])
        null_peak_period[k] = m["peak_freq_period"]
        null_peak_ratio[k] = m["peak_power_ratio"]
        null_p19[k] = m["power_at_period_19"]
        null_p7[k] = m["power_at_period_7"]
        if (k + 1) % 2500 == 0:
            print(f"    [D] perm {k + 1}/{N_PERMUTATIONS}  elapsed {time.time() - t1:.1f}s")
    print(f"  [D] perm done in {time.time() - t1:.1f} s")

    D_results = {
        "D.1_peak_freq_period": {
            "observed": obs["peak_freq_period"],
            "null_median": float(np.median(null_peak_period[np.isfinite(null_peak_period)])),
            "null_std": float(null_peak_period[np.isfinite(null_peak_period)].std()),
            "p_two_sided": two_sided_p(obs["peak_freq_period"], null_peak_period),
        },
        "D.2_peak_power_ratio": {
            "observed": obs["peak_power_ratio"],
            "null_median": float(np.median(null_peak_ratio)),
            "null_std": float(null_peak_ratio.std()),
            "p_two_sided": two_sided_p(obs["peak_power_ratio"], null_peak_ratio),
        },
        "D.3_power_at_period_19": {
            "observed": obs["power_at_period_19"],
            "null_median": float(np.median(null_p19)),
            "null_std": float(null_p19.std()),
            "p_two_sided": two_sided_p(obs["power_at_period_19"], null_p19),
        },
        "D.4_power_at_period_7": {
            "observed": obs["power_at_period_7"],
            "null_median": float(np.median(null_p7)),
            "null_std": float(null_p7.std()),
            "p_two_sided": two_sided_p(obs["power_at_period_7"], null_p7),
        },
    }

    spec_png = out_dir / "sub_D_verse_spectrum.png"
    try:
        _render_sub_D(verse_counts, obs, D_results, spec_png)
        spec_status = "ok"
    except Exception as e:
        spec_status = f"fail: {e}"
    D_results["png"] = str(spec_png)
    D_results["png_status"] = spec_status
    return D_results


def _render_sub_D(verse_counts: np.ndarray, obs: dict,
                  D_results: dict, out_png: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = len(verse_counts)
    x = verse_counts.astype(np.float64) - verse_counts.mean()
    X = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, d=1.0)
    power = np.abs(X) ** 2
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    ax = axes[0]
    ax.plot(np.arange(1, n + 1), verse_counts, "-o", markersize=4)
    ax.set_xlabel("Surah index (Mushaf order)")
    ax.set_ylabel("Verse count")
    ax.set_title(f"Mushaf-ordered verse-count sequence (n={n})")
    ax.grid(True, alpha=0.3)
    ax = axes[1]
    periods = np.where(freqs > 0, 1.0 / freqs, np.nan)
    ax.plot(periods[1:], power[1:], "-")
    for label, idx_period, color in (
        ("period 19", 19, "green"), ("period 7", 7, "orange"),
        (f"obs peak {obs['peak_freq_period']:.1f}",
         obs["peak_freq_period"], "red"),
    ):
        ax.axvline(idx_period, color=color, lw=1.5, linestyle="--", label=label)
    ax.set_xlabel("Period (in surahs)")
    ax.set_ylabel("FFT power |X(f)|^2")
    ax.set_xlim(2, n / 2)
    ax.set_xscale("log")
    ax.set_yscale("log")
    p7 = D_results["D.4_power_at_period_7"]
    p19 = D_results["D.3_power_at_period_19"]
    pk = D_results["D.2_peak_power_ratio"]
    ax.set_title(
        f"FFT spectrum    p_period_7={p7['p_two_sided']:.3f}    "
        f"p_period_19={p19['p_two_sided']:.3f}    "
        f"p_peak_ratio={pk['p_two_sided']:.3f}"
    )
    ax.grid(True, alpha=0.3)
    ax.legend()
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

    X_full = per_surah_matrix_in_mushaf_order(state)
    verse_counts = per_surah_verse_counts(state)
    print(f"[{EXP}] X_full.shape = {X_full.shape}, "
          f"verse_counts: min={verse_counts.min()} max={verse_counts.max()} "
          f"sum={verse_counts.sum()}")

    X_white = whitening_transform(X_full)
    cov_post = np.cov(X_white, rowvar=False)
    isotropy_err = float(np.linalg.norm(cov_post - np.eye(5)) / np.sqrt(5))
    print(f"[{EXP}] post-whitening isotropy error = {isotropy_err:.2e}")

    audit = {
        "A1_n_quran": int(X_full.shape[0]),
        "A1_pass": X_full.shape[0] == 114,
        "A2_isotropy_err": isotropy_err,
        "A2_pass": isotropy_err < 1e-6,
        "A3_total_verses": int(verse_counts.sum()),
        "A3_check_canonical_6236": int(verse_counts.sum()) == 6236,
        "A3_min_verse_count": int(verse_counts.min()),
        "A3_max_verse_count": int(verse_counts.max()),
    }
    print(f"[{EXP}] audit: {audit}")

    print(f"\n[{EXP}] === Sub-A: k-NN graph topology ===")
    A = run_sub_A(X_white, rng, out_dir)

    print(f"\n[{EXP}] === Sub-B: Mushaf trajectory descriptors ===")
    B = run_sub_B(X_white, rng, out_dir)

    print(f"\n[{EXP}] === Sub-C: intrinsic dimension ===")
    C = run_sub_C(X_white, rng, out_dir)

    print(f"\n[{EXP}] === Sub-D: verse-count spectrum ===")
    D = run_sub_D(verse_counts, rng, out_dir)

    # Family-wise BHL across 13 frozen tests
    p_named: list[tuple[str, float]] = []
    p_named.append(("A.1_is_planar_at_k5", float(A["A.1_is_planar_at_k5"]["p_one_sided_planar_or_more"])))
    for k in ("A.2_clustering_coefficient_at_k5", "A.3_modularity_at_k5",
              "A.4_spectral_gap_at_k5"):
        p_named.append((k, float(A[k]["p_two_sided"])))
    for k in ("B.1_closure_ratio", "B.2_self_intersection_count_2d",
              "B.3_kl_divergence_to_uniform"):
        p_named.append((k, float(B[k]["p_two_sided"])))
    for k in ("C.1_twonn_intrinsic_dim", "C.2_correlation_dim"):
        p_named.append((k, float(C[k]["p_two_sided"])))
    for k in ("D.1_peak_freq_period", "D.2_peak_power_ratio",
              "D.3_power_at_period_19", "D.4_power_at_period_7"):
        p_named.append((k, float(D[k]["p_two_sided"])))

    bhl_survivors = bonferroni_holm(p_named, ALPHA_BHL)
    nominal_significant = [n for n, p in p_named if np.isfinite(p) and p < 0.05]

    sub_families_with_bhl: set[str] = set()
    for s in bhl_survivors:
        sub_families_with_bhl.add(s.split(".", 1)[0])

    if len(bhl_survivors) >= 2 and len(sub_families_with_bhl) >= 2:
        verdict = "PASS_QURAN_INTRINSIC_GEOMETRY_DISTINCT"
    elif len(bhl_survivors) >= 1:
        verdict = "PARTIAL_INTRINSIC_GEOMETRY_PRESENT"
    elif len(nominal_significant) >= 2:
        verdict = "PARTIAL_NOMINAL_p05_NOT_BHL"
    else:
        verdict = "FAIL_NO_INTRINSIC_GEOMETRIC_STRUCTURE"

    receipt: dict[str, Any] = {
        "experiment": EXP,
        "schema_version": 1,
        "hypothesis": (
            "The 114-surah Quran point cloud, examined intrinsically against "
            "random nulls of the same n (NOT against control corpora), has "
            "at least 2 BHL-significant geometric/topological properties "
            "across at least 2 sub-families (k-NN graph, trajectory, "
            "intrinsic-dim, FFT spectrum) at family-wise alpha = 0.01 over "
            "13 tests."
        ),
        "verdict": verdict,
        "completed_at_utc": completed_at_utc,
        "wall_time_s": float(time.time() - t0),
        "frozen_constants": {
            "SEED": SEED, "N_NULL_CLOUDS": N_NULL_CLOUDS,
            "N_PERMUTATIONS": N_PERMUTATIONS, "ALPHA_BHL": ALPHA_BHL,
            "FEAT_COLS": FEAT_COLS, "KNN_K_VALUES": KNN_K_VALUES,
        },
        "audit_hooks": audit,
        "sub_A_knn_graph": A,
        "sub_B_trajectory": B,
        "sub_C_intrinsic_dim": C,
        "sub_D_verse_spectrum": D,
        "all_p_values": dict(p_named),
        "bhl_survivors": bhl_survivors,
        "nominal_significant_p_lt_05": nominal_significant,
        "n_bhl_survivors": len(bhl_survivors),
        "n_sub_families_with_bhl_survivors": len(sub_families_with_bhl),
    }
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    print("\n" + "=" * 72)
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  BHL survivors ({len(bhl_survivors)}/13): {bhl_survivors}")
    print(f"  nominal p<0.05 ({len(nominal_significant)}/13): {nominal_significant}")
    print(f"  sub-families with BHL: {sub_families_with_bhl}")
    print(f"  wall-time = {receipt['wall_time_s']:.1f} s")
    print(f"  receipt: {out_path}")
    print("=" * 72)
    return receipt


if __name__ == "__main__":
    main()
