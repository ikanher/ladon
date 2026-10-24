"""Retain a timed, source-paired three-step localization development control."""
import argparse
import hashlib
import json
import shutil
from dataclasses import asdict
from pathlib import Path
from time import monotonic

from test_proof_contract_planned_source import FIXTURE, request_for
from test_proof_contract_source_obligations import _complete

from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.proof_contract_source_obligations import instantiate_planned_source_leaf_requirement


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, default=str) + '\n')


def run(output):
    started = monotonic()
    deadline = started + 1800
    output.mkdir(parents=True, exist_ok=False)
    root = output / 'repo'
    root.mkdir()
    for name in ('ThreeSteps.lean', 'lean-toolchain'):
        shutil.copyfile(FIXTURE / name, root / name)
    original = (root / 'ThreeSteps.lean').read_bytes()
    snapshots = {}
    for name in ('firstBound', 'secondBound', 'thirdBound', 'alternateBound', 'endpoint'):
        snapshot = produce_formal_snapshot(root, 'ThreeSteps.lean', 'ThreeSteps',
                                          'ThreeSteps.' + name, timeout_seconds=30)
        write_json(output / (name + '-snapshot.json'), snapshot)
        if snapshot['status'] != 'extracted':
            raise RuntimeError('Source observation unavailable: ' + name)
        snapshots[name] = snapshot
    request = request_for((root, snapshots))
    request['deadlineMonotonic'] = deadline
    write_json(output / 'plan-request.json', asdict(request['planRequest']))
    write_json(output / 'plan-result.json', request['planResult'])
    first = instantiate_planned_source_leaf_requirement(request)
    write_json(output / 'middle-construction.json', first)
    if first['status'] != 'candidate-goal':
        raise RuntimeError('Intermediate source goal unavailable: ' + str(first['diagnostic']))
    wrong = _complete(request, first['capture'], 'by exact ThreeSteps.secondBound')
    write_json(output / 'middle-wrong-term.json', wrong)
    if wrong['status'] != 'rejected':
        raise RuntimeError('Wrong middle provider term was not rejected')
    alternate = request_for((root, snapshots), 'alternate', 'alternateBound')
    alternate['deadlineMonotonic'] = deadline
    alternative_goal = instantiate_planned_source_leaf_requirement(alternate)
    write_json(output / 'alternate-construction.json', alternative_goal)
    if alternative_goal['status'] != 'candidate-goal':
        raise RuntimeError('Alternate source goal unavailable')
    completed = _complete(alternate, alternative_goal['capture'], 'by exact ThreeSteps.alternateBound')
    write_json(output / 'alternate-completion.json', completed)
    if (completed['status'] != 'completed' or completed['replay']['status'] != 'accepted'
            or completed['trust']['accepted'] is not True):
        raise RuntimeError('Alternate kernel replay was not accepted')
    repeat = instantiate_planned_source_leaf_requirement(request)
    write_json(output / 'middle-repeat.json', repeat)
    for key in ('requestDigest', 'prefixDigest', 'generatedSourceDigest', 'selectedRequirement'):
        if first[key] != repeat[key]:
            raise RuntimeError('Repeated construction changed ' + key)
    if first['capture']['captureId'] != repeat['capture']['captureId']:
        raise RuntimeError('Repeated capture identity changed')
    if (root / 'ThreeSteps.lean').read_bytes() != original:
        raise RuntimeError('Original source changed')
    elapsed = monotonic() - started
    if elapsed >= 1800:
        raise RuntimeError('Thirty-minute localization execution budget expired')
    plan = request['planResult']
    route = plan['routeComparisons'][request['routeIndex']]
    summary = {'scope': 'constructed-source-paired-three-step-development-control',
        'sourceFidelity': 'attributed-unreviewed', 'wholeMethodAuthority': 'none',
        'mathematicalFalsity': 'not-established', 'elapsedSeconds': elapsed,
        'budgetSeconds': 1800, 'preparationIncluded': 'five fresh source observations and public planning',
        'implementationTimeIncluded': False, 'sourceUnchanged': True,
        'sourceDigest': 'sha256:' + hashlib.sha256(original).hexdigest(),
        'describedStepCount': len(route['stepRefs']),
        'retainedRequirementCount': len(route['backwardRequirements']),
        'selectedIdentity': request['selectedIdentity'],
        'requiredOffset': first['selectedRequirement']['contractRecord']['features']['regularity']['offset'],
        'providerOffset': snapshots['secondBound']['contract']['features']['regularity']['offset'],
        'wrongTermStatus': wrong['status'], 'alternativeReplay': completed['replay']['status'],
        'alternativeTrustAccepted': completed['trust']['accepted'],
        'repeatBindingsIdentical': True, 'limits': request['limits'],
        'requestDigest': first['requestDigest'], 'captureId': first['capture']['captureId']}
    write_json(output / 'SUMMARY.json', summary)
    print(json.dumps(summary, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    run(parser.parse_args().output.resolve())
