"""Independent artifact, metric, manuscript and citation checks (no frozen writes)."""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'experiments/icsec_final/reviewer_revision'
AUTH=ROOT/'experiments/icsec_final/authoritative_run_v2r1'
PAPER=Path(__file__).parent

def main():
    expected=pd.read_csv(DATA/'metrics_per_seed.csv'); checks=[]
    for seed in [101,202,303]:
        folder=AUTH/'scientific_outputs'/f'outer_{seed}'
        b=pd.read_parquet(DATA/f'outer_{seed}'/'Chow_workflow.parquet')
        original=pd.read_parquet(folder/'decisions/B0_workflow.parquet')
        assert b.pair_key.is_unique and original.pair_key.is_unique
        z=b.merge(original,on='pair_key',validate='one_to_one',suffixes=('_chow','_B0'))
        assert len(z)==len(b)==len(original)
        assert np.array_equal(z.actual_chow,z.actual_B0)
        assert np.array_equal(z.pair_type_chow,z.pair_type_B0)
        static=z.pair_type_B0.ne('MODEL_SCORED')
        assert np.array_equal(z.loc[static,'decision_chow'],z.loc[static,'decision_B0'])
        s=b[b.pair_type.eq('MODEL_SCORED')]; p=s.calibrated_probability.to_numpy()
        risks=np.stack([p,np.repeat(.1,len(p)),2*(1-p)],axis=1)
        assert np.array_equal(s.decision.to_numpy(),risks.argmin(axis=1))
        for method in ['GB17_B0','B0','B1','B2','B3','Chow']:
            f=b if method=='Chow' else pd.read_parquet(folder/'decisions'/f'{method}_workflow.parquet')
            counts=f.groupby(['actual','decision']).size().to_dict()
            tp=counts.get((1,2),0); fp=counts.get((0,2),0); fn=counts.get((1,0),0); rp=counts.get((1,1),0); review=rp+counts.get((0,1),0)
            n=(f.pair_type!='BLOCKING_MISS').sum()
            m=dict(TP=tp,FP=fp,FN=fn,positive_REVIEW=rp,REVIEW=review,
                   precision=tp/(tp+fp),decision_recall=tp/(tp+fn),end_to_end_recall=tp/(tp+fn+rp),
                   decision_F1=2*tp/(2*tp+fp+fn),end_to_end_F1=2*tp/(2*tp+fp+fn+rp),
                   review_rate=review/n,coverage=1-review/n,U=2*fp+fn+.1*review)
            row=expected[(expected.seed==seed)&(expected.policy==method)].iloc[0]
            for k,v in m.items(): assert np.isclose(v,row[k],rtol=0,atol=1e-12), (seed,method,k)
            assert tp+fn+rp==f.actual.sum()
        frozen=json.loads((folder/'policies.json').read_text())['parameters']
        for m in ['B2','B3']:
            trace=pd.read_csv(DATA/f'outer_{seed}'/f'{m}_anytime.csv')
            assert len(trace)==12000 and np.array_equal(trace.evaluations,np.arange(1,12001))
            assert (trace.best_U.diff().dropna()<=1e-10).all()
            assert np.allclose(trace.best_U,np.minimum.accumulate(trace.objective),rtol=0,atol=1e-10)
            assert np.allclose(trace.iloc[-1][['t_m','t_r','c_p','c_d']].astype(float),frozen[m],rtol=0,atol=1e-15)
        checks.append({'seed':seed,'independent_metrics':'PASS','risk_minimal':'PASS','static_scope_unchanged':'PASS','anytime_vectors':'PASS'})
    tex=(PAPER/'main.tex').read_text(); bib=(PAPER/'references.bib').read_text()
    agg=json.loads((DATA/'aggregate.json').read_text())
    for method, group in expected.groupby('policy'):
        for key, value in agg[method].items():
            assert np.isclose(group[key].mean(), value['mean'], rtol=0, atol=1e-10)
            assert np.isclose(group[key].std(ddof=1), value['sample_sd'], rtol=0, atol=1e-10)
    b0, b1 = agg['B0'], agg['B1']
    narrative = [
        f"Automatic recall rises from {b0['end_to_end_recall']['mean']:.4f} to {b1['end_to_end_recall']['mean']:.4f}",
        f"automatic F1 from {b0['end_to_end_F1']['mean']:.4f} to {b1['end_to_end_F1']['mean']:.4f}",
        f"The loss falls by {b0['U']['mean']-b1['U']['mean']:.1f}",
        f"$U$ worsens by {agg['B0']['U']['mean']-agg['GB17_B0']['U']['mean']:.1f}",
    ]
    pivot = expected.pivot(index='seed', columns='policy', values='U')
    chow_wins = [int(s) for s in pivot.index if pivot.loc[s,'Chow'] < min(pivot.loc[s,'B2'],pivot.loc[s,'B3'])]
    assert chow_wins == [101]
    narrative.append(f"the direct-risk rule has lower loss than B2/B3 in seed {chow_wins[0]}.")
    for phrase in narrative: assert phrase in tex, phrase
    gains = expected.pivot(index='seed', columns='policy', values='end_to_end_F1')
    for seed in [101,202,303]: assert f"{gains.loc[seed,'B1']-gains.loc[seed,'B0']:.6f}" in tex
    (PAPER/'NUMERIC_CLAIM_AUDIT.json').write_text(json.dumps({'verified_phrases':narrative,'Chow_better_than_B2_B3_seeds':chow_wins,'U_B3_minus_Chow':agg['B3']['U']['mean']-agg['Chow']['U']['mean'],'U_B3_minus_B2':agg['B3']['U']['mean']-agg['B2']['U']['mean'],'aggregate_recomputation':'PASS'},indent=2)+'\n')
    for m in ['GB17_B0','B0','B1','B2','B3','Chow']:
        label='GB-17+B0' if m=='GB17_B0' else 'GB-18+'+m
        cells=[f"{agg[m][k]['mean']:.4f}" for k in ['precision','decision_recall','end_to_end_recall','decision_F1','end_to_end_F1']]
        cells.extend([f"{100*agg[m]['review_rate']['mean']:.4f}",f"{agg[m]['U']['mean']:.1f}"])
        assert label+' & '+' & '.join(cells) in tex, m
    cited={k.strip() for group in re.findall(r'\\cite\{([^}]+)\}',tex) for k in group.split(',')}
    bibkeys=set(re.findall(r'@\w+\{([^,]+),',bib))
    assert cited==bibkeys, (cited-bibkeys,bibkeys-cited)
    refs=set(re.findall(r'\\ref\{([^}]+)\}',tex)); labels=set(re.findall(r'\\label\{([^}]+)\}',tex))
    assert refs<=labels
    assert not re.search(r'(?i)agentic|\bCRM\b|/Users/|thawaree|Project-for-Work',tex)
    for rel in re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}',tex): assert (PAPER/rel).is_file()
    log=(PAPER/'main.log').read_text()
    assert not re.search(r'Overfull|Citation.*undefined|Reference.*undefined|There were undefined',log)
    report={'checks':checks,'numeric_table':'PASS','citation_closure':'PASS','citation_count':len(cited),
            'figure_presence':'PASS','reference_labels':'PASS','off_topic_and_anonymity':'PASS',
            'tex_build':'PASS','overfull':False,'remaining_warnings':['font substitutions','one underfull paragraph','one underfull page box']}
    (PAPER/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
