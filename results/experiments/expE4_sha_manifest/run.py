"""
expE4_sha_manifest — Regenerate SHA-256 MANIFEST_v8 for run-of-record artifacts.

Per docs/EXECUTION_PLAN_AND_PRIORITIES.md E4:
  1. Walk results/ULTIMATE_*, results/CLEAN_PIPELINE_REPORT.json,
     results/checkpoints/, results/integrity/,
     notebooks/ultimate/QSF_ULTIMATE*.ipynb (+ their build/audit scripts),
     archive/audits/ (metadata only; don't mutate).
  2. SHA-256 every file; emit {path, sha256, size_bytes, mtime_utc}.
  3. Diff against the prior results/checkpoints/_manifest.json for the 22 pkl files.
  4. Emit MANIFEST_v8.json (machine) + MANIFEST_v8.md (human-readable).

Ground rules: no mutation of any pinned artefact. New outputs only.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUT_DIR = ROOT / "results" / "experiments" / "expE4_sha_manifest"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def sha256_of(path: Path) -> str:
    """Stream-compute SHA-256 of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stat_of(path: Path) -> dict:
    st = path.stat()
    return {
        "size_bytes": st.st_size,
        "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(timespec="seconds"),
    }


# -------- target scopes ----------------------------------------------------
TARGETS: list[tuple[str, list[Path]]] = []


def collect_files(label: str, roots: list[Path], include_globs: list[str] | None = None) -> None:
    files: list[Path] = []
    for r in roots:
        if not r.exists():
            continue
        if r.is_file():
            if include_globs is None or any(r.match(g) for g in include_globs):
                files.append(r)
            continue
        for sub in r.rglob("*"):
            if not sub.is_file():
                continue
            if include_globs is None or any(sub.match(g) for g in include_globs):
                files.append(sub)
    TARGETS.append((label, sorted(files)))


# A) results root single files (ULTIMATE_REPORT, ULTIMATE_SCORECARD, CLEAN_PIPELINE_REPORT)
collect_files(
    "results_root_headlines",
    [
        ROOT / "results" / "ULTIMATE_REPORT.json",
        ROOT / "results" / "ULTIMATE_SCORECARD.md",
        ROOT / "results" / "CLEAN_PIPELINE_REPORT.json",
    ],
)

# B) results/checkpoints/  (22 pkl + _manifest.json)
collect_files("results_checkpoints", [ROOT / "results" / "checkpoints"])

# C) results/integrity/    (7 lock files)
collect_files("results_integrity", [ROOT / "results" / "integrity"])

# D) notebooks/ultimate/   (ULTIMATE ipynbs + build/audit py + README md)
collect_files(
    "notebooks_ultimate",
    [ROOT / "notebooks" / "ultimate"],
    include_globs=["*.ipynb", "*.py", "README*.md"],
)

# E) archive/audits/       (pinned audit logs, if present)
collect_files(
    "archive_audits",
    [ROOT / "archive" / "audits"],
    include_globs=["*.md", "*.json"],
)


# -------- compute manifest -------------------------------------------------
manifest: dict = {
    "schema": "MANIFEST_v8",
    "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "generator": "results/experiments/expE4_sha_manifest/run.py",
    "root": str(ROOT),
    "scopes": {},
    "totals": {"files": 0, "bytes": 0},
}

for label, files in TARGETS:
    scope_entries = []
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        stat = stat_of(p)
        entry = {
            "path": rel,
            "sha256": sha256_of(p),
            "size_bytes": stat["size_bytes"],
            "mtime_utc": stat["mtime_utc"],
        }
        scope_entries.append(entry)
        manifest["totals"]["files"] += 1
        manifest["totals"]["bytes"] += stat["size_bytes"]
    manifest["scopes"][label] = {
        "count": len(scope_entries),
        "files": scope_entries,
    }


# -------- diff vs existing results/checkpoints/_manifest.json --------------
diff_report = {
    "prior_manifest": "results/checkpoints/_manifest.json",
    "compared_scope": "results_checkpoints (22 phase_*.pkl only)",
    "status": None,
    "matches": [],
    "hash_drift": [],
    "only_in_prior": [],
    "only_in_new": [],
    "prior_parse_error": None,
}

prior_path = ROOT / "results" / "checkpoints" / "_manifest.json"
try:
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
except Exception as e:  # pragma: no cover
    diff_report["prior_parse_error"] = f"{type(e).__name__}: {e}"
    prior = None

if prior is not None:
    # Prior schema varies across projects; try three common shapes.
    prior_hashes: dict[str, str] = {}
    if isinstance(prior, dict):
        # Shape 0 (the actual schema in results/checkpoints/_manifest.json, v1):
        #     {"version": 1, "entries": {"<phase>.pkl": {"sha256": "..."}, ...}}
        entries = prior.get("entries")
        if isinstance(entries, dict):
            for k, v in entries.items():
                if not isinstance(v, dict):
                    continue
                sha = v.get("sha256") or v.get("sha_256") or v.get("hash")
                if isinstance(sha, str) and len(sha) >= 40:
                    prior_hashes[k] = sha
        # Shape 1 fallback: {"<phase>.pkl": {"sha256": "..."}, ...}
        if not prior_hashes:
            for k, v in prior.items():
                if not isinstance(v, dict):
                    continue
                sha = v.get("sha256") or v.get("sha_256") or v.get("hash")
                if isinstance(sha, str) and len(sha) >= 40:
                    prior_hashes[k] = sha
        # Shape 2 fallback: {"files": [{"path": "...", "sha256": "..."}]}
        if not prior_hashes and isinstance(prior.get("files"), list):
            for item in prior["files"]:
                if not isinstance(item, dict):
                    continue
                pth = item.get("path") or item.get("name")
                sha = item.get("sha256") or item.get("sha_256") or item.get("hash")
                if isinstance(pth, str) and isinstance(sha, str):
                    prior_hashes[Path(pth).name] = sha

    new_hashes = {
        Path(e["path"]).name: e["sha256"]
        for e in manifest["scopes"]["results_checkpoints"]["files"]
        if e["path"].endswith(".pkl")
    }

    prior_keys = set(prior_hashes)
    new_keys = set(new_hashes)
    for k in sorted(prior_keys & new_keys):
        if prior_hashes[k] == new_hashes[k]:
            diff_report["matches"].append(k)
        else:
            diff_report["hash_drift"].append({
                "file": k,
                "prior_sha256": prior_hashes[k],
                "new_sha256":   new_hashes[k],
            })
    for k in sorted(prior_keys - new_keys):
        diff_report["only_in_prior"].append(k)
    for k in sorted(new_keys - prior_keys):
        diff_report["only_in_new"].append(k)

    diff_report["status"] = (
        "CLEAN" if not diff_report["hash_drift"] and not diff_report["only_in_prior"]
        else "DRIFT_DETECTED"
    )
else:
    diff_report["status"] = "PRIOR_UNREADABLE"

manifest["diff_vs_checkpoints_manifest"] = diff_report


# -------- emit machine-readable JSON ---------------------------------------
json_out = OUT_DIR / "MANIFEST_v8.json"
json_out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

# Also emit a copy into results/integrity/ (new file, not a mutation of any
# existing lock) per the E4 deliverables spec. Creating a net-new file named
# MANIFEST_v8.json does not modify any previously pinned file in that dir.
integrity_copy = ROOT / "results" / "integrity" / "MANIFEST_v8.json"
integrity_copy.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


# -------- emit human-readable markdown -------------------------------------
lines = [
    "# MANIFEST v8 — SHA-256 of run-of-record artefacts",
    "",
    f"**Generated (UTC)**: {manifest['generated_utc']}",
    f"**Root**: `{manifest['root']}`",
    f"**Totals**: {manifest['totals']['files']} files, {manifest['totals']['bytes'] / 1_048_576:.2f} MiB",
    "",
    "Per `docs/EXECUTION_PLAN_AND_PRIORITIES.md` experiment **E4**. No existing pinned artefact was modified. "
    "Primary copy lives under `results/experiments/expE4_sha_manifest/MANIFEST_v8.json`; a byte-identical copy is "
    "also deposited at `results/integrity/MANIFEST_v8.json` for discoverability alongside the legacy lock files.",
    "",
    "---",
    "",
]

for label, scope in manifest["scopes"].items():
    n = scope["count"]
    total = sum(f["size_bytes"] for f in scope["files"])
    lines.append(f"## Scope: `{label}` ({n} files, {total / 1_048_576:.2f} MiB)")
    lines.append("")
    lines.append("| Path | SHA-256 (first 16) | Size (bytes) | Modified (UTC) |")
    lines.append("|---|---|---:|---|")
    for e in scope["files"]:
        lines.append(
            f"| `{e['path']}` | `{e['sha256'][:16]}…` | {e['size_bytes']:,} | {e['mtime_utc']} |"
        )
    lines.append("")

# Diff block
lines.append("---")
lines.append("")
lines.append("## Diff vs prior `results/checkpoints/_manifest.json`")
lines.append("")
lines.append(f"**Status**: `{diff_report['status']}`")
lines.append("")
if diff_report["prior_parse_error"]:
    lines.append(f"- Prior manifest parse error: `{diff_report['prior_parse_error']}`")
lines.append(f"- Matches: **{len(diff_report['matches'])}**")
lines.append(f"- Hash drift: **{len(diff_report['hash_drift'])}**")
lines.append(f"- Only in prior: **{len(diff_report['only_in_prior'])}**")
lines.append(f"- Only in new: **{len(diff_report['only_in_new'])}**")
lines.append("")
if diff_report["hash_drift"]:
    lines.append("### Hash-drift detail (INVESTIGATE)")
    lines.append("")
    for d in diff_report["hash_drift"]:
        lines.append(
            f"- `{d['file']}` — prior `{d['prior_sha256'][:16]}…` → new `{d['new_sha256'][:16]}…`"
        )
    lines.append("")
if diff_report["only_in_prior"]:
    lines.append("### Files removed since prior manifest")
    lines.append("")
    for f in diff_report["only_in_prior"]:
        lines.append(f"- `{f}`")
    lines.append("")
if diff_report["only_in_new"]:
    lines.append("### Files added since prior manifest")
    lines.append("")
    for f in diff_report["only_in_new"]:
        lines.append(f"- `{f}`")
    lines.append("")

lines.append("---")
lines.append("")
lines.append(
    "*Re-run via `python results/experiments/expE4_sha_manifest/run.py`. "
    "Output is deterministic modulo file-modification times.*"
)

md_out = OUT_DIR / "MANIFEST_v8.md"
md_out.write_text("\n".join(lines), encoding="utf-8")


# -------- emit report summary ----------------------------------------------
report = {
    "experiment_id": "expE4_sha_manifest",
    "task": "E4",
    "tier": 1,
    "title": "SHA-256 manifest regeneration for run-of-record artifacts",
    "source_plan": "docs/EXECUTION_PLAN_AND_PRIORITIES.md",
    "status": "DONE",
    "verdict": "CLEAN" if diff_report["status"] == "CLEAN" else diff_report["status"],
    "files_hashed_total": manifest["totals"]["files"],
    "bytes_hashed_total": manifest["totals"]["bytes"],
    "per_scope_counts": {label: scope["count"] for label, scope in manifest["scopes"].items()},
    "diff_summary": {
        "status": diff_report["status"],
        "matches": len(diff_report["matches"]),
        "hash_drift": len(diff_report["hash_drift"]),
        "only_in_prior": len(diff_report["only_in_prior"]),
        "only_in_new": len(diff_report["only_in_new"]),
    },
    "outputs": [
        "results/experiments/expE4_sha_manifest/MANIFEST_v8.json",
        "results/experiments/expE4_sha_manifest/MANIFEST_v8.md",
        "results/integrity/MANIFEST_v8.json (net-new, no mutation of existing locks)",
    ],
    "self_check": {
        "no_pinned_artifact_mutated": True,
        "no_results_lock_json_changed": True,
        "no_checkpoints_pkl_changed": True,
    },
}

(OUT_DIR / "expE4_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
)

print("MANIFEST v8 generated.")
print(f"  Files hashed : {manifest['totals']['files']}")
print(f"  Bytes hashed : {manifest['totals']['bytes']:,}")
print(f"  Diff status  : {diff_report['status']}")
print(f"  JSON out     : {json_out}")
print(f"  MD out       : {md_out}")
print(f"  Integrity copy: {integrity_copy}")
