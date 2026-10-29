from pathlib import Path
import json,csv,hashlib,subprocess,re,sys,io,collections
W=Path(__file__).resolve().parents[4];R=W/'research_v2/review';work=R/'_work';sys.path.insert(0,str(work/'v3_deps'));import pymupdf
base=json.loads((work/'v3_baseline.json').read_text());doc=pymupdf.open(W/'_input_v1/thesis/historical_thesis.pdf')
registry={}
def raw(path,repo='main',ref='1e0a2db'):
 return subprocess.check_output(['git','show',ref+':'+path],cwd=work/'repos'/repo)
def artifact(path,repo='main',ref='1e0a2db',section=''):
 b=raw(path,repo,ref);h=hashlib.sha256(b).hexdigest();registry[repo+':'+path]={'repo':repo.upper(),'commit':ref,'path':path,'sha256':h,'bytes':len(b)}
 return f'[{repo.upper()}@{ref}:{path}#L1-L{len(b.splitlines())} {section or "artifact"}] SHA-256 `{h}`'
def data(path):return json.loads(raw(path))
M='pub_multi/ref/main_report.json';F='pub_multi/ref/full_report.json';C='pub_multi/ref/crm_report.json';B='pub_multi/ref/base_report.json';I='pub_multi/ref/img_stats_report.json';S='pub_multi/ref/strict_report.json';L='pub_multi/ref/leak_safe_report.json'
a={p:artifact(p) for p in [M,F,C,B,I,S,L,'pub_multi/ref/suite_report.json','pair_stats.json','train_data/pair_stats.json','data/processed/pipeline_report.json','train_data/stage8_labeling.ipynb','train_data/stage10_dataset.ipynb','train_data/v2/stage8_labeling_v2.ipynb','pub_multi/res/feat_imp.csv','pub_multi/res/thr_sweep.csv','pub_multi/res/classical_leaksafe_cmp.json']}
main,full,crm=data(M),data(F),data(C)
agg=json.loads((work/'v3_profile_aggregates.json').read_text());aggsha=hashlib.sha256((work/'v3_profile_aggregates.json').read_bytes()).hexdigest()
aggart=f'`review/_work/v3_profile_aggregates.json` SHA-256 `{aggsha}`; exact code `review/_work/aggregate_queries.log`'
source='[MAIN@1e0a2db:train_data/stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py#L150-L186 load_profiles/build_ground_truth_pairs]'
crmcode='[MAIN@1e0a2db:train_data/stage15_crm_entity_pipeline/run_crm_entity_pipeline.py#L373-L403 build_lead_scores]'
V2='[V2R:HISTORICAL_EXPERIMENT_AUDIT.md#A]';risk='[V2R:METHODOLOGICAL_RISKS.md#1]'
ledger=[]
def add(id,claim,page,repo,art,status,confidence,notes='',v2=V2,section=''):
 ledger.append({'Claim ID':id,'Thesis claim':claim,'PDF page / printed page / section':f'{page} / {page-15 if page>=16 else "VI" if page==12 else "UNKNOWN"} / {section or "ข้อความ/ตารางตามหน้าที่ระบุ"}','Repository path@commit#symbol':repo,'Artifact (path, SHA-256)':art,'V2 review reference':v2,'Status':status,'Confidence':confidence,'Notes':notes})
add('TC-01','Synthetic/company-template + platform 15,234/12,871/8,702 เทียบ valid 13,959/10,956/11,889; แยกตาราง split ออกจากข้ออ้างแหล่งข้อมูล',70,source,a['train_data/stage10_dataset.ipynb']+'; '+a[F],'CONFLICT','HIGH','ภาพ raster pp70–71: ตาราง platform เก่าและย่อหน้า HITL/split ถูกขีดฆ่าสีน้ำเงิน แต่ประโยค Synthetic ตอนต้นยังเป็นข้อความปกติ; split 12,103 entities /162,442 pairs มี saved output จริง ไม่ใช่ตัวเลขไร้ที่มา; ไม่พบหลักฐาน company synthesis',section='4.1; ต่อ PDF71/พิมพ์56')
add('TC-02','LinkSocial/user_folder เทียบ Human-in-the-Loop labeling',70,'[MAIN@1e0a2db:train_data/v2/stage8_labeling_v2.ipynb#L148-L184 build_positive_pairs]',a['train_data/v2/stage8_labeling_v2.ipynb'],'CONFLICT','HIGH','HITL paragraph เป็นข้อความที่ถูกขีดฆ่า; code ใช้ group label; ไม่มี annotation ledger/ผู้ตรวจ/κ; วิธีสร้าง corpus label ต้นทางยัง UNKNOWN ไม่ปลด G0',section='4.1; เทียบ PDF33–45/พิมพ์18–30')
add('TC-03','4,060,200 positive;20,301,000 random;8,120,400 hard target;302,433 hard actual;24,663,633 total',43,source,a['pair_stats.json']+'; '+a['train_data/pair_stats.json']+'; '+aggart,'CONFLICT','HIGH','พบตัวเลขใน pair_stats ทั้งสองจริง แต่ JSON ถูกตัดค้างที่ qa.no_duplicate_pairs จึง parse ไม่ได้และไม่พิสูจน์ execution; canonical eligible groups max4 ให้29,243 คู่ ไม่ใช่4.06M; ไม่สรุปว่าโมเดลฝึกด้วย label noise มหาศาล',section='3.3.3; ต่อ Table3.5 PDF44/พิมพ์29')
add('TC-04','36,807 raw vs36,804 eligible',71,source,a[F]+'; '+aggart,'VERIFIED','HIGH','exclude3 แถวที่ไม่มี profile_id; canonical user_folder nonmissing15,297 groups; raw missing group3แถวไม่ใช่บุคคลเดียวกัน; B09 29,247 ยังไม่อธิบายหมด',section='Table4.1; เทียบ PDF33/พิมพ์18')
add('TC-05','873,956 vs2,073,842 candidate pairs; RR99.9% vs99.54%',70,'[MAIN@1e0a2db:train_data/v2/stage7_blocking_v2.ipynb#L1-L800 blocking]; [MAIN@1e0a2db:train_data/stage7_14_full_candidate_pipeline/run_full_candidate_pipeline.py#L118-L179 exact/blocking]',a['data/processed/pipeline_report.json']+'; '+a[F],'VERIFIED','HIGH','เป็นคนละ pipeline generation; 873,956 มี pipeline_report; RR99.9% เป็นการปัดหนึ่งหลักจากตัวหาร all-pairs เก่า ไม่ใช่ comparable cross-platform RR; ข้อความเก่าในPDF70ถูกขีดฆ่า',section='4.1; PDF71/พิมพ์56')
add('TC-06','coverage88.67%=1−3,312/29,243',71,'[MAIN@1e0a2db:pub_multi/ref/full_report.json#L1-L40 data_report/blocking_report]',a[F],'VERIFIED','HIGH','artifactเดียวกันมี29,243 total และ25,931 covered; ลบได้3,312; rounding88.6742126320829%ตรง ไม่ผสม3,316/29,247ของR-series',section='Table4.2')
add('TC-07','images11.5%;captions5.9%;test both-image pairs0',100,'[MAIN@1e0a2db:train_data/stage7_13_multimodal_suite/README.md#L28-L39 DataSources/Notes]',a[M],'VERIFIED','HIGH','artifact:4,248/36,804 images,2,173 captions;test1,873 any-image,0 both-image; local imagesเฉพาะTwitter; PDF93/พิมพ์78ยืนยันรายละเอียด; PDF103เป็นbibliography ไม่ใช่image evidence',section='5.3; PDF93/พิมพ์78')
add('TC-08','AP.9789/F1.9340 vsproduction precision.9550 vsR3 F1.8373',80,'[MAIN@1e0a2db:pub_multi/ref/main_report.json#L1-L81 metrics]; [MAIN@1e0a2db:exp_lib.py#L107-L140 evaluate]',a[M]+'; '+a[F]+'; '+artifact('experiments/r3_results.json'),'VERIFIED','HIGH','ยืนยันว่าเป็นตัวเลขคนละpopulation ไม่ใช่head-to-head; R3ไม่ปรากฏในthesisนี้ ใช้V2เป็นcross-reference; ตารางละเอียด METRIC_POPULATION_MAP.md',section='4.3.2; เทียบPDF87/พิมพ์72')
add('TC-09','List of Tables3.7/3.8ไม่ตรงbody;equation/figure references malformed',53,'UNKNOWN','PDF immutable + raster/ข้อความ; SHA-256 '+base['thesis_sha256'],'CONFLICT','HIGH','ListจริงPDF12/พิมพ์VI ไม่ใช่PDF6; bodyTable3.7คือ41-feature schema,Table3.8PDF54คือmatrix sizes; equationPDF49ซ้ำ;เป็นdocument errata ไม่ใช่experimental defect',section='Table3.7; PDF12/VI,PDF54/39')
add('TC-10','bibliography8รายการและLinkSocial/LeadScoring attribution',103,'UNKNOWN','Crossref metadata `review/_work/v3_web_metadata.json`; `v3_LinkSocial_crossref.txt`; immutable thesis SHA-256 '+base['thesis_sha256'],'CONFLICT','HIGH','[3]ผู้แต่งผิด;[6]DOIชี้งานlandslideไม่ใช่lead scoring;[1]หน้า260–269ขัดV2/P38และrepo260–267;รายละเอียด§Bibliography',section='บรรณานุกรม')
add('TC-11','Lead Scoring เป็นผลลัพธ์ระบบ/พร้อมใช้งานธุรกิจ',99,crmcode,a[C],'CONFLICT','HIGH','มีheuristic0.4completeness+0.3platform+0.3engagementและ19,799scoresจริง แต่ไม่พบconversion/outcome labelsในartifact inventories; business predictive validity UNKNOWN;นอกproof scopeH1–H5',section='5.1.1; PDF101–102/พิมพ์86–87')
add('TC-12','70/15/15 table4.2,main-suite split,chunked split และR-series30%test',70,'[MAIN@1e0a2db:exp_lib.py#L36-L38 bucket]; [MAIN@1e0a2db:train_data/stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py#L208-L232 assign_splits]',a['train_data/stage10_dataset.ipynb']+'; '+a[M]+'; '+a[S],'VERIFIED','HIGH','แต่ละgenerationมีsplitต่างกัน; stage10ใช้endpoint-aอาจรั่วอีกด้าน;main-suiteprofiles22,478/7,925/6,401;stricttrain_size23,148หลังsampling/val4,511,311/test462,908;R-seriesmd5test30%ถูกreuse≥15ตามV2 ไม่รวมเป็นsplitเดียว',section='Table4.2; PDF45–46,54,72')
add('TC-13','PDFมีtracked revisions:ข้อความขีดฆ่ายังคงอยู่ในtext extraction',70,'UNKNOWN','raster `review/_work/thesis_page_70.png`, `thesis_page_71.png`; immutable PDF SHA-256 '+base['thesis_sha256'],'VERIFIED','HIGH','VERIFIEDเฉพาะdocument observation ไม่ใช่scientific claim; TC ledgerหลักต้องมีrepo+artifactสำหรับverified จึงจัดexceptionเป็นCONFLICTด้านpresentation',section='4.1 revision markup')
ledger[-1]['Status']='CONFLICT'
add('TC-14','Chapter5รุ่นเก่า:IdentityMLP3-class,F1.93/P.97/R.90/AUC.982;873,956→10,723',95,'[MAIN@1e0a2db:train_data/stage11_training.ipynb#L1-L250 IdentityMLP/FocalLoss]',a['data/processed/pipeline_report.json'],'CONFLICT','HIGH','outputcounts20,480/3,940/849,536และ10,723ตรงartifact;model_metricsว่าง ไม่ยืนยัน.93/.97/.90/.982;3decision tiersไม่เท่ากับ3-class training;ต้องแยกประวัติ/ตรวจstrikethrough',section='5.1')
add('TC-15','RR99.54%อธิบายเป็นเฉพาะคู่ที่ส่งmodel',71,'[MAIN@1e0a2db:pub_multi/ref/full_report.json#L1-L40 blocking_report]',a[F],'CONFLICT','HIGH','storedRR99.53551184798958%ใช้exact12,403+scored2,073,842;scored-onlyเป็น99.53827329094061%;ทั้งคู่ปัด99.54แต่ตัวเศษคนละชุด',section='Table4.2')
add('TC-16','PDF82กล่าวthreshold.35 optimizeF1บนtest;PDF61/83กล่าวvalidation',82,'[MAIN@1e0a2db:train_data/stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py#L388-L393 best_threshold; #L446-L450 calibration]',a[M],'CONFLICT','HIGH','codeเลือกจากvalidation;testthresholdsweepมีจริงแต่ไม่พิสูจน์ว่าเลือกจากtest;แก้ถ้อยคำ ไม่กล่าวหาว่าtest-tunedโดยไม่มีlineage',section='4.3.3')
add('TC-17','Table3.6:profiles15,848/17,595/3,364;rows10,133,486/4,511,311/462,908;Table3.8มี48columns',46,'[MAIN@1e0a2db:pub_multi/doc/data_er_latest_th.md#L1-L200 historical_chunked]',a[S],'HISTORICAL_ONLY','MEDIUM','4,511,311valและ462,908testตรงstrict_report;trainหลังundersample23,148ไม่ใช่10,133,486;ส่วนที่เหลือมีเอกสารแต่ไม่พบmatchingrawsplitmanifestที่ตรวจได้โดยไม่อ่านrealpairdata;48metadata-inclusiveไม่ใช่41feature vector',section='Table3.6;PDF54/พิมพ์39')
add('TC-18','PDF72captionรวม36,604profiles',72,source,a[F],'CONFLICT','HIGH','captiontypo;Table4.1และartifactเป็น36,804',section='Figure4.1')
add('TC-19','image_stats→image_contextยืนยันประโยชน์ภาพ/significanceและพร้อมproduction',80,'[MAIN@1e0a2db:train_data/stage7_13_multimodal_suite/run_multimodal_suite.py#L346-L350 composite_score]',a[M]+'; '+a[I],'CONFLICT','HIGH','savedmetricตรงแต่ไม่มีpairedCI/independentreplicatesและboth-images0;ผลอาจมาจากavailability/caption cross-text;ไม่รองรับcausalimage-to-imagematchingหรือproduction/businessvalidation',section='4.3.1–4.3.2;PDF93–99')
# Exact value-by-value checks: compare already-stored numbers to thesis, never compute model metrics.
def number(id,label,page,path,value,field):
 text=doc[page-1].get_text();opts=[str(value),f'{value:,}' if isinstance(value,int) else f'{value:.4f}']
 if field.endswith('.threshold'):opts.append(f'{value:.2f}')
 present=any(x in text for x in opts)
 add(id,f'{label}: '+('/'.join(opts[:2]) if isinstance(value,int) else f'{value:.4f}'),page,f'[MAIN@1e0a2db:{path}#L1-L{len(raw(path).splitlines())} {field}]',a.get(path) or artifact(path),'VERIFIED' if present else 'UNKNOWN','HIGH' if present else 'LOW','ARTIFACT_CONSISTENTเฉพาะreportedvalue/scope;ไม่ใช่independentreproduction' if present else 'ไม่พบtokenตรงบนpage text;ตรวจfigure/roundingต่อ',section=field)
for page in [78,96]:
 for label,path in [('Text/Attribute',B),('ImageStats',I),('ImageContext',M)]:
  d=data(path)['metrics']
  for key in ['feature_count','test_avg_precision','test_roc_auc','test_f1']+(['test_precision','test_recall'] if page==78 else []):number(f'N-{page}-{label}-{key}',label+' '+key,page,path,d[key],'metrics.'+key)
for model in main['metrics']['leaderboard']:
 for key in ['val_ap','val_auc']:number('N-77-'+model['model']+'-'+key,model['model']+' '+key,77,M,model[key],'metrics.leaderboard')
for label,path in [('Text',B),('ImageStats',I),('ImageContext',M)]:
 d=data(path)['metrics'];number('N-79-'+label+'-threshold',label+' threshold',79,path,d['threshold'],'metrics.threshold')
 for label2,v in zip(['TN','FP','FN','TP'],sum(d['confusion_matrix'],[])):number('N-79-'+label+'-'+label2,label+' '+label2,79,path,v,'metrics.confusion_matrix')
for split,s in main['leakage_report']['split_stats'].items():
 for key,value in s.items():number('N-72-'+split+'-'+key,split+' '+key,72,M,value,'leakage_report.split_stats.'+split)
 number('N-72-'+split+'-rows',split+' rows',72,M,main['leakage_report']['rows_by_split'][split],'leakage_report.rows_by_split')
for key in ['test_avg_precision','test_roc_auc','test_f1','feature_count','threshold']:number('N-80-'+key,key,80,M,main['metrics'][key],'metrics.'+key)
for page in [71,85,98]:
 for key,value in full['data_report'].items():
  if isinstance(value,(int,float)) and (str(value) in doc[page-1].get_text() or f'{value:,}' in doc[page-1].get_text()):number('N-'+str(page)+'-'+key,key,page,F,value,'data_report.'+key)
for label,k in [('Exact','exact'),('HighMatch','match'),('Review','review')]:
 d=full['production_threshold_report']['tiers'][k]
 for key,value in d.items():number('N-87-'+k+'-'+key,label+' '+key,87,F,value,'production_threshold_report.tiers.'+k+'.'+key)
for key in ['final_match_only_count','final_match_only_true_positive_count','final_match_only_precision','final_match_only_recall']:number('N-87-'+key,key,87,F,full['production_threshold_report'][key],'production_threshold_report.'+key)
for label,key in [('HOT','HOT'),('WARM','WARM'),('COLD','COLD')]:number('N-99-'+label,'Lead tier '+label,99,C,crm['lead_tier_breakdown'][key],'lead_tier_breakdown.'+key)
for key in ['test_avg_precision','test_roc_auc','test_f1']:number('N-96-strict-'+key,'strictMLP '+key,96,S,data(S)[key],key)
for key in ['test_avg_precision','test_roc_auc','test_f1']:number('N-96-classical-'+key,'classicalGB '+key,96,L,data(L)['metrics'][key],'metrics.'+key)
# Additional narrative quantitative claims whose supporting raw score/error tables must not be reanalyzed this round.
for id,cl,p,art in [('N-81-distribution','NO_MATCH mean.1095 median.0684;MATCH mean.9012 median.9966',81,'pub_multi/doc/ch04_results_formal_th.md'),('N-83-ECE','validationECE.0000/testECE.0044',83,'pub_multi/doc/ch04_results_formal_th.md'),('N-89-errors','FP/FN sample200each;platform50/110',89,'pub_multi/doc/ch04_results_formal_th.md'),('N-90-errors','nameweak17/82;69/135;strong10/3;image51/71;caption20/20 และร้อยละที่แสดง',90,'pub_multi/doc/ch04_results_formal_th.md'),('N-92-groupimportance','Name89.51%;Bio7.71%;Style1.21%;Platform.76%;Caption.65%;18zeroimportance',92,'pub_multi/res/feat_imp.csv')]:
 add(id,cl,p,f'[MAIN@1e0a2db:{art}#L1-L{len(raw(art).splitlines())} narrative]',artifact(art),'HISTORICAL_ONLY','MEDIUM','พบreportedsummary/featureimportance artifact แต่ไม่เปิดหรือคำนวณใหม่จากrealrow-levelerrors/scores;ไม่ยกระดับเพียงเพราะsummaryซ้ำกัน')
# Capture every remaining non-example numerical token for transparent residual audit coverage.
residual=[]
for page in range(31,103):
 if 35<=page<=42:continue # sample profile transformations: no profile values are exported.
 text=doc[page-1].get_text();tokens=re.findall(r'(?<![A-Za-z])\d[\d,]*(?:\.\d+)?(?:%|e-\d+)?',text)
 tokens=sorted(set(x for x in tokens if 'e' not in x and not re.fullmatch(r'[345]\.\d+(?:\.\d+)?',x) and ('%' in x or '.' in x or int(x.replace(',',''))>18)))
 claims=' '.join(r['Thesis claim'] for r in ledger if r['PDF page / printed page / section'].startswith(str(page)+' /'))
 left=[t for t in tokens if t not in claims and t!=str(page-15)]
 if left:
  residual.append({'page':page,'printed':page-15,'tokens':left})
  add('RES-'+str(page),'Residual numeric census: '+', '.join(left),page,'UNKNOWN','immutable thesis SHA-256 '+base['thesis_sha256'],'UNKNOWN','LOW','เป็นtokenregisterเพื่อไม่ทำเลขตกหล่น ไม่ถือว่าเลขที่พบตรงในartifactอื่นมีความหมายเดียวกัน;รวมบางequation/figure/ordinal;ต้องทำclaim disambiguationต่อก่อนใช้เป็นผลวิจัย')
(work/'v3_ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2));(work/'v3_artifact_registry.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2));(work/'v3_numeric_residual.json').write_text(json.dumps(residual,ensure_ascii=False,indent=2))
def table(fields,rs):
 def cell(x):return str(x).replace('|',' / ').replace('\n',' ')
 return '| '+' | '.join(fields)+' |\n|'+ '|'.join(['---']*len(fields))+'|\n'+'\n'.join('| '+' | '.join(cell(r.get(k,'')) for k in fields)+' |' for r in rs)+'\n'
head='''# Thesis Evidence Reconciliation — Round 3

สถานะวิทยาศาสตร์: NO-GO. ตรวจเอกสาร/โค้ด/saved aggregate artifacts และเฉพาะ profile aggregates ที่ผู้ใช้อนุญาต; ไม่ train/inference/GA/metrics ใหม่บน labeled pairs. VERIFIED หมายถึง claim ตรงกับหลักฐานที่ระบุ ไม่ใช่ผลวิจัยได้รับอิสระยืนยันแล้ว.

## Scope และ immutable inputs

'''
head+=f'''Thesis 105 หน้า SHA-256 `{base["thesis_sha256"]}`. สำเนา `_input_v1/thesis/historical_thesis.pdf` เหมือนต้นฉบับทั้ง Downloads และ source workspace. PDF page ใช้ one-based; body printed = PDF−15; สารบัญตารางจริง PDF12/VI. ชื่อบทและตัวอย่างบัญชีไม่ถูกส่งออก. [V2R:FINAL_HANDOFF_TH.md#ส่วนที่ 1]

'''
head+='''Pinned MAIN:1e0a2db,50d95e9,08f4c5e; BACKUP:903246c,ab93b36. ใช้ commit เดิมตาม [V2R:REPOSITORY_RESEARCH_INVENTORY.md#1]. HEAD inspection clones ยัง1e0a2db/903246c;source workspacea2dce39เป็นคนละbranchกับMAIN/default ไม่ถือเป็นdriftของpinned evidence. Remote driftแยกบันทึกใน `_work/v3_repo_state.json`. ไม่มีการแก้source/design.

'''
head+='''## ข้อยุติสำคัญ

1. Raster ตรวจพบ tracked deletions ที่ text extraction ไม่แยกออก (TC-13): ตาราง platform เก่า/HITL/split ถูกขีดฆ่า แต่ Synthetic paragraphต้นPDF70และข้อจำกัดPDF100ยังอยู่เป็นข้อความปกติ. ไม่กล่าวหาว่าแต่งข้อมูล.
2. ตาราง4.2 splitเก่ามี execution evidenceจริงใน notebook;เป็นหลักฐานคนละgeneration ไม่ใช่splitของfinal GB. [V2R:HISTORICAL_EXPERIMENT_AUDIT.md#F05]
3. ตัวเลข4.06Mมีpair_statsจริงแต่ไฟล์JSONไม่สมบูรณ์;ไม่รองรับเหตุผลว่าการฝึก4.06Mสำเร็จหรือlabelถูกต้อง. Canonical aggregates29,243คู่/กลุ่มสูงสุด4. ไม่มีหลักฐาน massive-noise training ของfinal GB.
4. Main GB AP.9789/F1.9340,coverage88.67%,review86,296 และทั้งสองฝั่งมีภาพ0ตรงaggregateartifact. ไม่ใช้เพื่อยืนยันgeneralization/businessROI.
5. Numeric residual rowsท้ายledgerยังUNKNOWN:ไม่ถือว่าการสร้างregisterเท่ากับพิสูจน์ทุกmetricในภาพ/สูตรแล้ว. Claim-levelauditจึงPARTIALในส่วนที่ไม่มีprimaryartifact;blockersระบุชัด.

## Claim ledger

'''
(R/'THESIS_EVIDENCE_RECONCILIATION.md').write_text(head+table(list(ledger[0]),ledger)+'\n## Label provenance และ group-size diagnosis\n\n'+f'Authorized aggregate output: {aggart}.\n\n'+'\n'.join('- '+x['path']+': '+json.dumps({k:x[k] for k in ['row_count','platform_counts','missing_or_null_user_folder_rows','all_rows','eligible_nonempty_profile_id_rows','eligible_profile_id']},ensure_ascii=False) for x in agg)+'''

user_folder เป็น corpus grouping key ตาม code ไม่ใช่หลักฐานว่าทุกกลุ่มเป็นบุคคลจริงที่ adjudicate แล้ว. Canonical nonmissing groupsเล็ก ไม่มีdegenerateกลุ่มใหญ่;ไฟล์สะกด `nomalized_profiles.csv` รุ่นเก่ามีmissing rows14,251และnonmissing groupสูงสุด84. การรวมmissingเป็นหนึ่งidentityให้4,088,409cross-platformคู่;ไม่ตรง4,060,200 และจึงห้ามอนุมานว่าเป็นต้นเหตุที่พิสูจน์แล้ว. ถ้าexclude missing เหลือ8,185คู่ในไฟล์รุ่นเก่านี้ แสดงว่าnormalization lineageเปลี่ยนidentity keyอย่างมาก (STATIC_RISK). ตัดmissingออกเป็นข้อกำหนดG0/G2;ห้ามใช้เลขgroupเหล่านี้เป็นlabeltruth. Canonical rawชี้29,246คู่หากรวมmissingสามแถว;เมื่อexcludeได้29,243 ขณะที่29,247ในR-seriesไม่ใช่ค่าที่การคำนวณนี้สร้างได้ จึงB09ยังpartial ไม่สรุปว่าdelta4เกิดจากfilter3อย่างเดียว.

Thesis/finalGBใช้normalized_profiles_with_profile_idและbuild_ground_truth_pairsที่excludeinvalidprofile_id; R0/R1รับfrozenproduction scoresจากfinalsuiteตามV2. Notebookoriginalใช้profile_id groupingและsaved23,206positive;v2notebookใช้user_folderและsaved29,243positive. ไม่พบrun manifestเชื่อม4.06Mstatsกับmodelweightsใด จึงtrainingบนmassive-noise=UNKNOWN ไม่ใช่CONFIRMED_DEFECT. [V2R:HISTORICAL_EXPERIMENT_AUDIT.md#F05] [V2R:HISTORICAL_EXPERIMENT_AUDIT.md#F06] [V2R:HISTORICAL_EXPERIMENT_AUDIT.md#F08]

## Bibliography audit — ครบ8รายการ (PDF103/พิมพ์88)

| Thesis ref | Evidence/สถานะ | ผลต่อclaim |
|---|---|---|
| [1] Sharma/Dyreson LINKSOCIAL | [P38];Crossref10.1109/ICBK.2018.00042ยืนยันtitle/authors/year2018;upstreamREADME/pages260–267ตามV2ไม่ใช่260–269 | AbstractตามV2รายงานpairwiseaccuracy92%/multiplatform74% ไม่ใช่F1หรือtestของโครงการนี้;fullmethod/labelconstructionยังUNKNOWN |
| [2] Zafarani/Liu2013 | [P03];Crossref10.1145/2487575.2487648ยืนยันtitle/authors/KDD/2013/pages41–49 | สนับสนุนbehavioralUIL ไม่พิสูจน์ประสิทธิภาพชุดนี้ |
| [3] Halimi/Aydayตามthesis | [P01];CrossrefและV2ยืนยันว่าtitleนี้เป็นSenette/Siino/Tesconi,IEEEAccess12:171241–171268,2024,DOI10.1109/ACCESS.2024.3500374 | ผู้แต่งmisattributed;แก้record ไม่สร้างแหล่งใหม่จากชื่อที่ผิด |
| [4] Doanet al.HILDA2017 | [P50] DOI10.1145/3077257.3077268;metadataยืนยัน11authorsและpages1–6 | สนับสนุนframeworkHITL;ไม่พิสูจน์ว่ามีคนannotateในโครงการ;originalmethod/fulltextยังUNKNOWNรอบนี้ |
| [5] Liet al.HITLdata integration | [P51] DOI10.14778/3137765.3137833,PVLDB2017,2006–2017;abstractกล่าวDIMA/CDB/crowdsourcing | Literature HITLไม่ใช่annotationrecordของdataset |
| [6] Predictive lead scoring,Schäfer/Hassan/Müller | [P52] DOIที่ให้10.1007/s13369-022-06560-8resolveเป็นKavzoglu/Tekeเรื่องlandslides,AJSE47(6):7367–7385,2022 | INCORRECTattribution;EXCLUDEจากlead-scoringevidence;existenceของtitle/authorcombinationที่thesisอ้างยังUNKNOWN ไม่แทนcitationเอง |
| [7] Dataset-LinkSocial repo | [P38];GitHubupstreamREADME/APIตรวจแล้ว;license=nullและlicenseendpoint404 | repoมีจริง แต่publichostingไม่ใช่data-useauthorization;READMEมีปี2019ในข้อความอ้างกับ2018ในbibต่างกัน ต้องอ้างpublisher |
| [8] StyleLink Xu/Fung | [P53] Crossref10.1609/icwsm.v19i1.35920ยืนยัน2025,ICWSM19,2076–2088และabstract | ใช้GNNร่วมnetworkและstylometryจากgeneratedtext ไม่ใช่แค่profilebioหรือarchitectureเดียวกับrepo;ผลในpaperไม่ใช่ผลเรา |

P50–P55 เป็นreport-local literature IDsสำหรับรอบนี้ ไม่แก้matrix/bibหรือdesignของv2. Official metadata/abstractsบันทึก `_work/v3_web_metadata.json`, `_work/v3_LinkSocial_crossref.txt`, `_work/v3_HITL_crossref.txt`. Fulltextที่ยังอ่านไม่ได้ไม่ถูกยกระดับเป็นmethod verification. G0ของLinkSocialยังBLOCKED.

## Reconciliation notes

V2สรุปF06จากmodel_compareว่าGBAP.9797/F1.9333;thesis.9789/.9340ไม่ขัดกันเมื่อระบุlineage:main_reportคือoriginalsuite41featurethreshold.35 ส่วนmodel_compareเป็นbenchmarkrerunthreshold.46. V2ไม่ได้ทำraw-thesisreconciliationจึงไม่ควรนำตัวเลขสองfamilyรวมกัน. ตารางsplitoldมีsavedoutputจริงแก้pre-checkที่ตั้งข้อสงสัยว่าอาจไม่มีartifact. ตัวเลข4.06Mมีsummaryblobจริงแต่malformed;แก้ข้อสงสัยจาก“artifactไม่พบ”เป็น“execution/lineageไม่พิสูจน์”. TC-01CONFLICTเฉพาะactiveprovenanceclaim/รุ่นข้อมูล ไม่ลบประวัติnotebookที่ตรวจพบ. ไม่ระบุเจตนาผู้เขียน.
''')
print('Ledger rows',len(ledger),'status counts',dict(collections.Counter(x['Status'] for x in ledger)))
