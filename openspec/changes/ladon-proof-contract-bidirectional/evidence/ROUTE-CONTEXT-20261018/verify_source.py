"""Independently recompute plan/goal and immutable raw-evidence bindings."""
import hashlib,json,tarfile
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.proof_contract_bridge import _accepted_check

p=Path('openspec/changes/ladon-proof-contract-bidirectional/evidence/ROUTE-CONTEXT-20261018')
def load(name):return json.loads((p/name).read_text())
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def digest(v):return 'sha256:'+hashlib.sha256(canon(v)).hexdigest()
def walk(v):
 if isinstance(v,dict):
  for key,item in v.items():
   yield key,item
   yield from walk(item)
 elif isinstance(v,list):
  for item in v:yield from walk(item)

accept=load('acceptance.json');assert accept['status']=='PASS'
runtime=load('RUNTIME.json');expected={r['path']:r['sha256'] for r in runtime['files']};assert len(expected)==500
assert all(hashlib.sha256(Path(s).read_bytes()).hexdigest()==h for s,h in expected.items())
with tarfile.open(p/'runtime.tar.gz') as tf:archived={m.name:hashlib.sha256(tf.extractfile(m).read()).hexdigest() for m in tf.getmembers() if m.isfile()}
assert archived==expected
artifacts={};peaks=[];metrics={}
for name in ('positive','middle'):
 request=load(name+'-request.json');plan=load(name+'-plan.json');result=load(name+'-result.json');root=Path(request['repoRoot'])
 assert result['planId']==plan['planId'] and result['binding']==plan['binding']
 binding=result['binding'];rows=[]
 assert binding['selectedIdentity']==request['selectedIdentity']
 assert binding['analysisRef']['artifactRef']==request['analysisArtifact']['artifactId']
 assert binding['desiredReadingIdentity']==request['analysisArtifact']['payload']['request']['desiredReadingIdentity']
 assert binding['selectedDemandDigest']==digest(binding['selectedDemand'])
 assert binding['outerDeadlineMonotonic']==request['deadlineMonotonic']
 assert result['routeComparisons']==request['analysisArtifact']['payload']['result']['routeComparisons']
 assert result['planStatus']==request['analysisArtifact']['payload']['result']['status']
 for goal in result['goals']:
  row={k:v for k,v in goal.items() if k not in {'term','result','supervision','termOrigin','goalDigest'}};row['status']='open'
  assert goal['routeBindingDigest']==digest(binding)
  assert goal['goalDigest']==digest(row),(name,goal['id'])
  rows.append({**row,'goalDigest':goal['goalDigest']})
  if 'result' in goal and isinstance(goal['result'],dict) and 'evidenceRef' in goal['result']:
   raw=load_goal_evidence(root,goal['result']);ref=goal['result']['evidenceRef'];artifacts[str(root/ref['path'])]=ref
   if goal['status']=='checked-support':assert _accepted_check(raw) and _accepted_check(goal['result'])
   capture=raw.get('capture',{}).get('capture',{})
   if capture:
    assert capture['captureId']==goal['result']['captureSummary']['captureId']
    assert raw['completion'].get('captureId')==capture['captureId']
    assert raw['typedSubject']['subject']['structural']==capture['goal']['typeStructural']
   for k,v in walk(raw):
    if k in ('peakRssBytes','peak_rss_bytes') and isinstance(v,(int,float)):peaks.append(v)
  if name=='positive':assert goal['status']=='checked-support'
 assert result['planId']==digest({'profile':'route-context-bridge-v1','binding':binding,'goals':rows,'residuals':result['residuals']})
 assert (root/'ThreeSteps.lean').read_bytes()==(p/'ThreeSteps.lean').read_bytes()
 metrics[name]={'status':result['status'],'goals':len(result['goals']),'checked':sum(g['status']=='checked-support' for g in result['goals']),'bytes':(p/(name+'-result.json')).stat().st_size,'elapsedSeconds':result['elapsedSeconds'],'demandDischarged':result['demandDischarged']}
assert metrics['positive']['checked']==13 and metrics['positive']['demandDischarged']
assert metrics['middle']['checked']==1 and not metrics['middle']['demandDischarged']
positive=load('positive-result.json');middle=load('middle-result.json')
assert len(positive['routeComparisons'])>=2
assert [g['occurrence'] for g in positive['goals'] if g['kind']=='premise-supply']==[4,5]
assert 'Fin 5' in positive['goals'][-4]['goal'] and 'Fin 5' not in positive['goals'][-1]['goal']
assert positive['goals'][-1]['termOrigin']=='composition-of-checked-reading-and-transfer'
assert middle['binding']['selectedRequirement']['contractRecord']['features']['regularity']['offset']==0
assert load('middle-request.json')['sourceBindings']['providerSnapshot']['contract']['features']['regularity']['offset']==2
assert 'result' not in middle['goals'][-1]
for name in ('missing-assumption','excluded-parent','closed-reading'):
 result=load(name+'-result.json');assert result['status']=='unresolved-bridge' and not result['demandDischarged']
 for goal in result['goals']:
  if isinstance(goal.get('result'),dict) and 'evidenceRef' in goal['result']:
   ref=goal['result']['evidenceRef'];root=Path(load('positive-request.json')['repoRoot']);raw=load_goal_evidence(root,goal['result']);artifacts[str(root/ref['path'])]=ref
   assert not _accepted_check(raw)
 assert not any(g['status']=='checked-support' for g in result['goals'])
assert 'Unknown identifier' in json.dumps(load_goal_evidence(Path(load('positive-request.json')['repoRoot']),load('excluded-parent-result.json')['goals'][-4]['result']))
for name in ('changed-reading','wrong-provider','forged-assumption','forged-rule','changed-order','changed-checkpoint'):
 result=load(name+'-result.json');assert result['status']=='rejected' and not result['demandDischarged']
for name in ('expired','expired-native'):
 result=load(name+'-result.json');assert result['status']=='incomplete' and 'preparation' not in result
mem=load('memory-stop-result.json');assert mem['memoryReportBackRequired'] and not mem['demandDischarged']
assert 'Stop progress and report back to user' in mem['diagnostic']['message']
flags=[]
for path in p.glob('*-result.json'):
 if path.name=='first-check.json':continue
 result=json.loads(path.read_text());assert path.stat().st_size<=8*1024**2
 assert result['wholeMethodAuthority']=='none' and result['mathematicalFalsity']=='not-established'
 for k,v in walk(result):
  if k in ('peakRssBytes','peak_rss_bytes') and isinstance(v,(int,float)):peaks.append(v)
  if k in ('timedOut','timed_out','memoryLimited','memory_limited','outputLimited','output_limited','memoryReportBackRequired') and v is True:flags.append(path.name)
assert set(flags)=={'memory-stop-result.json'},set(flags)
rawdir=p/'raw-goal-evidence';rawdir.mkdir()
rawmanifest=[]
for absolute,ref in artifacts.items():
 data=Path(absolute).read_bytes();destination=rawdir/(ref['sha256']+'.json');destination.write_bytes(data)
 assert hashlib.sha256(data).hexdigest()==ref['sha256']
 rawmanifest.append({'artifact':str(destination.relative_to(p)), 'originalPath':absolute, **ref})
(p/'RAW-EVIDENCE.json').write_text(json.dumps({'entries':len(rawmanifest),'files':rawmanifest},indent=2))
verification={'status':'PASS','cases':metrics,'rawEvidenceFiles':len(rawmanifest),'rawHashesAndProjectionsVerified':True,'planAndGoalDigestsRecomputed':True,'runtimeEntries':500,'liveAndArchiveHashesMatch':True,'sourceUnchanged':True,'maximumSampledRssBytes':max(peaks),'trueResourceFlagsOnly':sorted(set(flags)),'acceptance':accept,'detectionBenefit':'unmeasured','wholeMethodAuthority':'none'}
(p/'source-verification.json').write_text(json.dumps(verification,indent=2));print(json.dumps(verification,indent=2))
