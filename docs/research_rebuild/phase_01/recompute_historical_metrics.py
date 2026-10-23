#!/usr/bin/env python3.11
"""Read-only historical reanalysis. No repository evaluator/model imports.
Run: uv run --offline --python 3.11 python docs/research_rebuild/phase_01/recompute_historical_metrics.py
All writes are constrained to this script's assigned directory; sources are hashed
before reading and again before output. Assertions fail closed on identity errors.
"""
from pathlib import Path
import hashlib
import json
import math
import platform
import pandas as pd
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
assert OUT == ROOT / 'docs/research_rebuild/phase_01'
V2 = 'experiments/icsec_final/authoritative_run_v2'
R1 = 'experiments/icsec_final/authoritative_run_v2r1'
REV = 'experiments/icsec_final/reviewer_revision'
FULL = 'artifacts/decisioning/feature_aware_ga/one_stage_weighted_full_2m_20260914'
SOURCES, CHECKS, ROWS, COMPARISONS = {}, [], [], []


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def source(rel):
    p = ROOT / rel
    assert p.is_file(), rel
    digest = sha(p)
    if rel in SOURCES:
        assert SOURCES[rel]['sha256'] == digest, 'source changed during reading'
    SOURCES[rel] = {'sha256': digest, 'bytes': p.stat().st_size}
    return p


def parquet(rel, columns=None):
    return pd.read_parquet(source(rel), columns=columns)


def jread(rel):
    return json.loads(source(rel).read_text(encoding='utf-8'))


def check(name, **details):
    CHECKS.append({'check': name, 'pass': True, **details})


def keyed(f):
    assert f.pair_key.notna().all()
    assert not f.pair_key.duplicated().any(), 'duplicate pair keys'
    return f.set_index('pair_key').sort_index()


def equal_keys_labels(a, b, name, decision=False):
    aa, bb = keyed(a), keyed(b)
    assert aa.index.equals(bb.index), name + ': key identity'
    for col in ['actual', 'pair_type'] + (['decision'] if decision else []):
        if col in aa and col in bb:
            assert aa[col].equals(bb[col]), name + ': ' + col
    check(name, rows=len(a), duplicates=0, labels_equal=True, join='stable pair_key')


def ratios(tp, fp, fn, rp, rn):
    div = lambda a, b: a/b if b else 0.0
    return dict(precision=div(tp,tp+fp), conditional_recall=div(tp,tp+fn),
                automatic_recall=div(tp,tp+fn+rp),
                conditional_F1=div(2*tp,2*tp+fp+fn),
                automatic_F1=div(2*tp,2*tp+fp+fn+rp), U=2*fp+fn+.1*(rp+rn))


def metrics(f, family, partition, method, scope, artifact, status='INDEPENDENTLY_RECOMPUTED'):
    assert f.actual.isin([0,1]).all() and f.decision.isin([0,1,2]).all()
    y, d = f.actual, f.decision
    tp=int(((y==1)&(d==2)).sum()); fp=int(((y==0)&(d==2)).sum())
    fn=int(((y==1)&(d==0)).sum()); rp=int(((y==1)&(d==1)).sum())
    rn=int(((y==0)&(d==1)).sum()); tn=int(((y==0)&(d==0)).sum())
    n=len(f); candidates=int((f.pair_type!='BLOCKING_MISS').sum())
    assert tp+fp+fn+rp+rn+tn==n and tp+fn+rp==int(y.sum())
    row=dict(family=family,partition=str(partition),method=method,scope=scope,status=status,
             rows=n,candidates=candidates,positive_support=int(y.sum()),TP=tp,FP=fp,FN=fn,
             R_positive=rp,R_negative=rn,REVIEW=rp+rn,TN_candidate=tn,
             blocking_misses=int((f.pair_type=='BLOCKING_MISS').sum()),
             exact_rows=int((f.pair_type=='AUTO_EXACT').sum()),
             scored_rows=int((f.pair_type=='MODEL_SCORED').sum()),
             review_rate=(rp+rn)/candidates if candidates else None,
             candidate_coverage=1-(rp+rn)/candidates if candidates else None,
             c_FP=2,c_FN=1,c_REVIEW=.1,artifact=artifact,**ratios(tp,fp,fn,rp,rn))
    ROWS.append(row)
    return row


def compare(row, reported, mapping, artifact, tolerance=1e-10):
    deltas={}
    for old,new in mapping.items():
        if old in reported:
            delta=float(row[new])-float(reported[old]); deltas[old]=delta
    passed=all(abs(v)<=tolerance for v in deltas.values())
    COMPARISONS.append(dict(family=row['family'],partition=row['partition'],method=row['method'],
                            scope=row['scope'],summary_artifact=artifact,agrees=passed,deltas=deltas))
    return passed


def endpoint_key(f, a, b):
    x=pd.to_numeric(f[a],errors='raise').astype('int64')
    y=pd.to_numeric(f[b],errors='raise').astype('int64')
    assert ((x>=0)&(y>=0)&(x<2**32)&(y<2**32)&(x!=y)).all()
    return np.minimum(x,y)*2**32+np.maximum(x,y)


def run_icsec():
    cache={}
    common_map={'TP':'TP','FP':'FP','FN':'FN','REVIEW':'REVIEW','precision':'precision',
                'recall':'conditional_recall','F1':'conditional_F1','U':'U'}
    for family,base in [('ICSEC_V2',V2),('ICSEC_V2R1',R1)]:
        for seed in [101,202,303]:
            parent=f'{base}/scientific_outputs/outer_{seed}'
            summpath=f'{parent}/summary.json'; summary=jread(summpath)
            labels=parquet(f'{V2}/scientific_inputs/outer_{seed}/sealed_test_labels/labels.parquet')
            routes=parquet(f'{V2}/scientific_inputs/outer_{seed}/blocking_misses/same_role_routes.parquet')
            keyed(labels); keyed(routes)
            expected_miss=set(routes.loc[routes.role=='SEALED_TEST','pair_key'])
            reference=None
            for method in ['GB17_B0','B0','B1','B2','B3']:
                path=f'{parent}/decisions/{method}_workflow.parquet'; f=parquet(path)
                keyed(f)
                assert f.pair_type.isin(['AUTO_EXACT','MODEL_SCORED','BLOCKING_MISS']).all()
                miss=f[f.pair_type=='BLOCKING_MISS']; candidate=f[f.pair_type!='BLOCKING_MISS']
                assert set(miss.pair_key)==expected_miss
                assert (miss.actual==1).all() and (miss.decision==0).all()
                labeljoin=candidate.merge(labels,on='pair_key',how='outer',validate='one_to_one',
                                           indicator=True,suffixes=('_decision','_label'))
                assert (labeljoin._merge=='both').all()
                assert (labeljoin.actual_decision==labeljoin.actual_label).all()
                if reference is not None:
                    equal_keys_labels(reference,f,f'{family}/{seed}/{method} common workflow')
                reference=f
                for scope,ptype,filetail in [('EXACT_TIER','AUTO_EXACT','exact_tier'),
                                              ('MODEL_SCORED','MODEL_SCORED','model_scored')]:
                    component_path=f'{parent}/decisions/{method}_{filetail}.parquet'
                    component=parquet(component_path)
                    equal_keys_labels(component,f[f.pair_type==ptype],component_path,decision=True)
                    metrics(component,family,seed,method,scope,component_path)
                metrics(miss,family,seed,method,'BLOCKING_MISS',path)
                wr=metrics(f,family,seed,method,'WORKFLOW',path)
                compare(wr,summary[method],common_map,summpath)
                check(f'{family}/{seed}/{method} exact+scored+miss=workflow',
                      exact=wr['exact_rows'],scored=wr['scored_rows'],miss=wr['blocking_misses'],
                      positive_support=wr['positive_support'],sealed_labels_consistent=True)
                cache[(family,seed,method)]=f
    # Compare the two frozen families by key, never by parquet ordering.
    for seed in [101,202,303]:
        for method in ['GB17_B0','B0','B1','B2','B3']:
            equal_keys_labels(cache[('ICSEC_V2',seed,method)],cache[('ICSEC_V2R1',seed,method)],
                              f'V2 vs V2R1/{seed}/{method}',decision=True)
    revpath=f'{REV}/metrics_per_seed.csv'; reported=pd.read_csv(source(revpath))
    assert len(reported)==18 and not reported.duplicated(['seed','policy']).any()
    mapping={'TP':'TP','FP':'FP','FN':'FN','positive_REVIEW':'R_positive','REVIEW':'REVIEW',
             'candidates':'candidates','workflow_rows':'rows','precision':'precision',
             'decision_recall':'conditional_recall','end_to_end_recall':'automatic_recall',
             'decision_F1':'conditional_F1','end_to_end_F1':'automatic_F1','coverage':'candidate_coverage',
             'review_rate':'review_rate','U':'U'}
    for seed in [101,202,303]:
        for method in ['GB17_B0','B0','B1','B2','B3','Chow']:
            if method=='Chow':
                path=f'{REV}/outer_{seed}/Chow_workflow.parquet'; f=parquet(path)
                equal_keys_labels(f,cache[('ICSEC_V2R1',seed,'B0')],f'Chow vs common/{seed}')
                # Verify saved Chow actions against persisted p, not tune a new policy.
                scored=f[f.pair_type=='MODEL_SCORED']; p=scored.calibrated_probability.to_numpy()
                assert np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
                expected=np.argmin(np.column_stack([p,np.full(len(p),.1),2*(1-p)]),axis=1)
                assert np.array_equal(expected,scored.decision.to_numpy())
                assert (f.loc[f.pair_type=='AUTO_EXACT','decision']==2).all()
                assert (f.loc[f.pair_type=='BLOCKING_MISS','decision']==0).all()
                check(f'Chow persisted action equation/{seed}',tie_order='NO_MATCH,REVIEW,MATCH')
            else:
                f=cache[('ICSEC_V2R1',seed,method)]
                path=f'{R1}/scientific_outputs/outer_{seed}/decisions/{method}_workflow.parquet'
            row=metrics(f,'REVIEWER_REVISION',seed,method,'WORKFLOW',path)
            rr=reported[(reported.seed==seed)&(reported.policy==method)].iloc[0].to_dict()
            compare(row,rr,mapping,revpath)
    assert sum(r['family']=='REVIEWER_REVISION' for r in ROWS)==18
    aggregate_path=f'{REV}/aggregate.json'; aggregate=jread(aggregate_path)
    verified=pd.DataFrame([r for r in ROWS if r['family']=='REVIEWER_REVISION'])
    for method,values in aggregate.items():
        z=verified[verified.method==method]
        assert len(z)==3
        for statistic in ['mean','sample_sd']:
            recomputed: dict={new:float(np.mean(np.asarray(z[new],dtype=float)) if statistic=='mean' else np.std(np.asarray(z[new],dtype=float),ddof=1))
                        for old,new in mapping.items() if old in values}
            rr={old:record[statistic] for old,record in values.items()}
            recomputed.update(family='REVIEWER_AGGREGATE',partition=statistic,method=method,scope='PER_PARTITION_AGGREGATE')
            compare(recomputed,rr,mapping,aggregate_path)


def run_full():
    path=f'{FULL}/full_2m_pair_decisions.parquet'; f=parquet(path)
    f['pair_key']=endpoint_key(f,'profile_id_a','profile_id_b'); keyed(f)
    legacy=parquet('experiments/scored_pairs_enriched.parquet')
    legacy['pair_key']=endpoint_key(legacy,'profile_id_a','profile_id_b'); keyed(legacy)
    join=f.merge(legacy[['pair_key','actual','split','decision_source']],on='pair_key',
                 how='outer',validate='one_to_one',indicator=True,suffixes=('','_legacy'))
    assert (join._merge=='both').all()
    for col in ['actual','split','decision_source']:
        assert (join[col]==join[col+'_legacy']).all()
    candidates=parquet(f'{V2}/candidates/workflow.parquet')
    candidates['pair_key']=endpoint_key(candidates,'profile_row_id_a','profile_row_id_b'); keyed(candidates)
    cj=f[['pair_key','decision_source']].merge(candidates[['pair_key','pair_type']],on='pair_key',
                                              how='outer',validate='one_to_one',indicator=True)
    assert (cj._merge=='both').all()
    assert ((cj.decision_source=='AUTO_EXACT')==(cj.pair_type=='AUTO_EXACT')).all()
    check('full2M vs legacy vs V2 candidate endpoint identity',rows=len(f),duplicates=0,
          labels_equal=True,source_tiers_equal=True,join='canonical unordered endpoint integer key')
    # Independent endpoint label check and cross-platform positive denominator.
    profpath='data_for_project/normalized_profiles_with_profile_id.csv'
    profiles=pd.read_csv(source(profpath),keep_default_na=False,low_memory=False)
    for c in ['profile_row_id','profile_id']:
        profiles[c]=pd.to_numeric(profiles[c],errors='coerce')
    profiles=profiles[profiles.profile_row_id.notna()&profiles.profile_id.notna()].copy()
    profiles.profile_row_id=profiles.profile_row_id.astype('int64')
    assert not profiles.profile_row_id.duplicated().any()
    profiles.platform=profiles.platform.astype(str).str.lower().str.strip()
    prof=profiles.set_index('profile_row_id')
    fa=f.profile_id_a.map(prof.user_folder); fb=f.profile_id_b.map(prof.user_folder)
    assert fa.notna().all() and fb.notna().all()
    actual=((fa==fb)&(fa!='')).astype('int8')
    assert (actual==f.actual).all()
    assert (f.profile_id_a.map(prof.platform)!=f.profile_id_b.map(prof.platform)).all()
    gt=[]; all_positive=0; same_positive=0
    for _,g in profiles[profiles.user_folder.astype(str).str.strip()!=''].groupby('user_folder'):
        rs=list(g[['profile_row_id','platform']].itertuples(index=False,name=None))
        all_positive+=len(rs)*(len(rs)-1)//2
        for i,(a,pa) in enumerate(rs):
            for b,pb in rs[i+1:]:
                if pa==pb: same_positive+=1
                else: gt.append(min(a,b)*2**32+max(a,b))
    gt=set(gt); candidate_keys=set(f.pair_key); missing_keys=gt-candidate_keys
    assert set(f.loc[f.actual==1,'pair_key'])==gt&candidate_keys
    opaque_miss=parquet(f'{V2}/scientific_inputs/outer_101/blocking_misses/positive_pairs.parquet')
    digest=lambda k: hashlib.sha256(f'v2-pair:{k//2**32}:{k%2**32}'.encode()).hexdigest()
    assert set(opaque_miss.pair_key)=={digest(k) for k in missing_keys}
    check('full2M independent cross-platform ground truth accounting',eligible_profiles=len(profiles),
          all_platform_positive=all_positive,same_platform_positive=same_positive,
          cross_platform_positive=len(gt),candidate_positive=int(f.actual.sum()),
          blocking_misses=len(missing_keys),global_miss_keys_match_v2=True)
    scope=jread(f'{V2}/preflight/candidate_scope.json')
    assert len(gt)==scope['cross_platform_positives'] and len(missing_keys)==scope['cross_platform_blocking_misses']
    mpath=f'{FULL}/full_2m_metrics_by_split.csv'; reports=pd.read_csv(source(mpath))
    policies=[c.removesuffix('_decision_code') for c in f.columns if c.endswith('_decision_code')]
    assert len(policies)==4 and len(reports)==16
    f['pair_type']=np.where(f.decision_source=='AUTO_EXACT','AUTO_EXACT','MODEL_SCORED')
    fullmap={'tp':'TP','fp':'FP','fn':'FN','tn':'TN_candidate','review':'REVIEW',
             'rows':'rows','positive_support':'positive_support','precision':'precision',
             'recall':'automatic_recall','f1':'automatic_F1','cost':'U'}
    for split in ['val','test','drop','all']:
        selected=f if split=='all' else f[f.split==split]
        for policy in policies:
            z=selected[['pair_key','actual','pair_type']].copy()
            z['decision']=selected[policy+'_decision_code']
            assert (selected[policy+'_decision']==selected[policy+'_decision_code'].map({0:'NO_MATCH',1:'REVIEW',2:'MATCH'})).all()
            row=metrics(z,'FULL2M_10GENE',split,policy,'CANDIDATE',path)
            rr=reports[(reports.split==split)&(reports.policy==policy)].iloc[0].to_dict()
            compare(row,rr,fullmap,mpath)
            for scope_name,ptype in [('EXACT_TIER','AUTO_EXACT'),('MODEL_SCORED','MODEL_SCORED')]:
                metrics(z[z.pair_type==ptype],'FULL2M_10GENE',split,policy,scope_name,path)
            if split=='all':
                misses=pd.DataFrame({'pair_key':sorted(missing_keys),'actual':1,'pair_type':'BLOCKING_MISS','decision':0})
                workflow=pd.concat([z,misses],ignore_index=True); keyed(workflow)
                wr=metrics(workflow,'FULL2M_10GENE',split,policy,'WORKFLOW_CROSS_PLATFORM',path,
                           status='RECOMPUTED_PLUS_INDEPENDENT_GT_MISSES')
                assert wr['positive_support']==len(gt)
    check('full2M split workflow limitation',note='No split-local workflow correction inferred from V2 roles; splits differ. Only global workflow reconstructed.')


def summary_only():
    # Keep reported rows distinct. Counts copied from summary are NOT verified.
    tidy='experiments/r0_r5_summary_tidy.csv'; f=pd.read_csv(source(tidy))
    for rr in f.to_dict('records'):
        ROWS.append(dict(family='R_SERIES_REPORTED',partition=rr['split'],method=rr['config'],scope='LEGACY_WORKFLOW_REPORTED',
                         status='REPORTED_NOT_INDEPENDENTLY_VERIFIED',artifact=tidy,TP=int(rr['TP']),FP=int(rr['FP']),FN=int(rr['FN']),
                         REVIEW=int(rr['REVIEW']),reported_precision=rr['precision'],reported_recall=rr['recall'],reported_F1=rr['F1']))
    for name in ['r1_results.json','r2_results.json','r3_results.json','r4_privacy_tradeoff.json','r6_results.json']:
        jread('experiments/'+name)
    r6=jread('experiments/r6_results.json')
    for section in ['splits','ga_rules']:
        for split,rr in r6[section].items():
            ROWS.append(dict(family='R_SERIES_REPORTED',partition=split,method='R6' if section=='splits' else 'R6_GA',
                             scope='LEGACY_WORKFLOW_REPORTED',status='REPORTED_NOT_INDEPENDENTLY_VERIFIED',
                             artifact='experiments/r6_results.json',**{k:rr[k] for k in ['TP','FP','FN','REVIEW']},
                             reported_precision=rr['precision'],reported_recall=rr['recall'],reported_F1=rr['F1']))
    suite=jread('pub_multi/ref/suite_report.json'); source('pub_multi/ref/suite_lb.csv')
    for rr in suite['runs']:
        ROWS.append(dict(family='MULTIMODAL_REPORTED',partition='test',method=rr['run_name'],scope='SAMPLED_SUPERVISED_PAIRS',
                         status='REPORTED_NOT_INDEPENDENTLY_VERIFIED',artifact='pub_multi/ref/suite_report.json',
                         reported_precision=rr['test_precision'],reported_recall=rr['test_recall'],reported_F1=rr['test_f1'],
                         reported_AP=rr['test_avg_precision'],reported_AUC=rr['test_roc_auc'],
                         validation_F1=rr['val_f1'],validation_AP=rr['val_avg_precision'],feature_count=rr['feature_count']))
    # Aggregated confusion matrices provide arithmetic consistency, not row-level verification.
    for name in ['base_report.json','img_stats_report.json','main_report.json']:
        report=jread('pub_multi/ref/'+name); m=report['metrics']; cm=m.get('confusion_matrix')
        if cm:
            tn,fp=cm[0];fn,tp=cm[1]; calc=ratios(tp,fp,fn,0,0)
            check('multimodal summary arithmetic/'+name,status='SUMMARY_ARITHMETIC_ONLY',
                  F1_delta=calc['automatic_F1']-m['test_f1'],rows=tn+fp+fn+tp)
            assert abs(calc['automatic_F1']-m['test_f1'])<1e-12


def report():
    df=pd.DataFrame(ROWS)
    workflow=df[(df.family=='REVIEWER_REVISION')&(df.scope=='WORKFLOW')]
    avg=workflow.groupby('method')[['TP','FP','FN','R_positive','R_negative','REVIEW','conditional_recall','automatic_recall',
                                   'conditional_F1','automatic_F1','U']].mean().sort_values('U')
    header=['method']+list(avg.columns)
    table='| '+' | '.join(header)+' |\n|'+ '|'.join(['---']*len(header))+'|\n'
    for method,rr in avg.iterrows():
        table+='| '+method+' | '+' | '.join(f'{v:.6f}' if 'recall' in k or 'F1' in k else f'{v:.2f}' for k,v in rr.items())+' |\n'
    per=[]
    for seed in ['101','202','303']:
        z=workflow[workflow.partition==seed].set_index('method')
        winner='/'.join(z.index[np.isclose(z.U,z.U.min(),rtol=0,atol=1e-10)])
        bestf='/'.join(z.index[np.isclose(z.automatic_F1,z.automatic_F1.max(),rtol=0,atol=1e-12)])
        per.append(f'| {seed} | {winner} | {z.U.min():.1f} | {bestf} | {z.automatic_F1.max():.6f} | {z.loc["B3","U"]-z.loc["B2","U"]:+.1f} |')
    full=df[(df.family=='FULL2M_10GENE')&(df.partition=='all')&(df.scope.isin(['CANDIDATE','WORKFLOW_CROSS_PLATFORM']))]
    ft='| policy | scope | TP | FP | FN | R+ | R− | automatic recall | automatic F1 | U |\n|---|---|---:|---:|---:|---:|---:|---:|---:|---:|\n'
    for rr in full.sort_values(['scope','U']).to_dict('records'):
        ft+=f'| {rr["method"]} | {rr["scope"]} | {rr["TP"]:.0f} | {rr["FP"]:.0f} | {rr["FN"]:.0f} | {rr["R_positive"]:.0f} | {rr["R_negative"]:.0f} | {rr["automatic_recall"]:.6f} | {rr["automatic_F1"]:.6f} | {rr["U"]:.1f} |\n'
    failed=[c for c in COMPARISONS if not c['agrees']]
    exact=df[(df.family=='ICSEC_V2R1')&(df.method=='B0')&(df.scope=='EXACT_TIER')]
    et='\n'.join(f'- outer {r.partition}: exact N={r.rows:.0f}, TP={r.TP:.0f}, FP={r.FP:.0f}, precision={r.precision:.9f}' for r in exact.itertuples())
    rowscope=df.groupby(['family','status']).size()
    inventory='\n'.join(f'- {fam}: {int(n)} metric rows — {status}' for (fam,status),n in rowscope.items())
    refs='\n'.join(f'| `{p}` | `{v["sha256"]}` |' for p,v in sorted(SOURCES.items()))
    text=f'''# 04 — เปรียบเทียบผลประวัติด้วยการคำนวณใหม่จาก persisted artifacts

## สถานะและขอบเขต

นี่เป็น **read-only retrospective audit** ไม่ใช่การทดลองใหม่ ไม่ train, optimize, download, unpickle model หรือเรียก evaluator ของประวัติ ทุก output อยู่ใน `docs/research_rebuild/phase_01/` เท่านั้น

- Script: `recompute_historical_metrics.py`; ตารางเครื่องอ่าน: `verified_metrics.csv` / `verified_metrics.json`
- รันด้วย `uv run --offline --python 3.11 python docs/research_rebuild/phase_01/recompute_historical_metrics.py`
- อ่าน source/hash และคำนวณ counts จาก granular decisions โดยตรง ไม่คัดลอก counts จาก audit วันที่ก่อน
- Numerical agreement ไม่รับรอง raw provenance, label-access history, scorer independence, licensing หรือ causal superiority

{inventory}

## นิยามที่ใช้

`TP/FP` คือ positive/negative MATCH, `FN` คือ positive NO_MATCH (รวม blocking misses เมื่อ scope เป็น WORKFLOW), `R+`/`R−` คือ positive/negative REVIEW. `TN_candidate` นับเฉพาะ negative NO_MATCH ที่มีแถว ไม่ใช่ true negatives ทั้ง universe.

- precision = TP/(TP+FP)
- conditional recall = TP/(TP+FN); conditional F1 = 2TP/(2TP+FP+FN)
- automatic recall = TP/(TP+FN+R+); automatic F1 = 2TP/(2TP+FP+FN+R+)
- U = 2FP + FN + 0.1(R+ + R−), เป็น declared scenario ไม่ใช่ต้นทุนธุรกิจที่พิสูจน์แล้ว
- candidate coverage = 1−REVIEW/(EXACT_TIER+MODEL_SCORED); ตัวส่วนไม่รวม missed positives
- ไม่สมมติว่า human review แก้ R+ ถูกทั้งหมด

## ICSEC V2/V2R1 และ reviewer revision

V2 และ V2R1 มี 5 methods × 3 outer seeds ต่อ family; ตรวจ workflow, exact, scored และ miss แยกกัน ส่วน reviewer revision เป็น 6 methods × 3 seeds = **18 cases** (5 methods เดิม reuse V2R1 + Chow ที่บันทึกเพิ่ม) ไม่ใช่ 18 การทดลองอิสระ.

ตรวจด้วย stable `pair_key` ที่ sort/index และ one-to-one joins: ไม่มี duplicate key, key set/labels/pair_type เหมือนกันข้าม methods, label ตรงกับ sealed persisted labels, exact/scored components ตรง workflow และ misses ตรง SEALED_TEST routes. V2/V2R1 decisions ตรงกันเมื่อเทียบด้วย key ทุก method/seed. Chow saved decisions ตรง argmin `[p,.1,2(1−p)]` โดย tie order NO_MATCH→REVIEW→MATCH. ไม่ใช้ positional joins.

### Mean ข้าม 3 partitions (ค่าเฉลี่ย per-partition ไม่ใช่ pooled confusion)

{table}

### Winner เฉพาะกลุ่มเทียบได้: U ต่ำสุด / automatic F1 สูงสุด

| seed | min-U method | U | max automatic-F1 method | automatic F1 | U(B3)−U(B2) |
|---|---|---:|---|---:|---:|
{chr(10).join(per)}

B3 เป็น mean-U ต่ำสุดของ frozen reviewer group แต่ paired differences B3−B2 เล็ก/กลับทิศ และจำนวน outer partitions เพียง 3; ไม่ใช่หลักฐาน GA superiority, equivalence หรือ deployment recommendation. U winner ไม่จำเป็นต้องเป็น automatic-F1 winner. GB-17/GB-18 เปลี่ยน representation จึงไม่ใช่ optimizer-only comparison.

### Exact-tier errors ไม่เท่ากับศูนย์

{et}

## Full2M 10-gene: candidate ไม่ใช่ workflow

ยืนยัน unordered endpoint key identity ระหว่าง projection parquet, legacy cache และ V2 global candidate artifact ครบทุกแถว; labels/split/decision_source ตรงกันและไม่มี duplicate/self pair. Labels คำนวณซ้ำจาก endpoint→user_folder ผ่าน profile-row ID map ไม่จับคู่ตามตำแหน่ง. Positive universe คำนวณจาก eligible profile groups และ platform โดยไม่ใช้ constants จาก summary.

{ft}

จำนวน global candidate positives=25,931; independent cross-platform universe=29,243; blocking misses=3,312 (opaque keys ตรง persisted V2 miss artifact). All-platform positives=29,247 มี same-platform positives 4 คู่ ต้องไม่ปนกับ cross-platform denominator. exact=12,403 และ scored=2,073,842 รวม candidates=2,086,245.

10-gene แถว `all` candidate recall/F1/U คำนวณซ้ำตรง summary แต่เมื่อนับ misses workflow recall/F1/U เปลี่ยนตามตาราง. U เพิ่ม 3,312 สำหรับทุก policy เพราะ misses เป็น FN ร่วมกัน; ranking ในกลุ่มนี้ไม่เปลี่ยน. 10-gene เป็น U ต่ำสุดใน full2M frozen group ขณะที่ legacy_name_guard เป็น automatic-F1 สูงสุด (ไม่ใช่ claim superiority ของ optimizer). Full projection รวม validation/drop rows จึงไม่ใช่ held-out generalization. `val/test/drop` รายงาน candidate เท่านั้น: ไม่เติม V2 per-role misses ให้ legacy split เพราะเป็นคนละ split protocol. Model-scored/exact metrics แยกใน CSV.

## R-series และ multimodal: reported ไม่ใช่ independently verified

- R0–R5 tidy summary และ R6 summaries อยู่ในตารางพร้อม status `REPORTED_NOT_INDEPENDENTLY_VERIFIED`; ไม่เติม R+/R− จากการเดาย้อนสูตร ไม่ประกาศ key/label equivalence ข้าม R variants เมื่อไม่มี row-level decisions ที่ตรวจใน package นี้
- R-series ใช้ harness historical automatic denominator และต้นทุนเก่า (FP,FN,REVIEW)=(5,1,.02) ไม่ใช่ U=(2,1,.1) ของ ICSEC; script ไม่ปลอม U ใหม่จาก incomplete review-class counts. R3 F1=0.8373 เป็น reported test-F1 leader เฉพาะ numbered R0–R6 methods; manual_stage18 control มี reported test F1=0.8439 สูงกว่า แต่ FP=632 เทียบ R3 FP=38 และใช้ cost/rule ต่างกัน (experiments/r1_results.json#/rules/test/manual_stage18; experiments/r3_results.json#/rules/test/R3_ga). จึงไม่ใช่ R3 ชนะทุก metric หรือทุก historical control ไม่พิสูจน์ว่า GA เป็นเหตุของ gain และไม่รับรองคำว่า unbiased ในรายงานเก่า
- Multimodal suite เป็น sampled supervised pairs, ไม่ใช่ cross-platform workflow. Summary image_stats test F1=0.9340467605 มากกว่า image_context 0.9340136843; image_context เป็น reported composite/validation-F1 leader และมี AP สูงสุด แต่ไม่ใช่ test-F1 leader. ห้ามเลือก best model ใหม่จาก test
- ตรวจ arithmetic ของ persisted confusion matrices กับ F1 ใน base/img_stats/main reports เท่านั้น; **SUMMARY_ARITHMETIC_ONLY ไม่ใช่ independent row-level reproduction**. ไม่โหลด missing historical models/รัน inference เพื่อกลบช่องว่าง

## แปลความเปลี่ยนแปลงทีละ comparable development group

| Contrast | สิ่งเปลี่ยน/สิ่งคงไว้ตาม historical protocol | ผล/การตีความที่อนุญาต |
|---|---|---|
| R0→R1 | เปลี่ยน downstream four-parameter policyบน oldscore/cache; predictorไม่ฝึกใหม่ | reportedtest TP5864→6231,FP88→23,REVIEW8783→3116,F1.7964→.8292 จึงไม่ใช่เพิ่มF1ด้วยreviewมากขึ้นอย่างเดียว แต่ scorerindependenceยังไม่ยืนยัน |
| R2→R3 | ใช้ reconstructed17+MiniLM scorerเดียวในresultfamilyแล้วเปลี่ยน policy | reportedtest TP5157→6347,FP19→38,REVIEW1115→640,F1.7393→.8373 เป็นtrade-offอัตโนมัติที่reported ไม่ใช่ row-reproducedcleanablation |
| R4→R5 | Bloomrepresentationต่อLเดียวกันแล้วเปลี่ยนmanual→GApolicy | ที่L2000 reportedtestF1.7397→.8329,TP5158→6303,FP14→57,REVIEW766→700; Lต่างกันเปลี่ยนrepresentation/privacyscenarioด้วย ห้ามเอามาปนoptimizer-only |
| R6 manual→R6 GA | semantic/hashmodelprobabilityเดิมปรับpolicy; retrievalevaluationเป็นอีกpopulation | reportedtestF1.6053→.7801,TP3817→5620,REVIEW224→3712; gainมีทั้งMATCHเพิ่มและREVIEWเพิ่ม แต่retrievalmissrecoveryต่ำและไม่ใช่V2blockingcomparator |
| multimodal text→stats→context | เปลี่ยนfeaturemodalityภายในsampled-suiteprotocol; savedpairidentities/orderยังไม่ได้reproduceทั้งsuite | imagecontextreportedvalidation/composite/APleader; imgstatstestF1สูงกว่านิดเดียว ไม่มีหลักฐานว่าimagebranchชนะfullworkflow |
| GB17_B0→GB18_B0 | representationเพิ่มbert_cos; sameV2pairs/roles/trainindices/modelparams,B0policy; models/calibratorsต้องfitแยก | conditionalF1.849436→.850965,automaticF1.829952→.841952 แต่ meanU2351.97→2364.20 แย่ขึ้น; ไม่สรุปfeature18ดีกว่าทุกmetric |
| B0→B1 | fixed→validation-tunedtwothreshold; sameGB18 probabilities | automaticF1.841952→.866722 และpositiveREVIEW160.67→430.00; seed202/303มีMATCHเพิ่มเพียงเล็กน้อย ต้องแยกabstentionbenefit |
| B1→B2 | expandednamepolicy+searchdomainเปลี่ยน; notstrictlynested | meanUลดแต่automaticF1ลดจาก.866722เป็น.861105; ไม่ใช่pureoptimizercontrast |
| B2→B3 | identicalexpandedclass/bounds/data/objective/budget ต่างoptimizer | meanU1860.03→1858.23 แต่automaticF1.861105→.861031; pairedU −5.5/0/+.1 จึงยังไม่พิสูจน์GA superiority |
| full2Mpolicycontrols→10gene | weightedpolicyclass/evidenceเปลี่ยน ไม่ใช่เฉพาะoptimizer | lowerU/lessREVIEWกว่าlegacyguard แต่automaticF1ต่ำกว่า;รวมmissesและdevelopmentprojectionก่อนตีความ |

Sources exact results: `experiments/r1_results.json#/rules/test`, `experiments/r2_results.json#/splits/test`, `experiments/r3_results.json#/rules/test`, `experiments/r4_privacy_tradeoff.json#/per_L/2000`, `experiments/r6_results.json#/splits/test` และ `#/ga_rules/test`; V2/fullsourcesตามSHA-256tableและ`verified_metrics.json`. สองทางแรกเป็นreportedhistoricalcontrastsเท่านั้น ไม่รับรองpairedkeysโดยดูcountsตรงกัน

Historicalclassifierbenchmark/tuning/strict/sigmoidvariantsในmatrix02เปลี่ยนtrainingpopulation/config/calibrationจนไม่ควรรวมกับsuite3variants: GBเป็นreportedmainselection,strictlogreg+sigmoidเป็นอีกselectionlineage ไม่มีexternalresultสำหรับwinnerใหม่ และpost-hoctestthresholdsweepsไม่เป็นfairselectionevidence [02_HISTORICAL_EXPERIMENT_MATRIX.md:29–33; experiment_lineage.json] Phase1ไม่เลือกmodel/policyจากtestหรือทำcontrolledevaluationใหม่

## เทียบ historical summaries

ทั้งหมด {len(COMPARISONS)} comparisons; agree={len(COMPARISONS)-len(failed)}, disagree={len(failed)} ภายใต้ tolerance 1e−10. รายละเอียด mapping และ raw deltas ทุก field อยู่ใน JSON. V2/R1 เปรียบ recall/F1 กับ conditional นิยามเดิม, reviewer กับ conditional+automatic (รวม independent mean/sample SD จาก 3 partitions), full2M summary กับ automatic candidate. Agreement ต่าง scope ไม่แปลว่า headline เก่าเป็น workflow.

## ข้อจำกัด/การใช้ผล

ผลนี้ยืนยัน numerical layer ของแถวประวัติเท่านั้น ไม่เปลี่ยน policy หรือแก้ frozen sources. ไม่เปรียบ F1 ข้าม ICSEC/R-series/multimodal เป็น leaderboard เดียว. สำหรับ scientific claims ใหม่ต้องใช้ protocol ใหม่ที่ freeze ก่อนรัน โดย phase นี้ไม่ได้อนุญาตการรันนั้น.

## แหล่งข้อมูลและ SHA-256 ของ bytes ที่อ่าน

Hashes ด้านล่างถูกคำนวณก่อนอ่านและตรวจอีกครั้งก่อนเขียน outputs; identifiers/path เป็น repository-relative. Script hash และ environment อยู่ใน JSON. รายการนี้เป็น source list ไม่ใช่ manifest ของทั้ง repo.

| exact path | SHA-256 |
|---|---|
{refs}
'''
    return df,text


def self_test():
    f=pd.DataFrame({'pair_key':['a','b','c','d'],'actual':[1,1,0,0],
                    'decision':[2,1,1,0],'pair_type':['MODEL_SCORED']*4})
    a=keyed(f); b=keyed(f.iloc[::-1]); assert a.equals(b)
    r=ratios(1,0,0,1,1); assert r['conditional_recall']==1 and r['automatic_recall']==.5
    try:
        keyed(pd.concat([f,f.iloc[:1]]))
    except AssertionError:
        pass
    else:
        raise AssertionError('duplicate fixture must fail')
    check('synthetic formula/key fixtures',status='NOT_SCIENTIFIC_EVIDENCE',
          row_order_invariant=True,duplicate_rejected=True,positive_review_denominator=True)


if __name__=='__main__':
    self_test(); run_icsec(); run_full(); summary_only()
    # Include read-only implementation/protocol sources, without importing/executing them.
    for rel in ['docs/reports/ICSEC_REVIEW_REPO_AUDIT_TH.md','docs/plans/EXPERIMENT_REWRITE_PROTOCOL_TH.md',
                f'{V2}/final_runner.py',f'{V2}/real_adapters.py','experiments/code/reviewer_revision.py',
                'experiments/code/project_one_stage_to_full_2m.py','experiments/code/exp_lib.py',
                'experiments/REPORT_R0_R5.md',f'{REV}/aggregate.json']:
        source(rel)
    df,text=report()
    for rel,record in SOURCES.items():
        assert sha(ROOT/rel)==record['sha256'], 'historical input mutated: '+rel
    payload={'description':'Read-only persisted historical metric recomputation; no training/optimization',
             'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,
             'script_sha256':sha(Path(__file__)), 'metric_rows':len(ROWS),
             'reviewer_cases':18,'source_hashes':SOURCES,'checks':CHECKS,
             'summary_comparisons':COMPARISONS,'metrics':ROWS}
    df.to_csv(OUT/'verified_metrics.csv',index=False)
    (OUT/'verified_metrics.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (OUT/'04_RESULT_COMPARISON_TH.md').write_text(text,encoding='utf-8')
    print(json.dumps({'metric_rows':len(ROWS),'reviewer_cases':18,'checks':len(CHECKS),
                      'summary_comparisons':len(COMPARISONS),
                      'summary_disagreements':sum(not c['agrees'] for c in COMPARISONS),
                      'sources_unchanged':len(SOURCES),'outputs':str(OUT)},indent=2))
