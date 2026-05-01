"""exp176 Avenue A — Bayesian inversion.

Question: from letter-frequency data alone (no list of classical pairs),
can we RECOVER the 17 classical maqrūnāt pairs?

Method: rank all 113 Mushaf-adjacent pairs by their detrended F1+F2
distance. Predict the top-K highest-distance pairs as classical.
Score against the locked Farahi/Islahi/Drāz/Sahih-Muslim list.

If precision and recall substantially exceed random, F82 jumps from
"corroboration of a given list" to "blind recovery of the list" —
much stronger than pre-registered confirmation.
"""
from __future__ import annotations
import io
import json
import sys
from collections import Counter
from pathlib import Path
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ARABIC_LETTERS = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
ARABIC_LETTERS_SET = set(ARABIC_LETTERS)
MEDINAN = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 55, 57, 58, 59, 60,
           61, 62, 63, 64, 65, 66, 76, 98, 99, 110}

# Locked classical pair list (Farahi/Islahi/Drāz/Sahih Muslim).
CLASSICAL_PAIRS = [
    (2, 3), (8, 9), (55, 56), (67, 68), (73, 74), (75, 76), (77, 78),
    (81, 82), (83, 84), (87, 88), (91, 92), (93, 94), (99, 100),
    (103, 104), (105, 106), (111, 112), (113, 114),
]
N_CLASSICAL = len(CLASSICAL_PAIRS)


def load_surah_text():
    p = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\data\corpora\ar\quran_bare.txt")
    s = {i: [] for i in range(1, 115)}
    for line in p.read_text(encoding="utf-8").splitlines():
        x = line.split("|", 2)
        if len(x) < 3 or not x[0].strip().isdigit():
            continue
        k = int(x[0])
        if 1 <= k <= 114:
            s[k].append(x[2].strip())
    return {i: " ".join(s[i]) for i in range(1, 115)}


def letter_freq(text):
    only = [c for c in text if c in ARABIC_LETTERS_SET]
    n = len(only)
    if n == 0:
        return np.zeros(28), 0
    counts = Counter(only)
    return np.array([counts.get(c, 0) / n for c in ARABIC_LETTERS]), n


def detrend(F, logN, md):
    X = np.column_stack([np.ones(114), logN, logN**2, logN**3, md])
    R = np.zeros_like(F)
    for k in range(F.shape[1]):
        beta, *_ = np.linalg.lstsq(X, F[:, k], rcond=None)
        R[:, k] = F[:, k] - X @ beta
    return R


def bigram_top_k_features(joined, top):
    F = np.zeros((114, len(top)))
    for i in range(1, 115):
        only = "".join(c for c in joined[i] if c in ARABIC_LETTERS_SET)
        if len(only) < 2:
            continue
        counts = Counter(only[j:j + 2] for j in range(len(only) - 1))
        total = sum(counts.values())
        F[i - 1] = np.array([counts.get(b, 0) / total for b in top])
    return F


def main():
    joined = load_surah_text()
    F1 = np.zeros((114, 28))
    Nlet = np.zeros(114)
    for i in range(1, 115):
        F1[i - 1], Nlet[i - 1] = letter_freq(joined[i])
    logN = np.log(Nlet)
    md = np.array([1 if (i + 1) in MEDINAN else 0 for i in range(114)])

    F1_det = detrend(F1, logN, md)
    # Bigram top-50
    bg_all = Counter()
    for i in range(1, 115):
        only = "".join(c for c in joined[i] if c in ARABIC_LETTERS_SET)
        for j in range(len(only) - 1):
            bg_all[only[j:j + 2]] += 1
    top50 = [b for b, _ in bg_all.most_common(50)]
    F2 = bigram_top_k_features(joined, top50)
    F2_det = detrend(F2, logN, md)

    # Distance for each of the 113 adjacent pairs
    d_F1 = np.linalg.norm(np.diff(F1_det, axis=0), axis=1)
    d_F2 = np.linalg.norm(np.diff(F2_det, axis=0), axis=1)
    # z-score within all 113
    def z(x):
        return (x - x.mean()) / x.std()
    d_combined = z(d_F1) + z(d_F2)

    # Ground truth: 17 classical pairs (a-1 = pair index in 0..112)
    truth_set = set(a - 1 for (a, b) in CLASSICAL_PAIRS)

    print("=== AVENUE A: Bayesian inversion ===")
    print(f"Total Mushaf-adjacent pairs: 113")
    print(f"Ground-truth classical pairs (Farahi/Islahi/Drāz/Sahih Muslim): {N_CLASSICAL}")
    print()
    # Run prediction at K = 17 (matched to ground truth size)
    for label, scores in [("F1 letter-freq distance", d_F1),
                          ("F2 bigram-top50 distance", d_F2),
                          ("F1+F2 combined z-distance", d_combined)]:
        # Top-K highest-distance pairs predicted as classical
        K = N_CLASSICAL
        order = np.argsort(scores)[::-1]  # descending
        predicted_set = set(order[:K])
        tp = len(predicted_set & truth_set)
        fp = K - tp
        fn = N_CLASSICAL - tp
        precision = tp / K
        recall = tp / N_CLASSICAL
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        print(f"[{label}]")
        print(f"  Top-{K} predicted -> TP={tp}, FP={fp}, FN={fn}")
        print(f"  Precision = {precision:.3f}, Recall = {recall:.3f}, F1 = {f1:.3f}")

        # Random baseline: F1 if we pick K from 113 uniformly at random
        # E[TP] = K * (N_CLASSICAL / 113)
        exp_tp = K * N_CLASSICAL / 113
        exp_f1 = 2 * (exp_tp / K) * (exp_tp / N_CLASSICAL) / (exp_tp / K + exp_tp / N_CLASSICAL)
        print(f"  Random baseline F1 ≈ {exp_f1:.3f}  (expected TP = {exp_tp:.2f})")

        # Hypergeometric p-value: P(TP >= observed | random)
        from math import comb
        # X ~ Hypergeometric(N=113, K=17, n=K)
        N, KK, n = 113, N_CLASSICAL, K
        p_val = sum(comb(KK, k) * comb(N - KK, n - k) / comb(N, n)
                    for k in range(tp, min(KK, n) + 1))
        print(f"  Hypergeometric P(TP >= {tp}) = {p_val:.5f}")
        print()

    # Now use Mufaṣṣal-only restriction: classical pairs in Mufaṣṣal = 15
    print("=== Restricted to Mufaṣṣal block (pair indices 49..112, 64 pairs) ===")
    muf_pair_idx = np.arange(49, 113)
    truth_muf = truth_set & set(muf_pair_idx.tolist())
    n_muf_truth = len(truth_muf)
    print(f"Classical pairs within Mufaṣṣal: {n_muf_truth}")
    for label, scores in [("F1 letter-freq", d_F1),
                          ("F2 bigram-top50", d_F2),
                          ("F1+F2 combined z", d_combined)]:
        scores_muf = scores[muf_pair_idx]
        K = n_muf_truth
        order = np.argsort(scores_muf)[::-1]
        predicted_in_muf = set((muf_pair_idx[order[:K]]).tolist())
        tp = len(predicted_in_muf & truth_muf)
        precision = tp / K
        recall = tp / n_muf_truth
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        print(f"[{label} | Mufaṣṣal-restricted]")
        print(f"  Top-{K} -> TP={tp}, P={precision:.3f}, R={recall:.3f}, F1={f1:.3f}")
        from math import comb
        N, KK, n = len(muf_pair_idx), n_muf_truth, K
        p_val = sum(comb(KK, k) * comb(N - KK, n - k) / comb(N, n)
                    for k in range(tp, min(KK, n) + 1))
        exp_tp = K * n_muf_truth / N
        print(f"  Random baseline F1 ≈ {2*(exp_tp/K)*(exp_tp/n_muf_truth)/(exp_tp/K + exp_tp/n_muf_truth):.3f}")
        print(f"  Hypergeometric P(TP >= {tp}) = {p_val:.5f}")
        print()

    # ROC-AUC-style summary: rank-based test
    # For Mufaṣṣal (most informative region), compute the avg rank of classical pairs
    # vs avg rank of non-classical, normalized by 64.
    print("=== Rank-based AUC analysis (Mufaṣṣal-only) ===")
    for label, scores in [("F1 letter-freq", d_F1),
                          ("F2 bigram-top50", d_F2),
                          ("F1+F2 combined z", d_combined)]:
        scores_muf = scores[muf_pair_idx]
        # classical-pair indices in muf-local frame
        local_class = [i - 49 for i in truth_muf]
        local_nonclass = [i for i in range(len(muf_pair_idx)) if i not in local_class]
        # Mann-Whitney AUC: probability that a randomly-chosen classical-pair distance > non-classical-pair distance
        cnt = 0
        total = 0
        for ci in local_class:
            for nci in local_nonclass:
                if scores_muf[ci] > scores_muf[nci]:
                    cnt += 1
                elif scores_muf[ci] == scores_muf[nci]:
                    cnt += 0.5
                total += 1
        auc = cnt / total
        print(f"[{label}] AUC = {auc:.4f}  (0.5 = chance; > 0.5 means classical > non-classical)")
        # asymptotic z for AUC under H0
        n1, n2 = len(local_class), len(local_nonclass)
        mu_U = n1 * n2 / 2
        sigma_U = np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
        U = cnt
        z_auc = (U - mu_U) / sigma_U
        from math import erf, sqrt
        p_auc = 0.5 * (1 - erf(z_auc / sqrt(2)))
        print(f"  Mann-Whitney U-test: z = {z_auc:+.3f}, one-tailed p = {p_auc:.5f}")
        print()

    # SAVE
    out = dict(
        n_classical=N_CLASSICAL,
        n_classical_in_mufassal=n_muf_truth,
    )
    out_path = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp176_mushaf_tour\avenue_A_bayesian.json")
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nReceipt: {out_path}")


if __name__ == "__main__":
    main()
