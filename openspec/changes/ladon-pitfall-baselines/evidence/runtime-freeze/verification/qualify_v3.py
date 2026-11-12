import hashlib,json,os,subprocess,sys,time
from pathlib import Path
repo=Path('/home/codex/projects/ladon');state=repo/'.codex/state/pitfall-runtime';bundle=state/'bundles/baseline-v3';root=Path('/home/codex/.cache/ladon-pitfall-runtime/reconstructed-v3');cli=repo/'openspec/changes/ladon-pitfall-baselines/scripts/runtime_custody.py';out=repo/'openspec/changes/ladon-pitfall-baselines/evidence/runtime-freeze/verification/reconstruction-v3-r2.json'
anchor=json.loads((state/'capture-v3.stdout.json').read_text())['identity']
report={'schema':'ladon-runtime-reconstruction-v1','identity':anchor,'bundle':str(bundle),'reconstructedRoot':str(root),'commands':[],'status':'running'}
def call(action,*args,expect=0):
 cmd=[sys.executable,str(cli),action,'--bundle',str(bundle),'--identity',anchor,'--root',str(root),*args];start=time.monotonic()
 r=subprocess.run(cmd,text=True,capture_output=True,timeout=1200)
 report['commands'].append({'args':cmd,'expectedExitStatus':expect,'exitStatus':r.returncode,'seconds':time.monotonic()-start,'stdout':r.stdout,'stderr':r.stderr})
 out.write_text(json.dumps(report,indent=2)+'\n')
 if r.returncode!=expect:raise RuntimeError(f'{action} {args}: {r.returncode}: {r.stderr}')
 print('PASS',action,' '.join(args[:3]),flush=True);return r
try:
 call('verify')
 code='''import sys, pathlib, json, os, hashlib, sqlite3, ssl, ctypes, subprocess, _ssl, _sqlite3
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'src'));import ladon
modules=[json,hashlib,sqlite3,ssl,ctypes,subprocess,_ssl,_sqlite3,ladon]
origins={m.__name__:str(pathlib.Path(m.__file__).resolve()) for m in modules}
assert pathlib.Path(sys.prefix).resolve()==root/'python',(sys.prefix,root)
assert pathlib.Path(sys.executable).resolve()==root/'python/bin/python3',sys.executable
assert all(pathlib.Path(x).is_relative_to(root) for x in origins.values()),origins
assert all('site-packages' not in x for x in sys.path),sys.path
assert 'PYTHONPATH' not in os.environ
print(json.dumps({'python':sys.executable,'prefix':sys.prefix,'origins':origins,'sysPath':sys.path,'environment':dict(os.environ)},indent=2))'''
 r=call('exec','--profile','python','--','-I','-B','-c',code,str(root));report['pythonIdentity']=json.loads(r.stdout)
 call('run','--','version','--json')
 for profile,dirname in [('core','lean-core'),('mathlib','lean-mathlib')]:
  r=call('exec','--profile',profile,'--','--print-prefix');assert Path(r.stdout.strip()).resolve()==root/dirname,r.stdout
  fixture='core-fixture' if profile=='core' else 'mathlib-fixture'
  call('exec','--profile',profile,'--cwd',fixture,'--','Validation.lean')
 for relative,action in [('core-fixture/Pitfalls.lean','verify'),('core-fixture/.lake/build/lib/lean/Pitfalls.olean','verify'),('src/ladon/entrypoint.py','run'),('runtime_custody.py','run')]:
  p=root/relative;data=p.read_bytes();st=p.stat()
  try:
   p.write_bytes(data+b'\n# drift probe\n');call(action,*(['--','--version'] if action=='run' else []),expect=1)
  finally:p.write_bytes(data);os.utime(p,ns=(st.st_atime_ns,st.st_mtime_ns))
 extra=root/'src/ladon/_unexpected_custody_probe.py'
 try:extra.write_text('raise RuntimeError("unexpected source")\n');call('verify',expect=1)
 finally:extra.unlink(missing_ok=True)
 call('verify');report['status']='passed'
except Exception as exc:
 report['status']='failed';report['error']=str(exc);raise
finally:out.write_text(json.dumps(report,indent=2)+'\n')
