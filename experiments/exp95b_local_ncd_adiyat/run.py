"""
exp95b_local_ncd_adiyat/run.py
==============================
H34: window-local NCD (3-verse window centred on edit position) lifts
the Adiyat-864 ceiling above 0.999 without violating FPR.

Replicates the exp94_adiyat_864 protocol with one change:
  - Replace document-level NCD with a 3-verse window-local NCD centred
    on the perturbed verse position (byte-equal to exp41._window_ncd).
  - For Adiyat-864 every perturbation hits v1 (verse index 0), so the
    window is verses[0:3].

Pre-registered in PREREG.md (frozen 2026-04-26 night).

Reads (integrity-checked):
    phase_06_phi_m.pkl                                state['CORPORA']
    results/experiments/exp94_adiyat_864/...json     R12-only baseline (0.990741)

Writes ONLY under results/experiments/exp95b_local_ncd_adiyat/
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

EXP = "exp95b_local_ncd_adiyat"

# --- Frozen constants (mirror PREREG §7) -----------------------------------
SEED = 42
N_PERT_PER_UNIT = 20
CTRL_N_UNITS = 200
GZIP_LEVEL = 9
FPR_TARGET = 0.05
BAND_A_LO, BAND_A_HI = 15, 100
ADIYAT_LABEL = "Q:100"
EXPECTED_N_VARIANTS = 864
WINDOW_L0 = 3
PROTOCOL_DRIFT_TOL = 0.001

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


# --- Primitives (byte-equal to exp41 / exp43 / exp94 / exp95) --------------
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


def _window_bounds(vi: int, n: int) -> tuple[int, int]:
    """3-verse window centred on vi, right-clipped to [0, n).

    Byte-equal to exp41._window_ncd index logic.
    """
    lo = max(0, vi - WINDOW_L0 // 2)
    hi = min(n, lo + WINDOW_L0)
    lo = max(0, hi - WINDOW_L0)
    return lo, hi


def _doc_ncd(canon_verses, pert_verses) -> float:
    a = _letters_28(" ".join(canon_verses))
    b = _letters_28(" ".join(pert_verses))
    return _ncd(a, b)


def _window_ncd(canon_verses, pert_verses, vi: int) -> float:
    lo, hi = _window_bounds(vi, len(canon_verses))
    a = _letters_28(" ".join(canon_verses[lo:hi]))
    b = _letters_28(" ".join(pert_verses[lo:hi]))
    return _ncd(a, b)


# --- Perturbation that returns vi (byte-equal to exp94) --------------------
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


# --- 864 enumeration (byte-equal to exp43 / exp94 / exp95) -----------------
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
def _load_exp94() -> dict:
    path = (_ROOT / "results" / "experiments"
            / "exp94_adiyat_864" / "exp94_adiyat_864.json")
    if not path.exists():
        raise FileNotFoundError(f"exp94 receipt missing: {path}")
    with open(path, "r", encoding="utf-8") as f:
        j = json.load(f)
    return {
        "R12_only_baseline": float(j["recalls_at_5pct_fpr"]["R12_only_baseline"]),
        "NCD_p95_threshold": float(j["null_stats"]["NCD_p95_threshold"]),
        "null_NCD_mu": float(j["null_stats"]["mu"]["NCD"]),
        "null_NCD_sd": float(j["null_stats"]["sd"]["NCD"]),
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

    print(f"[{EXP}] H34 — window-local NCD on Adiyat-864 (window L0={WINDOW_L0})")

    exp94 = _load_exp94()
    print(f"[{EXP}] exp94 R12-only flat baseline: "
          f"{exp94['R12_only_baseline']:.6f}")
    print(f"[{EXP}] exp94 NCD_doc p95 threshold: "
          f"{exp94['NCD_p95_threshold']:.6f}")

    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    adiyat = next((u for u in CORPORA.get("quran", [])
                   if getattr(u, "label", "") == ADIYAT_LABEL), None)
    if adiyat is None:
        raise RuntimeError(f"{ADIYAT_LABEL} not found in CORPORA['quran']")
    canon_verses = list(adiyat.verses)
    v1 = canon_verses[0]
    print(f"[{EXP}] Canonical Q:100 has {len(canon_verses)} verses, "
          f"v1 len={len(v1)} chars")

    # --- Step 1: null calibration on 4000 ctrl perturbations ---
    print(f"[{EXP}] Step 1: {CTRL_N_UNITS} ctrl units × {N_PERT_PER_UNIT} edits "
          f"(window-local NCD + doc-level sanity) ...")
    ctrl_pool: list = []
    for name in ARABIC_CTRL:
        ctrl_pool.extend(_band_a(CORPORA.get(name, [])))
    rng_pool = random.Random(SEED + 1)
    rng_pool.shuffle(ctrl_pool)
    ctrl_units = ctrl_pool[:CTRL_N_UNITS]
    rng_c = random.Random(SEED + 2)

    null_window: list[float] = []
    null_doc: list[float] = []
    for u in ctrl_units:
        rng_u = random.Random(rng_c.randrange(1 << 30))
        for _ in range(N_PERT_PER_UNIT):
            pair = _apply_perturbation(u.verses, rng_u)
            if pair is None:
                continue
            pert_verses, vi = pair
            null_window.append(_window_ncd(u.verses, pert_verses, vi))
            null_doc.append(_doc_ncd(u.verses, pert_verses))
    n_null = len(null_window)
    print(f"[{EXP}] Null pool: n={n_null}")

    null_window_arr = np.asarray(null_window, dtype=float)
    null_doc_arr = np.asarray(null_doc, dtype=float)

    tau_window = float(np.quantile(null_window_arr, 1 - FPR_TARGET))
    tau_doc = float(np.quantile(null_doc_arr, 1 - FPR_TARGET))

    # Bootstrap CI on tau_window
    rng_boot = np.random.RandomState(SEED)
    boots = [
        float(np.quantile(
            null_window_arr[rng_boot.choice(n_null, n_null, replace=True)],
            1 - FPR_TARGET))
        for _ in range(1000)
    ]
    tau_window_ci = (float(np.percentile(boots, 2.5)),
                     float(np.percentile(boots, 97.5)))

    print(f"[{EXP}]   τ_window = {tau_window:.6f}  "
          f"CI95=[{tau_window_ci[0]:.6f}, {tau_window_ci[1]:.6f}]")
    print(f"[{EXP}]   τ_doc (sanity) = {tau_doc:.6f}  "
          f"(exp94 reported {exp94['NCD_p95_threshold']:.6f})")

    # Empirical FPR at τ_window on the same null
    null_fpr_window = float((null_window_arr >= tau_window).mean())
    null_fpr_doc = float((null_doc_arr >= tau_doc).mean())

    # --- Step 2: Adiyat-864 scoring ---
    print(f"[{EXP}] Step 2: enumerating Adiyat 864 variants ...")
    v1_variants = _enumerate_864(v1)
    n_var = len(v1_variants)
    print(f"[{EXP}] Enumerated {n_var} variants (expected {EXPECTED_N_VARIANTS})")

    per_variant: list[dict] = []
    for vv in v1_variants:
        new_v1 = vv["new_v1"]
        var_verses = [new_v1] + list(canon_verses[1:])
        ncd_window_val = _window_ncd(canon_verses, var_verses, vi=0)
        ncd_doc_val = _doc_ncd(canon_verses, var_verses)
        fires_window = bool(ncd_window_val >= tau_window)
        fires_doc = bool(ncd_doc_val >= tau_doc)
        per_variant.append({
            "pos": vv["pos"],
            "orig": vv["orig"],
            "repl": vv["repl"],
            "ncd_window": round(ncd_window_val, 6),
            "ncd_doc": round(ncd_doc_val, 6),
            "fires_window_local": fires_window,
            "fires_doc_flat_sanity": fires_doc,
        })

    # --- Step 3: aggregate recalls ---
    n_window = sum(1 for v in per_variant if v["fires_window_local"])
    n_doc = sum(1 for v in per_variant if v["fires_doc_flat_sanity"])
    recall_window = n_window / n_var if n_var else float("nan")
    recall_doc = n_doc / n_var if n_var else float("nan")
    lift = recall_window - exp94["R12_only_baseline"]

    # --- Step 4: per-position audit ---
    by_pos: dict[int, dict] = {}
    for v in per_variant:
        p = v["pos"]
        if p not in by_pos:
            by_pos[p] = {"n": 0, "n_fired_window": 0, "n_fired_doc": 0}
        by_pos[p]["n"] += 1
        by_pos[p]["n_fired_window"] += int(v["fires_window_local"])
        by_pos[p]["n_fired_doc"] += int(v["fires_doc_flat_sanity"])
    for p, d in by_pos.items():
        d["recall_window"] = d["n_fired_window"] / d["n"] if d["n"] else None
        d["recall_doc"] = d["n_fired_doc"] / d["n"] if d["n"] else None
    pos_audit = {str(p): by_pos[p] for p in sorted(by_pos.keys())}

    # --- Step 5: protocol drift gate ---
    drift = abs(recall_doc - exp94["R12_only_baseline"])
    protocol_ok = drift <= PROTOCOL_DRIFT_TOL

    # --- Verdict ---
    if not protocol_ok:
        verdict = "FAIL_protocol_drift"
    elif null_fpr_window > FPR_TARGET + 1e-6:
        verdict = "FAIL_window_overfpr"
    elif recall_window <= exp94["R12_only_baseline"]:
        verdict = "FAIL_window_no_lift"
    elif recall_window >= 0.9999:
        verdict = "PASS_window_100"
    elif recall_window >= 0.999:
        verdict = "PASS_window_999"
    else:
        verdict = "PARTIAL_window_lifts_below_999"

    elapsed = time.time() - t0

    print(f"\n{'=' * 64}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    print(f"  recall(window-local)       : {recall_window:.6f}  "
          f"({n_window}/{n_var})")
    print(f"  recall(doc-level sanity)   : {recall_doc:.6f}  "
          f"({n_doc}/{n_var})  [exp94 baseline {exp94['R12_only_baseline']:.6f}]")
    print(f"  lift over flat baseline    : {lift:+.6f}")
    print(f"  ctrl FPR at τ_window       : {null_fpr_window:.4f}  "
          f"(target ≤ {FPR_TARGET})")
    print(f"  ctrl FPR at τ_doc          : {null_fpr_doc:.4f}  "
          f"[sanity, expected ≈ {FPR_TARGET}]")
    print(f"  protocol drift             : {drift:.6f}  "
          f"(tol {PROTOCOL_DRIFT_TOL}, ok={protocol_ok})")
    print(f"{'=' * 64}")

    # Print position-level summary for the 8 positions with lowest recall
    positions_sorted = sorted(
        pos_audit.items(),
        key=lambda kv: kv[1].get("recall_window", 1.0) or 1.0
    )
    print(f"\n[{EXP}] Top-8 weakest positions (by window recall):")
    for p, d in positions_sorted[:8]:
        print(f"    pos {p:>2}  n={d['n']:>2}  "
              f"recall_window={d['recall_window']:.4f}  "
              f"recall_doc={d['recall_doc']:.4f}")

    report = {
        "experiment": EXP,
        "hypothesis": (
            "H34 — window-local NCD (3-verse window centred on edit) lifts "
            "the Adiyat-864 ceiling above 0.999 without violating FPR."
        ),
        "schema_version": 1,
        "prereg_document": "experiments/exp95b_local_ncd_adiyat/PREREG.md",
        "prereg_hash": _prereg_hash(),
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
            "window_l0": WINDOW_L0,
            "protocol_drift_tol": PROTOCOL_DRIFT_TOL,
        },
        "n_variants": n_var,
        "n_null_ctrl_edits": n_null,
        "tau_window": tau_window,
        "tau_window_ci95": list(tau_window_ci),
        "tau_doc_sanity": tau_doc,
        "ctrl_fpr_at_tau_window": null_fpr_window,
        "ctrl_fpr_at_tau_doc": null_fpr_doc,
        "recalls": {
            "window_local_primary": recall_window,
            "doc_flat_sanity": recall_doc,
            "exp94_R12_baseline": exp94["R12_only_baseline"],
            "lift_window_over_flat": lift,
        },
        "protocol_drift": {
            "abs_diff_doc_recall_vs_exp94": drift,
            "ok": protocol_ok,
        },
        "per_position_audit": pos_audit,
        "per_variant": per_variant,
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
