"""
expP13_loco_el/run.py
=====================
Leave-one-corpus-out ablation on the full-114-Quran EL classifier.

Pre-registered in PREREG.md (frozen 2026-04-26, v7.9-cand patch E).

Reads:  phase_06_phi_m.pkl ::state[CORPORA]
Writes: results/experiments/expP13_loco_el/expP13_loco_el.json

AUDIT FIX H5 (2026-04-26): all AUCs reported by this experiment are
IN-SAMPLE (the linear SVM fits on the same `(Xb, yb)` it then scores).
The JSON now exposes them under the explicit key `auc_in_sample` and
keeps the legacy key `auc` as a backward-compatible alias for
downstream consumers. A genuine out-of-sample AUC for the EL classifier
lives in the cross-validated experiment family (`exp22`, `exp36`,
`exp93`); this experiment is a deliberately in-sample LOCO robustness
check and the verdict thresholds (ROBUST_STRONG/ROBUST/etc.) are
pre-registered against the in-sample number.
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
    load_phase, safe_output_dir, self_check_begin, self_check_end,
)
from src.features import el_rate  # noqa: E402

EXP = "expP13_loco_el"
SEED = 42
SVM_C = 1.0
MIN_VERSES = 2
# AUDIT FIX F3b (2026-04-26): `hadith_bukhari` REMOVED from ARABIC_CTRL.
# Rationale (matches src/clean_pipeline.ARABIC_CORPORA_FOR_CONTROL,
# src/extended_tests*.py, and the notebook quarantine policy at v5):
#   Sahih al-Bukhari quotes the Quran verbatim by design, so including
#   it as a "control" inflates the EL-classifier baseline AUC (the
#   classifier sees Quran-shadow examples on the negative side and
#   hardens its decision boundary). The L1 audit caught this leak.
# Note: this drops the LOCO budget from 7 holdouts to 6.
ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


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

    # --- Compute EL per unit, group by corpus ---
    el_q = []
    el_per_corpus: dict[str, list[float]] = {c: [] for c in ARABIC_CTRL}
    for u in CORPORA.get("quran", []):
        if len(u.verses) >= MIN_VERSES:
            el_q.append(el_rate(list(u.verses)))
    for name in ARABIC_CTRL:
        for u in CORPORA.get(name, []):
            if len(u.verses) >= MIN_VERSES:
                el_per_corpus[name].append(el_rate(list(u.verses)))
    el_q = np.array(el_q, dtype=float)
    el_per_corpus = {k: np.array(v, dtype=float) for k, v in el_per_corpus.items()}
    n_q = len(el_q)
    print(f"[{EXP}] n_quran={n_q}")
    for k, v in el_per_corpus.items():
        print(f"[{EXP}]   n_{k:18s}={len(v)}")

    # --- Baseline: all 7 ctrl corpora ---
    from sklearn.svm import SVC
    from sklearn.metrics import roc_auc_score

    el_c_all = np.concatenate(list(el_per_corpus.values()))
    n_c_all = len(el_c_all)
    Xb = np.concatenate([el_q, el_c_all]).reshape(-1, 1)
    yb = np.concatenate([np.ones(n_q), np.zeros(n_c_all)])
    svm = SVC(kernel="linear", C=SVM_C, class_weight="balanced", random_state=SEED)
    svm.fit(Xb, yb)
    auc_baseline = float(roc_auc_score(yb, svm.decision_function(Xb)))
    print(f"[{EXP}] Baseline AUC (all {len(ARABIC_CTRL)} ctrl):       {auc_baseline:.4f}")

    # --- LOCO: drop one corpus at a time ---
    loco: dict[str, dict] = {}
    for held_out in ARABIC_CTRL:
        kept = [c for c in ARABIC_CTRL if c != held_out]
        el_c = np.concatenate([el_per_corpus[c] for c in kept])
        Xl = np.concatenate([el_q, el_c]).reshape(-1, 1)
        yl = np.concatenate([np.ones(n_q), np.zeros(len(el_c))])
        svm_l = SVC(kernel="linear", C=SVM_C, class_weight="balanced", random_state=SEED)
        svm_l.fit(Xl, yl)
        auc_l = float(roc_auc_score(yl, svm_l.decision_function(Xl)))
        loco[held_out] = {
            # H5: explicit honest label + legacy alias.
            "auc_in_sample": auc_l,
            "auc": auc_l,
            "n_ctrl_remaining": int(len(el_c)),
            "delta_vs_baseline": auc_l - auc_baseline,
        }
        print(f"[{EXP}]   drop {held_out:18s}  AUC = {auc_l:.4f}  "
              f"(Δ = {auc_l - auc_baseline:+.4f})")

    # --- Verdict (pre-registered against in-sample AUC; see H5 note) ---
    aucs_loco = [v["auc_in_sample"] for v in loco.values()]
    min_auc = float(min(aucs_loco))
    if min_auc >= 0.97:
        verdict = "ROBUST_STRONG"
    elif min_auc >= 0.95:
        verdict = "ROBUST"
    elif min_auc >= 0.90:
        verdict = "ROBUST_WEAK"
    else:
        verdict = "FRAGILE"

    print(f"[{EXP}] min LOCO AUC (in-sample) = {min_auc:.4f}  -> verdict: {verdict}")

    record = {
        "experiment": EXP,
        "prereg_sha256": _prereg_hash(),
        "n_quran": n_q,
        # H5: explicit honest labels + legacy aliases.
        "baseline_auc_in_sample": auc_baseline,
        "baseline_auc": auc_baseline,
        "loco": loco,
        "min_loco_auc_in_sample": min_auc,
        "min_loco_auc": min_auc,
        "max_loco_auc_in_sample": float(max(aucs_loco)),
        "max_loco_auc": float(max(aucs_loco)),
        "mean_loco_auc_in_sample": float(np.mean(aucs_loco)),
        "mean_loco_auc": float(np.mean(aucs_loco)),
        "verdict": verdict,
        "verdict_basis": "in_sample_auc",  # H5: be explicit
        "wall_time_s": time.time() - t0,
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] -> {out / (EXP + '.json')}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
