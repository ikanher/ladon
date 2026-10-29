import hashlib
import json
from pathlib import Path

repo = Path('/home/codex/projects/ladon')
evidence = repo / 'openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/provider-premise-audit-20261025'
slice_path = repo / 'openspec/changes/ladon-scoped-slice-traversal/evidence/completion-roundtrip/actual-slice.json'
node = json.loads(slice_path.read_text())['nodes'][0]
sha = lambda data: hashlib.sha256(data).hexdigest()
rows=[]
for key in ['1','2','5','6','7','application']:
    p=evidence / 'repaired' / ('replay-'+key)
    observation=node if key=='application' else next(r['providerObservation'] for r in node['premises'] if str(r['occurrence'])==key)
    capture=json.loads((p/'capture.json').read_text())
    completed=json.loads((p/'completion.json').read_text())
    command=json.loads((evidence/'repaired'/(key+'-command.json')).read_text())
    assert capture['status']=='captured'
    assert all(local['implementationDetail'] for local in capture['capture']['goal']['localContext'])
    assert completed['status']=='completed' and completed['captureId']==capture['capture']['captureId']
    assert completed['termDigest']=='sha256:'+sha(observation['closedProof'].encode())
    assert (p/'term.lean.txt').read_text()==observation['closedProof']
    original=repo/'.codex/state/navier-stokes-informed-diagnostic/formalization/NavierStokes/SmoothFamilyTorusInverse.lean'
    assert (p/'source.lean').read_text()==original.read_text()+'\nexample : '+observation['closedType']+' := by\n  skip\n'
    assert completed['application']['status']=='accepted' and not completed['application']['residualGoals']
    assert completed['replay']['status']=='accepted' and completed['replay']['coverage']=='complete'
    assert completed['trust']['accepted'] and completed['trust']['coverage']=='complete'
    assert set(completed['trust']['observedAxioms']) <= {'propext','Classical.choice','Quot.sound'}
    receipts=capture['processReceipts']+completed['processReceipts']
    assert len(receipts)==6
    assert all(r['returnCode']==0 and not any(r[f] for f in ['timedOut','memoryLimited','outputLimited']) for r in receipts)
    assert command['returncode']==0 and not any(command[f] for f in ['timed_out','memory_limited','output_limited'])
    rows.append({'case':key, 'captureId':completed['captureId'], 'status':completed['status'], 'conditionalOnly':True, 'trust':completed['trust'], 'residualGoals':0, 'processReceiptCount':len(receipts), 'elapsedSeconds':command['elapsed_seconds'], 'peakRssBytes':command['peak_rss_bytes']})
baseline=json.loads((evidence/'BASELINE.json').read_text())
assert all(sha((repo/path).read_bytes())==value for path,value in baseline['inputs'].items())
manifest=json.loads((repo/'.codex/state/navier-stokes-informed-diagnostic/SOURCE-MANIFEST.json').read_text())
source_root=repo/'.codex/state/navier-stokes-informed-diagnostic'
assert all(sha((source_root/path).read_bytes())==value for path,value in manifest.items())
result={'schema':'local-conditional-provider-replay-summary-v1','nativeCorrespondenceReceipt':False,'sliceUnchanged':True,'baselineInputsUnchanged':True,'primaryFilesUnchanged':len(manifest),'allSixConditionalReplaysCompleted':True,'totalElapsedSeconds':sum(r['elapsedSeconds'] for r in rows),'peakRssBytes':max(r['peakRssBytes'] for r in rows),'cases':rows,'paperNormBridge':'unestablished','paperFalsity':'not-established','freshDiscoveryCredit':False}
with (evidence/'VERIFICATION.json').open('x') as f:
    json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))
