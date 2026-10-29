"""Predeclare locked configurations and perform lead-only final evaluation."""
from pathlib import Path
import argparse
import io
import itertools
import json
import pickle
import sys
import time
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'work/representation'))
sys.path.insert(0,str(R/'work/statistics'))
import rep
from analysis_tools import metrics
from decision_run import fit_calibrator,apply_calibrator,decisions_for_policy,summarize_family,per_pair_cost
from representation_run import pair_summary,encode_scope,load_encoder
from preflight import ground_truth
from integrity import sha256,guarded_read,require_committed
from runtime import job,commit_files
P=json.loads((R/'protocol.json').read_text())
D=R/'data_derived/representation'
A=R/'artifacts'


def factorial_configurations(hybrid,mstar,best_policy):
    configs={}
    for b,m,p in itertools.product([0,1],repeat=3):
        blocker=['B0',hybrid][b]
        matcher=['rule',mstar][m]
        policy=['fixed_0.5',best_policy][p]
        key=f'factorial-B{b}-M{m}-P{p}'
        configs[key]={'exp_id':'E7-2','kind':'factorial','blocker':blocker,'matcher':matcher,'families':[policy],'factor_levels':{'blocker':b,'matcher':m,'policy':p}}
    return configs


def prepare_lock():
    if (R/'ledger/test_access.jsonl').exists(): raise PermissionError('final lock cannot change after test access')
    selection=json.loads((R/'metrics/blocker_selection.json').read_text())
    policies=json.loads((R/'metrics/policy_selection.json').read_text())
    single=json.loads((R/'metrics/single_group_selection.json').read_text())['best_single_group']
    model_names=['GBDT-lexical','GBDT-fusion',single]
    summaries={n:json.loads((R/f'metrics/model_{n}.json').read_text()) for n in model_names}
    rule=json.loads((R/'metrics/model_rule.json').read_text())
    # Same frozen calibration method as M*, fitted to rule OOF only. It is not
    # an extra selected matcher and cannot see test labels.
    oof=np.load(R/rule['oof_path'])['mean']
    y=np.load(D/'pair_metadata_dev.npz')['y']
    with job('E6-7','factorial-rule-calibration',{'method':policies['calibrator'],'scope':'all development OOF rule scores','no_method_reselection':True},category='calibration_fit') as rec:
        model=fit_calibrator(policies['calibrator'],oof,y)
        with (A/'rule_calibrator.pkl').open('wb') as f: pickle.dump(model,f)
        rec.update({'artifact_sha256':sha256(A/'rule_calibrator.pkl'),'test_access':False})
    configs={}
    lex,hybrid,best=selection['best_lexical'],selection['hybrid'],selection['B_star']
    for method in dict.fromkeys(['B0',lex,hybrid]):
        configs[f'blocking-{method}']={'exp_id':'E1-1' if method=='B0' else 'E1-3' if method=='sparse' else 'E1-5','kind':'blocking','blocker':method}
    for name in ['rule',*model_names]:
        exp='E2-3' if name=='rule' else summaries[name]['exp_id']
        configs[f'matcher-{name}']={'exp_id':exp,'kind':'matcher','blocker':best,'matcher':name}
    policy_groups={'E6-1':['fixed_0.5','historical_R0','historical_stage18'],'E6-2':['validation_F1'],'E6-3':['closed_cost','Chow'],'E6-4':['random','scrambled_sobol','TPE'],'E6-5':['GA'],'E6-6':['three_way']}
    for exp,names in policy_groups.items():
        configs[f'policy-{exp}']={'exp_id':exp,'kind':'policy','blocker':best,'matcher':policies['M_star'],'families':names}
    configs.update(factorial_configurations(hybrid,policies['M_star'],policies['best_policy']))
    ref='matcher-GBDT-lexical'
    if lex!=best:
        ref='workflow-REF'
        configs[ref]={'exp_id':'E7-1','kind':'matcher','blocker':lex,'matcher':'GBDT-lexical'}
    best_family=policies['best_policy']
    best_config=next(key for key,c in configs.items() if c['kind']=='policy' and best_family in c['families'])
    artifact_hashes={}
    for summary in summaries.values(): artifact_hashes.update(summary['model_hashes'])
    for path in [A/'rule_weights.npy',A/'calibrator.pkl',A/'rule_calibrator.pkl',D/'lexical_vectors_cv4.pkl',D/'retriever_refit.pkl',R/'metrics/blocker_selection.json',R/'metrics/policy_selection.json',R/'metrics/single_group_selection.json',R/'metrics/model_rule.json',R/'protocol.json',R/'manifests/split_summary.json',R/'manifests/TIER2_FIXED_PLAN.json',R/'tier2_run.py',*[R/name for name in ['final_run.py','decision_run.py','training.py','statistics_run.py','work/representation/rep.py','work/statistics/analysis_tools.py']],*[R/f'metrics/model_{n}.json' for n in model_names]]:
        artifact_hashes[str(path.relative_to(R))]=sha256(path)
    for config in configs.values(): config['artifact_hashes']=artifact_hashes
    lock={'root':str(R),'document':'FINAL_CONFIGS.md','configs':configs,'resource_hashes':{'data_derived/sealed_test.parquet':json.loads((R/'manifests/split_summary.json').read_text())['sealed_test_sha256']},'selection':selection,'policies':policies,'best_single':single,'aliases':{'E7-1_REF':ref,'E7-1_BEST_VAL':best_config},'source_protocol_sha256':sha256(R/'protocol.json'),'classification':P['status'],'metric_definitions':{'workflow_cost_denominator':'all within-test-fold cross-platform pairs, same denominator across blockers','workflow_AP':'all cross-platform pairs; unscored candidates/positives carry bottom rank through weighted mass, no classifier rows fabricated','policy_seed_aggregation':'mean metric across every declared optimizer seed; no seed selection','factorial_rule_calibration':'M* selected calibration algorithm, fitted on rule OOF; method not re-selected','test_opening':'one sealed resource open per exact configuration; cached representations allowed after authorization'}}
    path=R/'FINAL_CONFIGS.md'
    lines=['# Final Configurations — EXPLORATORY', '', 'ค่าทุกตัวและ artifacts ถูกตรึงก่อน --final; ไม่มี test-selected threshold/model/seed.', 'E7-1 REF ใช้ best lexical blocker + lexical GBDT + validation-F1; BEST-VAL alias ไป configuration ที่มีอยู่ ไม่ evaluate ซ้ำเพื่อนับยอด.', 'Eight E7-2 cells: B0 vs hybrid × tuned rule vs frozen M* × fixed0.5 vs best validation policy. Rule calibration ใช้ algorithm เดียวกับ M* และ fit บน rule OOF โดยไม่ reselect.', 'จำนวน final configurations อาจไม่เท่า planned19 เพราะนับ atomic access configurations แยกจาก grouped experiment variants; รายงาน actual จาก access log.', '', '| Config | Experiment | Kind | Blocker | Matcher / families |','|---|---|---|---|---|']
    for key,c in configs.items(): lines.append(f"| {key} | {c['exp_id']} | {c['kind']} | {c['blocker']} | {c.get('matcher','—')} / {','.join(c.get('families',[]))} |")
    lines.extend(['','## Frozen artifact SHA-256',*['- '+k+': '+v for k,v in artifact_hashes.items()]])
    path.write_text('\n'.join(lines)+'\n')
    lock['document_sha256']=sha256(path)
    (R/'manifests/final_lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    commit=commit_files([R/'final_run.py',R/'decision_run.py',R/'FINAL_CONFIGS.md',R/'manifests/final_lock.json'],'Freeze all final test configurations and artifact hashes before access')
    print(json.dumps({'final_lock_commit':commit,'configs':len(configs),'test_opened':False}),flush=True)
    return lock


class FinalContext:
    def __init__(self):
        self.frames={}
        self.embedding=None
        self.pairs={}
        self.features={}
        self.scores={}
        self.timings=[]
        with (D/'lexical_vectors_cv4.pkl').open('rb') as f: self.vectors=pickle.load(f)
        with (D/'retriever_refit.pkl').open('rb') as f: self.retriever=pickle.load(f)
        with (A/'calibrator.pkl').open('rb') as f: self.calibrator=pickle.load(f)
        with (A/'rule_calibrator.pkl').open('rb') as f: self.rule_calibrator=pickle.load(f)
    def embeddings(self,df):
        if self.embedding is None:
            t=time.monotonic()
            model=load_encoder()
            load_seconds=time.monotonic()-t
            times=[]
            for _ in range(5):
                t=time.monotonic()
                current=encode_scope(model,df)
                times.append(time.monotonic()-t)
                if self.embedding is None:
                    self.embedding=current
                elif any(not np.allclose(self.embedding[k],current[k],rtol=1e-5,atol=1e-6) for k in current):
                    raise ValueError('frozen encoder inference changed beyond tolerance')
            self.timings.append({'stage':'final_profile_embedding','seconds':float(np.median(times)),'profiles':len(df),'measurement_repetitions':5,'model_load_seconds':load_seconds,'ms_per_1000_profiles':float(np.median(times))*1e6/len(df)})
            del model
        return self.embedding
    def get_pairs(self,df,method):
        if method not in self.pairs:
            b0=rep.b0_pairs(df) if 'B0' not in self.pairs else self.pairs['B0']
            embeddings=None if method in ['B0','sparse'] else self.embeddings(df)['retrieval']
            times=[]
            pairs=None
            for _ in range(5):
                t=time.monotonic()
                current=rep.b0_pairs(df) if method=='B0' else rep.retrieval(df,self.retriever,embeddings,50,method,budget=len(b0))
                times.append(time.monotonic()-t)
                if pairs is not None and not np.array_equal(pairs,current): raise ValueError('frozen retrieval changed candidate keys')
                pairs=current
            self.pairs.setdefault('B0',b0)
            self.pairs[method]=pairs
            self.timings.append({'stage':'candidate_'+method,'seconds':float(np.median(times)),'pairs':len(pairs),'measurement_repetitions':5,'ms_per_1000':float(np.median(times))*1e6/len(pairs)})
        return self.pairs[method]
    def get_features(self,df,method):
        if method not in self.features:
            pairs=self.get_pairs(df,method)
            embeddings=self.embeddings(df)
            times=[]
            first=None
            for _ in range(5):
                t=time.monotonic()
                lex,names,groups=rep.lexical_features(df,pairs,self.vectors)
                sem=rep.semantic_features(embeddings,pairs,df)
                times.append(time.monotonic()-t)
                if first is not None and (not np.array_equal(first[0],lex) or not np.array_equal(first[1],sem)):
                    raise ValueError('feature transformation mutated values')
                if first is None: first=(lex,sem)
            self.features[method]=first
            self.timings.append({'stage':'pair_feature_'+method,'seconds':float(np.median(times)),'pairs':len(pairs),'measurement_repetitions':5,'ms_per_1000':float(np.median(times))*1e6/len(pairs)})
        return self.features[method]
    def get_scores(self,df,method,name):
        key=(method,name)
        if key not in self.scores:
            lex,sem=self.get_features(df,method)
            if name=='rule':
                weights=np.load(A/'rule_weights.npy')
                times=[]
                raw=None
                for _ in range(5):
                    t=time.monotonic()
                    current=(lex@weights)[None,:]
                    times.append(time.monotonic()-t)
                    if raw is not None and not np.array_equal(raw,current): raise ValueError('rule inference changed scores')
                    raw=current
                self.timings.append({'stage':'model_rule','pairs':len(lex),'seconds':float(np.median(times)),'measurement_repetitions':5,'ms_per_1000':float(np.median(times))*1e6/len(lex)})
            else:
                summary=json.loads((R/f'metrics/model_{name}.json').read_text())
                raw=[]
                for path in summary['model_paths']:
                    with (R/path).open('rb') as f: bundle=pickle.load(f)
                    X=lex if bundle['feature']=='lexical' else sem if bundle['feature']=='semantic' else np.concatenate([lex,sem],axis=1)
                    if bundle['columns'] is not None: X=X[:,bundle['columns']]
                    times=[]
                    # five actual repeats, predictions must be identical.
                    predicted=None
                    for _ in range(5):
                        t=time.monotonic()
                        candidate=bundle['model'].predict_proba(X)[:,1]
                        times.append(time.monotonic()-t)
                        if predicted is not None and not np.array_equal(predicted,candidate): raise ValueError('inference mutated predictions')
                        predicted=candidate
                    self.timings.append({'stage':'model_'+name,'seed':bundle['seed'],'pairs':len(X),'seconds':float(np.median(times)),'measurement_repetitions':5,'ms_per_1000':float(np.median(times))*1e6/len(X)})
                    raw.append(predicted)
                raw=np.stack(raw)
            self.scores[key]=raw
        return self.scores[key]


def workflow_metric(y,score,d,gt,all_pairs,n_profiles):
    out=metrics(y,score,d,total_positives=gt,n_profiles=n_profiles,cost=(2,1,.1))
    recall=out['end_to_end_recall']
    precision=out['precision']
    out['end_to_end_f1']=2*precision*recall/(precision+recall) if precision+recall else 0.
    out['workflow_cost_per_all_cross_platform_pair']=out['raw_cost']/all_pairs
    misses=gt-int(y.sum())
    unseen_neg=all_pairs-len(y)-misses
    if unseen_neg<0: raise ValueError('workflow population accounting failed')
    extended_y=np.r_[y,1,0]
    extended_score=np.r_[score,-1.,-1.]
    weights=np.r_[np.ones(len(y)),misses,unseen_neg]
    out['workflow_ap_all_pairs']=float(average_precision_score(extended_y,extended_score,sample_weight=weights))
    out['workflow_ap_note']='unscored cross-product mass ranked below every scored pair; virtual metric mass, not synthetic classifier rows'
    out['all_cross_platform_pairs']=all_pairs
    out['false_merges_per_1000_profiles']=out['fp']*1000/n_profiles
    return out


def run_final():
    lock=json.loads((R/'manifests/final_lock.json').read_text())
    require_committed(R/'FINAL_CONFIGS.md')
    context=FinalContext()
    outdir=R/'data_derived/final'
    outdir.mkdir(exist_ok=True)
    summaries={}
    for config_id,cfg in lock['configs'].items():
        with job(cfg['exp_id'],f'final-{config_id}',{'final_config_id':config_id,'lock_sha256':sha256(R/'manifests/final_lock.json'),'config':{k:v for k,v in cfg.items() if k!='artifact_hashes'}},final_evals=1,category='final_evaluation') as rec:
            data=guarded_read(R/'data_derived/sealed_test.parquet',final=True,config_id=config_id,lock=lock,access_log=R/'ledger/test_access.jsonl')
            df=pd.read_parquet(io.BytesIO(data))
            pairs=context.get_pairs(df,cfg['blocker'])
            summary=pair_summary(df,pairs)
            entity=df.entity.to_numpy()
            y=(entity[pairs[:,0]]==entity[pairs[:,1]]).astype(np.int8)
            rec.update({'final_config_id':config_id,'kind':cfg['kind'],'blocker':cfg['blocker'],'population':summary})
            payload={'pairs':pairs,'y':y,'entity_a':entity[pairs[:,0]],'entity_b':entity[pairs[:,1]],'all_entities':entity,'gt_pairs':ground_truth(df)}
            if cfg['kind']=='blocking':
                gt=ground_truth(df)
                n=len(df)
                pkeys=pairs[:,0].astype(np.int64)*n+pairs[:,1]
                gkeys=gt[:,0].astype(np.int64)*n+gt[:,1]
                found=np.isin(gkeys,pkeys)
                payload.update(found=found,gt_entity=entity[gt[:,0]])
            else:
                all_scores=context.get_scores(df,cfg['blocker'],cfg['matcher'])
                raw=all_scores.mean(axis=0)
                lex,_=context.get_features(df,cfg['blocker'])
                nsim=np.maximum(lex[:,1],lex[:,8]).astype(float)
                payload.update(raw_score=raw,seed_scores=all_scores,nsim=nsim)
                # Predeclared aggregate robustness/error strata; no manual claims.
                platform_codes=pd.Categorical(df.platform,categories=sorted(df.platform.unique())).codes
                payload['stratum_platform_pair']=np.sort(platform_codes[pairs],axis=1)
                presence=lex[:,[5,12,19,26,33]].astype(np.int8)
                payload['stratum_presence_pattern']=(presence*(1<<np.arange(5))).sum(axis=1)
                payload['stratum_username_low']=(lex[:,1]<.5)
                payload['stratum_both_names_low']=(nsim<.5)
                non_ascii=np.array([any(ord(c)>127 for c in a+b) for a,b in zip(df.fullname,df.bio)])
                payload['stratum_non_ascii_text']=non_ascii[pairs[:,0]]|non_ascii[pairs[:,1]]
                if cfg['kind']=='matcher':
                    model=json.loads((R/'metrics/model_rule.json' if cfg['matcher']=='rule' else R/f"metrics/model_{cfg['matcher']}.json").read_text())
                    point=model['operating_points']
                    d=(raw>=point['validation_F1_threshold']).astype(np.int8)*2
                    measure=workflow_metric(y,raw,d,summary['ground_truth_pairs'],summary['all_cross_platform_pairs'],len(df))
                    target_d=(raw>=point['precision_target_threshold']).astype(np.int8)*2
                    achieved=workflow_metric(y,raw,target_d,summary['ground_truth_pairs'],summary['all_cross_platform_pairs'],len(df))
                    measure['validation_selected_precision_target']=achieved
                    measure['test_precision_target_met']=achieved['precision']>=P['P_target']
                    measure['seed_AP']=[float(average_precision_score(y,s)) for s in all_scores]
                    measure['seed_AP_SD']=float(np.std(measure['seed_AP'],ddof=1)) if len(all_scores)>1 else 0.
                    rec['metrics']=measure
                    payload.update(decision=d)
                else:
                    times=[]
                    calibrated=None
                    for _ in range(5):
                        t=time.monotonic()
                        current=apply_calibrator(context.rule_calibrator if cfg['matcher']=='rule' else context.calibrator,raw)
                        times.append(time.monotonic()-t)
                        if calibrated is not None and not np.array_equal(calibrated,current): raise ValueError('calibration inference changed scores')
                        calibrated=current
                    context.timings.append({'stage':'calibration','config':config_id,'seconds':float(np.median(times)),'pairs':len(y),'measurement_repetitions':5,'ms_per_1000':float(np.median(times))*1e6/len(y)})
                    payload['calibrated_score']=calibrated
                    family_metrics={}
                    for family in cfg['families']:
                        specs=lock['policies']['families'][family]
                        decisions=[]
                        for spec in specs:
                            times=[]
                            decision=None
                            for _ in range(5):
                                t=time.monotonic()
                                current=decisions_for_policy(spec,calibrated,nsim)
                                times.append(time.monotonic()-t)
                                if decision is not None and not np.array_equal(decision,current): raise ValueError('policy inference changed decisions')
                                decision=current
                            decisions.append(decision)
                            context.timings.append({'stage':'policy_'+family,'config':config_id,'seed':spec.get('seed'),'seconds':float(np.median(times)),'pairs':len(y),'measurement_repetitions':5,'ms_per_1000':float(np.median(times))*1e6/len(y)})
                        measures=[workflow_metric(y,calibrated,d,summary['ground_truth_pairs'],summary['all_cross_platform_pairs'],len(df)) for d in decisions]
                        numeric=[k for k,v in measures[0].items() if isinstance(v,(int,float))]
                        family_metrics[family]={'means':{k:float(np.mean([m[k] for m in measures])) for k in numeric},'seed_SD':{k:float(np.std([m[k] for m in measures],ddof=1)) if len(measures)>1 else 0. for k in numeric},'per_seed':measures,'n_seeds':len(specs),'seed_aggregation':'arithmetic mean; no best seed selection'}
                        payload['cost_'+family]=np.mean([per_pair_cost(y,d) for d in decisions],axis=0)
                        payload['decision_'+family]=np.stack(decisions)
                    rec['families']=family_metrics
                    if cfg['kind']=='factorial': rec['factor_levels']=cfg['factor_levels']
            np.savez(outdir/f'{config_id}.npz',**payload)
            rec['prediction_artifact_sha256']=sha256(outdir/f'{config_id}.npz')
            rec['prediction_artifact_path']=str((outdir/f'{config_id}.npz').relative_to(R))
            summaries[config_id]=rec
    (R/'metrics/final_summary.json').write_text(json.dumps({'classification':P['status'],'configs':summaries,'aliases':lock['aliases'],'timings':context.timings,'final_configs_sha256':lock['document_sha256']},indent=2)+'\n')
    print(json.dumps({'final_evaluation_complete':True,'configurations':len(summaries),'classification':P['status']}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--final',action='store_true')
    args=parser.parse_args()
    if args.prepare: prepare_lock()
    elif args.final: run_final()
    else: raise PermissionError('must explicitly choose --prepare or --final')
