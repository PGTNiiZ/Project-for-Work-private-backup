"""Strict development-only boundary and append-only post-hoc records."""
from contextlib import contextmanager
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import sys
import time
import pandas as pd
ROOT=Path(__file__).resolve().parent
PARENT=ROOT.parent
PROJECT=PARENT.parent
LABEL='POST-HOC, DEVELOPMENT-ONLY, EXPLORATORY'
for name in ['metrics','ledger','artifacts','data_derived','tests','work']:(ROOT/name).mkdir(exist_ok=True)
sys.path.insert(0,str(PARENT/'work/representation'))
import rep

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    return h.hexdigest()

def load_fold(fold):
    if type(fold) is not int or fold not in (0,1,2,3):
        raise PermissionError('only development folds0..3 are permitted')
    path=PARENT/f'data_derived/dev_fold_{fold}.parquet'
    frame=pd.read_parquet(path)
    if not frame.fold.eq(fold).all():raise PermissionError('development routing mismatch')
    return frame

def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

@contextmanager
def run(stage,key,config=None):
    target=ROOT/'metrics'/f'{stage}--{key}.json'
    if target.exists():raise FileExistsError('append-only: run key already exists')
    start=dt.datetime.now(dt.timezone.utc).isoformat();clock=time.monotonic()
    config=config or {}
    cfg=ROOT/'ledger'/f'{stage}--{key}.json'
    if cfg.exists():raise FileExistsError('config key already reserved')
    dump(cfg,{'classification':LABEL,'stage':stage,'key':key,'config':config,'PLAN_sha256':digest(ROOT/'PLAN.json')})
    rec={'classification':LABEL,'stage':stage,'key':key,'start':start,'config_sha256':digest(cfg),'test_access':False,'status':'STARTED'}
    journal=ROOT/'ledger/runs.jsonl'
    with journal.open('a') as f:f.write(json.dumps(rec)+'\n')
    try:
        yield rec
        rec['status']='DONE'
    except Exception as exc:
        rec['status']='FAILED';rec['error_type']=type(exc).__name__
        raise
    finally:
        rec['end']=dt.datetime.now(dt.timezone.utc).isoformat();rec['runtime_seconds']=time.monotonic()-clock
        dump(target,rec)
        with journal.open('a') as f:f.write(json.dumps(rec)+'\n')
        print(json.dumps({'classification':LABEL,'stage':stage,'key':key,'status':rec['status'],'seconds':round(rec['runtime_seconds'],3)}),flush=True)
