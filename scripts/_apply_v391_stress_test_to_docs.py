"""scripts/_apply_v391_stress_test_to_docs.py
==================================================
Bump RANKED_FINDINGS.md and PROGRESS.md to V3.9.1 — Arabic-internal
multivariate stress test confirms F1/F2/F3/F47/F50/F58 are V3.9-robust.
"""
from __future__ import annotations
from pathlib import Path

# ---------------------------------------------------------------- RANKED
p = Path("docs/reference/findings/RANKED_FINDINGS.md")
text = p.read_text(encoding="utf-8")

old_v = "**Version**: 3.9 (2026-04-29 morning, **v7.9-cand patch H V3.9 - "
new_v = (
    "**Version**: 3.9.1 (2026-04-29 morning, **v7.9-cand patch H V3.9.1 - "
    "MULTIVARIATE STRESS TEST: even after V3.9 EL-confound worst case, "
    "Arabic-internal 4-D classifier (drop EL entirely) gives AUC = 0.9697, "
    "Cohen's d = 3.54 on Quran vs 4,719 Arabic peer units; Quran beats "
    "peers on every one of 5 features individually (d_min = 0.62, "
    "d_VL_CV = 1.46, d_T = 2.12); F1/F2/F3/F47/F50/F58 are V3.9-ROBUST; "
    "the project's 'Quran tops all Arabic texts' claim was always "
    "multivariate, not rhyme-driven, and remains valid**). Earlier: "
    "3.9 (V3.9 - "
)
if old_v in text:
    text = text.replace(old_v, new_v)
    print("[OK] RANKED version banner updated 3.9 -> 3.9.1")
else:
    print("[WARN] RANKED version banner not found")

p.write_text(text, encoding="utf-8")

# Mirror sync
mirror = Path("docs/RANKED_FINDINGS.md")
mirror.write_bytes(p.read_bytes())
print("[OK] mirror synced")

# ---------------------------------------------------------------- PROGRESS
pp = Path("docs/PROGRESS.md")
ptext = pp.read_text(encoding="utf-8")
old_p = ("**Last updated**: 2026-04-29 morning (**v7.9-cand patch H V3.9 — "
         "F63/F64 GENRE-SCOPE AUDIT, post-reviewer critique**.")
new_p = (
    "**Last updated**: 2026-04-29 morning (**v7.9-cand patch H V3.9.1 — "
    "MULTIVARIATE STRESS TEST follow-up to V3.9 GENRE-SCOPE AUDIT**. "
    "Reviewer follow-up: 'if F63's rhyme claim is genre-scope-bounded, "
    "doesn't that also weaken F1/F2/F3/F47/F50/F58 (Arabic-internal "
    "multivariate distinctiveness claims) which use EL as one of their "
    "five features?' **Answer: NO, those findings are V3.9-robust.** "
    "Stress test (`scripts/_audit_v39_multivariate_robustness.py`) "
    "rebuilds the canonical Band-A 5-D classifier (68 Quran surahs vs "
    "4,719 Arabic peer units across poetry × 3 epochs + ksucca + "
    "hindawi + arabic_bible) and probes EL dependency: "
    "**baseline 5-D AUC = 0.9953**, Cohen's d = 5.85; **worst-case 1** "
    "(poetry EL artificially set to Quran median 0.7272) AUC = 0.9888; "
    "**worst-case 2** (drop EL entirely, 4-D classifier on VL_CV + CN + "
    "H_cond + T) AUC = **0.9697**, Cohen's d = **3.54** ('huge' effect "
    "by Cohen's convention). **The Quran beats Arabic peers on every "
    "one of the 5 features individually**, with d_VL_CV = +1.46 (Quran "
    "verses 2.5× more variable than poetry's rigid meter), d_T = +2.12 "
    "(structural tension Quran -0.48 vs peers -2.26), d_CN = +1.08 "
    "(narrative connectives at verse-start), d_H_cond = +0.62, "
    "d_EL = +3.79 (V3.9-affected). **F50 Maqamat al-Hariri** "
    "(closest-genre Arabic saj' literature) AUC = 0.9902 stands within-genre. "
    "PAPER §4.47.12.3 added with full stress-test summary. "
    "V3.9 audit memo §8 appended with Arabic-internal robustness "
    "confirmation. **The project's 'Quran tops all Arabic texts' claim "
    "was always multivariate, and remains valid after V3.9.** Counts "
    "unchanged (64 currently positive findings; 60 retractions; "
    "12 failed-null pre-regs). \n\n"
    "**Earlier date**: 2026-04-29 morning (**v7.9-cand patch H V3.9 — "
    "F63/F64 GENRE-SCOPE AUDIT, post-reviewer critique**.")
if old_p in ptext:
    ptext = ptext.replace(old_p, new_p)
    print("[OK] PROGRESS version banner updated 3.9 -> 3.9.1")
else:
    print("[WARN] PROGRESS version banner not found")

pp.write_text(ptext, encoding="utf-8")

print()
print("[done] V3.9.1 doc updates complete")
