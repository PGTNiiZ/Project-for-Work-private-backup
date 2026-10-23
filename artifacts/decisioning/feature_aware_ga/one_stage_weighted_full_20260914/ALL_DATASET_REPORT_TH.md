# ผลการรัน Frozen GA Policy กับ Dataset ทั้งหมด

ใช้ genome ที่เลือกจาก validation และ freeze ไว้แล้วกับทุกแถวใน `train_all.parquet`
จำนวน 58,696 คู่ โดยไม่มีการ train หรือปรับ threshold/weight เพิ่มจาก train หรือ test.

## ผลรวมทุก Split

| Policy | Rows | Cost | Precision | Recall | F1 | FP | FN | REVIEW |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| one_stage_weighted_10gene | 58,696 | 1870.2 | 0.9970 | 0.8392 | 0.9113 | 73 | 380 | 13,442 |
| score_only_2threshold | 58,696 | 1887.7 | 0.9972 | 0.8302 | 0.9060 | 69 | 382 | 13,677 |
| legacy_name_guard_4threshold | 58,696 | 2371.0 | 0.9856 | 0.8582 | 0.9175 | 366 | 390 | 12,490 |

## One-Stage แยกตาม Split

| Split | Rows | Cost | Precision | Recall | F1 | FP | FN | REVIEW |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| train | 41,803 | 1130.3 | 0.9987 | 0.8467 | 0.9164 | 23 | 142 | 9,423 |
| val | 8,580 | 377.4 | 0.9934 | 0.8226 | 0.9000 | 24 | 122 | 2,074 |
| test | 8,313 | 362.5 | 0.9928 | 0.8208 | 0.8987 | 26 | 116 | 1,945 |
| all | 58,696 | 1870.2 | 0.9970 | 0.8392 | 0.9113 | 73 | 380 | 13,442 |

แถวระดับคู่พร้อม score และคำตัดสินของทั้งสาม policy อยู่ใน
`all_dataset_decisions.parquet`. ค่า metrics รวม train มีไว้บอกผลการ apply policy ครบ dataset;
ใช้ held-out test ใน `FULL_REPORT_TH.md` สำหรับสรุปความสามารถในการ generalize.
