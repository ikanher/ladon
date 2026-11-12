import json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
root=Path(sys.argv[1]);results=[]
def copy_git(src,dst):
 dst.mkdir()
 for child in src.iterdir():
  if child.name=='objects':(dst/child.name).symlink_to(child,target_is_directory=True)
  elif child.is_dir():shutil.copytree(child,dst/child.name,symlinks=False)
  else:shutil.copy2(child,dst/child.name)
def package_view(src,dst):
 dst.mkdir()
 for child in src.iterdir():
  out=dst/child.name
  if child.name=='.git' and child.is_dir():copy_git(child,out)
  elif child.name=='.lake' and child.is_dir():
   out.mkdir()
   for part in child.iterdir():
    if part.name=='build':(out/part.name).symlink_to(part,target_is_directory=True)
    elif part.is_dir():shutil.copytree(part,out/part.name,symlinks=False)
    else:shutil.copy2(part,out/part.name)
  else:out.symlink_to(child,target_is_directory=child.is_dir())
with tempfile.TemporaryDirectory(prefix='frozen-lake-probe-',dir='/tmp') as td:
 for label,fixture,tool in [('core','core-fixture','lean-core'),('mathlib','mathlib-fixture','lean-mathlib')]:
  src=root/fixture;work=Path(td)/label;work.mkdir()
  for name in ['lean-toolchain','lakefile.toml','lake-manifest.json']:shutil.copy2(src/name,work/name)
  local=work/'.lake';local.mkdir();(local/'build').symlink_to(src/'.lake/build',target_is_directory=True)
  pkg=src/'.lake/packages'
  if pkg.exists():
   dest=local/'packages';dest.mkdir()
   for p in pkg.iterdir():package_view(p,dest/p.name)
  env=dict(os.environ);env['PATH']=str(root/tool/'bin')+os.pathsep+str(root/'system-tools/bin');env['LEAN_SYSROOT']=str(root/tool);env['LEAN']=str(root/tool/'bin/lean');env.pop('LEAN_PATH',None)
  inspect='import os,json; print(json.dumps(os.environ.get("LEAN_PATH", "").split(":")))'
  cmd=[str(root/tool/'bin/lake'),'env',str(root/'python/bin/python3'),'-I','-B','-c',inspect]
  r=subprocess.run(cmd,cwd=work,env=env,text=True,capture_output=True,timeout=120)
  assert r.returncode==0,(label,r.stderr)
  paths=json.loads(r.stdout)
  for entry in paths:
   if not entry: continue
   path=Path(entry)
   if path.exists(): assert path.resolve().is_relative_to(root),(label,entry,path.resolve())
   else: assert path.is_relative_to(work) or path.is_relative_to(root),(label,entry)
  validation=[str(root/tool/'bin/lake'),'env','lean',str(src/'Validation.lean')]
  proof=subprocess.run(validation,cwd=work,env=env,text=True,capture_output=True,timeout=120)
  assert proof.returncode==0 and 'sorryAx' not in proof.stdout+proof.stderr,(label,proof.stdout,proof.stderr)
  results.append({'profile':label,'leanPath':paths,'exitStatus':proof.returncode,'stdout':proof.stdout,'stderr':proof.stderr})
print(json.dumps(results,indent=2))
