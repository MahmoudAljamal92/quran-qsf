"""scripts/dryrun_cross_tradition.py
====================================
Dry-run of the three new cross-tradition loaders + Quran reference,
to confirm Phase 4 (P4) ingestion is wired correctly. Writes nothing.
"""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from raw_loader import (  # noqa: E402
    load_pali, load_vedic, load_avestan, load_quran_bare,
)


def _print_row(name: str, units):
    nv = np.array([u.n_verses() for u in units])
    nw = np.array([u.n_words() for u in units])
    n = len(units)
    print(
        f"  {name:>15s}  {n:>5d} units  "
        f"{int(nv.sum()):>6d} verses  "
        f"{int(nw.sum()):>8d} words  "
        f"median {int(np.median(nv)):>4d} v/u"
    )


if __name__ == "__main__":
    print("=" * 64)
    print(" CROSS-TRADITION CORPORA -- unified dry-run")
    print("=" * 64)
    print()
    _print_row("quran (ref)", load_quran_bare())
    _print_row("pali",        load_pali())
    _print_row("vedic",       load_vedic())
    _print_row("avestan",     load_avestan())
    print()
    print("All four corpora successfully loaded.")
