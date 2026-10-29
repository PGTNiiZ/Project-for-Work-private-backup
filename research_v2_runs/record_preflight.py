"""Record environment and rerun diagnostics with prospective run accounting."""
from pathlib import Path
import importlib.metadata as md
import json
import platform
import subprocess
from integrity import sha256
from runtime import commit_files,job,append_event,utc
import preflight
R=Path(__file__).resolve().parent

def command(*args): return subprocess.check_output(args,text=True).strip()

def main():
    hardware={'os':platform.system(),'release':platform.release(),'architecture':platform.machine(),'cpu':command('sysctl','-n','machdep.cpu.brand_string'),'cpu_count':int(command('sysctl','-n','hw.ncpu')),'memory_bytes':int(command('sysctl','-n','hw.memsize')),'python':platform.python_version(),'threads_per_model':2,'device':'cpu'}
    versions={x:md.version(x) for x in ['numpy','pandas','scipy','scikit-learn','rapidfuzz','sentence-transformers','torch','optuna','numba','matplotlib','pyarrow','pytest']}
    env={'hardware':hardware,'packages':versions,'requirements_lock_sha256':sha256(R/'requirements.lock'),'scientific_status':'EXPLORATORY (LinkSocial, retrospectively exposed)','isolation':'project-local .venv; own sparse Git worktree; source inputs read-only','synthetic_smoke':'tests/test_smoke.py passed, not manuscript evidence','package_intelligence':'installer reported incomplete external threat-intelligence metadata checks; not a malicious-package finding','initial_integration_tests_passed':42}
    (R/'ENVIRONMENT.md').write_text('# Environment — Round4\n\n'+json.dumps(env,ensure_ascii=False,indent=2)+'\n\nModel weights downloaded only from pinned public revision; profile serialization and encoder inference remain local. No hosted embedding/LLM requests. No GPU acceleration used.\n')
    (R/'manifests/environment.json').write_text(json.dumps(env,indent=2)+'\n')
    paths=[R/'.gitignore',R/'ENVIRONMENT.md',R/'manifests/environment.json',R/'preflight.py',R/'integrity.py',R/'runtime.py',R/'training.py',R/'representation_run.py',R/'record_preflight.py',*sorted((R/'tests').glob('*.py')),*sorted((R/'work/representation').glob('*.py')),*sorted((R/'work/statistics').glob('*.py'))]
    commit_files(paths,'Record tested local environment and frozen representation implementations')
    # Initial unledgered adapter diagnostic is preserved honestly, not backdated.
    old=R/'metrics/label_sanity_adapter_initial_bug.json'
    append_event(R/'ledger/runs.jsonl',{'run_id':'D0-2--initial-adapter-check-retrospective','exp_id':'D0-2','config_hash':sha256(R/'configs/D0-2.yaml'),'data_hash':json.loads((R/'protocol.json').read_text())['raw_input_sha256'],'split_hash':'DISCARDED_ADAPTER_BUG','seed':42,'start_time':None,'end_time':None,'recorded_time':utc(),'hardware':hardware,'status':'FAILED','metrics_file':str(old.relative_to(R)),'metrics_sha256':sha256(old),'category':'diagnostic','retrospective_entry':True,'reason':'identity token case normalization bug; timestamps not recorded, not reconstructed','classification':'EXPLORATORY (LinkSocial, retrospectively exposed)','training_jobs':0,'tuning_fits':0,'validation_evals':0,'final_test_evaluations':0})
    with job('D0-2','canonical-sanity-rerun',{'source':'protocol.raw_input','adapter':'case-sensitive identity tokens'},category='diagnostic') as rec:
        preflight.run(R)
        rec.update(json.loads((R/'metrics/label_sanity.json').read_text()))
    with job('D0-4','split-integrity',{'resource':'split manifest','zero_overlap_required':True},category='diagnostic') as rec:
        rec.update(json.loads((R/'metrics/leakage_audit.json').read_text()))
        assert rec['entity_overlap']==0 and rec['component_overlap']==0
    commit_files([R/'D0_REPORT.md',R/'LABEL_SANITY.md',R/'LEAKAGE_AUDIT.md',*sorted((R/'manifests').glob('*.json')),*sorted((R/'metrics').glob('*.json')),R/'ledger/runs.jsonl'],'Record canonical sanity and leakage diagnostics before scientific execution')

if __name__=='__main__': main()
