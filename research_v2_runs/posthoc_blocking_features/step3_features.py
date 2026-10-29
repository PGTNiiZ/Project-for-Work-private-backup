"""STEP 2 freeze + STEP 3/4 feature matrices on the frozen multipass candidate set.
POST-HOC, DEVELOPMENT-ONLY, EXPLORATORY."""
import sys, json, hashlib
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parent / 'work/history'))
from common import run, load_fold, dump, ROOT, PARENT, rep, digest
import hist_features as H
D = PARENT / 'data_derived/representation'
DATA = ROOT / 'data_derived'
sel = json.loads((ROOT / 'metrics/step2_blocking_comparison.json').read_text())['pooled']
# preregistered rule: highest pooled development PC, ties fewer candidates then name
best = sorted(sel, key=lambda k: (-sel[k]['PC'], sel[k]['candidates'], k))[0]
assert best == 'multipass@2.0x', best
freeze = {'classification': 'POST-HOC, DEVELOPMENT-ONLY, EXPLORATORY', 'selected': best, 'rule': 'highest pooled development PC; ties fewer candidates',
          'pooled': sel, 'candidate_files': {f: digest(DATA / f'multipass_dev_fold{f}_2.0x.npy') for f in range(4)}}
fz = ROOT / 'metrics/blocker_FROZEN.json'
if not fz.exists():
    dump(fz, freeze)
with run('S3', 'feature-matrices', {'candidate_set': best}) as rec:
    folds = [load_fold(f) for f in range(4)]
    all_dev = pd.concat(folds, ignore_index=True)
    offs = np.cumsum([0] + [len(x) for x in folds])
    pairs, fold_id = [], []
    for f in range(4):
        p = np.load(DATA / f'multipass_dev_fold{f}_2.0x.npy').astype(np.int64) + offs[f]
        pairs.append(p); fold_id.append(np.full(len(p), f, np.int8))
    pairs = np.concatenate(pairs).astype(np.int32); fold_id = np.concatenate(fold_id)
    ent = all_dev.entity.to_numpy()
    y = (ent[pairs[:, 0]] == ent[pairs[:, 1]]).astype(np.int8)
    np.savez(DATA / 'pair_meta.npz', pairs=pairs, fold=fold_id, y=y)
    emb_bio = np.concatenate([np.load(D / f'embeddings_{f}.npz')['bio'] for f in range(4)])
    prof = all_dev[['username', 'fullname', 'bio', 'location', 'links', 'platform']].copy()
    prof['bio_mentions'] = ''   # unavailable in development schema: constant (disclosed adaptation)
    for cv in range(4):
        train = all_dev[all_dev.fold.ne(cv)].reset_index(drop=True)
        vec = rep.fit_tfidf(train)
        lex, names, groups = rep.lexical_features(all_dev, pairs, vec)
        bundle = H.fit_text(prof[all_dev.fold.ne(cv).to_numpy()].reset_index(drop=True))
        h23, hnames = H.text_features(prof, pairs, bundle, embeddings=emb_bio)
        np.save(DATA / f'F-LEX35_cv{cv}.npy', lex.astype(np.float32))
        np.save(DATA / f'H23_cv{cv}.npy', h23.astype(np.float32))
        np.save(DATA / f'H23+LEX35_cv{cv}.npy', np.concatenate([h23, lex], axis=1).astype(np.float32))
        print(json.dumps({'cv': cv, 'pairs': len(pairs), 'lex': lex.shape[1], 'h23': h23.shape[1]}), flush=True)
    dump(DATA / 'feature_names.json', {'F-LEX35': names, 'H23': list(hnames), 'H23+LEX35': list(hnames) + names})
    rec.update({'pairs': int(len(pairs)), 'positives': int(y.sum()), 'positives_per_fold': [int(y[fold_id == f].sum()) for f in range(4)],
                'pairs_per_fold': [int((fold_id == f).sum()) for f in range(4)],
                'H23_adaptations': ['bio_mentions constant empty (unavailable)', 'bio embedding = frozen MiniLM not MPNet', 'bio TF-IDF fit on train-dev folds only'],
                'image_columns': 'NOT built: historical-41 BLOCKED (no verifiable dev image linkage)'})
