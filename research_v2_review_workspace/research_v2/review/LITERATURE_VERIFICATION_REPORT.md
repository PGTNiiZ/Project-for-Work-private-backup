# Literature Verification Report (Phase 4)

วันที่: 2026-10-25 · ผู้ตรวจ: Agent B (บันทึก `_work/agentB/LIT_NOTES.md`, ตาราง `_work/agentB/paper_verification.csv` 49 แถว) · Lead ตรวจทานและรวมเข้า `literature/PAPER_EVIDENCE_MATRIX.csv`, `literature/REFERENCES.bib`

แหล่งที่ใช้: Crossref `/works/<doi>` และ query API, OpenAlex, หน้า publisher/proceedings (OpenProceedings, IJCAI, JMLR, NeurIPS, AAAI OJS, Tech Science Press), arXiv, GitHub API — dblp และ Semantic Scholar ตอบ HTTP 429 เกือบทุกครั้ง จึง **ไม่ใช้ dblp เป็นหลักฐาน**

หมายเหตุการดำเนินงาน: Agent B หยุดก่อนส่งสรุปเพราะ API rate limit หลังเขียนไฟล์ผลครบแล้ว (`LIT_NOTES.md` ครบทุกหัวข้อ; CSV parse ได้ 49 แถว) — Lead ตรวจว่าไฟล์ครบ ไม่ได้เรียก agent ซ้ำ

## 1. สถานะ K4 (ข้อค้างจาก v1)

| Item | สถานะ | ผล / หลักฐาน |
|---|---|---|
| P01 DOI | **RESOLVED** | 10.1109/ACCESS.2024.3500374 ยืนยัน; IEEE Access 12:171241–171268 (Crossref) |
| P10 volume/year | **RESOLVED** | Information Systems 120:102307, Feb 2024 |
| P19 DOI | **RESOLVED** | 10.1007/s10994-021-05964-1 |
| P30 DOI | **RESOLVED** | 10.1007/978-3-319-57454-7_49 (PAKDD 2017, LNCS) |
| P31 DOI | **RESOLVED** | 10.1145/3340531.3411931 (CIKM 2020) |
| P28 DOI/volume | **RESOLVED (metadata) / PARTIAL (content)** | 10.1016/j.eswa.2025.129026; ESWA 296:129026; **7 ผู้แต่ง** (v1 ระบุ 4); abstract เข้าถึงไม่ได้ → "unsupervised/K-Means" = UNCONFIRMED |
| P05 textual/dirty claim | **RESOLVED – supported** | ฉบับเต็ม: DL ชนะบน textual และ dirty; structured ใกล้เคียงไม่ดีกว่า; "dirty" = ค่าถูกย้าย attribute แบบสังเคราะห์ |
| P08 model list | **RESOLVED** | DeepMatcher, DITTO, EMTransformer, HierGAT (arXiv 2508.08076 v2 §5.1.2) |
| 16 รายการ V-LIT-KNOWN | **RESOLVED** (ทั้งหมด → V-LIT-WEB) | P03, P05, P15, P16, P17, P20–P23, P25–P27, P32, P33 ผ่าน Crossref; P06 ผ่าน DataCite + PDF; P24 ไม่มี DOI (author PDF + OpenAlex pp. 973–978) |
| P34 | **RESOLVED – REINSTATED** | Min, Luo, Liu, Gong, Chen, "From Identification to Obfuscation: A Survey of Cross-Network Mapping and Anti-Mapping Methods", CMC 86(2):1–23, 2026, DOI 10.32604/cmc.2025.073175 — ใช้เป็น survey context เท่านั้น |

**K4 = RESOLVED** (เหลือเพียงเนื้อหาของ P28 และ P36 ที่ UNCONFIRMED และถูกจำกัดการใช้)

## 2. การแก้เมทาดาทาเทียบ v1

- **P04:** ปี 2021 → **2020** (PVLDB 14(1) issue Sept 2020; VLDB 2021 คือปีการประชุม)
- เพิ่มเลขหน้า: P03 pp. 41–49 · P05 pp. 19–34 · P06 pp. 463–473 · P12 1–42 · P15 3980–3990 · P16 1183–1210 · P20 6(4):1–21 · P22 10(7):1895–1923 · P25 16(1):41–46 · P26 625–632 · P27 213–220 · P32 38(6):946–969 · P33 64(12):86–92 (7 ผู้แต่ง) — ใส่ใน `PAPER_EVIDENCE_MATRIX.csv` (คอลัมน์ venue); ใน `REFERENCES.bib` เติมแล้วสำหรับ P02, P24 และรายการที่มีปัญหา K4 ส่วนรายการอื่นยังควรเติม pages ก่อนส่งเล่ม (งานเก็บรายละเอียด ไม่ใช่ปัญหาความถูกต้อง)
- P12 online Mar 2020 (print 2021) — อ้าง 53(2) ถูกต้อง
- P24 ไม่มี DOI; pp. 973–978 มาจากแหล่งรอง (OpenAlex)

## 3. Misattribution / over-reach ที่พบ

| Paper | v1 อ้างว่า | ผลตรวจ | ป้าย |
|---|---|---|---|
| P08 | "test-time heterogeneity แย่กว่า training noise" (ทั่วไป) | จริงเฉพาะ granularity/hierarchical heterogeneity; label noise ใน training ก็ลด AUC | PARTIAL |
| P07 | entity-disjoint split (G3) และ candidate vs end-to-end (E7-1) | เป็นการอนุมานของ v1 เอง ไม่ใช่ข้อเสนอของ paper (paper สนับสนุน open entities, imbalance, multimodal, การประเมินเกินจริง) | PARTIAL |
| P12 | นิยาม PC/PQ/RR, token blocking, block purging | ตรวจเฉพาะ abstract | PARTIAL |
| P03 | "username-only" | ฉบับเต็มเข้าไม่ได้ (403) | PARTIAL |
| P02 | "noisy/incomplete/unstructured" | ไม่ได้ตรวจข้อความในฉบับเต็ม | PARTIAL |
| P14 | รายละเอียด FAISS | ไม่อยู่ใน abstract | PARTIAL |
| P28 | "three-way + K-Means" | UNCONFIRMED | PARTIAL |
| อื่น ๆ | — | ไม่พบการอ้างที่ผิดชัดเจน (ไม่มี verdict NO) | — |

## 4. งานที่อ้างโดยโค้ด/รายงานประวัติศาสตร์

| ID | งาน | ผล |
|---|---|---|
| P36 | Arford, Lin, Li, Hu, Chen (2025), "Assessing the De-Anonymization Risk of Social Media Users: A BERT-Based Entity Resolution Approach", IEEE ISI 2025, pp. 15–20, DOI 10.1109/ISI65680.2025.11201172 | metadata VERIFIED; **เนื้อหา UNCONFIRMED** (ไม่มี OA) — ห้ามอ้างตัวเลข; OpenAlex แสดงว่าอ้าง LinkSocial (P38) — อ้างใน [MAIN@1e0a2db:experiments/REPORT_R0_R5.md#L63-L67] |
| P37 | Li, Miao, Wang, Sun, Wang (2021), "Improving the Efficiency and Effectiveness for BERT-based Entity Resolution", AAAI-21 35(15):13226–13233, DOI 10.1609/aaai.v35i15.17562 | VERIFIED จากฉบับเต็ม: siamese BERT + hash-code blocking + matching แบบ multi-task — คำอธิบายใน REPORT_R0_R5 ถูกต้อง |
| (เดิม `_work/P36.pdf`) | Isele & Bizer 2012 GenLink | ไม่ใช่สองงานข้างต้น → เก็บเป็น P39 |

## 5. LinkSocial provenance (G0) — P38

- Sharma & Dyreson, "LINKSOCIAL: Linking User Profiles Across Multiple Social Media Platforms", IEEE ICBK 2018, pp. 260–267, DOI 10.1109/ICBK.2018.00042; abstract: feature จากโปรไฟล์ → cost function + SGD เรียนน้ำหนัก, clustering เลือก candidate; รายงาน 92% accuracy pair-wise, 74% multi-platform
- Repo `vishalshar/Dataset-LinkSocial`: จำนวนโปรไฟล์ Instagram 10,958 · Twitter 13,961 · Google+ 11,892 ตรงกับข้อมูลโครงการ (10,957 / 13,960 / 11,890) ในระดับ 1–2 บัญชีต่อแพลตฟอร์ม → **หลักฐานแวดล้อมที่แข็งแรงว่าข้อมูลโครงการคือ LinkSocial**
- **commit `fe67dd1` ของ gitlink ไม่พบ** ใน upstream หรือ fork ทั้ง 3 (GitHub API) → provenance chain ตามที่บันทึก **ตรวจสอบไม่ได้**
- **ไม่มี license file** (`license: null`) → ตามกฎหมายถือเป็น all rights reserved; README ขอเพียงให้อ้าง paper → G0/G1 blocker
- วิธีสร้าง GT: **UNCONFIRMED** (paper เต็ม paywall); Goga et al. (P46) แสดงว่า GT แบบ self-declared links อาจไม่เป็นตัวแทน → label-proxy risk ถือว่า **HIGH จนกว่าจะ audit**

## 6. งานใหม่ (14 รายการ, P36–P49; cap 20)

ดูตาราง §11 ของ `literature/LITERATURE_REVIEW_TH.md` — ทุกรายการระบุ gap ที่เติมในคอลัมน์ `gap_filled` ของ `PAPER_EVIDENCE_MATRIX.csv`
งานที่พิจารณาแต่ไม่เพิ่ม: GAEMTBD (Mishra et al. 2017, abstract เข้าไม่ได้; P39/P40 ครอบคลุม gap แล้ว); hybrid blocking เพิ่มเติม (P13 ครอบคลุม); PPRL attack เพิ่ม (P30/P31/P35 ครอบคลุม)

## 7. ข้อจำกัดของการตรวจรอบนี้

- dblp/Semantic Scholar ใช้ไม่ได้ (rate limit)
- ฉบับเต็มของ P02, P03, P12, P14, P28, P36, P38 เข้าไม่ได้หรือไม่ได้อ่าน → ข้อความที่อ้างจากเนื้อหาเหล่านี้ติดป้าย PARTIAL
- ช่องว่าง "GA vs RS/TPE ที่ budget เท่ากันสำหรับ linkage threshold" ยังต้องค้นอย่างเป็นระบบ (Scopus/IEEE Xplore) ก่อนอ้างในเล่ม
