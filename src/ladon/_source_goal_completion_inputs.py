"""Owned capture inputs and identity checks for explicit completion."""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from ladon._source_goal_protocol import HELPER_VERSION, PROTOCOL, _validate_goals
from ladon.source_association_io import _AssociationError, _digest

CAPTURE_FIELDS = frozenset({
    "source", "environment", "helper", "goal", "scope", "replay", "captureId",
})


def own_capture(value: Mapping[str, Any]) -> dict[str, Any]:
    """Detach caller data, then check its canonical ID before deeper validation."""
    try:
        owned = json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
    except (TypeError, ValueError) as error:
        raise _AssociationError("rejected", "invalid-capture", "capture must be JSON data") from error
    if not isinstance(owned, dict) or set(owned) != CAPTURE_FIELDS:
        raise _AssociationError("rejected", "invalid-capture", "a complete source capture is required")
    supplied = owned["captureId"]
    payload = {key: item for key, item in owned.items() if key != "captureId"}
    expected = _digest(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode())
    if supplied != expected:
        raise _AssociationError("stale", "capture-identity-mismatch", "capture differs from its canonical identity")
    _validate_capture(owned)
    return owned


def _validate_capture(capture: Mapping[str, Any]) -> None:
    if capture["scope"] != "source-goal-elaboration-observation" or capture["replay"] != "not-run":
        raise _AssociationError("rejected", "invalid-capture-scope", "exploration and checking receipts are not source captures")
    for key in ("source", "environment", "helper", "goal"):
        if not isinstance(capture[key], dict):
            raise _AssociationError("rejected", "invalid-capture", "capture sections must be objects")
    helper = capture["helper"]
    if helper.get("protocolVersion") != PROTOCOL or helper.get("helperVersion") != HELPER_VERSION:
        raise _AssociationError("rejected", "capture-version", "completion requires source capture v1")
    _validate_goal(capture["goal"])
    _validate_source(capture["source"])


def _validate_goal(goal: Mapping[str, Any]) -> None:
    ordinal, count = goal.get("ordinal"), goal.get("goalCount")
    if type(ordinal) is not int or type(count) is not int or not 0 <= ordinal < count:
        raise _AssociationError("rejected", "capture-selection", "capture goal selection is invalid")
    _validate_goals([{key: value for key, value in goal.items() if key not in {"ordinal", "goalCount"}}])


def _validate_source(source: Mapping[str, Any]) -> None:
    expected = {"path", "module", "digest", "byteLength", "position", "syntaxRange", "selectionRange"}
    if set(source) != expected:
        raise _AssociationError("rejected", "capture-source", "capture source fields are incomplete")
    if any(not isinstance(source[key], str) or not source[key] for key in ("path", "module", "digest")):
        raise _AssociationError("rejected", "capture-source", "capture source identities are invalid")
    _validate_source_positions(source)
    if type(source["byteLength"]) is not int or source["byteLength"] < 0:
        raise _AssociationError("rejected", "capture-source", "capture source length is invalid")


def _validate_source_positions(source: Mapping[str, Any]) -> None:
    for key, fields in (
        ("position", {"line", "column", "byteOffset"}),
        ("syntaxRange", {"startByte", "endByte"}),
        ("selectionRange", {"startByte", "endByteInclusive"}),
    ):
        row = source[key]
        if not isinstance(row, dict) or set(row) != fields:
            raise _AssociationError("rejected", "capture-source", "capture source selection is incomplete")
        if any(type(value) is not int or value < 0 for value in row.values()):
            raise _AssociationError("rejected", "capture-source", "capture source positions must be nonnegative integers")


def capture_request_fields(capture: Mapping[str, Any]) -> dict[str, Any]:
    source = capture["source"]
    return {
        "source_path": source["path"], "module": source["module"],
        "line": source["position"]["line"], "column": source["position"]["column"],
        "goal_ordinal": capture["goal"]["ordinal"],
        "expected_source_digest": source["digest"],
    }
