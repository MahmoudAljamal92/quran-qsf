"""scripts/_audit_v392_full_stress.py
==========================================
V3.9.2 — Run all four stress tests in one pass:

  T1. Hadith Bukhari INCLUDED in Arabic peer pool
  T2. Drop CN feature (Quran-genre-feature ablation)
  T3. Drop EL+CN combined (V3.9-affected + Quran-genre)
  T4. Cross-corpus weight transfer (Quran-blind classifier weights
      from Tanakh-vs-NT, applied to Quran-vs-Arabic-peers)

If T1 keeps AUC > 0.85, the "Quran tops all Arabic" claim survives
hadith inclusion (the most-similar-genre Arabic peer).

If T2/T3 keep AUC > 0.90, the Quran-distinctiveness is not driven by
the Quran-genre-defining CN feature.

If T4 keeps Quran extremal under Quran-blind classifier weights, the
multivariate finding is robust to feature-weight selection bias.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments._lib import load_phase  # noqa: E402
from src.features import features_5d, features_5d_lang_agnostic  # noqa: E402

# ----------------------------------------------------------------------
# Load all corpora
# ----------------------------------------------------------------------
print("# === V3.9.2 FULL STRESS TEST ===\n")
phi = load_phase("phase_06_phi_m")
state = phi.get("state", phi)
CORPORA = state.get("CORPORA", state.get("corpora"))
print(f"# Available corpora: {list(CORPORA.keys())}")

FEATURE_NAMES = ["EL", "VL_CV", "CN", "H_cond", "T"]


def feats_of(unit) -> np.ndarray | None:
    try:
        v = features_5d(unit.verses)
        if np.all(np.isfinite(v)):
            return v
    except Exception:
        return None
    return None


BAND_A = (15, 100)


def is_band_a(unit) -> bool:
    n = unit.n_verses() if callable(unit.n_verses) else unit.n_verses
    return BAND_A[0] <= n <= BAND_A[1]


# Build feature matrices for all relevant corpora
def collect(corpus_name, band_filter=False):
    out = []
    for u in CORPORA.get(corpus_name, []):
        if band_filter and not is_band_a(u):
            continue
        f = feats_of(u)
        if f is not None:
            out.append(f)
    return np.array(out)


X_quran = collect("quran", band_filter=True)
X_jahili = collect("poetry_jahili")
X_islami = collect("poetry_islami")
X_abbasi = collect("poetry_abbasi")
X_ksucca = collect("ksucca")
X_hindawi = collect("hindawi")
X_arabic_bible = collect("arabic_bible")
X_hadith = collect("hadith_bukhari")

X_peers_v391 = np.vstack([X_jahili, X_islami, X_abbasi, X_ksucca,
                          X_hindawi, X_arabic_bible])
X_peers_v392 = np.vstack([X_jahili, X_islami, X_abbasi, X_ksucca,
                          X_hindawi, X_arabic_bible, X_hadith])

print(f"# Quran (band-A) units            : {len(X_quran)}")
print(f"# Arabic peers (V3.9.1, no hadith): {len(X_peers_v391)}")
print(f"# Hadith Bukhari units             : {len(X_hadith)}")
print(f"# Arabic peers (V3.9.2, +hadith)  : {len(X_peers_v392)}")
print()


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def hotelling_t2(A: np.ndarray, B: np.ndarray) -> tuple[float, float]:
    nA, nB = len(A), len(B)
    p = A.shape[1] if A.ndim > 1 else 1
    if A.ndim == 1:
        A = A.reshape(-1, 1)
        B = B.reshape(-1, 1)
    mA, mB = A.mean(axis=0), B.mean(axis=0)
    SA = np.cov(A, rowvar=False, bias=False)
    SB = np.cov(B, rowvar=False, bias=False)
    Sp = ((nA - 1) * SA + (nB - 1) * SB) / (nA + nB - 2)
    if Sp.ndim == 0:
        Sp = np.array([[float(Sp)]])
    Sp = np.atleast_2d(Sp)
    diff = (mA - mB).reshape(-1)
    inv = np.linalg.inv(Sp)
    t2 = float((nA * nB) / (nA + nB) * diff @ inv @ diff)
    d = float(np.sqrt(diff @ inv @ diff))
    return t2, d


def auc_logreg_5fold(X, y, seed=42):
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


def per_feat_d(Xq: np.ndarray, Xp: np.ndarray):
    rows = []
    for i, name in enumerate(FEATURE_NAMES):
        mq, mp = Xq[:, i].mean(), Xp[:, i].mean()
        sq, sp = Xq[:, i].std(ddof=1), Xp[:, i].std(ddof=1)
        sp_pool = np.sqrt((sq**2 + sp**2) / 2)
        d = (mq - mp) / sp_pool if sp_pool > 0 else 0.0
        rows.append((name, mq, mp, d))
    return rows


# ----------------------------------------------------------------------
# T1: HADITH BUKHARI INCLUDED
# ----------------------------------------------------------------------
print("# " + "=" * 70)
print("# T1. HADITH BUKHARI INCLUDED in Arabic peer pool")
print("# " + "=" * 70)

X = np.vstack([X_quran, X_peers_v392])
y = np.concatenate([np.ones(len(X_quran)), np.zeros(len(X_peers_v392))])

t2, d = hotelling_t2(X_quran, X_peers_v392)
auc_m, auc_s = auc_logreg_5fold(X, y)
print(f"#   5-D T²       = {t2:.2f}")
print(f"#   5-D Cohen's d = {d:.4f}")
print(f"#   5-D AUC       = {auc_m:.6f} ± {auc_s:.6f}")
print()
print(f"#   Per-feature univariate Cohen's d (Quran vs +hadith peers):")
for name, mq, mp, di in per_feat_d(X_quran, X_peers_v392):
    print(f"#     {name:<8s}: Quran = {mq:>7.4f}; Peer+H = {mp:>7.4f}; d = {di:>+7.3f}")
print()

# Quran vs ONLY hadith
t2_h, d_h = hotelling_t2(X_quran, X_hadith)
X_qh = np.vstack([X_quran, X_hadith])
y_qh = np.concatenate([np.ones(len(X_quran)), np.zeros(len(X_hadith))])
auc_h, std_h = auc_logreg_5fold(X_qh, y_qh)
print(f"#   *Quran-vs-hadith ONLY*  T² = {t2_h:.2f}; Cohen's d = {d_h:.4f}")
print(f"#   *Quran-vs-hadith ONLY*  AUC = {auc_h:.6f} ± {std_h:.6f}")
print(f"#   Per-feature d (Quran vs hadith only):")
for name, mq, mp, di in per_feat_d(X_quran, X_hadith):
    print(f"#     {name:<8s}: Quran = {mq:>7.4f}; Hadith = {mp:>7.4f}; d = {di:>+7.3f}")
print()


# ----------------------------------------------------------------------
# T2: DROP CN FEATURE (Quran-genre ablation)
# ----------------------------------------------------------------------
print("# " + "=" * 70)
print("# T2. DROP CN FEATURE (Quran-genre-defining feature ablation)")
print("# " + "=" * 70)

drop_cn_idx = [i for i, n in enumerate(FEATURE_NAMES) if n != "CN"]
X_q_noCN = X_quran[:, drop_cn_idx]
X_p_noCN = X_peers_v392[:, drop_cn_idx]
X_noCN = np.vstack([X_q_noCN, X_p_noCN])
t2_2, d_2 = hotelling_t2(X_q_noCN, X_p_noCN)
auc_2, std_2 = auc_logreg_5fold(X_noCN, y)
print(f"#   4-D T²       = {t2_2:.2f}")
print(f"#   4-D Cohen's d = {d_2:.4f}")
print(f"#   4-D AUC       = {auc_2:.6f} ± {std_2:.6f}")
print()


# ----------------------------------------------------------------------
# T3: DROP EL + CN COMBINED
# ----------------------------------------------------------------------
print("# " + "=" * 70)
print("# T3. DROP EL+CN COMBINED (V3.9-affected + Quran-genre)")
print("# " + "=" * 70)

drop_el_cn_idx = [i for i, n in enumerate(FEATURE_NAMES)
                  if n not in ("EL", "CN")]
X_q_noEL_CN = X_quran[:, drop_el_cn_idx]
X_p_noEL_CN = X_peers_v392[:, drop_el_cn_idx]
X_noEL_CN = np.vstack([X_q_noEL_CN, X_p_noEL_CN])
t2_3, d_3 = hotelling_t2(X_q_noEL_CN, X_p_noEL_CN)
auc_3, std_3 = auc_logreg_5fold(X_noEL_CN, y)
print(f"#   3-D feature space: {[FEATURE_NAMES[i] for i in drop_el_cn_idx]}")
print(f"#   3-D T²       = {t2_3:.2f}")
print(f"#   3-D Cohen's d = {d_3:.4f}")
print(f"#   3-D AUC       = {auc_3:.6f} ± {std_3:.6f}")
print()


# ----------------------------------------------------------------------
# T4: CROSS-CORPUS WEIGHT TRANSFER (Quran-blind weights)
# ----------------------------------------------------------------------
print("# " + "=" * 70)
print("# T4. CROSS-CORPUS WEIGHT TRANSFER (Quran-BLIND classifier weights)")
print("# " + "=" * 70)
print("# Train logistic-regression weights on a non-Quran two-corpus split,")
print("# then apply those frozen weights to score Quran-vs-Arabic-peers.")
print("# If Quran is still extremal under foreign-trained weights, the")
print("# feature-weight selection is independent of Quran knowledge.")
print()

# Compute language-agnostic 5-D features for cross-tradition corpora
print("# Computing language-agnostic 5-D features for cross-tradition corpora...")


def feats_lang_agnostic(unit) -> np.ndarray | None:
    """Use language-agnostic feature pipeline (h_cond_initials)."""
    try:
        v = features_5d_lang_agnostic(unit.verses, stops=set())
        if np.all(np.isfinite(v)):
            return v
    except Exception:
        return None
    return None


def collect_lang_agnostic(corpus_name):
    out = []
    for u in CORPORA.get(corpus_name, []):
        f = feats_lang_agnostic(u)
        if f is not None:
            out.append(f)
    return np.array(out) if out else np.empty((0, 5))


# Train on Iliad-vs-Arabic-Bible (two non-Quran corpora; both narrative)
# This gives weights that distinguish Greek epic from Arabic religious-narrative,
# WITHOUT using any Quran units.
X_iliad_la = collect_lang_agnostic("iliad_greek")
X_ab_la = collect_lang_agnostic("arabic_bible")
print(f"# Iliad units (lang-agnostic feats): {len(X_iliad_la)}")
print(f"# Arabic Bible units (lang-agnostic feats): {len(X_ab_la)}")

# Use Quran's own feats too in the same lang-agnostic pipeline for fairness
X_quran_la = []
for u in CORPORA.get("quran", []):
    if not is_band_a(u):
        continue
    f = feats_lang_agnostic(u)
    if f is not None:
        X_quran_la.append(f)
X_quran_la = np.array(X_quran_la)

# Compute lang-agnostic peers (skip Iliad and Arabic Bible since they're for training)
peer_corpora_t4 = ["poetry_jahili", "poetry_islami", "poetry_abbasi",
                   "ksucca", "hindawi", "hadith_bukhari"]
X_peers_la_list = [collect_lang_agnostic(c) for c in peer_corpora_t4]
X_peers_la = np.vstack([x for x in X_peers_la_list if len(x) > 0])
print(f"# Quran (lang-agnostic, band-A): {len(X_quran_la)}")
print(f"# Arabic peers (lang-agnostic, no Quran/Iliad/AB): {len(X_peers_la)}")
print()

# Train LR on Iliad vs Arabic Bible
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

X_train = np.vstack([X_iliad_la, X_ab_la])
y_train = np.concatenate([np.ones(len(X_iliad_la)),
                          np.zeros(len(X_ab_la))])
scaler_t4 = StandardScaler().fit(X_train)
clf_t4 = LogisticRegression(max_iter=10000, C=1.0).fit(
    scaler_t4.transform(X_train), y_train)

print(f"# Training set: Iliad ({len(X_iliad_la)}) vs Arabic Bible ({len(X_ab_la)}) — NO QURAN")
train_score = clf_t4.score(scaler_t4.transform(X_train), y_train)
print(f"# Training accuracy (Iliad-vs-AB): {train_score:.4f}")
print(f"# Trained weights (lang-agnostic feats): {clf_t4.coef_[0]}")
print()

# Apply frozen weights to score Quran and Arabic peers
X_test = np.vstack([X_quran_la, X_peers_la])
y_test = np.concatenate([np.ones(len(X_quran_la)),
                         np.zeros(len(X_peers_la))])
proba = clf_t4.predict_proba(scaler_t4.transform(X_test))[:, 1]

# Quran-blind AUC
auc_blind = roc_auc_score(y_test, proba)
print(f"# Quran-blind AUC (Iliad-vs-AB weights applied to Quran-vs-peers): {auc_blind:.6f}")

# Score distribution
quran_scores = proba[:len(X_quran_la)]
peer_scores = proba[len(X_quran_la):]
print(f"# Quran score (median {np.median(quran_scores):.4f}, mean {quran_scores.mean():.4f})")
print(f"# Peer score  (median {np.median(peer_scores):.4f}, mean {peer_scores.mean():.4f})")

# Where does Quran rank in the projection?
# Higher score = more Iliad-like under the trained classifier
# But what we care about is: does Quran lie at one extreme of the score distribution?
all_scores = np.concatenate([quran_scores, peer_scores])
quran_rank_pct = (np.searchsorted(np.sort(all_scores),
                                   np.median(quran_scores)) /
                  len(all_scores) * 100)
print(f"# Quran median score percentile (of all units): {quran_rank_pct:.1f}%")
print()


# ----------------------------------------------------------------------
# SUMMARY TABLE
# ----------------------------------------------------------------------
print("# " + "=" * 70)
print("# V3.9.2 SUMMARY TABLE")
print("# " + "=" * 70)
print()
print(f"# {'Test':<60s} | {'AUC':<10s} | {'Cohen d':<10s} | T²")
print(f"# {'-'*60} | {'-'*10} | {'-'*10} | {'-'*8}")
print(f"# {'V3.9.1 baseline 5-D (no hadith)':<60s} | {'~0.9953':<10s} | {'~5.85':<10s} | ~2292")
print(f"# {'T1: 5-D + hadith INCLUDED':<60s} | {auc_m:<10.4f} | {d:<10.4f} | {t2:<8.0f}")
print(f"# {'T1: Quran-vs-HADITH-ONLY':<60s} | {auc_h:<10.4f} | {d_h:<10.4f} | {t2_h:<8.0f}")
print(f"# {'T2: 4-D drop CN (with hadith)':<60s} | {auc_2:<10.4f} | {d_2:<10.4f} | {t2_2:<8.0f}")
print(f"# {'T3: 3-D drop EL+CN (with hadith)':<60s} | {auc_3:<10.4f} | {d_3:<10.4f} | {t2_3:<8.0f}")
print(f"# {'T4: Quran-blind weights (lang-agnostic, +hadith)':<60s} | {auc_blind:<10.4f} | {'(blind)':<10s} | (blind)")
print()

print("# Verdict thresholds:")
verdicts = []
verdicts.append("T1 (hadith): " +
                ("ROBUST" if auc_m >= 0.90 else "WEAK" if auc_m >= 0.80 else "FAIL")
                + f" — AUC = {auc_m:.4f}")
verdicts.append("T2 (drop CN): " +
                ("ROBUST" if auc_2 >= 0.90 else "WEAK" if auc_2 >= 0.80 else "FAIL")
                + f" — AUC = {auc_2:.4f}")
verdicts.append("T3 (drop EL+CN): " +
                ("ROBUST" if auc_3 >= 0.85 else "WEAK" if auc_3 >= 0.75 else "FAIL")
                + f" — AUC = {auc_3:.4f}")
verdicts.append("T4 (Quran-blind weights): " +
                ("ROBUST" if auc_blind >= 0.85 else "WEAK" if auc_blind >= 0.70 else "FAIL")
                + f" — AUC = {auc_blind:.4f}")

for v in verdicts:
    print(f"#   {v}")
