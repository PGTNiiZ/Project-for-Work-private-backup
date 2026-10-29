# Final Handoff Report — Research V2 Literature Review & Experimental Master Plan

วันที่: 2026-10-25 · สถานะ: Phase 2 (Design) เสร็จในรูปร่าง · **Next-phase gate: NO-GO สำหรับการทดลอง**

## ข้อจำกัดของรอบนี้ (อ่านก่อน)

ไม่สามารถเข้าถึง `PGTNiiZ/Project-for-Work`, private backup, `research_v2/` เดิม, เอกสาร Phase 1 และ ICSEC ได้ → **ไม่มี V-REPO evidence เลย**; ข้อมูล R0–R6 มาจากสรุปที่ผู้ใช้ให้ และติด HIST-UNVERIFIED; ไม่มีการแก้ไขข้อมูล, train, รัน GA, commit หรือ push

## 1. จำนวนงานวิจัยที่ทบทวนและตรวจสอบ

35 รายการ: V-LIT-WEB 18 (2 รายการยังยืนยัน DOI ไม่ได้: P01, P28; อีก 3 รายการยังไม่ได้ใส่ DOI: P19, P30, P31), V-LIT-KNOWN 16 (ต้องตรวจกับ Crossref ก่อนใช้ในเล่ม), UNVERIFIED 1 (P34 — ถูกคัดออก)
ข้อแก้ไขเมทาดาทาที่พบ: Ditto ตีพิมพ์ PVLDB 14(1) ปี 2021 (ไม่ใช่ VLDB 2020); DOI ของ P01 ในเอกสารเดิมยืนยันไม่ได้; P34 ยืนยันการมีอยู่ไม่ได้

## 2. ทิศทางวิจัยหลัก

(1) การประเมินแบบสมจริง (open entities, prior จริง, end-to-end) (2) การแยกผลองค์ประกอบ pipeline (3) cost-sensitive decision และความยุติธรรมของการเทียบ GA (4) semantic representation ภายใต้ heterogeneity และต้นทุน (5) candidate generation แบบ sparse/dense/hybrid ภายใต้ budget เท่ากัน (6) privacy ที่ประเมินด้วยการโจมตี (optional)

## 3. Historical mapping

R0→E2-2/E2-1/E6-1 · R1→E6-5 (เทียบ E6-2…E6-4) · R2→E4-1/E5-3 · R3→แยกเป็น E5-3 + E6-5 และวัด interaction ใน E7-2 · R4/R5→E8-1/E8-2 + E8-3 (ใหม่) · R6→E1-4/E1-5 · GB→E3-2 · MiniLM/BERT→E4-1/E4-4 · feature-aware→E5-4/E5-5 · ICSEC→BLOCKED

## 4. จำนวน Track และ variant

7 core tracks + D0 diagnostics: **31 core experiment IDs** (30 ไม่ซ้ำ) + 4 diagnostics; optional **13** (8 ใน T1–T6, 5 ใน T8–T10)

## 5. Hypothesis-to-experiment coverage

| H | Primary contrast | Baseline | Experiments อื่น |
|---|---|---|---|
| H1 | E5-3/E5-1 vs best single group (E5-5) | E5-5 | E2-1, E5-4, E5-6, E7-3 |
| H2 | E3-2 vs E2-3 | E2-3 (tuned rule, budget เท่ากัน) | E2-2, E3-1, E3-3, learning curves, E7-2 |
| H3 | E5-3 vs E5-1 | E5-1 | E4-1, E4-2, E4-3/E4-4 (conditional), E7-3 |
| H4 | E6-5 vs best{E6-2,E6-3,E6-4} | non-GA optimized baselines | E6-1, E6-6, E6-7, E6-8, E7-2 |
| H5 | E1-5 vs best lexical blocker @k* | E1-1/E1-2/E1-3 | E1-4, E1-6, E7-1, E7-2 |

ทุกสมมติฐานมีการทดลอง + baseline + ตัวชี้วัดหลักที่วัดได้ + SESOI

## 6. งาน training ที่ต้องทำ

Minimum program: train ใหม่เฉพาะ LR และ GBDT (หลาย feature set) + calibration + policy search — **ไม่มี GPU**; Conditional: fine-tune bi-encoder/cross-encoder (GPU); ห้ามใช้โมเดลเดิมเป็นผล V2

## 7. Compute (ASSUMPTION, ต้องวัดจริง)

Scenario M (50k บัญชี/แพลตฟอร์ม, k=20 → ~1M คู่): core ≈ 50–80 CPU-ชม.; conditional GPU ≈ 5–10 GPU-ชม.; S ≈ 5–10 CPU-ชม.; L ต้องปรับวิธี (ANN, successive halving)

## 8. Research gaps / contributions

C1 factorial attribution · C2 protocol การประเมินสมจริงสำหรับ UIL · C3 GA vs non-GA ภายใต้ budget เท่ากัน · C4 semantic cost–benefit บนข้อมูลไทย/ผสม (ขึ้นกับ D0-2) · C5 label-uncertainty sensitivity · C6 privacy–utility (optional)

## 9. Blockers

G0 provenance · G1 data-use/ethics · การเข้าถึง repo (17/18 features, GA, split เดิม) · ICSEC · cost model จริง · ขนาด/ภาษาของข้อมูล · DOI ที่ยังไม่ยืนยัน

## 10. Minimum experimental program

D0-1…D0-4 → E1-1, E1-3, E1-4, E1-5 → E2-1, E2-3 → E3-1, E3-2 → E4-1, E5-1, E5-2, E5-3, E5-4, E5-5 → E6-7, E6-1…E6-6 → E7-1, E7-2, E7-4, E7-5, E7-6, E7-7 (27 IDs)

## 11. Optional advanced

E1-2, E1-6, E2-4, E3-3, E4-3, E4-4, E4-5, E5-6, E6-8, E7-3 (strata เล็ก = exploratory), T8 (E8-1…E8-3), T9 (E9-1), T10 (E10-1)

## 12. Next-phase gate decision

**NO-GO** สำหรับการทดลองทางวิทยาศาสตร์ · **GO** สำหรับ: ตรวจ repo เพื่อเติม `history/`, ยืนยัน DOI ที่ค้าง, สร้าง evaluation harness + smoke test บนข้อมูลสังเคราะห์, เตรียมเอกสาร G0/G1

---

## Deliverable Quality Gates — ผลการตรวจ

| เกณฑ์ | ผล | หมายเหตุ |
|---|---|---|
| ทุก hypothesis มี experiment และ baseline | ✅ | ตาราง §5 |
| ทุก core experiment มี measurable outcome | ✅ | คอลัมน์ primary_metric ใน `HYPOTHESIS_EXPERIMENT_MATRIX.csv` |
| ทุก research gap อ้างอิง literature | ✅ | `RESEARCH_GAPS_TH.md` ระบุ paper ID ทุกข้อ; G-3 ระบุว่าต้องค้นเพิ่ม |
| ทุก experiment ระบุว่าต้อง train หรือไม่ | ✅ | `TRAINING_REQUIREMENTS.md` + CSV |
| งานเก่าไม่ถูกนำเสนอเป็นผลใหม่ | ✅ | HIST-UNVERIFIED ทุกจุด |
| ลำดับการทดลองเป็นไปได้ | ✅ (มีเงื่อนไข) | ขึ้นกับ G0/G1 |
| ไม่มีผลใหม่ที่ถูกแต่งขึ้น | ✅ | ไม่มีตัวเลขผล V2; ตัวเลข compute ติด ASSUMPTION |
| แยก contribution ออกจาก implementation detail | ✅ | `RESEARCH_GAPS_TH.md` §"สิ่งที่ไม่ใช่ contribution" |
| Paper ทุกชิ้นลิงก์กับ experiment | ✅ (ยกเว้น P34 ที่ถูกคัดออก) | `PAPER_EVIDENCE_MATRIX.csv` |
| มี V-REPO evidence | ❌ **BLOCKED** | ไม่มีสิทธิ์เข้าถึง repo |
