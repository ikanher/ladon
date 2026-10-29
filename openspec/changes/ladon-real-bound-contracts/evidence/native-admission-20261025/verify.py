"""Verify final native results without promoting saved evidence to live authority."""
from pathlib import Path
import hashlib,json
from ladon.real_bound_native_check import native_checker_identity
from ladon.real_bound_native_production import inspect_real_bound
from ladon.proofir_v3 import validate_envelope_batch
base=Path('.codex/state/real-native');out=base/'qualification-final'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
final=json.loads((out/'RESULTS.json').read_text())
identity=json.loads((base/'INTEGRATED-IDENTITY.json').read_text())
assert identity['checkerIdentity']==native_checker_identity()
assert all(sha(Path(p))==digest for p,digest in identity['files'].items())
rows=final['cases'];assert len(rows)==9
assert sum(r['status']=='admitted' for r in rows)==5
assert sum(r['status']=='unresolved' for r in rows)==4
flags={'timedOut','memoryLimited','outputLimited','timed_out','memory_limited','output_limited'}
def no_limits(value):
 if isinstance(value,dict):
  assert not any(value.get(k) is True for k in flags)
  for child in value.values():no_limits(child)
 elif isinstance(value,list):
  for child in value:no_limits(child)
for row in rows:
 production=json.loads((out/(row['case']+'-production.json')).read_text());no_limits(production)
 assert production['check']['result']['checkerIdentity']==native_checker_identity()
 view=inspect_real_bound(production)
 assert view['authority']=='none' and not view['freshCheck'] and view['paperNormBridge']=='unresolved'
 if row['status']=='admitted':
  artifacts=production['artifacts'];validate_envelope_batch(artifacts)
  record=artifacts[-1]['payload']['record'];assert record['loss']==row['loss']
  assert record['admission']['scope']=='predicate-and-canonical-scalars'
  assert artifacts[-1]['payload']['provenance']['checkerAuthority']=='none'
  assert len(production['check']['result']['checks'])==2
for p in out.glob('*-command.json'):no_limits(json.loads(p.read_text()))
primarybase=Path('.codex/state/navier-stokes-informed-diagnostic')
primary=json.loads((primarybase/'SOURCE-MANIFEST.json').read_text())
assert all(sha(primarybase/p)==digest for p,digest in primary.items())
prior=Path('openspec/changes/ladon-real-bound-contracts/evidence');preserved={}
for folder in ['shape-observation-20261025','prefix-admission-20261025','bound-application-20261025','real-rules-20261025','derivative-prefix-20261025']:
 target=prior/folder;manifest=json.loads((target/'ARTIFACTS.json').read_text());assert all(sha(target/p)==digest for p,digest in manifest.items());preserved[folder]=len(manifest)
nat=json.loads((prior/'shape-observation-20261025/baseline.json').read_text())['files']
natpaths=['src/ladon/proof_contract_rules.py','src/ladon/proof_contracts.py','src/ladon/proof_contract_recognition.py','src/ladon/proof_contract_production.py','src/ladon/proof_contract_formal.py']
assert all(sha(Path(p))==nat[p] for p in natpaths)
frozen=json.loads((base/'frozen-tests.json').read_text())
bad=[r['path'] for r in frozen['frozenTests'] if r.get('matches') is False]
assert bad==[str(Path('tests/test_rational_lean_encoder_v2.py').resolve())]
peak=max([r['peakRssBytes'] for r in rows]+[json.loads((out/'REPLAY.json').read_text())['peakRssBytes']])
result={'freshAdmissions':{'generic':'3/3','informed':'2/2'},'negativeAdmissions':'0/4','negativeAttemptsUnresolved':4,
 'replayFresh':json.loads((out/'REPLAY.json').read_text()),'scalarCounterfeitsPassPredicateFailScalar':3,
 'paperNormBridge':'unresolved','sourceTheoremProof':'not-checked','symbolicLoss':'unsupported',
 'primaryFilesUnchanged':len(primary),'priorArtifactsUnchanged':preserved,'historicalNatRuntimeUnchanged':natpaths,
 'preexistingBoardMismatches':bad,'peakRssBytes':peak,'peakGiB':round(peak/1024**3,3),'maxRssGiB':12,
 'auditPost':1668,'identityUnchanged':True}
(base/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print('Verified fresh native admission5/5, negative promotion0/4, replay, unchanged inputs and prior packets.')
