from inspect import ROOT,show
import json,hashlib
out=[]
for seed in (101,202,303):
 for family in ('authoritative_run_v2','authoritative_run_v2r1'):
  for leaf in ('summary.json','fairness.json','label_access_audit.json','process_label_access_audit.json','prediction_immutability.json'):
   path=f'experiments/icsec_final/{family}/scientific_outputs/outer_{seed}/{leaf}'
   try: raw=show('backup','ab93b36',path);d=json.loads(raw)
   except Exception:continue
   if leaf=='summary.json':value=d
   elif leaf=='fairness.json':value={k:d[k] for k in ('passed','policy_class_equal','bounds_equal','budget','objective')}
   elif leaf=='label_access_audit.json':value={'event_count':len(d),'allowed_values':[x.get('allowed') for x in d],'phase_values':sorted(set(x.get('phase','') for x in d))}
   elif leaf=='process_label_access_audit.json':value={k:d[k] for k in ('pre_final_label_value_materializations','final_evaluation_label_value_materializations')}
   else:value={k:v for k,v in d.items() if k=='match'}
   out.append({'source':f'backup@ab93b36:{path}','line_count':len(raw.splitlines()),'json_key_selection':value,'git_blob_sha256':hashlib.sha256(raw.encode()).hexdigest(),'status':'RESULT_ARTIFACT_FOUND; values transcribed only, NOT INDEPENDENTLY_VERIFIED'})
(ROOT/'agentC'/'saved_summary_values.json').write_text(json.dumps(out,indent=2))
print('Saved',len(out),'allowlisted summary/audit artifacts; no row-level data read')
print(json.dumps([x for x in out if 'process_label' in x['source'] or 'fairness' in x['source']],indent=2))
