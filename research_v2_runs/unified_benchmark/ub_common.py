"""Shared paths, development-only loading and append-only records. POST-HOC EXPLORATORY."""
from contextlib import contextmanager
from pathlib import Path
import datetime as dt
import hashlib
import json
import sys
import time
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent
PROJECT = PARENT.parent
POSTHOC = PARENT / 'posthoc_blocking_features'
REPD = PARENT / 'data_derived/representation'
DATA = ROOT / 'data_derived'
ART = ROOT / 'artifacts'
METRICS = ROOT / 'metrics'
LABEL = 'POST-HOC EXPLORATORY (development reuse; no confirmatory claim)'
FOLDS = (0, 1, 2, 3)
SEEDS = (11, 23, 42, 71, 101)
for p in (DATA, ART, METRICS, ROOT / 'ledger', ROOT / 'work'):
    p.mkdir(exist_ok=True)
sys.path.insert(0, str(PARENT / 'work/representation'))
sys.path.insert(0, str(PARENT / 'work/statistics'))
sys.path.insert(0, str(PARENT))
sys.path.insert(0, str(POSTHOC))
sys.path.insert(0, str(POSTHOC / 'work/history'))
sys.path.insert(0, str(PROJECT / 'src'))
import rep  # noqa: E402
from preflight import ground_truth  # noqa: E402

PLAN = json.loads((ROOT / 'PLAN.json').read_text())


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(2 ** 20), b''):
            h.update(block)
    return h.hexdigest()


def load_fold(fold):
    if type(fold) is not int or fold not in FOLDS:
        raise PermissionError('only development folds 0..3 are permitted')
    frame = pd.read_parquet(PARENT / f'data_derived/dev_fold_{fold}.parquet')
    if not frame.fold.eq(fold).all():
        raise PermissionError('development routing mismatch')
    return frame


def all_dev():
    folds = [load_fold(f) for f in FOLDS]
    offs = np.cumsum([0] + [len(x) for x in folds])
    return folds, pd.concat(folds, ignore_index=True), offs


def dump_new(path, value):
    path = Path(path)
    if path.exists():
        raise FileExistsError(f'append-only: {path.name} exists')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + '\n')


def ledger(rec):
    with (ROOT / 'ledger/runs.jsonl').open('a') as f:
        f.write(json.dumps(rec) + '\n')


@contextmanager
def run(kind, key):
    start = dt.datetime.now(dt.timezone.utc).isoformat()
    clock = time.monotonic()
    rec = {'classification': LABEL, 'kind': kind, 'key': key, 'start': start, 'test_access': False,
           'PLAN_sha256': digest(ROOT / 'PLAN.json'), 'status': 'STARTED'}
    ledger(dict(rec))
    try:
        yield rec
        rec['status'] = 'DONE'
    except BaseException as exc:
        rec['status'] = 'FAILED'
        rec['error_type'] = type(exc).__name__
        rec['error'] = str(exc)[:300]
        raise
    finally:
        rec['end'] = dt.datetime.now(dt.timezone.utc).isoformat()
        rec['runtime_seconds'] = time.monotonic() - clock
        ledger({k: v for k, v in rec.items() if k in ('classification', 'kind', 'key', 'start', 'end', 'status', 'runtime_seconds', 'error_type', 'error', 'test_access', 'PLAN_sha256')})
