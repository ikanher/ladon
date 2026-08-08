from __future__ import annotations

import pytest

from ladon.semantic_extraction_protocol import (
    PROTOCOL,
    ExtractionRequest,
    FrameKind,
    Operation,
    SemanticIdentity,
    TerminalStatus,
    TerminalSummary,
    exact_expr_fingerprint_v1,
    search_shape_key_v1,
    validate_frame,
    collect_ndjson_frames,
    run_supervised_protocol,
    adapt_elaborated_payload,
)


def request() -> ExtractionRequest:
    return ExtractionRequest(
        request_id="req-1",
        operation=Operation.EXTRACT,
        identity=SemanticIdentity("repo", "Main", "sha256:source", "helper-v1", "lean-v4"),
    )


def test_request_and_summary_are_versioned_and_identity_bearing() -> None:
    req = request()
    header = req.as_frame()
    assert header["protocol"] == PROTOCOL
    summary = TerminalSummary(TerminalStatus.COMPLETE, {"declarations": 1}, 2, "req-1", req.identity).as_frame()
    assert summary["frame"] == FrameKind.SUMMARY
    assert summary["counts"] == {"declarations": 1}


def test_fingerprints_are_deterministic_and_versioned() -> None:
    assert exact_expr_fingerprint_v1("Nat") == exact_expr_fingerprint_v1("Nat")
    assert search_shape_key_v1(head="Eq", arity=2, is_proposition=True) == search_shape_key_v1(head="Eq", arity=2, is_proposition=True)
    assert len(search_shape_key_v1(head="Eq", arity=2, is_proposition=True)) == 64


def test_frame_validation_rejects_wrong_identity_and_duplicates() -> None:
    req = request()
    seen: set[tuple[str, str]] = set()
    frame = {"protocol": PROTOCOL, "frame": "declaration", "requestId": "req-1", "identity": req.identity.as_dict(), "id": "decl-1"}
    validate_frame(frame, req, ordinal=0, seen=seen)
    with pytest.raises(ValueError):
        validate_frame(frame, req, ordinal=1, seen=seen)
    frame["requestId"] = "wrong"
    with pytest.raises(ValueError):
        validate_frame(frame, req, ordinal=2, seen=set())


def test_collection_retains_safe_prefix_and_rejects_missing_summary() -> None:
    req = request()
    declaration = {"protocol": PROTOCOL, "frame": "declaration", "requestId": "req-1", "identity": req.identity.as_dict(), "id": "decl-1"}
    collection = collect_ndjson_frames(json_line(declaration), req)
    assert collection.status == TerminalStatus.PARTIAL
    assert len(collection.frames) == 1
    assert "missing terminal summary" in collection.diagnostics


def test_supervised_runner_receives_one_framed_request() -> None:
    req = request()
    calls: list[str] = []
    def runner(payload: str, _bounds) -> str:
        calls.append(payload)
        return json_line({"protocol": PROTOCOL, "frame": "summary", "requestId": "req-1", "status": "complete", "counts": {}, "emittedFrames": 0, "identity": req.identity.as_dict()})
    result = run_supervised_protocol(req, runner)
    assert result.status == TerminalStatus.COMPLETE
    assert len(calls) == 1


def test_existing_elaborated_payload_adapts_to_complete_frames() -> None:
    req = request()
    payload = {"declarations": [{"id": "decl-1"}], "dependencies": [{"id": "dep-1"}]}
    collection = collect_ndjson_frames(adapt_elaborated_payload(payload, req), req)
    assert collection.status == TerminalStatus.COMPLETE
    assert len(collection.frames) == 2


def json_line(value: dict[str, object]) -> str:
    import json

    return json.dumps(value) + "\n"
