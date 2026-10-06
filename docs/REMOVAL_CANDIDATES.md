# Code removal record

ดำเนินการแล้วเมื่อ **2026-08-18** หลังได้รับคำยืนยันจากเจ้าของ repository

ไฟล์ด้านล่างไม่มี production dependency หลังย้าย canonical implementation เข้า
`src/identity_resolution/` แล้ว ข้อมูล, trained models, CSV/Parquet, reports และ
R0–R6 result artifacts ไม่อยู่ในรายการลบ

## Generated publication snapshots

ลบแล้ว: `pub_multi/src/s01_prep.py` ถึง `s12_imgpair.py`; `pub_multi/build_pkg.py`
สามารถสร้างใหม่จาก canonical `src/` ได้ ปัจจุบันเก็บ
`pub_multi/src/genetic_optimizer.py` เพราะมี test และเป็นงานที่กำลังพัฒนา

ลบ generated runners แล้ว: `pub_multi/run/r_feat.ps1`, `r_multi.ps1`, `r_full.ps1`,
`r_crm.ps1`

## Superseded training scripts — removed

- `train_data/leakage_safe_experiment/run_experiment.py` และ `.ps1`
- `train_data/stage7_8_rebuilt_experiment/run_rebuilt_pipeline.py` และ `.ps1`
- scripts ใต้ `train_data/stage7_8_rebuilt_experiment_tuned/`
- PowerShell wrappers ของ hybrid/multimodal/full-candidate/CRM
- `train_data/stage9_compare_features.py`
- `train_data/stage9_features_pipeline.py` รุ่น non-chunked
- top-level training PowerShell wrappers ใต้ `train_data/`
- compatibility Python wrappers ของ full-candidate และ CRM

Implementation ที่ใช้จริงของ prepare/pairs/features/train/evaluate/predict/resolve
อยู่ใน `src/identity_resolution/` แล้ว

## Historical auxiliary code — removed

- Python files ที่เหลือใต้ `pipelines/`
- `tools/fix-data-platform.py`, `tools/fix_numpy.py`
- `scripts/analysis/compare_pipeline_metrics.py`
- `scripts/image/advanced_embeddings.py`
- `bigram_username_and_fullname/bigram_full_pipeline.py`

ผลลัพธ์เดิมของ auxiliary experiments ยังเก็บใน `artifacts/decisioning/`

## Historical notebooks — removed

Notebook ใต้ `train_data/`, `bio_vector/`, `image_process/`, `data/`, `archive/`
และ `experiments/notebooks/REPORT_R0_R5.ipynb` ไม่มี execution path ใน production
ปัจจุบัน ไฟล์กลุ่มนี้ถูกลบแล้วตามคำยืนยัน โดยไม่ลบ dataset, model, report หรือ
ผลการทดลองที่ notebook เคยสร้างไว้

Walkthrough notebooks ใต้ `experiments/walkthroughs/` จะเก็บไว้ เพราะเป็นเอกสาร
reproducible ของ R0–R6 ไม่ใช่ notebook pipeline ซ้ำ

## สิ่งที่เก็บไว้

- canonical implementation ทั้งหมดใต้ `src/identity_resolution/`
- dataset ใต้ `data/`, `data_for_project/`, `train_data/`, `image_process/`
- trained model, calibrator, scaler และ feature metadata
- report/artifact ใต้ `artifacts/` และผล R0–R6
- walkthrough notebook 9 ไฟล์ใต้ `experiments/walkthroughs/`
- `pub_multi/src/genetic_optimizer.py` เพราะยังมี automated test รองรับ
- evaluation notebook ใหม่: `notebooks/05_evaluate.ipynb`

รายละเอียดการตรวจหลัง cleanup อยู่ที่ `docs/CLEANUP_REPORT_TH.md`
