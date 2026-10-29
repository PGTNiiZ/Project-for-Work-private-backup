"""Frozen 200-configuration grouped searches, rule and selected refits."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse
import json
import pickle
import sys
import numpy as np
import optuna
from sklearn.metrics import average_precision_score,precision_recall_curve,f1_score
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'work/statistics'))
from analysis_tools import metrics
from training import fit_estimator,predict,attribute_columns
from runtime import job,commit_files,elapsed_fraction
from integrity import sha256

P=json.loads((R/'protocol.json').read_text())
D=R/'data_derived/representation'
A=R/'artifacts'
optuna.logging.set_verbosity(optuna.logging.WARNING)


def load_data(feature):
    meta=np.load(D/'pair_metadata_dev.npz')
    sem=np.load(D/'semantic_dev.npy',mmap_mode='r')
    X=[]
    for f in range(5):
        lex=np.load(D/f'lexical_dev_cv{f}.npy',mmap_mode='r')
        if feature=='lexical': X.append(lex)
        elif feature=='semantic': X.append(sem)
        elif feature=='fusion': X.append(np.concatenate([lex,sem],axis=1))
        else: raise ValueError('feature set not frozen')
    return meta,X


def operating_points(y,p):
    grid=np.array(P['threshold_grid'])
    values=[f1_score(y,p>=t,zero_division=0) for t in grid]
    threshold=float(grid[int(np.argmax(values))])
    precision,recall,thresholds=precision_recall_curve(y,p)
    valid=np.flatnonzero(precision[:-1]>=P['P_target'])
    precision_threshold=float(thresholds[valid[np.argmax(recall[valid])]]) if len(valid) else 1.0000001
    return {'validation_F1_threshold':threshold,'validation_F1':float(max(values)),'precision_target_threshold':precision_threshold,'P_target':P['P_target'],'target_feasible':bool(len(valid))}


def suggest(trial,learner):
    cfg=P[learner]
    if learner=='GBDT':
        return {'learning_rate':trial.suggest_categorical('learning_rate',cfg['learning_rate']),'max_leaf_nodes':trial.suggest_categorical('max_leaf_nodes',cfg['max_leaf_nodes']),'max_iter':trial.suggest_categorical('max_iter',cfg['max_iter']),'min_samples_leaf':trial.suggest_categorical('min_samples_leaf',cfg['min_samples_leaf']),'l2_regularization':trial.suggest_float('l2_regularization',*cfg['l2_regularization_log'],log=True)}
    return {'C':trial.suggest_float('C',*cfg['C_log'],log=True),'class_weight':trial.suggest_categorical('class_weight',cfg['class_weight'])}


def tune(learner,feature,exp_id):
    name=f'{learner}-{feature}'
    target=R/f'metrics/selection_{name}.json'
    if target.exists(): return json.loads(target.read_text())
    meta,X=load_data(feature)
    y,fold=meta['y'],meta['fold']
    study_path=A/f'study_{name}.pkl'
    if study_path.exists():
        with study_path.open('rb') as f: study=pickle.load(f)
    else:
        study=optuna.create_study(direction='maximize',sampler=optuna.samplers.TPESampler(seed=42))
    complete=sum(t.state==optuna.trial.TrialState.COMPLETE for t in study.trials)
    for number in range(complete,P['classifier_search_configs']):
        if elapsed_fraction()>=.85: raise TimeoutError('reporting cutoff: full search incomplete')
        trial=study.ask()
        params=suggest(trial,learner)
        with job(exp_id,f'{name}-trial{number:03d}',{'feature':feature,'learner':learner,'params':params,'folds':[0,1,2,3],'TPE_trial':number},seed=42,tuning_fits=4,validation_evals=4,category='hyperparameter_search') as rec:
            aps=[]
            for f in range(4):
                train=fold!=f
                val=fold==f
                model,_=fit_estimator(X[f][train],y[train],learner,params,seed=42)
                pred=predict(model,X[f][val])
                aps.append(float(average_precision_score(y[val],pred)))
                del model
            mean=float(np.mean(aps))
            rec.update({'fold_AP':aps,'mean_fold_AP':mean,'parameters':params,'test_access':False,'atomic_fit_count':4})
        study.tell(trial,mean)
        with study_path.open('wb') as f: pickle.dump(study,f)
    selected={'learner':learner,'feature':feature,'exp_id':exp_id,'params':study.best_params,'configs_completed':P['classifier_search_configs'],'tuning_fits':4*P['classifier_search_configs'],'validation_selection_AP':float(study.best_value),'selection_scope':'four development folds','classification':P['status']}
    target.write_text(json.dumps(selected,indent=2)+'\n')
    return selected


def refit(learner,feature,exp_id,params,*,group=None,exclude_group=None):
    name=f'{learner}-{feature}' + (f'-single-{group}' if group else '')+(f'-without-{exclude_group}' if exclude_group else '')
    target=R/f'metrics/model_{name}.json'
    if target.exists(): return json.loads(target.read_text())
    meta,X=load_data(feature)
    schema=json.loads((D/'feature_schema.json').read_text())
    y,fold=meta['y'],meta['fold']
    cols=None
    if group is not None or exclude_group is not None:
        cols=attribute_columns(schema,X[0].shape[1],group,exclude_group)
    if cols is not None: X=[x[:,cols] for x in X]
    seeds=P['gbdt_seeds'] if learner=='GBDT' else P['lr_seeds']
    oof=[]
    model_paths=[]
    seed_aps=[]
    for seed in seeds:
        scores=np.zeros(len(y),np.float64)
        for f in range(5):
            if elapsed_fraction()>=.85: raise TimeoutError('reporting cutoff: selected refits incomplete')
            key=f'{name}-seed{seed}-'+(f'oof{f}' if f<4 else 'refit')
            with job(exp_id,key,{'feature':feature,'learner':learner,'params':params,'held_out_fold':f if f<4 else None,'group':group,'exclude_group':exclude_group},seed=seed,training_jobs=1,validation_evals=int(f<4),category='selected_model_fit') as rec:
                train=fold!=f if f<4 else np.ones(len(y),bool)
                model,meta_fit=fit_estimator(X[f][train],y[train],learner,params,seed)
                rec.update(meta_fit)
                if f<4:
                    val=fold==f
                    pred=predict(model,X[f][val])
                    scores[val]=pred
                    rec['candidate_AP']=float(average_precision_score(y[val],pred))
                else:
                    model_path=A/f'model_{name}_seed{seed}.pkl'
                    with model_path.open('wb') as out: pickle.dump({'model':model,'columns':cols,'feature':feature,'params':params,'seed':seed},out)
                    model_paths.append(str(model_path.relative_to(R)))
                    rec['artifact_sha256']=sha256(model_path)
                del model
        oof.append(scores)
        seed_aps.append(float(average_precision_score(y,scores)))
    oof=np.stack(oof)
    path=A/f'oof_{name}.npz'
    np.savez(path,scores=oof,mean=oof.mean(axis=0),seeds=np.array(seeds))
    summary={'name':name,'exp_id':exp_id,'learner':learner,'feature':feature,'params':params,'group':group,'exclude_group':exclude_group,'seeds':seeds,'seed_AP':seed_aps,'seed_AP_SD':float(np.std(seed_aps,ddof=1)) if len(seeds)>1 else 0.,'mean_score_AP':float(average_precision_score(y,oof.mean(axis=0))),'model_paths':model_paths,'model_hashes':{s:sha256(R/s) for s in model_paths},'oof_path':str(path.relative_to(R)),'oof_sha256':sha256(path),'operating_points':operating_points(y,oof.mean(axis=0)),'training_jobs':int(5*len(seeds)),'classification':P['status']}
    summary['development_metrics']=metrics(y,oof.mean(axis=0))
    target.write_text(json.dumps(summary,indent=2)+'\n')
    return summary


def rule():
    target=R/'metrics/model_rule.json'
    if target.exists(): return json.loads(target.read_text())
    meta,X=load_data('lexical')
    y,fold=meta['y'],meta['fold']
    rng=np.random.default_rng(42)
    weights=rng.dirichlet(np.ones(X[0].shape[1]),size=P['classifier_search_configs'])
    best=-1
    best_weights=None
    best_oof=None
    for i,w in enumerate(weights):
        with job('E2-3',f'rule-trial{i:03d}',{'weights':w.tolist(),'folds':[0,1,2,3]},validation_evals=4,category='rule_parameter_search') as rec:
            scores=np.zeros(len(y))
            aps=[]
            for f in range(4):
                val=fold==f
                pred=X[f][val]@w
                scores[val]=pred
                aps.append(float(average_precision_score(y[val],pred)))
            value=float(np.mean(aps))
            rec.update({'mean_fold_AP':value,'fold_AP':aps})
            if value>best:
                best,best_weights,best_oof=value,w.copy(),scores.copy()
    path=A/'rule_weights.npy'
    np.save(path,best_weights)
    np.savez(A/'oof_rule.npz',mean=best_oof,scores=best_oof[None,:],seeds=np.array([42]))
    summary={'name':'rule','exp_id':'E2-3','configs_completed':P['classifier_search_configs'],'validation_selection_AP':best,'weights_path':str(path.relative_to(R)),'weights_sha256':sha256(path),'oof_path':'artifacts/oof_rule.npz','oof_sha256':sha256(A/'oof_rule.npz'),'operating_points':operating_points(y,best_oof),'development_metrics':metrics(y,best_oof),'classification':P['status']}
    target.write_text(json.dumps(summary,indent=2)+'\n')
    return summary


def run_family(learner,feature,exp_id):
    selected=tune(learner,feature,exp_id)
    return refit(learner,feature,exp_id,selected['params'])


def single_groups():
    parent=json.loads((R/'metrics/selection_GBDT-lexical.json').read_text())
    summaries=[]
    for g in P['lexical_groups']:
        summaries.append(refit('GBDT','lexical','E5-5',parent['params'],group=g))
    winner=sorted(summaries,key=lambda s:(-s['mean_score_AP'],s['name']))[0]
    (R/'metrics/single_group_selection.json').write_text(json.dumps({'best_single_group':winner['name'],'selected_on':'development mean ensemble AP only','summaries':summaries,'classification':P['status']},indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=['essential','supporting','single'],default='essential')
    args=parser.parse_args()
    commit_files([R/'training_driver.py',R/'training.py',R/'runtime.py'],'Register prospective grouped classifier and rule execution code')
    if args.mode=='single':
        single_groups()
        return
    tasks=[('GBDT','lexical','E3-2'),('GBDT','fusion','E5-3')] if args.mode=='essential' else [('LR','lexical','E3-1'),('GBDT','semantic','E4-2'),('LR','semantic','E4-2'),('LR','fusion','E5-3')]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run_family,*task) for task in tasks]
        if args.mode=='essential': futures.append(pool.submit(rule))
        failures=[]
        for future in as_completed(futures):
            try: future.result()
            except Exception as exc:
                failures.append(type(exc).__name__)
                print(json.dumps({'family_status':'FAILED','exception_type':type(exc).__name__}),flush=True)
    if args.mode=='essential' and (R/'metrics/selection_GBDT-lexical.json').exists():
        single_groups()
    if failures: raise RuntimeError('one or more families failed; see ledger and deviations')

if __name__=='__main__': main()
