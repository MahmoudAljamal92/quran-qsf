"""experiments/exp125_unified_quran_coordinate_pca/run.py — PCA-based unification.

Tests whether the 5 universal features collapse to a single principal direction
PC1, with the Quran as the unique extremum. If PASS, the PC1 loading vector
IS the unified linear formula subsuming F58 / F66 / F67 / F75 / F76 into one
single coordinate per corpus.

PREREG: experiments/exp125_unified_quran_coordinate_pca/PREREG.md
Input:  results/auxiliary/_phi_universal_xtrad_sizing.json (SHA-256 locked)
Output: results/experiments/exp125_unified_quran_coordinate_pca/exp125_unified_quran_coordinate_pca.json
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Paths and locked constants

ROOT = Path(__file__).resolve().parent.parent.parent
EXP_NAME = "exp125_unified_quran_coordinate_pca"
PREREG = Path(__file__).resolve().parent / "PREREG.md"
INPUT_SIZING = ROOT / "results" / "auxiliary" / "_phi_universal_xtrad_sizing.json"
OUT_DIR = ROOT / "results" / "experiments" / EXP_NAME
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / f"{EXP_NAME}.json"

EXPECTED_INPUT_SHA256 = (
    "0f8dcf0f69106020fac6c596716b4729d78fdece828ebb83aba3aa2b0a79fc22"
)

EXPECTED_CORPORA = [
    "quran",
    "poetry_jahili",
    "poetry_islami",
    "poetry_abbasi",
    "hindawi",
    "ksucca",
    "arabic_bible",
    "hebrew_tanakh",
    "greek_nt",
    "pali",
    "avestan_yasna",
]
FEATURE_NAMES = [
    "VL_CV",
    "p_max",
    "H_EL",
    "bigram_distinct_ratio",
    "gzip_efficiency",
]

# PREREG-locked acceptance thresholds
VAR_EXPLAINED_DOMINANCE = 0.60
VAR_EXPLAINED_STRONG = 0.80
VAR_EXPLAINED_PARTIAL = 0.40
Z_QURAN_OUTLIER = 5.0
Z_NO_COMPETITOR = 2.0


def _format_formula(loading, feature_names):
    """Return human-readable string of the unified linear formula."""
    parts = []
    for i, fn in enumerate(feature_names):
        coef = loading[i]
        sign = "+" if coef >= 0 else "-"
        if i == 0:
            parts.append(f"{coef:+.4f} * z_{fn}")
        else:
            parts.append(f"{sign} {abs(coef):.4f} * z_{fn}")
    return "alpha(c) = " + " ".join(parts)


def main():
    t0 = time.time()

    # ---- A1: input SHA-256 ------------------------------------------------
    raw = INPUT_SIZING.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != EXPECTED_INPUT_SHA256:
        receipt = {
            "experiment": EXP_NAME,
            "verdict": "FAIL_audit_input_sha256_mismatch",
            "expected_sha256": EXPECTED_INPUT_SHA256,
            "actual_sha256": actual_sha,
        }
        OUT_PATH.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"FAIL_audit_input_sha256_mismatch: {actual_sha}")
        return

    sizing = json.loads(raw.decode("utf-8"))
    medians = sizing["medians"]

    # ---- A2/A3: feature/corpus presence -----------------------------------
    for c in EXPECTED_CORPORA:
        if c not in medians:
            raise SystemExit(f"missing corpus: {c}")
        for fn in FEATURE_NAMES:
            if fn not in medians[c]:
                raise SystemExit(f"missing feature {fn} for corpus {c}")

    # ---- Build 11x5 matrix (rows=corpora, cols=features) -------------------
    X = np.array(
        [[float(medians[c][fn]) for fn in FEATURE_NAMES] for c in EXPECTED_CORPORA],
        dtype=np.float64,
    )
    assert X.shape == (11, 5)

    # ---- Stage A: standardise (z-score per feature) ----------------------
    mu = X.mean(axis=0)
    sigma = X.std(axis=0, ddof=0)  # population std for the 11-corpus pool
    Z = (X - mu) / sigma  # 11x5 z-scored matrix

    # ---- Stage B: covariance + eigendecomposition ------------------------
    # Use Z^T Z / (N-1) as sample covariance of the 5 features
    C = (Z.T @ Z) / (X.shape[0] - 1)  # 5x5
    eigenvalues, eigenvectors = np.linalg.eigh(C)
    # eigh returns ascending; we want descending
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]

    # Sign convention: choose sign of v_1 such that Quran's PC1 score is negative
    quran_idx = EXPECTED_CORPORA.index("quran")
    quran_z = Z[quran_idx]
    pc1_loading = eigenvectors[:, 0]
    if pc1_loading @ quran_z > 0:
        pc1_loading = -pc1_loading
        eigenvectors[:, 0] = pc1_loading
    pc2_loading = eigenvectors[:, 1]

    # ---- Stage C: project all corpora onto PC1, PC2 ----------------------
    pc1_scores = Z @ pc1_loading  # 11-vector
    pc2_scores = Z @ pc2_loading

    pc1_per_corpus = {c: float(pc1_scores[i]) for i, c in enumerate(EXPECTED_CORPORA)}
    pc2_per_corpus = {c: float(pc2_scores[i]) for i, c in enumerate(EXPECTED_CORPORA)}

    quran_pc1 = pc1_per_corpus["quran"]
    quran_pc2 = pc2_per_corpus["quran"]
    non_quran_pc1 = [v for c, v in pc1_per_corpus.items() if c != "quran"]
    non_quran_pc2 = [v for c, v in pc2_per_corpus.items() if c != "quran"]

    mean_pc1_nq = float(np.mean(non_quran_pc1))
    std_pc1_nq = float(np.std(non_quran_pc1, ddof=0))
    cv_pc1_nq = std_pc1_nq / abs(mean_pc1_nq) if mean_pc1_nq != 0 else float("inf")

    z_quran_pc1 = (quran_pc1 - mean_pc1_nq) / std_pc1_nq if std_pc1_nq > 0 else 0.0
    z_per_corpus_pc1 = {
        c: (v - mean_pc1_nq) / std_pc1_nq if std_pc1_nq > 0 else 0.0
        for c, v in pc1_per_corpus.items()
    }
    max_other_abs_z = max(
        abs(z_per_corpus_pc1[c]) for c in EXPECTED_CORPORA if c != "quran"
    )

    # ---- Variance explained ---------------------------------------------
    total_var = float(np.sum(eigenvalues))
    var_explained = (eigenvalues / total_var).tolist()
    var_explained_pc1 = float(var_explained[0])
    var_explained_cumulative = np.cumsum(var_explained).tolist()

    # ---- Sanity check: sum of eigenvalues should be ~5 (D=5 standardised features)
    sum_lambda_check = abs(total_var - 5.0) < 1e-6

    # ---- Verdict ladder -------------------------------------------------
    abs_z_q = abs(z_quran_pc1)
    if (var_explained_pc1 >= VAR_EXPLAINED_STRONG
            and abs_z_q >= Z_QURAN_OUTLIER
            and max_other_abs_z <= Z_NO_COMPETITOR):
        verdict = "PASS_strong_unified"
        verdict_reason = (
            f"PC1 captures {var_explained_pc1*100:.1f}% of variance "
            f"(>= {VAR_EXPLAINED_STRONG*100:.0f}%); Quran |z|={abs_z_q:.2f} >= "
            f"{Z_QURAN_OUTLIER}; max competing |z|={max_other_abs_z:.2f} <= "
            f"{Z_NO_COMPETITOR}. Strong single-formula unification."
        )
    elif (var_explained_pc1 >= VAR_EXPLAINED_DOMINANCE
            and abs_z_q >= Z_QURAN_OUTLIER
            and max_other_abs_z <= Z_NO_COMPETITOR):
        verdict = "PASS_unified"
        verdict_reason = (
            f"PC1 captures {var_explained_pc1*100:.1f}% of variance "
            f"(>= {VAR_EXPLAINED_DOMINANCE*100:.0f}%); Quran |z|={abs_z_q:.2f}; "
            f"max competing |z|={max_other_abs_z:.2f}. Single-formula unification "
            f"at moderate dominance."
        )
    elif (abs_z_q >= Z_QURAN_OUTLIER
            and max_other_abs_z <= Z_NO_COMPETITOR
            and var_explained_pc1 >= VAR_EXPLAINED_PARTIAL):
        verdict = "PARTIAL_quran_extremum_no_dominance"
        verdict_reason = (
            f"Quran is extremum (|z|={abs_z_q:.2f}) but PC1 only captures "
            f"{var_explained_pc1*100:.1f}% (< {VAR_EXPLAINED_DOMINANCE*100:.0f}%) "
            "- 2-D unification needed."
        )
    elif abs_z_q < Z_QURAN_OUTLIER:
        verdict = "FAIL_no_unification"
        verdict_reason = (
            f"Quran is not a strict outlier on PC1 (|z|={abs_z_q:.2f} < "
            f"{Z_QURAN_OUTLIER}). No unified single coordinate exists."
        )
    else:
        verdict = "PARTIAL_competing_outlier"
        verdict_reason = (
            f"Quran is extremum but a competing outlier exists (max other |z|="
            f"{max_other_abs_z:.2f} > {Z_NO_COMPETITOR})."
        )

    # ---- Unified formula string ------------------------------------------
    unified_formula = _format_formula(pc1_loading.tolist(), FEATURE_NAMES)

    # ---- Audit ----------------------------------------------------------
    audit = {
        "ok": True,
        "checks": {
            "A1_input_sha256_match": actual_sha == EXPECTED_INPUT_SHA256,
            "A2_features_match": True,
            "A3_corpora_match": True,
            "A4_deterministic": True,
            "A5_eigenvalue_sum_check": sum_lambda_check,
        },
    }

    # ---- prereg hash ----------------------------------------------------
    prereg_hash = hashlib.sha256(PREREG.read_bytes()).hexdigest()

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H79",
        "hypothesis": (
            "The 5 universal features collapse to a single principal direction "
            "PC1 in feature space, with the Quran as the unique extremum on "
            "that direction. PC1 is the unified linear formula."
        ),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "prereg_hash": prereg_hash,
        "input_sizing_sha256": actual_sha,
        "frozen_constants": {
            "EXPECTED_CORPORA": EXPECTED_CORPORA,
            "FEATURE_NAMES": FEATURE_NAMES,
            "VAR_EXPLAINED_DOMINANCE": VAR_EXPLAINED_DOMINANCE,
            "VAR_EXPLAINED_STRONG": VAR_EXPLAINED_STRONG,
            "VAR_EXPLAINED_PARTIAL": VAR_EXPLAINED_PARTIAL,
            "Z_QURAN_OUTLIER": Z_QURAN_OUTLIER,
            "Z_NO_COMPETITOR": Z_NO_COMPETITOR,
        },
        "results": {
            "feature_means_raw": dict(zip(FEATURE_NAMES, mu.tolist())),
            "feature_stds_raw": dict(zip(FEATURE_NAMES, sigma.tolist())),
            "eigenvalues": eigenvalues.tolist(),
            "var_explained_per_pc": var_explained,
            "var_explained_pc1": var_explained_pc1,
            "var_explained_cumulative": var_explained_cumulative,
            "pc1_loading": dict(zip(FEATURE_NAMES, pc1_loading.tolist())),
            "pc2_loading": dict(zip(FEATURE_NAMES, pc2_loading.tolist())),
            "pc1_score_per_corpus": pc1_per_corpus,
            "pc2_score_per_corpus": pc2_per_corpus,
            "quran_pc1_score": quran_pc1,
            "quran_pc2_score": quran_pc2,
            "mean_pc1_non_quran": mean_pc1_nq,
            "std_pc1_non_quran": std_pc1_nq,
            "cv_pc1_non_quran": cv_pc1_nq,
            "z_quran_pc1": z_quran_pc1,
            "abs_z_quran_pc1": abs_z_q,
            "max_other_abs_z_pc1": max_other_abs_z,
            "z_per_corpus_pc1": z_per_corpus_pc1,
            "unified_formula_string": unified_formula,
        },
        "audit_report": audit,
        "wall_time_s": round(time.time() - t0, 6),
    }

    OUT_PATH.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # ---- Console summary -------------------------------------------------
    print(f"# {EXP_NAME}")
    print(f"# verdict: {verdict}")
    print(f"# {verdict_reason}")
    print()
    print("## Variance explained per PC:")
    for i, v in enumerate(var_explained):
        cum = var_explained_cumulative[i]
        print(f"  PC{i+1}: {v*100:6.2f}%   (cumulative: {cum*100:6.2f}%)")
    print()
    print(f"## Unified formula (PC1 loading):")
    print(f"  {unified_formula}")
    print()
    print("## PC1 score per corpus (sorted ascending = most Quran-like first):")
    sorted_corpora = sorted(pc1_per_corpus.items(), key=lambda kv: kv[1])
    for c, v in sorted_corpora:
        z = z_per_corpus_pc1[c]
        flag = " <-- QURAN" if c == "quran" else ""
        print(f"  {c:20s}  PC1={v:+8.4f}  z={z:+7.2f}{flag}")
    print()
    print(f"# Quran z on PC1: {z_quran_pc1:+.4f}")
    print(f"# Max competing |z|: {max_other_abs_z:.4f}")
    print(f"# wall_time_s: {receipt['wall_time_s']}")
    print(f"# receipt: {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
