# รายงานผลละเอียด: Model Weights และ Feature-Aware GA

## ขอบเขตและความหมายของผล

run นี้ตอบคำถามสองเรื่องที่ต้องแยกออกจากกันบน labeled feature population ใน
`pub_multi/data/train_all.parquet` (**58,696 pairs**):

1. feature และ feature group ใดช่วยให้ pair-scoring model ทำนายความน่าจะเป็นว่าเป็นคนเดียวกัน
2. evidence group ใดควรเป็น guard ใน review band ของ GA และน้ำหนักของ evidence ที่มีข้อมูลอยู่ควรเป็นเท่าใดเพื่อลด business cost

ผลนี้ **ยังไม่ใช่รายงานสำหรับ production เต็มชุด**. historical GA cache มี 2,073,842 scored
candidates แต่ feature matrix ที่ใช้รอบนี้ overlap เพียง 20,757 คู่ (1.00%). ดังนั้นผลนี้ใช้ยืนยัน
แนวทาง model/feature research ได้ แต่ก่อน promote จะต้อง rebuild cache ที่มี availability mask
แบบเดียวกันให้ครอบคลุม candidate ทั้งหมดก่อน

## สิ่งที่ workflow ทำ

1. สร้าง `decisioning_features.parquet` ที่เก็บ evidence score และ availability mask แยกกันสำหรับ name, bio, URL, location, image และ style. ข้อมูลที่ไม่มีจะไม่ถูกแปลงเป็น similarity เท่ากับศูนย์
2. train Logistic Regression เพื่ออ่าน standardized coefficient และ train Gradient Boosting เพื่อจับความสัมพันธ์ non-linear. เลือก model ด้วย validation AP เท่านั้น
3. รัน GA selector policy: score-only และ one-guard policy สำหรับทุก group ที่มี coverage/support เพียงพอ
4. รัน weighted-evidence GA: เรียนรู้ weight ที่ไม่ติดลบ และ normalize ใหม่ตาม evidence ที่มีอยู่ในแต่ละคู่ จึงไม่มีการลงโทษ feature ที่หายไป
5. เปรียบเทียบทุก policy บน validation, freeze policy ที่ cost ต่ำสุด แล้วเปิด held-out test เพียง **หนึ่งครั้ง**

## Pair-Scoring Model

model ที่เลือก: **gradient_boosting**

| Validation AP | AUC | Precision | Recall | F1 | Threshold |
|---:|---:|---:|---:|---:|---:|
| 0.979692 | 0.972393 | 0.9688 | 0.8997 | 0.9330 | 0.51 |

| Model | Validation AP | AUC | Precision | Recall | F1 | Threshold |
|---|---:|---:|---:|---:|---:|---:|
| logistic_regression | 0.941986 | 0.924229 | 0.8716 | 0.8431 | 0.8571 | 0.42 |
| gradient_boosting | 0.979692 | 0.972393 | 0.9688 | 0.8997 | 0.9330 | 0.51 |

`logistic_coefficients.csv` แสดง coefficient ที่ตีความง่าย ส่วน
`grouped_permutation_importance_validation.csv` แสดงผลกระทบเชิง predictive จาก validation
โดยไม่ผูกกับ model เดียว การตัดสินบทบาท feature ควรอ่านทั้งสองไฟล์ร่วมกัน ไม่ควรสรุปจาก coefficient ตัวเดียว

### Top 10 Feature Effects จาก Permutation Importance

ค่า AP delta คือ AP ที่ลดลงโดยเฉลี่ยเมื่อสลับค่าของ feature นั้นใน validation; ค่ายิ่งสูงแปลว่า model พึ่งพา feature นั้นมากขึ้นภายใต้ข้อมูลชุดนี้

| Feature | Group | AP delta | Std. |
|---|---|---:|---:|
| username_token_sort | name | 0.127410 | 0.002655 |
| fullname_token_sort | name | 0.071982 | 0.002183 |
| fullname_jaro | name | 0.041630 | 0.001188 |
| username_jaro | name | 0.021471 | 0.000863 |
| fullname_lev | name | 0.009836 | 0.000571 |
| bio_tfidf_cosine | bio | 0.006717 | 0.000511 |
| username_lev | name | 0.005322 | 0.000586 |
| bio_sbert_cosine | bio | 0.004410 | 0.000459 |
| platform_pair_code | other | 0.003820 | 0.000399 |
| url_available | url | 0.001100 | 0.000181 |

## Coverage และ Reliability

| Evidence group | Coverage ที่ใช้ได้ | Positive support เมื่อมีข้อมูล | Positive rate เมื่อ score >= 0.5 | ให้ global GA weight ได้ |
|---|---:|---:|---:|---|
| name | 99.42% | 4,355 | 0.596 | yes |
| bio | 66.18% | 3,005 | 0.954 | yes |
| url | 67.93% | 3,148 | 0.941 | yes |
| location | 0.00% | 0 | 0.000 | no |
| image | 10.02% | 450 | 1.000 | yes |
| style | 66.18% | 3,005 | 0.533 | yes |

group ที่ไม่ผ่านเกณฑ์ไม่ได้แปลว่าไร้ประโยชน์ แต่ sparse เกินกว่าจะให้ global weight ในรอบนี้ได้
เช่น image อาจเป็น override เฉพาะตอนมีข้อมูล และ location ยังต้องแก้ availability ก่อนนำไปตัดสินใจ

## ผลเปรียบเทียบ GA Guard

business cost ใช้สูตร $cost = 5FP + FN + 0.02REVIEW$ ดังนั้น false positive มีโทษสูงกว่า false
negative ห้าเท่า

| Guard | Validation cost | Val precision | Val recall | Val FP | Val FN | Val review |
|---|---:|---:|---:|---:|---:|---:|
| bio | 150.34 | 0.9989 | 0.6040 | 3 | 56 | 3967 |
| style | 151.66 | 0.9988 | 0.5885 | 3 | 56 | 4033 |
| score_only | 151.72 | 0.9988 | 0.5882 | 3 | 56 | 4036 |
| image | 152.68 | 0.9988 | 0.5882 | 3 | 57 | 4034 |
| url | 156.64 | 0.9985 | 0.5889 | 4 | 56 | 4032 |
| name | 468.36 | 0.9787 | 0.7241 | 69 | 56 | 3368 |

ผู้ชนะบน validation คือ **bio**. genome และ history ทุก generation เก็บใน
`selector_generation_history.json` และ `selector_leaderboard.csv`.

threshold ของ policy ที่ชนะคือ `[0.9962156842943379, 0.05, 0.6449967296706599, 0.0]` ตามลำดับ
`[match_threshold, review_threshold, promote_threshold, demote_threshold]`. สำหรับ winner นี้ GA ใช้
bio score ใน review band เพื่อ promote คู่ที่ evidence สูง โดยไม่ hard-code `name_sim`.

## Weighted Evidence GA

weighted policy ที่ GA เลือกมีน้ำหนักแบบ availability-conditioned ดังนี้:

| Evidence group | GA weight |
|---|---:|
| name | 0.3939 |
| bio | 0.0000 |
| url | 0.1186 |
| image | 0.1833 |
| style | 0.3043 |

validation metrics: `{"fp": 28, "fn": 56, "review": 3892, "precision": 0.9897323065639897, "recall": 0.6153670770633834, "f1": 0.7588921692675383, "cost": 273.84000000000003}`

น้ำหนักนี้ใช้เฉพาะ evidence ที่มีข้อมูลจริง และจะ normalize ใหม่ตามกลุ่มที่ใช้ได้ต่อคู่. weight ที่เป็นศูนย์
หมายความว่า GA ไม่พบว่ากลุ่มนั้นลด validation cost เพิ่มจากกลุ่มอื่นภายใต้ objective ปัจจุบัน ไม่ได้หมายความว่า feature นั้นไร้ค่าใน pair-scoring model

## ผล Sealed Test หนึ่งครั้ง

policy ที่ freeze แล้ว: **selector:bio**

test metrics: `{"fp": 7, "fn": 63, "review": 3812, "precision": 0.9973138910207214, "recall": 0.5924321860041031, "f1": 0.7433147433147432, "cost": 174.24}`

ผล test นี้เกิดหลังเลือก policy จาก validation เสร็จ และไม่มีการใช้ test เพื่อเลือก weight, threshold หรือ guard

## ข้อสรุปและการใช้งานต่อ

model-weight stage กับ GA stage ทำหน้าที่ต่างกันโดยตั้งใจ: pair-scoring model เรียนรู้ probability จาก feature value และ mask ส่วน GA ไม่แก้ parameter ของ model แต่เลือกวิธีใช้ frozen probability ร่วมกับ evidence ที่มีอยู่เพื่อให้ MATCH/REVIEW/NO_MATCH ตาม business cost

สำหรับข้อมูลชุดนี้ bio เป็น guard ที่ลด validation cost ได้ดีที่สุด ขณะที่ name guard เพิ่ม recall แต่สร้าง FP มากจน cost สูงมาก; จึงเป็นหลักฐานว่า `name_sim` ไม่ควรถูก hard-code เป็น policy guard. ก่อน promote production ให้ rebuild `decisioning_features.parquet` บน full 2.07M candidate population, ตรวจ coverage ใหม่, freeze policy ด้วย validation และเปิด sealed test ชุดใหม่เพียงครั้งเดียว
