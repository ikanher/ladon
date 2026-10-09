"""Closed source-goal observation protocol, separate from checker receipts."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon._expr_graph_protocol import validate_structural_text
from ladon.lean_toolchain import LeanToolchainContext
from ladon.source_association_io import _AssociationError, _file_identity, _strict_json

PROTOCOL = "ladon-lean-source-goal-v1/capture"
HELPER_VERSION = "ladon-source-goal-helper-v1"
FRAME_PREFIX = "LADON_GOAL_FRAME "
FRAME_FIELDS = frozenset({
    "frame", "protocolVersion", "helperVersion", "leanVersion", "leanCommit",
    "leanExecutablePath", "compiledModulePaths", "requestId", "contextRef", "module",
    "filename", "sourceDigest", "line", "column", "byteOffset", "goals", "goalCount",
    "useAfter", "rangeStartByte", "rangeEndByte", "selectionEndByte", "namespaceName",
    "openDeclarationsStructural", "optionsStructural", "importedModules", "observationCount",
})
GOAL_FIELDS = frozenset({"goalId", "typeDisplay", "typeStructural", "localContext"})
LOCAL_FIELDS = frozenset({
    "localId", "userName", "binderInfo", "typeDisplay", "typeStructural",
    "valueDisplay", "valueStructural", "dependencies", "implementationDetail",
})


def protocol_error(message: str) -> None:
    raise _AssociationError("unavailable", "helper-protocol", message)


def decode_observation(stdout: str) -> dict[str, Any]:
    frames = [line[len(FRAME_PREFIX):] for line in stdout.splitlines()
              if line.startswith(FRAME_PREFIX)]
    if len(frames) != 1:
        protocol_error("source helper must emit exactly one terminal frame")
    value = _strict_json(frames[0])
    if not isinstance(value, dict) or set(value) != FRAME_FIELDS:
        protocol_error("source helper frame fields do not match protocol v1")
    identities = {
        "frame": "LADON_GOAL_FRAME", "protocolVersion": PROTOCOL,
        "helperVersion": HELPER_VERSION,
    }
    if any(value[key] != expected for key, expected in identities.items()):
        protocol_error("source helper reported another protocol or helper version")
    return value


def validate_observation(
    value: Mapping[str, Any], request: Mapping[str, Any],
    context: LeanToolchainContext, source: bytes,
) -> None:
    _validate_echo(value, request)
    _validate_worker(value, context)
    _validate_position(value, source)
    _validate_imports(value)
    _validate_goals(value["goals"])
    if len(value["goals"]) != value["goalCount"]:
        protocol_error("source helper goal count does not match its ordered goals")
    _validate_context_scalars(value)


def _validate_echo(value: Mapping[str, Any], request: Mapping[str, Any]) -> None:
    keys = ("requestId", "contextRef", "module", "filename", "sourceDigest", "line", "column")
    if any(value[key] != request[key] for key in keys):
        protocol_error("source helper did not echo the exact request identity")


def _validate_worker(value: Mapping[str, Any], context: LeanToolchainContext) -> None:
    _strings(value, ("leanVersion", "leanCommit", "leanExecutablePath"), nonempty=True)
    executable = Path(value["leanExecutablePath"])
    if (
        value["leanVersion"] != context.lean_release
        or (context.lean_commit is not None and value["leanCommit"] != context.lean_commit)
        or not executable.is_absolute() or executable.is_symlink()
        or executable.resolve(strict=True) != context.lean_path
        or _file_identity(executable)[0] != context.lean_identity
    ):
        raise _AssociationError("stale", "worker-identity", "observed Lean worker differs from selected toolchain")


def source_offset(source: bytes, line: int, column: int) -> int:
    # Lean FileMap uses LF lines and Unicode scalar columns, not UTF-16 or bytes.
    text = source.decode("utf-8")
    lines = text.split("\n")
    if line < 1 or line > len(lines) or column < 0 or column > len(lines[line - 1]):
        raise _AssociationError("unavailable", "source-position", "position is outside the exact source")
    prefix = "\n".join(lines[:line - 1])
    prefix = prefix + "\n" if line > 1 else ""
    return len((prefix + lines[line - 1][:column]).encode("utf-8"))


def _validate_position(value: Mapping[str, Any], source: bytes) -> None:
    keys = ("line", "column", "byteOffset", "goalCount", "rangeStartByte",
            "rangeEndByte", "selectionEndByte", "observationCount")
    if any(type(value[key]) is not int or value[key] < 0 for key in keys):
        protocol_error("source helper positions and counts must be nonnegative integers")
    if value["byteOffset"] != source_offset(source, value["line"], value["column"]):
        protocol_error("source helper byte offset differs from the requested scalar position")
    if not 0 <= value["rangeStartByte"] < value["rangeEndByte"] <= len(source):
        protocol_error("source helper syntax range lies outside the exact source")
    if not (
        value["rangeEndByte"] <= value["selectionEndByte"] <= len(source)
        and value["rangeStartByte"] <= value["byteOffset"] <= value["selectionEndByte"]
    ):
        protocol_error("source helper selection range does not contain the requested position")
    if value["observationCount"] != 1 or type(value["useAfter"]) is not bool:
        protocol_error("source helper did not select exactly one tactic context")


def _validate_imports(value: Mapping[str, Any]) -> None:
    names, rows = value["importedModules"], value["compiledModulePaths"]
    if not isinstance(names, list) or not isinstance(rows, list):
        protocol_error("source helper imported modules must be ordered arrays")
    if any(not isinstance(name, str) or not name for name in names):
        protocol_error("source helper imported module name is malformed")
    _validate_import_paths(rows)
    if [row["module"] for row in rows] != names:
        protocol_error("source helper path rows do not match its ordered import closure")


def _validate_import_paths(rows: list[Any]) -> None:
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"module", "path"}:
            protocol_error("source helper import path row is malformed")
        _strings(row, ("module", "path"), nonempty=True)


def _validate_context_scalars(value: Mapping[str, Any]) -> None:
    _strings(value, ("namespaceName", "openDeclarationsStructural", "optionsStructural"))


def _strings(row: Mapping[str, Any], fields: tuple[str, ...], *, nonempty=False) -> None:
    if any(not isinstance(row[key], str) for key in fields):
        protocol_error("source helper string field is malformed")
    if nonempty and any(not row[key] for key in fields):
        protocol_error("source helper required identity or type is empty")


def _validate_goals(goals: Any) -> None:
    if not isinstance(goals, list):
        protocol_error("source helper goals must be an ordered array")
    known = set()
    for goal in goals:
        if not isinstance(goal, dict) or set(goal) != GOAL_FIELDS:
            protocol_error("source helper goal fields are malformed")
        _strings(goal, ("goalId", "typeDisplay", "typeStructural"), nonempty=True)
        _structural_text(goal["typeStructural"])
        if goal["goalId"] in known:
            protocol_error("source helper repeats a goal identity")
        known.add(goal["goalId"])
        _validate_locals(goal["localContext"])


def _validate_locals(locals_: Any) -> None:
    if not isinstance(locals_, list):
        protocol_error("source helper local context must be an ordered array")
    known: set[str] = set()
    for local in locals_:
        _validate_local(local)
        dependencies = local["dependencies"]
        if any(dep not in known for dep in dependencies) or local["localId"] in known:
            protocol_error("source helper local identities/dependencies are out of order")
        known.add(local["localId"])


def _validate_local(local: Any) -> None:
    if not isinstance(local, dict) or set(local) != LOCAL_FIELDS:
        protocol_error("source helper local fields are malformed")
    _strings(local, ("localId", "userName", "binderInfo", "typeDisplay", "typeStructural"), nonempty=True)
    _strings(local, ("valueDisplay", "valueStructural"))
    _structural_text(local["typeStructural"])
    _structural_text(local["valueStructural"])
    if type(local["implementationDetail"]) is not bool:
        protocol_error("source helper implementation-detail role is malformed")
    dependencies = local["dependencies"]
    if not isinstance(dependencies, list) or any(not isinstance(dep, str) for dep in dependencies):
        protocol_error("source helper local dependencies must be an array of identities")
    if len(dependencies) != len(set(dependencies)):
        protocol_error("source helper repeats a local dependency identity")


def observation_identity(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "requestId"}


def _structural_text(text: str) -> None:
    try:
        validate_structural_text(text)
    except ValueError as error:
        protocol_error(str(error))
