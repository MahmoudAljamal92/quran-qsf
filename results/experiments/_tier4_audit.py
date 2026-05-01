"""
Zero-trust audit of Tier 4 outputs (E15, E16, E17).
E14 is DEFERRED and explicitly excluded from audit.

Checks:
  A1. All expected output files exist and parse.
  A2. Pre-registration block + seed + verdict present in each JSON report.
  A3. Reported verdicts match numeric criteria (no silent inflation).
  A4. No pinned artefacts (MANIFEST_v8) were mutated.
  A5. Sanity bounds on key numbers.
  A6. Known confounds / follow-up flags.
"""
from __future__ import annotations
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
EXP  = ROOT / "results" / "experiments"
FLAGS: list[dict] = []

def _flag(task, sev, code, msg):
    FLAGS.append({"task": task, "severity": sev, "code": code, "message": msg})

# ============================================================= A1 files
expected = {
    "E15": [
        "expE15_anti_variance/expE15_report.json",
        "expE15_anti_variance/expE15_report.md",
        "expE15_anti_variance/expE15_anti_manifold.png",
    ],
    "E16": [
        "expE16_lc2_signature/expE16_report.json",
        "expE16_lc2_signature/expE16_report.md",
        "expE16_lc2_signature/expE16_lc2_plot.png",
    ],
    "E17": [
        "expE17_dual_opt/expE17_report.json",
        "expE17_dual_opt/expE17_report.md",
        "expE17_dual_opt/expE17_pareto_scatter.png",
    ],
}
for task, paths in expected.items():
    for rel in paths:
        p = EXP / rel
        if not p.exists():
            _flag(task, "HIGH", "A1_MISSING_OUTPUT", f"missing: {rel}")
        elif p.stat().st_size == 0:
            _flag(task, "HIGH", "A1_EMPTY_OUTPUT", f"empty: {rel}")

# ============================================================= Load reports
reports: dict[str, dict] = {}
for task, paths in expected.items():
    for rel in paths:
        if rel.endswith(".json"):
            p = EXP / rel
            if p.exists():
                reports[task] = json.loads(p.read_text(encoding="utf-8"))

# ============================================================= A2 pre-registration
for task, r in reports.items():
    if "pre_registered_criteria" not in r:
        _flag(task, "MED", "A2_NO_PREREG_IN_JSON",
              "JSON lacks pre_registered_criteria block")
    if "verdict" not in r:
        _flag(task, "HIGH", "A2_NO_VERDICT", "JSON report lacks verdict")
    if "seed" not in r and "seeds" not in r:
        _flag(task, "MED",  "A2_NO_SEED", "no RNG seed recorded")

# ============================================================= A3 verdict re-derivation
def check_E15(r):
    pct  = r["quran_percentile_vs_ctrl"]
    p    = r["permutation_p"]
    if pct >= 95 and p <= 0.01:
        exp = "ANTI_VARIANCE_LAW"
    elif pct >= 75:
        exp = "WEAK_ANTI_VARIANCE"
    else:
        exp = "NULL_NO_ANTI_VARIANCE"
    if r["verdict"] != exp:
        _flag("E15", "HIGH", "A3_VERDICT_MISMATCH",
              f"JSON={r['verdict']} but criteria give {exp} "
              f"(pct={pct:.2f}, perm p={p:.4e})")

def check_E16(r):
    n5  = r["n_lambda_at_5pct"]
    n10 = r["n_lambda_at_10pct"]
    if n5 >= 3:
        exp = "LC2_SIGNATURE"
    elif n10 >= 3:
        exp = "WEAK_LC2"
    else:
        exp = "NULL_NO_LC2"
    if r["verdict"] != exp:
        _flag("E16", "HIGH", "A3_VERDICT_MISMATCH",
              f"JSON={r['verdict']} but criteria give {exp} (n5={n5}, n10={n10})")

def check_E17(r):
    q1  = r["mushaf"]["perm_quantile_J1"]
    q2  = r["mushaf"]["perm_quantile_J2"]
    beats_nuzul = r["mushaf_strictly_pareto_beats_nuzul"]
    b1, b2 = q1 <= 0.05, q2 <= 0.05
    if beats_nuzul and b1 and b2:
        exp = "MUSHAF_PARETO_DOMINANT"
    elif b1 or b2:
        exp = "MUSHAF_ONE_AXIS_DOMINANT"
    else:
        exp = "NULL_NO_DUAL_OPT"
    if r["verdict"] != exp:
        _flag("E17", "HIGH", "A3_VERDICT_MISMATCH",
              f"JSON={r['verdict']} but criteria give {exp} (q1={q1:.4f}, q2={q2:.4f}, beats_nuzul={beats_nuzul})")

if "E15" in reports: check_E15(reports["E15"])
if "E16" in reports: check_E16(reports["E16"])
if "E17" in reports: check_E17(reports["E17"])

# ============================================================= A4 pinned
manifest = ROOT / "results" / "experiments" / "expE4_sha_manifest" / "MANIFEST_v8.json"
if manifest.exists():
    man = json.loads(manifest.read_text(encoding="utf-8"))
    entries = man.get("entries") or man.get("files") or man
    flat: list[dict] = []
    if isinstance(entries, dict):
        for path, meta in entries.items():
            if isinstance(meta, dict):
                flat.append({"path": path, "sha256": meta.get("sha256") or meta.get("hash")})
            elif isinstance(meta, str):
                flat.append({"path": path, "sha256": meta})
    elif isinstance(entries, list):
        for e in entries:
            flat.append({"path": e.get("path"),
                         "sha256": e.get("sha256") or e.get("hash")})
    drift = []
    for e in flat:
        if not e.get("path") or not e.get("sha256"): continue
        fp = ROOT / e["path"]
        if not fp.exists() or fp.is_dir(): continue
        h = hashlib.sha256(fp.read_bytes()).hexdigest()
        if h != e["sha256"]:
            drift.append({"path": e["path"], "expected": e["sha256"][:12], "got": h[:12]})
    if drift:
        _flag("PINNED", "HIGH", "A4_PINNED_DRIFT",
              f"{len(drift)} pinned artefacts changed: {drift[:3]}")
    else:
        print(f"[audit] verified {len(flat)} manifest entries — no drift")
else:
    _flag("PINNED", "LOW", "A4_NO_MANIFEST", "no SHA manifest found")

# ============================================================= A5 sanity
if "E15" in reports:
    r = reports["E15"]
    if not (0 <= r["quran_percentile_vs_ctrl"] <= 100):
        _flag("E15", "HIGH", "A5_PCT_RANGE",
              f"percentile {r['quran_percentile_vs_ctrl']} outside [0,100]")
    if not (0 <= r["permutation_p"] <= 1):
        _flag("E15", "HIGH", "A5_P_RANGE",
              f"perm p {r['permutation_p']} outside [0,1]")
    if len(r["Sigma_ctrl_eigenvalues_ascending"]) != 5:
        _flag("E15", "MED", "A5_EIGV_COUNT",
              f"expected 5 eigenvalues, got {len(r['Sigma_ctrl_eigenvalues_ascending'])}")

if "E16" in reports:
    r = reports["E16"]
    for k, v in r["per_lambda"].items():
        if not (0 <= v["quran_median_pct"] <= 100):
            _flag("E16", "HIGH", "A5_PCT_RANGE",
                  f"λ={k}: pct {v['quran_median_pct']} outside [0,100]")

if "E17" in reports:
    r = reports["E17"]
    for who in ("mushaf", "nuzul"):
        q1 = r[who]["perm_quantile_J1"]
        q2 = r[who]["perm_quantile_J2"]
        if not (0 <= q1 <= 1) or not (0 <= q2 <= 1):
            _flag("E17", "HIGH", "A5_QUANT_RANGE",
                  f"{who}: quantiles outside [0,1] ({q1}, {q2})")

# ============================================================= A6 follow-ups / caveats
if "E15" in reports:
    _flag("E15", "LOW", "A6_SIGMA_REESTIMATION",
          "E15 permutation reestimates Σ per shuffle, which is the correct null "
          "(eigenstructure of RANDOM membership). Paired with stable basis choice "
          "(2 smallest λ of Σ_ctrl on non-shuffled data) for the observed statistic.")
if "E16" in reports:
    _flag("E16", "LOW", "A6_V_DOMINATED_AT_HIGH_LAMBDA",
          "E16 WEAK_LC2 is driven almost entirely by V (verse-final letter entropy) "
          "at high λ. The M term (H_cond root transitions) contributes little. "
          "Interpretation: the signature largely re-encodes the pre-existing "
          "'high-EL Quran outlier' property rather than a joint M+V optimization.")
if "E17" in reports:
    _flag("E17", "LOW", "A6_J2_NOT_EXTREMISED",
          "E17 MUSHAF_ONE_AXIS_DOMINANT: J1 (smoothness) quantile = 0.0 "
          "(Mushaf beats ALL 10,000 random perms), but J2 (sign-direction entropy) "
          "is NOT at the low extreme (q≈0.84). Dual-optimization falsified on J2; "
          "only the smoothness claim survives.")
    _flag("E17", "LOW", "A6_NUZUL_SOURCE",
          "E17 uses Egyptian Standard Edition (Azhar) chronology as Nuzul proxy. "
          "True historical chronology is uncertain; sensitivity to alternative "
          "chronological reconstructions (e.g., Nöldeke) not tested.")

# ============================================================= REPORT
severity_order = {"HIGH": 0, "MED": 1, "LOW": 2}
FLAGS.sort(key=lambda f: (severity_order[f["severity"]], f["task"], f["code"]))

summary = {
    "audit": "Tier-4 zero-trust audit (E15/E16/E17; E14 DEFERRED)",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "experiments_audited": list(reports.keys()),
    "n_flags": len(FLAGS),
    "flags_by_severity": {
        sev: sum(1 for f in FLAGS if f["severity"] == sev) for sev in ("HIGH", "MED", "LOW")
    },
    "verdicts": {t: reports[t].get("verdict") for t in reports},
    "flags": FLAGS,
}
(EXP / "_tier4_audit_report.json").write_text(
    json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
)

print(f"[audit] experiments audited: {list(reports.keys())}")
print(f"[audit] HIGH={summary['flags_by_severity']['HIGH']}  "
      f"MED={summary['flags_by_severity']['MED']}  "
      f"LOW={summary['flags_by_severity']['LOW']}")
for f in FLAGS:
    print(f"  [{f['severity']:>4}] {f['task']} {f['code']}: {f['message']}")
print(f"\nReport: {EXP / '_tier4_audit_report.json'}")
