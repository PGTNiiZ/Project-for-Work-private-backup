import sys, numpy as np
sys.path.insert(0, '.')
import harness as H
from ub_common import ROOT
mine = np.load('data_derived/X_sparse_FLEX35_cv0.npy'); v2 = np.load('../data_derived/representation/lexical_dev_cv0.npy')
m = H.load_meta('sparse'); v2m = np.load('../data_derived/representation/pair_metadata_dev.npz')
print('pairs equal', np.array_equal(m['pairs'], v2m['pairs']), 'y equal', np.array_equal(m['y'], v2m['y']), 'max |dX|', float(np.abs(mine - v2).max()), 'misses', m['misses'].tolist(), 'pos', int(m['y'].sum()))
H.model_job('J_sparse_FLEX35_GBDT', smoke=True)
H.ART = H.METRICS = ROOT / 'work/smoke'; H.SEEDS = (11,)
for r in ['L1_block_sparse', 'L1_rule_genome_GA', 'L1_rule_feature_aware_GA', 'L1_rule_f1max', 'L1_rule_chow']:
    H.eval_row(r)
    import json; d = json.load(open(H.METRICS / f'row_{r}.json'))['result']
    print(r, {k: round(v, 4) for k, v in d['mean'].items()}, d['calibrator_choices'])
