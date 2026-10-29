"""Development-only calibration and equal-budget policy searches."""
from pathlib import Path
import json
import pickle
import sys
import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss,f1_score
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'work/statistics'))
from analysis_tools import decide,optimize_policy,metrics
from runtime import job,commit_files,elapsed_fraction
from integrity import sha256
P=json.loads((R/'protocol.json').read_text())
A=R/'artifacts'


def apply_calibrator(model,values):
    p=np.asarray(values,float)
    if model is None: return np.clip(p,0,1)
    if isinstance(model,IsotonicRegression): return np.clip(model.predict(p),0,1)
    logits=np.log(np.clip(p,1e-6,1-1e-6)/(1-np.clip(p,1e-6,1-1e-6)))
    return model.predict_proba(logits[:,None])[:,1]


def fit_calibrator(method,p,y):
    if method=='identity': return None
    if method=='isotonic': return IsotonicRegression(out_of_bounds='clip').fit(p,y)
    logits=np.log(np.clip(p,1e-6,1-1e-6)/(1-np.clip(p,1e-6,1-1e-6)))
    return LogisticRegression(C=1.0,max_iter=500,random_state=42).fit(logits[:,None],y)


def decisions_for_policy(spec,p,nsim):
    typ=spec['type']
    if typ=='threshold': return (p>=spec['threshold']).astype(np.int8)*2
    if typ=='genome': return decide(p,nsim,spec['genome'])
    if typ=='dual':
        return np.where(p>=spec['t_match'],2,np.where(p>=spec['t_review'],1,0)).astype(np.int8)
    if typ=='chow':
        fp,fn,rev=spec['cost']
        risks=np.column_stack([fn*p,np.full(len(p),rev),fp*(1-p)])
        return np.argmin(risks,axis=1).astype(np.int8)
    raise ValueError('policy outside frozen types')


def per_pair_cost(y,d,cost=(2,1,.1)):
    fp,fn,rev=cost
    return np.where(d==1,rev,np.where((d==2)&(y==0),fp,np.where((d==0)&(y==1),fn,0.))).astype(float)


def summarize_family(specs,p,nsim,y,total_gt):
    stats=[metrics(y,p,decisions_for_policy(s,p,nsim),total_positives=total_gt,cost=(2,1,.1)) for s in specs]
    keys=['raw_cost','cost_per_pair','precision','recall','f1','end_to_end_recall','review_rate','review','tp','fp','automatic_fn','utility_fn']
    return {'n_seeds':len(specs),'means':{k:float(np.mean([r[k] for r in stats])) for k in keys},'seed_SD':{k:float(np.std([r[k] for r in stats],ddof=1)) if len(stats)>1 else 0. for k in keys},'per_seed':stats,'aggregation':'arithmetic mean across all predeclared optimizer seeds, never select a best seed'}


def pure_dual_search(p,y,seed,budget=2048,cost=(2,1,.1),misses=0):
    rng=np.random.default_rng(seed)
    points=np.sort(rng.random((budget,2)),axis=1)
    order=np.argsort(p,kind='stable')
    sy=y[order]
    sp=p[order]
    cpos=np.r_[0,np.cumsum(sy)]
    cneg=np.r_[0,np.cumsum(1-sy)]
    left=np.searchsorted(sp,points[:,0],side='left')
    right=np.searchsorted(sp,points[:,1],side='left')
    values=cost[0]*(cneg[-1]-cneg[right])+cost[1]*(cpos[left]+misses)+cost[2]*(right-left)
    i=int(np.argmin(values))
    return {'type':'dual','t_review':float(points[i,0]),'t_match':float(points[i,1]),'seed':seed,'evaluations':budget,'cost':float(values[i])}


def run():
    commit_files([R/'decision_run.py',R/'runtime.py'],'Register development-only calibration and budget-matched decision execution')
    names=['GBDT-lexical','GBDT-fusion']
    summaries={n:json.loads((R/f'metrics/model_{n}.json').read_text()) for n in names}
    mstar=sorted(names,key=lambda n:(-summaries[n]['mean_score_AP'],n!='GBDT-lexical'))[0]
    raw=np.load(R/summaries[mstar]['oof_path'])['mean']
    meta=np.load(R/'data_derived/representation/pair_metadata_dev.npz')
    y,fold=meta['y'],meta['fold']
    X=np.load(R/'data_derived/representation/lexical_dev_cv4.npy',mmap_mode='r')
    nsim=np.maximum(X[:,1],X[:,8]).astype(float)
    total_gt=sum(r['ground_truth_pairs'] for r in json.loads((R/'manifests/split_summary.json').read_text())['folds'] if r['fold']<4)
    misses=int(total_gt-y.sum())
    prior=[float(y[fold==f].mean()) for f in range(4)]
    ratio=max(prior)/min(prior)
    if ratio>1.5: raise ValueError('development equal-role prior ratio exceeds 1.5; calibration blocked')
    calibration={}
    cross={}
    for method in ['identity','platt','isotonic']:
        with job('E6-7',f'calibration-{method}',{'method':method,'input_model':mstar,'input_oof_sha256':summaries[mstar]['oof_sha256'],'calibration_scope':'leave-one-development-fold-out','Platt_C':1.0},validation_evals=4,category='calibration_fit') as rec:
            predicted=np.zeros(len(y))
            for f in range(4):
                train=fold!=f
                val=fold==f
                model=fit_calibrator(method,raw[train],y[train])
                predicted[val]=apply_calibrator(model,raw[val])
            stat=metrics(y,predicted,total_positives=total_gt)
            rec.update(stat)
            calibration[method]=stat
            cross[method]=predicted
    chosen=sorted(calibration,key=lambda m:(calibration[m]['brier'],['identity','platt','isotonic'].index(m)))[0]
    calibrator=fit_calibrator(chosen,raw,y)
    with (A/'calibrator.pkl').open('wb') as f: pickle.dump(calibrator,f)
    prob=cross[chosen]
    np.savez(A/'policy_development_inputs.npz',prob=prob,raw=raw,nsim=nsim,y=y,fold=fold)
    families={
        'fixed_0.5':[{'type':'threshold','threshold':.5}],
        'historical_R0':[{'type':'dual','t_match':.98,'t_review':.95}],
        'historical_stage18':[{'type':'genome','genome':[.98,.95,.90,.70]}],
    }
    for name,specs in families.items():
        with job('E6-1',name,{'policy':specs,'M_star':mstar,'calibrator':chosen},validation_evals=1) as rec:
            rec.update(summarize_family(specs,prob,nsim,y,total_gt))
    with job('E6-2','validation-F1-grid',{'grid':P['threshold_grid'],'M_star':mstar,'calibrator':chosen},validation_evals=99) as rec:
        fs=[f1_score(y,prob>=t,zero_division=0) for t in P['threshold_grid']]
        threshold=float(P['threshold_grid'][int(np.argmax(fs))])
        families['validation_F1']=[{'type':'threshold','threshold':threshold}]
        rec.update({'threshold':threshold,'validation_F1':float(max(fs))})
    for scenario in P['cost_sensitivity']:
        fp,fn,review=scenario
        key=f'cost-{fp}-{fn}-{review}'
        with job('E6-3',key,{'cost':scenario,'M_star':mstar,'calibrator':chosen},validation_evals=2) as rec:
            threshold={'type':'threshold','threshold':fp/(fp+fn)}
            chow={'type':'chow','cost':scenario}
            rec['threshold']=metrics(y,prob,decisions_for_policy(threshold,prob,nsim),total_positives=total_gt,cost=scenario)
            rec['chow']=metrics(y,prob,decisions_for_policy(chow,prob,nsim),total_positives=total_gt,cost=scenario)
            if scenario==[2,1,.1]:
                families['closed_cost']=[threshold]
                families['Chow']=[chow]
    for method in P['policy_optimizers']:
        specs=[]
        exp='E6-5' if method=='GA' else 'E6-4'
        for seed in P['policy_seeds']:
            if elapsed_fraction()>=.85: raise TimeoutError('reporting cutoff: complete policy seed budget unavailable')
            with job(exp,f'{method}-seed{seed}',{'optimizer':method,'budget':P['policy_budget_per_seed'],'M_star':mstar,'calibrator':chosen,'policy_space':'historical four-gene','cost':[2,1,.1]},seed=seed,validation_evals=P['policy_budget_per_seed'],category='policy_optimization') as rec:
                best=optimize_policy(prob,nsim,y,method,seed,P['policy_budget_per_seed'],cost=(2,1,.1),misses=misses)
                rec.update(best)
                specs.append({'type':'genome','genome':best['genome'],'seed':seed})
        families[method]=specs
    specs=[]
    for seed in P['policy_seeds']:
        with job('E6-6',f'pure-dual-seed{seed}',{'optimizer':'random','budget':P['policy_budget_per_seed'],'space':'0<=t_review<=t_match<=1','cost':[2,1,.1]},seed=seed,validation_evals=P['policy_budget_per_seed'],category='policy_optimization') as rec:
            best=pure_dual_search(prob,y,seed,P['policy_budget_per_seed'],(2,1,.1),misses)
            rec.update(best)
            specs.append(best)
    families['three_way']=specs
    stats={name:summarize_family(specs,prob,nsim,y,total_gt) for name,specs in families.items()}
    nongas=['validation_F1','closed_cost','Chow','random','scrambled_sobol','TPE']
    best_non_ga=sorted(nongas,key=lambda n:(stats[n]['means']['raw_cost'],n))[0]
    best_policy=sorted(stats,key=lambda n:(stats[n]['means']['raw_cost'],n))[0]
    summary={'M_star':mstar,'calibrator':chosen,'calibration_development':calibration,'calibration_prior_per_fold':prior,'prior_ratio_max_min':ratio,'families':families,'development_metrics':stats,'best_non_GA':best_non_ga,'best_policy':best_policy,'total_development_positives':int(total_gt),'blocking_missed_positives':misses,'calibrator_sha256':sha256(A/'calibrator.pkl'),'classification':P['status'],'uncertainty':'calibration method selection reuses development OOF; meta-calibration is not a nested independent generalization estimate','seed_aggregation':'all ten optimizer seeds averaged; no best seed selection'}
    (R/'metrics/policy_selection.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'policy_selection':{'M_star':mstar,'calibrator':chosen,'best_non_GA':best_non_ga,'best_policy':best_policy,'prior_ratio':ratio}}),flush=True)

if __name__=='__main__': run()
