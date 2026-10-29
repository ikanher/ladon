import ast,hashlib,json
from pathlib import Path
import ladon.real_prose_observation as observer
from ladon.real_prose_inputs import implementation_identity
b=Path('.codex/state/prose-observation-production');live=b/'live'
prior=Path('openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/navier-source-pair-20261027')
norm=Path('openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/coordinate-norm-bridge-20261027')
feasibility=Path('openspec/changes/ladon-real-prose-contracts/evidence/proposition-feasibility-20261027')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root,manifest):
 values=json.loads(manifest.read_text());bad=[name for name,digest in values.items() if not (root/name).is_file() or sha(root/name)!=digest];assert not bad,bad;return len(values)
original_runtime=json.loads((prior/'runtime-before.json').read_text())
changed=[name for name,digest in original_runtime.items() if sha(Path(name))!=digest]
assert changed==['src/ladon/proof_contract_cli.py'],changed
result={'oldRuntimeFilesUnchanged':len(original_runtime)-len(changed),'oldRuntimeFilesChanged':changed,
 'newRuntimeFiles':[str(p) for p in sorted(Path('src/ladon').rglob('*')) if p.suffix in {'.py','.lean'} and str(p) not in original_runtime],
 'primaryFilesUnchanged':verify(Path('.codex/state/navier-stokes-informed-diagnostic'),Path('.codex/state/navier-stokes-informed-diagnostic/SOURCE-MANIFEST.json')),
 'sourcePairFilesUnchanged':verify(prior,prior/'ARTIFACTS.json'),
 'normBridgeFilesUnchanged':verify(norm,norm/'ARTIFACTS.json'),
 'proseFeasibilityFilesUnchanged':verify(feasibility,feasibility/'ARTIFACTS.json'),
 'finalRevisionFilesUnchanged':verify(Path('.'),b/'FINAL-REVISION.json'),
}
current=implementation_identity()
observed=json.loads((live/'navier-observed-final.json').read_text())
replayed=json.loads((live/'navier-replayed-final.json').read_text())
inspected=json.loads((live/'navier-inspected-final.json').read_text())
for snapshot in [observed,replayed]:
 assert snapshot['status']=='observed' and snapshot['authority']=='syntax-only'
 assert snapshot['admission']=='unresolved' and snapshot['contract'] is None
 assert snapshot['check']['result']['implementationDigest']==current
 observer.inspect_prose_observation(snapshot)
assert observed['check']['result']['observation']['propositionExpr']==replayed['check']['result']['observation']['propositionExpr']
assert inspected['status']=='validated-historical' and inspected['authority']=='none' and inspected['freshCheck'] is False
assert inspected['sourceFreshness']=='current' and inspected['contextFreshness']=='current'
initial=json.loads((live/'navier-observed.json').read_text())
assert initial['check']['result']['implementationDigest']!=current
original=json.loads((prior/'interpretation-record.json').read_text())
reading=json.loads((live/'navier-reading.json').read_text())
assert reading['formula']==original['formula'] and reading['symbols']==original['symbols']
assert {k:v for k,v in reading['source'].items() if k!='path'}=={k:v for k,v in original['source'].items() if k!='path'}
assert (live/'project/ProseCases.lean').read_bytes()==Path('.codex/state/real-prose-integration/ProseCases.lean').read_bytes()
checks=[]
for name in ['navier-observed-final','navier-inspected-final','navier-replayed-final']:
 j=json.loads((live/(name+'-process.json')).read_text());assert j['returncode']==0
 assert not any(j[k] for k in ('timed_out','memory_limited','output_limited'))
 checks.append({'receipt':name+'-process.json','seconds':j['elapsed_seconds'],'peakRssBytes':j['peak_rss_bytes']})
def assertions(path):return sorted(ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(path.read_text())) if isinstance(n,ast.Assert))
assert assertions(b/'red/frozen-acceptance-before-quality.py')==assertions(Path('tests/test_real_prose_observation_contract.py'))
assert str(Path(observer.__file__).resolve()).startswith(str(Path('src').resolve()))
result.update({'publicProcesses':checks,'finalProcessSecondsSum':sum(x['seconds'] for x in checks),
 'peakRssBytes':max(x['peakRssBytes'] for x in checks),'maxRssBytes':12*1024**3,'sharedPublicClockSeconds':600,
 'initialSupersededObservationPreserved':True,'sameExactFormulaAndSymbols':True,'copiedSourceSpanOnlyRelocated':True,
 'frozenAcceptanceAssertionsPreserved':25,'publicSelectedCasesObserved':1,'publicSelectedCasesReplayed':1,
 'publicSelectedCasesInspected':1,'nativeSemanticContracts':0,'sourceFidelityCertified':False,
 'boundShapeRecognized':False,'paperRefuted':False,'sourceModule':str(Path(observer.__file__).resolve()),
 'finalSourceAuditPost':1898})
(b/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:v for k,v in result.items() if k not in ['newRuntimeFiles','publicProcesses']})
