"""
Zero-trust audit of Tier 3 outputs (E10–E13).

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
    "E10": [
        "expE10_composite_detector/expE10_report.json",
        "expE10_composite_detector/expE10_report.md",
        "expE10_composite_detector/expE10_detector_plots.png",
    ],
    "E11": [
        "expE11_local_window/expE11_report.json",
        "expE11_local_window/expE11_report.md",
        "expE11_local_window/expE11_auc_vs_N.png",
    ],
    "E12": [
        "expE12_bayesian_fusion/expE12_report.json",
        "expE12_bayesian_fusion/expE12_report.md",
        "expE12_bayesian_fusion/expE12_calibration_plots.png",
    ],
    "E13": [
        "expE13_auth_gate/expE13_report.json",
        "expE13_auth_gate/expE13_report.md",
        "expE13_auth_gate/expE13_gate_histogram.png",
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
reports = {}
for task, paths in expected.items():
    for rel in paths:
        if rel.endswith(".json"):
            p = EXP / rel
            if p.exists():
                reports[task] = json.loads(p.read_text(encoding="utf-8"))

# ============================================================= A2
for task, r in reports.items():
    if "pre_registered_criteria" not in r:
        _flag(task, "MED", "A2_NO_PREREG_IN_JSON",
              "JSON lacks pre_registered_criteria block")
    if "verdict" not in r:
        _flag(task, "HIGH", "A2_NO_VERDICT", "JSON report lacks verdict")
    if "seed" not in r and "seeds" not in r:
        _flag(task, "MED",  "A2_NO_SEED", "no RNG seed recorded")

# ============================================================= A3 verdict re-derivation
def check_E10(r):
    any_gain = False
    for Nkey, s in r["sweep_per_N"].items():
        if s.get("composite_gain"):
            any_gain = True; break
    exp = "COMPOSITE_GAIN" if any_gain else "NULL_NO_GAIN"
    if r["verdict"] != exp:
        _flag("E10", "HIGH", "A3_VERDICT_MISMATCH",
              f"JSON={r['verdict']} but criteria give {exp}")

def check_E11(r):
    baseline_N = r["baseline_N"]
    baseline_auc = r["auc_baseline_large_N"]
    best_auc = r["best_AUC"]
    delta = best_auc - baseline_auc
    if delta >= 0.10:
        exp = "LOCAL_AMPLIFICATION"
    elif delta >= 0.03:
        exp = "MODEST_AMPLIFICATION"
    else:
        exp = "NULL_NO_AMPLIFICATION"
    if r["verdict"] != exp:
        _flag("E11", "HIGH", "A3_VERDICT_MISMATCH",
              f"JSON={r['verdict']} but criteria give {exp} (delta={delta:.4f})")

def check_E12(r):
    m = r["models"]
    brier_vote = m["L2_logistic_baseline"]["brier_mean"]
    briers_bayes = [v["brier_mean"] for k, v in m.items() if k != "L2_logistic_baseline"]
    if not briers_bayes:
        return
    best_brier_bayes = min(briers_bayes)
    delta_brier = brier_vote - best_brier_bayes
    eces_bayes = [v["ece"] for k, v in m.items() if k != "L2_logistic_baseline"]
    best_ece = min(eces_bayes)
    exp = ("BAYES_CALIBRATED" if (delta_brier >= 0.01 and best_ece <= 0.10)
           else "NULL_NO_CALIBRATION_GAIN")
    if r["verdict"] != exp:
        _flag("E12", "HIGH", "A3_VERDICT_MISMATCH",
              f"JSON={r['verdict']} but criteria give {exp} (Δbrier={delta_brier:.4f}, ECE={best_ece:.4f})")

def check_E13(r):
    ranks = r["canon_rank_per_seed"]
    all_one = all(x == 1 for x in ranks)
    all_top10 = all(x <= 10 for x in ranks)
    p_mean = r["empirical_p_mean"]
    if all_one and p_mean <= 0.01:
        exp = "GATE_SOLID"
    elif all_top10:
        exp = "GATE_USEFUL"
    else:
        exp = "NULL_GATE_FAILS"
    if r["verdict"] != exp:
        _flag("E13", "HIGH", "A3_VERDICT_MISMATCH",
              f"JSON={r['verdict']} but criteria give {exp}")

if "E10" in reports: check_E10(reports["E10"])
if "E11" in reports: check_E11(reports["E11"])
if "E12" in reports: check_E12(reports["E12"])
if "E13" in reports: check_E13(reports["E13"])

# ============================================================= A4 pinned
manifest = ROOT / "results" / "experiments" / "expE4_sha_manifest" / "MANIFEST_v8.json"
if manifest.exists():
    man = json.loads(manifest.read_text(encoding="utf-8"))
    entries = man.get("entries") or man.get("files") or man
    flat = []
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
if "E11" in reports:
    r = reports["E11"]
    for Nkey, s in r["results_per_window"].items():
        auc = s["auc_mean"]
        if not (0.0 <= auc <= 1.0):
            _flag("E11", "HIGH", "A5_AUC_RANGE",
                  f"E11 {Nkey} AUC {auc} outside [0, 1]")
    if r["n_variants"] != 864:
        _flag("E11", "MED", "A5_N_VARIANTS",
              f"n_variants = {r['n_variants']} != 864 expected")

if "E12" in reports:
    r = reports["E12"]
    if r["residual_corr_max_abs"] > 1.0 or r["residual_corr_max_abs"] < 0:
        _flag("E12", "HIGH", "A5_CORR_RANGE",
              f"residual_corr_max_abs {r['residual_corr_max_abs']} out of [0,1]")
    for mname, m in r["models"].items():
        if not (0 <= m["ece"] <= 1):
            _flag("E12", "HIGH", "A5_ECE_RANGE",
                  f"ECE for {mname} = {m['ece']} outside [0, 1]")

if "E13" in reports:
    r = reports["E13"]
    ranks = r["canon_rank_per_seed"]
    if any(x < 1 or x > 865 for x in ranks):
        _flag("E13", "HIGH", "A5_RANK_RANGE",
              f"canonical rank outside [1, 865]: {ranks}")

# ============================================================= A6 follow-ups
if "E11" in reports:
    _flag("E11", "LOW", "A6_DESIGN_TRIVIALITY",
          "E11 LOCAL_AMPLIFICATION verdict is guaranteed-by-design: "
          "as N→whole surah, signal and null windows overlap → AUC→0.5. "
          "Headline = 'edits detectable at small N via simple NCD/L1 channels at AUC=1.0'.")
if "E10" in reports:
    _flag("E10", "LOW", "A6_CHANNEL_SATURATION",
          "E10 NULL_NO_GAIN because single channels saturate to AUC=1.0 at all "
          "non-degenerate N on the Adiyat single-letter enumeration. Harder "
          "(multi-letter, noisier) problems may yet show composite gain — not tested here.")
if "E12" in reports:
    _flag("E12", "LOW", "A6_PERFECT_BAYES_SEPARATION",
          "KDE-NB achieves Brier=0 and ECE=0 because the training data is "
          "perfectly class-separable. Posteriors saturate to 0/1. Realistic noisy "
          "tasks will give softer probabilities and more informative calibration.")
if "E13" in reports:
    _flag("E13", "LOW", "A6_GATE_ON_KNOWN_EDITS",
          "GATE_SOLID is evaluated on the 864 single-letter edits the gate was "
          "explicitly trained on. Real-world deployment requires testing on OUT-OF-"
          "DISTRIBUTION edits (multi-letter, insertion/deletion, cross-surah). "
          "Queued as follow-up.")

# ============================================================= REPORT
severity_order = {"HIGH": 0, "MED": 1, "LOW": 2}
FLAGS.sort(key=lambda f: (severity_order[f["severity"]], f["task"], f["code"]))

summary = {
    "audit": "Tier-3 zero-trust audit",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "experiments_audited": list(reports.keys()),
    "n_flags": len(FLAGS),
    "flags_by_severity": {
        sev: sum(1 for f in FLAGS if f["severity"] == sev) for sev in ("HIGH", "MED", "LOW")
    },
    "verdicts": {t: reports[t].get("verdict") for t in reports},
    "flags": FLAGS,
}
(EXP / "_tier3_audit_report.json").write_text(
    json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
)

print(f"[audit] experiments audited: {list(reports.keys())}")
print(f"[audit] HIGH={summary['flags_by_severity']['HIGH']}  "
      f"MED={summary['flags_by_severity']['MED']}  "
      f"LOW={summary['flags_by_severity']['LOW']}")
for f in FLAGS:
    print(f"  [{f['severity']:>4}] {f['task']} {f['code']}: {f['message']}")
print(f"\nReport: {EXP / '_tier3_audit_report.json'}")
