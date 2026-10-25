"""SYNTHETIC data preparation acceptance slice."""
from pathlib import Path
import sys
import importlib.util
import pytest
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def test_canonical_labels_atomic_split_and_endpoint_routing():
    if importlib.util.find_spec('preflight') is None:
        pytest.fail('canonical split adapter is missing')
    from preflight import prepare_frame, split_frame, route_pairs, ground_truth
    rows=[]
    for i in range(15):
        for platform in ['SYNTHETIC_A','SYNTHETIC_B']:
            rows.append(dict(profile_id=str(len(rows)),user_folder=f'SYNTHETIC_{i}',userName=f'SYNTHETIC_{platform}_{i}',fullName='SYNTHETIC name',bio='',location='',externalUrl_clean='',external_domain='',platform=platform))
    rows.append(dict(profile_id='',user_folder='',userName='SYNTHETIC',platform='SYNTHETIC_A'))
    frame, summary=prepare_frame(pd.DataFrame(rows).fillna(''))
    assert len(frame)==30 and summary['quarantined_rows']==1
    frame, report=split_frame(frame,seed=42)
    assert frame.groupby('entity').fold.nunique().max()==1
    assert sorted(frame.groupby('fold').entity.nunique().tolist())==[3]*5
    assert len(ground_truth(frame))==15
    pairs=np.array([[0,1],[0,2]],dtype=np.int32)
    routed,dropped=route_pairs(frame,pairs)
    assert all(frame.iloc[a].fold==frame.iloc[b].fold for a,b in routed)
    assert len(routed)+dropped==2
    assert set(frame.columns).isdisjoint({'user_folder','userName','profile_id'})
