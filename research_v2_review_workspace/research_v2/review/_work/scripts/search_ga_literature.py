import urllib.request,urllib.parse,json,concurrent.futures
from pathlib import Path
queries=['"record linkage" "genetic"','"entity resolution" "evolutionary"','"record linkage" "genetic programming"','"entity matching" "genetic algorithm"']
def search(q):
 try:
  u='https://api.crossref.org/works?rows=12&query.bibliographic='+urllib.parse.quote(q)
  d=json.load(urllib.request.urlopen(u,timeout=60))['message']['items']
  return {'query':q,'items':[{k:x.get(k) for k in ['title','DOI','author','published','container-title','URL','abstract']} for x in d]}
 except Exception as e:return {'query':q,'error':str(e)}
r=list(concurrent.futures.ThreadPoolExecutor(4).map(search,queries))
Path(__file__).resolve().parents[1].joinpath('ga_literature_search.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
for query in r:
 print(query['query'])
 for p in query.get('items',[]):print(p['DOI'],p['title'])
