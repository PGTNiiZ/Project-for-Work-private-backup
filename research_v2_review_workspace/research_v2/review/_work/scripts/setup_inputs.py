import zipfile,io,hashlib,csv,json,re,subprocess
from pathlib import Path
W=Path(__file__).resolve().parents[4]; work=W/'research_v2/review/_work'
rows=[]; docs={}
def unpack(blob,prefix):
 with zipfile.ZipFile(io.BytesIO(blob)) as z:
  for n in z.namelist():
   if n.endswith('/') or '__MACOSX' in n: continue
   b=z.read(n)
   if n.endswith('.zip'): unpack(b,prefix+n+'!'); continue
   text=b.decode('utf-8-sig'); sha=hashlib.sha256(b).hexdigest(); norm=hashlib.sha256(re.sub(r'\s+','',text).encode()).hexdigest()
   rows.append({'source':prefix+n,'sha256':sha,'normalized_sha256':norm,'canonical':Path(n).name})
   docs.setdefault(norm,(Path(n).name,b))
unpack(Path('/Users/thawaree.kha/Downloads/files.zip').read_bytes(),'files.zip!')
out=W/'_input_v1';out.mkdir(exist_ok=True)
for name,b in docs.values():
 p=out/name
 if p.exists() and p.read_bytes()!=b: p=out/(hashlib.sha256(b).hexdigest()[:8]+'_'+name)
 p.write_bytes(b)
with (out/'DUPLICATE_MAP.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}
(work/'input_manifest.json').write_text(json.dumps(manifest,indent=2))
refs={}
for repo in ['main','backup']:
 root=work/'repos'/repo
 subprocess.run(['git','fetch','--all','--tags'],cwd=root,check=True)
 refs[repo]=subprocess.check_output(['git','for-each-ref','--format=%(refname) %(objectname) %(committerdate:iso-strict)'],cwd=root,text=True)
 (work/(repo+'_refs.txt')).write_text(refs[repo])
 trees={}
 for line in refs[repo].splitlines():
  ref,sha,*_=line.split()
  if sha not in trees:
   trees[sha]=subprocess.check_output(['git','ls-tree','-r',sha],cwd=root,text=True)
 (work/(repo+'_trees.json')).write_text(json.dumps(trees))
print('Documents:',len(docs),'archive entries:',len(rows));print('\n'.join(manifest));print(json.dumps(refs,indent=2))
