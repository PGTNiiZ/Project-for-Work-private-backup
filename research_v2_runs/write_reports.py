"""Produce Thai reports and aggregate vector figures from actual frozen results."""
from pathlib import Path
import collections
import csv
import itertools
import json
import os
import sys
import numpy as np
R=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(R/'cache/matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve
from runtime import commit_files
from integrity import sha256
P=json.loads((R/'protocol.json').read_text())
REPORT=R/'reports'


def read(name): return json.loads((R/name).read_text())
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers),*['| '+' | '.join(str(x).replace('|','/') for x in row)+' |' for row in rows]])+'\n'
def number(value): return f'{value:.4f}'
def cite(path,section=''):
    return f'[MAIN@{EVIDENCE_COMMIT[:7]}:research_v2_runs/{path}#{section or "results"}]'
def ledger_latest(): return {r['run_id']:r for r in [json.loads(x) for x in (R/'ledger/runs.jsonl').read_text().splitlines()]}


def counts(lock,final):
    records=list(ledger_latest().values())
    done=[r for r in records if r['status']=='DONE']
    by_exp={}
    for exp in sorted(set(r['exp_id'] for r in done)):
        items=[r for r in done if r['exp_id']==exp]
        by_exp[exp]={k:sum(r.get(k,0) for r in items) for k in ['training_jobs','tuning_fits','validation_evals','final_test_evaluations']}
    operative=0
    for config in lock['configs'].values():
        if config['kind']=='blocking': operative+=1
        elif config['kind']=='matcher': operative+=2
        else: operative+=sum(len(lock['policies']['families'][f]) for f in config['families'])
    return {'classification':P['status'],'DONE_runs':len(done),'FAILED_runs':sum(r['status']=='FAILED' for r in records),'training_jobs':sum(r.get('training_jobs',0) for r in done),'tuning_fits':sum(r.get('tuning_fits',0) for r in done),'validation_atomic_evaluations':sum(r.get('validation_evals',0) for r in done),'validation_search_configurations':sum(r.get('category') in ['hyperparameter_search','rule_parameter_search'] for r in done),'final_access_bundles':len(final['configs']),'final_operating_point_evaluations':operative,'model_seed_AP_diagnostics':sum(len(c['metrics']['seed_AP']) for c in final['configs'].values() if c['kind']=='matcher'),'by_experiment':by_exp,'definitions':'training excludes tuning/calibration/TF-IDF; validation_atomic includes individual held-fold evaluations plus objective calls; final bundles != individual seed/threshold operating points'}


def coverage(counter):
    source=R.parent/'research_v2_review_workspace/research_v2/design/HYPOTHESIS_EXPERIMENT_MATRIX.csv'
    with source.open() as f: matrix=list(csv.DictReader(line for line in f if not line.startswith('#')))
    entries=[]
    done_exps=set(counter['by_experiment'])
    promoted={'E3-1','E4-2','E6-1','E6-6','E7-4','E7-5','E7-6'}
    for row in matrix:
        if row['v2_id_status'].startswith(('ALIAS','RETIRED')): continue
        exp=row['exp_id']
        tier='1' if row['priority']=='ESSENTIAL' or exp in promoted else '2' if row['priority']=='SUPPORTING' else '3' if row['priority']=='CONDITIONAL' else 'outside'
        status='DONE' if exp in done_exps else 'NOT RUN'
        reason=''
        if exp=='D0-1': status='NOT RUN';reason='ไม่มี dual annotation/provenance document; ใช้ DECLARED PASSED ตาม v4 ไม่อ้าง independent verification'
        elif exp=='D0-3': status='NOT RUN';reason='ไม่มี annotation capacity; ใช้ E7-6 S1/S2 ตาม fallback ที่อนุญาต'
        elif exp=='E5-4' and not (R/'metrics/tier2_summary.json').exists(): status='NOT RUN';reason='ยังไม่มี completed supporting ablation summary'
        elif exp=='E9-1':
            status='EXCLUDE';priority='EXCLUDE';reason='v4 ห้าม T9 image-to-image matching; ไม่เปิด conditional gate'
        elif exp in {'E7-3','E7-7'} and status=='DONE':
            status='PARTIAL';reason='strata/mechanical counts เสร็จ แต่ perturbations/manual semantic cause labels ไม่ได้ทำ'
        elif status!='DONE':
            reason='อยู่นอก Tier1 หรือ prerequisite ไม่ผ่าน/ไม่มี runnable frozen configuration; ดู BLOCKER_REGISTER.csv'
        entries.append({'exp_id':exp,'tier':tier,'priority':row['priority'],'status':status,'reason':reason})
    with (REPORT/'EXPERIMENT_COVERAGE.csv').open('w') as f:
        out=csv.DictWriter(f,fieldnames=entries[0].keys());out.writeheader();out.writerows(entries)
    return entries


def figures(final,secondary,blocking):
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
    def save(fig,name):
        fig.text(.5,.005,'EXPLORATORY (LinkSocial, retrospectively exposed)',ha='center',fontsize=7)
        fig.tight_layout(rect=(0,.035,1,1))
        for ext in ['svg','pdf','png']: fig.savefig(R/f'figures/{name}.{ext}',dpi=180)
        plt.close(fig)
    fig,ax=plt.subplots(figsize=(5.2,3.6))
    for name in ['rule','GBDT-lexical','GBDT-fusion']:
        data=np.load(R/f'data_derived/final/matcher-{name}.npz')
        precision,recall,_=precision_recall_curve(data['y'],data['raw_score'])
        idx=np.unique(np.linspace(0,len(recall)-1,min(400,len(recall))).astype(int))
        ax.plot(recall[idx],precision[idx],label=name)
    ax.set(xlabel='Candidate recall',ylabel='Precision',ylim=(0,1.02),xlim=(0,1),title='Locked within-fold candidate population')
    ax.legend(fontsize=8);save(fig,'pr_curves')
    fig,ax=plt.subplots(figsize=(5.2,3.6))
    for method in ['sparse','dense','hybrid_union','hybrid_rrf']:
        points=[]
        for k in P['retrieval_k']:
            rows=[r for r in blocking['rows'] if r['method']==method and r['budget_mode']=='k' and r['k']==k]
            points.append((sum(r['candidate_pairs'] for r in rows),sum(r['found_positives'] for r in rows)/sum(r['ground_truth_pairs'] for r in rows)))
        ax.plot(*zip(*points),marker='o',markersize=3,label=method)
    ax.set(xlabel='Unique candidate pairs (sum of four development folds)',ylabel='Pair Completeness',title='Development PC–candidate budget')
    ax.legend(fontsize=7);save(fig,'pc_candidate_curve')
    fig,ax=plt.subplots(figsize=(5.2,3.6))
    scenarios=P['cost_sensitivity']
    for family in ['Chow','GA','scrambled_sobol','TPE','random','three_way']:
        rows=[r for r in secondary['cost_sensitivity'] if r['family']==family]
        ys=[next(r for r in rows if r['cost_weights']==s)['mean_cost_per_all_cross_platform_pair'] for s in scenarios]
        ax.plot(range(len(ys)),ys,marker='o',markersize=3,label=family)
    ax.set_xticks(range(len(scenarios)),[':'.join(map(str,s)) for s in scenarios],fontsize=7)
    ax.set(xlabel='ASSUMPTION cost ratios FP:FN:REVIEW',ylabel='Expected cost / cross-platform pair',title='Frozen-policy cost sensitivity (no retuning)')
    ax.legend(fontsize=7);save(fig,'cost_sensitivity')
    lock=read('manifests/final_lock.json')
    data=np.load(R/'data_derived/final/policy-E6-5.npz')
    fig,ax=plt.subplots(figsize=(4,3.6))
    for key,label in [('raw_score','Uncalibrated'),('calibrated_score',lock['policies']['calibrator'])]:
        score=data[key];y=data['y']
        bins=np.array_split(np.argsort(score,kind='stable'),15)
        ax.plot([score[b].mean() for b in bins],[y[b].mean() for b in bins],marker='o',markersize=3,label=label)
    ax.plot([0,1],[0,1],ls='--',color='grey',lw=.8)
    ax.set(xlabel='Mean predicted probability',ylabel='Observed positive fraction',title='15 equal-mass reliability bins')
    ax.legend(fontsize=8);save(fig,'calibration_reliability')


def write_all():
    global EVIDENCE_COMMIT
    final=read('metrics/final_summary.json');primary=read('metrics/primary_contrasts.json');secondary=read('metrics/secondary_analyses.json');blocking=read('metrics/blocking_development.json');lock=read('manifests/final_lock.json');sanity=read('metrics/label_sanity.json')
    public=[*sorted((R/'metrics').glob('*.json')),*sorted((R/'manifests').glob('*.json')),R/'ledger/runs.jsonl',R/'ledger/test_access.jsonl',R/'DEVIATIONS.md']
    EVIDENCE_COMMIT=commit_files(public,'Seal aggregate exploratory outcomes and full append-only run ledger')
    counter=counts(lock,final)
    (REPORT/'ACTUAL_EXECUTION_COUNTS.json').write_text(json.dumps(counter,indent=2)+'\n')
    statuses=coverage(counter)
    intro='ทุกผลใหม่ในรายงานนี้เป็น EXPLORATORY (LinkSocial, retrospectively exposed). G0/G1 = DECLARED PASSED by researcher แต่ REFERENCE NOT PROVIDED; G5 = NOT MET. ไม่มี confirmatory result และไม่อ้างโมเดลดีที่สุดทั่วไป.\n\n'
    rows=[]
    for h in ['H1','H2','H3','H4','H5']:
        r=primary[h]
        rows.append([h,P['primary_contrasts'][h],number(r['delta']),f"[{number(r['ci95'][0])}, {number(r['ci95'][1])}]",f"{r['holm_adjusted_p']:.4g}",f"{r['tost_holm_adjusted_p']:.4g}",number(r['seed_delta_SD']),r['decision'],cite('metrics/primary_contrasts.json',h)])
    text='# Results Summary — Research V2\n\n'+intro+'## เหตุใดต้องแยกหลักฐาน\n\nงานนี้ทดสอบผลของ attributes, learner, frozen semantic representation, decision policy และ candidate generation แยกกัน ไม่เปรียบ AP ของ sampled historical test กับ natural candidate test. ประสิทธิภาพปลายทางรวม blocking misses และ REVIEW positives ที่ยังไม่ถูกเชื่อมอัตโนมัติ. '+cite('metrics/final_summary.json')+'\n\n## Primary contrasts\n\nH1–H3 ใช้ Δcandidate AP, H4 ใช้ relative cost reduction (GA เทียบ best non-GA ที่เลือกบน development), H5 ใช้ ΔPC ที่ exact candidate budget เท่ากัน. ค่าบวกสนับสนุนทิศทางที่เสนอ; ไม่ใช่ F1 ของทั้ง pipeline. B=10,000 paired identity/pigeonhole bootstrap; positive edges ใช้ identity multiplicity ครั้งเดียว และ negative dyads ใช้ product ของทั้งสอง endpoint.\n\n'+table(['H','Contrast','Δ','95% CI','Holm p','TOST Holm p','seed Δ SD','Decision','Evidence'],rows)
    text+='\nDecision supported ต้องมีขอบล่าง CI สูงกว่า SESOI และ primary Holm p<0.05 พร้อม seed stability; equivalence ใช้ approximate centered-bootstrap TOST และ CI90 ใน margin พร้อม Holm ของ equivalence family แยก. ไม่อ้าง joint FWER ของสอง families. ค่า p ไม่ใช่ศูนย์; ดู resolution ตาม B ใน JSON. '+cite('metrics/primary_contrasts.json')+'\n\n## Secondary results และขอบเขต\n\nค่า thresholds, calibration และ optimizer ถูกเลือกจาก development เท่านั้น. H4 cost ใช้ ASSUMPTION 2:1:0.1 และ perfect-review utility; automatic recall ไม่นับ reviewed positives เป็น recovered links. Cost sensitivity ใช้ policy ที่ freeze แล้ว ไม่ optimize ใหม่จาก test. '+cite('metrics/secondary_analyses.json')+'\n\nUnivariate features, model/seed summaries, leave-one-attribute-out, learning curves และ robustness strata อยู่ใน THESIS_TABLES_TH.md. Development OOF เป็น selection evidence ที่ถูกใช้ซ้ำ ไม่ใช่ nested independent estimate. ไม่มี human audit จึงรายงาน S1/S2 เท่านั้น; S2 precision=1 เป็นผลเชิงกลจากการเอา unlabeled negatives ออก ไม่ใช่การพิสูจน์ label correctness. '+cite('metrics/secondary_analyses.json','label_sensitivity')+'\n'
    text+='\nH4 เลือก best non-GA จาก development โดยรวม closed-form Chow. Comparator นี้อยู่นอก historical four-gene policy family จึงเป็น overall policy-system comparison ไม่ใช่ isolated GA-versus-search causal effect; การเปรียบเทียบ optimizer แบบ bounds/budget เดียวกันจำกัดที่ GA, random, Sobol และ TPE ใน policy table. H3 equivalence ภายใน margin ไม่ได้แปลว่า semantic ไม่มีประโยชน์ในทุก stratum/ภาษา; near-zero effect อาจติด seed-instability flag โดยไม่ขัดกับ margin-equivalence.\n'
    text+='\nAggregation clarification: H1–H3 ใช้ AP ของ frozen seed-ensemble probabilities ใน paired bootstrap; matcher table แสดง mean/SD ของ AP แยกแต่ละ seed และ PR curvesใช้ensemble. APเป็น nonlinear metric จึงไม่ควรลบ table means เพื่ออ้างว่าเท่ากับ primary Δพอดี. CI ไม่ได้รวม uncertainty จากการเลือก upstream configuration ใหม่.\n'
    (REPORT/'RESULTS_SUMMARY_TH.md').write_text(text)
    t='# Thesis-ready Tables — EXPLORATORY\n\n'+intro
    t+='## Dataset และ evaluation population\n\n'+table(['Item','ค่าที่วัด','Evidence'],[[k,v,cite('metrics/label_sanity.json',k)] for k,v in sanity.items() if isinstance(v,(int,float))])
    t+='\n## Blocking: matched-budget development\n\nPopulation = ผลรวมคู่ภายใน development folds เท่านั้น; ไม่รวมคู่ข้าม folds. ทุกวิธีในตารางมี total |C| เท่ากัน.\n\n'
    rows=[]
    for method in ['B0','sparse','dense','hybrid_union','hybrid_rrf']:
        scope=[r for r in blocking['rows'] if r['method']==method and r['budget_mode']==('native' if method=='B0' else 'matched')]
        c=sum(r['candidate_pairs'] for r in scope);gt=sum(r['ground_truth_pairs'] for r in scope);found=sum(r['found_positives'] for r in scope)
        rows.append([method,c,gt,found,number(found/gt),cite('metrics/blocking_development.json',method)])
    t+=table(['Method','|C|','GT denominator','Found positives','PC','Evidence'],rows)
    t+='\n## Blocking: locked test\n\n'+table(['Method','|C|','GT','PC','RR','Evidence'],[[c['blocker'],c['population']['candidate_pairs'],c['population']['ground_truth_pairs'],number(c['population']['pc']),number(c['population']['rr']),cite('metrics/final_summary.json',key)] for key,c in final['configs'].items() if c['kind']=='blocking'])
    t+='\n## Matcher comparison: natural candidate locked test\n\nทุกแถวใช้ B* และ candidate population เดียวกัน; F1/P/Rcandidate ใช้ validation-F1 threshold ไม่ใช้ test-selected threshold. Primary discrimination ใช้ mean score ของทุก GBDT seed.\n\n'
    rows=[]
    for key,c in final['configs'].items():
        if c['kind']!='matcher':continue
        m=c['metrics'];pop=c['population']
        rows.append([key,pop['candidate_pairs'],pop['found_positives'],number(m['candidate_ap']),number(m['f1']),number(m['precision']),number(m['end_to_end_recall']),number(m['seed_AP_SD']),cite('metrics/final_summary.json',key)])
    t+=table(['Matcher','N candidate','Positives','AP','candidate F1','P','e2e recall','seed AP SD','Evidence'],rows)
    t+='\n## Fusion และ ablations: development OOF เท่านั้น\n\nF-LEX = 35 features; F-SEM = 6 features; fusion = 41 features ไม่ใช่ historical image_context 41 features. ทั้ง username/fullname/bio/location/links ใช้ missingness indicators; leave-one-group-out ตัด semantic features ของ attribute นั้นด้วย. ไม่มีภาพใน V2 run.\n\n'
    modelrows=[]
    for path in sorted((R/'metrics').glob('model_*.json')):
        model=json.loads(path.read_text())
        ap=model.get('mean_score_AP',model.get('development_metrics',{}).get('candidate_ap'))
        modelrows.append([model['name'],number(ap),len(model.get('seeds',[42])),number(model.get('seed_AP_SD',0.)),cite('metrics/'+path.name)])
    t+=table(['Development model','OOF AP','Seeds','AP seed SD','Evidence'],modelrows)
    t+='\n## Policy comparison: expected cost และ automatic links\n\nPopulation = B* candidate set + blocked GT positives สำหรับ utility numerator; cost denominator ในตารางคือ all cross-platform pairs ใน locked fold. Cost ratios 2:1:0.1 เป็น ASSUMPTION ไม่ใช่เงินที่วัดได้. Mean/SD ใช้ทุก optimizer seed ไม่เลือก seed ที่ดีที่สุด.\n\n'
    rows=[]
    for key,c in final['configs'].items():
        if c['kind']!='policy':continue
        for family,values in c['families'].items():
            m,sd=values['means'],values['seed_SD']
            rows.append([family,values['n_seeds'],f"{m['workflow_cost_per_all_cross_platform_pair']:.7f}",f"{sd['workflow_cost_per_all_cross_platform_pair']:.7f}",number(m['precision']),number(m['end_to_end_recall']),number(m['review_rate']),cite('metrics/final_summary.json',key)])
    t+=table(['Policy','Seeds','Cost/all-pair','seed cost SD','Auto P','Auto e2e recall','Review rate|C','Evidence'],rows)
    t+='\n## End-to-end REF และ BEST-VAL\n\nREF คือ best lexical blocker + lexical GBDT + validation-F1; BEST-VAL เป็น bundle ของ best policy บน M* ที่เลือกจาก development. ใช้ alias ไป frozen evaluation เดิม ไม่เปิด test เพื่อสร้างยอดซ้ำ.\n\n'
    rows=[]
    for alias,key in final['aliases'].items():
        c=final['configs'][key]
        m=c['metrics'] if c['kind']=='matcher' else c['families'][lock['policies']['best_policy']]['means']
        rows.append([alias,key,number(m['precision']),number(m['end_to_end_recall']),number(m['end_to_end_f1']),f"{m['workflow_cost_per_all_cross_platform_pair']:.7f}",cite('metrics/final_summary.json',key)])
    t+=table(['Pipeline','Frozen config','Auto P','Auto recall','Auto F1','Cost/all-pair','Evidence'],rows)
    t+='\n## 2×2×2 stage attribution\n\nBlocker0=B0,1=hybrid; matcher0=calibrated tuned rule,1=M*; policy0=fixed0.5,1=best validation policy. ทุกแถวใช้ all cross-platform-pair cost denominator เดียวกัน.\n\n'+table(['Cell','B','M','P','Expected cost/all-pair','Auto recall'],[[c['config'],c['blocker'],c['matcher'],c['policy'],f"{c['cost']:.7f}",number(c['recall'])] for c in secondary['factorial_cells']])+cite('metrics/secondary_analyses.json','factorial_cells')+'\n'
    t+='\n## Compute cost\n\nInference entries เป็น median ของห้ารอบจริงบนเครื่องเดียว; ตารางย่อเป็น median ของ recorded medians เมื่อ stage มีหลาย seed/blocker. ไม่ใช่ deployment benchmark แบบ isolated hardware และไม่เอา sum concurrent runtimes ไปเรียก elapsed time. Encoder หน่วย profiles; ขั้นอื่นหน่วย pairs.\n\n'
    timings=collections.defaultdict(list)
    for r in final['timings']: timings[r['stage']].append(r)
    t+=table(['Stage','Observations','Median seconds','Unit','Repeats/observation'],[[stage,len(v),number(float(np.median([r['seconds'] for r in v]))),'profiles' if 'embedding' in stage else 'pairs',min(r['measurement_repetitions'] for r in v)] for stage,v in timings.items()])+cite('metrics/final_summary.json','timings')+'\n'
    curve_rows=[]
    for learner,exp in [('GBDT','E3-2'),('LR','E3-1')]:
        for fraction in [.1,.25,.5,1.]:
            paths=[]
            for fold in range(4):
                name=f'{exp}--learning-curve-{learner}-frac{fraction}-fold{fold}.json' if fraction<1 else f'{exp}--{learner}-lexical-seed42-oof{fold}.json'
                path=R/'metrics'/name
                if path.exists(): paths.append(path)
            if len(paths)!=4:continue
            values=[json.loads(p.read_text()) for p in paths]
            curve_rows.append([learner,fraction,number(float(np.mean([r['candidate_AP'] for r in values]))),number(float(np.std([r['candidate_AP'] for r in values],ddof=1))),4,'; '.join(cite('metrics/'+p.name) for p in paths)])
    t+='\n## Learning curves: fixed hyperparameters, seed42\n\nAP mean/SD ในตารางนี้เฉลี่ยระหว่างสี่ development folds ไม่ใช่ seed SD. TF-IDF fit เฉพาะ training entities ที่สุ่มเลือก; 100%ใช้ main selected seed42 OOF ไม่ใช้ ensemble. ไม่มี reduced-data tuned-rule comparison เพราะไม่ retune หลังเปิด test.\n\n'+table(['Learner','Entity fraction','Mean fold AP','Fold AP SD','Folds','Evidence'],curve_rows)
    t+='\n### Factorial effects\n\nนิยาม effect=2×mean(sign-product×metric) หรือ2βใน +/-1 coding; interactionนี้ไม่ใช่ raw difference-of-differences และเป็น descriptive component substitution บน corpusนี้เท่านั้น.\n\n'+table(['Factors','Cost effect','Recall effect'],[[' × '.join(r['factors']),f"{r['cost_effect']:.8f}",number(r['recall_effect'])] for r in secondary['factorial_effects']])+cite('metrics/secondary_analyses.json','factorial_effects')+'\n'
    t+='\nFeature benchmark ใช้ common lexical+semantic featurizer จึงไม่ใช่ isolated incremental semantic cost ratio; ไม่อ้าง full H3 ms/pair ratio ที่ไม่ได้วัดแยก. Learning curves ใช้ fixed hyperparameters และ TF-IDF ที่ fit บน selected training identities เท่านั้น; ไม่มีการ retune หลังเปิด test. '+cite('metrics/tier2_summary.json')+'\n'
    (REPORT/'THESIS_TABLES_TH.md').write_text(t)
    historical='# Historical Comparison — ขอบเขตที่เปรียบได้\n\n'+intro+'ไม่มี historical row ที่ใช้ split, candidate cohort, prior, decision semantics และ thresholds เดียวกับรอบใหม่ครบทุกข้อ จึงไม่รายงาน numerical delta หรือ ranking ข้ามรุ่น.\n\n'+table(['Historical result','Population / limitation','การใช้ที่อนุญาต'],[['R3 F1=0.8373','md5 entity-test30%; historical exact tier + misses; test reused ≥15','REFERENCE_ONLY; ไม่เทียบกับ candidate F1'],['Thesis GB AP=0.9789 / F1=0.9340','sampled test8,313 pairs; positives4,387; isotonic; threshold0.35','REFERENCE_ONLY; natural candidate prior ต่างกัน'],['Production precision=0.9550','whole corpus automatic MATCH; ไม่ใช่ heldout fold','REFERENCE_ONLY; ไม่ยืนยัน generalization'],['ICSEC v2 decision F1=0.8903 / revised e2e F1=0.8610','3 historical partitions; REVIEW-positive denominator ต่างกัน','REFERENCE_ONLY; ต้องแยก decision/e2e']])+'\nแหล่ง historical ทั้งหมด: [V2R:METRIC_POPULATION_MAP.md#Metric–Population Map] [V2R:METHODOLOGICAL_RISKS.md#R-15] [V2R:METHODOLOGICAL_RISKS.md#R-18]. ข้อมูลใหม่: '+cite('metrics/final_summary.json')+'\n\nB0 รอบใหม่ replicate key union ใน S1 แต่ exact candidates ไม่ได้รับ privileged AUTO_EXACT MATCH bypass; ทุกคู่ผ่าน matcher/policy เดียวกัน. ดังนั้นแม้ PC ใกล้เดิม ก็ไม่ใช่การ replicate production decision workflow ทั้งเส้น. '+cite('final_run.py','FinalContext')+'\n'
    (REPORT/'HISTORICAL_COMPARISON_TH.md').write_text(historical)
    threats='# Threats to Validity — Research V2\n\n'+intro+'## Label และ authorization\n\nuser_folder เป็น operational identity assumption; G0/G1 ไม่มี documentary references ใน header. มี same-platform username keys ที่พบหลาย identity labels 17 buckets (field ชื่อ components ใน artifact นับ key buckets ไม่ใช่จำนวน final connected components) ตาม aggregate audit จึงใช้ connected components ใน split ไม่ merge ground truth ตามชื่อ. ไม่มี manual positive/negative audit; URL/link features ยังเสี่ยง label proxy. S1/S2 เป็น sensitivity ไม่ใช่การยืนยัน label. '+cite('metrics/leakage_audit.json')+'\n\n## Retrospective exposure และ selection\n\nG5 NOT MET; random split ใหม่ไม่ลบ historical exposure. Development ถูกใช้เลือก blocker/tune classifiers/calibrator/policy ซ้ำ; OOF ไม่ได้เป็น nested independent estimate ของ full pipeline. การเปิด sealed resource ถูก guard ต่อ configuration หลัง commit FINAL_CONFIGS แต่ไม่ได้ทำให้ข้อมูลกลายเป็น confirmatory. '+cite('manifests/final_lock.json')+'\n\n## Population และ prior\n\nคู่ข้าม folds ไม่เข้าชุด candidate ของการประเมิน จึงไม่ใช่ whole-graph production prior. E7-4 มี full-graph prior reweight ตาม frozen plan แต่สมมติ conditional error/review rates ไม่เปลี่ยน ไม่ใช่ข้อมูลใหม่ที่สังเกตได้. AP sampled historical test และ AP natural candidate เทียบตรงไม่ได้. '+cite('metrics/secondary_analyses.json','prior')+'\n\n## Cost, calibration และ review\n\nCost2:1:0.1 รวม sensitivity อีกสามค่าเป็น ASSUMPTION; ไม่มี conversion/outcome labels. REVIEW utility สมมติ perfect review แต่ automatic recall ถือ reviewed positives เป็นยังไม่เชื่อม. Calibration method selection บน reused development OOF ไม่พิสูจน์ calibration ในประชากรอื่น. '+cite('metrics/policy_selection.json')+'\n\n## Statistical limits\n\nBootstrap เป็น paired identity/pigeonhole บน frozen predictions; negative edges ใช้ multiplicity ของ endpoint ทั้งสอง. CI conditional ต่อ models ที่ freeze; seed SD แยกต่างหาก ไม่ใช่ CI ที่ครอบคลุม split/domain uncertainty. TOST เป็น approximate centered-bootstrap; Holm primary differences และ Holm equivalence แยก family ไม่อ้าง joint guarantee10 tests. Secondary ablations/strata/factorial เป็น descriptive exploratory; ไม่ถือเป็น additional confirmatory discoveries. '+cite('metrics/primary_contrasts.json')+'\n\n## Scope และ implementation\n\nCPU MiniLM English revisionถูกตรึง ไม่ครอบคลุม encoder/model families ทั้งหมด; frozen encoderไม่มี fine-tuning. ข้อมูลเป็น LinkSocial เท่านั้น. ไม่มี T9 image-to-image, privacy attack, Lead Scoring หรือ entity-clustering proof. Hyperparameters ของ learning curves ถูกเลือกจาก full development ก่อน freeze จึงเป็น conditional learning curves ไม่ใช่ nested sample-efficiency proof. '+cite('manifests/TIER2_FIXED_PLAN.json')+'\n\n## Privacy และ operational deviations\n\nGitHub metadata ยังเป็น PUBLICทั้งสองrepo; ไม่ push หรือแก้visibility. มี terminal metadata incidentที่เผยชื่อไฟล์ภาพเก่าซึ่งอาจมีhandles; ไม่ลบหรืออ้างว่าไม่เคยเกิด. Output-file PII scan แยกจาก incident นี้; ไม่รับรองzero disclosureของทั้งsession. Operational clockต่อใหม่ตามคำสั่งcontinue; G4 original protocolไม่ถูกแก้. k*freezeเป็นselectionruleและTOST numeric implementation/conservative correctionก่อนfinal เป็นclarifications/deviationsที่เปิดเผย ไม่อ้าง strict literal protocol adherenceทุกข้อ. ดู DEVIATIONS.md และ GATE_RECORD.md.\n'
    (REPORT/'THREATS_TO_VALIDITY_TH.md').write_text(threats)
    blockers=[['G0-REF','เอกสารlabel provenance','UNKNOWN','REFERENCE NOT PROVIDED; researcher declarationเท่านั้น','แนบเอกสารlabel construction/adjudication','researcher'],['G1-REF','เอกสารethics/IRB/PDPA','UNKNOWN','REFERENCE NOT PROVIDED','แนบapprovalและdata-use scope','researcher'],['G5','fresh independent holdout','BLOCKED','LinkSocialย้อนหลังถูกใช้พัฒนาแล้ว','independent licensed/consented cohortก่อนconfirmatoryclaim','researcher'],['PRIVACY-PUBLIC','repository visibility','BLOCKED','live metadata PUBLICขัดprivate declaration','เจ้าของrepoตรวจสิทธิ์/visibility; ไม่เผยแพร่data','owner'],['PRIVACY-TRANSCRIPT','terminal metadata incident','BLOCKED','ชื่อไฟล์historicalอาจฝังhandlesปรากฏในtool transcript','จัดการtranscriptตามนโยบายเจ้าของระบบ; ไม่คัดลอกซ้ำ','owner'],['ANNOTATION','dual annotationและhidden positives','BLOCKED','ไม่มีannotation capacity','ผู้ตรวจสองคนและprotocolแยก; S3ยังไม่ทำ','researcher'],['TIER3','conditional fine-tuning','UNKNOWN','ไม่มีfrozen runnable GPU configuration/inclusion significance procedureก่อนtest','preregisterconditionalprogramใหม่พร้อมvalidation-only trigger','researcher'],['PARTIAL-ROBUSTNESS','perturbationและsemantic cause taxonomy','UNKNOWN','ทำเฉพาะfrozen prediction strata/mechanical counts','protocol perturbationและmanualtaxonomyก่อนnewholdout','researcher']]
    with (R/'BLOCKER_REGISTER.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['id','item','status','reason','unblock_action','owner']);w.writerows(blockers)
    tiers=collections.Counter((r['tier'],r['status']) for r in statuses)
    meanings={'H1':'หลาย lexical attributes เหนือกว่า best single group ที่เลือกจาก development','H2':'GBDT เทียบ tuned rule ที่ selection budget เท่ากัน','H3':'incremental frozen semantic contribution เทียบ lexical-only','H4':'GA เทียบ best non-GA (selected on development), positive Δ หมายถึงลด cost','H5':'hybrid เทียบ best lexical ที่ matched candidate budget'}
    finding_lines=[f"{h}: {meanings[h]}; Δ={number(primary[h]['delta'])}, CI95=[{number(primary[h]['ci95'][0])},{number(primary[h]['ci95'][1])}], decision={primary[h]['decision']} (EXPLORATORY)." for h in ['H1','H2','H3','H4','H5']]
    text='# Execution Handoff — Research V2\n\n'+intro+'## 1. สถานะและที่มาหลักฐาน\n\nOriginal G4 freeze commit932cf956; all final configurations commit81171fd9 ก่อน sealed test access. ไม่แก้ raw data, thesis, immutable v1 หรือ design. Source/metrics evidence commit: '+EVIDENCE_COMMIT+'. '+cite('metrics/final_summary.json')+'\n\n## 2. งานที่เสร็จในแต่ละ tier\n\n'+table(['Tier','DONE IDs','NOT RUN / partial IDs'],[[tier,', '.join(r['exp_id'] for r in statuses if r['tier']==tier and r['status']=='DONE'),', '.join(r['exp_id'] for r in statuses if r['tier']==tier and r['status']!='DONE')] for tier in ['1','2','3']])+'\nรายละเอียดเหตุผลราย ID: EXPERIMENT_COVERAGE.csv. D0-1/D0-3 ไม่มี human audit; ไม่ปลอม κ หรือ hidden-positive rate. Tier2 learning-curve rule baselineไม่ได้ลดinformationbudgetอย่างเท่าเทียม จึงไม่อ้างsampleefficiencyเหนือrule. Tier3/optionalไม่ถูกเปิดโดยใช้testผลเป็นtrigger; T9และLeadScoring EXCLUDE.\n\n## 3. Actual counts เทียบ plan\n\n'+table(['ปริมาณ','MVP plan','MVP+support plan','Actual measured'],[['Selected-model fits',217,414,counter['training_jobs']],['Tuning fits',2400,4800,counter['tuning_fits']],['Final configuration bundles',19,21,counter['final_access_bundles']],['Final operating-point/seed evaluations','หน่วยต่างจากbundle','แยกนับ',counter['final_operating_point_evaluations']],['Validation atomic evaluations','planนับconfigต่างหน่วย','ไม่เทียบตรง',counter['validation_atomic_evaluations']],['Search config evaluations','ไม่รวมfoldmultiplier','แยกจากatomic',counter['validation_search_configurations']]])+'\nActual source = ACTUAL_EXECUTION_COUNTS.json + append-only ledger; trainingไม่รวมcalibration/TF-IDF/tuning. Final bundlesรวมหลายpredeclaredseeds/families; จึงเปิดเผยoperating-point countแยกและไม่กล่าวว่าbundlecountเท่ากับindependentreplications. Originalplannedcounts: [V2R:../design/EXPERIMENTAL_MASTER_PLAN_TH.md#10].\n\n## 4. ข้อค้นพบหลักห้าข้อสำหรับกรรมการ\n\n'+'\n'.join(f'{i+1}. {line}' for i,line in enumerate(finding_lines))+'\n\nทุกข้อมีSESOI, Holm p, CI, seed SDและTOSTใน RESULTS_SUMMARY_TH.md; ไม่มีข้อใดเป็นconfirmatoryหรือuniversallybest. '+cite('metrics/primary_contrasts.json')+'\n\n## 5. สิ่งที่ขาดและเหตุผล\n\nเอกสารG0/G1, independentfreshholdout, humanlabelaudit, trueconversionoutcomes, perturbationprogramและmanualcauseattributionยังขาด. รายงานstrataที่มีอยู่เป็นmechanicalaggregateไม่วินิจฉัยimpersonation. ไม่มีisolatedincrementalsemanticfeaturizercostratio; ไม่แทนค่าที่ไม่ได้วัดด้วยestimate. รายละเอียด BLOCKER_REGISTER.csv และ THREATS_TO_VALIDITY_TH.md.\n\n## 6. Verification\n\nผลตรวจ executable จะ append จาก reports/consistency_check.txt หลังสร้างเอกสารและสแกน PII; ไม่มีการเติมPASSล่วงหน้า.\n\n## 7. ลำดับถัดไป\n\nแก้public-repository/transcript exposureกับเจ้าของระบบ → แนบเอกสารG0/G1 → humanlabel/proxy audit → เลือกlicensed/consented independentcohort → preregisternewconfirmatoryprotocolก่อนแตะlabels → ทำreplicationตามbudgetที่ประกาศ. ระหว่างนี้ใช้ตาราง/รูปเป็นEXPLORATORYเท่านั้นและห้ามpushderivedprofileartifacts.\n'
    (REPORT/'EXECUTION_HANDOFF_TH.md').write_text(text)
    figures(final,secondary,blocking)
    print(json.dumps({'reports_created':5,'figure_families':4,'counts':counter},ensure_ascii=False))

if __name__=='__main__': write_all()
