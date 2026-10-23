# 07 — ดูหน้าตา dataset ที่ใช้ทดลอง

ถ้าต้องการตามข้อมูลที่เข้าโมเดลและ GA ทุกสายหลัก ให้เริ่มที่ [ชุด Excel การทดลอง](experiment_excel/README.md): มี 41-feature multimodal, GA 10 พารามิเตอร์, GB-17 + MiniLM ของ ICSEC, validation/GA/test ของ V2R1 และประวัติ R-series พร้อมดัชนี artifact ทั้งโครงการ

ถ้าต้องการเปิดใน Excel เลย ใช้ [07_dataset_raw_to_features.xlsx](07_dataset_raw_to_features.xlsx). เริ่มที่ชีต `00_READ_ME` แล้วเปิด `03_PAIRS`: หนึ่งแถวมีข้อมูลดิบและข้อมูลหลัง clean ของโปรไฟล์ A/B พร้อม label และ 17 features. ชีต `01_RAW_PROFILES` กับ `02_CLEAN_PROFILES` แสดงโปรไฟล์ 36,807 แถวก่อนและหลัง clean ตามลำดับ; ชีต `05_IMAGE_PROFILES` และ `06_IMAGE_FEATURES` เป็น snapshot ภาพอีกสายหนึ่ง. สร้างไฟล์ซ้ำได้ด้วย `.venv/bin/python thesis_rebuild/build_dataset_excel.py` (ต้องมี `pandas` และ `XlsxWriter` ใน environment).

ข้อมูล A ใน `03_PAIRS` เชื่อมโปรไฟล์ได้แน่ชัด 203,401 คู่, ไม่พบ ID 1,049 คู่, และ ID ซ้ำ 251 คู่; ฝั่ง B ได้ 204,688 / 7 / 6 คู่ตามลำดับ. แถวที่เชื่อมไม่ได้ยังคงมี label และ feature ครบ แต่ช่องข้อมูลดิบ/clean ฝั่งนั้นว่างพร้อม `match_status_a` หรือ `match_status_b`. โปรไฟล์ในชีต `01_RAW_PROFILES` เป็น CSV ก่อน normalize ที่มีอยู่ใน workspace; JSON ดิบต้นทางไม่อยู่ใน workspace นี้

เปิด [notebook สำรวจข้อมูล](07_ดูหน้าตา_dataset.ipynb) แล้วรันจาก root ของ repository ใน VS Code/Jupyter ด้วย Python kernel ที่มี pandas. เปลี่ยน `DATASET` ใน cell แรกเพื่อดูไฟล์อื่น จะใช้ชื่อย่อใน `DATASETS` หรือ path ของ CSV/Parquet ภายใน repository ก็ได้. Cell ถัดไปแสดง catalog ของไฟล์ข้อมูลทั้งหมด 512 ไฟล์จาก `data/`, `train_data/`, `experiments/` และ `artifacts/` โดยไม่โหลดเนื้อหา. ตัวแปร `df` เก็บ **ทุกแถวและทุกคอลัมน์** ของไฟล์ที่เลือก; ใน VS Code กด **View as DataFrame** ที่ตัวแปร `df` เพื่อเลื่อน ค้น และกรองได้ โดย notebook แสดงเพียงตัวอย่างไม่กี่แถวเพื่อไม่ให้ output หนักเกินไป

## แผนที่ไฟล์หลัก (นับจากไฟล์ที่อยู่ใน repository ตอนนี้)

| Dataset | หนึ่งแถวแทน | แถว | คอลัมน์ | ใช้ดูอะไร |
| --- | --- | ---: | ---: | --- |
| `data/processed/all_profiles_cleaned.csv` | โปรไฟล์หนึ่งบัญชี | 24,729 | 15 | ข้อมูลโปรไฟล์หลังทำความสะอาด |
| `data/final/profiles_with_images.csv` | โปรไฟล์หนึ่งบัญชี พร้อมข้อมูลภาพถ้ามี | 24,729 | 39 | โปรไฟล์และ image metadata ในตารางเดียว |
| `data/final/image_features_complete.csv` | ภาพหนึ่งรายการที่ประมวลผลแล้ว | 2,459 | 25 | ฟีเจอร์ของภาพ ไม่ใช่ฟีเจอร์เปรียบเทียบคู่ |
| `data/processed/labeled_pairs.csv` | โปรไฟล์สองบัญชีหนึ่งคู่ พร้อม label | 204,701 | 6 | ตัวอย่างคู่และ ground truth |
| `data/processed/feature_matrix.csv` | คู่โปรไฟล์หนึ่งคู่ พร้อมฟีเจอร์เปรียบเทียบ | 204,701 | 21 | 4 คอลัมน์โครงสร้าง/label + 17 ฟีเจอร์ |
| `data/processed/train_dataset.csv` | คู่ที่อยู่ใน train snapshot | 143,316 | 25 | 17 ฟีเจอร์ + รหัส/label + ชื่อ/แพลตฟอร์มประกอบ |
| `data/processed/test_dataset.csv` | คู่ที่อยู่ใน test snapshot | 30,558 | 25 | โครงคอลัมน์เหมือน train |
| `data/processed/candidate_pairs.csv` | คู่ที่ผ่าน candidate generation | 873,956 | 3 | รหัสคู่และ `sim_score`; ยังไม่มีผลโมเดล |
| `data/processed/predictions.csv` | คู่ candidate ที่ได้คะแนนและ decision | 873,956 | 5 | เพิ่ม `probability` และ `decision` |

**อย่านำจำนวนแถวเหล่านี้ไปบวกเป็น dataset เดียว:** ไฟล์บางชุดเป็นการแปลงหรือแบ่งชุดจากแถวเดิม และ artifacts ของการทดลองรอบใหม่อยู่คนละ protocol. `train_dataset.csv` + `test_dataset.csv` รวมได้ 173,874 แถว จึงไม่ครอบคลุมทั้ง 204,701 แถวของ `feature_matrix.csv`; อย่าสรุปส่วนที่เหลือเป็น validation โดยไม่มี split manifest ของรอบนั้น

## อ่านคอลัมน์อย่างไร

`profiles_with_images.csv` มีข้อมูลดิบ/ทำความสะอาด (`userName`, `fullName`, `bio`, `externalUrl`, `location`, `*_clean`), คีย์ (`profile_id`, `user_folder`, `platform`), และข้อมูลภาพ (`image_path`, ขนาด/คุณภาพ/ใบหน้า/caption/สถานะ). `has_image=True` มี 2,459 จาก 24,729 แถว; แถวที่ไม่มีภาพจึงมีค่าว่างในคอลัมน์ภาพหลายตัว. ใน `image_features_complete.csv` ทั้ง 2,459 แถวระบุ `platform=twitter` ตาม snapshot นี้ อย่าขยายความว่า image coverage เท่ากันทุกแพลตฟอร์ม

`feature_matrix.csv` มีคีย์ `profile_id_a`, `profile_id_b`, `entity_id_a` และ `label` (`1` = match, `0` = non-match). ฟีเจอร์ตัวเลข 17 ตัวเรียงตามไฟล์:

| กลุ่ม | คอลัมน์ |
| --- | --- |
| username | `username_jaro`, `username_token_sort`, `username_levenshtein`, `username_both_empty` |
| full name | `fullname_jaro`, `fullname_token_sort`, `fullname_levenshtein`, `fullname_both_empty` |
| bio | `bio_jaro`, `bio_token_sort`, `bio_levenshtein`, `bio_both_empty`, `bio_tfidf_cosine` |
| URL | `url_exact_match`, `url_domain_match` |
| platform/location | `same_platform`, `location_sim` |

ไฟล์นี้มี label `0` จำนวน 175,458 และ `1` จำนวน 29,243. ความหมายเชิงวิธีคำนวณของฟีเจอร์ให้ดู [Stage 9 v2](00_notebook_history/v2/stage9_features_v2.ipynb) และโค้ดรุ่นปัจจุบันที่ [features.py](../src/identity_resolution/stages/features.py). `label` กับ `entity_id_a` ใช้กำกับข้อมูล ไม่ใช่ฟีเจอร์ที่โมเดลควรเรียนรู้

## ขอบเขตของการทดลองรุ่นอื่น

- ตารางข้างบนเป็น **snapshot ใน `data/`** ไม่ใช่ไฟล์ที่รวมทุก run ใน repository
- โมเดล multimodal main run เลือก **41 ฟีเจอร์** จากชุดที่สร้างได้ ดู [รายการ 41 ฟีเจอร์](../pub_multi/doc/feature_41_breakdown_th.md). ไม่ควรเรียก 17 คอลัมน์ใน `feature_matrix.csv` ว่า 41 ฟีเจอร์
- การทดลองควบคุม V2R1 ใช้ 17 handcrafted features และ frozen MiniLM feature ภายใต้ split/label protocol ของตน ดู [V2R1 protocol](../experiments/icsec_final/authoritative_run_v2r1/PROTOCOL_V2R1.md). ผลจากรอบนี้ไม่ควรเทียบจำนวนแถวหรือ metric กับ snapshot ข้างบนโดยตรง
