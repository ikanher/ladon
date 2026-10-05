from __future__ import annotations

import copy
import sqlite3

import pytest
from support.semantic_evidence import semantic_evidence
from test_stored_receipt_ownership import rebind_receipt

from ladon._semantic_observation_contract import validate_observation_semantics
from ladon.evidence_receipt_readers import stored_check_receipt
from ladon.proofir_sqlite_v3 import project_envelopes
from ladon.proofir_v3 import detached_content_id, validate_envelope_batch
from ladon.proofir_v3_queries import query_v3_theorem_evidence

CONTEXT = [{'name': 'x', 'type': 'Nat'}, {'name': 'h', 'type': 'x = x'}]


def rejected_context():
    artifacts, _, receipt = semantic_evidence(status='rejected', local_context=CONTEXT)
    context = {
        'kind': 'local-context', 'localId': 'local-context:observed',
        'searchShape': {'orderedLocals': copy.deepcopy(CONTEXT)},
    }
    check = artifacts[1]
    check['subjectRefs'].append(context)
    check['payload']['inputs']['subjectRefs'].append({
        'kind': context['kind'], 'localId': context['localId'],
    })
    check['artifactId'] = detached_content_id(check)
    validate_envelope_batch(artifacts)
    return artifacts, receipt


def read_receipt(artifacts, reader):
    if reader == 'stored':
        return stored_check_receipt(artifacts[1])
    if reader == 'live':
        receipt = artifacts[1]['extensions']['ladon.process-observation/v1']['evidenceReceipt']
        return validate_observation_semantics(
            {'failureStage': 'candidate-not-found'}, receipt, artifacts[1], 'Main.main',
            'rejected', request=None, scratch=False,
        )
    connection = sqlite3.connect(':memory:')
    try:
        project_envelopes(connection, artifacts)
        return query_v3_theorem_evidence(connection, 'Main.main', limit=10)
    finally:
        connection.close()


@pytest.mark.parametrize('reader', ['stored', 'live', 'dossier'])
@pytest.mark.parametrize('context', [
    [], [{'name': 'x', 'type': 'Bool'}, CONTEXT[1]], list(reversed(CONTEXT)),
    [*CONTEXT, {'name': 'extra', 'type': 'False'}],
])
def test_rehashed_rejected_receipt_cannot_change_owned_context(reader, context):
    artifacts, receipt = rejected_context()
    rebind_receipt(artifacts, subject={**receipt['subject'], 'localContext': context})
    with pytest.raises(ValueError, match='context'):
        read_receipt(artifacts, reader)


@pytest.mark.parametrize('reader', ['stored', 'live', 'dossier'])
@pytest.mark.parametrize('mutation', ['undeclared', 'unowned', 'ambiguous', 'malformed'])
def test_rejected_context_requires_unique_typed_input_owner(reader, mutation):
    artifacts, _ = rejected_context()
    check = artifacts[1]
    if mutation == 'undeclared':
        check['payload']['inputs']['subjectRefs'].pop()
    elif mutation == 'unowned':
        check['subjectRefs'].pop()
    elif mutation == 'ambiguous':
        duplicate = copy.deepcopy(check['subjectRefs'][-1])
        duplicate['localId'] += '-other'
        check['subjectRefs'].append(duplicate)
        check['payload']['inputs']['subjectRefs'].append({
            'kind': duplicate['kind'], 'localId': duplicate['localId'],
        })
    else:
        check['subjectRefs'][-1]['searchShape']['orderedLocals'] = 'invalid'
    check['artifactId'] = detached_content_id(check)
    with pytest.raises(ValueError, match='context'):
        read_receipt(artifacts, reader)


@pytest.mark.parametrize('reader', ['stored', 'live', 'dossier'])
def test_owned_rejected_context_roundtrips(reader):
    artifacts, original = rejected_context()
    before = copy.deepcopy(artifacts)
    read_receipt(artifacts, reader)
    assert artifacts == before
    assert stored_check_receipt(artifacts[1])['subject'] == original['subject']


def test_legacy_rejected_artifact_without_context_owner_remains_readable():
    artifacts, _, original = semantic_evidence(status='rejected', local_context=CONTEXT)
    assert stored_check_receipt(artifacts[1])['subject'] == original['subject']


def test_canonical_lean_context_display_fields_are_normalized():
    artifacts, original = rejected_context()
    context = artifacts[1]['subjectRefs'][-1]['searchShape']
    context['orderedLocals'] = [
        {'userName': row['name'], 'typeDisplay': row['type'], 'localId': str(index)}
        for index, row in enumerate(CONTEXT)
    ]
    artifacts[1]['artifactId'] = detached_content_id(artifacts[1])
    assert stored_check_receipt(artifacts[1])['subject'] == original['subject']
