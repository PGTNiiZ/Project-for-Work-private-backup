# Repository Research Inventory — Research V2 Evidence Review

วันที่ตรวจ: 2026-10-25 · ผู้ตรวจ: Lead (+ Agent A2 สำหรับ backup repo) · สถานะการทดลองทางวิทยาศาสตร์: **NO-GO**

> เอกสารนี้เป็น *ทะเบียน* ของสิ่งที่มีอยู่จริงใน repository (V-REPO) ไม่ใช่การยืนยันว่าผลถูกต้อง
> ไฟล์ข้อมูลไม่ได้ถูกเปิดเกิน header/สถิติระดับ schema (row count, missingness) ตาม §2 ของ prompt
> รายการไฟล์ทั้งหมดพร้อม SHA-256: `review/_work/repository_inventory.csv` (19,610 entries จาก 5 snapshot) ·
> สรุปตัวเลข: `review/_work/inventory_summary.json` · สคริปต์: `review/_work/scripts/inventory.py`

---

## 1. Snapshot ที่ตรวจ (HEAD ทุก branch)

| Repo | Ref | Commit | วันที่ commit | หมายเหตุ |
|---|---|---|---|---|
| MAIN `PGTNiiZ/Project-for-Work` | `main`, `origin/HEAD` | `1e0a2db` | 2026-08-10 | snapshot หลักของงาน R0–R6 + GB/automation |
| MAIN | `origin/docs/project-reorganization-plan` | `50d95e9` | 2026-10-24 | = 1e0a2db + เอกสาร status/reorganization (+2 plan files) |
| MAIN | `origin/work/safe-20260309-173639` | `08f4c5e` | 2026-03-12 | snapshot ช่วง notebook pipeline รุ่นแรก (9,911 data files) |
| BACKUP `PGTNiiZ/Project-for-Work-private-backup` | `main` | `903246c` | 2026-10-06 | source + reviewer revision (401 files) |
| BACKUP | `origin/transfer/2026-10-24-full` | `ab93b36` | 2026-10-24 | full workspace snapshot (6,077 files, 801 LFS pointers) |
| LOCAL (เครื่องผู้ใช้) | `backup/2026-10-24-full-transfer` | `a2dce39` | 2026-10-24 | branch ในเครื่อง ไม่พบใน remote ทั้งสอง; ไม่ได้ใช้เป็นหลักฐานหลัก |
| LOCAL | `research/phase15-*` (7 branches) | `1e0a2db` | — | ไม่มี commit ใหม่; เนื้อหาที่ยังไม่ commit ถูกเก็บใน `handoff/worktrees/` ของ BACKUP@ab93b36 |

หลักฐาน: `review/_work/main_refs.txt`, `review/_work/backup_refs.txt`, `git for-each-ref` บนเครื่องผู้ใช้

**ความสัมพันธ์ของเวอร์ชัน (ไม่สันนิษฐานว่า backup ใหม่กว่า):**
- BACKUP ไม่มี commit ร่วมกับ MAIN: ทั้ง 903246c และ ab93b36 เป็น root commit (`git rev-list --parents` ไม่มี parent) และ `git merge-base 1e0a2db 903246c` ไม่คืนค่า → ความสัมพันธ์ต้องวัดด้วย checksum ระดับไฟล์
- เทียบไฟล์ที่ path สอดคล้องกัน 9,564 คู่: **IDENTICAL_GIT_BLOB 8,986 คู่ · DIFFERENT 578 คู่** (`review/_work/corresponding_files.csv`)
- โค้ดการทดลองใน BACKUP ถูกย้ายไป `experiments/code/` และเปลี่ยน import path; function-level ต่างเพียงเล็กน้อย (ดู `REPOSITORY_COMPARISON.md`)

## 2. การจำแนกไฟล์ (นับจาก inventory)

| Snapshot | ไฟล์ทั้งหมด | plan | code | config | data | result | paper | test | LFS pointer |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| MAIN@1e0a2db | 4,823 | 72 | 109 | 2 | 4,497 | 137 | 0 | 5 | 0 |
| MAIN@50d95e9 | 4,825 | 74 | 109 | 2 | 4,497 | 137 | 0 | 5 | 0 |
| MAIN@08f4c5e | 9,962 | 1 | 24 | 2 | 9,911 | 24 | 0 | 0 | 0 |
| BACKUP@903246c | 401 | 75 | 75 | 2 | 105 | 6 | 121 | 17 | 0 |
| BACKUP@ab93b36 | 6,077 | 229 | 152 | 4 | 5,148 | 385 | 127 | 31 | 801 |

หมายเหตุ: MAIN ไม่มี `.gitattributes` และไม่มี LFS → ไฟล์ข้อมูลถูก commit เป็น blob เต็ม; BACKUP@ab93b36 ใช้ LFS สำหรับ `*.csv, *.parquet, *.npy, *.npz, *.pt, *.pkl, *.zip, *.xlsx, *.part` [BACKUP@ab93b36:.gitattributes#L1-L10]

## 3. Path ที่ prompt ระบุ — สถานะการพบ

| Path | MAIN@1e0a2db | BACKUP@903246c | BACKUP@ab93b36 |
|---|---|---|---|
| `EXPERIMENT_PLAN.md` | FOUND (root) | FOUND (`docs/plans/EXPERIMENT_PLAN.md`) | FOUND |
| `experiments/REPORT_R0_R5.md` | FOUND | NOT_FOUND (path นี้) | ตรวจโดย Agent A2 |
| `experiments/R6_GPU_IMPLEMENT_PLAN.md` | FOUND | NOT_FOUND (path นี้) | ตรวจโดย Agent A2 |
| `data_for_project/` | FOUND (มีไฟล์โปรไฟล์ดิบ — ดู §6) | NOT_FOUND | ตรวจโดย Agent A2 |
| `train_data/` | FOUND | NOT_FOUND | FOUND บางส่วน |
| `image_process/` | FOUND | NOT_FOUND (ย้ายเป็น `src/identity_resolution/imaging/`) | — |
| `pub_multi/` | FOUND | FOUND | FOUND |
| `docs/plans/`, `docs/reports/` | NOT_FOUND | FOUND | FOUND |
| `experiments/code/` | NOT_FOUND (โค้ดอยู่ที่ root) | FOUND (22 ไฟล์) | FOUND |
| `src/identity_resolution/` | NOT_FOUND | FOUND (32 ไฟล์) | FOUND |
| `tests/` | FOUND (5 ไฟล์) | FOUND (17 ไฟล์) | FOUND (31 ไฟล์) |
| `paper/`, `manuscript/` | NOT_FOUND | FOUND | FOUND |

## 4. แผนที่ตระกูลการทดลอง (experimental families) → path หลัก

| # | Family | Path หลัก (ตัวอย่าง) | ช่วงเวลา (git) |
|---|---|---|---|
| F01 | Original lexical matching (username/fullname/difflib + image embedding) | MAIN@64d3b0b:`match_profile.py`, `enhanced_matching.py`, `evaluate_matching.py` | 2026-01-14 → 02-16 |
| F02 | Bigram username/fullname retrieval + LR/SGD/RF ranking (+location) | MAIN@1e0a2db:`bigram_username_and_fullname/bigram_full_pipeline.py`; `data/processed/bigram_pipeline_results*/` | 2026-02-16 → 03-21 |
| F03 | SBERT/MPNet bio vector matching | MAIN@1e0a2db:`bio_vector/sbert_mpnet_matching.ipynb`, `vector_embredding.ipynb` | 2026-02-24 → |
| F04 | Image features (pHash/dHash, caption, ArcFace) | MAIN@1e0a2db:`image_process/*`; BACKUP:`src/identity_resolution/imaging/*` | 2026-01 → 08 |
| F05 | Notebook pipeline v1/v2 (stage7–17, IdentityMLP 17 features, FocalLoss) | MAIN@1e0a2db:`train_data/stage*.ipynb`, `train_data/v2/*` | 2026-03-14 → 03-18 |
| F06 | Leak-safe rebuilt/hybrid pipeline + multimodal suite (TF-IDF+SBERT+attribute+image; LR/GB/RF) | MAIN@1e0a2db:`train_data/stage7_8_rebuilt_experiment_hybrid/`, `stage7_13_multimodal_suite/`, `pub_multi/bench_*.py` | 2026-03 → 08 |
| F07 | Full-candidate pipeline (exact tier + key blocking) + CRM entity resolution | MAIN@1e0a2db:`train_data/stage7_14_full_candidate_pipeline/`, `stage15_crm_entity_pipeline/`; BACKUP:`src/identity_resolution/workflows/{full_candidate,crm}.py` | 2026-07 → 10 |
| F08 | R0 baseline + R1 GA re-decision | MAIN@1e0a2db:`exp_lib.py`, `exp_r1_ga_redecision.py`, `run_ga_experiments.py` | 2026-07-20 → 08-10 |
| F09 | R2/R3 MiniLM semantic feature (+GA) | MAIN@1e0a2db:`exp_r2_bert_feature.py` | 2026-08 |
| F10 | R4/R5 Bloom-filter encoding (+GA) | MAIN@1e0a2db:`exp_r4_bloom_privacy.py`, `experiments/bloom/` | 2026-08 |
| F11 | R6 BERT-ER semantic hash blocking | MAIN@1e0a2db:`exp_r6_bert_er.py`, `experiments/R6_GPU_IMPLEMENT_PLAN.md` | 2026-08 |
| F12 | Nested-protocol GA automation (multi-seed, cost sensitivity) | MAIN@1e0a2db:`experiments/automation/r1_*`, `r3_*` | 2026-08-08 → 09 |
| F13 | GB-17 / GB-18 / GB-18-GA (classical ML + MiniLM) | MAIN@1e0a2db:`run_gb_transformer_experiments.py`, `experiments/automation/gb_transformer_*` | 2026-08-09 |
| F14 | Feature-aware GA / policy weight optimisation / one-stage weighted GA | BACKUP:`experiments/code/run_*feature_aware*`, `run_one_stage_weighted_ga_experiment.py` | 2026-08-31 → 10 |
| F15 | Name-similarity ablation & feature attribution | BACKUP:`experiments/code/exp_name_similarity_ablation.py`, `exp_feature_attribution.py` | 2026-09 → 10 |
| F16 | ICSEC experiments (authoritative run v2/v2r1, repeated outer) | BACKUP:`experiments/code/run_icsec_*`, `experiments/icsec_final/**`, `paper/**` | 2026-09 → 10 |
| F17 | Reviewer-driven revision | BACKUP:`experiments/code/reviewer_revision.py`, `paper/reviewer_revision/`, `experiments/icsec_final/reviewer_revision/` | 2026-10 |
| F18 | Research rebuild / phase-15 gates (feature spec, split safety, evaluator, run isolation, governance, protocol) | BACKUP@ab93b36:`docs/research_rebuild/`, `handoff/worktrees/research-*` | 2026-10 |

รายละเอียด 17 ช่องต่อ family: `HISTORICAL_EXPERIMENT_AUDIT.md`

## 5. ขนาดข้อมูลที่ได้จาก repository (แทน ASSUMPTION ของ v1 — K5)

| รายการ | ค่า | แหล่ง |
|---|---|---|
| จำนวนโปรไฟล์ | 36,807 (Twitter 13,960 · Google+ 11,890 · Instagram 10,957) | นับแถวของ [MAIN@1e0a2db:data_for_project/normalized_profiles_with_profile_id.csv content-not-inspected (schema/row-count only)] ตรงกับ CLAUDE.md |
| จำนวน column | 21 (userName, fullName, bio, location, externalUrl, pictureURL, platform, user_folder, bio_urls, bio_url_count, bio_mentions, bio_mentions_count, location_type, location_valid, latitude, longitude, url_count, externalUrl_clean, external_domain, profile_id, profile_row_id) | header เดียวกัน |
| Missingness (สัดส่วนค่าว่าง) | userName 0.23% · fullName 2.32% · bio 18.04% · location 65.24% · externalUrl 16.92% · pictureURL 32.90% · user_folder 0.01% (3 แถว) | นับค่าว่างระดับ column (ไม่พิมพ์ค่า) |
| จำนวน entity (`user_folder`) | 15,297 — 1 บัญชี 1,526 · 2 บัญชี 6,039 · 3 บัญชี 7,728 · 4 บัญชี 4 | สถิติขนาดกลุ่ม (ไม่พิมพ์ค่า) |
| ความสัมพันธ์ 1:1 ต่อแพลตฟอร์ม | entity ที่มี >1 บัญชีบนแพลตฟอร์มเดียว = 4 (0.03%) → **เกือบ 1:1 ทั้งหมด** | เช่นเดียวกัน |
| คู่จริงข้ามแพลตฟอร์ม (documented) | 29,247 | [MAIN@1e0a2db:exp_lib.py#L26 TOTAL_POS_FULL], [MAIN@1e0a2db:EXPERIMENT_PLAN.md#L30] |
| คู่จริงข้ามแพลตฟอร์ม (นับใหม่จากไฟล์ข้างต้น) | 29,243 → **ARTIFACT_INCONSISTENT (ต่าง 4 คู่ = 0.014%)**; สาเหตุ UNKNOWN (อาจเป็นเวอร์ชันไฟล์/การ normalize platform) | การนับตามนิยาม stage8 (`user_folder` เดียวกัน + platform ต่างกัน) |
| คู่ทั้งหมดข้ามแพลตฟอร์ม (all-pairs) | 449,223,850 (คำนวณจากจำนวนต่อแพลตฟอร์ม) | คำนวณจากแถวบน |
| Candidate set ของ full-candidate pipeline (B0) | 2,086,245 คู่ = exact tier 12,403 + scored 2,073,842 | [MAIN@1e0a2db:EXPERIMENT_PLAN.md#L26] (HIST-UNVERIFIED: `match_decisions.parquet` ไม่ถูก commit → RESULT_ARTIFACT_NOT_FOUND) |
| คู่จริงที่ blocking พลาด | 3,316 (PC ของ B0 = 0.8866) | [MAIN@1e0a2db:EXPERIMENT_PLAN.md#L28], [MAIN@1e0a2db:experiments/REPORT_R0_R5.md#L59]; ไฟล์ [MAIN@1e0a2db:analysis_decision_matrix/blocking_missed_pairs.csv] มี 3,316 แถวข้อมูล → **ARTIFACT_CONSISTENT** (นับแถวเท่านั้น) |
| Candidate set ของ notebook pipeline v2 | 873,956 คู่; blocking recall ≈ 91.8% (v1 notebook 56.1%) | saved output ของ [MAIN@1e0a2db:train_data/v2/stage7_blocking_v2.ipynb] (EXECUTION_EVIDENCE_FOUND) และ [MAIN@1e0a2db:data/processed/pipeline_report.json] |
| Prior ใน B0 candidate set | ≈ 29,247 / 2,086,245 ≈ 1.40% | คำนวณจากสองแถวบน |

## 6. Privacy findings (สรุป — รายละเอียดใน `METHODOLOGICAL_RISKS.md` §P และ `review/_work/agentA2/PRIVACY_FINDINGS.csv`)

- **ทั้งสอง repository เป็น PUBLIC** (`gh repo view --json visibility` → `"PUBLIC"` ทั้ง `Project-for-Work` และ `Project-for-Work-private-backup`) แม้ชื่อ repo ที่สองจะบอกว่า private
- MAIN@1e0a2db commit ไฟล์ข้อมูลโปรไฟล์ดิบเป็น blob เต็ม (ไม่มี LFS) — ตัวอย่าง: `data_for_project/*.csv` (5 ไฟล์, 18–24 MB), `pub_multi/data/{train_all,fn_top,fp_top,train_all_sample}.csv` (header มี `userName_a`, `fullName_a`, `user_folder_a`, …), `analysis_decision_matrix/blocking_missed_pairs.csv` (header มี `userName_a`, `bio_a`, `externalUrl_a`, …), `data/processed/*`, `data/final/profiles_with_images.*`, `experiments/*.parquet` (มี pair id) — รวม ≥ 69 ไฟล์ ≈ 471 MB ที่ชื่อ/บทบาทบ่งว่ามีข้อมูลส่วนบุคคลหรือ ID ที่เชื่อมกลับได้
- MAIN@1e0a2db มี path ใต้ `image_process/downloaded_images/` จำนวน **4,248 ไฟล์** (ภาพโปรไฟล์ที่ดาวน์โหลดมา — ข้อมูลชีวมิติที่อาจระบุตัวบุคคลได้; ไม่ได้เปิดดู)
- ผลต่อ gate: **G1 ต้องจัดการเรื่องนี้ก่อน** (การเผยแพร่ข้อมูลส่วนบุคคลต่อสาธารณะเกิดขึ้นแล้ว) — การตัดสินใจแก้ไข (เปลี่ยนเป็น private / ลบประวัติ) เป็นของเจ้าของข้อมูล/ที่ปรึกษา ไม่ได้ทำในรอบนี้

## 7. ข้อจำกัดของ inventory

- ไม่ได้เปิดเนื้อหาไฟล์ข้อมูล (นอกจาก header และสถิติ schema ในตาราง §5)
- LFS objects ไม่ได้ถูก pull; ใช้ `oid sha256` เป็น checksum (content-not-inspected)
- ไม่มีการรัน pipeline/โมเดลใด
