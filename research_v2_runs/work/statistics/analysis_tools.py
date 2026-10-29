"""Array-only Round4 policies and paired identity-cluster inference.

Genome order is (t_match, t_review, c_promote, c_demote). No data access.
Optional optimizer dependencies are imported only by their optimizer.
"""
import math
import numpy as np
from numba import njit


def _vector(x, name, n=None, probability=False):
    x = np.asarray(x)
    if x.ndim != 1 or (n is not None and len(x) != n):
        raise ValueError(f'{name} must be a matched one-dimensional array')
    if not np.all(np.isfinite(x)):
        raise ValueError(f'{name} must be finite')
    if probability and np.any((x < 0) | (x > 1)):
        raise ValueError(f'{name} must lie in [0,1]')
    return np.ascontiguousarray(x)


def _labels(y, n=None):
    y = _vector(y, 'y', n)
    if np.any((y != 0) & (y != 1)):
        raise ValueError('y must be binary')
    return y.astype(np.int8)


def _cost(cost):
    c = np.asarray(cost, dtype=float)
    if c.shape != (3,) or not np.all(np.isfinite(c)) or np.any(c < 0):
        raise ValueError('cost must contain nonnegative finite FP,FN,REVIEW weights')
    return c


def clip_gene(g):
    """Historical sequential clipping, without modifying the input."""
    g = np.asarray(g, dtype=float)
    if g.shape != (4,) or not np.all(np.isfinite(g)):
        raise ValueError('genome must contain four finite values')
    tm = np.clip(g[0], .9, .999)
    tr = np.clip(g[1], .5, tm)
    cp = np.clip(g[2], .5, 1.)
    cd = np.clip(g[3], 0., cp)
    return np.array([tm, tr, cp, cd])


def decide(prob, nsim, g):
    p = _vector(prob, 'prob', probability=True)
    n = _vector(nsim, 'nsim', len(p), probability=True)
    tm, tr, cp, cd = clip_gene(g)
    d = np.zeros(len(p), dtype=np.int8)
    band = (p >= tr) & (p < tm)
    d[band] = 1
    d[band & (n < cd)] = 0
    d[(p >= tm) | (band & (n >= cp))] = 2
    return d


@njit(cache=True)
def _policy_cost(p, n, y, g, c, misses):
    fp = 0
    fn = 0
    review = 0
    for i in range(len(p)):
        d = 0
        if p[i] >= g[0]:
            d = 2
        elif p[i] >= g[1]:
            if n[i] >= g[2]:
                d = 2
            elif n[i] >= g[3]:
                d = 1
        if d == 2:
            fp += y[i] == 0
        elif d == 0:
            fn += y[i] == 1
        else:
            review += 1
    return c[0]*fp + c[1]*(fn + misses) + c[2]*review


def _from_unit(u):
    return clip_gene(np.array([.9, .5, .5, 0.]) + u * np.array([.099, .499, .5, 1.]))


def optimize_policy(prob, nsim, y, method, seed, budget=2048,
                    cost=(2, 1, .1), misses=0):
    """Exact objective-call budget; inherited GA elites retain their scores.

    Duplicate proposals count as calls; unique_evaluations counts exact genomes.
    """
    p = _vector(prob, 'prob', probability=True)
    n = _vector(nsim, 'nsim', len(p), probability=True)
    y = _labels(y, len(p))
    c = _cost(cost)
    if int(budget) != budget or budget < 1:
        raise ValueError('budget must be a positive integer')
    budget = int(budget)
    if not np.isfinite(misses) or misses < 0:
        raise ValueError('misses must be nonnegative')
    rng = np.random.default_rng(seed)
    seen, history = set(), []
    best, best_g = float('inf'), None

    def objective(g):
        nonlocal best, best_g
        g = clip_gene(g)
        seen.add(tuple(g))
        value = float(_policy_cost(p, n, y, g, c, float(misses)))
        if value < best:
            best, best_g = value, g.copy()
        history.append(best)
        return value

    method = method.lower()
    if method in ('random', 'scrambled_sobol', 'sobol'):
        if method == 'random':
            points = rng.random((budget, 4))
        else:
            from scipy.stats import qmc
            points = qmc.Sobol(4, scramble=True, seed=seed).random_base2(
                int(math.ceil(math.log2(budget))))[:budget]
        for point in points:
            objective(_from_unit(point))
    elif method == 'tpe':
        import optuna
        previous = optuna.logging.get_verbosity()
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        try:
            study = optuna.create_study(direction='minimize',
                                       sampler=optuna.samplers.TPESampler(seed=seed))
            def trial_objective(trial):
                return objective([trial.suggest_float('t_match', .9, .999),
                                  trial.suggest_float('t_review', .5, .999),
                                  trial.suggest_float('c_promote', .5, 1.),
                                  trial.suggest_float('c_demote', 0., 1.)])
            study.optimize(trial_objective, n_trials=budget, show_progress_bar=False)
        finally:
            optuna.logging.set_verbosity(previous)
    elif method == 'ga':
        pop = [_from_unit(u) for u in rng.random((min(64, budget), 4))]
        values = [objective(g) for g in pop]
        while len(history) < budget:
            elite_ids = np.argsort(values, kind='stable')[:12]
            elites = [pop[i] for i in elite_ids]
            elite_values = [values[i] for i in elite_ids]
            children = []
            for _ in range(min(64 - len(elites), budget - len(history))):
                a, b = rng.integers(0, len(elites), 2)
                child = np.where(rng.random(4) < .5, elites[a], elites[b])
                child = clip_gene(child + (rng.random(4) < .4) * rng.normal(0, .05, 4))
                children.append(child)
            values = elite_values + [objective(g) for g in children]
            pop = elites + children
    else:
        raise ValueError(f'unknown optimizer: {method}')
    return dict(genome=best_g.tolist(), cost=best, evaluations=len(history),
                unique_evaluations=len(seen), history=history)


def _decisions(d, n):
    d = _vector(d, 'decision', n)
    if np.any((d != 0) & (d != 1) & (d != 2)):
        raise ValueError('decisions must use codes 0,1,2')
    return d.astype(np.int8)


def _ap_order(score):
    order = np.argsort(-score, kind='stable')
    ends = np.r_[np.flatnonzero(np.diff(score[order]) != 0), len(score)-1]
    return order, ends.astype(np.int64)


@njit(cache=True)
def _weighted_ap(y, weight, order, ends):
    tp, mass, numerator, start = 0., 0., 0., 0
    for end in ends:
        group_tp = 0.
        for j in range(start, end+1):
            i = order[j]
            mass += weight[i]
            group_tp += weight[i] * y[i]
        tp += group_tp
        if mass > 0:
            numerator += group_tp * tp / mass
        start = end+1
    return numerator/tp if tp > 0 else 0.


def metrics(y, score, decision=None, total_positives=None, n_profiles=None,
            cost=(2, 1, .1)):
    """Candidate discrimination and automatic-link metrics, separate from utility.

    cost_per_pair denominator is candidate rows plus absent positive pairs.
    n_profiles optionally adds cost_per_profile, never changes pair denominator.
    """
    y = _labels(y)
    s = _vector(score, 'score', len(y), probability=True).astype(float)
    d = (s >= .5).astype(np.int8)*2 if decision is None else _decisions(decision, len(y))
    c = _cost(cost)
    positives = int(y.sum())
    total = positives if total_positives is None else total_positives
    if not np.isfinite(total) or total < positives or int(total) != total:
        raise ValueError('total_positives must be an integer >= candidate positives')
    misses = int(total)-positives
    tp = int(np.sum((d == 2) & (y == 1)))
    fp = int(np.sum((d == 2) & (y == 0)))
    rejected = int(np.sum((d == 0) & (y == 1)))
    review = int(np.sum(d == 1))
    precision = tp/(tp+fp) if tp+fp else 0.
    recall = tp/positives if positives else 0.
    raw = c[0]*fp + c[1]*(rejected+misses) + c[2]*review
    ece = 0.
    if len(y):
        for idx in np.array_split(np.argsort(s, kind='stable'), min(15, len(y))):
            ece += len(idx)/len(y) * abs(float(y[idx].mean()-s[idx].mean()))
        ap = float(_weighted_ap(y, np.ones(len(y)), *_ap_order(s)))
    else:
        ap = 0.
    out = dict(candidate_ap=ap, precision=precision, recall=recall,
               f1=2*precision*recall/(precision+recall) if precision+recall else 0.,
               tp=tp, fp=fp, tn=int(np.sum((d == 0) & (y == 0))),
               fn=positives-tp, automatic_fn=positives-tp+misses,
               utility_fn=rejected+misses, rejected_positive_fn=rejected,
               workflow_misses=misses, candidate_positives=positives,
               total_positives=int(total), n_pairs=len(y), review=review,
               review_positives=int(np.sum((d == 1) & (y == 1))),
               review_rate=review/len(y) if len(y) else 0.,
               end_to_end_recall=tp/total if total else 0.,
               raw_cost=float(raw), cost_per_pair=float(raw)/(len(y)+misses) if len(y)+misses else 0.,
               brier=float(np.mean((s-y)**2)) if len(y) else 0., ece15_equalmass=float(ece))
    if n_profiles is not None:
        if not np.isfinite(n_profiles) or n_profiles <= 0:
            raise ValueError('n_profiles must be positive')
        out['cost_per_profile'] = float(raw)/n_profiles
    return out


@njit(cache=True)
def _edge_weights(y, ea, eb, counts):
    w = np.empty(len(y), dtype=np.float64)
    for i in range(len(y)):
        w[i] = counts[ea[i]] if y[i] == 1 else float(counts[ea[i]])*counts[eb[i]]
    return w


@njit(cache=True)
def _contrast_value(y, sa, sb, ea, eb, counts, kind, oa, ta, ob, tb, missed, fn_cost):
    w = _edge_weights(y, ea, eb, counts)
    if kind == 0:
        return _weighted_ap(y, w, oa, ta)-_weighted_ap(y, w, ob, tb)
    mass, a, b = 0., 0., 0.
    for i in range(len(w)):
        mass += w[i]
        a += w[i]*sa[i]
        b += w[i]*sb[i]
    if kind == 1:
        return (a-b)/mass if mass > 0 else np.nan
    for entity in missed:
        a += counts[entity]*fn_cost
        b += counts[entity]*fn_cost
    return (b-a)/b if b > 0 else np.nan


def _entities(x, name, n_entities, n=None):
    x = _vector(x, name, n)
    if np.any(x != np.floor(x)) or np.any((x < 0) | (x >= n_entities)):
        raise ValueError(f'{name} must contain local integer entity IDs')
    return x.astype(np.int64)


def _pair_cost(y, decisions, found, cost):
    d = _decisions(decisions, len(y))
    values = np.where(d == 1, cost[2],
                      np.where((d == 2) & (y == 0), cost[0],
                               np.where((d == 0) & (y == 1), cost[1], 0.)))
    if found is not None:
        f = _labels(found, len(y)).astype(bool)
        values = np.where(f, values, y*cost[1])
    return values


def bootstrap_contrast(y, score_a, score_b, entity_a, entity_b, n_entities,
                       kind='ap', decisions_a=None, decisions_b=None,
                       found_a=None, found_b=None, B=10000, seed=4242,
                       se_soi=.02, cost=(2, 1, .1), missed_entity=None):
    """Paired fixed-n identity pigeonhole bootstrap on aligned pair arrays.

    AP/PC delta is A-B. Cost delta is (B-A)/B (A=GA, B=baseline).
    Positive edges must have identical entity endpoints; negatives use products
    of both endpoint multiplicities. Inputs must already be a unique aligned
    union of profile pairs: entity endpoint pairs are NOT profile-pair IDs and
    cannot be used to deduplicate rows.

    Cost: either pass nonnegative per-pair costs in scores, or both decisions.
    In decision mode found=False means absent candidate (positive costs FN).
    missed_entity is one entity ID per additional positive absent from BOTH
    aligned workflows; do not repeat misses already represented by union rows.
    Common normalizing pair mass cancels in the relative cost contrast.

    Degenerate AP draws without positives have AP=0; PC/cost draws with zero
    denominator are undefined and omitted, with effective_B reported explicitly.
    No exact TOST p-value is claimed; equivalence uses the 90% percentile CI.
    """
    if int(n_entities) != n_entities or n_entities < 1:
        raise ValueError('n_entities must be a positive integer')
    n_entities = int(n_entities)
    if int(B) != B or B < 1:
        raise ValueError('B must be a positive integer')
    B = int(B)
    if not np.isfinite(se_soi) or se_soi < 0:
        raise ValueError('se_soi must be finite and nonnegative')
    y = _labels(y)
    if len(y) == 0:
        raise ValueError('bootstrap requires at least one pair')
    sa = _vector(score_a, 'score_a', len(y)).astype(float)
    sb = _vector(score_b, 'score_b', len(y)).astype(float)
    ea = _entities(entity_a, 'entity_a', n_entities, len(y))
    eb = _entities(entity_b, 'entity_b', n_entities, len(y))
    if np.any((y == 1) & (ea != eb)):
        raise ValueError('positive edges must be within one identity')
    c = _cost(cost)
    kind = kind.lower()
    if kind not in ('ap', 'pc', 'cost'):
        raise ValueError('kind must be ap, pc, or cost')
    missed = np.empty(0, dtype=np.int64) if missed_entity is None else _entities(
        missed_entity, 'missed_entity', n_entities)
    if kind != 'cost' and len(missed):
        raise ValueError('missed_entity applies only to cost')
    if kind == 'pc':
        if not np.all(y == 1):
            raise ValueError('PC requires all ground-truth positive pairs')
        sa = _labels(sa if found_a is None else found_a, len(y)).astype(float)
        sb = _labels(sb if found_b is None else found_b, len(y)).astype(float)
    if kind == 'cost':
        if (decisions_a is None) != (decisions_b is None):
            raise ValueError('provide decisions for both workflows or neither')
        if decisions_a is not None:
            sa = _pair_cost(y, decisions_a, found_a, c)
            sb = _pair_cost(y, decisions_b, found_b, c)
        elif found_a is not None or found_b is not None:
            raise ValueError('found masks in cost mode require decisions')
        if np.any(sa < 0) or np.any(sb < 0):
            raise ValueError('per-pair costs must be nonnegative')
    oa, ta = _ap_order(sa)
    ob, tb = _ap_order(sb)
    code = {'ap': 0, 'pc': 1, 'cost': 2}[kind]
    ones = np.ones(n_entities, dtype=np.int64)
    args = (y, sa, sb, ea, eb)
    tail = (code, oa, ta, ob, tb, missed, float(c[1]))
    delta = float(_contrast_value(*args, ones, *tail))
    if not np.isfinite(delta):
        raise ValueError('point contrast undefined: zero denominator')
    rng = np.random.default_rng(seed)
    values = np.empty(B)
    # Stream draws: memory is O(n_pairs+n_entities), not O(B*n_entities).
    for i in range(B):
        counts = np.bincount(rng.integers(0, n_entities, n_entities), minlength=n_entities)
        values[i] = _contrast_value(*args, counts, *tail)
    valid = values[np.isfinite(values)]
    if not len(valid):
        raise ValueError('all bootstrap contrasts undefined')
    ci95 = np.quantile(valid, [.025, .975]).tolist()
    ci90 = np.quantile(valid, [.05, .95]).tolist()
    p = (1+int(np.sum(np.abs(valid-delta) >= abs(delta))))/(len(valid)+1)
    centered=valid-delta
    tost_lower=(1+int(np.sum(centered >= delta+se_soi)))/(len(valid)+1)
    tost_upper=(1+int(np.sum(centered <= delta-se_soi)))/(len(valid)+1)
    out = dict(delta=delta, ci95=ci95, ci90=ci90, p=float(p),
               tost_p_lower=float(tost_lower),tost_p_upper=float(tost_upper),
               tost_p=float(max(tost_lower,tost_upper)),bootstrap_B=B,
               effective_B=len(valid), undefined_B=B-len(valid), seed=int(seed),
               kind=kind, se_soi=float(se_soi),
               equivalent=bool(ci90[0] > -se_soi and ci90[1] < se_soi),
               equivalence_method='approximate centered paired bootstrap TOST with 90% percentile CI cross-check',
               p_method='two-sided centered paired bootstrap with +1 correction')
    if kind == 'cost':
        a = float(sa.sum()+len(missed)*c[1])
        b = float(sb.sum()+len(missed)*c[1])
        denom = len(y)+len(missed)
        out.update(relative_cost_reduction=delta, raw_cost_a=a, raw_cost_b=b,
                   cost_per_pair_a=a/denom, cost_per_pair_b=b/denom)
    return out


def holm(pvalues):
    """Holm step-down adjusted p-values in the original order."""
    p = _vector(pvalues, 'pvalues', probability=True).astype(float)
    order = np.argsort(p, kind='stable')
    adjusted = np.minimum(1., np.maximum.accumulate(p[order]*np.arange(len(p), 0, -1)))
    out = np.empty_like(p)
    out[order] = adjusted
    return out


def policy_cost(prob, nsim, y, g, cost=(2, 1, .1), misses=0):
    p = _vector(prob, 'prob', probability=True)
    n = _vector(nsim, 'nsim', len(p), probability=True)
    y = _labels(y, len(p))
    if not np.isfinite(misses) or misses < 0:
        raise ValueError('misses must be nonnegative')
    return float(_policy_cost(p, n, y, clip_gene(g), _cost(cost), float(misses)))
