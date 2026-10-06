# Closure Plan: พิสูจน์ว่า Feature อื่นแทน `name_sim` ใน GA Decision Policy ได้หรือไม่

## 1. คำถามที่ต้องตอบเพียงข้อเดียว

> ภายใต้ candidate population, validation split และ CRM cost policy เดียวกัน มี evidence guard ใดแทน `name` ใน GA decision policy แล้ว **ผ่าน quality gates** พร้อมมี cost ต่ำกว่าหรือไม่

คำว่า “แทนได้” ต้องหมายถึงผ่านทุกข้อพร้อมกัน:

1. Precision ≥ 0.99
2. Recall ≥ 0.70
3. ไม่มี platform pair ที่ support ≥100 มี Precision < 0.98
4. REVIEW ไม่เกิน capacity ที่ CRM owner กำหนด
5. ในกลุ่ม policy ที่ผ่านข้อ 1-4 เลือก policy ที่ CRM cost ต่ำสุด

$$
C_{crm}=2FP+FN+0.1REVIEW
$$

ห้ามสรุปว่า policy “ดีที่สุด” จาก cost ต่ำสุด หากไม่ผ่าน quality gates

## 2. เหตุผลที่ผลเดิมดูขัดกัน

ผลเดิมไม่ใช่คำตอบของ experiment เดียวกัน:

| ผลที่เห็น | คำถามที่ตอบ | Population | Objective | คำตอบ |
|---|---|---|---|---|
| Name group AP delta = 0.277651 | feature ใดมีผลต่อ pair-model score | labeled validation | permutation AP | `name` สำคัญสุดต่อ model |
| `bio` guard ชนะ | guard ใด cost ต่ำบน labeled subset | 58,696 labeled pairs | historical cost | `bio` ชนะเฉพาะ scope นี้ |
| `style` guard ชนะ | guard ใด cost ต่ำบน full cache | 2.07M pairs | historical cost | `style` ชนะเฉพาะ cost เก่า |
| `name` guard ชนะ cost 3,498.60 | guard ใด scalar cost ต่ำบน full validation | 2.07M pairs | `crm_derived_v1` | `name` cost ต่ำสุด แต่ไม่ผ่าน gates |

ดังนั้นไม่มี logical contradiction ข้อผิดพลาดเกิดจากใช้คำว่า “ดีที่สุด” โดยไม่ระบุว่า **ดีที่สุดต่อ metric ใด บนข้อมูลใด และภายใต้ cost ใด**

## 3. คำตอบปัจจุบันที่พูดได้ทันที

1. **Pair model:** ยังไม่มี feature group ที่แทน name similarity ได้ หลักฐาน permutation AP delta ของ Name = 0.277651 สูงกว่า Bio = 0.011153 ประมาณ 25 เท่า
2. **GA scalar-cost validation:** ภายใต้ `crm_derived_v1` ตัวที่ cost ต่ำสุดคือ `name` ไม่ใช่ `bio`, `style`, `URL` หรือ `image`
3. **Production decision:** ยังไม่มี policy ใดผ่านเกณฑ์ `Precision ≥0.99` และ `Recall ≥0.70`; แม้ `name` จะชนะ cost แต่ได้ Precision 0.9853 และ Recall 0.6240
4. **ข้อสรุปชั่วคราว:** ยัง proof ไม่ได้ว่า feature อื่นแทน `name_sim` ได้ และยัง proof ไม่ได้ว่า name-only policy พร้อม production

## 4. Canonical Experiment ที่ใช้ปิดคำถาม

### 4.1 Freeze protocol ก่อนรัน

- Population: full scored-candidate cache 2,073,842 คู่
- Split selection: entity-aware validation เท่านั้น
- Cost: `crm_derived_v1` เท่านั้น
- Model probability: frozen ห้าม retrain ระหว่าง guard comparison
- Feature schema และ availability masks: version/hash เดียวกัน
- Seeds: อย่างน้อย 10 GA seeds ต่อ policy
- Test: ห้ามอ่าน test เดิมในการเลือก policy

### 4.2 Policies ที่ต้องเปรียบเทียบ

| ID | Policy | บทบาท |
|---|---|---|
| G0 | score only | baseline ที่ไม่มี evidence guard |
| G1 | score + name | baseline ปัจจุบัน |
| G2 | score + bio | candidate replacement |
| G3 | score + URL | candidate replacement แบบ availability-gated |
| G4 | score + location | รันเมื่อ usable coverage ผ่าน gate เท่านั้น |
| G5 | score + image | candidate replacement แบบ availability-gated |
| G6 | score + style | candidate replacement |
| G7 | weighted evidence | candidate สำหรับเสริม name/รวมหลาย evidence |
| G8 | weighted evidence without name | ทดสอบ replacement โดยตรง |

G8 สำคัญที่สุดต่อคำว่า “แทน name” เพราะถ้ายังมี name อยู่ใน weighted policy จะสรุปได้เพียงว่า feature อื่น **ช่วยเสริม** name ไม่ใช่แทน name

### 4.3 Constrained objective

เปลี่ยนจาก scalar-cost ranking เป็น feasible-first ranking:

```text
1. แบ่ง policy เป็น feasible / infeasible จาก quality gates
2. ถ้ามี feasible policy: เลือก feasible policy ที่ cost ต่ำสุด
3. ถ้าไม่มี feasible policy: รายงาน NO POLICY PASSED
4. เรียง infeasible policy ด้วย constraint violation แล้วจึง cost
```

ห้ามใช้ penalty coefficient รวม Precision/Recall เข้า cost เพราะอาจทำให้ policy ที่ผิด gate ดูเหมือนชนะ

### 4.4 Stability และ uncertainty

สำหรับทุก policy รายงาน:

- median และ best/worst cost จาก 10 seeds
- สัดส่วน seed ที่ได้ policy ผ่าน gates
- bootstrap 95% CI ของ Precision, Recall, F1 และ cost
- metrics แยก Google+ × Twitter, Google+ × Instagram, Instagram × Twitter
- coverage, positive support และ high-score precision ของ guard
- FP/FN/REVIEW delta เทียบ G0 และ G1

Policy ถือว่า stable เมื่ออย่างน้อย 8/10 seeds เลือก operating region เดียวกันและ conclusion ผ่าน/ไม่ผ่าน gate ไม่เปลี่ยน

## 5. Fresh-Test Rule

test เดิมเคยถูกเปิดใน historical experiments แล้ว จึงไม่ใช้เป็นหลักฐาน final สำหรับ policy ที่ tune ใหม่ ขั้นปิดผลต้องมี fresh audit/temporal test:

1. stratified sample จาก exact collisions, high-score negatives, weak-name positives, blocking misses และทุก platform pair
2. ผู้ตรวจสองคน label อิสระ: MATCH / NO_MATCH / INSUFFICIENT
3. conflict ส่ง adjudicator คนที่สาม
4. lock labels และ checksum ก่อน freeze policy
5. เปิด fresh test เพียง policy เดียวหลัง constrained validation จบ

ถ้ายังไม่มี fresh test ให้สถานะผลเป็น **validation proof only** ห้ามใช้คำว่า production-proven

## 6. Implementation Plan

### Phase A: Constrained selector

แก้ไฟล์:

- `src/identity_resolution/core/business_cost.py`: เพิ่ม `PolicyConstraints` และ constraint violations
- `experiments/code/run_feature_aware_ga_pipeline.py`: feasible-first selection และ G8 without-name policy
- `experiments/code/run_full_feature_aware_ga_pipeline.py`: multi-seed runner, frozen protocol metadata และ no-test default

Tests:

- feasible policy ต้องชนะ infeasible policy แม้ cost สูงกว่า
- test labels เปลี่ยนแล้ว validation winner ต้องไม่เปลี่ยน
- missing evidence ต้องคง REVIEW ไม่ถูก demote เป็น NO_MATCH
- G8 ต้องไม่มี name score/weight ใน numerator และ denominator

### Phase B: Stability report

สร้าง artifacts:

```text
artifacts/decisioning/name_guard_closure_crm_v1/
  protocol.json
  seed_results.csv
  constrained_leaderboard.csv
  bootstrap_intervals.csv
  platform_pair_metrics.csv
  feature_attribution.csv
  frozen_policy.json
  validation_conclusion.json
```

`validation_conclusion.json` ต้องมีค่าเดียวจากชุดต่อไปนี้:

- `REPLACEMENT_PROVEN_ON_VALIDATION`
- `SUPPLEMENT_ONLY`
- `NAME_REMAINS_BEST_BUT_NOT_PROMOTABLE`
- `NO_POLICY_PASSED`

### Phase C: Fresh audit test

หลัง freeze winner แล้วจึงสร้าง `fresh_test_report.json` และตัดสิน final status:

- replacement ผ่าน fresh test → `REPLACEMENT_PROVEN`
- weighted policy ที่ยังใช้ name ผ่าน → `SUPPLEMENT_PROVEN`
- ไม่มี policy ผ่าน → `NO_PRODUCTION_POLICY`

## 7. Decision Table สำหรับตอบผล

| Validation/Fresh-test outcome | คำตอบที่อนุญาต |
|---|---|
| G2-G6 หรือ G8 ผ่าน gates และดีกว่า G1 | “feature อื่นแทน name guard ได้ภายใต้ protocol นี้” |
| G7 ผ่าน แต่ G8 ไม่ผ่าน | “feature อื่นช่วยเสริม name แต่ยังแทน name ไม่ได้” |
| G1 ผ่านและตัวอื่นไม่ผ่าน | “name guard ยังเป็น baseline ที่เหมาะที่สุด” |
| ทุก policy ไม่ผ่าน | “ยังไม่มี policy พร้อมใช้งาน; เปรียบเทียบ winner ไม่ใช่คำตอบ production” |
| Validation ผ่านแต่ยังไม่มี fresh test | “ผ่าน validation proof แต่ยังไม่ production-proven” |

## 8. รูปแบบคำตอบสุดท้ายที่ไม่ conflict

ใช้ข้อความนี้จนกว่าจะมีผล constrained/fresh-test ใหม่:

> Feature importance และ GA guard ตอบคนละคำถาม Permutation importance ยืนยันว่า name similarity มีผลต่อ pair-model score สูงที่สุด ส่วนการทดลอง GA ภายใต้ CRM cost พบว่า name guard มี validation cost ต่ำที่สุดใน full candidate population อย่างไรก็ตาม Precision 0.9853 และ Recall 0.6240 ยังไม่ผ่าน promotion gates จึงยังไม่มีหลักฐานว่า bio, URL, image หรือ style สามารถแทน name guard ได้ และยังไม่มี scalar-cost policy ใดพร้อม production ขั้นถัดไปคือเปรียบเทียบ constrained policies รวม weighted-without-name บน multi-seed validation แล้วเปิด fresh audit test เพียง policy เดียวหลัง freeze

## 9. Definition of Done

ปิดข้อสงสัยนี้ได้เมื่อครบทุกข้อ:

- ใช้ population, split, model score, feature version และ cost policy เดียวกัน
- มี G0-G8 รวม weighted-without-name
- ใช้ feasible-first constraints ไม่ใช่ cost อย่างเดียว
- มี multi-seed stability และ bootstrap CI
- รายงาน feature importance แยกจาก GA policy outcome
- freeze policy ก่อน fresh test
- final report ใช้คำว่า replacement, supplement หรือ no-policy ตาม Decision Table เท่านั้น
