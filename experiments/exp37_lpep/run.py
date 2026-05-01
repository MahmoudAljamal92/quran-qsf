"""
exp37_lpep/run.py
=================
Letter-Position Entropy Profile (LPEP).

Hypothesis (from 2026-04-20 deep-scan synthesis):
    The triliteral root system of Arabic predicts that, given a consonant
    letter L in a word of consonant-length k, the POSITION j of L within
    that word has LOW entropy: roots like f-ʿ-l anchor letters to
    positions 1/2/3 far more tightly than a random-placement null.

    Concretely, define

        LPEP_{L,k,j} = P(pos = j | letter = L, word_length = k)

    and the per-corpus summary

        <H(pos | L, k)> = sum_{L,k} P(L, k) * H(pos | L, k)

    where H(pos | L, k) = - sum_j P(j|L,k) log2 P(j|L,k).

    Lower <H(pos|L,k)>  ==>  tighter positional slots  ==>  stronger
    root-like structure.

Predictions
    1. 7 Arabic corpora all low (Semitic root system universal within Arabic).
    2. Among those 7, Quran ranks either 1st or tied-low (the root hypothesis
       alone does NOT predict Quran-extremality; this is the honest null).
    3. Cross-scripture: Iliad-Greek <H(pos|L,k)> is substantially HIGHER
       than any Arabic corpus (Greek is non-Semitic, no triliteral roots).
    4. Per-unit Cohen d(Q vs pooled Arabic-ctrl) distinguishes whether
       the Quran is extremal WITHIN Arabic or merely typical-Arabic.
       A d <= -0.3 (one-sided MW p_less <= 0.05) in favour of the Quran
       (Quran tighter) would be a genuinely new finding.

Protocol
    Band-A gate: [15, 100] verses per unit (for the per-unit comparison;
    pooled stats use the full corpus).
    Arabic-ctrl: poetry_{jahili,islami,abbasi}, ksucca, arabic_bible,
    hindawi (hadith quarantined per preregistration.json).
    Cross-scripture: iliad_greek (phase_06 ships 24 books; treated as
    pooled-only since book sizes differ drastically from Arabic units).

    Normalisation: drop diacritics + tatweel + non-letters; fold hamza
    variants to ا, ة to ه, ى to ي.  Resulting alphabet is the 28-letter
    canonical Arabic consonant set (matches _ultimate2_helpers.py).

    Word-length bins: k in {3, 4, 5, 6, 7+} (pooled for k>=7 to avoid
    sparsity).  Words with fewer than 3 post-normalisation letters are
    dropped (too short to have positional structure).

    Cell minimum: (L, k) cells with < 5 occurrences contribute NaN and
    are excluded from the weighted aggregate.

Reads (integrity-checked):
    phase_06_phi_m.pkl   (state['CORPORA'])

Writes ONLY under results/experiments/exp37_lpep/:
    exp37_lpep.json
    self_check_<ts>.json
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter, defaultdict
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

EXP = "exp37_lpep"

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]  # hadith_bukhari excluded (preregistration.json policy)
CROSS_SCRIPTURE = ["iliad_greek"]  # phase_06 has 24 books
BAND_A_LO, BAND_A_HI = 15, 100  # matches src/extended_tests.py
SEED = 42
N_BOOT = 2000

# Byte-for-byte copy of the diacritic list used by exp27/features.
DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)
TATWEEL = "\u0640"

# Canonical 28-letter Arabic consonant alphabet + folding rules.
# Matches experiments/_ultimate2_helpers.py:46.
ARABIC_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_FOLD = {
    "ء": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "ا", "ئ": "ا",
    "ة": "ه",
    "ى": "ي",
}

# Word-length bins -- k>=7 pooled as "7+"
K_BINS = (3, 4, 5, 6, 7)  # last is "7+"
MAX_K_KEY = 7  # any length >= MAX_K_KEY is keyed as MAX_K_KEY
MIN_CELL_COUNT = 5  # per-(L,k) cell minimum for H to be counted


# --------------------------------------------------------------------------- #
# Primitives                                                                  #
# --------------------------------------------------------------------------- #
def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC and c != TATWEEL)


def _normalise_arabic_letters(word: str) -> str:
    """Drop diacritics; fold hamza/ta-marbuta/alif-maqsura; keep only
    the 28-letter canonical consonant set.  Any foreign letter is
    passed through so non-Arabic streams (Greek) still work for the
    cross-scripture branch -- but those letters will not enter the
    Arabic 28-alphabet indexer, and the Greek branch uses its own
    alphabet-derivation below."""
    w = _strip_d(word)
    out_chars: list[str] = []
    for c in w:
        if c in _FOLD:
            out_chars.append(_FOLD[c])
        elif c in ARABIC_28:
            out_chars.append(c)
        # silently drop anything else (tanween, punctuation, digits)
    return "".join(out_chars)


def _extract_words_arabic(verses: Iterable[str]) -> list[str]:
    """Yield normalised Arabic words (letters only, 28-alphabet)
    of length >= 3. Words of length < 3 dropped."""
    out: list[str] = []
    for v in verses:
        for w in str(v).split():
            nw = _normalise_arabic_letters(w)
            if len(nw) >= 3:
                out.append(nw)
    return out


# Greek is tested only as a negative control. For Greek we strip
# diacritics, lowercase, and keep the 24-letter core alphabet.
_GREEK_DIAC = set(
    "\u0300\u0301\u0302\u0303\u0304\u0305\u0306\u0307\u0308\u0309\u030a"
    "\u030b\u030c\u030d\u030e\u030f\u0313\u0314\u0342\u0344\u0345"
)
_GREEK_FOLD = {
    # final-sigma -> sigma; tonos/dialytika collapsed via NFD+strip below
    "ς": "σ",
}


def _normalise_greek_letters(word: str) -> str:
    import unicodedata
    nfd = unicodedata.normalize("NFD", word)
    nfd = "".join(c for c in nfd if c not in _GREEK_DIAC)
    out_chars: list[str] = []
    for c in nfd.lower():
        if c in _GREEK_FOLD:
            out_chars.append(_GREEK_FOLD[c])
        elif "\u03b1" <= c <= "\u03c9":  # α..ω
            out_chars.append(c)
    return "".join(out_chars)


def _extract_words_greek(verses: Iterable[str]) -> list[str]:
    out: list[str] = []
    for v in verses:
        for w in str(v).split():
            nw = _normalise_greek_letters(w)
            if len(nw) >= 3:
                out.append(nw)
    return out


# --------------------------------------------------------------------------- #
# LPEP computation                                                            #
# --------------------------------------------------------------------------- #
def _bin_k(k: int) -> int:
    """Bucket word-length: 3, 4, 5, 6, or 7+ (returned as MAX_K_KEY=7)."""
    if k >= MAX_K_KEY:
        return MAX_K_KEY
    return k


def _lpep_counts(words: list[str]) -> dict:
    """Return the joint count tensor C[(L, k_bin, j)] and the marginal
    count C_Lk[(L, k_bin)] used to form P(j | L, k) later.

    j is 1-indexed position within the word (1..len(word)).
    For words of length >= MAX_K_KEY, positions beyond MAX_K_KEY are
    bucketed into j=MAX_K_KEY as well (tail pooling).  This avoids
    exploding the tensor while preserving the positional contrast
    between position 1 (word-initial), 2, 3, ..., MAX_K_KEY (tail).
    """
    joint: Counter = Counter()
    marg: Counter = Counter()
    n_words_total = 0
    n_letters_total = 0
    for w in words:
        k = len(w)
        if k < 3:
            continue
        n_words_total += 1
        kb = _bin_k(k)
        for raw_j, L in enumerate(w, start=1):
            j = raw_j if raw_j < MAX_K_KEY else MAX_K_KEY
            joint[(L, kb, j)] += 1
            marg[(L, kb)] += 1
            n_letters_total += 1
    return {
        "joint": joint, "marg": marg,
        "n_words": n_words_total, "n_letters": n_letters_total,
    }


def _mean_H_pos_from_counts(counts: dict) -> dict:
    """Compute <H(pos|L,k)> = sum_{L,k} P(L,k) H(pos|L,k) from a
    joint/marg count tensor.  Also return per-k breakdown."""
    joint: Counter = counts["joint"]
    marg: Counter = counts["marg"]

    # Filter to cells with enough data.
    kept_cells = {lk: n for lk, n in marg.items() if n >= MIN_CELL_COUNT}
    total_kept = sum(kept_cells.values())
    if total_kept == 0:
        return {
            "mean_H_pos": float("nan"),
            "per_k": {str(k): float("nan") for k in K_BINS},
            "n_cells_kept": 0, "n_cells_dropped": len(marg),
            "n_words": counts["n_words"], "n_letters": counts["n_letters"],
        }

    H_cells: dict = {}
    for (L, kb), n_Lk in kept_cells.items():
        # Aggregate position distribution for this (L, k_bin).
        pj: dict = defaultdict(int)
        for j in range(1, MAX_K_KEY + 1):
            pj[j] = joint.get((L, kb, j), 0)
        tot = sum(pj.values())
        if tot <= 0:
            continue
        H = 0.0
        for c in pj.values():
            if c > 0:
                p = c / tot
                H -= p * math.log2(p)
        H_cells[(L, kb)] = H

    # Weighted aggregate across cells.
    mean_H = sum(
        (kept_cells[lk] / total_kept) * H_cells.get(lk, 0.0)
        for lk in kept_cells
    )

    # Per-k breakdown.
    per_k: dict = {}
    for kb in K_BINS:
        cells_k = {L: n for (L, kbb), n in kept_cells.items() if kbb == kb}
        tot_k = sum(cells_k.values())
        if tot_k == 0:
            per_k[str(kb)] = float("nan")
            continue
        mH_k = sum(
            (cells_k[L] / tot_k) * H_cells.get((L, kb), 0.0)
            for L in cells_k
        )
        per_k[str(kb)] = float(mH_k)

    return {
        "mean_H_pos": float(mean_H),
        "per_k": per_k,
        "n_cells_kept": len(kept_cells),
        "n_cells_dropped": len(marg) - len(kept_cells),
        "n_words": counts["n_words"],
        "n_letters": counts["n_letters"],
    }


def _lpep_for_corpus(
    all_verses: list[list[str]], alphabet: str = "ar",
) -> dict:
    """Pool every verse across every unit; compute LPEP summary.
    alphabet in {'ar', 'el'} selects the word-extractor."""
    if alphabet == "ar":
        words = []
        for verses in all_verses:
            words.extend(_extract_words_arabic(verses))
    elif alphabet == "el":
        words = []
        for verses in all_verses:
            words.extend(_extract_words_greek(verses))
    else:
        raise ValueError(f"Unknown alphabet {alphabet!r}")
    counts = _lpep_counts(words)
    return _mean_H_pos_from_counts(counts)


def _lpep_for_unit(verses: list[str], alphabet: str = "ar") -> dict:
    """Per-unit LPEP (for the Cohen-d distribution)."""
    if alphabet == "ar":
        words = _extract_words_arabic(verses)
    elif alphabet == "el":
        words = _extract_words_greek(verses)
    else:
        raise ValueError(f"Unknown alphabet {alphabet!r}")
    counts = _lpep_counts(words)
    return _mean_H_pos_from_counts(counts)


# --------------------------------------------------------------------------- #
# Stats helpers                                                                #
# --------------------------------------------------------------------------- #
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
    clean = [v for v in values if math.isfinite(v)]
    if len(clean) < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    arr = np.asarray(clean, dtype=float)
    boots = np.empty(n_boot, dtype=float)
    n = len(arr)
    for b in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        boots[b] = float(stat(arr[idx]))
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)


def _mw_less(a, b) -> float:
    """MW one-sided: H_alt = 'a stochastically less than b'."""
    a = [x for x in a if math.isfinite(x)]
    b = [x for x in b if math.isfinite(x)]
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    try:
        res = stats.mannwhitneyu(a, b, alternative="less")
        return float(res.pvalue)
    except ValueError:
        return float("nan")


# --------------------------------------------------------------------------- #
# Main                                                                         #
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

        pooled = _lpep_for_corpus([u.verses for u in units], alphabet="ar")
        pooled["n_units"] = len(units)
        per_corpus_pooled[name] = pooled

        per_unit = [_lpep_for_unit(u.verses, alphabet="ar") for u in units]
        per_corpus_unit[name] = {
            "n_units": len(units),
            "mean_H_pos": [r["mean_H_pos"] for r in per_unit],
            "per_k_3": [r["per_k"].get("3", float("nan")) for r in per_unit],
            "per_k_4": [r["per_k"].get("4", float("nan")) for r in per_unit],
            "per_k_5": [r["per_k"].get("5", float("nan")) for r in per_unit],
            "per_k_6": [r["per_k"].get("6", float("nan")) for r in per_unit],
            "per_k_7plus": [
                r["per_k"].get("7", float("nan")) for r in per_unit
            ],
            "n_words": [r["n_words"] for r in per_unit],
        }

    # Cross-scripture: Iliad Greek (pooled only; 24 books is too few
    # for a meaningful per-unit Cohen d and book-sizes are non-comparable).
    cross: dict = {}
    for name in CROSS_SCRIPTURE:
        units = CORPORA.get(name, [])
        if not units:
            continue
        pooled = _lpep_for_corpus([u.verses for u in units], alphabet="el")
        pooled["n_units"] = len(units)
        cross[name] = pooled

    # -------- Quran vs pooled Arabic ctrl: d + MW + bootstrap ----------- #
    def _pool_ctrl(key: str) -> list[float]:
        vals: list[float] = []
        for name in ARABIC_CTRL:
            vals.extend(per_corpus_unit.get(name, {}).get(key, []))
        return [v for v in vals if math.isfinite(v)]

    q_mean = [
        v for v in per_corpus_unit.get("quran", {}).get("mean_H_pos", [])
        if math.isfinite(v)
    ]
    c_mean = _pool_ctrl("mean_H_pos")
    q_k3 = [
        v for v in per_corpus_unit.get("quran", {}).get("per_k_3", [])
        if math.isfinite(v)
    ]
    c_k3 = _pool_ctrl("per_k_3")

    summary = {
        "mean_H_pos_quran_mean": (
            float(np.mean(q_mean)) if q_mean else float("nan")
        ),
        "mean_H_pos_ctrl_mean": (
            float(np.mean(c_mean)) if c_mean else float("nan")
        ),
        "mean_H_pos_cohen_d": _cohens_d(q_mean, c_mean),
        "mean_H_pos_mwu_p_less": _mw_less(q_mean, c_mean),
        "mean_H_pos_quran_CI95": _bootstrap_ci(q_mean, N_BOOT, SEED),
        "mean_H_pos_ctrl_CI95": _bootstrap_ci(c_mean, N_BOOT, SEED + 1),
        "k3_H_pos_quran_mean": float(np.mean(q_k3)) if q_k3 else float("nan"),
        "k3_H_pos_ctrl_mean": float(np.mean(c_k3)) if c_k3 else float("nan"),
        "k3_H_pos_cohen_d": _cohens_d(q_k3, c_k3),
        "k3_H_pos_mwu_p_less": _mw_less(q_k3, c_k3),
        "n_quran_units": len(q_mean),
        "n_ctrl_units": len(c_mean),
    }

    # --------- Pooled ranking (low = tighter positional structure) ------ #
    pooled_ranking = sorted(
        [
            (k, v["mean_H_pos"])
            for k, v in per_corpus_pooled.items()
            if math.isfinite(v["mean_H_pos"])
        ],
        key=lambda x: x[1],
    )
    quran_rank = next(
        (i + 1 for i, (k, _) in enumerate(pooled_ranking) if k == "quran"),
        None,
    )

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "seed": SEED,
        "bands": {"lo": BAND_A_LO, "hi": BAND_A_HI},
        "k_bins": list(K_BINS),
        "max_k_key": MAX_K_KEY,
        "min_cell_count": MIN_CELL_COUNT,
        "n_boot": N_BOOT,
        "arabic_family_order": ARABIC_FAMILY,
        "per_corpus_pooled": per_corpus_pooled,
        "per_corpus_unit": per_corpus_unit,
        "cross_scripture_pooled": cross,
        "quran_vs_arabic_ctrl_summary": summary,
        "pooled_ranking_low_is_tighter": [
            {"corpus": k, "mean_H_pos": r} for k, r in pooled_ranking
        ],
        "quran_rank_pooled": quran_rank,
        "hypothesis_test_verdict": {
            "H_pos_semitic_tight": _semitic_tightness_verdict(
                per_corpus_pooled, cross,
            ),
            "H_pos_quran_extremal_within_arabic":
                _quran_extremal_verdict(summary, quran_rank, len(ARABIC_FAMILY)),
        },
        "notes": (
            "LPEP (Letter-Position Entropy Profile): <H(pos|L,k)> measures "
            "how tightly Arabic consonants cluster into fixed positions "
            "within words of a given length. Lower = tighter positional "
            "slots = more root-like structure. The Semitic triliteral "
            "root system predicts LOW values for Arabic and Hebrew and "
            "HIGH values for non-Semitic scripts. Quran-extremality "
            "WITHIN Arabic is the novel claim tested here."
        ),
        "provenance": {
            "input_checkpoint": "phase_06_phi_m.pkl",
            "arabic_ctrl": ARABIC_CTRL,
            "hadith_quarantined": True,
            "design_doc": "2026-04-20 deep-scan synthesis",
        },
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # -------------------- console --------------------------------------- #
    print(f"[{EXP}] wrote {outfile}")
    print(f"[{EXP}] Band-A [{BAND_A_LO},{BAND_A_HI}]  seed={SEED}")
    print(f"[{EXP}] POOLED <H(pos|L,k)> ranking (low = tighter):")
    for rank, (k, r) in enumerate(pooled_ranking, start=1):
        tag = "  <-- QURAN" if k == "quran" else ""
        n_words = per_corpus_pooled[k]["n_words"]
        print(f"   {rank:2d}. {k:20s}  <H> = {r:.4f}  "
              f"(n_words={n_words}){tag}")
    if cross:
        print(f"[{EXP}] Cross-scripture pooled:")
        for k, v in cross.items():
            print(f"   {k:20s}  <H> = {v['mean_H_pos']:.4f}  "
                  f"(n_words={v['n_words']})")
    s = summary
    print(f"[{EXP}] PER-UNIT <H(pos|L,k)>:")
    print(f"   Quran  mean = {s['mean_H_pos_quran_mean']:.4f}  "
          f"CI95 = {s['mean_H_pos_quran_CI95']}")
    print(f"   Ctrl   mean = {s['mean_H_pos_ctrl_mean']:.4f}  "
          f"CI95 = {s['mean_H_pos_ctrl_CI95']}")
    print(f"   Cohen d(Q-ctrl) = {s['mean_H_pos_cohen_d']:+.3f}  "
          f"MW p_less = {s['mean_H_pos_mwu_p_less']:.3e}")
    print(f"[{EXP}] k=3 only (triliteral-root cleanest slice):")
    print(f"   Quran  mean = {s['k3_H_pos_quran_mean']:.4f}  "
          f"Ctrl mean = {s['k3_H_pos_ctrl_mean']:.4f}")
    print(f"   Cohen d(Q-ctrl) = {s['k3_H_pos_cohen_d']:+.3f}  "
          f"MW p_less = {s['k3_H_pos_mwu_p_less']:.3e}")

    self_check_end(pre, EXP)
    return 0


# --------------------------------------------------------------------------- #
# Verdict helpers                                                              #
# --------------------------------------------------------------------------- #
def _semitic_tightness_verdict(per_corpus_pooled, cross) -> str:
    """Greek Iliad should be higher than every Arabic corpus if the
    Semitic-root hypothesis is right."""
    ar_values = [
        v["mean_H_pos"] for v in per_corpus_pooled.values()
        if math.isfinite(v["mean_H_pos"])
    ]
    greek_val = cross.get("iliad_greek", {}).get("mean_H_pos", float("nan"))
    if not ar_values or not math.isfinite(greek_val):
        return "INCONCLUSIVE (missing corpora)"
    max_ar = max(ar_values)
    if greek_val > max_ar:
        return "SUPPORTS"
    if greek_val < max_ar:
        return "FALSIFIES"
    return "TIES"


def _quran_extremal_verdict(summary, quran_rank, n_arabic) -> str:
    """Quran-extremal-within-Arabic requires (a) rank 1 on pooled,
    (b) Cohen d < -0.3 AND MW p_less < 0.05 on per-unit."""
    d = summary.get("mean_H_pos_cohen_d", float("nan"))
    p = summary.get("mean_H_pos_mwu_p_less", float("nan"))
    if not math.isfinite(d) or not math.isfinite(p):
        return "INCONCLUSIVE (NaN stats)"
    strong_d = d <= -0.3
    significant = p <= 0.05
    rank_one = quran_rank == 1
    if rank_one and strong_d and significant:
        return "SUPPORTS (rank 1 pooled + d<=-0.3 + p_less<=0.05)"
    if rank_one and (strong_d or significant):
        return "PARTIAL (rank 1 pooled but only one per-unit criterion met)"
    if rank_one:
        return "WEAK (rank 1 pooled but per-unit not significant)"
    return (
        f"FAILS (rank {quran_rank}/{n_arabic} pooled, "
        f"d={d:+.3f}, p_less={p:.3e})"
    )


if __name__ == "__main__":
    sys.exit(main())
