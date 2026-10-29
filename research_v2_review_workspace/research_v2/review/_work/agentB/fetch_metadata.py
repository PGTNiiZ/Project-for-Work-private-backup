from pathlib import Path
import csv,json,urllib.request,urllib.parse,concurrent.futures,time,hashlib
BASE=Path('/Users/thawaree.kha/Project-for-Work/research_v2_review_workspace')
OUT=BASE/'research_v2/review/_work/agentB'; (OUT/'raw').mkdir(parents=True,exist_ok=True)
rows=list(csv.DictReader((BASE/'_input_v1/PAPER_EVIDENCE_MATRIX.csv').open()))
def get(url):
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'LiteratureMetadataAudit/1.0','Accept':'application/json'})
  with urllib.request.urlopen(req,timeout=55) as r: return {'url':url,'status':r.status,'data':json.load(r)}
 except Exception as e:return {'url':url,'error':str(e)}
def run(row):
 pid=row['paper_id'];doi=row['doi']
 if pid=='P01':doi='10.1109/ACCESS.2024.3500374'
 if pid=='P34':doi='10.32604/cmc.2025.073175'
 url='https://api.crossref.org/works/'+urllib.parse.quote(doi,safe='/') if doi.startswith('10.') else 'https://api.crossref.org/works?query.title='+urllib.parse.quote(row['title'])+'&rows=3'
 result=get(url);(OUT/'raw'/f'{pid}_crossref.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 d=result.get('data',{}).get('message',{});items=d.get('items',[d])
 return pid,[(x.get('DOI'),x.get('title'),x.get('volume'),x.get('published'),x.get('page'),bool(x.get('abstract'))) for x in items]
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as ex:
 for result in ex.map(run,rows):print(result,flush=True)
manifest=[{'file':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted((BASE/'_input_v1').iterdir()) if f.is_file()]
(OUT/'input_manifest.json').write_text(json.dumps(manifest,indent=2))
