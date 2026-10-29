"""Append-only run accounting and isolated, explicit-path commits."""
from contextlib import contextmanager
from pathlib import Path
import datetime as dt
import hashlib
import json
import platform
import shutil
import subprocess
import time
from integrity import sha256,require_committed

ROOT=Path(__file__).resolve().parent
TREE=ROOT/'work/git_execution'
SERVICE=['-c','user.name=Research V2 execution recorder','-c','user.email=research-v2@localhost']

def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def append_event(path,event):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as f:
        f.write(json.dumps(event,ensure_ascii=False,allow_nan=False)+'\n')
        f.flush()

def terminal_record(start,status,error=None):
    record=dict(start,status=status,end_time=utc())
    if error is not None: record['exception_type']=type(error).__name__
    return record

def commit_files(paths,message):
    import fcntl
    lock_path=ROOT/'cache/git_commit.lock'
    lock_path.parent.mkdir(exist_ok=True)
    with lock_path.open('a') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
        try:
            return _commit_files(paths,message)
        finally:
            fcntl.flock(lock.fileno(),fcntl.LOCK_UN)


def _commit_files(paths,message):
    rels=[]
    for path in paths:
        path=Path(path).resolve()
        rel=path.relative_to(ROOT.parent)
        if any(x in rel.parts for x in ['.venv','data_derived','artifacts','cache','git_execution','__pycache__']):
            raise ValueError('private/derived resource must never be committed')
        target=TREE/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target)
        rels.append(str(rel))
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=TREE,text=True).strip()
    if branch!='research-v2-experiments': raise PermissionError('execution branch drift')
    subprocess.run(['git','add','--',*rels],cwd=TREE,check=True,stdout=subprocess.DEVNULL)
    pending=subprocess.run(['git','diff','--cached','--quiet'],cwd=TREE)
    if pending.returncode:
        subprocess.run(['git',*SERVICE,'commit','-qm',message],cwd=TREE,check=True,stdout=subprocess.DEVNULL)
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=TREE,text=True).strip()

def elapsed_fraction():
    p=json.loads((ROOT/'protocol.json').read_text())
    start=dt.datetime.fromisoformat(p['created_utc'])
    budget=p['operational_budget_minutes_assumption']
    resume=ROOT/'manifests/operational_resume.json'
    if resume.exists():
        operation=json.loads(resume.read_text())
        start=dt.datetime.fromisoformat(operation['resume_created_utc'])
        budget=operation['operational_budget_minutes_assumption']
    return (dt.datetime.now(dt.timezone.utc)-start).total_seconds()/(60*budget)

def assert_unused_run_key(path,run_id):
    path=Path(path)
    if path.exists():
        for line in path.read_text().splitlines():
            if json.loads(line)['run_id']==run_id:
                raise FileExistsError('run key already used; use an explicit new retry/version key')


def deny_post_test_tuning(root,category):
    if (Path(root)/'ledger/test_access.jsonl').exists() and category in {'hyperparameter_search','rule_parameter_search','policy_optimization','calibration_fit'}:
        raise PermissionError('retuning is prohibited after final test access')


@contextmanager
def job(exp_id,key,parameters=None,seed=42,training_jobs=0,tuning_fits=0,validation_evals=0,final_evals=0,category='scientific'):
    deny_post_test_tuning(ROOT,category)
    assert_unused_run_key(ROOT/'ledger/runs.jsonl',f'{exp_id}--{key}')
    protocol=json.loads((ROOT/'protocol.json').read_text())
    split=json.loads((ROOT/'manifests/split_summary.json').read_text()) if (ROOT/'manifests/split_summary.json').exists() else {'split_sha256':'NOT_YET_MATERIALIZED'}
    require_committed(ROOT/'PREREGISTRATION_FREEZE.md')
    config={'exp_id':exp_id,'key':key,'parameters':parameters or {},'seed':int(seed),'protocol_sha256':sha256(ROOT/'protocol.json'),'data_hash':protocol['raw_input_sha256'],'split_hash':split['split_sha256'],'category':category}
    cfg=ROOT/'configs/runs'/f'{exp_id}--{key}.yaml'
    cfg.parent.mkdir(exist_ok=True)
    text=json.dumps(config,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    if cfg.exists() and cfg.read_text()!=text:
        raise ValueError('run configuration key cannot be reused for changed content')
    cfg.write_text(text)
    commit=commit_files([cfg],'Register frozen exploratory run configuration')
    metrics_path=ROOT/'metrics'/f'{exp_id}--{key}.json'
    run_id=f'{exp_id}--{key}'
    start={'run_id':run_id,'exp_id':exp_id,'config_hash':sha256(cfg),'data_hash':config['data_hash'],'split_hash':config['split_hash'],'seed':int(seed),'start_time':utc(),'end_time':None,'hardware':{'machine':platform.machine(),'platform':platform.system()},'status':'STARTED','metrics_file':str(metrics_path.relative_to(ROOT)),'code_commit':commit,'config_file':str(cfg.relative_to(ROOT)),'classification':'EXPLORATORY (LinkSocial, retrospectively exposed)','category':category,'training_jobs':training_jobs,'tuning_fits':tuning_fits,'validation_evals':validation_evals,'final_test_evaluations':final_evals}
    append_event(ROOT/'ledger/runs.jsonl',start)
    out={}
    t=time.monotonic()
    try:
        yield out
        out['classification']='EXPLORATORY (LinkSocial, retrospectively exposed)'
        out['runtime_seconds']=time.monotonic()-t
        metrics_path.write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
        end=terminal_record(start,'DONE')
        end['metrics_sha256']=sha256(metrics_path)
        end['runtime_seconds']=out['runtime_seconds']
        append_event(ROOT/'ledger/runs.jsonl',end)
        print(json.dumps({'run':run_id,'status':'DONE','seconds':round(out['runtime_seconds'],3)}),flush=True)
    except BaseException as exc:
        metrics_path.write_text(json.dumps({'classification':'EXPLORATORY (LinkSocial, retrospectively exposed)','status':'FAILED','exception_type':type(exc).__name__,'runtime_seconds':time.monotonic()-t})+'\n')
        end=terminal_record(start,'FAILED',exc)
        end['runtime_seconds']=time.monotonic()-t
        end['metrics_sha256']=sha256(metrics_path)
        append_event(ROOT/'ledger/runs.jsonl',end)
        with (ROOT/'DEVIATIONS.md').open('a') as f:
            f.write(f'\n- Run {run_id}: FAILED ({type(exc).__name__}); no raw exception values logged. See metrics + ledger.\n')
        raise
