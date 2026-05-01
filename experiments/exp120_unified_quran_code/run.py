"""exp120_unified_quran_code — Unified Quran-Code D_QSF (V3.12).

Re-analyses the 11-corpus × 5-feature matrix from exp109 through a unified
composite distance D_QSF and tests whether the Quran is the unique global
extremum under permutation null.

Verdict: PASS_unified_quran_code_quran_rank_1 / PARTIAL_quran_rank_1_perm_p_above_0p05
       / FAIL_quran_not_rank_1_under_DQSF

Prereg: experiments/exp120_unified_quran_code/PREREG.md
Hypothesis ID: H75.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# ----- Frozen constants (mirror PREREG) ------------------------------------
SEED = 42
N_PERMUTATIONS = 10_000
PERM_ALPHA = 0.05

FEATURE_NAMES = [
    "VL_CV",
    "p_max",
    "H_EL",
    "bigram_distinct_ratio",
    "gzip_efficiency",
]
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

EXP_NAME = "exp120_unified_quran_code"
HYPOTHESIS_ID = "H75"
HYPOTHESIS_TEXT = (
    "Under D_QSF — Euclidean distance of per-corpus medians from the "
    "11-corpus centroid in a 5-feature standardised universal space — "
    "the Quran is the unique global extremum (rank 1) with permutation "
    "p < 0.05 against random corpus-label shuffling."
)

PREREG_PATH = ROOT / "experiments" / EXP_NAME / "PREREG.md"
INPUT_SIZING_JSON = ROOT / "results" / "auxiliary" / "_phi_universal_xtrad_sizing.json"
RECEIPT_DIR = ROOT / "results" / "experiments" / EXP_NAME
RECEIPT_PATH = RECEIPT_DIR / f"{EXP_NAME}.json"


# ----- Helpers --------------------------------------------------------------
def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def compute_d_qsf(matrix: np.ndarray) -> np.ndarray:
    """matrix: shape (n_corpora, n_features). Returns D_QSF per corpus."""
    mu = matrix.mean(axis=0)
    sigma = matrix.std(axis=0, ddof=0)
    sigma_safe = np.where(sigma > 1e-12, sigma, 1.0)
    z = (matrix - mu) / sigma_safe
    return np.sqrt((z * z).sum(axis=1))


# ----- Main -----------------------------------------------------------------
def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)

    sizing = json.loads(INPUT_SIZING_JSON.read_text(encoding="utf-8"))
    medians = sizing["medians"]
    assert sizing["features"] == FEATURE_NAMES, "feature list drift"
    for c in EXPECTED_CORPORA:
        assert c in medians, f"missing corpus: {c}"

    matrix = np.array(
        [[medians[c][f] for f in FEATURE_NAMES] for c in EXPECTED_CORPORA],
        dtype=float,
    )
    n_corpora, n_features = matrix.shape
    assert n_corpora == 11 and n_features == 5

    d_qsf = compute_d_qsf(matrix)
    order = np.argsort(-d_qsf)  # descending: highest D_QSF = rank 1
    ranks = np.empty(n_corpora, dtype=int)
    ranks[order] = np.arange(1, n_corpora + 1)

    quran_idx = EXPECTED_CORPORA.index("quran")
    quran_d_qsf = float(d_qsf[quran_idx])
    quran_rank = int(ranks[quran_idx])

    sorted_d = d_qsf[order]
    rank_2_d_qsf = float(sorted_d[1])
    margin = float(sorted_d[0] - sorted_d[1])

    per_corpus = {
        EXPECTED_CORPORA[i]: {
            "D_QSF": float(d_qsf[i]),
            "rank": int(ranks[i]),
            "z_scores": {
                FEATURE_NAMES[j]: float(
                    (matrix[i, j] - matrix[:, j].mean())
                    / max(matrix[:, j].std(ddof=0), 1e-12)
                )
                for j in range(n_features)
            },
        }
        for i in range(n_corpora)
    }

    # ----- Permutation null -------------------------------------------------
    # Correct null: independently shuffle each feature COLUMN across the 11
    # corpora. This breaks the multivariate signature (Quran's medians get
    # scrambled across features) while preserving the marginal feature
    # distributions. Tests: "is the Quran's *combination* of feature values
    # uniquely extremal, or is it just chance that one corpus ends up
    # extremum given the marginals?".
    #
    # NOTE: a row-only permutation is a no-op since compute_d_qsf is
    # invariant under row reordering (means and stds are pooled). The
    # column-shuffle null is the one with non-trivial discrimination.
    rng = np.random.default_rng(SEED)
    quran_rank1_count = 0
    for _ in range(N_PERMUTATIONS):
        perm_matrix = matrix.copy()
        for j in range(n_features):
            perm_j = rng.permutation(n_corpora)
            perm_matrix[:, j] = matrix[perm_j, j]
        perm_d = compute_d_qsf(perm_matrix)
        perm_order = np.argsort(-perm_d).tolist()
        perm_quran_rank = perm_order.index(quran_idx) + 1
        if perm_quran_rank == 1:
            quran_rank1_count += 1
    perm_p = quran_rank1_count / N_PERMUTATIONS

    # ----- Bootstrap CI on margin (10k resamples of 11 corpora w/ replacement)
    boot_rng = np.random.default_rng(SEED + 1)
    boot_quran_d = []
    boot_margin = []
    for _ in range(1000):
        idx = boot_rng.integers(0, n_corpora, size=n_corpora)
        boot_matrix = matrix[idx]
        boot_d = compute_d_qsf(boot_matrix)
        boot_quran_d.append(float(boot_d[idx.tolist().index(quran_idx)])
                             if quran_idx in idx.tolist() else float("nan"))
        boot_sorted = np.sort(boot_d)[::-1]
        boot_margin.append(float(boot_sorted[0] - boot_sorted[1]))
    boot_quran_d_arr = np.array([x for x in boot_quran_d if not np.isnan(x)])
    boot_margin_arr = np.array(boot_margin)

    quran_d_ci = (
        [float(np.percentile(boot_quran_d_arr, 2.5)),
         float(np.percentile(boot_quran_d_arr, 97.5))]
        if len(boot_quran_d_arr) > 0 else [None, None]
    )
    margin_ci = [
        float(np.percentile(boot_margin_arr, 2.5)),
        float(np.percentile(boot_margin_arr, 97.5)),
    ]

    # ----- Verdict ---------------------------------------------------------
    if quran_rank == 1 and perm_p < PERM_ALPHA:
        verdict = "PASS_unified_quran_code_quran_rank_1"
    elif quran_rank == 1:
        verdict = "PARTIAL_quran_rank_1_perm_p_above_0p05"
    else:
        verdict = "FAIL_quran_not_rank_1_under_DQSF"

    verdict_reason = (
        f"D_QSF(Quran) = {quran_d_qsf:.4f} (rank {quran_rank} of {n_corpora}); "
        f"D_QSF(rank-2) = {rank_2_d_qsf:.4f}; margin = {margin:.4f}; "
        f"perm_p = {perm_p:.6f} (PERM_ALPHA = {PERM_ALPHA})."
    )

    # ----- Audit hooks (PREREG-discipline checks) --------------------------
    audit_report = {
        "ok": True,
        "checks": {
            "feature_list_match": sizing["features"] == FEATURE_NAMES,
            "corpus_list_match": all(c in medians for c in EXPECTED_CORPORA),
            "matrix_shape": [int(matrix.shape[0]), int(matrix.shape[1])],
            "no_nan": bool(not np.isnan(matrix).any()),
            "z_finite": bool(np.isfinite(d_qsf).all()),
        },
    }
    if not all(audit_report["checks"].values()):
        audit_report["ok"] = False
        verdict = "FAIL_audit_" + ",".join(
            k for k, v in audit_report["checks"].items() if not v
        )

    # ----- Receipt ---------------------------------------------------------
    receipt = {
        "experiment": EXP_NAME,
        "hypothesis_id": HYPOTHESIS_ID,
        "hypothesis": HYPOTHESIS_TEXT,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "started_at_utc": started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "prereg_hash": sha256_file(PREREG_PATH),
        "frozen_constants": {
            "SEED": SEED,
            "N_PERMUTATIONS": N_PERMUTATIONS,
            "PERM_ALPHA": PERM_ALPHA,
            "FEATURE_NAMES": FEATURE_NAMES,
            "EXPECTED_CORPORA": EXPECTED_CORPORA,
        },
        "audit_report": audit_report,
        "results": {
            "D_QSF_quran": quran_d_qsf,
            "D_QSF_rank_quran": quran_rank,
            "D_QSF_rank_2_value": rank_2_d_qsf,
            "D_QSF_margin": margin,
            "perm_p_quran_rank_1": perm_p,
            "perm_alpha": PERM_ALPHA,
            "n_permutations": N_PERMUTATIONS,
            "bootstrap_quran_D_QSF_95CI": quran_d_ci,
            "bootstrap_margin_95CI": margin_ci,
        },
        "per_corpus": per_corpus,
        "input_sizing_sha256": sha256_file(INPUT_SIZING_JSON),
    }

    RECEIPT_PATH.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[{EXP_NAME}] Wrote receipt: {RECEIPT_PATH}")
    print(f"[{EXP_NAME}] verdict: {verdict}")
    print(f"[{EXP_NAME}] D_QSF(Quran) = {quran_d_qsf:.4f}, rank {quran_rank}/{n_corpora}, "
          f"margin={margin:.4f}, perm_p={perm_p:.6f}")
    print(f"[{EXP_NAME}] D_QSF ranking:")
    for i in order:
        c = EXPECTED_CORPORA[i]
        print(f"   rank {ranks[i]:2d}  {c:20s}  D_QSF = {d_qsf[i]:.4f}")


if __name__ == "__main__":
    main()
