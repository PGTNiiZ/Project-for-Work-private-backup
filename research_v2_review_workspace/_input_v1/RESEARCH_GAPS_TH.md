# Research Gaps และ Potential Contributions — Research V2

> **หลักการเขียน:** ช่องว่างทุกข้อระบุในรูป "ภายในชุดงานที่ทบทวน (35 รายการ, ดู `PAPER_EVIDENCE_MATRIX.csv`) **ไม่พบ**…" ไม่ใช่ "ยังไม่มีใครเคยทำ" เพราะการทบทวนนี้ไม่ใช่ systematic review แบบเต็มรูปแบบ ก่อนเขียนในเล่มวิทยานิพนธ์ต้องค้นซ้ำด้วยคำค้นที่บันทึกไว้ (Scopus/IEEE Xplore/ACM DL/dblp) และอัปเดตสถานะ

ระดับความมั่นใจของช่องว่าง: **สูง** = งานหลักหลายชิ้นระบุตรงกันว่าเป็นข้อจำกัด · **กลาง** = อนุมานจากขอบเขตของงานที่ทบทวน · **ต่ำ** = ต้องค้นเพิ่มก่อนอ้าง

---

## G-1 หลักฐานการแยกผลขององค์ประกอบ pipeline ใน profile-based UIL (ความมั่นใจ: กลาง)

- **ที่มา:** งาน EM แยก blocking กับ matching ชัดเจน [P12, P13, P14] และมีงานชี้ว่าการตั้ง benchmark ทำให้ผลสูงเกินจริง [P07] แต่ survey ด้าน UIL [P01, P02] สรุปงานในระดับวิธีการ/ชุดข้อมูล ไม่ใช่การทดลองควบคุมที่แยก blocking × representation × learner × decision policy บนข้อมูลชุดเดียว
- **ช่องว่าง:** ภายในชุดที่ทบทวน ไม่พบการศึกษา ablation แบบ factorial ที่แยกผลสี่องค์ประกอบสำหรับ UIL ที่ใช้เฉพาะ profile attributes
- **Contribution ที่เป็นไปได้ (C1):** ผล ablation แบบ factorial พร้อม paired uncertainty ที่บอกว่า "องค์ประกอบใดมีส่วนต่อผลเท่าไร" → **E7-2, E5-4**
- **ข้อควรระวัง:** contribution นี้มีคุณค่าแม้ผลเป็นลบ (เช่น semantic ไม่ช่วย)

## G-2 การประเมินแบบสมจริงสำหรับ UIL: open entities, prior สมจริง และ end-to-end (ความมั่นใจ: สูง สำหรับ EM; กลาง สำหรับ UIL)

- **ที่มา:** P07 แสดงว่าการสมมติ restricted entities และ balanced labels ทำให้ประเมินความก้าวหน้าของ EM สูงเกินจริง; P18 ชี้ว่า imbalance ทำให้ accuracy ไร้ความหมายและ F-measure มีจุดอ่อนเชิงแนวคิด
- **ช่องว่าง:** ภายในชุดที่ทบทวน ไม่พบงาน UIL ที่รายงานผล candidate-level คู่กับ end-to-end ที่ prior ตามธรรมชาติของ candidate set พร้อมการเปลี่ยนแปลงตาม prior
- **Contribution (C2):** protocol การประเมิน UIL ที่ใช้ซ้ำได้ (entity-disjoint split, end-to-end recall, prior sensitivity, grouped bootstrap) → **E7-1, E7-4, EVALUATION_AND_STATISTICS.md**
- **ระวัง:** นี่เป็น contribution เชิงระเบียบวิธี ไม่ใช่การอ้างว่าโมเดลใหม่ดีกว่า

## G-3 การเปรียบเทียบ GA กับ optimizer อื่นอย่างยุติธรรมสำหรับ decision policy ใน linkage (ความมั่นใจ: ต่ำ–กลาง)

- **ที่มา:** มีทฤษฎี threshold ตามต้นทุน [P24], reject option [P25] และ calibration [P26] ซึ่งให้ baseline เชิงวิเคราะห์ได้โดยไม่ต้องค้นหา; โครงการเดิมใช้ GA (R1/R3/R5 — HIST-UNVERIFIED) แต่จากสรุปที่ได้รับ ไม่ปรากฏว่ามี baseline ที่ optimize แบบ non-GA ภายใต้ budget เท่ากัน
- **ช่องว่าง:** ภายในชุดที่ทบทวน ไม่พบงานที่เทียบ GA กับ (a) closed-form cost-optimal threshold (b) random/Bayesian search ภายใต้จำนวน evaluation เท่ากัน สำหรับ policy ของ identity linkage — **ต้องค้นเพิ่ม** ด้วยคำค้น "genetic algorithm threshold record linkage", "evolutionary record linkage" ก่อนอ้าง
- **Contribution (C3):** ข้อสรุปว่า GA เพิ่มคุณค่าเหนือ baseline วิเคราะห์หรือไม่ ภายใต้ cost model ที่ประกาศล่วงหน้า → **E6-1…E6-6**
- **ผลที่เป็นไปได้ที่ยอมรับล่วงหน้า:** GA ไม่ดีกว่า E6-3/E6-4 อย่างมีนัย → ข้อเสนอให้ใช้วิธีที่ง่ายกว่า

## G-4 ความคุ้มค่าของ semantic representation บนโปรไฟล์ที่มีภาษาไทย/ผสมและ transliteration (ความมั่นใจ: กลาง)

- **ที่มา:** P04, P13, P14 ใช้ benchmark ภาษาอังกฤษเป็นหลัก; P08 ชี้ว่า semantic heterogeneity ตอน test เป็นปัญหาหลัก; P14 แสดงว่าต้นทุน vectorization ต่างกันมากระหว่างโมเดล
- **ช่องว่าง:** ภายในชุดที่ทบทวน ไม่พบการประเมิน semantic vs lexical สำหรับชื่อ/ไบโอที่สลับภาษาไทย–อังกฤษหรือถอดเสียง (เช่น "สมชาย" vs "somchai") ในบริบท UIL
- **Contribution (C4):** ประโยชน์ส่วนเพิ่ม (ΔPR-AUC, FN ที่กู้คืนได้) ต่อต้นทุน (ms/คู่) แยกตาม stratum ภาษา → **E4-1, E5-3, E7-3, E7-5**
- **เงื่อนไข:** ต้องยืนยันก่อนว่าข้อมูลจริงมีภาษาไทย/ผสมในสัดส่วนที่พอวิเคราะห์ (D0-2) — **UNKNOWN**

## G-5 ผลของ ground truth ไม่ครบและ negative ที่ไม่แน่นอนต่อข้อสรุป (ความมั่นใจ: กลาง)

- **ที่มา:** P01 และ P02 ชี้ว่าข้อมูลสาขานี้ไม่ครบและหาชุดข้อมูลยาก; P27 ให้กรอบ PU learning; P07 ชี้ผลของการสร้าง label ต่อการประเมิน
- **ช่องว่าง:** ภายในชุดที่ทบทวน ไม่พบงาน UIL ที่รายงานช่วงของ precision ภายใต้สมมติฐาน label ต่างกัน (เช่น unlabeled-as-negative vs excluded) พร้อม audit ตัวอย่าง
- **Contribution (C5):** sensitivity analysis ของ label assumption + audit ของ false positive อันดับต้น → **D0-3, E7-6**

## G-6 ความเป็นส่วนตัวที่ประเมินได้จริงของการเข้ารหัส Bloom filter สำหรับ social profile attributes (ความมั่นใจ: กลาง; optional)

- **ที่มา:** P29 เสนอ Bloom filter PPRL; P30, P31, P35 แสดงการโจมตีที่ re-identify ได้ภายใต้เงื่อนไขบางอย่าง
- **ช่องว่าง:** ภายในชุดที่ทบทวน ไม่พบการวัด privacy–utility trade-off ของ Bloom encoding บน username/display name ของโซเชียลมีเดีย (ซึ่ง distribution ของ q-gram ต่างจากชื่อในทะเบียนสุขภาพ)
- **Contribution (C6, optional):** utility loss (ΔPR-AUC) คู่กับ re-identification rate ภายใต้ threat model ที่ระบุ → **E8-1…E8-3**
- **Gate:** ต้องผ่าน ethics/data-use และมี threat model ก่อน

---

## สิ่งที่ **ไม่ใช่** contribution (implementation details)

แยกให้ชัดเพื่อไม่ให้ปะปนในเล่ม: การเขียน pipeline ใหม่, การจัด config/YAML, การเลือก library (scikit-learn/LightGBM/FAISS), การปรับ hyperparameter ทั่วไป, การทำ dashboard, การ port โค้ด R0–R6 — สิ่งเหล่านี้เป็น *เครื่องมือ* ที่ทำให้ C1–C6 ตรวจสอบได้ ไม่ใช่ข้อค้นพบ

## ลำดับความสำคัญของ contribution สำหรับวิทยานิพนธ์หลัก

| ลำดับ | Contribution | Hypothesis | สถานะ |
|---|---|---|---|
| 1 | C2 Protocol การประเมินสมจริง | ทั้งหมด | PROPOSED — ทำได้แม้โมเดลไม่ดีขึ้น |
| 2 | C1 Factorial attribution | H1–H5 | PROPOSED |
| 3 | C3 GA vs non-GA | H4 | PROPOSED |
| 4 | C4 Semantic cost–benefit | H3, H5 | PROPOSED (ขึ้นกับ D0-2) |
| 5 | C5 Label-uncertainty sensitivity | ทั้งหมด | PROPOSED |
| 6 | C6 Privacy–utility | T8 | OPTIONAL / BLOCKED |
