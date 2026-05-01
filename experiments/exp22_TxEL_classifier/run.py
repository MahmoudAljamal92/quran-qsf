"""
exp22_TxEL_classifier/run.py
============================
Two-feature classifier: can the (T, EL) pair alone separate Quran vs
Arabic-control Band-A surahs with AUC comparable to the locked 5-D D09
(AUC = 0.998, nested 5-fold)?

Motivation: the locked 5-D Mahalanobis classifier uses EL, VL_CV, CN,
H_cond, T. External review (2026-04-20) suggests that (T, EL) alone may
carry most of the signal. If AUC >= 0.97 under honest nested CV, the
paper can offer a Zipf-level parsimony claim: two scalar features, no
CamelTools root analyser, no stopword list.

Reads (integrity-checked):
  - phase_06_phi_m.pkl   (CORPORA, FEAT_COLS)

Writes ONLY under results/experiments/exp22_TxEL_classifier/:
  - exp22_TxEL_classifier.json
"""
from __future__ import annotations

import json
import sys
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
from src import features as ft  # noqa: E402

EXP = "exp22_TxEL_classifier"

ARABIC_FAMILY = [
    "quran", "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
BAND_A_LO, BAND_A_HI = 15, 100  # matches notebooks/ultimate/_build.py:1129
SEED = 42


def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


def _collect_TxEL(CORPORA, feat_cols):
    idx_T = feat_cols.index("T")
    idx_EL = feat_cols.index("EL")
    X, y = [], []
    for c in ARABIC_FAMILY:
        units = _band_a(CORPORA.get(c, []))
        for u in units:
            try:
                f5 = ft.features_5d(u.verses)
                X.append([f5[idx_T], f5[idx_EL]])
                y.append(1 if c == "quran" else 0)
            except Exception:
                continue
    return np.asarray(X, dtype=float), np.asarray(y, dtype=int)


def main() -> int:
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import roc_auc_score
        from sklearn.model_selection import StratifiedKFold
        from sklearn.preprocessing import StandardScaler
    except ImportError as e:
        print(f"[{EXP}] sklearn required: {e}")
        return 2

    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    CORPORA = state["CORPORA"]
    feat_cols = list(state["FEAT_COLS"])

    X, y = _collect_TxEL(CORPORA, feat_cols)
    if len(X) == 0 or y.sum() == 0 or (y == 0).sum() == 0:
        raise RuntimeError("insufficient data for 2D classifier")

    # Byte-exact parity with _build.py Cell 71 (D09 nested-CV protocol):
    # outer StratifiedKFold(5) with random_state=SEED; inner StratifiedKFold(3)
    # with random_state=SEED+1; StandardScaler fit inside each INNER train fold
    # (no leakage); LogisticRegression C tuned over {0.01, 0.1, 1.0, 10.0};
    # best-C refit on full outer-train with a fresh StandardScaler, evaluated
    # on outer-test.
    outer = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    C_GRID = [0.01, 0.1, 1.0, 10.0]
    aucs, best_Cs = [], []
    for tr, te in outer.split(X, y):
        Xtr, Xte, ytr, yte = X[tr], X[te], y[tr], y[te]
        inner = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED + 1)
        best, best_C = -np.inf, 1.0
        for C in C_GRID:
            ias = []
            for itr, ite in inner.split(Xtr, ytr):
                sc_in = StandardScaler().fit(Xtr[itr])
                clf = LogisticRegression(C=C, max_iter=2000).fit(
                    sc_in.transform(Xtr[itr]), ytr[itr]
                )
                ias.append(roc_auc_score(
                    ytr[ite],
                    clf.predict_proba(sc_in.transform(Xtr[ite]))[:, 1],
                ))
            m = float(np.mean(ias))
            if m > best:
                best, best_C = m, C
        sc = StandardScaler().fit(Xtr)
        clf = LogisticRegression(C=best_C, max_iter=2000).fit(
            sc.transform(Xtr), ytr
        )
        aucs.append(
            roc_auc_score(yte, clf.predict_proba(sc.transform(Xte))[:, 1])
        )
        best_Cs.append(best_C)

    auc_mean = float(np.mean(aucs))
    auc_std = float(np.std(aucs, ddof=1))

    report = {
        "experiment": EXP,
        "seed": SEED,
        "features": ["T", "EL"],
        "n_total": int(len(X)),
        "n_quran": int(y.sum()),
        "n_ctrl": int((y == 0).sum()),
        "protocol": (
            "nested-CV byte-exact parity with _build.py Cell 71: outer "
            "StratifiedKFold(5, SEED), inner StratifiedKFold(3, SEED+1), "
            "StandardScaler fit inside each inner-train fold, "
            "LogisticRegression C tuned over {0.01, 0.1, 1.0, 10.0}, best-C "
            "refit on full outer-train with a fresh StandardScaler."
        ),
        "auc_fold": [float(a) for a in aucs],
        "best_C_per_fold": [float(c) for c in best_Cs],
        "auc_mean": auc_mean,
        "auc_std": auc_std,
        "baseline_5D_nested_AUC_locked": 0.998,
        "note": (
            "Two-feature (T, EL) classifier vs 5-D baseline D09 = 0.998 using "
            "the IDENTICAL nested-CV protocol (Cell 71). Fair comparison."
        ),
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(
        f"[{EXP}] AUC (T,EL) nested-CV = {auc_mean:.4f} +/- {auc_std:.4f} "
        f"(locked 5-D nested = 0.998)"
    )
    print(f"[{EXP}] per-fold best C = {best_Cs}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
