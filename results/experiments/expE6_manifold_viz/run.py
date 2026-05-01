"""
expE6_manifold_viz — 2-D embeddings of the 114×5 Quran feature matrix in
(EL, VL_CV, CN, H_cond, T) space, z-scored against the 2509-unit Arabic
control pool.  First picture of the Mushaf trajectory.

PRE-REGISTRATION (set before execution):
  Null hypothesis:
      Moran's I along mushaf order and silhouette for Meccan/Medinan label
      both sit inside the 95% confidence band of 1000 label shuffles.
  Pass condition:
      Moran's I p < 0.05   OR   silhouette p < 0.05 (one-sided, label shuffle).
      If both pass → POSITIVE structure; if one passes → PARTIAL.
  Side effects:
      No mutation of any pinned artefact. Outputs under expE6 folder only.
  Seed:
      NUMPY_SEED = 42.
"""
from __future__ import annotations

import json
import pickle
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE, Isomap
from sklearn.metrics import silhouette_score

warnings.filterwarnings("ignore")

ROOT = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUTDIR = ROOT / "results" / "experiments" / "expE6_manifold_viz"
OUTDIR.mkdir(parents=True, exist_ok=True)

SEED = 42
N_SHUFFLES = 1000
RNG = np.random.default_rng(SEED)

# Al-Azhar canonical Meccan/Medinan classification (28 Medinan).
MEDINAN = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 55, 57, 58, 59, 60, 61,
           62, 63, 64, 65, 66, 76, 98, 99, 110, 113}

# --------------------------------------------------------------- LOAD
sys.path.insert(0, str(ROOT))
t0 = time.time()
state = pickle.load(open(ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl", "rb"))["state"]
FEAT_COLS = state["FEAT_COLS"]
q_feats = state["FEATS"]["quran"]
assert len(q_feats) == 114 and FEAT_COLS == ["EL", "VL_CV", "CN", "H_cond", "T"]

X_q = np.array([[f[c] for c in FEAT_COLS] for f in q_feats], dtype=float)  # (114, 5)

# Build control-pool matrix from the same 6 Arabic control corpora as §4.36
ARABIC_CTRL = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
               "ksucca", "arabic_bible", "hindawi"]
X_ctrl_rows = []
for name in ARABIC_CTRL:
    for f in state["FEATS"][name]:
        X_ctrl_rows.append([f[c] for c in FEAT_COLS])
X_ctrl = np.array(X_ctrl_rows, dtype=float)
assert X_ctrl.shape[1] == 5

# Z-score vs control pool (not vs global) — as in §4.36 protocol
mu = X_ctrl.mean(axis=0)
sd = X_ctrl.std(axis=0, ddof=1)
sd[sd == 0] = 1.0
X_qz = (X_q - mu) / sd

# Surah metadata
n_verses = np.array([f["n_verses"] for f in q_feats])
n_words  = np.array([f["n_words"]  for f in q_feats])
surah_ix = np.arange(1, 115)
is_medinan = np.array([s in MEDINAN for s in surah_ix])
era_labels = np.where(is_medinan, "Medinan", "Meccan")

print(f"Loaded in {time.time()-t0:.2f}s — X_q={X_qz.shape}, X_ctrl={X_ctrl.shape}")
print(f"  Medinan = {int(is_medinan.sum())}, Meccan = {int((~is_medinan).sum())}")

# --------------------------------------------------------------- EMBEDDINGS
t = time.time()
pca2 = PCA(n_components=2, random_state=SEED).fit(X_qz)
Y_pca = pca2.transform(X_qz)
explained_var = pca2.explained_variance_ratio_

tsne = TSNE(n_components=2, perplexity=15, random_state=SEED, init="pca", learning_rate="auto")
Y_tsne = tsne.fit_transform(X_qz)

# Isomap replaces UMAP (not installed)
iso = Isomap(n_components=2, n_neighbors=10).fit(X_qz)
Y_iso = iso.transform(X_qz)

print(f"Embeddings computed in {time.time()-t:.2f}s — PCA var={explained_var.sum():.3f}")

# --------------------------------------------------------------- STATISTICS
def morans_I(Y: np.ndarray) -> float:
    """Moran's I along the 1-D mushaf order: adjacency-weight matrix W[i,j]=1
    iff |i-j|=1 (standard rook contiguity on a chain)."""
    n = len(Y)
    W = np.zeros((n, n))
    for i in range(n - 1):
        W[i, i + 1] = W[i + 1, i] = 1.0
    S0 = W.sum()
    Yc = Y - Y.mean(axis=0, keepdims=True)
    num = 0.0
    den = (Yc ** 2).sum()
    for i in range(n):
        for j in range(n):
            num += W[i, j] * np.dot(Yc[i], Yc[j])
    return float((n / S0) * num / max(den, 1e-12))

def stats_for(Y: np.ndarray, name: str) -> dict:
    t = time.time()
    I_obs = morans_I(Y)
    # Silhouette coefficient for Meccan/Medinan labels (label unchanged, points Y)
    sil_obs = float(silhouette_score(Y, era_labels, metric="euclidean"))

    # --- Moran's I null: shuffle the order of surahs (relabels positions)
    I_null = np.empty(N_SHUFFLES)
    sil_null = np.empty(N_SHUFFLES)
    for i in range(N_SHUFFLES):
        perm = RNG.permutation(len(Y))
        I_null[i] = morans_I(Y[perm])
        # Silhouette null: shuffle era labels
        sil_null[i] = silhouette_score(Y, RNG.permutation(era_labels), metric="euclidean")

    p_I = (I_null >= I_obs).mean()                         # one-sided (clustering)
    p_sil = (sil_null >= sil_obs).mean()

    out = {
        "embedding":    name,
        "morans_I":     I_obs,
        "morans_I_null_mean": float(I_null.mean()),
        "morans_I_null_sd":   float(I_null.std()),
        "morans_I_p":   float(p_I),
        "silhouette":   sil_obs,
        "silhouette_null_mean": float(sil_null.mean()),
        "silhouette_null_sd":   float(sil_null.std()),
        "silhouette_p": float(p_sil),
        "sec":          time.time() - t,
    }
    print(f"  {name:>5}: I={I_obs:+.4f} (p={p_I:.3f}), "
          f"sil={sil_obs:+.4f} (p={p_sil:.3f})")
    return out

print("\nPermutation tests for spatial autocorrelation + era clustering:")
stats = {
    "PCA":   stats_for(Y_pca,  "PCA"),
    "TSNE":  stats_for(Y_tsne, "TSNE"),
    "ISO":   stats_for(Y_iso,  "ISO"),
}

# --------------------------------------------------------------- VERDICT
n_sig_I   = sum(1 for v in stats.values() if v["morans_I_p"]   < 0.05)
n_sig_sil = sum(1 for v in stats.values() if v["silhouette_p"] < 0.05)

if n_sig_I >= 2 and n_sig_sil >= 2:
    verdict = "POSITIVE_STRUCTURE"
elif n_sig_I >= 2 or n_sig_sil >= 2:
    verdict = "PARTIAL_STRUCTURE"
elif n_sig_I >= 1 or n_sig_sil >= 1:
    verdict = "WEAK_STRUCTURE"
else:
    verdict = "NULL_NO_STRUCTURE"

# --------------------------------------------------------------- OUTPUTS
report = {
    "experiment_id": "expE6_manifold_viz",
    "task": "E6",
    "tier": 2,
    "title": "2-D embeddings of 114x5 Quran feature matrix with Moran's I + silhouette tests",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "seed": SEED,
    "n_shuffles": N_SHUFFLES,
    "embeddings": ["PCA", "TSNE", "Isomap"],
    "note_umap": "UMAP not installed — replaced by Isomap (sklearn) as non-linear embedding",
    "inputs": {
        "source": "phase_06_phi_m.pkl state['FEATS']",
        "features": FEAT_COLS,
        "n_quran_units": int(len(X_q)),
        "n_ctrl_units": int(len(X_ctrl)),
        "arabic_ctrl_families": ARABIC_CTRL,
        "z_score_ref": "Arabic control pool mean/sd (matches §4.36 protocol)",
    },
    "medinan_surahs_count": int(is_medinan.sum()),
    "meccan_surahs_count":  int((~is_medinan).sum()),
    "pca_explained_variance_ratio": explained_var.tolist(),
    "stats": stats,
    "verdict": verdict,
    "pre_registered_criteria": {
        "null": "Moran's I and silhouette inside 95% CI of 1000 label shuffles",
        "POSITIVE_STRUCTURE": "Moran's I p<0.05 AND silhouette p<0.05 on >=2 of 3 embeddings",
        "PARTIAL_STRUCTURE": "Either metric sig on >=2 embeddings",
        "WEAK_STRUCTURE":    "Any metric sig on >=1 embedding",
    },
}

(OUTDIR / "expE6_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
)
np.savez_compressed(
    OUTDIR / "expE6_embeddings.npz",
    X_qz=X_qz, Y_pca=Y_pca, Y_tsne=Y_tsne, Y_iso=Y_iso,
    surah_ix=surah_ix, is_medinan=is_medinan, n_verses=n_verses,
    pca_explained=explained_var,
)

# --------------------------------------------------------------- PLOTS
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

for Yname, Y in [("PCA", Y_pca), ("TSNE", Y_tsne), ("ISO", Y_iso)]:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # (a) coloured by mushaf order
    sc0 = axes[0].scatter(Y[:, 0], Y[:, 1], c=surah_ix, cmap="viridis",
                          s=np.clip(n_verses / 5, 8, 200), edgecolor="0.3", lw=0.3)
    axes[0].set_title(f"{Yname} — coloured by mushaf order (size ∝ n_verses)")
    axes[0].set_xlabel("component 1"); axes[0].set_ylabel("component 2")
    cb = fig.colorbar(sc0, ax=axes[0]); cb.set_label("surah index")
    axes[0].grid(True, alpha=0.3)

    # (b) Meccan vs Medinan
    axes[1].scatter(Y[~is_medinan, 0], Y[~is_medinan, 1], c="C0", s=60,
                    edgecolor="0.3", lw=0.3, label=f"Meccan ({(~is_medinan).sum()})")
    axes[1].scatter(Y[is_medinan, 0], Y[is_medinan, 1], c="C3", s=60,
                    marker="^", edgecolor="0.3", lw=0.3,
                    label=f"Medinan ({is_medinan.sum()})")
    # annotate a few outliers and surah 1/114
    for i, s in enumerate(surah_ix):
        if s in (1, 2, 9, 18, 36, 55, 67, 112, 113, 114):
            axes[1].annotate(str(s), (Y[i, 0], Y[i, 1]), fontsize=8,
                             xytext=(3, 3), textcoords="offset points")
    s = stats[Yname] if Yname in stats else stats.get("ISO")
    axes[1].set_title(f"{Yname} — Meccan vs Medinan\n"
                      f"Moran's I={s['morans_I']:+.3f} (p={s['morans_I_p']:.3f}), "
                      f"silhouette={s['silhouette']:+.3f} (p={s['silhouette_p']:.3f})")
    axes[1].set_xlabel("component 1"); axes[1].set_ylabel("component 2")
    axes[1].legend(); axes[1].grid(True, alpha=0.3)

    fig.suptitle(f"expE6 — Quran 114×5 feature embedding ({Yname})", y=1.02)
    fig.tight_layout()
    fig.savefig(OUTDIR / f"expE6_embedding_{Yname}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

# --------------------------------------------------------------- MD
md = [
    "# expE6 — 2-D embeddings of 114×5 Quran feature matrix",
    "",
    f"**Generated (UTC)**: {report['generated_utc']}",
    f"**Seed**: {SEED}  |  **Shuffles**: {N_SHUFFLES}  |  **Embeddings**: PCA, t-SNE, Isomap",
    f"**Features**: {', '.join(FEAT_COLS)}  |  **z-score ref**: Arabic control pool ({len(X_ctrl)} units)",
    "",
    "## Pre-registration (set before execution)",
    "",
    "- **Null**: Moran's I and silhouette inside 95% CI of 1000 label shuffles.",
    "- **POSITIVE_STRUCTURE**: both metrics significant on ≥ 2 of 3 embeddings.",
    "- **PARTIAL_STRUCTURE**: ≥ 2 embeddings significant on one metric.",
    "- **WEAK_STRUCTURE**: ≥ 1 embedding significant on any metric.",
    "",
    f"## Verdict — **{verdict}**",
    "",
    f"| Embedding | Moran's I | Moran's I p | Silhouette | Silhouette p |",
    f"|---|---:|---:|---:|---:|",
]
for Yname, s in stats.items():
    md.append(
        f"| {Yname} | {s['morans_I']:+.4f} | {s['morans_I_p']:.4f} | "
        f"{s['silhouette']:+.4f} | {s['silhouette_p']:.4f} |"
    )

md.append("")
md.append(f"## PCA — explained-variance ratio: "
          f"PC1={explained_var[0]:.3f}, PC2={explained_var[1]:.3f}, "
          f"sum={explained_var.sum():.3f}")
md.append("")
md.append("## Meccan vs Medinan (Al-Azhar classification)")
md.append("")
md.append(f"- Meccan:  {(~is_medinan).sum()} surahs")
md.append(f"- Medinan: {is_medinan.sum()} surahs")
md.append("")
md.append("## Outputs")
md.append("")
md.append("- `expE6_report.json` — permutation-test results")
md.append("- `expE6_embeddings.npz` — all embedding arrays + metadata")
md.append("- `expE6_embedding_PCA.png` — PCA figure (order + era)")
md.append("- `expE6_embedding_TSNE.png` — t-SNE figure (order + era)")
md.append("- `expE6_embedding_ISO.png` — Isomap figure (order + era)")

(OUTDIR / "expE6_report.md").write_text("\n".join(md), encoding="utf-8")

print(f"\nVerdict: {verdict}")
print(f"Outputs in {OUTDIR}")
print(f"Total runtime: {time.time()-t0:.1f}s")
