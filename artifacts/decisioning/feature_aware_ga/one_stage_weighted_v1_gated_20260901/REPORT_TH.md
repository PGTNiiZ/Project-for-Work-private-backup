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
| one_stage_weighted_10gene | 380.00 | 378.50 | 414.60 | 0.9932 | 0.8174 | 0.8968 | 9/10 |
| score_only_2threshold | 385.90 | 385.90 | 385.90 | 0.9930 | 0.8114 | 0.8931 | 10/10 |
| legacy_name_guard_4threshold | 475.00 | 475.00 | 475.00 | 0.9790 | 0.8411 | 0.9048 | 0/10 |

ผู้ชนะ one-stage ตาม cost คือ seed **50**: thresholds
`[0.929269, 0.113674]`, cost **378.50**,
Precision **0.9933**, Recall **0.8144**, F1 **0.8950**,
FP=24, FN=127, REVIEW=2,035.

เทียบ best legacy name guard: cost เปลี่ยน -96.50,
FP -55, FN +3,
REVIEW +105. เทียบ score-only: costเปลี่ยน
-7.40.

Bootstrap 95% CI ของ best one-stage: Precision
[0.9905, 0.9961], Recall
[0.8030, 0.8267], F1
[0.8879, 0.9027] และ cost
[347.60, 407.62].

## น้ำหนักที่ GA เรียนรู้

| Feature | Best-seed weight | Median 10 seeds | Std. |
|---|---:|---:|---:|
| probability | 0.922176 | 0.923987 | 0.079421 |
| name | 0.027208 | 0.000000 | 0.008432 |
| bio | 0.000000 | 0.022477 | 0.034375 |
| url | 0.017648 | 0.000000 | 0.077036 |
| location | 0.000000 | 0.000000 | 0.000000 |
| social | 0.000000 | 0.000000 | 0.000000 |
| image | 0.032968 | 0.020737 | 0.013809 |
| style | 0.000000 | 0.000000 | 0.007059 |

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
| social | 2.52% | 150 | 1.0000 | no |
| image | 10.02% | 450 | 1.0000 | yes |
| style | 66.18% | 3,005 | 0.5329 | yes |

Feature ที่ coverage ต่ำกว่า 5% หรือ positive support ต่ำกว่า 100 ถูกบังคับ weight เป็นศูนย์ เพราะ
น้ำหนัก global ยังระบุได้ไม่น่าเชื่อถือ. Social ใช้ `max(mention_jaccard, hashtag_jaccard)` และ mask
จะเปิดเมื่อทั้งสอง profile มี mention/hashtag evidence; รอบนี้ coverage 2.52% จึงยังไม่ active.

## ข้อสรุป

ผลนี้เป็น **validation-only experiment**. การที่ policy มี cost ต่ำไม่ได้แปลว่าพร้อม production;
ต้องผ่าน precision/recall gates, ตรวจทุก platform pair, กำหนด review capacity และ freeze policy
ก่อนใช้ fresh audit test. Historical test เดิมไม่ได้ถูกเปิดซ้ำในรอบนี้.
