# Zero-Trust Audit — 20260501T182512Z

- Receipts scanned: **214**
- CRITICAL: **0**
- WARN: 72
- INFO: 62

## WARN (72)

### L6_no_calibration_source_declared — 72
- `results/experiments/exp02_mi_criticality/exp02_mi_criticality.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp07_tension_law/exp07_tension_law.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp08_tension_noncircular/exp08_tension_noncircular.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp09_R1_variant_forensics_9ch/exp09_R1_variant_forensics_9ch.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp102_imitation_battery/exp102_imitation_battery.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp104_F53_tanakh_pilot/exp104_F53_tanakh_pilot.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp104b_F53_psalm119/exp104b_F53_psalm119.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp104c_F53_psalm78/exp104c_F53_psalm78.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp105_F55_psalm78_bigram/exp105_F55_psalm78_bigram.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp105_harakat_restoration/exp105_harakat_restoration.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp110_phi_master_xtrad/exp110_phi_master_xtrad.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp112_F55_daodejing_bigram/exp112_F55_daodejing_bigram.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp113_joint_extremality_3way/exp113_joint_extremality_3way.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp114_alphabet_independent_pmax/exp114_alphabet_independent_pmax.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp118_multi_letter_F55_theorem/exp118_multi_letter_F55_theorem.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp119_universal_F55_scope/exp119_universal_F55_scope.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp124_one_bit_threshold_universal/exp124_one_bit_threshold_universal.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp124b_alphabet_corrected_one_bit_universal/exp124b_alphabet_corrected_one_bit_universal.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp124c_alphabet_corrected_universal_with_rigveda/exp124c_alphabet_corrected_universal_with_rigveda.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp135_F79_bootstrap_stability/exp135_F79_bootstrap_stability.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp137_The_Quran_Constant/exp137_The_Quran_Constant.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp137b_The_Quran_Constant_per_unit/exp137b_The_Quran_Constant_per_unit.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp155_F75_stretched_exp_predictive_validity/exp155_F75_stretched_exp_predictive_validity.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp159_paradigm_battery/exp159_paradigm_battery.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp162_sigma_bigram_universal/exp162_sigma_bigram_universal.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp177_quran_multifractal_fingerprint/exp177_quran_multifractal_fingerprint.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp21_E1_EL_survival/exp21_E1_EL_survival.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp29_cascade_product_code/exp29_cascade_product_code.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp30_cascade_R1_9ch/exp30_cascade_R1_9ch.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp43_adiyat_864_compound/exp43_adiyat_864_compound.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- ... and 42 more

## INFO (62)

### L2_stale_dep_failed — 1
- `results/experiments/exp95f_short_envelope_replication/exp95f_short_envelope_replication.json` — Receipt cites exp95e_full_114_consensus_universal which has a FAIL_* verdict. Either remove the citation or document why a failed result is being relied upon. (citing receipt is also FAIL_*, treating as follow-up characterisation, not substantive reliance)  (citing_verdict=FAIL_envelope_phase_boundary; cited_dep=exp95e_full_114_consensus_universal; dep_verdict=FAIL_per_surah_floor)

### L7_f_documents_retraction — 3
- `` — F54 cites receipt exp95e_full_114_consensus_universal whose verdict is FAIL_per_surah_floor (intentional — F-row documents retraction)  (f_number=54; cited_receipt=exp95e_full_114_consensus_universal; verdict=FAIL_per_surah_floor)
- `` — F91 cites receipt exp181_F83_max_feature whose verdict is NO_IMPROVEMENT_OVER_F83 (intentional — F-row documents retraction)  (f_number=91; cited_receipt=exp181_F83_max_feature; verdict=NO_IMPROVEMENT_OVER_F83)
- `` — F90 cites receipt exp180_F86_lagrangian_KKT whose verdict is  (intentional — F-row documents retraction)  (f_number=90; cited_receipt=exp180_F86_lagrangian_KKT; verdict=)

### L8_orphan_receipt — 58
- `results/experiments/exp02_mi_criticality/exp02_mi_criticality.json` — Receipt exp02_mi_criticality is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp03_adiyat/exp03_adiyat.json` — Receipt exp03_adiyat is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp04_onomatopoeia/exp04_onomatopoeia.json` — Receipt exp04_onomatopoeia is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp05_subclass_atlas/exp05_subclass_atlas.json` — Receipt exp05_subclass_atlas is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp06_band_b/exp06_band_b.json` — Receipt exp06_band_b is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp08_tension_noncircular/exp08_tension_noncircular.json` — Receipt exp08_tension_noncircular is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp105_harakat_restoration/exp105_harakat_restoration.json` — Receipt exp105_harakat_restoration is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp110_phi_master_xtrad/exp110_phi_master_xtrad.json` — Receipt exp110_phi_master_xtrad is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp112_F55_daodejing_bigram/exp112_F55_daodejing_bigram.json` — Receipt exp112_F55_daodejing_bigram is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp11_R3_cross_scripture/exp11_R3_cross_scripture.json` — Receipt exp11_R3_cross_scripture is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp125c_RG_scaling_alpha_unification/exp125c_RG_scaling_alpha_unification.json` — Receipt exp125c_RG_scaling_alpha_unification is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp127_lda_robust_subset_hunt/exp127_lda_robust_subset_hunt.json` — Receipt exp127_lda_robust_subset_hunt is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp12_R4_char_lm/exp12_R4_char_lm.json` — Receipt exp12_R4_char_lm is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp130_F75_stability_under_resampling/exp130_F75_stability_under_resampling.json` — Receipt exp130_F75_stability_under_resampling is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp135_F79_bootstrap_stability/exp135_F79_bootstrap_stability.json` — Receipt exp135_F79_bootstrap_stability is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp13_R5_adversarial/exp13_R5_adversarial.json` — Receipt exp13_R5_adversarial is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp14_R6_word_graph_modularity/exp14_R6_word_graph_modularity.json` — Receipt exp14_R6_word_graph_modularity is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp159_paradigm_battery/exp159_paradigm_battery.json` — Receipt exp159_paradigm_battery is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp15_R7_noise_curve/exp15_R7_noise_curve.json` — Receipt exp15_R7_noise_curve is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp160_cross_scripture_ncd/exp160_cross_scripture_ncd.json` — Receipt exp160_cross_scripture_ncd is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp161_arabic_char_lm_R4_scaffold/exp161_arabic_char_lm_R4_scaffold.json` — Receipt exp161_arabic_char_lm_R4_scaffold is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp162_sigma_bigram_universal/exp162_sigma_bigram_universal.json` — Receipt exp162_sigma_bigram_universal is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp163_quran_geometric_shape/exp163_quran_geometric_shape.json` — Receipt exp163_quran_geometric_shape is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp164_quran_shape_embedding_sensitivity/exp164_quran_shape_embedding_sensitivity.json` — Receipt exp164_quran_shape_embedding_sensitivity is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp16_R8_null_ladder/exp16_R8_null_ladder.json` — Receipt exp16_R8_null_ladder is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp17_R9_cross_scale_VIS/exp17_R9_cross_scale_VIS.json` — Receipt exp17_R9_cross_scale_VIS is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp18_R10_verse_internal_order/exp18_R10_verse_internal_order.json` — Receipt exp18_R10_verse_internal_order is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp62_adiyat_2d_retest/exp62_adiyat_2d_retest.json` — Receipt exp62_adiyat_2d_retest is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp65_dual_state_bic/exp65_dual_state_bic.json` — Receipt exp65_dual_state_bic is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp69_madd_bridge/exp69_madd_bridge.json` — Receipt exp69_madd_bridge is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- ... and 28 more
