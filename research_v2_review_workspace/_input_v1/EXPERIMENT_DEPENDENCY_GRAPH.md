# Experiment Dependency Graph — Research V2

ลำดับการทดลองถูกออกแบบให้ **ทุกขั้นใช้เฉพาะ artifact ที่ freeze แล้วจากขั้นก่อนหน้า** และ test ถูกเปิดเพียงครั้งเดียวที่ปลายทาง

## 1. แผนภาพ (Mermaid)

```mermaid
flowchart TD
  G0[G0 Ground-truth provenance] --> G1[G1 Data-use authorization]
  G1 --> D01[D0-1 Label audit]
  G1 --> D02[D0-2 Dataset profile]
  D01 --> D03[D0-3 Hidden-positive audit]
  D02 --> D04[D0-4 Leakage audit]
  D01 --> G2[G2 Data dictionary + label policy]
  D02 --> G2
  D03 --> G2
  G2 --> G3[G3 Split freeze + test lock]
  D04 --> G3
  G3 --> G4[G4 Pre-registration freeze]

  G4 --> E11[E1-1 Key blocking B0]
  G4 --> E12[E1-2 Token blocking]
  G4 --> E13[E1-3 TF-IDF retrieval]
  G4 --> E14[E1-4 Dense retrieval]
  E13 --> E15[E1-5 Hybrid]
  E14 --> E15
  E11 --> BREF{{B-REF = best lexical blocker on validation}}
  E12 --> BREF
  E13 --> BREF

  BREF --> E21[E2-1 Lexical features F-LEX]
  E14 --> E41[E4-1 Frozen semantic features F-SEM]
  E21 --> E22[E2-2 Historical rule replica]
  E21 --> E23[E2-3 Tuned rule]
  E21 --> E31[E3-1 LR]
  E21 --> E32[E3-2 GBDT]
  E31 --> E51[E5-1 Lexical-only]
  E32 --> E51
  E41 --> E52[E5-2 = E4-2 Semantic-only]
  E51 --> E53[E5-3 Lexical+Semantic]
  E41 --> E53
  E53 --> E54[E5-4 Leave-one-group-out]
  E51 --> E55[E5-5 Single-group]

  E53 --> MSEL{{Matcher M* selected on validation}}
  E51 --> MSEL
  MSEL --> E67[E6-7 Calibration]
  E67 --> E61[E6-1 Fixed]
  E67 --> E62[E6-2 Val-F1]
  E67 --> E63[E6-3 Cost-optimal]
  E67 --> E64[E6-4 Random+TPE]
  E64 --> E65[E6-5 GA same budget]
  E63 --> E66[E6-6 Three-way]
  E64 --> E66

  E15 --> G5[G5 Final-config declaration + fresh-holdout check]
  E66 --> G5
  E65 --> G5
  E23 --> G5
  G5 --> E71[E7-1 End-to-end on locked test]
  E71 --> E72[E7-2 2x2x2 attribution]
  E71 --> E73[E7-3 Robustness]
  E71 --> E74[E7-4 Prior sensitivity]
  E71 --> E75[E7-5 Cost]
  D03 --> E76[E7-6 Label sensitivity]
  E71 --> E76
  E71 --> E77[E7-7 Error analysis]

  E53 -. conditional .-> E43[E4-3 Fine-tuned bi-encoder]
  E53 -. conditional .-> E44[E4-4 Cross-encoder]
  E15 -. optional .-> E16[E1-6 Supervised meta-blocking]
  G1 -. optional, extra approval .-> T8[T8 Privacy E8-1..E8-3]
  G1 -. optional, image rights .-> T9[T9 Multimodal E9-1]
  D02 -. if 1:n .-> T10[T10 Entity-level E10-1]
```

## 2. ลำดับการทำงาน (topological order)

| ขั้น | รายการ | เข้าได้เมื่อ | ทำขนานกันได้ |
|---|---|---|---|
| 0 | G0 → G1 | — | — |
| 1 | D0-1, D0-2 | G1 | ได้ |
| 2 | D0-3, D0-4 | D0-1 / D0-2 | ได้ |
| 3 | G2 → G3 → G4 | D0 ครบ | — |
| 4 | E1-1…E1-4 | G4 | ได้ทั้งหมด |
| 5 | E1-5; เลือก B-REF; E2-1; E4-1 | ขั้น 4 | E2-1 ∥ E4-1 |
| 6 | E2-2, E2-3, E3-1, E3-2 | E2-1 | ได้ |
| 7 | E5-1, E5-2, E5-3 → E5-4, E5-5 | ขั้น 6 + E4-1 | ablations ขนานกัน |
| 8 | เลือก M*; E6-7 → E6-1…E6-6 | ขั้น 7 | E6-1…E6-4 ขนานกัน; E6-5 หลังตั้ง budget จาก E6-4 |
| 9 | G5 (ประกาศ final configs, ตรวจ holdout) | ขั้น 5–8 | — |
| 10 | E7-1 → E7-2…E7-7 | G5 | E7-2…E7-7 ขนานกัน |
| 11 | Conditional/optional | ตาม inclusion rule | — |

## 3. จุดเสี่ยงของลำดับ (critical path)

- **G0/G1 เป็นคอขวดหลัก** — ไม่มีขั้นใดเริ่มได้ก่อน
- **การเลือก B-REF** ส่งผลต่อทุก Track ถัดไป → ต้อง freeze และห้ามเปลี่ยนหลังเริ่ม T2 (ถ้าเปลี่ยน ต้องรัน T2–T6 ใหม่ทั้งหมด)
- **การเลือก M*** ส่งผลต่อ T6 → T6 ต้องใช้ score จาก M* ที่ freeze
- **E7-2 factorial** ต้องการ component ทั้ง 8 cells พร้อม — วางแผนเก็บ model artifacts ของ B0, E2-3, E6-1 ไว้ด้วย
- **E7-6** ต้องการ π_hidden จาก D0-3 — ถ้า D0-3 ไม่ได้ทำ E7-6 ทำได้แค่ S1/S2

## 4. งานที่ทำได้ **ก่อน** gate ผ่าน (ไม่ใช่การทดลองทางวิทยาศาสตร์)

- เขียน/ทบทวนโค้ด pipeline, unit tests, evaluation harness (grouped bootstrap, metrics)
- Smoke test บนข้อมูลสังเคราะห์หรือ benchmark สาธารณะที่ไม่มีข้อมูลส่วนบุคคล เพื่อวัด throughput (`COMPUTE_AND_COST_PLAN.md`)
- ตรวจ repository เดิมเพื่อเติม `history/` (เป็นการอ่านโค้ด ไม่ใช่การรันบนข้อมูลจริง — แต่ถ้า repo มีข้อมูลส่วนบุคคลฝังอยู่ ต้องผ่าน G1 ก่อนเปิด)
- เตรียมเอกสาร pre-registration
