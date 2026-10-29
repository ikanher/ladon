"""Verify frozen runtime, complete owners and protected earlier evidence."""
import ast
import hashlib
import json
from pathlib import Path

from ladon.real_prose_native_payload import recognition_history
from ladon.real_prose_native_production import inspect_real_prose_bound
from ladon.proofir_v3 import validate_envelope_batch

b=Path('.codex/state/real-prose-native');live=b/'live'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root,manifest):
 values=json.loads(manifest.read_text())
 bad=[n for n,h in values.items() if not (root/n).is_file() or sha(root/n)!=h]
 assert not bad,bad
 return len(values)
protected={}
for label,path in [
 ('sourcePair','openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/navier-source-pair-20261027'),
 ('normBridge','openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/coordinate-norm-bridge-20261027'),
 ('feasibility','openspec/changes/ladon-real-prose-contracts/evidence/proposition-feasibility-20261027'),
 ('observation','openspec/changes/ladon-real-prose-contracts/evidence/prose-observation-production-20261027'),
 ('recognition','openspec/changes/ladon-real-prose-contracts/evidence/prose-shape-v2-20261027')]:
 root=Path(path);protected[label]=verify(root,root/'ARTIFACTS.json')
root=Path('.codex/state/navier-stokes-informed-diagnostic')
protected['primary']=verify(root,root/'SOURCE-MANIFEST.json')
protected['auditedProduction']=verify(Path('.'),b/'AUDIT-REVISION-FINAL.json')
deadline=json.loads((live/'budget.json').read_text())['deadlineMonotonic']
cases=[]
for label,status,loss,scope,exit_code in [
 ('navier-produced','authored',4,'global',0),
 ('global-produced','authored',5,'global',0),
 ('set-produced','authored',7,'set-indexed',0),
 ('wrong-produced','unresolved',None,None,2),
 ('navier-replayed','authored',4,'global',0)]:
 saved=json.loads((live/(label+'.json')).read_text())
 assert saved['status']==status and saved['authority']=='none' and saved['admission']=='unresolved'
 inspected=inspect_real_prose_bound(saved)
 assert inspected['freshCheck'] is False and inspected['authority']=='none'
 artifacts=saved['check']['result']['artifacts']
 if status=='authored':
  validate_envelope_batch(artifacts)
  record=artifacts[-1]['payload']['record']
  assert record['loss']==loss and record['scope']['kind']==scope
  assert record['admission']=='unresolved' and artifacts[-1]['payload']['checkRunRefs']==[]
  assert record['origins']['constantGuard']
 else:assert artifacts==[]
 process=json.loads((live/(label+'-process.json')).read_text())
 assert process['returncode']==exit_code
 assert not any(process[k] for k in ['timed_out','memory_limited','output_limited'])
 assert deadline-600 <= process['startedMonotonic'] <= process['finishedMonotonic'] <= deadline
 assert process['peak_rss_bytes'] <= 12*1024**3
 assert (live/(label+'.json')).stat().st_size <= 8*1024**2
 assert len(process['stdout'].encode()) + len(process['stderr'].encode()) <= 8*1024**2
 cases.append({'case':label,'status':status,'loss':loss,'scope':scope,'seconds':process['elapsed_seconds'],
               'peakRssBytes':process['peak_rss_bytes']})
first=json.loads((live/'navier-produced.json').read_text());replayed=json.loads((live/'navier-replayed.json').read_text())
f=recognition_history(first['check']['result']['artifacts'][-1]['payload'])
r=recognition_history(replayed['check']['result']['artifacts'][-1]['payload'])
prior=json.loads(Path('.codex/state/prose-shape-v2/live/navier-recognized.json').read_text())
assert f['request']==r['request']==prior['request']
def proposition(x):return x['check']['result']['observation']['check']['result']['observation']['propositionExpr']
assert proposition(f)==proposition(r)==proposition(prior)
assert first['request']==replayed['request']
inspected=json.loads((live/'navier-inspected.json').read_text())
assert inspected['authority']=='none' and inspected['sourceFreshness']=='current' and inspected['freshCheck'] is False
process=json.loads((live/'navier-inspected-process.json').read_text())
assert process['returncode']==0 and not any(process[k] for k in ['timed_out','memory_limited','output_limited'])
assert deadline-600 <= process['startedMonotonic'] <= process['finishedMonotonic'] <= deadline
assert process['peak_rss_bytes'] <= 12*1024**3 and (live/'navier-inspected.json').stat().st_size <= 8*1024**2
def assertions(p):return sorted(ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.Assert))
for name in ['test_real_prose_native_cli.py','test_real_prose_native_records.py']:
 assert assertions(Path('tests')/name)==assertions(b/'quality-proposal'/('before-'+name))
frozen=json.loads((b/'FROZEN-TEST-CHECK.json').read_text())
changed=[row['path'] for row in frozen['frozenTests'] if row.get('matches') is False]
assert changed==['/home/codex/projects/ladon/tests/test_rational_lean_encoder_v2.py']
result={'protectedFilesUnchanged':protected,'publicCases':cases,'maxRssBytes':12*1024**3,
        'publicSharedClockSeconds':600,'publicProcessesWithinOriginalClock':True,'resourceAssertionsExplicit':True,
        'selectedRequestAndPropositionUnchanged':True,'sameAttributionOnReplay':True,
        'frozenAssertionASTsUnchanged':True,'unrelatedFrozenBoardMismatch':changed,
        'distinctReadingsAuthored':3,'distinctReadingsUnresolved':1,'freshSelectedReplays':1,
        'semanticAdmissions':0,'formalConnections':0,'fidelityCertified':False,
        'mathematicalFalsityEstablished':False,'discoveryBenefitEstablished':False,
        'committed':False,'pushed':False}
(b/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print({'protected':protected,'publicCases':len(cases),'semanticAdmissions':0,'formalConnections':0})
