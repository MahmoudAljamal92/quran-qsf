"""exp176 escalation 3b — maqrūnāt benchmark on alternative feature spaces.

Same 17 classical pairs as maqrunat_benchmark.py, but tested on:
  A. verse-final letter distribution (rhyme channel)
  B. verse-length distribution (architectural)
  C. bigram top-50
  D. letter unigram (recap, same as main)

If classical pairs concentrate in one of these spaces but not another,
that tells us which feature space is the true substrate of classical
thematic pairing.
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

CLASSICAL_PAIRS = [
    (2, 3, "al-Zahrāwān"),
    (8, 9, "Anfāl-Tawba"),
    (55, 56, "Raḥmān-Wāqiʿa"),
    (67, 68, "Mulk-Qalam"),
    (73, 74, "Muzzammil-Muddaththir"),
    (75, 76, "Qiyāma-Insān"),
    (77, 78, "Mursalāt-Nabaʾ"),
    (81, 82, "Takwīr-Infiṭār"),
    (83, 84, "Muṭaffifīn-Inshiqāq"),
    (87, 88, "Aʿlā-Ghāshiya"),
    (91, 92, "Shams-Layl"),
    (93, 94, "Ḍuḥā-Sharḥ"),
    (99, 100, "Zalzala-ʿĀdiyāt"),
    (103, 104, "ʿAṣr-Humaza"),
    (105, 106, "Fīl-Quraysh"),
    (111, 112, "Masad-Ikhlās"),
    (113, 114, "Muʿawwidhatān"),
]


def load_surahs_and_verses():
    path = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\data\corpora\ar\quran_bare.txt")
    surahs: dict[int, list[str]] = {i: [] for i in range(1, 115)}
    for line in path.read_text(encoding="utf-8").splitlines():
        p = line.split("|", 2)
        if len(p) < 3 or not p[0].strip().isdigit():
            continue
        s = int(p[0])
        if 1 <= s <= 114:
            surahs[s].append(p[2].strip())
    joined = {i: " ".join(surahs[i]) for i in range(1, 115)}
    return surahs, joined


def letter_freq(text: str):
    only = [c for c in text if c in ARABIC_LETTERS_SET]
    n = len(only)
    if n == 0:
        return np.zeros(28), 0
    counts = Counter(only)
    return np.array([counts.get(c, 0) / n for c in ARABIC_LETTERS]), n


def verse_final_letter_freq(verses):
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


def verse_length_distribution(verses, edges):
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


def bigram_top_k(text, top_bigrams):
    only = "".join(c for c in text if c in ARABIC_LETTERS_SET)
    if len(only) < 2:
        return np.zeros(len(top_bigrams))
    counts = Counter(only[i:i + 2] for i in range(len(only) - 1))
    total = sum(counts.values())
    return np.array([counts.get(b, 0) / total for b in top_bigrams])


def detrend(F, logN, md):
    X = np.column_stack([np.ones(114), logN, logN**2, logN**3, md])
    R = np.zeros_like(F)
    for k in range(F.shape[1]):
        beta, *_ = np.linalg.lstsq(X, F[:, k], rcond=None)
        R[:, k] = F[:, k] - X @ beta
    return R


def benchmark(F_det: np.ndarray, name: str, pairs, n_boot=20000, seed=20260501):
    consec = np.linalg.norm(np.diff(F_det, axis=0), axis=1)
    D = np.linalg.norm(F_det[:, None, :] - F_det[None, :, :], axis=-1)
    iu = np.triu_indices(114, k=1)
    all_pw = D[iu]

    classical_d = np.array([consec[a - 1] for (a, _b, _n) in pairs])
    ranks = np.array([float((consec < d).sum()) / 113 * 100 for d in classical_d])

    rng = np.random.default_rng(seed)
    # N2 null: random consecutive-index sample
    n_class = len(pairs)
    nulls = []
    for _ in range(n_boot):
        s = rng.choice(113, size=n_class, replace=False)
        nulls.append(consec[s].mean())
    nulls = np.array(nulls)
    p_lo = (np.sum(nulls <= classical_d.mean()) + 1) / (n_boot + 1)
    p_hi = (np.sum(nulls >= classical_d.mean()) + 1) / (n_boot + 1)
    from math import comb
    bh = int((ranks < 50).sum())
    p_sign = 2 * sum(comb(n_class, k) * 0.5**n_class for k in range(min(bh, n_class - bh), n_class + 1))
    # two-sided
    bdec = int((ranks < 10).sum())
    bqui = int((ranks < 20).sum())
    return dict(
        name=name,
        classical_mean=float(classical_d.mean()),
        all_mean=float(consec.mean()),
        ratio=float(classical_d.mean() / consec.mean()),
        mean_percentile=float(ranks.mean()),
        bottom_half_count=bh,
        bottom_decile_count=bdec,
        bottom_quintile_count=bqui,
        p_N2_lower_tail=float(p_lo),
        p_N2_upper_tail=float(p_hi),
        per_pair_percentiles=ranks.tolist(),
        per_pair_d=classical_d.tolist(),
    )


def main() -> None:
    surahs_text, joined = load_surahs_and_verses()
    Nlet = np.array([sum(1 for c in joined[i] if c in ARABIC_LETTERS_SET)
                     for i in range(1, 115)])
    logN = np.log(Nlet)
    md_label = np.array([1 if (i + 1) in MEDINAN else 0 for i in range(114)])

    F_A = np.array([letter_freq(joined[i])[0] for i in range(1, 115)])
    F_B = np.array([verse_final_letter_freq(surahs_text[i]) for i in range(1, 115)])
    all_lens = [sum(1 for c in v if c in ARABIC_LETTERS_SET)
                for i in range(1, 115) for v in surahs_text[i]]
    all_lens = [L for L in all_lens if L > 0]
    log_all = np.log(all_lens)
    edges = np.linspace(log_all.min() - 1e-6, log_all.max() + 1e-6, 9)
    F_C = np.array([verse_length_distribution(surahs_text[i], edges) for i in range(1, 115)])
    all_bg = Counter()
    for i in range(1, 115):
        only = "".join(c for c in joined[i] if c in ARABIC_LETTERS_SET)
        for j in range(len(only) - 1):
            all_bg[only[j:j + 2]] += 1
    top50 = [b for b, _ in all_bg.most_common(50)]
    F_D = np.array([bigram_top_k(joined[i], top50) for i in range(1, 115)])

    feature_spaces = [
        ("A_letter_unigram", detrend(F_A, logN, md_label)),
        ("B_verse_final_rhyme", detrend(F_B, logN, md_label)),
        ("C_verse_length_hist", detrend(F_C, logN, md_label)),
        ("D_bigram_top50", detrend(F_D, logN, md_label)),
        ("B_rhyme_RAW", F_B),          # test without detrender too
        ("C_VL_RAW", F_C),
    ]

    print(f"{'feature':26s} {'mean_d':>8s} {'all_d':>8s} {'ratio':>7s} "
          f"{'mean_pct':>9s} {'b_half':>7s} {'b_dec':>6s} {'p_lo':>8s} {'p_hi':>8s}")
    print("-" * 100)
    results = {}
    for name, F_det in feature_spaces:
        r = benchmark(F_det, name, CLASSICAL_PAIRS)
        results[name] = r
        print(f"{name:26s} {r['classical_mean']:>8.4f} {r['all_mean']:>8.4f} "
              f"{r['ratio']:>7.3f} {r['mean_percentile']:>8.1f}%  "
              f"{r['bottom_half_count']:>5d}/17 {r['bottom_decile_count']:>4d}/17 "
              f"{r['p_N2_lower_tail']:>8.4f} {r['p_N2_upper_tail']:>8.4f}")

    print()
    print("Per-pair percentile by feature space (higher = further apart):")
    print(f"  {'pair':>14s}", end="")
    for name, _ in feature_spaces:
        print(f" {name[:9]:>9s}", end="")
    print()
    for i, (a, b, note) in enumerate(CLASSICAL_PAIRS):
        lbl = f"{a}-{b} {note[:9]}"
        print(f"  {lbl:>14s}", end="")
        for name, _ in feature_spaces:
            pct = results[name]["per_pair_percentiles"][i]
            print(f" {pct:>8.1f}%", end="")
        print()

    out_path = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp176_mushaf_tour\maqrunat_on_other_features.json")
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReceipt: {out_path}")


if __name__ == "__main__":
    main()
