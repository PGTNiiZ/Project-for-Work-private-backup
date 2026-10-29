# Experiment Redundancy Review (Task B)

แยก 5 pipeline stages ตลอด: **S1** candidate generation · **S2** feature representation · **S3** classifier · **S4** decision policy · **S5** entity-level — การดีขึ้นที่ stage หนึ่งไม่ใช่การดีขึ้นของทั้ง pipeline จนกว่าวัดใน T7

## 1. การประเมิน track ของ v1 (D0, T1–T10)

| Track | มีโค้ดประวัติศาสตร์? | มีผลประวัติศาสตร์? | ซ้ำ/ขาด | จำเป็นต่อ H1–H5? | Replicate? | Train ใหม่? | Frozen pretrained? | ใช้ artifact เดิมหลัง gate? | ต้องข้อมูล/GT ใหม่? | GPU? | ขึ้นกับ | ตัดสิน |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D0 | Phase 1 audits [BACKUP@ab93b36:docs/research_rebuild/phase_01/] | บางส่วน (schema, lineage) | เพิ่ม D0-5 | ใช่ (gate) | — | ไม่ | — | audit scripts | ผู้ตรวจ label | ไม่ | G0/G1 | **KEEP** |
| T1 (S1) | B0 [F07], bigram [F02], R6 [F11] | B0 PC 0.8867; R6 4/3,316 | E1-2 อาจซ้ำ E1-3 → CONDITIONAL | H5 | E1-1 = replicate B0 | ไม่ (E1-6 ใช่) | E1-4 | B0 code | ไม่ | ไม่ | G4 | **KEEP** |
| T2 (S2/S3) | 17 features [F09]; ไม่มี tuned rule | — | **E2-2 ซ้ำกับ T6** (R0 เป็น policy) → RETIRED | H1, H2 | — | ไม่ | — | feature code | ไม่ | ไม่ | T1 | **KEEP (ลด 1)** |
| T3 (S3) | GB [F06, F13, F16] | ใช่ (HIST) | **E5-1 ≡ E3-2/E3-1** | H2 | — | ใช่ | — | — | ไม่ | ไม่ | T2 | **KEEP** |
| T4 (S2) | MiniLM [F09], DistilBERT [F11] | GB-17 vs GB-18 (HIST) | **E5-2 ≡ E4-2** | H3 | — | E4-2 ใช่; E4-3/4 ใช่ (GPU) | E4-1 | embedding code | ไม่ | E4-3/4/5 | T1 | **KEEP** |
| T5 (S2) | feature-aware GA [F14], name-sim [F15] | validation-only | E5-1, E5-2 เป็น alias | H1, H3 | — | ใช่ | — | — | ไม่ | ไม่ | T3, T4 | **KEEP (เหลือ E5-3/4/5/6)** |
| T6 (S4) | GA [F08], Sobol/Chow [F16b, F17] | ใช่ (HIST, consistent) | ไม่ซ้ำ; **ขาด random/TPE** ในประวัติศาสตร์ | H4 | E6-5 = replicate R1/R3/B3; E6-3 = Chow | ไม่ (policy) | — | GA/Sobol/Chow code | cost model ยืนยัน | ไม่ | T5 | **KEEP** |
| T7 (e2e) | e2e harness [F08, F16b] | ใช่ | ไม่ซ้ำ | ทุก H | — | ไม่ | — | harness | fresh holdout (G5) | ไม่ | T1–T6 | **KEEP** |
| T8 privacy | R4/R5 [F10] | utility เท่านั้น | **ขาด attack** | ไม่ (extension) | REIMPLEMENT | ใช่ | — | ไม่ | threat model, ethics | ไม่ | G1, GX-T8 | **OPTIONAL** |
| T9 multimodal | image [F04] | ผ่าน F06 | — | ไม่ | — | ใช่ | image encoder | ไม่ | สิทธิ์ภาพ | อาจ | GX-T9 | **CONDITIONAL** (คาดว่า coverage ไม่ผ่าน) |
| T10 entity-level (S5) | CRM union-find [F07] | ไม่ถูกประเมิน | — | ไม่ | — | ไม่ | — | union-find | ไม่ | ไม่ | D0-2 | **CONDITIONAL** (1:n 0.03% → คาดว่าไม่ทำ) |

**คำตอบ: V2 ควรคง 7 core tracks (T1–T7) + D0**; T8 OPTIONAL, T9 และ T10 CONDITIONAL

## 2. Redundancy ที่แก้

| ID | ประเภท | เหตุ | การแก้ | หลักฐาน |
|---|---|---|---|---|
| E5-2 ≡ E4-2 | duplicate (v1 รู้แล้ว) | config เดียวกัน | ALIAS → E4-2 | [V1:EXPERIMENTAL_MASTER_PLAN_TH.md#T5] |
| E5-1 ≡ E3-2/E3-1 | duplicate (ใหม่) | F-LEX + learner + budget + C(B*) เดียวกัน | ALIAS → E3-2 (GBDT), E3-1 (LR) | [V1:HYPOTHESIS_EXPERIMENT_MATRIX.csv#E5-1 depends_on E3-1;E3-2] |
| E2-2 | misconceived | R0 เป็น threshold บน learned score ไม่ใช่ lexical rule | RETIRED → E6-1 | [MAIN@1e0a2db:train_data/stage15_crm_entity_pipeline/run_crm_entity_pipeline.py#L117-L127] |
| E1-2 vs E1-3 | อาจซ้ำ | ทั้งคู่เป็น lexical schema-agnostic | CONDITIONAL (ตัดสินที่ G4 ตามเส้น PC–|C| บน development) | v1 §8 ข้อ 2 |
| E6-4 (random+TPE) vs ICSEC B2 (Sobol) | ขาด | ประวัติศาสตร์ใช้ Sobol อย่างเดียว | เพิ่ม scrambled Sobol ใน E6-4 | [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/policies.py#L53-L78] |

## 3. Historical vs V2 matrix (Task B output)

ตารางเต็ม 9 คอลัมน์ (Historical Experiment | Existing Evidence | V2 Experiment | Scientific Purpose | Differences | Reuse Decision | Training Needed | Blocking Issue | Confidence) อยู่ที่ `history/HISTORICAL_EXPERIMENT_MAPPING.md` §2 (Table 1)

## 4. การทดลองที่ไม่จำเป็นต่อ H1–H5 (ไม่อยู่ใน MVP)

E2-4, E3-3, E4-5, E5-6, E8-1…E8-3, D0-5 (OPTIONAL) · E1-2, E1-6, E4-3, E4-4, E6-8, E9-1, E10-1 (CONDITIONAL) · E3-1, E4-2, E5-4, E6-1, E6-6, E7-3…E7-7 (SUPPORTING — มีประโยชน์เชิงอธิบาย/ความทนทาน แต่ไม่ใช่ primary contrast)

## 5. จำนวน (จาก matrix; ตรวจด้วย `_work/scripts/consistency_check.py`)

- v1: 31 core IDs (30 unique) + 4 D0 + 13 optional = 48 แถว
- v2: 49 แถว = 46 distinct (5 D0 + 41) + 2 alias (E5-1, E5-2) + 1 retired (E2-2)
- Priority: ESSENTIAL 22 แถว (21 distinct + alias E5-1) · SUPPORTING 11 (10 + alias E5-2) · CONDITIONAL 7 · OPTIONAL 8 · EXCLUDE 1
