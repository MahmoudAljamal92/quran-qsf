"""
arxiv_submission/build_osf_deposit.py
=====================================
Build the OSF v7.3 deposit packet.

Output:
    arxiv_submission/osf_deposit_v73/
        osf_deposit_manifest.json   -- SHA-256 of every deposited file
        qsf_v73_deposit.zip         -- single-file upload archive

No network calls. After running this script, upload qsf_v73_deposit.zip
and osf_deposit_manifest.json manually to osf.io as a new project or a
versioned storage entry. The manifest.json's 'overall_sha256' is the
one-line fingerprint to quote in any published reference.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import zipfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent

DEPOSIT_DIR = _HERE / "osf_deposit_v73"

# Files to include in the deposit (relative to _ROOT).
MANIFEST_ENTRIES = [
    # The addendum itself (post-hoc code-state lock)
    "arxiv_submission/preregistration_v73_addendum.md",
    # Canonical pre-registration (Ultimate-1)
    "results/integrity/preregistration.json",
    # Experiment source code (the locked versions)
    "experiments/_lib.py",
    "experiments/_ultimate2_helpers.py",
    "experiments/exp37_lpep/run.py",
    "experiments/exp38_ccas_normalised/run.py",
    "experiments/exp41_gzip_formalised/run.py",
    "experiments/exp41_gzip_formalised/length_audit.py",
    "experiments/exp43_adiyat_864_compound/run.py",
    "experiments/exp44_F6_spectrum/run.py",
    # Feature extractor (the code that produced every scalar)
    "src/features.py",
    "src/roots.py",
    "src/raw_loader.py",
    # Result JSONs from this session's five new tests
    "results/experiments/exp37_lpep/exp37_lpep.json",
    "results/experiments/exp38_ccas_normalised/exp38_ccas_normalised.json",
    "results/experiments/exp41_gzip_formalised/exp41_gzip_formalised.json",
    "results/experiments/exp41_gzip_formalised/length_audit.json",
    "results/experiments/exp43_adiyat_864_compound/exp43_adiyat_864_compound.json",
    "results/experiments/exp44_F6_spectrum/exp44_F6_spectrum.json",
    # Ultimate-1 locks for cross-reference (read-only)
    "results/integrity/results_lock.json",
    "results/integrity/corpus_lock.json",
    "results/integrity/code_lock.json",
    "results/checkpoints/_manifest.json",
    # Scoring tools (so external reviewers can score a text the same way)
    "tools/qsf_score.py",
    "tools/qsf_score_app.py",
    "tools/README.md",
]


def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _build_zip(entries: list[tuple[Path, str]], zpath: Path) -> None:
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for src, arcname in entries:
            z.write(src, arcname)


def main() -> int:
    DEPOSIT_DIR.mkdir(exist_ok=True)
    zpath = DEPOSIT_DIR / "qsf_v73_deposit.zip"
    manifest_path = DEPOSIT_DIR / "osf_deposit_manifest.json"

    entries: list[dict] = []
    zip_entries: list[tuple[Path, str]] = []

    total_bytes = 0
    missing: list[str] = []
    for rel in MANIFEST_ENTRIES:
        path = _ROOT / rel
        if not path.exists():
            missing.append(rel)
            continue
        sha = _sha256(path)
        size = path.stat().st_size
        total_bytes += size
        entries.append({
            "rel_path": rel,
            "sha256": sha,
            "size_bytes": size,
        })
        zip_entries.append((path, rel))

    if missing:
        # AUDIT FIX 2026-04-21: fail-closed on incomplete deposit.
        print(f"[FATAL] {len(missing)} files missing from deposit:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        print(
            "\nRefusing to build an incomplete deposit. Fix the missing files\n"
            "or remove them from MANIFEST_ENTRIES before building.",
            file=sys.stderr,
        )
        return 1

    _build_zip(zip_entries, zpath)

    # Hash the zip itself
    zip_sha = _sha256(zpath)

    # Overall fingerprint: sha-256 of the sorted concatenation of
    # (rel_path, sha256) pairs. This is the canonical one-line
    # fingerprint for external citation.
    concat = "\n".join(
        f"{e['rel_path']}|{e['sha256']}"
        for e in sorted(entries, key=lambda x: x["rel_path"])
    )
    overall_sha = hashlib.sha256(concat.encode("utf-8")).hexdigest()

    manifest = {
        "deposit_name": "QSF v7.3 Results-Lock Deposit (post-hoc code-state lock)",
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_files": len(entries),
        "total_bytes": total_bytes,
        "zip_file": zpath.name,
        "zip_sha256": zip_sha,
        "overall_sha256": overall_sha,
        "overall_sha256_purpose": (
            "One-line fingerprint of the deposit. Computed as "
            "SHA-256(sorted '<rel_path>|<sha256>' entries, "
            "newline-joined). Quote this in any external reference."
        ),
        "files": entries,
        "missing_files": missing,
        "osf_upload_instructions": [
            "1. Create an OSF project at osf.io (Public visibility).",
            "2. In that project's Storage tab, upload the two files "
            "below:",
            "     - qsf_v73_deposit.zip",
            "     - osf_deposit_manifest.json",
            "3. Tag the OSF project with: QSF, stylometry, Arabic, Quran, "
            "post-hoc-lock",
            "4. Record the generated OSF DOI; quote alongside the "
            "'overall_sha256' in any publication.",
            "5. Do NOT modify the files after upload. If a post-upload "
            "change is needed, version it as a new OSF storage entry.",
        ],
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[osf_deposit] wrote {zpath} ({zpath.stat().st_size} bytes)")
    print(f"[osf_deposit] wrote {manifest_path}")
    print(f"[osf_deposit] {len(entries)} files, {total_bytes:,} bytes total")
    print(f"[osf_deposit] overall_sha256 = {overall_sha}")
    print(f"[osf_deposit] zip_sha256     = {zip_sha}")
    if missing:
        print(f"[osf_deposit] WARNING: {len(missing)} files missing from tree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
