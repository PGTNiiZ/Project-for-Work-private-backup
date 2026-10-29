# Evaluation Protocol และ Statistical Methodology — Research V2

สถานะ: **PROPOSED** — freeze ทั้งเอกสารที่ G4 (บันทึก SHA-256 ของไฟล์ใน `RESEARCH_GATES.md`)

---

## 1. ระดับการประเมิน (แยกให้ชัดเสมอ)

| ระดับ | ตัวหาร (denominator) | ใช้กับ |
|---|---|---|
| **Blocking-level** | คู่จริงทั้งหมดใน split | T1: PC, RR, PQ |
| **Candidate-level** | คู่ใน C(k*) ที่มี label | T2–T5: PR-AUC, P/R/F1 ของ matcher |
| **End-to-end** | คู่จริงทั้งหมดใน split (รวมที่ blocking ตกหล่น) | T6–T7: Recall_e2e, cost |
| **Entity-level (optional)** | identity clusters | T10: B-cubed |

ความสัมพันธ์: Recall_e2e = PC@k × Recall_matcher|C (ถ้าไม่มี post-processing) — **ต้องรายงานทั้งสามตัวคู่กันเสมอ** ห้ามรายงาน F1 candidate-level เป็นประสิทธิภาพระบบ [P07]

## 2. ตัวชี้วัด

### 2.1 Blocking
- **PC@k (Pair Completeness)** = |positives ∩ C(k)| / |positives|
- **RR (Reduction Ratio)** = 1 − |C(k)| / (|A| × |B|)
- **PQ (Pairs Quality)** = |positives ∩ C(k)| / |C(k)|
- **Recovery rate** = |missed_by_best_lexical ∩ found_by_X| / |missed_by_best_lexical|
- PC–|C| curve และพื้นที่ใต้เส้นโค้งที่ |C| ≤ |C|_max ที่ประกาศ

### 2.2 Matching
- **Primary: PR-AUC (average precision)** — เหมาะกับ imbalance [P23]
- P, R, F1 ที่ threshold policy ที่กำหนด (ไม่ใช่ threshold ที่ดีที่สุดบน test)
- **Recall @ Precision ≥ P_target** (P_target เสนอ 0.90; freeze ที่ G4)
- Calibration: Brier score, ECE (15 bins, equal-mass)
- ห้ามใช้ accuracy เป็นตัวชี้วัดหลัก [P18]

### 2.3 Decision / cost
- **Expected cost ต่อคู่** = (c_FP·FP + c_FN·FN + c_R·Review) / N_pairs — ใช้ cost model ที่ freeze
- False merges ต่อ 1,000 บัญชี, review rate, coverage = 1 − review rate
- Sensitivity ของ cost ratio c_FP:c_FN ∈ {1:1, 2:1, 5:1 (default), 10:1}

### 2.4 Robustness และ cost
- ผลแยก stratum: platform pair, ภาษา/ถอดเสียง, missingness pattern, ความถี่ของชื่อ
- ms/1k คู่ ต่อ stage, peak RAM/VRAM, training time — วัดบนฮาร์ดแวร์ที่ระบุ, median ของ 5 การวัด

## 3. การแบ่งข้อมูลและการป้องกัน leakage

1. **Entity-disjoint split:** group = identity cluster (และ connected component ถ้าจำเป็น) [P20]
2. **Test lock:** สร้าง test ครั้งเดียวที่ G3, เก็บ hash, เข้ารหัส/แยกสิทธิ์; สคริปต์ evaluation อ่าน test ได้เฉพาะเมื่อ flag `--final` และบันทึก log การเปิดทุกครั้ง
3. **Fit ทุกอย่างบน train เท่านั้น:** TF-IDF vocabulary, scaler, imputation, calibration (calibration fold ใน dev)
4. **Feature audit:** ตัด feature ใดที่ (a) ได้มาหลังการสร้าง label (b) เป็น ID ภายใน (c) สะท้อนกระบวนการสร้าง ground truth (เช่น ถ้า label มาจากลิงก์ข้ามแพลตฟอร์ม feature "URL ตรงกัน" อาจเป็น *label proxy* — ต้องตัดสินที่ D0-1 ว่าจะรวมหรือไม่ และรายงานผลทั้งแบบรวม/ไม่รวม)

## 4. การอนุมานทางสถิติ

### 4.1 หน่วยการ resample
คู่ข้อมูลไม่เป็นอิสระ (บัญชีเดียวอยู่ในหลายคู่; identity เดียวมีหลายบัญชี) จึงใช้ **cluster (entity-grouped) bootstrap**: resample identity clusters ของ test พร้อม candidate pairs ทั้งหมดที่เกี่ยวข้อง แล้วคำนวณ metric ใหม่

### 4.2 Paired comparison
- สำหรับคู่การเปรียบเทียบ (X vs Y) คำนวณ Δ = metric(X) − metric(Y) **ภายใน bootstrap sample เดียวกัน** → 95% percentile CI (BCa ถ้า B ≥ 5,000 ทำได้)
- B = 2,000 (ค่าตั้งต้น); เพิ่มเป็น 10,000 สำหรับ 5 primary contrasts
- การทดสอบรอง: McNemar (exact) บนการตัดสินระดับคู่ [P22] — ตีความด้วยความระวังเพราะละเมิดความเป็นอิสระ

### 4.3 Primary confirmatory contrasts (5 รายการ, Holm-adjusted, α = 0.05 family-wise)

| # | Hypothesis | Contrast | Metric |
|---|---|---|---|
| C1 | H1 | E5-3 (หรือ E5-1) vs best single group (E5-5) | PR-AUC |
| C2 | H2 | E3-2 vs E2-3 | PR-AUC |
| C3 | H3 | E5-3 vs E5-1 (GBDT) | PR-AUC |
| C4 | H4b | E6-5 vs best{E6-2, E6-3, E6-4} | Expected cost |
| C5 | H5 | E1-5 vs best lexical blocker | PC@k* |

H4a, H4c, H3a, H3b และ ablation ทั้งหมด = **secondary/exploratory** (รายงาน CI ไม่ adjust แต่ระบุชัดว่าเป็น exploratory)

### 4.4 การตัดสิน
- **สนับสนุน H:** Holm-adjusted p < 0.05 **และ** ขอบล่าง 95% CI ของ Δ > SESOI
- **เทียบเท่าในทางปฏิบัติ:** 90% CI อยู่ภายใน [−SESOI, +SESOI] (TOST)
- **ไม่สรุป (inconclusive):** กรณีอื่น — รายงานตามจริง ไม่ขยายการทดลองเพื่อหา significance

### 4.5 ความแปรปรวนจาก seed
รายงาน mean ± SD ข้าม seed; ใน bootstrap ใช้ prediction ที่เฉลี่ยข้าม seed (ensemble ของ score) หรือรายงาน CI ต่อ seed แล้วเลือกแบบใดแบบหนึ่ง **ที่ G4**; ถ้า SD ข้าม seed ≥ |Δ|/2 → ถือว่า effect ไม่เสถียร

### 4.6 Power / ความพอเพียงของข้อมูล
ก่อน G4 ทำ **pilot variance estimate** บน dev (grouped CV) เพื่อประมาณ SD ของ ΔPR-AUC แล้วตรวจว่า CI half-width ที่คาด < SESOI หรือไม่; ถ้าไม่ → (a) เพิ่มข้อมูล หรือ (b) ปรับ SESOI ขึ้นและประกาศ หรือ (c) ลดสมมติฐานเป็น exploratory — ตัดสิน *ก่อน* เปิด test

## 5. Ground truth ไม่ครบและ negative ที่ไม่แน่นอน

1. แบ่ง label เป็น {confirmed positive, confirmed negative, unlabeled}
2. **Primary analysis:** ตามนิยามที่ freeze ที่ G4 (ค่าตั้งต้น: unlabeled = negative เพราะเป็นกรณี conservative ต่อ precision)
3. **E7-6 Sensitivity:**
   - S1: unlabeled = negative (precision ต่ำสุดเชิงโครงสร้าง)
   - S2: ตัด unlabeled ออก (precision สูงเกินจริงได้)
   - S3: ปรับ FP ด้วย π_hidden จาก D0-3: FP_adj = FP × (1 − π_hidden) พร้อม CI ของ π_hidden
4. รายงาน **ช่วง** ของ precision/cost ไม่ใช่ค่าเดียว
5. หาก ground truth ถูกสร้างจาก blocking/feature ใดของระบบเดิม → ระบุเป็น **selection bias** ใน Threats to Validity และทำ E7-3 stratum "ไม่ได้มาจากกลไกนั้น" ถ้าเป็นไปได้

## 6. Class imbalance ที่สมจริง

- ประเมินที่ prior ตามธรรมชาติของ C(k*) (ไม่ใช่ชุดที่ balance) [P07]
- E7-4: reweight negative เพื่อจำลอง prior 0.5×, 0.1× ของ natural prior — precision ที่ prior π′: P′ = TPR·π′ / (TPR·π′ + FPR·(1−π′))
- รายงาน PR curve ไม่ใช่ ROC อย่างเดียว

## 7. อคติจากการทดลองซ้ำทางประวัติศาสตร์ (Retrospective bias)

ปัญหา: R0–R6 อาจถูกพัฒนา/เลือกบนข้อมูลชุดเดียวกันหลายรอบ (garden of forking paths) — ถ้า test ใหม่ทับกับข้อมูลที่ทีมเคยเห็นผล ข้อสรุปจะมีอคติแม้ split ใหม่

มาตรการ:
1. **G5 Fresh-holdout rule:** ถ้าพิสูจน์ไม่ได้ว่า identity ใน test ใหม่ไม่เคยถูกใช้ประเมินในงานเดิม → ต้อง (a) เก็บ/แยก holdout ใหม่ที่ไม่เคยถูกใช้ (ดีที่สุด: out-of-time หรือแพลตฟอร์ม/ช่วงเก็บข้อมูลใหม่) หรือ (b) ลดระดับทุกข้อสรุปเป็น "exploratory, retrospectively contaminated"
2. **Pre-registration (G4):** สมมติฐาน, contrasts, SESOI, metric, k*, cost model, seeds, budget — hash และ timestamp ก่อน run ใด ๆ บน validation ของ V2
3. **Experiment ledger:** บันทึกทุก run (รวมที่ล้มเหลว/ถูกทิ้ง) ใน append-only log; รายงานจำนวน configuration ที่ทดลองทั้งหมด
4. **ห้ามใช้ผลประวัติศาสตร์เลือก configuration** ของ V2 เว้นแต่ระบุเป็น prior ที่ประกาศใน G4 (เช่น "MiniLM ถูกเลือกเพราะใช้ใน R2") — การเลือกแบบนี้ไม่ทำให้ test ปนเปื้อน แต่ต้องโปร่งใส

## 8. ป้องกันการเลือกโมเดลด้วย test

- การเลือกทั้งหมดบน dev (grouped CV); test ถูกประเมิน **ครั้งเดียว** ต่อ configuration ที่ประกาศ
- ถ้าพบ bug หลังเปิด test: แก้ bug, รันใหม่, **รายงานทั้งผลก่อนและหลังแก้** พร้อมเหตุผล
- ห้าม "เลือก seed ที่ดีที่สุด" หรือ "เลือก k ที่ดีที่สุด" บน test

## 9. รูปแบบรายงานผลขั้นต่ำต่อ experiment

```
exp_id, hypothesis, config_hash, data_hash, split_hash, seed(s),
level (blocking/candidate/e2e), metric, point_estimate, ci_low, ci_high,
delta_vs_baseline, delta_ci_low, delta_ci_high, holm_p (ถ้า confirmatory),
n_pairs, n_positives, n_identities, prior, runtime, hardware, notes
```

## 10. Threats to validity ที่ต้องเขียนในเล่ม

Internal (leakage, selection bias จาก label, seed variance) · Construct (cost model สมมติ, label noise) · External (แพลตฟอร์ม/ภาษา/ช่วงเวลาเดียว, ความแตกต่างจาก benchmark EM) · Conclusion (multiplicity, power)
