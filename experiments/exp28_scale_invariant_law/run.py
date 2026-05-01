"""
exp28_scale_invariant_law/run.py
================================
Scale-invariant Markov-1 law audit — 4-scale unifier.

Hypothesis (2026-04-20 external review):
    The Quran exhibits bigram sufficiency at EVERY scale simultaneously:
        L0 character within word  (exp27, NEW)
        L1 root  at verse boundary (T11, locked)
        L2 verse-length coherence  (T32 / F6, locked)
        L3 surah-order path        (T8, locked)
    If all four show Quran-extremal bigram / Markov-1 dominance, this is
    a Zipf-class universal law candidate.

Output
    exp28_scale_invariant_law.json with:
      * per-scale Cohen d, Quran rank, verdict
      * a root-vs-char GAP metric (char_H3/H2 - root_H3/H2) per corpus
        that might itself be a Quran-specific fingerprint even if the
        uniform scale-invariance claim fails
      * overall verdict: HOLDS / PARTIAL / FAILS

Reads (integrity-checked via self_check_begin/end):
    results/CLEAN_PIPELINE_REPORT.json  (T11, T28, T32/F6, T8)
    results/experiments/exp27_hchar_bigram/exp27_hchar_bigram.json

Writes ONLY under results/experiments/exp28_scale_invariant_law/:
    exp28_scale_invariant_law.json
    self_check_<ts>.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    safe_output_dir,
    self_check_begin,
    self_check_end,
)

EXP = "exp28_scale_invariant_law"

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

# --------------------------------------------------------------------------- #
# Readers                                                                     #
# --------------------------------------------------------------------------- #
def _load_clean_report() -> dict:
    p = _ROOT / "results" / "CLEAN_PIPELINE_REPORT.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_exp27() -> dict:
    p = (
        _ROOT / "results" / "experiments" / "exp27_hchar_bigram"
        / "exp27_hchar_bigram.json"
    )
    if not p.exists():
        raise FileNotFoundError(
            f"exp27 output missing: {p}. Run exp27_hchar_bigram first."
        )
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
# Per-scale extractors                                                        #
# --------------------------------------------------------------------------- #
def _scale_L0_char_root(exp27: dict) -> dict:
    """L0a: intra-word character H3/H2 (exp27)."""
    pooled = exp27["per_corpus_pooled"]
    ranking = exp27["pooled_H3_over_H2_ranking_low_is_more_markov2"]
    quran_rank = exp27["quran_rank_pooled_H3_over_H2"]
    s = exp27["quran_vs_arabic_ctrl_summary"]
    # sign convention: Cohen d < 0 supports the law (Quran MORE Markov-1)
    d_supports_law = (
        s["H3_over_H2_cohen_d"] < 0
        and (s["H3_over_H2_mwu_p_less"] is not None
             and s["H3_over_H2_mwu_p_less"] < 0.05)
    )
    return {
        "scale": "L0_char_intra_word",
        "metric": "char H3/H2 (intra-word, '#'-separated)",
        "direction": "lower == more Markov-1-sufficient",
        "per_corpus_pooled_ratio": {
            k: v["H3_over_H2"] for k, v in pooled.items()
        },
        "ranking_low_is_better": ranking,
        "quran_rank_1_is_best": quran_rank,
        "n_corpora_ranked": len(ranking),
        "per_unit_quran_mean": s["H3_over_H2_quran_mean"],
        "per_unit_ctrl_mean": s["H3_over_H2_ctrl_mean"],
        "per_unit_cohen_d_q_minus_c": s["H3_over_H2_cohen_d"],
        "per_unit_mwu_p_less": s["H3_over_H2_mwu_p_less"],
        "law_supported": bool(d_supports_law and quran_rank == 1),
        "source": "exp27_hchar_bigram (2026-04-20, new)",
    }


def _scale_L1_root_verse_boundary(T11: dict) -> dict:
    """L1: verse-final root H3/H2 (T11, locked)."""
    per = T11["per_corpus"]
    ranking = T11["ranking_low_is_better"]
    q_rank = T11["quran_rank_low_ratio"]
    return {
        "scale": "L1_root_verse_boundary",
        "metric": "root H3/H2 on verse-final roots (CamelTools)",
        "direction": "lower == more Markov-1-sufficient",
        "per_corpus_pooled_ratio": {
            k: v["ratio_H3_over_H2"] for k, v in per.items()
        },
        "ranking_low_is_better": ranking,
        "quran_rank_1_is_best": q_rank,
        "n_corpora_ranked": len(ranking),
        "law_supported": bool(q_rank == 1),
        "source": "T11 locked (src/extended_tests.py:test_bigram_sufficiency)",
    }


def _scale_L1b_root_markov_order(T28: dict) -> dict:
    """L1b: root H2/H1 ratio (Markov-2-over-Markov-1 overhead, T28, locked)."""
    per = T28["per_corpus"]
    q_mean = T28["quran_H2_over_H1_mean"]
    c_mean = T28["ctrl_H2_over_H1_mean"]
    d = T28["cohens_d_quran_vs_ctrl"]
    p = T28["p_mwu_less"]
    # T28 paper claim: "Quran needs LESS additional info from M-2".
    # sign convention: d < 0 would support that; measured d_Q-C is
    # actually POSITIVE in the locked report (Quran MEAN > ctrl MEAN).
    law_supported = (d is not None and d < 0) and (
        p is not None and p < 0.05
    )
    return {
        "scale": "L1b_root_markov_order_H2_over_H1",
        "metric": "root H2/H1 (overhead of order-2 beyond order-1)",
        "direction": "lower == more Markov-1-sufficient",
        "per_corpus_H2_over_H1_mean": {
            k: v.get("H2_over_H1_mean") for k, v in per.items()
        },
        "quran_mean": q_mean,
        "ctrl_mean": c_mean,
        "cohens_d_q_minus_c": d,
        "mwu_p_less": p,
        "law_supported": bool(law_supported),
        "source": "T28 locked (src/extended_tests3.py:test_markov_order_sufficiency)",
    }


def _scale_L2_verse_length_coherence(T32: dict) -> dict:
    """L2: F6 lag-1 Spearman ρ(len_i, len_{i+1}), Band-A (T32, locked).
    NOT a bigram-sufficiency claim by itself; it is a coherence claim
    at the verse-length scale. Included for completeness of the 4-scale
    story per the feedback."""
    q = T32["quran"]
    c = T32["pool_ctrl"]
    d = T32["cohens_d_pool"]
    p_two = T32["p_mwu_two_sided"]
    # Feedback's framing: positive d indicates multi-step coherence,
    # which is "Markov-1 sufficient for lengths" (lag-1 dominates).
    # The locked F6 sign is POSITIVE d ≈ +0.83.
    law_supported = (
        d is not None and d > 0.5
        and p_two is not None and p_two < 0.05
    )
    return {
        "scale": "L2_verse_length_coherence",
        "metric": "F6 = Spearman rho(len_i, len_{i+1}) within a unit",
        "direction": "higher == stronger lag-1 coherence (Markov-1-like)",
        "quran_mean": q.get("mean"),
        "ctrl_mean": c.get("mean"),
        "cohens_d_q_minus_c_pool": d,
        "mwu_p_two_sided": p_two,
        "law_supported": bool(law_supported),
        "source": "T32 locked (src/extended_tests4.py: F6 length coherence)",
    }


def _scale_L3_path_minimality(T8: dict) -> dict:
    """L3: canonical surah-order path z-score (T8, locked).

    CLEAN_PIPELINE_REPORT schema (verified 2026-04-20):
        per_corpus[quran] = {
            'n', 'canon_path_cost', 'perm_cost_mean',
            'z_path', 'pct_path_below_canon',
            'canon_adj_var', 'pct_adj_var_below_canon',
        }
    'pct_path_below_canon' is the empirical one-sided p (percentage of
    random permutations whose path cost is BELOW the canonical cost;
    smaller = more optimal canonical order).
    """
    per = T8.get("per_corpus", {})
    q = per.get("quran", {})
    z = q.get("z_path") if q else None
    pct_below = q.get("pct_path_below_canon") if q else None
    # pct is in percent (e.g. 0.5 means 0.5%); convert to fraction for
    # the 0.05 threshold.
    p_empirical = (pct_below / 100.0) if isinstance(pct_below, (int, float)) else None
    law_supported = (z is not None and z < -2.0) and (
        p_empirical is not None and p_empirical < 0.05
    )
    return {
        "scale": "L3_surah_order_path_minimality",
        "metric": "canonical-order path z vs 2000 random permutations",
        "direction": "lower z (more negative) == more optimal canonical order",
        "quran_z_path": z,
        "quran_pct_perms_below_canon": pct_below,
        "quran_p_empirical_one_sided": p_empirical,
        "quran_canon_path_cost": q.get("canon_path_cost") if q else None,
        "quran_perm_cost_mean": q.get("perm_cost_mean") if q else None,
        "law_supported": bool(law_supported),
        "source": "T8 locked (src/extended_tests.py:test_path_optimality)",
    }


# --------------------------------------------------------------------------- #
# Char-vs-root GAP: new candidate fingerprint                                 #
# --------------------------------------------------------------------------- #
def _char_root_gap(L0: dict, L1: dict) -> dict:
    """For every corpus present in BOTH L0 (char) and L1 (root),
    compute gap = char_H3_over_H2 - root_H3_over_H2.

    Meaning:
      * small char ratio + small root ratio -> Markov-1 at both scales
      * small root ratio + large char ratio -> Quran-locked finding
      * large gap = "highly organized at root scale relative to char
        scale" -- this is a candidate new Quran-specific fingerprint
        even though the uniform scale-invariance claim fails.
    """
    char_r = L0["per_corpus_pooled_ratio"]
    root_r = L1["per_corpus_pooled_ratio"]
    common = sorted(set(char_r) & set(root_r))
    if not common:
        return {"gap_available": False}
    rows = []
    for c in common:
        ch = char_r.get(c)
        rt = root_r.get(c)
        if ch is None or rt is None or not math.isfinite(ch) or not math.isfinite(rt):
            continue
        rows.append((c, ch, rt, ch - rt))
    # rank by gap (high gap = Markov-1 stronger at root than char)
    rows_sorted = sorted(rows, key=lambda x: -x[3])
    quran_rank_high_gap = next(
        (i + 1 for i, (c, *_r) in enumerate(rows_sorted) if c == "quran"),
        None,
    )
    return {
        "gap_available": True,
        "gap_definition": "char_H3/H2  -  root_H3/H2  (both pooled)",
        "per_corpus": [
            {"corpus": c, "char_H3_H2": ch, "root_H3_H2": rt, "gap": g}
            for (c, ch, rt, g) in rows
        ],
        "ranking_high_gap_is_more_root_locked": [
            {"corpus": c, "gap": g} for (c, _, __, g) in rows_sorted
        ],
        "quran_rank_high_gap_1_is_best": quran_rank_high_gap,
        "is_new_quran_fingerprint": bool(quran_rank_high_gap == 1),
    }


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #
def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    clean = _load_clean_report()
    exp27 = _load_exp27()
    res = clean.get("results", {})

    # Pull each locked scale
    L0 = _scale_L0_char_root(exp27)
    L1 = _scale_L1_root_verse_boundary(res["T11_bigram_suf"])
    L1b = _scale_L1b_root_markov_order(res["T28_markov_order"])
    L2 = _scale_L2_verse_length_coherence(res["T32_f6_length_coherence"])
    L3 = _scale_L3_path_minimality(res["T8_path"])
    GAP = _char_root_gap(L0, L1)

    scales: list[dict] = [L0, L1, L1b, L2, L3]
    n_supported = sum(1 for s in scales if s["law_supported"])
    n_total = len(scales)

    # Verdict rubric
    if n_supported == n_total:
        verdict = "SCALE_INVARIANT_LAW_HOLDS"
    elif n_supported >= 3:
        verdict = "PARTIAL_LAW_HOLDS_AT_MAJORITY_SCALES"
    elif n_supported == 2:
        verdict = "LAW_HOLDS_AT_MINORITY_SCALES"
    else:
        verdict = "LAW_DOES_NOT_HOLD"

    headline_table = []
    for s in scales:
        headline_table.append({
            "scale": s["scale"],
            "metric": s["metric"],
            "direction": s["direction"],
            "law_supported": s["law_supported"],
        })

    report: dict[str, Any] = {
        "experiment": EXP,
        "schema_version": 1,
        "hypothesis": (
            "Scale-invariant Markov-1 law: the Quran exhibits bigram "
            "sufficiency at 4 independent scales (L0 chars, L1 roots, "
            "L2 verse-lengths, L3 surah-path) simultaneously."
        ),
        "scales": {
            "L0_char_intra_word": L0,
            "L1_root_verse_boundary": L1,
            "L1b_root_markov_order": L1b,
            "L2_verse_length_coherence": L2,
            "L3_surah_order_path": L3,
        },
        "char_root_gap_analysis": GAP,
        "headline_table": headline_table,
        "n_scales_supported": n_supported,
        "n_scales_total": n_total,
        "verdict": verdict,
        "interpretation": _interpretation(scales, GAP, verdict),
        "provenance": {
            "t11_source": "results/CLEAN_PIPELINE_REPORT.json#results.T11_bigram_suf",
            "t28_source": "results/CLEAN_PIPELINE_REPORT.json#results.T28_markov_order",
            "t32_source": "results/CLEAN_PIPELINE_REPORT.json#results.T32_f6_length_coherence",
            "t8_source":  "results/CLEAN_PIPELINE_REPORT.json#results.T8_path",
            "exp27_source": "results/experiments/exp27_hchar_bigram/exp27_hchar_bigram.json",
            "clean_report_status": clean.get("status"),
            "corpus_fingerprint": clean.get("corpus_fingerprint"),
        },
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # -------------------- console ---------------------------------------- #
    print(f"[{EXP}] wrote {outfile}")
    print(f"[{EXP}] --- 4-scale headline ---")
    for s in scales:
        flag = "SUPPORTS" if s["law_supported"] else "FAILS"
        print(f"   {s['scale']:42s}  {flag}")
    print(f"[{EXP}] n_scales_supported = {n_supported}/{n_total}")
    print(f"[{EXP}] VERDICT: {verdict}")
    if GAP.get("gap_available"):
        qg = GAP.get("quran_rank_high_gap_1_is_best")
        print(f"[{EXP}] char-root GAP: Quran rank (high=best) = {qg}  "
              f"-> new-fingerprint candidate = {GAP.get('is_new_quran_fingerprint')}")

    self_check_end(pre, EXP)
    return 0


def _interpretation(scales: list[dict], gap: dict, verdict: str) -> str:
    lines = []
    ok = [s["scale"] for s in scales if s["law_supported"]]
    ko = [s["scale"] for s in scales if not s["law_supported"]]
    lines.append(f"Law SUPPORTED at: {ok}")
    lines.append(f"Law FAILS at:     {ko}")
    if verdict == "SCALE_INVARIANT_LAW_HOLDS":
        lines.append(
            "All 4 scales agree -- promote to paper as a Zipf-class "
            "universal-law candidate. Cross-scripture replication "
            "required before headline claim."
        )
    else:
        lines.append(
            "Uniform scale-invariance claim is NOT supported. Report "
            "the scales that DO hold as separate locked findings. "
            "Revise any paper text that implied character-scale "
            "bigram-sufficiency for the Quran. Character-scale ratio "
            "rankings are dominated by genre/meter effects (see exp27 "
            "ranking: ksucca < quran < poetry), not by Quran-specific "
            "structure."
        )
    if gap.get("gap_available"):
        if gap.get("is_new_quran_fingerprint"):
            lines.append(
                "NEW candidate finding: the gap between character-level "
                "H3/H2 and root-level H3/H2 is largest for the Quran. "
                "That is a scale-DEPENDENT signature (not scale-invariant) "
                "but may still be publishable as a Quran-specific "
                "'root-character-gap' fingerprint. Requires its own "
                "permutation test and cross-scripture control before "
                "paper promotion."
            )
        else:
            lines.append(
                "Char-root gap does NOT rank Quran #1. No new "
                "fingerprint candidate from this angle."
            )
    return "  |  ".join(lines)


if __name__ == "__main__":
    sys.exit(main())
