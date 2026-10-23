"""Render the dataset-only report from audited aggregates; no upstream writes."""
from pathlib import Path
import csv,json,hashlib,collections
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
inv=json.loads((OUT/'dataset_inventory.json').read_text());ca=json.loads((OUT/'dataset_candidate_accounting.json').read_text());v2=json.loads((OUT/'dataset_v2_feature_verification.json').read_text());wb=json.loads((OUT/'dataset_workbook07_evidence.json').read_text());nb=json.loads((OUT/'dataset_notebook_evidence.json').read_text())
# Expand the inventory only with concrete additional inspected artifacts.
for row in ca['candidate_artifacts']+ca['feature18_replay']+[{'path':v2['artifact_path'],'sha256':v2['sha256'],'rows':v2['rows'],'columns':v2['columns']}]:
 if not any(x['path']==row['path'] for x in inv):inv.append({'exists':True,**row})
for n in ['experiments/profile_embeddings_minilm.npy','experiments/profile_embeddings_minilm_ids.npy','train_data/ground_truth_matrix.npz','thesis_rebuild/07_dataset_raw_to_features.xlsx']:
 if not any(x['path']==n for x in inv):
  p=ROOT/n;inv.append({'path':n,'exists':p.exists(),**({'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} if p.exists() else {})})
(OUT/'dataset_inventory.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n')
with (OUT/'dataset_inventory.csv').open('w',newline='') as f:
 fields=sorted(set().union(*(x.keys() for x in inv)));w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in x.items()} for x in inv)
with (OUT/'transformation_verification.csv').open(newline='') as f:trans=list(csv.DictReader(f))
stats=collections.Counter(x['status'] for x in trans)
s=[]
def add(t):s.append(t)
add('''# 01 — สร้างสายสืบย้อนข้อมูลและฟีเจอร์จากหลักฐานจริง

## 1. คำตัดสินและขอบเขต

**สถานะ: audit แบบอ่านอย่างเดียว ไม่ใช่การทดลองหรือ raw-to-result reproduction ใหม่** อ่านข้อกำหนดจาก `docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:100-105` และ `docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:18-29` ก่อนตรวจ ไม่รัน notebook, ไม่ฝึกโมเดล, ไม่ปรับ policy, ไม่ encode/download, ไม่แก้ข้อมูล/ผลประวัติ และไม่ทำ git operation การ replay TF-IDF เป็นการตรวจ transformation เดิมเท่านั้น มิใช่ training scorer หรือหลักฐานประเมิน unseen data (`dataset_readonly_audit.py:1-14,132-133`; ทุก path ของไฟล์ audit ในรายงานนี้อยู่ใต้ `docs/research_rebuild/phase_01/`)

ข้อสรุปหลัก:

1. **24,729 cleaned profiles กับ 36,807 normalized profiles เป็นคนละ snapshot; chain ระหว่างสองชุดยัง UNPROVEN** จำนวนแถวเท่ากันหรือคอลัมน์บางส่วนตรงกันไม่พิสูจน์ผู้สร้าง/เวลา/การ exclude (`transformation_verification.csv:7`; `dataset_inventory.csv`; `src/identity_resolution/stages/prepare.py:119-155`)
2. `07_dataset_raw_to_features.xlsx` เป็น workbook สำหรับ **แสดง snapshot และ join** ไม่ใช่โปรแกรมที่ผลิต raw→clean→features: builder อ่าน CSV ที่มีอยู่ทั้งหมดและเขียน Excel; ไม่คำนวณ 17 features ใหม่ (`thesis_rebuild/build_dataset_excel.py:12-39,121-131`)
3. `feature_matrix.csv` 21 columns/204,701 rows มี **4 metadata/label + 17 features แบบ Stage9** ไม่ใช่ GB-17 ของ R-series/V2 และไม่ใช่ 41-feature multimodal (`data/processed/feature_matrix.csv:1`; `thesis_rebuild/build_dataset_excel.py:38-39,109`)
4. คู่ Stage9 join ชุด 24,729 ปัจจุบันไม่ได้ทั้งสองปลายทุกแถว แต่ 36,807 blocking snapshot ตรวจ label ได้ในส่วนที่ endpoint ไม่กำกวม; **ห้ามถือ unresolved เป็น negative** (`dataset_audit_outputs.json`, `dataset_readonly_audit.py:143-148`)
5. Corrected V2 GB-17 ปัจจุบัน replay ฟีเจอร์ครบทุกแถวได้ตรงที่ float32 precision; canonical candidates ปัจจุบันตรง persisted pair keys ทั้ง exact/scored/workflow; การผ่านนี้ **ไม่ซ่อม raw provenance หรือทำให้ corpus เป็น external test** (`dataset_v2_feature_verification.json`; `dataset_candidate_accounting.json`; `docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:24-29,48`)

รายงานเผยแพร่เพียง schema/hash/สถิติสรุป ไม่มี username/bio/URL/แถวโปรไฟล์/ID คู่จริง ตาราง evidence notebook เก็บเฉพาะ source code และ hash ไม่เก็บ saved outputs ซึ่งอาจมีข้อมูลบุคคล (`dataset_readonly_audit.py:51-56`; `dataset_candidate_audit.py:1-4`)

### วิธีอ้าง evidence

- `N9-original`, `N9-v2`, `N8-v2`, `N7-v2`, `N7-original`, `N6-v2`, `NC-first`, `NC-later`, `NGT` เป็น alias ของ notebook ในภาคผนวก A; cell ใช้ **1-based ตำแหน่งใน cells array รวม markdown** และมี SHA-256 ทั้งไฟล์ ค่าที่กล่าวถึงในสูตรมาจาก source cell ไม่ใช่คำบรรยาย workbook
- ตัวเลขจาก CSV/inventory อ้าง `dataset_inventory.csv:เลขบรรทัด`; ผล replay ราย transformation อ้าง `transformation_verification.csv:เลขบรรทัด` พร้อมแหล่งกฎเดิม
- คำว่า PASS คือ equality ภายใต้นิยาม/ประชากร/tolerance ที่ระบุเท่านั้น; FAIL ของ replay ข้าม snapshot หมายถึงเข้ากันไม่ได้ **ไม่ใช่ยืนยันว่าผู้สร้างประวัติคำนวณผิด**; UNPROVEN/NOT_EXECUTED ไม่ถูกยกระดับเป็น PASS

## 2. Inventory: แถวหนึ่งแทนอะไรและไม่ควรรวมจำนวนแถว

ตารางด้านล่างเป็นผลอ่านไฟล์จริง ไม่ยึด CLAUDE.md/README เป็นแหล่งนับ แยกชื่อ `nomalized` (สะกดเดิม) กับ `normalized` อย่างเคร่งครัด:

| Artifact | แถว | คอลัมน์ | แถวซ้ำเต็มแถว | ID/entity สรุป | หลักฐาน |
|---|---:|---:|---:|---|---|''')
for i,r in enumerate(inv,2):
 if 'rows' not in r:continue
 info=[]
 for c in ['profile_row_id','profile_id','user_folder']:
  if c+'_unique' in r:info.append(c+' distinct='+str(r[c+'_unique'])+'; duplicate excess='+str(r[c+'_duplicate_excess']))
 add('| `'+r['path']+'` | '+str(r['rows'])+' | '+str(len(r.get('columns',[])))+' | '+str(r.get('duplicate_full_rows','ไม่ตรวจ'))+' | '+'; '.join(info)+' | `dataset_inventory.csv:'+str(i)+'`; source `'+r['path']+':1` |')
add('''
**การนับ entity:** inventory `*_unique` นับค่าที่อ่านด้วย `keep_default_na=False` รวม `''` เป็น distinct value ถ้ามี; positive combinatorics ตัด entity ว่างออก ห้ามเรียก distinct ทั้งหมดว่า known entities โดยไม่ลบ unknown (`dataset_readonly_audit.py:31-40`)

### Snapshots ที่สำคัญ

- **combined 36,807**: CSV ที่ใกล้ raw ที่สุดที่มีอยู่ ไม่ใช่ JSON ต้นทาง ประกอบด้วย 11 columns; distribution twitter 13,960 / googleplus 11,890 / instagram 10,957; มีข้อมูลก่อน normalization แต่ user-folder token ที่ดูเหมือน NA ทำให้ semantics ของ loader เปลี่ยน (`dataset_inventory.csv:2`; `NC-later cell13`; `thesis_rebuild/build_dataset_excel.py:108`)
- **all_profiles_cleaned 24,729**: 15 columns; twitter 8,535 / googleplus 8,302 / instagram 7,892; profile_id เป็น normalized outputProfileName ใน source prepare ไม่ใช่บัญชี row ID; fullName/profile_id/bio_clean สามารถ replay ด้วยกฎ prepare ได้ แต่ username มี 1 mismatch (`dataset_inventory.csv:7`; `src/identity_resolution/stages/prepare.py:149-155`; `dataset_reconciliation_outputs.json`)
- **merged 36,807**: 22 columns; blocking 36,807 เป็น 30 columns ที่ต่อจากเนื้อหา merged โดยทุก shared column ตรงตามลำดับแถว; equality นี้พิสูจน์ compatibility ปัจจุบัน ไม่ใช่ผู้สร้างประวัติ (`dataset_inventory.csv:5,8`; `transformation_verification.csv` แถว merged→blocking)
- **nomalized 36,807**: 21 columns มี user_folder ว่าง **14,251 แถว**; **normalized/merged** มี user_folder ว่าง **3 แถว**; nomalized→normalized user_folder ต่าง **14,348 แถว** แม้จำนวนแถวเท่ากัน จึงไม่ใช้แทนกันเพราะสะกดชื่อคล้ายกัน (`dataset_inventory.csv:3-5`; `dataset_candidate_accounting.json`; `transformation_verification.csv` แถว nomalized→normalized ordered user_folder)
- **profiles_with_images 24,729**: 39 columns และ image_features_complete 2,459×25 เป็นข้อมูลคนละระดับ; snapshot image feature ทั้งหมดเป็น twitter ไม่ใช่ pairwise features หรือ equal coverage ทุกแพลตฟอร์ม (`dataset_inventory.csv:15-16`; `thesis_rebuild/build_dataset_excel.py:103-104,155-158`)
- train_dataset 143,316 กับ test_dataset 30,558 ไม่ครอบคลุม feature_matrix 204,701; `val_dataset.csv` ไม่พบตาม path ที่ตรวจ จึงไม่สมมติแถวที่เหลือเป็น validation manifest ที่กู้ได้ (`dataset_inventory.csv:12-14`; `thesis_rebuild/07_ดูหน้าตา_dataset.md:25`)

## 3. แผนภาพ lineage ที่พิสูจน์ได้/ไม่ได้

```text
raw JSON ที่ NC-first/NC-later คาดหวัง
  └─ UNAVAILABLE ใน workspace → combined_profiles.csv (snapshot raw-like)
      ├─ NC-later pure cleaning rules → nomalized_profiles.csv
      │    └─ ส่วนมากของข้อความ/URL เข้ากันได้; entity mapping ไม่ครบ
      └─ normalized_profiles.csv → merged_profiles.csv
           ├─ shared fields mostly equal (username 1 mismatch normalized→merged)
           ├─ normalized_profiles_with_profile_id.csv
           │    └─ numeric entity ID + numeric profile_row_id → canonical/V2 retrieval
           └─ all_profiles_with_blocking_keys.csv (36,807)
                └─ 07 workbook raw/clean views + ambiguous-ID-safe pair enrichment

all_profiles_cleaned.csv (24,729) → profiles_with_images.csv (24,729)
  └─ อีก snapshot; ไม่มีหลักฐาน raw→36,807→24,729→36,807 เป็น chain เดียว

labeled_pairs.csv → feature_matrix.csv (keys/entity_a/label ordered equality PASS)
  └─ workbook 03_PAIRS (17 persisted Stage9 features ไม่ใช่ computed by workbook)
```

ลูกศรที่ข้อความระบุ equality ไม่ได้อ้างว่ามี production log/manifest ผู้สร้างที่ครบ (`transformation_verification.csv`; `dataset_candidate_audit.py:25-31`) Raw loader ใส่ source_folder/user_folder จาก directory และ platform จากชื่อ JSON แต่ raw directory ที่เอกสาร audit ตรวจว่าง ยังไม่กู้ JSON หรือสิทธิการใช้/แจกข้อมูลในงานนี้ (`NC-first cell6`; `docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:100-105,157-162`)

### Normalization: ไม่ใช่กฎเดียวทุก branch

| กฎ | ก computation ตาม source | ผลตรวจและข้อจำกัด |
|---|---|---|
| NC-first normalize_text | remove_emojis→lower→ลบ @ ตัวแรก→เก็บ `\\w/space`→ยุบ whitespace→trim | ใช้กับ userName/fullName; ไม่ใช่ ASCII-only และไม่ใช่ NFKC; `NC-first cell15` |
| NC-first clean_bio | ลบ emoji และ http/www URL→ยุบช่องว่าง→trim; ไม่ lower | ไม่เท่ากับ advanced bio; `NC-first cell15`; replay blocking bio ต่าง 29,950 แถว |
| NC-first location/URL | location lower+เก็บ comma; URL lower+strip protocol/www/trailing slash | replay blocking location/URL ต่าง 9,829/9,836; คนละ rule generation; `NC-first cell15`; transformation CSV |
| NC-later clean_username | trim/lower→ลบ @ หลายตัว→remove_emojis→เก็บ `[a-z0-9._-]`→ยุบ punctuation ซ้ำ→strip `._-` | raw→nomalized 1 mismatch; `NC-later cell30` |
| NC-later clean_fullname | trim/lower→remove_emojis→ลบ mr/mrs/ms/dr/prof→เก็บ ASCII a-z0-9/space→ยุบช่องว่าง | raw→nomalized 2 mismatches; `NC-later cell35` |
| NC-later advanced bio | safe_str→ftfy→html.unescape→whitespace→lower→extract/remove URL/mention→hashtag เป็นคำ→emoji.demojize→ลบ noisy separators→min length 3 | **NOT_EXECUTED**: environment ไม่มี emoji; ไม่แทนด้วย no-op; bio_urls/bio_mentions ใช้ต้นฉบับและเก็บ ` | `; `NC-later cells39,41`; transformation CSV |
| NC-later location | normalize whitespace/ลบ iPhone prefix→decimal coordinates→DMS→IP rejected→text fallback; คืน clean/type/valid/latitude/longitude | location/type/valid มี 1 mismatch ต่อ field; None coordinates source ไม่ตรง persisted zero fill; `NC-later cell46`; transformation CSV |
| NC-later external URL | safe_str; parse list-string ด้วย literal_eval; lower+เติม scheme ชั่วคราว→urlparse→domain/path/query ไม่เก็บ fragment→strip www/trailing slash; 0/1/many squash | url_count/externalUrl_clean/external_domain replay ตรงทั้งหมด; list columns บางชื่อไม่อยู่ persisted snapshot จึงไม่ได้อ้างตรวจ column ที่ไม่มี; `NC-later cells51-52` |
| prepare.py | normalize_text ชุดเดิมสำหรับ username/fullname/outputProfileName; bio_clean แค่ remove_emojis | บน cleaned24729: fullname/profile_id/bio PASS; username 1 mismatch; `src/identity_resolution/stages/prepare.py:98-116,149-155` |
| N6-v2 profile repair | null `platform_nan`/`platform_` ใช้ folder fallback หรือ unknown_index; duplicate เพิ่ม folder/index suffix | เป็น source recipe ที่ overwrite cleaned ชื่อเดิมเมื่อรัน; snapshot 24,729 ปัจจุบันไม่ได้อยู่ใน contract string-ID ของ Stage9; ไม่ได้รัน N6; `N6-v2 cells6,8,10` |
| corrected V2 text | None/float NaN→empty; NFKC→casefold→strip→lstrip @→ยุบช่องว่าง | แตกต่างจาก ASCII-clean และ lower อย่างเดียว; ตรวจผ่านฟีเจอร์ทั้งหมด; `experiments/icsec_final/authoritative_run_v2/features.py:22-27` |

**Coordinates ไม่ใช่ availability mask:** persisted nomalized มี latitude/longitude = 0 จำนวน 36,426 แถวต่อ field แต่ source location returns None เมื่อไม่มีพิกัด; replay เทียบ source None กับ snapshot zero พบ 36,421 mismatches ต่อ field นี่คือกฎ fill ที่ยังไม่พิสูจน์ผู้สร้างครบ ไม่ควรเอา (0,0) เป็นตำแหน่งคนจริง (`dataset_reconciliation_outputs.json`; `transformation_verification.csv:18-19`; `NC-later cell46`)

**Default NA vs literal token:** builder ใช้ pd.read_csv default NA และ fillna ก่อน assert ทำให้ raw→blocked identity fields ผ่าน; reader ของ audit ที่สงวน literal values พบ user_folder 3/outputProfileName 2 mismatches คำว่า row-aligned ใน workbook จึงเป็น alignment ภายใต้ parser ของ builder ไม่ใช่ byte/literal equality ทุก field (`thesis_rebuild/build_dataset_excel.py:18-29`; `transformation_verification.csv:2-6`; แถว builder default-NA ใน transformation CSV)

## 4. Workbook 07: ตรวจ ZIP/XML streaming และรู้ว่าชีตไหนทำอะไร

ตรวจ workbook โดย stdlib zipfile+ElementTree.iterparse (ไม่โหลด worksheet tree หรือ openpyxl) แล้วตรวจ count/schema/ค่าที่คัดจาก source CSV สายเดิม เก็บเพียง aggregate (`dataset_readonly_audit.py:149-195`; `dataset_reconciliation_audit.py:29-57`)

| Sheet | จำนวนแถวข้อมูล | คอลัมน์ | หน้าที่/หลักฐาน |
|---|---:|---:|---|''')
for r in wb['sheets']:
 meaning={'00_READ_ME':'metadata guide: ไม่ใช่ตาราง dataset; report columns=1 คือ first-row title ไม่ใช่ความกว้างสูงสุดของ guide','01_RAW_PROFILES':'source_row + 11 raw-like CSV fields','02_CLEAN_PROFILES':'source_row + 30 blocking-profile fields','03_PAIRS':'feature_row + keys/label + match_status/raw/clean A/B + 17 features','04_FEATURE_GUIDE':'คำอธิบาย 17 features ไม่ใช่สูตร executable','05_IMAGE_PROFILES':'39-column image profile snapshot','06_IMAGE_FEATURES':'25-column per-image snapshot'}[r['name']]
 add(f"| {r['name']} | {r['data_rows']:,} | {r['columns']} | {meaning}; `dataset_workbook07_evidence.json`; `thesis_rebuild/build_dataset_excel.py:93-158` |")
add('''
- Raw/clean/photo-feature source cell equality และ pair keys/label/features ของ 03_PAIRS ตรง source CSV ทั้งหมดที่ตรวจ; image-profile comparison เบื้องต้นต่าง 406 cells (bio 202/bio_clean 202/location 2) แต่เมื่อ decode OpenXML `_xHHHH_` control-character escapes แล้ว **เหลือ 0** ไม่ใช่ข้อมูลที่ถูกเปลี่ยน (`dataset_workbook07_evidence.json`; `dataset_reconciliation_outputs.json`; `dataset_reconciliation_audit.py:44-55`)
- Workbook ไม่มีการ execute สูตร similarity; builder เขียน string โดยปิด strings_to_formulas/strings_to_urls และใช้ constant_memory; source_row เป็น index+2 (`thesis_rebuild/build_dataset_excel.py:35,54-58,63-75`)
- ฝั่ง A: OK **203,401**, DUPLICATE_ID **251**, NO_PROFILE **1,049**; ฝั่ง B: **204,688/6/7** ตามลำดับ; builder เว้นข้อมูลโปรไฟล์ให้ blank เมื่อต่อไม่ได้หรือกำกวม แต่ยังคง feature/label เดิม (`dataset_audit_outputs.json`; `thesis_rebuild/build_dataset_excel.py:33-51,126-129`)
- **อย่ารัน workbook builder เพื่อแก้ lineage**: builder เป็น exporter ซึ่งอาจยืนยันแถวตรงกันภายใต้ NA parser แต่ไม่ได้ย้อนฝึก/คำนวณ feature (`thesis_rebuild/build_dataset_excel.py:18-39,126-129`)

## 5. พจนานุกรม 21 columns ของ feature_matrix.csv

นิยาม `S_m(a,b)` ตาม **N9-v2 cell4**: แปลงเป็น str→strip; ถ้าฝั่งใดว่างคืน 0; rapidfuzz branch `'jaro'` = `fuzz.WRatio/100` (**ไม่ใช่ Jaro/Jaro-Winkler**), `'token_sort'` = token_sort_ratio/100, method อื่นรวม `'levenshtein'` = fuzz.ratio/100 (**ไม่ใช่สูตร 1−edit_distance/max_length**); ถ้าไม่มี rapidfuzz ทุก method ใช้ SequenceMatcher.ratio ไม่เหมือน branch หลัก (`N9-original cell4`; `N9-v2 cell4`)

| ลำดับ | Column | จุดประสงค์และ computation จริง | ใช้เรียนรู้? | Source |
|---|---|---|---|---|''')
meanings={'profile_id_a':('ID บัญชีฝั่ง A สำหรับ lookup; ใน Stage9 เป็น string ไม่ใช่ numeric entity ID','ไม่'),'profile_id_b':('ID บัญชีฝั่ง B; ไม่รับประกัน unique ใน blocking snapshot','ไม่'),'entity_id_a':('folder/entity ฝั่ง A สำหรับ metadata และ split ประวัติ; ไม่ได้บันทึก entity_b','ไม่'),'label':('supervision 1 same-known-user_folder cross-platform / 0 คนละ folder ตาม Stage8; ไม่ใช่ input feature','ไม่'),'bio_tfidf_cosine':('cosine ของ bio_clean TF-IDF fit all bios: max_features=5000, stop_words=english,min_df=2; lookup duplicate key ใช้แถวสุดท้าย','ใช่'),'url_exact_match':('1 เมื่อ str(externalUrl_clean or empty) ทั้งสองมีค่าและเท่ากัน; miss lookup→0','ใช่'),'url_domain_match':('เหมือน exact แต่ใช้ url_domain; nan ที่ถูก str อาจกลายเป็น nonempty nan','ใช่'),'same_platform':('1 เมื่อ platform A=B สำหรับคู่ที่ lookup ได้ทั้งสอง; miss→0','ใช่'),'location_sim':('S_jaro(location_clean A,B) หรือ 0 เมื่อ missing; ชื่อ jaro ยังหมายถึง WRatio branch','ใช่')}
featcols=next(x['columns'] for x in inv if x['path']=='data/processed/feature_matrix.csv')
for i,c in enumerate(featcols,1):
 if c in meanings:meaning,learn=meanings[c]
 elif c.endswith('_both_empty'):meaning='1 เมื่อข้อความ '+c.split('_')[0]+' หลัง str(... or empty) และ strip ว่างทั้งสอง; หาก endpoint ใด lookup ไม่พบตั้ง 1 ให้ทั้งสาม fields';learn='ใช่'
 else:
  prefix,method=c.split('_',1);field={'username':'userName_clean','fullname':'fullName_clean','bio':'bio_clean'}[prefix];meaning='S_'+method+'('+field+' A,B); miss endpoint→0';learn='ใช่'
 cell='4' if i<=16 else '6' if c=='bio_tfidf_cosine' else '8' if c.startswith('url_') else '10'
 add(f'| {i} | `{c}` | {meaning} | {learn} | `N9-v2 cell{cell}`; `data/processed/feature_matrix.csv:1` |')
add('''
### Stage9 edge cases และผล replay

- Original ใช้ lookup `platform_userName_clean` ที่ประกอบเอง; v2 ใช้ column profile_id โดยตรง; ทั้งสอง `.loc` duplicate→`.iloc[0]` แต่ TF-IDF dict duplicate→**last index** จึงมี first/last inconsistency ภายใน recipe เดียว (`N9-original cells4,6`; `N9-v2 cells4,6`)
- pandas default NA เป็น float NaN ซึ่ง truthy; `str(value or '')` จึงกลายเป็น `'nan'` ไม่ใช่ empty อัตโนมัติ URL `'nan'=='nan'` อาจเป็น exact match และ both_empty flag ไม่แทน missingness อย่างปลอดภัย (`N9-v2 cells4,8,10`)
- Config N9-v2 ชี้ all_profiles_cleaned.csv ปัจจุบัน 24,729 และ schema ไม่ครบ location_clean/URL; ไม่สามารถประกาศว่าจะ regenerate artifact 204,701 ปัจจุบันจาก config นี้ครบโดยตรง (`N9-v2 cell2`; `dataset_inventory.csv:7,11`)
- Audit ทดลองกฎ N9-v2 กับ **blocking snapshot 36,807 ที่ workbook ใช้** ไม่ได้หลอกเปลี่ยน input แล้วเรียกว่า historical reproduction: username similarities ต่าง 922 ต่อ column; fullName 982; bio 1,009; both_empty ทั้งสามต่าง 1,055; URL exact/domain ต่าง 58/59; location 989; TF-IDF ต่าง 1; same_platform ตรง (ดูครบใน `transformation_verification.csv:24-40`) ข้อนี้บอก snapshot/recipe เข้ากันไม่ได้ครบ ไม่ควรอ้าง error rate ของโมเดล
- Keys/entity_a/label จาก labeled_pairs สู่ feature_matrix ตรงทุกแถวตามลำดับ; 204,701 rows ประกอบด้วย positives 29,243 / negatives 175,458 มี duplicate full rows 28 และ duplicate unordered pair excess 30; ไม่พบ conflicting labels ใน duplicate pair keys (`transformation_verification.csv:41-44`; `dataset_inventory.csv:10-11`)

## 6. GB-17 อีกชุดหนึ่ง: R2/legacy, corrected V2 และ production ต่างกัน

**จำนวน 17 เท่ากันไม่ได้แปลว่า feature set เดียวกัน** GB-17 ไม่มี Stage9 URL exact/domain และไม่ได้ใช้ Stage9 bio-TFIDF แต่มี name_sim/bio_jaccard/availability/length differences (`experiments/code/exp_r2_bert_feature.py:59-65,248-267`; `experiments/icsec_final/authoritative_run_v2/features.py:12-19`)

นิยาม V2: ใช้ข้อความ `_normalize` ข้างต้น; J=RapidFuzz **Jaro** (ไม่ใช่ WRatio และไม่ใช่ JaroWinkler); JW ใช้เฉพาะ cross-field name_sim; empty comparison ให้ 0 (`experiments/icsec_final/authoritative_run_v2/features.py:22-48,67-76`)

| Feature ตาม order ของ GB-17 | corrected V2 computation | ความต่าง legacy R2 | Source |
|---|---|---|---|''')
rows=[('username_jaro','J(username A,B)','jellyfish.jaro_winkler_similarity ไม่ใช่ Jaro'),('username_lev_sim','1−edit_distance/max(len A,len B); empty→0','สูตรเดียว แต่ cleaning lower/strip และ nan handling คนละชุด'),('username_token_sort','fuzz.token_sort_ratio/100; empty→0','ถ้าไม่ equal ใช้ JW บนการเรียง **ตัวอักษร** ไม่ใช่ sort tokens'),('fullname_jaro','J(fullname A,B)','JW'),('fullname_lev_sim','1−edit_distance/max fullname length; empty→0','สูตรเดียว/cleaning ต่าง'),('fullname_token_sort','fuzz.token_sort_ratio/100','JW ของ fullname ที่เรียง words'),('name_sim','max JW ของ username/fullname A × username/fullname B ทั้ง 4 available comparisons; no score/label input','ดึง scored.name_sim จาก cache ที่ gate ด้วย predecessor score'),('bio_jaccard','intersection/union ของ set whitespace tokens; both empty→0','สูตรเดียว/cleaning ต่าง'),('bio_len_ratio','min(character length)/max(character length); max=0→0','สูตรเดียว'),('both_have_bio','float(bool(bio A and bio B))','สูตรเดียว'),('location_jaro','J(location A,B); empty→0','JW'),('location_exact','float(nonempty A and A=B)','สูตรเดียว'),('both_have_location','float(bool(location A and B))','สูตรเดียว'),('same_platform','float(nonempty platform A and A=B)','สูตรเดียว; cross-platform candidates จึงคง 0'),('username_len_diff','abs(len A−len B)/max length; max=0→0','สูตรเดียว'),('fullname_wordcount_diff','abs(words A−words B)/max wordcount; max=0→0','สูตรเดียว'),('username_prefix3_match','1 เมื่อทั้งสอง len≥3 และ 3 chars แรกตรงกัน','สูตรเดียว; ต่างกับ blocking ASCII-stripped prefix3')]
for n,formula,diff in rows:add(f'| `{n}` | {formula} | {diff} | `features.py V2:67-108`; `exp_r2_bert_feature.py:175-267` |')
add('''
- **Legacy learned dependency:** exp_lib สร้าง name_sim เฉพาะ not AUTO_EXACT และ score≥NSIM_MIN_SCORE; ส่วนอื่นถูก 0 แล้ว R2 โหลดค่าคอลัมน์นั้น ไม่ได้ recompute similarity อิสระ feature primitive pure แต่ final feature ถูก gate ด้วย learned predecessor score จึงไม่ใช่ clean lexical ablation (`experiments/code/exp_lib.py:93-101`; `experiments/code/exp_r2_bert_feature.py:257`; `docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:136-141`)
- **corrected V2 verification:** audit ไม่โหลด scorer และ replay GB-17 จาก profile text ทั้ง 2,073,842 persisted model-scored pairs; 17/17 columns ไม่มี mismatch หรือ numeric difference หลัง cast float32; endpoint ไม่หาย (`dataset_v2_feature_verification.json`; `dataset_v2_feature_audit.py:1-40`)
- **production/multimodal ไม่ใช่ 17/18 ชุดนี้:** train_base มีชื่อ username_jaro แต่จริงใช้ JaroWinkler.normalized_similarity; username_lev เป็น normalized distance; มี TF-IDF bio, MPNet SBERT bio, domain/url/mention/hashtag/style/platform pair code และ image wrappers; selected 41 feature ของอีกสายไม่ใช่ feature_matrix 21 columns (`src/identity_resolution/stages/train_base.py:308-335,339-392`; `thesis_rebuild/build_dataset_excel.py:109`; `thesis_rebuild/07_ดูหน้าตา_dataset.md:46`)

## 7. Feature 18: semantic MiniLM cosine และ provenance ที่ยังไม่ครบ

ชื่อ `bert_cos` คือ feature เพิ่ม 1 ตัว ไม่ใช่การเพิ่ม 18 semantic dimensions: fullName + space + bio + space + location, strip และ empty→`[empty]`; frozen pretrained all-MiniLM-L6-v2 encode normalized embedding; similarity = dot(eA,eB) ของ unit vectors (`experiments/code/exp_r2_bert_feature.py:83-117,121-140`; `experiments/code/run_icsec_authoritative_v2.py:150-166`; `features.py V2:19`)

Audit **อ่าน existing .npy/.parquet เท่านั้น**:

- existing embedding shape **36,807×384**, IDs 36,807 ไม่ซ้ำ; unit norm อยู่ใน 0.9999998212–1.0000001192; 3 IDs ไม่อยู่ eligible 36,804 เพราะ profile entity ID หาย แต่ eligible ทุกแถวมี embedding (`dataset_candidate_accounting.json` section existing_minilm_embeddings; `dataset_candidate_audit.py:60-76`)
- legacy pair_bert_cos **2,073,842 rows**: recompute จาก existing vectors **mismatch 0, max diff 0**; V2 bert_cos 2,073,842: mismatch 0 ภายใต้ atol=1e-6/rtol=1e-5, max abs diff 6.556510925292969e-7; endpoint embedding missing 0 ทั้งสอง (`dataset_candidate_accounting.json` section feature18_replay; `dataset_candidate_audit.py:67-76`)
- Source pin เพียง model identifier ไม่ได้พิสูจน์ Hugging Face revision, tokenizer version, encoder weights hash, package versions ที่สร้าง vector หรือ historical encoding ตรง; hash .npy ยืนยัน bytes ปัจจุบันเท่านั้น รายงานจึงใช้คำว่า **cosine replay verified, encoder provenance incomplete** (`experiments/code/run_icsec_authoritative_v2.py:154-156`; `experiments/code/exp_r2_bert_feature.py:109-113`)
- TF-IDF vocabulary fit all bios ของ Stage9 กับ frozen pretrained MiniLM ต่างกัน: normalization/encoding โดยไม่มี fit scorer ใหม่ไม่ใช่การยืนยันว่า vocabulary/representation chain ของทุก branch leak-free (`N9-v2 cell6`; `src/identity_resolution/stages/train_base.py:310-324`; `docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:29,43`)

## 8. ID/entity/ground truth: ต้องแยกหน่วยข้อมูล

| Branch | profile ID หมายถึง | entity label มาจาก | ความเสี่ยง |
|---|---|---|---|
| cleaned24729/prepare | normalize outputProfileName; ใช้ร่วมข้าม platform | outputProfileName-based legacy matching | ไม่ unique profile-row key; source prepare อ้าง ID consistent แต่ไม่เท่ากับพิสูจน์ person truth |
| Stage7/9 notebook | string account-like platform_username/profile_id | Stage8v2 user_folder | null/collision/repair first-vs-last lookup; entity_id_a ขาด entity_b |
| normalized_with_profile_id | numeric profile_row_id ระดับแถว; numeric profile_id ระดับ entity | user_folder โดย mapping | ต้อง exclude missing numeric entity ID; row order ต้อง freeze |
| V2 safe pair | canonical hash ของ sorted numeric row IDs | entity_digest จาก folder; role แยกสองปลาย | hash pseudonym ไม่ใช่ anonymization guarantee; ไม่เปิดเผยในรายงานนี้ |

Sources: `src/identity_resolution/stages/prepare.py:153-155,190-212`; `N6-v2 cells6,8`; `N9-v2 cell4`; `src/identity_resolution/workflows/full_candidate.py:50-68`; `experiments/icsec_final/authoritative_run_v2/real_adapters.py:21-36,39-68`

Numeric snapshot มี 36,807 unique profile_row_id โดย ID เป็นลำดับ index ปัจจุบัน; known folders **15,297** แต่ inventory user_folder distinct **15,298** รวม unknown empty; missing folder/numeric profile_id **3/3**; mapping known folder→numeric entity ID เป็น 1-to-1 (0 multi-ID groups/0 reverse contradictions) ข้อนี้ยืนยัน mapping ภายใน snapshot ไม่พิสูจน์บุคคลจากภายนอก (`dataset_candidate_accounting.json` numeric_entity_mapping; `dataset_candidate_audit.py:31-33`)

Ground truth ของ canonical input: **29,247 all-platform = 29,243 cross-platform + 4 same-platform**; มี repeated entity/platform 4 groups จึงห้ามยึดแต่ละ entity มีหนึ่งบัญชีต่อ platform (`dataset_inventory.csv:4-6,8`; `dataset_candidate_accounting.json` canonical_candidate_accounting)

### Historical GT matrix / CSV ไม่ควรรวมกับ current normalized denominator

- NGT recipe กำหนด missing folder เป็น `__no_label_index` แล้วสร้าง symmetric sparse entries ของทุกคู่ใน folder ไม่กรอง platform; diagonal ไม่มี self-pair; index CSV ใช้ merged userName/user_folder (`NGT cells6,8,10,14`)
- `train_data/ground_truth_matrix.npz` **ไม่พบ** ในตำแหน่งคาดหวัง จึงไม่ได้ตรวจ shape/nnz จาก matrix และไม่อ้างว่ามี binary ปัจจุบัน; CSV/index ยังมีอยู่ (`dataset_inventory.csv` missing npz entry; `dataset_audit_outputs.json` ground_truth empty; `dataset_candidate_accounting.json` historical_gt_csv)
- `ground_truth_pairs.csv` มี **58,500 directed rows** ไม่ซ้ำ ไม่มี self/out-of-range/nonunit label และ symmetry ตรง; upper triangle มี **29,246 cross-platform + 4 same-platform** ซึ่งมากกว่าปัจจุบัน cross positives 3 คู่; index-folder ต่าง current merged 3 rows และมี **6 directed pairs ที่ folder ตาม index ต่างกัน** จึงไม่ประกาศ CSV เป็น authority ของ current normalized truth (`dataset_candidate_accounting.json` historical_gt_csv; `dataset_candidate_audit.py:55-59`)
- Label check ที่ไม่สุ่ม/ไม่เปิด sealed test artifact: Stage9 บน blocking snapshot resolve สองปลายได้ **203,367** คู่, unresolved **1,334**; label mismatch 0 และ entity_id_a mismatch 0 เฉพาะ resolvable; บน cleaned24729 resolve ไม่ได้ **204,701** คู่ ไม่ใช่ label verified pass (`dataset_audit_outputs.json` label_verification; `dataset_readonly_audit.py:143-148`)

## 9. Pair labels และ blocking: อย่าปนสามประชากร

### 9.1 Stage8v2 supervised pairs ไม่ใช่ candidate population

Positive pairs: groupby user_folder, combinations ภายใน folder, ข้าม platform เท่านั้น; random negatives: uniform platform-combo แล้วสุ่มหนึ่งแถวต่อ platform ตรวจ folder ต่าง; target **5×positives**, seed=42; hard negatives จาก candidates ที่ platform ต่าง+known folder ต่าง target=positives; concatenate/shuffle ไม่ canonical dedup (`N8-v2 cells2,4,6,8,10`)

Persisted labels 29,243 positive + 175,458 negative = 204,701; negative ratio สอดคล้อง target 5 random + 1 hard แต่ **artifact ไม่มี pair_type จึงไม่ได้พิสูจน์ breakdown ของทุก negative row**; duplicate unordered pairs 30 เป็นข้อเตือนว่าการสุ่มไม่ได้ canonical-dedup ใน source (`dataset_inventory.csv:10-11`; `N8-v2 cell10`)

### 9.2 Legacy Stage7/v2 candidates 873,956

- Original Stage7: exact URL/username; prefix3/stripped-prefix4/fullname-first4/rare-domain≤5; block>500 **สุ่มเหลือ 500** ด้วย seed42; graph edge weight mean ของ fullname WRatio/username token-sort/URL binary; accept≥.5 และ prune<.3 (หลัง accept .5 prune นี้ไม่ตัด edge ต่ำ .3 เพิ่มได้); union exact หากยังไม่มี (`N7-original cells3,5,7,9,11,13,15`)
- v2 Stage7: prefix3 username/fullname, fullname tokens len≥3, url_domain, location first20, stripped username prefix4; key len≥2; block>500 **ทิ้งทั้ง block**; cross-platform infer prefixของ string ID; unordered min/max set; similarity max ของ token-sort username/fullname≥.5; ช่วงนี้คนละ blocking กับ original (`N7-v2 cells3,5,7,9,11`)
- Persisted candidate_pairs.csv มี 873,956 คู่ ไม่มี duplicate unordered/self; ไม่ได้ full-rebuild notebook candidate graph ใน audit นี้ จึง **producer version ยัง unproven**; 29,243 unique positive keys ใน supervised artifact มีอยู่ใน candidates **25,252**, ไม่อยู่ **3,991**, key coverage **0.8635228944**; string-key lookup ambiguous ต้องไม่เทียบกับ canonical row retrieval recall; unambiguous known-entity positives 25,209/unresolved pairs 3,306 (`dataset_inventory.csv:9`; `dataset_candidate_accounting.json` legacy_candidates)
- v2 notebook print `Blocking recall ~91.8%` เป็น hard-coded summary ไม่ได้คำนวณจาก truth ใน cell ดังกล่าว และไม่ตรง current artifact key coverage ที่ audit วัด จึงไม่ใช้เป็น verified retrieval recall (`N7-v2 cell11`)

### 9.3 Canonical full-candidate/V2: คำนวณใหม่จริงแบบ read-only

ใช้ fc.load_profiles normalize strings, กรอง missing numeric row/entity IDs 3 แถวก่อน; eligible **36,804** (twitter 13,959/googleplus 11,889/instagram 10,956), cross-platform universe **449,149,239** ไม่ใช่ universe 36,807 rows (**449,222,850**) (`src/identity_resolution/workflows/full_candidate.py:50-78`; `dataset_candidate_accounting.json` eligibility/canonical_candidate_accounting)

- Exact: userName_norm exact len≥3 หรือ nonempty lower externalUrl_clean exact; cross-platform only ไม่รับประกัน person match (`full_candidate.py:90-122`)
- Scored blocking: ASCII-stripped lower prefix3 จาก username/fullname; external_domain ตัด 18 generic domains ตาม source; union cross-platform pairs แล้วลบ exact ไม่มี block cap หรือ graph similarity filterในฟังก์ชันนี้; incremental counts ขึ้นกับลำดับ keys (`full_candidate.py:29-35,43-47,60-67,125-151`)
- Recomputed keys เทียบ persisted exact/model_scored/workflow **missing=0/extra=0/duplicate=0 ทุกชุด**; ไม่ใช่เพียง summary ตรงกัน (`dataset_candidate_accounting.json` candidate_artifacts; `dataset_candidate_audit.py:35-50`)

| Scope | จำนวนคู่/positive | นิยาม |
|---|---:|---|
| exact | 12,403 | true positive 12,340 / false positive 63 |
| model scored | 2,073,842 | cross-platform positives 13,591 |
| workflow candidates | 2,086,245 | exact + scored ไม่ทับกัน |
| covered positives | 25,931 | 12,340 + 13,591 |
| blocking misses | 3,312 | 29,243 − 25,931; ไม่สร้าง synthetic classifier prediction |
| retrieval recall | 0.8867421263 | 25,931 / 29,243 |
| search space reduction | 0.9953551185 | 1 − 2,086,245 / 449,149,239 |
| username exact incremental | 11,133 | first exact group contribution |
| URL exact incremental | 1,270 | novel pairs after username exact |
| username prefix3 incremental | 1,026,466 | novel scored after exact |
| fullname prefix3 incremental | 1,041,315 | novel scored after previous key |
| external domain incremental | 6,061 | novel scored after previous keys |

แหล่งตัวเลขทุกแถว: `dataset_candidate_accounting.json` canonical_candidate_accounting/candidate_artifacts; กฎ `src/identity_resolution/workflows/full_candidate.py:90-151`; audit `dataset_candidate_audit.py:35-50` identities ทั้งสี่ตรวจ true: exact/scored disjoint, exact+scored=workflow, covered+missed=cross positives, all=cross+same ไม่ได้อ้าง threshold/model metrics จากจำนวนเหล่านี้

## 10. ผลตรวจ transformation ทั้งหมด (ไม่ซ่อน FAIL)
''')
add(f"มี checks **{len(trans)}** รายการ: "+', '.join(f'{k}={v}' for k,v in sorted(stats.items()))+' ผลยังมี unresolved chain และ dependency missing; ห้ามอ่านจำนวน PASS ว่า raw-to-result ผ่านทั้งหมด (source: `transformation_verification.csv:1-'+str(len(trans)+1)+'`)\n')
add('| Transformation | Checked rows/cells | Mismatches | Status | Source/output |\n|---|---:|---:|---|---|')
for i,r in enumerate(trans,2):add('| '+r['transformation'].replace('|','/')+' | '+r['checked_rows']+' | '+r['mismatch_rows']+' | '+r['status']+' | `'+r['source']+'`; `transformation_verification.csv:'+str(i)+'` |')
add('''
## 11. งานที่ปิดได้และ blockers ก่อน rebuild จริง

**ปิดได้ใน phase นี้:** inventory/hash/schema/missingness/duplicates, typed row-vs-entity ID accounting, workbook export compatibility, per-rule replay ที่ไม่ต้อง dependency missing, pair label audit เฉพาะ resolvable, canonical retrieval accounting เทียบ unordered persisted keys, corrected V2 features ทุกแถวและ cosine-from-existing-vector replay (`dataset_inventory.*`; `dataset_v2_feature_verification.json`; `dataset_candidate_accounting.json`; `transformation_verification.csv`)

**ยังไม่ปิด:** JSON raw/source URI/revision/license/consent; chronology/log producer 24,729↔36,807; typo nomalized entity repair; advanced bio replay ไม่มี emoji/ftfy chain; hidden coordinate fill; recipe/collision repair ที่สร้าง legacy feature values; model revision/tokenizer ของ MiniLM; absent npz; current raw-vs-normalized missing-ID discrepancies; producer of 873,956 candidates ไม่ได้ full replay (`NC-later cells39,46,58`; `dataset_inventory.csv`; `docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:100-105,157-162`)

แนะนำ input contract สำหรับงานถัดไปเป็น **snapshot-based retrospective reanalysis** จาก `normalized_profiles_with_profile_id.csv` พร้อม SHA256/explicit 3-row exclusions และ entity/row IDs คนละชื่อ; field missing ต้องเก็บ mask ไม่ใช้ nan-string/zero-coordinate; canonical unordered pair dedup; ห้าม negative label เมื่อ entity unknown; labels/role routing ต้องสองปลายและไม่เปิด sealed file ก่อน final evaluator (`docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md:18-29,37-48`; `experiments/icsec_final/authoritative_run_v2/real_adapters.py:71-99,110-131`)

## 12. Audit artifacts และวิธีทำซ้ำ

ทั้งหมดสร้างใหม่ใน assigned directory ไม่เขียนต้นฉบับ:

- `dataset_readonly_audit.py`: inventory/stdlib workbook/legacy Stage9 and cleaning rules replay; refuses existing outputs unless --refresh-new-audit.
- `dataset_candidate_audit.py`: numeric mapping, canonical candidate reconstruction/key equality, GT CSV, feature18 dot product; no sealed role labels.
- `dataset_reconciliation_audit.py`: profile clean rules/typed OpenXML control escaping; reconciles only this new audit's check rows.
- `dataset_v2_feature_audit.py`: independent whole-artifact corrected GB-17 replay.
- `dataset_report_renderer.py`: render report and extend new inventory from concrete inspected artifacts.
- `dataset_inventory.csv/json`, `transformation_verification.csv`, `dataset_audit_outputs.json`, `dataset_candidate_accounting.json`, `dataset_reconciliation_outputs.json`, `dataset_v2_feature_verification.json`, `dataset_workbook07_evidence.json`, `dataset_notebook_evidence.json`: aggregates/source/hash only.

รันใน checkout copy/assigned output directory ใหม่ด้วย Python 3.11 environment ที่มี pandas/numpy/scipy/sklearn/rapidfuzz; ไม่ install dependency หากขาด:

```bash
.venv/bin/python docs/research_rebuild/phase_01/dataset_readonly_audit.py
.venv/bin/python docs/research_rebuild/phase_01/dataset_candidate_audit.py
.venv/bin/python docs/research_rebuild/phase_01/dataset_reconciliation_audit.py
.venv/bin/python docs/research_rebuild/phase_01/dataset_v2_feature_audit.py
.venv/bin/python docs/research_rebuild/phase_01/dataset_report_renderer.py
```

คำสั่งแรกปฏิเสธ overwrite เมื่อมี outputs; อย่าใช้ refresh กับ frozen/historical artifact package ตัวเลือก refresh ใช้ได้เฉพาะไฟล์ audit ใหม่ของงานนี้ ไม่ใช่ต้นฉบับ กรณี dependency missing ต้องเก็บ NOT_EXECUTED ไม่ fabricate output (`dataset_readonly_audit.py:15-20,92-108`)

## ภาคผนวก A — Notebook source aliases และ hash

| Alias | Exact source path | SHA-256 |
|---|---|---|''')
alias={'09_features.ipynb':'N9-original','stage9_features_v2.ipynb':'N9-v2','stage8_labeling_v2.ipynb':'N8-v2','stage7_blocking_v2.ipynb':'N7-v2','07_blocking.ipynb':'N7-original','stage6_preprocessing_v2.ipynb':'N6-v2','01_data_clean_first.ipynb':'NC-first','01_data_clean_later.ipynb':'NC-later','build_ground_truth_matrix.ipynb':'NGT'}
for path,info in nb.items():
 if Path(path).name in alias:add('| '+alias[Path(path).name]+' | `'+path+'` | `'+info['sha256']+'` |')
add('''
`dataset_notebook_evidence.json` ให้ cell source hashes เพิ่มเพื่อให้ตรวจได้แม้ notebook metadata/output เปลี่ยน; source aliases ในเนื้อหาข้างบนต้องตีความตาม table นี้ ไม่ใช่ notebook ที่ชื่อคล้ายกันอีก path

## ภาคผนวก B — SHA256 ของ inputs/artifacts ที่ตรวจ

| Path | SHA-256 / absence |
|---|---|''')
for r in inv:add('| `'+r['path']+'` | `'+str(r.get('sha256','ABSENT'))+'` |')
report=OUT/'01_DATASET_AND_FEATURE_LINEAGE.md';assert not report.exists();report.write_text('\n'.join(s)+'\n')
print(json.dumps({'report':str(report.relative_to(ROOT)),'inventory_entries':len(inv),'transformation_checks':len(trans),'status_counts':dict(stats),'v2_feature_values_checked':v2['rows']*len(v2['features'])},ensure_ascii=False))
