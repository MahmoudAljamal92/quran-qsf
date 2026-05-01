"""One-shot summariser for exp95e v1 receipt.

Run from repo root:
    python scripts/summarise_exp95e_v1.py
"""
from __future__ import annotations

import json
from pathlib import Path


def band_k(v: float) -> str:
    if v >= 0.999:
        return "perfect (>=0.999)"
    if v >= 0.5:
        return "high (0.5-0.999)"
    if v > 0:
        return "low (0-0.5)"
    return "zero"


def main() -> None:
    receipt_path = Path("results/experiments/exp95e_full_114_consensus_universal/v1/exp95e_full_114_consensus_universal.json")
    d = json.loads(receipt_path.read_text(encoding="utf-8"))
    ps = d["per_surah"]

    print(f"Receipt: {receipt_path}")
    print(f"Verdict: {d.get('verdict', '(field not present)')}")
    print(f"Surahs: {d['n_surahs_scored']} / 114")
    print(f"Variants: {d['n_variants_total']}")
    print()

    print("Aggregate consensus recall (K = at least k compressors fire):")
    agg = d["aggregate"]
    print(f"  K=1: {agg['recall_K1']:.4f}")
    print(f"  K=2: {agg['recall_K2']:.4f}  <-- headline")
    print(f"  K=3: {agg['recall_K3']:.4f}")
    print(f"  K=4: {agg['recall_K4']:.4f}")
    print()

    print("Per-compressor solo aggregate recall:")
    solo = agg["recall_solo"]
    for c in ("gzip", "bz2", "lzma", "zstd"):
        print(f"  {c:6s}: {solo[c]:.4f}")
    print()

    print("ctrl-null FPR (false-positive rate on null pool):")
    cn = d["ctrl_null"]
    for c, v in cn["fpr_per_compressor_at_locked_tau"].items():
        print(f"  {c:6s}: {v:.4f}")
    for k, v in cn["fpr_by_consensus_K"].items():
        print(f"  K={k}: {v:.5f}")
    print()

    bands_k1 = {"perfect (>=0.999)": 0, "high (0.5-0.999)": 0, "low (0-0.5)": 0, "zero": 0}
    bands_k2 = {"perfect (>=0.999)": 0, "high (0.5-0.999)": 0, "low (0-0.5)": 0, "zero": 0}
    for v in ps.values():
        bands_k1[band_k(v["recall_K1"])] += 1
        bands_k2[band_k(v["recall_K2"])] += 1

    print("Per-surah K=1 recall distribution:")
    for k, v in bands_k1.items():
        print(f"  {k:25s} {v:3d}")
    print()
    print("Per-surah K=2 recall distribution:")
    for k, v in bands_k2.items():
        print(f"  {k:25s} {v:3d}")
    print()

    print("Top 12 surahs by K=2 recall:")
    top = sorted(ps.items(), key=lambda x: -x[1]["recall_K2"])[:12]
    for sid, v in top:
        print(
            f"  {sid}  n={v['n_variants']:5d}  "
            f"K1={v['recall_K1']:.4f}  K2={v['recall_K2']:.4f}  "
            f"K3={v['recall_K3']:.4f}  K4={v['recall_K4']:.4f}  "
            f"| gzip={v['recall_solo_gzip']:.3f}  bz2={v['recall_solo_bz2']:.3f}  "
            f"lzma={v['recall_solo_lzma']:.3f}  zstd={v['recall_solo_zstd']:.3f}"
        )
    print()

    print("Surahs with K=1 = 1.0 but K=2 = 0 (gzip-only catches all, others miss all):")
    for sid, v in ps.items():
        if v["recall_K1"] >= 0.999 and v["recall_K2"] < 1e-9:
            print(f"  {sid}  n={v['n_variants']:5d}  gzip={v['recall_solo_gzip']:.3f}")


if __name__ == "__main__":
    main()
