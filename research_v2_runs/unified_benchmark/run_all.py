"""Run every planned input, model job and row with 4 parallel workers. POST-HOC EXPLORATORY.
Skips anything whose append-only output already exists, so it can be resumed."""
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = str(ROOT.parent / '.venv/bin/python')
PLAN = json.loads((ROOT / 'PLAN.json').read_text())
ENV = dict(os.environ, OMP_NUM_THREADS='2', UB_THREADS='2', PYTHONWARNINGS='ignore')
LOG = ROOT / 'work/run_all.log'
failed = []


def say(msg):
    line = f'[{time.strftime("%H:%M:%S")}] {msg}'
    print(line, flush=True)
    with LOG.open('a') as f:
        f.write(line + '\n')


def call(args, key):
    t = time.monotonic()
    with (ROOT / f'work/{key}.log').open('a') as out:
        r = subprocess.run([PY, *args], cwd=ROOT, env=ENV, stdout=out, stderr=subprocess.STDOUT)
    say(f'{key} exit={r.returncode} {time.monotonic() - t:.0f}s')
    if r.returncode:
        failed.append(key)


def pool(tasks, workers=4):
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda t: call(*t), tasks))


jobs = PLAN['model_jobs']
data = ROOT / 'data_derived'
blockers = sorted({j['blocker'] for j in jobs.values()})
say('phase A0: pair metadata')
pool([(['build_inputs.py', 'meta', b], f'meta-{b}') for b in blockers if not (data / f'meta_{b}.npz').exists()])
need = sorted({(j['blocker'], j['features']) for j in jobs.values()})
todo = [(b, f) for b, f in need if not (data / f'X_{b}_{f}_cv3.npy').exists()]
first = [t for t in todo if t[1] in ('N1',)]
say('phase A1/A2: features')
pool([(['build_inputs.py', 'features', b, f], f'feat-{b}-{f}') for b, f in first])
pool([(['build_inputs.py', 'features', b, f], f'feat-{b}-{f}') for b, f in todo if (b, f) not in first])

order = {'AdaBoost': 0, 'IdentityMLP': 1, 'MLP': 2, 'RF': 3, 'ExtraTrees': 4, 'GBDT': 5, 'LR': 7, 'LinearSVM': 8, 'GBfixed': 9}
jl = sorted(jobs, key=lambda k: (order[jobs[k]['learner']], 0 if '2x' in k else 1, k))
jl = [k for k in jl if not (ROOT / f'metrics/job_{k}.json').exists()]
say(f'phase B: {len(jl)} model jobs')
pool([(['harness.py', 'job', k], f'job-{k}') for k in jl])

rows = [r for r in PLAN['rows'] if not (ROOT / f'metrics/row_{r["id"]}.json').exists()]
base = [r for r in rows if not r.get('alias_of') and (r.get('metrics_only') or f'job-{r["model_job"]}' not in failed)]
slow = lambda r: 0 if r['rule'] in ('genome_TPE',) else 1
say(f'phase C: {len(base)} rows')
pool([(['harness.py', 'row', r['id']], f'row-{r["id"]}') for r in sorted(base, key=slow)])
pool([(['harness.py', 'row', r['id']], f'row-{r["id"]}') for r in rows if r.get('alias_of')])
say(f'ALL DONE; failed={failed}')
