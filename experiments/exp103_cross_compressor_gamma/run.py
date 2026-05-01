"""
exp103_cross_compressor_gamma/run.py
=====================================
H35a — Cross-compressor universality of the Quran-indicator gamma.

Note (2026-04-26 night, v7.9-cand patch G): this hypothesis was originally
registered as H35 on 2026-04-22. The H35 label was later re-used by
exp95c_multi_compressor_adiyat for a different hypothesis; this experiment
is relabelled H35a to disambiguate. Numerics, verdict, and audit trail
unchanged. See RETRACTIONS_REGISTRY.md::R51 and
AUDIT_MEMO_2026-04-26_RISK_VECTORS.md §4.

Repeats the exp41_gzip_formalised.length_audit protocol with up to 4
lossless compressors (gzip, bzip2, zstd, brotli) on the same 68 Band-A
Quran + 200 ctrl units under the same internal single-letter edit
perturbation policy, and measures the coefficient-of-variation of
gamma across the available compressors.

This experiment is the empirical falsifier for Theorem 1 of
docs/PREREG_GAMMA_KOLMOGOROV.md. See PREREG.md §9 for the programme-
level decision outcomes of each verdict.

Pre-registered in PREREG.md (frozen 2026-04-22).

Reads (integrity-checked):
    phase_06_phi_m.pkl                                   state['CORPORA']
    results/experiments/exp41_gzip_formalised/length_audit.json
        -> used only for gzip gamma reproduction sanity check

Writes ONLY under results/experiments/exp103_cross_compressor_gamma/
"""
from __future__ import annotations

import bz2
import gzip
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats as sp_stats

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

EXP = "exp103_cross_compressor_gamma"

# --- Frozen constants (mirror PREREG §7) -----------------------------------
SEED = 42
N_PERT_PER_UNIT = 20
CTRL_N_UNITS = 200
BAND_A_LO, BAND_A_HI = 15, 100
GZIP_LEVEL = 9
BZIP2_LEVEL = 9
ZSTD_LEVEL = 22
BROTLI_QUALITY = 11

GAMMA_LOCKED_GZIP_EXP41 = 0.0716
GAMMA_REPRODUCTION_TOL = 0.01

CV_GAMMA_PASS = 0.10
CV_GAMMA_PARTIAL = 0.20

MIN_COMPRESSORS = 2

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


# --- Compressor registry ---------------------------------------------------
def _probe_compressors() -> dict[str, callable]:
    """Return {name: Z(s) -> int} for every importable compressor."""
    out: dict[str, callable] = {}

    # gzip (always)
    def _z_gzip(s: str) -> int:
        return len(gzip.compress(s.encode("utf-8"), compresslevel=GZIP_LEVEL))
    out["gzip"] = _z_gzip

    # bzip2 (always; stdlib)
    def _z_bz2(s: str) -> int:
        return len(bz2.compress(s.encode("utf-8"), compresslevel=BZIP2_LEVEL))
    out["bzip2"] = _z_bz2

    # zstd (optional)
    try:
        import zstandard  # type: ignore
        zstd_ctx = zstandard.ZstdCompressor(level=ZSTD_LEVEL)

        def _z_zstd(s: str) -> int:
            return len(zstd_ctx.compress(s.encode("utf-8")))
        out["zstd"] = _z_zstd
    except Exception as e:
        print(f"[{EXP}] zstd not available: {type(e).__name__}: {e}")

    # brotli (optional)
    try:
        import brotli  # type: ignore

        def _z_brotli(s: str) -> int:
            return len(brotli.compress(s.encode("utf-8"),
                                       quality=BROTLI_QUALITY))
        out["brotli"] = _z_brotli
    except Exception as e:
        print(f"[{EXP}] brotli not available: {type(e).__name__}: {e}")

    return out


# --- Text primitives (byte-equal to exp41) ---------------------------------
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


def _ncd(z_fn: callable, a: str, b: str) -> float:
    if not a and not b:
        return 0.0
    za = z_fn(a)
    zb = z_fn(b)
    zab = z_fn(a + b)
    denom = max(1, max(za, zb))
    return (zab - min(za, zb)) / denom


def _band_a(units):
    return [u for u in units if BAND_A_LO <= len(u.verses) <= BAND_A_HI]


# --- Perturbation (byte-equal to exp41._apply_perturbation) ----------------
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
            new_toks = list(toks)
            new_toks[wi] = new_word
            new_verses = list(verses)
            new_verses[vi] = " ".join(new_toks)
            return new_verses, vi
    return None


def _build_perturbation_plan(q_units, ctrl_units) -> list[dict]:
    """Build one fixed list of perturbations that every compressor sees.

    Same seed, same perturbation policy => same (canon, edited) pairs
    across compressors. Only the compressor changes. This isolates the
    compressor as the only source of variation in gamma.
    """
    rng_q = random.Random(SEED)
    rng_c = random.Random(SEED + 2)
    plan: list[dict] = []

    def _emit(group: str, units, rng_outer):
        for u in units:
            rng_u = random.Random(rng_outer.randrange(1 << 30))
            canon_stream = _letters_28(" ".join(u.verses))
            n_letters = len(canon_stream)
            if n_letters < 50:
                continue
            for _ in range(N_PERT_PER_UNIT):
                result = _apply_perturbation(u.verses, rng_u)
                if result is None:
                    continue
                pert_verses, _vi = result
                edited_stream = _letters_28(" ".join(pert_verses))
                plan.append({
                    "group": group,
                    "n_letters": n_letters,
                    "canon_stream": canon_stream,
                    "edited_stream": edited_stream,
                })

    _emit("quran", q_units, rng_q)
    _emit("ctrl", ctrl_units, rng_c)
    return plan


# --- Log-linear regression --------------------------------------------------
def _fit_gamma(n_letters: np.ndarray, ncd: np.ndarray, quran: np.ndarray) -> dict:
    """OLS fit:  log(ncd) = a + b * log(n_letters) + g * I(Quran)."""
    mask = (ncd > 0) & np.isfinite(ncd) & np.isfinite(n_letters)
    X = np.column_stack([
        np.ones(mask.sum()),
        np.log(n_letters[mask]),
        quran[mask].astype(float),
    ])
    y = np.log(ncd[mask])
    # OLS via numpy
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    # Residuals + covariance
    resid = y - X @ beta
    n, k = X.shape
    dof = max(1, n - k)
    sigma2 = float((resid @ resid) / dof)
    # Covariance of beta
    xtx_inv = np.linalg.inv(X.T @ X)
    cov_beta = sigma2 * xtx_inv
    se = np.sqrt(np.diag(cov_beta))
    g = float(beta[2])
    g_se = float(se[2])
    t = g / g_se if g_se > 0 else float("inf")
    # Two-sided p from t-distribution
    p = float(2.0 * (1.0 - sp_stats.t.cdf(abs(t), df=dof)))
    ci_lo = g - 1.96 * g_se
    ci_hi = g + 1.96 * g_se
    return {
        "alpha": float(beta[0]),
        "beta_length": float(beta[1]),
        "gamma": g,
        "gamma_se": g_se,
        "gamma_CI95_lo": float(ci_lo),
        "gamma_CI95_hi": float(ci_hi),
        "gamma_t": float(t),
        "gamma_p_two_sided": p,
        "ci_excludes_zero": bool(ci_lo > 0 or ci_hi < 0),
        "n_points": int(mask.sum()),
        "length_slope_se": float(se[1]),
        "sigma2_resid": sigma2,
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

    print(f"[{EXP}] H35a — cross-compressor gamma universality")

    # --- Probe compressors ---
    compressors = _probe_compressors()
    available = list(compressors.keys())
    print(f"[{EXP}] Available compressors: {available}")

    if len(available) < MIN_COMPRESSORS:
        print(f"[{EXP}] FAIL_n_compressors: need >= {MIN_COMPRESSORS}, "
              f"got {len(available)}")
        _write_early_fail(out, "FAIL_n_compressors",
                          {"available": available,
                           "required_min": MIN_COMPRESSORS})
        self_check_end(pre, EXP)
        return 1

    # --- Load corpus ---
    print(f"[{EXP}] Loading phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    CORPORA = phi["state"]["CORPORA"]

    q_units = _band_a(CORPORA.get("quran", []))
    ctrl_pool: list = []
    for name in ARABIC_CTRL:
        ctrl_pool.extend(_band_a(CORPORA.get(name, [])))
    rng_pool = random.Random(SEED + 1)
    rng_pool.shuffle(ctrl_pool)
    ctrl_units = ctrl_pool[:CTRL_N_UNITS]
    print(f"[{EXP}] n_q_bandA={len(q_units)}  n_ctrl={len(ctrl_units)}")

    # --- Build single perturbation plan, reused across all compressors ---
    print(f"[{EXP}] Building perturbation plan ...")
    plan = _build_perturbation_plan(q_units, ctrl_units)
    n_plan = len(plan)
    print(f"[{EXP}] Plan size: {n_plan} edits")

    if n_plan < 500:
        print(f"[{EXP}] WARN: perturbation plan has only {n_plan} edits; "
              "regression may be low-power.")

    n_letters = np.asarray([row["n_letters"] for row in plan], dtype=float)
    quran_flag = np.asarray(
        [row["group"] == "quran" for row in plan], dtype=int
    )

    # --- Per-compressor NCD + gamma fit ---
    per_compressor: dict[str, dict] = {}
    for cname, z_fn in compressors.items():
        t_c = time.time()
        ncd_vals = np.empty(n_plan, dtype=float)
        for i, row in enumerate(plan):
            ncd_vals[i] = _ncd(z_fn, row["canon_stream"], row["edited_stream"])
            if not math.isfinite(ncd_vals[i]) or ncd_vals[i] <= 0:
                ncd_vals[i] = float("nan")
        # Per-group summaries (for sanity)
        q_mask = quran_flag.astype(bool) & np.isfinite(ncd_vals)
        c_mask = (~quran_flag.astype(bool)) & np.isfinite(ncd_vals)
        q_med = float(np.median(ncd_vals[q_mask])) if q_mask.any() else float("nan")
        c_med = float(np.median(ncd_vals[c_mask])) if c_mask.any() else float("nan")
        fit = _fit_gamma(n_letters, ncd_vals, quran_flag)
        fit["q_median_ncd"] = q_med
        fit["ctrl_median_ncd"] = c_med
        fit["raw_cohens_d_confounded"] = _cohens_d_safe(
            ncd_vals[q_mask], ncd_vals[c_mask]
        )
        fit["runtime_seconds"] = round(time.time() - t_c, 2)
        per_compressor[cname] = fit
        print(f"[{EXP}]   {cname:7s}  gamma={fit['gamma']:+.4f}  "
              f"CI=[{fit['gamma_CI95_lo']:+.4f}, {fit['gamma_CI95_hi']:+.4f}]  "
              f"p={fit['gamma_p_two_sided']:.2e}  "
              f"q_med={q_med:.4f}  ctrl_med={c_med:.4f}  "
              f"dt={fit['runtime_seconds']}s")

    # --- gzip reproduction sanity ---
    gzip_gamma = per_compressor.get("gzip", {}).get("gamma", float("nan"))
    gzip_reproduction_ok = abs(gzip_gamma - GAMMA_LOCKED_GZIP_EXP41) <= GAMMA_REPRODUCTION_TOL
    print(f"[{EXP}] gzip gamma measured = {gzip_gamma:+.4f}  "
          f"locked = {GAMMA_LOCKED_GZIP_EXP41}  "
          f"reproduction {'OK' if gzip_reproduction_ok else 'FAIL'} "
          f"(tol ±{GAMMA_REPRODUCTION_TOL})")

    # --- Cross-compressor stats ---
    gammas = np.asarray(
        [per_compressor[c]["gamma"] for c in available], dtype=float
    )
    g_mean = float(np.mean(gammas))
    g_sd = float(np.std(gammas, ddof=0))  # population sd, not sample
    g_sd_sample = float(np.std(gammas, ddof=1)) if len(gammas) > 1 else float("nan")
    cv = g_sd / abs(g_mean) if g_mean != 0 else float("inf")
    print(f"[{EXP}] Cross-compressor gamma: mean={g_mean:+.4f}  "
          f"sd(pop)={g_sd:.4f}  sd(sample,ddof=1)={g_sd_sample:.4f}  "
          f"CV={cv:.4f}")

    # Per-compressor CI exclusion-of-zero
    ci_excludes: dict[str, bool] = {
        c: bool(per_compressor[c]["ci_excludes_zero"]) for c in available
    }
    any_null = any(not v for v in ci_excludes.values())

    # --- Verdict ---
    if not gzip_reproduction_ok:
        verdict = "FAIL_gzip_reproduction"
    elif any_null:
        verdict = "FAIL_any_compressor_null"
    elif cv > CV_GAMMA_PARTIAL:
        verdict = "FAIL_not_universal"
    elif cv > CV_GAMMA_PASS:
        verdict = "PARTIAL_weakly_universal"
    else:
        verdict = "PASS_universal"

    elapsed = time.time() - t0

    print(f"\n{'=' * 64}")
    print(f"[{EXP}] PRE-REGISTERED VERDICT: {verdict}")
    print(f"  compressors tested    : {available}  (n={len(available)})")
    print(f"  gzip reproduction     : "
          f"{'OK' if gzip_reproduction_ok else 'FAIL'}  "
          f"measured {gzip_gamma:+.4f} vs locked {GAMMA_LOCKED_GZIP_EXP41}")
    print(f"  cross-compressor mean : {g_mean:+.4f}")
    print(f"  cross-compressor CV   : {cv:.4f}  (PASS<={CV_GAMMA_PASS}, "
          f"PARTIAL<={CV_GAMMA_PARTIAL})")
    for c in available:
        pc = per_compressor[c]
        mark = "SIG" if pc["ci_excludes_zero"] else "NULL"
        print(f"    {c:7s}  gamma={pc['gamma']:+.4f}  "
              f"[{pc['gamma_CI95_lo']:+.4f}, {pc['gamma_CI95_hi']:+.4f}]  "
              f"{mark}")
    print(f"{'=' * 64}")

    report = {
        "experiment": EXP,
        "hypothesis": (
            "H35a — Quran-indicator gamma is universal across compressor "
            "families (falsifier for Theorem 1 of "
            "docs/PREREG_GAMMA_KOLMOGOROV.md). Hypothesis ID relabelled "
            "from H35 → H35a on 2026-04-26 night to resolve collision "
            "with exp95c_multi_compressor_adiyat (which now owns H35); "
            "numerics, verdict, audit trail unchanged. See "
            "RETRACTIONS_REGISTRY.md::R51."
        ),
        "schema_version": 1,
        "prereg_document": "experiments/exp103_cross_compressor_gamma/PREREG.md",
        "prereg_hash": _prereg_hash(),
        "frozen_constants": {
            "seed": SEED,
            "n_pert_per_unit": N_PERT_PER_UNIT,
            "ctrl_n_units": CTRL_N_UNITS,
            "band_a": [BAND_A_LO, BAND_A_HI],
            "gzip_level": GZIP_LEVEL,
            "bzip2_level": BZIP2_LEVEL,
            "zstd_level": ZSTD_LEVEL,
            "brotli_quality": BROTLI_QUALITY,
            "gamma_locked_gzip_exp41": GAMMA_LOCKED_GZIP_EXP41,
            "gamma_reproduction_tol": GAMMA_REPRODUCTION_TOL,
            "cv_gamma_pass": CV_GAMMA_PASS,
            "cv_gamma_partial": CV_GAMMA_PARTIAL,
            "min_compressors": MIN_COMPRESSORS,
        },
        "compressors_tested": available,
        "n_quran_units_bandA": len(q_units),
        "n_ctrl_units": len(ctrl_units),
        "n_perturbations": n_plan,
        "per_compressor": per_compressor,
        "gzip_reproduction": {
            "measured": gzip_gamma,
            "locked": GAMMA_LOCKED_GZIP_EXP41,
            "tolerance": GAMMA_REPRODUCTION_TOL,
            "within_tol": gzip_reproduction_ok,
        },
        "cross_compressor": {
            "gammas": {c: per_compressor[c]["gamma"] for c in available},
            "mean": g_mean,
            "sd_population_ddof0": g_sd,
            "sd_sample_ddof1": g_sd_sample,
            "cv": cv,
            "any_ci_includes_zero": any_null,
            "ci_excludes_zero_per_compressor": ci_excludes,
        },
        "verdict": verdict,
        "programme_decision": _programme_decision(verdict),
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


def _cohens_d_safe(a: np.ndarray, b: np.ndarray) -> float:
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if a.size < 2 or b.size < 2:
        return float("nan")
    va = float(a.var(ddof=1))
    vb = float(b.var(ddof=1))
    pooled = ((a.size - 1) * va + (b.size - 1) * vb) / (a.size + b.size - 2)
    if pooled <= 0:
        return float("nan")
    return float((a.mean() - b.mean()) / math.sqrt(pooled))


def _programme_decision(verdict: str) -> str:
    """Mirror PREREG §9 decision outcomes."""
    return {
        "PASS_universal": (
            "Theorem 1 worth formal proof work. Proceed to "
            "Kolmogorov/MDL collaborator recruitment per "
            "docs/PREREG_GAMMA_KOLMOGOROV.md §5."
        ),
        "PARTIAL_weakly_universal": (
            "Re-scope programme to 'gamma is a positive constant for "
            "all LZ-family compressors'. Proceed with MDL statistician "
            "(tier 5.2), not full Kolmogorov-theorist (tier 5.1)."
        ),
        "FAIL_not_universal": (
            "ABORT the Kolmogorov-derivation programme. gamma = +0.0716 "
            "survives as a gzip-specific reproducible empirical scalar "
            "only; re-frame in paper as 'compressor-calibrated edit-"
            "detection parameter' rather than information-theoretic "
            "constant candidate."
        ),
        "FAIL_any_compressor_null": (
            "At least one compression family is blind to the Quran "
            "signal. Re-frame programme as 'identify the compression "
            "mechanism that captures gamma, and use THAT mechanism's "
            "theory for Theorem 1'."
        ),
        "FAIL_gzip_reproduction": (
            "gzip baseline failed to reproduce exp41's locked gamma = "
            "+0.0716 within ±0.01. Something has drifted (corpus, code, "
            "perturbation policy). Do not proceed; investigate drift "
            "first."
        ),
        "FAIL_n_compressors": (
            "Fewer than 2 compressors importable. Install `zstandard` "
            "and/or `brotli` via pip and re-run."
        ),
    }.get(verdict, "UNKNOWN_VERDICT")


def _write_early_fail(out: Path, verdict: str, context: dict) -> None:
    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump({
            "experiment": EXP,
            "schema_version": 1,
            "verdict": verdict,
            "context": context,
            "prereg_hash": _prereg_hash(),
            "programme_decision": _programme_decision(verdict),
        }, f, indent=2, ensure_ascii=False, default=float)


if __name__ == "__main__":
    sys.exit(main())
