import hashlib,json,tarfile
from pathlib import Path
P=Path('openspec/changes/ladon-proof-contract-bidirectional/evidence/CONTEXT-OBLIGATIONS-20261018')
def load(f):return json.loads((P/f).read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
acceptance=load('acceptance.json');assert acceptance['status']=='PASS'
runtime=load('RUNTIME.json');expected={r['path']:r['sha256'] for r in runtime['files']}
assert len(expected)==493 and all(sha(Path(p).read_bytes())==h for p,h in expected.items())
with tarfile.open(P/'runtime.tar.gz') as tf:
 archive={m.name:sha(tf.extractfile(m).read()) for m in tf.getmembers() if m.isfile()}
assert archive==expected
flags={'memoryLimited','memory_limited','outputLimited','output_limited','timedOut','timed_out','memoryReportBackRequired'}
peakkeys={'peakRssBytes','peak_rss_bytes'}
def walk(obj,path='$'):
 if isinstance(obj,dict):
  for k,v in obj.items():
   if k in flags and v is True:yield ('flag',path+'.'+k)
   if k in peakkeys and isinstance(v,(float,int)):yield ('rss',v)
   yield from walk(v,path+'.'+k)
 elif isinstance(obj,list):
  for i,v in enumerate(obj):yield from walk(v,f'{path}[{i}]')
metrics={};allpeaks=[];positive_goal_count=0
for name in ('ordered','representation','dependent','missing','parent','one-way'):
 result=load(name+'-result.json');planned=load(name+'-plan.json');request=load(name+'-input.json')
 expected_status='checked-support' if name in ('ordered','representation','dependent') else 'unresolved-bridge'
 assert result['status']==expected_status
 assert result['planId']==planned['planId']
 assert result['binding']==planned['binding']
 assert result['binding']['correspondenceRef']==request['correspondenceRef']
 assert result['binding']['originalSource']['sha256']==acceptance['sourceSha256']
 rows=[]
 for goal in result['goals']:
  assert goal['binding']==result['binding']
  original={k:v for k,v in goal.items() if k not in {'goalDigest','term','result','supervision'}}
  original['status']='open'
  assert goal['goalDigest']=='sha256:'+sha(canonical(original))
  rows.append({**original,'goalDigest':goal['goalDigest']})
  if goal['status']=='checked-support':
   checked=goal['result'];assert checked['status']=='supported'
   completion=checked['completion'];assert completion['status']=='completed'
   assert completion['replay']['status']=='accepted' and completion['trust']['accepted'] is True
 if expected_status=='checked-support':
  assert not result['residuals'] and all(g['status']=='checked-support' for g in result['goals'])
  positive_goal_count+=len(result['goals'])
 assert result['planId']=='sha256:'+sha(canonical({'profile':'source-context-bridge-v1','binding':result['binding'],'goals':rows,'residuals':result['residuals']}))
 values=list(walk(result));trueflags=[v for k,v in values if k=='flag'];assert not trueflags
 peaks=[v for k,v in values if k=='rss'];allpeaks.extend(peaks)
 size=(P/(name+'-result.json')).stat().st_size;assert size<=8388608
 metrics[name]={'status':result['status'],'goals':len(result['goals']),'checked':sum(g['status']=='checked-support' for g in result['goals']),'bytes':size,'elapsedSeconds':result['elapsedSeconds'],'maximumSampledRssBytes':max(peaks,default=0),'planAndGoalDigestsRecomputed':True}
 assert result['wholeMethodAuthority']=='none' and result['mathematicalFalsity']=='not-established'
assert positive_goal_count==21,positive_goal_count
rp=load('representation-result.json');assert rp['binding']['objectMap']['n']=={'symbol':'val','args':['i']}
assert rp['binding']['originalInterpretation']['formula']['binder']['domain']=='Fin 5'
dp=load('dependent-result.json');assert dp['binding']['originalInterpretation']['formula']['body']['binder']['domain']=='Fin n'
assert [g['occurrence'] for g in load('ordered-result.json')['goals'] if g['kind']=='premise-supply']==[2,3]
assert 'Unknown identifier' in json.dumps(load('parent-result.json')) and 'Contexts.ordered' in json.dumps(load('parent-result.json'))
assert load('changed-checkpoint-result.json')['status']=='rejected'
assert load('expired-result.json')['status']=='incomplete' and 'preparation' not in load('expired-result.json')
mem=load('memory-stop-result.json');assert mem['memoryReportBackRequired'] and mem['status']=='incomplete'
assert 'Stop progress and report back to user' in mem['diagnostic']['message']
trueflags={};maximum=0
for f in P.glob('*.json'):
 if f.name in ('source-verification.json','MANIFEST.json'):continue
 values=list(walk(json.loads(f.read_text())));hits=[v for k,v in values if k=='flag']
 if hits:trueflags[f.name]=hits
 maximum=max(maximum,max((v for k,v in values if k=='rss'),default=0))
assert set(trueflags)=={'memory-stop-result.json'},trueflags
source=(P/'Contexts.lean').read_bytes();assert sha(source)==acceptance['sourceSha256']
root=Path(load('ordered-input.json')['repoRoot']);assert (root/'Contexts.lean').read_bytes()==source
out={'status':'PASS','runtimeEntries':493,'runtimeArchiveAndLiveHashesMatch':True,'cases':metrics,'positiveCheckedGoalsWithReplayAndTrust':21,'maximumSampledRssBytes':maximum,'allTopLevelResultResourceFlags':trueflags,'sourceUnchanged':True,'acceptance':acceptance,'detectionBenefit':'unmeasured','wholeMethodAuthority':'none'}
(P/'source-verification.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
