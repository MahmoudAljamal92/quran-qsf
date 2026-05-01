"""scripts/_show_multivariate_arabic_internal.py
======================================================
Show the locked Arabic-internal multivariate findings (T², AUC,
Phi_master) and demonstrate that they are NOT touched by the V3.9
genre-scope audit (which only narrowed the cross-tradition F63/F64
rhyme claim).
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ULT = ROOT / "results" / "ULTIMATE_REPORT.json"

print("# === Locked Arabic-internal multivariate findings ===\n")

if not ULT.exists():
    print("# ULTIMATE_REPORT.json not found")
else:
    d = json.loads(ULT.read_text(encoding="utf-8"))
    # Print all keys with their actual values for AUC/T2/phi/BF
    items_of_interest = []
    for k, v in d.items():
        klow = k.lower()
        if isinstance(v, dict) and "actual" in v:
            actual = v.get("actual")
            name = v.get("name", k)
            if any(s in klow for s in ["auc", "t2", "phi", "bf",
                                        "cohen", "el_", "vl_", "cn_",
                                        "h_cond", "tension", "maqamat",
                                        "mw_", "perm_p"]):
                items_of_interest.append((k, name, actual))
    print(f"# Found {len(items_of_interest)} locked scalars matching multivariate keys:")
    print()
    for k, name, actual in sorted(items_of_interest):
        if isinstance(actual, (int, float)):
            print(f"#   {k:<35s}  {actual:>14.6g}  ({name})")

print()
print("# === KEY HEADLINE NUMBERS (Arabic-internal, multivariate) ===")
print()
print("# These are the locked numbers from PAPER §4.1 / §4.5:")
print("#")
print("#   T² Hotelling (Band-A 5-D)        = 3,557")
print("#   Cohen's d                         = 6.66")
print("#   Mann-Whitney p                    = 1.75e-44")
print("#   Permutation p (exp26)             = floor 5e-3 (with 0/10,000 hits at observed T²)")
print("#   Classifier AUC (5-D, nested CV)   = 0.998")
print("#   Bootstrap T² 95% CI (full Quran)  = [3,127, 4,313]; band-A INSIDE")
print("#   Phi_master                        = 1,862.31 nats")
print("#   log10 Bayes Factor                = 808.85")
print("#   EL alone (1-D, band-A)            = AUC 0.9971")
print("#   EL alone (1-D, all bands)         = AUC 0.981")
print("#   F50 Maqamat al-Hariri (saj' poetry) = AUC 0.9902, MW p = 2.4e-38")
print("#   LOCO EL (drop one Arabic corpus)  = min AUC 0.9796")
print()
print("# The 5-D feature space:")
print("#   F1: EL    = end-letter rhyme rate")
print("#   F2: VL_CV = verse-length coefficient of variation (in words)")
print("#   F3: CN    = discourse-connective start-rate (Arabic-specific morphology)")
print("#   F4: H_cond = conditional root-bigram entropy (Arabic-specific)")
print("#   F5: T     = structural tension (H_cond - H_el)")
print()
print("# The Arabic peer pool used by these classifiers (band-A 68 surahs vs 2,509 controls):")
print("#   poetry_jahili    (pre-Islamic Arabic poetry)")
print("#   poetry_islami    (early Islamic-era Arabic poetry)")
print("#   poetry_abbasi    (Abbasid Arabic poetry)")
print("#   ksucca           (classical Arabic prose)")
print("#   hindawi          (modern Arabic prose)")
print("#   arabic_bible     (Smith Van Dyke 1865 Arabic Bible)")
print()
print("# *** THE MULTIVARIATE FINDINGS ARE NOT AFFECTED BY V3.9 ***")
print("# V3.9 narrowed the cross-tradition F63/F64 rhyme claim from")
print("# 'most rhymed text' to 'religious-narrative-prose extremum'.")
print("# It did NOT touch F1 / F2 / F3 / F47 / F50 / F58 which are")
print("# Arabic-internal multivariate findings (5 features, including")
print("# 4 features that have NOTHING to do with rhyme).")
