"""STEP 4: GBDT for one feature set. POST-HOC, DEVELOPMENT-ONLY, EXPLORATORY.
usage: step4_train.py <F-LEX35|H23|H23+LEX35> """
import sys, json, pickle
from pathlib import Path
import numpy as np
import optuna
from sklearn.metrics import average_precision_score
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).parents[1]))
from common import run, dump, ROOT, PARENT
from training import fit_estimator, predict
P = json.loads((PARENT / 'protocol.json').read_text())
DATA = ROOT / 'data_derived'
optuna.logging.set_verbosity(optuna.logging.WARNING)
feat = sys.argv[1]
meta = np.load(DATA / 'pair_meta.npz')
y, fold = meta['y'], meta['fold']
X = [np.load(DATA / f'{feat}_cv{c}.npy', mmap_mode='r') for c in range(4)]
names = json.loads((DATA / 'feature_names.json').read_text())[feat]
assert X[0].shape[1] == len(names)
cfg = P['GBDT']


def suggest(t):
    return {'learning_rate': t.suggest_categorical('learning_rate', cfg['learning_rate']), 'max_leaf_nodes': t.suggest_categorical('max_leaf_nodes', cfg['max_leaf_nodes']),
            'max_iter': t.suggest_categorical('max_iter', cfg['max_iter']), 'min_samples_leaf': t.suggest_categorical('min_samples_leaf', cfg['min_samples_leaf']),
            'l2_regularization': t.suggest_float('l2_regularization', *cfg['l2_regularization_log'], log=True)}


Xm = [np.ascontiguousarray(x) for x in X]
with run('S4', f'tune-{feat}', {'feature': feat, 'configs': 200, 'sampler': 'TPE seed42', 'objective': 'mean AP over four held development folds', 'space': cfg}) as rec:
    study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=42))
    trials = []
    for n in range(P['classifier_search_configs']):
        t = study.ask(); params = suggest(t); aps = []
        for f in range(4):
            tr, va = fold != f, fold == f
            m, _ = fit_estimator(Xm[f][tr], y[tr], 'GBDT', params, seed=42)
            aps.append(float(average_precision_score(y[va], predict(m, Xm[f][va]))))
        study.tell(t, float(np.mean(aps)))
        trials.append({'trial': n, 'params': params, 'fold_AP': aps, 'mean_AP': float(np.mean(aps))})
        if n % 25 == 0: print(feat, n, float(np.mean(aps)), flush=True)
    rec.update({'configs_completed': 200, 'tuning_fits': 800, 'best_params': study.best_params, 'best_mean_AP': float(study.best_value), 'trials': trials})
best = study.best_params
oof = {}
with run('S4', f'refit-{feat}', {'feature': feat, 'params': best, 'seeds': P['gbdt_seeds']}) as rec:
    for seed in P['gbdt_seeds']:
        s = np.zeros(len(y))
        for f in range(4):
            tr, va = fold != f, fold == f
            m, _ = fit_estimator(Xm[f][tr], y[tr], 'GBDT', best, seed=seed)
            s[va] = predict(m, Xm[f][va])
            if seed == 42:
                rng = np.random.default_rng(1000 + f)
                idx = np.flatnonzero(va); idx = np.sort(rng.choice(idx, size=min(25000, len(idx)), replace=False))
                base = average_precision_score(y[idx], predict(m, Xm[f][idx]))
                dec = np.zeros((3, Xm[f].shape[1]))
                for j in range(Xm[f].shape[1]):
                    col = Xm[f][idx, j]
                    if np.ptp(Xm[f][:, j]) == 0: continue
                    for r in range(3):
                        Z = Xm[f][idx].copy(); Z[:, j] = np.random.default_rng(7 * r + j).permutation(col)
                        dec[r, j] = base - average_precision_score(y[idx], predict(m, Z))
                oof.setdefault('imp', []).append(dec.mean(0))
        oof[seed] = s
        rec[f'seed{seed}_oof_AP'] = float(average_precision_score(y, s))
        rec[f'seed{seed}_fold_AP'] = [float(average_precision_score(y[fold == f], s[fold == f])) for f in range(4)]
    imp = np.array(oof['imp'])
    rec['importance_mean_AP_drop'] = dict(zip(names, imp.mean(0).tolist())); rec['importance_SD_across_folds'] = dict(zip(names, imp.std(0, ddof=1).tolist()))
    np.savez(DATA / f'oof_{feat}.npz', **{str(s): oof[s] for s in P['gbdt_seeds']})
