"""Aggregate-only read-only candidate, identity mapping, GT CSV and embedding audit.
Never runs training/encoding or writes upstream. No sealed-role label file is opened.
"""
from pathlib import Path
import sys,json,hashlib,itertools,re,csv
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
assert sys.version_info[:2]==(3,11)
sys.path.insert(0,str(ROOT/'src'))
from identity_resolution.workflows import full_candidate as fc

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p,default=False):return pd.read_csv(ROOT/p,keep_default_na=default,low_memory=False)
def key(a,b):
 a,b=sorted((int(a),int(b)));return (a<<32)|b
out={};checks=[]
def check(n,N,m,s,detail=''):
 checks.append(dict(transformation=n,checked_rows=N,mismatch_rows=m,status='PASS' if m==0 else 'FAIL',source=s,detail=detail))
raw=read('data_for_project/combined_profiles.csv');raw.columns=[c.strip().strip('"') for c in raw]
merged=read('data_for_project/merged_profiles.csv');norm=read('data_for_project/normalized_profiles.csv');typo=read('data_for_project/nomalized_profiles.csv');pid=read('data_for_project/normalized_profiles_with_profile_id.csv');block=read('data/processed/all_profiles_with_blocking_keys.csv')
for a,b,an,bn in [(merged,block,'merged','blocking'),(norm,merged,'normalized','merged'),(typo,norm,'nomalized','normalized')]:
 for c in sorted(set(a)&set(b)):check(an+'→'+bn+' ordered '+c,len(a),int(a[c].astype(str).ne(b[c].astype(str)).sum()),'dataset_candidate_audit.py:30-31','Observed ordered equality, NOT proof of historical producer')
# Reproduce builder default pandas NA equality alongside literal-preserving audit.
rd=read('data_for_project/combined_profiles.csv',True);rd.columns=[c.strip().strip('"') for c in rd];bd=read('data/processed/all_profiles_with_blocking_keys.csv',True)
for c in ['source_folder','user_folder','platform','outputProfileName','pictureURL']:check('builder default-NA raw→blocked '+c,len(raw),int(rd[c].fillna('').astype(str).ne(bd[c].fillna('').astype(str)).sum()),'thesis_rebuild/build_dataset_excel.py:18-29','Default NA erases literal NA/nan tokens; literal-preserving audit separately flags differences')
check('normalized→profile snapshot row id sequential',len(pid),int(pid.profile_row_id.astype(int).ne(np.arange(len(pid))).sum()),'data_for_project/normalized_profiles_with_profile_id.csv:header; dataset_candidate_audit.py')
mapgroups=pid[pid.user_folder.ne('')].groupby('user_folder').profile_id.nunique();back=pid.groupby('profile_id').user_folder.nunique()
out['numeric_entity_mapping']={'profile_rows':len(pid),'unique_profile_row_id':pid.profile_row_id.nunique(),'known_entity_groups':int(len(mapgroups)),'entity_groups_with_multiple_numeric_profile_id':int(mapgroups.gt(1).sum()),'numeric_ids_with_multiple_folder_values':int(back.gt(1).sum()),'missing_user_folder':int(pid.user_folder.eq('').sum()),'missing_numeric_profile_id':int(pid.profile_id.astype(str).eq('').sum()),'missing_row_id':int(pid.profile_row_id.astype(str).eq('').sum())}
# Missing folder rows are not positives. Eligibility fc.load_profiles drops missing numeric IDs.
profiles=fc.load_profiles();out['eligibility']={'all_snapshot_rows':len(pid),'fc_eligible_rows':len(profiles),'dropped_missing_numeric_ids':len(pid)-len(profiles),'platform_counts':profiles.platform.value_counts().to_dict(),'missing_entity_remaining':int(profiles.user_folder.eq('').sum()),'source':'src/identity_resolution/workflows/full_candidate.py:50-68'}
exact,ed=fc.build_exact_match_pairs(profiles);scored,sd=fc.build_candidate_pairs(profiles,exact);workflow=exact|scored
truth=set();allpositive=0;same=0
for _,g in profiles[profiles.user_folder.ne('')].groupby('user_folder',sort=False):
 rows=list(g[['profile_row_id','platform']].itertuples(index=False,name=None));allpositive+=len(rows)*(len(rows)-1)//2
 for (a,pa),(b,pb) in itertools.combinations(rows,2):
  if pa==pb:same+=1
  else:truth.add(key(a,b))
covered=len(truth&workflow);possible=fc.count_cross_platform_all_pairs(profiles)
out['canonical_candidate_accounting']={'exact':len(exact),'scored':len(scored),'workflow':len(workflow),'exact_true_positive':len(exact&truth),'exact_false_positive':len(exact-truth),'cross_platform_positives':len(truth),'all_platform_positives':allpositive,'same_platform_positives':same,'covered_positive':covered,'missed_positive':len(truth-workflow),'possible_cross_platform_pairs':possible,'retrieval_recall':covered/len(truth),'reduction':1-len(workflow)/possible,'exact_breakdown_incremental':ed,'blocking_breakdown_incremental':sd,'invariants':{'exact_scored_disjoint':not bool(exact&scored),'exact_plus_scored_equals_workflow':len(exact)+len(scored)==len(workflow),'covered_plus_missed_equals_positive':covered+len(truth-workflow)==len(truth),'all_equals_cross_plus_same':allpositive==len(truth)+same}}
par=[]
for name,expected in [('exact_tier',exact),('model_scored',scored),('workflow',workflow)]:
 p=ROOT/f'experiments/icsec_final/authoritative_run_v2/candidates/{name}.parquet';d=pd.read_parquet(p);ks=[key(a,b) for a,b in zip(d.profile_row_id_a,d.profile_row_id_b)];persist=set(ks)
 par.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'rows':len(d),'columns':list(d),'duplicate_unordered_excess':len(ks)-len(persist),'recomputed_missing_keys':len(expected-persist),'recomputed_extra_keys':len(persist-expected),'cross_platform_positive_count':len(persist&truth)})
out['candidate_artifacts']=par
# Legacy candidates: lookup ambiguity explicitly isolated.
legacy=read('data/processed/candidate_pairs.csv');counts=block.profile_id.value_counts();u=block[block.profile_id.map(counts).eq(1)].set_index('profile_id');a=legacy.profile_id_a.map(u.user_folder);b=legacy.profile_id_b.map(u.user_folder);valid=a.notna()&b.notna()&a.ne('')&b.ne('');knownpos=valid&a.eq(b)
legacykeys=set(tuple(sorted((str(x),str(y)))) for x,y in zip(legacy.profile_id_a,legacy.profile_id_b));labeled=read('data/processed/labeled_pairs.csv');positivekeys=set(tuple(sorted((str(x),str(y)))) for x,y in zip(labeled.loc[labeled.label.eq(1),'profile_id_a'],labeled.loc[labeled.label.eq(1),'profile_id_b']))
out['legacy_candidates']={'rows':len(legacy),'unambiguous_known_entity_pairs':int(valid.sum()),'unresolved_pairs':int((~valid).sum()),'positives_unambiguous':int(knownpos.sum()),'labeled_positive_unique_pair_keys':len(positivekeys),'labeled_positive_keys_in_candidates':len(positivekeys&legacykeys),'labeled_positive_keys_not_in_candidates':len(positivekeys-legacykeys),'positive_key_coverage':len(positivekeys&legacykeys)/len(positivekeys),'caution':'String profile keys collapse duplicates. This is artifact intersection, not row-level canonical retrieval recall.'}
# Historical symmetric GT pair CSV uses indices, avoid personal username fields.
gtpath=ROOT/'train_data/ground_truth_pairs.csv';gt=pd.read_csv(gtpath,usecols=['idx_i','idx_j','match']);idx=read('train_data/ground_truth_matrix_index.csv');ii=gt.idx_i.astype(int).to_numpy();jj=gt.idx_j.astype(int).to_numpy();folders=idx.user_folder.astype(str).to_numpy();validrange=(ii>=0)&(jj>=0)&(ii<len(idx))&(jj<len(idx));gkeys={(int(a),int(b)) for a,b in zip(ii,jj)};platforms=merged.platform.astype(str).to_numpy()
out['historical_gt_csv']={'path':str(gtpath.relative_to(ROOT)),'sha256':sha(gtpath),'matrix_npz_present':(ROOT/'train_data/ground_truth_matrix.npz').exists(),'rows':len(gt),'directed_unique_pairs':len(gkeys),'self_pairs':int(np.count_nonzero(ii==jj)),'out_of_range':int(np.count_nonzero(~validrange)),'nonunit_match':int(gt.match.ne(1).sum()),'asymmetric_directed_pairs':sum((b,a) not in gkeys for a,b in gkeys),'different_index_entity_pairs':int(np.count_nonzero(folders[ii]!=folders[jj])),'cross_platform_upper_pairs':int(np.count_nonzero((ii<jj)&(platforms[ii]!=platforms[jj]))),'same_platform_upper_pairs':int(np.count_nonzero((ii<jj)&(platforms[ii]==platforms[jj]))),'index_vs_current_merged_folder_mismatch':int(idx.user_folder.astype(str).ne(merged.user_folder.astype(str)).sum()),'index_vs_current_merged_username_mismatch':int(idx.userName.astype(str).ne(merged.userName.astype(str)).sum())}
# Existing embeddings only. No encoder load, download or embedding generation.
embpath=ROOT/'experiments/profile_embeddings_minilm.npy';idpath=ROOT/'experiments/profile_embeddings_minilm_ids.npy';emb=np.load(embpath,mmap_mode='r');ids=np.load(idpath,allow_pickle=False);idmap={int(k):i for i,k in enumerate(ids)}
out['existing_minilm_embeddings']={'embedding_path':str(embpath.relative_to(ROOT)),'embedding_sha256':sha(embpath),'id_path':str(idpath.relative_to(ROOT)),'id_sha256':sha(idpath),'shape':list(emb.shape),'id_count':len(ids),'duplicate_ids':len(ids)-len(set(map(int,ids))),'norm_min':float(np.linalg.norm(emb,axis=1).min()),'norm_max':float(np.linalg.norm(emb,axis=1).max()),'ids_not_in_current_eligible':len(set(map(int,ids))-set(map(int,profiles.profile_row_id))),'eligible_ids_without_embedding':len(set(map(int,profiles.profile_row_id))-set(map(int,ids)))}
cosresults=[]
for rel in ['experiments/pair_bert_cos.parquet','experiments/icsec_final/authoritative_run_v2/features/bert_cos.parquet']:
 p=ROOT/rel
 if not p.exists():continue
 d=pd.read_parquet(p);cols=('profile_row_id_a','profile_row_id_b') if 'profile_row_id_a' in d else ('profile_id_a','profile_id_b');m=0;missing=0;maxdiff=0.;outside=0
 for start in range(0,len(d),100000):
  part=d.iloc[start:start+100000];a=part[cols[0]].map(idmap);b=part[cols[1]].map(idmap);ok=a.notna()&b.notna();missing+=int((~ok).sum());computed=np.sum(emb[a[ok].astype(int)]*emb[b[ok].astype(int)],axis=1);actual=part.loc[ok,'bert_cos'].to_numpy();diff=np.abs(computed-actual);maxdiff=max(maxdiff,float(diff.max(initial=0)));m+=int((~np.isclose(computed,actual,rtol=1e-5,atol=1e-6)).sum());outside+=int(((actual < -1.00001)|(actual>1.00001)).sum())
 cosresults.append({'path':rel,'sha256':sha(p),'rows':len(d),'missing_embedding_endpoints':missing,'mismatch_rows_vs_existing_legacy_embedding':m,'max_abs_difference':maxdiff,'cosine_out_of_range':outside,'note':'V2 independently regenerated embeddings may differ; mismatch is not proof V2 incorrect. Existing encoder revision not inferred from filename.'})
out['feature18_replay']=cosresults
# privacy-preserving counts only; do not print unresolved keys or raw values.
output=OUT/'dataset_candidate_accounting.json';assert not output.exists();output.write_text(json.dumps(out,ensure_ascii=False,indent=2,default=lambda v:int(v) if isinstance(v,np.integer) else str(v))+'\n')
with (OUT/'transformation_verification.csv').open('a',newline='') as f:csv.DictWriter(f,fieldnames=list(checks[0])).writerows(checks)
print(json.dumps(out,ensure_ascii=False,indent=2,default=lambda v:int(v) if isinstance(v,np.integer) else str(v)))
