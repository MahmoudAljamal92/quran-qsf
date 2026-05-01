"""
exp94_adiyat_864/run.py
========================
Unified Stack Law on the canonical Adiyat 864-variant enumeration.

Tests whether a single closed-form formula (logistic stack or Fisher
chi^2_6 combiner) achieves recall >= 99.0% on all 864 single-letter
substitutions of Surah 100 verse 1, at the exp41 ctrl-p95 threshold.

Enumeration byte-equal to exp43_adiyat_864_compound.
Perturbation policy byte-equal to exp41_gzip_formalised._apply_perturbation.

Pre-registered verdicts (evaluated in order; see PREREG.md):
    FAIL_sanity_R12_replication  recall(R12-only, 864) < 0.98
    FAIL_n_variants              |variants| != 864
    PASS_unified_99              max(recall_logistic, recall_Fisher) >= 0.99
    PARTIAL_below_99_above_R12   max unified >= R12 but < 0.99
    FAIL_unified_below_R12       best unified < R12 - 0.005

Reads (integrity-checked):
    phase_06_phi_m.pkl                                state['CORPORA']
    results/experiments/exp93_unified_stack/exp93_unified_stack.json
    results/experiments/exp41_gzip_formalised/exp41_gzip_formalised.json

Writes ONLY under results/experiments/exp94_adiyat_864/
"""
from __future__ import annotations

import gzip
import json
import math
import random
import sys
import time
from pathlib import Path

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
from src import features as ft  # noqa: E402

EXP = "exp94_adiyat_864"

# --- Frozen constants (mirror PREREG §8) -----------------------------------
SEED = 42
N_PERT_PER_UNIT = 20
CTRL_N_UNITS = 200
GZIP_LEVEL = 9
FPR_TARGET = 0.05
W_T, W_EL, B_TEL = 0.5329, 4.1790, -1.5221
BAND_A_LO, BAND_A_HI = 15, 100
ADIYAT_LABEL = "Q:100"
EXPECTED_N_VARIANTS = 864
RECALL_GATE = 0.99
SANITY_R12_MIN_RECALL = 0.98

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ALPH_IDX = {c: i for i, c in enumerate(ARABIC_CONS_28)}
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

# features_5d returns (EL, VL_CV, CN, H_cond, T)
_FV_ORDER = ["EL", "VL_CV", "CN", "H_cond", "T"]


# --- Primitives (byte-equal to exp41 / exp43) ------------------------------
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
    za, zb = _gz_len(a), _gz_len(b)
    zab = _gz_len(a + b)
    denom = max(1, max(za, zb))
    return (zab - min(za, zb)) / denom


def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


def _L_TEL_from_f5(f5):
    el = float(f5[_FV_ORDER.index("EL")])
    t = float(f5[_FV_ORDER.index("T")])
    return W_T * t + W_EL * el + B_TEL


# --- Perturbation (byte-equal to exp41) ------------------------------------
def _apply_perturbation(verses, rng: random.Random):
    nv = len(verses)
    if nv < 5:
        return None
    vi_choices = list(range(1, nv - 1))
    rng.shuffle(vi_choices)
    cons = list(ARABIC_CONS_28)
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
            candidates = [c for c in cons if c != original]
            if not candidates:
                continue
            repl = rng.choice(candidates)
            new_word = w[:pos] + repl + w[pos + 1:]
            new_toks = list(toks); new_toks[wi] = new_word
            new_verses = list(verses); new_verses[vi] = " ".join(new_toks)
            return new_verses, vi
    return None


# --- Canonical 864 enumeration (byte-equal to exp43) -----------------------
def _enumerate_864(v1: str) -> list[dict]:
    """Return list of (pos, orig, repl, new_v1) for every (pos, repl != orig)
    where v1[pos] is in ARABIC_CONS_28."""
    out = []
    for pos, ch in enumerate(v1):
        if ch not in ARABIC_CONS_28:
            continue
        for repl in ARABIC_CONS_28:
            if repl == ch:
                continue
            new_v1 = v1[:pos] + repl + v1[pos + 1:]
            out.append({"pos": pos, "orig": ch, "repl": repl, "new_v1": new_v1})
    return out


# --- Stats helpers ---------------------------------------------------------
def _z_score(arr, mu, sd):
    if sd <= 0:
        return np.zeros_like(arr, dtype=float)
    return (np.asarray(arr, dtype=float) - mu) / sd


def _empirical_upper_p(scores, null_scores) -> np.ndarray:
    """p = P(null >= score), right-tail empirical p-value."""
    null = np.sort(np.asarray(null_scores, dtype=float))
    s = np.asarray(scores, dtype=float)
    idx = np.searchsorted(null, s, side="left")
    p = (len(null) - idx + 1) / (len(null) + 1)
    return np.clip(p, 1e-12, 1.0)


def _fisher_chi2_p(p1, p2, p3) -> tuple[np.ndarray, np.ndarray]:
    eps = 1e-12
    x2 = -2.0 * (np.log(np.clip(p1, eps, 1.0))
                 + np.log(np.clip(p2, eps, 1.0))
                 + np.log(np.clip(p3, eps, 1.0)))
    p = 1.0 - stats.chi2.cdf(x2, df=6)
    return x2, p


# --- Load exp93 Stage 2 coefficients ---------------------------------------
def _load_exp93_stage2_coefs() -> dict:
    path = _ROOT / "results" / "experiments" / "exp93_unified_stack" \
        / "exp93_unified_stack.json"
    if not path.exists():
        raise FileNotFoundError(f"exp93 receipt missing: {path}")
    with open(path, "r", encoding="utf-8") as f:
        j = json.load(f)
    folds = j["stage2_edit_detection"]["logistic_stack"]["fold_coefficients"]
    w_dL = float(np.mean([f["w_absdL"] for f in folds]))
    w_NCD = float(np.mean([f["w_NCDedit"] for f in folds]))
    w_dPhi = float(np.mean([f["w_absdPhi"] for f in folds]))
    b = float(np.mean([f["b"] for f in folds]))
    return {"w_dL": w_dL, "w_NCD": w_NCD, "w_dPhi": w_dPhi, "b": b}


# --- Per-variant feature computation ---------------------------------------
def _triple_vs_canon(canon_verses, var_verses, canon_phi, canon_L):
    try:
        var_phi = ft.features_5d(var_verses)
    except Exception:
        return None
    var_L = _L_TEL_from_f5(var_phi)
    dL = var_L - canon_L
    ncd_edit = _ncd(_letters_28(" ".join(canon_verses)),
                    _letters_28(" ".join(var_verses)))
    dPhi = float(np.linalg.norm(np.asarray(var_phi, dtype=float)
                                - np.asarray(canon_phi, dtype=float)))
    return float(dL), float(ncd_edit), float(dPhi)


# --- Main ------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] H30b — Unified Stack Law on canonical Adiyat 864")
    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    CORPORA = state["CORPORA"]

    # --- Locate Surah 100 canonical ---
    adiyat = next((u for u in CORPORA.get("quran", [])
                   if getattr(u, "label", "") == ADIYAT_LABEL), None)
    if adiyat is None:
        raise RuntimeError(f"{ADIYAT_LABEL} not found in CORPORA['quran']")
    canon_verses = list(adiyat.verses)
    v1 = canon_verses[0]

    canon_phi = ft.features_5d(canon_verses)
    canon_L = _L_TEL_from_f5(canon_phi)
    print(f"[{EXP}] Canonical Q:100 v1 has len={len(v1)} chars")
    print(f"[{EXP}] Canonical L_TEL={canon_L:.4f}")

    # --- Step 1: null calibration on 4000 ctrl perturbations ---
    print(f"[{EXP}] Step 1: 4000 ctrl-edit null calibration ...")
    ctrl_pool: list = []
    for name in ARABIC_CTRL:
        ctrl_pool.extend(_band_a(CORPORA.get(name, [])))
    rng_pool = random.Random(SEED + 1)
    rng_pool.shuffle(ctrl_pool)
    ctrl_units = ctrl_pool[:CTRL_N_UNITS]
    rng_c = random.Random(SEED + 2)

    null_dL, null_NCD, null_dPhi = [], [], []
    for u in ctrl_units:
        rng_u = random.Random(rng_c.randrange(1 << 30))
        try:
            u_phi = ft.features_5d(u.verses)
        except Exception:
            continue
        u_L = _L_TEL_from_f5(u_phi)
        for _ in range(N_PERT_PER_UNIT):
            pair = _apply_perturbation(u.verses, rng_u)
            if pair is None:
                continue
            pert_verses, _vi = pair
            tr = _triple_vs_canon(u.verses, pert_verses, u_phi, u_L)
            if tr is None:
                continue
            dL, nc, dp = tr
            null_dL.append(abs(dL))
            null_NCD.append(nc)
            null_dPhi.append(abs(dp))
    n_null = len(null_NCD)
    print(f"[{EXP}] Null built: n={n_null} ctrl-edits; dt={time.time()-t0:.1f}s")

    null_dL = np.asarray(null_dL, dtype=float)
    null_NCD = np.asarray(null_NCD, dtype=float)
    null_dPhi = np.asarray(null_dPhi, dtype=float)

    # Null stats for z-scoring (used by logistic + naive)
    mu_null = {
        "dL": float(null_dL.mean()),
        "NCD": float(null_NCD.mean()),
        "dPhi": float(null_dPhi.mean()),
    }
    sd_null = {
        "dL": float(null_dL.std(ddof=1)) or 1.0,
        "NCD": float(null_NCD.std(ddof=1)) or 1.0,
        "dPhi": float(null_dPhi.std(ddof=1)) or 1.0,
    }

    # --- Step 2: enumerate 864 Adiyat variants ---
    print(f"[{EXP}] Step 2: enumerating Adiyat 864 variants ...")
    v1_variants = _enumerate_864(v1)
    n_var = len(v1_variants)
    print(f"[{EXP}] Enumerated {n_var} variants  "
          f"(expected {EXPECTED_N_VARIANTS})")

    adiyat_dL, adiyat_NCD, adiyat_dPhi = [], [], []
    adiyat_rows = []
    t1 = time.time()
    for vv in v1_variants:
        var_verses = [vv["new_v1"]] + list(canon_verses[1:])
        tr = _triple_vs_canon(canon_verses, var_verses, canon_phi, canon_L)
        if tr is None:
            continue
        dL, nc, dp = tr
        adiyat_dL.append(abs(dL))
        adiyat_NCD.append(nc)
        adiyat_dPhi.append(abs(dp))
        adiyat_rows.append({
            "pos": vv["pos"], "orig": vv["orig"], "repl": vv["repl"],
            "dL": round(dL, 6), "NCD_edit": round(nc, 6),
            "dPhi": round(dp, 6),
        })
    adiyat_dL = np.asarray(adiyat_dL, dtype=float)
    adiyat_NCD = np.asarray(adiyat_NCD, dtype=float)
    adiyat_dPhi = np.asarray(adiyat_dPhi, dtype=float)
    n_adiyat = len(adiyat_NCD)
    print(f"[{EXP}] 864 variants scored; dt={time.time()-t1:.1f}s  "
          f"(n_completed={n_adiyat})")

    # --- Step 3: per-formula thresholds and recalls ---
    print(f"[{EXP}] Step 3: per-formula thresholds and recalls ...")
    # Formula baseline R12 (single-layer, the published 99.1% claim)
    thr_R12 = float(np.quantile(null_NCD, 1 - FPR_TARGET))
    recall_R12 = float((adiyat_NCD >= thr_R12).mean())

    # Unified formula A — logistic stack (frozen from exp93 Stage 2)
    coefs = _load_exp93_stage2_coefs()
    def _logit_stack(dL_arr, NCD_arr, dPhi_arr):
        zdL = _z_score(dL_arr, mu_null["dL"], sd_null["dL"])
        zNCD = _z_score(NCD_arr, mu_null["NCD"], sd_null["NCD"])
        zdPhi = _z_score(dPhi_arr, mu_null["dPhi"], sd_null["dPhi"])
        lin = (coefs["b"] + coefs["w_dL"] * zdL + coefs["w_NCD"] * zNCD
               + coefs["w_dPhi"] * zdPhi)
        return 1.0 / (1.0 + np.exp(-lin))

    score_logit_null = _logit_stack(null_dL, null_NCD, null_dPhi)
    score_logit_adiyat = _logit_stack(adiyat_dL, adiyat_NCD, adiyat_dPhi)
    thr_logit = float(np.quantile(score_logit_null, 1 - FPR_TARGET))
    recall_logit = float((score_logit_adiyat >= thr_logit).mean())

    # Unified formula B — Fisher chi^2_6 combiner (parameter-free)
    p_dL_null = _empirical_upper_p(null_dL, null_dL)
    p_NCD_null = _empirical_upper_p(null_NCD, null_NCD)
    p_dPhi_null = _empirical_upper_p(null_dPhi, null_dPhi)
    x2_null, p_fisher_null = _fisher_chi2_p(p_dL_null, p_NCD_null, p_dPhi_null)

    p_dL_ad = _empirical_upper_p(adiyat_dL, null_dL)
    p_NCD_ad = _empirical_upper_p(adiyat_NCD, null_NCD)
    p_dPhi_ad = _empirical_upper_p(adiyat_dPhi, null_dPhi)
    x2_ad, p_fisher_ad = _fisher_chi2_p(p_dL_ad, p_NCD_ad, p_dPhi_ad)

    thr_fisher_x2 = float(np.quantile(x2_null, 1 - FPR_TARGET))
    recall_fisher = float((x2_ad >= thr_fisher_x2).mean())

    # Unified formula C — naive z-sum
    def _naive_sum(dL_arr, NCD_arr, dPhi_arr):
        return (_z_score(dL_arr, mu_null["dL"], sd_null["dL"])
                + _z_score(NCD_arr, mu_null["NCD"], sd_null["NCD"])
                + _z_score(dPhi_arr, mu_null["dPhi"], sd_null["dPhi"]))

    score_naive_null = _naive_sum(null_dL, null_NCD, null_dPhi)
    score_naive_adiyat = _naive_sum(adiyat_dL, adiyat_NCD, adiyat_dPhi)
    thr_naive = float(np.quantile(score_naive_null, 1 - FPR_TARGET))
    recall_naive = float((score_naive_adiyat >= thr_naive).mean())

    # --- Verdict dispatch ---
    sanity_R12_ok = recall_R12 >= SANITY_R12_MIN_RECALL
    n_ok = (n_var == EXPECTED_N_VARIANTS and n_adiyat == EXPECTED_N_VARIANTS)
    best_unified = max(recall_logit, recall_fisher)
    if not n_ok:
        verdict = "FAIL_n_variants"
    elif not sanity_R12_ok:
        verdict = "FAIL_sanity_R12_replication"
    elif best_unified >= RECALL_GATE:
        verdict = "PASS_unified_99"
    elif best_unified >= recall_R12 - 0.005:
        verdict = "PARTIAL_below_99_above_R12"
    else:
        verdict = "FAIL_unified_below_R12"

    elapsed = time.time() - t0

    # --- Console summary ---
    print(f"\n{'=' * 64}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    print(f"  n_variants            : {n_var} (expected {EXPECTED_N_VARIANTS})")
    print(f"  n_null_ctrl_edits     : {n_null}")
    print(f"  R12 threshold (p95)   : {thr_R12:.6f}")
    print(f"  recall(R12-only)      : {recall_R12:.4f}  (gate >= {SANITY_R12_MIN_RECALL})")
    print(f"  recall(logistic stack): {recall_logit:.4f}")
    print(f"  recall(Fisher chi2_6) : {recall_fisher:.4f}  (gate >= {RECALL_GATE})")
    print(f"  recall(naive z-sum)   : {recall_naive:.4f}  [informational]")
    print(f"  fold-avg stack coefs  : w_dL={coefs['w_dL']:.4f}  "
          f"w_NCD={coefs['w_NCD']:.4f}  w_dPhi={coefs['w_dPhi']:.4f}  "
          f"b={coefs['b']:.4f}")
    print(f"{'=' * 64}\n")

    # --- Write receipt ---
    report = {
        "experiment": EXP,
        "hypothesis": "H30b — Unified Stack Law on canonical Adiyat-864",
        "schema_version": 1,
        "prereg_document": "experiments/exp94_adiyat_864/PREREG.md",
        "adiyat_label": ADIYAT_LABEL,
        "canonical_verse1_len": len(v1),
        "canonical_L_TEL": round(canon_L, 6),
        "n_variants": int(n_var),
        "n_null_ctrl_edits": int(n_null),
        "frozen_constants": {
            "seed": SEED, "n_pert_per_unit": N_PERT_PER_UNIT,
            "ctrl_n_units": CTRL_N_UNITS, "gzip_level": GZIP_LEVEL,
            "fpr_target": FPR_TARGET,
            "w_T": W_T, "w_EL": W_EL, "b_TEL": B_TEL,
            "expected_n_variants": EXPECTED_N_VARIANTS,
            "recall_gate": RECALL_GATE,
            "sanity_r12_min_recall": SANITY_R12_MIN_RECALL,
        },
        "null_stats": {
            "mu": mu_null, "sd": sd_null,
            "NCD_p95_threshold": round(thr_R12, 6),
            "logit_p95_threshold": round(thr_logit, 6),
            "fisher_x2_p95_threshold": round(thr_fisher_x2, 6),
            "naive_p95_threshold": round(thr_naive, 6),
        },
        "stage2_logistic_coefs_from_exp93": coefs,
        "recalls_at_5pct_fpr": {
            "R12_only_baseline": round(recall_R12, 6),
            "unified_logistic_stack": round(recall_logit, 6),
            "unified_fisher_chi2_6": round(recall_fisher, 6),
            "naive_z_sum_reviewer_baseline": round(recall_naive, 6),
        },
        "adiyat_864_per_variant": adiyat_rows,
        "prereg_gates": {
            "sanity_R12_replication": bool(sanity_R12_ok),
            "n_variants_match": bool(n_ok),
            "logistic_passes_99": bool(recall_logit >= RECALL_GATE),
            "fisher_passes_99": bool(recall_fisher >= RECALL_GATE),
            "best_unified_above_R12_minus_0_005":
                bool(best_unified >= recall_R12 - 0.005),
        },
        "verdict": verdict,
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=float)
    print(f"[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
