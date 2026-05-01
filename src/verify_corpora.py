# -*- coding: utf-8 -*-
"""
src/verify_corpora.py
=====================
Sanity-check gate. Every corpus must pass before it enters the pipeline.

Checks per corpus:
    (G1) at least 10 units
    (G2) no unit has > 80% of verses being single-token (rules out meter-labels)
    (G3) no unit has > 50% of verses being identical (rules out
         "Genesis Genesis Genesis" pickle bug)
    (G4) verse word-count variability across the corpus is reasonable
         (coefficient of variation of per-verse word count in [0.05, 3.0])
    (G5) Arabic-script ratio of verse text > 40% (rules out language mixups)
"""
from __future__ import annotations

import sys
from collections import Counter

import numpy as np

from . import raw_loader as rl


def _arabic_ratio(verse: str) -> float:
    if not verse:
        return 0.0
    arab = sum(1 for c in verse if "\u0600" <= c <= "\u06FF")
    alpha = sum(1 for c in verse if c.isalpha())
    return arab / max(alpha, 1)


def verify_corpus(
    name: str, units: list[rl.Unit], require_arabic: bool = True
) -> tuple[bool, list[str]]:
    """Return (ok, [issues]). Issues are human-readable."""
    issues: list[str] = []
    if len(units) < 10:
        issues.append(f"G1 FAIL: only {len(units)} units (need >= 10)")

    for u in units:
        tokens_per_verse = [len(v.split()) for v in u.verses]
        if not tokens_per_verse:
            continue
        frac_single = sum(1 for k in tokens_per_verse if k <= 1) / len(tokens_per_verse)
        if frac_single > 0.80:
            issues.append(
                f"G2 FAIL: unit {u.label} has {frac_single*100:.0f}% "
                f"single-token verses"
            )
            break
        cnt = Counter(u.verses)
        most, n_most = cnt.most_common(1)[0]
        frac_same = n_most / len(u.verses)
        if frac_same > 0.50:
            issues.append(
                f"G3 FAIL: unit {u.label} has {frac_same*100:.0f}% "
                f"identical verses (example: {most[:40]!r})"
            )
            break

    all_wc = []
    ar_ratios = []
    for u in units:
        for v in u.verses:
            all_wc.append(len(v.split()))
            if require_arabic:
                ar_ratios.append(_arabic_ratio(v))
    if all_wc:
        mean = np.mean(all_wc); std = np.std(all_wc)
        cv = std / max(mean, 1e-9)
        if cv < 0.05 or cv > 3.0:
            issues.append(
                f"G4 FAIL: corpus-level verse-wc CV = {cv:.3f} "
                f"(outside [0.05, 3.0]; mean={mean:.1f}, std={std:.1f})"
            )
    if require_arabic and ar_ratios:
        mean_ar = float(np.mean(ar_ratios))
        if mean_ar < 0.40:
            issues.append(
                f"G5 FAIL: mean Arabic-script ratio = {mean_ar:.2f} "
                f"(need >= 0.40)"
            )

    return (len(issues) == 0), issues


def verify_all(corpora: dict[str, list[rl.Unit]]) -> dict[str, dict]:
    report: dict[str, dict] = {}
    print("=" * 72)
    print("CORPUS SANITY-CHECK GATE")
    print("=" * 72)
    for name, units in corpora.items():
        require_arabic = name != "iliad_greek"
        ok, issues = verify_corpus(name, units, require_arabic=require_arabic)
        report[name] = {
            "ok": ok, "n_units": len(units), "issues": issues
        }
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name:<22s}  n_units={len(units):>5d}")
        for iss in issues:
            print(f"         - {iss}")
    print()
    return report


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    corpora = rl.load_all(include_extras=True)
    report = verify_all(corpora)
    n_fail = sum(1 for v in report.values() if not v["ok"])
    if n_fail:
        print(f"[!] {n_fail}/{len(report)} corpora FAILED sanity gate.")
    else:
        print(f"[OK] All {len(report)} corpora passed.")
