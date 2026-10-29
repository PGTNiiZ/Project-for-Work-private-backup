# Historical Experiment Audit — ตระกูลการทดลองเดิมทั้งหมด (17 ช่องต่อ family)

วันที่: 2026-10-25 · สถานะ: **V-REPO (อ่านโค้ด/เอกสาร/artifact เท่านั้น — ไม่มีการรันซ้ำ)** · การทดลองทางวิทยาศาสตร์: **NO-GO**

ป้าย lifecycle ที่ใช้ (รายงานแยกอิสระ): `CODE_FOUND` · `EXECUTION_EVIDENCE_FOUND` · `RESULT_ARTIFACT_FOUND` · `ARTIFACT_CONSISTENT`/`ARTIFACT_INCONSISTENT` · `PROPOSED_NEVER_EXECUTED` · `UNKNOWN` (ไม่มี family ใดได้ `INDEPENDENTLY_VERIFIED` ในรอบนี้)

หลักการอ่าน: *พบโค้ด ≠ ได้รัน* · *พบตัวเลข ≠ การประเมินถูกต้อง* · ตัวเลขผลประวัติศาสตร์ทุกตัวในเอกสารนี้ยังเป็น **HIST** (ใช้ได้เป็นแรงจูงใจของสมมติฐานเท่านั้น)

ตัวย่อ: MAIN = `PGTNiiZ/Project-for-Work`; BACKUP = `PGTNiiZ/Project-for-Work-private-backup`; commit 7 ตัวตาม `REPOSITORY_RESEARCH_INVENTORY.md`

---

## A. ข้อค้นพบหลักที่เปลี่ยนความเข้าใจจาก v1 (สรุปก่อนรายละเอียด)

| # | v1 (HIST-UNVERIFIED) | หลักฐาน repository | ผล |
|---|---|---|---|
| A1 | R0–R3 เป็น factorial 2×2 (17/18 features × threshold/GA) | R0/R1 ใช้ score จาก "production" multimodal model `image_context_r075_h20_s42` (41 features; TF-IDF+SBERT+attribute+image; train บน split 70/15/15 ของตัวเอง) [MAIN@1e0a2db:train_data/stage7_14_full_candidate_pipeline/run_full_candidate_pipeline.py#L22 BEST_RUN_PATH], [MAIN@1e0a2db:pub_multi/doc/model_compare.md#Summary]; ส่วน R2/R3 train IdentityMLP ใหม่บน 17 hand features ที่คำนวณใหม่ + `bert_cos` บน split `val` ของ harness [MAIN@1e0a2db:exp_r2_bert_feature.py#L53-L61 FEATURE17_COLS], [#L511-L560 build_r2_probabilities] | **OVERTURNED** — โครงสร้างเป็น 2×2 ในชื่อ แต่แกน representation ปน (model family, training data, feature implementation และ +semantic เปลี่ยนพร้อมกัน); "17 features" ของ R0 ไม่ใช่ชุดเดียวกับ R2 |
| A2 | GA เทียบกับ manual threshold เท่านั้น | MAIN: baseline มีเพียง R0 production rule (0.98/0.95) และ manual stage18 rule [MAIN@1e0a2db:exp_r1_ga_redecision.py#L176-L190 main]; ทุก automation run ใช้ baseline เดิม [MAIN@1e0a2db:run_ga_experiments.py#L75-L128 _r1_baseline/_r2_baseline/make_r1_data/make_r3_data]; ไม่พบ random/TPE/grid ที่ budget เท่ากันใน MAIN | **CONFIRMED สำหรับ MAIN**; BACKUP ดูส่วน C (Agent A2) |
| A3 | F1 0.8373 ของ R3 เป็น candidate-level และไม่ทราบ split | harness นับ FN จาก blocking-missed และ TP/FP ของ exact tier ต่อ split [MAIN@1e0a2db:exp_lib.py#L107-L140 split_constants/evaluate]; split = md5(user_folder)%100<30 → test 30%, ที่เหลือ val 70% [#L36-L38 bucket]; GA optimize บน val เท่านั้น [MAIN@1e0a2db:exp_r1_ga_redecision.py#L168-L174] | **OVERTURNED** — F1 0.8373 เป็น *end-to-end เทียบกับ candidate generation B0* (recall ตัวหาร = คู่จริงทั้งหมดใน split รวมที่ blocking พลาด; REVIEW ไม่นับเป็น TP) บน test 30% ที่ entity-disjoint; แต่ยังมี STATIC_RISK: MLP ของ R2 ถูก train บน 85% ของคู่ใน val แล้ว GA ถูก tune บน val ทั้งชุด (รวมคู่ที่ใช้ train) |
| A4 | R6 กู้คู่ที่ blocking พลาดได้จำกัด | 0/3,316 ที่ radius 0; 4/3,316 (0.12%) ที่ radius 1; end-to-end MATCH 3 คู่ [MAIN@1e0a2db:experiments/r6_blocking_recovery.json] = [MAIN@1e0a2db:experiments/REPORT_R0_R5.md#L85-L88] | **CONFIRMED** (ARTIFACT_CONSISTENT) — แต่ R6 ใช้ frozen DistilBERT + hash 64 บิต ไม่คุม budget; ไม่ใช่การทดสอบ dense retrieval แบบ top-k |
| A5 | Ground truth อาจสร้างจาก blocking/URL (selection bias/label proxy) | GT = `user_folder` / `profile_id` (กลุ่มบัญชีต่อคน) [MAIN@1e0a2db:train_data/stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py#L167-L186 build_ground_truth_pairs]; มี gitlink ไปยัง dataset ภายนอก `data/data/Dataset-LinkSocial` (submodule commit `fe67dd1`, ไม่มี `.gitmodules`) [MAIN@1e0a2db:data/data/Dataset-LinkSocial]; blocking keys ไม่ได้ใช้ label [run_full_candidate_pipeline.py#L35]; แต่ exact tier ใช้ username/URL ตรงกันเป็น auto-MATCH [#L118-L150]; ทีมเดิมมีรายการ feature ที่ "behave like near-direct label proxies" [MAIN@1e0a2db:train_data/leakage_excluded_features.txt#L1-L7] | **PARTIALLY RESOLVED** — GT ไม่ได้มาจาก blocking ของระบบ (จึงไม่มี selection bias เชิงโครงสร้างต่อ PC ของ B0) แต่ *วิธีสร้าง GT ของ dataset ต้นทาง* (LinkSocial) ยัง UNKNOWN → label-proxy risk ของ URL/username ยังเปิดอยู่ (G0) |
| A6 | (ใหม่) test ถูกใช้ซ้ำ | test split md5<30 เดียวกันถูกใช้โดย R0–R6, nested R1/R3 (5 seeds × หลาย run), sensitivity 2 run, GB 2 run [MAIN@1e0a2db:experiments/automation/*/summary.md] — ≥ 15 การประเมินบน test ชุดเดียว | DESIGN_LIMITATION → G5 fresh-holdout ทำไม่ได้ด้วยข้อมูลเดิม |
| A7 | (ใหม่) "R3 ดีที่สุด" | ใน artifact เดียวกัน manual stage18 rule ได้ test F1 = 0.8439 > R3 0.8373 > R1 0.8292 แต่ cost สูงกว่า (4,998.5 vs 2,062.3) [MAIN@1e0a2db:experiments/r1_results.json#rules.test.manual_stage18]; แถวนี้ไม่ถูกแสดงในตาราง REPORT [MAIN@1e0a2db:experiments/REPORT_R0_R5.md#L11-L24] | ข้ออ้าง "R3 F1 สูงสุดในทุก experiment" [REPORT#L122] **ไม่ถูกต้องตาม artifact** (ถูกเฉพาะเมื่อจำกัดชุดที่แสดง) → ห้ามอ้าง R3 universally best |
| A9 | (ใหม่) `name_sim` ใน cache เป็นศูนย์เมื่อ score ของโมเดลเดิม < 0.5 | [MAIN@1e0a2db:exp_lib.py#L93-L101 build_cache]; feature นี้อยู่ใน 17 features ของ R2/R3/R4/R5/GB [MAIN@1e0a2db:exp_r2_bert_feature.py#L56]; BACKUP ระบุเป็น hidden learned dependency และแก้ใน v2 [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/REPAIR_PROTOCOL.md#L6-L10] | CONFIRMED_DEFECT → ผล R2–R5, GB-17/18 (MAIN) และ ICSEC v1 มี feature ที่ขึ้นกับ scorer ที่ split ไม่ทราบ |
| A8 | (ใหม่) GA ไม่ลด cost บน test เสมอ | nested R1: GA test F1 0.8563 แต่ test cost สูงกว่า baseline R0 +1.09% ในทุก 5 seeds [MAIN@1e0a2db:experiments/automation/r1_nested_primary_20260809/summary.md#สรุป] | หลักฐานว่า objective ที่ optimize บน validation ไม่ transfer ไป test เสมอ → สนับสนุนความจำเป็นของ H4b |

---

## B. Families ใน MAIN

### F01 — Original lexical matching (ม.ค.–ก.พ. 2026)

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | จับคู่โปรไฟล์ข้ามแพลตฟอร์มด้วยความคล้ายของชื่อ/username + image embedding |
| 2 Hypothesis เดิม | UNKNOWN (ไม่มีเอกสารสมมติฐาน) |
| 3 Code | [MAIN@64d3b0b:match_profile.py], [MAIN@64d3b0b:enhanced_matching.py], [MAIN@64d3b0b:evaluate_matching.py#L93-L107] |
| 4 Config | threshold sweep {0.5, 0.6, 0.7, 0.8, 0.85, 0.9} [evaluate_matching.py#L94] |
| 5 Dataset+checksum | `profiles_with_embeddings.csv` ด้วย absolute path ของเครื่องอื่น [match_profile.py#L19]; ground truth คู่ Instagram–Google+ [evaluate_matching.py#L10] — checksum UNKNOWN (ไฟล์ไม่อยู่ใน commit นี้) |
| 6 Preprocessing | lowercase/strip ใน `enhanced_matching` (UNKNOWN รายละเอียด) |
| 7 Blocking | UNKNOWN |
| 8 Features | difflib `SequenceMatcher`, embedding cosine ของภาพ [match_profile.py#L1-L40] |
| 9 Model | rule (weighted similarity + threshold) |
| 10 Training | ไม่มี |
| 11 Validation/test | threshold sweep บนชุดเดียวกับที่รายงาน (ไม่มี split) |
| 12 Seeds | – |
| 13 Metrics | accuracy/precision/recall/F1 ต่อ threshold |
| 14 Artifacts | ไม่พบ |
| 15 Limitations | ไม่มี split; ใช้ accuracy; path ผูกเครื่อง |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE: UNKNOWN · RESULT_ARTIFACT: UNKNOWN |
| 17 Reuse V2 | **REFERENCE_ONLY** |

### F02 — Bigram username/fullname retrieval + ranking (+location)

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | หา candidate top-k ต่อโปรไฟล์ต้นทางด้วย bigram index แล้วจัดอันดับด้วย classifier ต่อคู่แพลตฟอร์ม |
| 2 Hypothesis เดิม | location ช่วยเพิ่ม top-1 accuracy (จากชื่อผล "with_location") |
| 3 Code | [MAIN@1e0a2db:bigram_username_and_fullname/bigram_full_pipeline.py#L287-L327 top_k_candidates_by_ub], [#L376-L411 build_balanced_train_set], [#L552 train_test_split] |
| 4 Config | top_k (argument), location confidence gate [#L328-L375] |
| 5 Dataset | ground truth แยกไฟล์ต่อคู่แพลตฟอร์ม `data/processed/pairs_{instagram_googleplus,twitter_googleplus,twitter_instagram}.csv` [#L28-L31 DEFAULT_PAIR_FILES] — **แหล่ง GT ต่างจาก `user_folder` ของงานหลัง**; sha256 ดู `repository_inventory.csv` (content-not-inspected) |
| 6 Preprocessing | `norm_text`, `normalize_location` [#L44-L69] |
| 7 Blocking | bigram inverted index + upper-bound top-k (เป็น sparse retrieval แบบหนึ่ง) |
| 8 Features | bigram Jaccard username/fullname + location (haversine) [#L267-L286] |
| 9 Model | SGD (linear), RandomForest |
| 10 Training | balanced train set จาก top-k ของ source ใน train |
| 11 Validation/test | `train_test_split` บน source rows (ต่อไฟล์คู่แพลตฟอร์ม) — ใกล้เคียง entity split เฉพาะภายในคู่แพลตฟอร์มนั้น; ไม่มี validation แยก |
| 12 Seeds | UNKNOWN (ค่า default) |
| 13 Metrics | top1_accuracy, candidate_recall_topk |
| 14 Artifacts | [MAIN@1e0a2db:data/processed/bigram_pipeline_results/bigram_pipeline_metrics_summary.csv]: top-1 0.8195–0.9195, candidate recall@k 0.9331–0.9593, test_size 3,094 ต่อคู่; [.../bigram_pipeline_results_with_location/bigram_vs_location_comparison.csv]: Δtop-1 จาก location 0.000–+0.0071, Δcandidate recall 0 ถึง −0.0087 |
| 15 Limitations | GT ต่างชุด; ไม่มี CI; candidate-level ต่อคู่แพลตฟอร์ม |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND (prediction CSVs) · RESULT_ARTIFACT_FOUND · ARTIFACT_CONSISTENT: UNKNOWN (ไม่มีรายงานให้เทียบ) |
| 17 Reuse V2 | **REFERENCE_ONLY** (แนวคิด bigram index → REIMPLEMENT เป็นส่วนหนึ่งของ E1-3 char n-gram retrieval) |

### F03 — SBERT/MPNet bio-vector matching

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | จับคู่ด้วย embedding ของ bio |
| 2 Hypothesis | semantic ของ bio ช่วยจับคู่ (UNKNOWN อย่างเป็นทางการ) |
| 3 Code | [MAIN@1e0a2db:bio_vector/sbert_mpnet_matching.ipynb], [MAIN@1e0a2db:bio_vector/vector_embredding.ipynb] |
| 4 Config | `all-mpnet-base-v2` (ภายหลังใช้ใน F06 [MAIN@1e0a2db:train_data/stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py#L45 SBERT_MODEL_NAME]) |
| 5 Dataset | UNKNOWN (notebook) |
| 6–12 | UNKNOWN / ไม่มีโปรโตคอลแยก split ที่ระบุได้จากโค้ด |
| 13 Metrics | ไม่พบบรรทัด metric ใน saved output |
| 14 Artifacts | saved outputs 9/26 code cells (sbert_mpnet), 19/19 (vector_embredding) |
| 15 Limitations | ไม่มี split/metric ที่ตรวจได้ |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND (saved outputs) · RESULT_ARTIFACT: UNKNOWN |
| 17 Reuse V2 | **REFERENCE_ONLY** (ตัวเลือก encoder สำหรับ E4-1) |

### F04 — Image features / multimodal (pHash, dHash, face stats, caption, ArcFace)

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | เพิ่มสัญญาณจากภาพโปรไฟล์ |
| 2 Hypothesis | image ช่วยเพิ่มคุณภาพจับคู่ |
| 3 Code | [MAIN@1e0a2db:train_data/stage7_13_multimodal_suite/run_multimodal_suite.py#L74-L98 compute_local_image_descriptor], [#L222-L290 make_multimodal_wrappers]; [MAIN@1e0a2db:image_process/*]; BACKUP:`src/identity_resolution/imaging/*` |
| 4 Config | run `image_context_r075_h20_s42` (ชื่อ run บ่ง ratio/hard-negative/seed) |
| 5 Dataset | `image_process/downloaded_images/` (4,248 path ใน commit — PRIVACY_FINDING), `data/final/image_features_complete.csv` |
| 6 Preprocessing | perceptual hash, brightness/contrast/entropy, caption → SBERT |
| 7 Blocking | ไม่ใช้ |
| 8 Features | image_phash_sim, image_dhash_sim, diff ของสถิติภาพ, face count/area, caption cross features |
| 9 Model | ตาม F06 (LR/GB/RF) |
| 10–11 | ตาม F06 (split 70/15/15) |
| 12 Seeds | 42 (ชื่อ run) |
| 13 Metrics | AP/AUC/F1 บนคู่ที่ sample |
| 14 Artifacts | coverage: "Local image coverage is partial and currently maps to Twitter profiles only" [MAIN@1e0a2db:train_data/stage7_13_multimodal_suite/README.md#Notes] |
| 15 Limitations | coverage จำกัด (Twitter เท่านั้น) → เงื่อนไข coverage ≥ 50% ของ T9 ไม่น่าผ่าน; ข้อมูลชีวมิติ |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND (run directory ถูกอ้าง) · RESULT_ARTIFACT_FOUND (ผ่าน model_compare) |
| 17 Reuse V2 | **BLOCKED** (GX-T9 สิทธิ์ภาพ/biometric) |

### F05 — Notebook pipeline v1/v2 (stage 7–17, IdentityMLP)

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | pipeline ครบ blocking → labeling → features → MLP → calibration → merge → lead score |
| 2 Hypothesis | UNKNOWN (เชิงวิศวกรรม) |
| 3 Code | [MAIN@1e0a2db:train_data/v2/stage7_blocking_v2.ipynb … stage15_16_17_merge_scoring_export_v2.ipynb], [MAIN@1e0a2db:train_data/stage10_13_training_pipeline.py] |
| 4 Config | IdentityMLP hidden [256,128,64], FocalLoss(α=0.25, γ=2), Adam, cosine LR, isotonic, train-neg-ratio 3.0 (สถาปัตยกรรมเดียวกับที่ R2 คัดลอก [MAIN@1e0a2db:exp_r2_bert_feature.py#L1-L13]) |
| 5 Dataset | `merged_profiles.csv` / `normalized_profiles*.csv` (sha256 ใน inventory; content-not-inspected) |
| 6 Preprocessing | stage6 v2 normalization |
| 7 Blocking | key blocking v2 → 873,956 candidates, "Blocking recall ~91.8% (v1: 56.1%)" [saved output MAIN@1e0a2db:train_data/v2/stage7_blocking_v2.ipynb#STAGE 7 v2 SUMMARY] |
| 8 Features | 17 string-similarity + `bio_tfidf_cosine`; TF-IDF `fit_transform(all_bios)` ของ *ทุก* โปรไฟล์ [MAIN@1e0a2db:train_data/v2/stage9_features_v2.ipynb#cell Step 9.2 (raw JSON L299-L300)] |
| 9 Model | IdentityMLP |
| 10 Training | positive = `user_folder` เดียวกัน + platform ต่างกัน; negative = random + hard จาก blocking candidates [stage8_labeling_v2.ipynb#8.1 (raw L148-L184), hard negatives (raw L329-L363)]; undersample negative ใน train |
| 11 Validation/test | entity split โดยใช้ `entity_id_a` เท่านั้น [stage10_dataset_v2.ipynb#10.1 (raw L158-L173)] → negative ที่ฝั่ง b อยู่ split อื่นยังเข้าได้ (STATIC_RISK) |
| 12 Seeds | RANDOM_SEED เดียว |
| 13 Metrics | test ROC-AUC 0.9702, AP 0.9414, best val F1 0.9172, threshold 0.38 [saved output stage12_13_calibration_evaluation_v2.ipynb]; CLAUDE.md ระบุ F1 0.915/AUC 0.970/P 0.959/R 0.874 |
| 14 Artifacts | `data/processed/{model.pt,calibrator.pkl,predictions.csv,pipeline_report.json}` (pipeline_report: candidate_pairs 873,956; unified_customers 10,723) |
| 15 Limitations | ประเมินบนคู่ที่ sample (balanced + hard negatives) ไม่ใช่ prior ตามธรรมชาติ; TF-IDF transductive; split ด้านเดียว |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND (saved outputs) · RESULT_ARTIFACT_FOUND · AUC: ARTIFACT_CONSISTENT กับ CLAUDE.md (LOW — split/provenance ไม่ชัด); F1/P/R: UNKNOWN |
| 17 Reuse V2 | **REFERENCE_ONLY** (ไม่ใช้ผล; สถาปัตยกรรม MLP ไม่อยู่ใน core V2) |

### F06 — Leak-safe rebuilt/hybrid pipeline + multimodal suite + pub_multi benchmarks

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | สร้างชุดทดลองที่ "leak-safe" และเลือกโมเดลหลักของระบบ |
| 2 Hypothesis | การรวม TF-IDF+SBERT+attribute(+image) และ model family ที่เหมาะสมให้คุณภาพสูงสุด |
| 3 Code | [MAIN@1e0a2db:train_data/stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py], [MAIN@1e0a2db:train_data/stage7_13_multimodal_suite/run_multimodal_suite.py], [MAIN@1e0a2db:pub_multi/bench_classical_leaksafe.py], [MAIN@1e0a2db:pub_multi/bench_strict_models.py] |
| 4 Config | LR(balanced), GB(n=300, lr=0.05, depth=6), RF(400, depth 18) [run_rebuilt_pipeline.py#L418-L433 train_and_eval]; best by val AP [#L439]; isotonic on val [#L446]; threshold = argmax val F1 [#L388-L393, #L450] |
| 5 Dataset | `normalized_profiles_with_profile_id.csv` (sha256 ใน inventory) |
| 6 Preprocessing | lower/strip, URL/domain/mention/hashtag parsing [#L66-L165] |
| 7 Blocking | ไม่ใช้ (คู่ sample) |
| 8 Features | 41 features ใน run `image_context` [MAIN@1e0a2db:pub_multi/doc/model_compare.md#L3]; TF-IDF bio `fit_transform` บนทุกโปรไฟล์ที่มี entity [#L305-L313 make_profile_bundle] |
| 9 Model | LR/GB/RF (+MLP, ExtraTrees, AdaBoost, LinearSVM ใน pub_multi) |
| 10 Training | split entity 70/15/15 แบบ greedy-balanced ตามจำนวน positive [#L208-L232 assign_splits]; negative random + hard ต่อ split [#L234-L303 generate_negatives] |
| 11 Validation/test | entity-disjoint (group = profile_id) ✓; มี `single_feature_leakage_check` บน test [#L395-L416]; รายการ feature ที่ตัดเพราะเป็น label proxy [MAIN@1e0a2db:train_data/leakage_excluded_features.txt], [..._strict.txt] |
| 12 Seeds | 42 |
| 13 Metrics | GB test AP 0.9797, AUC 0.9737, F1 0.9333 (41 features) [model_compare.md#Summary]; strict no-leak: test positives 1,207 / negatives 461,701; RF/GB/LR precision 1.000, recall 0.815–0.817 [MAIN@1e0a2db:pub_multi/doc/model_strict_compare.md#L5-L11] |
| 14 Artifacts | `pub_multi/log/*.json`, `pub_multi/res/*`, `pub_multi/doc/*` |
| 15 Limitations | คู่ที่ sample ไม่ใช่ candidate set จริง; TF-IDF transductive; **operating point ของสาย strict ถูกเลือกหลังดู confusion matrix บน test** ("ควรใช้ logreg + sigmoid @ threshold 0.50 ซึ่งให้ TP=986, FP=10 …") [model_strict_compare.md#Strict Operating Point] → CONFIRMED_DEFECT ระดับการรายงาน |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND (logs) · RESULT_ARTIFACT_FOUND · ARTIFACT_CONSISTENT: UNKNOWN (ไม่ได้เทียบทุกตัวเลข) |
| 17 Reuse V2 | `assign_splits` / leakage lists → **REUSE_AFTER_VERIFICATION** (เป็น input ของ D0-4/G2); ผลโมเดล → **REFERENCE_ONLY** |

### F07 — Full-candidate pipeline (B0) + CRM entity resolution

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | ให้คะแนนคู่ candidate จริงทั้งระบบ แล้วสร้างตาราง CRM (match_decisions, review_queue, unified_profiles, lead_scores) |
| 2 Hypothesis | – (production) |
| 3 Code | [MAIN@1e0a2db:train_data/stage7_14_full_candidate_pipeline/run_full_candidate_pipeline.py], [MAIN@1e0a2db:train_data/stage15_crm_entity_pipeline/run_crm_entity_pipeline.py]; BACKUP: `src/identity_resolution/workflows/{full_candidate,crm}.py` |
| 4 Config | exact tier: username ตรงกัน (≥3 ตัวอักษร) หรือ external URL ตรงกัน → AUTO_EXACT [#L118-L150 build_exact_match_pairs]; blocking keys `username_prefix3`, `fullname_prefix3`, `external_domain` (ตัด generic domain) [#L35 BLOCKING_KEYS, #L153-L179]; decision MATCH ≥ 0.98, REVIEW ≥ 0.95 [stage15:#L117-L127, #L408-L409] |
| 5 Dataset | โปรไฟล์ที่มี `profile_id` เท่านั้น [#L83] (= 36,804/36,807 ตามสถิติ schema) |
| 6 Preprocessing | `lower_text`, prefix3 |
| 7 Blocking | ดูช่อง 4 → 2,086,245 คู่ (exact 12,403 + scored 2,073,842); blocking-missed 3,316 → PC = 0.8866 [MAIN@1e0a2db:EXPERIMENT_PLAN.md#L26-L33] |
| 8 Features | ตาม multimodal best run (41) |
| 9 Model | `best_model.pkl` ของ `image_context_r075_h20_s42` [#L202-L214] |
| 10 Training | ไม่ train ใหม่ (ใช้โมเดล F06) |
| 11 Validation/test | `split_name='full'` ทั้งหมด [EXPERIMENT_PLAN.md#L26] |
| 12 Seeds | – |
| 13 Metrics | FP 925 / FN 5,554 / REVIEW 86,296 (full) [EXPERIMENT_PLAN.md#L4, #L31-L33]; JSON บันทึก FN 5,558 [MAIN@1e0a2db:experiments/r1_results.json#rules.full.R0_production] → **ARTIFACT_INCONSISTENT เล็กน้อย (5,554 vs 5,558)**; REPORT ใช้ 5,558 (ตรง JSON) |
| 14 Artifacts | `match_decisions.parquet` **ไม่ถูก commit** → RESULT_ARTIFACT_NOT_FOUND สำหรับ input หลักของ R0/R1; `blocking_missed_pairs.csv` มี 3,316 แถว (ARTIFACT_CONSISTENT) |
| 15 Limitations | closed world (เกือบทุกโปรไฟล์มี entity); exact tier auto-MATCH ผิด 63 คู่ (full) [EXPERIMENT_PLAN.md#L31]; โมเดล scoring ถูก train บน split ที่ต่างจาก harness ของ R0–R5 |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND (ตัวเลขใน plan/JSON) · RESULT_ARTIFACT: บางส่วน |
| 17 Reuse V2 | B0 (exact tier + key blocking) → **REUSE_AFTER_VERIFICATION** เป็น E1-1; CRM merge/lead score → **REFERENCE_ONLY** (นอกขอบเขต H1–H5; ใช้ใน T10 ถ้าทำ) |

### F08 — R0 baseline + R1 GA re-decision

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | วัดว่า GA re-decision ลด FP/REVIEW ได้แค่ไหนโดยไม่ train ใหม่ [MAIN@1e0a2db:EXPERIMENT_PLAN.md#L16] |
| 2 Hypothesis | "R1 ดีขึ้นถ้า cost(test) ลดและ REVIEW ลด >50% โดย precision ≥ ~0.94" [EXPERIMENT_PLAN.md#L113] |
| 3 Code | [MAIN@1e0a2db:exp_lib.py], [MAIN@1e0a2db:exp_r1_ga_redecision.py], [MAIN@1e0a2db:run_ga_experiments.py] |
| 4 Config | genome `[t_m, t_r, c_promote, c_demote]` + name_sim band [exp_r1_ga_redecision.py#L75-L84 decide_code]; bounds t_m∈[0.90,0.999], t_r∈[0.5,t_m], c_p∈[0.5,1], c_d∈[0,c_p] [#L107-L113 clip]; fitness = 5·FP + 1·FN + 0.02·REVIEW บน val [#L15, #L96-L100, #L135-L137]; pop 60, gens 40, elite 12, uniform crossover, Gaussian σ=0.02 p=0.3, seed 42 [#L16, #L33-L43] → objective evaluations ≈ 60 + 48×40 = 1,980 genome ใหม่ (การนับจากโค้ด) |
| 5 Dataset | `match_decisions.parquet` (ไม่ commit) + `normalized_profiles_with_profile_id.csv` + `blocking_missed_pairs.csv` [exp_lib.py#L19-L21] |
| 6 Preprocessing | name_sim = max Jaro–Winkler ของ 4 คู่ userName/fullName [exp_lib.py#L48-L64]; คำนวณเฉพาะ score ≥ 0.5 [#L93-L101] |
| 7 Blocking | B0 (F07) |
| 8 Features | score จาก production model (41 features) + name_sim |
| 9 Model | ไม่มี (policy เท่านั้น) |
| 10 Training | ไม่มี |
| 11 Validation/test | split entity md5 70/30, คู่ข้าม split ถูก drop [exp_lib.py#L36-L38, #L86-L91]; GA บน val [exp_r1_ga_redecision.py#L168-L171]; รายงานบน test |
| 12 Seeds | legacy: 1 (42); automation: 5 seeds {7, 42, 123, 999, 2025} [MAIN@1e0a2db:experiments/automation/r1_20260808_200954/summary.md] |
| 13 Metrics | FP, FN, REVIEW, P, R, F1, cost (end-to-end ต่อ split) [exp_lib.py#L130-L140] |
| 14 Artifacts | [MAIN@1e0a2db:experiments/r1_results.json]: test R0 F1 0.7964, R1 0.8292, manual_stage18 0.8439; automation r1: F1 0.8292 ± 0.0000 (5 seeds) |
| 15 Limitations | (a) production model train บน split 70/15/15 seed 42 ของ F06 ซึ่ง *ไม่สอดคล้อง* กับ md5 split → entity ใน test ของ harness น่าจะเคยอยู่ใน training ของโมเดล score (STATIC_RISK leakage ต่อ R0/R1); (b) ไม่มี non-GA optimizer; (c) ไม่มี CI |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND (`r1_ga_history.json`, automation timestamped dirs) · RESULT_ARTIFACT_FOUND · **ARTIFACT_CONSISTENT** (REPORT#L13-L14 = JSON) |
| 17 Reuse V2 | `evaluate`/`split_constants` (แนวคิด end-to-end) และ GA → **REUSE_AFTER_VERIFICATION** (E6-5, E7-1); score ของ R0 → **EXCLUDE** จากผล V2 (ใช้เป็น historical replica ของ policy ใน E6-1 เท่านั้น) |

### F09 — R2/R3 MiniLM semantic feature (+GA)

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | วัดว่า transformer representation ช่วยแค่ไหน [EXPERIMENT_PLAN.md#L17] |
| 2 Hypothesis | "R2 ดีขึ้นถ้ากู้ FN-in-candidate ได้โดย FP ไม่บวม" [EXPERIMENT_PLAN.md#L114] |
| 3 Code | [MAIN@1e0a2db:exp_r2_bert_feature.py] |
| 4 Config | `all-MiniLM-L6-v2` encode ข้อความ `fullName + bio + location` ต่อโปรไฟล์ [#L78-L92, #L104]; feature 18 = cosine; IdentityMLP [256,128,64], FocalLoss, 30 epochs, patience 5, neg ratio 3.0 [#L301-L310 constants]; R2 policy = 0.98/0.95 [#L584]; R3 = GA เดิม [#L613-L625 run_r3] |
| 5 Dataset | cache ของ F08 + `pair_features17.parquet`, `pair_bert_cos.parquet`, `profile_embeddings_minilm.npy` (committed; PRIVACY: มี pair/profile id) |
| 6 Preprocessing | clean "", "nan"; "[empty]" ถ้าว่าง |
| 7 Blocking | B0 |
| 8 Features | 17 hand features: username_{jaro,lev_sim,token_sort}, fullname_{jaro,lev_sim,token_sort}, name_sim, bio_{jaccard,len_ratio}, both_have_bio, location_{jaro,exact}, both_have_location, same_platform, username_len_diff, fullname_wordcount_diff, username_prefix3_match [#L53-L61] + bert_cos |
| 9 Model | IdentityMLP |
| 10 Training | legacy: train บน 85% ของคู่ใน val (stratified *ตามคู่* ไม่ใช่ entity) + isotonic บน 15% ที่เหลือ [#L526-L548 build_r2_probabilities]; nested (ส.ค.): model_train/model_calibration/ga_validation แยก entity 70/15/15 ภายใน dev [MAIN@1e0a2db:exp_lib.py#L145-L221 build_nested_entity_split], [exp_r2_bert_feature.py#L867-L930 train_r2_probabilities (override)] |
| 11 Validation/test | legacy: GA tune บน val ทั้งชุด (รวมคู่ที่ใช้ train MLP) → STATIC_RISK (threshold tuning บน in-sample predictions); test 30% เหมือน F08 |
| 12 Seeds | legacy 1; nested model seeds {42, 7, 123} × GA 5 seeds |
| 13 Metrics | legacy test: R2 F1 0.7393, R3 0.8373 [MAIN@1e0a2db:experiments/r2_results.json], [r3_results.json]; FN recovery R2 282/2,242, R3 728/2,242 [r2_r3_fn_recovery.json]; nested R3: F1 0.8615 ± 0.0001 (model seed 42), 0.8642 ± 0.0041 (seed 7), 0.8620 ± 0.0001 (seed 123); baseline R2-manual 0.8224/0.8434/0.8547 [automation/r3_*/summary.md] |
| 14 Artifacts | ตามช่อง 13 + `r3_ga_history.json`, `r2_run.log` |
| 15 Limitations | R0→R2 ไม่ใช่การเพิ่ม feature อย่างเดียว (A1); manual threshold 0.98/0.95 ไม่ได้ re-tune ให้ score scale ใหม่ (ผู้เขียนยอมรับเอง [REPORT#L50-L52]) → R2-manual เป็น baseline ที่อ่อน; ความแปรปรวนจาก model seed ของ baseline (0.82–0.85) ใหญ่กว่าความต่าง R3 nested ระหว่าง seed |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND (`r2_run.log`, training_history.csv) · RESULT_ARTIFACT_FOUND · **ARTIFACT_CONSISTENT** (REPORT#L15-L16, #L45-L48 = JSON) |
| 17 Reuse V2 | feature code (17 hand features, MiniLM cosine) → **REUSE_AFTER_VERIFICATION** เป็นส่วนหนึ่งของ F-LEX/F-SEM; MLP → **REFERENCE_ONLY**; ผล → HIST |

### F10 — R4/R5 Bloom-filter encoding (+GA)

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | privacy/accuracy trade-off [EXPERIMENT_PLAN.md#L103-L107] |
| 2 Hypothesis | "R4 ยอมรับได้ถ้า F1 ตก < ~2–3 จุด" [EXPERIMENT_PLAN.md#L115] |
| 3 Code | [MAIN@1e0a2db:exp_r4_bloom_privacy.py] |
| 4 Config | L ∈ {2000, 1000, 500, 250}, k = 10, bigram, md5 กับ **salt คงที่ที่อยู่ในโค้ด** [#L48-L50, #L80-L90] |
| 5 Dataset | เหมือน F09; `experiments/bloom/*.npz/*.parquet` (committed; PRIVACY) |
| 6–7 | เหมือน F09 |
| 8 Features | dice_username, dice_fullname, name_sim_bloom + **feature ที่ไม่ใช่ชื่อแบบ plaintext** (bio/location/platform/length) [#L58-L62 NON_NAME_COLS, #L192] |
| 9 Model | IdentityMLP |
| 10 Training | เหมือน F09 legacy (val, pair-level split) [#L195-L210] |
| 11 Validation/test | GA ใช้ `name_sim_bloom` [#L253-L263] บน val; test 30% |
| 12 Seeds | 1 |
| 13 Metrics | R4 test F1 0.7244–0.7397; R5 0.8308–0.8329 [MAIN@1e0a2db:experiments/r4_privacy_tradeoff.json] |
| 14 Artifacts | `r4_privacy_tradeoff.json/.png`, `r4_run.log` |
| 15 Limitations | ไม่มี threat model/attack; salt อยู่ใน source code → dictionary/frequency attack ทำได้ทันที [P29–P31, P35]; bio/location ยังเป็น plaintext; REPORT ระบุทิศทาง privacy ขัดกับแผน (REPORT#L17, #L20 เรียก L=2000 ว่า "privacy สูงสุด" และ L=250 "privacy ต่ำสุด/ชนบ่อยสุด" ขณะที่แผนระบุ "L เล็ก = ชนกันเยอะ = privacy สูง" [EXPERIMENT_PLAN.md#L106]) → ข้ออ้าง "ปลอดภัยกว่ามาก" [REPORT#L126-L128] **ไม่มีหลักฐานรองรับ** |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND · RESULT_ARTIFACT_FOUND · **ARTIFACT_CONSISTENT** (ตัวเลข REPORT#L17-L24 = JSON) |
| 17 Reuse V2 | encoder → **REIMPLEMENT** (keyed HMAC, threat model) ใน T8 เท่านั้น; ข้ออ้าง privacy → **EXCLUDE** |

### F11 — R6 BERT-ER semantic hash blocking

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | กู้คู่ 3,316 ที่ blocking พลาด [REPORT#L61-L67] |
| 2 Hypothesis | learnable hash บน BERT embedding จับคู่ที่ชื่อต่างกันได้ |
| 3 Code | [MAIN@1e0a2db:exp_r6_bert_er.py]; แผน GPU [MAIN@1e0a2db:experiments/R6_GPU_IMPLEMENT_PLAN.md] |
| 4 Config | `distilbert-base-uncased` frozen [#L70, #L157-L160], HASH_BITS 64 [#L71], EPOCHS 40 [#L75] (REPORT ระบุ 27 epochs [REPORT#L95] — น่าจะ early stop; UNKNOWN), cosine contrastive loss, match head |
| 5 Dataset | cache F08; held-out 3,316 คู่ ห้ามใช้ train (assert) [#L230-L241] |
| 6 Preprocessing | serialize โปรไฟล์เป็นข้อความ |
| 7 Blocking | Hamming radius 0/1 ใน hash space |
| 8 Features | embedding [h_a, h_b, h_a·h_b, |h_a−h_b|] |
| 9 Model | hash head + match head (MLP) |
| 10 Training | คู่ใน val + random negatives [#L250-L283 build_training_pairs] |
| 11 Validation/test | GA บน val [#L566]; test 30% |
| 12 Seeds | 1 |
| 13 Metrics | recovery 0/3,316 (r0), 4/3,316 (r1); R6 test F1 0.6053; R6-GA 0.7801 [r6_results.json], [r6_blocking_recovery.json] |
| 14 Artifacts | `r6_*` JSON/log, `experiments/r6_bert_er/r6_probabilities.parquet` (PRIVACY) |
| 15 Limitations | frozen backbone (CPU); ไม่คุม candidate budget; hash bucket ให้คู่ใหม่เพียง 2,006 คู่ [r6_results.json#new_blocking]; ไม่ได้เทียบกับ kNN dense retrieval ธรรมดา |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND (`r6_run.log`) · RESULT_ARTIFACT_FOUND · **ARTIFACT_CONSISTENT** (REPORT#L85-L88, #L103-L104 = JSON); แผน GPU = **PROPOSED_NEVER_EXECUTED** |
| 17 Reuse V2 | **REFERENCE_ONLY** (V2 ใช้ dense kNN top-k ที่คุม budget ใน E1-4 แทน; hash blocking ไม่อยู่ใน core) |

### F12 — Nested-protocol GA automation (multi-seed, cost sensitivity)

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | ทำให้ R1/R3 "publication-grade": nested entity split, หลาย seed, sensitivity ของ cost |
| 2 Hypothesis | ผลของ GA เสถียรข้าม seed และ cost ratio |
| 3 Code | [MAIN@1e0a2db:run_ga_experiments.py#L585-L937 publication-grade override + main], [MAIN@1e0a2db:exp_lib.py#L145-L247] |
| 4 Config | dev แบ่ง model_train 70 / model_calibration 15 / ga_validation 15 (entity, md5 + seed) [exp_lib.py#L145-L146]; test เดิม 30% "sealed" [#L191-L192]; sensitivity W_FN=2 และ W_FP=10 |
| 5 Dataset | เหมือน F08/F09 |
| 6–9 | เหมือน F08/F09 |
| 10 Training | R2 MLP train ใหม่บน model_train, calibrate บน model_calibration |
| 11 Validation/test | GA บน ga_validation เท่านั้น; ตรวจ entity overlap = 0 และ raise ถ้าพบ [exp_lib.py#L197-L207] ✓ |
| 12 Seeds | GA 5 seeds; R2 model seeds 42/7/123 |
| 13 Metrics | ดู F08/F09 ช่อง 13; sensitivity: F1 0.8614–0.8615 ทั้ง W_FN=2 และ W_FP=10 [automation/r3_sensitivity_*/summary.md] |
| 14 Artifacts | `experiments/automation/*/{config,summary,trials,generations,split_manifest,environment}.json/csv` (+ model .pt/.pkl) |
| 15 Limitations | test เดิมถูกใช้ซ้ำ (A6); ยังไม่มี non-GA baseline; ไม่มี CI (SD ข้าม GA seed เล็กมาก ≈ 0.0001 → ความแปรปรวนจริงมาจาก model seed/การ sample ข้อมูลซึ่งไม่ถูกประเมิน) |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND (`environment.json`, `status.json`, timestamp dirs) · RESULT_ARTIFACT_FOUND · ARTIFACT_CONSISTENT (summary.md ↔ trials.csv ภายใน run; ตรวจเฉพาะ r1_nested/r3_primary) |
| 17 Reuse V2 | `build_nested_entity_split` + entity-overlap assert → **REUSE_AFTER_VERIFICATION** (โครง D_train/D_cal/D_policy ของ V2); ผล → HIST |

### F13 — GB-17 / GB-18 / GB-18-GA (classical ML + MiniLM)

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | แยกผลของ MiniLM (GB-17→GB-18) และ decision layer (GB-18→GB-18-GA) ด้วย model family เดียว [MAIN@1e0a2db:run_gb_transformer_experiments.py#L1-L12] |
| 2 Hypothesis | "fair GB comparison" |
| 3 Code | [MAIN@1e0a2db:run_gb_transformer_experiments.py] |
| 4 Config | GradientBoosting(n=300, lr=0.05, depth=6, rs=42) (ไม่ tune) [#L296, #L582]; isotonic บน model_calibration [#L279-L301 train_gb_variant] |
| 5 Dataset | nested split seed 42 (F12) |
| 6–8 | 17 / 18 features ตาม F09 |
| 9 Model | GB |
| 10 Training | model_train, undersample neg ratio 3.0 [#L269-L295 deterministic_sample_indices/train_gb_variant] |
| 11 Validation/test | GA บน ga_validation; test ครั้งเดียว |
| 12 Seeds | model 1 (42); GA 5 |
| 13 Metrics | test F1: GB-17 0.5967, GB-18 0.8296, GB-18-GA 0.8612, R3 0.8615; weighted cost: R3 1,917.39 < GB-18-GA 2,083.22 [MAIN@1e0a2db:experiments/automation/gb_transformer_primary_20260809/summary.md], [test_results.csv]; repro run ให้ผลเหมือนกันทุกหลัก [gb_transformer_repro_20260809/test_results.csv] |
| 14 Artifacts | `artifact_hashes.json`, `split_manifest.json`, model pkl |
| 15 Limitations | ใช้ manual threshold 0.98/0.95 กับ GB ที่ score scale ต่างกัน → GB-17 F1 0.5967 สะท้อน threshold ไม่ใช่ representation; ไม่ tune hyperparameter; seed เดียว |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND · RESULT_ARTIFACT_FOUND · ARTIFACT_CONSISTENT (summary.md ↔ test_results.csv; primary ↔ repro เหมือนกัน = deterministic reproducibility ภายในเครื่องเดิม) |
| 17 Reuse V2 | โครงการเปรียบเทียบแบบ isolated effect → แนวคิดของ E5-1 vs E5-3; โค้ด → **REUSE_AFTER_VERIFICATION**; ผล → HIST |

---

## C. Families ใน BACKUP (F14–F18)

> ส่วนนี้สังเคราะห์จากบันทึกของ Agent A2 (`review/_work/agentA2/BACKUP_FAMILIES.md`) — ดู "Reconciliation notes" ท้ายเอกสาร

หลัก provenance: run ของ ICSEC ทั้งหมดรันจาก working tree ที่ยังไม่ commit บนเครื่องผู้ใช้ (HEAD = MAIN@1e0a2db, dirty) และโค้ดที่รันจริงมี sha256 ตรงกับไฟล์ที่ภายหลัง commit ใน BACKUP@903246c/ab93b36 [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2r1/provenance/v2r1_manifest.json#git_commit,sources]

### F16a — ICSEC v1 / historical (`primary_reproduction`, `repeated_outer`, `authoritative_run`)

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | เทียบ GB-17, GB-18 (+MiniLM), GB-18-GA [BACKUP@ab93b36:experiments/icsec_final/authoritative_run/PROTOCOL.md#L1-L8] |
| 2 Hypothesis | MiniLM เพิ่มคุณค่า; GA ลด utility U เทียบ fixed threshold [BACKUP@ab93b36:paper/ieee/main.tex#L125-L127] |
| 3 Code | [BACKUP@ab93b36:experiments/icsec_final/authoritative_run/run_authoritative_outer.py#L16-L24]; [BACKUP@ab93b36:experiments/code/run_icsec_repeated_outer.py#L1-L58]; [BACKUP@ab93b36:experiments/code/analyze_icsec_primary.py#L60-L97] |
| 4 Config | GB(300, 0.05, 6, rs=42); undersample 3:1; isotonic; fixed 0.98/0.95; GA pop 60 × gen 40, elites 12, seeds 7/42/123/999/2025; U = 2FP + FN + 0.1REVIEW [PROTOCOL.md#L38-L55] |
| 5 Dataset | `normalized_profiles_with_profile_id.csv` sha256 17a95f75…; cache `scored_pairs_enriched.parquet` 396884be…, `pair_features17.parquet` 215d2a1e…, `pair_bert_cos.parquet` 687e93cb… [BACKUP@ab93b36:experiments/icsec_final/statistical_analysis/analysis_manifest.json#source_hashes] |
| 6 Preprocessing | keep_default_na=False; ต้องมี profile_row_id/profile_id ตัวเลข |
| 7 Blocking | B0 (F07) |
| 8 Features | 17 hand features (+bert_cos) — **name_sim แบบ gated** (เป็นศูนย์ถ้า score ของโมเดลเดิม < 0.5) [BACKUP@ab93b36:experiments/code/exp_lib.py#L28,L93-L101] |
| 9 Model | GB + isotonic |
| 10 Training | model_train 70% / calibration 15% ของ development (entity_nested_v1) |
| 11 Val/test | outer MD5(`icsec-outer-v1:seed:entity`)%100<30 → test; GA บน ga_validation; **v1 โหลด label ของ test เข้าตาราง candidate ก่อน fit** [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/REPAIR_PROTOCOL.md#L12-L14] |
| 12 Seeds | outer 101/202/303 × GA 5 seeds |
| 13 Metrics | TP/FP/FN/REVIEW, P, R (รวม REVIEW positive + blocking miss ในตัวหาร), F1, U; mean ± SD |
| 14 Artifacts | GB-17 F1 0.8293 ± 0.0278; GB-18 0.8280 ± 0.0223; GB-18-GA 0.8604 ± 0.0012, U 1801.67 [BACKUP@ab93b36:experiments/icsec_final/authoritative_run/AUTHORITATIVE_RESULTS.md#L41-L49] |
| 15 Limitations | name_sim gated; label อ่านก่อน fit; GA เทียบเฉพาะ fixed threshold; pair bootstrap |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND · RESULT_ARTIFACT_FOUND (ส่วนใหญ่ LFS, content-not-inspected) · **ARTIFACT_INCONSISTENT** ระหว่าง IEEE draft (GB-18-GA F1 .8603, U 1802.7) กับ authoritative_run (0.860406, 1801.67) [BACKUP@ab93b36:paper/ieee/main.tex#L100-L104] |
| 17 Reuse | **EXCLUDE** (ผล) · REFERENCE_ONLY (บันทึกข้อบกพร่อง) |

### F16b — ICSEC v2 / v2r1 (ตัวเลขของ paper)

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | ทำซ้ำโดยแก้ name_sim, แยก label ทางกายภาพ และ baseline ที่แยกผล validation tuning (B0→B1), policy class (B1→B2), optimizer (B2 Sobol vs B3 GA) [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/REPAIR_PROTOCOL.md#L16-L27] |
| 2 Hypothesis | claim rule ประกาศล่วงหน้า: B3 > B2 สม่ำเสมอ → อภิปรายประโยชน์ของ GA ได้; B3 ≈ B2 → ยกให้ policy class ไม่ใช่ GA [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/CLAIM_PROTOCOL.md#L3-L7] |
| 3 Code | [BACKUP@ab93b36:experiments/code/run_icsec_authoritative_v2.py#L83-L367]; `authoritative_run_v2/{features,policies,final_runner,real_adapters,artifact_producers,label_sealing}.py`; v2r1 `run_v2r1.py`, `sealed_guard.py` |
| 4 Config | FINAL_BUDGET 12,000; B1 unscrambled Sobol d=2; B2 Sobol d=4 (budget = realized ของ B3); B3 GA pop 60, mutation-only (**ไม่มี crossover**) [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/policies.py#L53-L118] |
| 5 Dataset | sha256 17a95f75…; frozen inputs workflow.parquet 30d168d4…, gb17.parquet 960fe07b…, bert_cos.parquet 9c569348…; MiniLM revision 1110a243… [v2r1_manifest.json#frozen_inputs,minilm] |
| 6 Preprocessing | NFKC + casefold + whitespace + strip '@'; 36,804 eligible |
| 7 Blocking | B0: 12,403 exact + 2,073,842 scored; ครอบคลุม 25,931 / 29,243 positive; พลาด 3,312 (recall 88.67%) [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/provenance/preflight_manifest.json#candidate_scope] |
| 8 Features | 17 (name_sim ไม่ gate) + bert_cos [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/features.py#L12-L19]; same_platform = 0 คงที่ |
| 9 Model | GB-17/GB-18 + isotonic [final_runner.py#L149-L175] |
| 10 Training | undersample 3:1 ใน TRAIN; calibrator บน CALIBRATION เต็ม |
| 11 Val/test | role = MD5(`entity_nested_v2:seed:entity`)%100<30 → SEALED_TEST; dev → TRAIN 70 / CAL 15 / POLICY_VAL 15; คู่ข้าม role ถูก drop (seed 101: 1,344,063 / 2,086,245) [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/preflight/routing_static.json#seeds.101]; sealed label store; pre-final label materialisation = 0 [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/process_label_access_audit.json] |
| 12 Seeds | outer 101/202/303; optimizer 1 seed ต่อ partition; GB rs=42 |
| 13 Metrics | workflow = exact + scored + blocking miss (FN); **"decision recall" ไม่นับ REVIEW positive ในตัวหาร** [final_runner.py#L52-L62]; U; mean ± SD; **ไม่มี CI** |
| 14 Artifacts | F1: GB17_B0 0.8494, B0 0.8510, B1 0.8910, B2 0.8901, B3 0.8903; U 2352.0 / 2364.2 / 1864.6 / 1860.0 / 1858.2 [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/FINAL_RESULTS.md#L27-L33]; B3 unique vectors 8,414–8,874 จาก 12,000 [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2r1/optimizer_budget_transparency.json] |
| 15 Limitations | 3 partitions; calibration prior shift (CAL 5.7% vs TEST 2.2% positive → over-prediction) [BACKUP@ab93b36:artifacts/audit/icsec_review_20261010/evidence.json#role_priors,calibration_diagnostics]; 64% ของคู่ถูก drop; Sobol unscrambled ไม่มี seed; test เคยเห็นผล v1 แล้ว |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND (process audit ≈2026-09-05) · RESULT_ARTIFACT_FOUND · **ARTIFACT_CONSISTENT** (FINAL_RESULTS = final_evidence.json = v2r1 independent_metrics; paper ตรง) |
| 17 Reuse | **REUSE_AFTER_VERIFICATION** (sealed-label store, freeze manifest, route_pairs, budget audit) · **REPLICATE** (ผล) — BLOCKED โดย G0/G1 |

### F17 — Reviewer-driven revision

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | วิเคราะห์เพิ่มบนหลักฐาน v2r1 ที่ freeze แล้ว: M1 e2e recall/F1 ที่นับ REVIEW; M2 Chow rule; M4 anytime replay; M5 claim cleanup [BACKUP@ab93b36:experiments/icsec_final/reviewer_revision/PROTOCOL.md#L3-L13] |
| 2 Hypothesis | ข้อกังวลของ reviewer: REVIEW ทำให้ recall สูงเกิน; rule ตรงอาจเท่ากับ policy ที่ค้นหา |
| 3 Code | [BACKUP@903246c:experiments/code/reviewer_revision.py]; `run_reviewer_revision.py`; tests |
| 4 Config | C(NO_MATCH)=(0,1), C(REVIEW)=(0.1,0.1), C(MATCH)=(2,0) — argmin [p, 0.1, 2(1−p)] |
| 5 Dataset | row-level decisions ของ v2r1 (LFS, ตรวจด้วย hash) |
| 6–10 | สืบทอด v2r1; `model_refit=false`, `calibration_refit=false`, `test_tuning=false` [BACKUP@ab93b36:experiments/icsec_final/reviewer_revision/provenance.json] |
| 11 Val/test | Chow ไม่มีพารามิเตอร์ให้ tune; ประเมินบน sealed test เดิม |
| 12 Seeds | 101/202/303 |
| 13 Metrics | + positive_REVIEW, e2e recall/F1, review rate, coverage |
| 14 Artifacts | e2e F1: B0 0.8420, B1 0.8667, B2 0.8611, B3 0.8610, Chow 0.8542; U Chow 1879.0 [BACKUP@ab93b36:experiments/icsec_final/reviewer_revision/aggregate.json]; tests 102 passed [tests_final.log] |
| 15 Limitations | Chow ถูกเพิ่มหลังเห็นผล test ของ B0–B3 (post-hoc baseline บน test ที่ใช้ซ้ำ); ไม่มี CI |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND · RESULT_ARTIFACT_FOUND · **ARTIFACT_CONSISTENT** (paper Table = aggregate.json) [BACKUP@ab93b36:paper/reviewer_revision/NUMERIC_CLAIM_AUDIT.json] |
| 17 Reuse | **REUSE_AFTER_VERIFICATION** (M1 metric, Chow rule เป็น baseline บังคับ) · ผล REFERENCE_ONLY |

### F14 — Feature-aware GA / policy weight optimisation

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | แทน/เสริม name_sim guard ด้วยกลุ่มหลักฐานอื่น (selector policies → one-stage weighted 10 ยีน) [BACKUP@ab93b36:docs/plans/GA_FEATURE_AWARE_DECISIONING_PLAN_TH.md] |
| 2 Hypothesis | feature-aware policy ลด CRM cost โดยผ่าน Precision ≥ 0.99 และ Recall ≥ 0.70 [BACKUP@ab93b36:docs/plans/NAME_SIM_GA_PROOF_CLOSURE_PLAN_TH.md#1] |
| 3 Code | [BACKUP@ab93b36:experiments/code/run_feature_aware_ga_pipeline.py#L83-L370]; `run_full_feature_aware_ga_pipeline.py`; `run_one_stage_weighted_ga_experiment.py`; `run_full_2m_one_stage_ga.py` |
| 4 Config | one-stage pop 128 × gen 100 × seeds 42–51; cost crm_derived_v1; comparator legacy pop 60 × gen 40 (budget ไม่เท่า) |
| 5 Dataset | (a) `pub_multi/data/train_all.parquet` 58,696 แถว ae3735c3…; (b) cache v1 `scored_pairs_enriched.parquet` 396884be… |
| 6–7 | group score = max ของ similarity ในกลุ่ม; (a) ไม่มี blocking; (b) B0 |
| 8 Features | 37 features รวม 18 image features [BACKUP@ab93b36:artifacts/decisioning/feature_aware_ga/automated_20260831_final/feature_manifest.json] |
| 9 Model | `probability` จากโมเดลเดิม (multimodal หรือ CRM scorer) |
| 10–11 | GA บน val; (b) val/test split ถูกใส่ภายหลังการให้คะแนน → scorer อาจเคยเห็น test entity |
| 12 Seeds | 10 / 3 |
| 13 Metrics | candidate-level (full-2M one-stage ไม่นับ blocking miss) |
| 14 Artifacts | one_stage_weighted_full_20260914 test F1: 10-gene 0.8987 (cost 362.5) vs score-only 0.8932 (360.8) vs legacy name guard 0.9029 (484.5) [BACKUP@ab93b36:artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_20260914/full_result.json#test_metrics] |
| 15 Limitations | function class/budget/population ไม่เท่ากัน; ไม่มี non-GA optimizer; pair bootstrap |
| 16 Lifecycle | CODE_FOUND · EXECUTION_EVIDENCE_FOUND · RESULT_ARTIFACT_FOUND · report-vs-artifact: UNKNOWN |
| 17 Reuse | **REFERENCE_ONLY**; full-2M บน cache v1 → **EXCLUDE** |

### F15 — Name-similarity ablation (N0–N7) + feature attribution

| ช่อง | รายละเอียด |
|---|---|
| 1 Objective | name similarity ที่ซับซ้อนขึ้น (Damerau, char n-gram, token-set, handle, phonetic) ช่วย baseline multimodal หรือไม่ [BACKUP@ab93b36:experiments/code/exp_name_similarity_ablation.py#L48-L69] |
| 2 Hypothesis | name features ครอบงำหลักฐาน; หลักฐานอื่นแทน name_sim ไม่ได้ |
| 3 Code | `exp_name_similarity_ablation.py`, `exp_feature_attribution.py`, `src/identity_resolution/stages/feature_registry.py` |
| 4 Config | LR / GB(300, 0.05, 6) / RF(400, 18); seed 42 |
| 5 Dataset | sha256 17a95f75… ผ่าน train_base |
| 6–7 | positive จาก profile_id; random + hard negatives (prefix bucket); ไม่มี blocking |
| 8 Features | multimodal base + 15 name features |
| 9 Model | best by val AP (GB) + isotonic |
| 10 Training | train 41,803 / val 8,580 / test 8,313 คู่ |
| 11 Val/test | entity split 70/15/15 (overlap 0); model selection + calibration + threshold + รายงาน บน val เดียวกัน (in-sample); test sealed (ไม่มี test_metrics.json) |
| 12 Seeds | 42 |
| 13 Metrics | val AP/AUC/P/R/F1 |
| 14 Artifacts | val F1 N0 0.9410 → N6 0.9553; AP 0.9809 → 0.9850 (คู่ ≈51% positive) [BACKUP@ab93b36:artifacts/evaluation/name_similarity/N*/validation_metrics.json] |
| 15 Limitations | คู่ balanced; in-sample val; N7 ไม่เคยรัน |
| 16 Lifecycle | N0–N6: CODE · EXEC · RESULT (validation only); N7 + attribution: **PROPOSED_NEVER_EXECUTED** |
| 17 Reuse | **REFERENCE_ONLY**; name functions → REIMPLEMENT/REUSE_AFTER_VERIFICATION |

### F07b — Production package `src/identity_resolution/**` (CRM)

สรุป: CODE_FOUND; RESULT_ARTIFACT_FOUND (CRM exports; `customer_360.json` committed เป็นข้อมูลดิบ — PRIVACY); checkpoint ของ production model **ไม่มี** → EXECUTION_EVIDENCE ของโมเดลที่เลือก: UNKNOWN [BACKUP@ab93b36:docs/research_rebuild/phase_01/05_DATA_AND_EXPERIMENT_LIMITATIONS.md#L52]; train_base: TF-IDF fit บนทุกโปรไฟล์, selection/calibration/threshold บน val เดียวกัน [BACKUP@ab93b36:src/identity_resolution/stages/train_base.py#L308-L311, #L425-L476]; Reuse: full_candidate + core/name_similarity → REUSE_AFTER_VERIFICATION; train_base split/TF-IDF → REIMPLEMENT; scorer → RETRAIN; lead scoring → EXCLUDE (ไม่เคยถูก validate กับ outcome)

### F18 — Research rebuild Phase 1 / Phase 1.5 gates

สรุป: Phase 1 audit (221 metric records / 142 checks) RESULT_ARTIFACT_FOUND [BACKUP@ab93b36:docs/research_rebuild/phase_01/06_PHASE_1_READINESS_GATE.md#L21]; Phase 1.5 gate code (split_safety, evaluator, run_manifest, feature18_contract) CODE_FOUND + EXECUTION_EVIDENCE_FOUND (synthetic tests) [BACKUP@ab93b36:handoff/worktrees/research-phase15-integration/docs/research_rebuild/phase_01_5/INTEGRATED_TEST_EVIDENCE.json]; Gate status: snapshot/entity mapping/ground truth NOT VERIFIED, Gate 8 PENDING HUMAN APPROVAL, Gate 9 NOT FROZEN, "Phase 2 NO-GO" [BACKUP@ab93b36:handoff/worktrees/research-phase15-integration/docs/research_rebuild/phase_01_5/GATE_STATUS_MATRIX.md#L3-L15]; Gate 9 config (P0 fixed, P1 Chow, P2 two-threshold, P3 random, P4 scrambled Sobol, P5 GA; 2,048 calls) = **PROPOSED_NEVER_EXECUTED**; Reuse: **REUSE_AFTER_VERIFICATION** เป็นโครง protocol ของ V2

### Tests (backup)

16 ไฟล์ (เหมือนกันใน 903246c/ab93b36): synthetic 13; real-data 1 (`test_authoritative_v2_preflight.py`); mixed 1 (`test_ga_runner.py` ข้ามถ้าไม่มี cache) [`review/_work/agentA2/BACKUP_FAMILIES.md` Family 7] — **ไม่ได้รันในรอบนี้** (pytest ไม่ได้ติดตั้งสำหรับ python3.11); หลักฐานการรันเดิม: 102 passed [BACKUP@ab93b36:experiments/icsec_final/reviewer_revision/tests_final.log]


---

## D. ตารางสรุป lifecycle (ทุก family)

| Family | CODE_FOUND | EXECUTION_EVIDENCE_FOUND | RESULT_ARTIFACT_FOUND | Consistency | Reuse |
|---|---|---|---|---|---|
| F01 Lexical (ม.ค.) | ✓ | UNKNOWN | UNKNOWN | — | REFERENCE_ONLY |
| F02 Bigram | ✓ | ✓ | ✓ | UNKNOWN | REFERENCE_ONLY |
| F03 SBERT bio | ✓ | ✓ (saved outputs) | UNKNOWN | — | REFERENCE_ONLY |
| F04 Image | ✓ | ✓ | ✓ (ผ่าน F06) | UNKNOWN | BLOCKED |
| F05 Notebook IdentityMLP | ✓ | ✓ | ✓ | AUC CONSISTENT (LOW) | REFERENCE_ONLY |
| F06 Leak-safe multimodal / pub_multi | ✓ | ✓ | ✓ | UNKNOWN; strict op-point เลือกจาก test | REFERENCE_ONLY / REUSE_AFTER_VERIFICATION (lists) |
| F07 B0 + CRM | ✓ | ✓ | บางส่วน (`match_decisions` NOT_FOUND) | blocking_missed CONSISTENT; FN 5,554 vs 5,558 INCONSISTENT (เล็กน้อย) | REUSE_AFTER_VERIFICATION (B0) |
| F08 R0/R1 | ✓ | ✓ | ✓ | CONSISTENT | REPLICATE (policy) / EXCLUDE (score) |
| F09 R2/R3 | ✓ | ✓ | ✓ | CONSISTENT | REIMPLEMENT / REPLICATE |
| F10 R4/R5 | ✓ | ✓ | ✓ | CONSISTENT (ตัวเลข); ข้ออ้าง privacy ไม่มีหลักฐาน | REIMPLEMENT |
| F11 R6 | ✓ | ✓ | ✓ | CONSISTENT; GPU plan PROPOSED_NEVER_EXECUTED | REFERENCE_ONLY |
| F12 Nested automation | ✓ | ✓ | ✓ | CONSISTENT | REUSE_AFTER_VERIFICATION |
| F13 GB-17/18/18-GA | ✓ | ✓ | ✓ | CONSISTENT (primary = repro) | REUSE_AFTER_VERIFICATION / REPLICATE |
| F14 Feature-aware GA | ✓ | ✓ | ✓ | UNKNOWN | REFERENCE_ONLY / EXCLUDE |
| F15 Name-sim N0–N6 (N7) | ✓ | ✓ (N7: PROPOSED_NEVER_EXECUTED) | ✓ (validation) | — | REFERENCE_ONLY |
| F16a ICSEC v1 | ✓ | ✓ | ✓ (LFS) | IEEE draft INCONSISTENT | EXCLUDE |
| F16b ICSEC v2/v2r1 | ✓ | ✓ | ✓ | CONSISTENT | REUSE_AFTER_VERIFICATION / REPLICATE |
| F17 Reviewer revision | ✓ | ✓ | ✓ | CONSISTENT | REUSE_AFTER_VERIFICATION |
| F18 Phase 1 / 1.5 gates | ✓ | ✓ (synthetic) | ✓ (audit) | — ; Gate 9 PROPOSED_NEVER_EXECUTED | REUSE_AFTER_VERIFICATION |

ไม่มี family ใดได้ `INDEPENDENTLY_VERIFIED` (ไม่มีการรันซ้ำในรอบนี้)

## Reconciliation notes

| ประเด็น | ฝั่ง A | ฝั่ง B | ข้อยุติ |
|---|---|---|---|
| ขอบเขตของ "R0 = 17 features" | EXPERIMENT_PLAN เดิมเรียก R0 ว่า "17 feature (เดิม)" [MAIN@1e0a2db:EXPERIMENT_PLAN.md#L12] | โค้ดแสดงว่า score ของ R0 มาจาก multimodal best run (41 features) [MAIN@1e0a2db:train_data/stage7_14_full_candidate_pipeline/run_full_candidate_pipeline.py#L22]; [MAIN@1e0a2db:pub_multi/doc/model_compare.md#L3] | repository (โค้ด) ชนะสำหรับ "สิ่งที่เกิดขึ้น" → R0 = 41-feature model; "17 features" ใช้ได้เฉพาะ R2/R3/GB-17 |
| จำนวนคู่จริงทั้งหมด | 29,247 [MAIN@1e0a2db:exp_lib.py#L26] | 29,243 (นับใหม่จาก schema; ตรงกับ canonical ของ BACKUP Phase 1 [BACKUP@ab93b36:docs/research_rebuild/phase_01/01_DATASET_AND_FEATURE_LINEAGE.md#L106]) | ใช้ 29,243 เป็นค่า canonical; 29,247 = ค่าเก่า (stale) ที่ BACKUP จัดเป็น HISTORICAL |
| Blocking miss | 3,316 (MAIN plan/REPORT; CSV 3,316 แถว) | 3,312 (BACKUP preflight) | ต่างตาม canonical positive set (29,247 vs 29,243); ใช้ค่า BACKUP v2 คู่กับ 29,243 |
| GA vs non-GA | Lead (MAIN): ไม่มี non-GA baseline | Agent A2 (BACKUP): ICSEC v2 มี Sobol budget เท่ากัน | ทั้งสองถูกในขอบเขตของตัวเอง → assumption ถูกยืนยันสำหรับ R-series/ICSEC v1 และถูกล้มสำหรับ ICSEC v2 |
| name_sim | Lead: ไม่ได้ระบุว่าเป็น defect ในร่างแรก | Agent A2: CONFIRMED_DEFECT (gated by predecessor score) | ยอมรับข้อของ A2 — ตรวจ [MAIN@1e0a2db:exp_lib.py#L93-L101] แล้ว logic เดียวกันใน MAIN → ใช้กับ R2/R3/R4/R5/GB-17/18 ของ MAIN ด้วย (ดู METHODOLOGICAL_RISKS R-08) |
