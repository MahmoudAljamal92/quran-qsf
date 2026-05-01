# QSF ULTIMATE — Run Scorecard
Generated: 2026-04-27T23:08:47  FAST_MODE=True

| ID | Finding | Expected | Actual | Drift | Tol | Verdict |
|---|---|---|---|---|---|---|
| Abbasi_8_discriminators | Abbasi_8_discriminators | None | 7 | — | None | — OK |
| Abbasi_directional_beats | Abbasi_directional_beats | None | 6 | — | inf | — OK |
| Adiyat_blind | Adiyat winning variant (7-metric) | 0.71 | 0.5714 | 0.139 | 0.3 | PROVED OK |
| Adiyat_metric7_perm_p | Adiyat_metric7_perm_p | None | 0.06965 | — | inf | — OK |
| Blind_rejection_rates | Blind_rejection_rates | None | 0 | — | None | — OK |
| CamelTools_phi_m_rerun | CamelTools_phi_m_rerun | None | 6.663 | — | None | — OK |
| D01 | Anti-metric VL_CV d (Band A, audit v5) | 1.4 | 1.67 | 0.27 | inf | PENDING_REBLESS_v5 (was WEAKENED, pre-Band-A) OK |
| D02 | LEGACY Phi_M Cohen d (biased) | 6.34 | 6.663 | 0.323 | inf | DEPRECATED (biased; see Phi_M_hotelling_T2) OK |
| D03 | Quran EL | 0.707 | 0.7074 | 0.000434 | 0.03 | PROVED OK |
| D04 | Quran CN | 0.086 | 0.08597 | 3.17e-05 | 0.01 | PROVED OK |
| D05 | I(EL;CN) unit-level (bits) | 0.1 | 0.09957 | 0.000433 | 0.15 | FALSIFIED (unit) OK |
| D06 | Turbo gain G_turbo | 1.644 | 1.644 | 0.000434 | 0.05 | WEAKENED OK |
| D07 | Scale-free −log10 Fisher p @ W=10 — audit v5 | 16 | 16.08 | 0.0816 | inf | PENDING_REBLESS_v5 (was 1.1e-16 machine-eps artefact; now chi2.sf) OK |
| D08 | Markov z-score (Quran) — audit v5 | 44.9 | 44.88 | 0.0204 | inf | PENDING_REBLESS_v5 (was WEAKENED, pre-hadith-removal) OK |
| D09 | Classifier AUC Quran vs Arabic ctrl — audit v5 | 0.998 | 0.998 | 9.42e-06 | inf | PENDING_REBLESS_v5 (was PROVED STRONGER, pre-hadith-removal) OK |
| D10 | %T>0 Quran | 39.7 | 39.71 | 0.00588 | 3.0 | PROVED STRONGER OK |
| D11 | Perturbation gap sum — audit v5 | 5.02 | 5.023 | 0.00324 | inf | PENDING_REBLESS_v5 (was PROVED STRONGER, pre-hadith-removal) OK |
| D13 | D13 | None | 2.145 | — | None | — OK |
| D13_hindawi_in_pool_legacy | D13_hindawi_in_pool_legacy | None | 2.072 | — | inf | — OK |
| D13_hindawi_loo | D13_hindawi_loo | None | 2.145 | — | inf | — OK |
| D14 | Verse-internal gap — audit v5 | 5.8 | 5.638 | 0.162 | inf | PENDING_REBLESS_v5 (was PROVED STRONGER, pre-hadith-removal) OK |
| D16 | D16 | None | 0.3052 | — | None | — OK |
| D17 | Canonical path z-score (Band A, audit v5) | -3.96 | -2.444 | 1.52 | inf | PENDING_REBLESS_v5 (was PROVED, pre-Band-A) OK |
| D20 | Hierarchical Omega (Quran) — audit v5 | 7.89 | 8.29 | 0.4 | inf | PENDING_REBLESS_v5 (was WEAKENED, pre-hadith-removal) OK |
| D21 | Rhyme-swap P3 Quran vs Bible | -0.28 | -0.16 | 0.12 | 0.15 | NOT REPRODUCED OK |
| D22 | Root-diversity x EL — audit v5 | 0.632 | 0.6321 | 5.41e-05 | inf | PENDING_REBLESS_v5 (was PROVED STRONGER, pre-hadith-removal) OK |
| D23 | Canon-wins rate (Quran) | 1 | 1 | 0 | 0.05 | PROVED OK |
| D24 | Phi_M 10-fold CV median d — audit v5 | 6.89 | 7.298 | 0.408 | inf | PENDING_REBLESS_v5 (was PROVED STRONGER, pre-hadith-removal) OK |
| D25 | F_Meccan Band A — audit v5 | 0.8 | 0.7966 | 0.00338 | inf | PENDING_REBLESS_v5 (was FALSIFIED, pre-hadith-removal) OK |
| D26 | Bootstrap Omega > 2.0 fraction | 1 | 1 | 0 | 0.05 | PROVED STRONGER OK |
| D27 | LEGACY Abbasi discrimination (now directional) | 7 | 6 | 1 | inf | DEPRECATED (non-directional; see D27_directional) OK |
| D27_directional | D27_directional | None | 6 | — | inf | — OK |
| D28 | LEGACY tight-fairness Cohen d | 6.34 | 6.663 | 0.323 | inf | DEPRECATED (biased; see Phi_M_hotelling_T2) OK |
| E3_berry_esseen | E3_berry_esseen | None | 0.09766 | — | 1.0 | — OK |
| E_epi_variants | E_epi_variants | None | 0 | — | None | — OK |
| E_epi_waqf | E_epi_waqf | None | 0 | — | inf | — OK |
| E_harakat_capacity | H(harakat | rasm) bits | 1.96 | 1.964 | 0.00385 | 0.15 | PROVED OK |
| FDR_BH_coverage_frac | FDR_BH_coverage_frac | None | 0.2241 | — | inf | — OK |
| FDR_BH_n_claims_total | FDR_BH_n_claims_total | None | 58 | — | inf | — OK |
| FDR_BH_n_significant | FDR_BH_n_significant | None | 7 | — | None | — OK |
| FDR_BH_n_tested | FDR_BH_n_tested | None | 13 | — | inf | — OK |
| G1 | Hill alpha min across 5 features | 2.5 | 2.486 | 0.0143 | 1.0 | PROVED OK |
| G1_min_units | G1_min_units | None | 1 | — | None | — OK |
| G2 | Max normalised 5-ch MI | 0.3 | 0.3182 | 0.0182 | 0.05 | PROVED OK |
| G2_no_single_token | G2_no_single_token | None | 1 | — | None | — OK |
| G3_no_identical | G3_no_identical | None | 1 | — | None | — OK |
| G4_cv_valid | G4_cv_valid | None | 1 | — | None | — OK |
| G5_arabic_ratio | G5_arabic_ratio | None | 1 | — | None | — OK |
| HSIC_EL_CN_perm_p | HSIC(EL,CN) permutation p | 1 | 0.5323 | 0.468 | inf | REPORTING (binning-free MI alt) OK |
| HSIC_EL_CN_quran | HSIC(EL,CN) Quran (Band A) | 0 | 0.004649 | 0.00465 | inf | REPORTING (binning-free MI alt) OK |
| HSIC_G2_max_quran | HSIC 5-ch max pair (Quran) | 0 | 0.04752 | 0.0475 | inf | REPORTING (G2 kernel variant) OK |
| HSIC_G2_perm_p | HSIC 5-ch max perm p | 1 | 0.004975 | 0.995 | inf | REPORTING (G2 kernel variant) OK |
| H_cond_MM_quran | H_cond_MM_quran | None | 1.521 | — | inf | — OK |
| Heuristic_phi_m_rerun | Heuristic_phi_m_rerun | None | 6.508 | — | None | — OK |
| Hurst_DFA_quran | Hurst_DFA_quran | None | 0.901 | — | inf | — OK |
| Hurst_DFA_quran_R2 | DFA Hurst log-log R² (Quran) | 1 | 0.9901 | 0.00991 | inf | REPORTING (scaling-regime gate) OK |
| L1 | SCI (Quran) | 5.3 | 5.421 | 0.121 | 2.0 | EXPLORATORY OK |
| L2 | Retention scaling alpha | 1 | 1.15 | 0.15 | inf | EXPLORATORY OK |
| L3 | Free-energy F (Quran) | 0 | 1.1 | 1.1 | 5.0 | EXPLORATORY OK |
| L4 | Aljamal invariance CV | 1.7 | 1.551 | 0.149 | 1.0 | EXPLORATORY OK |
| L5 | OBI inequality slack (kappa=1) | -74 | -74.4 | 0.404 | 15.0 | EXPLORATORY OK |
| L6 | Empirical gamma slope b | 0 | -0.004282 | 0.00428 | 0.5 | EXPLORATORY OK |
| L7 | Psi(Quran) rank | 1 | 1 | 0 | 1.0 | EXPLORATORY OK |
| L7_sparse_pca_d | Sparse-PCA PC1 Cohen's d (Q vs ctrl) | 0 | 4.813 | 4.81 | inf | REPORTING (Ψ alternative) OK |
| L7_sparse_pca_perm_p | Sparse-PCA PC1 perm p | 1 | 0.004975 | 0.995 | inf | REPORTING (Ψ alternative) OK |
| MI_D05_miller_madow | MI_D05_miller_madow | None | 0.02531 | — | inf | — OK |
| MI_bin_sensitivity_range | MI_bin_sensitivity_range | None | 0.4744 | — | inf | — OK |
| MonteCarlo_const_null | MonteCarlo_const_null | None | 15.98 | — | inf | — OK |
| Nuzul_vs_Mushaf | Nuzul_vs_Mushaf | None | 1 | — | None | — OK |
| PROXY_1_compression_p1 | PROXY_1_compression_p1 | None | 0.4809 | — | inf | — OK |
| PROXY_2_compression_p3 | PROXY_2_compression_p3 | None | 0.005044 | — | inf | — OK |
| Partial_quote_leak | Partial_quote_leak | None | 0.007786 | — | None | — OK |
| Phi_M_hotelling_T2 | Phi_M Hotelling T² (Band A) | 0 | 3557 | 3.56e+03 | inf | HEADLINE (pending lock refresh) OK |
| Phi_M_perm_p_value | Phi_M permutation p-value | 0 | 0.004975 | 0.00498 | inf | HEADLINE (pending lock refresh) OK |
| PickleBug_simulation | PickleBug_simulation | None | 1 | — | None | — OK |
| PreReg_A_leave_one_out | PreReg_A_leave_one_out | None | 5.255 | — | None | — OK |
| PreReg_B_meccan_medinan | PreReg_B_meccan_medinan | None | 0.7966 | — | None | — OK |
| PreReg_C_bootstrap_omega | PreReg_C_bootstrap_omega | None | 1 | — | None | — OK |
| Psi_perm_p_value | Psi_perm_p_value | None | 0.1592 | — | inf | — OK |
| Psi_quran_rank | Psi_quran_rank | None | 1 | — | inf | — OK |
| S1 | LEGACY multivariate separation d | 6.34 | 6.663 | 0.323 | inf | DEPRECATED (biased; see Phi_M_hotelling_T2) OK |
| S2 | S2 | None | 0.09957 | — | None | — OK |
| S3 | S3 | None | 0.8671 | — | None | — OK |
| S4 | H3/H2 bigram sufficiency | 0.222 | 0.222 | 3.25e-06 | 0.02 | PROVED (partial) OK |
| S5 | Shannon-Aljamal path minimality z (Band A, audit v5) | -3.96 | -2.444 | 1.52 | inf | PENDING_REBLESS_v5 (was PROVED, pre-Band-A) OK |
| Supp_A_Hurst | Quran Hurst H | 0.7 | 0.7381 | 0.0381 | 0.15 | PROVED OK |
| Supp_A_Hurst_R2 | R/S Hurst log-log R² (Quran) | 1 | 0.9912 | 0.00884 | inf | REPORTING (scaling-regime gate) OK |
| Supp_B_multilevel_Hurst | Supp_B_multilevel_Hurst | None | 0.5366 | — | None | — OK |
| Supp_C_acoustic_bridge | Supp_C_acoustic_bridge | None | 0.8724 | — | inf | — OK |
| Supp_C_acoustic_bridge_perm_p | Supp-C rhyme×conn perm p | 1 | 0.8657 | 0.134 | inf | REPORTING (chi2 replacement) OK |
| T1 | T1 | None | 1.67 | — | None | — OK |
| T10 | T10 | None | 39.71 | — | None | — OK |
| T11 | T11 | None | 0.222 | — | None | — OK |
| T12 | T12 | None | 7.298 | — | None | — OK |
| T13 | T13 | None | 0.7966 | — | None | — OK |
| T14 | T14 | None | 1 | — | None | — OK |
| T15 | T15 | None | 0.998 | — | None | — OK |
| T16 | T16 | None | 8.288e-17 | — | None | — OK |
| T17 | T17 | None | 5.023 | — | None | — OK |
| T18 | T18 | None | 5.638 | — | None | — OK |
| T19 | T19 | None | 0.3052 | — | None | — OK |
| T2 | T2 | None | 6.663 | — | None | — OK |
| T20 | T20 | None | -0.16 | — | None | — OK |
| T21 | T21 | None | 0.6476 | — | None | — OK |
| T22 | T22 | None | 0.6321 | — | None | — OK |
| T23 | T23 | None | 1.964 | — | None | — OK |
| T24 | T24 | None | 0.09936 | — | None | — OK |
| T25 | T25 | None | 8 | — | None | — OK |
| T26 | T26 | None | 1.575 | — | None | — OK |
| T27 | T27 | None | 0.8556 | — | None | — OK |
| T28 | H2/H1 Markov-order d — audit v5 | -0.03 | 0.4247 | 0.455 | inf | PENDING_REBLESS_v5 (was NOT REPRODUCED, pre-hadith-removal) OK |
| T29 | phi_frac (golden-ratio claim) | -0.915 | -0.9155 | 0.000465 | 0.2 | NOT REPRODUCED OK |
| T3 | T3 | None | 0.8671 | — | None | — OK |
| T30 | T30 | None | 0.8483 | — | None | — OK |
| T31 | T31 | None | 1 | — | None | — OK |
| T4 | T4 | None | 8.29 | — | None | — OK |
| T5 | T5 | None | 100 | — | None | — OK |
| T6 | T6 | None | 0.9102 | — | None | — OK |
| T7 | I(EL;CN) corpus-level (bits) | 1.17 | 1.175 | 0.00487 | 0.1 | PROVED (corpus) OK |
| T8 | T8 | None | -2.444 | — | None | — OK |
| T9 | T9 | None | 44.88 | — | None | — OK |
| TDA_H1_bootstrap_p | TDA H1 marginal-shuffle perm p | 1 | 1 | 0 | inf | REPORTING (closes caveat c) OK |
| TDA_H1_max_persistence | Max H1 persistence (Quran 5D) | 0 | 0 | 0 | inf | APPENDIX (USE_TDA) OK |
| TDA_n_loops_long_lived | # H1 features > 0.25 σ | 0 | 0 | 0 | inf | APPENDIX (USE_TDA) OK |
| Tight_fairness_band_A | Tight_fairness_band_A | None | 6.663 | — | None | — OK |
| Tight_fairness_band_B | Tight_fairness_band_B | None | 3.55 | — | None | — OK |
| Tight_fairness_band_C | Tight_fairness_band_C | None | 10.11 | — | None | — OK |

## Summary
- total locked scalars: 127
- drift violations:     0