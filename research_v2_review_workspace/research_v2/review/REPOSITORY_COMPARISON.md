# Repository Comparison — MAIN vs BACKUP

วันที่: 2026-10-25 · แหล่ง: `_work/corresponding_files.csv` (sha256 ต่อไฟล์, 9,564 คู่ path), `_work/agentA/cross_repo_function_comparison.json` (AST ต่อ function), `diff` ของ `git show` (Lead + Agent A2 `_work/agentA2/BACKUP_VS_MAIN.md`)

## 1. ความสัมพันธ์ของเวอร์ชัน

| ประเด็น | ผล | หลักฐาน |
|---|---|---|
| ancestry | ไม่มี commit ร่วม: BACKUP@903246c และ BACKUP@ab93b36 เป็น root commit; `git merge-base` ไม่คืนค่า | `git rev-list --parents` |
| ไฟล์ path ตรงกัน | IDENTICAL_GIT_BLOB 8,986 · DIFFERENT 578 | `_work/corresponding_files.csv` |
| backup "ใหม่กว่า" หรือไม่ | **ไม่สันนิษฐาน**: BACKUP เก็บโค้ดที่รัน ICSEC จาก working tree ที่ไม่ commit บน MAIN@1e0a2db (dirty) — คือ "ใหม่กว่าในเวลา" สำหรับ ICSEC/feature-aware/reviewer แต่โค้ด R-series เป็นสำเนา import/path ของ MAIN | [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2r1/provenance/v2r1_manifest.json#git_commit,git_dirty] |
| Layout | MAIN: script การทดลองอยู่ root; BACKUP: `experiments/code/` (package `experiments.code`) + `src/identity_resolution/` | inventory |

## 2. ไฟล์การทดลองที่สอดคล้องกัน (file-level SHA-256 + function-level diff)

| ไฟล์ | MAIN@1e0a2db sha256[:12] | BACKUP@903246c sha256[:12] | เท่ากัน? | Function ที่ต่าง (AST) | ความต่างเชิงเนื้อหา |
|---|---|---|---|---|---|
| exp_lib.py | cc8d7c28b5fe | 984adb9cf584 | ไม่ | 0/12 | path เท่านั้น: `ROOT`, `PFW`, `BLOCKING_MISSED` ย้ายไป `artifacts/decisioning/analysis_decision_matrix/` [MAIN@1e0a2db:exp_lib.py#L17-L21] vs [BACKUP@903246c:experiments/code/exp_lib.py#L17-L21] |
| exp_r1_ga_redecision.py | 6403ce71d916 | b6dc3eede40e | ไม่ | 1/13 (`cost_from_counts`) | **ค่า cost เริ่มต้น 5/1/0.02 → 2/1/0.1 (crm_derived_v1)** [MAIN@1e0a2db:exp_r1_ga_redecision.py#L15-L31] vs [BACKUP@903246c:experiments/code/exp_r1_ga_redecision.py#L11-L21] |
| exp_r2_bert_feature.py | d50c460ba3d5 | 98da5cb8b2d9 | ไม่ | 0/26 | import style |
| exp_r4_bloom_privacy.py | 5d8abf546c2f | 91a0a93b4b34 | ไม่ | 1/10 (`main`) | import + ข้อความ error |
| exp_r6_bert_er.py | b67f3a0b2e7e | c061400c4564 | ไม่ | 1/20 (`build_training_pairs`) | import ของ `bucket` (try/except) — ไม่มี logic เปลี่ยน |
| run_ga_experiments.py | d3d35daf4991 | 2568a427c2aa | ไม่ | (ไม่อยู่ใน AST JSON) | scenario `A_current` เปลี่ยนเป็น `CostWeights()` = 2/1/0.1 [MAIN@1e0a2db:run_ga_experiments.py#L228] vs [BACKUP@ab93b36:experiments/code/run_ga_experiments.py#L236] |
| run_gb_transformer_experiments.py | 51e29bd57a48 | 52b1aedaf909 | ไม่ | 1/28 (`run`) | `GA_WEIGHTS` 5/1/0.02 → 2/1/0.1 [MAIN@1e0a2db:run_gb_transformer_experiments.py#L67] vs [BACKUP@ab93b36:experiments/code/run_gb_transformer_experiments.py#L69] |
| build_r0_r3_report.py | ec8e6aa84e75 | ec8e6aa84e75 | **ใช่** | 0 | — |
| stage9_features_pipeline_chunked.py ↔ src/.../stages/features.py | — | — | ไม่ | 1/29 (`_load_profile_image_module`) | module path |
| stage15 run_crm_entity_pipeline.py ↔ src/.../workflows/crm.py | — | — | ไม่ | 3/11 (`build_feature_engine`, `build_match_decisions`, `ensure_dirs`) | path/structure (ค่า threshold 0.98/0.95 คงเดิม [BACKUP@ab93b36:src/identity_resolution/workflows/crm.py#L341-L344]) |
| tests/test_ga_runner.py | — | — | ไม่ | 4 test symbols | น้ำหนักที่คาด 5/1/0.02 → 2/1/0.1 + `legacy_config` สำหรับ regression กับ artifact เดิม |
| tests/test_ga_threshold.py | — | — | ไม่ | + `test_default_cost_is_crm_derived_v1` | — |
| tests/test_nested_protocol.py, test_r2_training.py | — | — | ไม่ | 0 | import |
| ไฟล์ที่มีเฉพาะ BACKUP | — | — | — | — | ICSEC v2/v2r1, reviewer revision, feature-aware GA, name-sim, `src/identity_resolution/**`, 12 test files |
| ไฟล์ที่มีเฉพาะ MAIN | — | — | — | — | notebook pipeline (`train_data/*.ipynb`), `bigram_*`, `bio_vector/`, `image_process/` (+ภาพ 4,248 ไฟล์), ข้อมูลดิบไม่ใช้ LFS |

**ผลสุทธิ:** การจัดระเบียบใหม่ใน BACKUP เป็น import/path เป็นหลัก มี **การเปลี่ยนเชิงความหมายหนึ่งจุด: ค่า cost เริ่มต้นของ GA** → การรัน R-series จาก BACKUP จะไม่ reproduce artifact ของ MAIN ถ้าไม่ส่ง legacy weights เอง

## 3. แต่ละการทดลองรันจาก repo ใด (เฉพาะที่ log/path พิสูจน์ได้)

| Artifact family | หลักฐาน | รันจาก |
|---|---|---|
| R0–R6 legacy JSON (`experiments/r*_results.json`) | weights ที่บันทึก = 5/1/0.02 [MAIN@1e0a2db:experiments/r1_results.json#weights] = ค่า default ของ MAIN | **โค้ดแบบ MAIN** (commit ที่แน่นอน UNKNOWN — ไฟล์ถูก commit ครั้งเดียวที่ 1f57da1) |
| R-series automation (2026-08-08/09) | config บันทึก path Windows `D:\...\Code\experiments\scored_pairs_enriched.parquet` และ weights 5/1/0.02 [BACKUP@ab93b36:experiments/automation/r3_primary_20260809/config.json#input_artifacts] | **โค้ด layout MAIN บนเครื่อง Windows**; commit UNKNOWN |
| GB-transformer primary | `runner_source.sha256` = MAIN `run_gb_transformer_experiments.py`; `ga_source.sha256` = MAIN `exp_r1_ga_redecision.py`; แต่ `exp_lib_source`/`r2_source` ไม่ตรงกับ blob ใดใน repo [BACKUP@ab93b36:experiments/automation/gb_transformer_primary_20260809/summary.json#input_artifacts] | **MAIN** (runner/GA); exp_lib/r2 = variant ที่ไม่ commit (UNKNOWN) |
| ICSEC v1 authoritative_run | `git_commit.txt` = 1e0a2db + dirty; SHA256SUMS ของ runner = blob ใน BACKUP@ab93b36 | **working tree ไม่ commit บน MAIN@1e0a2db; โค้ด = BACKUP** |
| ICSEC v2/v2r1 | v2r1 manifest: source sha256 ตรงกับ BACKUP; preflight v2 ใช้ runner รุ่นก่อน (16,826 bytes) ที่ต่างจากที่ commit (25,345 bytes) | **working tree (MAIN HEAD, dirty) → code = BACKUP@903246c/ab93b36** |
| Reviewer revision | provenance hashes = BACKUP@903246c | **BACKUP** |
| Feature-aware GA, name-sim N0–N6 | path `/Users/thawaree.kha/Project-for-Work/...`; import `identity_resolution.*`; ไม่มี source hash | layout BACKUP; revision UNKNOWN |

## 4. ข้อพึงระวังสำหรับ V2

1. ระบุ cost weights อย่างชัดแจ้งในทุก config (อย่าพึ่ง default ที่ต่างกันระหว่าง repo)
2. ใช้ source sha256 + commit ที่ clean ใน run manifest (บทเรียน: ICSEC รันจาก dirty tree)
3. โค้ดที่จะใช้ซ้ำควรมาจาก BACKUP (มี sealed-label store, name_sim แก้แล้ว) แต่ต้องตรวจกับ test สังเคราะห์ก่อน
