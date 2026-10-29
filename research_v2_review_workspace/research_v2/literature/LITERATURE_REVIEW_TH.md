# Literature Review — Cross-platform Social Media Identity Resolution (Research V2, v2 verified)

## Changes vs v1

| # | การเปลี่ยนแปลง | หลักฐาน |
|---|---|---|
| L1 | ทั้ง 35 รายการตรวจซ้ำ → V-LIT-WEB ทั้งหมด (16 รายการ V-LIT-KNOWN เดิมยืนยันผ่าน Crossref/DataCite/publisher) | `review/LITERATURE_VERIFICATION_REPORT.md` §1 |
| L2 | P01 DOI 10.1109/ACCESS.2024.3500374 **ยืนยันแล้ว** (IEEE Access 12:171241–171268) | Crossref |
| L3 | P04 ปี 2021 → **2020** (PVLDB 14(1) issue Sept 2020; นำเสนอ VLDB 2021) | Crossref |
| L4 | P10 = Information Systems 120:102307 (Feb 2024); P19/P30/P31 เพิ่ม DOI; P28 DOI 10.1016/j.eswa.2025.129026, ESWA 296:129026, **7 ผู้แต่ง**; รายละเอียด "unsupervised + K-Means" ของ P28 = UNCONFIRMED | Crossref/OpenAlex |
| L5 | P05 claim (textual/dirty) **ยืนยันจากฉบับเต็ม**; P08 model list (DeepMatcher, DITTO, EMTransformer, HierGAT) **ยืนยัน** แต่ข้อความ "test-time heterogeneity แย่กว่า training noise" เป็นจริงเฉพาะ granularity heterogeneity → PARTIAL | `review/_work/agentB/LIT_NOTES.md` §1, §3 |
| L6 | **P34 REINSTATED**: Min, Luo, Liu, Gong, Chen (2026) CMC 86(2):1–23, DOI 10.32604/cmc.2025.073175 — ใช้เป็น survey context เท่านั้น | Crossref + publisher page |
| L7 | เพิ่ม 14 งาน (P36–P49) ตาม gap ที่ระบุ — §11 ใหม่ | `literature/PAPER_EVIDENCE_MATRIX.csv` |
| L8 | ตัดสมมติฐาน "ภาษาไทย/ผสม" ออกจากข้อสรุปเชิงออกแบบ: ข้อมูลโครงการคือ LinkSocial [P38] และไม่มีหลักฐาน literature/repo ว่ามีภาษาไทย | [P38]; `review/RESEARCH_GAP_VALIDATION.md` G-4 |
| L9 | เพิ่มการเชื่อม L1 (literature) ↔ L2 (repo) ใน `review/LITERATURE_VS_IMPLEMENTATION.md` | — |

---


เวอร์ชัน: 0.1 (ร่างสำหรับ Phase 2 Design) · วันที่จัดทำ: 2026-10-25 · สถานะงานวิจัย: **NO-GO สำหรับการทดลองทางวิทยาศาสตร์** (ดู `design/RESEARCH_GATES.md`)

---

## 0. ป้ายสถานะหลักฐาน (ใช้ทุกเอกสารใน `research_v2/`)

| ป้าย | ความหมาย |
|---|---|
| **V-LIT-WEB** | VERIFIED literature evidence — ตรวจเมทาดาทา (ชื่อเรื่อง ผู้แต่ง ปี แหล่งตีพิมพ์ และ DOI ถ้ามีระบุ) จากแหล่งต้นทาง (สำนักพิมพ์ / arXiv / dblp / คลังสถาบัน) ในรอบนี้ |
| **V-LIT-KNOWN** | งานรากฐานที่มีเมทาดาทามาตรฐานเป็นที่รู้จักแพร่หลาย แต่ **ยังไม่ได้ตรวจซ้ำในรอบนี้** ต้องตรวจกับ Crossref/dblp ก่อนใช้ในเล่มวิทยานิพนธ์ |
| **V-REPO** | VERIFIED repository evidence — ตรวจจากไฟล์ใน repository จริง |
| **HIST-UNVERIFIED** | ผลลัพธ์ทางประวัติศาสตร์ที่ยังไม่ผ่านการตรวจซ้ำ ห้ามใช้เป็นข้อสรุปของ V2 |
| **PROPOSED** | การทดลองใหม่ที่เสนอ ยังไม่มีผลลัพธ์ |
| **UNKNOWN / BLOCKED** | ไม่ทราบ หรือถูกปิดกั้นด้วย gate / การเข้าถึง |

> **ข้อจำกัดสำคัญของรอบนี้ (ต้องอ่านก่อน):** ผู้จัดทำ **ไม่สามารถเข้าถึง** `PGTNiiZ/Project-for-Work`, `PGTNiiZ/Project-for-Work-private-backup`, โฟลเดอร์ `research_v2/` เดิม, เอกสาร Phase 1 audit และเอกสาร ICSEC ได้ในเซสชันนี้ ดังนั้น **ไม่มีหลักฐานประเภท V-REPO ในเอกสารชุดนี้เลย** ข้อมูลประวัติ R0–R6 ทั้งหมดมาจากสรุปที่ผู้ใช้ให้มา และติดป้าย HIST-UNVERIFIED ทุกจุด งานแมปประวัติศาสตร์ (`history/`) จึงเป็น "แม่แบบที่ต้องเติมจาก repo" ไม่ใช่การยืนยัน

---

## 1. ขอบเขตและวิธีการทบทวน

**คำถามนำ:** (Q-a) งานวิจัยปัจจุบันนิยามและประเมินปัญหาการเชื่อมโยงตัวตนข้ามแพลตฟอร์มอย่างไร (Q-b) องค์ประกอบใดของ pipeline (blocking, representation, learning, decision) ที่มีหลักฐานว่าส่งผลต่อคุณภาพ (Q-c) แนวปฏิบัติการประเมินใดที่ทำให้ผลสูงเกินจริง (Q-d) ความเสี่ยงด้านความเป็นส่วนตัวของเทคนิคที่โครงการเดิมใช้ (Bloom filter)

**วิธีค้น:** เริ่มจากงานแกน 5 ชิ้นที่กำหนด แล้วขยายแบบ backward/forward snowballing ไปยัง (i) survey UIL (ii) deep / PLM-based entity matching (iii) blocking และ meta-blocking (iv) ระเบียบวิธีประเมิน record linkage (v) privacy-preserving record linkage (PPRL) (vi) ระเบียบวิธีทางสถิติและการรั่วไหลของข้อมูล ช่วงปีหลัก 2018–2026 พร้อมงานรากฐาน

**เกณฑ์คัดเข้า:** ตีพิมพ์ใน venue ที่มี peer review (หรือ arXiv ที่ต่อมาตีพิมพ์), เกี่ยวข้องกับอย่างน้อยหนึ่ง Track, และตรวจสอบเมทาดาทาได้ **เกณฑ์คัดออก:** งานที่ยืนยันการมีอยู่ไม่ได้ (ดู P34), บทความบล็อก/Medium, และงานที่อ้างผลโดยไม่มีวิธีการ

**สรุปจำนวน (v2):** 49 รายการ = 35 เดิม (ตรวจซ้ำทั้งหมด → V-LIT-WEB; P34 reinstated) + 14 ใหม่ (P36–P49) — ไม่มีรายการ UNVERIFIED ที่ใช้เป็นหลักฐาน; เนื้อหาของ P36 และ abstract ของ P28 = UNCONFIRMED

**ข้อควรระวังเชิงระเบียบวิธี:** Literature ทำหน้าที่ *ให้เหตุผลว่าควรทดสอบอะไรและอย่างไร* ไม่ใช่หลักฐานว่าสมมติฐานของเราจะเป็นจริงบนข้อมูลของเรา งานด้าน Entity Matching (EM) ส่วนใหญ่ประเมินบน benchmark สินค้า/บรรณานุกรม ซึ่งต่างจากโปรไฟล์โซเชียลมีเดียทั้งด้านโครงสร้าง ภาษา และพฤติกรรมของผู้ใช้ (เช่น การตั้งชื่อเลียนแบบ การจงใจไม่ให้เชื่อมโยง)

---

## 2. การวางตำแหน่งปัญหา: UIL, EM และ ER

- **User Identity Linkage (UIL)** คือการตัดสินว่าบัญชีบนแพลตฟอร์มต่างกันเป็นของบุคคลเดียวกันหรือไม่ โดยใช้ข้อมูลโปรไฟล์ เนื้อหา พฤติกรรม หรือโครงข่าย [P01, P02] ปัญหานี้มีชื่อเรียกหลายแบบ เช่น User Identity Resolution, Profile Linkage, Anchor Link Prediction [P01]
- **Entity Matching (EM)** คือขั้นตอนตัดสินคู่ระเบียนว่าอ้างถึงสิ่งเดียวกันหรือไม่ ส่วน **Entity Resolution (ER)** ครอบคลุมทั้ง blocking + matching + (บางครั้ง) clustering [P04, P12, P17]
- **ความหมายต่อ V2:** โครงการของเราเป็น *profile-based UIL* ที่ใช้เครื่องมือแบบ EM (pairwise features → classifier → threshold) จึงต้องยืมทั้งระเบียบวิธี EM (blocking/matching แยกขั้น) และข้อพิจารณาเฉพาะ UIL (ความไม่สม่ำเสมอของโปรไฟล์, ข้อจำกัด API, ความเป็นส่วนตัว)

---

## 3. งานแกน 5 ชิ้น (Core Papers)

### P01 — Senette, Siino & Tesconi. *User Identity Linkage on Social Networks: A Review of Modern Techniques and Applications.* IEEE Access, 2024. — **V-LIT-WEB** (v2: DOI 10.1109/ACCESS.2024.3500374, 12:171241–171268 ยืนยันแล้ว)

- **ยืนยันแล้ว:** ชื่อเรื่อง ผู้แต่ง ปี 2024 และวารสาร IEEE Access (คลังมหาวิทยาลัย Catania และ IIT-CNR), preprint arXiv:2409.08966
- **ยังไม่ยืนยัน:** DOI `10.1109/ACCESS.2024.3500374` ที่ปรากฏในเอกสารสรุปเดิม — ค้นแล้วไม่พบการยืนยันจากแหล่งต้นทาง ต้องตรวจจาก IEEE Xplore ก่อนอ้าง
- **สาระ:** ทบทวนงาน UIL ตั้งแต่ปี 2016 ถึงปัจจุบัน ครอบคลุมการนิยามปัญหา (จำกัดเหลือสองรูปแบบที่พบบ่อย), วิธีสกัดคุณลักษณะ, อัลกอริทึม/โมเดล, ชุดข้อมูล และ metrics และชี้ว่าการขาดชุดข้อมูลที่ครบถ้วน รวมถึงนโยบายการเข้าถึง API ที่เข้มงวดขึ้นด้วยเหตุผลด้านความเป็นส่วนตัว เป็นอุปสรรคของสาขา
- **ข้อจำกัด:** เป็น survey จึงไม่ให้ผลเปรียบเทียบภายใต้ protocol เดียวกัน
- **นำไปใช้:** กรอบแนวคิดของ Literature Review, การนิยามปัญหา (RQ0), การเลือก metrics และเหตุผลของ gate ด้าน data-use → **T2, T5, T7, G1**

### P04 — Li, Li, Suhara, Doan & Tan. *Deep Entity Matching with Pre-Trained Language Models (Ditto).* PVLDB 14(1):50–60, 2020 (issue Sept 2020; นำเสนอที่ VLDB 2021; v2 แก้ปี). DOI: 10.14778/3421424.3421431 — **V-LIT-WEB**

- **หมายเหตุเมทาดาทา:** prompt เดิมระบุ "VLDB, 2020" แต่ฉบับตีพิมพ์คือ PVLDB เล่ม 14 ปี 2021 (arXiv:2004.00584 ส่งเมื่อ 2020)
- **วิธี:** มอง EM เป็น sequence-pair classification โดย serialize ระเบียนสองรายการแล้ว fine-tune PLM (BERT, DistilBERT, RoBERTa) พร้อมเทคนิคเสริม 3 อย่าง: ใส่ domain knowledge, summarization ของสตริงยาว, data augmentation
- **ผลที่รายงาน (บน benchmark ของผู้แต่ง):** ดีกว่า SOTA เดิมสูงสุดราว 29 จุด F1 และได้ F1 96.5% บนงานจับคู่บริษัทขนาดใหญ่
- **ข้อจำกัดเมื่อใช้กับ V2:** benchmark เป็นข้อมูลสินค้า/บรรณานุกรมที่ผ่าน blocking แล้วและมีสัดส่วน positive สูงกว่าความเป็นจริง (ดู P07); ต้องใช้ GPU และข้อมูลฝึกที่มี label
- **นำไปใช้:** เป็นแม่แบบของ cross-encoder ใน **E4-4** (เงื่อนไข) — ไม่ใช่หลักฐานว่า Transformer จะดีที่สุดบนข้อมูลเรา

### P07 — Wang, Lin, Fu, Han, Sun, Xiong, Chen, Lu & Zhu. *Bridging the Gap between Reality and Ideality of Entity Matching: A Revisiting and Benchmark Re-Construction.* IJCAI 2022, pp. 3978–3984. DOI: 10.24963/ijcai.2022/552 — **V-LIT-WEB**

- **วิธี:** สร้าง corpus ใหม่และสร้าง benchmark ใหม่แบบทีละขั้น โดยเปลี่ยนสมมติฐานโดยนัยสามข้อของ benchmark เดิม คือ restricted entities → open entities, balanced labels → imbalanced labels, single-modal → multi-modal
- **ข้อค้นพบหลัก:** สมมติฐานของ benchmark เดิมไม่สอดคล้องกับสภาพแวดล้อมเปิด ทำให้ซ่อนความท้าทายหลักของงานและประเมินความก้าวหน้าของ EM **สูงเกินจริงอย่างมีนัยสำคัญ**; โค้ดและข้อมูลเผยแพร่ที่ github.com/tshu-w/ember
- **นำไปใช้ (สำคัญที่สุดต่อระเบียบวิธี V2):** (1) ต้องประเมินที่ class prior สมจริง (**E7-4**) (2) แยก candidate-level กับ end-to-end (**E7-1**) (3) ต้องมีการแบ่งข้อมูลแบบ entity-disjoint (**G3**) (4) เป็นเหตุผลของ T9 (multimodal) แบบมีเงื่อนไข

### P10 — Gagliardelli, Papadakis, Simonini, Bergamaschi & Palpanas. *GSM: A Generalized Approach to Supervised Meta-blocking for Scalable Entity Resolution.* Information Systems (Elsevier). DOI: 10.1016/j.is.2023.102307 — **V-LIT-WEB** (v2: vol. 120, art. 102307, 2024)

- **บริบท:** ฉบับวารสารที่ขยายจาก P11 (*Generalized Supervised Meta-blocking*, PVLDB 15(9):1902–1910, 2022, DOI 10.14778/3538598.3538611)
- **วิธี:** schema-agnostic blocking ให้ recall สูงแต่สร้างคู่ที่ไม่เกี่ยวข้องจำนวนมาก; meta-blocking ให้น้ำหนักคู่จากรูปแบบ co-occurrence ในบล็อกแล้วตัดคู่น้ำหนักต่ำ; supervised meta-blocking รวมหลาย weighting scheme เป็น feature vector ให้ binary classifier และ GSM ใช้ probabilistic classifier เพื่อให้คะแนนที่ใช้กับ pruning algorithm ใดก็ได้ พร้อมศึกษา feature set ที่เหมาะสมและขนาด training set ขั้นต่ำ
- **ข้อจำกัดต่อ V2:** ประเมินบน benchmark ER ทั่วไป ไม่ใช่โปรไฟล์โซเชียล; ต้องมี label สำหรับฝึก pruning classifier
- **นำไปใช้:** กรอบคิดของ **T1** (การแลก recall กับจำนวนคู่), metric PC/PQ/RR, และ **E1-6** (supervised meta-blocking, optional)

### P08 — Moslemi, Mousavi, Behkamal & Milani. *Heterogeneity in Entity Matching: A Survey and Experimental Analysis.* Data & Knowledge Engineering 164:102575, July 2026. DOI: 10.1016/j.datak.2026.102575 — **V-LIT-WEB**

- **สาระ:** เสนอ taxonomy ของความแตกต่าง (heterogeneity) สองกลุ่มหลักคือ representation และ semantic heterogeneity, ทบทวนวิธี EM ผ่านเลนส์นี้, เผยแพร่ benchmark สำหรับทดสอบ semantic heterogeneity และทดลองกับโมเดล SOTA ในประเด็น synonym variation, granularity และ dirty/noisy data; ข้อค้นพบเด่นคือความแตกต่างที่เกิดตอน test ส่งผลเสียมากกว่า noise ตอน train
- **ข้อควรระวัง:** เอกสารเดิมระบุชื่อโมเดลที่ทดสอบ (DeepMatcher, Ditto, EMTransformer, HierGAT) — **ยังไม่ได้ตรวจรายชื่อจากเนื้อหาเต็ม** อย่าอ้างรายชื่อนี้จนกว่าจะตรวจ
- **นำไปใช้:** ออกแบบ robustness strata ใน **E7-3** (transliteration ไทย–อังกฤษ, คำพ้อง, ข้อมูลสกปรก) และเหตุผลว่าต้องรายงานผลแยกตาม platform pair

---

## 4. Candidate Generation และ Blocking (T1, H5)

- **P12 Papadakis et al., ACM CSUR 53(2), 2020 (DOI 10.1145/3377455) — V-LIT-WEB:** จัดระเบียบเทคนิคด้านประสิทธิภาพของ ER เป็น Blocking, Filtering และ hybrid ใช้เป็นแหล่งนิยาม Pair Completeness (PC), Pairs Quality (PQ), Reduction Ratio (RR) และ token blocking / block purging
- **P13 Thirumuruganathan et al. (DeepBlocker), PVLDB 14(11):2459–2472, 2021 (DOI 10.14778/3476249.3476294) — V-LIT-WEB:** นิยาม design space ของ DL-based blocking และพัฒนา 8 แบบที่ **ไม่ต้องใช้ label**; พบว่าแบบที่ดีที่สุดชนะวิธีเดิมบนข้อมูล dirty/textual และ *ใกล้เคียง* บนข้อมูล structured และการรวม DL กับ non-DL ให้ผลดีขึ้นอีก → เหตุผลของ **E1-4 (dense)** และ **E1-5 (hybrid)** และเหตุผลว่าทำไมต้องคง lexical baseline ไว้
- **P14 Zeakis et al., PVLDB 16(9):2225–2238, 2023 (DOI 10.14778/3598581.3598594) — V-LIT-WEB:** ทดลองโมเดลภาษา 12 ตัวบน 17 benchmark ประเมิน vectorization overhead, blocking ด้วย kNN บน embedding (FAISS) และ matching ทั้ง supervised/unsupervised → เหตุผลของการวัด **ต้นทุน embedding** (E7-5) และการใช้ kNN top-k เป็นตัวควบคุม candidate budget
- **P10/P11 (GSM)** — ดูข้างบน
- **ข้อสรุปเชิงออกแบบ:** Literature สนับสนุนว่า (1) ต้องประเมิน blocking ด้วย recall ของคู่จริง *และ* ขนาด candidate set พร้อมกัน (2) การเปรียบเทียบ dense กับ sparse ต้องคุม budget k ให้เท่ากัน (3) hybrid เป็นทางเลือกที่ควรทดสอบ — แต่ไม่มีงานใดในชุดนี้ทดสอบบนโปรไฟล์โซเชียลข้ามแพลตฟอร์มแบบ LinkSocial (v2: ตัดคำว่า "ภาษาไทย/ผสม" เพราะไม่มีหลักฐานว่าข้อมูลมีภาษาไทย); top-k TF/IDF เป็น baseline ที่แข็งแรง [P45]

---

## 5. Representation, Learned Matching และ Semantic Models (T2–T5, H1–H3)

- **P16 Fellegi & Sunter, JASA 1969 — V-LIT-WEB (v2 re-checked):** กรอบความน่าจะเป็นของ record linkage ที่แยก match / possible match (clerical review) / non-match → รากฐานของทั้ง rule-based baseline (**E2-4**) และ three-way decision (**E6-6**)
- **P17 Christen, *Data Matching*, Springer 2012 — V-LIT-WEB (v2 re-checked):** ตำราอ้างอิง similarity functions (Jaro–Winkler, edit distance, q-gram) และ pipeline มาตรฐาน → **T2**
- **P05 Mudgal et al., SIGMOD 2018 (DeepMatcher) — V-LIT-WEB (v2 re-checked):** design space ของ DL-based EM; เป็นที่รู้จักว่าได้ประโยชน์มากบนข้อมูล textual/dirty มากกว่า structured (v2: ยืนยันจากฉบับเต็ม — DL ชนะบน textual/dirty; บน structured ใกล้เคียง ไม่ดีกว่า; 'dirty' = ค่าที่ถูกย้าย attribute แบบสังเคราะห์) → ใช้เป็นเหตุผลเชิงคุณภาพว่าทำไม H3 อาจได้ผลต่างกันตามชนิด attribute (bio vs username)
- **P06 Brunner & Stockinger, EDBT 2020 — V-LIT-WEB (v2 re-checked):** ใช้ Transformer กับ EM ในช่วงเดียวกับ Ditto (Ditto อ้างถึงว่าเป็นงานคู่ขนาน — V-LIT-WEB ผ่าน P04)
- **P04 Ditto** — ดูข้างบน → **E4-4**
- **P15 Reimers & Gurevych, EMNLP-IJCNLP 2019 (Sentence-BERT) — V-LIT-WEB (v2 re-checked):** bi-encoder แบบ siamese สำหรับ sentence embedding ที่คำนวณ cosine ได้เร็ว → เหตุผลของ **E4-1** (frozen bi-encoder, เช่น MiniLM) และ E1-4
- **P14 Zeakis et al.** — ให้หลักฐานว่าต้นทุนและคุณภาพของ embedding ต่างกันมากตามโมเดลและข้อมูล → ไม่ควรสมมติว่าโมเดลใหญ่ดีกว่าเสมอ
- **P09 Peeters, Steiner & Bizer, EDBT 2025, pp. 529–541 (DOI 10.48786/edbt.2025.42) — V-LIT-WEB:** ศึกษา LLM ทั้ง hosted และ open-source สำหรับ EM; รายงานว่าไม่มี prompt เดียวที่ดีที่สุด ต้องปรับตามโมเดล/ชุดข้อมูล, LLM ที่ดีที่สุดใช้ตัวอย่างฝึกน้อยหรือไม่ใช้เลยแต่ได้ผลใกล้ PLM ที่ fine-tune ด้วยตัวอย่างหลายพัน และทนต่อ entity ที่ไม่เคยเห็นได้ดีกว่า → **E4-5 (optional, BLOCKED โดย data-use gate หากต้องส่งข้อมูลส่วนบุคคลไป API ภายนอก)**
- **P08 Moslemi et al.** — ความทนทานต่อ heterogeneity → E7-3
- **UIL-specific:** P02 Shu et al. (SIGKDD Explorations 18(2), 2017, DOI 10.1145/3068777.3068781 — V-LIT-WEB) สรุปว่าข้อมูลตัวตนบนแต่ละแพลตฟอร์มของคนเดียวกันอาจต่างกันมาก และข้อมูลโซเชียลมีขนาดใหญ่ มี noise ไม่ครบ และไม่มีโครงสร้าง; P03 Zafarani & Liu (KDD 2013, MOBIUS — V-LIT-WEB v2) ใช้คุณลักษณะเชิงพฤติกรรมของการตั้งชื่อผู้ใช้ → เหตุผลของ H1 (username เดี่ยวไม่พอ) และ per-attribute feature ใน **E2-1**; P28 Peng et al. (DECTUIL, ESWA 296:129026, 2026, DOI 10.1016/j.eswa.2025.129026, 7 ผู้แต่ง — V-LIT-WEB; รายละเอียด unsupervised/K-Means = UNCONFIRMED เพราะเข้าถึง abstract ไม่ได้) เป็น UIL ที่ใช้ three-way decision → อ้างเป็นแรงจูงใจของ three-way decision ใน UIL เท่านั้น ไม่ใช่ baseline โดยตรง (ปัญหาและข้อมูลต่างกัน)

---

## 6. Decision Policy, Cost-sensitive Matching และการประเมิน (T6–T7, H4)

- **P24 Elkan, IJCAI 2001 — V-LIT-WEB (v2 re-checked):** threshold ที่เหมาะสมตามต้นทุนคำนวณได้จาก probability ที่ calibrate แล้ว (p* = c_FP / (c_FP + c_FN) ในกรณีต้นทุนคงที่) → **E6-3** คือ baseline เชิงวิเคราะห์ที่ GA ต้องชนะ
- **P25 Chow, IEEE Trans. IT 1970 — V-LIT-WEB (v2 re-checked):** reject option / error–reject trade-off → **E6-6** (match/review/non-match)
- **P26 Niculescu-Mizil & Caruana, ICML 2005 — V-LIT-WEB (v2 re-checked):** classifier หลายชนิดให้ probability ที่ไม่ calibrate; Platt/isotonic → **E6-7** เป็นเงื่อนไขก่อน E6-3/E6-6
- **P18 Hand & Christen, Stat. Comput. 28(3):539–547, 2018 (DOI 10.1007/s11222-017-9746-6) — V-LIT-WEB:** ชี้ว่าเพราะ class imbalance สูงใน record linkage จึงใช้ accuracy ไม่ได้ และ F-measure มีจุดอ่อนเชิงแนวคิด: น้ำหนักสัมพัทธ์ระหว่าง precision กับ recall ควรมาจากปัญหาและผู้ใช้ ไม่ใช่จากวิธี linkage ที่ใช้ → V2 จะรายงาน F1 *ควบคู่* กับ precision/recall แยก, PR-AUC และ **expected cost ที่กำหนดล่วงหน้า** (ไม่ใช้ F1 ตัวเดียวเป็น primary สำหรับ H4)
- **P19 Hand, Christen & Kirielle, Mach. Learn. 110(3):451–456, 2021 (F*) — V-LIT-WEB (dblp):** การแปลง F-measure ที่ตีความได้ → secondary metric ทางเลือก
- **P23 Saito & Rehmsmeier, PLoS ONE 2015 — V-LIT-WEB (v2 re-checked):** PR plot ให้ข้อมูลมากกว่า ROC เมื่อข้อมูลไม่สมดุล → PR-AUC เป็น primary สำหรับ ranking quality
- **P07 Wang et al.** — class balance ที่ไม่สมจริงทำให้ผลสูงเกินจริง → E7-4

---

## 7. ระเบียบวิธีป้องกันอคติ (ใช้ทุก Track)

- **P20 Kaufman et al., ACM TKDD 2012 — V-LIT-WEB (v2 re-checked):** นิยามและการตรวจจับ data leakage → entity-disjoint split, ห้าม feature ที่ใช้ข้อมูลจาก label/อนาคต (**G3, D0-4**)
- **P21 Varma & Simon, BMC Bioinformatics 2006 — V-LIT-WEB (v2 re-checked):** การเลือกโมเดลด้วย CV ชุดเดียวกับที่ใช้ประเมินทำให้ error ต่ำเกินจริง → nested / held-out validation และ **test lock**
- **P22 Dietterich, Neural Computation 1998 — V-LIT-WEB (v2 re-checked):** การทดสอบทางสถิติเพื่อเปรียบเทียบ classifier (McNemar, 5×2cv) → paired comparison เป็นการทดสอบรองควบคู่ cluster bootstrap
- **P27 Elkan & Noto, KDD 2008 — V-LIT-WEB (v2 re-checked):** การเรียนรู้จาก positive + unlabeled → กรอบคิดสำหรับ "negative ที่ไม่แน่นอน" (**D0-3, E7-6**)
- **P33 Gebru et al., CACM 2021 (Datasheets for Datasets) — V-LIT-WEB (v2 re-checked):** แม่แบบ data dictionary / provenance (**G0, G2**)

---

## 8. ความเป็นส่วนตัว (T8)

- **P29 Schnell, Bachteler & Reiher, BMC Med. Inform. Decis. Mak. 9:41, 2009 (DOI 10.1186/1472-6947-9-41) — V-LIT-WEB:** เสนอ PPRL ด้วย Bloom filter บน q-gram ของ identifier ที่ทนต่อความผิดพลาดของการสะกด และมีภาระคำนวณต่ำ → แม่แบบของ R4/R5 เดิม
- **P35 Kroll & Steinmetzer, HEALTHINF 2015 — V-LIT-WEB; P30 Christen, Schnell, Vatsalan & Ranbaduge, PAKDD 2017, pp. 628–640 — V-LIT-WEB; P31 Vidanage, Christen, Ranbaduge & Schnell, CIKM 2020, pp. 1485–1494 — V-LIT-WEB:** สายงานโจมตี (cryptanalysis / graph matching) ที่แสดงว่า Bloom filter encoding สามารถถูกย้อน (re-identify) บางค่าได้ภายใต้เงื่อนไขที่กำหนด บางวิธีไม่ต้องรู้ฟังก์ชันหรือพารามิเตอร์การเข้ารหัส
- **P32 Vatsalan et al., Information Systems 2013 — V-LIT-WEB (v2 re-checked):** taxonomy ของ PPRL
- **ข้อสรุป:** การอ้างว่า R4/R5 "รักษาความเป็นส่วนตัว" **ไม่สามารถทำได้** หากไม่มี threat model และการประเมินการโจมตี → T8 ต้องมี **E8-3 (privacy attack evaluation)** จึงจะมีความหมายทางวิทยาศาสตร์
- **P34 Min et al., "From Identification to Obfuscation: A Survey of Cross-Network Mapping and Anti-Mapping Methods", CMC 86(2):1–23, 2026 — V-LIT-WEB (v2 REINSTATED):** survey ของ UIL mapping และ anti-mapping/obfuscation → ใช้เป็นบริบทด้าน privacy (G1/T8) เท่านั้น ไม่ใช้สำหรับข้ออ้างเชิงประจักษ์

---

## 9. สังเคราะห์: Literature บอกอะไรกับ V2 (และไม่ได้บอกอะไร)

**สิ่งที่ literature สนับสนุน (เป็นเหตุผลของการออกแบบ):**
1. แยก blocking ออกจาก matching และวัดทั้งสองระดับ [P07, P10, P12, P13]
2. ประเมินที่ class prior สมจริงและ entity แบบเปิด [P07, P18]
3. Semantic/PLM representation *อาจ* ช่วยกับข้อมูลที่เป็นข้อความหรือสกปรก แต่ประโยชน์ขึ้นกับชนิดข้อมูลและมีต้นทุน [P04, P13, P14]
4. Decision threshold ควรผูกกับต้นทุนที่กำหนดล่วงหน้า และ probability ต้อง calibrate [P18, P24, P26]
5. Bloom filter ไม่ได้รับประกันความเป็นส่วนตัวด้วยตัวเอง [P30, P31, P35]
6. Heterogeneity ช่วง test (เฉพาะ granularity) ทำให้ generalize ยากกว่าการเรียนจาก training ที่ heterogeneous; label noise ใน training ก็ลด AUC [P08] (v2: PARTIAL)

**สิ่งที่ literature ไม่ได้บอก (ต้องทดสอบเอง = ช่องว่าง):** ดู `RESEARCH_GAPS_TH.md` — โดยเฉพาะ (i) หลักฐานบนโปรไฟล์โซเชียลข้ามแพลตฟอร์ม (ภาษาขึ้นกับ D0-2) (ii) การแยกผลขององค์ประกอบ pipeline ใน UIL แบบ profile-based (iii) GA เทียบกับ optimizer ที่ไม่ใช่ GA ภายใต้ budget เท่ากัน (iv) ผลของ ground truth ไม่ครบต่อข้อสรุป

---

## 10. รายการที่ต้องตรวจเพิ่มก่อนใช้ในเล่ม

| รายการ | สิ่งที่ต้องทำ |
|---|---|
| P01 | ยืนยัน DOI ฉบับ IEEE Access จาก IEEE Xplore |
| P10 | ยืนยันเล่ม/ปี/หน้าบน ScienceDirect (ปีตีพิมพ์ฉบับเล่ม) |
| P28 | ยืนยัน DOI และเล่มของ DECTUIL |
| P08 | v2: ยืนยันแล้ว (DeepMatcher, DITTO, EMTransformer, HierGAT) |
| P05 | ตรวจข้อความเรื่องผลบนข้อมูล textual/dirty จากฉบับเต็ม |
| P34 | v2: ยืนยันแล้ว (REINSTATED) |
| V-LIT-KNOWN ทั้งหมด | ตรวจกับ Crossref/dblp แล้วเปลี่ยนป้ายเป็น V-LIT-WEB |
| งาน ICSEC เดิม | **BLOCKED** — ไม่มีสิทธิ์เข้าถึงในรอบนี้ |


## 11. งานที่เพิ่มใน v2 (P36–P49) — แต่ละงานเติม gap ที่ระบุ

| ID | งาน | Gap ที่เติม | ใช้กับ |
|---|---|---|---|
| P36 | Arford et al., IEEE ISI 2025, DOI 10.1109/ISI65680.2025.11201172 (เนื้อหา UNCONFIRMED) | ตรวจการอ้างอิงของ R6 [MAIN@1e0a2db:experiments/REPORT_R0_R5.md#L63-L67]; กรอบ de-anonymisation | G1, E4-3/E4-4 (บริบท) |
| P37 | Li et al., AAAI-21 35(15):13226–13233 (BERT-ER) — ยืนยันจากฉบับเต็ม | ตรวจการอ้างอิงของ R6; hash blocking + matching ร่วมกัน | E1-4, E4-4 |
| P38 | Sharma & Dyreson, ICBK 2018 (LINKSOCIAL), DOI 10.1109/ICBK.2018.00042 | **G0: แหล่งข้อมูลของโครงการ** (จำนวนโปรไฟล์ต่อแพลตฟอร์มตรงกันในระดับ 1–2 บัญชี) | D0-1, D0-2, G0 |
| P39 | Isele & Bizer, PVLDB 5(11) 2012 (GenLink) | H4: GP/evolutionary learning ของ linkage rule + threshold | E6-5 |
| P40 | de Carvalho et al., IEEE TKDE 24(3) 2012 | H4: GP สำหรับ dedup function | E6-5 |
| P41 | Bergstra & Bengio, JMLR 13 2012 (random search) | H4: baseline random search ที่ budget เท่ากัน | E6-4 |
| P42 | Bergstra et al., NeurIPS 2011 (TPE) | H4: baseline TPE | E6-4 |
| P43 | Geifman & El-Yaniv, NeurIPS 2017 (selective classification) | H4c: risk–coverage ของ review band | E6-6 |
| P44 | Gokhale et al., SIGMOD 2014 (Corleone) | human-in-the-loop EM | E6-6, D0-1 |
| P45 | Paulsen et al., PVLDB 16(6) 2023 (Sparkly) | H5: sparse top-k baseline ที่แข็งแรง | E1-3, E1-5 |
| P46 | Goga et al., KDD 2015 | H1: availability/consistency ของ attribute; การประเมิน UIL ที่ขนาดสมจริง; อคติของ self-declared GT | E5-5, E7-4, D0-1 |
| P47 | Papadakis et al., ICDE 2024 | benchmark ที่เกือบ linearly separable → วัด linear vs non-linear gap ก่อนอ้าง | E3-1, E3-2 |
| P48 | Köpcke et al., PVLDB 3(1-2) 2010 | H2: learned vs non-learned ER บนงานจริง | E2-3, E3-2 |
| P49 | Field & Welsh, JRSS-B 69(3) 2007 | cluster bootstrap สำหรับคู่ที่แชร์ entity | E7-1, E7-2 |

ช่องว่างที่ยังเหลือ (v2): ไม่พบงานที่เทียบ GA กับ random search/TPE ที่ budget เท่ากันสำหรับ threshold ของ record linkage — G-3 ยังเป็น contribution ที่เป็นไปได้ แต่ต้องค้นอย่างเป็นระบบ (Scopus/IEEE) ก่อนอ้าง [`review/_work/agentB/LIT_NOTES.md` §7]
