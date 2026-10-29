# คำถามวิจัยและสมมติฐาน — Research V2 (v2, reconciled 2026-10-25)

## Changes vs v1

| # | การเปลี่ยนแปลง | หลักฐาน |
|---|---|---|
| C1 | นิยาม 1:1 ใน §0 เปลี่ยนจาก UNKNOWN → "เกือบ 1:1": entity ที่มี >1 บัญชีบนแพลตฟอร์มเดียว 4/15,297 (0.03%); singleton 1,526 entity | สถิติ schema ใน `review/REPOSITORY_RESEARCH_INVENTORY.md` §5 |
| C2 | H1 primary contrast ระบุให้ชัด: **E5-1 (= E3-2, lexical ทุกกลุ่ม) vs best E5-5 (lexical กลุ่มเดียว)** — ตัดความกำกวม "E5-3 (หรือ E5-1)" ของ v1 เพื่อให้ H1 ไม่ขึ้นกับผลของ H3 | `review/HYPOTHESIS_COVERAGE_REVIEW.md` H1 |
| C3 | H3a ไม่สันนิษฐานภาษาไทย/ถอดเสียงอีกต่อไป: ข้อมูลมาจาก LinkSocial (Twitter/Google+/Instagram) [P38] และไม่มีหลักฐานใน repo หรือ literature ว่ามีภาษาไทย → stratum ภาษาเป็น CONDITIONAL ตาม D0-2 | [P38]; [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/DATA_GOVERNANCE.md#L3]; `review/RESEARCH_GAP_VALIDATION.md` G-4 |
| C4 | H4 cost model: ค่าตั้งต้นเปลี่ยนจาก 5:1, c_R = 0.2·c_FN (สมมติ) → **ผู้สมัครหลัก crm_derived_v1 = c_FP:c_FN:c_R = 2:1:0.1** ที่มีเอกสารที่มาใน repo; ค่า 5:1:0.02 ของ R-series เป็น sensitivity (ทั้งสองยังต้อง freeze/ยืนยันโดยเจ้าของโจทย์ที่ G4) | [BACKUP@903246c:src/identity_resolution/core/business_cost.py#L1-L31 CRM_COST_WEIGHTS]; [BACKUP@ab93b36:docs/reports/2608-update-project2/CRM_COST_MODEL_TH.md]; [MAIN@1e0a2db:exp_r1_ga_redecision.py#L15] |
| C5 | H4b: optimizer ที่ไม่ใช่ GA = random search + **scrambled Sobol** + TPE; budget = **2,048** objective evaluations (2^11 เพื่อรักษาสมบัติ balance ของ Sobol; v1 = 2,000); policy space หลัก = genome 4 ยีนของ GA เดิม (t_m, t_r, c_promote, c_demote) + space 2-threshold | [MAIN@1e0a2db:exp_r1_ga_redecision.py#L75-L113]; [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/BASELINE_PROTOCOL.md#L5-L12]; [P41, P42] |
| C6 | H4a เพิ่ม Chow/posterior-risk rule (closed-form three-way) เป็นส่วนของ E6-3 | [BACKUP@903246c:experiments/code/reviewer_revision.py]; [P25] |
| C7 | H5: budget หลัก = จำนวน candidate รวมเท่ากับ B0 (|C_B0| ≈ 2.09M คู่ HIST) แทน k ต่อบัญชีเพียงอย่างเดียว เพราะ key blocking (B0) ไม่มี k โดยธรรมชาติ; ยังรายงาน PC–|C| และ PC@k | [MAIN@1e0a2db:EXPERIMENT_PLAN.md#L26-L33]; [P12, P45] |
| C8 | เพิ่ม §6 "หลักฐานประวัติศาสตร์ต่อสมมติฐาน" (V-REPO แทน HIST-UNVERIFIED) และ DQ7 (historical artifact re-analysis, D0-5) | `review/HISTORICAL_EXPERIMENT_AUDIT.md` |
| C9 | นิยาม end-to-end recall ระบุให้นับ positive ที่ถูกส่ง REVIEW เป็น "ไม่ถูกเชื่อมอัตโนมัติ" (ตาม M1 ของ reviewer revision) และรายงาน decision-recall แยก | [BACKUP@ab93b36:experiments/icsec_final/reviewer_revision/PROTOCOL.md#L5] |

---


สถานะ: **PROPOSED** · ต้อง freeze ที่ Gate G4 (pre-registration) ก่อนเปิดดูผลบน validation ชุดใดก็ตาม

---

## 0. นิยามร่วม (ใช้ทุกสมมติฐาน)

| สัญลักษณ์/คำ | นิยามเชิงปฏิบัติการ |
|---|---|
| **บัญชี (account)** | โปรไฟล์หนึ่งรายการบนแพลตฟอร์มหนึ่ง (A หรือ B) |
| **Identity / entity** | บุคคลจริงหนึ่งคนตาม ground truth; หนึ่ง identity อาจมีบัญชีบนแต่ละแพลตฟอร์ม 0..n บัญชี (สถิติ schema พบว่า **เกือบ 1:1**: 4/15,297 entity มี >1 บัญชีบนแพลตฟอร์มเดียว; 1,526 entity มีบัญชีเดียว — ยืนยันซ้ำใน D0-2) |
| **คู่จริง (positive pair)** | (a, b) ที่ ground truth ยืนยันว่าเป็น identity เดียวกัน |
| **Confirmed negative** | คู่ที่ ground truth ยืนยันว่า *ไม่ใช่* identity เดียวกัน |
| **Unlabeled pair** | คู่ที่ไม่มีการยืนยันทั้งสองทาง (ห้ามถือเป็น negative โดยอัตโนมัติ — ดู E7-6) |
| **Candidate set C(k)** | ชุดคู่ที่ blocker ส่งต่อ โดย budget = k คู่ต่อบัญชีฝั่ง B (หรือขนาดรวม |C| เท่ากันระหว่าง blocker) |
| **Candidate-level metric** | วัดเฉพาะคู่ใน C(k) |
| **End-to-end metric** | ตัวหารของ recall = คู่จริง *ทั้งหมด* ใน test (รวมคู่ที่ blocker ตกหล่น) |
| **Frozen protocol** | split, feature definition, metric, cost model, SESOI และการทดสอบทางสถิติที่ลงนาม hash ไว้ที่ G4 |
| **SESOI** | Smallest Effect Size Of Interest — ผลต่างขั้นต่ำที่ถือว่ามีความหมายเชิงปฏิบัติ (ค่าตั้งต้นเสนอด้านล่าง ปรับได้ครั้งเดียวที่ G4 จากความแปรปรวนใน pilot ของ D0) |

## 1. คำถามวิจัย

- **RQ0 (diagnostic):** ข้อมูลและ ground truth ที่มีอยู่รองรับข้อสรุปแบบใดได้บ้าง (provenance, ความครบของ label, missingness, ภาษา, ความสัมพันธ์ 1:1)
- **RQ1:** การใช้หลาย profile attribute ร่วมกันให้คุณภาพการจับคู่ดีกว่า attribute เดี่ยวที่ดีที่สุดหรือไม่ และ attribute กลุ่มใดเติมเต็มกัน
- **RQ2:** เมื่อใช้ feature ชุดเดียวกัน learned matcher ดีกว่า rule-based matcher ที่ถูก tune อย่างยุติธรรมหรือไม่
- **RQ3:** semantic representation เพิ่มคุณภาพเหนือ lexical representation หรือไม่ ในกลุ่มข้อมูลใด และคุ้มค่ากับต้นทุนหรือไม่
- **RQ4:** decision policy ที่ optimize ตามต้นทุนลด expected cost ได้มากกว่า baseline หรือไม่ และ GA ให้ประโยชน์เพิ่มจาก optimizer ที่ไม่ใช่ GA หรือไม่
- **RQ5:** candidate generation แบบ semantic/hybrid กู้คู่จริงที่ lexical blocking ตกหล่นได้หรือไม่ ภายใต้ budget เท่ากัน และส่งผลต่อ end-to-end recall เท่าไร

---

## 2. สมมติฐาน (falsifiable, operational)

> รูปแบบ: H_x (ทางเลือก) vs H_x,0 (ศูนย์) · ตัวชี้วัดหลัก · การเปรียบเทียบ · SESOI · กฎการตัดสิน · เงื่อนไขที่ทำให้สมมติฐานถูกปฏิเสธ
> การตัดสินทั้งหมดใช้ **ผลต่างแบบ paired บน test ที่ล็อกไว้** พร้อม **95% CI จาก entity-grouped bootstrap** (B = 2,000) และปรับ multiplicity ด้วย Holm ข้าม 5 สมมติฐานหลัก (ดู `EVALUATION_AND_STATISTICS.md`)

### H1 — Feature Complementarity

- **H1:** เมื่อคง learner (GBDT ที่ตั้ง hyperparameter ด้วย validation เดียวกัน) และ candidate set C(B*) ให้เหมือนกัน matcher ที่ใช้ **lexical feature ของ attribute ทุกกลุ่ม** (E5-1 = E3-2) จะมี **PR-AUC (candidate-level)** สูงกว่า matcher ที่ใช้ attribute กลุ่มเดียวที่ดีที่สุด (เลือกบน validation) อย่างน้อย SESOI
- **H1,0:** ΔPR-AUC ≤ SESOI
- **SESOI เสนอ:** ΔPR-AUC = 0.02
- **การทดลอง:** E5-1 (= E3-2, all lexical groups) vs best E5-5 (single lexical group, เลือกบน validation) — primary; E5-4 (leave-one-group-out บน E5-3) เป็น explanatory
- **ตัวชี้วัดรอง:** Recall @ Precision ≥ P_target, จำนวน FP, ผลใน stratum ที่ attribute หายไป
- **ปฏิเสธ H1 เมื่อ:** ขอบล่าง 95% CI ของ Δ < SESOI; ถ้า CI อยู่ภายใน [−SESOI, +SESOI] ทั้งหมด (TOST) → สรุปว่า "เทียบเท่าในทางปฏิบัติ"
- **ข้อแม้:** ถ้า missingness ของ attribute หนึ่ง > 50% ในแพลตฟอร์มใด ต้องรายงานแยก stratum

### H2 — Learned vs Rule-based Matching

- **H2:** ด้วย lexical feature ชุดเดียวกัน (E2-1) learned matcher (LR หรือ GBDT, เลือกหนึ่งตัวล่วงหน้าเป็น primary = **GBDT**) มี PR-AUC สูงกว่า rule-based matcher ที่ **น้ำหนักและ threshold ถูก tune บน validation** (E2-3) อย่างน้อย SESOI
- **H2,0:** ΔPR-AUC ≤ SESOI
- **SESOI เสนอ:** 0.02 PR-AUC และรายงาน ΔF1 ที่ threshold cost-optimal ของแต่ละตัว
- **การทดลอง:** E3-2 vs E2-3 (primary); E3-1 vs E2-3, E2-2 (historical replica) เป็นข้อมูลประกอบ
- **ความยุติธรรม:** rule-based ต้องได้ tuning budget (จำนวน configuration ที่ประเมิน) ไม่น้อยกว่า learner — ห้ามเทียบ learner ที่ tune แล้วกับ rule ที่ตั้งด้วยมือเท่านั้น
- **ตัวชี้วัดรอง:** training time, inference ms/1k คู่, ความไวต่อขนาด training set (learning curve 10/25/50/100%)

### H3 — Semantic Representation Contribution

- **H3:** เมื่อคง learner และ candidate set ให้เหมือนกัน การเพิ่ม semantic feature (cosine จาก frozen bi-encoder ต่อ attribute ข้อความ) เข้าไปใน lexical feature (E5-3) ให้ PR-AUC สูงกว่า lexical-only (E5-1) อย่างน้อย SESOI
- **H3,0:** ΔPR-AUC ≤ SESOI
- **SESOI เสนอ:** 0.01 PR-AUC (ต่ำกว่า H1/H2 เพราะเป็นส่วนเพิ่ม) **และ** ต้องรายงาน cost ratio (ms/คู่ ของ E5-3 ÷ E5-1)
- **Sub-hypothesis H3a (heterogeneity):** ประโยชน์ของ semantic มากกว่าใน stratum ที่ชื่อ/username ต่างกันตามตัวอักษร (เช่น username_jaro < 0.5) หรือ bio ยาว — stratum ภาษา/สคริปต์ทำเฉพาะเมื่อ D0-2 พบความหลากหลายของภาษาพอ (ไม่สันนิษฐานภาษาไทย) เทียบกับ stratum ที่ username ตรงกันตามตัวอักษร (interaction test ผ่าน bootstrap ของ difference-in-differences) — **exploratory** ไม่นับใน Holm
- **Sub-hypothesis H3b (fine-tuning):** fine-tuned encoder (E4-3/E4-4) ดีกว่า frozen (E4-1) — ทำเฉพาะเมื่อผ่านเกณฑ์ inclusion ของ T4
- **การทดลอง:** E5-1, E5-2, E5-3 (กับ LR และ GBDT), E4-1…E4-4
- **ปฏิเสธ H3 เมื่อ:** ขอบล่าง CI < SESOI → รายงานว่า semantic ไม่ให้ประโยชน์ที่มีความหมายบนข้อมูลนี้ (เป็นผลที่ยอมรับได้)

### H4 — Decision Optimization และ Cost-sensitive Matching

- **ต้องกำหนดก่อน (G4):** cost model `c_FP` (false merge), `c_FN` (missed link), `c_R` (ต้นทุน review ต่อคู่) — ผู้สมัครค่าหลัก = **crm_derived_v1: c_FP : c_FN : c_R = 2 : 1 : 0.1** (มีเอกสารที่มาจากต้นทุนงาน CRM ใน repo [BACKUP@903246c:src/identity_resolution/core/business_cost.py#L8-L31]) และ sensitivity ที่ {1:1:0.1, 5:1:0.02 (ค่า R-series), 10:1:0.1} — ค่าที่ใช้จริงต้องยืนยันโดยเจ้าของโจทย์ที่ G4
- **H4a:** cost-optimal threshold จาก calibrated probability (E6-3) ให้ **expected cost ต่อคู่** ต่ำกว่า fixed threshold (E6-1) อย่างน้อย SESOI
- **H4b (คำถามหลักเรื่อง GA):** GA (E6-5) ให้ expected cost ต่ำกว่า **baseline ที่ดีที่สุดในกลุ่ม non-GA** {E6-2, E6-3 (รวม Chow), E6-4 (random / scrambled Sobol / TPE)} อย่างน้อย SESOI ภายใต้ policy space เดียวกัน (genome 4 ยีนเดิม) และ **objective evaluations เท่ากัน = 2,048**; หลักฐานประวัติศาสตร์ (ICSEC v2) ชี้ว่า GA ≈ Sobol (ΔU = 1.8, อยู่ใน SD, 3 partitions, ไม่มี CI) จึงคาดล่วงหน้าว่าผลอาจเป็น 'เทียบเท่า' (TOST)
- **H4c (three-way):** policy แบบ match/review/non-match (E6-6) ให้ expected cost (รวม review) ต่ำกว่า two-way ที่ดีที่สุด
- **H4,0:** Δcost ≤ SESOI สำหรับแต่ละข้อ
- **SESOI เสนอ:** ลด expected cost ≥ 5% (relative)
- **ตัวชี้วัดรอง:** false merges ต่อ 1,000 บัญชี, review rate, coverage (สัดส่วนที่ตัดสินอัตโนมัติ), seed variance ของ GA
- **ข้อแม้:** score ที่ป้อนทุก policy ต้องมาจาก matcher ตัวเดียวกัน (frozen) — H4 ทดสอบ *เฉพาะ policy* ไม่ใช่ representation

### H5 — Candidate Generation และ Blocking Recovery

- **H5:** ที่ candidate budget เท่ากัน (จำนวนคู่รวม = |C_B0| ของ historical blocker; รายงาน PC@k ประกอบ) hybrid retrieval (lexical ∪ dense, E1-5) มี **Pair Completeness PC@k** สูงกว่า lexical blocking ที่ดีที่สุด (max{E1-1, E1-2, E1-3}) อย่างน้อย SESOI และ **เมื่อส่งต่อให้ matcher ตัวเดียวกัน** ให้ end-to-end recall ที่ precision คงที่สูงขึ้น
- **H5,0:** ΔPC@k ≤ SESOI
- **SESOI เสนอ:** ΔPC@k = 0.02 หรือกู้คืน ≥ 10% ของคู่จริงที่ lexical blocker ตกหล่น (เลือกเกณฑ์หนึ่งเป็น primary ที่ G4; ค่าตั้งต้น = ΔPC@k)
- **k หลัก:** เลือกบน validation เป็นค่าน้อยที่สุดที่ lexical baseline ให้ PC ≥ 0.95 หรือ k = 20 ถ้าไม่ถึง (ประกาศที่ G4); รายงานเส้นโค้ง PC–|C| เต็ม
- **ตัวชี้วัดรอง:** RR, PQ, blocking-missed positives ที่กู้คืนได้, เวลาสร้าง index/query
- **การทดลอง:** E1-1…E1-5 (candidate-level) → E7-1/E7-2 (end-to-end)

---

## 3. คำถามเชิงวินิจฉัย (Diagnostic Questions — ไม่ใช่สมมติฐาน)

| ID | คำถาม | การทดลอง |
|---|---|---|
| DQ0 | ground truth มาจากไหน ใครสร้าง ด้วยเกณฑ์ใด และได้รับอนุญาตใช้หรือไม่ | G0, G1 |
| DQ1 | ความครบของ label: สัดส่วน unlabeled, ความแม่นยำของ negative | D0-1, D0-3 |
| DQ2 | missingness และภาษาของแต่ละ attribute ต่อแพลตฟอร์ม | D0-2 |
| DQ3 | มีการรั่วไหลข้าม split หรือการซ้ำซ้อนของบัญชี/identity หรือไม่ | D0-4 |
| DQ4 | ข้อผิดพลาดที่เหลือเป็นแบบใด (taxonomy) | E7-7 |
| DQ5 | ผลไวต่อสมมติฐานของ label แค่ไหน | E7-6 |
| DQ6 | ต้นทุนการคำนวณของแต่ละ stage | E7-5 |

## 4. การวางแผนผลที่เป็นไปได้ (pre-committed interpretation)

| ผล | การตีความที่ยอมรับล่วงหน้า |
|---|---|
| H1 จริง, H3 ไม่จริง | attribute หลายชนิดสำคัญกว่าวิธีแทนข้อความ → ลงทุนที่การเก็บ attribute มากกว่าโมเดลใหญ่ |
| H2 ไม่จริง | rule ที่ tune ดีเพียงพอ; ML ไม่จำเป็นบนข้อมูลขนาดนี้ |
| H4b ไม่จริง | ใช้ closed-form/Bayesian search แทน GA ในระบบจริง; ผลประวัติ R1/R3 อาจมาจากการไม่มี baseline ที่ tune |
| H5 จริงแต่ end-to-end ไม่ดีขึ้น | คู่ที่กู้ได้เป็นคู่ยากที่ matcher ก็ตัดสินผิด → bottleneck อยู่ที่ matcher |
| ทุกข้อไม่จริง | รายงานเป็น negative result พร้อม protocol (C2) ซึ่งยังเป็น contribution |

## 5. สิ่งที่ห้ามอ้าง

- ห้ามอ้างว่า R3 หรือโมเดลใด "ดีที่สุดโดยทั่วไป" — ทุกข้อสรุปผูกกับชุดข้อมูล, split, cost model และ budget ที่ประกาศ
- ห้ามใช้ผล HIST-UNVERIFIED (เช่น F1 = 0.8373 ของ R3) เป็นหลักฐานยืนยันหรือปฏิเสธสมมติฐานใด
- ห้ามเลือกตัวชี้วัด, k, หรือ cost model หลังเห็นผล test


## 6. หลักฐานประวัติศาสตร์ต่อสมมติฐาน (V-REPO — ใช้เป็นแรงจูงใจเท่านั้น ไม่ใช่หลักฐานยืนยัน)

| H | หลักฐานที่พบ (lifecycle) | ข้อจำกัดที่ทำให้ยังไม่ตอบคำถาม |
|---|---|---|
| H1 | bigram + location: Δtop-1 0.000–+0.007 [MAIN@1e0a2db:data/processed/bigram_pipeline_results_with_location/bigram_vs_location_comparison.csv] (RESULT_ARTIFACT_FOUND); N0–N6 name-feature ablation validation F1 0.9410→0.9553 [BACKUP@ab93b36:artifacts/evaluation/name_similarity/N*/validation_metrics.json] (validation-only, คู่ balanced) | ไม่มี single-group vs all-group บน candidate set จริง; ไม่มี CI |
| H2 | ไม่พบ tuned rule baseline; F06 เทียบเฉพาะ learner หลายตัว (GB > RF > MLP > LR) บนคู่ sample [MAIN@1e0a2db:pub_multi/doc/model_compare.md] | rule baseline ไม่ถูก tune → H2 ยังไม่ถูกทดสอบ |
| H3 | GB-17 → GB-18 (+MiniLM): ICSEC v1 F1 0.8293 vs 0.8280 (เท่ากันในทางปฏิบัติ) [BACKUP@ab93b36:experiments/icsec_final/authoritative_run/AUTHORITATIVE_RESULTS.md#L41-L49]; v2 GB17_B0 0.8494 vs B0 (GB-18) 0.8510 [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/FINAL_RESULTS.md#L27-L33]; MAIN GB-17 0.5967 vs GB-18 0.8296 ที่ threshold มือ (ส่วนต่างเป็นผลของ threshold) | ผลขัดกันขึ้นกับ policy → ต้องเทียบที่ PR-AUC (threshold-free) |
| H4 | ICSEC v2: B1 tuned 2-threshold U 1864.6, B2 Sobol 1860.0, B3 GA 1858.2, Chow 1879.0, B0 fixed 2364.2 [BACKUP@ab93b36:experiments/icsec_final/reviewer_revision/aggregate.json] (ARTIFACT_CONSISTENT กับ paper); MAIN nested R1: GA F1 ↑ แต่ cost test สูงกว่า R0 +1.09% [MAIN@1e0a2db:experiments/automation/r1_nested_primary_20260809/summary.md] | 3 partitions × 1 optimizer seed; ไม่มี CI; calibration prior shift (CONFIRMED_DEFECT); test ถูกใช้ซ้ำ |
| H5 | R6 hash blocking กู้ได้ 4/3,316 (radius 1) [MAIN@1e0a2db:experiments/r6_blocking_recovery.json]; B0 PC 0.8867 [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/provenance/preflight_manifest.json#candidate_scope] | ไม่มี dense/sparse top-k ที่คุม budget; frozen backbone |

DQ7 (ใหม่): ผลประวัติศาสตร์ที่ต่างกันเล็กน้อย (เช่น R1 vs R3, B2 vs B3) เกินความแปรปรวนจากการสุ่ม entity หรือไม่ → D0-5 (OPTIONAL, exploratory, ต้องผ่าน G1)
