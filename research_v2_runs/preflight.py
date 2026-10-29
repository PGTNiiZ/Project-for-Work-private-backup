"""Canonical local adapter. Only aggregates leave data_derived/."""
from pathlib import Path
import collections
import datetime as dt
import hashlib
import inspect
import itertools
import json
import re
import unicodedata
import numpy as np
import pandas as pd
from integrity import sha256, require_committed

FIELDS={'username':'userName','fullname':'fullName','bio':'bio','location':'location','links':'externalUrl_clean','domain':'external_domain','platform':'platform'}

def norm(value):
    s=unicodedata.normalize('NFKC',str(value)).strip().lower()
    return '' if s in {'','nan','none','null','<na>'} else re.sub(r'\s+',' ',s)

def ground_truth(frame):
    pairs=[]
    platforms=frame.platform.to_numpy()
    for ix in frame.groupby('entity',sort=False).indices.values():
        for a,b in itertools.combinations(ix,2):
            if platforms[a]!=platforms[b]: pairs.append((min(a,b),max(a,b)))
    return np.array(pairs,dtype=np.int32).reshape(-1,2)

def prepare_frame(raw):
    # Identity tokens are identifiers, not text features: preserve exact case/bytes.
    keys=raw['user_folder'].astype(str)
    valid=keys.map(norm).ne('') & pd.to_numeric(raw['profile_id'],errors='coerce').notna()
    frame=pd.DataFrame({k:raw.loc[valid,v].map(norm).to_numpy() for k,v in FIELDS.items()})
    frame['entity']=pd.factorize(keys[valid],sort=True)[0].astype(np.int32)
    counts=frame.groupby('entity').size()
    # A canonical group bigger than ten is not automatically an identity.
    if int(counts.max())>10:
        raise ValueError('degenerate canonical label groups; construction stopped')
    gt=ground_truth(frame)
    summary={'input_rows':int(len(raw)),'eligible_rows':int(len(frame)),'quarantined_rows':int((~valid).sum()),'missing_key_rows':int(keys.eq('').sum()),'distinct_entities':int(frame.entity.nunique()),'group_size_histogram':{str(k):int(v) for k,v in counts.value_counts().sort_index().items()},'max_group_size':int(counts.max()),'cross_platform_positive_pairs':int(len(gt)),'platform_counts':{str(k):int(v) for k,v in frame.platform.value_counts().items()},'million_positive_guard':bool(len(gt)<1000000)}
    if not summary['million_positive_guard']:
        raise ValueError('million-positive guard failed; canonical construction stopped')
    return frame,summary

def split_frame(frame,seed=42):
    frame=frame.copy()
    n=int(frame.entity.max())+1
    parent=np.arange(n)
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]
            x=parent[x]
        return int(x)
    dup_cross=0
    subset=frame[frame.username.str.len().ge(3)]
    for _,g in subset.groupby(['platform','username'],sort=False):
        entities=g.entity.unique()
        if len(entities)>1:
            dup_cross+=1
            a=find(int(entities[0]))
            for e in entities[1:]: parent[find(int(e))]=a
    frame['component']=np.array([find(int(e)) for e in frame.entity],dtype=np.int32)
    strata=collections.defaultdict(list)
    for component,g in frame.groupby('component',sort=True):
        sig=tuple(sorted((str(k),int(v)) for k,v in g.platform.value_counts().items()))
        strata[sig].append((int(component),int(g.entity.nunique()),int(len(g))))
    rng=np.random.default_rng(seed)
    entity_counts=np.zeros(5,dtype=int)
    profile_counts=np.zeros(5,dtype=int)
    assignments={}
    for sig in sorted(strata,key=str):
        values=strata[sig]
        rng.shuffle(values)
        for component,ne,np_ in values:
            fold=min(range(5),key=lambda f:(entity_counts[f],profile_counts[f],f))
            assignments[component]=fold
            entity_counts[fold]+=ne
            profile_counts[fold]+=np_
    frame['fold']=frame.component.map(assignments).astype(np.int8)
    assert int(frame.groupby('entity').fold.nunique().max())==1
    assert int(frame.groupby('component').fold.nunique().max())==1
    summary={'entity_overlap':0,'component_overlap':0,'same_platform_username_cross_identity_components':dup_cross,'folds':[{'fold':i,'entities':int(frame.loc[frame.fold.eq(i),'entity'].nunique()),'profiles':int(frame.fold.eq(i).sum()),'ground_truth_pairs':int(len(ground_truth(frame[frame.fold.eq(i)].reset_index(drop=True))))} for i in range(5)],'routing':'both endpoints same fold; no negative edges across folds'}
    return frame,summary

def route_pairs(frame,pairs):
    pairs=np.asarray(pairs,dtype=np.int32).reshape(-1,2)
    if len(pairs) and (np.any(pairs[:,0]>=pairs[:,1]) or len(np.unique(pairs,axis=0))!=len(pairs)):
        raise ValueError('pairs must be canonical unique undirected keys')
    roles=frame.fold.to_numpy()
    keep=roles[pairs[:,0]]==roles[pairs[:,1]]
    return pairs[keep],int((~keep).sum())

def run(root):
    root=Path(root)
    protocol=json.loads((root/'protocol.json').read_text())
    require_committed(root/'PREREGISTRATION_FREEZE.md')
    raw_path=root.parent/protocol['raw_input']
    if sha256(raw_path)!=protocol['raw_input_sha256']:
        raise ValueError('raw input changed before preflight')
    raw=pd.read_csv(raw_path,dtype=str,keep_default_na=False,low_memory=False)
    frame,sanity=prepare_frame(raw)
    frame,leak=split_frame(frame,protocol['split_seed'])
    derived=root/'data_derived'
    for f in range(5):
        scope=frame[frame.fold.eq(f)].reset_index(drop=True)
        scope.to_parquet(derived/(f'dev_fold_{f}.parquet' if f<4 else 'sealed_test.parquet'),index=False)
    manifest=frame[['entity','component','fold']]
    manifest.to_parquet(derived/'split_manifest.parquet',index=False)
    split_hash=sha256(derived/'split_manifest.parquet')
    public={'split_sha256':split_hash,'raw_sha256':protocol['raw_input_sha256'],'sealed_test_sha256':sha256(derived/'sealed_test.parquet'),'folds':leak['folds'],'entity_overlap':0,'component_overlap':0,'test_is_exploratory':True}
    (root/'manifests/split_summary.json').write_text(json.dumps(public,indent=2)+'\n')
    (root/'metrics/label_sanity.json').write_text(json.dumps(sanity,indent=2)+'\n')
    (root/'metrics/leakage_audit.json').write_text(json.dumps(leak,indent=2)+'\n')
    # Dataset profile details below are development-only: no test attributes inspected.
    dev=frame[frame.fold.ne(4)]
    profile={'scope':'development folds only','attributes':{},'language_detection':'Unicode script proxy, not validated language identification'}
    for field in ['username','fullname','bio','location','links']:
        lengths=dev[field].str.len()
        profile['attributes'][field]={'missing_rate':float(lengths.eq(0).mean()),'median_length':float(lengths.median()),'non_ascii_rows':int(dev[field].map(lambda s:any(ord(c)>127 for c in s)).sum()),'thai_script_rows':int(dev[field].str.contains('[\u0e00-\u0e7f]',regex=True).sum())}
    (root/'metrics/dataset_profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    (root/'LABEL_SANITY.md').write_text('# Label Sanity — EXPLORATORY\n\nSource: protocol.json raw_input + raw SHA-256. Code: preflight.py prepare_frame/ground_truth.\n\n'+json.dumps(sanity,ensure_ascii=False,indent=2)+'\n\nใช้ canonical normalized source เท่านั้น; ไม่ใช้ nomalized_profiles.csv ที่มี degenerate null grouping ในหลักฐาน Round3. ไม่ได้พิสูจน์ว่า historical models ทุกตัวใช้ labels ชุดเสีย จึงยังไม่เรียก historical impact ว่า CONFIRMED_DEFECT. G0 เป็น researcher declaration ไม่ใช่การรับรอง identity ภายนอก.\n')
    (root/'LEAKAGE_AUDIT.md').write_text('# Leakage Audit — EXPLORATORY\n\n'+json.dumps(leak,ensure_ascii=False,indent=2)+f'\n\nSplit manifest SHA-256: {split_hash}\nIdentity IDs/row mappings อยู่เฉพาะ data_derived ที่ gitignore; ไม่มี identifiers ในรายงาน. Primary features ไม่ใช้ original profile_id, user_folder หรือ historical predecessor scores. Same-account aliases ใช้ connected component เฉพาะ split grouping ไม่แก้ ground truth.\n')
    (root/'D0_REPORT.md').write_text('# D0 — EXPLORATORY\n\nD0-1: DECLARED provenance; ไม่มี independent dual annotation.\nD0-2: aggregate schema/coverage ใน metrics/dataset_profile.json (development only).\nD0-3: NOT RUN — ไม่มี annotation capacity; ใช้ E7-6 S1/S2; ไม่แต่ง hidden-positive rate.\nD0-4: identity/component overlap = 0; split hashใน manifests/split_summary.json. Reused historical population ไม่ใช่ pristine holdout.\n\n'+json.dumps(profile,ensure_ascii=False,indent=2)+'\n')
    with (root/'aggregate_queries.log').open('a') as log:
        log.write(dt.datetime.now(dt.timezone.utc).isoformat()+'\n'+inspect.getsource(prepare_frame)+'\n'+inspect.getsource(ground_truth)+'\n'+inspect.getsource(split_frame)+'\nrun(root): raw canonical loaded locally; output only above aggregate dictionaries; full code SHA256='+sha256(__file__)+'\n')
    print(json.dumps({'preflight':'DONE','eligible_profiles':sanity['eligible_rows'],'positive_pairs':sanity['cross_platform_positive_pairs'],'split_hash':split_hash,'entity_overlap':0,'quarantined':sanity['quarantined_rows']}),flush=True)
    return public

if __name__=='__main__':
    run(Path(__file__).resolve().parent)
