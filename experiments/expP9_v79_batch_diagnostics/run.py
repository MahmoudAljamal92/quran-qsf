"""
expP9_v79_batch_diagnostics/run.py
==================================
Six pre-registered diagnostics packaged as a single deterministic batch:
  N1 cross-tradition EL-alone test
  N4 per-surah EL boundary-distance ranking
  N6 bag-of-verses null vs per-surah lock-on
  N8 EL stress curve under terminal-letter corruption
  N9 Brown joint-anomaly synthesis on full-114 witnesses
  NEW2 per-corpus dominant-final-letter forensics
  expC1plus_v2 per-surah Sigma-p2 bootstrap

Pre-registered in PREREG.md (frozen 2026-04-26).
"""
from __future__ import annotations

import hashlib
import json
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
from src.features import el_rate, features_5d  # noqa: E402

EXP = "expP9_v79_batch_diagnostics"

SEED = 42
MIN_VERSES = 2
N_BOOT_AUC = 500
N_BOOT_RENYI2 = 10000
N_SIM_BAG = 5000
CORRUPTION_LEVELS = [0.01, 0.05, 0.10, 0.20, 0.50]
ARABIC_ALPHABET = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
EL_BOUNDARY = 0.314
ARABIC_CTRL = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
               "ksucca", "arabic_bible", "hindawi"]
NON_ARABIC = ["hebrew_tanakh", "greek_nt", "iliad_greek",
              "pali_dn", "pali_mn", "rigveda", "avestan_yasna"]
BAND_A = (15, 100)


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _verse_final_letter(v: str) -> str | None:
    """Extract the last Arabic letter of a verse string. Returns None if no
    Arabic letter found."""
    s = v.strip()
    for c in reversed(s):
        if "\u0621" <= c <= "\u064A":  # basic Arabic letters
            return c
    return None


def _surah_pmf(verses: list[str]) -> dict:
    """PMF of verse-final Arabic letters for a single surah."""
    finals = [_verse_final_letter(v) for v in verses]
    finals = [f for f in finals if f is not None]
    n = len(finals)
    if n == 0:
        return {"n": 0, "pmf": {}, "sum_p2": float("nan"),
                "argmax": None, "p_max": float("nan")}
    from collections import Counter
    c = Counter(finals)
    pmf = {k: v / n for k, v in c.items()}
    sum_p2 = float(sum(p * p for p in pmf.values()))
    argmax = max(pmf, key=pmf.get)
    return {"n": n, "pmf": pmf, "sum_p2": sum_p2,
            "argmax": argmax, "p_max": float(pmf[argmax])}


def _fit_svm_1d_auc(EL: np.ndarray, y: np.ndarray, seed: int = SEED) -> dict:
    """Fit a 1-D linear SVM on EL and report AUC on the same data.

    H5 (2026-04-26): returned ``"auc"``/``"accuracy"`` are IN-SAMPLE.
    Explicit honest keys ``"auc_in_sample"`` / ``"accuracy_in_sample"``
    are now also present; legacy keys remain as aliases.
    """
    from sklearn.svm import SVC
    from sklearn.metrics import roc_auc_score, accuracy_score
    X = EL.reshape(-1, 1)
    svm = SVC(kernel="linear", C=1.0, class_weight="balanced",
              random_state=seed)
    svm.fit(X, y)
    dec = svm.decision_function(X)
    auc_is = float(roc_auc_score(y, dec))
    acc_is = float(accuracy_score(y, svm.predict(X)))
    return {
        # H5: explicit honest labels + legacy aliases.
        "auc_in_sample": auc_is,
        "accuracy_in_sample": acc_is,
        "auc": auc_is,
        "accuracy": acc_is,
        "w": float(svm.coef_[0][0]),
        "b": float(svm.intercept_[0]),
    }


def _bootstrap_auc_1d(EL_q: np.ndarray, EL_c: np.ndarray,
                      n_boot: int = N_BOOT_AUC, seed: int = SEED) -> dict:
    """Bootstrap CI on the IN-SAMPLE AUC of the 1-D EL classifier. Each
    replicate fits on the bootstrap-resampled (EL_b, y_b) and scores
    AUC on the SAME (EL_b, y_b). H5: this is a CI on training-fit AUC,
    not on out-of-sample generalisation."""
    from sklearn.svm import SVC
    from sklearn.metrics import roc_auc_score
    rng = np.random.RandomState(seed)
    aucs: list[float] = []
    nq, nc = len(EL_q), len(EL_c)
    for _ in range(n_boot):
        iq = rng.choice(nq, nq, replace=True)
        ic = rng.choice(nc, nc, replace=True)
        EL_b = np.concatenate([EL_q[iq], EL_c[ic]]).reshape(-1, 1)
        y_b = np.concatenate([np.ones(nq), np.zeros(nc)])
        try:
            svm = SVC(kernel="linear", C=1.0, class_weight="balanced",
                      random_state=seed)
            svm.fit(EL_b, y_b)
            aucs.append(float(roc_auc_score(y_b, svm.decision_function(EL_b))))
        except Exception:
            pass
    if not aucs:
        return {"median": None, "ci_lo": None, "ci_hi": None}
    arr = np.asarray(aucs)
    return {"median": float(np.median(arr)),
            "ci_lo": float(np.percentile(arr, 2.5)),
            "ci_hi": float(np.percentile(arr, 97.5))}


def _gather_units(CORPORA: dict, names: list[str], min_v: int = MIN_VERSES):
    rows = []
    for name in names:
        for u in CORPORA.get(name, []):
            nv = len(u.verses)
            if nv < min_v:
                continue
            try:
                el = float(el_rate(list(u.verses)))
            except Exception:
                continue
            rows.append({
                "corpus": name, "label": getattr(u, "label", ""),
                "n_verses": nv, "el": el,
            })
    return rows


# --- Sub-test N1: cross-tradition EL-alone --------------------------------
def run_N1(CORPORA: dict, q_rows: list[dict]) -> dict:
    print(f"\n[{EXP}] === N1 cross-tradition EL-alone ===")
    EL_q = np.array([r["el"] for r in q_rows], dtype=float)
    results = {}
    for ctrl_name in ARABIC_CTRL + NON_ARABIC:
        ctrl_rows = _gather_units(CORPORA, [ctrl_name])
        if len(ctrl_rows) < 5:
            results[ctrl_name] = {"skipped": "too few units",
                                  "n_ctrl": len(ctrl_rows)}
            continue
        EL_c = np.array([r["el"] for r in ctrl_rows], dtype=float)
        EL_all = np.concatenate([EL_q, EL_c])
        y_all = np.concatenate([np.ones(len(EL_q)), np.zeros(len(EL_c))])
        fit = _fit_svm_1d_auc(EL_all, y_all)
        ci = _bootstrap_auc_1d(EL_q, EL_c)
        results[ctrl_name] = {
            "n_quran": len(EL_q), "n_ctrl": len(EL_c),
            "auc": fit["auc"], "accuracy": fit["accuracy"],
            "w": fit["w"], "b": fit["b"],
            "median_el_quran": float(np.median(EL_q)),
            "median_el_ctrl": float(np.median(EL_c)),
            "bootstrap_ci": ci,
        }
        print(f"[{EXP}]   Quran vs {ctrl_name:18s} n_C={len(EL_c):4d}  "
              f"AUC = {fit['auc']:.4f}  med(EL_Q)={np.median(EL_q):.3f}  "
              f"med(EL_C)={np.median(EL_c):.3f}")
    aucs_arabic = [results[k]["auc"] for k in ARABIC_CTRL
                   if "auc" in results.get(k, {})]
    aucs_nonarabic = [results[k]["auc"] for k in NON_ARABIC
                      if "auc" in results.get(k, {})]
    min_arabic = min(aucs_arabic) if aucs_arabic else float("nan")
    min_nonarabic = min(aucs_nonarabic) if aucs_nonarabic else float("nan")
    if min_arabic >= 0.95 and min_nonarabic >= 0.95:
        verdict = "PASS_quran_specific_cross_script"
    elif min_arabic >= 0.95 and min_nonarabic < 0.95:
        verdict = "PASS_arabic_only"
    else:
        verdict = "FAIL_class_property"
    print(f"[{EXP}]   min AUC vs Arabic ctrl     = {min_arabic:.4f}")
    print(f"[{EXP}]   min AUC vs non-Arabic ctrl = {min_nonarabic:.4f}")
    print(f"[{EXP}]   verdict = {verdict}")
    return {
        "per_corpus": results,
        "aggregate": {
            "min_auc_arabic": min_arabic,
            "min_auc_nonarabic": min_nonarabic,
            "n_corpora_arabic": len(aucs_arabic),
            "n_corpora_nonarabic": len(aucs_nonarabic),
        },
        "verdict": verdict,
    }


# --- Sub-test N4: per-surah EL boundary-distance ranking ------------------
def run_N4(q_rows: list[dict]) -> dict:
    print(f"\n[{EXP}] === N4 per-surah EL boundary-distance ranking ===")
    ranked = sorted(q_rows, key=lambda r: r["el"] - EL_BOUNDARY)
    table = [{
        "rank": i + 1,
        "label": r["label"], "n_verses": r["n_verses"],
        "el": r["el"], "delta_to_boundary": r["el"] - EL_BOUNDARY,
        "above_boundary": bool(r["el"] >= EL_BOUNDARY),
    } for i, r in enumerate(ranked)]
    n_above = sum(1 for r in table if r["above_boundary"])
    n_below = len(table) - n_above
    print(f"[{EXP}]   n_above_boundary = {n_above} / {len(table)}; "
          f"n_below = {n_below}")
    print(f"[{EXP}]   5 closest to boundary:")
    closest = sorted(table, key=lambda r: abs(r["delta_to_boundary"]))[:5]
    for r in closest:
        print(f"[{EXP}]     surah {r['label']:8s} n={r['n_verses']:4d}  "
              f"EL={r['el']:.3f}  Δ={r['delta_to_boundary']:+.3f}  "
              f"{'above' if r['above_boundary'] else 'BELOW'}")
    return {
        "boundary": EL_BOUNDARY,
        "n_above": n_above,
        "n_below": n_below,
        "ranking": table,
        "closest_to_boundary_top5": closest,
    }


# --- Sub-test N6: bag-of-verses null --------------------------------------
def run_N6(CORPORA: dict, q_units: list, seed: int = SEED) -> dict:
    print(f"\n[{EXP}] === N6 bag-of-verses null (per-surah lock-on test) ===")
    # Build corpus-pool PMF over all Quran verse-finals
    all_finals: list[str] = []
    for u in q_units:
        for v in u.verses:
            f = _verse_final_letter(v)
            if f is not None:
                all_finals.append(f)
    from collections import Counter
    c = Counter(all_finals)
    n_pool = sum(c.values())
    letters = sorted(c.keys())
    pool_p = np.array([c[l] / n_pool for l in letters], dtype=float)
    rng = np.random.RandomState(seed)
    per_surah = []
    n_pass = 0
    for u in q_units:
        nv = len(u.verses)
        finals = [_verse_final_letter(v) for v in u.verses]
        finals = [f for f in finals if f is not None]
        if len(finals) < 2:
            continue
        # Observed EL: max-frequency-final / total
        obs_pmf = Counter(finals)
        obs_p_max = max(obs_pmf.values()) / len(finals)
        # Null distribution: sample n=len(finals) from pool PMF, compute
        # max-frequency / n
        sims = rng.choice(len(letters), size=(N_SIM_BAG, len(finals)),
                          replace=True, p=pool_p)
        null_p_max = []
        for row in sims:
            counts = np.bincount(row, minlength=len(letters))
            null_p_max.append(counts.max() / len(finals))
        null_p_max = np.asarray(null_p_max)
        p_one_sided = float((null_p_max >= obs_p_max).mean())
        per_surah.append({
            "label": getattr(u, "label", ""),
            "n_verses": len(finals),
            "obs_p_max_final": float(obs_p_max),
            "obs_dominant_final": max(obs_pmf, key=obs_pmf.get),
            "null_p_max_mean": float(null_p_max.mean()),
            "null_p_max_p99": float(np.percentile(null_p_max, 99)),
            "p_one_sided_obs_geq_null": p_one_sided,
            "exceeds_null_99pct": bool(obs_p_max > np.percentile(null_p_max, 99)),
        })
        if obs_p_max > np.percentile(null_p_max, 99):
            n_pass += 1
    n_total = len(per_surah)
    pct = (n_pass / n_total * 100) if n_total else 0.0
    if pct >= 95.0:
        verdict = "PASS_per_surah_lock_on"
    elif pct >= 50.0:
        verdict = "PARTIAL_lock_on"
    else:
        verdict = "FAIL_consistent_with_pool_iid"
    print(f"[{EXP}]   n_surahs_tested = {n_total}")
    print(f"[{EXP}]   pct exceeding 99th-pctile of iid-pool null = {pct:.1f} %")
    print(f"[{EXP}]   verdict = {verdict}")
    return {
        "n_surahs_tested": n_total,
        "n_exceeds_null_99pct": n_pass,
        "pct_exceeds_null_99pct": pct,
        "pool_pmf_top5": dict(sorted(
            {l: pool_p[i] for i, l in enumerate(letters)}.items(),
            key=lambda kv: -kv[1])[:5]),
        "n_sim_per_surah": N_SIM_BAG,
        "per_surah_sample_top5_lowest_p": sorted(
            per_surah, key=lambda r: -r["p_one_sided_obs_geq_null"])[:5],
        "verdict": verdict,
    }


# --- Sub-test N8: EL stress curve -----------------------------------------
def run_N8(CORPORA: dict, seed: int = SEED) -> dict:
    print(f"\n[{EXP}] === N8 EL stress curve under terminal-letter corruption ===")
    rng = np.random.RandomState(seed)
    q_units = CORPORA.get("quran", [])
    band_a_q = [u for u in q_units if BAND_A[0] <= len(u.verses) <= BAND_A[1]]
    print(f"[{EXP}]   band-A Quran units: {len(band_a_q)}")

    # Pre-extract per-verse final positions for fast corruption.
    def corrupt_el(verses: list[str], frac: float) -> float:
        finals = []
        for v in verses:
            f = _verse_final_letter(v)
            finals.append(f if f is not None else "ا")
        n = len(finals)
        n_corrupt = int(round(frac * n))
        idx = rng.choice(n, size=n_corrupt, replace=False) if n_corrupt > 0 else []
        for i in idx:
            finals[i] = ARABIC_ALPHABET[rng.randint(28)]
        from collections import Counter
        c = Counter(finals)
        return max(c.values()) / n

    # Baseline AUC at f = 0
    EL_q0 = np.array([float(el_rate(list(u.verses))) for u in band_a_q])
    ctrl_rows = _gather_units(CORPORA, ARABIC_CTRL)
    ctrl_band_a = [r for r in ctrl_rows
                   if BAND_A[0] <= r["n_verses"] <= BAND_A[1]]
    EL_c = np.array([r["el"] for r in ctrl_band_a])
    EL_all0 = np.concatenate([EL_q0, EL_c])
    y_all = np.concatenate([np.ones(len(EL_q0)), np.zeros(len(EL_c))])
    fit0 = _fit_svm_1d_auc(EL_all0, y_all)

    rows = [{"f": 0.0, "auc": fit0["auc"], "n_q": int(len(EL_q0)),
             "n_c": int(len(EL_c)),
             "median_el_q": float(np.median(EL_q0))}]
    print(f"[{EXP}]   f = 0.000  AUC = {fit0['auc']:.4f}  med(EL_Q) = "
          f"{np.median(EL_q0):.3f}")
    for f in CORRUPTION_LEVELS:
        EL_qf = np.array([corrupt_el(list(u.verses), f) for u in band_a_q])
        EL_allf = np.concatenate([EL_qf, EL_c])
        fit = _fit_svm_1d_auc(EL_allf, y_all)
        rows.append({"f": f, "auc": fit["auc"], "n_q": int(len(EL_qf)),
                     "n_c": int(len(EL_c)),
                     "median_el_q": float(np.median(EL_qf))})
        print(f"[{EXP}]   f = {f:.3f}  AUC = {fit['auc']:.4f}  med(EL_Q) = "
              f"{np.median(EL_qf):.3f}")

    # Find max f such that AUC >= 0.95
    f_robust = 0.0
    for r in rows:
        if r["auc"] >= 0.95:
            f_robust = max(f_robust, r["f"])
    return {
        "stress_curve": rows,
        "f_max_at_AUC_95": f_robust,
        "n_band_a_quran": int(len(band_a_q)),
        "n_band_a_ctrl": int(len(EL_c)),
    }


# --- Sub-test N9: Brown joint-anomaly synthesis ---------------------------
def run_N9() -> dict:
    print(f"\n[{EXP}] === N9 Brown joint-anomaly synthesis ===")
    # Source p-values from existing locked / v7.9-cand JSONs.
    # AUC -> z via: z = sqrt(2) * Phi^-1(AUC) approx (Hanley-McNeil).
    from scipy.stats import norm, chi2

    p_vals = {}
    notes = {}

    # p_EL: from exp104 overall AUC = 0.9813
    auc_EL = 0.9813
    z_EL = float(np.sqrt(2) * norm.ppf(auc_EL))
    p_EL = float(norm.sf(z_EL))
    p_vals["EL_full114"] = p_EL
    notes["EL_full114"] = (f"exp104 overall AUC={auc_EL}, Hanley-McNeil "
                            f"z={z_EL:.3f}")

    # p_R3: expP4_cross_tradition_R3 Quran z = -8.92 (one-sided minimisation)
    z_R3 = -8.92
    p_R3 = float(norm.cdf(z_R3))
    p_vals["R3_canonical_path"] = p_R3
    notes["R3_canonical_path"] = "expP4 z=-8.92, one-sided lower"

    # p_J1: mushaf-J1 smoothness; locked at 1e-6 floor (perm-1M)
    p_vals["J1_mushaf_smoothness"] = 1e-6
    notes["J1_mushaf_smoothness"] = ("expE17b 1M perms, p_one_sided "
                                      "<= 1/(1e6+1)")

    # p_Hurst: expP4_quran_hurst_forensics H=0.914 perm-p = 0.0002 (2 / 5000)
    p_vals["Hurst_unit_words"] = 4e-4
    notes["Hurst_unit_words"] = "expP4 H=0.914, perm-null 2/5000"

    p_arr = np.array(list(p_vals.values()))
    keys = list(p_vals.keys())

    # Stouffer (assuming independence)
    z_stouffer = float(np.sum([norm.ppf(1 - p) for p in p_arr]) /
                        np.sqrt(len(p_arr)))
    p_stouffer = float(norm.sf(z_stouffer))

    # Brown's method assumes correlation among the p-values' chi2(2)
    # transforms. Without corpus-internal correlation matrix at hand, we use
    # a CONSERVATIVE rho = 0.5 prior between all pairs (arXiv:0710.5468).
    # Brown's chi2: T = -2 * sum log(p), distributed approximately as
    # c * chi2(2k') where c, k' adjust for correlation.
    rho = 0.5
    k = len(p_arr)
    T = float(-2 * np.sum(np.log(p_arr)))
    # Empirical Brown approximation (Kost & McDermott 2002)
    var_T = 4 * k + 8 * (k * (k - 1) / 2) * rho * (3.25 + 0.75 * rho)
    c = var_T / (4 * k)
    df = (4 * k) ** 2 / var_T
    p_brown = float(chi2.sf(T / c, df))
    log10p_brown = float(np.log10(p_brown)) if p_brown > 0 else None

    print(f"[{EXP}]   per-channel p-values:")
    for k_, p_ in p_vals.items():
        print(f"[{EXP}]     {k_:24s} p = {p_:.3e}")
    print(f"[{EXP}]   Stouffer z = {z_stouffer:.2f}, p = {p_stouffer:.3e}")
    print(f"[{EXP}]   Brown (rho={rho}) chi2 T = {T:.2f}, df={df:.2f}, "
          f"p = {p_brown:.3e}  (log10 p = {log10p_brown})")

    return {
        "p_vals_per_channel": p_vals,
        "channel_notes": notes,
        "stouffer": {"z": z_stouffer, "p": p_stouffer},
        "brown": {
            "rho_assumed": rho, "chi2_T": T, "df_eff": df, "c_scale": c,
            "p": p_brown, "log10_p": log10p_brown,
        },
        "notes": ("Brown rho=0.5 is a conservative correlation prior; tighter "
                   "than Stouffer's rho=0 but looser than the within-Arabic "
                   "empirical corr matrix would give. Replace once the 5-D "
                   "feature corr matrix is estimated on controls."),
    }


# --- Sub-test NEW2: per-corpus dominant-final-letter forensics -----------
def run_NEW2(CORPORA: dict) -> dict:
    print(f"\n[{EXP}] === NEW2 per-corpus dominant-final-letter forensics ===")
    rows = []
    for name in ["quran"] + ARABIC_CTRL + NON_ARABIC:
        units = CORPORA.get(name, [])
        all_finals = []
        for u in units:
            for v in u.verses:
                f = _verse_final_letter(v)
                if f is not None:
                    all_finals.append(f)
        if not all_finals:
            # Try non-Arabic corpus: reuse last char if not Arabic
            for u in units:
                for v in u.verses:
                    s = v.strip()
                    if s:
                        all_finals.append(s[-1])
        from collections import Counter
        c = Counter(all_finals)
        n = sum(c.values())
        if n == 0:
            rows.append({"corpus": name, "n": 0, "skipped": True})
            continue
        pmf = {k: v / n for k, v in c.items()}
        sum_p2 = float(sum(p * p for p in pmf.values()))
        argmax = max(pmf, key=pmf.get)
        rows.append({
            "corpus": name,
            "n_verse_finals": n,
            "alphabet_size": len(pmf),
            "dominant_final": argmax,
            "p_max": float(pmf[argmax]),
            "p_max_sq_lower_bound_pair_collision": float(pmf[argmax] ** 2),
            "sum_p2": sum_p2,
            "renyi2_bits": float(-np.log2(sum_p2)) if sum_p2 > 0 else None,
            "is_arabic": name in (["quran"] + ARABIC_CTRL),
        })
        print(f"[{EXP}]   {name:18s} n={n:7d}  dominant='{argmax}'  "
              f"p_max={pmf[argmax]:.4f}  Σp²={sum_p2:.4f}")
    # Within-Arabic ranking by p_max
    arabic_rows = [r for r in rows if r.get("is_arabic")
                   and not r.get("skipped")]
    arabic_rows.sort(key=lambda r: -r["p_max"])
    rank_quran_arabic = next((i for i, r in enumerate(arabic_rows)
                              if r["corpus"] == "quran"), -1) + 1
    return {
        "per_corpus": rows,
        "quran_arabic_rank_by_p_max": rank_quran_arabic,
        "n_arabic_corpora": len(arabic_rows),
    }


# --- Sub-test expC1plus_v2: per-surah Σp² bootstrap ----------------------
def run_C1plus_v2(q_units: list, seed: int = SEED) -> dict:
    print(f"\n[{EXP}] === expC1plus_v2 per-surah Σp² ≈ 0.5 bootstrap ===")
    rng = np.random.RandomState(seed)
    band_a = [u for u in q_units
              if BAND_A[0] <= len(u.verses) <= BAND_A[1]]
    sums = []
    for u in band_a:
        d = _surah_pmf(list(u.verses))
        if d["n"] >= 2 and np.isfinite(d["sum_p2"]):
            sums.append(d["sum_p2"])
    sums = np.asarray(sums, dtype=float)
    n = len(sums)
    print(f"[{EXP}]   band-A surahs analysed: {n}  mean Σp² = "
          f"{sums.mean():.4f}  median = {np.median(sums):.4f}")
    # Bootstrap median CI
    boots = []
    for _ in range(N_BOOT_RENYI2):
        idx = rng.choice(n, n, replace=True)
        boots.append(np.median(sums[idx]))
    boots = np.asarray(boots)
    ci_lo = float(np.percentile(boots, 2.5))
    ci_hi = float(np.percentile(boots, 97.5))
    median_obs = float(np.median(sums))
    half_in_ci = ci_lo <= 0.5 <= ci_hi
    sqrt_mean = float(np.sqrt(sums.mean()))
    print(f"[{EXP}]   95 % bootstrap CI for median = [{ci_lo:.4f}, {ci_hi:.4f}]")
    print(f"[{EXP}]   0.5 in CI? {half_in_ci}")
    print(f"[{EXP}]   √mean Σp² = {sqrt_mean:.4f}  (1/√2 = "
          f"{1/np.sqrt(2):.4f})")
    return {
        "n_band_a_surahs": int(n),
        "mean_sum_p2": float(sums.mean()),
        "median_sum_p2_observed": median_obs,
        "median_bootstrap_ci_95": [ci_lo, ci_hi],
        "half_in_median_ci_95": bool(half_in_ci),
        "sqrt_mean_sum_p2": sqrt_mean,
        "one_over_sqrt_2": float(1/np.sqrt(2)),
        "gap_to_one_over_sqrt_2": float(abs(sqrt_mean - 1/np.sqrt(2))),
        "verdict": "PASS_at_half" if half_in_ci else (
            "PARTIAL_near_half" if abs(median_obs - 0.5) < 0.1
            else "FAIL_not_half"),
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
    print(f"[{EXP}] v7.9-cand batched diagnostics: N1+N4+N6+N8+N9+NEW2+C1plus_v2")
    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    q_units = CORPORA.get("quran", [])
    q_rows = _gather_units(CORPORA, ["quran"])
    print(f"[{EXP}] Quran units loaded: {len(q_rows)}")

    res_N1 = run_N1(CORPORA, q_rows)
    res_N4 = run_N4(q_rows)
    res_N6 = run_N6(CORPORA, q_units)
    res_N8 = run_N8(CORPORA)
    res_N9 = run_N9()
    res_NEW2 = run_NEW2(CORPORA)
    res_C1plus_v2 = run_C1plus_v2(q_units)

    common = {
        "experiment": EXP,
        "schema_version": 1,
        "prereg_document": "experiments/expP9_v79_batch_diagnostics/PREREG.md",
        "prereg_hash": _prereg_hash(),
        "frozen_constants": {
            "seed": SEED, "min_verses": MIN_VERSES,
            "n_boot_auc": N_BOOT_AUC,
            "n_boot_renyi2": N_BOOT_RENYI2,
            "n_sim_bag": N_SIM_BAG,
            "corruption_levels": CORRUPTION_LEVELS,
            "el_boundary": EL_BOUNDARY,
            "arabic_ctrl": ARABIC_CTRL, "non_arabic": NON_ARABIC,
            "band_a": list(BAND_A),
        },
    }

    for tag, payload in [
        ("N1_cross_tradition_el", res_N1),
        ("N4_boundary_distance", res_N4),
        ("N6_bag_of_verses_null", res_N6),
        ("N8_stress_curve", res_N8),
        ("N9_brown_synthesis", res_N9),
        ("NEW2_dominant_final_forensics", res_NEW2),
        ("expC1plus_v2_per_surah", res_C1plus_v2),
    ]:
        full = {**common, "payload_tag": tag, **payload}
        path = out / f"{tag}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(full, f, ensure_ascii=False, indent=2, allow_nan=True)
        print(f"[{EXP}] wrote {path}")

    summary = {
        **common,
        "summary": {
            "N1_verdict": res_N1.get("verdict"),
            "N1_min_auc_arabic": res_N1["aggregate"]["min_auc_arabic"],
            "N1_min_auc_nonarabic": res_N1["aggregate"]["min_auc_nonarabic"],
            "N4_n_above": res_N4["n_above"],
            "N4_n_below": res_N4["n_below"],
            "N6_pct_lock_on": res_N6["pct_exceeds_null_99pct"],
            "N6_verdict": res_N6["verdict"],
            "N8_f_max_at_AUC_95": res_N8["f_max_at_AUC_95"],
            "N9_brown_log10_p": res_N9["brown"]["log10_p"],
            "NEW2_quran_arabic_rank_by_p_max": res_NEW2["quran_arabic_rank_by_p_max"],
            "C1plus_v2_verdict": res_C1plus_v2["verdict"],
        },
        "runtime_seconds": round(time.time() - t0, 2),
    }
    with open(out / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, allow_nan=True)
    print(f"\n[{EXP}] summary written; total runtime = "
          f"{summary['runtime_seconds']} s")
    self_check_end(pre, exp_name=EXP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
