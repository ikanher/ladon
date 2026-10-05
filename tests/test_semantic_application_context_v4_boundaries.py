"""Falsify cross-version batch and incomplete canonical observation promotion."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from ladon.semantic_candidate_batch_worker import _batch_probe_name, _parse_batch_worker_payload
from ladon.semantic_candidate_worker import (
    SemanticCandidateRequest,
    _application_subject,
    _goal_request_digest,
    _subject,
)
from ladon.semantic_stored_receipt import _stored_check

V3 = "ladon-lean-semantic-v3/check-candidates"
V4 = "ladon-lean-semantic-v4/check-candidates"


def batch_frames(request, *, header_protocol=V3, row_protocol=V3, summary_protocol=V3):
    header = {
        "protocol": header_protocol, "frameVersion": 1, "frameKind": "header",
        "sequence": 0, "terminal": False, "universePolicy": "lean-level-mvar-succ-zero/v1",
        "requestId": "req-mixed", "goalRequestDigest": _goal_request_digest(request),
        "executionContextRef": "unbound", "leanVersion": "4.32.1", "leanCommit": "commit",
        "executablePath": "/bin/lean", "module": "Main",
        "probe": {"name": _batch_probe_name(request), "typeDisplay": "True", "typeStructural": "True"},
        "importedModules": [{"module": "Main", "oleanPath": "/tmp/Main.olean"}], "localContext": [],
    }
    row = {
        "candidate": "Main.step", "status": "accepted",
        "candidateSubject": {"name": "Main.step", "typeDisplay": "True", "typeStructural": "True"},
        "applicationTerm": "Main.step", "dischargedHypotheses": [], "substitutions": [],
        "residualPremises": [], "failureStage": "", "diagnostic": "",
    }
    if row_protocol == V4:
        row.update(residualContexts=[], declarationBinders=[])
    body = {"protocol": row_protocol, "frameVersion": 1, "frameKind": "candidate", "sequence": 1, "terminal": False, "requestId": "req-mixed", "row": row}
    summary = {"protocol": summary_protocol, "frameVersion": 1, "frameKind": "summary", "sequence": 2, "terminal": True, "requestId": "req-mixed", "completed": 1, "total": 1}
    return "\n".join("LADON_FRAME " + json.dumps(frame) for frame in [header, body, summary])


@pytest.mark.parametrize("header,row,summary", [(V3, V3, V4), (V4, V3, V4), (V3, V4, V3)])
def test_batch_cannot_promote_a_prefix_from_a_different_protocol(header, row, summary):
    request = SemanticCandidateRequest(Path("."), "Main", "True", "Main.step")
    try:
        payload, terminal = _parse_batch_worker_payload(
            batch_frames(request, header_protocol=header, row_protocol=row, summary_protocol=summary),
            request, "req-mixed", [request.candidate],
        )
    except ValueError:
        return
    assert not terminal, payload
    assert len(payload["rows"]) <= 1


@pytest.mark.parametrize("missing", ["residual_contexts", "selected_declaration", "semantic_protocol"])
def test_application_identity_rejects_partial_versioned_inputs(missing):
    selected = {"name": "Main.step", "typeDisplay": "True", "typeStructural": "True", "binders": []}
    kwargs = {"residual_contexts": [], "selected_declaration": selected, "semantic_protocol": V4}
    del kwargs[missing]
    with pytest.raises((TypeError, ValueError)):
        _application_subject(
            _subject("statement", selected), _subject("declaration", selected), [], **kwargs,
        )


def test_stored_v4_contexts_are_validated_even_when_read_without_projection():
    shape = {
        "applicationObservationVersion": 4, "semanticProtocol": V4,
        "applicationTerm": "Main.step", "substitutions": [], "dischargedHypotheses": [],
        "residualPremises": [{"typeDisplay": "True", "typeStructural": "True"}],
        "residualContexts": [],
        "selectedDeclaration": {"name": "Main.step", "typeDisplay": "True", "typeStructural": "True", "binders": []},
    }
    artifact = {"payload": {"inputs": {"subjectRefs": [{"kind": "candidate-application", "localId": "app"}]}}, "subjectRefs": [{"kind": "candidate-application", "localId": "app", "searchShape": shape}]}
    with pytest.raises((TypeError, ValueError), match="context|observation"):
        _stored_check(artifact)
