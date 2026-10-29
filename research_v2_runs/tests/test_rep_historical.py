"""SYNTHETIC historical B0 parity test."""
from pathlib import Path
import sys
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'work/representation'))
from rep import b0_pairs

def test_historical_ascii_prefix_not_unicode_prefix():
    df=pd.DataFrame({'username':['abc','xyz'],'fullname':['éélena','éélise'],'bio':['',''],'location':['',''],'links':['',''],'domain':['',''],'platform':['SYNTHETIC_A','SYNTHETIC_B']})
    assert len(b0_pairs(df))==0
