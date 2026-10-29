import subprocess,json,hashlib,csv,re,ast,collections,os
from pathlib import Path
W=Path(__file__).resolve().parents[4]; work=W/'research_v2/review/_work'
# Reuse source Git objects read-only; only alternate configuration in inspection clones.
source=Path('/Users/thawaree.kha/Project-for-Work/.git/objects')
for repo in ['main','backup']:
 alt=work/'repos'/repo/'.git/objects/info/alternates';alt.parent.mkdir(parents=True,exist_ok=True);alt.write_text(str(source)+'\n')

def git(repo,args): return subprocess.check_output(['git',*args],cwd=work/'repos'/repo)
def classify(p):
 s=p.lower();ext=Path(s).suffix
 if any(x in s for x in ['.env','credentials','secret','token']): return 'restricted'
 if ext in ['.csv','.parquet','.npz','.npy','.pt','.pkl','.joblib','.jpg','.jpeg','.png','.gif','.webp','.xlsx','.gz','.zip','.bin','.h5','.hdf5','.pdf']: return 'data' if not any(x in s for x in ['metric','summary','result','aggregate']) else 'result'
 if 'test' in s and ext=='.py':return 'test'
 if ext in ['.py','.ipynb','.sh']:return 'code'
 if ext in ['.toml','.yml','.yaml','.ini','.cfg'] or Path(s).name in ['requirements.txt','.gitignore','.gitattributes']:return 'config'
 if ext in ['.tex','.bib'] or any(x in s for x in ['paper/','manuscript/']):return 'paper'
 if ext=='.json':return 'result'
 if ext in ['.md','.txt']:return 'plan'
 return 'data'

allrows=[];meta={};contents={};progress={}
for repo in ['main','backup']:
 trees=json.loads((work/(repo+'_trees.json')).read_text()); rows=[]; blobs={}
 for commit,tree in trees.items():
  # Obtain unquoted paths with NUL-safe git tree. Never print data-member filenames.
  for entry in git(repo,['ls-tree','-rz',commit]).split(b'\0'):
   if not entry:continue
   info,p=entry.split(b'\t',1);mode,kind,oid=info.decode().split();path=p.decode()
   if kind!='blob': continue
   typ=classify(path)
   record={'repo':repo,'commit':commit,'path':path,'git_blob':oid,'class':typ,'sha256':'UNKNOWN','size':'UNKNOWN','lfs_oid':'','lfs_size':'','content_inspected':'no'}
   rows.append(record);blobs.setdefault(oid,[]).append(record)
 # Batch metadata can access existing local objects; do not demand lazy remote blobs for data.
 env=dict(os.environ,GIT_NO_LAZY_FETCH='1')
 proc=subprocess.run(['git','cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)'],input=('\n'.join(blobs)+'\n').encode(),stdout=subprocess.PIPE,cwd=work/'repos'/repo,env=env)
 sizes={}
 for line in proc.stdout.decode().splitlines():
  parts=line.split()
  if len(parts)==3 and parts[1]=='blob':sizes[parts[0]]=int(parts[2])
 for i,(oid,rs) in enumerate(blobs.items()):
  size=sizes.get(oid)
  for r in rs:r['size']=size if size is not None else 'UNKNOWN'
  typ=rs[0]['class'];path=rs[0]['path']
  # Read text/code only, small possible pointer files. Hash all locally present non-restricted objects streaming.
  if typ=='restricted':continue
  if size is None and typ=='data':continue
  if size is None and typ!='data':
   size=int(git(repo,['cat-file','-s',oid]));sizes[oid]=size
   for r in rs:r['size']=size
  if size is None:continue
  p=subprocess.Popen(['git','cat-file','blob',oid],cwd=work/'repos'/repo,stdout=subprocess.PIPE,env=env)
  h=hashlib.sha256(); buf=[];readtext=typ!='data' and size<8_000_000
  pointer=size<256; first=b''
  while True:
   b=p.stdout.read(1024*1024)
   if not b:break
   h.update(b)
   if pointer or readtext:buf.append(b)
  if p.wait()!=0:continue
  data=b''.join(buf)
  ispointer=data.startswith(b'version https://git-lfs.github.com/spec/v1')
  for r in rs:
   r['sha256']=h.hexdigest()
   if ispointer:
    m=re.search(rb'oid sha256:([0-9a-f]+)\nsize (\d+)',data)
    if m:r['lfs_oid']=m[1].decode();r['lfs_size']=int(m[2])
   elif readtext:r['content_inspected']='static-text'
  if readtext and not ispointer:contents[(repo,oid)]=data
 for r in rows:
  # Paths to data members may themselves identify a person; keep only parent class + opaque path digest.
  if r['class']=='data' and (r['path'].startswith(('image_process/','data/'))):
   r['path']='REDACTED_DATA_MEMBER/'+hashlib.sha256(r['path'].encode()).hexdigest()[:24]+Path(r['path']).suffix
 allrows.extend(rows)
 progress[repo]={'refs':len(trees),'entries':len(rows),'unique_blobs':len(blobs),'hashed_blobs':sum(rs[0]['sha256']!='UNKNOWN' for rs in blobs.values())}
with (work/'repository_inventory.csv').open('w') as f:
 wr=csv.DictWriter(f,fieldnames=allrows[0]);wr.writeheader();wr.writerows(allrows)
(work/'inventory_summary.json').write_text(json.dumps(progress,indent=2))
# Pairwise corresponding paths across every tree pair: inventory lookup only sanitized shared paths.
comparison=[]
backup_index=collections.defaultdict(list)
for r in allrows:
 if r['repo']=='backup':backup_index[r['path']].append(r)
for a in [r for r in allrows if r['repo']=='main']:
 for b in backup_index[a['path']]:
  item={'main_commit':a['commit'],'backup_commit':b['commit'],'path':a['path'],'main_sha256':a['sha256'],'backup_sha256':b['sha256'],'relation':'IDENTICAL_GIT_BLOB' if a['git_blob']==b['git_blob'] else 'DIFFERENT','normalized_equal':'UNKNOWN','function_changes':'UNKNOWN'}
  ab=contents.get(('main',a['git_blob']));bb=contents.get(('backup',b['git_blob']))
  if ab and bb:
   item['normalized_equal']=re.sub(rb'\s+',b'',ab)==re.sub(rb'\s+',b'',bb)
   if a['path'].endswith('.py'):
    def funcs(data):
     try:
      tree=ast.parse(data.decode('utf-8-sig'));return {n.name:ast.dump(n,include_attributes=False) for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
     except (SyntaxError,UnicodeError):return {}
    af,bf=funcs(ab),funcs(bb)
    item['function_changes']=json.dumps({'added':sorted(bf.keys()-af.keys()),'removed':sorted(af.keys()-bf.keys()),'changed':sorted(k for k in af.keys()&bf.keys() if af[k]!=bf[k])})
  comparison.append(item)
with (work/'corresponding_files.csv').open('w') as f:
 wr=csv.DictWriter(f,fieldnames=comparison[0]);wr.writeheader();wr.writerows(comparison)
print(json.dumps(progress,indent=2)); print('Corresponding file pairs:',len(comparison))
