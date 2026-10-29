"""SYNTHETIC decisions and workflow accounting, no project data."""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from decision_run import decisions_for_policy,pure_dual_search,per_pair_cost
from final_run import workflow_metric


def test_workflow_ap_and_cost_include_unretrieved_population():
    y=np.array([1,0],dtype=np.int8)
    p=np.array([.8,.7])
    d=np.array([2,0],dtype=np.int8)
    out=workflow_metric(y,p,d,gt=2,all_pairs=4,n_profiles=4)
    assert out['candidate_ap']==1
    assert out['workflow_ap_all_pairs']==.75
    assert out['end_to_end_recall']==.5
    assert abs(out['end_to_end_f1']-2/3)<1e-12
    assert out['workflow_cost_per_all_cross_platform_pair']==.25


def test_closed_form_risk_and_dual_search_have_exact_objectives():
    p=np.array([.05,.5,.96])
    nsim=np.zeros(3)
    y=np.array([0,1,1],dtype=np.int8)
    d=decisions_for_policy({'type':'chow','cost':[2,1,.1]},p,nsim)
    assert d.tolist()==[0,1,2]
    assert np.isclose(per_pair_cost(y,d).sum(),.1)
    result=pure_dual_search(p,y,42,budget=32)
    d=decisions_for_policy(result,p,nsim)
    assert result['evaluations']==32
    assert np.isclose(result['cost'],per_pair_cost(y,d).sum())


def test_factorial_keeps_eight_declared_cells_even_if_policy_levels_coincide():
    import final_run
    assert hasattr(final_run,'factorial_configurations'), 'explicit factorial cell builder missing'
    configs=final_run.factorial_configurations('hybrid_rrf','GBDT-lexical','fixed_0.5')
    assert len(configs)==8
    assert len(set(configs))==8
    assert sorted(c['factor_levels']['policy'] for c in configs.values())==[0,0,0,0,1,1,1,1]
