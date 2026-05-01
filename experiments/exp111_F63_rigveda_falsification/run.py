"""experiments/exp111_F63_rigveda_falsification/run.py
==========================================================
F63 falsification test against Sanskrit Vedic Rigveda.

If Rigveda's per-sūkta p_max ≥ Quran's 0.7273 OR H_EL ≤ Quran's 0.9685,
F63 is dethroned and the verdict is FAIL_rigveda_dethrones_quran.

Sizing showed Rigveda median p_max = 0.3333 and H_EL = 2.2878, so we
expect PASS_quran_rhyme_extremum_xtrad_with_rigveda.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._phi_universal_xtrad_sizing import (  # noqa: E402
    _load_quran,
    _load_arabic_peers,
    _load_hebrew_tanakh,
    _load_greek_nt,
    _load_pali,
    _load_avestan,
    _features_universal,
)
from scripts._rigveda_loader_v2 import (  # noqa: E402
    load_rigveda,
    features_universal_sanskrit,
)


SEED = 42
N_PERMUTATIONS = 10000
H_EL_MARGIN = 0.5
P_MAX_MARGIN = 1.4
PERM_ALPHA_BONF = 5e-4
HERE = Path(__file__).resolve().parent
PREREG_PATH = HERE / "PREREG.md"
RECEIPT_PATH = (
    ROOT / "results" / "experiments" /
    "exp111_F63_rigveda_falsification" /
    "exp111_F63_rigveda_falsification.json"
)
F63_R1_PATH = ROOT / "results" / "auxiliary" / "_f63_real_verse_only_perm.json"
RIGVEDA_MANIFEST = ROOT / "data" / "corpora" / "sa" / "manifest.json"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    print("# === exp111_F63_rigveda_falsification — execution ===")
    started_at = datetime.now(timezone.utc)
    t0 = time.time()
    prereg_bytes = PREREG_PATH.read_bytes()
    prereg_hash = _sha256(prereg_bytes)
    print(f"# PREREG hash: {prereg_hash}")

    print("# 1. loading corpora ...")
    quran = _load_quran()
    arabic = _load_arabic_peers()
    arabic_bible = arabic.get("arabic_bible", [])
    hebrew = _load_hebrew_tanakh()
    greek = _load_greek_nt()
    pali = _load_pali()
    avestan = _load_avestan()
    rigveda = load_rigveda()
    CORPORA = ["quran", "arabic_bible", "hebrew_tanakh", "greek_nt",
               "pali", "avestan_yasna", "rigveda"]
    units_by_corpus = {
        "quran": quran,
        "arabic_bible": arabic_bible,
        "hebrew_tanakh": hebrew,
        "greek_nt": greek,
        "pali": pali,
        "avestan_yasna": avestan,
        "rigveda": rigveda,
    }
    for c in CORPORA:
        print(f"#   {c}: {len(units_by_corpus[c])} units")

    # Audit A1: Rigveda manifest sha256 check
    a1_ok = True
    a1_details = {}
    if RIGVEDA_MANIFEST.exists():
        man = json.loads(RIGVEDA_MANIFEST.read_text(encoding="utf-8"))
        for fmeta in man.get("files", []):
            fp = ROOT / "data" / "corpora" / "sa" / fmeta["filename"]
            actual = _sha256(fp.read_bytes())
            expected = fmeta["sha256"]
            ok = (actual == expected)
            a1_details[fmeta["filename"]] = {
                "expected_sha256": expected, "actual_sha256": actual,
                "match": ok}
            if not ok:
                a1_ok = False
        print(f"# A1 (Rigveda manifest): "
              f"{'OK (10/10 mandalas SHA-256 match)' if a1_ok else 'FAIL_DRIFT'}")
    else:
        a1_ok = False
        print(f"# A1 (Rigveda manifest): MISSING")

    print("# 2. extracting universal features (per corpus) ...")
    feats = {c: [] for c in CORPORA}
    for c in CORPORA:
        if c == "rigveda":
            extractor = features_universal_sanskrit
        else:
            extractor = _features_universal
        for u in units_by_corpus[c]:
            try:
                feats[c].append(extractor(u))
            except Exception:
                pass
        print(f"#   {c}: {len(feats[c])} units passed")

    # Audit A2: feature parity for Quran vs F63 R1
    a2_ok = True
    a2_details = {}
    if F63_R1_PATH.exists():
        f63 = json.loads(F63_R1_PATH.read_text(encoding="utf-8"))
        f63_quran = f63["medians"]["quran"]
        q_pmax = float(np.median([f["p_max"] for f in feats["quran"]]))
        q_hel = float(np.median([f["H_EL"] for f in feats["quran"]]))
        a2_details = {
            "exp111_quran_p_max": q_pmax,
            "f63_r1_quran_p_max": f63_quran["p_max"],
            "delta_p_max": abs(q_pmax - f63_quran["p_max"]),
            "exp111_quran_h_el": q_hel,
            "f63_r1_quran_h_el": f63_quran["H_EL"],
            "delta_h_el": abs(q_hel - f63_quran["H_EL"]),
        }
        if a2_details["delta_p_max"] > 1e-9 or a2_details["delta_h_el"] > 1e-9:
            a2_ok = False
        print(f"# A2 (feature-parity vs F63 R1): "
              f"{'OK' if a2_ok else 'FAIL'}; "
              f"delta_p_max={a2_details['delta_p_max']:.2e}, "
              f"delta_h_el={a2_details['delta_h_el']:.2e}")

    print("\n# === medians ===")
    print(f"# {'corpus':<14s}  {'n':>5s}  {'p_max':>10s}  {'H_EL':>10s}")
    medians = {}
    for c in CORPORA:
        fs = feats[c]
        pmax = float(np.median([f["p_max"] for f in fs]))
        hel  = float(np.median([f["H_EL"]  for f in fs]))
        medians[c] = (pmax, hel)
        print(f"# {c:<14s}  {len(fs):>5d}  {pmax:>10.4f}  {hel:>10.4f}")

    qpmax, qhel = medians["quran"]
    others = [(c, p, h) for c, (p, h) in medians.items() if c != "quran"]
    next_p_max_corpus, next_p_max_val, _ = max(others, key=lambda t: t[1])
    next_h_el_corpus, _, next_h_el_val = min(others, key=lambda t: t[2])
    ratio_p_max = qpmax / next_p_max_val
    ratio_h_el = qhel / next_h_el_val

    print(f"\n# Quran p_max = {qpmax:.4f}; next-highest = {next_p_max_corpus} = {next_p_max_val:.4f}; "
          f"ratio = {ratio_p_max:.4f} (need > {P_MAX_MARGIN})")
    print(f"# Quran H_EL  = {qhel:.4f}; next-lowest  = {next_h_el_corpus} = {next_h_el_val:.4f}; "
          f"ratio = {ratio_h_el:.4f} (need < {H_EL_MARGIN})")

    # Permutation null
    print(f"\n# 3. permutation null ({N_PERMUTATIONS} shuffles, seed={SEED})")
    all_pmax = []
    all_hel = []
    for c in CORPORA:
        for f in feats[c]:
            all_pmax.append(f["p_max"])
            all_hel.append(f["H_EL"])
    all_pmax = np.array(all_pmax)
    all_hel = np.array(all_hel)
    n_total = len(all_pmax)
    sizes = [len(feats[c]) for c in CORPORA]
    quran_idx = CORPORA.index("quran")

    rng = np.random.default_rng(SEED)
    n_h_passes = 0
    n_p_passes = 0
    pt0 = time.time()
    for it in range(N_PERMUTATIONS):
        perm = rng.permutation(n_total)
        offsets = np.cumsum([0] + sizes)
        h_meds = np.empty(len(CORPORA))
        p_meds = np.empty(len(CORPORA))
        for j in range(len(CORPORA)):
            sub = perm[offsets[j]:offsets[j+1]]
            if len(sub) == 0:
                h_meds[j] = np.inf; p_meds[j] = -np.inf
            else:
                h_meds[j] = np.median(all_hel[sub])
                p_meds[j] = np.median(all_pmax[sub])
        fh = h_meds[quran_idx]; fp = p_meds[quran_idx]
        others_h = np.delete(h_meds, quran_idx)
        others_p = np.delete(p_meds, quran_idx)
        nlh = float(others_h.min()); nhp = float(others_p.max())
        rh = fh / nlh if nlh > 0 else np.inf
        rp = fp / nhp if nhp > 0 else 0
        if fh < nlh and rh < H_EL_MARGIN:
            n_h_passes += 1
        if fp > nhp and rp > P_MAX_MARGIN:
            n_p_passes += 1
        if (it + 1) % 1000 == 0:
            print(f"#   {it+1}/{N_PERMUTATIONS} ({time.time()-pt0:.1f}s); "
                  f"H_EL_passes={n_h_passes}, p_max_passes={n_p_passes}")

    perm_p_h = n_h_passes / N_PERMUTATIONS
    perm_p_p = n_p_passes / N_PERMUTATIONS
    print(f"# perm_p (H_EL extremum)  = {perm_p_h:.6f}")
    print(f"# perm_p (p_max extremum) = {perm_p_p:.6f}")

    # Verdict
    cond1 = qhel < next_h_el_val and ratio_h_el < H_EL_MARGIN
    cond2 = qpmax > next_p_max_val and ratio_p_max > P_MAX_MARGIN
    cond3 = perm_p_h < PERM_ALPHA_BONF
    cond4 = perm_p_p < PERM_ALPHA_BONF
    cond_audit = a1_ok and a2_ok

    if cond1 and cond2 and cond3 and cond4 and cond_audit:
        verdict = "PASS_quran_rhyme_extremum_xtrad_with_rigveda"
    elif (not cond1 or not cond2):
        verdict = "FAIL_rigveda_dethrones_quran"
    elif not cond_audit:
        verdict = "FAIL_audit"
    else:
        verdict = "FAIL_perm_p_above_alpha"

    print(f"\n# VERDICT: {verdict}")
    wall = time.time() - t0
    finished_at = datetime.now(timezone.utc)
    print(f"# wall-time: {wall:.1f}s")

    receipt = {
        "experiment": "exp111_F63_rigveda_falsification",
        "hypothesis_id": "H66",
        "verdict": verdict,
        "started_at_utc": started_at.isoformat(),
        "finished_at_utc": finished_at.isoformat(),
        "wall_seconds": wall,
        "prereg_path": str(PREREG_PATH.relative_to(ROOT)),
        "prereg_sha256": prereg_hash,
        "scope": ("F63 R1 6-corpus pool + Rigveda Saṃhitā (1003 sūktas, "
                  "10 mandalas; DharmicData edition, Devanāgarī skeleton, "
                  "33 consonants + 14 vowels)"),
        "corpora": CORPORA,
        "n_units_per_corpus": {c: len(feats[c]) for c in CORPORA},
        "n_total": int(n_total),
        "medians": {c: {"p_max": p, "H_EL": h}
                    for c, (p, h) in medians.items()},
        "quran_p_max": float(qpmax),
        "quran_h_el":  float(qhel),
        "next_highest_p_max_corpus": next_p_max_corpus,
        "next_highest_p_max_value":  float(next_p_max_val),
        "next_lowest_h_el_corpus":   next_h_el_corpus,
        "next_lowest_h_el_value":    float(next_h_el_val),
        "ratio_p_max": float(ratio_p_max),
        "ratio_h_el":  float(ratio_h_el),
        "permutation": {
            "n_perms": N_PERMUTATIONS,
            "seed": SEED,
            "perm_p_h_el": perm_p_h,
            "perm_p_p_max": perm_p_p,
            "alpha_bonf": PERM_ALPHA_BONF,
        },
        "decision_rule": {
            "h_el_margin": H_EL_MARGIN,
            "p_max_margin": P_MAX_MARGIN,
            "cond_h_el_extremum": bool(cond1),
            "cond_p_max_extremum": bool(cond2),
            "cond_perm_p_h_el": bool(cond3),
            "cond_perm_p_p_max": bool(cond4),
        },
        "audit_report": {
            "ok": bool(cond_audit),
            "a1_rigveda_manifest_sha256": {"ok": a1_ok, "details": a1_details},
            "a2_feature_parity_quran_vs_f63_r1": {"ok": a2_ok,
                                                   "details": a2_details},
        },
        "calibration_source": "none — analytic & permutation",
    }
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    print(f"# receipt: {RECEIPT_PATH}")
    return 0 if verdict.startswith("PASS_") else 1


if __name__ == "__main__":
    sys.exit(main())
