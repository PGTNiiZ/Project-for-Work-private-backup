# บันทึก worker: representation/retrieval

- สร้าง `rep.py` และ `test_rep.py` ภายในโฟลเดอร์นี้เท่านั้น ไม่อ่าน profile จริง/labels ไม่รัน scientific experiment และไม่ commit
- อ่าน protocol และ generic domain constants จาก source; ใช้ generic domains 14 รายการตาม historical implementation
- ใช้ `research_v2_runs/.venv/bin/python` ทดสอบ synthetic เท่านั้น
- เก็บหลักฐาน RED/GREEN แยกไฟล์ `red_*.log` / `green_*.log`; normalization → B0 → lexical → semantic → retrieval แต่ละชุดมี failure จาก API ที่ยังไม่มี ก่อนเพิ่ม implementation
- ผลตรวจสุดท้าย: `python -m pytest .../test_rep.py -q -W error` ผ่าน 12 tests (รวม parameterization) ไม่มี warning ดู `verification.log`

## API ที่ lead ต้องทราบ

- import `rep` ผ่าน sys.path ของโฟลเดอร์นี้
- dataframe ต้องเป็น RangeIndex เริ่ม 0 โดย reset index หลังเลือก training rows; module ไม่ reorder dataframe และไม่อ่าน `entity`
- `fit_tfidf(train_df)` คืน dict ห้ากลุ่ม; `lexical_features` คืน `(X, names, groups)` รวม 35 columns
- `semantic_features` คืน X หก columns: fullname cosine/both_present/one_missing แล้ว bio ในลำดับเดียวกัน
- `fit_retriever(train_df)` คืน vectorizer แยกสำหรับ argument `sparse_vectors` ของ `retrieval` ไม่รับ dict ห้ากลุ่มแทน
- ใช้ `profiletext(df)` ได้เพื่อสร้าง serialization เดียวกันให้ dense encoder: `[username] ... [fullname] ... [bio] ... [location] ...`; ถ้าทั้งสี่ว่างคืน empty string
- retrieval คืน canonical int32 pairs เรียง score มากไปน้อยแล้ว canonical pair เมื่อคะแนนเท่ากัน ไม่ใช่ lexicographic ทั้งชุด (B0 เป็น lexicographic)
- hybrid_union แบบไม่มี budget แบ่ง floor(k/2) sparse + ceil(k/2) dense; odd k=1 จึงใช้ dense
- การตีความ ranking ที่ระบุใน docstring: union score = max(sparse cosine,dense cosine); RRF c=60 รวมสองอันดับต่อ directed query/platform แล้วใช้ maximum directed fused score ของ canonical pair ไม่เพิ่มคะแนนเพราะพบสองทิศทาง
- RRF ไม่มี budget คัด k หลัง fuse ต่อ query/platform แล้ว deduplicate; budget mode เริ่ม pool50 ต่อ retriever และเพิ่ม100/200/400/... จนมีพอ จึง rank/truncate ให้ exact count
- Empty TF-IDF training ที่ไม่มี eligible ngram ใช้ fixed zero-effect vocabulary ไม่ fit ข้อมูล inference และไม่เพิ่ม artificial training text
- float32 dot-product ของคู่ identical คนละข้อความอาจต่างระดับ rounding เล็กน้อย จึงเรียงตาม score จริง ไม่ปัดคะแนนเพื่อทำให้เสมอกัน

## สิ่งที่ตรวจแล้ว

NFKC/missing sentinels, exact/prefix/domain B0, cross-platform, deduplication, missing masks, zero embeddings, reversed/duplicate pair order, positional index rejection, train-only vocabulary, empty training, all four retrieval methods, score ranking เทียบ independent dense oracle, exact budget/error เมื่อเป็นไปไม่ได้, pool extension และ batch boundary ที่ 256, guard dataframe ที่ห้ามอ่าน entity

ไม่ได้ benchmark 7k profiles จริงเพื่อรักษาขอบเขต worker; implementation ทำ dot product batch256 ต่อ target platform ไม่สร้าง NxN matrix ทั้งชุด
