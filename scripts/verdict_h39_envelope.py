"""Verdict applier for H39 (exp95f_short_envelope_replication).

Reads the SHORT-scope receipt of exp95e_full_114_consensus_universal and the
SHORT envelope table produced by `scripts/analyse_exp95e_envelope.py --scope
short`, then applies the verdict ladder defined in
`experiments/exp95f_short_envelope_replication/PREREG.md` §2.2.

Run from repo root:
    python scripts/verdict_h39_envelope.py

Writes:
    results/experiments/exp95f_short_envelope_replication/exp95f_short_envelope_replication.json
"""
from __future__ import annotations

import csv
import datetime as _dt
import hashlib
import json
import math
from pathlib import Path

# --- Paths --------------------------------------------------------------

_ROOT = Path(__file__).resolve().parent.parent
SHORT_RECEIPT = (
    _ROOT
    / "results/experiments/exp95e_full_114_consensus_universal/short/exp95e_full_114_consensus_universal.json"
)
SHORT_ENVELOPE = (
    _ROOT
    / "results/experiments/exp95e_full_114_consensus_universal/short/envelope_table.csv"
)
PREREG_DOC = _ROOT / "experiments/exp95f_short_envelope_replication/PREREG.md"
PREREG_HASH_FILE = _ROOT / "experiments/exp95f_short_envelope_replication/PREREG_HASH.txt"
OUT_DIR = _ROOT / "results/experiments/exp95f_short_envelope_replication"
OUT_PATH = OUT_DIR / "exp95f_short_envelope_replication.json"

# --- Locked thresholds from PREREG §2 -----------------------------------

# §2.1 phase boundary ranges (literal V1 extremes — NOT optimised on SHORT)
PHASE_LOWER_TOTAL_MAX = 188   # all surahs with total ≤ 188 must satisfy K=2 ≥ 0.90
PHASE_UPPER_TOTAL_MIN = 873   # all surahs with total ≥ 873 must satisfy K=2 ≤ 0.10
PHASE_LOWER_K2_MIN = 0.90
PHASE_UPPER_K2_MAX = 0.10

# §2.2 correlation thresholds
CORR_THRESHOLD_FAIL = -0.70   # ladder branch 4: r > -0.70 fails H39.1
CORR_THRESHOLD_FULL = -0.85   # ladder branch 7: r ≤ -0.85 promotes to PASS

# §6 audit hooks
TAU_DRIFT_TOL = 1e-12
EXPECTED_PREREG_HASH_PARENT = "ec14a1f6dcb81c3a54b0daeafa2b10f8707457ee4305de07d58ee7ede568e9a7"
Q100_K2_MIN = 0.99
Q100_GZIP_SOLO_MIN = 0.98
SHORT_VARIANT_MIN = 300_000
SHORT_VARIANT_MAX = 500_000


# --- Stat helpers --------------------------------------------------------

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
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    return pearson(ranks(xs), ranks(ys))


# --- Audit hooks (PREREG §6) --------------------------------------------

def check_audit_hooks(receipt: dict) -> dict:
    """Return audit-hook status. ok=True means all hooks pass; the H39 verdict
    is only applied when ok=True."""
    audit = receipt.get("audit_report", {})

    # 1. τ-drift sentinel (max abs drift ≤ 1e-12)
    tau = audit.get("tau_drift_sentinel", {})
    tau_ok = bool(tau.get("ok"))
    tau_max_drift = tau.get("max_drift")

    # 2. PREREG-hash sentinel (parent exp95e PREREG hash matches expected)
    fp = audit.get("prereg_fingerprint", {})
    fp_actual = fp.get("actual_hash")
    fp_ok = fp_actual == EXPECTED_PREREG_HASH_PARENT

    # 3. Embedded Q:100 regression: K=2 ≥ 0.99 AND gzip-solo ≥ 0.98
    q100 = audit.get("q100_regression", {})
    q100_k2_actual = q100.get("K2_recall_q100", {}).get("actual")
    q100_gzip_actual = q100.get("gzip_solo_recall_q100", {}).get("actual")
    q100_k2_ok = (q100_k2_actual is not None) and q100_k2_actual >= Q100_K2_MIN
    q100_gzip_ok = (q100_gzip_actual is not None) and q100_gzip_actual >= Q100_GZIP_SOLO_MIN

    # 4. Variant-count sanity: SHORT n_variants_total ∈ [300 K, 500 K]
    n_variants = receipt.get("n_variants_total")
    nv_ok = (
        n_variants is not None
        and SHORT_VARIANT_MIN <= int(n_variants) <= SHORT_VARIANT_MAX
    )

    overall_ok = tau_ok and fp_ok and q100_k2_ok and q100_gzip_ok and nv_ok

    return {
        "ok": overall_ok,
        "tau_drift_sentinel": {"ok": tau_ok, "max_drift": tau_max_drift, "tol": TAU_DRIFT_TOL},
        "prereg_hash_sentinel": {
            "ok": fp_ok,
            "actual": fp_actual,
            "expected": EXPECTED_PREREG_HASH_PARENT,
        },
        "q100_regression_h39": {
            "ok": q100_k2_ok and q100_gzip_ok,
            "K2_actual": q100_k2_actual,
            "K2_min": Q100_K2_MIN,
            "K2_ok": q100_k2_ok,
            "gzip_solo_actual": q100_gzip_actual,
            "gzip_solo_min": Q100_GZIP_SOLO_MIN,
            "gzip_solo_ok": q100_gzip_ok,
        },
        "variant_count_sanity": {
            "ok": nv_ok,
            "n_variants_total": n_variants,
            "min": SHORT_VARIANT_MIN,
            "max": SHORT_VARIANT_MAX,
        },
    }


# --- Verdict ladder (PREREG §2.2) ---------------------------------------

def apply_verdict_ladder(rows: list[dict], audit: dict, receipt_present: bool) -> dict:
    """Apply the §2.2 verdict ladder; first match wins."""

    # Branch 1: receipt missing or malformed
    if not receipt_present or not rows:
        return {"verdict": "FAIL_short_run_did_not_complete", "branch": 1}

    # Branch 2: τ drift
    tau = audit["tau_drift_sentinel"]
    if not tau["ok"]:
        return {"verdict": "FAIL_short_tau_drift", "branch": 2, "tau": tau}

    # Branch 3: Q:100 drift (H39-specific bar: K=2 ≥ 0.99, gzip-solo ≥ 0.98)
    q100 = audit["q100_regression_h39"]
    if not q100["ok"]:
        return {"verdict": "FAIL_q100_drift_short", "branch": 3, "q100": q100}

    # Compute correlations on H39's predictor (log10 total_letters → K=2 recall)
    log_total = [math.log10(int(r["n_total_letters"])) for r in rows]
    k2 = [float(r["recall_K2"]) for r in rows]
    r_pearson = pearson(log_total, k2)
    r_spearman = spearman(log_total, k2)

    # Phase-boundary check
    lower_violations: list[dict] = []
    upper_violations: list[dict] = []
    n_lower = 0
    n_upper = 0
    for r in rows:
        total = int(r["n_total_letters"])
        rk2 = float(r["recall_K2"])
        if total <= PHASE_LOWER_TOTAL_MAX:
            n_lower += 1
            if rk2 < PHASE_LOWER_K2_MIN:
                lower_violations.append({
                    "surah": r["surah"], "n_total_letters": total, "recall_K2": rk2,
                    "required_min": PHASE_LOWER_K2_MIN,
                })
        elif total >= PHASE_UPPER_TOTAL_MIN:
            n_upper += 1
            if rk2 > PHASE_UPPER_K2_MAX:
                upper_violations.append({
                    "surah": r["surah"], "n_total_letters": total, "recall_K2": rk2,
                    "required_max": PHASE_UPPER_K2_MAX,
                })

    # Branch 4: correlation too weak (H39.1 fails)
    h39_1_ok = (r_pearson <= CORR_THRESHOLD_FAIL)
    if not h39_1_ok:
        return {
            "verdict": "FAIL_envelope_correlation",
            "branch": 4,
            "pearson": r_pearson,
            "spearman": r_spearman,
            "threshold": CORR_THRESHOLD_FAIL,
        }

    # Branch 5: phase boundary fails (H39.2 fails)
    h39_2_ok = (not lower_violations) and (not upper_violations)
    if not h39_2_ok:
        return {
            "verdict": "FAIL_envelope_phase_boundary",
            "branch": 5,
            "n_lower_band": n_lower,
            "n_upper_band": n_upper,
            "lower_band_violations": lower_violations,
            "upper_band_violations": upper_violations,
            "pearson": r_pearson,
            "spearman": r_spearman,
        }

    # Branches 6 / 7: both H39.1 and H39.2 pass
    base = {
        "pearson": r_pearson,
        "spearman": r_spearman,
        "n_lower_band": n_lower,
        "n_upper_band": n_upper,
        "h39_1_ok": True,
        "h39_2_ok": True,
    }
    if r_pearson <= CORR_THRESHOLD_FULL:
        return {"verdict": "PASS_envelope_replicates", "branch": 7, **base}
    return {"verdict": "PARTIAL_envelope_replicates", "branch": 6, **base}


# --- Main ---------------------------------------------------------------

def _sha256(p: Path) -> str | None:
    if not p.exists():
        return None
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load PREREG hash for receipt provenance.
    prereg_hash_h39 = (
        PREREG_HASH_FILE.read_text(encoding="utf-8").strip()
        if PREREG_HASH_FILE.exists() else None
    )

    receipt_present = SHORT_RECEIPT.exists() and SHORT_ENVELOPE.exists()
    if not receipt_present:
        print(f"[verdict_h39] missing receipt(s): {SHORT_RECEIPT.exists()=}, {SHORT_ENVELOPE.exists()=}")

    receipt: dict = {}
    rows: list[dict] = []
    if receipt_present:
        receipt = json.loads(SHORT_RECEIPT.read_text(encoding="utf-8"))
        with SHORT_ENVELOPE.open("r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

    audit = check_audit_hooks(receipt) if receipt else {
        "ok": False,
        "tau_drift_sentinel": {"ok": False},
        "prereg_hash_sentinel": {"ok": False},
        "q100_regression_h39": {"ok": False},
        "variant_count_sanity": {"ok": False},
    }

    verdict_block = apply_verdict_ladder(rows, audit, receipt_present)

    out = {
        "experiment": "exp95f_short_envelope_replication",
        "schema_version": 1,
        "hypothesis_id": "H39",
        "prereg_document": str(PREREG_DOC.relative_to(_ROOT)).replace("\\", "/"),
        "prereg_hash": prereg_hash_h39,
        "parent_receipt": {
            "path": str(SHORT_RECEIPT.relative_to(_ROOT)).replace("\\", "/"),
            "sha256": _sha256(SHORT_RECEIPT),
        },
        "envelope_csv": {
            "path": str(SHORT_ENVELOPE.relative_to(_ROOT)).replace("\\", "/"),
            "sha256": _sha256(SHORT_ENVELOPE),
        },
        "frozen_thresholds": {
            "phase_lower_total_max": PHASE_LOWER_TOTAL_MAX,
            "phase_upper_total_min": PHASE_UPPER_TOTAL_MIN,
            "phase_lower_k2_min": PHASE_LOWER_K2_MIN,
            "phase_upper_k2_max": PHASE_UPPER_K2_MAX,
            "corr_threshold_fail": CORR_THRESHOLD_FAIL,
            "corr_threshold_full": CORR_THRESHOLD_FULL,
        },
        "audit_report": audit,
        "verdict_block": verdict_block,
        "verdict": verdict_block["verdict"],
        "f55_promotion": verdict_block["verdict"] in {
            "PASS_envelope_replicates",
            "PARTIAL_envelope_replicates",
        },
        "completed_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }

    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    # Console summary
    print(f"# H39 verdict applier -- receipt at {OUT_PATH}")
    print(f"# Verdict       : {verdict_block['verdict']}")
    print(f"# Branch        : {verdict_block.get('branch')}")
    if "pearson" in verdict_block:
        print(f"# Pearson r     : {verdict_block['pearson']:+.4f}  (PASS <= {CORR_THRESHOLD_FULL})")
        print(f"# Spearman rho  : {verdict_block.get('spearman', float('nan')):+.4f}")
    if "n_lower_band" in verdict_block:
        print(f"# Surahs <= {PHASE_LOWER_TOTAL_MAX} letters : {verdict_block['n_lower_band']}  (must all have K=2 >= {PHASE_LOWER_K2_MIN})")
        print(f"# Surahs >= {PHASE_UPPER_TOTAL_MIN} letters : {verdict_block['n_upper_band']}  (must all have K=2 <= {PHASE_UPPER_K2_MAX})")
    print(f"# Audit hooks   : {audit['ok']}")
    print(f"# F55 promotion : {out['f55_promotion']}")


if __name__ == "__main__":
    main()
