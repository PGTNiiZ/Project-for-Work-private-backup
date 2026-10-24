# รายงานการจัดระเบียบ Codebase

วันที่ดำเนินการ: **2026-08-18**

## ผลลัพธ์

โค้ดระบบหลักมี source of truth เดียวที่ `src/identity_resolution/` และเรียงตาม
ML lifecycle ชัดเจน:

```text
prepare → pairs → features → train → evaluate → predict → resolve
```

แต่ละขั้นเรียกผ่าน `identity-ml <stage>` ส่วนงาน R0–R6 ยังอยู่ใต้ `experiments/`
ในฐานะ research code และไม่ถูก production import

## กลุ่มที่ลบแล้ว

1. generated publication snapshots `pub_multi/src/s01_prep.py` ถึง `s12_imgpair.py`
2. generated PowerShell runners ใต้ `pub_multi/run/`
3. training scripts/wrappers ที่ซ้ำกับ canonical stages ใต้ `train_data/`
4. auxiliary Stage 8–18 Python code ใต้ `pipelines/`
5. maintenance/analysis scripts ใต้ `tools/`, `scripts/` และ bigram pipeline รุ่นเก่า
6. historical notebooks ใต้ `train_data/`, `bio_vector/`, `image_process/`, `data/`,
   `archive/` และ report notebook รุ่นเก่า

รายชื่อเชิงรายการอยู่ใน `docs/REMOVAL_CANDIDATES.md`

## กลุ่มที่ตั้งใจเก็บ

- source code หลักใน `src/identity_resolution/`
- research implementation และผล R0–R6
- dataset ทั้งหมด รวม CSV/Parquet และ normalized profiles
- model files, calibrator, scaler และ feature-column metadata
- JSON/CSV reports และ decision artifacts
- walkthrough notebook 9 ไฟล์สำหรับ reproduce งานทดลอง
- `pub_multi/src/genetic_optimizer.py` ซึ่งมี test รองรับ

## Evaluate stage

- CLI: `identity-ml evaluate`
- implementation: `src/identity_resolution/stages/evaluate.py`
- notebook: `notebooks/05_evaluate.ipynb`
- CLI artifact: `artifacts/evaluation/current_model_evaluation.json`
- notebook artifact: `artifacts/evaluation/notebook_model_evaluation.json`

threshold ถูกเลือกด้วย validation F1 (precision ใช้ตัดสินเมื่อเสมอ) แล้วล็อก threshold
ก่อนรายงาน test metrics จึงไม่ใช้ test labels เพื่อปรับ threshold

## การกู้คืน

ไฟล์ที่ Git เคยติดตามสามารถกู้จาก Git history ได้ แต่ cleanup รอบนี้ยังไม่ได้ commit
เพื่อให้เจ้าของ repository ตรวจ diff ก่อน ส่วนข้อมูล/model/report ไม่ได้อยู่ในขอบเขตลบ
