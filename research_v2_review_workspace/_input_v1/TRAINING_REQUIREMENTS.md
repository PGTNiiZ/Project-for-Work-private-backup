# Training Requirements — Research V2

สถานะ: **PROPOSED** · ห้าม train โมเดลใดจนกว่า G0–G4 ผ่าน (G5 ต้องผ่านก่อนเปิด test)

## 1. หลักการ

1. **ไม่ใช้โมเดลประวัติศาสตร์เป็นผลของ V2** — ทุกโมเดลที่ให้ผลใน V2 ต้อง train ใหม่บน split ที่ freeze ใน G3 เพราะ split/label เดิมยังไม่ผ่านการตรวจ (HIST-UNVERIFIED)
2. **ทุกการเลือก (hyperparameter, threshold, feature set, k) ทำบน train+validation ผ่าน grouped CV เท่านั้น**
3. **Budget เท่ากันสำหรับคู่ที่ถูกเปรียบเทียบ** (rule vs learner; GA vs non-GA)
4. **Seeds:** โมเดล/optimizer ที่ stochastic รัน ≥ 5 seeds (GBDT, TPE, GA = 10 seeds; fine-tuning = 3 seeds) และรายงาน mean ± SD
5. **Artifacts ที่ต้องเก็บทุก run:** config (YAML), dataset hash + split manifest hash, code commit hash, library versions (lockfile), model revision (สำหรับ encoder), seed, metrics JSON, เวลา/ฮาร์ดแวร์

## 2. ตารางความต้องการ training

| Exp | ต้อง train? | ประเภท | ข้อมูลที่ใช้ fit | การเลือก | Seeds | GPU | หมายเหตุ |
|---|---|---|---|---|---|---|---|
| E1-1, E1-2 | ไม่ | rule | – | k บน validation | – | ไม่ | |
| E1-3 | ไม่ (fit vocabulary) | unsupervised | train accounts เท่านั้น | k | – | ไม่ | ห้าม fit TF-IDF รวม test |
| E1-4 | ไม่ | frozen encoder | – | k | – | ทางเลือก | ระบุ model revision |
| E1-5 | ไม่ | combination | – | union vs RRF บน validation | – | ไม่ | |
| E1-6 | **ใช่** | supervised (pruning classifier) | train | grouped CV | 5 | ไม่ | optional |
| E2-1 | ไม่ | feature extraction | TF-IDF vocab จาก train | – | – | ไม่ | |
| E2-2 | ไม่ | fixed rule | – | – | – | ไม่ | ต้องได้สูตรจาก repo |
| E2-3 | ไม่ (parameter search) | weight/threshold search | validation (inner CV) | random search 200 | 5 | ไม่ | budget = T3 |
| E2-4 | ไม่ (unsupervised EM) | probabilistic | train (ไม่ใช้ label) | – | 5 inits | ไม่ | optional |
| E3-1 | **ใช่** | supervised LR | train | grouped CV, 200 configs | 1 (deterministic) | ไม่ | |
| E3-2 | **ใช่** | supervised GBDT | train | grouped CV, 200 configs | 5 | ไม่ | early stopping บน inner fold |
| E3-3 | **ใช่** | supervised RF | train | grouped CV | 5 | ไม่ | optional |
| E4-1 | ไม่ | frozen inference | – | เลือก encoder ≤ 2 ตัวบน validation | – | ทางเลือก | |
| E4-2 / E5-2 | **ใช่** (classifier) | supervised | train | grouped CV | 5 | ไม่ | |
| E4-3 | **ใช่** | fine-tune bi-encoder | train positives + hard negatives | validation early stop | 3 | **ใช่** | conditional |
| E4-4 | **ใช่** | fine-tune cross-encoder | train pairs | validation early stop | 3 | **ใช่** | conditional |
| E4-5 | ไม่ | prompting | few-shot จาก train | prompt freeze ที่ G4 | 3 (sampling) | **ใช่** (local LLM) | BLOCKED by G1 |
| E5-1, E5-3, E5-4, E5-5 | **ใช่** | supervised (LR & GBDT) | train | grouped CV | 5 | ไม่ | E5-4/E5-5 = หนึ่ง run ต่อกลุ่ม attribute |
| E5-6 | **ใช่** | supervised | train | grouped CV | 5 | ไม่ | optional |
| E6-7 | fit 1–2 พารามิเตอร์ | calibration | calibration fold (แยกจาก fold ที่ใช้ early stop) | Platt vs isotonic | – | ไม่ | |
| E6-1…E6-3 | ไม่ | analytic/threshold | validation | – | – | ไม่ | |
| E6-4, E6-5 | ไม่ (policy optimization) | search | validation (inner CV) | 2,000 evals | 10 | ไม่ | ห้ามแตะ test |
| E6-6, E6-8 | ไม่ | search / assignment | validation | – | 10 | ไม่ | |
| E7-* | ไม่ | evaluation | locked test | – | – | ไม่ | ใช้โมเดลที่ freeze |
| E8-1 | **ใช่** (retrain classifier) | supervised on encoded features | train | grouped CV | 5 | ไม่ | optional/BLOCKED |
| E9-1 | **ใช่** | supervised (+frozen image encoder) | train | grouped CV | 5 | ทางเลือก | optional/BLOCKED |
| E10-1 | ไม่ | clustering | – | validation | – | ไม่ | optional |

**สรุป:** core program มี supervised training เฉพาะ classical classifiers (LR, GBDT) — **ไม่มี GPU training ใน minimum program**; GPU จำเป็นเฉพาะ E4-3/E4-4 (conditional) และ E4-5 (optional)

## 3. การแบ่งข้อมูลสำหรับ training

```
ทั้งหมด (identity clusters)
├── TEST (locked, ~20% ของ identity) — เปิดครั้งเดียวที่ E7-1
└── DEVELOPMENT (~80%)
    ├── Outer: GroupKFold 5 folds × 3 repeats (group = identity) → ประมาณ performance บน dev สำหรับ selection
    └── Inner: สำหรับ hyperparameter / threshold / calibration
        └── calibration fold แยกจาก early-stopping fold
```

- Group = identity cluster (บัญชีทุกตัวของคนเดียวกันอยู่ split เดียวกัน) **และ** ถ้าบัญชี B ปรากฏใน candidate ของหลาย identity ให้ใช้ connected component ของกราฟ candidate เป็น group เมื่อ component เล็กพอ (ตรวจใน D0-4)
- Stratify ตาม platform pair
- ถ้าข้อมูลมีเวลา: เพิ่ม out-of-time holdout (G5)

## 4. Negative sampling และ imbalance

- **Train:** อนุญาต downsample negative (ratio ที่เลือกบน validation เช่น 1:10, 1:50, natural) แต่ต้อง **calibrate บน validation ที่ prior ตามธรรมชาติ**
- **Validation/Test:** ใช้ candidate set ตามธรรมชาติ ห้าม undersample
- **Hard negatives:** สำหรับ fine-tuning (E4-3/E4-4) ใช้ top-k candidates ที่ไม่ใช่ positive จาก E1-5 — ระวัง hidden positives (D0-3); ทางเลือก: กรองคู่ที่ similarity สูงมากออกจาก negative ของ train

## 5. Learning curves (เพื่อ H2)

E3-1, E3-2, E2-3 รันที่ 10%, 25%, 50%, 100% ของ train (identity-level subsampling) — ตอบว่า learned matcher ต้องการข้อมูลเท่าไรจึงชนะ tuned rule

## 6. สิ่งที่ห้ามทำ

- ห้ามใช้โมเดล GB/MiniLM/BERT ที่ train ไว้ในงานเดิมเป็นผล V2
- ห้าม fine-tune encoder ด้วยข้อมูลที่รวม test accounts (แม้ไม่มี label)
- ห้ามปรับ GA hyperparameters หลังเห็นผล E6-4
- ห้ามส่งข้อมูลโปรไฟล์ไป API ภายนอก (LLM hosted) โดยไม่มีการอนุมัติ G1 เป็นลายลักษณ์อักษร
