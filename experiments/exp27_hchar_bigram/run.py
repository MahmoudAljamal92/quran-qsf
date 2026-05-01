"""
exp27_hchar_bigram/run.py
=========================
Character-bigram sufficiency within words (H_char_3 / H_char_2 and
H_char_2 / H_char_1) -- the character-level analog of T11 / T28.

Hypothesis (from 2026-04-20 external review):
    If the Quran's intra-word character bigrams are 'sufficient' in the
    same Markov sense that root bigrams are at the verse-transition
    scale (T11: H3/H2 = 0.096, rank 1/6) and that verse-length bigrams
    are at the surah scale (F6 lag-1 d = +0.877), then a SCALE-INVARIANT
    MARKOV-1 LAW holds at 4 independent scales simultaneously:
        character -> root -> verse-length -> surah-order.
    That is a Zipf-class universal claim suitable for PNAS.

Protocol
    * Band-A gate:        [15, 100] verses per unit (same as T11).
    * Arabic controls:    poetry_jahili/islami/abbasi, ksucca,
                          arabic_bible, hindawi (hadith quarantined,
                          matches src/extended_tests.py ARABIC_CTRL).
    * Normalisation:      diacritics stripped (DIAC set from
                          src.features) + non-alphabetic chars dropped.
    * Sequence:           for each verse, for each WORD, emit the
                          letters left-to-right, separated by a word
                          boundary symbol '#' so cross-word pairs do
                          NOT contribute to the bigram (intra-word
                          only -- matches the feedback's "bigram
                          sufficiency within words" wording).
    * Per-corpus aggregate: concatenate all Band-A verses' char
                          streams, compute H1, H2, H3 via the same
                          _entropy helper as T11
                          (H_n = H(x_1..x_n) - H(x_1..x_{n-1})).
    * Per-unit:           same, but per-surah/per-chapter unit, to get
                          a distribution for Cohen d + MW p + bootstrap.
    * Cross-scripture:    an additional pooled row for Greek Iliad
                          (phase_06 ships 24 full books; no Band-A
                          filter because Iliad books are hundreds of
                          lines each).  If the law is scale-invariant
                          within Arabic AND Greek Iliad's ratio sits
                          above the Quran's, the cross-script story
                          holds.

Reads (integrity-checked):
    phase_06_phi_m.pkl   (state['CORPORA'])

Writes ONLY under results/experiments/exp27_hchar_bigram/:
    exp27_hchar_bigram.json
    self_check_<ts>.json
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy import stats

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

EXP = "exp27_hchar_bigram"

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]  # hadith_bukhari intentionally excluded (preregistration.json)
CROSS_SCRIPTURE = ["iliad_greek"]  # phase_06 has 24 full books
BAND_A_LO, BAND_A_HI = 15, 100  # matches src/extended_tests.py:37
SEED = 42
N_BOOT = 2000
WORD_SEP = "#"  # intra-word isolator; does NOT appear in natural text

# Diacritics to strip -- byte-for-byte copy of src/features.py:DIAC
# (Arabic harakat + tanween + shadda + sukun + hamza-above/below +
# other combining marks). Keeping this list inline, rather than
# importing, keeps exp27 runnable even if src/features.py moves.
DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)


# --------------------------------------------------------------------------- #
# Primitives                                                                  #
# --------------------------------------------------------------------------- #
def _strip_d(s: str) -> str:
    """Same policy as src/features.py:_strip_d."""
    return "".join(c for c in str(s) if c not in DIAC)


def _char_stream(verses: Iterable[str]) -> list[str]:
    """Per-unit char stream: for each word, emit its letters; insert
    '#' between words so bigrams do NOT cross word boundaries.

    Non-alphabetic characters (digits, punctuation, whitespace,
    leftover combining marks after _strip_d) are skipped.
    """
    out: list[str] = []
    first = True
    for v in verses:
        for w in _strip_d(v).split():
            letters = [c for c in w if c.isalpha()]
            if not letters:
                continue
            if not first:
                out.append(WORD_SEP)
            out.extend(letters)
            first = False
    return out


def _entropy(seq) -> float:
    """Shannon entropy in bits, byte-exact parity with
    src/extended_tests.py::_entropy."""
    c = Counter(seq)
    total = sum(c.values())
    if total == 0:
        return 0.0
    return -sum((n / total) * math.log2(n / total) for n in c.values())


def _hn(stream: list[str], n: int) -> float:
    """Conditional entropy H(x_n | x_1..x_{n-1}) via H(n-gram) - H((n-1)-gram).
    Parity with src/extended_tests.py:test_bigram_sufficiency::hn_seq.

    We DROP any n-gram that contains WORD_SEP -- that guarantees
    intra-word-only bigrams/trigrams (crossing a word boundary would
    otherwise leak a cross-word dependency into the estimate).
    """
    if len(stream) < n:
        return 0.0
    ngrams = [
        tuple(stream[i:i + n])
        for i in range(len(stream) - n + 1)
        if WORD_SEP not in stream[i:i + n]
    ]
    if not ngrams:
        return 0.0
    hn = _entropy(ngrams)
    if n == 1:
        return hn
    prev = [
        tuple(stream[i:i + n - 1])
        for i in range(len(stream) - n + 2)
        if WORD_SEP not in stream[i:i + n - 1]
    ]
    if not prev:
        return 0.0
    return hn - _entropy(prev)


def _cohens_d(a: list[float], b: list[float]) -> float:
    a = np.asarray([x for x in a if not math.isnan(x)], dtype=float)
    b = np.asarray([x for x in b if not math.isnan(x)], dtype=float)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    pv = (
        (len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)
    ) / (len(a) + len(b) - 2)
    if pv <= 0:
        return float("nan")
    return float((a.mean() - b.mean()) / math.sqrt(pv))


def _bootstrap_ci(
    values: list[float], n_boot: int, seed: int,
    stat=np.mean, alpha: float = 0.05,
) -> tuple[float, float]:
    """Percentile bootstrap CI."""
    clean = [v for v in values if math.isfinite(v)]
    if len(clean) < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    arr = np.asarray(clean, dtype=float)
    boots = np.empty(n_boot, dtype=float)
    idx_upper = len(arr)
    for b in range(n_boot):
        idx = [rng.randrange(idx_upper) for _ in range(idx_upper)]
        boots[b] = float(stat(arr[idx]))
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)


# --------------------------------------------------------------------------- #
# Per-unit computation                                                        #
# --------------------------------------------------------------------------- #
def _unit_ratios(verses) -> dict:
    """Compute H1, H2, H3, H2/H1, H3/H2 on one unit's intra-word char
    stream.  NaN returned if stream is too short."""
    stream = _char_stream(verses)
    if len(stream) < 50:  # minimum so trigrams are meaningful
        return {
            "H1": float("nan"), "H2": float("nan"), "H3": float("nan"),
            "H2_over_H1": float("nan"), "H3_over_H2": float("nan"),
            "n_chars": len(stream),
        }
    h1 = _hn(stream, 1)
    h2 = _hn(stream, 2)
    h3 = _hn(stream, 3)
    return {
        "H1": h1, "H2": h2, "H3": h3,
        "H2_over_H1": (h2 / h1) if h1 > 0 else float("nan"),
        "H3_over_H2": (h3 / h2) if h2 > 0 else float("nan"),
        "n_chars": len(stream),
    }


def _pooled_ratios(all_verses) -> dict:
    """Pool every verse across every Band-A unit of a corpus, then
    compute H1/H2/H3/ratios once. Mirrors T11's pooled-corpus design."""
    stream: list[str] = []
    for verses in all_verses:
        chunk = _char_stream(verses)
        if chunk:
            if stream:
                stream.append(WORD_SEP)
            stream.extend(chunk)
    if len(stream) < 50:
        return {
            "H1": float("nan"), "H2": float("nan"), "H3": float("nan"),
            "H2_over_H1": float("nan"), "H3_over_H2": float("nan"),
            "n_chars": len(stream),
        }
    h1 = _hn(stream, 1)
    h2 = _hn(stream, 2)
    h3 = _hn(stream, 3)
    return {
        "H1": h1, "H2": h2, "H3": h3,
        "H2_over_H1": (h2 / h1) if h1 > 0 else float("nan"),
        "H3_over_H2": (h3 / h2) if h2 > 0 else float("nan"),
        "n_chars": len(stream),
    }


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #
def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    per_corpus_pooled: dict = {}
    per_corpus_unit: dict = {}
    ARABIC_FAMILY = ["quran"] + ARABIC_CTRL
    for name in ARABIC_FAMILY:
        units = _band_a(CORPORA.get(name, []))
        if len(units) < 5:
            continue

        # Pooled (T11-parity)
        pooled = _pooled_ratios([u.verses for u in units])
        pooled["n_units"] = len(units)
        per_corpus_pooled[name] = pooled

        # Per-unit distribution (for Cohen d + MW + bootstrap)
        per_unit = [_unit_ratios(u.verses) for u in units]
        per_corpus_unit[name] = {
            "n_units": len(units),
            "H1": [r["H1"] for r in per_unit],
            "H2": [r["H2"] for r in per_unit],
            "H3": [r["H3"] for r in per_unit],
            "H2_over_H1": [r["H2_over_H1"] for r in per_unit],
            "H3_over_H2": [r["H3_over_H2"] for r in per_unit],
            "n_chars": [r["n_chars"] for r in per_unit],
        }

    # Cross-scripture panel (no Band-A filter; Iliad books are long)
    cross = {}
    for name in CROSS_SCRIPTURE:
        units = CORPORA.get(name, [])
        if not units:
            continue
        pooled = _pooled_ratios([u.verses for u in units])
        pooled["n_units"] = len(units)
        per_unit = [_unit_ratios(u.verses) for u in units]
        cross[name] = {
            "pooled": pooled,
            "per_unit_H3_over_H2_median": float(
                np.nanmedian([r["H3_over_H2"] for r in per_unit])
            ),
            "per_unit_H2_over_H1_median": float(
                np.nanmedian([r["H2_over_H1"] for r in per_unit])
            ),
            "n_units": len(units),
        }

    # --------- Quran vs pooled Arabic ctrl: Cohen d + MW ---------------- #
    def _pool_ctrl(ratio_key: str) -> list[float]:
        vals: list[float] = []
        for name in ARABIC_CTRL:
            vals.extend(per_corpus_unit.get(name, {}).get(ratio_key, []))
        return [v for v in vals if math.isfinite(v)]

    q_H32 = [
        v for v in per_corpus_unit.get("quran", {}).get("H3_over_H2", [])
        if math.isfinite(v)
    ]
    c_H32 = _pool_ctrl("H3_over_H2")
    q_H21 = [
        v for v in per_corpus_unit.get("quran", {}).get("H2_over_H1", [])
        if math.isfinite(v)
    ]
    c_H21 = _pool_ctrl("H2_over_H1")

    def _mw_less(a, b) -> float:
        if len(a) < 2 or len(b) < 2:
            return float("nan")
        try:
            res = stats.mannwhitneyu(a, b, alternative="less")
            return float(res.pvalue)
        except ValueError:
            return float("nan")

    summary = {
        "H3_over_H2_quran_mean": float(np.mean(q_H32)) if q_H32 else float("nan"),
        "H3_over_H2_ctrl_mean": float(np.mean(c_H32)) if c_H32 else float("nan"),
        "H3_over_H2_cohen_d": _cohens_d(q_H32, c_H32),
        "H3_over_H2_mwu_p_less": _mw_less(q_H32, c_H32),
        "H3_over_H2_quran_CI95": _bootstrap_ci(q_H32, N_BOOT, SEED),
        "H3_over_H2_ctrl_CI95": _bootstrap_ci(c_H32, N_BOOT, SEED + 1),
        "H2_over_H1_quran_mean": float(np.mean(q_H21)) if q_H21 else float("nan"),
        "H2_over_H1_ctrl_mean": float(np.mean(c_H21)) if c_H21 else float("nan"),
        "H2_over_H1_cohen_d": _cohens_d(q_H21, c_H21),
        "H2_over_H1_mwu_p_less": _mw_less(q_H21, c_H21),
        "H2_over_H1_quran_CI95": _bootstrap_ci(q_H21, N_BOOT, SEED + 2),
        "H2_over_H1_ctrl_CI95": _bootstrap_ci(c_H21, N_BOOT, SEED + 3),
        "n_quran_units": len(q_H32),
        "n_ctrl_units": len(c_H32),
    }

    # ----------- Ranking by pooled H3/H2 (low = more Markov-2) ---------- #
    pooled_ranking = sorted(
        [
            (k, v["H3_over_H2"])
            for k, v in per_corpus_pooled.items()
            if math.isfinite(v["H3_over_H2"])
        ],
        key=lambda x: x[1],
    )
    quran_rank_low = next(
        (i + 1 for i, (k, _) in enumerate(pooled_ranking) if k == "quran"),
        None,
    )

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "seed": SEED,
        "bands": {"lo": BAND_A_LO, "hi": BAND_A_HI},
        "word_sep": WORD_SEP,
        "n_boot": N_BOOT,
        "arabic_family_order": ARABIC_FAMILY,
        "per_corpus_pooled": per_corpus_pooled,
        "per_corpus_unit": per_corpus_unit,
        "cross_scripture_pooled": cross,
        "quran_vs_arabic_ctrl_summary": summary,
        "pooled_H3_over_H2_ranking_low_is_more_markov2": [
            {"corpus": k, "ratio": r} for k, r in pooled_ranking
        ],
        "quran_rank_pooled_H3_over_H2": quran_rank_low,
        "notes": (
            "Character-level analog of T11 (root H3/H2). Positive result "
            "(d < 0 i.e. Quran H3/H2 < ctrl; MW p_less < 0.01; Quran "
            "rank == 1) confirms bigram sufficiency at the CHARACTER "
            "scale.  Combined with the locked T11 (roots), F6 (verse "
            "lengths), T8 (path) and T28 (H2/H1 root-order), this is "
            "the SCALE-INVARIANT MARKOV-1 LAW candidate.  Next step: "
            "exp28 assembles all 4 scales into a single summary table."
        ),
        "provenance": {
            "input_checkpoint": "phase_06_phi_m.pkl",
            "arabic_ctrl": ARABIC_CTRL,
            "hadith_quarantined": True,
            "mirror_of": "src/extended_tests.py::test_bigram_sufficiency (T11)",
        },
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # -------------------- console ---------------------------------------- #
    print(f"[{EXP}] wrote {outfile}")
    print(f"[{EXP}] Band-A [{BAND_A_LO},{BAND_A_HI}]  seed={SEED}  "
          f"n_boot={N_BOOT}")
    print(f"[{EXP}] POOLED H3/H2 ranking (low = more Markov-2-sufficient):")
    for rank, (k, r) in enumerate(pooled_ranking, start=1):
        tag = "  <-- QURAN" if k == "quran" else ""
        print(f"   {rank:2d}. {k:20s}  H3/H2 = {r:.4f}{tag}")
    s = summary
    print(f"[{EXP}] PER-UNIT H3/H2: Quran mean={s['H3_over_H2_quran_mean']:.4f} "
          f"(CI95={s['H3_over_H2_quran_CI95']})")
    print(f"[{EXP}]                ctrl  mean={s['H3_over_H2_ctrl_mean']:.4f} "
          f"(CI95={s['H3_over_H2_ctrl_CI95']})")
    print(f"[{EXP}]                Cohen d(Q-ctrl) = {s['H3_over_H2_cohen_d']:+.3f}"
          f"   MW p_less = {s['H3_over_H2_mwu_p_less']:.3e}")
    print(f"[{EXP}] PER-UNIT H2/H1: Quran mean={s['H2_over_H1_quran_mean']:.4f}  "
          f"ctrl={s['H2_over_H1_ctrl_mean']:.4f}  "
          f"d = {s['H2_over_H1_cohen_d']:+.3f}  "
          f"MW p_less = {s['H2_over_H1_mwu_p_less']:.3e}")
    if cross:
        print(f"[{EXP}] Cross-scripture pooled H3/H2:")
        for k, v in cross.items():
            print(f"   {k:20s}  pooled H3/H2 = {v['pooled']['H3_over_H2']:.4f}  "
                  f"(n_units={v['n_units']})")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
