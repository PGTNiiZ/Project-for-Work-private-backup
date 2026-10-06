"""Reviewer-requested fixed-risk rule; fixtures are NOT manuscript evidence."""
import importlib
import numpy as np


def test_closed_form_minimizes_declared_risk():
    import importlib.util
    module = importlib.import_module('experiments.code.reviewer_revision') if importlib.util.find_spec('experiments.code.reviewer_revision') else None
    assert module is not None, 'reviewer_revision fixed-risk implementation is missing'
    p = np.array([0., .05, .10, .50, .95, .98, 1.])
    d = module.chow_decide(p)
    np.testing.assert_array_equal(d, [0, 0, 0, 1, 1, 2, 2])
    risk = np.column_stack([p, np.full(p.shape, .1), 2 * (1-p)])
    np.testing.assert_allclose(risk[np.arange(len(p)), d], risk.min(axis=1))


def test_positive_review_is_in_end_to_end_denominator():
    from experiments.code import reviewer_revision as module
    assert hasattr(module, 'metrics'), 'extended metrics are missing'
    import pandas as pd
    f = pd.DataFrame({'actual':[1,1,1,0,0], 'decision':[2,0,1,2,1],
                      'pair_type':['MODEL_SCORED']*5})
    m = module.metrics(f)
    assert m['decision_recall'] == .5
    assert m['end_to_end_recall'] == 1/3
    assert m['decision_F1'] == .5
    assert m['end_to_end_F1'] == .4
    assert m['positive_REVIEW'] == 1
    assert m['review_rate'] == .4
    assert m['U'] == 3.2


def test_risk_rule_is_minimal_over_dense_posterior_grid():
    from experiments.code.reviewer_revision import chow_decide
    p = np.linspace(0, 1, 10001)
    risks = np.column_stack([p, np.full(p.shape, .1), 2*(1-p)])
    d = chow_decide(p)
    np.testing.assert_array_equal(d, risks.argmin(axis=1))


def test_risk_rule_rejects_invalid_posteriors():
    import pytest
    from experiments.code.reviewer_revision import chow_decide
    for p in [[np.nan], [np.inf], [-.01], [1.01]]:
        with pytest.raises(ValueError):
            chow_decide(np.array(p))


def test_review_rate_excludes_unreviewable_blocking_misses():
    import pandas as pd
    from experiments.code.reviewer_revision import metrics
    m = metrics(pd.DataFrame({'actual':[1,1], 'decision':[1,0],
                              'pair_type':['MODEL_SCORED','BLOCKING_MISS']}))
    assert m['review_rate'] == 1
    assert m['coverage'] == 0
    assert m['end_to_end_recall'] == 0


def test_documented_four_parameter_boundaries():
    from experiments.icsec_final.authoritative_run_v2.policies import decide_four_parameter
    p = np.array([.98,.7,.7,.7,.699,.979])
    s = np.array([0.,.85,.2,.199,.99,.849])
    np.testing.assert_array_equal(decide_four_parameter(p,s,(.98,.7,.85,.2)), [2,2,1,0,0,1])


