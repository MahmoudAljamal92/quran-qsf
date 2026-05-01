"""
exp38_ccas_normalised/run.py
============================
Consonant Co-occurrence Anomaly Score, normalised by intra-document
bigram-matrix variance.

Motivation
    exp30 tested raw |Delta M|_F (channel C_bigram_dist in R1's 9ch bank)
    and found MW p(Q |Delta| > ctrl |Delta|) = 0.58 -- the channel fires
    on any edit but does NOT fire more in the Quran. The raw Frobenius
    magnitude is dominated by edit location (which letters are touched),
    not by host-text structural tightness.

    The one variant NOT yet tested is the per-document-variance
    normalisation:

        CCAS_norm(doc, edit) = |M_edited - M_canonical|_F
                              / sigma_intra_doc(M)

    where sigma_intra_doc is the std of |M_window - mean(M_window)|_F
    across K=10 random same-size sliding-window submatrices of the
    unperturbed document. This factors out document-size and letter-
    inventory effects and isolates "how much a fixed-size edit
    perturbs the intrinsic bigram structure" -- which is the only
    quantity under which the root-system hypothesis actually predicts
    Quran-specificity.

    If this ALSO fails the MW test, the entire letter-transition-matrix
    detector family is closed and we know the detection signal (if any)
    must live in a non-matrix statistic (gzip NCD, LPEP, or perplexity).

Protocol
    Target Band-A Quran surahs: n=68 (same as exp29).
    Matched-length ctrl units: 200 Band-A Arabic-ctrl units (same as
        exp29, hadith quarantined).
    Perturbations: N_PERT = 20 per unit, INTERNAL single-letter swap
        (non-initial + non-terminal letter in a non-boundary word of a
        non-terminal verse) matching exp29::_apply_perturbation.
    Matrix: 28x28 STRICT-consonant transition count matrix.
        Alphabet ARABIC_CONS_28 from _ultimate2_helpers.
        Hamza variants folded to alef (matches strict-rasm policy).
    Sigma: K=10 random equal-length windows (same total letter count
        as the document), std of |M_window - M_mean|_F.

    Statistic per (unit, perturbation):
        raw_ccas   = |M_edited - M_canonical|_F
        norm_ccas  = raw_ccas / sigma_intra_doc  (NaN if sigma == 0)

    Tests:
        MW_less(raw Q, raw ctrl)      -- sanity replication of exp30
        MW_greater(raw Q, raw ctrl)   -- Quran-specificity direction
        MW_greater(norm Q, norm ctrl) -- the novel test
        Cohen d (Q - ctrl) on each

    Threshold: MW p_greater <= 0.05 AND Cohen d >= +0.3 to claim
    Quran-specificity at this variant.

Reads (integrity-checked):
    phase_06_phi_m.pkl   state['CORPORA']

Writes ONLY under results/experiments/exp38_ccas_normalised/:
    exp38_ccas_normalised.json
    self_check_<ts>.json
"""
from __future__ import annotations

import json
import math
import random
import sys
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

EXP = "exp38_ccas_normalised"

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]  # hadith quarantined
BAND_A_LO, BAND_A_HI = 15, 100
SEED = 42
N_PERT = 20            # perturbations per unit
CTRL_N_UNITS = 200     # matched-length ctrl units
K_WINDOWS = 10         # sliding windows for sigma_intra_doc

ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ALPH_IDX = {c: i for i, c in enumerate(ARABIC_CONS_28)}
ALPH_N = len(ARABIC_CONS_28)

DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)
_FOLD = {
    "ء": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "ا", "ئ": "ا",
    "ة": "ه",
    "ى": "ي",
}


# --------------------------------------------------------------------------- #
# Primitives                                                                  #
# --------------------------------------------------------------------------- #
def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)


def _letters_28(text: str) -> str:
    """Extract the 28-letter canonical consonant stream.  Hamza
    variants folded to alef; ة -> ه; ى -> ي.  Word boundaries and
    whitespace are DROPPED (matrix is corpus-global, not intra-word)."""
    out: list[str] = []
    for c in _strip_d(text):
        if c in _FOLD:
            out.append(_FOLD[c])
        elif c in _ALPH_IDX:
            out.append(c)
    return "".join(out)


def _matrix(letters: str) -> np.ndarray:
    """28x28 letter-transition count matrix from a consonant string."""
    M = np.zeros((ALPH_N, ALPH_N), dtype=float)
    for a, b in zip(letters[:-1], letters[1:]):
        ia = _ALPH_IDX.get(a)
        ib = _ALPH_IDX.get(b)
        if ia is not None and ib is not None:
            M[ia, ib] += 1.0
    return M


def _frob(M: np.ndarray) -> float:
    return float(np.linalg.norm(M))


# --------------------------------------------------------------------------- #
# sigma_intra_doc via K equal-length sliding windows                          #
# --------------------------------------------------------------------------- #
def _sigma_intra_doc(
    letters: str, window_len: int, k: int, rng: random.Random,
) -> float:
    """Return std of |M_win - M_mean|_F across k random windows of
    window_len consecutive letters drawn from `letters`.

    If the document is shorter than 2*window_len we fall back to
    returning the raw std of window matrices (no subtraction of mean).
    Returns 0.0 if the document has fewer than window_len letters.
    """
    n = len(letters)
    if n < window_len or k < 2:
        return 0.0
    # Anchor positions such that each window fits.
    max_start = n - window_len
    if max_start < 1:
        return 0.0
    n_samples = min(k, max_start)
    starts = rng.sample(range(max_start), n_samples)
    mats = [_matrix(letters[s:s + window_len]) for s in starts]
    stack = np.stack(mats, axis=0)          # (k, 28, 28)
    M_mean = stack.mean(axis=0)
    diffs = [_frob(m - M_mean) for m in mats]
    if not diffs:
        return 0.0
    return float(np.std(diffs, ddof=1)) if len(diffs) > 1 else 0.0


# --------------------------------------------------------------------------- #
# Perturbation (byte-exact same policy as exp29::_apply_perturbation)          #
# --------------------------------------------------------------------------- #
_ARABIC_CONS_28_LIST = list(ARABIC_CONS_28)


def _apply_perturbation(
    verses: list[str], rng: random.Random,
) -> tuple[list[str], int] | None:
    nv = len(verses)
    if nv < 5:
        return None
    vi_choices = list(range(1, nv - 1))
    rng.shuffle(vi_choices)
    for vi in vi_choices:
        toks = _strip_d(verses[vi]).split()
        if len(toks) < 3:
            continue
        wi_choices = list(range(1, len(toks) - 1))
        rng.shuffle(wi_choices)
        for wi in wi_choices:
            w = toks[wi]
            alpha_positions = [i for i, c in enumerate(w) if c.isalpha()]
            if len(alpha_positions) < 3:
                continue
            interior = alpha_positions[1:-1]
            if not interior:
                continue
            pos = rng.choice(interior)
            original = w[pos]
            candidates = [c for c in _ARABIC_CONS_28_LIST if c != original]
            if not candidates:
                continue
            repl = rng.choice(candidates)
            new_word = w[:pos] + repl + w[pos + 1:]
            new_toks = list(toks)
            new_toks[wi] = new_word
            new_verses = list(verses)
            new_verses[vi] = " ".join(new_toks)
            return new_verses, vi
    return None


# --------------------------------------------------------------------------- #
# Per-unit CCAS computation                                                    #
# --------------------------------------------------------------------------- #
def _run_unit(
    verses: list[str], rng: random.Random,
    n_pert: int = N_PERT, k_win: int = K_WINDOWS,
) -> dict:
    """Return per-perturbation (raw_ccas, norm_ccas) lists plus the
    unit's sigma_intra_doc and canonical matrix Frobenius."""
    canon_text = " ".join(verses)
    canon_letters = _letters_28(canon_text)
    if len(canon_letters) < 50:
        return {"raw": [], "norm": [], "sigma": float("nan"),
                "canon_frob": float("nan"), "n_letters": len(canon_letters)}
    M_canon = _matrix(canon_letters)
    canon_frob = _frob(M_canon)

    # Choose a window length that is 1/4 of the doc (so we get multiple
    # non-overlapping windows in a sensible document). Cap at 2000 so
    # long control units don't produce single-window artefacts.
    win_len = max(50, min(2000, len(canon_letters) // 4))
    sigma = _sigma_intra_doc(canon_letters, win_len, k_win, rng)

    raw_list: list[float] = []
    norm_list: list[float] = []
    for _ in range(n_pert):
        out = _apply_perturbation(verses, rng)
        if out is None:
            continue
        new_verses, _vi = out
        new_letters = _letters_28(" ".join(new_verses))
        M_new = _matrix(new_letters)
        delta = _frob(M_new - M_canon)
        raw_list.append(delta)
        if sigma > 0 and math.isfinite(sigma):
            norm_list.append(delta / sigma)
        else:
            norm_list.append(float("nan"))

    return {
        "raw": raw_list, "norm": norm_list, "sigma": sigma,
        "canon_frob": canon_frob,
        "n_letters": len(canon_letters),
        "window_len": win_len,
    }


# --------------------------------------------------------------------------- #
# Stats helpers                                                                #
# --------------------------------------------------------------------------- #
def _finite(xs: Iterable[float]) -> list[float]:
    return [x for x in xs if math.isfinite(x)]


def _cohens_d(a: list[float], b: list[float]) -> float:
    a = np.asarray(_finite(a), dtype=float)
    b = np.asarray(_finite(b), dtype=float)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    pv = (
        (len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)
    ) / (len(a) + len(b) - 2)
    if pv <= 0:
        return float("nan")
    return float((a.mean() - b.mean()) / math.sqrt(pv))


def _mw(a, b, alternative: str) -> float:
    a = _finite(a); b = _finite(b)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    try:
        res = stats.mannwhitneyu(a, b, alternative=alternative)
        return float(res.pvalue)
    except ValueError:
        return float("nan")


def _summary_stats(q: list[float], c: list[float]) -> dict:
    q_f = _finite(q); c_f = _finite(c)
    return {
        "n_q": len(q_f), "n_ctrl": len(c_f),
        "q_mean": float(np.mean(q_f)) if q_f else float("nan"),
        "q_median": float(np.median(q_f)) if q_f else float("nan"),
        "ctrl_mean": float(np.mean(c_f)) if c_f else float("nan"),
        "ctrl_median": float(np.median(c_f)) if c_f else float("nan"),
        "cohen_d": _cohens_d(q, c),
        "mw_p_greater": _mw(q, c, "greater"),
        "mw_p_less": _mw(q, c, "less"),
    }


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

    # ------------------ Quran Band-A -------------------------------- #
    rng_q = random.Random(SEED)
    q_units = _band_a(CORPORA.get("quran", []))
    q_raw: list[float] = []
    q_norm: list[float] = []
    q_sigma_per_unit: list[float] = []
    q_canon_frob_per_unit: list[float] = []
    for u in q_units:
        rng_u = random.Random(rng_q.randrange(1 << 30))
        r = _run_unit(u.verses, rng_u)
        q_raw.extend(r["raw"])
        q_norm.extend(r["norm"])
        q_sigma_per_unit.append(r["sigma"])
        q_canon_frob_per_unit.append(r["canon_frob"])

    # ------------------ Arabic ctrl Band-A (200 matched) ------------ #
    rng_c = random.Random(SEED + 1)
    ctrl_pool = []
    for name in ARABIC_CTRL:
        ctrl_pool.extend(_band_a(CORPORA.get(name, [])))
    rng_c.shuffle(ctrl_pool)
    ctrl_units = ctrl_pool[:CTRL_N_UNITS]

    c_raw: list[float] = []
    c_norm: list[float] = []
    c_sigma_per_unit: list[float] = []
    c_canon_frob_per_unit: list[float] = []
    for u in ctrl_units:
        rng_u = random.Random(rng_c.randrange(1 << 30))
        r = _run_unit(u.verses, rng_u)
        c_raw.extend(r["raw"])
        c_norm.extend(r["norm"])
        c_sigma_per_unit.append(r["sigma"])
        c_canon_frob_per_unit.append(r["canon_frob"])

    raw_summary = _summary_stats(q_raw, c_raw)
    norm_summary = _summary_stats(q_norm, c_norm)

    # ------------------ Verdict ------------------------------------- #
    def _verdict(s: dict, label: str) -> str:
        d = s["cohen_d"]
        pg = s["mw_p_greater"]
        if not math.isfinite(d) or not math.isfinite(pg):
            return f"INCONCLUSIVE ({label})"
        if d >= 0.3 and pg <= 0.05:
            return f"SUPPORTS Quran-specificity ({label})"
        if d >= 0.1 and pg <= 0.10:
            return f"WEAK ({label})"
        return f"FAILS ({label}; d={d:+.3f}, p_greater={pg:.3e})"

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "seed": SEED,
        "bands": {"lo": BAND_A_LO, "hi": BAND_A_HI},
        "n_pert_per_unit": N_PERT,
        "k_windows": K_WINDOWS,
        "alphabet": "ARABIC_CONS_28 (hamza folded, ة->ه, ى->ي)",
        "arabic_ctrl": ARABIC_CTRL,
        "n_quran_units": len(q_units),
        "n_ctrl_units": len(ctrl_units),
        "n_q_perturbations": len(q_raw),
        "n_ctrl_perturbations": len(c_raw),
        "per_unit_sigma_intra_doc": {
            "quran_median": (
                float(np.median(_finite(q_sigma_per_unit)))
                if _finite(q_sigma_per_unit) else float("nan")
            ),
            "ctrl_median": (
                float(np.median(_finite(c_sigma_per_unit)))
                if _finite(c_sigma_per_unit) else float("nan")
            ),
        },
        "per_unit_canon_frob": {
            "quran_median": (
                float(np.median(_finite(q_canon_frob_per_unit)))
                if _finite(q_canon_frob_per_unit) else float("nan")
            ),
            "ctrl_median": (
                float(np.median(_finite(c_canon_frob_per_unit)))
                if _finite(c_canon_frob_per_unit) else float("nan")
            ),
        },
        "raw_frobenius_summary": raw_summary,
        "normalised_ccas_summary": norm_summary,
        "verdicts": {
            "raw_frobenius": _verdict(raw_summary, "raw"),
            "normalised_ccas": _verdict(norm_summary, "norm"),
        },
        "notes": (
            "CCAS_norm = |M_edited - M_canonical|_F / sigma_intra_doc "
            "where sigma_intra_doc is the std of Frobenius distances "
            "between K=10 random equal-length sub-document matrices "
            "and their mean. Tests whether the Quran's bigram structure "
            "is SPECIFICALLY more sensitive to a fixed-size edit than "
            "Arabic controls' bigram structure is -- the one variant "
            "of the letter-transition-matrix detector that was not "
            "tested by exp09/exp30."
        ),
        "provenance": {
            "input_checkpoint": "phase_06_phi_m.pkl",
            "perturbation_policy": "exp29::_apply_perturbation (internal, "
                                    "non-boundary word, non-terminal verse)",
            "design_doc": "2026-04-20 deep-scan synthesis",
        },
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # -------- console ------------------------------------------------- #
    print(f"[{EXP}] wrote {outfile}")
    print(f"[{EXP}] n_quran_units={len(q_units)}  n_ctrl_units={len(ctrl_units)}")
    print(f"[{EXP}] n_q_perturbations={len(q_raw)}  "
          f"n_ctrl_perturbations={len(c_raw)}")
    print(f"[{EXP}] per-unit sigma_intra_doc median: "
          f"Q={report['per_unit_sigma_intra_doc']['quran_median']:.3f}  "
          f"ctrl={report['per_unit_sigma_intra_doc']['ctrl_median']:.3f}")
    for label, s in [("RAW Frobenius", raw_summary),
                     ("NORM CCAS    ", norm_summary)]:
        print(f"[{EXP}] {label}: "
              f"Q median={s['q_median']:.4f}  "
              f"ctrl median={s['ctrl_median']:.4f}  "
              f"d={s['cohen_d']:+.3f}  "
              f"MW p_greater={s['mw_p_greater']:.3e}  "
              f"MW p_less={s['mw_p_less']:.3e}")
    print(f"[{EXP}] VERDICTS:")
    for k, v in report["verdicts"].items():
        print(f"   {k}: {v}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
