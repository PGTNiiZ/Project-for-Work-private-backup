# Research Gates — Research V2

**สถานะรวมปัจจุบัน (2026-10-25): NO-GO สำหรับการทดลองทางวิทยาศาสตร์ทั้งหมด**
**GO สำหรับ:** งานเอกสาร, การตรวจ repository เชิงโค้ด (ถ้าไม่มีข้อมูลส่วนบุคคล), การเขียน evaluation harness, smoke test บนข้อมูลสังเคราะห์

---

## สรุปสถานะ

| Gate | ชื่อ | สถานะ | ปลดล็อก |
|---|---|---|---|
| G0 | Ground-truth provenance | **BLOCKED** (ข้อมูลไม่พร้อม — Phase 1 ระบุว่าไม่ผ่าน; เอกสาร Phase 1 ไม่ได้ถูกเข้าถึงในรอบนี้) | G1 |
| G1 | Data-use authorization & privacy | **BLOCKED** | D0 ทั้งหมด |
| G2 | Data dictionary & label policy | NOT STARTED | G3 |
| G3 | Split freeze & test lock | NOT STARTED | G4 |
| G4 | Pre-registration freeze | NOT STARTED | T1–T6 |
| G5 | Final-config declaration & fresh-holdout | NOT STARTED | T7 (เปิด test) |
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
