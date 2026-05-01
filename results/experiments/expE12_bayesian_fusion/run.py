"""
expE12_bayesian_fusion — Bayesian channel fusion on the Adiyat 864 enumeration.
Converts the composite detector from ad-hoc logistic voting into a calibrated
posterior P(edit | evidence) via (i) KDE-estimated class-conditional densities,
(ii) naive Bayes (assuming conditional independence), (iii) Gaussian-copula
correction if residual correlations exceed |ρ|=0.3.

PRE-REGISTRATION (set before execution):
  Null hypothesis:
      Bayesian Brier score >= voting-rule Brier score (complexity not justified).
  Pass condition:
      Bayesian Brier <= logistic-vote Brier − 0.01 AND calibration ECE <= 0.10
      → BAYES_CALIBRATED.
      Below threshold → NULL_NO_CALIBRATION_GAIN.
  Side effects:
      No mutation of any pinned artefact; outputs under expE12 folder only.
  Seed: 42.

Evaluated at window N=5 (E11 peak); re-uses E11 channel definitions.
"""
from __future__ import annotations

import importlib.util
import json
import pickle
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import norm
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, GroupKFold
from sklearn.metrics import brier_score_loss, roc_auc_score, log_loss
from sklearn.neighbors import KernelDensity

warnings.filterwarnings("ignore")

ROOT = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUTDIR = ROOT / "results" / "experiments" / "expE12_bayesian_fusion"
OUTDIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

SEED = 42
WINDOW_N = 5
ADIYAT_LABEL = "Q:100"

# Reuse channels + helpers from E11
E11_PATH = ROOT / "results" / "experiments" / "expE11_local_window" / "run.py"
spec = importlib.util.spec_from_file_location("expE11_run", E11_PATH)
e11 = importlib.util.module_from_spec(spec)
sys.modules["expE11_run"] = e11
spec.loader.exec_module(e11)
channels_pair, CHANNEL_NAMES = e11.channels_pair, e11.CHANNEL_NAMES
enumerate_864, window_text = e11.enumerate_864, e11.window_text

# --------------------------------------------------------------- LOAD
t0 = time.time()
state = pickle.load(open(ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl", "rb"))["state"]
adiyat = next(u for u in state["CORPORA"]["quran"] if getattr(u, "label", "") == ADIYAT_LABEL)
canon_verses = list(adiyat.verses)
v0 = canon_verses[0]
variants = enumerate_864(v0)
V_EDIT, V_FAR = 0, len(canon_verses) - 1
print(f"Loaded in {time.time()-t0:.2f}s — {len(variants)} variants, N={WINDOW_N}")

# --------------------------------------------------------------- FEATURES
def compute_features(N):
    X_sig = np.zeros((len(variants), len(CHANNEL_NAMES)))
    X_null = np.zeros((len(variants), len(CHANNEL_NAMES)))
    cls = []
    for i, v in enumerate(variants):
        var_verses = list(canon_verses); var_verses[0] = v["new_v0"]
        X_sig[i] = channels_pair(window_text(canon_verses, V_EDIT, N),
                                  window_text(var_verses,   V_EDIT, N),
                                  canon_verses, var_verses)
        X_null[i] = channels_pair(window_text(canon_verses, V_FAR, N),
                                   window_text(var_verses,   V_FAR, N),
                                   canon_verses, var_verses)
        cls.append(v["class"])
    X = np.vstack([X_sig, X_null])
    y = np.concatenate([np.ones(len(X_sig)), np.zeros(len(X_null))]).astype(int)
    g = np.array(cls + cls)
    mu = X_null.mean(axis=0); sd = X_null.std(axis=0, ddof=1); sd[sd == 0] = 1.0
    Xz = (X - mu) / sd
    return Xz, y, g

Xz, y, groups = compute_features(WINDOW_N)
print(f"X={Xz.shape}, y={y.shape}")

# --------------------------------------------------------------- RESIDUAL CORRELATION
# Correlation of features among CLASS-1 (edit) and CLASS-0 (null) samples separately
def class_corr(Xz, y, cls):
    Xc = Xz[y == cls]
    if Xc.shape[0] < 3: return np.zeros((Xz.shape[1], Xz.shape[1]))
    # guard against zero-variance columns (e.g., LEN_DIFF at N>=5)
    sd = Xc.std(axis=0, ddof=1)
    Xc = Xc[:, sd > 1e-9]  # drop degenerate
    if Xc.shape[1] < 2: return None
    return np.corrcoef(Xc.T)

C_edit = class_corr(Xz, y, 1)
C_null = class_corr(Xz, y, 0)
max_offdiag = 0.0
for C in (C_edit, C_null):
    if C is None: continue
    off = C[np.triu_indices_from(C, k=1)]
    if off.size:
        max_offdiag = max(max_offdiag, float(np.abs(off).max()))
print(f"Max off-diagonal residual correlation: |rho| = {max_offdiag:.4f}")

COPULA_CORRECTION_NEEDED = max_offdiag > 0.3
print(f"Copula correction needed: {COPULA_CORRECTION_NEEDED}")

# --------------------------------------------------------------- NAIVE-BAYES with KDE
class KDENaiveBayes:
    def __init__(self, bandwidth: float = 0.25):
        self.bandwidth = bandwidth
        self.log_prior_ = None
        self.kdes_ = {}
        self.keep_dims_ = None

    def fit(self, X, y):
        self.classes_ = np.array(sorted(np.unique(y)))
        # Keep only dimensions with variance in BOTH classes
        keep = np.ones(X.shape[1], dtype=bool)
        for c in self.classes_:
            keep &= X[y == c].std(axis=0, ddof=1) > 1e-9
        # If no dims survive, use all (degenerate handled at predict)
        if keep.sum() == 0: keep = np.ones_like(keep)
        self.keep_dims_ = keep

        self.kdes_ = {}
        for c in self.classes_:
            Xc = X[y == c][:, keep]
            self.kdes_[c] = [KernelDensity(bandwidth=self.bandwidth).fit(
                                Xc[:, d].reshape(-1, 1))
                             for d in range(Xc.shape[1])]
        priors = np.array([(y == c).mean() for c in self.classes_])
        priors = np.clip(priors, 1e-9, 1.0)
        self.log_prior_ = np.log(priors)
        return self

    def log_joint(self, X):
        Xk = X[:, self.keep_dims_]
        lj = np.zeros((X.shape[0], len(self.classes_)))
        for ci, c in enumerate(self.classes_):
            lj[:, ci] = self.log_prior_[ci] + sum(
                self.kdes_[c][d].score_samples(Xk[:, d].reshape(-1, 1))
                for d in range(Xk.shape[1])
            )
        return lj

    def predict_proba(self, X):
        lj = self.log_joint(X)
        # softmax across classes
        m = lj.max(axis=1, keepdims=True)
        e = np.exp(lj - m)
        return e / e.sum(axis=1, keepdims=True)

# --------------------------------------------------------------- Gaussian-copula-corrected NB
class CopulaNB(KDENaiveBayes):
    """Naive Bayes with Gaussian-copula correction over the kept dimensions.
    Uses Φ⁻¹(F_d(x_d)) per class to obtain latent Gaussians; estimates the
    class-conditional correlation matrix; combines log-likelihoods correctly."""

    def fit(self, X, y):
        super().fit(X, y)
        self.Sigma_, self.SigmaInv_, self.logdet_ = {}, {}, {}
        for c in self.classes_:
            Xc = X[y == c][:, self.keep_dims_]
            # Gaussian latent via empirical cdf -> normal quantile
            n, d = Xc.shape
            Z = np.zeros_like(Xc)
            for j in range(d):
                ranks = np.argsort(np.argsort(Xc[:, j])) + 1
                Z[:, j] = norm.ppf(ranks / (n + 1))
            Sigma = np.cov(Z.T) if d > 1 else np.array([[1.0]])
            # regularise
            Sigma = 0.9 * Sigma + 0.1 * np.eye(Sigma.shape[0])
            self.Sigma_[c]     = Sigma
            self.SigmaInv_[c]  = np.linalg.inv(Sigma)
            self.logdet_[c]    = float(np.linalg.slogdet(Sigma)[1])
            # store ranks for empirical cdf on test data
            self._Xtrain_ = X  # needed for per-dim empirical cdf at predict

    def _emp_cdf_quantile(self, X, c):
        """latent Gaussian for each point under class c's empirical cdf."""
        Xc_train = self._Xtrain_[self._Xtrain_y_cache == c][:, self.keep_dims_]
        Xk = X[:, self.keep_dims_]
        n = Xc_train.shape[0]
        Z = np.zeros_like(Xk)
        for j in range(Xk.shape[1]):
            r = np.array([(Xc_train[:, j] <= v).sum() for v in Xk[:, j]])
            r = np.clip(r, 1, n)
            Z[:, j] = norm.ppf(r / (n + 1))
        return Z

    def fit_with_y(self, X, y):
        self._Xtrain_y_cache = y
        return self.fit(X, y)

    def log_joint(self, X):
        Xk = X[:, self.keep_dims_]
        d = Xk.shape[1]
        lj = np.zeros((X.shape[0], len(self.classes_)))
        for ci, c in enumerate(self.classes_):
            # marginal log-density from KDE (naive part)
            log_marg = sum(
                self.kdes_[c][j].score_samples(Xk[:, j].reshape(-1, 1))
                for j in range(d)
            )
            # copula correction: - 0.5 * z' (Sigma^-1 - I) z - 0.5 log|Sigma|
            Z = self._emp_cdf_quantile(X, c)
            corr = -0.5 * np.einsum("ij,jk,ik->i",
                                    Z, self.SigmaInv_[c] - np.eye(d), Z) \
                   - 0.5 * self.logdet_[c]
            lj[:, ci] = self.log_prior_[ci] + log_marg + corr
        return lj

# --------------------------------------------------------------- Compare: L2 logistic baseline vs KDE-NB vs CopulaNB
def evaluate(model_factory, name, Xz, y, groups, n_splits=4):
    t = time.time()
    uniq = np.unique(groups)
    if len(uniq) >= n_splits:
        splits = list(GroupKFold(n_splits=n_splits).split(Xz, y, groups))
    else:
        splits = list(StratifiedKFold(n_splits=n_splits, shuffle=True,
                                      random_state=SEED).split(Xz, y))
    aucs, briers, lls = [], [], []
    probas = np.zeros(len(y))
    for tr, te in splits:
        m = model_factory()
        if hasattr(m, "fit_with_y"):
            m.fit_with_y(Xz[tr], y[tr])
        else:
            m.fit(Xz[tr], y[tr])
        p = m.predict_proba(Xz[te])[:, 1] if hasattr(m, "predict_proba") \
            else 1.0 / (1.0 + np.exp(-m.decision_function(Xz[te])))
        probas[te] = p
        aucs.append(roc_auc_score(y[te], p))
        briers.append(brier_score_loss(y[te], np.clip(p, 1e-9, 1 - 1e-9)))
        lls.append(log_loss(y[te], np.clip(p, 1e-9, 1 - 1e-9)))
    # Expected Calibration Error (10 bins)
    bins = np.linspace(0, 1, 11)
    ece = 0.0
    for b in range(10):
        mask = (probas >= bins[b]) & (probas < bins[b + 1])
        if mask.sum() == 0: continue
        pred_mean = probas[mask].mean()
        true_mean = y[mask].mean()
        ece += (mask.sum() / len(y)) * abs(pred_mean - true_mean)
    print(f"  {name:>14}: AUC={np.mean(aucs):.4f}, Brier={np.mean(briers):.4f}, "
          f"log-loss={np.mean(lls):.4f}, ECE={ece:.4f}, {time.time()-t:.1f}s")
    return {"name": name,
            "auc_mean":   float(np.mean(aucs)),
            "brier_mean": float(np.mean(briers)),
            "ll_mean":    float(np.mean(lls)),
            "ece":        float(ece),
            "probas":     probas.tolist()}

print("\nCalibration comparison:")
vote = evaluate(lambda: LogisticRegression(penalty="l2", C=1.0, max_iter=2000,
                                           solver="lbfgs", random_state=SEED),
                "L2_logistic (baseline)", Xz, y, groups)
bayes_nb = evaluate(lambda: KDENaiveBayes(bandwidth=0.25),
                    "KDE_NaiveBayes",      Xz, y, groups)
if COPULA_CORRECTION_NEEDED:
    bayes_copula = evaluate(lambda: CopulaNB(bandwidth=0.25),
                            "KDE+Copula_NB",       Xz, y, groups)
else:
    bayes_copula = None
    print("  KDE+Copula_NB: SKIPPED (max |rho| <= 0.3, conditional independence OK)")

# --------------------------------------------------------------- Verdict
brier_vote = vote["brier_mean"]
brier_bayes = min(bayes_nb["brier_mean"],
                  bayes_copula["brier_mean"] if bayes_copula else np.inf)
delta_brier = brier_vote - brier_bayes   # positive = Bayes is better
ece_bayes = min(bayes_nb["ece"],
                bayes_copula["ece"] if bayes_copula else np.inf)
if delta_brier >= 0.01 and ece_bayes <= 0.10:
    verdict = "BAYES_CALIBRATED"
else:
    verdict = "NULL_NO_CALIBRATION_GAIN"

# --------------------------------------------------------------- OUTPUT
report = {
    "experiment_id": "expE12_bayesian_fusion",
    "task": "E12",
    "tier": 3,
    "title": "Bayesian channel fusion — calibrated P(edit | evidence) on Adiyat 864",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "seed": SEED,
    "window_N": WINDOW_N,
    "n_variants": len(variants),
    "channels": CHANNEL_NAMES,
    "residual_corr_max_abs": max_offdiag,
    "copula_correction_used": COPULA_CORRECTION_NEEDED,
    "models": {
        "L2_logistic_baseline": {k: v for k, v in vote.items() if k != "probas"},
        "KDE_NaiveBayes":       {k: v for k, v in bayes_nb.items() if k != "probas"},
        **({"KDE_Copula_NB":    {k: v for k, v in bayes_copula.items() if k != "probas"}}
           if bayes_copula else {}),
    },
    "delta_brier_vote_vs_bayes": float(delta_brier),
    "ece_best_bayes": float(ece_bayes),
    "verdict": verdict,
    "pre_registered_criteria": {
        "null":              "Bayesian Brier >= logistic-vote Brier (no gain)",
        "BAYES_CALIBRATED":  "Bayesian Brier <= logistic-vote Brier − 0.01 AND ECE <= 0.10",
        "NULL_NO_CALIBRATION_GAIN": "below threshold",
        "side_effects": "no mutation of any pinned artefact; outputs under expE12 folder only",
    },
}
(OUTDIR / "expE12_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
)

# --------------------------------------------------------------- Plots
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# ROC comparison
from sklearn.metrics import roc_curve
for res in [vote, bayes_nb] + ([bayes_copula] if bayes_copula else []):
    pb = np.array(res["probas"])
    fpr, tpr, _ = roc_curve(y, pb)
    axes[0].plot(fpr, tpr, label=f"{res['name']} AUC={res['auc_mean']:.4f}")
axes[0].plot([0, 1], [0, 1], "k--", alpha=0.4)
axes[0].set_xlabel("FPR"); axes[0].set_ylabel("TPR")
axes[0].set_title(f"ROC — Bayesian vs logistic (N={WINDOW_N})")
axes[0].legend(); axes[0].grid(True, alpha=0.3)

# Calibration curves (reliability diagrams)
bins = np.linspace(0, 1, 11)
mids = 0.5 * (bins[:-1] + bins[1:])
for res in [vote, bayes_nb] + ([bayes_copula] if bayes_copula else []):
    pb = np.array(res["probas"])
    empirical = []
    for b in range(10):
        mask = (pb >= bins[b]) & (pb < bins[b + 1])
        empirical.append(y[mask].mean() if mask.sum() else np.nan)
    axes[1].plot(mids, empirical, "o-",
                 label=f"{res['name']} ECE={res['ece']:.3f}")
axes[1].plot([0, 1], [0, 1], "k--", alpha=0.4, label="perfect")
axes[1].set_xlabel("predicted probability")
axes[1].set_ylabel("empirical frequency of class 1")
axes[1].set_title("Reliability diagram")
axes[1].legend(); axes[1].grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig(OUTDIR / "expE12_calibration_plots.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --------------------------------------------------------------- Markdown
md = [
    "# expE12 — Bayesian channel fusion (Adiyat 864)",
    "",
    f"**Generated (UTC)**: {report['generated_utc']}",
    f"**Seed**: {SEED}  |  **Window N**: {WINDOW_N}  |  **Variants**: {len(variants)}",
    f"**Channels**: {', '.join(CHANNEL_NAMES)}",
    f"**Max residual |ρ|**: {max_offdiag:.4f}  |  **Copula correction used**: {COPULA_CORRECTION_NEEDED}",
    "",
    "## Pre-registration (set before execution)",
    "",
    "- **Null**: Bayesian Brier ≥ logistic-vote Brier (complexity not justified).",
    "- **BAYES_CALIBRATED**: Bayesian Brier ≤ voting Brier − 0.01 AND ECE ≤ 0.10.",
    "- **NULL_NO_CALIBRATION_GAIN**: below that threshold.",
    "",
    f"## Verdict — **{verdict}** (Brier Δ = {delta_brier:+.4f}, ECE(best bayes) = {ece_bayes:.4f})",
    "",
    "## Model comparison",
    "",
    "| Model | AUC | Brier | log-loss | ECE |",
    "|---|--:|--:|--:|--:|",
    f"| L2 logistic (baseline) | {vote['auc_mean']:.4f} | {vote['brier_mean']:.4f} | "
    f"{vote['ll_mean']:.4f} | {vote['ece']:.4f} |",
    f"| KDE naive Bayes | {bayes_nb['auc_mean']:.4f} | {bayes_nb['brier_mean']:.4f} | "
    f"{bayes_nb['ll_mean']:.4f} | {bayes_nb['ece']:.4f} |",
]
if bayes_copula:
    md.append(f"| KDE + Gaussian copula | {bayes_copula['auc_mean']:.4f} | "
              f"{bayes_copula['brier_mean']:.4f} | {bayes_copula['ll_mean']:.4f} | "
              f"{bayes_copula['ece']:.4f} |")

md.append("")
md.append("## Outputs")
md.append("")
md.append("- `expE12_report.json` — numbers + verdict")
md.append("- `expE12_calibration_plots.png` — ROC + reliability diagram")

(OUTDIR / "expE12_report.md").write_text("\n".join(md), encoding="utf-8")

print(f"\nVerdict: {verdict} (ΔBrier={delta_brier:+.4f}, ECE={ece_bayes:.4f})")
print(f"Total runtime: {time.time()-t0:.1f}s")
