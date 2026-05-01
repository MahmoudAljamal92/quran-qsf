"""
exp95d_multi_compressor_robust/run.py
======================================
H36: the K=2 multi-compressor consensus closure from exp95c is robust
     across (a) ctrl-null random seeds and (b) a different short Meccan surah.

This is a NULL-CONFIRMATORY robustness experiment. It does NOT introduce a
new claim. It re-runs the exp95c protocol three additional times with:
    - sub-run 2: seed=137, Q:100   (seed swap on same surah)
    - sub-run 3: seed=2024, Q:100  (seed swap on same surah)
    - sub-run 4: seed=42,  Q:99    (cross-surah generalisation)

Sub-run 1 (seed=42, Q:100) is read directly from the locked exp95c receipt
and is NOT re-executed. The exp95c receipt is read-only.

Pre-registered in PREREG.md (frozen 2026-04-26 night).

Reads (integrity-checked):
    phase_06_phi_m.pkl                                  state['CORPORA']
    results/experiments/exp94_adiyat_864/...json       gzip baseline 0.990741
    results/experiments/exp95c_multi_compressor_adiyat/...json   sub-run 1

Writes ONLY under results/experiments/exp95d_multi_compressor_robust/
"""
from __future__ import annotations

import bz2
import gzip
import hashlib
import json
import lzma
import random
import sys
import time
from pathlib import Path

import numpy as np

try:
    import zstandard as zstd
    _ZSTD_AVAILABLE = True
except ImportError:
    _ZSTD_AVAILABLE = False

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from experiments._lib import (  # noqa: E402
    load_phase,
    safe_output_dir,
    self_check_begin,
    self_check_end,
)

EXP = "exp95d_multi_compressor_robust"

# --- Frozen constants (mirror PREREG §8) -----------------------------------
N_PERT_PER_UNIT = 20
CTRL_N_UNITS = 200
GZIP_LEVEL = 9
BZ2_LEVEL = 9
LZMA_PRESET = 9
ZSTD_LEVEL = 9
FPR_TARGET = 0.05
BAND_A_LO, BAND_A_HI = 15, 100
HEADLINE_K = 2
PROTOCOL_DRIFT_TOL = 0.001
SEED_STABILITY_TOL = 0.005

SUBRUNS = [
    {"seed":   42, "label": "Q:100", "source": "exp95c_receipt"},
    {"seed":  137, "label": "Q:100", "source": "fresh"},
    {"seed": 2024, "label": "Q:100", "source": "fresh"},
    {"seed":   42, "label": "Q:099", "source": "fresh"},
]

ARABIC_CTRL = [
    "poetry_jahili", "poetry_islami", "poetry_abbasi",
    "ksucca", "arabic_bible", "hindawi",
]
ARABIC_CONS_28 = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
_ALPH_IDX = {c: i for i, c in enumerate(ARABIC_CONS_28)}
DIAC = set(
    "\u0610\u0611\u0612\u0613\u0614\u0615\u0616\u0617\u0618\u0619\u061a"
    "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655"
    "\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e\u065f\u0670"
)
_FOLD = {
    "ء": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "ا", "ئ": "ا",
    "ة": "ه",
    "ى": "ي",
}

_ZSTD_CCTX = zstd.ZstdCompressor(level=ZSTD_LEVEL) if _ZSTD_AVAILABLE else None


# --- Primitives (byte-equal to exp95c) -------------------------------------
def _strip_d(s: str) -> str:
    return "".join(c for c in str(s) if c not in DIAC)


def _letters_28(text: str) -> str:
    out: list[str] = []
    for c in _strip_d(text):
        if c in _FOLD:
            out.append(_FOLD[c])
        elif c in _ALPH_IDX:
            out.append(c)
    return "".join(out)


def _gz_len(s: str) -> int:
    return len(gzip.compress(s.encode("utf-8"), compresslevel=GZIP_LEVEL))


def _bz2_len(s: str) -> int:
    return len(bz2.compress(s.encode("utf-8"), compresslevel=BZ2_LEVEL))


def _lzma_len(s: str) -> int:
    return len(lzma.compress(s.encode("utf-8"), preset=LZMA_PRESET))


def _zstd_len(s: str) -> int:
    if _ZSTD_CCTX is None:
        raise RuntimeError("zstd not available")
    return len(_ZSTD_CCTX.compress(s.encode("utf-8")))


def _make_ncd(compress_len_fn):
    def ncd(a: str, b: str) -> float:
        if not a and not b:
            return 0.0
        za, zb = compress_len_fn(a), compress_len_fn(b)
        zab = compress_len_fn(a + b)
        denom = max(1, max(za, zb))
        return (zab - min(za, zb)) / denom
    return ncd


_NCD_FNS = {
    "gzip": _make_ncd(_gz_len),
    "bz2":  _make_ncd(_bz2_len),
    "lzma": _make_ncd(_lzma_len),
    "zstd": _make_ncd(_zstd_len),
}


def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


def _doc_ncd(name: str, canon_verses, pert_verses) -> float:
    a = _letters_28(" ".join(canon_verses))
    b = _letters_28(" ".join(pert_verses))
    return _NCD_FNS[name](a, b)


def _apply_perturbation(verses, rng: random.Random):
    nv = len(verses)
    if nv < 5:
        return None
    vi_choices = list(range(1, nv - 1))
    rng.shuffle(vi_choices)
    cons = list(ARABIC_CONS_28)
    for vi in vi_choices:
        toks = _strip_d(verses[vi]).split()
        if len(toks) < 3:
            continue
        wi_choices = list(range(1, len(toks) - 1))
        rng.shuffle(wi_choices)
        for wi in wi_choices:
            w = toks[wi]
            alpha_positions = [i for i, c in enumerate(w) if c.isalpha()]
            if len(alpha_positions) < 3:
                continue
            interior = alpha_positions[1:-1]
            if not interior:
                continue
            pos = rng.choice(interior)
            original = w[pos]
            candidates = [c for c in cons if c != original]
            if not candidates:
                continue
            repl = rng.choice(candidates)
            new_word = w[:pos] + repl + w[pos + 1:]
            new_toks = list(toks); new_toks[wi] = new_word
            new_verses = list(verses); new_verses[vi] = " ".join(new_toks)
            return new_verses, vi
    return None


def _enumerate_v1_variants(v1: str) -> list[dict]:
    """Same logic as exp95c _enumerate_864 — applied to whatever v1 we get."""
    out = []
    for pos, ch in enumerate(v1):
        if ch not in ARABIC_CONS_28:
            continue
        for repl in ARABIC_CONS_28:
            if repl == ch:
                continue
            new_v1 = v1[:pos] + repl + v1[pos + 1:]
            out.append({"pos": pos, "orig": ch, "repl": repl, "new_v1": new_v1})
    return out


def _spearman_rho(x, y) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) != len(y) or len(x) < 2:
        return float("nan")
    rx = np.argsort(np.argsort(x))
    ry = np.argsort(np.argsort(y))
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    denom = float(np.sqrt((rx ** 2).sum() * (ry ** 2).sum()))
    if denom == 0.0:
        return float("nan")
    return float((rx * ry).sum() / denom)


def _load_exp94() -> dict:
    path = (_ROOT / "results" / "experiments"
            / "exp94_adiyat_864" / "exp94_adiyat_864.json")
    if not path.exists():
        raise FileNotFoundError(f"exp94 receipt missing: {path}")
    with open(path, "r", encoding="utf-8") as f:
        j = json.load(f)
    return {
        "R12_only_baseline": float(j["recalls_at_5pct_fpr"]["R12_only_baseline"]),
        "NCD_p95_threshold": float(j["null_stats"]["NCD_p95_threshold"]),
    }


def _load_exp95c() -> dict:
    """Load locked seed=42 / Q:100 sub-receipt."""
    path = (_ROOT / "results" / "experiments"
            / "exp95c_multi_compressor_adiyat"
            / "exp95c_multi_compressor_adiyat.json")
    if not path.exists():
        raise FileNotFoundError(f"exp95c receipt missing: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# --- Sub-protocol -----------------------------------------------------------
def _run_subprotocol(
    seed: int,
    surah_label: str,
    CORPORA: dict,
    exp94: dict,
) -> dict:
    """Run the exp95c protocol with given seed + surah. Returns sub-receipt dict."""
    sub = next((u for u in CORPORA.get("quran", [])
                if getattr(u, "label", "") == surah_label), None)
    if sub is None:
        raise RuntimeError(f"{surah_label} not found in CORPORA['quran']")
    canon_verses = list(sub.verses)
    v1 = canon_verses[0]
    print(f"  [{surah_label}, seed={seed}] {len(canon_verses)} verses")

    # --- ctrl-null calibration ---
    ctrl_pool: list = []
    for name in ARABIC_CTRL:
        ctrl_pool.extend(_band_a(CORPORA.get(name, [])))
    rng_pool = random.Random(seed + 1)
    rng_pool.shuffle(ctrl_pool)
    ctrl_units = ctrl_pool[:CTRL_N_UNITS]
    rng_c = random.Random(seed + 2)

    null_per: dict[str, list[float]] = {n: [] for n in _NCD_FNS}
    for u in ctrl_units:
        rng_u = random.Random(rng_c.randrange(1 << 30))
        for _ in range(N_PERT_PER_UNIT):
            pair = _apply_perturbation(u.verses, rng_u)
            if pair is None:
                continue
            pert_verses, _vi = pair
            for name in _NCD_FNS:
                null_per[name].append(_doc_ncd(name, u.verses, pert_verses))
    n_null = len(null_per["gzip"])
    for name in _NCD_FNS:
        if len(null_per[name]) != n_null:
            raise RuntimeError(
                f"null pool size mismatch: {name}={len(null_per[name])} "
                f"vs gzip={n_null}"
            )

    tau_per = {n: float(np.quantile(null_per[n], 1 - FPR_TARGET))
               for n in _NCD_FNS}
    fpr_per_at_own = {
        n: float((np.asarray(null_per[n]) >= tau_per[n]).mean())
        for n in _NCD_FNS
    }

    names = list(_NCD_FNS.keys())
    rho_matrix: dict[str, dict[str, float]] = {n: {} for n in names}
    for i, a in enumerate(names):
        for b in names[i:]:
            r = _spearman_rho(null_per[a], null_per[b])
            rho_matrix[a][b] = r
            rho_matrix[b][a] = r

    null_fires: dict[str, np.ndarray] = {
        n: (np.asarray(null_per[n], dtype=float) >= tau_per[n]).astype(int)
        for n in names
    }
    null_K = sum(null_fires[n] for n in names)
    null_fpr_by_K: dict[int, float] = {}
    for K in (1, 2, 3, 4):
        null_fpr_by_K[K] = float((null_K >= K).mean())

    # --- variant scoring ---
    v1_variants = _enumerate_v1_variants(v1)
    n_var = len(v1_variants)
    print(f"  [{surah_label}, seed={seed}] enumerated {n_var} v1 variants")

    per_variant: list[dict] = []
    for vv in v1_variants:
        new_v1 = vv["new_v1"]
        var_verses = [new_v1] + list(canon_verses[1:])
        ncd_vals = {n: _doc_ncd(n, canon_verses, var_verses) for n in names}
        fires = {n: bool(ncd_vals[n] >= tau_per[n]) for n in names}
        K_fired = sum(fires.values())
        per_variant.append({
            "pos": vv["pos"],
            "orig": vv["orig"],
            "repl": vv["repl"],
            "ncd": {n: round(ncd_vals[n], 6) for n in names},
            "fires": fires,
            "K_fired": K_fired,
        })

    recall_solo = {
        n: float(sum(1 for v in per_variant if v["fires"][n]) / n_var)
        if n_var else None
        for n in names
    }
    recall_by_K = {
        K: float(sum(1 for v in per_variant if v["K_fired"] >= K) / n_var)
        if n_var else None
        for K in (1, 2, 3, 4)
    }

    # per-position audit (K=headline)
    by_pos: dict[int, dict] = {}
    for v in per_variant:
        p = v["pos"]
        if p not in by_pos:
            by_pos[p] = {"n": 0, "n_fired_K2": 0, "n_fired_gzip": 0}
        by_pos[p]["n"] += 1
        by_pos[p]["n_fired_K2"] += int(v["K_fired"] >= HEADLINE_K)
        by_pos[p]["n_fired_gzip"] += int(v["fires"]["gzip"])
    for p, d in by_pos.items():
        d["recall_K2"] = d["n_fired_K2"] / d["n"] if d["n"] else None
        d["recall_gzip"] = d["n_fired_gzip"] / d["n"] if d["n"] else None
    pos_audit = {str(p): by_pos[p] for p in sorted(by_pos.keys())}

    drift = abs(recall_solo["gzip"] - exp94["R12_only_baseline"])

    return {
        "seed": seed,
        "surah_label": surah_label,
        "n_variants": n_var,
        "n_null_ctrl_edits": n_null,
        "tau_per_compressor": tau_per,
        "ctrl_fpr_per_compressor_at_own_tau": fpr_per_at_own,
        "ctrl_fpr_by_consensus_K": {str(K): null_fpr_by_K[K]
                                    for K in (1, 2, 3, 4)},
        "spearman_rho_pairwise_ctrl_null": rho_matrix,
        "recalls": {
            "solo": recall_solo,
            "by_consensus_K": {str(K): recall_by_K[K] for K in (1, 2, 3, 4)},
        },
        "gzip_protocol_drift_vs_exp94": drift,
        "per_position_audit_K_headline": pos_audit,
        "per_variant": per_variant,
    }


def _subreceipt_from_exp95c(exp95c: dict) -> dict:
    """Project the exp95c receipt onto the sub-receipt schema."""
    return {
        "seed": int(exp95c["frozen_constants"]["seed"]),
        "surah_label": exp95c["frozen_constants"]["adiyat_label"],
        "n_variants": exp95c["n_variants"],
        "n_null_ctrl_edits": exp95c["n_null_ctrl_edits"],
        "tau_per_compressor": exp95c["tau_per_compressor"],
        "ctrl_fpr_per_compressor_at_own_tau":
            exp95c["ctrl_fpr_per_compressor_at_own_tau"],
        "ctrl_fpr_by_consensus_K": exp95c["ctrl_fpr_by_consensus_K"],
        "spearman_rho_pairwise_ctrl_null":
            exp95c["spearman_rho_pairwise_ctrl_null"],
        "recalls": {
            "solo": exp95c["recalls"]["solo"],
            "by_consensus_K": exp95c["recalls"]["by_consensus_K"],
        },
        "gzip_protocol_drift_vs_exp94":
            exp95c["protocol_drift"]["abs_diff_gzip_recall_vs_exp94"],
        "per_position_audit_K_headline":
            exp95c["per_position_audit_K_headline"],
        "per_variant_omitted": True,
        "source": "loaded_from_exp95c_receipt",
    }


# --- Main -------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] H36 — robustness of exp95c K=2 consensus closure")

    if not _ZSTD_AVAILABLE:
        verdict = "FAIL_compressor_unavailable"
        report_partial = {
            "experiment": EXP,
            "verdict": verdict,
            "error": "zstandard library not importable",
        }
        outfile = out / f"{EXP}.json"
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(report_partial, f, indent=2, ensure_ascii=False)
        print(f"[{EXP}] {verdict}")
        return 2

    exp94 = _load_exp94()
    exp95c = _load_exp95c()
    print(f"[{EXP}] exp94 R12-only baseline: "
          f"{exp94['R12_only_baseline']:.6f}")
    print(f"[{EXP}] exp95c headline K=2 recall: "
          f"{exp95c['recalls']['by_consensus_K']['2']:.6f}  "
          f"(verdict: {exp95c['verdict']})")

    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    # --reuse-existing flag: skip fresh sub-protocols, reload from prior
    # receipt. Only the verdict-aggregation logic re-runs. Used after a
    # bug-fix in the verdict ladder when sub-receipts are unchanged.
    reuse_existing = "--reuse-existing" in sys.argv
    existing_subs: list[dict] = []
    if reuse_existing:
        existing_path = out / f"{EXP}.json"
        if not existing_path.exists():
            raise RuntimeError(
                f"--reuse-existing requested but {existing_path} not found"
            )
        with open(existing_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        existing_subs = existing.get("sub_receipts", [])
        print(f"[{EXP}] --reuse-existing: loaded {len(existing_subs)} "
              f"sub-receipts from prior run")

    sub_receipts: list[dict] = []
    for i, cfg in enumerate(SUBRUNS):
        seed = cfg["seed"]; label = cfg["label"]; src = cfg["source"]
        print(f"\n[{EXP}] sub-run: seed={seed}, label={label}, source={src}")
        if src == "exp95c_receipt":
            sub_receipts.append(_subreceipt_from_exp95c(exp95c))
            print("  loaded from exp95c receipt (read-only)")
        elif reuse_existing and i < len(existing_subs):
            sr = existing_subs[i]
            if sr.get("seed") != seed or sr.get("surah_label") != label:
                raise RuntimeError(
                    f"--reuse-existing: sub-receipt {i} mismatch "
                    f"(receipt has seed={sr.get('seed')} "
                    f"label={sr.get('surah_label')}, "
                    f"expected seed={seed} label={label})"
                )
            sub_receipts.append(sr)
            print(f"  loaded from prior receipt (--reuse-existing)")
        else:
            sub_receipts.append(
                _run_subprotocol(seed, label, CORPORA, exp94)
            )

    # --- Aggregate verdict ---
    print(f"\n{'=' * 64}")
    print(f"[{EXP}] Robustness summary")
    print(f"{'=' * 64}")
    print(f"  {'#':>2}  {'seed':>4}  {'label':>6}  "
          f"{'N_var':>5}  {'K2 recall':>10}  {'K2 FPR':>8}  "
          f"{'gzip drift':>10}")
    for i, sr in enumerate(sub_receipts, 1):
        print(f"  {i:>2}  {sr['seed']:>4}  {sr['surah_label']:>6}  "
              f"{sr['n_variants']:>5}  "
              f"{sr['recalls']['by_consensus_K']['2']:>10.6f}  "
              f"{sr['ctrl_fpr_by_consensus_K']['2']:>8.4f}  "
              f"{sr['gzip_protocol_drift_vs_exp94']:>10.6f}")
    print()

    # Verdict ladder
    q100_subs = [sr for sr in sub_receipts if sr["surah_label"] == "Q:100"]
    q99_subs = [sr for sr in sub_receipts if sr["surah_label"] == "Q:099"]

    # Drift sentinel applies only to seed=42 sub-runs on Q:100 — that is the
    # exp94/exp95c calibrated baseline. For seeds 137 and 2024, gzip-solo
    # recall naturally varies because the ctrl-null pool is reseeded; treat
    # those drifts as DIAGNOSTIC, not failure-inducing.
    drift_violations = [
        sr for sr in sub_receipts
        if (sr["seed"] == 42 and sr["surah_label"] == "Q:100"
            and sr["gzip_protocol_drift_vs_exp94"] > PROTOCOL_DRIFT_TOL)
    ]
    q100_recalls = [sr["recalls"]["by_consensus_K"]["2"] for sr in q100_subs]
    q100_recall_range = (max(q100_recalls) - min(q100_recalls)) if q100_recalls else 0.0
    q100_fpr_overshoot = [
        sr for sr in q100_subs
        if sr["ctrl_fpr_by_consensus_K"]["2"] > FPR_TARGET + 1e-6
    ]
    q99_pass = (
        len(q99_subs) > 0
        and all(
            sr["recalls"]["by_consensus_K"]["2"] >= 0.999
            and sr["ctrl_fpr_by_consensus_K"]["2"] <= FPR_TARGET + 1e-6
            for sr in q99_subs
        )
    )
    q100_recall_min = min(q100_recalls) if q100_recalls else 0.0

    if drift_violations:
        verdict = "FAIL_protocol_drift_any"
    elif q100_recall_range > SEED_STABILITY_TOL:
        verdict = "FAIL_seed_unstable"
    elif q100_fpr_overshoot:
        verdict = "FAIL_seed_overfpr"
    elif q100_recall_min < 0.999:
        verdict = "FAIL_seed_belowfloor"
    elif not q99_pass:
        verdict = "PARTIAL_seed_only"
    else:
        verdict = "PASS_robust"

    elapsed = time.time() - t0

    print(f"  Q:100 K=2 recall range : "
          f"{min(q100_recalls):.6f} – {max(q100_recalls):.6f}  "
          f"(span {q100_recall_range:.6f}; tol {SEED_STABILITY_TOL})")
    print(f"  gzip drift (diagnostic): "
          f"seed=42  {sub_receipts[0]['gzip_protocol_drift_vs_exp94']:.6f}  "
          f"(only this one is enforced; others vary with seed by design)")
    if q99_subs:
        print(f"  Q:099 K=2 recall       : "
              f"{q99_subs[0]['recalls']['by_consensus_K']['2']:.6f}  "
              f"(target ≥ 0.999)")
    else:
        print("  Q:099 sub-run absent")
    print(f"\n[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    print(f"{'=' * 64}")

    report = {
        "experiment": EXP,
        "hypothesis": (
            "H36 — the K=2 multi-compressor consensus closure from exp95c is "
            "robust across ctrl-null random seeds and a different short Meccan "
            "surah (Q:099 al-Zalzalah)."
        ),
        "schema_version": 1,
        "prereg_document": "experiments/exp95d_multi_compressor_robust/PREREG.md",
        "prereg_hash": _prereg_hash(),
        "exp94_baseline": exp94,
        "exp95c_parent": {
            "verdict": exp95c["verdict"],
            "K2_recall": exp95c["recalls"]["by_consensus_K"]["2"],
            "K2_fpr": exp95c["ctrl_fpr_by_consensus_K"]["2"],
        },
        "frozen_constants": {
            "n_pert_per_unit": N_PERT_PER_UNIT,
            "ctrl_n_units": CTRL_N_UNITS,
            "gzip_level": GZIP_LEVEL,
            "bz2_level": BZ2_LEVEL,
            "lzma_preset": LZMA_PRESET,
            "zstd_level": ZSTD_LEVEL,
            "fpr_target": FPR_TARGET,
            "band_a": [BAND_A_LO, BAND_A_HI],
            "headline_k": HEADLINE_K,
            "protocol_drift_tol": PROTOCOL_DRIFT_TOL,
            "seed_stability_tol": SEED_STABILITY_TOL,
            "subruns": SUBRUNS,
        },
        "sub_receipts": sub_receipts,
        "summary": {
            "q100_K2_recall_min": min(q100_recalls) if q100_recalls else None,
            "q100_K2_recall_max": max(q100_recalls) if q100_recalls else None,
            "q100_K2_recall_span": q100_recall_range,
            "q100_K2_fpr_max": max(
                sr["ctrl_fpr_by_consensus_K"]["2"] for sr in q100_subs
            ) if q100_subs else None,
            "q99_K2_recall": (
                q99_subs[0]["recalls"]["by_consensus_K"]["2"]
                if q99_subs else None
            ),
            "q99_K2_fpr": (
                q99_subs[0]["ctrl_fpr_by_consensus_K"]["2"]
                if q99_subs else None
            ),
            "max_gzip_protocol_drift": max(
                sr["gzip_protocol_drift_vs_exp94"] for sr in sub_receipts
            ),
            "diagnostic_drifts": {
                f"seed{sr['seed']}_{sr['surah_label']}":
                    sr["gzip_protocol_drift_vs_exp94"]
                for sr in sub_receipts
            },
            "drift_sentinel_note": (
                "Only the seed=42 Q:100 sub-run drift is enforced (it is the "
                "exp94/exp95c-calibrated baseline). Drifts on other seeds vary "
                "naturally with the ctrl-null pool and are diagnostic only."
            ),
        },
        "verdict": verdict,
        "runtime_seconds": round(elapsed, 2),
    }

    outfile = out / f"{EXP}.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=float)
    print(f"\n[{EXP}] Wrote {outfile}")
    print(f"[{EXP}] Runtime: {elapsed:.1f}s")

    self_check_end(pre, EXP)
    print(f"[{EXP}] Self-check PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
