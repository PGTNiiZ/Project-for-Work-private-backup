# ผลทดลอง One-Stage Weighted GA: 2 Thresholds + 8 Feature Weights

## สิ่งที่เปลี่ยน

กฎเดิมใช้ genome 4 ค่า `[t_match, t_review, c_promote, c_demote]` และนำ `name_sim`
ไปเทียบทั้ง promote/demote cutoffs ใน review band. รอบนี้ตัด `c_promote/c_demote` ออกและใช้
genome 10 ค่า:

```text
[t_match, t_review,
 w_probability, w_name, w_bio, w_url,
 w_location, w_social, w_image, w_style]
```

คะแนนทั้งแปดตัวถูกถ่วงน้ำหนักและ normalize เฉพาะ feature ที่ available ต่อคู่ จากนั้นตัดสิน
เพียงครั้งเดียวด้วยสอง threshold. `probability` ถูกเก็บเป็นหนึ่งในแปด input เพื่อไม่ทิ้งสัญญาณ
non-linear จาก frozen pair model. ผลทั้งหมดด้านล่างใช้ **validation 8,580 คู่เท่านั้น** และไม่ได้อ่าน
หรือประเมิน held-out test.

## ผลหลาย Seed

| Policy | Median cost | Best | Worst | Median P | Median R | Median F1 | ผ่าน P>=.99 และ R>=.70 |
|---|---:|---:|---:|---:|---:|---:|---:|
| one_stage_weighted_10gene | 382.45 | 377.40 | 413.20 | 0.9914 | 0.8398 | 0.9093 | 9/10 |
| score_only_2threshold | 385.90 | 385.90 | 385.90 | 0.9930 | 0.8114 | 0.8931 | 10/10 |
| legacy_name_guard_4threshold | 475.00 | 475.00 | 475.00 | 0.9790 | 0.8411 | 0.9048 | 0/10 |

ผู้ชนะ one-stage ตาม cost คือ seed **43**: thresholds
`[0.929041, 0.098222]`, cost **377.40**,
Precision **0.9934**, Recall **0.8226**, F1 **0.9000**,
FP=24, FN=122, REVIEW=2,074.

เทียบ best legacy name guard: cost เปลี่ยน -97.60,
FP -55, FN -2,
REVIEW +144. เทียบ score-only: costเปลี่ยน
-8.50.

Bootstrap 95% CI ของ best one-stage: Precision
[0.9905, 0.9961], Recall
[0.8116, 0.8342], F1
[0.8933, 0.9072] และ cost
[346.59, 407.80].

## น้ำหนักที่ GA เรียนรู้

| Feature | Best-seed weight | Median 10 seeds | Std. |
|---|---:|---:|---:|
| probability | 0.943825 | 0.840662 | 0.087081 |
| name | 0.000000 | 0.000000 | 0.014000 |
| bio | 0.028275 | 0.030635 | 0.018070 |
| url | 0.000000 | 0.011887 | 0.059047 |
| location | 0.000000 | 0.000000 | 0.000000 |
| social | 0.027901 | 0.053375 | 0.033687 |
| image | 0.000000 | 0.019657 | 0.039357 |
| style | 0.000000 | 0.000000 | 0.004338 |

น้ำหนักเหล่านี้คือ **decision-policy weights** ไม่ใช่ feature importance หรือ coefficient ภายใน
pair model. ค่ามัธยฐานและส่วนเบี่ยงเบนใช้ดูความเสถียร; ห้ามตีความจาก best seed เพียงค่าเดียว.

## Coverage และ Support

| Feature | Coverage | Positive support | Positive rate เมื่อ score>=0.5 | Active |
|---|---:|---:|---:|---|
| probability | 100.00% | 4,386 | 0.9614 | yes |
| name | 99.42% | 4,355 | 0.5962 | yes |
| bio | 66.18% | 3,005 | 0.9542 | yes |
| url | 67.93% | 3,148 | 0.9412 | yes |
| location | 0.00% | 0 | 0.0000 | no |
| social | 2.52% | 150 | 1.0000 | yes |
| image | 10.02% | 450 | 1.0000 | yes |
| style | 66.18% | 3,005 | 0.5329 | yes |

Feature ที่ไม่มีข้อมูลหรือไม่ผ่าน coverage/support ตาม protocol.json ถูกบังคับน้ำหนักศูนย์: location
Social ใช้ `max(mention_jaccard, hashtag_jaccard)` และ mask เปิดเมื่อทั้งสอง profile มี
mention/hashtag evidence. อ่าน coverage ในตารางประกอบการตีความน้ำหนัก.

## ข้อสรุป

ผลนี้เป็น **validation-only experiment** ซึ่งเลือกและวัด best seed บนชุดเดียวกัน;
bootstrap CI ไม่ได้รวมความไม่แน่นอนจากการเลือก policy. Legacy ใช้ population 60, generations 40
ขณะที่ one-stage และ score-only ใช้งบตาม protocol.json จึงไม่ใช่การเทียบด้วยงบค้นหาเท่ากัน.
การที่ policy มี cost ต่ำไม่ได้แปลว่าพร้อม production;
ต้องผ่าน precision/recall gates, ตรวจทุก platform pair, กำหนด review capacity และ freeze policy
ก่อนใช้ fresh audit test. Historical test เดิมไม่ได้ถูกเปิดซ้ำในรอบนี้.
