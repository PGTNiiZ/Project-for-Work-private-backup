from pathlib import Path
import sys,json
OUT=Path(__file__).parent;sys.path.insert(0,str(OUT/'_deps'))
from pypdf import PdfReader
from bs4 import BeautifulSoup
for f in (OUT/'raw').iterdir():
 if f.suffix=='.pdf':
  text='\n'.join(f'\nPAGE {i+1}\n'+p.extract_text() for i,p in enumerate(PdfReader(str(f)).pages))
 elif f.suffix=='.html':
  s=BeautifulSoup(f.read_text(),'html.parser')
  for x in s(['script','style','nav']):x.decompose()
  text=s.get_text('\n',strip=True)
 else:continue
 (OUT/'raw'/(f.stem+'.txt')).write_text(text)
 print(f.name,len(text))
