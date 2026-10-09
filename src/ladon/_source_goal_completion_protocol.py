"""Closed completion and independent replay protocols for captured Lean goals."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ladon._source_goal_completion_binding import (
    FRAME_FIELDS,
    FRAME_PREFIX,
    HELPER_VERSION,
    PROTOCOL,
    REPLAY_FIELDS,
    REPLAY_PREFIX,
    REPLAY_PROTOCOL,
    _fail,
    _validate_completion_inputs,
    _validate_frame_identity,
)
from ladon._source_goal_completion_observation import (
    _validate_inventory,
    _validate_observation,
    _validate_worker,
)
from ladon._source_goal_protocol import _validate_goals
from ladon.lean_toolchain import LeanToolchainContext
from ladon.source_association_io import _strict_json


def _frame(stdout: str, prefix: str, expected: frozenset[str], label: str) -> dict[str, Any]:
    if not isinstance(stdout, str):
        _fail(f"{label} output must be text")
    rows = [line[len(prefix):] for line in stdout.splitlines() if line.startswith(prefix)]
    if len(rows) != 1:
        _fail(f"{label} must emit exactly one terminal frame")
    value = _strict_json(rows[0])
    if not isinstance(value, dict) or set(value) != expected:
        _fail(f"{label} fields do not match the closed protocol")
    return value


def decode_completion(stdout: str) -> dict[str, Any]:
    value = _frame(stdout, FRAME_PREFIX, FRAME_FIELDS, "completion helper")
    if value["frame"] != "LADON_COMPLETION_FRAME" or value["protocolVersion"] != PROTOCOL or value["helperVersion"] != HELPER_VERSION:
        _fail("completion helper reported another protocol or helper version")
    return value


def validate_completion(
    value: Mapping[str, Any], request: Mapping[str, Any],
    capture: Mapping[str, Any], toolchain: LeanToolchainContext, source: bytes,
) -> None:
    """Bind one terminal frame to the exact request, capture and pinned worker."""
    _validate_completion_inputs(value, request, capture, source)
    _validate_frame_identity(value, request, capture)
    _validate_worker(value, capture["environment"], toolchain)
    _validate_observation(value, request, capture)
    _validate_inventory(value, capture["environment"])
    _validate_outcome(value)
    expected_module = "LadonCompletionContext_" + request["requestId"] if value["status"] == "accepted" else ""
    if value["sourceContextModule"] != expected_module:
        _fail("completion source context does not match the exact request")


def _validate_outcome(value):
    status = value["status"]
    if status not in {"accepted", "incomplete", "rejected", "unsupported"}:
        _fail("completion status is outside the protocol")
    if type(value["goalCount"]) is not int or type(value["goalOrdinal"]) is not int or type(value["useAfter"]) is not bool:
        _fail("completion goal selection fields are malformed")
    _validate_residuals(value["residualGoals"])
    _validate_diagnostic(value["diagnostic"])
    _validate_status(value, status)


def _validate_status(value, status):
    if status == "accepted":
        _validate_accepted(value)
    elif status == "incomplete":
        _validate_incomplete(value)
    elif value["closedTargetText"] or value["closedProofText"]:
        _fail("rejected or unsupported completion cannot carry closed expressions")
    if status == "unsupported" and (value["termDisplay"] or value["termStructural"]):
        _fail("unsupported observation cannot claim to have checked the proposed term")


def _validate_residuals(residual):
    if not isinstance(residual, list):
        _fail("residual goals must be an ordered array")
    _validate_goals(residual)


def _validate_diagnostic(diagnostic):
    if diagnostic is not None and (not isinstance(diagnostic, dict) or set(diagnostic) != {"code", "message"} or any(not isinstance(diagnostic[k], str) or not diagnostic[k] for k in diagnostic)):
        _fail("completion diagnostic must be null or an exact code/message object")


def _validate_accepted(value):
    required = ("closedTargetText", "closedProofText", "termDisplay", "termStructural")
    if value["residualGoals"] or any(not value[key] for key in required):
        _fail("accepted completion requires a checked term, closed expressions and no residual goals")


def _validate_incomplete(value):
    if not value["residualGoals"] or value["closedTargetText"] or value["closedProofText"]:
        _fail("incomplete completion requires actual residual goals and no closed proof")


def decode_replay(stdout: str) -> dict[str, Any]:
    value = _frame(stdout, REPLAY_PREFIX, REPLAY_FIELDS, "compiler replay")
    if value["frame"] != "LADON_COMPLETION_REPLAY" or value["protocolVersion"] != REPLAY_PROTOCOL:
        _fail("compiler replay reported another protocol")
    return value


def validate_replay(value: Mapping[str, Any], expected: Mapping[str, Any]) -> None:
    """Validate bindings and Lean-collected transitive axioms for replay."""
    _validate_replay_shape(value)
    _validate_replay_bindings(value, expected)
    _validate_replay_axioms(value["observedAxioms"], value["coverage"])


def _validate_replay_shape(value):
    if not isinstance(value, Mapping) or set(value) != REPLAY_FIELDS:
        _fail("compiler replay fields do not match the closed protocol")
    if value["frame"] != "LADON_COMPLETION_REPLAY" or value["protocolVersion"] != REPLAY_PROTOCOL:
        _fail("compiler replay reported another protocol")


def _validate_replay_bindings(value, expected):
    for key in ("requestId", "captureId", "termDigest", "sourceDigest", "declaration", "sourceContextDigest"):
        if not isinstance(value[key], str) or value[key] != expected[key] or not value[key]:
            _fail(f"compiler replay binding {key} does not match generated source", "stale", "replay-binding")


def _validate_replay_axioms(axioms, coverage):
    if coverage == "unavailable":
        if axioms is not None:
            _fail("unavailable axiom collection cannot report a partial list")
        _fail("compiler replay coverage is unavailable", "unavailable", "axiom-coverage")
    if coverage != "complete":
        _fail("compiler replay coverage status is malformed")
    if not isinstance(axioms, list) or any(not isinstance(x, str) or not x for x in axioms) or axioms != sorted(set(axioms)):
        _fail("Lean-collected axiom names must be sorted and unique")
