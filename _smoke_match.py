"""Smoke test for app/quran_match.py — must pass before wiring into the UI."""
from app.quran_match import classify, load_quran, normalise

# Warm cache
verses, flat_norm, _ = load_quran()
print(f"Loaded {len(verses)} verses, flat normalised length = {len(flat_norm)} chars")
print()

cases = [
    # (label, text, expected_verdict)
    ("Al-Fatiha exact (full)",
     """بسم الله الرحمن الرحيم
الحمد لله رب العالمين
الرحمن الرحيم
مالك يوم الدين
إياك نعبد وإياك نستعين
اهدنا الصراط المستقيم
صراط الذين أنعمت عليهم غير المغضوب عليهم ولا الضالين""",
     "QURAN_VERBATIM"),

    ("Al-Fatiha with 1 letter changed (مالك → ماللك)",
     """بسم الله الرحمن الرحيم
الحمد لله رب العالمين
الرحمن الرحيم
ماللك يوم الدين
إياك نعبد وإياك نستعين
اهدنا الصراط المستقيم
صراط الذين أنعمت عليهم غير المغضوب عليهم ولا الضالين""",
     "MODIFIED_QURAN"),

    ("Al-Adiyat v1 exact",
     "والعاديات ضبحا",
     "QURAN_VERBATIM"),

    ("Al-Adiyat v1 with ع→غ (والعاديات → والغاديات)",
     "والغاديات ضبحا",
     "MODIFIED_QURAN"),

    ("Al-Adiyat v1 with ض→ص (ضبحا → صبحا)",
     "والعاديات صبحا",
     "MODIFIED_QURAN"),

    ("3 verses of Al-Baqara (exact)",
     "الم ذلك الكتاب لا ريب فيه هدى للمتقين الذين يؤمنون بالغيب ويقيمون الصلاة ومما رزقناهم ينفقون",
     "QURAN_VERBATIM"),

    ("Random Arabic poetry (not Quran)",
     "قف بنا نبكي على ذكرى حبيب ومنزل بسقط اللوى بين الدخول فحومل",
     "NOT_QURAN"),

    ("English text",
     "The quick brown fox jumps over the lazy dog repeatedly.",
     "NOT_QURAN"),

    ("Very short fragment (1 word from Quran)",
     "الرحمن",
     None),  # legitimately ambiguous — could be verbatim
]

passed = failed = 0
for label, text, expected in cases:
    c = classify(text)
    ok = (expected is None) or (c.verdict == expected)
    status = "PASS" if ok else "FAIL"
    if ok: passed += 1
    else: failed += 1
    print(f"[{status}] {label}")
    print(f"        verdict   = {c.verdict}")
    print(f"        deviation = {c.deviation_pct:.2%}  (input letters = {c.n_input_letters})")
    if c.verbatim:
        v = c.verbatim
        print(f"        location  = Surah {v.surah_start}:{v.verse_start} -> {v.surah_end}:{v.verse_end} "
              f"({v.n_verses_spanned} verses)")
    if c.fuzzy:
        f = c.fuzzy
        print(f"        closest   = Surah {f.surah_start}:{f.verse_start} -> {f.surah_end}:{f.verse_end} "
              f"(edit distance = {f.edit_distance})")
    if expected and not ok:
        print(f"        EXPECTED  = {expected}")
    print()

print(f"=== {passed} passed, {failed} failed ===")
