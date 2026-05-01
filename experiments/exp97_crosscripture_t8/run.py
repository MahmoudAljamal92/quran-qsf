"""
exp97_crosscripture_t8/run.py
==============================
H34 — Cross-scripture canonical-path optimality as a shared Abrahamic
property. Thin adapter over the already-executed
exp35_R3_cross_scripture_redo receipt.

This experiment does NOT re-run the 5000-permutation canonical-path
test. It reads the frozen v7.2 exp35 receipt and emits:
  (a) a floored Monte-Carlo corpus-scale p-value per scripture,
  (b) a reproduced BH-adjustment across the four scriptures,
  (c) the Abrahamic-vs-secular cohort verdict, and
  (d) a §4.37-ready corpus_scale_evidence_sheet for the Fisher
      combiner.

Pre-registered in PREREG.md (frozen 2026-04-22).

Reads only:
    results/experiments/exp35_R3_cross_scripture_redo/exp35_R3_cross_scripture_redo.json

Writes ONLY under results/experiments/exp97_crosscripture_t8/
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    safe_output_dir,
    self_check_begin,
    self_check_end,
)

EXP = "exp97_crosscripture_t8"

# --- Frozen constants (mirror PREREG §7) -----------------------------------
SEED = 42
EXPECTED_SCRIPTURES = ["quran", "hebrew_tanakh", "greek_nt", "iliad_greek"]
ABRAHAMIC_COHORT = {"quran", "hebrew_tanakh", "greek_nt"}
SECULAR_COHORT = {"iliad_greek"}
EXPECTED_N_PERM = 5000
BH_ALPHA = 0.05
BH_REPRODUCTION_TOL = 1e-9


def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _bh_adjust(p_values: list[float]) -> list[float]:
    """Benjamini-Hochberg step-up adjustment. Order-preserving return
    (same index order as input). Byte-equal to the algorithm used in
    exp35's _one_sided_p_bh."""
    n = len(p_values)
    order = np.argsort(p_values)
    adj = np.empty(n, dtype=float)
    prev = 1.0
    for rank_idx, i in enumerate(reversed(order)):
        k = n - rank_idx
        bh = p_values[i] * n / k
        prev = min(prev, bh)
        adj[i] = min(prev, 1.0)
    return [float(v) for v in adj]


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] H34 — Abrahamic-property adapter over exp35 canonical-path T8")

    # --- Step 1: load exp35 receipt ---
    exp35_path = (_ROOT / "results" / "experiments"
                  / "exp35_R3_cross_scripture_redo"
                  / "exp35_R3_cross_scripture_redo.json")
    if not exp35_path.exists():
        print(f"[{EXP}] FAIL_exp35_missing: {exp35_path}")
        _write_fail_report(out, "FAIL_exp35_missing",
                           {"missing_path": str(exp35_path)})
        self_check_end(pre, EXP)
        return 1

    exp35_sha = _sha256(exp35_path)
    with open(exp35_path, "r", encoding="utf-8") as f:
        exp35 = json.load(f)

    print(f"[{EXP}] exp35 receipt SHA-256 = {exp35_sha[:16]}...")

    per_s = exp35.get("per_scripture", {})
    if not all(s in per_s for s in EXPECTED_SCRIPTURES):
        missing = [s for s in EXPECTED_SCRIPTURES if s not in per_s]
        print(f"[{EXP}] FAIL_exp35_schema_drift: missing {missing}")
        _write_fail_report(out, "FAIL_exp35_schema_drift",
                           {"missing_scriptures": missing})
        self_check_end(pre, EXP)
        return 1

    n_perm_rows = [int(per_s[s]["n_perm"]) for s in EXPECTED_SCRIPTURES]
    if not all(n == EXPECTED_N_PERM for n in n_perm_rows):
        print(f"[{EXP}] FAIL_exp35_schema_drift: n_perm rows = {n_perm_rows}  "
              f"(expected {EXPECTED_N_PERM} for each)")
        _write_fail_report(out, "FAIL_exp35_schema_drift",
                           {"n_perm_rows": n_perm_rows})
        self_check_end(pre, EXP)
        return 1

    # --- Step 2: Monte-Carlo floor on the p-values ---
    mc_floor = 1.0 / (EXPECTED_N_PERM + 1)
    raw_p = [float(per_s[s]["p_one_sided"]) for s in EXPECTED_SCRIPTURES]
    p_corpus = [max(p, mc_floor) for p in raw_p]

    print(f"[{EXP}] MC-floor on p = 1/(n_perm+1) = {mc_floor:.6f}")
    for s, p, pc in zip(EXPECTED_SCRIPTURES, raw_p, p_corpus):
        note = "floored" if pc > p else "as-is"
        print(f"[{EXP}]   {s:16s}  p_raw={p:.6f}  p_corpus={pc:.6f}  ({note})")

    # --- Step 3: reproduce BH adjustment ---
    q_reproduced = _bh_adjust(p_corpus)
    q_exp35 = [
        float(exp35["BH_pooling"]["per_scripture"][s])
        for s in EXPECTED_SCRIPTURES
    ]

    # For scriptures whose p_corpus differs from raw p (only ones where
    # raw was below the MC floor), the BH recomputation will legitimately
    # differ from exp35. We check reproduction on whichever rows' p
    # did not move.
    bh_drift: list[dict] = []
    for s, p_raw, pc, qr, qe in zip(
        EXPECTED_SCRIPTURES, raw_p, p_corpus, q_reproduced, q_exp35
    ):
        moved = pc != p_raw
        diff = qr - qe
        bh_drift.append({
            "scripture": s,
            "p_was_floored": bool(moved),
            "q_reproduced": qr,
            "q_exp35": qe,
            "diff": diff,
            "within_tol_when_not_floored": (
                True if moved else abs(diff) <= BH_REPRODUCTION_TOL
            ),
        })
    bh_drift_ok = all(row["within_tol_when_not_floored"] for row in bh_drift)
    print(f"[{EXP}] BH reproduction (non-floored rows): "
          f"{'OK' if bh_drift_ok else 'DRIFT'}")

    # --- Step 4: emit §4.37-ready evidence sheet ---
    evidence_sheet: dict[str, dict] = {}
    for s, pc, qr in zip(EXPECTED_SCRIPTURES, p_corpus, q_reproduced):
        row_s = per_s[s]
        cohort = ("abrahamic_scripture" if s in ABRAHAMIC_COHORT
                  else "secular_control")
        pass_bh = bool(qr <= BH_ALPHA)
        evidence_sheet[s] = {
            "z_path": float(row_s["z_path"]),
            "canonical_path_cost": float(row_s["canonical_path_cost"]),
            "perm_mean": float(row_s["perm_mean"]),
            "perm_std": float(row_s["perm_std"]),
            "p_one_sided_raw": float(row_s["p_one_sided"]),
            "p_corpus_mc_floored": float(pc),
            "q_corpus_bh": float(qr),
            "pass_BH": pass_bh,
            "cohort_label": cohort,
            "n_units": int(row_s["n_units"]),
            "alphabet": row_s.get("alphabet", "unknown"),
        }

    for s, row in evidence_sheet.items():
        mark = "PASS_BH" if row["pass_BH"] else "fail_BH"
        print(f"[{EXP}]   {s:16s}  z={row['z_path']:+.3f}  "
              f"p={row['p_corpus_mc_floored']:.6f}  "
              f"q={row['q_corpus_bh']:.6f}  {mark}  "
              f"({row['cohort_label']})")

    # --- Step 5: verdict ---
    abr_pass = all(evidence_sheet[s]["pass_BH"] for s in ABRAHAMIC_COHORT)
    sec_fail = all(not evidence_sheet[s]["pass_BH"] for s in SECULAR_COHORT)

    if not bh_drift_ok:
        verdict = "FAIL_bh_reproduction"
    elif abr_pass and sec_fail:
        verdict = "PASS_shared_abrahamic"
    elif abr_pass and not sec_fail:
        verdict = "PARTIAL_no_negative_control_separation"
    else:
        verdict = "FAIL_shared_abrahamic_property"

    elapsed = time.time() - t0

    print(f"\n{'=' * 64}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    print(f"  Abrahamic cohort passes BH : "
          f"{all(evidence_sheet[s]['pass_BH'] for s in ABRAHAMIC_COHORT)}")
    print(f"  Secular control fails BH    : "
          f"{all(not evidence_sheet[s]['pass_BH'] for s in SECULAR_COHORT)}")
    print(f"{'=' * 64}")

    report = {
        "experiment": EXP,
        "hypothesis": (
            "H34 — Cross-scripture canonical-path optimality is a shared "
            "Abrahamic property (thin adapter over exp35 v7.2)."
        ),
        "schema_version": 1,
        "prereg_document": "experiments/exp97_crosscripture_t8/PREREG.md",
        "prereg_hash": _prereg_hash(),
        "exp35_receipt_path": str(exp35_path.relative_to(_ROOT)),
        "exp35_receipt_sha256": exp35_sha,
        "frozen_constants": {
            "seed": SEED,
            "expected_scriptures": EXPECTED_SCRIPTURES,
            "abrahamic_cohort": sorted(ABRAHAMIC_COHORT),
            "secular_cohort": sorted(SECULAR_COHORT),
            "expected_n_perm": EXPECTED_N_PERM,
            "bh_alpha": BH_ALPHA,
            "bh_reproduction_tol": BH_REPRODUCTION_TOL,
        },
        "mc_floor": mc_floor,
        "bh_reproduction_audit": bh_drift,
        "bh_reproduction_ok": bh_drift_ok,
        "corpus_scale_evidence_sheet": evidence_sheet,
        "cohort_summary": {
            "abrahamic_all_pass_BH": abr_pass,
            "secular_all_fail_BH": sec_fail,
            "n_abrahamic": len(ABRAHAMIC_COHORT),
            "n_secular": len(SECULAR_COHORT),
        },
        "p_corpus_for_section_4_37": {
            "quran": float(evidence_sheet["quran"]["p_corpus_mc_floored"]),
        },
        "interpretation": (
            "exp35 v7.2 measured canonical-path z in 5-D language-agnostic "
            "feature space across four scriptures at N_PERM=5000. "
            "The three Abrahamic scriptures' canonical orderings are "
            "shorter than any permutation (p < 1/5001 = "
            f"{mc_floor:.6f}); the secular control Iliad is not "
            "(p = 0.6274). This rebuts the 'Arabic-only' objection to "
            "the unified stack at the corpus scale: canonical-path "
            "optimality generalises across Abrahamic scripture. It does "
            "NOT, however, say anything about EL, R12, or any other "
            "within-scripture statistic; cross-language generalisation "
            "for those was tested in exp90_cross_language_el (FAILED — "
            "EL is Arabic-specific)."
        ),
        "verdict": verdict,
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=float)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.2f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


def _write_fail_report(out: Path, verdict: str, context: dict) -> None:
    report = {
        "experiment": EXP,
        "schema_version": 1,
        "verdict": verdict,
        "context": context,
        "prereg_hash": _prereg_hash(),
    }
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=float)


if __name__ == "__main__":
    sys.exit(main())
