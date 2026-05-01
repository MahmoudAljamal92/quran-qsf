"""
exp95c_multi_compressor_adiyat/run.py
=====================================
H35: multi-compressor consensus NCD lifts the Adiyat-864 ceiling above
0.999 without violating FPR.

Replicates the exp94_adiyat_864 protocol with one change:
  - Replace gzip-only NCD with 4 parallel NCDs across {gzip, bz2, lzma,
    zstd}, each with its own independent ctrl-p95 threshold.
  - Variant fires at consensus rule K if ≥ K of 4 compressors flag it.
  - Headline verdict uses K=2; K∈{1,3,4} reported as diagnostics.

Pre-registered in PREREG.md (frozen 2026-04-26 night).

Reads (integrity-checked):
    phase_06_phi_m.pkl                                state['CORPORA']
    results/experiments/exp94_adiyat_864/...json     R12-only baseline (0.990741)

Writes ONLY under results/experiments/exp95c_multi_compressor_adiyat/
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

EXP = "exp95c_multi_compressor_adiyat"

# --- Frozen constants (mirror PREREG §8) -----------------------------------
SEED = 42
N_PERT_PER_UNIT = 20
CTRL_N_UNITS = 200
GZIP_LEVEL = 9
BZ2_LEVEL = 9
LZMA_PRESET = 9
ZSTD_LEVEL = 9
FPR_TARGET = 0.05
BAND_A_LO, BAND_A_HI = 15, 100
ADIYAT_LABEL = "Q:100"
EXPECTED_N_VARIANTS = 864
HEADLINE_K = 2
PROTOCOL_DRIFT_TOL = 0.001

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

# zstd compressor (re-used; shared across calls is safe)
_ZSTD_CCTX = zstd.ZstdCompressor(level=ZSTD_LEVEL) if _ZSTD_AVAILABLE else None


# --- Primitives (byte-equal to exp41 / exp43 / exp94 / exp95) --------------
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


# --- Perturbation that returns vi (byte-equal to exp94) --------------------
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


# --- 864 enumeration (byte-equal to exp43 / exp94 / exp95) -----------------
def _enumerate_864(v1: str) -> list[dict]:
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


# --- Receipt loader --------------------------------------------------------
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


def _prereg_hash() -> str:
    p = _HERE / "PREREG.md"
    if not p.exists():
        return "PREREG_MD_MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _spearman_rho(x, y) -> float:
    """Spearman rank correlation. Returns nan if inputs are degenerate."""
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


# --- Main ------------------------------------------------------------------
def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out = safe_output_dir(EXP)
    pre = self_check_begin()
    t0 = time.time()

    print(f"[{EXP}] H35 — multi-compressor consensus NCD on Adiyat-864")
    print(f"[{EXP}] Compressors: gzip-{GZIP_LEVEL}, bz2-{BZ2_LEVEL}, "
          f"lzma-preset-{LZMA_PRESET}, zstd-{ZSTD_LEVEL}")

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
        print(f"[{EXP}] {verdict}: install with `pip install zstandard`")
        return 2

    exp94 = _load_exp94()
    print(f"[{EXP}] exp94 R12-only baseline: "
          f"{exp94['R12_only_baseline']:.6f}")

    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    adiyat = next((u for u in CORPORA.get("quran", [])
                   if getattr(u, "label", "") == ADIYAT_LABEL), None)
    if adiyat is None:
        raise RuntimeError(f"{ADIYAT_LABEL} not found in CORPORA['quran']")
    canon_verses = list(adiyat.verses)
    v1 = canon_verses[0]
    print(f"[{EXP}] Canonical Q:100 has {len(canon_verses)} verses")

    # --- Step 1: 4-compressor null calibration ---
    print(f"[{EXP}] Step 1: {CTRL_N_UNITS} ctrl units × {N_PERT_PER_UNIT} edits "
          f"× 4 compressors ...")
    ctrl_pool: list = []
    for name in ARABIC_CTRL:
        ctrl_pool.extend(_band_a(CORPORA.get(name, [])))
    rng_pool = random.Random(SEED + 1)
    rng_pool.shuffle(ctrl_pool)
    ctrl_units = ctrl_pool[:CTRL_N_UNITS]
    rng_c = random.Random(SEED + 2)

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
    print(f"[{EXP}] Null pool: n={n_null} per compressor")
    for name in _NCD_FNS:
        if len(null_per[name]) != n_null:
            raise RuntimeError(
                f"null pool size mismatch: {name}={len(null_per[name])} "
                f"vs gzip={n_null}"
            )

    # Per-compressor ctrl-p95 thresholds
    tau_per = {n: float(np.quantile(null_per[n], 1 - FPR_TARGET))
               for n in _NCD_FNS}
    fpr_per_at_own = {
        n: float((np.asarray(null_per[n]) >= tau_per[n]).mean())
        for n in _NCD_FNS
    }

    print(f"[{EXP}]   τ thresholds (ctrl-p95 per compressor):")
    for n in _NCD_FNS:
        print(f"[{EXP}]     {n:>5}: τ = {tau_per[n]:.6f}  "
              f"ctrl FPR at own τ = {fpr_per_at_own[n]:.4f}")

    # Sanity: gzip τ should reproduce exp94 NCD_p95_threshold ≈ 0.0496
    gzip_tau_drift = abs(tau_per["gzip"] - exp94["NCD_p95_threshold"])

    # --- Pairwise correlation audit (Step 5) ---
    print(f"[{EXP}] Pairwise Spearman rank correlations (ctrl null):")
    names = list(_NCD_FNS.keys())
    rho_matrix: dict[str, dict[str, float]] = {n: {} for n in names}
    for i, a in enumerate(names):
        for b in names[i:]:
            r = _spearman_rho(null_per[a], null_per[b])
            rho_matrix[a][b] = r
            rho_matrix[b][a] = r
            if a != b:
                print(f"[{EXP}]     ρ({a:>5}, {b:>5}) = {r:+.4f}")

    # Per-compressor ctrl null fires at own τ (vector); plus 4-compressor
    # consensus FPR for K∈{1,2,3,4}.
    null_fires: dict[str, np.ndarray] = {
        n: (np.asarray(null_per[n], dtype=float) >= tau_per[n]).astype(int)
        for n in names
    }
    null_K = sum(null_fires[n] for n in names)  # int per ctrl edit
    null_fpr_by_K: dict[int, float] = {}
    for K in (1, 2, 3, 4):
        null_fpr_by_K[K] = float((null_K >= K).mean())

    print(f"[{EXP}] Ctrl-null consensus FPR by K:")
    for K in (1, 2, 3, 4):
        print(f"[{EXP}]     K={K}: FPR = {null_fpr_by_K[K]:.4f}")

    # --- Step 2: Adiyat-864 scoring ---
    print(f"[{EXP}] Step 2: enumerating Adiyat 864 variants ...")
    v1_variants = _enumerate_864(v1)
    n_var = len(v1_variants)
    print(f"[{EXP}] Enumerated {n_var} variants (expected {EXPECTED_N_VARIANTS})")

    per_variant: list[dict] = []
    adiyat_per_compressor_ncd: dict[str, list[float]] = {n: [] for n in names}
    for vv in v1_variants:
        new_v1 = vv["new_v1"]
        var_verses = [new_v1] + list(canon_verses[1:])
        ncd_vals = {n: _doc_ncd(n, canon_verses, var_verses) for n in names}
        fires = {n: bool(ncd_vals[n] >= tau_per[n]) for n in names}
        K_fired = sum(fires.values())
        for n in names:
            adiyat_per_compressor_ncd[n].append(ncd_vals[n])
        per_variant.append({
            "pos": vv["pos"],
            "orig": vv["orig"],
            "repl": vv["repl"],
            "ncd": {n: round(ncd_vals[n], 6) for n in names},
            "fires": fires,
            "K_fired": K_fired,
        })

    # --- Step 3: consensus recalls ---
    recall_solo = {
        n: float(sum(1 for v in per_variant if v["fires"][n]) / n_var)
        for n in names
    }
    recall_by_K = {
        K: float(sum(1 for v in per_variant if v["K_fired"] >= K) / n_var)
        for K in (1, 2, 3, 4)
    }

    # --- Step 4: per-position audit (for the headline K=2 rule) ---
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

    # --- Protocol drift (gzip solo vs exp94 baseline) ---
    drift = abs(recall_solo["gzip"] - exp94["R12_only_baseline"])
    protocol_ok = drift <= PROTOCOL_DRIFT_TOL

    # --- Verdict ---
    if not protocol_ok:
        verdict = "FAIL_protocol_drift"
    elif null_fpr_by_K[HEADLINE_K] > FPR_TARGET + 1e-6:
        verdict = "FAIL_consensus_overfpr"
    elif recall_by_K[HEADLINE_K] <= exp94["R12_only_baseline"]:
        verdict = "FAIL_consensus_no_lift"
    elif recall_by_K[HEADLINE_K] >= 0.9999:
        verdict = "PASS_consensus_100"
    elif recall_by_K[HEADLINE_K] >= 0.999:
        verdict = "PASS_consensus_999"
    else:
        verdict = "PARTIAL_consensus_lifts_below_999"

    elapsed = time.time() - t0

    print(f"\n{'=' * 64}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    print(f"  exp94 baseline (gzip)  : {exp94['R12_only_baseline']:.6f}")
    print(f"  gzip protocol drift    : {drift:.6f}  (tol {PROTOCOL_DRIFT_TOL})")
    print(f"\n  Per-compressor SOLO recall:")
    for n in names:
        print(f"      {n:>5}: recall = {recall_solo[n]:.6f}  "
              f"(τ {tau_per[n]:.6f})")
    print(f"\n  Consensus recall by K (K=2 is headline):")
    for K in (1, 2, 3, 4):
        marker = "  <-- headline" if K == HEADLINE_K else ""
        print(f"      K={K}: recall = {recall_by_K[K]:.6f}  "
              f"FPR = {null_fpr_by_K[K]:.4f}{marker}")
    print(f"{'=' * 64}")

    # Top-8 weakest positions under K=2
    positions_sorted = sorted(
        pos_audit.items(),
        key=lambda kv: kv[1].get("recall_K2", 1.0) or 1.0
    )
    print(f"\n[{EXP}] Top-8 weakest positions (by K={HEADLINE_K} recall):")
    for p, d in positions_sorted[:8]:
        print(f"    pos {p:>2}  n={d['n']:>2}  "
              f"recall_K2={d['recall_K2']:.4f}  "
              f"recall_gzip={d['recall_gzip']:.4f}")

    report = {
        "experiment": EXP,
        "hypothesis": (
            "H35 — multi-compressor consensus NCD across {gzip, bz2, lzma, "
            "zstd} at K=2 lifts the Adiyat-864 ceiling above 0.999 without "
            "violating FPR."
        ),
        "schema_version": 1,
        "prereg_document": "experiments/exp95c_multi_compressor_adiyat/PREREG.md",
        "prereg_hash": _prereg_hash(),
        "exp94_baseline": exp94,
        "frozen_constants": {
            "seed": SEED,
            "n_pert_per_unit": N_PERT_PER_UNIT,
            "ctrl_n_units": CTRL_N_UNITS,
            "gzip_level": GZIP_LEVEL,
            "bz2_level": BZ2_LEVEL,
            "lzma_preset": LZMA_PRESET,
            "zstd_level": ZSTD_LEVEL,
            "fpr_target": FPR_TARGET,
            "band_a": [BAND_A_LO, BAND_A_HI],
            "adiyat_label": ADIYAT_LABEL,
            "expected_n_variants": EXPECTED_N_VARIANTS,
            "headline_k": HEADLINE_K,
            "protocol_drift_tol": PROTOCOL_DRIFT_TOL,
        },
        "n_variants": n_var,
        "n_null_ctrl_edits": n_null,
        "tau_per_compressor": tau_per,
        "ctrl_fpr_per_compressor_at_own_tau": fpr_per_at_own,
        "ctrl_fpr_by_consensus_K": {str(K): null_fpr_by_K[K]
                                    for K in (1, 2, 3, 4)},
        "spearman_rho_pairwise_ctrl_null": rho_matrix,
        "gzip_tau_drift_vs_exp94": gzip_tau_drift,
        "recalls": {
            "solo": recall_solo,
            "by_consensus_K": {str(K): recall_by_K[K] for K in (1, 2, 3, 4)},
            "exp94_R12_baseline": exp94["R12_only_baseline"],
            "lift_K_headline_over_flat": (
                recall_by_K[HEADLINE_K] - exp94["R12_only_baseline"]
            ),
        },
        "protocol_drift": {
            "abs_diff_gzip_recall_vs_exp94": drift,
            "ok": protocol_ok,
        },
        "per_position_audit_K_headline": pos_audit,
        "per_variant": per_variant,
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
