"""Synthetic-only API smoke; no repository datasets or labels are opened."""
import json
import time
import numpy as np
import analysis_tools as a


def main():
    rng = np.random.default_rng(19)
    p, ns = rng.random(1000), rng.random(1000)
    ea, eb = rng.integers(0, 20, 1000), rng.integers(0, 20, 1000)
    y = (ea == eb).astype(np.int8)
    g = a.clip_gene([.95, .7, .8, .3])
    d = a.decide(p, ns, g)
    assert d.dtype == np.int8
    a.policy_cost(p, ns, y, g)
    a.metrics(y, p, d, total_positives=int(y.sum())+3, n_profiles=60)
    for method in ['random', 'scrambled_sobol', 'TPE', 'GA']:
        result = a.optimize_policy(p, ns, y, method, 11, budget=32)
        assert result['evaluations'] == 32
    for kind in ['ap', 'cost']:
        kwargs = {} if kind == 'ap' else dict(decisions_a=d, decisions_b=np.zeros(1000, np.int8))
        a.bootstrap_contrast(y, p, 1-p, ea, eb, 20, kind=kind, B=100, **kwargs)
    take = y == 1
    a.bootstrap_contrast(y[take], p[take] >= .5, p[take] >= .7,
                         ea[take], eb[take], 20, kind='pc', B=100)
    a.holm([.01, .04, .2])
    # Full-size exact-objective synthetic timing, one run (not a scientific run).
    p, ns, y = rng.random(200000), rng.random(200000), rng.integers(0, 2, 200000)
    start = time.perf_counter()
    result = a.optimize_policy(p, ns, y, 'GA', 11, budget=2048)
    assert result['evaluations'] == 2048
    print(json.dumps(dict(smoke='PASS', ga_evaluations=result['evaluations'],
                          synthetic_rows=len(y), seconds=round(time.perf_counter()-start, 3))))


if __name__ == '__main__':
    main()
