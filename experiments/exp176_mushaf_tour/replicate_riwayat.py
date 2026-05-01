"""exp176 — riwayat replication of Mushaf-tour finding.
Parses Tanzil-style Warsh/Qalun/Duri/Shuba/Sousi files (different format
from Hafs `quran_bare.txt`) and reruns the primary statistic on each.
"""
from __future__ import annotations
import io
import sys
import re
from collections import Counter
from pathlib import Path
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ARABIC_LETTERS = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
ARABIC_LETTERS_SET = set(ARABIC_LETTERS)
MEDINAN = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 55,
           57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 76, 98, 99, 110}
NUZUL = [96, 68, 73, 74, 1, 111, 81, 87, 92, 89, 93, 94, 103, 100, 108,
         102, 107, 109, 105, 113, 114, 112, 53, 80, 97, 91, 85, 95, 106,
         101, 75, 104, 77, 50, 90, 86, 54, 38, 7, 72, 36, 25, 35, 19, 20,
         56, 26, 27, 28, 17, 10, 11, 12, 15, 6, 37, 31, 34, 39, 40, 41, 42,
         43, 44, 45, 46, 51, 88, 18, 16, 71, 14, 21, 23, 32, 52, 67, 69, 70,
         78, 79, 82, 84, 30, 29, 83, 2, 8, 3, 33, 60, 4, 99, 57, 47, 13, 55,
         76, 65, 98, 59, 24, 22, 63, 58, 49, 66, 64, 61, 62, 48, 5, 9, 110]


def hafs_load() -> dict[int, str]:
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


def load_riwaya(path: Path) -> dict[int, str] | None:
    raw = path.read_text(encoding="utf-8")
    chunks = re.split(r"سُورَةُ[^\n]*\n", raw)
    chunks = [c for c in chunks if c.strip()]
    if len(chunks) != 114:
        print(f"WARN: got {len(chunks)} chunks instead of 114 for {path}")
        return None
    return {i + 1: chunks[i] for i in range(114)}


def to_bare(text: str) -> str:
    return "".join(c for c in text if c in ARABIC_LETTERS_SET)


def letter_freq(text: str) -> tuple[np.ndarray, int]:
    only = to_bare(text)
    n = len(only)
    if n == 0:
        return np.zeros(28), 0
    counts = Counter(only)
    return np.array([counts.get(c, 0) / n for c in ARABIC_LETTERS]), n


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
    md_label = np.array([1 if (i + 1) in MEDINAN else 0 for i in range(114)])
    nuzul_idx = np.array([s - 1 for s in NUZUL])

    sources = [("hafs", hafs_load())]
    riwayat_dir = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\data\corpora\ar\riwayat")
    for name in ["warsh", "qalun", "duri", "shuba", "sousi"]:
        sources.append((name, load_riwaya(riwayat_dir / f"{name}.txt")))

    print(f"{'riwaya':8s} {'total_let':>10s} {'L_m':>8s} {'L_n':>8s} "
          f"{'L_greedy':>9s} {'null_mean':>10s} {'null_std':>9s} "
          f"{'z':>7s} {'p':>7s} {'below/B':>9s}")
    print("-" * 102)
    results = {}
    for name, surah_text in sources:
        if surah_text is None:
            continue
        F = np.zeros((114, 28))
        Nlet = np.zeros(114)
        for i in range(1, 115):
            F[i - 1], Nlet[i - 1] = letter_freq(surah_text[i])
        if Nlet.min() == 0:
            print(f"{name:8s} EMPTY surahs detected; skipping")
            continue
        logN = np.log(Nlet)
        F_det = detrend(F, logN, md_label)
        L_m = L2_tour(np.arange(114), F_det)
        L_n = L2_tour(nuzul_idx, F_det)
        # greedy NN from surah-1
        n = 114
        visited = [0]; used = {0}; cur = 0
        while len(visited) < n:
            best_d, best_j = np.inf, -1
            for j in range(n):
                if j in used:
                    continue
                d = float(np.linalg.norm(F_det[cur] - F_det[j]))
                if d < best_d:
                    best_d, best_j = d, j
            visited.append(best_j); used.add(best_j); cur = best_j
        L_g = L2_tour(np.array(visited), F_det)
        np.random.seed(20260501)
        B = 2000
        nulls = np.array([L2_tour(np.random.permutation(114), F_det) for _ in range(B)])
        z = (L_m - nulls.mean()) / nulls.std()
        p = (np.sum(nulls <= L_m) + 1) / (B + 1)
        below = int(np.sum(nulls < L_m))
        print(f"{name:8s} {Nlet.sum():>10.0f} {L_m:>8.4f} {L_n:>8.4f} "
              f"{L_g:>9.4f} {nulls.mean():>10.4f} {nulls.std():>9.4f} "
              f"{z:>+7.3f} {p:>7.4f} {below:>4d}/{B}")
        results[name] = dict(L_m=L_m, L_n=L_n, L_greedy=L_g,
                             null_mean=float(nulls.mean()),
                             null_std=float(nulls.std()), z=float(z), p=float(p))

    if len(results) > 1:
        print("\nCV across riwayat:")
        for k in ["L_m", "L_n", "L_greedy", "z"]:
            vals = np.array([results[n][k] for n in results])
            cv = vals.std() / abs(vals.mean()) if vals.mean() else float("nan")
            print(f"  {k}: mean={vals.mean():.4f}  std={vals.std():.4f}  CV={cv:.4f}  "
                  f"min={vals.min():.4f}  max={vals.max():.4f}")


if __name__ == "__main__":
    main()
