"""Record the prospective v4 protocol; never read profile records."""
from pathlib import Path
import csv
import datetime as dt
import hashlib
import json
import subprocess

R = Path(__file__).resolve().parent
ROOT = R.parent
D = ROOT / 'research_v2_review_workspace/research_v2/design'
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest()
def cmd(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()
for folder in ['configs','ledger','manifests','reports','figures','metrics','work/representation','work/statistics','data_derived','artifacts','tests']:
    (R / folder).mkdir(parents=True, exist_ok=True)
now = dt.datetime.now(dt.timezone.utc)
protocol = {
    'created_utc': now.isoformat(), 'deadline_provided': False,
    'operational_budget_minutes_assumption': 120,
    'stop_launching_support_fraction': .70, 'reporting_fraction': .85,
    'source_commit': cmd('git','rev-parse','HEAD'),
    'design_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sorted(D.rglob('*')) if p.is_file()},
    'protected_input_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT/'research_v2_review_workspace/_input_v1').rglob('*')) if p.is_file()},
    'raw_input': 'data_for_project/normalized_profiles_with_profile_id.csv',
    'raw_input_sha256': sha(ROOT/'data_for_project/normalized_profiles_with_profile_id.csv'),
    'historical_artifacts': {str(p.relative_to(ROOT)): sha(p) for folder in ['experiments','pub_multi/ref','pub_multi/res','data/processed'] for p in sorted((ROOT/folder).rglob('*')) if p.is_file() and not p.is_symlink()},
    'status': 'EXPLORATORY (LinkSocial, retrospectively exposed)',
    'folds': 5, 'test_fold': 4, 'development_folds': [0,1,2,3], 'split_seed': 42,
    'split_assignment': 'stratify identities by sorted platform multiplicities; seeded shuffle within stratum; greedily assign next identity to smallest fold by entity count then profile count then fold index',
    'pair_routing': 'both endpoints must belong to same fold; train on union of three development fold-local candidate populations; never cross-fold negatives',
    'normalization': 'Unicode NFKC, lowercase, strip and collapse whitespace; null/nan/none sentinel to empty; no identity or predecessor score as feature',
    'label_definition': 'same nonempty canonical user_folder and different platform; all other candidates unlabeled-as-negative S1; S2 removes unlabeled, not a measured upper bound on truth',
    'lexical_groups': ['username','fullname','bio','location','links'],
    'lexical_columns_per_group': ['exact','jaro_winkler','normalized_levenshtein','token_jaccard','tfidf_cosine','both_present','one_missing'],
    'tfidf': {'analyzer':'char_wb','ngram_range':[3,4],'min_df':2,'max_features':60000,'dtype':'float32','fit_scope':'training profiles only per OOF fit; all development only for refit'},
    'encoder': {'name':'sentence-transformers/all-MiniLM-L6-v2','revision':'1110a243fdf4706b3f48f1d95db1a4f5529b4d41','device':'cpu','max_seq_length':256,'normalize_embeddings':True,'semantic_fields':['fullname','bio'],'empty':'zero vector, no sentinel similarity','retrieval_serialization':'username + fullname + bio + location separated by literal field markers'},
    'retrieval_k': [1,5,10,20,50],
    'k_star_selection': 'minimum k on the fixed grid with pooled development lexical PC >= .95; otherwise 20; selection rule frozen, value chosen on development only',
    'retrieval_budget': 'k per query per other platform; directed proposals deduplicated to undirected pairs; hybrid union k/2 sparse + k/2 dense, and RRF c=60; primary exact total candidate count = fold-local B0 count; extend k pool deterministically through 100,200,400 until budget available, no label use',
    'B0': 'exact username length>=3 or nonempty externalUrl_clean, username/fullname alphanumeric prefix3, external_domain excluding historical generic domains',
    'primary_matcher_candidates': 'best lexical blocker of B0/sparse/hybrid by pooled dev PC at matched B0 budget; ties fewer candidates then method name; same C for every representation/model contrast',
    'classifier_search_configs': 200, 'classifier_search_optimizer':'TPE, seed 42; four development folds; maximize mean fold average precision',
    'rule_search': '200 simplex random weight configurations, four folds, maximize mean AP; threshold selected on dev only from 99 values',
    'GBDT': {'implementation':'sklearn.HistGradientBoostingClassifier','learning_rate':[.03,.1],'max_leaf_nodes':[15,31,63],'max_iter':[50,100,150],'min_samples_leaf':[20,50],'l2_regularization_log':[1e-6,10],'early_stopping':False,'train_negative_ratio':3},
    'LR': {'C_log':[.001,100],'class_weight':[None,'balanced'],'max_iter':500,'train_negative_ratio':3,'scaler_fit':'training only'},
    'gbdt_seeds':[11,23,42,71,101], 'lr_seeds':[42],
    'policy_seeds':[11,23,42,71,101,131,151,181,211,241],
    'policy_budget_per_seed':2048, 'policy_optimizers':['random','scrambled_sobol','TPE','GA'],
    'policy_genome':['t_match','t_review','c_promote','c_demote'],
    'policy_bounds': [[.90,.999],[.50,.999],[.50,1.0],[0.0,1.0]],
    'policy_constraints':'t_review<=t_match; c_demote<=c_promote; historical clip; independent ungated max(username_jw,fullname_jw) for name similarity',
    'GA': {'population':64,'elites':12,'crossover':'uniform','mutation_probability':.4,'mutation_sigma':.05,'evaluations':'64 initial + 1984 new genomes exactly; cache hits count as calls, report unique separately'},
    'cost': {'name':'crm_derived_v1_ASSUMPTION','FP':2.0,'FN':1.0,'REVIEW':.1,'review_outcome':'perfect review assumed only in utility; reviewed positives are not automatic matches'},
    'cost_sensitivity': [[1,1,.1],[2,1,.1],[5,1,.02],[10,1,.1]],
    'P_target':.90, 'threshold_grid':[i/100 for i in range(1,100)],
    'calibration':'identity, Platt, isotonic; leave-one-dev-fold-out calibrator evaluation, select minimum pooled Brier; refit chosen calibrator on natural-prior OOF only',
    'M_star_selection':'best of lexical and fusion GBDT by mean development AP, then lexical on tie; never choose using test',
    'primary_contrasts': {'H1':'lexical GBDT minus best dev-selected single lexical group AP','H2':'lexical GBDT minus tuned rule AP','H3':'fusion GBDT minus lexical GBDT AP','H4':'relative cost reduction GA vs dev-selected best non-GA policy','H5':'hybrid PC minus dev-selected best lexical PC at exact B0 budget'},
    'SESOI':{'H1':.02,'H2':.02,'H3':.01,'H4':.05,'H5':.02},
    'statistics':{'bootstrap_B':10000,'bootstrap_seed':4242,'primary_prediction':'mean of all five GBDT seeds','cluster':'identity pigeonhole/multiway bootstrap: negative edge weight = multiplicity(endpoint1)*multiplicity(endpoint2); positive within-identity edge weight = multiplicity(identity); same draw for both methods','CI':'95% percentile paired delta','p':'two-sided centered bootstrap +1 correction; Holm across five contrasts','equivalence':'TOST via 90% bootstrap CI inside +/- SESOI, explicitly approximate bootstrap TOST','alpha':.05},
    'final_cells':'B0 vs hybrid x tuned rule vs M_star x fixed .5 vs best validation policy; 8 complete unique configurations; additional H1 single-group/H2 lexical/H3 fusion/semantic and blocking configs predeclared in FINAL_CONFIGS before final access',
    'test_loader':'requires --final, committed FINAL_CONFIGS and exact frozen config/artifact hashes; once per configuration; appended access log',
    'annotation_capacity':False, 'label_sensitivity':['S1','S2'],
    'T9':'EXCLUDE', 'lead_scoring':'EXCLUDE','push':'DISABLED',
    'unresolved_defaults':'specific seed integers, computational wallclock budget, encoder choice as English/historical prior, HGB iteration cap and negative ratio are prospective ASSUMPTION defaults, not measured results',
}
(R/'protocol.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n')
with (D/'HYPOTHESIS_EXPERIMENT_MATRIX.csv').open() as f:
    rows=list(csv.DictReader(line for line in f if not line.startswith('#')))
for row in rows:
    if row['v2_id_status'].startswith(('ALIAS','RETIRED')): continue
    (R/'configs'/f"{row['exp_id']}.yaml").write_text(json.dumps({'exp_id':row['exp_id'],'priority':row['priority'],'name':row['name'],'protocol_sha256':sha(R/'protocol.json'),'planned_training_jobs':row['n_training_jobs'],'planned_validation_evals':row['n_validation_evals'],'planned_test_evals':row['n_test_evals'],'depends_on':row['depends_on']},ensure_ascii=False,indent=2)+'\n')
(R/'.gitignore').write_text('.venv/\n__pycache__/\n.pytest_cache/\n*.pyc\ndata_derived/\nartifacts/\ncache/\n*.log\nwork/**/tmp/\n')
(R/'GATE_RECORD.md').write_text('''# Gate Record — Round 4

G0: DECLARED PASSED by researcher; REFERENCE NOT PROVIDED.
G1: DECLARED PASSED by researcher; REFERENCE NOT PROVIDED.
ไม่มีการตรวจยืนยันเอกสาร provenance หรือ ethics/IRB/PDPA แทนผู้วิจัย การอนุญาตนี้มาจาก prompt v4 โดยตรง.
G4: freeze prospectively ตาม PREREGISTRATION_FREEZE.md; valid ต่อเมื่อ commit มาก่อน scientific run.
G5: NOT MET. ทุกผลต้องระบุ EXPLORATORY (LinkSocial, retrospectively exposed).
GO สำหรับ local exploratory execution ตามคำประกาศผู้วิจัย ไม่ใช่ confirmatory GO.
G2/G3: ต้องตรวจ label sanity และ zero cross-fold identities ก่อน training; ไม่มี human annotation capacity จึงใช้ E7-6 S1/S2 เท่านั้น.
PUSH_TO_PRIVATE_REPO: DISABLED.
Repository privacy: ผู้วิจัยประกาศ private แต่ live gh repo metadata รอบ preflight พบ visibility=PUBLIC ทั้งสอง repository; ไม่เปลี่ยน visibility และไม่ upload ข้อมูล/ผลใด ๆ.
Requested role labels astra6.1 / luna6.1 เป็นชื่อที่ผู้ใช้กำหนด ไม่ยืนยันว่าเป็น model aliases ที่ runtime รองรับ.
''')
(R/'DEVIATIONS.md').write_text('''# Deviations — prospective decisions ก่อน validation

- DEADLINE ว่าง: operational time budget = 120 นาที ASSUMPTION เริ่มที่ protocol.created_utc; เวลาเป็น execution cap ไม่ใช่ empirical runtime estimate. 70% งด Tier2 ใหม่, 85% งด runs ใหม่และรายงาน. งานที่ไม่ทันเป็น NOT RUN ไม่ลด scientific budgets.
- G0/G1 evidence references ว่าง: บันทึก DECLARED PASSED ไม่อ้าง documentary verification. G5 NOT MET เสมอ.
- คำประกาศ repositories private ขัด live metadata PUBLIC ทั้งคู่; ไม่ push (DISABLED) และไม่แก้ visibility.
- Cost conflict: hypotheses เสนอ crm_derived_v1 2:1:0.1 ขณะที่ evaluation §2.3 เรียก 5:1 default; ใช้ 2:1:0.1 เป็น primary ตาม hypothesis และ freeze อีกสาม scenarios ก่อนเห็นผล. Cost ทั้งหมด ASSUMPTION.
- Counts conflict: matrix E5-5 ใช้ 150 jobs แต่ TR3/TR4 ระบุ 5 GB seeds x (4 OOF+1 refit) x 5 groups =125 jobs; E5-3 matrix30 ขัด GB5 seeds/LR1 seed ซึ่งได้30รวม. จะรายงาน actual counters เทียบ historical planned MVP217 ไม่สร้าง dummy fits เพื่อให้ยอดตรง.
- Encoder English MiniLM เป็น prospective historical prior; report script distribution จาก D0 ไม่ใช้ผลเปรียบเทียบเลือก encoderย้อนหลัง; multilingual/fine-tuning อยู่ CONDITIONAL.
- คง raw user_folder เป็น operational label assumption ไม่อ้าง independently established identity; no human annotation capacity. Shared/blank group ต้อง quarantine ไม่รวมเป็น identityเดียว; historical label-noise impact เป็น UNKNOWN เว้นมี execution/artifact proof.
- H5 exact matched budget ใช้ fold-local B0 count; k-grid secondary; source key/URL label proxy ยังเป็น threat ไม่ถือ G0 researcher declaration แก้ proxy validity.
- AP bootstrap ใช้ multiway endpoint multiplicities สำหรับ negative dyads และ single identity multiplicity สำหรับ positive pairs; รายงานนิยามนี้เพราะคำว่า entity bootstrap ใน design ไม่ได้กำหนด cross-identity edge weighting.
- LR/F-SEM และ learning curves เป็น SUPPORTING แต่ v4 ยกไว้ Tier1; ทำตาม v4 priority เมื่อไม่ขัด dependency, ไม่มี RF (OPTIONAL) ใน Tier1.
- Test fold index4ตรง fold5ของเอกสาร; equal entity count ต่างกันได้หนึ่งคน (integer constraint); stratify platform multiplicities และ balance profile countsในties.
- User-requested worker alias ไม่สามารถ pin ผ่าน delegate tool schema ได้; ไม่กล่าวอ้างว่าได้ใช้ luna6.1.
''')
lines=['# Preregistration Freeze — G4', '',f'UTC timestamp: {now.isoformat()}',f'Pre-run source commit: {protocol["source_commit"]}',f'Protocol SHA-256: {sha(R/"protocol.json")}', '', 'EXPLORATORY (LinkSocial, retrospectively exposed). ไม่มีผล validation/test ของรอบนี้ถูกอ่านก่อนสร้าง freeze.', 'ค่าทุกตัวอยู่ใน protocol.json (cost, k* selection rule, P_target, SESOI, seeds, search spaces/budgets). Freeze นี้ไม่ได้ยืนยัน G5 หรือ power.', 'Pilot variance ไม่ทำก่อน freeze เพราะทุกผลเป็น exploratory ตั้งแต่ต้น; ไม่ปรับ SESOI ย้อนหลัง.', '', '## Design file hashes']
lines.extend(f'- {k}: {v}' for k,v in protocol['design_sha256'].items())
lines.extend(['','## Protected inputs','Hash ทั้ง _input_v1, raw input และ historical output inventory อยู่ใน protocol.json; ไม่รวม profile values หรือ identifiers.','','## Config hashes'])
lines.extend(f'- configs/{p.name}: {sha(p)}' for p in sorted((R/'configs').glob('*.yaml')))
(R/'PREREGISTRATION_FREEZE.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'freeze_created_utc':now.isoformat(),'protocol_sha256':sha(R/'protocol.json'),'configs':len(list((R/'configs').glob('*.yaml'))),'protected_files':len(protocol['protected_input_sha256']),'historical_artifacts':len(protocol['historical_artifacts'])}))
