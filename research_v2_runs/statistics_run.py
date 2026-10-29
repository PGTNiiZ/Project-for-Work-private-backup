"""Lead-only post-final inference on frozen predictions; no retraining."""
from pathlib import Path
import itertools
import json
import sys
import numpy as np
from sklearn.metrics import average_precision_score
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'work/statistics'))
from analysis_tools import bootstrap_contrast,holm,metrics
from runtime import job,commit_files
P=json.loads((R/'protocol.json').read_text())


def load_final(name):
    return dict(np.load(R/f'data_derived/final/{name}.npz'))


def aligned(a,b):
    if not np.array_equal(a['pairs'],b['pairs']) or not np.array_equal(a['y'],b['y']):
        raise ValueError('paired contrast prediction keys or labels do not align')
    if len(np.unique(a['pairs'],axis=0))!=len(a['pairs']):
        raise ValueError('duplicate final prediction keys')


def entity_codes(data):
    unique=np.unique(data['all_entities'])
    return np.searchsorted(unique,data['entity_a']),np.searchsorted(unique,data['entity_b']),len(unique)


def bootstrap_primary():
    lock=json.loads((R/'manifests/final_lock.json').read_text())
    selection=lock['selection']
    lex=load_final('matcher-GBDT-lexical')
    fused=load_final('matcher-GBDT-fusion')
    single=load_final('matcher-'+lock['best_single'])
    rule=load_final('matcher-rule')
    comparisons={'H1':(lex,single),'H2':(lex,rule),'H3':(fused,lex)}
    results={}
    for hypothesis,(a,b) in comparisons.items():
        aligned(a,b)
        ea,eb,n=entity_codes(a)
        with job('E7-1',f'primary-{hypothesis}',{'contrast':P['primary_contrasts'][hypothesis],'metric':'candidate_AP','bootstrap':P['statistics'],'SESOI':P['SESOI'][hypothesis]},category='aggregate_statistics') as rec:
            result=bootstrap_contrast(a['y'],a['raw_score'],b['raw_score'],ea,eb,n,B=10000,seed=4242,se_soi=P['SESOI'][hypothesis])
            sa=a['seed_scores']
            sb=b['seed_scores']
            deltas=[float(average_precision_score(a['y'],sa[i])-average_precision_score(a['y'],sb[i if len(sb)>1 else 0])) for i in range(len(sa))]
            result['seed_delta_SD']=float(np.std(deltas,ddof=1)) if len(deltas)>1 else 0.
            result['seed_deltas']=deltas
            result['population']='same B_star candidate set in locked test fold'
            result['n_pairs']=len(a['y'])
            result['n_entities']=n
            rec.update(result)
            results[hypothesis]=result
    ga=load_final('policy-E6-5')
    baseline=lock['policies']['best_non_GA']
    exp='E6-2' if baseline=='validation_F1' else 'E6-3' if baseline in ['closed_cost','Chow'] else 'E6-4'
    bg=load_final('policy-'+exp)
    aligned(ga,bg)
    ea,eb,n=entity_codes(ga)
    unique=np.unique(ga['all_entities'])
    gt=ga['gt_pairs']
    # Candidate row keys are positional safe keys, never original profile IDs.
    n_profiles=len(ga['all_entities'])
    keys=ga['pairs'][:,0].astype(np.int64)*n_profiles+ga['pairs'][:,1]
    gtkeys=gt[:,0].astype(np.int64)*n_profiles+gt[:,1]
    missed=~np.isin(gtkeys,keys)
    missed_codes=np.searchsorted(unique,ga['all_entities'][gt[missed,0]])
    with job('E7-1','primary-H4',{'contrast':P['primary_contrasts']['H4'],'baseline_selected_on_development':baseline,'bootstrap':P['statistics'],'SESOI':P['SESOI']['H4'],'seed_aggregation':'mean expected cost across every predeclared seed'},category='aggregate_statistics') as rec:
        result=bootstrap_contrast(ga['y'],ga['cost_GA'],bg['cost_'+baseline],ea,eb,n,kind='cost',B=10000,seed=4242,se_soi=.05,missed_entity=missed_codes,cost=(2,1,.1))
        actual_ga=ga['decision_GA']
        actual_base=bg['decision_'+baseline]
        def costs(ds):
            return np.array([2*np.sum((d==2)&(ga['y']==0))+np.sum((d==0)&(ga['y']==1))+.1*np.sum(d==1)+int(missed.sum()) for d in ds],float)
        ca,cb=costs(actual_ga),costs(actual_base)
        if len(cb)==1: cb=np.repeat(cb,len(ca))
        seed_delta=(cb-ca)/cb
        result.update({'baseline':baseline,'seed_delta_SD':float(seed_delta.std(ddof=1)),'seed_deltas':seed_delta.tolist(),'population':'same B_star candidate workflow plus every blocked positive','n_pairs':len(ga['y'])+int(missed.sum()),'n_entities':n,'missing_positives':int(missed.sum())})
        rec.update(result)
        results['H4']=result
    a=load_final('blocking-'+selection['hybrid'])
    b=load_final('blocking-'+selection['best_lexical'])
    if not np.array_equal(a['gt_pairs'],b['gt_pairs']): raise ValueError('blocking GT populations differ')
    unique=np.unique(a['all_entities'])
    e=np.searchsorted(unique,a['gt_entity'])
    with job('E7-1','primary-H5',{'contrast':P['primary_contrasts']['H5'],'exact_budget':'fold-local B0 unique pair count','bootstrap':P['statistics'],'SESOI':P['SESOI']['H5']},category='aggregate_statistics') as rec:
        result=bootstrap_contrast(np.ones(len(e),np.int8),a['found'].astype(float),b['found'].astype(float),e,e,len(unique),kind='pc',B=10000,seed=4242,se_soi=.02)
        result.update({'seed_delta_SD':0.,'seed_variation_note':'deterministic frozen retrieval, no stochastic retriever seeds','population':'all GT positive cross-platform pairs in locked test fold; matched B0 candidate budget','n_pairs':len(e),'n_entities':len(unique)})
        rec.update(result)
        results['H5']=result
    hs=['H1','H2','H3','H4','H5']
    adjusted=holm([results[h]['p'] for h in hs])
    tost_adjusted=holm([results[h]['tost_p'] for h in hs])
    for h,padj,tost_padj in zip(hs,adjusted,tost_adjusted):
        result=results[h]
        result['holm_adjusted_p']=float(padj)
        result['tost_holm_adjusted_p']=float(tost_padj)
        unstable=result['seed_delta_SD']>=abs(result['delta'])/2 if result['seed_delta_SD']>0 else False
        result['seed_instability_flag']=bool(unstable)
        if padj<.05 and result['ci95'][0]>P['SESOI'][h] and not unstable:
            decision='supported'
        elif result['equivalent'] and tost_padj<.05:
            decision='equivalent'
        elif result['ci95'][1]<P['SESOI'][h]:
            decision='not supported'
        else:
            decision='inconclusive'
        result['decision']=decision
        result['classification']=P['status']
        result['decision_scope']='exploratory LinkSocial only; equivalence uses approximate bootstrap TOST, not exact parametric TOST'
    (R/'metrics/primary_contrasts.json').write_text(json.dumps(results,indent=2)+'\n')
    return results


def secondary():
    lock=json.loads((R/'manifests/final_lock.json').read_text())
    final=json.loads((R/'metrics/final_summary.json').read_text())
    best_family=lock['policies']['best_policy']
    best_key=lock['aliases']['E7-1_BEST_VAL']
    data=load_final(best_key)
    y=data['y']
    decisions=data['decision_'+best_family]
    total_gt=len(data['gt_pairs'])
    misses=total_gt-int(y.sum())
    counts=[]
    for d in decisions:
        counts.append({'tp':int(np.sum((d==2)&(y==1))),'fp':int(np.sum((d==2)&(y==0))),'rejected_pos':int(np.sum((d==0)&(y==1))),'review_pos':int(np.sum((d==1)&(y==1))),'review_neg':int(np.sum((d==1)&(y==0)))})
    mean={k:float(np.mean([c[k] for c in counts])) for k in counts[0]}
    prior_rows=[]
    sanity=json.loads((R/'metrics/label_sanity.json').read_text())
    platform_counts=list(sanity['platform_counts'].values())
    full_pairs=sum(a*b for a,b in itertools.combinations(platform_counts,2))
    full_prior=sanity['cross_platform_positive_pairs']/full_pairs
    for scope in ['candidate','workflow']:
        positives=int(y.sum()) if scope=='candidate' else total_gt
        population=len(y) if scope=='candidate' else final['configs'][best_key]['population']['all_cross_platform_pairs']
        negatives=population-positives
        natural=positives/population
        tpr=mean['tp']/positives
        fpr=mean['fp']/negatives
        fnr=(mean['rejected_pos']+(misses if scope=='workflow' else 0))/positives
        rp=mean['review_pos']/positives
        rn=mean['review_neg']/negatives
        factors=[1.,.5,.1]+([full_prior/natural] if scope=='workflow' else [])
        for factor in factors:
            pi=natural*factor
            denominator=tpr*pi+fpr*(1-pi)
            precision=tpr*pi/denominator if denominator else 0.
            cost=2*fpr*(1-pi)+fnr*pi+.1*(rp*pi+rn*(1-pi))
            prior_rows.append({'scope':scope,'natural_prior':natural,'factor':factor,'assumed_prior':pi,'reweighted_precision':precision,'assumed_expected_cost_per_pair':cost,'assumptions':'conditional TPR/FPR/review rates stable under prior shift; not a newly observed cohort'})
    with job('E7-4','prior-sensitivity',{'factors':[1,.5,.1],'scope':['candidate','workflow'],'configuration':best_key},category='aggregate_statistics') as rec:
        rec.update({'rows':prior_rows})
    sensitivity=[]
    for d in decisions:
        tp=int(np.sum((d==2)&(y==1)))
        fp=int(np.sum((d==2)&(y==0)))
        s1=tp/(tp+fp) if tp+fp else 0.
        s2=1. if tp else 0.
        s2_cost=(np.sum((d==0)&(y==1))+misses+.1*np.sum((d==1)&(y==1)))/total_gt
        sensitivity.append({'S1_precision_unlabeled_as_negative':s1,'S2_precision_unlabeled_excluded':s2,'S2_positive_only_cost_per_positive':float(s2_cost)})
    with job('E7-6','label-sensitivity-S1-S2',{'S3':'NOT RUN: no annotation estimate','configuration':best_key},category='aggregate_statistics') as rec:
        rec.update({'per_seed':sensitivity,'caveat':'S2 removes every unlabeled negative; precision=1 is mechanical and not a demonstrated truth bound; no independent negative or positive label audit'})
    strata=[]
    for field in ['stratum_username_low','stratum_both_names_low','stratum_non_ascii_text','stratum_presence_pattern']:
        values=data[field]
        for value in np.unique(values):
            subset=values==value
            stat=metrics(y[subset],data['calibrated_score'][subset])
            strata.append({'stratum':field,'value':int(value),'n_pairs':int(subset.sum()),'positive_pairs':int(y[subset].sum()),'candidate_AP':stat['candidate_ap'],'definition_note':'non_ascii is script proxy, not language identification; presence pattern is five binary both-present indicators'})
    platform=data['stratum_platform_pair']
    for value in np.unique(platform,axis=0):
        subset=np.all(platform==value,axis=1)
        strata.append({'stratum':'platform_pair_code','value':value.tolist(),'n_pairs':int(subset.sum()),'positive_pairs':int(y[subset].sum()),'candidate_AP':float(average_precision_score(y[subset],data['calibrated_score'][subset])) if y[subset].sum() else 0.})
    with job('E7-3','robustness-strata',{'population':'fixed BEST_VAL predictions','perturbations':'NOT RUN; no newly tuned test perturbation configurations'},category='aggregate_statistics') as rec:
        rec['rows']=strata
    taxonomy=[]
    for d in decisions:
        fp=(d==2)&(y==0)
        fn=(d!=2)&(y==1)
        low=data['stratum_both_names_low'].astype(bool)
        taxonomy.append({'FP_low_both_names':int(np.sum(fp&low)),'FP_other_feature_patterns':int(np.sum(fp&~low)),'FN_low_both_names_in_candidates':int(np.sum(fn&low)),'FN_other_feature_patterns_in_candidates':int(np.sum(fn&~low)),'FN_blocking_miss':misses,'REVIEW_positive_not_auto_linked':int(np.sum((d==1)&(y==1))),'FP_total':int(fp.sum()),'automatic_FN_total':int(fn.sum())+misses})
    with job('E7-7','error-taxonomy-counts',{'taxonomy':'mechanical feature-defined classes only','semantic_causes':['impersonation UNKNOWN','organization UNKNOWN'],'individual_records':'not output'},category='aggregate_statistics') as rec:
        rec.update({'per_seed':taxonomy,'limitations':'No manual attribution of impersonation, organization, or true label error; user_folder categories are operational labels only'})
    cells=[]
    for key,cfg in lock['configs'].items():
        if cfg['kind']!='factorial': continue
        out=final['configs'][key]
        family=cfg['families'][0]
        cells.append({'config':key,**cfg['factor_levels'],'cost':out['families'][family]['means']['workflow_cost_per_all_cross_platform_pair'],'recall':out['families'][family]['means']['end_to_end_recall']})
    effects=[]
    for size in [1,2,3]:
        for factors in itertools.combinations(['blocker','matcher','policy'],size):
            # Difference-of-means coding: 2*mean(product +/-1 * Y).
            cost=2*np.mean([np.prod([2*c[f]-1 for f in factors])*c['cost'] for c in cells])
            recall=2*np.mean([np.prod([2*c[f]-1 for f in factors])*c['recall'] for c in cells])
            effects.append({'factors':list(factors),'cost_effect':float(cost),'recall_effect':float(recall),'scope':'descriptive fixed eight-cell factorial contrast; interactions do not imply external causal generalization'})
    with job('E7-2','factorial-attribution',{'n_cells':8,'coding':'+/-1; effect=2*mean(signproduct*metric)'},category='aggregate_statistics') as rec:
        assert len(cells)==8
        rec.update({'cells':cells,'effects':effects})
    with job('E7-5','measured-compute-cost',{'source':'ledger runtimes + final inference timing','concurrency':'up to two threads per model; multiple CPU runs overlap; walltime != sum CPU task walltimes'},category='aggregate_statistics') as rec:
        rec.update({'timings':final['timings'],'caveat':'recorded inference stages use median of five repeats; model loading separate; training timings are run walltime under declared concurrency; peak training GPU memory not measured, CPU only'})
    cost_stress=[]
    for config_id,cfg in lock['configs'].items():
        if cfg['kind']!='policy': continue
        values=load_final(config_id)
        labels=values['y']
        absent=len(values['gt_pairs'])-int(labels.sum())
        denominator=final['configs'][config_id]['population']['all_cross_platform_pairs']
        for family in cfg['families']:
            for fp_cost,fn_cost,review_cost in P['cost_sensitivity']:
                costs=[(fp_cost*np.sum((d==2)&(labels==0))+fn_cost*(np.sum((d==0)&(labels==1))+absent)+review_cost*np.sum(d==1))/denominator for d in values['decision_'+family]]
                cost_stress.append({'family':family,'cost_weights':[fp_cost,fn_cost,review_cost],'mean_cost_per_all_cross_platform_pair':float(np.mean(costs)),'seed_SD':float(np.std(costs,ddof=1)) if len(costs)>1 else 0.,'thresholds_frozen_at_primary_cost':True,'assumption':'cost scenario, not measured financial outcome'})
    with job('E6-3','frozen-policy-cost-sensitivity',{'cost_scenarios':P['cost_sensitivity'],'retuning':False},category='aggregate_statistics') as rec:
        rec['rows']=cost_stress
    payload={'cost_sensitivity':cost_stress,'prior':prior_rows,'label_sensitivity':sensitivity,'strata':strata,'taxonomy':taxonomy,'factorial_cells':cells,'factorial_effects':effects,'classification':P['status']}
    (R/'metrics/secondary_analyses.json').write_text(json.dumps(payload,indent=2)+'\n')


def independently_check_metrics():
    lock=json.loads((R/'manifests/final_lock.json').read_text())
    final=json.loads((R/'metrics/final_summary.json').read_text())
    checks=[]
    for key,cfg in lock['configs'].items():
        data=load_final(key)
        report=final['configs'][key]
        y=data['y']
        assert int(y.sum())==report['population']['found_positives']
        assert len(data['gt_pairs'])==report['population']['ground_truth_pairs']
        if cfg['kind']=='matcher':
            d=data['decision']
            tp=int(((d==2)&(y==1)).sum())
            fp=int(((d==2)&(y==0)).sum())
            assert tp==report['metrics']['tp'] and fp==report['metrics']['fp']
            assert np.isclose(report['metrics']['end_to_end_recall'],tp/len(data['gt_pairs']))
            assert np.isclose(report['metrics']['candidate_ap'],average_precision_score(y,data['raw_score']))
        elif cfg['kind'] in ['policy','factorial']:
            for name in cfg['families']:
                raw=[]
                for d in data['decision_'+name]:
                    fp=int(((d==2)&(y==0)).sum())
                    fn=int(((d==0)&(y==1)).sum())
                    review=int((d==1).sum())
                    raw.append(2*fp+fn+.1*review+len(data['gt_pairs'])-int(y.sum()))
                assert np.isclose(np.mean(raw),report['families'][name]['means']['raw_cost'])
        checks.append({'configuration':key,'independent_count_check':'PASS'})
    (R/'metrics/independent_metric_check.json').write_text(json.dumps({'checks':checks,'classification':P['status']},indent=2)+'\n')


def main():
    if not (R/'ledger/test_access.jsonl').exists(): raise PermissionError('post-final statistics require completed authorized final access')
    commit_files([R/'statistics_run.py'],'Register post-final paired cluster bootstrap and aggregate sensitivity code')
    independently_check_metrics()
    bootstrap_primary()
    secondary()

if __name__=='__main__': main()
