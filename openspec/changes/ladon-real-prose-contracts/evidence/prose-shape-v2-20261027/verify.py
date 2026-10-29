import hashlib,json,time
from pathlib import Path
from ladon.real_prose_inputs import implementation_identity
from ladon.real_prose_observation import inspect_prose_observation
from ladon.real_prose_recognition import inspect_recognition

b=Path('.codex/state/prose-shape-v2');live=b/'live'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root,manifest):
 values=json.loads(manifest.read_text());bad=[n for n,d in values.items() if not (root/n).is_file() or sha(root/n)!=d];assert not bad,bad;return len(values)
protected={}
for label,root in [('sourcePair',Path('openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/navier-source-pair-20261027')),('normBridge',Path('openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/coordinate-norm-bridge-20261027')),('feasibility',Path('openspec/changes/ladon-real-prose-contracts/evidence/proposition-feasibility-20261027')),('observation',Path('openspec/changes/ladon-real-prose-contracts/evidence/prose-observation-production-20261027'))]:
 protected[label]=verify(root,root/'ARTIFACTS.json')
primary=Path('.codex/state/navier-stokes-informed-diagnostic');protected['primary']=verify(primary,primary/'SOURCE-MANIFEST.json')
protected['auditedRevision']=verify(Path('.'),b/'audit-revision.json')
frozen=json.loads((b/'FROZEN-TEST-CHECK.json').read_text())
assert all(r.get('matches') for r in frozen['frozenTests'] if r['path'].endswith(('test_real_prose_shape_v2.py','test_real_prose_recognition.py','test_real_prose_observation_contract.py')))
current=implementation_identity();cases=[]
for label,status,loss,scope,code in [('navier-recognized','recognized',4,'global',0),('global-five','recognized',5,'global',0),('set-seven','recognized',7,'set-indexed',0),('wrong-product','unresolved',5,'global',2)]:
 s=json.loads((live/(label+'.json')).read_text());i=s['check']['result'];f=i['features'];assert s['status']==status
 assert s['contract'] is None and s['admission']=='unresolved' and s['authority']=='syntax-only'
 assert i['observation']['check']['result']['implementationDigest']==current
 assert f['candidate']['loss']==loss and f['candidate']['scope']['kind']==scope
 assert [r['state'] for r in i['normalization']['worker']['results']]==(['checked','checked'] if code==0 else ['checked','unresolved'])
 inspection=inspect_recognition(s);assert inspection['freshCheck'] is False and inspection['authority']=='none'
 p=json.loads((live/(label+'-process.json')).read_text());assert p['returncode']==code
 assert not any(p[k] for k in ('timed_out','memory_limited','output_limited'))
 cases.append({'case':label,'status':status,'loss':loss,'scope':scope,'seconds':p['elapsed_seconds'],'peakRssBytes':p['peak_rss_bytes'],'leanVersion':i['normalization']['worker']['leanVersion']})
selected=json.loads((live/'navier-recognized.json').read_text())
old=json.loads(Path('.codex/state/prose-observation-production/live/navier-observed-final.json').read_text())
assert selected['request']==old['request']
assert selected['check']['result']['observation']['check']['result']['observation']['propositionExpr']==old['check']['result']['observation']['propositionExpr']
inspect_prose_observation(old)
try:inspect_prose_observation(old,Path('.codex/state/prose-observation-production/live/project'))
except ValueError:old_current_rejected=True
else:raise AssertionError('stale prior runtime must reject current-root semantic reuse')
inspected=json.loads((live/'navier-inspected.json').read_text());assert inspected['authority']=='none' and inspected['sourceFreshness']=='current'
prior=Path('openspec/changes/ladon-real-prose-contracts/evidence/prose-observation-production-20261027')
versions=json.loads((prior/'FINAL-REVISION.json').read_text())
changed=[n for n,h in versions.items() if n.startswith('src/') and sha(Path(n))!=h]
assert set(changed)=={'src/ladon/real_prose_cli.py','src/ladon/real_prose_observation.py'},changed
result={'protectedFilesUnchanged':protected,'priorRuntimeFilesChanged':changed,'publicCases':cases,
 'publicSuccesses':3,'publicResiduals':1,'nativeSemanticContracts':0,'admissions':0,'connections':0,
 'sameSelectedRequestAndTypedProposition':True,'oldHistoryReadable':True,'oldCurrentRuntimeRejected':True,
 'frozenTaskTestsUnchanged':True,'unrelatedFrozenMismatch':json.loads((b/'UNRELATED-FROZEN-BASELINE.json').read_text()),
 'maxRssBytes':12*1024**3,'publicSharedClockSeconds':600,'publicClockCompletedBeforeDeadline':time.monotonic()<json.loads((live/'budget.json').read_text())['deadlineMonotonic'],
 'discoveryBenefitEstablished':False,'mathematicalFalsityEstablished':False,'committed':False,'pushed':False}
assert result['publicClockCompletedBeforeDeadline']
(b/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print({'protected':protected,'publicSuccesses':3,'publicResiduals':1,'priorRuntimeChanges':changed})
