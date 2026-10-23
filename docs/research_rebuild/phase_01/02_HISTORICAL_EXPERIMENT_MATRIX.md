# 02 — Historical Experiment Lineage Matrix

## ขอบเขตและระดับหลักฐาน
ตาราง CSV/JSON มี **1077 แถว** แยก experiment × variant × model/configuration × seed × split/threshold diagnostic โดยไม่ยุบ family ให้เหลือแถวเดียว ทุกผลเป็น `reported_only` หรือ historical smoke/reviewer-derived ตามคอลัมน์ status; การอ่าน summary หรือ historical independent_metrics ไม่เท่ากับคำนวณใหม่จากแถวผล ค่าของ V2R1 ที่ companion audit คำนวณต่อแถวต้องอ้างรายงานนั้นแยก ไม่เปลี่ยนสถานะในตารางนี้โดยปริยาย

ไม่มีการ train/optimization/download และไม่มีการเขียนทับ source/model/result/workbook ประวัติ แถว CSV row/JSON pointer เป็นตำแหน่ง citation ของผล ไม่ใช้เป็น pair join; ไม่ merge positional data และไม่ประกาศ compatibility เพียงเพราะจำนวนแถวหรือชื่อ feature เท่ากัน

Parent verification เพิ่ม `lineage_metric_evidence_links.csv/json` จำนวน48links สำหรับ V2/V2R1 summaries และ reviewer rows โดยจับ family/outer seed/method/scope ไม่ใช่rowposition แต่ละlinkชี้granularartifactและstatusที่คำนวณซ้ำใน`verified_metrics.json`; numerical evidenceผ่านไม่เลื่อนrawprovenance/governance/leakageclaimให้PASS. สถานะreported-onlyของsource-summaryในmatrixคงเดิมโดยมีcompanionevidenceชัดเจน

อ่าน audit/protocol ก่อนทำงาน: `docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md`, `docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md`, V2 `PROTOCOL.md` และ V2R1 `PROTOCOL_V2R1.md`. Protocol เสนอรอบใหม่ยังไม่ใช่ผลรันใหม่

## รายการ lineage และความต่างที่ต้องรักษา

| Family | จำนวนแถว | ประชากร/การตีความ |
|---|---:|---|
| Notebook-legacy | 3 | original test25053 vs notebookv2 test30713; distinct from multimodal and V2R1 |
| multimodal | 694 | 58696 sampled pairs; not full 2086245 candidates |
| R-series | 68 | full cache2086245 =exact12403+scored2073842; current cache test_scored191693 verified from split/decision_source columns; test_exact3747 |
| ICSEC-legacy | 30 | legacy score/feature scope; source-specific constants must not be promoted to V2 |
| ICSEC-V2 | 15 | cross-platform eligible input36804; exact12403/scored2073842/full2086245; covered positives25931 of29243, misses3312; seed-specific test scopes |
| ICSEC-V2R1 | 33 | V2 candidate keys and scope; exact/model-scored/blocking-miss workflows per outer seed |
| GA-evidence | 234 | sampled58696 vs full2086245; full projection includes development and dropped rows |

### R0–R6 และหลักฐานต้นทาง
- R0 คือ production score baseline ไม่ใช่ proof ว่า scorer ต้นทางมี17 inputs: source/model ต้นฉบับขาด และ production main report ระบุ image-context41. เก็บชื่อ historical17 กับ scorer provenance ambiguity คนละข้อ ไม่แก้ชื่อย้อนหลัง
- R1 เป็น4-parameter downstream GA `[t_match,t_review,c_promote,c_demote]` บน probability เดิม ไม่ฝึก predictor; manual_stage18 เป็นอีก policy variant. R2/R3 ใช้ reconstructed17+MiniLM18 ไม่ใช่ notebook17 หรือ multimodal41. name_sim ของ legacyถูก gate ด้วย predecessor score>=.5 (`exp_lib.py:93–101`) จึงไม่เป็น feature ablation ล้วน
- R4/R5 แยก Bloom lengths2000/1000/500/250,k10 × manual/GA × test/full ครบ. Bloom privacy claim เป็นประวัติ ไม่ใช่การรับรอง privacy จาก audit นี้
- R6/R6-GA แยก probability evaluation บน original cache ออกจาก semantic retrieval radius0/radius1 บน missed-positive3316; frozen DistilBERT +learned64-bit hash/match heads ไม่ใช่ fine-tuned backbone. recovery4 candidates/3 MATCH เป็น historical report ไม่ใช่ metric recomputation ใหม่
- Legacy full total_pos29247/misses3316 แตกต่างจาก cross-platform V2 total_pos29243/misses3312; ห้ามย้าย constantsข้าม family. ตรวจcacheปัจจุบันจากคอลัมน์split/decision_sourceได้test_scored191693/test_exact3747 ตรงจำนวนscoredในoriginalreport; ยังไม่พิสูจน์pairkey/modellineageจากจำนวนแถวตรงกัน

### Multimodal / model comparisons แบบแยก variant
- Suite text_attr_hybrid23, image_stats37, image_context41 แยกทั้งสาม; original model leaderboards GB/RF/logreg ถูกเก็บแยก model และ selected metric report. main sampled data58696 = train41803 +val8580 +test8313 ไม่ใช่ full workflow2.086M
- Main benchmark7 families GB/RF/logreg/extra_trees/linear_svm/adaboost/MLP, tuning15 configurations, negative-ratio6 runs, leakage-safe3 models, strict5 models, strict calibration8 model×calibrator และ threshold sweepsทั้งหมดเป็นแถวแยก; labels strict/leak-safe ไม่ใช่การรับรองว่า leak-free
- Original suite selected GB@.35 กับ refreshed benchmark GB@.46 เป็นคนละผล; strict report logreg+sigmoid@.50 และ MLP strict referenceไม่ใช่ final production GB. Source/modelที่เลือกจากvalidation ≠ runnable current model (binaryต้นฉบับหาย) ≠ external evaluation (ไม่พบผล external corpusในชุดนี้)
- Main TF-IDF fitทุก profiles, valใช้เลือกmodel/calibrator/threshold; strict test462908 ไม่ใช่ main8313; test threshold sweepและ *_diag เป็น post-hoc diagnostic ไม่ใช่ค่าที่เลือกจากvalidation

### 4-parameter GA ไม่ใช่ implementation เดียวกัน
| Implementation | Selection / crossover / mutation / bounds / budget |
|---|---|
| R1 `exp_r1_ga_redecision.py:22–37,100–149` | pop60,gens40,elite12คงเดิม; uniform crossover; child-only Gaussian σ.02,p.30; t_match[.90,.999],t_review[.5,t_match],cp[.5,1],cd[0,cp]. Initialization t_review upper.9/cd.6 แต่ clipอนุญาตโตได้. Callsมีsort/history/final extra ไม่เท่ากับ nominal2400โดยอัตโนมัติ |
| V2/V2R1 `policies.py:12,93–118` | pop60,budget12000; top20% parent pool; ไม่มี crossover; clone parents แล้ว mutateทั้งpopulationรวมelite σ.02,p.30; clip t_review≤.9,cd≤.6. Elitismไม่ใช่คงgenomeเดิม;200 evaluated populationsระบุในV2R1 protocol |
| B1/B2 Sobol `policies.py:53–90` | deterministic scramble=False; B1 two dimensions t_reviewถึง.999 ต่างจาก B2/B3ถึง.90. B2/B3 four-gene bounds/objectiveเหมือนกัน แต่ B1→B2ไม่strictly nested |
| Evidence guard `run_feature_aware_ga_pipeline.py:467–534` | four thresholdsอีกimplementation: t_match[.50,.999],t_review[.05,t_match]; availability-gated name/group evidence; inherited CRM costs artifact-specific ไม่สมมติR1 defaults |

### 10-gene GA และ weighted review-band ต้องแยกกัน
- `run_feature_aware_ga_pipeline.py:34–43,294–464` one-stage genome = `[t_match,t_review,w_probability,w_name,w_bio,w_url,w_location,w_social,w_image,w_style]`; weighted availability score `sum(w*s*m)/sum(w*m)` แล้วใช้สอง thresholds; ไม่ใช่เพิ่ม10featuresให้GB หรือ optimize model weights
- One-stage normalize nonnegativeweights และมีactive masks/coverage gates; เมื่อdenominator=0จะคงREVIEW ไม่ใช่fallback probability (`302–339`); แม้probabilitymask=1แต่weightอาจเป็น0. Exportที่เรียก41featuresขาด4columnsจากdeclaredschema: domain_count_a/domain_count_b/hashtag_count_a/hashtag_count_b; sourceMODEL_FEATURESมี37จริง จึงห้ามอ้างว่าExcel01มี41rawfeatureครบจากชื่อworkbook. child uniform crossover, σ.025สำหรับthreshold/σ.05สำหรับweight,p.30; config population/generations/eliteต้องตามprotocolแต่ละrun. Guard-weighted policyเก่าคือ4cutoffs+groupweights ใช้ weighted evidenceเฉพาะreviewband จึงไม่ใช่ one-stage10gene
- Sampled one_stage_v1 /gated /20260914 /all8 /full sampled /full2M มี seed/comparator/splitผลแยกกัน. Full2Mมีsocial absentและเก็บ6group evidence+availability/probability ไม่ได้มี41rawfeaturesครบต่อcandidate; workbook01bต้องอ่านexact tierแยก
- Full2M reported all one-stage: candidate positives25931,TP20095,FP183,recall.774941,F1.869744,U4045.6. Auditเก่ารายงานการเติมmisses3312เป็นworkflow recall.687173,F1.811575,U7357.6; ที่นี่ไม่คำนวณใหม่และไม่ยกค่าcorrectedมาแทนreported row. all/projectionรวมdevelopment ไม่ใช่unseen test

### ICSEC V2 vs V2R1 และ reviewer replay
- แยก3seeds×5methodsต่อpackage: GB17_B0, GB18 B0 fixed, B1 tuned simple Sobol, B2 expanded Sobol, B3 expanded GA. GB17/18ใช้corrected lexical features; MiniLMเพิ่มหนึ่งfeature. GB300/.05/depth6, TRAIN negative3:1, CALIBRATION isotonic และPOLICY_VALIDATION policy searchแยกrole
- V2คือpre-integrity-repair; V2R1ซ่อมsealed-label materialization guardและpre-label prediction freeze โดยไม่เปลี่ยนscientificconfiguration. Protocol/hashclaimsไม่แทนpair-key checksของauditปัจจุบัน
- V2/V2R1 frozen recall=TP/(TP+FN)ตัดpositiveREVIEWออก; R-series/10geneใช้TP/allpositivesต่างกัน. Reviewer revisionเพิ่มautomaticrecall/F1และChow; metrics_per_seedเก็บแยกderived historical rows
- workbook03 S*_VAL_REPLAY /S*_B2_REPLAY /S*_B3_REPLAY เป็นretrospective validation-only replay ไม่ใช่original optimizer call log; selectedpoliciesจริงอยู่V2R1 policies.json. ไม่มี optimizer seed ใหม่หรือ reselection ใน matrix

## Workbook availability และ cells ที่ตรวจจริง
คำสั่งมอบหมายกล่าวถึงห้า workbooks แต่ directoryปัจจุบันมี **7 workbooks** ที่ไม่ใช่Excel lock file: ตรวจทั้งหมดเพื่อไม่ตก05/06และ01b. อ่านXML `00_READ_ME` ทุกcellและheadersของทุกsheet;ไม่อ่านแถวprofileจริงลงเอกสารนี้. Hashเป็นbytesปัจจุบัน ไม่ใช่proofว่าexportถูกต้องทุกแถว. Tableด้านล่างแสดงmanifestcellsจริง โดยsheet partsเป็นการแบ่งExcel limitไม่ใช่experimentเพิ่ม

| Workbook / manifest cells | Sheet prefix | Source จริง | rows / columns / parts (reported workbook cells) |
|---|---|---|---|
| `thesis_rebuild/experiment_excel/01_multimodal_and_GA.xlsx#00_READ_ME!A7:E7` | MULTI41_GA_INPUT | `artifacts/decisioning/feature_aware_ga/automated_20260831_sealed/decisioning_features.parquet` | 58696 / 55 / 1 |
| `thesis_rebuild/experiment_excel/01_multimodal_and_GA.xlsx#00_READ_ME!A8:E8` | R1_VALIDATION_TRACE | `experiments/walkthroughs/r1_ga_redecision/data/r1_ga_validation_chromosome_detail.csv` | 21617 / 40 / 1 |
| `thesis_rebuild/experiment_excel/01_multimodal_and_GA.xlsx#00_READ_ME!A9:E9` | R1_GA_INPUT | `experiments/walkthroughs/r1_ga_redecision/data/r1_ga_run_input.csv` | 9097 / 7 / 1 |
| `thesis_rebuild/experiment_excel/01_multimodal_and_GA.xlsx#00_READ_ME!A10:E10` | R1_TRANSITIONS | `experiments/walkthroughs/r1_ga_redecision/data/r1_ga_transition_summary.csv` | 13 / 7 / 1 |
| `thesis_rebuild/experiment_excel/01_multimodal_and_GA.xlsx#00_READ_ME!A11:E11` | R1_CHANGED_EXAMPLES | `experiments/walkthroughs/r1_ga_redecision/data/r1_ga_changed_examples.csv` | 6 / 41 / 1 |
| `thesis_rebuild/experiment_excel/01_multimodal_and_GA.xlsx#00_READ_ME!A12:E12` | GA10_FULL_DECISIONS | `artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/full_2m_pair_decisions.parquet` | 2086245 / 18 / 2 |
| `thesis_rebuild/experiment_excel/01b_GA_full_feature_to_decision.xlsx#00_READ_ME!A7:E7` | EXACT_TIER | `artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/full_2m_pair_decisions.parquet [0:12403]` | 12403 / 18 / 1 |
| `thesis_rebuild/experiment_excel/01b_GA_full_feature_to_decision.xlsx#00_READ_ME!A8:E8` | GA_INPUT_OUTPUT | `artifacts/decisioning/feature_aware_ga/full_2m/feature_chunks + artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/full_2m_pair_decisions.parquet` | 2073842 / 38 / 2 |
| `thesis_rebuild/experiment_excel/02_ICSEC_model_inputs.xlsx#00_READ_ME!A7:E7` | MODEL_FEATURES | `experiments/icsec_final/authoritative_run_v2/features/gb17.parquet + bert_cos.parquet` | 2073842 / 20 / 2 |
| `thesis_rebuild/experiment_excel/02_ICSEC_model_inputs.xlsx#00_READ_ME!A8:E8` | PROFILES_ROW_ID | `data_for_project/normalized_profiles_with_profile_id.csv` | 36807 / 21 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A7:E7` | S101_DEV_LABELS | `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_101/development_labels/labels.parquet` | 548490 / 3 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A8:E8` | S101_TEST_LABELS | `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_101/sealed_test_labels/labels.parquet` | 193692 / 2 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A9:E9` | S101_ROUTING | `experiments/icsec_final/authoritative_run_v2/routing/outer_101/model_scored.parquet` | 729821 / 5 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A10:E10` | S101_BLOCK_MISS | `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_101/blocking_misses/positive_pairs.parquet` | 3312 / 2 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A11:E11` | S101_VAL_REPLAY | `experiments/icsec_final/reviewer_revision/outer_101/validation_replay_input.parquet` | 26152 / 4 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A12:E12` | S101_B2_REPLAY | `experiments/icsec_final/reviewer_revision/outer_101/B2_anytime.csv` | 12000 / 7 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A13:E13` | S101_B3_REPLAY | `experiments/icsec_final/reviewer_revision/outer_101/B3_anytime.csv` | 12000 / 7 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A14:E14` | S101_FROZEN_PRED | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/sealed_predictions/predictions.parquet` | 950305 / 4 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A15:E15` | S101_B0_TEST | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B0_workflow.parquet` | 194726 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A16:E16` | S101_B1_TEST | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B1_workflow.parquet` | 194726 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A17:E17` | S101_B2_TEST | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B2_workflow.parquet` | 194726 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A18:E18` | S101_B3_TEST | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/B3_workflow.parquet` | 194726 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A19:E19` | S101_GB17_B0_TEST | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/decisions/GB17_B0_workflow.parquet` | 194726 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A20:E20` | S202_DEV_LABELS | `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_202/development_labels/labels.parquet` | 565651 / 3 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A21:E21` | S202_TEST_LABELS | `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_202/sealed_test_labels/labels.parquet` | 197531 / 2 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A22:E22` | S202_ROUTING | `experiments/icsec_final/authoritative_run_v2/routing/outer_202/model_scored.parquet` | 750820 / 5 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A23:E23` | S202_BLOCK_MISS | `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_202/blocking_misses/positive_pairs.parquet` | 3312 / 2 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A24:E24` | S202_VAL_REPLAY | `experiments/icsec_final/reviewer_revision/outer_202/validation_replay_input.parquet` | 23164 / 4 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A25:E25` | S202_B2_REPLAY | `experiments/icsec_final/reviewer_revision/outer_202/B2_anytime.csv` | 12000 / 7 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A26:E26` | S202_B3_REPLAY | `experiments/icsec_final/reviewer_revision/outer_202/B3_anytime.csv` | 12000 / 7 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A27:E27` | S202_FROZEN_PRED | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/sealed_predictions/predictions.parquet` | 969255 / 4 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A28:E28` | S202_B0_TEST | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B0_workflow.parquet` | 198545 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A29:E29` | S202_B1_TEST | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B1_workflow.parquet` | 198545 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A30:E30` | S202_B2_TEST | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B2_workflow.parquet` | 198545 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A31:E31` | S202_B3_TEST | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/B3_workflow.parquet` | 198545 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A32:E32` | S202_GB17_B0_TEST | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/decisions/GB17_B0_workflow.parquet` | 198545 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A33:E33` | S303_DEV_LABELS | `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_303/development_labels/labels.parquet` | 538735 / 3 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A34:E34` | S303_TEST_LABELS | `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_303/sealed_test_labels/labels.parquet` | 203731 / 2 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A35:E35` | S303_ROUTING | `experiments/icsec_final/authoritative_run_v2/routing/outer_303/model_scored.parquet` | 730103 / 5 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A36:E36` | S303_BLOCK_MISS | `experiments/icsec_final/authoritative_run_v2/scientific_inputs/outer_303/blocking_misses/positive_pairs.parquet` | 3312 / 2 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A37:E37` | S303_VAL_REPLAY | `experiments/icsec_final/reviewer_revision/outer_303/validation_replay_input.parquet` | 24825 / 4 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A38:E38` | S303_B2_REPLAY | `experiments/icsec_final/reviewer_revision/outer_303/B2_anytime.csv` | 12000 / 7 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A39:E39` | S303_B3_REPLAY | `experiments/icsec_final/reviewer_revision/outer_303/B3_anytime.csv` | 12000 / 7 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A40:E40` | S303_FROZEN_PRED | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/sealed_predictions/predictions.parquet` | 1000015 / 4 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A41:E41` | S303_B0_TEST | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B0_workflow.parquet` | 204738 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A42:E42` | S303_B1_TEST | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B1_workflow.parquet` | 204738 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A43:E43` | S303_B2_TEST | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B2_workflow.parquet` | 204738 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A44:E44` | S303_B3_TEST | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/B3_workflow.parquet` | 204738 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A45:E45` | S303_GB17_B0_TEST | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/decisions/GB17_B0_workflow.parquet` | 204738 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A46:E46` | POLICY_PARAMETERS | `V2R1 scientific_outputs/outer_*/policies.json` | 12 / 7 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A47:E47` | REV_SELECTED_VECTORS | `experiments/icsec_final/reviewer_revision/selected_vectors.csv` | 12 / 6 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A48:E48` | REV_ANYTIME_CHECKS | `experiments/icsec_final/reviewer_revision/anytime_checkpoints.csv` | 48 / 9 / 1 |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx#00_READ_ME!A49:E49` | REV_METRICS | `experiments/icsec_final/reviewer_revision/metrics_per_seed.csv` | 18 / 17 / 1 |
| `thesis_rebuild/experiment_excel/04_source_artifact_catalog.xlsx#00_READ_ME!A7:E7` | FLOW | `Manual path map verified against local artifacts` | 14 / 4 / 1 |
| `thesis_rebuild/experiment_excel/04_source_artifact_catalog.xlsx#00_READ_ME!A8:E8` | FILES | `data/, data_for_project/, train_data/, artifacts/, experiments/` | 807 / 6 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A7:E7` | R0_R5_SUMMARY | `experiments/r0_r5_summary_tidy.csv` | 24 / 11 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A8:E8` | R0_R3_MATRIX | `experiments/automation/r0_r3_report_20260809/r0_r3_experimental_matrix.csv` | 4 / 16 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A9:E9` | R2_PROB | `experiments/r2_probabilities.parquet` | 2073842 / 3 / 2 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A10:E10` | R6_PROB | `experiments/r6_bert_er/r6_probabilities.parquet` | 2073842 / 3 / 2 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A11:E11` | R6_NEW_CANDIDATES | `experiments/r6_bert_er/new_candidate_pairs.parquet` | 2006 / 2 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A12:E12` | RUN01_GENERATIONS | `experiments/automation/r1_20260808_200954/generations.csv` | 200 / 10 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A13:E13` | RUN01_TRIALS | `experiments/automation/r1_20260808_200954/trials.csv` | 5 / 18 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A14:E14` | RUN02_GENERATIONS | `experiments/automation/r1_nested_primary_20260809/generations.csv` | 200 / 10 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A15:E15` | RUN02_TRIALS | `experiments/automation/r1_nested_primary_20260809/trials.csv` | 5 / 18 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A16:E16` | RUN03_GENERATIONS | `experiments/automation/r3_model_seed123_20260809/generations.csv` | 200 / 10 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A17:E17` | RUN03_TRIALS | `experiments/automation/r3_model_seed123_20260809/trials.csv` | 5 / 18 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A18:E18` | RUN03_TRAINING | `experiments/automation/r3_model_seed123_20260809/training_history.csv` | 30 / 6 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A19:E19` | RUN03_R2_PROB | `experiments/automation/r3_model_seed123_20260809/r2_probabilities.parquet` | 2073842 / 3 / 2 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A20:E20` | RUN04_GENERATIONS | `experiments/automation/r3_model_seed7_20260809/generations.csv` | 200 / 10 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A21:E21` | RUN04_TRIALS | `experiments/automation/r3_model_seed7_20260809/trials.csv` | 5 / 18 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A22:E22` | RUN04_TRAINING | `experiments/automation/r3_model_seed7_20260809/training_history.csv` | 30 / 6 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A23:E23` | RUN04_R2_PROB | `experiments/automation/r3_model_seed7_20260809/r2_probabilities.parquet` | 2073842 / 3 / 2 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A24:E24` | RUN05_GENERATIONS | `experiments/automation/r3_primary_20260809/generations.csv` | 200 / 10 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A25:E25` | RUN05_TRIALS | `experiments/automation/r3_primary_20260809/trials.csv` | 5 / 18 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A26:E26` | RUN05_TRAINING | `experiments/automation/r3_primary_20260809/training_history.csv` | 30 / 6 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A27:E27` | RUN05_R2_PROB | `experiments/automation/r3_primary_20260809/r2_probabilities.parquet` | 2073842 / 3 / 2 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A28:E28` | RUN06_GENERATIONS | `experiments/automation/r3_sensitivity_fn2_20260809/generations.csv` | 200 / 10 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A29:E29` | RUN06_TRIALS | `experiments/automation/r3_sensitivity_fn2_20260809/trials.csv` | 5 / 18 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A30:E30` | RUN07_GENERATIONS | `experiments/automation/r3_sensitivity_fp10_20260809/generations.csv` | 200 / 10 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A31:E31` | RUN07_TRIALS | `experiments/automation/r3_sensitivity_fp10_20260809/trials.csv` | 5 / 18 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A32:E32` | RUN09_GENERATIONS | `experiments/automation/r3_smoke_v2/generations.csv` | 5 / 10 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A33:E33` | RUN09_TRIALS | `experiments/automation/r3_smoke_v2/trials.csv` | 1 / 18 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A34:E34` | RUN09_TRAINING | `experiments/automation/r3_smoke_v2/training_history.csv` | 5 / 6 / 1 |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx#00_READ_ME!A35:E35` | RUN09_R2_PROB | `experiments/automation/r3_smoke_v2/r2_probabilities.parquet` | 2073842 / 3 / 2 |
| `thesis_rebuild/experiment_excel/06_GA_search_parameters.xlsx#00_READ_ME!A7:E7` | GA10_VALID_TRIALS | `artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/full_2m_validation_trials.csv` | 9 / 10 / 1 |
| `thesis_rebuild/experiment_excel/06_GA_search_parameters.xlsx#00_READ_ME!A8:E8` | GA10_SPLIT_METRICS | `artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/full_2m_metrics_by_split.csv` | 16 / 16 / 1 |
| `thesis_rebuild/experiment_excel/06_GA_search_parameters.xlsx#00_READ_ME!A9:E9` | GA10_COVERAGE | `artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/full_2m_feature_coverage.csv` | 8 / 5 / 1 |
| `thesis_rebuild/experiment_excel/06_GA_search_parameters.xlsx#00_READ_ME!A10:E10` | GBT01_TRIALS | `experiments/automation/gb_transformer_primary_20260809/trials.csv` | 5 / 17 / 1 |
| `thesis_rebuild/experiment_excel/06_GA_search_parameters.xlsx#00_READ_ME!A11:E11` | GBT01_GENERATIONS | `experiments/automation/gb_transformer_primary_20260809/ga_generations.csv` | 200 / 9 / 1 |
| `thesis_rebuild/experiment_excel/06_GA_search_parameters.xlsx#00_READ_ME!A12:E12` | GBT02_TRIALS | `experiments/automation/gb_transformer_repro_20260809/trials.csv` | 5 / 17 / 1 |
| `thesis_rebuild/experiment_excel/06_GA_search_parameters.xlsx#00_READ_ME!A13:E13` | GBT02_GENERATIONS | `experiments/automation/gb_transformer_repro_20260809/ga_generations.csv` | 200 / 9 / 1 |
| `thesis_rebuild/experiment_excel/06_GA_search_parameters.xlsx#00_READ_ME!A14:E14` | GBT04_TRIALS | `experiments/automation/gb_transformer_smoke_v2_20260809/trials.csv` | 5 / 17 / 1 |
| `thesis_rebuild/experiment_excel/06_GA_search_parameters.xlsx#00_READ_ME!A15:E15` | GBT04_GENERATIONS | `experiments/automation/gb_transformer_smoke_v2_20260809/ga_generations.csv` | 10 / 9 / 1 |
| `thesis_rebuild/experiment_excel/06_GA_search_parameters.xlsx#00_READ_ME!A16:E16` | GA10_GENERATIONS | `artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/full_2m_generation_history.json` | 117 / 9 / 1 |
| `thesis_rebuild/experiment_excel/06_GA_search_parameters.xlsx#00_READ_ME!A17:E17` | GA_JSON_FACTS | `artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/full_2m_frozen_policies_before_test.json + artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914/full_2m_result.json + artifacts/decisioning/feature_aware_ga/automated_20260831_sealed/weighted_ga_history.json + artifacts/decisioning/feature_aware_ga/automated_20260831_sealed/selector_generation_history.json` | 651 / 3 / 1 |

Builder `thesis_rebuild/build_experiment_excels.py:122–173` ใช้ slicesใน01bแต่assertคู่IDsทั้งสองฝั่งและlabels; `177–202` assertGB/BERT keysก่อนappend. เหล่านี้เป็นsourcecode checks ไม่ใช่การexecutebuilderใหม่หรือcertifyexportปัจจุบันโดยmatrixนี้. Catalog04เป็นinventory/pathmap ไม่ใช่result reproduction. V2R1 workbookเก็บsealedlabelsหลังfinalevaluationแล้ว ห้ามใช้testเลือกpolicyใหม่หรือเผยแพร่PII

## Compact result matrix (primary historical rows)
ตารางเต็มและทุกรายmodel/tuning/threshold/seedอยู่CSV/JSON; compactตัดsweepsเพื่อให้อ่านง่าย ไม่ใช้เป็นจำนวนการทดลองอิสระ

| ID | Family / variant | ผลที่เก็บไว้ | Source exact locator |
|---|---|---|---|
| E0698 | R-series: R0_production:test | TP=5864; FP=88; FN=1689; REVIEW=8783; precision=0.9852; recall=0.6683; F1=0.7964; cost=2304.7 | `experiments/r1_results.json#/rules/test/R0_production` |
| E0699 | R-series: manual_stage18:test | TP=6866; FP=632; FN=1701; REVIEW=6876; precision=0.9157; recall=0.7825; F1=0.8439; cost=4998.5 | `experiments/r1_results.json#/rules/test/manual_stage18` |
| E0700 | R-series: R1_ga:test | TP=6231; FP=23; FN=1885; REVIEW=3116; precision=0.9963; recall=0.7101; F1=0.8292; cost=2062.3 | `experiments/r1_results.json#/rules/test/R1_ga` |
| E0701 | R-series: R0_production:full | TP=19624; FP=925; FN=5558; REVIEW=86296; precision=0.955; recall=0.671; F1=0.7882; cost=11908.9 | `experiments/r1_results.json#/rules/full/R0_production` |
| E0702 | R-series: manual_stage18:full | TP=22959; FP=6763; FN=5604; REVIEW=73007; precision=0.7725; recall=0.785; F1=0.7787; cost=40879.1 | `experiments/r1_results.json#/rules/full/manual_stage18` |
| E0703 | R-series: R1_ga:full | TP=20855; FP=234; FN=6284; REVIEW=28438; precision=0.9889; recall=0.7131; F1=0.8286; cost=8022.8 | `experiments/r1_results.json#/rules/full/R1_ga` |
| E0704 | R-series: R3_ga:test | TP=6347; FP=38; FN=1873; REVIEW=640; precision=0.994; recall=0.7233; F1=0.8373 | `experiments/r3_results.json#/rules/test/R3_ga` |
| E0705 | R-series: R3_ga:full | TP=21274; FP=465; FN=6179; REVIEW=2751; precision=0.9786; recall=0.7274; F1=0.8345 | `experiments/r3_results.json#/rules/full/R3_ga` |
| E0706 | R-series: R2_manual:test | TP=5157; FP=19; FN=2523; REVIEW=1115; precision=0.9963; recall=0.5877; F1=0.7393 | `experiments/r2_results.json#/splits/test` |
| E0707 | R-series: R2_manual:full | TP=17275; FP=110; FN=8286; REVIEW=3897; precision=0.9937; recall=0.5907; F1=0.7409 | `experiments/r2_results.json#/splits/full` |
| E0708 | R-series: R4_manual:L2000:test | TP=5158; FP=14; FN=2858; REVIEW=766; precision=0.9973; recall=0.5878; F1=0.7397 | `experiments/r4_privacy_tradeoff.json#/per_L/2000/R4_manual/test` |
| E0709 | R-series: R4_manual:L2000:full | TP=17243; FP=96; FN=9492; REVIEW=2623; precision=0.9945; recall=0.5896; F1=0.7403 | `experiments/r4_privacy_tradeoff.json#/per_L/2000/R4_manual/full` |
| E0710 | R-series: R5_ga:L2000:test | TP=6303; FP=57; FN=1823; REVIEW=700; precision=0.991; recall=0.7183; F1=0.8329 | `experiments/r4_privacy_tradeoff.json#/per_L/2000/R5_ga/test` |
| E0711 | R-series: R5_ga:L2000:full | TP=21135; FP=648; FN=6020; REVIEW=2759; precision=0.9703; recall=0.7226; F1=0.8283 | `experiments/r4_privacy_tradeoff.json#/per_L/2000/R5_ga/full` |
| E0712 | R-series: R4_manual:L1000:test | TP=5085; FP=14; FN=2931; REVIEW=766; precision=0.9973; recall=0.5795; F1=0.733 | `experiments/r4_privacy_tradeoff.json#/per_L/1000/R4_manual/test` |
| E0713 | R-series: R4_manual:L1000:full | TP=16979; FP=88; FN=9752; REVIEW=2621; precision=0.9948; recall=0.5805; F1=0.7332 | `experiments/r4_privacy_tradeoff.json#/per_L/1000/R4_manual/full` |
| E0714 | R-series: R5_ga:L1000:test | TP=6288; FP=57; FN=1820; REVIEW=721; precision=0.991; recall=0.7166; F1=0.8317 | `experiments/r4_privacy_tradeoff.json#/per_L/1000/R5_ga/test` |
| E0715 | R-series: R5_ga:L1000:full | TP=21087; FP=647; FN=6014; REVIEW=2816; precision=0.9702; recall=0.721; F1=0.8272 | `experiments/r4_privacy_tradeoff.json#/per_L/1000/R5_ga/full` |
| E0716 | R-series: R4_manual:L500:test | TP=4991; FP=14; FN=2453; REVIEW=1354; precision=0.9972; recall=0.5688; F1=0.7244 | `experiments/r4_privacy_tradeoff.json#/per_L/500/R4_manual/test` |
| E0717 | R-series: R4_manual:L500:full | TP=16660; FP=85; FN=8167; REVIEW=4726; precision=0.9949; recall=0.5696; F1=0.7245 | `experiments/r4_privacy_tradeoff.json#/per_L/500/R4_manual/full` |
| E0718 | R-series: R5_ga:L500:test | TP=6277; FP=57; FN=1818; REVIEW=738; precision=0.991; recall=0.7153; F1=0.8309 | `experiments/r4_privacy_tradeoff.json#/per_L/500/R5_ga/test` |
| E0719 | R-series: R5_ga:L500:full | TP=21058; FP=647; FN=6010; REVIEW=2855; precision=0.9702; recall=0.72; F1=0.8266 | `experiments/r4_privacy_tradeoff.json#/per_L/500/R5_ga/full` |
| E0720 | R-series: R4_manual:L250:test | TP=5001; FP=14; FN=2760; REVIEW=1026; precision=0.9972; recall=0.5699; F1=0.7253 | `experiments/r4_privacy_tradeoff.json#/per_L/250/R4_manual/test` |
| E0721 | R-series: R4_manual:L250:full | TP=16710; FP=84; FN=9171; REVIEW=3528; precision=0.995; recall=0.5713; F1=0.7259 | `experiments/r4_privacy_tradeoff.json#/per_L/250/R4_manual/full` |
| E0722 | R-series: R5_ga:L250:test | TP=6276; FP=57; FN=1881; REVIEW=674; precision=0.991; recall=0.7152; F1=0.8308 | `experiments/r4_privacy_tradeoff.json#/per_L/250/R5_ga/test` |
| E0723 | R-series: R5_ga:L250:full | TP=21059; FP=643; FN=6206; REVIEW=2538; precision=0.9704; recall=0.72; F1=0.8267 | `experiments/r4_privacy_tradeoff.json#/per_L/250/R5_ga/full` |
| E0724 | R-series: R6_manual:test | TP=3817; FP=19; FN=4749; REVIEW=224; precision=0.995; recall=0.435; F1=0.6053 | `experiments/r6_results.json#/splits/test` |
| E0725 | R-series: R6_manual:full | TP=12610; FP=144; FN=15958; REVIEW=799; precision=0.9887; recall=0.4312; F1=0.6005 | `experiments/r6_results.json#/splits/full` |
| E0726 | R-series: R6_GA:test | TP=5620; FP=13; FN=2266; REVIEW=3712; precision=0.9977; recall=0.6405; F1=0.7801 | `experiments/r6_results.json#/ga_rules/test` |
| E0727 | R-series: R6_GA:full | TP=20064; FP=94; FN=5529; REVIEW=31219; precision=0.9953; recall=0.686; F1=0.8122 | `experiments/r6_results.json#/ga_rules/full` |
| E0796 | ICSEC-V2: outer101:B0 | TP=5873; FP=32; FN=2454; REVIEW=502; precision=0.9945808636748518; recall=0.705296024978984; F1=0.8253232152894885; U=2568.2 | `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/summary.json#/B0` |
| E0797 | ICSEC-V2: outer101:B1 | TP=6897; FP=112; FN=1567; REVIEW=659; precision=0.984020545013554; recall=0.8148629489603024; F1=0.8914883991469009; U=1856.9 | `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/summary.json#/B1` |
| E0798 | ICSEC-V2: outer101:B2 | TP=6649; FP=83; FN=1575; REVIEW=914; precision=0.98767082590612; recall=0.8084873540856031; F1=0.8891414816795935; U=1832.4 | `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/summary.json#/B2` |
| E0799 | ICSEC-V2: outer101:B3 | TP=6646; FP=83; FN=1567; REVIEW=939; precision=0.9876653291722396; recall=0.8092049190308048; F1=0.8895730156605541; U=1826.9 | `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/summary.json#/B3` |
| E0800 | ICSEC-V2: outer101:GB17_B0 | TP=5583; FP=65; FN=2377; REVIEW=884; precision=0.9884915014164306; recall=0.7013819095477387; F1=0.8205467372134039; U=2595.4 | `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/summary.json#/GB17_B0` |
| E0801 | ICSEC-V2: outer202:B0 | TP=6641; FP=145; FN=2089; REVIEW=4; precision=0.9786324786324786; recall=0.7607101947308132; F1=0.8560195926785253; U=2379.4 | `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/summary.json#/B0` |
| E0802 | ICSEC-V2: outer202:B1 | TP=6649; FP=147; FN=1523; REVIEW=968; precision=0.9783696291936433; recall=0.8136319138521781; F1=0.8884286477819346; U=1913.8 | `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/summary.json#/B1` |
| E0803 | ICSEC-V2: outer202:B2 | TP=6584; FP=116; FN=1523; REVIEW=1062; precision=0.9826865671641791; recall=0.8121376588133712; F1=0.8893091105558183; U=1861.2 | `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/summary.json#/B2` |
| E0804 | ICSEC-V2: outer202:B3 | TP=6584; FP=116; FN=1523; REVIEW=1062; precision=0.9826865671641791; recall=0.8121376588133712; F1=0.8893091105558183; U=1861.2 | `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/summary.json#/B3` |
| E0805 | ICSEC-V2: outer202:GB17_B0 | TP=6487; FP=87; FN=2060; REVIEW=215; precision=0.9867660480681473; recall=0.758979758979759; F1=0.8580120362409894; U=2255.5 | `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/summary.json#/GB17_B0` |
| E0806 | ICSEC-V2: outer303:B0 | TP=6982; FP=87; FN=1971; REVIEW=0; precision=0.9876927429622294; recall=0.7798503294984921; F1=0.871551616527275; U=2145.0 | `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/summary.json#/B0` |
| E0807 | ICSEC-V2: outer303:B1 | TP=6983; FP=87; FN=1583; REVIEW=660; precision=0.9876944837340877; recall=0.8151996264300724; F1=0.8931951905858275; U=1823.0 | `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/summary.json#/B1` |
| E0808 | ICSEC-V2: outer303:B2 | TP=7049; FP=124; FN=1583; REVIEW=555; precision=0.9827129513453228; recall=0.8166126042632067; F1=0.8919962037329959; U=1886.5 | `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/summary.json#/B2` |
| E0809 | ICSEC-V2: outer303:B3 | TP=7049; FP=124; FN=1583; REVIEW=556; precision=0.9827129513453228; recall=0.8166126042632067; F1=0.8919962037329959; U=1886.6 | `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/summary.json#/B3` |
| E0810 | ICSEC-V2: outer303:GB17_B0 | TP=6978; FP=115; FN=1975; REVIEW=0; precision=0.983786832087974; recall=0.7794035518820507; F1=0.8697494702729651; U=2205.0 | `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/summary.json#/GB17_B0` |
| E0811 | ICSEC-V2R1: outer101:B0 | TP=5873; FP=32; FN=2454; REVIEW=502; precision=0.9945808636748518; recall=0.705296024978984; F1=0.8253232152894885; U=2568.2 | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/summary.json#/B0` |
| E0812 | ICSEC-V2R1: outer101:B1 | TP=6897; FP=112; FN=1567; REVIEW=659; precision=0.984020545013554; recall=0.8148629489603024; F1=0.8914883991469009; U=1856.9 | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/summary.json#/B1` |
| E0813 | ICSEC-V2R1: outer101:B2 | TP=6649; FP=83; FN=1575; REVIEW=914; precision=0.98767082590612; recall=0.8084873540856031; F1=0.8891414816795935; U=1832.4 | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/summary.json#/B2` |
| E0814 | ICSEC-V2R1: outer101:B3 | TP=6646; FP=83; FN=1567; REVIEW=939; precision=0.9876653291722396; recall=0.8092049190308048; F1=0.8895730156605541; U=1826.9 | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/summary.json#/B3` |
| E0815 | ICSEC-V2R1: outer101:GB17_B0 | TP=5583; FP=65; FN=2377; REVIEW=884; precision=0.9884915014164306; recall=0.7013819095477387; F1=0.8205467372134039; U=2595.4 | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/summary.json#/GB17_B0` |
| E0816 | ICSEC-V2R1: outer202:B0 | TP=6641; FP=145; FN=2089; REVIEW=4; precision=0.9786324786324786; recall=0.7607101947308132; F1=0.8560195926785253; U=2379.4 | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/summary.json#/B0` |
| E0817 | ICSEC-V2R1: outer202:B1 | TP=6649; FP=147; FN=1523; REVIEW=968; precision=0.9783696291936433; recall=0.8136319138521781; F1=0.8884286477819346; U=1913.8 | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/summary.json#/B1` |
| E0818 | ICSEC-V2R1: outer202:B2 | TP=6584; FP=116; FN=1523; REVIEW=1062; precision=0.9826865671641791; recall=0.8121376588133712; F1=0.8893091105558183; U=1861.2 | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/summary.json#/B2` |
| E0819 | ICSEC-V2R1: outer202:B3 | TP=6584; FP=116; FN=1523; REVIEW=1062; precision=0.9826865671641791; recall=0.8121376588133712; F1=0.8893091105558183; U=1861.2 | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/summary.json#/B3` |
| E0820 | ICSEC-V2R1: outer202:GB17_B0 | TP=6487; FP=87; FN=2060; REVIEW=215; precision=0.9867660480681473; recall=0.758979758979759; F1=0.8580120362409894; U=2255.5 | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/summary.json#/GB17_B0` |
| E0821 | ICSEC-V2R1: outer303:B0 | TP=6982; FP=87; FN=1971; REVIEW=0; precision=0.9876927429622294; recall=0.7798503294984921; F1=0.871551616527275; U=2145.0 | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/summary.json#/B0` |
| E0822 | ICSEC-V2R1: outer303:B1 | TP=6983; FP=87; FN=1583; REVIEW=660; precision=0.9876944837340877; recall=0.8151996264300724; F1=0.8931951905858275; U=1823.0 | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/summary.json#/B1` |
| E0823 | ICSEC-V2R1: outer303:B2 | TP=7049; FP=124; FN=1583; REVIEW=555; precision=0.9827129513453228; recall=0.8166126042632067; F1=0.8919962037329959; U=1886.5 | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/summary.json#/B2` |
| E0824 | ICSEC-V2R1: outer303:B3 | TP=7049; FP=124; FN=1583; REVIEW=556; precision=0.9827129513453228; recall=0.8166126042632067; F1=0.8919962037329959; U=1886.6 | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/summary.json#/B3` |
| E0825 | ICSEC-V2R1: outer303:GB17_B0 | TP=6978; FP=115; FN=1975; REVIEW=0; precision=0.983786832087974; recall=0.7794035518820507; F1=0.8697494702729651; U=2205.0 | `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/summary.json#/GB17_B0` |

## Source/hash citations และสิ่งที่ยังไม่พิสูจน์
Source pathsทุกแถวพร้อม SHA-256เต็มอยู่`experiment_lineage.json.source_artifacts`และ`experiments[].source_artifacts`; CSVคงJSONในfieldซ้อน. Workbook hashและcell contentพร้อมheadersอยู่`workbooks[]`. ตัวเลขแถวCSVนับheaderเป็นrow1; JSONใช้exactpointer; ไม่มีแถวrawPIIถูกcopyลงmatrix

| Source / implementation | SHA-256 |
|---|---|
| `thesis_rebuild/experiment_excel/01_multimodal_and_GA.xlsx` | `1e97b640b782a821a5af191a85440cffcfea092a44a10374242e9a4662ef27e6` |
| `thesis_rebuild/experiment_excel/01b_GA_full_feature_to_decision.xlsx` | `2d562423dcdbc9775c6d929804ce4144df216db012e123b0595abfe2c586c3d0` |
| `thesis_rebuild/experiment_excel/02_ICSEC_model_inputs.xlsx` | `8287937a3abe81098213f363b4bf60e958adbbef88e422dcde4795bfe029f15d` |
| `thesis_rebuild/experiment_excel/03_ICSEC_V2R1_GA.xlsx` | `89f54396959f1485924bcf75e1c84629b1be58cd8be2a6e420d99865f72e65b2` |
| `thesis_rebuild/experiment_excel/04_source_artifact_catalog.xlsx` | `3c886f98f230d440647d7048144296ab8732f4e88876d9b5b9b345b538bdfce9` |
| `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx` | `bbce30f0a1d0fbbb9ce84c7b953be5567da09f29d973756d27046f6afc736df2` |
| `thesis_rebuild/experiment_excel/06_GA_search_parameters.xlsx` | `02a20a2628386678eb50804b6d5d2547a4bd216ac836cd41028349e912cfb4f0` |
| `experiments/code/exp_r1_ga_redecision.py` | `b6dc3eede40e33e8fea65ef4ea49d5ac3f05c0ab7a6d6ad1fae8ef36c14b8c23` |
| `experiments/code/exp_lib.py` | `984adb9cf584210f5c2cbbae15062346388211df4812f0f32f91dcfd0f661db4` |
| `experiments/code/exp_r2_bert_feature.py` | `98da5cb8b2d976bb021f03a593b64f9ca0b36451656fc3c6b2c262ebfef9d698` |
| `experiments/code/exp_r4_bloom_privacy.py` | `91a0a93b4b343b885debb42c0c25ea8b68d2a4d701998e6b2502c8153db3c5b4` |
| `experiments/code/exp_r6_bert_er.py` | `c061400c45640bbbd1d9a5c3cc9cadbe342cab81419999066be0e0a8d05c7a64` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_101/summary.json` | `c6c23600adbe05f6946ccbd6f13fa9cdf1d39185f91dec65d327325b1de8a66d` |
| `experiments/icsec_final/authoritative_run_v2/policies.py` | `951b16ccab46b33f40f7b796ccb268b1630f8f9e0aa71bf44c8965998b8fb50b` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_202/summary.json` | `a98317339252d0da152a181bf31530762d4766402b347ef78b8d8d2cd902fa19` |
| `experiments/icsec_final/authoritative_run_v2/scientific_outputs/outer_303/summary.json` | `e6fd5c1ad4bc103745a3bc1350bba73904cd5fcbdcacf8dd2176a93975298fb6` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/summary.json` | `c6c23600adbe05f6946ccbd6f13fa9cdf1d39185f91dec65d327325b1de8a66d` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_202/summary.json` | `a98317339252d0da152a181bf31530762d4766402b347ef78b8d8d2cd902fa19` |
| `experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_303/summary.json` | `e6fd5c1ad4bc103745a3bc1350bba73904cd5fcbdcacf8dd2176a93975298fb6` |
| `thesis_rebuild/build_experiment_excels.py` | `59159635c2909cfc29eaa6cda3ae103d14a9a96725aa8ce82a618f4f03b763f0` |
| `pub_multi/build_pkg.py` | `07fae0bcf05f392e01fda363e6d33bf4b7629888a518ea7d37a36a80e697108c` |
| `src/identity_resolution/stages/train_multimodal.py` | `613ee8238b5eb2b991192ee1c9c586cd8a6e3ea4c53f0fff11c38939d5b70b05` |
| `src/identity_resolution/stages/train_base.py` | `23a61e740674cbb0454e5477d7804e2d96ddfe0740f961c7a8cf84a4ff824c17` |
| `pub_multi/bench_models.py` | `f39c2c824534da4747e5dda9d44eb8853842854dd8634d8892dcd5b3cb08ddb0` |
| `pub_multi/tune_top_models.py` | `b8494da5f4e0593bea31677d4557326812c1f6a1a9a0ccc23f7f5bc5e79a3d05` |
| `pub_multi/bench_classical_leaksafe.py` | `826d2c6d57fcad7b63df7d3c51559ad9a143fcef7ec4e2261b11143fee15be50` |
| `pub_multi/bench_strict_models.py` | `a69f03ec4682ecce0aa1e3cd2c0370c5f38168c1679175e8418267fe953e34d0` |
| `pub_multi/strict_calibration_compare.py` | `1259f90f611e483ad4c550929c9cf6c3bf17b9048dfb68cbc4c8f8e97a7e1591` |
| `experiments/code/run_feature_aware_ga_pipeline.py` | `15af5a3907609f4e45c9dcbf2345bda95ac985f29ccc8db2b014bf938053ac5d` |
| `experiments/code/run_one_stage_weighted_ga_experiment.py` | `5b5c9c124d1c112fc3ac42bc7055ecb82890740d61069ac8c03d473d7d3ffbbf` |
| `experiments/code/run_full_2m_one_stage_ga.py` | `231faf12686b37a45a2bfc04d572d5f80c4e05b59eab7c25b59ccd3153a97ab4` |
| `experiments/icsec_final/authoritative_run_v2/final_runner.py` | `61bf80f161172177b124ceece4ceb6c2930c76617d0a371d656deb86eab46b37` |
| `experiments/icsec_final/authoritative_run_v2/features.py` | `9975f02ff9086c96e68823d8c02d153bc44adc966973a2b066f175cc907250e0` |
| `experiments/icsec_final/authoritative_run_v2r1/final_runner_r1.py` | `f529e4b5a711021f3dd9beeafb834c7e9237cbd217ac02da12feb4cf3336ec03` |
| `experiments/icsec_final/authoritative_run_v2r1/PROTOCOL_V2R1.md` | `0c60bbd98a53740497a79b43f9aeb1988246c5c8ccdc740f2ba1f4653f2e056f` |
| `experiments/icsec_final/authoritative_run_v2/features/gb17.parquet` | `960fe07b6e46abae8502d4bc8fae6dd8a0589f5bb61d7faea9ae07534f85a057` |
| `experiments/icsec_final/authoritative_run_v2/features/bert_cos.parquet` | `9c5693483020ae2a9937d979474df30ec5156e4b20632ad8a6e9866393947297` |

### Gate ก่อนเรียกผล compatible/reproduced
ตรวจcanonicalunorderedpairkeys,duplicate keys,labelsและทั้งสองentityroles,exact/scored/missedscopeและdenominators,featureorderและpreprocessing/model/calibratorhashes,policyboundary/operators,costschedule,selection/testaccessprovenance. การมี2073842แถวทั้งสองไฟล์ไม่ทำให้rowiเป็นคู่เดียวกัน;hashตรงพิสูจน์bytesไม่เปลี่ยน ไม่ได้พิสูจน์split/provenanceถูกต้อง

### ข้อจำกัดของ reconstruction
- ใช้snapshotและartifactsที่มี ไม่กู้rawJSON/checkpointsที่หายและไม่ฝึกใหม่. Historical metricsยังเป็นreported-onlyแม้previousauditกล่าวว่าตรง;งานcompanionคำนวณV2R1ต่อแถวเป็นหลักฐานคนละlayer
- Workbook00_READ_MEcountsเป็นreportedexportinventory; sourceParquetfootercount/schemaและhashอ่านจริงสำหรับpathsในJSON. ไม่ยืนยันallcell-to-sourceequalityของmillionrows
- Variantที่มีแต่validationleaderboardไม่มีtestpredictionแยกรุ่นถูกคงไว้เป็นvalidationclaim ไม่สร้างtestmetricsให้เติมช่องว่าง. AbsoluteWindows pathsในreportคงเป็นhistoricalidentifiers ไม่อ้างว่าlocalfileเหล่านั้นมีอยู่
- No external corpus/generalization claim; no guaranteeofprivacy/datausagepermission. WorkbookมีPII/testlabelsห้ามเผยแพร่โดยไม่ตรวจgovernance
