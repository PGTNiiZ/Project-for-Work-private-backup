# Speaker Script เฉพาะข้อ 13: Genetic Algorithm และ Business-Cost Optimization

สคริปต์นี้ใช้พูดประกอบข้อ 13 ของรายงาน [`PROJECT_REPORT_TH.md`](../manuscript/PROJECT_REPORT_TH.md) ใช้เวลาประมาณ 15-18 นาที ครอบคลุมข้อ 13.1-13.9 และอธิบายว่าทำอะไร ทำไม และทำอย่างไร

## เป้าหมายของข้อ 13

**พูดว่า:**

> ในข้อ 13 เราจะเปลี่ยนจากคำถามว่า model ทำนายคู่ได้ดีแค่ไหน ไปเป็นคำถามว่า เมื่อ model ให้ probability มาแล้ว เราควรตัดสินคู่ใดเป็น MATCH คู่ใดส่ง REVIEW และคู่ใดเป็น NO_MATCH เพื่อให้ต้นทุนทางธุรกิจต่ำที่สุด
>
> ส่วนนี้มีสามแนวคิดที่ต้องแยกออกจากกันให้ชัด หนึ่ง model สร้าง calibrated probability สอง GA ใช้ probability ที่ freeze แล้วเพื่อหา decision policy และสาม business cost เป็นตัวกำหนดว่าความผิดพลาดแต่ละชนิดแพงไม่เท่ากัน GA ไม่ได้ train model ใหม่และไม่ได้เปลี่ยนน้ำหนัก feature ภายใน Gradient Boosting

**ประโยคสั้นสำหรับเน้น:**

> Model ตอบว่า “คู่นี้เหมือนกันมากแค่ไหน” ส่วน GA ตอบว่า “ภายใต้ต้นทุนธุรกิจ เราจะทำอะไรกับคะแนนนี้”

---

## 13.1 Objective Function (ประมาณ 2 นาที)

### หัวข้อนี้ทำอะไร

แปลงเวลาปฏิบัติงานของ CRM ให้เป็นฟังก์ชันต้นทุนที่ GA สามารถ optimize ได้

### ทำไมต้องทำ

Precision, Recall หรือ F1 ให้น้ำหนัก FP และ FN ตามนิยามของ metric แต่ในการทำงานจริง FP, FN และ REVIEW ใช้ต้นทุนไม่เท่ากัน โดยเฉพาะ false positive ที่อาจรวมลูกค้าคนละคนเข้าด้วยกันและต้องใช้เวลาแก้ไขมากกว่า

### ทำอย่างไร

- ค่าแรงสมมติ 100 บาทต่อชั่วโมง
- REVIEW ใช้ 1 นาที คิดเป็น 1.67 บาท
- FN ใช้ 10 นาที คิดเป็น 16.67 บาท
- FP ใช้ 20 นาที คิดเป็น 33.33 บาท
- หารทุกค่าด้วยต้นทุน FN เพื่อ normalize ให้ FN มีน้ำหนักเท่ากับ 1

จึงได้:

$$
C_{crm}=2FP+FN+0.1REVIEW
$$

### สคริปต์พูด

> เราเริ่มจากต้นทุนที่ตีความได้จริง ค่าแรงคือ 100 บาทต่อชั่วโมง การ review หนึ่งคู่ใช้ประมาณ 1 นาที การจัดการ false negative ใช้ 10 นาที และการแก้ false positive ใช้ 20 นาที เมื่อ normalize ด้วยต้นทุน false negative จะได้ cost เท่ากับ 2 คูณ FP บวก FN บวก 0.1 คูณ REVIEW
>
> ความหมายคือ false positive หนึ่งคู่แพงเท่ากับ false negative สองคู่ และ review สิบคู่มีต้นทุนเท่ากับ false negative หนึ่งคู่ ดังนั้น policy ที่ลด review ได้มากอาจคุ้มค่า แต่ต้องไม่แลกด้วย false positives หรือ false negatives มากเกินไป
>
> Policy ปัจจุบันใช้ชื่อเวอร์ชัน `crm_derived_v1` ส่วนงานทดลองเก่าใช้สูตร 5FP บวก FN บวก 0.02 REVIEW เราเก็บผลเก่าไว้เพื่อ reproducibility และติดป้ายว่า historical แต่ไม่แก้ตัวเลขใน artifact ย้อนหลัง

### จุดที่ต้องระวัง

> การนำ counts จาก policy เก่ามาคำนวณ cost ใหม่เรียกว่า re-score เท่านั้น ยังไม่ใช่ re-optimize เพราะ policy เดิมถูกค้นหาภายใต้วัตถุประสงค์คนละสูตร

**ประโยคเชื่อม:**

> เมื่อมี objective แล้ว ขั้นต่อไปคือต้องกำหนดว่า GA สามารถปรับพารามิเตอร์ใดได้บ้าง

---

## 13.2 Genome ของ R1/R3 (ประมาณ 1.5 นาที)

### หัวข้อนี้ทำอะไร

กำหนด chromosome หรือชุดตัวแปรที่ GA ค้นหา

$$
g=[t_{match},t_{review},c_{promote},c_{demote}]
$$

### ความหมายของตัวแปร

- $t_{match}$: probability ที่สูงพอให้เป็น MATCH โดยตรง
- $t_{review}$: ขอบล่างของช่วง REVIEW
- $c_{promote}$: evidence threshold สำหรับเลื่อนคู่ใน review band ขึ้นเป็น MATCH
- $c_{demote}$: evidence threshold สำหรับลดคู่ที่ evidence อ่อนลงเป็น NO_MATCH

### สคริปต์พูด

> Genome ของ R1 และ R3 มีสี่ค่า สองค่าแรกควบคุม calibrated probability และอีกสองค่าควบคุม evidence guard ใน review band GA จะสร้าง threshold หลายชุด ประเมิน cost ของแต่ละชุด แล้วคัดเลือกและผสมชุดที่ดีกว่าต่อเนื่องหลาย generation
>
> ประเด็นสำคัญคือ implementation เดิมกำหนด `name_sim` เป็น evidence guard ไว้ล่วงหน้า GA เลือกเฉพาะ threshold สี่ค่า ไม่ได้เลือกว่าจะใช้ name, bio หรือ URL เพราะฉะนั้นประโยคว่า “GA เดิมพิสูจน์ว่า name ดีที่สุด” ไม่ถูกต้อง ประโยคที่ถูกคือ “ผู้ออกแบบกำหนด name ให้ GA ก่อน แล้ว GA หา threshold ที่เหมาะกับ name”

### ตัวอย่างการไหลของคำตัดสิน

> ถ้า probability สูงกว่า $t_{match}$ ระบบให้ MATCH ทันที ถ้าอยู่ระหว่าง $t_{review}$ กับ $t_{match}$ ระบบจะตรวจ evidence เพิ่ม ถ้า evidence สูงกว่า $c_{promote}$ จึงเลื่อนเป็น MATCH ถ้าต่ำกว่า $c_{demote}$ จึงลดเป็น NO_MATCH ส่วนกรณีกลางยังอยู่ใน REVIEW

**ประโยคเชื่อม:**

> เพื่อพิสูจน์ว่า name เหมาะจริงหรือไม่ เราจึงต้องเปิดให้ evidence ชนิดอื่นเข้าแข่งขันภายใต้ protocol เดียวกัน

---

## 13.3 Feature-Aware GA (ประมาณ 2 นาที)

### หัวข้อนี้ทำอะไร

เปรียบเทียบ policy แบบ score-only กับ policy ที่ใช้ guard จาก name, bio, URL, image และ style

### ทำอย่างไร

1. ใช้ calibrated probability ชุดเดียวกันทุก policy
2. ใช้ validation population เดียวกัน
3. เปลี่ยนเฉพาะ evidence guard
4. ใช้ availability mask เพื่อไม่ตีความ “ไม่มีข้อมูล” เป็น similarity ต่ำ
5. เปรียบเทียบ FP, FN, REVIEW, Precision, Recall และ cost

### สคริปต์พูด

> Feature-aware GA ถูกสร้างขึ้นเพื่อทำ comparison ที่ GA เดิมทำไม่ได้ เราให้ score-only, name, bio, URL, image และ style แข่งขันกัน โดยทุกตัวใช้ model probability ชุดเดียวกันและต่างกันเฉพาะ guard ที่ใช้ใน review band
>
> ใน historical labeled-validation run เมื่อเอา counts เดิมมา re-score ด้วย CRM cost ใหม่ bio มี cost ต่ำสุด 458.70 รองลงมาคือ style 465.30 และ score-only 465.60 ส่วน name มี cost 530.80 แม้ name จะให้ Recall สูงสุด 0.7241 แต่สร้าง FP 69 คู่ เทียบกับ bio เพียง 3 คู่
>
> อย่างไรก็ตาม ตารางนี้ยังไม่ใช่ current winner เพราะ threshold เหล่านั้นถูกค้นหาภายใต้ objective เก่า เราใช้ตารางนี้เพื่อวิเคราะห์ sensitivity ว่า policy เดิมตอบสนองอย่างไรเมื่อ business weights เปลี่ยนเท่านั้น

### วิธีอ่านตารางให้ถูกต้อง

> ถ้าดู Recall อย่างเดียว name ชนะ แต่ถ้าดู cost จาก counts ของ policy เดิม bio ชนะ นี่ไม่ใช่ความขัดแย้ง เพราะคำว่า “ดีที่สุด” เปลี่ยนตาม metric และ objective ที่ใช้ตัดสิน

**ประโยคเชื่อม:**

> ก่อนสรุปว่า guard ใดน่าเชื่อถือ เราต้องตรวจด้วยว่า evidence นั้นมีให้ใช้ในกี่เปอร์เซ็นต์ของคู่ทั้งหมด

---

## 13.4 Availability Coverage (ประมาณ 1.5 นาที)

### หัวข้อนี้ทำอะไร

วัดว่าแต่ละ evidence group มีข้อมูลพร้อมใช้จริงมากน้อยเพียงใด และเมื่อ score สูงมีโอกาสเป็น positive เท่าไร

### สคริปต์พูด

> Name มี availability 99.42 เปอร์เซ็นต์ จึงใช้ได้เกือบทุกคู่ Bio และ style มีประมาณ 66.18 เปอร์เซ็นต์ URL มี 67.93 เปอร์เซ็นต์ Image มีเพียง 10.02 เปอร์เซ็นต์ และ location ไม่มี usable evidence ใน validation run นี้
>
> Image มี high-score positive rate เท่ากับ 1.0 ดูเหมือนแม่นมาก แต่พบในคู่เพียงประมาณ 10 เปอร์เซ็นต์ เราจึงไม่ควรใช้ image เป็น global default ควรใช้เป็น positive evidence เฉพาะเมื่อภาพพร้อมทั้งสองฝั่ง
>
> Availability mask มีหน้าที่แยกสองกรณีออกจากกัน คือ similarity ต่ำจริง กับไม่มีข้อมูลให้เปรียบเทียบ ถ้าไม่มี mask ค่า missing อาจถูกแทนด้วยศูนย์และทำให้ระบบ reject คู่โดยไม่มีหลักฐาน

### ข้อสรุปของหัวข้อนี้

> Reliability ต้องอ่านคู่กับ coverage เสมอ Evidence ที่แม่นในกลุ่มเล็กอาจมีประโยชน์มากเมื่อ available แต่ไม่สามารถแทนสัญญาณที่ครอบคลุมทั้ง population ได้

**ประโยคเชื่อม:**

> ต่อไปต้องแยกอีกเรื่องหนึ่งที่มักสับสน คือ feature ที่สำคัญต่อ model ไม่จำเป็นต้องเป็น guard ที่ลด business cost ได้ดีที่สุด

---

## 13.5 Model Weights ไม่เท่ากับ GA Weights (ประมาณ 1.5 นาที)

### หัวข้อนี้ทำอะไร

แยกบทบาทของ feature importance ภายใน pair scorer ออกจาก evidence weight หรือ guard ใน decision policy

### สคริปต์พูด

> Model feature importance ตอบว่า feature ใดช่วยจัดอันดับ probability ของคู่ทั้งหมด ส่วน GA guard ตอบว่า ในบริเวณที่ model ยังไม่แน่ใจ evidence ใดช่วยเลื่อนหรือลดคำตัดสินแล้วทำให้ business cost ต่ำลง
>
> สองคำถามนี้ใช้ population และ objective ต่างกัน Feature อาจสำคัญมากต่อ model แต่เมื่อถูกนำมาใช้เป็น hard guard อาจเพิ่ม false positives หรือ false negatives ได้ ในทางกลับกัน feature ที่มีบทบาทรองใน model อาจช่วยแยกบางคู่ใน review band ได้ดี
>
> ดังนั้นเราไม่สามารถนำ feature importance ไปใช้เป็น GA weight โดยตรง และไม่สามารถใช้ผล GA guard เพื่อสรุปว่า feature นั้นสำคัญที่สุดต่อ model

### ประโยคสรุป

> Model importance คือ contribution ต่อ score ส่วน GA utility คือ contribution ต่อ decision cost

---

## 13.5.1 Proof: Feature มีผลต่อ Model มากน้อยเพียงใด (ประมาณ 2 นาที)

### หัวข้อนี้ทำอะไร

ใช้ permutation importance พิสูจน์ผลของแต่ละ feature และ evidence group ต่อ Gradient Boosting บน validation

### ทำอย่างไร

1. วัด Average Precision ของ model ก่อนสลับข้อมูล
2. สลับค่าของ feature หนึ่งตัวหรือหนึ่ง group เพื่อทำลายความสัมพันธ์กับ label
3. ให้ model เดิมทำนายใหม่โดยไม่ retrain
4. วัด AP ที่ลดลง
5. AP delta สูงหมายถึง model พึ่ง feature นั้นมาก

### สคริปต์พูด

> วิธีพิสูจน์คือ permutation importance เราเก็บ model เดิมไว้ แล้วสลับค่าของ feature บน validation ทีละส่วน ถ้าสลับแล้ว Average Precision ลดลงมาก แปลว่า model เคยพึ่งข้อมูลส่วนนั้นในการจัดอันดับคู่
>
> ผลระดับ group พบว่า Name มี sum AP delta 0.277651 สูงที่สุดอย่างชัดเจน Bio อยู่ที่ 0.011153 กลุ่ม platform และ availability อยู่ที่ 0.004224 Style 0.001577 URL 0.001100 Image 0.000908 และ Location เท่ากับศูนย์
>
> เมื่อดูราย feature ตัวที่มีผลสูงสุดคือ `username_token_sort` 0.127410 ตามด้วย `fullname_token_sort` 0.071982, `fullname_jaro` 0.041630 และ `username_jaro` 0.021471 จึงพิสูจน์ได้ว่า name token และ character similarities เป็นสัญญาณหลักของ pair scorer ในข้อมูลชุดนี้ ส่วน `bio_tfidf_cosine` เป็นสัญญาณรองที่มีผลจริง

### สิ่งที่ผลนี้พิสูจน์และไม่พิสูจน์

**พิสูจน์ได้:**

> Pair model ปัจจุบันพึ่ง name มากกว่า evidence group อื่นอย่างชัดเจนบน validation ชุดนี้

**ยังพิสูจน์ไม่ได้:**

> Name เป็น causal signal, name ต้องได้ GA weight สูงสุด หรือ name guard พร้อมใช้งาน production

**ข้อควรระวัง:**

> AP delta ต่ำของ image และ location ต้องอ่านร่วมกับ coverage ที่ต่ำ ไม่ควรสรุปว่า evidence เหล่านี้ไม่มีคุณค่าใน dataset ที่สมบูรณ์กว่า

**ประโยคเชื่อม:**

> หลังทดลอง guard ทีละตัว ขั้นต่อไปคือให้ GA ผสม evidence หลายชนิดด้วยน้ำหนักที่เรียนรู้ร่วมกัน

---

## 13.6 Weighted GA Result (ประมาณ 1.5 นาที)

### หัวข้อนี้ทำอะไร

ให้ GA เรียนน้ำหนักของหลาย evidence groups แทนการเลือก guard เพียงกลุ่มเดียว

### สคริปต์พูด

> Historical weighted GA เรียนน้ำหนัก name 0.3939, style 0.3043, image 0.1833, URL 0.1186 และ bio 0 ผลลัพธ์มี FP 28, FN 56 และ REVIEW 3,892 เมื่อ re-score ด้วย CRM cost ใหม่ได้ 501.20 ซึ่งยังแพ้ bio selector ที่ 458.70
>
> การที่ bio selector ชนะ แต่ bio weight ใน weighted GA เป็นศูนย์ไม่ใช่ contradiction เพราะ selector กับ weighted aggregate เป็น hypothesis class คนละแบบ Selector ใช้กฎจาก bio เพียงตัวเดียว ส่วน weighted GA ต้องหาส่วนผสมและ thresholds พร้อมกัน ทำให้ optimization landscape และคำตอบที่ได้ต่างกัน

### ข้อควรระวัง

> น้ำหนักชุดนี้เป็นผล historical labeled run ไม่ใช่น้ำหนัก production และไม่ใช่ feature importance ของ Gradient Boosting

### ผลทดลอง one-stage policy v2

> รอบใหม่ตัด name promote/demote cutoffs ออก เหลือ threshold สองตัวและ policy weights แปดตัวจาก frozen probability, name, bio, URL, location, social, image และ style บน validation 8,580 คู่ one-stage มี median cost 380.0 จาก 10 seeds เทียบ score-only 385.9 และ legacy name guard 475.0 โดย 9 ใน 10 seeds ผ่าน Precision 0.99 และ Recall 0.70
>
> Best seed ได้ Precision 0.9933, Recall 0.8144 และ cost 378.5 น้ำหนักหลักคือ frozen probability 0.9222 ส่วน image 0.0330, name 0.0272 และ URL 0.0176 Location กับ social ถูก fix เป็นศูนย์เพราะ coverage ไม่ผ่าน gate จึงห้ามสรุปว่าไม่มีประโยชน์ และแม้ explicit name weight ต่ำก็ห้ามสรุปว่า model ไม่ใช้ชื่อ เพราะ probability ถูกเรียนจาก name features อยู่แล้ว
>
> ผลนี้ยังเป็น validation-only; historical test ไม่ถูกเปิดซ้ำ และ review capacity ยังไม่ถูกกำหนด

**ประโยคเชื่อม:**

> เมื่อเลือก policy จาก validation แล้ว ขั้นตอนที่ถูกต้องคือ freeze policy ก่อนเปิด test

---

## 13.7 Sealed-Test Result (ประมาณ 1.5 นาที)

### หัวข้อนี้ทำอะไร

ประเมิน historical `bio` selector บน test ที่ไม่ได้ใช้ระหว่างการเลือก policy

### สคริปต์พูด

> หลังเลือก bio บน validation เรา freeze policy แล้วเปิด sealed test หนึ่งครั้ง ผลคือ Precision 0.9973, Recall 0.5924 และ F1 0.7433 มี FP 7, FN 63, REVIEW 3,812 และ CRM-derived cost 458.20
>
> ผลนี้แสดงว่า policy คุม false positive ได้ดีมาก แต่ recall ต่ำ หมายความว่าระบบระมัดระวังจนพลาด true matches จำนวนมาก นอกจากนี้ labeled feature population มี 58,696 คู่ และ overlap กับ full scored candidates เพียง 20,757 คู่ หรือ 1 เปอร์เซ็นต์ จึงใช้เป็น proof of mechanism ว่า workflow freeze แล้ว test ได้ แต่ยังใช้ promote production ไม่ได้

### จุดเน้น

> Sealed test ที่ถูกต้องไม่ได้แปลว่า population นั้นแทน production population ได้เสมอ ต้องตรวจ population coverage เพิ่มด้วย

**ประโยคเชื่อม:**

> เพื่อทดสอบกับ distribution ที่ใกล้ workflow จริงมากขึ้น เราจึงสร้าง evidence cache ครบกว่า 2.07 ล้าน scored candidates

---

## 13.8 ผลรันเต็ม 2.07 ล้าน Scored Candidates (ประมาณ 2.5 นาที)

### หัวข้อนี้ทำอะไร

ขยาย feature-aware decisioning จาก labeled subset ไปยัง full scored-candidate population จำนวน 2,073,842 คู่ใน 42 parquet chunks

### สคริปต์พูดส่วนแรก: historical style policy

> Full historical-cost run เลือก style ก่อนเปิด test หนึ่งครั้ง เมื่อดู scored sealed test ได้ Precision 0.9985 แต่ Recall เพียง 0.1604 และ F1 0.2764 เมื่อรวม exact tier และ blocking misses เป็น system sealed test Recall เพิ่มเป็น 0.4995 และ F1 เป็น 0.6656
>
> Full system projection ได้ Precision 0.9937, Recall 0.4949, F1 0.6607, FP 92, REVIEW 34,955 และ cost 9,963.50 ผลนี้มี precision สูง แต่สูญเสีย recall มาก จึงไม่ใช่ policy ที่สมดุล

### ทำไม scored กับ system metric ต่างกัน

> Scored metric วัดเฉพาะคู่ที่ model ให้คะแนน ส่วน system metric รวม exact matches และ false negatives จาก blocking miss ความต่างของตัวเลขจึงเกิดจาก evaluation boundary ไม่ใช่การคำนวณขัดกัน

### สคริปต์พูดส่วนที่สอง: เปรียบเทียบ R0, R3 และ style

> เมื่อเปรียบเทียบ full projection ภายใต้ cost ใหม่ R0 baseline มี F1 0.7882 และ cost 16,037.60 R3 name GA มี F1 สูงสุด 0.8345 และ costต่ำสุด 7,384.10 ส่วน historical style GA มี F1 0.6607 และ cost 9,963.50
>
> เหตุผลที่ R3 ชนะหลัง re-score คือ cost ของ REVIEW เพิ่มจาก 0.02 เป็น 0.1 Historical style policy ยังทิ้ง REVIEW 34,955 คู่ ขณะที่ R3 เหลือ 2,751 คู่ ผลนี้ยืนยันว่า policy winner ขึ้นกับ business weights

### ข้อสรุปสำคัญ

> เมื่อ objective เปลี่ยน ต้อง rerun search การนำ policy เก่ามาคำนวณ cost ใหม่ใช้เปรียบเทียบย้อนหลังได้ แต่ไม่รับประกันว่าจะเป็น policy ที่ดีที่สุดภายใต้ objective ใหม่

**ประโยคเชื่อม:**

> เพราะฉะนั้นขั้นตอนสุดท้ายคือ re-optimize GA จริงบน full validation ด้วย CRM cost เวอร์ชันปัจจุบัน

---

## 13.9 CRM-Cost Validation-Only Rerun (ประมาณ 2.5 นาที)

### หัวข้อนี้ทำอะไร

Reuse feature cache 2,073,842 คู่ แต่ค้นหา policy ใหม่บน validation เท่านั้นด้วย objective `crm_derived_v1`

### สคริปต์พูดผล selector

> ผล rerun ล่าสุดพบว่า name selector มี validation cost ต่ำสุด 3,498.60 ได้ Precision 0.9853, Recall 0.6240 และ F1 0.7641 โดยมี FP 89, FN 2,189 และ REVIEW 11,316
>
> Bio มี cost 3,761.40, style 3,808.70, score-only 3,810.30, image 3,975.50 และ URL 4,943.20 ส่วน weighted GA มี cost 4,897.10, Precision 0.9293, Recall 0.5691 และ F1 0.7059 จึงแพ้ name selector ภายใต้ scalar cost ปัจจุบัน

### ทำไม name ชนะรอบนี้ แต่ bio หรือ style เคยชนะ

> ทั้งสามผลมาจากคนละ experiment condition Bio ชนะ historical labeled-subset policy หลัง re-score, style ชนะ historical full run ภายใต้ objective เก่า และ name ชนะ current full-validation search ภายใต้ CRM cost ใหม่ จึงไม่ใช่ผลเดียวกันที่ขัดกัน

### Promotion gates

> ถึง name จะมี cost ต่ำสุด แต่ Precision 0.9853 ยังต่ำกว่า gate 0.99 และ Recall 0.6240 ยังต่ำกว่า gate 0.70 ดังนั้น scalar-cost winner ไม่ใช่ production winner Artifact จึงระบุ `test_evaluated=false` เรา freeze ผลไว้สำหรับพัฒนา constrained objective และไม่เปิด test เดิมซ้ำ

### แนวทางถัดไป

> รอบถัดไปควร minimize cost ภายใต้ข้อจำกัด Precision อย่างน้อย 0.99 และ Recall อย่างน้อย 0.70 แทนการ minimize scalar cost อย่างเดียว ถ้าไม่มี policy ผ่าน gates ต้องปรับ retrieval, representation หรือ review policy ไม่ใช่ลด gate เพื่อให้ผลผ่าน

### ข้อสรุปที่พูดแล้วไม่ conflict

> Name เป็น evidence group ที่สำคัญที่สุดต่อ pair model และเป็น scalar-cost winner ใน current full validation แต่ปัจจุบันยังไม่มี selector หรือ weighted policy ใดผ่าน production gates

---

# สรุปข้อ 13 (ประมาณ 1 นาที)

**พูดว่า:**

> ข้อ 13 แสดงให้เห็นว่า decision optimization ต้องแยกจาก model training อย่างชัดเจน เราเริ่มจากแปลงเวลาทำงานเป็น CRM cost ใช้ GA ค้นหา thresholds และ evidence guards จาก frozen probability จากนั้นตรวจทั้ง coverage, model importance, sealed test และ full population
>
> หลักฐานปัจจุบันสรุปได้สามข้อ หนึ่ง name มีผลต่อ pair score สูงสุด สอง policy winner เปลี่ยนได้เมื่อ population และ business objective เปลี่ยน และสาม current name selector แม้มี validation cost ต่ำสุด แต่ยังไม่ผ่าน Precision และ Recall gates จึงยังไม่พร้อม production

---

# คำถามที่คาดว่าจะถูกถามเฉพาะข้อ 13

## GA เปลี่ยนน้ำหนักของ Gradient Boosting หรือไม่

> ไม่เปลี่ยน Model, scaler และ isotonic calibrator ถูก freeze ก่อน GA เริ่มทำงาน GA ใช้ calibrated probability ที่ได้แล้วและปรับเฉพาะ decision thresholds กับ evidence policy

## ทำไมไม่ใช้ F1 เป็น objective ของ GA

> เพราะ F1 ไม่สะท้อนต้นทุนของ FP, FN และ REVIEW ที่ต่างกัน โดยเฉพาะ REVIEW ซึ่งไม่มีอยู่ใน binary F1 Business cost ทำให้เราประเมิน three-way decision ตามภาระงานจริงได้

## ทำไม false positive มีน้ำหนัก 2

> จากสมมติฐานเวลาปฏิบัติงาน FP ใช้เวลาแก้ 20 นาที ขณะที่ FN ใช้ 10 นาที หลัง normalize ด้วย FN จึงมีน้ำหนัก 2 ต่อ 1

## ทำไม review มีน้ำหนัก 0.1

> Review ใช้เวลาประมาณ 1 นาที เทียบกับ FN 10 นาที จึงได้ 0.1 หลัง normalize

## Feature ใดแทน name similarity ได้

> จากหลักฐานปัจจุบันยังไม่มี feature group ใดแทน name ใน pair scorer ได้ Name มี permutation AP delta 0.277651 สูงกว่ากลุ่มอื่นมาก Bio มีประโยชน์รอง แต่ยังไม่ใช่ replacement ที่พิสูจน์แล้ว

## Bio weight เป็นศูนย์ แต่ทำไม bio selector เคยชนะ

> เพราะ one-guard selector กับ weighted aggregate เป็น policy คนละรูปแบบและมี search space ต่างกัน Weight ศูนย์ใน weighted historical run ไม่ได้ลบผลของ bio selector experiment

## ทำไม current winner ยังไม่เปิด test

> Current winner ไม่ผ่าน validation gates ตั้งแต่ก่อนเปิด test การเปิด test ต่อจะไม่เปลี่ยนสถานะ promotion และอาจทำให้ test ถูกใช้วนซ้ำในการพัฒนา จึงเก็บ test sealed ไว้

## R3 กับ current name selector เป็นตัวเดียวกันหรือไม่

> ไม่ใช่ R3 เป็นผลใน R-series common harness ส่วน current name selector มาจาก full-validation feature-aware rerun ภายใต้ `crm_derived_v1` ทั้งสองใช้ name evidence แต่ population, genome และ evaluation context ต่างกัน

## Cost ต่ำสุดแปลว่าดีที่สุดหรือไม่

> ดีที่สุดเฉพาะ scalar objective และ population ที่ระบุเท่านั้น สำหรับ production ยังต้องผ่าน Precision, Recall, entity-level over-merge และ operational gates เพิ่มเติม

# ประโยคปิดข้อ 13

> ดังนั้นผลของข้อ 13 ไม่ใช่ว่า GA เลือก feature ใดแล้วจบ แต่เป็นการพิสูจน์ว่า model evidence, decision policy และ business cost ต้องประเมินแยกกัน Current name policy เป็นจุดเริ่มต้นที่ดีที่สุดตาม validation cost แต่ขั้นต่อไปต้องใช้ constrained optimization และ fresh audit test ก่อนนำไปใช้จริงครับ
