"""Closed completion and independent replay protocols for captured Lean goals."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon._source_goal_protocol import GOAL_FIELDS, _validate_goals
from ladon.lean_toolchain import LeanToolchainContext
from ladon.source_association_io import _MODULE, _AssociationError, _file_identity, _strict_json

PROTOCOL = "ladon-lean-source-completion-v1/check"
HELPER_VERSION = "ladon-source-completion-helper-v1"
FRAME_PREFIX = "LADON_COMPLETION_FRAME "
REPLAY_PROTOCOL = "ladon-lean-source-completion-replay-v1"
REPLAY_PREFIX = "LADON_COMPLETION_REPLAY "
FRAME_FIELDS = frozenset(["frame", "protocolVersion", "helperVersion", "requestId", "captureId", "termDigest", "contextRef", "module", "filename", "sourceDigest", "line", "column", "leanVersion", "leanCommit", "leanExecutablePath", "goalOrdinal", "goalCount", "useAfter", "byteOffset", "rangeStartByte", "rangeEndByte", "selectionEndByte", "namespaceName", "openDeclarationsStructural", "optionsStructural", "importedModules", "compiledModulePaths", "directImports", "selectedGoal", "status", "termDisplay", "termStructural", "residualGoals", "closedTargetText", "closedProofText", "diagnostic"])
REPLAY_FIELDS = frozenset(["frame", "protocolVersion", "requestId", "captureId", "termDigest", "sourceDigest", "declaration", "observedAxioms", "coverage"])


def _fail(message: str, status: str = "unavailable", code: str = "helper-protocol") -> None:
    raise _AssociationError(status, code, message)


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


def _validate_worker(value, env, toolchain):
    _validate_captured_worker(value, env)
    _validate_live_worker(value, toolchain)


def _validate_captured_worker(value, env):
    if any(value[k] != env[cap] for k, cap in (("leanVersion", "leanVersion"), ("leanCommit", "leanCommit"), ("leanExecutablePath", "leanExecutablePath"))):
        _fail("completion worker differs from captured toolchain identity", "stale", "worker-identity")


def _validate_live_worker(value, toolchain):
    exe = Path(value["leanExecutablePath"])
    if (value["leanVersion"] != toolchain.lean_release
        or (toolchain.lean_commit is not None and value["leanCommit"] != toolchain.lean_commit)
        or not exe.is_absolute() or exe.is_symlink() or exe.resolve(strict=True) != toolchain.lean_path
        or _file_identity(exe)[0] != toolchain.lean_identity):
        _fail("completion helper Lean worker differs from the selected pinned toolchain", "stale", "worker-identity")


def _validate_observation(value, request, capture):
    src, env, goal = capture["source"], capture["environment"], capture["goal"]
    if (src["digest"] != request["sourceDigest"] or src["module"] != request["module"]
        or src["path"] != request["filename"] or src["position"]["line"] != request["line"]
        or src["position"]["column"] != request["column"] or goal["ordinal"] != request["goalOrdinal"]):
        _fail("request does not identify the captured source goal", "stale", "capture-identity")
    selected = value["selectedGoal"]
    if selected is None:
        if value["status"] not in ("unsupported", "rejected") or value["diagnostic"] is None:
            _fail("selected goal may be absent only for a diagnosed unavailable observation")
        return
    _validate_position_scope(value, src, env, capture["helper"]["observation"])
    _validate_selected_goal(value, goal)


def _validate_position_scope(value, src, env, helper_observation):
    integer_fields = ("line", "column", "byteOffset", "rangeStartByte", "rangeEndByte", "selectionEndByte", "goalCount", "goalOrdinal")
    if any(type(value[k]) is not int for k in integer_fields) or type(value["useAfter"]) is not bool:
        _fail("completion position and count fields must be exact integers/booleans")
    pos, syntax, selection = src["position"], src["syntaxRange"], src["selectionRange"]
    observed = (value["byteOffset"], value["rangeStartByte"], value["rangeEndByte"], value["selectionEndByte"], value["useAfter"])
    expected = (pos["byteOffset"], syntax["startByte"], syntax["endByte"], selection["endByteInclusive"], helper_observation["useAfter"])
    if observed != expected:
        _fail("fresh source observation differs from the preserved source capture", "stale", "observation-changed")
    for key, capture_key in (("namespaceName", "namespace"), ("openDeclarationsStructural", "openDeclarationsStructural"), ("optionsStructural", "optionsStructural")):
        if value[key] != env[capture_key]:
            _fail(f"fresh {key} differs from the preserved capture", "stale", "observation-changed")


def _validate_selected_goal(value, goal):
    if value["goalCount"] != goal["goalCount"] or value["goalOrdinal"] >= value["goalCount"]:
        _fail("fresh goal count or selected ordinal differs from capture", "stale", "observation-changed")
    selected = value["selectedGoal"]
    if not isinstance(selected, dict) or set(selected) != GOAL_FIELDS:
        _fail("selected goal row is malformed")
    if selected != {k: goal[k] for k in GOAL_FIELDS}:
        _fail("fresh selected goal differs from preserved capture", "stale", "observation-changed")
    _validate_goals([selected])


def _validate_inventory(value, env):
    inventory = env["compiledInventory"]["modules"]
    paths = value["compiledModulePaths"]
    _validate_paths(paths, inventory)
    _validate_import_order(value["importedModules"], paths)
    _validate_direct_imports(value["directImports"])


def _validate_paths(paths, inventory):
    if not isinstance(paths, list) or any(not isinstance(row, dict) or set(row) != {"module", "path"} for row in paths):
        _fail("fresh compiled module path rows are malformed")
    ordered = [{"module": x["module"], "path": x["path"]} for x in sorted(paths, key=lambda x: x["module"])]
    if ordered != [{"module": x["module"], "path": x["path"]} for x in inventory]:
        _fail("fresh compiled-module paths differ from captured inventory", "stale", "compiled-inventory-changed")


def _validate_import_order(imported, paths):
    if not isinstance(imported, list) or any(not _module_name(x) for x in imported) or imported != [x["module"] for x in paths]:
        _fail("ordered imported module names differ from fresh path rows", "stale", "compiled-inventory-changed")


def _validate_direct_imports(direct):
    if not isinstance(direct, list) or any(not _module_name(x) for x in direct) or len(direct) != len(set(direct)):
        _fail("owner direct-import list is malformed")


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
    for key in ("requestId", "captureId", "termDigest", "sourceDigest", "declaration"):
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


def _sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _module_name(name: Any) -> bool:
    return isinstance(name, str) and bool(_MODULE.fullmatch(name))


def _strings(row: Mapping[str, Any], keys: tuple[str, ...]) -> None:
    if any(not isinstance(row[k], str) for k in keys):
        _fail("completion frame contains a malformed string field")
