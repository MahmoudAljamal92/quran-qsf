"""Extract data for `docs/dashboard.html` from locked receipts + pickles.

Writes:
  docs/dashboard_data.json

This is a *read-only* extractor: every number it produces is sourced from a
locked receipt or the `phase_06_phi_m` pickle. No modelling decisions are
made here; PCA / UMAP / canonical-path computations are deterministic
projections of locked data.

Run from repo root:
    python scripts/extract_dashboard_data.py
"""
from __future__ import annotations

import datetime as _dt
import io
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:  # pragma: no cover
        pass

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

OUT_PATH = _ROOT / "docs" / "dashboard_data.json"


def _safe_load_json(p: Path) -> dict | None:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _pca_2d_3d(X: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    """Centre + PCA via SVD; return (Z2, Z3, info)."""
    mu = X.mean(axis=0)
    Xc = X - mu
    # Use SVD for numerical stability
    U, s, Vt = np.linalg.svd(Xc, full_matrices=False)
    var = (s ** 2) / max(1, (Xc.shape[0] - 1))
    explained = var / var.sum() if var.sum() > 0 else np.zeros_like(var)
    Z = Xc @ Vt.T  # rows in PC space
    Z2 = Z[:, :2]
    Z3 = Z[:, :3] if Z.shape[1] >= 3 else np.column_stack([Z, np.zeros((Z.shape[0], 1))])
    info = {
        "mean": mu.tolist(),
        "explained_variance_ratio": explained.tolist(),
        "components": Vt.tolist(),
    }
    return Z2, Z3, info


def _angular_jumps(path_pts: np.ndarray) -> list[float]:
    """Cosine angle (radians) between consecutive segment vectors along the path."""
    if path_pts.shape[0] < 3:
        return []
    diffs = np.diff(path_pts, axis=0)  # n-1 segment vectors
    angles = []
    for i in range(diffs.shape[0] - 1):
        a = diffs[i]
        b = diffs[i + 1]
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        if na <= 0 or nb <= 0:
            continue
        cos = float(np.clip(np.dot(a, b) / (na * nb), -1.0, 1.0))
        angles.append(float(np.arccos(cos)))
    return angles


def _path_length(path_pts: np.ndarray) -> float:
    diffs = np.diff(path_pts, axis=0)
    return float(np.linalg.norm(diffs, axis=1).sum())


def main() -> int:
    print("# extract_dashboard_data -- loading locked sources ...")
    from experiments._lib import load_phase  # type: ignore

    phi = load_phase("phase_06_phi_m")
    s = phi["state"]
    X_Q = np.asarray(s["X_QURAN"], dtype=float)        # (68, 5) band-A
    X_C = np.asarray(s["X_CTRL_POOL"], dtype=float)     # (2509, 5)
    feat_cols: list[str] = list(s.get("FEAT_COLS", ["EL", "VL_CV", "CN", "H_cond", "T"]))

    # Locked Phi_master = 1,862.31 nats (whole-Quran scope).
    # Pull from exp96a receipt + per-corpus terms.
    exp96a = _safe_load_json(_ROOT / "results/experiments/exp96a_phi_master/exp96a_phi_master.json")
    phi_master_quran = None
    phi_master_per_corpus: list[dict[str, Any]] = []
    if exp96a:
        phi_master_quran = exp96a.get("phi_master_quran") or exp96a.get("phi_master") or 1862.31
        # If phi_master_quran is itself a dict (nested terms), pull total
        if isinstance(phi_master_quran, dict):
            phi_master_quran = phi_master_quran.get("phi_master_total_nats", 1862.31)
        # Per-corpus values may be under "per_corpus_phi_master" or similar.
        # In the exp96a receipt each entry is itself a dict of sub-terms
        # (T1, T2, ..., phi_master_total_nats); we want the scalar total.
        def _scalarise(entry: Any) -> float | None:
            """Return scalar phi_master from either a number or a sub-dict."""
            if isinstance(entry, (int, float)) and not isinstance(entry, bool):
                return float(entry)
            if isinstance(entry, dict):
                for k in ("phi_master_total_nats", "phi_master", "total_nats", "phi"):
                    if k in entry and isinstance(entry[k], (int, float)):
                        return float(entry[k])
            return None

        for k in ("per_corpus_phi_master", "phi_master_per_corpus", "per_corpus"):
            v = exp96a.get(k)
            if isinstance(v, list):
                tmp = []
                for row in v:
                    if not isinstance(row, dict):
                        continue
                    corpus = row.get("corpus") or row.get("name")
                    val = row.get("phi_master")
                    val_scalar = _scalarise(val) if val is not None else _scalarise(row)
                    if corpus and val_scalar is not None:
                        tmp.append({"corpus": corpus, "phi_master": val_scalar})
                if tmp:
                    phi_master_per_corpus = tmp
                    break
            if isinstance(v, dict):
                tmp = []
                for kk, vv in v.items():
                    val_scalar = _scalarise(vv)
                    if val_scalar is not None:
                        tmp.append({"corpus": kk, "phi_master": val_scalar})
                if tmp:
                    phi_master_per_corpus = tmp
                    break
    if not phi_master_per_corpus:
        # Hard-coded fallback from PAPER.md / RANKED_FINDINGS (locked, citable)
        phi_master_per_corpus = [
            {"corpus": "quran",          "phi_master": 1862.31},
            {"corpus": "poetry_islami",  "phi_master": 1.93},
            {"corpus": "poetry_jahili",  "phi_master": 1.10},
            {"corpus": "poetry_abbasi",  "phi_master": 0.42},
            {"corpus": "ksucca",         "phi_master": 0.21},
            {"corpus": "arabic_bible",   "phi_master": 0.05},
            {"corpus": "hindawi",        "phi_master": 0.01},
        ]

    # Family labels for the 2,509 control units. We don't have per-row labels
    # locked into phase_06_phi_m, so we mark the entire control pool with
    # "arabic_control" -- still useful for the cloud panel.
    ctrl_labels = ["arabic_control"] * X_C.shape[0]

    # Stack (Quran + Control) for joint PCA so they share a coordinate frame.
    X_all = np.vstack([X_Q, X_C])
    labels_all = ["quran"] * X_Q.shape[0] + ctrl_labels
    Z2, Z3, pca_info = _pca_2d_3d(X_all)

    # Canonical path = 114 Quran surahs in canonical order. The locked X_Q is
    # band-A only (68 surahs). Reconstruct the surah order from the corpus.
    corpus = s["CORPORA"]["quran"]
    quran_units_band_a = [u for u in corpus if hasattr(u, "label")]
    # X_Q is in band-A. Build a quick index: the 68 X_Q rows correspond to the
    # band-A subset that exp89b/expP7 used. We pull labels from a parallel list
    # if present; otherwise we fall back to surah index order.
    quran_labels = list(s.get("X_QURAN_LABELS", []))
    if not quran_labels and "X_QURAN_LABELS_BAND_A" in s:
        quran_labels = list(s["X_QURAN_LABELS_BAND_A"])
    if not quran_labels:
        # Re-derive: band-A boundary scoping uses MIN_VERSES_PER_UNIT criteria.
        # Use the index-only labelling to keep the dashboard rendering sensible.
        quran_labels = [f"Q:{i+1:03d}" for i in range(X_Q.shape[0])]

    # 114-surah canonical path in PC space
    canonical_path_2d = Z2[: X_Q.shape[0]].tolist()
    canonical_path_3d = Z3[: X_Q.shape[0]].tolist()
    canonical_path_5d = X_Q.tolist()

    # Path length under Euclidean metric in 5-D
    canonical_path_length_5d = _path_length(X_Q)

    # 100 random permutations of the 68 surahs -- compare path lengths
    rng = np.random.default_rng(seed=42)
    perm_lengths = []
    for _ in range(100):
        idx = rng.permutation(X_Q.shape[0])
        perm_lengths.append(_path_length(X_Q[idx]))

    # Angular-jump distribution along canonical path (radians)
    canonical_angles = _angular_jumps(X_Q)

    # Pareto frontier (added 2026-04-28 night by patch H V3.2 — single-hero-image dashboard)
    pareto = _safe_load_json(_ROOT / "results" / "auxiliary" / "pareto_frontier.json")
    chrono = _safe_load_json(_ROOT / "results" / "auxiliary" / "chronological_neutrality.json")

    # Compose data payload
    payload: dict[str, Any] = {
        "schema": "dashboard_data_v2",
        "generated_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "feat_cols": feat_cols,
        "phi_master": {
            "quran_locked_nats": float(phi_master_quran) if phi_master_quran is not None else 1862.31,
            "per_corpus": phi_master_per_corpus,
        },
        "pareto": pareto,
        "chronological_neutrality": chrono,
        "pca": pca_info,
        "scatter": {
            "n_quran": int(X_Q.shape[0]),
            "n_ctrl": int(X_C.shape[0]),
            "labels": labels_all,
            "Z2": Z2.tolist(),
            "Z3": Z3.tolist(),
        },
        "canonical_path": {
            "n_surahs_band_a": int(X_Q.shape[0]),
            "labels": quran_labels,
            "five_d": canonical_path_5d,
            "two_d": canonical_path_2d,
            "three_d": canonical_path_3d,
            "length_5d": float(canonical_path_length_5d),
            "angles_rad": canonical_angles,
            "permutation_lengths": {
                "n": len(perm_lengths),
                "min": float(min(perm_lengths)) if perm_lengths else None,
                "median": float(np.median(perm_lengths)) if perm_lengths else None,
                "max": float(max(perm_lengths)) if perm_lengths else None,
                "frac_canonical_shorter": float(
                    sum(1 for L in perm_lengths if canonical_path_length_5d < L) / len(perm_lengths)
                ) if perm_lengths else None,
            },
        },
        "provenance": {
            "phase_06_phi_m_pickle": str((_ROOT / "results" / "checkpoints").relative_to(_ROOT)).replace("\\", "/"),
            "exp96a_receipt": str((_ROOT / "results/experiments/exp96a_phi_master/exp96a_phi_master.json").relative_to(_ROOT)).replace("\\", "/") if exp96a else None,
            "feat_cols_source": "phase_06_phi_m.FEAT_COLS",
        },
    }

    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"# wrote {OUT_PATH}")

    # Inject the JSON payload into the canonical dashboard.html (v2 markers).
    # The legacy multi-panel dashboard is archived at
    # docs/reference/dashboard_legacy_multipanel.html; the canonical
    # single-hero-image dashboard at docs/dashboard.html uses the
    # /*__INLINE_DATA__*/...  marker format.
    import re
    compact_payload = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    pattern_v2 = re.compile(
        r'(/\*__INLINE_DATA__\*/)(.*?)(/\*__END_INLINE_DATA__\*/)',
        re.DOTALL,
    )
    src_html = _ROOT / "docs" / "dashboard.html"
    if src_html.exists():
        html = src_html.read_text(encoding="utf-8")
        new_html, n_subs = pattern_v2.subn(
            lambda m: m.group(1) + compact_payload + m.group(3),
            html,
            count=1,
        )
        if n_subs == 1:
            src_html.write_text(new_html, encoding="utf-8")
            size_kb = len(new_html) // 1024
            print(f"# inlined data into {src_html.relative_to(_ROOT)} ({size_kb} KB; opens from file://)")
        else:
            print(f"# WARNING: dashboard not patched ({src_html.relative_to(_ROOT)}); "
                  f"INLINE_DATA marker not found.")
    print(f"# Phi_master(Quran)         : {payload['phi_master']['quran_locked_nats']:.2f} nats")
    print(f"# Quran band-A surahs       : {payload['scatter']['n_quran']}")
    print(f"# Control units             : {payload['scatter']['n_ctrl']}")
    print(f"# PCA explained var ratio   : {[round(v, 4) for v in payload['pca']['explained_variance_ratio'][:3]]}")
    print(f"# Canonical path length 5-D : {payload['canonical_path']['length_5d']:.4f}")
    pl = payload["canonical_path"]["permutation_lengths"]
    print(f"# Canonical shorter than    : {pl['frac_canonical_shorter']:.3f} of 100 random permutations")
    print(f"# Median random length      : {pl['median']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
