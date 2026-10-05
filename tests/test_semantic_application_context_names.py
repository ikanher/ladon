"""Observed local identities remain distinct when displayed names repeat."""
import json
from pathlib import Path

import pytest
from test_semantic_application_context_v4 import frame, local
from test_semantic_application_context_v4_boundaries import V4, batch_frames

from ladon.semantic_candidate_batch_worker import _parse_batch_worker_payload
from ladon.semantic_candidate_worker import (
    SemanticCandidateRequest,
    _parse_worker_payload,
    _validate_rejected_worker_payload,
)


def locals_():
    return [local('_', 'local:0'), local('_', 'local:1')]


@pytest.mark.parametrize('protocol,valid', [('ladon-lean-semantic-v4/check-candidate', True),
                                          ('ladon-lean-semantic-v3/check-candidate', False)])
def test_repeated_display_names_dispatch_by_protocol(protocol, valid):
    request = SemanticCandidateRequest(Path('.'), 'Main', 'True', 'Main.step')
    payload = frame(request)
    payload.update(protocol=protocol, localContext=locals_())
    if not valid:
        del payload['residualContexts'], payload['declarationBinders']
        with pytest.raises(ValueError, match='duplicate local identity'):
            _parse_worker_payload('LADON_FRAME ' + json.dumps(payload), request, 'req-v4')
    else:
        parsed = _parse_worker_payload('LADON_FRAME ' + json.dumps(payload), request, 'req-v4')
        assert parsed['localContext'] == locals_()


def test_v4_repeated_local_id_is_still_rejected():
    request = SemanticCandidateRequest(Path('.'), 'Main', 'True', 'Main.step')
    payload = frame(request)
    payload['localContext'] = [local('_', 'local:0'), local('h', 'local:0')]
    with pytest.raises(ValueError, match='duplicate local identity'):
        _parse_worker_payload('LADON_FRAME ' + json.dumps(payload), request, 'req-v4')


def test_v4_batch_accepts_distinct_anonymous_locals():
    request = SemanticCandidateRequest(Path('.'), 'Main', 'True', 'Main.step')
    stream = batch_frames(request, header_protocol=V4, row_protocol=V4, summary_protocol=V4)
    rows = [json.loads(line.removeprefix('LADON_FRAME ')) for line in stream.splitlines()]
    rows[0]['localContext'] = locals_()
    stream = '\n'.join('LADON_FRAME ' + json.dumps(row) for row in rows)
    payload, terminal = _parse_batch_worker_payload(stream, request, 'req-mixed', [request.candidate])
    assert terminal and payload['localContext'] == locals_()


@pytest.mark.parametrize('protocol,valid', [('ladon-lean-semantic-v4/check-candidate', True),
                                          ('ladon-lean-semantic-v3/check-candidate', False)])
def test_v4_rejection_retains_distinct_anonymous_locals(protocol, valid):
    request = SemanticCandidateRequest(Path('.'), 'Main', 'True', 'Main.step')
    payload = frame(request)
    for field in ['candidate', 'applicationTerm', 'substitutions', 'dischargedHypotheses', 'residualPremises', 'residualContexts', 'declarationBinders']:
        del payload[field]
    payload.update(protocol=protocol, localContext=locals_(), candidateName=request.candidate,
                   status='rejected', failureStage='application-rejected', diagnostic='rejected')
    if valid:
        _validate_rejected_worker_payload(payload, request, 'req-v4')
    else:
        with pytest.raises(ValueError, match='duplicate local identity'):
            _validate_rejected_worker_payload(payload, request, 'req-v4')
