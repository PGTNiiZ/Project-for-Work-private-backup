# Experimental Master Plan — Research V2 (ฉบับภาษาไทย)

สถานะ: **PROPOSED** · การทดลองทางวิทยาศาสตร์: **NO-GO** จนกว่า G0–G5 ผ่าน (ดู `RESEARCH_GATES.md`)
เอกสารที่ต้องอ่านคู่กัน: `RESEARCH_QUESTIONS_AND_HYPOTHESES.md`, `HYPOTHESIS_EXPERIMENT_MATRIX.csv`, `EVALUATION_AND_STATISTICS.md`, `EXPERIMENT_DEPENDENCY_GRAPH.md`

---

## 0. หลักการออกแบบ (Design Principles)

1. **แยกผลทีละองค์ประกอบ:** แต่ละการทดลองเปลี่ยนตัวแปรอิสระ *หนึ่ง* มิติ (blocking / representation / learner / policy) และตรึงส่วนที่เหลือที่ "reference configuration"
2. **Reference configuration (REF)** ใช้เป็นจุดยึดของทุก Track:
   - Blocker: B-REF = lexical blocker ที่ดีที่สุดบน validation จาก T1 (คาดว่า E1-2 หรือ E1-3)
   - Features: F-LEX = lexical feature set เต็ม (E2-1)
   - Learner: GBDT (E3-2) และ LR (E3-1) เป็นตัวที่สอง
   - Policy: validation-F1 threshold (E6-2) สำหรับ T1–T5; T6 เป็นที่เดียวที่เปลี่ยน policy
3. **Compact matrix:** core = 7 Tracks, **31 core experiment IDs** (30 ที่ไม่ซ้ำ เพราะ E5-2 ≡ E4-2) + **4 diagnostics** (D0); optional **13 variants** (8 ภายใน T1–T6 + 5 ใน T8–T10) — ไม่มีการแข่งโมเดลแบบไม่จำกัด
4. **Test lock:** test ถูกเปิดครั้งเดียวต่อ configuration ที่ประกาศใน G4; การเลือกทุกอย่างทำบน train/validation (grouped CV)
5. **ป้ายสถานะ:** ทุก variant ติด PROPOSED; ผลประวัติ R0–R6 ติด HIST-UNVERIFIED และใช้เป็น *สมมติฐานตั้งต้น* เท่านั้น

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
   - **E1-1 Standard/exact key blocking** — key = normalized username prefix / exact normalized name (จำลอง blocking เดิมให้ใกล้ที่สุด → *historical replica* B0)
   - **E1-2 Token blocking + block purging** (schema-agnostic) [P12]
   - **E1-3 Sparse retrieval:** TF-IDF character 3–4-gram, cosine top-k
   - **E1-4 Dense retrieval:** frozen sentence encoder (multilingual MiniLM ถ้ามีภาษาไทย) + exact/HNSW kNN top-k [P13, P14, P15]
   - **E1-5 Hybrid:** union ของ E1-3 และ E1-4 ที่ budget รวม k (แบ่ง k/2 + k/2) และ reciprocal rank fusion — เลือกหนึ่งแบบบน validation
   - *E1-6 (optional) Supervised meta-blocking แบบ GSM* — ต้องใช้ label, ทำเฉพาะเมื่อ E1-5 ยังมี PC ต่ำกว่าเป้า
5. **ตัวแปร:** IV = วิธี blocking, budget k ∈ {1, 5, 10, 20, 50}; DV = PC@k, RR, PQ, จำนวน blocking-missed positives ที่กู้คืน, เวลา build/query, หน่วยความจำ
6. **Controls/Baselines:** E1-1 (historical replica) และ "oracle upper bound" = PC = 1 (all pairs, คำนวณเฉพาะบน sample ถ้าใหญ่เกิน); normalization เดียวกันทุกวิธี; k เท่ากัน
7. **ข้อมูล/label:** ต้องรู้ positive *ทั้งหมด* ใน split (ไม่ใช่เฉพาะที่ผ่าน blocking เดิม) — ถ้า ground truth ถูกสร้างจาก blocking เดิม PC ของ E1-1 จะสูงเกินจริงโดยโครงสร้าง (**selection bias**; ต้องตรวจใน D0-1)
8. **Training:** ไม่ต้องสำหรับ E1-1…E1-5 (encoder frozen, TF-IDF fit บน train เท่านั้น); E1-6 ต้อง train
9. **โมเดล/config:** TF-IDF (char_wb, n=3–4, min_df=2); encoder: `paraphrase-multilingual-MiniLM-L12-v2` หรือ `all-MiniLM-L6-v2` (เลือกตาม D0-2 ภาษา) — ระบุ revision hash; FAISS IndexFlatIP (exact) เป็นค่าตั้งต้น, HNSW เฉพาะเมื่อ N ใหญ่
10. **Metrics:** primary = PC@k* ; secondary = PC–|C| curve AUC, RR, PQ, recovery rate = |missed_by_best_lexical ∩ found_by_X| / |missed_by_best_lexical|, latency
11. **สถิติ:** paired entity-grouped bootstrap บน ΔPC@k*; McNemar ระดับคู่จริง (found/not found) เป็นการทดสอบรอง
12. **Compute:** ไม่ต้อง GPU (encoder เล็กรันบน CPU ได้); ดู `COMPUTE_AND_COST_PLAN.md`
13. **Failure modes:** ground truth สร้างจาก blocking เดิม (ทำให้ไม่เป็นธรรม); hub accounts ที่โผล่ใน top-k ของทุกคน; ชื่อสั้นมาก/ซ้ำบ่อย; dense retrieval ไม่เข้าใจการถอดเสียงไทย
14. **เกณฑ์เข้าวิทยานิพนธ์หลัก:** E1-1…E1-5 เข้าเสมอ (ต้นทุนต่ำ, จำเป็นต่อ H5 และ end-to-end); E1-6 เข้าเฉพาะเมื่อ best PC@k* < 0.90
15. **งานเก่าที่ใช้ซ้ำ/ต้อง revalidate:** R6 (BERT semantic blocking) และ "semantic blocking" — HIST-UNVERIFIED; ใช้ *โค้ด* ได้หลังตรวจ (ดู `REUSABLE_COMPONENTS.md`) แต่ต้องรันใหม่ภายใต้ budget k ที่คุม

---

## T2 — Lexical Representation และ Rule-based Matching

1. **แรงจูงใจ:** lexical similarity เป็น baseline ที่ถูก โปร่งใส และเป็นฐานของ R0/R1 เดิม; ต้องรู้ว่า attribute ใดให้สัญญาณ ก่อนจะอ้างว่าโมเดลซับซ้อนช่วย
2. **Literature:** P17 (similarity functions), P16 (Fellegi–Sunter), P02/P03 (UIL features, username behaviour), P01
3. **Hypothesis:** H1 (สัญญาณต่อ attribute), H2 (เป็น rule-based baseline)
4. **Variants:**
   - **E2-1 Per-attribute similarity profile:** สำหรับแต่ละกลุ่ม attribute (username, display name, bio, URL/ลิงก์, location ฯลฯ ตาม D0-2) คำนวณ exact, Jaro–Winkler, normalized Levenshtein, token Jaccard, char-3gram TF-IDF cosine + missing indicator → เป็น F-LEX; รายงาน univariate PR-AUC ต่อ feature (ไม่มีการ train)
   - **E2-2 Historical rule replica:** สูตรน้ำหนัก/threshold ของ R0 ตามที่บันทึกใน repo (HIST-UNVERIFIED จนกว่า V-REPO)
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
14. **เกณฑ์เข้า:** E2-1, E2-3 เข้าเสมอ; E2-2 เข้าในบท "historical replication" ถ้าได้ V-REPO; E2-4 optional
15. **งานเก่า:** "17 features" ของ R0/R1 → ต้องได้รายการและนิยามจาก repo (**BLOCKED**) แล้ว map เข้า F-LEX; ห้ามสมมติว่าเหมือนเดิม

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
14. **เกณฑ์เข้า:** E3-1, E3-2 เข้าเสมอ
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
   - **E5-1 Lexical-only** (F-LEX)
   - **E5-2 Semantic-only** (F-SEM) — เท่ากับ E4-2
   - **E5-3 Lexical + Semantic** (F-LEX ∪ F-SEM)
   - **E5-4 Leave-one-attribute-group-out** จาก E5-3 (หนึ่ง run ต่อกลุ่ม attribute)
   - **E5-5 Single-attribute-group models** (username-only, name-only, bio-only, …)
   - *E5-6 (optional) Missingness-aware fusion:* missing indicators + native NaN vs mean imputation
5. **ตัวแปร:** IV = feature set; DV = PR-AUC, Recall@P_target
6. **Controls:** learner, hyperparameter search budget, C(k*), seeds เหมือนกัน
7. **ข้อมูล:** เหมือน T3 + stratum missingness จาก D0-2
8. **Training:** ต้อง (classifier ต่อ feature set)
9. **Config:** เหมือน T3
10. **Metrics:** primary = PR-AUC; secondary = ΔFN/ΔFP per stratum, permutation importance (diagnostic เท่านั้น ไม่ใช่ hypothesis test)
11. **สถิติ:** paired grouped bootstrap; ablation ทุกตัวรายงาน CI แต่ **ไม่** ปรับ multiplicity เข้ากลุ่ม confirmatory (เป็น explanatory)
12. **Compute:** CPU; จำนวน run = (3 + n_groups×2) × 2 learners × 5 seeds
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
   - **E6-1 Fixed threshold** 0.5 (และค่าที่ใช้ใน R0 ถ้าได้ V-REPO)
   - **E6-2 Validation-F1-optimal threshold**
   - **E6-3 Closed-form cost-optimal threshold** t* = c_FP / (c_FP + c_FN) บน calibrated probability
   - **E6-4 Non-GA search baseline:** random search + TPE (Optuna) บน policy space เดียวกับ GA
   - **E6-5 GA** บน policy space เดียวกัน, budget objective evaluations เท่ากับ E6-4
   - **E6-6 Three-way policy:** (t_low, t_high) → non-match / review / match; ค้นด้วยวิธีที่ดีที่สุดระหว่าง E6-3-analytic (Chow) และ E6-4
   - *E6-8 (optional) One-to-one constraint:* greedy/Hungarian assignment หลัง threshold (ถ้า D0-2 ยืนยันว่าเป็น 1:1)
5. **ตัวแปร:** IV = policy/optimizer; DV = expected cost ต่อคู่, false merges/1k, review rate, coverage, P/R/F1
6. **Controls:** score เดียวกัน; policy space เดียวกัน (เช่น 1 threshold, 2 thresholds, หรือ threshold + per-platform offset); **budget = 2,000 objective evaluations** สำหรับ E6-4 และ E6-5; optimize บน validation (inner CV) เท่านั้น; GA และ TPE รัน 10 seeds
7. **ข้อมูล:** validation ที่ใหญ่พอให้ประมาณ threshold เสถียร (เสนอ ≥ 200 positives); cost model จากเจ้าของโจทย์ (**UNKNOWN** → ใช้ค่าตั้งต้น + sensitivity)
8. **Training:** ไม่ train base model ใหม่; มีเพียง calibration (fit 1–2 พารามิเตอร์) และ policy search
9. **Config GA (เสนอ):** population 40 × 50 generations = 2,000 evaluations, tournament selection, elitism 2, mutation σ = 0.05 — ตั้งค่าที่ G4 และ **ห้ามปรับหลังเห็น validation result ของ E6-4**
10. **Metrics:** primary = expected cost ต่อคู่ (ตาม cost model ที่ freeze); secondary = false merges/1k, review rate, F1, seed SD
11. **สถิติ:** paired grouped bootstrap บน Δcost; ความแปรปรวนข้าม seed ของ optimizer รายงานแยก
12. **Compute:** ต่ำมาก (policy evaluation บน vector ของ score)
13. **Failure modes:** overfit threshold กับ validation เล็ก; cost model ที่ไม่สะท้อนการใช้งานจริง; GA ได้เปรียบจาก budget มากกว่า (ต้องคุม)
14. **เกณฑ์เข้า:** E6-1…E6-7 เข้าเสมอ (ต้นทุนต่ำ, ตอบ H4 ตรง); E6-8 เข้าเมื่อ 1:1 ยืนยัน
15. **งานเก่า:** โค้ด GA ใช้ซ้ำได้หลังตรวจว่าไม่มีการอ่าน test (**ต้องตรวจ V-REPO**); ผล R1/R3/R5 ต้อง revalidate

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
15. **งานเก่า:** รายงานผล R0–R6 → ใช้เป็น "historical comparison table" ในภาคผนวก ติดป้าย HIST-UNVERIFIED

---

## T8–T10 — Optional Extensions (ประเมินแยก ไม่บังคับ)

| Track | Variants | เงื่อนไขเริ่ม (ต้องครบทุกข้อ) | เกณฑ์เข้าวิทยานิพนธ์ | Literature |
|---|---|---|---|---|
| **T8 Privacy-preserving** | E8-1 Bloom-encoded similarity vs plaintext (replica R4) · E8-2 + best policy จาก T6 (replica R5) · **E8-3 attack evaluation**: frequency/pattern-mining attack จำลองบนข้อมูลของเรา → re-identification rate | threat model เป็นลายลักษณ์อักษร; ethics อนุมัติการทดลองโจมตี; G1 | ต้องมี E8-3 เสมอ — ห้ามรายงาน E8-1/E8-2 โดยไม่มี E8-3 แล้วอ้างว่า "privacy-preserving" | P29, P30, P31, P32, P35 |
| **T9 Multimodal** | E9-1 profile image similarity (perceptual hash / image embedding) เป็น feature เพิ่มเข้า E5-3 | สิทธิ์ใช้ภาพชัดเจน; coverage ภาพ ≥ 50% ของคู่; การจัดการ biometric data ผ่าน G1 | ΔPR-AUC > SESOI บน validation และไม่มีปัญหากฎหมาย | P07 |
| **T10 Entity-level** | E10-1 connected components vs correlation-clustering จาก pairwise decisions; metrics: B-cubed P/R, cluster F1, จำนวน transitivity violations | ground truth ระดับ identity ที่เชื่อถือได้ (D0-1); มีกรณี 1:n จริง | เข้าเมื่อ D0-2 พบว่า >5% ของ identity มีหลายบัญชีต่อแพลตฟอร์ม | P28, P16 |

E4-5 (LLM) และ E1-6 (supervised meta-blocking) จัดเป็น optional ด้วย

---

## 8. โปรแกรมทดลองขั้นต่ำที่แนะนำ (Minimum Viable Program)

ตอบ H1–H5 ครบด้วยจำนวน run น้อยที่สุด:

1. D0-1…D0-4 (บังคับ)
2. T1: E1-1, E1-3, E1-4, E1-5 (ตัด E1-2 ได้ถ้า E1-3 ครอบคลุม — ตัดสินที่ G4)
3. T2: E2-1, E2-3
4. T3: E3-1, E3-2
5. T4/T5: E4-1, E5-1, E5-2, E5-3, E5-4, E5-5 (GBDT เป็นหลัก, LR เป็น robustness)
6. T6: E6-7, E6-1, E6-2, E6-3, E6-4, E6-5, E6-6
7. T7: E7-1, E7-2, E7-4, E7-5, E7-6, E7-7

= **27 experiment IDs** + 4 diagnostics; ไม่มี GPU fine-tuning; คาดว่าทำได้บน CPU workstation (ดู compute plan)

## 9. สิ่งที่ต้องยืนยันก่อน freeze แผน (UNKNOWN / BLOCKED)

- ขนาดข้อมูล, จำนวนแพลตฟอร์ม, รายการ attribute — **UNKNOWN** (ต้องได้จาก D0-2 / repo)
- ที่มาของ ground truth — **BLOCKED** (G0)
- รายการ 17/18 features เดิม, โค้ด GA, รายละเอียด R6 — **BLOCKED** (ต้องเข้าถึง repo)
- cost model จริงของการใช้งาน — **UNKNOWN**
- เอกสาร ICSEC — **BLOCKED**
