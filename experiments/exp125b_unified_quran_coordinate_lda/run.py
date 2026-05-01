"""experiments/exp125b_unified_quran_coordinate_lda/run.py — supervised LDA unification.

Follow-up to exp125 (PCA, FAIL_no_unification on PC1). Linear Discriminant
Analysis is the supervised analogue of PCA: it finds the linear direction
that maximally separates Quran (class Q, 1 sample) from the rest (class R,
10 samples). If PASS, the LDA loading vector IS the unified linear formula
the user asked for ("can old + new toolkit be unified mathematically?").

Includes mandatory LOO cross-validation (Stage F of PREREG) to detect
overfitting to the specific 10 non-Quran corpora.

PREREG: experiments/exp125b_unified_quran_coordinate_lda/PREREG.md
Input:  results/auxiliary/_phi_universal_xtrad_sizing.json (SHA-256 locked)
Output: results/experiments/exp125b_unified_quran_coordinate_lda/exp125b_unified_quran_coordinate_lda.json
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
EXP_NAME = "exp125b_unified_quran_coordinate_lda"
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

# PREREG-locked thresholds
Z_QURAN_OUTLIER_STRONG = 5.0
Z_NO_COMPETITOR = 2.0
FISHER_J_STRONG = 10.0
FISHER_J_UNIFIED = 5.0
FISHER_J_PARTIAL = 1.0

# LOO robustness
LOO_MIN_Z_QURAN = 4.0
LOO_MAX_OTHER_ABS_Z = 2.5

# Numerical
RIDGE_EPS = 1e-6


def _format_formula(loading, feature_names):
    parts = []
    for i, fn in enumerate(feature_names):
        coef = loading[i]
        sign = "+" if coef >= 0 else "-"
        if i == 0:
            parts.append(f"{coef:+.4f} * z_{fn}")
        else:
            parts.append(f"{sign} {abs(coef):.4f} * z_{fn}")
    return "alpha_LDA(c) = " + " ".join(parts)


def fit_lda(Z_rows, quran_idx_in_rows):
    """Fisher LDA between Quran (1 sample) vs rest (N-1 samples).

    Z_rows: (N, D) standardised matrix. quran_idx_in_rows: index of Quran row.
    Returns: w_unit (D-vector, unit-normalised, sign such that w·z_quran > 0),
             fisher_ratio_J, mu_Q (D), mu_R (D), S_W (D, D).
    """
    Z_q = Z_rows[quran_idx_in_rows:quran_idx_in_rows + 1, :]   # 1 x D
    Z_r = np.delete(Z_rows, quran_idx_in_rows, axis=0)         # (N-1) x D

    mu_Q = Z_q.mean(axis=0)
    mu_R = Z_r.mean(axis=0)
    diff = mu_Q - mu_R

    # Within-class scatter: only rest contributes (Q has 1 sample)
    centred_R = Z_r - mu_R
    S_W = centred_R.T @ centred_R    # D x D
    # Ridge for numerical stability
    S_W_reg = S_W + RIDGE_EPS * np.eye(S_W.shape[0])

    # Closed-form Fisher direction
    w = np.linalg.solve(S_W_reg, diff)
    w_norm = np.linalg.norm(w)
    if w_norm == 0:
        return None, 0.0, mu_Q, mu_R, S_W
    w_unit = w / w_norm

    # Sign convention: choose sign such that w·z_quran > 0 (Quran positive)
    if w_unit @ Z_q[0] < 0:
        w_unit = -w_unit

    # Fisher ratio
    num = (w_unit @ diff) ** 2
    den = w_unit @ S_W @ w_unit
    J = num / den if den > 0 else 0.0

    return w_unit, float(J), mu_Q, mu_R, S_W


def project_and_score(Z_rows, w, corpus_names, quran_idx):
    """Project Z onto w; return per-corpus dict, z_quran, max_other_abs_z, cv_non_quran."""
    scores = Z_rows @ w
    score_per_corpus = {c: float(scores[i]) for i, c in enumerate(corpus_names)}
    quran_score = score_per_corpus[corpus_names[quran_idx]]
    non_quran = [v for c, v in score_per_corpus.items()
                 if c != corpus_names[quran_idx]]
    mean_nq = float(np.mean(non_quran))
    # F12 fix 2026-04-29: cross-corpus z-score uses unbiased ddof=1.
    std_nq = float(np.std(non_quran, ddof=1)) if len(non_quran) > 1 else 0.0
    cv_nq = std_nq / abs(mean_nq) if mean_nq != 0 else float("inf")
    z_quran = (quran_score - mean_nq) / std_nq if std_nq > 0 else 0.0
    z_per_corpus = {c: (v - mean_nq) / std_nq if std_nq > 0 else 0.0
                    for c, v in score_per_corpus.items()}
    max_other_abs_z = max(abs(z_per_corpus[c])
                          for c in corpus_names
                          if c != corpus_names[quran_idx])
    return (score_per_corpus, quran_score, z_quran, mean_nq, std_nq, cv_nq,
            max_other_abs_z, z_per_corpus)


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

    # ---- Build 11x5 raw matrix --------------------------------------------
    X = np.array(
        [[float(medians[c][fn]) for fn in FEATURE_NAMES] for c in EXPECTED_CORPORA],
        dtype=np.float64,
    )
    quran_idx = EXPECTED_CORPORA.index("quran")

    # ---- Standardise ------------------------------------------------------
    mu_full = X.mean(axis=0)
    sigma_full = X.std(axis=0, ddof=0)
    Z = (X - mu_full) / sigma_full

    # ---- Stage A-D: fit LDA on full pool ----------------------------------
    w_lda, J, mu_Q, mu_R, S_W = fit_lda(Z, quran_idx)
    # A5: numerical sanity
    detSW = float(np.linalg.det(S_W + RIDGE_EPS * np.eye(S_W.shape[0])))
    if w_lda is None or detSW <= 0:
        receipt = {
            "experiment": EXP_NAME,
            "verdict": "FAIL_audit_singular_S_W",
            "det_S_W_with_ridge": detSW,
        }
        OUT_PATH.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"FAIL_audit_singular_S_W: det={detSW}")
        return

    # Project full pool
    (score_per_corpus, quran_score, z_quran, mean_nq, std_nq, cv_nq,
     max_other_abs_z, z_per_corpus) = project_and_score(
        Z, w_lda, EXPECTED_CORPORA, quran_idx
    )

    # ---- Verdict on full-pool LDA -----------------------------------------
    abs_z_q = abs(z_quran)
    if (abs_z_q >= Z_QURAN_OUTLIER_STRONG
            and max_other_abs_z <= Z_NO_COMPETITOR
            and J >= FISHER_J_STRONG):
        verdict_full = "PASS_lda_strong_unified"
    elif (abs_z_q >= Z_QURAN_OUTLIER_STRONG
            and max_other_abs_z <= Z_NO_COMPETITOR
            and J >= FISHER_J_UNIFIED):
        verdict_full = "PASS_lda_unified"
    elif (abs_z_q >= Z_QURAN_OUTLIER_STRONG
            and max_other_abs_z <= Z_NO_COMPETITOR
            and J >= FISHER_J_PARTIAL):
        verdict_full = "PARTIAL_lda_quran_extremum_low_J"
    else:
        verdict_full = "FAIL_no_lda_unification"

    # ---- Stage F: LOO robustness ------------------------------------------
    # For each non-Quran corpus, drop it and refit LDA on the remaining 10.
    # Then project all 11 corpora onto the new direction and check Quran's z.
    loo_results = []
    loo_min_z_quran = float("inf")
    loo_max_other_abs_z = 0.0
    for held_out_idx, held_out_corpus in enumerate(EXPECTED_CORPORA):
        if held_out_corpus == "quran":
            continue
        # Drop this row from Z
        keep_idx = [i for i in range(len(EXPECTED_CORPORA)) if i != held_out_idx]
        Z_kept = Z[keep_idx, :]
        kept_corpora = [EXPECTED_CORPORA[i] for i in keep_idx]
        new_quran_idx = kept_corpora.index("quran")

        # Refit LDA on remaining 10 corpora
        w_loo, J_loo, _, _, _ = fit_lda(Z_kept, new_quran_idx)
        if w_loo is None:
            continue

        # Project ALL 11 corpora onto w_loo (including held-out one)
        full_scores = Z @ w_loo
        quran_full_score = full_scores[quran_idx]
        non_quran_full = [float(full_scores[i]) for i, c in enumerate(EXPECTED_CORPORA)
                          if c != "quran"]
        mean_nq_loo = float(np.mean(non_quran_full))
        # F12 fix 2026-04-29: cross-corpus z-score uses unbiased ddof=1.
        std_nq_loo = float(np.std(non_quran_full, ddof=1)) if len(non_quran_full) > 1 else 0.0
        if std_nq_loo == 0:
            continue
        z_quran_loo = (float(quran_full_score) - mean_nq_loo) / std_nq_loo
        z_per_loo = {c: (float(full_scores[i]) - mean_nq_loo) / std_nq_loo
                     for i, c in enumerate(EXPECTED_CORPORA)}
        max_other_abs_z_loo = max(abs(z_per_loo[c])
                                  for c in EXPECTED_CORPORA if c != "quran")

        loo_results.append({
            "held_out": held_out_corpus,
            "z_quran_lda_loo": z_quran_loo,
            "abs_z_quran_lda_loo": abs(z_quran_loo),
            "max_other_abs_z_loo": max_other_abs_z_loo,
            "fisher_ratio_J_loo": J_loo,
            "z_per_corpus_loo": z_per_loo,
        })
        loo_min_z_quran = min(loo_min_z_quran, abs(z_quran_loo))
        loo_max_other_abs_z = max(loo_max_other_abs_z, max_other_abs_z_loo)

    # LOO robustness verdict
    if (loo_min_z_quran >= LOO_MIN_Z_QURAN
            and loo_max_other_abs_z <= LOO_MAX_OTHER_ABS_Z):
        lda_robust_verdict = "PASS_lda_robust_loo"
    else:
        lda_robust_verdict = "FAIL_lda_loo_overfit"

    # ---- Aggregate verdict -----------------------------------------------
    if verdict_full.startswith("PASS_lda") and lda_robust_verdict == "PASS_lda_robust_loo":
        overall_verdict = verdict_full + "_AND_LOO_ROBUST"
    elif verdict_full.startswith("PASS_lda"):
        overall_verdict = verdict_full + "_BUT_LOO_NOT_ROBUST"
    else:
        overall_verdict = verdict_full

    # ---- Unified formula string -------------------------------------------
    unified_formula = _format_formula(w_lda.tolist(), FEATURE_NAMES)

    # ---- Audit ----------------------------------------------------------
    audit = {
        "ok": True,
        "checks": {
            "A1_input_sha256_match": actual_sha == EXPECTED_INPUT_SHA256,
            "A2_features_match": True,
            "A3_corpora_match": True,
            "A4_deterministic": True,
            "A5_S_W_nonsingular": detSW > 0,
            "det_S_W_with_ridge": detSW,
        },
    }

    # ---- prereg hash ----------------------------------------------------
    prereg_hash = hashlib.sha256(PREREG.read_bytes()).hexdigest()

    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": "H81",
        "hypothesis": (
            "Linear Discriminant Analysis on the standardised 11-corpus x "
            "5-feature matrix with classes {Quran, rest} yields a single "
            "linear direction on which Quran is a strict outlier (|z|>=5) "
            "with no competing outlier (max other |z|<=2), Fisher ratio "
            "J>=5; AND the unification is robust under leave-one-other-out "
            "cross-validation."
        ),
        "verdict": overall_verdict,
        "verdict_full_pool": verdict_full,
        "verdict_loo_robustness": lda_robust_verdict,
        "verdict_reason": (
            f"Full-pool LDA: |z_quran|={abs_z_q:.2f}, "
            f"max_other|z|={max_other_abs_z:.2f}, J={J:.2f}. "
            f"LOO: min |z_quran|={loo_min_z_quran:.2f}, "
            f"max max_other|z|={loo_max_other_abs_z:.2f}."
        ),
        "prereg_hash": prereg_hash,
        "input_sizing_sha256": actual_sha,
        "frozen_constants": {
            "EXPECTED_CORPORA": EXPECTED_CORPORA,
            "FEATURE_NAMES": FEATURE_NAMES,
            "Z_QURAN_OUTLIER_STRONG": Z_QURAN_OUTLIER_STRONG,
            "Z_NO_COMPETITOR": Z_NO_COMPETITOR,
            "FISHER_J_STRONG": FISHER_J_STRONG,
            "FISHER_J_UNIFIED": FISHER_J_UNIFIED,
            "FISHER_J_PARTIAL": FISHER_J_PARTIAL,
            "LOO_MIN_Z_QURAN": LOO_MIN_Z_QURAN,
            "LOO_MAX_OTHER_ABS_Z": LOO_MAX_OTHER_ABS_Z,
            "RIDGE_EPS": RIDGE_EPS,
        },
        "results": {
            "feature_means_raw": dict(zip(FEATURE_NAMES, mu_full.tolist())),
            "feature_stds_raw": dict(zip(FEATURE_NAMES, sigma_full.tolist())),
            "lda_loading": dict(zip(FEATURE_NAMES, w_lda.tolist())),
            "mu_Q": dict(zip(FEATURE_NAMES, mu_Q.tolist())),
            "mu_R": dict(zip(FEATURE_NAMES, mu_R.tolist())),
            "fisher_ratio_J": J,
            "lda_score_per_corpus": score_per_corpus,
            "quran_lda_score": quran_score,
            "mean_lda_non_quran": mean_nq,
            "std_lda_non_quran": std_nq,
            "cv_lda_non_quran": cv_nq,
            "z_quran_lda": z_quran,
            "abs_z_quran_lda": abs_z_q,
            "max_other_abs_z_lda": max_other_abs_z,
            "z_per_corpus_lda": z_per_corpus,
            "unified_formula_string": unified_formula,
            "loo_results": loo_results,
            "loo_min_abs_z_quran": loo_min_z_quran,
            "loo_max_other_abs_z": loo_max_other_abs_z,
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
    print(f"# verdict (overall): {overall_verdict}")
    print(f"# verdict (full-pool): {verdict_full}")
    print(f"# verdict (LOO): {lda_robust_verdict}")
    print()
    print(f"## Unified linear formula (LDA on 11-pool):")
    print(f"  {unified_formula}")
    print()
    print(f"## Full-pool projection (sorted ascending; Quran is positive by convention):")
    sorted_corpora = sorted(score_per_corpus.items(), key=lambda kv: kv[1])
    for c, v in sorted_corpora:
        z = z_per_corpus[c]
        flag = "  <-- QURAN" if c == "quran" else ""
        print(f"  {c:20s}  alpha_LDA={v:+8.4f}  z={z:+8.2f}{flag}")
    print()
    print(f"# Quran |z|: {abs_z_q:.4f}    max_other|z|: {max_other_abs_z:.4f}")
    print(f"# Fisher ratio J: {J:.4f}")
    print()
    print(f"## LOO robustness ({len(loo_results)} iterations):")
    for r in loo_results:
        print(f"  drop={r['held_out']:20s}  |z_quran|_LOO={r['abs_z_quran_lda_loo']:6.2f}"
              f"  max_other|z|={r['max_other_abs_z_loo']:.2f}  J={r['fisher_ratio_J_loo']:.2f}")
    print(f"# LOO min |z_quran|: {loo_min_z_quran:.4f}")
    print(f"# LOO max max_other|z|: {loo_max_other_abs_z:.4f}")
    print(f"# wall_time_s: {receipt['wall_time_s']}")
    print(f"# receipt: {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
