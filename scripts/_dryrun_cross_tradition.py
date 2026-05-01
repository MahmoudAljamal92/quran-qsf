# -*- coding: utf-8 -*-
"""Quick dry-run for the three new cross-tradition loaders."""
from __future__ import annotations

import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
from raw_loader import load_pali, load_vedic, load_avestan

# L5 (audit-fix 2026-04-26): robust Avestan label parser. The previous
# implementation `int(u.label.split("y")[2])` assumed exactly the format
# `yasna:y<NN>` and would silently break on any future fragment markers
# (e.g. `yasna:y01a`) or label-format change. The regex anchors on the
# canonical prefix and tolerates an optional trailing letter fragment.
_YASNA_LABEL_RE = re.compile(r"^yasna:y(\d+)[a-z]?$", re.IGNORECASE)

print("=" * 70)
print("Cross-tradition corpus dry-run")
print("=" * 70)

for name, fn in [("pali", load_pali), ("vedic", load_vedic), ("avestan", load_avestan)]:
    units = fn()
    if not units:
        print(f"\n{name}: 0 units (FAIL)")
        continue
    nv = np.array([u.n_verses() for u in units])
    nw = np.array([u.n_words() for u in units])
    print(f"\n{name}: {len(units)} units")
    print(f"  verses: median={int(np.median(nv))}, min={int(nv.min())}, max={int(nv.max())}, total={int(nv.sum())}")
    print(f"  words : median={int(np.median(nw))}, min={int(nw.min())}, max={int(nw.max())}, total={int(nw.sum())}")
    if name == "avestan":
        labels: list[int] = []
        bad: list[str] = []
        for u in units:
            m = _YASNA_LABEL_RE.match(u.label)
            if m:
                labels.append(int(m.group(1)))
            else:
                bad.append(u.label)
        labels.sort()
        if bad:
            print(f"  [warn] {len(bad)} unrecognised avestan label(s): "
                  f"{bad[:3]}{' ...' if len(bad) > 3 else ''}")
        print(f"  chapters present: {labels[:5]} ... {labels[-5:]}")
        print(f"  range: {min(labels)}..{max(labels)}, count: {len(labels)}")
        missing = [c for c in range(73) if c not in labels]
        print(f"  missing: {missing if missing else 'none'}")
        print("  Sample Yasna 1 (canonical LTR):")
        y1 = next((u for u in units if u.label == "yasna:y01"), None)
        if y1:
            for v in y1.verses[:3]:
                print(f"    | {v[:120]}")
        print("  Sample Yasna 28 (Gatha, oldest layer):")
        y28 = next((u for u in units if u.label == "yasna:y28"), None)
        if y28:
            for v in y28.verses[:3]:
                print(f"    | {v[:120]}")
