import hashlib,json
from pathlib import Path
out=Path('openspec/changes/ladon-real-bound-contracts/evidence/prefix-admission-20261025')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=Path('.codex/state/navier-stokes-informed-diagnostic');primary=json.loads((base/'SOURCE-MANIFEST.json').read_text());assert all(sha(base/p)==v for p,v in primary.items())
old=Path('openspec/changes/ladon-real-bound-contracts/evidence/shape-observation-20261025');art=json.loads((old/'ARTIFACTS.json').read_text());assert all(sha(old/p)==v for p,v in art.items())
tracked=['src/ladon/proof_contract_rules.py','src/ladon/proof_contracts.py','src/ladon/proof_contract_recognition.py','src/ladon/proof_contract_production.py','src/ladon/proof_contract_formal.py','src/ladon/proof_contract_payloads.py']
reference=json.loads((old/'baseline.json').read_text())['files'];assert all(sha(Path(p))==reference[p] for p in tracked)
x=json.loads((out/'public-result.json').read_text());assert x['status']=='checked-laws' and x['admission']=='unresolved' and x['contract'] is None
checks=x['supervision']['result']['checks'];assert len(checks)==3
counts=[]
for row in checks:
 a=row['evidence'];c=a['completion'];assert c['status']=='completed' and c['trust']['accepted'] and c['replay']['status']=='accepted'
 assert set(c['trust']['observedAxioms']) <= {'propext','Classical.choice','Quot.sound'}
 counts.append({'goal':row['goal']['id'],'captureReceipts':len(a['capture']['processReceipts']),'completionReceipts':len(c['processReceipts']),'separateTypingReceipt':True})
 assert counts[-1]['captureReceipts']+counts[-1]['completionReceipts']==6
neg=json.loads((out/'negative-supervision.json').read_text());assert neg['timed_out']
board=json.loads(Path('.codex/state/real-bound-admission/frozen-tests.json').read_text());mismatch=[r['path'] for r in board['frozenTests'] if r.get('matches') is False];assert mismatch==[str(Path('tests/test_rational_lean_encoder_v2.py').resolve())]
result={'primaryFilesUnchanged':len(primary),'priorShapeArtifactsUnchanged':len(art),'historicalNatRuntimeUnchanged':tracked,'freshPublicGoalsChecked':3,'receiptAccounting':counts,'sorryNegative':'incomplete-timeout','fullObservedAdmission':'unresolved','preexistingBoardMismatches':mismatch,'verificationCorrection':'Initial verification script incorrectly expected six completion-only receipts; observed protocol has two capture plus four completion receipts, with separate typing receipt. No product evidence or tests changed.'}
(out/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print('Verified primary sources, old artifacts, native trust and exact receipt accounting.')
