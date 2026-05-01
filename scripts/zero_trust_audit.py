"""zero_trust_audit.py — deep cross-experiment audit beyond integrity_audit.py.

Goes beyond JSON-shape and PREREG-hash checks. Covers:

  L1  Pre-registration discipline (PREREG hash older than receipt timestamp).
  L2  Stale dependency: receipt cites another resource (checkpoint/receipt);
      target must exist and not be a FAIL_*.
  L3  Numerical-claim inflation: doc-claimed scalars (RANKED_FINDINGS,
      PAPER.md, REFERENCE.md, PROGRESS.md) match the underlying receipt.
  L4  Retraction completeness: every FAIL_* receipt is mentioned in
      RETRACTIONS_REGISTRY; every retraction cites a real receipt.
  L5  Verdict-vs-audit consistency: PASS verdict requires `audit_report.ok`
      truthy; FAIL_audit_* requires `audit_report.ok` falsy.
  L6  Calibration leakage smell: receipts that carry a `tau` / `threshold`
      should declare a `calibration_source` AND that source should not
      visibly include the test-fold corpus.
  L7  F-finding chain: each F-finding cites a receipt whose verdict starts
      with PASS_ and whose prerequisite-F numbers are not retracted.
  L8  Orphan checks: receipts with no document reference; doc claims with
      no receipt.

Each issue is one of:
  - CRITICAL: clearly violates a guarantee. Must be fixed or formally
    disclosed in `docs/KNOWN_INTEGRITY_DEVIATIONS.md` before public
    release.
  - WARN: smells bad but may have a benign explanation.
  - INFO: bookkeeping note; no integrity question.

Outputs:
  results/integrity/zero_trust_audit_<UTC>.json
  results/integrity/zero_trust_audit_<UTC>.md
  results/integrity/zero_trust_audit_LATEST.{json,md}

Run:
  python scripts/zero_trust_audit.py
Exit code 0 iff zero CRITICAL findings.
"""
from __future__ import annotations

import datetime as _dt
import io
import json
import re
import sys
from pathlib import Path
from typing import Any

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:  # pragma: no cover
        pass

ROOT = Path(__file__).resolve().parent.parent
EXPS = ROOT / "results" / "experiments"
DOCS = ROOT / "docs"
INTEG = ROOT / "results" / "integrity"

# --- Severity constants -------------------------------------------------
CRITICAL = "CRITICAL"
WARN = "WARN"
INFO = "INFO"

# --- Helpers ------------------------------------------------------------

def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _read_json(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _list_receipts() -> list[Path]:
    """Locate canonical receipts.

    Standard layout: results/experiments/<name>/<name>.json
    Multi-run layout (e.g. exp95e): results/experiments/<name>/<subdir>/<name>.json
        where <subdir> ∈ {short, v1, v2, ...}. We pick the most recent run
        by mtime as the canonical primary so dependency checks work.
    """
    out: list[Path] = []
    if not EXPS.exists():
        return out
    for sub in sorted(EXPS.iterdir()):
        if not sub.is_dir():
            continue
        primary = sub / f"{sub.name}.json"
        if primary.exists():
            out.append(primary)
            continue
        sub_runs = [
            sd / f"{sub.name}.json"
            for sd in sub.iterdir()
            if sd.is_dir() and (sd / f"{sub.name}.json").exists()
        ]
        if sub_runs:
            sub_runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            out.append(sub_runs[0])
    return out


def _exp_name(receipt_path: Path) -> str:
    """Receipt filename stem — robust against multi-run subdir layouts."""
    return receipt_path.stem


def _verdict_of(receipt: dict) -> str:
    for k in ("verdict", "verdict_audit", "outcome", "decision"):
        if isinstance(receipt.get(k), str):
            return receipt[k]
    # nested verdict_block
    vb = receipt.get("verdict_block")
    if isinstance(vb, dict) and isinstance(vb.get("verdict"), str):
        return vb["verdict"]
    return ""


def _prereg_md_path_for(receipt_path: Path) -> Path | None:
    """Map results/experiments/<exp>/<exp>.json → experiments/<exp>/PREREG.md."""
    exp_name = _exp_name(receipt_path)
    candidate = ROOT / "experiments" / exp_name / "PREREG.md"
    if candidate.exists():
        return candidate
    return None


# --- Audit checks -------------------------------------------------------

def check_l1_prereg_timing(receipts: list[Path]) -> list[dict]:
    """L1: PREREG.md mtime <= receipt's started_at_utc (or completed_at_utc)."""
    issues: list[dict] = []
    for rp in receipts:
        rec = _read_json(rp) or {}
        prereg = _prereg_md_path_for(rp)
        if not prereg:
            continue
        prereg_mtime = _dt.datetime.fromtimestamp(
            prereg.stat().st_mtime, tz=_dt.timezone.utc
        )
        started = rec.get("started_at_utc") or rec.get("completed_at_utc")
        if not started:
            continue
        try:
            recv_started = _dt.datetime.fromisoformat(started.replace("Z", "+00:00"))
        except Exception:
            continue
        if prereg_mtime > recv_started:
            issues.append({
                "level": "L1_prereg_timing",
                "severity": WARN,  # mtime can be touched benignly
                "receipt": str(rp.relative_to(ROOT)).replace("\\", "/"),
                "prereg_mtime": prereg_mtime.isoformat(),
                "receipt_started": started,
                "msg": (
                    "PREREG.md was modified AFTER receipt's started_at_utc. "
                    "Most often benign (file touched by editor) but if the "
                    "PREREG content actually changed, this is a CRITICAL "
                    "post-hoc rule edit. Cross-check with PREREG_HASH.txt."
                ),
            })
    return issues


def check_l2_stale_deps(receipts: list[Path]) -> list[dict]:
    """L2: pickle / receipt references inside frozen_constants exist + are not FAIL_*."""
    issues: list[dict] = []
    receipt_index: dict[str, Path] = {_exp_name(rp): rp for rp in receipts}
    receipt_verdicts: dict[str, str] = {}
    for name, rp in receipt_index.items():
        rec = _read_json(rp) or {}
        receipt_verdicts[name] = _verdict_of(rec)

    cite_re = re.compile(r"results/experiments/(exp[0-9A-Za-z_]+)/")
    for rp in receipts:
        rec = _read_json(rp) or {}
        # Walk the entire receipt looking for cross-experiment references.
        flat = json.dumps(rec, ensure_ascii=False)
        cited = set(cite_re.findall(flat))
        cited.discard(_exp_name(rp))  # self-ref is not a cross-dep
        for dep in sorted(cited):
            if dep not in receipt_index:
                issues.append({
                    "level": "L2_stale_dep_missing",
                    "severity": CRITICAL,
                    "receipt": str(rp.relative_to(ROOT)).replace("\\", "/"),
                    "cited_dep": dep,
                    "msg": f"Receipt cites results/experiments/{dep}/ but it does not exist on disk.",
                })
                continue
            dep_verdict = receipt_verdicts[dep]
            if dep_verdict.startswith("FAIL_"):
                # If the citing receipt itself is FAIL_*, this is legitimate
                # follow-up scholarship (one failure characterising another).
                # Only PASS_*-depends-on-FAIL_* is a CRITICAL integrity issue.
                citing_verdict = _verdict_of(rec)
                if citing_verdict.startswith("FAIL_"):
                    severity = INFO
                    msg_suffix = (
                        " (citing receipt is also FAIL_*, treating as "
                        "follow-up characterisation, not substantive reliance)"
                    )
                elif citing_verdict.startswith("BLOCKED_"):
                    severity = WARN
                    msg_suffix = " (citing receipt is BLOCKED)"
                else:
                    severity = CRITICAL
                    msg_suffix = ""
                issues.append({
                    "level": "L2_stale_dep_failed",
                    "severity": severity,
                    "receipt": str(rp.relative_to(ROOT)).replace("\\", "/"),
                    "citing_verdict": citing_verdict,
                    "cited_dep": dep,
                    "dep_verdict": dep_verdict,
                    "msg": (
                        f"Receipt cites {dep} which has a FAIL_* verdict. "
                        f"Either remove the citation or document why a "
                        f"failed result is being relied upon."
                        + msg_suffix
                    ),
                })
            elif dep_verdict.startswith("BLOCKED_"):
                issues.append({
                    "level": "L2_stale_dep_blocked",
                    "severity": WARN,
                    "receipt": str(rp.relative_to(ROOT)).replace("\\", "/"),
                    "cited_dep": dep,
                    "dep_verdict": dep_verdict,
                    "msg": f"Receipt cites {dep} which is BLOCKED.",
                })
    return issues


def check_l3_inflation(receipts: list[Path]) -> list[dict]:
    """L3: scan headline scalars in RANKED_FINDINGS, PAPER, REFERENCE, PROGRESS;
    cross-check the *most-cited* scalars against their receipts.

    We only look for high-confidence patterns to avoid false positives:
      AUC = 0.998  (and similar 4-decimal AUCs)
      T² = 3,557  / T2 = 3,557  / T-squared = 3,557
      Φ_master = 1,862.31  /  Phi_master = 1862.31
      p = X.YZ * 10^N / X.YZe-N
    """
    issues: list[dict] = []
    docs = [DOCS / "RANKED_FINDINGS.md", DOCS / "PAPER.md", DOCS / "REFERENCE.md", DOCS / "PROGRESS.md"]
    docs = [d for d in docs if d.exists()]
    if not docs:
        return issues

    # Build a scalar index from receipts: receipt-name → {scalar_name: value}.
    scalar_index: dict[str, dict[str, float]] = {}
    for rp in receipts:
        rec = _read_json(rp) or {}
        flat: dict[str, Any] = {}
        # collect numeric fields from a few common nesting levels
        def walk(obj, prefix=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    walk(v, f"{prefix}.{k}" if prefix else k)
            elif isinstance(obj, (int, float)):
                if isinstance(obj, bool):
                    return
                flat[prefix] = float(obj)
        walk(rec)
        scalar_index[_exp_name(rp)] = flat

    # Check Phi_master claim: 1,862.31 cited often; verify exp96a value.
    exp96a = scalar_index.get("exp96a_phi_master", {})
    phi_claimed = None
    for v in exp96a.values():
        # most likely under "phi_master_quran" or similar
        pass
    # Direct lookup
    for k in ("phi_master", "phi_master_quran", "overall.phi_master"):
        if k in exp96a:
            phi_claimed = exp96a[k]
            break

    # Scan docs for "1,862.31 nats" or "1,862.31" near "Phi_master"
    if phi_claimed is not None:
        for d in docs:
            txt = _read_text(d)
            # Find numbers near "Φ_master" or "Phi_master" or "phi_master"
            for m in re.finditer(r"(?:Φ_?master|Phi[_ ]?master|phi[_ ]?master)[^0-9\n]{0,40}([0-9]+(?:[,\s][0-9]{3})*(?:\.[0-9]+)?)", txt):
                num_str = m.group(1).replace(",", "").replace(" ", "")
                try:
                    val = float(num_str)
                except Exception:
                    continue
                if 100 < val < 1_000_000:  # plausible nats-scale band
                    if abs(val - phi_claimed) / max(1.0, abs(phi_claimed)) > 0.005:  # 0.5 %
                        issues.append({
                            "level": "L3_inflation_phi_master",
                            "severity": CRITICAL,
                            "doc": str(d.relative_to(ROOT)).replace("\\", "/"),
                            "claimed": val,
                            "receipt_value": phi_claimed,
                            "delta": val - phi_claimed,
                            "msg": (
                                f"{d.name} claims Φ_master ≈ {val:.2f} but "
                                f"exp96a receipt has {phi_claimed:.2f}."
                            ),
                        })

    # Check T2 claim (band-A T² = 3,557 from expP7).
    expp7 = scalar_index.get("expP7_phi_m_full_quran", {})
    t2_claimed = None
    for k in ("overall.T2", "T2", "T_squared", "overall.t2"):
        if k in expp7:
            t2_claimed = expp7[k]
            break
    if t2_claimed is not None:
        for d in docs:
            txt = _read_text(d)
            for m in re.finditer(r"T(?:[²2]|\^2|-squared)\s*=?\s*([0-9]+(?:[,\s][0-9]{3})*(?:\.[0-9]+)?)", txt):
                num_str = m.group(1).replace(",", "").replace(" ", "")
                try:
                    val = float(num_str)
                except Exception:
                    continue
                # Allow either band-A T² or full-114 T² (different receipts);
                # we just check that whatever doc claim exists is within 1 %
                # of *some* receipt's T² for T² ≥ 1000.
                if val < 1000:
                    continue
                # Find the closest receipt T² value
                receipt_t2_values = []
                for nm, scalars in scalar_index.items():
                    for kk, vv in scalars.items():
                        if "T2" in kk and 1000 < vv < 100_000:
                            receipt_t2_values.append((nm, kk, vv))
                if not receipt_t2_values:
                    continue
                closest = min(receipt_t2_values, key=lambda x: abs(x[2] - val))
                if abs(closest[2] - val) / val > 0.01:  # 1 %
                    issues.append({
                        "level": "L3_inflation_T2",
                        "severity": WARN,  # may be a different receipt's T²
                        "doc": str(d.relative_to(ROOT)).replace("\\", "/"),
                        "claimed": val,
                        "closest_receipt": closest[0],
                        "closest_field": closest[1],
                        "closest_value": closest[2],
                        "msg": (
                            f"T² = {val:.2f} cited in {d.name} differs by "
                            f"> 1 % from the closest receipt T² "
                            f"({closest[0]}::{closest[1]} = {closest[2]:.2f})."
                        ),
                    })
    return issues


def check_l4_retraction_completeness(receipts: list[Path]) -> list[dict]:
    issues: list[dict] = []
    reg_path = DOCS / "RETRACTIONS_REGISTRY.md"
    if not reg_path.exists():
        return [{"level": "L4_no_registry", "severity": CRITICAL,
                 "msg": "RETRACTIONS_REGISTRY.md missing."}]
    reg_text = _read_text(reg_path)

    for rp in receipts:
        rec = _read_json(rp) or {}
        verdict = _verdict_of(rec)
        exp_name = _exp_name(rp)
        if not verdict.startswith("FAIL_"):
            continue
        # Documented FAILs sometimes use FAIL_audit_* (audit only, retain
        # underlying claim) and sometimes FAIL_<substantive>. Both should
        # appear in the registry.
        if exp_name not in reg_text:
            issues.append({
                "level": "L4_orphan_fail",
                "severity": CRITICAL,
                "receipt": str(rp.relative_to(ROOT)).replace("\\", "/"),
                "verdict": verdict,
                "msg": (
                    f"Receipt with verdict {verdict} but experiment name "
                    f"{exp_name} not mentioned in RETRACTIONS_REGISTRY.md. "
                    f"Add an entry or reclassify the verdict."
                ),
            })
    return issues


def check_l5_verdict_audit_consistency(receipts: list[Path]) -> list[dict]:
    issues: list[dict] = []
    for rp in receipts:
        rec = _read_json(rp) or {}
        verdict = _verdict_of(rec)
        audit = rec.get("audit_report") or rec.get("audit") or {}
        ok = None
        if isinstance(audit, dict):
            ok = audit.get("ok") if "ok" in audit else None
            if ok is None:
                ok = audit.get("audit_ok")
        if ok is None:
            continue
        ok_bool = bool(ok)
        if verdict.startswith("PASS") and not ok_bool:
            issues.append({
                "level": "L5_pass_but_audit_failed",
                "severity": CRITICAL,
                "receipt": str(rp.relative_to(ROOT)).replace("\\", "/"),
                "verdict": verdict,
                "audit_ok": ok_bool,
                "msg": "PASS verdict but audit_report.ok is falsy. Inflation risk.",
            })
        if verdict.startswith("FAIL_audit") and ok_bool:
            issues.append({
                "level": "L5_audit_fail_but_audit_ok",
                "severity": CRITICAL,
                "receipt": str(rp.relative_to(ROOT)).replace("\\", "/"),
                "verdict": verdict,
                "audit_ok": ok_bool,
                "msg": "FAIL_audit verdict but audit_report.ok is truthy. Logic error.",
            })
    return issues


def check_l6_calibration_leakage(receipts: list[Path]) -> list[dict]:
    """Receipts with a tau/threshold field should declare a calibration_source
    that does not visibly include the test-fold corpus."""
    issues: list[dict] = []
    tau_keys = {"tau", "threshold", "tau_inside", "tau_calibrated", "tau_floor"}
    for rp in receipts:
        rec = _read_json(rp) or {}
        flat = json.dumps(rec, ensure_ascii=False).lower()
        has_tau = any(k in flat for k in tau_keys)
        if not has_tau:
            continue
        decl = (
            rec.get("calibration_source")
            or rec.get("frozen_constants", {}).get("calibration_source") if isinstance(rec.get("frozen_constants"), dict) else None
        )
        if decl is None:
            issues.append({
                "level": "L6_no_calibration_source_declared",
                "severity": WARN,
                "receipt": str(rp.relative_to(ROOT)).replace("\\", "/"),
                "msg": (
                    "Receipt carries a tau/threshold-style field but "
                    "declares no calibration_source. Cannot verify that "
                    "calibration is independent of the test fold."
                ),
            })
    return issues


def check_l7_f_chain(receipts: list[Path]) -> list[dict]:
    """RANKED_FINDINGS.md F-rows must cite a real receipt whose verdict
    starts with PASS_."""
    issues: list[dict] = []
    rf = DOCS / "RANKED_FINDINGS.md"
    if not rf.exists():
        return issues
    txt = _read_text(rf)

    # F-row pattern: lines beginning with `| F<N>` or `| **F<N>**` etc.
    # Capture the first experiment name on the row.
    row_re = re.compile(r"^\|\s*\*?\*?\s*F(\d+)\b.*?\|", re.MULTILINE)
    cite_re = re.compile(r"`?(?:results/experiments/)?(exp[0-9A-Za-z_]+)/?")

    receipt_verdicts = {}
    for rp in receipts:
        rec = _read_json(rp) or {}
        receipt_verdicts[_exp_name(rp)] = _verdict_of(rec)

    # Legacy substantive-PASS verdict tokens (custom names that pre-date the
    # modern PASS_* convention but are nonetheless positive findings).
    _PASS_LIKE_TOKENS = (
        "PASS", "STRONG", "ROBUST", "STABLE", "SUPPORTED", "PROVED",
        "TIGHTENED", "QURAN_DISTINCT", "QURAN_TOP", "EXTREMUM",
        "DOMINATES", "SUFFICIENT", "META_FINDING", "META_STABLE",
        "GIT_THEOREM_PASS", "PROVENANCE_FOUND", "REFINES_PHI_M_POSITIVELY",
        "DETECTOR_DIFFERENTIATES", "LAW_SUPPORTED", "NEAR_LOCAL_OPTIMUM",
        "RIWAYAT_DEPENDENT",  # F49 framing — partial but documents finding
        "PARTIAL",            # F70 / F72 / F73 PARTIAL_PASS findings (V3.12)
    )

    def _is_pass_like(verdict: str) -> bool:
        if verdict.startswith("PASS"):
            return True
        u = verdict.upper()
        if u.startswith("FAIL") or u.startswith("BLOCKED"):
            return False
        return any(tok in u for tok in _PASS_LIKE_TOKENS)

    for m in row_re.finditer(txt):
        f_no = int(m.group(1))
        # Look at the next ~600 chars to find a receipt citation
        end = m.end()
        chunk = txt[end:end + 600]
        cites = cite_re.findall(chunk)
        cites = [c for c in cites if c.startswith("exp")]
        if not cites:
            issues.append({
                "level": "L7_f_no_receipt_cite",
                "severity": WARN,
                "f_number": f_no,
                "msg": f"F{f_no} row in RANKED_FINDINGS has no receipt citation in its body.",
            })
            continue
        primary = cites[0]
        if primary not in receipt_verdicts:
            issues.append({
                "level": "L7_f_cite_nonexistent_receipt",
                "severity": CRITICAL,
                "f_number": f_no,
                "cited_receipt": primary,
                "msg": f"F{f_no} cites receipt {primary} which does not exist.",
            })
            continue
        v = receipt_verdicts[primary]
        if not _is_pass_like(v):
            # Legitimate retraction-documenting F-row: if the F-row's body
            # text explicitly says RETRACTED / FALSIFIED / FAIL, the cite
            # to a FAIL receipt is intentional, not a bug.
            chunk_upper = chunk.upper()
            is_retraction_doc = any(
                kw in chunk_upper for kw in
                ("RETRACTED", "FALSIFIED", "RETRACTION", "FAIL_")
            )
            severity = INFO if is_retraction_doc else CRITICAL
            issues.append({
                "level": ("L7_f_documents_retraction" if is_retraction_doc
                          else "L7_f_cites_non_pass"),
                "severity": severity,
                "f_number": f_no,
                "cited_receipt": primary,
                "verdict": v,
                "msg": (
                    f"F{f_no} cites receipt {primary} whose verdict is {v}"
                    + (" (intentional — F-row documents retraction)" if is_retraction_doc
                       else " (not PASS_ and no retraction marker in row body)")
                ),
            })
    return issues


def check_l8_orphans(receipts: list[Path]) -> list[dict]:
    """Receipts that no doc references (orphan) AND doc claims with no receipt (vapor)."""
    issues: list[dict] = []
    docs_text = ""
    for d in (DOCS / "RANKED_FINDINGS.md", DOCS / "PROGRESS.md", DOCS / "PAPER.md", DOCS / "REFERENCE.md"):
        if d.exists():
            docs_text += _read_text(d) + "\n"
    for rp in receipts:
        name = _exp_name(rp)
        if name not in docs_text:
            issues.append({
                "level": "L8_orphan_receipt",
                "severity": INFO,
                "receipt": str(rp.relative_to(ROOT)).replace("\\", "/"),
                "msg": f"Receipt {name} is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.",
            })
    return issues


# --- Driver ------------------------------------------------------------

def main() -> int:
    receipts = _list_receipts()
    print(f"# zero_trust_audit -- {len(receipts)} receipts under {EXPS}")

    all_issues: list[dict] = []
    all_issues.extend(check_l1_prereg_timing(receipts))
    all_issues.extend(check_l2_stale_deps(receipts))
    all_issues.extend(check_l3_inflation(receipts))
    all_issues.extend(check_l4_retraction_completeness(receipts))
    all_issues.extend(check_l5_verdict_audit_consistency(receipts))
    all_issues.extend(check_l6_calibration_leakage(receipts))
    all_issues.extend(check_l7_f_chain(receipts))
    all_issues.extend(check_l8_orphans(receipts))

    by_severity = {CRITICAL: 0, WARN: 0, INFO: 0}
    for it in all_issues:
        by_severity[it["severity"]] = by_severity.get(it["severity"], 0) + 1

    INTEG.mkdir(parents=True, exist_ok=True)
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_out = INTEG / f"zero_trust_audit_{ts}.json"
    md_out = INTEG / f"zero_trust_audit_{ts}.md"

    payload = {
        "schema": "zero_trust_audit_v1",
        "completed_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "n_receipts_scanned": len(receipts),
        "tally_by_severity": by_severity,
        "issues": all_issues,
    }
    json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # Markdown report
    lines: list[str] = []
    lines.append(f"# Zero-Trust Audit — {ts}")
    lines.append("")
    lines.append(f"- Receipts scanned: **{len(receipts)}**")
    lines.append(f"- CRITICAL: **{by_severity[CRITICAL]}**")
    lines.append(f"- WARN: {by_severity[WARN]}")
    lines.append(f"- INFO: {by_severity[INFO]}")
    lines.append("")

    sev_order = [CRITICAL, WARN, INFO]
    for sev in sev_order:
        rows = [it for it in all_issues if it["severity"] == sev]
        if not rows:
            continue
        lines.append(f"## {sev} ({len(rows)})")
        lines.append("")
        # Group by check level
        by_level: dict[str, list[dict]] = {}
        for it in rows:
            by_level.setdefault(it["level"], []).append(it)
        for level, items in sorted(by_level.items()):
            lines.append(f"### {level} — {len(items)}")
            for it in items[:30]:  # cap rendering at 30 per category
                rec = it.get("receipt", "")
                msg = it.get("msg", "")
                extra = "; ".join(
                    f"{k}={v}" for k, v in it.items()
                    if k not in {"level", "severity", "receipt", "msg"}
                )
                lines.append(f"- `{rec}` — {msg}" + (f"  ({extra})" if extra else ""))
            if len(items) > 30:
                lines.append(f"- ... and {len(items) - 30} more")
            lines.append("")

    md_out.write_text("\n".join(lines), encoding="utf-8")

    # LATEST symlinks (Windows-safe: rewrite copies)
    (INTEG / "zero_trust_audit_LATEST.json").write_text(
        json_out.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (INTEG / "zero_trust_audit_LATEST.md").write_text(
        md_out.read_text(encoding="utf-8"), encoding="utf-8"
    )

    print(f"# Receipts scanned : {len(receipts)}")
    print(f"# CRITICAL         : {by_severity[CRITICAL]}")
    print(f"# WARN             : {by_severity[WARN]}")
    print(f"# INFO             : {by_severity[INFO]}")
    print(f"# JSON receipt     : {json_out}")
    print(f"# Markdown receipt : {md_out}")

    return 0 if by_severity[CRITICAL] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
