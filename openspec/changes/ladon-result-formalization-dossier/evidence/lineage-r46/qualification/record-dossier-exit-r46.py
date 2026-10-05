from pathlib import Path
import json,hashlib,subprocess
from datetime import datetime,timezone
root=Path('/home/codex/projects/ladon');run=Path(__file__).parent.parent;q=run/'full-qualification';candidate=run/'candidate';child=root/'openspec/changes/ladon-result-formalization-dossier';parent=root/'openspec/changes/ladon-result-understanding-and-release-umbrella'
def read(path):return json.loads(path.read_text())
def digest(path):return 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path):return {'path':str(path),'digest':digest(path)}
context=read(q/'context-r46.json');claim_path=root/'openspec/changes/ladon-result-claim-correspondence/full-acceptance-r46.json';claim=read(claim_path);development=read(child/'acceptance-r46.json')
assert claim['status']=='passed'
for key in ('candidateIdentity','sourceTreeIdentity','wheelDigest','environmentRef'):assert claim[key]==context[key]
assert development['candidate']['candidateCommit']==claim['candidateCommit']
assert 'sha256:'+development['wheel']['sha256']==context['wheelDigest']
assert development['verification']['independentAuditPost']==227
for py in ('py311','py312'):
 assert '152 passed' in (run/(py+'-contracts.log')).read_text()
 assert read(q/f'integration-validation-r46-{py}.json')['status']=='passed'
 assert read(q/f'discovery-validation-r46-{py}.json')['status']=='passed'
assert read(run/'clean-checkout.command.json')['exitCode']==0
assert '2821 passed' in (run/'clean-checkout.log').read_text()
for row in read(run/'source-inventory.json'):
 if row['path'].startswith(('src/','tests/','scripts/')):assert hashlib.sha256((root/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
contracts=[candidate/'openspec/changes/ladon-result-formalization-dossier/specs/ladon-result-formalization-dossier/spec.md',candidate/'openspec/changes/ladon-result-understanding-and-release-umbrella/specs/ladon-result-formalization-dossier/spec.md']
contracts+=sorted((candidate/'src/ladon/schemas').glob('ladon-result-*.schema.json'))
record={'schemaVersion':1,'milestoneId':'ladon-result-formalization-dossier:full','status':'passed','recordedAt':datetime.now(timezone.utc).isoformat(),'candidateCommit':claim['candidateCommit'],**{k:context[k] for k in ('candidateIdentity','sourceTreeIdentity','wheelDigest','environmentRef')},'evidenceContractIdentities':{str(p.relative_to(candidate)):digest(p) for p in contracts},'prerequisites':{'claimCorrespondence':ref(claim_path),'integrationAndDiscovery':ref(parent/'integration-requalification-r46.json')},'developmentEvidence':ref(child/'acceptance-r46.json'),'priorComponentAndCheckingEvidence':ref(child/'acceptance-r45.json'),'commands':[read(run/(n+'.command.json')) for n in ('clean-checkout','py311-contracts','py312-contracts','default-install','default-origin','default-lineage')],'outcomes':{'installedResultTestsPerRuntime':{'py311':152,'py312':152},'cleanQualityTests':2821,'cleanInstalledContractTests':29,'independentCodeAuditPost':227,'realExposition':development['field'],'frozenBaseline':ref(q/'baseline-comparison-r46.json'),'scope':['Exact claim/component/target and attributable assessment cards','Stored checking operations retain their own evidence dimensions','Explicit read-only lineage and exact canonical-subject dossier selection','Distinct assumption origins, unknown unsupported extraction and transitive trust','Bounded JSON/text pages, revision/input/query-bound cursors and exact omission references']},'omissions':[],'limitations':development['limitations'][1:]+['This is the formalization-dossier capability exit only. Reading guides, portable bundles, process provenance and later qualitative evaluation are open.','The upstream umbrella independent maintainer labels and historical child-order proof remain separate unsatisfied conditions.','The original frozen baseline expected inspect to be unavailable. Its files are unchanged; the new derived comparison records this intentional feature addition and eight unchanged command outcomes.','The prior r45 evidence records historical component/checking field exploration; the current wheel is independently covered by the152 installed result contracts on each supported Python runtime.']}
out=child/'full-acceptance-r46.json';assert not out.exists();out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(ref(out)))
