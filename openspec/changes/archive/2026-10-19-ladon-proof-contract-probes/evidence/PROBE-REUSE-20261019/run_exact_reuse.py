"""Bounded end-to-end exact-result reuse against a fresh local probe fixture."""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import time
from pathlib import Path

from ladon._proof_contract_route_context_evidence import load_goal_evidence
from ladon.correspondence_check import prepare_correspondence
from ladon.proof_contract_bridge import _accepted_check
from ladon.proof_contract_bridge_supervision import run_bridge_job
from ladon.proof_contract_probes import check_application_probe, plan_application_probe
from ladon.proof_contract_source import produce_prose_contract
from ladon.proofir_correspondence import bind_native_interpretation, correspondence_artifacts

evidence = Path(__file__).resolve().parent
fixture = Path('.codex/state/proof-contract-analysis/application-probes')
previous = fixture / 'qualification-01'
attempt = evidence / 'attempt-04'
attempt.mkdir(exist_ok=True)
scratch = attempt / 'scratch'
root = scratch / 'repo'
root.mkdir(parents=True, exist_ok=True)
for name in ('Bridge.lean', 'lean-toolchain'):
    shutil.copyfile(previous / 'repo' / name, root / name)
started = time.monotonic()
deadline = started + 1800
limits = {'timeout_seconds': 30, 'max_rss_bytes': 12 * 1024**3,
          'max_output_bytes': 8 * 1024**2}
template = {'familyId': 'regularity-boundary', 'version': 'regularity-boundary-v1',
            'direction': 'right-to-left', 'kind': 'counterexample'}
terms = {
    'formal-reading': 'Iff.rfl',
    'probe': '''by
  constructor
  · exact AppProbe.weak ()
  · intro h
    have bad := h 0 0
    simpa [AppProbe.M, AppProbe.N, AppProbe.F, AppProbe.C] using bad''',
}
rows = []


def save(name, value):
    (attempt / f'{name}.json').write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')


source_bytes = (root / 'Bridge.lean').read_bytes()
extraction = run_bridge_job('extract-provider', {'repoRoot': str(root),
    'sourcePath': 'Bridge.lean', 'sourceDigest': 'sha256:' + hashlib.sha256(source_bytes).hexdigest(),
    'declaration': 'AppProbe.use', 'application': 'AppProbe.weak'},
    deadline_monotonic=deadline, limits=limits)
save('fresh-extraction', extraction)
assert extraction['status'] == 'completed' and extraction['result']['complete']
actual = extraction['result']
original = json.loads((fixture / 'feasibility' / 'snapshots.json').read_text(encoding='utf-8'))
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
sides = []
for snapshot in snapshots:
    plan = prepare_correspondence(snapshot['interpretation'], actual, {})
    owner = correspondence_artifacts(bind_native_interpretation(plan, batch, source_root=root))
    batch.append(owner)
    contract = next(item for item in snapshot['artifacts'] if item['artifactKind'] == 'proofir.contract')
    sides.append({'contractRef': {'artifactRef': contract['artifactId'], 'kind': 'contract',
                                'localId': contract['payload']['contractId']},
                  'correspondenceRef': {'artifactRef': owner['artifactId'], 'kind': 'correspondence',
                                       'localId': owner['payload']['correspondenceId']}})
request = {'repoRoot': str(root), 'context': {'artifacts': batch}, 'left': sides[0],
           'right': sides[1], 'template': template, 'deadlineMonotonic': deadline,
           'limits': limits}

planned = plan_application_probe(request)
save('planned', planned)
assert planned['status'] == 'planned', planned.get('diagnostic')
checked = check_application_probe(request, planned['planId'], terms)
save('checked', checked)
assert checked['status'] == 'checked-local-nonimplication', checked.get('diagnostic')
assert len([goal for goal in checked['goals'] if goal['status'] == 'checked-support']) == 2
for goal in checked['goals']:
    assert _accepted_check(load_goal_evidence(root, goal['result']))
rows.append({'case': 'first-check', 'status': checked['status'],
             'reusedGoals': sum(goal.get('reused') is True for goal in checked['goals'])})

reused = check_application_probe(request, planned['planId'], {}, cached_result=checked)
save('reused', reused)
assert reused['status'] == checked['status'], reused.get('diagnostic')
assert all(goal.get('reused') is True for goal in reused['goals'])
assert [goal['result'] for goal in reused['goals']] == [goal['result'] for goal in checked['goals']]
rows.append({'case': 'exact-reuse', 'status': reused['status'],
             'reusedGoals': sum(goal.get('reused') is True for goal in reused['goals']),
             'elapsedSeconds': reused['elapsedSeconds']})

changed_assumptions = {**request, 'left': request['right'], 'right': request['left']}
assumptions = check_application_probe(changed_assumptions, planned['planId'], {}, cached_result=checked)
save('changed-assumptions', assumptions)
assert assumptions['status'] == 'rejected' and assumptions['checkerAuthority'] == 'none'
rows.append({'case': 'changed-assumptions', 'status': assumptions['status'],
             'diagnostic': assumptions['diagnostic']['code']})

changed_template = {**request, 'template': {**request['template'], 'version': 'regularity-boundary-v2'}}
template_result = check_application_probe(changed_template, planned['planId'], {}, cached_result=checked)
save('changed-template', template_result)
assert template_result['status'] == 'rejected' and template_result['checkerAuthority'] == 'none'
rows.append({'case': 'changed-template-revision', 'status': template_result['status'],
             'diagnostic': template_result['diagnostic']['code']})

source_path = root / 'reading-0.txt'
reading_bytes = source_path.read_bytes()
try:
    source_path.write_bytes(reading_bytes + b'\nChanged source for cache invalidation.\n')
    source_result = check_application_probe(request, planned['planId'], {}, cached_result=checked)
finally:
    source_path.write_bytes(reading_bytes)
save('source-drift', source_result)
assert source_result['status'] == 'rejected' and source_result['checkerAuthority'] == 'none'
rows.append({'case': 'source-drift', 'status': source_result['status'],
             'diagnostic': source_result['diagnostic']['code']})

toolchain_path = root / 'lean-toolchain'
toolchain_bytes = toolchain_path.read_bytes()
try:
    toolchain_path.write_bytes(b'leanprover/lean4:v9.9.9\n')
    environment_result = check_application_probe(request, planned['planId'], {}, cached_result=checked)
finally:
    toolchain_path.write_bytes(toolchain_bytes)
save('environment-drift', environment_result)
assert environment_result['status'] == 'rejected' and environment_result['checkerAuthority'] == 'none'
rows.append({'case': 'environment-drift', 'status': environment_result['status'],
             'diagnostic': environment_result['diagnostic']['code']})

expired_request = {**request, 'deadlineMonotonic': 0}
expired = check_application_probe(expired_request, planned['planId'], {}, cached_result=checked)
save('expired', expired)
assert expired['status'] == 'incomplete' and expired['checkerAuthority'] == 'none'
rows.append({'case': 'expired-deadline', 'status': expired['status'],
             'diagnostic': expired['diagnostic']['code']})

assert (root / 'lean-toolchain').read_bytes() == toolchain_bytes
assert source_path.read_bytes() == reading_bytes
summary = {'status': 'PASS', 'elapsedSeconds': time.monotonic() - started,
           'budgetSeconds': 1800, 'cases': rows,
           'scope': 'Exact local result reuse under same deadline after fresh source preparation; not a natural-language fidelity or manuscript-error claim.'}
save('RESULT', summary)
print(json.dumps(summary, sort_keys=True), flush=True)
