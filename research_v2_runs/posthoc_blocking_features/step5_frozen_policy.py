"""STEP 4b: frozen-policy end-to-end recall and recall by miss cause. POST-HOC, DEVELOPMENT-ONLY, EXPLORATORY.
Calibrator (Platt) and Chow policy are the ORIGINAL frozen ones; nothing is refit or retuned."""
import sys, json, pickle
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.metrics import average_precision_score
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).parents[1]))
from common import run, load_fold, dump, ROOT, PARENT
import blocking
from decision_run import apply_calibrator
from preflight import ground_truth
DATA = ROOT / 'data_derived'
meta = np.load(DATA / 'pair_meta.npz'); y, fold, pairs = meta['y'], meta['fold'], meta['pairs']
cal = pickle.load(open(PARENT / 'artifacts/calibrator.pkl', 'rb'))
TOTAL = sum(len(ground_truth(load_fold(f))) for f in range(4))
FEATS = ['F-LEX35', 'H23', 'H23+LEX35']
SEEDS = [11, 23, 42, 71, 101]
with run('S5', 'frozen-policy-and-cause-recall', {'policy': 'Chow cost 2:1:0.1 on frozen Platt calibrator', 'total_positives': TOTAL}) as rec:
    folds = [load_fold(f) for f in range(4)]
    offs = np.cumsum([0] + [len(x) for x in folds])
    cause = np.full(len(y), '-', dtype='<U1')
    for f in range(4):
        df = folds[f]; sel = np.flatnonzero((fold == f) & (y == 1))
        local = pairs[sel] - offs[f]
        train = pd.concat([x for g, x in enumerate(folds) if g != f], ignore_index=True)
        cause[sel] = blocking.assign_causes(blocking.similarity_flags(df, local, blocking.fit_passes(train)))
    out = {'total_positives': int(TOTAL), 'candidate_positives': int(y.sum()), 'positives_by_cause': {c: int(((cause == c)).sum()) for c in 'abcdef'}, 'sets': {}}
    for feat in FEATS:
        z = np.load(DATA / f'oof_{feat}.npz'); per = []
        for s in SEEDS:
            raw = z[str(s)]; p = apply_calibrator(cal, raw)
            risks = np.column_stack([1 * p, np.full(len(p), .1), 2 * (1 - p)])
            d = np.argmin(risks, axis=1)
            tp = int(((d == 2) & (y == 1)).sum()); rv = int(((d == 1) & (y == 1)).sum()); fp = int(((d == 2) & (y == 0)).sum())
            byc = {c: {'n': int((cause == c).sum()), 'auto': int(((d == 2) & (y == 1) & (cause == c)).sum()), 'review': int(((d == 1) & (y == 1) & (cause == c)).sum())} for c in 'abcdef'}
            per.append({'seed': s, 'oof_AP': float(average_precision_score(y, raw)), 'auto_tp': tp, 'auto_fp': fp, 'review_pos': rv, 'review_pairs': int((d == 1).sum()),
                        'end_to_end_auto_recall': tp / TOTAL, 'recall_after_perfect_review': (tp + rv) / TOTAL, 'precision': tp / max(tp + fp, 1), 'by_cause': byc})
        out['sets'][feat] = per
    dump(ROOT / 'metrics/step5_frozen_policy_results.json', out)
    for feat, per in out['sets'].items():
        print(feat, 'AP', np.mean([r['oof_AP'] for r in per]).round(4), 'e2e', np.mean([r['end_to_end_auto_recall'] for r in per]).round(4),
              'review+', np.mean([r['recall_after_perfect_review'] for r in per]).round(4), 'prec', np.mean([r['precision'] for r in per]).round(4))
    print(out['positives_by_cause'])
