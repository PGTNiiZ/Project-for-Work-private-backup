"""SYNTHETIC verification + source-only provenance; no scientific data reads."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
# history -> work -> posthoc_blocking_features -> research_v2_runs -> project
ROOT=HERE.parents[3]
PIN='1e0a2dbba4d30e7b291dda3cc02d6c11fdd3909b'
BACKUP_PIN='903246c87eba069d4c07106695cbae072dbbb343'
REVIEW=ROOT/'research_v2_review_workspace/research_v2/review'
REPOS=REVIEW/'_work/repos'
SOURCES={
 'base':'train_data/stage7_8_rebuilt_experiment_hybrid/run_rebuilt_pipeline.py',
 'multimodal':'train_data/stage7_13_multimodal_suite/run_multimodal_suite.py',
 'recover':'image_process/recover_profile_images.py',
}

def git(repo,*args):
    return subprocess.check_output(['git','-C',str(REPOS/repo),*args])

assert git('main','rev-parse','HEAD').decode().strip()==PIN
assert git('backup','rev-parse','HEAD').decode().strip()==BACKUP_PIN
manifest=dict(scope='SYNTHETIC / CODE-ONLY / DEVELOPMENT-ONLY; NO REAL DATA READS',
    main_pin=PIN,backup_pin=BACKUP_PIN,sources={},packages={})
for key,path in SOURCES.items():
    content=git('main','show',f'{PIN}:{path}')
    entry=dict(path=path,pinned_sha256=hashlib.sha256(content).hexdigest())
    if key!='recover':
        copy=REVIEW/'_work/agentA/source/main'/f'{path}.txt'
        # Source snapshots omit the final newline: compare rstrip LF explicitly.
        entry['review_copy']=str(copy.relative_to(ROOT))
        entry['matches_pinned_ignoring_final_newline']=copy.read_bytes().rstrip(b'\n')==content.rstrip(b'\n')
        assert entry['matches_pinned_ignoring_final_newline']
        entry['backup_path_exists']=bool(git('backup','ls-tree','-r','--name-only',BACKUP_PIN,path))
    manifest['sources'][key]=entry
for package in ('numpy','scipy','scikit-learn','rapidfuzz','Pillow','pandas'):
    manifest['packages'][package]=importlib.metadata.version(package)
for name in ('hist_features.py','test_hist_features_synthetic.py','test_source_parity_synthetic.py','MAPPING_TH.md'):
    manifest.setdefault('owned_sha256',{})[name]=hashlib.sha256((HERE/name).read_bytes()).hexdigest()
cmd=[sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_*synthetic.py','-v']
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
run=subprocess.run(cmd,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(HERE/'SYNTHETIC_TEST_RESULTS.txt').write_text('SYNTHETIC ONLY — no scientific metrics\n'+run.stdout)
manifest['test_exit_code']=run.returncode
manifest['test_command']='PYTHONDONTWRITEBYTECODE=1 research_v2_runs/.venv/bin/python -m unittest discover -s research_v2_runs/posthoc_blocking_features/work/history -p test_*synthetic.py -v'
(HERE/'SOURCE_AUDIT.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(run.stdout)
print('source copies verified against pinned MAIN; source-only provenance saved')
raise SystemExit(run.returncode)
