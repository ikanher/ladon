import hashlib,json
from pathlib import Path
from ladon.proof_contract_formal import verify_formal_snapshot
repo=Path('/home/codex/projects/ladon')
base=repo/'openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/jet-contract-frontier-20261025'
root=repo/'.codex/state/navier-stokes-informed-diagnostic/formalization'
rows=[]
for name in ['inverse_finiteJets','applyMultiplier_finiteJets','nonbarPart_finiteJets']:
 raw=json.loads((base/(name+'.json')).read_text());v=verify_formal_snapshot(raw,root)
 assert v['status']=='unsupported' and v['contract'] is None and not v['artifacts']
 assert v['observation']['status']=='observed' and v['observation']['sourceModuleOwned']
 assert isinstance(v['observation']['typeExpr'],dict) and isinstance(v['observation']['normalizedTypeExpr'],dict)
 assert v['residuals'][0]['code']=='unsupported-domain'
 assert v['residuals'][0]['feature']=='telescope.b0.type'
 assert v['coverage']['statementFeatures']=='unsupported'
 assert not any(v['featureOrigins'].values())
 c=json.loads((base/(name+'-command.json')).read_text())
 assert c['returncode']==0 and not any(c[k] for k in ['memoryLimited','timedOut','outputLimited'])
 rows.append({'declaration':name,'statementObserved':True,'snapshotVerified':True,'contractExtracted':False,'status':v['status'],'residuals':v['residuals'],'elapsedSeconds':c['elapsedSeconds'],'peakRssBytes':c['peakRssBytes']})
manifest=json.loads((root.parent/'SOURCE-MANIFEST.json').read_text());assert all(hashlib.sha256((root.parent/p).read_bytes()).hexdigest()==h for p,h in manifest.items())
baseline=json.loads((base/'BASELINE.json').read_text())
assert hashlib.sha256((root/'NavierStokes/SmoothFamilyTorusInverse.lean').read_bytes()).hexdigest()==baseline['sourceSha256']
assert all(hashlib.sha256((repo/p).read_bytes()).hexdigest()==h for p,h in baseline['runtime'].items())
previous=repo/'openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/norm-route-audit-20261025'
old=json.loads((previous/'ARTIFACTS.json').read_text());assert all(hashlib.sha256((previous/p).read_bytes()).hexdigest()==h for p,h in old.items())
result={'schema':'local-jet-contract-baseline-v1','observedStatements':3,'extractedContracts':0,'fixedLossObserved':2,'fixedLossExtracted':0,'symbolicLossObserved':1,'symbolicLossExtracted':0,'originalFilesUnchanged':len(manifest),'priorRouteArtifactsUnchanged':len(old),'relevantRuntimeUnchanged':True,'totalCommandSeconds':sum(r['elapsedSeconds'] for r in rows),'peakRssBytes':max(r['peakRssBytes'] for r in rows),'cases':rows,'proposedTarget':{'fixedLossExtracted':2,'fixedLossTotal':2,'symbolicLossRemainsUnsupported':True},'discoveryCredit':False,'profileImplemented':False}
with (base/'VERIFICATION.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print({k:result[k] for k in ['observedStatements','extractedContracts','totalCommandSeconds','originalFilesUnchanged','priorRouteArtifactsUnchanged','relevantRuntimeUnchanged']})
