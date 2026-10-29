# แผนที่ฟีเจอร์ประวัติศาสตร์ — NEW POST-HOC / DEVELOPMENT-ONLY / EXPLORATORY

## ข้อสรุปและสถานะ

- ยืนยันนิยาม **23 text + 14 image statistics + 4 image context** จาก MAIN commit `1e0a2dbba4d30e7b291dda3cc02d6c11fdd3909b` และเทียบ implementation ปัจจุบัน ไม่ใช่การเปิดหรือ retune ผลเดิม
- **historical41 = BLOCKED สำหรับข้อมูลจริงในขอบเขตนี้**: development parquet ไม่มี `profile_row_id`, `profile_id`, `user_folder`, `pictureURL`; ไม่สามารถรับรอง image/caption linkage ได้ด้วย normalized username/platform เพียงอย่างเดียว ห้ามใช้ศูนย์แทน “เชื่อมโยงไม่ได้” และเรียกว่า historical41
- **historical23 exact = ยังไม่พร้อม**: historical `bio_mentions` ไม่อยู่ใน schema 7 normalized attrs และตัวพิมพ์ใหญ่ของ bio สูญหายแล้วหาก bio ถูก lower-case; คอลัมน์ links ต้องยืนยันว่าเทียบเท่า historical `bio_urls` ไม่ใช่ URL คนละแหล่ง โปรแกรมจึงบังคับ `bio_mentions` ให้ caller ระบุเอง ไม่อนุมานจาก bio โดยเงียบ
- legacy encoder คือ **`sentence-transformers/all-mpnet-base-v2` ไม่ใช่ MiniLM** (`train_base.py:45`; historical base:45) การใช้ frozen development MiniLM จาก lead ทำได้ในสูตร dot-product เดิม แต่ต้องเรียก adapted historical-text23 ไม่ใช่ exact historical reproduction; ไม่รัน inference ใหม่
- โค้ดใหม่เป็น pure transformation ไม่มี file/network/model/cache access ไม่มี label/score/decision/split input การ fit TF-IDF รับเฉพาะ training-development frame ที่ caller ส่งให้ ส่วนการรับรอง split อยู่ที่ caller ไม่สามารถพิสูจน์จาก feature-only frame ได้
- ไม่เปิด raw profiles, CSV, parquet, ภาพ, metadata/cache หรือ original final artifacts ใด ๆ; ทดสอบเฉพาะ SYNTHETIC

## แหล่งอ้างอิงที่ตรวจ

ชื่อย่อ `BASE` = `MAIN@1e0a2db:train_data/stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py`
ชื่อย่อ `MM` = `MAIN@1e0a2db:train_data/stage7_13_multimodal_suite/run_multimodal_suite.py`

สำเนาที่อ่านได้:
- `research_v2_review_workspace/research_v2/review/_work/agentA/source/main/train_data/stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py.txt`
- `research_v2_review_workspace/research_v2/review/_work/agentA/source/main/train_data/stage7_13_multimodal_suite/run_multimodal_suite.py.txt`
- git show source-only จาก audit clone `research_v2_review_workspace/research_v2/review/_work/repos/main`; clone HEAD ตรง pin ด้านบน
- BACKUP HEAD = `903246c87eba069d4c07106695cbae072dbbb343`; `git ls-tree` สอง historical Python path นี้ไม่พบ จึงไม่แต่งนิยามจาก backup
- current `src/identity_resolution/stages/train_base.py:308–396` สืบทอด BASE; current `src/identity_resolution/stages/train_multimodal.py:64–308` สืบทอด MM
- `src/identity_resolution/stages/features.py` เป็นอีก feature pipeline อย่าเหมารวมกับ 23/41; `imaging/pair_features.py` มี bit-Hamming pHash และ CLIP/face logic ของอีก branch ไม่ใช่สูตร hex-character MM
- review document `research_v2_review_workspace/research_v2/review/THESIS_EVIDENCE_RECONCILIATION.md` TC-07 ชี้ thesis PDF100/พิมพ์85 §5.3 และ PDF93/พิมพ์78 เรื่อง image/caption availability; แถว N-78 / N-96 Text/Attribute-feature_count ชี้ PDF78/พิมพ์63 และ PDF96/พิมพ์81 = 23 ฟีเจอร์ รายงานนี้ใช้ review document เท่านั้น ไม่อ่าน original result JSON ที่ review อ้างถึง และไม่ยกระดับตัวเลขเหล่านั้นเป็นผลตรวจใหม่

## การเตรียมข้อความตาม BASE:66–161

`userName/fullName/bio/location` ใช้ strip + lower; `platform` ใน text path ไม่ถูก canonicalize เพิ่ม URL: parse serialized list, strip+lower+rstrip('/'); domain คำนวณจาก URLs ด้วย urlparse และ `.replace('www.','')` **ไม่ใช้ input domain โดยตรง**; mentions มาจาก `bio_mentions` แยก pipe/whitespace แล้ว lstrip('@'); hashtags จาก `#(\w+)` ใน lower bio

style_caps ใช้ **bio ก่อน lower**; avg_word_len นับทุก token ของ whitespace split รวม punctuation; punct = จำนวนอักขระที่ไม่ใช่ alnum และไม่ใช่ whitespace หารความยาว normalized bio

## 23 text features เรียงตาม BASE:359–381

Jaro = RapidFuzz `JaroWinkler.normalized_similarity`; token-sort = `fuzz.token_sort_ratio/100`; Jaccard ชุดว่างสองฝั่ง = 0

| # | ชื่อจริง | นิยาม | BASE line |
|---|---|---|---|
|1|username_jaro|Jaro username A/B แม้ค่าว่าง|359|
|2|username_lev|1−Levenshtein distance / max(lenA,lenB,1)|360|
|3|username_token_sort|token-sort username|361|
|4|fullname_jaro|Jaro fullname A/B|362|
|5|fullname_lev|normalized distance เช่น username|363|
|6|fullname_token_sort|token-sort fullname|364|
|7|bio_tfidf_cosine|dot ของ L2 TF-IDF bio unigram+bigram, max_features4000,min_df1|365;305–308|
|8|bio_sbert_cosine|dot frozen normalized MPNet bio embedding A/B|366;309–321|
|9|domain_jaccard|Jaccard URL-derived domains|367|
|10|url_jaccard|Jaccard normalized URLs|368|
|11|domain_count_a|min(count distinct domains A,10)/10|369|
|12|domain_count_b|เหมือน A สำหรับ B|370|
|13|location_jaro|Jaro เฉพาะ location ทั้งสองไม่ว่าง มิฉะนั้น0|371|
|14|location_token_sort|token-sort เฉพาะ location ทั้งสองไม่ว่าง มิฉะนั้น0|372|
|15|mention_jaccard|Jaccard ของ historical bio_mentions|373|
|16|hashtag_jaccard|Jaccard hashtags|374|
|17|hashtag_count_a|min(count distinct hashtags A,10)/10|375|
|18|hashtag_count_b|เหมือน A สำหรับ B|376|
|19|style_caps_diff|abs(raw bio uppercase ratio A−B)|377|
|20|style_avgword_diff|abs(mean word length A−B)|378|
|21|style_biolen_ratio|min bio lengths/max; ทั้งสองว่าง=1,ว่างข้างเดียว=0|379|
|22|style_punct_diff|abs(punctuation ratio A−B)|380|
|23|platform_pair_code|sorted googleplus+instagram=0,googleplus+twitter=1,instagram+twitter=2;อื่น=-1|381;48–52|

**ความต่างที่ตั้งใจสำหรับ leakage safety**: original `make_profile_bundle(profiles)` fit TF-IDF บน eligible profiles ที่ส่งให้ ก่อน transform ทุก split (`BASE:305–308,522`); adapter ใหม่ fit เฉพาะ `train_dev_df` ดังนั้นเป็น audited formulas ภายใต้ development-safe refit ไม่ใช่ bit-exact original pipeline output

## 14 image-statistics features เรียงตาม MM:256–282

กำหนด L=has_local_image, M=has_image_metadata จากแหล่งที่พิสูจน์ linkage ได้แล้ว; ถ้าต้องใช้สองภาพแต่มีไม่ครบจะเป็น0 ตาม source ไม่ใช่เพราะ unresolved mapping

|#|ชื่อจริง|นิยาม|
|---|---|---|
|1|image_any_local|L_A OR L_B|
|2|image_both_local|L_A AND L_B|
|3|image_one_local_only|any AND NOT both|
|4|image_phash_sim|ถ้า both: 1−จำนวน hex-character ที่ต่างกันจาก zip(hashA,hashB)/max(len(hashA),1); hashว่าง=0|
|5|image_dhash_sim|สูตร hex-character เดียวกันสำหรับ dhash|
|6|image_brightness_diff|ถ้า both: abs(brightness A−B)|
|7|image_contrast_diff|ถ้า both: abs(contrast A−B)|
|8|image_entropy_diff|ถ้า both: abs(entropy A−B)|
|9|image_rgb_l1|ถ้า both: (abs(RA−RB)+abs(GA−GB)+abs(BA−BB))/3|
|10|image_filesize_ratio|ถ้า both: min(sizeKB A,B)/max(sizeKB A,B,1e−6)|
|11|image_face_count_diff|ถ้า M ทั้งสอง: abs(num_faces A−B)|
|12|image_face_area_diff|ถ้า M ทั้งสอง: abs(face_area_ratio A−B)|
|13|image_blur_diff|ถ้า M ทั้งสอง: abs(blur_score A−B)|
|14|image_metadata_any|M_A OR M_B|

**ไม่ใช่** 14 scalar image descriptors ต่อ profile และไม่ใช่ bit-Hamming ของ pHash: มี availability flags, numeric differences และ metadata รวมอยู่ด้วย

### Legacy per-profile descriptors และแหล่งกำเนิด

MM:68–99 เปิด PIL RGB/L:
- width,height,aspect_ratio=width/max(height,1),file_size_kb=actual file bytes/1024
- brightness=mean(PIL L)/255; contrast=std(PIL L)/255
- avg_r/g/b=mean(PIL RGB float32/255)
- entropy ใช้ `np.histogram(gray,bins=256,range=(0,255),density=True)` ตัด bins ที่0 แล้ว `−sum(hist*log2(hist))` รักษารายละเอียด density/range เดิม ไม่เปลี่ยนเป็น entropy สูตรอื่น
- local_phash=`str(imagehash.phash(rgb))`; local_dhash=`str(imagehash.dhash(rgb))`
- has_local_image=1 หลัง descriptor computation สำเร็จ
- width,height,aspect_ratio ถูกสร้างแต่ไม่ได้เข้า 14 pair features; face_confidence/status_done ถูกโหลดแต่ไม่ได้เข้า 18 pair features
- `blur_score,num_faces,face_area_ratio,caption_en,status` เป็นข้อมูลนำเข้า `image_features_complete.csv` (MM:141–158) MM ไม่คำนวณ detector/caption ใหม่ตรงนี้; current `imaging/features.py` มี OpenCV Laplacian blur และ face/CLIP machinery แต่ยืนยัน model version/weights ของ metadata ที่เคยใช้จาก code อย่างเดียวไม่ได้ (**UNKNOWN**)

## 4 image-context features เรียงตาม MM:284–304

|#|ชื่อจริง|นิยาม|
|---|---|---|
|1|image_caption_any|caption_emb_idx A≥0 OR B≥0 (ไม่ใช่ has_local_image)|
|2|image_caption_bio_sbert_cross|max(dot(captionA,bioB) ถ้ามี captionA มิฉะนั้น0, dot(captionB,bioA) ถ้ามี captionB มิฉะนั้น0)|
|3|image_caption_fullname_token_cross|max(token-sort captionA/fullnameB, captionB/fullnameA); captionว่างทางนั้น=0|
|4|image_caption_username_token_cross|max(token-sort captionA/usernameB, captionB/usernameA); captionว่างทางนั้น=0|

caption_en ถูก lower ใน MM:155 และ encode ด้วย **encoder เดียวกับ bio** + normalize_embeddings=True (MM:193–206); captions ไม่ใช่ image embedding, CLIP cosine หรือ face embedding และไม่มี caption-caption cosine ในชุดนี้ ตัว max ไม่ควร clamp เป็น0 เสมอ: ถ้ามี captionทั้งสองและ dotติดลบทั้งสอง ผล max ยังติดลบตาม source

ความพร้อมจริงของ dev-only captions/metadata/frozen caption embeddings = **UNKNOWN/BLOCKED** ไม่ได้เปิดไฟล์เพื่อคาดเดา

## Image path lookup: ช่องว่างที่ทำให้ historical41 BLOCKED

1. MM:102–114 / current `train_multimodal.py:98–110` scan downloaded_images, เอาส่วนก่อน `_` เป็น int `profile_row_id`; ถ้าชน rowid จะ overwrite โดย traversal order ไม่มี username/platform guard
2. source `MAIN@1e0a2db:image_process/recover_profile_images.py:get_filename` และ current `src/identity_resolution/imaging/recover.py:94–101`: filename = `{idx:05d}_{safe_name}_{md5(original_url)[:8]}{ext}` โดย safe_name เก็บ alnum/`-_` และแทนอักขระอื่นด้วย `_`; idx มาจาก enumerate แถว CSV; **filename ไม่มี platform** และ sanitized username ไม่ reversible; URL ที่กู้สำเร็จอาจต่างจาก URL ที่ใช้ hash ชื่อไฟล์
3. normalized username อาจสูญเสียตัวพิมพ์ใหญ่/@/punctuation, หลาย platform อาจใช้ชื่อเดียวกัน, หลาย raw names อาจ sanitize เหมือนกัน จึงไม่สามารถพิสูจน์ว่าภาพที่ดูเหมือนชื่อ dev ไม่ใช่ test profile ได้จาก dev whitelist อย่างเดียว การ unique ภายใน dev ไม่พิสูจน์ global uniqueness หรือ absence จาก test
4. ไม่มี original rowid ใน dev frame: ห้ามใช้ local RangeIndex แทน legacy idx โดยตรง และห้ามอ่าน full CSV เพื่อ restore แถว
5. metadata join MM:151–164 ใช้ `(metadata.profile_id renamed user_folder,platform)` แล้ว local join ใช้ `profile_row_id`; dev entity/component ไม่ได้มีหลักฐานว่าแทน raw user_folder ได้ จึงห้ามเดา
6. อีก convention `imaging/embeddings.py:62–65` = `{profile_id}_{platform}_{url_hash}.jpg` ใน data/images ไม่ใช่ downloaded_images convention; `imaging/pair_features.py:124–144` lookup MD5(pictureURL)[:8] ใช้ได้ก็ต่อเมื่อมี dev-only original pictureURL+approved index ซึ่งไม่มีใน schema ที่แจ้ง
7. ทางปลดบล็อกที่ยอมรับได้: ผู้มีสิทธิ์จัดทำ **dev-only linkage/descriptor/caption manifest** ที่ provenance ตรง raw rowid หรือ original URL/profile keys, รับรองไม่มี test profiles, ตัด ambiguous keys และไม่เปิด whole mixed cache; task นี้ไม่ได้สร้างหรืออ่าน manifest ดังกล่าว

ผล: **ไม่เขียน image loader, ไม่ scan filenames ของภาพจริง, ไม่เปิดภาพใด, ไม่เติม absent ทั้งชุด, ไม่อ้างว่า historical41 runnable**

## แยก R-series name_sim gate ออกจาก 41-feature suite

`experiments/code/exp_lib.py:48–64` name_sim=max Jaro-Winkler ของ username/fullname ไขว้4คู่ (Jellyfish); `:93–101` สร้าง cache ตั้ง name_sim=0 ก่อน และคำนวณเฉพาะ `(decision_source != AUTO_EXACT) & (score >= 0.5)` นี่เป็น **post-score enrichment gate** ของ harness ไม่ใช่คุณสมบัติที่แท้จริงว่า low-score profiles ไม่มีชื่อคล้ายกัน

BASE:359–381 และ MM:256–304 **ไม่มี name_sim คอลัมน์รวมและไม่มี score gate** ห้ามใส่ gate เข้า historical23/41 หรือเหมาว่าทุก R-family มี gate เหมือนกัน Adapter นี้คำนวณ name similarities ของทุกคู่ที่รับมาโดยไม่เห็น scores/decisions

## API ใหม่และข้อกำหนด

ไฟล์ `research_v2_runs/posthoc_blocking_features/work/history/hist_features.py`

```python
bundle = fit_text(train_dev_df)
X23, names23 = text_features(dev_df, pairs, bundle, embeddings=frozen_dev_bio_embeddings)
X18, names18 = image_features(dev_df, pairs, dev_descriptors,
    bio_embeddings=frozen_dev_bio_embeddings,
    caption_embeddings=frozen_dev_caption_embeddings)
```

- df: zero-based contiguous RangeIndex; columns `username,fullname,bio,location,links,platform,bio_mentions`, optional `domain` (ignored). Project away `entity/component/fold` ก่อนเรียก; unexpected columns ถูกปฏิเสธ ห้ามใช้ entity identifiers เป็น features
- pairs: integer ndarray shape(n,2) หรือ DataFrame **สองคอลัมน์เท่านั้น** `profile_row_id_a,profile_row_id_b` ซึ่งชื่อ API นี้หมายถึง local RangeIndex endpoints ไม่ใช่ historical raw row IDs; ไม่มี labels/scores/splits/decisions
- embeddings: caller-supplied, 2D finite, row-aligned; rows norm1 หรือ0; text API signature optional แต่ถ้าไม่ส่งจะ raise ไม่แทน zero semantic feature เพื่อหลอกว่า exact
- dev_descriptors: zero-based RangeIndex เท่า df, exact feature-only columns ตาม `DESCRIPTOR_COLS`; explicit has_local_image/has_image_metadata binary, caption_emb_idx integer≥−1; None/misaligned/missing schema ถูกปฏิเสธ
- output float64 พร้อม ordered feature names ไม่คืน labels หรือ keys
- adaptation ที่เปิดเผย: `ast.literal_eval` แทน restricted eval; รับ Python list links ได้; empty-vocabulary training ให้ TF-IDF0 แทน source ที่จะ raise; all-absent images ต้องเป็น **explicit audited absence** จาก caller ไม่ใช่ unresolved linkage

## การทดสอบ

`test_hist_features_synthetic.py`: watched RED ก่อนสร้าง text module และ watched RED ก่อนเพิ่ม image API แล้ว GREEN

`test_source_parity_synthetic.py`: differential audit หลัง implementation เทียบ 23/18 formulas กับ allowlisted AST function bodies ของ reviewed source; ไม่ execute top-level imports/loaders/model/data logic ทดสอบ synthetic labels เฉพาะ legacy reference ซึ่งบังคับ label schema; adapter ไม่รับ labels

ขอบเขต: การทดสอบสังเคราะห์ยืนยันสูตรและ shape/order/input rejection ไม่ใช่ model performance, coverage หรือ scientific result และไม่ยืนยัน mapping ไปข้อมูลจริง

รันจาก root:

```sh
PYTHONDONTWRITEBYTECODE=1 research_v2_runs/.venv/bin/python -m unittest discover \
  -s research_v2_runs/posthoc_blocking_features/work/history \
  -p 'test_*synthetic.py' -v
```
