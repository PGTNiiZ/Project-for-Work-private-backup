"""SYNTHETIC mutually exclusive miss-cause tests."""
from pathlib import Path
import importlib.util
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def test_taxonomy_is_exhaustive_and_ceiling_is_not_swallowed_by_missingness():
    assert importlib.util.find_spec('blocking') is not None
    from blocking import assign_causes
    flags={'u':np.array([0,.1,.9,.1,.4]),'n':np.array([0,.1,.1,.2,.4]),'cross':np.array([0,.1,.1,.9,.4]),'max_text':np.array([0,.1,.9,.9,.4]),'link':np.array([False,True,False,False,False]),'missing':np.array([True,False,False,False,False])}
    assert assign_causes(flags).tolist()==['e','d','a','b','f']


def test_cross_field_and_links_are_measured_without_labels():
    from blocking import similarity_flags,fit_passes
    import pandas as pd
    df=pd.DataFrame({'username':['syntheticalpha','different'],'fullname':['other','syntheticalpha'],'bio':['',''],'location':['',''],'links':['https://synthetic.example/a','https://synthetic.example/b'],'domain':['synthetic.example','synthetic.example'],'platform':['a','b']})
    vectors=fit_passes(df)
    flags=similarity_flags(df,np.array([[0,1]],np.int32),vectors)
    assert flags['cross'][0]==1 and flags['link'][0] and not flags['missing'][0]


def test_multipass_is_label_blind_exact_budget_and_cross_platform():
    from blocking import fit_passes, multipass_pairs
    import pandas as pd
    rows = []
    for i in range(30):
        for pl in ['a', 'b', 'c']:
            rows.append(dict(username=f'user{i:02d}zz' if pl != 'c' else f'other{i:02d}', fullname=f'user{i:02d}zz' if pl == 'c' else f'name{i:02d}',
                             bio='', location='', links='', domain='', platform=pl))
    df = pd.DataFrame(rows)
    vec = fit_passes(df)
    pairs, info, passes = multipass_pairs(df, vec, 100)
    assert len(pairs) == 100 and len({tuple(p) for p in pairs}) == 100
    pl = df.platform.to_numpy()
    assert (pl[pairs[:, 0]] != pl[pairs[:, 1]]).all()
    pairs2, _, _ = multipass_pairs(df, vec, 100)
    assert (pairs == pairs2).all()
