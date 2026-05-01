"""
expParadigm2_OP2_feature_pair_search/run.py
============================================
Paradigm-Stage 2 — P2_OP2 partial: numerical feature-pair search.

Tests whether the canonical (X, Y) pairing
    X_canonical = primary triliteral root  (from CamelTools per-verse)
    Y_canonical = terminal letter
is at least a LOCAL optimum among cheap alternative pairings, in the sense
that no alternative pair produces a stronger Quran-vs-ctrl discrimination
on the entropy gap T = H_cond(X | X_prev) - H(Y).

Alternatives tested (all CamelTools-free; cheap to compute):
    X candidates (deep) — sequence of one token per verse:
      X_canonical           : (locked T, recomputed at canonical level)
      X_terminal_letter     : last alphabetic char of each verse
      X_first_letter_lastword: first alphabetic char of the verse-final word
      X_last_word_full      : the entire verse-final word (whitespace-split)
      X_last_bigram         : last 2 alphabetic chars of each verse
    Y candidates (surface):
      Y_canonical           : H(end_letter) per src.features.h_el
      Y_end_bigram          : H(last 2 alphabetic chars)
      Y_first_letter_lastword: H(first letter of last word)
      Y_last_word_full      : H(entire last word)

For each (X, Y) pair we compute T_alt = H_cond(X | X_prev) - H(Y) per
Band-A surah (n_verses ∈ [15, 100]). The DISCRIMINATION METRIC is

    Quran_T_pct_pos - max(ctrl_corpus_T_pct_pos)

(i.e., the gap in fraction of Band-A surahs with T_alt > 0 between Quran
and the strongest secular Arabic comparator). The canonical (root,
end-letter) pair has Quran_pct ≈ 0.397 and max-ctrl ≈ 0.001 (per S6),
gap ≈ 0.396. The local-optimum claim PASSES if no alternative pair
produces a larger gap.

Reads (read-only):
  - results/checkpoints/phase_06_phi_m.pkl
    * FEATS (per-surah canonical T values for all corpora) — for the
      canonical baseline pair.
    * CORPORA (verse strings per surah for all corpora) — for the
      alternative-pair entropy computations.

Writes:
  - results/experiments/expParadigm2_OP2_feature_pair_search/
      expParadigm2_OP2_feature_pair_search.json
"""

from __future__ import annotations

import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase,
    safe_output_dir,
    self_check_begin,
    self_check_end,
)

EXP = "expParadigm2_OP2_feature_pair_search"
BAND_A_LO, BAND_A_HI = 15, 100
ARABIC_LETTER = re.compile(r"[\u0621-\u064A]")


# ============================================================================
# X / Y token extractors (one token per verse)
# ============================================================================
def _alphabetic_chars(s: str) -> str:
    return "".join(ARABIC_LETTER.findall(s))


def _last_word(verse: str) -> str:
    """Return last whitespace-separated token (after stripping non-letter
    junk on both ends)."""
    toks = verse.strip().split()
    return toks[-1] if toks else ""


def _terminal_letter(verse: str) -> str:
    s = _alphabetic_chars(verse)
    return s[-1] if s else ""


def _first_letter_of_last_word(verse: str) -> str:
    w = _last_word(verse)
    s = _alphabetic_chars(w)
    return s[0] if s else ""


def _last_bigram(verse: str) -> str:
    s = _alphabetic_chars(verse)
    return s[-2:] if len(s) >= 2 else (s if s else "")


def _last_word_alphabetic_only(verse: str) -> str:
    """Last word with only Arabic letters (drop diacritics/punctuation)."""
    return _alphabetic_chars(_last_word(verse))


X_EXTRACTORS = {
    "X_terminal_letter":         _terminal_letter,
    "X_first_letter_lastword":   _first_letter_of_last_word,
    "X_last_word_full":          _last_word_alphabetic_only,
    "X_last_bigram":             _last_bigram,
}

Y_EXTRACTORS = {
    "Y_canonical_end_letter":    _terminal_letter,
    "Y_end_bigram":              _last_bigram,
    "Y_first_letter_lastword":   _first_letter_of_last_word,
    "Y_last_word_full":          _last_word_alphabetic_only,
}


# ============================================================================
# Entropy helpers
# ============================================================================
def _shannon_entropy_bits(values: list) -> float:
    n = len(values)
    if n == 0:
        return 0.0
    cnt = Counter(values)
    h = 0.0
    for c in cnt.values():
        if c > 0:
            p = c / n
            h -= p * math.log2(p)
    return h


def _conditional_entropy_bits(seq: list) -> float:
    """H(X_t | X_{t-1}) on a sequence of tokens. Equivalent to
    H(joint) - H(prev), where joint = (prev, curr) bigrams."""
    n = len(seq)
    if n < 2:
        return 0.0
    pairs = list(zip(seq[:-1], seq[1:]))
    cnt_pair = Counter(pairs)
    cnt_prev = Counter(seq[:-1])
    total = sum(cnt_pair.values())
    if total == 0:
        return 0.0
    h = 0.0
    by_prev: dict = {}
    for (a, b), n_ab in cnt_pair.items():
        by_prev.setdefault(a, Counter())[b] += n_ab
    for a, n_a in cnt_prev.items():
        p_a = n_a / total
        row = by_prev.get(a, Counter())
        row_total = sum(row.values())
        if row_total == 0:
            continue
        row_h = 0.0
        for c in row.values():
            if c > 0:
                p = c / row_total
                row_h -= p * math.log2(p)
        h += p_a * row_h
    return h


# ============================================================================
# Per-surah T for an (X, Y) pair
# ============================================================================
def _per_surah_T(verses: list[str], x_extract, y_extract) -> float:
    """T = H_cond(X | X_prev) - H(Y) for a single surah."""
    if len(verses) < 2:
        return float("nan")
    x_seq = [x_extract(v) for v in verses]
    y_seq = [y_extract(v) for v in verses]
    # Filter empty tokens (no Arabic letters)
    x_seq_clean = [t for t in x_seq if t]
    y_seq_clean = [t for t in y_seq if t]
    if len(x_seq_clean) < 2 or not y_seq_clean:
        return float("nan")
    h_cond = _conditional_entropy_bits(x_seq_clean)
    h_y = _shannon_entropy_bits(y_seq_clean)
    return h_cond - h_y


def _band_a_T_per_corpus(corpora: dict, x_extract, y_extract) -> dict:
    """For each corpus (whose units have verse-count in [LO, HI]), compute
    per-surah T, return dict of corpus → array of per-surah T."""
    out = {}
    for c, units in corpora.items():
        ts = []
        for u in units:
            verses = list(u.verses)
            if BAND_A_LO <= len(verses) <= BAND_A_HI:
                ts.append(_per_surah_T(verses, x_extract, y_extract))
        out[c] = np.asarray(
            [t for t in ts if math.isfinite(t)], dtype=float
        )
    return out


def _T_pct_pos(arr: np.ndarray) -> float:
    return float((arr > 0).mean()) if arr.size else float("nan")


# ============================================================================
# Discrimination metric
# ============================================================================
def _discrimination_metric(per_corpus: dict, ctrl_pool_names: list) -> dict:
    quran_arr = per_corpus.get("quran", np.array([]))
    if quran_arr.size == 0:
        return {"error": "no Quran data"}
    quran_pct = _T_pct_pos(quran_arr)
    ctrl_pcts = {}
    max_ctrl = -1.0
    max_ctrl_corpus = None
    for c in ctrl_pool_names:
        arr = per_corpus.get(c, np.array([]))
        pct = _T_pct_pos(arr)
        ctrl_pcts[c] = (pct, int(arr.size))
        if math.isfinite(pct) and pct > max_ctrl:
            max_ctrl = pct
            max_ctrl_corpus = c
    return {
        "quran_T_pct_pos": quran_pct,
        "ctrl_T_pct_pos_per_corpus": {
            c: {"pct_pos": v[0], "n_band_a": v[1]} for c, v in ctrl_pcts.items()
        },
        "max_ctrl_pct_pos": max_ctrl,
        "max_ctrl_corpus":  max_ctrl_corpus,
        "discrim_gap_quran_minus_max_ctrl": (quran_pct - max_ctrl
                                              if max_ctrl >= 0 else float("nan")),
        "n_quran_band_a": int(quran_arr.size),
    }


# ============================================================================
# Main
# ============================================================================
def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    corpora = state["CORPORA"]
    feats = state["FEATS"]
    ctrl_pool_names = list(state["ARABIC_CTRL_POOL"])
    print(f"[{EXP}] ctrl pool: {ctrl_pool_names}")
    print(f"[{EXP}] Band-A range: [{BAND_A_LO}, {BAND_A_HI}]")

    # =========== Canonical baseline (X = primary root, Y = end letter) ===========
    # Use locked per-surah T values from FEATS (no CamelTools needed).
    print(f"\n[{EXP}] === CANONICAL pair (X = primary root, Y = end letter) ===")
    canonical_T_per_corpus = {}
    for c in ["quran"] + ctrl_pool_names:
        ts = [r["T"] for r in feats.get(c, [])
              if BAND_A_LO <= r["n_verses"] <= BAND_A_HI
              and isinstance(r.get("T"), (int, float))
              and math.isfinite(r["T"])]
        canonical_T_per_corpus[c] = np.asarray(ts, dtype=float)
    canonical_metric = _discrimination_metric(
        canonical_T_per_corpus, ctrl_pool_names
    )
    print(f"[{EXP}]   Quran T_pct_pos: {canonical_metric['quran_T_pct_pos']:.4f}")
    print(f"[{EXP}]   max ctrl: {canonical_metric['max_ctrl_pct_pos']:.4f} "
          f"({canonical_metric['max_ctrl_corpus']})")
    print(f"[{EXP}]   discrim gap: "
          f"{canonical_metric['discrim_gap_quran_minus_max_ctrl']:+.4f}")

    # =========== Alternative-pair search (16 pairs) ===========
    print(f"\n[{EXP}] === ALTERNATIVE pairs (X × Y = "
          f"{len(X_EXTRACTORS)} × {len(Y_EXTRACTORS)} = "
          f"{len(X_EXTRACTORS) * len(Y_EXTRACTORS)} cheap pairs) ===")
    alt_results = []
    n_pairs_total = len(X_EXTRACTORS) * len(Y_EXTRACTORS)
    pair_i = 0
    for x_name, x_fn in X_EXTRACTORS.items():
        for y_name, y_fn in Y_EXTRACTORS.items():
            pair_i += 1
            t_pair = time.time()
            per_corpus = _band_a_T_per_corpus(corpora, x_fn, y_fn)
            metric = _discrimination_metric(per_corpus, ctrl_pool_names)
            metric["pair"] = f"{x_name} × {y_name}"
            metric["x_name"] = x_name
            metric["y_name"] = y_name
            metric["runtime_s"] = round(time.time() - t_pair, 2)
            alt_results.append(metric)
            print(f"[{EXP}]   [{pair_i:>2d}/{n_pairs_total}] "
                  f"{x_name:<28s} × {y_name:<26s}  "
                  f"Q={metric['quran_T_pct_pos']:.3f}  "
                  f"max_ctrl={metric['max_ctrl_pct_pos']:.3f}  "
                  f"gap={metric['discrim_gap_quran_minus_max_ctrl']:+.4f}  "
                  f"({metric['runtime_s']}s)", flush=True)

    # =========== Canonical-vs-alternatives ranking ===========
    canonical_gap = canonical_metric["discrim_gap_quran_minus_max_ctrl"]
    n_alts_better = sum(
        1 for a in alt_results
        if math.isfinite(a["discrim_gap_quran_minus_max_ctrl"])
        and a["discrim_gap_quran_minus_max_ctrl"] > canonical_gap
    )
    n_alts_total = sum(
        1 for a in alt_results
        if math.isfinite(a["discrim_gap_quran_minus_max_ctrl"])
    )

    if n_alts_better == 0:
        verdict = "P2_OP2_LOCAL_OPTIMUM_CONFIRMED"
    elif n_alts_better <= 2:
        verdict = "P2_OP2_NEAR_LOCAL_OPTIMUM_(<=2_alternatives_beat_it)"
    else:
        verdict = "P2_OP2_FALSIFIED_(>2_alternatives_beat_canonical)"

    # Sort alternatives by discrim gap (desc) for readable output
    alt_sorted = sorted(
        alt_results,
        key=lambda a: -a["discrim_gap_quran_minus_max_ctrl"]
        if math.isfinite(a["discrim_gap_quran_minus_max_ctrl"])
        else -float("inf"),
    )

    runtime = time.time() - t0
    report = {
        "experiment": EXP,
        "task_id": "P2_OP2 partial — feature-pair search (no CamelTools)",
        "title": (
            "Numerical local-optimum search: among 16 cheap alternative "
            "(X, Y) pairings of T = H_cond(X|X_prev) - H(Y), is the "
            "canonical (primary-root, end-letter) pair the strongest "
            "Quran-vs-secular-Arabic discriminator?"
        ),
        "method": (
            "Discrimination metric = Quran_T_pct_pos - max(ctrl_T_pct_pos). "
            "Canonical baseline taken from locked per-surah T values in "
            "phase_06_phi_m FEATS (no CamelTools re-run). 16 alternative "
            "pairs computed from cheap features (no CamelTools). Pre-reg: "
            "PASS if 0/16 alternatives beat the canonical gap."
        ),
        "band_A_range": [BAND_A_LO, BAND_A_HI],
        "n_alternatives_tested": int(n_alts_total),
        "canonical_baseline": {
            "x_name": "X_primary_root_CamelTools",
            "y_name": "Y_canonical_end_letter",
            **canonical_metric,
        },
        "alternative_pairs_sorted_by_gap_desc": alt_sorted,
        "n_alternatives_beating_canonical": int(n_alts_better),
        "verdict": verdict,
        "interpretation": [
            "If verdict = P2_OP2_LOCAL_OPTIMUM_CONFIRMED, no cheap "
            "alternative pair beats the canonical (root, end-letter). "
            "This is empirical evidence for local optimality of the "
            "canonical T pairing — consistent with P2_OP2's claim. The "
            "FORMAL P2_OP2 proof requires extending this to the full "
            "feature space (months of work).",
            "If verdict = P2_OP2_FALSIFIED, the canonical is NOT a local "
            "optimum. Investigate the winning alternative pair — it may "
            "be a stronger replacement for the project's T definition.",
            "Note: this search uses cheap (CamelTools-free) X candidates "
            "(end-letter, first-letter-of-last-word, last-word, "
            "last-bigram). The canonical X = primary triliteral root "
            "(via CamelTools) was NOT re-tested; we used the locked "
            "per-surah T values directly. A larger search would also "
            "vary X over morphological alternatives (lemma, POS-tag) — "
            "those need CamelTools, too slow for this session.",
        ],
        "runtime_seconds": round(runtime, 2),
    }

    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Stdout
    print()
    print(f"[{EXP}] -- ranking by discrim-gap descending --")
    print(f"[{EXP}]   {'rank':>4s}  {'gap':>8s}  {'pair':<55s}")
    print(f"[{EXP}]   {'CANON':>4s}  {canonical_gap:+.4f}  "
          f"X_primary_root × Y_canonical_end_letter  (locked)")
    for i, a in enumerate(alt_sorted, start=1):
        print(f"[{EXP}]   {i:>4d}  "
              f"{a['discrim_gap_quran_minus_max_ctrl']:+.4f}  "
              f"{a['pair']:<55s}")
    print()
    print(f"[{EXP}] {n_alts_better}/{n_alts_total} alternative pairs beat "
          f"the canonical gap ({canonical_gap:+.4f})")
    print(f"[{EXP}] verdict: {verdict}")
    print(f"[{EXP}] runtime: {runtime:.1f}s")
    print(f"[{EXP}] wrote {out / f'{EXP}.json'}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
