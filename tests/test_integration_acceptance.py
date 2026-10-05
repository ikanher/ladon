"""Integration cannot be promoted by partial, failed or mismatched gate records."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ladon.child_acceptance import content_digest
from ladon.integration_acceptance import _validate_prerequisites


@pytest.fixture
def prerequisite_case():
    root = Path(__file__).resolve().parents[1]
    inventory = json.loads((root / 'openspec/changes/ladon-authority-safe-verified-discovery-umbrella/children/integration-acceptance-inventory.json').read_text())
    scope = dict.fromkeys(('candidateIdentity', 'sourceTreeIdentity', 'wheelDigest',
                          'producerIdentity', 'environmentRef'), 'sha256:' + 'a' * 64)
    scope['workingDirectory'] = '/candidate'
    scope['candidateCommit'] = 'b' * 40
    receipt = {**scope, 'outputDirectory': '/evidence', 'integrationPrerequisiteArtifactRefs': []}
    evidence = {}
    log = b'gate completed\n'
    log_ref = content_digest(log)
    evidence[log_ref] = log
    records = []
    for gate in inventory['integrationPrerequisites']:
        argv = [part.format(candidateCommit=scope['candidateCommit'], outputDirectory='/evidence')
                for part in gate['argvTemplate']]
        records.append({**scope, 'gateId': gate['gateId'], 'argv': argv, 'exitCode': 0,
                        'status': 'passed', 'logArtifactRef': log_ref})
    return inventory, receipt, evidence, records


def _record(case):
    inventory, receipt, evidence, records = case
    receipt['integrationPrerequisiteArtifactRefs'] = []
    for row in records:
        data = json.dumps(row).encode()
        ref = content_digest(data)
        evidence[ref] = data
        receipt['integrationPrerequisiteArtifactRefs'].append(ref)
    return inventory, receipt, evidence


def _move_output(receipt, records, output):
    old = receipt['outputDirectory']
    receipt['outputDirectory'] = output
    for row in records:
        row['argv'] = [part.replace(old, output) for part in row['argv']]


def test_complete_prerequisites_are_candidate_bound(prerequisite_case):
    _validate_prerequisites(*_record(prerequisite_case))


@pytest.mark.parametrize('mutation', [
    'missing-gate', 'duplicate-gate', 'failed-exit', 'boolean-exit', 'failed-status',
    'wrong-candidate', 'wrong-cwd', 'wrong-wheel', 'changed-command', 'missing-log',
    'empty-log', 'unreviewed-extra-gate', 'new-record-field', 'output-inside-candidate',
    'relative-output', 'output-traversal', 'missing-inventory-gate',
])
def test_prerequisite_promotion_rejects_incomplete_or_mismatched_records(prerequisite_case, mutation):
    case = copy.deepcopy(prerequisite_case)
    inventory, receipt, evidence, records = case
    row = records[0]
    actions = {
        'missing-gate': lambda: records.pop(),
        'duplicate-gate': lambda: records.__setitem__(-1, copy.deepcopy(row)),
        'failed-exit': lambda: row.__setitem__('exitCode', 1),
        'boolean-exit': lambda: row.__setitem__('exitCode', False),
        'failed-status': lambda: row.__setitem__('status', 'blocked'),
        'wrong-candidate': lambda: row.__setitem__('candidateCommit', 'c' * 40),
        'wrong-cwd': lambda: row.__setitem__('workingDirectory', '/other-candidate'),
        'wrong-wheel': lambda: row.__setitem__('wheelDigest', 'sha256:' + 'd' * 64),
        'changed-command': lambda: row['argv'].__setitem__(-1, 'HEAD'),
        'missing-log': lambda: evidence.clear(),
        'empty-log': lambda: evidence.__setitem__(row['logArtifactRef'], b''),
        'unreviewed-extra-gate': lambda: row.__setitem__('gateId', 'optional-atlas'),
        'new-record-field': lambda: row.__setitem__('unlock', True),
        'output-inside-candidate': lambda: _move_output(receipt, records, '/candidate/logs'),
        'relative-output': lambda: _move_output(receipt, records, 'logs'),
        'output-traversal': lambda: _move_output(receipt, records, '/outside/../candidate/logs'),
        'missing-inventory-gate': lambda: (inventory['integrationPrerequisites'].pop(), records.pop()),
    }
    actions[mutation]()
    with pytest.raises(ValueError):
        _validate_prerequisites(*_record(case))
