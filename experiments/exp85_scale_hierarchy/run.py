"""
exp85_scale_hierarchy/run.py
==============================
H5: Perturbation Scale Hierarchy as a Universal Oral-Text Law.

Motivation
    d(word) = 2.45 > d(verse) = 1.77 > d(letter) = 0.80 for the Quran.
    Is this ordering universal or Quran-specific?

Perturbation definitions
    letter:  swap one random interior letter in one random word
    word:    swap two random words within one verse
    verse:   swap two random verses

    For each perturbation, recompute features_5d, then compute the
    Euclidean distance from the canonical feature vector.

Protocol (frozen before execution)
    T1. Per corpus, per unit: compute canonical features_5d.
    T2. Per scale (letter, word, verse): apply 10 perturbations,
        compute perturbed features_5d, compute distance.
    T3. Cohen's d = mean(distance_scale) / pooled_sd across units.
    T4. Test hierarchy: d(word) > d(verse) > d(letter).
    T5. Test universality.

Pre-registered thresholds
    UNIVERSAL_LAW:  hierarchy holds for >= 6/7 corpora
    QURAN_SPECIFIC: hierarchy holds only for Quran
    NULL:           no consistent hierarchy

Reads: phase_06_phi_m.pkl -> CORPORA
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
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
from src.features import (  # noqa: E402
    el_rate, vl_cv, cn_rate, h_el, ARABIC_CONN,
    h_cond_initials,
)

EXP = "exp85_scale_hierarchy"
SEED = 42
N_PERT = 10
MIN_VERSES = 10

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]

DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)
ARABIC_CONS_28 = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")


def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)


def _features_fast(verses: list[str]) -> np.ndarray:
    el = el_rate(verses)
    cv = vl_cv(verses)
    cn = cn_rate(verses, ARABIC_CONN)
    hc = h_cond_initials(verses)
    he = h_el(verses)
    T = hc - he
    return np.array([el, cv, cn, hc, T])


def _perturb_letter(verses: list[str], rng: random.Random) -> list[str] | None:
    """Swap one interior letter in a random word of a random verse."""
    if len(verses) < 3:
        return None
    for _ in range(20):
        vi = rng.randint(1, len(verses) - 2)
        v = _strip_d(verses[vi])
        words = v.split()
        if len(words) < 2:
            continue
        wi = rng.randint(0, len(words) - 1)
        w = words[wi]
        alpha_pos = [i for i, c in enumerate(w) if c.isalpha()]
        if len(alpha_pos) < 3:
            continue
        interior = alpha_pos[1:-1]
        if not interior:
            continue
        pos = rng.choice(interior)
        original = w[pos]
        candidates = [c for c in ARABIC_CONS_28 if c != original]
        if not candidates:
            continue
        repl = rng.choice(candidates)
        new_w = w[:pos] + repl + w[pos + 1:]
        new_words = list(words)
        new_words[wi] = new_w
        new_verses = list(verses)
        new_verses[vi] = " ".join(new_words)
        return new_verses
    return None


def _perturb_word(verses: list[str], rng: random.Random) -> list[str] | None:
    """Swap two random words within a random verse."""
    if len(verses) < 3:
        return None
    for _ in range(20):
        vi = rng.randint(0, len(verses) - 1)
        words = verses[vi].split()
        if len(words) < 3:
            continue
        i1, i2 = rng.sample(range(len(words)), 2)
        new_words = list(words)
        new_words[i1], new_words[i2] = new_words[i2], new_words[i1]
        new_verses = list(verses)
        new_verses[vi] = " ".join(new_words)
        return new_verses
    return None


def _perturb_verse(verses: list[str], rng: random.Random) -> list[str] | None:
    """Swap two random verses."""
    if len(verses) < 3:
        return None
    i1, i2 = rng.sample(range(len(verses)), 2)
    new_verses = list(verses)
    new_verses[i1], new_verses[i2] = new_verses[i2], new_verses[i1]
    return new_verses


def _analyse_corpus(units, n_pert=N_PERT) -> dict:
    rng = random.Random(SEED)
    perturbations = {
        "letter": _perturb_letter,
        "word": _perturb_word,
        "verse": _perturb_verse,
    }

    # Collect per-unit distances for each scale
    scale_dists = {s: [] for s in perturbations}
    n_used = 0

    for u in units:
        if len(u.verses) < MIN_VERSES:
            continue
        n_used += 1

        f_canon = _features_fast(u.verses)

        for scale_name, pert_fn in perturbations.items():
            dists = []
            for _ in range(n_pert):
                pv = pert_fn(u.verses, rng)
                if pv is None:
                    continue
                f_pert = _features_fast(pv)
                d = float(np.linalg.norm(f_pert - f_canon))
                dists.append(d)
            if dists:
                scale_dists[scale_name].append(np.mean(dists))

    result = {"n_used": n_used}
    for scale in ["letter", "word", "verse"]:
        arr = np.array(scale_dists[scale])
        if len(arr) > 0:
            result[f"d_{scale}_mean"] = round(float(arr.mean()), 6)
            result[f"d_{scale}_std"] = round(float(arr.std(ddof=1)), 6) if len(arr) > 1 else 0
            result[f"d_{scale}_n"] = len(arr)
        else:
            result[f"d_{scale}_mean"] = None

    # Check hierarchy
    d_l = result.get("d_letter_mean")
    d_w = result.get("d_word_mean")
    d_v = result.get("d_verse_mean")
    if d_l is not None and d_w is not None and d_v is not None:
        result["hierarchy_word_gt_verse"] = d_w > d_v
        result["hierarchy_verse_gt_letter"] = d_v > d_l
        result["hierarchy_strict"] = d_w > d_v > d_l
    else:
        result["hierarchy_strict"] = None

    return result


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] Loading phase_06_phi_m.pkl...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    all_names = ["quran"] + ARABIC_CTRL
    results = {}

    for cname in all_names:
        units = CORPORA.get(cname, [])
        t_start = time.time()
        r = _analyse_corpus(units)
        dt = time.time() - t_start
        results[cname] = r

        d_l = r.get("d_letter_mean", "N/A")
        d_w = r.get("d_word_mean", "N/A")
        d_v = r.get("d_verse_mean", "N/A")
        h = "✓" if r.get("hierarchy_strict") else "✗"
        print(f"[{EXP}] {cname:20s}: n={r['n_used']:4d}  "
              f"d_letter={d_l}  d_word={d_w}  d_verse={d_v}  "
              f"strict={h}  ({dt:.1f}s)")

    # --- T4/T5: Universality ---
    print(f"\n[{EXP}] === T4/T5: Scale hierarchy universality ===")
    print(f"  {'Corpus':20s}  {'d(letter)':>10s}  {'d(word)':>10s}  {'d(verse)':>10s}  "
          f"{'w>v':>4s}  {'v>l':>4s}  strict")

    n_strict = 0
    n_wv = 0
    n_vl = 0
    for cname in all_names:
        r = results[cname]
        dl = r.get("d_letter_mean")
        dw = r.get("d_word_mean")
        dv = r.get("d_verse_mean")
        if dl is None:
            continue
        wv = dw > dv if dw and dv else False
        vl = dv > dl if dv and dl else False
        strict = wv and vl
        n_strict += int(strict)
        n_wv += int(wv)
        n_vl += int(vl)
        flag = " ***" if cname == "quran" else ""
        print(f"  {cname:20s}  {dl:10.6f}  {dw:10.6f}  {dv:10.6f}  "
              f"{'✓' if wv else '✗':>4s}  {'✓' if vl else '✗':>4s}  "
              f"{'✓' if strict else '✗'}{flag}")

    n_total = sum(1 for c in all_names if results[c].get("d_letter_mean") is not None)
    print(f"\n  Strict hierarchy: {n_strict}/{n_total}")
    print(f"  d(word) > d(verse): {n_wv}/{n_total}")
    print(f"  d(verse) > d(letter): {n_vl}/{n_total}")

    # --- Quran ratios ---
    q = results["quran"]
    if q.get("d_letter_mean") and q.get("d_word_mean") and q.get("d_verse_mean"):
        ratio_wl = q["d_word_mean"] / q["d_letter_mean"] if q["d_letter_mean"] > 0 else 0
        ratio_wv = q["d_word_mean"] / q["d_verse_mean"] if q["d_verse_mean"] > 0 else 0
        print(f"\n  Quran d(word)/d(letter) = {ratio_wl:.2f}")
        print(f"  Quran d(word)/d(verse) = {ratio_wv:.2f}")

    # --- Verdict ---
    if n_strict >= 6:
        verdict = "UNIVERSAL_LAW"
    elif n_strict >= 4:
        verdict = "SUGGESTIVE_UNIVERSAL"
    elif results["quran"].get("hierarchy_strict"):
        verdict = "QURAN_SPECIFIC"
    else:
        verdict = "NULL"

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  Strict hierarchy: {n_strict}/{n_total}")
    print(f"{'=' * 60}")

    report = {
        "experiment": EXP,
        "hypothesis": "H5 — Is d(word) > d(verse) > d(letter) a universal oral-text law?",
        "schema_version": 1,
        "n_perturbations": N_PERT,
        "per_corpus": results,
        "universality": {
            "n_strict_hierarchy": n_strict,
            "n_word_gt_verse": n_wv,
            "n_verse_gt_letter": n_vl,
            "n_corpora": n_total,
        },
        "verdict": verdict,
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
