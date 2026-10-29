"""SYNTHETIC approximate-bootstrap TOST acceptance test."""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'work/statistics'))
from analysis_tools import bootstrap_contrast

def test_tost_reports_both_one_sided_pvalues_not_only_a_ci_boolean():
    y=np.array([0,1],np.int8)
    s=np.array([.1,.9])
    e=np.array([0,1])
    b=np.array([1,1])
    out=bootstrap_contrast(y,s,s,e,b,2,B=32,se_soi=.02)
    assert 'tost_p' in out, 'TOST numerical tests not implemented'
    assert out['tost_p']==max(out['tost_p_lower'],out['tost_p_upper'])
    assert np.isclose(out['tost_p'],1/33)
    assert out['equivalent']
