exec((__import__('pathlib').Path(__file__).parent/'fetch_metadata.py').read_text().split('with concurrent.futures.ThreadPoolExecutor')[0])
# Retry failed metadata using query discovery, never repair identifiers silently.
for row in rows:
 p=OUT/'raw'/f"{row['paper_id']}_crossref.json";d=json.loads(p.read_text())
 if 'error' in d:
  d=get('https://api.crossref.org/works?query.bibliographic='+urllib.parse.quote(row['title'])+'&rows=3')
  (OUT/'raw'/f"{row['paper_id']}_retry.json").write_text(json.dumps(d,ensure_ascii=False,indent=2))
  print(row['paper_id'],str(d)[:450],flush=True)
urls={
'P01_abs':'https://arxiv.org/abs/2409.08966',
'P04_pdf':'https://www.vldb.org/pvldb/vol14/p50-li.pdf',
'P05_pdf':'https://pages.cs.wisc.edu/~anhai/papers1/deepmatcher-sigmod18.pdf',
'P06_html':'https://openproceedings.org/2020/conf/edbt/paper_58.pdf',
'P07_html':'https://www.ijcai.org/proceedings/2022/552',
'P08_html':'https://arxiv.org/html/2508.08076v1',
'P08_abs':'https://arxiv.org/abs/2508.08076',
'P09_pdf':'https://openproceedings.org/2025/conf/edbt/paper-42.pdf',
'P15_html':'https://aclanthology.org/D19-1410/',
'P24_pdf':'https://cseweb.ucsd.edu/~elkan/rescale.pdf',
'P26_pdf':'https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf',
'P28_html':'https://www.sciencedirect.com/science/article/abs/pii/S0957417425026430',
'P34_doi':'https://doi.org/10.32604/cmc.2025.073175',
'P35_pdf':'https://www.scitepress.org/Papers/2015/51760/51760.pdf',
}
def fetch(item):
 key,url=item
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=65) as r:
   data=r.read(); dest=OUT/'raw'/(key+('.pdf' if data.startswith(b'%PDF') else '.html'));dest.write_bytes(data)
   z={'url':url,'final_url':r.url,'status':r.status,'bytes':len(data),'path':str(dest)}
 except Exception as e:z={'url':url,'error':str(e)}
 (OUT/'raw'/(key+'_fetch.json')).write_text(json.dumps(z,ensure_ascii=False,indent=2));return key,z
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
 for x in ex.map(fetch,urls.items()):print(x,flush=True)
