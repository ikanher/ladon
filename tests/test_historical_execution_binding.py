from __future__ import annotations

import copy
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from support.semantic_evidence import semantic_evidence
from support.semantic_execution import with_execution_context
from test_stored_receipt_ownership import rebind_receipt

from ladon._semantic_observation_evidence import resolve_observation_evidence
from ladon.evidence_receipt import project_evidence_receipt, validate_evidence_receipt
from ladon.evidence_receipt_readers import stored_check_receipt
from ladon.proofir_sqlite_v3 import project_envelopes
from ladon.proofir_v3 import detached_content_id, validate_envelope_batch
from ladon.proofir_v3_queries import _check_runs, _observations, query_v3_theorem_evidence
from ladon.semantic_evidence_registry import SemanticEvidenceRegistry


def fixture(case='accepted', mode='explicit', label='main'):
    artifacts, _, _ = semantic_evidence(label, status=case, scratch=case in {'compiled', 'timeout'})
    return with_execution_context(artifacts, mode)


def read(artifacts, reader):
    if reader == 'stored':
        return stored_check_receipt(artifacts[1], environment_artifacts=artifacts[:1])
    if reader == 'live':
        return resolve_observation_evidence(
            {'artifacts': artifacts}, artifacts[1]['extensions']['ladon.process-observation/v1']['evidenceReceipt'],
            {row['artifactId']: row for row in artifacts},
        )
    connection = sqlite3.connect(':memory:')
    try:
        project_envelopes(connection, artifacts)
        if artifacts[1]['payload']['operation'] == 'scratch-compilation':
            subjects = [{
                'ownerArtifactId': artifacts[1]['artifactId'],
                'kind': 'candidate-application', 'localId': 'candidate-application:main',
            }]
            return {'checks': _check_runs(connection, subjects, 10),
                    'observations': _observations(connection, subjects, 10)}
        return query_v3_theorem_evidence(connection, 'Main.main', limit=10)
    finally:
        connection.close()


@pytest.mark.parametrize('reader', ['stored', 'live', 'dossier'])
@pytest.mark.parametrize('mode', ['explicit', 'ambient'])
@pytest.mark.parametrize('case', ['accepted', 'applicable-with-residuals', 'rejected', 'compiled', 'timeout'])
def test_rehashed_receipt_cannot_swap_recorded_execution_selection(reader, mode, case):
    artifacts, _ = fixture(case, mode)
    rebind_receipt(artifacts, execution_binding='ambient-observed' if mode == 'explicit' else 'explicit-pinned')
    validate_envelope_batch(artifacts)
    with pytest.raises(ValueError, match='execution'):
        read(artifacts, reader)


@pytest.mark.parametrize('reader', ['stored', 'live', 'dossier'])
@pytest.mark.parametrize('mode', ['explicit', 'ambient'])
def test_historical_context_roundtrip_uses_no_current_files(reader, mode):
    artifacts, source = fixture(mode=mode)
    before = copy.deepcopy(artifacts)
    read(artifacts, reader)
    projected = stored_check_receipt(artifacts[1], environment_artifacts=artifacts[:1])
    assert projected['executionBinding'] == source['executionBinding']
    assert projected['observationState'] == 'stored'
    assert artifacts == before


@pytest.mark.parametrize('reader', ['stored', 'live', 'dossier'])
@pytest.mark.parametrize('mode', ['explicit', 'ambient'])
def test_recorded_lean_identity_must_match_check_executable(reader, mode):
    artifacts, _ = fixture(mode=mode)
    artifacts[1]['payload']['checker']['executableDigest'] = 'sha256:' + 'f' * 64
    artifacts[1]['artifactId'] = detached_content_id(artifacts[1])
    with pytest.raises(ValueError, match='execution'):
        read(artifacts, reader)


@pytest.mark.parametrize('metadata', ['invalid', '{}', 'null', '{"selectionMode":"explicit","selectionMode":"ambient"}'])
@pytest.mark.parametrize('reader', ['stored', 'live', 'dossier'])
def test_present_invalid_execution_metadata_is_not_legacy_absence(metadata, reader):
    artifacts, _, _ = semantic_evidence()
    artifacts, _ = with_execution_context(artifacts, encoded_context=metadata)
    with pytest.raises(ValueError, match='execution'):
        read(artifacts, reader)


def test_missing_recorded_environment_weakens_only_read_binding():
    artifacts, source = fixture()
    before = copy.deepcopy(artifacts)
    projected = stored_check_receipt(artifacts[1])
    assert projected['executionBinding'] == 'none'
    assert projected['observationState'] == 'stored'
    for field in ['operationOutcome', 'authorityBasis', 'analysisCompleteness', 'sourceFreshness', 'environmentMatch', 'subject']:
        assert projected[field] == source[field]
    assert projected['limitations'] and artifacts == before
    assert project_evidence_receipt(projected, projection_kind='sqlite-row') == projected
    validate_evidence_receipt(projected)


def test_legacy_environment_without_context_does_not_establish_recorded_binding():
    artifacts, _, original = semantic_evidence()
    projected = stored_check_receipt(artifacts[1], environment_artifacts=artifacts[:1])
    assert projected['executionBinding'] == 'none'
    assert artifacts[1]['extensions']['ladon.process-observation/v1']['evidenceReceipt'] == original


@pytest.mark.parametrize('field', ['leanIdentity', 'lakeIdentity', 'pinDigest', 'sourceTreeIdentity', 'contextIdentity', 'pinContent', 'selectionMode'])
@pytest.mark.parametrize('value', [None, [], 'invalid'])
def test_incomplete_or_invalid_captured_context_cannot_bind_execution(field, value):
    artifacts, _ = fixture()
    context = json.loads(artifacts[0]['payload']['options']['toolchainContext'])
    context[field] = value
    artifacts, _ = with_execution_context(artifacts, context=context)
    with pytest.raises(ValueError, match='execution'):
        read(artifacts, 'stored')


def test_duplicate_key_in_otherwise_complete_context_is_rejected():
    artifacts, _ = fixture()
    encoded = artifacts[0]['payload']['options']['toolchainContext']
    artifacts, _ = with_execution_context(artifacts, encoded_context=encoded[:-1] + ', "selectionMode":"explicit"}')
    with pytest.raises(ValueError, match='execution'):
        read(artifacts, 'stored')


def test_same_environment_identity_does_not_select_another_content_owner():
    artifacts, _ = fixture()
    other = copy.deepcopy(artifacts[0])
    other['producer']['name'] = 'another-producer'
    other['artifactId'] = detached_content_id(other)
    with pytest.raises(ValueError, match='execution'):
        stored_check_receipt(artifacts[1], environment_artifacts=[other])


def test_ambiguous_declared_environment_inputs_fail_closed():
    artifacts, _ = fixture()
    other = copy.deepcopy(artifacts[0])
    other['producer']['name'] = 'another-producer'
    other['artifactId'] = detached_content_id(other)
    artifacts[1]['payload']['inputs']['artifactRefs'].append(other['artifactId'])
    artifacts[1]['artifactId'] = detached_content_id(artifacts[1])
    with pytest.raises(ValueError, match='execution'):
        stored_check_receipt(artifacts[1], environment_artifacts=[artifacts[0], other])


def test_environment_without_typed_context_is_explicitly_unbound():
    artifacts, _ = fixture()
    artifacts, _ = with_execution_context(artifacts, encoded_context='ambient-unbound')
    assert read(artifacts, 'stored')['executionBinding'] == 'none'


def test_dossier_environment_lookup_is_bounded_and_set_oriented():
    connection = sqlite3.connect(':memory:')
    artifacts = []
    for index in range(20):
        rows, _ = fixture(label='main-' + str(index))
        rows[1]['subjectRefs'][0]['searchShape']['declarationName'] = 'Main.shared'
        rows[1]['artifactId'] = detached_content_id(rows[1])
        artifacts.extend(rows)
    project_envelopes(connection, artifacts)
    before = connection.execute('SELECT canonical_json FROM proofir_v3_artifacts ORDER BY content_artifact_id').fetchall()
    traces = []
    connection.set_trace_callback(traces.append)
    dossier = query_v3_theorem_evidence(connection, 'Main.shared', limit=5)
    assert len(dossier['checks']['rows']) == 5
    assert all(row['evidenceReceipt']['executionBinding'] == 'explicit-pinned' for row in dossier['checks']['rows'])
    assert len([query for query in traces if query.lstrip().upper().startswith('SELECT')]) <= 12
    assert connection.execute('SELECT canonical_json FROM proofir_v3_artifacts ORDER BY content_artifact_id').fetchall() == before
    connection.close()


@pytest.mark.parametrize('mode', ['explicit', 'ambient'])
def test_legacy_direct_executable_context_preserves_recorded_binding(mode):
    artifacts, _ = fixture(mode=mode)
    artifacts[0]['payload']['options'].pop('observedLeanExecutableDigest')
    artifacts, source = with_execution_context(artifacts, mode, observed_identity=False)
    assert read(artifacts, 'stored')['executionBinding'] == source['executionBinding']


@pytest.mark.parametrize('record_worker', [True, False])
def test_ambient_launcher_and_observed_worker_identities_remain_distinct(record_worker):
    artifacts, _ = fixture(mode='ambient')
    context = json.loads(artifacts[0]['payload']['options']['toolchainContext'])
    context['leanIdentity'] = context['lakeIdentity']
    artifacts[0]['payload']['options'].pop('observedLeanExecutableDigest')
    artifacts, _ = with_execution_context(artifacts, 'ambient', context=context, observed_identity=record_worker)
    expected = 'ambient-observed' if record_worker else 'none'
    assert read(artifacts, 'stored')['executionBinding'] == expected


def test_explicit_selection_cannot_relabel_launcher_as_exact_worker():
    artifacts, _ = fixture()
    context = json.loads(artifacts[0]['payload']['options']['toolchainContext'])
    context['leanIdentity'] = context['lakeIdentity']
    artifacts, _ = with_execution_context(artifacts, context=context)
    with pytest.raises(ValueError, match='execution'):
        read(artifacts, 'stored')


def test_unbound_context_does_not_hide_a_recorded_worker_identity_contradiction():
    artifacts, _ = fixture()
    artifacts, _ = with_execution_context(artifacts, encoded_context='ambient-unbound')
    artifacts[1]['payload']['checker']['executableDigest'] = 'sha256:' + 'f' * 64
    artifacts[1]['artifactId'] = detached_content_id(artifacts[1])
    with pytest.raises(ValueError, match='execution'):
        read(artifacts, 'stored')


@pytest.mark.parametrize('case', ['compiled', 'timeout'])
def test_ambient_scratch_records_selected_toolchain_not_parent_worker(case):
    artifacts, _ = fixture(case, mode='ambient')
    artifacts[0]['payload']['options']['observedLeanExecutableDigest'] = 'sha256:' + 'f' * 64
    artifacts, source = with_execution_context(artifacts, 'ambient', observed_identity=False)
    projected = read(artifacts, 'stored')
    assert projected['executionBinding'] == source['executionBinding'] == 'ambient-observed'
    assert projected['authorityBasis'] == 'process-observation'
    assert projected['analysisCompleteness'] == 'partial'


def test_ambient_partial_batch_records_selected_context_without_terminal_authority():
    artifacts, _, _ = semantic_evidence(authority_basis='process-observation', completeness='partial')
    application = next(row for row in artifacts[1]['subjectRefs'] if row['kind'] == 'candidate-application')
    application['searchShape']['processOutcome'] = 'timeout'
    artifacts[1]['payload']['results'][0]['diagnostics'] = [{
        'stage': 'batch-process', 'code': 'timeout', 'pointer': '/process',
        'message': 'interrupted batch', 'order': 0,
    }]
    artifacts, _ = with_execution_context(artifacts, 'ambient')
    artifacts[0]['payload']['options']['observedLeanExecutableDigest'] = 'sha256:' + 'f' * 64
    artifacts, _ = with_execution_context(artifacts, 'ambient', observed_identity=False)
    projected = read(artifacts, 'stored')
    assert projected['executionBinding'] == 'ambient-observed'
    assert projected['authorityBasis'] == 'process-observation'
    assert projected['analysisCompleteness'] == 'partial'


@pytest.mark.parametrize('kind', ['semantic-artifact', 'semantic-check'])
def test_installed_expansion_rejects_rehashed_execution_binding(tmp_path, kind):
    artifacts, _ = fixture(mode='ambient')
    rebind_receipt(artifacts, execution_binding='explicit-pinned')
    store = tmp_path / 'evidence.sqlite'
    SemanticEvidenceRegistry(store).register_bundle(artifacts)
    console = os.environ.get('LADON_CONSOLE', str(Path(sys.executable).with_name('ladon')))
    command = [console, 'proof-search', 'evidence', kind, artifacts[1]['artifactId'],
               '--repo-root', str(tmp_path), '--evidence-store', str(store), '--format', 'json']
    if kind == 'semantic-check':
        command += ['--local-id', artifacts[1]['payload']['checkRunId']]
    result = subprocess.run(command, capture_output=True, text=True, cwd=tmp_path, timeout=10, check=False)
    assert result.returncode == 1 and result.stdout == ''
    assert json.loads(result.stderr)['diagnostic']['code'] == 'invalid-stored-evidence-receipt'
