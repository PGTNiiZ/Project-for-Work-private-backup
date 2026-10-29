"""STEP 2: multi-pass blocking vs sparse at 1x/1.5x/2x budget. POST-HOC, DEVELOPMENT-ONLY, EXPLORATORY.
Retrieval never sees labels; labels used only afterwards to count PC."""
import sys, json, math, time
from pathlib import Path
import numpy as np, pandas as pd, pickle
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).parents[1]))
from common import run, load_fold, dump, ROOT, PARENT, rep
import blocking
from preflight import ground_truth
D = PARENT / 'data_derived/representation'
MULT = [1.0, 1.5, 2.0]
DATA = ROOT / 'data_derived'
with run('S2', 'multipass-vs-sparse-attempt2', {'multipliers': MULT, 'passes': list(blocking.PASSES), 'pool': 50}) as rec:
    folds = [load_fold(f) for f in range(4)]
    rows = []
    cause_recovered = {}
    for f, df in enumerate(folds):
        n = len(df)
        base = len(np.load(D / f'pairs_{f}_sparse_matched.npy'))
        train = pd.concat([x for g, x in enumerate(folds) if g != f], ignore_index=True)
        t0 = time.monotonic(); vec = blocking.fit_passes(train); fit_s = time.monotonic() - t0
        with (D / f'retriever_{f}.pkl').open('rb') as inp:
            sv = pickle.load(inp)
        gt = ground_truth(df); gk = gt[:, 0].astype(np.int64) * n + gt[:, 1]
        sp1 = np.load(D / f'pairs_{f}_sparse_matched.npy')
        miss1 = gt[~np.isin(gk, sp1[:, 0].astype(np.int64) * n + sp1[:, 1])]
        cause_miss = blocking.assign_causes(blocking.similarity_flags(df, miss1, vec))
        cause_of = dict(zip((miss1[:, 0].astype(np.int64) * n + miss1[:, 1]).tolist(), cause_miss.tolist()))
        for m in MULT:
            budget = math.ceil(base * m)
            for method in ['sparse', 'multipass']:
                t0 = time.monotonic()
                if method == 'sparse':
                    pairs = np.load(D / f'pairs_{f}_sparse_matched.npy') if m == 1.0 else rep.retrieval(df, sv, None, 50, 'sparse', budget=budget)
                    extra = {}
                    run_s = time.monotonic() - t0 if m != 1.0 else None
                else:
                    pairs, extra, _ = blocking.multipass_pairs(df, vec, budget); extra = {'pool_'+k if k=='budget' else k: v for k, v in extra.items()}
                    run_s = time.monotonic() - t0 + fit_s
                keys = pairs[:, 0].astype(np.int64) * n + pairs[:, 1]
                found = np.isin(gk, keys)
                rec_by_cause = {c: 0 for c in 'abcdef'}
                for k in keys[np.isin(keys, list(cause_of))]:
                    rec_by_cause[cause_of[int(k)]] += 1
                row = dict(fold=f, method=method, multiplier=m, budget=int(budget), candidates=int(len(pairs)), ground_truth=int(len(gt)),
                           found=int(found.sum()), runtime_seconds=run_s, recovered_of_sparse1x_misses=rec_by_cause, **extra)
                rows.append(row)
                print(json.dumps({k: v for k, v in row.items() if k != 'recovered_of_sparse1x_misses'}), flush=True)
                if method == 'multipass' and m == 1.0:
                    np.save(DATA / f'multipass_dev_fold{f}_1.0x.npy', pairs)
                np.save(DATA / f'{method}_dev_fold{f}_{m}x.npy', pairs)
    pooled = {}
    for method in ['sparse', 'multipass']:
        for m in MULT:
            r = [x for x in rows if x['method'] == method and x['multiplier'] == m]
            rc = {c: sum(x['recovered_of_sparse1x_misses'][c] for x in r) for c in 'abcdef'}
            pooled[f'{method}@{m}x'] = dict(found=sum(x['found'] for x in r), ground_truth=sum(x['ground_truth'] for x in r),
                PC=sum(x['found'] for x in r) / sum(x['ground_truth'] for x in r), candidates=sum(x['candidates'] for x in r),
                runtime_seconds=sum(x['runtime_seconds'] or 0 for x in r), recovered_of_sparse1x_misses_by_cause=rc)
    dump(ROOT / 'metrics/step2_blocking_comparison.json', {'classification': 'POST-HOC, DEVELOPMENT-ONLY, EXPLORATORY', 'rows': rows, 'pooled': pooled})
    print(json.dumps(pooled, indent=1))
