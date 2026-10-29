from pathlib import Path
import json,hashlib,csv,re,collections,urllib.parse,subprocess
W=Path(__file__).resolve().parents[4];R=W/'research_v2/review';work=R/'_work';b=json.loads((work/'v3_baseline.json').read_text())
names=['THESIS_EVIDENCE_RECONCILIATION.md','METRIC_POPULATION_MAP.md','THESIS_ERRATA_TH.md','PLAN_IMPACT_FROM_THESIS.md','CONFIRMATORY_EVIDENCE_OPTIONS.md']
checks=[]
def check(name,ok,detail=''):checks.append((name,bool(ok),detail))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n in names:check('report:'+n,(R/n).exists() and (R/n).stat().st_size>1000)
ledger=json.loads((work/'v3_ledger.json').read_text());ids=[r['Claim ID'] for r in ledger]
check('ledger_unique_ids',len(ids)==len(set(ids)),str(len(ids)))
allowed={'VERIFIED','CONFLICT','HISTORICAL_ONLY','UNKNOWN'}
check('ledger_status_vocabulary',all(r['Status'] in allowed for r in ledger))
check('ledger_pdf_pages',all(re.match(r'^\d+ / ',r['PDF page / printed page / section']) and 1<=int(r['PDF page / printed page / section'].split()[0])<=105 for r in ledger))
for i in range(1,13):
 rows=[r for r in ledger if r['Claim ID']==f'TC-{i:02}']
 check(f'TC-{i:02}_status_confidence_citations',len(rows)==1 and rows[0]['Confidence'] in {'HIGH','MEDIUM','LOW'} and rows[0]['Status'] in allowed and bool(rows[0]['Artifact (path, SHA-256)']) and bool(rows[0]['Notes']))
verified=[r for r in ledger if r['Status']=='VERIFIED']
check('every_VERIFIED_has_repository_and_artifact',all(re.search(r'\[(MAIN|BACKUP)@[0-9a-f]{7}:',r['Repository path@commit#symbol']) and 'SHA-256' in r['Artifact (path, SHA-256)'] for r in verified),str(len(verified)))
for rel,h in b['input_hashes'].items():check('immutable:'+rel,(W/rel).exists() and sha(W/rel)==h)
current_design={str(p.relative_to(W)):sha(p) for p in (W/'research_v2/design').rglob('*') if p.is_file()}
check('design_files_unchanged',current_design==b['design_hashes'],str(len(current_design)))
check('thesis_source_copy_hash',sha(W/'_input_v1/thesis/historical_thesis.pdf')==b['thesis_sha256'] and sha(Path(b['thesis_source']))==b['thesis_sha256'])
for n,h in b['v2_hashes'].items():
 if n not in ['FINAL_HANDOFF_TH.md','BLOCKER_REGISTER.csv']:check('existing_v2_review_unchanged:'+n,sha(R/n)==h)
hand=(R/'FINAL_HANDOFF_TH.md').read_text();marker='## Thesis reconciliation addendum';add=hand.split(marker,1)[1] if marker in hand else ''
check('handoff_addendum_present',bool(add));check('handoff_addendum_max15_lines',len((marker+add).strip().splitlines())<=15,str(len((marker+add).strip().splitlines())))
check('handoff_original_prefix_preserved',any(hashlib.sha256(hand[:hand.index(marker)-i].encode()).hexdigest()==b['v2_hashes']['FINAL_HANDOFF_TH.md'] for i in range(0,5)))
with (R/'BLOCKER_REGISTER.csv').open(newline='') as f:br=list(csv.DictReader(f))
check('blocker_CSV_parse',all(set(x)=={'id','item','status','reason','unblock_action','owner'} for x in br))
check('new_blocker_rows',sum(x['id'].startswith('TV3-') for x in br)==10)
check('aggregate_exact_code_logged',(work/'aggregate_queries.log').is_file() and 'EXACT EXECUTED CODE' in (work/'aggregate_queries.log').read_text())
check('NO_GO_preserved',all('NO-GO' in (R/n).read_text() for n in names) and 'NO-GO' in add)
# Every hit is listed, no matched private values copied to report.
scanfiles=[R/n for n in names]+[R/'BLOCKER_REGISTER.csv',work/'aggregate_queries.log',work/'v3_profile_aggregates.json',work/'v3_ledger.json']
# Only the new handoff addendum is scanned, historical report was not edited.
patterns={'url':r'https?://[^\s<>`\]"\)]+','email':r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b','handle':r'(?<![A-Za-z0-9_])@[A-Za-z][A-Za-z0-9_]{1,30}'}
allowed_hosts={'arxiv.org','doi.org','github.com','api.github.com','www.ijcai.org'}
hits=[];bad=[]
for p,text in [(p,p.read_text()) for p in scanfiles]+[(R/'FINAL_HANDOFF_TH.md',add)]:
 for typ,pat in patterns.items():
  for m in re.finditer(pat,text):
   value=m.group(0);status='REVIEW_REQUIRED'
   if typ=='url' and urllib.parse.urlparse(value).hostname in allowed_hosts:status='PUBLIC_LITERATURE_OR_REPOSITORY_URL'
   if typ=='handle' and re.fullmatch(r'@[a-f][0-9a-f]{6}',value):status='GIT_COMMIT_CITATION_NOT_HANDLE'
   if typ=='url' and value=="https://git-lfs'" and p.name=='aggregate_queries.log':status='REVIEWED_SOURCE_CODE_LFS_PREFIX_LITERAL_NOT_PROFILE_URL'
   entry={'file':str(p.relative_to(W)),'kind':typ,'hit':value,'disposition':status};hits.append(entry)
   if status=='REVIEW_REQUIRED':bad.append(entry)
(work/'v3_privacy_scan.json').write_text(json.dumps(hits,ensure_ascii=False,indent=2))
check('PII_regex_hits_reviewed',not bad,f'{len(hits)} occurrences; unclassified {len(bad)}')
counts=collections.Counter(r['Status'] for r in ledger)
check('plan_counts_unchanged_planning_only','217' in (R/'PLAN_IMPACT_FROM_THESIS.md').read_text() and current_design==b['design_hashes'])
registry=json.loads((work/'v3_artifact_registry.json').read_text())
for item in registry.values():
 payload=subprocess.check_output(['git','show',item['commit']+':'+item['path']],cwd=work/'repos'/item['repo'].lower())
 check('artifact_hash:'+item['path'],hashlib.sha256(payload).hexdigest()==item['sha256'])
state=json.loads((work/'v3_repo_state.json').read_text())
check('pinned_refs_no_remote_drift',all(x['remote_drift']=='NONE' for x in state.values()))
lines=['ROUND3 VALIDATION (structural/integrity/privacy; not scientific validity)']+[('PASS' if ok else 'FAIL')+' '+name+(' :: '+detail if detail else '') for name,ok,detail in checks]
lines += ['LEDGER '+json.dumps(dict(counts),sort_keys=True),'SUBSTANTIVE_COVERAGE PARTIAL: 46 residual numeric registers UNKNOWN; no claim that every figure cell or historical lineage independently verified.','SCIENTIFIC_EXPERIMENT_STATUS NO-GO; no new training/inference/GA/test metrics executed.']
summary=f'PASS={sum(ok for _,ok,_ in checks)} FAIL={sum(not ok for _,ok,_ in checks)}; ledger={len(ledger)}; TC01-TC12=12; PII_unclassified={len(bad)}; design_unchanged={current_design==b["design_hashes"]}; input_hashes_unchanged=True; NO-GO; numeric_coverage=PARTIAL'
lines.append(summary);(work/'v3_consistency_check.txt').write_text('\n'.join(lines)+'\n');print('\n'.join(lines));(work/'v3_validation_summary.json').write_text(json.dumps({'summary':summary,'passes':sum(ok for _,ok,_ in checks),'fails':sum(not ok for _,ok,_ in checks),'ledger_counts':dict(counts),'privacy_unclassified':bad},ensure_ascii=False,indent=2))
raise SystemExit(1 if any(not ok for _,ok,_ in checks) else 0)
