"""Re-ordered execution (researcher instruction; frozen plan unchanged). POST-HOC EXPLORATORY.
Order: GBDT jobs -> LR/LinearSVM jobs -> Layer-2 fixed-config jobs -> Layer-2 rows -> Layer-1 rows whose job is complete -> alias rows.
RF/ExtraTrees/AdaBoost are not launched here. At most 4 harness processes run at once (counting jobs already running; stopped ones do not count)."""
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = str(ROOT.parent / '.venv/bin/python')
PLAN = json.loads((ROOT / 'PLAN.json').read_text())
ENV = dict(os.environ, OMP_NUM_THREADS='2', UB_THREADS='2', PYTHONWARNINGS='ignore')
LOG = ROOT / 'work/run_phase2.log'
MAXP = 4
DEFER = ('J_sparse_FLEX35_RF', 'J_sparse_FLEX35_ExtraTrees', 'J_sparse_FLEX35_AdaBoost')


def say(msg):
    with LOG.open('a') as f:
        f.write(f'[{time.strftime("%H:%M:%S")}] {msg}\n')


def active_harness():
    out = subprocess.run(['ps', '-eo', 'stat,args'], capture_output=True, text=True).stdout.splitlines()
    return sum(1 for l in out if 'harness.py' in l and not l.strip().startswith('T'))


def done_job(k):
    return (ROOT / f'metrics/job_{k}.json').exists()


def done_row(r):
    return (ROOT / f'metrics/row_{r}.json').exists()


jobs = PLAN['model_jobs']
running_now = subprocess.run(['ps', '-eo', 'args'], capture_output=True, text=True).stdout
gbdt = sorted(k for k, j in jobs.items() if j['learner'] == 'GBDT' and k not in running_now)
linear = [k for k in ('J_sparse_FLEX35_LR', 'J_sparse_FLEX35_LinearSVM')]
fixed = sorted(k for k, j in jobs.items() if j['learner'] in ('GBfixed', 'IdentityMLP'))
tasks = [('job', k, None) for k in gbdt + linear + fixed if not done_job(k)]
rows = PLAN['rows']
l2 = [r for r in rows if r['layer'] == 2 and not r.get('alias_of')]
l1 = [r for r in rows if r['layer'] == 1 and not r.get('alias_of')]
l1.sort(key=lambda r: 0 if r['rule'] == 'genome_TPE' else 1)
aliases = [r for r in rows if r.get('alias_of')]
for r in l2 + l1 + aliases:
    if r['model_job'] in DEFER or done_row(r['id']):
        continue
    tasks.append(('row', r['id'], r))

procs = {}
say(f'start: {len(tasks)} tasks queued')
while tasks or procs:
    for key, (p, t0) in list(procs.items()):
        if p.poll() is not None:
            say(f'{key} exit={p.returncode} {time.monotonic() - t0:.0f}s')
            procs.pop(key)
    launched = True
    while launched and tasks and active_harness() < MAXP:
        launched = False
        for i, (kind, key, r) in enumerate(tasks):
            if kind == 'row':
                if r.get('alias_of'):
                    ready = done_row(r['alias_of'])
                elif r.get('metrics_only'):
                    ready = True
                else:
                    ready = done_job(r['model_job'])
                if not ready:
                    pending_job = r.get('model_job') and (any(t[1] == r['model_job'] for t in tasks) or r['model_job'] in running_now or any(r['model_job'] in k for k in procs))
                    pending_src = r.get('alias_of') and (any(t[1] == r['alias_of'] for t in tasks) or f'row-{r["alias_of"]}' in procs)
                    if not (pending_job or pending_src):
                        # dependency finished without output (failed): drop with a log line
                        say(f'{key} skipped: dependency missing'); tasks.pop(i); launched = True; break
                    continue
            log = (ROOT / f'work/{kind}-{key}.log').open('a')
            procs[f'{kind}-{key}'] = (subprocess.Popen([PY, 'harness.py', kind, key], cwd=ROOT, env=ENV, stdout=log, stderr=subprocess.STDOUT), time.monotonic())
            tasks.pop(i); launched = True
            time.sleep(2)
            break
    time.sleep(15)
say('PHASE2 DONE')
