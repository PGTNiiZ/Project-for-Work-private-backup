from pathlib import Path
import concurrent.futures,subprocess,json,sys
OUT=Path(__file__).parent;sys.path.insert(0,str(OUT/'_deps'))
from bs4 import BeautifulSoup
urls={
'P10_scidir':'https://www.sciencedirect.com/science/article/pii/S0306437923001357',
'P28_scidir':'https://www.sciencedirect.com/science/article/pii/S0957417425026430',
'P35_pdf_retry':'https://www.scitepress.org/Papers/2015/51760/51760.pdf',
'P24_ijcai':'https://www.ijcai.org/Proceedings/01-1/contents.html',
'P27_author':'https://cseweb.ucsd.edu/~elkan/posonly.pdf',
'P03_author':'https://www.public.asu.edu/~huanliu/papers/kdd13.pdf',
'P16_taylor':'https://www.tandfonline.com/doi/abs/10.1080/01621459.1969.10501049',
'P31_acm':'https://dl.acm.org/doi/abs/10.1145/3340531.3411931',
'P32_elsevier':'https://api.elsevier.com/content/article/doi/10.1016/j.is.2012.11.005?httpAccept=text/xml',
'P10_elsevier':'https://api.elsevier.com/content/article/doi/10.1016/j.is.2023.102307?httpAccept=text/xml',
}
def fetch(item):
 key,url=item;p=OUT/'raw'/f'{key}.body'
 r=subprocess.run(['curl','-sSL','--max-time','45','-o',str(p),'-w','%{http_code} %{url_effective}',url],capture_output=True,text=True)
 data=p.read_bytes() if p.exists() else b''
 if data.startswith(b'%PDF'):
  from pypdf import PdfReader
  import io,logging;logging.disable(logging.CRITICAL)
  text='\n'.join(x.extract_text() for x in PdfReader(io.BytesIO(data)).pages)
 else:
  s=BeautifulSoup(data,'html.parser')
  for z in s(['script','style','nav']):z.decompose()
  text=s.get_text('\n',strip=True)
 (OUT/'raw'/f'{key}.txt').write_text(text)
 result={'url':url,'curl_status':r.stdout,'error':r.stderr,'bytes':len(data)}
 (OUT/'raw'/f'{key}_fetch.json').write_text(json.dumps(result,indent=2));return key,result
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
 for x in ex.map(fetch,urls.items()):print(x,flush=True)
s=BeautifulSoup((OUT/'raw/P35_publisher.html').read_bytes(),'html.parser')
for x in s(['script','style','nav']):x.decompose()
(OUT/'raw/P35_publisher.txt').write_text(s.get_text('\n',strip=True))
