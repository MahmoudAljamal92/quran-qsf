"""
E18 addendum — UTF-8 confound control.

The primary E18 run detected a strong Fisher signal at (n=31, nsym=8) and
(n=31, nsym=12) over the Quran's UTF-8 byte stream.  Before interpreting
this as Reed-Solomon structure, we MUST rule out the obvious confound:

    UTF-8 encoding of Arabic text has strong positional byte-pair
    structure (lead-byte 0xD8..0xDB + continuation-byte 0x80..0xBF
    interleave).  Random byte-level shuffles break this positional
    structure.  Therefore the "signal" might simply reflect this
    universal UTF-8 property, not any Quran-specific code.

Test protocol:

    1. Run the IDENTICAL E18 pipeline on an Arabic CONTROL corpus
       (poetry.txt), chunked into surah-sized byte units.
    2. If control shows the SAME Fisher-significant signal at the SAME
       (n, nsym), the Quran result is a pure UTF-8 artifact → NULL.
    3. If control shows NULL and Quran shows signal, the result is
       Quran-specific (warrants further investigation).
    4. Also run the test on a single-byte-alphabet Quran representation
       (Arabic letters remapped to bytes 1..30, stripping UTF-8
       positional structure entirely).  Same reasoning applies.
"""
from __future__ import annotations
import json, time, unicodedata
from pathlib import Path
from collections import defaultdict

import numpy as np
from scipy import stats

ROOT    = Path(r"C:\Users\mtj_2\OneDrive\Desktop\Quran")
OUT_DIR = ROOT / "results" / "experiments" / "expE18_reed_solomon"
QURAN   = ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"
POETRY  = ROOT / "data" / "corpora" / "ar" / "poetry.txt"

SEED             = 42
B_PERMUTATIONS   = 200
MAX_BYTES        = 2048
MIN_BYTES        = 64
PRIM_POLY        = 0x11d
PRIM_ELEM        = 0x02

# Focused grid: the configs where Quran-UTF8 showed signal, plus the nulls.
GRID = [
    (15,  4),
    (31,  8),
    (31, 12),
    (63, 16),
]

rng = np.random.default_rng(SEED)

# --------------------------------------------------------------- GF(2^8) tables
EXP = np.zeros(512, dtype=np.uint8)
LOG = np.zeros(256, dtype=np.uint16)
_x = 1
for _i in range(255):
    EXP[_i] = _x
    LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= PRIM_POLY
for _i in range(255, 512):
    EXP[_i] = EXP[_i - 255]

def syndrome_l1_batch(r: np.ndarray, nsym: int) -> float:
    n_blocks, n = r.shape
    total = np.zeros(n_blocks, dtype=np.int32)
    for i in range(nsym):
        root = int(EXP[i % 255])
        val = np.zeros(n_blocks, dtype=np.uint8)
        for j in range(n):
            if root != 0:
                nz = val != 0
                if np.any(nz):
                    v2 = np.zeros(n_blocks, dtype=np.uint8)
                    v2[nz] = EXP[(LOG[val[nz]].astype(np.int32) + LOG[root]) % 255]
                    val = v2
                else:
                    val = np.zeros(n_blocks, dtype=np.uint8)
            else:
                val = np.zeros(n_blocks, dtype=np.uint8)
            val ^= r[:, j]
        total += val.astype(np.int32)
    return float(total.mean())

# --------------------------------------------------------------- byte-stream constructors

def quran_utf8_streams():
    """Recreate the primary pipeline for reference."""
    lines = [x for x in QURAN.read_text(encoding="utf-8").splitlines() if "|" in x]
    bys = defaultdict(list)
    for ln in lines:
        parts = ln.split("|", 2)
        if len(parts) != 3: continue
        try: s = int(parts[0])
        except: continue
        bys[s].append(parts[2])
    out = {}
    for s, vs in bys.items():
        buf = ("\n".join(vs)).encode("utf-8")[:MAX_BYTES]
        if len(buf) >= MIN_BYTES:
            out[s] = np.frombuffer(buf, dtype=np.uint8)
    return out

def build_compact_alphabet(by_surah):
    """Map each Arabic letter (and space/newline) to a distinct byte 1..N.
       Diacritics stripped."""
    chars = set()
    for s, vs in by_surah.items():
        for t in vs:
            t_nfd = unicodedata.normalize("NFD", t)
            for ch in t_nfd:
                if unicodedata.combining(ch): continue
                chars.add(ch)
    alphabet = sorted(chars)
    # ensure space + newline first
    mapping = {}
    for i, ch in enumerate(alphabet, start=1):
        mapping[ch] = i
    return mapping

def quran_compact_streams():
    lines = [x for x in QURAN.read_text(encoding="utf-8").splitlines() if "|" in x]
    bys = defaultdict(list)
    for ln in lines:
        parts = ln.split("|", 2)
        if len(parts) != 3: continue
        try: s = int(parts[0])
        except: continue
        bys[s].append(parts[2])
    mapping = build_compact_alphabet(bys)
    print(f"[E18c] compact alphabet size: {len(mapping)}")
    out = {}
    for s, vs in bys.items():
        joined = "\n".join(vs)
        stripped = unicodedata.normalize("NFD", joined)
        codes = []
        for ch in stripped:
            if unicodedata.combining(ch): continue
            c = mapping.get(ch)
            if c is not None:
                codes.append(c)
        buf = np.array(codes[:MAX_BYTES], dtype=np.uint8)
        if len(buf) >= MIN_BYTES:
            out[s] = buf
    return out

def poetry_utf8_streams():
    """Chunk poetry.txt into surah-size byte units (≈ 512-byte avg Quran chunk)."""
    raw = POETRY.read_text(encoding="utf-8", errors="replace")
    # split on double-newline (poem boundary) for roughly independent chunks
    chunks = [c for c in raw.split("\n\n") if len(c.strip()) > 50]
    out = {}
    unit = 0
    for c in chunks:
        buf = c.encode("utf-8")[:MAX_BYTES]
        if len(buf) >= MIN_BYTES:
            out[unit] = np.frombuffer(buf, dtype=np.uint8)
            unit += 1
        if unit >= 114:   # match Quran scale
            break
    return out

# --------------------------------------------------------------- one-experiment driver

def run_arm(name: str, streams: dict):
    print(f"\n[E18c] === arm = {name}  ({len(streams)} units) ===")
    arm_out = []
    t_arm = time.time()
    for (n_code, nsym) in GRID:
        t1 = time.time()
        per_unit = []
        for s, buf in streams.items():
            L = len(buf)
            n_blocks = L // n_code
            if n_blocks < 1: continue
            r_obs = buf[:n_blocks * n_code].reshape(n_blocks, n_code)
            T_obs = syndrome_l1_batch(r_obs, nsym)
            null_T = np.empty(B_PERMUTATIONS)
            for b in range(B_PERMUTATIONS):
                perm = rng.permutation(L)
                r_sh = buf[perm][:n_blocks * n_code].reshape(n_blocks, n_code)
                null_T[b] = syndrome_l1_batch(r_sh, nsym)
            p = float((null_T <= T_obs).mean())
            per_unit.append({"unit": s, "n_blocks": int(n_blocks),
                             "T_obs": T_obs,
                             "null_mean": float(null_T.mean()),
                             "p_left": p})
        B = B_PERMUTATIONS
        p_vec = np.array([max(r["p_left"], 1.0 / (B + 1)) for r in per_unit])
        chi2  = -2.0 * np.log(p_vec).sum()
        df    = 2 * len(p_vec)
        fisher_p = float(1.0 - stats.chi2.cdf(chi2, df)) if df > 0 else 1.0
        n_sig05 = int(sum(1 for r in per_unit if r["p_left"] <= 0.05))
        n_sig01 = int(sum(1 for r in per_unit if r["p_left"] <= 0.01))
        dt = time.time() - t1
        print(f"[E18c] arm={name:<22s} (n={n_code}, nsym={nsym}):  "
              f"fisher p={fisher_p:.3e}  sig05={n_sig05}/{len(per_unit)}  "
              f"sig01={n_sig01}/{len(per_unit)}   [{dt:.1f}s]")
        arm_out.append({
            "n": n_code, "nsym": nsym,
            "n_units": len(per_unit),
            "fisher_chi2": chi2, "fisher_df": df, "fisher_p": fisher_p,
            "n_sig_at_0.05": n_sig05, "n_sig_at_0.01": n_sig01,
            "runtime_sec": dt,
        })
    print(f"[E18c] arm={name} total: {time.time()-t_arm:.1f}s")
    return arm_out

# --------------------------------------------------------------- run all arms

arms = {
    "A_quran_utf8":    quran_utf8_streams(),
    "B_quran_compact": quran_compact_streams(),
    "C_poetry_utf8":   poetry_utf8_streams(),
}
results = {name: run_arm(name, s) for name, s in arms.items()}

# --------------------------------------------------------------- confound logic
def sig_at(arm_res, n, nsym, alpha=0.01):
    for r in arm_res:
        if r["n"] == n and r["nsym"] == nsym:
            return r["fisher_p"] <= alpha
    return False

# check the strongest UTF-8 Quran signal at (31, 8)
focal = (31, 8)
quran_utf8_sig   = sig_at(results["A_quran_utf8"], *focal)
quran_compact_sig= sig_at(results["B_quran_compact"], *focal)
poetry_utf8_sig  = sig_at(results["C_poetry_utf8"], *focal)

print(f"\n[E18c] focal config ({focal[0]}, {focal[1]}) signal at α=0.01:")
print(f"  A quran_utf8:    {quran_utf8_sig}")
print(f"  B quran_compact: {quran_compact_sig}")
print(f"  C poetry_utf8:   {poetry_utf8_sig}")

if quran_utf8_sig and poetry_utf8_sig and not quran_compact_sig:
    verdict = "NULL_UTF8_CONFOUND"
    interpretation = ("UTF-8 encoding positional structure confounds the RS "
                      "syndrome test.  Signal present on Quran-UTF8 AND Arabic "
                      "control (poetry), absent on Quran compact-alphabet → "
                      "no Quran-specific RS structure; the signal is a "
                      "universal UTF-8 artifact.")
elif quran_utf8_sig and poetry_utf8_sig and quran_compact_sig:
    verdict = "NULL_ARABIC_GENERIC"
    interpretation = ("Signal present on all three arms → the test picks up "
                      "generic Arabic-language statistical structure, not RS "
                      "codeword structure.  Classic null.")
elif quran_compact_sig and not poetry_utf8_sig:
    verdict = "RS_STRUCTURE_CANDIDATE"
    interpretation = ("Signal survives compact-alphabet stripping AND is "
                      "absent in Arabic control → potentially Quran-specific "
                      "RS-like structure.  REPLICATE before claiming.")
elif not quran_utf8_sig:
    verdict = "NULL_NO_RS_STRUCTURE"
    interpretation = ("No signal on Quran-UTF8.  Clean NULL closure.")
else:
    verdict = "AMBIGUOUS"
    interpretation = "Mixed pattern; see per-arm Fisher p-values."

print(f"\n[E18c] final verdict = {verdict}")

# --------------------------------------------------------------- JSON
report = {
    "experiment": "E18_reed_solomon_CONTROLS",
    "verdict": verdict,
    "focal_config": {"n": focal[0], "nsym": focal[1]},
    "arms": results,
    "focal_signals": {
        "quran_utf8_sig":    quran_utf8_sig,
        "quran_compact_sig": quran_compact_sig,
        "poetry_utf8_sig":   poetry_utf8_sig,
    },
    "interpretation": interpretation,
    "pre_registered_criteria": {
        "confound_rule": ("quran_utf8 + poetry_utf8 both significant AND "
                           "quran_compact not significant ⇒ NULL_UTF8_CONFOUND"),
        "genuine_rule": ("quran_compact significant AND poetry_utf8 not "
                          "significant ⇒ RS_STRUCTURE_CANDIDATE"),
    },
    "seed": SEED,
}
(OUT_DIR / "expE18_controls_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8"
)
print(f"[E18c] report: {OUT_DIR / 'expE18_controls_report.json'}")
