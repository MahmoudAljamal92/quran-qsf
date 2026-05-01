"""scripts/_audit_daodejing_chapter_lengths.py
==================================================
Investigate why F55 returned FAIL_recall_below_unity on Daodejing
chapter 1. Test whether a longer chapter passes the strict τ = 2.0 recall.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.exp112_F55_daodejing_bigram.run import (
    load_daodejing_chapters, bigram_dist_l1_half,
)

chapters = load_daodejing_chapters()
print(f"# chapter lengths (skeleton, descending):")
lens = sorted([(c["chapter"], len(c["skeleton"])) for c in chapters],
              key=lambda t: -t[1])
for ch, n in lens[:10]:
    print(f"#   chapter {ch:>2d}: {n} chars")
all_lens = [n for _, n in lens]
print(f"# median: {sorted(all_lens)[len(all_lens)//2]}")
print(f"# min: {min(all_lens)}, max: {max(all_lens)}")

# Test recall on a few different chapter lengths
alphabet = sorted(set("".join(c["skeleton"] for c in chapters)))
print(f"\n# alphabet size: {len(alphabet)}")

for ch_target in [1, 38, 64, 39, 31, 20, 81]:
    target = chapters[ch_target - 1]["skeleton"]
    n_var = 0; n_pass = 0; max_d = 0; min_d = 999
    fails = []
    for i in range(len(target)):
        for c in alphabet:
            if c == target[i]:
                continue
            v = target[:i] + c + target[i+1:]
            d = bigram_dist_l1_half(target, v)
            n_var += 1
            if d >= 2.0:
                n_pass += 1
            else:
                fails.append((i, target[i], c, d))
            if d > max_d:
                max_d = d
            if d < min_d:
                min_d = d
    rec = n_pass / n_var
    print(f"\n# Chapter {ch_target:>2d} ({len(target):>3d} chars): "
          f"recall = {rec:.6f} ({n_pass}/{n_var}); "
          f"max Δ = {max_d}, min Δ = {min_d}")
    if fails:
        # Show 3 sample failures
        print(f"#   3 sample failures (pos, original, substitute, Δ):")
        for i, orig, sub, d in fails[:3]:
            ctx_lo = max(0, i-2)
            ctx_hi = min(len(target), i+3)
            print(f"#     pos {i:>2d}: '{orig}' -> '{sub}', Δ = {d:.4f}, "
                  f"context: ...{target[ctx_lo:ctx_hi]}...")
