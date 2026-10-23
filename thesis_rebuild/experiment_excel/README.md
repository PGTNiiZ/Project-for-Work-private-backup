# Excel สำหรับไล่ข้อมูลการทดลองทีละขั้น

เปิด `04_source_artifact_catalog.xlsx` ชีต `FLOW` ก่อน แล้วตามไปยัง workbook ที่ระบุ. ทุก workbook มีชีต `00_READ_ME` บอก path ต้นทางและจำนวนแถว; ชื่อชีตที่ลงท้าย `_1`, `_2` คือส่วนต่อกันของตารางเดียว ไม่ใช่คนละ experiment.

| ไฟล์ | ข้อมูลที่เปิดดูได้ |
| --- | --- |
| [07_dataset_raw_to_features.xlsx](../07_dataset_raw_to_features.xlsx) | CSV ก่อน clean → clean → คู่ที่มี 17 features พร้อมข้อมูลดิบ A/B 204,701 คู่ และ image snapshots |
| [01_multimodal_and_GA.xlsx](01_multimodal_and_GA.xlsx) | 41-feature input 58,696 แถว; R1 GA input/trace; ผล GA 10 พารามิเตอร์ 2,086,245 คู่ |
| [01b_GA_full_feature_to_decision.xlsx](01b_GA_full_feature_to_decision.xlsx) | input กลุ่มหลักฐาน 2,073,842 คู่จับคู่กับ output GA แถวต่อแถว; exact tier 12,403 คู่แยกชีต |
| [02_ICSEC_model_inputs.xlsx](02_ICSEC_model_inputs.xlsx) | โปรไฟล์ที่มี `profile_row_id` และ feature 17 + MiniLM cosine ของ 2,073,842 คู่ |
| [03_ICSEC_V2R1_GA.xlsx](03_ICSEC_V2R1_GA.xlsx) | สาม seeds: development labels, routing, validation replay, optimizer replay, policy parameters, frozen predictions และผล test B0–B3/GB17_B0 |
| [04_source_artifact_catalog.xlsx](04_source_artifact_catalog.xlsx) | ดัชนี source CSV/Parquet/JSON ทุกไฟล์ที่มีในโครงการ พร้อม path, จำนวนแถว, schema และผังขั้นตอน |
| [05_R0_R6_experiment_history.xlsx](05_R0_R6_experiment_history.xlsx) | R2/R6 probabilities, R6 candidates, R1/R3 trials และ generation logs ของแต่ละ run |
| [06_GA_search_parameters.xlsx](06_GA_search_parameters.xlsx) | GA 10 พารามิเตอร์: validation trials, generation history, frozen policy, feature coverage; รวม GA ของ GB transformer |

## อ่านข้อจำกัดก่อนเทียบค่า

- `feature_matrix.csv` รุ่นเก่ามี 17 features แต่ไม่ใช่ GB-17 ของ ICSEC; 41-feature multimodal และ GA 10 พารามิเตอร์ก็อยู่คนละ protocol. ใช้ชื่อ workbook, source path และ seed กำกับเสมอ
- GA 10 พารามิเตอร์บน candidate เต็มเก็บ **6 group scores + availability** ต่อคู่ใน feature chunks ไม่ได้เก็บ 41 features รายคู่ครบทุกแถว; 41-feature input ที่มีจริงเป็นชุด 58,696 แถว. ชีต `01b` แสดงสิ่งที่ป้อน policy กับ output ที่เกิดขึ้นจริงตาม artifact
- `S*_VAL_REPLAY` และ `S*_B2/B3_REPLAY` ของ ICSEC มาจาก reviewer revision replay; ไม่ใช่ call log ต้นฉบับที่บันทึกตอน V2R1 รัน. ค่า policy ที่เลือกจริงอยู่ใน `POLICY_PARAMETERS` และผล test อยู่ในชีต `S*_*_TEST`
- ไฟล์ Excel มีโปรไฟล์และ label จริง รวมทั้ง sealed test labels ที่เปิดหลังการประเมินแล้ว; อย่าใช้ผล test เลือกค่าใหม่หรือเผยแพร่ไฟล์โดยไม่ตรวจสิทธิข้อมูล
- JSON ดิบของโปรไฟล์ต้นทางไม่ได้อยู่ใน workspace; ชีต raw ใช้ CSV ก่อน normalize ที่มีอยู่

คำอธิบายคอลัมน์เชิงวิธีคำนวณ: [41 features](../../pub_multi/doc/feature_41_breakdown_th.md), [R1 GA trace](../../experiments/walkthroughs/r1_ga_redecision/DATA_DICTIONARY.md), [V2R1 protocol](../../experiments/icsec_final/authoritative_run_v2r1/PROTOCOL_V2R1.md).

สร้าง workbook ซ้ำด้วย `.venv/bin/python thesis_rebuild/build_experiment_excels.py <part>` โดย `<part>` เป็น `multimodal_ga`, `ga_full_join`, `icsec_features`, `icsec_ga`, `catalog`, `r_history` หรือ `ga_search_details`; ใช้ `build_dataset_excel.py` สำหรับเล่ม raw-to-17-features.
