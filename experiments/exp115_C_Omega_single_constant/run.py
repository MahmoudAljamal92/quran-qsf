"""exp115_C_Omega_single_constant — single information-theoretic constant C_Ω.

C_Ω(text, A) := 1 − H_EL(text) / log₂(A) ∈ [0, 1]

Information-theoretic interpretation: fraction of the alphabet's maximum entropy
that is used for rhyme prediction. = I(end-letter; text) / log₂(A).

Tests whether the Quran is the unique global C_Ω maximum across 12 cross-tradition
corpora at the locked margin Quran/rank-2 ≥ 1.3.

Prereg: experiments/exp115_C_Omega_single_constant/PREREG.md
Hypothesis ID: H70.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import stats as scs

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

EXP114_RECEIPT = ROOT / "results/experiments/exp114_alphabet_independent_pmax/exp114_alphabet_independent_pmax.json"
N_PERMS = 10_000
SEED = 42
LOCKED_RATIO_FLOOR = 1.3
LOCKED_Z_FLOOR = -2.0


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    out_dir = ROOT / "results" / "experiments" / "exp115_C_Omega_single_constant"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load exp114 receipt
    exp114 = json.load(open(EXP114_RECEIPT, encoding="utf-8"))
    rows = exp114["per_corpus"]

    # Compute C_Ω = 1 - R_HEL for each corpus
    for r in rows:
        r["C_Omega"] = 1.0 - r["R_HEL_normalised"]

    # Sort descending by C_Omega
    rows_sorted = sorted(rows, key=lambda r: -r["C_Omega"])
    quran_idx = next(i for i, r in enumerate(rows_sorted) if r["corpus"] == "quran")

    quran_C_Omega = next(r["C_Omega"] for r in rows_sorted if r["corpus"] == "quran")
    quran_rank = quran_idx + 1
    quran_is_rank1 = quran_rank == 1
    rank2_C_Omega = rows_sorted[1]["C_Omega"] if quran_is_rank1 else rows_sorted[0]["C_Omega"]
    ratio_quran_rank2 = quran_C_Omega / rank2_C_Omega
    margin_pass = ratio_quran_rank2 >= LOCKED_RATIO_FLOOR

    # Form-A: rank-based perm-null (will saturate at 1/N)
    rng = np.random.default_rng(SEED)
    omega_vec = np.array([r["C_Omega"] for r in rows])
    quran_pos = next(i for i, r in enumerate(rows) if r["corpus"] == "quran")
    null_count_a = 0
    for _ in range(N_PERMS):
        perm = rng.permutation(len(omega_vec))
        shuffled = omega_vec[perm]
        if shuffled[quran_pos] == np.max(shuffled):
            null_count_a += 1
    perm_p_a = null_count_a / N_PERMS

    # Form-B: z-score parametric (primary)
    others_arr = np.array([r["C_Omega"] for r in rows if r["corpus"] != "quran"])
    peer_mean = float(np.mean(others_arr))
    peer_std = float(np.std(others_arr, ddof=1))
    quran_z = (quran_C_Omega - peer_mean) / peer_std if peer_std > 0 else 0.0
    parametric_p_t = float(1.0 - scs.t.cdf(quran_z, df=len(others_arr) - 1))  # one-tailed (upper)
    z_pass = quran_z >= -LOCKED_Z_FLOOR  # i.e. z >= 2.0

    # Decision
    if quran_is_rank1 and margin_pass and z_pass and parametric_p_t < 0.05:
        verdict = "PASS_quran_unique_C_Omega_max"
    elif not quran_is_rank1:
        verdict = "FAIL_quran_not_rank_1"
    elif not margin_pass:
        verdict = "FAIL_margin_below_1_3"
    elif not z_pass:
        verdict = "FAIL_z_above_minus_2"
    else:
        verdict = "FAIL_parametric_p_above_0_05"

    finished = datetime.now(timezone.utc).isoformat()
    receipt = {
        "experiment": "exp115_C_Omega_single_constant",
        "hypothesis_id": "H70",
        "verdict": verdict,
        "started_at_utc": started,
        "completed_at_utc": finished,
        "prereg_document": "experiments/exp115_C_Omega_single_constant/PREREG.md",
        "prereg_sha256": _sha256(ROOT / "experiments/exp115_C_Omega_single_constant/PREREG.md"),
        "frozen_constants": {
            "FORMULA": "C_Omega(text, A) := 1 - H_EL(text) / log2(A)",
            "INTERPRETATION": "fraction of alphabet's max entropy used for rhyme prediction; = I(end-letter; text) / log2(A)",
            "RATIO_FLOOR_QURAN_OVER_RANK2": LOCKED_RATIO_FLOOR,
            "Z_FLOOR_QURAN_VS_PEERS": LOCKED_Z_FLOOR,
            "N_PERMS": N_PERMS,
            "SEED": SEED,
        },
        "source_receipt_sha256": {"exp114": _sha256(EXP114_RECEIPT)},
        "ranked_corpora_by_C_Omega_desc": [
            {
                "corpus": r["corpus"],
                "alphabet_size": r["alphabet_size"],
                "H_EL_bits": r["H_EL_bits"],
                "R_HEL_normalised": r["R_HEL_normalised"],
                "C_Omega": r["C_Omega"],
                "is_oral_canon": r["is_oral_canon"],
            } for r in rows_sorted
        ],
        "quran_C_Omega": quran_C_Omega,
        "quran_rank": quran_rank,
        "rank2_C_Omega": rank2_C_Omega,
        "ratio_quran_to_rank2": ratio_quran_rank2,
        "margin_pass_at_1_3": margin_pass,
        "form_A_rank_based_perm_null": {
            "perm_p_quran_global_max": perm_p_a,
            "perm_n": N_PERMS,
            "perm_seed": SEED,
            "note": "saturates at 1/N=0.083 with N=12; see form_B for non-saturating test.",
        },
        "form_B_z_score_parametric": {
            "peer_mean": peer_mean,
            "peer_std": peer_std,
            "quran_z_vs_peers": quran_z,
            "parametric_p_t_one_tailed_upper": parametric_p_t,
            "z_pass_at_minus_2": z_pass,
            "p_pass_at_0_05": parametric_p_t < 0.05,
        },
        "audit_report": {
            "ok": all([
                len(rows) == 12,
                exp114["audit_report"]["ok"],
            ]),
            "n_corpora": len(rows),
            "exp114_audit_ok": exp114["audit_report"]["ok"],
        },
    }

    out_path = out_dir / "exp115_C_Omega_single_constant.json"
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n=== exp115 — C_Omega Single Information-Theoretic Constant ===\n")
    print(f"Formula: C_Ω(text, A) := 1 − H_EL(text) / log₂(A)")
    print(f"Interpretation: fraction of alphabet entropy used for rhyme prediction\n")
    print(f"{'Rank':<5} {'Corpus':<18} {'A':>3} {'H_EL':>8} {'C_Ω':>8} {'oral?':>6}")
    print("-" * 60)
    for i, r in enumerate(rows_sorted):
        flag = "ORAL" if r["is_oral_canon"] else "secul"
        print(f"{i+1:<5} {r['corpus']:<18} {r['alphabet_size']:>3} {r['H_EL_bits']:>8.4f} {r['C_Omega']:>8.4f} {flag:>6}")
    print(f"\n--- Decision-rule checks ---")
    print(f"  Quran C_Ω = {quran_C_Omega:.4f} (rank {quran_rank}/12)")
    print(f"  Rank-2 C_Ω = {rank2_C_Omega:.4f} ({rows_sorted[1]['corpus']})")
    print(f"  Ratio Quran/rank-2 = {ratio_quran_rank2:.4f}  (floor = {LOCKED_RATIO_FLOOR}, pass = {margin_pass})")
    print(f"  Form-A perm-p (rank-based, saturated): {perm_p_a:.4f}")
    print(f"  Form-B Quran z vs 11 peers = {quran_z:+.4f}  (floor = {-LOCKED_Z_FLOOR}, pass = {z_pass})")
    print(f"  Form-B parametric p (one-tailed upper) = {parametric_p_t:.6f}")
    print(f"\nVerdict: {verdict}")
    print(f"Receipt: {out_path.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
