r"""
Gem-scanner — systematic satellite-scan of every <5 MB file in given roots,
indexing finding-IDs / keyword hits and diffing them against the Ultimate
pipeline's `names_registry.json`.

Usage (PowerShell, from repo root):
    python -X utf8 scripts/gem_scanner.py `
        --root "C:\Users\mtj_2\OneDrive\Desktop\Quran" `
        --root "D:\backup" `
        --out  "results/lost_gems_index.json"

Outputs:
- results/lost_gems_index.json             # finding-ID -> [files, counts]
- results/lost_gems_keywords.json          # keyword   -> [files, counts]
- results/lost_gems_diff.md                # IDs present in scans but NOT
                                             blessed in ultimate/names_registry.json
- results/lost_gems_orphan_jsons.md        # json files that declare numeric
                                             findings (.*result.*, verdict,
                                             p_value, cohens_d) but whose
                                             filename is not referenced by
                                             the ultimate pipeline.

Does NOT execute anything dangerous; read-only + JSON/MD writes under
`results/`. Safe to run.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MAX_BYTES = 5 * 1024 * 1024                        # 5 MB
TEXTY_EXT = {".py", ".md", ".txt", ".json", ".csv", ".ipynb",
             ".html", ".tex", ".yml", ".yaml", ".toml"}
SKIP_DIR_NAMES = {"__pycache__", ".git", "node_modules", ".venv", "venv",
                  "env", ".mypy_cache", ".pytest_cache", ".ipynb_checkpoints"}

# Finding-ID grammar seen across the project:
#   D01-D28  S1-S5  T1-T31  G1-G5  L1-L7  E1-E3  F1-F8  C00xx  P1-P6
#   S10..S24 (old pipeline)  V7-V29 (older)
ID_RE = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"(?:"
    r"D(?:0[0-9]|1[0-9]|2[0-8])"                 # D01–D28
    r"|S(?:[1-9]|1[0-9]|2[0-4])"                 # S1–S24
    r"|T(?:[1-9]|[12][0-9]|3[0-5])"              # T1–T35
    r"|G[1-5]"                                    # G1–G5
    r"|L[1-7]"                                    # L1–L7
    r"|E[1-4]"                                    # E1–E4
    r"|F[1-8]"                                    # F1–F8
    r"|C0[0-3][0-9][0-9]"                         # C0002, C0267, ...
    r"|V(?:0?[9]|1[0-9]|2[0-9])"                  # V9–V29 (legacy versions)
    r"|P[1-6]"                                    # P1–P6 (phases / pillars)
    r")"
    r"(?![A-Za-z0-9_])"
)

# High-value topical keywords (lowercased match)
TOPIC_KWS = [
    # letter-level / variant-level detection
    "variant_forensics", "qira", "qiraat", "rasm", "harakat",
    "letter_swap", "letter swap", "letter-swap",
    "single-letter", "one letter", "character-level", "char-level",
    "char_lm", "character lm", "transformer lm", "byte-level",
    # cross-scale / propagation
    "cross_scale", "cross-scale", "vertical integration", "propagation",
    "sliding_window", "sliding window", "local window",
    # physical / information-theoretic laws
    "channel capacity", "error-detection", "error detection",
    "error correction", "transmission", "noisy channel",
    "berry-esseen", "berry esseen", "csiszar", "körner", "csiszár",
    "fisher information", "cramer-rao",
    # candidate laws
    "variational principle", "saturation law", "optimality law",
    "half-life law", "scaling law", "upper bound law",
    "unified law", "universal law", "master law",
    # spectral / topology
    "spectral radius", "spectral entropy", "eigenvalue",
    "persistent homology", "rqa", "recurrence", "hurst",
    "modularity", "louvain", "graph topology", "betweenness",
    # Phi / composite
    "phi_triple", "phi triple", "phi_m", "phi_plus", "phi+",
    "hotelling", "mahalanobis", "csiszár-körner",
    # semantic / acoustic
    "semantic_bridge", "acoustic bridge", "pitch", "maqam",
    "tajweed", "madd", "syllable",
    # adversarial / forgery
    "adversarial", "forgery", "el-aware", "markov forgery",
    "synthetic quran", "blind rejection",
    # symbolic / formula
    "symbolic regression", "pysr", "formula discovery",
    # cross-language
    "tanakh", "iliad", "septuagint", "hebrew bible", "greek nt",
    "cross-language", "cross language", "crosslang",
    # retracted / falsified
    "falsified", "retracted", "not reproduced", "dead finding",
    "law not confirmed",
]

# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------
def iter_files(roots: list[Path]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        if not root.exists():
            print(f"[warn] root does not exist: {root}", file=sys.stderr)
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # prune skip dirs in-place
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
            for f in filenames:
                p = Path(dirpath) / f
                try:
                    if p.suffix.lower() not in TEXTY_EXT:
                        continue
                    if p.stat().st_size > MAX_BYTES:
                        continue
                    out.append(p)
                except OSError:
                    continue
    return out


def read_text_safely(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def scan_one(p: Path, id_hits: dict, kw_hits: dict, numeric_findings: dict):
    txt = read_text_safely(p)
    if not txt:
        return
    lower = txt.lower()

    # ---- finding-IDs ----
    for m in ID_RE.finditer(txt):
        tok = m.group(0)
        id_hits[tok][str(p)] = id_hits[tok].get(str(p), 0) + 1

    # ---- topic keywords ----
    for kw in TOPIC_KWS:
        n = lower.count(kw)
        if n:
            kw_hits[kw][str(p)] = n

    # ---- json files: pull any numeric finding scalars out ----
    if p.suffix.lower() == ".json":
        try:
            data = json.loads(txt)
            if isinstance(data, dict):
                flat: dict[str, object] = {}
                _flatten(data, "", flat)
                useful = {
                    k: v for k, v in flat.items()
                    if any(tag in k.lower()
                           for tag in ("p_value", "pvalue", "cohens_d", "d_value",
                                       "verdict", "hotelling", "mahalanob",
                                       "phi", "separation", "auc", "rho", "r_squared",
                                       "ratio"))
                }
                if useful:
                    numeric_findings[str(p)] = useful
        except Exception:
            pass


def _flatten(obj, prefix, out):
    """flatten a nested dict/list into a dotted-key map of scalars"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            _flatten(v, f"{prefix}.{k}" if prefix else str(k), out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:10]):  # cap list exploration
            _flatten(v, f"{prefix}[{i}]", out)
    else:
        # keep scalars only, bounded
        if isinstance(obj, (int, float, str, bool)) and len(str(obj)) < 200:
            out[prefix] = obj


# ---------------------------------------------------------------------------
# Diff vs ultimate pipeline
# ---------------------------------------------------------------------------
def diff_vs_registry(id_hits, registry_path: Path) -> dict:
    try:
        registry = set(json.loads(registry_path.read_text(encoding="utf-8"))["names"])
    except Exception as exc:
        print(f"[warn] cannot read {registry_path}: {exc}", file=sys.stderr)
        return {}

    blessed_bases = {n.split("_")[0] for n in registry}

    return {
        tok: sorted(files)[:10]
        for tok, files in sorted(id_hits.items())
        if tok not in registry and tok.split("_")[0] not in blessed_bases
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", action="append", required=True,
                    help="Root directory to scan (repeatable).")
    ap.add_argument("--registry",
                    default="results/integrity/names_registry.json",
                    help="Ultimate-pipeline names registry for diffing.")
    ap.add_argument("--out",
                    default="results/lost_gems_index.json",
                    help="Main output JSON (index of finding IDs).")
    args = ap.parse_args()

    roots = [Path(r).resolve() for r in args.root]
    print(f"[scan] {len(roots)} root(s):")
    for r in roots:
        print(f"        {r}")

    files = iter_files(roots)
    print(f"[scan] {len(files):,} eligible text files (<5 MB).")

    id_hits: dict[str, dict[str, int]] = defaultdict(dict)
    kw_hits: dict[str, dict[str, int]] = defaultdict(dict)
    numeric_findings: dict[str, dict] = {}

    for i, p in enumerate(files, 1):
        scan_one(p, id_hits, kw_hits, numeric_findings)
        if i % 500 == 0:
            print(f"        {i:,}/{len(files):,}")

    out_main = Path(args.out).resolve()
    out_main.parent.mkdir(parents=True, exist_ok=True)

    out_main.write_text(json.dumps(
        {k: v for k, v in sorted(id_hits.items())}, indent=2, ensure_ascii=False),
        encoding="utf-8")

    kw_path = out_main.with_name("lost_gems_keywords.json")
    kw_path.write_text(json.dumps(
        {k: v for k, v in sorted(kw_hits.items())}, indent=2, ensure_ascii=False),
        encoding="utf-8")

    num_path = out_main.with_name("lost_gems_orphan_jsons.json")
    num_path.write_text(json.dumps(numeric_findings, indent=2, ensure_ascii=False),
                        encoding="utf-8")

    # diff against registry
    diff = diff_vs_registry(id_hits, Path(args.registry))
    diff_md = out_main.with_name("lost_gems_diff.md")
    lines = ["# Lost-gem finding-IDs NOT blessed in the Ultimate pipeline",
             f"(diffed against `{args.registry}`; {len(diff)} unique IDs)\n"]
    for tok, files_list in diff.items():
        lines.append(f"## `{tok}` — {len(id_hits[tok])} file(s)")
        for f in files_list:
            lines.append(f"  - {f}")
        lines.append("")
    diff_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"[done] wrote {out_main}")
    print(f"[done] wrote {kw_path}")
    print(f"[done] wrote {num_path}")
    print(f"[done] wrote {diff_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
