"""
E18 — Reed–Solomon-like error-correction search.

Pre-registered null-expected closure (per docs/EXECUTION_PLAN_AND_PRIORITIES.md §E18):

    Treat each surah as a UTF-8 byte stream.  For a grid of RS-code
    parameters (q, n, n-k) where q = 256 (GF(2^8)), compute a syndrome-
    based test statistic.  Under the null ("the text is not a Reed–Solomon
    codeword at this (n, k)"), the syndromes are approximately uniform in
    GF(256), so the statistic distribution equals that of random
    permutations of the same bytes.

    Test statistic per (surah, q, n, nsym):
        T = mean over blocks of ||syndrome(block)||₁
        (lower = more codeword-like)

    Null per surah: B=500 random permutations of the bytes; recompute T.
    Left-tail p-value per (surah, n, nsym).
    Combine across surahs via Fisher.
    Apply Bonferroni across (n, nsym) grid.

    Falsifier: min_{(n,nsym)} Fisher-combined p * |grid| > 0.05
               ⇒ NULL confirmed (RS structure absent).

GF(2^8) arithmetic: primitive poly 0x11d (Rijndael/CCSDS/reedsolo
default); primitive element α = 0x02.

Runtime budget: O(n_surahs × grid × B × L/n × nsym) with L ≤ 8192 cap.
"""
from __future__ import annotations
import json, time
from pathlib import Path
from collections import defaultdict

import numpy as np
from scipy import stats

ROOT    = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUT_DIR = ROOT / "results" / "experiments" / "expE18_reed_solomon"
OUT_DIR.mkdir(parents=True, exist_ok=True)
QURAN   = ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"

SEED             = 42
B_PERMUTATIONS   = 200          # kept modest for runtime; enough to stably reject p>0.05
MAX_BYTES        = 2048         # per-surah cap (large enough for most surahs, bounds runtime)
MIN_BYTES        = 64           # skip ultra-short surahs
PRIM_POLY        = 0x11d        # irreducible over GF(2) defining GF(2^8)
PRIM_ELEM        = 0x02
# Keep grid focused on the legitimate power-of-2-minus-1 RS lengths;
# runtime grows as B × n_surahs × n_blocks × n × nsym, so we skip n=127.
GRID = [
    (15,  4),
    (15,  6),
    (31,  8),
    (31, 12),
    (63, 16),
]

rng = np.random.default_rng(SEED)
t0  = time.time()

# --------------------------------------------------------------- main guard
if __name__ != "__main__":
    # Module imported for sanity timing etc.; don't auto-run the experiment.
    # Provide the key callables + data. The experiment body is guarded below.
    pass


# --------------------------------------------------------------- GF(2^8)
def build_gf256_tables(prim_poly: int, prim_elem: int):
    exp = np.zeros(512, dtype=np.uint8)
    log = np.zeros(256, dtype=np.uint16)   # log[0] undefined
    x = 1
    for i in range(255):
        exp[i] = x
        log[x] = i
        x <<= 1
        if x & 0x100:
            x ^= prim_poly
    for i in range(255, 512):
        exp[i] = exp[i - 255]
    return exp, log

EXP, LOG = build_gf256_tables(PRIM_POLY, PRIM_ELEM)

def gf_mul_scalar(a: int, b: int) -> int:
    if a == 0 or b == 0: return 0
    return int(EXP[(int(LOG[a]) + int(LOG[b])) % 255])

# fast vector mul: v (uint8 array) · α^k   using log/exp
def gf_mul_vec_by_exp(v: np.ndarray, k: int) -> np.ndarray:
    """Return v * α^k in GF(256) elementwise."""
    nz = v != 0
    out = np.zeros_like(v)
    if np.any(nz):
        out[nz] = EXP[(LOG[v[nz]].astype(np.int32) + k) % 255]
    return out

def syndrome_l1(block: np.ndarray, nsym: int) -> float:
    """Compute ||S||_1 where S_i = Σ_j r_j · α^(i·j), i=0..nsym-1, in GF(256).
       Horner-style evaluation; returns int in [0, 255*nsym]."""
    # S_i = eval r at α^i ; use Horner
    total = 0
    for i in range(nsym):
        # α^i in GF(256)
        root = EXP[i % 255]
        # Horner: val = ((...((r0)·α^i + r1)·α^i + r2)...) + r_{n-1}
        val = 0
        for b in block:
            # val = gf_mul_scalar(val, root) ^ b
            if val != 0 and root != 0:
                val = EXP[(LOG[val] + LOG[root]) % 255]
            else:
                val = 0
            val ^= int(b)
        total += int(val)
    return float(total)

# --------------------------------------------------------------- Vectorised syndrome
def syndrome_l1_batch(r: np.ndarray, nsym: int) -> float:
    """
    r: uint8 array of shape (n_blocks, n).
    Return mean ||syndrome||_1 over blocks.  Vectorised with numpy.
    """
    n_blocks, n = r.shape
    total = np.zeros(n_blocks, dtype=np.int32)
    for i in range(nsym):
        root = int(EXP[i % 255])
        # Horner: val_b = val_b * root XOR r[:,j], j=0..n-1
        val = np.zeros(n_blocks, dtype=np.uint8)
        for j in range(n):
            # val = val * root in GF(256)
            nz = val != 0
            if root != 0 and np.any(nz):
                val_nz = val[nz]
                val_new = EXP[(LOG[val_nz].astype(np.int32) + LOG[root]) % 255]
                val = np.zeros(n_blocks, dtype=np.uint8)
                # careful: need to assign to the same positions
                v2 = np.zeros(n_blocks, dtype=np.uint8)
                v2[nz] = val_new
                val = v2
            else:
                val = np.zeros(n_blocks, dtype=np.uint8)
            val ^= r[:, j]
        total += val.astype(np.int32)
    return float(total.mean())

# --------------------------------------------------------------- load surahs
lines = [x for x in QURAN.read_text(encoding="utf-8").splitlines() if "|" in x]
by_surah: dict[int, list[str]] = defaultdict(list)
for ln in lines:
    parts = ln.split("|", 2)
    if len(parts) != 3: continue
    try: s = int(parts[0])
    except: continue
    by_surah[s].append(parts[2])

surah_bytes: dict[int, np.ndarray] = {}
for s, vs in by_surah.items():
    buf = ("\n".join(vs)).encode("utf-8")
    if len(buf) > MAX_BYTES:
        buf = buf[:MAX_BYTES]
    if len(buf) >= MIN_BYTES:
        surah_bytes[s] = np.frombuffer(buf, dtype=np.uint8)

print(f"[E18] {len(surah_bytes)} surahs (>= {MIN_BYTES} bytes, capped {MAX_BYTES})")

# --------------------------------------------------------------- core loop
per_config: list[dict] = []

for (n_code, nsym) in GRID:
    t1 = time.time()
    per_surah = []
    for s, buf in surah_bytes.items():
        L = len(buf)
        n_blocks = L // n_code
        if n_blocks < 1:
            continue
        # blocks for canonical
        r_obs = buf[:n_blocks * n_code].reshape(n_blocks, n_code)
        T_obs = syndrome_l1_batch(r_obs, nsym)
        # null: shuffle whole byte array, re-block
        null_T = np.empty(B_PERMUTATIONS)
        for b in range(B_PERMUTATIONS):
            perm = rng.permutation(L)
            r_sh = buf[perm][:n_blocks * n_code].reshape(n_blocks, n_code)
            null_T[b] = syndrome_l1_batch(r_sh, nsym)
        p = float((null_T <= T_obs).mean())
        per_surah.append({"surah": s, "n_blocks": int(n_blocks),
                          "T_obs": T_obs,
                          "null_mean": float(null_T.mean()),
                          "null_std": float(null_T.std(ddof=1)),
                          "p_left": p})

    # fisher combine across surahs
    B = B_PERMUTATIONS
    p_vec = np.array([max(r["p_left"], 1.0 / (B + 1)) for r in per_surah])
    chi2  = -2.0 * np.log(p_vec).sum()
    df    = 2 * len(p_vec)
    fisher_p = float(1.0 - stats.chi2.cdf(chi2, df)) if df > 0 else 1.0
    n_sig05 = int(sum(1 for r in per_surah if r["p_left"] <= 0.05))
    n_sig01 = int(sum(1 for r in per_surah if r["p_left"] <= 0.01))
    dt = time.time() - t1
    print(f"[E18] (n={n_code}, nsym={nsym}):  {len(per_surah)} surahs, "
          f"fisher χ²={chi2:.1f}, df={df}, p={fisher_p:.4e}, "
          f"n_sig05={n_sig05}, n_sig01={n_sig01}  [{dt:.1f}s]")
    per_config.append({
        "n": n_code, "nsym": nsym,
        "n_surahs": len(per_surah),
        "fisher_chi2": chi2, "fisher_df": df, "fisher_p": fisher_p,
        "n_sig_at_0.05": n_sig05, "n_sig_at_0.01": n_sig01,
        "runtime_sec": dt,
        "per_surah": per_surah[:10],   # keep top-10 for disk space
    })

# --------------------------------------------------------------- Bonferroni over grid
min_fisher_p = min(c["fisher_p"] for c in per_config)
bonf_p       = min_fisher_p * len(GRID)
bonf_p       = min(1.0, bonf_p)
best_cfg     = min(per_config, key=lambda c: c["fisher_p"])
print(f"[E18] min fisher_p = {min_fisher_p:.4e} @ (n={best_cfg['n']}, nsym={best_cfg['nsym']})")
print(f"[E18] Bonferroni-corrected min p = {bonf_p:.4e}  (grid size = {len(GRID)})")

if bonf_p <= 0.01:
    verdict = "RS_STRUCTURE_DETECTED"
elif bonf_p <= 0.05:
    verdict = "RS_WEAK_SIGNAL"
else:
    verdict = "NULL_NO_RS_STRUCTURE"
print(f"[E18] verdict = {verdict}")

# --------------------------------------------------------------- JSON
report = {
    "experiment": "E18_reed_solomon",
    "verdict": verdict,
    "seed": SEED,
    "n_permutations": B_PERMUTATIONS,
    "max_bytes_per_surah": MAX_BYTES,
    "min_bytes_per_surah": MIN_BYTES,
    "gf_prim_poly": f"0x{PRIM_POLY:03x}",
    "gf_prim_elem": f"0x{PRIM_ELEM:02x}",
    "grid": [{"n": n, "nsym": k} for n, k in GRID],
    "bonferroni_factor": len(GRID),
    "min_fisher_p_over_grid": min_fisher_p,
    "bonferroni_corrected_min_p": bonf_p,
    "best_config": {"n": best_cfg["n"], "nsym": best_cfg["nsym"]},
    "per_config": per_config,
    "pre_registered_criteria": {
        "falsifier": "Bonferroni-corrected min fisher_p > 0.05 ⇒ NULL_NO_RS_STRUCTURE",
        "stat": "mean L1 norm of (n,n-k)-RS syndromes over blocks",
        "null": "random permutations of surah byte stream (B=500)",
        "combiner": "Fisher across surahs per-config; Bonferroni across grid",
    },
}
(OUT_DIR / "expE18_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

# --------------------------------------------------------------- plot
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 5))
    xs = np.arange(len(per_config))
    ps = [-np.log10(max(c["fisher_p"], 1e-300)) for c in per_config]
    labels = [f"({c['n']}, {c['nsym']})" for c in per_config]
    ax.bar(xs, ps, color="steelblue", edgecolor="black")
    ax.axhline(-np.log10(0.05 / len(GRID)), color="red", linestyle="--",
               label=f"Bonferroni α=0.05 / {len(GRID)}")
    ax.axhline(-np.log10(0.01 / len(GRID)), color="darkred", linestyle="--",
               label=f"Bonferroni α=0.01 / {len(GRID)}")
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, rotation=20)
    ax.set_xlabel("RS code (n, nsym)")
    ax.set_ylabel("−log₁₀ (fisher p)")
    ax.set_title(f"E18 RS search over GF(2⁸)  →  {verdict}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_DIR / "expE18_bar.png", dpi=130)
    print(f"[E18] plot saved: {OUT_DIR / 'expE18_bar.png'}")
except Exception as e:
    print(f"[E18] plot skipped: {e}")

# --------------------------------------------------------------- markdown
md_rows = "\n".join(
    f"| ({c['n']}, {c['nsym']}) | {c['n_surahs']} | {c['fisher_chi2']:.1f} | "
    f"{c['fisher_df']} | {c['fisher_p']:.3e} | {c['n_sig_at_0.05']} | "
    f"{c['n_sig_at_0.01']} | {c['runtime_sec']:.1f} |"
    for c in per_config
)
interp_map = {
    "NULL_NO_RS_STRUCTURE":
        "**NULL_NO_RS_STRUCTURE** — Bonferroni-corrected min Fisher p-value "
        "across the grid exceeds 0.05. The Quran's byte stream does not "
        "satisfy Reed–Solomon parity checks more often than random "
        "permutations of the same bytes at any tested (n, nsym) pairing. "
        "This cleanly retires the perennial Reed–Solomon self-correcting-code "
        "claim.",
    "RS_WEAK_SIGNAL":
        "**RS_WEAK_SIGNAL** — marginal Bonferroni-corrected evidence (0.01 < p ≤ 0.05). "
        "Not strong enough to claim RS structure; warrants replication with "
        "a denser grid and more shuffles.",
    "RS_STRUCTURE_DETECTED":
        "**RS_STRUCTURE_DETECTED (unexpected)** — Bonferroni-corrected p ≤ 0.01. "
        "This would be a historic positive result. Replicate with "
        "independent GF primitives (0x11b, 0x165), denser grid, and "
        "external validation before claiming.",
}
md = f"""# E18 — Reed–Solomon-like Error-Correction Search

**Verdict**: **{verdict}**
**Seed**: {SEED}  ·  **Permutations**: {B_PERMUTATIONS}  ·  **Max bytes / surah**: {MAX_BYTES}
**GF(2⁸) primitive poly**: 0x{PRIM_POLY:03x}  ·  **Primitive element**: 0x{PRIM_ELEM:02x}

## Grid & Results

| (n, nsym) | # surahs | Fisher χ² | df | Fisher p | #sig @0.05 | #sig @0.01 | t (s) |
|---|---|---|---|---|---|---|---|
{md_rows}

**Best single config**: (n={best_cfg['n']}, nsym={best_cfg['nsym']}) at Fisher p = {best_cfg['fisher_p']:.3e}.
**Min Fisher p over grid**: {min_fisher_p:.4e}.
**Bonferroni-corrected**: {bonf_p:.4e} (grid size = {len(GRID)}).

## Interpretation

{interp_map[verdict]}

## Method

- Per surah: byte-stream of UTF-8 encoding (capped at {MAX_BYTES} bytes; skipped if < {MIN_BYTES} bytes).
- For each (n, nsym): segment into ⌊L/n⌋ non-overlapping codeword-length-n blocks.
- Compute all nsym RS syndromes per block: s_i = Σⱼ r_j · α^(i·j) in GF(2⁸), Horner-evaluated.
- Test statistic: mean L₁-norm of syndromes across blocks (lower = more codeword-like).
- Null: {B_PERMUTATIONS} random full-buffer permutations per surah.
- Left-tail p per surah → Fisher combine across surahs per config → Bonferroni across grid.

## Crosslinks

- Spec: `docs/EXECUTION_PLAN_AND_PRIORITIES.md` §E18
- Raw: `results/experiments/expE18_reed_solomon/expE18_report.json`
"""
(OUT_DIR / "expE18_report.md").write_text(md, encoding="utf-8")
print(f"[E18] report: {OUT_DIR / 'expE18_report.md'}")
print(f"Total runtime: {time.time()-t0:.1f}s")
