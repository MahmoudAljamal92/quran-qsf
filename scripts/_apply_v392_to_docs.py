"""scripts/_apply_v392_to_docs.py
=====================================
Bump RANKED_FINDINGS.md and PROGRESS.md to V3.9.2 — full four-test
stress battery (T1 hadith, T2 drop-CN, T3 drop-EL+CN, T4 Quran-blind).
"""
from __future__ import annotations
from pathlib import Path

# ----- RANKED -----
p = Path("docs/reference/findings/RANKED_FINDINGS.md")
text = p.read_text(encoding="utf-8")

old_v = "**Version**: 3.9.1 (2026-04-29 morning, **v7.9-cand patch H V3.9.1 - "
new_v = (
    "**Version**: 3.9.2 (2026-04-29 morning, **v7.9-cand patch H V3.9.2 - "
    "FOUR-TEST STRESS BATTERY: (T1) hadith Bukhari INCLUDED 5-D AUC = "
    "0.9954 (no change vs V3.9.1 baseline 0.9953; user prediction "
    "confirmed); (T1b) Quran-vs-hadith ONLY AUC = 0.9992; (T2) drop CN "
    "feature 4-D AUC = 0.9929 (CN was NOT the discriminative driver); "
    "(T3) drop EL+CN combined 3-D AUC = 0.9639, Cohen's d = 3.39 "
    "(harshest fair test survived); (T4) Quran-BLIND classifier weights "
    "(trained on Iliad-vs-Arabic-Bible, NO Quran in training) AUC = "
    "0.8202, Quran in 93rd percentile of score distribution. "
    "F1/F2/F3/F47/F50/F58 all STRENGTHENED. The 'Quran wins because we "
    "hand-picked Quran-genre features' argument is EMPIRICALLY REFUTED. "
    "Hadith does not rival Quran (every feature except VL_CV favors "
    "Quran with d > 2). Audit memo: "
    "`docs/reference/sprints/V3.9.2_FULL_STRESS_AUDIT.md`**). Earlier: "
    "3.9.1 (V3.9.1 - "
)
if old_v in text:
    text = text.replace(old_v, new_v)
    print("[OK] RANKED banner 3.9.1 -> 3.9.2")
else:
    print("[WARN] RANKED banner anchor not found")

p.write_text(text, encoding="utf-8")

# Mirror
mirror = Path("docs/RANKED_FINDINGS.md")
mirror.write_bytes(p.read_bytes())
print("[OK] mirror synced")

# ----- PROGRESS -----
pp = Path("docs/PROGRESS.md")
ptext = pp.read_text(encoding="utf-8")

old_p = ("**Last updated**: 2026-04-29 morning (**v7.9-cand patch H V3.9.1 — "
         "MULTIVARIATE STRESS TEST follow-up to V3.9 GENRE-SCOPE AUDIT**.")
new_p = (
    "**Last updated**: 2026-04-29 morning (**v7.9-cand patch H V3.9.2 — "
    "FULL FOUR-TEST STRESS BATTERY against V3.8/V3.9/V3.9.1 weak points**. "
    "User asked 'what could tear our case apart?' and listed four "
    "specific concerns: (1) hadith Bukhari was excluded from V3.9.1 "
    "peer pool — most-similar-genre Arabic peer; (2) CN feature is "
    "Quran-genre-defining (counts 14 specific Arabic narrative-"
    "connectives at verse-start); (3) what if BOTH EL and CN are "
    "dropped; (4) feature-selection bias — 5 features chosen knowing "
    "Quran's properties. **All four tests run in one pass** "
    "(`scripts/_audit_v392_full_stress.py`). **Results**: T1 hadith "
    "INCLUDED 5-D AUC = 0.9954 (no change vs V3.9.1 baseline 0.9953); "
    "T1b Quran-vs-hadith ONLY AUC = 0.9992; T2 drop-CN 4-D AUC = "
    "0.9929 (CN was redundant — NOT the driver); T3 drop EL+CN 3-D "
    "AUC = **0.9639**, Cohen's d = **3.39** (harshest fair test "
    "survived); T4 Quran-BLIND weights (trained on Iliad-vs-Arabic-"
    "Bible, NO Quran) AUC = **0.8202**, Quran in **93rd percentile** "
    "of score distribution. **F1/F2/F3/F47/F50/F58 all STRENGTHENED**. "
    "User's prediction 'hadith won't rival Quran' EMPIRICALLY "
    "CONFIRMED (per-feature: EL d=+3.43, CN d=+2.09, H_cond d=+2.61, "
    "T d=+3.14; only VL_CV slightly favors hadith d=-0.83). The "
    "'Quran wins because we hand-picked Quran-genre features' "
    "argument is EMPIRICALLY REFUTED (drop-CN AUC = 0.9929). "
    "**Honest residual**: T4 AUC 0.82 < calibrated 0.99 — "
    "calibration-tuning contributes; but Quran-blind 93rd-percentile "
    "is the conservative defensible baseline. PAPER §4.47.12.4 added "
    "with full V3.9.2 four-test summary table. Audit memo "
    "`docs/reference/sprints/V3.9.2_FULL_STRESS_AUDIT.md` filed. "
    "**No locked PASS finding's status changes**. Counts unchanged "
    "(64 currently positive findings; 60 retractions; 12 failed-null "
    "pre-regs).\n\n"
    "**Earlier date**: 2026-04-29 morning (**v7.9-cand patch H V3.9.1 — "
    "MULTIVARIATE STRESS TEST follow-up to V3.9 GENRE-SCOPE AUDIT**.")
if old_p in ptext:
    ptext = ptext.replace(old_p, new_p)
    print("[OK] PROGRESS banner 3.9.1 -> 3.9.2")
else:
    print("[WARN] PROGRESS banner anchor not found")

pp.write_text(ptext, encoding="utf-8")
print()
print("[done] V3.9.2 doc updates complete")
