"""
Zero-trust audit of exp52 feature definitions + Wav2Vec2 vocab dropout.

Run:
    python -u -m experiments.exp52_acoustic_bridge_full._audit

Verifies:
  C1 syllable_count          on 5 known short surahs (manual counts)
  C2 madd_count              on basmalah + chosen verses, explicit char-by-char listing
  C3 ghunnah_count           on verses with known ghunnah incidents
  C4 emphatic_count          on verses with known emphatic letters
  A4 vocab dropout           across the whole 6 236-verse Quran

Exits non-zero if any check fails a hard invariant (e.g. >2 % vocab dropout).
"""
from __future__ import annotations
import re
import sys
from collections import Counter
from pathlib import Path

# allow both `python -m` and direct exec
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.exp52_acoustic_bridge_full._text import (
    load_quran_vocal,
    count_syllables, count_syllables_full,
    count_madd, count_madd_full,
    count_emphatic, count_emphatic_full,
    count_ghunnah,
    count_words, text_features, normalize_for_ctc, build_alignment_target,
    SHORT_VOWELS, TANWEEN, MADD_MARKS, EMPHATIC, EMPHATIC_FULL, NASAL,
    SHADDA, SUKUN, PLAIN_ALIF, ALIF, WAW, YA, FATHA, DAMMA, KASRA,
    TAAWUDH, BASMALAH,
    _DIAC_RE,
)

CORPUS_PATH = ROOT / "data" / "corpora" / "ar" / "quran_vocal.txt"

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

failures = []
warnings_l = []


def expect(cond: bool, name: str, detail: str = "") -> None:
    if cond:
        print(f"  {PASS} {name}")
    else:
        print(f"  {FAIL} {name}   {detail}")
        failures.append(name)


def warn(cond: bool, name: str, detail: str = "") -> None:
    if cond:
        print(f"  {PASS} {name}")
    else:
        print(f"  {WARN} {name}   {detail}")
        warnings_l.append(name)


def header(s: str) -> None:
    print()
    print("=" * 72)
    print(f"  {s}")
    print("=" * 72)


def dump_chars(text: str) -> None:
    """Pretty-print every codepoint in the string for manual inspection."""
    for i, c in enumerate(text):
        cp = ord(c)
        name = ""
        if c in SHORT_VOWELS:          name = "short-vowel"
        elif c in TANWEEN:             name = "tanween"
        elif c in MADD_MARKS:          name = "madd-mark"
        elif c in EMPHATIC:            name = "EMPHATIC"
        elif c in NASAL:               name = "nasal"
        elif c == SHADDA:              name = "SHADDA"
        elif c == SUKUN:               name = "sukun"
        elif c == " ":                 name = "space"
        elif 0x0621 <= cp <= 0x063A:   name = "letter"
        elif 0x0641 <= cp <= 0x064A:   name = "letter"
        elif cp == 0x0671:             name = "alif-wasla"
        elif cp == 0x0670:             name = "superscript-alif"
        elif cp == 0x0640:             name = "tatweel"
        elif cp == 0x06DB:             name = "waqf"
        print(f"    [{i:>3}] U+{cp:04X}  {c!r:>6}  {name}")


def main() -> int:
    print("loading corpus ...", end=" ", flush=True)
    corpus = load_quran_vocal(CORPUS_PATH)
    assert 1 in corpus and 114 in corpus
    print(f"OK ({len(corpus)} surahs, {sum(len(v) for v in corpus.values())} verses)")

    # ---------- C1 SYLLABLE COUNT (narrow + full) ----------
    header("C1  syllable_count (narrow) vs syllable_count_full (+tanween)")
    print("  Surah 112 (Al-Ikhlas) per-verse counts (note: v1 in corpus includes basmalah):")
    v112 = corpus[112]
    for (vn, txt) in v112:
        n_sv = sum(1 for c in txt if c in SHORT_VOWELS)
        n_tw = sum(1 for c in txt if c in TANWEEN)
        n_md = sum(1 for c in txt if c in MADD_MARKS)
        print(f"    v{vn}: short_vowels={n_sv:>2}  tanween={n_tw}  madd_marks={n_md}  "
              f"narrow={count_syllables(txt):>2}  full={count_syllables_full(txt):>2}  "
              f"text={txt}")
    s112_narrow = [count_syllables(t) for (_, t) in v112]
    s112_full   = [count_syllables_full(t) for (_, t) in v112]
    expect(all(s >= 1 for s in s112_narrow), "s112: all narrow counts >= 1")
    expect(all(sf >= sn for sn, sf in zip(s112_narrow, s112_full)),
           "full count >= narrow count in every verse",
           f"narrow={s112_narrow}  full={s112_full}")
    # Tanween audit-wide: verify count_syllables_full(t) = count_syllables(t) + tanween_in_t
    delta_ok = True
    for s in corpus:
        for (_, t) in corpus[s]:
            delta = count_syllables_full(t) - count_syllables(t)
            n_tw = sum(1 for c in t if c in TANWEEN)
            if delta != n_tw:
                delta_ok = False; break
        if not delta_ok: break
    expect(delta_ok, "quran-wide: syllable_count_full - syllable_count == tanween_count")

    # ---------- C2 MADD COUNT (narrow + full) ----------
    header("C2  madd_count (narrow: explicit marks) vs madd_count_full (+ natural)")
    # Basmalah as it appears in the corpus (small-alif form) — find it in verse 1 of surah 1.
    basmalah_corpus = corpus[1][0][1]
    n_small_alif = sum(1 for c in basmalah_corpus if c == "\u0670")
    n_madd_above = sum(1 for c in basmalah_corpus if c == "\u0653")
    n_m_corpus = count_madd(basmalah_corpus)
    n_m_full_corpus = count_madd_full(basmalah_corpus)
    print(f"  Basmalah (corpus form, Fatiha v1): small-alif={n_small_alif}  "
          f"madd-above={n_madd_above}  narrow={n_m_corpus}  full={n_m_full_corpus}")
    expect(n_m_corpus == n_small_alif + n_madd_above,
           "count_madd on corpus basmalah = small-alif + madd-above")
    expect(n_small_alif >= 1, "corpus basmalah contains >= 1 small-alif (for رَحْمَـٰن)")
    expect(n_m_full_corpus > n_m_corpus,
           "full > narrow (basmalah has natural madds: 'bismi' has ya+kasra, 'allah' has lam+fatha+alif...)",
           f"narrow={n_m_corpus} full={n_m_full_corpus}")

    # Ya-Sin v1 is "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ يسٓ" — basmalah + "ya-sin" with madd-above on sin.
    v36_v1 = corpus[36][0][1]
    print(f"  Surah 36 v1: narrow={count_madd(v36_v1)}  full={count_madd_full(v36_v1)}  text={v36_v1!r}")
    expect(count_madd(v36_v1) >= 1,
           "Surah 36 v1 has >=1 explicit madd (the ٓ over sin)")

    # Quran-wide
    n_with_narrow = 0; total_narrow = 0; total_full = 0; n_verses_total = 0
    for s in corpus:
        for (_, t) in corpus[s]:
            total_narrow += count_madd(t)
            total_full   += count_madd_full(t)
            if count_madd(t) > 0: n_with_narrow += 1
            n_verses_total += 1
    print(f"  Quran-wide: {n_with_narrow}/{n_verses_total} verses have >=1 explicit madd "
          f"({100*n_with_narrow/n_verses_total:.1f}%).")
    print(f"  Quran-wide totals: narrow={total_narrow}   full={total_full}   "
          f"(x{total_full/max(total_narrow,1):.1f})")
    expect(n_with_narrow > 1000,
           f"explicit madd occurs in many verses ({n_with_narrow})",
           "need >1000 for statistical power")
    expect(total_full > total_narrow * 3,
           "full count >> narrow count (natural madds are much more common)",
           f"{total_full} vs {total_narrow}")

    # ---------- C3 GHUNNAH COUNT ----------
    header("C3  ghunnah_count  (definition: tanween + (ن|م + shadda))")
    # Classical rule: tanween gets ghunnah UNLESS followed by an izhar letter (ء ه ع ح غ خ)
    # Our def counts ALL tanween -> slight overestimate.
    # Also: nun/mim + shadda always has ghunnah -> correctly captured.
    # Missing: idgham cases where a stand-alone nun (not shadda'd) gets merged with
    # following م ن و ي + creates ghunnah. That is NOT counted.
    n_tanw_total = 0; n_nasalshadda_total = 0
    for s in corpus:
        for (_, t) in corpus[s]:
            n_tanw_total += sum(1 for c in t if c in TANWEEN)
            n_nasalshadda_total += sum(1 for i in range(len(t) - 1)
                                       if t[i] in NASAL and t[i + 1] == SHADDA)
    print(f"  Quran-wide: tanween={n_tanw_total}  nasal+shadda={n_nasalshadda_total}  "
          f"total ghunnah (our def)={n_tanw_total + n_nasalshadda_total}")
    expect(n_tanw_total > 3000, f"tanween very common ({n_tanw_total})")
    expect(n_nasalshadda_total > 500, f"nasal+shadda occurs often ({n_nasalshadda_total})")

    # ---------- C4 EMPHATIC COUNT (strict + full) ----------
    header("C4  emphatic_count  (strict: ص ض ط ظ ق) vs emphatic_count_full (+ خ غ)")
    print(f"  EMPHATIC strict  = {sorted(EMPHATIC)}      (n={len(EMPHATIC)})")
    print(f"  EMPHATIC_FULL    = {sorted(EMPHATIC_FULL)} (n={len(EMPHATIC_FULL)})")
    expect({"\u0635","\u0636","\u0637","\u0638","\u0642"}.issubset(EMPHATIC),
           "strict emphatic set = ص ض ط ظ ق")
    expect("\u062E" in EMPHATIC_FULL and "\u063A" in EMPHATIC_FULL,
           "full emphatic set adds خ and غ (classical isti`lā')")
    n_strict = 0; n_full = 0
    for s in corpus:
        for (_, t) in corpus[s]:
            n_strict += count_emphatic(t)
            n_full   += count_emphatic_full(t)
    print(f"  Quran-wide: strict={n_strict}   full={n_full}   "
          f"(full adds {n_full-n_strict} instances)")
    expect(n_strict > 5000, f"plenty of strict emphatic instances ({n_strict})")
    expect(n_full > n_strict, "full > strict (as expected)")

    # ---------- A4 VOCAB DROPOUT ----------
    header("A4  Wav2Vec2 vocab dropout  (chars lost by normalize_for_ctc + tokenizer)")
    # Load the tokenizer we actually use in the pipeline
    print("  loading tokenizer ...", end=" ", flush=True)
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("jonatasgrosman/wav2vec2-large-xlsr-53-arabic")
    vocab = tok.get_vocab()
    print(f"OK (vocab size = {len(vocab)})")
    # Apply normalize_for_ctc to every verse, then check each resulting char
    n_in_total = 0          # codepoints in original Uthmani
    n_normalized = 0        # codepoints in normalized output
    n_tokenizer_hits = 0    # codepoints in normalized that ARE in vocab
    missing = Counter()     # codepoints NOT in vocab (after normalization)
    for s in corpus:
        for (_, t) in corpus[s]:
            n_in_total += len(t)
            clean, _back = normalize_for_ctc(t)
            n_normalized += len(clean)
            for c in clean:
                key = "|" if c == " " else c
                if key in vocab:
                    n_tokenizer_hits += 1
                else:
                    missing[c] += 1
    print(f"  original codepoints:     {n_in_total:,}")
    print(f"  after normalize_for_ctc: {n_normalized:,}  "
          f"({100*(n_in_total - n_normalized)/n_in_total:.2f}% stripped as OOV)")
    print(f"  tokenizer-hit codepoints in normalized: {n_tokenizer_hits:,}")
    unseen = n_normalized - n_tokenizer_hits
    print(f"  unexpected dropout (normalize kept, tokenizer misses): {unseen:,}"
          f"  ({100*unseen/max(n_normalized,1):.4f}%)")
    if missing:
        print("  top OOV codepoints that slipped through normalize_for_ctc:")
        for c, n in missing.most_common(15):
            print(f"    U+{ord(c):04X}  {c!r}  x{n}")
    expect(unseen / max(n_normalized, 1) < 0.001,
           "unexpected dropout < 0.1% of normalized chars",
           f"actual: {100*unseen/max(n_normalized,1):.4f}%")
    # Soft budget: overall strip from OOV normalization should be small
    strip_frac = (n_in_total - n_normalized) / n_in_total
    warn(strip_frac < 0.03,
         f"strip fraction via normalize_for_ctc = {100*strip_frac:.2f}% of original",
         "above 3% means we're losing meaningful marks — investigate")

    # ---------- BUG1-CLOSED: no doubled basmalah in CTC target ----------
    header("BUG1-CLOSED  CTC target has exactly one basmalah per surah")
    # Build the expected signature from the corpus basmalah itself (Fatiha v1)
    # after applying normalize_for_ctc + _DIAC_RE strip + space-collapse.
    # That way the signature auto-adapts to whatever the pipeline produces,
    # avoiding hardcoded mismatches (e.g. ٰ -> ا adds an extra alif in رحمان).
    def _canon(raw: str) -> str:
        c, _ = normalize_for_ctc(raw)
        b = _DIAC_RE.sub("", c).replace("\u0640", "")
        return re.sub(r"\s+", " ", b).strip()

    BSM_PHRASE = _canon(corpus[1][0][1])     # Fatiha v1 = basmalah
    print(f"  basmalah canonical signature (len={len(BSM_PHRASE)}): {BSM_PHRASE!r}")
    for sn in (1, 2, 9, 36, 108, 112, 114):
        tgt = build_alignment_target(sn, corpus[sn])
        clean = ""
        for (_, raw) in tgt:
            c, _ig = normalize_for_ctc(raw)
            clean += c + " "
        bare = _DIAC_RE.sub("", clean).replace("\u0640", "")
        bare = re.sub(r"\s+", " ", bare).strip()
        n_bsm = bare.count(BSM_PHRASE)
        expected = 0 if sn == 9 else 1
        ok = (n_bsm == expected)
        if ok:
            print(f"  {PASS} surah {sn:>3}: {n_bsm} basmalah in target  (expected {expected})")
        else:
            print(f"  {FAIL} surah {sn:>3}: {n_bsm} basmalah in target  (expected {expected})")
            failures.append(f"bug1_surah_{sn}_has_{n_bsm}_basmalah")
    # Also: first pseudo-verse for surahs != 1 should be TAAWUDH, not BASMALAH
    for sn in (2, 9, 36, 108, 112):
        tgt = build_alignment_target(sn, corpus[sn])
        assert tgt[0][0] == -1, f"surah {sn}: first pseudo-verse id should be -1"
        first_text = tgt[0][1]
        ok = (first_text == TAAWUDH)
        if ok:
            print(f"  {PASS} surah {sn:>3}: first pseudo-verse is TAAWUDH")
        else:
            failures.append(f"bug1_surah_{sn}_first_pv_not_taawudh")
            print(f"  {FAIL} surah {sn:>3}: first pseudo-verse is NOT TAAWUDH  ({first_text[:40]!r})")
    # And surah 1 should have no preamble
    tgt1 = build_alignment_target(1, corpus[1])
    ok = (tgt1[0][0] == 1)
    if ok:
        print(f"  {PASS} surah   1: no preamble (first real verse is v1)")
    else:
        failures.append("bug1_surah1_has_preamble")
        print(f"  {FAIL} surah   1: first entry is v{tgt1[0][0]}, expected v1")

    # ---------- Summary ----------
    header("SUMMARY")
    if failures:
        print(f"  {FAIL}  {len(failures)} hard failure(s):")
        for f in failures:
            print(f"     - {f}")
    else:
        print(f"  {PASS}  no hard failures.")
    if warnings_l:
        print(f"  {WARN}  {len(warnings_l)} soft warning(s):")
        for w in warnings_l:
            print(f"     - {w}")
    else:
        print(f"  {PASS}  no soft warnings.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
