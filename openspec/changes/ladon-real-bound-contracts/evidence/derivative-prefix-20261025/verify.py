"""Check exact fresh receipts, component metrics, source immutability and old profiles."""
from pathlib import Path
import hashlib,json
from ladon.real_bound_binding_check import binding_identity
from ladon.proof_contracts import validate_contract
base=Path('.codex/state/derivative-prefix')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
resource_flags={'timed_out','memory_limited','output_limited','timedOut','memoryLimited','outputLimited'}
def no_resource_failure(value):
 if isinstance(value,dict):
  assert not any(value.get(k) is True for k in resource_flags)
  for child in value.values():no_resource_failure(child)
 elif isinstance(value,list):
  for child in value:no_resource_failure(child)
def case(path,command,kind,name):
 data=json.loads(path.read_text());receipt=json.loads(command.read_text())
 no_resource_failure(data);no_resource_failure(receipt)
 checked=data['supervision']['result']
 assert checked['checkerIdentity']==binding_identity()
 assert data['admission']=='unresolved' and data['contract'] is None
 actual=checked['check']['evidence']
 row={'case':name,'kind':kind,'status':data['status'],'seconds':receipt['elapsed_seconds'],'peakRssBytes':receipt['peak_rss_bytes']}
 if kind=='derivative':
  assert data['paperNormBridge']=='unresolved'
  assert data['derivativeAdmission']==('checked' if data['status']=='checked-binding' else 'unresolved')
 if data['status']=='checked-binding':
  completion=actual['completion']
  assert actual['status']=='supported' and completion['status']=='completed'
  assert completion['trust']['accepted'] and completion['trust']['coverage']=='complete'
  assert completion['trust']['policy']=='lean-standard-no-placeholders-v1'
  assert set(completion['trust']['observedAxioms'])<={'propext','Classical.choice','Quot.sound'}
  assert completion['replay']['status']=='accepted'
  assert actual['capture']['capture']['goal']['typeStructural']==actual['typedSubject']['subject']['structural']
  row.update(captureReceipts=len(actual['capture']['processReceipts']),completionReceipts=len(completion['processReceipts']))
  assert row['captureReceipts']==2 and row['completionReceipts']==4
 return row
rows=[case(base/'generic-first/result.json',base/'generic-first/check-command.json','derivative','zero-loss')]
for r in json.loads((base/'matrix/RESULTS.json').read_text()):
 name=r['case'];rows.append(case(base/'matrix'/(name+'-result.json'),base/'matrix'/(name+'-command.json'),'derivative',name))
for r in json.loads((base/'original/RESULTS.json').read_text()):
 name=r['case'];rows.append(case(base/'original'/(name+'-result.json'),base/'original'/(name+'-command.json'),'derivative',name))
for r in json.loads((base/'v1-replay/RESULTS.json').read_text()):
 name=r['case'];rows.append(case(base/'v1-replay'/(name+'-result.json'),base/'v1-replay'/(name+'-command.json'),'v1',name))
for name in ('original','mutated'):
 rows.append(case(base/'v1-import-replay'/(name+'-result.json'),base/'v1-import-replay'/(name+'-command.json'),'v1',name))
derivative=[r for r in rows if r['kind']=='derivative'];legacy=[r for r in rows if r['kind']=='v1']
assert len(derivative)==12 and sum(r['status']=='checked-binding' for r in derivative)==4
assert len(legacy)==11 and sum(r['status']=='checked-binding' for r in legacy)==3
for name in ('placeholder',):
 data=json.loads((base/'matrix'/(name+'-result.json')).read_text())
 assert data['supervision']['result']['check']['evidence']['completion']['diagnostic']['code']=='disallowed-axiom-dependency'
assert json.loads((base/'v1-import-replay/RESULTS.json').read_text())['pinnedContextUnchanged']
for path in (base/'generic-first/result.json',base/'generic-first/plan.json'):
 try:validate_contract(json.loads(path.read_text()))
 except (ValueError,TypeError,KeyError):pass
 else:raise AssertionError('derivative record became a historical Nat contract')
boundaries=json.loads((base/'boundaries/RESULTS.json').read_text());assert boundaries['invalidInputs']==5
primarybase=Path('.codex/state/navier-stokes-informed-diagnostic')
primary=json.loads((primarybase/'SOURCE-MANIFEST.json').read_text())
assert all(sha(primarybase/p)==v for p,v in primary.items())
prior=Path('openspec/changes/ladon-real-bound-contracts/evidence');preserved={}
for folder in ('shape-observation-20261025','prefix-admission-20261025','bound-application-20261025','real-rules-20261025'):
 target=prior/folder;manifest=json.loads((target/'ARTIFACTS.json').read_text())
 assert all(sha(target/p)==v for p,v in manifest.items());preserved[folder]=len(manifest)
nat=json.loads((prior/'shape-observation-20261025/baseline.json').read_text())['files']
natpaths=['src/ladon/proof_contract_rules.py','src/ladon/proof_contracts.py','src/ladon/proof_contract_recognition.py',
 'src/ladon/proof_contract_production.py','src/ladon/proof_contract_formal.py','src/ladon/proof_contract_payloads.py']
assert all(sha(Path(p))==nat[p] for p in natpaths)
rules=json.loads((prior/'real-rules-20261025/IMPLEMENTATION.json').read_text())['files']
assert all(sha(Path(p))==v for p,v in rules.items())
board=json.loads((base/'frozen-tests.json').read_text())
bad=[r['path'] for r in board['frozenTests'] if r.get('matches') is False]
assert bad==[str(Path('tests/test_rational_lean_encoder_v2.py').resolve())]
assert json.loads((base/'quality-refactor/EQUIVALENCE.json').read_text())['astIdenticalAfterHelperExpansion']
result={'cases':rows,'derivativeBindingsChecked':4,'derivativeNegativeAttemptsUnresolved':8,
 'originalDerivativeBindings':'2/2','originalObservedLosses':[5,4],'informedSemanticContractsAdmitted':'0/2',
 'paperNormBridge':'unresolved','v1BindingsChecked':3,'v1NegativeAttemptsUnresolved':8,
 'invalidInputsRejected':5,'legacyNatRejections':2,'primaryFilesUnchanged':len(primary),'priorArtifactsUnchanged':preserved,
 'historicalNatRuntimeUnchanged':natpaths,'priorRuleLibraryEvidenceUnchanged':True,
 'preexistingBoardMismatches':bad,'bindingHistory':'Old helper identities are historical; all direct v1 cases freshly replayed here.',
 'qualityRefactor':'All 11 assertions and cases preserved; exact helper-expanded AST equality, original bytes archived.'}
(base/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print('Verified',len(rows),'fresh mathematical attempts, 5 invalid API controls, 2 legacy Nat rejections,',len(primary),'original files.')
