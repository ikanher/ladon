"""Isolated explicit v4 contracts and an unchanged historical v3 control."""
from __future__ import annotations

from pathlib import Path

import pytest

from ladon.semantic_candidate_protocol import validate_application_rows
from ladon.semantic_candidate_worker import (
    SEMANTIC_PROTOCOL,
    SemanticCandidateRequest,
    _application_subject,
    _execution_context_ref,
    _goal_request_digest,
    _subject,
    _validate_worker_frame,
)

V4_PROTOCOL = "ladon-lean-semantic-v4/check-candidate"


def _local(local_id: str, name: str, structural: str) -> dict[str, object]:
    return {
        "localId": local_id,
        "userName": name,
        "binderInfo": "default",
        "typeDisplay": structural,
        "typeStructural": structural,
        "valueDisplay": "",
        "valueStructural": "",
        "dependencies": [],
        "origin": "goal-introduced",
    }


def _v3_rows() -> dict[str, object]:
    return {
        "substitutions": [],
        "dischargedHypotheses": [],
        "residualPremises": [{"typeDisplay": "R x", "typeStructural": "app R x"}],
        "localContext": [_local("local:x", "x", "Nat")],
    }


def _frame(request: SemanticCandidateRequest, *, v4_fields: bool) -> dict[str, object]:
    frame: dict[str, object] = {
        "protocol": V4_PROTOCOL if v4_fields else SEMANTIC_PROTOCOL,
        "frameVersion": 1,
        "sequence": 0,
        "terminal": True,
        "universePolicy": "lean-level-mvar-succ-zero/v1",
        "requestId": "request-v4-contract",
        "goalRequestDigest": _goal_request_digest(request),
        "executionContextRef": _execution_context_ref(request),
        "leanVersion": "4.32.2",
        "leanCommit": "commit",
        "executablePath": "/bin/lean",
        "module": "Main",
        "probe": {"name": "ladonSemanticProbe_test", "typeDisplay": "Target", "typeStructural": "Target"},
        "candidate": {"name": request.candidate, "typeDisplay": "Nat → Target", "typeStructural": "forallE Nat Target"},
        "applicationTerm": "Main.candidate",
        "dischargedHypotheses": [],
        "importedModules": [{"module": "Main", "oleanPath": "/tmp/Main.olean"}],
        "substitutions": [],
        "residualPremises": [{"typeDisplay": "R x", "typeStructural": "app R x"}],
        "localContext": [_local("local:x", "x", "Nat")],
    }
    if v4_fields:
        frame["residualContexts"] = [
            {"goalId": "?m.4", "localContext": [_local("local:x", "x", "Nat")]},
        ]
        frame["declarationBinders"] = [
            {**_local("local:param0", "x", "Nat"), "origin": "declaration-parameter"},
        ]
    return frame


def test_legacy_v3_expression_only_residual_remains_valid() -> None:
    """The old strict row validator continues to accept its historical shape."""
    request = SemanticCandidateRequest(Path("."), "Main", "True", "Main.candidate")
    _validate_worker_frame(_frame(request, v4_fields=False), request, "request-v4-contract")
    validate_application_rows(_v3_rows())


def test_v4_frame_with_context_and_binders_dispatches() -> None:
    request = SemanticCandidateRequest(Path("."), "Main", "True", "Main.candidate")
    _validate_worker_frame(_frame(request, v4_fields=True), request, "request-v4-contract")


def test_v4_frame_without_context_or_binders_rejects_for_missing_v4_evidence() -> None:
    request = SemanticCandidateRequest(Path("."), "Main", "True", "Main.candidate")
    frame = _frame(request, v4_fields=False)
    frame["protocol"] = V4_PROTOCOL
    with pytest.raises(ValueError) as rejected:
        _validate_worker_frame(frame, request, "request-v4-contract")
    message = str(rejected.value)
    assert "residualContexts" in message or "declarationBinders" in message


def test_application_identity_v4_binds_context_per_same_expression_residual() -> None:
    """Equal residual expressions with distinct observed contexts need distinct IDs."""
    statement = _subject("statement", {"name": "Target", "typeDisplay": "Target", "typeStructural": "Target"})
    selected = {
        "name": "Main.candidate",
        "typeDisplay": "R x → R x → Target",
        "typeStructural": "forallE R (forallE R Target)",
        "binders": [{**_local("local:param0", "x", "Nat"), "origin": "declaration-parameter"}],
    }
    declaration = _subject("declaration", selected)
    residual = _subject("statement", {"name": "R x", "typeDisplay": "R x", "typeStructural": "app R x"})
    residuals = [residual, dict(residual)]
    rows = [
        {"typeDisplay": "R x", "typeStructural": "app R x"},
        {"typeDisplay": "R x", "typeStructural": "app R x"},
    ]
    base_context = [
        _local("local:x", "x", "Nat"),
        {
            **_local("local:y", "y", "Nat"),
            "valueDisplay": "wrap x",
            "valueStructural": "wrap x",
            "dependencies": ["local:x"],
        },
    ]
    changed_value_context = [
        base_context[0],
        {**base_context[1], "valueDisplay": "wrap (wrap x)", "valueStructural": "wrap (wrap x)"},
    ]
    contexts = [
        {"goalId": "?m.1", "localContext": base_context},
        {"goalId": "?m.2", "localContext": base_context},
    ]
    changed = [contexts[0], {"goalId": "?m.2", "localContext": changed_value_context}]
    def build(owned_contexts: list[dict[str, object]]) -> dict[str, object]:
        return _application_subject(
            statement,
            declaration,
            residuals,
            application_term="candidate ?m₁ ?m₂",
            residual_rows=rows,
            residual_contexts=owned_contexts,
            selected_declaration=selected,
            semantic_protocol=V4_PROTOCOL,
        )

    first = build(contexts)
    second = build(changed)
    assert first["fingerprint"]["digest"] != second["fingerprint"]["digest"]  # type: ignore[index]
    assert first["searchShape"]["applicationObservationVersion"] == 4  # type: ignore[index]
