"""exp109_phi_universal_xtrad/run.py
=====================================
H64: cross-tradition Quran-distinctiveness via universal-feature outlier
detection. Replicates the sizing diagnostic with PREREG-locked thresholds,
audit hooks, and a 10,000-permutation null on the rhyme-extremum claim.

Hash-locked PREREG: ../PREREG.md (sha-256 must match _PREREG_EXPECTED_HASH).

Decision rule (PREREG §3.3):
  PASS iff:
    (1) median(H_EL, quran)  ==  min over 11 corpora
    (2) median(p_max, quran) ==  max over 11 corpora
    (3) quran_h_el / next_lowest_h_el  < H_EL_MARGIN  = 0.5
    (4) quran_p_max / next_highest_p_max > P_MAX_MARGIN = 1.4
    AND
    (5) perm_p(p_max) < 5e-4   (Bonferroni-corrected at K=2)
    (6) perm_p(H_EL)  < 5e-4

Wall-time predicted: ~5-10 min (10,000 permutations on ~5,000 units).
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Re-use the sizing script's loaders and feature extractor (locked).
from scripts._phi_universal_xtrad_sizing import (  # noqa: E402
    _load_quran,
    _load_arabic_peers,
    _load_hebrew_tanakh,
    _load_greek_nt,
    _load_pali,
    _load_avestan,
    _features_universal,
    NORMALISERS,
)

EXP = "exp109_phi_universal_xtrad"

# ---- Live progress log -------------------------------------------------
_PROGRESS_LOG = _ROOT / "results" / "experiments" / EXP / "progress.log"
_PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
_progress_fh = open(_PROGRESS_LOG, "w", encoding="utf-8", buffering=1)


def _log(msg: str) -> None:
    print(msg, flush=True)
    _progress_fh.write(msg + "\n")
    _progress_fh.flush()


# ---- PREREG hash sentinel ----------------------------------------------
_PREREG_EXPECTED_HASH = (
    "d25d5dcad64932b147b5e4fee161092842d5338a4622f74dc9a711f788a481ef"
)


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _enforce_prereg_hash() -> str:
    actual = _prereg_hash()
    if actual != _PREREG_EXPECTED_HASH:
        raise RuntimeError(
            f"PREREG hash mismatch:\n"
            f"  expected: {_PREREG_EXPECTED_HASH}\n"
            f"  actual  : {actual}"
        )
    return actual


# ---- Frozen constants --------------------------------------------------
SEED = 42
N_PERMUTATIONS = 10000
PERM_ALPHA = 0.001
PERM_BONFERRONI_K = 2  # we test p_max AND H_EL
PERM_ALPHA_BONF = PERM_ALPHA / PERM_BONFERRONI_K  # 5e-4
H_EL_MARGIN = 0.5     # Quran H_EL must be < 0.5 * next-lowest
P_MAX_MARGIN = 1.4    # Quran p_max must be > 1.4 * next-highest

EXPECTED_CORPORA = [
    "quran", "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "hindawi", "ksucca", "arabic_bible",
    "hebrew_tanakh", "greek_nt", "pali", "avestan_yasna",
]


# ---- Loader dispatch ---------------------------------------------------
def _load_all_corpora() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    out["quran"] = _load_quran()
    arabic_peers = _load_arabic_peers()
    for name, units in arabic_peers.items():
        out[name] = units
    out["hebrew_tanakh"] = _load_hebrew_tanakh()
    out["greek_nt"] = _load_greek_nt()
    out["pali"] = _load_pali()
    out["avestan_yasna"] = _load_avestan()
    return out


def _corpus_byte_fingerprint(units: list[dict]) -> str:
    """Deterministic sha256 of a corpus's loaded content."""
    h = hashlib.sha256()
    for u in units:
        h.update(u.get("label", "").encode("utf-8"))
        h.update(b"\x00")
        for v in u.get("verses", []):
            h.update(v.encode("utf-8"))
            h.update(b"\n")
        h.update(b"||")
    return h.hexdigest()


# ---- Main driver -------------------------------------------------------
def main() -> int:
    _log(f"# {EXP} -- starting (cross-tradition Quran-rhyme-extremum, H64)")
    t_start = time.time()
    started_at_utc = datetime.now(timezone.utc).isoformat()
    actual_hash = _enforce_prereg_hash()
    _log(f"# PREREG hash OK: {actual_hash[:16]}...")

    audit: dict = {"ok": True, "checks": {}, "warnings": [], "errors": []}

    # ------------------------------------------------------------------
    # 1) Load all 11 corpora
    # ------------------------------------------------------------------
    _log("# Step 1: loading 11 corpora ...")
    corpora_raw = _load_all_corpora()
    n_units_by_corpus: dict[str, int] = {
        c: len(corpora_raw.get(c, [])) for c in EXPECTED_CORPORA
    }
    _log(f"#   units: {n_units_by_corpus}")
    audit["checks"]["n_units_per_corpus_loaded"] = n_units_by_corpus

    # A1+A2: corpus byte fingerprint (loader determinism)
    fingerprints = {
        c: _corpus_byte_fingerprint(corpora_raw.get(c, []))
        for c in EXPECTED_CORPORA
    }
    audit["checks"]["corpus_sha256"] = fingerprints
    _log(f"# Step 2: corpus byte fingerprints captured")

    # A6: hadith_bukhari quarantine check
    quarantine_ok = "hadith_bukhari" not in corpora_raw
    audit["checks"]["quarantine_ok"] = quarantine_ok
    if not quarantine_ok:
        audit["ok"] = False
        audit["errors"].append("quarantine_breach_hadith_bukhari_in_pool")
        _log("# FAIL: hadith_bukhari quarantine breached")

    # ------------------------------------------------------------------
    # 2) Compute features per unit per corpus
    # ------------------------------------------------------------------
    _log("# Step 3: extracting universal 5-D features per unit ...")
    feats_by_corpus: dict[str, list[dict]] = {}
    for name in EXPECTED_CORPORA:
        feats_by_corpus[name] = []
        for u in corpora_raw.get(name, []):
            try:
                f = _features_universal(u)
                feats_by_corpus[name].append(f)
            except Exception as e:
                _log(f"# WARN: {name}/{u.get('label')} feature extraction "
                     f"failed: {e}")
        _log(f"#   {name}: {len(feats_by_corpus[name])} units extracted")

    # ------------------------------------------------------------------
    # 3) Compute per-corpus medians
    # ------------------------------------------------------------------
    _log("# Step 4: computing per-corpus medians ...")
    feature_names = ["VL_CV", "p_max", "H_EL",
                     "bigram_distinct_ratio", "gzip_efficiency"]
    medians: dict[str, dict[str, float]] = {}
    for name in EXPECTED_CORPORA:
        m: dict[str, float] = {}
        fs = feats_by_corpus[name]
        for k in feature_names:
            vals = [f[k] for f in fs]
            m[k] = float(np.median(vals)) if vals else float("nan")
        m["n_units"] = len(fs)
        medians[name] = m
    audit["checks"]["medians"] = medians

    # Pretty-print the medians table
    _log("")
    _log("# === Per-corpus median feature vector ===")
    cols = ["corpus      ", "n_units"] + feature_names
    _log("# " + "  ".join(f"{c:>22s}" for c in cols))
    for name, m in medians.items():
        cells = [f"{name:<12s}", f"{m['n_units']:>5d}"]
        for k in feature_names:
            cells.append(f"{m[k]:>22.4f}")
        _log("# " + "  ".join(f"{c:>22s}" for c in cells))

    # ------------------------------------------------------------------
    # 4) A3: sizing-receipt parity
    # ------------------------------------------------------------------
    sizing_path = _ROOT / "results" / "auxiliary" / "_phi_universal_xtrad_sizing.json"
    sizing_parity_ok = True
    sizing_diff: dict[str, dict[str, float]] = {}
    if sizing_path.exists():
        sz = json.loads(sizing_path.read_text(encoding="utf-8"))
        sz_medians = sz.get("medians", {})
        for name, m in medians.items():
            sz_m = sz_medians.get(name, {})
            for k in feature_names:
                if k in sz_m:
                    diff = abs(m[k] - sz_m[k])
                    if diff > 1e-9:
                        sizing_parity_ok = False
                        sizing_diff.setdefault(name, {})[k] = diff
        audit["checks"]["sizing_parity_ok"] = sizing_parity_ok
        if not sizing_parity_ok:
            audit["warnings"].append(
                f"sizing_parity_drift: {sizing_diff}")
            _log(f"# WARN A3: sizing parity drift detected: {sizing_diff}")
        else:
            _log("# A3 sizing-receipt parity: OK (all medians match within 1e-9)")
    else:
        sizing_parity_ok = False
        audit["warnings"].append("sizing_receipt_missing")

    # ------------------------------------------------------------------
    # 5) Decision rule (locked)
    # ------------------------------------------------------------------
    _log("")
    _log("# Step 5: applying locked decision rule (PREREG §3.3) ...")

    quran_h_el = medians["quran"]["H_EL"]
    quran_p_max = medians["quran"]["p_max"]
    other_h_el = {c: medians[c]["H_EL"] for c in EXPECTED_CORPORA
                  if c != "quran"}
    other_p_max = {c: medians[c]["p_max"] for c in EXPECTED_CORPORA
                   if c != "quran"}
    next_lowest_h_el_corpus = min(other_h_el, key=lambda c: other_h_el[c])
    next_lowest_h_el_value = other_h_el[next_lowest_h_el_corpus]
    next_highest_p_max_corpus = max(other_p_max, key=lambda c: other_p_max[c])
    next_highest_p_max_value = other_p_max[next_highest_p_max_corpus]

    h_el_ratio = quran_h_el / next_lowest_h_el_value
    p_max_ratio = quran_p_max / next_highest_p_max_value

    quran_is_h_el_argmin = quran_h_el < next_lowest_h_el_value
    quran_is_p_max_argmax = quran_p_max > next_highest_p_max_value
    h_el_margin_ok = h_el_ratio < H_EL_MARGIN
    p_max_margin_ok = p_max_ratio > P_MAX_MARGIN

    audit["checks"]["quran_h_el"] = quran_h_el
    audit["checks"]["quran_p_max"] = quran_p_max
    audit["checks"]["next_lowest_h_el"] = {
        "corpus": next_lowest_h_el_corpus, "value": next_lowest_h_el_value
    }
    audit["checks"]["next_highest_p_max"] = {
        "corpus": next_highest_p_max_corpus, "value": next_highest_p_max_value
    }
    audit["checks"]["h_el_ratio"] = h_el_ratio
    audit["checks"]["p_max_ratio"] = p_max_ratio
    audit["checks"]["quran_is_h_el_argmin"] = quran_is_h_el_argmin
    audit["checks"]["quran_is_p_max_argmax"] = quran_is_p_max_argmax
    audit["checks"]["h_el_margin_ok"] = h_el_margin_ok
    audit["checks"]["p_max_margin_ok"] = p_max_margin_ok

    _log(f"#   quran H_EL  = {quran_h_el:.4f}  vs next-lowest "
         f"({next_lowest_h_el_corpus}) = {next_lowest_h_el_value:.4f}  "
         f"ratio = {h_el_ratio:.4f} (need < {H_EL_MARGIN})")
    _log(f"#   quran p_max = {quran_p_max:.4f}  vs next-highest "
         f"({next_highest_p_max_corpus}) = {next_highest_p_max_value:.4f}  "
         f"ratio = {p_max_ratio:.4f} (need > {P_MAX_MARGIN})")

    # ------------------------------------------------------------------
    # 6) A4: permutation null on Quran-as-extremum
    # ------------------------------------------------------------------
    _log("")
    _log(f"# Step 6: A4 permutation null ({N_PERMUTATIONS} perms, seed={SEED}) ...")
    rng = np.random.default_rng(SEED)

    # Pool all units' (H_EL, p_max) features with their corpus-of-origin label
    all_h_el: list[float] = []
    all_p_max: list[float] = []
    all_origin: list[str] = []
    for name in EXPECTED_CORPORA:
        for f in feats_by_corpus[name]:
            all_h_el.append(f["H_EL"])
            all_p_max.append(f["p_max"])
            all_origin.append(name)
    all_h_el_arr = np.array(all_h_el)
    all_p_max_arr = np.array(all_p_max)
    n_total = len(all_origin)
    sizes = [n_units_by_corpus[c] for c in EXPECTED_CORPORA]
    quran_idx = EXPECTED_CORPORA.index("quran")

    # Observed test statistics
    obs_quran_h_el_extreme = (h_el_margin_ok and quran_is_h_el_argmin)
    obs_quran_p_max_extreme = (p_max_margin_ok and quran_is_p_max_argmax)

    # Under the null, randomly assign each unit to one of the 11 "labels"
    # preserving sizes, then check whether the random Quran-labelled subset
    # achieves both extrema with the locked margins.
    n_h_el_passes = 0
    n_p_max_passes = 0
    perm_t0 = time.time()
    for it in range(N_PERMUTATIONS):
        perm = rng.permutation(n_total)
        # Slice into 11 groups by sizes
        offsets = np.cumsum([0] + sizes)
        # Assemble medians per fake-corpus
        h_el_meds = np.empty(11)
        p_max_meds = np.empty(11)
        for j in range(11):
            idx = perm[offsets[j]:offsets[j+1]]
            if len(idx) == 0:
                h_el_meds[j] = np.inf
                p_max_meds[j] = -np.inf
            else:
                h_el_meds[j] = np.median(all_h_el_arr[idx])
                p_max_meds[j] = np.median(all_p_max_arr[idx])
        fake_quran_h_el = h_el_meds[quran_idx]
        fake_quran_p_max = p_max_meds[quran_idx]
        fake_others_h_el = np.delete(h_el_meds, quran_idx)
        fake_others_p_max = np.delete(p_max_meds, quran_idx)
        fake_next_lowest_h_el = float(fake_others_h_el.min())
        fake_next_highest_p_max = float(fake_others_p_max.max())
        if fake_next_lowest_h_el > 0:
            fake_h_el_ratio = fake_quran_h_el / fake_next_lowest_h_el
        else:
            fake_h_el_ratio = np.inf
        if fake_next_highest_p_max > 0:
            fake_p_max_ratio = fake_quran_p_max / fake_next_highest_p_max
        else:
            fake_p_max_ratio = 0
        if (fake_quran_h_el < fake_next_lowest_h_el
                and fake_h_el_ratio < H_EL_MARGIN):
            n_h_el_passes += 1
        if (fake_quran_p_max > fake_next_highest_p_max
                and fake_p_max_ratio > P_MAX_MARGIN):
            n_p_max_passes += 1
        if (it + 1) % 1000 == 0:
            _log(f"#   permutation {it+1}/{N_PERMUTATIONS} "
                 f"({time.time()-perm_t0:.1f}s); "
                 f"H_EL passes={n_h_el_passes}, "
                 f"p_max passes={n_p_max_passes}")

    perm_p_h_el = n_h_el_passes / N_PERMUTATIONS
    perm_p_p_max = n_p_max_passes / N_PERMUTATIONS
    audit["checks"]["perm_p_h_el"] = perm_p_h_el
    audit["checks"]["perm_p_p_max"] = perm_p_p_max
    audit["checks"]["perm_alpha_bonferroni"] = PERM_ALPHA_BONF
    perm_h_el_ok = perm_p_h_el < PERM_ALPHA_BONF
    perm_p_max_ok = perm_p_p_max < PERM_ALPHA_BONF
    audit["checks"]["perm_h_el_ok"] = perm_h_el_ok
    audit["checks"]["perm_p_max_ok"] = perm_p_max_ok
    _log(f"#   perm_p (H_EL extremum)  = {perm_p_h_el:.6f}  "
         f"(need < {PERM_ALPHA_BONF})")
    _log(f"#   perm_p (p_max extremum) = {perm_p_p_max:.6f}  "
         f"(need < {PERM_ALPHA_BONF})")

    # ------------------------------------------------------------------
    # 7) Decide verdict
    # ------------------------------------------------------------------
    if not quarantine_ok:
        verdict = "FAIL_audit_quarantine_breach"
        verdict_reason = "hadith_bukhari accidentally included in pool."
    elif not sizing_parity_ok:
        verdict = "FAIL_audit_sizing_parity"
        verdict_reason = (f"sizing-receipt parity violated; medians drift "
                          f"by > 1e-9: {sizing_diff}")
    elif not quran_is_h_el_argmin:
        verdict = "FAIL_quran_not_h_el_argmin"
        verdict_reason = (f"Quran H_EL = {quran_h_el} is not strict argmin; "
                          f"next-lowest is {next_lowest_h_el_corpus} = "
                          f"{next_lowest_h_el_value}.")
    elif not quran_is_p_max_argmax:
        verdict = "FAIL_quran_not_p_max_argmax"
        verdict_reason = (f"Quran p_max = {quran_p_max} is not strict argmax; "
                          f"next-highest is {next_highest_p_max_corpus} = "
                          f"{next_highest_p_max_value}.")
    elif not h_el_margin_ok:
        verdict = "FAIL_h_el_margin_too_small"
        verdict_reason = (f"h_el_ratio = {h_el_ratio:.4f} >= "
                          f"{H_EL_MARGIN} (margin too small).")
    elif not p_max_margin_ok:
        verdict = "FAIL_p_max_margin_too_small"
        verdict_reason = (f"p_max_ratio = {p_max_ratio:.4f} <= "
                          f"{P_MAX_MARGIN} (margin too small).")
    elif not perm_h_el_ok:
        verdict = "FAIL_perm_null_above_alpha"
        verdict_reason = (f"perm_p(H_EL) = {perm_p_h_el:.6f} >= "
                          f"{PERM_ALPHA_BONF}.")
    elif not perm_p_max_ok:
        verdict = "FAIL_perm_null_above_alpha"
        verdict_reason = (f"perm_p(p_max) = {perm_p_p_max:.6f} >= "
                          f"{PERM_ALPHA_BONF}.")
    else:
        verdict = "PASS_quran_rhyme_extremum_cross_tradition"
        verdict_reason = (
            f"Quran is the rhyme extremum across 11 cross-tradition corpora: "
            f"H_EL = {quran_h_el:.4f} (lowest, {h_el_ratio:.3f}x next-lowest); "
            f"p_max = {quran_p_max:.4f} (highest, {p_max_ratio:.3f}x next-highest); "
            f"perm_p(H_EL) = {perm_p_h_el:.6f}, perm_p(p_max) = "
            f"{perm_p_p_max:.6f}; both < Bonferroni alpha {PERM_ALPHA_BONF}.")

    # ------------------------------------------------------------------
    # 8) Write receipt
    # ------------------------------------------------------------------
    completed_at = datetime.now(timezone.utc).isoformat()
    out_dir = _ROOT / "results" / "experiments" / EXP
    out_dir.mkdir(parents=True, exist_ok=True)
    receipt = {
        "experiment": EXP,
        "hypothesis_id": "H64",
        "hypothesis": (
            "Cross-tradition Quran-distinctiveness via universal 5-D "
            "structural feature space: Quran is rhyme-extremum across 11 "
            "corpora spanning 5 language families and 5 religious traditions."
        ),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "started_at_utc": started_at_utc,
        "completed_at_utc": completed_at,
        "wall_time_s": time.time() - t_start,
        "prereg_hash": actual_hash,
        "prereg_expected_hash": _PREREG_EXPECTED_HASH,
        "prereg_document": "experiments/exp109_phi_universal_xtrad/PREREG.md",
        "frozen_constants": {
            "SEED": SEED,
            "N_PERMUTATIONS": N_PERMUTATIONS,
            "PERM_ALPHA": PERM_ALPHA,
            "PERM_BONFERRONI_K": PERM_BONFERRONI_K,
            "PERM_ALPHA_BONF": PERM_ALPHA_BONF,
            "H_EL_MARGIN": H_EL_MARGIN,
            "P_MAX_MARGIN": P_MAX_MARGIN,
            "EXPECTED_CORPORA": EXPECTED_CORPORA,
            "FEATURE_NAMES": feature_names,
            "calibration_source":
                "frozen_thresholds_no_data_calibration",
        },
        "audit_report": audit,
        "pre_stage_diagnostic_receipt":
            "results/auxiliary/_phi_universal_xtrad_sizing.json",
    }
    out_path = out_dir / f"{EXP}.json"
    out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    _log("")
    _log(f"# VERDICT: {verdict}")
    _log(f"# Reason: {verdict_reason}")
    _log(f"# Receipt: {out_path}")
    _log(f"# Total wall-time: {time.time() - t_start:.1f}s")
    return 0 if verdict.startswith("PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
