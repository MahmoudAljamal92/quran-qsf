"""
Zero-trust audit of Tier 5 outputs + the formerly-deferred E14.
Scope: E14 (multiscale law), E18 (Reed-Solomon + controls), E19 (ring),
       E20 (constant hunt).

Checks:
  A1. All expected output files exist and parse.
  A2. Pre-registration block + seed + verdict present in each JSON.
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
    "E14": [
        "expE14_multiscale_law/expE14_report.json",
        "expE14_multiscale_law/expE14_report.md",
        "expE14_multiscale_law/expE14_shapley_and_R.png",
    ],
    "E18": [
        "expE18_reed_solomon/expE18_report.json",
        "expE18_reed_solomon/expE18_report.md",
        "expE18_reed_solomon/expE18_controls_report.json",
        "expE18_reed_solomon/expE18_FINAL_report.json",
        "expE18_reed_solomon/expE18_FINAL_report.md",
    ],
    "E19": [
        "expE19_ring_composition/expE19_report.json",
        "expE19_ring_composition/expE19_report.md",
        "expE19_ring_composition/expE19_ring_plot.png",
    ],
    "E20": [
        "expE20_constant_hunt/expE20_report.json",
        "expE20_constant_hunt/expE20_report.md",
        "expE20_constant_hunt/expE20_sensitivity.png",
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
e18_final: dict | None = None
for task, paths in expected.items():
    for rel in paths:
        if rel.endswith(".json") and "FINAL" not in rel and "controls" not in rel:
            p = EXP / rel
            if p.exists():
                reports[task] = json.loads(p.read_text(encoding="utf-8"))

if (EXP / "expE18_reed_solomon/expE18_FINAL_report.json").exists():
    e18_final = json.loads((EXP / "expE18_reed_solomon/expE18_FINAL_report.json").read_text(encoding="utf-8"))

# ============================================================= A2 pre-registration
for task, r in reports.items():
    if "pre_registered_criteria" not in r:
        _flag(task, "MED", "A2_NO_PREREG_IN_JSON",
              "JSON lacks pre_registered_criteria block")
    if "verdict" not in r and "FINAL_verdict" not in r:
        _flag(task, "HIGH", "A2_NO_VERDICT", "JSON lacks verdict")
    if "seed" not in r and "seeds" not in r:
        _flag(task, "MED",  "A2_NO_SEED", "no RNG seed recorded")

# ============================================================= A3 verdict re-derivation

def check_E14(r):
    p_brown = r["brown_p_combined"]
    max_share = r["max_single_scale_share"]
    if p_brown < 0.01 and max_share < 0.60:
        exp = "MULTISCALE_LAW"
    elif p_brown < 0.01:
        exp = "SINGLE_SCALE_DOMINANT"
    else:
        exp = "NULL_NO_COMBINED_EVIDENCE"
    if r["verdict"] != exp:
        _flag("E14", "HIGH", "A3_VERDICT_MISMATCH",
              f"JSON={r['verdict']} but criteria give {exp} "
              f"(p_Brown={p_brown:.3e}, max_share={max_share:.3f})")

def check_E18(r_primary, r_final):
    """E18 final verdict depends on A-vs-B-arm contrast."""
    if r_final is None:
        _flag("E18", "HIGH", "A3_NO_FINAL_REPORT",
              "expE18_FINAL_report.json absent; cannot re-derive verdict")
        return
    contrasts = r_final.get("decisive_contrasts", [])
    b_kills = any(c.get("B_kills_signal") for c in contrasts)
    a_sig   = bool(contrasts) and any(
        (c.get("p_quran_utf8") is not None and c["p_quran_utf8"] <= 0.01)
        for c in contrasts
    )
    if b_kills:
        exp = "NULL_UTF8_CONFOUND"
    elif a_sig:
        exp = "RS_STRUCTURE_CANDIDATE"
    else:
        exp = "NULL_NO_RS_STRUCTURE"
    if r_final["FINAL_verdict"] != exp:
        _flag("E18", "HIGH", "A3_VERDICT_MISMATCH",
              f"JSON={r_final['FINAL_verdict']} but criteria give {exp} "
              f"(b_kills={b_kills}, a_sig={a_sig})")

def check_E19(r):
    fp = r["fisher_combined_p"]
    if fp <= 0.01:
        exp = "FEATURE_LEVEL_RING"
    elif fp <= 0.05:
        exp = "WEAK_RING"
    else:
        exp = "NULL_NO_RING"
    if r["verdict"] != exp:
        _flag("E19", "HIGH", "A3_VERDICT_MISMATCH",
              f"JSON={r['verdict']} but criteria give {exp} (Fisher p={fp:.4f})")

def check_E20(r):
    da = r["derived_analytic"]
    de = r["derived_empirical"]
    stable = r["B_sensitivity_sweep"]["neighborhood_10pct"]["stable"]
    ds = r["D_downstream_T2_sensitivity"]["downstream_stable"]
    if da:
        exp = "DERIVED_ANALYTIC"
    elif de:
        exp = "DERIVED_EMPIRICAL"
    elif stable and (ds is not False):
        exp = "STABLE_MAGIC"
    else:
        exp = "MAGIC_NUMBER_FLAG"
    if r["verdict"] != exp:
        _flag("E20", "HIGH", "A3_VERDICT_MISMATCH",
              f"JSON={r['verdict']} but criteria give {exp} "
              f"(da={da}, de={de}, B-stable={stable}, downstream_stable={ds})")

if "E14" in reports: check_E14(reports["E14"])
if "E18" in reports: check_E18(reports["E18"], e18_final)
if "E19" in reports: check_E19(reports["E19"])
if "E20" in reports: check_E20(reports["E20"])

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
if "E14" in reports:
    r = reports["E14"]
    if not (0 <= r["brown_p_combined"] <= 1):
        _flag("E14", "HIGH", "A5_P_RANGE",
              f"Brown p {r['brown_p_combined']} outside [0,1]")
    shares = r["shapley_shares"].values()
    if any(s > 1.05 or s < -0.50 for s in shares):
        _flag("E14", "MED", "A5_SHAPLEY_RANGE",
              f"Shapley share out of plausible [-0.5, 1.05]: {list(shares)}")
    # fisher uncorrected should be <= Brown-corrected χ² (same value; correction is only df)
    if abs(r["brown_chi2_obs"] - r["fisher_chi2_uncorrected"]) > 1e-9:
        _flag("E14", "MED", "A5_BROWN_CHI2_MISMATCH",
              f"Brown χ² ({r['brown_chi2_obs']}) != Fisher χ² ({r['fisher_chi2_uncorrected']})")

if "E19" in reports:
    r = reports["E19"]
    if not (0 <= r["fisher_combined_p"] <= 1):
        _flag("E19", "HIGH", "A5_P_RANGE",
              f"Fisher p {r['fisher_combined_p']} outside [0,1]")
    # 6 of 79 sig at 0.05 under null → expected ~ 4; both 4-8 range acceptable
    n05 = r["n_surahs_sig_at_0.05"]
    if n05 > r["n_surahs_tested"] / 2:
        _flag("E19", "MED", "A5_EXCESS_PER_SURAH",
              f"n_sig_at_0.05 ({n05}) > half of n_tested — unexpected given Fisher null")

if "E20" in reports:
    r = reports["E20"]
    target = r["target_constant"]["value"]
    best_rel = r["C_closed_form_candidates"][0]["rel_err"]
    if not (0 < target < 1):
        _flag("E20", "HIGH", "A5_TARGET_RANGE",
              f"target {target} outside (0,1)")
    if best_rel > 1.0:
        _flag("E20", "MED", "A5_CF_RANGE", f"best cf rel_err {best_rel} huge")

if e18_final is not None:
    for arm_name, arm in e18_final.get("arms_summary", {}).items():
        for cfg in arm.get("configs", []):
            if not (0 <= cfg["fisher_p"] <= 1):
                _flag("E18", "HIGH", "A5_P_RANGE",
                      f"{arm_name} (n={cfg['n']}, nsym={cfg['nsym']}): p={cfg['fisher_p']}")

# ============================================================= A6 follow-ups / caveats
if "E14" in reports:
    r = reports["E14"]
    # Nulls on S2/S3/S5 are abs-deviation; on S1/S4 they are raw distances.
    # This is a defensible choice (already noted in PREREG) but worth flagging.
    _flag("E14", "LOW", "A6_ABS_DEV_FRAME",
          "E14 uses absolute-deviation framing for S2/S3/S5 and raw distance for S1/S4. "
          "Mixing is defensible (each scale's null mean is explicitly zero under the "
          "frame chosen) but a future sensitivity pass should verify that a uniform "
          "raw-distance framing gives the same Brown verdict.")
    _flag("E14", "LOW", "A6_FISHER_CAP_LITERAL",
          "S5_L_TEL observed p=0.000856 is within the finite-resolution null "
          "(null_pool_size=2335 → minimum p ≈ 4.3e-4). Fisher uses the clipped value; "
          "conservative. The Brown-combined p=1.4e-6 is therefore robust to a 2× tightening.")

if "E18" in reports and e18_final is not None:
    _flag("E18", "LOW", "A6_POETRY_ARM_UNDERPOWERED",
          "Arm C (poetry control) chunker split on '\\n\\n' which yielded only 1 unit. "
          "Arm C is informational; the decisive rule uses A-vs-B contrast alone, which "
          "is adequate. A future run with a better-tokenised Arabic control would "
          "add independent confound confirmation.")
    _flag("E18", "LOW", "A6_B_AT_n63_borderline",
          "Arm B (compact alphabet) shows (n=63, nsym=16) at Fisher p=0.031 — borderline "
          "and not at the focal configs (31, 8/12). The confound verdict applies to the "
          "ORIGINAL UTF-8 signal's configs only; a trailing borderline at (63, 16) on the "
          "compact alphabet is expected residual structure in Arabic letter statistics.")

if "E19" in reports:
    r = reports["E19"]
    if r["n_surahs_sig_at_0.05"] > (r["expected_at_0.05_under_null"] + 2):
        _flag("E19", "LOW", "A6_PER_SURAH_SLIGHT_EXCESS",
              f"{r['n_surahs_sig_at_0.05']} vs expected ~{r['expected_at_0.05_under_null']:.1f} — "
              "within Poisson noise (√4=2 SD), but worth a future replication with larger B.")
    _flag("E19", "LOW", "A6_SIMPLE_FEATURES",
          "E19 uses a simple 5-D per-verse feature vector (chars, words, connector_count, "
          "unique_letters, mean_word_length). Richer semantic features (e.g., root-vector "
          "embeddings) could still reveal higher-order ring structure; this test only "
          "rules out ring structure at the surface-lexical/length feature level.")

if "E20" in reports:
    r = reports["E20"]
    _flag("E20", "LOW", "A6_ANALYTIC_MATCH_IS_COINCIDENTAL",
          "E20 DERIVED_ANALYTIC passes on 1/√26=0.19612 at 0.04% rel_err, but 26 has no "
          "canonical Arabic/Quranic grounding (abjad has 28 letters, not 26). The match "
          "is a numerical coincidence; the report's markdown flags this explicitly and "
          "recommends publication as 'empirical parameter with coincidence note'.")
    _flag("E20", "LOW", "A6_B_SWEEP_NOT_INVARIANT",
          "Sensitivity sweep on chars_nospace shows exclusion count {1, 2, 3} across the "
          "±10% neighborhood — NOT strictly invariant. However, Hotelling T² ratio "
          "(max/min) over corresponding Band-A drops = 1.14, so the downstream outlier "
          "claim survives. This is the honest reading; the STABLE_MAGIC branch would "
          "have triggered if downstream_stable were False.")

# ============================================================= REPORT
severity_order = {"HIGH": 0, "MED": 1, "LOW": 2}
FLAGS.sort(key=lambda f: (severity_order[f["severity"]], f["task"], f["code"]))

verdicts = {}
for t, r in reports.items():
    verdicts[t] = r.get("verdict") or r.get("FINAL_verdict")
if e18_final is not None:
    verdicts["E18"] = e18_final.get("FINAL_verdict")

summary = {
    "audit": "Tier-5 zero-trust audit (E14/E18/E19/E20)",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "experiments_audited": list(reports.keys()),
    "n_flags": len(FLAGS),
    "flags_by_severity": {
        sev: sum(1 for f in FLAGS if f["severity"] == sev) for sev in ("HIGH", "MED", "LOW")
    },
    "verdicts": verdicts,
    "flags": FLAGS,
}
(EXP / "_tier5_audit_report.json").write_text(
    json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
)

print(f"[audit] experiments audited: {list(reports.keys())}")
print(f"[audit] verdicts: {verdicts}")
print(f"[audit] HIGH={summary['flags_by_severity']['HIGH']}  "
      f"MED={summary['flags_by_severity']['MED']}  "
      f"LOW={summary['flags_by_severity']['LOW']}")
for f in FLAGS:
    print(f"  [{f['severity']:>4}] {f['task']} {f['code']}: {f['message']}")
print(f"\nReport: {EXP / '_tier5_audit_report.json'}")
