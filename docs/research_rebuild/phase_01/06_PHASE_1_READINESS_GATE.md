# Phase 1 Acceptance Gate — ทำความเข้าใจได้ แต่ยังไม่อนุมัติ Phase 2

## คำตัดสิน

**PHASE 1 OVERALL: PARTIAL. PHASE 2 SCIENTIFIC EXECUTION: BLOCKED.**

จัดทำ reconstruction ของ source/artifacts ที่มีอยู่และ independent metric reanalysis แล้ว แต่ไม่ประกาศว่า raw-to-result reproduction, historical feature reproducibility ทุกสาย หรือสิทธิข้อมูลผ่านครบ ไม่มี training/optimization หรือการเริ่ม Phase 2 ในงานนี้

สถานะ: PASS = ตรวจ criterion ใน scope ที่ระบุสำเร็จ; PARTIAL = พิสูจน์ได้บางสาย/บางชั้น; BLOCKED = ขาดหรือขัดกันจนทำ claim/งานที่ระบุไม่ได้; NOT VERIFIED = ยังไม่มี executable/documentary evidence ยืนยัน ไม่ใช้ PASS แทนคำว่าไฟล์มีอยู่

## Gate matrix

| หัวข้อ | สถานะ | สิ่งที่ตรวจได้ | ช่องว่าง/เงื่อนไข | ผลต่อ Phase 2 |
|---|---|---|---|---|
| Dataset integrity | PARTIAL | numeric snapshot 36,807 rows; profile_row_id unique; eligible 36,804 rows หลัง exclude missing entity/numeric IDs 3; inventories/hash/schema ได้ | legacy string IDs ambiguous และ workbook image cells 406 mismatches; snapshot contract ใหม่ยังไม่ได้ freeze | ต้องเลือก numeric snapshot และรับรอง exclusions ก่อน run; ไม่ใช้ ambiguous legacy IDs |
| Data lineage | PARTIAL | workbook/source inventory; combined→blocking row-alignment checks; feature/cache artifacts trace ตาม paths | raw JSON ไม่พร้อม; cleaned24,729 เป็นอีก population; historical value transforms หลายตัว reproduce ไม่ตรง | raw-to-result BLOCKED; snapshot reanalysis ทำได้แบบมีเงื่อนไข |
| Ground-truth mapping | PARTIAL | eligible user_folder↔numeric entity mapping one-to-one; 15,297 known groups; no mapping conflict | historical ground_truth_pairs CSV มี directed pairs 6 คู่ที่ไม่ตรง index entities และ index/current merged folder mismatches 3; NPZ หาย | ห้ามใช้ GT เก่าโดยไม่ reconcile; ล็อก labels จาก selected numeric snapshot ใหม่ |
| Pair population accounting | PASS เฉพาะ canonical current population | exact12,403 + scored2,073,842 =2,086,245; positive25,931+miss3,312=29,243; same-platform4 แยกแล้ว; canonical keys ตรง persisted artifacts | legacy873,956 string-key candidatesมี unresolved3,306; ไม่รับรอง numbered R variants มี paired key sets เท่ากัน | reuse แนวทางได้แต่ต้องสร้าง role-local accounting ตาม protocol ใหม่ |
| Feature reproducibility | PARTIAL รวม history; PASS เฉพาะ corrected V2-17 replay | corrected V2 ทั้ง17features replayจากsourceบน2,073,842pairsตรงทุกvalue; MiniLMcosineตรงexistingembeddingsภายใต้tolerance; definitionsแยกnotebook/reconstructed/corrected | historical transformationsหลายตัว FAIL, notebook TF-IDF subset replayไม่ใช่ full fit provenance; hidden score gate; encoder revision lineageยังต้องล็อก | corrected label-free schema, train-only learned preprocessing และ cachesใหม่ต้องผ่าน preflight |
| Experiment lineage | PARTIAL | 1,077 lineage records แยก family/variant/config/seed/scope; source/hash/workbook cells | หลาย records reported-only; production checkpointต้นฉบับไม่พร้อม; old cache independenceไม่รับรอง | ใช้ historyอธิบายได้ แต่ไม่ใช้เป็น controlled authoritative tableใหม่ |
| Historical metric consistency | PASS เฉพาะ audited granular families; PARTIAL รวมทุก history |221 metric records; V2/V2R1/reviewer/full2M row recomputation;142 checks;76 comparisonsไม่มี disagreementในนิยามเดิม | R/multimodal summary-only; conditional≠automatic; candidate≠workflow; cost scenariosต่าง | ต้องล็อก evaluatorใหม่; numerical PASS ไม่ใช่ scientific design PASS |
| Leakage risks | BLOCKED สำหรับ reuse historical pipelines เป็น unseen experiment | sourceระบุ splitฝั่งa, score gate, full-profile TF-IDF, reusedval; V2R1 lifecyclerepairมี protocol | ยังไม่ verified runnerใหม่ทั้งสองปลาย/train-only fit/sealed evaluation; same corpusสำรวจแล้ว | แก้/ทดสอบ contractsก่อน controlled run; historical limitationอธิบายแยก |
| Reproducibility | PARTIAL | read-only audit scriptsทำงานจริง; input/source hashesและ machine-readable outputs | raw-to-resultและproduction inferenceต้นฉบับไม่ครบ; runnerใหม่ยังไม่ได้ implement/verifyในPhase1 | snapshot-based new runnerต้องผ่าน fail-closed preflightก่อน seedจริง |
| Data governance limitations | NOT VERIFIED | repository governanceระบุข้อจำกัดชัด; audit outputsใช้aggregates/hash/schemaไม่ปล่อยrawpairs | reuse rights,consent,ToS,IRB,redistributionไม่ยืนยัน | block publicdata release/approval claims; internal scientific runรอเจ้าของยืนยันกรอบสิทธิ |

Sources ของทุกจำนวน: `dataset_inventory.json`, `dataset_candidate_accounting.json`, `dataset_audit_outputs.json`, `dataset_reconciliation_outputs.json`, `experiment_lineage.json`, `verified_metrics.json` (source SHA-256 และ metric/source mapping ภายใน) สำหรับ workflow contracts: `docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:18–48,67–88,122–180` และ governance: `experiments/icsec_final/authoritative_run_v2/DATA_GOVERNANCE.md:3–14` ดูรายละเอียดราย claim ใน reports 01/02/04/05 ไม่อ่านตารางนี้แทนหลักฐาน

## จุดที่ต้องยกระดับก่อน Phase 2 กับข้อจำกัดที่ไม่ต้องกู้ทั้งหมด

### Blockers สำหรับ scientific execution ใหม่

1. ผู้วิจัยเลือก input authority ให้ชัด: `normalized_profiles_with_profile_id.csv` เป็น candidate snapshot ไม่ใช่ raw; รับรอง mapping, exclusions3rows, repeated platforms และ labels source แยกจาก ground_truth_matrix indexเก่า [dataset_candidate_accounting.json]
2. Freeze versioned protocol: ที่อ้างอิงอยู่เป็น **ข้อเสนอ** และมี A–I implementation sequence ไม่ใช่ named experimental arms A–F ต้องระบุว่าคำว่า A–F หมายถึง stage A ถึง F หรือต้องการ armsหกชุดใหม่ ห้าม auditนี้ตั้งชื่อ/อนุมัติแทนผู้วิจัย [docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:3,166–178]
3. กำหนด cohort/splitก่อนทำscorer: entityทั้งสองปลายroleเดียว, count cross-role drops, train-only preprocessing, calibration/policy/testrolesตามpopulationเดียวกัน [protocol:31–48]
4. Freeze corrected feature/order/cache/model contracts รวมencoderrevision,text composition,IDindex; ห้ามนำ oldscore-gated namefeatureมาเป็นcleanablation [protocol:67–88; experiments/code/exp_lib.py:93–101]
5. Implementและทดสอบ evaluator: TP+FN+R+=allpositives,exact+scored candidates,covered+missed=allpositives,reviewclasscounts,scope,costparameters [protocol:122–141,180]
6. Repair run isolation/wrapperrestore/chunkmanifestและrejectduplicates/mismatchedhashesก่อนreuse [src/identity_resolution/stages/train_multimodal.py:350–365; src/identity_resolution/workflows/full_candidate.py:188–192]
7. Lock policy ladder/bounds/ties/budget/internalseedsและcomparisoncriterionบนdevelopmentก่อนดูtest; random/Sobol/GAclassเดียวกัน [protocol:90–120]
8. ยืนยันกรอบใช้ข้อมูล/ethicsและ explicit authorizationก่อน scientific seeds ห้ามอ้าง externalgeneralizationจากsplitใหม่บนcorpusเดิม [DATA_GOVERNANCE.md; protocol:48]

งาน 1–8 เป็น next safe actions ที่ยังไม่ได้ทำใน Phase 1 นี้ ต้องแยก implementation/preflight จาก scientific execution และต้องมีคำอนุมัติเริ่มPhase2ใหม่ ไม่รันpilotหรือtrainingโดยอ่านรายงานนี้ว่าเป็นapproval

### Historical limitations ที่บันทึกไว้ได้โดยไม่จำเป็นต้องกู้ก่อน snapshot reanalysis

- Raw missing: blockคำอ้าง raw reproduction แต่ไม่ block normalizedsnapshot reanalysisที่นิยามสิทธิ/lineageชัด
- Oldproductionmodel missing: block rerun/inferenceต้นฉบับ แต่ไม่ต้องสร้าง binaryปลอมก่อน trainใหม่ในrun isolatedที่อนุมัติแล้ว
- Legacy workbook/image/feature mismatches: block exacthistoricalreproduction; ไม่จำเป็นต้องแก้historicalfilesเพื่อใช้ numeric snapshotและnewdeterministicfeatures
- Summary-only R/multimodal results: ใช้developmenthistoryอย่างระบุstatus ไม่เพิ่มความแน่นอนด้วยการเดาdecisionrows
- n=3/oldbootstrap/prior shift: เป็นข้อจำกัดผลเก่า ไม่ต้องreoptimizeผลเก่าเพื่อเริ่มdesignใหม่
- Noexternalcorpus: ไม่blockretrospectiveanalysis แต่blockexternalgeneralizationclaim

## Readiness ต่อ A–F ที่ผู้ใช้กล่าวถึง

อ้างอิง literal stage labelsในprotocolเดิมโดยไม่ตีความเป็น sixexperimentalmethods:

| Stage | วัตถุประสงค์เดิม | ReadinessจากPhase1 |
|---|---|---|
| A | input snapshot +field/ID/labelaudit | PARTIAL:มีauditแต่snapshot/exclusions/labelsauthorityยังไม่freeze |
| B | split+evaluator+minimalfixtures | NOT VERIFIEDสำหรับ implementationใหม่; historicalV2R1ไม่แทน testsใหม่ |
| C | runisolation/cache/preprocessingrepair | BLOCKEDสำหรับ reuse current risky paths; Phase1ไม่แก้runtime |
| D | developmentpilot | BLOCKEDรอA–C/protocol/authorization; ไม่ได้รัน |
| E | retrievalRQ1 | BLOCKEDรอprotocol/implementation; ไม่มีnewretrievalresult |
| F | scorer/calibrationRQ2 | BLOCKEDรอstagesก่อนหน้า; ไม่มีtraining/calibrationใหม่ |

Source: `docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:166–180`. หากA–Fหมายถึงอีกexperimentdefinitionซึ่งไม่ได้อยู่ในreferencesที่ตรวจ ต้องส่ง/ล็อกdefinitionนั้นก่อนแทนmappingนี้

## ข้อสรุปที่ยอมให้ใช้ตอนนี้

- อธิบาย researchdevelopment และ policy trade-offโดยรักษาfamily/scope
- ใช้ independently recomputed historicalmetrics ของ audited granularfamiliesเป็นประวัติ ไม่เรียก newcontrolledexperiment
- ไม่สรุป GA overallwinner: B3 meanUต่ำสุดเล็กน้อยในV2R1 frozen group; automaticF1เฉลี่ย B1สูงกว่า; full2M U10geneต่ำสุดแต่F1legacyguardสูงกว่า [04_RESULT_COMPARISON_TH.md]
- ไม่ประกาศ Phase1 PASSครบ หรือ Phase2 SAFE TO RUN จนblockersและNOT VERIFIEDที่เกี่ยวกับscopeใหม่ได้รับหลักฐาน
