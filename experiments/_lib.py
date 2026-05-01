"""
experiments/_lib.py
===================
Read-only helpers for the QSF experiments sandbox.

Guarantees (by construction):
  1. load_phase / load_integrity only READ. They verify SHA-256 against
     results/checkpoints/_manifest.json before returning data.
  2. safe_output_dir() refuses to create any path outside
     results/experiments/<exp_name>/.
  3. self_check_begin/end hashes every protected file; any drift raises
     IntegrityError and the experiment is flagged FAILED.

This module does not modify the main pipeline or the locked results.
"""

from __future__ import annotations

import hashlib
import json
import os
import pickle
import time
from pathlib import Path
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Paths (anchored relative to this file so it works regardless of cwd)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent          # .../Quran/experiments
_ROOT = _HERE.parent                              # .../Quran
_RESULTS = _ROOT / "results"
_CHECKPOINTS = _RESULTS / "checkpoints"
_INTEGRITY = _RESULTS / "integrity"
_EXPERIMENTS_OUT = _RESULTS / "experiments"

# Files and folders that MUST NOT be mutated mid-experiment.
# Order matters only for the printout; mutation of any of these *during* an
# experiment is a hard stop. Audit-fix F-8 extends the snapshot to the
# Ultimate-2 source files so a silent drift in the Python that produces the
# headline numbers is detected as well. Drift detection only — this list is
# NOT a write-lock; files may be edited between runs.
_PROTECTED_FILES = [
    _RESULTS / "ULTIMATE_REPORT.json",
    _RESULTS / "ULTIMATE_SCORECARD.md",
    _RESULTS / "CLEAN_PIPELINE_REPORT.json",
    _CHECKPOINTS / "_manifest.json",
    _INTEGRITY / "code_lock.json",
    _INTEGRITY / "corpus_lock.json",
    _INTEGRITY / "fdr_coverage_audit.json",
    _INTEGRITY / "headline_baselines.json",
    _INTEGRITY / "names_registry.json",
    _INTEGRITY / "preregistration.json",
    _INTEGRITY / "results_lock.json",
    _ROOT / "notebooks" / "ultimate" / "QSF_ULTIMATE.ipynb",
    # Ultimate-2 source files (audit-fix F-8).
    _ROOT / "notebooks" / "ultimate" / "QSF_ULTIMATE_2.ipynb",
    _ROOT / "notebooks" / "ultimate" / "_build_ultimate2.py",
    _ROOT / "experiments" / "ultimate2_pipeline.py",
    _ROOT / "experiments" / "_ultimate2_helpers.py",
    _ROOT / "experiments" / "exp09_R1_variant_forensics_9ch" / "run.py",
    # F11 fix 2026-04-29: feature extractors that drive every Quran-distinctiveness
    # claim must be drift-monitored alongside locked receipts and checkpoints.
    _ROOT / "src" / "features.py",
    _ROOT / "src" / "raw_loader.py",
    _ROOT / "scripts" / "_phi_universal_xtrad_sizing.py",
]
_PROTECTED_DIRS = [_CHECKPOINTS, _INTEGRITY, _RESULTS / "figures"]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class IntegrityError(RuntimeError):
    """A protected file or checkpoint no longer matches its pinned SHA-256."""


class SandboxViolation(RuntimeError):
    """Attempted to create/write outside results/experiments/."""


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------
def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Checkpoint manifest (cached on first read)
# ---------------------------------------------------------------------------
_MANIFEST_CACHE: Dict[str, Any] | None = None


def _manifest() -> Dict[str, Any]:
    global _MANIFEST_CACHE
    if _MANIFEST_CACHE is None:
        mpath = _CHECKPOINTS / "_manifest.json"
        if not mpath.exists():
            raise IntegrityError(f"Missing manifest: {mpath}")
        with open(mpath, "r", encoding="utf-8") as f:
            _MANIFEST_CACHE = json.load(f)
    return _MANIFEST_CACHE


# ---------------------------------------------------------------------------
# Read-only loaders
# ---------------------------------------------------------------------------
def list_phases() -> list[str]:
    """Return the sorted list of available checkpoint phase names
    (without the .pkl suffix)."""
    entries = _manifest().get("entries", {})
    return sorted(k[:-4] if k.endswith(".pkl") else k for k in entries)


def _warn_fingerprint_drift(fname: str, entry: dict) -> None:
    """Compare a checkpoint entry's fingerprint against the current lock files.
    Emits a loud warning if they diverge (stale checkpoint vs. new code/data).

    AUDIT FIX 2026-04-24: when env var ``QSF_STRICT_DRIFT=1``, drift is
    promoted from a warning to an ``IntegrityError`` so result-producing
    runs cannot silently mix stale-checkpoint + new-code state.

    F11 FIX 2026-04-29: default behaviour is now ``strict=True`` (drift
    raises ``IntegrityError``). Set env var ``QSF_RELAX_DRIFT=1`` to
    downgrade drift to a warning for exploratory / debugging runs.
    Setting ``QSF_STRICT_DRIFT=1`` is now redundant but still honoured.
    """
    import warnings
    fp = entry.get("fingerprint", {})
    if not fp:
        return
    cp_corpus = fp.get("corpus_sha", "")
    cp_code = fp.get("code_sha", "")
    relax = os.environ.get("QSF_RELAX_DRIFT", "").strip() in ("1", "true", "True", "yes", "YES")
    strict = not relax
    drifts: list[str] = []
    # Load current lock combined hashes
    cl_path = _INTEGRITY / "corpus_lock.json"
    kl_path = _INTEGRITY / "code_lock.json"
    try:
        if cl_path.exists():
            with open(cl_path, "r", encoding="utf-8") as f:
                cur_corpus = json.load(f).get("combined", "")
            if cp_corpus and cur_corpus and cp_corpus != cur_corpus:
                msg = (
                    f"[FINGERPRINT DRIFT] {fname}: checkpoint corpus_sha "
                    f"{cp_corpus[:12]}... != current corpus_lock combined "
                    f"{cur_corpus[:12]}...\n"
                    f"  This checkpoint was created under a different corpus state."
                )
                drifts.append(msg)
                if not strict:
                    warnings.warn(msg, stacklevel=3)
        if kl_path.exists():
            with open(kl_path, "r", encoding="utf-8") as f:
                cur_code = json.load(f).get("combined", "")
            if cp_code and cur_code and cp_code != cur_code:
                msg = (
                    f"[FINGERPRINT DRIFT] {fname}: checkpoint code_sha "
                    f"{cp_code[:12]}... != current code_lock combined "
                    f"{cur_code[:12]}...\n"
                    f"  This checkpoint was created under a different code state."
                )
                drifts.append(msg)
                if not strict:
                    warnings.warn(msg, stacklevel=3)
    except Exception:
        pass  # lock files unreadable — don't block the load
    if strict and drifts:
        raise IntegrityError(
            "Refusing to load drifted checkpoint (default-strict mode).\n  - "
            + "\n  - ".join(drifts)
            + "\n  Rebuild checkpoints under the current lock, or set "
              "QSF_RELAX_DRIFT=1 to downgrade to a warning for exploratory runs."
        )


def load_phase(name: str) -> Any:
    """Load a pipeline checkpoint by name, e.g. 'phase_06_phi_m'.

    Raises IntegrityError if the on-disk SHA-256 differs from the manifest.
    The pickle is opened in binary READ mode only; nothing is written back.
    """
    fname = name if name.endswith(".pkl") else f"{name}.pkl"
    path = _CHECKPOINTS / fname

    entries = _manifest().get("entries", {})
    if fname not in entries:
        raise FileNotFoundError(
            f"Unknown checkpoint '{fname}'. Available: {list_phases()}"
        )
    expected = entries[fname]["sha256"]

    if not path.exists():
        raise FileNotFoundError(f"Checkpoint missing on disk: {path}")

    actual = _sha256(path)
    if actual != expected:
        raise IntegrityError(
            f"Checkpoint SHA-256 mismatch for {fname}\n"
            f"  expected: {expected}\n"
            f"  actual:   {actual}\n"
            f"REFUSING TO LOAD. Do NOT proceed until you have restored the file."
        )

    # AUDIT FIX 2026-04-21: verify checkpoint fingerprint against current
    # corpus_lock / code_lock so stale-checkpoint + new-code mixing is flagged.
    _warn_fingerprint_drift(fname, entries[fname])

    with open(path, "rb") as f:
        return pickle.load(f)


def load_integrity(name: str) -> Any:
    """Load one of the JSON files in results/integrity/, read-only.

    Accepts names with or without the .json suffix. Returns the parsed JSON.
    """
    fname = name if name.endswith(".json") else f"{name}.json"
    path = _INTEGRITY / fname
    if not path.exists():
        raise FileNotFoundError(f"Not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Output guard
# ---------------------------------------------------------------------------
def safe_output_dir(exp_name: str) -> Path:
    """Return (and create if needed) results/experiments/<exp_name>/.

    Any path that resolves outside this tree raises SandboxViolation.
    """
    if not exp_name or "/" in exp_name or "\\" in exp_name or ".." in exp_name:
        raise SandboxViolation(
            f"Bad experiment name {exp_name!r}. "
            "Use a short slug like 'exp01_ftail'."
        )
    out = (_EXPERIMENTS_OUT / exp_name).resolve()
    try:
        out.relative_to(_EXPERIMENTS_OUT.resolve())
    except ValueError as e:
        raise SandboxViolation(
            f"Refusing to create {out}: outside results/experiments/."
        ) from e
    out.mkdir(parents=True, exist_ok=True)
    return out


# ---------------------------------------------------------------------------
# Self-check (pre / post experiment)
# ---------------------------------------------------------------------------
def _protected_file_hashes() -> Dict[str, str]:
    out: Dict[str, str] = {}
    for p in _PROTECTED_FILES:
        if p.exists():
            out[str(p.relative_to(_ROOT))] = _sha256(p)
    return out


def _protected_dir_hashes() -> Dict[str, Dict[str, str]]:
    """Hash every file inside every protected directory."""
    out: Dict[str, Dict[str, str]] = {}
    for d in _PROTECTED_DIRS:
        if not d.exists():
            continue
        sub: Dict[str, str] = {}
        for f in sorted(d.rglob("*")):
            if f.is_file():
                sub[str(f.relative_to(_ROOT))] = _sha256(f)
        out[str(d.relative_to(_ROOT))] = sub
    return out


def self_check_begin() -> Dict[str, Any]:
    """Snapshot hashes of every protected file + directory.

    Call this at the start of an experiment. Pass the result to
    self_check_end() at the very end to confirm nothing was mutated.
    """
    return {
        "ts_start": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "files": _protected_file_hashes(),
        "dirs": _protected_dir_hashes(),
    }


def self_check_end(pre: Dict[str, Any], exp_name: str | None = None) -> Dict[str, Any]:
    """Re-hash all protected files/dirs and compare against the pre-snapshot.

    Raises IntegrityError listing every mutated path. On success, optionally
    writes a JSON receipt under results/experiments/<exp_name>/self_check_*.json.
    """
    post = {
        "ts_end": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "files": _protected_file_hashes(),
        "dirs": _protected_dir_hashes(),
    }

    changed: list[str] = []

    for rel, h in pre["files"].items():
        if post["files"].get(rel) != h:
            changed.append(f"FILE {rel}")
    for rel in post["files"]:
        if rel not in pre["files"]:
            changed.append(f"NEW PROTECTED FILE APPEARED: {rel}")

    for d, sub in pre["dirs"].items():
        post_sub = post["dirs"].get(d, {})
        for rel, h in sub.items():
            if post_sub.get(rel) != h:
                changed.append(f"DIR {rel}")
        for rel in post_sub:
            if rel not in sub:
                changed.append(f"NEW FILE IN PROTECTED DIR: {rel}")

    receipt = {
        "ok": not changed,
        "changed": changed,
        "pre_ts": pre["ts_start"],
        "post_ts": post["ts_end"],
        "n_protected_files": len(pre["files"]),
        "n_protected_dir_files": sum(len(v) for v in pre["dirs"].values()),
    }

    if exp_name:
        out = safe_output_dir(exp_name)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        with open(out / f"self_check_{stamp}.json", "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2)

    if changed:
        raise IntegrityError(
            "Protected files/directories were mutated during this experiment:\n  - "
            + "\n  - ".join(changed)
        )
    return receipt


# ---------------------------------------------------------------------------
# Human-readable summary (run `python -m experiments._lib` to preview)
# ---------------------------------------------------------------------------
def _summary() -> str:
    lines = [
        "QSF experiments sandbox",
        f"  root           : {_ROOT}",
        f"  checkpoints    : {_CHECKPOINTS}",
        f"  integrity      : {_INTEGRITY}",
        f"  experiments out: {_EXPERIMENTS_OUT}",
        "",
        f"Available phases ({len(list_phases())}):",
    ]
    for p in list_phases():
        lines.append(f"  - {p}")
    lines.append("")
    lines.append(f"Protected files     : {len(_PROTECTED_FILES)}")
    lines.append(f"Protected directories: {len(_PROTECTED_DIRS)}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(_summary())
