import json,subprocess,hashlib
from pathlib import Path
s=Path(__file__).resolve().parent;p=s/'parity';records=[]
for cmd in ['inspect','guide']:
 for fmt in ['text','json']:
  a=p/f'small-{cmd}-{fmt}-original-before.stdout';b=p/f'small-{cmd}-{fmt}-relocated-before.stdout'
  assert a.read_bytes()==b.read_bytes(),(a,b)
small=s/'small-complete'
for cmd,args in [('resolve',[]),('inspect',['--section','checking']),('guide',['--section','checking','--guide',str(small/'guide.json')])]:
 outs=[]
 for side,exe in [('before',s.parent/'preparation-r65/py311/bin/ladon'),('after',s/'py311/bin/ladon')]:
  argv=[str(exe),'result',cmd,str(small/'manifest.json'),'--artifact',str(small/'artifact-0.json'),'--artifact',str(small/'artifact-1.json'),*args]
  r=subprocess.run(argv,capture_output=True);assert r.returncode==0,r.stderr
  (p/f'explicit-{cmd}-{side}.stdout').write_bytes(r.stdout);outs.append(r.stdout)
  records.append({'command':argv,'exit':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest()})
 assert outs[0]==outs[1]
(p/'extra-records.json').write_text(json.dumps({'relocation_bytes_identical':True,'explicit_requests':records},indent=2)+'\n');print('6 explicit commands and relocation parity pass')
