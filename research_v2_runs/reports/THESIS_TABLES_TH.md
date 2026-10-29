# Thesis-ready Tables — EXPLORATORY

ทุกผลใหม่ในรายงานนี้เป็น EXPLORATORY (LinkSocial, retrospectively exposed). G0/G1 = DECLARED PASSED by researcher แต่ REFERENCE NOT PROVIDED; G5 = NOT MET. ไม่มี confirmatory result และไม่อ้างโมเดลดีที่สุดทั่วไป.

## Dataset และ evaluation population

| Item | ค่าที่วัด | Evidence |
|---|---|---|
| input_rows | 36807 | [MAIN@1bc4a8c:research_v2_runs/metrics/label_sanity.json#input_rows] |
| eligible_rows | 36804 | [MAIN@1bc4a8c:research_v2_runs/metrics/label_sanity.json#eligible_rows] |
| quarantined_rows | 3 | [MAIN@1bc4a8c:research_v2_runs/metrics/label_sanity.json#quarantined_rows] |
| missing_key_rows | 3 | [MAIN@1bc4a8c:research_v2_runs/metrics/label_sanity.json#missing_key_rows] |
| distinct_entities | 15297 | [MAIN@1bc4a8c:research_v2_runs/metrics/label_sanity.json#distinct_entities] |
| max_group_size | 4 | [MAIN@1bc4a8c:research_v2_runs/metrics/label_sanity.json#max_group_size] |
| cross_platform_positive_pairs | 29243 | [MAIN@1bc4a8c:research_v2_runs/metrics/label_sanity.json#cross_platform_positive_pairs] |
| million_positive_guard | True | [MAIN@1bc4a8c:research_v2_runs/metrics/label_sanity.json#million_positive_guard] |

## Blocking: matched-budget development

Population = ผลรวมคู่ภายใน development folds เท่านั้น; ไม่รวมคู่ข้าม folds. ทุกวิธีในตารางมี total |C| เท่ากัน.

| Method | |C| | GT denominator | Found positives | PC | Evidence |
|---|---|---|---|---|---|
| B0 | 351494 | 23391 | 20740 | 0.8867 | [MAIN@1bc4a8c:research_v2_runs/metrics/blocking_development.json#B0] |
| sparse | 351494 | 23391 | 21576 | 0.9224 | [MAIN@1bc4a8c:research_v2_runs/metrics/blocking_development.json#sparse] |
| dense | 351494 | 23391 | 14100 | 0.6028 | [MAIN@1bc4a8c:research_v2_runs/metrics/blocking_development.json#dense] |
| hybrid_union | 351494 | 23391 | 14111 | 0.6033 | [MAIN@1bc4a8c:research_v2_runs/metrics/blocking_development.json#hybrid_union] |
| hybrid_rrf | 351494 | 23391 | 21526 | 0.9203 | [MAIN@1bc4a8c:research_v2_runs/metrics/blocking_development.json#hybrid_rrf] |

## Blocking: locked test

| Method | |C| | GT | PC | RR | Evidence |
|---|---|---|---|---|---|
| B0 | 87702 | 5852 | 0.8870 | 0.9951 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#blocking-B0] |
| sparse | 87702 | 5852 | 0.9245 | 0.9951 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#blocking-sparse] |
| hybrid_rrf | 87702 | 5852 | 0.9241 | 0.9951 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#blocking-hybrid_rrf] |

## Matcher comparison: natural candidate locked test

ทุกแถวใช้ B* และ candidate population เดียวกัน; F1/P/Rcandidate ใช้ validation-F1 threshold ไม่ใช้ test-selected threshold. Primary discrimination ใช้ mean score ของทุก GBDT seed.

| Matcher | N candidate | Positives | AP | candidate F1 | P | e2e recall | seed AP SD | Evidence |
|---|---|---|---|---|---|---|---|---|
| matcher-rule | 87702 | 5410 | 0.9237 | 0.8838 | 0.9443 | 0.7678 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#matcher-rule] |
| matcher-GBDT-lexical | 87702 | 5410 | 0.9790 | 0.9543 | 0.9835 | 0.8568 | 0.0008 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#matcher-GBDT-lexical] |
| matcher-GBDT-fusion | 87702 | 5410 | 0.9793 | 0.9536 | 0.9779 | 0.8602 | 0.0007 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#matcher-GBDT-fusion] |
| matcher-GBDT-lexical-single-fullname | 87702 | 5410 | 0.8807 | 0.8580 | 0.9345 | 0.7333 | 0.0006 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#matcher-GBDT-lexical-single-fullname] |

## Fusion และ ablations: development OOF เท่านั้น

F-LEX = 35 features; F-SEM = 6 features; fusion = 41 features ไม่ใช่ historical image_context 41 features. ทั้ง username/fullname/bio/location/links ใช้ missingness indicators; leave-one-group-out ตัด semantic features ของ attribute นั้นด้วย. ไม่มีภาพใน V2 run.

| Development model | OOF AP | Seeds | AP seed SD | Evidence |
|---|---|---|---|---|
| GBDT-fusion-without-bio | 0.9744 | 5 | 0.0002 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_GBDT-fusion-without-bio.json#results] |
| GBDT-fusion-without-fullname | 0.9128 | 5 | 0.0003 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_GBDT-fusion-without-fullname.json#results] |
| GBDT-fusion-without-links | 0.9636 | 5 | 0.0002 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_GBDT-fusion-without-links.json#results] |
| GBDT-fusion-without-location | 0.9777 | 5 | 0.0002 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_GBDT-fusion-without-location.json#results] |
| GBDT-fusion-without-username | 0.9483 | 5 | 0.0003 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_GBDT-fusion-without-username.json#results] |
| GBDT-fusion | 0.9778 | 5 | 0.0002 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_GBDT-fusion.json#results] |
| GBDT-lexical-single-bio | 0.2840 | 5 | 0.0007 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_GBDT-lexical-single-bio.json#results] |
| GBDT-lexical-single-fullname | 0.8805 | 5 | 0.0006 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_GBDT-lexical-single-fullname.json#results] |
| GBDT-lexical-single-links | 0.6579 | 5 | 0.0003 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_GBDT-lexical-single-links.json#results] |
| GBDT-lexical-single-location | 0.0635 | 5 | 0.0002 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_GBDT-lexical-single-location.json#results] |
| GBDT-lexical-single-username | 0.7787 | 5 | 0.0005 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_GBDT-lexical-single-username.json#results] |
| GBDT-lexical | 0.9769 | 5 | 0.0002 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_GBDT-lexical.json#results] |
| GBDT-semantic | 0.8564 | 5 | 0.0003 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_GBDT-semantic.json#results] |
| LR-fusion-without-bio | 0.9529 | 1 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_LR-fusion-without-bio.json#results] |
| LR-fusion-without-fullname | 0.8800 | 1 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_LR-fusion-without-fullname.json#results] |
| LR-fusion-without-links | 0.9412 | 1 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_LR-fusion-without-links.json#results] |
| LR-fusion-without-location | 0.9600 | 1 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_LR-fusion-without-location.json#results] |
| LR-fusion-without-username | 0.9208 | 1 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_LR-fusion-without-username.json#results] |
| LR-fusion | 0.9600 | 1 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_LR-fusion.json#results] |
| LR-lexical-single-bio | 0.1934 | 1 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_LR-lexical-single-bio.json#results] |
| LR-lexical-single-fullname | 0.8612 | 1 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_LR-lexical-single-fullname.json#results] |
| LR-lexical-single-links | 0.6504 | 1 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_LR-lexical-single-links.json#results] |
| LR-lexical-single-location | 0.0636 | 1 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_LR-lexical-single-location.json#results] |
| LR-lexical-single-username | 0.7680 | 1 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_LR-lexical-single-username.json#results] |
| LR-lexical | 0.9595 | 1 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_LR-lexical.json#results] |
| LR-semantic | 0.8448 | 1 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_LR-semantic.json#results] |
| rule | 0.9253 | 1 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/model_rule.json#results] |

## Policy comparison: expected cost และ automatic links

Population = B* candidate set + blocked GT positives สำหรับ utility numerator; cost denominator ในตารางคือ all cross-platform pairs ใน locked fold. Cost ratios 2:1:0.1 เป็น ASSUMPTION ไม่ใช่เงินที่วัดได้. Mean/SD ใช้ทุก optimizer seed ไม่เลือก seed ที่ดีที่สุด.

| Policy | Seeds | Cost/all-pair | seed cost SD | Auto P | Auto e2e recall | Review rate|C | Evidence |
|---|---|---|---|---|---|---|---|
| fixed_0.5 | 1 | 0.0000582 | 0.0000000 | 0.9779 | 0.8602 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#policy-E6-1] |
| historical_R0 | 1 | 0.0000736 | 0.0000000 | 0.9985 | 0.6987 | 0.0058 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#policy-E6-1] |
| historical_stage18 | 1 | 0.0000742 | 0.0000000 | 0.9969 | 0.7666 | 0.0008 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#policy-E6-1] |
| validation_F1 | 1 | 0.0000570 | 0.0000000 | 0.9807 | 0.8589 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#policy-E6-2] |
| closed_cost | 1 | 0.0000560 | 0.0000000 | 0.9883 | 0.8483 | 0.0000 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#policy-E6-3] |
| Chow | 1 | 0.0000454 | 0.0000000 | 0.9970 | 0.7847 | 0.0163 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#policy-E6-3] |
| random | 10 | 0.0000498 | 0.0000003 | 0.9969 | 0.8017 | 0.0049 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#policy-E6-4] |
| scrambled_sobol | 10 | 0.0000498 | 0.0000003 | 0.9969 | 0.7990 | 0.0052 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#policy-E6-4] |
| TPE | 10 | 0.0000496 | 0.0000000 | 0.9970 | 0.8022 | 0.0050 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#policy-E6-4] |
| GA | 10 | 0.0000495 | 0.0000000 | 0.9970 | 0.8026 | 0.0050 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#policy-E6-5] |
| three_way | 10 | 0.0000448 | 0.0000001 | 0.9969 | 0.7982 | 0.0137 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#policy-E6-6] |

## End-to-end REF และ BEST-VAL

REF คือ best lexical blocker + lexical GBDT + validation-F1; BEST-VAL เป็น bundle ของ best policy บน M* ที่เลือกจาก development. ใช้ alias ไป frozen evaluation เดิม ไม่เปิด test เพื่อสร้างยอดซ้ำ.

| Pipeline | Frozen config | Auto P | Auto recall | Auto F1 | Cost/all-pair | Evidence |
|---|---|---|---|---|---|---|
| E7-1_REF | matcher-GBDT-lexical | 0.9835 | 0.8568 | 0.9158 | 0.0000560 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#matcher-GBDT-lexical] |
| E7-1_BEST_VAL | policy-E6-6 | 0.9969 | 0.7982 | 0.8865 | 0.0000448 | [MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#policy-E6-6] |

## 2×2×2 stage attribution

Blocker0=B0,1=hybrid; matcher0=calibrated tuned rule,1=M*; policy0=fixed0.5,1=best validation policy. ทุกแถวใช้ all cross-platform-pair cost denominator เดียวกัน.

| Cell | B | M | P | Expected cost/all-pair | Auto recall |
|---|---|---|---|---|---|
| factorial-B0-M0-P0 | 0 | 0 | 0 | 0.0000947 | 0.7433 |
| factorial-B0-M0-P1 | 0 | 0 | 1 | 0.0000744 | 0.5891 |
| factorial-B0-M1-P0 | 0 | 1 | 0 | 0.0000674 | 0.8380 |
| factorial-B0-M1-P1 | 0 | 1 | 1 | 0.0000543 | 0.7898 |
| factorial-B1-M0-P0 | 1 | 0 | 0 | 0.0000949 | 0.7478 |
| factorial-B1-M0-P1 | 1 | 0 | 1 | 0.0000713 | 0.5882 |
| factorial-B1-M1-P0 | 1 | 1 | 0 | 0.0000567 | 0.8592 |
| factorial-B1-M1-P1 | 1 | 1 | 1 | 0.0000444 | 0.7980 |
[MAIN@1bc4a8c:research_v2_runs/metrics/secondary_analyses.json#factorial_cells]

## Compute cost

Inference entries เป็น median ของห้ารอบจริงบนเครื่องเดียว; ตารางย่อเป็น median ของ recorded medians เมื่อ stage มีหลาย seed/blocker. ไม่ใช่ deployment benchmark แบบ isolated hardware และไม่เอา sum concurrent runtimes ไปเรียก elapsed time. Encoder หน่วย profiles; ขั้นอื่นหน่วย pairs.

| Stage | Observations | Median seconds | Unit | Repeats/observation |
|---|---|---|---|---|
| candidate_B0 | 1 | 0.1435 | pairs | 5 |
| candidate_sparse | 1 | 5.4545 | pairs | 5 |
| final_profile_embedding | 1 | 53.7365 | profiles | 5 |
| candidate_hybrid_rrf | 1 | 9.2383 | pairs | 5 |
| pair_feature_sparse | 1 | 3.0321 | pairs | 5 |
| model_rule | 3 | 0.0011 | pairs | 5 |
| model_GBDT-lexical | 5 | 0.2130 | pairs | 5 |
| model_GBDT-fusion | 15 | 0.2114 | pairs | 5 |
| model_GBDT-lexical-single-fullname | 5 | 0.1662 | pairs | 5 |
| calibration | 14 | 0.0010 | pairs | 5 |
| policy_fixed_0.5 | 5 | 0.0000 | pairs | 5 |
| policy_historical_R0 | 1 | 0.0002 | pairs | 5 |
| policy_historical_stage18 | 1 | 0.0005 | pairs | 5 |
| policy_validation_F1 | 1 | 0.0000 | pairs | 5 |
| policy_closed_cost | 1 | 0.0000 | pairs | 5 |
| policy_Chow | 1 | 0.0007 | pairs | 5 |
| policy_random | 10 | 0.0005 | pairs | 5 |
| policy_scrambled_sobol | 10 | 0.0005 | pairs | 5 |
| policy_TPE | 10 | 0.0005 | pairs | 5 |
| policy_GA | 10 | 0.0005 | pairs | 5 |
| policy_three_way | 50 | 0.0002 | pairs | 5 |
| pair_feature_B0 | 1 | 2.4960 | pairs | 5 |
| pair_feature_hybrid_rrf | 1 | 2.7153 | pairs | 5 |
[MAIN@1bc4a8c:research_v2_runs/metrics/final_summary.json#timings]

## Learning curves: fixed hyperparameters, seed42

AP mean/SD ในตารางนี้เฉลี่ยระหว่างสี่ development folds ไม่ใช่ seed SD. TF-IDF fit เฉพาะ training entities ที่สุ่มเลือก; 100%ใช้ main selected seed42 OOF ไม่ใช้ ensemble. ไม่มี reduced-data tuned-rule comparison เพราะไม่ retune หลังเปิด test.

| Learner | Entity fraction | Mean fold AP | Fold AP SD | Folds | Evidence |
|---|---|---|---|---|---|
| GBDT | 0.1 | 0.9372 | 0.0047 | 4 | [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--learning-curve-GBDT-frac0.1-fold0.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--learning-curve-GBDT-frac0.1-fold1.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--learning-curve-GBDT-frac0.1-fold2.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--learning-curve-GBDT-frac0.1-fold3.json#results] |
| GBDT | 0.25 | 0.9651 | 0.0029 | 4 | [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--learning-curve-GBDT-frac0.25-fold0.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--learning-curve-GBDT-frac0.25-fold1.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--learning-curve-GBDT-frac0.25-fold2.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--learning-curve-GBDT-frac0.25-fold3.json#results] |
| GBDT | 0.5 | 0.9719 | 0.0023 | 4 | [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--learning-curve-GBDT-frac0.5-fold0.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--learning-curve-GBDT-frac0.5-fold1.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--learning-curve-GBDT-frac0.5-fold2.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--learning-curve-GBDT-frac0.5-fold3.json#results] |
| GBDT | 1.0 | 0.9767 | 0.0016 | 4 | [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--GBDT-lexical-seed42-oof0.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--GBDT-lexical-seed42-oof1.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--GBDT-lexical-seed42-oof2.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-2--GBDT-lexical-seed42-oof3.json#results] |
| LR | 0.1 | 0.9338 | 0.0008 | 4 | [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--learning-curve-LR-frac0.1-fold0.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--learning-curve-LR-frac0.1-fold1.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--learning-curve-LR-frac0.1-fold2.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--learning-curve-LR-frac0.1-fold3.json#results] |
| LR | 0.25 | 0.9480 | 0.0014 | 4 | [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--learning-curve-LR-frac0.25-fold0.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--learning-curve-LR-frac0.25-fold1.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--learning-curve-LR-frac0.25-fold2.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--learning-curve-LR-frac0.25-fold3.json#results] |
| LR | 0.5 | 0.9551 | 0.0015 | 4 | [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--learning-curve-LR-frac0.5-fold0.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--learning-curve-LR-frac0.5-fold1.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--learning-curve-LR-frac0.5-fold2.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--learning-curve-LR-frac0.5-fold3.json#results] |
| LR | 1.0 | 0.9595 | 0.0014 | 4 | [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--LR-lexical-seed42-oof0.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--LR-lexical-seed42-oof1.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--LR-lexical-seed42-oof2.json#results]; [MAIN@1bc4a8c:research_v2_runs/metrics/E3-1--LR-lexical-seed42-oof3.json#results] |

### Factorial effects

นิยาม effect=2×mean(sign-product×metric) หรือ2βใน +/-1 coding; interactionนี้ไม่ใช่ raw difference-of-differences และเป็น descriptive component substitution บน corpusนี้เท่านั้น.

| Factors | Cost effect | Recall effect |
|---|---|---|
| blocker | -0.00000585 | 0.0082 |
| matcher | -0.00002809 | 0.1541 |
| policy | -0.00001735 | -0.1058 |
| blocker × matcher | -0.00000441 | 0.0065 |
| blocker × policy | -0.00000062 | -0.0046 |
| matcher × policy | 0.00000462 | 0.0511 |
| blocker × matcher × policy | 0.00000104 | -0.0019 |
[MAIN@1bc4a8c:research_v2_runs/metrics/secondary_analyses.json#factorial_effects]

Feature benchmark ใช้ common lexical+semantic featurizer จึงไม่ใช่ isolated incremental semantic cost ratio; ไม่อ้าง full H3 ms/pair ratio ที่ไม่ได้วัดแยก. Learning curves ใช้ fixed hyperparameters และ TF-IDF ที่ fit บน selected training identities เท่านั้น; ไม่มีการ retune หลังเปิด test. [MAIN@1bc4a8c:research_v2_runs/metrics/tier2_summary.json#results]

## Univariate development diagnostics — EXPLORATORY

ใช้ candidate population ของสี่ development folds; เป็น feature diagnostics ไม่ใช่ supervised test model comparison.

| Feature | Candidate AP | n pairs |
|---|---|---|
| username_exact | 0.4462 | 351494 |
| username_jaro_winkler | 0.7004 | 351494 |
| username_normalized_levenshtein | 0.7017 | 351494 |
| username_token_jaccard | 0.4462 | 351494 |
| username_tfidf_cosine | 0.7632 | 351494 |
| username_both_present | 0.0617 | 351494 |
| username_one_missing | 0.0613 | 351494 |
| fullname_exact | 0.6058 | 351494 |
| fullname_jaro_winkler | 0.8118 | 351494 |
| fullname_normalized_levenshtein | 0.7661 | 351494 |
| fullname_token_jaccard | 0.7640 | 351494 |
| fullname_tfidf_cosine | 0.8510 | 351494 |
| fullname_both_present | 0.0624 | 351494 |
| fullname_one_missing | 0.0608 | 351494 |
| bio_exact | 0.0679 | 351494 |
| bio_jaro_winkler | 0.1488 | 351494 |
| bio_normalized_levenshtein | 0.1563 | 351494 |
| bio_token_jaccard | 0.1979 | 351494 |
| bio_tfidf_cosine | 0.1825 | 351494 |
| bio_both_present | 0.0583 | 351494 |
| bio_one_missing | 0.0667 | 351494 |
| location_exact | 0.0614 | 351494 |
| location_jaro_winkler | 0.0614 | 351494 |
| location_normalized_levenshtein | 0.0614 | 351494 |
| location_token_jaccard | 0.0614 | 351494 |
| location_tfidf_cosine | 0.0614 | 351494 |
| location_both_present | 0.0614 | 351494 |
| location_one_missing | 0.0627 | 351494 |
| links_exact | 0.2002 | 351494 |
| links_jaro_winkler | 0.2890 | 351494 |
| links_normalized_levenshtein | 0.2528 | 351494 |
| links_token_jaccard | 0.2002 | 351494 |
| links_tfidf_cosine | 0.6100 | 351494 |
| links_both_present | 0.0617 | 351494 |
| links_one_missing | 0.0603 | 351494 |

Source: metrics/E2-1--univariate-OOF-lexical.json
| Feature | Candidate AP | n pairs |
|---|---|---|
| fullname_cosine | 0.8253 | 351494 |
| fullname_both_present | 0.0624 | 351494 |
| fullname_one_missing | 0.0608 | 351494 |
| bio_cosine | 0.1993 | 351494 |
| bio_both_present | 0.0583 | 351494 |
| bio_one_missing | 0.0667 | 351494 |

Source: metrics/E4-1--univariate-semantic.json

## Robustness strata — EXPLORATORY, descriptive

Strata อาจทับซ้อนกัน; denominator คือ candidate rows และ positives ภายในแต่ละ stratum ไม่เปรียบ AP ระหว่าง strata เป็น causal gain.

| Stratum | n pairs | Positive pairs | Candidate AP |
|---|---|---|---|
| stratum_username_low=0 | 46393 | 4790 | 0.9877 |
| stratum_username_low=1 | 41309 | 620 | 0.9024 |
| stratum_both_names_low=0 | 66026 | 5348 | 0.9825 |
| stratum_both_names_low=1 | 21676 | 62 | 0.6221 |
| stratum_non_ascii_text=0 | 77516 | 4492 | 0.9797 |
| stratum_non_ascii_text=1 | 10186 | 918 | 0.9772 |
| stratum_presence_pattern=0 | 54 | 0 | 0.0000 |
| stratum_presence_pattern=1 | 2317 | 73 | 0.8166 |
| stratum_presence_pattern=2 | 22 | 1 | 0.5000 |
| stratum_presence_pattern=3 | 9158 | 681 | 0.9322 |
| stratum_presence_pattern=4 | 59 | 0 | 0.0000 |
| stratum_presence_pattern=5 | 330 | 16 | 0.9340 |
| stratum_presence_pattern=7 | 10618 | 616 | 0.9620 |
| stratum_presence_pattern=16 | 13 | 0 | 0.0000 |
| stratum_presence_pattern=17 | 239 | 20 | 0.9699 |
| stratum_presence_pattern=18 | 19 | 1 | 1.0000 |
| stratum_presence_pattern=19 | 10224 | 925 | 0.9888 |
| stratum_presence_pattern=20 | 131 | 1 | 1.0000 |
| stratum_presence_pattern=21 | 801 | 45 | 0.9805 |
| stratum_presence_pattern=22 | 4 | 1 | 1.0000 |
| stratum_presence_pattern=23 | 53713 | 3030 | 0.9896 |
| platform_pair_code=[0, 1] | 24444 | 1529 | 0.9788 |
| platform_pair_code=[0, 2] | 39245 | 1935 | 0.9734 |
| platform_pair_code=[1, 2] | 24013 | 1946 | 0.9849 |

## Mechanical error taxonomy — EXPLORATORY

เป็น flags/counts จาก frozen predictions ไม่ใช่ adjudicated semantic causes; ไม่รวม flags ซ้ำเป็น total ใหม่.

| Operating-point index | FP_low_both_names | FP_other_feature_patterns | FN_low_both_names_in_candidates | FN_other_feature_patterns_in_candidates | FN_blocking_miss | REVIEW_positive_not_auto_linked | FP_total | automatic_FN_total |
|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 15 | 41 | 677 | 442 | 505 | 15 | 1160 |
| 2 | 0 | 14 | 43 | 706 | 442 | 535 | 14 | 1191 |
| 3 | 0 | 14 | 43 | 702 | 442 | 532 | 14 | 1187 |
| 4 | 0 | 15 | 42 | 692 | 442 | 521 | 15 | 1176 |
| 5 | 0 | 14 | 43 | 718 | 442 | 548 | 14 | 1203 |
| 6 | 0 | 15 | 42 | 700 | 442 | 529 | 15 | 1184 |
| 7 | 0 | 15 | 42 | 692 | 442 | 521 | 15 | 1176 |
| 8 | 0 | 14 | 43 | 713 | 442 | 535 | 14 | 1198 |
| 9 | 0 | 15 | 41 | 663 | 442 | 491 | 15 | 1146 |
| 10 | 0 | 14 | 43 | 704 | 442 | 538 | 14 | 1189 |

Source: metrics/secondary_analyses.json
