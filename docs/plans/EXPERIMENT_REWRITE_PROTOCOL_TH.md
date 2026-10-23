# ร่างวิธีการทดลองใหม่จาก repo audit — 10 ตุลาคม 2026

สถานะ: **ข้อเสนอสำหรับการทดลองรอบใหม่ ยังไม่ได้รันหรือแทนที่ผลเดิม**

อ้างอิง [ผลตรวจทั้ง repo](../reports/ICSEC_REVIEW_REPO_AUDIT_TH.md) เป้าหมายตั้งต้นคือประเมินการจับคู่ทั้ง workflow และแยกว่าการปรับ retrieval, representation และ decision policy ช่วยส่วนใด โดยวัด GA เทียบกับวิธีที่ง่ายกว่าภายใต้เงื่อนไขเดียวกัน ขอบเขตนี้เป็นสมมติฐานทำงานระหว่างรอผู้ใช้ระบุแกนงานวิจัยที่ต้องการ

## คำถามวิจัยและสิ่งที่ต้องได้จากแต่ละส่วน

| คำถาม | การเปรียบเทียบที่ตอบได้ | หลักฐานหลัก |
|---|---|---|
| RQ1: หา positive pairs ได้ครบเพียงใดด้วยต้นทุน candidate เท่าใด | blocking เดิม กับ blocking เดิมรวม lexical retrieval เพิ่ม | retrieval recall, missed positives, candidates/profile, runtime |
| RQ2: representation เพิ่มช่วย scorer หรือไม่ | GB-17 กับ GB-18 บน pairs/splits/training budget เดียวกัน; LR บน feature17 เป็น model baseline | AP, PR curve, calibration, U/automatic metrics ภายใต้ policy protocol เดียวกัน |
| RQ3: policy ที่ซับซ้อนขึ้นช่วยเกินกฎคำนวณตรงและ threshold tuning หรือไม่ | fixed, Chow, simple optimum, expanded policy | U, automatic recall/F1, precision, REVIEW+, REVIEW−, coverage |
| RQ4: GA คุ้มกว่าการค้นหาอื่นหรือไม่ | random/Sobol/GA บน expanded class เดียวกัน | best validation U ต่อ actual calls, runtime, unique proposals, test paired differences |

RQ4 ต้องยอมรับผลว่าไม่พบประโยชน์เพิ่มได้ ไม่ตั้งเป้าตัวเลขว่า GA ต้องชนะ หากอาจารย์ต้องการงานใหม่ด้านอัลกอริทึมโดยเฉพาะ empirical study นี้ต้องมี contribution เพิ่มที่ตั้งสมมติฐานและตรวจได้จริง ไม่เพิ่มจำนวน genes เพื่อให้เกิดความใหม่อย่างเดียว

## 1. ล็อก input และหน่วยข้อมูลก่อน

ใช้ `profile_row_id` เป็น ID ของโปรไฟล์หนึ่งแถว ใช้ `entity_id` ที่ map จาก `user_folder` เป็น ID ของบุคคล/ground-truth group ไม่ใช้ชื่อ `profile_id` สลับสองความหมายแบบหลายไฟล์เดิม

สำหรับทุก input snapshot ให้มี source URI/revision เท่าที่มี, SHA-256, schema, จำนวนโปรไฟล์/แพลตฟอร์ม/entities และรายการกฎ exclude ต้องตรวจ duplicate profile rows, repeated platform ภายใน entity, missing entity และ mapping ID ก่อนสร้าง pairs กรณีไม่รู้ entity ต้องเป็น unknown label หรืออยู่นอก supervised experiment ห้ามถือเป็น negative โดยอัตโนมัติ

Raw directory ใน workspace ปัจจุบันว่างและไม่มี `.gitmodules` ดังนั้นมีสองสถานะที่ต้องเขียนให้ตรงความจริง:

- เริ่มรอบใหม่จาก normalized snapshot 36,807 แถวที่มีอยู่: ทำได้หลัง validation และเรียกว่า snapshot-based reanalysis; eligible counts ต้องคำนวณจากกฎใหม่ ไม่ hard-code ให้เท่าของเดิม
- หากต้องการอ้าง raw-to-result reproduction: ต้องมี raw source รุ่นที่ตรงกันและตรวจสิทธิ/ที่มาก่อนจึงจะทำส่วนนี้ครบ การคัดลอก notebook เก่าไม่เติมหลักฐาน raw ที่หาย

เก็บ original field กับ normalized field คนละคอลัมน์; normalization เป็น deterministic rules ไม่ใช้ label หรือ model probability; ลำดับโปรไฟล์ก่อน encoding ต้องมี ID index ควบคู่ embeddings

## 2. ใช้ split เดียวตลอด scorer → calibration → policy → test

ข้อเสนอตั้งต้น: แบ่ง entity เป็น **5 folds** โดยตรึง seed และสมดุลจำนวน entity/platform coverage เท่าที่ทำได้ สำหรับ outer fold i ใช้ TEST=i, CALIBRATION=(i+1) mod 5, POLICY_VALIDATION=(i+2) mod 5 และ TRAIN=อีกสอง folds เท่ากับประมาณ **40/20/20/20**

ข้อเสนอนี้ทำให้ calibration/policy/test มีขนาด cohort ใกล้กัน ลด prior shift ที่เกิดจาก role sizes 10.5% เทียบ 30% ใน V2R1 แต่ไม่ได้รับประกันว่าการกระจายทุก feature หรือ posterior จะตรงกัน ต้องตรวจ positive rates จริงทุก role เสมอ เป้าหมายที่วัดคือการจับคู่ภายใน cohort ที่ประกาศขนาด ไม่อ้างว่า probability เหมือนการ search ในฐานข้อมูลเต็มทุกขนาด

กฎต่อคู่:

1. ปลายทั้งสองของ positive/negative pair ต้องเป็น entity ใน role เดียวกัน
2. คู่ข้าม role ไม่เข้า fit, policy selection หรือผลของ role ใด; เก็บจำนวนที่ drop เพื่ออธิบาย population
3. ฟังก์ชันสร้าง candidate ใช้เพียง profile evidence ของ cohort นั้น; labeler เป็นขั้นแยก
4. จำนวน positives ทั้งหมดของแต่ละ roleมาจาก ground truth cross-platform ภายใน role ไม่ใช่จำนวนที่ blocking คืนมา
5. shared preprocessing ที่ต้องเรียนค่า เช่น TF-IDF fit เฉพาะ TRAIN; frozen pretrained encoder ใช้ encode ทุก role ได้ แต่ต้องตรึง model revision/text composition
6. ตรวจ disjointness จาก entity ของทั้งสองปลายจริง ไม่ตรวจเฉพาะ entity_a หรือ pseudo entity เช่น `role:TRAIN`

5 outer folds เป็นการขยายการประเมินแบบมีโครงสร้าง ไม่เป็นหลักประกัน statistical power และ training sets ข้าม outer foldsยังทับกันได้ ให้รายงาน paired differences โดยไม่ถือทุก fold/optimizer seedเป็น independent observations

ข้อมูล corpus นี้ถูกใช้พัฒนาและดูผลมาแล้ว การเปลี่ยน seed/ตั้งชื่อ SEALED_TEST ใหม่ไม่ทำให้เป็น dataset ที่ไม่เคยถูกสำรวจ ประกาศการทดลองใหม่ว่าเป็น retrospective reanalysis ที่ตรึง protocol ก่อนรัน หากจะอ้าง external generalization ต้องมี corpus หรือข้อมูลอิสระเพิ่ม

## 3. ทำ retrieval experiment ขนาดเล็กที่ตอบข้อจำกัดจริง

เริ่มจากสองวิธี:

| Retrieval | กฎ | การเลือกค่าที่ต้องใช้ label |
|---|---|---|
| C0 | exact username/URL + prefix3 username/fullname + external-domain เดิม | ตรึงกฎเป็น historical baseline |
| C1 | union ของ C0 กับ top-k lexical character-ngram similarity ข้ามแพลตฟอร์ม | เลือก k/budget จาก development เท่านั้น |

สำหรับ C1 ใช้ character TF-IDF/nearest-neighbor tools ที่ติดตั้งอยู่แล้ว ถ้า vectorizer มี vocabulary/IDF ให้ fit บน TRAIN แล้ว transform บทบาทอื่น ให้ candidate budget ที่เทียบกันได้และระบุว่า top-k ต่อ query/target-platform จากนั้น canonicalize/deduplicate unordered pairs

ตั้ง k candidates ที่จะพิจารณาล่วงหน้า เช่น {10,20,50}; เลือกจาก POLICY_VALIDATION ตามเป้าหมาย retrieval recall/candidate budget ที่เขียนใน protocol ก่อนเปิด TEST รายงาน complete retrieval trade-off และจำนวน recovered positives/new negatives ไม่เลือกจาก test recall

แยกผลอย่างน้อยตาม platform pair, available/missing name/bio และ name similarity ต่ำ การวัด lexical retrieval อีกวิธีหนึ่งไม่ได้พิสูจน์ superiority ต่อทุก semantic/graph retrieval method

เลือก C0 เป็น retrieval ที่ตรึงสำหรับ RQ2–RQ4 เพื่อให้เปลี่ยนปัจจัยเดียว แล้วทำ C1 กับ scorer+policy ที่เลือกจาก development เป็นการทดลองเพิ่มผลทั้ง workflowหนึ่งชุด การ train/evaluate ใต้ C1 ต้องใช้ candidate population ของ C1 ตามบทบาท ไม่เอาผลคนละ candidate set มาลบกันแล้วเรียกว่า optimizer gain

## 4. Train scorer อย่างมี comparator ที่เกี่ยวข้อง

ชุดขั้นต่ำ: LR-17, GB-17, GB-18 โดย GB-17/18 ใช้ split/training pair keys/model parameters เหมือนกัน ต่างเฉพาะ MiniLM cosine หนึ่งคอลัมน์

- ใช้ corrected label-free feature17; คำนวณ name similarity ทุกคู่ที่ต้องใช้ ไม่ gate ด้วย probability จาก scorer เก่า
- TRAIN อาจ undersample negatives เช่น 3:1 แต่ต้องบันทึก chosen pair-key hash และ reuse sample เดียวกันเมื่อเทียบ representation
- CALIBRATION/POLICY_VALIDATION/TEST ใช้ candidate population เต็มตาม cohort ของตน; ไม่สุ่มให้อัตรา positive เท่าชุด supervised benchmark เก่า
- ตรึง model hyperparameters ล่วงหน้าสำหรับ controlled comparison ถ้าจะ tune model ให้ทำ entity-aware inner validation ภายใน TRAIN และคิด budget แยกจาก policy search
- ห้ามใช้ test metrics เป็น tie-break ในการเลือก best model/run; ตรวจ `train_multimodal.main` เดิมที่ sort ด้วย test เป็น secondary keysก่อนนำมาใช้
- บันทึก raw scores, model ID, feature schema/order, preprocessing objects, embedding revision และ pair keys

ยังไม่จำเป็นต้องนำ image/CRM/graph ทุกสายมารวมในรอบแรก หากจะเพิ่มแต่ละชนิดให้เป็น ablation บน protocol เดียวกันและมี input ที่กู้ได้จริง ตารางจากสายเก่าใช้เป็น development history เท่านั้น

## 5. Calibration ต้องตรวจบนข้อมูลที่ calibrator ไม่ได้ fit

ใช้ isotonic เป็น primary calibrator เพื่อให้มีสะพานเทียบประวัติ และกำหนด sigmoid เป็น calibration comparator ล่วงหน้า ถ้าจะเลือก calibrator ให้เลือกจาก development ตาม metric ที่ตรึงไว้ เช่น Brier; รายงานว่าการเลือก calibrator และ policy ใช้ validation เดียวกันและยังต้องมี TEST แยก

รายงาน raw และ calibrated Brier, reliability diagram, positive rate, mean p และ ECE พร้อม bin counts ใน CALIBRATION/POLICY_VALIDATION/TEST; ระบุ CALIBRATION เป็น in-sample fit diagnostic ของ calibrator ไม่อ้างเป็นหลักฐาน generalization

ดูช่วง probability ที่เป็น operating thresholds โดยเฉพาะ หาก score คงที่เป็น plateau ต้องรักษาคู่ที่คะแนนเท่ากันไว้ด้วยกัน ไม่ตัดกลุ่มเพื่อให้ validation loss ดูต่ำลง ไม่ใช้ ECE ค่าเดียวใน population ที่ negative มากตัดสินว่า “calibrate ดีแล้ว”

ถ้าต้อง deploy กับขนาดฐานข้อมูล/positive prior ต่างจาก cohort ที่ทดลอง ต้องกำหนด target population และแผน calibration ใหม่จาก deployment-representative development data ก่อน การใส่ prior correction ต้องประกาศสมมติฐานและห้ามประมาณจาก TEST labels

## 6. Policy ladder ที่ตีความได้

| Policy | มีการค้นหาหรือไม่ | บทบาท |
|---|---|---|
| P0 fixed .98/.95 | ไม่มี | historical baseline ที่ระบุว่าค่าถูกเลือกจากระบบเดิม |
| P1 direct posterior risk (Chow) | ไม่มี | baseline จาก cost matrix; เลือก argmin ของความเสี่ยงสาม action |
| P2 simple empirical optimum | ค้นหาที่ unique calibrated-score breakpoints บน validation | baseline สอง threshold ที่ไม่ขึ้นกับ luck ของ optimizer |
| P3 expanded-name random | มี | reference ของ search ใน expanded policy |
| P4 expanded-name Sobol | มี | space-filling reference |
| P5 expanded-name GA | มี | ทดสอบประโยชน์จาก optimizer |

สำหรับ costs (FP,FN,REVIEW)=(2,1,.1) และ review มี fixed cost ต่อคู่/ไม่มี human error penalty เพิ่ม ความเสี่ยงคือ `R(NO_MATCH)=p`, `R(REVIEW)=.1`, `R(MATCH)=2(1-p)` ให้ใช้ argmin โดยประกาศ tie order ค่าขอบ .1/.95 เป็นกรณีของ cost นี้เท่านั้น หากค่า review สูงจน reviewไม่คุ้มใน scenario อื่น argmin จะจัดการได้โดยไม่บังคับสอง threshold ผิดรูป

P2: รวมคู่ที่ p เท่ากันแล้วนับ class counts ใช้ cumulative losses ของ NO_MATCH/REVIEW/MATCH เพื่อหา ordered cuts ที่ดีที่สุด รวม all-MATCH/all-NO_MATCH/no-REVIEW edge cases ตรวจผลกับ brute-force ใน fixture เล็ก วิธีนี้ค้นหาสอง threshold ได้ครบตามคะแนนที่มีและเป็น baseline ที่เหมาะก่อนใช้ search จำนวนมาก

Expanded policy ใหม่ต้องมีพารามิเตอร์ที่ปิด name gate ได้จริงและคืน P2 ได้ทุกแถว วิธีที่เสนอคือใช้ `s > c_promote` สำหรับ promotion และ `s < c_demote` สำหรับ demotion ภายใน review band; เมื่อ `c_promote=1,c_demote=0` จะปิดทั้งสอง gate สำหรับ s∈[0,1] นี่เป็น **นิยามใหม่** ต่างจาก V2 ที่ใช้ >= ต้อง version และทดสอบขอบอย่างชัดเจน ไม่เปลี่ยน source ของ frozen V2

ให้ `0<=t_review<=t_match<=u` โดย `u=nextafter(1,+inf)` เป็นขอบ sentinel เพื่อแทน all-NO_MATCH ได้แม้ p=1 และให้ `0<=c_demote<=c_promote<=1`; ใช้ representation/repair เดียวกันสำหรับ random/Sobol/GA และบันทึกว่าการ sort/clip เปลี่ยนการกระจายของ proposals อย่างไร กรณี name missing ให้ gateไม่ทำงานและปล่อยผลเป็น REVIEW ตาม probability band; ให้ missingness เป็น explicit mask ไม่ตีความ zero score เป็นหลักฐานปฏิเสธเสมอ

นำ P2 optimum มาเป็น incumbent candidate เริ่มต้นของทั้งสาม optimizers อย่างเท่ากัน และนับ objective call เท่ากัน รายงานทั้งผลที่ได้จาก initialized incumbent และส่วนที่ search ทำให้ดีขึ้น

## 7. Optimizer protocol ที่ไม่ปน split seed กับ GA seed

- มี 5 outer folds และ **5 internal optimizer seeds** ต่อ fold สำหรับ GA/random; Sobol แบบ scrambleใช้ 5 scrambles เช่นกันและบันทึก configuration ถ้าต้องเก็บ unscrambled historical referenceให้เป็นผลประกอบคนละ label
- budget หลักเสนอ **2,048 actual objective evaluations** ต่อ run; checkpoints **128/512/2,048** ไม่รันต่อจน GA ชนะ หากต้องการงบสูง 8,192 ให้กำหนดเป็น secondary budget ก่อนเริ่ม
- ใช้ objective/data/policy bounds/initial incumbentเหมือนกัน บันทึก actual calls, unique parameter vectors, unique decisions เมื่อทำได้, wall-clock time และ incumbent vector/loss
- ระบุ population, parent selection, crossover, mutation probability/σ, elitism, boundary repair และ seed policy ให้ครบ เลือก implementation หนึ่งชุดให้ชัด ไม่เรียก R1 GA กับ V2 GA ว่าเหมือนกัน
- เปรียบเทียบ distribution ของ runs ภายใน fold และ paired per-fold test outcomes ห้ามนับ 25 optimizer runs เป็น 25 independent datasets
- ถ้าต้องส่ง deployment policy เพียงหนึ่งตัว ให้เลือกจาก validation ตามกฎ tie-break ที่ประกาศก่อนเปิด TEST และรวมงบของทุก seed ที่ใช้ค้นหาในการรายงาน

จำนวนดังกล่าวเป็น starting design เพื่อแยกปัจจัย ไม่ใช่ power calculation ที่รับประกันว่าจะพบความต่างเล็กมาก งาน pilot ใช้ development เท่านั้นเพื่อวัด runtime/ความแปรปรวนก่อน freeze ตัวเลขสุดท้าย

## 8. Metrics ที่ใช้ร่วมกันทั้ง repo รอบใหม่

สำหรับ cohort/test universe เดียวกัน กำหนด:

- TP/FP = positive/negative ที่ถูก MATCH ทั้ง exact และ model-scored
- FN = positive ที่ถูก NO_MATCH รวม positives ที่ candidate generation พลาด
- R+ / R− = positives/negatives ใน REVIEW; REVIEW = R+ + R−
- TN = negative ที่ถูก NO_MATCH ใน candidates; ถ้าจะรายงาน TN ทั้ง universe ต้องนับ ungenerated negatives อย่างชัดเจน
- `automatic_recall = TP / (TP + FN + R+)`
- `automatic_F1 = 2TP / (2TP + FP + FN + R+)`
- `decision_recall = TP / (TP + FN)` เป็น conditional secondary metric
- `precision = TP / (TP + FP)`
- `U = c_FP*FP + c_FN*FN + c_REVIEW*REVIEW`
- candidate coverage = `1 - REVIEW / (exact + scored candidates)` ระบุว่าตัวส่วนไม่รวม blocking misses

ทุกตารางมี counts, denominator, scope, outer fold, policy/model ID และ cost scenario ค่าเฉลี่ยใช้ convention เดียวกันพร้อมราย fold; pair-model AP/F1 แยกจาก workflow quality รวมทั้งรายงาน exact-tier precisionและจำนวน errors ที่ gate นี้ทำให้แก้ไม่ได้

เพิ่ม risk–coverage/quality–review-load curves ที่ policy points กำหนดจาก development ล่วงหน้า แสดง class-specific counts เพราะ overall coverage ถูกครอบงำด้วย negative จำนวนมาก ไม่สมมติ human reviewถูก 100% เป็นผลจริง หากแสดง perfect-review recallให้ติดป้ายว่า optimistic scenario

สำหรับ validation–test comparison แสดง U พร้อม N/positive support และ U ต่อ 10,000 candidates โดยใช้ component scope เดียวกัน การเอา validation search loss ที่ไม่มี exact/missesไปลบกับ full test U ไม่ใช่ overfitting gap ที่ตีความตรง ๆ ได้

## 9. Statistical reporting และ cost sensitivity

ใช้ paired differences ของแต่ละ outer foldเป็นผลหลัก รายงาน median/range ของ optimizer repeats ภายใน foldและ mean/SD ข้าม foldsโดยบอกว่าไม่ได้อิสระทั้งหมด ใช้คำว่า “ยังไม่มีหลักฐานว่าดีกว่า” เมื่อข้อมูลไม่พอ ไม่ตีความ null resultเป็น equivalence

ยังไม่ใช้ pair-wise iid bootstrapเดิมเป็น CI ของผู้ใช้ทั้งหมด หากจำเป็นต้องมี CI ให้กำหนด entity/query resampling ที่จัดการ negative pairสองปลายได้และทำ paired drawsร่วมกัน รวมผลของ exact/missesตาม estimandที่ประกาศ หรือจำกัดให้เป็น conditional pair diagnostic และติดป้ายข้อจำกัด

Cost scenarios ขั้นต่ำ: FN=1, FP∈{1,2,5}, REVIEW∈{.05,.1,.2} สำหรับแต่ละ scenario:

1. ปรับ Chowจาก cost matrix โดยตรง
2. เลือก P2/expanded policiesใหม่บน POLICY_VALIDATION เท่านั้น
3. freeze policiesทั้งเก้า scenariosก่อน batch test evaluation
4. รายงาน winner/ranking, trade-offและจำนวน REVIEW พร้อม costs ทั้ง rawและnormalized

ตาราง reweight frozen outcomesใน auditเป็น exploratory diagnostic ใช้แสดงว่าข้อสรุปขึ้นกับต้นทุน แต่ไม่ใช่ผลการ optimizeที่ต้นทุนแต่ละชุด การเพิ่ม scenarioอื่นหลังดู testต้องติดป้าย post-hoc

## 10. รูปแบบรันที่เล็กและตรวจสอบได้

ใช้ตัวรันการทดลองหนึ่งตัวภายใต้ `experiments/code/` ประกอบฟังก์ชันที่มีอยู่และตรวจแล้ว เขียน output ภายใต้ `artifacts/experiments/rebuild_v1/<run_id>/` แบบปฏิเสธ overwrite โดย default; ไม่มี global module patch ค้างข้าม experiment และไม่ glob score chunksของคนละ run

แต่ละ runเก็บ input/source hashes, environment lock, split manifests, model/calibrator/schema, validation-selected parameters, search traces, label-free test predictions, freeze manifest และ derived metrics/reports แยก origin ของ runเก่าและใหม่อย่างชัดเจน Hashยืนยันว่า bytesไม่เปลี่ยน ไม่ได้พิสูจน์ว่าการเลือกการทดลองไม่เคยได้รับอิทธิพลจากผลเก่า

ประเมิน testทุกวิธีที่ freezeไว้ใน batchเดียว แล้วให้ตาราง/รูป/ข้อความดึงจาก metrics fileกลาง ห้ามพิมพ์ค่าที่แก้มือในบทความโดยไม่มี source row/model/policy mapping

## ลำดับลงมือและเกณฑ์ผ่าน

| ลำดับ | งาน | ผ่านเมื่อ |
|---|---|---|
| A | input snapshot + field/ID/label audit | traceจำนวนแถวและ exclusionsได้; ไม่มี ID/label contradiction; ระบุ raw limitation |
| B | split + evaluator + minimal fixtures | สองปลายไม่รั่ว; positives = TP+FN+R+; candidate covered+missed=all positives; toy Chowถูก |
| C | repair run isolation/cache/preprocessing | รัน variantเดี่ยว/ต่อกันได้ schemaเดียวกัน; cacheผิด hash/duplicate keysถูก reject; fitใช้ TRAINเท่านั้น |
| D | development pilot | วัด runtime/memory/supportได้; เลือก protocol/budgetsจาก developmentและ freeze |
| E | RQ1 retrieval | ได้ recall–candidate budgetและmiss slicesตาม roles |
| F | RQ2 scorer/calibration | ได้ frozen scoresและdiagnosticsของ LR17/GB17/GB18บน cohortsเดียวกัน |
| G | RQ3–RQ4 policies/search | Chow/simple optimum/random/Sobol/GAครบ, หลาย seeds, actual traces |
| H | final batch evaluation | predictionsถูก freezeก่อน label evaluation; independent recomputationตรง |
| I | paper/thesis tables | ทุก claimมี scope/source; paired comparisons/sensitivityครบ; data/AI disclosureตรงข้อเท็จจริง |

Testsที่ต้องมีเพราะจับความเสี่ยงจริง: คู่ `(A,B)`/`(C,B)` ข้าม role, positiveที่ย้าย NO_MATCH→REVIEWไม่เพิ่ม automatic recall, blocking missesไม่หายจากตัวส่วน, Chow ties/extreme costs, P2 optimumตรง brute force, expanded gateปิดได้ที่ s=0/1, modelไม่เปลี่ยนเมื่อสลับ test labels, preprocessไม่ fit test, runสอง variantไม่ซ้ำคอลัมน์ และ chunk manifestไม่รับ stale/duplicate pairs

## ใช้ code เดิมส่วนใด

| ส่วน | แนวทาง |
|---|---|
| Pair key/normalization/name similarity | reuse pure functionsที่ตรวจแล้ว; กำหนด semanticsและtestsก่อนเลือก canonicalตัวเดียว |
| V2 entity routing / artifacts | reuseแนวทางและvalidationของสองปลาย; ผล frozenเดิมเก็บประวัติ |
| Reviewer automatic metrics / Chow | reuseสูตรและboundary checks; เพิ่ม completecomponent countsและcost parametersที่งานใหม่ต้องใช้จริง |
| Classical scorers / calibration | ใช้ sklearnที่ติดตั้ง; ฝึกภายใต้ splitใหม่ |
| Legacy cache/production probabilities | ใช้ตรวจประวัติ/เทียบ lineage; ไม่ใช้เป็น scorerของ unseen-entity experimentใหม่ |
| R6, image, CRM, 10-gene policy | เก็บเป็นงานเสริมจนbaselineหลักครบและมีคำถามเฉพาะที่ต้องใช้ |

ยังไม่เริ่มรันโมเดลใหม่ในขั้น audit นี้ งานแรกของการเขียนใหม่คือ A–C เพื่อให้การรันครั้งถัดไปวัดสิ่งที่ตั้งใจจริง ไม่ใช่เพิ่ม experiment labelsบนตัวแบ่งชุดและตัวประเมินเดิม
