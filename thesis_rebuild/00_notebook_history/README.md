# 00 — เริ่มจาก notebook ที่เราเคยทำจริง

นี่คือ **สำเนา notebook ประวัติจาก Git** เพื่อย้อนดูวิธีคิดและลำดับที่ทำ ไม่ใช่ pipeline ใหม่ และยังไม่ได้รันซ้ำในโฟลเดอร์นี้ ไฟล์ต้นทางเดิมถูกลบจาก working tree ตอนจัดระเบียบ repository แต่ยังอยู่ใน Git history

**เปิดก่อน:** [คู่มือ Data Cleaning](01_เริ่มจาก_data_clean.md) แล้วดู [notebook data clean รุ่นแรก](original/01_data_clean_first.ipynb) ทีละ cell

## เส้นทางเดิมตามลำดับ

| ลำดับ | Notebook ที่กู้มา | ตอนนั้นทำอะไร | ไปอ่านต่อ |
|---|---|---|---|
| 00 | [สำรวจข้อมูล](original/00_dataset_exploration.ipynb) | ดูข้อมูลและ field เบื้องต้น | 01 |
| 01 | [Data clean รุ่นแรก](original/01_data_clean_first.ipynb) | โหลด JSON, ทำ DataFrame, จัดการค่าว่างและ normalize ชื่อ/bio/location/URL | [คู่มือ](01_เริ่มจาก_data_clean.md) |
| 01b | [Data clean รุ่นหลัง](original/01_data_clean_later.ipynb) | เพิ่มการอ่าน CSV/label และแก้กระบวนการเตรียมข้อมูล | เทียบกับ 01 ก่อน |
| 07 | [Blocking](original/07_blocking.ipynb) | สร้าง candidate pairs ที่จะส่งให้โมเดล | [ขั้น 02](../02_ข้อมูลถึงคู่ผู้ใช้.md) |
| 08 | [Labeling](original/08_labeling.ipynb) | สร้างคู่บวกและคู่ลบ | [ขั้น 03](../03_คู่ผู้ใช้ถึงคะแนน.md) |
| 09 | [Features](original/09_features.ipynb) | คำนวณความคล้ายรายคู่ | [ขั้น 03](../03_คู่ผู้ใช้ถึงคะแนน.md) |
| 10 | [Dataset split](original/10_dataset_split.ipynb) | แยก train/validation/test และจัดการ class imbalance | [ขั้น 03](../03_คู่ผู้ใช้ถึงคะแนน.md) |
| 11 | [Training](original/11_training.ipynb) | ฝึกโมเดลตัวอย่างใน notebook | [ขั้น 03](../03_คู่ผู้ใช้ถึงคะแนน.md) |
| 12–13 | [Calibration + evaluation](original/12_13_calibration_evaluation.ipynb) | ปรับคะแนนและวัดผล | [ขั้น 03](../03_คู่ผู้ใช้ถึงคะแนน.md) |
| 14 | [Inference](original/14_inference.ipynb) | ใช้โมเดลกับ candidate pairs | [ขั้น 04](../04_คะแนนถึงการตัดสินใจ.md) |
| 15–17 | [Merge / scoring / export](original/15_16_17_merge_scoring_export.ipynb) | รวมโปรไฟล์และเตรียมผลออก | [ขั้น 05](../05_ผลลัพธ์อ่านอย่างไร.md) |

Notebook [ตรวจโปรไฟล์รวม](extras/check_combined_profiles.ipynb) และ [สร้าง ground-truth matrix](extras/build_ground_truth_matrix.ipynb) เป็นงานสำรวจประกอบ ไม่ใช่ขั้นบังคับในลำดับหลัก

## จุดเปลี่ยนเป็น v2

หลังพบปัญหารหัส `profile_id` ซ้ำ/ผิดรูปและการพลาดคู่ใน blocking มี notebook [v2 ตั้งแต่ Stage 6–17](v2/) แยกไว้ การอ่านประวัติให้ดู **รุ่นเดิมก่อน แล้วค่อย v2** เพื่อเห็นว่าแก้อะไร ห้ามหยิบตัวเลขจากสองรุ่นมารวมเป็นผลทดลองเดียว

## ที่มาของสำเนา

- สำรวจข้อมูล: `cb36d27:Initial-State/dataset.ipynb` (มีนาคม 2026); ไฟล์ชื่อเดียวกันใน commit มกราคมเป็นเพียงค่า `0` ไม่ใช่ notebook ที่เปิดอ่านได้
- Data clean รุ่นแรก: `e57ffcf:Clean-Data/preprocess_pipeline_backup.ipynb` (มีนาคม 2026)
- Data clean รุ่นหลัง, Stage 7–17, notebook เสริมและ v2: `1e0a2db:train_data/...` ก่อนการ cleanup ของ working tree

Notebook เหล่านี้มี path/output จากเครื่องและช่วงเวลาที่ทำเดิม บาง cell เขียนทับ CSV ได้ **อ่านเพื่อทำความเข้าใจก่อน อย่าใช้ Run All** ผลที่ใช้รายงานปัจจุบันยังต้องอ้าง artifact และ protocol ของแต่ละรอบตาม [ขั้น 05](../05_ผลลัพธ์อ่านอย่างไร.md)
