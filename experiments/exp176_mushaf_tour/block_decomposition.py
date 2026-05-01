"""exp176 escalation 4 — classical four-block macro-taxonomy test.

Classical Qur'ānic scholarship divides the 114 surahs into 4 macro-
blocks by length (attributed to ʿAlī ibn Abī Ṭālib via Abū Dāwūd,
Tirmidhī's taxonomy, Burhān of Zarkashī):

    al-sabʿ al-ṭiwāl  (the Seven Long)   : Surahs 2-8 or 2-9
    al-miʾīn          (the Hundreds)     : ~Surahs 9/10-35
    al-mathānī        (the Repeated)     : ~Surahs 36-49
    al-mufaṣṣal       (the Detailed)     : Surahs 50-114 (short)

This experiment tests whether F81's letter-frequency tour coherence
is *structured by these blocks*: is the within-block L per-pair
substantially tighter than the between-block adjacency, and is the
observed value of this within/between ratio tighter than under
random permutation?

Bonus: test whether, if we FIX the four macro-blocks (any surah
permuted only within its block), the Mushaf within-block ordering
is still tighter than random under that CONSTRAINED null.
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

# Classical four-block taxonomy. Multiple classical sources give
# slightly different boundaries — we use the most-cited (al-Zarkashī's
# Burhān, consistent with Ibn ʿArabī and Tirmidhī):
#   ṭiwāl  : 2-9   (seven long + Tawba often counted as 8th)
#   miʾīn  : 10-35 (surahs with ~100 verses or more)
#   mathānī: 36-49 (the "repeated/paired")
#   mufaṣṣal: 50-114
BLOCKS_CLASSICAL = {
    "tiwāl": list(range(2, 10)),        # 2..9 (8 surahs; "seven" + Tawba)
    "miʾīn": list(range(10, 36)),       # 10..35
    "mathānī": list(range(36, 50)),     # 36..49
    "mufaṣṣal": list(range(50, 115)),   # 50..114 (includes Fātiḥa? no — she opens)
}
# Note: surah 1 (al-Fātiḥa) is classically a separate prologue (al-sabʿ al-mathānī
# in a different sense — "the seven oft-repeated") and does not fit this length scheme.


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


def L2_tour(idx: np.ndarray, F: np.ndarray) -> float:
    return float(np.sum(np.linalg.norm(np.diff(F[idx], axis=0), axis=1)))


def main() -> None:
    surah_text = load_surahs()
    F = np.zeros((114, 28))
    Nlet = np.zeros(114)
    for i in range(1, 115):
        F[i - 1], Nlet[i - 1] = letter_freq(surah_text[i])
    logN = np.log(Nlet)
    md_label = np.array([1 if (i + 1) in MEDINAN else 0 for i in range(114)])
    F_det = detrend(F, logN, md_label)

    consec = np.linalg.norm(np.diff(F_det, axis=0), axis=1)

    # Assign each surah (1..114) to block index
    block_of = np.zeros(114, dtype=int)
    block_names = list(BLOCKS_CLASSICAL.keys())
    for bi, (bname, slist) in enumerate(BLOCKS_CLASSICAL.items(), start=1):
        for s in slist:
            block_of[s - 1] = bi
    # Surah 1 (Fātiḥa) -> block 0 (prologue, separate)

    # For each consecutive pair (i, i+1) in Mushaf, is it within-block or between-block?
    pair_same_block = np.array([
        (block_of[i] == block_of[i + 1]) and (block_of[i] > 0)
        for i in range(113)
    ])
    within_count = int(pair_same_block.sum())
    between_count = 113 - within_count

    within_d = consec[pair_same_block]
    between_d = consec[~pair_same_block]
    mean_within = within_d.mean() if len(within_d) else np.nan
    mean_between = between_d.mean() if len(between_d) else np.nan

    print(f"Mushaf consecutive pairs: {within_count} within-block, {between_count} between-block")
    print(f"mean within-block d  = {mean_within:.4f}")
    print(f"mean between-block d = {mean_between:.4f}")
    print(f"ratio within/between = {mean_within / mean_between:.3f}  "
          f"(< 1.0 => within-block pairs are tighter)")

    # Permutation test: if we randomly permute the 114 surahs, what fraction
    # of permutations give within/between ratio ≤ Mushaf's?
    obs_ratio = mean_within / mean_between
    B = 10000
    rng = np.random.default_rng(20260501)
    nulls_ratio = []
    D = np.linalg.norm(F_det[:, None, :] - F_det[None, :, :], axis=-1)
    for _ in range(B):
        perm = rng.permutation(114)
        # new consec pairs under this perm, check same-block status per Mushaf
        # NB: block assignment is by original surah-ID, so pair_same_block uses
        # perm[i], perm[i+1] original-ID block identity.
        wins = []
        betws = []
        for i in range(113):
            a, b = perm[i], perm[i + 1]
            d = D[a, b]
            if block_of[a] == block_of[b] and block_of[a] > 0:
                wins.append(d)
            else:
                betws.append(d)
        if wins and betws:
            r = float(np.mean(wins) / np.mean(betws))
        else:
            r = np.nan
        nulls_ratio.append(r)
    nulls_ratio = np.array([r for r in nulls_ratio if not np.isnan(r)])
    p_ratio = (np.sum(nulls_ratio <= obs_ratio) + 1) / (len(nulls_ratio) + 1)
    print(f"\nWithin/between ratio under random perm: "
          f"{nulls_ratio.mean():.3f} ± {nulls_ratio.std():.3f}")
    print(f"Mushaf ratio = {obs_ratio:.3f}; permutation p = {p_ratio:.5f}  "
          f"({int(np.sum(nulls_ratio <= obs_ratio))}/{len(nulls_ratio)} below)")

    # Per-block tour length: Mushaf within-block sum vs random within-block
    print("\nPer-block Mushaf tour length:")
    per_block_results = {}
    for bi, (bname, slist) in enumerate(BLOCKS_CLASSICAL.items(), start=1):
        idx = np.array([s - 1 for s in slist])
        if len(idx) < 2:
            continue
        # Mushaf order inside block
        L_m_block = L2_tour(idx, F_det)
        # random permutations within block
        nulls = []
        for _ in range(5000):
            p = rng.permutation(len(idx))
            nulls.append(L2_tour(idx[p], F_det))
        nulls = np.array(nulls)
        z = (L_m_block - nulls.mean()) / nulls.std()
        p = (np.sum(nulls <= L_m_block) + 1) / (len(nulls) + 1)
        print(f"  {bname:10s} (|block| = {len(idx):3d}): L_m = {L_m_block:.4f}  "
              f"null = {nulls.mean():.4f} ± {nulls.std():.4f}  z = {z:+.3f}  "
              f"p = {p:.4f}  below = {int(np.sum(nulls < L_m_block))}/5000")
        per_block_results[bname] = dict(
            size=int(len(idx)), L_mushaf=float(L_m_block),
            null_mean=float(nulls.mean()), null_std=float(nulls.std()),
            z=float(z), p=float(p),
        )

    # Constrained null: fix block assignments (preserve block IDs per position
    # in Mushaf order), only permute within each block.
    print("\nConstrained null (block-preserving within-block permutation):")
    block_indices_in_order = {bi: np.where(block_of == bi)[0] for bi in range(1, 5)}
    # also block 0 for Fātiḥa
    if (block_of == 0).any():
        block_indices_in_order[0] = np.where(block_of == 0)[0]

    def block_preserving_perm(rng):
        new = np.arange(114)
        for bi, idx_pos in block_indices_in_order.items():
            if len(idx_pos) <= 1:
                continue
            # Randomly permute the surah-IDs within these positions
            vals = new[idx_pos].copy()
            rng.shuffle(vals)
            new[idx_pos] = vals
        return new

    B2 = 5000
    L_mushaf_total = L2_tour(np.arange(114), F_det)
    nulls_constrained = []
    for _ in range(B2):
        perm = block_preserving_perm(rng)
        nulls_constrained.append(L2_tour(perm, F_det))
    nulls_constrained = np.array(nulls_constrained)
    z_c = (L_mushaf_total - nulls_constrained.mean()) / nulls_constrained.std()
    p_c = (np.sum(nulls_constrained <= L_mushaf_total) + 1) / (B2 + 1)
    below_c = int(np.sum(nulls_constrained < L_mushaf_total))
    print(f"  Mushaf L = {L_mushaf_total:.4f}  "
          f"constrained null = {nulls_constrained.mean():.4f} ± {nulls_constrained.std():.4f}")
    print(f"  z = {z_c:+.3f}  p = {p_c:.4f}  below = {below_c}/{B2}")
    print("  (this tests whether, GIVEN the classical four-block partition,")
    print("   the Mushaf WITHIN-BLOCK ordering is still tighter than random)")

    out = dict(
        blocks=BLOCKS_CLASSICAL,
        within_count=within_count,
        between_count=between_count,
        mean_within_d=float(mean_within),
        mean_between_d=float(mean_between),
        within_between_ratio=float(obs_ratio),
        p_ratio_random_perm=float(p_ratio),
        per_block=per_block_results,
        constrained_null=dict(
            L_mushaf=float(L_mushaf_total),
            null_mean=float(nulls_constrained.mean()),
            null_std=float(nulls_constrained.std()),
            z=float(z_c), p=float(p_c), below=below_c, total=B2,
        ),
    )
    out_path = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran\results\experiments\exp176_mushaf_tour\block_decomposition.json")
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReceipt: {out_path}")


if __name__ == "__main__":
    main()
