"""Role counts describe actual attempts; direct premise scope is never prose fidelity."""
import json
from types import SimpleNamespace

import pytest

from ladon import correspondence_check as checker
from ladon.correspondence_cli import _inspect
from ladon.proofir_v3_queries import query_v3_correspondence
from tests.test_correspondence_context import context_database
from tests.test_correspondence_query_coverage import OWNER, REF

KINDS = ['welltypedness', 'representation-transport', 'conditional-validity',
         'premise-supply', 'conclusion-transfer', 'premise-provider-validity']
ROLES = ['interpretation-typing', 'object-map-typing', 'conditional-replay',
         'premise-supply', 'conclusion-transfer', 'premise-provider-replay']


@pytest.mark.parametrize('attempts', [[], [0, 1], [2, 3, 4, 5], [0, 1, 2, 3, 4, 5]])
def test_public_checker_counts_only_attempted_roles(tmp_path, monkeypatch, attempts):
    obligations = [{'id': str(i), 'kind': kind} for i, kind in enumerate(KINDS)]
    (tmp_path / 'Proof.lean').write_text('')
    plan = {'obligations': obligations, 'interpretation': {},
            'slice': {'selection': {'sourceFile': 'Proof.lean'}}}
    checks = [{'obligation': str(i), 'goal': 'True', 'mode': 'prove',
               'status': 'unresolved'} for i in attempts]
    monkeypatch.setattr(checker, '_check_correspondence', lambda *_args, **_kwargs: {'checks': checks})
    result = checker.check_correspondence(plan, [], tmp_path)['executionAccounting']
    _assert_role_counts(result, attempts)
    assert result['premiseScope']['directObligationCount'] == 1
    assert result['premiseScope']['sourceAssumptions'] == 'not-assessed'


def _assert_role_counts(result, attempts):
    assert result['checkRoleProfile'] == 'correspondence-check-roles-v2'
    assert result['checkRoleCounts'] == {role: int(i in attempts) for i, role in enumerate(ROLES)}
    assert result['typingProbeCount'] == int(0 in attempts)
    assert result['objectMapTypingCount'] == int(1 in attempts)
    assert result['totalTypingCheckCount'] == sum(i < 2 for i in attempts)
    assert result['substantiveCheckCount'] == sum(i >= 2 for i in attempts)
    assert result['checkCount'] == len(attempts)


@pytest.mark.parametrize('count', [0, 2])
def test_inspection_counts_all_selected_premises_even_when_rows_are_truncated(count):
    db = context_database()
    for i in range(count):
        db.execute('INSERT INTO proofir_v3_correspondence_obligations VALUES(?,?,?,?,?,?,?)',
                   (OWNER, i, f'p{i}', 'premise-supply', 'True', 'supported', '/'))
    result = query_v3_correspondence(db, REF, limit=1)
    scope = result['premiseScope']
    assert scope['directObligationCount'] == count
    assert scope['boundary'] == ('no-direct-premise-obligations' if count == 0
                                 else 'selected-direct-premise-obligations')
    assert scope['sourceAssumptions'] == 'not-assessed'
    assert 'argument types' in scope['message']
    assert result['dimensions'] == {}
    assert result['authority'] == 'stored-evidence-only'


def test_plain_cli_inspection_also_explains_empty_boundary(tmp_path):
    path = tmp_path / 'plan.json'
    path.write_text(json.dumps({'planId': 'p', 'obligations': [], 'residuals': []}))
    result = _inspect(SimpleNamespace(plan=path, context_max_bytes=65536))
    assert result['premiseScope']['boundary'] == 'no-direct-premise-obligations'
    assert result['premiseScope']['sourceAssumptions'] == 'not-assessed'
    assert result['premiseScope']['directObligationCount'] == 0
