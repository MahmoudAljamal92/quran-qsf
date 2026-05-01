"""
exp36_TxEL_seed_metaCI/run.py
=============================
Meta-CI over the (T, EL) 2-feature classifier — replicates exp22 across
5 independent random seeds so the reported AUC carries a *between-seed*
variance bound, not just the within-seed 5-fold CV variance.

Motivation: exp22 reports AUC = 0.9979 ± 0.0018 (nested-CV, 5 folds,
SEED = 42). That ±0.0018 is the across-fold dispersion at a single seed;
it does not bound across-seed dispersion (different fold assignments).
For a PNAS-grade claim we need to show the AUC is stable across
independent randomizations of the outer and inner fold splits.

Protocol (byte-exact parity with exp22 per seed)
    Seeds: [42, 43, 44, 45, 46]
    Per seed:
        outer = StratifiedKFold(5, shuffle=True, random_state=seed)
        inner = StratifiedKFold(3, shuffle=True, random_state=seed+1)
        StandardScaler fit inside each inner-train fold (no leakage)
        LogisticRegression C tuned over {0.01, 0.1, 1.0, 10.0}
        best-C refit on full outer-train with fresh StandardScaler
        AUC = roc_auc_score on outer-test, averaged across 5 folds
    Reported:
        AUC_per_seed, AUC_mean_across_seeds, AUC_std_across_seeds,
        total N_folds = 25, all within-fold AUCs
    Verdict: "META_STABLE" iff AUC_std_across_seeds < 0.005

Reads (integrity-checked):
    phase_06_phi_m.pkl  (CORPORA, FEAT_COLS)

Writes ONLY under results/experiments/exp36_TxEL_seed_metaCI/:
    exp36_TxEL_seed_metaCI.json
    self_check_<ts>.json
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

EXP = "exp36_TxEL_seed_metaCI"

ARABIC_FAMILY = [
    "quran", "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
BAND_A_LO, BAND_A_HI = 15, 100
SEEDS = [42, 43, 44, 45, 46]
C_GRID = [0.01, 0.1, 1.0, 10.0]


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


def _nested_cv_single_seed(X, y, seed: int) -> dict:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold
    from sklearn.preprocessing import StandardScaler

    outer = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    aucs: list[float] = []
    best_Cs: list[float] = []
    for tr, te in outer.split(X, y):
        Xtr, Xte, ytr, yte = X[tr], X[te], y[tr], y[te]
        inner = StratifiedKFold(n_splits=3, shuffle=True, random_state=seed + 1)
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
    return {
        "seed": seed,
        "auc_fold": [float(a) for a in aucs],
        "best_C_per_fold": [float(c) for c in best_Cs],
        "auc_mean_within_seed": float(np.mean(aucs)),
        "auc_std_within_seed": float(np.std(aucs, ddof=1)),
    }


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    CORPORA = state["CORPORA"]
    feat_cols = list(state["FEAT_COLS"])

    X, y = _collect_TxEL(CORPORA, feat_cols)
    if len(X) == 0 or y.sum() == 0 or (y == 0).sum() == 0:
        raise RuntimeError("insufficient data for 2D classifier")

    per_seed: list[dict] = []
    for s in SEEDS:
        print(f"[{EXP}] running seed={s} ...", flush=True)
        per_seed.append(_nested_cv_single_seed(X, y, s))

    seed_means = np.array([r["auc_mean_within_seed"] for r in per_seed])
    # Flatten all within-seed fold AUCs (25 folds total)
    all_fold_aucs = [
        a for r in per_seed for a in r["auc_fold"]
    ]

    meta_mean = float(seed_means.mean())
    meta_std = float(seed_means.std(ddof=1))
    all_fold_mean = float(np.mean(all_fold_aucs))
    all_fold_std = float(np.std(all_fold_aucs, ddof=1))
    min_auc = float(min(all_fold_aucs))
    max_auc = float(max(all_fold_aucs))
    verdict = "META_STABLE" if meta_std < 0.005 else (
        "META_MARGINAL" if meta_std < 0.01 else "META_UNSTABLE"
    )

    report = {
        "experiment": EXP,
        "features": ["T", "EL"],
        "n_total": int(len(X)),
        "n_quran": int(y.sum()),
        "n_ctrl": int((y == 0).sum()),
        "seeds": SEEDS,
        "protocol": (
            "byte-exact parity with exp22 / _build.py Cell 71 per seed: "
            "outer StratifiedKFold(5, shuffle=True, random_state=seed), "
            "inner StratifiedKFold(3, shuffle=True, random_state=seed+1), "
            "StandardScaler fit inside each inner-train fold, "
            "LogisticRegression C tuned over {0.01, 0.1, 1.0, 10.0}, "
            "best-C refit on full outer-train with fresh StandardScaler."
        ),
        "per_seed": per_seed,
        "meta_summary": {
            "auc_mean_across_seeds": meta_mean,
            "auc_std_across_seeds": meta_std,
            "auc_min_across_seeds": float(seed_means.min()),
            "auc_max_across_seeds": float(seed_means.max()),
            "n_seeds": len(SEEDS),
            "n_folds_total": len(all_fold_aucs),
            "all_folds_mean": all_fold_mean,
            "all_folds_std": all_fold_std,
            "all_folds_min": min_auc,
            "all_folds_max": max_auc,
        },
        "verdict": verdict,
        "baseline_5D_nested_AUC_locked": 0.998,
        "note": (
            "Meta-CI across 5 independent seeds. A verdict of "
            "META_STABLE (std < 0.005) supports a Zipf-class parsimony "
            "claim at PNAS-grade precision: the (T, EL) fingerprint "
            "classifies Quran vs Arabic ctrl at AUC ~ 0.998 regardless "
            "of the fold randomisation."
        ),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # -------------------- console ---------------------------------------- #
    print(f"[{EXP}] wrote {outfile}")
    print(f"[{EXP}] --- per-seed within-CV means ---")
    for r in per_seed:
        print(f"   seed={r['seed']}  AUC={r['auc_mean_within_seed']:.6f} "
              f"+/- {r['auc_std_within_seed']:.6f}  "
              f"(folds={r['auc_fold']})")
    print(f"[{EXP}] meta-mean AUC = {meta_mean:.6f} +/- {meta_std:.6f} "
          f"(across {len(SEEDS)} seeds)")
    print(f"[{EXP}] all-folds AUC range = "
          f"[{min_auc:.6f}, {max_auc:.6f}]  "
          f"(N_folds = {len(all_fold_aucs)})")
    print(f"[{EXP}] verdict: {verdict}")

    self_check_end(pre, EXP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
