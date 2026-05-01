"""
exp95_phonetic_modulation/run.py
================================
H33: phonetic-distance-modulated R12 threshold closes the Adiyat-864
ceiling.

Replicates the exp94_adiyat_864 protocol with two changes:
  1. The R12 threshold is bucketed by phonetic Hamming distance
     d_hamming(orig, repl) from the exp54 PHONETIC_FEATURES table.
     Each stratum d has its own empirical ctrl-null 95th-percentile
     threshold tau(d).
  2. A Boolean VL_CV >= 0.1962 sanity gate (from exp98) is AND-ed in.

Pre-registered in PREREG.md (frozen 2026-04-22).

Reads (integrity-checked):
    phase_06_phi_m.pkl                                   state['CORPORA']
    results/experiments/exp54_phonetic_law_full/...json  slope/intercept/verdict
    results/experiments/exp94_adiyat_864/...json         R12-only baseline
    results/experiments/exp41_gzip_formalised/...json    ctrl-p95 sanity

Writes ONLY under results/experiments/exp95_phonetic_modulation/
"""
from __future__ import annotations

import gzip
import hashlib
import json
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

EXP = "exp95_phonetic_modulation"

# --- Frozen constants (mirror PREREG §7) -----------------------------------
SEED = 42
N_PERT_PER_UNIT = 20
CTRL_N_UNITS = 200
GZIP_LEVEL = 9
FPR_TARGET = 0.05
BAND_A_LO, BAND_A_HI = 15, 100
ADIYAT_LABEL = "Q:100"
EXPECTED_N_VARIANTS = 864
VLCV_FLOOR = 0.1962
SPARSE_STRATUM_MIN_N = 30
EXP54_SLOPE = 0.007265
EXP54_INTERCEPT = -0.002388

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

# --- Phonetic feature vectors (byte-equal to exp54_phonetic_law_full) ------
PHONETIC_FEATURES = {
    "ا": (8.0, 0.5, 0, 0, 0),
    "ب": (1.0, 0.0, 1, 0, 0),
    "ت": (2.0, 0.0, 0, 0, 0),
    "ث": (2.5, 1.0, 0, 0, 0),
    "ج": (4.0, 0.5, 1, 0, 0),
    "ح": (7.0, 1.0, 0, 0, 0),
    "خ": (5.0, 1.0, 0, 0, 0),
    "د": (2.0, 0.0, 1, 0, 0),
    "ذ": (2.5, 1.0, 1, 0, 0),
    "ر": (2.0, 4.0, 1, 0, 0),
    "ز": (3.0, 1.0, 1, 0, 1),
    "س": (3.0, 1.0, 0, 0, 1),
    "ش": (3.5, 1.0, 0, 0, 1),
    "ص": (3.0, 1.0, 0, 1, 1),
    "ض": (2.0, 0.0, 1, 1, 0),
    "ط": (2.0, 0.0, 0, 1, 0),
    "ظ": (2.5, 1.0, 1, 1, 0),
    "ع": (7.0, 1.0, 1, 0, 0),
    "غ": (5.0, 1.0, 1, 0, 0),
    "ف": (1.0, 1.0, 0, 0, 0),
    "ق": (6.0, 0.0, 0, 0, 0),
    "ك": (5.0, 0.0, 0, 0, 0),
    "ل": (2.0, 3.0, 1, 0, 0),
    "م": (1.0, 2.0, 1, 0, 0),
    "ن": (2.0, 2.0, 1, 0, 0),
    "ه": (8.0, 1.0, 0, 0, 0),
    "و": (1.0, 5.0, 1, 0, 0),
    "ي": (4.0, 5.0, 1, 0, 0),
}


def _place_bin(p: float) -> int:
    if p <= 1.5:
        return 0
    if p <= 3.25:
        return 1
    if p <= 4.5:
        return 2
    if p <= 6.5:
        return 3
    if p <= 7.5:
        return 4
    return 5


def hamming_phonetic(a: str, b: str) -> int:
    """5-D discretised-feature Hamming distance (byte-equal to exp54 M1)."""
    if a not in PHONETIC_FEATURES or b not in PHONETIC_FEATURES:
        return 5  # unknown pair = max distance
    fa, fb = PHONETIC_FEATURES[a], PHONETIC_FEATURES[b]
    d = 0
    d += int(_place_bin(fa[0]) != _place_bin(fb[0]))
    d += int(round(fa[1]) != round(fb[1]))
    d += int(fa[2] != fb[2])
    d += int(fa[3] != fb[3])
    d += int(fa[4] != fb[4])
    return d


# --- Primitives (byte-equal to exp41 / exp43 / exp94) ----------------------
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


# --- Perturbation that reports the (orig, repl) pair used ------------------
def _apply_perturbation_with_pair(verses, rng: random.Random):
    """Byte-equal to exp94._apply_perturbation but also returns (orig, repl)
    so we can bucket the NCD by phonetic distance."""
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
            new_toks = list(toks)
            new_toks[wi] = new_word
            new_verses = list(verses)
            new_verses[vi] = " ".join(new_toks)
            return new_verses, vi, original, repl
    return None


# --- VL_CV (byte-equal to exp98 / src.features.vl_cv) ----------------------
def _vl_cv(verses) -> float:
    lens = [len(v.split()) for v in verses]
    if len(lens) < 2:
        return 0.0
    arr = np.asarray(lens, dtype=float)
    if arr.mean() == 0.0:
        return 0.0
    return float(arr.std(ddof=1) / arr.mean())


# --- 864 enumeration (byte-equal to exp43 / exp94) -------------------------
def _enumerate_864(v1: str) -> list[dict]:
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


# --- Receipt loaders -------------------------------------------------------
def _load_exp54() -> dict:
    path = (_ROOT / "results" / "experiments"
            / "exp54_phonetic_law_full" / "exp54_phonetic_law_full.json")
    if not path.exists():
        raise FileNotFoundError(f"exp54 receipt missing: {path}")
    with open(path, "r", encoding="utf-8") as f:
        j = json.load(f)
    if j.get("overall_verdict") != "LAW_CONFIRMED":
        raise RuntimeError(
            f"exp54 overall_verdict = {j.get('overall_verdict')!r}; "
            "PREREG §4 FAIL_exp54_missing: expected LAW_CONFIRMED."
        )
    m1 = j["metric_results"]["M1_hamming"]
    return {
        "slope": float(m1["slope"]),
        "intercept": float(m1["intercept"]),
        "pearson_r": float(m1["pearson_r"]),
        "prereg_hash": j.get("prereg_hash", ""),
    }


def _load_exp94() -> dict:
    path = (_ROOT / "results" / "experiments"
            / "exp94_adiyat_864" / "exp94_adiyat_864.json")
    if not path.exists():
        raise FileNotFoundError(f"exp94 receipt missing: {path}")
    with open(path, "r", encoding="utf-8") as f:
        j = json.load(f)
    return {
        "R12_only_baseline": float(j["recalls_at_5pct_fpr"]["R12_only_baseline"]),
        "null_NCD_mu": float(j["null_stats"]["mu"]["NCD"]),
        "null_NCD_sd": float(j["null_stats"]["sd"]["NCD"]),
        "NCD_p95_threshold": float(j["null_stats"]["NCD_p95_threshold"]),
    }


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


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

    print(f"[{EXP}] H33 — phonetic-distance-modulated R12 on Adiyat-864")

    # --- Load receipts ---
    exp54 = _load_exp54()
    exp94 = _load_exp94()
    print(f"[{EXP}] exp54 M1_hamming: slope={exp54['slope']:+.6f}  "
          f"intercept={exp54['intercept']:+.6f}  r={exp54['pearson_r']:.3f}")
    print(f"[{EXP}] exp94 R12-only recall baseline: {exp94['R12_only_baseline']:.4f}")
    print(f"[{EXP}] exp94 NCD p95 threshold (non-stratified): "
          f"{exp94['NCD_p95_threshold']:.6f}")

    # --- Load corpus ---
    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    adiyat = next((u for u in CORPORA.get("quran", [])
                   if getattr(u, "label", "") == ADIYAT_LABEL), None)
    if adiyat is None:
        raise RuntimeError(f"{ADIYAT_LABEL} not found in CORPORA['quran']")
    canon_verses = list(adiyat.verses)
    v1 = canon_verses[0]
    canon_stream = _letters_28(" ".join(canon_verses))
    canon_vlcv = _vl_cv(canon_verses)
    print(f"[{EXP}] Canonical Q:100 VL_CV = {canon_vlcv:.4f}  "
          f"(floor {VLCV_FLOOR}, passes = {canon_vlcv >= VLCV_FLOOR})")

    vlcv_sanity_ok = canon_vlcv >= VLCV_FLOOR

    # --- Step 1: stratified null calibration ---
    print(f"[{EXP}] Step 1: {CTRL_N_UNITS} ctrl units × {N_PERT_PER_UNIT} edits ...")
    ctrl_pool: list = []
    for name in ARABIC_CTRL:
        ctrl_pool.extend(_band_a(CORPORA.get(name, [])))
    rng_pool = random.Random(SEED + 1)
    rng_pool.shuffle(ctrl_pool)
    ctrl_units = ctrl_pool[:CTRL_N_UNITS]
    rng_c = random.Random(SEED + 2)

    null_by_d: dict[int, list[float]] = {d: [] for d in range(6)}
    null_all: list[float] = []
    for u in ctrl_units:
        rng_u = random.Random(rng_c.randrange(1 << 30))
        ctrl_canon_stream = _letters_28(" ".join(u.verses))
        for _ in range(N_PERT_PER_UNIT):
            pair = _apply_perturbation_with_pair(u.verses, rng_u)
            if pair is None:
                continue
            pert_verses, _vi, orig, repl = pair
            d = hamming_phonetic(orig, repl)
            ncd_val = _ncd(ctrl_canon_stream,
                           _letters_28(" ".join(pert_verses)))
            null_by_d[d].append(ncd_val)
            null_all.append(ncd_val)
    n_null = len(null_all)
    print(f"[{EXP}] Null pool: n={n_null}  per-d sizes: "
          + "  ".join(f"d{d}={len(null_by_d[d])}" for d in range(6)))

    # --- Build tau(d) thresholds ---
    tau_by_d: dict[int, float] = {}
    tau_ci_by_d: dict[int, tuple[float, float]] = {}
    tau_source: dict[int, str] = {}
    for d in range(6):
        arr = np.asarray(null_by_d[d], dtype=float)
        if arr.size >= SPARSE_STRATUM_MIN_N:
            thr = float(np.quantile(arr, 1 - FPR_TARGET))
            tau_by_d[d] = thr
            tau_source[d] = f"stratified (n={arr.size})"
        elif arr.size > 0:
            # Sparse — fall back to adjacent bucket or pool
            nearest = None
            for dd in (d - 1, d + 1, d - 2, d + 2):
                if 0 <= dd <= 5 and len(null_by_d[dd]) >= SPARSE_STRATUM_MIN_N:
                    nearest = dd
                    break
            if nearest is not None:
                thr = float(np.quantile(null_by_d[nearest], 1 - FPR_TARGET))
                tau_by_d[d] = thr
                tau_source[d] = f"adjacent (pooled from d={nearest}, this-n={arr.size})"
            else:
                thr = float(np.quantile(null_all, 1 - FPR_TARGET))
                tau_by_d[d] = thr
                tau_source[d] = f"global fallback (this-n={arr.size})"
        else:
            tau_by_d[d] = float(np.quantile(null_all, 1 - FPR_TARGET))
            tau_source[d] = "global fallback (empty stratum)"

    # Bootstrap CI on each stratum tau
    rng_boot = np.random.RandomState(SEED)
    for d in range(6):
        arr = np.asarray(null_by_d[d], dtype=float)
        if arr.size < SPARSE_STRATUM_MIN_N:
            tau_ci_by_d[d] = (float("nan"), float("nan"))
            continue
        boots = [
            float(np.quantile(arr[rng_boot.choice(arr.size, arr.size, replace=True)],
                              1 - FPR_TARGET))
            for _ in range(1000)
        ]
        tau_ci_by_d[d] = (float(np.percentile(boots, 2.5)),
                          float(np.percentile(boots, 97.5)))

    for d in range(6):
        ci = tau_ci_by_d[d]
        lo = f"{ci[0]:.6f}" if np.isfinite(ci[0]) else "   n/a"
        hi = f"{ci[1]:.6f}" if np.isfinite(ci[1]) else "   n/a"
        print(f"[{EXP}]   τ(d={d}) = {tau_by_d[d]:.6f}  "
              f"CI95=[{lo}, {hi}]  src={tau_source[d]}")

    # Ctrl FPR per stratum at its own tau (should be ~5% by construction)
    ctrl_fpr_by_d: dict[int, float] = {}
    for d in range(6):
        arr = np.asarray(null_by_d[d], dtype=float)
        if arr.size == 0:
            ctrl_fpr_by_d[d] = float("nan")
        else:
            ctrl_fpr_by_d[d] = float((arr >= tau_by_d[d]).mean())

    overfpr_strata = [
        d for d, fpr in ctrl_fpr_by_d.items()
        if np.isfinite(fpr) and fpr > FPR_TARGET + 1e-6
        and len(null_by_d[d]) >= SPARSE_STRATUM_MIN_N
    ]

    # --- Step 2: Adiyat-864 scoring ---
    print(f"[{EXP}] Step 2: enumerating Adiyat 864 variants ...")
    v1_variants = _enumerate_864(v1)
    n_var = len(v1_variants)
    print(f"[{EXP}] Enumerated {n_var} variants (expected {EXPECTED_N_VARIANTS})")

    per_variant: list[dict] = []
    for vv in v1_variants:
        new_v1 = vv["new_v1"]
        var_verses = [new_v1] + list(canon_verses[1:])
        var_stream = _letters_28(" ".join(var_verses))
        ncd_edit = _ncd(canon_stream, var_stream)
        d = hamming_phonetic(vv["orig"], vv["repl"])
        tau = tau_by_d[d]
        fires_r12_mod = bool(ncd_edit >= tau)
        fires_r12_flat = bool(ncd_edit >= exp94["NCD_p95_threshold"])
        fires_vlcv = bool(canon_vlcv >= VLCV_FLOOR)
        fires_conj = bool(fires_r12_mod and fires_vlcv)
        per_variant.append({
            "pos": vv["pos"],
            "orig": vv["orig"],
            "repl": vv["repl"],
            "d_hamming": d,
            "ncd_edit": round(ncd_edit, 6),
            "tau_at_d": round(tau, 6),
            "fires_R12_flat_exp94": fires_r12_flat,
            "fires_R12_modulated": fires_r12_mod,
            "fires_conjunction_with_vlcv": fires_conj,
        })

    # --- Step 3: aggregate recalls ---
    n_flat = sum(1 for v in per_variant if v["fires_R12_flat_exp94"])
    n_mod = sum(1 for v in per_variant if v["fires_R12_modulated"])
    n_conj = sum(1 for v in per_variant if v["fires_conjunction_with_vlcv"])
    recall_flat = n_flat / n_var if n_var else float("nan")
    recall_mod = n_mod / n_var if n_var else float("nan")
    recall_conj = n_conj / n_var if n_var else float("nan")

    # --- Step 5: per-stratum audit ---
    stratum_audit: dict[int, dict] = {}
    for d in range(6):
        in_stratum = [v for v in per_variant if v["d_hamming"] == d]
        n_s = len(in_stratum)
        fired_mod = sum(1 for v in in_stratum if v["fires_R12_modulated"])
        fired_flat = sum(1 for v in in_stratum if v["fires_R12_flat_exp94"])
        stratum_audit[d] = {
            "n_variants": n_s,
            "n_fired_modulated": fired_mod,
            "n_fired_flat_exp94": fired_flat,
            "recall_modulated": (fired_mod / n_s) if n_s else None,
            "recall_flat_exp94": (fired_flat / n_s) if n_s else None,
            "tau": tau_by_d[d],
            "tau_ci95": list(tau_ci_by_d[d]),
            "tau_source": tau_source[d],
            "ctrl_n": len(null_by_d[d]),
            "ctrl_fpr_at_tau": ctrl_fpr_by_d[d],
        }

    # --- Verdict ---
    if not vlcv_sanity_ok:
        verdict = "FAIL_vlcv_sanity"
    elif overfpr_strata:
        verdict = "FAIL_ctrl_stratum_overfpr"
    elif recall_mod >= 0.9999:
        verdict = "PASS_modulation_100"
    elif recall_mod >= 0.999:
        verdict = "PASS_modulation_99.9"
    elif recall_mod > exp94["R12_only_baseline"]:
        verdict = "PARTIAL_modulation_lifts_below_999"
    else:
        verdict = "FAIL_modulation_no_lift"

    elapsed = time.time() - t0

    print(f"\n{'=' * 64}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    print(f"  recall(R12-flat  baseline) : {recall_flat:.4f}  "
          f"({n_flat}/{n_var})")
    print(f"  recall(R12-modulated)      : {recall_mod:.4f}  "
          f"({n_mod}/{n_var})")
    print(f"  recall(modulated ∧ VL_CV)  : {recall_conj:.4f}  "
          f"({n_conj}/{n_var})")
    if overfpr_strata:
        print(f"  OVER-FPR STRATA: "
              + "  ".join(f"d={d} fpr={ctrl_fpr_by_d[d]:.3f}"
                          for d in overfpr_strata))
    print(f"{'=' * 64}")
    for d in range(6):
        s = stratum_audit[d]
        print(f"  d={d}  n_var={s['n_variants']:3d}  "
              f"n_fired_mod={s['n_fired_modulated']:3d}  "
              f"recall_mod={s['recall_modulated']}  "
              f"recall_flat={s['recall_flat_exp94']}  "
              f"ctrl_fpr={s['ctrl_fpr_at_tau']}")

    report = {
        "experiment": EXP,
        "hypothesis": (
            "H33 — phonetic-distance-modulated R12 closes the Adiyat-864 "
            "ceiling without violating per-stratum FPR."
        ),
        "schema_version": 1,
        "prereg_document": "experiments/exp95_phonetic_modulation/PREREG.md",
        "prereg_hash": _prereg_hash(),
        "exp54_inputs": exp54,
        "exp94_baseline": exp94,
        "frozen_constants": {
            "seed": SEED,
            "n_pert_per_unit": N_PERT_PER_UNIT,
            "ctrl_n_units": CTRL_N_UNITS,
            "gzip_level": GZIP_LEVEL,
            "fpr_target": FPR_TARGET,
            "band_a": [BAND_A_LO, BAND_A_HI],
            "adiyat_label": ADIYAT_LABEL,
            "expected_n_variants": EXPECTED_N_VARIANTS,
            "vlcv_floor": VLCV_FLOOR,
            "sparse_stratum_min_n": SPARSE_STRATUM_MIN_N,
        },
        "canonical_q100_vlcv": canon_vlcv,
        "vlcv_sanity_ok": vlcv_sanity_ok,
        "n_variants": n_var,
        "n_null_ctrl_edits": n_null,
        "tau_by_d": {str(d): tau_by_d[d] for d in range(6)},
        "tau_ci95_by_d": {str(d): list(tau_ci_by_d[d]) for d in range(6)},
        "tau_source_by_d": {str(d): tau_source[d] for d in range(6)},
        "ctrl_n_by_d": {str(d): len(null_by_d[d]) for d in range(6)},
        "ctrl_fpr_by_d": {str(d): ctrl_fpr_by_d[d] for d in range(6)},
        "overfpr_strata": overfpr_strata,
        "recalls": {
            "R12_flat_exp94_reproduction": recall_flat,
            "R12_modulated_primary": recall_mod,
            "R12_modulated_AND_vlcv_floor": recall_conj,
            "R12_only_baseline_from_exp94": exp94["R12_only_baseline"],
            "delta_vs_baseline": recall_mod - exp94["R12_only_baseline"],
        },
        "stratum_audit": {str(d): stratum_audit[d] for d in range(6)},
        "verdict": verdict,
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=float)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
