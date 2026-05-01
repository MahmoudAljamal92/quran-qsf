"""
expP18_shannon_capacity_el/run.py
=================================
Shannon-information-theoretic upper bounds on the EL feature.

Pre-registered in PREREG.md (frozen 2026-04-26, v7.9-cand patch E).

Reads:  phase_06_phi_m.pkl ::state[CORPORA]
Writes: results/experiments/expP18_shannon_capacity_el/expP18_shannon_capacity_el.json
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import unicodedata
from collections import Counter
from math import log2
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase, safe_output_dir, self_check_begin, self_check_end,
)
from src.features import el_rate  # noqa: E402

EXP = "expP18_shannon_capacity_el"
ALPHABET_SIZE = 28  # Arabic abjad consonant alphabet


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _terminal_natural_letter(verse: str) -> str | None:
    for c in reversed(verse.strip()):
        cat = unicodedata.category(c)
        if cat.startswith("M"):
            continue
        if c.isalpha():
            return c
    return None


def _per_corpus_terminal_pmf(units: list) -> dict:
    finals: list[str] = []
    for u in units:
        for v in u.verses:
            ch = _terminal_natural_letter(v)
            if ch:
                finals.append(ch)
    if not finals:
        return {"n_finals": 0, "p_max": None, "EL_iid_floor": None,
                 "H2_renyi": None, "EL_actual": None}
    cnt = Counter(finals)
    tot = sum(cnt.values())
    pmf = {l: c / tot for l, c in cnt.items()}
    p_max = max(pmf.values())
    # EL i.i.d. floor = Σ p²
    sum_p2 = sum(p * p for p in pmf.values())
    H2 = -log2(sum_p2) if sum_p2 > 0 else float("nan")
    # Actual EL on the concatenated verse stream
    all_verses = []
    for u in units:
        all_verses.extend(u.verses)
    EL_actual = el_rate(all_verses) if len(all_verses) >= 2 else float("nan")
    # Theoretical max EL under "pmax + 27 uniform off-dominant"
    p_off = (1.0 - p_max) / (ALPHABET_SIZE - 1)
    EL_max_under_pmax = p_max * p_max + (ALPHABET_SIZE - 1) * p_off * p_off
    return {
        "n_finals": tot,
        "n_distinct_letters": len(cnt),
        "p_max": p_max,
        "top_letter": cnt.most_common(1)[0][0],
        "EL_iid_floor": sum_p2,
        "H2_renyi": H2,
        "EL_actual": EL_actual,
        "EL_actual_minus_floor": EL_actual - sum_p2 if EL_actual is not None else None,
        "EL_max_under_pmax_uniform_off": EL_max_under_pmax,
    }


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    print(f"[{EXP}] Computing per-corpus Shannon EL bounds:")
    table: dict[str, dict] = {}
    for name, units in CORPORA.items():
        s = _per_corpus_terminal_pmf(units)
        table[name] = s
        if s.get("p_max") is None:
            print(f"[{EXP}]   {name:20s} (empty)")
            continue
        print(f"[{EXP}]   {name:20s} p_max={s['p_max']:.3f}  "
              f"EL_iid_floor={s['EL_iid_floor']:.3f}  "
              f"EL_actual={s['EL_actual']:.3f}  "
              f"H2={s['H2_renyi']:.3f}")

    # --- Theorem ---
    # For any corpus with terminal-letter pmf having dominant mass p_max
    # on a 28-letter alphabet, the maximum achievable EL under independent
    # sampling is p_max² + (1-p_max)²/27.
    print(f"\n[{EXP}] === Theorem ===")
    print(f"[{EXP}] For a 28-letter alphabet with dominant-letter mass p_max,")
    print(f"[{EXP}] the EL_iid_floor (= Σ p²) is BOUNDED ABOVE by:")
    print(f"[{EXP}]   EL_max(p_max) = p_max² + (1-p_max)²/(K-1)   K=28")
    print(f"[{EXP}]")
    print(f"[{EXP}] Numerical implications:")
    for pm in (0.10, 0.20, 0.30, 0.50, 0.70):
        bound = pm * pm + (1 - pm) ** 2 / (ALPHABET_SIZE - 1)
        print(f"[{EXP}]   p_max = {pm:.2f}  ->  EL_max <= {bound:.4f}")
    print(f"[{EXP}]")
    print(f"[{EXP}] Inversion: to reach EL >= 0.50 under i.i.d. sampling,")
    print(f"[{EXP}] solve p² + (1-p)²/27 = 0.50:")
    # Solve x^2 + (1-x)^2/27 = 0.5  =>  27 x^2 + (1-x)^2 = 13.5
    # =>  27 x^2 + 1 - 2x + x^2 = 13.5  =>  28 x^2 - 2 x - 12.5 = 0
    a, b, c = 28, -2, -12.5
    disc = b*b - 4*a*c
    x_pos = (-b + (disc**0.5)) / (2*a)
    print(f"[{EXP}]   minimum p_max for EL >= 0.50 (i.i.d.) = {x_pos:.4f}")

    # Inversion at EL = 0.71 (Quran's actual)
    quran_actual = table.get("quran", {}).get("EL_actual")
    quran_pmax = table.get("quran", {}).get("p_max")
    if quran_actual is not None and quran_pmax is not None:
        # Calc minimum p_max for EL_iid >= quran_actual
        c2 = -(quran_actual - 1.0/27.0) * 27.0
        # 28 p_max^2 - 2 p_max + (1 - 27 EL) = 0  // up to algebraic shuffle
        # Actually with EL = p_max^2 + (1-p_max)^2/27:
        # 27 EL = 27 p_max^2 + (1-p_max)^2
        # 27 EL = 27 p_max^2 + 1 - 2 p_max + p_max^2
        # 27 EL = 28 p_max^2 - 2 p_max + 1
        # 28 p_max^2 - 2 p_max + (1 - 27 EL) = 0
        a2, b2, c2 = 28, -2, 1 - 27 * quran_actual
        disc2 = b2*b2 - 4*a2*c2
        if disc2 >= 0:
            x_min_for_quran = (-b2 + (disc2**0.5)) / (2*a2)
            print(f"[{EXP}] Minimum p_max needed for EL_iid >= Quran actual EL ({quran_actual:.3f}): "
                  f"{x_min_for_quran:.4f}")
            print(f"[{EXP}] Quran observed p_max(ن) = {quran_pmax:.4f}")
            saturates = abs(quran_pmax - x_min_for_quran) < 0.05
            print(f"[{EXP}] Saturation: {'YES (within 5% absolute tolerance)' if saturates else 'NO'}")
        else:
            x_min_for_quran = None
    else:
        x_min_for_quran = None

    record = {
        "experiment": EXP,
        "prereg_sha256": _prereg_hash(),
        "alphabet_size_K": ALPHABET_SIZE,
        "table": table,
        "theorem_min_pmax_for_EL_iid_geq_050": x_pos,
        "min_pmax_for_quran_EL": x_min_for_quran,
        "quran_observed_pmax": quran_pmax,
        "quran_observed_EL": quran_actual,
        "quran_saturates_iid_bound": (
            abs(quran_pmax - x_min_for_quran) < 0.05
            if (quran_pmax is not None and x_min_for_quran is not None)
            else None
        ),
        "wall_time_s": time.time() - t0,
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] -> {out / (EXP + '.json')}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
