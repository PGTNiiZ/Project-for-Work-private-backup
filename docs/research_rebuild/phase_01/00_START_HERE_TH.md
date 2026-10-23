# เริ่มอ่าน Phase 1 Research Reconstruction ที่นี่

## สถานะ

**Phase 1: PARTIAL — reconstruction package พร้อมอ่าน แต่ยังมี evidence gaps. Phase 2: BLOCKED / NOT STARTED.** ไม่ใช่ผล training หรือ optimization รอบใหม่ งานนี้ตรวจ source, workbooks และ persisted artifacts แบบ read-only แล้วเขียนเฉพาะ isolated audit deliverables ใน directory นี้ ดู acceptance criteria ที่ `06_PHASE_1_READINESS_GATE.md`

## อ่านตามลำดับ WHY → WHAT → HOW → RESULT

1. `03_MODEL_AND_GA_EXPLANATION_TH.md` — เรียนปัญหา/profile/entity/pairs/features/model/calibration/GA/metricsด้วยภาษาไทย มีตัวอย่างประกอบที่ไม่ใช่บุคคลจริง
2. `01_DATASET_AND_FEATURE_LINEAGE.md` — dataset counts/IDs/labels/transformations,21normalizedcolumns,17featuresแต่ละสาย,MiniLMfeature18และmultimodalfeatures
3. `02_HISTORICAL_EXPERIMENT_MATRIX.md` — experimentlineage; อย่าเรียกทุกGAว่าimplementationเดียวหรือเอาF1คนละprotocolมาแข่ง
4. `04_RESULT_COMPARISON_TH.md` — independenthistoricalmetricrecomputation,winnersที่มีscopeและเปรียบconditional/automatic
5. `05_DATA_AND_EXPERIMENT_LIMITATIONS.md` — missingraw,feature/exportmismatches,leakage,prior/governanceและข้อจำกัดinterpretation
6. `06_PHASE_1_READINESS_GATE.md` — PASS/PARTIAL/BLOCKED/NOT VERIFIEDและสิ่งต้องทำก่อนPhase2

## งานวิจัยทำอะไรจริง

มีหลายdevelopmentfamilies: notebook17-feature neuralpairmodel; supervisedmultimodaltext/image/contextclassifier; R0–R6 representation/decision/privacy/retrieval; ICSECV2/V2R1 correctedGB17/18พร้อมfourparameterpolicies; feature-aware/one-stage10geneGAอีกสาย ไม่ใช่หนึ่งcontrolledstudyที่เปลี่ยนแต่optimizer [02_HISTORICAL_EXPERIMENT_MATRIX.md; experiment_lineage.json]

Numeric snapshotมี36,807profiles; eligibilityของcanonicalfullcandidateเหลือ36,804เพราะ3rowsไม่มีnumericentity/groundtruthfolder ต่างจากcleaned/imagepopulation24,729 ซึ่งไม่ควรเล่าว่าเป็นการcleanแล้วเพิ่มแถวกลับมาโดยไม่มีlineage [dataset_inventory.json; dataset_candidate_accounting.json; 01_DATASET_AND_FEATURE_LINEAGE.md]

Canonicalcandidateaccountingตรวจได้2,086,245pairs=12,403exact+2,073,842scored; cross-platformpositiveuniverse29,243 มีcandidatecovered25,931และmiss3,312 ส่วนall-platformpositive29,247รวมsame-platform4คู่ ต้องรักษาตัวส่วน [dataset_candidate_accounting.json]

## Workbook availability

พบทุกไฟล์ที่ขอ ไม่ใช้Exceltemporarylockfiles:

- `thesis_rebuild/experiment_excel/01_multimodal_and_GA.xlsx`
- `thesis_rebuild/experiment_excel/01b_GA_full_feature_to_decision.xlsx`
- `thesis_rebuild/experiment_excel/02_ICSEC_model_inputs.xlsx`
- `thesis_rebuild/experiment_excel/04_source_artifact_catalog.xlsx`
- `thesis_rebuild/experiment_excel/05_R0_R6_experiment_history.xlsx`
- `thesis_rebuild/07_dataset_raw_to_features.xlsx`

เพิ่มเติมmatrixauditอ่าน`03_ICSEC_V2R1_GA.xlsx`และ`06_GA_search_parameters.xlsx`ที่มีอยู่ด้วย [experiment_lineage.json.workbooks; 02_HISTORICAL_EXPERIMENT_MATRIX.md:55–156]

Workbook inspectionไม่ใช่executionbuilder/recalculation: manifestcells/header/fullsheetcount/hashตรวจแยกจากsemanticvaluechecksที่มีsourceartifacts ไม่ปล่อยrawprofile/pairrowsในpackageนี้ [extract_workbooks.py; dataset_workbook07_evidence.json; dataset_reconciliation_outputs.json] รายการhashของหกไฟล์และsheetinventoryอยู่`workbook_inventory.csv`/`workbook_evidence.json`

## ผลดีที่สุดต้องถามว่าดีที่สุดตามอะไร

- Multimodalเดิม: image_contextเป็นreportedvalidation/compositeleader; image_statsมีreportedtestF1สูงกว่านิดเดียว ไม่ใช่เหตุให้เลือกใหม่จากtest
- NumberedR0–R6: R3reportedtestF1=.8373; manual_stage18control=.8439แต่FPมากกว่า จึงห้ามกล่าวR3ชนะทุกcontrol/ทุกmetric ผลกลุ่มนี้ยังreported-only
- V2R1/reviewerfrozengroup: B3meanU=1858.23ต่ำสุด; B1meanautomaticF1=.866722สูงสุด; B3−B2Uต่อseedคือ−5.5,0,+.1 ไม่รองรับGAoverallwinner
- Full2M10gene: lowestUในfrozengroup แต่legacynameguardautomaticF1สูงกว่า; one-stageautomaticworkflowrecall=.687173,F1=.811575,U=7357.6หลังรวมmisses ไม่ใช่candidateF1=.869744 และไม่ใช่newheld-outgeneralization

ทุกจำนวนข้างต้นมาจาก`04_RESULT_COMPARISON_TH.md`/`verified_metrics.json`ซึ่งเก็บsourcepath/hash/scope ไม่เทียบตัวเลขระหว่างbulletsเป็นleaderboardเดียว

## Machine-readable evidence

| ไฟล์ | ใช้ทำอะไร |
|---|---|
| dataset_inventory.csv/json | artifactavailability/hash/schema/count/IDquality |
| transformation_verification.csv | transformationchecksและPASS/FAIL/UNPROVEN/NOT_EXECUTED |
| dataset_audit_outputs.json | legacylabels/endpointmappingและfeaturechecks |
| dataset_reconciliation_outputs.json | storedblocking/cleaned/workbookimagemismatches |
| dataset_candidate_accounting.json | numericmapping/candidatekeys/GTscope/MiniLMreplay |
| experiment_lineage.csv/json |1,077lineagerecordsรวมconfigs/sweeps ไม่ใช่1,077independentexperiments |
| verified_metrics.csv/json |221metricrecords; includesreported-onlyrecordsที่ติดstatusชัด |
| workbook_inventory.csv/workbook_evidence.json | workbookhash,metadata/header,sheetcounts |
| illustrative_metrics.json | ตัวอย่างสูตรสมมติ ไม่ใช่researchresults |
| verification.json | ตรวจpackage/counts/sources/hashesโดยparentaudit |
| SHA256SUMS.json | finaldeliverablemanifest ไม่hashตัวmanifestเอง |

Statusอยู่ในแต่ละrecord: sourceimplementation/summaryreported/per-rowrecomputedเป็นคนละชั้น ไม่เลื่อนreported-onlyเป็นverifiedเพราะsummaryดูสมเหตุผล

## ทำอะไรต่ออย่างปลอดภัย

ก่อนPhase2: (1)รับรองnumeric snapshot/exclusions/labels authority (2)freezeversionedprotocolและความหมายA–F (3)สร้างsplit/evaluator/preprocessing/cachecontractsและtestsใหม่ (4)ล็อกcandidatepopulation,feature/encoderrevision,calibration/policy/objective/budgets/ties (5)ยืนยันdatagovernanceและอนุมัติexecution แล้วจึงทำdevelopmentpilotในrunใหม่ ห้ามแก้frozenhistoryให้ดูผ่าน [06_PHASE_1_READINESS_GATE.md; docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:18–48,166–193]

ReferenceprotocolเดิมมีA–Iimplementationsequence; Phase1mappingA–FจึงหมายถึงstagesAถึงFอย่างมีเงื่อนไข ไม่ได้inventexperimentalarmshกชุด และไม่ได้อนุมัติขั้นD/E/Fให้รัน

## Safety boundary

ไม่มีclassifiertraining/fine-tuning,GAoptimization,newembeddingdownload,originaldatasetedit,frozenresultoverwrite,commit/merge/push หรือPhase2. มีdeterministicpreprocessing/TF-IDFrule replayเพื่อaudit transformationจากexistinginputเท่านั้น ไม่ใช่learnedscorerexperiment [dataset_audit_outputs.json.privacy; read-onlyaudit scripts]

Workbook/rawrowsและpair-levelPIIคงอยู่ต้นทาง ไม่copyมาdeliverables สิทธิreuse/consent/IRB/redistributionยังNOT VERIFIED [experiments/icsec_final/authoritative_run_v2/DATA_GOVERNANCE.md]
