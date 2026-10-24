"""Native obligation analyses bind whole demand graphs to exact input owners."""
import copy
import importlib
import sqlite3
from dataclasses import replace

import pytest
from test_proof_contract_obligation_bundles import _request
from test_proof_contract_propagation_native import remade

from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database
from ladon.proofir_v3 import validate_envelope_batch


def _artifact(request):
    module = importlib.import_module('ladon.proof_contract_obligation_artifacts')
    return module.obligations_artifact(request, analysis_id='analysis:bundles')


def _batch(request, artifact):
    return [request.derivation_artifact, *request.contract_artifacts, artifact]


def test_native_bundle_replays_full_request_and_exact_source_owners():
    _, request = _request()
    artifact = _artifact(request)
    assert artifact['payload']['stage'] == 'obligations'
    assert artifact['payload']['result']['schema'] == 'ladon-contract-obligation-planner-v2'
    assert artifact['payload']['request']['desiredReadingIdentity'] == request.desired_reading_identity
    assert artifact['payload']['derivationGoalRef']['artifactRef'] == request.derivation_artifact['artifactId']
    validate_envelope_batch(_batch(request, artifact))
    assert _artifact(request) == artifact


@pytest.mark.parametrize('mutation', ['edge', 'reading', 'authority', 'pending'])
def test_rehashed_native_bundle_forgery_is_rejected(mutation):
    _, request = _request()
    artifact = _artifact(request)
    payload = copy.deepcopy(artifact['payload'])
    if mutation == 'reading':
        payload['request']['desiredReadingIdentity']['readingId'] = 'reading:changed'
    elif mutation == 'authority':
        payload['result']['checkerAuthority'] = 'kernel-checked'
    elif mutation == 'pending':
        payload['result']['coverage']['pendingBranches'].append({'reason': 'invented'})
    else:
        route = next(r for r in payload['result']['routeComparisons'] if r['describedRoute'])
        bundle = route['obligationBundle']
        root = next(d for d in bundle['demands'] if d['demandId'] == bundle['rootDemandId'])
        root['alternatives'][0]['requirements'][0]['childDemandId'] = 'sha256:' + '0'*64
    with pytest.raises((ValueError, TypeError)):
        validate_envelope_batch(_batch(request, remade(artifact, payload)))


def test_native_bundle_cannot_reuse_same_goal_label_under_different_owner():
    _, request = _request()
    artifact = _artifact(request)
    graph = copy.deepcopy(request.derivation_artifact)
    graph['producer']['name'] += '-different'
    from ladon.proofir_v3 import detached_content_id

    graph['artifactId'] = detached_content_id(graph)
    with pytest.raises(ValueError):
        validate_envelope_batch([graph, *request.contract_artifacts, artifact])


@pytest.mark.parametrize('deadline', ['2000-01-01T00:00:00Z', '2100-01-01T00:00:00Z'])
def test_native_deadline_replay_never_reads_current_clock(monkeypatch, deadline):
    _, request = _request()
    request = replace(request, bounds={'deadlineUtc': deadline})
    artifact = _artifact(request)
    import ladon._contract_propagation_deadline as clock

    def forbidden():
        raise AssertionError('historical inspection must not observe current time')

    monkeypatch.setattr(clock, '_utc_now', forbidden)
    validate_envelope_batch(_batch(request, artifact))
    assert artifact['payload']['result']['deadlineObservation']


def test_native_projection_preserves_stage_result_and_derivation_index():
    _, request = _request()
    artifact = _artifact(request)
    connection = sqlite3.connect(':memory:')
    project_envelopes(connection, _batch(request, artifact))
    validate_v3_database(connection)
    row = connection.execute('SELECT stage FROM proofir_v3_contract_analyses').fetchone()
    assert row == ('obligations',)
    owner = connection.execute('SELECT derivation_owner,goal_local_id '
                               'FROM proofir_v3_contract_analysis_derivations').fetchone()
    assert owner == (request.derivation_artifact['artifactId'], request.goal_ref['localId'])
    indexes = {r[1] for r in connection.execute(
        'PRAGMA index_list(proofir_v3_contract_analysis_derivations)')}
    assert 'idx_v3_contract_analysis_derivation' in indexes
