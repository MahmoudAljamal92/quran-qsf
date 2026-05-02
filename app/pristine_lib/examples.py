"""examples.py — eight demo presets covering every detection mode.

Each preset has:
  id        : short slug
  label     : 1-line UI label
  expected  : 1-line expected verdict (cosmetic; not used for scoring)
  text      : raw input string

Texts are short and either (a) drawn from the canonical Hafs corpus,
(b) drawn from public-domain classical Arabic / Hebrew poetry, or
(c) authored inline (for the modern-prose example). All examples are
purely illustrative and play no role in scoring.
"""
from __future__ import annotations

# Surah 100 (Al-Adiyat) — verses 1-11, canonical Hafs (matches quran_bare.txt).
_SURAH_100 = """\
بسم الله الرحمن الرحيم والعاديات ضبحا
فالموريات قدحا
فالمغيرات صبحا
فأثرن به نقعا
فوسطن به جمعا
إن الإنسان لربه لكنود
وإنه على ذلك لشهيد
وإنه لحب الخير لشديد
أفلا يعلم إذا بعثر ما في القبور
وحصل ما في الصدور
إن ربهم بهم يومئذ لخبير"""

# Same surah with ONE letter changed in verse 1 (ع -> غ in العاديات).
_SURAH_100_ONE_EDIT = """\
بسم الله الرحمن الرحيم والغاديات ضبحا
فالموريات قدحا
فالمغيرات صبحا
فأثرن به نقعا
فوسطن به جمعا
إن الإنسان لربه لكنود
وإنه على ذلك لشهيد
وإنه لحب الخير لشديد
أفلا يعلم إذا بعثر ما في القبور
وحصل ما في الصدور
إن ربهم بهم يومئذ لخبير"""

# Same surah with verses 2 and 3 swapped (verbatim letters; structure broken).
_SURAH_100_VERSE_SWAP = """\
بسم الله الرحمن الرحيم والعاديات ضبحا
فالمغيرات صبحا
فالموريات قدحا
فأثرن به نقعا
فوسطن به جمعا
إن الإنسان لربه لكنود
وإنه على ذلك لشهيد
وإنه لحب الخير لشديد
أفلا يعلم إذا بعثر ما في القبور
وحصل ما في الصدور
إن ربهم بهم يومئذ لخبير"""

# Mu'allaqa of Imru' al-Qais (opening; pre-Islamic, public domain).
_MUALLAQA = """\
قفا نبك من ذكرى حبيب ومنزل
بسقط اللوى بين الدخول فحومل
فتوضح فالمقراة لم يعف رسمها
لما نسجتها من جنوب وشمأل
ترى بعر الآرام في عرصاتها
وقيعانها كأنه حب فلفل
كأني غداة البين يوم تحملوا
لدى سمرات الحي ناقف حنظل
وقوفا بها صحبي علي مطيهم
يقولون لا تهلك أسى وتجمل
وإن شفائي عبرة مهراقة
فهل عند رسم دارس من معول
كدأبك من أم الحويرث قبلها
وجارتها أم الرباب بمأسل
إذا قامتا تضوع المسك منهما
نسيم الصبا جاءت بريا القرنفل"""

# Modern Arabic prose (authored inline; news-style, no rhyme).
_MODERN_PROSE = """\
أعلنت الحكومة اليوم عن خطة جديدة لتطوير قطاع التعليم
وقالت وزيرة التربية في مؤتمر صحفي إن الميزانية المخصصة
ستتضاعف خلال السنوات الخمس المقبلة
وأضافت أن الأولوية ستكون لتحسين البنية التحتية للمدارس
وتدريب المعلمين على استخدام التكنولوجيا الحديثة
كما أشارت إلى أن المناهج الدراسية ستخضع لمراجعة شاملة
بهدف مواكبة التطورات العالمية في مجالي العلوم والرياضيات
وأكدت أن الحكومة تعمل بالتعاون مع منظمات دولية
لضمان جودة التعليم في جميع المراحل الدراسية"""

# Psalm 23 (Hebrew, public domain).
_PSALM_23 = """\
מזמור לדוד יהוה רעי לא אחסר
בנאות דשא ירביצני על מי מנחות ינהלני
נפשי ישובב ינחני במעגלי צדק למען שמו
גם כי אלך בגיא צלמות לא אירא רע
כי אתה עמדי שבטך ומשענתך המה ינחמני
תערך לפני שלחן נגד צררי
דשנת בשמן ראשי כוסי רויה
אך טוב וחסד ירדפוני כל ימי חיי
ושבתי בבית יהוה לארך ימים"""

# Random nonsense / extremely short input (tests short-input guard).
_TINY = "abc 123 ✨"


PRESETS = [
    {
        "id": "verbatim_quran",
        "label": "Verbatim Quran — Surah 100 (Al-Adiyat, 11 verses)",
        "expected": "Layer A: ✓ verbatim · Layer B: 100% match · Layer C: no tampering",
        "text": _SURAH_100,
    },
    {
        "id": "one_letter_edit",
        "label": "Modified Quran — 1 letter changed (ع → غ in verse 1)",
        "expected": "Layer A: ≈ near-Quran (1 letter) · Layer C1 fires (Δ_bigram = 2)",
        "text": _SURAH_100_ONE_EDIT,
    },
    {
        "id": "verse_swap",
        "label": "Modified Quran — 2 verses swapped (letters preserved)",
        "expected": "Layer A: ≈ same letters · Layer C2 fires (gzip-NCD ↑)",
        "text": _SURAH_100_VERSE_SWAP,
    },
    {
        "id": "muallaqa",
        "label": "Pre-Islamic poetry — Mu'allaqa of Imru' al-Qais",
        "expected": "Layer A: ✗ not in corpus · Layer B: ~25-50% (rhymed but not Quranic)",
        "text": _MUALLAQA,
    },
    {
        "id": "modern_prose",
        "label": "Modern Arabic prose — news-style article",
        "expected": "Layer A: ✗ not in corpus · Layer B: <30% (no rhyme spine)",
        "text": _MODERN_PROSE,
    },
    {
        "id": "psalm_23",
        "label": "Hebrew Psalm 23 (Tanakh)",
        "expected": "Layer A: ✗ not Arabic · Layer B: <20% to Quran's Arabic-rasm fingerprint",
        "text": _PSALM_23,
    },
    {
        "id": "tiny",
        "label": "Too-short input (under guard threshold)",
        "expected": "All layers: insufficient text — guard raised",
        "text": _TINY,
    },
]


def by_id(preset_id: str):
    for p in PRESETS:
        if p["id"] == preset_id:
            return p
    return None


__all__ = ["PRESETS", "by_id"]
