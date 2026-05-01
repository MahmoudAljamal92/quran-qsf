"""exp176 — Mushaf-as-Tour Coherence
Frozen PREREG implementation. See PREREG.md.
"""
from __future__ import annotations
import io
import sys
import json
import os
from collections import Counter
from pathlib import Path
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"
OUT_DIR = ROOT / "results" / "experiments" / "exp176_mushaf_tour"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ARABIC_LETTERS = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
MEDINAN = {2, 3, 4, 5, 8, 9, 22, 24, 33, 47, 48, 49, 55,
           57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 76, 98, 99, 110}
SEED = 20260501
B = 5000


def load_surahs() -> dict[int, str]:
    surahs: dict[int, list[str]] = {i: [] for i in range(1, 115)}
    raw = DATA.read_text(encoding="utf-8")
    for line in raw.splitlines():
        parts = line.split("|", 2)
        if len(parts) < 3 or not parts[0].strip().isdigit():
            continue
        s = int(parts[0])
        if 1 <= s <= 114:
            surahs[s].append(parts[2].strip())
    return {i: " ".join(surahs[i]) for i in range(1, 115)}


def letter_only(text: str) -> str:
    return "".join(c for c in text if c in ARABIC_LETTERS)


def letter_freq(text: str) -> tuple[np.ndarray, int]:
    only = letter_only(text)
    n = len(only)
    if n == 0:
        return np.zeros(len(ARABIC_LETTERS)), 0
    counts = Counter(only)
    return np.array([counts.get(c, 0) / n for c in ARABIC_LETTERS]), n


def bigram_freq(text: str, top_bigrams: list[str]) -> np.ndarray:
    only = letter_only(text)
    if len(only) < 2:
        return np.zeros(len(top_bigrams))
    counts = Counter(only[i:i + 2] for i in range(len(only) - 1))
    total = sum(counts.values())
    if total == 0:
        return np.zeros(len(top_bigrams))
    return np.array([counts.get(bg, 0) / total for bg in top_bigrams])


def find_top_bigrams(texts: dict[int, str], k: int = 50) -> list[str]:
    bg = Counter()
    for s in range(1, 115):
        only = letter_only(texts[s])
        for i in range(len(only) - 1):
            bg[only[i:i + 2]] += 1
    return [b for b, _ in bg.most_common(k)]


def detrend_features(F: np.ndarray, logN: np.ndarray, md: np.ndarray) -> np.ndarray:
    X = np.column_stack([np.ones(len(logN)), logN, logN**2, logN**3, md])
    R = np.zeros_like(F)
    for k in range(F.shape[1]):
        beta, *_ = np.linalg.lstsq(X, F[:, k], rcond=None)
        R[:, k] = F[:, k] - X @ beta
    return R


def tour_length_l2(idx: np.ndarray, F: np.ndarray) -> float:
    return float(np.sum(np.linalg.norm(np.diff(F[idx], axis=0), axis=1)))


def tour_length_cos(idx: np.ndarray, F: np.ndarray) -> float:
    p = F[idx]
    norms = np.linalg.norm(p, axis=1, keepdims=True) + 1e-12
    pn = p / norms
    cos = np.sum(pn[:-1] * pn[1:], axis=1)
    return float(np.sum(1 - cos))


def greedy_tour_l2(F: np.ndarray, start: int = 0) -> float:
    n = len(F)
    visited = [start]
    used = {start}
    cur = start
    while len(visited) < n:
        best_d, best_j = np.inf, -1
        for j in range(n):
            if j in used:
                continue
            d = float(np.linalg.norm(F[cur] - F[j]))
            if d < best_d:
                best_d, best_j = d, j
        visited.append(best_j)
        used.add(best_j)
        cur = best_j
    return tour_length_l2(np.array(visited), F)


def perm_null(F: np.ndarray, statistic, B: int, seed: int,
              stratify_md: np.ndarray | None = None) -> np.ndarray:
    rng = np.random.default_rng(seed)
    nulls = np.zeros(B)
    for b in range(B):
        if stratify_md is None:
            perm = rng.permutation(114)
        else:
            perm = np.arange(114)
            for lbl in [0, 1]:
                ix = np.where(stratify_md == lbl)[0]
                rng.shuffle(ix)
                perm[stratify_md == lbl] = ix
        nulls[b] = statistic(perm, F)
    return nulls


def summarise(L_obs: float, nulls: np.ndarray) -> dict:
    z = float((L_obs - nulls.mean()) / nulls.std())
    p = float((np.sum(nulls <= L_obs) + 1) / (len(nulls) + 1))
    frac_below = float(np.mean(nulls < L_obs))
    return dict(
        L_obs=L_obs,
        null_mean=float(nulls.mean()),
        null_std=float(nulls.std()),
        null_min=float(nulls.min()),
        null_max=float(nulls.max()),
        z=z,
        p_one_sided=p,
        frac_strictly_below=frac_below,
    )


def main() -> None:
    print("=" * 70)
    print("exp176 — Mushaf-as-Tour Coherence (frozen PREREG)")
    print("=" * 70)
    surah_text = load_surahs()
    md_label = np.array([1 if (i + 1) in MEDINAN else 0 for i in range(114)])

    F1 = np.zeros((114, len(ARABIC_LETTERS)))
    Nlet = np.zeros(114)
    for i in range(1, 115):
        F1[i - 1], Nlet[i - 1] = letter_freq(surah_text[i])
    logN = np.log(Nlet)
    F1_det = detrend_features(F1, logN, md_label)

    top50 = find_top_bigrams(surah_text, 50)
    F2 = np.array([bigram_freq(surah_text[i], top50) for i in range(1, 115)])
    F2_det = detrend_features(F2, logN, md_label)

    mushaf = np.arange(114)
    print(f"\nMushaf statistics:")
    primary_obs = tour_length_l2(mushaf, F1_det)
    print(f"  Primary  L(F1_det, L2)        = {primary_obs:.4f}")
    sec1_obs = tour_length_l2(mushaf, F1)
    print(f"  Sec-1    L(F1_raw, L2)        = {sec1_obs:.4f}")
    sec2_obs = tour_length_l2(mushaf, F2_det)
    print(f"  Sec-2    L(F2_det, L2)        = {sec2_obs:.4f}")
    sec3_obs = tour_length_cos(mushaf, F2)
    print(f"  Sec-3    L(F2_raw, cosine)    = {sec3_obs:.4f}")

    greedy = greedy_tour_l2(F1_det, 0)
    print(f"\n  Greedy NN (F1_det) from surah-1: {greedy:.4f}  "
          f"(Mushaf is {primary_obs/greedy:.2f}x greedy)")

    print(f"\nRunning permutation nulls B={B} ...")
    nulls_A_primary = perm_null(F1_det, tour_length_l2, B, SEED)
    nulls_A_sec1 = perm_null(F1, tour_length_l2, B, SEED + 1)
    nulls_A_sec2 = perm_null(F2_det, tour_length_l2, B, SEED + 2)
    nulls_A_sec3 = perm_null(F2, tour_length_cos, B, SEED + 3)
    nulls_B_primary = perm_null(F1_det, tour_length_l2, B, SEED + 4,
                                stratify_md=md_label)

    receipt = {
        "experiment": "exp176_mushaf_tour",
        "seed": SEED,
        "B": B,
        "n_surahs": 114,
        "n_letters_total": int(Nlet.sum()),
        "feature_dim_F1": F1.shape[1],
        "feature_dim_F2": F2.shape[1],
        "greedy_nn_F1_det_from_surah1": greedy,
        "primary_F1_det_L2_NullA": summarise(primary_obs, nulls_A_primary),
        "primary_F1_det_L2_NullB_md_strat": summarise(primary_obs, nulls_B_primary),
        "secondary_F1_raw_L2_NullA": summarise(sec1_obs, nulls_A_sec1),
        "secondary_F2_det_L2_NullA": summarise(sec2_obs, nulls_A_sec2),
        "secondary_F2_raw_cos_NullA": summarise(sec3_obs, nulls_A_sec3),
    }

    # Verdict
    p = receipt["primary_F1_det_L2_NullA"]
    pB = receipt["primary_F1_det_L2_NullB_md_strat"]
    cond1 = (p["z"] <= -4 and p["p_one_sided"] <= 0.001 and
             pB["z"] <= -4 and pB["p_one_sided"] <= 0.001)
    cond2 = any(receipt[k]["z"] <= -4 and receipt[k]["p_one_sided"] <= 0.001
                for k in ["secondary_F1_raw_L2_NullA",
                          "secondary_F2_det_L2_NullA",
                          "secondary_F2_raw_cos_NullA"])
    cond3 = p["frac_strictly_below"] <= 1.0 / B

    if cond1 and cond2 and cond3:
        verdict = "CONFIRM"
    elif p["z"] <= -2.5 and p["p_one_sided"] <= 0.01:
        verdict = "CONFIRM_WEAK"
    else:
        verdict = "REFUTE"
    receipt["verdict"] = verdict
    receipt["verdict_conditions"] = dict(cond1=cond1, cond2=cond2, cond3=cond3)

    print("\n=== Receipts ===")
    for k in ["primary_F1_det_L2_NullA", "primary_F1_det_L2_NullB_md_strat",
              "secondary_F1_raw_L2_NullA", "secondary_F2_det_L2_NullA",
              "secondary_F2_raw_cos_NullA"]:
        v = receipt[k]
        print(f"  {k:38s}: L={v['L_obs']:.4f}  null={v['null_mean']:.4f}±"
              f"{v['null_std']:.4f}  min={v['null_min']:.4f}  z={v['z']:+.3f}  "
              f"p={v['p_one_sided']:.4f}  below={v['frac_strictly_below']:.5f}")
    print(f"\nVERDICT: {verdict}")
    print(f"  cond1 (primary in both nulls): {cond1}")
    print(f"  cond2 (≥1 secondary):          {cond2}")
    print(f"  cond3 (frac below ≤ 1/B):      {cond3}")

    out_json = OUT_DIR / "receipt.json"
    out_json.write_text(json.dumps(receipt, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"\nWrote {out_json}")

    # Figure
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(11, 4))
        ax = axes[0]
        ax.hist(nulls_A_primary, bins=60, color="0.7", edgecolor="k", alpha=0.8,
                label=f"Null A (perm), B={B}")
        ax.axvline(primary_obs, color="C3", lw=2,
                   label=f"Mushaf={primary_obs:.3f}")
        ax.axvline(greedy, color="C2", lw=2, ls="--",
                   label=f"Greedy NN={greedy:.3f}")
        ax.set_xlabel("Tour length L (F1 detrended, L2)")
        ax.set_ylabel("Count")
        ax.set_title("Mushaf vs random permutations\n"
                     f"z={p['z']:+.2f}  p={p['p_one_sided']:.4f}")
        ax.legend(loc="upper right", fontsize=9)
        ax = axes[1]
        ax.hist(nulls_B_primary, bins=60, color="0.7", edgecolor="k", alpha=0.8,
                label=f"Null B (M/D-strat)")
        ax.axvline(primary_obs, color="C3", lw=2, label="Mushaf")
        ax.set_xlabel("Tour length L (F1 detrended, L2)")
        ax.set_title("Mushaf vs M/D-stratified permutations\n"
                     f"z={pB['z']:+.2f}  p={pB['p_one_sided']:.4f}")
        ax.legend(loc="upper right", fontsize=9)
        fig.tight_layout()
        fig_path = OUT_DIR / "tour_null_distribution.png"
        fig.savefig(fig_path, dpi=120)
        print(f"Wrote {fig_path}")
    except Exception as e:
        print(f"(figure skipped: {e})")


if __name__ == "__main__":
    main()
