# ตรวจ repo เทียบรีวิว ICSEC 2026 — 10 ตุลาคม 2026

**What this repo does:** repo นี้มีหลายสายสำหรับจับคู่โปรไฟล์ข้ามแพลตฟอร์ม ตั้งแต่ notebook รุ่นแรก ระบบ multimodal/CRM การทดลอง R-series การทดลองบทความ V2R1 และ GA 10 พารามิเตอร์ แต่ละสายใช้ข้อมูล ตัวแบ่งชุด และนิยามผลต่างกัน การตรวจนี้สมมติการใช้งานเป็นนักวิจัยหนึ่งคนรัน batch บนข้อมูลประมาณ 36,800 โปรไฟล์/2.09 ล้าน candidate pairs และต้องรันซ้ำได้โดยไม่ปนผลเก่า

**ข้อสรุป:** ข้อวิจารณ์หลักของผู้ประเมินมีหลักฐานรองรับ แต่ไม่ใช่ทุกข้อเป็น bug และไม่ใช่ทุกสายมีปัญหาเดียวกัน V2R1 มีการแบ่ง entity ที่ตรวจได้และผลที่คำนวณซ้ำตรงกัน ส่วนสาย notebook/คะแนน production เก่ามีปัญหาที่ไม่ควรนำไปตั้งต้นทดลองใหม่โดยตรง ควรเขียน protocol และตัวรันใหม่โดยใช้ส่วนที่ตรวจแล้วซ้ำ ไม่จำเป็นต้องทิ้งทุกฟังก์ชัน

แหล่งรีวิว: จดหมายที่ผู้ใช้แนบ ชื่อบทความ #1571350182 ประกอบด้วย Second Round Reviews 1–3 การตรวจนี้ไม่ได้เข้าถึง PDF ที่ส่งจริงใน EDAS จึงแยกข้อความในจดหมายออกจากฉบับแก้ที่พบใน workspace

## หลักฐานและขอบเขตที่ตรวจจริง

- สำรวจรายการไฟล์ที่ `rg --files` มองเห็น 1,203 ไฟล์ ณ เวลาตรวจ; parse Python 113 ไฟล์และ notebook 32 ไฟล์ ไม่พบ Python syntax error การ parse ไม่ได้หมายถึงอ่านทุกบรรทัดหรือ execute ทุก notebook
- อ่านเส้นทางข้อมูล/แบ่งชุด/feature/model/calibration/policy/evaluation หลักใน `src/`, `experiments/code/`, authoritative V2/V2R1, publication scripts, notebook ประวัติที่เกี่ยวข้อง และเอกสารผล
- คำนวณ TP/FP/FN/REVIEW/automatic metrics/U จากแถวผลเดิมครบ 6 วิธี × 3 partitions = 18 ชุด ตรงกับผลที่เก็บไว้ทั้งหมด
- ตรวจ hash ของ frozen outputs 93 รายการ, source 11 รายการ และ frozen inputs 11 รายการ: ตรงทั้งหมด
- ตรวจ entity-role manifests ทั้งสามรอบ: TRAIN/CALIBRATION/POLICY_VALIDATION/SEALED_TEST ไม่ทับกันภายในแต่ละรอบ
- ตรวจ anytime traces 6 ชุด: มี 12,000 calls/ชุด และ incumbent loss ตรงกับ running minimum
- รัน `uv run --python 3.11 --extra dev pytest -q tests pub_multi/tests`: **105 passed in 25.96s** คำสั่ง `python3.11 -m pytest` ของ interpreter นอก uv ไม่มี pytest จึงใช้ environment ของ repo
- ทำตัวอย่างขนาดเล็กยืนยัน duplicate features จาก wrappers และการโหลด score chunks เก่าปนใหม่ โดยใช้ข้อมูลจำลอง/temporary directory
- วิเคราะห์ calibration และ cost sensitivity เพิ่มจากผลที่ freeze แล้วเท่านั้น ไม่มีการเลือก policy ใหม่จาก test

ผลตรวจแบบอ่านด้วยโปรแกรม: [evidence.json](../../artifacts/audit/icsec_review_20261010/evidence.json), [role priors](../../artifacts/audit/icsec_review_20261010/role_priors.csv), [paired differences](../../artifacts/audit/icsec_review_20261010/paired_cost_differences.csv), [แก้ขอบเขต full-2M metrics](../../artifacts/audit/icsec_review_20261010/full2m_scope_correction.csv)

## แผนที่หลักฐาน — ห้ามรวมเป็นการทดลองเดียว

| สาย | ข้อมูล/ตัวแบ่งชุด | ใช้ได้สำหรับอะไร | ข้อจำกัดหลักที่พบ |
|---|---|---|---|
| Notebook original/v2 | `data/processed/feature_matrix.csv`, 204,701 คู่ | อธิบายประวัติการพัฒนา | Stage10 ใช้ entity ฝั่ง a เท่านั้น |
| Production/multimodal | `pub_multi/data/train_all.parquet`, 58,696 คู่; test 8,313 คู่ | ผลเดิมบน sampled supervised pairs | TF-IDF fit ทุกโปรไฟล์, validation ทำหลายหน้าที่, โมเดลต้นฉบับบางไฟล์หาย |
| R0–R6/legacy cache | `experiments/scored_pairs_enriched.parquet`, 2,086,245 คู่ | ผลพัฒนาการ/diagnostics | แบ่ง val/test ใหม่หลังคะแนนต้นทางมีแล้ว; name feature ถูก gate ด้วยคะแนนเก่า |
| ICSEC V2R1 | GB-17/18; seeds 101/202/303; 4 entity roles | ฐานผลบทความที่ตรวจย้อนกลับได้ดีที่สุดใน repo | conditional recall, prior ต่างข้าม role, baseline/domain/จำนวนรอบจำกัด |
| Reviewer revision | 18 ชุดผลเดิมและ Chow เพิ่ม; validation replay | ตอบ M1/M2 และบางส่วนของ M4/M6 | ไม่ใช่การทดลองอิสระเพิ่ม; checklist บางข้อประกาศแก้ครบเกินหลักฐาน |
| One-stage 10-gene/full 2M | ทั้ง sampled pairs และ legacy full cache | ทดลองนโยบายอีกสาย | full-2M metrics เป็น candidate scope; ชื่อ test ไม่รับประกัน scorer ไม่เคยเห็น entity |

## ต้องแก้ก่อนใช้เป็นหลักฐานของการทดลองใหม่

### 1. Notebook ที่เรียกว่า entity-aware ยังมีโปรไฟล์เดียวกันข้าม train/test

- **คืออะไร:** [Stage10 v2](../../thesis_rebuild/00_notebook_history/v2/stage10_dataset_v2.ipynb), code cell 4 และ [Stage10 original](../../thesis_rebuild/00_notebook_history/original/10_dataset_split.ipynb) กรองคู่ด้วย `entity_id_a` เพียงฝั่งเดียว แล้วตรวจ overlap เฉพาะชุด entity ฝั่ง a
- **ปัญหา:** คู่ `(A,B)` อยู่ train และ `(C,B)` อยู่ test ได้ แม้ A กับ C ไม่ทับกัน เมื่อ replay กฎ v2 seed 42 บน feature CSV ปัจจุบัน พบ profile IDs ทับ train/test **16,706 IDs** จาก profile IDs ใน test 18,646 IDs นี่เป็นการตรวจ split บน artifact ปัจจุบัน ไม่ใช่การรันโมเดลประวัติซ้ำ
- **แก้:** แบ่ง entity ก่อน แล้วรับคู่เข้าบทบาทหนึ่งต่อเมื่อ entity ของทั้งสองปลายอยู่บทบาทเดียวกัน ใช้หลักของ [route_pairs](../../experiments/icsec_final/authoritative_run_v2/real_adapters.py) หรือ [build_entity_split](../../src/identity_resolution/stages/features.py) ที่ตรวจสองปลายแล้ว
- **ถ้าข้าม:** การรัน notebook ใหม่จะยังอ้างว่า unseen identities ทั้งที่มีคน/โปรไฟล์เดิมอยู่ใน train

### 2. Test ใน legacy cache ไม่เป็นอิสระจาก scorer ต้นทางตาม lineage ที่มี

- **คืออะไร:** [exp_lib.py](../../experiments/code/exp_lib.py), `build_cache` L72 เป็นต้นไป โหลดคะแนนจาก CRM แล้วค่อย hash `user_folder` เป็น val/test; [full-2M runner](../../experiments/code/run_full_2m_one_stage_ga.py) ใช้ split นี้ต่อ
- **ปัญหา:** เทียบกับ production train rows ที่แพ็กอยู่ใน `pub_multi/data/train_all.parquet` พบ entity ร่วมกับ legacy test **2,445 จาก 4,554 entities** และ test pairs **168,973/195,440** แตะ entity ที่อยู่ใน training export อย่างน้อยหนึ่งปลาย การ freeze GA ก่อนเปิด test ไม่ทำให้ scorer ต้นทางเป็นอิสระขึ้น
- **แก้:** สร้าง split ของทุกชั้นร่วมกันก่อน train scorer; score ของ CALIBRATION/POLICY_VALIDATION/TEST ต้องมาจาก scorer ที่ไม่ fit ด้วย entity ของบทบาทเหล่านั้น
- **ถ้าข้าม:** ผล GA อาจใช้สรุปการปรับ policy บนคะแนนที่มีอยู่ได้ แต่ใช้พิสูจน์การจับคู่คนที่ scorer ไม่เคยเห็นไม่ได้ โมเดล production ต้นฉบับหายใน workspace จึงยังยืนยันประวัติ fit ของ binary เดิมโดยอิสระไม่ได้; overlap ที่รายงานยืนยันจาก training export และโค้ดสร้างแพ็กเกจ

### 3. Full-2M ของ GA 10 genes ไม่รวม blocking misses ใน recall/F1/U

- **คืออะไร:** [project_one_stage_to_full_2m.py](../../experiments/code/project_one_stage_to_full_2m.py) เรียก `expanded_metrics` ด้วยแถว candidate cache; [decision_metrics](../../experiments/code/run_feature_aware_ga_pipeline.py) หาร recall ด้วย positives ในแถวที่รับเข้าเท่านั้น
- **ปัญหา:** แถว `all` ของ one-stage มี TP=20,095, FP=183 และ positives ใน candidates=25,931 จึงได้ recall 0.7749/F1 0.8697 แต่ positives ทั้ง workflow มี 29,243; ต้องเติม blocking misses 3,312 เมื่อตรวจแล้วว่า candidate keys ของ cache เก่าและ V2 ตรงกันทั้งหมด จะได้ **recall 0.687173, F1 0.811575, U 7357.6** แทน U 4045.6
- **แก้:** ใช้ evaluator กลางที่รับ exact/scored/missed components และรายงาน candidate กับ workflow metrics เป็นชื่อชัดเจน
- **ถ้าข้าม:** อาจเข้าใจว่าระบบผ่าน recall gate 0.70 ทั้ง workflow ทั้งที่แถว `all` หลังรวม misses ยังไม่ถึง ค่านี้เป็น full projection ซึ่งรวม development rows จึงไม่ใช่ผล generalization ใหม่ด้วย

### 4. Reviewer M1 ถูกต้อง: headline F1 เดิมตัด positive REVIEW ออก

- **คืออะไร:** [_metrics](../../experiments/icsec_final/authoritative_run_v2/final_runner.py), L52 ใช้ `TP/(TP+FN)` โดย FN นับเฉพาะ positive NO_MATCH รวม blocking misses
- **ปัญหา:** ย้าย positive จาก NO_MATCH ไป REVIEW ลดตัวส่วนได้แม้ยังไม่ MATCH; B0→B1 decision F1 0.850965→0.891037 ขณะที่ automatic F1 0.841952→0.866722 ใน seeds 202/303 automatic F1 เพิ่มเพียง 0.000479/0.000070
- **แก้:** ใช้ [reviewer_revision.metrics](../../experiments/code/reviewer_revision.py) เป็นจุดเริ่มสำหรับ automatic metrics และเพิ่ม negative REVIEW/TN/component slices ให้ครบ ใช้ conditional metrics เป็นผลประกอบโดยระบุชื่อ
- **ถ้าข้าม:** ข้อสรุปว่า “จับคู่ได้ดีขึ้น” จะรวมประโยชน์จากการพักการตัดสินใจเข้าไปด้วย ฉบับ reviewer revision แก้การรายงานเรื่องนี้แล้ว แต่สูตร frozen เดิมตั้งใจคงไว้เพื่อประวัติ

### 5. มี prior shift ระหว่าง CALIBRATION และ TEST แม้ CALIBRATION ไม่ได้ undersample

- **คืออะไร:** [role_for_entity](../../experiments/code/run_icsec_authoritative_v2.py), L169 แบ่งประมาณ TRAIN 49%, CALIBRATION 10.5%, POLICY_VALIDATION 10.5%, TEST 30%; [train_and_calibrate](../../experiments/icsec_final/authoritative_run_v2/final_runner.py), L149 ใช้ negatives 3:1 เฉพาะ TRAIN
- **ปัญหา:** positive pair เป็น entity เดียวจึงมีโอกาสอยู่ role ประมาณ q แต่ negative pair ต้องให้สอง entity อยู่ role เดียวกันจึงประมาณ q² สัดส่วน positives ของ candidate population จึงต่างตามขนาด role; ตัวเลขจริงอยู่ในตารางด้านล่าง และ mean predicted probability ใน TEST สูงกว่า observed positive rate ทั้งสามรอบ
- **แก้:** กำหนดประชากรเป้าหมายและขนาด search cohort ก่อน แบ่ง calibration/validation/test ให้เทียบกันได้ ตรวจ reliability diagram/Brier/ช่วงคะแนนที่ใช้ตัดสิน และถ้าจะปรับ prior ต้องใช้ข้อมูล/สมมติฐานจาก development หรือ deployment design ที่ระบุล่วงหน้า ห้าม fit correction จาก test labels
- **ถ้าข้าม:** ค่า p ที่ calibrate บนอีกสัดส่วนหนึ่งอาจไม่ตรงกับความเสี่ยงจริงใน test/deployment ทำให้ทั้ง Chow และ threshold tuning ตีความยาก ความต่างของ prior เพียงอย่างเดียวไม่พิสูจน์ว่าเป็นสาเหตุทั้งหมดของช่องว่างผล

| Seed | CALIBRATION positive % (scored) | POLICY_VALIDATION positive % | TEST positive % | TEST mean p % | TEST ECE, 10 bins |
|---|---:|---:|---:|---:|---:|
| 101 | 5.7072 | 5.5904 | 2.1835 | 2.6544 | 0.004709 |
| 202 | 6.7076 | 6.0266 | 2.0903 | 2.7130 | 0.006239 |
| 303 | 5.9435 | 5.8933 | 2.1095 | 2.6040 | 0.004952 |

ECE ข้างต้นเป็น post-hoc diagnostic ที่คำนวณจาก frozen TEST probabilities ในการตรวจครั้งนี้ ไม่ได้ใช้เลือก calibrator ค่าเฉลี่ยที่เล็กในข้อมูล negative มากไม่รับรองว่า calibration บริเวณ threshold ดี; bins และจำนวนตัวอย่างเก็บใน evidence.json

### 6. Production preprocessing และ calibration ใช้ขอบเขตต่างจากที่เอกสารเรียก leak-safe

- **คืออะไร:** [train_base.py](../../src/identity_resolution/stages/train_base.py), `make_profile_bundle` L307 fit TF-IDF ด้วยทุกโปรไฟล์; `train_and_eval` L427 ใช้ val เลือก model, fit isotonic และเลือก threshold; val/test negatives มาจาก pair sampling
- **ปัญหา:** การอ้างผลกับ unseen data แบบ inductive ต้องไม่เรียน vocabulary/IDF จาก test; calibration บน sampled val ที่มี positive **51.12%** ไม่ใช่ candidate prior ของระบบจริง และการวัด val หลัง fit calibrator บน val เองเป็นผลในชุด fit ของ calibrator
- **แก้:** fit preprocessing จาก TRAIN และ transform บทบาทอื่น; แยก CALIBRATION กับ POLICY_VALIDATION; เก็บชุดประเมินเป็น candidate population ที่นิยามไว้ ผล production เก่าเก็บเป็น historical sampled-pair benchmark
- **ถ้าข้าม:** ความมั่นใจ/threshold จาก supervised benchmark จะถูกใช้เหมือนเป็น probability บน full candidates ข้อผิดพลาดนี้ไม่ใช่หลักฐานว่า V2R1 ใช้ test fit model เพราะ V2R1 ใช้ feature/runner อีกสาย

### 7. รัน multimodal หลายแบบต่อกันทำให้เพิ่ม feature ภาพซ้ำ

- **คืออะไร:** [train_multimodal.py](../../src/identity_resolution/stages/train_multimodal.py), `load_base_module` L36 คืน module object เดียวทุกครั้ง แต่ `run_experiment` L350 เปลี่ยน `base.make_profile_bundle` และ `base.compute_features` เป็น wrapper
- **ปัญหา:** default loop รัน image_stats แล้ว image_context; wrapper ตัวหลังครอบตัวแรกอีกชั้น การทดสอบจำลองกับ wrapper จริงพบชื่อ feature ภาพซ้ำ **14 คอลัมน์** ซึ่งอาจทำให้ parquet/model input ล้มเหลวหรือ schema ไม่ตรง
- **แก้:** เก็บ original functions แล้วคืนค่าด้วย `try/finally` หลังแต่ละ experiment หรือส่ง functions เข้า workflow โดยไม่แก้ global module; เพิ่ม test ว่ารันสอง variant ต่อกันได้ schema เท่ากับรันแยก
- **ถ้าข้าม:** การ retrain ตาม default command อาจไม่ได้ feature set ที่ประกาศไว้ แม้ tests 105 ข้อปัจจุบันผ่าน นี่เป็น bug ใน source ปัจจุบัน ไม่ได้พิสูจน์ว่า artifacts ประวัติสร้างด้วย source รุ่นนี้

### 8. Score chunks เก่าปนรอบใหม่ได้

- **คืออะไร:** [full_candidate.py](../../src/identity_resolution/workflows/full_candidate.py), `score_candidates_chunked` เขียนชื่อไฟล์ตาม start/stop และ `load_scored_candidates` L188 โหลดทุกไฟล์ที่ glob เจอ; exact exports ใช้แนวเดียวกัน
- **ปัญหา:** เปลี่ยน chunk size หรือ candidate population แล้วเขียนที่เดิม ไฟล์รอบก่อนยังอยู่ ตัวอย่างจริงกับ loader: chunk `[0:2]` เก่ากับ `[0:3]` ใหม่ถูกโหลดเป็น 5 แถวโดยมีคู่ซ้ำ 2 คู่ ส่วน `--reuse-scores` ไม่ตรวจ model/input hashes
- **แก้:** output directory ใหม่ต่อ run และ manifest ระบุ chunk ที่เป็นของ run นั้น ตรวจ unique canonical pair keys และ hashes ก่อนรวม/ใช้ cache
- **ถ้าข้าม:** ตัวเลข/การ merge CRM อาจนับคู่ซ้ำหรือใช้คะแนนจากโมเดลเก่าโดยไม่รู้ตัว

### 9. ยัง reproduce จาก raw หรือรัน production ตาม README ไม่ได้ครบ

- **คืออะไร:** raw path `data/data/Dataset-LinkSocial` เป็น gitlink commit `fe67dd1102d9265fb5c47d0f3d8ff19546294571` แต่ directory ว่างและไม่มี `.gitmodules`; path ของ selected production model ใน [settings.py](../../src/identity_resolution/settings.py) ไม่มี `models/best_model.pkl`
- **ปัญหา:** `identity-ml prepare` ไม่มี raw ที่คาดไว้ และ predict โหลดโมเดลที่หาย; cleaned CSV มี 24,729 แถว แต่ normalized CSV มี 36,807 แถวและยังไม่มี lineage ที่พิสูจน์ว่าไฟล์หนึ่งสร้างอีกไฟล์หนึ่ง นอกจากนี้ prepare/pairs/features/train ใช้ input paths คนละสาย และ train แบบ multimodal สร้าง dataset ของตนเอง จึงยังไม่ใช่ chain เดียวตามรูป lifecycle
- **แก้:** ประกาศ input snapshot หนึ่งชุด พร้อมที่มา/hash/schema/ข้อยกเว้น และระบุ stage contracts ให้ตรง หากเริ่มจาก normalized snapshot ต้องบอกตรง ๆ ว่าเป็นการ reanalysis จาก snapshot ไม่ใช่ raw-to-result reproduction; กู้หรือ retrain โมเดลที่จำเป็นลง run ใหม่
- **ถ้าข้าม:** การ “เริ่มตั้งแต่ clean” อาจได้ข้อมูลคนละประชากร หรือคำสั่งรันหยุดก่อนถึงการทดลอง ค่า hash ของ V2R1 ที่ผ่านไม่ได้ซ่อม lineage ที่ขาดก่อนหน้า

## ควรแก้เพื่อให้ตอบคำถามวิจัยและรีวิวได้ครบ

### 10. Baseline และ search domain ยังไม่แยกผลของ policy class ได้สะอาด

- **คืออะไร:** [policies.py](../../experiments/icsec_final/authoritative_run_v2/policies.py), L12/L53/L74 จำกัด t_review เริ่ม 0.50 ขณะที่ Chow ภายใต้ต้นทุนนี้มีขอบ 0.10; B1 ไปถึง 0.999 แต่ B2/B3 ไปถึง 0.90
- **ปัญหา:** B1→B2 เปลี่ยนทั้งกฎและ search domain; expanded rule เดิมยังปิด promotion ไม่ได้ทุกกรณีด้วย `c_p=1,c_d=0` เพราะใช้ `s>=c_p` เช่น p=.8,s=1,t_m=.98,t_r=.5: simple=REVIEW แต่ expanded=MATCH
- **แก้:** มี Chow และ simple two-threshold optimum จาก unique score breakpoints เป็น baseline; ให้ expanded policy มี setting ที่คืน simple decisions ได้จริงรวมขอบ s=0/1 แล้วให้ GA/Sobol/random ใช้กฎ/bounds/objective เดียวกันทั้งหมด
- **ถ้าข้าม:** จะสรุปไม่ได้ว่าชนะเพราะความยืดหยุ่น กรอบค้นหา หรือ optimizer เพิ่ม Chow ใน reviewer revision แล้ว แต่ยังไม่ได้แก้โครงทดลองเดิม

### 11. จำนวน outer partitions และ optimizer repeats ยังตอบเรื่อง GA ได้จำกัด

- **คืออะไร:** V2R1 มี 3 outer seeds และ GA หนึ่ง internal seedต่อ partition ใช้เลขเดียวกับ outer seed; Sobol ไม่ scramble จึงไม่เปลี่ยนเมื่อเปลี่ยน seed argument
- **ปัญหา:** optimizer variation ปนกับ split variation ผล B3−B2 ใน test U เป็น **−5.5, 0, +0.1**; mean −1.8 ไม่เป็นหลักฐาน equivalence หรือ superiority B1→B2 ยังกลับทิศใน seed 303
- **แก้:** รายงาน paired differences ตามตารางนี้ และรอบใหม่แยก outer partitions กับ optimizer seeds มี random search, actual-call budgets และ anytime curves เก็บทุก seed โดยไม่เลือก seed จาก test
- **ถ้าข้าม:** “GA ดีที่สุด” จะอาศัยค่าเฉลี่ยที่เล็กมาก ขณะที่การทำ 10 optimizer seeds บน validation ชุดเดียวก็ไม่เท่ากับมีข้อมูลทดลองอิสระ 10 ชุด

| Seed | U(B1)−U(B0) | U(B2)−U(B1) | U(B3)−U(B2) | U(B1)−U(Chow) |
|---|---:|---:|---:|---:|
| 101 | −711.3 | −24.5 | −5.5 | +33.5 |
| 202 | −465.6 | −52.6 | 0.0 | −11.2 |
| 303 | −322.0 | +63.5 | +0.1 | −65.7 |

### 12. Bootstrap เดิมสุ่มคู่แบบอิสระ ทั้งที่คู่แชร์ entity

- **คืออะไร:** [bootstrap_intervals](../../experiments/code/run_one_stage_weighted_ga_experiment.py), L279 สุ่ม indices ของ pairs และสุ่มแยกสำหรับแต่ละ policy; [analyze_icsec_primary.py](../../experiments/code/analyze_icsec_primary.py), L60 มี paired bootstrap แต่ยังสุ่มเป็นคู่และตรึง exact/miss constants
- **ปัญหา:** `(A,B)` กับ `(A,C)` พึ่งข้อมูลของ A ร่วมกัน การสุ่มแต่ละคู่ไม่สะท้อนความแปรปรวนระดับคน และ CI ของ best policy ที่เลือกจาก validation เดียวกันไม่รวม selection uncertainty
- **แก้:** ใช้ paired per-outer differences เป็นรายงานขั้นต่ำ; หากจะทำ CI ให้กำหนด sampling unit ระดับ entity/query และจัดการ negative pairs ที่มีสอง entity ให้ถูกต้อง ใช้ draws เดียวกันเมื่อเทียบวิธี
- **ถ้าข้าม:** CI อาจดูแคบกว่าความไม่แน่นอนที่งานต้องการอ้าง อย่านำ CI สาย primary reproduction เก่ามาแนบผล V2R1

### 13. Semantic ablation ของบทความยังไม่พอเลือก representation และ cache เก่ามี score-dependent feature

- **คืออะไร:** V2R1 เทียบ GB-17/18 เฉพาะ B0 แล้วใช้ GB-18 ต่อ; [exp_lib.py](../../experiments/code/exp_lib.py), L96 คำนวณ name_sim เฉพาะ score>=.5 และ [exp_r2_bert_feature.py](../../experiments/code/exp_r2_bert_feature.py), L257 เอาค่านั้นเป็น feature
- **ปัญหา:** mean U ของ GB-18+B0 แย่ขึ้น **12.2333** แม้ conditional F1 สูงขึ้นเล็กน้อย; threshold เดียวไม่แยกคุณภาพ representation จาก calibration/operating point ส่วน cache เก่ามี low-score rows **1,288,634** แถวที่ name_sim เป็นศูนย์ทั้งหมด จึงไม่ใช่ lexical similarity ล้วน
- **แก้:** รอบใหม่คำนวณ name evidence โดยไม่ดู model score ตาม [corrected_name_sim](../../experiments/icsec_final/authoritative_run_v2/features.py) แล้วเทียบ GB-17 และ GB-18 ทั้ง discrimination/calibration และนโยบายเดียวกันหลังเลือกบน validation อย่างเป็นธรรม
- **ถ้าข้าม:** จะอธิบายผลของ MiniLM ผิดหรือพา signal จาก scorer เก่าเข้าการทดลองใหม่ V2R1 ซ่อม name feature แล้ว จึงไม่ควรเหมารวมว่าผล GB-17/18 ฉบับนั้นมี score gate เดิม

### 14. Blocking และ exact tier มี implementation แต่รายละเอียด/ผลไม่ครบในบทความ

- **คืออะไร:** [full_candidate.py](../../src/identity_resolution/workflows/full_candidate.py), L90/L125 ใช้ exact username/URL และ blocking username-prefix3/fullname-prefix3/external-domain; V2 scope นับ 25,931/29,243 positives = 88.67%
- **ปัญหา:** policy หลัง blocking กู้ 3,312 positives ที่ไม่ถูกสร้างคู่ไม่ได้ exact global tier มี 12,403 คู่และ FP 63; TEST precision ของ exact tierในสามรอบคือ 0.997521/0.996467/0.999732 การ bypass model ไม่ได้แปลว่าถูก 100%
- **แก้:** แสดงกฎ blocking และ metrics แยก tier/slices; ถ้ารอบใหม่อ้างผลทั้งระบบ ให้เพิ่ม retrieval alternative ที่เลือกบน development และวัด recall เทียบ candidate count/runtime บนชุดเดียวกัน
- **ถ้าข้าม:** จะลงทุนกับ policy gain ไม่กี่หน่วยโดยไม่รู้ข้อจำกัดต้นทาง Reviewer 2 ถูกสำหรับการทดลองบทความ แต่คำว่า “ไม่มี blocking alternative ใน repo เลย” ไม่ถูก: มี R6 ซึ่งใช้ protocol อื่นและยังไม่ใช่ controlled comparator ของ V2R1

### 15. Ranking เปลี่ยนเมื่อเปลี่ยนต้นทุน และยังไม่มีหลักฐานค่าต้นทุนจริง

- **คืออะไร:** U=2FP+FN+0.1REVIEW เป็น scenario assumption; [business_cost.py](../../src/identity_resolution/core/business_cost.py) ยังเรียกว่า CRM-derived ตามสมมติฐานค่าจ้าง
- **ปัญหา:** audit นี้ reweight frozen decisions ที่ FP∈{1,2,5}, REVIEW∈{.05,.1,.2}, FN=1 พบ mean-loss winner สลับระหว่าง Chow/B1/B3 เช่น (2,1,.05)=Chow, (2,1,.1)=B3, (2,1,.2)=B1
- **แก้:** รายงาน sensitivity ให้ครบ และแยกการ reweight policy เดิมออกจากการ retrain/reselect policy บน validation สำหรับต้นทุนแต่ละ scenario รายงาน review load/capacity และ automatic quality ร่วมด้วย
- **ถ้าข้าม:** คำแนะนำใช้ GA จะดูเป็นข้อสรุปทั่วไป ทั้งที่ขึ้นกับต้นทุน สายเก่ามี sensitivity scripts อยู่แล้ว แต่ไม่ใช่หลักฐาน sensitivity ของ V2R1 ชุดนี้

### 16. Data governance และ AI-use disclosure ยังเป็นข้อมูลที่โค้ดยืนยันแทนผู้เขียนไม่ได้

- **คืออะไร:** [DATA_GOVERNANCE.md](../../experiments/icsec_final/authoritative_run_v2/DATA_GOVERNANCE.md) ระบุเอกสารสิทธิ/การเก็บ/consent/ethics ยังไม่ยืนยัน; [AI_DISCLOSURE_AUDIT.md](../../paper/reviewer_revision/AI_DISCLOSURE_AUDIT.md) ยังเป็นร่าง
- **ปัญหา:** public corpus ไม่เป็นหลักฐานว่า redistribution อนุญาต และร่าง disclosure มีชื่อเครื่องมือ/โมเดลที่ audit นี้ยืนยันประวัติไม่ได้ รูปแบบภาษา/ขีด em dash เพียงอย่างเดียวก็พิสูจน์การใช้ AI ไม่ได้
- **แก้:** รวบรวมแหล่งข้อมูล/เงื่อนไขใช้และกระบวนการที่ผู้เขียนใช้จริง; ใช้ disclosure ตาม factual usage การใช้ผู้ช่วยกับโค้ด/analysis/manuscript revision รอบนี้เกิน language polishing แล้วหากนำงานนั้นไปใช้
- **ถ้าข้าม:** ยังตอบข้อทักท้วงเรื่องที่มา/การเปิดเผยไม่ได้ การตรวจครั้งนี้ไม่ได้วินิจฉัยสิทธิทางกฎหมายหรืออ้างว่าได้รับ ethics approval

### 17. Checklist ฉบับแก้และข้อความบางส่วนใน repo ให้สถานะเกินหลักฐาน

- **คืออะไร:** [REVISION_REPORT.md](../../paper/reviewer_revision/REVISION_REPORT.md), L22 ระบุ M5 เป็น identity edge case ที่ไม่มีคำถามจริง และ M4/M6 เป็น FIXED; README/เล่มเดิมยังชู R3 best หรือเรียก production score ว่า 17-feature ในบางจุด
- **ปัญหา:** จดหมายระบุ M5 ชัดว่า n=3/paired analysis; M4 ยังไม่มี random search/multiple GA seeds และ M6 ในตัวบทบอกเพียง seeded selection/Gaussian mutation โดยไม่ครบ crossover/σ/elitism GA ของ V2 จริงไม่มี crossover, เลือก top 20%, ทำ mutation แม้แถว elite, σ=.02 ต่อ gene ด้วย probability .30 และ clip bounds — ต่างจาก R1 GA ที่มี uniform crossover และเก็บ elite
- **แก้:** ใช้ issue matrix ด้านล่างเป็นสถานะตรวจล่าสุด; แก้เอกสารที่ไม่ frozen และแยกชื่อ experiment/model/version ให้ตรง artifact ถ้าจะเปลี่ยนไฟล์ใน revision package ต้อง reclose manifest ของ package นั้นอย่างมีบันทึก
- **ถ้าข้าม:** คนทำรอบใหม่อาจคิดว่าแก้รีวิวครบแล้ว หรือใช้ GA คนละ implementation โดยเชื่อว่าเหมือนกัน

## ตอบรีวิวเป็นข้อ ๆ

### Reviewer 1 — Major

| ข้อ | คำตัดสินจาก repo ปัจจุบัน | งานที่ยังต้องทำ |
|---|---|---|
| M1 REVIEW/recall | ยืนยันปัญหาการตีความ; revision เพิ่ม automatic metrics แล้ว | ใช้เป็น headline รอบใหม่, รายงาน R+/R− และ risk–coverage |
| M2 Chow baseline | ขาดในต้นฉบับตามจดหมาย; revision มีและคำนวณถูก | ตรวจ calibration/prior และเปิด domain/เพิ่ม exact simple optimum |
| M3 U ผิดทิศ | GB-18 U สูงกว่า GB-17 12.2333 จริง; source revision เขียนถูกแล้ว | อธิบายเหตุผลใช้ GB-18 ต่อ หรือเทียบทั้งสอง representation อย่างยุติธรรม |
| M4 optimizer comparison | anytime/vectors มีแล้ว แต่แก้เพียงบางส่วน | random baseline, budgets เล็ก, หลาย internal seeds, config GA จริง |
| M5 n=3/paired differences | จริง; ข้อความ M5 ในรายงานเก่าจับประเด็นผิด | ใช้ paired table, แยก variance และจำกัดข้อสรุป |
| M6 policy incomplete | decision equation/bounds/name normalization ชัดขึ้นแล้ว | เพิ่ม GA settings ครบ และแก้ non-nested design สำหรับรอบใหม่ |
| M7 Agentic CRM | ไม่พบใน main.tex ของ reviewer revision | เล่ม CRM ต้องมี downstream evaluation ของตนเองถ้าจะอ้างผล |

ตัวเลข back-calculation “ประมาณ 236 positives ย้ายไป REVIEW” ของ reviewer ไม่ใช่จำนวนที่คำนวณจากแถวจริง เพราะนำค่าเฉลี่ย recall และ FN ไปกลับสูตรที่ไม่เป็นเชิงเส้น ผลจริง B0→B1 คือ mean TP +344.33, FN −613.67, positive REVIEW +269.33 ข้อวิจารณ์เชิงหลักการยังถูกต้อง และการ defer เพิ่มไม่ได้ทำให้ precision/F1 สูงขึ้นเสมอสำหรับทุก policy

เหตุผล “12,000^(1/4) ≈ 10.5 จึงแทบรับประกันว่า GA ไม่ชนะ” เป็น intuition ไม่ใช่ข้อพิสูจน์ งาน replay พบ GA ได้ validation loss ดีกว่า Sobol บางงบ/seed จึงควรวัด anytime โดยตรง; ยังไม่มีหลักฐานชัยชนะทั่วไปจากรอบเดียวต่อ partition

### Reviewer 1 — Minor

| ข้อ | ผลตรวจ/สิ่งที่ยังขาด |
|---|---|
| 1 calibration sampling prior | TRAIN เท่านั้นที่ undersample; พบ role-induced prior shift เพิ่มเติมตามข้อ 5 |
| 2 exact-tier precision | คำนวณได้และมีบางรายงาน production แต่ไม่ได้แสดงครบในบทความ; audit นี้ให้ค่าราย seed แล้ว |
| 3 blocking description | โค้ดมีกฎชัดเจน; main.tex ยังอธิบายไม่พอ |
| 4 model-family development screen | มี LR/RF/GB/neural benchmarks หลายสาย แต่ไม่ใช่ controlled evidence ภายใต้ V2R1 เดียวกัน |
| 5 URL in Fig.1 | URL ใช้ใน retrieval/exact tier แต่ไม่อยู่ใน scorer17; ควรแยกสองชั้นในรูป ไม่ต้องอ้างว่า URL ไม่ถูกใช้ทั้งระบบ |
| 6 repeated figure | revision เพิ่ม anytime แล้ว แต่ยังเก็บ development figure; ควรใช้พื้นที่ตามคำถามหลัก |
| 7 broken headings | revised source ใช้ headings ชัดขึ้นแล้ว; ยังไม่ได้เทียบ submitted PDF จริง |
| 8 garbled sentence/F1 typo | revised Results เขียนใหม่; ไม่พบข้อความตัวอย่างนั้นในส่วนที่อ่าน |
| 9 equation formatting | revised source ใช้ equation environment แล้ว |
| 10 excessive precision | ยังมี 88.6742% และ 99.5355% ใน main.tex |
| 11 B0 thresholds | พบ fixed .98/.95; ยังไม่มีหลักฐานเลือกค่าอย่างเป็นระบบตามต้นทุนนี้ |
| 12 cost sensitivity | มีของสายเก่า; audit นี้เพิ่ม frozen-policy diagnostic สำหรับ V2R1 แต่ยังไม่ได้ reselect ทุก scenario |
| 13 validation–test gap | มี validation traces และ test decisions แต่บทความยังไม่แสดงตารางเปรียบเทียบที่ scope/normalization ตรงกัน |
| 14 related work | revision ยัง 13 references และยังไม่ครอบคลุมตามคำแนะนำครบ; ไม่ควรเติมงาน graph ที่ไม่มีข้อมูลทดสอบแล้วอ้างว่าเทียบแล้ว |
| 15 AI/editorial | แก้ภาษาได้; actual disclosure ต้องตรงการใช้จริงและเวอร์ชันที่ส่ง ไม่ใช้รูปแบบภาษาเป็นหลักฐานการใช้ AI |
| 16 reproducibility link | local artifacts/hash มี; ไม่พบ public code/config link ใน main.tex และ raw-to-result ยังมีช่องว่าง |

### Reviewer 2 และ 3

Reviewer 2 ถูกเรื่อง single historical corpus, n=3, assumed costs, REVIEW, non-nested search และ CRM framing ข้อจำกัด Google+ และข้อมูลเก่าแก้ด้วยการแบ่ง seed เพิ่มอย่างเดียวไม่ได้ ข้อวิจารณ์ว่าบทความไม่มี alternative blocking เป็นจริงสำหรับ controlled study นี้ แม้ repo มี R6 อยู่ก็ตาม

Reviewer 3 ว่า “มีเพียง GB และเปลี่ยน learning parameters” ไม่ตรงกับ B0–B3: scorer ถูกตรึงและเปลี่ยน decision policy; repo ยังมีโมเดลอื่นด้วย อย่างไรก็ตาม ข้อทักท้วงเรื่อง novelty และ comparison ที่เกี่ยวข้องยังตอบไม่ครบ การเพิ่มโมเดลจำนวนมากโดยเปลี่ยน data/protocol ไปพร้อมกันจะไม่แก้ปัญหานี้ ควรทำ baseline ที่เกี่ยวข้องภายใต้ protocol เดียวและเขียน contribution เป็น empirical study ตามหลักฐาน

## ของที่นำกลับมาใช้ได้

| เก็บ/ใช้ต่อ | เงื่อนไข |
|---|---|
| normalized snapshot และ ground truth จาก user_folder | อ้างเป็น snapshot ที่มีอยู่ พร้อม hash และขอบเขตที่พิสูจน์ได้ |
| V2 candidate keys/features/decisions | เก็บเป็น historical reference; hash ที่ตรวจผ่านไม่ใช่หลักฐาน raw provenance ครบ |
| V2 corrected lexical/name functions | label-free; ทดสอบ missing values, symmetric pair identity และ schema |
| entity routing ทั้งสองปลาย | ใช้ก่อน train; ปรับสัดส่วน role ให้ตรงโจทย์ |
| GB/LR/isotonic ที่ติดตั้งอยู่ | fit ใหม่เฉพาะบทบาทตาม protocol ใหม่; ไม่โหลด scorer เก่าเป็นหลักฐาน unseen test |
| Chow + automatic evaluator | ขยาย component accounting และ class-specific review counts ให้ครบ |
| validation replay / per-call traces | ใช้โครงบันทึก แต่รอบใหม่ต้องบันทึกตั้งแต่เริ่ม ไม่ต้อง replay เพื่อเดาประวัติ |

แนวทางรอบใหม่อยู่ใน [EXPERIMENT_REWRITE_PROTOCOL_TH.md](../plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md) เอกสารนี้เป็นแผนที่เสนอจากผล audit ยังไม่มีผลทดลองรอบใหม่

## หลักวิธีวิทยาที่ตรวจจากแหล่งต้นฉบับ

- การ fit preprocessing ด้วย TRAIN และ transform ชุดอื่นสอดคล้องกับ [scikit-learn: Common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html)
- การ calibration ต้องใช้ข้อมูลแยกจากการ fit classifier และดู reliability ของ probabilities: [scikit-learn: Probability calibration](https://scikit-learn.org/stable/modules/calibration.html)
- การรายงาน reject option ร่วมกับ coverage/risk มีฐานใน [Geifman & El-Yaniv, 2017](https://papers.nips.cc/paper_files/paper/2017/hash/4a8423d5e91fda00bb7e46540e2b0cf1-Abstract.html)
- Random search เป็น baseline ที่เกี่ยวข้องในการประเมิน optimizer: [Bergstra & Bengio, JMLR 2012](https://www.jmlr.org/papers/v13/bergstra12a.html)

**Verdict:** แก้ split/evaluation/probability population และความสามารถรันซ้ำก่อนเพิ่ม GA complexity; V2R1 เป็นฐานอ้างอิงที่เก็บไว้ได้ แต่หลักฐานยังไม่สนับสนุน GA superiority ทั่วไป

**Not checked:** ไม่ได้ retrain โมเดล/embeddings, regenerate raw, รันทุก notebook, ตรวจ raw JSON ทุกโปรไฟล์/ภาพ, audit network/image ingestion ด้าน security แบบเต็ม, ทดสอบ CRM กับมนุษย์, ยืนยันสิทธิข้อมูลจากเจ้าของ หรือเปิด submitted PDF ใน EDAS ผล audit นี้ไม่ใช่ผลทดลองใหม่หรือการรับรองว่าทุกบรรทัดของ repo ถูกตรวจแล้ว
