from pathlib import Path
import sys,hashlib,json,shutil,subprocess
W=Path(__file__).resolve().parents[4]; R=W/'research_v2/review'; work=R/'_work'
sys.path.insert(0,str(work/'v3_deps'));import fitz
candidates=[Path('/Users/thawaree.kha/Downloads/Project-for-Work-private-backup-main/docs/เล่มรายงาน.pdf'),Path('/Users/thawaree.kha/Project-for-Work/docs/เล่มรายงาน.pdf')]
found=[]
for p in candidates:
 if p.exists():
  d=fitz.open(p);found.append((p,len(d),hashlib.sha256(p.read_bytes()).hexdigest()));print(str(p),len(d),found[-1][2]);print(d[0].get_text()[:130])
p,n,h=next(x for x in found if x[1]==105)
out=W/'_input_v1/thesis';out.mkdir(parents=True,exist_ok=True);dest=out/'historical_thesis.pdf';shutil.copyfile(p,dest)
manifest={str(p.relative_to(W)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (W/'_input_v1').rglob('*') if p.is_file()}
design={str(p.relative_to(W)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (W/'research_v2/design').rglob('*') if p.is_file()}
base={'thesis_source':str(p),'thesis_sha256':h,'thesis_pages':n,'input_hashes':manifest,'design_hashes':design,'v2_hashes':{q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in R.glob('*') if q.is_file()}}
(work/'v3_baseline.json').write_text(json.dumps(base,ensure_ascii=False,indent=2))
# Never persist full thesis text: sample-profile pages remain only in PDF.
d=fitz.open(dest)
meta=[]
for i,page in enumerate(d):
 t=page.get_text();lines=t.strip().splitlines(); footer=lines[-1] if lines else ''
 meta.append({'pdf_page':i+1,'footer_candidate':footer if len(footer)<12 else 'UNKNOWN','characters':len(t)})
(work/'v3_page_map.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print('Snapshot frozen:',len(manifest),'inputs',len(design),'design files')
