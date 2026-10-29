import subprocess,pathlib,json,re
ROOT=pathlib.Path('/Users/thawaree.kha/Project-for-Work/research_v2_review_workspace/research_v2/review/_work')
def show(repo,ref,path):
 return subprocess.check_output(['git','show',f'{ref}:{path}'],cwd=ROOT/'repos'/repo,text=True)
def excerpt(repo,ref,path,pattern,context=4):
 s=show(repo,ref,path); lines=s.splitlines(); hits=set()
 for i,l in enumerate(lines):
  if re.search(pattern,l,re.I): hits.update(range(max(0,i-context),min(len(lines),i+context+1)))
 return f'\n## {repo}@{ref}:{path}\n'+ '\n'.join(f'{i+1}: {lines[i]}' for i in sorted(hits))+'\n'
if __name__=='__main__':
 import sys
 repo,ref,path,pattern=sys.argv[1:5]
 print(excerpt(repo,ref,path,pattern))
