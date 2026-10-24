# ผลทดลองเต็มรูปแบบ: One-Stage Weighted GA

## Protocol

GA เลือก genome จาก validation เท่านั้น จำนวน 10 seeds โดยทุก policy ใช้
population และ generations เท่ากัน จากนั้นเขียน `frozen_policies_before_test.json` ก่อนอ่าน held-out
test. ไฟล์ freeze มี SHA-256 `4fb45abe7f43d5cd9d09670060b66436493bdc854bd5695e1e437881aafcc38e` และ source hash ถูกตรวจซ้ำก่อนประเมิน test.

## ผล Held-out Test (8,313 คู่; positive 4,387)

| Policy | Cost | Precision | Recall | F1 | FP | FN | REVIEW |
|---|---:|---:|---:|---:|---:|---:|---:|
| score_only_2threshold | 360.8 | 0.9936 | 0.8113 | 0.8932 | 23 | 116 | 1,988 |
| one_stage_weighted_10gene | 362.5 | 0.9928 | 0.8208 | 0.8987 | 26 | 116 | 1,945 |
| legacy_name_guard_4threshold | 484.5 | 0.9749 | 0.8409 | 0.9029 | 95 | 117 | 1,775 |

ความต่างของ one-stage เทียบ baseline (ค่าติดลบลดลง):

| Baseline | ΔCost | ΔFP | ΔFN | ΔREVIEW |
|---|---:|---:|---:|---:|
| score_only_2threshold | +1.7 | +3 | +0 | -43 |
| legacy_name_guard_4threshold | -122.0 | -69 | -1 | +170 |

One-stage ผ่าน gate รวมบน test: **ผ่าน**
(Precision ≥ .99 และ Recall ≥ .70). Bootstrap 95% CI: Precision
[0.9899, 0.9953], Recall
[0.8092, 0.8318], F1
[0.8915, 0.9053], Cost
[333.8, 393.3].

## Validation-to-Test Generalization

One-stage: cost 377.4 → 362.5, precision
0.9934 → 0.9928, recall
0.8226 → 0.8208, F1 0.9000 → 0.8987.

ผลราย platform, coverage, bootstrap และ transition ระหว่างคำตัดสินอยู่ใน CSV ข้างรายงานนี้.
การประเมินนี้ครอบคลุม labeled pair population ใน `train_all.parquet`; ยังไม่ใช่การ project policy
ไปยัง full candidate cache ประมาณ 2.07 ล้านคู่ และ review capacity ยังไม่ได้กำหนด.
