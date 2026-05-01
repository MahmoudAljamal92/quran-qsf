"""Envelope analysis for exp95e: does V1/total-corpus letter ratio
predict K=2 recall?

Run from repo root:
    python scripts/analyse_exp95e_envelope.py             # default scope = v1
    python scripts/analyse_exp95e_envelope.py --scope short
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import load_phase  # noqa: E402
from experiments.exp95e_full_114_consensus_universal._enumerate import letters_28  # noqa: E402


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx * dy > 0 else float("nan")


def spearman(xs: list[float], ys: list[float]) -> float:
    def ranks(v: list[float]) -> list[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0  # 1-based avg rank
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    return pearson(ranks(xs), ranks(ys))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=["v1", "short"], default="v1",
                        help="Which exp95e receipt to analyse (default: v1).")
    args = parser.parse_args()
    scope = args.scope

    base = Path(f"results/experiments/exp95e_full_114_consensus_universal/{scope}")
    receipt_path = base / "exp95e_full_114_consensus_universal.json"
    d = json.loads(receipt_path.read_text(encoding="utf-8"))
    ps = d["per_surah"]
    print(f"# Scope: {scope}")
    print(f"# Receipt: {receipt_path}")
    print()

    print("Loading phase_06_phi_m corpus to compute total surah letters_28 ...")
    phi = load_phase("phase_06_phi_m")
    quran = phi["state"]["CORPORA"]["quran"]
    print(f"Loaded {len(quran)} surahs.")
    print()

    rows: list[dict] = []
    for u in quran:
        label = getattr(u, "label", None)
        if label not in ps:
            continue
        v1_text = letters_28(u.verses[0])
        full_text = letters_28(" ".join(u.verses))
        n_v1 = len(v1_text)
        n_full = len(full_text)
        ratio = n_v1 / n_full if n_full > 0 else 0.0
        row = {
            "surah": label,
            "n_verses": len(u.verses),
            "n_v1_letters": n_v1,
            "n_total_letters": n_full,
            "v1_over_total": ratio,
            "recall_K1": ps[label]["recall_K1"],
            "recall_K2": ps[label]["recall_K2"],
            "recall_K3": ps[label]["recall_K3"],
            "gzip": ps[label]["recall_solo_gzip"],
            "lzma": ps[label]["recall_solo_lzma"],
            "zstd": ps[label]["recall_solo_zstd"],
        }
        rows.append(row)

    rows.sort(key=lambda r: -r["v1_over_total"])

    print(f"# Envelope analysis ({len(rows)} surahs)")
    print()
    print(f"{'surah':6s} {'verses':>6s} {'v1_let':>7s} {'tot_let':>8s} "
          f"{'ratio':>6s}  {'K1':>5s} {'K2':>5s} {'K3':>5s}  "
          f"{'gz':>5s} {'lz':>5s} {'zs':>5s}")
    print("-" * 92)
    for r in rows:
        print(
            f"{r['surah']:6s} {r['n_verses']:>6d} {r['n_v1_letters']:>7d} "
            f"{r['n_total_letters']:>8d} {r['v1_over_total']:>6.3f}  "
            f"{r['recall_K1']:>5.3f} {r['recall_K2']:>5.3f} {r['recall_K3']:>5.3f}  "
            f"{r['gzip']:>5.3f} {r['lzma']:>5.3f} {r['zstd']:>5.3f}"
        )

    ratios = [r["v1_over_total"] for r in rows]
    log_total = [math.log10(r["n_total_letters"]) for r in rows]
    k2 = [r["recall_K2"] for r in rows]
    k1 = [r["recall_K1"] for r in rows]
    gzip_solo = [r["gzip"] for r in rows]
    lzma_solo = [r["lzma"] for r in rows]
    zstd_solo = [r["zstd"] for r in rows]

    print()
    print("# Correlations")
    print()
    print(f"{'predictor':25s}  {'pearson':>8s}  {'spearman':>9s}")
    print("-" * 50)
    for name, x in [
        ("v1_over_total -> K2", ratios),
        ("log10(total_letters) -> K2", log_total),
        ("v1_over_total -> K1", ratios),
        ("log10(total_letters) -> K1", log_total),
        ("v1_over_total -> gzip", ratios),
        ("v1_over_total -> lzma", ratios),
        ("v1_over_total -> zstd", ratios),
    ]:
        target_name = name.split("->")[-1].strip()
        target = {
            "K2": k2, "K1": k1, "gzip": gzip_solo,
            "lzma": lzma_solo, "zstd": zstd_solo,
        }[target_name]
        p = pearson(x, target)
        s = spearman(x, target)
        print(f"{name:25s}  {p:>+8.4f}  {s:>+9.4f}")

    print()
    print("# Threshold check: does K2 = 1.0 cleanly separate by ratio or total length?")
    perfect = [r for r in rows if r["recall_K2"] >= 0.999]
    failed = [r for r in rows if r["recall_K2"] < 1e-9]
    middling = [r for r in rows if 1e-9 <= r["recall_K2"] < 0.999]
    if perfect:
        rs = [r["v1_over_total"] for r in perfect]
        ts = [r["n_total_letters"] for r in perfect]
        print(f"  K2 perfect ({len(perfect)} surahs):  v1/total min={min(rs):.3f} max={max(rs):.3f} median={sorted(rs)[len(rs)//2]:.3f}; total_letters max={max(ts):>5d}")
    if middling:
        rs = [r["v1_over_total"] for r in middling]
        ts = [r["n_total_letters"] for r in middling]
        print(f"  K2 middling ({len(middling)} surahs):  v1/total min={min(rs):.3f} max={max(rs):.3f} median={sorted(rs)[len(rs)//2]:.3f}; total_letters min={min(ts):>5d} max={max(ts):>5d}")
    if failed:
        rs = [r["v1_over_total"] for r in failed]
        ts = [r["n_total_letters"] for r in failed]
        print(f"  K2 zero    ({len(failed)} surahs):  v1/total min={min(rs):.3f} max={max(rs):.3f} median={sorted(rs)[len(rs)//2]:.3f}; total_letters min={min(ts):>5d}")

    out_csv = base / "envelope_table.csv"
    cols = ["surah", "n_verses", "n_v1_letters", "n_total_letters",
            "v1_over_total", "recall_K1", "recall_K2", "recall_K3",
            "gzip", "lzma", "zstd"]
    lines = [",".join(cols)]
    for r in rows:
        lines.append(",".join(str(r[c]) for c in cols))
    out_csv.write_text("\n".join(lines), encoding="utf-8")
    print()
    print(f"Wrote envelope table -> {out_csv}")


if __name__ == "__main__":
    main()
