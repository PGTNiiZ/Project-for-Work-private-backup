"""STEP 1: classify sparse-blocker misses from similarity features. Aggregate counts only.
POST-HOC, DEVELOPMENT-ONLY, EXPLORATORY."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).parents[1]))
from common import run, load_fold, dump, ROOT, PARENT
import blocking
from preflight import ground_truth
D = PARENT / 'data_derived/representation'
with run('S1', 'sparse-miss-diagnosis', {'folds': [0, 1, 2, 3], 'baseline': 'sparse matched pairs from original frozen run'}) as rec:
    folds = [load_fold(f) for f in range(4)]
    out = {'per_fold': {}}
    tot = {}; plat = {}; overlap = {}; found_tot = 0; gt_tot = 0
    for f, df in enumerate(folds):
        train = pd.concat([x for g, x in enumerate(folds) if g != f], ignore_index=True)
        vec = blocking.fit_passes(train)
        gt = ground_truth(df)
        n = len(df)
        sp = np.load(D / f'pairs_{f}_sparse_matched.npy')
        have = sp[:, 0].astype(np.int64) * n + sp[:, 1]
        gk = gt[:, 0].astype(np.int64) * n + gt[:, 1]
        miss = gt[~np.isin(gk, have)]
        found_tot += len(gt) - len(miss); gt_tot += len(gt)
        fl = blocking.similarity_flags(df, miss, vec)
        cause = blocking.assign_causes(fl)
        pl = df.platform.to_numpy()
        pp = np.array(['+'.join(sorted((pl[a], pl[b]))) for a, b in miss])
        out['per_fold'][f] = {'ground_truth': int(len(gt)), 'sparse_candidates': int(len(sp)), 'missed': int(len(miss)),
                              'cause': {c: int((cause == c).sum()) for c in 'abcdef'}}
        for c, p in zip(cause, pp):
            tot[c] = tot.get(c, 0) + 1
            plat.setdefault(p, {})
            plat[p][c] = plat[p].get(c, 0) + 1
        flags = {'a_overlap(user>=.85&name<.5)': (fl['u'] >= .85) & (fl['n'] < .5), 'b_overlap(cross>=.85)': fl['cross'] >= .85,
                 'c_overlap(missing)': fl['missing'], 'd_overlap(link)': fl['link'], 'e_overlap(max_text<.2)': fl['max_text'] < .2}
        for k, v in flags.items():
            overlap[k] = overlap.get(k, 0) + int(v.sum())
        print('fold', f, out['per_fold'][f], flush=True)
    out['pooled_cause'] = {c: tot.get(c, 0) for c in 'abcdef'}
    out['pooled_platform_pair'] = plat
    out['pooled_ground_truth'] = gt_tot; out['pooled_found'] = found_tot; out['pooled_missed'] = gt_tot - found_tot
    out['pooled_PC_sparse'] = found_tot / gt_tot
    out['overlapping_flags_not_exclusive'] = overlap
    out['ceiling_PC_excluding_cause_e'] = (gt_tot - tot.get('e', 0)) / gt_tot
    out['note'] = 'causes computed from similarity features only; not human adjudication; e = ceiling for these features only'
    dump(ROOT / 'metrics/step1_miss_causes.json', out)
    rec.update({'summary': out['pooled_cause']})
    print(json.dumps({k: v for k, v in out.items() if k != 'per_fold'}, indent=1))
