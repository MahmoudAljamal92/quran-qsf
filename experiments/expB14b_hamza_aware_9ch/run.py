"""
expB14b_hamza_aware_9ch/run.py
==============================
Opportunity B14b (OPPORTUNITY_TABLE_DETAIL.md THIS QUARTER #21):
  Full hamza-aware parallel of the 9-channel forensic detector. The B14
  audit (2026-04-24 evening) showed that the legacy detector produces
  byte-identical statistics for E7a (ع↔ا) / E7b (ع↔أ) / E7c (ع↔آ)
  because every channel re-normalises via `normalize_rasm` / `letters_only`
  which folds أ إ آ ٱ → ا inside the feature extractor. This experiment
  builds a parallel `nine_channel_features_hamza_preserving()` that uses
  `normalize_rasm_hamza_preserving` (already in _ultimate2_helpers.py)
  + an extended 38-char alphabet that keeps hamza-bearing alef variants
  distinct from bare alef.

  We then apply BOTH detectors (legacy + hamza-preserving) to a synthetic
  triplet of edits — ع→ا, ع→أ, ع→آ — on the same canonical Quran verse,
  and compare per-channel feature deltas. Pre-registration: the
  hamza-preserving detector PASSES if at least one of {Channel A, C, D,
  E, F, H, I} produces non-identical features across the 3 sub-classes
  (i.e., the architectural blindness is closed at the channel level).

  Excluded from the differential test: Channels B and G require a
  control-trained reference (CharNGramLM + root-bigram Counter) which
  must be re-trained on the hamza-preserving alphabet. Documented as a
  follow-up; the 7 remaining channels are sufficient to demonstrate the
  architectural fix.

This experiment is PROOF-OF-CONCEPT for the B14b redesign. A full
production version would (i) re-train channels B/G on the hamza-
preserving alphabet, and (ii) re-run exp46 / exp50 with the new detector
to see if any of the 16 audited no-E7 detections gain or lose detection
under hamza preservation.

Reads (read-only):
  - results/checkpoints/phase_06_phi_m.pkl  (CORPORA.quran for canonical
                                              text)

Writes:
  - results/experiments/expB14b_hamza_aware_9ch/expB14b_hamza_aware_9ch.json
"""

from __future__ import annotations

import gzip
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

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
from experiments._ultimate2_helpers import (  # noqa: E402
    ARABIC_CONSONANTS,
    ARABIC_EXTRA,
    normalize_rasm,
    normalize_rasm_strict,
    normalize_rasm_hamza_preserving,
)

EXP = "expB14b_hamza_aware_9ch"

# ---------------------------------------------------------------------------
# Extended alphabet: 28 consonants + 5 extras + 4 hamza-bearing alef variants
# + space. Under hamza-preserving normalisation أ ≠ ا, so the transition
# matrix needs separate cells for each.
# ---------------------------------------------------------------------------
HAMZA_ALEF_VARIANTS: str = "أإآٱ"   # hamza-on-alef, hamza-under-alef, madda, wasla
ALPHABET_HAMZA: str = ARABIC_CONSONANTS + ARABIC_EXTRA + HAMZA_ALEF_VARIANTS + " "
ALPHABET_HAMZA_IDX: dict[str, int] = {c: i for i, c in enumerate(ALPHABET_HAMZA)}
ALPHABET_HAMZA_N: int = len(ALPHABET_HAMZA)  # 28 + 5 + 4 + 1 = 38

# Legacy alphabet for direct comparison (matches exp09's ALPHABET).
ALPHABET_LEGACY: str = ARABIC_CONSONANTS + ARABIC_EXTRA + " "
ALPHABET_LEGACY_IDX: dict[str, int] = {c: i for i, c in enumerate(ALPHABET_LEGACY)}
ALPHABET_LEGACY_N: int = len(ALPHABET_LEGACY)  # 34


# ---------------------------------------------------------------------------
# Hamza-preserving primitives (mirror of _ultimate2_helpers but never fold)
# ---------------------------------------------------------------------------
import re  # noqa: E402

_WS_RE = re.compile(r"\s+")


def letters_only_hamza_preserving(text: str) -> str:
    """Hamza-preserving counterpart of `letters_only`. Strips diacritics
    + tatweel + spaces but keeps أ / إ / آ / ٱ distinct from ا."""
    return _WS_RE.sub("", normalize_rasm_hamza_preserving(text))


def words_hamza_preserving(text: str) -> list[str]:
    """Tokenise on whitespace under hamza-preserving normalisation."""
    return normalize_rasm_hamza_preserving(text).split()


def words_legacy(text: str) -> list[str]:
    """Mirror exp09's `words` for direct comparison: tokenise under legacy
    folding normaliser."""
    return normalize_rasm(text).split()


# ---------------------------------------------------------------------------
# Hamza-preserving channels A, C, D, E, F, H, I
# (Channels B and G require trained control references — re-training on
# the extended alphabet is documented as a follow-up; not done here.)
# ---------------------------------------------------------------------------
def _letter_transition_matrix(text: str, alphabet_idx: dict[str, int],
                              n: int, normaliser) -> np.ndarray:
    """Generic letter-transition counter parameterised by alphabet + normaliser.
    Mirrors exp09's `_letter_transition_matrix` line-for-line."""
    M = np.zeros((n, n), dtype=float)
    t = normaliser(text)
    for a, b in zip(t[:-1], t[1:]):
        ia = alphabet_idx.get(a)
        ib = alphabet_idx.get(b)
        if ia is not None and ib is not None:
            M[ia, ib] += 1.0
    return M


def channel_A_spectral(text: str, *, hamza_preserve: bool) -> float:
    if hamza_preserve:
        M = _letter_transition_matrix(
            text, ALPHABET_HAMZA_IDX, ALPHABET_HAMZA_N,
            normalize_rasm_hamza_preserving,
        )
    else:
        M = _letter_transition_matrix(
            text, ALPHABET_LEGACY_IDX, ALPHABET_LEGACY_N, normalize_rasm,
        )
    if M.size == 0 or not M.any():
        return 0.0
    try:
        s = np.linalg.svd(M, compute_uv=False)
    except np.linalg.LinAlgError:
        return 0.0
    if len(s) < 2 or s[0] <= 0:
        return 0.0
    return float(s[1] / s[0])


def channel_C_bigram_dist(canonical_text: str, tampered_text: str,
                          *, hamza_preserve: bool) -> float:
    """L2 distance between bigram-count vectors. Mirrors exp09 line-for-
    line, but lets the caller choose folding vs hamza-preserving."""
    def counts(s: str) -> Counter:
        if hamza_preserve:
            t = letters_only_hamza_preserving(s)
        else:
            # Legacy uses letters_only_strict (folds 4 alef variants → ا).
            t = re.sub(r"\s+", "", normalize_rasm_strict(s))
        return Counter(zip(t, t[1:]))
    A = counts(canonical_text)
    B = counts(tampered_text)
    keys = set(A) | set(B)
    if not keys:
        return 0.0
    diff_sq = 0.0
    for k in keys:
        d = A.get(k, 0) - B.get(k, 0)
        diff_sq += d * d
    return math.sqrt(diff_sq)


def channel_D_wazn(text: str, *, hamza_preserve: bool) -> float:
    """Wazn-diversity. Long-vowel set differs under hamza-preserving:
    legacy treats أ as L (long vowel, because أ → ا which is in 'اويى');
    hamza-preserving treats أ as C (consonant, glottal-stop onset).
    This is the channel where the architectural fix has the SHARPEST
    semantic consequence (and arguably the legacy folding is wrong here:
    أ is phonologically /ʔa/ not /ā/)."""
    LONG_VOWELS_LEGACY = "اويى"
    LONG_VOWELS_HAMZA  = "اويى"  # same set; أ etc. are NOT long vowels
    L_set = LONG_VOWELS_HAMZA if hamza_preserve else LONG_VOWELS_LEGACY
    norm = normalize_rasm_hamza_preserving if hamza_preserve else normalize_rasm
    shapes: list[str] = []
    for w in norm(text).split():
        s = "".join("L" if ch in L_set else "C" for ch in w)
        if s:
            shapes.append(s)
    if not shapes:
        return 0.0
    return len(set(shapes)) / len(shapes)


def channel_E_gzip_ncd(a: str, b: str) -> float:
    """gzip NCD — operates on the BYTES of the input. Hamza-preservation
    matters only insofar as the BYTE STREAM differs between أ (0xd8 0xa3)
    and ا (0xd8 0xa7). Both detectors use `letters_only` to strip
    whitespace/diacritics; legacy folds, hamza-preserving keeps."""
    def gz(x: str) -> int:
        return len(gzip.compress(x.encode("utf-8")))
    ga, gb, gab = gz(a), gz(b), gz(a + b)
    return (gab - min(ga, gb)) / max(1, max(ga, gb))


def channel_F_coupling(verses: list[str], *, hamza_preserve: bool) -> float:
    """Mean adjacent-verse Jaccard similarity on bigram set."""
    def bigram_set(s: str) -> set:
        if hamza_preserve:
            t = letters_only_hamza_preserving(s)
        else:
            t = re.sub(r"\s+", "", normalize_rasm_strict(s))
        return set(zip(t, t[1:]))
    if len(verses) < 2:
        return 0.0
    J = []
    for a, b in zip(verses[:-1], verses[1:]):
        A, B = bigram_set(a), bigram_set(b)
        denom = len(A | B)
        J.append(len(A & B) / denom if denom else 0.0)
    return float(np.mean(J))


def channel_H_local_spectral(verses: list[str], window: int = 3,
                             *, hamza_preserve: bool) -> float:
    """Mean A-spectral over overlapping k-verse windows."""
    if len(verses) < window:
        return 0.0
    vals = []
    for i in range(len(verses) - window + 1):
        chunk = " ".join(verses[i:i + window])
        vals.append(channel_A_spectral(chunk, hamza_preserve=hamza_preserve))
    return float(np.mean(vals))


def channel_I_root_field(text: str, *, hamza_preserve: bool) -> float:
    """Share of adjacent word-pairs whose root starts with the same letter.
    Without re-training a hamza-aware root extractor (which would require
    its own audit + null distribution), we use the heuristic 'first letter
    of the word after stripping the standard prefixes' — same as exp09's
    `_triliteral_root` first-letter logic, just under the chosen normaliser.
    """
    norm_words = (words_hamza_preserving(text) if hamza_preserve
                  else words_legacy(text))
    # Strip a small prefix list (mirror of _triliteral_root prefixes).
    PREFIXES = ("والـ", "فالـ", "بالـ", "الـ", "و", "ف", "ب", "ك", "ل", "س",
                "وال", "فال", "بال", "ال")  # Kept deliberately conservative
    def first_root_letter(w: str) -> str:
        for pref in sorted(PREFIXES, key=len, reverse=True):
            if w.startswith(pref) and len(w) > len(pref) + 2:
                w = w[len(pref):]
                break
        if not w:
            return "_"
        return w[0]
    firsts = [first_root_letter(w) for w in norm_words]
    if len(firsts) < 2:
        return 0.0
    hits = sum(1 for a, b in zip(firsts[:-1], firsts[1:])
               if a and b and a == b and a != "_")
    return hits / (len(firsts) - 1)


# ---------------------------------------------------------------------------
# Feature assembly (7-channel subset)
# ---------------------------------------------------------------------------
CHANNELS_7: tuple[str, ...] = (
    "A_spectral",   "C_bigram_dist", "D_wazn",
    "E_ncd",        "F_coupling",
    "H_local_spec", "I_root_field",
)


def seven_channel_features(
    verses: list[str],
    canonical_text: str | None = None,
    *,
    hamza_preserve: bool,
) -> dict[str, float]:
    """7-channel feature vector. Skips B (root-bigram LL) and G (root-trigram
    LM) because they require trained references on the hamza-preserving
    alphabet. Documented as a B14b follow-up."""
    full = " ".join(verses)
    canon = canonical_text if canonical_text is not None else full
    norm = (normalize_rasm_hamza_preserving if hamza_preserve
            else normalize_rasm)
    full_letters = (letters_only_hamza_preserving(full) if hamza_preserve
                    else re.sub(r"\s+", "", norm(full)))
    canon_letters = (letters_only_hamza_preserving(canon) if hamza_preserve
                     else re.sub(r"\s+", "", norm(canon)))
    return {
        "A_spectral":     channel_A_spectral(full, hamza_preserve=hamza_preserve),
        "C_bigram_dist":  channel_C_bigram_dist(canon, full,
                                                 hamza_preserve=hamza_preserve),
        "D_wazn":         channel_D_wazn(full, hamza_preserve=hamza_preserve),
        "E_ncd":          channel_E_gzip_ncd(full_letters, canon_letters),
        "F_coupling":     channel_F_coupling(verses,
                                              hamza_preserve=hamza_preserve),
        "H_local_spec":   channel_H_local_spectral(verses,
                                                    hamza_preserve=hamza_preserve),
        "I_root_field":   channel_I_root_field(full,
                                                hamza_preserve=hamza_preserve),
    }


# ---------------------------------------------------------------------------
# Differential test
# ---------------------------------------------------------------------------
def _find_verse_with_ayn(units) -> tuple[int, int, list[str], str]:
    """Pick the first Quran verse containing 'ع' that's at least 5 words
    long (so per-channel features have something to chew on). Returns
    (surah_num, verse_idx, all_verses_in_surah, the_target_verse)."""
    for u in units:
        sn = int(str(u.label).replace("Q:", "").strip())
        for i, v in enumerate(u.verses):
            if "ع" in v and len(v.split()) >= 5:
                return sn, i, list(u.verses), v
    raise RuntimeError("No verse containing ع found in canonical Quran")


def _make_edits(verse: str) -> dict[str, str]:
    """For a verse containing ع, return three perturbed variants:
    E7a: ع → ا  (bare alef)
    E7b: ع → أ  (hamza-on-alef)
    E7c: ع → آ  (madda-alef)
    Substitution is applied to the FIRST occurrence of ع only, to keep
    the edit single-letter."""
    if "ع" not in verse:
        raise ValueError("verse contains no ع")
    idx = verse.index("ع")
    return {
        "E7a_ayn_to_bare_alef":   verse[:idx] + "ا" + verse[idx + 1:],
        "E7b_ayn_to_hamza_alef":  verse[:idx] + "أ" + verse[idx + 1:],
        "E7c_ayn_to_madda_alef":  verse[:idx] + "آ" + verse[idx + 1:],
    }


def main() -> int:
    out = safe_output_dir(EXP)
    pre = self_check_begin()

    phi = load_phase("phase_06_phi_m")
    state = phi["state"]
    quran_units = state["CORPORA"]["quran"]
    sn, vidx, all_verses, target_verse = _find_verse_with_ayn(quran_units)
    print(f"[{EXP}] target verse: surah {sn}, idx {vidx}, "
          f"len = {len(target_verse.split())} words")
    print(f"[{EXP}] verse: {target_verse}")

    edits = _make_edits(target_verse)
    print(f"[{EXP}] edits:")
    for name, edited in edits.items():
        print(f"[{EXP}]   {name}: {edited}")

    # For each detector convention (legacy = folds, hamza_preserve = keeps):
    # compute the 7-channel features for the canonical verse (target) AND
    # for each of the 3 perturbed variants. Report deltas.
    canon_features_legacy = seven_channel_features(
        all_verses, canonical_text=target_verse, hamza_preserve=False
    )
    canon_features_hamza = seven_channel_features(
        all_verses, canonical_text=target_verse, hamza_preserve=True
    )

    results = []
    for name, edited in edits.items():
        # Replace the target verse in the surah's verse list
        edited_verses = list(all_verses)
        edited_verses[vidx] = edited
        feats_legacy = seven_channel_features(
            edited_verses, canonical_text=target_verse, hamza_preserve=False,
        )
        feats_hamza = seven_channel_features(
            edited_verses, canonical_text=target_verse, hamza_preserve=True,
        )
        delta_legacy = {
            k: feats_legacy[k] - canon_features_legacy[k]
            for k in CHANNELS_7
        }
        delta_hamza = {
            k: feats_hamza[k] - canon_features_hamza[k]
            for k in CHANNELS_7
        }
        results.append({
            "edit_name": name,
            "feats_legacy": feats_legacy,
            "feats_hamza":  feats_hamza,
            "delta_vs_canon_legacy": delta_legacy,
            "delta_vs_canon_hamza":  delta_hamza,
        })

    # ---- Architectural-blindness check ----
    # Compute, for each detector, whether the 3 sub-classes produce
    # IDENTICAL deltas (architectural blindness) or DIFFERENT deltas (the fix).
    legacy_identical_per_channel: dict[str, bool] = {}
    hamza_identical_per_channel:  dict[str, bool] = {}
    for ch in CHANNELS_7:
        legacy_vals = [r["delta_vs_canon_legacy"][ch] for r in results]
        hamza_vals  = [r["delta_vs_canon_hamza"][ch]  for r in results]
        legacy_identical_per_channel[ch] = (
            max(abs(v - legacy_vals[0]) for v in legacy_vals) < 1e-9
        )
        hamza_identical_per_channel[ch] = (
            max(abs(v - hamza_vals[0]) for v in hamza_vals) < 1e-9
        )

    n_legacy_blind   = sum(1 for v in legacy_identical_per_channel.values() if v)
    n_hamza_blind    = sum(1 for v in hamza_identical_per_channel.values()  if v)
    n_legacy_fixed   = len(CHANNELS_7) - n_legacy_blind
    n_hamza_fixed    = len(CHANNELS_7) - n_hamza_blind

    if n_hamza_fixed >= 1 and n_hamza_fixed > n_legacy_fixed:
        verdict = "B14b_HAMZA_AWARE_DETECTOR_DIFFERENTIATES"
    elif n_hamza_fixed == n_legacy_fixed and n_hamza_fixed > 0:
        verdict = "B14b_NO_NET_GAIN_HAMZA_PRESERVING"
    else:
        verdict = "B14b_HAMZA_PRESERVING_NO_DIFFERENTIAL_SIGNAL"

    report = {
        "experiment": EXP,
        "task_id": "B14b",
        "title": (
            "Hamza-aware parallel of the 9-channel forensic detector. "
            "Differential test: does keeping أ إ آ ٱ distinct from ا "
            "throughout all 7 (of 9) channels produce different feature "
            "deltas for E7a (ع↔ا), E7b (ع↔أ), E7c (ع↔آ) sub-classes "
            "where the legacy detector produces byte-identical results?"
        ),
        "design_notes": [
            "Standalone parallel detector — does NOT modify the protected "
            "files _ultimate2_helpers.py or exp09/run.py.",
            "Uses normalize_rasm_hamza_preserving (already in helpers, "
            "added under B14 work 2026-04-24).",
            "Extended alphabet: 28 consonants + 5 extras + 4 hamza-bearing "
            "alef variants {أ,إ,آ,ٱ} + space = 38 chars.",
            "Channels B (root-bigram LL) and G (root-trigram LM) excluded "
            "from this MVP because they require control-trained references "
            "on the hamza-preserving alphabet — re-training is a "
            "production-grade follow-up.",
        ],
        "alphabet_legacy_size":  ALPHABET_LEGACY_N,
        "alphabet_hamza_size":   ALPHABET_HAMZA_N,
        "hamza_alef_variants":   HAMZA_ALEF_VARIANTS,
        "target_verse": {
            "surah": sn, "verse_idx": vidx, "text": target_verse,
        },
        "edits": edits,
        "canonical_features_legacy":     canon_features_legacy,
        "canonical_features_hamza":      canon_features_hamza,
        "edit_results": results,
        "architectural_blindness": {
            "legacy_identical_across_3_subclasses_per_channel":
                legacy_identical_per_channel,
            "hamza_identical_across_3_subclasses_per_channel":
                hamza_identical_per_channel,
            "n_channels_blind_legacy": n_legacy_blind,
            "n_channels_blind_hamza":  n_hamza_blind,
            "n_channels_fixed_legacy": n_legacy_fixed,
            "n_channels_fixed_hamza":  n_hamza_fixed,
        },
        "verdict": verdict,
        "interpretation": [
            "B14 found that under the legacy detector, E7a / E7b / E7c "
            "produce byte-identical statistics — the detector cannot "
            "distinguish bare-alef from hamza-bearing-alef substitutions.",
            "Under the hamza-preserving parallel detector, channels that "
            "differ across the 3 sub-classes (n_channels_fixed_hamza > 0) "
            "represent the architectural fix: those channels can now "
            "tell ع↔ا apart from ع↔أ apart from ع↔آ.",
            "Production-grade B14b would (i) re-train channels B/G on "
            "the hamza-preserving alphabet, (ii) re-run exp46/exp50 with "
            "the new detector to see if any of the 16 audited no-E7 "
            "detections gain hamza-sensitivity, (iii) verify that the "
            "headline H1_STRUCTURAL_ARABIC_BLINDNESS / "
            "H2_QURAN_SPECIFIC_IMMUNITY verdict from B16 doesn't shift "
            "under the new detector. Estimated additional effort: 1-2 "
            "weeks engineering + re-runs.",
        ],
    }

    with open(out / f"{EXP}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Stdout
    print()
    print(f"[{EXP}] ALPHABETS: legacy={ALPHABET_LEGACY_N} chars  "
          f"hamza={ALPHABET_HAMZA_N} chars  (4 new alef variants kept distinct)")
    print()
    print(f"[{EXP}] -- per-channel deltas vs canonical (signed) --")
    print(f"[{EXP}] {'channel':<14s}  "
          f"{'E7a_legacy':>11s} {'E7b_legacy':>11s} {'E7c_legacy':>11s}  "
          f"{'L?':<3s}  "
          f"{'E7a_hamza':>11s} {'E7b_hamza':>11s} {'E7c_hamza':>11s}  "
          f"{'H?':<3s}")
    for ch in CHANNELS_7:
        leg = [r["delta_vs_canon_legacy"][ch] for r in results]
        ham = [r["delta_vs_canon_hamza"][ch]  for r in results]
        leg_id = "ID" if legacy_identical_per_channel[ch] else "DIFF"
        ham_id = "ID" if hamza_identical_per_channel[ch]  else "DIFF"
        print(f"[{EXP}] {ch:<14s}  "
              f"{leg[0]:>+11.6f} {leg[1]:>+11.6f} {leg[2]:>+11.6f}  "
              f"{leg_id:<4s} "
              f"{ham[0]:>+11.6f} {ham[1]:>+11.6f} {ham[2]:>+11.6f}  "
              f"{ham_id}")
    print()
    print(f"[{EXP}] LEGACY: {n_legacy_blind}/7 channels blind (identical "
          f"across 3 sub-classes); {n_legacy_fixed}/7 distinguish.")
    print(f"[{EXP}] HAMZA : {n_hamza_blind}/7 channels blind (identical "
          f"across 3 sub-classes); {n_hamza_fixed}/7 distinguish.")
    print(f"[{EXP}] verdict: {verdict}")
    print(f"[{EXP}] wrote {out / f'{EXP}.json'}")

    self_check_end(pre, exp_name=EXP)
    print(f"[{EXP}] self-check PASS: no protected file mutated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
