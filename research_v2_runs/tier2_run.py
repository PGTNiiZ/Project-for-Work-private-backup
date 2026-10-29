"""Frozen-hyperparameter Tier2 ablations and true entity learning curves."""
from pathlib import Path
import argparse
import json
import pickle
import sys
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'work/representation'))
import rep
from training import fit_estimator,predict
from training_driver import refit
from runtime import job,commit_files,elapsed_fraction
from integrity import sha256
P=json.loads((R/'protocol.json').read_text())
D=R/'data_derived/representation'


def freeze_plan():
    if (R/'ledger/test_access.jsonl').exists(): raise PermissionError('Tier2 plan must be frozen before final access')
    parents={}
    for learner,feature in [('GBDT','lexical'),('GBDT','fusion'),('LR','lexical'),('LR','fusion')]:
        path=R/f'metrics/selection_{learner}-{feature}.json'
        parents[f'{learner}-{feature}']={'path':str(path.relative_to(R)),'sha256':sha256(path),'params':json.loads(path.read_text())['params']}
    plan={'classification':P['status'],'parents':parents,'groups':P['lexical_groups'],'gbdt_seeds':P['gbdt_seeds'],'lr_seeds':P['lr_seeds'],'learning_curve_fractions':[.1,.25,.5],'learning_curve_seed':42,'learning_curve_folds':[0,1,2,3],'scope':'development OOF only; no additional final evaluations or hyperparameter selection','single_attribute_LR':'supporting within E5-5; cannot change primary GBDT best-single-group selection','rule_learning_curve':'NOT RUN: main weights use full development label-informed selection; avoid unequal information-budget sample-efficiency claim','ablation':'drop every lexical AND semantic feature belonging to excluded attribute'}
    path=R/'manifests/TIER2_FIXED_PLAN.json'
    path.write_text(json.dumps(plan,indent=2)+'\n')
    commit_files([path,R/'tier2_run.py',R/'training.py',R/'training_driver.py',R/'tests/test_training.py'],'Freeze supporting attribute ablations and entity learning curve controls before final')
    return plan


def check_plan():
    plan=json.loads((R/'manifests/TIER2_FIXED_PLAN.json').read_text())
    for parent in plan['parents'].values():
        if sha256(R/parent['path'])!=parent['sha256']: raise PermissionError('frozen Tier2 parent changed')
    return plan


def curve_inputs(fraction,fold):
    target=R/f'data_derived/curve_{fraction}_{fold}.npz'
    if target.exists(): return dict(np.load(target))
    frames=[pd.read_parquet(R/f'data_derived/dev_fold_{f}.parquet') for f in range(4)]
    frame=pd.concat(frames,ignore_index=True)
    meta=np.load(D/'pair_metadata_dev.npz')
    pairs,y,roles=meta['pairs'],meta['y'],meta['fold']
    components=frame.component.to_numpy()
    available=np.unique(components[frame.fold.to_numpy()!=fold])
    rng=np.random.default_rng(42+fold)
    chosen=rng.choice(available,max(1,int(len(available)*fraction)),replace=False)
    profiles=np.isin(components,chosen)&frame.fold.ne(fold).to_numpy()
    pair_train=(roles!=fold)&profiles[pairs[:,0]]&profiles[pairs[:,1]]
    pair_val=roles==fold
    relevant=np.r_[np.flatnonzero(pair_train),np.flatnonzero(pair_val)]
    vectors=rep.fit_tfidf(frame[profiles].reset_index(drop=True))
    X,_,_=rep.lexical_features(frame,pairs[relevant],vectors)
    n_train=int(pair_train.sum())
    data={'X_train':X[:n_train],'X_val':X[n_train:],'y_train':y[pair_train],'y_val':y[pair_val],'training_entities':np.array(frame.loc[profiles,'entity'].nunique()),'training_profiles':np.array(profiles.sum()),'membership_sha256':np.array(__import__('hashlib').sha256(np.sort(chosen).tobytes()).hexdigest())}
    np.savez(target,**data)
    return data


def run():
    if not (R/'metrics/final_summary.json').exists(): raise PermissionError('Tier2 starts only after completed Tier1 final evaluation')
    plan=check_plan()
    summaries=[]
    for learner in ['GBDT','LR']:
        parent=plan['parents'][learner+'-fusion']
        for group in plan['groups']:
            if elapsed_fraction()>=.70: return save(summaries,'operational 70% cutoff: no new Tier2 runs')
            summaries.append(refit(learner,'fusion','E5-4',parent['params'],exclude_group=group))
    for fraction in plan['learning_curve_fractions']:
        for fold in plan['learning_curve_folds']:
            if elapsed_fraction()>=.70: return save(summaries,'operational 70% cutoff before next learning curve point')
            data=curve_inputs(fraction,fold)
            for learner,exp in [('GBDT','E3-2'),('LR','E3-1')]:
                parent=plan['parents'][learner+'-lexical']
                with job(exp,f'learning-curve-{learner}-frac{fraction}-fold{fold}',{'fraction':fraction,'fold':fold,'learner':learner,'params':parent['params'],'parent_sha256':parent['sha256'],'training_membership_sha256':str(data['membership_sha256'])},seed=42,training_jobs=1,validation_evals=1,category='fixed_learning_curve_fit') as rec:
                    model,fit=fit_estimator(data['X_train'],data['y_train'],learner,parent['params'],42)
                    score=predict(model,data['X_val'])
                    path=R/f'artifacts/curve_{learner}_{fraction}_{fold}.npz'
                    np.savez(path,score=score,y=data['y_val'])
                    rec.update(fit)
                    rec.update({'candidate_AP':float(average_precision_score(data['y_val'],score)),'fraction':fraction,'fold':fold,'learner':learner,'n_training_entities':int(data['training_entities']),'n_training_profiles':int(data['training_profiles']),'n_validation_pairs':int(len(score)),'prediction_sha256':sha256(path),'no_hyperparameter_selection':True})
    for group in plan['groups']:
        if elapsed_fraction()>=.70: return save(summaries,'operational70%cutoff before extra LR single-group variant')
        summaries.append(refit('LR','lexical','E5-5',plan['parents']['LR-lexical']['params'],group=group))
    return save(summaries,'DONE')


def save(summaries,status):
    data={'classification':P['status'],'status':status,'models':summaries,'rule_learning_curve':'NOT RUN: full-development tuned weights are not a matched reduced-data baseline'}
    (R/'metrics/tier2_summary.json').write_text(json.dumps(data,indent=2)+'\n')
    return data

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--freeze',action='store_true')
    args=parser.parse_args()
    if args.freeze: freeze_plan()
    else: run()
