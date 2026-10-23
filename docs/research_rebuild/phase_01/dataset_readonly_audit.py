"""Read-only dataset audit. Outputs only aggregates in this directory; never runs notebooks.
Run: .venv/bin/python docs/research_rebuild/phase_01/dataset_readonly_audit.py
Python interpreter must be 3.11. Output replacement is refused unless --refresh-new-audit.
"""
from pathlib import Path
import sys, json, hashlib, csv, ast, re, math, html, unicodedata, zipfile
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from collections import Counter
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
assert sys.version_info[:2] == (3, 11)
OUTPUTS = ['dataset_inventory.json','dataset_inventory.csv','transformation_verification.csv','dataset_audit_outputs.json','dataset_notebook_evidence.json','dataset_workbook07_evidence.json']
if '--refresh-new-audit' not in sys.argv:
    assert not any((OUT / n).exists() for n in OUTPUTS), 'Audit outputs already exist; refusing overwrite'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def save(n,v): (OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,default=lambda x:int(x) if isinstance(x,np.integer) else str(x))+'\n')
def read(n):
    d=pd.read_csv(ROOT/n,keep_default_na=False,low_memory=False)
    d.columns=[c.strip().strip('"') for c in d.columns]
    return d
FILES=['data_for_project/combined_profiles.csv','data_for_project/nomalized_profiles.csv','data_for_project/normalized_profiles.csv','data_for_project/merged_profiles.csv','data_for_project/normalized_profiles_with_profile_id.csv','data/processed/all_profiles_cleaned.csv','data/processed/all_profiles_with_blocking_keys.csv','data/processed/candidate_pairs.csv','data/processed/labeled_pairs.csv','data/processed/feature_matrix.csv','data/processed/train_dataset.csv','data/processed/val_dataset.csv','data/processed/test_dataset.csv','data/final/profiles_with_images.csv','data/final/image_features_complete.csv','train_data/ground_truth_matrix_index.csv','train_data/ground_truth_pairs.csv','data/profiles_with_enriched_text.csv']
inv=[]; dfs={}
for n in FILES:
    p=ROOT/n
    if not p.exists(): inv.append({'path':n,'exists':False});continue
    d=read(n);dfs[n]=d
    row={'path':n,'exists':True,'sha256':sha(p),'bytes':p.stat().st_size,'rows':len(d),'columns':list(d.columns),'duplicate_full_rows':int(d.duplicated().sum()),'empty_by_column':{c:int(d[c].astype(str).str.strip().eq('').sum()) for c in d.columns},'literal_nan_by_column':{c:int(d[c].astype(str).str.lower().eq('nan').sum()) for c in d.columns}}
    for c in ['platform','label']:
        if c in d:row[c+'_counts']={str(k):int(v) for k,v in d[c].value_counts().items()}
    for c in ['profile_id','profile_row_id','user_folder']:
        if c in d:row[c+'_unique']=int(d[c].nunique());row[c+'_duplicate_excess']=int(d[c].duplicated().sum());row[c+'_duplicate_rows']=int(d[c].duplicated(keep=False).sum())
    if 'user_folder' in d and 'platform' in d:
        known=d[d.user_folder.astype(str).str.strip().ne('')];group=known.groupby('user_folder').size();ct=known.groupby(['user_folder','platform']).size()
        allpos=int((group*(group-1)//2).sum());same=int((ct*(ct-1)//2).sum())
        row.update(positive_pairs_all_platform=allpos,positive_pairs_same_platform=same,positive_pairs_cross_platform=allpos-same,repeated_entity_platform_groups=int((ct>1).sum()),entity_size_histogram={str(k):int(v) for k,v in group.value_counts().sort_index().items()},cross_platform_universe=sum(int(a)*int(b) for i,a in enumerate(d.platform.value_counts()) for b in d.platform.value_counts().iloc[i+1:]))
    if {'profile_id_a','profile_id_b'}<=set(d):
        keys=[tuple(sorted((str(a),str(b)))) for a,b in zip(d.profile_id_a,d.profile_id_b)]
        row['duplicate_unordered_pair_excess']=len(keys)-len(set(keys));row['self_pairs']=int(d.profile_id_a.eq(d.profile_id_b).sum())
        if 'label' in d:row['conflicting_pair_labels']=int(pd.DataFrame({'key':keys,'label':d.label}).groupby('key').label.nunique().gt(1).sum())
    inv.append(row)
save('dataset_inventory.json',inv)
with (OUT/'dataset_inventory.csv').open('w',newline='') as f:
    fields=sorted(set().union(*(r.keys() for r in inv)));w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in inv)
# Only source cells, never saved notebook outputs (which can contain personal rows).
nb={}
for p in (ROOT/'thesis_rebuild/00_notebook_history').rglob('*.ipynb'):
    if any(x in p.name for x in ['clean','features','label','blocking','ground_truth','preprocessing']):
        obj=json.loads(p.read_text());nb[str(p.relative_to(ROOT))]={'sha256':sha(p),'code_cells':[{'cell_1based':i+1,'source_sha256':hashlib.sha256(''.join(c.get('source',[])).encode()).hexdigest(),'source':''.join(c.get('source',[]))} for i,c in enumerate(obj['cells']) if c['cell_type']=='code']}
save('dataset_notebook_evidence.json',nb)
checks=[]
def check(name,n,m,source,status=None,detail=''):
    checks.append(dict(transformation=name,checked_rows=n,mismatch_rows=m,status=status or ('PASS' if m==0 else 'FAIL'),source=source,detail=detail))
raw=dfs[FILES[0]];blocked=dfs['data/processed/all_profiles_with_blocking_keys.csv'];clean=dfs['data/processed/all_profiles_cleaned.csv'];features=dfs['data/processed/feature_matrix.csv'];labels=dfs['data/processed/labeled_pairs.csv'];merged=dfs['data_for_project/merged_profiles.csv']
for c in ['source_folder','user_folder','platform','outputProfileName','pictureURL']:
    check('raw→blocking row alignment '+c,len(raw),int(raw[c].astype(str).ne(blocked[c].astype(str)).sum()),'thesis_rebuild/build_dataset_excel.py:25-29')
check('24729 cleaned→36807 normalized',0,'','docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md:100-105','UNPROVEN','Different row count/schema; no proven producer chain; not presumed subset.')
# Controlled execution of function definitions only, selected explicit AST nodes.
ns={'pd':pd,'np':np,'re':re,'math':math,'html':html,'unicodedata':unicodedata,'ast':ast,'urlparse':urlparse}
def funcs(path,cell):
    source=next(c['source'] for c in nb[path]['code_cells'] if c['cell_1based']==cell)
    tree=ast.parse(source);defs=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
    exec(compile(ast.Module(body=defs,type_ignores=[]),path+':cell'+str(cell),'exec'),ns)
first='thesis_rebuild/00_notebook_history/original/01_data_clean_first.ipynb';later='thesis_rebuild/00_notebook_history/original/01_data_clean_later.ipynb'
funcs(first,15)
for src,target,fn in [('userName','userName_clean','normalize_text'),('fullName','fullName_clean','normalize_text'),('bio','bio_clean','clean_bio'),('location','location_clean','normalize_location'),('externalUrl','externalUrl_clean','normalize_url')]:
    pred=blocked[src].map(ns[fn]);check('first-clean rules on blocking snapshot '+target,len(blocked),int(pred.astype(str).ne(blocked[target].astype(str)).sum()),first+':cell15')
for cell in [30,35,46,51]:funcs(later,cell)
normalized=dfs['data_for_project/nomalized_profiles.csv']
for src,fn in [('userName','clean_username'),('fullName','clean_fullname')]:
    pred=raw[src].map(ns[fn]);check('raw→nomalized '+src,len(raw),int(pred.astype(str).ne(normalized[src].astype(str)).sum()),later+':cell'+('30' if src=='userName' else '35'))
loc=raw.location.map(ns['clean_location_full'])
for field in ['location','location_type','location_valid','latitude','longitude']:
    key='location_clean' if field=='location' else field
    if field in normalized:
        pred=loc.map(lambda x:x[key]);act=normalized[field]
        if field in ['latitude','longitude','location_valid']:
            m=int((~np.isclose(pd.to_numeric(pred,errors='coerce'),pd.to_numeric(act,errors='coerce'),equal_nan=True)).sum())
        else:m=int(pred.astype(str).ne(act.astype(str)).sum())
        check('raw→nomalized '+field,len(raw),m,later+':cell46')
urls=raw.externalUrl.map(ns['clean_external_url_field'])
for field,ix,squash in [('externalUrl_clean_list',0,False),('external_domain_list',1,False),('url_count',2,False),('externalUrl_clean',0,True),('external_domain',1,True)]:
    if field in normalized:
        pred=urls.map(lambda x:ns['squash_single_or_list'](x[ix]) if squash else x[ix]);check('raw→nomalized '+field,len(raw),int(pred.astype(str).ne(normalized[field].astype(str)).sum()),later+':cells51-52')
# Dependencies must really exist; no identity substitute for ftfy/emoji.
try:
    import emoji
    from ftfy import fix_text
    ns.update(emoji=emoji,fix_text=fix_text,URL_RE=re.compile(r'https?://\S+|www\.\S+',re.I),MENTION_RE=re.compile(r'@(\w+)'),HASHTAG_RE=re.compile(r'#(\w+)'),NOISY_SEP_RE=re.compile(r'[|•·►▸▹▻>>>★☆✦✧~≡]{1,}'),MULTISPACE_RE=re.compile(r'\s+'))
    funcs(later,39)
    pred=raw.bio.map(ns['clean_bio']);check('raw→nomalized bio advanced',len(raw),int(pred.astype(str).ne(normalized.bio.astype(str)).sum()),later+':cell39',detail='Current installed emoji/ftfy, not proven historical package versions')
    for field,fn in [('bio_urls','extract_urls'),('bio_mentions','extract_mentions')]:
        pred=raw.bio.map(lambda x:' | '.join(ns['clean_single_url'](u) if field=='bio_urls' else u.lower() for u in ns[fn](ns['safe_str'](x))))
        check('raw→nomalized '+field,len(raw),int(pred.ne(normalized[field].astype(str)).sum()),later+':cell41')
        countfield='bio_url_count' if field=='bio_urls' else 'bio_mentions_count'
        count=pred.map(lambda x:len(x.split(' | ')) if x else 0)
        check('raw→nomalized '+countfield,len(raw),int(count.astype(str).ne(normalized[countfield].astype(str)).sum()),later+':cell41')
except ImportError as e:check('advanced bio',0,'',later+':cell39','NOT_EXECUTED',str(e))
# Legacy feature replay: default pandas NA semantics and first/last duplicate lookup exactly as Stage9v2.
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
p=pd.read_csv(ROOT/'data/processed/all_profiles_with_blocking_keys.csv',low_memory=False)
firstlookup=p.drop_duplicates('profile_id',keep='first').set_index('profile_id');lastlookup={k:i for i,k in enumerate(p.profile_id)}
source='thesis_rebuild/00_notebook_history/v2/stage9_features_v2.ipynb'
A=features.profile_id_a.map(lambda k:k in firstlookup.index);B=features.profile_id_b.map(lambda k:k in firstlookup.index);ok=A&B
fcounts=Counter(blocked.profile_id.astype(str)); mapping={}
for side in ['a','b']:
    ids=features['profile_id_'+side].astype(str);mapping[side]=dict(Counter('NO_PROFILE' if fcounts[x]==0 else 'DUPLICATE_ID' if fcounts[x]>1 else 'OK' for x in ids))
for col,prefix in [('userName_clean','username'),('fullName_clean','fullname'),('bio_clean','bio')]:
    av=features.profile_id_a.map(firstlookup[col]).map(lambda v:str(v or ''));bv=features.profile_id_b.map(firstlookup[col]).map(lambda v:str(v or ''))
    for method,fn in [('jaro',fuzz.WRatio),('token_sort',fuzz.token_sort_ratio),('levenshtein',fuzz.ratio)]:
        vals=np.array([fn(a.strip(),b.strip())/100 if a.strip() and b.strip() and valid else 0 for a,b,valid in zip(av,bv,ok)])
        check('Stage9v2 replay '+prefix+'_'+method,len(features),int((~np.isclose(vals,features[prefix+'_'+method],rtol=1e-6,atol=1e-7)).sum()),source+':cell4',detail='Replay against 36807 blocking snapshot; configured cleaned input is a different 24729-row snapshot')
    vals=np.array([float(not a.strip() and not b.strip()) if valid else 1 for a,b,valid in zip(av,bv,ok)])
    check('Stage9v2 replay '+prefix+'_both_empty',len(features),int((vals!=features[prefix+'_both_empty']).sum()),source+':cell4')
for field,outfield in [('externalUrl_clean','url_exact_match'),('url_domain','url_domain_match')]:
    av=features.profile_id_a.map(firstlookup[field]).map(lambda v:str(v or ''));bv=features.profile_id_b.map(firstlookup[field]).map(lambda v:str(v or ''))
    vals=np.array([float(bool(a and b and a==b)) if valid else 0 for a,b,valid in zip(av,bv,ok)])
    check('Stage9v2 replay '+outfield,len(features),int((vals!=features[outfield]).sum()),source+':cell8')
av=features.profile_id_a.map(firstlookup.platform);bv=features.profile_id_b.map(firstlookup.platform)
check('Stage9v2 replay same_platform',len(features),int(((av.eq(bv)&ok).astype(float)!=features.same_platform).sum()),source+':cell10')
av=features.profile_id_a.map(firstlookup.location_clean).map(lambda v:str(v or ''));bv=features.profile_id_b.map(firstlookup.location_clean).map(lambda v:str(v or ''))
vals=np.array([fuzz.WRatio(a.strip(),b.strip())/100 if a.strip() and b.strip() and valid else 0 for a,b,valid in zip(av,bv,ok)])
check('Stage9v2 replay location_sim',len(features),int((~np.isclose(vals,features.location_sim,rtol=1e-6,atol=1e-7)).sum()),source+':cell10')
tf=TfidfVectorizer(max_features=5000,stop_words='english',min_df=2);mat=tf.fit_transform(p.bio_clean.fillna(''))
ia=features.profile_id_a.map(lastlookup);ib=features.profile_id_b.map(lastlookup);valid=ia.notna()&ib.notna();v=np.zeros(len(features));v[valid]=np.asarray(mat[ia[valid].astype(int)].multiply(mat[ib[valid].astype(int)]).sum(axis=1)).ravel()
check('Stage9v2 replay bio_tfidf_cosine',len(features),int((~np.isclose(v,features.bio_tfidf_cosine,rtol=1e-5,atol=1e-7)).sum()),source+':cell6',detail='Fit on all 36807 blocking bios; no historical vocabulary artifact loaded')
for c in ['profile_id_a','profile_id_b','entity_id_a','label']:
    check('labeled→feature ordered '+c,len(labels),int(labels[c].astype(str).ne(features[c].astype(str)).sum()),source+':cells4,12')
# Ground truth sparse matrix without fitting or prediction.
from scipy.sparse import load_npz
npz=ROOT/'train_data/ground_truth_matrix.npz';gt={}
if npz.exists():
    matrix=load_npz(npz);ix=dfs['train_data/ground_truth_matrix_index.csv'];r,c=matrix.nonzero();folders=merged.user_folder.astype(str).to_numpy();platforms=merged.platform.astype(str).to_numpy()
    gt={'path':str(npz.relative_to(ROOT)),'sha256':sha(npz),'shape':list(matrix.shape),'nnz':matrix.nnz,'diagonal_nonzero':int(np.count_nonzero(matrix.diagonal())),'asymmetry_nnz':int((matrix!=matrix.T).nnz),'nonunit_values':int(np.count_nonzero(matrix.data!=1)),'off_entity_nonzeros':int(np.count_nonzero(folders[r]!=folders[c])),'cross_platform_upper_positive':int(np.count_nonzero((r<c)&(platforms[r]!=platforms[c]))),'same_platform_upper_positive':int(np.count_nonzero((r<c)&(platforms[r]==platforms[c])))}
    for field in ['userName','user_folder']:check('matrix index→merged '+field,len(merged),int(ix[field].astype(str).ne(merged[field].astype(str)).sum()),'thesis_rebuild/00_notebook_history/extras/build_ground_truth_matrix.ipynb:cells4,14')
# Pair label verification ONLY on unambiguous endpoints; unknown/duplicates never treated negative.
labelaudit={}
for popname,pop in [('blocking36807',blocked),('cleaned24729',clean)]:
    counts=pop.profile_id.value_counts();uniq=pop[pop.profile_id.map(counts).eq(1)].set_index('profile_id');ea=features.profile_id_a.map(uniq.user_folder);eb=features.profile_id_b.map(uniq.user_folder);valid=ea.notna()&eb.notna()&ea.ne('')&eb.ne('');truth=ea.eq(eb).astype(int)
    labelaudit[popname]={'resolvable_pairs':int(valid.sum()),'unresolved_pairs':int((~valid).sum()),'label_mismatches_resolvable':int((truth[valid]!=features.label[valid]).sum()),'entity_id_a_mismatches_resolvable':int(ea[valid].astype(str).ne(features.entity_id_a[valid].astype(str)).sum())}
# Workbook streaming ZIP/XML. No personal values leave memory.
book=ROOT/'thesis_rebuild/07_dataset_raw_to_features.xlsx';N='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}';R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}';wb={'path':str(book.relative_to(ROOT)),'sha256':sha(book),'sheets':[]}
with zipfile.ZipFile(book) as z:
    ss=[]
    if 'xl/sharedStrings.xml' in z.namelist():ss=[''.join(t.itertext()) for t in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(N+'si')]
    rel={e.attrib['Id']:e.attrib['Target'] for e in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    for sh in ET.fromstring(z.read('xl/workbook.xml')).find(N+'sheets'):
        target=rel[sh.attrib[R+'id']];member=target.lstrip('/') if target.startswith('/') else 'xl/'+target
        header=None;nrows=0;status={};formulas=0;compare=0;mismatch=0
        name=sh.attrib['name'];frame_path={'01_RAW_PROFILES':FILES[0],'02_CLEAN_PROFILES':'data/processed/all_profiles_with_blocking_keys.csv','05_IMAGE_PROFILES':'data/final/profiles_with_images.csv','06_IMAGE_FEATURES':'data/final/image_features_complete.csv'}.get(name)
        frame=pd.read_csv(ROOT/frame_path,low_memory=False) if frame_path else None
        if frame is not None: frame.columns=[c.strip().strip('"') for c in frame.columns]
        with z.open(member) as f:
            for event,e in ET.iterparse(f,events=('end',)):
                if e.tag!=N+'row':continue
                cells={}
                for cell in e.findall(N+'c'):
                    ref=cell.attrib['r'];letters=re.match('[A-Z]+',ref).group();idx=0
                    for ch in letters:idx=idx*26+ord(ch)-64
                    val=cell.find(N+'v');typ=cell.attrib.get('t');text=val.text if val is not None else ''
                    if typ=='inlineStr':text=''.join(cell.find(N+'is').itertext())
                    elif typ=='s':text=ss[int(text)]
                    if cell.find(N+'f') is not None:formulas+=1
                    cells[idx-1]=text or ''
                if header is None:header=[cells.get(i,'') for i in range(max(cells,default=-1)+1)]
                else:
                    nrows+=1
                    if name=='03_PAIRS':
                        for side in ['a','b']:
                            k='match_status_'+side;v=cells.get(header.index(k),'');status.setdefault(k,Counter())[v]+=1
                        expected=features.iloc[nrows-1]
                        for field in ['profile_id_a','profile_id_b','entity_id_a','label',*features.columns[4:]]:
                            v=cells.get(header.index(field),'');a=expected[field];compare+=1
                            try:equal=math.isclose(float(v),float(a),rel_tol=1e-9,abs_tol=1e-12)
                            except (ValueError,TypeError):equal=str(v)==str(a)
                            mismatch+=not equal
                    elif frame is not None and nrows<=len(frame):
                        expected=frame.iloc[nrows-1]
                        for field in frame.columns:
                            v=cells.get(header.index(field),'');a=expected[field];compare+=1
                            if pd.isna(a): a=''
                            try:equal=math.isclose(float(v),float(a),rel_tol=1e-9,abs_tol=1e-12)
                            except (ValueError,TypeError):equal=str(v)==str(a) or (v in ['0','1'] and isinstance(a,(bool,np.bool_)) and int(v)==int(a))
                            mismatch+=not equal
                e.clear()
        wb['sheets'].append({'name':name,'data_rows':nrows,'columns':len(header),'headers':header,'formulas':formulas,'match_status_counts':{k:dict(v) for k,v in status.items()},'compared_source_cells':compare,'mismatched_source_cells':mismatch})
save('dataset_workbook07_evidence.json',wb)
with (OUT/'transformation_verification.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)
result={'python':sys.version,'audit_script_sha256':sha(Path(__file__)),'ground_truth':gt,'workbook_endpoint_mapping_recomputed':mapping,'label_verification':labelaudit,'transformation_status_counts':dict(Counter(x['status'] for x in checks)),'privacy':'No personal rows, endpoint IDs, entity folder values, or predictions exported. Notebook source only; no notebook execution. No fitting except deterministic TFIDF replay for transformation audit; no training/calibration/optimization.'}
save('dataset_audit_outputs.json',result)
print(json.dumps({'inventory_files':len(inv),'checks':len(checks),'statuses':result['transformation_status_counts'],'ground_truth':gt,'mapping':mapping,'label_verification':labelaudit,'workbook_sheets':[{k:v for k,v in x.items() if k in ['name','data_rows','columns','mismatched_source_cells']} for x in wb['sheets']]},ensure_ascii=False,indent=2))
