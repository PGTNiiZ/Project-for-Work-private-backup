"""Common nested harness: model jobs (tuning + cross-fitted scores) and row evaluation (calibration + rule + metrics).
POST-HOC EXPLORATORY, development folds 0-3 only.
usage: harness.py job <job_id> [--smoke] | harness.py row <row_id>"""
import json
import os
import sys
import time
import numpy as np
from sklearn.metrics import average_precision_score
from ub_common import ART, DATA, METRICS, PARENT, PLAN, ROOT, FOLDS, SEEDS, LABEL, dump_new, run

THREADS = int(os.environ.get('UB_THREADS', '2'))
TOTAL_POS = 23391
COST = (2.0, 1.0, 0.1)
COST_ALT = (5.0, 1.0, 0.02)
GRID = json.loads((PARENT / 'protocol.json').read_text())['threshold_grid']
GBDT_SPACE = json.loads((PARENT / 'protocol.json').read_text())['GBDT']
ALL_PAIRS = sum(r['all_cross_platform_pairs'] for r in json.loads((PARENT / 'metrics/blocking_development.json').read_text())['rows'] if r['method'] == 'B0')


def load_meta(blocker):
    z = np.load(DATA / f'meta_{blocker}.npz')
    return {k: z[k] for k in z.files}


def load_X(blocker, fs, cv):
    return np.load(DATA / f'X_{blocker}_{fs}_cv{cv}.npy')


# ---------------------------------------------------------------- learners
def suggest(trial, learner):
    s = trial.suggest_categorical; fl = trial.suggest_float
    if learner == 'GBDT':
        c = GBDT_SPACE
        return dict(learning_rate=s('learning_rate', c['learning_rate']), max_leaf_nodes=s('max_leaf_nodes', c['max_leaf_nodes']),
                    max_iter=s('max_iter', c['max_iter']), min_samples_leaf=s('min_samples_leaf', c['min_samples_leaf']),
                    l2_regularization=fl('l2_regularization', *c['l2_regularization_log'], log=True))
    if learner in ('LR', 'LinearSVM'):
        return dict(C=fl('C', 1e-3, 100, log=True), class_weight=s('class_weight', [None, 'balanced']))
    if learner in ('RF', 'ExtraTrees'):
        return dict(n_estimators=s('n_estimators', [200, 400]), max_depth=s('max_depth', [8, 12, 18, None]),
                    min_samples_leaf=s('min_samples_leaf', [1, 5, 20]), max_features=s('max_features', ['sqrt', 0.5]))
    if learner == 'MLP':
        return dict(hidden=s('hidden', ['64', '128-64', '256-128-64']), alpha=fl('alpha', 1e-6, 1e-2, log=True),
                    learning_rate_init=fl('learning_rate_init', 1e-4, 1e-2, log=True))
    if learner == 'AdaBoost':
        return dict(n_estimators=s('n_estimators', [50, 100, 200]), learning_rate=fl('learning_rate', 0.05, 1.5, log=True))
    raise ValueError(learner)


def _subsample(y, seed):
    rng = np.random.default_rng(seed)
    pos = np.flatnonzero(y == 1); neg = np.flatnonzero(y == 0)
    neg = rng.choice(neg, size=min(len(neg), 3 * len(pos)), replace=False)
    return np.sort(np.r_[pos, neg])


class Fitted:
    def __init__(self, model, kind):
        self.model, self.kind = model, kind

    def score(self, X):
        if self.kind == 'svm':
            return self.model.decision_function(X).astype(np.float64)
        if self.kind == 'torch':
            import torch
            self.model.eval()
            with torch.no_grad():
                return self.model(torch.tensor(X, dtype=torch.float32)).numpy().astype(np.float64)   # logits
        p = np.clip(self.model.predict_proba(X)[:, 1].astype(np.float64), 1e-7, 1 - 1e-7)
        return np.log(p / (1 - p))


def fit(learner, params, X, y, seed, groups=None):
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    ix = _subsample(y, seed)
    Xs, ys = np.asarray(X[ix], np.float32), y[ix]
    if learner == 'GBDT':
        from sklearn.ensemble import HistGradientBoostingClassifier
        m = HistGradientBoostingClassifier(**params, early_stopping=False, random_state=seed); kind = 'prob'
    elif learner == 'GBfixed':
        from sklearn.ensemble import HistGradientBoostingClassifier
        m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_depth=6, max_leaf_nodes=None, early_stopping=False, random_state=seed); kind = 'prob'
    elif learner == 'LR':
        from sklearn.linear_model import LogisticRegression
        m = make_pipeline(StandardScaler(), LogisticRegression(**params, max_iter=500, random_state=seed)); kind = 'prob'
    elif learner == 'LinearSVM':
        from sklearn.svm import LinearSVC
        m = make_pipeline(StandardScaler(), LinearSVC(**params, max_iter=5000, random_state=seed)); kind = 'svm'
    elif learner == 'RF':
        from sklearn.ensemble import RandomForestClassifier
        m = RandomForestClassifier(**params, n_jobs=THREADS, random_state=seed); kind = 'prob'
    elif learner == 'ExtraTrees':
        from sklearn.ensemble import ExtraTreesClassifier
        m = ExtraTreesClassifier(**params, n_jobs=THREADS, random_state=seed); kind = 'prob'
    elif learner == 'MLP':
        from sklearn.neural_network import MLPClassifier
        hid = tuple(int(x) for x in params['hidden'].split('-'))
        m = make_pipeline(StandardScaler(), MLPClassifier(hid, alpha=params['alpha'], learning_rate_init=params['learning_rate_init'],
                                                          max_iter=100, early_stopping=True, validation_fraction=0.1, random_state=seed)); kind = 'prob'
    elif learner == 'AdaBoost':
        from sklearn.ensemble import AdaBoostClassifier
        m = AdaBoostClassifier(**params, random_state=seed); kind = 'prob'
    elif learner == 'IdentityMLP':
        return Fitted(_fit_identity_mlp(Xs, ys, seed, None if groups is None else groups[ix]), 'torch')
    else:
        raise ValueError(learner)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        m.fit(Xs, ys)
    return Fitted(m, kind)


def _fit_identity_mlp(X, y, seed, groups):
    """R2/R3 IdentityMLP with original hyperparameters; early stopping on a 15% entity-hash slice of the training rows."""
    import torch
    from torch import nn
    torch.manual_seed(seed); np.random.seed(seed); torch.set_num_threads(THREADS)
    hold = (groups * 2654435761 + seed) % 100 < 15
    mu, sd = X[~hold].mean(0), X[~hold].std(0) + 1e-6

    class Net(nn.Module):
        def __init__(self, d):
            super().__init__()
            layers, prev = [], d
            for h in (256, 128, 64):
                layers += [nn.Linear(prev, h), nn.BatchNorm1d(h), nn.ReLU(), nn.Dropout(0.3)]; prev = h
            layers.append(nn.Linear(prev, 1)); self.net = nn.Sequential(*layers)
            self.register_buffer('mu', torch.tensor(mu)); self.register_buffer('sd', torch.tensor(sd))

        def forward(self, x):
            return self.net((x - self.mu) / self.sd).squeeze(-1)
    model = Net(X.shape[1])
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=30)
    Xt, yt = torch.tensor(X[~hold]), torch.tensor(y[~hold].astype(np.float32))
    Xv, yv = torch.tensor(X[hold]), y[hold]
    bce = nn.BCEWithLogitsLoss(reduction='none')
    best, state, patience = -1, None, 5
    gen = torch.Generator().manual_seed(seed)
    for epoch in range(30):
        model.train()
        order = torch.randperm(len(yt), generator=gen)
        for s in range(0, len(order), 8192):
            ix = order[s:s + 8192]
            if len(ix) < 2:
                continue
            logits = model(Xt[ix]); t = yt[ix]
            p = torch.sigmoid(logits); pt = torch.where(t == 1, p, 1 - p)
            at = torch.where(t == 1, torch.full_like(t, .25), torch.full_like(t, .75))
            loss = (at * (1 - pt) ** 2 * bce(logits, t)).mean()
            opt.zero_grad(); loss.backward(); opt.step()
        sched.step()
        model.eval()
        with torch.no_grad():
            ap = average_precision_score(yv, model(Xv).numpy())
        if ap > best:
            best, state, patience = ap, {k: v.clone() for k, v in model.state_dict().items()}, 5
        else:
            patience -= 1
            if patience <= 0:
                break
    model.load_state_dict(state)
    return model


# ---------------------------------------------------------------- model job
def model_job(job_id, smoke=False):
    cfg = PLAN['model_jobs'][job_id]
    blocker, fs, learner = cfg['blocker'], cfg['features'], cfg['learner']
    tuned = cfg['tuning'] == 'TPE200'
    n_configs = 2 if smoke else 200
    seeds = SEEDS[:1] if smoke else SEEDS
    out_npz = (ROOT / 'work/smoke' if smoke else ART) / f'scores_{job_id}.npz'
    out_json = (ROOT / 'work/smoke' if smoke else METRICS) / f'job_{job_id}.json'
    if out_npz.exists() or out_json.exists():
        raise FileExistsError('append-only: job already ran')
    out_npz.parent.mkdir(parents=True, exist_ok=True)
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    meta = load_meta(blocker); y, fold = meta['y'], meta['fold']
    import pandas as pd
    from ub_common import all_dev
    _, dev, _ = all_dev()
    groups = dev.entity.astype('category').cat.codes.to_numpy().astype(np.int64)[meta['pairs'][:, 0]]
    arrays, info = {}, {'job': job_id, 'config': cfg, 'classification': LABEL, 'smoke': smoke, 'folds': {}}
    with run('job' if not smoke else 'smoke-job', job_id) as rec:
        for s in seeds:
            arrays[f'outer_{s}'] = np.full(len(y), np.nan, np.float32)
        for f in FOLDS:
            t0 = time.monotonic()
            X = load_X(blocker, fs, f)
            T = [g for g in FOLDS if g != f]; c = (f + 1) % 4; A = [g for g in T if g != c]
            rA, rc = np.isin(fold, A), fold == c
            params, trials = {}, []
            if tuned:
                study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=42))
                for _ in range(n_configs):
                    tr = study.ask(); prm = suggest(tr, learner)
                    m = fit(learner, prm, X[rA], y[rA], 42, groups[rA])
                    ap = float(average_precision_score(y[rc], m.score(X[rc])))
                    study.tell(tr, ap); trials.append(ap)
                params = study.best_params
            for s in seeds:
                inner = np.full(len(y), np.nan, np.float32)
                for g in T:
                    tr_rows = np.isin(fold, [h for h in T if h != g])
                    m = fit(learner, params, X[tr_rows], y[tr_rows], s, groups[tr_rows])
                    inner[fold == g] = m.score(X[fold == g])
                arrays[f'inner_{s}_{f}'] = inner
                m = fit(learner, params, X[np.isin(fold, T)], y[np.isin(fold, T)], s, groups[np.isin(fold, T)])
                arrays[f'outer_{s}'][fold == f] = m.score(X[fold == f])
            info['folds'][f] = {'selection_fold': c, 'best_params': params, 'best_inner_AP': max(trials) if trials else None,
                                'configs': len(trials), 'seconds': time.monotonic() - t0}
            print(job_id, 'fold', f, 'done', round(time.monotonic() - t0), 's', flush=True)
        np.savez_compressed(out_npz, **arrays)
        info['candidate_AP_per_seed'] = {s: float(average_precision_score(y, arrays[f'outer_{s}'])) for s in seeds}
        info['score_sha256'] = __import__('ub_common').digest(out_npz)
        rec['candidate_AP_per_seed'] = info['candidate_AP_per_seed']
    info['runtime_seconds'] = rec['runtime_seconds']
    dump_new(out_json, info)


# ---------------------------------------------------------------- calibration
def _cal_fit(method, s, y):
    from sklearn.isotonic import IsotonicRegression
    from sklearn.linear_model import LogisticRegression
    if method == 'isotonic':
        return IsotonicRegression(out_of_bounds='clip', y_min=0, y_max=1).fit(s, y)
    return LogisticRegression(C=1e6, max_iter=1000).fit(s[:, None], y)


def _cal_apply(model, s):
    from sklearn.isotonic import IsotonicRegression
    p = model.predict(s) if isinstance(model, IsotonicRegression) else model.predict_proba(s[:, None])[:, 1]
    return np.clip(p, 0, 1)


def choose_calibrator(s, y, fold, A):
    a1, a2 = A
    brier = {}
    for m in ('platt', 'isotonic'):
        tot = 0.0
        for fit_f, ev_f in ((a1, a2), (a2, a1)):
            cal = _cal_fit(m, s[fold == fit_f], y[fold == fit_f])
            p = _cal_apply(cal, s[fold == ev_f]); tot += float(((p - y[fold == ev_f]) ** 2).sum())
        brier[m] = tot / int(np.isin(fold, A).sum())
    best = 'platt' if brier['platt'] <= brier['isotonic'] else 'isotonic'
    rows = np.isin(fold, A)
    return best, _cal_fit(best, s[rows], y[rows]), brier


# ---------------------------------------------------------------- rules
def _dual_cost(p, y, points, cost, misses):
    order = np.argsort(p, kind='stable'); sy = y[order]; sp = p[order]
    cpos = np.r_[0, np.cumsum(sy)]; cneg = np.r_[0, np.cumsum(1 - sy)]
    left = np.searchsorted(sp, points[:, 0], side='left'); right = np.searchsorted(sp, points[:, 1], side='left')
    return cost[0] * (cneg[-1] - cneg[right]) + cost[1] * (cpos[left] + misses) + cost[2] * (right - left)


def _dual(points):
    return {'type': 'dual', 't_review': float(points[0]), 't_match': float(points[1])}


GROUP_COLS = {'name': [1, 4, 8, 11], 'bio': [15, 18], 'url': [28, 29, 32], 'location': [22, 25]}
GROUP_AVAIL = {'name': [5, 12], 'bio': [19], 'url': [33], 'location': [26]}


def group_scores(Xlex, p):
    S = [p]; M = [np.ones(len(p))]
    for g in ('name', 'bio', 'url', 'location'):
        S.append(np.clip(Xlex[:, GROUP_COLS[g]].max(1), 0, 1)); M.append((Xlex[:, GROUP_AVAIL[g]].max(1) > 0).astype(float))
    return np.column_stack(S), np.column_stack(M)


def fa_decide(S, M, g):
    tm, tr, w = g[0], g[1], g[2:]
    num = (S * M * w).sum(1); den = (M * w).sum(1)
    comb = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
    eff = den > 0
    d = np.ones(len(comb), np.int8)
    d[eff & (comb < tr)] = 0; d[eff & (comb >= tm)] = 2
    return d


def _decision_cost(d, y, cost, misses):
    return cost[0] * ((d == 2) & (y == 0)).sum() + cost[1] * (((d == 0) & (y == 1)).sum() + misses) + cost[2] * (d == 1).sum()


def fa_ga(S, M, y, seed, misses, budget=2048):
    rng = np.random.default_rng(seed)

    def clipg(g):
        g = np.clip(g, 0, 1); g[1] = min(g[1], g[0]); return g
    seen = []
    def obj(g):
        seen.append(1); return float(_decision_cost(fa_decide(S, M, g), y, COST, misses))
    pop = [clipg(rng.random(7)) for _ in range(64)]; vals = [obj(g) for g in pop]
    while len(seen) < budget:
        ids = np.argsort(vals, kind='stable')[:12]; el = [pop[i] for i in ids]; ev = [vals[i] for i in ids]
        kids = []
        for _ in range(min(52, budget - len(seen))):
            a, b = rng.integers(0, 12, 2)
            ch = np.where(rng.random(7) < .5, el[a], el[b]); kids.append(clipg(ch + (rng.random(7) < .4) * rng.normal(0, .05, 7)))
        vals = ev + [obj(g) for g in kids]; pop = el + kids
    return pop[int(np.argmin(vals))], len(seen)


def tune_rule(rule, p, y, nsim, misses, seed, extra=None):
    from analysis_tools import optimize_policy
    from decision_run import pure_dual_search
    if rule == 'three_way':
        r = pure_dual_search(p, y, seed, 2048, COST, misses); return {'type': 'dual', 't_review': r['t_review'], 't_match': r['t_match']}, 2048
    if rule == 'dual_sobol':
        from scipy.stats import qmc
        pts = np.sort(qmc.Sobol(2, scramble=False).random_base2(11), axis=1)
        return _dual(pts[int(np.argmin(_dual_cost(p, y, pts, COST, misses)))]), 2048
    if rule.startswith('genome_'):
        method = {'genome_GA': 'ga', 'genome_GA_5_1_002': 'ga', 'genome_sobol': 'scrambled_sobol', 'genome_TPE': 'tpe', 'genome_random': 'random'}[rule]
        cost = COST_ALT if rule == 'genome_GA_5_1_002' else COST
        r = optimize_policy(p, nsim, y, method, seed, 2048, cost=cost, misses=misses)
        return {'type': 'genome', 'genome': r['genome']}, r['evaluations']
    if rule == 'f1max':
        best, bt = -1, None
        P = int(y.sum()) + misses
        for t in GRID:
            tp = int(((p >= t) & (y == 1)).sum()); fp = int(((p >= t) & (y == 0)).sum())
            f1 = 2 * tp / max(2 * tp + fp + (P - tp), 1)
            if f1 > best:
                best, bt = f1, t
        return {'type': 'threshold', 'threshold': bt}, len(GRID)
    if rule == 'feature_aware_GA':
        S, M = extra
        g, n = fa_ga(S, M, y, seed, misses); return {'type': 'fa', 'genome': g.tolist()}, n
    fixed = {'manual_098_095': {'type': 'dual', 't_match': .98, 't_review': .95}, 'stage18': {'type': 'genome', 'genome': [.98, .95, .9, .7]},
             'fixed_05': {'type': 'threshold', 'threshold': .5}, 'closed_cost': {'type': 'threshold', 'threshold': 2 / 3}, 'chow': {'type': 'chow'}}
    return fixed[rule], 0


def apply_rule(spec, p, nsim, extra=None):
    from analysis_tools import decide
    t = spec['type']
    if t == 'threshold':
        return (p >= spec['threshold']).astype(np.int8) * 2
    if t == 'dual':
        return np.where(p >= spec['t_match'], 2, np.where(p >= spec['t_review'], 1, 0)).astype(np.int8)
    if t == 'genome':
        return decide(p, nsim, spec['genome'])
    if t == 'chow':
        return np.argmin(np.column_stack([COST[1] * p, np.full(len(p), COST[2]), COST[0] * (1 - p)]), 1).astype(np.int8)
    if t == 'fa':
        return fa_decide(*extra, np.array(spec['genome']))
    raise ValueError(t)


# ---------------------------------------------------------------- row evaluation
def summarize(d, y, scores):
    tp = int(((d == 2) & (y == 1)).sum()); fp = int(((d == 2) & (y == 0)).sum())
    rev = int((d == 1).sum()); revpos = int(((d == 1) & (y == 1)).sum())
    fn_util = TOTAL_POS - tp - revpos
    out = dict(candidate_AP=float(average_precision_score(y, scores)), auto_recall=tp / TOTAL_POS, recall_perfect_review=(tp + revpos) / TOTAL_POS,
               auto_precision=tp / max(tp + fp, 1), false_merges=fp, review=rev, review_positives=revpos, auto_tp=tp)
    for name, w in (('2_1_0.1', COST), ('5_1_0.02', COST_ALT)):
        c = w[0] * fp + w[1] * fn_util + w[2] * rev
        out[f'cost_{name}'] = c; out[f'cost_per_pair_{name}'] = c / ALL_PAIRS
    return out


def eval_row(row_id):
    row = next(r for r in PLAN['rows'] if r['id'] == row_id)
    out = METRICS / f'row_{row_id}.json'
    if out.exists():
        raise FileExistsError('append-only')
    with run('row', row_id) as rec:
        if row.get('metrics_only') == 'PC':
            summ = json.loads((DATA / 'candidates_summary.json').read_text())['pc']
            b = row_id.split('_', 2)[2]
            res = {'PC_2x': summ[f'{b}@2.0x'], 'PC_1x': summ[f'{b}@1.0x']}
        else:
            if row.get('alias_of'):
                src = METRICS / f'row_{row["alias_of"]}.json'
                res = {'alias_of': row['alias_of'], 'note': 'identical configuration; metrics read from the aliased row', 'source_sha256': __import__('ub_common').digest(src)}
            else:
                job = PLAN['model_jobs'][row['model_job']]
                meta = load_meta(job['blocker']); y, fold, nsim, misses, exact = meta['y'], meta['fold'], meta['nsim'], meta['misses'], meta['exact']
                z = np.load(ART / f'scores_{row["model_job"]}.npz')
                use_exact = bool(row.get('exact_tier'))
                fa = row['rule'] == 'feature_aware_GA'
                per_seed, choices = {}, []
                for s in SEEDS:
                    d_all = np.zeros(len(y), np.int8); outer = z[f'outer_{s}'].astype(np.float64)
                    specs = {}
                    for f in FOLDS:
                        T = [g for g in FOLDS if g != f]; c = (f + 1) % 4; A = [g for g in T if g != c]
                        inner = z[f'inner_{s}_{f}'].astype(np.float64)
                        meth, cal, brier = choose_calibrator(inner, y, fold, A)
                        choices.append(meth)
                        rc = (fold == c) & (~exact if use_exact else True)
                        rf = fold == f
                        pc_ = _cal_apply(cal, inner[rc]); pf = _cal_apply(cal, outer[rf])
                        ec = ef = None
                        if fa:
                            Xc = load_X('sparse', 'FLEX35', f)
                            ec = group_scores(Xc[rc], pc_); ef = group_scores(Xc[rf], pf)
                        spec, n_eval = tune_rule(row['rule'], pc_, y[rc], nsim[rc], int(misses[c]), s, ec)
                        d = apply_rule(spec, pf, nsim[rf], ef)
                        if use_exact:
                            d[exact[rf]] = 2
                        d_all[rf] = d
                        specs[f] = {'calibrator': meth, 'brier': brier, 'rule': spec, 'rule_evaluations': n_eval}
                    per_seed[s] = {**summarize(d_all, y, outer), 'folds': specs}
                keys = [k for k in per_seed[SEEDS[0]] if k != 'folds']
                res = {'mean': {k: float(np.mean([per_seed[s][k] for s in SEEDS])) for k in keys},
                       'sd': {k: float(np.std([per_seed[s][k] for s in SEEDS], ddof=1)) for k in keys},
                       'PC': float(y.sum()) / TOTAL_POS, 'candidates': int(len(y)), 'calibrator_choices': {m: choices.count(m) for m in set(choices)},
                       'per_seed': per_seed}
        rec_out = {'row': row, 'classification': LABEL, 'result': res}
    rec_out['runtime_seconds'] = rec['runtime_seconds']
    dump_new(out, rec_out)


if __name__ == '__main__':
    if sys.argv[1] == 'job':
        model_job(sys.argv[2], smoke='--smoke' in sys.argv)
    else:
        eval_row(sys.argv[2])
