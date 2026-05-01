"""scripts/_rigveda_sizing.py -- pre-stage sizing diagnostic for exp104e.

Surveys all 10 Rigveda mandalas; reports per-sukta consonant-skeleton lengths
and identifies viable target candidates clearing the 1000-letter floor.
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent

# Devanagari consonants U+0915 ... U+0939 (क-ह) plus extensions
DEVA_CONS: set[str] = {chr(c) for c in range(0x0915, 0x0939 + 1)}
DEVA_CONS |= {"\u0929", "\u0931", "\u0934"}  # ऩ ऱ ऴ
# nukta-modified: ऩ ऱ ऴ क़ ख़ ग़ ज़ ड़ ढ़ फ़ य़
DEVA_CONS |= {chr(c) for c in range(0x0958, 0x0960)}


def consonant_skeleton(text: str) -> str:
    out: list[str] = []
    for ch in unicodedata.normalize("NFC", text):
        if ch in DEVA_CONS:
            out.append(ch)
    return "".join(out)


def main() -> int:
    all_suktas: list[tuple[int, int, int]] = []
    for mandala_num in range(1, 11):
        path = _ROOT / "data" / "corpora" / "sa" / f"rigveda_mandala_{mandala_num}.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for entry in data:
            skel = consonant_skeleton(entry["text"])
            all_suktas.append((entry["mandala"], entry["sukta"], len(skel)))

    print(f"Total suktas: {len(all_suktas)}")
    lens = [s[2] for s in all_suktas]
    lens_sorted = sorted(lens)
    print(
        f"Consonant-skeleton length: "
        f"min={min(lens)}, "
        f"median={lens_sorted[len(lens) // 2]}, "
        f"mean={sum(lens) / len(lens):.0f}, "
        f"max={max(lens)}"
    )
    print()

    n_above_1000 = sum(1 for s in all_suktas if s[2] >= 1000)
    n_above_1500 = sum(1 for s in all_suktas if s[2] >= 1500)
    n_above_2000 = sum(1 for s in all_suktas if s[2] >= 2000)
    n_above_2500 = sum(1 for s in all_suktas if s[2] >= 2500)
    print(f"Suktas with >=1000 consonants: {n_above_1000} / {len(all_suktas)}")
    print(f"Suktas with >=1500 consonants: {n_above_1500} / {len(all_suktas)}")
    print(f"Suktas with >=2000 consonants: {n_above_2000} / {len(all_suktas)}")
    print(f"Suktas with >=2500 consonants: {n_above_2500} / {len(all_suktas)}")
    print()

    print("Top 15 longest suktas (cleanest exp104e target candidates):")
    for m, s, n in sorted(all_suktas, key=lambda x: -x[2])[:15]:
        print(f"  RV {m}.{s}: {n} consonants")
    print()

    rv11 = [(m, s, n) for m, s, n in all_suktas if m == 1 and s == 1]
    if rv11:
        n = rv11[0][2]
        status = "clears 1000 floor" if n >= 1000 else "BELOW 1000 floor"
        print(f"Rigveda 1.1 (the Agni opener): {n} consonants -- {status}")

    # Peer-pool feasibility for top candidates: how many other suktas
    # fall within +/-30% of each top candidate?
    print()
    print("Peer-pool feasibility (length-matched +/-30%) for top 5 candidates:")
    for m, s, n in sorted(all_suktas, key=lambda x: -x[2])[:5]:
        lo, hi = int(n * 0.70), int(n * 1.30)
        n_peers = sum(1 for (m2, s2, n2) in all_suktas
                      if (m2, s2) != (m, s) and lo <= n2 <= hi)
        ok = "OK" if n_peers >= 100 else "WOULD-FAIL audit"
        print(f"  RV {m}.{s} (n={n}): peers in [{lo},{hi}] = {n_peers}  ({ok})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
