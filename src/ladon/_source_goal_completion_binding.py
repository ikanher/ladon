"""Request and capture identity bindings for source-goal completion."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from ladon.source_association_io import _MODULE, _AssociationError

PROTOCOL = "ladon-lean-source-completion-v1/check"
HELPER_VERSION = "ladon-source-completion-helper-v1"
FRAME_PREFIX = "LADON_COMPLETION_FRAME "
REPLAY_PROTOCOL = "ladon-lean-source-completion-replay-v1"
REPLAY_PREFIX = "LADON_COMPLETION_REPLAY "
FRAME_FIELDS = frozenset(["frame", "protocolVersion", "helperVersion", "requestId", "captureId", "termDigest", "contextRef", "module", "filename", "sourceDigest", "line", "column", "leanVersion", "leanCommit", "leanExecutablePath", "goalOrdinal", "goalCount", "useAfter", "byteOffset", "rangeStartByte", "rangeEndByte", "selectionEndByte", "namespaceName", "openDeclarationsStructural", "optionsStructural", "importedModules", "compiledModulePaths", "directImports", "selectedGoal", "status", "termDisplay", "termStructural", "residualGoals", "closedTargetText", "closedProofText", "diagnostic"])
REPLAY_FIELDS = frozenset(["frame", "protocolVersion", "requestId", "captureId", "termDigest", "sourceDigest", "declaration", "observedAxioms", "coverage"])


def _fail(message: str, status: str = "unavailable", code: str = "helper-protocol") -> None:
    raise _AssociationError(status, code, message)


def _sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _module_name(name: Any) -> bool:
    return isinstance(name, str) and bool(_MODULE.fullmatch(name))


def _strings(row: Mapping[str, Any], keys: tuple[str, ...]) -> None:
    if any(not isinstance(row[k], str) for k in keys):
        _fail("completion frame contains a malformed string field")


def _validate_completion_inputs(value, request, capture, source):
    if not isinstance(value, Mapping) or set(value) != FRAME_FIELDS:
        _fail("completion frame fields do not match the closed protocol")
    _validate_request_shape(request)
    _validate_capture_shape(capture)
    _validate_request_capture(request, capture)
    _validate_request_payload(request, capture, source)


def _validate_capture_shape(capture):
    fields = {"source", "environment", "helper", "goal", "scope", "replay", "captureId"}
    if not isinstance(capture, Mapping) or set(capture) != fields:
        _fail("captured source-goal object is malformed", "stale", "capture-identity")
    if any(not isinstance(capture.get(key), Mapping) for key in ("source", "environment", "helper", "goal")):
        _fail("capture source, environment, helper or goal is malformed", "stale", "capture-identity")
    _validate_capture_subobjects(capture)


def _validate_capture_subobjects(capture):
    if capture.get("scope") != "source-goal-elaboration-observation" or capture.get("replay") != "not-run":
        _fail("capture has an unsupported source-goal scope or replay state", "stale", "capture-identity")
    _validate_capture_environment(capture["environment"])
    _validate_capture_source(capture["source"])
    _validate_capture_selection(capture["helper"], capture["goal"])


def _validate_capture_environment(env):
    inventory = env.get("compiledInventory")
    if not isinstance(inventory, Mapping) or not isinstance(inventory.get("modules"), list):
        _fail("capture compiled inventory is malformed", "stale", "capture-identity")


def _validate_capture_source(src):
    if any(not isinstance(src.get(k), Mapping) for k in ("position", "syntaxRange", "selectionRange")):
        _fail("capture source ranges or position are malformed", "stale", "capture-identity")


def _validate_capture_selection(helper, goal):
    if not isinstance(helper.get("observation"), Mapping) or type(goal.get("ordinal")) is not int or type(goal.get("goalCount")) is not int:
        _fail("capture helper observation or goal selection is malformed", "stale", "capture-identity")


def _validate_request_shape(request):
    fields = {"protocolVersion", "contextRef", "module", "filename", "sourceDigest", "snapshotPath", "line", "column", "requestId", "captureId", "term", "termDigest", "goalOrdinal"}
    if not isinstance(request, Mapping) or set(request) != fields or request.get("protocolVersion") != PROTOCOL:
        _fail("completion request fields do not match the closed request protocol")
    if any(not isinstance(request.get(k), str) or not request[k] for k in ("protocolVersion", "contextRef", "module", "filename", "sourceDigest", "snapshotPath", "requestId", "captureId", "termDigest")) or not isinstance(request.get("term"), str):
        _fail("completion request identity contains an empty string")
    _validate_request_position(request)


def _validate_request_position(request):
    if any(type(request.get(k)) is not int or request[k] < 0 for k in ("line", "column", "goalOrdinal")) or request["line"] < 1:
        _fail("completion request position and ordinal are malformed")


def _validate_request_capture(request, capture):
    if request.get("captureId") != capture.get("captureId") or request.get("contextRef") != capture["environment"].get("executionContextRef"):
        _fail("completion request does not bind the supplied capture identity", "stale", "capture-identity")
    canonical = {k: v for k, v in capture.items() if k != "captureId"}
    digest = _sha(json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())
    if capture.get("captureId") != digest:
        _fail("capture identifier does not bind the canonical captured observation", "stale", "capture-id")


def _validate_request_payload(request, capture, source):
    if not isinstance(request.get("term"), str) or request.get("termDigest") != _sha(request["term"].encode()):
        _fail("term digest does not bind exact proposed UTF-8 text", "stale", "term-digest")
    if not isinstance(source, bytes) or _sha(source) != request.get("sourceDigest"):
        _fail("completion source bytes do not match the requested digest", "stale", "source-digest-mismatch")


def _validate_frame_identity(value, request, capture):
    expected = {"frame": "LADON_COMPLETION_FRAME", "protocolVersion": PROTOCOL,
        "helperVersion": HELPER_VERSION, "requestId": request["requestId"],
        "captureId": capture["captureId"], "termDigest": request["termDigest"],
        "contextRef": request["contextRef"], "module": request["module"],
        "filename": request["filename"], "sourceDigest": request["sourceDigest"],
        "line": request["line"], "column": request["column"], "goalOrdinal": request["goalOrdinal"]}
    if any(value[k] != v for k, v in expected.items()):
        _fail("completion frame does not echo the exact request identity")
    if any(type(value[k]) is not int for k in ("line", "column", "goalOrdinal")):
        _fail("completion frame positions and ordinal must be exact integers")
    identities = ("requestId", "captureId", "termDigest", "contextRef", "module", "filename", "sourceDigest")
    if any(not isinstance(value[k], str) or not value[k] for k in identities):
        _fail("completion frame identity is malformed")
    _strings(value, ("leanVersion", "leanCommit", "leanExecutablePath", "namespaceName", "openDeclarationsStructural", "optionsStructural", "termDisplay", "termStructural", "closedTargetText", "closedProofText"))
