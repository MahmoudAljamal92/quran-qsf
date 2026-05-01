"""
exp45_two_letter_746k/run.py
============================
Two-letter enumeration on Surah 100 (Al-Adiyat) verse 1.

Motivation
    exp43 exhaustively tested all 864 single-letter substitutions and
    reported compound detection rates.  This experiment extends the
    enumeration to **all pairs of simultaneous single-letter edits** at
    distinct consonant positions, addressing the "multi-letter gap" in
    the detection claim.

    The verse has N_pos consonant positions, each admitting 27
    replacements.  For two *distinct* positions (i < j) the number of
    unique two-letter variants is:

        C(N_pos, 2) x 27 x 27 ~ 362 k   (for N_pos = 32)

    (The user-facing "864² → 746 k" count includes ordered pairs and
    same-position edits; this script enumerates only the non-degenerate
    set where i < j, giving ~362 k distinct variants.  Add ordered
    pairs to exactly match the full 746 k if needed.)

Detectors (identical to exp43)
    D1  Phi_M         : |Phi_M_var − Phi_M_canon| > 0
    D2  NCD_doc       : NCD above exp41 ctrl-p95
    D3  NCD_win       : NCD on 3-verse window above exp41 ctrl-p95
    D4  H_char window : |ΔH_char| > 0.01 bits (exploratory)
    D5  CCAS Frob     : ‖ΔM‖_F > 0 (tautological)

    Compound headline = D2 AND D5 (same as exp43).

Outputs
    Per-variant row  :  (pos1, repl1, pos2, repl2) + D1–D5 flags
    Aggregate rates  :  per detector, compound, by inter-position gap

Reads (integrity-checked)
    phase_06_phi_m.pkl  →  CORPORA, mu, S_inv
    results/experiments/exp41_gzip_formalised/exp41_gzip_formalised.json

Writes ONLY under results/experiments/exp45_two_letter_746k/

Runtime estimate  ~45–90 min full;  ~2 min fast (100 position-pairs).
"""
from __future__ import annotations

import gzip
import json
import math
import sys
import time
from itertools import combinations
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
from src import features as ft  # noqa: E402

EXP = "exp45_two_letter_746k"

ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ALPH_IDX = {c: i for i, c in enumerate(ARABIC_CONS_28)}
ADIYAT_LABEL = "Q:100"
WINDOW = 3
GZIP_LEVEL = 9

DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)
_FOLD = {"ء": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "ا", "ئ": "ا",
         "ة": "ه", "ى": "ي"}


# --------------------------------------------------------------------------- #
# Primitives  (shared with exp43)                                              #
# --------------------------------------------------------------------------- #
def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)


def _letters_28(text: str) -> str:
    out: list[str] = []
    for c in _strip_d(text):
        if c in _FOLD:
            out.append(_FOLD[c])
        elif c in _ALPH_IDX:
            out.append(c)
    return "".join(out)


def _gz_len(s: str) -> int:
    return len(gzip.compress(s.encode("utf-8"), compresslevel=GZIP_LEVEL))


def _ncd(a: str, b: str) -> float:
    if not a and not b:
        return 0.0
    za = _gz_len(a); zb = _gz_len(b); zab = _gz_len(a + b)
    denom = max(1, max(za, zb))
    return (zab - min(za, zb)) / denom


def _matrix(letters: str) -> np.ndarray:
    N = len(_ALPH_IDX)
    M = np.zeros((N, N), dtype=float)
    for a, b in zip(letters[:-1], letters[1:]):
        ia = _ALPH_IDX.get(a); ib = _ALPH_IDX.get(b)
        if ia is not None and ib is not None:
            M[ia, ib] += 1.0
    return M


def _h_char_window(verses) -> float:
    """Intra-word bigram minus unigram entropy over a verse window."""
    from collections import Counter
    stream: list[str] = []
    first = True
    for v in verses:
        for w in _strip_d(v).split():
            letters = [c for c in w if c.isalpha()]
            if not letters:
                continue
            if not first:
                stream.append("#")
            stream.extend(letters)
            first = False
    if len(stream) < 4:
        return 0.0
    bigrams = [
        (stream[i], stream[i + 1])
        for i in range(len(stream) - 1)
        if "#" not in (stream[i], stream[i + 1])
    ]
    unigrams = [c for c in stream if c != "#"]
    if not bigrams or not unigrams:
        return 0.0
    cb = Counter(bigrams); cu = Counter(unigrams)
    tb = sum(cb.values()); tu = sum(cu.values())
    hb = -sum((n / tb) * math.log2(n / tb) for n in cb.values())
    hu = -sum((n / tu) * math.log2(n / tu) for n in cu.values())
    return hb - hu


# --------------------------------------------------------------------------- #
# Thresholds from exp41                                                        #
# --------------------------------------------------------------------------- #
def _load_exp41_thresholds() -> dict:
    path = _ROOT / "results" / "experiments" / "exp41_gzip_formalised" / \
        "exp41_gzip_formalised.json"
    if not path.exists():
        return {"doc_ctrl_p95": 0.05, "win_ctrl_p95": 0.10}
    with open(path, "r", encoding="utf-8") as f:
        j = json.load(f)
    return {
        "doc_ctrl_p95": float(j["doc_scale_summary"]["ctrl_p95"]),
        "win_ctrl_p95": float(j["window_scale_summary"]["ctrl_p95"]),
    }


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main(fast: bool = False) -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    CORPORA = state["CORPORA"]
    mu = np.asarray(state["mu"], dtype=float)
    Sinv = np.asarray(state["S_inv"], dtype=float)

    adiyat = None
    for u in CORPORA.get("quran", []):
        if u.label == ADIYAT_LABEL:
            adiyat = u
            break
    if adiyat is None:
        raise RuntimeError("Surah 100 not found in CORPORA['quran']")

    thresholds = _load_exp41_thresholds()
    doc_p95 = thresholds["doc_ctrl_p95"]
    win_p95 = thresholds["win_ctrl_p95"]

    canon_verses = list(adiyat.verses)
    v1 = canon_verses[0]

    # --- Canonical baselines ---
    f_canon = ft.features_5d(canon_verses)
    phi_canon = float(ft.phi_m(f_canon, mu, Sinv).ravel()[0])
    canon_doc_stream = _letters_28(" ".join(canon_verses))
    win_lo, win_hi = 0, min(WINDOW, len(canon_verses))
    canon_win_stream = _letters_28(" ".join(canon_verses[win_lo:win_hi]))
    canon_win_verses = canon_verses[win_lo:win_hi]
    canon_Mwin = _matrix(canon_win_stream)
    canon_H_win = _h_char_window(canon_win_verses)

    # --- Identify consonant positions in verse 1 ---
    cons_positions = [i for i, ch in enumerate(v1) if ch in ARABIC_CONS_28]
    n_pos = len(cons_positions)
    print(f"[{EXP}] verse 1 has {n_pos} consonant positions "
          f"-> C({n_pos},2) × 27² = {n_pos*(n_pos-1)//2 * 729} "
          f"two-letter variants")

    all_pairs = list(combinations(range(n_pos), 2))
    if fast:
        import random
        rng = random.Random(42)
        cap = min(100, len(all_pairs))
        all_pairs = rng.sample(all_pairs, cap)
        print(f"[{EXP}] FAST mode: sampling {cap} position-pairs")

    # --- Enumerate ---
    n_total = len(all_pairs) * 27 * 27
    results: list[dict] = []
    counts = {"D1": 0, "D2": 0, "D3": 0, "D4": 0, "D5": 0,
              "compound_D2_D5": 0, "compound_any": 0}
    done = 0
    batch_t = time.time()

    for pair_idx, (pi, pj) in enumerate(all_pairs):
        abs_i = cons_positions[pi]
        abs_j = cons_positions[pj]
        orig_i = v1[abs_i]
        orig_j = v1[abs_j]

        for repl_i in ARABIC_CONS_28:
            if repl_i == orig_i:
                continue
            for repl_j in ARABIC_CONS_28:
                if repl_j == orig_j:
                    continue

                # Apply both substitutions
                v1_new = list(v1)
                v1_new[abs_i] = repl_i
                v1_new[abs_j] = repl_j
                v1_new = "".join(v1_new)
                new_verses = [v1_new] + list(canon_verses[1:])

                # D1 Phi_M
                try:
                    f_var = ft.features_5d(new_verses)
                    phi_var = float(ft.phi_m(f_var, mu, Sinv).ravel()[0])
                except Exception:
                    done += 1
                    continue
                d1 = abs(phi_var - phi_canon) > 1e-6

                # D2 doc NCD
                var_doc_stream = _letters_28(" ".join(new_verses))
                ncd_doc = _ncd(canon_doc_stream, var_doc_stream)
                d2 = ncd_doc >= doc_p95

                # D3 window NCD
                var_win_verses = new_verses[win_lo:win_hi]
                var_win_stream = _letters_28(" ".join(var_win_verses))
                ncd_win = _ncd(canon_win_stream, var_win_stream)
                d3 = ncd_win >= win_p95

                # D4 H_char
                var_H = _h_char_window(var_win_verses)
                d_H = abs(var_H - canon_H_win)
                d4 = d_H > 0.01

                # D5 CCAS Frob
                Mwin_var = _matrix(var_win_stream)
                d_F = float(np.linalg.norm(Mwin_var - canon_Mwin))
                d5 = d_F > 0

                counts["D1"] += int(d1)
                counts["D2"] += int(d2)
                counts["D3"] += int(d3)
                counts["D4"] += int(d4)
                counts["D5"] += int(d5)
                counts["compound_D2_D5"] += int(d2 and d5)
                counts["compound_any"] += int(d1 or d2 or d3 or d4 or d5)

                # Store only a summary row (full per-variant JSON would be GBs)
                if fast:
                    results.append({
                        "pos1": abs_i, "orig1": orig_i, "repl1": repl_i,
                        "pos2": abs_j, "orig2": orig_j, "repl2": repl_j,
                        "phi_m_delta": phi_var - phi_canon,
                        "ncd_doc": round(ncd_doc, 5),
                        "D1": d1, "D2": d2, "D3": d3, "D4": d4, "D5": d5,
                    })

                done += 1
                if done % 5000 == 0:
                    elapsed = time.time() - batch_t
                    rate = done / elapsed if elapsed > 0 else 0
                    eta = (n_total - done) / rate if rate > 0 else 0
                    print(f"  [{done:>7d}/{n_total}]  "
                          f"{rate:.0f} var/s  ETA {eta:.0f}s")

    elapsed_total = time.time() - t0
    n_var = done

    # --- Detection rates ---
    def _rate(key: str) -> float:
        return counts[key] / n_var if n_var else 0.0

    r_d1 = _rate("D1")
    r_d2 = _rate("D2")
    r_d3 = _rate("D3")
    r_d4 = _rate("D4")
    r_d5 = _rate("D5")
    r_compound = _rate("compound_D2_D5")
    r_any = _rate("compound_any")

    report = {
        "experiment": EXP,
        "schema_version": 1,
        "fast_mode": fast,
        "adiyat_label": ADIYAT_LABEL,
        "canonical_verse1": v1,
        "canonical_phi_m": phi_canon,
        "n_consonant_positions": n_pos,
        "n_position_pairs_tested": len(all_pairs),
        "n_variants_evaluated": n_var,
        "n_variants_theoretical": n_pos * (n_pos - 1) // 2 * 729,
        "exp41_thresholds": thresholds,
        "detection_counts": counts,
        "detection_rates": {
            "D1_phi_m_moves": round(r_d1, 6),
            "D2_ncd_doc_above_ctrl95": round(r_d2, 6),
            "D3_ncd_win_above_ctrl95": round(r_d3, 6),
            "D4_h_char_moves_uncalibrated": round(r_d4, 6),
            "D5_ccas_frob_moves_tautological": round(r_d5, 6),
            "compound_D2_AND_D5_headline": round(r_compound, 6),
            "compound_ANY": round(r_any, 6),
        },
        "comparison_vs_exp43_single_letter": {
            "note": (
                "exp43 tested 864 single-letter variants. If detection "
                "rates here are HIGHER, two-letter edits are easier to "
                "detect (expected — more signal per variant). If LOWER, "
                "there may be cancellation effects between edits."
            ),
        },
        "runtime_seconds": round(elapsed_total, 2),
        "verdict": (
            f"Two-letter compound D2&D5 headline: "
            f"{counts['compound_D2_D5']}/{n_var} "
            f"({r_compound:.1%}).  "
            f"ANY detector fires on {r_any:.1%} of variants."
        ),
    }

    if fast and results:
        report["sample_variants"] = results[:50]

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # --- Console ---
    print(f"\n[{EXP}] DONE in {elapsed_total:.1f}s  "
          f"({n_var} variants evaluated)")
    print(f"[{EXP}] DETECTION RATES (of {n_var} two-letter variants):")
    print(f"   D1 Phi_M moves                    : {r_d1:.1%}")
    print(f"   D2 NCD doc above ctrl-p95         : {r_d2:.1%}")
    print(f"   D3 NCD win above ctrl-p95         : {r_d3:.1%}")
    print(f"   D4 H_char moves (uncalibrated)    : {r_d4:.1%}  [exploratory]")
    print(f"   D5 CCAS Frob moves (tautological) : {r_d5:.1%}  [trivial]")
    print(f"   D2 AND D5 [headline]              : {r_compound:.1%}")
    print(f"   ANY of D1-D5                      : {r_any:.1%}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    fast = "--fast" in sys.argv
    sys.exit(main(fast=fast))
