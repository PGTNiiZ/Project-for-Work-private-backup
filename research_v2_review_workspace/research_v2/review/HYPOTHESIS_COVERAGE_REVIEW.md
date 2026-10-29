# Hypothesis Coverage Review (Task D)

ตอบ 10 คำถามต่อสมมติฐาน · ถ้อยคำที่แก้ถูกบันทึกใน `design/RESEARCH_QUESTIONS_AND_HYPOTHESES.md` (Changes vs v1 C1–C9)
**Main contributions** = H1–H5 primary contrasts (C1–C5, Holm) · **Supporting** = H3a, H3b, H4a, H4c, ablations, T7 robustness

## H1 — Feature complementarity

| # | คำถาม | คำตอบ |
|---|---|---|
| 1 | มีความหมาย? | ใช่ — ตอบว่าควรลงทุนเก็บ attribute เพิ่มหรือไม่; missingness สูง (location 65%, bio 18%, URL 17%) ทำให้คำถามนี้สำคัญ [REPOSITORY_RESEARCH_INVENTORY §5] |
| 2 | ทดสอบได้ด้วยข้อมูล? | ได้ (5 กลุ่ม attribute มีครบใน schema) — หลัง G0/G1 |
| 3 | literature motivate? | ใช่ [P01, P02, P46] |
| 4 | ตอบแล้วทางประวัติศาสตร์? | **ไม่** — มีเพียง location delta ใน bigram (≈0) และ name-sim ablation แบบ validation-only บนคู่ balanced (HIST) |
| 5 | ยังเปิดอะไร | กลุ่มใดเติมกัน; ผลเมื่อ attribute หาย |
| 6 | การทดลองที่จำเป็น | **E5-1 (= E3-2), E5-5** (ESSENTIAL); E5-4 (SUPPORTING) |
| 7 | Fair baseline | best single lexical group (เลือกบน development) ภายใต้ learner/hyperparameter เดียวกัน |
| 8 | ผลที่สนับสนุน | ขอบล่าง 95% CI ของ ΔPR-AUC > 0.02 |
| 9 | ผลที่หักล้าง | CI อยู่ใน [−0.02, 0.02] (TOST) → เทียบเท่า |
| 10 | ข้อจำกัด | username/fullname สัมพันธ์สูง (collinear) → leave-one-out ประเมินต่ำ; label-proxy ของกลุ่ม link (URL) |
| แก้ถ้อยคำ | primary contrast เป็น lexical-only (ไม่ขึ้นกับ H3) — **C2** |

## H2 — Learned vs rule-based

| # | คำถาม | คำตอบ |
|---|---|---|
| 1 | มีความหมาย? | ใช่ — กำหนดว่าควรใช้ ML หรือไม่ |
| 2 | ทดสอบได้? | ได้ |
| 3 | literature? | ใช่ [P48, P47, P17] |
| 4 | ตอบแล้ว? | **ไม่** — ไม่มี rule ที่ tune ในประวัติศาสตร์ (F01 ใช้ sweep บนชุดรายงาน) |
| 5 | ยังเปิด | ช่องว่าง learned vs tuned rule และ data-efficiency (learning curve) |
| 6 | การทดลอง | **E2-3, E3-2** (ESSENTIAL); E3-1, learning curves (SUPPORTING) |
| 7 | Fair baseline | E2-3 tuned rule ที่ budget 200 configs เท่ากับ learner |
| 8 | สนับสนุน | ΔPR-AUC CI > 0.02 |
| 9 | หักล้าง | TOST เทียบเท่า หรือ rule ชนะ |
| 10 | ข้อจำกัด | ถ้า pairs เกือบ linearly separable [P47] gap จะเล็กโดยธรรมชาติ |
| แก้ถ้อยคำ | ไม่ต้องแก้ |

## H3 — Semantic representation

| # | คำถาม | คำตอบ |
|---|---|---|
| 1 | มีความหมาย? | ใช่ — ตัดสินว่าคุ้มค่าต้นทุน embedding หรือไม่ |
| 2 | ทดสอบได้? | ได้ (frozen encoder ไม่ต้อง GPU) |
| 3 | literature? | ใช่ [P14, P15, P05, P13] |
| 4 | ตอบแล้ว? | **บางส่วน (HIST, ขัดกัน)**: ICSEC GB-17 ≈ GB-18 (v1 0.8293 vs 0.8280; v2 0.8494 vs 0.8510); MAIN GB-17 0.5967 vs GB-18 0.8296 แต่ต่างเพราะ threshold มือ |
| 5 | ยังเปิด | ผลแบบ threshold-free (PR-AUC) + CI; ผลต่อ stratum ที่ชื่อต่างกัน |
| 6 | การทดลอง | **E4-1, E5-3 vs E5-1** (ESSENTIAL); E4-2, E7-3 (SUPPORTING); E4-3/E4-4 (CONDITIONAL) |
| 7 | Fair baseline | E5-1 (= E3-2) ภายใต้ budget เดียวกัน |
| 8 | สนับสนุน | ΔPR-AUC CI > 0.01 พร้อม cost ratio |
| 9 | หักล้าง | TOST เทียบเท่า — **คาดล่วงหน้าว่าน่าจะเป็นผลนี้** จากหลักฐาน ICSEC (บันทึกเป็น prior ที่ G4) |
| 10 | ข้อจำกัด | encoder English-only ถ้าข้อมูลหลายภาษา; sentinel "[empty]"; bio ว่าง 18% |
| แก้ถ้อยคำ | H3a ไม่สันนิษฐานภาษาไทย — **C3** |

## H4 — Decision optimisation / GA

| # | คำถาม | คำตอบ |
|---|---|---|
| 1 | มีความหมาย? | ใช่ — เป็นคำถามหลักของงานเดิม (GA) |
| 2 | ทดสอบได้? | ได้ (ต้นทุน compute ต่ำ) |
| 3 | literature? | ใช่ [P24, P25, P26, P39–P43] |
| 4 | ตอบแล้ว? | **บางส่วน (HIST, ARTIFACT_CONSISTENT)**: ICSEC v2 GA ≈ Sobol (ΔU 1.8 ภายใน SD); tuned two-threshold B1 ใกล้เคียง; Chow แย่กว่า (1879.0) แต่ภายใต้ calibration prior shift; MAIN nested R1: GA เพิ่ม F1 แต่ cost test สูงกว่า R0 |
| 5 | ยังเปิด | CI ระดับ entity, หลาย seed, random/TPE, calibration ที่ถูกต้อง, cost model ที่ยืนยันโดยเจ้าของ |
| 6 | การทดลอง | **E6-7, E6-2, E6-3, E6-4, E6-5** (ESSENTIAL); E6-1, E6-6 (SUPPORTING) |
| 7 | Fair baseline | best{E6-2, E6-3+Chow, E6-4 (random/Sobol/TPE)} ใน policy space เดียวกัน (4 ยีน) ที่ 2,048 evals |
| 8 | สนับสนุน H4b | Δcost ≥ 5% (CI) |
| 9 | หักล้าง | TOST เทียบเท่า (คาดล่วงหน้า) หรือ non-GA ชนะ |
| 10 | ข้อจำกัด | cost weights เป็นสมมติฐาน; objective แบน; within-fold precision |
| แก้ถ้อยคำ | cost model ผู้สมัคร = crm_derived_v1; optimizer + budget 2,048 — **C4, C5, C6** |

## H5 — Candidate generation

| # | คำถาม | คำตอบ |
|---|---|---|
| 1 | มีความหมาย? | ใช่ — blocking กำหนดเพดาน recall (B0 PC 0.8867) |
| 2 | ทดสอบได้? | ได้ |
| 3 | literature? | ใช่ [P12, P13, P45] |
| 4 | ตอบแล้ว? | **บางส่วน**: R6 hash blocking ล้มเหลว (4/3,316) แต่ไม่ใช่ top-k dense retrieval ที่คุม budget |
| 5 | ยังเปิด | sparse/dense/hybrid ที่ budget เท่ากัน |
| 6 | การทดลอง | **E1-1, E1-3, E1-4, E1-5** (ESSENTIAL); E1-2, E1-6 (CONDITIONAL); e2e ผ่าน E7-2 |
| 7 | Fair baseline | best{E1-1, E1-3} ที่ |C_B0| |
| 8 | สนับสนุน | ΔPC ≥ 0.02 (CI) หรือกู้ ≥10% ของ B0-missed |
| 9 | หักล้าง | TOST เทียบเท่า หรือกู้คืนได้แต่ e2e ไม่ดีขึ้น (bottleneck ที่ matcher) |
| 10 | ข้อจำกัด | budget matching ระหว่าง key blocking (ไม่มี k) และ top-k; hub accounts |
| แก้ถ้อยคำ | budget = |C_B0| — **C7** |

## สมมติฐานใหม่?

ไม่เพิ่ม hypothesis หลัก — คำถามสำคัญที่พบ (ผลประวัติศาสตร์เกินความแปรปรวนหรือไม่) เป็น **diagnostic DQ7 / D0-5 (OPTIONAL)** ไม่ใช่ hypothesis เพราะใช้ข้อมูลที่ contaminated และไม่สามารถยืนยันได้

## สรุปความครอบคลุม

| H | ESSENTIAL experiment + fair baseline + primary metric | ผ่าน |
|---|---|---|
| H1 | E5-5 vs E5-1 (=E3-2), PR-AUC | ✓ |
| H2 | E3-2 vs E2-3, PR-AUC | ✓ |
| H3 | E5-3 vs E5-1, PR-AUC | ✓ |
| H4 | E6-5 vs best{E6-2, E6-3, E6-4}, expected cost | ✓ |
| H5 | E1-5 vs best{E1-1, E1-3}, PC@|C_B0| | ✓ |

ทุกสมมติฐานมีการออกแบบที่ป้องกันได้ (defensible) **ภายใต้เงื่อนไข** ว่า G0/G1 ผ่าน และยอมรับว่าข้อสรุปบนข้อมูลเดิมเป็น exploratory (G5)
