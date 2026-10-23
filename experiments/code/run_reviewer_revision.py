"""Reanalyze frozen outcomes; replay validation search without retraining.
Run: uv run --python 3.11 python -m experiments.code.run_reviewer_revision
"""
from pathlib import Path
import hashlib
import json
import pickle
import platform
import sys
import warnings
import numpy as np
import pandas as pd
from experiments.code.reviewer_revision import chow_decide, metrics
from experiments.icsec_final.authoritative_run_v2 import policies as pol
from experiments.icsec_final.authoritative_run_v2.features import FEATURE18_COLUMNS

ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT/'experiments/icsec_final/authoritative_run_v2'
AUTH = ROOT/'experiments/icsec_final/authoritative_run_v2r1'
OUT = ROOT/'experiments/icsec_final/reviewer_revision'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=True)
    inputs = {}
    for mf in AUTH.rglob('SHA256SUMS.txt'):
        for line in mf.read_text().splitlines():
            h, f = line.split('  ',1)
            p = mf.parent/f
            assert sha(p)==h, f'bad frozen hash {p}'
            inputs[str(p.relative_to(ROOT))]=h
    prov = json.loads((AUTH/'provenance/v2r1_manifest.json').read_text())
    for rel,h in prov['sources'].items():
        assert sha(ROOT/rel)==h, f'changed source {rel}'
        inputs[rel]=h
    for rel,h in prov['frozen_inputs'].items():
        assert sha(V2/rel)==h, f'changed input {rel}'
        inputs[str((V2/rel).relative_to(ROOT))]=h
    rows = []
    for seed in [101,202,303]:
        d=AUTH/'scientific_outputs'/f'outer_{seed}'
        summary=json.loads((d/'summary.json').read_text())
        original={}
        for method, old in summary.items():
            f=pd.read_parquet(d/'decisions'/f'{method}_workflow.parquet')
            assert f.pair_key.is_unique
            original[method]=f
            m=metrics(f)
            for k,oldkey in [('precision','precision'),('decision_recall','recall'),('decision_F1','F1'),('U','U'),('TP','TP'),('FP','FP'),('FN','FN'),('REVIEW','REVIEW')]:
                assert abs(m[k]-old[oldkey])<1e-12, (seed,method,k)
            rows.append(dict(seed=seed,policy=method,**m))
        baseline=original['B0'].copy()
        scored=baseline.pair_type.eq('MODEL_SCORED')
        baseline.loc[scored,'decision']=chow_decide(baseline.loc[scored,'calibrated_probability'].to_numpy())
        # Probability and decisions are already joined by safe pair key in frozen workflow.
        frozen=pd.read_parquet(d/'sealed_predictions/predictions.parquet')
        p=frozen.loc[frozen.model_policy.eq('B0'),['pair_key','calibrated_probability']]
        joined=baseline.loc[scored,['pair_key','calibrated_probability']].merge(p,on='pair_key',validate='one_to_one',suffixes=('_row','_frozen'))
        assert len(joined)==scored.sum()
        assert np.array_equal(joined.calibrated_probability_row,joined.calibrated_probability_frozen)
        sd=OUT/f'outer_{seed}'; sd.mkdir(exist_ok=True)
        baseline.to_parquet(sd/'Chow_workflow.parquet',index=False)
        rows.append(dict(seed=seed,policy='Chow',**metrics(baseline)))
        print('METRICS',seed,flush=True)
    table=pd.DataFrame(rows)
    table.to_csv(OUT/'metrics_per_seed.csv',index=False)
    agg={m:{k:dict(mean=float(g[k].mean()),sample_sd=float(g[k].std(ddof=1))) for k in table.columns if k not in ['seed','policy']} for m,g in table.groupby('policy')}
    (OUT/'aggregate.json').write_text(json.dumps(agg,indent=2)+'\n')
    print('AGGREGATES',json.dumps(agg),flush=True)

    # Validation-only replay. The original _cost is observed, not modified mathematically.
    f17=pd.read_parquet(V2/'features/gb17.parquet')
    bert=pd.read_parquet(V2/'features/bert_cos.parquet')
    features=f17.merge(bert,on=['profile_row_id_a','profile_row_id_b'],validate='one_to_one',sort=False)
    checkpoints=[]
    for seed in [101,202,303]:
        d=AUTH/'scientific_outputs'/f'outer_{seed}'; sd=OUT/f'outer_{seed}'
        route=pd.read_parquet(V2/'routing'/f'outer_{seed}'/'workflow.parquet')
        val=route.loc[route.role.eq('POLICY_VALIDATION') & route.pair_type.eq('MODEL_SCORED')]
        val=val.merge(features,on=['profile_row_id_a','profile_row_id_b'],validate='one_to_one',sort=False)
        meta=json.loads((V2/'scientific_inputs'/f'outer_{seed}'/'input_artifact_manifest.json').read_text())
        labpath=Path(meta['artifacts']['development']['path'])
        labels=pd.read_parquet(labpath)
        labels=labels.loc[labels.role.eq('POLICY_VALIDATION'),['pair_key','actual']]
        val=val.merge(labels,on='pair_key',validate='one_to_one',sort=False)
        assert val.pair_key.is_unique
        inputs[str(labpath.relative_to(ROOT))]=sha(labpath)
        with (d/'models/GB-18_model.pkl').open('rb') as fh: model=pickle.load(fh)
        with (d/'models/GB-18_calibrator.pkl').open('rb') as fh: cal=pickle.load(fh)
        p=cal.predict(model.predict_proba(val[FEATURE18_COLUMNS].to_numpy(np.float32))[:,1])
        y=val.actual.to_numpy(np.int8); n=val.name_sim.to_numpy()
        pd.DataFrame({'pair_key':val.pair_key,'probability':p,'name_sim':n,'actual':y}).to_parquet(sd/'validation_replay_input.parquet',index=False)
        frozen=json.loads((d/'policies.json').read_text())['parameters']
        original_cost=pol._cost; original_decide=pol.decide_four_parameter
        for method,search in [('B2',pol.b2_sobol_search),('B3',pol.b3_ga_search)]:
            history=[]; current=[None]; best=[float('inf'),None]
            def observe_decide(prob,name,genome):
                current[0]=genome
                return original_decide(prob,name,genome)
            def observe_cost(decisions,actual):
                value=original_cost(decisions,actual)
                if value<best[0]: best[:]=[value,current[0]]
                history.append((len(history)+1,value,best[0],*best[1]))
                return value
            pol.decide_four_parameter=observe_decide; pol._cost=observe_cost
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore',UserWarning)
                    winner,metadata=search(p,n,y,budget=12000,seed=seed)
            finally:
                pol._cost=original_cost; pol.decide_four_parameter=original_decide
            assert tuple(winner)==tuple(frozen[method]), f'replay vector mismatch {seed} {method}'
            trace=pd.DataFrame(history,columns=['evaluations','objective','best_U','t_m','t_r','c_p','c_d'])
            assert len(trace)==12000
            trace.to_csv(sd/f'{method}_anytime.csv',index=False)
            for b in [100,250,500,1000,2000,4000,8000,12000]:
                checkpoints.append(dict(seed=seed,policy=method,**trace.iloc[b-1].to_dict()))
            print('REPLAY VERIFIED',seed,method,'best_validation_U',best[0],'vector',winner,flush=True)
        (sd/'replay_verification.json').write_text(json.dumps({'final_vectors_identical':True,'validation_rows':len(val),'seed':seed,'budget':12000},indent=2)+'\n')
    pd.DataFrame(checkpoints).to_csv(OUT/'anytime_checkpoints.csv',index=False)
    provenance={'python':sys.version,'platform':platform.platform(),'inputs':inputs,
                'sources':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'experiments/code/reviewer_revision.py']},
                'protocol_sha256':sha(OUT/'PROTOCOL.md'),'model_refit':False,'calibration_refit':False,
                'test_tuning':False,'validation_replay_budget':12000,'seeds':[101,202,303]}
    (OUT/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    # Runtime logs are still open when this executes; close their hashes only after process exit.
    (OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(OUT)}\n' for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt' and p.suffix!='.log'))
    print('COMPLETE',flush=True)

if __name__=='__main__':
    main()
