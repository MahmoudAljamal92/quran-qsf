"""exp175_surah_invariant_atlas — scan 18 candidate intrinsic
surah-level invariants; flag any with CV < 0.05 as Quran-internal
reference constants. Paradigm candidate = CV < 0.01 with theoretical
interpretation.

Operating principle: Quran is the reference. No external corpora.
"""
from __future__ import annotations
import gzip
import io
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
QURAN_VOCAL = ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt"
QURAN_BARE = ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"

# Arabic alphabet
ALPHABET_28 = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
ALPHABET_SET = set(ALPHABET_28)
NORMALISE = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه",
             "ء": "", "ؤ": "", "ئ": ""}


def normalise(text):
    return "".join(NORMALISE.get(ch, ch) for ch in text)


def letters_only(text):
    t = normalise(text)
    return "".join(ch for ch in t if ch in ALPHABET_SET)


# Sonority classes (from exp168)
VOWEL_DIAS = {"\u064E": (4,), "\u0650": (4,), "\u064F": (4,),
              "\u064B": (4, 2), "\u064C": (4, 2), "\u064D": (4, 2),
              "\u0670": (4,), "\u0653": (4,), "\u0655": (4,),
              "\u0656": (4,), "\u0657": (4,), "\u065E": (4,)}
GLIDE_LIQ = set("\u0648\u064A\u0644\u0631")
NASAL_L = set("\u0645\u0646")
ALEF = set("\u0627\u0671")
SHADDA = "\u0651"; SUKUN = "\u0652"


def _sonority(ch):
    if ch in ALEF: return 4
    if ch in GLIDE_LIQ: return 3
    if ch in NASAL_L: return 2
    cp = ord(ch)
    if 0x0621 <= cp <= 0x064A or ch == "\u0671": return 1
    return None


DROP_RANGES = [(0x0660, 0x0669), (0x066B, 0x066C), (0x06D6, 0x06ED), (0x200C, 0x200F)]
DROP_SINGLES = {0x00A0, 0x0640}


def is_dropped(ch):
    cp = ord(ch)
    if cp < 128: return True
    if cp in DROP_SINGLES: return True
    for lo, hi in DROP_RANGES:
        if lo <= cp <= hi: return True
    return False


def sonority_seq(text):
    out = []; last = None
    for ch in text:
        if ch in (" ", "\n", "\t", "\r") or is_dropped(ch) or ch == SUKUN:
            continue
        if ch == SHADDA:
            if last is not None: out.append(last)
            continue
        if ch in VOWEL_DIAS:
            for v in VOWEL_DIAS[ch]: out.append(v)
            continue
        cls = _sonority(ch)
        if cls is None: continue
        out.append(cls)
        if cls != 4: last = cls
    return np.asarray(out, dtype=np.int8)


# Rhyme classes (from exp172)
LONG_VOWEL_RS = set("\u0627\u0648\u064A\u0649\u0671\u0622")
NASAL_RS = set("\u0645\u0646")
LIQ_RS = set("\u0644\u0631")
CORONAL_RS = set("\u062A\u062B\u062F\u0630\u0632\u0633\u0634\u0635\u0636\u0637\u0638")
LABIAL_RS = set("\u0628\u0641")
DORSAL_RS = set("\u062C\u0643\u0642\u062E\u063A")
GUTTURAL_RS = set("\u062D\u0639\u0647\u0621\u0623\u0625\u0624\u0626")
TAA_MARBUTA = "\u0629"


def rhyme_class(letter):
    if letter in LONG_VOWEL_RS: return 0
    if letter in NASAL_RS: return 1
    if letter in LIQ_RS: return 2
    if letter in CORONAL_RS or letter == TAA_MARBUTA: return 3
    if letter in LABIAL_RS: return 4
    if letter in DORSAL_RS: return 5
    if letter in GUTTURAL_RS: return 6
    return None


def last_letter_raw(text):
    DR = [(0x0660, 0x0669), (0x066B, 0x066C), (0x06D6, 0x06ED), (0x200C, 0x200F),
          (0x064B, 0x065F), (0x0670, 0x0670)]
    DS = {0x00A0, 0x0640, 0x0651, 0x0652}
    for ch in reversed(text):
        if ch in (" ", "\n", "\t", "\r"): continue
        cp = ord(ch)
        if cp < 128: continue
        if cp in DS: continue
        drop = False
        for lo, hi in DR:
            if lo <= cp <= hi: drop = True; break
        if drop: continue
        if 0x0621 <= cp <= 0x064A or ch in ("\u0671", "\u0649"):
            return ch
    return None


# ──────────────────────────────────────────────────────────────────
# Per-surah invariants
# ──────────────────────────────────────────────────────────────────
def compute_invariants(surah_vocal_lines):
    """surah_vocal_lines: list of verse strings (vocalised, no 'surah|verse|' prefix)
       Returns dict of 18 invariants."""
    text_vocal = "\n".join(surah_vocal_lines)
    letters = letters_only(text_vocal)
    N = len(letters)
    if N < 20:
        return None

    counts = Counter(letters)
    total = sum(counts.values())
    p = np.array([counts.get(l, 0) for l in ALPHABET_28], dtype=float) / total
    p_nz = p[p > 0]

    # A1..A5
    H_1 = float(-(p_nz * np.log2(p_nz)).sum())
    p_max = float(p.max())
    H_inf = float(-np.log2(p_max))
    rényi_gap = float(H_1 - H_inf)
    C_Om = float(1 - H_1 / np.log2(28))

    # Bigram
    bigrams = [letters[i:i+2] for i in range(len(letters) - 1)]
    bcounts = Counter(bigrams)
    b_distinct_ratio = len(bcounts) / max(1, len(bigrams))
    b_p = np.array(list(bcounts.values()), dtype=float) / sum(bcounts.values())
    H_2 = float(-(b_p * np.log2(b_p)).sum())
    H2_over_H1 = H_2 / H_1 if H_1 > 0 else float("nan")

    # Sonority (needs vocalised text)
    S = sonority_seq(text_vocal)
    if len(S) < 10:
        rho_lag1 = float("nan"); alt_rate = float("nan"); vowel_frac = float("nan")
    else:
        s0 = S - S.mean()
        v = (s0 * s0).sum()
        rho_lag1 = float((s0[:-1] * s0[1:]).sum() / v) if v > 0 else float("nan")
        alt_rate = float((S[1:] != S[:-1]).mean())
        vowel_frac = float((S == 4).mean())

    # Verse-level
    verse_letters = [len(letters_only(v)) for v in surah_vocal_lines if letters_only(v)]
    if len(verse_letters) < 2:
        mean_vl = float("nan"); VL_CV = float("nan")
        rhyme_classes = []
    else:
        vl = np.asarray(verse_letters, dtype=float)
        mean_vl = float(vl.mean())
        VL_CV = float(vl.std() / vl.mean())
        # Extract verse-end rhyme class
        rhyme_classes = []
        for v in surah_vocal_lines:
            ll = last_letter_raw(v)
            if ll is None: continue
            c = rhyme_class(ll)
            if c is not None: rhyme_classes.append(c)

    if len(rhyme_classes) < 2:
        nasal_frac = float("nan"); H_EL = float("nan"); rhyme_purity = float("nan")
    else:
        rc = np.asarray(rhyme_classes)
        nasal_frac = float((rc == 1).mean())
        rc_counts = np.bincount(rc, minlength=7).astype(float)
        rc_p = rc_counts / rc_counts.sum()
        rc_nz = rc_p[rc_p > 0]
        H_EL = float(-(rc_nz * np.log2(rc_nz)).sum())
        rhyme_purity = float(rc_p.max())

    # Compression
    raw_bytes = text_vocal.encode("utf-8")
    gz_bytes = gzip.compress(raw_bytes, compresslevel=6)
    gz_ratio = len(gz_bytes) / max(1, len(raw_bytes))
    letter_compression_eff = H_1 / np.log2(28)
    redundancy = 1 - letter_compression_eff

    return {
        "A1_H_1": H_1,
        "A2_H_inf": H_inf,
        "A3_renyi_gap": rényi_gap,
        "A4_C_Omega": C_Om,
        "A5_p_max": p_max,
        "B1_bigram_distinct_ratio": b_distinct_ratio,
        "B2_H2_over_H1": H2_over_H1,
        "C1_rho_lag1": rho_lag1,
        "C2_alt_rate": alt_rate,
        "C3_vowel_frac": vowel_frac,
        "D1_mean_vl": mean_vl,
        "D2_VL_CV": VL_CV,
        "D3_nasal_frac": nasal_frac,
        "D4_H_EL": H_EL,
        "D5_rhyme_purity": rhyme_purity,
        "E1_gz_ratio": gz_ratio,
        "E2_letter_compression_eff": letter_compression_eff,
        "E3_redundancy": redundancy,
        "N_letters": N,
        "N_verses": len(verse_letters),
    }


# ──────────────────────────────────────────────────────────────────
# Shuffle null: permute letters within each surah (preserves multiset)
# ──────────────────────────────────────────────────────────────────
def compute_invariants_letter_shuffle(surah_vocal_lines, rng):
    """Shuffle letters within the surah while preserving verse structure
    (keep verse lengths fixed, shuffle only letter order)."""
    full_text = "\n".join(surah_vocal_lines)
    letters = list(letters_only(full_text))
    rng.shuffle(letters)
    # Rebuild verses with shuffled letters of the same per-verse length
    idx = 0
    shuffled_lines = []
    for v in surah_vocal_lines:
        per_verse = len(letters_only(v))
        if per_verse == 0:
            shuffled_lines.append("")
            continue
        shuffled_lines.append("".join(letters[idx:idx + per_verse]))
        idx += per_verse
    return compute_invariants(shuffled_lines)


def main():
    out_dir = ROOT / "results" / "experiments" / "exp175_surah_invariant_atlas"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[exp175] Loading surahs ...", flush=True)
    raw = QURAN_VOCAL.read_text(encoding="utf-8")
    surah_lines = {i: [] for i in range(1, 115)}
    for line in raw.splitlines():
        p = line.split("|", 2)
        if len(p) < 3 or not p[0].strip().isdigit():
            continue
        s = int(p[0])
        if 1 <= s <= 114:
            surah_lines[s].append(p[2])

    # Compute observed invariants per surah
    print("[exp175] Computing 18 candidate invariants per surah ...", flush=True)
    per_surah = {}
    for s in range(1, 115):
        inv = compute_invariants(surah_lines[s])
        if inv is not None:
            per_surah[s] = inv
    print(f"[exp175] {len(per_surah)} surahs with enough data", flush=True)

    invariant_keys = [k for k in list(per_surah[2].keys()) if k not in ("N_letters", "N_verses")]
    # Report CV per invariant
    print("\n[exp175] === per-invariant distribution across surahs ===", flush=True)
    summary = {}
    for key in invariant_keys:
        vals = np.array([per_surah[s][key] for s in sorted(per_surah.keys())
                         if np.isfinite(per_surah[s].get(key, np.nan))], dtype=float)
        if len(vals) < 10:
            continue
        mean = float(vals.mean()); std = float(vals.std())
        cv = float(std / abs(mean)) if mean != 0 else float("inf")
        summary[key] = {"n": int(len(vals)), "mean": mean, "std": std, "cv": cv,
                        "min": float(vals.min()), "max": float(vals.max())}
        flag = "<<< CV<0.01" if cv < 0.01 else ("<<< CV<0.05" if cv < 0.05 else ("<< CV<0.10" if cv < 0.10 else ""))
        print(f"  {key:35s}  n={len(vals):3d}  mean={mean:+.4f}  std={std:.4f}  CV={cv:.4f} {flag}", flush=True)

    # Sort by CV ascending
    sorted_by_cv = sorted(summary.items(), key=lambda kv: kv[1]["cv"])
    low_cv_candidates = [(k, v) for k, v in sorted_by_cv if v["cv"] < 0.05 and v["mean"] != 0]

    print(f"\n[exp175] tight invariants (CV < 0.05): {len(low_cv_candidates)}", flush=True)
    for k, v in low_cv_candidates:
        print(f"    {k:35s}  CV={v['cv']:.4f}  mean={v['mean']:+.4f}", flush=True)

    # Shuffle null for the low-CV candidates
    # For each candidate, compute the shuffled-CV over N_PERM permutations
    N_PERM = 1000
    print(f"\n[exp175] Shuffle null (N_PERM={N_PERM}, letter-permutation within each surah) ...", flush=True)
    shuffled_cv = {k: [] for k, _ in low_cv_candidates}
    t0 = time.time()
    rng = np.random.default_rng(20260501)
    for pi in range(N_PERM):
        # For each surah, shuffle letters and recompute ALL invariants
        per_perm_values = {k: [] for k, _ in low_cv_candidates}
        for s in per_surah.keys():
            inv_shuf = compute_invariants_letter_shuffle(surah_lines[s], rng)
            if inv_shuf is None:
                continue
            for k, _ in low_cv_candidates:
                v = inv_shuf.get(k, float("nan"))
                if np.isfinite(v):
                    per_perm_values[k].append(v)
        # Compute CV of each shuffled vector
        for k in shuffled_cv:
            vals = np.asarray(per_perm_values[k], dtype=float)
            if len(vals) > 10 and vals.mean() != 0:
                cv = float(vals.std() / abs(vals.mean()))
                shuffled_cv[k].append(cv)
        if (pi + 1) % 100 == 0:
            print(f"    [shuffle] {pi+1}/{N_PERM}  elapsed {time.time()-t0:.1f}s", flush=True)

    # p-value: observed CV vs shuffled CV distribution
    print("\n[exp175] === shuffle-null results for low-CV invariants ===", flush=True)
    paradigm_candidates = []
    strong_candidates = []
    for k, stats in low_cv_candidates:
        shuf_cvs = np.asarray(shuffled_cv[k])
        obs_cv = stats["cv"]
        p_low = float((1 + (shuf_cvs <= obs_cv).sum()) / (1 + len(shuf_cvs)))
        z = (obs_cv - shuf_cvs.mean()) / (shuf_cvs.std() + 1e-30)
        mark = ""
        if obs_cv < 0.01 and p_low < 0.01:
            mark = " ╔═ PARADIGM"
            paradigm_candidates.append(k)
        elif obs_cv < 0.05 and p_low < 0.01:
            mark = " ═ STRONG"
            strong_candidates.append(k)
        print(f"  {k:35s}  obs_CV={obs_cv:.4f}  shuf_CV={shuf_cvs.mean():.4f}±{shuf_cvs.std():.4f}  z={z:+.2f}  p(≤obs)={p_low:.4g}{mark}", flush=True)

    # Spearman against length and index
    print("\n[exp175] === length & position-drift check for low-CV invariants ===", flush=True)
    length_log = np.array([np.log10(per_surah[s]["N_letters"] + 1) for s in sorted(per_surah.keys())])
    idx_vec = np.array([s for s in sorted(per_surah.keys())])
    length_rhos = {}; idx_rhos = {}
    for k, _ in low_cv_candidates:
        vals = np.array([per_surah[s][k] for s in sorted(per_surah.keys())], dtype=float)
        mask = np.isfinite(vals)
        rho_L, _ = spearmanr(length_log[mask], vals[mask])
        rho_I, _ = spearmanr(idx_vec[mask], vals[mask])
        length_rhos[k] = float(rho_L); idx_rhos[k] = float(rho_I)
        print(f"  {k:35s}  ρ(log-len)={rho_L:+.4f}  ρ(idx)={rho_I:+.4f}", flush=True)

    # Verdict
    if len(paradigm_candidates) >= 1:
        verdict = f"PASS_PARADIGM_INVARIANT_{len(paradigm_candidates)}"
    elif len(strong_candidates) >= 3:
        verdict = f"PASS_STRONG_INVARIANTS_{len(strong_candidates)}"
    elif len(strong_candidates) >= 1:
        verdict = f"PASS_PARTIAL_{len(strong_candidates)}"
    else:
        verdict = "FAIL"

    print(f"\n[exp175] ╔══════════════════════════════════════════════", flush=True)
    print(f"[exp175] ║ VERDICT: {verdict}", flush=True)
    print(f"[exp175] ║ paradigm candidates (CV<0.01 & p<0.01): {paradigm_candidates}", flush=True)
    print(f"[exp175] ║ strong candidates (CV<0.05 & p<0.01):   {strong_candidates}", flush=True)
    print(f"[exp175] ╚══════════════════════════════════════════════", flush=True)

    receipt = {
        "experiment": "exp175_surah_invariant_atlas",
        "frozen_at": "2026-05-01",
        "verdict": verdict,
        "n_surahs": len(per_surah),
        "per_invariant_summary": summary,
        "low_CV_candidates": [k for k, _ in low_cv_candidates],
        "paradigm_candidates": paradigm_candidates,
        "strong_candidates": strong_candidates,
        "per_surah_values": {str(s): per_surah[s] for s in sorted(per_surah.keys())},
        "shuffle_null": {
            k: {
                "obs_cv": low_cv_candidates[i][1]["cv"] if i < len(low_cv_candidates) else None,
                "shuf_cv_mean": float(np.mean(shuffled_cv[k])) if shuffled_cv[k] else None,
                "shuf_cv_std": float(np.std(shuffled_cv[k])) if shuffled_cv[k] else None,
                "p_obs_le_shuf": float((1 + (np.asarray(shuffled_cv[k]) <= low_cv_candidates[i][1]["cv"]).sum()) / (1 + len(shuffled_cv[k]))) if shuffled_cv[k] else None,
            } for i, (k, _) in enumerate(low_cv_candidates)
        },
        "length_robustness": length_rhos,
        "idx_drift": idx_rhos,
    }
    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False, default=float), encoding="utf-8")
    print(f"[exp175] receipt → {out_dir / 'receipt.json'}", flush=True)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # CV ranking bar chart
        keys = [k for k, _ in sorted_by_cv]
        cvs = [summary[k]["cv"] for k in keys]
        fig, ax = plt.subplots(figsize=(11, 7))
        colors = ["#2e7d32" if cv < 0.01 else ("#1976d2" if cv < 0.05 else ("#ffa000" if cv < 0.10 else "#888")) for cv in cvs]
        ax.barh(range(len(keys)), cvs, color=colors)
        ax.set_yticks(range(len(keys)))
        ax.set_yticklabels(keys, fontsize=8)
        ax.axvline(0.01, color="#2e7d32", linestyle="--", label="CV=0.01 paradigm")
        ax.axvline(0.05, color="#1976d2", linestyle="--", label="CV=0.05 strong")
        ax.axvline(0.10, color="#ffa000", linestyle="--", label="CV=0.10 loose")
        ax.set_xscale("log")
        ax.set_xlabel("CV (log scale)")
        ax.set_title(f"exp175: 18 candidate surah-invariants ranked by CV — {verdict}")
        ax.legend()
        ax.invert_yaxis()
        fig.tight_layout()
        fig.savefig(out_dir / "fig_cv_ranking.png", dpi=120)
        plt.close(fig)

        # Per-surah scatter for top-6 low-CV candidates
        top6 = [k for k, _ in sorted_by_cv[:6]]
        fig, axes = plt.subplots(2, 3, figsize=(14, 8))
        for ax, k in zip(axes.flat, top6):
            vals = np.array([per_surah[s][k] for s in sorted(per_surah.keys())], dtype=float)
            idx = np.array(sorted(per_surah.keys()))
            mask = np.isfinite(vals)
            ax.plot(idx[mask], vals[mask], "o", color="#1976d2", markersize=3)
            ax.axhline(summary[k]["mean"], color="r", linestyle="--",
                       label=f"mean={summary[k]['mean']:.4f}  CV={summary[k]['cv']:.4f}")
            ax.set_xlabel("surah"); ax.set_ylabel(k)
            ax.set_title(k)
            ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
        fig.suptitle(f"exp175: top-6 tightest surah invariants — {verdict}")
        fig.tight_layout()
        fig.savefig(out_dir / "fig_top6_invariants.png", dpi=120)
        plt.close(fig)
        print(f"[exp175] figures → {out_dir}", flush=True)
    except Exception as e:
        print(f"[exp175] fig skip: {e}", flush=True)


if __name__ == "__main__":
    main()
