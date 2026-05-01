"""Quick check that all audit v3 patches landed in the regenerated notebook."""
from __future__ import annotations
import json
from pathlib import Path

NB = Path(__file__).with_name("QSF_ULTIMATE.ipynb")
nb = json.loads(NB.read_text(encoding="utf-8"))

markers = {
    # Round-1 audit v3 (issues 2, 3, 4, 5, 7, 10, 17)
    "#2 MI sign fix":         "K_obs_x + K_obs_y - K_obs_joint - 1",
    "#4 per-verse feat":      "_per_verse_feat",
    "#7 FDR dedupe":          "Mahal_family_perm_p",
    "#3 G3 x-range gate":     "INSUFFICIENT_RANGE",
    "#5 eps caveat (97)":     "PER-TOKEN substitution rate",
    "#10 DFA R2 id":          "Hurst_DFA_quran_R2",
    "#17 MC perm stats":      "_acou_stats",
    "NAMES add R-S R²":       "Supp_A_Hurst_R2",
    "lock add Supp-C":        "Supp_C_acoustic_bridge_perm_p",
    "BH dedupe comment":      "inserted ONCE into BH",
    "L2 token-rate caveat":   "indexed in per-token eps units",

    # Round-2 audit v3 (issues 21a, 22, 23)
    "#22 TDA bootstrap null": "marginal-shuffle null",
    "#22 TDA boot p id":      "TDA_H1_bootstrap_p",
    "#21a sparse-PCA L7":     "SparsePCA(n_components=1",
    "#21a L7 d id":           "L7_sparse_pca_d",
    "#21a L7 perm p id":      "L7_sparse_pca_perm_p",
    "Cell 132 caveat c CLOSED": "CLOSED (audit 2026-04-18 v3)",

    # Round-3 audit v4 (9 bugs fixed 2026-04-18)
    "#v4.1 T21 Iliad bless":     "bless('T21', float(iliad_z))",
    "#v4.1 Z_SCORE_IDS T21":     "'T21': 'T21_iliad_z'",
    "#v4.2 rbf hoisted to C8":   "shared RBF kernel helper",
    "#v4.3 Fig 2 letter_10pct":  "qt.get('letter_10pct'",
    "#v4.3 Fig 2 word_10pct":    "qt.get('word_10pct'",
    "#v4.4 bless inf except":    "(tol == float('inf')) or UPDATE_LOCK",
    "#v4.5 NB_DIR unconditional":"NB_DIR   = Path.cwd()\nif (NB_DIR.parent.parent",
    "#v4.6 Psi perm local centroid": "pseudo-non-quran rows",
    "#v4.6 Psi perm mu_loc_p":   "mahalanobis(Xp, mu_loc_p, Sinv_loc_p)",
    "#v4.7 T10 uses pct_T_pos":  "bless('T10', pct_T_pos)",
    "#v4.8 Py 3.10 assert":      "Python 3.10+ required",
    "#v4.9 tol_override no-lock":"entry is None and tol_override is not None",

    # Round-3 audit v4 · Round 2 (bugs 10-13)
    "#v4.10 T6 blessed":         "bless('T6', float(d6))",
    "#v4.11 T13 blessed":        "bless('T13', float(min(F_M, F_D)))",
    "#v4.12 ckpt 08 ALL_RESULTS":"save_checkpoint('08_scalefree_path'",
    "#v4.12 ckpt 22 ALL_RESULTS":"'tda_results':    {k: {kk: (float(vv) if isinstance(vv, (int, float, np.floating)) else vv)\n                            for kk, vv in v.items()} for k, v in TDA_RESULTS.items()},\n}, state={'ALL_RESULTS': ALL_RESULTS})",
    "#v4.13 T15 = AUC (nested-CV)":"bless('T15', auc_nested)",

    # Zero-trust audit v4.3 (state leaks + Phase-21 ckpt)
    "#v4.14 Phase-21 ckpt":       "save_checkpoint('21_final_scorecard'",
    "#v4.15 ARABIC_FAMILY hoisted":"AUDIT 2026-04-18 (v4): ARABIC_FAMILY hoisted here",
    "#v4.16 Phase-7 pre-resume":  "pull CORPORA, FEATS, mu, S_inv, bands",
    "#v4.17 Phase-14 heavy state": "carry heavy globals that Phase 15-22 may need",
    "#v4.18 Phase-18 heavy state": "Phase 21 Fig 3/4 reads ns_L6, omega_proxy, gammas",

    # ------------------------------------------------------------
    # ROUND-4 AUDIT v5 (2026-04-19) — adversarial zero-trust audit
    #   V2  hadith-leak in src/* control pools           (fatal flaw)
    #   V3  Band-A filter missing in T1 and T8           (fatal flaw)
    #   V4  Fisher-p machine-eps artefact (1-cdf → sf)   (fatal flaw)
    #   V5  MD-drift alarm only printed, never halted    (warning)
    #   V7  D07 locked to machine-eps, tol rubber-stamp  (warning)
    # ------------------------------------------------------------
    "#v5.V2 hadith sentinel":       "hadith-leak sentinel",
    "#v5.V2 sentinel raises":       "hadith_bukhari leaked back into",
    "#v5.V4 Fisher logsf fallback": "_chi2.logsf(entry['chi2'], entry['df'])",
    "#v5.V4 D07 -log10 bless":      "bless('D07', float(neg_log10_p))",
    "#v5.V4 Hotelling ridge 1e-6":  "ridge unified to 1e-6 to match every other",
    "#v5.V5 MD-drift pos halt":     "[HALL drift5]",
    "#v5.V5 MD-drift positive set": "_POSITIVE_VERDICTS = {",
    "#v5.V7 D07 log-domain lock":   "'Scale-free \u2212log10 Fisher p @ W=10 \u2014 audit v5'",
    "#v5.V7 PENDING_REBLESS tag":   "PENDING_REBLESS_v5",

    # ------------------------------------------------------------
    # ROUND-5 AUDIT v6 (2026-04-19) — post-v5 submission-rigor fixes
    #   F1  T15/D09 blessed on nested-CV, Cell 62 demoted to diagnostic
    #   F2  inner-fold scaler leakage eliminated (StratifiedKFold + per-fold scaler)
    #   F3  Cell 61 + Cell 99 fail-closed on missing external vocab
    #   F4  Cell 60 self-audit theater replaced with real checks
    #   F5  drift5 surfaces missing headline IDs
    # ------------------------------------------------------------
    "#v6.F1 T15 bless nested":      "bless('T15', auc_nested)",
    "#v6.F1 Cell 62 demoted":       "T15 upstream 5-fold AUC (DIAGNOSTIC, not blessed)",
    "#v6.F2 StratifiedKFold outer": "outer = StratifiedKFold(n_splits=5",
    "#v6.F2 inner-fold scaler":     "sc_in = StandardScaler().fit(Xtr[itr])",
    "#v6.F3 synth fail-closed":     "tautologize the adversarial synthesis test",
    "#v6.F3 blind fail-closed":     "invalidate the blind-rejection null",
    "#v6.F4 real centroid check":   "'C Quran excluded from Arabic centroid'",
    "#v6.F4 real bandA check":      "'D Band-A gating configured'",
    "#v6.F5 drift5 headline gap":   "_required_headline_ids = {'Phi_M_hotelling_T2'",
    "#v6.D perm S_loc per-perm":    "S_loc  = np.cov(Xp_B.T, ddof=1) + ridge",
    "#v6.D docstring note":         "v6 fix D",
    "#v6.E T22->T24 lesion fix":    "T24',      # Lesion \u2014 verse-deletion null",
    "#v6.K fig resume guard":       "_ = resume_from('18_discovery')",
    "#v6.K fig3 presence check":    "_fig3_ok = (all(k in globals()",
    "#v6.K fig4 presence check":    "'PSI' in globals() and PSI:",
    "#v6.K fig6 presence check":    "'Hurst_vals' in globals() and 'H_multi' in globals():",
    "#v6.L PREREG amendments":      "'amendments': [",
    "#v6.L amendment audit_id":     "'audit_id': 'v5 fix \u2467'",

    # ------------------------------------------------------------
    # ROUND-6 AUDIT v6 W-fixes (2026-04-19) — PNAS hostile-audit follow-up
    #   W1-a  Universal 1e-4 absolute-drift lens in Phase 21
    #   W1-b  Headline Phi_M baseline envelope (headline_baselines.json)
    #   W2    Cross-language Band-A fallback removed -> INFEASIBLE skip
    #   W4-a  D05 degenerate std returns NaN (not 0.0) with warn
    #   W5-a  Checkpoint-pickle SHA manifest + mid-run verification
    #   W5-b  Removed '<UPDATED>' escape hatch in results-lock SHA check
    # ------------------------------------------------------------
    "#v6.W1-a UNIVERSAL_DRIFT constant":   "UNIVERSAL_DRIFT_ABSOLUTE = 1e-4",
    "#v6.W1-a drift-1e-4 print tag":       "[drift-1e-4]",
    "#v6.W1-b HEADLINE_REL_TOL constant":  "HEADLINE_REL_TOL = 0.05",
    "#v6.W1-b headline_baselines write":   "headline_baselines.json WRITTEN",
    "#v6.W1-b headline_baselines raise":   "[HALL headline-baseline]",
    "#v6.W2  cross-language INFEASIBLE":   "CL_INFEASIBLE = []",
    "#v6.W2  INFEASIBLE skip print":       "INFEASIBLE \u2014 0/",
    "#v6.W4-a D05 NaN on degenerate":      "returning NaN (not 0.0)",
    "#v6.W5-a manifest constant":          "_CKPT_MANIFEST = CKPT_DIR / '_manifest.json'",
    "#v6.W5-a SHA drift IntegrityError":   "[HALL ckpt]",
    "#v6.W5-a SHA verify pre-pickle":      "verify on-disk bytes SHA before handing to pickle.loads",
    "#v6.W5-b results-lock strict":        "if rl_payload.get('hash') != recomputed:",

    # Regression sentinels — these MUST NOT exist
    "#2 MI old sign (should NOT exist)": "K_obs_joint - K_obs_x - K_obs_y + 1",
    "#v4.1 T15 iliad (should NOT exist)": "bless('T15', float(iliad_z))",
    "#v4.2 rbf in USE_HSIC (should NOT exist)": "if USE_HSIC:\n    def _rbf_kernel(M):",
    "#v4.3 letter_shuffle fig (should NOT exist)": "qt.get('letter_shuffle'",
    "#v4.5 NB_DIR ternary (should NOT exist)": "NB_DIR   = Path.cwd() if (Path.cwd() / 'QSF_ULTIMATE.ipynb').exists() else Path.cwd()",
    "#v4.6 Psi perm global mu (should NOT exist)": "mahalanobis(Xp, mu, S_inv)",
    "#v4.7 T10 as h_q (should NOT exist)": "bless('T10', float(h_q))",
    # v5 anti-regressions (notebook)
    "#v5.V4 D07 raw p bless (should NOT exist)": "bless('D07', float(p_w10))",
    "#v5.V5 info-only drift (should NOT exist)": "MD-drift is INFORMATIONAL ONLY",
    # v6 anti-regressions (notebook)
    "#v6.W2  CL fallback (should NOT exist)":     "if not recs: recs = FEATS[cl]  # fallback",
    "#v6.W5-b <UPDATED> hash (should NOT exist)": "rl_payload.get('hash') not in (recomputed, '<UPDATED>')",
    "#v6.W4-a D05 silent zero (should NOT exist)":"if el.std() == 0 or cn.std() == 0: return 0.0",
}

# ---------------------------------------------------------------------------
# v5 extras: the hadith-quarantine, T1/T8 Band-A filter, and Fisher-sf fixes
# live in the `src/` layer (outside the notebook). Scan them here so the audit
# check catches a regression at either layer. Audit-fix L1 2026-04-26: also
# scan `experiments/**/*.py` to catch the same regression at the experiments
# layer (expP12, expP13 had silently re-introduced hadith into ARABIC_CTRL).
# ---------------------------------------------------------------------------
SRC = NB.parent.parent.parent / "src"
EXPERIMENTS = NB.parent.parent.parent / "experiments"

# Experiments that are LEGITIMATELY allowed to mention "hadith_bukhari" in a
# list literal because hadith is either the experimental TARGET or an
# intentional diagnostic addition (audit / supplement scripts that include
# hadith on purpose to measure its effect, then quarantine it from the
# headline pool). Adding a directory name here is a deliberate exemption;
# do not add a directory just to silence a warning - the audit's job is to
# force you to look at every new occurrence.
HADITH_ALLOWLIST_DIRS = {
    "expP10_hadith_N1_prereg",     # hadith IS the experimental target
    "expP9_v79_batch_diagnostics", # audit/supplement, intentionally includes
                                   # hadith for diagnostic comparison
    "exp07_tension_law",           # explicit "still compute, flag" robustness
    "exp08_tension_noncircular",   # comment-only mention; not in ARABIC_CORPORA
    "expP14_cross_script_dominant_letter",
                                   # set-membership check picks MAX p_max
                                   # across Arabic comparators as the
                                   # denominator (line ~129); including
                                   # hadith RAISES the denominator and
                                   # makes the Quran-dominance ratio
                                   # HARDER to confirm. Conservative, not
                                   # a leak.
}
src_markers = {
    # must-exist (post-fix)
    "#v5.V2 cp hadith removed":       (SRC / "clean_pipeline.py",  "hadith_bukhari` QUARANTINED"),
    "#v5.V2 et1 hadith removed":      (SRC / "extended_tests.py",  "`hadith_bukhari` removed"),
    "#v5.V2 et2 hadith removed":      (SRC / "extended_tests2.py", "`hadith_bukhari` removed"),
    "#v5.V2 et3 hadith removed":      (SRC / "extended_tests3.py", "`hadith_bukhari` removed"),
    "#v5.V3 T1 Band-A in pipeline":   (SRC / "clean_pipeline.py",  "Band-A filter was missing here"),
    "#v5.V3 T8 Band-A in et1":        (SRC / "extended_tests.py",  "Band-A filter was missing. The z-score WITHIN"),
    "#v5.V4 Fisher sf in et2":        (SRC / "extended_tests2.py", "stats.chi2.sf(chi2, df)"),
    "#v5.V4 Fisher logsf in et2":     (SRC / "extended_tests2.py", "stats.chi2.logsf(chi2, df)"),
    # v6 W4-b: T11 NaN sort fix in extended_tests.py
    "#v6.W4-b NaN-bucket in T11":     (SRC / "extended_tests.py",  "ranking_nan_bucket"),
    "#v6.W4-b NaN-filter comment":    (SRC / "extended_tests.py",
                                       "Python's `sorted` on NaN-valued keys"),
    # must-NOT-exist (regressions)
    "#v5.V2 cp hadith (should NOT exist)":  (SRC / "clean_pipeline.py",  '"hadith_bukhari",'),
    "#v5.V2 et1 hadith (should NOT exist)": (SRC / "extended_tests.py",  '"hadith_bukhari",'),
    "#v5.V2 et2 hadith (should NOT exist)": (SRC / "extended_tests2.py", '"hadith_bukhari",'),
    "#v5.V2 et3 hadith (should NOT exist)": (SRC / "extended_tests3.py", '"hadith_bukhari",'),
    "#v5.V4 Fisher 1-cdf (should NOT exist)": (SRC / "extended_tests2.py",
                                               "1 - stats.chi2.cdf(chi2, df)"),
    # v6 anti-regression: old raw-sort over possibly-NaN key in T11
    "#v6.W4-b raw NaN sort (should NOT exist)": (
        SRC / "extended_tests.py",
        'sorted(per.items(), key=lambda kv: kv[1]["ratio_H3_over_H2"])'),
}

all_src = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")

bad = 0
print("--- notebook markers ---")
for tag, needle in markers.items():
    hit = needle in all_src
    should_miss = "should NOT exist" in tag
    ok = (not hit) if should_miss else hit
    flag = "[OK]  " if ok else "[FAIL]"
    if not ok:
        bad += 1
    print(f"{flag} {tag:<40s}  pattern: {needle!r}")

print("--- src/* markers (v5) ---")
for tag, (path, needle) in src_markers.items():
    if not path.exists():
        print(f"[SKIP] {tag:<40s}  path missing: {path}")
        bad += 1
        continue
    body = path.read_text(encoding="utf-8")
    hit = needle in body
    should_miss = "should NOT exist" in tag
    ok = (not hit) if should_miss else hit
    flag = "[OK]  " if ok else "[FAIL]"
    if not ok:
        bad += 1
    print(f"{flag} {tag:<40s}  pattern: {needle!r}  ({path.name})")

# ---------------------------------------------------------------------------
# Experiments-layer hadith-quarantine scan (L1, 2026-04-26).
# Walks every experiments/**/*.py and flags any non-comment line that
# contains the exact regression signature `"hadith_bukhari",` (i.e. hadith
# included as an element of a list/tuple literal). Files in directories
# listed in HADITH_ALLOWLIST_DIRS are exempt.
#
# A "non-comment line" here is determined by: the substring `"hadith_bukhari",`
# appears BEFORE the first `#` on the line. This is a heuristic, not a full
# parser, but matches the regression pattern (`..., "hadith_bukhari", ...,`).
# ---------------------------------------------------------------------------
print("--- experiments/* hadith-quarantine scan (L1) ---")
NEEDLE_HADITH = '"hadith_bukhari",'
hadith_offenders = []
if EXPERIMENTS.exists():
    for p in sorted(EXPERIMENTS.rglob("*.py")):
        # Identify the experiment top-level directory (the one immediately
        # under EXPERIMENTS), e.g. exp95e_full_114_consensus_universal.
        try:
            rel = p.relative_to(EXPERIMENTS)
        except ValueError:
            continue
        top = rel.parts[0] if rel.parts else ""
        if top in HADITH_ALLOWLIST_DIRS:
            continue
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(body.splitlines(), start=1):
            idx = line.find(NEEDLE_HADITH)
            if idx < 0:
                continue
            comment = line.find("#")
            if comment >= 0 and comment < idx:
                # `#` precedes the needle on this line -> it's a comment
                continue
            hadith_offenders.append((str(rel).replace("\\", "/"), lineno, line.strip()))

if hadith_offenders:
    bad += len(hadith_offenders)
    print(f"[FAIL] {len(hadith_offenders)} experiment(s) re-introduce hadith into a list:")
    for rel, lineno, line in hadith_offenders:
        print(f"        experiments/{rel}:{lineno}: {line[:120]}")
else:
    print(f"[OK]   no experiments include 'hadith_bukhari' in a list literal "
          f"(allowlist: {sorted(HADITH_ALLOWLIST_DIRS)})")

raise SystemExit(0 if bad == 0 else 2)
