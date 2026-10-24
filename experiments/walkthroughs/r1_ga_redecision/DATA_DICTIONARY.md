# R1 GA input data — คำอธิบายแบบทีละแถว

ไฟล์ใน `data/` สร้างจากข้อมูล `ga_validation` จริงของ R1 และ chromosome ที่เลือกจาก seed 999 โดยไม่ rerun หรือ retrain GA

## ไฟล์

- `r1_ga_validation_chromosome_detail.csv` — scored pair ทุกแถวใน `ga_validation` พร้อม trace การตัดสินใจและ cost
- `r1_ga_run_input.csv` — 9,097 แถวที่ถูกส่งเข้า `run_ga` จริง; สาม array หลักคือ `probability`, `name_similarity`, `actual_code`
- `r1_ga_branch_examples.csv` — ตัวอย่างขนาดเล็กที่ครอบคลุมเส้นทางหลักของ chromosome
- `r1_ga_changed_examples.csv` — ตัวอย่างที่เทียบ R0 กับ GA และแสดงว่าดีขึ้นหรือแย่ลงตรงไหน
- `r1_ga_transition_summary.csv` — สรุปทุก transition เช่น REVIEW → MATCH พร้อม cost ก่อนและหลัง
- `r1_ga_validation_summary.json` — จำนวนแถว, genome, weights และการกระทบยอด cost

สร้างไฟล์ซ้ำได้ด้วย:

```bash
python experiments/walkthroughs/r1_ga_redecision/export_r1_ga_input_detail.py
```

## Input ที่ chromosome ใช้

| คอลัมน์ | ความหมาย |
|---|---|
| `profile_id_a`, `profile_id_b` | รหัสคู่ profile เพื่อ trace กลับไปยัง source; ไม่ใช่ gene และไม่ถูกใช้ตัดสินใจ |
| `probability` | score ของ R0 ที่เปรียบเทียบกับ `t_m` และ `t_r` |
| `name_similarity` | Jaro-Winkler name similarity ที่เปรียบเทียบกับ `c_promote` และ `c_demote` เฉพาะ probability band |
| `actual_code` | label จริง: 0 = NO_MATCH, 1 = MATCH; ใช้คำนวณ fitness หลังตัดสินใจ ไม่ใช่ input ของ decision rule |
| `entered_run_ga` | `True` เมื่อ `probability >= 0.5` และแถวถูกส่งเข้า `run_ga`; positive ที่ต่ำกว่า floor ถูกนับเป็น constant FN |

## Chromosome

| คอลัมน์ | เปรียบเทียบกับ | ความหมาย |
|---|---|---|
| `t_m` | `probability` | ตั้งแต่ค่านี้ขึ้นไปเป็น MATCH โดยตรง |
| `t_r` | `probability` | ต่ำกว่าค่านี้เป็น NO_MATCH โดยตรง |
| `c_promote` | `name_similarity` | ใน probability band ถ้าชื่อถึงค่านี้ให้ promote เป็น MATCH |
| `c_demote` | `name_similarity` | ใน probability band ถ้าชื่อต่ำกว่าค่านี้ให้ demote เป็น NO_MATCH |

## Trace การเปรียบเทียบ

| คอลัมน์ | เงื่อนไข |
|---|---|
| `prob_ge_t_m` | `probability >= t_m` |
| `prob_lt_t_r` | `probability < t_r` |
| `prob_in_band` | `t_r <= probability < t_m` |
| `name_ge_c_promote` | `name_similarity >= c_promote` |
| `name_lt_c_demote` | `name_similarity < c_demote` |
| `probability_route` | `DIRECT_MATCH`, `DIRECT_NO_MATCH` หรือ `BETWEEN_THRESHOLDS` |
| `name_route` | `PROMOTE_TO_MATCH`, `DEMOTE_TO_NO_MATCH`, `REVIEW_ZONE` หรือ `NOT_USED` |

## Output และ cost ต่อแถว

| คอลัมน์ | ความหมาย |
|---|---|
| `ga_decision_code` | 0 = NO_MATCH, 1 = REVIEW, 2 = MATCH |
| `ga_decision_label` | decision แบบข้อความ |
| `is_false_positive` | GA ตอบ MATCH แต่ actual เป็น NO_MATCH |
| `is_false_negative` | GA ตอบ NO_MATCH แต่ actual เป็น MATCH |
| `is_review` | GA ส่งให้คนตรวจ |
| `fp_cost` | `5 × is_false_positive` |
| `fn_cost` | `1 × is_false_negative` |
| `review_cost` | `0.02 × is_review` |
| `row_total_cost` | `fp_cost + fn_cost + review_cost` |
| `r0_decision_label`, `r0_row_cost` | decision และ cost เดิมก่อนใช้ GA |
| `decision_changed` | GA เปลี่ยน decision จาก R0 หรือไม่ |
| `cost_delta_ga_minus_r0` | `GA cost - R0 cost`; ค่าติดลบหมายถึง GA ทำให้ดีขึ้น |
| `ga_effect` | `IMPROVED`, `WORSENED` หรือ `SAME_COST` |
| `search_row_cost` | cost ของแถวที่เข้า `run_ga` จริง |
| `constant_below_floor_cost` | FN cost ของ positive row ที่ต่ำกว่า score floor และไม่เข้า search array |

`AUTO_EXACT` และคู่จริงที่ไม่ผ่าน candidate blocking ไม่ได้เข้า chromosome. Fixed errors เหล่านี้แสดงแยกใน summary เพื่อไม่ให้เข้าใจผิดว่า GA สามารถปรับแก้ได้
