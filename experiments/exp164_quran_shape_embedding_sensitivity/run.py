"""experiments/exp164_quran_shape_embedding_sensitivity/run.py
==================================================================
V3.24 candidate -- F80 promotion gate.

Tests whether the three BHL-significant cloud-shape descriptors from
exp163 (linearity_westin, planarity_westin, symmetry_score) survive
under independent embeddings of the per-unit corpus point cloud.

Embeddings:
    raw_phi_m            5-D (EL, VL_CV, CN, H_cond, T) -- exp163 baseline
    whitened_phi_m       Mahalanobis-whitened using combined-pool covariance
    alphabet_freq_pca5   28-letter frequency vectors -> top-5 PCs of pool
                         (independent of Phi_M pipeline)

PASS criterion: Quran BHL-significant (family-wise alpha = 0.01 over 9 tests)
on at least 2 descriptors in at least 2 embeddings, with at least one being
alphabet_freq_pca5. Otherwise PARTIAL or FAIL_PIPELINE_SPECIFIC.

Inputs : phase_06_phi_m.pkl
PREREG : experiments/exp164_quran_shape_embedding_sensitivity/PREREG.md
Output : results/experiments/exp164_quran_shape_embedding_sensitivity/
            exp164_quran_shape_embedding_sensitivity.json
            sensitivity_heatmap.png
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

EXP = "exp164_quran_shape_embedding_sensitivity"
SEED = 43
N_BOOTSTRAP = 10_000
N_SUBSAMPLE = 200
ALPHA_BHL = 0.01
PCA_DIMS = 5
TARGET_DESC = ["linearity_westin", "planarity_westin", "symmetry_score"]
FEAT_COLS = ["EL", "VL_CV", "CN", "H_cond", "T"]

CORPORA = [
    "quran", "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hadith_bukhari", "hindawi",
]

ARABIC_28 = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
A28_SET = set(ARABIC_28)
A28_INDEX = {c: i for i, c in enumerate(ARABIC_28)}
DIACRITIC_RANGES = (
    (0x0610, 0x061A), (0x064B, 0x065F), (0x06D6, 0x06ED),
    (0x0670, 0x0670),
)
TATWEEL = "\u0640"
HAMZA_FOLD = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
              "ئ": "ي", "ؤ": "و", "ء": "",
              "ة": "ه", "ى": "ي"}


# =========================================================================
#  Letter folding (matches exp95j and exp160 pipeline)
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


def letter_freq_vector(unit) -> np.ndarray | None:
    verses = getattr(unit, "verses", None)
    if verses is None and isinstance(unit, dict):
        verses = unit.get("verses", [])
    if not verses:
        return None
    joined = " ".join(verses)
    folded = to_28_letters(joined)
    if len(folded) < 50:
        return None
    counts = np.zeros(28, dtype=np.float64)
    for ch in folded:
        counts[A28_INDEX[ch]] += 1
    return counts / counts.sum()


# =========================================================================
#  Shape descriptors (subset of exp163 — only the 3 target descriptors)
# =========================================================================

def shape_3desc(X: np.ndarray) -> dict[str, float]:
    """Compute linearity_westin, planarity_westin, symmetry_score only."""
    n, d = X.shape
    if n < d + 1:
        return {k: float("nan") for k in TARGET_DESC}
    Xc = X - X.mean(axis=0)
    cov = np.cov(Xc, rowvar=False)
    eig = np.linalg.eigvalsh(cov)
    eig = np.sort(eig)[::-1]
    eig = np.maximum(eig, 1e-12)
    linearity = float((eig[0] - eig[1]) / eig[0]) if d >= 2 else 0.0
    planarity = (float((eig[1] - eig[-1]) / eig[0]) if d >= 3 else 0.0)
    Xref = -Xc
    D = cdist(Xc, Xref)
    nn_to_ref = D.min(axis=1)
    pdist = cdist(Xc, Xc)
    iu = np.triu_indices(n, k=1)
    median_pd = float(np.median(pdist[iu])) if iu[0].size else 1.0
    if median_pd <= 0:
        median_pd = 1.0
    sym_score = float(nn_to_ref.mean() / median_pd)
    return {
        "linearity_westin": linearity,
        "planarity_westin": planarity,
        "symmetry_score": sym_score,
    }


def two_sided_p(observed: float, null_array: np.ndarray) -> float:
    if null_array.size == 0 or not np.isfinite(observed):
        return float("nan")
    p_low = float((null_array <= observed).mean())
    p_high = float((null_array >= observed).mean())
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
#  Per-corpus matrix builders
# =========================================================================

def per_corpus_phi_matrix(state: dict, corpus_name: str) -> np.ndarray:
    feats = state["FEATS"][corpus_name]
    return np.array([[u[c] for c in FEAT_COLS] for u in feats],
                    dtype=np.float64)


def quran_band_A_phi_matrix(state: dict) -> np.ndarray:
    """Return the 68-row Band-A Quran matrix that exp163 used.

    `state["X_QURAN"]` is already the Band-A filtered matrix (verified by
    exp163 audit hook A1).
    """
    return state["X_QURAN"].astype(np.float64)


def per_corpus_alphabet_freq_matrix(
        state: dict,
        corpus_name: str,
) -> tuple[np.ndarray, list[int]]:
    """Return (N x 28) letter-frequency matrix and the indices of units
    that produced valid vectors (>= 50 letters).
    """
    units = state["CORPORA"][corpus_name]
    rows: list[np.ndarray] = []
    valid_idx: list[int] = []
    for i, u in enumerate(units):
        v = letter_freq_vector(u)
        if v is not None:
            rows.append(v)
            valid_idx.append(i)
    if not rows:
        return np.zeros((0, 28), dtype=np.float64), []
    return np.vstack(rows), valid_idx


def quran_band_A_alphabet_freq(state: dict) -> np.ndarray:
    """Letter-frequency matrix for the same 68 Band-A surahs that exp163
    uses. We identify Band-A surahs by matching them to FEATS['quran'] dict
    rows whose [EL, VL_CV, CN, H_cond, T] equals an X_QURAN row.

    Robust matching: compare FEATS rows to X_QURAN rows by all-feature
    equality up to 1e-9.
    """
    X_band_A = state["X_QURAN"].astype(np.float64)
    feats = state["FEATS"]["quran"]
    units = state["CORPORA"]["quran"]
    # Build per-surah feature row from FEATS
    feat_rows = np.array([[u[c] for c in FEAT_COLS] for u in feats],
                         dtype=np.float64)
    # For each X_QURAN row, find matching FEATS row index
    matched_idx: list[int] = []
    used = set()
    for q_row in X_band_A:
        diffs = np.abs(feat_rows - q_row).sum(axis=1)
        order = np.argsort(diffs)
        for j in order:
            if j in used:
                continue
            if diffs[j] < 1e-7:
                matched_idx.append(int(j))
                used.add(int(j))
                break
        else:
            raise RuntimeError("Failed to match X_QURAN row to FEATS row")
    if len(matched_idx) != X_band_A.shape[0]:
        raise RuntimeError(
            f"Band-A match incomplete: {len(matched_idx)} vs "
            f"{X_band_A.shape[0]}"
        )
    rows: list[np.ndarray] = []
    for j in matched_idx:
        v = letter_freq_vector(units[j])
        if v is None:
            raise RuntimeError(
                f"Band-A surah idx {j} has < 50 letters; "
                f"unexpected for Quran."
            )
        rows.append(v)
    return np.vstack(rows)


# =========================================================================
#  Embedding constructors
# =========================================================================

def build_raw_phi_m_embedding(state: dict) -> dict[str, Any]:
    """Embedding 1: raw 5-D Phi_M, no transform."""
    X_q = quran_band_A_phi_matrix(state)
    pool_rows: list[np.ndarray] = []
    pool_corpus: list[str] = []
    per_corpus: dict[str, np.ndarray] = {}
    for cname in CORPORA:
        if cname == "quran":
            per_corpus[cname] = X_q
            pool_rows.append(X_q)
            pool_corpus.extend([cname] * X_q.shape[0])
        else:
            X = per_corpus_phi_matrix(state, cname)
            per_corpus[cname] = X
            pool_rows.append(X)
            pool_corpus.extend([cname] * X.shape[0])
    pool = np.vstack(pool_rows)
    return {
        "name": "raw_phi_m",
        "X_quran": X_q,
        "pool": pool,
        "pool_corpus_labels": pool_corpus,
        "per_corpus": per_corpus,
        "transform_info": "identity (raw 5-D Phi_M)",
    }


def build_whitened_phi_m_embedding(state: dict) -> dict[str, Any]:
    """Embedding 2: Mahalanobis-whiten using combined-pool covariance.
    After this transform pool covariance ~ I_5 (unit isotropic).
    """
    raw = build_raw_phi_m_embedding(state)
    pool = raw["pool"]
    mu = pool.mean(axis=0)
    Z = pool - mu
    Sigma = np.cov(Z, rowvar=False) + 1e-6 * np.eye(5)
    w, V = np.linalg.eigh(Sigma)
    A = (V * np.sqrt(1.0 / w)).T  # shape (5,5); A^T A == Sigma_inv
    pool_white = (pool - mu) @ A.T
    # Sanity-check whitening
    cov_white = np.cov(pool_white, rowvar=False)
    isotropy_err = float(
        np.linalg.norm(cov_white - np.eye(5)) / np.sqrt(5)
    )
    per_corpus: dict[str, np.ndarray] = {}
    for cname, X in raw["per_corpus"].items():
        per_corpus[cname] = (X - mu) @ A.T
    X_q_white = (raw["X_quran"] - mu) @ A.T
    return {
        "name": "whitened_phi_m",
        "X_quran": X_q_white,
        "pool": pool_white,
        "pool_corpus_labels": raw["pool_corpus_labels"],
        "per_corpus": per_corpus,
        "transform_info": (
            f"Mahalanobis-whiten via combined-pool cov; ridge=1e-6; "
            f"post-whiten isotropy_err = {isotropy_err:.2e}"
        ),
        "isotropy_err_post_whiten": isotropy_err,
    }


def build_alphabet_freq_pca5_embedding(state: dict) -> dict[str, Any]:
    """Embedding 3: per-unit 28-letter frequency vector -> PCA top 5.
    Pool = Quran (Band-A) ∪ all 7 controls (>= 50 letters).
    PCA fit on the combined pool.
    """
    X_q_28 = quran_band_A_alphabet_freq(state)  # 68 x 28
    per_corpus_28: dict[str, np.ndarray] = {"quran": X_q_28}
    pool_rows: list[np.ndarray] = [X_q_28]
    pool_corpus: list[str] = ["quran"] * X_q_28.shape[0]
    valid_count: dict[str, int] = {"quran": int(X_q_28.shape[0])}
    for cname in CORPORA:
        if cname == "quran":
            continue
        X28, _idx = per_corpus_alphabet_freq_matrix(state, cname)
        per_corpus_28[cname] = X28
        pool_rows.append(X28)
        pool_corpus.extend([cname] * X28.shape[0])
        valid_count[cname] = int(X28.shape[0])
    pool_28 = np.vstack(pool_rows)
    # PCA (centered SVD)
    mu28 = pool_28.mean(axis=0)
    P = pool_28 - mu28
    U, S, Vt = np.linalg.svd(P, full_matrices=False)
    components = Vt[:PCA_DIMS]
    var_explained = (S ** 2)[:PCA_DIMS] / np.sum(S ** 2)
    project = lambda M: (M - mu28) @ components.T  # noqa: E731
    X_q_5 = project(X_q_28)
    pool_5 = project(pool_28)
    per_corpus_5: dict[str, np.ndarray] = {
        cn: project(per_corpus_28[cn]) for cn in per_corpus_28
    }
    return {
        "name": "alphabet_freq_pca5",
        "X_quran": X_q_5,
        "pool": pool_5,
        "pool_corpus_labels": pool_corpus,
        "per_corpus": per_corpus_5,
        "transform_info": (
            f"per-unit 28-letter freq vector (>= 50 letters), "
            f"PCA-{PCA_DIMS} on combined pool; "
            f"top-{PCA_DIMS} PC var explained = "
            f"{[round(v, 3) for v in var_explained.tolist()]}"
        ),
        "pca_var_explained": var_explained.tolist(),
        "valid_count_per_corpus": valid_count,
    }


# =========================================================================
#  Run a single embedding through the test family
# =========================================================================

def run_embedding(emb: dict[str, Any],
                  rng: np.random.Generator) -> dict[str, Any]:
    name = emb["name"]
    X_q = emb["X_quran"]
    pool = emb["pool"]
    n_target = X_q.shape[0]
    print(f"  [{name}] X_quran.shape = {X_q.shape}, pool.shape = {pool.shape}")

    # Quran observed descriptors
    quran_desc = shape_3desc(X_q)

    # Per-control: subsample N_SUBSAMPLE times to n_target, take median
    per_corpus_desc: dict[str, dict[str, float]] = {"quran": quran_desc}
    for cname, X in emb["per_corpus"].items():
        if cname == "quran":
            continue
        if X.shape[0] < n_target:
            per_corpus_desc[cname] = shape_3desc(X)
            continue
        descs = []
        for _ in range(N_SUBSAMPLE):
            idx = rng.choice(X.shape[0], size=n_target, replace=False)
            descs.append(shape_3desc(X[idx]))
        agg = {k: float(np.median([d[k] for d in descs])) for k in TARGET_DESC}
        per_corpus_desc[cname] = agg

    # Bootstrap-from-pool null for the Quran
    print(f"  [{name}] running {N_BOOTSTRAP} bootstraps of n={n_target} ...")
    t1 = time.time()
    null_descs: list[dict[str, float]] = []
    for k in range(N_BOOTSTRAP):
        idx = rng.choice(pool.shape[0], size=n_target, replace=False)
        null_descs.append(shape_3desc(pool[idx]))
        if (k + 1) % 2500 == 0:
            print(f"    [{name}] bootstrap {k + 1}/{N_BOOTSTRAP}  "
                  f"elapsed {time.time() - t1:.1f}s")
    print(f"  [{name}] bootstrap done in {time.time() - t1:.1f} s")

    quran_p: dict[str, dict[str, Any]] = {}
    for k in TARGET_DESC:
        nulls = np.array([d[k] for d in null_descs], dtype=np.float64)
        nulls = nulls[np.isfinite(nulls)]
        obs = quran_desc[k]
        p2 = two_sided_p(obs, nulls)
        rank_low_corpora = sorted(
            per_corpus_desc.items(),
            key=lambda kv: (
                kv[1][k] if np.isfinite(kv[1][k]) else float("inf")
            ),
        )
        rank_q_low = next(i for i, (cn, _) in enumerate(rank_low_corpora)
                          if cn == "quran") + 1
        quran_p[k] = {
            "observed": obs,
            "null_median": float(np.median(nulls)) if nulls.size else float("nan"),
            "null_std": float(nulls.std()) if nulls.size else float("nan"),
            "p_two_sided_vs_bootstrap": p2,
            "quran_rank_low_in_8_corpora": int(rank_q_low),
        }

    return {
        "embedding_name": name,
        "transform_info": emb["transform_info"],
        "n_quran": int(n_target),
        "n_pool": int(pool.shape[0]),
        "per_corpus_desc": per_corpus_desc,
        "quran_results": quran_p,
        "extra": {
            k: emb[k]
            for k in ("isotropy_err_post_whiten", "pca_var_explained",
                      "valid_count_per_corpus")
            if k in emb
        },
    }


# =========================================================================
#  Composite verdict + heatmap
# =========================================================================

def render_heatmap(results: dict[str, Any], out_png: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    embedding_names = list(results["per_embedding"].keys())
    fig, ax = plt.subplots(figsize=(10, 5))
    M = np.zeros((len(embedding_names), len(TARGET_DESC)))
    annot = []
    for i, en in enumerate(embedding_names):
        row_text = []
        for j, dn in enumerate(TARGET_DESC):
            qr = results["per_embedding"][en]["quran_results"][dn]
            p = qr["p_two_sided_vs_bootstrap"]
            obs = qr["observed"]
            rk = qr["quran_rank_low_in_8_corpora"]
            # Use -log10(p+1e-5) for color intensity
            M[i, j] = -math.log10(max(p, 1e-5))
            row_text.append(
                f"obs={obs:.3f}\np={p:.4f}\nrank={rk}/8"
            )
        annot.append(row_text)
    im = ax.imshow(M, cmap="viridis", aspect="auto", vmin=0, vmax=4.5)
    ax.set_xticks(range(len(TARGET_DESC)))
    ax.set_xticklabels([d.replace("_", "\n") for d in TARGET_DESC])
    ax.set_yticks(range(len(embedding_names)))
    ax.set_yticklabels(embedding_names)
    for i in range(len(embedding_names)):
        for j in range(len(TARGET_DESC)):
            color = "white" if M[i, j] > 2 else "black"
            ax.text(j, i, annot[i][j], ha="center", va="center",
                    fontsize=9, color=color)
    cbar = plt.colorbar(im, ax=ax, label="-log10(p_two_sided_vs_bootstrap)")
    bhl_thr = -math.log10(ALPHA_BHL / 9)
    cbar.ax.axhline(y=bhl_thr, color="red", linewidth=1.5)
    ax.set_title(
        "exp164 -- Quran shape sensitivity across 3 embeddings\n"
        f"(BHL alpha=0.01 over 9 tests; -log10(p_BHL_min) = {bhl_thr:.2f})"
    )
    fig.tight_layout()
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> dict[str, Any]:
    out_dir = safe_output_dir(EXP)
    out_path = out_dir / f"{EXP}.json"
    t0 = time.time()
    completed_at_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rng = np.random.default_rng(SEED)

    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]

    # Build the three embeddings
    print(f"[{EXP}] Building embeddings ...")
    emb_raw = build_raw_phi_m_embedding(state)
    print(f"  raw_phi_m: pool={emb_raw['pool'].shape}")
    emb_white = build_whitened_phi_m_embedding(state)
    print(f"  whitened_phi_m: isotropy_err = "
          f"{emb_white['isotropy_err_post_whiten']:.2e}")
    emb_alpha = build_alphabet_freq_pca5_embedding(state)
    print(f"  alphabet_freq_pca5: per-corpus n = "
          f"{emb_alpha['valid_count_per_corpus']}")

    # Audit hooks
    audit = {
        "A1_n_band_A_quran": int(state["X_QURAN"].shape[0]),
        "A1_pass": state["X_QURAN"].shape[0] == 68,
        "A2_isotropy_err_whitened": emb_white["isotropy_err_post_whiten"],
        "A2_pass": emb_white["isotropy_err_post_whiten"] < 1e-6,
        "A3_pca_var_explained": emb_alpha["pca_var_explained"],
        "A4_valid_alphabet_n_per_corpus": emb_alpha["valid_count_per_corpus"],
    }

    # Run all three through the test family
    per_embedding: dict[str, Any] = {}
    for emb in (emb_raw, emb_white, emb_alpha):
        print(f"\n[{EXP}] === Embedding: {emb['name']} ===")
        per_embedding[emb["name"]] = run_embedding(emb, rng)

    # Family-wise BHL across 9 tests = 3 desc × 3 embeddings
    p_named: list[tuple[str, float]] = []
    for en, res in per_embedding.items():
        for dn, qr in res["quran_results"].items():
            p_named.append((f"{en}/{dn}", qr["p_two_sided_vs_bootstrap"]))
    bhl_survivors = bonferroni_holm(p_named, ALPHA_BHL)

    survivors_by_embedding: dict[str, list[str]] = {
        en: [s.split("/", 1)[1] for s in bhl_survivors if s.startswith(en + "/")]
        for en in per_embedding
    }
    survivors_by_descriptor: dict[str, list[str]] = {
        dn: [s.split("/", 1)[0] for s in bhl_survivors if s.endswith("/" + dn)]
        for dn in TARGET_DESC
    }

    # Determine verdict
    n_emb_ge2_desc = sum(
        1 for en in per_embedding if len(survivors_by_embedding[en]) >= 2
    )
    alphabet_has_ge2 = len(survivors_by_embedding.get("alphabet_freq_pca5",
                                                       [])) >= 2
    raw_only = (
        len(survivors_by_embedding.get("raw_phi_m", [])) > 0
        and len(survivors_by_embedding.get("whitened_phi_m", [])) == 0
        and len(survivors_by_embedding.get("alphabet_freq_pca5", [])) == 0
    )

    if n_emb_ge2_desc >= 2 and alphabet_has_ge2:
        verdict = "PASS_PORTABLE_GEOMETRY"
    elif raw_only:
        verdict = "FAIL_PIPELINE_SPECIFIC"
    elif len(bhl_survivors) > 0:
        verdict = "PARTIAL_NON_PORTABLE_GEOMETRY"
    else:
        verdict = "FAIL_NO_BHL_SURVIVORS"

    # Render heatmap
    heatmap_path = out_dir / "sensitivity_heatmap.png"
    summary_pre = {
        "per_embedding": per_embedding,
    }
    try:
        render_heatmap(summary_pre, heatmap_path)
        heatmap_status = "ok"
    except Exception as e:
        heatmap_status = f"fail: {e}"

    receipt: dict[str, Any] = {
        "experiment": EXP,
        "schema_version": 1,
        "hypothesis": (
            "The three exp163 BHL-significant cloud-shape descriptors "
            "(linearity_westin, planarity_westin, symmetry_score) for the "
            "Quran's 68 Band-A surahs persist as BHL-significant under "
            "independent embeddings (whitened-Phi_M and alphabet-freq-PCA5)."
        ),
        "verdict": verdict,
        "completed_at_utc": completed_at_utc,
        "wall_time_s": float(time.time() - t0),
        "frozen_constants": {
            "SEED": SEED, "N_BOOTSTRAP": N_BOOTSTRAP,
            "N_SUBSAMPLE": N_SUBSAMPLE, "ALPHA_BHL": ALPHA_BHL,
            "PCA_DIMS": PCA_DIMS, "TARGET_DESC": TARGET_DESC,
            "FEAT_COLS": FEAT_COLS, "CORPORA": CORPORA,
        },
        "audit_hooks": audit,
        "per_embedding": per_embedding,
        "bhl_alpha_family_wise": ALPHA_BHL,
        "bhl_n_tests": len(p_named),
        "bhl_survivors": bhl_survivors,
        "survivors_by_embedding": survivors_by_embedding,
        "survivors_by_descriptor": survivors_by_descriptor,
        "n_embeddings_with_ge2_desc_survivors": int(n_emb_ge2_desc),
        "alphabet_has_ge2_survivors": bool(alphabet_has_ge2),
        "heatmap_png": str(heatmap_path),
        "heatmap_status": heatmap_status,
    }
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    print("\n" + "=" * 70)
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  BHL survivors ({len(bhl_survivors)}/9 tests):")
    for s in bhl_survivors:
        en, dn = s.split("/", 1)
        qr = per_embedding[en]["quran_results"][dn]
        print(f"    {s:<48}  obs={qr['observed']:.3f}  "
              f"p={qr['p_two_sided_vs_bootstrap']:.5f}  "
              f"rank={qr['quran_rank_low_in_8_corpora']}/8")
    print(f"  embeddings with >= 2 BHL-sig descriptors: {n_emb_ge2_desc}/3")
    print(f"  alphabet_freq_pca5 has >= 2 BHL-sig: {alphabet_has_ge2}")
    print(f"  heatmap: {heatmap_status}")
    print(f"  wall-time = {receipt['wall_time_s']:.1f} s")
    print(f"  receipt: {out_path}")
    print("=" * 70)
    return receipt


if __name__ == "__main__":
    main()
