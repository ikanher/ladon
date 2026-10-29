import hashlib,json
from pathlib import Path
from ladon.correspondence_check import _generated_prelude
b=Path('.codex/state/real-prose-connection')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root,manifest):
 values=json.loads(manifest.read_text());bad=[n for n,h in values.items() if not (root/n).is_file() or sha(root/n)!=h]
 assert not bad,bad
 return len(values)
runtime=Path('.codex/state/real-prose-native/AUDIT-REVISION-FINAL.json')
protected={'productionRuntime':verify(Path('.'),runtime)}
for key,path in [
 ('primary','.codex/state/navier-stokes-informed-diagnostic'),
 ('sourcePair','openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/navier-source-pair-20261027'),
 ('normBridge','openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/coordinate-norm-bridge-20261027'),
 ('feasibility','openspec/changes/ladon-real-prose-contracts/evidence/proposition-feasibility-20261027'),
 ('observation','openspec/changes/ladon-real-prose-contracts/evidence/prose-observation-production-20261027'),
 ('recognition','openspec/changes/ladon-real-prose-contracts/evidence/prose-shape-v2-20261027'),
 ('authoredNative','openspec/changes/ladon-real-prose-contracts/evidence/authored-real-native-20261027')]:
 root=Path(path);manifest=root/('SOURCE-MANIFEST.json' if key=='primary' else 'ARTIFACTS.json')
 protected[key]=verify(root,manifest)
attempts=[]
folder=b/'attempt-sources';folder.mkdir(exist_ok=True)
for label,case,n,witness,basefile in [
 ('five-attempt-1','five',1,False,'Context-before-canonical.lean'),
 ('five-attempt-2','five',2,True,'Context-before-canonical.lean'),
 ('five-attempt-3','five',3,True,'probe-project/Context.lean'),
 ('four-attempt-1','four',1,True,'probe-project/Context.lean')]:
 p=json.loads((b/('probe-'+case+'.json')).read_text())
 source=(b/basefile).read_bytes()
 if witness:
  name='LadonProbeConnectionWitness_'+case
  source+=f'\n theorem _root_.{name} : ({p["goal"]}) := ({p["term"]})\n'.encode()
 (folder/(label+'-source.lean')).write_bytes(source)
 generated=(_generated_prelude(None,source,{},p['goal'])+f'\nexample : {p["goal"]} := by\n  skip\n').encode()
 (folder/(label+'-captured.lean')).write_bytes(generated)
 result=json.loads((b/f'probe-{case}-{n}-result.json').read_text())
 capture=result.get('capture',{}).get('capture')
 if capture:
  assert capture['source']['digest']=='sha256:'+hashlib.sha256(generated).hexdigest(),label
  assert capture['source']['byteLength']==len(generated),label
 receipt=json.loads((b/(label+'-process.json')).read_text())
 assert receipt['returncode']==0 and not any(receipt[k] for k in ['timed_out','memory_limited','output_limited'])
 assert receipt['peak_rss_bytes']<=12*1024**3
 assert len(receipt['stdout'].encode())+len(receipt['stderr'].encode())<=8*1024**2
 completion=result.get('completion',{})
 attempts.append({'attempt':label,'seconds':receipt['elapsed_seconds'],'peakRssBytes':receipt['peak_rss_bytes'],
                  'outerStatus':result['status'],'completionStatus':completion.get('status'),
                  'completionDiagnostic':completion.get('diagnostic'),
                  'replay':completion.get('replay',{}).get('status'),
                  'trustAccepted':completion.get('trust',{}).get('accepted')})
diag=json.loads((b/'SUBJECT-DIAGNOSTIC.json').read_text())
assert diag['cases'][1]['completeTrust'] is True and diag['cases'][1]['kernelReplay']=='accepted'
assert diag['cases'][1]['rawSubjectsEqual'] is False and diag['cases'][1]['diagnosticOnlyAlphaFingerprintsEqual'] is True
assert all(c['diagnosticOnlyAlphaFingerprintsEqual'] for c in diag['cases'])
negative=(b/'FOUR-ROUTE-DIAGNOSTIC.txt').read_text();assert 'shiftFour n' in negative and '(n + 5)' in negative
graph=json.loads((b/'GRAPH-FEASIBILITY.json').read_text());assert graph['roundtripExact'] and graph['encodedGraphBytes']<=8*1024**2
assert graph['rawPairBytes']>8*1024**2
result={'protectedFilesUnchanged':protected,'attempts':attempts,'probeClockSeconds':600,'probeClockReset':False,
 'resourceStops':0,'productionAcceptanceUnchanged':True,'sourcePairConnectionQualified':False,
 'completeOwnerBindingQualified':False,'freshAdmissionOrchestrationQualified':False,
 'underlyingConditionalFiveWitnessKernelAccepted':True,'wrapperAccepted':False,
 'fourRouteRejectedAtInput':True,'mathematicalFalsityEstablished':False,'sourceFidelityEstablished':False,
 'graphRoundtripDiagnosticOnly':graph,'childCompleteTasks':4,'childTotalTasks':6,
 'committed':False,'pushed':False}
(b/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print({'protected':protected,'attempts':len(attempts),'productionChanged':False,'wrapperAccepted':False})
