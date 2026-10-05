"""Versioned observations must retain exact context and declaration ownership."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ladon._semantic_observation_results import _validate_candidate_shape
from ladon.semantic_candidate_batch_worker import _validate_batch_row
from ladon.semantic_candidate_protocol import validate_application_rows
from ladon.semantic_candidate_worker import (
    SemanticCandidateRequest,
    _application_subject,
    _context_subject,
    _goal_request_digest,
    _parse_worker_payload,
    _probe_name,
    _subject,
)
from ladon.semantic_projection_core import SemanticProjectionError
from ladon.semantic_stored_receipt import _stored_check

V4 = "ladon-lean-semantic-v4/check-candidate"
BATCH4 = "ladon-lean-semantic-v4/check-candidates"


def local(name="x", local_id="local:0", structural="Nat", dependencies=()):
    return {
        "localId": local_id, "userName": name, "binderInfo": "default",
        "typeDisplay": structural, "typeStructural": structural,
        "valueDisplay": "", "valueStructural": "", "dependencies": list(dependencies),
        "origin": "goal-introduced",
    }


def rows():
    return {
        "protocol": V4, "substitutions": [], "dischargedHypotheses": [],
        "residualPremises": [{"typeDisplay": "True", "typeStructural": "True"}],
        "localContext": [],
        "residualContexts": [{"goalId": "_uniq.1", "localContext": [local()]}],
        "declarationBinders": [],
    }


def test_legacy_expression_only_rows_remain_readable():
    payload = rows()
    payload["protocol"] = "ladon-lean-semantic-v3/check-candidate"
    del payload["residualContexts"], payload["declarationBinders"]
    validate_application_rows(payload)


@pytest.mark.parametrize("missing", ["residualContexts", "declarationBinders"])
def test_v4_cannot_omit_an_observation_population(missing):
    payload = rows()
    del payload[missing]
    with pytest.raises((ValueError, TypeError), match="context|binder|observation"):
        validate_application_rows(payload)


@pytest.mark.parametrize("fault", ["missing-context", "extra-context", "unknown-dependency", "duplicate-id", "forward-dependency", "value-half-present"])
def test_v4_residual_context_is_closed_ordered_and_owned(fault):
    payload = rows()
    context = payload["residualContexts"][0]["localContext"]
    if fault == "missing-context":
        payload["residualContexts"] = []
    elif fault == "extra-context":
        payload["residualContexts"].append(deepcopy(payload["residualContexts"][0]))
    elif fault == "unknown-dependency":
        context[0]["dependencies"] = ["local:foreign"]
    elif fault == "duplicate-id":
        context.append(local("y"))
    elif fault == "forward-dependency":
        context[0]["dependencies"] = ["local:1"]
        context.append(local("y", "local:1"))
    else:
        context[0]["valueDisplay"] = "0"
    with pytest.raises((ValueError, TypeError), match="context|local|depend|value"):
        validate_application_rows(payload)


def test_v4_context_can_have_shadowed_names_and_value_dependencies():
    payload = rows()
    first = local()
    second = local("x", "local:1", dependencies=["local:0"])
    second.update(valueDisplay="x", valueStructural="fvar earlier-x")
    payload["residualContexts"][0]["localContext"] = [first, second]
    validate_application_rows(payload)


def declaration():
    return {"name": "Main.step", "typeDisplay": "True → True", "typeStructural": "forall True True", "binders": []}


def application(contexts=None, selected=None):
    selected = declaration() if selected is None else selected
    return _application_subject(
        _subject("statement", {"typeDisplay": "True", "typeStructural": "True"}),
        _subject("declaration", selected),
        [_subject("statement", {"typeDisplay": "True", "typeStructural": "True"})],
        context=_context_subject("sha256:" + "a" * 64, []),
        application_term="Main.step ?h",
        residual_rows=rows()["residualPremises"],
        residual_contexts=rows()["residualContexts"] if contexts is None else contexts,
        selected_declaration=selected, semantic_protocol=V4,
    )


def test_v4_application_identity_binds_context_and_full_declaration_inventory():
    a = application()
    contexts = deepcopy(rows()["residualContexts"])
    contexts[0]["localContext"][0]["typeStructural"] = "Bool"
    b = application(contexts)
    selected = declaration()
    selected["binders"] = [{**local("premise"), "origin": "declaration-parameter"}]
    c = application(selected=selected)
    assert len({p["localId"] for p in [a, b, c]}) == 3
    assert a["fingerprint"]["scheme"]["version"] == "2"
    assert a["searchShape"]["applicationObservationVersion"] == 4


def test_v4_display_only_changes_do_not_change_structural_application_identity():
    contexts = deepcopy(rows()["residualContexts"])
    contexts[0]["localContext"][0]["typeDisplay"] = "ℕ"
    assert application()["localId"] == application(contexts)["localId"]


def frame(request):
    return {
        **rows(), "frameVersion": 1, "sequence": 0, "terminal": True,
        "universePolicy": "lean-level-mvar-succ-zero/v1", "requestId": "req-v4",
        "goalRequestDigest": _goal_request_digest(request), "executionContextRef": "unbound",
        "leanVersion": "4.32.1", "leanCommit": "commit", "executablePath": "/bin/lean",
        "module": "Main", "probe": {"name": _probe_name(request), "typeDisplay": "True", "typeStructural": "True"},
        "candidate": {"name": request.candidate, "typeDisplay": "True → True", "typeStructural": "forall True True"},
        "applicationTerm": "Main.step ?h",
        "importedModules": [{"module": "Main", "oleanPath": "/tmp/Main.olean"}],
    }


def test_v4_single_frame_accepts_owned_observations_and_rejects_extra_fields():
    request = SemanticCandidateRequest(Path("."), "Main", "True", "Main.step")
    payload = frame(request)
    parsed = _parse_worker_payload("LADON_FRAME " + json.dumps(payload), request, "req-v4")
    assert parsed["residualContexts"] == payload["residualContexts"]
    payload["foreignEvidence"] = {}
    with pytest.raises(ValueError):
        _parse_worker_payload("LADON_FRAME " + json.dumps(payload), request, "req-v4")


def test_v4_batch_rows_require_the_same_owned_context_population():
    payload = rows()
    row = {
        "candidate": "Main.step", "status": "applicable-with-residuals",
        "candidateSubject": {k: v for k, v in declaration().items() if k != "binders"},
        "applicationTerm": "Main.step ?h", "failureStage": "", "diagnostic": "",
        **{k: payload[k] for k in ["substitutions", "dischargedHypotheses", "residualPremises", "residualContexts", "declarationBinders"]},
    }
    _validate_batch_row(row, "Main.step", protocol=BATCH4)
    row["residualContexts"] = []
    with pytest.raises((ValueError, TypeError)):
        _validate_batch_row(row, "Main.step", protocol=BATCH4)


def test_stored_v4_reads_new_fields_without_synthesizing_legacy_populations():
    shape = {
        "applicationObservationVersion": 4, "semanticProtocol": V4,
        "residualContexts": rows()["residualContexts"], "selectedDeclaration": declaration(),
    }
    subject = {"kind": "candidate-application", "localId": "app", "searchShape": shape}
    artifact = {"payload": {"inputs": {"subjectRefs": [{"kind": "candidate-application", "localId": "app"}]}}, "subjectRefs": [subject]}
    assert _stored_check(artifact) == shape
    subject["searchShape"] = {"residualPremises": rows()["residualPremises"]}
    legacy = _stored_check(artifact)
    assert "residualContexts" not in legacy and "selectedDeclaration" not in legacy


def test_v4_projection_ownership_rejects_missing_or_changed_declaration_evidence():
    shape = {"applicationTerm": "Main.step", "substitutions": [], "residualPremises": [], "dischargedHypotheses": [], "localContext": [], "applicationObservationVersion": 4, "semanticProtocol": V4, "residualContexts": [], "selectedDeclaration": declaration()}
    receipt = {"subject": {"localContext": []}}
    check = deepcopy(shape)
    del check["selectedDeclaration"]
    with pytest.raises(SemanticProjectionError):
        _validate_candidate_shape(check, receipt, shape)
    check = deepcopy(shape)
    check["selectedDeclaration"]["typeStructural"] = "False"
    with pytest.raises(SemanticProjectionError):
        _validate_candidate_shape(check, receipt, shape)
