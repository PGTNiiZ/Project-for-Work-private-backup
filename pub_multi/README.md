# pub_multi

แพ็กเกจนี้เป็นเวอร์ชันหลักของ pipeline แบบ multimodal สำหรับใช้ทำเล่ม รายงาน และตรวจงาน โดยรวม code, data, results, plots และ docs ไว้ในจุดเดียว

## แกนหลักที่เลือก

- main retrieval + production pipeline: `stage7_14_full_candidate_pipeline`
- main training pipeline: `stage7_13_multimodal_suite`
- main run: `image_context_r075_h20_s42`
- chosen model inside the run: `gb`

## ทำไมเลือกตัวนี้

- test AP = 0.9789
- test AUC = 0.9734
- test F1 = 0.9340
- ได้ composite score สูงสุดใน suite
- ตัวใกล้เคียงที่สุดคือ `image_stats` ซึ่งคะแนนใกล้มาก แต่ `image_context` ให้ AP/AUC สูงกว่าเล็กน้อยและสะท้อนแนวคิด multimodal ได้ครบกว่า

## ตัวเลขสำคัญ

- all cross-platform pairs: 449,149,239
- exact matches: 12,403
- candidate pairs for model: 2,073,842
- ground-truth coverage: 88.67%
- final match-only precision: 0.9550
- final match-only recall: 0.6711
- review queue: 86,296

## tuning ที่อ้างอิง

best tuning row จาก rebuilt experiment:
- random_neg_ratio = 0.75
- hard_neg_ratio = 2.0
- test_f1 = 0.9316

## Genetic algorithm tuning

`genetic_algorithm_tuning.py` ใช้ genetic algorithm เลือก feature พร้อม tune
hyperparameters ของ Gradient Boosting และ MATCH threshold โดยใช้ validation split
เป็น fitness เท่านั้น และประเมิน test split หลังจบการค้นหาหนึ่งครั้ง เพื่อป้องกัน
test leakage

รันแบบเต็ม:

```bash
python3.11 pub_multi/genetic_algorithm_tuning.py
```

ทดลองแบบเร็ว ก่อนสั่ง full search:

```bash
python3.11 pub_multi/genetic_algorithm_tuning.py \
  --population-size 6 --generations 3 \
  --max-train-rows 10000 --max-val-rows 3000
```

ผลลัพธ์อยู่ใน `pub_multi/ga_output/`: model pickle, selected features,
generation history และ JSON report ใช้ `--seed` เพื่อให้ผลทำซ้ำได้
