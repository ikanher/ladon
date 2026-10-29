"""Input-profile feasibility only; fixture graphs do not establish source routes."""
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process
from ladon.proofir_v3 import make_envelope, validate_envelope
from ladon.real_bound_shape import observe_bound_shape

BASE = Path('.codex/state/source-pair-current').resolve()
OUT = BASE / 'boundary-retry'
OUT.mkdir(exist_ok=False)
FIXTURE = Path('tests/fixtures/proof_contract_propagation')
NATIVE = Path('openspec/changes/ladon-real-bound-contracts/evidence/qualification-20261027/native')
DEADLINE = time.monotonic() + max(0, (BASE/'boundary/nat-control-process.json').stat().st_mtime + 120 - time.time())

def save(name, value):
    path = OUT / (name + '.json')
    path.write_text(json.dumps(value, indent=2) + '\n')
    return path

def invoke(label, args):
    cmd = [sys.executable, '-m', 'ladon.entrypoint', 'investigation', 'contract', *map(str,args)]
    receipt = run_bounded_target_process(cmd, cwd=Path.cwd(), timeout_seconds=max(0.01, DEADLINE-time.monotonic()), max_rss_bytes=12*1024**3, max_output_bytes=8*1024**2)
    save(label+'-process', {'command':cmd,**asdict(receipt)})
    assert not any((receipt.timed_out, receipt.memory_limited, receipt.output_limited))
    return receipt

positive = OUT/'nat-control-output.json'
r = invoke('nat-control', ['propagate','--derivation',FIXTURE/'graph.json','--contract',FIXTURE/'contract.json','--request',FIXTURE/'request.json','--analysis-id','analysis:profile-control','--output',positive])
assert r.returncode == 0, (r.stdout,r.stderr)
result=json.loads(positive.read_text())['payload']['result']
assert result['complete'] and result['frontiers']
rows=[]
for label in ['canonical','inverse_finiteJets','nonbarPart_finiteJets']:
    production=json.loads((NATIVE/(label+'-production.json')).read_text())
    contract=production['artifacts'][-1]
    validate_envelope(contract)
    cp=save(label+'-contract',contract)
    graph=json.loads((FIXTURE/'graph.json').read_text())
    graph=make_envelope(artifact_kind=graph['artifactKind'],producer=graph['producer'],environment_ref=contract['environmentRef'],subject_refs=graph['subjectRefs'],coverage=graph['coverage'],payload=graph['payload'],limitations=[],extensions=graph['extensions']).to_dict()
    gp=save(label+'-fixture-graph',graph)
    destination=OUT/(label+'-output.json')
    receipt=invoke(label,['propagate','--derivation',gp,'--contract',cp,'--request',FIXTURE/'request.json','--analysis-id','analysis:profile-probe','--output',destination])
    response=json.loads(receipt.stdout)
    assert receipt.returncode==2 and response=={'status':'invalid','error':'contract profile digest mismatch'},response
    assert not destination.exists()
    rows.append({'case':label,'status':response,'seconds':receipt.elapsed_seconds,'peakRssBytes':receipt.peak_rss_bytes,'artifactId':contract['artifactId'],'outputCreated':False})
old=json.loads(Path('openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/source-pair-20261018/formal-snapshot.json').read_text())
shape=observe_bound_shape(old['observation']['normalizedTypeExpr'])
assert shape['candidate'] is None
save('prior-matrix-shape',{'scope':'current pure recognizer applied to historical expression; no fresh source observation','result':shape})
save('RESULT',{'scope':'interface feasibility; no independent source-pair gate credit','natFixtureControl':'complete','realInputs':rows,'priorMatrixShape':'unsupported','sharedDeadlineSeconds':120,'maxRssBytes':12*1024**3,'runtimeEdits':False})
print(json.dumps(rows,indent=2))
