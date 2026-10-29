import hashlib,json,time
from pathlib import Path
b=Path('.codex/state/real-prose-integration')
prior=Path('openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/navier-source-pair-20261027')
norm=Path('openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/coordinate-norm-bridge-20261027')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root,manifest):
 values=json.loads(manifest.read_text());bad=[k for k,v in values.items() if not (root/k).is_file() or sha(root/k)!=v];assert not bad,bad;return len(values)
j={
 'runtimeFilesUnchanged':verify(Path('.'),prior/'runtime-before.json'),
 'primaryFilesUnchanged':verify(Path('.codex/state/navier-stokes-informed-diagnostic'),Path('.codex/state/navier-stokes-informed-diagnostic/SOURCE-MANIFEST.json')),
 'priorSourcePairFilesUnchanged':verify(prior,prior/'ARTIFACTS.json'),
 'normBridgeFilesUnchanged':verify(norm,norm/'ARTIFACTS.json'),
}
original=Path('.codex/state/navier-pair-integration/project/PaperVocabulary.lean')
assert (b/'ProseCases.lean').read_bytes().startswith(original.read_bytes())
assert (b/'ProseAliasCases.lean').read_bytes().startswith((b/'ProseCases.lean').read_bytes())
j['originalVocabularyPrefixUnchanged']=True
j['identities']={str(p):sha(p) for p in [original,b/'ProseCases.lean',b/'ProseAliasCases.lean',b/'observe_proposition.lean',b/'failed-helper-1.lean',Path('src/ladon/lean/ladon_formal_contract_helper.lean'),Path('src/ladon/real_bound_shape.py'),Path('src/ladon/proof_contracts.py')]}
expected={'selected-2':('unsupported-bound-shape',False),'generic':('predicate-admission-unchecked',True),'shift-alias':('unsupported-scale',False),'product-alias':('unsupported-bound-shape',False)}
for label,(code,has) in expected.items():
 result=json.loads((b/(label+'-shape.json')).read_text());value=json.loads((b/(label+'-value.json')).read_text());receipt=json.loads((b/(label+'-process.json')).read_text())
 assert receipt['returncode']==0 and value['status']=='observed'
 assert value['protocolVersion']=='experimental-proposition-value-v1'
 assert (result['candidate'] is not None)==has and result['admission']=='unresolved'
 assert result['residuals'][0]['code']==code
for label,msg in [('non-prop','Selected definition does not describe a proposition'),('theorem-selection','Only local proposition definitions are allowed')]:
 receipt=json.loads((b/(label+'-process.json')).read_text());assert receipt['returncode']==1 and msg in receipt['stderr']
 assert not (b/(label+'-shape.json')).exists()
receipts=[]
for p in sorted(b.glob('*-process.json')):
 r=json.loads(p.read_text());assert not any(r[k] for k in ['timed_out','memory_limited','output_limited'])
 receipts.append({'receipt':p.name,'exit':r['returncode'],'seconds':r['elapsed_seconds'],'peakRssBytes':r['peak_rss_bytes']})
j.update({'processes':receipts,'processSecondsSum':sum(r['seconds'] for r in receipts),'peakRssBytes':max(r['peakRssBytes'] for r in receipts),'sharedBudgetSeconds':600,'remainingSecondsAtVerification':json.loads((b/'budget.json').read_text())['deadlineMonotonic']-time.monotonic(),'nativeProseProduction':False,'predicateAdmission':False,'sourceFidelityCertified':False,'paperRefuted':False,'runtimeChanged':False})
(b/'VERIFICATION.json').write_text(json.dumps(j,indent=2)+'\n')
print({k:v for k,v in j.items() if k not in ('identities','processes')})
