# Training Requirements — Research V2 (v2 reconciled)

สถานะ: **PROPOSED** · ห้าม train โมเดลใดจนกว่า G0–G4 ผ่าน (G5 ต้องผ่านก่อนเปิด test) · การทดลองทางวิทยาศาสตร์: **NO-GO**

## Changes vs v1

| # | การเปลี่ยนแปลง | หลักฐาน |
|---|---|---|
| TR1 | Split: entity-atomic 5 folds ขนาดเท่ากัน (fold 5 = test; folds 1–4 cross-fitting) แทน TEST 20% + GroupKFold 5×3 — OOF scores ใช้กับ calibration และ policy เพื่อไม่ให้ prior ต่างจาก test | CONFIRMED_DEFECT calibration prior shift ของ ICSEC v2 [BACKUP@ab93b36:artifacts/audit/icsec_review_20261010/evidence.json#role_priors]; `EXPERIMENTAL_MASTER_PLAN_TH.md` §11 |
| TR2 | Tuning budget: 200 configs × 4 folds = 800 fits ต่อ learner×feature set (v1: 200 × 5 = 1,000) | ตามจำนวน development folds |
| TR3 | นับ training jobs รวม seed และ cross-fit folds (4 OOF + 1 refit = 5 fits ต่อ seed) | จำนวนแน่นอนใน `HYPOTHESIS_EXPERIMENT_MATRIX.csv` (`n_training_jobs`) |
| TR4 | ห้ามใช้ `name_sim` และ score จาก cache ประวัติศาสตร์ (`scored_pairs_enriched.parquet`) เป็น feature — CONFIRMED_DEFECT | [MAIN@1e0a2db:exp_lib.py#L93-L101 build_cache] |
| TR5 | TF-IDF/SBERT vocabulary & scaler fit บน train ของแต่ละ fold เท่านั้น (ประวัติศาสตร์ fit บนทุกโปรไฟล์) | [MAIN@1e0a2db:train_data/stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py#L305-L313 make_profile_bundle] |
| TR6 | E5-1 = E3-2 และ E5-2 = E4-2 (ไม่ train ซ้ำ); E2-2 retired | `review/ID_CHANGELOG.md` |
| TR7 | Policy optimisation budget 2,048 evals × 10 seeds ต่อ optimizer (random / scrambled Sobol / TPE / GA) | `EXPERIMENTAL_MASTER_PLAN_TH.md` M6 |

## 1. หลักการ

1. **ไม่ใช้โมเดลประวัติศาสตร์เป็นผลของ V2** — production multimodal model (F06/F07), IdentityMLP (F05/F09), GB-17/18 (F13/ICSEC) ทั้งหมด train บน split ที่ test ถูกใช้ซ้ำ หรือมี name_sim แบบ gated → RETRAIN ใหม่ทั้งหมดบน split ที่ freeze ใน G3
2. **ทุกการเลือก (hyperparameter, threshold, feature set, k, B*, M*) ทำบน development folds เท่านั้น**
3. **Budget เท่ากันสำหรับคู่ที่ถูกเปรียบเทียบ** (rule vs learner = 200 configs; GA vs non-GA = 2,048 evaluations)
4. **Seeds:** GBDT 5 seeds; LR deterministic (1); optimizer ทุกตัว 10 seeds; fine-tuning 3 seeds — รายงาน mean ± SD
5. **Artifacts ทุก run:** config, dataset hash + split manifest hash, code commit hash, lockfile, encoder revision, seed, metrics JSON, เวลา/ฮาร์ดแวร์ (ใช้รูปแบบ `artifact_hashes.json` / `split_manifest.json` ของ F12/F13 [MAIN@1e0a2db:experiments/automation/gb_transformer_primary_20260809/])

## 2. ตารางความต้องการ training (ทุก ID — จำนวนจาก matrix)

| Exp | ต้อง train? | ประเภท | Training jobs | Tuning fits | GPU | Priority | เหตุผลทางวิทยาศาสตร์ |
|---|---|---|---:|---:|---|---|---|
| D0-1 | No | — | 0 | 0 | No | ESSENTIAL | — |
| D0-2 | No | — | 0 | 0 | No | ESSENTIAL | — |
| D0-3 | No | — | 0 | 0 | No | ESSENTIAL | — |
| D0-4 | No | — | 0 | 0 | No | ESSENTIAL | — |
| D0-5 | No | — | 0 | 0 | No | OPTIONAL | — |
| E1-1 | No | — | 0 | 0 | No | ESSENTIAL | — |
| E1-2 | No | — | 0 | 0 | No | CONDITIONAL | — |
| E1-3 | No | fit vocabulary on D_train only | 0 | 0 | No | ESSENTIAL | — |
| E1-4 | No | frozen encoder | 0 | 0 | No (optional) | ESSENTIAL | — |
| E1-5 | No | — | 0 | 0 | No | ESSENTIAL | — |
| E1-6 | Yes | classifier for pruning | 25 | 0 | No | CONDITIONAL | ต้องมี pruning classifier — จำเป็นเฉพาะเมื่อ blocking ไม่ถึงเป้า |
| E2-1 | No | TF-IDF vocab on D_train only | 0 | 0 | No | ESSENTIAL | — |
| E2-2 | — | RETIRED | — | — | — | — | รวมเข้า E6-1 |
| E2-3 | No | parameter search on D_train (grouped CV) | 0 | 0 | No | ESSENTIAL | ไม่ใช่ supervised training แต่เป็น parameter search ที่ใช้ label → ต้องอยู่ใน protocol และใช้ budget เท่า T3 |
| E2-4 | No | unsupervised EM (5 inits) | 0 | 0 | No | OPTIONAL | EM ไม่ใช้ label |
| E3-1 | Yes | supervised | 17 | 800 | No | SUPPORTING | ต้อง train ใหม่: ไม่มี LR ประวัติศาสตร์ที่ train บน split ที่ผ่าน gate |
| E3-2 | Yes | supervised | 37 | 800 | No | ESSENTIAL | ต้อง train ใหม่: GB ประวัติศาสตร์ (F06/F13/ICSEC) train บน split ที่ test ถูกใช้ซ้ำและ name_sim แบบ gated |
| E3-3 | Yes | supervised | 25 | 800 | No | OPTIONAL | optional robustness |
| E4-1 | No | frozen encoder inference | 0 | 0 | No (optional) | ESSENTIAL | frozen encoder = inference เท่านั้น (ไม่ใช่ training) |
| E4-2 | Yes | supervised classifier | 30 | 1600 | No | SUPPORTING | classifier ใหม่บน F-SEM |
| E4-3 | Yes | fine-tuning | 15 | 0 | Yes | CONDITIONAL | fine-tune เพื่อทดสอบ H3b; GPU |
| E4-4 | Yes | fine-tuning | 15 | 0 | Yes | CONDITIONAL | fine-tune cross-encoder; GPU |
| E4-5 | No | prompting | 0 | 0 | Yes | OPTIONAL | prompting ไม่ใช่ training; ต้องการ GPU สำหรับ inference ของโมเดล local |
| E5-1 | ไม่ | alias | — | — | — | — | ใช้ artifact ของ E3-2/E3-1 |
| E5-2 | ไม่ | alias | — | — | — | — | ใช้ artifact ของ E4-2 |
| E5-3 | Yes | supervised | 30 | 1600 | No | ESSENTIAL | classifier ใหม่บน F-LEX ∪ F-SEM |
| E5-4 | Yes | supervised | 150 | 0 | No | SUPPORTING | classifier ต่อ feature set (hyperparameter ตรึงจาก E5-3) |
| E5-5 | Yes | supervised | 150 | 0 | No | ESSENTIAL | classifier ต่อกลุ่ม attribute (hyperparameter ตรึงจาก E3-2) |
| E5-6 | Yes | supervised | 50 | 0 | No | OPTIONAL | classifier ต่อ missing-handling |
| E6-7 | No | calibration fit (1-2 params) | 0 | 0 | No | ESSENTIAL | fit 1–2 พารามิเตอร์ (calibration) — ไม่ใช่ retraining |
| E6-1 | No | — | 0 | 0 | No | SUPPORTING | — |
| E6-2 | No | threshold sweep (99 values) | 0 | 0 | No | ESSENTIAL | — |
| E6-3 | No | analytic | 0 | 0 | No | ESSENTIAL | — |
| E6-4 | No | policy search 3 optimizers x 10 seeds x 2,048 evals | 0 | 0 | No | ESSENTIAL | policy optimisation (ไม่ใช่ classifier retraining) |
| E6-5 | No | policy search 10 seeds x 2,048 evals | 0 | 0 | No | ESSENTIAL | policy optimisation (ไม่ใช่ classifier retraining) |
| E6-6 | No | policy search 10 seeds x 2,048 evals | 0 | 0 | No | SUPPORTING | policy optimisation |
| E6-8 | No | assignment | 0 | 0 | No | CONDITIONAL | — |
| E7-1 | No | — | 0 | 0 | No | ESSENTIAL | — |
| E7-2 | No | — | 0 | 0 | No | ESSENTIAL | — |
| E7-3 | No | — | 0 | 0 | No | SUPPORTING | — |
| E7-4 | No | — | 0 | 0 | No | SUPPORTING | — |
| E7-5 | No | — | 0 | 0 | No | SUPPORTING | — |
| E7-6 | No | — | 0 | 0 | No | SUPPORTING | — |
| E7-7 | No | — | 0 | 0 | No | SUPPORTING | — |
| E8-1 | Yes | retrain classifier on encoded features | 100 | 0 | No | OPTIONAL | classifier ใหม่บน encoded features |
| E8-2 | No | policy search | 0 | 0 | No | OPTIONAL | — |
| E8-3 | No | — | 0 | 0 | No | OPTIONAL | — |
| E9-1 | Yes | supervised (+ frozen image encoder) | 25 | 0 | Optional | CONDITIONAL | classifier ใหม่ + frozen image encoder |
| E10-1 | No | — | 0 | 0 | No | CONDITIONAL | — |

**สรุป:** MVP มี supervised training เฉพาะ GBDT (E3-2, E5-3, E5-5) = 217 training jobs + 2,400 tuning fits — **ไม่มี GPU**; GPU จำเป็นเฉพาะ E4-3/E4-4 (CONDITIONAL, 30 jobs) และ E4-5 (OPTIONAL, inference)

## 3. Baseline การจำแนก training (ตาม prompt Task F)

| Component | สถานะ training | ใน V2 |
|---|---|---|
| Rules (B0 blocking, fixed policy, R0/stage18 rule) | ไม่มี supervised training | E1-1, E6-1 |
| TF-IDF | fit vocabulary ไม่ใช่ supervised แต่เป็น leakage risk → fit บน train fold เท่านั้น | E1-3, E2-1 |
| LR / GBDT | training ใหม่ | E3-1, E3-2, E4-2, E5-3/4/5 |
| Frozen encoder | inference เท่านั้น + classifier training | E1-4, E4-1 → E4-2/E5-3 |
| Fine-tuned Transformer | training ใหม่ (GPU) | E4-3, E4-4 |
| GA / random / Sobol / TPE | policy optimisation ไม่ใช่ classifier retraining | E6-4, E6-5, E6-6 |
| Hybrid retrieval | unsupervised | E1-5 |
| Fusion | classifier training | E5-3 |
| Multimodal | ขึ้นกับ coverage (Twitter เท่านั้นในประวัติศาสตร์) | E9-1 (CONDITIONAL) |

ลำดับที่ประหยัด compute: Baseline (E1-1, E2-3, E6-1) → Classical ML (E3-2) → Frozen semantic (E4-1, E5-3) → Fusion/ablation (E5-4, E5-5) → Decision optimisation (T6) → Conditional fine-tuning (E4-3/E4-4)

## 4. การแบ่งข้อมูลสำหรับ training

```
ทั้งหมด (15,297 entities + 3 singleton profiles)
├── Fold 5 = TEST (locked, ~20% entities) — เปิดครั้งเดียวหลัง G5
└── Folds 1–4 = DEVELOPMENT
    ├── Hyperparameter search: 4-fold grouped CV (200 configs)
    ├── OOF predictions ของ config ที่เลือก → calibration (E6-7) + policy search (T6)
    └── Refit บน folds 1–4 ทั้งหมด (ต่อ seed) → ทำนาย TEST
```

- Group = entity (`user_folder`); stratify ตาม platform-pair composition ของ entity
- คู่ข้าม fold ถูก drop และรายงานสัดส่วน (DESIGN_LIMITATION)

## 5. Negative sampling และ imbalance

- **Train:** อนุญาต downsample negative (ratio เลือกบน development เช่น 1:3 แบบประวัติศาสตร์, 1:10, natural) แต่ calibrate บน OOF ที่ prior ตามธรรมชาติของ fold
- **Development OOF / Test:** candidate set ตามธรรมชาติ ห้าม undersample
- **Hard negatives (fine-tuning):** top-k ที่ไม่ใช่ positive จาก E1-5 — ระวัง hidden positives (D0-3)

## 6. Learning curves (H2 secondary)

E2-3, E3-1, E3-2 ที่ 10%, 25%, 50% ของ entity ใน development (1 seed × 4 OOF folds ต่อจุด; 100% = run หลัก)

## 7. สิ่งที่ห้ามทำ

- ห้ามใช้โมเดล/score/prediction ประวัติศาสตร์เป็นผล V2 หรือเป็น feature
- ห้าม fit encoder/vectorizer ด้วยข้อมูลที่รวม test fold
- ห้ามปรับ GA hyperparameters หลังเห็นผล E6-4
- ห้ามส่งข้อมูลโปรไฟล์ไป API ภายนอกโดยไม่มีการอนุมัติ G1 เป็นลายลักษณ์อักษร
