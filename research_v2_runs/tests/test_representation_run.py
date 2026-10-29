"""SYNTHETIC candidate accounting acceptance test."""
from pathlib import Path
import importlib.util
import sys
import pytest
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def test_blocking_miss_and_candidate_denominators_stay_separate():
    if importlib.util.find_spec('representation_run') is None:
        pytest.fail('blocking workflow adapter missing')
    from representation_run import pair_summary
    df=pd.DataFrame({'entity':[0,0,1,1],'platform':['a','b','a','b']})
    out=pair_summary(df,np.array([[0,1],[0,3]],dtype=np.int32))
    assert out['ground_truth_pairs']==2
    assert out['candidate_pairs']==2
    assert out['found_positives']==1
    assert out['blocking_misses']==1
    assert out['pc']==.5
    assert out['all_cross_platform_pairs']==4
