from __future__ import annotations

import copy
import json

import pytest
from support.semantic_evidence import digest, semantic_evidence
from support.semantic_execution import with_execution_context
from test_stored_receipt_ownership import rebind_receipt

from ladon.evidence_receipt import project_evidence_receipt, validate_evidence_receipt
from ladon.evidence_receipt_readers import stored_check_receipt
from ladon.proof_search_cli import _render_text
from ladon.proofir_v3 import detached_content_id, validate_envelope_batch
from ladon.semantic_execution_binding import UNRECORDED_EXECUTION
from ladon.semantic_projection_fit import _minimal_projection
from ladon.semantic_result_projection import project_semantic_result


def check_fixture(status='accepted', context='legacy', label='main'):
    artifacts, _, source = semantic_evidence(label, status=status)
    if context != 'legacy':
        mode = 'explicit' if context == 'explicit' else 'ambient'
        artifacts, source = with_execution_context(artifacts, mode)
        if context == 'unbound':
            artifacts, source = with_execution_context(artifacts, mode, encoded_context='ambient-unbound')
        elif context.startswith('launcher'):
            recorded = json.loads(artifacts[0]['payload']['options']['toolchainContext'])
            recorded['leanIdentity'] = digest('elan-launcher')
            artifacts[0]['payload']['options'].pop('observedLeanExecutableDigest', None)
            artifacts, source = with_execution_context(
                artifacts, mode, context=recorded, observed_identity=context == 'launcher-recorded',
            )
    check = public_check(artifacts, source, status)
    return check, {row['artifactId']: row for row in artifacts}


def public_check(artifacts, source, status):
    application = next((r['searchShape'] for r in artifacts[1]['subjectRefs']
                        if r['kind'] == 'candidate-application'), {})
    return {
        'status': status, 'evidenceReceipt': source, 'artifacts': artifacts,
        'environmentRef': source['environmentRef'], 'checkRunRef': source['checkRunRef'],
        'applicationTerm': application.get('applicationTerm'),
        'substitutions': application.get('substitutions', []),
        'residualPremises': application.get('residualPremises', []),
        'dischargedHypotheses': application.get('dischargedHypotheses', []),
        'failureStage': 'candidate-not-found' if status == 'rejected' else None,
    }


def payload_for(check, operation):
    if operation == 'check-candidate':
        return {'schema': 'ladon-semantic-candidate-check-result-v1', 'operation': operation, **check}
    return {
        'schema': 'ladon-verified-discovery-result-v1', 'operation': operation, 'status': 'available',
        'request': {'module': 'Main', 'goal': 'True', 'localContext': [], 'maxCandidates': 1},
        'candidates': [{'name': check['evidenceReceipt']['subject']['candidate'], 'check': check}],
        'coverage': {'shortlisted': 1, 'truncated': False},
    }


def card_for(view, operation):
    return view['candidate']['check'] if operation == 'check-candidate' else view['candidates'][0]['check']


@pytest.mark.parametrize('status', ['accepted', 'applicable-with-residuals', 'rejected'])
@pytest.mark.parametrize('context,recorded', [
    ('legacy', False), ('unbound', False), ('launcher-unknown', False),
    ('explicit', True), ('ambient', True), ('launcher-recorded', True),
])
@pytest.mark.parametrize('projection', ['llm', 'review'])
@pytest.mark.parametrize('operation', ['check-candidate', 'discover'])
def test_compact_binding_matches_independent_historical_evidence(status, context, recorded, projection, operation):
    check, registry = check_fixture(status, context)
    payload = payload_for(check, operation)
    before = copy.deepcopy((payload, registry))
    projected = project_semantic_result(payload, projection=projection, registered_artifacts=registry)
    kind = 'json-renderer' if operation == 'check-candidate' else 'aggregate'
    source = check['evidenceReceipt']
    expected = stored_check_receipt(check['artifacts'][1], projection_kind=kind,
                                    environment_artifacts=check['artifacts'][:1])
    validate_evidence_receipt(expected)
    card = card_for(projected, operation)
    assert card['authority'] == {field: expected[field] for field in card['authority']}
    assert card['receiptIdentity'] == expected['receiptIdentity']
    assert card['sourceReceiptIdentity'] == source['receiptIdentity']
    assert card['executionBindingLimitation'] == (None if recorded else UNRECORDED_EXECUTION)
    assert (payload, registry) == before
    text = _render_text(projected)
    assert f"executionBinding={expected['executionBinding']}" in text
    assert expected['receiptIdentity'] in text and source['receiptIdentity'] in text
    assert (UNRECORDED_EXECUTION in text) == (not recorded)


@pytest.mark.parametrize('projection', ['llm', 'review'])
@pytest.mark.parametrize('operation', ['check-candidate', 'discover'])
@pytest.mark.parametrize('scratch_status', ['compiled', 'failed', 'timeout', 'output-limited', 'memory-limited', 'process-failed'])
def test_legacy_scratch_binding_and_reason_survive_minimal_projection(projection, operation, scratch_status):
    check, registry = check_fixture()
    artifacts, scratch_registry, source = semantic_evidence('scratch', candidate='Main.main', status=scratch_status, scratch=True)
    registry.update(scratch_registry)
    check['scratch'] = {
        'status': scratch_status, 'evidenceReceipt': source, 'artifacts': artifacts,
        'environmentRef': source['environmentRef'], 'checkRunRef': source['checkRunRef'],
        'sourceDigest': digest('scratch-source:scratch'), 'applicationTerm': 'Main.main',
        'parentCheckRunRef': check['evidenceReceipt']['checkRunRef'],
    }
    payload = payload_for(check, operation)
    before = copy.deepcopy((payload, registry))
    projected = project_semantic_result(payload, projection=projection, registered_artifacts=registry)
    kind = 'json-renderer' if operation == 'check-candidate' else 'aggregate'
    expected = stored_check_receipt(artifacts[1], projection_kind=kind, environment_artifacts=artifacts[:1])
    for view in [projected, _minimal_projection(projected)]:
        card = card_for(view, operation)
        assert_legacy_scratch(card, source, expected)
        assert UNRECORDED_EXECUTION in _render_text(view)
    assert (payload, registry) == before


def assert_legacy_scratch(card, source, expected):
    scratch = card['scratch']
    assert card['authority']['executionBinding'] == scratch['authority']['executionBinding'] == 'none'
    assert card['executionBindingLimitation'] == scratch['executionBindingLimitation'] == UNRECORDED_EXECUTION
    assert scratch['authority']['authorityBasis'] == 'process-observation'
    assert scratch['authority']['analysisCompleteness'] == 'partial'
    assert scratch['authority']['operationOutcome'] == source['operationOutcome']
    assert scratch['receiptIdentity'] == expected['receiptIdentity']
    assert scratch['sourceReceiptIdentity'] == source['receiptIdentity']


@pytest.mark.parametrize('projection', ['llm', 'review'])
@pytest.mark.parametrize('operation', ['check-candidate', 'discover'])
@pytest.mark.parametrize('recorded', [False, True])
def test_provisional_binding_preserves_partial_process_scope(projection, operation, recorded):
    artifacts, _, source = semantic_evidence(authority_basis='process-observation', completeness='partial')
    artifact = artifacts[1]
    application = next(r for r in artifact['subjectRefs'] if r['kind'] == 'candidate-application')
    application['searchShape']['processOutcome'] = 'timeout'
    artifact['payload']['results'][0]['diagnostics'] = [{
        'stage': 'batch-process', 'code': 'timeout', 'pointer': '/process',
        'message': 'partial batch', 'order': 0,
    }]
    artifact['artifactId'] = detached_content_id(artifact)
    if recorded:
        artifacts, source = with_execution_context(artifacts)
    check = public_check(artifacts, source, 'provisional-observation')
    check.update(observedStatus='accepted', batchTerminal=False, processOutcome='timeout')
    payload = payload_for(check, operation)
    if operation == 'discover':
        payload['status'] = 'partial'
    registry = {r['artifactId']: r for r in artifacts}
    projected = project_semantic_result(payload, projection=projection, registered_artifacts=registry)
    card = card_for(projected, operation)
    assert card['authority']['executionBinding'] == ('explicit-pinned' if recorded else 'none')
    assert card['authority']['authorityBasis'] == 'process-observation'
    assert card['authority']['analysisCompleteness'] == 'partial'
    assert card['authority']['operationOutcome'] == 'accepted'


@pytest.mark.parametrize('projection', ['llm', 'review'])
def test_compact_projection_rejects_a_rehashed_selection_swap(projection):
    check, registry = check_fixture(context='ambient')
    rebind_receipt(check['artifacts'], execution_binding='explicit-pinned')
    check['evidenceReceipt'] = check['artifacts'][1]['extensions']['ladon.process-observation/v1']['evidenceReceipt']
    registry = {r['artifactId']: r for r in check['artifacts']}
    with pytest.raises(ValueError, match='execution'):
        project_semantic_result(payload_for(check, 'check-candidate'), projection=projection, registered_artifacts=registry)


def test_legacy_binding_cannot_be_restored_by_a_later_renderer():
    check, _ = check_fixture()
    projected = stored_check_receipt(check['artifacts'][1], projection_kind='aggregate', environment_artifacts=check['artifacts'][:1])
    for kind in ['json-renderer', 'text-renderer', 'aggregate', 'dossier', 'sqlite-row']:
        child = project_evidence_receipt(projected, projection_kind=kind)
        assert child['executionBinding'] == 'none'
        assert UNRECORDED_EXECUTION in child['limitations']
        with pytest.raises(ValueError):
            project_evidence_receipt(child, projection_kind=kind, execution_binding='explicit-pinned')


def test_audit_projection_keeps_canonical_legacy_bytes():
    check, registry = check_fixture()
    payload = payload_for(check, 'check-candidate')
    before = copy.deepcopy(payload)
    assert project_semantic_result(payload, projection='audit', registered_artifacts=registry) == before
    assert payload == before


def test_full_population_still_rejects_corrupt_omitted_metadata():
    checks, registry = [], {}
    for index in range(17):
        check, entries = check_fixture(context='explicit', label=f'candidate{index}')
        checks.append(check)
        registry.update(entries)
    artifacts, receipt = with_execution_context(copy.deepcopy(checks[-1]['artifacts']), encoded_context='invalid')
    validate_envelope_batch(artifacts)
    checks[-1] = public_check(artifacts, receipt, 'accepted')
    registry.update({r['artifactId']: r for r in artifacts})
    payload = payload_for(checks[0], 'discover')
    payload['request']['maxCandidates'] = 17
    payload['coverage']['shortlisted'] = 17
    payload['candidates'] = [{'name': c['evidenceReceipt']['subject']['candidate'], 'check': c} for c in checks]
    with pytest.raises(ValueError, match='execution context'):
        project_semantic_result(payload, projection='llm', registered_artifacts=registry)
