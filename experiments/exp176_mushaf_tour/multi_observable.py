"""exp176 escalation 1 — multi-observable joint tour coherence.

Tests the same primary statistic on FOUR independent Quran observables:
  A. letter-frequency F1 (unigram, 28-D)           [already done as primary]
  B. verse-final-letter distribution F_rhyme (28-D) [rhyme channel]
  C. verse-length distribution F_VL (8-bin, log-scale) [architectural]
  D. bigram-frequency F2 top-50 (50-D)             [locally-sequential]

For each observable X_k we compute:
  - L_Mushaf(X_k) under its own length+M/D detrender
  - null distribution over B=5000 random permutations
  - z_k, p_k
Then the joint statistic
  Z_joint = (1/sqrt(4)) * sum_k z_k        (Stouffer)
  Fisher  = -2 * sum_k log(p_k)            (Fisher combined)
under independence. We also run a combined null: for each random perm,
compute the SAME perm applied to all four observables and take
Z_joint_perm, giving an empirical combined p.
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


def load_hafs_surahs_and_verses():
    path = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\data\corpora\ar\quran_bare.txt")
    surahs_text: dict[int, list[str]] = {i: [] for i in range(1, 115)}
    for line in path.read_text(encoding="utf-8").splitlines():
        p = line.split("|", 2)
        if len(p) < 3 or not p[0].strip().isdigit():
            continue
        s = int(p[0])
        if 1 <= s <= 114:
            surahs_text[s].append(p[2].strip())
    joined = {i: " ".join(surahs_text[i]) for i in range(1, 115)}
    return surahs_text, joined


def letter_freq(text: str) -> np.ndarray:
    only = [c for c in text if c in ARABIC_LETTERS_SET]
    n = len(only)
    if n == 0:
        return np.zeros(28)
    counts = Counter(only)
    return np.array([counts.get(c, 0) / n for c in ARABIC_LETTERS])


def verse_final_letter_freq(verses: list[str]) -> np.ndarray:
    """Rhyme channel: distribution over verse-final Arabic letters."""
    finals = []
    for v in verses:
        rev = [c for c in reversed(v) if c in ARABIC_LETTERS_SET]
        if rev:
            finals.append(rev[0])
    if not finals:
        return np.zeros(28)
    counts = Counter(finals)
    n = len(finals)
    return np.array([counts.get(c, 0) / n for c in ARABIC_LETTERS])


def verse_length_distribution(verses: list[str], edges: np.ndarray) -> np.ndarray:
    """Architectural: log-scale histogram of per-verse letter counts."""
    lens = []
    for v in verses:
        n = sum(1 for c in v if c in ARABIC_LETTERS_SET)
        if n > 0:
            lens.append(n)
    if not lens:
        return np.zeros(len(edges) - 1)
    counts, _ = np.histogram(np.log(lens), bins=edges)
    s = counts.sum()
    if s == 0:
        return np.zeros_like(counts, dtype=float)
    return counts.astype(float) / s


def bigram_top_k_freq(text: str, top_bigrams: list[str]) -> np.ndarray:
    only = "".join(c for c in text if c in ARABIC_LETTERS_SET)
    if len(only) < 2:
        return np.zeros(len(top_bigrams))
    counts = Counter(only[i:i + 2] for i in range(len(only) - 1))
    total = sum(counts.values())
    return np.array([counts.get(b, 0) / total for b in top_bigrams])


def detrend(F: np.ndarray, logN: np.ndarray, md: np.ndarray) -> np.ndarray:
    X = np.column_stack([np.ones(114), logN, logN**2, logN**3, md])
    R = np.zeros_like(F)
    for k in range(F.shape[1]):
        beta, *_ = np.linalg.lstsq(X, F[:, k], rcond=None)
        R[:, k] = F[:, k] - X @ beta
    return R


def L2_tour(idx: np.ndarray, F: np.ndarray) -> float:
    return float(np.sum(np.linalg.norm(np.diff(F[idx], axis=0), axis=1)))


def main() -> None:
    surahs_text, joined = load_hafs_surahs_and_verses()

    # total letters per surah (for detrender)
    Nlet = np.array([sum(1 for c in joined[i] if c in ARABIC_LETTERS_SET)
                     for i in range(1, 115)])
    logN = np.log(Nlet)
    md_label = np.array([1 if (i + 1) in MEDINAN else 0 for i in range(114)])

    # --- Observable A: letter-frequency unigram
    F_A = np.array([letter_freq(joined[i]) for i in range(1, 115)])
    F_A_det = detrend(F_A, logN, md_label)

    # --- Observable B: verse-final letter distribution
    F_B = np.array([verse_final_letter_freq(surahs_text[i]) for i in range(1, 115)])
    F_B_det = detrend(F_B, logN, md_label)

    # --- Observable C: verse-length distribution (8 log-spaced bins)
    # determine edges from pooled log-lengths
    all_lens = []
    for i in range(1, 115):
        for v in surahs_text[i]:
            n = sum(1 for c in v if c in ARABIC_LETTERS_SET)
            if n > 0:
                all_lens.append(n)
    log_all = np.log(all_lens)
    edges = np.linspace(log_all.min() - 1e-6, log_all.max() + 1e-6, 9)
    F_C = np.array([verse_length_distribution(surahs_text[i], edges) for i in range(1, 115)])
    F_C_det = detrend(F_C, logN, md_label)

    # --- Observable D: top-50 bigram frequencies
    all_bg: Counter[str] = Counter()
    for i in range(1, 115):
        only = "".join(c for c in joined[i] if c in ARABIC_LETTERS_SET)
        for j in range(len(only) - 1):
            all_bg[only[j:j + 2]] += 1
    top50 = [bg for bg, _ in all_bg.most_common(50)]
    F_D = np.array([bigram_top_k_freq(joined[i], top50) for i in range(1, 115)])
    F_D_det = detrend(F_D, logN, md_label)

    observables = {
        "A_letter_unigram": F_A_det,
        "B_verse_final_rhyme": F_B_det,
        "C_verse_length_hist": F_C_det,
        "D_letter_bigram_top50": F_D_det,
    }

    B = 5000
    np.random.seed(20260501)
    perms = [np.random.permutation(114) for _ in range(B)]

    z_scores = {}
    p_values = {}
    per_obs = {}
    null_matrix = np.zeros((B, len(observables)))

    for idx_k, (name, F) in enumerate(observables.items()):
        L_obs = L2_tour(np.arange(114), F)
        nulls = np.array([L2_tour(perm, F) for perm in perms])
        mu = nulls.mean()
        sd = nulls.std()
        z = (L_obs - mu) / sd
        below = int(np.sum(nulls < L_obs))
        p = (below + 1) / (B + 1)
        z_scores[name] = float(z)
        p_values[name] = float(p)
        per_obs[name] = dict(L_obs=float(L_obs), null_mean=float(mu),
                             null_std=float(sd), z=float(z), p=float(p),
                             below=below, total=B)
        null_matrix[:, idx_k] = (nulls - mu) / sd  # z-scored per observable
        print(f"{name:26s}  L={L_obs:.4f}  null={mu:.4f}±{sd:.4f}  z={z:+.3f}  "
              f"p={p:.4f}  below={below}/{B}")

    # joint statistics under independence assumption
    K = len(observables)
    z_arr = np.array([z_scores[n] for n in observables])
    p_arr = np.array([p_values[n] for n in observables])
    Z_stouffer_indep = z_arr.sum() / np.sqrt(K)
    # Fisher needs one-tailed p; we already used lower-tail below-count so p is one-tailed
    fisher_chi2 = -2 * np.log(p_arr).sum()
    fisher_df = 2 * K

    # empirical joint null: apply same permutation index across all observables,
    # sum per-obs z and compare to Mushaf's sum
    joint_null = null_matrix.sum(axis=1)  # under same-perm null, z's are correlated
    joint_obs = z_arr.sum()
    joint_below = int(np.sum(joint_null <= joint_obs))
    joint_p = (joint_below + 1) / (B + 1)
    joint_z = (joint_obs - joint_null.mean()) / joint_null.std()

    # Brown correction: effective K_eff = K^2 / (K + 2 * sum_{i<j} rho_ij)
    # where rho_ij is the null-permutation correlation between obs i and j z-scores.
    R = np.corrcoef(null_matrix.T)  # KxK
    sum_off = float(R.sum() - K)  # 2 * sum_{i<j} rho_ij = R.sum() - K (diag = 1 each)
    K_eff = K * K / (K + sum_off)
    Z_stouffer_brown = z_arr.sum() / np.sqrt(K + sum_off)

    print()
    print(f"joint (independence Stouffer)  Z = {Z_stouffer_indep:+.3f}")
    print(f"joint (Brown-corrected)        Z = {Z_stouffer_brown:+.3f}  "
          f"(K_eff = {K_eff:.3f}, sum_R off-diag = {sum_off:.3f})")
    print(f"joint (Fisher chi2 at df={fisher_df})  chi2 = {fisher_chi2:.3f}")
    print(f"joint empirical same-perm null:")
    print(f"  joint_z_obs = {joint_obs:+.3f}   joint_null_mean = {joint_null.mean():+.3f}   "
          f"null_std = {joint_null.std():.3f}")
    print(f"  Mushaf joint rank in same-perm null: {joint_below + 1}/{B + 1}  p = {joint_p:.6f}")

    # per-observable mushaf vs nuzul
    NUZUL = [96, 68, 73, 74, 1, 111, 81, 87, 92, 89, 93, 94, 103, 100, 108,
             102, 107, 109, 105, 113, 114, 112, 53, 80, 97, 91, 85, 95, 106,
             101, 75, 104, 77, 50, 90, 86, 54, 38, 7, 72, 36, 25, 35, 19, 20,
             56, 26, 27, 28, 17, 10, 11, 12, 15, 6, 37, 31, 34, 39, 40, 41, 42,
             43, 44, 45, 46, 51, 88, 18, 16, 71, 14, 21, 23, 32, 52, 67, 69, 70,
             78, 79, 82, 84, 30, 29, 83, 2, 8, 3, 33, 60, 4, 99, 57, 47, 13, 55,
             76, 65, 98, 59, 24, 22, 63, 58, 49, 66, 64, 61, 62, 48, 5, 9, 110]
    nuzul_idx = np.array([s - 1 for s in NUZUL])
    print("\nMushaf vs Nuzul per observable:")
    for name, F in observables.items():
        L_m = L2_tour(np.arange(114), F)
        L_n = L2_tour(nuzul_idx, F)
        print(f"  {name:26s}  L_m={L_m:.4f}  L_n={L_n:.4f}  "
              f"Nuzul-Mushaf = {L_n - L_m:+.4f}")

    out = dict(
        per_observable=per_obs,
        Z_stouffer_independence=float(Z_stouffer_indep),
        Z_stouffer_brown=float(Z_stouffer_brown),
        K_eff_brown=float(K_eff),
        Fisher_chi2=float(fisher_chi2),
        Fisher_df=fisher_df,
        joint_empirical_p=float(joint_p),
        joint_empirical_z=float(joint_z),
        null_zscore_correlations=R.tolist(),
    )
    out_path = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp176_mushaf_tour\multi_observable.json")
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReceipt: {out_path}")


if __name__ == "__main__":
    main()
