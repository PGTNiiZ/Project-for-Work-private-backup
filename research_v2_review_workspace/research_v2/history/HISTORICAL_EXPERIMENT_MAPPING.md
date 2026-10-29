# Historical Experiment Mapping — งานเดิม → Research V2 (v2, V-REPO)

## Changes vs v1

| # | การเปลี่ยนแปลง | หลักฐาน |
|---|---|---|
| H1 | ทุกแถวเปลี่ยนจาก HIST-UNVERIFIED (สรุปของผู้ใช้) → lifecycle labels พร้อม citation จาก repository | `review/HISTORICAL_EXPERIMENT_AUDIT.md` |
| H2 | **"R0–R3 = factorial 2×2" ถูกล้ม (OVERTURNED)**: R0/R1 ใช้ score ของ production multimodal model (41 features) ส่วน R2/R3 ใช้ IdentityMLP ใหม่บน 17 hand features + bert_cos | [MAIN@1e0a2db:train_data/stage7_14_full_candidate_pipeline/run_full_candidate_pipeline.py#L22]; [MAIN@1e0a2db:exp_r2_bert_feature.py#L53-L61] |
| H3 | **"GA เทียบเฉพาะ manual threshold" — CONFIRMED สำหรับ R-series/ICSEC v1, OVERTURNED สำหรับ ICSEC v2** (มี Sobol budget เท่ากัน 12,000 calls) | [MAIN@1e0a2db:exp_r1_ga_redecision.py#L176-L190]; [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/BASELINE_PROTOCOL.md#L5-L12] |
| H4 | **"F1 0.8373 เป็น candidate-level และไม่รู้ split" — OVERTURNED**: end-to-end เทียบ candidate generation B0 บน test md5 30% (GA tune บน val 70%) | [MAIN@1e0a2db:exp_lib.py#L36-L38, #L107-L140] |
| H5 | **"R6 กู้คืนได้จำกัด" — CONFIRMED** (4/3,316 ที่ radius 1; ARTIFACT_CONSISTENT) | [MAIN@1e0a2db:experiments/r6_blocking_recovery.json] |
| H6 | **"GT อาจสร้างจาก blocking/URL" — PARTIALLY RESOLVED**: GT มาจาก folder ของ LinkSocial ไม่ใช่ blocking ของระบบ; การที่ LinkSocial ใช้ cross-link/URL หรือไม่ยัง UNKNOWN | [BACKUP@ab93b36:src/identity_resolution/stages/prepare.py#L28-L69]; [P38] |
| H7 | เพิ่ม families ที่ v1 ไม่รู้จัก: ICSEC v1/v2/v2r1, reviewer revision, feature-aware GA, name-similarity ablation, Phase 1/1.5 gates, notebook pipeline, leak-safe multimodal suite | `review/REPOSITORY_RESEARCH_INVENTORY.md` §4 |
| H8 | ICSEC: BLOCKED → V-REPO (ตัวเลข paper = aggregate artifacts) | [BACKUP@ab93b36:paper/reviewer_revision/NUMERIC_CLAIM_AUDIT.json] |

---

## 1. โครงสร้างการทดลองเดิมตามที่พบจริง

| ID เดิม | Score/representation ที่ใช้จริง | Decision | Split (optimize → report) | Level | ผลที่บันทึก (test) | Lifecycle |
|---|---|---|---|---|---|---|
| R0 | production multimodal model `image_context_r075_h20_s42` (41 features; train split 70/15/15 ของตัวเอง) | 0.98/0.95 | — → md5 test 30% | end-to-end เทียบ B0 | F1 0.7964 [MAIN@1e0a2db:experiments/r1_results.json] | CODE · EXEC · RESULT · CONSISTENT |
| R1 | เหมือน R0 + name_sim | GA 4 ยีน | val 70% → test 30% | e2e | F1 0.8292; nested 0.8563 (cost test +1.09% vs R0) | CODE · EXEC · RESULT · CONSISTENT |
| (manual stage18) | เหมือน R0 | rule [0.98,0.95,0.90,0.70] | — → test | e2e | F1 0.8439 (cost 4,998.5) — ไม่แสดงใน REPORT | RESULT_ARTIFACT_FOUND |
| R2 | IdentityMLP ใหม่ (17 hand features + MiniLM cosine) train บน 85% ของคู่ใน val | 0.98/0.95 | — → test | e2e | F1 0.7393 | CODE · EXEC · RESULT · CONSISTENT |
| R3 | เหมือน R2 | GA | val (รวมคู่ที่ใช้ train MLP) → test | e2e | F1 0.8373; nested 0.8615–0.8642 | CODE · EXEC · RESULT · CONSISTENT |
| R4 | MLP บน Bloom-Dice (ชื่อ) + feature plaintext อื่น | 0.98/0.95 | — → test | e2e | F1 0.7244–0.7397 | CODE · EXEC · RESULT · CONSISTENT |
| R5 | เหมือน R4 | GA | val → test | e2e | F1 0.8308–0.8329 | CODE · EXEC · RESULT · CONSISTENT |
| R6 | frozen DistilBERT + hash/match heads | 0.98/0.95, GA | val → test | e2e + blocking recovery | F1 0.6053 / 0.7801; recovery 4/3,316 | CODE · EXEC · RESULT · CONSISTENT |
| GB-17/18/18-GA (MAIN) | GB บน 17 / 18 features | 0.98/0.95, GA | nested (model_train/cal/ga_val) → test | e2e | F1 0.5967 / 0.8296 / 0.8612 | CODE · EXEC · RESULT · CONSISTENT (primary = repro) |
| ICSEC v1 | GB-17/18/18-GA, 3 outer splits | fixed / GA | entity nested v1 → test | e2e | GB-18-GA F1 0.8604 ± 0.0012 | CODE · EXEC · RESULT; IEEE draft ARTIFACT_INCONSISTENT |
| ICSEC v2/v2r1 | GB-17/18 (name_sim แก้แล้ว), 3 outer splits | B0 fixed, B1 2-thr Sobol, B2 4-param Sobol, B3 GA (12,000 calls) | entity_nested_v2 → sealed test | e2e (decision recall ไม่นับ REVIEW) | F1 0.8510 / 0.8910 / 0.8901 / 0.8903; U 2364.2 / 1864.6 / 1860.0 / 1858.2 | CODE · EXEC · RESULT · CONSISTENT (paper = artifacts) |
| Reviewer revision | v2r1 frozen | + Chow closed-form | ไม่มีการ refit | e2e (นับ REVIEW) | e2e F1 B3 0.8610; Chow U 1879.0 | CODE · EXEC · RESULT · CONSISTENT |

ที่มาของตัวเลข: `review/HISTORICAL_EXPERIMENT_AUDIT.md` (F08–F17) — ทั้งหมดเป็น **HIST** (ไม่ได้ replicate)

## 2. Table 1 — Historical-to-V2 Experiment Mapping

| Historical Experiment | Existing Evidence (lifecycle + citations) | V2 Experiment | Scientific Purpose | Differences | Reuse Decision | Training Needed | Blocking Issue | Confidence |
|---|---|---|---|---|---|---|---|---|
| F01 Original lexical | CODE_FOUND [MAIN@64d3b0b:match_profile.py] | E2-1, E2-3 | lexical signal / rule baseline | ไม่มี split; rule ไม่ tune | REFERENCE_ONLY | ไม่ | — | HIGH (ไม่มีผลให้ใช้) |
| F02 Bigram retrieval + ranking | CODE · EXEC · RESULT [MAIN@1e0a2db:data/processed/bigram_pipeline_results/bigram_pipeline_metrics_summary.csv] | E1-3 (แนวคิด), E5-4 (location) | sparse candidate gen | GT คนละแหล่ง (pair files) | REFERENCE_ONLY | ไม่ | — | MEDIUM |
| F03 SBERT/MPNet bio | CODE · EXEC (saved outputs) | E4-1 (ตัวเลือก encoder) | semantic of bio | ไม่มี metric ที่ตรวจได้ | REFERENCE_ONLY | ไม่ (frozen) | — | MEDIUM |
| F04 Image / multimodal | CODE · EXEC · RESULT (ผ่าน F06) | E9-1 | image signal | coverage Twitter เท่านั้น | BLOCKED | ใช่ (classifier) | GX-T9, G1 (ภาพ 4,248 ไฟล์ใน repo PUBLIC) | HIGH |
| F05 Notebook pipeline (IdentityMLP) | CODE · EXEC · RESULT; AUC ARTIFACT_CONSISTENT (LOW) | — | — | คู่ sample, split ด้านเดียว, TF-IDF transductive | REFERENCE_ONLY | — | — | MEDIUM |
| F06 Leak-safe multimodal suite (= R0 score model) | CODE · EXEC · RESULT; strict operating point เลือกจาก test (CONFIRMED_DEFECT รายงาน) | E3-2 (ภาพรวม learner), E2-1 (feature 41 ตัวเป็นแหล่ง) | learner/feature | คู่ sample ไม่ใช่ candidate set | REFERENCE_ONLY (ผล); REUSE_AFTER_VERIFICATION (leakage lists, assign_splits idea) | ใช่ (retrain) | — | HIGH |
| F07 B0 full-candidate + CRM | CODE · EXEC; `match_decisions.parquet` RESULT_ARTIFACT_NOT_FOUND; blocking_missed 3,316 CONSISTENT | **E1-1**, E7-2 (B0 factor), E10-1 (union-find) | historical blocker baseline | — | REUSE_AFTER_VERIFICATION | ไม่ | — | HIGH |
| R0 | ดูตาราง §1 | **E6-1** (R0 rule บน matcher V2), E7-2 (fixed policy factor) | historical policy bridge | score model V2 ต่างจากเดิม | REPLICATE (policy) / EXCLUDE (score) | ไม่ | — | HIGH |
| R1 | ดูตาราง §1 | **E6-5** (GA 4 ยีน) vs E6-2/E6-3/E6-4 | H4b | V2 มี non-GA budget-matched + CI | REPLICATE | ไม่ (policy search) | G0/G1 | HIGH |
| manual stage18 | RESULT_ARTIFACT_FOUND | E6-1 | historical rule | — | REPLICATE | ไม่ | — | HIGH |
| R2 | ดูตาราง §1 | **E5-3 vs E5-1** (+E4-1) | H3 | V2 threshold-free PR-AUC; learner เดิมทั้งสองฝั่ง | REIMPLEMENT (feature code ใช้ซ้ำหลังตรวจ) | ใช่ | name_sim gated (แก้) | HIGH |
| R3 | ดูตาราง §1 | แยกเป็น E5-3 (S2) + E6-5 (S4) + interaction ใน E7-2 | H3 × H4 | ห้ามอ้าง "best" | REPLICATE (แยกองค์ประกอบ) | ใช่ | — | HIGH |
| R4 | ดูตาราง §1 | E8-1 | privacy–utility | keyed HMAC, threat model | REIMPLEMENT | ใช่ | GX-T8 | HIGH |
| R5 | ดูตาราง §1 | E8-2 + **E8-3 attack (บังคับ)** | privacy claim | ประวัติศาสตร์ไม่มี attack | REIMPLEMENT | ไม่ (policy) | GX-T8 | HIGH |
| R6 | ดูตาราง §1; แผน GPU PROPOSED_NEVER_EXECUTED | **E1-4, E1-5** (dense/hybrid ที่คุม budget); E4-3 (fine-tune, CONDITIONAL) | H5 | V2 ใช้ kNN top-k แทน hash bucket | REFERENCE_ONLY | E1-4 ไม่; E4-3 ใช่ (GPU) | — | HIGH |
| F12 Nested automation | CODE · EXEC · RESULT · CONSISTENT | โครง split ของ V2 (§11 master plan), D0-5 | protocol | V2 ใช้ 5 equal folds | REUSE_AFTER_VERIFICATION (build_nested_entity_split, overlap assert) | — | — | HIGH |
| F13 GB-17/18/18-GA | CODE · EXEC · RESULT · CONSISTENT | E3-2, E5-3, E6-5 | isolated effects | V2 tune hyperparameter + PR-AUC | REUSE_AFTER_VERIFICATION (code) / REPLICATE (result) | ใช่ | — | HIGH |
| F14 Feature-aware GA | CODE · EXEC · RESULT; source = v1 cache (EXCLUDE) | E5-4 (ความสำคัญของกลุ่ม), E6-5 (policy class) | feature-aware policy | function class/budget ไม่เท่ากัน | REFERENCE_ONLY | — | score lineage ไม่ทราบ | MEDIUM |
| F15 Name-sim ablation N0–N6 | CODE · EXEC · RESULT (validation only); N7 PROPOSED_NEVER_EXECUTED | E2-1 (name features), E5-4 | H1 | คู่ balanced, validation in-sample | REFERENCE_ONLY (ผล) / REIMPLEMENT (name_similarity functions) | — | — | MEDIUM |
| F16 ICSEC v1 | CODE · EXEC · RESULT; IEEE draft ARTIFACT_INCONSISTENT | — | — | name_sim gated; label read ก่อน fit (CONFIRMED_DEFECT) | EXCLUDE (ผล) | — | — | HIGH |
| F16 ICSEC v2/v2r1 | CODE · EXEC · RESULT · CONSISTENT | **E6-2/E6-4/E6-5** (replication), sealed-label harness | H4b | V2: 10 seeds, cluster bootstrap, random/TPE เพิ่ม, แก้ calibration prior | REPLICATE (ผล) / REUSE_AFTER_VERIFICATION (harness) | ใช่ (GB retrain) | G0/G1; test ถูกใช้ซ้ำ | HIGH |
| F17 Reviewer revision (Chow, e2e metrics) | CODE · EXEC · RESULT · CONSISTENT | **E6-3** (Chow), metric definition ใน EVALUATION §ES1 | H4a | Chow เพิ่มหลังเห็นผล test (post-hoc) | REUSE_AFTER_VERIFICATION | ไม่ | — | HIGH |
| F18 Phase 1 / 1.5 gates | CODE · EXEC (synthetic tests); Gate 9 PROPOSED_NEVER_EXECUTED | G0–G5, RESEARCH_GATES | governance/protocol | V2 gates map กับ Gate 1–9 | REUSE_AFTER_VERIFICATION | — | Gate 1/2/3/8 human records | HIGH |

## 3. การใช้ผลประวัติศาสตร์อย่างถูกต้องในเล่ม V2

| ทำได้ | ห้ามทำ |
|---|---|
| ใช้เป็นแรงจูงใจของสมมติฐาน ("ICSEC v2 พบ GA ≈ Sobol จึงทดสอบซ้ำแบบควบคุม") | อ้าง F1 0.8373 หรือ U 1858.2 เป็นผลของ V2 |
| ภาคผนวก historical table พร้อม lifecycle label และข้อจำกัด (A1–A8) | เทียบตรงกับผล V2 ในตารางเดียวโดยไม่มีคำเตือน |
| ใช้ค่าตั้งต้น (MiniLM-L6-v2, GB 300/0.05/6, genome 4 ยีน, cost 2:1:0.1) เป็น prior ที่ประกาศใน G4 | ใช้ผลเดิมเลือก configuration หลังเห็นผล V2 |
| Replicate R1/R3/ICSEC-B3 (E6-5) แล้วรายงานว่า replicate หรือไม่ | สรุปว่า R3 หรือโมเดลใด "universally best" (artifact เองแสดงว่า manual stage18 มี F1 สูงกว่า R3) |

## 4. Checklist ผู้ตรวจ (สถานะหลังรอบนี้)

| Run | Repo path | Commit | Split ที่ optimize | Split ที่รายงาน | Level | ผลที่ตรวจได้ | สถานะใหม่ |
|---|---|---|---|---|---|---|---|
| R0 | `exp_r1_ga_redecision.py` (R0_production) | MAIN@1e0a2db | — (โมเดลเดิม train 70/15/15 ของ F06) | md5 test 30% | e2e vs B0 | F1 0.7964 | ARTIFACT_CONSISTENT |
| R1 | `exp_r1_ga_redecision.py`, `run_ga_experiments.py` | MAIN@1e0a2db | md5 val 70% / nested ga_validation | test 30% | e2e | 0.8292 / 0.8563 | ARTIFACT_CONSISTENT |
| R2 | `exp_r2_bert_feature.py` | MAIN@1e0a2db | MLP: 85% คู่ใน val | test 30% | e2e | 0.7393 | ARTIFACT_CONSISTENT |
| R3 | `exp_r2_bert_feature.py#L613-L625` | MAIN@1e0a2db | val ทั้งหมด (รวมคู่ train MLP) / nested | test 30% | e2e | 0.8373 / 0.8615 | ARTIFACT_CONSISTENT |
| R4 | `exp_r4_bloom_privacy.py` | MAIN@1e0a2db | — | test 30% | e2e | 0.7244–0.7397 | ARTIFACT_CONSISTENT |
| R5 | `exp_r4_bloom_privacy.py#L253-L263` | MAIN@1e0a2db | val | test 30% | e2e | 0.8308–0.8329 | ARTIFACT_CONSISTENT |
| R6 | `exp_r6_bert_er.py` | MAIN@1e0a2db | val | test 30% + held-out 3,316 | e2e + recovery | 0.6053 / 0.7801; 4/3,316 | ARTIFACT_CONSISTENT |

- seeds: legacy 1 (42); automation GA 5 seeds; model seeds 42/7/123 — ไม่มี CI ในทุก run ของ MAIN
- ข้อมูลส่วนบุคคลถูก commit ลง repo สาธารณะ → แจ้ง G1 (ดู `review/METHODOLOGICAL_RISKS.md` §P)
- ความต่าง MAIN vs BACKUP: ส่วนใหญ่ import/path; ค่า cost เริ่มต้นเปลี่ยน 5/1/0.02 → 2/1/0.1 (`review/REPOSITORY_COMPARISON.md`)
