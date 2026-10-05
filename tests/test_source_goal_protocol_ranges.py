"""Transport controls for cursor-selection range and observed worker identity."""
from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest

from ladon._source_goal_protocol import PROTOCOL, validate_observation
from ladon.source_association_io import _AssociationError


@pytest.fixture
def observation(tmp_path):
    source = b"example : True := by\n  skip\n"
    executable = tmp_path / "lean"
    executable.write_bytes(b"transport fixture, not a Lean executable")
    context = SimpleNamespace(
        lean_release="4.32.1", lean_commit=None, lean_path=executable,
        lean_identity="sha256:" + hashlib.sha256(executable.read_bytes()).hexdigest(),
    )
    request = {
        "requestId": "test", "contextRef": "context", "module": "Owner",
        "filename": "Owner.lean", "sourceDigest": "source", "line": 2, "column": 6,
    }
    frame = {
        **request, "frame": "LADON_GOAL_FRAME", "protocolVersion": PROTOCOL,
        "helperVersion": "ladon-source-goal-helper-v1", "leanVersion": "4.32.1",
        "leanCommit": "observed-commit", "leanExecutablePath": str(executable),
        "compiledModulePaths": [{"module": "Init", "path": "/tmp/Init.olean"}],
        "byteOffset": len(source) - 1, "goals": [], "goalCount": 0,
        "useAfter": True, "rangeStartByte": 22, "rangeEndByte": len(source) - 1,
        "selectionEndByte": len(source), "namespaceName": "",
        "openDeclarationsStructural": "", "optionsStructural": "",
        "importedModules": ["Init"], "observationCount": 1,
    }
    return frame, request, context, source


def test_disjoint_selection_range_is_rejected(observation):
    frame, request, context, source = observation
    frame.update(rangeStartByte=0, rangeEndByte=7, selectionEndByte=7)
    with pytest.raises(_AssociationError, match="selection range"):
        validate_observation(frame, request, context, source)


def test_empty_observed_commit_is_rejected_even_without_expected_commit(observation):
    frame, request, context, source = observation
    frame["leanCommit"] = ""
    with pytest.raises(_AssociationError, match="empty"):
        validate_observation(frame, request, context, source)


def test_trailing_cursor_can_follow_raw_tactic_syntax(observation):
    frame, request, context, source = observation
    frame.update(line=3, column=0, byteOffset=len(source))
    request.update(line=3, column=0)
    validate_observation(frame, request, context, source)


@pytest.mark.parametrize("selection_end", [True, -1, 7, 100])
def test_selection_range_has_ordered_bounded_integer_end(observation, selection_end):
    frame, request, context, source = observation
    frame["selectionEndByte"] = selection_end
    with pytest.raises(_AssociationError):
        validate_observation(frame, request, context, source)
