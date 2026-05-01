"""
expP9_v79_batch_diagnostics/run_audit_patch.py
==============================================
Zero-trust audit patch (2026-04-26 evening).

Findings from the audit of the v7.9-cand sprint code & paper:
  1. N1 supplement was missing hebrew_tanakh + greek_nt (load_all needed
     include_cross_lang=True, which run_supplement.py did not set).
  2. PAPER §4.41.8 claimed "Bible reaches only 14.7 % ن-finals" — that 14.7 %
     is Bible's `ا` (alif) rate. Bible's actual ن rate = 7.53 %.
  3. Brown's joint p in N9 used p_Hurst = 4e-4 ("2/5000 perms"); actual
     Hurst JSON shows p_one_sided = 1.999e-4 (≈ 2/10001, i.e. 10 000 perms).

This patch:
  * Re-runs N1 EL-only AUC for hebrew_tanakh and greek_nt.
  * Computes the correct ن rate for every corpus (NOT the dominant rate).
  * Re-runs Brown synthesis with corrected p_Hurst.

Writes:
  results/experiments/expP9_v79_batch_diagnostics/audit_patch.json
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
NOON = "\u0646"  # ن
ALIF = "\u0627"  # ا


def _verse_final_letter(v: str) -> str | None:
    s = v.strip()
    for c in reversed(s):
        if "\u0621" <= c <= "\u064A":
            return c
    return None


def _gather_units(units, min_v: int = 2):
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
                     "n_verses": nv, "el": el})
    return rows


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


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()
    print(f"[{EXP}] AUDIT PATCH")
    print(f"[{EXP}] loading all corpora (include_cross_lang=True, "
          f"include_cross_tradition=True) ...")
    CORPORA = raw_loader.load_all(include_extras=True,
                                   include_cross_lang=True,
                                   include_cross_tradition=True)
    CORPORA["hadith_bukhari"] = raw_loader.load_hadith_bukhari()
    print(f"[{EXP}] corpora present: {sorted(CORPORA.keys())}")

    # --- Patch #1 + #2: per-corpus actual ن rate + Hebrew/Greek-NT N1 -----
    print(f"\n[{EXP}] === Per-corpus actual ن rate (NOT dominant) ===")
    from collections import Counter
    noon_rates = {}
    for name, units in CORPORA.items():
        finals = []
        for u in units:
            for v in u.verses:
                f = _verse_final_letter(v)
                if f:
                    finals.append(f)
        n = len(finals)
        if n == 0:
            continue
        c = Counter(finals)
        p_n = c.get(NOON, 0) / n
        p_a = c.get(ALIF, 0) / n
        dominant = c.most_common(1)[0]
        noon_rates[name] = {
            "n_verse_finals": n,
            "p_noon": float(p_n),
            "p_alif": float(p_a),
            "dominant_letter": dominant[0],
            "p_dominant": float(dominant[1] / n),
            "is_arabic_script": (
                name in ("quran", "arabic_bible", "hadith_bukhari",
                         "poetry_jahili", "poetry_islami", "poetry_abbasi",
                         "ksucca", "hindawi")),
        }
        print(f"[{EXP}]   {name:18s} n={n:6d}  "
              f"p(ن)={p_n:.4f}  p(ا)={p_a:.4f}  "
              f"dominant={dominant[0]} @ {dominant[1]/n:.4f}")

    # --- Patch #2: Hebrew Tanakh + Greek NT N1 EL-alone AUC ----------------
    print(f"\n[{EXP}] === N1 EL-alone for Hebrew Tanakh + Greek NT (missing) ===")
    q_rows = _gather_units(CORPORA["quran"])
    EL_q = np.array([r["el"] for r in q_rows], dtype=float)
    n1_patch = {}
    for ctrl_name in ["hebrew_tanakh", "greek_nt"]:
        if ctrl_name not in CORPORA:
            n1_patch[ctrl_name] = {"missing": True}
            continue
        ctrl_rows = _gather_units(CORPORA[ctrl_name])
        if len(ctrl_rows) < 5:
            n1_patch[ctrl_name] = {"too_few_units": len(ctrl_rows)}
            continue
        EL_c = np.array([r["el"] for r in ctrl_rows], dtype=float)
        EL_all = np.concatenate([EL_q, EL_c])
        y_all = np.concatenate([np.ones(len(EL_q)), np.zeros(len(EL_c))])
        try:
            fit = _fit_svm_1d_auc(EL_all, y_all)
            n1_patch[ctrl_name] = {
                "n_quran": int(len(EL_q)),
                "n_ctrl": int(len(EL_c)),
                "auc": fit["auc"],
                "w": fit["w"], "b": fit["b"],
                "median_el_quran": float(np.median(EL_q)),
                "median_el_ctrl": float(np.median(EL_c)),
            }
            print(f"[{EXP}]   Quran vs {ctrl_name:16s} n_C={len(EL_c):5d}  "
                  f"AUC = {fit['auc']:.4f}  med(EL_C)={np.median(EL_c):.3f}")
        except Exception as e:
            n1_patch[ctrl_name] = {"error": str(e)}

    # --- Patch #3: Brown synthesis with corrected p_Hurst -----------------
    print(f"\n[{EXP}] === Brown synthesis with corrected p_Hurst = 2e-4 ===")
    from scipy.stats import norm, chi2
    auc_EL = 0.9813
    z_EL = float(np.sqrt(2) * norm.ppf(auc_EL))
    p_EL = float(norm.sf(z_EL))
    p_R3 = float(norm.cdf(-8.92))
    p_J1 = 1e-6
    p_Hurst_orig = 4e-4
    p_Hurst_correct = 2e-4   # actual = 1.9996e-4 = 2/10001 from JSON

    def brown(p_arr, rho=0.5):
        T = float(-2 * np.sum(np.log(p_arr)))
        k = len(p_arr)
        var_T = 4 * k + 8 * (k * (k - 1) / 2) * rho * (3.25 + 0.75 * rho)
        c = var_T / (4 * k)
        df = (4 * k) ** 2 / var_T
        return {
            "chi2_T": T, "c_scale": c, "df_eff": df,
            "p": float(chi2.sf(T / c, df)),
        }

    p_arr_orig = np.array([p_EL, p_R3, p_J1, p_Hurst_orig])
    p_arr_correct = np.array([p_EL, p_R3, p_J1, p_Hurst_correct])
    brown_orig = brown(p_arr_orig)
    brown_correct = brown(p_arr_correct)
    print(f"[{EXP}]   Brown (orig p_Hurst=4e-4): chi2_T={brown_orig['chi2_T']:.2f}  "
          f"p={brown_orig['p']:.3e}  log10p={np.log10(brown_orig['p']):.3f}")
    print(f"[{EXP}]   Brown (corr p_Hurst=2e-4): chi2_T={brown_correct['chi2_T']:.2f}  "
          f"p={brown_correct['p']:.3e}  log10p={np.log10(brown_correct['p']):.3f}")

    # --- Cross-tradition R3 / Hurst headline disclosure --------------------
    cross_tradition_disclosure = {
        "R3_quran_vs_strongest": {
            "quran_z": -8.92,
            "rigveda_z": -18.93,
            "hebrew_tanakh_z": -15.29,
            "greek_nt_z": -12.06,
            "quran_rank_among_oral_liturgical": "4th most extreme (Rigveda > Tanakh > NT > Quran)",
            "note": "The Quran's R3 path-minimality z is real but is not the most extreme; multiple oral-liturgical canons exceed it.",
        },
        "Hurst_quran_vs_others": {
            "quran_p": 1.9996e-4,
            "ties_with": ["hebrew_tanakh", "greek_nt", "rigveda"],
            "note": "All four corpora hit the same p≈2e-4 floor (1 hit in 10000 perms). Hurst H is not Quran-specific.",
        },
    }

    payload = {
        "experiment": EXP,
        "schema_version": 1,
        "payload_tag": "audit_patch",
        "audit_findings": {
            "issue_1_missing_hebrew_greek_NT": (
                "PREREG.md NON_ARABIC lists hebrew_tanakh + greek_nt; the "
                "main run.py used phase_06_phi_m.pkl which only contains "
                "iliad_greek among non-Arabic corpora; the supplement used "
                "load_all(include_cross_lang=False) which also omits these."),
            "issue_2_paper_bible_noon_rate_wrong": (
                "PAPER §4.41.8 said 'Bible reaches only 14.7 % ن-finals'. "
                "14.7 % is Bible's ا (alif) rate, not its ن rate. Bible's "
                "actual ن rate = 7.53 %. Quran-vs-Bible ن-gap is therefore "
                "42.57 pp (not 35.4 pp); the direction makes the verse-end-"
                "selection claim STRONGER not weaker."),
            "issue_3_n9_phurst_off_by_2x": (
                "N9 Brown synthesis used p_Hurst=4e-4 (claimed '2/5000 "
                "perms'). Actual Hurst JSON has p_one_sided=1.9996e-4 = "
                "≈2/10001 (10000 perms). Joint Brown p slightly understated."),
            "issue_4_R3_quran_not_most_extreme": (
                "expP4_cross_tradition_R3 has Rigveda z=-18.93, Tanakh "
                "z=-15.29, Greek NT z=-12.06 all more extreme than Quran "
                "z=-8.92. The Quran is 4th most extreme on R3, not 1st."),
            "issue_5_hadith_post_hoc": (
                "The hadith_bukhari corpus was added post-hoc (not in the "
                "PREREG.md frozen 2026-04-26 morning). Hadith results are "
                "EXPLORATORY, not pre-registered."),
        },
        "patch_1_per_corpus_noon_rate": noon_rates,
        "patch_2_hebrew_greek_nt_n1": n1_patch,
        "patch_3_brown_synthesis": {
            "p_vals_corrected": {
                "EL_full114": p_EL, "R3_canonical_path": p_R3,
                "J1_mushaf_smoothness": p_J1,
                "Hurst_unit_words_corrected": p_Hurst_correct,
            },
            "brown_orig_p_hurst_4e-4": brown_orig,
            "brown_correct_p_hurst_2e-4": brown_correct,
            "log10_p_orig": float(np.log10(brown_orig["p"])),
            "log10_p_correct": float(np.log10(brown_correct["p"])),
        },
        "cross_tradition_disclosure": cross_tradition_disclosure,
        "runtime_seconds": round(time.time() - t0, 2),
    }
    p = out / "audit_patch.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, allow_nan=True)
    print(f"\n[{EXP}] wrote {p}")
    print(f"[{EXP}] runtime = {payload['runtime_seconds']} s")
    self_check_end(pre, exp_name=EXP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
