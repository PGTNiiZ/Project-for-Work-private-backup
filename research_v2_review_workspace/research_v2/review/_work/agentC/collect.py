from inspect import ROOT,show,excerpt
import json,re
jobs=[
('main','1e0a2db','exp_lib.py',r'NSIM_MIN_SCORE|def evaluate|def build_nested|def nested_split|sa =|sb =|same_dev_role|used_entities|total_pos'),
('main','1e0a2db','exp_r1_ga_redecision.py',r'def |cost|population|generations|seed|fitness|budget'),
('main','1e0a2db','exp_r2_bert_feature.py',r'"name_sim":|SentenceTransformer\(|def train_r2_probabilities|calibrator.fit|idx_train|if .*PATH.exists|model_calibration|early_stopping'),
('main','1e0a2db','exp_r4_bloom_privacy.py',r'def |split|sample|calibrat|train_test_split|seed|full|hash'),
('main','1e0a2db','exp_r6_bert_er.py',r'def |split|calibrat|train_test_split|sample|seed|test|fitness'),
('main','1e0a2db','run_gb_transformer_experiments.py',r'def |split_constants|actual|fit\(|calibrat|seed|test|budget|name_sim'),
('backup','903246c','src/identity_resolution/stages/features.py',r'__idx|_source_idx|tfidf|def build_entity_split|pair_subset|profile_id.*row|return .*profile_id'),
('backup','903246c','src/identity_resolution/stages/pairs.py',r'def |label|user_folder|sample|random_state|negative|positive'),
('backup','903246c','src/identity_resolution/stages/train_neural.py',r'def set_seed|test_y=|calibrator.fit|choose_threshold\(|scaler.fit|test_df =|best_val_ap|neg_sampled'),
('backup','903246c','experiments/code/run_icsec_repeated_outer.py',r'def |entity|actual|test|calibrat|constant|seed'),
('backup','903246c','experiments/code/analyze_icsec_primary.py',r'def |bootstrap|seed|constant|blocking|REVIEW|fn|total_pos'),
('backup','ab93b36','experiments/icsec_final/authoritative_run_v2/features.py',r'def |name_sim|jaro|WRatio|score|label'),
('backup','ab93b36','experiments/icsec_final/authoritative_run_v2/policies.py',r'def |budget|evaluations|cost|REVIEW|seed|sobol|population'),
('backup','ab93b36','experiments/icsec_final/authoritative_run_v2/final_runner.py',r'def |label|read|fit\(|calibrat|test|freeze|budget|evaluate'),
('backup','ab93b36','experiments/icsec_final/authoritative_run_v2/real_adapters.py',r'def |role_a|role_b|entity|label|drop'),
('backup','ab93b36','experiments/icsec_final/authoritative_run_v2r1/final_runner_r1.py',r'def |label|read|freeze|fit\(|calibrat|test|budget'),
('backup','ab93b36','experiments/icsec_final/authoritative_run_v2r1/sealed_guard.py',r'def |label|read|denied|access|phase'),
('backup','903246c','docs/GETTING_STARTED_TH.md',r'canonical|src/|architecture'),
('backup','903246c','docs/ARCHITECTURE_TH.md',r'canonical|src/|train|feature|calib'),
]
outputs=[]
for repo,ref,path,pat in jobs:
 try:
  text=excerpt(repo,ref,path,pat,2); out=ROOT/'agentC'/('source_'+repo+'_'+ref+'_'+path.replace('/','__')+'.txt');out.write_text(text);outputs.append({'repo':repo,'ref':ref,'path':path,'extract':out.name,'source_lines':len(show(repo,ref,path).splitlines())})
 except Exception as e: outputs.append({'repo':repo,'ref':ref,'path':path,'error':str(e)})
(ROOT/'agentC'/'source_index.json').write_text(json.dumps(outputs,indent=2))
print(json.dumps(outputs,indent=2))
