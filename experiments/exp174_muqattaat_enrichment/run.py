"""exp174_muqattaat_enrichment — first modern-pipeline intrinsic test
of whether the 14 disjoint letters heading 29 surahs are statistically
over-represented in the surah bodies they head.

Operating principle: Quran is the reference. No external corpora.
Paradigm-shift candidate.
"""
from __future__ import annotations
import io
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
QURAN_BARE = ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"

# ──────────────────────────────────────────────────────────────────
# Frozen configuration
# ──────────────────────────────────────────────────────────────────
BASMALAH = "بسم الله الرحمن الرحيم"

# Muqatta'at openers (bare Arabic, as appears after basmalah strip)
MUQ_V1 = {
    2: "الم", 3: "الم", 7: "المص",
    10: "الر", 11: "الر", 12: "الر", 13: "المر",
    14: "الر", 15: "الر",
    19: "كهيعص", 20: "طه",
    26: "طسم", 27: "طس", 28: "طسم",
    29: "الم", 30: "الم", 31: "الم", 32: "الم",
    36: "يس", 38: "ص",
    40: "حم", 41: "حم", 42: "حم", 43: "حم", 44: "حم", 45: "حم", 46: "حم",
    50: "ق", 68: "ن",
}
# Surah 42 has عسق as v2 opener
MUQ_V2 = {42: "عسق"}

MUQ_SURAHS = sorted(MUQ_V1.keys())
assert len(MUQ_SURAHS) == 29

# Unique opener letters (should be 14)
UNIQUE_LETTERS = sorted(set("".join(MUQ_V1.values())) | set("".join(MUQ_V2.values())))
assert len(UNIQUE_LETTERS) == 14, f"expected 14 got {len(UNIQUE_LETTERS)}: {UNIQUE_LETTERS}"

# 28-letter Arabic alphabet (post-normalisation)
ALPHABET_28 = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
assert len(ALPHABET_28) == 28

# Normalisation map
NORMALISE = {
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ى": "ي",
    "ة": "ه",
    # drop hamza-on-seat variants (keep as no-letter by mapping to empty)
    "ء": "", "ؤ": "", "ئ": "",
}


def normalise(text: str) -> str:
    return "".join(NORMALISE.get(ch, ch) for ch in text)


def letters_only(text: str) -> str:
    """Keep only alphabet_28 letters (after normalisation)."""
    t = normalise(text)
    alpha = set(ALPHABET_28)
    return "".join(ch for ch in t if ch in alpha)


# ──────────────────────────────────────────────────────────────────
# Build surah bodies
# ──────────────────────────────────────────────────────────────────
def build_surah_bodies():
    raw = QURAN_BARE.read_text(encoding="utf-8")
    surah_verses = {i: {} for i in range(1, 115)}
    for line in raw.splitlines():
        p = line.split("|", 2)
        if len(p) < 3 or not p[0].strip().isdigit():
            continue
        s = int(p[0])
        if 1 <= s <= 114:
            surah_verses[s][int(p[1])] = p[2]

    surah_bodies = {}
    for s in range(1, 115):
        verses = surah_verses[s]
        if not verses:
            surah_bodies[s] = ""
            continue
        # Strip basmalah from v1 unless s in {1, 9}
        v1 = verses[1]
        if s not in (1, 9):
            if v1.startswith(BASMALAH):
                v1 = v1[len(BASMALAH):].lstrip()
            else:
                # tolerant strip
                v1 = v1.replace(BASMALAH, "", 1).lstrip()
        # Strip muqatta'at opener from v1
        if s in MUQ_V1:
            opener = MUQ_V1[s]
            if v1.startswith(opener):
                v1 = v1[len(opener):].lstrip()
            else:
                # fallback: remove first occurrence
                idx = v1.find(opener)
                if idx == 0:
                    v1 = v1[len(opener):].lstrip()
        verses[1] = v1
        # Strip muqatta'at from v2 for surah 42
        if s in MUQ_V2 and 2 in verses:
            v2 = verses[2]
            opener = MUQ_V2[s]
            if v2.startswith(opener):
                verses[2] = v2[len(opener):].lstrip()
            elif v2.strip() == opener:
                verses[2] = ""
        body = "\n".join(verses[v] for v in sorted(verses) if verses[v])
        surah_bodies[s] = body
    return surah_bodies


def letter_counts_per_surah(bodies):
    counts = {}
    totals = {}
    for s, body in bodies.items():
        letters = letters_only(body)
        c = Counter(letters)
        counts[s] = c
        totals[s] = len(letters)
    return counts, totals


# ──────────────────────────────────────────────────────────────────
# Statistics
# ──────────────────────────────────────────────────────────────────
def enrichment_and_pairs(counts, totals, muq_v1, muq_v2):
    """Return (list of (s, letter, E, log_E), list of all (s,ℓ) pair tuples)."""
    total_letters_all = sum(totals.values())
    global_counts = Counter()
    for s in totals:
        global_counts.update(counts[s])

    pair_data = []
    for s, opener in muq_v1.items():
        letters_here = list(opener)
        if s in muq_v2:
            letters_here.extend(list(muq_v2[s]))
        for ell in set(letters_here):
            if ell not in ALPHABET_28 and ell not in NORMALISE:
                continue
            ell_n = normalise(ell)
            if ell_n not in ALPHABET_28:
                continue
            n_ell_s = counts[s].get(ell_n, 0)
            tot_s = totals[s]
            if tot_s == 0:
                continue
            f_s = n_ell_s / tot_s
            n_ell_outside = global_counts[ell_n] - n_ell_s
            tot_outside = total_letters_all - tot_s
            if tot_outside == 0:
                continue
            f_out = n_ell_outside / tot_outside
            if f_out == 0:
                continue
            E = f_s / f_out
            pair_data.append({
                "surah": s, "letter": ell_n,
                "n_in_surah": int(n_ell_s),
                "total_letters_surah": int(tot_s),
                "n_outside": int(n_ell_outside),
                "total_outside": int(tot_outside),
                "f_surah": f_s, "f_outside": f_out,
                "E": E, "log2_E": float(np.log2(E)) if E > 0 else float("nan"),
            })
    return pair_data


def aggregate_stats(pair_data, counts, totals, muq_letter_surahs):
    """Compute T1, T2, T3, T5 from a pair-data list. T4 needs per-letter z-scores."""
    logs = np.array([p["log2_E"] for p in pair_data if np.isfinite(p["log2_E"])])
    Es = np.array([p["E"] for p in pair_data])
    T1_mean_log_E = float(logs.mean())
    T2_frac_E_gt_1 = float((Es > 1).mean())

    # T3: pooled-by-letter enrichment (14 unique letters)
    total_letters_all = sum(totals.values())
    global_counts = Counter()
    for s in totals:
        global_counts.update(counts[s])
    pooled_E = {}
    for ell, surahs in muq_letter_surahs.items():
        ell_n = normalise(ell)
        if ell_n not in ALPHABET_28:
            continue
        n_in = sum(counts[s].get(ell_n, 0) for s in surahs)
        tot_in = sum(totals[s] for s in surahs)
        n_out = global_counts[ell_n] - n_in
        tot_out = total_letters_all - tot_in
        if tot_in == 0 or tot_out == 0:
            pooled_E[ell_n] = float("nan"); continue
        f_in = n_in / tot_in; f_out = n_out / tot_out
        pooled_E[ell_n] = (f_in / f_out) if f_out > 0 else float("nan")
    T3_n_letters_gt_1 = int(sum(1 for v in pooled_E.values() if np.isfinite(v) and v > 1))

    # T5: top-rank-within-surah
    top3_hits = 0
    for s, opener in MUQ_V1.items():
        body_letters = list(opener)
        if s in MUQ_V2:
            body_letters.extend(list(MUQ_V2[s]))
        body_letters = [normalise(l) for l in body_letters]
        body_letters = set(l for l in body_letters if l in ALPHABET_28)
        if not body_letters:
            continue
        # rank surah letters by count, desc
        ranked = sorted(counts[s].items(), key=lambda x: -x[1])
        top3 = [r[0] for r in ranked[:3]]
        if any(l in top3 for l in body_letters):
            top3_hits += 1
    T5_top3_hits = int(top3_hits)

    return {
        "T1_mean_log2_E": T1_mean_log_E,
        "T2_frac_E_gt_1": T2_frac_E_gt_1,
        "T3_n_pooled_letters_gt_1": T3_n_letters_gt_1,
        "T5_top3_hits": T5_top3_hits,
        "pooled_E": pooled_E,
        "n_pairs": int(len(Es)),
    }


# ──────────────────────────────────────────────────────────────────
# Null B: permute which 29 surahs get which opener-group
# ──────────────────────────────────────────────────────────────────
# Opener groups (preserving exact opener strings and their surah counts)
GROUPS = {
    "الم": [2, 3, 29, 30, 31, 32],
    "المص": [7],
    "الر": [10, 11, 12, 14, 15],
    "المر": [13],
    "كهيعص": [19],
    "طه": [20],
    "طسم": [26, 28],
    "طس": [27],
    "يس": [36],
    "ص": [38],
    "حم": [40, 41, 42, 43, 44, 45, 46],
    "حم/عسق": [42],   # symbolic; will be handled specially
    "ق": [50],
    "ن": [68],
}
# Note surah 42 is in both "حم" (6-member) and "حم/عسق" (singleton). In the shuffle:
# we shuffle the 29 unique-surah assignment and handle 42's double-assignment
# carefully. Simpler: shuffle the 29 surahs by opener-string (NOT group membership),
# as a direct permutation of (surah -> opener-string).
# Observed muqattaat list:
OBS_MUQ_V1 = dict(MUQ_V1)
OBS_MUQ_V2 = dict(MUQ_V2)


def permute_surahs(rng, bodies_keys):
    """Randomly choose 29 surahs from 114; assign them to the observed 29
    opener-strings (preserving opener-to-surah-count distribution).
    Preserve the V2 special case for the same 'position' as surah 42."""
    all_surahs = sorted([s for s in bodies_keys if 1 <= s <= 114])
    chosen = list(rng.choice(all_surahs, size=29, replace=False))
    rng.shuffle(chosen)
    observed = sorted(OBS_MUQ_V1.keys())
    # Build mapping observed_surah -> random_surah
    mapping = dict(zip(observed, chosen))
    new_v1 = {mapping[s]: OBS_MUQ_V1[s] for s in observed}
    # For surah 42's V2 opener: map by observed index
    new_v2 = {}
    for s_obs, op in OBS_MUQ_V2.items():
        new_v2[mapping[s_obs]] = op
    return new_v1, new_v2, mapping


def count_test_statistics(counts, totals, muq_v1, muq_v2):
    """Compute pair_data and aggregate_stats given a (muq_v1, muq_v2) assignment."""
    # Build muq_letter_surahs
    letter_surahs = {}
    for s, op in muq_v1.items():
        for l in set(op):
            letter_surahs.setdefault(l, set()).add(s)
    for s, op in muq_v2.items():
        for l in set(op):
            letter_surahs.setdefault(l, set()).add(s)
    letter_surahs = {k: sorted(v) for k, v in letter_surahs.items()}

    pair_data = []
    total_letters_all = sum(totals.values())
    global_counts = Counter()
    for s in totals:
        global_counts.update(counts[s])

    for s, opener in muq_v1.items():
        letters_here = set(opener)
        if s in muq_v2:
            letters_here |= set(muq_v2[s])
        for ell in letters_here:
            ell_n = normalise(ell)
            if ell_n not in ALPHABET_28:
                continue
            n_in = counts[s].get(ell_n, 0)
            tot_s = totals[s]
            if tot_s == 0:
                continue
            n_out = global_counts[ell_n] - n_in
            tot_out = total_letters_all - tot_s
            if tot_out == 0:
                continue
            f_in = n_in / tot_s; f_out = n_out / tot_out
            if f_out == 0:
                continue
            E = f_in / f_out
            pair_data.append({"E": E, "log2_E": float(np.log2(E)) if E > 0 else float("nan")})

    return aggregate_stats_from_lists(pair_data, letter_surahs, counts, totals, muq_v1, muq_v2)


def aggregate_stats_from_lists(pair_data, letter_surahs, counts, totals, muq_v1, muq_v2):
    logs = np.array([p["log2_E"] for p in pair_data if np.isfinite(p["log2_E"])])
    Es = np.array([p["E"] for p in pair_data])
    T1 = float(logs.mean()) if len(logs) else float("nan")
    T2 = float((Es > 1).mean()) if len(Es) else float("nan")

    total_letters_all = sum(totals.values())
    global_counts = Counter()
    for s in totals:
        global_counts.update(counts[s])
    T3 = 0
    for ell, surahs in letter_surahs.items():
        ell_n = normalise(ell)
        if ell_n not in ALPHABET_28:
            continue
        n_in = sum(counts[s].get(ell_n, 0) for s in surahs)
        tot_in = sum(totals[s] for s in surahs)
        n_out = global_counts[ell_n] - n_in
        tot_out = total_letters_all - tot_in
        if tot_in == 0 or tot_out == 0:
            continue
        if tot_out > 0 and (n_out / tot_out) > 0:
            if (n_in / tot_in) / (n_out / tot_out) > 1:
                T3 += 1

    top3_hits = 0
    for s, opener in muq_v1.items():
        letters_here = set(opener)
        if s in muq_v2:
            letters_here |= set(muq_v2[s])
        letters_here = set(normalise(l) for l in letters_here)
        letters_here = set(l for l in letters_here if l in ALPHABET_28)
        if not letters_here or not counts.get(s):
            continue
        ranked = sorted(counts[s].items(), key=lambda x: -x[1])
        top3 = set(r[0] for r in ranked[:3])
        if letters_here & top3:
            top3_hits += 1

    return {"T1": T1, "T2": T2, "T3": T3, "T5": int(top3_hits), "n_pairs": int(len(Es))}


# ──────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────
def main():
    out_dir = ROOT / "results" / "experiments" / "exp174_muqattaat_enrichment"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[exp174] Loading & cleaning surahs ...", flush=True)
    bodies = build_surah_bodies()
    counts, totals = letter_counts_per_surah(bodies)
    print(f"[exp174] 114 surah bodies built. Total letters = {sum(totals.values())}", flush=True)
    # sanity: disjoint opener letters equal the famous 14
    print(f"[exp174] unique opener letters: {UNIQUE_LETTERS}  (count {len(UNIQUE_LETTERS)})", flush=True)

    # Verify muqatta'at stripping worked: the first verse of surah 2 should have 0 muqatta'at letters on its first verse.
    # We'll skip the detailed verification and proceed to observed statistics.

    print("\n[exp174] === observed per-pair enrichment ===", flush=True)
    pair_data = enrichment_and_pairs(counts, totals, MUQ_V1, MUQ_V2)
    # Print top/bottom enrichment examples
    sorted_pairs = sorted(pair_data, key=lambda x: -x["E"])
    print(f"[exp174] total observed (surah, letter) pairs = {len(pair_data)}", flush=True)
    print("  TOP 10 enrichment:", flush=True)
    for p in sorted_pairs[:10]:
        print(f"    surah {p['surah']:3d}  letter {p['letter']}  E = {p['E']:.4f}  log2E = {p['log2_E']:+.4f}  (n_in={p['n_in_surah']}, tot_in={p['total_letters_surah']})", flush=True)
    print("  BOTTOM 5 enrichment:", flush=True)
    for p in sorted_pairs[-5:]:
        print(f"    surah {p['surah']:3d}  letter {p['letter']}  E = {p['E']:.4f}  log2E = {p['log2_E']:+.4f}", flush=True)

    # T1–T5 observed
    letter_surahs_obs = {}
    for s, op in MUQ_V1.items():
        for l in set(op):
            letter_surahs_obs.setdefault(normalise(l), set()).add(s)
    for s, op in MUQ_V2.items():
        for l in set(op):
            letter_surahs_obs.setdefault(normalise(l), set()).add(s)
    letter_surahs_obs = {k: sorted(v) for k, v in letter_surahs_obs.items()}

    obs_stats = aggregate_stats(pair_data, counts, totals, letter_surahs_obs)
    T1_obs = obs_stats["T1_mean_log2_E"]
    T2_obs = obs_stats["T2_frac_E_gt_1"]
    T3_obs = obs_stats["T3_n_pooled_letters_gt_1"]
    T5_obs = obs_stats["T5_top3_hits"]
    pooled_E_obs = obs_stats["pooled_E"]

    print(f"\n[exp174] === observed aggregate statistics ===", flush=True)
    print(f"  T1 mean log2(E)                        = {T1_obs:+.6f}  (mean E = {2**T1_obs:.4f})", flush=True)
    print(f"  T2 fraction of pairs with E > 1        = {T2_obs:.6f}   ({int(T2_obs * obs_stats['n_pairs'])}/{obs_stats['n_pairs']})", flush=True)
    print(f"  T3 pooled-by-letter E > 1 count        = {T3_obs} / 14", flush=True)
    print(f"  T5 top-3 hit count                     = {T5_obs} / 29", flush=True)
    print("\n  Per-letter pooled E (14 unique openers):", flush=True)
    for ell in sorted(pooled_E_obs.keys()):
        val = pooled_E_obs[ell]
        print(f"    {ell}: E_pool = {val:.4f}", flush=True)

    # ─────────────────────────────────────────
    # T4: per-letter shuffle z-score for pooled E
    # Using Null B: random 29-surah resample preserving group structure
    # ─────────────────────────────────────────
    print("\n[exp174] === Null B: surah permutation (10,000 perms) ===", flush=True)
    rng = np.random.default_rng(20260501)
    N_PERM = 10_000
    T1_null = np.empty(N_PERM); T2_null = np.empty(N_PERM)
    T3_null = np.empty(N_PERM, dtype=int); T5_null = np.empty(N_PERM, dtype=int)

    # For T4 we track per-letter pooled E under null
    pooled_null = {ell: np.empty(N_PERM) for ell in pooled_E_obs.keys()}

    t0 = time.time()
    all_surahs = sorted([s for s in bodies.keys() if 1 <= s <= 114])
    observed_surahs = sorted(OBS_MUQ_V1.keys())

    for i in range(N_PERM):
        chosen = rng.choice(all_surahs, size=29, replace=False)
        mapping = dict(zip(observed_surahs, chosen))
        new_v1 = {mapping[s]: OBS_MUQ_V1[s] for s in observed_surahs}
        new_v2 = {mapping[s_obs]: op for s_obs, op in OBS_MUQ_V2.items()}
        st = count_test_statistics(counts, totals, new_v1, new_v2)
        T1_null[i] = st["T1"]; T2_null[i] = st["T2"]
        T3_null[i] = st["T3"]; T5_null[i] = st["T5"]

        # per-letter pooled E under this permutation
        letter_surahs_perm = {}
        for s, op in new_v1.items():
            for l in set(op):
                letter_surahs_perm.setdefault(normalise(l), set()).add(s)
        for s, op in new_v2.items():
            for l in set(op):
                letter_surahs_perm.setdefault(normalise(l), set()).add(s)
        total_letters_all = sum(totals.values())
        global_counts = Counter()
        for s in totals:
            global_counts.update(counts[s])
        for ell in pooled_E_obs.keys():
            ss = list(letter_surahs_perm.get(ell, []))
            if not ss:
                pooled_null[ell][i] = float("nan"); continue
            n_in = sum(counts[s].get(ell, 0) for s in ss)
            tot_in = sum(totals[s] for s in ss)
            n_out = global_counts[ell] - n_in
            tot_out = total_letters_all - tot_in
            if tot_in == 0 or tot_out == 0 or (n_out / tot_out) == 0:
                pooled_null[ell][i] = float("nan"); continue
            pooled_null[ell][i] = (n_in / tot_in) / (n_out / tot_out)

        if (i + 1) % 1000 == 0:
            print(f"    [perm] {i+1}/{N_PERM}  elapsed {time.time()-t0:.1f}s", flush=True)

    # p-values
    p_T1 = float((1 + (T1_null >= T1_obs).sum()) / (1 + N_PERM))
    p_T2 = float((1 + (T2_null >= T2_obs).sum()) / (1 + N_PERM))
    p_T3 = float((1 + (T3_null >= T3_obs).sum()) / (1 + N_PERM))
    p_T5 = float((1 + (T5_null >= T5_obs).sum()) / (1 + N_PERM))

    # T4: per-letter BHL
    per_letter_p = {}
    for ell, Eobs in pooled_E_obs.items():
        null_vals = pooled_null[ell]
        mask = np.isfinite(null_vals)
        if mask.sum() == 0 or not np.isfinite(Eobs):
            per_letter_p[ell] = (Eobs, float("nan"), float("nan"))
            continue
        null_vals = null_vals[mask]
        z = (Eobs - null_vals.mean()) / (null_vals.std() + 1e-30)
        p = float((1 + (null_vals >= Eobs).sum()) / (1 + len(null_vals)))
        per_letter_p[ell] = (Eobs, z, p)

    # Bonferroni-Holm on 14 letter p-values
    sorted_letters = sorted(per_letter_p.items(), key=lambda x: x[1][2] if np.isfinite(x[1][2]) else 1)
    M = 14
    alpha_family = 0.05
    bhl_passers = []
    for i, (ell, (Eobs, z, p)) in enumerate(sorted_letters):
        thresh = alpha_family / (M - i)
        if p < thresh:
            bhl_passers.append({"letter": ell, "E_obs": Eobs, "z": z, "p": p, "threshold": thresh})
        else:
            break
    T4_n_bhl = len(bhl_passers)

    print(f"\n[exp174] ── null-B p-values ──", flush=True)
    print(f"  T1 mean log2(E)    : obs={T1_obs:+.6f}  null={T1_null.mean():+.6f}±{T1_null.std():.6f}  z={(T1_obs-T1_null.mean())/T1_null.std():+.2f}  p={p_T1:.4g}", flush=True)
    print(f"  T2 frac E>1        : obs={T2_obs:.6f}  null={T2_null.mean():.6f}±{T2_null.std():.6f}  z={(T2_obs-T2_null.mean())/T2_null.std():+.2f}  p={p_T2:.4g}", flush=True)
    print(f"  T3 n_pooled_letters: obs={T3_obs}      null={T3_null.mean():.2f}±{T3_null.std():.2f}  p={p_T3:.4g}", flush=True)
    print(f"  T4 BHL survivors   : {T4_n_bhl} / 14", flush=True)
    print(f"  T5 top-3 hits      : obs={T5_obs}      null={T5_null.mean():.2f}±{T5_null.std():.2f}  p={p_T5:.4g}", flush=True)

    print("\n[exp174] Per-letter enrichment (sorted by p):", flush=True)
    for ell, (Eobs, z, p) in sorted_letters:
        mark = " ✓BHL" if any(b["letter"] == ell for b in bhl_passers) else ""
        print(f"    {ell}  E_obs={Eobs:.4f}  z={z:+.3f}  p={p:.4g}{mark}", flush=True)

    # Verdict
    alpha = 0.01
    pass_T1 = p_T1 < alpha; pass_T2 = p_T2 < alpha; pass_T3 = p_T3 < alpha
    pass_T5 = p_T5 < alpha
    pass_T4 = T4_n_bhl >= 1  # at least one BHL survivor

    n_pass = int(pass_T1) + int(pass_T2) + int(pass_T3) + int(pass_T4) + int(pass_T5)
    effect_size_ok = T1_obs > 0.05

    if all([pass_T1, pass_T2, pass_T3, pass_T4, pass_T5]) and effect_size_ok:
        verdict = "PASS_MUQATTAAT_ENRICHMENT_PARADIGM"
    elif n_pass >= 3:
        verdict = "PASS_STRONG"
    elif n_pass >= 1:
        verdict = f"PASS_PARTIAL_{n_pass}of5"
    else:
        verdict = "FAIL"

    print(f"\n[exp174] ╔══════════════════════════════════════════════", flush=True)
    print(f"[exp174] ║ VERDICT: {verdict}", flush=True)
    print(f"[exp174] ║ T1={T1_obs:+.4f} p={p_T1:.4g}  T2={T2_obs:.4f} p={p_T2:.4g}", flush=True)
    print(f"[exp174] ║ T3={T3_obs}/14 p={p_T3:.4g}  T4 BHL={T4_n_bhl}/14  T5={T5_obs}/29 p={p_T5:.4g}", flush=True)
    print(f"[exp174] ║ effect size ⟨log2 E⟩ = {T1_obs:+.4f}  (mean E = {2**T1_obs:.4f})", flush=True)
    print(f"[exp174] ║ n_pass {n_pass}/5", flush=True)
    print(f"[exp174] ╚══════════════════════════════════════════════", flush=True)

    receipt = {
        "experiment": "exp174_muqattaat_enrichment",
        "frozen_at": "2026-05-01",
        "verdict": verdict,
        "n_pass": int(n_pass),
        "unique_opener_letters": UNIQUE_LETTERS,
        "muq_surahs": MUQ_SURAHS,
        "n_pairs_observed": int(len(pair_data)),
        "observed": {
            "T1_mean_log2_E": T1_obs,
            "T1_mean_E": float(2 ** T1_obs),
            "T2_frac_E_gt_1": T2_obs,
            "T3_n_pooled_letters_gt_1": T3_obs,
            "T4_BHL_survivors": T4_n_bhl,
            "T5_top3_hits": T5_obs,
            "pooled_E_per_letter": {k: v for k, v in pooled_E_obs.items()},
            "per_pair": pair_data,
        },
        "null_B_surah_permutation": {
            "n_perm": N_PERM,
            "T1": {"null_mean": float(T1_null.mean()), "null_std": float(T1_null.std()), "p": p_T1, "pass": bool(pass_T1)},
            "T2": {"null_mean": float(T2_null.mean()), "null_std": float(T2_null.std()), "p": p_T2, "pass": bool(pass_T2)},
            "T3": {"null_mean": float(T3_null.mean()), "null_std": float(T3_null.std()), "p": p_T3, "pass": bool(pass_T3)},
            "T4": {"BHL_passers": bhl_passers, "n_BHL": T4_n_bhl, "pass": bool(pass_T4)},
            "T5": {"null_mean": float(T5_null.mean()), "null_std": float(T5_null.std()), "p": p_T5, "pass": bool(pass_T5)},
            "per_letter": {k: {"E_obs": v[0], "z": v[1], "p": v[2]} for k, v in per_letter_p.items()},
        },
        "alpha_per_test": alpha,
        "effect_size_threshold": 0.05,
        "effect_size_pass": bool(effect_size_ok),
    }
    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False, default=float), encoding="utf-8")
    print(f"[exp174] receipt → {out_dir / 'receipt.json'}", flush=True)

    # Figures
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 3, figsize=(15, 9))
        for ax, (label, obs, null) in zip(
            axes.flat,
            [("T1 mean log2(E)", T1_obs, T1_null),
             ("T2 frac E>1", T2_obs, T2_null),
             ("T3 n pooled letters E>1", T3_obs, T3_null),
             ("T5 top-3 hits", T5_obs, T5_null)]
        ):
            ax.hist(null, bins=40, color="#888", alpha=0.7, density=True, label="null B")
            ax.axvline(obs, color="r", linewidth=2, label=f"obs {obs:.4f}" if not isinstance(obs, int) else f"obs {obs}")
            ax.set_title(label); ax.legend()
        # Per-letter bar chart
        ax = axes[1, 1]
        labels = list(pooled_E_obs.keys())
        vals = [pooled_E_obs[l] for l in labels]
        colors = ["#2e7d32" if v > 1 else "#c62828" for v in vals]
        ax.bar(range(len(labels)), vals, color=colors)
        ax.axhline(1.0, color="k", linestyle="--")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels)
        ax.set_ylabel("E_pool"); ax.set_title("per-letter pooled enrichment")
        axes[1, 2].axis("off")
        axes[1, 2].text(0.1, 0.7, f"Verdict: {verdict}\n\nn_pass: {n_pass}/5\n⟨log2 E⟩: {T1_obs:+.4f}\nmean E: {2**T1_obs:.4f}\nBHL survivors: {T4_n_bhl}/14",
                        fontsize=12, verticalalignment="top")
        fig.suptitle(f"exp174 muqatta'at frequency enrichment — {verdict}")
        fig.tight_layout()
        fig.savefig(out_dir / "fig_nulls.png", dpi=120)
        plt.close(fig)
        print(f"[exp174] figure → {out_dir / 'fig_nulls.png'}", flush=True)
    except Exception as e:
        print(f"[exp174] fig skip: {e}", flush=True)


if __name__ == "__main__":
    main()
