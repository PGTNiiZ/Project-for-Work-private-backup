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
| one_stage_weighted_10gene | 379.90 | 376.80 | 382.40 | 0.9927 | 0.8292 | 0.9037 | 10/10 |
| score_only_2threshold | 385.90 | 385.90 | 385.90 | 0.9930 | 0.8114 | 0.8931 | 10/10 |
| legacy_name_guard_4threshold | 475.00 | 475.00 | 475.00 | 0.9790 | 0.8411 | 0.9048 | 0/10 |

ผู้ชนะ one-stage ตาม cost คือ seed **45**: thresholds
`[0.946179, 0.105450]`, cost **376.80**,
Precision **0.9941**, Recall **0.8053**, F1 **0.8898**,
FP=21, FN=127, REVIEW=2,078.

เทียบ best legacy name guard: cost เปลี่ยน -98.20,
FP -58, FN +3,
REVIEW +148. เทียบ score-only: costเปลี่ยน
-9.10.

Bootstrap 95% CI ของ best one-stage: Precision
[0.9913, 0.9967], Recall
[0.7938, 0.8176], F1
[0.8827, 0.8974] และ cost
[346.90, 406.20].

## น้ำหนักที่ GA เรียนรู้

| Feature | Best-seed weight | Median 10 seeds | Std. |
|---|---:|---:|---:|
| probability | 0.767789 | 0.738538 | 0.095416 |
| name | 0.007792 | 0.003896 | 0.007960 |
| bio | 0.000000 | 0.006907 | 0.021229 |
| url | 0.004929 | 0.002951 | 0.009744 |
| location | 0.186584 | 0.189857 | 0.111749 |
| social | 0.023644 | 0.024500 | 0.024718 |
| image | 0.009263 | 0.010500 | 0.033323 |
| style | 0.000000 | 0.000000 | 0.000000 |

น้ำหนักเหล่านี้คือ **decision-policy weights** ไม่ใช่ feature importance หรือ coefficient ภายใน
pair model. ค่ามัธยฐานและส่วนเบี่ยงเบนใช้ดูความเสถียร; ห้ามตีความจาก best seed เพียงค่าเดียว.

## Coverage และ Support

| Feature | Coverage | Positive support | Positive rate เมื่อ score>=0.5 | Active |
|---|---:|---:|---:|---|
| probability | 100.00% | 4,386 | 0.9614 | yes |
| name | 99.42% | 4,355 | 0.5962 | yes |
| bio | 66.18% | 3,005 | 0.9542 | yes |
| url | 67.93% | 3,148 | 0.9412 | yes |
| location | 0.00% | 0 | 0.0000 | yes |
| social | 2.52% | 150 | 1.0000 | yes |
| image | 10.02% | 450 | 1.0000 | yes |
| style | 66.18% | 3,005 | 0.5329 | yes |

ทุก feature เปิดให้ GA เรียนรู้น้ำหนักได้; น้ำหนักศูนย์ในผลลัพธ์เป็นค่าที่ GA เลือกเอง.
Social ใช้ `max(mention_jaccard, hashtag_jaccard)` และ mask เปิดเมื่อทั้งสอง profile มี
mention/hashtag evidence. อ่าน coverage ในตารางประกอบการตีความน้ำหนัก.

## ข้อสรุป

ผลนี้เป็น **validation-only experiment** ซึ่งเลือกและวัด best seed บนชุดเดียวกัน;
bootstrap CI ไม่ได้รวมความไม่แน่นอนจากการเลือก policy. Legacy ใช้ population 60, generations 40
ขณะที่ one-stage และ score-only ใช้งบตาม protocol.json จึงไม่ใช่การเทียบด้วยงบค้นหาเท่ากัน.
การที่ policy มี cost ต่ำไม่ได้แปลว่าพร้อม production;
ต้องผ่าน precision/recall gates, ตรวจทุก platform pair, กำหนด review capacity และ freeze policy
ก่อนใช้ fresh audit test. Historical test เดิมไม่ได้ถูกเปิดซ้ำในรอบนี้.
