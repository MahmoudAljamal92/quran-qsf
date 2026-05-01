"""
expE15_anti_variance — Anti-Variance Manifold formalization.

Hypothesis: the Quran sits at an unusually *low-variance* point in 5-D feature
space relative to Arabic controls. Formalize as: project onto the two
smallest-eigenvalue eigenvectors of the pooled control covariance Σ_ctrl; this
is the "anti-manifold". Measure each unit's anti-distance = norm of its
projection onto this subspace. Quran should sit at the HIGH percentile of the
anti-distance distribution (far from the control centroid along the
low-variance axes).

PRE-REGISTRATION (set before execution):
  Null hypothesis: Quran anti-distance percentile < 95.
  Pass condition:
      - percentile >= 95 AND label-shuffle p <= 0.01 → ANTI_VARIANCE_LAW
      - percentile >= 75 but < 95              → WEAK_ANTI_VARIANCE
      - below that                             → NULL_NO_ANTI_VARIANCE
  Side effects: no mutation of pinned artefacts; outputs under expE15 only.
  Seed: 42.

Notes:
  - Band-A (15<=n_verses<=100) controls only, matching upstream §4 convention.
  - Anti-basis = 2 smallest-eigenvalue eigenvectors of Σ_ctrl (pooled controls).
  - Anti-distance = Mahalanobis distance along the anti-subspace (standardized
    by the eigenvalues so both axes are on the same scale).
  - Label-shuffle null: permute "Quran vs control" membership labels 10 000×.
"""
from __future__ import annotations
import json
import pickle
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUTDIR = ROOT / "results" / "experiments" / "expE15_anti_variance"
OUTDIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

SEED = 42
N_PERM = 10_000
ARABIC_CTRL = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
               "ksucca", "arabic_bible", "hindawi"]
FV_ORDER = ["EL", "VL_CV", "CN", "H_cond", "T"]
BAND_A_LO, BAND_A_HI = 15, 100

t0 = time.time()
state = pickle.load(open(ROOT / "results" / "checkpoints" / "phase_06_phi_m.pkl", "rb"))["state"]
assert state["FEAT_COLS"] == FV_ORDER
CORPORA = state["CORPORA"]; FEATS = state["FEATS"]

# --------------------------------------------------------------- Build 5-D matrices
X_q_rows = []
q_labels = []
for i, u in enumerate(CORPORA["quran"]):
    if BAND_A_LO <= len(u.verses) <= BAND_A_HI:
        X_q_rows.append([FEATS["quran"][i][c] for c in FV_ORDER])
        q_labels.append(getattr(u, "label", f"Q_{i}"))
X_q = np.array(X_q_rows, dtype=float)

X_c_rows, c_labels = [], []
for name in ARABIC_CTRL:
    for i, u in enumerate(CORPORA.get(name, [])):
        if BAND_A_LO <= len(u.verses) <= BAND_A_HI:
            X_c_rows.append([FEATS[name][i][c] for c in FV_ORDER])
            c_labels.append(f"{name}:{getattr(u, 'label', i)}")
X_c = np.array(X_c_rows, dtype=float)

print(f"[E15] Band-A Quran units: {X_q.shape[0]}, Arabic controls: {X_c.shape[0]}")

# --------------------------------------------------------------- Standardise + pooled covariance
# Standardise using combined mean + std to ensure features are on comparable scales
mu = X_c.mean(axis=0)
sd = X_c.std(axis=0, ddof=1); sd[sd == 0] = 1.0
Z_q = (X_q - mu) / sd
Z_c = (X_c - mu) / sd

Sigma = np.cov(Z_c, rowvar=False)
vals, vecs = np.linalg.eigh(Sigma)          # ascending eigenvalues
order_ascending = np.argsort(vals)
vals_asc = vals[order_ascending]
vecs_asc = vecs[:, order_ascending]

print(f"[E15] eigenvalues of Σ_ctrl (standardised, ascending):")
for i, v in enumerate(vals_asc):
    print(f"  λ_{i+1} = {v:.6f}  ({v/vals.sum()*100:.1f}% of variance)")

# --------------------------------------------------------------- Anti-manifold = 2 smallest eigenvectors
anti = vecs_asc[:, :2]                      # shape (5, 2)
anti_vals = vals_asc[:2]                    # shape (2,)

# Standardized projections so both anti axes are unit-variance under the control
proj_c = Z_c @ anti
proj_q = Z_q @ anti

# Mahalanobis distance along anti axes (standardise by sqrt(λ) so variance=1)
lam_safe = np.maximum(anti_vals, 1e-12)
d_c = np.sqrt(((proj_c / np.sqrt(lam_safe)) ** 2).sum(axis=1))
d_q = np.sqrt(((proj_q / np.sqrt(lam_safe)) ** 2).sum(axis=1))
print(f"\n[E15] anti-distances:")
print(f"  control mean={d_c.mean():.4f}, sd={d_c.std(ddof=1):.4f}, max={d_c.max():.4f}")
print(f"  Quran units mean={d_q.mean():.4f}, sd={d_q.std(ddof=1):.4f}, max={d_q.max():.4f}")

# --------------------------------------------------------------- Percentile of mean Quran anti-distance vs control
d_q_mean = float(d_q.mean())
percentile_obs = float((d_c <= d_q_mean).mean() * 100)
print(f"\n[E15] mean Quran anti-distance percentile (vs controls): {percentile_obs:.2f}%")

# --------------------------------------------------------------- Permutation null: swap labels
rng = np.random.default_rng(SEED)
all_Z = np.vstack([Z_q, Z_c])
n_q, n_c = len(Z_q), len(Z_c)
labels_obs = np.concatenate([np.ones(n_q, dtype=int), np.zeros(n_c, dtype=int)])

perm_stats = np.zeros(N_PERM)
for i in range(N_PERM):
    perm_labels = rng.permutation(labels_obs)
    Z_qi = all_Z[perm_labels == 1]; Z_ci = all_Z[perm_labels == 0]
    # Re-estimate Σ on permuted control side
    Sigma_i = np.cov(Z_ci, rowvar=False)
    vals_i, vecs_i = np.linalg.eigh(Sigma_i)
    o = np.argsort(vals_i)
    anti_i = vecs_i[:, o[:2]]; lam_i = np.maximum(vals_i[o[:2]], 1e-12)
    proj_qi = Z_qi @ anti_i
    proj_ci = Z_ci @ anti_i
    d_qi = np.sqrt(((proj_qi / np.sqrt(lam_i)) ** 2).sum(axis=1)).mean()
    perm_stats[i] = d_qi

p_perm = float(((perm_stats >= d_q_mean).sum() + 1) / (N_PERM + 1))
print(f"[E15] label-shuffle p (N={N_PERM}): {p_perm:.4e}   "
      f"(perm null mean={perm_stats.mean():.4f}, obs={d_q_mean:.4f})")

# --------------------------------------------------------------- Verdict
if percentile_obs >= 95 and p_perm <= 0.01:
    verdict = "ANTI_VARIANCE_LAW"
elif percentile_obs >= 75:
    verdict = "WEAK_ANTI_VARIANCE"
else:
    verdict = "NULL_NO_ANTI_VARIANCE"
print(f"\nVerdict: {verdict}")

# --------------------------------------------------------------- Hyperplane equation
# Write the formal anti-manifold equation: for a unit with standardised features
# z = (x - mu)/sd, its anti-projection is a = A^T z, and anti-distance is
# ||diag(1/sqrt(lambda)) A^T z||_2.
A_str = np.array2string(anti, precision=4, suppress_small=True)
mu_str = np.array2string(mu, precision=4, suppress_small=True)
sd_str = np.array2string(sd, precision=4, suppress_small=True)
lam_str = np.array2string(anti_vals, precision=6, suppress_small=True)

# --------------------------------------------------------------- Outputs
report = {
    "experiment_id": "expE15_anti_variance",
    "task": "E15",
    "tier": 4,
    "title": "Anti-Variance Manifold formalization + empirical fit",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "seed": SEED,
    "n_quran_units_bandA":   int(n_q),
    "n_control_units_bandA": int(n_c),
    "feature_order": FV_ORDER,
    "control_mu":  mu.tolist(),
    "control_sd":  sd.tolist(),
    "Sigma_ctrl_eigenvalues_ascending": vals_asc.tolist(),
    "anti_basis_2_smallest":   anti.T.tolist(),   # 2×5
    "anti_lambdas":            anti_vals.tolist(),
    "quran_anti_distance_mean":  d_q_mean,
    "quran_anti_distance_max":   float(d_q.max()),
    "control_anti_distance_mean": float(d_c.mean()),
    "control_anti_distance_max":  float(d_c.max()),
    "quran_percentile_vs_ctrl":   percentile_obs,
    "permutation_p":              p_perm,
    "permutation_n":              N_PERM,
    "verdict":                    verdict,
    "pre_registered_criteria": {
        "null":                  "Quran anti-distance percentile < 95",
        "ANTI_VARIANCE_LAW":     "percentile >= 95 AND perm p <= 0.01",
        "WEAK_ANTI_VARIANCE":    "percentile >= 75 but < 95",
        "NULL_NO_ANTI_VARIANCE": "below that threshold",
        "side_effects":          "no mutation of any pinned artefact; outputs under expE15 only",
    },
    "hyperplane_formula_text":
        f"anti_distance(x) = || diag(1/sqrt(λ_anti)) · Aᵀ · (x - μ)/σ ||_2,  "
        f"A = 2 smallest-eigval eigenvectors of Σ_ctrl "
        f"(features in order {FV_ORDER})",
}
(OUTDIR / "expE15_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
)

# --------------------------------------------------------------- Plot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 2-D anti-manifold scatter (control + Quran)
axes[0].scatter(proj_c[:, 0], proj_c[:, 1], s=10, c="C0", alpha=0.6, label=f"Arabic controls (n={n_c})")
axes[0].scatter(proj_q[:, 0], proj_q[:, 1], s=12, c="red", alpha=0.75,
                label=f"Quran units (n={n_q})")
axes[0].axhline(0, color="k", alpha=0.2); axes[0].axvline(0, color="k", alpha=0.2)
axes[0].set_xlabel(f"anti-axis 1  (λ = {anti_vals[0]:.4f})")
axes[0].set_ylabel(f"anti-axis 2  (λ = {anti_vals[1]:.4f})")
axes[0].set_title(f"Anti-manifold projection (verdict: {verdict})")
axes[0].legend(); axes[0].grid(True, alpha=0.3)

# Distance histogram
axes[1].hist(d_c, bins=30, color="C0", alpha=0.6, label=f"controls (n={n_c})")
axes[1].axvline(d_q_mean, color="red", lw=2,
                label=f"Quran mean = {d_q_mean:.3f} (pct={percentile_obs:.1f}%)")
axes[1].axvline(np.percentile(d_c, 95), color="k", ls="--", alpha=0.5,
                label="control 95th percentile")
axes[1].set_xlabel("anti-distance")
axes[1].set_ylabel("count (control units)")
axes[1].set_title(f"Anti-distance distribution  |  perm p = {p_perm:.2e}")
axes[1].legend(); axes[1].grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig(OUTDIR / "expE15_anti_manifold.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# --------------------------------------------------------------- Markdown
md = [
    "# expE15 — Anti-Variance Manifold",
    "",
    f"**Generated (UTC)**: {report['generated_utc']}",
    f"**Seed**: {SEED}  |  **N perm**: {N_PERM}",
    f"**Quran units (Band-A)**: {n_q}  |  **Arabic control units (Band-A)**: {n_c}",
    f"**Feature order**: {FV_ORDER}",
    "",
    "## Pre-registration",
    "",
    "- **Null**: Quran anti-distance percentile < 95 relative to controls.",
    "- **ANTI_VARIANCE_LAW**: percentile >= 95 AND label-shuffle p <= 0.01.",
    "- **WEAK_ANTI_VARIANCE**: percentile >= 75 but < 95.",
    "- **NULL_NO_ANTI_VARIANCE**: below that.",
    "",
    f"## Verdict — **{verdict}**",
    "",
    "## Key numbers",
    "",
    f"- **Quran mean anti-distance**:   {d_q_mean:.4f}",
    f"- **Control mean anti-distance**: {d_c.mean():.4f}",
    f"- **Quran percentile vs controls**: {percentile_obs:.2f} %",
    f"- **Label-shuffle p (N={N_PERM})**: {p_perm:.3e}",
    f"- **Σ_ctrl eigenvalues (ascending)**: {['%.5f' % v for v in vals_asc]}",
    "",
    "## Anti-basis (2 smallest eigenvectors of Σ_ctrl, rows = eigenvectors)",
    "",
    "```",
    A_str,
    "```",
    "",
    "## Formal statement",
    "",
    "Let `x ∈ R⁵` be the 5-D feature vector of a unit in order `(EL, VL_CV, CN, H_cond, T)`.",
    "Define the standardised feature `z = (x − μ_ctrl) / σ_ctrl`, where `μ_ctrl` and `σ_ctrl` are",
    "the mean and standard deviation vectors over the 6-corpus Band-A Arabic control pool.",
    "Let `A ∈ R^{5×2}` be the two eigenvectors of `Σ_ctrl = Cov(z_ctrl)` with the smallest",
    "eigenvalues `λ₁ ≤ λ₂`. The **anti-distance** of unit `x` is",
    "",
    "```",
    "d_anti(x) = || diag(1/√λ_anti) · Aᵀ · z ||_2",
    "```",
    "",
    "Empirically,",
    f"- μ_ctrl = {mu_str}",
    f"- σ_ctrl = {sd_str}",
    f"- λ_anti = {lam_str}",
    "",
    "## Outputs",
    "",
    "- `expE15_report.json` — all numbers including hyperplane coefficients.",
    "- `expE15_anti_manifold.png` — 2-D anti-projection scatter + distance histogram.",
]
(OUTDIR / "expE15_report.md").write_text("\n".join(md), encoding="utf-8")
print(f"Total runtime: {time.time()-t0:.1f}s")
