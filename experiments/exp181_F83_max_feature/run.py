"""exp181 — F91 = F83 Bayesian inversion with maximum-feature supervised classifier.

Extends F83 (which used only F1 letter-freq + F2 bigram) to an 8-feature
vector per Mushaf-adjacent pair, then runs:

   - unsupervised: combined-z ranking (same as F83 method, but richer score)
   - supervised  : logistic regression with leave-one-out CV
   - supervised  : random forest with leave-one-out CV

Features per Mushaf-adjacent pair (s, s+1) — 8 features total:
   1. d_letter   : L2 in 28-D detrended letter-freq                (from F83)
   2. d_bigram50 : L2 in 50-D top-bigram detrended                 (from F83)
   3. d_trig100  : L2 in 100-D top-trigram detrended               (NEW)
   4. d_rhyme    : L2 in 28-D verse-final-letter histogram         (NEW)
   5. d_len_mean : |E[verse_len]_s − E[verse_len]_{s+1}|, log-scaled (NEW)
   6. d_len_cv   : |CV[verse_len]_s − CV[verse_len]_{s+1}|         (NEW)
   7. d_logN     : |log(letters_s) − log(letters_{s+1})|           (NEW)
   8. muqatta    : 1 if both s and s+1 open with muqattaʿāt, else 0 (NEW)

Target: y_k = 1 if adjacency slot k corresponds to a classical Farahi/Islahi/
Drāz/Sahih-Muslim maqrūnāt pair, else 0. 17 positives out of 113 slots.

F83 baseline: F1-only TP=7/17 (F1-score = 0.412, p = 0.00402).
F91 target  : TP ≥ 11/17 via supervised classifier (F1-score ≥ 0.65, p ≤ 10⁻⁵).
"""
from __future__ import annotations
import io
import json
import sys
import re
from collections import Counter
from math import comb, erf, sqrt
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import roc_auc_score

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"
OUT_DIR = ROOT / "results" / "experiments" / "exp181_F83_max_feature"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ARABIC_LETTERS = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
ARABIC_LETTERS_SET = set(ARABIC_LETTERS)
MEDINAN = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 55, 57, 58, 59, 60,
           61, 62, 63, 64, 65, 66, 76, 98, 99, 110}

# Classical pair list (identical to F83)
CLASSICAL_PAIRS = [
    (2, 3), (8, 9), (55, 56), (67, 68), (73, 74), (75, 76), (77, 78),
    (81, 82), (83, 84), (87, 88), (91, 92), (93, 94), (99, 100),
    (103, 104), (105, 106), (111, 112), (113, 114),
]
N_CLASSICAL = len(CLASSICAL_PAIRS)

# Surahs with muqattaʿāt (disjointed letters) opening
MUQATTAAT_SURAHS = {2, 3, 7, 10, 11, 12, 13, 14, 15, 19, 20, 26, 27, 28, 29, 30,
                    31, 32, 36, 38, 40, 41, 42, 43, 44, 45, 46, 50, 68}

SEED = 20260503


def load_surahs_and_verses():
    """Return:
       - joined: dict[surah_id -> full text concatenated]
       - verses: dict[surah_id -> list[str]]
    """
    joined_parts: dict[int, list[str]] = {i: [] for i in range(1, 115)}
    verse_list: dict[int, list[str]] = {i: [] for i in range(1, 115)}
    for line in DATA.read_text(encoding="utf-8").splitlines():
        x = line.split("|", 2)
        if len(x) < 3 or not x[0].strip().isdigit():
            continue
        k = int(x[0])
        if 1 <= k <= 114:
            joined_parts[k].append(x[2].strip())
            verse_list[k].append(x[2].strip())
    joined = {i: " ".join(joined_parts[i]) for i in range(1, 115)}
    return joined, verse_list


def letter_only(text: str) -> str:
    return "".join(c for c in text if c in ARABIC_LETTERS_SET)


def verse_final_letter_hist(verses: list[str]) -> np.ndarray:
    """Per-surah histogram of verse-final letters (28-D, normalised)."""
    finals = []
    for v in verses:
        only = letter_only(v)
        if only:
            finals.append(only[-1])
    if not finals:
        return np.zeros(28)
    counts = Counter(finals)
    total = sum(counts.values())
    return np.array([counts.get(c, 0) / total for c in ARABIC_LETTERS])


def letter_freq(text: str) -> tuple[np.ndarray, int]:
    only = letter_only(text)
    n = len(only)
    if n == 0:
        return np.zeros(28), 0
    counts = Counter(only)
    return np.array([counts.get(c, 0) / n for c in ARABIC_LETTERS]), n


def ngram_top_k(joined, k, n):
    """Top-k n-grams across Quran, returns a list of n-gram strings."""
    counter = Counter()
    for i in range(1, 115):
        only = letter_only(joined[i])
        for j in range(len(only) - n + 1):
            counter[only[j:j + n]] += 1
    return [g for g, _ in counter.most_common(k)]


def ngram_features(joined, ngrams, n):
    """Per-surah n-gram frequency vector for given ngram list."""
    F = np.zeros((114, len(ngrams)))
    for i in range(1, 115):
        only = letter_only(joined[i])
        if len(only) < n:
            continue
        counts = Counter(only[j:j + n] for j in range(len(only) - n + 1))
        total = sum(counts.values())
        F[i - 1] = np.array([counts.get(g, 0) / total for g in ngrams])
    return F


def detrend(F, logN, md):
    X = np.column_stack([np.ones(114), logN, logN**2, logN**3, md])
    R = np.zeros_like(F)
    for k in range(F.shape[1]):
        beta, *_ = np.linalg.lstsq(X, F[:, k], rcond=None)
        R[:, k] = F[:, k] - X @ beta
    return R


def pair_feature_matrix(joined, verse_list) -> tuple[np.ndarray, list[str]]:
    """Build 113 x 8 pair-feature matrix."""
    # Per-surah global stats
    F1 = np.zeros((114, 28))
    Nlet = np.zeros(114)
    for i in range(1, 115):
        F1[i - 1], Nlet[i - 1] = letter_freq(joined[i])
    logN = np.log(Nlet)
    md = np.array([1 if (i + 1) in MEDINAN else 0 for i in range(114)])
    F1_det = detrend(F1, logN, md)

    top50_bg = ngram_top_k(joined, 50, 2)
    F2 = ngram_features(joined, top50_bg, 2)
    F2_det = detrend(F2, logN, md)

    top100_tg = ngram_top_k(joined, 100, 3)
    F3 = ngram_features(joined, top100_tg, 3)
    F3_det = detrend(F3, logN, md)

    # rhyme-letter (verse-final) histograms
    R = np.zeros((114, 28))
    for i in range(1, 115):
        R[i - 1] = verse_final_letter_hist(verse_list[i])
    R_det = detrend(R, logN, md)

    # verse-length stats per surah
    vl_mean = np.zeros(114)
    vl_cv = np.zeros(114)
    for i in range(1, 115):
        ls = [len(letter_only(v)) for v in verse_list[i]]
        if ls:
            vl_mean[i - 1] = np.mean(ls)
            if len(ls) > 1 and np.mean(ls) > 0:
                vl_cv[i - 1] = np.std(ls, ddof=1) / np.mean(ls)

    # muqatta indicator
    muq = np.array([1 if (i + 1) in MUQATTAAT_SURAHS else 0 for i in range(114)])

    # Build 113 x 8 features
    X_pair = np.zeros((113, 8))
    feat_names = [
        "d_letter", "d_bigram50", "d_trig100", "d_rhyme",
        "d_len_mean_log", "d_len_cv", "d_logN", "muqatta_both",
    ]
    for k in range(113):
        a, b = k, k + 1  # 0-indexed
        X_pair[k, 0] = np.linalg.norm(F1_det[a] - F1_det[b])
        X_pair[k, 1] = np.linalg.norm(F2_det[a] - F2_det[b])
        X_pair[k, 2] = np.linalg.norm(F3_det[a] - F3_det[b])
        X_pair[k, 3] = np.linalg.norm(R_det[a] - R_det[b])
        # log-scaled length mean diff
        X_pair[k, 4] = abs(np.log(vl_mean[a] + 1) - np.log(vl_mean[b] + 1))
        X_pair[k, 5] = abs(vl_cv[a] - vl_cv[b])
        X_pair[k, 6] = abs(logN[a] - logN[b])
        X_pair[k, 7] = float(muq[a] and muq[b])
    return X_pair, feat_names


def eval_topk_with_hyper(scores: np.ndarray, y_true: np.ndarray, K: int) -> dict:
    N = len(y_true)
    KK = int(y_true.sum())
    order = np.argsort(scores)[::-1]
    predicted_set = set(order[:K].tolist())
    truth_set = set(np.where(y_true)[0].tolist())
    tp = len(predicted_set & truth_set)
    fp = K - tp
    fn = KK - tp
    prec = tp / K if K else 0.0
    rec = tp / KK if KK else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    # Hypergeometric P(TP >= tp | random)
    p_val = sum(comb(KK, k) * comb(N - KK, K - k) / comb(N, K)
                for k in range(tp, min(KK, K) + 1))
    return dict(
        tp=tp, fp=fp, fn=fn,
        precision=prec, recall=rec, f1=f1,
        hyper_p=float(p_val),
        K=K, N=N, K_true=KK,
    )


def loo_logistic_scores(X: np.ndarray, y: np.ndarray,
                         C_values: list[float] | None = None) -> np.ndarray:
    """Return LOO-CV probability of class 1 per sample."""
    if C_values is None:
        C_values = [1.0]
    loo = LeaveOneOut()
    probs = np.zeros(len(y))
    for train, test in loo.split(X):
        scaler = StandardScaler().fit(X[train])
        Xtr = scaler.transform(X[train])
        Xte = scaler.transform(X[test])
        # Simple single-C logistic with L2
        clf = LogisticRegression(penalty="l2", C=C_values[0], class_weight="balanced",
                                  max_iter=2000, solver="liblinear")
        clf.fit(Xtr, y[train])
        probs[test] = clf.predict_proba(Xte)[:, 1]
    return probs


def loo_random_forest_scores(X: np.ndarray, y: np.ndarray, seed: int) -> np.ndarray:
    loo = LeaveOneOut()
    probs = np.zeros(len(y))
    for train, test in loo.split(X):
        clf = RandomForestClassifier(n_estimators=300, max_depth=None,
                                     class_weight="balanced", random_state=seed,
                                     n_jobs=1)
        clf.fit(X[train], y[train])
        probs[test] = clf.predict_proba(X[test])[:, 1]
    return probs


def main():
    print("=" * 72)
    print("exp181 — F91 = F83 Bayesian inversion with max-feature classifier")
    print("=" * 72)

    joined, verse_list = load_surahs_and_verses()
    print("\nBuilding 8-feature pair matrix (113 pairs x 8 features)...")
    X_pair, feat_names = pair_feature_matrix(joined, verse_list)
    print(f"  Features: {feat_names}")
    print(f"  Shape   : {X_pair.shape}")

    # Ground truth vector
    y = np.zeros(113, dtype=int)
    for (a, b) in CLASSICAL_PAIRS:
        y[a - 1] = 1  # slot index a-1 is between surah a and a+1 (since 1-indexed surahs)
    assert y.sum() == N_CLASSICAL

    K = N_CLASSICAL

    # ----- Per-feature unsupervised ranking evaluation -----
    print("\n=== Per-feature standalone ranking (Top-K hypergeometric test) ===")
    per_feat_results = {}
    for j, name in enumerate(feat_names):
        res = eval_topk_with_hyper(X_pair[:, j], y, K)
        per_feat_results[name] = res
        print(f"  {name:18s}  TP={res['tp']:2d}/{K}  F1={res['f1']:.3f}  "
              f"hyperP={res['hyper_p']:.5f}")

    # ----- F83 baseline reproduction (d_letter standalone) -----
    f83_baseline = per_feat_results["d_letter"]
    print(f"\n  F83 BASELINE (d_letter only): TP={f83_baseline['tp']}/{K}, "
          f"F1={f83_baseline['f1']:.3f}, p={f83_baseline['hyper_p']:.5f}")

    # ----- Combined-z ranking (F83 style but with all 8 features) -----
    def z(x):
        return (x - x.mean()) / (x.std() + 1e-12)
    combined_z = np.sum(np.column_stack([z(X_pair[:, j]) for j in range(8)]), axis=1)
    res_combined = eval_topk_with_hyper(combined_z, y, K)
    print(f"\n  Unsupervised combined-z of all 8 features: "
          f"TP={res_combined['tp']}/{K}, F1={res_combined['f1']:.3f}, "
          f"p={res_combined['hyper_p']:.5f}")

    # ----- Supervised logistic regression with LOO -----
    print("\n=== Supervised LOO Logistic Regression ===")
    logit_scores = loo_logistic_scores(X_pair, y, C_values=[1.0])
    auc_logit = roc_auc_score(y, logit_scores)
    res_logit = eval_topk_with_hyper(logit_scores, y, K)
    print(f"  AUC-ROC = {auc_logit:.4f}")
    print(f"  Top-{K} TP={res_logit['tp']}/{K}, F1={res_logit['f1']:.3f}, "
          f"p={res_logit['hyper_p']:.5f}")

    # ----- Supervised Random Forest with LOO -----
    print("\n=== Supervised LOO Random Forest ===")
    rf_scores = loo_random_forest_scores(X_pair, y, SEED)
    auc_rf = roc_auc_score(y, rf_scores)
    res_rf = eval_topk_with_hyper(rf_scores, y, K)
    print(f"  AUC-ROC = {auc_rf:.4f}")
    print(f"  Top-{K} TP={res_rf['tp']}/{K}, F1={res_rf['f1']:.3f}, "
          f"p={res_rf['hyper_p']:.5f}")

    # ----- Mufaṣṣal-restricted evaluation (matches F83 second table) -----
    print("\n=== Mufaṣṣal-restricted (slots 49..112, 64 pairs, 15 truth) ===")
    muf_idx = np.arange(49, 113)
    y_muf = y[muf_idx]
    K_muf = int(y_muf.sum())
    print(f"  Pairs in Mufaṣṣal: {len(muf_idx)}, truth: {K_muf}")

    for name, scores_all in [
        ("d_letter (F83)", X_pair[:, 0]),
        ("combined_z (8-feat)", combined_z),
        ("logit LOO", logit_scores),
        ("rf LOO", rf_scores),
    ]:
        scores_muf = scores_all[muf_idx]
        res_muf = eval_topk_with_hyper(scores_muf, y_muf, K_muf)
        # Mann-Whitney AUC on Mufaṣṣal subset
        local_class = np.where(y_muf)[0]
        local_nonclass = np.where(~y_muf.astype(bool))[0]
        cnt, total = 0, 0
        for ci in local_class:
            for nci in local_nonclass:
                if scores_muf[ci] > scores_muf[nci]:
                    cnt += 1
                elif scores_muf[ci] == scores_muf[nci]:
                    cnt += 0.5
                total += 1
        mw_auc = cnt / total if total > 0 else float("nan")
        n1, n2 = len(local_class), len(local_nonclass)
        mu_U = n1 * n2 / 2
        sigma_U = sqrt(n1 * n2 * (n1 + n2 + 1) / 12) if n1 * n2 > 0 else float("inf")
        z_mw = (cnt - mu_U) / sigma_U if sigma_U > 0 else 0.0
        p_mw = 0.5 * (1 - erf(z_mw / sqrt(2)))
        print(f"  {name:22s}  TP={res_muf['tp']:2d}/{K_muf}  "
              f"F1={res_muf['f1']:.3f}  hyperP={res_muf['hyper_p']:.5f}  "
              f"MW AUC={mw_auc:.3f}  z={z_mw:+.2f}  p={p_mw:.4f}")

    # ----- Receipt -----
    receipt = dict(
        experiment="exp181_F83_max_feature",
        finding_id="F91",
        seed=SEED,
        n_pairs=113,
        n_classical=N_CLASSICAL,
        features=feat_names,
        baseline_F83_d_letter=f83_baseline,
        per_feature_standalone=per_feat_results,
        combined_z_8feat=res_combined,
        supervised_logit_loo=dict(auc=float(auc_logit), **res_logit),
        supervised_rf_loo=dict(auc=float(auc_rf), **res_rf),
        classical_pair_predicted_indices_logit=list(
            map(int, np.argsort(logit_scores)[::-1][:K].tolist())
        ),
        classical_pair_predicted_indices_rf=list(
            map(int, np.argsort(rf_scores)[::-1][:K].tolist())
        ),
        truth_pair_slots=list(map(int, np.where(y)[0].tolist())),
    )

    # Verdict
    best_tp = max(res_logit["tp"], res_rf["tp"],
                  res_combined["tp"], f83_baseline["tp"])
    best_method = None
    if res_logit["tp"] == best_tp:
        best_method = "logistic_LOO"
    elif res_rf["tp"] == best_tp:
        best_method = "random_forest_LOO"
    elif res_combined["tp"] == best_tp:
        best_method = "combined_z_unsupervised"
    else:
        best_method = "F83_baseline"
    improvement_over_F83 = best_tp - f83_baseline["tp"]

    # Tier verdict
    if best_tp >= 12:
        verdict = "PASS_strong_recovery_12plus_out_of_17"
    elif best_tp >= 10:
        verdict = "PASS_moderate_recovery_10plus"
    elif best_tp >= 8:
        verdict = "PARTIAL_PASS_modest_improvement_over_F83"
    elif best_tp == 7:
        verdict = "NO_IMPROVEMENT_OVER_F83"
    else:
        verdict = "FAIL_worse_than_F83"

    receipt["best_tp"] = int(best_tp)
    receipt["best_method"] = best_method
    receipt["improvement_over_F83_TP"] = int(improvement_over_F83)
    receipt["verdict"] = verdict

    print(f"\n=== VERDICT ===")
    print(f"  Best TP over all methods: {best_tp}/17 (F83 baseline: {f83_baseline['tp']}/17)")
    print(f"  Best method             : {best_method}")
    print(f"  Improvement over F83    : {improvement_over_F83:+d} pairs")
    print(f"  Verdict                 : {verdict}")

    out_path = OUT_DIR / "exp181_F83_max_feature.json"
    out_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"\nReceipt: {out_path}")


if __name__ == "__main__":
    main()
