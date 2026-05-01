# Zero-Trust Audit — 20260428T221126Z

- Receipts scanned: **158**
- CRITICAL: **0**
- WARN: 55
- INFO: 50

## WARN (55)

### L6_no_calibration_source_declared — 55
- `results/experiments/exp02_mi_criticality/exp02_mi_criticality.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp07_tension_law/exp07_tension_law.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp08_tension_noncircular/exp08_tension_noncircular.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp09_R1_variant_forensics_9ch/exp09_R1_variant_forensics_9ch.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp102_imitation_battery/exp102_imitation_battery.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp104_F53_tanakh_pilot/exp104_F53_tanakh_pilot.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp104b_F53_psalm119/exp104b_F53_psalm119.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp104c_F53_psalm78/exp104c_F53_psalm78.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp105_harakat_restoration/exp105_harakat_restoration.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp21_E1_EL_survival/exp21_E1_EL_survival.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp29_cascade_product_code/exp29_cascade_product_code.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp30_cascade_R1_9ch/exp30_cascade_R1_9ch.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp43_adiyat_864_compound/exp43_adiyat_864_compound.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp44_F6_spectrum/exp44_F6_spectrum.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp45_two_letter_746k/exp45_two_letter_746k.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp47_phonetic_distance_law/exp47_phonetic_distance_law.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp48_verse_graph_topology/exp48_verse_graph_topology.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp49_6d_hotelling/exp49_6d_hotelling.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp53_ar1_6d_gate/exp53_ar1_6d_gate.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp54_phonetic_law_full/exp54_phonetic_law_full.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp55_gamma_length_stratified/exp55_gamma_length_stratified.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp60_lc3_parsimony_theorem/exp60_lc3_parsimony_theorem.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp61_vl_cv_floor_sensitivity/exp61_vl_cv_floor_sensitivity.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp63_var1_cross_feature/exp63_var1_cross_feature.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp64_unified_law_ensemble/exp64_unified_law_ensemble.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp65_dual_state_bic/exp65_dual_state_bic.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp66_extended_mahalanobis/exp66_extended_mahalanobis.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp67_adjacent_jaccard/exp67_adjacent_jaccard.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp69_madd_bridge/exp69_madd_bridge.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- `results/experiments/exp80_mi_decay/exp80_mi_decay.json` — Receipt carries a tau/threshold-style field but declares no calibration_source. Cannot verify that calibration is independent of the test fold.
- ... and 25 more

## INFO (50)

### L2_stale_dep_failed — 1
- `results/experiments/exp95f_short_envelope_replication/exp95f_short_envelope_replication.json` — Receipt cites exp95e_full_114_consensus_universal which has a FAIL_* verdict. Either remove the citation or document why a failed result is being relied upon. (citing receipt is also FAIL_*, treating as follow-up characterisation, not substantive reliance)  (citing_verdict=FAIL_envelope_phase_boundary; cited_dep=exp95e_full_114_consensus_universal; dep_verdict=FAIL_per_surah_floor)

### L7_f_documents_retraction — 1
- `` — F54 cites receipt exp95e_full_114_consensus_universal whose verdict is FAIL_per_surah_floor (intentional — F-row documents retraction)  (f_number=54; cited_receipt=exp95e_full_114_consensus_universal; verdict=FAIL_per_surah_floor)

### L8_orphan_receipt — 48
- `results/experiments/exp02_mi_criticality/exp02_mi_criticality.json` — Receipt exp02_mi_criticality is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp03_adiyat/exp03_adiyat.json` — Receipt exp03_adiyat is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp04_onomatopoeia/exp04_onomatopoeia.json` — Receipt exp04_onomatopoeia is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp05_subclass_atlas/exp05_subclass_atlas.json` — Receipt exp05_subclass_atlas is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp06_band_b/exp06_band_b.json` — Receipt exp06_band_b is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp08_tension_noncircular/exp08_tension_noncircular.json` — Receipt exp08_tension_noncircular is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp105_harakat_restoration/exp105_harakat_restoration.json` — Receipt exp105_harakat_restoration is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp11_R3_cross_scripture/exp11_R3_cross_scripture.json` — Receipt exp11_R3_cross_scripture is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp12_R4_char_lm/exp12_R4_char_lm.json` — Receipt exp12_R4_char_lm is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp13_R5_adversarial/exp13_R5_adversarial.json` — Receipt exp13_R5_adversarial is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp14_R6_word_graph_modularity/exp14_R6_word_graph_modularity.json` — Receipt exp14_R6_word_graph_modularity is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp15_R7_noise_curve/exp15_R7_noise_curve.json` — Receipt exp15_R7_noise_curve is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp16_R8_null_ladder/exp16_R8_null_ladder.json` — Receipt exp16_R8_null_ladder is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp17_R9_cross_scale_VIS/exp17_R9_cross_scale_VIS.json` — Receipt exp17_R9_cross_scale_VIS is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp18_R10_verse_internal_order/exp18_R10_verse_internal_order.json` — Receipt exp18_R10_verse_internal_order is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp62_adiyat_2d_retest/exp62_adiyat_2d_retest.json` — Receipt exp62_adiyat_2d_retest is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp65_dual_state_bic/exp65_dual_state_bic.json` — Receipt exp65_dual_state_bic is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp69_madd_bridge/exp69_madd_bridge.json` — Receipt exp69_madd_bridge is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp71_benford/exp71_benford.json` — Receipt exp71_benford is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp75_fractal_dimension/exp75_fractal_dimension.json` — Receipt exp75_fractal_dimension is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp77_gamma_entropy/exp77_gamma_entropy.json` — Receipt exp77_gamma_entropy is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp78_inverse_phi_cascade/exp78_inverse_phi_cascade.json` — Receipt exp78_inverse_phi_cascade is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp79_ar1_decorrelation/exp79_ar1_decorrelation.json` — Receipt exp79_ar1_decorrelation is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp81_entropy_rate/exp81_entropy_rate.json` — Receipt exp81_entropy_rate is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp82_transfer_entropy/exp82_transfer_entropy.json` — Receipt exp82_transfer_entropy is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp85_scale_hierarchy/exp85_scale_hierarchy.json` — Receipt exp85_scale_hierarchy is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp91_meccan_medinan_stability/exp91_meccan_medinan_stability.json` — Receipt exp91_meccan_medinan_stability is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp92_genai_adversarial_forge/exp92_genai_adversarial_forge.json` — Receipt exp92_genai_adversarial_forge is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp97_multifractal_spectrum/exp97_multifractal_spectrum.json` — Receipt exp97_multifractal_spectrum is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- `results/experiments/exp98_per_verse_mdl/exp98_per_verse_mdl.json` — Receipt exp98_per_verse_mdl is not referenced from any of RANKED_FINDINGS / PROGRESS / PAPER / REFERENCE.
- ... and 18 more
