# Research Gap Validation

ตรวจ G-1…G-6 ของ v1 [V1:RESEARCH_GAPS_TH.md] กับ literature ที่ตรวจแล้ว (P01–P49) และหลักฐาน repository — ผลถูกเขียนกลับเข้า `literature/RESEARCH_GAPS_TH.md` (Changes vs v1 RG-a…RG-f)

| Gap | v1 confidence | หลักฐานใหม่ (literature) | หลักฐานใหม่ (repository) | สถานะ v2 | Confidence v2 | Contribution ที่ยังตั้งได้ |
|---|---|---|---|---|---|---|
| G-1 Factorial attribution ของ pipeline | กลาง | ไม่พบงาน UIL ที่ทำ factorial blocking × representation × learner × policy [P01, P02, P46] | R0–R3 ตั้งใจเป็น 2×2 แต่ปน (A1); ICSEC v2 แยก B0→B1→B2→B3 ได้เฉพาะแกน policy | **VALID** (ยังเปิด) | กลาง | C1 → E7-2, E5-4 |
| G-2 Realistic evaluation (e2e, prior) | สูง (EM) / กลาง (UIL) | P07, P47 (benchmark เกินจริง); P46 (small-sample UIL เกินจริง: recall 19% ที่ precision 95% เมื่อขนาดสมจริง) | repo มี e2e harness แล้ว (R-05) แต่ใช้ within-role pairs, ไม่มี CI | **VALID แต่ต้องปรับถ้อยคำ**: ไม่ใช่ "ไม่มีใครทำ e2e" — โครงการเองทำ e2e แล้ว; ช่องว่างคือ prior sensitivity + cluster CI + label sensitivity | สูง | C2 → E7-1, E7-4, E7-6 |
| G-3 GA vs optimizer อื่นที่ budget เท่ากัน | ต่ำ–กลาง | P39, P40 (GP/GA ใน linkage); P41, P42 (baseline); ไม่พบการเทียบที่ budget เท่ากันสำหรับ linkage threshold | **ICSEC v2 ของโครงการเองเทียบ GA vs Sobol แล้ว** (GA ≈ Sobol) [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2/FINAL_RESULTS.md#L27-L33] | **NARROWED**: เป็น "replication ที่เข้มกว่า" (10 seeds, random/TPE, cluster CI, แก้ calibration) ไม่ใช่ first evidence | กลาง | C3 → E6-4, E6-5 (TOST สำหรับ "เทียบเท่า") |
| G-4 Semantic บนภาษาไทย/ถอดเสียง | กลาง | ไม่มี paper สนับสนุนว่าข้อมูลมีภาษาไทย; P38 = Twitter/Google+/Instagram | ไม่มีหลักฐาน repo ว่ามีภาษาไทย; encoder ที่ใช้เป็น English (MiniLM-L6-v2, distilbert-uncased) | **NOT SUPPORTED as stated → RE-SCOPED** เป็น semantic cost–benefit บนคู่ที่ชื่อต่างกันตามตัวอักษร | ต่ำ (จนกว่า D0-2) | C4 (ลดระดับ) → E5-3, E7-3 |
| G-5 Ground truth ไม่ครบ / negative ไม่แน่นอน | กลาง | P27, P46 (self-declared GT bias), P38 (วิธีสร้าง GT ไม่ทราบ) | GT = corpus annotation ที่ไม่ได้ตรวจภายนอก [BACKUP@ab93b36:docs/research_rebuild/phase_01/05_DATA_AND_EXPERIMENT_LIMITATIONS.md#L11-L15]; exact tier FP 63 | **VALID (แข็งแรงขึ้น)** | กลาง–สูง | C5 → D0-1, D0-3, E7-6 |
| G-6 Privacy ของ Bloom บน social attributes | กลาง (optional) | P29–P32, P35, P34 | R4/R5 อ้าง privacy โดยไม่มี attack, salt ในโค้ด | **VALID (optional)** | กลาง | C6 → E8-1…E8-3 |
| G-7 (ใหม่) Test exposure ของข้อมูลที่ถูกใช้ซ้ำ | — | P21 | test เดิมถูกใช้ ≥15 ครั้ง; ICSEC test 3 ชุดถูกใช้ซ้ำใน v2r1/reviewer | **NEW** | สูง | ส่วนหนึ่งของ C2 → D0-4, G5, D0-5 |

## สิ่งที่ไม่ใช่ contribution (ย้ำ)

การ port โค้ด R-series, การจัด YAML/manifest, sealed-label store, การเลือก library — เป็นเครื่องมือ ไม่ใช่ข้อค้นพบ; ICSEC paper ที่ตีพิมพ์/ส่งแล้วต้องถูกอ้างเป็นงานก่อนหน้า (ระวัง self-plagiarism) ไม่ใช่ผลใหม่
