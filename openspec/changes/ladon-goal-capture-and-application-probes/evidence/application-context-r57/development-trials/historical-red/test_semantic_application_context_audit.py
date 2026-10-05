"""Falsification checks from independent application-observation review."""
from pathlib import Path
import sys

import pytest

from ladon.process_supervisor import ProcessResult
from ladon.proof_search_semantic_cli import render_semantic_candidates
from ladon.semantic_candidate_batch_worker import _materialize_batch_row
from ladon.semantic_candidate_worker import SemanticCandidateRequest, _environment_artifact, _rejected_artifacts

SINGLE = 'ladon-lean-semantic-v4/check-candidate'
BATCH = 'ladon-lean-semantic-v4/check-candidates'


def rejection(tmp_path, protocol):
    compiled = tmp_path / 'Main.olean'
    compiled.write_bytes(b'owned fixture bytes')
    helper = tmp_path / 'helper.lean'
    helper.write_text('owned helper identity')
    payload = {
        'protocol': protocol, 'failureStage': 'candidate-not-found', 'diagnostic': 'missing',
        'module': 'Main', 'leanVersion': '4.fixture', 'leanCommit': 'fixture',
        'executablePath': sys.executable, 'importedModules': [{'module': 'Main', 'oleanPath': str(compiled)}],
        'localContext': [], 'probe': {'name': 'probe', 'typeDisplay': 'True', 'typeStructural': 'True'},
        'requestId': 'owned-request', 'executionContextRef': 'unbound',
        'universePolicy': 'lean-level-mvar-succ-zero/v1',
    }
    process = ProcessResult((sys.executable, str(helper)), 0, 'same stdout bytes', '', 0.1)
    return SemanticCandidateRequest(tmp_path, 'Main', 'True', 'Main.missing'), helper, process, payload


def observation(artifact):
    return artifact['extensions']['ladon.process-observation/v1']


@pytest.mark.parametrize('protocol', [SINGLE, BATCH])
def test_rejected_v4_process_identity_binds_original_protocol(tmp_path, protocol):
    request, helper, process, payload = rejection(tmp_path, protocol)
    artifacts, _ = _rejected_artifacts(request, helper, process, payload, helper_identity='helper')
    row = observation(artifacts[1])
    assert row['semanticProtocol'] == protocol
    assert row['applicationObservationVersion'] == 4
    payload['protocol'] = 'ladon-lean-semantic-v3/check-candidate'
    old, _ = _rejected_artifacts(request, helper, process, payload, helper_identity='helper')
    assert artifacts[1]['payload']['checkRunId'] != old[1]['payload']['checkRunId']
    assert 'applicationObservationVersion' not in observation(old[1])


def test_rejected_v4_batch_preserves_wire_identity_without_inventing_application(tmp_path):
    request, helper, process, payload = rejection(tmp_path, BATCH)
    row = {'candidate': request.candidate, 'status': 'rejected', 'failureStage': 'candidate-not-found',
           'diagnostic': 'missing', 'applicationTerm': '', 'substitutions': [],
           'dischargedHypotheses': [], 'residualPremises': [], 'residualContexts': [], 'declarationBinders': []}
    environment = _environment_artifact(tmp_path, payload)
    result = _materialize_batch_row(request, helper, process, payload, environment, row)
    assert observation(result['artifacts'][1])['semanticProtocol'] == BATCH
    assert 'selectedDeclaration' not in result
    assert 'applicationObservationVersion' not in result


def test_direct_v4_text_is_bounded_and_discloses_clipping():
    huge = 'x' * 1_000_000
    check = {'applicationObservationVersion': 4, 'status': 'applicable-with-residuals',
             'selectedDeclaration': {'typeDisplay': huge, 'binders': [{'binderInfo': huge}] * 1000},
             'residualPremises': [{'typeDisplay': huge}] * 10,
             'residualContexts': [{'goalId': huge, 'localContext': []}] * 10,
             'checkRunRef': {'artifactRef': 'exact-check', 'localId': 'check:1'}}
    text = '\n'.join(render_semantic_candidates([{'name': 'Main.step', 'check': check}], include_projected_evidence=True))
    assert len(text) < 8000
    assert 'omission' in text and 'expand check evidence' in text
    assert 'remaining goal 0:' in text and 'exact-check' in text
