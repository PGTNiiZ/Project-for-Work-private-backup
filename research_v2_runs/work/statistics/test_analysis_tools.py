import numpy as np
import pytest
import analysis_tools as a


@pytest.mark.parametrize('method', ['random', 'scrambled_sobol', 'TPE', 'GA'])
@pytest.mark.parametrize('budget', [16, 32, 73])
def test_optimizer_exact_budget_and_determinism(method, budget):
    rng = np.random.default_rng(4)
    p, n, y = rng.random(80), rng.random(80), rng.integers(0, 2, 80)
    r = a.optimize_policy(p, n, y, method, 13, budget=budget)
    s = a.optimize_policy(p, n, y, method, 13, budget=budget)
    assert r['evaluations'] == budget
    assert 1 <= r['unique_evaluations'] <= budget
    assert r['cost'] == a.policy_cost(p, n, y, r['genome'])
    np.testing.assert_array_equal(r['genome'], s['genome'])
    assert np.all(np.diff(r['history']) <= 0)


def test_metrics_review_is_not_automatic_recall():
    r = a.metrics([1, 1, 0, 0], [.9, .8, .7, .1], [2, 1, 2, 0], total_positives=3)
    assert r['candidate_ap'] == 1
    assert r['precision'] == .5
    assert r['recall'] == .5
    assert r['end_to_end_recall'] == pytest.approx(1/3)
    assert r['utility_fn'] == 1
    assert r['automatic_fn'] == 2
    assert r['workflow_misses'] == 1
    assert r['raw_cost'] == pytest.approx(3.1)
    assert r['cost_per_pair'] == pytest.approx(3.1/5)
    assert r['review_rate'] == .25
    assert a.metrics([1, 0], [.5, .4])['tp'] == 1


def test_handcomputed_ties_ap():
    r = a.metrics([1, 0, 1], [.8, .8, .2])
    assert r['candidate_ap'] == pytest.approx(7/12)
    with pytest.raises(ValueError):
        a.metrics([1], [.3, .4])
    with pytest.raises(ValueError):
        a.metrics([1], [.3], [3])


def test_cluster_weights_cross_endpoints_and_weighted_ap():
    y = np.array([1, 0, 0], dtype=np.int8)
    w = a._edge_weights(y, np.array([0, 0, 1]), np.array([0, 1, 2]), np.array([2, 3, 1]))
    np.testing.assert_array_equal(w, [2, 6, 3])
    assert a._weighted_ap(np.array([1, 0, 1]), np.array([2., 3., 1.]),
                          *a._ap_order(np.array([.8, .8, .2]))) == pytest.approx(13/30)


def test_bootstrap_matches_independent_reference_and_endpoint_swap():
    y = np.array([1, 1, 0, 0, 0], dtype=np.int8)
    ea, eb = np.array([0, 1, 0, 0, 1]), np.array([0, 1, 1, 2, 2])
    sa, sb = np.array([.9, .8, .8, .2, .3]), np.array([.8, .7, .9, .2, .3])
    B, seed = 101, 42
    rng = np.random.default_rng(seed)
    from sklearn.metrics import average_precision_score
    values = []
    for _ in range(B):
        counts = np.bincount(rng.integers(0, 3, 3), minlength=3)
        w = np.where(y == 1, counts[ea], counts[ea]*counts[eb])
        if w[y == 1].sum() == 0:
            values.append(0.)
        else:
            values.append(average_precision_score(y, sa, sample_weight=w) -
                          average_precision_score(y, sb, sample_weight=w))
    r = a.bootstrap_contrast(y, sa, sb, ea, eb, 3, B=B, seed=seed)
    delta = average_precision_score(y, sa)-average_precision_score(y, sb)
    assert r['delta'] == pytest.approx(delta)
    np.testing.assert_allclose(r['ci95'], np.quantile(values, [.025, .975]))
    assert r['p'] == pytest.approx((1+np.sum(np.abs(np.array(values)-delta) >= abs(delta)))/(B+1))
    s = a.bootstrap_contrast(y, sa, sb, eb, ea, 3, B=B, seed=seed)
    assert r == s
    assert r['bootstrap_B'] == B
    assert 'approximate' in r['equivalence_method']
    centered=np.asarray(values)-delta
    expected_lower=(1+np.sum(centered >= delta+r['se_soi']))/(B+1)
    expected_upper=(1+np.sum(centered <= delta-r['se_soi']))/(B+1)
    assert r['tost_p_lower']==pytest.approx(expected_lower)
    assert r['tost_p_upper']==pytest.approx(expected_upper)
    assert r['tost_p']==pytest.approx(max(expected_lower,expected_upper))


def test_bootstrap_pc_cost_and_holm():
    ea, eb = [0, 1, 2], [0, 1, 2]
    pc = a.bootstrap_contrast([1]*3, [1, 1, 0], [1, 0, 0], ea, eb, 3, kind='pc', B=100)
    assert pc['delta'] == pytest.approx(1/3)
    r = a.bootstrap_contrast([1, 0, 0], [0, 1, 1], [1, 2, 2],
                              [0, 0, 1], [0, 1, 2], 3, kind='cost', B=100)
    assert r['delta'] == pytest.approx(.6)
    assert r['relative_cost_reduction'] == pytest.approx(.6)
    q = a.bootstrap_contrast([1, 0], [.9, .8], [.9, .8], [0, 0], [0, 1], 2,
                            kind='cost', decisions_a=[1, 0], decisions_b=[0, 2],
                            missed_entity=[1], B=20)
    assert q['delta'] == pytest.approx((4-1.1)/4)
    np.testing.assert_allclose(a.holm([.03, .01, .2, .04]), [.09, .04, .2, .09])
    with pytest.raises(ValueError):
        a.bootstrap_contrast([1], [.4], [.3], [0], [1], 2, B=10)


def test_full_ga_budget_counts_only_new_proposals(monkeypatch):
    original = a._policy_cost
    calls = []
    def counted(*args):
        calls.append(tuple(args[3]))
        return original(*args)
    monkeypatch.setattr(a, '_policy_cost', counted)
    r = a.optimize_policy([.8, .95], [.5, .8], [1, 0], 'GA', 11)
    assert len(calls) == r['evaluations'] == 2048
    assert len(set(calls)) == r['unique_evaluations']


def test_cost_bootstrap_reference_uses_both_negative_endpoints():
    y, ea, eb = np.array([1, 0, 0]), np.array([0, 0, 1]), np.array([0, 1, 2])
    ca, cb = np.array([.1, 1., 2.]), np.array([1., 2., 3.])
    rng = np.random.default_rng(9)
    values = []
    for _ in range(123):
        c = np.bincount(rng.integers(0, 3, 3), minlength=3)
        w = np.where(y == 1, c[ea], c[ea]*c[eb])
        if w @ cb > 0:
            values.append((w @ cb-w @ ca)/(w @ cb))
    r = a.bootstrap_contrast(y, ca, cb, ea, eb, 3, kind='cost', B=123, seed=9)
    np.testing.assert_allclose(r['ci95'], np.quantile(values, [.025, .975]))
    assert r['effective_B'] == len(values)
    swap = a.bootstrap_contrast(y, ca, cb, eb, ea, 3, kind='cost', B=123, seed=9)
    assert r == swap


def test_metrics_calibration_and_cost_sensitivity():
    r = a.metrics([1, 0], [.8, .2], [0, 1], total_positives=2, cost=(5, 2, .3))
    assert r['brier'] == pytest.approx(.04)
    assert r['ece15_equalmass'] == pytest.approx(.2)
    assert r['raw_cost'] == pytest.approx(4.3)
    assert a.policy_cost([.6], [.2], [1], [.95, .7, .8, .3], cost=(5, 2, .3), misses=1) == 4
    assert a.metrics([], [])['candidate_ap'] == 0
    assert a.holm([]).size == 0


def test_historical_policy_and_cost():
    g = [.95, .7, .8, .3]
    p = [.69, .95, .8, .8, .8, .7]
    n = [1, 0, .8, .29, .3, .5]
    d = a.decide(p, n, g)
    assert d.dtype == np.int8
    np.testing.assert_array_equal(d, [0, 2, 2, 0, 1, 1])
    assert a.policy_cost(p, n, [1, 0, 1, 1, 1, 0], g, misses=2) == pytest.approx(6.2)
    np.testing.assert_allclose(a.clip_gene([2, 2, -1, 2]), [.999, .999, .5, .5])
    with pytest.raises(ValueError):
        a.decide([.5], [.2, .3], g)
