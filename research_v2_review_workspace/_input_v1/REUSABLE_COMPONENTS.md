# Reusable Components — งานเดิมที่นำกลับมาใช้ได้ (และเงื่อนไข)

> **สถานะ:** ไม่ได้เข้าถึง repository ในรอบนี้ — รายการด้านล่างเป็น **component ที่คาดว่าจะมีจากคำอธิบาย R0–R6** พร้อมเกณฑ์ตรวจรับ ไม่ใช่การยืนยันว่ามีอยู่จริง (ทุกแถว = UNKNOWN จนกว่าตรวจ)

## 1. หลักการนำกลับมาใช้

1. **ใช้ซ้ำได้ = โค้ด/ความรู้** ไม่ใช่ **ผลลัพธ์/โมเดลที่ train แล้ว**
2. ทุก component ต้องผ่าน **acceptance test** ก่อนเข้า pipeline V2
3. Component ที่สัมผัส split/label ต้องถูกตรวจว่าไม่อ่าน test

## 2. ตาราง component

| Component (คาดว่ามี) | ที่มา | ใช้ใน V2 | ระดับการใช้ซ้ำ | Acceptance test ก่อนใช้ | สถานะ |
|---|---|---|---|---|---|
| Profile loader / parser ต่อแพลตฟอร์ม | ทุก R | D0-2, ทุก Track | ใช้ซ้ำได้หลังตรวจ | unit test บนตัวอย่างสังเคราะห์; ตรวจ encoding UTF-8/NFKC สำหรับภาษาไทย/emoji | UNKNOWN |
| Normalization (lowercase, strip, emoji) | R0 | E2-1, E1-* | ใช้ซ้ำ + บันทึกเป็น config | ทดสอบ idempotence; ตรวจว่าไม่ทำลายอักษรไทย | UNKNOWN |
| 17 lexical features | R0/R1 | E2-1 (F-LEX) | ใช้ซ้ำนิยาม; อาจเพิ่ม/ตัด | test ต่อ feature กับค่าที่คำนวณด้วยมือ; ตรวจ label-proxy feature | UNKNOWN |
| Semantic cosine (MiniLM) | R2/R3 | E4-1 | ใช้ซ้ำ + ตรึง model revision | ตรวจว่าใช้ multilingual หรือไม่; ทดสอบ cosine บนคู่ไทย/อังกฤษสังเคราะห์ | UNKNOWN |
| GA implementation | R1/R3/R5 | E6-5 | ใช้ซ้ำหลัง refactor ให้รับ budget และ seed เป็นพารามิเตอร์ | ตรวจว่า fitness อ่านเฉพาะ validation; ทดสอบ reproducibility ด้วย seed | UNKNOWN |
| Threshold evaluator | R0/R2 | E6-1, E6-2 | ใช้ซ้ำ | เทียบกับ scikit-learn metrics | UNKNOWN |
| Bloom filter encoder | R4/R5 | E8-1 (optional) | ใช้ซ้ำ | ตรวจพารามิเตอร์ (length, k, q); ใช้ keyed hashing หรือไม่ | UNKNOWN |
| BERT/semantic blocker | R6 | E1-4 | ใช้ซ้ำบางส่วน; ต้องเพิ่มการคุม budget k | วัด PC@k เทียบ brute force บน sample | UNKNOWN |
| GB training script | GB experiments | E3-2 | อ้างอิง hyperparameter เท่านั้น; เขียน training ใหม่ให้ใช้ grouped CV | — | UNKNOWN |
| Report/plot scripts | ทุก R | E7 | ใช้ซ้ำได้ถ้าแยกจากข้อมูลจริง | — | UNKNOWN |
| ข้อมูลดิบ / label | ทุก R | ทุก Track | **ห้ามแก้ไขต้นฉบับ**; ใช้ผ่าน read-only + hash | G0–G3 | **BLOCKED** |
| โมเดลที่ train แล้ว / predictions เดิม | ทุก R | — (เฉพาะ historical appendix) | **ไม่ใช้เป็นผล V2** | — | HIST-UNVERIFIED |

## 3. Component ใหม่ที่ต้องสร้าง (ไม่มีในงานเดิมตามสรุปที่ได้รับ)

| Component | ใช้ใน | เหตุผล |
|---|---|---|
| Entity-grouped split + manifest hashing | G3 | ป้องกัน leakage [P20] |
| Test-lock wrapper (`--final`, access log) | G3, G5 | ป้องกัน test-set selection [P21] |
| Cluster bootstrap + paired Δ CI + Holm + TOST | ทุก Track | `EVALUATION_AND_STATISTICS.md` |
| Blocking evaluator (PC/PQ/RR/recovery, budget k) | T1 | H5 |
| Calibration module (Platt/isotonic) | E6-7 | P26 |
| Cost-based policy evaluator + three-way | T6 | P24, P25 |
| Non-GA optimizer baseline (random + TPE, budget-matched) | E6-4 | H4b fairness |
| Experiment ledger (append-only) | ทุก run | retrospective bias |
| Label-sensitivity evaluator (S1/S2/S3) | E7-6 | P27 |
| Privacy attack harness | E8-3 | P30, P31, P35 |

## 4. ข้อแนะนำการจัดโครงสร้างโค้ด (implementation detail — ไม่ใช่ contribution)

```
research_v2/
  src/  blocking/ features/ models/ policy/ eval/ privacy/
  configs/  (หนึ่ง YAML ต่อ exp_id)
  manifests/ (split + data hashes, read-only)
  ledger/   (append-only JSONL)
  results/  (metrics JSON ต่อ run; ไม่มีข้อมูลส่วนบุคคล)
```
