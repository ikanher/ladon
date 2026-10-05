"""Compare current commands to frozen baseline without changing its expectations."""
from pathlib import Path
import argparse, json, hashlib, runpy
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,required=True);parser.add_argument('--ladon',type=Path,required=True);parser.add_argument('--runtime',required=True);args=parser.parse_args()
base=Path(__file__).parent.parent/'candidate/openspec/changes/ladon-result-understanding-and-release-umbrella/baselines/fixed-epoch-v1'
inv=json.loads((base/'inventory.json').read_text())
for name,expected in inv['files'].items():assert 'sha256:'+hashlib.sha256((base/name).read_bytes()).hexdigest()==expected,name
h=runpy.run_path(str(base/'replay.py'));out=args.output_dir;out.mkdir(exist_ok=False)
original=json.loads((base/'manifest.json').read_text());commands=[]
for name,manifest in h['variants'](original):
 p=out/(name+'.json');h['save'](p,manifest);commands.append(h['run'](args.ladon,out,name,['result','validate',str(p)]))
for name,tail in [('baseline-text',['validate',str(out/'baseline.json'),'--format','text']),('inspect',['inspect',str(out/'baseline.json')]),('guide',['guide',str(out/'baseline.json')])]:commands.append(h['run'](args.ladon,out,name,['result',*tail]))
results=[]
for record in commands:
 name=record['id'];old=json.loads((base/'observations'/args.runtime/(name+'.command.json')).read_text())
 if name=='inspect':
  assert old['exitCode']==2 and record['exitCode']==0
  assert not (out/record['stderr']).read_bytes()
  payload=json.loads((out/record['stdout']).read_text())
  assert payload['operation']=='inspect' and payload['inspectionScope']=='offline-supplied-evidence'
  assert payload['coverage']['canonicalResolution']=={'unresolved':20}
  assert payload['coverage']['proofCoverage']==payload['coverage']['transitiveTrust']=='unknown'
  assert payload['pagination']['total']==30 and 0<payload['pagination']['returned']<=100
  assert (out/record['stdout']).stat().st_size<=32768
  results.append({'id':name,'comparison':'expected-feature-addition','oldExitCode':2,'newExitCode':0,'scope':'Bounded offline inspection; frozen manifest still lacks canonical inputs.'})
 elif name=='guide':
  assert old['exitCode']==2 and record['exitCode']==0
  payload=json.loads((out/record['stdout']).read_text())
  assert payload['operation']=='guide' and payload['scope']=='offline-supplied-evidence'
  assert payload['guideStatus']=='unavailable' and payload['rows'][0]['status']=='unavailable'
  assert payload['reuseApplicability']=='not-checked' and not (out/record['stderr']).read_bytes()
  results.append({'id':name,'comparison':'expected-feature-addition','oldExitCode':2,'newExitCode':0,'scope':'Explicit missing guide; no generated explanation or canonical promotion.'})
 else:
  assert record['exitCode']==old['exitCode'],name
  assert (out/record['stdout']).read_bytes()==(base/'observations'/args.runtime/old['stdout']).read_bytes(),name
  new=(out/record['stderr']).read_bytes();prior=(base/'observations'/args.runtime/old['stderr']).read_bytes()
  if new or prior:assert json.loads(new)['diagnostic']['code']==json.loads(prior)['diagnostic']['code'],name
  results.append({'id':name,'comparison':'unchanged','exitCode':record['exitCode']})
for name,expected in inv['files'].items():assert 'sha256:'+hashlib.sha256((base/name).read_bytes()).hexdigest()==expected,name
report={'status':'passed','runtime':args.runtime,'cases':9,'unchangedCases':7,'expectedFeatureAdditions':2,'frozenFiles':len(inv['files']),'originalBaselineUnchanged':True,'comparisons':results,'commands':commands}
h['save'](out/'summary.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ('commands','comparisons')}))
