# Plan Impact from Thesis — ข้อเสนอเท่านั้น

NO-GO. ไม่มีการแก้ไฟล์ใน design/ รอบนี้. จำนวนตามแผน v2:21 distinct ESSENTIAL experiments,217 classifier training jobs และ19 final test evaluations เป็น planning counts ไม่ใช่งานที่ดำเนินการแล้ว. รอบนี้ training/GA/inference/scientific evaluation ที่รันใหม่=0. [V2R:FINAL_HANDOFF_TH.md#Q7] [V2R:FINAL_HANDOFF_TH.md#ส่วนที่ 4]

## เหตุผลก่อนข้อเสนอ

Thesisครอบคลุมdata preparation,notebookMLP,classicalmodels,multimodal suite,calibration,thresholdingและCRM exportsจริง ไม่ใช่แค่R0–R6. MainGB41-featureมีsavedtestAP0.978927924122322/F10.9340136843325989ในmain_report ตรงthesisเมื่อปัด4หลัก. สิ่งนี้เพิ่มhistorical evidenceให้H1–H3 แต่ไม่แทนการทดลองV2เพราะpairset,splits,featuresและpriorsไม่เหมือนกัน และไม่มีfreshholdout. [MAIN@1e0a2db:pub_multi/ref/main_report.json#L1-L81 metrics] [V2R:HISTORICAL_EXPERIMENT_AUDIT.md#F06]

## ข้อเสนอและผลต่อcounts

| Proposal | IDs / stage ที่กระทบ | Evidence / เหตุผล | Reuse/priority ที่เสนอ | MVP count impact |
|---|---|---|---|---|
| PI-01 Hold executionทั้งหมดจนG0/G1ผ่านและTC-01/02/03มีdisposition | D0-1,D0-4,G0,G1,G2;E3-2,E5-3,E5-5และtrainingทั้งหมด | TC-01activeSyntheticclaimขัดsource;TC-02HITLไม่มีledgerแม้paragraphถูกขีดฆ่า;TC-03summarymalformedและcanonicalpositivecountต่างกันมาก | BLOCKED;217jobsรวมtuningfitsห้ามเริ่ม;documentauditทำได้ | 21/217/19ไม่เปลี่ยน;executionholdไม่ใช่ตัดexperiment |
| PI-02 Labelcontractversionedและrejectmissingidentityก่อนpairbuilding | D0-1,D0-2,D0-4,G0/G2,E1-1,E2-1 | canonicaleligible15,297groups,max4,29,243positives;oldnomalizedมี14,251missingและกลุ่มnonmissing84;ไม่ยืนยัน4.06Mtraininglineage | REIMPLEMENTvalidationguard;แยกconfirmedpositive/confirmednegative/unlabeled;ไม่ยกuser_folderเป็นpersontruthโดยอัตโนมัติ | ΔESSENTIAL=0;ไม่สร้างdiagnosticIDใหม่เพื่อให้countพอง |
| PI-03 แยกT9เป็นEXCLUDEสำหรับcurrentcorpusimage-to-imageclaim;กลับเข้าได้เฉพาะnewpairedimages+rights | E9-1/GX-T9/S2representation | TC-07:alllocalimagesมาจากTwitter,testboth-image0,coverage11.5%<เดิม50%condition;captions5.9% | EXCLUDE(currentdata);CONDITIONALสำหรับnewdataพร้อมpairedimagecoverage/biometricapproval;availability/caption-to-textอาจเป็นsupportingrepresentationtestแต่ไม่เรียกimage-to-image | MVPΔ=0/0/0เพราะE9-1อยู่นอกMVP;ถ้ารับข้อเสนอตัดadvancedE9-1ออกจะลด1variant/25trainingjobsจากแผนALL669เป็น644;ยังไม่แก้matrix |
| PI-04 LeadScoringเป็นdownstreamapplicationไม่ใช่proofscope | CRM/T10applicationdiscussion;ไม่เพิ่มE-ID | TC-11:heuristic0.4/0.3/0.3+outputtiersจริง;ไม่มีconversion/outcomelabelsที่พบ | REFERENCE_ONLYสำหรับimplementation;EXCLUDEจากpredictivebusinessperformanceclaims | ΔMVP=0;ไม่มีlead-scoringtrainingjobที่ควรนับเพิ่ม |
| PI-05 บังคับpopulation/lineagecolumnsทุกtable | E7-1,E7-2,E7-4,E7-6;T1–T6ทั้งหมด | candidate-sampleAP.9789≠fullcandidateAP.6017≠productionP.9550≠R3e2eF1.8373;TC-08 | REUSE_AFTER_VERIFICATIONevaluatorconcept;REIMPLEMENTscopeassertions | countsเดิม;19finalevaluationsต้องpredeclareทั้งconfigurationและpopulation |
| PI-06 ปรับcalibrationdesignให้แยกfit/selection/reportingและpriorcompatibility | E6-7,E6-2,E6-3,E6-4,E6-5 | thesisECEvalidation.0000เป็นin-sample;threshold.35selectedval;naturalcandidatepriorต่างsampletest;[V2R:METHODOLOGICAL_RISKS.md#R-10] | REIMPLEMENTfold-safe/OOFcalibrationตามV2;ไม่reusesuitecalibratorเป็นfinalV2 | ΔMVP=0ในรอบนี้;หากภายหลังเพิ่มcalibrationfold/fitsต้องrecountก่อนG4ไม่ทำเงียบ ๆ |
| PI-07 เลือกconfirmatorystrategyก่อนG4 | G5,E7-1,E7-2,H1–H5 | testreuse≥15ตามV2;ชื่อfreshsplitใหม่ไม่ลบretrospectiveexposure | PROPOSEDoption(c)ตอนนี้;option(a)/(b)เป็นfutureconfirmatoryextensionหลังgate | คง21/217/19เป็นexploratorybudgetหากG0/G1ผ่าน;externalconfirmatorybudgetUNKNOWNจนเลือกdatasetและtransferprotocol |
| PI-08 ย้ายoldnotebook/strictresultsเป็นhistoricalappendix | E2-1,E3-1,E3-2,E4-1,E5-3;historyF05/F06 | Table4.2oldsplittraceableจริง;4.06Mstatsไม่parse;strict462,908testไม่ใช่8,313suitemaintest | REFERENCE_ONLY;RETRAINclassifiersเมื่อgatesผ่าน;ไม่เปลี่ยนbaselineเป็นhistoricalMLPโดยไม่มีเหตุผล | ΔMVP=0;ไม่มีtrainingjobอัตโนมัติเพิ่มเพียงเพราะthesisมีMLP |

ตัวเลขΔเป็นPROPOSED planning reconciliationคำนวณจากv2matrix ไม่ใช่measurement. ยืนยันE9-1มี25plannedjobsใน`design/HYPOTHESIS_EXPERIMENT_MATRIX.csv`;ผลรวมALL669−25=644คำนวณด้วยtool รอบนี้. Count21/217/19ไม่ถูกเปลี่ยนหรือรับรองว่ากำลังexecution. [V2R:TRAINING_DECISION_REPORT.md#จำนวนงาน] [V2R:FINAL_HANDOFF_TH.md#Table 4]

## Thesis-era components → V2 (ห้าขั้นต้องไม่ปน)

| Historical component | Stage / V2 ID | Existing evidence | Reuse decision / training |
|---|---|---|---|
| exact-first +prefix/domainblocking | S1candidate generation;E1-1 | full_reportexact12,403/scored2,073,842;codebuild_exact_match_pairs | REUSE_AFTER_VERIFICATION;ไม่supervisedtrain;อย่าถือexactlabelsเป็นgroundtruthอัตโนมัติ |
| text/attribute22และhybrid23 | S2feature representation;E2-1,E4-1 | leak_safe_report/main/basefeaturecountและsourcewrappers | REUSE_AFTER_VERIFICATIONprimitivefunctions;TF-IDFfitต้องREIMPLEMENTtrain-only;frozenencoderไม่retrainแต่ต้องrevision/hash |
| LR/GB/RF | S3classifier;E3-1,E3-2;RF E3-3optional | classical_leaksafe_cmp.json+source300/.05/6,400/18/leaf2 | RETRAINบนV2split;historicalweightsREFERENCE_ONLY |
| image_stats37 /image_context41 | S2representation;E9-1เฉพาะconditionalextension | main_reportmodalitycoverageและsuite_report | currentimage-to-imageEXCLUDE;caption/textwrappersREUSE_AFTER_VERIFICATIONไม่อ้างเหมือน17/18R-seriesfeatures |
| IdentityMLP/FocalLoss | S3classifier;supportingarchitectureเท่านั้น ไม่สร้างessentialIDใหม่ | notebook/strict_report+v2F05 | REFERENCE_ONLY;ถ้าจำเป็นcomparisonใหม่ต้องpredeclareและRETRAIN;ไม่คัดค่าจาก“3-class”summaryมาใช้ |
| isotoniccalibration | S4decision precondition;E6-7 | main_report+calibrationcode | REUSE_AFTER_VERIFICATIONalgorithm;fitใหม่บนroleที่ถูกต้อง ไม่reusehistoricalcalibrator |
| dualthresholdMATCH/REVIEW/NO_MATCH | S4decisionpolicy;E6-1,E6-2,E6-3,E6-6 | match.98/review.95ในfull_report/crm_report | REPLICATEfixedpolicyเป็นcontrolบนfrozenV2scores;REVIEWไม่ใช่resolvedpositive |
| GAของR1/R3และlaterICSEC | S4decisionpolicy;E6-4vsE6-5 | V2ตรวจval-onlyselectionและequal-budgetSobolในlaterfamilyแล้ว | REUSE_AFTER_VERIFICATIONcode;policyoptimizationไม่ใช่classifiertraining;รอบนี้ไม่รัน |
| connectedcomponentsunification | S5entityresolution;E10-1 | crm_report19,799unifiedprofilesและsourceunionrules | REFERENCE_ONLY;CONDITIONALentityGT;pairPไม่ใช่clusterprecision |
| heuristicLeadScoring | downstreamนอกห้าขั้นproof | build_lead_scoresและcrm_reporttiers | REFERENCE_ONLYimplementation;EXCLUDEoutcomeclaimsจนมีconversionlabels |

Source: [MAIN@1e0a2db:pub_multi/ref/main_report.json#L1-L213 metrics/leakage_report/modality_report]; [MAIN@1e0a2db:pub_multi/ref/crm_report.json#L1-L40]; [MAIN@1e0a2db:train_data/stage15_crm_entity_pipeline/run_crm_entity_pipeline.py#L373-L403 build_lead_scores]; [V2R:HISTORICAL_EXPERIMENT_AUDIT.md#F05]; [V2R:HISTORICAL_EXPERIMENT_AUDIT.md#F06]; [V2R:REUSABLE_COMPONENTS.md#ตาราง component]. ข้อมูลreuseเป็นconditionalไม่ใช่certificationว่าcodeพร้อมproduction.

## ลำดับที่เสนอ

1. จัดdispositionTC-01/02/03และprivacyreleaseโดยเจ้าของ/ที่ปรึกษา;ไม่แก้PDFต้นฉบับ.
2. G0:source-labelconstruction,exactinputhashes,missing/invalididentitypolicyและrunlineage;G1:permission/ethics/PDPA.
3. ตัดสินexploratoryversusconfirmatoryrouteก่อนเปิดdataเพื่อtrainingใหม่.
4. หลังgateผ่านจึงD0→G2→G3→G4;ก่อนหน้านั้นทำเฉพาะเอกสารและsyntheticengineeringตามสิทธิ์.
5. Baseline→ClassicalML→FrozenSemantic→Fusion→DecisionOptimization;G5decision→declaredtestreporting;fine-tuning/newimagesอยู่conditionalextension.

ไม่มีการเพิ่มhypothesisหรือเปลี่ยนdesignfileในรอบนี้. TC findingsเพิ่มเหตุผลของgate ไม่ใช่ใบอนุญาตข้ามgate.
