"""
expE10_composite_detector — Optimal-weight composite detector across the 9
forensic channels defined in E11, evaluated on the Adiyat 864-variant
enumeration with group-kfold CV (leave-one-letter-class-out), multi-classifier
comparison, calibration, and per-channel feature importance.

PRE-REGISTRATION (set before execution):
  Null hypothesis:
      Composite detector AUC <= best single-channel AUC + 0.01 at ANY
      tested window N (no gain over best single channel at any scale).
  Pass condition:
      Best composite AUC >= best single-channel AUC + 0.01 on 4-fold
      leave-one-letter-class-out CV at ANY N in {1,2,3,5,8,13}
      → COMPOSITE_GAIN.
      Below that → NULL_NO_GAIN (single channels saturate).
  Side effects:
      No mutation of any pinned artefact; outputs under expE10 folder only.
  Seed:
      NUMPY_SEED = 42.

Builds on expE11 channel definitions; reuses its within-variant null design
(window at V_EDIT vs window at V_FAR). Evaluated across the full window
sweep to find any regime where composite fusion adds real value over any
single channel.
"""
from __future__ import annotations

import gzip
import importlib.util
import json
import pickle
import sys
import time
import warnings
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (roc_auc_score, f1_score, brier_score_loss,
                             roc_curve, precision_recall_curve,
                             average_precision_score)
from sklearn.model_selection import GroupKFold, StratifiedKFold

warnings.filterwarnings("ignore")

ROOT = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUTDIR = ROOT / "results" / "experiments" / "expE10_composite_detector"
OUTDIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

SEED = 42
WINDOWS_N = [1, 2, 3, 5, 8, 13]           # full sweep matching E11
WINDOW_PRIMARY = 5                        # headline window (E11 peak)
ADIYAT_LABEL = "Q:100"

# Reuse channels + helpers from E11 by importing its module
E11_PATH = ROOT / "results" / "experiments" / "expE11_local_window" / "run.py"
spec = importlib.util.spec_from_file_location("expE11_run", E11_PATH)
e11 = importlib.util.module_from_spec(spec)
sys.modules["expE11_run"] = e11
spec.loader.exec_module(e11)

channels_pair   = e11.channels_pair
CHANNEL_NAMES   = e11.CHANNEL_NAMES
enumerate_864   = e11.enumerate_864
window_text     = e11.window_text

# --------------------------------------------------------------- LOAD
t0 = time.time()
state = pickle.load(open(ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl", "rb"))["state"]
adiyat = next(u for u in state["CORPORA"]["quran"] if getattr(u, "label", "") == ADIYAT_LABEL)
canon_verses = list(adiyat.verses)
v0 = canon_verses[0]
variants = enumerate_864(v0)
V_EDIT, V_FAR = 0, len(canon_verses) - 1
print(f"Loaded in {time.time()-t0:.2f}s — {len(variants)} variants; sweeping N in {WINDOWS_N}")

# --------------------------------------------------------------- FEATURE PRECOMPUTE
def compute_features_at_N(N: int):
    X_sig = np.zeros((len(variants), len(CHANNEL_NAMES)))
    X_null = np.zeros((len(variants), len(CHANNEL_NAMES)))
    classes_arr = []
    for i, v in enumerate(variants):
        var_verses = list(canon_verses); var_verses[0] = v["new_v0"]
        csig = window_text(canon_verses, V_EDIT, N)
        vsig = window_text(var_verses,   V_EDIT, N)
        X_sig[i] = channels_pair(csig, vsig, canon_verses, var_verses)
        cnul = window_text(canon_verses, V_FAR, N)
        vnul = window_text(var_verses,   V_FAR, N)
        X_null[i] = channels_pair(cnul, vnul, canon_verses, var_verses)
        classes_arr.append(v["class"])
    X = np.vstack([X_sig, X_null])
    y = np.concatenate([np.ones(len(X_sig)), np.zeros(len(X_null))]).astype(int)
    groups = np.array(classes_arr + classes_arr)
    mu = X_null.mean(axis=0); sd = X_null.std(axis=0, ddof=1); sd[sd == 0] = 1.0
    Xz = (X - mu) / sd
    return X, Xz, y, groups

# --------------------------------------------------------------- COMPOSITES
def evaluate_model(name, model, Xz, y, groups, n_splits=4):
    t = time.time()
    # Leave-one-letter-class-out where possible; fallback to stratified-k
    uniq = np.unique(groups)
    if len(uniq) >= n_splits:
        gkf = GroupKFold(n_splits=n_splits)
        splits = list(gkf.split(Xz, y, groups))
    else:
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=SEED)
        splits = list(skf.split(Xz, y))

    aucs, f1s, briers, aps = [], [], [], []
    probas_all = np.zeros(len(y))
    for fold_idx, (tr, te) in enumerate(splits):
        m = model()
        m.fit(Xz[tr], y[tr])
        if hasattr(m, "predict_proba"):
            proba = m.predict_proba(Xz[te])[:, 1]
        else:
            sc = m.decision_function(Xz[te])
            # simple scale to [0,1] for Brier
            proba = 1.0 / (1.0 + np.exp(-sc))
        probas_all[te] = proba
        aucs.append(roc_auc_score(y[te], proba))
        yhat = (proba >= 0.5).astype(int)
        f1s.append(f1_score(y[te], yhat))
        briers.append(brier_score_loss(y[te], proba))
        aps.append(average_precision_score(y[te], proba))
    print(f"  {name:>14}: AUC={np.mean(aucs):.4f}±{np.std(aucs,ddof=1):.4f}, "
          f"AP={np.mean(aps):.4f}, Brier={np.mean(briers):.4f}, "
          f"{time.time()-t:.1f}s")
    return {
        "name": name,
        "auc_mean":   float(np.mean(aucs)),
        "auc_sd":     float(np.std(aucs, ddof=1)),
        "auc_folds":  [float(a) for a in aucs],
        "f1_mean":    float(np.mean(f1s)),
        "brier_mean": float(np.mean(briers)),
        "ap_mean":    float(np.mean(aps)),
        "probas":     probas_all.tolist(),
        "n_splits":   len(splits),
    }

# --------------------------------------------------------------- SWEEP ACROSS N
print(f"\nWindow sweep: N in {WINDOWS_N}; single-channel AUC and 3-model composite AUC (4-fold group CV)")
sweep_results = {}
any_gain = False
best_gain_N = None
best_gain_delta = -np.inf

def make_models():
    return {
        "L2_logistic": lambda: LogisticRegression(penalty="l2", C=1.0, max_iter=2000,
                                                  solver="lbfgs", random_state=SEED),
        "Fisher_LDA":  lambda: LinearDiscriminantAnalysis(),
        "GradBoost":   lambda: GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                                          random_state=SEED),
    }

for N in WINDOWS_N:
    print(f"\n--- N = {N} ---")
    X_N, Xz_N, y_N, groups_N = compute_features_at_N(N)

    # single-channel AUCs
    s_aucs = {}
    for c, name in enumerate(CHANNEL_NAMES):
        try:
            s_aucs[name] = float(roc_auc_score(y_N, Xz_N[:, c]))
        except Exception:
            s_aucs[name] = float("nan")
    best_single_name = max(s_aucs, key=lambda k: s_aucs[k])
    best_single_auc  = s_aucs[best_single_name]
    print(f"  best single: {best_single_name} = {best_single_auc:.4f}")

    # composite models
    models = make_models()
    mres = {n: evaluate_model(n, fn, Xz_N, y_N, groups_N)
            for n, fn in models.items()}
    best_comp_name = max(mres, key=lambda k: mres[k]["auc_mean"])
    best_comp_auc  = mres[best_comp_name]["auc_mean"]
    delta_N = best_comp_auc - best_single_auc
    if delta_N > best_gain_delta:
        best_gain_delta = delta_N
        best_gain_N = N

    if delta_N >= 0.01:
        any_gain = True

    sweep_results[f"N{N}"] = {
        "window_N":         N,
        "single_aucs":      s_aucs,
        "best_single":      best_single_name,
        "best_single_auc":  best_single_auc,
        "models":           {k: {kk: vv for kk, vv in r.items() if kk != "probas"}
                             for k, r in mres.items()},
        "best_composite":   best_comp_name,
        "best_composite_auc": best_comp_auc,
        "delta_vs_single":  float(delta_N),
        "composite_gain":   bool(delta_N >= 0.01),
    }
    # Keep probas of best composite for downstream plots (headline N)
    if N == WINDOW_PRIMARY:
        primary_probas = np.array(mres[best_comp_name]["probas"])
        primary_y       = y_N
        primary_Xz      = Xz_N
        primary_best_comp = best_comp_name

verdict = "COMPOSITE_GAIN" if any_gain else "NULL_NO_GAIN"
print(f"\nSweep summary: best gain = {best_gain_delta:+.4f} at N={best_gain_N}. "
      f"any_gain(>=0.01)={any_gain}")

# --------------------------------------------------------------- FEATURE IMPORTANCE (at primary N)
# L2 logistic coefficients on full data at primary N
clf_full = LogisticRegression(penalty="l2", C=1.0, max_iter=2000,
                              solver="lbfgs", random_state=SEED).fit(primary_Xz, primary_y)
coef_l2 = clf_full.coef_.ravel()
gb_full = GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                     random_state=SEED).fit(primary_Xz, primary_y)
gb_imp = gb_full.feature_importances_
imp_norm = np.abs(coef_l2) / max(np.abs(coef_l2).sum(), 1e-9)

feature_importance = [
    {"channel": n,
     "l2_coef":             float(coef_l2[i]),
     "l2_coef_abs_norm":    float(imp_norm[i]),
     "gb_importance":       float(gb_imp[i]),
     "single_auc_primary":  float(sweep_results[f"N{WINDOW_PRIMARY}"]["single_aucs"][n])}
    for i, n in enumerate(CHANNEL_NAMES)
]
feature_importance.sort(key=lambda r: -r["gb_importance"])

# --------------------------------------------------------------- Youden threshold at primary N
fpr, tpr, thr = roc_curve(primary_y, primary_probas)
youden = tpr - fpr
j_idx = int(np.argmax(youden))
youden_thr = float(thr[j_idx])
youden_sens = float(tpr[j_idx]); youden_spec = float(1 - fpr[j_idx])
yhat_y = (primary_probas >= youden_thr).astype(int)
f1_y = float(f1_score(primary_y, yhat_y))
print(f"\nYouden-optimal threshold ({primary_best_comp} at N={WINDOW_PRIMARY}): "
      f"thr={youden_thr:.4f}, sens={youden_sens:.4f}, spec={youden_spec:.4f}, F1={f1_y:.4f}")

# --------------------------------------------------------------- OUTPUT
report = {
    "experiment_id": "expE10_composite_detector",
    "task": "E10",
    "tier": 3,
    "title": "Optimal-weight composite detector — 9 forensic channels on Adiyat 864",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "seed": SEED,
    "windows_N": WINDOWS_N,
    "window_primary": WINDOW_PRIMARY,
    "n_variants": len(variants),
    "channels": CHANNEL_NAMES,
    "sweep_per_N": sweep_results,
    "best_gain": {
        "N":     best_gain_N,
        "delta": float(best_gain_delta),
    },
    "verdict": verdict,
    "feature_importance_primary_N": feature_importance,
    "youden_threshold": {
        "threshold":   youden_thr,
        "sensitivity": youden_sens,
        "specificity": youden_spec,
        "f1":          f1_y,
    },
    "pre_registered_criteria": {
        "null":           "Composite AUC <= best-single AUC + 0.01 at every tested N",
        "COMPOSITE_GAIN": "At any tested N, composite AUC >= best-single AUC + 0.01",
        "NULL_NO_GAIN":   "At every N, composite AUC < best-single AUC + 0.01 (single channels saturate)",
        "side_effects":   "no mutation of any pinned artefact; outputs under expE10 folder only",
    },
}
(OUTDIR / "expE10_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
)

# --------------------------------------------------------------- Plots
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# AUC vs N curve (best single, and 3 composites)
Ns = WINDOWS_N
bs_aucs = [sweep_results[f"N{n}"]["best_single_auc"] for n in Ns]
for mname in ["L2_logistic", "Fisher_LDA", "GradBoost"]:
    comp_aucs = [sweep_results[f"N{n}"]["models"][mname]["auc_mean"] for n in Ns]
    comp_sds  = [sweep_results[f"N{n}"]["models"][mname]["auc_sd"]   for n in Ns]
    axes[0].errorbar(Ns, comp_aucs, yerr=comp_sds, fmt="o-", label=mname, capsize=3)
axes[0].plot(Ns, bs_aucs, "s--", color="0.3", label="best single channel")
axes[0].axhline(0.5, color="red", ls=":", alpha=0.5, label="chance")
axes[0].set_xlabel("window half-width N")
axes[0].set_ylabel("4-fold CV AUC")
axes[0].set_title("Composite vs best-single across N")
axes[0].legend(); axes[0].grid(True, alpha=0.3)

# Precision-Recall curve at primary N
precisions, recalls, _ = precision_recall_curve(primary_y, primary_probas)
axes[1].plot(recalls, precisions, color="C3",
             label=f"{primary_best_comp} AP={sweep_results[f'N{WINDOW_PRIMARY}']['models'][primary_best_comp]['ap_mean']:.4f}")
axes[1].set_xlabel("Recall"); axes[1].set_ylabel("Precision")
axes[1].set_title(f"Precision-Recall (best composite at N={WINDOW_PRIMARY})")
axes[1].legend(); axes[1].grid(True, alpha=0.3)

# Feature importance (GB + L2 |coef|)
chn = [r["channel"] for r in feature_importance]
gb_i = [r["gb_importance"] for r in feature_importance]
l2_i = [r["l2_coef_abs_norm"] for r in feature_importance]
ix = np.arange(len(chn))
axes[2].barh(ix - 0.2, gb_i, height=0.4, color="C1", label="GradBoost")
axes[2].barh(ix + 0.2, l2_i, height=0.4, color="C0", label="|L2 coef| (normalised)")
axes[2].set_yticks(ix); axes[2].set_yticklabels(chn)
axes[2].set_xlabel("importance / normalised coefficient")
axes[2].set_title("Per-channel feature importance")
axes[2].legend(); axes[2].grid(True, alpha=0.3, axis="x")
axes[2].invert_yaxis()

fig.tight_layout()
fig.savefig(OUTDIR / "expE10_detector_plots.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --------------------------------------------------------------- Markdown
md = [
    "# expE10 — Optimal-weight composite detector (Adiyat 864)",
    "",
    f"**Generated (UTC)**: {report['generated_utc']}",
    f"**Seed**: {SEED}  |  **Window sweep**: N in {WINDOWS_N}  |  **Primary**: N={WINDOW_PRIMARY}",
    f"**Variants**: {len(variants)}  |  **Channels**: {', '.join(CHANNEL_NAMES)}",
    f"**CV**: 4-fold GroupKFold by letter-class (guttural/labial/emphatic/other)",
    "",
    "_Extension over E11: adds LDA + GradBoost composites and searches the"
    " full N sweep for any regime where composite fusion beats the best single"
    " channel by ≥ 0.01 AUC._",
    "",
    "## Pre-registration (set before execution)",
    "",
    "- **Null**: composite AUC ≤ best-single AUC + 0.01 (no gain).",
    "- **COMPOSITE_GAIN**: best composite AUC ≥ best-single AUC + 0.01.",
    "- **NULL_NO_GAIN**: below that threshold.",
    "- **CV design**: 4-fold GroupKFold grouped by letter class (guttural/labial/emphatic/other).",
    "",
    f"## Verdict — **{verdict}** (best composite−single gain = {best_gain_delta:+.4f} at N={best_gain_N})",
    "",
    "## Sweep summary",
    "",
    "| N | best single (AUC) | L2_logistic | Fisher_LDA | GradBoost | Δ best composite − single | gain ≥ 0.01 |",
    "|--:|---|--:|--:|--:|--:|:-:|",
]
for N in WINDOWS_N:
    s = sweep_results[f"N{N}"]
    md.append(
        f"| {N} | {s['best_single']} ({s['best_single_auc']:.4f}) | "
        f"{s['models']['L2_logistic']['auc_mean']:.4f} | "
        f"{s['models']['Fisher_LDA']['auc_mean']:.4f} | "
        f"{s['models']['GradBoost']['auc_mean']:.4f} | "
        f"{s['delta_vs_single']:+.4f} | {'YES' if s['composite_gain'] else 'no'} |"
    )

md.append("")
md.append(f"## Single-channel AUCs at primary N={WINDOW_PRIMARY}")
md.append("")
md.append("| Channel | AUC |")
md.append("|---|--:|")
for k, v in sorted(sweep_results[f'N{WINDOW_PRIMARY}']['single_aucs'].items(),
                   key=lambda kv: -kv[1]):
    md.append(f"| {k} | {v:.4f} |")

md.append("")
md.append("## Feature importance (sorted by GradBoost)")
md.append("")
md.append("| Channel | GradBoost | \\|L2 coef\\| (norm) | Single-channel AUC (primary N) |")
md.append("|---|--:|--:|--:|")
for r in feature_importance:
    md.append(f"| {r['channel']} | {r['gb_importance']:.4f} | "
              f"{r['l2_coef_abs_norm']:.4f} | {r['single_auc_primary']:.4f} |")

md.append("")
md.append("## Youden-optimal threshold (best composite)")
md.append("")
md.append(f"- **threshold**: {youden_thr:.4f}  |  **sensitivity**: {youden_sens:.4f}  |  "
          f"**specificity**: {youden_spec:.4f}  |  **F1**: {f1_y:.4f}")

md.append("")
md.append("## Outputs")
md.append("")
md.append("- `expE10_report.json` — all numbers")
md.append("- `expE10_detector_plots.png` — ROC + PR + feature-importance")

(OUTDIR / "expE10_report.md").write_text("\n".join(md), encoding="utf-8")

print(f"\nVerdict: {verdict}  (best Δ = {best_gain_delta:+.4f} at N={best_gain_N})")
print(f"Total runtime: {time.time()-t0:.1f}s")
