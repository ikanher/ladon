"""Root-only current-runtime application probe qualification, all attempts retained."""
import copy
import hashlib
import json
import time
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.proof_contract_bridge import _accepted_check
from ladon.proof_contract_bridge_supervision import run_bridge_job
from ladon.proof_contract_probes import check_application_probe, plan_application_probe
from ladon.proof_contract_source import produce_prose_contract
from ladon.correspondence_check import prepare_correspondence
from ladon.proofir_correspondence import bind_native_interpretation, correspondence_artifacts
from ladon.proofir_v3 import detached_content_id

p = Path('.codex/state/proof-contract-analysis/application-probes/qualification-01')
root = (p / 'repo').resolve()
started = time.monotonic()
deadline = started + 1800
limits = {'timeout_seconds': 30, 'max_rss_bytes': 12 * 1024**3, 'max_output_bytes': 8 * 1024**2}
template = {'familyId': 'regularity-boundary', 'version': 'regularity-boundary-v1',
            'direction': 'right-to-left', 'kind': 'counterexample'}
outcomes = []


def save(name, value):
    with (p / (name + '.json')).open('x') as stream:
        json.dump(value, stream, sort_keys=True, ensure_ascii=False, indent=2)


def record(name, result, expected):
    save(name, result)
    outcomes.append({'case': name, 'status': result['status'], 'expected': expected,
                     'elapsedSeconds': time.monotonic() - started})
    print(name, result['status'], time.monotonic() - started, flush=True)
    assert result['status'] == expected, (name, result.get('diagnostic'))


def trusted(result, count):
    supported = [g for g in result['goals'] if g['status'] == 'checked-support']
    assert len(supported) == count
    for goal in supported:
        raw = load_goal_evidence(root, goal['result'])
        assert _accepted_check(raw)
        assert goal['result']['evidenceRef']['path']


save('START', {'startedMonotonic': started, 'deadlineMonotonic': deadline, 'budgetSeconds': 1800,
               'limits': limits, 'scope': 'First closed regularity family only; four other families unsupported'})
runtime = json.loads((p / 'RUNTIME.json').read_text())
assert all(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest() == r['sha256'] for r in runtime['files'])
source = (root / 'Bridge.lean').read_bytes()
extracted = run_bridge_job('extract-provider', {'repoRoot': str(root), 'sourcePath': 'Bridge.lean',
    'sourceDigest': 'sha256:' + hashlib.sha256(source).hexdigest(),
    'declaration': 'AppProbe.use', 'application': 'AppProbe.weak'},
    deadline_monotonic=deadline, limits=limits)
save('extraction', extracted)
assert extracted['status'] == 'completed'
actual = extracted['result']
assert actual['complete'] and not actual['localContext'] and not actual['nodes'][0]['premises']
save('actual', actual)

original = json.loads(Path('.codex/state/proof-contract-analysis/application-probes/feasibility/snapshots.json').read_text())
snapshots, batch = [], []
for index, offset in ((0, 0), (1, 1), (2, 1)):
    reading = copy.deepcopy(original[offset]['interpretation'])
    quote = f'For every s and x, M s (F x) <= C * N (s + {offset}) x.'
    raw = (quote + '\n').encode()
    path = f'reading-{index}.txt'
    (root / path).write_bytes(raw)
    reading['id'] = f'reading-{index}'
    reading['source'] = {'path': path, 'startLine': 1, 'endLine': 1, 'quote': quote,
                         'sha256': hashlib.sha256(raw).hexdigest()}
    snapshot = produce_prose_contract(root, reading, original[offset]['contract'],
        original[offset]['featureOrigins'], alternative_id=reading['id'],
        environment_ref=actual['environment'])
    snapshots.append(snapshot)
    batch.extend(snapshot['artifacts'])
save('snapshots', snapshots)
sides = []
for snapshot in snapshots:
    plan = prepare_correspondence(snapshot['interpretation'], actual, {})
    owner = correspondence_artifacts(bind_native_interpretation(plan, batch, source_root=root))
    batch.append(owner)
    contract = next(a for a in snapshot['artifacts'] if a['artifactKind'] == 'proofir.contract')
    sides.append({'contractRef': {'artifactRef': contract['artifactId'], 'kind': 'contract',
                                'localId': contract['payload']['contractId']},
                  'correspondenceRef': {'artifactRef': owner['artifactId'], 'kind': 'correspondence',
                                       'localId': owner['payload']['correspondenceId']}})
request = {'repoRoot': str(root), 'context': {'artifacts': batch}, 'left': sides[0], 'right': sides[1],
           'template': template, 'deadlineMonotonic': deadline, 'limits': limits}
save('request', request)
planned = plan_application_probe(request)
record('counterexample-plan', planned, 'planned')
terms = {'formal-reading': 'Iff.rfl', 'probe': '''by
  constructor
  · exact AppProbe.weak ()
  · intro h
    have bad := h 0 0
    simpa [AppProbe.M, AppProbe.N, AppProbe.F, AppProbe.C] using bad'''}
checked = check_application_probe(request, planned['planId'], terms)
record('counterexample-checked', checked, 'checked-local-nonimplication')
trusted(checked, 2)

control = {**request, 'left': sides[2], 'template': {**template, 'kind': 'implication'}}
save('control-request', control)
cp = plan_application_probe(control)
record('control-plan', cp, 'planned')
cc = check_application_probe(control, cp['planId'], {'formal-reading': 'Iff.rfl', 'probe': 'by intro h; exact h'})
record('control-checked', cc, 'checked-local-implication')
trusted(cc, 2)

record('missing-terms', check_application_probe(request, planned['planId'], {}), 'unresolved')
bad = check_application_probe(request, planned['planId'], {'formal-reading': 'Iff.rfl', 'probe': 'by trivial'})
record('failed-elaboration', bad, 'unresolved')
trusted(bad, 1)
failed = load_goal_evidence(root, bad['goals'][1]['result'])
assert not _accepted_check(failed)
record('changed-clock', check_application_probe({**request, 'deadlineMonotonic': deadline - 1},
    planned['planId'], terms), 'rejected')
record('changed-limits', check_application_probe({**request, 'limits': {**limits, 'max_rss_bytes': 11 * 1024**3}},
    planned['planId'], terms), 'rejected')

for family in ('constant-uniformity', 'witness-dependence', 'restricted-domain', 'inequality-direction'):
    unsupported = plan_application_probe({**request, 'template': {**template, 'familyId': family, 'version': family + '-v1'}})
    record('unsupported-' + family, unsupported, 'unsupported')
    assert not unsupported['goals'] and unsupported['residuals']
record('unknown-template', plan_application_probe({**request, 'template': {**template, 'version': 'unknown'}}), 'rejected')
crossed = {**sides[1], 'correspondenceRef': sides[0]['correspondenceRef']}
record('wrong-owner', plan_application_probe({**request, 'right': crossed}), 'rejected')
forged = copy.deepcopy(request)
contract = next(a for a in forged['context']['artifacts'] if a['artifactId'] == sides[0]['contractRef']['artifactRef'])
contract['payload']['record']['features']['regularity']['offset'] = 77
contract['artifactId'] = detached_content_id(contract)
forged['left']['contractRef']['artifactRef'] = contract['artifactId']
record('wrong-feature', plan_application_probe(forged), 'rejected')
record('wrong-context', plan_application_probe({**request, 'context': {**request['context'], 'goal': 'True'}}), 'rejected')
quote_path = root / 'reading-0.txt'
before = quote_path.read_bytes()
try:
    quote_path.write_bytes(before + b'Changed source.\n')
    record('source-drift', plan_application_probe(request), 'rejected')
finally:
    quote_path.write_bytes(before)
record('expired', plan_application_probe({**request, 'deadlineMonotonic': 0}), 'incomplete')

# Deliberate memory stop LAST. No proof retries, cap changes or Lean work below.
memory = plan_application_probe({**request, 'limits': {**limits, 'max_rss_bytes': 1024**2}})
record('memory-last', memory, 'incomplete')
assert memory['diagnostic']['code'] == 'memory-limit' and memory['memoryReportBackRequired']
assert 'Stop progress' in memory['diagnostic']['message']
assert all(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest() == r['sha256'] for r in runtime['files'])
save('RESULT', {'status': 'PASS', 'elapsedSeconds': time.monotonic() - started,
    'budgetSeconds': 1800, 'checkedGoals': 5, 'cases': outcomes,
    'scope': 'Authored source-bound regularity reading only; not NL fidelity, PDE or all-five-family acceptance',
    'memoryLastNoRetry': True, 'runtimeUnchanged': True})
