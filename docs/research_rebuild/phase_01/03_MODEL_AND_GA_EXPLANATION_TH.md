# คู่มือทำความเข้าใจ Identity Resolution: ปัญหา → ข้อมูล → วิธี → ผล

## 1. งานนี้แก้ปัญหาอะไร

โปรไฟล์บน Twitter, Google+ และ Instagram ไม่ใช่คนสามคนเสมอไป งานนี้สร้างระบบตัดสินว่าโปรไฟล์สองรายการเป็นคนเดียวกันหรือไม่ แล้วจึงนำ MATCH edges ไปประกอบ customer entity สำหรับ CRM การทำนายคู่ถูกไม่ได้รับประกันว่า cluster ที่ merge ถูกทั้งหมด และไม่มีหลักฐานใน Phase 1 นี้ว่าคุณภาพ lead หรือผลธุรกิจดีขึ้นจริง [src/identity_resolution/workflows/crm.py; docs/GETTING_STARTED_TH.md:5–21; docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:181–183,239]

อ่านรายงานนี้คู่กับ `01_DATASET_AND_FEATURE_LINEAGE.md` สำหรับสูตรทุกคอลัมน์, `02_HISTORICAL_EXPERIMENT_MATRIX.md` สำหรับตัวแบ่งชุด และ `04_RESULT_COMPARISON_TH.md` สำหรับตัวเลขที่ตรวจซ้ำ ห้ามอ่านชื่อ R3/GB-18/GA ว่าเป็นโมเดลเดียวกันทั้งหมด

## 2. Profile, entity และ label ต่างกันอย่างไร

Profile คือหนึ่งแถวข้อมูลบัญชี; entity คือกลุ่มบุคคลตาม ground truth ที่มีอยู่ `user_folder` เป็นหลักฐานการจัดกลุ่มใน snapshot ส่วน numeric `profile_id` ในสาย production ถูกใช้เป็น entity identifier และ `profile_row_id` เป็นแถวโปรไฟล์ ตรงข้ามกับ notebook เก่าที่ใช้ชื่อ `profile_id` หมายถึง `platform_username` จึงต้องดู schema ของไฟล์ก่อน join เสมอ [src/identity_resolution/stages/train_base.py:152–189; experiments/code/exp_lib.py:41–45,81–91; docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:18–29]

ตัวอย่างประกอบ ไม่ใช่ข้อมูลบุคคลจริง: แถว 10 บน Twitter และแถว 20 บน Instagram มี entity E1 เดียวกัน จึงเป็น positive pair; แถว 30 ของ E2 เป็น negative เมื่อเทียบกับ E1 การให้ label นี้บอกว่า dataset จัดกลุ่มอย่างไร ไม่ใช่การตรวจสอบตัวตนด้วยเอกสารจากเจ้าของบัญชี หาก entity หายต้องไม่ตีว่าเป็น negative โดยอัตโนมัติ [src/identity_resolution/stages/train_base.py:170–189,256–265; docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:20–22]

คนที่มีสามโปรไฟล์ต่างแพลตฟอร์มสร้างคู่บวกได้สามคู่ แต่ถ้ามีสองโปรไฟล์แพลตฟอร์มเดียวกัน ต้องแยก all-platform positives กับ cross-platform positives สาย train_base ข้าม same-platform pairs อย่างชัดเจน [src/identity_resolution/stages/train_base.py:173–188] รายงาน counts จริงและข้อยกเว้นอยู่ใน dataset inventory ห้ามนำจำนวนคู่จากอีก scope มาเป็น denominator โดยไม่ตรวจ

## 3. ทำไมต้อง clean/normalize และทำไมจำนวนแถวอาจไม่เท่ากัน

Clean คือจัดการรูปแบบและเงื่อนไขคุณภาพ; normalize คือทำข้อความให้อยู่รูปแบบเทียบกันได้ เช่น lowercase/strip, URL parsing หรือ list parsing แต่การมีไฟล์ชื่อ cleaned และ normalized ไม่ได้พิสูจน์ว่ามาจาก population เดียวกัน เอกสาร audit เดิมพบ cleaned 24,729 แถวกับ normalized 36,807 แถว และ raw directory ที่ production คาดไว้ไม่มีข้อมูล จึงยังเล่าเป็น raw-to-result ที่ทำซ้ำครบไม่ได้ [docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:100–105]

การเปลี่ยนจำนวนแถวอาจเกิดจาก exclusion, duplicate removal, merge หรือเปลี่ยน input population ต้องมี keys และเหตุผลจริงรองรับ ไม่อธิบายส่วนต่างด้วยการเดา รายงาน 01 แยกสิ่งที่ source ตั้งใจทำออกจากสิ่งที่ artifact พิสูจน์ได้

## 4. คู่ฝึกกับ candidate pairs ไม่ใช่สิ่งเดียวกัน

คู่ฝึกแบบ supervised sampling รวม positives กับ random negatives และ hard negatives ที่ชื่อใกล้กัน ใน production historical code สุ่มข้ามแพลตฟอร์มและต่าง entity; hard negatives ใช้ username prefixes และ name similarities [src/identity_resolution/stages/train_base.py:237–289]

Candidates คือคู่ที่ retrieval/blocking เลือกให้ระบบพิจารณาจาก search population ไม่ได้ถูกสุ่มให้มี positives ใกล้ 50% โดยธรรมชาติ ระบบเดิมมี exact username/URL tier และ prefix3 username/fullname/external-domain blocking [src/identity_resolution/workflows/full_candidate.py; docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:143–148] Exact ไม่ใช่ ground truth แม้ชื่อหรือ URL ตรงกันก็อาจผิด ต้องตรวจ precision ของ tier นี้แยก

Blocking miss คือ positive ที่ไม่ถูกสร้างเป็น candidate ไม่มี policy ที่ทำงานหลัง blocking กู้คู่ที่ไม่เคยได้รับเข้าได้ ถ้าวัดทั้ง workflow ต้องนับ miss เป็น FN ไม่สร้าง fake probability เพื่อให้ดูว่าโมเดลประเมินแล้ว [docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:37–44,124–137]

## 5. Feature คือหลักฐานตัวเลข ไม่ใช่คำตอบ

โมเดลไม่ได้อ่านความหมายชื่อคอลัมน์เอง แต่รับเวกเตอร์ตัวเลขหนึ่งชุดต่อคู่ Feature บางตัวเป็น similarity (มากคือคล้าย), บางตัวเป็น difference (มากคือต่าง), บางตัวเป็น missingness flag อย่าถือว่าทุกคอลัมน์ยิ่งสูงยิ่งดี [experiments/icsec_final/authoritative_run_v2/features.py:12–19,89–113]

ตัวอย่างประกอบ: `username_lev_sim` ของ V2 คำนวณ `1 - edit_distance/max(length_a,length_b)` เมื่อทั้งสองมีข้อความ; ถ้าข้างหนึ่งหายให้ศูนย์ คู่นามสมมติ `abcd`/`abce` ต่างหนึ่งตำแหน่ง จึงได้ 0.75 เป็นตัวอย่างอธิบายสูตร ไม่ใช่ผล dataset [experiments/icsec_final/authoritative_run_v2/features.py:70–76]

Jaro วัดความคล้ายของลำดับอักขระ; token-sort จัดเรียงคำก่อนเทียบ; Jaccard ของ bio เป็น intersection/union ของชุดคำ; length ratio เป็นสัดส่วนความยาวสั้นต่อยาว; exact location และ both-have flags บอกการตรงและการมีข้อมูล `name_sim` V2 ใช้ maximum ของ Jaro-Winkler สี่คู่ไขว้ username/fullname โดย normalize NFKC/casefold/ช่องว่างและไม่มี score gate [experiments/icsec_final/authoritative_run_v2/features.py:22–49,67–108]

ความต่างสำคัญ: legacy cache คำนวณ name_sim เฉพาะแถว scored ที่ predecessor score ≥ 0.5; แถวอื่นถูกใส่ศูนย์ ดังนั้น feature สุดท้ายขึ้นกับ scorer เก่า ไม่ใช่ lexical evidence ล้วน การอธิบายว่า “ทุกคู่คำนวณความคล้ายชื่อ” จึงผิดสำหรับสายนี้ [experiments/code/exp_lib.py:28,93–101]

Feature 18 ของ corrected V2 คือ `bert_cos` เพิ่มจาก 17 คอลัมน์เดิม เป็น cosine ของ semantic representation ไม่ใช่ GA gene และไม่ใช่ภาพ การอ้างว่า semantic ดีขึ้นต้องเปรียบเทียบ pairs/splits/model parameters/calibration/policy ที่ควบคุมไว้ ไม่ใช่ดู F1 คนละ run [experiments/icsec_final/authoritative_run_v2/features.py:12–19; docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:67–78]

สาย multimodal มี TF-IDF, SBERT, URL/domain, mention/hashtag, style, platform และ image/context features อีกชุด ไม่ใช่ GB-17 บวกภาพทุกกรณี รายการ `MODEL_FEATURES` ใน feature-aware GA อีกสายยังต่างจาก feature count 41 ที่รายงาน multimodal ต้องตรวจ schema ทีละ artifact [src/identity_resolution/stages/train_base.py:152–164; experiments/code/run_feature_aware_ga_pipeline.py:44–53]

## 6. ML models เรียนอะไร

Logistic Regression เรียนสัมประสิทธิ์เพื่อรวม features ก่อนแปลงเป็นคะแนน; Gradient Boosting ประกอบต้นไม้หลายตัวเพื่อเรียนความสัมพันธ์ไม่เชิงเส้น; Random Forest และ neural models เป็น comparator ที่ปรากฏใน development history ไม่ใช่ว่าทุกตัวถูกฝึกบน protocol V2R1 [thesis_rebuild/03_คู่ผู้ใช้ถึงคะแนน.md:26–36; experiment lineage report 02]

V2 runner ระบุ GradientBoostingClassifier 300 trees, learning_rate 0.05, max_depth 6, random_state 42 ใช้ negatives TRAIN ได้สูงสุดสามเท่าของ positives; GB-17 และ GB-18 ใช้ sampled train indices เดียวกัน และ fit isotonic บน CALIBRATION แยกจาก TRAIN [experiments/icsec_final/authoritative_run_v2/final_runner.py:22–37,149–174] นี่คือข้อกำหนด source ไม่ใช่คำกล่าวว่า Phase 1 ได้ retrain แล้ว

## 7. Calibration ทำอะไร และไม่ได้ทำอะไร

คะแนน 0.9 จาก classifier ไม่รับประกันว่าคู่ระดับนั้นถูก 90% Calibration เรียนฟังก์ชันแปลง raw scores เป็น probability-like scores จาก labels อีกชุด Isotonic เป็นฟังก์ชันไม่ลดและมี plateau จึงมีหลายคู่ได้คะแนนเดียวกัน [experiments/icsec_final/authoritative_run_v2/final_runner.py:149–163; docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:80–88]

Calibration ไม่ใช่การแก้ blocking misses และไม่ใช่การฝึก feature representation ใหม่ หาก fit calibrator และวัดบนชุดเดียวกัน ค่าดังกล่าวเป็น in-sample diagnostic ไม่ใช่หลักฐาน generalization สาย production เดิมใช้ val หลายหน้าที่และ fit TF-IDF ทุกโปรไฟล์ ส่วน V2 แยก calibration กับ policy validation แต่อัตราบวกแต่ละ role ยังต่างกันเพราะ cohort size [docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:64–84]

## 8. Decision policy และ GA ทำหน้าที่ไหน

MATCH = รวมอัตโนมัติตามกฎ; REVIEW = พักให้ตรวจต่อ ไม่ใช่ยืนยันว่าเป็นคนเดียวกันแล้ว; NO_MATCH = ไม่รวมตาม policy ณ รอบนั้น REVIEW ในผลทดลองเป็น deferred decision ไม่มี measured human adjudication ที่ทำให้ทุก REVIEW กลายเป็นคำตอบถูก [docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:122–141]

V2 B0 กำหนด MATCH เมื่อ p≥0.98, REVIEW เมื่อ 0.95≤p<0.98, นอกนั้น NO_MATCH B1 ค้นสอง thresholds ด้วย Sobol; B2/B3 ใช้ four-parameter class เดียวกัน `[t_match,t_review,c_promote,c_demote]` ใน review band ถ้า name_sim≥c_promote จะ promote เป็น MATCH; ถ้าต่ำกว่า c_demote เป็น NO_MATCH B2 ใช้ Sobol ส่วน B3 ใช้ GA [experiments/icsec_final/authoritative_run_v2/policies.py:10–37,53–78,93–118]

GA ย่อ Genetic Algorithm สร้าง population ของ parameter vectors ประเมิน objective เลือก parents/mutate และติดตาม incumbent มันไม่เปลี่ยน fitted GB เมื่อ optimize downstream policy ในสาย V2 ทั้ง B2/B3 ใช้ 12,000 actual evaluations บน policy-validation และ frozen scorer [experiments/icsec_final/authoritative_run_v2/final_runner.py:177–203] V2 GA ไม่มี crossover;เลือก top 20% แล้วเติม population จากกลุ่มนั้นก่อน mutation σ=.02 ด้วยโอกาส .30 ต่อ gene แม้ elite rows ก็ถูก mutate จึงไม่ควรใช้คำอธิบาย R1 GA แทน V2 [experiments/icsec_final/authoritative_run_v2/policies.py:93–118]

10-gene GA คือ policy อีกแบบ: สอง thresholds + แปด weights ของ probability/name/bio/URL/location/social/image/style โดยรวม score แบบ availability-conditioned weighted mean `sum(score*mask*weight)/sum(mask*weight)` หากไม่มี effective evidence คง REVIEW ส่วน four-parameter GA ใช้ name evidence แค่ใน review band นี่เป็น policy class ต่างกัน ไม่ใช่การเปรียบเทียบ optimizer เดียวกันโดยเพิ่มความละเอียด [experiments/code/run_feature_aware_ga_pipeline.py:32–43,274–339]

Model coefficients ไม่เท่ากับ GA weights ตัวอย่าง logistic coefficients ถูกเรียนจาก TRAIN ใน feature-aware pipeline ขณะที่ policy ถูกเลือกอีกขั้นบน validation; อย่าเขียนว่า GA ฝึก neural network หรือ Gradient Boosting หากไม่ได้ทำจริง [experiments/code/run_feature_aware_ga_pipeline.py:189–222]

## 9. คิด Precision, Recall, F1 และ Utility อย่างไร

นิยามจาก three-action policy และ scope ทั้ง workflow:

- TP: positive ที่ MATCH; FP: negative ที่ MATCH
- FN: positive ที่ NO_MATCH รวม blocking misses
- R+: positive ที่ REVIEW; R−: negative ที่ REVIEW; REVIEW=R++R−
- Precision=TP/(TP+FP)
- Automatic recall=TP/(TP+FN+R+)
- Automatic F1=2TP/(2TP+FP+FN+R+)
- Decision-conditional recall=TP/(TP+FN)
- Decision-conditional F1=2TP/(2TP+FP+FN)
- U=2FP+FN+0.1REVIEW: เป็น loss ยิ่งต่ำยิ่งดี ไม่ใช่ utility ที่ยิ่งมากยิ่งดี

สูตร automatic เป็นข้อกำหนด protocol ใหม่ ส่วน frozen V2 headline เดิมคำนวณ conditional recall/F1; R-series evaluate ใช้ total_pos จึงห้ามเหมาว่าทุกสายตัด REVIEW ออกจาก denominator [docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:124–137; experiments/icsec_final/authoritative_run_v2/final_runner.py:52–62; experiments/code/exp_lib.py:130–140]

ตัวอย่างประกอบที่คำนวณด้วย `illustrative_metrics.json`: positive 10 คู่; TP=6, FN=2, R+=2, FP=1, R−=3 จะได้ precision 0.857143, automatic recall 0.6, conditional recall 0.75, automatic F1 0.705882, conditional F1 0.8, U=4.5 ถ้าย้าย FN หนึ่งคู่ไป REVIEW แต่ไม่เพิ่ม MATCH automatic recall/F1 เท่าเดิม ขณะที่ conditional recall/F1 สูงขึ้น และ U ลดเหลือ 3.6 นั่นคือประโยชน์จากการพักการตัดสิน ไม่ใช่จับคู่เพิ่ม

ค่าสัมประสิทธิ์ 2/1/.1 เป็น scenario assumption; source business_cost ตั้งชื่อ `crm_derived_v1` และ docstring อ้างค่าจ้าง แต่ Phase 1 ไม่มีเอกสารค่าต้นทุนจริงให้รับรอง [src/identity_resolution/core/business_cost.py:8–17; docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:150–155] จึงต้องรายงาน TP/FP/FN/REVIEW ร่วม ไม่ยกผู้ชนะ U เป็นผู้ชนะทุกสถานการณ์

## 10. ประวัติทดสอบอะไรและเราควรเชื่ออะไร

R0 baseline → R1 policy search; R2 เพิ่ม MiniLM → R3 ปรับ policy หลัง representation เปลี่ยน; R4/R5 Bloom privacy; R6 semantic blocking เป็น development branches ที่ต้องใช้ matrix 02 เพื่อระบุรุ่นจริง ไม่เรียกชื่อ R-series ว่าเดียวกับ V2 B0–B3 [experiments/REPORT_R0_R5.md; docs/GETTING_STARTED_TH.md:75–98]

Multimodal เปรียบเทียบ representation และ sampled-pair classifier; V2/V2R1 แยก entity roles และ scorer/policy; 10-gene มี sampled กับ full-cache projection คนละ scope ผลบน full population ที่รวม development rows ไม่ใช่ unseen generalization [docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:23–32,43–55]

สิ่งที่เรียนรู้ได้คือ threshold tuning/REVIEW เปลี่ยน trade-off, retrieval เป็นเพดาน recall, feature definition และ calibration prior มีผล ส่วนการชนะของ GA โดยทั่วไป, ประโยชน์ธุรกิจจริง, raw-to-result reproducibility และสิทธิข้อมูลยังไม่ถูกพิสูจน์ ค่ารายวิธีและ winner แบบมี scope อยู่รายงาน 04 ไม่ใช้คู่มือนี้สร้างตารางตัวเลขแข่งข้ามสาย

## 11. ทำไมต้องออกแบบใหม่

การแบ่งเฉพาะ entity ฝั่ง a ยังทำให้อีกปลายรั่ว; score cache ที่สร้างก่อน split อาจมี scorer เคยเห็น entity; learned preprocessing fit ทุกข้อมูลทำให้ inductive evaluation ไม่สะอาด; positive REVIEW ทำให้ headline conditional F1 สูงแม้ยังไม่ MATCH; bounds/policy class ที่เปลี่ยนพร้อม optimizer ไม่ระบุเหตุของ gain [docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:34–91,109–141]

รอบใหม่จึงต้องล็อก snapshot/IDs, split ทั้งสองปลาย, train-only preprocessing, calibration และ policy selection คนละ role, fixed candidate cohort, complete exact/scored/miss accounting และ random/Sobol/GA บน class/budget เดียวกัน โดยยอมรับผลว่า GA อาจไม่มีประโยชน์เพิ่ม [docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:18–48,67–120]

รายงาน Phase 1 นี้อ่านและคำนวณจากสิ่งที่เก็บไว้เท่านั้น ไม่มี training, embedding regeneration, calibration refit, policy optimization หรือ Phase 2 execution การรู้ข้อจำกัดเป็นผลลัพธ์ที่ต้องการ ไม่ใช่ความล้มเหลวเพราะไม่ได้เพิ่มคะแนน
