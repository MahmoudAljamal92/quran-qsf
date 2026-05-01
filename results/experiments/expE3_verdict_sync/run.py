"""
expE3_verdict_sync — Cross-document verdict sync audit.

Per docs/EXECUTION_PLAN_AND_PRIORITIES.md E3:
  1. Parse canonical verdicts for H1..H31 from docs/HYPOTHESES_AND_TESTS.md
     Execution Tracker table (the single source of truth per PROJECT_MAP.md).
  2. Grep each H-ID across PAPER.md, RANKED_FINDINGS.md,
     DEEPSCAN_ULTIMATE_FINDINGS.md, OPPORTUNITY_SCAN_2026-04-22.md.
  3. Extract the verdict string mentioned near each H-ID in each doc.
  4. Flag mismatches -> emit diff report.

This is an *audit* script: it does not modify any doc. If mismatches are
found, a follow-up patch pass (human-reviewed) edits the off-canonical docs.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT   = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUTDIR = ROOT / "results" / "experiments" / "expE3_verdict_sync"
OUTDIR.mkdir(parents=True, exist_ok=True)

CANON_DOC = ROOT / "docs" / "HYPOTHESES_AND_TESTS.md"
TARGET_DOCS = [
    ROOT / "docs" / "PAPER.md",
    ROOT / "docs" / "RANKED_FINDINGS.md",
    ROOT / "docs" / "DEEPSCAN_ULTIMATE_FINDINGS.md",
    ROOT / "docs" / "OPPORTUNITY_SCAN_2026-04-22.md",
]

# ---- Verdict vocabulary (observed in HYPOTHESES_AND_TESTS tracker) ---------
# Categorised by polarity for cosmetic-vs-semantic drift detection.
VERDICT_GROUPS = {
    "POSITIVE": {
        "PROVED", "PASS", "DETERMINATE", "EQUATION_DERIVED", "DISTINCT",
        "SIGNIFICANT", "LAW_CONFIRMED", "ANOMALY_SURVIVES",
    },
    "SUGGESTIVE": {
        "SUGGESTIVE", "SUGGESTIVE_UNIVERSAL", "PARTIAL", "PARTIAL_BRIDGE",
        "BIMODAL_MODERATE", "BENFORD_DEVIATING", "DIRECTIONAL",
    },
    "WEAK_OR_REDUNDANT": {
        "WEAK", "REDUNDANT", "SIGNIFICANT_BUT_REDUNDANT",
        "ROBUST_ARBITRARY_CONSTANT_MINOR_LEAK", "LENGTH_DRIVEN",
    },
    "NEGATIVE": {
        "NULL", "FAILS", "FAIL", "FALSIFIED", "FALSIFIER_TRIGGERED",
        "NOT REPRODUCED", "NOT_REPRODUCED", "RETRACTED",
    },
    "ADMIN": {"SKIPPED"},
}
ALL_VERDICTS = {v for g in VERDICT_GROUPS.values() for v in g}

def group_of(v: str) -> str:
    v_norm = v.upper().replace(" ", "_")
    for g, vs in VERDICT_GROUPS.items():
        if v_norm in {x.upper().replace(" ", "_") for x in vs}:
            return g
    return "UNKNOWN"

# ---- Parse canonical tracker from HYPOTHESES_AND_TESTS.md -----------------
# The tracker is a pipe-delimited table whose rows look like:
#   | H16 | LC3 ... | exp60 | **PARTIAL** — ... | 2026-04-21 |
# with occasional multi-verdict cells like "PARTIAL", "SIGNIFICANT", etc.
# We capture the H-ID and the bolded-or-caps verdict token.
canon_text = CANON_DOC.read_text(encoding="utf-8")

row_re = re.compile(
    r"^\|\s*(H\d+(?:→\w+)?)\s*\|"     # H-ID (H16, H16->Adiyat, etc.)
    r"[^|]*\|"                        # hypothesis name col
    r"[^|]*\|"                        # experiment col
    r"\s*([^|]+?)\s*\|"               # verdict col
    r"\s*([0-9\-]+|—)\s*\|",          # date col
    re.MULTILINE,
)

canon: dict[str, dict] = {}
for m in row_re.finditer(canon_text):
    h_id_raw = m.group(1).replace("→", "_to_")
    verdict_cell = m.group(2).strip()
    # Strip markdown bold/italic
    cleaned = re.sub(r"\*+", "", verdict_cell)
    # Take the first all-caps token up to whitespace/punct as the canonical verdict.
    tok_m = re.match(r"([A-Z][A-Z_]+(?:\s[A-Z][A-Z_]+)*)", cleaned)
    verdict_token = tok_m.group(1).strip() if tok_m else cleaned.split("—")[0].strip()
    canon[h_id_raw] = {
        "hypothesis_id": h_id_raw,
        "verdict_token": verdict_token,
        "verdict_group": group_of(verdict_token),
        "full_verdict_cell": cleaned.strip(),
        "date": m.group(3).strip(),
    }

# Known post-tracker hypotheses from in-body headings (H21..H22..H31 etc.):
# These are embedded in the body with "### Hn:" headers and have
# "#### EXECUTED" + "**Verdict**: ..." lines. Parse those too.
body_verdict_re = re.compile(
    r"^###\s+(H\d+)[:\s].*?"
    r"####\s*(?:✅\s*|❌\s*)?EXECUTED.*?"
    r"\*\*Verdict\*\*:\s*\**([A-Z_][A-Z_ ]*)",
    re.MULTILINE | re.DOTALL,
)
for m in body_verdict_re.finditer(canon_text):
    h_id = m.group(1)
    if h_id in canon:
        continue  # tracker already has it
    verdict_token = m.group(2).strip().rstrip("*").strip()
    canon[h_id] = {
        "hypothesis_id": h_id,
        "verdict_token": verdict_token,
        "verdict_group": group_of(verdict_token),
        "full_verdict_cell": verdict_token,
        "date": "body-section",
    }

canon = dict(sorted(canon.items(), key=lambda kv: (
    int(re.match(r"H(\d+)", kv[0]).group(1)),
    kv[0]
)))

# ---- Scan each target doc for each H-ID ----------------------------------
def extract_context(text: str, pos: int, radius: int = 400) -> str:
    lo = max(0, pos - radius // 3)
    hi = min(len(text), pos + radius)
    return text[lo:hi].replace("\n", " ")

scan_rows: list[dict] = []
for doc in TARGET_DOCS:
    if not doc.exists():
        continue
    text = doc.read_text(encoding="utf-8", errors="replace")
    lower_text = text
    for h_id, c in canon.items():
        base = h_id.split("_to_")[0]   # "H16_to_Adiyat" -> "H16"
        # Find occurrences of "H16" as a token (avoid matching H160, etc.)
        for m in re.finditer(rf"\b{re.escape(base)}\b", text):
            ctx = extract_context(text, m.start(), radius=500)
            # Pull verdict tokens present in this context, if any.
            found_verdicts = set()
            for v in ALL_VERDICTS:
                if re.search(rf"\b{re.escape(v)}\b", ctx):
                    found_verdicts.add(v)
            # Only record if either a verdict is nearby OR the H-ID appears on
            # a line that looks structured (contains | or verdict synonyms).
            structural = "|" in ctx or "EXECUTED" in ctx or "Verdict" in ctx
            if not (found_verdicts or structural):
                # Heuristic noise filter: skip pure prose H16 mentions without
                # any verdict context; they are not sync risks.
                continue
            canon_token = c["verdict_token"].upper().replace(" ", "_")
            match_status = "NO_VERDICT_NEAR_HID"
            if found_verdicts:
                found_groups = {group_of(v) for v in found_verdicts}
                canon_group = c["verdict_group"]
                if canon_token in {v.upper().replace(" ", "_") for v in found_verdicts}:
                    match_status = "EXACT_MATCH"
                elif canon_group in found_groups:
                    match_status = "SAME_GROUP"
                else:
                    match_status = "GROUP_MISMATCH"
            line_no = text.count("\n", 0, m.start()) + 1
            scan_rows.append({
                "doc":           str(doc.relative_to(ROOT)).replace("\\", "/"),
                "hypothesis_id": h_id,
                "line":          line_no,
                "canon_verdict": c["verdict_token"],
                "canon_group":   c["verdict_group"],
                "found_verdicts_nearby": sorted(found_verdicts),
                "match_status":  match_status,
                "context":       ctx.strip()[:400],
            })

# ---- Emit JSON + markdown diff report ------------------------------------
# Counts
from collections import Counter
status_counts = Counter(r["match_status"] for r in scan_rows)
per_doc_counts = {}
for r in scan_rows:
    per_doc_counts.setdefault(r["doc"], Counter())[r["match_status"]] += 1

summary = {
    "experiment_id": "expE3_verdict_sync",
    "task": "E3",
    "tier": 1,
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "canonical_source": str(CANON_DOC.relative_to(ROOT)).replace("\\", "/"),
    "canonical_hypothesis_count": len(canon),
    "docs_scanned": [str(d.relative_to(ROOT)).replace("\\", "/") for d in TARGET_DOCS],
    "total_references": len(scan_rows),
    "status_counts": dict(status_counts),
    "per_doc_counts": {d: dict(c) for d, c in per_doc_counts.items()},
    "canon_verdicts": canon,
}

(OUTDIR / "expE3_report.json").write_text(
    json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
)
(OUTDIR / "scan_rows.json").write_text(
    json.dumps(scan_rows, indent=2, ensure_ascii=False), encoding="utf-8"
)

# Markdown diff report: focus on mismatches.
md = [
    "# expE3 — Cross-Document Verdict Sync (audit report)",
    "",
    f"**Generated (UTC)**: {summary['generated_utc']}",
    f"**Canonical source**: `{summary['canonical_source']}` ({len(canon)} hypotheses parsed)",
    "**Docs scanned**: " + ", ".join(f"`{d}`" for d in summary['docs_scanned']),
    "",
    "## Status counts (across all H-ID references)",
    "",
    "| Status | Count | Meaning |",
    "|---|---:|---|",
    f"| EXACT_MATCH | {status_counts.get('EXACT_MATCH', 0)} | Verdict string near H-ID matches the canonical token exactly |",
    f"| SAME_GROUP | {status_counts.get('SAME_GROUP', 0)} | Synonym in the same polarity group (e.g. PARTIAL ↔ SUGGESTIVE) — cosmetic drift |",
    f"| GROUP_MISMATCH | {status_counts.get('GROUP_MISMATCH', 0)} | **Semantic drift** — reviewer-fatal; patch required |",
    f"| NO_VERDICT_NEAR_HID | {status_counts.get('NO_VERDICT_NEAR_HID', 0)} | H-ID mentioned but no verdict string within ±500 chars |",
    "",
]

# Per-doc breakdown
md.append("## Per-doc breakdown")
md.append("")
md.append("| Doc | EXACT | SAME_GROUP | GROUP_MISMATCH | NO_VERDICT |")
md.append("|---|---:|---:|---:|---:|")
for d, c in per_doc_counts.items():
    md.append(
        f"| `{d}` | {c.get('EXACT_MATCH',0)} | {c.get('SAME_GROUP',0)} | "
        f"{c.get('GROUP_MISMATCH',0)} | {c.get('NO_VERDICT_NEAR_HID',0)} |"
    )
md.append("")

# Semantic drift — the priority-patch list
drifts = [r for r in scan_rows if r["match_status"] == "GROUP_MISMATCH"]
md.append(f"## Semantic drift (GROUP_MISMATCH) — {len(drifts)} cases — **patch required**")
md.append("")
if drifts:
    md.append("| # | Doc | Line | H-ID | Canonical | Found nearby | Context (truncated) |")
    md.append("|--:|---|---:|---|---|---|---|")
    for i, r in enumerate(drifts, 1):
        md.append(
            f"| {i} | `{r['doc']}` | {r['line']} | **{r['hypothesis_id']}** | "
            f"`{r['canon_verdict']}` ({r['canon_group']}) | "
            f"{', '.join(f'`{v}`' for v in r['found_verdicts_nearby']) or '—'} | "
            f"{r['context'][:200].replace('|',' ')} |"
        )
else:
    md.append("_None detected. All H-ID references either match exactly, "
              "match within the same polarity group, or have no verdict string nearby._")
md.append("")

# Same-group (cosmetic) drift — optional patch list
same_grp = [r for r in scan_rows if r["match_status"] == "SAME_GROUP"]
md.append(f"## Cosmetic drift (SAME_GROUP) — {len(same_grp)} cases — optional patch")
md.append("")
if same_grp and len(same_grp) <= 40:
    md.append("| # | Doc | Line | H-ID | Canonical | Synonym found |")
    md.append("|--:|---|---:|---|---|---|")
    for i, r in enumerate(same_grp, 1):
        md.append(
            f"| {i} | `{r['doc']}` | {r['line']} | {r['hypothesis_id']} | "
            f"`{r['canon_verdict']}` | "
            f"{', '.join(f'`{v}`' for v in r['found_verdicts_nearby'])} |"
        )
elif same_grp:
    md.append(f"_Showing first 30 of {len(same_grp)}. Full list in `scan_rows.json`._")
    md.append("")
    md.append("| # | Doc | Line | H-ID | Canonical | Synonym found |")
    md.append("|--:|---|---:|---|---|---|")
    for i, r in enumerate(same_grp[:30], 1):
        md.append(
            f"| {i} | `{r['doc']}` | {r['line']} | {r['hypothesis_id']} | "
            f"`{r['canon_verdict']}` | "
            f"{', '.join(f'`{v}`' for v in r['found_verdicts_nearby'])} |"
        )
else:
    md.append("_None detected._")
md.append("")

md.append("## Canonical verdict table (parsed from HYPOTHESES_AND_TESTS.md)")
md.append("")
md.append("| H-ID | Verdict | Group | Date |")
md.append("|---|---|---|---|")
for h_id, c in canon.items():
    md.append(f"| {h_id} | `{c['verdict_token']}` | {c['verdict_group']} | {c['date']} |")

(OUTDIR / "expE3_diff_report.md").write_text("\n".join(md), encoding="utf-8")

# ---- console summary ------------------------------------------------------
print(f"Canonical hypotheses parsed : {len(canon)}")
print(f"Docs scanned                : {len(TARGET_DOCS)}")
print(f"Total H-ID references found : {len(scan_rows)}")
for k, v in status_counts.items():
    print(f"  {k:>22s}: {v}")
print(f"\nReports:\n  - {OUTDIR / 'expE3_report.json'}")
print(f"  - {OUTDIR / 'scan_rows.json'}")
print(f"  - {OUTDIR / 'expE3_diff_report.md'}")
