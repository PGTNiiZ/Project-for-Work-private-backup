# Experimental Master Plan — Research V2 (ฉบับภาษาไทย, v2 reconciled)

## Changes vs v1

| # | การเปลี่ยนแปลง | หลักฐาน / เหตุผล |
|---|---|---|
| M1 | **E2-2 RETIRED → รวมเข้า E6-1**: R0 ไม่ใช่ lexical rule formula แต่เป็น threshold 0.98/0.95 บน score ของโมเดล multimodal 41 features; rule มือของ stage18 เป็น policy 4 ยีน → อยู่ใน T6 | [MAIN@1e0a2db:train_data/stage15_crm_entity_pipeline/run_crm_entity_pipeline.py#L117-L127, #L408-L409]; [MAIN@1e0a2db:exp_r1_ga_redecision.py#L18 STAGE18_MANUAL] |
| M2 | **E5-2 เป็น ALIAS ของ E4-2** (ไม่ใช่ experiment แยก) — แก้ความซ้ำ E5-2 ≡ E4-2 | v1 §T5 ระบุ "เท่ากับ E4-2" |
| M3 | **E5-1 เป็น ALIAS ของ E3-2 (GBDT) / E3-1 (LR)** — config เดียวกันทุกประการ (F-LEX, learner, budget, C(B*)) | v1 matrix: E5-1 depends_on E3-1;E3-2 |
| M4 | **E1-1 ระบุได้ครบจาก repo**: exact tier (username ≥3 ตัวอักษร / external URL ตรงกัน) + key blocking (`username_prefix3`, `fullname_prefix3`, `external_domain`) | [MAIN@1e0a2db:train_data/stage7_14_full_candidate_pipeline/run_full_candidate_pipeline.py#L35, #L118-L179] |
| M5 | **Budget ของ H5** = จำนวนคู่รวมเท่ากับ |C_B0| (≈2.09M HIST ทั้งระบบ) + เส้น PC–|C| และ PC@k | key blocking ไม่มี k; [MAIN@1e0a2db:EXPERIMENT_PLAN.md#L26] |
| M6 | **Policy budget 2,000 → 2,048** และ E6-4 เพิ่ม **scrambled Sobol** (baseline ที่ ICSEC v2 ใช้) ร่วมกับ random/TPE | Sobol ต้องการ 2^m จุด; [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/BASELINE_PROTOCOL.md#L5-L12] |
| M7 | **E6-5 policy space = genome 4 ยีนเดิม** (t_m, t_r, c_promote, c_demote; bounds ตามโค้ดเดิม) — ทำให้ E6-5 เป็น replication ของ R1/R3/ICSEC-B3 | [MAIN@1e0a2db:exp_r1_ga_redecision.py#L75-L113] |
| M8 | **E6-3 รวม Chow posterior-risk rule** (three-way closed form) | [BACKUP@903246c:experiments/code/reviewer_revision.py] |
| M9 | **Split protocol ใหม่**: entity-atomic 5 folds ขนาดเท่ากัน (1 fold = test, 4 folds = development แบบ cross-fitting) แทน 70/15/15/30 — แก้ calibration prior shift ที่พบใน ICSEC v2 (calibration prior 5.7% vs test 2.2%) | CONFIRMED_DEFECT ใน `review/METHODOLOGICAL_RISKS.md` R-10; [BACKUP@ab93b36:artifacts/audit/icsec_review_20261010/evidence.json#role_priors] |
| M10 | **Priority labels ใหม่** (ESSENTIAL/SUPPORTING/CONDITIONAL/OPTIONAL/EXCLUDE) แทน core/optional; MVP = ESSENTIAL เท่านั้น (21 experiments รวม D0) | prompt §4; `review/EXPERIMENT_REDUNDANCY_REVIEW.md` |
| M11 | E1-2 → CONDITIONAL; E3-1, E4-2, E5-4, E6-1, E6-6, E7-3…E7-7 → SUPPORTING; E1-6, E4-3, E4-4, E6-8, E9-1, E10-1 → CONDITIONAL | `review/EXPERIMENT_REDUNDANCY_REVIEW.md` |
| M12 | **D0-5 (ใหม่, OPTIONAL)** historical artifact re-analysis; D0-1 ขยายให้ครอบคลุม provenance ของ LinkSocial; D0-4 ครอบคลุม "historical exposure" ของ entity ใน test เดิม | [P38]; test เดิมถูกใช้ ≥15 ครั้ง (`review/HISTORICAL_EXPERIMENT_AUDIT.md` A6) |
| M13 | ข้อมูลภาษาไทยไม่ถูกสันนิษฐานอีกต่อไป; encoder เริ่มต้น = English/multilingual ตาม D0-2 | [P38]; `RESEARCH_GAP_VALIDATION.md` G-4 |
| M14 | ทุก "HIST-UNVERIFIED" ของ R0–R6 ถูกแทนด้วย lifecycle labels + citation | `review/HISTORICAL_EXPERIMENT_AUDIT.md` |
| M15 | §8 MVP และ §9 unknowns เขียนใหม่; เพิ่ม §10 counts, §11 split protocol, §12 per-experiment specification | — |

---


สถานะ: **PROPOSED (v2 reconciled 2026-10-25)** · การทดลองทางวิทยาศาสตร์: **NO-GO** จนกว่า G0–G5 ผ่าน (ดู `RESEARCH_GATES.md`) · แหล่งความจริงเดียวของ ID/จำนวน = `HYPOTHESIS_EXPERIMENT_MATRIX.csv`
เอกสารที่ต้องอ่านคู่กัน: `RESEARCH_QUESTIONS_AND_HYPOTHESES.md`, `HYPOTHESIS_EXPERIMENT_MATRIX.csv`, `EVALUATION_AND_STATISTICS.md`, `EXPERIMENT_DEPENDENCY_GRAPH.md`

---

## 0. หลักการออกแบบ (Design Principles)

1. **แยกผลทีละองค์ประกอบ:** แต่ละการทดลองเปลี่ยนตัวแปรอิสระ *หนึ่ง* มิติ (blocking / representation / learner / policy) และตรึงส่วนที่เหลือที่ "reference configuration"
2. **Reference configuration (REF)** ใช้เป็นจุดยึดของทุก Track:
   - Blocker: B-REF = lexical blocker ที่ดีที่สุดบน validation จาก T1 (คาดว่า E1-2 หรือ E1-3)
   - Features: F-LEX = lexical feature set เต็ม (E2-1)
   - Learner: GBDT (E3-2) และ LR (E3-1) เป็นตัวที่สอง
   - Policy: validation-F1 threshold (E6-2) สำหรับ T1–T5; T6 เป็นที่เดียวที่เปลี่ยน policy
   - Pipeline stages แยกเด็ดขาด 5 ขั้น: S1 candidate generation (T1) · S2 feature representation (T2 E2-1, T4 E4-1, T5) · S3 classifier (T2 E2-3, T3) · S4 decision policy (T6) · S5 entity-level (T10) — การดีขึ้นที่ขั้นหนึ่งไม่ใช่การดีขึ้นของทั้ง pipeline จนกว่าจะวัดใน T7
3. **Compact matrix (v2):** 7 core Tracks + D0; **41 distinct experiments + 5 diagnostics = 46 distinct IDs**; 2 alias IDs (E5-1, E5-2) และ 1 retired (E2-2) — นับจาก `HYPOTHESIS_EXPERIMENT_MATRIX.csv` (ดู §10)
4. **Test lock:** test ถูกเปิดครั้งเดียวต่อ configuration ที่ประกาศใน G4; การเลือกทุกอย่างทำบน train/validation (grouped CV)
5. **ป้ายสถานะ:** ทุก variant ติด PROPOSED; ผลประวัติ R0–R6/ICSEC ติด lifecycle label (V-REPO) และยังใช้เป็น *สมมติฐานตั้งต้น* เท่านั้น — ห้ามใช้ยืนยัน/ปฏิเสธ H ใด

## 0.1 สรุปจำนวน

| Track | Core variants | Optional | ต้อง train? | Hypothesis |
|---|---|---|---|---|
| D0 Diagnostics | 4 (D0-1…D0-4) | – | ไม่ | DQ0–DQ3 |
| T1 Blocking | 5 (E1-1…E1-5) | 1 (E1-6) | ไม่ (E1-6 ใช่) | H5 |
| T2 Lexical | 3 (E2-1…E2-3) | 1 (E2-4) | ไม่ (fit พารามิเตอร์ rule บน validation) | H1, H2 |
| T3 Classical ML | 2 (E3-1, E3-2) | 1 (E3-3 RF) | ใช่ | H2 |
| T4 Semantic | 2 (E4-1, E4-2) | 3 (E4-3, E4-4, E4-5) | E4-1 ไม่; E4-2 train classifier; E4-3/4 fine-tune | H3 |
| T5 Fusion/Ablation | 5 (E5-1…E5-5) | 1 (E5-6) | ใช่ (classifier) | H1, H3 |
| T6 Decision | 6 (E6-1…E6-6) + E6-7 calibration (precondition) | 1 (E6-8 one-to-one) | ไม่ train base model; optimize policy | H4 |
| T7 End-to-end | 7 (E7-1…E7-7) | – | ไม่ (ใช้โมเดลจาก T1–T6) | H1–H5, DQ4–DQ6 |
| T8–T10 | – | 5 | ขึ้นกับ variant | extension |

---

## 1. Diagnostics D0 (บังคับก่อนทุก Track)

| ID | สิ่งที่ทำ | Output | Gate ที่ปลดล็อก |
|---|---|---|---|
| D0-1 | Label provenance audit: แหล่งที่มา ผู้สร้าง เกณฑ์ เครื่องมือ วันที่; สุ่ม ≥ 200 positive ให้ผู้ตรวจ 2 คนตรวจซ้ำอิสระ; คำนวณ Cohen's κ | `label_audit.md`, κ, อัตราผิดของ positive | G0, G2 |
| D0-2 | Dataset profile: จำนวนบัญชี/identity ต่อแพลตฟอร์ม, missingness ต่อ attribute, ภาษา (ไทย/อังกฤษ/ผสม), ความยาว bio, ความสัมพันธ์ 1:1 หรือ 1:n | data dictionary + datasheet [P33] | G2 |
| D0-3 | Negative uncertainty audit: สุ่มคู่ที่ "ไม่มี label" แต่ lexical similarity สูง (top-decile) ≥ 200 คู่ ให้ตรวจด้วยมือ เพื่อประมาณสัดส่วน hidden positives | ค่าประมาณ π_hidden พร้อม CI | G2, E7-6 |
| D0-4 | Leakage audit: identity ที่ข้าม split, บัญชีซ้ำ, feature ที่อาจรั่ว (เช่น ID ภายใน, timestamp การสร้าง label) [P20] | `leakage_report.md` | G3 |

> D0 ไม่ใช่การทดลองทางวิทยาศาสตร์ แต่ **ต้องได้รับ data-use authorization (G1) ก่อน** เพราะต้องเปิดดูข้อมูลส่วนบุคคล

---

## T1 — Candidate Generation และ Blocking

1. **แรงจูงใจทางวิทยาศาสตร์:** การเปรียบเทียบทุกคู่ระหว่างสองแพลตฟอร์มมีความซับซ้อนกำลังสอง; blocking กำหนด *เพดาน* ของ end-to-end recall — คู่ที่ไม่เข้า candidate set ไม่มีทางถูกจับคู่ได้ R6 เดิม (HIST-UNVERIFIED) รายงานข้อจำกัดในการกู้คู่ที่ blocking พลาด จึงต้องวัดอย่างเป็นระบบ
2. **Literature:** P12 (taxonomy, PC/PQ/RR), P10/P11 (supervised meta-blocking), P13 (DL blocking ไม่ต้อง label; DL+non-DL ดีกว่า), P14 (kNN บน embedding และต้นทุน vectorization), P07 (end-to-end vs candidate-level)
3. **Hypothesis:** H5 (primary); ให้ candidate set แก่ทุก Track ถัดไป
4. **Variants:**
   - **E1-1 Historical B0 replica** — exact tier: username ตรงกัน (≥3 ตัวอักษร) หรือ external URL ตรงกัน → AUTO_EXACT; key blocking: `username_prefix3`, `fullname_prefix3`, `external_domain` (ตัด generic domain) [MAIN@1e0a2db:train_data/stage7_14_full_candidate_pipeline/run_full_candidate_pipeline.py#L35, #L118-L179] — PC ประวัติศาสตร์ 0.8867 (HIST, ARTIFACT_CONSISTENT ระหว่าง MAIN plan และ BACKUP preflight)
   - **E1-2 Token blocking + block purging** (schema-agnostic) [P12] — CONDITIONAL
   - **E1-3 Sparse retrieval:** TF-IDF character 3–4-gram, cosine top-k (baseline ที่แข็งแรงตาม [P45])
   - **E1-4 Dense retrieval:** frozen sentence encoder (multilingual MiniLM ถ้ามีภาษาไทย) + exact/HNSW kNN top-k [P13, P14, P15]
   - **E1-5 Hybrid:** union ของ E1-3 และ E1-4 ที่ budget รวม k (แบ่ง k/2 + k/2) และ reciprocal rank fusion — เลือกหนึ่งแบบบน validation
   - *E1-6 (optional) Supervised meta-blocking แบบ GSM* — ต้องใช้ label, ทำเฉพาะเมื่อ E1-5 ยังมี PC ต่ำกว่าเป้า
5. **ตัวแปร:** IV = วิธี blocking, budget k ∈ {1, 5, 10, 20, 50} **และ budget รวมที่เท่ากับ |C_B0|** (primary ของ H5); DV = PC@|C_B0|, PC@k, RR, PQ, จำนวน B0-missed positives ที่กู้คืน, เวลา build/query, หน่วยความจำ
6. **Controls/Baselines:** E1-1 (historical replica) และ "oracle upper bound" = PC = 1 (all pairs, คำนวณเฉพาะบน sample ถ้าใหญ่เกิน); normalization เดียวกันทุกวิธี; k เท่ากัน
7. **ข้อมูล/label:** ต้องรู้ positive *ทั้งหมด* ใน split — repo ยืนยันว่า GT (`user_folder`) มาจาก folder ของ dataset ต้นทาง LinkSocial ไม่ได้มาจาก blocking ของระบบ [BACKUP@ab93b36:src/identity_resolution/stages/prepare.py#L28-L69] จึงไม่มี selection bias เชิงโครงสร้างต่อ PC; แต่ถ้า LinkSocial สร้าง GT จาก cross-link ที่ผู้ใช้ประกาศ exact URL/username tier อาจเป็น label proxy (UNKNOWN → D0-1)
8. **Training:** ไม่ต้องสำหรับ E1-1…E1-5 (encoder frozen, TF-IDF fit บน train เท่านั้น); E1-6 ต้อง train
9. **โมเดล/config:** TF-IDF (char_wb, n=3–4, min_df=2); encoder: `paraphrase-multilingual-MiniLM-L12-v2` หรือ `all-MiniLM-L6-v2` (เลือกตาม D0-2 ภาษา) — ระบุ revision hash; FAISS IndexFlatIP (exact) เป็นค่าตั้งต้น, HNSW เฉพาะเมื่อ N ใหญ่
10. **Metrics:** primary = PC@k* ; secondary = PC–|C| curve AUC, RR, PQ, recovery rate = |missed_by_best_lexical ∩ found_by_X| / |missed_by_best_lexical|, latency
11. **สถิติ:** paired entity-grouped bootstrap บน ΔPC@k*; McNemar ระดับคู่จริง (found/not found) เป็นการทดสอบรอง
12. **Compute:** ไม่ต้อง GPU (encoder เล็กรันบน CPU ได้); ดู `COMPUTE_AND_COST_PLAN.md`
13. **Failure modes:** ground truth สร้างจาก blocking เดิม (ทำให้ไม่เป็นธรรม); hub accounts ที่โผล่ใน top-k ของทุกคน; ชื่อสั้นมาก/ซ้ำบ่อย; dense retrieval ไม่เข้าใจการถอดเสียงไทย
14. **เกณฑ์เข้าวิทยานิพนธ์หลัก:** E1-1…E1-5 เข้าเสมอ (ต้นทุนต่ำ, จำเป็นต่อ H5 และ end-to-end); E1-6 เข้าเฉพาะเมื่อ best PC@k* < 0.90
15. **งานเก่าที่ใช้ซ้ำ/ต้อง revalidate:** B0 code → REUSE_AFTER_VERIFICATION (E1-1); R6 hash blocking (RESULT_ARTIFACT_FOUND, ARTIFACT_CONSISTENT: 4/3,316 ที่ radius 1) → REFERENCE_ONLY; bigram index (F02) → แนวคิดของ E1-3

---

## T2 — Lexical Representation และ Rule-based Matching

1. **แรงจูงใจ:** lexical similarity เป็น baseline ที่ถูก โปร่งใส และเป็นฐานของ R0/R1 เดิม; ต้องรู้ว่า attribute ใดให้สัญญาณ ก่อนจะอ้างว่าโมเดลซับซ้อนช่วย
2. **Literature:** P17 (similarity functions), P16 (Fellegi–Sunter), P02/P03 (UIL features, username behaviour), P01
3. **Hypothesis:** H1 (สัญญาณต่อ attribute), H2 (เป็น rule-based baseline)
4. **Variants:**
   - **E2-1 Per-attribute similarity profile:** สำหรับแต่ละกลุ่ม attribute (username, display name, bio, URL/ลิงก์, location ฯลฯ ตาม D0-2) คำนวณ exact, Jaro–Winkler, normalized Levenshtein, token Jaccard, char-3gram TF-IDF cosine + missing indicator → เป็น F-LEX; รายงาน univariate PR-AUC ต่อ feature (ไม่มีการ train)
   - ~~E2-2 Historical rule replica~~ — **RETIRED** (ย้ายไป E6-1): repo แสดงว่า R0 คือ threshold 0.98/0.95 บน score ของโมเดล ไม่ใช่สูตร lexical
   - **E2-3 Tuned rule:** weighted sum ของ F-LEX โดยน้ำหนัก ∈ simplex และ threshold ถูกค้นด้วย random search บน validation ที่ budget เท่ากับ hyperparameter search ของ T3
   - *E2-4 (optional) Fellegi–Sunter แบบ unsupervised EM* — baseline เชิงทฤษฎีที่ไม่ใช้ label
5. **ตัวแปร:** IV = similarity function / rule; DV = PR-AUC, F1, P, R ที่ threshold policy เดียวกัน
6. **Controls:** candidate set = C(k*) จาก B-REF; normalization (lowercase, NFKC, strip emoji/diacritics option) ตรึงที่ G4
7. **ข้อมูล:** label train/val สำหรับ tuning ของ E2-3; E2-1 ใช้ train เท่านั้นในการ fit TF-IDF vocabulary
8. **Training:** ไม่มี supervised model; E2-3 คือการ optimize พารามิเตอร์บน validation (นับเป็น "selection" ต้องอยู่ใน protocol)
9. **Config:** `rapidfuzz`/`jellyfish` สำหรับ string metrics; random search 200 configs (เท่ากับ T3; ค่า budget กลาง B_search = 200)
10. **Metrics:** primary = PR-AUC; secondary = F1@validation-threshold, Recall@P≥P_target
11. **สถิติ:** paired grouped bootstrap
12. **Compute:** CPU, นาทีถึงชั่วโมงขึ้นกับ |C|
13. **Failure modes:** feature หลายตัวซ้ำซ้อนกัน (collinear); การทำ normalization ทำลายสัญญาณ (เช่น ตัด emoji ที่เป็นเอกลักษณ์); script ไทยไม่ถูก tokenize
14. **เกณฑ์เข้า:** E2-1, E2-3 ESSENTIAL; E2-4 OPTIONAL
15. **งานเก่า:** รายการ 17 hand features ได้จาก repo แล้ว: username_{jaro, lev_sim, token_sort}, fullname_{jaro, lev_sim, token_sort}, name_sim, bio_{jaccard, len_ratio}, both_have_bio, location_{jaro, exact}, both_have_location, same_platform, username_len_diff, fullname_wordcount_diff, username_prefix3_match [MAIN@1e0a2db:exp_r2_bert_feature.py#L53-L61] → map เข้า F-LEX; **ห้ามใช้ `name_sim` แบบ gated ของ cache เดิม** (CONFIRMED_DEFECT: เป็นศูนย์เมื่อ score ของโมเดลเดิม < 0.5) [MAIN@1e0a2db:exp_lib.py#L93-L101]; `same_platform` เป็นค่าคงที่ 0 (ตัดออก); feature 41 ตัวของ production model (F06) เป็นแหล่งเพิ่มเติมสำหรับ url/domain/mention

---

## T3 — Classical Machine Learning

1. **แรงจูงใจ:** แยกผลของ "การเรียนรู้น้ำหนัก/ปฏิสัมพันธ์ของ feature" ออกจาก feature engineering (H2)
2. **Literature:** P10 (probabilistic classifier ใน pipeline ER), P17, P21 (selection bias), P26 (calibration)
3. **Hypothesis:** H2 (primary), ให้ score แก่ T5–T7
4. **Variants:**
   - **E3-1 Logistic Regression** (L2, class_weight balanced vs none เลือกบน validation; feature standardized)
   - **E3-2 Gradient Boosted Trees** (LightGBM หรือ scikit-learn HistGradientBoosting; รองรับ NaN โดยตรง)
   - *E3-3 (optional) Random Forest* — ทำเฉพาะเมื่อ E3-1 กับ E3-2 ต่างกันมาก เพื่อดูว่าเป็นผลของ non-linearity หรือไม่
5. **ตัวแปร:** IV = learner; DV = PR-AUC, F1, Brier score, training/inference time
6. **Controls:** F-LEX เดียวกับ E2-3, C(k*) เดียวกัน, tuning budget เท่ากัน (B_search = 200 configs, TPE); ablation ใน T5 ใช้ hyperparameter ที่ tune บน E5-3 แล้วตรึงไว้, 5 seeds สำหรับ GBDT
7. **ข้อมูล:** train/val/test แบบ entity-disjoint (GroupKFold โดย group = identity cluster); negative sampling = ใช้ candidate set ตามธรรมชาติ ไม่ undersample ใน validation/test
8. **Training:** **ต้อง train ใหม่ทั้งหมด** — โมเดลประวัติศาสตร์ (GB เดิม) ใช้ไม่ได้เพราะ split/label ไม่ผ่านการตรวจ
9. **Config:** GBDT: num_leaves {15,31,63}, learning_rate {0.03,0.1}, n_estimators early stopping บน inner validation, min_child_samples {20,50}; LR: C ∈ logspace(−3,2)
10. **Metrics:** primary = PR-AUC; secondary = F1 ที่ policy E6-2, Brier, ECE, ms/1k คู่
11. **สถิติ:** paired grouped bootstrap; seed variance ต้องเล็กกว่า |effect|/2 จึงจะตีความได้
12. **Compute:** CPU นาที/โมเดล (ขึ้นกับ |C|)
13. **Failure modes:** overfit กับ identity ที่มีหลายบัญชี; imbalance ทำให้ LR เอนเอียง; feature leakage
14. **เกณฑ์เข้า:** E3-2 ESSENTIAL (= E5-1); E3-1 SUPPORTING
15. **งานเก่า:** "GB" ประวัติ — ใช้เป็นแหล่ง hyperparameter เริ่มต้นได้ (HIST-UNVERIFIED) แต่ต้อง train ใหม่

---

## T4 — Semantic Representation

1. **แรงจูงใจ:** ข้อความใน bio/display name อาจเหมือนกันเชิงความหมายแต่ต่างตัวอักษร (ภาษา/การถอดเสียง/คำพ้อง); R2/R3 เดิมเพิ่ม semantic cosine เป็น feature ที่ 18 (HIST-UNVERIFIED)
2. **Literature:** P15 (SBERT), P04 (Ditto), P05/P06, P14 (ต้นทุน/คุณภาพ embedding), P08 (heterogeneity), P09 (LLM)
3. **Hypothesis:** H3, H3a, H3b
4. **Variants:**
   - **E4-1 Frozen bi-encoder cosine** ต่อ attribute ข้อความ (display name, bio) → semantic feature set F-SEM (ไม่มีการ train)
   - **E4-2 Semantic-only classifier:** GBDT/LR บน F-SEM อย่างเดียว (train classifier เท่านั้น)
   - *E4-3 (conditional) Fine-tuned bi-encoder* ด้วย contrastive loss บน train positives + hard negatives จาก C(k)
   - *E4-4 (conditional) Fine-tuned cross-encoder (Ditto-style)* บน serialized profile pair
   - *E4-5 (optional, BLOCKED by default) LLM zero/few-shot* — อนุญาตเฉพาะโมเดลที่รันภายในเครื่อง และผ่าน G1
5. **ตัวแปร:** IV = representation (frozen / fine-tuned / cross-encoder); DV = PR-AUC, ΔFN recovered, ms/คู่, GPU-hours
6. **Controls:** C(k*) เดียวกัน; classifier เดียวกันเมื่อเทียบ feature set; encoder revision ตรึง; serialization template ตรึงที่ G4
7. **ข้อมูล:** ต้องรู้ภาษาของ attribute (D0-2); E4-3/E4-4 ต้องมี positive ใน train ≥ ~1,000 คู่ (เกณฑ์เสนอ) มิฉะนั้นไม่ทำ
8. **Training:** E4-1 ไม่; E4-2 train classifier; E4-3/E4-4 fine-tune (GPU)
9. **Config:** E4-1: multilingual MiniLM (384-d), mean pooling, max_len 128; E4-4: base encoder ขนาดเล็ก (MiniLM/XLM-R base ถ้าภาษาไทยมาก), lr 2e-5, 3 epochs, batch 32, early stopping บน validation, 3 seeds
10. **Metrics:** primary = PR-AUC; secondary = FN recovered vs E5-1, ms/คู่, GPU-h, ผลแยก stratum ภาษา
11. **สถิติ:** paired grouped bootstrap; H3a ใช้ difference-in-differences ระหว่าง strata
12. **Compute:** E4-1 CPU ได้; E4-3/E4-4 GPU (ดู compute plan)
13. **Failure modes:** encoder ไม่รองรับภาษาไทย/ชื่อเฉพาะ; bio ว่างจำนวนมาก (semantic ไม่มีข้อมูล); fine-tune overfit กับ identity; cosine ของข้อความ boilerplate ("official account") สูงผิดปกติ
14. **เกณฑ์เข้า:** E4-1, E4-2 เข้าเสมอ; **E4-3/E4-4 เข้าเฉพาะเมื่อ** (a) H3 ด้วย frozen ให้ Δ > 0 อย่างมีนัย หรือ (b) error analysis แสดงว่า FN ส่วนใหญ่เป็นแบบ semantic **และ** มีข้อมูลฝึกพอ
15. **งานเก่า:** MiniLM, BERT (R2/R3/R6) → ใช้ชื่อโมเดลและ preprocessing เป็นจุดเริ่มต้น; ต้อง revalidate ทุกผล

---

## T5 — Multi-feature Fusion และ Ablation

1. **แรงจูงใจ:** ทดสอบ H1 และ H3 โดยตรงด้วยการเปลี่ยน *feature set* ขณะตรึง learner
2. **Literature:** P01/P02 (หลาย attribute), P13 (การรวม DL + non-DL), P07
3. **Hypothesis:** H1, H3
4. **Variants (ทุกตัวรันกับทั้ง LR และ GBDT):**
   - **E5-1 Lexical-only** (F-LEX) — **ALIAS ของ E3-2/E3-1** (ไม่ train ซ้ำ)
   - **E5-2 Semantic-only** (F-SEM) — **ALIAS ของ E4-2**
   - **E5-3 Lexical + Semantic** (F-LEX ∪ F-SEM)
   - **E5-4 Leave-one-attribute-group-out** จาก E5-3 (หนึ่ง run ต่อกลุ่ม attribute)
   - **E5-5 Single-attribute-group models** (lexical เท่านั้น) — 5 กลุ่ม: G_user, G_name (fullname + cross name), G_bio, G_loc, G_link (url/domain/mention)
   - *E5-6 (optional) Missingness-aware fusion:* missing indicators + native NaN vs mean imputation
5. **ตัวแปร:** IV = feature set; DV = PR-AUC, Recall@P_target
6. **Controls:** learner, hyperparameter search budget, C(k*), seeds เหมือนกัน
7. **ข้อมูล:** เหมือน T3 + stratum missingness จาก D0-2
8. **Training:** ต้อง (classifier ต่อ feature set)
9. **Config:** เหมือน T3
10. **Metrics:** primary = PR-AUC; secondary = ΔFN/ΔFP per stratum, permutation importance (diagnostic เท่านั้น ไม่ใช่ hypothesis test)
11. **สถิติ:** paired grouped bootstrap; ablation ทุกตัวรายงาน CI แต่ **ไม่** ปรับ multiplicity เข้ากลุ่ม confirmatory (เป็น explanatory)
12. **Compute:** CPU; จำนวน training jobs ดู §10 (n_groups = 5)
13. **Failure modes:** attribute ที่หายมากทำให้ ablation ตีความผิด; correlated features ทำให้ leave-one-out ประเมินความสำคัญต่ำ
14. **เกณฑ์เข้า:** E5-1, E5-3, E5-4, E5-5 เข้าเสมอ; E5-2 เข้าเพราะใช้ร่วม T4
15. **งานเก่า:** "feature-aware experiments" (HIST-UNVERIFIED) → ใช้เป็นสมมติฐานว่ากลุ่มใดน่าจะสำคัญ

---

## T6 — Decision Policy Optimization

1. **แรงจูงใจ:** แยกคำถาม "ตัดสินใจอย่างไรจาก score" ออกจาก "สร้าง score อย่างไร"; GA ของ R1/R3/R5 (HIST-UNVERIFIED) ไม่มี baseline ที่ optimize แบบ non-GA ตามสรุปที่ได้รับ
2. **Literature:** P24 (cost-optimal threshold), P25 (reject option), P26 (calibration), P16 (possible-match zone), P18 (F-measure weakness), P28 (three-way decision ใน UIL)
3. **Hypothesis:** H4a, H4b, H4c
4. **Variants (score = output ของ matcher ที่ถูก freeze จาก T5 ตัวที่เลือกบน validation):**
   - **E6-7 Calibration (precondition):** Platt vs isotonic บน validation fold แยก (calibration fold)
   - **E6-1 Fixed/historical policies** — t = 0.5; R0 (MATCH ≥ 0.98, REVIEW ≥ 0.95); stage18 manual rule [0.98, 0.95, 0.90, 0.70] (รับ E2-2 เดิม)
   - **E6-2 Validation-F1-optimal threshold**
   - **E6-3 Closed-form cost-optimal threshold** t* = c_FP / (c_FP + c_FN) บน calibrated probability + **Chow posterior-risk three-way rule** argmin[c_FN·p, c_R, c_FP·(1−p)]
   - **E6-4 Non-GA search baseline:** random search + scrambled Sobol + TPE บน policy space เดียวกับ GA
   - **E6-5 GA** บน genome 4 ยีนเดิม [MAIN@1e0a2db:exp_r1_ga_redecision.py#L75-L113], budget objective evaluations เท่ากับ E6-4 (= replication ของ R1/R3 และ ICSEC-v2 B3)
   - **E6-6 Three-way policy:** (t_low, t_high) → non-match / review / match; ค้นด้วยวิธีที่ดีที่สุดระหว่าง E6-3-analytic (Chow) และ E6-4
   - *E6-8 (optional) One-to-one constraint:* greedy/Hungarian assignment หลัง threshold (ถ้า D0-2 ยืนยันว่าเป็น 1:1)
5. **ตัวแปร:** IV = policy/optimizer; DV = expected cost ต่อคู่, false merges/1k, review rate, coverage, P/R/F1
6. **Controls:** score เดียวกัน; policy space เดียวกัน (เช่น 1 threshold, 2 thresholds, หรือ threshold + per-platform offset); **budget = 2,048 objective evaluations** สำหรับ E6-4 และ E6-5 (นับ evaluation จริงรวม duplicate และรายงาน unique); optimize บน OOF scores ของ development folds เท่านั้น; GA, random, Sobol (scramble seed) และ TPE รัน 10 seeds
7. **ข้อมูล:** validation ที่ใหญ่พอให้ประมาณ threshold เสถียร (เสนอ ≥ 200 positives); cost model จากเจ้าของโจทย์ (**UNKNOWN** → ใช้ค่าตั้งต้น + sensitivity)
8. **Training:** ไม่ train base model ใหม่; มีเพียง calibration (fit 1–2 พารามิเตอร์) และ policy search
9. **Config GA (เสนอ, ใกล้เคียงของเดิม):** population 64 × 32 generations = 2,048 evaluations, elite 12, uniform crossover, Gaussian mutation σ = 0.02 p = 0.30 (ค่าเดิม pop 60 × gen 40 ≈ 1,980 genome ใหม่) — ตั้งค่าที่ G4 และ **ห้ามปรับหลังเห็น validation result ของ E6-4**
10. **Metrics:** primary = expected cost ต่อคู่ (ตาม cost model ที่ freeze); secondary = false merges/1k, review rate, F1, seed SD
11. **สถิติ:** paired grouped bootstrap บน Δcost; ความแปรปรวนข้าม seed ของ optimizer รายงานแยก
12. **Compute:** ต่ำมาก (policy evaluation บน vector ของ score)
13. **Failure modes:** overfit threshold กับ validation เล็ก; cost model ที่ไม่สะท้อนการใช้งานจริง; GA ได้เปรียบจาก budget มากกว่า (ต้องคุม)
14. **เกณฑ์เข้า:** E6-1…E6-7 เข้าเสมอ (ต้นทุนต่ำ, ตอบ H4 ตรง); E6-8 เข้าเมื่อ 1:1 ยืนยัน
15. **งานเก่า:** โค้ด GA ตรวจแล้วว่ารับเฉพาะข้อมูลที่ผู้เรียกส่ง (validation) [MAIN@1e0a2db:exp_r1_ga_redecision.py#L1-L5, #L130-L156] → REUSE_AFTER_VERIFICATION; ICSEC v2 มี sealed-label store/budget audit ที่ใช้ซ้ำได้ [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/real_adapters.py#L102-L135]; ผลประวัติศาสตร์: GA ≈ Sobol (U 1858.2 vs 1860.0), tuned two-threshold 1864.6, Chow 1879.0, fixed 2364.2 (ARTIFACT_CONSISTENT, 3 partitions, ไม่มี CI)

---

## T7 — End-to-End Evaluation, Robustness และ Cost

1. **แรงจูงใจ:** ผล candidate-level ไม่เท่ากับผลระบบจริง [P07]; ต้องบอกได้ว่าแต่ละ stage มีส่วนเท่าไร และระบบทนต่อความแตกต่างของข้อมูลแค่ไหน [P08]
2. **Literature:** P07, P08, P18, P23, P22, P27
3. **Hypothesis:** H1–H5 (ยืนยันระดับระบบ), DQ4–DQ6
4. **Variants:**
   - **E7-1 End-to-end evaluation** ของ configuration ที่ประกาศล่วงหน้า (REF และ BEST-VAL) บน locked test: end-to-end P/R/F1, cost, PR-AUC เทียบ all positives
   - **E7-2 Stage attribution (2×2×2 factorial):** Blocker {B0=E1-1, B*=best} × Matcher {E2-3 rule, E3-2/E5-3 learned} × Policy {E6-1, best-of-T6} = 8 cells บน validation (ทั้งหมด) และบน test (เฉพาะ 8 cells ที่ประกาศ) → main effects และ interactions
   - **E7-3 Robustness strata:** แยกผลตาม platform pair, missingness pattern, ภาษา/ถอดเสียง, ความยาว bio, ความนิยมของชื่อ (name frequency) + perturbation test (case, emoji, transliteration, truncation)
   - **E7-4 Prior sensitivity:** precision/expected cost ที่ class prior ต่าง ๆ (natural prior ของ C(k), ×0.5, ×0.1) ผ่านการ reweight และรายงาน PR curve
   - **E7-5 Compute & inference cost:** เวลา build index, ms/1k คู่ ของแต่ละ stage, peak RAM/VRAM, training time, ขนาดโมเดล
   - **E7-6 Label-uncertainty sensitivity:** ประเมินภายใต้ (a) unlabeled = negative (b) unlabeled excluded (c) ปรับด้วย π_hidden จาก D0-3 → ช่วง precision
   - **E7-7 Error analysis:** taxonomy ของ FN/FP (ชื่อซ้ำทั่วไป, impersonation, บัญชีองค์กร, ข้อมูลว่าง, ต่างภาษา) บน validation; บน test เฉพาะการนับตาม taxonomy ที่ freeze แล้ว
5. **ตัวแปร:** IV = configuration / stratum / prior / label assumption; DV = end-to-end metrics, cost, latency
6. **Controls:** configuration ทั้งหมดถูกเลือกก่อนเปิด test; ไม่มีการ retune หลังเปิด
7. **ข้อมูล:** locked test ที่ entity-disjoint; ควรมี **out-of-time หรือ out-of-collection holdout** ถ้าข้อมูลเดิมเคยถูกใช้ในงานประวัติศาสตร์ (ดู G5)
8. **Training:** ไม่มี (ใช้โมเดลที่ freeze)
9. **Config:** ตาม T1–T6
10. **Metrics:** primary = end-to-end Recall ที่ Precision ≥ P_target และ expected cost; secondary = F1, PR-AUC (all positives), latency
11. **สถิติ:** grouped bootstrap, Holm สำหรับ 5 primary contrasts, TOST สำหรับข้อสรุป "ไม่ต่าง"
12. **Compute:** ต่ำ–กลาง (inference เท่านั้น)
13. **Failure modes:** strata เล็กเกิน (CI กว้าง → รายงานเป็น exploratory); test ถูกใช้ซ้ำโดยไม่ตั้งใจ
14. **เกณฑ์เข้า:** E7-1, E7-2, E7-4, E7-5, E7-6 เข้าเสมอ; E7-3, E7-7 เข้าเสมอแต่ส่วน strata เล็กเป็น exploratory
15. **งานเก่า:** harness end-to-end ของ `exp_lib.evaluate` (นับ blocking-missed เป็น FN) → REUSE_AFTER_VERIFICATION แต่ต้องเพิ่ม end-to-end recall ที่นับ positive REVIEW (M1 ของ reviewer revision); ผล R0–R6/ICSEC → ภาคผนวก historical table พร้อม lifecycle label

---

## T8–T10 — Optional Extensions (ประเมินแยก ไม่บังคับ)

| Track | Variants | เงื่อนไขเริ่ม (ต้องครบทุกข้อ) | เกณฑ์เข้าวิทยานิพนธ์ | Literature |
|---|---|---|---|---|
| **T8 Privacy-preserving** | E8-1 Bloom-encoded similarity vs plaintext (replica R4) · E8-2 + best policy จาก T6 (replica R5) · **E8-3 attack evaluation**: frequency/pattern-mining attack จำลองบนข้อมูลของเรา → re-identification rate | threat model เป็นลายลักษณ์อักษร; ethics อนุมัติการทดลองโจมตี; G1 | ต้องมี E8-3 เสมอ — ห้ามรายงาน E8-1/E8-2 โดยไม่มี E8-3 แล้วอ้างว่า "privacy-preserving" | P29, P30, P31, P32, P35 |
| **T9 Multimodal** | E9-1 profile image similarity (perceptual hash / image embedding) เป็น feature เพิ่มเข้า E5-3 | สิทธิ์ใช้ภาพชัดเจน; coverage ภาพ ≥ 50% ของคู่; การจัดการ biometric data ผ่าน G1 | ΔPR-AUC > SESOI บน validation และไม่มีปัญหากฎหมาย | P07 |
| **T10 Entity-level** | E10-1 connected components vs correlation-clustering จาก pairwise decisions; metrics: B-cubed P/R, cluster F1, จำนวน transitivity violations | ground truth ระดับ identity ที่เชื่อถือได้ (D0-1); มีกรณี 1:n จริง | เข้าเมื่อ D0-2 พบว่า >5% ของ identity มีหลายบัญชีต่อแพลตฟอร์ม | P28, P16 |

E4-5 (LLM) และ E1-6 (supervised meta-blocking) จัดเป็น optional ด้วย

---

## 8. Minimum Viable Scientific Program (MVP = ESSENTIAL เท่านั้น)

ตอบ RQ1–RQ5 (H1–H5 primary contrasts C1–C5) ด้วยจำนวน run น้อยที่สุด — **21 experiments** (4 diagnostics + 17):

1. D0-1, D0-2, D0-3, D0-4 (หลัง G0/G1)
2. S1: E1-1 (B0 replica), E1-3 (sparse), E1-4 (dense), E1-5 (hybrid) → เลือก B* บน development
3. S2/S3: E2-1 (F-LEX), E2-3 (tuned rule), E3-2 (GBDT = E5-1), E4-1 (F-SEM), E5-3 (lex+sem), E5-5 (single group)
4. S4: E6-7 (calibration), E6-2, E6-3 (+Chow), E6-4 (random/Sobol/TPE), E6-5 (GA)
5. End-to-end: E7-1, E7-2

Primary contrasts: C1 H1 = E5-1 vs best E5-5 · C2 H2 = E3-2 vs E2-3 · C3 H3 = E5-3 vs E5-1 · C4 H4b = E6-5 vs best{E6-2, E6-3, E6-4} · C5 H5 = E1-5 vs best{E1-1, E1-3} ที่ |C_B0| — ไม่มี GPU

## 8.1 Advanced program

- **SUPPORTING (11 IDs: 10 experiments + alias E5-2):** E3-1, E4-2 (=E5-2), E5-4, E6-1, E6-6, E7-3, E7-4, E7-5, E7-6, E7-7 — ควรทำถ้าเวลาพอ เพราะให้คำอธิบาย/ความทนทาน (ไม่เข้า Holm)
- **CONDITIONAL (7):** E1-2, E1-6 (ถ้า best PC < 0.90 — ค่า B0 ประวัติศาสตร์ 0.8867 ชี้ว่าเงื่อนไขอาจเกิด), E4-3, E4-4 (GPU; inclusion rule T4), E6-8 (ถ้า 1:1 ยืนยัน), E9-1 (GX-T9 + coverage), E10-1 (ถ้า 1:n > 5%)
- **OPTIONAL (8):** D0-5, E2-4, E3-3, E4-5, E5-6, E8-1, E8-2, E8-3
- **EXCLUDE (1):** E2-2 (retired)

## 9. สิ่งที่ต้องยืนยันก่อน freeze แผน (UNKNOWN / BLOCKED)

| รายการ | สถานะ v2 | หลักฐาน |
|---|---|---|
| ขนาดข้อมูล/แพลตฟอร์ม/attribute | **RESOLVED (V-REPO, schema)**: 36,807 โปรไฟล์, 3 แพลตฟอร์ม, 21 columns, 15,297 entities | `review/REPOSITORY_RESEARCH_INVENTORY.md` §5 |
| ที่มาของ ground truth | **PARTIAL**: LinkSocial [P38]; วิธีสร้าง label ของ LinkSocial UNKNOWN; gitlink `fe67dd1` ไม่พบใน repo upstream | `review/_work/agentA2/G0_G1_EVIDENCE.md`; `review/_work/agentB/LIT_NOTES.md` §6 |
| รายการ 17/18 features, โค้ด GA, รายละเอียด R6 | **RESOLVED** | `review/HISTORICAL_EXPERIMENT_AUDIT.md` F08–F11 |
| cost model จริง | **PARTIAL**: crm_derived_v1 (2:1:0.1) มีเอกสารใน repo แต่ยังไม่ถูกลงนามโดยเจ้าของโจทย์ | [BACKUP@ab93b36:docs/reports/2608-update-project2/CRM_COST_MODEL_TH.md] |
| เอกสาร ICSEC | **RESOLVED (V-REPO)** | `review/HISTORICAL_EXPERIMENT_AUDIT.md` F16–F17 |
| data-use authorization (G1) | **BLOCKED — ไม่มีเอกสารใดใน repo**; repo ทั้งสองเป็น PUBLIC และมีข้อมูลส่วนบุคคล | `review/_work/agentA2/G0_G1_EVIDENCE.md`; `review/METHODOLOGICAL_RISKS.md` §P |
| fresh holdout (G5) | **BLOCKED**: ทุก entity เคยอยู่ใน train/test ของงานประวัติศาสตร์ → ต้องมีข้อมูลใหม่ หรือประกาศผลเป็น "retrospectively contaminated" | `review/HISTORICAL_EXPERIMENT_AUDIT.md` A6 |

## 10. จำนวนที่แน่นอน (คำนวณจาก `HYPOTHESIS_EXPERIMENT_MATRIX.csv` ด้วย `review/_work/scripts/consistency_check.py`)

นิยาม: **distinct experiment** = ID ที่ไม่ใช่ alias/retired · **variant** = configuration ที่ถูกเปรียบเทียบภายใน experiment · **training job** = การ fit โมเดล supervised หนึ่งครั้ง (รวม seed และ cross-fit fold; ไม่รวม hyperparameter search) · **tuning fit** = fit ระหว่าง hyperparameter search (200 configs × 4 folds) · **validation evaluation** = การประเมินบน development (config ของ rule/learner) หรือ objective evaluation ของ policy search · **final test evaluation** = configuration ที่ประกาศล่วงหน้าแล้วถูกประเมินบน test ครั้งเดียว

| ชุด | Distinct experiments | Variants | Training jobs | Tuning fits | Validation evals (model/rule) | Policy objective evals | Final test evals |
|---|---:|---:|---:|---:|---:|---:|---:|
| MVP (ESSENTIAL) | 21 (4 D0 + 17) | 49 | 217 | 2,400 | 869 | 82,025 | 19 |
| MVP + SUPPORTING | 31 (4 D0 + 27) | 61 | 414 | 4,800 | 1,500 | 102,508 | 21 |
| ทั้งหมด (รวม CONDITIONAL/OPTIONAL) | 46 (5 D0 + 41) | 92 | 669 | 5,600 | 1,741 | 102,513 | 21 |

- GPU training jobs: 30 (E4-3, E4-4 = 15 + 15; CONDITIONAL) + E4-5 inference (OPTIONAL) — **0 ใน MVP**
- Final test evaluations ของ MVP (19): blocking 3 (E1-1, E1-3, E1-5) · matcher 4 (E2-3, E3-2, E5-3, best E5-5) · policy 4 (E6-2, E6-3, E6-4 best, E6-5 selected) · end-to-end 8 (E7-1: REF, BEST-VAL; E7-2: 6 cells ที่เหลือ) — test fold ถูกเปิด **ครั้งเดียว** โดยประเมินทั้ง 19 configurations พร้อมกันหลัง G5
- ตัวเลข compute ทั้งหมดเป็น ASSUMPTION จนกว่าจะวัดใน smoke test (`COMPUTE_AND_COST_PLAN.md`)

## 11. Split protocol (แก้ไขจาก v1 — ใช้ทุก Track)

1. Group = `user_folder` entity (connected component ถ้า D0-4 พบการเชื่อมข้าม entity); โปรไฟล์ไม่มี entity (3 แถว) = singleton
2. **Entity-atomic 5 folds ขนาดเท่ากัน** (hash ด้วย seed ที่ freeze ที่ G4; สอดคล้องกับ Gate 9 draft ที่เสนอ seed 20261010 [BACKUP@ab93b36:handoff/worktrees/research-phase15-integration/docs/research_rebuild/phase_01_5/gate_09/EXPERIMENT_CONFIG_V1.json]) → fold 5 = **locked test**; folds 1–4 = development
3. Candidate pairs ที่ endpoint อยู่คนละ fold ถูก drop (รายงานสัดส่วน; Gate 5 ประมาณ 604,123 คู่คงอยู่ / 1,482,122 ถูก drop [BACKUP@ab93b36:handoff/worktrees/research-phase15-integration/docs/research_rebuild/phase_01_5/GATE_STATUS_MATRIX.md#L11]) — DESIGN_LIMITATION: precision บน test เป็น within-fold ไม่ใช่ทั้งกราฟ → E7-4 รายงาน prior ของทั้งกราฟ
4. Hyperparameter search: 4-fold grouped CV บน development; **OOF predictions** ของ config ที่เลือก = input ของ calibration (E6-7) และ policy search (T6) — fold ขนาดเท่ากันทำให้ prior ของ calibration ≈ prior ของ test (แก้ CONFIRMED_DEFECT ของ ICSEC v2)
5. Final model = refit บน development ทั้งหมด (ต่อ seed) → ทำนาย test ครั้งเดียว
6. TF-IDF/scaler/imputer fit บนข้อมูล train ของแต่ละ fold เท่านั้น (ห้าม transductive แบบ F05/F06)
7. **Fresh-holdout:** entity ทุกตัวเคยอยู่ใน train/val/test ของงานเดิม → G5 ไม่ผ่านด้วยข้อมูลนี้; ทางเลือก (a) เก็บ/ได้รับข้อมูลใหม่ที่ไม่เคยถูกใช้ (b) ประกาศทุกข้อสรุปเป็น exploratory/retrospectively contaminated ในบทคัดย่อ

## 12. Per-experiment specification (ทุก ID ใน matrix)

ตัวเลข runtime ทั้งหมดเป็น **ASSUMPTION** (ยังไม่ได้วัด) · "ลำดับ" = ขั้นใน `EXPERIMENT_DEPENDENCY_GRAPH.md` §2

| ID | Priority | ลำดับ | Stage | Objective / Proposed | IV | Baseline | Data/GT | Training (GPU) | Primary metric / สถิติ | Runtime | Dependencies | Reusable code | Artifacts | Acceptance | Failure/Exclusion |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D0-1 | ESSENTIAL | 1 | diagnostic | ยืนยันที่มาของ GT (LinkSocial) + κ ของ positive ≥200 คู่ | — | — | สิทธิ์ G1; ผู้ตรวจ 2 คน | No (No) | Cohen kappa; positive error rate; — | ASSUMPTION: 3–5 วันคน | G1 | MAIN@1e0a2db:train_data/stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py#L167-L186 | label_audit.md, κ | κ ≥ 0.80 และกลไกสร้าง GT มีเอกสาร | κ < 0.80 → แก้ label policy ก่อน; ไม่พบกลไก → H ทุกข้อเป็น exploratory |
| D0-2 | ESSENTIAL | 1 | diagnostic | datasheet ต่อแพลตฟอร์ม | — | — | G1 | No (No) | Missingness and language per attribute; — | ASSUMPTION: 1–2 วัน | G1 | — | datasheet.md | missingness/ภาษา/1:n ครบทุก attribute | — |
| D0-3 | ESSENTIAL | 2 | diagnostic | ประมาณ π_hidden จากคู่ similarity สูงที่ไม่มี label | — | — | G1, ผู้ตรวจ | No (No) | Estimated hidden-positive rate pi_hidden with CI; — | ASSUMPTION: 2–3 วันคน | G1;D0-1 | — | pi_hidden.json + CI | CI กว้าง ≤ ±0.05 | ทำไม่ได้ → E7-6 ทำเฉพาะ S1/S2 |
| D0-4 | ESSENTIAL | 2 | diagnostic | ตรวจ leakage/บัญชีซ้ำ/การถูกใช้ใน test เดิม | — | — | split manifest เดิม (md5, icsec-outer, entity_nested_v2) | No (No) | Cross-split identities; leaky features; identities previously used in historical test; — | ASSUMPTION: 1 วัน | D0-2 | MAIN@1e0a2db:exp_lib.py#L166-L221 build_nested_entity_split; MAIN@1e0a2db:train_data/leakage_excluded_features.txt | leakage_report.md | 0 entity ข้าม split; รายการ label-proxy features | พบ leakage → แก้ split ก่อน G3 |
| D0-5 | OPTIONAL | 2 | diagnostic | CI ย้อนหลังของผลประวัติศาสตร์จาก prediction ที่เก็บไว้ | — | — | G1; prediction artifacts | No (No) | Bootstrap CI of historical deltas (R1 vs R3; GB-18 vs GB-18-GA); — | ASSUMPTION: < 1 วัน CPU | G1 | MAIN@1e0a2db:exp_lib.py#L130-L140 evaluate | historical_ci.json | ติดป้าย exploratory/HIST | ไม่ได้ G1 → ข้าม |
| E1-1 | ESSENTIAL | 4 | S1 candidate generation | replicate B0 (exact tier + prefix3/domain keys) ภายใต้ split V2 | Blocking method | B0 (baseline) | positive ทั้งหมดใน fold (รวมที่ blocking พลาด) | No (No) | PC at native |C_B0|; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: นาที CPU | G4 | MAIN@1e0a2db:train_data/stage7_14_full_candidate_pipeline/run_full_candidate_pipeline.py#L118-L179 | candidates_B0.parquet (ภายใน), pc_report.json | PC ภายใน ±0.005 ของ HIST 0.8867 (sanity) | ต่างมาก → หยุดและตรวจ pipeline |
| E1-2 | CONDITIONAL | 4 | S1 candidate generation | token blocking + purging | Blocking method | E1-1 | เหมือน E1-1 | No (No) | PC@|C_B0|; — | ASSUMPTION: นาที | G4 | — | pc_curve.json | ทำเมื่อ E1-3 ไม่ครอบงำ (ตัดสินที่ G4) | — |
| E1-3 | ESSENTIAL | 4 | S1 candidate generation | TF-IDF char n-gram top-k (fit บน D_train) | Blocking method; k | E1-1 | เหมือน E1-1 | No (No) | PC@|C_B0| and PC@k*; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: 5–30 นาที CPU | G4 | MAIN@1e0a2db:bigram_username_and_fullname/bigram_full_pipeline.py#L287-L327 (idea only) | pc_curve.json | PC–|C| รายงานครบ k∈{1,5,10,20,50} | vocab fit ปน test → EXCLUDE run |
| E1-4 | ESSENTIAL | 4 | S1 candidate generation | dense kNN ด้วย frozen encoder ≤2 ตัว | Blocking method; encoder; k | best lexical | เหมือน E1-1 + model revision | No (No (optional)) | PC@k*; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: encode 36.8k ข้อความ ~2–10 นาที CPU | G4;D0-2 | MAIN@1e0a2db:exp_r2_bert_feature.py#L95-L114 encode_profiles | pc_curve.json, index stats | PC–|C| ครบ | — |
| E1-5 | ESSENTIAL | 5 | S1 candidate generation | hybrid union/RRF ที่ budget = |C_B0| | Fusion mode; k | best lexical | เหมือน E1-1 | No (No) | PC@|C_B0| (primary H5); paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: นาที | E1-3;E1-4 | — | pc_curve.json, recovery.json | ΔPC ตาม H5 (CI) | — |
| E1-6 | CONDITIONAL | 11 | S1 candidate generation | supervised meta-blocking (GSM) | Blocking method | E1-5 | label D_train | Yes (No) | PC@|C_B0|; — | ASSUMPTION: ชั่วโมง CPU | E1-5;G3 (run only if best PC < 0.90) | — | pc_curve.json | ทำเมื่อ best PC < 0.90 บน validation | — |
| E2-1 | ESSENTIAL | 5 | S2 feature representation | F-LEX per attribute + univariate PR-AUC | Similarity function per attribute | — | D_train/D_dev | No (No) | Univariate PR-AUC per feature; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: 1–5 นาที CPU (~0.6M คู่ within-fold) | E1-5;E1-1 | MAIN@1e0a2db:exp_r2_bert_feature.py#L53-L61 FEATURE17_COLS; #L146-L265 compute_features17 | features_lex.parquet (ภายใน), feature_report.json | ทุก feature มี unit test; ไม่มี label-proxy ที่ยังไม่ตัดสิน | feature ที่เป็น proxy → รายงานสองแบบ (G2) |
| E2-2 | EXCLUDE | 0 | S4 decision policy | RETIRED → E6-1 | — | — | — | No (No) | —; — | — | — | — | — | — | — |
| E2-3 | ESSENTIAL | 6 | S3 classifier | tuned weighted rule (200 configs) | Rule weights/threshold | rule (baseline H2) | D_dev grouped CV | No (No) | PR-AUC; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: < 1 ชม. CPU | E2-1 | — | rule_config.json | budget = T3 | — |
| E2-4 | OPTIONAL | 11 | S3 classifier | Fellegi–Sunter EM | Probabilistic rule | E2-3 | ไม่ใช้ label ใน fit | No (No) | PR-AUC; — | ASSUMPTION: นาที | E2-1 | — | fs_params.json | — | EM ไม่ลู่เข้า → รายงาน |
| E3-1 | SUPPORTING | 6 | S3 classifier | LR บน F-LEX | Learner | E2-3 | D_dev | Yes (No) | PR-AUC; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: < 1 ชม. | E2-1;G4 | — | model+config hash | — | — |
| E3-2 | ESSENTIAL | 6 | S3 classifier | GBDT บน F-LEX (= E5-1) | Learner | E2-3 (H2) / reference ของ H1,H3 | D_dev | Yes (No) | PR-AUC; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: 5–20 CPU-ชม. รวม tuning | E2-1;G4 | MAIN@1e0a2db:run_gb_transformer_experiments.py#L279-L301 train_gb_variant | model+OOF scores | seed SD < |Δ|/2 | — |
| E3-3 | OPTIONAL | 11 | S3 classifier | RF บน F-LEX | Learner | E3-2 | D_dev | Yes (No) | PR-AUC; — | ASSUMPTION: ชั่วโมง | E3-2 | — | — | ทำเมื่อ LR กับ GBDT ต่างมาก | — |
| E4-1 | ESSENTIAL | 5 | S2 feature representation | F-SEM cosine (frozen) | Encoder (<=2) | — | model revision ตรึง | No (No (optional)) | Univariate PR-AUC per semantic feature; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: encode นาที | E1-5;D0-2 | MAIN@1e0a2db:exp_r2_bert_feature.py#L78-L137 | embeddings cache (ภายใน) | revision hash บันทึก | — |
| E4-2 | SUPPORTING | 7 | S3 classifier | semantic-only classifier (เดิม E5-2) | Feature set | E3-2 | D_dev | Yes (No) | PR-AUC; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: 5–20 CPU-ชม. | E4-1 | — | OOF scores | — | — |
| E4-3 | CONDITIONAL | 11 | S2 feature representation | fine-tune bi-encoder | Representation training | E4-1 ใน E5-3 | positive ≥ ~1,000 ใน D_train | Yes (Yes) | PR-AUC; — | ASSUMPTION: 2–5 GPU-ชม. | E5-3;T4 inclusion rule | — | model | เข้าเมื่อผ่าน inclusion rule T4 | ไม่ผ่าน → ไม่ทำ |
| E4-4 | CONDITIONAL | 11 | S3 classifier | fine-tune cross-encoder | Representation training | E5-3 | เหมือน E4-3 | Yes (Yes) | PR-AUC; — | ASSUMPTION: 2–4 GPU-ชม. | E5-3;T4 inclusion rule | — | model | เหมือน E4-3 | เหมือน E4-3 |
| E4-5 | OPTIONAL | 11 | S3 classifier | local LLM บน sample | Matcher type | E5-3 | G1 อนุมัติชัดเจน | No (Yes) | PR-AUC (on sample); — | ASSUMPTION: 1–3 GPU-ชม. | G1 explicit approval | — | — | — | ห้ามใช้ hosted API |
| E5-1 | ESSENTIAL | 6 | S3 classifier | alias ของ E3-2/E3-1 | — | — | — | No (No) | (from E3-2); paired entity-grouped bootstrap (Δ, 95% CI) | 0 (ไม่มี job ใหม่) | E3-2 | — | — | — | — |
| E5-2 | SUPPORTING | 7 | S3 classifier | alias ของ E4-2 | — | — | — | No (No) | (from E4-2); paired entity-grouped bootstrap (Δ, 95% CI) | 0 | E4-2 | — | — | — | — |
| E5-3 | ESSENTIAL | 7 | S2 feature representation | F-LEX ∪ F-SEM | Feature set | E5-1 (=E3-2) | D_dev | Yes (No) | PR-AUC; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: 5–20 CPU-ชม. | E3-2;E4-1 | MAIN@1e0a2db:run_gb_transformer_experiments.py#L279-L301 | OOF scores; ms/คู่ | ΔPR-AUC ตาม H3 + cost ratio | — |
| E5-4 | SUPPORTING | 7 | S2 feature representation | leave-one-group-out 5 กลุ่ม | Feature set | E5-3 | D_dev | Yes (No) | Delta PR-AUC per group; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: 2–6 CPU-ชม. | E5-3 | — | ablation.json | explanatory เท่านั้น | — |
| E5-5 | ESSENTIAL | 7 | S2 feature representation | single lexical group 5 กลุ่ม | Feature set | E5-1 vs best group | D_dev | Yes (No) | PR-AUC; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: 2–6 CPU-ชม. | E3-2 | — | ablation.json | ΔPR-AUC ตาม H1 | — |
| E5-6 | OPTIONAL | 11 | S2 feature representation | missingness-aware | Missing handling | E5-3 | D0-2 strata | Yes (No) | PR-AUC in high-missing strata; — | ASSUMPTION: 1–3 CPU-ชม. | E5-3;D0-2 | — | — | — | — |
| E6-7 | ESSENTIAL | 8 | S4 decision policy | Platt vs isotonic บน OOF ที่ prior เท่ากับ test fold | Calibration method | uncalibrated | OOF scores ของ M* | No (No) | ECE;Brier; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: นาที | E5-3;E3-2 | MAIN@1e0a2db:run_gb_transformer_experiments.py#L279-L301 | calibrator + reliability | ECE ต่างระหว่าง dev-OOF และ fold อื่น ≤ 0.01 | prior shift > 1.5× → ปรับ split ก่อน (บทเรียน ICSEC v2) |
| E6-1 | SUPPORTING | 8 | S4 decision policy | t=0.5, R0 0.98/0.95, stage18 manual rule | Policy | —(reference) | OOF calibrated scores | No (No) | Expected cost per pair; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: วินาที | E6-7 | MAIN@1e0a2db:exp_r1_ga_redecision.py#L18 STAGE18_MANUAL; #L75-L84 decide_code | policy_eval.json | — | — |
| E6-2 | ESSENTIAL | 8 | S4 decision policy | threshold ที่ให้ F1 สูงสุดบน dev | Policy | E6-1 | เหมือน E6-1 | No (No) | Expected cost per pair; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: วินาที | E6-7 | MAIN@1e0a2db:train_data/stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py#L388-L393 choose_threshold | policy.json | — | — |
| E6-3 | ESSENTIAL | 8 | S4 decision policy | closed-form cost threshold + Chow three-way | Policy | E6-1 | cost model freeze | No (No) | Expected cost per pair; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: วินาที | E6-7 | BACKUP@903246c:experiments/code/reviewer_revision.py (chow_decide) | policy.json ×4 cost scenarios | — | — |
| E6-4 | ESSENTIAL | 8 | S4 decision policy | random / scrambled Sobol / TPE × 10 seeds × 2,048 | Optimizer | E6-3 | เหมือน E6-1 | No (No) | Expected cost per pair; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: นาที | E6-7 | BACKUP@903246c:experiments/icsec_final/authoritative_run_v2/policies.py (b1_search/b2_sobol_search) | traces.parquet, policy.json | budget audit ผ่าน (นับ evaluation จริง) | budget ไม่เท่ากัน → rerun |
| E6-5 | ESSENTIAL | 8 | S4 decision policy | GA genome 4 ยีน × 10 seeds × 2,048 | Optimizer | best of E6-2/E6-3/E6-4 | เหมือน E6-1 | No (No) | Expected cost per pair; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: นาที | E6-4 | MAIN@1e0a2db:exp_r1_ga_redecision.py#L75-L156 decide_code/clip/run_ga | traces.parquet, policy.json | budget audit ผ่าน; config GA ตรึงก่อนเห็น E6-4 | ปรับ GA หลังเห็น E6-4 → ผลเป็น exploratory |
| E6-6 | SUPPORTING | 8 | S4 decision policy | three-way (t_low,t_high) | Policy structure | best two-way | cost รวม review | No (No) | Expected cost incl. review; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: นาที | E6-3;E6-4 | — | policy.json | — | — |
| E6-8 | CONDITIONAL | 11 | S4 decision policy | one-to-one assignment | Post-processing | best policy | 1:1 ยืนยันใน D0-2 | No (No) | Expected cost; — | ASSUMPTION: นาที | E6-6;D0-2 (1:1 confirmed) | — | — | ทำเมื่อ 1:1 ยืนยัน (คาดว่าใช่: 4/15,297) | — |
| E7-1 | ESSENTIAL | 10 | end-to-end | REF และ BEST-VAL บน test ครั้งเดียว | Configuration | REF | test fold ที่ lock + G5 | No (No) | End-to-end Recall@P_target and expected cost; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: < 1 ชม. | T1-T6;G5 | MAIN@1e0a2db:exp_lib.py#L107-L140 split_constants/evaluate | final_metrics.json + CI | เปิด test ครั้งเดียว มี log | test ถูกเปิดก่อน → ลดเป็น exploratory |
| E7-2 | ESSENTIAL | 10 | end-to-end | 2×2×2 factorial | Blocker x Matcher x Policy | cell (B0, rule, fixed) | เหมือน E7-1 | No (No) | Main effects on end-to-end expected cost; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: < 1 ชม. | E7-1 | — | factorial.json | 8 cells ประกาศก่อน G5 | — |
| E7-3 | SUPPORTING | 10 | end-to-end | strata + perturbation | Stratum / perturbation | unperturbed | D0-2 strata | No (No) | Per-stratum PR-AUC and cost; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: < 1 ชม. | E7-1 | — | strata.json | strata เล็ก = exploratory | — |
| E7-4 | SUPPORTING | 10 | end-to-end | prior sensitivity (natural, ×0.5, ×0.1, full-graph prior) | Prior | natural | — | No (No) | Precision and cost at priors; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: นาที | E7-1 | — | prior.json | — | — |
| E7-5 | SUPPORTING | 10 | end-to-end | วัด ms/1k คู่ต่อ stage | Stage | — | ฮาร์ดแวร์ระบุ | No (No) | ms per 1k pairs per stage; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: ชั่วโมง | T1-T6 | — | cost.json | median 5 ครั้ง | — |
| E7-6 | SUPPORTING | 10 | end-to-end | label sensitivity S1/S2/S3 | Label assumption | S1 | π_hidden จาก D0-3 | No (No) | Precision range across assumptions; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: นาที | D0-3;E7-1 | — | label_sens.json | — | — |
| E7-7 | SUPPORTING | 10 | end-to-end | error taxonomy | — | — | validation; test นับตาม taxonomy ที่ freeze | No (No) | FN/FP counts by taxonomy class; paired entity-grouped bootstrap (Δ, 95% CI) | ASSUMPTION: 1–2 วันคน | E7-1 | — | taxonomy.json (ไม่มีตัวอย่างจริง) | ตัวอย่างในเล่มเป็น SYNTHETIC | — |
| E8-1 | OPTIONAL | 12 | S2 feature representation | keyed Bloom vs plaintext | Encoding (L) | E5-1 | GX-T8 | Yes (No) | Delta PR-AUC; — | ASSUMPTION: ชั่วโมง | G1;GX-T8 threat model | MAIN@1e0a2db:exp_r4_bloom_privacy.py#L75-L133 (REIMPLEMENT with keyed HMAC) | — | ต้องมี E8-3 เสมอ | ไม่มี threat model → ไม่ทำ |
| E8-2 | OPTIONAL | 12 | S4 decision policy | Bloom + best policy | Policy | E8-1 | GX-T8 | No (No) | Expected cost; — | ASSUMPTION: นาที | E8-1 | — | — | เหมือน E8-1 | — |
| E8-3 | OPTIONAL | 12 | S2 feature representation | attack evaluation | Attack type | — | ethics approval | No (No) | Re-identification rate; — | ASSUMPTION: ชั่วโมง | E8-1;ethics approval | — | attack.json (ไม่มีค่าที่ re-identify ได้) | re-identification rate รายงานพร้อม threat model | — |
| E9-1 | CONDITIONAL | 12 | S2 feature representation | image similarity feature | Feature set | E5-3 | GX-T9 + coverage ≥ 50% | Yes (Optional) | Delta PR-AUC; — | ASSUMPTION: 1–2 GPU-ชม. | G1;GX-T9 image rights;coverage>=50% | BACKUP:src/identity_resolution/imaging/* | — | coverage ผ่าน | coverage ประวัติศาสตร์ = Twitter เท่านั้น → คาดว่าไม่ผ่าน |
| E10-1 | CONDITIONAL | 12 | S5 entity-level resolution | clustering จาก pairwise | Clustering method | connected components | 1:n > 5% | No (No) | B-cubed F1; — | ASSUMPTION: นาที | D0-2 (1:n present >5%) | MAIN@1e0a2db:train_data/stage15_crm_entity_pipeline/run_crm_entity_pipeline.py#L250-L272 (union-find) | — | ทำเมื่อ 1:n > 5% | สถิติ schema 0.03% → คาดว่าไม่ทำ |
