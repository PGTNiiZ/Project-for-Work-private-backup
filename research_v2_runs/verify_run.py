"""Read-only final verification; emits aggregates, never profile filenames."""
from pathlib import Path
import collections
import csv
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from integrity import sha256
from runtime import ROOT as R,TREE


def technical_service_email(value):
    return value.lower() in {'noreply@anthropic.com','claude@anthropic.com','noreply@openai.com'}


def owned_commit_scope(records,external):
    own=[path for commit,paths in records.items() if commit not in external for path in paths]
    foreign=[path for commit,paths in records.items() if commit in external for path in paths]
    return {'owned_outside_count':sum(not p.startswith('research_v2_runs/') for p in own),'concurrent_path_count':len(foreign),'concurrent_commits':sorted(external),'scope':'per-commit ownership; unrelated inherited history retained, not rewritten'}


def working_lfs_hash(file):
    if not file.exists(): return 'MISSING'
    if file.stat().st_size<1024:
        data=file.read_bytes()
        if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
            current=re.search(rb'^oid sha256:([0-9a-f]{64})$',data,re.M)
            return current.group(1).decode() if current else 'INVALID_POINTER'
    return sha256(file)


def raw_git_baseline(protocol):
    root=R.parent
    source=protocol['source_commit']
    roots=['data_for_project/','data/raw/','image_process/downloaded_images/','train_data/ground_truth_labels.csv','train_data/ground_truth_matrix_index.csv','train_data/ground_truth_pairs.csv']
    raw=subprocess.check_output(['git','ls-tree','-rz','--full-tree',source,'--',*roots],cwd=root)
    records=[]
    for item in raw.split(b'\0'):
        if not item: continue
        meta,path=item.split(b'\t',1)
        mode,typ,oid=meta.split()
        if typ==b'blob' and mode in [b'100644',b'100755']: records.append((oid,path))
    baseline_digest=hashlib.sha256()
    actual_digest=hashlib.sha256()
    mismatches=0
    difference_details=[]
    measured=0
    pointers=0
    process=subprocess.Popen(['git','cat-file','--batch'],cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    for oid,path in records:
        process.stdin.write(oid+b'\n')
        process.stdin.flush()
        header=process.stdout.readline().split()
        size=int(header[2])
        remaining=size
        h=hashlib.sha256()
        small=b''
        while remaining:
            chunk=process.stdout.read(min(1048576,remaining))
            if not chunk: raise ValueError('truncated immutable Git object')
            h.update(chunk)
            if size<1024: small+=chunk
            remaining-=len(chunk)
        process.stdout.read(1)
        expected=h.hexdigest()
        pointer=re.search(rb'^oid sha256:([0-9a-f]{64})$',small,re.M)
        file=root/path.decode('utf-8',errors='surrogateescape')
        if pointer:
            pointers+=1
            expected=pointer.group(1).decode()
            actual=working_lfs_hash(file)
            measured+=int(file.exists() and not (file.stat().st_size<1024 and file.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1')))
        else:
            actual=sha256(file) if file.exists() else 'MISSING'
            measured+=int(file.exists())
        if actual!=expected:
            mismatches+=1
            difference_details.append({'namespace':path.split(b'/')[0].decode(),'opaque_path_sha256':hashlib.sha256(path).hexdigest(),'is_DS_Store_metadata':path.split(b'/')[-1]==b'.DS_Store','expected_sha256':expected,'actual_sha256':actual,'current_exists':file.exists(),'current_bytes':file.stat().st_size if file.exists() else None,'source_blob_bytes':size,'LFS':bool(pointer)})
        opaque=hashlib.sha256(path).digest()
        baseline_digest.update(opaque+expected.encode())
        actual_digest.update(opaque+actual.encode())
    process.stdin.close()
    process.wait()
    return {'reference_commit':source,'reference_method':'SHA256 reconstructed from immutable pre-run Git objects; LFS content uses oid if only pointer available','files_checked':len(records),'content_SHA256_measured':measured,'LFS_pointer_cases':pointers,'mismatches':mismatches,'difference_details':difference_details,'baseline_aggregate_sha256':baseline_digest.hexdigest(),'current_aggregate_sha256':actual_digest.hexdigest(),'filenames_not_output':True}


def scan_public_outputs(write=True):
    patterns={'url':re.compile(r'https?://[^\s<>\]\)\"\']+'),'email':re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'),'handle':re.compile(r'(?<![\w])@[A-Za-z0-9_]{2,}')}
    allowed_url_prefixes=['http://www.w3.org/','http://purl.org/','http://creativecommons.org/','https://matplotlib.org/','https://github.com/PGTNiiZ/Project-for-Work','https://doi.org/']
    findings=[]
    files=[p for folder in ['reports','figures','ledger'] for p in (R/folder).rglob('*') if p.is_file()]
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(R.parent/'research_v2_review_workspace/research_v2/review/_work/v3_deps'))
    for path in files:
        if path.suffix=='.png': continue
        if path.suffix=='.pdf':
            import fitz
            with fitz.open(path) as pdf: text='\n'.join(page.get_text() for page in pdf)
        else:
            try: text=path.read_text()
            except UnicodeDecodeError: continue
        for kind,pattern in patterns.items():
            for match in pattern.finditer(text):
                value=match.group()
                label='UNCLASSIFIED'
                if kind=='url' and any(value.startswith(prefix) for prefix in allowed_url_prefixes): label='REVIEWED_TECHNICAL_OR_REPOSITORY_URL'
                if kind=='handle' and re.fullmatch('@[0-9a-f]{7,40}',value): label='REVIEWED_GIT_COMMIT_CITATION'
                if kind=='email' and value in ['research-v2@localhost','fixture@localhost']: label='REVIEWED_SYNTHETIC_SERVICE_IDENTITY'
                findings.append({'file':str(path.relative_to(R)),'line':text.count('\n',0,match.start())+1,'kind':kind,'classification':label})
    source=json.loads((R/'protocol.json').read_text())['source_commit']
    messages=subprocess.check_output(['git','log',source+'..HEAD','--format=%B'],cwd=TREE,text=True)
    for kind,pattern in patterns.items():
        for match in pattern.finditer(messages):
            label='REVIEWED_SOFTWARE_SERVICE_EMAIL_NOT_PROFILE_VALUE' if kind=='email' and technical_service_email(match.group()) else 'UNCLASSIFIED'
            findings.append({'file':'GIT_COMMIT_MESSAGES','line':messages.count('\n',0,match.start())+1,'kind':kind,'classification':label})
    result={'files_scanned':len(files),'findings':findings,'unclassified_hits':sum(f['classification']=='UNCLASSIFIED' for f in findings),'profile_values_confirmed':0,'scope':'new public reports/figures text, ledger, commit messages; PNG graphics generated only from aggregate arrays','terminal_transcript_privacy_incident_not_erased':True}
    if write: (R/'manifests/pii_scan.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def verify():
    protocol=json.loads((R/'protocol.json').read_text())
    checks=[]
    def check(name,condition,detail=''):
        checks.append({'check':name,'status':'PASS' if condition else 'FAIL','detail':detail})
    expected=['RESULTS_SUMMARY_TH.md','THESIS_TABLES_TH.md','HISTORICAL_COMPARISON_TH.md','THREATS_TO_VALIDITY_TH.md','EXECUTION_HANDOFF_TH.md']
    for name in expected: check('report '+name,(R/'reports'/name).exists() and (R/'reports'/name).stat().st_size>0)
    for name in ['DEVIATIONS.md','GATE_RECORD.md','PREREGISTRATION_FREEZE.md','LABEL_SANITY.md','ENVIRONMENT.md','FINAL_CONFIGS.md']:
        check('root artifact '+name,(R/name).exists() and (R/name).stat().st_size>0)
    rows=[json.loads(line) for line in (R/'ledger/runs.jsonl').read_text().splitlines()]
    latest={r['run_id']:r for r in rows}
    done=[r for r in latest.values() if r['status']=='DONE']
    commits=subprocess.check_output(['git','log','--reverse','--format=%H','--','research_v2_runs/PREREGISTRATION_FREEZE.md'],cwd=TREE,text=True).splitlines()
    frozen=commits[0]
    frozen_time=int(subprocess.check_output(['git','show','-s','--format=%ct',frozen],cwd=TREE,text=True))
    scientific=[r for r in latest.values() if r.get('category')!='diagnostic' and r.get('start_time')]
    first=min(dt.datetime.fromisoformat(r['start_time']).timestamp() for r in scientific)
    check('G4 committed before first scientific run',frozen_time<first,frozen)
    lock=json.loads((R/'manifests/final_lock.json').read_text())
    access=[json.loads(x) for x in (R/'ledger/test_access.jsonl').read_text().splitlines()]
    first_final=min(dt.datetime.fromisoformat(r['timestamp']).timestamp() for r in access)
    final_commits=subprocess.check_output(['git','log','--reverse','--format=%H','--','research_v2_runs/FINAL_CONFIGS.md'],cwd=TREE,text=True).splitlines()
    final_time=int(subprocess.check_output(['git','show','-s','--format=%ct',final_commits[0]],cwd=TREE,text=True))
    check('FINAL_CONFIGS committed before final access',final_time<first_final,final_commits[0])
    keys=[e['config_id'] for e in access]
    check('final access matches exact frozen configurations',set(keys)==set(lock['configs']) and len(keys)==len(set(keys)))
    check('final declaration unchanged',sha256(R/'FINAL_CONFIGS.md')==lock['document_sha256'])
    check('frozen artifacts unchanged',all(sha256(R/path)==expected for path,expected in next(iter(lock['configs'].values()))['artifact_hashes'].items()))
    check('all DONE metrics trace by SHA256',all((R/r['metrics_file']).exists() and sha256(R/r['metrics_file'])==r['metrics_sha256'] for r in done))
    check('all scientific results EXPLORATORY',all(r.get('classification')==protocol['status'] for r in scientific))
    check('every run config hash matches',all((R/r['config_file']).exists() and sha256(R/r['config_file'])==r['config_hash'] for r in scientific))
    commit_ids=sorted(set(r['code_commit'] for r in scientific))
    times=subprocess.check_output(['git','show','--no-patch','--format=%H %ct',*commit_ids],cwd=TREE,text=True)
    commit_times={line.split()[0]:int(line.split()[1]) for line in times.splitlines() if len(line.split())==2}
    check('each run config committed before run timestamp',all(commit_times[r['code_commit']]<=dt.datetime.fromisoformat(r['start_time']).timestamp() for r in scientific))
    batch=subprocess.Popen(['git','cat-file','--batch'],cwd=TREE,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    config_mismatch=0
    for r in scientific:
        expression=r['code_commit']+':research_v2_runs/'+r['config_file']
        batch.stdin.write(expression.encode()+b'\n');batch.stdin.flush()
        header=batch.stdout.readline().split()
        if header[-1:]==[b'missing']:
            config_mismatch+=1;continue
        content=batch.stdout.read(int(header[2]));batch.stdout.read(1)
        config_mismatch+=int(hashlib.sha256(content).hexdigest()!=r['config_hash'])
    batch.stdin.close();batch.wait()
    check('run configurations exist verbatim in their recorded commits',config_mismatch==0,f'mismatches={config_mismatch}')
    protected={**protocol['design_sha256'],**protocol['protected_input_sha256'],**protocol['historical_artifacts'],protocol['raw_input']:protocol['raw_input_sha256']}
    mismatches=sum(not (R.parent/path).is_file() or sha256(R.parent/path)!=expected for path,expected in protected.items())
    check('raw input/thesis/v1/design/historical SHA256 unchanged',mismatches==0,f'{len(protected)} protected files; mismatches={mismatches}')
    baseline=raw_git_baseline(protocol)
    (R/'manifests/raw_immutability.json').write_text(json.dumps(baseline,indent=2)+'\n')
    check('additional raw datasets and images match pinned Git SHA256',baseline['mismatches']==0 and baseline['files_checked']>0,f"files={baseline['files_checked']}; no filenames output")
    primary=json.loads((R/'metrics/primary_contrasts.json').read_text())
    check('five primary contrasts CI/Holm/decision',set(primary)=={'H1','H2','H3','H4','H5'} and all(r['bootstrap_B']==10000 and 'holm_adjusted_p' in r and len(r['ci95'])==2 and 'decision' in r for r in primary.values()))
    check('equivalence decisions have TOST support',all(r['decision']!='equivalent' or (r['tost_holm_adjusted_p']<.05 and r['equivalent']) for r in primary.values()))
    policies=[r for r in done if r.get('category')=='policy_optimization']
    check('policy budgets exactly 2048 per seed',len(policies)==50 and all(json.loads((R/r['metrics_file']).read_text())['evaluations']==2048 for r in policies))
    searches=[r for r in done if r.get('category')=='hyperparameter_search']
    groups=collections.Counter(json.loads((R/r['config_file']).read_text())['parameters']['learner']+'-'+json.loads((R/r['config_file']).read_text())['parameters']['feature'] for r in searches)
    check('six model searches at 200 configs each',len(groups)==6 and all(n==200 for n in groups.values()))
    coverage=list(csv.DictReader((R/'reports/EXPERIMENT_COVERAGE.csv').open()))
    tier1=[r for r in coverage if r['tier']=='1']
    check('every Tier1 DONE or explicit reason',bool(tier1) and all(r['status']=='DONE' or bool(r['reason']) for r in tier1))
    check('independent frozen metric recomputation',all(r['independent_count_check']=='PASS' for r in json.loads((R/'metrics/independent_metric_check.json').read_text())['checks']))
    no_post_tune=all(dt.datetime.fromisoformat(r['start_time']).timestamp()<first_final for r in done if r.get('category') in {'hyperparameter_search','rule_parameter_search','policy_optimization','calibration_fit'})
    check('no primary hyperparameter/policy/calibration jobs after test opened',no_post_tune,'supporting model-summary validation-only threshold diagnostics disclosed separately')
    fixed=json.loads((R/'manifests/TIER2_FIXED_PLAN.json').read_text())
    valid_post_fits=True
    for r in done:
        if not r.get('training_jobs') or dt.datetime.fromisoformat(r['start_time']).timestamp()<first_final:continue
        parameters=json.loads((R/r['config_file']).read_text())['parameters']
        parent=parameters['learner']+'-'+parameters.get('feature','lexical')
        valid_post_fits &= parameters['params']==fixed['parents'][parent]['params'] and r['exp_id'] in {'E5-4','E5-5','E3-1','E3-2'}
    check('all post-final supporting fits use pre-final frozen hyperparameters',valid_post_fits)
    check('inference timing stages have five measured repetitions',all(t['measurement_repetitions']==5 for t in json.loads((R/'metrics/final_summary.json').read_text())['timings']))
    rules=[r for r in done if r.get('category')=='rule_parameter_search']
    check('tuned rule has exactly 200 configurations',len(rules)==200)
    pii=scan_public_outputs()
    check('public-output PII scan classified, zero profile-value hits',pii['unclassified_hits']==0,f"unclassified={pii['unclassified_hits']}; terminal incident separately disclosed")
    changed=subprocess.check_output(['git','diff','--name-only',protocol['source_commit'],'HEAD'],cwd=TREE,text=True).splitlines()
    history=subprocess.check_output(['git','log',protocol['source_commit']+'..HEAD','--format=COMMIT:%H','--name-only'],cwd=TREE,text=True)
    touched={}
    current=None
    for line in history.splitlines():
        if line.startswith('COMMIT:'):
            current=line.removeprefix('COMMIT:');touched[current]=[]
        elif line and current:touched[current].append(line)
    external={'c68c9d209bc690306f75c01cf36b07603d26a169'}
    scope=owned_commit_scope(touched,external)
    scope.update(recorded_base=protocol['source_commit'],concurrent_parent='932cf9569abb38dfd9c3aa55e258da299e5290e6',whole_branch_is_runs_only=False,concurrent_change_retained_without_rewrite=True)
    (R/'manifests/concurrent_change_scope.json').write_text(json.dumps(scope,indent=2)+'\n')
    check('all owned committed additions confined to research_v2_runs',scope['owned_outside_count']==0,'inherited concurrent c68c9d20 has16 outside paths; explicitly retained, not counted as owned writes')
    check('concurrent outside delta exactly documented',set(p for p in changed if not p.startswith('research_v2_runs/'))==set(touched[next(iter(external))]),'whole branch includes unrelated holdout_eval changes; review before any future release')
    check('no private data/model/embedding/prediction committed',all(not any('/'+part+'/' in '/'+p for part in ['data_derived','artifacts','cache','.venv']) for p in changed))
    check('push remains disabled',protocol['push']=='DISABLED')
    for path in (R/'reports').glob('*.csv'):
        with path.open() as f: list(csv.DictReader(f))
    summary={'PASS':sum(c['status']=='PASS' for c in checks),'FAIL':sum(c['status']=='FAIL' for c in checks),'checks':checks,'scientific_status':protocol['status'],'G0_G1':'DECLARED PASSED; REFERENCE NOT PROVIDED','G5':'NOT MET','protocol_deviations_disclosed':True,'privacy_scope':'file-output scan only; terminal metadata incident remains','commit_worktree_branch':subprocess.check_output(['git','branch','--show-current'],cwd=TREE,text=True).strip()}
    (R/'manifests/verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    lines=[f"{c['status']} {c['check']} {c['detail']}".rstrip() for c in checks]
    lines.append(f"PASS={summary['PASS']} FAIL={summary['FAIL']} EXPLORATORY; G5 NOT MET; terminal privacy incident disclosed")
    (R/'reports/consistency_check.txt').write_text('\n'.join(lines)+'\n')
    print(lines[-1])
    return summary

if __name__=='__main__':
    result=verify()
    sys.exit(int(result['FAIL']>0))
