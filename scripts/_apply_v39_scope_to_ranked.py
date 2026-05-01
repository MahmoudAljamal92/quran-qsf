"""scripts/_apply_v39_scope_to_ranked.py
==============================================
One-shot updater: bump RANKED_FINDINGS.md to V3.9 and add the
F63/F64 GENRE-SCOPE AUDIT V3.9 note to the F63 row.
"""
from __future__ import annotations
from pathlib import Path

p = Path("docs/reference/findings/RANKED_FINDINGS.md")
text = p.read_text(encoding="utf-8")

# Update version banner
old_v = "**Version**: 3.8 (2026-04-29 morning, **v7.9-cand patch H V3.8 - F63 SCOPE AUDIT"
new_v = (
    "**Version**: 3.9 (2026-04-29 morning, **v7.9-cand patch H V3.9 - "
    "F63/F64 GENRE-SCOPE AUDIT: scope corrected from \"most rhymed text\" to "
    "\"religious-narrative-prose extremum\"; classical Arabic qasida poetry "
    "per-bayt almost certainly beats Quran by rāwī-rule but cannot be "
    "measured from our data because available poetry corpora do not preserve "
    "real bayt boundaries; Quran 36:69 disclaims being poetry; "
    "Quran achieves sajʿ-density approaching qasida-density while functioning "
    "as religious-narrative-text**). Earlier: 3.8 (V3.8 - F63 SCOPE AUDIT"
)
if old_v in text:
    text = text.replace(old_v, new_v)
    print("[OK] Version banner updated 3.8 -> 3.9")
else:
    print("[WARN] Version banner anchor not found")

# Insert V3.9 GENRE-SCOPE AUDIT in F63 row right before "PREREG h" (which
# was the V3.8 lead-in to the PREREG hash citation)
old_anchor = " **PREREG h"
new_text = (
    " **V3.9 GENRE-SCOPE AUDIT (2026-04-29 morning, post-V3.8 reviewer critique)**: "
    "F63 framing was over-broad. **Classical Arabic qasida poetry per-bayt rhymes "
    "uniformly by *rāwī*-rule (per-poem p_max approaches 1.0), and would beat the "
    "Quran on rhyme uniformity if measured per-bayt.** Our poetry corpora do NOT "
    "preserve real bayt boundaries (HuggingFace `arbml/Ashaar` stores poems as flat "
    "word strings; bayt-count-aligned chunking gives per-poem p_max ≈ 0.30, but this "
    "is a unit-resolution artefact — chunking drift over variable-length bayts "
    "randomises end-letter). The 50-hemistich window p_max on `poetry.txt` (median "
    "0.46, p90 0.62) is below Quran 0.7273, but this is hemistich (half-bayt) "
    "granularity where only every other line rhymes. **Corrected scope (V3.9 lock)**: "
    "F63/F64 is the rhyme-extremum among **canonical RELIGIOUS-NARRATIVE-PROSE texts** "
    "(Quran + Tanakh + Greek NT + Pāli DN+MN + Avestan Yasna + Arabic Bible + Sanskrit "
    "Rigveda), NOT among all-text. **Quran 36:69** (`وَمَا عَلَّمْنَاهُ الشِّعْرَ "
    "وَمَا يَنبَغِي لَهُ`) explicitly disclaims being poetry; the genre is *rhymed "
    "prose (sajʿ)*, not *qasida*. **The genuinely distinctive feature**: Quran achieves "
    "sajʿ-density approaching qasida-density while functioning as religious-narrative-text "
    "— NOT \"more rhyme than poetry\" (false), but \"rhyme-density approaching poetry "
    "while being scripture\" (true). 0/10,000 perm null still holds at religious-"
    "narrative-prose scope; F63/F64 status unchanged. Audit memo: "
    "`docs/reference/sprints/F63_GENRE_SCOPE_AUDIT_V3.9.md`. "
    "**PREREG h"
)
if old_anchor in text:
    text = text.replace(old_anchor, new_text, 1)
    print("[OK] F63 row updated with V3.9 GENRE-SCOPE AUDIT note")
else:
    print("[WARN] F63 PREREG anchor not found")

p.write_text(text, encoding="utf-8")
print(f"[saved] {p}")
