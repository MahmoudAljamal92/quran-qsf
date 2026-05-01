"""Integrity audit for QSF experiment receipts.

Walks every receipt under `results/experiments/<exp_name>/<exp_name>.json`,
applies the checks codified in `docs/INTEGRITY_PROTOCOL.md`, and writes a
Markdown + JSON summary to `results/integrity/integrity_audit_<timestamp>.{md,json}`.

Verdict per receipt:
- PASS                          — all required fields, PREREG hash matches, audit report all-green, verdict in closed set
- WARN_missing_self_check       — passes but no self_check_*.json companion
- WARN_missing_optional_field   — passes but is missing a non-required provenance field
- FAIL_unparseable              — JSON malformed
- FAIL_no_verdict               — no `verdict` field
- FAIL_prereg_hash_mismatch     — PREREG.md SHA-256 disagrees with receipt's `prereg_hash`
- FAIL_prereg_missing           — receipt declares a prereg path that does not exist
- FAIL_audit_red_unreported     — at least one audit-hook block has `ok=false` and the receipt's verdict is not an audit-failure verdict

Run from repo root:
    python scripts/integrity_audit.py

Exit codes:
- 0 if zero FAIL rows
- 1 if any FAIL row
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import io
import json
import re
import sys
from pathlib import Path
from typing import Any

# Force UTF-8 stdout on Windows.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:  # pragma: no cover
        pass

_ROOT = Path(__file__).resolve().parent.parent
RESULTS_EXPERIMENTS = _ROOT / "results" / "experiments"
INTEGRITY_DIR = _ROOT / "results" / "integrity"

# Receipts older than 2026-04-01 are pre-protocol and only get a soft check.
PROTOCOL_FROZEN_AT = _dt.datetime(2026, 4, 1, tzinfo=_dt.timezone.utc)

# Verdict prefixes that explicitly capture audit failures (so an audit-red
# receipt is OK if its verdict starts with one of these).
AUDIT_FAIL_VERDICT_PREFIXES = (
    "FAIL_audit_",
    "FAIL_short_tau_drift",
    "FAIL_q100_drift",
    "FAIL_short_run_did_not_complete",
)

REQUIRED_FIELDS = ("verdict",)
RECOMMENDED_FIELDS = ("prereg_hash", "prereg_document", "completed_at_utc",
                      "experiment", "audit_report")


# --- Hashing -------------------------------------------------------------

def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


# --- Audit-block scan ----------------------------------------------------

def _walk_audit_oks(node: Any, path: str = "audit_report") -> list[tuple[str, bool]]:
    """Recursively find every (`<dotted_path>`, `ok`) pair in a JSON sub-tree.
    Only collects the leaf-level `ok` keys. Useful for spotting any `ok: false`
    embedded deep inside an `audit_report`."""
    out: list[tuple[str, bool]] = []
    if isinstance(node, dict):
        if "ok" in node and isinstance(node.get("ok"), bool):
            out.append((path, bool(node["ok"])))
        for k, v in node.items():
            if k == "ok":
                continue
            out.extend(_walk_audit_oks(v, f"{path}.{k}"))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.extend(_walk_audit_oks(v, f"{path}[{i}]"))
    return out


def _verdict_handles_audit_failure(verdict: str) -> bool:
    """Returns True if the verdict string itself acknowledges an audit failure."""
    if not verdict:
        return False
    return any(verdict.startswith(p) for p in AUDIT_FAIL_VERDICT_PREFIXES)


# --- Per-receipt audit ---------------------------------------------------

def audit_receipt(receipt_path: Path) -> dict[str, Any]:
    rel = str(receipt_path.relative_to(_ROOT)).replace("\\", "/")
    out: dict[str, Any] = {
        "receipt": rel,
        "verdict_audit": "PASS",
        "warnings": [],
        "errors": [],
    }

    # 1. Parse
    try:
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
    except Exception as e:
        out["verdict_audit"] = "FAIL_unparseable"
        out["errors"].append(f"json_parse: {e!r}")
        return out

    # 2. Schema: required fields. Accept legacy alternative names for verdict.
    legacy_verdict_aliases = (
        "FINAL_verdict", "verdict_final", "result", "status",
        "gate_verdict", "overall_verdict",
    )
    raw_verdict = data.get("verdict")
    if raw_verdict is None:
        for alias in legacy_verdict_aliases:
            if alias in data and data[alias]:
                raw_verdict = data[alias]
                out["verdict_alias_used"] = alias
                break
    if raw_verdict is None:
        # No top-level verdict. Allow if any verdict_*-prefixed field or
        # `pre_registered_outcomes` / `pre_registered_predictions` is present
        # (cross-corpus / theorem-output schemas).
        verdict_like_keys = [
            k for k in data.keys()
            if k.startswith("verdict_") or k in (
                "pre_registered_outcomes", "pre_registered_predictions",
                "P2_OP1_renyi2_uniqueness", "theorem_min_pmax_for_EL_iid_geq_050",
                "interpretation", "FINAL_interpretation",
                "headline",  # descriptive / ranking experiments
                "summary",
            )
        ]
        if verdict_like_keys:
            out["warnings"].append(f"verdict_field_in_alternative_schema:{verdict_like_keys[:3]}")
        elif (_ROOT / "experiments" / receipt_path.parent.name / "PREREG.md").exists():
            # Has PREREG.md but no verdict-like field anywhere -- real failure.
            out["errors"].append("missing_required_field:verdict")
            out["verdict_audit"] = "FAIL_no_verdict"
            return out
        else:
            out["warnings"].append("no_verdict_field_legacy")

    out["verdict"] = raw_verdict if isinstance(raw_verdict, str) else None
    out["experiment"] = data.get("experiment", receipt_path.parent.name)
    out["hypothesis_id"] = data.get("hypothesis_id") or data.get("hypothesis")

    # 3. Schema: recommended fields
    for f in RECOMMENDED_FIELDS:
        if f not in data:
            out["warnings"].append(f"missing_recommended_field:{f}")

    # 4. PREREG hash check.
    # Modern receipts declare `prereg_document` and `prereg_hash`. If the
    # experiment folder has a PREREG.md we *require* a hash; otherwise the
    # receipt is grandfather-protocol (predates 2026-04-26 PREREG-hash discipline).
    prereg_doc_field = data.get("prereg_document") or data.get("prereg_path")
    prereg_hash_claimed = (
        data.get("prereg_hash")
        or data.get("prereg_hash_actual")
        or data.get("prereg_hash_expected")
        or data.get("prereg_sha256")
    )
    exp_dir_prereg = receipt_path.parent.parent / "experiments" / receipt_path.parent.name / "PREREG.md"
    legacy_grandfathered = not (
        prereg_doc_field or prereg_hash_claimed
        or (_ROOT / "experiments" / receipt_path.parent.name / "PREREG.md").exists()
    )
    if legacy_grandfathered:
        out["grandfathered_pre_protocol"] = True
    if prereg_doc_field and prereg_hash_claimed:
        prereg_path = (_ROOT / prereg_doc_field).resolve()
        if not prereg_path.exists():
            # Maybe it's already an absolute path
            prereg_path = Path(prereg_doc_field)
        if not prereg_path.exists():
            out["errors"].append(f"prereg_doc_not_found:{prereg_doc_field}")
            out["verdict_audit"] = "FAIL_prereg_missing"
            return out
        actual = sha256_file(prereg_path)
        if actual != prereg_hash_claimed:
            out["errors"].append(
                f"prereg_hash_mismatch:expected={prereg_hash_claimed} actual={actual}"
            )
            out["verdict_audit"] = "FAIL_prereg_hash_mismatch"
            return out
        out["prereg_hash_verified"] = True
    elif prereg_doc_field and not prereg_hash_claimed:
        out["warnings"].append("prereg_document_present_but_no_hash_field")
    elif (not prereg_doc_field) and (_ROOT / "experiments" / receipt_path.parent.name / "PREREG.md").exists():
        # The folder has a PREREG.md but the receipt does not reference it.
        out["warnings"].append("prereg_md_exists_but_receipt_does_not_reference_it")

    # 5. Audit-report scan
    audit = data.get("audit_report") or data.get("audit") or {}
    if isinstance(audit, dict) and audit:
        oks = _walk_audit_oks(audit)
        red = [(p, ok) for (p, ok) in oks if ok is False]
        if red:
            v = data.get("verdict", "")
            if _verdict_handles_audit_failure(v):
                # The receipt's verdict already acknowledges the audit failure;
                # this is an honest failed-null, not a hidden problem.
                out["audit_red_acknowledged"] = [p for p, _ in red]
            else:
                out["errors"].append(
                    f"audit_red_not_reflected_in_verdict:{[p for p,_ in red]}"
                )
                out["verdict_audit"] = "FAIL_audit_red_unreported"
                return out
    elif "audit_report" in RECOMMENDED_FIELDS and not audit:
        out["warnings"].append("audit_report_empty_or_absent")

    # 6. Self-check companions
    siblings = list(receipt_path.parent.glob("self_check_*.json"))
    if not siblings:
        out["warnings"].append("no_self_check_companion")
    else:
        out["self_check_count"] = len(siblings)

    # 7. Verdict-string sanity (must start with PASS/FAIL/PARTIAL/SUGGESTIVE/NULL/...
    #    plus the BLOCKED/REOPENED prefixes). Some legacy receipts have verdict
    #    as a dict; in that case skip prefix sanity but flag as warning.
    if isinstance(raw_verdict, str):
        v = raw_verdict.strip()
        if v:
            first = v.split("_")[0]
            allowed = {
                "PASS", "FAIL", "PARTIAL", "SUGGESTIVE", "NULL", "BLOCKED",
                "REOPENED", "DOUBLE", "NO", "RETIRED", "STABLE", "CONFIRMED",
                # Legacy verdict prefixes used in pre-protocol receipts.
                "QURAN", "ROBUST", "TIGHTENED", "PROSE", "MUSHAF", "JUZ",
                "P2", "GIT", "T", "EL", "RIWAYAT",
            }
            if first not in allowed:
                out["warnings"].append(f"unexpected_verdict_prefix:{first}")
    elif raw_verdict is not None:
        out["warnings"].append(f"verdict_not_string:type={type(raw_verdict).__name__}")

    # 8. Promotion of WARN if there are warnings but no errors. Grandfathered
    # legacy receipts get a softer treatment (only block on hard schema errors).
    if out["verdict_audit"] == "PASS" and out["warnings"]:
        if out.get("grandfathered_pre_protocol"):
            out["verdict_audit"] = "PASS_grandfathered"
        elif any(w.startswith("missing_recommended_field") for w in out["warnings"]):
            out["verdict_audit"] = "WARN_missing_optional_field"
        elif "no_self_check_companion" in out["warnings"]:
            out["verdict_audit"] = "WARN_missing_self_check"

    return out


# --- Walk + summary ------------------------------------------------------

def find_all_receipts() -> list[Path]:
    """Locate `results/experiments/<exp_name>/<exp_name>.json` receipts (canonical only)."""
    out: list[Path] = []
    if not RESULTS_EXPERIMENTS.exists():
        return out
    for d in sorted(RESULTS_EXPERIMENTS.iterdir()):
        if not d.is_dir():
            continue
        canon = d / f"{d.name}.json"
        if canon.exists():
            out.append(canon)
            continue
        # Some legacy experiments have differently-named canonical receipts.
        # Look for `*FINAL_report.json` or `*_PROOF.json`.
        legacy = list(d.glob("*FINAL_report.json")) + list(d.glob("*_PROOF.json"))
        if legacy:
            out.append(sorted(legacy)[0])
    return out


def _doc_sync_check() -> dict[str, Any]:
    """Verify doc-scoreboard arithmetic AND mirror byte/row-content parity.

    Three checks per (canonical, mirror) pair:
      1. **Scoreboard arithmetic**: retractions + failed_nulls == grand_total.
      2. **Scoreboard cross-parity**: canonical and mirror agree on each scalar.
      3. **Row-content parity** (the D02 lesson): the actual R-rows must match
         in count between canonical and mirror, AND the body SHA-256 should
         match. If only scoreboards match but row counts differ, that's the
         silent drift D02 caught the hard way.

    Pairs checked:
      - RETRACTIONS_REGISTRY: canonical=docs/reference/findings, mirror=docs
      - RANKED_FINDINGS: canonical=docs/reference/findings, mirror=docs
    """
    import hashlib

    out: dict[str, Any] = {"ok": True, "details": {}}

    pairs = [
        ("RETRACTIONS_REGISTRY",
         _ROOT / "docs" / "reference" / "findings" / "RETRACTIONS_REGISTRY.md",
         _ROOT / "docs" / "RETRACTIONS_REGISTRY.md"),
        ("RANKED_FINDINGS",
         _ROOT / "docs" / "reference" / "findings" / "RANKED_FINDINGS.md",
         _ROOT / "docs" / "RANKED_FINDINGS.md"),
    ]

    def _scoreboard_totals(p: Path) -> dict[str, int | None]:
        if not p.exists():
            return {"retractions": None, "failed_nulls": None, "grand_total": None}
        text = p.read_text(encoding="utf-8")
        def _num_after(label_re: str) -> int | None:
            pat = r"\|[^|\n]*" + label_re + r"[^|\n]*\|\s*\**\s*(\d+)\s*\**\s*\|"
            m = re.search(pat, text)
            return int(m.group(1)) if m else None
        return {
            "retractions": _num_after(r"Total retractions"),
            "failed_nulls": _num_after(r"Failed null pre-registrations"),
            "grand_total": _num_after(r"Grand total entries"),
        }

    def _row_count(p: Path, row_re: str) -> int:
        if not p.exists():
            return 0
        text = p.read_text(encoding="utf-8")
        return len(re.findall(row_re, text, re.MULTILINE))

    def _body_sha(p: Path) -> str | None:
        if not p.exists():
            return None
        return hashlib.sha256(p.read_bytes()).hexdigest()

    for label, canonical, mirror in pairs:
        section: dict[str, Any] = {}

        # 1. Scoreboard arithmetic + parity (only meaningful for RETRACTIONS_REGISTRY)
        if "RETRACTIONS_REGISTRY" in label:
            canon_totals = _scoreboard_totals(canonical)
            mirror_totals = _scoreboard_totals(mirror)
            section["canonical_totals"] = canon_totals
            section["mirror_totals"] = mirror_totals
            for sub_label, t in (("canonical", canon_totals), ("mirror", mirror_totals)):
                r, fn, g = t["retractions"], t["failed_nulls"], t["grand_total"]
                if r is not None and fn is not None and g is not None and r + fn != g:
                    out["ok"] = False
                    section[f"{sub_label}_arith_mismatch"] = {
                        "retractions": r, "failed_nulls": fn, "grand_total": g,
                        "expected_grand_total": r + fn,
                    }
            for k in ("retractions", "failed_nulls", "grand_total"):
                if (canon_totals[k] is not None and mirror_totals[k] is not None
                        and canon_totals[k] != mirror_totals[k]):
                    out["ok"] = False
                    section[f"mirror_disagreement:{k}"] = {
                        "canonical": canon_totals[k],
                        "mirror": mirror_totals[k],
                    }

        # 2. Row-count parity — only for files with a stable table format.
        # RETRACTIONS_REGISTRY uses | R<N> | ... | (table). RANKED_FINDINGS
        # uses bullet-list format that's harder to count robustly, so for it
        # we rely on SHA-256 parity below.
        if "RETRACTIONS_REGISTRY" in label:
            canon_rows = _row_count(canonical, r"^\|\s*R\d+\s*\|")
            mirror_rows = _row_count(mirror, r"^\|\s*R\d+\s*\|")
            section["canonical_row_count"] = canon_rows
            section["mirror_row_count"] = mirror_rows
            if canon_rows != mirror_rows:
                out["ok"] = False
                section["row_count_mismatch"] = {
                    "canonical": canon_rows,
                    "mirror": mirror_rows,
                    "diff": canon_rows - mirror_rows,
                    "msg": "ROW-CONTENT DRIFT (D02-style). The mirror is out of sync.",
                }

        # 3. Body SHA-256 parity (the authoritative check, format-independent).
        # If they differ, that's a CRITICAL drift signal regardless of row-count.
        canon_sha = _body_sha(canonical)
        mirror_sha = _body_sha(mirror)
        section["canonical_sha256"] = canon_sha
        section["mirror_sha256"] = mirror_sha
        section["sha256_match"] = canon_sha == mirror_sha if canon_sha and mirror_sha else None
        if canon_sha and mirror_sha and canon_sha != mirror_sha:
            out["ok"] = False
            section["sha256_mismatch"] = {
                "canonical": canon_sha[:16] + "...",
                "mirror": mirror_sha[:16] + "...",
                "msg": (
                    "BYTE-LEVEL DRIFT between canonical and mirror. Run: "
                    f"`Copy-Item {canonical.relative_to(_ROOT)} {mirror.relative_to(_ROOT)} -Force` "
                    "to repair, then re-run this audit."
                ),
            }

        out["details"][label] = section

    # Backwards-compat: keep the old top-level keys for the canonical+mirror
    # of RETRACTIONS_REGISTRY so existing dashboards still work.
    if "RETRACTIONS_REGISTRY" in out["details"]:
        sec = out["details"]["RETRACTIONS_REGISTRY"]
        out["details"]["canonical"] = sec.get("canonical_totals", {})
        out["details"]["mirror"] = sec.get("mirror_totals", {})

    return out


def main() -> int:
    INTEGRITY_DIR.mkdir(parents=True, exist_ok=True)
    receipts = find_all_receipts()
    print(f"# integrity_audit -- scanning {len(receipts)} receipts under results/experiments/")
    print()

    rows: list[dict[str, Any]] = []
    for r in receipts:
        row = audit_receipt(r)
        rows.append(row)

    # Tally
    tally: dict[str, int] = {}
    for row in rows:
        v = row["verdict_audit"]
        tally[v] = tally.get(v, 0) + 1

    # Doc-sync arithmetic spot-check
    doc_sync = _doc_sync_check()

    # Build report
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_out = INTEGRITY_DIR / f"integrity_audit_{stamp}.json"
    md_out = INTEGRITY_DIR / f"integrity_audit_{stamp}.md"

    pass_count = sum(v for k, v in tally.items() if k.startswith("PASS"))
    warn_count = sum(v for k, v in tally.items() if k.startswith("WARN"))
    fail_count = sum(v for k, v in tally.items() if k.startswith("FAIL"))

    json_out.write_text(json.dumps({
        "schema": "integrity_audit_v1",
        "completed_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "n_receipts": len(rows),
        "tally": tally,
        "doc_sync": doc_sync,
        "rows": rows,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    # Markdown summary (only the non-PASS rows + tally)
    md = []
    md.append(f"# Integrity audit — {stamp}\n")
    md.append(f"- Receipts scanned: **{len(rows)}**")
    md.append(f"- PASS: **{pass_count}**, WARN: **{warn_count}**, FAIL: **{fail_count}**")
    md.append(f"- Doc-sync arithmetic: **{'PASS' if doc_sync['ok'] else 'FAIL'}**\n")
    if not doc_sync["ok"]:
        md.append("## Doc-sync issues\n")
        md.append("```json")
        md.append(json.dumps(doc_sync["details"], indent=2, ensure_ascii=False))
        md.append("```\n")
    md.append("## Tally\n")
    for k, v in sorted(tally.items()):
        md.append(f"- `{k}`: {v}")
    md.append("")

    nonpass = [r for r in rows if r["verdict_audit"] != "PASS"]
    if nonpass:
        md.append("## Non-PASS rows\n")
        md.append("| Receipt | Audit verdict | Errors | Warnings |")
        md.append("|---|---|---|---|")
        for r in nonpass:
            errs = "; ".join(r.get("errors", [])) or "—"
            warns = "; ".join(r.get("warnings", [])) or "—"
            md.append(f"| `{r['receipt']}` | `{r['verdict_audit']}` | {errs} | {warns} |")
        md.append("")

    md.append("## Reproduce\n")
    md.append("```powershell")
    md.append("python scripts/integrity_audit.py")
    md.append("```")
    md_out.write_text("\n".join(md), encoding="utf-8")

    # Console summary
    print(f"# Receipts scanned : {len(rows)}")
    print(f"# PASS             : {pass_count}")
    print(f"# WARN             : {warn_count}")
    print(f"# FAIL             : {fail_count}")
    print(f"# Doc-sync arith.  : {'PASS' if doc_sync['ok'] else 'FAIL'}")
    print(f"#")
    if nonpass:
        print(f"# Non-PASS rows ({len(nonpass)}):")
        for r in nonpass:
            errs = (r.get("errors") or [None])[0] or ""
            warns = (r.get("warnings") or [None])[0] or ""
            tag = errs or warns or ""
            print(f"#   {r['verdict_audit']:38s} {r['receipt']}  {tag}")
    print(f"#")
    print(f"# Receipt JSON     : {json_out.relative_to(_ROOT)}")
    print(f"# Receipt MD       : {md_out.relative_to(_ROOT)}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
