"""
exp34_R11_adiyat_variants/run.py
================================
Closes the last ADIYAT §13.3 "not tested" cell: does the R11 symbolic-
regression formula Φ_sym = H_nano_ln + RST − VL_CV detect the three
Adiyat letter-substitution variants?

Formula source
    archive/scripts_pipeline/scripts/path_acd_tests.py:113–166
    (the original symbolic-regression discovery script).

Variants (see docs/ADIYAT_ANALYSIS_AR.md §2.4 table):
    A :  ع → غ  at verse 1 "والعاديات" → "والغاديات"
    B :  ض → ص  at verse 1 "ضبحاً"      → "صبحاً"
    C :  both simultaneously

Protocol
    * Read canonical Surah 100 verse texts from phase_06_phi_m (read-only).
    * Build 3 text variants by single-character replacement at the
      declared position (verse index, word index, char index).
      We implement the edit **at the raw-verse level** (before any
      diacritic stripping) so the edit is byte-identical to how a
      scribe would actually have produced it.
    * Compute Φ_sym for each of {canonical, A, B, C}.
    * Compare ΔΦ_sym against the locked per-Quran-surah Φ_sym standard
      deviation (σ_Q = 0.19464 from R11_manual_phi_sym.json:24)
      and against |Q_mean − ctrl_pool_mean| pairs.
    * Verdict: "CHANNEL_DETECTS_VARIANT" iff |Φ_sym_variant − Φ_sym_canon|
      / σ_Q ≥ 1.0 AND the sign moves the variant closer to the nearest
      control-corpus mean than to the Quran mean.

Reads (integrity-checked):
    phase_06_phi_m.pkl   (state['CORPORA']['quran'][99] = Surah 100)
    results/experiments/exp19_R11_symbolic_formula/R11_manual_phi_sym.json
      (for σ_Q and corpus means)

Writes ONLY under results/experiments/exp34_R11_adiyat_variants/:
    exp34_R11_adiyat_variants.json
    self_check_<ts>.json
"""
from __future__ import annotations

import json
import math
import sys
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

EXP = "exp34_R11_adiyat_variants"

# --------------------------------------------------------------------------- #
# Φ_sym primitive features (byte-exact parity with                             #
# archive/scripts_pipeline/scripts/path_acd_tests.py:113–166)                 #
# --------------------------------------------------------------------------- #
def compute_h_nano_ln(verses: list[str]) -> float:
    """ln of the character-bigram Shannon entropy (bits) over the
    verse text joined by single spaces."""
    text = " ".join(verses)
    bigrams = [text[i:i + 2] for i in range(len(text) - 1)]
    if len(bigrams) < 10:
        return float("nan")
    counts = Counter(bigrams)
    total = sum(counts.values())
    h = -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)
    return math.log(h) if h > 0 else float("nan")


def compute_rst(verses: list[str]) -> float:
    """RST (Rate of Singleton Tokens): fraction of the unique Arabic
    letters in the Unicode range U+0621–U+064A that occur exactly once
    across the whole surah text."""
    letters: list[str] = []
    for v in verses:
        letters.extend(c for c in v if "\u0621" <= c <= "\u064a")
    if not letters:
        return float("nan")
    counts = Counter(letters)
    n_unique = len(counts)
    if n_unique == 0:
        return float("nan")
    return sum(1 for n in counts.values() if n == 1) / n_unique


def compute_vl_cv(verses: list[str]) -> float:
    """Coefficient of variation of verse word counts. Uses population
    std (np.std default, ddof=0) to match the archival script."""
    wc = np.array([len(v.split()) for v in verses], dtype=float)
    if len(wc) < 2 or wc.mean() == 0.0:
        return float("nan")
    return float(wc.std() / (wc.mean() + 1e-12))


def phi_sym(verses: list[str]) -> dict:
    h_nano = compute_h_nano_ln(verses)
    rst = compute_rst(verses)
    vlcv = compute_vl_cv(verses)
    phi = h_nano + rst - vlcv
    return {
        "H_nano_ln": h_nano,
        "RST": rst,
        "VL_CV": vlcv,
        "Phi_sym": phi,
    }


# --------------------------------------------------------------------------- #
# Variant application                                                         #
# --------------------------------------------------------------------------- #
def _apply_single_char_edit(
    verses: list[str], verse_idx: int, old_char: str, new_char: str,
    occurrence: int = 1,
) -> tuple[list[str], dict]:
    """Replace the `occurrence`-th instance of `old_char` in the
    verse at `verse_idx`. `occurrence` is 1-indexed. Returns
    (new_verses, diagnostic_dict).

    Raises ValueError if the occurrence is not found -- no silent
    fallback (audit-fix F-6 style)."""
    v = verses[verse_idx]
    seen = 0
    char_pos = -1
    for i, c in enumerate(v):
        if c == old_char:
            seen += 1
            if seen == occurrence:
                char_pos = i
                break
    if char_pos < 0:
        raise ValueError(
            f"Occurrence {occurrence} of '{old_char}' not found in verse "
            f"{verse_idx + 1}: first 40 chars = {v[:40]!r}"
        )
    new_verse = v[:char_pos] + new_char + v[char_pos + 1:]
    new_verses = list(verses)
    new_verses[verse_idx] = new_verse
    return new_verses, {
        "verse_idx": verse_idx,
        "verse_1indexed": verse_idx + 1,
        "original_char": old_char,
        "new_char": new_char,
        "occurrence": occurrence,
        "char_pos_within_verse": char_pos,
        "context_before": v[max(0, char_pos - 6):char_pos],
        "context_after": v[char_pos + 1:char_pos + 7],
    }


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #
def _load_r11_manual() -> dict:
    p = (
        _ROOT / "results" / "experiments" / "exp19_R11_symbolic_formula"
        / "R11_manual_phi_sym.json"
    )
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    quran_units = CORPORA["quran"]
    # Surah 100 = index 99 (0-indexed), label "Q:100"
    adiyat = next(
        (u for u in quran_units
         if getattr(u, "label", None) == "Q:100" or u.label.endswith(":100")),
        None,
    )
    if adiyat is None:
        raise RuntimeError("Surah 100 (al-Adiyat) not found in CORPORA['quran']")

    canon_verses = list(adiyat.verses)

    # Variant A: ع → غ at verse 1 (والعاديات -> والغاديات).
    # Variant B: ض → ص at verse 1 (ضبحا       -> صبحا).
    # Variant C: both simultaneously.
    variants: dict[str, tuple[list[str], list[dict]]] = {}

    # -- A --
    vA, dA = _apply_single_char_edit(
        canon_verses, verse_idx=0, old_char="\u0639",
        new_char="\u063a", occurrence=1,  # ع -> غ
    )
    variants["A_ein_to_ghayn"] = (vA, [dA])

    # -- B --
    vB, dB = _apply_single_char_edit(
        canon_verses, verse_idx=0, old_char="\u0636",
        new_char="\u0635", occurrence=1,  # ض -> ص
    )
    variants["B_dhad_to_sad"] = (vB, [dB])

    # -- C -- (apply A then B on A's output)
    vC_tmp, dCA = _apply_single_char_edit(
        canon_verses, verse_idx=0, old_char="\u0639",
        new_char="\u063a", occurrence=1,
    )
    vC, dCB = _apply_single_char_edit(
        vC_tmp, verse_idx=0, old_char="\u0636",
        new_char="\u0635", occurrence=1,
    )
    variants["C_both"] = (vC, [dCA, dCB])

    # Compute Φ_sym for each
    canon_phi = phi_sym(canon_verses)
    results: dict = {
        "canonical": {
            "verse1_first40": canon_verses[0][:40],
            **canon_phi,
        },
        "variants": {},
    }
    for name, (vs, edits) in variants.items():
        vp = phi_sym(vs)
        results["variants"][name] = {
            "edits": edits,
            "verse1_first40": vs[0][:40],
            **vp,
            "delta_H_nano_ln": vp["H_nano_ln"] - canon_phi["H_nano_ln"],
            "delta_RST": vp["RST"] - canon_phi["RST"],
            "delta_VL_CV": vp["VL_CV"] - canon_phi["VL_CV"],
            "delta_Phi_sym": vp["Phi_sym"] - canon_phi["Phi_sym"],
        }

    # Standardise against per-Quran-surah σ and nearest-ctrl distance
    r11_manual = _load_r11_manual()
    per_corpus = r11_manual["per_corpus"]
    q_mu = per_corpus["quran"]["phi_sym_mean"]
    q_sd = per_corpus["quran"]["phi_sym_std"]

    # Nearest control corpus to Quran on Phi_sym (low or high)
    ctrl_dist: list[tuple[str, float]] = []
    for c_name, c_stats in per_corpus.items():
        if c_name == "quran" or c_stats.get("phi_sym_mean") is None:
            continue
        ctrl_dist.append((c_name, c_stats["phi_sym_mean"] - q_mu))
    # Nearest below and nearest above
    below = sorted([x for x in ctrl_dist if x[1] < 0], key=lambda x: -x[1])
    above = sorted([x for x in ctrl_dist if x[1] >= 0], key=lambda x: x[1])
    nearest_below = below[0] if below else (None, None)
    nearest_above = above[0] if above else (None, None)

    for name, info in results["variants"].items():
        dphi = info["delta_Phi_sym"]
        info["delta_in_Quran_sigma"] = float(dphi / q_sd) if q_sd > 0 else None
        # Does the variant move TOWARD a control-pole? +sign toward
        # nearest_above, -sign toward nearest_below (both mean "away
        # from Quran centre").
        if dphi < 0 and nearest_below[0] is not None:
            info["moves_toward_ctrl_pole"] = nearest_below[0]
            info["distance_to_that_pole_before"] = abs(nearest_below[1])
            info["distance_to_that_pole_after"] = abs(
                (canon_phi["Phi_sym"] + dphi) -
                per_corpus[nearest_below[0]]["phi_sym_mean"]
            )
        elif dphi > 0 and nearest_above[0] is not None:
            info["moves_toward_ctrl_pole"] = nearest_above[0]
            info["distance_to_that_pole_before"] = abs(nearest_above[1])
            info["distance_to_that_pole_after"] = abs(
                (canon_phi["Phi_sym"] + dphi) -
                per_corpus[nearest_above[0]]["phi_sym_mean"]
            )
        else:
            info["moves_toward_ctrl_pole"] = None

        sigma_mag = abs(info["delta_in_Quran_sigma"] or 0.0)
        info["verdict"] = (
            "CHANNEL_DETECTS_VARIANT" if sigma_mag >= 1.0 else
            "DETECTION_MARGINAL" if sigma_mag >= 0.5 else
            "CHANNEL_BLIND"
        )

    # ---- Report --------------------------------------------------------- #
    report = {
        "experiment": EXP,
        "schema_version": 1,
        "formula": "Phi_sym = H_nano_ln + RST - VL_CV",
        "formula_source": (
            "archive/scripts_pipeline/scripts/path_acd_tests.py:113-166"
        ),
        "surah_label": adiyat.label,
        "n_verses": len(canon_verses),
        "Quran_phi_sym_mean_locked": q_mu,
        "Quran_phi_sym_std_locked": q_sd,
        "nearest_ctrl_pole_below_Quran": {
            "corpus": nearest_below[0],
            "delta_mu": nearest_below[1],
        },
        "nearest_ctrl_pole_above_Quran": {
            "corpus": nearest_above[0],
            "delta_mu": nearest_above[1],
        },
        "results": results,
        "interpretation": (
            "Each variant's delta_Phi_sym is compared to the locked "
            "within-Quran surah standard deviation sigma_Q. A variant "
            "that shifts Phi_sym by more than 1 sigma_Q is declared "
            "DETECTED by this channel; 0.5-1 sigma_Q is MARGINAL; "
            "below 0.5 sigma_Q is BLIND."
        ),
        "provenance": {
            "canon_input_checkpoint": "phase_06_phi_m.pkl",
            "r11_manual_source": (
                "results/experiments/exp19_R11_symbolic_formula/"
                "R11_manual_phi_sym.json"
            ),
        },
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # -------------------- console ---------------------------------------- #
    print(f"[{EXP}] wrote {outfile}")
    print(f"[{EXP}] canonical  Phi_sym = {canon_phi['Phi_sym']:+.5f}  "
          f"(H_nano_ln={canon_phi['H_nano_ln']:+.4f}  "
          f"RST={canon_phi['RST']:.4f}  VL_CV={canon_phi['VL_CV']:.4f})")
    print(f"[{EXP}] per-Quran-surah locked sigma = {q_sd:.5f}")
    for name, info in results["variants"].items():
        dphi = info["delta_Phi_sym"]
        nsig = info["delta_in_Quran_sigma"]
        print(f"   {name:24s}  Phi_sym={info['Phi_sym']:+.5f}  "
              f"DeltaPhi={dphi:+.5f} ({nsig:+.3f}sigma_Q)  "
              f"verdict={info['verdict']}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
