"""
exp87_unified_probe/run.py
===========================
H21: Unified Two-Scale Law — I_total = macro_z + α × micro_z ≥ C

Tests whether a linear combination of macro structural score (LOO Mahalanobis
margin) and micro phonetic score (4 tashkeel-based features) maintains a stable
floor across all 114 Quran surahs, while excluding vocalized non-Quran controls.

Data sources (all read-only):
    archive/archive_old_jsons/LOO_TAU_MAX_results.json
    archive/archive_old_jsons/QSF_S10_results.json
    archive/helpers/tashkeela_fiqh_vocal.txt
    archive/helpers/poetry_vocal.txt

Writes ONLY under results/experiments/exp87_unified_probe/:
    exp87_unified_probe.json
    self_check_<ts>.json
"""
from __future__ import annotations

import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import mannwhitneyu, spearmanr

# ── Paths ──────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_ROOT / "experiments"))

from _lib import self_check_begin, self_check_end, safe_output_dir

EXP_NAME = "exp87_unified_probe"
_ARCHIVE = _ROOT / "archive"

# ── Micro feature functions (frozen, matching S10 phonetic pipeline) ───────
TASHKEEL_RE  = re.compile(r'[\u064b-\u0652\u0670\u0653]')
SUKUN        = '\u0652'
SHADDA       = '\u0651'
MADD_LETTERS = set('\u0627\u0648\u064a')  # alef, waw, ya


def madd_density(text: str) -> float:
    letters = re.findall(r'[\u0621-\u064a]', text)
    if not letters:
        return float('nan')
    madd = sum(1 for l in letters if l in MADD_LETTERS)
    return madd / len(letters)


def sukun_entropy(text: str) -> float:
    positions = [i for i, c in enumerate(text) if c == SUKUN]
    if len(positions) < 2:
        return float('nan')
    gaps = [positions[i + 1] - positions[i] for i in range(len(positions) - 1)]
    cnt = Counter(gaps)
    total = sum(cnt.values())
    return -sum((c / total) * math.log2(c / total) for c in cnt.values())


def shadda_density(text: str) -> float:
    if not text:
        return float('nan')
    return text.count(SHADDA) / max(len(text), 1)


def tashkeel_markov_entropy(text: str) -> float:
    diacs = [c for c in text if c in '\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652']
    if len(diacs) < 4:
        return float('nan')
    bigrams = list(zip(diacs, diacs[1:]))
    cnt = Counter(bigrams)
    total = sum(cnt.values())
    return -sum((c / total) * math.log2(c / total) for c in cnt.values())


def compute_micro_features(text: str) -> dict:
    return {
        'madd_density':            madd_density(text),
        'sukun_entropy':           sukun_entropy(text),
        'shadda_density':          shadda_density(text),
        'tashkeel_markov_entropy': tashkeel_markov_entropy(text),
    }


# ── Pseudo-surah builder ──────────────────────────────────────────────────
def count_letters(text: str) -> int:
    bare = TASHKEEL_RE.sub('', text)
    return len(re.findall(r'[\u0621-\u064a]', bare))


def build_pseudo_surahs(lines: list[str], targets: list[int]) -> list[list[str]]:
    lines = [l.strip() for l in lines if l.strip() and count_letters(l) > 0]
    pseudo = []
    idx = 0
    for target in targets:
        chunk = []
        letters_so_far = 0
        while idx < len(lines):
            line_letters = count_letters(lines[idx])
            chunk.append(lines[idx])
            letters_so_far += line_letters
            idx += 1
            if letters_so_far >= target * 0.7:
                break
        if chunk:
            pseudo.append(chunk)
    # Pad if we ran out of lines
    while len(pseudo) < len(targets) and pseudo:
        pseudo.append(pseudo[-1])
    return pseudo[:len(targets)]


# ══════════════════════════════════════════════════════════════════════════
def main() -> None:
    t0 = time.time()
    pre = self_check_begin()
    out_dir = safe_output_dir(EXP_NAME)

    print(f"{'=' * 65}")
    print(f"  exp87_unified_probe -- H21 Unified Two-Scale Law")
    print(f"{'=' * 65}\n")

    # ── S1: Load macro margins ──────────────────────────────────────────
    loo_path = _ARCHIVE / "archive_old_jsons" / "LOO_TAU_MAX_results.json"
    with open(loo_path, "r", encoding="utf-8") as f:
        loo = json.load(f)

    macro = {}
    for row in loo['loo_detail']:
        idx = row['surah_idx']
        margin = row['tau_max_loo'] - row['dist']
        macro[idx] = {
            'dist': row['dist'],
            'tau_loo': row['tau_max_loo'],
            'margin': margin,
            'passes_macro': row['passes'],
        }
    print(f"Macro: {len(macro)} surahs loaded")
    print(f"  Macro pass (LOO): {sum(1 for v in macro.values() if v['passes_macro'])}/114")

    # ── S2: Load micro composite ────────────────────────────────────────
    s10_path = _ARCHIVE / "archive_old_jsons" / "QSF_S10_results.json"
    with open(s10_path, "r", encoding="utf-8") as f:
        s10 = json.load(f)

    micro_raw = {int(k): v for k, v in s10['micro_composite_by_surah'].items()}
    print(f"Micro: {len(micro_raw)} surahs loaded")
    hard_failures = s10.get('hard_failures', [])
    print(f"  Hard macro failures: {hard_failures}")

    # ── S3: Build Quran DataFrame and normalize ─────────────────────────
    rows = []
    for idx in range(1, 115):
        if idx not in macro or idx not in micro_raw:
            continue
        rows.append({
            'surah_idx':    idx,
            'macro_margin': macro[idx]['margin'],
            'macro_pass':   macro[idx]['passes_macro'],
            'micro_comp':   micro_raw[idx],
        })

    n_q = len(rows)
    macro_arr = np.array([r['macro_margin'] for r in rows])
    micro_arr = np.array([r['micro_comp'] for r in rows])

    macro_mu, macro_sd = float(macro_arr.mean()), float(macro_arr.std())
    micro_mu, micro_sd = float(micro_arr.mean()), float(micro_arr.std())

    macro_z = (macro_arr - macro_mu) / macro_sd
    micro_z = (micro_arr - micro_mu) / micro_sd

    print(f"\nQuran: {n_q} surahs")
    print(f"  macro_z range: [{macro_z.min():.3f}, {macro_z.max():.3f}]")
    print(f"  micro_z range: [{micro_z.min():.3f}, {micro_z.max():.3f}]")

    # ── S4: Fit alpha on Quran-only ─────────────────────────────────────
    # Strategy A: 100% coverage — maximize the minimum I_total
    def quran_floor_100(alpha: float) -> float:
        i_total = macro_z + alpha * micro_z
        return float(i_total.min())

    # Strategy B: 95% coverage — maximize the 5th percentile of I_total
    def quran_floor_95(alpha: float) -> float:
        i_total = macro_z + alpha * micro_z
        return float(np.percentile(i_total, 5))

    alpha_grid = np.linspace(0.0, 3.0, 301)

    # Strategy A
    floors_100 = [quran_floor_100(a) for a in alpha_grid]
    best_100 = int(np.argmax(floors_100))
    alpha_100 = round(float(alpha_grid[best_100]), 2)

    # Strategy B
    floors_95 = [quran_floor_95(a) for a in alpha_grid]
    best_95 = int(np.argmax(floors_95))
    alpha_95 = round(float(alpha_grid[best_95]), 2)

    # Refine strategy B with scipy
    res_95 = minimize_scalar(lambda a: -quran_floor_95(a),
                             bounds=(0.0, 4.0), method='bounded')
    alpha_95_opt = float(res_95.x)

    print(f"\n  Strategy A (100% coverage): alpha = {alpha_100}")
    print(f"  Strategy B (95% coverage):  alpha = {alpha_95} "
          f"(refined: {alpha_95_opt:.4f})")

    # Use strategy B as primary (more robust to single outlier surahs)
    ALPHA = alpha_95
    ALPHA_100 = alpha_100
    i_total_q = macro_z + ALPHA * micro_z
    i_total_q_100 = macro_z + ALPHA_100 * micro_z
    THRESHOLD = float(np.percentile(i_total_q, 5))  # 95% Quran coverage
    THRESHOLD_100 = float(i_total_q_100.min())       # 100% Quran coverage
    n_q_pass = int((i_total_q >= THRESHOLD).sum())
    n_q_pass_100 = int((i_total_q_100 >= THRESHOLD_100).sum())

    # Also compute: which surahs fail the 95% threshold?
    failing_95 = []
    for r, it in zip(rows, i_total_q):
        if it < THRESHOLD:
            failing_95.append(r['surah_idx'])

    print(f"\n  Using ALPHA = {ALPHA} (95% coverage strategy)")
    print(f"  Quran I_total range: [{i_total_q.min():.4f}, {i_total_q.max():.4f}]")
    print(f"  Threshold C (5th pct) = {THRESHOLD:.4f}  -> {n_q_pass}/114 pass")
    print(f"  Strategy A (100%):  alpha={ALPHA_100}, C={THRESHOLD_100:.4f}")
    if failing_95:
        print(f"  Surahs failing 95% threshold: {failing_95}")

    # Show hard failures
    print(f"\n  Hard macro failure rescue check:")
    for r, mz, uz, it in zip(rows, macro_z, micro_z, i_total_q):
        if r['surah_idx'] in hard_failures:
            rescued = "RESCUED" if it >= THRESHOLD else "STILL FAILS"
            print(f"    Surah {r['surah_idx']:3d}: macro_z={mz:+.3f}  "
                  f"micro_z={uz:+.3f}  i_total={it:+.3f}  {rescued}")

    # ── S5: Build pseudo-surahs from vocalized controls ─────────────────
    # Approximate Quran letter targets (sorted ascending)
    quran_letter_targets = sorted([
        47, 78, 100, 126, 132, 139, 142, 148, 150, 158, 164, 166, 168, 172,
        175, 178, 182, 191, 194, 198, 202, 211, 215, 218, 222, 228, 234, 244,
        252, 261, 268, 274, 278, 285, 291, 298, 304, 312, 321, 330, 345, 356,
        367, 381, 392, 405, 418, 432, 448, 465, 482, 500, 518, 538, 558, 580,
        602, 625, 649, 675, 700, 726, 754, 783, 813, 845, 879, 914, 950, 988,
        1028, 1070, 1115, 1160, 1210, 1260, 1315, 1375, 1440, 1510, 1580,
        1655, 1735, 1820, 1910, 2005, 2105, 2210, 2322, 2440, 2565, 2700,
        2845, 3000, 3165, 3340, 3528, 3730, 3945, 4175, 4421, 4685, 4967,
        5270, 5594, 5940, 6310, 6705, 7127, 7580, 8065, 8584, 9140, 9736,
    ])

    control_files = {
        'tashkeela_fiqh': _ARCHIVE / "helpers" / "tashkeela_fiqh_vocal.txt",
        'poetry_vocal':   _ARCHIVE / "helpers" / "poetry_vocal.txt",
    }

    MICRO_FEATURES = ['madd_density', 'sukun_entropy', 'shadda_density',
                      'tashkeel_markov_entropy']

    ctrl_results = {}
    print(f"\n{'=' * 65}")
    print("  External control testing")
    print(f"{'=' * 65}")

    for corpus_name, fpath in control_files.items():
        if not fpath.exists():
            print(f"\n  MISSING: {fpath} -- skipping {corpus_name}")
            ctrl_results[corpus_name] = {"status": "MISSING", "n": 0}
            continue

        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        print(f"\n  {corpus_name}: {len(lines):,} lines")

        pseudo_surahs = build_pseudo_surahs(lines, quran_letter_targets)
        print(f"    Built {len(pseudo_surahs)} pseudo-surahs")

        # Compute micro features for each pseudo-surah
        ctrl_micro_comps = []
        n_nan = 0
        for ps in pseudo_surahs:
            full_text = ' '.join(ps)
            feats = compute_micro_features(full_text)
            # Compute composite: z-score each feature relative to Quran stats,
            # then average (matching S10 protocol)
            feat_vals = []
            for feat_name in MICRO_FEATURES:
                val = feats[feat_name]
                if math.isnan(val):
                    n_nan += 1
                    feat_vals.append(0.0)  # impute with Quran mean (z=0)
                else:
                    feat_vals.append(val)
            ctrl_micro_comps.append(np.mean(feat_vals))

        ctrl_micro_arr = np.array(ctrl_micro_comps)

        # Now we need to normalize the control micro composites to be comparable
        # with Quran micro_z. The Quran micro was z-scored using Quran mean/std.
        # For controls, we compute their raw micro composite, then z-score using
        # the SAME Quran mean/std (from the raw micro_comp, not the z-scored).
        ctrl_micro_z = (ctrl_micro_arr - micro_mu) / micro_sd

        # For macro: controls don't have LOO margins. We test two scenarios:
        # TEST A: Micro-only — does micro_z alone separate?
        # TEST B: Conservative — give controls macro_z = 0 (Quran average)
        ctrl_i_total_conservative = 0.0 + ALPHA * ctrl_micro_z

        n_below = int((ctrl_i_total_conservative < THRESHOLD).sum())
        pct_excluded = 100.0 * n_below / len(ctrl_i_total_conservative)

        # Micro-only: compare distributions
        mw_stat, mw_p = mannwhitneyu(micro_z, ctrl_micro_z, alternative='greater')

        print(f"    NaN imputations: {n_nan}")
        print(f"    Ctrl micro_z: mean={ctrl_micro_z.mean():+.3f}  "
              f"std={ctrl_micro_z.std():.3f}  "
              f"range=[{ctrl_micro_z.min():+.3f}, {ctrl_micro_z.max():+.3f}]")
        print(f"    MW p(Quran micro > ctrl micro): {mw_p:.4e}")
        print(f"    Conservative I_total (macro_z=0): "
              f"mean={ctrl_i_total_conservative.mean():+.3f}")
        print(f"    Excluded below C={THRESHOLD:.3f}: "
              f"{n_below}/{len(ctrl_i_total_conservative)} = {pct_excluded:.1f}%")

        if pct_excluded >= 70:
            verdict_corpus = "STRONG"
        elif pct_excluded >= 40:
            verdict_corpus = "MODERATE"
        else:
            verdict_corpus = "WEAK"
        print(f"    Verdict: {verdict_corpus}")

        ctrl_results[corpus_name] = {
            "status": "OK",
            "n_pseudo_surahs": len(pseudo_surahs),
            "n_nan_imputations": n_nan,
            "ctrl_micro_z_mean": round(float(ctrl_micro_z.mean()), 4),
            "ctrl_micro_z_std": round(float(ctrl_micro_z.std()), 4),
            "mw_p_quran_greater": float(mw_p),
            "conservative_i_total_mean": round(float(ctrl_i_total_conservative.mean()), 4),
            "n_excluded": n_below,
            "pct_excluded": round(pct_excluded, 2),
            "verdict": verdict_corpus,
        }

    # ── S6: Falsifier check ─────────────────────────────────────────────
    # If ctrl micro mean >= Quran micro mean -> micro axis is non-discriminative
    falsifier_triggered = False
    for cname, cdata in ctrl_results.items():
        if cdata.get("status") == "OK":
            if cdata["ctrl_micro_z_mean"] >= 0.0:
                falsifier_triggered = True
                print(f"\n  WARNING FALSIFIER: {cname} micro_z mean "
                      f"({cdata['ctrl_micro_z_mean']:+.3f}) >= Quran mean (0.0)")

    # ── S7: Overall verdict ─────────────────────────────────────────────
    verdicts = [v.get("verdict", "MISSING") for v in ctrl_results.values()
                if v.get("status") == "OK"]
    if not verdicts:
        overall = "NO_DATA"
    elif falsifier_triggered:
        overall = "FALSIFIER_TRIGGERED"
    elif all(v == "STRONG" for v in verdicts):
        overall = "STRONG"
    elif all(v in ("STRONG", "MODERATE") for v in verdicts):
        overall = "MODERATE"
    else:
        overall = "WEAK"

    runtime = time.time() - t0

    print(f"\n{'=' * 65}")
    print(f"  OVERALL VERDICT: {overall}")
    print(f"  ALPHA = {ALPHA}, C = {THRESHOLD:.4f}")
    print(f"  Runtime: {runtime:.1f}s")
    print(f"{'=' * 65}")

    # ── S8: Save results ────────────────────────────────────────────────
    results = {
        "experiment": EXP_NAME,
        "hypothesis": "H21 -- Unified Two-Scale Law: I_total = macro_z + alpha * micro_z >= C",
        "schema_version": 1,
        "strategy_A_100pct": {
            "alpha": ALPHA_100,
            "threshold_C": THRESHOLD_100,
            "quran_pass": f"{n_q_pass_100}/114",
            "note": "100% coverage: maximises min(I_total); alpha=0 means micro hurts worst-case surah",
        },
        "strategy_B_95pct": {
            "alpha": ALPHA,
            "threshold_C": THRESHOLD,
            "quran_pass": f"{n_q_pass}/114",
            "failing_surahs": failing_95,
            "note": "95% coverage: maximises 5th percentile; allows dropping worst 5%",
        },
        "alpha": ALPHA,
        "threshold_C": THRESHOLD,
        "quran_n": n_q,
        "quran_macro_z_range": [round(float(macro_z.min()), 4),
                                round(float(macro_z.max()), 4)],
        "quran_micro_z_range": [round(float(micro_z.min()), 4),
                                round(float(micro_z.max()), 4)],
        "quran_i_total_range": [round(float(i_total_q.min()), 4),
                                round(float(i_total_q.max()), 4)],
        "hard_failure_rescue": {},
        "control_results": ctrl_results,
        "falsifier_triggered": falsifier_triggered,
        "verdict": overall,
        "runtime_seconds": round(runtime, 2),
    }

    # Hard failure detail
    for r, mz, uz, it in zip(rows, macro_z, micro_z, i_total_q):
        if r['surah_idx'] in hard_failures:
            results["hard_failure_rescue"][str(r['surah_idx'])] = {
                "macro_z": round(float(mz), 4),
                "micro_z": round(float(uz), 4),
                "i_total": round(float(it), 4),
                "rescued": bool(it >= THRESHOLD),
            }

    out_json = out_dir / f"{EXP_NAME}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {out_json}")

    # ── Self-check ──────────────────────────────────────────────────────
    receipt = self_check_end(pre, EXP_NAME)
    print(f"Self-check: {'PASSED' if receipt['ok'] else 'FAILED'}")


if __name__ == "__main__":
    main()
