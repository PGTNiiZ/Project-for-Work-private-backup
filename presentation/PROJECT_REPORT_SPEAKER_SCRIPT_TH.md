# Speaker Script: Identity Resolution Pipeline

เอกสารนี้เป็นสคริปต์พูดประกอบ [`PROJECT_REPORT_TH.md`](../manuscript/PROJECT_REPORT_TH.md) ฉบับปัจจุบัน ใช้สำหรับการนำเสนอประมาณ 35-45 นาที หากมีเวลา 15-20 นาที ให้พูดเฉพาะส่วนที่มีป้าย **แกนหลัก**

## วิธีใช้สคริปต์

- อ่านข้อความใต้หัวข้อ **พูดว่า** ได้โดยตรง แล้วปรับสำนวนให้เป็นธรรมชาติ
- ข้อความใต้ **ทำอะไร / ทำไม / ทำอย่างไร** ใช้ตอบคำถามเพิ่มเติม
- ตัวเลขต่างขอบเขตห้ามเปรียบเทียบตรง ๆ เช่น pair-model test, full projection และ GA validation
- คำว่า “ดีที่สุด” ต้องตามด้วย metric, population และ cost policy เสมอ

---

# เปิดการนำเสนอ (1 นาที) — แกนหลัก

**ทำอะไร:** แนะนำโจทย์และผลลัพธ์ปลายทาง

**พูดว่า:**

> โปรเจกต์นี้เป็นระบบ Identity Resolution สำหรับตรวจว่าบัญชีจาก Twitter, Google+ และ Instagram เป็นบุคคลเดียวกันหรือไม่ เป้าหมายปลายทางคือรวมบัญชีเหล่านั้นเป็น unified customer profile เพื่อใช้ใน Customer 360, CRM และ lead scoring งานนี้ไม่ใช่แค่การ train classifier แต่เป็น pipeline ตั้งแต่การทำความสะอาดข้อมูล การสร้าง candidate pairs การให้คะแนนคู่ การกำหนด decision policy ไปจนถึงการรวม entity

**ประโยคเชื่อม:**

> ก่อนลงรายละเอียด ผมจะเริ่มจากภาพรวมทั้งระบบก่อน เพื่อให้เห็นว่า model และ GA อยู่ตรงไหนของงาน

---

# บทคัดย่อ (2 นาที) — แกนหลัก

**ทำอะไร:** สรุปข้อมูล วิธี ผล และข้อจำกัดในภาพเดียว

**ทำไม:** ทำให้ผู้ฟังรู้ผลสำคัญก่อนรับรายละเอียด

**พูดว่า:**

> ข้อมูลเริ่มต้นมี 36,807 profiles และมี 36,804 profiles ที่ผ่าน eligibility check คิดเป็น 15,297 entities หากจับคู่ข้ามแพลตฟอร์มทั้งหมดจะมีประมาณ 449.15 ล้านคู่ เราจึงใช้ exact matching และ blocking ลดเหลือ 2.086 ล้านคู่ แต่ยังครอบคลุม ground truth ได้ 88.67 เปอร์เซ็นต์
>
> Pair model หลักเป็น Gradient Boosting 41 features ร่วมกับ isotonic calibration ได้ test F1 เท่ากับ 0.9340 บน labeled pairs แต่เมื่อรวมข้อจำกัดของ blocking และ decision policy แล้ว full baseline F1 ลดเหลือ 0.7882 จุดนี้แสดงว่า model ที่ดีอย่างเดียวไม่พอ ระบบ retrieval และ operating policy มีผลมาก
>
> งานทดลองต่อยอดพบว่า R3 ให้สมดุลดีที่สุดใน R-series ส่วน GA ที่ optimize ด้วย CRM cost ล่าสุดเลือก name guard บน validation แต่ Precision 0.9853 และ Recall 0.6240 ยังไม่ผ่าน promotion gates ดังนั้นผลปัจจุบันยังเป็นงาน validation ไม่ใช่ production policy

**ห้ามพูด:** “โมเดล production มี F1 0.934 ทั้งระบบ” เพราะ 0.934 เป็น pair-model test เท่านั้น

---

# 1. บทนำ (3 นาที)

## 1.1 ที่มาและความสำคัญ — แกนหลัก

**ทำอะไร:** อธิบายปัญหาบัญชีของคนเดียวกันกระจายหลายแพลตฟอร์ม

**ทำไม:** Exact match อย่างเดียวพลาดกรณีชื่อหรือข้อมูลต่างกัน แต่ fuzzy match กว้างเกินไปเสี่ยงรวมผิดคน

**ทำอย่างไร:** ออกแบบ retrieval, pair scoring, three-way decision และ entity graph เป็นคนละชั้น

**พูดว่า:**

> คนหนึ่งคนอาจใช้ username คนละแบบ ชื่อเต็มคนละภาษา bio คนละข้อความ หรือเปลี่ยนรูปตามเวลา Exact match จึงจับได้เฉพาะกรณีง่าย ในอีกด้านหนึ่ง ถ้าใช้ fuzzy matching กว้างเกินไปก็เกิด false merge ซึ่งกระทบ CRM และความเป็นส่วนตัว เราจึงแยกงานเป็นหลายชั้นเพื่อควบคุมความเสี่ยง

## 1.2 วัตถุประสงค์

**พูดว่า:**

> วัตถุประสงค์มีทั้งด้านระบบและด้านการทดลอง เราต้องลด search space สร้าง features ป้องกัน leakage calibrate probability วิเคราะห์ error ทดลอง representation และสร้างทางเชื่อมไปยัง unified profile ไม่ได้วัดความสำเร็จจาก F1 ตัวเดียว

## 1.3 คำถามวิจัย

**พูดว่า:**

> คำถามหลักคือ blocking ลดจำนวนคู่ได้เท่าไร feature และ model ใดเหมาะ เหตุใด model F1 สูงแต่ end-to-end ต่ำกว่า GA ลดต้นทุนได้หรือไม่ และ feature อื่นสามารถแทน name similarity ใน decision policy ได้หรือไม่

## 1.4 ขอบเขต

**พูดว่า:**

> ขอบเขตหลักคือ cross-platform pairs และใช้ user_folder เป็น operational ground truth งานนี้ยังไม่อ้างว่า deploy production แล้ว และคู่ที่ blocking ไม่สร้างขึ้นมาจะไม่ถูก model ประเมิน

---

# 2. ภาพรวมสถาปัตยกรรม (3 นาที) — แกนหลัก

## 2.0 End-to-end architecture ภาพเดียว

**วิธีชี้ภาพ:** ไล่เส้นกลางจากบนลงล่าง แล้วอธิบายแขนงซ้ายและขวาภายหลัง

**พูดว่า:**

> ภาพนี้อ่านจากบนลงล่าง เริ่มจาก raw social profiles แล้ว clean และ normalize หลังจากนั้นสร้าง exact tier และ candidate retrieval คู่ที่เป็น candidate จะถูกคำนวณ features แล้วแบ่ง entity-aware split
>
> ฝั่ง model ใช้ train split สำหรับ fit Gradient Boosting ใช้ validation สำหรับ isotonic calibration แล้ว freeze model, scaler และ calibrator ผลที่ได้คือ calibrated probability
>
> Probability เดียวกันแยกไปสองทาง ทางแรกใช้ threshold 0.35 วัด pair-model benchmark อีกทางส่งเข้า GA พร้อม evidence cache เพื่อเลือก MATCH, REVIEW หรือ NO_MATCH GA เปลี่ยนวิธีตัดสินใจ แต่ไม่ retrain model
>
> MATCH edges ถูกนำไปสร้าง entity graph ด้วย Union-Find แล้วสร้าง unified profile และ CRM outputs ส่วน REVIEW ส่งให้คนตรวจ และ NO_MATCH ถูกปฏิเสธ

## 2.1 Canonical lifecycle

**พูดว่า:**

> ถ้ามองในระดับคำสั่ง ระบบมี lifecycle คือ prepare, pairs, features, train, evaluate, predict และ resolve แต่ละ stage มี input/output ชัดเจนและสามารถ replay ได้

## 2.2 Architecture layers

**พูดว่า:**

> โค้ดแบ่ง ownership เป็น core domain logic, lifecycle stages, full-candidate workflows, imaging adapters, research experiments และ publication tooling Research อ่าน artifacts จากระบบหลักได้ แต่ไม่ควรย้อนกลับไปควบคุม production runtime

## 2.3 Data flow ตั้งแต่ profile ถึง customer entity

**พูดว่า:**

> ในเชิงข้อมูล exact matches และ policy MATCH จะกลายเป็น graph edges จากนั้น connected components จะกำหนด customer entity การตัดสิน pair ผิดเพียงหนึ่ง edge อาจทำให้ component ผิดทั้งกลุ่ม จึงต้องควบคุม false positive อย่างเข้มงวด

## 2.4 Development และ deployment boundary

**พูดว่า:**

> Train ใช้ train entities การเลือก calibrator, threshold และ policy ใช้ validation ส่วน test ต้องเปิดหลัง freeze เท่านั้น Full candidates ใช้ frozen scorer และ frozen policy ไม่มีการ fit เพิ่มจาก production population

---

# 3. ข้อมูลและคุณภาพข้อมูล (3 นาที)

## 3.1 ชุดข้อมูลหลัก

**พูดว่า:**

> ข้อมูล input มี 36,807 แถว แต่มี 3 แถวที่ identifier ไม่พร้อม จึงเหลือ 36,804 แถวสำหรับ workflow ตัวเลขสองค่านี้ตอบคนละขั้นและไม่ใช่ความขัดแย้ง

## 3.2 Ground truth

**ทำอย่างไร:** คู่จาก user_folder เดียวกันเป็น positive และต่าง folder เป็น negative

**พูดว่า:**

> Ground truth ใช้ user_folder เป็น entity identifier มี positive pairs ทั้งหมด 29,247 คู่ แต่ primary cross-platform scope มี 29,243 คู่ ความต่าง 4 คู่เป็น same-platform pairs

## 3.3 ความสมบูรณ์ของ field

**พูดว่า:**

> Username และ fullname มี coverage สูง แต่ location มีเพียง 34.76 เปอร์เซ็นต์ ต้องแยก profile coverage จาก pair coverage เพราะการคำนวณ similarity มักต้องมีข้อมูลทั้งสองฝั่ง

## 3.4 ข้อมูลภาพ

**พูดว่า:**

> Image evidence มีข้อจำกัดสูง การดาวน์โหลดรอบล่าสุดล้มเหลว 998 จาก 998 URLs และ image context เพิ่ม F1 เพียงประมาณ 0.001 ในข้อมูลนี้ เราจึงถือภาพเป็น optional evidence ไม่ใช่สัญญาณหลัก

## 3.5 ความเสี่ยงด้านข้อมูล

**พูดว่า:**

> ความเสี่ยงหลักคือข้อมูล archival, URL และรูปหมดอายุ, label noise, exact username collision และ hard cases ที่ไม่มี evidence เพียงพอ ข้อจำกัดเหล่านี้สร้าง performance ceiling ที่แก้ด้วย model complexity อย่างเดียวไม่ได้

---

# 4. Candidate Generation และ Blocking (2 นาที) — แกนหลัก

## 4.1 เหตุผลที่ต้อง blocking

**พูดว่า:**

> ถ้าเทียบทุกคู่ข้ามแพลตฟอร์มจะมี 449,149,239 คู่ ซึ่งแพงเกินไป Blocking ใช้ key เช่น username prefix, fullname prefix และ domain เพื่อลดคู่ก่อนคำนวณ features ราคาแพง

## 4.2 ผล retrieval

**พูดว่า:**

> Candidate workflow เหลือ 2,086,245 คู่ ลด search space 99.54 เปอร์เซ็นต์ และครอบคลุม positive ground truth 25,931 จาก 29,243 คู่ หรือ retrieval recall 88.67 เปอร์เซ็นต์

## 4.3 Recall ceiling

**พูดว่า:**

> ยังมี blocking misses 3,312 cross-platform pairs คู่เหล่านี้ไม่มี score ดังนั้น threshold หรือ GA ที่ปลายทางแก้ไม่ได้ ต้องแก้ candidate retrieval โดยตรง

---

# 5. Feature Engineering (3 นาที)

## 5.1 Feature groups

**พูดว่า:**

> Features ครอบคลุม Name, Bio, URL, Location, Style, Social context, Image และ Platform metadata เพื่อให้ model มีทั้ง lexical, semantic, contextual และ availability signals

## 5.2 Similarity functions

**พูดว่า:**

> เราใช้หลาย similarity functions เพราะแต่ละชนิดตอบรูปแบบความต่างไม่เหมือนกัน Levenshtein วัด edit distance, cosine วัดทิศทางของ vectors และ Jaccard วัด overlap ของ sets เช่น URL หรือ mentions

## 5.3 Missingness-aware representation — แกนหลัก

**พูดว่า:**

> Similarity เท่ากับศูนย์อาจหมายถึงข้อมูลต่างกันจริงหรือไม่มีข้อมูล จึงต้องแยก score ออกจาก availability mask สำหรับ weighted evidence เราหารด้วยผลรวมน้ำหนักเฉพาะ evidence ที่มีอยู่ คู่ที่ไม่มี evidence จะคงเป็น REVIEW แทนการถูกลงโทษเป็น NO_MATCH

## 5.4 Feature importance ของ production model

**พูดว่า:**

> Feature importance แสดงว่า fullname token sort, username token sort และ fullname Jaro มีน้ำหนักสูงสุด รวมแล้ว name features เป็นสัญญาณหลัก Bio เป็นสัญญาณรอง ขณะที่ image features มีผลต่ำในข้อมูลที่ coverage จำกัด

**ข้อควรระวัง:** Feature importance ไม่เท่ากับ GA weight และไม่ใช่ causal effect

---

# 6. Pair Construction และ Leakage Control (2 นาที) — แกนหลัก

## 6.1 ประเภทคู่สำหรับ train

**พูดว่า:**

> Training data มี positive pairs, random negatives และ hard negatives Hard negatives สำคัญเพราะ random negatives แยกง่ายเกินไปและอาจทำให้ metric ดูสูงเกินการใช้งานจริง

## 6.2 Entity-aware split

**พูดว่า:**

> เรา split ที่ระดับ entity ไม่ใช่ระดับ pair เพื่อไม่ให้ profiles ของคนเดียวกันหลุดไปอยู่ทั้ง train และ test การตรวจสอบยืนยันว่า entity overlap ระหว่าง splits เป็นศูนย์

## 6.3 Split sizes ของ feature matrix

**พูดว่า:**

> Feature matrix มี 58,696 คู่ แบ่งเป็น train 41,803, validation 8,580 และ test 8,313 คู่ จำนวน positive และ negative ค่อนข้างสมดุล

## 6.4 Sealed-test rule

**พูดว่า:**

> หลักการคือ train บน train เลือก model/calibrator/policy บน validation จากนั้น freeze แล้วเปิด test ครั้งเดียว ถ้ากลับไปปรับจาก test ค่า test จะไม่ unbiased อีกต่อไป

---

# 7. Model Training และ Calibration (4 นาที) — แกนหลัก

## 7.1 Model families

**พูดว่า:**

> เราเปรียบเทียบ Logistic Regression, Random Forest, Gradient Boosting และ neural models โดย Gradient Boosting ถูกเลือกเพราะให้ validation balance ดีที่สุดใน multimodal suite

## 7.2 Calibration

**พูดว่า:**

> หลัง fit Gradient Boosting บน train เราได้ raw probability แล้ว fit isotonic calibrator บน validation เพื่อให้ score สอดคล้องกับ empirical probability มากขึ้น จากนั้น freeze model, scaler และ calibrator
>
> Threshold 0.35 ถูกเลือกบน validation F1 เพื่อวัด binary pair classifier เท่านั้น ส่วน manual policy ใช้ 0.98 และ 0.95 และ GA จะเลือก threshold อีกชุดหนึ่ง ทั้งสามกรณีใช้ calibrated probability เดียวกันและไม่มีการ retrain model

**คำตอบสั้นเมื่อถูกถามว่า GA เปลี่ยน model ไหม:**

> ไม่เปลี่ยนครับ GA เปลี่ยน operating rule หลัง model เท่านั้น

## 7.3 Pair-model result

**พูดว่า:**

> บน test 8,313 คู่ ที่ binary threshold 0.35 ได้ AP 0.9789, Precision 0.9507, Recall 0.9179 และ F1 0.9340 มี FP 209 และ FN 360 นี่คือ pair-model benchmark ไม่รวม blocking misses และไม่ใช่ผลหลัง GA

---

# 8. ผลตาม Platform และ Difficulty (2 นาที)

## 8.1 Platform-pair performance

**พูดว่า:**

> Instagram กับ Twitter ให้ F1 สูงสุดที่ 0.9489 ส่วน Google+ กับ Twitter มี recall ต่ำสุด 0.8936 และสร้าง FN มากที่สุด สะท้อน platform/domain shift

## 8.2 Difficulty slices

**พูดว่า:**

> Easy slice มี recall 0.9433 แต่ Mid ลดเหลือ 0.223 และ Hard เท่ากับศูนย์ แม้ Hard มีเพียง 5 positives ผลนี้เตือนว่า overall F1 ถูกขับเคลื่อนด้วยกรณีชื่อชัดเป็นส่วนใหญ่

---

# 9. Full-Candidate Decision Pipeline (3 นาที) — แกนหลัก

## 9.1 Decision tiers

**พูดว่า:**

> Baseline operational policy ใช้ score ตั้งแต่ 0.98 เป็น MATCH, 0.95 ถึง 0.98 เป็น REVIEW และต่ำกว่า 0.95 เป็น NO_MATCH นี่เป็น manual policy ไม่ใช่ threshold 0.35 และไม่ใช่ GA genome
>
> Exact tier มี precision 0.9949, Match tier มี 0.8942 และ Review tier มีเพียง 0.0471 จึงต้องเปิดประมาณ 21 คู่เพื่อพบ true match หนึ่งคู่

## 9.2 End-to-end baseline

**พูดว่า:**

> เมื่อรวม exact, scored decisions และ blocking misses แล้ว baseline มี TP 19,624, FP 925, FN 5,558 และ REVIEW 86,296 ได้ Precision 0.9550, Recall 0.6710 และ F1 0.7882

## 9.3 ทำไม pair-model F1 0.934 ไม่เท่ากับ full F1 0.788

**พูดว่า:**

> Pair-model test วัดเฉพาะคู่ที่อยู่ใน labeled feature matrix ส่วน full workflow รวม retrieval misses, exact tier, decision thresholds และ workload จึงเป็นคนละ evaluation boundary ตัวเลขทั้งสองถูกต้องแต่ตอบคนละคำถาม

---

# 10. Error Analysis (3 นาที)

## 10.1 False positives

**พูดว่า:**

> Baseline มี false matches 925 คู่ โดย 63 คู่มาจาก exact tier และ median score ของ FP สูงถึง 0.9954 แสดงว่า tail calibration และ exact collisions ยังเป็นความเสี่ยง

## 10.2 Scored false negatives

**พูดว่า:**

> มี true pairs 2,242 คู่ที่ผ่าน blocking แต่ถูกตัดเป็น NO_MATCH กลุ่มนี้ยังแก้ได้ด้วย representation, calibration หรือ decision policy เพราะมี score แล้ว

## 10.3 Blocking misses

**พูดว่า:**

> Blocking misses 3,316 ตาม research scope ไม่มี score จึงต้องแก้ด้วย retrieval เช่น additional keys หรือ semantic nearest neighbors ไม่ใช่ปรับ threshold

## 10.4 Review burden

**พูดว่า:**

> REVIEW 86,296 คู่มี positive เพียง 4,065 คู่ จึงเป็น operational bottleneck เป้าหมายของ decision policy ต้องลด workload พร้อมรักษา precision และ recall

---

# 11. Name-Similarity Ablation N0-N6 (2 นาที)

**ทำอะไร:** เปรียบเทียบวิธีแทนชื่อภายใต้ protocol เดียวกัน

**พูดว่า:**

> เราทดลอง N0 ถึง N6 บน validation โดย N6 ซึ่งรวม character 3-gram กับ handle features ให้ F1 0.9553 สูงกว่า baseline N0 ที่ 0.9410 ผลนี้สนับสนุน N6 เป็น candidate representation แต่ยังต้องผ่าน sealed test ก่อนเรียกว่า production replacement

**ห้ามสับสน:** N-series เปลี่ยน representation ใน model ไม่ใช่การเลือก GA guard

---

# 12. Representation × Decision R0-R6 (4 นาที)

## 12.1 แนวคิดการทดลอง

**พูดว่า:**

> R-series แยกสองแกน คือ representation และ decision rule เพื่อดูว่า feature ใหม่ดีจริงหรือเพียงต้องใช้ threshold ที่เหมาะกับ distribution ใหม่

## 12.2 ผล test

**พูดว่า:**

> R3 ซึ่งใช้ BERT cosine ร่วมกับ GA ให้ Test F1 สูงสุดใน common harness ที่ 0.8373 R5 Bloom-GA ตามมาใกล้เคียงที่ 0.8329 ส่วน R6 frozen BERT-ER ยังต่ำกว่า

## 12.3 R3 full projection

**พูดว่า:**

> R3 projection เพิ่ม full F1 จาก 0.7882 เป็น 0.8345 ลด FP ประมาณ 49.7 เปอร์เซ็นต์ และลด REVIEW 96.8 เปอร์เซ็นต์ แต่ยังเป็น research projection ไม่ใช่ deployed policy

## 12.4 FN recovery

**พูดว่า:**

> R3 กู้ scored false negatives เข้า MATCH หรือ REVIEW ได้ 728 คู่ หรือ 32.5 เปอร์เซ็นต์ มากกว่า R2 ที่ใช้ manual threshold แสดงว่า representation และ decision policy ต้องออกแบบร่วมกัน

## 12.5 Privacy-utility trade-off

**พูดว่า:**

> Bloom representation ที่ length 2,000 เมื่อใช้ GA มี F1 ต่างจาก R3 เพียง 0.0044 จึงน่าสนใจในกรณี privacy สำคัญ แต่ Bloom filter ไม่ใช่ encryption guarantee และต้องมี threat model

## 12.6 R6 semantic blocking

**พูดว่า:**

> R6 กู้ blocking misses ได้เพียง 4 จาก 3,316 คู่ที่ Hamming radius ไม่เกินหนึ่ง จึงเป็น negative result ที่บอกว่า frozen encoder ยังไม่พร้อม ต้อง fine-tune และใช้ hard negatives

---

# 13. Genetic Algorithm และ Business Cost (6 นาที) — แกนหลัก

## 13.1 Objective function

**พูดว่า:**

> CRM cost ปัจจุบันคือ 2FP บวก FN บวก 0.1 REVIEW โดย normalize จากเวลาทำงาน FP 20 นาที FN 10 นาที และ review 1 นาที Policy version คือ crm_derived_v1 ส่วนผลเก่าที่ใช้ 5 ต่อ 1 ต่อ 0.02 ต้องติดป้าย historical

## 13.2 Genome ของ R1/R3

**พูดว่า:**

> Genome มี match threshold, review threshold, promote threshold และ demote threshold ใน R1 เดิม name similarity ถูกกำหนดไว้ล่วงหน้า GA เลือกเพียง thresholds ดังนั้นไม่ควรพูดว่า R1 พิสูจน์ว่า name เป็น guard ที่ดีที่สุด

## 13.3 Feature-aware GA

**พูดว่า:**

> เราจึงเปรียบเทียบ score-only, name, bio, URL, image และ style โดยใช้ availability mask Historical labeled-subset run เลือก bio แต่ตารางนี้เป็น policy ที่ optimize ด้วย objective เก่าแล้วนำ counts มา re-cost จึงเป็น sensitivity analysis ไม่ใช่ current winner

## 13.4 Availability coverage

**พูดว่า:**

> Name มี coverage เกือบทั้งหมด Bio และ URL ประมาณสองในสาม Image ประมาณ 10 เปอร์เซ็นต์ และ Location ไม่มี usable evidence ใน validation การอ่าน reliability ต้องอ่านคู่กับ coverage เสมอ

## 13.5 Model weights ไม่เท่ากับ GA weights

**พูดว่า:**

> Model feature importance ตอบว่า feature ช่วยสร้าง probability มากเท่าไร ส่วน GA guard ตอบว่า evidence ช่วยตัดสินใน review band อย่างไร Name มี permutation AP delta 0.277651 สูงสุดอย่างชัดเจน Bio อยู่ที่ 0.011153 แต่ความสำคัญต่อ model ไม่ได้แปลว่า policy ผ่าน production gates

### 13.5.1 Proof: feature มีผลต่อ model มากน้อยเพียงใด

**พูดว่า:**

> วิธีพิสูจน์ใช้ permutation importance บน validation โดยสลับค่าของแต่ละ feature แล้วดูว่า Average Precision ลดลงเท่าไร Name group ลดลง 0.277651, Bio 0.011153, Other 0.004224, Style 0.001577, URL 0.001100, Image 0.000908 และ Location เท่ากับศูนย์ ผลนี้บอกว่า model พึ่ง name มากที่สุดในข้อมูลชุดนี้ แต่ต้องอ่านร่วมกับ coverage และไม่ควรตีความเป็น causal effect

## 13.6 Weighted GA result

**พูดว่า:**

> Historical weighted GA ให้น้ำหนัก name 0.3939, style 0.3043, image 0.1833 และ URL 0.1186 แต่ผลนี้มาจาก labeled historical run จึงใช้เพื่ออธิบาย mechanism ไม่ใช่ current production weight

### 13.6.1 One-stage GA: 2 thresholds + 8 weights

**พูดว่า:**

> เราทดลองตัด name promote และ demote cutoffs ออก แล้วใช้ genome 10 ค่า คือ threshold สองตัวกับ policy weights แปดตัว ได้แก่ frozen probability, name, bio, URL, location, social, image และ style คะแนนทั้งหมดถูกรวมครั้งเดียวแบบ availability-gated ก่อนตัดสินด้วยสอง threshold
>
> บน validation 8,580 คู่และ 10 seeds one-stage มี median cost 380.0 เทียบ score-only 385.9 และ legacy name guard 475.0 โดย 9 ใน 10 seeds ผ่าน Precision 0.99 และ Recall 0.70 Best seed ได้ Precision 0.9933, Recall 0.8144, F1 0.8950 และ cost 378.5
>
> น้ำหนัก best seed คือ probability 0.9222, image 0.0330, name 0.0272 และ URL 0.0176 ส่วน bio/style เป็นศูนย์ใน seed ที่ชนะ Location กับ social ถูก fix เป็นศูนย์เพราะ coverage ไม่ผ่าน gate ข้อสำคัญคือ name weight เป็นศูนย์ในค่ามัธยฐานไม่ได้แปลว่า model ไม่ใช้ชื่อ เพราะ frozen probability เองถูกเรียนมาจาก name features อยู่แล้ว
>
> รอบนี้เป็น validation-only และยังไม่เปิด held-out test ต้องตรวจ review capacity และ fresh audit test ก่อนใช้คำว่า production-ready

## 13.7 Sealed-test result

**พูดว่า:**

> Historical labeled run freeze bio แล้วเปิด test ได้ Precision 0.9973 แต่ Recall 0.5924 และ F1 0.7433 Population นี้ overlap กับ full scored candidates เพียง 1 เปอร์เซ็นต์ จึงเป็น proof of mechanism เท่านั้น

## 13.8 Historical full 2.07M run

**พูดว่า:**

> Historical full run เลือก style ภายใต้ cost เก่า เมื่อ re-cost ด้วย CRM policy ปัจจุบัน full projection cost เท่ากับ 9,963.50 และ F1 0.6607 ต่ำกว่า R3 จึงไม่ควร promote

## 13.9 CRM-cost validation-only rerun — แกนหลัก

**พูดว่า:**

> เมื่อ re-optimize บน full validation ด้วย crm_derived_v1 ตัวที่ cost ต่ำสุดคือ name ที่ 3,498.60 ได้ Precision 0.9853, Recall 0.6240 และ F1 0.7641 Weighted GA มี cost 4,897.10
>
> อย่างไรก็ตาม winner ยังไม่ผ่าน gates ที่กำหนดไว้คือ Precision อย่างน้อย 0.99 และ Recall อย่างน้อย 0.70 จึง freeze สำหรับงานวิจัยแต่ไม่เปิด test เดิมซ้ำและไม่ promote

**คำตอบที่ไม่ conflict:**

> Name สำคัญที่สุดต่อ pair model และเป็น scalar-cost winner ใน current full validation แต่ยังไม่มี feature guard หรือ weighted policy ใดผ่าน production gates

---

# 14. Entity Resolution และ CRM Layer (2 นาที)

**พูดว่า:**

> คู่ที่เป็น MATCH จะกลายเป็น graph edges แล้วรวม connected components ด้วย Union-Find จากนั้นสร้าง canonical fields, unified customer profile และ lead score ความเสี่ยงคือ FP เพียง edge เดียวอาจเชื่อมคนผิดหลาย profiles จึงต้องมี merge safety และ entity-level metrics ก่อน production

---

# 15. Reproducibility และ Engineering Controls (2 นาที)

## 15.1 Environment

**พูดว่า:**

> ระบบใช้ Python 3.11 และ pin dependencies ตามกลุ่มงาน เพื่อให้ training และ report generation ทำซ้ำได้

## 15.2 Artifact lineage

**พูดว่า:**

> ทุกผลต้องย้อนกลับไปยัง source checksum, feature version, split manifest, model parameters, calibrator, policy genome และ evaluation report ได้

## 15.3 Known reproducibility risk

**พูดว่า:**

> เคยมีความเสี่ยงจาก similarity implementation เปลี่ยนตาม dependency ที่ติดตั้ง โค้ดใหม่จึงต้องระบุ metric ชัดและห้าม silent fallback

## 15.4 Figure reproducibility

**พูดว่า:**

> รูปทั้งหมดสร้างจาก script และ fail หาก artifact ต้นทางหาย จึงไม่มีการใช้ค่าจำลองมาวาดแทนผลจริง

---

# 16. ข้อจำกัดของงาน (2 นาที) — แกนหลัก

**พูดว่า:**

> ข้อจำกัดหลักมีสิบข้อ ได้แก่ retrieval ceiling, evidence version mismatch, data age, image coverage, hard-case sample ต่ำ, ground-truth proxy, pair metrics ยังไม่ใช่ entity metrics, objective dependency, full projection ไม่ใช่ fresh sealed test และยังไม่มี deployment evidence
>
> ข้อจำกัดเหล่านี้ทำให้เราสรุปได้เฉพาะ validation และ research evidence ไม่ควรใช้คำว่า production-proven

---

# 17. ข้อเสนอแนะเชิงระบบ (3 นาที)

## 17.1 Full feature-aware cache

**พูดว่า:**

> งาน full cache เสร็จแล้ว 2,073,842 scored candidates แต่ current scalar-cost winner ยังไม่ผ่าน gates งานถัดไปคือ constrained objective และ fresh audit test

## 17.2 ลด false auto-merge

**พูดว่า:**

> ควรตรวจ calibration tail, exact collisions และ cluster-level over-merge พร้อมใช้ secondary evidence ก่อนสร้าง graph edge

## 17.3 แก้ blocking misses

**พูดว่า:**

> เพิ่ม semantic retrieval เป็น union กับ lexical blocking แล้ว gate ด้วย recall gain, candidate inflation และ downstream precision

## 17.4 ปรับ name representation

**พูดว่า:**

> ทดสอบ N6 ด้วย sealed protocol และ full scoring โดยยังไม่ลบ Jaro/token-sort เดิมจนกว่าจะมี ablation ยืนยัน

## 17.5 Data enrichment

**พูดว่า:**

> ต้อง snapshot URL และภาพในเวลาที่เก็บข้อมูล เพิ่ม location hierarchy, temporal metadata และ audited labels สำหรับ hard cases

## 17.6 Monitoring

**พูดว่า:**

> Monitoring ต้องครอบคลุม retrieval coverage, score drift, exact collisions, sampled MATCH precision, review yield และ component size เพื่อจับ over-merge

---

# 18. Roadmap การนำไปใช้ (1 นาที)

**พูดว่า:**

> Roadmap เริ่มจาก freeze data และ split สร้าง feature cache ทำ coverage audit รัน constrained GA freeze winner แล้วเปิด fresh test จากนั้นจึงทำ full projection, shadow CRM และ controlled deployment ทุก phase มี promotion gate และ rollback boundary

---

# 19. สรุปผล (2 นาที) — แกนหลัก

**พูดว่า:**

> งานนี้สร้าง end-to-end Identity Resolution pipeline ที่ตรวจสอบย้อนกลับได้ Pair model ให้ F1 0.9340 แต่ full baseline เหลือ 0.7882 เพราะ retrieval และ decision policy เป็นคอขวด R3 เป็น research comparator ที่สมดุลที่สุดใน R-series และ N6 เป็น name representation candidate
>
> Feature-aware proof ยืนยันว่า name features สำคัญที่สุดต่อ model แต่ current name GA policy ยังไม่ผ่าน production gates ดังนั้นข้อเสนอสุดท้ายคือรักษา calibrated Gradient Boosting เป็น baseline พัฒนา constrained GA แก้ blocking misses และเพิ่ม entity-level evaluation ก่อน deployment

---

# 20. Evidence Index

**พูดว่า:**

> ทุกคำกล่าวสำคัญในรายงานมี artifact อ้างอิง ตั้งแต่ model evaluation, blocking statistics, GA leaderboard, name ablation ไปจนถึง full candidate projection เพื่อให้ตรวจสอบและทำซ้ำได้

---

# Appendix A: สถานะคำกล่าวสำคัญ

**ใช้ตอบกรรมการ:**

- Pair-model F1 0.9340: ยืนยันจาก test artifact
- Full baseline F1 0.7882: ยืนยันจาก full evaluation
- R3 เป็นผลดีที่สุด: เฉพาะใน common R-series harness
- R3 deploy แล้ว: ยังไม่จริง
- Image สำคัญมาก: หลักฐานปัจจุบันไม่รองรับ
- Name สำคัญต่อ model: รองรับ
- Name เป็น production GA policy: ยังไม่ผ่าน gates
- Semantic blocking แก้ปัญหาแล้ว: ยังไม่จริง
- CRM deployment สำเร็จ: ยังไม่มี artifact

# Appendix B: คำสั่งทำซ้ำรูป

**พูดว่า:**

> รูปในรายงานสามารถสร้างซ้ำด้วย `.venv/bin/python manuscript/generate_report_figures.py` และ PDF สร้างด้วย `.venv/bin/python manuscript/generate_report_pdf.py`

---

# คำถามที่คาดว่าจะถูกถาม

## ทำไม F1 มีหลายค่า

> เพราะวัดคนละ boundary ครับ 0.9340 เป็น pair-model test, 0.7882 เป็น full baseline ที่รวม blocking misses และ 0.7641 เป็น current GA validation policy ห้ามนำมาเรียงโดยไม่ระบุ population และ policy

## ทำไม model ใช้ threshold 0.35 แต่ production ใช้ 0.98/0.95

> 0.35 optimize binary F1 เพื่อวัด classifier ส่วน 0.98/0.95 เป็น manual three-way operating policy สำหรับคุมความเสี่ยงและ review workload GA เป็นวิธีเลือก operating thresholds ใหม่จาก validation

## GA train model ใหม่หรือไม่

> ไม่ครับ Model, scaler, calibrator และ probability ถูก freeze GA ปรับเฉพาะวิธีเปลี่ยน probability และ evidence เป็น MATCH, REVIEW หรือ NO_MATCH

## Feature ใดแทน name ได้

> จากหลักฐานปัจจุบันยังไม่มี Name มีผลต่อ model สูงสุด และเป็น current scalar-cost GA winner แต่ policy ยังไม่ผ่าน gates Bio, URL, image และ style จึงยังพิสูจน์ว่าแทน name ไม่ได้

## ทำไม bio เคยชนะแล้วตอนนี้ name ชนะ

> เพราะเป็นคนละ population และคนละ objective Bio ชนะ historical labeled subset, style ชนะ historical full run และ name ชนะ current CRM-cost full validation จึงไม่ใช่ผลทดลองเดียวกันที่ขัดกัน

## พร้อม production หรือยัง

> ยังไม่พร้อมครับ ต้องมี constrained policy ที่ผ่าน Precision/Recall gates, fresh audit test, entity-level over-merge metrics และ shadow deployment evidence ก่อน

# ประโยคปิดการนำเสนอ

> สรุปแล้ว จุดแข็งของงานนี้คือไม่ได้หยุดที่ model accuracy แต่ตรวจครบทั้ง retrieval, calibration, decision cost และ entity risk ผลปัจจุบันบอกชัดว่าระบบมี baseline ที่แข็งแรง แต่ production readiness ต้องแก้ blocking misses และใช้ constrained decision policy ที่ผ่าน fresh test ก่อนครับ
