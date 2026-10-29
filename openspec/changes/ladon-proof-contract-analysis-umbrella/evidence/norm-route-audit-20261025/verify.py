import hashlib,json
from pathlib import Path
from ladon.proof_slice import slice_identity
from ladon.proof_slice_validation import validate_slice_shape
from ladon._source_goal_helpers import helper_source
repo=Path('/home/codex/projects/ladon')
base=repo/'openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/norm-route-audit-20261025'
root=repo/'.codex/state/navier-stokes-informed-diagnostic/formalization'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=root/'NavierStokes/SmoothFamilyTorusInverse.lean'
helpersha=hashlib.sha256(helper_source(repo/'src/ladon/lean/ladon_scoped_slice_helper.lean')).hexdigest()
rows=[]
for label,order in [('inverse',1),('centering',0)]:
 x=json.loads((base/f'{label}-slice.json').read_text());validate_slice_shape(x)
 assert slice_identity(x)==x['sliceId'] and x['complete'] and len(x['nodes'])==1
 assert x['helper']['sha256']==helpersha and x['source']['sha256']==sha(source)
 node=x['nodes'][0];arg=node['arguments'][5]
 assert arg['type']['display']=='Nat'
 graph=json.loads(arg['expression']['structural'].split(':',1)[1])
 assert graph=={'nodes':[['const','`OfNat.ofNat','[Lean.Level.zero]'],['const','`Nat','[]'],['app',0,1],['lit',f'Lean.Literal.natVal {order}'],['app',2,3],['const','`instOfNatNat','[]'],['app',5,3],['app',4,6]],'root':7}
 rows.append({'case':label,'status':x['status'],'localCount':len(x['localContext']),'applicationCount':1,'growthOrder':order,'growthArgumentGraphVerified':True,'genericInputOrder':'n + l + 4','sourceReadSpecialization':f'n + {order+4}','frontiers':[f['reason'] for f in x['frontiers']],'helperMatches':True,'sourceMatches':True})
a=json.loads((base/'jet-check-5.json').read_text());b=json.loads((base/'jet-check-4.json').read_text())
assert a['status']=='accepted' and not a['residualPremises']
assert b['status']=='rejected' and b['failureStage']=='application-rejected'
assert (base/'jet-goal-5.txt').read_text().replace('n + 5','n + 4')==(base/'jet-goal-4.txt').read_text()
c=json.loads((base/'jet-capture.json').read_text());r=json.loads((base/'jet-completion.json').read_text())
assert c['status']=='captured' and r['status']=='completed' and c['capture']['captureId']==r['captureId']
assert r['replay']['status']=='accepted' and r['trust']['accepted'] and r['trust']['coverage']=='complete'
assert not r['application']['residualGoals']
assert set(r['trust']['observedAxioms']) <= {'propext','Classical.choice','Quot.sound'}
assert all(local['implementationDetail'] for local in c['capture']['goal']['localContext'])
assert (base/'JetRouteReplay.lean').read_text()==source.read_text()+'\nexample : '+(base/'jet-goal-5.txt').read_text().strip()+' := by\n  skip\n'
assert r['termDigest']=='sha256:'+hashlib.sha256((base/'jet-term.txt').read_text().strip().encode()).hexdigest()
receipts=c['processReceipts']+r['processReceipts'];assert len(receipts)==6
assert all(q['returnCode']==0 and not any(q[k] for k in ['timedOut','memoryLimited','outputLimited']) for q in receipts)
manifest=json.loads((root.parent/'SOURCE-MANIFEST.json').read_text());assert all(sha(root.parent/p)==h for p,h in manifest.items())
baseline=json.loads((base/'BASELINE.json').read_text());assert all(sha(repo/p)==h for p,h in baseline['inputs'].items())
old=repo/'openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/provider-premise-audit-20261025';oldmanifest=json.loads((old/'ARTIFACTS.json').read_text());assert all(sha(old/p)==h for p,h in oldmanifest.items())
value={'schema':'local-norm-route-verification-v1','nativeContractArtifact':False,'sourceBoundApplications':rows,'fiveOrderCandidate':'accepted','fourOrderCandidate':'application-rejected','negativeIsNotRefutation':True,'fullJetCopiedSourceReplay':'completed','axioms':r['trust']['observedAxioms'],'processReceipts':6,'originalFilesUnchanged':len(manifest),'priorProviderArtifactsUnchanged':len(oldmanifest),'baselineInputsUnchanged':True,'paperNormBridge':'unestablished','fourLossAlternative':'not-located-in-inspected-routes','semanticAbsenceClaim':False,'discoveryCredit':False}
with (base/'VERIFICATION.json').open('x') as f:json.dump(value,f,indent=2);f.write('\n')
print({k:value[k] for k in ['fiveOrderCandidate','fourOrderCandidate','fullJetCopiedSourceReplay','originalFilesUnchanged','priorProviderArtifactsUnchanged','paperNormBridge']})
