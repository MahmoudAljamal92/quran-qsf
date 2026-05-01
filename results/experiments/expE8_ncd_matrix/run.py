"""
expE8_ncd_matrix — 114 x 114 gzip Normalised Compression Distance matrix for
all surah-surah pairs in the canonical Mushaf.

PRE-REGISTRATION (set before execution):
  Null hypotheses:
      (H0-a) NCD(i,j) is uncorrelated with |i-j| (mushaf-order Mantel test).
      (H0-b) Meccan-Meccan and Medinan-Medinan NCD means equal Meccan-Medinan
             NCD means (era-block permutation test).
      (H0-c) Hierarchical clustering silhouette width = shuffle baseline.
  Pass conditions:
      At least one of the three null hypotheses rejected at alpha=0.01 with
      1000 permutations; report effect sizes.
  Side effects:
      No mutation of pinned artefacts; outputs under expE8 folder only.
  Seed:
      NUMPY_SEED = 42.
"""
from __future__ import annotations

import gzip
import json
import pickle
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from sklearn.metrics import silhouette_score

warnings.filterwarnings("ignore")

ROOT = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUTDIR = ROOT / "results" / "experiments" / "expE8_ncd_matrix"
OUTDIR.mkdir(parents=True, exist_ok=True)

SEED = 42
N_PERM = 1000
RNG = np.random.default_rng(SEED)

MEDINAN = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 55, 57, 58, 59, 60, 61,
           62, 63, 64, 65, 66, 76, 98, 99, 110, 113}

# --------------------------------------------------------------- LOAD
sys.path.insert(0, str(ROOT))
t0 = time.time()
state = pickle.load(open(ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl", "rb"))["state"]
quran_units = state["CORPORA"]["quran"]

surah_texts: list[bytes] = []
for u in quran_units:
    # joined with newlines — preserves verse boundaries so gzip sees verse structure
    surah_texts.append("\n".join(u.verses).encode("utf-8"))
print(f"Loaded in {time.time()-t0:.2f}s — {len(surah_texts)} surahs, "
      f"total bytes={sum(len(b) for b in surah_texts):,}")

# --------------------------------------------------------------- NCD
def _csize(b: bytes, level: int = 9) -> int:
    return len(gzip.compress(b, compresslevel=level))

print("\nPre-computing individual compressed sizes ...")
C = np.array([_csize(b) for b in surah_texts], dtype=float)
print(f"  C range: {C.min():,.0f} .. {C.max():,.0f} bytes "
      f"(median={np.median(C):,.0f})")

print(f"\nComputing 114x114 NCD matrix ({114*113//2:,} unique pairs) ...")
t = time.time()
NCD = np.zeros((114, 114), dtype=float)
for i in range(114):
    for j in range(i + 1, 114):
        Cij = _csize(surah_texts[i] + b"\n" + surah_texts[j])
        d = (Cij - min(C[i], C[j])) / max(C[i], C[j])
        NCD[i, j] = NCD[j, i] = d
    if (i + 1) % 20 == 0:
        print(f"  row {i+1}/114 in {time.time()-t:.1f}s")
print(f"  done in {time.time()-t:.1f}s")

# sanity
assert np.allclose(NCD, NCD.T)
off = NCD[np.triu_indices(114, k=1)]
print(f"  NCD off-diagonal: min={off.min():.3f}, max={off.max():.3f}, "
      f"mean={off.mean():.3f}, median={np.median(off):.3f}")

# --------------------------------------------------------------- MANTEL
def mantel_test(A: np.ndarray, B: np.ndarray, n_perm: int, seed: int = 0) -> dict:
    assert A.shape == B.shape and A.shape[0] == A.shape[1]
    n = A.shape[0]
    tri = np.triu_indices(n, k=1)
    a = A[tri]; b = B[tri]
    r_obs = float(np.corrcoef(a, b)[0, 1])
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm)
    for k in range(n_perm):
        perm = rng.permutation(n)
        Bp = B[np.ix_(perm, perm)]
        null[k] = float(np.corrcoef(a, Bp[tri])[0, 1])
    p = float(((np.abs(null) >= abs(r_obs)).sum() + 1) / (n_perm + 1))  # two-sided
    return {"r": r_obs, "null_mean": float(null.mean()),
            "null_sd": float(null.std()), "p_two_sided": p}

# Order-distance matrix D_ord[i,j] = |i-j|
ix = np.arange(114)
D_ord = np.abs(ix[:, None] - ix[None, :]).astype(float)

# Era adjacency: D_era[i,j] = 0 if same era, 1 else
era = np.array([1 if (i + 1) in MEDINAN else 0 for i in range(114)])
D_era = (era[:, None] != era[None, :]).astype(float)

print(f"\nMantel test NCD vs mushaf-order distance (|i-j|) "
      f"with {N_PERM} permutations ...")
t = time.time()
mantel_order = mantel_test(NCD, D_ord, n_perm=N_PERM, seed=SEED)
print(f"  r={mantel_order['r']:+.4f}, "
      f"null={mantel_order['null_mean']:+.4f}+-{mantel_order['null_sd']:.4f}, "
      f"p={mantel_order['p_two_sided']:.4f}, {time.time()-t:.1f}s")

print(f"Mantel test NCD vs era-difference ({N_PERM} permutations) ...")
t = time.time()
mantel_era = mantel_test(NCD, D_era, n_perm=N_PERM, seed=SEED + 1)
print(f"  r={mantel_era['r']:+.4f}, "
      f"null={mantel_era['null_mean']:+.4f}+-{mantel_era['null_sd']:.4f}, "
      f"p={mantel_era['p_two_sided']:.4f}, {time.time()-t:.1f}s")

# --------------------------------------------------------------- Era block test
tri_ix = np.triu_indices(114, k=1)
era_pair = (era[tri_ix[0]] != era[tri_ix[1]])
within = off[~era_pair]
between = off[era_pair]
obs_diff = float(between.mean() - within.mean())

print(f"\nEra-block permutation test (within vs between means):")
print(f"  mean NCD within-era:  {within.mean():.4f} (n={len(within)})")
print(f"  mean NCD between-era: {between.mean():.4f} (n={len(between)})")
print(f"  obs diff (between - within): {obs_diff:+.5f}")

null_diffs = np.empty(N_PERM)
for k in range(N_PERM):
    era_p = RNG.permutation(era)
    ep = (era_p[tri_ix[0]] != era_p[tri_ix[1]])
    null_diffs[k] = off[ep].mean() - off[~ep].mean()
p_era_block = float(((np.abs(null_diffs) >= abs(obs_diff)).sum() + 1) / (N_PERM + 1))
print(f"  null_diff mean={null_diffs.mean():+.5f}, sd={null_diffs.std():.5f}, "
      f"p={p_era_block:.4f}")

# --------------------------------------------------------------- Hier clustering
print("\nHierarchical clustering (average linkage) + silhouette vs era labels")
Z = linkage(squareform(NCD, checks=False), method="average")
# Cluster into 2 for comparison with Meccan/Medinan
labels_2 = fcluster(Z, t=2, criterion="maxclust")
# silhouette with pre-computed NCD (sklearn wants (n, n) + metric="precomputed")
sil_era_obs = float(silhouette_score(NCD, era, metric="precomputed"))
sil_cluster = float(silhouette_score(NCD, labels_2, metric="precomputed"))
print(f"  silhouette(era=Meccan/Medinan, NCD) = {sil_era_obs:+.4f}")
print(f"  silhouette(hier-cluster-2, NCD)     = {sil_cluster:+.4f}")

sil_null = np.empty(N_PERM)
for k in range(N_PERM):
    sil_null[k] = silhouette_score(NCD, RNG.permutation(era), metric="precomputed")
p_sil_era = float(((sil_null >= sil_era_obs).sum() + 1) / (N_PERM + 1))
print(f"  shuffle-null silhouette: mean={sil_null.mean():+.4f}, "
      f"sd={sil_null.std():.4f}, one-sided p (era >= null) = {p_sil_era:.4f}")

# --------------------------------------------------------------- Verdict
any_sig = [
    mantel_order["p_two_sided"] < 0.01,
    mantel_era["p_two_sided"] < 0.01,
    p_era_block < 0.01,
    p_sil_era < 0.01,
]
n_sig = int(sum(any_sig))
if n_sig >= 2:
    verdict = "STRUCTURED_NCD"
elif n_sig == 1:
    verdict = "PARTIAL_STRUCTURE"
else:
    verdict = "NULL_NO_STRUCTURE"

# --------------------------------------------------------------- Outputs
np.savez_compressed(OUTDIR / "expE8_ncd_matrix.npz",
                    NCD=NCD, C_indiv=C, era=era, mushaf_order=ix)

report = {
    "experiment_id": "expE8_ncd_matrix",
    "task": "E8",
    "tier": 2,
    "title": "114x114 gzip-NCD block-pair distance matrix",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "seed": SEED,
    "n_perm": N_PERM,
    "compression": {"alg": "gzip", "level": 9},
    "n_surahs": 114,
    "total_input_bytes": int(sum(len(b) for b in surah_texts)),
    "C_individual_stats": {
        "min":    float(C.min()),
        "max":    float(C.max()),
        "median": float(np.median(C)),
        "mean":   float(C.mean()),
    },
    "NCD_off_diag_stats": {
        "min":    float(off.min()),
        "max":    float(off.max()),
        "mean":   float(off.mean()),
        "median": float(np.median(off)),
        "sd":     float(off.std()),
    },
    "mantel_order":    mantel_order,
    "mantel_era":      mantel_era,
    "era_block": {
        "mean_within":  float(within.mean()),
        "mean_between": float(between.mean()),
        "obs_diff":     obs_diff,
        "null_mean":    float(null_diffs.mean()),
        "null_sd":      float(null_diffs.std()),
        "p_two_sided":  p_era_block,
    },
    "silhouette_era": {
        "sil_obs":     sil_era_obs,
        "null_mean":   float(sil_null.mean()),
        "null_sd":     float(sil_null.std()),
        "p_one_sided": p_sil_era,
    },
    "hier_cluster_silhouette": sil_cluster,
    "verdict": verdict,
    "pre_registered_criteria": {
        "STRUCTURED_NCD":    ">=2 of 4 nulls rejected at alpha=0.01",
        "PARTIAL_STRUCTURE": "exactly 1 of 4 nulls rejected",
        "NULL_NO_STRUCTURE": "no nulls rejected",
    },
}
(OUTDIR / "expE8_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
)

# --------------------------------------------------------------- Plots
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# NCD heatmap
fig, ax = plt.subplots(figsize=(9, 8))
im = ax.imshow(NCD, cmap="viridis", vmin=off.min(), vmax=off.max())
ax.set_xlabel("surah j"); ax.set_ylabel("surah i")
ax.set_title(f"expE8 — 114×114 gzip-NCD matrix "
             f"(mean off-diag = {off.mean():.3f})")
fig.colorbar(im, ax=ax, label="NCD")
fig.tight_layout()
fig.savefig(OUTDIR / "expE8_ncd_heatmap.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# NCD vs |i-j| scatter
fig, ax = plt.subplots(figsize=(8, 5))
d_ord_flat = D_ord[tri_ix]
ax.scatter(d_ord_flat, off, s=3, alpha=0.25, c="C0")
ax.set_xlabel("mushaf-order distance |i-j|")
ax.set_ylabel("gzip-NCD")
ax.set_title(f"expE8 — NCD vs mushaf order\nMantel r={mantel_order['r']:+.4f}, "
             f"p={mantel_order['p_two_sided']:.4f}")
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(OUTDIR / "expE8_ncd_vs_order.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --------------------------------------------------------------- MD
md = [
    "# expE8 — 114×114 gzip Normalised Compression Distance (NCD) matrix",
    "",
    f"**Generated (UTC)**: {report['generated_utc']}",
    f"**Seed**: {SEED}  |  **Permutations per test**: {N_PERM}  |  **Compression**: gzip level 9",
    "",
    "## Pre-registration (set before execution)",
    "",
    "- **H0-a (Mantel order)**: NCD uncorrelated with |i-j|.",
    "- **H0-b (Era block)**: Mean NCD within-era == between-era.",
    "- **H0-c (Silhouette)**: Era label silhouette inside shuffle-null CI.",
    "- **STRUCTURED_NCD**: ≥ 2 of 4 nulls rejected at α = 0.01.",
    "",
    f"## Verdict — **{verdict}** (n significant = {n_sig} / 4)",
    "",
    "## NCD matrix summary",
    "",
    f"- **Off-diagonal**: min = {off.min():.3f}, max = {off.max():.3f}, "
    f"mean = {off.mean():.3f}, median = {np.median(off):.3f}, sd = {off.std():.3f}",
    f"- **Compressed sizes**: median = {np.median(C):,.0f} bytes (min {C.min():,.0f}, max {C.max():,.0f})",
    "",
    "## Null-hypothesis tests",
    "",
    "| Test | Statistic | Obs | Null mean | Null sd | p | Reject α=0.01 |",
    "|---|---|--:|--:|--:|--:|:-:|",
    f"| H0-a Mantel vs mushaf order  | r | {mantel_order['r']:+.4f} | "
    f"{mantel_order['null_mean']:+.4f} | {mantel_order['null_sd']:.4f} | "
    f"{mantel_order['p_two_sided']:.4f} | {'YES' if mantel_order['p_two_sided']<0.01 else 'no'} |",
    f"| H0-a Mantel vs era adjacency | r | {mantel_era['r']:+.4f} | "
    f"{mantel_era['null_mean']:+.4f} | {mantel_era['null_sd']:.4f} | "
    f"{mantel_era['p_two_sided']:.4f} | {'YES' if mantel_era['p_two_sided']<0.01 else 'no'} |",
    f"| H0-b Era block diff (between − within) | Δ | {obs_diff:+.5f} | "
    f"{null_diffs.mean():+.5f} | {null_diffs.std():.5f} | "
    f"{p_era_block:.4f} | {'YES' if p_era_block<0.01 else 'no'} |",
    f"| H0-c Era silhouette (one-sided) | s | {sil_era_obs:+.4f} | "
    f"{sil_null.mean():+.4f} | {sil_null.std():.4f} | "
    f"{p_sil_era:.4f} | {'YES' if p_sil_era<0.01 else 'no'} |",
    "",
    f"## Hierarchical clustering (average linkage, 2 clusters): silhouette = {sil_cluster:+.4f}",
    "",
    "## Outputs",
    "",
    "- `expE8_ncd_matrix.npz` — 114×114 NCD matrix + per-surah C sizes + metadata",
    "- `expE8_report.json` — all null-test numbers + verdict",
    "- `expE8_ncd_heatmap.png` — colour heatmap",
    "- `expE8_ncd_vs_order.png` — NCD vs |i-j| scatter + Mantel r",
]
(OUTDIR / "expE8_report.md").write_text("\n".join(md), encoding="utf-8")

print(f"\nVerdict: {verdict}  ({n_sig}/4 nulls rejected at α=0.01)")
print(f"Outputs in {OUTDIR}")
print(f"Total runtime: {time.time()-t0:.1f}s")
