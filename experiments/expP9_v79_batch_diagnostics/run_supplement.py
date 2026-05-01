"""
expP9_v79_batch_diagnostics/run_supplement.py
=============================================
Supplementary cross-tradition + hadith re-run of N1 + NEW2 using the full
load_all(include_cross_tradition=True) corpus set, plus the hadith Bukhari
corpus that was missing from phase_06_phi_m.pkl.

This addresses the v7.9-cand main batch's incomplete N1 (only 7 of the
intended 13 corpora were loaded from phase_06).

Writes:
  results/experiments/expP9_v79_batch_diagnostics/N1_supplement.json
  results/experiments/expP9_v79_batch_diagnostics/NEW2_supplement.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import safe_output_dir, self_check_begin, self_check_end  # noqa: E402
from src import raw_loader  # noqa: E402
from src.features import el_rate  # noqa: E402

EXP = "expP9_v79_batch_diagnostics"
SEED = 42
MIN_VERSES = 2

ARABIC_CTRL = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
               "ksucca", "arabic_bible", "hindawi"]
NON_ARABIC = ["hebrew_tanakh", "greek_nt", "iliad_greek",
              "pali_dn", "pali_mn", "rigveda", "avestan_yasna"]
ALL_CTRL = ARABIC_CTRL + NON_ARABIC + ["hadith_bukhari"]


def _verse_final_letter(v: str, allow_any: bool = False) -> str | None:
    s = v.strip()
    for c in reversed(s):
        if "\u0621" <= c <= "\u064A":
            return c
    if allow_any:
        return s[-1] if s else None
    return None


def _fit_svm_1d_auc(EL: np.ndarray, y: np.ndarray, seed: int = SEED) -> dict:
    """H5 (2026-04-26): returned ``\"auc\"`` is IN-SAMPLE; explicit honest
    key ``\"auc_in_sample\"`` is also present (legacy ``\"auc\"`` retained
    as alias)."""
    from sklearn.svm import SVC
    from sklearn.metrics import roc_auc_score
    X = EL.reshape(-1, 1)
    svm = SVC(kernel="linear", C=1.0, class_weight="balanced",
              random_state=seed)
    svm.fit(X, y)
    auc_is = float(roc_auc_score(y, svm.decision_function(X)))
    return {
        # H5: explicit honest label + legacy alias.
        "auc_in_sample": auc_is,
        "auc": auc_is,
        "w": float(svm.coef_[0][0]), "b": float(svm.intercept_[0]),
    }


def _gather_units(units, min_v: int = MIN_VERSES) -> list[dict]:
    rows = []
    for u in units:
        nv = len(u.verses)
        if nv < min_v:
            continue
        try:
            el = float(el_rate(list(u.verses)))
        except Exception:
            continue
        rows.append({"label": getattr(u, "label", ""),
                     "n_verses": nv, "el": el,
                     "verses": list(u.verses)})
    return rows


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()
    print(f"[{EXP}] supplement: full cross-tradition + hadith re-run of N1 + NEW2")

    print(f"[{EXP}] raw_loader.load_all(include_cross_tradition=True) ...")
    CORPORA = raw_loader.load_all(include_extras=True,
                                   include_cross_lang=False,
                                   include_cross_tradition=True)
    print(f"[{EXP}] corpora loaded: {sorted(CORPORA.keys())}")

    # Add hadith separately
    try:
        hadith_units = raw_loader.load_hadith_bukhari()
        CORPORA["hadith_bukhari"] = hadith_units
        print(f"[{EXP}] + hadith_bukhari: {len(hadith_units)} units")
    except Exception as e:
        print(f"[{EXP}] hadith load failed: {e}")
        CORPORA["hadith_bukhari"] = []

    q_units = CORPORA.get("quran", [])
    q_rows = _gather_units(q_units)
    EL_q = np.array([r["el"] for r in q_rows], dtype=float)
    print(f"[{EXP}] Quran rows: {len(q_rows)}  median EL = {np.median(EL_q):.3f}")

    # --- N1 supplement: cross-tradition EL-alone --------------------------
    print(f"\n[{EXP}] === N1 supplement: cross-tradition EL-alone ===")
    n1: dict[str, dict] = {}
    for ctrl_name in ALL_CTRL:
        units = CORPORA.get(ctrl_name, [])
        ctrl_rows = _gather_units(units)
        if len(ctrl_rows) < 5:
            n1[ctrl_name] = {"skipped": "too few units",
                              "n_ctrl": len(ctrl_rows)}
            continue
        EL_c = np.array([r["el"] for r in ctrl_rows], dtype=float)
        EL_all = np.concatenate([EL_q, EL_c])
        y_all = np.concatenate([np.ones(len(EL_q)), np.zeros(len(EL_c))])
        try:
            fit = _fit_svm_1d_auc(EL_all, y_all)
        except Exception as e:
            n1[ctrl_name] = {"error": str(e)}; continue
        n1[ctrl_name] = {
            "n_quran": len(EL_q), "n_ctrl": len(EL_c),
            "auc": fit["auc"], "w": fit["w"], "b": fit["b"],
            "median_el_quran": float(np.median(EL_q)),
            "median_el_ctrl": float(np.median(EL_c)),
        }
        cls = "arabic" if ctrl_name in ARABIC_CTRL else (
              "hadith" if ctrl_name == "hadith_bukhari" else "non_arabic")
        print(f"[{EXP}]   [{cls:10s}] Quran vs {ctrl_name:18s} n_C={len(EL_c):5d}  "
              f"AUC = {fit['auc']:.4f}  med(EL_C)={np.median(EL_c):.3f}")

    aucs_arabic = [n1[k]["auc"] for k in ARABIC_CTRL if "auc" in n1.get(k, {})]
    aucs_nonarabic = [n1[k]["auc"] for k in NON_ARABIC if "auc" in n1.get(k, {})]
    auc_hadith = n1.get("hadith_bukhari", {}).get("auc")
    summary_n1 = {
        "min_auc_arabic": min(aucs_arabic) if aucs_arabic else None,
        "min_auc_nonarabic": min(aucs_nonarabic) if aucs_nonarabic else None,
        "auc_hadith": auc_hadith,
        "n_arabic_ok": len(aucs_arabic),
        "n_nonarabic_ok": len(aucs_nonarabic),
    }
    print(f"[{EXP}]   summary:")
    print(f"[{EXP}]     min AUC vs Arabic ctrl     = {summary_n1['min_auc_arabic']}")
    print(f"[{EXP}]     min AUC vs non-Arabic ctrl = {summary_n1['min_auc_nonarabic']}")
    print(f"[{EXP}]     AUC vs hadith              = {auc_hadith}")
    if (summary_n1["min_auc_arabic"] is not None
            and summary_n1["min_auc_nonarabic"] is not None
            and summary_n1["min_auc_arabic"] >= 0.95
            and summary_n1["min_auc_nonarabic"] >= 0.95):
        verdict = "PASS_quran_specific_cross_script"
    elif (summary_n1["min_auc_arabic"] is not None
            and summary_n1["min_auc_arabic"] >= 0.95):
        verdict = "PASS_arabic_only" if (
            summary_n1["min_auc_nonarabic"] is not None
            and summary_n1["min_auc_nonarabic"] < 0.95) else "PARTIAL"
    else:
        verdict = "FAIL_class_property"
    print(f"[{EXP}]   verdict = {verdict}")

    # --- NEW2 supplement: per-corpus dominant-final forensics ------------
    print(f"\n[{EXP}] === NEW2 supplement: dominant-final forensics ===")
    new2_rows = []
    from collections import Counter
    for name in ["quran"] + ALL_CTRL:
        units = CORPORA.get(name, [])
        all_finals = []
        for u in units:
            for v in u.verses:
                f = _verse_final_letter(v, allow_any=True)
                if f is not None:
                    all_finals.append(f)
        if not all_finals:
            new2_rows.append({"corpus": name, "n": 0, "skipped": True})
            continue
        c = Counter(all_finals)
        n = sum(c.values())
        pmf = {k: v / n for k, v in c.items()}
        argmax = max(pmf, key=pmf.get)
        sum_p2 = float(sum(p * p for p in pmf.values()))
        new2_rows.append({
            "corpus": name, "n_verse_finals": n,
            "alphabet_size": len(pmf),
            "dominant_final": argmax,
            "p_max": float(pmf[argmax]),
            "p_max_squared": float(pmf[argmax] ** 2),
            "sum_p2": sum_p2,
            "renyi2_bits": float(-np.log2(sum_p2)) if sum_p2 > 0 else None,
            "is_arabic": name in (["quran"] + ARABIC_CTRL + ["hadith_bukhari"]),
        })
        print(f"[{EXP}]   {name:18s} n={n:7d}  dominant='{argmax}'  "
              f"p_max={pmf[argmax]:.4f}  Σp²={sum_p2:.4f}  "
              f"R2={new2_rows[-1]['renyi2_bits']:.3f} bits")
    # Within-Arabic-incl-hadith ranking by p_max
    rows_with_data = [r for r in new2_rows if not r.get("skipped")]
    arabic_rows = [r for r in rows_with_data if r["is_arabic"]]
    arabic_rows.sort(key=lambda r: -r["p_max"])
    rank_quran = next((i for i, r in enumerate(arabic_rows)
                       if r["corpus"] == "quran"), -1) + 1
    print(f"[{EXP}]   Quran rank by p_max (within Arabic incl hadith) = "
          f"{rank_quran} of {len(arabic_rows)}")

    # --- Write outputs ----------------------------------------------------
    common = {
        "experiment": EXP,
        "schema_version": 1,
        "supplement_to": "expP9_v79_batch_diagnostics main run "
                         "(2026-04-26)",
        "frozen_constants": {
            "seed": SEED, "min_verses": MIN_VERSES,
            "all_ctrl": ALL_CTRL,
        },
    }
    with open(out / "N1_supplement.json", "w", encoding="utf-8") as f:
        json.dump({**common, "payload_tag": "N1_supplement",
                   "per_corpus": n1, "summary": summary_n1,
                   "verdict": verdict}, f, ensure_ascii=False,
                  indent=2, allow_nan=True)
    print(f"[{EXP}] wrote {out / 'N1_supplement.json'}")
    with open(out / "NEW2_supplement.json", "w", encoding="utf-8") as f:
        json.dump({**common, "payload_tag": "NEW2_supplement",
                   "per_corpus": new2_rows,
                   "quran_rank_by_p_max": rank_quran,
                   "n_corpora_arabic_incl_hadith": len(arabic_rows)},
                  f, ensure_ascii=False, indent=2, allow_nan=True)
    print(f"[{EXP}] wrote {out / 'NEW2_supplement.json'}")
    print(f"\n[{EXP}] supplement runtime = {round(time.time() - t0, 2)} s")
    self_check_end(pre, exp_name=EXP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
