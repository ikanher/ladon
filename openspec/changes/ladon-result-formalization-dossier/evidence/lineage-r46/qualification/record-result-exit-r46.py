import hashlib,json,subprocess
from datetime import datetime,timezone
from pathlib import Path
base=Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s/full-qualification')
project=Path('/home/codex/projects/ladon')
context=json.loads((base/'context-r46.json').read_text())
candidate=Path(context['workingDirectory'])
commit=json.loads((base/'candidate-r46.json').read_text())['commit']
bundle=base/'integration-bundle-r46'
child=project/'openspec/changes/ladon-result-claim-correspondence'
parent=project/'openspec/changes/ladon-result-understanding-and-release-umbrella'

def ref(path):
    path=Path(path)
    return {'path':str(path),'digest':'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()}

def load(path):return json.loads(Path(path).read_text())

prerequisites=load(base/'prerequisites-r46/commands.json')
assert len(prerequisites)==11 and all(r['exitCode']==0 for r in prerequisites)
qualification={}
for family in ('correctness','authority','integration','discovery'):
    receipt=load(bundle/f'{family}-receipt.json')
    assert receipt['status']=='passed'
    for key in ('candidateIdentity','sourceTreeIdentity','wheelDigest','environmentRef','producerIdentity'):
        assert receipt[key]==context[key],(family,key)
    runtimes={}
    for runtime in ('py311','py312'):
        result=load(base/f'{family}-r46-{runtime}.json')
        assert result['exitCode']==0 and len(result['passed'])==len(result['collected'])
        runtimes[runtime]={'passed':len(result['passed']),'collected':len(result['collected']),
                           'result':ref(base/f'{family}-r46-{runtime}.json'),
                           'log':ref(base/f'{family}-r46-{runtime}.log')}
    qualification[family]={'receiptIdentity':receipt['receiptIdentity'],
                          'receipt':ref(bundle/f'{family}-receipt.json'),'runtimes':runtimes}
for runtime in ('py311','py312'):
    integration=load(base/f'integration-validation-r46-{runtime}.json')
    discovery=load(base/f'discovery-validation-r46-{runtime}.json')
    assert integration['status']==discovery['status']=='passed'
    assert integration['candidateCommit']==commit
    assert len(load(base/f'integration-mutations-r46-{runtime}.json'))==10
    assert len(discovery['networkMutations'])==5

report={'schemaVersion':1,'status':'passed','candidateCommit':commit,
        'recordedAt':datetime.now(timezone.utc).isoformat(),'bundleRoot':str(bundle),
        'context':ref(base/'context-r46.json'),'qualification':qualification,
        'prerequisites':prerequisites,
        'validators':{r:{kind:ref(base/f'{kind}-validation-r46-{r}.json')
                         for kind in ('integration','discovery')} for r in ('py311','py312')},
        'historicalQualification':'integration-requalification-r41.json retains original earlier failures and candidate identities.',
        'limitations':['Recorded candidate qualification does not complete the upstream umbrella or its independent review and historical order requirements.',
                      'No public distribution, license or institutional acceptance is established.',
                      'Historical candidate captures remain immutable and are not attributed to this execution.']}
integration_path=parent/'integration-requalification-r46.json'
assert not integration_path.exists()
integration_path.write_text(json.dumps(report,indent=2)+'\n')
commands=load(base/'result-focused-commands-r46.json')
assert all(c['exitCode']==0 for c in commands)
for runtime in ('py311','py312'):
    assert '82 passed' in (base/f'result-installed-r46-{runtime}.log').read_text()
baseline=load(base/'baseline-comparison-r46.json');assert baseline['status']=='passed'
usage=load(base/'result-usage-r46/commands.json')
assert len(usage)==4 and all(c['exitCode']==0 for c in usage)
contracts={str(p.relative_to(candidate)):ref(p)['digest'] for p in [
    candidate/'openspec/changes/ladon-result-claim-correspondence/specs/ladon-result-claim-correspondence/spec.md',
    candidate/'src/ladon/schemas/ladon-result-manifest-v1.schema.json',
    candidate/'src/ladon/proofir_v3.py',candidate/'src/ladon/proofir_attachment_policy.py',
    candidate/'src/ladon/stored_candidate_type.py',
    candidate/'openspec/changes/ladon-authority-safe-verified-discovery-umbrella/children/integration-acceptance-inventory.json',
    candidate/'openspec/changes/ladon-authority-safe-verified-discovery-umbrella/children/discovery-acceptance-inventory.json']}
implementation=load(base/'source-manifest-r46.json')['files']
implementation={p:d for p,d in implementation.items() if p in {'src/ladon/_result_manifest_shape.py','src/ladon/result_manifest.py','src/ladon/result_manifest_io.py','src/ladon/result_manifest_summary.py','src/ladon/result_evidence_io.py','src/ladon/result_resolution.py','src/ladon/result_cli.py','src/ladon/cli.py','src/ladon/entrypoint.py','src/ladon/schemas/ladon-result-manifest-v1.schema.json','tests/test_result_manifest.py','tests/test_result_cli.py','tests/test_result_resolution.py','docs/RESULT_MANIFEST.md'}}
exit={'schemaVersion':1,'milestoneId':'ladon-result-claim-correspondence:full','status':'passed',
      'recordedAt':datetime.now(timezone.utc).isoformat(),'candidateCommit':commit,
      **{k:context[k] for k in ('candidateIdentity','sourceTreeIdentity','wheelDigest','environmentRef')},
      'evidenceContractIdentities':contracts,'qualification':ref(integration_path),
      'commands':commands,'outcomes':{'installedManifestResolverTests':{'py311':82,'py312':82},
        'baseline':baseline,'usage':usage,
        'negativeEvidence':'Ambiguous, missing, stale, weak, contradictory and malformed canonical inputs retain rejection/unresolved distinctions.'},
      'implementationFiles':implementation,'omissions':[],
      'limitations':['Resolution binds stored canonical target identity only; checker acceptance and live source freshness remain not-assessed.',
                    'Project revision and source-map associations are producer-declared; reviewer identities remain self-attributed.',
                    'Synthetic positive fixtures are not real Lean proofs; the frozen exposition retains 20 unresolved targets.',
                    'This claim-correspondence compatibility receipt does not itself qualify the dossier, guides or bundles, complete the upstream umbrella, or establish measured benefit or human understanding.',
                    'The full qualification ran on an immutable isolated candidate; later task/report metadata is separately validated.']}
exit_path=child/'full-acceptance-r46.json';assert not exit_path.exists()
exit_path.write_text(json.dumps(exit,indent=2)+'\n')
print(json.dumps({'qualification':ref(integration_path),'fullExit':ref(exit_path)}))
