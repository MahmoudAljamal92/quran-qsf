"""exp102_imitation_battery — score every available Arabic imitation against
the locked 5-D Phi_M classifier from expP7 / phase_06_phi_m.

Contract (PREREG.md, hash-locked at PREREG_HASH.txt):
- 5-D extractor: src.features.features_5d(verses, stops)
- Reference centroid + Sigma_inv: phase_06_phi_m.mu, phase_06_phi_m.S_inv
- Cluster threshold: tau_inside = 95th percentile of Phi_M over the locked
  114 Quran surahs under the same centroid + Sigma_inv.
- Imitations: every subdir of data/corpora/imitations/ (verses.json or text.txt).
- Verdict ladder: see PREREG.md section 2.3.

Run from repo root:
    python -m experiments.exp102_imitation_battery.run

Receipt:
    results/experiments/exp102_imitation_battery/exp102_imitation_battery.json
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

# UTF-8 stdout on Windows.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:  # pragma: no cover
        pass

# Make the repo root importable for `src.features` and `experiments._lib`.
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Locked PREREG hash (read once at module load; aborts on mismatch).
_PREREG_PATH = _HERE / "PREREG.md"
_PREREG_HASH_PATH = _HERE / "PREREG_HASH.txt"


def _sha256(p: Path) -> str | None:
    if not p.exists() or not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


_PREREG_EXPECTED_HASH = (
    _PREREG_HASH_PATH.read_text(encoding="utf-8").strip()
    if _PREREG_HASH_PATH.exists() else None
)


# --- Output paths -------------------------------------------------------

OUT_DIR = _ROOT / "results" / "experiments" / "exp102_imitation_battery"
OUT_PATH = OUT_DIR / "exp102_imitation_battery.json"
IMITATIONS_DIR = _ROOT / "data" / "corpora" / "imitations"


# --- Imitation loading --------------------------------------------------

def _load_imitation(subdir: Path) -> dict[str, Any]:
    """Load one imitation. Returns a dict with keys:
    - id              : subdir name
    - verses          : list[str]
    - n_verses        : int
    - source          : dict (from SOURCE.json) or empty
    - source_sha256   : sha256 of the raw verses.json or text.txt file
    - load_error      : str or None
    """
    out: dict[str, Any] = {
        "id": subdir.name,
        "verses": [],
        "n_verses": 0,
        "source": {},
        "source_sha256": None,
        "load_error": None,
    }
    src_json = subdir / "SOURCE.json"
    if src_json.exists():
        try:
            out["source"] = json.loads(src_json.read_text(encoding="utf-8"))
        except Exception as e:
            out["source"] = {"_error": str(e)}

    verses_json = subdir / "verses.json"
    text_txt = subdir / "text.txt"

    if verses_json.exists():
        try:
            data = json.loads(verses_json.read_text(encoding="utf-8"))
            out["source_sha256"] = _sha256(verses_json)
            # Two accepted shapes:
            #   {"verses": [...]}
            #   {"surahs": [{"label": "F:001", "verses": [...]}, ...]}
            if isinstance(data, dict) and "surahs" in data:
                vs: list[str] = []
                for s in data["surahs"]:
                    vs.extend(v.strip() for v in s.get("verses", []) if isinstance(v, str) and v.strip())
                out["verses"] = vs
            elif isinstance(data, dict) and "verses" in data:
                out["verses"] = [v.strip() for v in data["verses"] if isinstance(v, str) and v.strip()]
            elif isinstance(data, list):
                out["verses"] = [v.strip() for v in data if isinstance(v, str) and v.strip()]
            else:
                out["load_error"] = "unrecognised verses.json schema"
        except Exception as e:
            out["load_error"] = f"verses.json parse error: {e!r}"
    elif text_txt.exists():
        try:
            txt = text_txt.read_text(encoding="utf-8")
            out["source_sha256"] = _sha256(text_txt)
            # one verse per non-empty line
            out["verses"] = [ln.strip() for ln in txt.splitlines() if ln.strip()]
        except Exception as e:
            out["load_error"] = f"text.txt read error: {e!r}"
    else:
        out["load_error"] = "no verses.json or text.txt in subdir"

    out["n_verses"] = len(out["verses"])
    return out


# --- Phi_M helpers ------------------------------------------------------

def _phi_m_per_row(X: np.ndarray, mu: np.ndarray, S_inv: np.ndarray) -> np.ndarray:
    """Mahalanobis^2 of each row of X against mu under S_inv (squared distance)."""
    d = X - mu  # (n, d)
    return np.einsum("ij,jk,ik->i", d, S_inv, d)


# --- Verdict ladder (PREREG section 2.3) --------------------------------

def _apply_verdict_ladder(
    pipeline_ok: bool,
    n_imitations_loaded: int,
    per_imitation: list[dict[str, Any]],
    tau_inside: float,
) -> dict[str, Any]:
    if not pipeline_ok:
        return {"verdict": "BLOCKED_pipeline_dependency_missing", "branch": 1}
    if n_imitations_loaded == 0:
        return {"verdict": "BLOCKED_no_imitations_on_disk", "branch": 2}

    # Audit malformed imitations -- branch 3 fires only if EVERY scored
    # imitation is malformed; otherwise we proceed with the well-formed ones.
    well_formed = [r for r in per_imitation if r.get("scoring_ok")]
    malformed = [r for r in per_imitation if not r.get("scoring_ok")]
    if not well_formed:
        return {
            "verdict": "FAIL_audit_unit_invariant",
            "branch": 3,
            "n_malformed": len(malformed),
            "n_well_formed": 0,
        }

    # Branch 4 -- any imitation inside cluster
    inside = [
        r for r in well_formed
        if r["phi_m"] <= tau_inside and r["classifier_predicts_quran"]
    ]
    if inside:
        return {
            "verdict": "FAIL_imitation_inside_cluster",
            "branch": 4,
            "n_inside": len(inside),
            "inside_ids": [r["id"] for r in inside],
            "tau_inside": tau_inside,
        }

    # Branch 5 -- any imitation in the boundary band
    boundary = [
        r for r in well_formed
        if r["phi_m"] <= 2.0 * tau_inside
    ]
    if boundary:
        return {
            "verdict": "PARTIAL_imitation_borderline",
            "branch": 5,
            "n_boundary": len(boundary),
            "boundary_ids": [r["id"] for r in boundary],
            "tau_inside": tau_inside,
        }

    # Branch 6 -- all clear
    return {
        "verdict": "PASS_all_imitations_outside_cluster",
        "branch": 6,
        "n_well_formed": len(well_formed),
        "tau_inside": tau_inside,
    }


# --- Main ---------------------------------------------------------------

def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    started_at = _dt.datetime.now(_dt.timezone.utc).isoformat()

    # Audit: PREREG hash sentinel
    prereg_actual = _sha256(_PREREG_PATH)
    prereg_ok = (
        _PREREG_EXPECTED_HASH is not None
        and prereg_actual == _PREREG_EXPECTED_HASH
    )
    if not prereg_ok:
        # We still write a receipt so the failure is visible; no scoring runs.
        receipt = {
            "experiment": "exp102_imitation_battery",
            "schema_version": 1,
            "hypothesis_id": "H40",
            "prereg_document": str(_PREREG_PATH.relative_to(_ROOT)).replace("\\", "/"),
            "prereg_hash": prereg_actual,
            "prereg_hash_expected": _PREREG_EXPECTED_HASH,
            "audit_report": {
                "ok": False,
                "prereg_hash_sentinel": {"ok": False},
            },
            "verdict": "BLOCKED_prereg_hash_mismatch",
            "verdict_block": {"branch": 0, "verdict": "BLOCKED_prereg_hash_mismatch"},
            "completed_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        }
        OUT_PATH.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[exp102] PREREG hash mismatch -- wrote BLOCKED receipt to {OUT_PATH}")
        return 1

    # Audit: pipeline-import sentinel
    pipeline_ok = True
    pipeline_error: str | None = None
    try:
        from src.features import features_5d, derive_stopwords  # type: ignore
        from experiments._lib import load_phase  # type: ignore
    except Exception as e:
        pipeline_ok = False
        pipeline_error = repr(e)

    # Audit: load locked phase_06_phi_m for centroid + Sigma_inv + locked Quran X
    mu = None
    S_inv = None
    X_QURAN = None
    feat_cols: list[str] = []
    stops_set: set[str] = set()
    locked_load_error: str | None = None
    if pipeline_ok:
        try:
            phi = load_phase("phase_06_phi_m")
            s = phi["state"]
            mu = np.asarray(s["mu"], dtype=float)
            S_inv = np.asarray(s["S_inv"], dtype=float)
            X_QURAN = np.asarray(s["X_QURAN"], dtype=float)
            feat_cols = list(s.get("FEAT_COLS", ["EL", "VL_CV", "CN", "H_cond", "T"]))
            # Derive stops from the locked Quran corpus the same way exp89b/expP7 do.
            quran_corpus = s["CORPORA"]["quran"]
            all_verses: list[str] = []
            for u in quran_corpus:
                all_verses.extend(getattr(u, "verses", []))
            stops_set = derive_stopwords(all_verses, top_n=20)
        except Exception as e:
            pipeline_ok = False
            locked_load_error = repr(e)

    # Compute tau_inside (95th percentile of Phi_M over locked 114 Quran surahs).
    tau_inside = None
    quran_phi_m_stats: dict[str, float] = {}
    if pipeline_ok and X_QURAN is not None and mu is not None and S_inv is not None:
        quran_phi_m = _phi_m_per_row(X_QURAN, mu, S_inv)
        finite = quran_phi_m[np.isfinite(quran_phi_m)]
        if finite.size:
            tau_inside = float(np.quantile(finite, 0.95))
            quran_phi_m_stats = {
                "n": int(finite.size),
                "min": float(finite.min()),
                "median": float(np.median(finite)),
                "p95": tau_inside,
                "max": float(finite.max()),
            }

    # Walk imitations directory
    per_imitation: list[dict[str, Any]] = []
    if not IMITATIONS_DIR.exists():
        IMITATIONS_DIR.mkdir(parents=True, exist_ok=True)

    subdirs = sorted([p for p in IMITATIONS_DIR.iterdir() if p.is_dir()]) if IMITATIONS_DIR.exists() else []

    for sub in subdirs:
        rec = _load_imitation(sub)
        rec["scoring_ok"] = False
        if pipeline_ok and rec["n_verses"] >= 5 and not rec.get("load_error"):
            try:
                feats = features_5d(rec["verses"], stops_set)  # type: ignore
                feats_arr = np.asarray(feats, dtype=float).reshape(1, -1)
                phi_m_val = float(_phi_m_per_row(feats_arr, mu, S_inv)[0])  # type: ignore[arg-type]
                # Linear classifier prediction (sign of w . x + b > 0 -> quran class).
                # Loaded from expP7 receipt overall block.
                expp7_path = _ROOT / "results" / "experiments" / "expP7_phi_m_full_quran" / "expP7_phi_m_full_quran.json"
                w_arr = np.zeros(feats_arr.shape[1])
                b_val = 0.0
                if expp7_path.exists():
                    expp7 = json.loads(expp7_path.read_text(encoding="utf-8"))
                    w_loaded = expp7.get("overall", {}).get("w")
                    b_loaded = expp7.get("overall", {}).get("b")
                    if isinstance(w_loaded, (list, tuple)) and len(w_loaded) == feats_arr.shape[1]:
                        w_arr = np.asarray(w_loaded, dtype=float)
                    if isinstance(b_loaded, (int, float)):
                        b_val = float(b_loaded)
                score = float(feats_arr @ w_arr + b_val)
                # Sign convention from expP7: positive -> quran class.
                rec["features_5d"] = {feat_cols[i]: float(feats_arr[0, i]) for i in range(feats_arr.shape[1])}
                rec["phi_m"] = phi_m_val
                rec["classifier_score"] = score
                rec["classifier_predicts_quran"] = score > 0.0
                rec["scoring_ok"] = True
            except Exception as e:
                rec["scoring_error"] = repr(e)
        elif rec["n_verses"] < 5 and not rec.get("load_error"):
            rec["load_error"] = f"unit invariant fail: only {rec['n_verses']} verses (< 5 required)"
        # Don't dump the raw verses into the receipt (could be huge); keep summary only.
        rec.pop("verses", None)
        per_imitation.append(rec)

    n_loaded = sum(1 for r in per_imitation if r.get("scoring_ok"))

    audit_report = {
        "ok": prereg_ok and pipeline_ok and (tau_inside is not None or n_loaded == 0),
        "prereg_hash_sentinel": {"ok": prereg_ok, "actual": prereg_actual,
                                 "expected": _PREREG_EXPECTED_HASH},
        "pipeline_import_sentinel": {"ok": pipeline_ok, "error": pipeline_error,
                                     "locked_load_error": locked_load_error},
        "tau_inside_sanity": {
            "ok": bool(tau_inside is not None and np.isfinite(tau_inside)),
            "tau_inside": tau_inside,
            "quran_phi_m_stats": quran_phi_m_stats,
        },
    }

    verdict_block = _apply_verdict_ladder(
        pipeline_ok=pipeline_ok,
        n_imitations_loaded=n_loaded,
        per_imitation=per_imitation,
        tau_inside=tau_inside if tau_inside is not None else 0.0,
    )

    receipt = {
        "experiment": "exp102_imitation_battery",
        "schema_version": 1,
        "hypothesis_id": "H40",
        "prereg_document": str(_PREREG_PATH.relative_to(_ROOT)).replace("\\", "/"),
        "prereg_hash": prereg_actual,
        "prereg_hash_expected": _PREREG_EXPECTED_HASH,
        "frozen_constants": {
            "feat_cols": feat_cols,
            "stops_count": len(stops_set),
            "stops_sample": sorted(list(stops_set))[:20],
        },
        "imitations_dir": str(IMITATIONS_DIR.relative_to(_ROOT)).replace("\\", "/"),
        "n_imitation_subdirs": len(subdirs),
        "n_imitations_scored": n_loaded,
        "tau_inside_p95_quran": tau_inside,
        "quran_phi_m_stats": quran_phi_m_stats,
        "per_imitation": per_imitation,
        "audit_report": audit_report,
        "verdict_block": verdict_block,
        "verdict": verdict_block["verdict"],
        "started_at_utc": started_at,
        "completed_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }

    OUT_PATH.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")

    # Console summary
    print(f"# exp102_imitation_battery -- receipt at {OUT_PATH}")
    print(f"# Verdict          : {verdict_block['verdict']}  (branch {verdict_block.get('branch')})")
    print(f"# Pipeline OK      : {pipeline_ok}")
    if pipeline_error:
        print(f"# Pipeline error   : {pipeline_error}")
    if tau_inside is not None:
        print(f"# tau_inside (p95) : {tau_inside:.4f}")
        s = quran_phi_m_stats
        print(f"# Quran Phi_M stats: n={s.get('n')} min={s.get('min'):.4f} med={s.get('median'):.4f} p95={s.get('p95'):.4f} max={s.get('max'):.4f}")
    print(f"# Imitation subdirs: {len(subdirs)}")
    print(f"# Imitations scored: {n_loaded}")
    if per_imitation:
        for r in per_imitation:
            tag = "OK" if r.get("scoring_ok") else "SKIP"
            extra = ""
            if r.get("scoring_ok"):
                extra = f"phi_m={r['phi_m']:.3f} score={r['classifier_score']:+.3f} predicts_quran={r['classifier_predicts_quran']}"
            elif r.get("load_error"):
                extra = f"err={r['load_error']}"
            print(f"#   [{tag}] {r['id']:32s}  {extra}")

    return 0 if verdict_block["verdict"].startswith("PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
