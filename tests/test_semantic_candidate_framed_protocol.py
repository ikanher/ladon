from __future__ import annotations

import json
from pathlib import Path

import pytest

from ladon.semantic_candidate_worker import (
    SEMANTIC_FRAME_PREFIX,
    SemanticCandidateRequest,
    _parse_worker_payload,
)


def _payload() -> dict[str, object]:
    return {
        "protocol": "ladon-lean-semantic-v3/check-candidate",
        "frameVersion": 1,
        "sequence": 0,
        "terminal": True,
        "universePolicy": "lean-level-mvar-succ-zero/v1",
        "requestId": "req-test",
        "executionContextRef": "unbound",
        "leanVersion": "4.0",
        "leanCommit": "commit",
        "executablePath": "/bin/lean",
        "module": "Main",
        "probe": {"name": "ladonSemanticProbe_abc", "typeDisplay": "Nat", "typeStructural": "Nat"},
        "candidate": {"name": "Main.identity", "typeDisplay": "Nat", "typeStructural": "Nat"},
        "applicationTerm": "Main.identity",
        "dischargedHypotheses": [],
        "importedModules": [{"module": "Main", "oleanPath": "/tmp/Main.olean"}],
        "substitutions": [],
        "residualPremises": [],
        "localContext": [],
    }


def test_framed_parser_allows_bounded_process_noise_but_requires_one_nonce_bound_frame() -> None:
    request = SemanticCandidateRequest(Path("."), "Main", "Nat", "Main.identity")
    payload = _payload()
    payload["probe"]["name"] = "ladonSemanticProbe_" + ""  # parser identity is checked below
    # The actual probe name is request-derived; use the worker helper's name.
    from ladon.semantic_candidate_worker import _probe_name

    payload["probe"]["name"] = _probe_name(request)
    output = "warning from Lean\n" + SEMANTIC_FRAME_PREFIX + json.dumps(payload) + "\n"
    assert _parse_worker_payload(output, request, "req-test")["requestId"] == "req-test"


def test_framed_parser_rejects_duplicate_or_forged_frames() -> None:
    request = SemanticCandidateRequest(Path("."), "Main", "Nat", "Main.identity")
    from ladon.semantic_candidate_worker import _probe_name

    payload = _payload()
    payload["probe"]["name"] = _probe_name(request)
    frame = SEMANTIC_FRAME_PREFIX + json.dumps(payload)
    with pytest.raises(ValueError, match="duplicate terminal"):
        _parse_worker_payload(frame + "\n" + frame, request, "req-test")
    payload["requestId"] = "req-other"
    with pytest.raises(ValueError, match="mismatched request ID"):
        _parse_worker_payload(SEMANTIC_FRAME_PREFIX + json.dumps(payload), request, "req-test")


def test_framed_parser_preserves_typed_nonempty_local_context() -> None:
    request = SemanticCandidateRequest(Path("."), "Main", "Nat", "Main.identity")
    from ladon.semantic_candidate_worker import _probe_name

    payload = _payload()
    payload["probe"]["name"] = _probe_name(request)
    payload["localContext"] = [
        {
            "localId": "local:0",
            "userName": "x",
            "binderInfo": "default",
            "typeDisplay": "Nat",
            "typeStructural": "Nat",
            "valueDisplay": "",
            "valueStructural": "",
            "dependencies": [],
            "origin": "goal-introduced",
        }
    ]
    parsed = _parse_worker_payload(SEMANTIC_FRAME_PREFIX + json.dumps(payload), request, "req-test")
    assert parsed["localContext"][0]["origin"] == "goal-introduced"


def test_framed_parser_rejects_same_name_with_mismatched_local_type() -> None:
    request = SemanticCandidateRequest(
        Path("."),
        "Main",
        "x = x",
        "Main.identity",
        local_context=({"name": "x", "type": "Nat"},),
    )
    from ladon.semantic_candidate_worker import _probe_name

    payload = _payload()
    payload["probe"]["name"] = _probe_name(request)
    payload["localContext"] = [
        {
            "localId": "local:0",
            "userName": "x",
            "binderInfo": "default",
            "typeDisplay": "Bool",
            "typeStructural": "Bool",
            "valueDisplay": "",
            "valueStructural": "",
            "dependencies": [],
            "origin": "goal-introduced",
        }
    ]
    with pytest.raises(ValueError, match="mismatched type"):
        _parse_worker_payload(SEMANTIC_FRAME_PREFIX + json.dumps(payload), request, "req-test")


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("frameVersion", 2),
        ("sequence", 1),
        ("terminal", False),
        ("universePolicy", "unknown/v0"),
    ],
)
def test_framed_parser_rejects_invalid_terminal_state(field: str, replacement: object) -> None:
    request = SemanticCandidateRequest(Path("."), "Main", "Nat", "Main.identity")
    from ladon.semantic_candidate_worker import _probe_name

    payload = _payload()
    payload["probe"]["name"] = _probe_name(request)
    payload[field] = replacement
    message = (
        "unsupported universe policy" if field == "universePolicy" else "invalid terminal frame"
    )
    with pytest.raises(ValueError, match=message):
        _parse_worker_payload(SEMANTIC_FRAME_PREFIX + json.dumps(payload), request, "req-test")


def test_framed_parser_rejects_malformed_json_and_missing_frame() -> None:
    request = SemanticCandidateRequest(Path("."), "Main", "Nat", "Main.identity")
    with pytest.raises(ValueError, match="no JSON payload"):
        _parse_worker_payload("ordinary output", request, "req-test")
    with pytest.raises(ValueError, match="non-framed JSON"):
        _parse_worker_payload(SEMANTIC_FRAME_PREFIX + "{bad", request, "req-test")
