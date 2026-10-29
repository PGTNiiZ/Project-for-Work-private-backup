# Blocking และ Feature sets — รายงานภาษาไทย

**สถานะ: POST-HOC, DEVELOPMENT-ONLY, EXPLORATORY** — ใช้ development folds 0–3 เท่านั้น ไม่แตะ test fold
(ledger/test_access.jsonl ไม่เปลี่ยน: 21 บรรทัด, sha256 400bc83f…) ผลหลัก H1–H5 ไม่ถูกแก้ สถานะโครงการยัง NO-GO
ตัวเลขเป็นผลบน development ที่ถูกเลือก/ปรับซ้ำ จึงไม่ใช่ค่าประมาณแบบ nested และห้ามใช้เป็นผลสรุปของงานตีพิมพ์

## 0. ภาพรวมทั้ง pipeline (1 หน้า, ภาษาง่าย)

เป้าหมาย: ดูโปรไฟล์จากหลายแพลตฟอร์ม (Twitter, Google+, Instagram) แล้วบอกว่าคู่ไหนเป็นคนเดียวกัน
ถ้าเทียบทุกคู่ต้องทำเป็นหลายร้อยล้านครั้ง จึงแบ่งเป็น 4 ขั้น

1. Blocking (คัดคู่ผู้สมัคร) — แต่ละโปรไฟล์ดึงเฉพาะโปรไฟล์ที่ "หน้าตาใกล้เคียง" มาเป็นคู่ผู้สมัคร
   ถ้าคู่ที่เป็นคนเดียวกันหลุดตรงนี้ ขั้นหลังช่วยไม่ได้ ตัววัดคือ PC (pair completeness = สัดส่วนคู่จริงที่ยังอยู่ในรายการ)
2. Features — แต่ละคู่ผู้สมัครถูกแปลงเป็นตัวเลข เช่น ชื่อผู้ใช้คล้ายกันแค่ไหน ชื่อเต็มคล้ายกันแค่ไหน ลิงก์ซ้ำกันหรือไม่
3. Model (GBDT) — ต้นไม้ตัดสินใจหลายต้นเรียนรู้จากตัวเลขเหล่านี้ แล้วให้คะแนนว่า "น่าจะเป็นคนเดียวกัน"
   ใช้ cross-validation แบบ entity-disjoint (คนเดียวกันไม่อยู่ทั้งฝั่งสอนและฝั่งสอบ) AP คือคุณภาพการจัดอันดับ (1 = สมบูรณ์)
4. นโยบายตัดสินใจ (ตรึงไว้ตั้งแต่ก่อนหน้า ไม่ปรับ) — คะแนนถูกปรับเป็นความน่าจะเป็น (Platt) แล้วกฎตามต้นทุนแยกเป็น
   "รวมอัตโนมัติ / ส่งคนตรวจ / ไม่รวม" end-to-end recall = สัดส่วนคู่จริงทั้งหมดที่ระบบรวมอัตโนมัติได้ถูกต้อง (นับคู่ที่ blocking ทำหลุดเป็นพลาดด้วย)

## 1. วินิจฉัย blocking miss ของ sparse (Step 1)

วิธี: sparse (TF-IDF) พลาดคู่จริง 1,815 จาก 23,391 (PC 0.9224) เราจัดสาเหตุของคู่ที่พลาดด้วยค่า similarity เท่านั้น
(ไม่อ่านโปรไฟล์ ไม่ใช้ป้ายกำกับตอนคัดคู่) โดยจัดตามลำดับความสำคัญให้แต่ละคู่ได้ 1 สาเหตุ

| สาเหตุ | จำนวน | หมายเหตุ |
|---|---|---|
| a username คล้าย ชื่อไม่คล้าย | 19 | น้อยมาก |
| b username ฝั่งหนึ่งคล้าย fullname อีกฝั่ง (cross-field) | 256 | |
| c ชื่อ/username ขาดด้านใดด้านหนึ่ง | 264 | |
| d เชื่อมได้ทาง link/โดเมนเท่านั้น | 47 | |
| e ไม่มีสัญญาณข้อความเลย (เพดานที่กู้ไม่ได้) | 54 | ceiling PC ถ้าไม่นับ e = 0.9977 |
| f อื่น ๆ | 1,175 | 65% ของที่พลาด — ยังอธิบายด้วย feature ข้อความไม่ได้ |

แยกตามคู่แพลตฟอร์ม (f / b / c / e / d / a): googleplus+twitter 591/114/77/28/11/7;
googleplus+instagram 335/117/107/24/5/2; instagram+twitter 249/25/80/2/31/10
ข้อจำกัด: สาเหตุมาจากเกณฑ์ similarity ที่ตั้งเอง ไม่ใช่การตรวจโดยมนุษย์ และ "e" เป็นเพดานเฉพาะ feature ชุดนี้
ข้อสังเกต: สาเหตุใหญ่สุดคือ "f" ไม่ใช่ปัญหาชื่อ/username ดังนั้นการเพิ่ม pass ข้อความแก้ได้จำกัด

## 2. Multi-pass blocking (Step 2)

วิธี: แยกค้นหา 4 เส้นทาง (username TF-IDF, fullname TF-IDF, username↔fullname ข้ามช่อง, คีย์โดเมนลิงก์) แล้วรวมผล
จัดเรียงด้วยคะแนนโดยไม่ใช้ป้ายกำกับ และตัดที่งบจำนวนคู่เท่ากับ sparse ที่ 1x / 1.5x / 2x (pooled dev, ground truth 23,391)

| blocker | งบ | candidates | PC | runtime รวม 4 folds |
|---|---|---|---|---|
| sparse | 1.0x | 351,494 | 0.9224 | – |
| sparse | 1.5x | 527,243 | 0.9301 | 20.6 s |
| sparse | 2.0x | 702,988 | 0.9361 | 20.3 s |
| multipass | 1.0x | 351,494 | 0.9345 | 21.5 s |
| multipass | 1.5x | 527,243 | 0.9364 | 21.6 s |
| multipass | 2.0x | 702,988 | 0.9376 | 21.4 s |

ที่งบเท่ากัน multipass ดีกว่า sparse +1.2 จุด PC (กู้คืนได้ราว 283 คู่) การเพิ่มงบให้ผลน้อยลงเรื่อย ๆ
(ผลต่างยังเล็ก) ตามกฎที่ตั้งไว้ "PC สูงสุดบน pooled development" ได้ multipass@2.0x ถูก freeze (metrics/blocker_FROZEN.json)
แต่ถ้าสนใจต้นทุน multipass@1.0x ได้ PC 0.9345 ที่จำนวนคู่เท่าเดิม (ต่างจาก 2.0x เพียง 0.003) — ข้อสังเกต ไม่ได้เปลี่ยนสิ่งที่ freeze
ผลกู้ตามสาเหตุอยู่ใน metrics/step2_blocking_comparison.json (เช่น fold 3 ที่ 2x: b 68/68, a 3/3, d 10/10, c 18/69, f 76/303, e 0/20)
สรุปคือ multipass กู้ cross-field และลิงก์ได้เกือบหมด แต่กลุ่ม c, f และ e กู้ได้น้อย

## 3. Feature ประวัติศาสตร์ (Step 3)

- historical-23 (text/attribute): พบโค้ดต้นทางและทำ parity test บนข้อมูล SYNTHETIC ผ่าน 5/5 (รวมเทียบกับ train_base.py ปัจจุบัน)
  ปรับตามข้อจำกัดของ dev schema: bio_mentions เป็นค่าคงที่ว่าง, bio embedding ใช้ MiniLM ที่ freeze ไว้ แทน MPNet, TF-IDF fit เฉพาะส่วน train
  ต้องบันทึกว่า "ใช้ซ้ำ" (นิยามเดิม) กับ "ดัดแปลง" (3 ข้อข้างต้น) แยกกัน
- ตัวเลข 14 image statistics + 4 image context (รวม 41): **BLOCKED** — dev parquet มีเฉพาะข้อความ normalized + entity/fold
  ไม่มี row-id/pictureURL ที่พิสูจน์การจับคู่รูปได้ และ raw CSV/image cache มีโปรไฟล์ฝั่ง test ปนอยู่ จึงไม่ใช้
  ไม่เติมศูนย์แทนรูป ดังนั้นไม่รัน historical-41 และไม่มีตัวเลข image coverage
- name_sim zeroing defect: ใน train_data/*.py ไม่พบ name_sim; การตรวจ parity ของ 23 feature ไม่พบการทำให้เป็นศูนย์ในโค้ดที่ตรวจ
  ยังสรุปไม่ได้ว่าเป็นกรณีของ notebook เดิม — ยืนยันไม่ได้ (UNVERIFIED)
- แก้ไขเทสต์ synthetic เล็กน้อย: เติมตัวแปร FEATURE_PROGRESS_HOOK ใน namespace ของเทสต์ (เทสต์เดิม error เพราะ extract ฟังก์ชันออกมาเดี่ยว ๆ) ผ่านแล้ว

## 4. เปรียบเทียบ GBDT (Step 4) บน candidate ที่ freeze

วิธี: GBDT ต่อ feature set จูน 200 configs (TPE) บน entity-disjoint dev folds จากนั้น refit 5 seeds (11, 23, 42, 71, 101)
ใช้ calibrator และนโยบายเดิมโดยไม่ refit ผลเป็นค่าเฉลี่ย 5 seeds; recall หารด้วย 23,391 (คู่จริงทั้งหมด)

| feature set | OOF AP (SD) | end-to-end auto recall | recall ถ้าคนตรวจถูกหมด | precision auto |
|---|---|---|---|---|
| F-LEX35 | 0.9706 (0.0003) | 0.8087 | 0.9018 | 0.9916 |
| historical-23 | 0.9632 (0.0001) | 0.7843 | 0.8889 | 0.9955 |
| historical-23 + F-LEX35 | 0.9770 (0.0001) | 0.8187 | 0.9066 | 0.9945 |
| historical-41 | ไม่รัน (BLOCKED) | – | – | – |

อ่านผล: ชุดรวมดีที่สุดทั้ง AP และ recall (+1.0 จุดเทียบ F-LEX35 ที่ recall อัตโนมัติ) historical-23 ต่ำสุดใน AP แต่ precision สูงสุด
(อนุรักษ์กว่า) SD ข้าม seed เล็กมากเพราะ seed เปลี่ยนเฉพาะ refit ไม่ได้ครอบคลุมความไม่แน่นอนจากการ split/การจูน จึงไม่ควรตีความเป็นนัยสำคัญทางสถิติ

### Feature importance (ค่า AP ที่ลดลงเมื่อสลับค่าคอลัมน์ บน held-fold, ≤25,000 คู่, 3 รอบ, seed 42)
- F-LEX35: username_tfidf_cosine 0.102, links_tfidf_cosine 0.091, fullname_tfidf_cosine 0.062
- historical-23: username_token_sort 0.122, domain_count_b 0.072, url_jaccard 0.069, fullname_jaro 0.043
- รวม: username_tfidf_cosine 0.067, fullname_tfidf_cosine 0.056, domain_count_b 0.048, links_tfidf_cosine 0.025
ข้อควรระวัง: permutation importance ของ feature ที่สัมพันธ์กัน (username/ลิงก์หลายแบบ) กระจายคะแนนกัน อย่าตีความเป็นเหตุเป็นผล

### Feature set ช่วยสาเหตุไหน
ตารางด้านล่างคือจำนวนคู่จริงที่รวมอัตโนมัติได้ (ค่าเฉลี่ย 5 seeds) แยกตามสาเหตุ ซึ่งจัดด้วย taxonomy เดียวกันกับข้อ 1
**คำเตือน:** นี่คือการจัดกลุ่มคู่จริงที่อยู่ใน candidate ทั้งหมด (ไม่ใช่เฉพาะคู่ที่ sparse พลาด) ลำดับความสำคัญของ taxonomy ทำให้กลุ่ม b ใหญ่
(16,393) จึงไม่ใช่ "สาเหตุ miss" ในข้อ 1 และกลุ่ม e = 0 เพราะคู่ไร้สัญญาณหลุดจาก candidate ไปแล้ว

| สาเหตุ (จำนวนคู่จริงใน candidate) | F-LEX35 | H23 | H23+LEX35 |
|---|---|---|---|
| a (397) | 350 | 345 | 357 |
| b (16,393) | 14,871 | 14,354 | 14,980 |
| c (679) | 459 | 443 | 469 |
| d (129) | 73 | 107 | 110 |
| f (4,333) | 3,163 | 3,097 | 3,234 |

H23 ช่วยกลุ่ม d (ลิงก์/โดเมน) มากกว่า F-LEX35 (107 vs 73) สอดคล้องกับ importance ของ domain_count_b/url_jaccard
ชุดรวมดีที่สุดทุกกลุ่ม แต่กลุ่ม c และ f (ข้อมูลขาด/ไม่มีสัญญาณชัด) ยังรวมอัตโนมัติได้เพียง ~69% และ ~75% — เพดานคือข้อมูลที่ขาด ไม่ใช่โมเดล

## 5. การตรวจสอบ
- tests posthoc_blocking_features/tests: 4 passed; synthetic historical-feature tests: 5 OK
- ไม่เข้าถึง test fold; ledger ไม่เปลี่ยน; H5 primary result และ sparse/hybrid_rrf เดิมไม่ถูกแก้
- DEVIATIONS.md บันทึกงานนี้แล้ว
- ยังไม่ได้ commit (ตามนโยบาย local commit บน research-v2-experiments เมื่อผู้ใช้สั่ง) และไม่ push

## 6. สิ่งที่ยังไม่ทราบ
- historical-41 และ image coverage: ต้องมี row-id/รูปที่ผูกกับ dev โดยไม่ผ่านโปรไฟล์ test
- name_sim defect: ยังตรวจไม่พบ ไม่ยืนยันว่ามี/ไม่มี
- แยกผลของ blocker ใหม่ออกจากผลของ feature set: ทุก feature set ใช้ candidate ชุดเดียวกัน (multipass@2.0x) การเปรียบเทียบกับ H5 เดิมจึงไม่ใช่ apple-to-apple
