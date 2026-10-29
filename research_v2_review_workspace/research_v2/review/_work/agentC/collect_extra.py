from inspect import ROOT,show,excerpt
import json,re
jobs=[('main','1e0a2db','train_data/stage10_dataset.ipynb'),('main','1e0a2db','train_data/v2/stage10_dataset_v2.ipynb'),('main','1e0a2db','train_data/stage8_labeling.ipynb'),('main','1e0a2db','train_data/v2/stage8_labeling_v2.ipynb'),('main','1e0a2db','train_data/stage9_features.ipynb'),('main','1e0a2db','train_data/v2/stage9_features_v2.ipynb')]
pattern=r'train_test_split|entity|profile_id_a|profile_id_b|user_folder|fit_transform|tfidf|sample\(|random_state|\.iloc\[0\]|\.values\[0\]'
for repo,ref,path in jobs:
 raw=show(repo,ref,path); rawlines=raw.splitlines(); obj=json.loads(raw); out=[f'# {repo}@{ref}:{path} — code cells ONLY; outputs intentionally excluded']
 for ci,cell in enumerate(obj.get('cells',[])):
  if cell.get('cell_type')!='code':continue
  src=cell.get('source',[]);src=src if isinstance(src,list) else src.splitlines(True)
  hits=set()
  for i,line in enumerate(src):
   if re.search(pattern,line,re.I):hits.update(range(max(0,i-2),min(len(src),i+3)))
  if hits:
   out.append(f'CELL {ci}')
   for i in sorted(hits):
    encoded=json.dumps(src[i],ensure_ascii=False); matches=[j+1 for j,l in enumerate(rawlines) if encoded in l]
    out.append(f'cell_source_L{i+1}; raw_JSON_L{matches}: {src[i].rstrip()}')
 (ROOT/'agentC'/('notebook_'+path.replace('/','__')+'.txt')).write_text('\n'.join(out))
 print(path,'code excerpts',len(out))
for repo,ref,path,pat in [('backup','903246c','src/identity_resolution/stages/train_base.py',r'fit_transform|def assign_splits|split_profiles|calibrator.fit|make_profile_bundle|best_name|leaderboard|profile_id.*groupby|groupby.*profile_id'),('backup','903246c','src/identity_resolution/workflows/full_candidate.py',r'load_best_model|BEST_RUN_PATH|within_candidates|final_match_only|def load_profiles'),('backup','ab93b36','experiments/icsec_final/authoritative_run_v2/artifact_producers.py',r'def validate_input|sealed.*read|read_parquet|sealed_test|validate_input_artifacts'),('backup','ab93b36','experiments/code/run_reviewer_revision.py',r'def |bootstrap|conditional|Chow|risk|objective|replay|seed|FN|REVIEW')]:
 (ROOT/'agentC'/('source_'+repo+'_'+ref+'_'+path.replace('/','__')+'.txt')).write_text(excerpt(repo,ref,path,pat,3))
