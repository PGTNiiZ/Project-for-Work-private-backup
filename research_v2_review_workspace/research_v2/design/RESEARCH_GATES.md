# Research Gates — Research V2 (v2 reconciled)

## Changes vs v1

| # | การเปลี่ยนแปลง | หลักฐาน |
|---|---|---|
| RG1 | G0: BLOCKED → **PARTIAL (NOT VERIFIED)** — กลไกที่ project ได้ `user_folder` (ชื่อ folder ของ dataset ต้นทาง) และแหล่ง (LinkSocial [P38]) มีหลักฐาน; วิธีที่ LinkSocial สร้าง label, ผู้สร้าง, error rate, license ไม่มีเอกสาร; gitlink `fe67dd1` ไม่พบใน repo upstream | [BACKUP@ab93b36:src/identity_resolution/stages/prepare.py#L28-L69 load_all_profiles]; [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/DATA_GOVERNANCE.md#L3]; `review/_work/agentB/LIT_NOTES.md` §6 |
| RG2 | G1: ยัง **BLOCKED** — ไม่พบเอกสารอนุญาตใด ๆ; repo เดิมบันทึกเองว่า Gate 8 "PENDING HUMAN APPROVAL"; **เพิ่มเกณฑ์: แก้การเผยแพร่ข้อมูลส่วนบุคคลใน repo สาธารณะ** | [BACKUP@ab93b36:handoff/worktrees/research-phase15-integration/docs/research_rebuild/phase_01_5/gate_08/DATA_GOVERNANCE_ASSESSMENT.md#L3]; `gh repo view` → PUBLIC ทั้งสอง repo |
| RG3 | G2: เพิ่มเกณฑ์ label-proxy audit (สัดส่วน positive ที่ username ตรงกัน/URL ชี้ข้ามแพลตฟอร์ม) | exact tier TP 12,340 / FP 63 [BACKUP@ab93b36:docs/research_rebuild/phase_01/01_DATASET_AND_FEATURE_LINEAGE.md#L130] |
| RG4 | G3: split = entity-atomic 5 folds ขนาดเท่ากัน + ตรวจ prior ของ OOF vs test | `EXPERIMENTAL_MASTER_PLAN_TH.md` §11 |
| RG5 | G5: **fresh-holdout ไม่ผ่านด้วยข้อมูลเดิม** (test md5 เดิมถูกใช้ ≥15 ครั้งใน MAIN; ICSEC v1/v2/v2r1/reviewer ใช้ test 3 ชุดซ้ำ) | `review/HISTORICAL_EXPERIMENT_AUDIT.md` A6; [BACKUP@ab93b36:experiments/icsec_final/reviewer_revision/PROTOCOL.md#L3] |
| RG6 | เพิ่ม mapping กับ Gate 1–9 ของ Phase 1.5 ใน backup (งานเดิมที่ทำต่อเนื่อง) | [BACKUP@ab93b36:handoff/worktrees/research-phase15-integration/docs/research_rebuild/phase_01_5/GATE_STATUS_MATRIX.md#L3-L15] |

---


**สถานะรวมปัจจุบัน (2026-10-25, หลังตรวจ repository): NO-GO สำหรับการทดลองทางวิทยาศาสตร์ทั้งหมด** — ไม่พบหลักฐาน G0/G1 ที่เพียงพอ
**GO สำหรับ:** งานเอกสาร, การตรวจ repository เชิงโค้ด (ถ้าไม่มีข้อมูลส่วนบุคคล), การเขียน evaluation harness, smoke test บนข้อมูลสังเคราะห์

---

## สรุปสถานะ

| Gate | ชื่อ | สถานะ | ปลดล็อก |
|---|---|---|---|
| G0 | Ground-truth provenance | **PARTIAL / NOT VERIFIED** — แหล่ง = LinkSocial [P38]; วิธีสร้าง label/ผู้สร้าง/license ไม่มีเอกสาร; Phase 1.5 Gate 3 "NOT VERIFIED" | G1 |
| G1 | Data-use authorization & privacy | **BLOCKED** — ไม่มีเอกสารอนุญาต; repo สาธารณะมีข้อมูลส่วนบุคคล; Phase 1.5 Gate 8 "PENDING HUMAN APPROVAL" | D0 ทั้งหมด |
| G2 | Data dictionary & label policy | NOT STARTED | G3 |
| G3 | Split freeze & test lock | NOT STARTED | G4 |
| G4 | Pre-registration freeze | NOT STARTED | T1–T6 |
| G5 | Final-config declaration & fresh-holdout | NOT STARTED — **fresh-holdout จะไม่ผ่านด้วยข้อมูลเดิม** | T7 (เปิด test) |
| GX-T8 | Threat model + ethics สำหรับการทดลองโจมตี | NOT STARTED | T8 |
| GX-T9 | สิทธิ์ใช้ภาพ/biometric | NOT STARTED | T9 |

---

## G0 — Ground-truth Provenance

**คำถาม:** label ทุกคู่มาจากไหน และเชื่อถือได้แค่ไหน

เกณฑ์ผ่าน (ต้องครบ):
- [ ] เอกสารระบุแหล่งที่มาของ positive (เช่น ลิงก์ข้ามแพลตฟอร์มที่ผู้ใช้ประกาศเอง, การ annotate ด้วยมือ, ชุดข้อมูลภายนอก) พร้อมวันที่และผู้รับผิดชอบ
- [ ] ระบุว่า negative มาจากไหน (ยืนยันจริง หรือ "ไม่มี label")
- [ ] ระบุว่ากลไกการสร้าง label ใช้ feature/blocking ใดของระบบที่จะทดสอบหรือไม่ (selection bias)
- [ ] เวอร์ชันและ hash ของไฟล์ label
- [ ] ถ้ามาจากชุดข้อมูลภายนอก: license และเงื่อนไขการใช้

**ถ้าไม่ผ่าน:** ห้ามทำ D0 เชิงตัวเลข; ทำได้เพียงสืบค้นเอกสาร

## G1 — Data-use Authorization และ Privacy

เกณฑ์ผ่าน:
- [ ] หลักฐานสิทธิ์ใช้ข้อมูล (ToS ของแพลตฟอร์ม/สัญญา/ความยินยอม) สำหรับวัตถุประสงค์งานวิจัยนี้
- [ ] การพิจารณาด้านจริยธรรม (IRB/คณะกรรมการจริยธรรมการวิจัยในมนุษย์ของสถาบัน) หรือหนังสือยกเว้น
- [ ] การประเมินตามกฎหมายคุ้มครองข้อมูลส่วนบุคคลที่ใช้บังคับ (เช่น PDPA ของไทย หากเกี่ยวข้อง): ฐานทางกฎหมาย, data minimization, ระยะเวลาเก็บ, ผู้มีสิทธิ์เข้าถึง — *ไม่ใช่คำแนะนำทางกฎหมาย ควรปรึกษาเจ้าหน้าที่คุ้มครองข้อมูลของสถาบัน*
- [ ] นโยบาย: ห้ามส่งข้อมูลโปรไฟล์ไปบริการภายนอก (รวม LLM API) โดยไม่มีอนุมัติเฉพาะ
- [ ] นโยบาย: ห้ามเผยแพร่ตัวอย่างบัญชีที่ระบุตัวตนได้ในเล่ม (ใช้ตัวอย่างสังเคราะห์/ปิดบัง)
- [ ] ข้อจำกัดการใช้ผลลัพธ์ (dual-use: การเชื่อมโยงตัวตนอาจถูกใช้ติดตามบุคคล) ระบุใน Ethics Statement

## G2 — Data Dictionary และ Label Policy

เกณฑ์ผ่าน:
- [ ] Datasheet (P33) สำหรับแต่ละแพลตฟอร์ม: attribute, ชนิด, missingness, ภาษา (จาก D0-2)
- [ ] Label policy: นิยาม positive/negative/unlabeled; การจัดการ 1:n
- [ ] ผล D0-1: κ ≥ 0.80 บน positive sample (เกณฑ์เสนอ) หรือแผนแก้ไขถ้าต่ำกว่า
- [ ] ผล D0-3: ค่าประมาณ π_hidden พร้อม CI
- [ ] ตัดสินเรื่อง "label-proxy features" (เช่น URL ข้ามแพลตฟอร์ม) — รวม/ไม่รวม/รายงานทั้งสองแบบ

## G3 — Split Freeze และ Test Lock

เกณฑ์ผ่าน:
- [ ] Split manifest (identity → split) พร้อม SHA-256
- [ ] D0-4: 0 identity ข้าม split; รายงานบัญชีซ้ำ
- [ ] Test เก็บแยกสิทธิ์; evaluation script บังคับ flag `--final` และบันทึก log การเปิด
- [ ] ระบุว่า test ทับกับข้อมูลที่ใช้ใน R0–R6 หรือไม่ (ข้อมูลสำหรับ G5)

## G4 — Pre-registration Freeze

เอกสารที่ต้อง freeze (บันทึก SHA-256 + วันที่ + ผู้ลงนาม):
- [ ] `RESEARCH_QUESTIONS_AND_HYPOTHESES.md` (H1–H5, SESOI สุดท้าย)
- [ ] `EVALUATION_AND_STATISTICS.md` (metrics, contrasts, Holm, bootstrap B, TOST)
- [ ] Cost model (c_FP, c_FN, c_R) และเหตุผล
- [ ] k*, P_target, B_search, GA config, seeds
- [ ] Inclusion rules ของ conditional experiments
- [ ] Pilot variance check (power) ผ่าน หรือมีการปรับ SESOI ที่ประกาศ

| ไฟล์ | SHA-256 | วันที่ | ผู้ลงนาม |
|---|---|---|---|
| (เติมเมื่อ freeze) | | | |

## G5 — Final-config Declaration และ Fresh-holdout

เกณฑ์ผ่าน:
- [ ] รายการ configuration ที่จะประเมินบน test (REF, BEST-VAL, 8 cells ของ E7-2) ประกาศพร้อม hash ของ model artifacts
- [ ] Experiment ledger ครบ (รวม run ที่ล้มเหลว)
- [ ] **Fresh-holdout check:** test ไม่ทับกับ identity ที่เคยใช้ประเมินใน R0–R6 **หรือ** ข้อสรุปทั้งหมดถูกลดระดับเป็น exploratory (ระบุในบทคัดย่อ)
- [ ] ผู้ตรวจอิสระ (อาจารย์ที่ปรึกษา/เพื่อนร่วมทีม) ยืนยันว่าไม่มีการเปิด test ก่อนหน้า

## GX-T8 / GX-T9 — Extension Gates

- T8: threat model (ผู้โจมตีรู้อะไร, มี auxiliary data อะไร), อนุมัติจริยธรรมสำหรับการจำลองการโจมตี, ห้ามเผยแพร่ค่าที่ re-identify ได้
- T9: สิทธิ์การใช้ภาพโปรไฟล์, การจัดการข้อมูลชีวมิติ (ใบหน้า) ตามกฎหมาย, coverage ≥ 50%

---

## ผู้มีอำนาจตัดสิน gate (ต้องกำหนด)

| Gate | ผู้ตัดสิน (เสนอ) |
|---|---|
| G0, G2 | ผู้วิจัย + อาจารย์ที่ปรึกษา |
| G1, GX | คณะกรรมการจริยธรรม / DPO ของสถาบัน |
| G3, G4, G5 | ผู้วิจัย + ผู้ตรวจอิสระ |


---

## หลักฐานที่ต้องได้เพื่อปลดล็อกแต่ละ gate (v2)

| Gate | หลักฐานที่มีแล้ว (V-REPO) | หลักฐานที่ยังขาด → ปลดล็อกเมื่อ |
|---|---|---|
| G0 | GT = ชื่อ folder ของ LinkSocial; 15,297 entities; mapping user_folder↔profile_id ไม่ขัดแย้ง [BACKUP@ab93b36:docs/research_rebuild/phase_01/01_DATASET_AND_FEATURE_LINEAGE.md#L100-L108] | เอกสารวิธีสร้าง label ของ LinkSocial (จาก paper เต็ม P38 หรือติดต่อผู้เขียน), snapshot ที่ระบุ commit จริงของ dataset (fe67dd1 ไม่พบใน upstream), การตัดสินเรื่อง label-proxy, ลงนามโดยที่ปรึกษา |
| G1 | repo เดิมบันทึกขอบเขต governance ไว้ชัด (ไม่อ้าง consent/IRB) [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/DATA_GOVERNANCE.md#L3-L14] | license/permission จากผู้สร้าง LinkSocial (repo ไม่มี license file), การพิจารณาจริยธรรม/IRB หรือหนังสือยกเว้น, การประเมิน PDPA, **การตัดสินใจของเจ้าของเรื่องการเผยแพร่ข้อมูลส่วนบุคคลใน repo PUBLIC** (ภาพ 4,248 ไฟล์, CSV โปรไฟล์, `customer_360.json`) |
| G2 | datasheet บางส่วน (schema stats) | D0-1 κ, D0-3 π_hidden, label-proxy decision |
| G3 | โค้ด split + entity-overlap assert ใช้ซ้ำได้ [MAIN@1e0a2db:exp_lib.py#L166-L221] | split manifest ใหม่ + hash; D0-4 = 0 overlap |
| G4 | Gate 9 draft (P0–P5, 2,048 calls) ใน backup เป็นจุดตั้งต้น [BACKUP@ab93b36:handoff/worktrees/research-phase15-integration/docs/research_rebuild/phase_01_5/gate_09/EXPERIMENT_CONFIG_V1.json] | เอกสารที่ freeze พร้อม hash/ผู้ลงนาม |
| G5 | — | ข้อมูล holdout ใหม่ที่ไม่เคยถูกใช้ **หรือ** การประกาศลดระดับข้อสรุปทั้งหมดเป็น exploratory |
