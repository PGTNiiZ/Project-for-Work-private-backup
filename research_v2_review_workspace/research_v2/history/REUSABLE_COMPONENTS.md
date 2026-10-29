# Reusable Components — งานเดิมที่นำกลับมาใช้ได้ (v2, V-REPO)

## Changes vs v1

| # | การเปลี่ยนแปลง | หลักฐาน |
|---|---|---|
| RC1 | ทุกแถวที่ v1 เป็น UNKNOWN ถูกแทนด้วย path + commit จริง และ reuse label ตาม prompt §4 | `review/HISTORICAL_EXPERIMENT_AUDIT.md` |
| RC2 | พบ component ที่ v1 คิดว่า "ต้องสร้างใหม่" แต่มีอยู่แล้ว: entity nested split + overlap assert, sealed-label store, prediction freeze manifest, budget-equalised Sobol baseline, Chow rule, end-to-end metric ที่นับ REVIEW | [MAIN@1e0a2db:exp_lib.py#L145-L221]; [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/real_adapters.py#L102-L135]; [BACKUP@903246c:experiments/code/reviewer_revision.py] |
| RC3 | ระบุ component ที่ **ห้ามใช้**: cache `scored_pairs_enriched.parquet` (name_sim gated + score ของโมเดลที่ split ไม่ทราบ), production model checkpoint, prediction ประวัติศาสตร์ | CONFIRMED_DEFECT ใน `review/METHODOLOGICAL_RISKS.md` |
| RC4 | ค่า cost เริ่มต้นต่างกันระหว่าง repo → ต้องส่งค่า cost อย่างชัดแจ้งทุกครั้ง | [MAIN@1e0a2db:exp_r1_ga_redecision.py#L15] vs [BACKUP@903246c:src/identity_resolution/core/business_cost.py#L14-L18] |

## 1. หลักการนำกลับมาใช้ (คงเดิม)

1. ใช้ซ้ำได้ = โค้ด/ความรู้ ไม่ใช่ผลลัพธ์/โมเดลที่ train แล้ว
2. ทุก component ต้องผ่าน acceptance test (บนข้อมูลสังเคราะห์) ก่อนเข้า pipeline V2
3. Component ที่สัมผัส split/label ต้องถูกตรวจว่าไม่อ่าน test

## 2. ตาราง component

| Component | ที่มา (citation) | ใช้ใน V2 | Reuse decision | Acceptance test ก่อนใช้ |
|---|---|---|---|---|
| Profile loader (LinkSocial JSON → table) | [BACKUP@ab93b36:src/identity_resolution/stages/prepare.py#L28-L69 load_all_profiles] | D0-2 | REUSE_AFTER_VERIFICATION | unit test บนโฟลเดอร์สังเคราะห์; ตรวจว่า user_folder ไม่ถูกแก้ |
| Normalization (NFKC + casefold + whitespace + strip '@') | [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2r1/FEATURE_SCHEMA_V2R1.md#L25] | E1-*, E2-1 | REUSE_AFTER_VERIFICATION | idempotence test |
| B0 exact tier + key blocking | [MAIN@1e0a2db:train_data/stage7_14_full_candidate_pipeline/run_full_candidate_pipeline.py#L118-L179]; [BACKUP@ab93b36:src/identity_resolution/workflows/full_candidate.py#L90-L151] | E1-1 | REUSE_AFTER_VERIFICATION | replay ได้ 2,086,245 คู่ / PC 0.8867 บนข้อมูลเดิม (หลัง G1) |
| 17 hand features | [MAIN@1e0a2db:exp_r2_bert_feature.py#L146-L265 compute_features17]; แก้ name_sim แบบไม่ gate [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/features.py#L12-L19] | E2-1 | REUSE_AFTER_VERIFICATION (เวอร์ชัน v2 เท่านั้น) | ตรวจ name_sim ไม่ขึ้นกับ score; ตัด same_platform (ค่าคงที่) |
| Name-similarity functions (Damerau, char n-gram, token-set, phonetic) | [BACKUP@ab93b36:src/identity_resolution/core/name_similarity.py] | E2-1 | REIMPLEMENT/REUSE_AFTER_VERIFICATION | test เทียบค่าที่คำนวณด้วยมือ |
| MiniLM cosine (all-MiniLM-L6-v2, fullName+bio+location, "[empty]" sentinel) | [MAIN@1e0a2db:exp_r2_bert_feature.py#L78-L137]; revision บันทึกใน [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2r1/provenance/v2r1_manifest.json#minilm] | E4-1, E1-4 | REUSE_AFTER_VERIFICATION + ตรึง revision | ตรวจ sentinel ไม่สร้าง cosine สูงปลอมระหว่างโปรไฟล์ว่าง (ต้องเพิ่ม missing indicator) |
| GA 4 ยีน (decide_code, clip, run_ga) | [MAIN@1e0a2db:exp_r1_ga_redecision.py#L75-L156] | E6-5 | REUSE_AFTER_VERIFICATION (ส่ง cost และ budget ชัดแจ้ง) | seed reproducibility; นับ evaluation จริง |
| Sobol baseline + budget transparency | [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/policies.py#L53-L118]; [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2r1/optimizer_budget_transparency.json] | E6-4 | REUSE_AFTER_VERIFICATION + **scramble** (เดิม unscrambled ไม่มี seed) | budget audit |
| Chow posterior-risk rule | [BACKUP@903246c:experiments/code/reviewer_revision.py] | E6-3 | REUSE_AFTER_VERIFICATION | test ties/argmin |
| End-to-end harness (blocking-missed = FN; exact tier constants) | [MAIN@1e0a2db:exp_lib.py#L107-L140]; [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/final_runner.py#L246-L264] | E7-1, E7-2 | REUSE_AFTER_VERIFICATION + เพิ่ม e2e recall ที่นับ REVIEW | เทียบกับ sklearn บนข้อมูลสังเคราะห์ |
| Entity nested split + overlap assert | [MAIN@1e0a2db:exp_lib.py#L166-L221 build_nested_entity_split] | G3 | REUSE_AFTER_VERIFICATION (ปรับเป็น 5 equal folds) | overlap = 0; prior ต่อ fold รายงาน |
| Sealed-label store + process read guard + prediction freeze | [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/real_adapters.py#L102-L135]; [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2r1/sealed_guard.py] | G3, G5, E7-1 | REUSE_AFTER_VERIFICATION | synthetic tests เดิม (`tests/test_v2r1_integrity.py`) ต้องผ่าน |
| Run manifest / artifact hashes | [MAIN@1e0a2db:experiments/automation/gb_transformer_primary_20260809/artifact_hashes.json]; Gate 7 run_manifest [BACKUP@ab93b36:handoff/worktrees/research-phase15-integration/docs/research_rebuild/phase_01_5/gate_07] | ทุก run | REUSE_AFTER_VERIFICATION | — |
| Leakage feature lists (label proxies) | [MAIN@1e0a2db:train_data/leakage_excluded_features.txt]; [..._strict.txt] | D0-4, G2 | REUSE_AFTER_VERIFICATION (เป็น input ของการตัดสิน) | — |
| Bloom encoder | [MAIN@1e0a2db:exp_r4_bloom_privacy.py#L75-L133] | E8-1 | REIMPLEMENT (keyed HMAC; salt ไม่อยู่ในโค้ด) | attack test E8-3 |
| R6 hash blocker | [MAIN@1e0a2db:exp_r6_bert_er.py] | — | REFERENCE_ONLY | — |
| CRM merge (union-find) / lead score | [MAIN@1e0a2db:train_data/stage15_crm_entity_pipeline/run_crm_entity_pipeline.py#L250-L403] | E10-1 (union-find เท่านั้น) | REFERENCE_ONLY (lead score: EXCLUDE จาก research claim) | — |
| Cluster bootstrap | ประวัติศาสตร์ resample คู่ [BACKUP@ab93b36:experiments/code/analyze_icsec_primary.py#L60-L97] | ทุก Track | REIMPLEMENT (resample entity) [P49] | coverage test บนข้อมูลสังเคราะห์ |
| **Historical caches/predictions/models** (`scored_pairs_enriched.parquet`, `pair_features17.parquet`, `*_probabilities.parquet`, `best_model.pkl`) | [MAIN@1e0a2db:experiments/*] | D0-5 เท่านั้น | **EXCLUDE** จากผล V2 | — |
| ข้อมูลดิบ / label | [MAIN@1e0a2db:data_for_project/normalized_profiles_with_profile_id.csv] (sha256 17a95f75…) | ทุก Track | **BLOCKED** (G0/G1); อ่านผ่าน read-only + hash | — |

## 3. Component ใหม่ที่ยังต้องสร้าง

| Component | ใช้ใน | เหตุผล |
|---|---|---|
| Random search + TPE ที่ budget-matched (ไม่มีในประวัติศาสตร์) | E6-4 | `git grep` ไม่พบ optimizer นอกจาก GA/Sobol (`review/_work/agentA2/BACKUP_METHOD_CHECKS.md` assumption (a)) |
| Entity-level cluster bootstrap + paired Δ + Holm + TOST | ทุก Track | ประวัติศาสตร์ไม่มี CI ใน MAIN; BACKUP ใช้ pair bootstrap |
| Blocking evaluator ที่ budget = |C_B0| + PC–|C| | T1 | H5 |
| Tuned weighted rule (E2-3) | T2 | ไม่มี rule baseline ที่ tune ในประวัติศาสตร์ |
| Label-sensitivity evaluator (S1/S2/S3) | E7-6 | — |
| Privacy attack harness | E8-3 | R4/R5 ไม่มี attack |
