"""Verify frozen historical inputs and exact fresh binding proof receipts."""
import hashlib,json
from pathlib import Path
from ladon.real_bound_binding_check import binding_identity
base=Path('.codex/state/real-bound-binding')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
primarybase=Path('.codex/state/navier-stokes-informed-diagnostic')
primary=json.loads((primarybase/'SOURCE-MANIFEST.json').read_text())
assert all(sha(primarybase/p)==digest for p,digest in primary.items())
prior={}
for name in ('shape-observation-20261025','prefix-admission-20261025'):
 folder=Path('openspec/changes/ladon-real-bound-contracts/evidence')/name
 manifest=json.loads((folder/'ARTIFACTS.json').read_text())
 assert all(sha(folder/p)==digest for p,digest in manifest.items())
 prior[name]=len(manifest)
checks=[]
for folder,names in [('public-matrix',['dependent-positive','wrong-measure','sorry','unused-false-no-rescue','forged-live-expression','same-name-changed-definition']),
 ('public-matrix-followup',['unused-false-positive','changed-instance','retained-proof-parameter']),
 ('import-mutation',['original','mutated'])]:
 for name in names:
  result=json.loads((base/folder/(name+'-result.json')).read_text())
  run=json.loads((base/folder/(name+'-command.json')).read_text())
  actual=result['supervision']['result'];assert actual['checkerIdentity']==binding_identity()
  assert result['admission']=='unresolved' and result['contract'] is None
  assert not run['timed_out'] and not run['memory_limited'] and not run['output_limited']
  e=actual['check']['evidence'];row={'case':name,'status':result['status'],'seconds':run['elapsed_seconds'],
                                  'peakRssBytes':run['peak_rss_bytes']}
  if result['status']=='checked-binding':
   c=e['completion'];assert c['status']=='completed' and c['replay']['status']=='accepted'
   assert c['trust']['policy']=='lean-standard-no-placeholders-v1' and c['trust']['accepted']
   assert c['trust']['coverage']=='complete'
   assert set(c['trust']['observedAxioms']) <= {'propext','Classical.choice','Quot.sound'}
   assert e['capture']['capture']['goal']['typeStructural']==e['typedSubject']['subject']['structural']
   row['captureReceipts']=len(e['capture']['processReceipts']);row['completionReceipts']=len(c['processReceipts'])
   assert row['captureReceipts']==2 and row['completionReceipts']==4
  checks.append(row)
assert sum(r['status']=='checked-binding' for r in checks)==3
assert sum(r['status']=='unresolved' for r in checks)==8
sorry=json.loads((base/'public-matrix/sorry-result.json').read_text())['supervision']['result']['check']['evidence']['completion']
assert sorry['diagnostic']['code']=='disallowed-axiom-dependency'
assert 'sorryAx' in sorry['trust']['observedAxioms']
for folder,name,message in [('public-matrix','forged-live-expression','live declaration differs'),
                            ('public-matrix-followup','retained-proof-parameter','proof-valued bound parameters')]:
 e=json.loads((base/folder/(name+'-result.json')).read_text())['supervision']['result']['check']['evidence']
 assert message in e['typecheck']['stdout']
for name in ('stale-source','receipt-is-not-plan'):
 r=json.loads((base/'stale-controls'/(name+'.json')).read_text());assert r['returncode']==2
 assert json.loads(r['stdout'])['status']=='invalid'
assert json.loads((base/'import-mutation/RESULTS.json').read_text())['pinnedContextUnchanged']
# Prior native mathematical profile meanings remain byte-identical.
priorbase=Path('openspec/changes/ladon-real-bound-contracts/evidence/shape-observation-20261025')
old=json.loads((priorbase/'baseline.json').read_text())['files']
nat=['src/ladon/proof_contract_rules.py','src/ladon/proof_contracts.py','src/ladon/proof_contract_recognition.py',
     'src/ladon/proof_contract_production.py','src/ladon/proof_contract_formal.py','src/ladon/proof_contract_payloads.py']
assert all(sha(Path(p))==old[p] for p in nat)
board=json.loads((base/'frozen-tests.json').read_text())
bad=[r['path'] for r in board['frozenTests'] if r.get('matches') is False]
assert bad==[str(Path('tests/test_rational_lean_encoder_v2.py').resolve())]
result={'primaryFilesUnchanged':len(primary),'priorArtifactsUnchanged':prior,'historicalNatRuntimeUnchanged':nat,
        'cases':checks,'predicateBindingsChecked':3,'negativeAttemptsUnresolved':8,'staleOrReceiptInputsRejected':2,
        'preexistingBoardMismatches':bad,'genericSemanticContractsAdmitted':0,'informedContractsAdmitted':'0/2',
        'historicalSorryNegative':'prior 15-minute run remains incomplete; this fresh run rejected sorryAx',
        'harnessCorrection':'Original unused-false positive selected b1 while live J used b2; original failed attempt retained. Corrected control and wrong-instance attempt are separate.'}
(base/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print('Verified',len(primary),'original files,',sum(prior.values()),'prior artifacts,',len(checks),'fresh cases and two invalid-input controls.')
