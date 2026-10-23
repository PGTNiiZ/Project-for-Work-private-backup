"""Targeted reconciliation of workbook image booleans and present profile contracts.
Reads only, exports aggregates, appends checks in new audit table; no personal examples.
"""
from pathlib import Path
import json,csv,re,zipfile,ast,math,unicodedata
from collections import Counter
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
res={};checks=[]
def check(n,N,m,s,detail=''):
 checks.append(dict(transformation=n,checked_rows=N,mismatch_rows=m,status='PASS' if m==0 else 'FAIL',source=s,detail=detail))
b=pd.read_csv(ROOT/'data/processed/all_profiles_with_blocking_keys.csv',low_memory=False)
for col,src in [('name_prefix3','userName_clean'),('fullname_prefix3','fullName_clean')]:
 pred=b[src].astype(str).str[:3].str.strip();check('stored blocking key '+col,len(b),int(pred.astype(str).ne(b[col].fillna('').astype(str)).sum()),'thesis_rebuild/00_notebook_history/original/07_blocking.ipynb:cell5')
pred=b.externalUrl_clean.map(lambda x:x.split('/')[0].strip() if isinstance(x,str) and x.strip() else '')
check('stored blocking url_domain',len(b),int(pred.ne(b.url_domain.fillna('').astype(str)).sum()),'thesis_rebuild/00_notebook_history/original/07_blocking.ipynb:cell5')
# Original-clean CSV reconstruction with prepare source pure definitions, not loader execution.
p=ROOT/'src/identity_resolution/stages/prepare.py';ns={'pd':pd,'re':re};tree=ast.parse(p.read_text());defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['remove_emojis','normalize_text']];exec(compile(ast.Module(body=defs,type_ignores=[]),str(p),'exec'),ns)
c=pd.read_csv(ROOT/'data/processed/all_profiles_cleaned.csv',low_memory=False)
for target,src in [('userName_clean','userName'),('fullName_clean','fullName'),('profile_id','outputProfileName')]:
 pred=c[src].map(ns['normalize_text']);check('prepare pure rule on cleaned24729 '+target,len(c),int(pred.ne(c[target].fillna('').astype(str)).sum()),'src/identity_resolution/stages/prepare.py:98-116,149-155')
pred=c.bio.map(lambda x:ns['remove_emojis'](str(x)) if pd.notna(x) else '')
check('prepare pure rule on cleaned24729 bio_clean',len(c),int(pred.ne(c.bio_clean.fillna('').astype(str)).sum()),'src/identity_resolution/stages/prepare.py:151')
# Missing coordinates: check a documented None becomes 0 fill in persisted snapshot.
n=pd.read_csv(ROOT/'data_for_project/nomalized_profiles.csv',keep_default_na=False,low_memory=False)
res['coordinate_zero_fill']={field:{'zero_rows':int(n[field].astype(str).isin(['0','0.0']).sum()),'empty_rows':int(n[field].astype(str).eq('').sum())} for field in ['latitude','longitude']}
# Targeted image worksheet, no full workbook tree. String vs boolean is lossless compared canonically.
book=ROOT/'thesis_rebuild/07_dataset_raw_to_features.xlsx';N='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}';R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}';img=pd.read_csv(ROOT/'data/final/profiles_with_images.csv',low_memory=False);byfield=Counter();boolonly=Counter();rows=0;compared=0
with zipfile.ZipFile(book) as z:
 rel={e.attrib['Id']:e.attrib['Target'] for e in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))};sh=next(s for s in ET.fromstring(z.read('xl/workbook.xml')).find(N+'sheets') if s.attrib['name']=='05_IMAGE_PROFILES');t=rel[sh.attrib[R+'id']];member=t.lstrip('/') if t.startswith('/') else 'xl/'+t;header=None
 with z.open(member) as f:
  for _,e in ET.iterparse(f,events=['end']):
   if e.tag!=N+'row':continue
   vals={}
   for cell in e.findall(N+'c'):
    k=0
    for ch in re.match('[A-Z]+',cell.attrib['r']).group():k=k*26+ord(ch)-64
    v=cell.find(N+'v');typ=cell.attrib.get('t');text=v.text if v is not None else ''
    if typ=='inlineStr':text=''.join(cell.find(N+'is').itertext())
    vals[k-1]=text or ''
   if header is None:header=[vals[i] for i in range(len(vals))]
   else:
    expected=img.iloc[rows];rows+=1
    for field in img:
     a=expected[field];a='' if pd.isna(a) else a;v=vals.get(header.index(field),'');v=re.sub(r'_x([0-9A-Fa-f]{4})_',lambda m:chr(int(m.group(1),16)),v);compared+=1
     try:equal=math.isclose(float(a),float(v),rel_tol=1e-9,abs_tol=1e-12)
     except (ValueError,TypeError):equal=str(a)==str(v) or (v in ['0','1'] and isinstance(a,(bool,np.bool_)) and int(v)==int(a))
     if not equal:
      if str(a) in ['True','False'] and v in ['0','1'] and (str(a)=='True')==(v=='1'):boolonly[field]+=1
      else:byfield[field]+=1
   e.clear()
res['workbook_image_reconciliation']={'rows':rows,'compared_cells':compared,'boolean_serialization_equivalent_differences':dict(boolonly),'remaining_mismatches_by_column':dict(byfield),'remaining_mismatched_cells':sum(byfield.values())}
check('workbook image cells semantic comparison',compared,sum(byfield.values()),'thesis_rebuild/build_dataset_excel.py:63-75,155-156','String True/False vs Excel boolean 1/0 treated serialization-equivalent')
# No complete rebuild execution; only selected producer rules have been exercised.
res['checks']=checks
p=OUT/'dataset_reconciliation_outputs.json';p.write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
with (OUT/'transformation_verification.csv').open(newline='') as f: prior=list(csv.DictReader(f))
names={x['transformation'] for x in checks};prior=[x for x in prior if x['transformation'] not in names]
with (OUT/'transformation_verification.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(prior+checks)
print(json.dumps(res,ensure_ascii=False,indent=2))
