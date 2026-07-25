from __future__ import annotations

import json
from pathlib import Path

import pytest

from ladon.lean_protocol import (
    BatchRequest,
    LeanProtocolError,
    ModuleRequest,
    PROTOCOL_VERSION,
    parse_framed_stream,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "lean_runtime"
REQUESTS = (
    ModuleRequest(0, "Pkg.A", "Pkg/A.lean"),
    ModuleRequest(1, "Pkg.B", "Pkg/B.lean"),
)


def test_batch_request_matches_versioned_fixture_contract() -> None:
    request = BatchRequest(REQUESTS)

    assert json.loads(request.to_json()) == json.loads(
        FIXTURE_ROOT.joinpath("batch-request-v1.json").read_text(encoding="utf-8")
    )


def test_mixed_batch_preserves_ordered_success_and_failure() -> None:
    outcome = parse_framed_stream(
        FIXTURE_ROOT.joinpath("mixed-result-v1.jsonl").read_text(encoding="utf-8"),
        REQUESTS,
    )

    assert [record.request.module for record in outcome.records] == ["Pkg.A", "Pkg.B"]
    assert outcome.records[0].payload is not None
    assert outcome.records[1].diagnostic is not None
    assert outcome.summary is not None
    assert outcome.summary.completed == 1


@pytest.mark.parametrize(
    "bad_line, expected",
    [
        ("not-json", "malformed helper JSON frame"),
        (
            json.dumps(
                {
                    "frame": "module",
                    "protocolVersion": PROTOCOL_VERSION,
                    "requestIndex": 1,
                    "module": "Pkg.B",
                    "file": "Pkg/B.lean",
                    "status": "ok",
                    "payload": {},
                }
            ),
            "out-of-order helper module frame",
        ),
        (
            json.dumps(
                {
                    "frame": "module",
                    "protocolVersion": "future-protocol",
                }
            ),
            "protocol version mismatch",
        ),
    ],
)
def test_malformed_or_mismatched_frame_becomes_deterministic_partial_rows(
    bad_line: str,
    expected: str,
) -> None:
    outcome = parse_framed_stream(bad_line, REQUESTS)

    assert [record.status for record in outcome.records] == ["failed", "failed"]
    assert expected in outcome.diagnostics[0].message


def test_validated_prefix_survives_later_malformed_frame() -> None:
    good = json.dumps(
        {
            "frame": "module",
            "protocolVersion": PROTOCOL_VERSION,
            "requestIndex": 0,
            "module": "Pkg.A",
            "file": "Pkg/A.lean",
            "status": "ok",
            "payload": {},
        }
    )

    outcome = parse_framed_stream(f"{good}\nnot-json\n", REQUESTS)

    assert outcome.records[0].status == "ok"
    assert outcome.records[1].status == "failed"
    assert outcome.diagnostics


def test_strict_protocol_error_retains_outcome() -> None:
    with pytest.raises(LeanProtocolError) as caught:
        parse_framed_stream("not-json\n", REQUESTS, strict=True)

    assert len(caught.value.outcome.records) == 2
    assert caught.value.outcome.diagnostics
