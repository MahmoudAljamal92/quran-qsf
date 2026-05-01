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

    # --- SHORT-INPUT AMBIGUITY AUDIT (user-reported issue) ---------------
    # These are the exact cases the user pressed us on: single common Arabic
    # words that appear in the Quran but also in every Arabic text ever
    # written. Honest behaviour is NOT to call them QURAN_VERBATIM.

    ("Single word كتب (3 letters, very common Arabic root)",
     "كتب",
     "TOO_SHORT"),

    ("Single word الله (4 letters, ubiquitous in Arabic)",
     "الله",
     "QURAN_SUBSTRING_AMBIGUOUS"),

    ("Single word الرحمن (6 letters, Quranic but everyday)",
     "الرحمن",
     "QURAN_SUBSTRING_AMBIGUOUS"),

    ("Two-word phrase الحمد لله (ubiquitous liturgical)",
     "الحمد لله",
     "QURAN_SUBSTRING_AMBIGUOUS"),

    ("Three-word phrase بسم الله الرحمن (partial Basmala)",
     "بسم الله الرحمن",
     "QURAN_SUBSTRING_AMBIGUOUS"),

    ("Full Basmala (short AND very common formula)",
     "بسم الله الرحمن الرحيم",
     "QURAN_SUBSTRING_AMBIGUOUS"),

    ("Single-word Quranic rarity مدهامتان (Rahman 55:64, unique)",
     "مدهامتان",
     "QURAN_VERBATIM"),  # 8 letters AND occurs exactly once ⇒ distinctive

    ("Non-Quranic short Arabic phrase (قهوة الصباح لذيذة)",
     "قهوة الصباح لذيذة",
     None),  # may be NOT_QURAN or TOO_SHORT depending on fuzzy — accept either

    ("Garbage Arabic letters (ططططط)",
     "ططططط",
     None),
]

passed = failed = 0
for label, text, expected in cases:
    c = classify(text)
    ok = (expected is None) or (c.verdict == expected)
    status = "PASS" if ok else "FAIL"
    if ok: passed += 1
    else: failed += 1
    print(f"[{status}] {label}")
    print(f"        verdict      = {c.verdict}  (confidence: {c.confidence})")
    print(f"        deviation    = {c.deviation_pct:.2%}  (input letters = {c.n_input_letters})")
    if c.occurrence_count:
        print(f"        occurrences  = {c.occurrence_count}  (times this exact substring appears in the Quran)")
    if c.verbatim:
        v = c.verbatim
        print(f"        location     = Surah {v.surah_start}:{v.verse_start} -> {v.surah_end}:{v.verse_end} "
              f"({v.n_verses_spanned} verses)")
    if c.fuzzy:
        f = c.fuzzy
        print(f"        closest      = Surah {f.surah_start}:{f.verse_start} -> {f.surah_end}:{f.verse_end} "
              f"(edit distance = {f.edit_distance})")
    if c.rationale:
        # wrap long rationale
        r = c.rationale
        print(f"        rationale    = {r}")
    if expected and not ok:
        print(f"        EXPECTED     = {expected}")
    print()

print(f"=== {passed} passed, {failed} failed ===")
