from pathlib import Path
import urllib.request,urllib.parse,json,concurrent.futures,re
W=Path(__file__).resolve().parents[4];out=W/'research_v2/review/_work'
def get(u):
 try:
  q=urllib.request.Request(u,headers={'User-Agent':'ResearchEvidenceReview/3.0'});b=urllib.request.urlopen(q,timeout=45).read();return {'url':u,'body':b.decode('utf-8','replace')}
 except Exception as e:return {'url':u,'error':str(e)}
urls=['https://api.crossref.org/works/'+urllib.parse.quote(x,safe='') for x in ['10.1109/ICBK.2018.00042','10.1145/2487575.2487648','10.1145/3077257.3077268','10.14778/3137765.3137833','10.1007/s13369-022-06560-8']]
urls += ['https://api.crossref.org/works?rows=3&query.title='+urllib.parse.quote(x) for x in ['User identity linkage on social networks a review of modern techniques and applications','StyleLink User Identity Linkage Across Social Media with Stylometric Representations','MAUIL Multi-level Attribute Embedding for Semi-supervised User Identity Linkage']]
for repo in ['ChenBaiyang/MAUIL','KDD-HIEPT/DeepLink','vishalshar/Dataset-LinkSocial']:
 urls += ['https://api.github.com/repos/'+repo,'https://api.github.com/repos/'+repo+'/readme','https://api.github.com/repos/'+repo+'/license']
results=list(concurrent.futures.ThreadPoolExecutor(6).map(get,urls))
(out/'v3_web_metadata.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
for r in results:
 print('\nSOURCE',r['url'])
 if 'error' in r:print(r['error']);continue
 try:d=json.loads(r['body'])
 except Exception:continue
 if 'message' in d:
  m=d['message'];items=m.get('items',[m])
  for p in items:print(json.dumps({k:p.get(k) for k in ['title','author','container-title','published','DOI','volume','issue','page','abstract']},ensure_ascii=False))
 elif 'content' in d:
  import base64;t=base64.b64decode(d['content']).decode();
  # README/LICENSE only; no dataset file requested.
  print(t[:16000])
 else:print(json.dumps({k:d.get(k) for k in ['full_name','default_branch','license','html_url']},ensure_ascii=False))
