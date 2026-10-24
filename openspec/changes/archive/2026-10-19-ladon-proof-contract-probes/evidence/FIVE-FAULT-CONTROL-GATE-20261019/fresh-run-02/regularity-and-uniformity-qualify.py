"""Root-owned qualification: both typed source families, negatives, memory last."""
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.correspondence_check import prepare_correspondence
from ladon.proof_contract_bridge import _accepted_check
from ladon.proof_contract_bridge_supervision import run_bridge_job
from ladon.proof_contract_probes import check_application_probe, plan_application_probe
from ladon.proof_contract_source import produce_prose_contract
from ladon.proofir_correspondence import bind_native_interpretation, correspondence_artifacts
from ladon.proofir_v3 import detached_content_id, validate_envelope_batch

p = Path(os.environ['LADON_GATE_OUTPUT']).resolve()
started = time.monotonic()
deadline = float(os.environ['LADON_GATE_DEADLINE'])
limits = {'timeout_seconds': 30, 'max_rss_bytes': 12 * 1024**3, 'max_output_bytes': 8 * 1024**2}
cases, attempts = [], []


def save(name, value):
    with (p / (name + '.json')).open('x') as stream:
        json.dump(value, stream, sort_keys=True, ensure_ascii=False, indent=2)


def outcome(name, result, expected, category='api'):
    cases.append({'case': name, 'category': category, 'status': result['status'],
                  'expected': expected, 'elapsedSeconds': time.monotonic() - started})
    print(name, result['status'], cases[-1]['elapsedSeconds'], flush=True)
    assert result['status'] == expected, (name, result.get('diagnostic'))


def invoke(name, request, expected, *, plan_id=None, terms=None, cli=False):
    save(name + '-request', request)
    if terms is not None:
        save(name + '-terms', terms)
    if cli:
        result = invoke_cli(name, plan_id, terms, expected)
    else:
        result = (plan_application_probe(request) if plan_id is None else
                  check_application_probe(request, plan_id, terms))
        save(name + '-result', result)
    outcome(name, result, expected)
    return result


def invoke_cli(name, plan_id, terms, expected):
    operation = 'probe' if plan_id is None else 'check-probe'
    command = [sys.executable, '-m', 'ladon.entrypoint', 'investigation', 'contract', operation,
               '--input', str(p / (name + '-request.json')), '--output', str(p / (name + '-result.json'))]
    if terms is not None:
        command += ['--plan-id', plan_id, '--terms', str(p / (name + '-terms.json'))]
    before = time.monotonic()
    process = subprocess.run(command, env={**os.environ, 'PYTHONPATH': 'src:tests'},
        capture_output=True, text=True, check=False, timeout=max(.1, deadline - time.monotonic()))
    save(name + '-process', {'command': command, 'returnCode': process.returncode,
        'elapsedSeconds': time.monotonic() - before, 'stdout': process.stdout, 'stderr': process.stderr})
    success = expected == 'planned' or expected.startswith('checked-local-')
    assert process.returncode == (0 if success else 2), (name, process.stderr, process.stdout)
    return json.loads((p / (name + '-result.json')).read_text())


def verify_proofs(name, request, result, expected):
    accepted = 0
    for goal in result['goals']:
        compact = goal.get('result')
        if compact:
            raw = load_goal_evidence(request['repoRoot'], compact)
            checked = _accepted_check(raw)
            accepted += checked
            assert checked == (goal['status'] == 'checked-support')
            attempts.append({'case': name, 'goalId': goal['goalId'], 'accepted': checked,
                'goalDigest': goal['goalDigest'], 'evidenceRef': compact['evidenceRef'],
                'processReceipt': goal['supervision']['processReceipt']})
    assert accepted == expected
    assert result['artifact']['payload']['checkRunRefs'] == []
    assert all(g['status'] == 'open' for g in result['artifact']['payload']['result']['goals'])


def source_request(label, originals, source_path, family, version):
    root = (p / (label + '-repo')).resolve()
    root.mkdir()
    shutil.copyfile(source_path / 'Bridge.lean', root / 'Bridge.lean')
    shutil.copyfile(source_path / 'lean-toolchain', root / 'lean-toolchain')
    source = (root / 'Bridge.lean').read_bytes()
    namespace = 'AppProbe' if label == 'regularity' else 'UniformProbe'
    extracted = run_bridge_job('extract-provider', {'repoRoot': str(root), 'sourcePath': 'Bridge.lean',
        'sourceDigest': 'sha256:' + hashlib.sha256(source).hexdigest(),
        'declaration': namespace + '.use', 'application': namespace + '.weak'},
        deadline_monotonic=deadline, limits=limits)
    save(label + '-extraction', extracted)
    assert extracted['status'] == 'completed'
    actual = extracted['result']
    assert actual['complete'] and not actual['localContext'] and not actual['nodes'][0]['premises']
    snapshots, artifacts = [], []
    for original in originals:
        reading = original['interpretation']
        (root / reading['source']['path']).write_bytes((reading['source']['quote'] + '\n').encode())
        snapshot = produce_prose_contract(root, reading, original['contract'], original['featureOrigins'],
            alternative_id=reading['id'], environment_ref=actual['environment'])
        snapshots.append(snapshot)
        artifacts.extend(snapshot['artifacts'])
    sides = []
    for snapshot in snapshots:
        owner = correspondence_artifacts(bind_native_interpretation(
            prepare_correspondence(snapshot['interpretation'], actual, {}), artifacts, source_root=root))
        artifacts.append(owner)
        contract = next(a for a in snapshot['artifacts'] if a['artifactKind'] == 'proofir.contract')
        sides.append({'contractRef': {'artifactRef': contract['artifactId'], 'kind': 'contract',
            'localId': contract['payload']['contractId']}, 'correspondenceRef': {
            'artifactRef': owner['artifactId'], 'kind': 'correspondence',
            'localId': owner['payload']['correspondenceId']}})
    save(label + '-snapshots', snapshots)
    return {'repoRoot': str(root), 'context': {'artifacts': artifacts}, 'left': sides[0], 'right': sides[1],
        'template': {'familyId': family, 'version': version, 'direction': 'right-to-left', 'kind': 'counterexample'},
        'deadlineMonotonic': deadline, 'limits': limits}, sides


save('START', {'startedMonotonic': started, 'deadlineMonotonic': deadline, 'budgetSeconds': 1800,
    'limits': limits, 'scope': 'Regularity v1 and constant-uniformity v2; no other-family or detection claim'})
runtime = json.loads((p / 'RUNTIME.json').read_text())
assert all(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest() == r['sha256'] for r in runtime['files'])
old = Path('openspec/changes/ladon-proof-contract-probes/evidence/REGULARITY-APPLICATION-20261019')
reg_original = json.loads((old / 'snapshots.json').read_text())
regularity, reg_sides = source_request('regularity', reg_original, old / 'probe-repo',
    'regularity-boundary', 'regularity-boundary-v1')
constant_original = json.loads(Path('.codex/state/proof-contract-analysis/constant-probes/feasibility/snapshots.json').read_text())
uniformity, uniform_sides = source_request('uniformity', constant_original,
    Path('.codex/state/proof-contract-analysis/constant-probes/feasibility/repo'),
    'constant-uniformity', 'constant-uniformity-v2')
reg_terms = json.loads(Path('.codex/state/proof-contract-analysis/application-probes/feasibility/terms.json').read_text()) if Path('.codex/state/proof-contract-analysis/application-probes/feasibility/terms.json').exists() else {
    'formal-reading': 'Iff.rfl', 'probe': '''by
  constructor
  · exact AppProbe.weak ()
  · intro h
    have bad := h 0 0
    simpa [AppProbe.M, AppProbe.N, AppProbe.F, AppProbe.C] using bad'''}
constant_terms = json.loads(Path('.codex/state/proof-contract-analysis/constant-probes/feasibility/terms.json').read_text())
for label, request, sides, terms, cli in [
    ('regularity', regularity, reg_sides, reg_terms, False),
    ('uniformity', uniformity, uniform_sides, constant_terms, True)]:
    planned = invoke(label + '-plan', request, 'planned', cli=cli)
    checked = invoke(label + '-checked', request, 'checked-local-nonimplication',
        plan_id=planned['planId'], terms=terms, cli=cli)
    verify_proofs(label + '-checked', request, checked, 2)
    control = {**request, 'left': sides[2], 'template': {**request['template'], 'kind': 'implication'}}
    cp = invoke(label + '-control-plan', control, 'planned', cli=cli)
    cc = invoke(label + '-control-checked', control, 'checked-local-implication',
        plan_id=cp['planId'], terms={'formal-reading': 'Iff.rfl', 'probe': 'by intro h; exact h'}, cli=cli)
    verify_proofs(label + '-control-checked', control, cc, 2)
    if label == 'uniformity':
        uniform_plan = planned

pid = uniform_plan['planId']
invoke('missing-terms', uniformity, 'unresolved', plan_id=pid, terms={}, cli=True)
bad = invoke('failed-term', uniformity, 'unresolved', plan_id=pid,
    terms={'formal-reading': 'Iff.rfl', 'probe': 'by trivial'}, cli=True)
verify_proofs('failed-term', uniformity, bad, 1)
invoke('changed-clock', {**uniformity, 'deadlineMonotonic': deadline - 1}, 'rejected', plan_id=pid, terms=constant_terms)
invoke('changed-limits', {**uniformity, 'limits': {**limits, 'max_rss_bytes': 11 * 1024**3}},
    'rejected', plan_id=pid, terms=constant_terms)
for family, version in [('constant-uniformity', 'constant-uniformity-v1'),
    ('witness-dependence', 'witness-dependence-v1'), ('restricted-domain', 'restricted-domain-v1'),
    ('inequality-direction', 'inequality-direction-v1')]:
    invoke('unsupported-' + family, {**uniformity, 'template': {**uniformity['template'],
        'familyId': family, 'version': version}}, 'unsupported')
invoke('unknown-template', {**uniformity, 'template': {**uniformity['template'], 'version': 'unknown'}}, 'rejected')
invoke('wrong-owner', {**uniformity, 'right': {**uniform_sides[1],
    'correspondenceRef': uniform_sides[0]['correspondenceRef']}}, 'rejected')
for mutation in ['permission', 'telescope']:
    forged = copy.deepcopy(uniformity)
    contract = next(a for a in forged['context']['artifacts'] if a['artifactId'] == forged['right']['contractRef']['artifactRef'])
    record = contract['payload']['record']
    record['features']['constantDependencies']['allowedBinderIds'] = []
    record['features']['witnessDependencies'][0]['allowedBinderIds'] = []
    if mutation == 'telescope':
        record['telescope'][0], record['telescope'][1] = record['telescope'][1], record['telescope'][0]
    contract['artifactId'] = detached_content_id(contract)
    forged['right']['contractRef']['artifactRef'] = contract['artifactId']
    invoke('wrong-' + mutation, forged, 'rejected')
invoke('wrong-context', {**uniformity, 'context': {**uniformity['context'], 'goal': 'True'}}, 'rejected')
symbol_tamper = copy.deepcopy(uniformity)
reading = next(a for a in symbol_tamper['context']['artifacts'] if a['artifactKind'] == 'proofir.interpretation'
               and a['payload']['interpretationId'] == 'uniform-reading-1')
reading['payload']['record']['symbols']['mul']['leanName'] = 'Nat.add'
reading['artifactId'] = detached_content_id(reading)
invoke('native-symbol-tamper', symbol_tamper, 'rejected')

# Explicit semantic-goal tampering BEFORE memory: both hashes are recomputed.
forged = copy.deepcopy(uniform_plan['artifact'])
goal = forged['payload']['result']['goals'][1]
goal['goal'] += ' ∧ True'
goal['goalDigest'] = 'sha256:' + hashlib.sha256(goal['goal'].encode()).hexdigest()
forged['artifactId'] = detached_content_id(forged)
save('rehashed-goal-request', {'context': uniformity['context'], 'artifact': forged})
try:
    validate_envelope_batch([*uniformity['context']['artifacts'], forged])
except ValueError as error:
    rejected = {'status': 'rejected', 'diagnostic': str(error), 'category': 'pure-native-validation'}
else:
    raise AssertionError('Rehashed native goal was admitted')
save('rehashed-goal-result', rejected)
outcome('rehashed-goal', rejected, 'rejected', 'pure-native-validation')

for label, relative in [('quote-drift', 'reading-0.txt'), ('formal-drift', 'Bridge.lean')]:
    path = Path(uniformity['repoRoot']) / relative
    before = path.read_bytes()
    try:
        path.write_bytes(before + b'\n-- changed source\n')
        invoke(label, uniformity, 'rejected')
    finally:
        path.write_bytes(before)
invoke('expired', {**uniformity, 'deadlineMonotonic': 0}, 'incomplete')

# Final resource control: NO proof retries, cap increases or Lean work below.
memory = invoke('memory-last', {**uniformity, 'limits': {**limits, 'max_rss_bytes': 1024**2}}, 'incomplete')
assert memory['diagnostic']['code'] == 'memory-limit' and memory['memoryReportBackRequired']
assert 'Stop progress' in memory['diagnostic']['message']
assert all(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest() == r['sha256'] for r in runtime['files'])
save('RESULT', {'status': 'PASS', 'elapsedSeconds': time.monotonic() - started, 'budgetSeconds': 1800,
    'cases': cases, 'checkerAttempts': len(attempts), 'acceptedChecks': sum(g['accepted'] for g in attempts),
    'proofEvidence': attempts, 'memoryLastNoRetry': True, 'runtimeUnchanged': True,
    'scope': 'Two constructed source-bound families; no NL fidelity, PDE, all-five-family or detection claim'})
