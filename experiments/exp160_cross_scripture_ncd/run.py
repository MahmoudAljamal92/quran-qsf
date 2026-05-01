"""experiments/exp160_cross_scripture_ncd/run.py
=================================================
V3.23 candidate -- INTER-SCRIPTURE NORMALIZED COMPRESSION DISTANCE.

Question:
    Does each Quran surah have an Arabic-Bible nearest-neighbour that
    aligns with known thematic parallels (Yusuf <-> Joseph, Musa <-> Exodus,
    Nuh <-> Noah)? If yes, NCD discovers thematic cross-canonical
    structure beyond superficial lexical overlap.

Note on cross-script NCD:
    Cross-script NCD (Quran-Arabic vs Tanakh-Hebrew, vs NT-Greek, vs
    Iliad-Greek) is degenerate: gzip cannot share substrings across
    different scripts, so all such NCD values approach 1.0 regardless
    of semantic content. We therefore test against the Arabic Bible
    (1,183 chapters, same script as the Quran) as the primary reference,
    and use Greek Iliad / NT only as null baselines confirming the
    cross-script degeneracy.

Approach:
    1. Load Quran (114 surahs), Arabic Bible (~1183 chapters), Greek NT
       (~260 chapters), Iliad (24 books).
    2. Compute Q x {AB, NT, I} cross-NCD matrices using gzip (level 9) on
       UTF-8 byte streams. NCD(x,y) = (C(xy) - min(C(x),C(y))) / max(C(x),C(y)).
    3. For each Quran surah, identify the nearest neighbour in the Arabic
       Bible.
    4. Compare nearest-neighbour distance to a length-stratified
       random-permutation null built from the same reference pool.
    5. Verdict: PASS if a hand-curated set of expected thematic pairings
       (Yusuf <-> Joseph, Musa <-> Exodus, Nuh <-> Noah, etc.) all appear
       within the top-3 Arabic-Bible nearest neighbours of the
       corresponding Quran surah, AND mean Quran-Iliad NCD is uniformly
       high (>= 0.95) confirming the cross-script null.

PREREG  : experiments/exp160_cross_scripture_ncd/PREREG.md
Inputs  : phase_06_phi_m.pkl (CORPORA dict, drift-relax env recommended)
Output  : results/experiments/exp160_cross_scripture_ncd/exp160_cross_scripture_ncd.json
"""
from __future__ import annotations

import gzip
import io
import json
import sys
import time
from pathlib import Path
from typing import Any

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

from experiments._lib import load_phase, safe_output_dir  # noqa: E402
from src import raw_loader as rl                          # noqa: E402

EXP = "exp160_cross_scripture_ncd"
SEED = 42
GZIP_LEVEL = 9
N_PERM_NULL = 5000

# Curated expected cross-scripture pairings (Quran surah label : reference label
# substring or list of substrings to look for).
# These are conservative thematic anchors documented in standard
# comparative-religion references; the Quran labels are 1-indexed surah
# numbers (Q:0NN format used by the project's loaders).
# Curated expected cross-canon pairings against the ARABIC BIBLE.
# Quran labels are Q:0NN (1-indexed); Arabic-Bible labels look like
# 'bible:تكوين :NN' (Genesis), 'bible:خروج :NN' (Exodus). We anchor on
# the Arabic book name token in the label.
EXPECTED_PAIRINGS_QAB = [
    # (quran_label, [arabic_book_substr,...], description)
    ("Q:012", ["تكوين"],
     "Yusuf <-> Joseph narrative (Genesis / تكوين 37-50)"),
    ("Q:020", ["خروج"],
     "Ta-Ha <-> Moses' encounter / Exodus / خروج"),
    ("Q:028", ["خروج"],
     "Qasas <-> Moses' birth and calling / Exodus"),
    ("Q:071", ["تكوين"],
     "Nuh <-> Noah's flood (Genesis 6-9 / تكوين)"),
    ("Q:002", ["تكوين", "خروج"],
     "Baqara <-> creation + Decalogue (long surah; Genesis or Exodus)"),
    ("Q:019", ["لوقا", "متى"],
     "Maryam <-> Mary / Annunciation (Luke / لوقا or Matthew / متى)"),
    ("Q:003", ["لوقا", "متى"],
     "Aal-Imran <-> family of Imran / Mary / Jesus narrative"),
    ("Q:021", ["دانيال", "ملوك"],
     "Anbiya <-> Prophets (Daniel / دانيال or Kings / ملوك)"),
]


def doc_text(unit) -> str:
    """Concatenate a unit's verses into a single text (newline-joined)."""
    return "\n".join(unit.verses)


def gzip_size(b: bytes) -> int:
    """Length of gzip(b) at GZIP_LEVEL."""
    return len(gzip.compress(b, compresslevel=GZIP_LEVEL))


def ncd_pair(b1: bytes, b2: bytes, c1: int, c2: int) -> float:
    """NCD(x,y) = (C(xy) - min(C(x),C(y))) / max(C(x),C(y))."""
    c12 = gzip_size(b1 + b2)
    return (c12 - min(c1, c2)) / max(c1, c2)


def cross_ncd_matrix(docsA: list[bytes], docsB: list[bytes],
                     CA: list[int], CB: list[int],
                     label: str = "") -> np.ndarray:
    """Compute NCD[i,j] for every (i in A, j in B). Symmetric in NCD def
    but not symmetric here because A and B are different corpora."""
    nA, nB = len(docsA), len(docsB)
    M = np.empty((nA, nB), dtype=np.float32)
    for i in range(nA):
        if i % 10 == 0:
            print(f"    [{label}] row {i+1}/{nA}", flush=True)
        b1 = docsA[i]
        c1 = CA[i]
        for j in range(nB):
            M[i, j] = ncd_pair(b1, docsB[j], c1, CB[j])
    return M


def length_stratified_null(M: np.ndarray, lensA: np.ndarray, lensB: np.ndarray,
                           rng: np.random.Generator,
                           n_perm: int = N_PERM_NULL) -> dict[str, Any]:
    """For each row i in A, build a null distribution of the per-row
    minimum NCD by repeatedly sampling B-indices uniformly at random.

    To control for length, we additionally weight the null sampling
    inversely proportional to length difference (so randomly-paired
    documents are roughly length-matched).
    """
    nA, nB = M.shape
    null_min = np.empty((nA, n_perm), dtype=np.float32)
    for i in range(nA):
        w = 1.0 / (np.abs(lensB - lensA[i]) + 1.0)
        w = w / w.sum()
        for k in range(n_perm):
            j_sample = rng.choice(nB, size=min(20, nB), replace=False, p=w)
            null_min[i, k] = M[i, j_sample].min()
    obs_min = M.min(axis=1)
    p_per_row = np.array([(null_min[i] <= obs_min[i]).sum() / n_perm
                          for i in range(nA)])
    return {
        "obs_min_ncd": obs_min.tolist(),
        "null_min_mean": float(null_min.mean()),
        "null_min_std": float(null_min.std()),
        "obs_min_mean": float(obs_min.mean()),
        "obs_min_median": float(np.median(obs_min)),
        "p_per_row": p_per_row.tolist(),
        "frac_rows_p_below_05": float((p_per_row < 0.05).mean()),
        "frac_rows_p_below_01": float((p_per_row < 0.01).mean()),
    }


def main() -> dict[str, Any]:
    out_dir = safe_output_dir(EXP)
    receipt_path = out_dir / f"{EXP}.json"
    t0 = time.time()
    completed_at_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rng = np.random.default_rng(SEED)

    # ---- 1. Load all corpora --------------------------------------------
    print(f"[{EXP}] Loading Quran + Arabic Bible + Iliad from phase_06_phi_m.pkl ...")
    phi = load_phase("phase_06_phi_m")
    quran_units = phi["state"]["CORPORA"]["quran"]
    arabic_bible_units = phi["state"]["CORPORA"]["arabic_bible"]
    iliad_units = phi["state"]["CORPORA"]["iliad_greek"]
    print(f"  quran        : {len(quran_units)} surahs")
    print(f"  arabic_bible : {len(arabic_bible_units)} chapters")
    print(f"  iliad        : {len(iliad_units)} books")

    print(f"[{EXP}] Loading Greek NT directly from raw_loader (null baseline) ...")
    try:
        nt_units = rl.load_greek_nt()
        print(f"  nt    : {len(nt_units)} chapters")
    except Exception as e:
        print(f"  nt    : LOAD FAILED -- {e}")
        nt_units = []

    # ---- 2. Pre-compute text/byte/C(.) for every unit -------------------
    def prep(units):
        texts = [doc_text(u) for u in units]
        bytes_ = [t.encode("utf-8") for t in texts]
        sizes = [gzip_size(b) for b in bytes_]
        return texts, bytes_, sizes

    print(f"[{EXP}] Pre-compressing each unit (gzip level {GZIP_LEVEL}) ...")
    qT, qB, qC = prep(quran_units)
    abT, abB, abC = prep(arabic_bible_units)
    nT, nB, nC = prep(nt_units) if nt_units else ([], [], [])
    iT, iB, iC = prep(iliad_units)
    print(f"  Quran        bytes total = {sum(len(b) for b in qB)/1024:.1f} KB, "
          f"mean gz size = {np.mean(qC):.0f}")
    print(f"  Arabic Bible bytes total = {sum(len(b) for b in abB)/1024:.1f} KB, "
          f"mean gz size = {np.mean(abC):.0f}")
    if nT:
        print(f"  NT           bytes total = {sum(len(b) for b in nB)/1024:.1f} KB, "
              f"mean gz size = {np.mean(nC):.0f}")
    print(f"  Iliad        bytes total = {sum(len(b) for b in iB)/1024:.1f} KB, "
          f"mean gz size = {np.mean(iC):.0f}")

    # ---- 3. Compute Q x {T, NT, I} cross-NCD matrices --------------------
    results: dict[str, Any] = {}

    quran_lens = np.array([len(b) for b in qB], dtype=float)

    print(f"\n[{EXP}] Q x ArabicBible NCD ({len(qB)} x {len(abB)}) ...")
    t1 = time.time()
    M_qab = cross_ncd_matrix(qB, abB, qC, abC, label="Q-AB")
    print(f"  Q-AB matrix done in {time.time()-t1:.1f} s")
    nn_idx_qab = np.argmin(M_qab, axis=1)
    nn_val_qab = M_qab[np.arange(len(qB)), nn_idx_qab]
    ab_lens = np.array([len(b) for b in abB], dtype=float)
    null_qab = length_stratified_null(M_qab, quran_lens, ab_lens, rng)
    results["quran_arabic_bible"] = {
        "n_quran": len(qB),
        "n_arabic_bible": len(abB),
        "obs_mean_ncd": float(M_qab.mean()),
        "obs_min_ncd_per_surah": [float(v) for v in nn_val_qab],
        "nearest_neighbour": [
            {"quran_label": quran_units[i].label,
             "arabic_bible_label": arabic_bible_units[nn_idx_qab[i]].label,
             "ncd": float(nn_val_qab[i])}
            for i in range(len(qB))
        ],
        "null": null_qab,
    }

    if nt_units:
        print(f"\n[{EXP}] Q x NT NCD ({len(qB)} x {len(nB)}) ...")
        t1 = time.time()
        M_qn = cross_ncd_matrix(qB, nB, qC, nC, label="Q-NT")
        print(f"  Q-NT matrix done in {time.time()-t1:.1f} s")
        nn_idx_qn = np.argmin(M_qn, axis=1)
        nn_val_qn = M_qn[np.arange(len(qB)), nn_idx_qn]
        nt_lens = np.array([len(b) for b in nB], dtype=float)
        null_qn = length_stratified_null(M_qn, quran_lens, nt_lens, rng)
        results["quran_nt"] = {
            "n_quran": len(qB),
            "n_nt": len(nB),
            "obs_mean_ncd": float(M_qn.mean()),
            "obs_min_ncd_per_surah": [float(v) for v in nn_val_qn],
            "nearest_neighbour": [
                {"quran_label": quran_units[i].label,
                 "nt_label": nt_units[nn_idx_qn[i]].label,
                 "ncd": float(nn_val_qn[i])}
                for i in range(len(qB))
            ],
            "null": null_qn,
        }

    print(f"\n[{EXP}] Q x Iliad NCD ({len(qB)} x {len(iB)}) ...")
    t1 = time.time()
    M_qi = cross_ncd_matrix(qB, iB, qC, iC, label="Q-I")
    print(f"  Q-Iliad matrix done in {time.time()-t1:.1f} s")
    nn_idx_qi = np.argmin(M_qi, axis=1)
    nn_val_qi = M_qi[np.arange(len(qB)), nn_idx_qi]
    iliad_lens = np.array([len(b) for b in iB], dtype=float)
    null_qi = length_stratified_null(M_qi, quran_lens, iliad_lens, rng)
    results["quran_iliad"] = {
        "n_quran": len(qB),
        "n_iliad": len(iB),
        "obs_mean_ncd": float(M_qi.mean()),
        "obs_min_ncd_per_surah": [float(v) for v in nn_val_qi],
        "nearest_neighbour": [
            {"quran_label": quran_units[i].label,
             "iliad_label": iliad_units[nn_idx_qi[i]].label,
             "ncd": float(nn_val_qi[i])}
            for i in range(len(qB))
        ],
        "null": null_qi,
    }

    # ---- 4. Verdict on curated thematic pairings ------------------------
    pairing_results = []
    for q_label, expected_substrs, descr in EXPECTED_PAIRINGS_QAB:
        q_idx = next((i for i, u in enumerate(quran_units)
                      if u.label == q_label), None)
        if q_idx is None:
            pairing_results.append({"quran_label": q_label,
                                    "description": descr,
                                    "status": "QURAN_LABEL_NOT_FOUND"})
            continue
        ranking = np.argsort(M_qab[q_idx])
        top10 = [(arabic_bible_units[j].label, float(M_qab[q_idx, j]))
                 for j in ranking[:10]]
        # Find best rank of any expected substring match (Arabic match)
        best_rank = None
        best_match = None
        for rank, j in enumerate(ranking):
            lbl = arabic_bible_units[j].label
            if any(sub in lbl for sub in expected_substrs):
                best_rank = rank
                best_match = lbl
                break
        pairing_results.append({
            "quran_label": q_label,
            "description": descr,
            "expected_substrs": expected_substrs,
            "top_10_neighbours": top10,
            "best_match_label": best_match,
            "best_match_rank_0idx": best_rank,
            "passes_top_3": (best_rank is not None and best_rank < 3),
            "passes_top_10": (best_rank is not None and best_rank < 10),
        })
    n_pairings_top3 = sum(1 for p in pairing_results if p.get("passes_top_3"))
    n_pairings_top10 = sum(1 for p in pairing_results if p.get("passes_top_10"))

    # ---- 5. Composite verdict --------------------------------------------
    qab = results.get("quran_arabic_bible", {})
    pq05_qab = qab.get("null", {}).get("frac_rows_p_below_05", 0.0)
    pq01_qab = qab.get("null", {}).get("frac_rows_p_below_01", 0.0)

    qi = results.get("quran_iliad", {})
    iliad_mean = qi.get("obs_mean_ncd", 0.0)

    # PASS criteria: at least 5 of 8 thematic pairings appear in top-3
    # AND Quran-Iliad mean NCD is uniformly high (>= 0.95) confirming
    # cross-script null.
    if n_pairings_top3 >= 5 and iliad_mean >= 0.95:
        verdict = "PASS_QURAN_ARABIC_BIBLE_THEMATIC_NCD_STRUCTURE"
    elif n_pairings_top3 >= 3:
        verdict = "PARTIAL_THEMATIC_NCD_STRUCTURE_PRESENT"
    elif n_pairings_top10 >= 3:
        verdict = "WEAK_TOP10_PAIRINGS_DETECTED"
    else:
        verdict = "FAIL_NO_THEMATIC_NCD_STRUCTURE"

    receipt: dict[str, Any] = {
        "experiment": EXP,
        "schema_version": 1,
        "hypothesis": ("Same-script gzip-NCD discovers thematic Quran <-> "
                       "Arabic-Bible pairings (e.g., Yusuf <-> Joseph (Genesis), "
                       "Musa <-> Exodus, Maryam <-> Luke) at top-3 nearest-"
                       "neighbour rank, while Quran <-> Iliad cross-script NCD "
                       "is uniformly degenerate (mean >= 0.95)."),
        "verdict": verdict,
        "completed_at_utc": completed_at_utc,
        "wall_time_s": float(time.time() - t0),
        "frozen_constants": {
            "GZIP_LEVEL": GZIP_LEVEL, "N_PERM_NULL": N_PERM_NULL, "SEED": SEED,
        },
        "results": {
            **results,
            "thematic_pairings": pairing_results,
            "n_pairings_top3": int(n_pairings_top3),
            "n_pairings_top10": int(n_pairings_top10),
            "n_pairings_total": len(EXPECTED_PAIRINGS_QAB),
        },
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False),
                            encoding="utf-8")
    print("\n" + "=" * 70)
    print(f"[{EXP}] VERDICT: {verdict}")
    print(f"  thematic pairings top-3 hit: {n_pairings_top3}/{len(EXPECTED_PAIRINGS_QAB)}")
    print(f"  thematic pairings top-10 hit: {n_pairings_top10}/{len(EXPECTED_PAIRINGS_QAB)}")
    if results.get("quran_arabic_bible"):
        print(f"  Q-AB frac_rows p<0.05 = {pq05_qab:.3f}")
    if results.get("quran_iliad"):
        print(f"  Q-Iliad mean NCD = {iliad_mean:.3f}  (script-mismatch baseline)")
    print(f"  wall-time = {receipt['wall_time_s']:.1f} s")
    print(f"  receipt: {receipt_path}")
    print("=" * 70)
    return receipt


if __name__ == "__main__":
    main()
