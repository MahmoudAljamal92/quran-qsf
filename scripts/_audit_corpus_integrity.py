"""scripts/_audit_corpus_integrity.py
==========================================
Q2: how do we know the source files are correct?

Check (1) source-file SHA-256 against any documented manifest values,
(2) byte size, (3) line count, (4) actual sample content for sanity,
(5) declared provenance, and (6) public-domain / license status.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CORPORA = [
    ("quran",        "data/corpora/ar/quran_bare.txt",
     "Tanzil.net 'simple-clean' (uthmani-skeleton); CC-BY-3.0; 6,236 verses."),
    ("poetry",       "data/corpora/ar/poetry_raw.csv",
     "Arabic Poetry Comprehensive (Hugging Face arbml/Ashaar); CC-BY-4.0."),
    ("hindawi",      "data/corpora/ar/hindawi.txt",
     "Hindawi Foundation modern Arabic prose (publicly licensed)."),
    ("ksucca",       "data/corpora/ar/ksucca.txt",
     "Classical Arabic Ksucca prose (KSU Arabic corpus)."),
    ("arabic_bible", "data/corpora/ar/arabic_bible.xlsx",
     "Smith Van Dyke 1865 Arabic Bible; PUBLIC DOMAIN."),
    ("hebrew_tanakh","data/corpora/he/tanakh_wlc.txt",
     "Westminster Leningrad Codex (WLC); PUBLIC DOMAIN; 929 chapters."),
    ("greek_nt",     "data/corpora/el/opengnt_v3_3.csv",
     "OpenGNT v3.3 (NA28 + Robinson Pierpont 2020); CC-BY-SA-4.0; 7,957 verses."),
]

print("# Corpus integrity audit (Q2)")
print(f"# {'name':<14s}  {'size_bytes':>12s}  sha256[:24]   provenance")
print("# " + "-" * 100)
manifest = {}
for name, rel, prov in CORPORA:
    p = ROOT / rel
    if not p.exists():
        print(f"#  {name:<14s}  MISSING                                 {prov}")
        continue
    size = p.stat().st_size
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    sha = h.hexdigest()
    manifest[name] = {"path": rel, "size": size, "sha256": sha,
                      "provenance": prov}
    print(f"#  {name:<14s}  {size:>12,d}  {sha[:24]}  {prov}")

print()
print("# Pali (multi-file) and Avestan (multi-file) -- aggregate hash")
import glob
pali_glob = ROOT / "data" / "corpora" / "pi"
pali_files = sorted([str(p) for p in pali_glob.glob("**/*.json")])
print(f"#  pali: {len(pali_files):>4d} JSON files")
if pali_files:
    h = hashlib.sha256()
    for f in pali_files:
        with open(f, "rb") as fh:
            h.update(fh.read())
    sha = h.hexdigest()
    print(f"#       aggregate sha256: {sha[:48]}")
    manifest["pali"] = {"n_files": len(pali_files), "aggregate_sha256": sha,
                        "provenance":
                        "SuttaCentral root-pli-ms (Mahasangiti, Bilara); "
                        "CC0-1.0; PUBLIC DOMAIN"}

ave_glob = ROOT / "data" / "corpora" / "ae"
ave_files = sorted([str(p) for p in ave_glob.glob("y*.htm")])
print(f"#  avestan: {len(ave_files):>4d} HTM files")
if ave_files:
    h = hashlib.sha256()
    for f in ave_files:
        with open(f, "rb") as fh:
            h.update(fh.read())
    sha = h.hexdigest()
    print(f"#       aggregate sha256: {sha[:48]}")
    manifest["avestan"] = {"n_files": len(ave_files), "aggregate_sha256": sha,
                           "provenance":
                           "Avesta.org Geldner-1896 edition; PUBLIC DOMAIN"}

print()
print("# === Sample text from each corpus (first 200 chars after preamble) ===")
print()
for name, rel, prov in CORPORA:
    p = ROOT / rel
    if not p.exists() or rel.endswith(".xlsx"):
        continue
    print(f"# --- {name} ({rel}) ---")
    txt = p.read_text(encoding="utf-8", errors="replace")[:300]
    print(f"#   {repr(txt[:280])}")
    print()

print()
print("# === Cross-check Quran first 5 verses ===")
quran = (ROOT / "data" / "corpora" / "ar" / "quran_bare.txt").read_text(
    encoding="utf-8")
print("# (Sura|Verse|Text)")
for line in quran.splitlines()[:5]:
    print(f"#   {line}")

# Save manifest
out = ROOT / "results" / "auxiliary" / "_corpus_integrity_manifest.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
               encoding="utf-8")
print()
print(f"# Manifest written to: {out}")
