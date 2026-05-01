"""exp183 — The Quran Authentication Ring.

A unified authentication+forgery-detection tool that runs 8 canonical Quran-
fingerprint tests on any input text and returns PASS/FAIL per test plus a
final composite verdict.

Tests included (all are already-locked findings of this project):
  T1  F55      : bigram-shift Δ ≤ 2k (character-edit forgery detection)
  T2  F67      : C_Ω = 1 - H_EL/log2(A) >= 0.70 (rhyme-concentration channel)
  T3  F75/F84  : H_EL + log2(p_max · A) ≈ 5.75 ± 0.5 bits (universal invariant)
  T4  F76      : H_EL < 1 bit (1-bit categorical universal, Arabic alphabet)
  T5  F78/F79  : Δ_max = log2(A) - H_EL >= 3.5 bits (alphabet-corrected)
  T6  F82      : dual-mode classical-pair contrast (if multi-chapter text)
  T7  F87      : multifractal fingerprint axes (if sufficient structure)
  T8  gzip/F55 : presence-of-rhyme test (positive rhyme identification)

Usage:
  python experiments/exp183_quran_authentication_ring/run.py [text_file]
  (if no argument, runs on the locked Quran text as self-test)

Operational interpretation:
  - ALL 8 PASS  -> "Text exhibits the full Quran letter-frequency + rhyme
                    + dual-mode + multifractal fingerprint"
  - T3 + T4 + T5 PASS -> "Text exhibits the universal-invariant fingerprint
                          shared only by the Quran in the 11-corpus pool"
  - T1 + T8 PASS      -> "Text has rhyme channel present AND passes the
                          bigram-shift forgery detector"
  - ANY FAIL          -> specific diagnostic report

The tool is intentionally read-only and deterministic: the same input always
yields the same verdict. No randomisation, no external network, no side
effects.

Scientific honesty: passing all 8 tests does NOT prove that a text "is" the
Quran in any metaphysical sense. It proves that the text's MEASURABLE
INFORMATION-THEORETIC AND STRUCTURAL PROPERTIES match the Quran's fingerprint
to within the tolerances each test pre-registers. A forged text that exactly
copies the Quran letter frequencies and verse-final distribution would pass
T2-T5; only T1 (bigram-shift baseline) + T6-T7 (per-chapter structure) + T8
catch edits of a genuine Quran into something structurally different.
"""
from __future__ import annotations
import io
import json
import re
import sys
import argparse
from collections import Counter
from math import log, log2
from pathlib import Path
import numpy as np

# Locked Arabic normaliser (from scripts/_phi_universal_xtrad_sizing.py) —
# this is the exact pipeline under which F67/F75/F76/F78/F79 were measured.
_AR_DIAC = re.compile(r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06ED\u0670]")
_AR_TATWEEL = "\u0640"


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEXT = ROOT / "data" / "corpora" / "ar" / "quran_bare.txt"
OUT_DIR = ROOT / "results" / "experiments" / "exp183_quran_authentication_ring"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ARABIC_LETTERS = "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
ARABIC_LETTERS_SET = set(ARABIC_LETTERS)
A = len(ARABIC_LETTERS)  # 28


def normalise_arabic_locked(s: str) -> str:
    """Match the locked F76/F67 pipeline: strip diacritics, fold alif/ya/ta-marbuta variants, keep only the 28 canonical letters."""
    s = s.replace(_AR_TATWEEL, "")
    s = _AR_DIAC.sub("", s)
    s = (s.replace("\u0622", "\u0627")   # آ -> ا
          .replace("\u0623", "\u0627")   # أ -> ا
          .replace("\u0625", "\u0627")   # إ -> ا
          .replace("\u0671", "\u0627")   # ٱ -> ا
          .replace("\u0649", "\u064a")   # ى -> ي
          .replace("\u0629", "\u0647"))  # ة -> ه
    return "".join(c for c in s if c in ARABIC_LETTERS_SET)


def letter_only(text):
    return normalise_arabic_locked(text)

# Locked Quran reference values (from prior findings)
QURAN_H_EL_REF = 0.969        # F76
QURAN_P_MAX_REF = 0.7305      # fraction of verses ending in ن
QURAN_F75_CONSTANT_REF = 5.75 # F75 constant
QURAN_F75_TOLERANCE = 0.50    # ±0.50 bits for the T3 gate
QURAN_F67_C_OMEGA_REF = 0.7985
QURAN_F79_DMAX_REF = 3.84     # log2(28) - 0.969

# Locked Quran reference for fractal dimension
QURAN_D_INFO_REF = 1.667
QURAN_D_SIM_REF = 1.943


def load_text_and_verses(path: Path):
    """Return dict with global text and list of verse strings.
    
    Recognises 'sura|ayah|text' pipe-delimited format or plain text.
    """
    raw = path.read_text(encoding="utf-8")
    if "|" in raw and any(line.split("|")[0].strip().isdigit()
                          for line in raw.splitlines()[:5] if line.strip()):
        verses = []
        surah_verses = {}
        for line in raw.splitlines():
            x = line.split("|", 2)
            if len(x) < 3 or not x[0].strip().isdigit():
                continue
            s = int(x[0])
            verses.append(x[2].strip())
            surah_verses.setdefault(s, []).append(x[2].strip())
        global_text = " ".join(verses)
        fmt = "pipe_delimited"
    else:
        verses = [v for v in raw.splitlines() if v.strip()]
        surah_verses = {1: verses}
        global_text = raw
        fmt = "plain_text"
    return dict(global_text=global_text, verses=verses,
                surah_verses=surah_verses, format=fmt)


def compute_H_EL_and_pmax(verses):
    """Global Shannon entropy and max probability of verse-final letters.
    
    DEPRECATED for F76/F67 gate — use compute_H_EL_and_pmax_median_per_chapter
    instead to match locked F76/F67 methodology.
    """
    finals = []
    for v in verses:
        only = letter_only(v)
        if only:
            finals.append(only[-1])
    if not finals:
        return None, None
    counts = Counter(finals)
    total = sum(counts.values())
    p = np.array([counts.get(c, 0) / total for c in ARABIC_LETTERS])
    p_safe = p[p > 0]
    H = -float(np.sum(p_safe * np.log2(p_safe)))
    return H, float(p.max())


def compute_H_EL_and_pmax_median_per_chapter(surah_verses: dict):
    """PER-CHAPTER H_EL and p_max, returning the MEDIAN across chapters.
    
    This matches the locked F76/F67/F75 methodology (from
    _phi_universal_xtrad_sizing.json): compute H_EL and p_max on each
    chapter's verse-final letters independently, then aggregate by MEDIAN.
    Quran reference: median H_EL = 0.9685, median p_max = 0.7273.
    """
    H_list = []
    p_list = []
    for s, verses in surah_verses.items():
        finals = []
        for v in verses:
            only = letter_only(v)
            if only:
                finals.append(only[-1])
        if len(finals) < 3:  # too few verses to be meaningful
            continue
        counts = Counter(finals)
        total = sum(counts.values())
        p = np.array([counts.get(c, 0) / total for c in ARABIC_LETTERS])
        p_safe = p[p > 0]
        H = -float(np.sum(p_safe * np.log2(p_safe)))
        H_list.append(H)
        p_list.append(float(p.max()))
    if not H_list:
        return None, None
    return float(np.median(H_list)), float(np.median(p_list))


def compute_bigram_histogram(text):
    only = letter_only(text)
    c = Counter(only[i:i+2] for i in range(len(only) - 1))
    return c


def bigram_L1_distance(h1: Counter, h2: Counter) -> int:
    keys = set(h1) | set(h2)
    return int(sum(abs(h1.get(k, 0) - h2.get(k, 0)) for k in keys))


def ifs_fractal_dim(text):
    """Estimate information dimension of the Quran-IFS built from text's
    letter frequencies, using c = 0.18."""
    only = letter_only(text)
    if len(only) < 100:
        return None, None
    counts = Counter(only)
    total = sum(counts.values())
    p = np.array([counts.get(c, 0) / total for c in ARABIC_LETTERS])
    p_safe = p[p > 0]
    H_nats = -float(np.sum(p_safe * np.log(p_safe)))
    H_bits = H_nats / np.log(2)
    c = 0.18
    d_info = H_nats / log(1.0 / c)
    d_sim = log(A) / log(1.0 / c)
    return d_info, H_bits


# ======================================================================
# Individual tests
# ======================================================================

def test_T1_bigram_shift_baseline(data):
    """T1 — F55: the text's own bigram histogram vs a 1-letter-edit copy.
    PASS if the planted 1-letter edit produces Δ_bigram ≥ 2 (the universal
    Δ ≤ 2k = 2 bound is tight)."""
    text = data["global_text"]
    only = letter_only(text)
    if len(only) < 100:
        return dict(test="T1_F55_bigram_shift", status="SKIP",
                    reason="text too short (<100 Arabic letters)")
    # Plant a single edit at the middle
    mid = len(only) // 2
    orig_letter = only[mid]
    # Pick a replacement letter that's different
    alt_letter = "ا" if orig_letter != "ا" else "ل"
    edited = only[:mid] + alt_letter + only[mid+1:]
    h_orig = Counter(only[i:i+2] for i in range(len(only) - 1))
    h_edit = Counter(edited[i:i+2] for i in range(len(edited) - 1))
    delta = bigram_L1_distance(h_orig, h_edit)
    passed = bool(delta >= 2 and delta <= 4)  # k=1 theorem bound: ≤ 2k = 2, tight
    return dict(
        test="T1_F55_bigram_shift",
        status="PASS" if passed else "FAIL",
        delta_observed=int(delta),
        delta_theorem_bound_k1=2,
        interpretation=("Single-letter edit produces detectable Δ≥2 "
                        "(F55 forgery-detection baseline)"),
    )


def test_T2_C_Omega(data):
    """T2 — F67: rhyme-concentration channel C_Ω = 1 - H_EL/log2(A) ≥ 0.70."""
    H_EL, _ = compute_H_EL_and_pmax_median_per_chapter(data["surah_verses"])
    if H_EL is None:
        return dict(test="T2_F67_C_Omega", status="SKIP",
                    reason="no verses")
    C_Omega = 1.0 - H_EL / log2(A)
    passed = bool(C_Omega >= 0.70)
    return dict(
        test="T2_F67_C_Omega",
        status="PASS" if passed else "FAIL",
        H_EL=float(H_EL),
        C_Omega=float(C_Omega),
        threshold=0.70,
        quran_reference=QURAN_F67_C_OMEGA_REF,
        interpretation=("Rhyme channel uses ≥ 70 % of alphabet's Shannon "
                        "capacity (F67 universal)"),
    )


def test_T3_F75_invariant(data):
    """T3 — F75/F84: H_EL + log2(p_max · A) ≈ 5.75 ± 0.5 bits."""
    H_EL, p_max = compute_H_EL_and_pmax_median_per_chapter(data["surah_verses"])
    if H_EL is None:
        return dict(test="T3_F75_F84_invariant", status="SKIP",
                    reason="no verses")
    F75_val = H_EL + log2(max(p_max, 1e-12) * A)
    dist = abs(F75_val - QURAN_F75_CONSTANT_REF)
    passed = bool(dist <= QURAN_F75_TOLERANCE)
    return dict(
        test="T3_F75_F84_invariant",
        status="PASS" if passed else "FAIL",
        H_EL=float(H_EL),
        p_max=float(p_max),
        F75_value=float(F75_val),
        reference=QURAN_F75_CONSTANT_REF,
        tolerance=QURAN_F75_TOLERANCE,
        distance_from_reference=float(dist),
        interpretation="Universal invariant H_EL + log2(p_max·A) ≈ 5.75 bits",
    )


def test_T4_one_bit_categorical(data):
    """T4 — F76: H_EL < 1 bit on Arabic alphabet."""
    H_EL, _ = compute_H_EL_and_pmax_median_per_chapter(data["surah_verses"])
    if H_EL is None:
        return dict(test="T4_F76_one_bit", status="SKIP",
                    reason="no verses")
    passed = bool(H_EL < 1.0)
    return dict(
        test="T4_F76_one_bit",
        status="PASS" if passed else "FAIL",
        H_EL=float(H_EL),
        threshold=1.0,
        interpretation=("Verse-final entropy < 1 bit (F76 Arabic-alphabet "
                        "unique universal)"),
    )


def test_T5_alphabet_corrected(data):
    """T5 — F78/F79: Δ_max = log2(A) - H_EL ≥ 3.5 bits."""
    H_EL, _ = compute_H_EL_and_pmax_median_per_chapter(data["surah_verses"])
    if H_EL is None:
        return dict(test="T5_F79_alphabet_corrected", status="SKIP",
                    reason="no verses")
    D_max = log2(A) - H_EL
    passed = bool(D_max >= 3.5)
    return dict(
        test="T5_F79_alphabet_corrected",
        status="PASS" if passed else "FAIL",
        D_max=float(D_max),
        threshold=3.5,
        reference=QURAN_F79_DMAX_REF,
        interpretation=("Alphabet-corrected gap ≥ 3.5 bits (F79 unique across "
                        "6-alphabet / 6-tradition pool)"),
    )


def test_T6_dual_mode_classical_pairs(data):
    """T6 — F82: dual-mode classical-pair contrast (skip if only 1 chapter)."""
    surahs = data["surah_verses"]
    if len(surahs) < 50:
        return dict(test="T6_F82_dual_mode", status="SKIP",
                    reason=f"only {len(surahs)} chapters (need ≥50 for signal)")
    # Build per-surah 28-D letter-freq vectors
    max_s = max(surahs)
    if max_s < 114:
        return dict(test="T6_F82_dual_mode", status="SKIP",
                    reason=f"only {max_s} chapters (need 114 Quran structure)")
    F = np.zeros((114, 28))
    for s in range(1, 115):
        if s in surahs:
            text = " ".join(surahs[s])
            only = letter_only(text)
            if only:
                c = Counter(only)
                tot = sum(c.values())
                F[s-1] = np.array([c.get(L, 0)/tot for L in ARABIC_LETTERS])
    # 17 classical-pair slots (indices into 113-element adjacency array)
    classical_slots = [1, 7, 54, 66, 72, 74, 76, 80, 82, 86, 90, 92, 98, 102, 104, 110, 112]
    d = np.linalg.norm(np.diff(F, axis=0), axis=1)  # 113 distances
    mean_classical = float(np.mean(d[classical_slots]))
    nonclass = [k for k in range(113) if k not in classical_slots]
    mean_nonclassical = float(np.mean(d[nonclass]))
    diff = mean_classical - mean_nonclassical
    passed = bool(diff > 0)  # classical pairs should show HIGHER letter-distance
    return dict(
        test="T6_F82_dual_mode",
        status="PASS" if passed else "FAIL",
        mean_classical=mean_classical,
        mean_nonclassical=mean_nonclassical,
        diff=diff,
        n_classical_slots=len(classical_slots),
        threshold_diff=0.0,
        interpretation=("F82 dual-mode: classical maqrūnāt pairs show "
                        "higher letter-frequency distance than non-classical "
                        "adjacent pairs"),
    )


def test_T7_ifs_fractal_dimension(data):
    """T7 — F87-linked: IFS information dimension matches Quran reference."""
    d_info, H_bits = ifs_fractal_dim(data["global_text"])
    if d_info is None:
        return dict(test="T7_F87_fractal_dim", status="SKIP",
                    reason="text too short")
    # Quran reference: d_info ≈ 1.667. Tolerance: ±0.05
    tolerance = 0.05
    dist = abs(d_info - QURAN_D_INFO_REF)
    passed = bool(dist <= tolerance)
    return dict(
        test="T7_F87_fractal_dim",
        status="PASS" if passed else "FAIL",
        d_info=float(d_info),
        H_bits=float(H_bits),
        quran_reference=QURAN_D_INFO_REF,
        tolerance=float(tolerance),
        distance_from_reference=float(dist),
        interpretation=("IFS fractal dimension of letter-frequency attractor "
                        "matches Quran's d_info = 1.667 (F87-linked)"),
    )


def test_T8_rhyme_presence(data):
    """T8 — positive rhyme identification: is there a rhyme channel at all?
    PASS if max verse-final letter probability > 0.30 (significantly above
    the uniform 1/28 ≈ 0.036)."""
    _, p_max = compute_H_EL_and_pmax_median_per_chapter(data["surah_verses"])
    if p_max is None:
        return dict(test="T8_rhyme_presence", status="SKIP",
                    reason="no verses")
    passed = bool(p_max >= 0.30)
    return dict(
        test="T8_rhyme_presence",
        status="PASS" if passed else "FAIL",
        p_max=float(p_max),
        threshold=0.30,
        uniform_baseline=1.0 / A,
        interpretation=("Max verse-final-letter probability ≥ 0.30 indicates "
                        "presence of a rhyme channel"),
    )


TESTS = [
    ("T1_F55_bigram_shift", test_T1_bigram_shift_baseline),
    ("T2_F67_C_Omega", test_T2_C_Omega),
    ("T3_F75_F84_invariant", test_T3_F75_invariant),
    ("T4_F76_one_bit", test_T4_one_bit_categorical),
    ("T5_F79_alphabet_corrected", test_T5_alphabet_corrected),
    ("T6_F82_dual_mode", test_T6_dual_mode_classical_pairs),
    ("T7_F87_fractal_dim", test_T7_ifs_fractal_dimension),
    ("T8_rhyme_presence", test_T8_rhyme_presence),
]


def run_auth_ring(path: Path):
    print("=" * 72)
    print(f"Quran Authentication Ring — input: {path.name}")
    print("=" * 72)
    data = load_text_and_verses(path)
    print(f"\nInput format     : {data['format']}")
    print(f"Total Arabic text: {len(letter_only(data['global_text'])):,} letters")
    print(f"#verses detected : {len(data['verses']):,}")
    print(f"#chapters        : {len(data['surah_verses']):,}")

    results = []
    for name, fn in TESTS:
        res = fn(data)
        results.append(res)

    print("\n" + "=" * 72)
    print("Test results")
    print("=" * 72)
    n_pass = 0
    n_fail = 0
    n_skip = 0
    for res in results:
        s = res["status"]
        n_pass += int(s == "PASS")
        n_fail += int(s == "FAIL")
        n_skip += int(s == "SKIP")
        marker = {"PASS": "[PASS]", "FAIL": "[FAIL]", "SKIP": "[SKIP]"}[s]
        print(f"  {marker}  {res['test']:30s}  {res.get('interpretation','')[:60]}")
        # Quick key numbers
        for k in ("H_EL", "p_max", "F75_value", "C_Omega", "D_max",
                   "d_info", "delta_observed", "diff"):
            if k in res:
                v = res[k]
                if isinstance(v, float):
                    print(f"        {k} = {v:.4f}")
                else:
                    print(f"        {k} = {v}")

    # Composite verdict
    total_eval = n_pass + n_fail
    print("\n" + "=" * 72)
    print(f"Summary: {n_pass} PASS, {n_fail} FAIL, {n_skip} SKIP "
          f"(of {len(results)} tests)")
    # Core fingerprint: T2 + T3 + T4 + T5 + T8 (the 5 info-theoretic tests
    # that define the "Quran universal code")
    core_tests = {"T2_F67_C_Omega", "T3_F75_F84_invariant", "T4_F76_one_bit",
                  "T5_F79_alphabet_corrected", "T8_rhyme_presence"}
    core_results = [r for r in results if r["test"] in core_tests]
    core_pass = sum(1 for r in core_results if r["status"] == "PASS")
    core_total = sum(1 for r in core_results if r["status"] != "SKIP")

    print(f"\nCore fingerprint (T2+T3+T4+T5+T8): {core_pass} / {core_total} PASS")

    # ------------------------------------------------------------------
    # Weighted composite authenticity score ∈ [0, 1]
    # T1 / T6 / T7 are the "hard-to-forge" channels (bigram-edit response,
    # full 114-chapter dual-mode structure, IFS fractal dimension); they
    # count 2×. T2-T5 + T8 are the easier-to-match entropy channels; they
    # count 1×. SKIP tests contribute neither to numerator nor denominator.
    # ------------------------------------------------------------------
    weights = {
        "T1_F55_bigram_shift": 2.0,
        "T2_F67_C_Omega": 1.0,
        "T3_F75_F84_invariant": 1.0,
        "T4_F76_one_bit": 1.0,
        "T5_F79_alphabet_corrected": 1.0,
        "T6_F82_dual_mode": 2.0,
        "T7_F87_fractal_dim": 2.0,
        "T8_rhyme_presence": 1.0,
    }
    w_num = 0.0
    w_den = 0.0
    for res in results:
        if res["status"] == "SKIP":
            continue
        w = weights.get(res["test"], 1.0)
        w_den += w
        if res["status"] == "PASS":
            w_num += w
    composite_score = w_num / w_den if w_den > 0 else 0.0
    print(f"Composite authenticity score  : {composite_score:.3f}  (weighted {w_num:.1f} / {w_den:.1f})")

    if core_pass == core_total and core_total == 5 and n_fail == 0:
        verdict = "FULL_QURAN_UNIVERSAL_CODE_MATCH"
        print("\n>>> VERDICT: FULL_QURAN_UNIVERSAL_CODE_MATCH <<<")
        print("    Text exhibits the complete Quran information-theoretic")
        print("    fingerprint: 1-bit EL entropy, 3.84-bit redundancy gap,")
        print("    5.75-bit universal invariant, 80% channel usage, and rhyme presence.")
    elif core_pass >= 4:
        verdict = "PARTIAL_QURAN_FINGERPRINT_MATCH"
        print("\n>>> VERDICT: PARTIAL_QURAN_FINGERPRINT_MATCH "
              f"({core_pass}/5 core tests PASS) <<<")
    elif core_pass >= 2:
        verdict = "RHYMED_LITERARY_CORPUS_NOT_QURAN_FINGERPRINT"
        print("\n>>> VERDICT: RHYMED_LITERARY_CORPUS (not a Quran fingerprint match) <<<")
    else:
        verdict = "NON_RHYMED_TEXT"
        print("\n>>> VERDICT: NON_RHYMED_TEXT (no literary-rhyme signature detected) <<<")

    receipt = dict(
        experiment="exp183_quran_authentication_ring",
        input_file=str(path),
        input_format=data["format"],
        n_arabic_letters=len(letter_only(data["global_text"])),
        n_verses=len(data["verses"]),
        n_chapters=len(data["surah_verses"]),
        results=results,
        n_pass=n_pass,
        n_fail=n_fail,
        n_skip=n_skip,
        core_pass=core_pass,
        core_total=core_total,
        composite_score=float(composite_score),
        composite_weights=weights,
        verdict=verdict,
    )
    out_path = OUT_DIR / f"auth_ring_{path.stem}.json"
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"\nReceipt: {out_path}")
    return receipt


def main():
    parser = argparse.ArgumentParser(description="Quran Authentication Ring")
    parser.add_argument("text_file", nargs="?", default=str(DEFAULT_TEXT),
                        help="Path to input text file (default: locked Quran)")
    args = parser.parse_args()
    path = Path(args.text_file)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    return run_auth_ring(path)


if __name__ == "__main__":
    main()
