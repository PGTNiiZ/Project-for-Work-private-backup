# เริ่มใหม่ที่ Data Cleaning จริง ๆ

## เปิดอะไรตามลำดับ

1. [Notebook สำรวจข้อมูล](original/00_dataset_exploration.ipynb): ดูว่าเริ่มรู้จักข้อมูลและ field อย่างไร
2. [Notebook Data Clean รุ่นแรก](original/01_data_clean_first.ipynb): อ่านจากบนลงล่าง นี่เป็นจุดเริ่มหลัก
3. [Notebook Data Clean รุ่นหลัง](original/01_data_clean_later.ipynb): ดูเฉพาะส่วนที่เพิ่ม/เปลี่ยนจากรุ่นแรก
4. [v2 Stage 6](v2/stage6_preprocessing_v2.ipynb): ดูการซ่อม `profile_id` ก่อนเข้า blocking

## Notebook Data Clean รุ่นแรกทำอะไร

| ช่วง cell | สิ่งที่เกิดขึ้น | คำถามที่ควรตอบในเล่ม |
|---|---|---|
| Stage 1 | ตั้ง path/import | ข้อมูลต้นทางอยู่ไหน ใช้ library อะไร |
| Stage 2 | โหลดไฟล์ JSON ของโปรไฟล์ → DataFrame → raw CSV และตรวจไฟล์ที่บันทึก | จำนวนแถว/แพลตฟอร์มก่อน clean เท่าไร |
| Stage 3.1–3.2 | copy DataFrame และจัดการ `NaN` | field ใดขาด และแทนอย่างไร |
| Stage 3.3–3.7 | normalize username, full name, bio, location, URL/domain | ทำไมต้อง normalize ก่อนเทียบคู่ |
| Stage 3.8–3.9 | สร้าง `profile_id`, จัดข้อมูลหลัง normalize และบันทึกผล | ID ไม่ซ้ำหรือผิดรูปไหม; output ไปไหน |

**ผลที่เห็นใน workspace ตอนนี้:** [all_profiles_cleaned.csv](../../data/processed/all_profiles_cleaned.csv) มี **24,729 records** ส่วน [normalized_profiles_with_profile_id.csv](../../data_for_project/normalized_profiles_with_profile_id.csv) มี **36,807 records** (นับด้วย CSV parser เพราะบาง field มีขึ้นบรรทัดใหม่) ไฟล์สองชุดนี้มาจากคนละช่วง/ทางเดิน จึง **ยังห้ามเขียนว่าไฟล์หลังเกิดจากไฟล์แรกแบบหนึ่งต่อหนึ่ง** โดยไม่มีหลักฐาน lineage เพิ่ม

## จุดที่ยังรันใหม่จากต้นทางไม่ได้

โฟลเดอร์ raw ที่โค้ดเดิมคาดไว้ (`data/data/Dataset-LinkSocial`) ว่างใน workspace นี้ Git บันทึก path นั้นเป็น gitlink แต่ไม่มี `.gitmodules` บอกแหล่งดาวน์โหลด อีกทั้ง notebook รุ่นเก่ามี path แบบ relative/absolute จากเครื่องเดิมและมี cell ที่เขียนทับ output ดังนั้นตอนนี้เรากู้ **ลำดับงานและโค้ดประวัติ** ได้ แต่ยังไม่สามารถยืนยันว่ารัน Data Clean จาก raw แล้วได้ตัวเลขเดิมครบทุกขั้น

การเริ่มทดลองใหม่แบบตรวจสอบได้จึงต้องทำตามนี้: หา raw source ให้ตรงรุ่น → บันทึก checksum/จำนวนแถว → รัน clean ลง **โฟลเดอร์ output ใหม่** → ตรวจ null, ID ซ้ำ, แถวตามแพลตฟอร์ม → ค่อยไป Stage 7 ห้ามเขียนทับ artifact ที่ใช้อ้างอิงเล่มเดิม

**งานแรกที่ทำได้โดยไม่รันอะไร:** เปิด `01_data_clean_first.ipynb` แล้วจด 4 อย่าง: input path, จำนวนแถวก่อน clean, กฎจัดการค่าว่าง/normalize, output path นี่จะกลายเป็นตาราง “แหล่งข้อมูลและการเตรียมข้อมูล” ในบท 3
