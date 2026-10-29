# Historical Experiment Mapping — R0–R6 และงานเกี่ยวข้อง → Research V2

> **สถานะหลักฐานของเอกสารนี้:** ข้อมูลประวัติทั้งหมดมาจาก **สรุปที่ผู้ใช้ให้มาในการสนทนา** (ซึ่งอ้างถึง `EXPERIMENT_PLAN.md` เดิมและรายงานผล) — **ไม่ได้ตรวจจาก repository** เพราะเข้าถึง `PGTNiiZ/Project-for-Work` และ backup ไม่ได้ในรอบนี้ ทุกแถวจึงเป็น **HIST-UNVERIFIED** และทุกช่อง "V-REPO" เป็น **BLOCKED** จนกว่าจะมีผู้ตรวจเติม

---

## 1. โครงสร้างการทดลองเดิม (ตามสรุปที่ได้รับ)

แนวคิดเดิม: **Representation × Decision** — เปลี่ยนชุด feature แล้วเปรียบเทียบวิธีตัดสินใจ

| ID เดิม | Representation | Decision | คำถามเดิม | ผลที่รายงาน (HIST-UNVERIFIED) |
|---|---|---|---|---|
| R0 | 17 features | manual threshold | baseline | — |
| R1 | 17 features | GA | GA ช่วยไหม | — |
| R2 | 18 features (+ semantic cosine) | threshold | semantic ช่วยไหม | — |
| R3 | 18 features | GA | semantic + GA | F1 = 0.8373 สูงสุดในชุด R0–R5 ที่เปรียบเทียบ |
| R4 | Bloom filter encoding | threshold | privacy transform กระทบผลแค่ไหน | — |
| R5 | Bloom filter encoding | GA | optimized policy ลดการสูญเสียได้ไหม | — |
| R6 | BERT-based semantic blocking | — | กู้คู่ที่ blocking เดิมพลาดได้ไหม | พบข้อจำกัดในการกู้คู่ |

### 1.1 การประเมินเชิงระเบียบวิธีของการออกแบบเดิม (ไม่ใช่การประเมินผล)

**จุดแข็ง:** R0–R3 เป็น factorial 2×2 (17/18 features × threshold/GA) ซึ่งโดยหลักการแยก main effect ของ semantic feature และ GA ได้ — V2 รักษาแนวคิดนี้ไว้ใน E7-2 และ T5/T6

**ข้อจำกัดที่ทำให้ยังใช้เป็นข้อสรุปไม่ได้:**
1. **Baseline ของ GA ไม่ยุติธรรม (ตามสรุปที่ได้รับ):** เทียบ GA กับ manual threshold เท่านั้น ไม่มี validation-tuned threshold หรือ optimizer อื่นที่ budget เท่ากัน → effect ของ GA อาจรวมผลของ "การ tune ใด ๆ ก็ได้" (แก้ใน E6-2…E6-5)
2. **ไม่ทราบว่า GA ถูก optimize บน split ใด** — ถ้าใช้ชุดเดียวกับที่รายงาน F1 จะเป็น test-set selection → ต้องตรวจโค้ด
3. **ไม่ทราบระดับการประเมิน** (candidate-level หรือ end-to-end) → R6 ชี้ว่า blocking มีคู่ตกหล่น ดังนั้นถ้า F1 0.8373 เป็น candidate-level ประสิทธิภาพระบบจริงจะต่ำกว่า
4. **ไม่มี CI / paired test / seeds** ในสรุปที่ได้รับ → ไม่ทราบว่าความต่างระหว่าง R0–R5 เกินความแปรปรวนหรือไม่
5. **ไม่ทราบ split แบบ entity-disjoint หรือไม่**
6. **Label provenance ไม่ผ่าน gate** → ทุกผลขึ้นกับ label ที่ยังไม่ตรวจ
7. **Multiple runs on same data** → retrospective bias (ดู `EVALUATION_AND_STATISTICS.md` §7)
8. **R4/R5 ไม่มี threat model** → อ้างเรื่องความเป็นส่วนตัวไม่ได้ (P30, P31, P35)

---

## 2. ตาราง mapping งานเดิม → V2

| งานเดิม | สิ่งที่ V2 สืบทอด | Experiment ใน V2 | ต้อง revalidate อะไร | ต้องตรวจจาก repo (BLOCKED) |
|---|---|---|---|---|
| **R0** | สูตร rule + 17 features เป็น *historical replica* | E2-2 (replica), E2-1 (feature definitions), E6-1 (fixed threshold) | นิยาม feature แต่ละตัว, normalization, threshold ที่ใช้ | `EXPERIMENT_PLAN.md`, โค้ดสร้าง feature, ค่า threshold, split |
| **R1** | GA บน 17 features | E6-5 (GA) เทียบ E6-2/E6-3/E6-4 | budget ของ GA, policy space (threshold? weights?), split ที่ใช้ optimize | โค้ด GA, fitness function, population/generations, seed |
| **R2** | semantic cosine (feature ที่ 18) | E4-1 (F-SEM), E5-3 vs E5-1 | encoder ที่ใช้, attribute ที่ embed, pooling | ชื่อโมเดลและ revision, preprocessing |
| **R3** | 18 features + GA | E5-3 + E6-5 (แต่แยกผลกันใน E7-2) | ห้ามถือว่า "ดีที่สุด" — เป็นเพียงจุดเริ่มสมมติฐาน H3/H4 | วิธีคำนวณ F1 0.8373 (split, level, threshold) |
| **R4** | Bloom-encoded features | E8-1 (optional) | parameters ของ Bloom (k hash, length, q) | โค้ด encoding |
| **R5** | Bloom + GA | E8-2 (optional) + **E8-3 attack eval (ใหม่, บังคับถ้าทำ T8)** | เหมือน R1 | เหมือน R1 |
| **R6** | BERT semantic blocking | E1-4 (dense retrieval), E1-5 (hybrid) ภายใต้ budget k เท่ากัน | budget ที่ใช้, วิธีวัดการกู้คืน | โค้ด retrieval, k, index |
| **GA (ทั่วไป)** | operator/encoding ของ GA | E6-5 | ว่าไม่อ่าน test | — |
| **GB (Gradient Boosting)** | hyperparameter เริ่มต้น | E3-2 | ต้อง train ใหม่ทั้งหมด | config เดิม |
| **MiniLM** | ตัวเลือก encoder | E4-1, E1-4 | multilingual หรือไม่ (ภาษาไทย) | model id |
| **BERT** | ตัวเลือก encoder ใหญ่ / cross-encoder | E4-4 (conditional) | | model id, fine-tune หรือ frozen |
| **Semantic blocking** | แนวคิด dense candidate generation | E1-4, E1-5 | | |
| **Feature-aware experiments** | สมมติฐานว่ากลุ่ม attribute ใดสำคัญ | E5-4, E5-5 | | รายการการทดลองและผล |
| **ICSEC materials** | บริบท/การนิยามปัญหาเดิม; ระวัง self-plagiarism และการอ้างผลซ้ำ | Literature/บทนำ | ผลใน paper ต้องติดป้าย HIST-UNVERIFIED ในเล่ม V2 | **BLOCKED** — ต้องได้ไฟล์ |

---

## 3. การใช้ผลประวัติศาสตร์อย่างถูกต้องในเล่ม V2

| ทำได้ | ห้ามทำ |
|---|---|
| ใช้เป็นแรงจูงใจของสมมติฐาน ("งานเดิมพบสัญญาณว่า…จึงทดสอบอย่างควบคุม") | อ้าง F1 0.8373 เป็นผลของ V2 |
| ใส่ในภาคผนวกเป็น historical table พร้อมป้ายและข้อจำกัด | เทียบตรงกับผล V2 ในตารางเดียวกันโดยไม่มีคำเตือน |
| ใช้ค่าตั้งต้น (encoder, hyperparameters) เป็น prior ที่ประกาศใน G4 | ใช้ผลเดิมเลือก configuration หลังเห็นผล V2 |
| Replicate R0/R1 (E2-2, E6-5) ภายใต้ protocol ใหม่ แล้วรายงานว่าผล replicate หรือไม่ | สรุปว่า R3 "universally best" |

---

## 4. Checklist สำหรับผู้ตรวจ repository (เติมเพื่อเปลี่ยน HIST-UNVERIFIED → V-REPO)

สำหรับแต่ละ R0–R6:

- [ ] path ของ config/script และ commit hash
- [ ] ไฟล์ข้อมูลที่ใช้ + hash; ตรงกับข้อมูลที่ V2 จะใช้หรือไม่
- [ ] วิธีแบ่ง train/val/test; entity-disjoint หรือไม่
- [ ] ชุดที่ใช้ optimize threshold/GA vs ชุดที่รายงานผล
- [ ] ระดับการประเมิน (candidate / end-to-end)
- [ ] จำนวนคู่, จำนวน positive, prior
- [ ] seeds และจำนวนครั้งที่รัน
- [ ] รายการ feature 17/18 ตัว พร้อมนิยาม
- [ ] ผลลัพธ์ดิบ (predictions) ยังมีอยู่หรือไม่ — ถ้ามี สามารถคำนวณ CI ย้อนหลังได้ (ยังคงเป็น HIST แต่มี uncertainty)
- [ ] ข้อมูลส่วนบุคคลถูก commit ลง repo หรือไม่ (ถ้าใช่ → แจ้ง G1 ทันที)
- [ ] ความต่างระหว่าง main repo กับ private backup

| Run | Repo path | Commit | Split ที่ optimize | Split ที่รายงาน | Level | ผลที่ตรวจได้ | สถานะใหม่ |
|---|---|---|---|---|---|---|---|
| R0 | | | | | | | HIST-UNVERIFIED |
| R1 | | | | | | | HIST-UNVERIFIED |
| R2 | | | | | | | HIST-UNVERIFIED |
| R3 | | | | | | | HIST-UNVERIFIED |
| R4 | | | | | | | HIST-UNVERIFIED |
| R5 | | | | | | | HIST-UNVERIFIED |
| R6 | | | | | | | HIST-UNVERIFIED |
