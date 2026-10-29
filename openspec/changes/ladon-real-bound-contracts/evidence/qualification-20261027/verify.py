"""Validate current execution results and keep admission denominators separate."""
import hashlib,json
from pathlib import Path
from ladon.real_bound_native_check import native_checker_identity
from ladon.real_bound_native_production import inspect_real_bound

BASE=Path('.codex/state/task41');ROOT=Path.cwd()
def read(path):return json.loads(path.read_text())
def save(name,value):(BASE/name).write_text(json.dumps(value,indent=2)+'\n')
def no_limits(value):
 if isinstance(value,dict):
  assert not any(value.get(k) is True for k in ('timedOut','memoryLimited','outputLimited','timed_out','memory_limited','output_limited'))
  for child in value.values():no_limits(child)
 elif isinstance(value,list):
  for child in value:no_limits(child)

def unchanged(root,manifest):
 bad=[p for p,h in manifest.items() if not (root/p).is_file() or hashlib.sha256((root/p).read_bytes()).hexdigest()!=h]
 assert not bad,bad
 return len(manifest)

runtime=read(BASE/'runtime-before.json');runtime_count=unchanged(ROOT,runtime)
primary_root=Path('.codex/state/navier-stokes-informed-diagnostic')
primary_count=unchanged(primary_root,read(primary_root/'SOURCE-MANIFEST.json'))
prior={}
for name in ['shape-observation-20261025','prefix-admission-20261025','bound-application-20261025','real-rules-20261025','derivative-prefix-20261025','native-admission-20261025']:
 root=Path('openspec/changes/ladon-real-bound-contracts/evidence')/name
 prior[name]=unchanged(root,read(root/'ARTIFACTS.json'))
nat_names=['proof_contract_rules.py','proof_contracts.py','proof_contract_recognition.py','proof_contract_production.py','proof_contract_formal.py']
nat_old=read(Path('openspec/changes/ladon-real-bound-contracts/evidence/shape-observation-20261025/baseline.json'))['files']
nat_count=unchanged(ROOT,{'src/ladon/'+name:nat_old['src/ladon/'+name] for name in nat_names})
native=read(BASE/'native/RESULTS.json');rows=native['cases'];assert len(rows)==9
expected={'canonical':0,'loss-seven':7,'named':0,'inverse_finiteJets':5,'nonbarPart_finiteJets':4}
for row in rows:
 p=read(BASE/'native'/(row['case']+'-production.json'));no_limits(p)
 assert p['check']['result']['checkerIdentity']==native_checker_identity()
 assert p['status']==('admitted' if row['case'] in expected else 'unresolved')
 view=inspect_real_bound(p);assert view['authority']=='none' and not view['freshCheck'] and view['paperNormBridge']=='unresolved'
 if row['case'] in expected:
  record=p['artifacts'][-1]['payload']['record'];assert record['loss']==row['loss']==expected[row['case']]
  assert record['admission']['scope']=='predicate-and-canonical-scalars'
  assert len(p['check']['result']['checks'])==2
 else:assert p['artifacts']==[] and p['authority']=='none'
 if row['case'] in ['multiplication','order','zero']:assert row['goals']==['supported','unresolved']
 if row['case']=='placeholder':assert 'sorryAx' in json.dumps(p['check']) and row['goals'][0]=='unresolved'
observations=[read(p) for p in (BASE/'native').glob('*-observation.json')]
assert sum(o['status']=='observed' for o in observations)==8
symbolic=read(BASE/'native/symbolic-observation.json')
assert symbolic['status']=='unsupported' and symbolic['candidate'] is None and symbolic['contract'] is None
assert all(o['admission']=='unresolved' and o['contract'] is None for o in observations)
replay=read(BASE/'native/REPLAY.json');assert replay['freshJob']
for p in (BASE/'native').glob('*-command.json'):no_limits(read(p))

derivative=read(BASE/'derivative/RESULTS.json');binding=read(BASE/'binding/RESULTS.json');imported=read(BASE/'import/RESULTS.json')
assert len(derivative)==10 and sum(r['status']=='checked-binding' for r in derivative)==2
assert len(binding)==9 and sum(r['status']=='checked-binding' for r in binding)==2
assert imported['original']=='checked-binding' and imported['mutated']=='unresolved'
assert imported['sourceUnchanged'] and imported['pinnedContextUnchanged'] and imported['compiledModuleChanged']
for group in ['derivative','binding','import']:
 process=read(BASE/(group+'-process.json'));no_limits(process);assert process['returncode']==0
 for p in (BASE/group).glob('*-result.json'):
  result=read(p);no_limits(result);assert result['admission']=='unresolved' and result['contract'] is None

peaks=[r['peakRssBytes'] for r in rows]+[replay['peakRssBytes']]
peaks += [read(BASE/(name+'-process.json'))['peak_rss_bytes'] for name in ['derivative','binding','import']]
result={'status':'qualification-passed','native':{'observedCandidates':8,'unsupportedSymbolic':1,'genericAdmissionAttempts':7,'genericAdmitted':3,'genericUnresolvedNegatives':4,'informedAdmissionAttempts':2,'informedAdmitted':2,'falsePromotions':0,'freshReplay':replay,'cases':rows},
 'derivativeBindings':{'positiveAttempts':2,'checked':2,'negativeAttempts':8,'falsePromotions':0,'cases':derivative},
 'namedBindings':{'positiveAttempts':3,'checked':3,'negativeAttempts':8,'falsePromotions':0,'cases':binding,'importedMeaning':imported},
 'peakRssBytes':max(peaks),'maxRssBytes':12*1024**3,'publicWorkerDeadlineSeconds':600,'outerCliDeadlineSeconds':660,
 'historicalNatFilesUnchanged':nat_count,'runtimeFilesUnchanged':runtime_count,'primaryFilesUnchanged':primary_count,'historicalArtifactsUnchanged':prior,
 'runtimeManifest':'runtime-before.json','sourceAuditPost':1819,
 'sourceTheoremProof':'not-checked','paperNormBridge':'unresolved','historicalEvidenceAuthentication':'not-established',
 'unfamiliarSourceDiscovery':'not-evaluated','heldOutBenefit':'not-evaluated','sourceFidelity':'separate-gate',
 'note':'Public matrix durations exclude initial formal snapshot generation unless recorded in aggregate process receipts. Concurrent matrix elapsed times are not summed as wall time.'}
save('VERIFICATION.json',result)
print(json.dumps({'status':result['status'],'genericNative':'3/3','informedNative':'2/2','nativeNegativePromotions':'0/4','derivativeNegativePromotions':'0/8','namedNegativePromotions':'0/8','symbolic':'unsupported','peakGiB':round(max(peaks)/1024**3,3)}))
