from pathlib import Path
import subprocess,csv,io,json,hashlib,collections,itertools
W=Path(__file__).resolve().parents[4]; work=W/'research_v2/review/_work'
repo=work/'repos/main'
results=[]
# Authorized v3 aggregate queries; no row/key/profile values printed or retained.
for path in ['data_for_project/merged_profiles.csv','data_for_project/normalized_profiles_with_profile_id.csv','data_for_project/nomalized_profiles.csv','data/processed/all_profiles_cleaned.csv']:
 b=subprocess.check_output(['git','show','1e0a2db:'+path],cwd=repo)
 if b.startswith(b'version https://git-lfs'):continue
 reader=csv.DictReader(io.StringIO(b.decode('utf-8-sig')))
 platform=collections.Counter();groups=collections.defaultdict(collections.Counter);nulls=0;rows=0;eligible=0;egroups=collections.defaultdict(collections.Counter)
 for row in reader:
  rows+=1;p=row.get('platform','');platform[p]+=1;g=row.get('user_folder','')
  if not g.strip() or g.strip().lower() in ['nan','null','none']:nulls+=1
  groups[g][p]+=1
  if row.get('profile_id','').strip():eligible+=1;egroups[g][p]+=1
 def summarize(gs):
  hist=collections.Counter(sum(v.values()) for v in gs.values())
  cross=sum(sum(a*c for a,c in itertools.combinations(v.values(),2)) for v in gs.values())
  return {'distinct_groups':len(gs),'group_size_histogram':dict(sorted(hist.items())),'cross_platform_positive_pairs':cross,'max_group_size':max(hist,default=0),'missing_key_group_rows':sum(sum(v.values()) for k,v in gs.items() if not k.strip() or k.strip().lower() in ['nan','null','none']),'cross_platform_pairs_nonmissing_keys':sum(sum(a*c for a,c in itertools.combinations(v.values(),2)) for k,v in gs.items() if k.strip() and k.strip().lower() not in ['nan','null','none'])}
 results.append({'repo':'MAIN','commit':'1e0a2db','path':path,'sha256':hashlib.sha256(b).hexdigest(),'row_count':rows,'platform_counts':dict(platform),'missing_or_null_user_folder_rows':nulls,'all_rows':summarize(groups),'eligible_nonempty_profile_id_rows':eligible,'eligible_profile_id':summarize(egroups) if egroups else None})
(work/'v3_profile_aggregates.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
with (work/'aggregate_queries.log').open('a') as log:
 log.write('\nV3 authorized non-identifying aggregate query; no model metrics or optimization.\nSCRIPT SHA256 '+hashlib.sha256(Path(__file__).read_bytes()).hexdigest()+'\nEXACT EXECUTED CODE:\n'+Path(__file__).read_text()+'\nOUTPUT:\n'+json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps(results,ensure_ascii=False,indent=2))
