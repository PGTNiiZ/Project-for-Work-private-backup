# ข้อจำกัดข้อมูลและการทดลอง: อะไรพิสูจน์ได้และอะไรยังไม่ได้

รายงานนี้ไม่แก้ source, datasets, frozen packages หรือ historical results ข้อจำกัดแยกเป็น (1) สิ่งที่ตรวจจาก source/current snapshot (2) สิ่งที่ audit เดิมรายงาน (3) สิ่งที่ยังไม่มีหลักฐาน การมี hash ยืนยัน bytes ไม่เท่ากับรับรองการเก็บข้อมูล, label correctness หรือการเลือกการทดลองโดยไม่เคยดูผล

## 1. Raw provenance และความหมายของ snapshot

Audit เดิมรายงาน raw gitlink `data/data/Dataset-LinkSocial` revision `fe67dd1102d9265fb5c47d0f3d8ff19546294571` ไม่มีเนื้อหาและไม่มี `.gitmodules`; cleaned กับ normalized ไม่ได้มี row-key reconciliation ที่พิสูจน์ chain [docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:100–105] สถานะไฟล์/จำนวนแถว/hash ที่ Phase 1 ตรวจปัจจุบันอยู่ `dataset_inventory.json` และรายละเอียด transformation อยู่รายงาน 01 ไม่ใช้จำนวนแถวเท่ากันเพียงอย่างเดียวพิสูจน์ว่า values และ ordering เหมือนกัน

ผลต่อการเริ่มใหม่: BLOCKED สำหรับการอ้าง raw-to-result reproduction แต่ไม่จำเป็นต้อง block snapshot-based retrospective reanalysis หากล็อก snapshot ที่ผ่าน identity/schema/label integrity และระบุที่มาที่ขาดอย่างตรงไปตรงมา [docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:18–29,48]

## 2. Ground truth เป็น corpus annotation ไม่ใช่ identity verification ภายนอก

Label ใช้ entity grouping ตาม user_folder/numeric mapping ใน derivative ไม่ใช่ตรวจเอกสารจริง การตรวจ mapping consistency ตรวจได้ว่าหนึ่งแถว map อย่างไร แต่พิสูจน์ไม่ได้ว่าผู้เก็บต้นทางจัดคนถูกทุกกรณี Unknown entities ไม่ควรกลายเป็น negative ผ่าน fallback [src/identity_resolution/stages/train_base.py:170–189; experiments/code/exp_lib.py:81–91; docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:20–22]

Same-platform positive ต้องแยกจาก cross-platform positive และ repeated platform ภายใน entity ต้องมีรายงานข้อยกเว้น ไม่ใช้ hard-coded `TOTAL_POS_FULL=29247` ของ legacy เป็น authority สำหรับทุกสาย [experiments/code/exp_lib.py:26; docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:37–44]

## 3. Leakage มีหลายชั้น ไม่ใช่ผ่าน entity overlap แล้วจบ

| ความเสี่ยง | หลักฐาน | ผลต่อการตีความ | สิ่งที่ต้องเปลี่ยนก่อนรอบใหม่ |
|---|---|---|---|
| notebook split ตรวจเพียง entity ฝั่ง a | audit เดิม: docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:36–41; archived Stage10 notebook cell 4 | endpoint b ร่วม train/test ได้; ตัวเลข overlap เป็น replay ของ audit เดิม ไม่ใช่ Phase 1 retrain | split entity ก่อนและ require ทั้งสองปลาย role เดียวกัน |
| legacy cache split หลัง predecessor scoring | experiments/code/exp_lib.py:72–101 | hash val/test ของ policy ไม่รับประกัน scorer ไม่เคยเห็นคน test | scorer/calibration/policy/test ใช้ split manifest เดียวตั้งแต่ต้น |
| TF-IDF fit ทุก profiles | src/identity_resolution/stages/train_base.py:307; audit เดิม:79–84 | transductive preprocessing ไม่ใช่ inductive unseen evaluation | fit TRAIN เท่านั้นและ transform roles อื่น |
| validation reused | audit เดิม:79–84; src/identity_resolution/stages/train_base.py:427 เป็นต้นไป | model selection, isotonic fit, threshold selection ใช้ชุดเดียว; val metrics เป็น in-sample ต่อ calibrator | CALIBRATION กับ POLICY_VALIDATION แยก |
| name_sim gated ด้วย old score | experiments/code/exp_lib.py:28,93–101 | features dependence ต่อ predecessor learned scorer; ไม่ใช่ pure lexical ablation | ใช้ corrected label-free function ทุกแถวใน run ใหม่ |
| v2 sealed-label materialization issue | experiments/icsec_final/authoritative_run_v2r1/PROTOCOL_V2R1.md:22–46 | V2R1 ซ่อม lifecycle; ไม่อนุมาน causal leakage จากชื่อ SEALED_TEST หรือ file access อย่างเดียว | guard actual materialization, freeze predictions ก่อน final label join |

V2R1 มี integrity repairs ตาม protocol ไม่ใช่เหตุให้เอาผล legacy มานับเป็น unseen evidence และ corpus นี้ถูกสำรวจแล้ว การเปลี่ยน seed ไม่ทำให้เป็น external/never-seen corpus [experiments/icsec_final/authoritative_run_v2r1/PROTOCOL_V2R1.md:3–20; docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:46–48]

## 4. Pair population และ metrics ต้องรักษา scope

`EXACT_TIER`, `MODEL_SCORED`, `BLOCKING_MISS`, `WORKFLOW`, sampled test และ full projection เป็นคนละ scope การเรียกไฟล์ test ไม่รับประกัน fit lineage; full projection อาจรวม development rows ห้ามรวมผลหรือเพิ่ม constants โดยไม่มี key/population proof [docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:23–32,43–55]

Frozen V2 `_metrics` ใช้ positive NO_MATCH เป็น FN และตัด positive REVIEW ออกจาก recall/F1 denominator; R-series `evaluate` ใช้ total_pos จึงต่างนิยามแม้ชื่อ F1 เหมือนกัน [experiments/icsec_final/authoritative_run_v2/final_runner.py:52–62; experiments/code/exp_lib.py:130–140] Independent tables ในรายงาน 04 แสดง conditional กับ automatic แยกกัน การที่ U ลดเพราะ REVIEW เพิ่มไม่ใช่ measured successful human matching

ตัวเลข historical summary ที่ไม่มี row-level decisions/pair labels ให้คำนวณซ้ำต้องติดป้าย REPORTED_ONLY ไม่สร้างแถวหรือ labels ขึ้นใหม่เพื่อเติมหลักฐาน

## 5. Joins และ Excel ไม่ใช่ scientific authority ด้วยตัวเอง

Workbook ถูกอ่านแบบ OOXML read-only; metadata cells, headers, sheet row counts และ hashes อยู่ `workbook_evidence.json` ไม่มีการ recalculate Excel formulas เพราะจะต้องเขียน workbook และไม่มีสูตร cache ที่คำนวณเองแล้วให้เป็น evidence การมี copied metric สองแห่งตรงกันไม่ใช่ independent reproduction [extract_workbooks.py; experimental evidence methodology ใน docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:9–21]

ไม่ join records ด้วย row position ใน Phase 1 หาก workbook เอาค่า probability/feature ไปประกบจาก position ต้องจัดเป็น export-lineage limitation จนกว่าจะพิสูจน์ canonical pair identities/ordering ได้ Column naming, numeric ID และ profile_id แบบ string ต้องตรวจตาม artifact

Workbook extraction ไม่ปล่อย raw profiles/pair rows ออกเป็น deliverables ใช้เฉพาะ metadata/header/counts; sheet เล็กเก็บ metadata ต้องผ่าน PII/export scan ก่อนปิด package

## 6. Source ปัจจุบันไม่ใช่หลักฐาน source ณ historical fit

Source ปัจจุบันของ multimodal ใช้ shared module และแทน `base.make_profile_bundle`/`base.compute_features`; default loop รันหลาย variants ไม่มี restore ใน `run_experiment` [src/identity_resolution/stages/train_multimodal.py:350–365,414–424] Audit เดิมมี fixture ยืนยัน feature wrappers ซ้อน แต่ไม่ได้แปลว่าทุก historical artifact ถูกสร้างด้วย source นี้ [docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:86–91]

Chunk loader glob ทุก `candidate_scores_*.parquet` และ concat โดยไม่มี current-run manifest [src/identity_resolution/workflows/full_candidate.py:188–192] จึงต้อง reject stale/duplicate/mismatched-model caches ก่อน reuse ไม่เรียก cache existence ว่า reproducible run

Production path `image_context_r075_h20_s42` เป็น config identity ไม่ใช่ proof checkpoint พร้อมโหลด [src/identity_resolution/settings.py:29–34; src/identity_resolution/workflows/full_candidate.py:174–185] ตาราง inventory และ report 02 แยก selection winner, configured inference model และ artifact availability

## 7. Calibration prior และ GA attribution

Role cohort sizes ต่างกันทำให้อัตราบวกต่าง แม้ negatives CALIBRATION ไม่ถูก undersample: positive pair มาจาก entity เดียว แต่ negative ใช้สอง entity ภายใน role เหตุผลนี้อธิบายความเสี่ยง prior shift ไม่พิสูจน์ว่าเป็นเหตุทั้งหมดของผลต่าง [docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:64–77] ไม่ fit correction จาก test labels

B1→B2 เปลี่ยน policy class และ bounds ไม่ nested จริง ส่วน B2→B3 ใช้ class/bounds/objective/budget เดียวแต่สาม outer seeds และ internal seed เดียวต่อ partition ยังไม่สนับสนุน superiority ทั่วไป [experiments/icsec_final/authoritative_run_v2r1/PROTOCOL_V2R1.md:53–75; docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:109–127]

10-gene weighted decision เปลี่ยน function class/features/population จาก four-parameter จึงไม่แยกผลของ optimizer ต้องเทียบ random/Sobol/GA บน class เดียวกัน, actual budget และ initialization เดียวก่อนอ้าง causal advantage [experiments/code/run_feature_aware_ga_pipeline.py:274–353; docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:90–120]

## 8. Uncertainty และ external validity

Pair rows แชร์ entity จึงไม่ใช่ iid samples; bootstrap คู่ไม่รับรองความแปรปรวนระดับคน การมี optimizer repeats ไม่เท่ากับ independent datasets และสาม partitions ไม่พิสูจน์ equivalence จาก gain เล็ก [docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:116–134; docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:143–147]

Corpus เก่าบนสาม platforms ไม่รับรองข้อมูลปัจจุบัน, drift, deployment cohorts, ภาษาใหม่ หรือผล downstream CRM ต้องระบุ retrospective reanalysis และไม่อ้าง external validation ที่ไม่ได้ทำ [docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:210–214,239; docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:48]

## 9. Data governance และ cost claims

ยังไม่ verified machine-readable reuse license, redistribution permission, collection methodology, platform ToS compliance, consent/notification หรือ IRB documentation Public hosting ไม่เท่ากับอนุญาตแจก raw data [experiments/icsec_final/authoritative_run_v2/DATA_GOVERNANCE.md:3–14] การ audit code ไม่สามารถสร้าง ethics approval แทนผู้วิจัย

Cost weights `.fp=2,.fn=1,.review=.1` เป็น scenario assumptions ไม่มี measured operational cost evidence ใน Phase 1 [src/identity_resolution/core/business_cost.py:8–17; docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:150–161] Winner ต้องระบุ scenario; reweight frozen decisions ไม่เท่ากับ policy reoptimization บน cost ใหม่

Governance NOT VERIFIED ไม่ได้บอกว่าผิดกฎหมายแน่นอน แต่ block public raw/pair-row release และ block การอ้าง consent/IRB/redistribution rights จนได้เอกสารจริง สำหรับ internal reanalysis ต้องให้ผู้วิจัย/หน่วยงานยืนยันสิทธิและนโยบายก่อนอนุมัติ scientific execution

## 10. สิ่งใดต้อง block ก่อน Phase 2

1. ไม่มี selected snapshot/hash/schema/exclusion/ID mapping ที่รับรองครบ หรือมี contradiction unresolved
2. ไม่ได้ล็อกนิยาม experiment A–F และ mapping กับ protocol จริง: เอกสารอ้างอิงปัจจุบันมีลำดับ A–I ไม่ใช่หก experiments A–F [docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:166–180]
3. Split/evaluator/preprocessing/cache contracts ใหม่ยังไม่ verified; canonical runner ต้อง complete ไม่ใช่เพียง tests ผ่าน
4. Objective/cost assumptions/bounds/search budgets/tie rules/test-access rules ยังไม่ freeze ก่อน run
5. ใช้ predecessor score-gated features หรือ historical predictions เป็น unseen scorer โดยไม่มี training provenance
6. ไม่มี authorization ด้านข้อมูลและ explicit run approval

สิ่งที่บันทึกเป็น historical limitation โดยไม่ block normalized-snapshot reanalysis โดยตัวมันเอง: raw directory หาย (ถ้าไม่อ้าง raw reconstruction), production checkpoint เก่าหาย (ถ้าจะ train ใหม่ใน isolated Phase 2), historical scores ต่าง protocol, old optimizer traces ไม่ครบ, ไม่มี external corpus (ถ้าไม่อ้าง external generalization) เงื่อนไขทั้งหมดต้องใช้ร่วมกับ gate รายงาน 06 ไม่ใช่อนุญาตเริ่ม Phase 2 จากรายงานนี้
