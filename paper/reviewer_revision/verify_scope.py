"""Recompute global scope from eligible profiles and frozen pair-key artifacts."""
from pathlib import Path
import json
import sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from experiments.code.run_icsec_authoritative_v2 import load_public_profiles, candidate_scope, pair_key

def main():
    v2=ROOT/'experiments/icsec_final/authoritative_run_v2'
    profiles=load_public_profiles()
    candidates={}
    for name,file in [('exact','exact_tier'),('scored','model_scored'),('workflow','workflow')]:
        f=pd.read_parquet(v2/'candidates'/f'{file}.parquet')
        candidates[name]={pair_key(a,b) for a,b in f[['profile_row_id_a','profile_row_id_b']].itertuples(index=False,name=None)}
        assert len(candidates[name])==len(f)
    assert not candidates['exact'] & candidates['scored']
    assert candidates['exact'] | candidates['scored'] == candidates['workflow']
    candidates['exact_breakdown']=candidates['blocking_breakdown']={}
    report=candidate_scope(profiles,candidates)
    report.pop('exact_tier_breakdown'); report.pop('blocking_key_breakdown')
    report['method']='Current eligible profiles plus persisted candidate keys; candidate generation not rerun'
    (Path(__file__).parent/'CANDIDATE_SCOPE_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
