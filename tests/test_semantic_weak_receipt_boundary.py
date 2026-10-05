"""Fail closed on malformed weak receipts while preserving raw audit scope."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from ladon.evidence_receipt import build_evidence_receipt
from ladon.evidence_receipt_readers import receipt_text_lines
from ladon.proof_search_cli import _render_text
from ladon.semantic_execution_binding import UNRECORDED_EXECUTION
from ladon.semantic_observation_closure import validate_semantic_observation_population
from ladon.semantic_result_delivery import deliver_semantic_result
from ladon.semantic_result_projection import SemanticProjectionError, project_semantic_result

WEAK_STATUSES = (
    'timeout', 'resource-limited', 'output-limited', 'memory-limited',
    'failed-checker', 'invalid-worker-output', 'unassessed',
)


def weak_payload(status, operation, receipt=None, *, population=1):
    check = {'status': status, 'candidate': 'Main.expected', 'artifacts': []}
    check['evidenceReceipt'] = receipt
    if operation == 'check-candidate':
        return {'schema': 'ladon-semantic-candidate-check-result-v1',
                'operation': operation, **check}
    rows = [{'name': f'Main.omitted{i}', 'check': {'status': 'unassessed'}}
            for i in range(population - 1)]
    rows.append({'name': 'Main.expected', 'check': check})
    return {'schema': 'ladon-verified-discovery-result-v1', 'operation': operation,
            'status': 'failed', 'candidates': rows,
            'request': {'module': 'Main', 'goal': 'True', 'localContext': [],
                        'maxCandidates': population},
            'coverage': {'shortlisted': population, 'truncated': False}}


def weak_receipt(binding):
    return build_evidence_receipt(
        subject={'module': 'Main', 'candidate': 'Main.expected', 'goal': 'True',
                 'localContext': []},
        execution_binding=binding, observation_state='failed', operation_outcome='failed',
        authority_basis='not-assessed', analysis_completeness='not-assessed',
        source_freshness='unknown', environment_match='unknown',
    )


@pytest.mark.parametrize('projection', ['llm', 'review'])
@pytest.mark.parametrize('operation', ['check-candidate', 'discover'])
@pytest.mark.parametrize('status', WEAK_STATUSES)
@pytest.mark.parametrize('malformed', [False, 0, 'receipt', [], ['receipt']])
def test_present_malformed_weak_receipt_is_rejected(projection, operation, status, malformed):
    payload = weak_payload(status, operation, malformed)
    with pytest.raises(SemanticProjectionError, match='invalid evidence receipt shape'):
        project_semantic_result(payload, projection=projection, registered_artifacts={})


@pytest.mark.parametrize('projection', ['llm', 'review'])
@pytest.mark.parametrize('status', WEAK_STATUSES)
def test_malformed_weak_receipt_in_omitted_population_is_rejected(projection, status):
    payload = weak_payload(status, 'discover', False, population=12)
    with pytest.raises(SemanticProjectionError, match='invalid evidence receipt shape'):
        project_semantic_result(payload, projection=projection, registered_artifacts={})


@pytest.mark.parametrize('malformed', [False, 0, 'receipt', [], ['receipt']])
def test_present_malformed_scratch_receipt_is_not_an_unattributed_failure(malformed):
    payload = weak_payload('failed-checker', 'check-candidate')
    payload['scratch'] = {'status': 'failed', 'evidenceReceipt': malformed}
    with pytest.raises(SemanticProjectionError, match='invalid evidence receipt shape'):
        validate_semantic_observation_population(payload, {})


@pytest.mark.parametrize('operation', ['check-candidate', 'discover'])
@pytest.mark.parametrize('status', WEAK_STATUSES)
@pytest.mark.parametrize('binding', ['none', 'ambient-observed', 'explicit-pinned'])
def test_weak_receipts_preserve_attempted_selection_without_checker_authority(operation, status, binding):
    receipt = weak_receipt(binding)
    payload = weak_payload(status, operation, receipt)
    before = copy.deepcopy(payload)
    result = project_semantic_result(payload, projection='llm', registered_artifacts={})
    row = result['candidate'] if operation == 'check-candidate' else result['candidates'][0]
    check = row['check']
    assert_weak_card(check, receipt)
    assert f'executionBinding={binding}' in _render_text(result)
    assert payload == before


def assert_weak_card(check, receipt):
    assert check['receiptIdentity'] == receipt['receiptIdentity']
    assert check['sourceReceiptIdentity'] == receipt['receiptIdentity']
    assert check['environmentRef'] is None and check['checkRunRef'] is None
    assert check['authority'] == {key: receipt[key] for key in check['authority']}
    assert check['authority']['authorityBasis'] == 'not-assessed'
    assert check['authority']['analysisCompleteness'] == 'not-assessed'
    assert check['authority']['observationState'] == 'failed'


@pytest.mark.parametrize('operation', ['check-candidate', 'discover'])
@pytest.mark.parametrize('missing', [True, False])
def test_absent_or_null_receipt_remains_supported(operation, missing):
    payload = weak_payload('unassessed', operation)
    check = payload if operation == 'check-candidate' else payload['candidates'][0]['check']
    if missing:
        check.pop('evidenceReceipt')
    result = project_semantic_result(payload, projection='review', registered_artifacts={})
    row = result['candidate'] if operation == 'check-candidate' else result['candidates'][0]
    assert row['check']['receiptIdentity'] is None
    assert row['check']['authority']['authorityBasis'] is None


def test_unattributed_scratch_failure_preserves_scratch_role():
    payload = weak_payload('failed-checker', 'check-candidate')
    payload['scratch'] = {'status': 'failed', 'evidenceReceipt': None}
    observations = validate_semantic_observation_population(payload, {})
    assert [row.scratch for row in observations] == [False, True]
    assert all(row.check_run_id is None for row in observations)


@pytest.mark.parametrize('operation', ['check-candidate', 'discover'])
@pytest.mark.parametrize('status', WEAK_STATUSES)
def test_absent_receipt_does_not_inherit_public_completeness(operation, status):
    payload = weak_payload(status, operation)
    check = payload if operation == 'check-candidate' else payload['candidates'][0]['check']
    check['analysisCompleteness'] = 'complete'
    result = project_semantic_result(payload, projection='llm', registered_artifacts={})
    row = result['candidate'] if operation == 'check-candidate' else result['candidates'][0]
    assert row['check']['authority']['analysisCompleteness'] is None


@pytest.mark.parametrize('operation', ['check-candidate', 'discover'])
def test_raw_audit_copy_does_not_validate_or_register_compact_evidence(tmp_path: Path, operation):
    payload = weak_payload('unassessed', operation, False)
    before = copy.deepcopy(payload)
    store = tmp_path / 'unused' / 'semantic.sqlite'
    result = deliver_semantic_result(payload, projection='audit', repo_root=tmp_path,
                                     registry_path=store, max_registry_bytes=1)
    assert result == before
    assert result is not payload
    assert not store.parent.exists()
    result['status'] = 'modified'
    assert payload == before


@pytest.mark.parametrize('operation', ['check-candidate', 'discover'])
def test_raw_audit_text_labels_source_receipts(operation):
    payload = weak_payload('failed-checker', operation, weak_receipt('explicit-pinned'))
    text = _render_text(deliver_semantic_result(payload, projection='audit', repo_root=Path('.')))
    assert 'audit source: original observations; execution binding is not revalidated in this view.' in text
    assert 'executionBinding=explicit-pinned' in text
    compact = project_semantic_result(payload, projection='llm', registered_artifacts={})
    assert 'audit source:' not in _render_text(compact)


def test_stored_text_keeps_finite_binding_limitation_and_exact_identity():
    receipt = weak_receipt('none')
    receipt = build_evidence_receipt(
        subject=receipt['subject'], execution_binding='none', observation_state='stored',
        operation_outcome='rejected', authority_basis='elaborator-check',
        analysis_completeness='complete', environment_match='exact',
        environment_ref='sha256:' + 'a' * 64, check_run_ref='check:' + 'b' * 64,
        limitations=[UNRECORDED_EXECUTION, 'other original limitation'],
    )
    lines = receipt_text_lines(receipt)
    assert lines[0] == f"evidenceReceipt: {receipt['receiptIdentity']}"
    assert f'execution binding limitation: {UNRECORDED_EXECUTION}' in lines
    assert 'other original limitation' not in '\n'.join(lines)
    assert not any('execution binding limitation:' in line for line in receipt_text_lines(weak_receipt('ambient-observed')))
