# Training Decision Report (Task F)

รายละเอียดต่อ ID: `design/TRAINING_REQUIREMENTS.md` §2 (สร้างจาก matrix) · สถานะ: **NO-GO** — ห้าม train จนกว่า G0–G4 ผ่าน

## 1. การตัดสินต่อ component

| Component | ต้อง train ใหม่? | เหตุผลทางวิทยาศาสตร์ | GPU? | V2 IDs |
|---|---|---|---|---|
| Blocking rules (B0 exact + key) | ไม่ | ไม่มีพารามิเตอร์ที่เรียนจาก label | ไม่ | E1-1 |
| Token blocking | ไม่ | rule | ไม่ | E1-2 |
| TF-IDF char n-gram | ไม่ (fit vocabulary) | unsupervised แต่เป็น leakage risk ถ้า fit รวม test (ประวัติศาสตร์ fit ทุกโปรไฟล์ — R-06) | ไม่ | E1-3, E2-1 |
| Frozen bi-encoder (MiniLM ฯลฯ) | ไม่ (inference) | pretrained; ตรึง revision | ไม่ (CPU พอ: 36,807 โปรไฟล์) | E1-4, E4-1 |
| Hybrid retrieval | ไม่ | union/RRF | ไม่ | E1-5 |
| Supervised meta-blocking | **ใช่** | pruning classifier | ไม่ | E1-6 (CONDITIONAL) |
| Tuned weighted rule | ไม่ (parameter search ที่ใช้ label) | ต้องอยู่ใน protocol และ budget เท่า learner | ไม่ | E2-3 |
| Fellegi–Sunter EM | ไม่ (unsupervised EM) | — | ไม่ | E2-4 |
| LR / GBDT / RF | **ใช่ — RETRAIN ทั้งหมด** | โมเดลประวัติศาสตร์: split ไม่ตรง harness (R0), name_sim gated (R-08), test ใช้ซ้ำ (R-15), calibration prior shift (R-10) | ไม่ | E3-1, E3-2, E3-3, E4-2, E5-3, E5-4, E5-5, E5-6 |
| Fine-tuned bi-encoder / cross-encoder | **ใช่** (CONDITIONAL) | ทดสอบ H3b เฉพาะเมื่อ frozen ให้ผล หรือ FN ส่วนใหญ่เป็นแบบ semantic | **ใช่** | E4-3, E4-4 |
| Local LLM | ไม่ (prompting) | ต้อง G1 | ใช่ (inference) | E4-5 |
| Calibration (Platt/isotonic) | fit 1–2 พารามิเตอร์ | ต้อง fit บน OOF ที่ prior เท่ากับ test fold | ไม่ | E6-7 |
| GA / random / Sobol / TPE | ไม่ (policy optimisation, ไม่ใช่ classifier retraining) | budget 2,048 × 10 seeds | ไม่ | E6-4, E6-5, E6-6 |
| Closed-form cost / Chow | ไม่ | analytic | ไม่ | E6-3 |
| Fixed / historical rules | ไม่ | replicate policy เดิม | ไม่ | E6-1 |
| One-to-one assignment | ไม่ | post-processing | ไม่ | E6-8 |
| Bloom-encoded classifier | **ใช่** | feature space ใหม่ | ไม่ | E8-1 |
| Image feature classifier | **ใช่** | + frozen image encoder | อาจ | E9-1 |
| Entity clustering | ไม่ | — | ไม่ | E10-1 |

## 2. โมเดลที่ต้อง retrain (Q9)

ทุก classifier ที่ให้ผลใน V2: GBDT (E3-2, E5-3, E5-5, E5-4), LR (E3-1, E4-2/E5-3 robustness), semantic-only (E4-2) — **ไม่มีโมเดลประวัติศาสตร์ใดถูกใช้เป็นผล V2** (production multimodal, IdentityMLP R2, GB-17/18, ICSEC GB ทั้งหมด → EXCLUDE จากผล)

## 3. จำนวนงาน (จาก matrix)

| ชุด | Training jobs | Tuning fits | GPU jobs |
|---|---:|---:|---:|
| MVP (ESSENTIAL) | 217 | 2,400 | 0 |
| + SUPPORTING | 414 | 4,800 | 0 |
| ทั้งหมด | 669 | 5,600 | 30 (E4-3, E4-4) |

## 4. ลำดับที่ประหยัด compute

Baseline (E1-1, E2-3, E6-1) → Classical ML (E3-2) → Frozen semantic (E4-1 → E5-3) → Fusion/ablation (E5-5, E5-4) → Decision optimisation (E6-7 → E6-2/E6-3/E6-4 → E6-5) → Conditional fine-tuning (E4-3/E4-4) เฉพาะเมื่อผ่าน inclusion rule
