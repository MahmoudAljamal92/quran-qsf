"""exp176 escalation 3 — classical maqrūnāt benchmark.

Pre-registered list of surah pairs classically asserted as thematically
paired (sources: Farahi/Islahi nazm al-Qurʾān, Drāz studies, Zarkashi's
Burhān, Suyūṭī's Itqān, Ibn ʿArabī's Aḥkām). ONLY pairs universally
recognized in classical and modern nazm literature are included.

Hypothesis: classical pairs should concentrate in the tight tail of the
letter-frequency adjacent-pair distance distribution. Measured via:

  (a) what percentile of the 113 adjacent Mushaf-pair distances does
      the classical list fall in, on average?
  (b) permutation test: if we randomly pick 16 pairs (the size of our
      classical list), how often does the mean distance fall this low?

The benchmark is blind w.r.t. the distance metric — pairs are chosen
ONLY from classical literature, not from low-distance pairs.
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
MEDINAN = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 55, 57, 58, 59, 60,
           61, 62, 63, 64, 65, 66, 76, 98, 99, 110}

# Pre-registered classical maqrūnāt / nazm pairs (ALL consecutive; ALL
# from well-established classical or modern-classical Qur'ānic scholarship.
# Each has a one-line source note).
CLASSICAL_PAIRS = [
    (2, 3,   "al-Zahrāwān (Sahih Muslim); Farahi/Islahi nazm pair"),
    (8, 9,   "single surah in some codices; no basmala between them; Ibn ʿAbbās"),
    (55, 56, "Rahmān-Wāqiʿa paradise-judgment pair; Farahi"),
    (67, 68, "Mulk-Qalam consecutive disclosure pair; Islahi"),
    (73, 74, "Muzzammil-Muddaththir both ya-ayyuha-form address pair"),
    (75, 76, "Qiyāma-Insān eschatological continuation; Drāz"),
    (77, 78, "Mursalāt-Nabaʾ eschatological continuation; Drāz"),
    (81, 82, "Takwīr-Infiṭār 'when X happens' cosmic-disruption pair"),
    (83, 84, "Muṭaffifīn-Inshiqāq judgment-day pair"),
    (87, 88, "Aʿlā-Ghāshiya paired khuṭba-recitation; Sahih Muslim"),
    (91, 92, "Shams-Layl cosmic-oath pair; Farahi"),
    (93, 94, "Ḍuḥā-Sharḥ consolation pair; classical"),
    (99, 100, "Zalzala-ʿĀdiyāt eschatological-horses pair; Islahi"),
    (103, 104, "ʿAṣr-Humaza paired denunciation; Drāz"),
    (105, 106, "Fīl-Quraysh historically linked (ʿIkrima/Ubayy codex fused)"),
    (111, 112, "Masad-Ikhlās polemic vs affirmation pair; classical"),
    (113, 114, "al-Muʿawwidhatān (the two refuges) — universal pairing"),
]


def load_surahs():
    path = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\data\corpora\ar\quran_bare.txt")
    surahs: dict[int, list[str]] = {i: [] for i in range(1, 115)}
    for line in path.read_text(encoding="utf-8").splitlines():
        p = line.split("|", 2)
        if len(p) < 3 or not p[0].strip().isdigit():
            continue
        s = int(p[0])
        if 1 <= s <= 114:
            surahs[s].append(p[2].strip())
    return {i: " ".join(surahs[i]) for i in range(1, 115)}


def letter_freq(text: str):
    only = [c for c in text if c in ARABIC_LETTERS]
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


def main() -> None:
    surah_text = load_surahs()
    F = np.zeros((114, 28))
    Nlet = np.zeros(114)
    for i in range(1, 115):
        F[i - 1], Nlet[i - 1] = letter_freq(surah_text[i])
    logN = np.log(Nlet)
    md_label = np.array([1 if (i + 1) in MEDINAN else 0 for i in range(114)])
    F_det = detrend(F, logN, md_label)

    # ALL 113 consecutive Mushaf pair distances
    consec_dists = np.linalg.norm(np.diff(F_det, axis=0), axis=1)

    # CLASSICAL pairs (all consecutive by construction)
    classical_d = []
    for (a, b, note) in CLASSICAL_PAIRS:
        assert b == a + 1, f"Non-consecutive pair: {a},{b}"
        classical_d.append(consec_dists[a - 1])

    classical_d = np.array(classical_d)
    n_class = len(classical_d)

    print(f"Pre-registered classical pairs: {n_class}")
    print()
    print(f"{'pair':>7s} {'d':>8s} {'percentile':>11s}  note")
    ranks = []
    for i, (a, b, note) in enumerate(CLASSICAL_PAIRS):
        d = classical_d[i]
        # percentile among the 113 consecutive pair distances
        pct = float((consec_dists < d).sum()) / 113.0 * 100
        ranks.append(pct)
        print(f"  {a:3d}-{b:<3d} {d:>8.4f} {pct:>10.1f}%  {note}")

    ranks = np.array(ranks)

    # Aggregate statistics
    print()
    print(f"Mean classical-pair distance: {classical_d.mean():.4f}")
    print(f"Mean of ALL 113 consecutive distances: {consec_dists.mean():.4f}")
    print(f"Classical/all ratio: {classical_d.mean()/consec_dists.mean():.3f}")
    print(f"Mean percentile of classical pairs: {ranks.mean():.1f}% (50% would be null)")

    # Null test: draw n_class random SURAH PAIRS (not necessarily consecutive)
    # from feature space and compute mean distance.
    # Two nulls:
    # (N1) random surah-pair null: any (i,j), i<j — what fraction of random 17-pair samples
    #      has mean distance ≤ classical mean?
    # (N2) random consecutive-index null: pick 17 of the 113 Mushaf consecutive pairs
    #      at random — does classical cluster at the low-d end?

    D = np.linalg.norm(F_det[:, None, :] - F_det[None, :, :], axis=-1)
    iu = np.triu_indices(114, k=1)
    all_pairwise = D[iu]  # length 114*113/2 = 6441

    rng = np.random.default_rng(20260501)
    B = 20000
    # N1: random pair null
    n1_nulls = []
    for _ in range(B):
        sample = rng.choice(len(all_pairwise), size=n_class, replace=False)
        n1_nulls.append(all_pairwise[sample].mean())
    n1_nulls = np.array(n1_nulls)
    p_N1 = (np.sum(n1_nulls <= classical_d.mean()) + 1) / (B + 1)
    print(f"\n(N1) random-pair null (B={B}): "
          f"null mean = {n1_nulls.mean():.4f} ± {n1_nulls.std():.4f}; "
          f"p(classical ≤ null) = {p_N1:.5f}")

    # N2: random consecutive-index null
    n2_nulls = []
    for _ in range(B):
        sample = rng.choice(113, size=n_class, replace=False)
        n2_nulls.append(consec_dists[sample].mean())
    n2_nulls = np.array(n2_nulls)
    p_N2 = (np.sum(n2_nulls <= classical_d.mean()) + 1) / (B + 1)
    print(f"(N2) random-consecutive-index null (B={B}): "
          f"null mean = {n2_nulls.mean():.4f} ± {n2_nulls.std():.4f}; "
          f"p(classical ≤ null) = {p_N2:.5f}")

    # N3: signed-rank test: under H0 each classical pair is at median percentile 50%
    from math import comb
    # sign test: how many classical pairs fall in bottom half?
    bottom_half = (ranks < 50).sum()
    # two-sided binomial
    p_sign = 2 * sum(comb(n_class, k) * 0.5**n_class for k in range(bottom_half, n_class + 1))
    p_sign = min(p_sign, 1.0)
    print(f"(N3) sign test: {bottom_half}/{n_class} classical pairs in bottom half of "
          f"consecutive-pair distances; binomial two-sided p = {p_sign:.5f}")

    # How many in bottom decile/quintile?
    bottom_decile = (ranks < 10).sum()
    bottom_quintile = (ranks < 20).sum()
    bottom_quartile = (ranks < 25).sum()
    print(f"    bottom 10%: {bottom_decile}/{n_class} (expected {n_class * 0.10:.1f} under H0)")
    print(f"    bottom 20%: {bottom_quintile}/{n_class} (expected {n_class * 0.20:.1f})")
    print(f"    bottom 25%: {bottom_quartile}/{n_class} (expected {n_class * 0.25:.1f})")

    out = dict(
        classical_pairs=[dict(a=a, b=b, d=float(classical_d[i]),
                              percentile=float(ranks[i]), note=note)
                         for i, (a, b, note) in enumerate(CLASSICAL_PAIRS)],
        n_pairs=n_class,
        mean_classical_distance=float(classical_d.mean()),
        mean_all_consecutive_distance=float(consec_dists.mean()),
        ratio_classical_to_all=float(classical_d.mean() / consec_dists.mean()),
        mean_percentile=float(ranks.mean()),
        p_N1_random_pair_null=float(p_N1),
        p_N2_random_consecutive_null=float(p_N2),
        p_N3_sign_test=float(p_sign),
        bottom_decile_count=int(bottom_decile),
        bottom_quintile_count=int(bottom_quintile),
        bottom_quartile_count=int(bottom_quartile),
    )
    out_path = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp176_mushaf_tour\maqrunat_benchmark.json")
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReceipt: {out_path}")


if __name__ == "__main__":
    main()
