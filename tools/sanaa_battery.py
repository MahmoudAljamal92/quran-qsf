"""tools/sanaa_battery.py — Run every Ṣanʿāʾ variant through F55 + F69.

Loads `data/external/sanaa_variants.json` and for each (canonical, sanaa)
pair reports:
  Δ_bigram (F55)         — bigram-histogram L1 distance
  k_min                  — implied lower bound on letter edits (Theorem F69)
  gzip-fingerprint Δ     — sequence-aware F68 form
  F55 verdict            — NEAR / VARIANT / DISTANT
  rasm-skeleton match    — does the diacritic-stripped 28-letter rasm match?

Prints a summary table and writes a JSON receipt under `results/auxiliary/`.

This is a forensic auditing tool: a PASS verdict here does not mean the
candidate text IS the Quran, only that the F55+F69 distance is consistent
with the published variants. To establish authenticity one needs paleographic
+ chains-of-transmission evidence, which are not stylometric.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.sanaa_compare import (  # noqa: E402
    bigram_histogram,
    delta_bigram,
    gzip_fingerprint_delta,
    normalise_arabic,
)


def audit_variant(v: dict) -> dict:
    canonical = v["canonical_text"]
    sanaa = v["sanaa_text"]

    n_can = normalise_arabic(canonical)
    n_san = normalise_arabic(sanaa)

    rasm_match = (n_can == n_san)
    h_can = bigram_histogram(n_can)
    h_san = bigram_histogram(n_san)
    d = delta_bigram(h_can, h_san)
    k_min = max(0, int((d + 1) // 2)) if d > 0 else 0
    gz_d = gzip_fingerprint_delta(n_can, n_san)

    if d == 0 and rasm_match:
        verdict = "RASM_IDENTICAL"
    elif d == 0:
        verdict = "BIGRAM_HISTOGRAM_TIE_RASM_DIFFERENT"   # word-reorder gap
    elif d <= 2:
        verdict = "NEAR_VARIANT_consistent_with_1_letter_edit"
    elif d <= 10:
        verdict = f"NEAR_VARIANT_consistent_with_up_to_{k_min}_letter_edits"
    elif d <= 50:
        verdict = f"VARIANT_consistent_with_up_to_{k_min}_letter_edits"
    else:
        verdict = f"DISTANT_VARIANT_at_least_{k_min}_letter_edits_apart"

    return {
        "id": v["id"],
        "location": v["location"],
        "rasm_difference_type": v["rasm_difference_type"],
        "source_citation": v["source_citation"],
        "rasm_skeleton_match": rasm_match,
        "skeleton_canonical_length": len(n_can.replace(" ", "")),
        "skeleton_sanaa_length": len(n_san.replace(" ", "")),
        "delta_bigram": d,
        "implied_k_min_letter_edits": k_min,
        "f55_verdict": verdict,
        "gzip_fingerprint_delta": round(gz_d, 5),
        "notes": v.get("notes", ""),
    }


def main(argv=None) -> int:
    fixture_path = ROOT / "data" / "external" / "sanaa_variants.json"
    out_dir = ROOT / "results" / "auxiliary"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(fixture_path, encoding="utf-8") as f:
        fixture = json.load(f)
    variants = fixture["variants"]

    print(f"\n=== Ṣanʿāʾ variant battery — {len(variants)} entries ===\n")
    print(f"  Fixture: {fixture_path.relative_to(ROOT)}")
    print(f"  Disclaimer: {fixture['_disclaimer']}\n")
    print(f"  {'ID':<35s}  {'Δ_bigram':>10s}  {'k_min':>6s}  {'gzip Δ':>8s}  Verdict")
    print("  " + "-" * 110)

    audited = []
    for v in variants:
        a = audit_variant(v)
        audited.append(a)
        gzd = f"{a['gzip_fingerprint_delta']:.4f}"
        print(f"  {a['id']:<35s}  {a['delta_bigram']:>10.2f}  {a['implied_k_min_letter_edits']:>6d}  {gzd:>8s}  {a['f55_verdict']}")

    out_path = out_dir / "_sanaa_battery.json"
    out_path.write_text(json.dumps({
        "fixture_about": fixture["_about"],
        "fixture_disclaimer": fixture["_disclaimer"],
        "n_variants": len(audited),
        "results": audited,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  Receipt: {out_path.relative_to(ROOT)}\n")

    print("  Honest interpretation:")
    print("  >> Each Δ_bigram is a *replicable distance number*, not a truth-value.")
    print("  >> k_min is the strict lower bound on letter changes (F69 theorem).")
    print("  >> A variant flagged BIGRAM_HISTOGRAM_TIE_RASM_DIFFERENT is in the")
    print("     F55 permutation-invariance gap — use F70 (sequence-aware) for those.")
    print("  >> To establish which reading is canonical, you need paleographic +")
    print("     chains-of-transmission evidence, NOT this stylometric tool.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
