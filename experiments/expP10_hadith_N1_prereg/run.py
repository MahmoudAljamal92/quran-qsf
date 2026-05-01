"""
expP10_hadith_N1_prereg/run.py
==============================
Pre-registered N1: EL one-feature classifier (Quran-vs-Arabic-ctrl-trained)
generalises to hadith Bukhari as held-out test.

Pre-registered in PREREG.md (frozen 2026-04-26, v7.9-cand patch E).

Reads:  phase_06_phi_m.pkl ::state[CORPORA]
Writes: results/experiments/expP10_hadith_N1_prereg/expP10_hadith_N1_prereg.json
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

EXP = "expP10_hadith_N1_prereg"
SEED = 42
SVM_C = 1.0
N_BOOT = 500
MIN_VERSES = 2
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


def _verdict(auc: float) -> str:
    if auc >= 0.97:
        return "PASS_STRONG"
    if auc >= 0.95:
        return "PASS"
    if auc >= 0.90:
        return "PASS_WEAK"
    return "FAIL"


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

    # --- Compute EL per unit ---
    el_q, el_c, el_h = [], [], []
    for u in CORPORA.get("quran", []):
        if len(u.verses) >= MIN_VERSES:
            el_q.append(el_rate(list(u.verses)))
    for name in ARABIC_CTRL:
        for u in CORPORA.get(name, []):
            if len(u.verses) >= MIN_VERSES:
                el_c.append(el_rate(list(u.verses)))
    for u in CORPORA.get("hadith_bukhari", []):
        if len(u.verses) >= MIN_VERSES:
            el_h.append(el_rate(list(u.verses)))

    el_q = np.array(el_q, dtype=float)
    el_c = np.array(el_c, dtype=float)
    el_h = np.array(el_h, dtype=float)
    n_q, n_c, n_h = len(el_q), len(el_c), len(el_h)
    print(f"[{EXP}] n_quran={n_q}  n_ctrl={n_c}  n_hadith={n_h}")
    if n_q < 5 or n_c < 5 or n_h < 5:
        raise RuntimeError(f"Insufficient sample sizes for binding test (q={n_q}, c={n_c}, h={n_h})")

    # --- Fit EL boundary on Quran vs Arabic-ctrl ONLY (hadith held out) ---
    from sklearn.svm import SVC
    from sklearn.metrics import roc_auc_score
    from scipy.stats import mannwhitneyu

    X_train = np.concatenate([el_q, el_c]).reshape(-1, 1)
    y_train = np.concatenate([np.ones(n_q), np.zeros(n_c)])
    svm = SVC(kernel="linear", C=SVM_C, class_weight="balanced", random_state=SEED)
    svm.fit(X_train, y_train)
    w = float(svm.coef_[0][0])
    b = float(svm.intercept_[0])
    boundary_el = -b / w if w != 0 else float("nan")

    # AUC on training
    auc_train = float(roc_auc_score(y_train, svm.decision_function(X_train)))

    # --- HELD-OUT TEST: Quran (positive) vs Hadith (negative) under same boundary ---
    X_test = np.concatenate([el_q, el_h]).reshape(-1, 1)
    y_test = np.concatenate([np.ones(n_q), np.zeros(n_h)])
    auc_holdout = float(roc_auc_score(y_test, svm.decision_function(X_test)))

    # --- Mann-Whitney U: Quran EL > Hadith EL ---
    mw = mannwhitneyu(el_q, el_h, alternative="greater")
    mw_p = float(mw.pvalue)

    # --- Bootstrap 95% CI on the held-out AUC ---
    rng = np.random.RandomState(SEED)
    aucs = []
    for _ in range(N_BOOT):
        iq = rng.choice(n_q, n_q, replace=True)
        ih = rng.choice(n_h, n_h, replace=True)
        Xb = np.concatenate([el_q[iq], el_h[ih]]).reshape(-1, 1)
        yb = np.concatenate([np.ones(n_q), np.zeros(n_h)])
        try:
            aucs.append(float(roc_auc_score(yb, svm.decision_function(Xb))))
        except Exception:
            aucs.append(float("nan"))
    aucs = np.array([a for a in aucs if np.isfinite(a)])
    ci = {
        "median": float(np.median(aucs)) if aucs.size else None,
        "ci_lo": float(np.percentile(aucs, 2.5)) if aucs.size else None,
        "ci_hi": float(np.percentile(aucs, 97.5)) if aucs.size else None,
        "n_valid": int(aucs.size),
    }

    verdict = _verdict(auc_holdout)
    print(f"[{EXP}] EL_q mean = {el_q.mean():.4f}  EL_c mean = {el_c.mean():.4f}  EL_h mean = {el_h.mean():.4f}")
    print(f"[{EXP}] Boundary EL = {boundary_el:.4f}")
    print(f"[{EXP}] AUC train (Quran vs Arabic-ctrl)  = {auc_train:.4f}")
    print(f"[{EXP}] AUC holdout (Quran vs Hadith)     = {auc_holdout:.4f}  [VERDICT: {verdict}]")
    print(f"[{EXP}] Bootstrap 95%% CI on holdout AUC: [{ci['ci_lo']:.4f}, {ci['ci_hi']:.4f}]")
    print(f"[{EXP}] MW p (Quran EL > Hadith EL): {mw_p:.4e}")

    record = {
        "experiment": EXP,
        "prereg_sha256": _prereg_hash(),
        "n_quran": n_q,
        "n_ctrl": n_c,
        "n_hadith": n_h,
        "el_quran_mean": float(el_q.mean()),
        "el_quran_std": float(el_q.std(ddof=1)),
        "el_hadith_mean": float(el_h.mean()),
        "el_hadith_std": float(el_h.std(ddof=1)),
        "el_ctrl_mean": float(el_c.mean()),
        "el_ctrl_std": float(el_c.std(ddof=1)),
        "boundary_w": w,
        "boundary_b": b,
        "boundary_el_threshold": boundary_el,
        "auc_train_quran_vs_arabic_ctrl": auc_train,
        "auc_holdout_quran_vs_hadith": auc_holdout,
        "auc_holdout_quran_vs_hadith_ci": ci,
        "mw_p_quran_gt_hadith": mw_p,
        "verdict": verdict,
        "wall_time_s": time.time() - t0,
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    print(f"[{EXP}] -> {out / (EXP + '.json')}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
