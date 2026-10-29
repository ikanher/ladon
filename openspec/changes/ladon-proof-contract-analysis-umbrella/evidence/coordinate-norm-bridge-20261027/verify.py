import hashlib,json,time
from pathlib import Path
base=Path('.codex/state/coordinate-norm-bridge')
prior=Path('openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/navier-source-pair-20261027')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root,manifest):
    values=json.loads(manifest.read_text())
    bad=[name for name,digest in values.items() if not (root/name).is_file() or sha(root/name)!=digest]
    assert not bad,bad
    return len(values)
result={
 'runtimeFilesUnchanged':verify(Path('.'),prior/'runtime-before.json'),
 'primaryFilesUnchanged':verify(Path('.codex/state/navier-stokes-informed-diagnostic'),Path('.codex/state/navier-stokes-informed-diagnostic/SOURCE-MANIFEST.json')),
 'previousPairFilesUnchanged':verify(prior,prior/'ARTIFACTS.json'),
 'paperInputsUnchanged':verify(Path('.'),prior/'source-before.json'),
}
original=Path('.codex/state/navier-stokes-informed-diagnostic/formalization/NavierStokes/SmoothFamilyTorusInverse.lean').read_bytes()
assert (base/'FreshSourceBridge.lean').read_bytes().startswith(original)
assert (base/'FreshFourProbe.lean').read_bytes().startswith((base/'FreshSourceBridge.lean').read_bytes())
assert (base/'CoordinateNormBridge.lean').read_bytes()==(base/'attempt-6.lean').read_bytes()
processes=[]
for p in sorted(base.glob('*-process.json')):
    j=json.loads(p.read_text());assert not any(j[k] for k in ('timed_out','memory_limited','output_limited'))
    processes.append({'receipt':p.name,'exit':j['returncode'],'seconds':j['elapsed_seconds'],'peakRssBytes':j['peak_rss_bytes']})
    if p.name in ['attempt-2-process.json','attempt-5-process.json','attempt-6-process.json','fresh-source-process.json']:
        assert j['returncode']==0 and 'sorryAx' not in j['stdout'] and 'error:' not in j['stdout']
j=json.loads((base/'fresh-four-process.json').read_text())
assert j['returncode']==1 and 'Application type mismatch' in j['stdout']
assert 'CoordinateBound F (n + 4) C' in j['stdout'] and 'CoordinateBound F (n + 5) C' in j['stdout']
result.update({
 'originalSelectedSourceCopiedExactly':True,'finalProofMatchesCheckedAttempt':True,
 'genericCoordinateNormComparison':'checked-standard-axioms',
 'coordinatePartialIdentity':'checked-standard-axioms',
 'orderZero':'checked-standard-axioms','factorOneCounterexample':'checked-standard-axioms',
 'coordinateInverseFive':'fresh-selected-source-checked-standard-axioms',
 'fourOrderApplication':'rejected-at-input-bound',
 'paperNormAttribution':False,'nativeRealFrontier':False,'fourOrderRefuted':False,
 'processes':processes,'processSecondsSum':sum(r['seconds'] for r in processes),
 'peakRssBytes':max(r['peakRssBytes'] for r in processes),
 'sharedLeanBudgetSeconds':600,'maxRssBytes':12*1024**3,
 'remainingSecondsAtVerification':json.loads((base/'lean-budget.json').read_text())['deadlineMonotonic']-time.monotonic(),
 'auditBoardPost':1868,
})
(base/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:v for k,v in result.items() if k!='processes'})
