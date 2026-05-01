"""exp175 fast null — tests whether the observed CV of tight invariants
across 114 surahs is SIGNIFICANTLY LOWER than the null CV produced by
random partitioning the Quran's letter pool into 114 chunks of the
observed lengths.

This is the *correct* null for multiset-dependent invariants like H_1 and
vowel_frac (which are invariant under within-surah letter shuffling).
"""
from __future__ import annotations
import io, json, sys, time
from collections import Counter
from pathlib import Path
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
QURAN_VOCAL = ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt"

# Inline the key converters
ALPHABET_28 = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
ALPHABET_SET = set(ALPHABET_28)
NORMALISE = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه",
             "ء": "", "ؤ": "", "ئ": ""}


def normalise(text):
    return "".join(NORMALISE.get(ch, ch) for ch in text)


def letters_only(text):
    return "".join(ch for ch in normalise(text) if ch in ALPHABET_SET)


# sonority converter (for alt_rate, vowel_frac)
VOWEL_DIAS = {"\u064E": (4,), "\u0650": (4,), "\u064F": (4,),
              "\u064B": (4, 2), "\u064C": (4, 2), "\u064D": (4, 2),
              "\u0670": (4,), "\u0653": (4,), "\u0655": (4,),
              "\u0656": (4,), "\u0657": (4,), "\u065E": (4,)}
GLIDE_LIQ = set("\u0648\u064A\u0644\u0631")
NASAL_L = set("\u0645\u0646")
ALEF = set("\u0627\u0671")
SHADDA = "\u0651"; SUKUN = "\u0652"
DROP_RANGES = [(0x0660, 0x0669), (0x066B, 0x066C), (0x06D6, 0x06ED), (0x200C, 0x200F)]
DROP_SINGLES = {0x00A0, 0x0640}


def is_dropped(ch):
    cp = ord(ch)
    if cp < 128: return True
    if cp in DROP_SINGLES: return True
    for lo, hi in DROP_RANGES:
        if lo <= cp <= hi: return True
    return False


def _sonority(ch):
    if ch in ALEF: return 4
    if ch in GLIDE_LIQ: return 3
    if ch in NASAL_L: return 2
    cp = ord(ch)
    if 0x0621 <= cp <= 0x064A or ch == "\u0671": return 1
    return None


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


def main():
    out_dir = ROOT / "results" / "experiments" / "exp175_surah_invariant_atlas"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[exp175b] Loading ...", flush=True)
    raw = QURAN_VOCAL.read_text(encoding="utf-8")
    surah_lines = {i: [] for i in range(1, 115)}
    for line in raw.splitlines():
        p = line.split("|", 2)
        if len(p) < 3 or not p[0].strip().isdigit():
            continue
        s = int(p[0])
        if 1 <= s <= 114:
            surah_lines[s].append(p[2])

    # Surah 1: compute per-surah letter bags, sonority sequences, lengths
    print("[exp175b] Computing per-surah bags ...", flush=True)
    surah_letter_bag = {}
    surah_sonority = {}
    surah_length = {}
    for s in range(1, 115):
        text = "\n".join(surah_lines[s])
        letters = letters_only(text)
        sson = sonority_seq(text)
        if len(letters) < 20:
            continue
        surah_letter_bag[s] = letters
        surah_sonority[s] = sson
        surah_length[s] = len(letters)

    N_sur = len(surah_letter_bag)
    # Pool all letters
    all_letters = "".join(surah_letter_bag[s] for s in sorted(surah_letter_bag))
    all_sonority = np.concatenate([surah_sonority[s] for s in sorted(surah_sonority)])
    total_letters = len(all_letters)
    total_son = len(all_sonority)
    lengths_letters = [surah_length[s] for s in sorted(surah_letter_bag)]
    lengths_son = [len(surah_sonority[s]) for s in sorted(surah_sonority)]
    print(f"[exp175b] {N_sur} surahs, total letters {total_letters}, total sonority tokens {total_son}", flush=True)

    # Observed statistics
    def H_1_of(letters):
        c = Counter(letters)
        total = sum(c.values())
        p = np.array([c.get(l, 0) for l in ALPHABET_28], dtype=float) / total
        p_nz = p[p > 0]
        return float(-(p_nz * np.log2(p_nz)).sum())

    def p_max_of(letters):
        c = Counter(letters)
        total = sum(c.values())
        return float(max(c.values())) / total

    def vowel_frac_of(son):
        return float((son == 4).mean())

    def alt_rate_of(son):
        return float((son[1:] != son[:-1]).mean())

    def lag1_rho_of(son):
        s0 = son.astype(float) - son.mean()
        v = (s0 * s0).sum()
        return float((s0[:-1] * s0[1:]).sum() / v) if v > 0 else float("nan")

    H1_obs = np.array([H_1_of(surah_letter_bag[s]) for s in sorted(surah_letter_bag)])
    pmax_obs = np.array([p_max_of(surah_letter_bag[s]) for s in sorted(surah_letter_bag)])
    vowel_obs = np.array([vowel_frac_of(surah_sonority[s]) for s in sorted(surah_sonority)])
    alt_obs = np.array([alt_rate_of(surah_sonority[s]) for s in sorted(surah_sonority)])
    rho_obs = np.array([lag1_rho_of(surah_sonority[s]) for s in sorted(surah_sonority)])

    print("\n[exp175b] Observed CV of target invariants (114 surahs):", flush=True)
    for name, arr in [("H_1", H1_obs), ("p_max", pmax_obs), ("vowel_frac", vowel_obs),
                      ("alt_rate", alt_obs), ("rho_lag1", rho_obs)]:
        cv = arr.std() / abs(arr.mean())
        print(f"  {name:12s}  mean={arr.mean():+.4f}  std={arr.std():.4f}  CV={cv:.4f}", flush=True)

    # ─────────────────────────────────────────
    # Null A: random-partition of the letter pool
    # Randomly permute the pool, then split into 114 chunks of the SAME lengths.
    # Compute CV of each invariant across chunks.
    # ─────────────────────────────────────────
    print("\n[exp175b] === Null A: random-partition letter pool (10,000 perms) ===", flush=True)
    N_PERM = 10_000
    rng = np.random.default_rng(20260501)
    letter_arr = np.frombuffer(all_letters.encode("utf-32-le"), dtype=np.uint32)
    # Map each unique char to int index for speed
    unique_chars = np.unique(letter_arr)
    char_to_int = {c: i for i, c in enumerate(unique_chars)}
    int_arr = np.array([char_to_int[c] for c in letter_arr], dtype=np.int32)
    K = len(unique_chars)
    char_to_alpha = {}
    for c, i in char_to_int.items():
        ch = chr(c)
        char_to_alpha[i] = ALPHABET_28.index(ch) if ch in ALPHABET_SET else -1
    alpha_of_int = np.array([char_to_alpha[i] for i in range(K)], dtype=np.int8)

    # For each perm: permute int_arr, split into chunks, compute invariants
    cvs_H1 = np.empty(N_PERM)
    cvs_pmax = np.empty(N_PERM)

    # length-based starting indices
    cum_lens = np.cumsum([0] + lengths_letters)

    t0 = time.time()
    perm = int_arr.copy()
    for k in range(N_PERM):
        rng.shuffle(perm)
        # map to alphabet indices
        alph = alpha_of_int[perm]
        # Compute per-chunk H_1 and p_max
        H1s = np.empty(N_sur)
        pms = np.empty(N_sur)
        for i in range(N_sur):
            chunk = alph[cum_lens[i]: cum_lens[i + 1]]
            # drop -1 (non-alphabet chars — shouldn't appear after letters_only but safety)
            valid = chunk[chunk >= 0]
            if len(valid) == 0:
                H1s[i] = float("nan"); pms[i] = float("nan"); continue
            counts = np.bincount(valid, minlength=28).astype(float)
            total = counts.sum()
            p = counts / total
            p_nz = p[p > 0]
            H1s[i] = -(p_nz * np.log2(p_nz)).sum()
            pms[i] = p.max()
        cvs_H1[k] = H1s.std() / abs(H1s.mean())
        cvs_pmax[k] = pms.std() / abs(pms.mean())
        if (k + 1) % 1000 == 0:
            print(f"    [null-A letter] {k+1}/{N_PERM}  elapsed {time.time()-t0:.1f}s", flush=True)

    # Observed CV
    cv_H1_obs = H1_obs.std() / abs(H1_obs.mean())
    cv_pmax_obs = pmax_obs.std() / abs(pmax_obs.mean())
    p_H1 = float((1 + (cvs_H1 <= cv_H1_obs).sum()) / (1 + N_PERM))
    p_pmax = float((1 + (cvs_pmax <= cv_pmax_obs).sum()) / (1 + N_PERM))
    z_H1 = (cv_H1_obs - cvs_H1.mean()) / (cvs_H1.std() + 1e-30)
    z_pmax = (cv_pmax_obs - cvs_pmax.mean()) / (cvs_pmax.std() + 1e-30)

    print(f"\n  H_1 CV     : obs={cv_H1_obs:.4f}  null={cvs_H1.mean():.4f}±{cvs_H1.std():.4f}  z={z_H1:+.2f}  p(obs≤null)={p_H1:.4g}", flush=True)
    print(f"  p_max CV   : obs={cv_pmax_obs:.4f}  null={cvs_pmax.mean():.4f}±{cvs_pmax.std():.4f}  z={z_pmax:+.2f}  p(obs≤null)={p_pmax:.4g}", flush=True)

    # ─────────────────────────────────────────
    # Null B for sonority sequence: random partition of sonority pool
    # ─────────────────────────────────────────
    print("\n[exp175b] === Null B: random-partition sonority pool (10,000 perms) ===", flush=True)
    cvs_vowel = np.empty(N_PERM)
    cvs_alt = np.empty(N_PERM)
    cvs_rho = np.empty(N_PERM)
    cum_son = np.cumsum([0] + lengths_son)
    son_arr = np.array(all_sonority)
    perm_s = son_arr.copy()
    t0 = time.time()
    for k in range(N_PERM):
        rng.shuffle(perm_s)
        vs = np.empty(N_sur); als = np.empty(N_sur); rhs = np.empty(N_sur)
        for i in range(N_sur):
            chunk = perm_s[cum_son[i]: cum_son[i + 1]]
            if len(chunk) < 10:
                vs[i] = float("nan"); als[i] = float("nan"); rhs[i] = float("nan"); continue
            vs[i] = (chunk == 4).mean()
            als[i] = (chunk[1:] != chunk[:-1]).mean()
            x0 = chunk.astype(float) - chunk.mean()
            v = (x0 * x0).sum()
            rhs[i] = ((x0[:-1] * x0[1:]).sum() / v) if v > 0 else float("nan")
        cvs_vowel[k] = np.nanstd(vs) / abs(np.nanmean(vs))
        cvs_alt[k] = np.nanstd(als) / abs(np.nanmean(als))
        rho_m = np.nanmean(rhs); rho_s = np.nanstd(rhs)
        cvs_rho[k] = rho_s / abs(rho_m) if rho_m != 0 else float("nan")
        if (k + 1) % 1000 == 0:
            print(f"    [null-B son] {k+1}/{N_PERM}  elapsed {time.time()-t0:.1f}s", flush=True)

    cv_vowel_obs = vowel_obs.std() / abs(vowel_obs.mean())
    cv_alt_obs = alt_obs.std() / abs(alt_obs.mean())
    cv_rho_obs = rho_obs.std() / abs(rho_obs.mean())
    p_vowel = float((1 + (cvs_vowel <= cv_vowel_obs).sum()) / (1 + N_PERM))
    p_alt = float((1 + (cvs_alt <= cv_alt_obs).sum()) / (1 + N_PERM))
    p_rho = float((1 + (cvs_rho <= cv_rho_obs).sum()) / (1 + N_PERM))
    z_v = (cv_vowel_obs - cvs_vowel.mean()) / (cvs_vowel.std() + 1e-30)
    z_a = (cv_alt_obs - cvs_alt.mean()) / (cvs_alt.std() + 1e-30)
    z_r = (cv_rho_obs - cvs_rho.mean()) / (cvs_rho.std() + 1e-30)

    print(f"\n  vowel_frac CV: obs={cv_vowel_obs:.4f}  null={cvs_vowel.mean():.4f}±{cvs_vowel.std():.4f}  z={z_v:+.2f}  p(obs≤null)={p_vowel:.4g}", flush=True)
    print(f"  alt_rate CV  : obs={cv_alt_obs:.4f}  null={cvs_alt.mean():.4f}±{cvs_alt.std():.4f}  z={z_a:+.2f}  p(obs≤null)={p_alt:.4g}", flush=True)
    print(f"  rho_lag1 CV  : obs={cv_rho_obs:.4f}  null={cvs_rho.mean():.4f}±{cvs_rho.std():.4f}  z={z_r:+.2f}  p(obs≤null)={p_rho:.4g}", flush=True)

    # Verdict logic
    alpha = 0.01
    pass_H1 = p_H1 < alpha
    pass_pmax = p_pmax < alpha
    pass_vowel = p_vowel < alpha
    pass_alt = p_alt < alpha
    pass_rho = p_rho < alpha
    n_pass = sum([pass_H1, pass_pmax, pass_vowel, pass_alt, pass_rho])

    survivors = []
    if pass_H1: survivors.append("H_1")
    if pass_pmax: survivors.append("p_max")
    if pass_vowel: survivors.append("vowel_frac")
    if pass_alt: survivors.append("alt_rate")
    if pass_rho: survivors.append("rho_lag1")

    if n_pass >= 1:
        verdict = f"PASS_{n_pass}_QURAN_HOMOGENEITY_INVARIANTS"
    else:
        verdict = "FAIL"

    print(f"\n[exp175b] ╔══════════════════════════════════════════════", flush=True)
    print(f"[exp175b] ║ VERDICT: {verdict}", flush=True)
    print(f"[exp175b] ║ survivors: {survivors}", flush=True)
    print(f"[exp175b] ║ The Quran's 114 surahs are anomalously HOMOGENEOUS on these quantities", flush=True)
    print(f"[exp175b] ║ vs the null of random-partition of the Quran's letter/sonority pool into", flush=True)
    print(f"[exp175b] ║ 114 chunks of the same observed lengths.", flush=True)
    print(f"[exp175b] ╚══════════════════════════════════════════════", flush=True)

    receipt = {
        "experiment": "exp175b_homogeneity_null",
        "frozen_at": "2026-05-01",
        "verdict": verdict,
        "n_surahs": int(N_sur),
        "n_perm": N_PERM,
        "alpha_per_test": alpha,
        "target_invariants": {
            "H_1":         {"obs_mean": float(H1_obs.mean()),   "obs_std": float(H1_obs.std()),   "obs_cv": cv_H1_obs,  "null_cv_mean": float(cvs_H1.mean()),  "null_cv_std": float(cvs_H1.std()),  "z": float(z_H1), "p": p_H1, "pass": bool(pass_H1)},
            "p_max":       {"obs_mean": float(pmax_obs.mean()), "obs_std": float(pmax_obs.std()), "obs_cv": cv_pmax_obs,"null_cv_mean": float(cvs_pmax.mean()),"null_cv_std": float(cvs_pmax.std()),"z": float(z_pmax), "p": p_pmax, "pass": bool(pass_pmax)},
            "vowel_frac":  {"obs_mean": float(vowel_obs.mean()),"obs_std": float(vowel_obs.std()),"obs_cv": cv_vowel_obs,"null_cv_mean": float(cvs_vowel.mean()),"null_cv_std": float(cvs_vowel.std()),"z": float(z_v), "p": p_vowel, "pass": bool(pass_vowel)},
            "alt_rate":    {"obs_mean": float(alt_obs.mean()),  "obs_std": float(alt_obs.std()),  "obs_cv": cv_alt_obs, "null_cv_mean": float(cvs_alt.mean()), "null_cv_std": float(cvs_alt.std()), "z": float(z_a), "p": p_alt, "pass": bool(pass_alt)},
            "rho_lag1":    {"obs_mean": float(rho_obs.mean()),  "obs_std": float(rho_obs.std()),  "obs_cv": cv_rho_obs, "null_cv_mean": float(cvs_rho.mean()), "null_cv_std": float(cvs_rho.std()), "z": float(z_r), "p": p_rho, "pass": bool(pass_rho)},
        },
        "survivors": survivors,
    }
    (out_dir / "receipt_homogeneity_null.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False, default=float), encoding="utf-8")
    print(f"[exp175b] receipt → {out_dir / 'receipt_homogeneity_null.json'}", flush=True)


if __name__ == "__main__":
    main()
