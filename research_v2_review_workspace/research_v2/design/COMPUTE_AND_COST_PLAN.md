# Compute และ Cost Plan — Research V2 (v2 reconciled)

## Changes vs v1

| # | การเปลี่ยนแปลง | หลักฐาน |
|---|---|---|
| CP1 | ขนาดข้อมูล **แทน ASSUMPTION ด้วยค่าจาก repository**: 36,807 โปรไฟล์ (Twitter 13,960 / Google+ 11,890 / Instagram 10,957); 15,297 entities; candidate set B0 ≈ 2,086,245 คู่ (HIST); within-fold pairs ของ 5-fold entity split ≈ 604,123 คู่ (Gate 5 technical, HIST) | `review/REPOSITORY_RESEARCH_INVENTORY.md` §5; [MAIN@1e0a2db:EXPERIMENT_PLAN.md#L26]; [BACKUP@ab93b36:handoff/worktrees/research-phase15-integration/docs/research_rebuild/phase_01_5/GATE_STATUS_MATRIX.md#L11] |
| CP2 | ข้อความที่ต้อง embed = 36,807 โปรไฟล์ × ≤3 attribute (ไม่ใช่ 20k–2M ตาม scenario) | เช่นเดียวกัน |
| CP3 | Search budget 200 configs × **4** folds; policy 2,048 evals | `TRAINING_REQUIREMENTS.md` TR2, TR7 |
| CP4 | เพิ่มค่าที่ **วัดได้จริงในประวัติศาสตร์** (ไม่ใช่ V2): DistilBERT fine-tune บน CPU ≈ 6.3 วินาที/step (batch 16); GA 4 ยีน 5 seeds ใช้ 0.3–12 วินาที/seed; GB-18 fit (≈26k แถวหลัง undersample) — เป็น *ตัวชี้* เท่านั้น ต้องวัดใหม่ | [MAIN@1e0a2db:experiments/REPORT_R0_R5.md#L74-L78]; [MAIN@1e0a2db:experiments/automation/r1_nested_primary_20260809/summary.md]; [BACKUP@ab93b36:experiments/icsec_final/authoritative_run_v2r1/scientific_outputs/outer_101/training.json] |
| CP5 | Scenario L ตัดออก (ขนาดจริงอยู่ระหว่าง S และ M); ตาราง §3 คิดที่ "R (repo-size)" | CP1 |

> ตัวเลข *เวลา* ทุกตัวในเอกสารนี้ยังเป็น **ASSUMPTION** (ไม่ได้วัดใน V2) ยกเว้นแถวที่ระบุว่า "HIST measured" ซึ่งเป็นค่าที่บันทึกในงานเดิมบนเครื่องเดิม

---


> **คำเตือน:** ตัวเลขทั้งหมดในเอกสารนี้เป็น **ค่าประมาณระดับ order-of-magnitude จากสมมติฐาน (ASSUMPTION)** ไม่ใช่ผลการวัด ขนาดข้อมูลจริง **UNKNOWN** (ต้องได้จาก D0-2) และ throughput ต้องวัดจริงใน **engineering smoke test** บนข้อมูลสังเคราะห์/สาธารณะที่ไม่มีข้อมูลส่วนบุคคล (ทำได้ก่อนผ่าน gate เพราะไม่ใช่การทดลองทางวิทยาศาสตร์และไม่แตะข้อมูลจริง) แล้วแทนค่าในตารางนี้

## 1. สมมติฐานฐาน (ASSUMPTIONS)

| รหัส | สมมติฐาน | ค่า |
|---|---|---|
| A1 | ฮาร์ดแวร์ CPU | workstation 8 cores, RAM 32 GB |
| A2 | ฮาร์ดแวร์ GPU (เฉพาะ conditional) | 1× GPU ระดับ 16 GB VRAM (เช่น T4/A4000 class) |
| A3 | Candidate budget | k* = 20 คู่ต่อบัญชีฝั่ง B |
| A4 | Text attributes ที่ embed | 2 (display name, bio) ต่อบัญชี |
| A5 | Lexical features | ~30–40 ต่อคู่ |
| A6 | Throughput string features | 5,000–20,000 คู่/วินาที/core (rapidfuzz, vectorized) |
| A7 | Frozen MiniLM encoding | CPU 200–1,000 ข้อความ/วินาที; GPU 2,000–5,000 ข้อความ/วินาที |
| A8 | GBDT fit | ~5 วินาที ต่อ 100k แถว×40 features (8 cores), โตเกือบเชิงเส้นตามแถว |
| A9 | Search budget | B_search = 200 configs × 4 development folds; ablation ใช้ hyperparameter ตรึง |
| A10 | Cross-encoder fine-tune (MiniLM-L12, max_len 128) | train 300–600 คู่/วินาที, infer 1,000–2,000 คู่/วินาที บน A2 |
| A11 | Bootstrap | 10,000 resamples × 5 primary contrasts; 2,000 สำหรับรายการอื่น |

## 2. Scenario ขนาดข้อมูล

| Scenario | บัญชีต่อแพลตฟอร์ม | |C(k*)| ≈ N_B × k | ข้อความที่ต้อง embed |
|---|---|---|---|
| S (small) | 5,000 | 100,000 คู่ | 20,000 |
| M (medium) | 50,000 | 1,000,000 คู่ | 200,000 |
| L (large) | 500,000 | 10,000,000 คู่ | 2,000,000 |

## 3. ประมาณต้นทุนต่อ Track (core program)

| Track / Exp | S | M | L | หมายเหตุ |
|---|---|---|---|---|
| D0 audits | คน: ~3–5 วันทำงาน (dual annotation 200+200 คู่) | เท่ากัน | เท่ากัน | ต้นทุนหลักเป็นแรงคน ไม่ใช่ compute |
| E1-1/E1-2 blocking | < 1 นาที CPU | นาที | 10–60 นาที | |
| E1-3 TF-IDF kNN (sparse) | < 1 นาที | 5–30 นาที | ชั่วโมง; อาจต้อง MinHash/LSH | |
| E1-4 dense encode + kNN | encode 20 วินาที–2 นาที CPU; kNN exact วินาที | encode 3–17 นาที CPU; kNN exact นาที | encode 0.5–3 ชม. CPU (หรือ 7–17 นาที GPU); ต้อง HNSW | exact kNN ที่ L ≈ 10^14 FLOPs → ใช้ ANN |
| E2-1 features | วินาที–นาที | 1–4 นาที (8 cores) | 10–40 นาที | |
| E2-3 tuned rule | นาที | < 1 ชม. | ชั่วโมง | vectorized |
| E3-1 LR (200×5 fits) | นาที | < 1 ชม. | ไม่กี่ชั่วโมง | |
| E3-2 GBDT tuning (200×5 fits) | ~1–2 CPU-ชม. | ~15–20 CPU-ชม. | ~150–200 CPU-ชม. (ต้องลด: successive halving / subsample) | ขั้นที่แพงที่สุดของ core |
| E5-3 GBDT tuning | เท่ากับ E3-2 | เท่ากับ E3-2 | เท่ากับ E3-2 | |
| E5 ablations (~10 feature sets × 5 folds × 5 seeds, hyperparams ตรึง) | ~0.5 ชม. | ~4–8 ชม. | ~40–80 ชม. | |
| E6 policies (GA/TPE 2,000 evals × 10 seeds) | วินาที–นาที | นาที | < 1 ชม. | evaluation บน score vector |
| E7 bootstrap + reporting | นาที | < 1 ชม. | ชั่วโมง | |
| **รวม core (MVP)** | **≈ 5–10 CPU-ชม.** | **≈ 50–80 CPU-ชม.** | **≈ 500+ CPU-ชม. (ต้องออกแบบใหม่เพื่อ scale)** | ไม่มี GPU |

## 4. ต้นทุน conditional / optional

| Exp | S | M | หมายเหตุ |
|---|---|---|---|
| E4-3 bi-encoder fine-tune (3 seeds) | ~0.5–1 GPU-ชม. | ~2–5 GPU-ชม. | |
| E4-4 cross-encoder MiniLM (3 seeds; train ~200k คู่หลัง downsample, 3 epochs) | ~0.5 GPU-ชม. | ~2–4 GPU-ชม. | ถ้าใช้ XLM-R base คูณ ~3–4 |
| E4-4 inference บน C(k*) ของ test | นาที | ~10–20 นาที GPU | cross-encoder ไม่เหมาะกับ L บน CPU |
| E4-5 local LLM (บน sample 2,000 คู่) | ~1–3 GPU-ชม. | เท่ากัน (ใช้ sample) | BLOCKED by G1 |
| E8-3 privacy attacks | ชั่วโมง CPU | ชั่วโมง CPU | ต้อง ethics |
| E9-1 image embedding | ~0.2 GPU-ชม. | ~1–2 GPU-ชม. | ต้องสิทธิ์ภาพ |

## 5. ต้นทุน inference (สำหรับ E7-5 และการตัดสิน H3)

ตัวชี้วัดที่ต้องวัดจริง: **ms ต่อ 1,000 คู่ ต่อ stage**, เวลา build index, peak RAM/VRAM

ค่าคาดการณ์เชิงสัมพัทธ์ (ASSUMPTION, ต้องวัด): lexical features ≈ 1×; + frozen semantic (embedding cache ต่อบัญชี, cosine ต่อคู่) ≈ 1–2× เมื่อ embed ล่วงหน้า; cross-encoder ≈ 100–1,000× ของ lexical บน CPU — ดังนั้น H3b ต้องชนะด้วยผลที่มากพอจะคุ้มต้นทุน (รายงาน cost ratio คู่กับ ΔPR-AUC เสมอ)

## 6. Storage และ artifacts

- Embedding cache: 384 dims × float32 × 2 attrs ≈ 3 KB/บัญชี → M: ~300 MB; L: ~3 GB
- Candidate pairs + features (parquet): M ~ 0.2–0.5 GB; L ~ 2–5 GB
- Logs/ledger/configs: เล็กมาก
- **ข้อมูลส่วนบุคคลต้องเก็บบนเครื่อง/คลังที่ผ่าน G1 เท่านั้น** ห้าม sync ขึ้น public repo หรือบริการคลาวด์ที่ไม่ได้อนุมัติ

## 7. งบเวลา (calendar) โดยประมาณสำหรับ Scenario M

| ช่วง | งาน | เวลา (ASSUMPTION) |
|---|---|---|
| สัปดาห์ 0–2 | G0–G2 (provenance, data-use, D0-1…D0-3) | ขึ้นกับผู้อนุมัติ — **ปัจจัยเสี่ยงหลัก** |
| สัปดาห์ 2–3 | G3 split freeze, D0-4, smoke test, G4 pre-registration | 1 สัปดาห์ |
| สัปดาห์ 3–4 | T1, T2 | 1 สัปดาห์ |
| สัปดาห์ 4–6 | T3, T4 (frozen), T5 | 2 สัปดาห์ |
| สัปดาห์ 6–7 | T6 | 1 สัปดาห์ |
| สัปดาห์ 7–8 | G5 → T7 (เปิด test ครั้งเดียว), error analysis | 1–2 สัปดาห์ |
| ภายหลัง | T4 conditional, T8–T10 | ตามผล inclusion rules |

## 8. การลดต้นทุนถ้าข้อมูลใหญ่ (Scenario L)

1. Successive halving / Hyperband แทน grid; tune บน subsample 20% ของ identity แล้วยืนยันบนเต็ม
2. ANN (HNSW) แทน exact kNN — รายงาน recall ของ ANN เทียบ exact บน sample
3. ลด k* หลังเห็นเส้น PC–|C| บน validation
4. ตัด E1-2 หรือ E3-3 ออก

## 9. ข้อมูลที่ต้องเติม (UNKNOWN)

ขนาดจริงของแต่ละแพลตฟอร์ม, จำนวน attribute, ภาษา, ฮาร์ดแวร์ที่มีจริง, งบ GPU (ถ้ามี) — เมื่อได้แล้วให้แก้ตาราง §2–§4 และบันทึกเวอร์ชัน


---

## 10. Scenario "R" (ขนาดจาก repository) — แทน §2–§3 สำหรับการวางแผน (เวลา = ASSUMPTION)

| รายการ | ค่า | สถานะ |
|---|---|---|
| โปรไฟล์ / entities | 36,807 / 15,297 | V-REPO (schema) |
| Candidate pairs (B0, ทั้งกราฟ) | ≈ 2.09M | HIST (V-REPO doc) |
| Candidate pairs ภายใน fold (5 entity folds) | ≈ 0.60M | HIST (Gate 5 technical) |
| Positive ทั้งหมด / ที่ B0 ครอบคลุม | 29,243 / 25,931 | V-REPO (นับจาก schema / BACKUP preflight) |
| ข้อความที่ embed | ≤ 110k (36,807 × ≤3 attribute) | คำนวณ |

| Track | ประมาณการ (ASSUMPTION) |
|---|---|
| E1-1/E1-3/E1-4/E1-5 | นาที–<1 ชม. CPU รวม (ASSUMPTION) |
| E2-1 features บน ~0.6M คู่ | 1–5 นาที CPU (ASSUMPTION) |
| E2-3 + E3-2 tuning (800 fits ต่อชุด) | 5–20 CPU-ชม. ต่อ learner×feature set (ASSUMPTION; GB ของ sklearn ช้ากว่า HistGB/LightGBM มาก) |
| E5-3, E4-2 tuning | เท่ากับ E3-2 ต่อชุด (ASSUMPTION) |
| E5-4 + E5-5 (300 fits, hyperparameter ตรึง) | 3–10 CPU-ชม. (ASSUMPTION) |
| T6 (≈82k policy evaluations บน score vector ~0.5M แถว) | < 1 ชม. CPU (ASSUMPTION) |
| T7 bootstrap (10,000 × 5 contrasts) | < 1 ชม. (ASSUMPTION) |
| **รวม MVP** | **≈ 30–80 CPU-ชม.; 0 GPU-ชม. (ASSUMPTION)** |
| CONDITIONAL E4-3/E4-4 | ≈ 4–10 GPU-ชม. (ASSUMPTION) |
