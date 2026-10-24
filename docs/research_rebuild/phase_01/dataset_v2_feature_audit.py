"""Independent aggregate-only replay of all persisted corrected V2 GB-17 values.
No fitting, scoring, labels, training, download or upstream writes.
"""
from pathlib import Path
import sys,json,hashlib,csv,time
import numpy as np
import pandas as pd
from rapidfuzz import fuzz
from rapidfuzz.distance import Jaro,JaroWinkler,Levenshtein
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
assert sys.version_info[:2]==(3,11)
sys.path.insert(0,str(ROOT))
from experiments.icsec_final.authoritative_run_v2.features import _normalize,FEATURE17_COLUMNS
p=ROOT/'experiments/icsec_final/authoritative_run_v2/features/gb17.parquet';d=pd.read_parquet(p);prof=pd.read_csv(ROOT/'data_for_project/normalized_profiles_with_profile_id.csv',keep_default_na=False,low_memory=False)
columns=['userName','fullName','bio','location','platform'];lookup={int(row.profile_row_id):tuple(_normalize(getattr(row,c)) for c in columns) for row in prof.itertuples(index=False)}
mismatch=np.zeros(17,dtype=np.int64);maxdiff=np.zeros(17);bad=0;t=time.monotonic()
def sim(a,b):return float(Jaro.similarity(a,b)) if a and b else 0.
def lev(a,b):return float(1-Levenshtein.distance(a,b)/max(len(a),len(b))) if a and b else 0.
def token(a,b):return float(fuzz.token_sort_ratio(a,b)/100) if a and b else 0.
for start in range(0,len(d),100000):
 part=d.iloc[start:start+100000];expected=part[FEATURE17_COLUMNS].to_numpy(dtype=np.float64);got=np.zeros_like(expected)
 for i,(a,b) in enumerate(zip(part.profile_row_id_a,part.profile_row_id_b)):
  if int(a) not in lookup or int(b) not in lookup:bad+=1;continue
  ua,fa,ba,la,pa=lookup[int(a)];ub,fb,bb,lb,pb=lookup[int(b)];sa=set(ba.split());sb=set(bb.split());ml=max(len(ba),len(bb));mu=max(len(ua),len(ub));wa=len(fa.split());wb=len(fb.split());mw=max(wa,wb)
  name=max((JaroWinkler.similarity(x,y) for x in [ua,fa] for y in [ub,fb] if x and y),default=0.)
  got[i]=[sim(ua,ub),lev(ua,ub),token(ua,ub),sim(fa,fb),lev(fa,fb),token(fa,fb),name,len(sa&sb)/len(sa|sb) if sa or sb else 0.,min(len(ba),len(bb))/ml if ml else 0.,float(bool(ba and bb)),sim(la,lb),float(bool(la and la==lb)),float(bool(la and lb)),float(bool(pa and pa==pb)),abs(len(ua)-len(ub))/mu if mu else 0.,abs(wa-wb)/mw if mw else 0.,float(len(ua)>=3 and len(ub)>=3 and ua[:3]==ub[:3])]
 # Producer saves float32. Compare after identical storage precision.
 got=got.astype(np.float32).astype(np.float64);diff=np.abs(got-expected);mismatch+=(~np.isclose(got,expected,rtol=1e-6,atol=1e-7)).sum(axis=0);maxdiff=np.maximum(maxdiff,diff.max(axis=0))
out={'artifact_path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rows':len(d),'columns':list(d),'source':'experiments/icsec_final/authoritative_run_v2/features.py:22-113','missing_endpoint_rows':bad,'elapsed_seconds':time.monotonic()-t,'features':[{'name':n,'checked_rows':len(d),'mismatch_rows':int(m),'max_absolute_difference':float(md),'status':'PASS' if m==0 else 'FAIL'} for n,m,md in zip(FEATURE17_COLUMNS,mismatch,maxdiff)],'privacy':'No labels or per-pair values exported. Existing features read and pure formulas replayed.'}
op=OUT/'dataset_v2_feature_verification.json';assert not op.exists();op.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
checks=[dict(transformation='V2 corrected feature replay '+x['name'],checked_rows=x['checked_rows'],mismatch_rows=x['mismatch_rows'],status=x['status'],source=out['source'],detail='All persisted model-scored pairs; stored float32 precision; no learned predecessor score') for x in out['features']]
with (OUT/'transformation_verification.csv').open('a',newline='') as f:csv.DictWriter(f,fieldnames=list(checks[0])).writerows(checks)
print(json.dumps(out,ensure_ascii=False,indent=2))
