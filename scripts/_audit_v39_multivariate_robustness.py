"""scripts/_audit_v39_multivariate_robustness.py
=====================================================
V3.9 stress test: how much of the Quran's Arabic-internal 5-D distinctiveness
is from EL alone vs the other 4 features?

Stress test: artificially set poetry corpora's EL feature to match Quran's
(worst case for Quran-distinctiveness under V3.9 — assumes that with real
bayt boundaries, poetry would have the same EL as Quran). Recompute the
5-D AUC and see how much it drops.

If AUC stays > 0.95: the Arabic-internal multivariate finding is robust
to V3.9. Quran's "crush" of Arabic peers is from MULTIPLE features, not
just rhyme.

If AUC drops to < 0.7: most of the Quran's distinctiveness was from
rhyme alone, and V3.9 affects the Arabic-internal claim too.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments._lib import load_phase  # noqa: E402
from src.features import features_5d  # noqa: E402

phi = load_phase("phase_06_phi_m")
state = phi.get("state", phi)
CORPORA = state.get("CORPORA", state.get("corpora"))

print(f"# Available corpora: {list(CORPORA.keys())}")
print(f"# Loaded {sum(len(v) for v in CORPORA.values())} units total")
print()

# Compute the canonical 5-D feature vector per Unit (from src.features)
# Order: [el_rate, vl_cv, cn_rate, h_cond_roots, T = h_cond - h_el]
FEATURE_NAMES = ["EL", "VL_CV", "CN", "H_cond", "T"]


def feats_of(unit) -> np.ndarray | None:
    try:
        v = features_5d(unit.verses)
        if np.all(np.isfinite(v)):
            return v
    except Exception:
        return None
    return None


# Apply band-A filter: 15 ≤ n_verses ≤ 100 for Quran units
BAND_A = (15, 100)


def is_band_a(unit) -> bool:
    n = unit.n_verses() if callable(unit.n_verses) else unit.n_verses
    return BAND_A[0] <= n <= BAND_A[1]


# Build feature matrix
X_quran, X_peers = [], []
peers_corpora = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
                 "ksucca", "hindawi", "arabic_bible"]
for u in CORPORA.get("quran", []):
    if not is_band_a(u):
        continue
    f = feats_of(u)
    if f is not None and np.all(np.isfinite(f)):
        X_quran.append(f)
for c in peers_corpora:
    for u in CORPORA.get(c, []):
        f = feats_of(u)
        if f is not None and np.all(np.isfinite(f)):
            X_peers.append(f)

X_q = np.array(X_quran)
X_p = np.array(X_peers)
print(f"# Quran band-A units: {len(X_q)}")
print(f"# Arabic peer units: {len(X_p)}")
print(f"# 5-D feature names: {FEATURE_NAMES}")
print(f"# Quran feature medians: "
      f"{[round(float(x), 4) for x in np.median(X_q, axis=0)]}")
print(f"# Peer  feature medians: "
      f"{[round(float(x), 4) for x in np.median(X_p, axis=0)]}")

# Build labels
y_q = np.ones(len(X_q))
y_p = np.zeros(len(X_p))
X = np.vstack([X_q, X_p])
y = np.concatenate([y_q, y_p])
print(f"# Combined: {X.shape[0]} units × {X.shape[1]} features")
print()


def hotelling_t2(A: np.ndarray, B: np.ndarray) -> tuple[float, float]:
    """Compute pooled-covariance Hotelling T² for two groups A, B."""
    nA, nB = len(A), len(B)
    p = A.shape[1]
    mA, mB = A.mean(axis=0), B.mean(axis=0)
    SA = np.cov(A, rowvar=False, bias=False)
    SB = np.cov(B, rowvar=False, bias=False)
    Sp = ((nA - 1) * SA + (nB - 1) * SB) / (nA + nB - 2)
    if Sp.ndim == 0:  # scalar from 1-D input
        Sp = np.array([[float(Sp)]])
        diff = (mA - mB).reshape(1)
    else:
        diff = mA - mB
    inv = np.linalg.inv(Sp)
    t2 = float((nA * nB) / (nA + nB) * diff @ inv @ diff)
    d = float(np.sqrt(diff @ inv @ diff))
    return t2, d


def auc_logreg_5fold(X, y, seed=42):
    """Nested 5-fold CV AUC with logistic regression (no calibration)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import roc_auc_score
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    aucs = []
    for tr, te in skf.split(X, y):
        scaler = StandardScaler().fit(X[tr])
        Xtr, Xte = scaler.transform(X[tr]), scaler.transform(X[te])
        clf = LogisticRegression(max_iter=10000, C=1.0).fit(Xtr, y[tr])
        proba = clf.predict_proba(Xte)[:, 1]
        aucs.append(roc_auc_score(y[te], proba))
    return float(np.mean(aucs)), float(np.std(aucs))


print("# === BASELINE: All 5 features ===")
t2_baseline, d_baseline = hotelling_t2(X_q, X_p)
auc_mean, auc_std = auc_logreg_5fold(X, y)
print(f"#   Hotelling T² = {t2_baseline:.2f} (project locked = 3,557)")
print(f"#   Cohen's d    = {d_baseline:.4f} (project locked = 6.66)")
print(f"#   5-D AUC      = {auc_mean:.6f} ± {auc_std:.6f} (project locked = 0.998)")
print()

# Stress test 1: poetry's EL set to Quran's median EL
quran_median_el = float(np.median(X_q[:, 0]))
print(f"# === STRESS TEST 1: Poetry EL artificially set to Quran median ({quran_median_el:.4f}) ===")
print(f"# (Worst case for Quran-distinctiveness if poetry had real bayts)")
X_p_stress = X_p.copy()
X_p_stress[:, 0] = quran_median_el
X_stress = np.vstack([X_q, X_p_stress])
t2_s, d_s = hotelling_t2(X_q, X_p_stress)
auc_s, std_s = auc_logreg_5fold(X_stress, y)
print(f"#   Hotelling T² = {t2_s:.2f} (vs baseline {t2_baseline:.2f}; "
      f"reduction {100 * (1 - t2_s/t2_baseline):.1f}%)")
print(f"#   Cohen's d    = {d_s:.4f}")
print(f"#   5-D AUC      = {auc_s:.6f} ± {std_s:.6f} "
      f"(vs baseline {auc_mean:.6f})")
print()

# Stress test 2: drop EL feature entirely (use only the 4 non-rhyme features)
print(f"# === STRESS TEST 2: Drop EL entirely; classify on 4 features only ===")
print(f"# (How much of Quran-distinctiveness is in NON-RHYME features?)")
X_q4 = X_q[:, 1:]; X_p4 = X_p[:, 1:]
X4 = np.vstack([X_q4, X_p4])
t2_4, d_4 = hotelling_t2(X_q4, X_p4)
auc_4, std_4 = auc_logreg_5fold(X4, y)
print(f"#   Hotelling T² = {t2_4:.2f} (4-D, no EL)")
print(f"#   Cohen's d    = {d_4:.4f}")
print(f"#   4-D AUC      = {auc_4:.6f} ± {std_4:.6f}")
print()

# Stress test 3: EL alone (1-D classifier)
print(f"# === STRESS TEST 3: EL feature alone (1-D classifier) ===")
print(f"# (Project locked: 0.9971 at band-A — but this is the V3.9-affected number)")
X_q1 = X_q[:, :1]; X_p1 = X_p[:, :1]
X1 = np.vstack([X_q1, X_p1])
t2_1, d_1 = hotelling_t2(X_q1, X_p1)
auc_1, std_1 = auc_logreg_5fold(X1, y)
print(f"#   Hotelling T² = {t2_1:.2f} (1-D, EL only)")
print(f"#   Cohen's d    = {d_1:.4f}")
print(f"#   1-D AUC      = {auc_1:.6f} ± {std_1:.6f}")
print()

# Per-feature univariate t-test contributions
print(f"# === Per-feature univariate Cohen's d (Quran vs Arabic peer pool) ===")
for i, name in enumerate(FEATURE_NAMES):
    mq = float(np.mean(X_q[:, i])); mp = float(np.mean(X_p[:, i]))
    sq = float(np.std(X_q[:, i], ddof=1)); sp = float(np.std(X_p[:, i], ddof=1))
    sp_pool = np.sqrt((sq**2 + sp**2) / 2)
    d_i = (mq - mp) / sp_pool
    print(f"#   {name:<14s}: Quran mean = {mq:>8.4f}; Peer mean = {mp:>8.4f}; "
          f"Cohen's d = {d_i:>+7.3f}")

print()
print("# === SUMMARY ===")
print(f"# Baseline 5-D AUC: {auc_mean:.4f} (project locked 0.998)")
print(f"# After stress test 1 (poetry EL = Quran EL): {auc_s:.4f}")
print(f"#   -> {100*(auc_mean-auc_s)/auc_mean:.2f}% relative AUC reduction")
print(f"# After stress test 2 (drop EL entirely): {auc_4:.4f}")
print(f"#   -> {100*(auc_mean-auc_4)/auc_mean:.2f}% relative AUC reduction")
print(f"# EL-only classifier: {auc_1:.4f}")
print()
if auc_s > 0.95 and auc_4 > 0.95:
    print("# ROBUST: even without EL, Arabic-internal AUC stays > 0.95.")
    print("# The Quran's 'crush' of Arabic peers is multivariate, not just rhyme.")
elif auc_s > 0.85 and auc_4 > 0.85:
    print("# MOSTLY ROBUST: AUC drops but stays high. Multivariate signal real.")
else:
    print("# CONCERN: removing EL drops AUC dramatically. Most of the Quran-")
    print("# distinctiveness was from rhyme alone; V3.9 may affect this finding.")
