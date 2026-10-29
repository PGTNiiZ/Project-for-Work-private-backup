# Experiment Dependency Graph — Research V2 (v2 reconciled)

## Changes vs v1

| # | การเปลี่ยนแปลง | เหตุผล/หลักฐาน |
|---|---|---|
| G1 | ลบ node E2-2 (RETIRED → E6-1) | `review/ID_CHANGELOG.md` |
| G2 | E5-1 และ E5-2 แสดงเป็น alias (เส้นประ) ของ E3-2 และ E4-2 — ไม่มี job ใหม่ | `review/EXPERIMENT_REDUNDANCY_REVIEW.md` |
| G3 | เพิ่ม D0-5 (OPTIONAL) และเส้น D0-4 → G3 ที่ครอบคลุม historical exposure ของ test เดิม | test เดิมถูกใช้ ≥15 ครั้ง (`review/HISTORICAL_EXPERIMENT_AUDIT.md` A6) |
| G4 | B-REF → **B\*** เลือกจาก {E1-1, E1-3, E1-5} บน development ที่ budget = \|C_B0\| | `EXPERIMENTAL_MASTER_PLAN_TH.md` M5 |
| G5 | T6 ใช้ OOF scores ของ M* จาก cross-fitting (ไม่ใช่ validation fold เล็ก) | M9 (calibration prior shift CONFIRMED_DEFECT) |
| G6 | ทุก node มีป้าย priority; MVP critical path ระบุ | prompt §4 |
| G7 | G5 ระบุว่า **fresh-holdout ทำไม่ได้ด้วยข้อมูลเดิม** → ต้องข้อมูลใหม่หรือลดระดับข้อสรุป | `RESEARCH_GATES.md` G5 |

ลำดับการทดลองถูกออกแบบให้ **ทุกขั้นใช้เฉพาะ artifact ที่ freeze แล้วจากขั้นก่อนหน้า** และ test fold ถูกเปิดเพียงครั้งเดียวที่ปลายทาง

## 1. แผนภาพ (Mermaid)

```mermaid
flowchart TD
  classDef ess fill:#d8f0d8,stroke:#2e7d32;
  classDef sup fill:#e3ecfa,stroke:#1f5fbf;
  classDef cond fill:#fff4d6,stroke:#b07d00,stroke-dasharray: 4 3;
  classDef opt fill:#eeeeee,stroke:#777,stroke-dasharray: 2 2;
  classDef gate fill:#fde2e2,stroke:#c62828;

  G0[G0 Ground-truth provenance]:::gate --> G1[G1 Data-use authorization]:::gate
  G1 --> D01[D0-1 Label + LinkSocial provenance audit]:::ess
  G1 --> D02[D0-2 Dataset profile]:::ess
  D01 --> D03[D0-3 Hidden-positive audit]:::ess
  D02 --> D04[D0-4 Leakage + historical-exposure audit]:::ess
  G1 -.-> D05[D0-5 Historical artifact re-analysis]:::opt
  D01 --> G2[G2 Data dictionary + label policy]:::gate
  D02 --> G2
  D03 --> G2
  G2 --> G3[G3 Split freeze: 5 entity folds, test locked]:::gate
  D04 --> G3
  G3 --> G4[G4 Pre-registration freeze]:::gate

  G4 --> E11[E1-1 B0 replica]:::ess
  G4 --> E12[E1-2 Token blocking]:::cond
  G4 --> E13[E1-3 TF-IDF top-k]:::ess
  G4 --> E14[E1-4 Dense kNN]:::ess
  E13 --> E15[E1-5 Hybrid at budget C_B0]:::ess
  E14 --> E15
  E15 -.-> E16[E1-6 Supervised meta-blocking]:::cond
  E11 --> BSTAR{{B* chosen on development}}
  E12 --> BSTAR
  E13 --> BSTAR
  E15 --> BSTAR

  BSTAR --> E21[E2-1 F-LEX]:::ess
  BSTAR --> E41[E4-1 F-SEM frozen]:::ess
  E21 --> E23[E2-3 Tuned rule]:::ess
  E21 -.-> E24[E2-4 Fellegi-Sunter EM]:::opt
  E21 --> E31[E3-1 LR]:::sup
  E21 --> E32[E3-2 GBDT]:::ess
  E32 -.-> E33[E3-3 RF]:::opt
  E32 -. alias .- E51[E5-1 = E3-2]:::ess
  E41 --> E42[E4-2 Semantic-only]:::sup
  E42 -. alias .- E52[E5-2 = E4-2]:::sup
  E32 --> E53[E5-3 Lex+Sem]:::ess
  E41 --> E53
  E32 --> E55[E5-5 Single group]:::ess
  E53 --> E54[E5-4 Leave-one-group-out]:::sup
  E53 -.-> E56[E5-6 Missingness-aware]:::opt
  E53 -.-> E43[E4-3 Fine-tuned bi-encoder GPU]:::cond
  E53 -.-> E44[E4-4 Cross-encoder GPU]:::cond
  E53 -.-> E45[E4-5 Local LLM]:::opt

  E53 --> MSEL{{M* chosen on development}}
  E32 --> MSEL
  MSEL --> E67[E6-7 Calibration on OOF]:::ess
  E67 --> E61[E6-1 Fixed + historical rules]:::sup
  E67 --> E62[E6-2 Val-F1 threshold]:::ess
  E67 --> E63[E6-3 Cost-optimal + Chow]:::ess
  E67 --> E64[E6-4 Random / Sobol / TPE]:::ess
  E64 --> E65[E6-5 GA budget-matched]:::ess
  E63 --> E66[E6-6 Three-way]:::sup
  E64 --> E66
  E66 -.-> E68[E6-8 One-to-one]:::cond

  E15 --> G5[G5 Final-config declaration + fresh-holdout decision]:::gate
  E23 --> G5
  E55 --> G5
  E65 --> G5
  E62 --> G5
  E63 --> G5
  G5 --> E71[E7-1 End-to-end REF + BEST-VAL]:::ess
  G5 --> E72[E7-2 2x2x2 factorial]:::ess
  E71 --> E73[E7-3 Robustness]:::sup
  E71 --> E74[E7-4 Prior sensitivity]:::sup
  E71 --> E75[E7-5 Compute cost]:::sup
  D03 --> E76[E7-6 Label sensitivity]:::sup
  E71 --> E76
  E71 --> E77[E7-7 Error analysis]:::sup

  G1 -. GX-T8 threat model + ethics .-> E81[E8-1 Keyed Bloom]:::opt
  E81 -.-> E82[E8-2 Bloom + policy]:::opt
  E81 -.-> E83[E8-3 Attack evaluation]:::opt
  G1 -. GX-T9 image rights + coverage .-> E91[E9-1 Image feature]:::cond
  D02 -. if 1:n > 5% .-> E101[E10-1 Entity clustering]:::cond
```

## 2. ลำดับการทำงาน (topological order)

| ขั้น | รายการ (priority) | เข้าได้เมื่อ | ทำขนานกันได้ |
|---|---|---|---|
| 0 | G0 → G1 | — | — |
| 1 | D0-1, D0-2 (ESSENTIAL) | G1 | ได้ |
| 2 | D0-3, D0-4 (ESSENTIAL); D0-5 (OPTIONAL) | D0-1 / D0-2 | ได้ |
| 3 | G2 → G3 → G4 | D0-1…D0-4 | — |
| 4 | E1-1, E1-3, E1-4 (ESSENTIAL); E1-2 (CONDITIONAL) | G4 | ได้ทั้งหมด |
| 5 | E1-5 → เลือก B*; E2-1 ∥ E4-1 | ขั้น 4 | E2-1 ∥ E4-1 |
| 6 | E2-3, E3-2 (= E5-1) (ESSENTIAL); E3-1 (SUPPORTING) | E2-1 | ได้ |
| 7 | E5-3, E5-5 (ESSENTIAL); E4-2 (= E5-2), E5-4 (SUPPORTING) | ขั้น 6 + E4-1 | ได้ |
| 8 | เลือก M*; E6-7 → E6-2, E6-3, E6-4 → E6-5 (ESSENTIAL); E6-1, E6-6 (SUPPORTING) | ขั้น 7 | E6-1…E6-4 ขนานกัน; E6-5 หลังตรวจ budget audit ของ E6-4 |
| 9 | G5 (ประกาศ 19 test configurations + hash; ตัดสิน fresh-holdout) | ขั้น 5–8 | — |
| 10 | E7-1, E7-2 (ESSENTIAL) → E7-3…E7-7 (SUPPORTING) | G5 | E7-3…E7-7 ขนานกัน |
| 11 | CONDITIONAL/OPTIONAL ของ T1–T6: E1-6, E2-4, E3-3, E4-3, E4-4, E4-5, E5-6, E6-8 | ตาม inclusion rule (ตัดสินบน development ก่อน G5; ถ้าตัดสินหลัง G5 ต้องเป็น exploratory) | — |
| 12 | T8 (E8-1, E8-2, E8-3), T9 (E9-1), T10 (E10-1) | GX gates | — |

## 3. จุดเสี่ยงของลำดับ (critical path)

- **G0/G1 เป็นคอขวดหลัก** — repo ไม่มีเอกสาร G1 ใด ๆ และ G0 ยัง PARTIAL (`RESEARCH_GATES.md`)
- **G5 fresh-holdout** — entity ทุกตัวเคยถูกใช้ในงานเดิม → ต้องตัดสินก่อนเปิด test ว่าจะ (a) หาข้อมูลใหม่ หรือ (b) ลดระดับเป็น exploratory
- **การเลือก B\*** ส่งผลต่อทุก Track ถัดไป → freeze ก่อนเริ่มขั้น 5; ถ้าเปลี่ยน ต้องรันขั้น 5–8 ใหม่
- **การเลือก M\*** ส่งผลต่อ T6 → T6 ใช้ OOF score ของ M* ที่ freeze
- **E7-2 factorial** ต้องการ artifacts ของ B0 (E1-1), rule (E2-3) และ fixed policy (E6-1 R0 rule) — เก็บไว้แม้ไม่ใช่ตัวเลือกที่ดีที่สุด
- **E7-6** ต้องการ π_hidden จาก D0-3 — ถ้าไม่ได้ทำ D0-3 ทำได้แค่ S1/S2

## 4. งานที่ทำได้ **ก่อน** gate ผ่าน (ไม่ใช่การทดลองทางวิทยาศาสตร์)

- แก้ privacy exposure ของ repo สาธารณะ (การตัดสินใจของเจ้าของข้อมูล — ดู `review/METHODOLOGICAL_RISKS.md` §P)
- เขียน/ทบทวน evaluation harness, cluster bootstrap, budget audit, sealed-label store (ใช้ซ้ำจาก ICSEC v2 หลังตรวจ)
- Smoke test บนข้อมูลสังเคราะห์เพื่อวัด throughput (`COMPUTE_AND_COST_PLAN.md`)
- เตรียมเอกสาร G0/G1 และ pre-registration (G4)
